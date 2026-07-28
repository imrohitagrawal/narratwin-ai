"""Issue #302 A1 owner-curation policy and durable record types."""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from collections.abc import Callable, Collection, Mapping
from typing import Any, Literal, TypeVar
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
T = TypeVar("T")
def restored_records(rows: object, identity_field: str, decode: Callable[[dict[str, Any]], T],
                     valid: Callable[[T], bool]) -> dict[str, T]:
    if not isinstance(rows, list):
        return {}
    identities = [row.get(identity_field) for row in rows if isinstance(row, dict)]
    restored: dict[str, T] = {}
    for row in rows:
        try:
            value = decode(dict(row))
            identity = getattr(value, identity_field)
            if isinstance(identity, str) and identities.count(identity) == 1 and valid(value):
                restored[identity] = value
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return restored
def record_is_valid(value: T, valid: Callable[[T], bool]) -> bool:
    try:
        return valid(value)
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
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
def canonical_record_id(value: object, prefix: str) -> bool:
    return isinstance(value, str) and re.match(rf"^{prefix}_[0-9]{{6}}$", value) is not None and value != f"{prefix}_000000"
def legal_pair(source: SourceRecord, decision: SourceDecisionRecord) -> bool:
    identity = (decision.source_id, decision.tenant_id, decision.actor_id, decision.project_id,
                decision.checksum, decision.source_version, decision.assertions_fingerprint)
    expected = (source.source_id, source.tenant_id, source.owner_id, source.project_id,
                source.checksum, source.assertions.source_version, source.assertions_fingerprint)
    state = (decision.decision_state, decision.action, decision.reason, decision.approved_at is not None)
    return isinstance(source.assertions, SourceAssertions) and all(isinstance(value, str) for value in (source.source_id, source.tenant_id, source.owner_id, source.project_id, source.source_filename, source.content_type, source.checksum, source.text, source.assertions_fingerprint, source.ingestion_status, source.created_at, source.assertions.classification, source.assertions.provenance, source.assertions.rights_basis, source.assertions.rights_status, source.assertions.usage_policy, source.assertions.source_version, decision.decision_id, decision.source_id, decision.tenant_id, decision.actor_id, decision.project_id, decision.checksum, decision.source_version, decision.assertions_fingerprint, decision.policy_version, decision.server_decision, decision.action, decision.reason, decision.decision_state, decision.created_at)) and isinstance(source.size_bytes, int) and not isinstance(source.size_bytes, bool) and isinstance(decision.raw_content_retained, bool) and (source.ingested_at is None or isinstance(source.ingested_at, str)) and (decision.approved_at is None or isinstance(decision.approved_at, str)) and canonical_record_id(source.source_id, "source") and canonical_record_id(decision.decision_id, "decision") and identity == expected and decision.raw_content_retained and decision.server_decision == "ALLOW" and decision.policy_version == CURATION_POLICY_VERSION and allowed_for_review(source_assertions(source)) and source.assertions_fingerprint == assertions_digest(source_assertions(source)) and state in (("PENDING_REVIEW", "ACCEPT_FOR_REVIEW", "AWAITING_CURATOR_APPROVAL", False), ("APPROVED", "APPROVE", "CURATOR_APPROVED_POLICY_VERIFIED", True)) and (decision.decision_state == "APPROVED" or source.ingestion_status == "NOT_STARTED")
def restore_curated(source_rows: object, decision_rows: object, projects: Mapping[str, Any],
                    source_valid: Callable[[SourceRecord], bool], legacy_document_ids: Collection[str]) -> tuple[dict[str, SourceRecord], dict[str, SourceDecisionRecord]]:
    source_rows = source_rows if isinstance(source_rows, list) else []
    decision_rows = decision_rows if isinstance(decision_rows, list) else []
    sources: dict[str, SourceRecord] = {}
    source_ids = [row.get("source_id") for row in source_rows if isinstance(row, dict)]
    for row in source_rows:
        try:
            payload = dict(row)
            payload["assertions"] = SourceAssertions(**payload["assertions"])
            source = SourceRecord(**payload)
        except (KeyError, TypeError, ValueError):
            continue
        project = projects.get(source.project_id) if isinstance(source.project_id, str) else None
        if source.source_id not in legacy_document_ids and source_ids.count(source.source_id) == 1 and all(isinstance(value, str) for value in (source.source_id, source.tenant_id, source.owner_id, source.project_id, source.source_filename, source.content_type, source.checksum, source.text, source.assertions_fingerprint, source.ingestion_status, source.created_at, source.assertions.classification, source.assertions.provenance, source.assertions.rights_basis, source.assertions.rights_status, source.assertions.usage_policy, source.assertions.source_version)) and isinstance(source.size_bytes, int) and not isinstance(source.size_bytes, bool) and (source.ingested_at is None or isinstance(source.ingested_at, str)) and project and (project.tenant_id, project.owner_id) == (source.tenant_id, source.owner_id) and source.checksum == hashlib.sha256(source.text.encode()).hexdigest() and source.size_bytes == len(source.text.encode()) and source.ingestion_status in {"NOT_STARTED", "INGESTED"} and source_valid(source):
            sources[source.source_id] = source
    decisions: dict[str, SourceDecisionRecord] = {}
    decision_ids = [row.get("decision_id") for row in decision_rows if isinstance(row, dict)]
    decision_source_ids = [row.get("source_id") for row in decision_rows if isinstance(row, dict)]
    for row in decision_rows:
        try:
            decision = SourceDecisionRecord(**row)
        except (KeyError, TypeError, ValueError):
            continue
        restored_source = sources.get(decision.source_id) if isinstance(decision.source_id, str) else None
        if decision_ids.count(decision.decision_id) == decision_source_ids.count(decision.source_id) == 1 and all(isinstance(value, str) for value in (decision.decision_id, decision.source_id, decision.tenant_id, decision.actor_id, decision.project_id, decision.checksum, decision.source_version, decision.assertions_fingerprint, decision.policy_version, decision.server_decision, decision.action, decision.reason, decision.decision_state, decision.created_at)) and isinstance(decision.raw_content_retained, bool) and (decision.approved_at is None or isinstance(decision.approved_at, str)) and restored_source and legal_pair(restored_source, decision) and not any(value.source_id == decision.source_id for value in decisions.values()):
            decisions[decision.decision_id] = decision
    linked = {decision.source_id for decision in decisions.values()}
    return {key: value for key, value in sources.items() if key in linked}, decisions
