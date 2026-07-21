"""Optional server-side avatar/video provider boundary for Stage 7.

The module uses injected transports and resolvers so local/dev/test/CI never
need provider SDKs, secrets, or network access.
"""

from __future__ import annotations

import email.utils
import ipaddress
import json
import re
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from urllib.parse import urlparse

from backend.app.rag.chunking import checksum_text

SUPPORTED_VIDEO_MIME_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}
API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,}$")
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")
INJECTION_PATTERN = re.compile(
    r"(ignore\s+(?:all\s+)?previous|system\s+prompt|developer\s+message|"
    r"<script\b|javascript:|data:text/html|prompt\s+injection)",
    re.IGNORECASE,
)
ProviderJobState = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "deleted",
    "deletion_pending",
    "deletion_failed",
    "unknown_after_accept",
]
AssetProvenance = Literal[
    "fully_synthetic_no_real_person",
    "provider_stock_licensed_non_identifiable",
    "prompt_with_existing_avatar_reference",
    "custom_replica",
    "digital_twin",
    "user_provided_likeness_image",
    "cloned_identity",
    "real_person_likeness",
    "unknown",
]
QuotaReservationState = Literal["RESERVED", "COMMITTED", "REFUNDED", "UNKNOWN"]


@dataclass(frozen=True)
class AvatarVideoHTTPResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True)
class AvatarVideoArtifactResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes
    final_url: str
    redirected: bool = False


class AvatarVideoTransport(Protocol):
    def create_job(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> AvatarVideoHTTPResponse:
        ...

    def get_job(
        self,
        *,
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> AvatarVideoHTTPResponse:
        ...

    def download_artifact(
        self,
        *,
        url: str,
        timeout_seconds: float,
    ) -> AvatarVideoArtifactResponse:
        ...

    def delete_job(
        self,
        *,
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> AvatarVideoHTTPResponse:
        ...


@dataclass(frozen=True)
class AvatarVideoProviderConfig:
    provider_id: str
    enabled: bool = False
    api_key: str = ""
    model_id: str = "disabled"
    model_version: str = "disabled"
    base_url: str = "https://provider.invalid"
    supported_languages: Sequence[str] = ("en",)
    max_script_characters: int = 5_000
    max_video_bytes: int = 10 * 1024 * 1024
    timeout_seconds: float = 10.0
    max_retries: int = 1
    retry_backoff_seconds: float = 0.0
    max_retry_after_seconds: float = 30.0
    max_poll_attempts: int = 3
    max_concurrent_jobs: int = 1
    provider_supports_hard_delete: bool = False
    provider_supports_idempotency: bool = False
    synthetic_marking_policy_version: str = ""


@dataclass(frozen=True)
class AvatarVideoBillingPolicy:
    billable_unit: Literal["second", "minute", "credit", "job"]
    duration_cap_seconds: int
    per_run_dollar_ceiling: float
    balance_error_statuses: tuple[int, ...] = (402,)
    retry_can_create_billable_job: bool = True


@dataclass(frozen=True)
class AvatarVideoSourceBinding:
    source_run_id: str
    trace_id: str
    language: str
    audience: str
    script: str
    script_checksum: str
    citation_refs: tuple[str, ...]
    expected_citation_refs: tuple[str, ...]
    evaluation_id: str
    evaluation_status: Literal["PASSED", "FAILED", "UNKNOWN"]
    evaluation_checksum: str
    expected_evaluation_checksum: str
    tts_audio_checksum: str | None = None


@dataclass(frozen=True)
class AvatarVideoRenderRequest:
    request_id: str
    source: AvatarVideoSourceBinding
    asset_provenance: AssetProvenance
    artifact_extension: Literal[".mp4", ".webm"] = ".mp4"


@dataclass(frozen=True)
class AvatarVideoQuotaReservation:
    request_id: str
    units: int
    state: QuotaReservationState


@dataclass(frozen=True)
class ExternalAvatarVideoResult:
    provider_id: str
    provider_mode: Literal["OPTIONAL_EXTERNAL"]
    model_id: str
    model_version: str
    provider_job_id: str
    artifact_checksum: str
    artifact_mime_type: str
    artifact_extension: str
    artifact_bytes: bytes
    source_run_id: str
    trace_id: str
    language: str
    audience: str
    script_checksum: str
    citation_refs: tuple[str, ...]
    evaluation_id: str
    evaluation_status: Literal["PASSED"]
    evaluation_checksum: str
    tts_audio_checksum: str | None
    disclosure_text: str
    disclosure_version: str
    retention_state: Literal["ACTIVE"]
    deletion_state: Literal["NOT_REQUESTED"]
    provider_synthetic_marking_policy_version: str
    attempt_count: int


@dataclass(frozen=True)
class AvatarVideoDeletionEvidence:
    provider_id: str
    provider_job_id: str
    deletion_state: Literal["DELETED"]
    provider_deletion_status: int
    deleted_at: str
    tombstone_checksum: str


class AvatarVideoProviderError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        billable_unknown: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.billable_unknown = billable_unknown


class InMemoryAvatarVideoQuotaLedger:
    def __init__(self, *, unit_limit: int) -> None:
        self.unit_limit = unit_limit
        self.reservations: dict[str, AvatarVideoQuotaReservation] = {}
        self._reserved_units = 0
        self._committed_units = 0
        self._lock = threading.Lock()

    def reserve(self, *, request_id: str, units: int) -> AvatarVideoQuotaReservation:
        if units <= 0:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_QUOTA_INVALID", "Quota units are required.")
        with self._lock:
            existing = self.reservations.get(request_id)
            if existing is not None:
                return existing
            if self._reserved_units + self._committed_units + units > self.unit_limit:
                raise AvatarVideoProviderError(429, "AVATAR_VIDEO_QUOTA_EXHAUSTED", "Avatar/video quota exhausted.")
            reservation = AvatarVideoQuotaReservation(request_id=request_id, units=units, state="RESERVED")
            self.reservations[request_id] = reservation
            self._reserved_units += units
            return reservation

    def commit(self, request_id: str) -> None:
        with self._lock:
            reservation = self.reservations[request_id]
            if reservation.state != "RESERVED":
                return
            self._reserved_units -= reservation.units
            self._committed_units += reservation.units
            self.reservations[request_id] = AvatarVideoQuotaReservation(request_id, reservation.units, "COMMITTED")

    def refund(self, request_id: str) -> None:
        with self._lock:
            reservation = self.reservations.get(request_id)
            if reservation is None or reservation.state != "RESERVED":
                return
            self._reserved_units -= reservation.units
            self.reservations[request_id] = AvatarVideoQuotaReservation(request_id, reservation.units, "REFUNDED")

    def mark_unknown(self, request_id: str) -> None:
        with self._lock:
            reservation = self.reservations.get(request_id)
            if reservation is None or reservation.state != "RESERVED":
                return
            self._reserved_units -= reservation.units
            self.reservations[request_id] = AvatarVideoQuotaReservation(request_id, reservation.units, "UNKNOWN")


class ExternalAvatarVideoProvider:
    provider_mode: Literal["OPTIONAL_EXTERNAL"] = "OPTIONAL_EXTERNAL"

    def __init__(
        self,
        *,
        config: AvatarVideoProviderConfig,
        billing_policy: AvatarVideoBillingPolicy,
        transport: AvatarVideoTransport,
        quota_ledger: InMemoryAvatarVideoQuotaLedger,
        resolve_host: Callable[[str], Sequence[str]],
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.config = config
        self.billing_policy = billing_policy
        self.transport = transport
        self.quota_ledger = quota_ledger
        self.resolve_host = resolve_host
        self.sleep = sleep
        self.clock = clock
        self.events: list[dict[str, object]] = []
        self._completed_results: dict[str, ExternalAvatarVideoResult] = {}
        self._semaphore = threading.BoundedSemaphore(max(1, config.max_concurrent_jobs))

    def render(self, request: AvatarVideoRenderRequest) -> ExternalAvatarVideoResult:
        self._validate_config()
        self._validate_request(request)
        if request.request_id in self._completed_results:
            self._record_event("avatar_video.duplicate_spend_blocked", request, quota_outcome="reused")
            return self._completed_results[request.request_id]
        units = max(1, min(self.billing_policy.duration_cap_seconds, len(request.source.script) // 100 + 1))
        reservation = self.quota_ledger.reserve(request_id=request.request_id, units=units)
        acquired = self._semaphore.acquire(blocking=False)
        if not acquired:
            self.quota_ledger.refund(request.request_id)
            raise AvatarVideoProviderError(
                429,
                "AVATAR_VIDEO_PROVIDER_BACKPRESSURE",
                "Avatar/video provider concurrency limit is reached.",
                retryable=True,
            )
        try:
            result = self._render_reserved(request=request, reserved_units=reservation.units)
        except AvatarVideoProviderError as exc:
            if exc.billable_unknown:
                self.quota_ledger.mark_unknown(request.request_id)
            elif exc.code != "AVATAR_VIDEO_QUOTA_EXHAUSTED":
                self.quota_ledger.refund(request.request_id)
            raise
        else:
            self.quota_ledger.commit(request.request_id)
            self._completed_results[request.request_id] = result
            return result
        finally:
            self._semaphore.release()

    def delete_artifact(self, result: ExternalAvatarVideoResult) -> AvatarVideoDeletionEvidence:
        if not self.config.provider_supports_hard_delete:
            raise AvatarVideoProviderError(
                412,
                "AVATAR_VIDEO_DELETION_EVIDENCE_UNAVAILABLE",
                "Provider deletion evidence is unavailable.",
            )
        response = self.transport.delete_job(
            url=f"{self.config.base_url.rstrip('/')}/jobs/{result.provider_job_id}?hard=true",
            headers=self._headers(),
            timeout_seconds=self.config.timeout_seconds,
        )
        if response.status_code not in {200, 202, 204}:
            raise AvatarVideoProviderError(502, "AVATAR_VIDEO_DELETION_FAILED", "Provider deletion failed.")
        deleted_at = self.clock().isoformat()
        tombstone_checksum = checksum_text(
            "|".join((self.config.provider_id, result.provider_job_id, "DELETED", deleted_at))
        )
        evidence = AvatarVideoDeletionEvidence(
            provider_id=self.config.provider_id,
            provider_job_id=result.provider_job_id,
            deletion_state="DELETED",
            provider_deletion_status=response.status_code,
            deleted_at=deleted_at,
            tombstone_checksum=tombstone_checksum,
        )
        self._record_event("avatar_video.deletion_evidence_recorded", result, deletion_state="DELETED")
        return evidence

    def _render_reserved(self, *, request: AvatarVideoRenderRequest, reserved_units: int) -> ExternalAvatarVideoResult:
        del reserved_units
        attempts = self.config.max_retries + 1
        last_error: AvatarVideoProviderError | None = None
        for attempt in range(1, attempts + 1):
            try:
                create_response = self.transport.create_job(
                    url=f"{self.config.base_url.rstrip('/')}/jobs",
                    headers={**self._headers(), "idempotency-key": request.request_id},
                    json_body={
                        "model_id": self.config.model_id,
                        "language": request.source.language,
                        "script_checksum": request.source.script_checksum,
                        "source_run_id": request.source.source_run_id,
                        "trace_id": request.source.trace_id,
                        "asset_provenance": request.asset_provenance,
                    },
                    timeout_seconds=self.config.timeout_seconds,
                )
            except TimeoutError as exc:
                raise AvatarVideoProviderError(
                    504,
                    "AVATAR_VIDEO_PROVIDER_TIMEOUT",
                    "Provider create timed out after possible remote acceptance.",
                    retryable=False,
                    billable_unknown=True,
                ) from exc
            error = self._error_from_response(create_response)
            if error is not None:
                last_error = error
                if error.retryable and attempt < attempts:
                    self.sleep(self.config.retry_backoff_seconds)
                    continue
                raise error
            create_payload = parse_strict_json_object(create_response.body)
            reject_unexpected_fields(create_payload, {"status", "provider_job_id"})
            provider_job_id = require_safe_string(create_payload.get("provider_job_id"), "provider_job_id")
            status = require_job_state(create_payload.get("status"))
            if status not in {"queued", "running", "succeeded"}:
                raise AvatarVideoProviderError(
                    502,
                    "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
                    "Provider create returned an invalid job state.",
                )
            return self._poll_and_download(
                request=request,
                provider_job_id=provider_job_id,
                attempt_count=attempt,
            )
        assert last_error is not None
        raise last_error

    def _poll_and_download(
        self,
        *,
        request: AvatarVideoRenderRequest,
        provider_job_id: str,
        attempt_count: int,
    ) -> ExternalAvatarVideoResult:
        for poll_attempt in range(1, self.config.max_poll_attempts + 1):
            status_response = self.transport.get_job(
                url=f"{self.config.base_url.rstrip('/')}/jobs/{provider_job_id}",
                headers=self._headers(),
                timeout_seconds=self.config.timeout_seconds,
            )
            error = self._error_from_response(status_response)
            if error is not None:
                raise error
            payload = parse_strict_json_object(status_response.body)
            if contains_injection(payload):
                raise AvatarVideoProviderError(
                    422,
                    "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
                    "Provider response contains unsafe instructions.",
                )
            reject_unexpected_fields(payload, {"status", "artifact_url", "retry_after"})
            status = require_job_state(payload.get("status"))
            if status == "failed":
                raise AvatarVideoProviderError(502, "AVATAR_VIDEO_PROVIDER_FAILURE", "Provider job failed.")
            if status == "succeeded":
                artifact_url = require_safe_url(str(payload.get("artifact_url", "")), self.resolve_host)
                artifact = self.transport.download_artifact(
                    url=artifact_url,
                    timeout_seconds=self.config.timeout_seconds,
                )
                return self._result_from_artifact(
                    request=request,
                    provider_job_id=provider_job_id,
                    artifact_url=artifact_url,
                    artifact=artifact,
                    attempt_count=attempt_count,
                )
            retry_after = parse_retry_after(payload.get("retry_after"), self.config.max_retry_after_seconds)
            self._record_event(
                "avatar_video.poll_retry",
                request,
                provider_job_state=status,
                retry_attempt=poll_attempt,
                status_code=status_response.status_code,
            )
            self.sleep(retry_after)
        raise AvatarVideoProviderError(
            504,
            "AVATAR_VIDEO_RETRY_CAP_EXCEEDED",
            "Provider polling exceeded the retry cap.",
            retryable=True,
        )

    def _result_from_artifact(
        self,
        *,
        request: AvatarVideoRenderRequest,
        provider_job_id: str,
        artifact_url: str,
        artifact: AvatarVideoArtifactResponse,
        attempt_count: int,
    ) -> ExternalAvatarVideoResult:
        if artifact.redirected or artifact.final_url != artifact_url:
            raise AvatarVideoProviderError(502, "AVATAR_VIDEO_UNSAFE_URL", "Provider artifact redirected.")
        if not 200 <= artifact.status_code < 300:
            raise AvatarVideoProviderError(502, "AVATAR_VIDEO_ARTIFACT_INVALID", "Provider artifact fetch failed.")
        content_type = artifact.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        expected_extension = SUPPORTED_VIDEO_MIME_TYPES.get(content_type)
        if expected_extension is None or expected_extension != request.artifact_extension:
            raise AvatarVideoProviderError(
                502,
                "AVATAR_VIDEO_ARTIFACT_INVALID",
                "Provider artifact MIME or extension is invalid.",
            )
        if not artifact.body:
            raise AvatarVideoProviderError(502, "AVATAR_VIDEO_ARTIFACT_INVALID", "Provider artifact is empty.")
        if len(artifact.body) > self.config.max_video_bytes:
            raise AvatarVideoProviderError(413, "AVATAR_VIDEO_ARTIFACT_TOO_LARGE", "Provider artifact is too large.")
        result = ExternalAvatarVideoResult(
            provider_id=self.config.provider_id,
            provider_mode=self.provider_mode,
            model_id=self.config.model_id,
            model_version=self.config.model_version,
            provider_job_id=provider_job_id,
            artifact_checksum=checksum_bytes(artifact.body),
            artifact_mime_type=content_type,
            artifact_extension=expected_extension,
            artifact_bytes=artifact.body,
            source_run_id=request.source.source_run_id,
            trace_id=request.source.trace_id,
            language=request.source.language,
            audience=request.source.audience,
            script_checksum=request.source.script_checksum,
            citation_refs=request.source.citation_refs,
            evaluation_id=request.source.evaluation_id,
            evaluation_status="PASSED",
            evaluation_checksum=request.source.evaluation_checksum,
            tts_audio_checksum=request.source.tts_audio_checksum,
            disclosure_text="AI-generated synthetic avatar/video. No cloned identity was used.",
            disclosure_version="stage7-avatar-video-disclosure-v1",
            retention_state="ACTIVE",
            deletion_state="NOT_REQUESTED",
            provider_synthetic_marking_policy_version=self.config.synthetic_marking_policy_version,
            attempt_count=attempt_count,
        )
        self._record_event(
            "avatar_video.artifact_validated",
            result,
            status_code=artifact.status_code,
            artifact_validation_result="pass",
            quota_outcome="commit",
        )
        return result

    def _validate_config(self) -> None:
        if not self.config.enabled:
            raise AvatarVideoProviderError(403, "AVATAR_VIDEO_PROVIDER_DISABLED", "Avatar/video provider disabled.")
        if not self.config.api_key:
            raise AvatarVideoProviderError(403, "AVATAR_VIDEO_PROVIDER_KEY_MISSING", "Avatar/video key missing.")
        if not API_KEY_PATTERN.fullmatch(self.config.api_key):
            raise AvatarVideoProviderError(403, "AVATAR_VIDEO_PROVIDER_KEY_INVALID", "Avatar/video key invalid.")
        if not self.config.provider_id or not SAFE_ID_PATTERN.fullmatch(self.config.provider_id):
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_CONFIG_INVALID", "Provider ID invalid.")
        if not self.config.model_id or not self.config.model_version:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_CONFIG_INVALID", "Provider model invalid.")
        if not self.config.synthetic_marking_policy_version:
            raise AvatarVideoProviderError(
                412,
                "AVATAR_VIDEO_PROVIDER_CONFIG_INVALID",
                "Synthetic marking policy version is required.",
            )
        if self.billing_policy.per_run_dollar_ceiling <= 0 or self.billing_policy.duration_cap_seconds <= 0:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_CONFIG_INVALID", "Billing policy invalid.")

    def _validate_request(self, request: AvatarVideoRenderRequest) -> None:
        source = request.source
        for value, field_name in (
            (request.request_id, "request_id"),
            (source.source_run_id, "source_run_id"),
            (source.trace_id, "trace_id"),
            (source.evaluation_id, "evaluation_id"),
        ):
            if not SAFE_ID_PATTERN.fullmatch(value):
                raise AvatarVideoProviderError(422, "AVATAR_VIDEO_BINDING_MISMATCH", f"{field_name} is invalid.")
        if source.language not in self.config.supported_languages:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_LANGUAGE_UNSUPPORTED", "Language unsupported.")
        if source.evaluation_status != "PASSED":
            raise AvatarVideoProviderError(412, "AVATAR_VIDEO_EVAL_NOT_APPROVED", "Evaluation did not pass.")
        if source.script_checksum != checksum_text(source.script):
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_BINDING_MISMATCH", "Script checksum mismatch.")
        if source.evaluation_checksum != source.expected_evaluation_checksum:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_BINDING_MISMATCH", "Evaluation checksum mismatch.")
        if source.citation_refs != source.expected_citation_refs:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_CITATION_MISMATCH", "Citation refs mismatch.")
        if not source.script.strip() or len(source.script) > self.config.max_script_characters:
            raise AvatarVideoProviderError(413, "AVATAR_VIDEO_SCRIPT_INVALID", "Script is invalid for provider.")
        if contains_injection(source.script):
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", "Script is unsafe.")
        if request.asset_provenance not in {
            "fully_synthetic_no_real_person",
            "provider_stock_licensed_non_identifiable",
        }:
            raise AvatarVideoProviderError(
                403,
                "AVATAR_VIDEO_LIKENESS_ASSET_REJECTED",
                "Asset provenance is not allowed for this checkpoint.",
            )

    def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {self.config.api_key}", "content-type": "application/json"}

    def _error_from_response(self, response: AvatarVideoHTTPResponse) -> AvatarVideoProviderError | None:
        status = response.status_code
        if 200 <= status < 300:
            return None
        if status in self.billing_policy.balance_error_statuses:
            return AvatarVideoProviderError(402, "AVATAR_VIDEO_PROVIDER_PAYMENT_REQUIRED", "Payment required.")
        if status in {401, 403}:
            return AvatarVideoProviderError(403, "AVATAR_VIDEO_PROVIDER_KEY_INVALID", "Provider auth failed.")
        if status in {408, 429, 500, 502, 503, 504}:
            return AvatarVideoProviderError(
                503 if status >= 500 else status,
                "AVATAR_VIDEO_PROVIDER_RETRYABLE_FAILURE",
                "Provider retryable failure.",
                retryable=True,
            )
        return AvatarVideoProviderError(502, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", "Provider failure.")

    def _record_event(self, event: str, subject: AvatarVideoRenderRequest | ExternalAvatarVideoResult, **extra: object) -> None:
        if isinstance(subject, AvatarVideoRenderRequest):
            trace_id = subject.source.trace_id
        else:
            trace_id = subject.trace_id
        allowed: dict[str, object] = {
            "event": event,
            "trace_id": trace_id,
            "provider_id": self.config.provider_id,
        }
        for key in (
            "status_code",
            "retry_attempt",
            "quota_outcome",
            "provider_job_state",
            "artifact_validation_result",
            "deletion_state",
        ):
            if key in extra:
                allowed[key] = extra[key]
        self.events.append(allowed)


def parse_strict_json_object(body: bytes) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise AvatarVideoProviderError(
                    422,
                    "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
                    "Provider response contains duplicate JSON keys.",
                )
            result[key] = value
        return result

    try:
        payload = json.loads(body.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AvatarVideoProviderError(
            422,
            "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
            "Provider response is malformed.",
        ) from exc
    if not isinstance(payload, dict):
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", "Provider response invalid.")
    return payload


def reject_unexpected_fields(payload: dict[str, object], allowed: set[str]) -> None:
    unexpected = set(payload) - allowed
    if unexpected:
        raise AvatarVideoProviderError(
            422,
            "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
            "Provider response contains unexpected fields.",
        )


def require_safe_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID_PATTERN.fullmatch(value):
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", f"{field_name} is invalid.")
    return value


def require_job_state(value: object) -> ProviderJobState:
    if value not in {"queued", "running", "succeeded", "failed", "deleted", "deletion_pending", "deletion_failed"}:
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", "Provider job state invalid.")
    return value  # type: ignore[return-value]


def require_safe_url(url: str, resolve_host: Callable[[str], Sequence[str]]) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_UNSAFE_URL", "Provider artifact URL is unsafe.")
    extension = "." + parsed.path.rsplit(".", 1)[-1].lower() if "." in parsed.path else ""
    if extension not in set(SUPPORTED_VIDEO_MIME_TYPES.values()):
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_UNSAFE_URL", "Provider artifact URL extension is unsafe.")
    addresses = resolve_host(parsed.hostname)
    if not addresses:
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_UNSAFE_URL", "Provider artifact host did not resolve.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise AvatarVideoProviderError(422, "AVATAR_VIDEO_UNSAFE_URL", "Provider artifact host is unsafe.")
    return url


def parse_retry_after(value: object, max_seconds: float) -> float:
    if value is None:
        return 0.0
    parsed_seconds = 0.0
    if isinstance(value, (int, float)):
        parsed_seconds = float(value)
    elif isinstance(value, str):
        try:
            parsed_seconds = float(value)
        except ValueError:
            try:
                parsed_date = email.utils.parsedate_to_datetime(value)
            except (TypeError, ValueError) as exc:
                raise AvatarVideoProviderError(
                    422,
                    "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID",
                    "Retry-After is invalid.",
                ) from exc
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=UTC)
            parsed_seconds = (parsed_date - datetime.now(UTC)).total_seconds()
    else:
        raise AvatarVideoProviderError(422, "AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID", "Retry-After is invalid.")
    if parsed_seconds < 0:
        return 0.0
    return min(parsed_seconds, max_seconds)


def contains_injection(value: object) -> bool:
    if isinstance(value, str):
        return INJECTION_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(contains_injection(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_injection(item) for item in value)
    return False


def checksum_bytes(content: bytes) -> str:
    return checksum_text(content.hex())
