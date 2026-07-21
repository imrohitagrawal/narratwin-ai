"""Local-only hosted-demo access, quota, retention, and disclosure boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, Literal
from urllib.parse import unquote
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

HOSTED_DEMO_DISCLOSURE_VERSION = "hosted-demo-disclosure-v1"
HOSTED_DEMO_ALLOWED_DISCLOSURE_TEXT = (
    "AI-generated demo using local mock providers; no cloned identity or real provider call."
)
MAX_HOSTED_DEMO_ARTIFACT_BYTES = 10_000_000
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
CHECKSUM_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
SAFE_FILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_URL_PATTERN = re.compile(
    r"https?://|www\.|^//|javascript\s*:|data\s*:|ftp\s*:|file\s*:",
    re.IGNORECASE,
)
PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "reveal provider keys",
    "system prompt",
    "developer message",
    "jailbreak",
    "<script",
)
RAW_OUTPUT_MARKERS = (
    "raw prompt",
    "raw script",
    "source script text",
    "translated script text",
    "sourcescripttext",
    "translatedscripttext",
    "contentbase64",
    "provider payload",
    "media bytes",
)
CLONED_IDENTITY_MARKERS = (
    "using cloned identity",
    "with cloned identity",
    "cloned face",
    "cloned voice",
    "digital twin",
    "real-person likeness",
    "real person likeness",
    "replica profile",
)
ARTIFACT_MIME_BY_SUFFIX = {
    ".html": "text/html",
    ".json": "application/json",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".vtt": "text/vtt",
}

ErrorDetailValue = str | int | float | bool


class HostedDemoError(Exception):
    """Structured hosted-demo error safe for API exposure."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, ErrorDetailValue] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class HostedDemoJsonError(ValueError):
    """JSON parsing error with a stable client-safe code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def hash_hosted_demo_secret(secret: str) -> str:
    return "sha256:" + hashlib.sha256(secret.encode("utf-8")).hexdigest()


def stable_checksum(parts: tuple[object, ...]) -> str:
    payload = json.dumps(parts, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_hosted_demo_evaluation_checksum(
    *,
    tenant_id: str,
    project_id: str,
    actor_id: str,
    source_run_id: str,
    trace_id: str,
    language: str,
    audience: str,
    script_checksum: str,
    evaluation_id: str,
    evaluation_status: str,
    citation_refs: tuple[str, ...],
    citation_indexes: tuple[int, ...],
    multilingual_run_id: str | None = None,
    translated_script_checksum: str | None = None,
    subtitles_checksum: str | None = None,
    voice_manifest_checksum: str | None = None,
    tts_audio_checksum: str | None = None,
    avatar_render_id: str | None = None,
    avatar_video_provider_metadata_checksum: str | None = None,
) -> str:
    return stable_checksum(
        (
            "hosted-demo-evaluation-v1",
            tenant_id,
            project_id,
            actor_id,
            source_run_id,
            trace_id,
            language,
            audience,
            script_checksum,
            evaluation_id,
            evaluation_status,
            citation_refs,
            citation_indexes,
            multilingual_run_id,
            translated_script_checksum,
            subtitles_checksum,
            voice_manifest_checksum,
            tts_audio_checksum,
            avatar_render_id,
            avatar_video_provider_metadata_checksum,
        )
    )


def build_hosted_demo_artifact_checksum(
    *,
    artifact_id: str,
    artifact_kind: str,
    artifact_file_name: str,
    source_run_id: str,
    script_checksum: str,
    evaluation_checksum: str,
    disclosure_version: str,
) -> str:
    return stable_checksum(
        (
            "hosted-demo-artifact-v1",
            artifact_id,
            artifact_kind,
            artifact_file_name,
            source_run_id,
            script_checksum,
            evaluation_checksum,
            disclosure_version,
        )
    )


def build_hosted_demo_session_binding_hash(
    *,
    tenant_id: str,
    invite_id: str,
    session_id: str,
    session_secret: str,
) -> str:
    return stable_checksum(
        (
            "hosted-demo-session-binding-v1",
            tenant_id,
            invite_id,
            session_id,
            session_secret,
        )
    )


def _isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def build_hosted_demo_tombstone_checksum(
    *,
    request: HostedDemoAccessRequest,
    deleted_at: datetime,
) -> str:
    return stable_checksum(
        (
            "hosted-demo-tombstone-v1",
            request.artifact.artifact_id,
            request.artifact.artifact_kind,
            request.artifact.artifact_checksum,
            request.source.tenant_id,
            request.source.project_id,
            request.source.actor_id,
            request.source.source_run_id,
            request.source.trace_id,
            request.source.script_checksum,
            request.source.evaluation_checksum,
            request.retention.retention_record_id,
            request.retention.retention_state,
            request.retention.deletion_state,
            _isoformat_utc(request.retention.deletion_requested_at),
            _isoformat_utc(deleted_at),
            request.retention.provider_deletion_status,
            request.retention.local_only_provider_evidence,
        )
    )


def build_hosted_demo_tombstone_id(tombstone_checksum: str) -> str:
    return "tombstone_" + tombstone_checksum[7:23]


def build_hosted_demo_deletion_evidence_id(tombstone_checksum: str) -> str:
    return "deletion_evidence_" + tombstone_checksum[7:23]


def parse_hosted_demo_json(raw_body: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: set[str] = set()
        output: dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                raise HostedDemoJsonError("DUPLICATE_JSON_KEY", "Hosted-demo request JSON contains a duplicate key.")
            seen.add(key)
            output[key] = value
        return output

    try:
        parsed = json.loads(raw_body.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except UnicodeDecodeError as exc:
        raise HostedDemoJsonError("MALFORMED_JSON", "Hosted-demo request body must be UTF-8 JSON.") from exc
    except json.JSONDecodeError as exc:
        raise HostedDemoJsonError("MALFORMED_JSON", "Hosted-demo request body must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise HostedDemoJsonError("INVALID_JSON_OBJECT", "Hosted-demo request body must be a JSON object.")
    return parsed


def _validate_safe_identifier(value: str, *, field_name: str) -> str:
    if not SAFE_ID_PATTERN.match(value):
        raise ValueError(f"{field_name} must be a bounded safe identifier.")
    return value


def _validate_checksum(value: str | None, *, field_name: str) -> str | None:
    if value is not None and not CHECKSUM_PATTERN.match(value):
        raise ValueError(f"{field_name} must be a sha256 checksum.")
    return value


def _canonicalize_text(value: str) -> str:
    normalized = value.strip()
    for _ in range(8):
        decoded = unquote(normalized)
        if decoded == normalized:
            break
        normalized = decoded.strip()
    return normalized


def _contains_unsafe_url(value: object) -> bool:
    if isinstance(value, str):
        normalized = _canonicalize_text(value)
        return bool(UNSAFE_URL_PATTERN.search(normalized))
    if isinstance(value, dict):
        return any(_contains_unsafe_url(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_unsafe_url(item) for item in value)
    return False


def _validate_safe_file_name(value: str) -> str:
    if "/" in value or "\\" in value or "\x00" in value or not SAFE_FILE_NAME_PATTERN.match(value):
        raise ValueError("artifactFileName must be a bounded basename.")
    if _contains_unsafe_url(value):
        raise ValueError("artifactFileName must not contain a URL or scheme.")
    return value


def _contains_prompt_injection_marker(value: object) -> bool:
    if isinstance(value, str):
        lowered = _canonicalize_text(value).lower()
        return any(marker in lowered for marker in PROMPT_INJECTION_MARKERS)
    if isinstance(value, dict):
        return any(_contains_prompt_injection_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_prompt_injection_marker(item) for item in value)
    return False


def _contains_raw_output_marker(value: object) -> bool:
    if isinstance(value, str):
        lowered = _canonicalize_text(value).lower()
        compact = re.sub(r"[^a-z0-9]+", "", lowered)
        return any(marker in lowered or marker.replace(" ", "") in compact for marker in RAW_OUTPUT_MARKERS)
    if isinstance(value, dict):
        return any(_contains_raw_output_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_raw_output_marker(item) for item in value)
    return False


def _contains_cloned_identity_marker(value: object) -> bool:
    if isinstance(value, str):
        lowered = _canonicalize_text(value).lower()
        return any(marker in lowered for marker in CLONED_IDENTITY_MARKERS)
    if isinstance(value, dict):
        return any(_contains_cloned_identity_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_cloned_identity_marker(item) for item in value)
    return False


class HostedDemoArtifactInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    artifact_id: str = Field(alias="artifactId", min_length=1, max_length=128)
    artifact_kind: Literal[
        "SCRIPT",
        "SUBTITLES",
        "VOICE_MANIFEST",
        "AVATAR_DEMO",
        "RENDER_MANIFEST",
        "VIDEO_PLACEHOLDER",
    ] = Field(alias="artifactKind")
    artifact_checksum: str = Field(alias="artifactChecksum")
    artifact_mime_type: str = Field(alias="artifactMimeType", min_length=1, max_length=128)
    artifact_file_name: str = Field(alias="artifactFileName", min_length=1, max_length=128)
    artifact_size_bytes: int = Field(alias="artifactSizeBytes", ge=0)
    artifact_visibility: Literal["HOSTED_DEMO_REVIEWER"] = Field(alias="artifactVisibility")

    @field_validator("artifact_id")
    @classmethod
    def safe_artifact_id(cls, value: str) -> str:
        return _validate_safe_identifier(value, field_name="artifactId")

    @field_validator("artifact_checksum")
    @classmethod
    def valid_artifact_checksum(cls, value: str) -> str:
        checked = _validate_checksum(value, field_name="artifactChecksum")
        assert checked is not None
        return checked

    @field_validator("artifact_file_name")
    @classmethod
    def safe_artifact_file_name(cls, value: str) -> str:
        return _validate_safe_file_name(value)


class HostedDemoSourceInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    tenant_id: str = Field(alias="tenantId", min_length=1, max_length=128)
    project_id: str = Field(alias="projectId", min_length=1, max_length=128)
    actor_id: str = Field(alias="actorId", min_length=1, max_length=128)
    source_run_id: str = Field(alias="sourceRunId", min_length=1, max_length=128)
    trace_id: str = Field(alias="traceId", min_length=1, max_length=128)
    language: str = Field(min_length=2, max_length=16)
    audience: str = Field(min_length=1, max_length=64)
    script_checksum: str = Field(alias="scriptChecksum")
    citation_refs: list[str] = Field(alias="citationRefs", min_length=1, max_length=32)
    citation_indexes: list[int] = Field(alias="citationIndexes", min_length=1, max_length=32)
    evaluation_id: str = Field(alias="evaluationId", min_length=1, max_length=128)
    evaluation_status: Literal["PASSED", "FAILED", "UNKNOWN"] = Field(alias="evaluationStatus")
    evaluation_checksum: str = Field(alias="evaluationChecksum")
    multilingual_run_id: str | None = Field(default=None, alias="multilingualRunId")
    translated_script_checksum: str | None = Field(default=None, alias="translatedScriptChecksum")
    subtitles_checksum: str | None = Field(default=None, alias="subtitlesChecksum")
    voice_manifest_checksum: str | None = Field(default=None, alias="voiceManifestChecksum")
    tts_audio_checksum: str | None = Field(default=None, alias="ttsAudioChecksum")
    avatar_render_id: str | None = Field(default=None, alias="avatarRenderId")
    avatar_video_provider_metadata_checksum: str | None = Field(
        default=None,
        alias="avatarVideoProviderMetadataChecksum",
    )

    @field_validator(
        "tenant_id",
        "project_id",
        "actor_id",
        "source_run_id",
        "trace_id",
        "evaluation_id",
        "multilingual_run_id",
        "avatar_render_id",
    )
    @classmethod
    def safe_optional_ids(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_safe_identifier(value, field_name="identifier")

    @field_validator(
        "script_checksum",
        "evaluation_checksum",
        "translated_script_checksum",
        "subtitles_checksum",
        "voice_manifest_checksum",
        "tts_audio_checksum",
        "avatar_video_provider_metadata_checksum",
    )
    @classmethod
    def valid_optional_checksums(cls, value: str | None) -> str | None:
        return _validate_checksum(value, field_name="checksum")


class HostedDemoDisclosureInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    disclosure_text: str = Field(alias="disclosureText", min_length=1, max_length=512)
    disclosure_version: str = Field(alias="disclosureVersion", min_length=1, max_length=128)


class HostedDemoAccessInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    invite_id: str = Field(alias="inviteId", min_length=1, max_length=128)
    invite_secret: str = Field(alias="inviteSecret", min_length=1, max_length=512)
    session_id: str = Field(alias="sessionId", min_length=1, max_length=128)
    session_secret: str = Field(alias="sessionSecret", min_length=1, max_length=512)
    session_state: Literal["ACTIVE", "EXPIRED", "REVOKED"] = Field(alias="sessionState")
    session_expires_at: datetime = Field(alias="sessionExpiresAt")
    requested_operation: Literal["VIEW"] = Field(alias="requestedOperation")

    @field_validator("invite_id", "session_id")
    @classmethod
    def safe_access_ids(cls, value: str) -> str:
        return _validate_safe_identifier(value, field_name="access identifier")


class HostedDemoRetentionInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    retention_record_id: str = Field(alias="retentionRecordId", min_length=1, max_length=128)
    retention_state: Literal["ACTIVE", "PENDING_DELETION", "DELETED"] = Field(alias="retentionState")
    retention_expires_at: datetime = Field(alias="retentionExpiresAt")
    deletion_state: Literal["NOT_REQUESTED", "PENDING", "DELETED", "FAILED"] = Field(alias="deletionState")
    deletion_requested_at: datetime | None = Field(default=None, alias="deletionRequestedAt")
    deleted_at: datetime | None = Field(default=None, alias="deletedAt")
    tombstone_id: str | None = Field(default=None, alias="tombstoneId")
    tombstone_checksum: str | None = Field(default=None, alias="tombstoneChecksum")
    deletion_evidence_id: str | None = Field(default=None, alias="deletionEvidenceId")
    provider_deletion_status: Literal[
        "NOT_REQUESTED",
        "PENDING",
        "FAKE_LOCAL_DELETED",
        "FAILED",
    ] = Field(alias="providerDeletionStatus")
    local_only_provider_evidence: bool = Field(alias="localOnlyProviderEvidence")

    @field_validator("retention_record_id", "tombstone_id", "deletion_evidence_id")
    @classmethod
    def safe_retention_ids(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_safe_identifier(value, field_name="retention identifier")

    @field_validator("tombstone_checksum")
    @classmethod
    def valid_tombstone_checksum(cls, value: str | None) -> str | None:
        return _validate_checksum(value, field_name="tombstoneChecksum")


class HostedDemoAccessRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    artifact: HostedDemoArtifactInput
    source: HostedDemoSourceInput
    disclosure: HostedDemoDisclosureInput
    access: HostedDemoAccessInput
    retention: HostedDemoRetentionInput
    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=128)
    quota_units: int = Field(alias="quotaUnits", ge=1, le=100)
    local_outcome: Literal["SUCCESS", "FAIL_BEFORE_SIDE_EFFECT", "TIMEOUT_AFTER_ACCEPTED"] = Field(
        default="SUCCESS",
        alias="localOutcome",
    )

    @field_validator("idempotency_key")
    @classmethod
    def safe_idempotency_key(cls, value: str) -> str:
        return _validate_safe_identifier(value, field_name="idempotencyKey")


class HostedDemoProviderPosture(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    hosted_demo_enabled: bool = Field(alias="hostedDemoEnabled")
    provider_mode: Literal["LOCAL_FAKE", "DISABLED"] = Field(alias="providerMode")
    allow_network_egress: bool = Field(alias="allowNetworkEgress")
    real_provider_calls_enabled: bool = Field(alias="realProviderCallsEnabled")
    public_url_enabled: bool = Field(alias="publicUrlEnabled")
    paid_spend_enabled: bool = Field(alias="paidSpendEnabled")


class HostedDemoArtifactRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    artifact_id: str = Field(alias="artifactId")
    artifact_kind: str = Field(alias="artifactKind")
    artifact_checksum: str = Field(alias="artifactChecksum")
    artifact_mime_type: str = Field(alias="artifactMimeType")
    artifact_file_name: str = Field(alias="artifactFileName")
    artifact_visibility: Literal["DENIED", "HOSTED_DEMO_REVIEWER"] = Field(alias="artifactVisibility")


class HostedDemoSourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    actor_id: str = Field(alias="actorId")
    source_run_id: str = Field(alias="sourceRunId")
    trace_id: str = Field(alias="traceId")
    language: str
    audience: str
    script_checksum: str = Field(alias="scriptChecksum")
    citation_refs: list[str] = Field(alias="citationRefs")
    citation_indexes: list[int] = Field(alias="citationIndexes")
    evaluation_id: str = Field(alias="evaluationId")
    evaluation_status: str = Field(alias="evaluationStatus")
    evaluation_checksum: str = Field(alias="evaluationChecksum")
    multilingual_run_id: str | None = Field(default=None, alias="multilingualRunId")
    translated_script_checksum: str | None = Field(default=None, alias="translatedScriptChecksum")
    subtitles_checksum: str | None = Field(default=None, alias="subtitlesChecksum")
    voice_manifest_checksum: str | None = Field(default=None, alias="voiceManifestChecksum")
    tts_audio_checksum: str | None = Field(default=None, alias="ttsAudioChecksum")
    avatar_render_id: str | None = Field(default=None, alias="avatarRenderId")
    avatar_video_provider_metadata_checksum: str | None = Field(
        default=None,
        alias="avatarVideoProviderMetadataChecksum",
    )


class HostedDemoDisclosureRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    disclosure_text: str = Field(alias="disclosureText")
    disclosure_version: str = Field(alias="disclosureVersion")


class HostedDemoAccessRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    access_record_id: str = Field(alias="accessRecordId")
    access_state: Literal["DENIED", "GRANTED", "HELD"] = Field(alias="accessState")
    denial_reason: str | None = Field(default=None, alias="denialReason")
    invite_id_hash: str = Field(alias="inviteIdHash")
    session_id_hash: str = Field(alias="sessionIdHash")
    session_state: str = Field(alias="sessionState")
    session_expires_at: str = Field(alias="sessionExpiresAt")
    requested_operation: str = Field(alias="requestedOperation")


class HostedDemoQuotaRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    quota_reservation_id: str | None = Field(default=None, alias="quotaReservationId")
    quota_state: Literal["NOT_RESERVED", "RESERVED", "COMMITTED", "REFUNDED", "UNKNOWN", "EXHAUSTED"] = Field(
        alias="quotaState"
    )
    quota_units: int = Field(alias="quotaUnits")
    quota_scope: Literal["LOCAL_FAKE_SESSION"] = Field(alias="quotaScope")
    quota_limit: int = Field(alias="quotaLimit")
    quota_remaining: int = Field(alias="quotaRemaining")
    quota_outcome: str = Field(alias="quotaOutcome")
    retry_after_seconds: int | None = Field(default=None, alias="retryAfterSeconds")
    backoff_seconds: int | None = Field(default=None, alias="backoffSeconds")
    idempotency_scope: str = Field(alias="idempotencyScope")
    request_checksum: str = Field(alias="requestChecksum")


class HostedDemoRetentionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    retention_record_id: str = Field(alias="retentionRecordId")
    retention_state: str = Field(alias="retentionState")
    retention_expires_at: str = Field(alias="retentionExpiresAt")
    deletion_state: str = Field(alias="deletionState")
    deletion_requested_at: str | None = Field(default=None, alias="deletionRequestedAt")
    deleted_at: str | None = Field(default=None, alias="deletedAt")
    tombstone_id: str | None = Field(default=None, alias="tombstoneId")
    tombstone_checksum: str | None = Field(default=None, alias="tombstoneChecksum")
    deletion_evidence_id: str | None = Field(default=None, alias="deletionEvidenceId")
    provider_deletion_status: str = Field(alias="providerDeletionStatus")
    local_only_provider_evidence: bool = Field(alias="localOnlyProviderEvidence")


class HostedDemoObservabilityRecord(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    event: str
    trace_id: str = Field(alias="traceId")
    status_code: int = Field(alias="statusCode")
    access_outcome: str = Field(alias="accessOutcome")
    quota_outcome: str = Field(alias="quotaOutcome")
    retention_state: str = Field(alias="retentionState")
    artifact_validation_result: str = Field(alias="artifactValidationResult")


class HostedDemoDecision(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider_posture: HostedDemoProviderPosture = Field(alias="providerPosture")
    artifact: HostedDemoArtifactRecord
    source: HostedDemoSourceRecord
    disclosure: HostedDemoDisclosureRecord
    access: HostedDemoAccessRecord
    quota: HostedDemoQuotaRecord
    retention: HostedDemoRetentionRecord
    observability: HostedDemoObservabilityRecord


@dataclass(frozen=True)
class HostedDemoAccessConfig:
    enabled: bool = False
    require_invite: bool = True
    session_ttl_seconds: int = 900
    allowed_reviewer_count: int = 1
    per_session_quota: int = 1
    global_quota: int = 1
    retention_days: int = 7
    disclosure_version: str = HOSTED_DEMO_DISCLOSURE_VERSION
    allowed_invite_hashes: frozenset[str] = frozenset()
    allowed_session_hashes: frozenset[str] = frozenset()
    allowed_session_binding_hashes: frozenset[str] = frozenset()


@dataclass
class _QuotaReservation:
    request_checksum: str
    reservation_id: str | None
    state: Literal["COMMITTED", "REFUNDED", "UNKNOWN", "NOT_RESERVED", "EXHAUSTED"]
    units: int
    decision: HostedDemoDecision


@dataclass
class _TerminalRetentionEvidence:
    retention: HostedDemoRetentionRecord


@dataclass
class HostedDemoAccessService:
    config: HostedDemoAccessConfig = field(default_factory=HostedDemoAccessConfig)
    redacted_events: list[dict[str, ErrorDetailValue]] = field(default_factory=list)
    _reservations: dict[str, _QuotaReservation] = field(default_factory=dict)
    _session_units: dict[str, int] = field(default_factory=dict)
    _retention_terminal_states: dict[str, _TerminalRetentionEvidence] = field(default_factory=dict)
    _global_units: int = 0
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def configure(self, config: HostedDemoAccessConfig) -> None:
        self.config = config
        self.reset_runtime_state()

    def reset(self) -> None:
        self.config = HostedDemoAccessConfig()
        self.reset_runtime_state()

    def reset_runtime_state(self) -> None:
        self.redacted_events.clear()
        self._reservations.clear()
        self._session_units.clear()
        self._retention_terminal_states.clear()
        self._global_units = 0

    def record_local_retention_terminal_state(self, request: HostedDemoAccessRequest) -> None:
        self._validate_request(request)
        if request.retention.retention_state not in {"PENDING_DELETION", "DELETED"}:
            raise HostedDemoError(
                422,
                "RETENTION_STATE_MISMATCH",
                "Trusted local retention markers must be pending deletion or deleted.",
            )
        with self._lock:
            self._record_retention_terminal_state(request)

    @property
    def quota_reserved_count(self) -> int:
        return self._global_units

    def decide(self, request: HostedDemoAccessRequest) -> HostedDemoDecision:
        try:
            self._validate_request(request)
        except HostedDemoError as exc:
            self._record_validation_error(request, exc)
            raise
        request_checksum = self._request_checksum(request)
        idempotency_scope = self._idempotency_scope(request)
        with self._lock:
            if not self.config.enabled:
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason="HOSTED_DEMO_DISABLED",
                    quota_state="NOT_RESERVED",
                    quota_outcome="disabled",
                )
            auth_denial = self._access_denial_reason(request)
            if auth_denial is not None:
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason=auth_denial,
                    quota_state="NOT_RESERVED",
                    quota_outcome="auth_denied",
                )
            stored_retention_denial = self._stored_retention_denial_reason(request)
            if stored_retention_denial is not None:
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason=self._retention_denial_for_state(stored_retention_denial.retention.retention_state),
                    quota_state="NOT_RESERVED",
                    quota_outcome="retention_denied",
                    retention_record=stored_retention_denial.retention,
                )

            existing = self._reservations.get(idempotency_scope)
            if existing is not None:
                if existing.request_checksum != request_checksum:
                    raise HostedDemoError(409, "IDEMPOTENCY_CONFLICT", "Idempotency key was replayed with different input.")
                return existing.decision

            retention_denial = self._retention_denial_reason(request)
            if retention_denial is not None:
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason=retention_denial,
                    quota_state="NOT_RESERVED",
                    quota_outcome="retention_denied",
                )

            if not self._has_quota(request):
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason="QUOTA_EXHAUSTED",
                    quota_state="EXHAUSTED",
                    quota_outcome="exhausted",
                    retry_after_seconds=60,
                    backoff_seconds=30,
                )

            reservation_id = f"quota_{uuid4().hex}"
            self._reserve(request)
            if request.local_outcome == "FAIL_BEFORE_SIDE_EFFECT":
                self._release(request)
                return self._deny(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    reason="LOCAL_FAKE_JOB_FAILED",
                    quota_state="REFUNDED",
                    quota_outcome="refunded_before_side_effect",
                    reservation_id=reservation_id,
                )
            if request.local_outcome == "TIMEOUT_AFTER_ACCEPTED":
                decision = self._decision(
                    request,
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    access_state="HELD",
                    denial_reason="QUOTA_UNKNOWN_AFTER_ACCEPTED_TIMEOUT",
                    quota_state="UNKNOWN",
                    quota_outcome="unknown_after_accepted_timeout",
                    artifact_visibility="DENIED",
                    reservation_id=reservation_id,
                    retry_after_seconds=60,
                    backoff_seconds=30,
                )
                self._record_event(decision)
                self._store_reservation(
                    idempotency_scope=idempotency_scope,
                    request_checksum=request_checksum,
                    reservation_id=reservation_id,
                    state="UNKNOWN",
                    units=request.quota_units,
                    decision=decision,
                )
                return decision

            decision = self._decision(
                request,
                request_checksum=request_checksum,
                idempotency_scope=idempotency_scope,
                access_state="GRANTED",
                denial_reason=None,
                quota_state="COMMITTED",
                quota_outcome="committed",
                artifact_visibility="HOSTED_DEMO_REVIEWER",
                reservation_id=reservation_id,
            )
            self._record_event(decision)
            self._store_reservation(
                idempotency_scope=idempotency_scope,
                request_checksum=request_checksum,
                reservation_id=reservation_id,
                state="COMMITTED",
                units=request.quota_units,
                decision=decision,
            )
            return decision

    def _validate_request(self, request: HostedDemoAccessRequest) -> None:
        dumped = request.model_dump(mode="json", by_alias=True)
        if _contains_unsafe_url(dumped):
            raise HostedDemoError(422, "UNSAFE_URL", "Hosted-demo input contains an unsafe URL.")
        if _contains_prompt_injection_marker(dumped):
            raise HostedDemoError(422, "UNSAFE_DISPLAY_TEXT", "Hosted-demo display text contains unsafe instructions.")
        if _contains_raw_output_marker(dumped):
            raise HostedDemoError(422, "UNSAFE_DISPLAY_TEXT", "Hosted-demo display text contains raw output markers.")
        if _contains_cloned_identity_marker(dumped):
            raise HostedDemoError(
                422,
                "UNSAFE_DISPLAY_TEXT",
                "Hosted-demo display text crosses the Checkpoint 1 identity boundary.",
            )
        if request.disclosure.disclosure_text != HOSTED_DEMO_ALLOWED_DISCLOSURE_TEXT:
            raise HostedDemoError(422, "UNSAFE_DISPLAY_TEXT", "Hosted-demo disclosure text is not allowlisted.")
        self._validate_artifact(request)
        self._validate_evaluation(request)
        self._validate_retention(request)

    def _validate_artifact(self, request: HostedDemoAccessRequest) -> None:
        artifact = request.artifact
        if artifact.artifact_size_bytes > MAX_HOSTED_DEMO_ARTIFACT_BYTES:
            raise HostedDemoError(413, "ARTIFACT_TOO_LARGE", "Hosted-demo artifact exceeds the local size limit.")
        suffix = "." + artifact.artifact_file_name.rsplit(".", 1)[-1].lower()
        expected_mime = ARTIFACT_MIME_BY_SUFFIX.get(suffix)
        if expected_mime is None or expected_mime != artifact.artifact_mime_type:
            raise HostedDemoError(422, "ARTIFACT_TYPE_MISMATCH", "Hosted-demo artifact MIME and extension mismatch.")
        expected = build_hosted_demo_artifact_checksum(
            artifact_id=artifact.artifact_id,
            artifact_kind=artifact.artifact_kind,
            artifact_file_name=artifact.artifact_file_name,
            source_run_id=request.source.source_run_id,
            script_checksum=request.source.script_checksum,
            evaluation_checksum=request.source.evaluation_checksum,
            disclosure_version=request.disclosure.disclosure_version,
        )
        if artifact.artifact_checksum != expected:
            raise HostedDemoError(422, "ARTIFACT_CHECKSUM_MISMATCH", "Hosted-demo artifact evidence is stale.")

    def _validate_evaluation(self, request: HostedDemoAccessRequest) -> None:
        source = request.source
        if source.evaluation_status != "PASSED":
            raise HostedDemoError(422, "EVALUATION_NOT_PASSED", "Hosted-demo artifacts require passed evaluation.")
        if len(source.citation_refs) != len(source.citation_indexes):
            raise HostedDemoError(422, "CITATION_MISMATCH", "Citation references and indexes must align.")
        if any(index < 0 for index in source.citation_indexes):
            raise HostedDemoError(422, "CITATION_MISMATCH", "Citation indexes must be non-negative.")
        expected = build_hosted_demo_evaluation_checksum(
            tenant_id=source.tenant_id,
            project_id=source.project_id,
            actor_id=source.actor_id,
            source_run_id=source.source_run_id,
            trace_id=source.trace_id,
            language=source.language,
            audience=source.audience,
            script_checksum=source.script_checksum,
            evaluation_id=source.evaluation_id,
            evaluation_status=source.evaluation_status,
            citation_refs=tuple(source.citation_refs),
            citation_indexes=tuple(source.citation_indexes),
            multilingual_run_id=source.multilingual_run_id,
            translated_script_checksum=source.translated_script_checksum,
            subtitles_checksum=source.subtitles_checksum,
            voice_manifest_checksum=source.voice_manifest_checksum,
            tts_audio_checksum=source.tts_audio_checksum,
            avatar_render_id=source.avatar_render_id,
            avatar_video_provider_metadata_checksum=source.avatar_video_provider_metadata_checksum,
        )
        if source.evaluation_checksum != expected:
            raise HostedDemoError(422, "EVALUATION_CHECKSUM_MISMATCH", "Hosted-demo evaluation evidence is stale.")

    def _validate_retention(self, request: HostedDemoAccessRequest) -> None:
        retention = request.retention
        terminal = (
            retention.deletion_state == "DELETED"
            and retention.deletion_requested_at is not None
            and retention.deleted_at is not None
            and retention.tombstone_id is not None
            and retention.tombstone_checksum is not None
            and retention.deletion_evidence_id is not None
            and retention.provider_deletion_status == "FAKE_LOCAL_DELETED"
            and retention.local_only_provider_evidence
        )
        if retention.retention_state == "ACTIVE":
            active = (
                retention.deletion_state == "NOT_REQUESTED"
                and retention.deletion_requested_at is None
                and retention.deleted_at is None
                and retention.tombstone_id is None
                and retention.tombstone_checksum is None
                and retention.deletion_evidence_id is None
                and retention.provider_deletion_status == "NOT_REQUESTED"
                and retention.local_only_provider_evidence
            )
            if not active:
                raise HostedDemoError(
                    422,
                    "RETENTION_STATE_MISMATCH",
                    "Active hosted-demo records must not carry pending or deleted evidence.",
                )
        if retention.retention_state == "PENDING_DELETION":
            pending = (
                retention.deletion_state == "PENDING"
                and retention.deletion_requested_at is not None
                and retention.deleted_at is None
                and retention.tombstone_id is None
                and retention.tombstone_checksum is None
                and retention.deletion_evidence_id is None
                and retention.provider_deletion_status == "PENDING"
                and retention.local_only_provider_evidence
            )
            if not pending:
                raise HostedDemoError(
                    422,
                    "RETENTION_STATE_MISMATCH",
                    "Pending hosted-demo deletion requires pending local evidence only.",
                )
        if retention.retention_state == "DELETED":
            if not terminal:
                raise HostedDemoError(
                    422,
                    "DELETION_EVIDENCE_INCOMPLETE",
                    "Deleted hosted-demo records require terminal local tombstone evidence.",
                )
            assert retention.deleted_at is not None
            assert retention.deletion_requested_at is not None
            if retention.deleted_at < retention.deletion_requested_at:
                raise HostedDemoError(
                    422,
                    "DELETION_EVIDENCE_INCOMPLETE",
                    "Deleted hosted-demo records require deletion after request time.",
                )
            expected_tombstone_checksum = build_hosted_demo_tombstone_checksum(
                request=request,
                deleted_at=retention.deleted_at,
            )
            if (
                retention.tombstone_checksum != expected_tombstone_checksum
                or retention.tombstone_id != build_hosted_demo_tombstone_id(expected_tombstone_checksum)
                or retention.deletion_evidence_id
                != build_hosted_demo_deletion_evidence_id(expected_tombstone_checksum)
            ):
                raise HostedDemoError(
                    422,
                    "DELETION_EVIDENCE_INCOMPLETE",
                    "Deleted hosted-demo records require deterministic local/fake tombstone metadata.",
                )

    def _access_denial_reason(self, request: HostedDemoAccessRequest) -> str | None:
        now = datetime.now(UTC)
        expires_at = request.access.session_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if request.access.session_state != "ACTIVE" or expires_at <= now:
            return "SESSION_DENIED"
        if expires_at > now + timedelta(seconds=self.config.session_ttl_seconds):
            return "SESSION_DENIED"
        if self.config.require_invite and hash_hosted_demo_secret(request.access.invite_secret) not in self.config.allowed_invite_hashes:
            return "INVITE_DENIED"
        if hash_hosted_demo_secret(request.access.session_secret) not in self.config.allowed_session_hashes:
            return "SESSION_DENIED"
        if self._session_binding_hash(request) not in self.config.allowed_session_binding_hashes:
            return "SESSION_DENIED"
        return None

    def _retention_denial_reason(self, request: HostedDemoAccessRequest) -> str | None:
        if request.retention.retention_state == "PENDING_DELETION":
            return "RETENTION_PENDING_DELETION"
        if request.retention.retention_state == "DELETED":
            return "RETENTION_DELETED"
        now = datetime.now(UTC)
        expires_at = request.retention.retention_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            return "RETENTION_EXPIRED"
        return None

    def _retention_denial_for_state(self, retention_state: str) -> str:
        if retention_state == "PENDING_DELETION":
            return "RETENTION_PENDING_DELETION"
        return "RETENTION_DELETED"

    def _stored_retention_denial_reason(self, request: HostedDemoAccessRequest) -> _TerminalRetentionEvidence | None:
        stored = self._retention_terminal_states.get(self._retention_subject_hash(request))
        if stored is not None and request.retention.retention_state == "ACTIVE":
            return stored
        return None

    def _record_retention_terminal_state(self, request: HostedDemoAccessRequest) -> None:
        if request.retention.retention_state in {"PENDING_DELETION", "DELETED"}:
            subject_hash = self._retention_subject_hash(request)
            existing = self._retention_terminal_states.get(subject_hash)
            if existing is not None and existing.retention.retention_state == "DELETED":
                return
            self._retention_terminal_states[subject_hash] = _TerminalRetentionEvidence(
                retention=self._retention_record_from_request(request)
            )

    def _has_quota(self, request: HostedDemoAccessRequest) -> bool:
        session_hash = self._quota_subject_hash(request)
        session_used = self._session_units.get(session_hash, 0)
        return (
            session_used + request.quota_units <= self.config.per_session_quota
            and self._global_units + request.quota_units <= self.config.global_quota
        )

    def _reserve(self, request: HostedDemoAccessRequest) -> None:
        session_hash = self._quota_subject_hash(request)
        self._session_units[session_hash] = self._session_units.get(session_hash, 0) + request.quota_units
        self._global_units += request.quota_units

    def _release(self, request: HostedDemoAccessRequest) -> None:
        session_hash = self._quota_subject_hash(request)
        self._session_units[session_hash] = max(0, self._session_units.get(session_hash, 0) - request.quota_units)
        self._global_units = max(0, self._global_units - request.quota_units)

    def _session_binding_hash(self, request: HostedDemoAccessRequest) -> str:
        return build_hosted_demo_session_binding_hash(
            tenant_id=request.source.tenant_id,
            invite_id=request.access.invite_id,
            session_id=request.access.session_id,
            session_secret=request.access.session_secret,
        )

    def _quota_subject_hash(self, request: HostedDemoAccessRequest) -> str:
        return "quota_subject_" + self._session_binding_hash(request)[7:]

    def _retention_subject_hash(self, request: HostedDemoAccessRequest) -> str:
        return stable_checksum(
            (
                "hosted-demo-retention-subject-v2",
                request.source.tenant_id,
                request.source.project_id,
                request.source.source_run_id,
                request.artifact.artifact_id,
                request.artifact.artifact_checksum,
            )
        )

    def _idempotency_scope(self, request: HostedDemoAccessRequest) -> str:
        return stable_checksum(
            (
                "hosted-demo-idempotency-scope-v2",
                request.source.tenant_id,
                request.access.invite_id,
                request.access.session_id,
                request.idempotency_key,
                hash_hosted_demo_secret(request.access.invite_secret),
                hash_hosted_demo_secret(request.access.session_secret),
                self._session_binding_hash(request),
            )
        )

    def _store_reservation(
        self,
        *,
        idempotency_scope: str,
        request_checksum: str,
        reservation_id: str | None,
        state: Literal["COMMITTED", "REFUNDED", "UNKNOWN", "NOT_RESERVED", "EXHAUSTED"],
        units: int,
        decision: HostedDemoDecision,
    ) -> None:
        self._reservations[idempotency_scope] = _QuotaReservation(
            request_checksum=request_checksum,
            reservation_id=reservation_id,
            state=state,
            units=units,
            decision=decision,
        )

    def _deny(
        self,
        request: HostedDemoAccessRequest,
        *,
        request_checksum: str,
        idempotency_scope: str,
        reason: str,
        quota_state: Literal["NOT_RESERVED", "REFUNDED", "EXHAUSTED"],
        quota_outcome: str,
        reservation_id: str | None = None,
        retry_after_seconds: int | None = None,
        backoff_seconds: int | None = None,
        retention_record: HostedDemoRetentionRecord | None = None,
    ) -> HostedDemoDecision:
        decision = self._decision(
            request,
            request_checksum=request_checksum,
            idempotency_scope=idempotency_scope,
            access_state="DENIED",
            denial_reason=reason,
            quota_state=quota_state,
            quota_outcome=quota_outcome,
            artifact_visibility="DENIED",
            reservation_id=reservation_id,
            retry_after_seconds=retry_after_seconds,
            backoff_seconds=backoff_seconds,
            retention_record=retention_record,
        )
        self._record_event(decision)
        self._store_reservation(
            idempotency_scope=idempotency_scope,
            request_checksum=request_checksum,
            reservation_id=reservation_id,
            state=quota_state,
            units=0,
            decision=decision,
        )
        return decision

    def _decision(
        self,
        request: HostedDemoAccessRequest,
        *,
        request_checksum: str,
        idempotency_scope: str,
        access_state: Literal["DENIED", "GRANTED", "HELD"],
        denial_reason: str | None,
        quota_state: Literal["NOT_RESERVED", "RESERVED", "COMMITTED", "REFUNDED", "UNKNOWN", "EXHAUSTED"],
        quota_outcome: str,
        artifact_visibility: Literal["DENIED", "HOSTED_DEMO_REVIEWER"],
        reservation_id: str | None = None,
        retry_after_seconds: int | None = None,
        backoff_seconds: int | None = None,
        retention_record: HostedDemoRetentionRecord | None = None,
    ) -> HostedDemoDecision:
        quota_remaining = max(0, self.config.global_quota - self._global_units)
        status_code = 200 if access_state in {"GRANTED", "HELD"} else 403
        response_request_checksum = self._response_request_checksum(request)
        redacted_idempotency_scope = self._public_idempotency_scope(
            request,
            response_request_checksum=response_request_checksum,
        )
        effective_retention = retention_record or self._retention_record_from_request(request)
        return HostedDemoDecision(
            providerPosture=HostedDemoProviderPosture(
                hostedDemoEnabled=self.config.enabled,
                providerMode="LOCAL_FAKE" if self.config.enabled else "DISABLED",
                allowNetworkEgress=False,
                realProviderCallsEnabled=False,
                publicUrlEnabled=False,
                paidSpendEnabled=False,
            ),
            artifact=HostedDemoArtifactRecord(
                artifactId=request.artifact.artifact_id,
                artifactKind=request.artifact.artifact_kind,
                artifactChecksum=request.artifact.artifact_checksum,
                artifactMimeType=request.artifact.artifact_mime_type,
                artifactFileName=request.artifact.artifact_file_name,
                artifactVisibility=artifact_visibility,
            ),
            source=HostedDemoSourceRecord.model_validate(request.source.model_dump(by_alias=True)),
            disclosure=HostedDemoDisclosureRecord.model_validate(request.disclosure.model_dump(by_alias=True)),
            access=HostedDemoAccessRecord(
                accessRecordId=self._public_access_record_id(
                    request,
                    response_request_checksum=response_request_checksum,
                ),
                accessState=access_state,
                denialReason=denial_reason,
                inviteIdHash=hash_hosted_demo_secret(request.access.invite_id),
                sessionIdHash=hash_hosted_demo_secret(request.access.session_id),
                sessionState=request.access.session_state,
                sessionExpiresAt=request.access.session_expires_at.isoformat(),
                requestedOperation=request.access.requested_operation,
            ),
            quota=HostedDemoQuotaRecord(
                quotaReservationId=reservation_id,
                quotaState=quota_state,
                quotaUnits=request.quota_units,
                quotaScope="LOCAL_FAKE_SESSION",
                quotaLimit=self.config.global_quota,
                quotaRemaining=quota_remaining,
                quotaOutcome=quota_outcome,
                retryAfterSeconds=retry_after_seconds,
                backoffSeconds=backoff_seconds,
                idempotencyScope=redacted_idempotency_scope,
                requestChecksum=response_request_checksum,
            ),
            retention=effective_retention,
            observability=HostedDemoObservabilityRecord(
                event="hosted_demo.access_granted" if access_state == "GRANTED" else "hosted_demo.access_denied",
                traceId=request.source.trace_id,
                statusCode=status_code,
                accessOutcome=access_state,
                quotaOutcome=quota_outcome,
                retentionState=effective_retention.retention_state,
                artifactValidationResult="PASSED",
            ),
        )

    def _retention_record_from_request(self, request: HostedDemoAccessRequest) -> HostedDemoRetentionRecord:
        return HostedDemoRetentionRecord(
            retentionRecordId=request.retention.retention_record_id,
            retentionState=request.retention.retention_state,
            retentionExpiresAt=request.retention.retention_expires_at.isoformat(),
            deletionState=request.retention.deletion_state,
            deletionRequestedAt=(
                request.retention.deletion_requested_at.isoformat()
                if request.retention.deletion_requested_at is not None
                else None
            ),
            deletedAt=request.retention.deleted_at.isoformat() if request.retention.deleted_at is not None else None,
            tombstoneId=request.retention.tombstone_id,
            tombstoneChecksum=request.retention.tombstone_checksum,
            deletionEvidenceId=request.retention.deletion_evidence_id,
            providerDeletionStatus=request.retention.provider_deletion_status,
            localOnlyProviderEvidence=request.retention.local_only_provider_evidence,
        )

    def _record_event(self, decision: HostedDemoDecision) -> None:
        self.redacted_events.append(decision.observability.model_dump(by_alias=True))
        if decision.access.denial_reason is not None:
            self.redacted_events[-1]["denialReason"] = decision.access.denial_reason

    def _record_validation_error(self, request: HostedDemoAccessRequest, error: HostedDemoError) -> None:
        self.redacted_events.append(
            {
                "event": "hosted_demo.validation_denied",
                "traceId": request.source.trace_id,
                "statusCode": error.status_code,
                "accessOutcome": "DENIED",
                "quotaOutcome": "validation_denied",
                "retentionState": request.retention.retention_state,
                "artifactValidationResult": "FAILED",
                "denialReason": error.code,
            }
        )

    def _request_checksum(self, request: HostedDemoAccessRequest) -> str:
        redacted = request.model_dump(mode="json", by_alias=True)
        access = redacted["access"]
        assert isinstance(access, dict)
        access["inviteSecret"] = hash_hosted_demo_secret(request.access.invite_secret)
        access["sessionSecret"] = hash_hosted_demo_secret(request.access.session_secret)
        return stable_checksum(("hosted-demo-request-v1", redacted))

    def _response_request_checksum(self, request: HostedDemoAccessRequest) -> str:
        redacted = request.model_dump(mode="json", by_alias=True)
        access = redacted["access"]
        assert isinstance(access, dict)
        access["inviteSecret"] = "[redacted]"
        access["sessionSecret"] = "[redacted]"
        return stable_checksum(("hosted-demo-response-request-v1", redacted))

    def _public_idempotency_scope(
        self,
        request: HostedDemoAccessRequest,
        *,
        response_request_checksum: str,
    ) -> str:
        return "idem_scope_" + stable_checksum(
            (
                "hosted-demo-public-idempotency-scope-v1",
                request.source.tenant_id,
                request.access.invite_id,
                request.access.session_id,
                request.idempotency_key,
                response_request_checksum,
            )
        )[7:31]

    def _public_access_record_id(
        self,
        request: HostedDemoAccessRequest,
        *,
        response_request_checksum: str,
    ) -> str:
        return "access_" + stable_checksum(
            (
                "hosted-demo-public-access-record-v1",
                request.source.tenant_id,
                request.access.invite_id,
                request.access.session_id,
                response_request_checksum,
            )
        )[7:23]


hosted_demo_service = HostedDemoAccessService()
