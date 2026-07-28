"""Issue #302 A1 owner-curation policy and durable record types."""
from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass
from collections.abc import Callable, Mapping
from typing import Any, Literal
CURATION_SCHEMA_VERSION = "source-curation-v1"
CURATION_POLICY_VERSION = "source-curation-policy-v1"
SourceDecisionState = Literal["PENDING_REVIEW", "APPROVED", "EXCLUDED"]
@dataclass(frozen=True)
class SourceAssertions:
    classification: str
    provenance: str
    rights_basis: str
    rights_status: str
    usage_policy: str
    source_version: str
@dataclass
class SourceRecord:
    source_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    source_filename: str
    content_type: str
    size_bytes: int
    checksum: str
    text: str
    assertions: SourceAssertions
    assertions_fingerprint: str
    ingestion_status: Literal["NOT_STARTED", "INGESTED"] = "NOT_STARTED"
    created_at: str = ""
    ingested_at: str | None = None
@dataclass
class SourceDecisionRecord:
    decision_id: str
    source_id: str
    tenant_id: str
    actor_id: str
    project_id: str
    checksum: str
    source_version: str
    assertions_fingerprint: str
    policy_version: str = CURATION_POLICY_VERSION
    server_decision: Literal["ALLOW"] = "ALLOW"
    action: Literal["ACCEPT_FOR_REVIEW", "APPROVE"] = "ACCEPT_FOR_REVIEW"
    reason: str = "AWAITING_CURATOR_APPROVAL"
    decision_state: SourceDecisionState = "PENDING_REVIEW"
    raw_content_retained: bool = True
    created_at: str = ""
    approved_at: str | None = None
@dataclass(frozen=True)
class CuratedOutcome:
    code: str
    source: SourceRecord
    decision: SourceDecisionRecord
    idempotency_replayed: bool = False
def canonical_digest(values: Mapping[str, Any]) -> str:
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
def assertions_digest(assertions: SourceAssertions) -> str:
    return canonical_digest(asdict(assertions))
def allowed_for_review(assertions: SourceAssertions) -> bool:
    return (assertions.classification, assertions.provenance, assertions.rights_basis,
            assertions.rights_status, assertions.usage_policy) == (
            "PUBLIC_SAFE", "PROJECT_AUTHORED_SYNTHETIC", "PROJECT_OWNED", "ELIGIBLE",
            "LOCAL_TEST_REUSE_ALLOWED") and 0 < len(assertions.source_version.strip()) <= 128

def source_assertions(source: SourceRecord) -> SourceAssertions:
    return source.assertions

def legal_pair(source: SourceRecord, decision: SourceDecisionRecord) -> bool:
    identity = (decision.source_id, decision.tenant_id, decision.actor_id, decision.project_id,
                decision.checksum, decision.source_version, decision.assertions_fingerprint)
    expected = (source.source_id, source.tenant_id, source.owner_id, source.project_id,
                source.checksum, source.assertions.source_version, source.assertions_fingerprint)
    state = (decision.decision_state, decision.action, decision.reason, decision.approved_at is not None)
    return identity == expected and decision.raw_content_retained and decision.server_decision == "ALLOW" and decision.policy_version == CURATION_POLICY_VERSION and allowed_for_review(source_assertions(source)) and source.assertions_fingerprint == assertions_digest(source_assertions(source)) and state in {("PENDING_REVIEW", "ACCEPT_FOR_REVIEW", "AWAITING_CURATOR_APPROVAL", False), ("APPROVED", "APPROVE", "CURATOR_APPROVED_POLICY_VERIFIED", True)} and (decision.decision_state == "APPROVED" or source.ingestion_status == "NOT_STARTED")

def restore_curated(source_rows: list[Any], decision_rows: list[Any], projects: Mapping[str, Any],
                    source_valid: Callable[[SourceRecord], bool]) -> tuple[dict[str, SourceRecord], dict[str, SourceDecisionRecord]]:
    sources: dict[str, SourceRecord] = {}
    for row in source_rows:
        try:
            payload = dict(row)
            payload["assertions"] = SourceAssertions(**payload["assertions"])
            source = SourceRecord(**payload)
        except (KeyError, TypeError, ValueError):
            continue
        project = projects.get(source.project_id)
        if project and (project.tenant_id, project.owner_id) == (source.tenant_id, source.owner_id) and source.checksum == hashlib.sha256(source.text.encode()).hexdigest() and source.size_bytes == len(source.text.encode()) and source.ingestion_status in {"NOT_STARTED", "INGESTED"} and source_valid(source):
            sources[source.source_id] = source
    decisions: dict[str, SourceDecisionRecord] = {}
    for row in decision_rows:
        try:
            decision = SourceDecisionRecord(**row)
        except (KeyError, TypeError, ValueError):
            continue
        restored_source = sources.get(decision.source_id)
        if restored_source and legal_pair(restored_source, decision) and not any(value.source_id == decision.source_id for value in decisions.values()):
            decisions[decision.decision_id] = decision
    linked = {decision.source_id for decision in decisions.values()}
    return {key: value for key, value in sources.items() if key in linked}, decisions
