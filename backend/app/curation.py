"""Issue #302 A1 owner-curation policy and durable record types."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping

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
    source_version: str
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
    action: Literal["ACCEPT_FOR_REVIEW", "APPROVE"] = "ACCEPT_FOR_REVIEW"
    reason: str = "AWAITING_CURATOR_APPROVAL"
    decision_state: SourceDecisionState = "PENDING_REVIEW"
    raw_content_retained: bool = True
    created_at: str = ""
    approved_at: str | None = None


@dataclass(frozen=True)
class LegacySourceProjection:
    document_id: str
    source_contract: Literal["UNSEALED_LEGACY"] = "UNSEALED_LEGACY"
    h1_eligible: bool = False


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
    return (
        assertions.classification == "PUBLIC_SAFE"
        and assertions.provenance == "PROJECT_AUTHORED_SYNTHETIC"
        and assertions.rights_basis == "PROJECT_OWNED"
        and assertions.rights_status == "ELIGIBLE"
        and assertions.usage_policy == "LOCAL_TEST_REUSE_ALLOWED"
        and bool(assertions.source_version.strip())
    )
