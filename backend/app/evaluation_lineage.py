from __future__ import annotations

import hashlib
import json
import math
import re
from decimal import Decimal
from typing import Any, Mapping, cast

from backend.app.rag.chunking import checksum_text
from backend.app.rag import models as rag
from backend.app.stage4 import WalkthroughRunRecord, evaluation_to_api

CHECKSUM_SCHEMA = "stage7-source-evaluation-checksum-v2"
RETRIEVAL_POLICY: dict[str, Any] = {"belowThresholdBackfill": False, "computedEvidenceScoresOnly": True,
    "fallback": {"crossProjectExpansion": False, "mode": "deterministic keyword overlap",
                 "scope": "bound tenantId/projectId"},
    "maximumChunksPerDocument": 3, "minimumDistinctDocuments": 1, "minimumRetrievedChunks": 1,
    "minimumScoreComparison": "inclusive-gte", "minimumScoreThreshold": "0.72", "topK": 6, "version": "stage4-rag-v1",
    "refusalReasons": ["EMPTY_CONTEXT", "LOW_RETRIEVAL_CONFIDENCE", "AMBIGUOUS_CONTEXT",
                       "CROSS_PROJECT_CONTEXT", "UNSAFE_CONTEXT"],
    "syntheticEligibilityScoresAllowed": False, "terminalRefusalBeforeGeneration": True,
    "tieBreakOrder": ["score desc", "approved_at desc", "chunk_index asc", "chunk_id asc"],
}
ROOT_KEYS = {"checksumSchema", "evaluation", "retrievalPolicy", "scope", "selectedContext", "sourceCitationIndexes"}
GROUNDING_EVIDENCE_KEYS = {"checksum", "claims", "policyVersion"}
GROUNDING_CLAIM_KEYS = {"claimId", "propositionEvidenceChecksum", "propositionIds"}
CONTEXT_KEYS = {"approvedAt", "chunkChecksum", "chunkId", "chunkIndex", "chunkingStrategyVersion",
                "contextRefId", "documentId", "projectId", "retrievalScore", "snapshotChecksum",
                "sourceDocumentChecksum", "tenantId"}


def _identifier(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or re.search(r"[\x00-\x1f\x7f]", value):
        raise ValueError("Evaluation lineage identifier is invalid.")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_score(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("Retrieval score must be finite binary64.")
    number = float(value)
    if not 0 <= number <= 1:
        raise ValueError("Retrieval score is outside [0,1].")
    fixed = "0" if number == 0 else format(Decimal(repr(number)), "f")
    return fixed.rstrip("0").rstrip(".") if "." in fixed else fixed


def canonical_stage4_checksum(value: object) -> str:
    digest = _identifier(value).removeprefix("sha256:")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "Invalid checksum.")
    return "sha256:" + digest


def validate_evaluation_lineage_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    value = dict(payload)
    evaluation = cast(dict[str, object], value.get("evaluation"))
    scope = cast(dict[str, object], value.get("scope"))
    contexts = cast(list[dict[str, object]], value.get("selectedContext"))
    citations = cast(list[object], value.get("sourceCitationIndexes"))
    _require(
        set(value) in {frozenset(ROOT_KEYS), frozenset(ROOT_KEYS | {"groundingEvidence"})}
        and value.get("checksumSchema") == CHECKSUM_SCHEMA,
        "Noncanonical lineage root.",
    )
    keys = {"evaluationId", "runId", "status", "traceId"}
    _require(
        isinstance(evaluation, dict) and set(evaluation) == keys,
        "Evaluation lineage identity is noncanonical.",
    )
    _require(
        evaluation.get("status") in {"PASSED", "FAILED", "UNKNOWN"},
        "Evaluation lineage status is invalid.",
    )
    for key in ("evaluationId", "runId", "traceId"):
        _identifier(evaluation.get(key))
    _require(
        isinstance(scope, dict) and set(scope) == {"tenantId", "projectId"},
        "Lineage scope is noncanonical.",
    )
    tenant_id, project_id = _identifier(scope.get("tenantId")), _identifier(scope.get("projectId"))
    _require(
        value.get("retrievalPolicy") == RETRIEVAL_POLICY and isinstance(contexts, list),
        "Noncanonical policy.",
    )
    _require(len(contexts) <= rag.RETRIEVAL_TOP_K, "Evaluation lineage exceeds frozen topK.")
    identities: dict[str, set[str]] = {"refs": set(), "chunks": set()}
    documents: dict[str, int] = {}
    for row in contexts:
        _require(
            isinstance(row, dict) and set(row) == CONTEXT_KEYS,
            "Selected-context evidence is noncanonical.",
        )
        _require(
            (row.get("tenantId"), row.get("projectId")) == (tenant_id, project_id),
            "Context crosses scope.",
        )
        ref, chunk, document = (
            _identifier(row.get(key)) for key in ("contextRefId", "chunkId", "documentId")
        )
        _require(
            ref not in identities["refs"] and chunk not in identities["chunks"],
            "Duplicate context identity.",
        )
        identities["refs"].add(ref)
        identities["chunks"].add(chunk)
        documents[document] = documents.get(document, 0) + 1
        _require(
            documents[document] <= rag.RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT, "Document cap exceeded."
        )
        _require(
            type(row.get("chunkIndex")) is int and cast(int, row["chunkIndex"]) >= 0,
            "Chunk index is invalid.",
        )
        _require(
            row.get("chunkingStrategyVersion") == rag.CHUNKING_STRATEGY_VERSION,
            "Invalid chunking version.",
        )
        raw_score = row.get("retrievalScore")
        _require(isinstance(raw_score, str), "Bad score encoding.")
        score = cast(str, raw_score)
        _require(
            score == canonical_score(float(score)) and float(score) >= rag.RETRIEVAL_MIN_SCORE,
            "Bad score.",
        )
        _identifier(row.get("approvedAt"))
        checksums = (
            row.get(key) for key in ("chunkChecksum", "snapshotChecksum", "sourceDocumentChecksum")
        )
        _require(
            all(canonical_stage4_checksum(item) == item for item in checksums),
            "Invalid checksum.",
        )
    _require(
        evaluation["status"] != "PASSED" or bool(contexts),
        "Passed lineage requires selected evidence.",
    )
    _require(
        isinstance(citations, list) and all(type(i) is int and i > 0 for i in citations),
        "Bad citations.",
    )
    grounding = value.get("groundingEvidence")
    if grounding is not None:
        _require(
            isinstance(grounding, dict)
            and set(grounding) == GROUNDING_EVIDENCE_KEYS
            and grounding.get("policyVersion") == "cut1-atomic-grounding-v1",
            "Noncanonical grounding evidence.",
        )
        grounding_row = cast(dict[str, object], grounding)
        claims = grounding_row.get("claims")
        _require(isinstance(claims, list) and len(claims) == len(citations) > 0, "Bad grounding claims.")
        claim_rows = cast(list[object], claims)
        claim_ids: set[str] = set()
        for claim in claim_rows:
            _require(isinstance(claim, dict) and set(claim) == GROUNDING_CLAIM_KEYS, "Bad grounding claim.")
            claim_row = cast(dict[str, object], claim)
            claim_id = _identifier(claim_row.get("claimId"))
            propositions = claim_row.get("propositionIds")
            _require(
                claim_id not in claim_ids
                and isinstance(propositions, list)
                and 0 < len(propositions) <= 8
                and len(set(propositions)) == len(propositions)
                and all(isinstance(item, str) and re.fullmatch(r"fact_[0-9]{3}", item) for item in propositions),
                "Bad grounding propositions.",
            )
            claim_ids.add(claim_id)
            canonical_stage4_checksum(claim_row.get("propositionEvidenceChecksum"))
        projection = json.dumps(claim_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        _require(grounding_row.get("checksum") == checksum_text(projection), "Bad grounding evidence checksum.")
    return cast(
        dict[str, Any],
        json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)),
    )


def build_source_evaluation_checksum(lineage_payload: Mapping[str, object], /) -> str:
    canonical = validate_evaluation_lineage_payload(lineage_payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def derive_evaluation_lineage(run: WalkthroughRunRecord) -> dict[str, Any]:
    ev = run.evaluation
    _require((run.status, run.failure_reason, run.evaluation_status) == ("COMPLETED", None, "PASSED"), "Invalid run.")
    if ev is None or ev.evaluation_status != "PASSED" or ev.unsupported_claims:
        raise ValueError("Stage 4 evaluation is missing, refused, or invalid.")
    _require((ev.run_id, ev.tenant_id, ev.project_id) == (run.run_id, run.tenant_id, run.project_id), "Bad identity.")
    frozen = (rag.RETRIEVAL_STRATEGY_VERSION, rag.RETRIEVAL_TOP_K, rag.RETRIEVAL_MIN_SCORE)
    fields = ("retrieval_strategy_version", "retrieval_top_k", "retrieval_score_threshold")
    _require(all(tuple(getattr(item, key) for key in fields) == frozen for item in (run, ev)), "Policy mismatch.")
    api_contexts = {row["contextRefId"]: row for row in evaluation_to_api(ev, run)["contextRefs"]}
    selected: list[dict[str, object]] = []
    for context in run.retrieved_context:
        snapshot = dict(api_contexts[context.context_ref_id]["evidenceSnapshot"])
        stored = snapshot.pop("snapshotChecksum")
        _require(stored == checksum_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":"))), "Bad snapshot.")
        row = {key: snapshot[key] for key in CONTEXT_KEYS if key in snapshot}
        row["sourceDocumentChecksum"] = canonical_stage4_checksum(row["sourceDocumentChecksum"])
        row.update(approvedAt=context.chunk.approved_at, contextRefId=context.context_ref_id,
                   retrievalScore=canonical_score(context.score), snapshotChecksum=stored)
        selected.append(row)
    payload = {"checksumSchema": CHECKSUM_SCHEMA,
               "evaluation": {"evaluationId": ev.evaluation_id, "runId": run.run_id,
                              "status": run.evaluation_status, "traceId": run.trace_id},
               "retrievalPolicy": RETRIEVAL_POLICY,
               "scope": {"projectId": run.project_id, "tenantId": run.tenant_id},
               "selectedContext": selected,
               "sourceCitationIndexes": [support.citation_index for support in ev.claim_supports]}
    if ev.policy_version == "cut1-atomic-grounding-v1":
        claims = [
            {
                "claimId": support.claim_id,
                "propositionEvidenceChecksum": support.proposition_evidence_checksum,
                "propositionIds": list(support.proposition_ids),
            }
            for support in ev.claim_supports
        ]
        _require(
            all(item["propositionIds"] and item["propositionEvidenceChecksum"] for item in claims),
            "Cut 1 grounding evidence is incomplete.",
        )
        projection = json.dumps(claims, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["groundingEvidence"] = {
            "checksum": checksum_text(projection),
            "claims": claims,
            "policyVersion": ev.policy_version,
        }
    return validate_evaluation_lineage_payload(payload)
