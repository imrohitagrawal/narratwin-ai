"""Optional server-side TTS provider boundary for Stage 6.

The module deliberately uses an injected transport so local/dev/test/CI never
need provider SDKs, secrets, or network access.

Stage 6 validates sourceContextRefIds and citation_indexes before calling this
boundary; this module does not generate scripts, answers, or citations.
"""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from backend.app.rag.chunking import checksum_text

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
    ) -> TTSHTTPResponse:
        ...


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
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.billable = billable


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
            if self._committed_characters + self._reserved_characters + characters > self.character_limit:
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
            raise TTSProviderError(422, "TTS_PROVIDER_CONFIG_INVALID", "TTS provider config is invalid.")
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
            raise TTSProviderError(422, "TTS_PROVIDER_CONFIG_INVALID", "TTS voice configuration is invalid.")

    def _validate_request(self, *, cleaned_text: str, language: str) -> None:
        if not cleaned_text:
            raise TTSProviderError(422, "TTS_SCRIPT_EMPTY", "TTS input is required.")
        if len(cleaned_text) > self.config.max_input_characters:
            raise TTSProviderError(413, "TTS_SCRIPT_TOO_LARGE", "TTS input exceeds the provider limit.")
        if language not in self.config.supported_languages:
            raise TTSProviderError(422, "TTS_LANGUAGE_UNSUPPORTED", "TTS provider does not support this language.")

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
            return TTSProviderError(403, "TTS_PROVIDER_AUTH_FAILED", "TTS provider authentication failed.")
        if status == 402:
            return TTSProviderError(402, "TTS_PROVIDER_PAYMENT_REQUIRED", "TTS provider payment is required.")
        return TTSProviderError(502, "TTS_PROVIDER_FAILURE", "TTS provider returned an invalid status.")

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
            raise TTSProviderError(502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider response is invalid.")
        if content_type not in SUPPORTED_AUDIO_MIME_TYPES:
            raise TTSProviderError(502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider audio type is invalid.")
        if not response.body:
            raise TTSProviderError(502, "TTS_PROVIDER_RESPONSE_INVALID", "TTS provider returned empty audio.")
        if len(response.body) > self.config.max_audio_bytes:
            raise TTSProviderError(413, "TTS_PROVIDER_AUDIO_TOO_LARGE", "TTS provider audio exceeds the size limit.")
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
