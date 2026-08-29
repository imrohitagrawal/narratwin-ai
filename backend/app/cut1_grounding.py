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
    UnsupportedClaim,
)

CUT1_STYLE = "CUT1_ATOMIC_FACTS_V1"
CUT1_POLICY_VERSION = "cut1-atomic-grounding-v1"
CUT1_SCHEMA_VERSION = "cut1-project-facts-v1"
FACTS_RELATIVE_PATH = Path("docs/governance/cut1-project-facts-v1.json")
FACTS_SOURCE_FILENAME = "cut1-project-facts-v1.md"
ACCEPTED_REVISION = "a868137fab607ae75d4b272301e9fc52b898e15c"
EXPECTED_ASSET_SHA256 = "cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b"
MAX_CONTRACT_BYTES = 131_072
MAX_SOURCES = 16
MAX_SPANS = 64
MAX_PROPOSITIONS = 64
EXACT_REPOSITORY_SOURCES = {
    "README.md",
    "backend/app/stage4.py",
    "docs/AI_BUILD_BRIEF.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/PRD.md",
    "docs/PROJECT_AVATAR_PACK.md",
    "docs/STATUS.md",
    "docs/ADR/0054-cut1-presenter-registry.md",
    "docs/STAGE_ISSUE_PLAN.md",
}
OWNER_RECORDS = {
    "src_owner_5197711390": {
        "locator": "https://github.com/imrohitagrawal/narratwin-ai/issues/366#issuecomment-5197711390",
        "revision": "comment:5197711390@2026-08-05T21:41:25Z",
        "byteCount": 4322,
        "sha256": "30d6afe6758598f172c48a65d4d507662a9ab6eefebbcf492af07052c8e13528",
    },
    "src_owner_5263752038": {
        "locator": "https://github.com/imrohitagrawal/narratwin-ai/issues/421#issuecomment-5263752038",
        "revision": "comment:5263752038@2026-08-12T07:36:47Z",
        "byteCount": 2068,
        "sha256": "a797084c6f2d6c20ceb33deeb54e1dc7104a65e4adba49a8aa3f4b04ed8f5644",
    },
}
OWNER_RECORD_SPANS = {
    "src_owner_span_01": {
        "sourceId": "src_owner_5197711390",
        "byteStart": 170,
        "byteEnd": 520,
        "byteCount": 350,
        "sha256": "438d9f8e92240781e62472d39e75d8c28c72e20008ba9a82588c7a7f31ff99b2",
        "text": "- Visible brand spelling is exactly `StackClimb`; domain `stackclimb.com`. "
        "Rohit Agrawal is the founder, owner, product thinker, product owner, and producer. "
        "NarraTwin AI was conceived, is owned, and is produced by Rohit Agrawal under "
        "StackClimb. Do not use `®`, claim registration, public availability, deployment, "
        "release, or production readiness.",
    },
    "src_owner_421_stackclimb": {
        "sourceId": "src_owner_5263752038",
        "byteStart": 347, "byteEnd": 452, "byteCount": 105,
        "sha256": "4982c4c0b87481d71cb592d12df62faf30223324aba5d884024364b6baf249b7",
        "text": "“StackClimb is the technology and product innovation brand founded, owned, and led by Rohit Agrawal.”",
    },
    "src_owner_421_knowledge": {
        "sourceId": "src_owner_5263752038",
        "byteStart": 456, "byteEnd": 587, "byteCount": 131,
        "sha256": "0580768ac894641157cfa71776a919d5dc32a32c34ee8e7c71165921911e4a5b",
        "text": "“Complex projects often contain valuable knowledge spread across documents, code, architecture notes, and technical decisions.”",
    },
    "src_owner_421_meera": {
        "sourceId": "src_owner_5263752038",
        "byteStart": 591, "byteEnd": 678, "byteCount": 87,
        "sha256": "e15d32954d30cb1160ff942fc862ea33c8a70b254d42db56931c487bd4b08719",
        "text": "“For Cut 1, Meera is the selected presenter and presents the prepared walkthrough.”",
    },
}
PRESENTERS = ("meera", "myra", "raj")
SELECTED_PRESENTER = "meera"
SOURCE_CLASSIFICATIONS = {"OWNER_ASSERTED", "REPOSITORY_SOURCE"}
OWNER_DIRECT_CLAIMS = {"claim_003", "claim_005"}
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
ID_PATTERN = re.compile(r"(?:src|fact|claim)_[a-z0-9_]{1,64}\Z")
PREDICATE_PATTERN = re.compile(r"[a-z][a-z0-9_.]{2,80}\Z")
EXPECTED_REQUIRED_PREDICATES = (
    ("narratwin.platform",),
    ("presenter.identity", "presenter.downstream_role"),
    (
        "stackclimb.brand",
        "stackclimb.technology_context",
        "stackclimb.product_innovation_context",
        "stackclimb.founder.rohit",
        "stackclimb.owner.rohit",
        "stackclimb.lead.rohit",
    ),
    (
        "narratwin.conceived.rohit",
        "narratwin.owner.rohit",
        "narratwin.producer.rohit",
        "narratwin.under_stackclimb",
    ),
    (
        "knowledge.documents",
        "knowledge.code",
        "knowledge.architecture",
        "knowledge.technical_decisions",
    ),
    ("product.approved_input", "product.clear_guided_walkthrough"),
    ("product.approved_input",),
    ("flow.organize", "flow.retrieve", "product.audience_aware"),
    (
        "grounding.source_support",
        "grounding.context_refs",
        "grounding.evaluation",
        "grounding.no_unsupported_fact",
    ),
    (
        "application.python_fastapi_backend",
        "application.nextjs_ui",
        "application.rag",
        "application.evaluation_safety",
        "application.multilingual",
        "application.captions",
        "application.speech",
        "application.presenter_led_media",
    ),
    (
        "architecture.project_understanding_core",
        "architecture.modular_provider_boundaries",
        "architecture.technologies_evolve",
    ),
    ("reuse.other_projects",),
    (
        "reuse.approved_documentation",
        "reuse.tailored_explanation",
        "explanation.purpose",
        "explanation.architecture",
        "explanation.technologies",
        "explanation.capabilities",
        "explanation.decisions",
        "explanation.integrations",
    ),
    ("experience.prepared_walkthrough", "experience.first_mode", "presenter.selected_meera"),
    ("interactive.future", "interactive.not_current_demo"),
    (
        "experience.stackclimb_product",
        "experience.approved_knowledge",
        "experience.grounded",
        "experience.presenter_led",
    ),
    ("presenter.identity",),
    ("presenter.identity", "reuse.other_projects"),
)


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
    if (
        not isinstance(value, str)
        or ID_PATTERN.fullmatch(value) is None
        or not value.startswith(prefix)
    ):
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
    source_classification: str


@dataclass(frozen=True)
class Proposition:
    proposition_id: str
    statement: str
    predicate_ids: tuple[str, ...]
    source_span_ids: tuple[str, ...]
    source_classification: str


@dataclass(frozen=True)
class ClaimMapping:
    claim_id: str
    claim_sha256_by_presenter: Mapping[str, str]
    required_predicate_ids: tuple[str, ...]
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
                f"{item.proposition_id} [{item.source_classification}]: {item.statement}"
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
            "requiredPredicateIds": list(mapping.required_predicate_ids),
            "propositions": [
                {
                    "propositionId": proposition_id,
                    "predicateIds": list(self.propositions[proposition_id].predicate_ids),
                    "sourceClassification": self.propositions[proposition_id].source_classification,
                    "sourceSpans": [
                        {
                            "byteCount": self.spans[span_id].byte_count,
                            "byteEnd": self.spans[span_id].byte_end,
                            "byteStart": self.spans[span_id].byte_start,
                            "sha256": self.spans[span_id].sha256,
                            "sourceId": self.spans[span_id].source_id,
                            "sourceClassification": self.spans[span_id].source_classification,
                            "spanId": span_id,
                        }
                        for span_id in self.propositions[proposition_id].source_span_ids
                    ],
                    "statementSha256": _sha(self.propositions[proposition_id].statement.encode()),
                }
                for proposition_id in mapping.proposition_ids
            ],
        }
        return "sha256:" + _sha(_canonical(value))


def _read_contract(root: Path) -> tuple[bytes, dict[str, Any]]:
    target = root.resolve() / FACTS_RELATIVE_PATH
    try:
        if (
            target.is_symlink()
            or not target.is_file()
            or target.stat().st_size > MAX_CONTRACT_BYTES
        ):
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
        current = b"" if target.is_symlink() or not target.is_file() else target.read_bytes()
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


def load_cut1_grounding_contract(*, root: Path) -> Cut1GroundingContract:
    raw, authoritative = _read_contract(root)
    value = _object(
        authoritative,
        {
            "schemaVersion",
            "policyVersion",
            "acceptedRevision",
            "sources",
            "propositions",
            "claimMappings",
        },
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
    observed_repository_sources: set[str] = set()
    observed_owner_records: set[str] = set()
    observed_owner_spans: set[str] = set()
    for source_value in source_rows:
        source = _object(
            source_value,
            {
                "sourceId", "locatorType", "sourceClassification", "locator", "revision",
                "byteCount", "sha256", "spans",
            },
        )
        source_id = _identifier(source["sourceId"], prefix="src_")
        locator_type, locator = source["locatorType"], source["locator"]
        source_classification = source["sourceClassification"]
        if (
            source_id in source_ids
            or locator_type not in {"repository", "owner-record"}
            or source_classification not in SOURCE_CLASSIFICATIONS
            or (locator_type == "repository") != (source_classification == "REPOSITORY_SOURCE")
            or not isinstance(locator, str)
        ):
            _fail()
        source_ids.add(source_id)
        source_sha256 = _checksum(source["sha256"])
        source_bytes: bytes | None
        if locator_type == "repository":
            if (
                locator not in EXACT_REPOSITORY_SOURCES
                or str(PurePosixPath(locator)) != locator
                or source["revision"] != ACCEPTED_REVISION
            ):
                _fail()
            observed_repository_sources.add(locator)
            source_bytes = _immutable_source_bytes(root, locator, source_sha256)
            if source["byteCount"] != len(source_bytes) or source_sha256 != _sha(source_bytes):
                _fail()
        else:
            if (
                source_id in observed_owner_records
                or {
                    "locator": locator,
                    "revision": source["revision"],
                    "byteCount": source["byteCount"],
                    "sha256": source_sha256,
                }
                != OWNER_RECORDS.get(source_id)
            ):
                _fail()
            observed_owner_records.add(source_id)
            source_bytes = None
        if not isinstance(source["spans"], list) or not 0 < len(source["spans"]) <= MAX_SPANS:
            _fail()
        for span_value in source["spans"]:
            span = _object(
                span_value, {"spanId", "byteStart", "byteEnd", "byteCount", "sha256", "text"}
            )
            span_id = _identifier(span["spanId"], prefix="src_")
            source_size = cast(int, source["byteCount"])
            start = _bounded_int(span["byteStart"], maximum=source_size)
            end = _bounded_int(span["byteEnd"], maximum=source_size)
            text_value = span["text"]
            if span_id in spans or end <= start or not isinstance(text_value, str):
                _fail()
            if source_bytes is None:
                expected_owner_span = OWNER_RECORD_SPANS.get(span_id)
                if (
                    expected_owner_span is None
                    or {
                        "sourceId": source_id,
                        "byteStart": start,
                        "byteEnd": end,
                        "byteCount": span["byteCount"],
                        "sha256": span["sha256"],
                        "text": text_value,
                    }
                    != expected_owner_span
                ):
                    _fail()
                observed_owner_spans.add(span_id)
            selected = source_bytes[start:end] if source_bytes is not None else text_value.encode()
            if (
                len(selected) != end - start
                or span["byteCount"] != len(selected)
                or _checksum(span["sha256"]) != _sha(selected)
                or text_value.encode() != selected
            ):
                _fail()
            spans[span_id] = SourceSpan(
                span_id, source_id, start, end, len(selected), cast(str, span["sha256"]),
                cast(str, source_classification),
            )
    if (
        observed_repository_sources != EXACT_REPOSITORY_SOURCES
        or observed_owner_records != set(OWNER_RECORDS)
        or observed_owner_spans != set(OWNER_RECORD_SPANS)
    ):
        _fail()

    propositions: dict[str, Proposition] = {}
    for proposition_value in proposition_rows:
        row = _object(
            proposition_value,
            {"propositionId", "statement", "predicateIds", "sourceSpanIds"},
        )
        proposition_id = _identifier(row["propositionId"], prefix="fact_")
        statement, predicate_ids, span_ids = (
            row["statement"],
            row["predicateIds"],
            row["sourceSpanIds"],
        )
        if (
            proposition_id in propositions
            or not isinstance(statement, str)
            or not 20 <= len(statement.encode()) <= 400
            or statement != statement.strip()
            or not isinstance(predicate_ids, list)
            or not 0 < len(predicate_ids) <= 16
            or not isinstance(span_ids, list)
            or not 0 < len(span_ids) <= 8
        ):
            _fail()
        checked_predicates = tuple(predicate_ids)
        if len(set(checked_predicates)) != len(checked_predicates) or any(
            not isinstance(item, str) or PREDICATE_PATTERN.fullmatch(item) is None
            for item in checked_predicates
        ):
            _fail()
        checked_spans = tuple(_identifier(item, prefix="src_") for item in span_ids)
        if len(set(checked_spans)) != len(checked_spans) or any(
            item not in spans for item in checked_spans
        ):
            _fail()
        source_classifications = {spans[item].source_classification for item in checked_spans}
        if len(source_classifications) != 1:
            _fail()
        propositions[proposition_id] = Proposition(
            proposition_id, statement, checked_predicates, checked_spans,
            next(iter(source_classifications)),
        )

    mappings: list[ClaimMapping] = []
    used_propositions: set[str] = set()
    for index, mapping_value in enumerate(mapping_rows, start=1):
        row = _object(
            mapping_value,
            {"claimId", "claimSha256ByPresenter", "requiredPredicateIds", "propositionIds"},
        )
        claim_id = _identifier(row["claimId"], prefix="claim_")
        hashes = row["claimSha256ByPresenter"]
        required_predicates = row["requiredPredicateIds"]
        proposition_ids = row["propositionIds"]
        if (
            claim_id != f"claim_{index:03d}"
            or not isinstance(hashes, dict)
            or set(hashes) != set(PRESENTERS)
        ):
            _fail()
        checked_hashes = {presenter: _checksum(hashes[presenter]) for presenter in PRESENTERS}
        if (
            not isinstance(required_predicates, list)
            or not 0 < len(required_predicates) <= 32
            or not isinstance(proposition_ids, list)
            or not 0 < len(proposition_ids) <= 8
        ):
            _fail()
        checked_required = tuple(required_predicates)
        if (
            checked_required != EXPECTED_REQUIRED_PREDICATES[index - 1]
            or len(set(checked_required)) != len(checked_required)
            or any(
                not isinstance(item, str) or PREDICATE_PATTERN.fullmatch(item) is None
                for item in checked_required
            )
        ):
            _fail()
        checked_ids = tuple(_identifier(item, prefix="fact_") for item in proposition_ids)
        supplied_predicates = (
            {
                predicate
                for proposition_id in checked_ids
                for predicate in propositions[proposition_id].predicate_ids
            }
            if all(item in propositions for item in checked_ids)
            else set()
        )
        if (
            len(set(checked_ids)) != len(checked_ids)
            or any(item not in propositions for item in checked_ids)
            or not set(checked_required).issubset(supplied_predicates)
            or any(
                not set(propositions[item].predicate_ids).intersection(checked_required)
                for item in checked_ids
            )
        ):
            _fail()
        used_propositions.update(checked_ids)
        mappings.append(ClaimMapping(claim_id, checked_hashes, checked_required, checked_ids))
    if used_propositions != set(propositions):
        _fail()
    from backend.app.narration import canonical_presenter_text

    canonical_hashes = {
        presenter: tuple(
            _sha(item.group(0).encode())
            for item in re.finditer(
                r"\S.*?[.!?](?=\s|$)", canonical_presenter_text(presenter), re.DOTALL
            )
        )
        for presenter in PRESENTERS
    }
    if any(
        len(canonical_hashes[presenter]) != len(mappings)
        or any(
            mapping.claim_sha256_by_presenter[presenter] != canonical_hashes[presenter][index]
            for index, mapping in enumerate(mappings)
        )
        for presenter in PRESENTERS
    ):
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
    failed = replace(
        baseline,
        evaluation_status="FAILED",
        groundedness_score=0.0,
        faithfulness_score=0.0,
        unsupported_claim_count=len(candidate.claims),
        unsupported_claims=[
            UnsupportedClaim(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                reason="The governed Cut 1 atomic grounding contract was not satisfied.",
            )
            for claim in candidate.claims
        ],
        claim_supports=[],
        context_ref_coverage=0.0,
        policy_version=CUT1_POLICY_VERSION,
    )
    try:
        contract = load_cut1_grounding_contract(root=root)
        baseline_supported = {support.claim_id for support in baseline.claim_supports}
        if (
            len(candidate.claims) != len(contract.claim_mappings)
            or baseline.unsupported_claim_count != len(candidate.claims) - len(OWNER_DIRECT_CLAIMS)
            or baseline_supported != OWNER_DIRECT_CLAIMS
            or any(
                item.reason != "Claim text is not directly present in the cited retrieved chunk."
                for item in baseline.unsupported_claims
            )
            or any(
                claim.proposition_ids or claim.proposition_evidence_checksum
                for claim in candidate.claims
            )
        ):
            return failed
        claim_hashes = [_sha(claim.text.encode()) for claim in candidate.claims]
        matching_presenters = tuple(
            presenter
            for presenter in PRESENTERS
            if all(
                claim.claim_id == mapping.claim_id
                and claim_hash == mapping.claim_sha256_by_presenter[presenter]
                for claim, claim_hash, mapping in zip(
                    candidate.claims, claim_hashes, contract.claim_mappings, strict=True
                )
            )
        )
        if len(matching_presenters) != 1:
            return failed
        chunks = {item.chunk_id: item for item in all_chunks}
        fact_checksum = "sha256:" + _sha(contract.project_source_bytes())
        supports: list[ClaimSupport] = []
        for claim, mapping in zip(candidate.claims, contract.claim_mappings, strict=True):
            if claim.chunk_id is None or not 0 < claim.citation_index <= len(retrieved_context):
                return failed
            context = retrieved_context[claim.citation_index - 1]
            if (
                context.chunk != chunks.get(claim.chunk_id)
                or context.chunk.source_filename != FACTS_SOURCE_FILENAME
                or context.chunk.source_document_checksum != fact_checksum
                or (context.chunk.tenant_id, context.chunk.project_id) != (tenant_id, project_id)
            ):
                return failed
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
        return failed
