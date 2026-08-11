"""Deterministic, source-bound grounding for the governed Cut 1 narration only."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, cast

from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import (
    ClaimSupport,
    EvaluationResult,
    GeneratedScript,
    KnowledgeChunk,
    RetrievedContext,
)

CUT1_STYLE = "CUT1_ATOMIC_FACTS_V1"
CUT1_POLICY_VERSION = "cut1-atomic-grounding-v1"
CUT1_SCHEMA_VERSION = "cut1-project-facts-v1"
FACTS_RELATIVE_PATH = Path("docs/governance/cut1-project-facts-v1.json")
FACTS_SOURCE_FILENAME = "cut1-project-facts-v1.md"
ACCEPTED_REVISION = "a868137fab607ae75d4b272301e9fc52b898e15c"
EXPECTED_ASSET_SHA256 = "ace9b936d4eeb8540cf6b617ce371da94262393202201d08c2ce30761761f8ca"
MAX_CONTRACT_BYTES = 131_072
MAX_SOURCES = 16
MAX_SPANS = 64
MAX_PROPOSITIONS = 64
EXACT_SOURCE_PATHS = {
    "README.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/PRD.md",
    "docs/PROJECT_AVATAR_PACK.md",
    "docs/ADR/0055-cut1-narration-speech-lock.md",
    "docs/QUALITY_GATES.md",
}
PRESENTERS = ("meera", "myra", "raj")
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
ID_PATTERN = re.compile(r"(?:src|fact|claim)_[a-z0-9_]{1,64}\Z")


class Cut1GroundingError(ValueError):
    """A bounded, non-sensitive Cut 1 contract validation failure."""


class _DuplicateKey(ValueError):
    pass


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _fail() -> NoReturn:
    raise Cut1GroundingError("Cut 1 grounding contract is invalid.")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _object(value: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        _fail()
    return cast(dict[str, Any], value)


def _identifier(value: object, *, prefix: str) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None or not value.startswith(prefix):
        _fail()
    return value


def _checksum(value: object) -> str:
    if not isinstance(value, str) or SHA_PATTERN.fullmatch(value) is None:
        _fail()
    return value


def _bounded_int(value: object, *, maximum: int) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        _fail()
    return value


@dataclass(frozen=True)
class SourceSpan:
    span_id: str
    source_id: str
    byte_start: int
    byte_end: int
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class Proposition:
    proposition_id: str
    statement: str
    source_span_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimMapping:
    claim_id: str
    claim_sha256_by_presenter: Mapping[str, str]
    proposition_ids: tuple[str, ...]


@dataclass(frozen=True)
class Cut1GroundingContract:
    policy_version: str
    accepted_revision: str
    asset_sha256: str
    contract_sha256: str
    spans: Mapping[str, SourceSpan]
    propositions: Mapping[str, Proposition]
    claim_mappings: tuple[ClaimMapping, ...]

    def project_source_bytes(self) -> bytes:
        return (
            "\n".join(
                f"{item.proposition_id}: {item.statement}"
                for item in self.propositions.values()
            )
            + "\n"
        ).encode()

    def evidence_checksum(self, mapping: ClaimMapping) -> str:
        value = {
            "acceptedRevision": self.accepted_revision,
            "assetSha256": self.asset_sha256,
            "claimId": mapping.claim_id,
            "claimSha256ByPresenter": dict(mapping.claim_sha256_by_presenter),
            "contractSha256": self.contract_sha256,
            "policyVersion": self.policy_version,
            "propositions": [
                {
                    "propositionId": proposition_id,
                    "sourceSpans": [
                        {
                            "byteCount": self.spans[span_id].byte_count,
                            "byteEnd": self.spans[span_id].byte_end,
                            "byteStart": self.spans[span_id].byte_start,
                            "sha256": self.spans[span_id].sha256,
                            "sourceId": self.spans[span_id].source_id,
                            "spanId": span_id,
                        }
                        for span_id in self.propositions[proposition_id].source_span_ids
                    ],
                    "statementSha256": _sha(
                        self.propositions[proposition_id].statement.encode()
                    ),
                }
                for proposition_id in mapping.proposition_ids
            ],
        }
        return "sha256:" + _sha(_canonical(value))


def _read_contract(root: Path) -> tuple[bytes, dict[str, Any]]:
    target = root.resolve() / FACTS_RELATIVE_PATH
    try:
        if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_CONTRACT_BYTES:
            _fail()
        raw = target.read_bytes()
        if _sha(raw) != EXPECTED_ASSET_SHA256:
            _fail()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, _DuplicateKey):
        _fail()
    if not isinstance(value, dict):
        _fail()
    return raw, value


def _immutable_source_bytes(root: Path, path: str, expected_sha256: str) -> bytes:
    target = root.resolve() / path
    try:
        current = target.read_bytes()
    except OSError:
        current = b""
    if _sha(current) == expected_sha256:
        return current
    try:
        result = subprocess.run(
            ["git", "show", f"{ACCEPTED_REVISION}:{path}"],
            cwd=root.resolve(),
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        _fail()
    if result.returncode != 0 or _sha(result.stdout) != expected_sha256:
        _fail()
    return result.stdout


def load_cut1_grounding_contract(
    *, root: Path, payload: Mapping[str, object] | None = None
) -> Cut1GroundingContract:
    raw, authoritative = _read_contract(root)
    if payload is not None and _canonical(payload) != _canonical(authoritative):
        _fail()
    value = _object(
        authoritative,
        {"schemaVersion", "policyVersion", "acceptedRevision", "sources", "propositions", "claimMappings"},
    )
    if (
        value["schemaVersion"] != CUT1_SCHEMA_VERSION
        or value["policyVersion"] != CUT1_POLICY_VERSION
        or value["acceptedRevision"] != ACCEPTED_REVISION
    ):
        _fail()
    source_rows = value["sources"]
    proposition_rows = value["propositions"]
    mapping_rows = value["claimMappings"]
    if (
        not isinstance(source_rows, list)
        or not 0 < len(source_rows) <= MAX_SOURCES
        or not isinstance(proposition_rows, list)
        or not 0 < len(proposition_rows) <= MAX_PROPOSITIONS
        or not isinstance(mapping_rows, list)
        or len(mapping_rows) != 18
    ):
        _fail()

    spans: dict[str, SourceSpan] = {}
    source_ids: set[str] = set()
    observed_paths: set[str] = set()
    for source_value in source_rows:
        source = _object(source_value, {"sourceId", "path", "revision", "byteCount", "sha256", "spans"})
        source_id = _identifier(source["sourceId"], prefix="src_")
        path = source["path"]
        if (
            source_id in source_ids
            or not isinstance(path, str)
            or path not in EXACT_SOURCE_PATHS
            or str(PurePosixPath(path)) != path
            or source["revision"] != ACCEPTED_REVISION
        ):
            _fail()
        source_ids.add(source_id)
        observed_paths.add(path)
        source_sha256 = _checksum(source["sha256"])
        source_bytes = _immutable_source_bytes(root, path, source_sha256)
        if (
            source["byteCount"] != len(source_bytes)
            or source_sha256 != _sha(source_bytes)
            or not isinstance(source["spans"], list)
            or not 0 < len(source["spans"]) <= MAX_SPANS
        ):
            _fail()
        for span_value in source["spans"]:
            span = _object(span_value, {"spanId", "byteStart", "byteEnd", "byteCount", "sha256", "text"})
            span_id = _identifier(span["spanId"], prefix="src_")
            start = _bounded_int(span["byteStart"], maximum=len(source_bytes))
            end = _bounded_int(span["byteEnd"], maximum=len(source_bytes))
            text_value = span["text"]
            if span_id in spans or end <= start or not isinstance(text_value, str):
                _fail()
            selected = source_bytes[start:end]
            if (
                span["byteCount"] != len(selected)
                or _checksum(span["sha256"]) != _sha(selected)
                or text_value.encode() != selected
            ):
                _fail()
            spans[span_id] = SourceSpan(
                span_id, source_id, start, end, len(selected), cast(str, span["sha256"])
            )
    if observed_paths != EXACT_SOURCE_PATHS:
        _fail()

    propositions: dict[str, Proposition] = {}
    for proposition_value in proposition_rows:
        row = _object(proposition_value, {"propositionId", "statement", "sourceSpanIds"})
        proposition_id = _identifier(row["propositionId"], prefix="fact_")
        statement, span_ids = row["statement"], row["sourceSpanIds"]
        if (
            proposition_id in propositions
            or not isinstance(statement, str)
            or not 20 <= len(statement.encode()) <= 400
            or statement != statement.strip()
            or not isinstance(span_ids, list)
            or not 0 < len(span_ids) <= 8
        ):
            _fail()
        checked_spans = tuple(_identifier(item, prefix="src_") for item in span_ids)
        if len(set(checked_spans)) != len(checked_spans) or any(item not in spans for item in checked_spans):
            _fail()
        propositions[proposition_id] = Proposition(proposition_id, statement, checked_spans)

    mappings: list[ClaimMapping] = []
    used_propositions: set[str] = set()
    for index, mapping_value in enumerate(mapping_rows, start=1):
        row = _object(mapping_value, {"claimId", "claimSha256ByPresenter", "propositionIds"})
        claim_id = _identifier(row["claimId"], prefix="claim_")
        hashes, proposition_ids = row["claimSha256ByPresenter"], row["propositionIds"]
        if claim_id != f"claim_{index:03d}" or not isinstance(hashes, dict) or set(hashes) != set(PRESENTERS):
            _fail()
        checked_hashes = {presenter: _checksum(hashes[presenter]) for presenter in PRESENTERS}
        if not isinstance(proposition_ids, list) or not 0 < len(proposition_ids) <= 8:
            _fail()
        checked_ids = tuple(_identifier(item, prefix="fact_") for item in proposition_ids)
        if len(set(checked_ids)) != len(checked_ids) or any(item not in propositions for item in checked_ids):
            _fail()
        used_propositions.update(checked_ids)
        mappings.append(ClaimMapping(claim_id, checked_hashes, checked_ids))
    if used_propositions != set(propositions):
        _fail()
    return Cut1GroundingContract(
        CUT1_POLICY_VERSION,
        ACCEPTED_REVISION,
        _sha(raw),
        _sha(_canonical(authoritative)),
        spans,
        propositions,
        tuple(mappings),
    )


def evaluate_cut1_grounding(
    *,
    root: Path,
    tenant_id: str,
    project_id: str,
    run_id: str,
    candidate: GeneratedScript,
    retrieved_context: list[RetrievedContext],
    prompt: str,
    all_chunks: list[KnowledgeChunk],
) -> EvaluationResult:
    baseline = evaluate_grounding(
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        candidate=candidate,
        retrieved_context=retrieved_context,
        prompt=prompt,
        all_chunks=all_chunks,
    )
    try:
        contract = load_cut1_grounding_contract(root=root)
        if (
            len(candidate.claims) != len(contract.claim_mappings)
            or baseline.unsupported_claim_count != len(candidate.claims)
            or baseline.claim_supports
            or any(
                item.reason != "Claim text is not directly present in the cited retrieved chunk."
                for item in baseline.unsupported_claims
            )
            or any(claim.proposition_ids or claim.proposition_evidence_checksum for claim in candidate.claims)
        ):
            return baseline
        claim_hashes = [_sha(claim.text.encode()) for claim in candidate.claims]
        presenter = next(
            (
                presenter_id
                for presenter_id in PRESENTERS
                if all(
                    claim.claim_id == mapping.claim_id
                    and claim_hash == mapping.claim_sha256_by_presenter[presenter_id]
                    for claim, claim_hash, mapping in zip(
                        candidate.claims, claim_hashes, contract.claim_mappings, strict=True
                    )
                )
            ),
            None,
        )
        if presenter is None:
            return baseline
        chunks = {item.chunk_id: item for item in all_chunks}
        fact_checksum = "sha256:" + _sha(contract.project_source_bytes())
        supports: list[ClaimSupport] = []
        for claim, mapping in zip(candidate.claims, contract.claim_mappings, strict=True):
            if claim.chunk_id is None or not 0 < claim.citation_index <= len(retrieved_context):
                return baseline
            context = retrieved_context[claim.citation_index - 1]
            if (
                context.chunk != chunks.get(claim.chunk_id)
                or context.chunk.source_filename != FACTS_SOURCE_FILENAME
                or context.chunk.source_document_checksum != fact_checksum
                or (context.chunk.tenant_id, context.chunk.project_id) != (tenant_id, project_id)
            ):
                return baseline
            supports.append(
                ClaimSupport(
                    claim_support_id=f"claimsup_{len(supports) + 1:03d}",
                    claim_id=claim.claim_id,
                    context_ref_id=context.context_ref_id,
                    chunk_id=context.chunk.chunk_id,
                    document_id=context.chunk.document_id,
                    support_status="SUPPORTED",
                    support_score=1.0,
                    support_reason="All governed atomic propositions verified from immutable source spans.",
                    citation_index=claim.citation_index,
                    proposition_ids=mapping.proposition_ids,
                    proposition_evidence_checksum=contract.evidence_checksum(mapping),
                )
            )
        return replace(
            baseline,
            evaluation_status="PASSED",
            groundedness_score=1.0,
            faithfulness_score=1.0,
            unsupported_claim_count=0,
            unsupported_claims=[],
            claim_supports=supports,
            context_ref_coverage=1.0,
            policy_version=CUT1_POLICY_VERSION,
        )
    except (Cut1GroundingError, OSError, TypeError, ValueError):
        return baseline
