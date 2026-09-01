"""Optional server-side TTS provider boundary for Stage 6.

The module deliberately uses an injected transport so local/dev/test/CI never
need provider SDKs, secrets, or network access.

Stage 6 validates sourceContextRefIds and citation_indexes before calling this
boundary; this module does not generate scripts, answers, or citations.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import math
import ipaddress
import os
import re
import struct
import sys
import threading
import time
from array import array
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from backend.app.narration import TTSConsumptionReceipt
from backend.app.rag.chunking import checksum_text
from backend.app.storage import write_state

SUPPORTED_AUDIO_MIME_TYPES = {"audio/mpeg": ".mp3", "audio/wav": ".wav"}
ELEVENLABS_API_BASE_URL = "https://api.elevenlabs.io/v1"
API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,}$")
VoiceProvenance = Literal["stock", "cloned", "custom", "private", "unknown"]
ReservationState = Literal["RESERVED", "COMMITTED", "REFUNDED"]


@dataclass(frozen=True)
class TTSHTTPResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class TTSTransport(Protocol):
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> TTSHTTPResponse: ...


@dataclass(frozen=True)
class TTSProviderConfig:
    provider_id: str
    enabled: bool
    api_key: str
    voice_id: str
    voice_provenance: VoiceProvenance
    model_id: str
    model_version: str
    supported_languages: Sequence[str]
    max_input_characters: int
    max_audio_bytes: int
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    max_concurrent_requests: int


@dataclass(frozen=True)
class TTSQuotaReservation:
    request_id: str
    reserved_characters: int
    state: ReservationState


@dataclass(frozen=True)
class ExternalTTSResult:
    provider: str
    provider_mode: str
    model_id: str
    model_version: str
    voice_id: str
    voice_provenance: VoiceProvenance
    provider_history_item_id: str | None
    language: str
    mime_type: str
    audio_bytes: bytes
    estimated_billable_characters: int
    attempt_count: int


class TTSProviderError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        billable: bool = False,
        provider_diagnostics: GoogleTTSFailureDiagnostics | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.billable = billable
        self.provider_diagnostics = provider_diagnostics


class InMemoryTTSQuotaLedger:
    def __init__(self, *, character_limit: int) -> None:
        self.character_limit = character_limit
        self.reservations: dict[str, TTSQuotaReservation] = {}
        self._committed_characters = 0
        self._reserved_characters = 0
        self._lock = threading.Lock()

    def reserve(self, *, request_id: str, characters: int) -> TTSQuotaReservation:
        if characters <= 0:
            raise TTSProviderError(422, "TTS_SCRIPT_EMPTY", "TTS input is required.")
        with self._lock:
            existing = self.reservations.get(request_id)
            if existing is not None:
                return existing
            if (
                self._committed_characters + self._reserved_characters + characters
                > self.character_limit
            ):
                raise TTSProviderError(429, "TTS_QUOTA_EXHAUSTED", "TTS quota is exhausted.")
            reservation = TTSQuotaReservation(
                request_id=request_id,
                reserved_characters=characters,
                state="RESERVED",
            )
            self.reservations[request_id] = reservation
            self._reserved_characters += characters
            return reservation

    def commit(self, request_id: str) -> None:
        with self._lock:
            reservation = self.reservations[request_id]
            if reservation.state != "RESERVED":
                return
            self._reserved_characters -= reservation.reserved_characters
            self._committed_characters += reservation.reserved_characters
            self.reservations[request_id] = TTSQuotaReservation(
                request_id=reservation.request_id,
                reserved_characters=reservation.reserved_characters,
                state="COMMITTED",
            )

    def refund(self, request_id: str) -> None:
        with self._lock:
            reservation = self.reservations.get(request_id)
            if reservation is None or reservation.state != "RESERVED":
                return
            self._reserved_characters -= reservation.reserved_characters
            self.reservations[request_id] = TTSQuotaReservation(
                request_id=reservation.request_id,
                reserved_characters=reservation.reserved_characters,
                state="REFUNDED",
            )


class ElevenLabsTTSProvider:
    provider = "elevenlabs"
    provider_mode = "OPTIONAL_EXTERNAL"

    def __init__(
        self,
        *,
        config: TTSProviderConfig,
        transport: TTSTransport,
        quota_ledger: InMemoryTTSQuotaLedger,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.transport = transport
        self.quota_ledger = quota_ledger
        self.sleep = sleep
        self._semaphore = threading.BoundedSemaphore(max(1, config.max_concurrent_requests))

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        request_id: str,
        trace_id: str,
    ) -> ExternalTTSResult:
        cleaned_text = text.strip()
        self._validate_config()
        self._validate_request(cleaned_text=cleaned_text, language=language)
        reservation = self.quota_ledger.reserve(request_id=request_id, characters=len(cleaned_text))
        acquired = self._semaphore.acquire(blocking=False)
        if not acquired:
            self.quota_ledger.refund(request_id)
            raise TTSProviderError(
                429,
                "TTS_PROVIDER_BACKPRESSURE",
                "TTS provider concurrency limit is reached.",
                retryable=True,
            )
        try:
            return self._synthesize_reserved(
                text=cleaned_text,
                language=language,
                request_id=reservation.request_id,
                trace_id=trace_id,
                billable_characters=reservation.reserved_characters,
            )
        except TTSProviderError as exc:
            if not exc.billable:
                self.quota_ledger.refund(request_id)
            raise
        finally:
            self._semaphore.release()

    def _synthesize_reserved(
        self,
        *,
        text: str,
        language: str,
        request_id: str,
        trace_id: str,
        billable_characters: int,
    ) -> ExternalTTSResult:
        attempts = self.config.max_retries + 1
        last_error: TTSProviderError | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.transport.post(
                    url=f"{ELEVENLABS_API_BASE_URL}/text-to-speech/{self.config.voice_id}",
                    headers={
                        "xi-api-key": self.config.api_key,
                        "content-type": "application/json",
                    },
                    json_body={
                        "text": text,
                        "model_id": self.config.model_id,
                        "language_code": language,
                        "trace_id": trace_id,
                    },
                    timeout_seconds=self.config.timeout_seconds,
                )
            except TimeoutError as exc:
                last_error = TTSProviderError(
                    504,
                    "TTS_PROVIDER_TIMEOUT",
                    "TTS provider timed out.",
                    retryable=True,
                )
                if attempt < attempts:
                    self.sleep(self.config.retry_backoff_seconds)
                    continue
                raise last_error from exc
            error = self._error_from_response(response)
            if error is not None:
                last_error = error
                if error.retryable and attempt < attempts:
                    self.sleep(self.config.retry_backoff_seconds)
                    continue
                raise error
            result = self._result_from_response(
                response=response,
                language=language,
                billable_characters=billable_characters,
                attempt_count=attempt,
            )
            self.quota_ledger.commit(request_id)
            return result
        assert last_error is not None
        raise last_error

    def _validate_config(self) -> None:
        if self.config.provider_id != self.provider:
            raise TTSProviderError(
                422, "TTS_PROVIDER_CONFIG_INVALID", "TTS provider config is invalid."
            )
        if not self.config.enabled:
            raise TTSProviderError(403, "TTS_PROVIDER_DISABLED", "TTS provider is disabled.")
        if not self.config.api_key:
            raise TTSProviderError(403, "TTS_PROVIDER_KEY_MISSING", "TTS provider key is missing.")
        if not API_KEY_PATTERN.fullmatch(self.config.api_key):
            raise TTSProviderError(403, "TTS_PROVIDER_KEY_INVALID", "TTS provider key is invalid.")
        if self.config.voice_provenance != "stock":
            raise TTSProviderError(
                403,
                "TTS_VOICE_PROVENANCE_UNSUPPORTED",
                "TTS voice provenance is not allowed for this checkpoint.",
            )
        if not self.config.voice_id or "/" in self.config.voice_id or "\\" in self.config.voice_id:
            raise TTSProviderError(
                422, "TTS_PROVIDER_CONFIG_INVALID", "TTS voice configuration is invalid."
            )

    def _validate_request(self, *, cleaned_text: str, language: str) -> None:
        if not cleaned_text:
            raise TTSProviderError(422, "TTS_SCRIPT_EMPTY", "TTS input is required.")
        if len(cleaned_text) > self.config.max_input_characters:
            raise TTSProviderError(
                413, "TTS_SCRIPT_TOO_LARGE", "TTS input exceeds the provider limit."
            )
        if language not in self.config.supported_languages:
            raise TTSProviderError(
                422, "TTS_LANGUAGE_UNSUPPORTED", "TTS provider does not support this language."
            )

    def _error_from_response(self, response: TTSHTTPResponse) -> TTSProviderError | None:
        status = response.status_code
        if 200 <= status < 300:
            return None
        if status in {408, 429, 500, 502, 503, 504}:
            return TTSProviderError(
                503 if status >= 500 else status,
                "TTS_PROVIDER_RETRYABLE_FAILURE",
                "TTS provider returned a retryable failure.",
                retryable=True,
            )
        if status in {401, 403}:
            return TTSProviderError(
                403, "TTS_PROVIDER_AUTH_FAILED", "TTS provider authentication failed."
            )
        if status == 402:
            return TTSProviderError(
                402, "TTS_PROVIDER_PAYMENT_REQUIRED", "TTS provider payment is required."
            )
        return TTSProviderError(
            502, "TTS_PROVIDER_FAILURE", "TTS provider returned an invalid status."
        )

    def _result_from_response(
        self,
        *,
        response: TTSHTTPResponse,
        language: str,
        billable_characters: int,
        attempt_count: int,
    ) -> ExternalTTSResult:
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type == "application/json":
            if _json_mentions_url(response.body):
                raise TTSProviderError(
                    502,
                    "TTS_PROVIDER_RESPONSE_UNSAFE",
                    "TTS provider returned an unsupported URL response.",
                )
            raise TTSProviderError(
                502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider response is invalid."
            )
        if content_type not in SUPPORTED_AUDIO_MIME_TYPES:
            raise TTSProviderError(
                502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider audio type is invalid."
            )
        if not response.body:
            raise TTSProviderError(
                502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider returned empty audio."
            )
        if len(response.body) > self.config.max_audio_bytes:
            raise TTSProviderError(
                413, "TTS_PROVIDER_AUDIO_TOO_LARGE", "TTS provider audio exceeds the size limit."
            )
        return ExternalTTSResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            model_id=self.config.model_id,
            model_version=self.config.model_version,
            voice_id=self.config.voice_id,
            voice_provenance=self.config.voice_provenance,
            provider_history_item_id=response.headers.get("history-item-id"),
            language=language,
            mime_type=content_type,
            audio_bytes=response.body,
            estimated_billable_characters=billable_characters,
            attempt_count=attempt_count,
        )


def _json_mentions_url(body: bytes) -> bool:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return _contains_url(payload)


def _contains_url(value: object) -> bool:
    if isinstance(value, str):
        return value.startswith(("http://", "https://"))
    if isinstance(value, dict):
        return any(_contains_url(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_url(item) for item in value)
    return False


def checksum_bytes(content: bytes) -> str:
    return checksum_text(content.hex())


GOOGLE_TTS_ENDPOINT = "https://eu-texttospeech.googleapis.com"
GOOGLE_TTS_URL = f"{GOOGLE_TTS_ENDPOINT}/v1/text:synthesize"
GOOGLE_TTS_MODEL = "gemini-2.5-pro-tts"
GOOGLE_TTS_LOCALE = "en-IN"
GOOGLE_TTS_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
GOOGLE_PROMPT_CONTRACT_VERSION = "cut1-google-gemini-tts-style-prompts-v1"
GOOGLE_PROMPT_FILE_SHA256 = "d8e38274fd986fed16aa64cbc3c8f720f4a4e01dfe4ffcc5f922d05cd5c9e017"
GOOGLE_PROMPT_FILE_BYTES = 7_500
GOOGLE_VOICE_MAP = {"meera": "Despina", "myra": "Leda", "raj": "Achird"}
GOOGLE_SAMPLE_RATE = 24_000
GOOGLE_MIN_DURATION_SECONDS = 90
GOOGLE_MAX_DURATION_SECONDS = 120
GOOGLE_MAX_AUDIO_BYTES = 44 + GOOGLE_MAX_DURATION_SECONDS * GOOGLE_SAMPLE_RATE * 2
GOOGLE_MAX_RESPONSE_BYTES = ((GOOGLE_MAX_AUDIO_BYTES + 2) // 3) * 4 + 64
GOOGLE_MAX_STATE_BYTES = 80_000_000
GOOGLE_MAX_LEDGER_ROWS = 10
GOOGLE_STATE_SCHEMA = "cut1-google-gemini-tts-state-v1"
GOOGLE_EGRESS_SCREEN_POLICY_VERSION = "cut1-google-tts-egress-screen-v1"
GOOGLE_INPUT_PRICE_MICROUSD_PER_MILLION_TOKENS = 1_000_000
GOOGLE_OUTPUT_PRICE_MICROUSD_PER_MILLION_TOKENS = 20_000_000
GOOGLE_CHECKSUM_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
GOOGLE_PRESENTER_BINDING_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
GOOGLE_LOGGER = logging.getLogger(__name__ + ".google")


GoogleSpendState = Literal[
    "PENDING", "COMPLETED", "FAILED_BILLABLE", "BILLABLE_UNKNOWN", "TOMBSTONED"
]
GoogleTransportKind = Literal["REST_HTTP_1_1", "OFFICIAL_GRPC_UNARY"]


@dataclass(frozen=True)
class GoogleTTSConfig:
    """Server-owned activation evidence; contains no provider choice or credential."""

    enabled: bool = False
    activation_record_sha256: str = ""
    activation_expires_at: str = ""
    privacy_approved: bool = False
    policy_approved: bool = False
    budget_audio_tokens: int = 0
    budget_microusd: int = 0
    quota_requests: int = 0
    max_concurrent_requests: int = 1
    timeout_seconds: float = 3.0
    approved_quota_project_sha256: str = ""


@dataclass(frozen=True)
class GoogleIdentity:
    access_token: str = field(repr=False)
    identity_evidence_sha256: str
    quota_project_id: str = field(repr=False)
    quota_project_sha256: str


class GoogleIdentityProvider(Protocol):
    # Concrete optional identity and transport implementations live in the
    # provider-owned google_tts_runtime module, not in this provider boundary.
    def resolve(self, *, scope: str) -> GoogleIdentity: ...

    def revalidate_quota_project(self, identity: GoogleIdentity) -> None: ...


@dataclass(frozen=True)
class GoogleEgressScreening:
    policy_version: str
    result: Literal["PASS", "REJECT"]
    evidence_checksum: str


_GOOGLE_GRPC_STATUS_ALLOWLIST = frozenset(
    {
        "OK",
        "CANCELLED",
        "UNKNOWN",
        "INVALID_ARGUMENT",
        "DEADLINE_EXCEEDED",
        "NOT_FOUND",
        "ALREADY_EXISTS",
        "PERMISSION_DENIED",
        "RESOURCE_EXHAUSTED",
        "FAILED_PRECONDITION",
        "ABORTED",
        "OUT_OF_RANGE",
        "UNIMPLEMENTED",
        "INTERNAL",
        "UNAVAILABLE",
        "DATA_LOSS",
        "UNAUTHENTICATED",
    }
)


class GoogleTransportError(Exception):
    def __init__(
        self,
        *,
        egress_possible: bool,
        grpc_status: str | None = None,
        raw_detail: object | None = None,
    ) -> None:
        super().__init__("Google TTS transport failed.")
        self.egress_possible = egress_possible
        self.grpc_status = grpc_status if grpc_status in _GOOGLE_GRPC_STATUS_ALLOWLIST else None
        # `raw_detail` is accepted only so a boundary caller can explicitly
        # discard it. It is never retained on the exception or diagnostics.
        del raw_detail


@dataclass(frozen=True)
class GoogleTTSHTTPResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes
    final_url: str
    redirect_count: int
    peer_ip: str
    resolved_addresses: tuple[str, ...]
    proxy_used: bool = False
    tls_verified: bool = False
    tls_server_name: str = ""
    peer_port: int = 0
    transport_kind: GoogleTransportKind = "REST_HTTP_1_1"


@dataclass(frozen=True)
class GoogleTTSFailureDiagnostics:
    """Bounded non-success metadata that cannot retain provider content or identifiers."""

    upstream_status_code: int | None
    response_byte_count: int
    response_body_sha256: str | None
    provider_error_code: int | None
    provider_error_status: str | None
    provider_request_id_sha256: str | None
    provider_trace_id_sha256: str | None
    transport_kind: GoogleTransportKind = "REST_HTTP_1_1"
    grpc_status: str | None = None
    raw_response_retained: bool = field(default=False, init=False)
    raw_headers_retained: bool = field(default=False, init=False)

    def as_safe_dict(self) -> dict[str, int | str | bool | None]:
        return {
            "transportKind": self.transport_kind,
            "upstreamStatusCode": self.upstream_status_code,
            "responseByteCount": self.response_byte_count,
            "responseBodySha256": self.response_body_sha256,
            "providerErrorCode": self.provider_error_code,
            "providerErrorStatus": self.provider_error_status,
            "grpcStatus": self.grpc_status,
            "providerRequestIdSha256": self.provider_request_id_sha256,
            "providerTraceIdSha256": self.provider_trace_id_sha256,
            "rawResponseRetained": self.raw_response_retained,
            "rawHeadersRetained": self.raw_headers_retained,
        }


class GoogleTTSPreparedTransport(Protocol):
    """Opaque, connection-bound capability returned by the injected transport."""

    url: str
    resolved_addresses: tuple[str, ...]
    peer_ip: str
    proxy_used: bool
    tls_verified: bool
    tls_server_name: str
    peer_port: int
    redirects_disabled: bool
    dns_pinned: bool
    transport_kind: GoogleTransportKind

    def send(
        self,
        *,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> GoogleTTSHTTPResponse:
        """Write on the already-established, attested TLS session only."""
        ...


class GoogleTTSTransport(Protocol):
    def prepare(self, *, url: str, timeout_seconds: float) -> GoogleTTSPreparedTransport:
        """Establish and attest the connection before receiving auth or content."""
        ...


@dataclass(frozen=True)
class ApprovedNarrationTTSResult:
    """Provider-neutral result admitted to the Cut 1 audio authority boundary."""

    provider: str
    provider_mode: str
    presenter_id: str
    requested_voice: str
    requested_locale: str
    model_id: str
    receipt_checksum: str
    request_checksum: str
    config_checksum: str
    mime_type: str
    artifact_checksum: str
    audio_bytes: bytes


class TTSProvider(Protocol):
    """Provider-neutral product boundary for approved narration synthesis."""

    def synthesize(self, *, receipt: TTSConsumptionReceipt) -> ApprovedNarrationTTSResult: ...


@dataclass(frozen=True)
class GoogleAudioMeasurements:
    duration_seconds: float
    sample_rate_hertz: int
    channels: int
    bits_per_sample: int
    frame_count: int
    rms: float
    peak: int
    active_ratio: float
    clipping_ratio: float
    zero_crossing_interval_kinds: int


@dataclass(frozen=True)
class GoogleTTSResult(ApprovedNarrationTTSResult):
    endpoint_region: str
    effective_voice_verified: bool
    prompt_contract_version: str
    prompt_sha256: str
    request_fingerprint: str
    identity_evidence_sha256: str
    screening_policy_version: str
    screening_result: str
    screening_evidence_checksum: str
    reserved_input_tokens: int
    reserved_output_tokens: int
    reserved_cost_microusd: int
    actual_output_tokens: int
    actual_cost_microusd: int
    measurements: GoogleAudioMeasurements
    spend_state: GoogleSpendState
    retention_state: str
    deletion_state: str
    attempt_count: int


@dataclass
class _GoogleLedgerEntry:
    fingerprint: str
    receipt_checksum: str
    state: GoogleSpendState
    reserved_input_tokens: int
    reserved_output_tokens: int
    reserved_cost_microusd: int
    result: GoogleTTSResult | None = None
    deletion_checksum: str | None = None


class _DuplicateGoogleKey(ValueError):
    pass


def _google_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateGoogleKey(key)
        result[key] = value
    return result


def _google_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _google_error(
    code: str,
    message: str,
    *,
    status: int = 422,
    billable: bool = False,
    provider_diagnostics: GoogleTTSFailureDiagnostics | None = None,
) -> TTSProviderError:
    return TTSProviderError(
        status,
        code,
        message,
        retryable=False,
        billable=billable,
        provider_diagnostics=provider_diagnostics,
    )


_GOOGLE_ERROR_STATUS_ALLOWLIST = frozenset(
    {
        "ABORTED",
        "ALREADY_EXISTS",
        "CANCELLED",
        "DATA_LOSS",
        "DEADLINE_EXCEEDED",
        "FAILED_PRECONDITION",
        "INTERNAL",
        "INVALID_ARGUMENT",
        "NOT_FOUND",
        "OUT_OF_RANGE",
        "PERMISSION_DENIED",
        "RESOURCE_EXHAUSTED",
        "UNAUTHENTICATED",
        "UNAVAILABLE",
        "UNIMPLEMENTED",
        "UNKNOWN",
    }
)
_GOOGLE_REQUEST_ID_HEADERS = frozenset({"x-goog-request-id", "x-google-request-id", "x-request-id"})
_GOOGLE_TRACE_ID_HEADERS = frozenset({"x-cloud-trace-context", "x-google-gfe-request-trace"})
_GOOGLE_DIAGNOSTIC_IDENTIFIER_MAX_BYTES = 512


def _google_header_digest(headers: dict[str, str], names: frozenset[str]) -> str | None:
    selected = [
        value for name, value in headers.items() if isinstance(name, str) and name.lower() in names
    ]
    if len(selected) != 1:
        return None
    encoded = selected[0].encode("utf-8")
    if not encoded or len(encoded) > _GOOGLE_DIAGNOSTIC_IDENTIFIER_MAX_BYTES:
        return None
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _google_failure_diagnostics(response: GoogleTTSHTTPResponse) -> GoogleTTSFailureDiagnostics:
    provider_code: int | None = None
    provider_status: str | None = None
    content_type = response.headers.get("content-type", "").lower().replace(" ", "")
    if response.body and content_type in {"application/json", "application/json;charset=utf-8"}:
        try:
            payload = json.loads(
                response.body.decode("utf-8"), object_pairs_hook=_google_json_object
            )
            error = payload.get("error") if isinstance(payload, dict) else None
            code = error.get("code") if isinstance(error, dict) else None
            status = error.get("status") if isinstance(error, dict) else None
            if (
                isinstance(code, int)
                and not isinstance(code, bool)
                and code == response.status_code
                and isinstance(status, str)
                and status in _GOOGLE_ERROR_STATUS_ALLOWLIST
            ):
                provider_code = code
                provider_status = status
        except (UnicodeDecodeError, ValueError):
            pass
    return GoogleTTSFailureDiagnostics(
        upstream_status_code=response.status_code,
        response_byte_count=len(response.body),
        response_body_sha256="sha256:" + hashlib.sha256(response.body).hexdigest(),
        provider_error_code=provider_code,
        provider_error_status=provider_status,
        provider_request_id_sha256=_google_header_digest(
            response.headers, _GOOGLE_REQUEST_ID_HEADERS
        ),
        provider_trace_id_sha256=_google_header_digest(response.headers, _GOOGLE_TRACE_ID_HEADERS),
    )


def _google_grpc_failure_diagnostics(
    error: GoogleTransportError,
) -> GoogleTTSFailureDiagnostics | None:
    if error.grpc_status is None:
        return None
    return GoogleTTSFailureDiagnostics(
        upstream_status_code=None,
        response_byte_count=0,
        response_body_sha256=None,
        provider_error_code=None,
        provider_error_status=None,
        provider_request_id_sha256=None,
        provider_trace_id_sha256=None,
        transport_kind="OFFICIAL_GRPC_UNARY",
        grpc_status=error.grpc_status,
    )


class GoogleGeminiTTSProvider:
    """Disabled-default Gemini-TTS adapter with no SDK or ambient network path."""

    provider = "google-cloud-text-to-speech"
    provider_mode = "OPTIONAL_EXTERNAL_DISABLED_DEFAULT"

    def __init__(
        self,
        *,
        config: GoogleTTSConfig,
        identity_provider: GoogleIdentityProvider,
        transport: GoogleTTSTransport,
        receipt_validator: Callable[[TTSConsumptionReceipt], bool],
        prompt_contract_path: Path,
        egress_screener: Callable[[TTSConsumptionReceipt], GoogleEgressScreening] | None = None,
        state_path: Path | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config
        self.identity_provider = identity_provider
        self.transport = transport
        self.receipt_validator = receipt_validator
        self.prompt_contract_path = prompt_contract_path
        self.egress_screener = egress_screener or screen_google_tts_egress
        self.state_path = state_path
        self.clock = clock or (lambda: datetime.now(UTC))
        self._ledger: dict[str, _GoogleLedgerEntry] = {}
        self._lock = threading.RLock()
        self._semaphore = threading.BoundedSemaphore(max(1, config.max_concurrent_requests))
        self._restore()

    def synthesize(self, *, receipt: TTSConsumptionReceipt) -> GoogleTTSResult:
        self._validate_config()
        lock_path = self._acquire_durable_lock()
        try:
            with self._lock:
                self._ledger.clear()
                self._restore()
            return self._synthesize_durable(receipt=receipt)
        finally:
            self._release_durable_lock(lock_path)

    def _synthesize_durable(self, *, receipt: TTSConsumptionReceipt) -> GoogleTTSResult:
        profile, screening = self._validate_before_identity(receipt)
        request_body = self._request_body(receipt, profile)
        fingerprint = self._fingerprint(receipt, profile, request_body)
        reserved_input_tokens = len(receipt.spoken_text.encode("utf-8")) + len(
            cast(str, profile["prompt"]).encode("utf-8")
        )
        reserved_output_tokens = GOOGLE_MAX_DURATION_SECONDS * 25
        reserved_cost_microusd = _google_cost_microusd(
            reserved_input_tokens, reserved_output_tokens
        )
        with self._lock:
            existing = self._ledger.get(fingerprint)
            if existing is not None:
                if existing.receipt_checksum != receipt.receipt_checksum:
                    raise _google_error(
                        "GOOGLE_TTS_IDEMPOTENCY_CONFLICT",
                        "TTS request conflicts with prior authority.",
                        status=409,
                    )
                if existing.state == "COMPLETED" and existing.result is not None:
                    self._validate_stored_result(
                        existing.result,
                        receipt,
                        profile,
                        request_body,
                        fingerprint,
                        screening,
                    )
                    return existing.result
                if existing.state == "BILLABLE_UNKNOWN":
                    raise _google_error(
                        "GOOGLE_TTS_BILLABLE_UNKNOWN",
                        "TTS billing state requires reconciliation.",
                        status=409,
                        billable=True,
                    )
                if existing.state == "TOMBSTONED":
                    raise _google_error(
                        "GOOGLE_TTS_ARTIFACT_DELETED",
                        "TTS artifact is deleted.",
                        status=410,
                        billable=True,
                    )
                raise _google_error(
                    "GOOGLE_TTS_IN_PROGRESS", "TTS request is already in progress.", status=409
                )
            if any(
                entry.receipt_checksum == receipt.receipt_checksum
                for entry in self._ledger.values()
            ):
                raise _google_error(
                    "GOOGLE_TTS_IDEMPOTENCY_CONFLICT",
                    "TTS receipt is already bound to another request state.",
                    status=409,
                )
            reserved_requests = len(self._ledger)
            if reserved_requests >= self.config.quota_requests:
                raise _google_error(
                    "GOOGLE_TTS_QUOTA_BLOCKED", "Google TTS quota is unavailable.", status=429
                )
            used_output_tokens = sum(
                entry.reserved_output_tokens for entry in self._ledger.values()
            )
            used_cost_microusd = sum(
                entry.reserved_cost_microusd for entry in self._ledger.values()
            )
            if used_output_tokens + reserved_output_tokens > self.config.budget_audio_tokens:
                raise _google_error(
                    "GOOGLE_TTS_BUDGET_BLOCKED", "Google TTS budget is unavailable.", status=402
                )
            if used_cost_microusd + reserved_cost_microusd > self.config.budget_microusd:
                raise _google_error(
                    "GOOGLE_TTS_BUDGET_BLOCKED",
                    "Google TTS cost budget is unavailable.",
                    status=402,
                )
            self._ledger[fingerprint] = _GoogleLedgerEntry(
                fingerprint,
                receipt.receipt_checksum,
                "PENDING",
                reserved_input_tokens,
                reserved_output_tokens,
                reserved_cost_microusd,
            )
            try:
                self._persist_locked()
            except Exception:
                self._ledger.pop(fingerprint, None)
                raise _google_error(
                    "GOOGLE_TTS_RESERVATION_FAILED",
                    "TTS request reservation could not be persisted.",
                    status=503,
                )
        if not self._semaphore.acquire(blocking=False):
            self._drop_pre_egress(fingerprint)
            raise _google_error(
                "GOOGLE_TTS_CONCURRENCY_BLOCKED", "TTS concurrency limit is reached.", status=429
            )
        try:
            try:
                prepared = self.transport.prepare(
                    url=GOOGLE_TTS_URL,
                    timeout_seconds=self.config.timeout_seconds,
                )
            except Exception:
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_PRE_EGRESS_FAILURE",
                    "TTS transport preflight failed.",
                    status=503,
                ) from None
            try:
                self._validate_prepared_transport(prepared)
            except TTSProviderError:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise
            except Exception:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                    "Google TTS transport policy evidence is invalid.",
                    status=503,
                ) from None
            try:
                identity = self.identity_provider.resolve(scope=GOOGLE_TTS_SCOPE)
            except Exception:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_IDENTITY_UNAVAILABLE",
                    "TTS runtime identity is unavailable.",
                    status=503,
                ) from None
            try:
                self._validate_identity(identity)
            except TTSProviderError:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise
            try:
                self.identity_provider.revalidate_quota_project(identity)
            except Exception:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_IDENTITY_UNAVAILABLE",
                    "TTS runtime identity is unavailable.",
                    status=503,
                ) from None
            try:
                headers = self._request_headers(identity)
                self._validate_request_headers(headers, identity)
            except TTSProviderError:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise
            except Exception:
                self._close_prepared(prepared)
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_REQUEST_HEADERS_INVALID",
                    "Google TTS request headers are invalid.",
                    status=403,
                ) from None
            try:
                response = prepared.send(
                    headers=headers,
                    json_body=request_body,
                    timeout_seconds=self.config.timeout_seconds,
                )
            except GoogleTransportError as exc:
                diagnostics = _google_grpc_failure_diagnostics(exc)
                if exc.egress_possible:
                    self._set_state(fingerprint, "BILLABLE_UNKNOWN")
                    raise _google_error(
                        "GOOGLE_TTS_BILLABLE_UNKNOWN",
                        "TTS billing state requires reconciliation.",
                        status=504,
                        billable=True,
                        provider_diagnostics=diagnostics,
                    ) from None
                self._drop_pre_egress(fingerprint)
                raise _google_error(
                    "GOOGLE_TTS_PRE_EGRESS_FAILURE",
                    "TTS transport failed before egress.",
                    status=503,
                    provider_diagnostics=diagnostics,
                ) from None
            except Exception:
                self._set_state(fingerprint, "BILLABLE_UNKNOWN")
                raise _google_error(
                    "GOOGLE_TTS_BILLABLE_UNKNOWN",
                    "TTS billing state requires reconciliation.",
                    status=504,
                    billable=True,
                ) from None
            try:
                audio = self._response_audio(response, prepared)
                measurements = validate_google_wav(audio)
                try:
                    authority_current = self.receipt_validator(receipt)
                except Exception:
                    authority_current = False
                if not authority_current:
                    self._set_state(fingerprint, "FAILED_BILLABLE")
                    raise _google_error(
                        "GOOGLE_TTS_AUTHORITY_STALE_AFTER_EGRESS",
                        "TTS receipt authority changed during synthesis.",
                        status=409,
                        billable=True,
                    )
                actual_output_tokens = math.ceil(measurements.duration_seconds * 25)
                actual_cost_microusd = _google_cost_microusd(
                    reserved_input_tokens, actual_output_tokens
                )
                result = GoogleTTSResult(
                    provider=self.provider,
                    provider_mode=self.provider_mode,
                    presenter_id=receipt.presenter_id,
                    requested_voice=cast(str, profile["provider_voice"]),
                    requested_locale=GOOGLE_TTS_LOCALE,
                    model_id=GOOGLE_TTS_MODEL,
                    endpoint_region="EU",
                    effective_voice_verified=False,
                    prompt_contract_version=GOOGLE_PROMPT_CONTRACT_VERSION,
                    prompt_sha256="sha256:" + cast(str, profile["prompt_sha256"]),
                    request_fingerprint=fingerprint,
                    request_checksum=self._request_contract_checksum(
                        receipt, profile, request_body
                    ),
                    config_checksum=self._config_checksum(),
                    identity_evidence_sha256=identity.identity_evidence_sha256,
                    receipt_checksum=receipt.receipt_checksum,
                    screening_policy_version=screening.policy_version,
                    screening_result=screening.result,
                    screening_evidence_checksum=screening.evidence_checksum,
                    reserved_input_tokens=reserved_input_tokens,
                    reserved_output_tokens=reserved_output_tokens,
                    reserved_cost_microusd=reserved_cost_microusd,
                    actual_output_tokens=actual_output_tokens,
                    actual_cost_microusd=actual_cost_microusd,
                    artifact_checksum="sha256:" + hashlib.sha256(audio).hexdigest(),
                    mime_type="audio/wav",
                    audio_bytes=audio,
                    measurements=measurements,
                    spend_state="COMPLETED",
                    retention_state="LOCAL_ACTIVE_PROVIDER_RETENTION_UNKNOWN",
                    deletion_state="ACTIVE",
                    attempt_count=1,
                )
                with self._lock:
                    self._ledger[fingerprint] = _GoogleLedgerEntry(
                        fingerprint,
                        receipt.receipt_checksum,
                        "COMPLETED",
                        reserved_input_tokens,
                        actual_output_tokens,
                        actual_cost_microusd,
                        result,
                    )
                    try:
                        self._persist_locked()
                    except Exception:
                        self._ledger[fingerprint] = _GoogleLedgerEntry(
                            fingerprint,
                            receipt.receipt_checksum,
                            "BILLABLE_UNKNOWN",
                            reserved_input_tokens,
                            reserved_output_tokens,
                            reserved_cost_microusd,
                        )
                        raise _google_error(
                            "GOOGLE_TTS_FINALIZE_FAILED",
                            "TTS result could not be durably finalized.",
                            status=503,
                            billable=True,
                        ) from None
                self._log("completed", fingerprint, receipt.presenter_id)
                return result
            except TTSProviderError:
                if self._request_state_current(receipt) == "PENDING":
                    self._set_state(fingerprint, "FAILED_BILLABLE")
                raise
        finally:
            self._semaphore.release()

    def request_state(self, receipt: TTSConsumptionReceipt) -> GoogleSpendState | None:
        if self.state_path is None:
            return self._request_state_current(receipt)
        lock_path = self._acquire_durable_lock()
        try:
            with self._lock:
                self._ledger.clear()
                self._restore()
            return self._request_state_current(receipt)
        finally:
            self._release_durable_lock(lock_path)

    def _request_state_current(self, receipt: TTSConsumptionReceipt) -> GoogleSpendState | None:
        profile = self._load_profile(receipt.presenter_id)
        body = self._request_body(receipt, profile)
        entry = self._ledger.get(self._fingerprint(receipt, profile, body))
        if entry is None:
            entry = next(
                (
                    candidate
                    for candidate in self._ledger.values()
                    if candidate.receipt_checksum == receipt.receipt_checksum
                ),
                None,
            )
        return entry.state if entry is not None else None

    def delete_artifact(self, receipt: TTSConsumptionReceipt) -> None:
        lock_path = self._acquire_durable_lock()
        try:
            with self._lock:
                self._ledger.clear()
                self._restore()
            self._delete_artifact_durable(receipt)
        finally:
            self._release_durable_lock(lock_path)

    def _delete_artifact_durable(self, receipt: TTSConsumptionReceipt) -> None:
        if (
            not isinstance(receipt, TTSConsumptionReceipt)
            or GOOGLE_CHECKSUM_PATTERN.fullmatch(receipt.receipt_checksum) is None
        ):
            raise _google_error(
                "GOOGLE_TTS_AUTHORITY_INVALID",
                "TTS receipt authority is invalid.",
                status=409,
            )
        with self._lock:
            matches = [
                entry
                for entry in self._ledger.values()
                if entry.receipt_checksum == receipt.receipt_checksum
            ]
            entry = matches[0] if len(matches) == 1 else None
            if entry is None:
                raise _google_error(
                    "GOOGLE_TTS_ARTIFACT_NOT_FOUND", "TTS artifact was not found.", status=404
                )
            if entry.state == "TOMBSTONED":
                return
            if entry.state != "COMPLETED":
                raise _google_error(
                    "GOOGLE_TTS_DELETE_STATE_INVALID",
                    "TTS artifact cannot be deleted in its current state.",
                    status=409,
                )
            fingerprint = entry.fingerprint
            tombstone = _GoogleLedgerEntry(
                fingerprint,
                receipt.receipt_checksum,
                "TOMBSTONED",
                entry.reserved_input_tokens,
                entry.reserved_output_tokens,
                entry.reserved_cost_microusd,
                None,
                _google_sha(
                    {
                        "deletionState": "TOMBSTONED",
                        "fingerprint": fingerprint,
                        "providerRetention": "UNKNOWN_NO_PROVIDER_DELETE_API_CLAIM",
                        "receiptChecksum": receipt.receipt_checksum,
                    }
                ),
            )
            self._ledger[fingerprint] = tombstone
            try:
                self._persist_locked()
            except Exception:
                self._ledger[fingerprint] = entry
                raise _google_error(
                    "GOOGLE_TTS_DELETE_PERSISTENCE_FAILED",
                    "TTS artifact deletion could not be persisted.",
                    status=503,
                ) from None

    def _acquire_durable_lock(self) -> Path:
        if self.state_path is None:
            raise _google_error(
                "GOOGLE_TTS_DURABLE_STATE_REQUIRED",
                "Google TTS durable state is required.",
                status=503,
            )
        lock_path = self.state_path.with_name(self.state_path.name + ".issue368.lock")
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="ascii") as handle:
                handle.write("issue-368-exclusive-egress\n")
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            raise _google_error(
                "GOOGLE_TTS_CONCURRENCY_BLOCKED",
                "TTS durable request lock is unavailable.",
                status=409,
            ) from None
        except OSError:
            raise _google_error(
                "GOOGLE_TTS_DURABLE_STATE_UNAVAILABLE",
                "Google TTS durable state is unavailable.",
                status=503,
            ) from None
        return lock_path

    def _release_durable_lock(self, lock_path: Path) -> None:
        try:
            lock_path.unlink()
        except OSError:
            # A retained lock is a fail-closed reconciliation gate, never a
            # reason to risk a second egress or expose a private path.
            pass

    def _validate_before_identity(
        self, receipt: TTSConsumptionReceipt
    ) -> tuple[dict[str, Any], GoogleEgressScreening]:
        self._validate_config()
        try:
            authority_current = isinstance(
                receipt, TTSConsumptionReceipt
            ) and self.receipt_validator(receipt)
        except Exception:
            authority_current = False
        if not authority_current:
            raise _google_error(
                "GOOGLE_TTS_AUTHORITY_INVALID", "TTS receipt authority is invalid.", status=409
            )
        receipt_checksums = (
            receipt.narration_checksum,
            receipt.source_evaluation_checksum,
            receipt.evaluation_checksum,
            receipt.approval_checksum,
            receipt.receipt_checksum,
        )
        if (
            any(
                not isinstance(value, str) or GOOGLE_CHECKSUM_PATTERN.fullmatch(value) is None
                for value in receipt_checksums
            )
            or not isinstance(receipt.presenter_binding_checksum, str)
            or GOOGLE_PRESENTER_BINDING_PATTERN.fullmatch(receipt.presenter_binding_checksum)
            is None
        ):
            raise _google_error(
                "GOOGLE_TTS_AUTHORITY_INVALID", "TTS receipt authority is malformed.", status=409
            )
        if (
            not isinstance(receipt.presenter_id, str)
            or not isinstance(receipt.spoken_text, str)
            or not isinstance(receipt.request_id, str)
            or not isinstance(receipt.trace_id, str)
            or not isinstance(receipt.version, int)
            or isinstance(receipt.version, bool)
        ):
            raise _google_error(
                "GOOGLE_TTS_AUTHORITY_INVALID", "TTS receipt authority is malformed.", status=409
            )
        if receipt.presenter_id not in GOOGLE_VOICE_MAP:
            raise _google_error(
                "PRESENTER_NOT_ALLOWLISTED", "Presenter is not allowlisted for TTS."
            )
        if receipt.duration_requirement_seconds != (90, 120):
            raise _google_error(
                "GOOGLE_TTS_AUTHORITY_INVALID", "TTS duration authority is invalid."
            )
        text_bytes = receipt.spoken_text.encode("utf-8")
        if not text_bytes or len(text_bytes) > 4_000:
            raise _google_error(
                "GOOGLE_TTS_TEXT_LIMIT", "TTS text exceeds its UTF-8 byte limit.", status=413
            )
        try:
            screening = self.egress_screener(receipt)
        except Exception:
            raise _google_error(
                "GOOGLE_TTS_EGRESS_SCREEN_UNAVAILABLE",
                "TTS egress screening is unavailable.",
                status=503,
            ) from None
        expected_screening_checksum = _google_sha(
            {
                "narrationChecksum": receipt.narration_checksum,
                "policyVersion": GOOGLE_EGRESS_SCREEN_POLICY_VERSION,
                "result": screening.result
                if isinstance(screening, GoogleEgressScreening)
                else None,
            }
        )
        if (
            not isinstance(screening, GoogleEgressScreening)
            or screening.policy_version != GOOGLE_EGRESS_SCREEN_POLICY_VERSION
            or screening.result not in {"PASS", "REJECT"}
            or screening.evidence_checksum != expected_screening_checksum
        ):
            raise _google_error(
                "GOOGLE_TTS_EGRESS_SCREEN_INVALID",
                "TTS egress screening evidence is invalid.",
                status=503,
            )
        if screening.result != "PASS":
            raise _google_error(
                "GOOGLE_TTS_EGRESS_BLOCKED", "TTS content failed privacy or secret screening."
            )
        profile = self._load_profile(receipt.presenter_id)
        prompt_bytes = cast(str, profile["prompt"]).encode("utf-8")
        if len(prompt_bytes) > 4_000 or len(text_bytes) + len(prompt_bytes) > 5_000:
            raise _google_error(
                "GOOGLE_TTS_TEXT_LIMIT", "TTS request exceeds its UTF-8 byte limit.", status=413
            )
        return profile, screening

    def _validate_config(self) -> None:
        if (
            not isinstance(self.config.enabled, bool)
            or not isinstance(self.config.activation_record_sha256, str)
            or not isinstance(self.config.activation_expires_at, str)
            or not isinstance(self.config.privacy_approved, bool)
            or not isinstance(self.config.policy_approved, bool)
            or not isinstance(self.config.budget_audio_tokens, int)
            or isinstance(self.config.budget_audio_tokens, bool)
            or not isinstance(self.config.budget_microusd, int)
            or isinstance(self.config.budget_microusd, bool)
            or not isinstance(self.config.quota_requests, int)
            or isinstance(self.config.quota_requests, bool)
            or not isinstance(self.config.max_concurrent_requests, int)
            or isinstance(self.config.max_concurrent_requests, bool)
            or not isinstance(self.config.timeout_seconds, (int, float))
            or isinstance(self.config.timeout_seconds, bool)
            or not isinstance(self.config.approved_quota_project_sha256, str)
        ):
            raise _google_error("GOOGLE_TTS_CONFIG_INVALID", "Google TTS configuration is invalid.")
        if not self.config.enabled:
            raise _google_error("GOOGLE_TTS_DISABLED", "Google TTS is disabled.", status=403)
        if not GOOGLE_CHECKSUM_PATTERN.fullmatch(self.config.approved_quota_project_sha256):
            raise _google_error("GOOGLE_TTS_CONFIG_INVALID", "Google TTS configuration is invalid.")
        if self.state_path is None:
            raise _google_error(
                "GOOGLE_TTS_DURABLE_STATE_REQUIRED",
                "Google TTS durable state is required.",
                status=503,
            )
        if not GOOGLE_CHECKSUM_PATTERN.fullmatch(self.config.activation_record_sha256):
            raise _google_error(
                "GOOGLE_TTS_ACTIVATION_INVALID",
                "Google TTS activation evidence is invalid.",
                status=403,
            )
        try:
            expires = datetime.fromisoformat(self.config.activation_expires_at)
        except ValueError:
            raise _google_error(
                "GOOGLE_TTS_ACTIVATION_INVALID",
                "Google TTS activation evidence is invalid.",
                status=403,
            ) from None
        try:
            now = self.clock()
        except Exception:
            raise _google_error(
                "GOOGLE_TTS_CONFIG_INVALID", "Google TTS configuration is invalid."
            ) from None
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or expires.tzinfo is None
            or expires <= now
        ):
            raise _google_error(
                "GOOGLE_TTS_ACTIVATION_INVALID",
                "Google TTS activation evidence is stale.",
                status=403,
            )
        if not self.config.privacy_approved:
            raise _google_error(
                "GOOGLE_TTS_PRIVACY_BLOCKED", "Google TTS privacy approval is absent.", status=403
            )
        if not self.config.policy_approved:
            raise _google_error(
                "GOOGLE_TTS_POLICY_BLOCKED", "Google TTS policy approval is absent.", status=403
            )
        if self.config.budget_audio_tokens < GOOGLE_MAX_DURATION_SECONDS * 25:
            raise _google_error(
                "GOOGLE_TTS_BUDGET_BLOCKED", "Google TTS budget is unavailable.", status=402
            )
        minimum_cost = _google_cost_microusd(0, GOOGLE_MAX_DURATION_SECONDS * 25)
        if self.config.budget_microusd < minimum_cost:
            raise _google_error(
                "GOOGLE_TTS_BUDGET_BLOCKED", "Google TTS cost budget is unavailable.", status=402
            )
        if not 1 <= self.config.quota_requests <= GOOGLE_MAX_LEDGER_ROWS:
            raise _google_error(
                "GOOGLE_TTS_QUOTA_BLOCKED", "Google TTS quota is unavailable.", status=429
            )
        if (
            self.config.max_concurrent_requests != 1
            or not 0 < self.config.timeout_seconds <= threading.TIMEOUT_MAX
        ):
            raise _google_error("GOOGLE_TTS_CONFIG_INVALID", "Google TTS configuration is invalid.")

    def _load_profile(self, presenter_id: str) -> dict[str, Any]:
        try:
            if self.prompt_contract_path.is_symlink():
                raise OSError("symlink")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self.prompt_contract_path, flags)
            with os.fdopen(descriptor, "rb") as handle:
                raw = handle.read(GOOGLE_PROMPT_FILE_BYTES + 1)
        except OSError:
            raise _google_error(
                "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                "TTS prompt contract is unavailable.",
                status=503,
            ) from None
        if (
            len(raw) != GOOGLE_PROMPT_FILE_BYTES
            or hashlib.sha256(raw).hexdigest() != GOOGLE_PROMPT_FILE_SHA256
        ):
            raise _google_error(
                "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                "TTS prompt contract checksum is invalid.",
                status=503,
            )
        try:
            payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_google_json_object)
        except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateGoogleKey):
            raise _google_error(
                "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                "TTS prompt contract schema is invalid.",
                status=503,
            ) from None
        if (
            not isinstance(payload, dict)
            or payload.get("prompt_contract_version") != GOOGLE_PROMPT_CONTRACT_VERSION
        ):
            raise _google_error(
                "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                "TTS prompt contract version is invalid.",
                status=503,
            )
        profiles = payload.get("profiles")
        if not isinstance(profiles, list) or len(profiles) != 3:
            raise _google_error(
                "GOOGLE_TTS_PROMPT_CONTRACT_INVALID", "TTS prompt profiles are invalid.", status=503
            )
        by_id: dict[str, dict[str, Any]] = {}
        for item in profiles:
            if not isinstance(item, dict):
                raise _google_error(
                    "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                    "TTS prompt profile is invalid.",
                    status=503,
                )
            semantic_id = item.get("semantic_profile_id")
            prompt = item.get("prompt")
            if not isinstance(semantic_id, str) or not isinstance(prompt, str):
                raise _google_error(
                    "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                    "TTS prompt profile is invalid.",
                    status=503,
                )
            encoded = prompt.encode("utf-8")
            if (
                item.get("provider_voice") != GOOGLE_VOICE_MAP.get(semantic_id)
                or item.get("model") != GOOGLE_TTS_MODEL
                or item.get("locale") != GOOGLE_TTS_LOCALE
                or item.get("endpoint") != GOOGLE_TTS_ENDPOINT
                or item.get("prompt_contract_version") != GOOGLE_PROMPT_CONTRACT_VERSION
                or item.get("prompt_utf8_bytes") != len(encoded)
                or item.get("prompt_sha256") != hashlib.sha256(encoded).hexdigest()
            ):
                raise _google_error(
                    "GOOGLE_TTS_PROMPT_CONTRACT_INVALID",
                    "TTS prompt profile binding is invalid.",
                    status=503,
                )
            by_id[semantic_id] = item
        if set(by_id) != set(GOOGLE_VOICE_MAP) or presenter_id not in by_id:
            raise _google_error(
                "PRESENTER_NOT_ALLOWLISTED", "Presenter is not allowlisted for TTS."
            )
        return by_id[presenter_id]

    def _request_body(
        self, receipt: TTSConsumptionReceipt, profile: dict[str, Any]
    ) -> dict[str, object]:
        return {
            "input": {"text": receipt.spoken_text, "prompt": cast(str, profile["prompt"])},
            "voice": {
                "languageCode": GOOGLE_TTS_LOCALE,
                "modelName": GOOGLE_TTS_MODEL,
                "name": cast(str, profile["provider_voice"]),
            },
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": GOOGLE_SAMPLE_RATE},
        }

    def _fingerprint(
        self, receipt: TTSConsumptionReceipt, profile: dict[str, Any], body: dict[str, object]
    ) -> str:
        return _google_sha(
            {
                "requestChecksum": self._request_contract_checksum(receipt, profile, body),
                "receiptChecksum": receipt.receipt_checksum,
                "activationRecordSha256": self.config.activation_record_sha256,
                "configChecksum": self._config_checksum(),
            }
        )

    def _request_contract_checksum(
        self, receipt: TTSConsumptionReceipt, profile: dict[str, Any], body: dict[str, object]
    ) -> str:
        return _google_sha(
            {
                "method": "POST",
                "url": GOOGLE_TTS_URL,
                "orderedHeaderNames": [
                    "Authorization",
                    "Content-Type",
                    "x-goog-user-project",
                ],
                "orderedJson": body,
                "semanticPresenterId": receipt.presenter_id,
                "promptContractVersion": GOOGLE_PROMPT_CONTRACT_VERSION,
                "promptSha256": cast(str, profile["prompt_sha256"]),
                "output": {
                    "container": "WAV",
                    "encoding": "PCM16",
                    "sampleRateHertz": 24_000,
                    "channels": 1,
                },
                "costPolicy": {
                    "inputMicrousdPerMillionTokens": GOOGLE_INPUT_PRICE_MICROUSD_PER_MILLION_TOKENS,
                    "outputMicrousdPerMillionTokens": GOOGLE_OUTPUT_PRICE_MICROUSD_PER_MILLION_TOKENS,
                    "outputTokensPerSecond": 25,
                },
                "quotaProjectRequired": True,
                "approvedQuotaProjectIdSha256": self.config.approved_quota_project_sha256,
            }
        )

    def _config_checksum(self) -> str:
        return _google_sha(
            {
                "activationRecordSha256": self.config.activation_record_sha256,
                "approvedQuotaProjectIdSha256": self.config.approved_quota_project_sha256,
                "activationExpiresAt": self.config.activation_expires_at,
                "budgetAudioTokens": self.config.budget_audio_tokens,
                "budgetMicrousd": self.config.budget_microusd,
                "enabled": self.config.enabled,
                "maxConcurrentRequests": self.config.max_concurrent_requests,
                "policyApproved": self.config.policy_approved,
                "privacyApproved": self.config.privacy_approved,
                "quotaRequests": self.config.quota_requests,
                "timeoutSeconds": self.config.timeout_seconds,
                "inputMicrousdPerMillionTokens": GOOGLE_INPUT_PRICE_MICROUSD_PER_MILLION_TOKENS,
                "outputMicrousdPerMillionTokens": GOOGLE_OUTPUT_PRICE_MICROUSD_PER_MILLION_TOKENS,
            }
        )

    def _validate_identity(self, identity: GoogleIdentity) -> None:
        if (
            not isinstance(identity, GoogleIdentity)
            or not isinstance(identity.access_token, str)
            or not identity.access_token
            or len(identity.access_token) > 16_384
            or not identity.access_token.isascii()
            or any(character.isspace() for character in identity.access_token)
            or "\n" in identity.access_token
            or "\r" in identity.access_token
            or not isinstance(identity.identity_evidence_sha256, str)
            or not GOOGLE_CHECKSUM_PATTERN.fullmatch(identity.identity_evidence_sha256)
            or not isinstance(identity.quota_project_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", identity.quota_project_id)
            or not isinstance(identity.quota_project_sha256, str)
            or not GOOGLE_CHECKSUM_PATTERN.fullmatch(identity.quota_project_sha256)
            or not hmac.compare_digest(
                identity.quota_project_sha256,
                self.config.approved_quota_project_sha256,
            )
            or not hmac.compare_digest(
                identity.quota_project_sha256,
                "sha256:" + hashlib.sha256(identity.quota_project_id.encode("utf-8")).hexdigest(),
            )
        ):
            raise _google_error(
                "GOOGLE_TTS_IDENTITY_INVALID", "TTS runtime identity is invalid.", status=403
            )

    def _request_headers(self, identity: GoogleIdentity) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {identity.access_token}",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-user-project": identity.quota_project_id,
        }

    def _validate_request_headers(self, headers: dict[str, str], identity: GoogleIdentity) -> None:
        expected_names = ("Authorization", "Content-Type", "x-goog-user-project")
        quota_value = headers.get("x-goog-user-project")
        if (
            tuple(headers) != expected_names
            or headers.get("Authorization") != f"Bearer {identity.access_token}"
            or headers.get("Content-Type") != "application/json; charset=utf-8"
            or not isinstance(quota_value, str)
            or not hmac.compare_digest(quota_value, identity.quota_project_id)
            or not hmac.compare_digest(
                "sha256:" + hashlib.sha256(quota_value.encode("utf-8")).hexdigest(),
                self.config.approved_quota_project_sha256,
            )
        ):
            raise _google_error(
                "GOOGLE_TTS_REQUEST_HEADERS_INVALID",
                "Google TTS request headers are invalid.",
                status=403,
            )

    def _response_audio(
        self,
        response: GoogleTTSHTTPResponse,
        prepared: GoogleTTSPreparedTransport,
    ) -> bytes:
        if (
            not isinstance(response, GoogleTTSHTTPResponse)
            or not isinstance(response.status_code, int)
            or isinstance(response.status_code, bool)
            or not 100 <= response.status_code <= 599
            or not isinstance(response.headers, dict)
            or any(
                not isinstance(key, str) or not isinstance(value, str)
                for key, value in response.headers.items()
            )
            or not isinstance(response.body, bytes)
            or not isinstance(response.redirect_count, int)
            or isinstance(response.redirect_count, bool)
        ):
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID",
                "Google TTS response schema is invalid.",
                status=502,
                billable=True,
            )
        self._validate_transport_evidence(response, prepared)
        if len(response.body) > GOOGLE_MAX_RESPONSE_BYTES:
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SIZE_INVALID",
                "Google TTS response size is invalid.",
                status=502,
                billable=True,
            )
        if not 200 <= response.status_code < 300:
            raise _google_error(
                "GOOGLE_TTS_PROVIDER_FAILURE",
                "Google TTS returned a non-success status.",
                status=502,
                billable=True,
                provider_diagnostics=_google_failure_diagnostics(response),
            )
        content_type = response.headers.get("content-type", "").lower().replace(" ", "")
        if content_type not in {"application/json", "application/json;charset=utf-8"}:
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID",
                "Google TTS response type is invalid.",
                status=502,
                billable=True,
            )
        if not response.body:
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SIZE_INVALID",
                "Google TTS response size is invalid.",
                status=502,
                billable=True,
            )
        try:
            payload = json.loads(
                response.body.decode("utf-8"), object_pairs_hook=_google_json_object
            )
        except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateGoogleKey):
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID",
                "Google TTS response schema is invalid.",
                status=502,
                billable=True,
            ) from None
        if (
            not isinstance(payload, dict)
            or set(payload) != {"audioContent"}
            or not isinstance(payload["audioContent"], str)
        ):
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID",
                "Google TTS response schema is invalid.",
                status=502,
                billable=True,
            )
        encoded = payload["audioContent"]
        if not encoded:
            raise _google_error(
                "GOOGLE_TTS_AUDIO_INVALID", "Google TTS audio is empty.", status=502, billable=True
            )
        if len(encoded) > ((GOOGLE_MAX_AUDIO_BYTES + 2) // 3) * 4:
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_BASE64_INVALID",
                "Google TTS audio encoding is invalid.",
                status=502,
                billable=True,
            )
        try:
            audio = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise _google_error(
                "GOOGLE_TTS_RESPONSE_BASE64_INVALID",
                "Google TTS audio encoding is invalid.",
                status=502,
                billable=True,
            ) from None
        if not audio or len(audio) > GOOGLE_MAX_AUDIO_BYTES:
            raise _google_error(
                "GOOGLE_TTS_AUDIO_INVALID",
                "Google TTS audio is empty or oversized.",
                status=502,
                billable=True,
            )
        return audio

    def _validate_prepared_transport(self, prepared: GoogleTTSPreparedTransport) -> None:
        if getattr(prepared, "transport_kind", None) not in {
            "REST_HTTP_1_1",
            "OFFICIAL_GRPC_UNARY",
        }:
            raise _google_error(
                "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                "Google TTS transport policy evidence is invalid.",
                status=502,
            )
        self._validate_network_evidence(
            url=prepared.url,
            resolved_addresses=prepared.resolved_addresses,
            peer_ip=prepared.peer_ip,
            proxy_used=prepared.proxy_used,
            tls_verified=prepared.tls_verified,
            tls_server_name=prepared.tls_server_name,
            peer_port=prepared.peer_port,
            redirects_ok=prepared.redirects_disabled,
            dns_pinned=prepared.dns_pinned,
        )

    @staticmethod
    def _close_prepared(prepared: GoogleTTSPreparedTransport) -> None:
        close = getattr(prepared, "close", None)
        if callable(close):
            try:
                close()
            except OSError:
                pass

    def _validate_transport_evidence(
        self,
        response: GoogleTTSHTTPResponse,
        prepared: GoogleTTSPreparedTransport,
    ) -> None:
        if (
            response.transport_kind != prepared.transport_kind
            or response.transport_kind not in {"REST_HTTP_1_1", "OFFICIAL_GRPC_UNARY"}
            or response.resolved_addresses != prepared.resolved_addresses
            or response.peer_ip != prepared.peer_ip
        ):
            raise _google_error(
                "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                "Google TTS transport policy evidence is invalid.",
                status=502,
                billable=True,
            )
        self._validate_network_evidence(
            url=response.final_url,
            resolved_addresses=response.resolved_addresses,
            peer_ip=response.peer_ip,
            proxy_used=response.proxy_used,
            tls_verified=response.tls_verified,
            tls_server_name=response.tls_server_name,
            peer_port=response.peer_port,
            redirects_ok=response.redirect_count == 0,
            dns_pinned=True,
            billable=True,
        )

    def _validate_network_evidence(
        self,
        *,
        url: str,
        resolved_addresses: tuple[str, ...],
        peer_ip: str,
        proxy_used: bool,
        tls_verified: bool,
        tls_server_name: str,
        peer_port: int,
        redirects_ok: bool,
        dns_pinned: bool,
        billable: bool = False,
    ) -> None:
        if (
            not isinstance(url, str)
            or not isinstance(resolved_addresses, tuple)
            or any(not isinstance(value, str) for value in resolved_addresses)
            or not isinstance(peer_ip, str)
            or not isinstance(proxy_used, bool)
            or not isinstance(tls_verified, bool)
            or not isinstance(tls_server_name, str)
            or not isinstance(peer_port, int)
            or isinstance(peer_port, bool)
            or not isinstance(redirects_ok, bool)
            or not isinstance(dns_pinned, bool)
        ):
            raise _google_error(
                "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                "Google TTS transport policy evidence is invalid.",
                status=502,
                billable=billable,
            )
        try:
            peer = ipaddress.ip_address(peer_ip)
            resolved = tuple(ipaddress.ip_address(value) for value in resolved_addresses)
        except (TypeError, ValueError):
            raise _google_error(
                "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                "Google TTS transport policy evidence is invalid.",
                status=502,
                billable=billable,
            ) from None
        if (
            url != GOOGLE_TTS_URL
            or not redirects_ok
            or not dns_pinned
            or proxy_used
            or not tls_verified
            or tls_server_name != "eu-texttospeech.googleapis.com"
            or peer_port != 443
            or not resolved
            or peer not in resolved
            or any(
                value.is_private
                or value.is_loopback
                or value.is_link_local
                or value.is_multicast
                or value.is_unspecified
                or value.is_reserved
                for value in resolved
            )
        ):
            raise _google_error(
                "GOOGLE_TTS_TRANSPORT_POLICY_INVALID",
                "Google TTS transport policy evidence is invalid.",
                status=502,
                billable=billable,
            )

    def _set_state(self, fingerprint: str, state: GoogleSpendState) -> None:
        with self._lock:
            entry = self._ledger[fingerprint]
            entry.state = state
            entry.result = None
            try:
                self._persist_locked()
            except Exception:
                entry.state = "BILLABLE_UNKNOWN"
                raise _google_error(
                    "GOOGLE_TTS_STATE_PERSISTENCE_FAILED",
                    "TTS billing state could not be durably updated.",
                    status=503,
                    billable=True,
                ) from None
        self._log(state.lower(), fingerprint, None)

    def _drop_pre_egress(self, fingerprint: str) -> None:
        with self._lock:
            self._ledger.pop(fingerprint, None)
            try:
                self._persist_locked()
            except OSError:
                # The durable PENDING row is intentionally left ambiguous; restore
                # converts it to BILLABLE_UNKNOWN and therefore never re-egresses.
                pass

    # fmt: off
    def _validate_stored_result(self, result: GoogleTTSResult,
                                receipt: TTSConsumptionReceipt,
                                profile: dict[str, Any], body: dict[str, object],
                                fingerprint: str,
                                screening: GoogleEgressScreening) -> None:
        measurements = validate_google_wav(result.audio_bytes)
        expected_output_tokens = math.ceil(measurements.duration_seconds * 25)
        expected_input_tokens = (len(receipt.spoken_text.encode("utf-8"))
                                 + len(cast(str, profile["prompt"]).encode("utf-8")))
        if (
            result.provider != self.provider or result.provider_mode != self.provider_mode
            or result.presenter_id != receipt.presenter_id or result.requested_voice != profile["provider_voice"]
            or result.requested_locale != GOOGLE_TTS_LOCALE or result.model_id != GOOGLE_TTS_MODEL
            or result.endpoint_region != "EU" or result.effective_voice_verified is not False
            or result.prompt_contract_version != GOOGLE_PROMPT_CONTRACT_VERSION
            or result.prompt_sha256 != "sha256:" + cast(str, profile["prompt_sha256"])
            or result.request_fingerprint != fingerprint
            or result.request_checksum != self._request_contract_checksum(receipt, profile, body)
            or result.receipt_checksum != receipt.receipt_checksum
            or result.screening_policy_version != screening.policy_version or result.screening_result != "PASS"
            or result.screening_evidence_checksum != screening.evidence_checksum
            or result.reserved_input_tokens != expected_input_tokens
            or result.reserved_output_tokens != GOOGLE_MAX_DURATION_SECONDS * 25
            or result.reserved_cost_microusd != _google_cost_microusd(expected_input_tokens, GOOGLE_MAX_DURATION_SECONDS * 25)
            or result.actual_output_tokens != expected_output_tokens
            or result.actual_cost_microusd != _google_cost_microusd(expected_input_tokens, expected_output_tokens)
            or result.artifact_checksum != "sha256:" + hashlib.sha256(result.audio_bytes).hexdigest()
            or result.config_checksum != self._config_checksum()
            or GOOGLE_CHECKSUM_PATTERN.fullmatch(result.identity_evidence_sha256) is None
            or measurements != result.measurements or result.spend_state != "COMPLETED"
            or result.retention_state != "LOCAL_ACTIVE_PROVIDER_RETENTION_UNKNOWN"
            or result.deletion_state != "ACTIVE" or result.attempt_count != 1
        ):
            raise _google_error("GOOGLE_TTS_STORED_RESULT_INVALID",
                                "Stored TTS result is invalid.", status=409, billable=True)

    def _state_payload_locked(self) -> dict[str, object]:
        rows: list[dict[str, object]] = []
        for entry in self._ledger.values():
            row: dict[str, object] = {
                "fingerprint": entry.fingerprint, "receiptChecksum": entry.receipt_checksum,
                "state": entry.state, "reservedInputTokens": entry.reserved_input_tokens,
                "reservedOutputTokens": entry.reserved_output_tokens,
                "reservedCostMicrousd": entry.reserved_cost_microusd,
            }
            if entry.deletion_checksum is not None:
                row["deletionChecksum"] = entry.deletion_checksum
            if entry.result is not None:
                result = entry.result
                row["result"] = {
                    "provider": result.provider, "providerMode": result.provider_mode,
                    "presenterId": result.presenter_id, "requestedVoice": result.requested_voice,
                    "requestedLocale": result.requested_locale, "modelId": result.model_id,
                    "endpointRegion": result.endpoint_region, "effectiveVoiceVerified": result.effective_voice_verified,
                    "promptContractVersion": result.prompt_contract_version, "promptSha256": result.prompt_sha256,
                    "requestFingerprint": result.request_fingerprint, "requestChecksum": result.request_checksum,
                    "configChecksum": result.config_checksum, "identityEvidenceSha256": result.identity_evidence_sha256,
                    "receiptChecksum": result.receipt_checksum, "screeningPolicyVersion": result.screening_policy_version,
                    "screeningResult": result.screening_result, "screeningEvidenceChecksum": result.screening_evidence_checksum,
                    "reservedInputTokens": result.reserved_input_tokens, "reservedOutputTokens": result.reserved_output_tokens,
                    "reservedCostMicrousd": result.reserved_cost_microusd, "actualOutputTokens": result.actual_output_tokens,
                    "actualCostMicrousd": result.actual_cost_microusd, "artifactChecksum": result.artifact_checksum,
                    "audioBase64": base64.b64encode(result.audio_bytes).decode("ascii"),
                    "measurements": result.measurements.__dict__, "spendState": result.spend_state,
                    "retentionState": result.retention_state, "deletionState": result.deletion_state,
                    "attemptCount": result.attempt_count,
                }
            rows.append(row)
        unsigned = {"schema": GOOGLE_STATE_SCHEMA, "requests": rows}
        return {**unsigned, "stateChecksum": _google_sha(unsigned)}

    def _persist_locked(self) -> None:
        if self.state_path is not None:
            write_state(self.state_path, self._state_payload_locked())

    def _restore(self) -> None:
        if self.state_path is None:
            return
        try:
            if self.state_path.is_symlink():
                raise ValueError("symlink")
            if not self.state_path.exists():
                return
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self.state_path, flags)
            with os.fdopen(descriptor, "rb") as handle:
                raw = handle.read(GOOGLE_MAX_STATE_BYTES + 1)
            if not raw or len(raw) > GOOGLE_MAX_STATE_BYTES:
                raise ValueError("state size")
            payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_google_json_object)
            if not isinstance(payload, dict):
                raise ValueError("state type")
            if set(payload) != {"schema", "requests", "stateChecksum"}:
                raise ValueError("fields")
            unsigned = {"schema": payload.get("schema"), "requests": payload.get("requests")}
            if payload.get("schema") != GOOGLE_STATE_SCHEMA or not isinstance(payload.get("requests"), list):
                raise ValueError("schema")
            if payload.get("stateChecksum") != _google_sha(unsigned):
                raise ValueError("state checksum")
            if len(payload["requests"]) > min(self.config.quota_requests, GOOGLE_MAX_LEDGER_ROWS):
                raise ValueError("row count")
            for row in payload["requests"]:
                if not isinstance(row, dict) or set(row) - {
                    "fingerprint", "receiptChecksum", "state", "result", "deletionChecksum",
                    "reservedInputTokens", "reservedOutputTokens", "reservedCostMicrousd",
                }:
                    raise ValueError("row")
                if not {
                    "fingerprint", "receiptChecksum", "state", "reservedInputTokens",
                    "reservedOutputTokens", "reservedCostMicrousd",
                } <= set(row):
                    raise ValueError("row fields")
                fingerprint = cast(str, row["fingerprint"])
                receipt_checksum = cast(str, row["receiptChecksum"])
                state = cast(GoogleSpendState, row["state"])
                reserved_input_tokens = row["reservedInputTokens"]
                reserved_output_tokens = row["reservedOutputTokens"]
                reserved_cost_microusd = row["reservedCostMicrousd"]
                if (not GOOGLE_CHECKSUM_PATTERN.fullmatch(fingerprint)
                        or not GOOGLE_CHECKSUM_PATTERN.fullmatch(receipt_checksum)):
                    raise ValueError("checksum")
                if (
                    not _google_positive_int(reserved_input_tokens)
                    or not _google_positive_int(reserved_output_tokens)
                    or not _google_positive_int(reserved_cost_microusd)
                    or reserved_input_tokens > 8_000
                    or reserved_output_tokens > GOOGLE_MAX_DURATION_SECONDS * 25
                ):
                    raise ValueError("reservation")
                if state not in {
                    "PENDING", "COMPLETED", "FAILED_BILLABLE", "BILLABLE_UNKNOWN", "TOMBSTONED",
                }:
                    raise ValueError("state")
                if (state == "COMPLETED") != ("result" in row):
                    raise ValueError("result state")
                if state != "TOMBSTONED" and "deletionChecksum" in row:
                    raise ValueError("deletion state")
                if state == "PENDING":
                    state = "BILLABLE_UNKNOWN"
                result = self._result_from_state(row.get("result")) if state == "COMPLETED" else None
                if state == "COMPLETED" and (
                    result is None
                    or result.request_fingerprint != fingerprint
                    or result.receipt_checksum != receipt_checksum
                ):
                    raise ValueError("binding")
                if (state == "COMPLETED" and result is not None and (
                        reserved_input_tokens != result.reserved_input_tokens
                        or reserved_output_tokens != result.actual_output_tokens
                        or reserved_cost_microusd != result.actual_cost_microusd
                )):
                    raise ValueError("reconciliation")
                if fingerprint in self._ledger:
                    raise ValueError("duplicate")
                deletion_checksum = cast(str | None, row.get("deletionChecksum"))
                if state == "TOMBSTONED":
                    expected_deletion = _google_sha(
                        {
                            "deletionState": "TOMBSTONED", "fingerprint": fingerprint,
                            "providerRetention": "UNKNOWN_NO_PROVIDER_DELETE_API_CLAIM",
                            "receiptChecksum": receipt_checksum,
                        }
                    )
                    if deletion_checksum != expected_deletion:
                        raise ValueError("deletion")
                elif deletion_checksum is not None:
                    raise ValueError("deletion state")
                self._ledger[fingerprint] = _GoogleLedgerEntry(
                    fingerprint, receipt_checksum, state, cast(int, reserved_input_tokens),
                    cast(int, reserved_output_tokens), cast(int, reserved_cost_microusd),
                    result, deletion_checksum,
                )
        except (
            OSError, UnicodeDecodeError, json.JSONDecodeError, _DuplicateGoogleKey,
            KeyError, TypeError, ValueError, binascii.Error, TTSProviderError,
        ):
            self._ledger.clear()
            raise _google_error(
                "GOOGLE_TTS_STATE_INVALID", "Persisted TTS state is invalid.", status=503
            ) from None

    def _result_from_state(self, value: object) -> GoogleTTSResult | None:
        if not isinstance(value, dict):
            return None
        expected_fields = {
            "provider", "providerMode", "presenterId", "requestedVoice", "requestedLocale",
            "modelId", "endpointRegion", "effectiveVoiceVerified", "promptContractVersion",
            "promptSha256", "requestFingerprint", "requestChecksum", "configChecksum",
            "identityEvidenceSha256", "receiptChecksum", "screeningPolicyVersion",
            "screeningResult", "screeningEvidenceChecksum", "reservedInputTokens",
            "reservedOutputTokens", "reservedCostMicrousd", "actualOutputTokens",
            "actualCostMicrousd", "artifactChecksum", "audioBase64", "measurements",
            "spendState", "retentionState", "deletionState", "attemptCount",
        }
        if set(value) != expected_fields:
            raise ValueError("result fields")
        encoded = value["audioBase64"]
        if (
            not isinstance(encoded, str)
            or not encoded
            or len(encoded) > ((GOOGLE_MAX_AUDIO_BYTES + 2) // 3) * 4
        ):
            raise ValueError("result audio size")
        audio = base64.b64decode(encoded, validate=True)
        if not audio or len(audio) > GOOGLE_MAX_AUDIO_BYTES:
            raise ValueError("result audio")
        measurement_value = value["measurements"]
        measurement_fields = {
            "duration_seconds", "sample_rate_hertz", "channels", "bits_per_sample",
            "frame_count", "rms", "peak", "active_ratio", "clipping_ratio",
            "zero_crossing_interval_kinds",
        }
        if not isinstance(measurement_value, dict) or set(measurement_value) != measurement_fields:
            raise ValueError("measurements")
        measurement_ints = {
            "sample_rate_hertz", "channels", "bits_per_sample", "frame_count", "peak",
            "zero_crossing_interval_kinds",
        }
        measurement_floats = {"duration_seconds", "rms", "active_ratio", "clipping_ratio"}
        if any(
            not _google_positive_int(measurement_value[field]) for field in measurement_ints
        ) or any(
            not isinstance(measurement_value[field], (int, float))
            or isinstance(measurement_value[field], bool)
            for field in measurement_floats
        ):
            raise ValueError("measurement types")
        string_fields = expected_fields - {
            "effectiveVoiceVerified", "reservedInputTokens", "reservedOutputTokens",
            "reservedCostMicrousd", "actualOutputTokens", "actualCostMicrousd",
            "audioBase64", "measurements", "attemptCount",
        }
        if any(not isinstance(value[field], str) for field in string_fields):
            raise ValueError("result strings")
        integer_fields = {
            "reservedInputTokens", "reservedOutputTokens", "reservedCostMicrousd",
            "actualOutputTokens", "actualCostMicrousd", "attemptCount",
        }
        if any(not _google_positive_int(value[field]) for field in integer_fields):
            raise ValueError("result integers")
        if not isinstance(value["effectiveVoiceVerified"], bool):
            raise ValueError("result bool")
        measurements = GoogleAudioMeasurements(**cast(dict[str, Any], measurement_value))
        result = GoogleTTSResult(
            provider=cast(str, value["provider"]), provider_mode=cast(str, value["providerMode"]),
            presenter_id=cast(str, value["presenterId"]), requested_voice=cast(str, value["requestedVoice"]),
            requested_locale=cast(str, value["requestedLocale"]), model_id=cast(str, value["modelId"]),
            endpoint_region=cast(str, value["endpointRegion"]),
            effective_voice_verified=value["effectiveVoiceVerified"],
            prompt_contract_version=cast(str, value["promptContractVersion"]), prompt_sha256=cast(str, value["promptSha256"]),
            request_fingerprint=cast(str, value["requestFingerprint"]), request_checksum=cast(str, value["requestChecksum"]),
            config_checksum=cast(str, value["configChecksum"]), identity_evidence_sha256=cast(str, value["identityEvidenceSha256"]),
            receipt_checksum=cast(str, value["receiptChecksum"]), artifact_checksum=cast(str, value["artifactChecksum"]),
            mime_type="audio/wav",
            screening_policy_version=cast(str, value["screeningPolicyVersion"]), screening_result=cast(str, value["screeningResult"]),
            screening_evidence_checksum=cast(str, value["screeningEvidenceChecksum"]),
            reserved_input_tokens=cast(int, value["reservedInputTokens"]), reserved_output_tokens=cast(int, value["reservedOutputTokens"]),
            reserved_cost_microusd=cast(int, value["reservedCostMicrousd"]), actual_output_tokens=cast(int, value["actualOutputTokens"]),
            actual_cost_microusd=cast(int, value["actualCostMicrousd"]), audio_bytes=audio, measurements=measurements,
            spend_state=cast(GoogleSpendState, value["spendState"]),
            retention_state=cast(str, value["retentionState"]), deletion_state=cast(str, value["deletionState"]),
            attempt_count=cast(int, value["attemptCount"]),
        )
        validate_google_wav(audio)
        return result

    def _log(self, event: str, fingerprint: str, presenter_id: str | None) -> None:
        GOOGLE_LOGGER.info(
            "google_tts event=%s fingerprint=%s presenter=%s endpoint_region=EU",
            event,
            fingerprint,
            presenter_id or "none",
        )


# fmt: off
def _google_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _google_cost_microusd(input_tokens: int, output_tokens: int) -> int:
    numerator = (input_tokens * GOOGLE_INPUT_PRICE_MICROUSD_PER_MILLION_TOKENS
                 + output_tokens * GOOGLE_OUTPUT_PRICE_MICROUSD_PER_MILLION_TOKENS)
    return math.ceil(numerator / 1_000_000)


def screen_google_tts_egress(receipt: TTSConsumptionReceipt) -> GoogleEgressScreening:
    """Return versioned, non-content screening evidence for approved narration."""
    text = receipt.spoken_text
    lowered = text.lower()
    secret_fragments = ("begin private key", "authorization: bearer", "service_account",
                        "refresh_token", "api_key=", "apikey=", "password=", "secret=")
    patterns = (
        r"\b[A-Za-z0-9._%+-]+@(?!stackclimb\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        r"(?<!\d)(?:\+?\d[\s().-]*){10,15}(?!\d)",
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        r"(?<!\d)(?:\d[ -]?){12}(?!\d)",
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
    )
    rejected = any(fragment in lowered for fragment in secret_fragments) or any(
        re.search(pattern, text) is not None for pattern in patterns
    )
    result: Literal["PASS", "REJECT"] = "REJECT" if rejected else "PASS"
    return GoogleEgressScreening(GOOGLE_EGRESS_SCREEN_POLICY_VERSION, result, _google_sha({
        "narrationChecksum": receipt.narration_checksum,
        "policyVersion": GOOGLE_EGRESS_SCREEN_POLICY_VERSION, "result": result,
    }))


def validate_google_wav(audio: bytes) -> GoogleAudioMeasurements:
    if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise _google_error("GOOGLE_TTS_AUDIO_INVALID",
                            "Google TTS audio container is invalid.", status=502, billable=True)
    if struct.unpack_from("<I", audio, 4)[0] != len(audio) - 8:
        raise _google_error("GOOGLE_TTS_AUDIO_INVALID",
                            "Google TTS audio length is invalid.", status=502, billable=True)
    offset = 12
    fmt: tuple[int, int, int, int, int, int] | None = None
    pcm: bytes | None = None
    seen: set[bytes] = set()
    while offset < len(audio):
        if offset + 8 > len(audio):
            raise _google_error("GOOGLE_TTS_AUDIO_INVALID",
                                "Google TTS audio is truncated.", status=502, billable=True)
        chunk_id = audio[offset : offset + 4]
        size = struct.unpack_from("<I", audio, offset + 4)[0]
        start, end = offset + 8, offset + 8 + size
        if chunk_id in seen or chunk_id not in {b"fmt ", b"data"} or end > len(audio) or size % 2:
            raise _google_error("GOOGLE_TTS_AUDIO_INVALID",
                                "Google TTS audio chunks are invalid.", status=502, billable=True)
        seen.add(chunk_id)
        if chunk_id == b"fmt ":
            if size != 16:
                raise _google_error("GOOGLE_TTS_AUDIO_FORMAT_INVALID",
                                    "Google TTS audio format is invalid.", status=502, billable=True)
            fmt = struct.unpack_from("<HHIIHH", audio, start)
        else:
            pcm = audio[start:end]
        offset = end
    if offset != len(audio) or fmt is None or pcm is None or seen != {b"fmt ", b"data"}:
        raise _google_error(
            "GOOGLE_TTS_AUDIO_INVALID", "Google TTS audio is incomplete.", status=502, billable=True
        )
    audio_format, channels, sample_rate, byte_rate, block_align, bits = fmt
    if (
        (audio_format, channels, sample_rate, byte_rate, block_align, bits)
        != (1, 1, GOOGLE_SAMPLE_RATE, GOOGLE_SAMPLE_RATE * 2, 2, 16)
        or not pcm
        or len(pcm) % 2
    ):
        raise _google_error("GOOGLE_TTS_AUDIO_FORMAT_INVALID",
                            "Google TTS audio format is invalid.", status=502, billable=True)
    frame_count = len(pcm) // 2
    duration = frame_count / GOOGLE_SAMPLE_RATE
    if not GOOGLE_MIN_DURATION_SECONDS <= duration <= GOOGLE_MAX_DURATION_SECONDS:
        raise _google_error("GOOGLE_TTS_AUDIO_DURATION_INVALID",
                            "Google TTS audio duration is invalid.", status=502, billable=True)
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(value) for value in samples)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    active_ratio = sum(abs(value) >= 300 for value in samples) / len(samples)
    clipping_ratio = sum(abs(value) >= 32_000 for value in samples) / len(samples)
    crossings: list[int] = []
    previous_sign = samples[0] >= 0
    last_crossing = 0
    for index, value in enumerate(samples[1 : min(len(samples), GOOGLE_SAMPLE_RATE * 10)], start=1):
        sign = value >= 0
        if sign != previous_sign:
            crossings.append(index - last_crossing)
            last_crossing = index
            previous_sign = sign
    interval_kinds = len(set(crossings))
    if peak < 500 or rms < 200 or active_ratio < 0.05:
        raise _google_error("GOOGLE_TTS_AUDIO_SILENT",
                            "Google TTS audio signal is silent or near-silent.", status=502, billable=True)
    if len(crossings) < 8 or interval_kinds <= 2:
        raise _google_error("GOOGLE_TTS_AUDIO_TONE_INVALID",
                            "Google TTS audio signal is tone-only.", status=502, billable=True)
    if clipping_ratio > 0.02:
        raise _google_error("GOOGLE_TTS_AUDIO_CLIPPED",
                            "Google TTS audio signal is clipped.", status=502, billable=True)
    return GoogleAudioMeasurements(duration, sample_rate, channels, bits, frame_count, rms,
                                   peak, active_ratio, clipping_ratio, interval_kinds)

# fmt: on
