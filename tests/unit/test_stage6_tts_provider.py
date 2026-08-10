import base64
import json
import struct
from dataclasses import replace
from pathlib import Path

import pytest
from typing import Any

from backend.app.tts_provider import (
    ElevenLabsTTSProvider,
    InMemoryTTSQuotaLedger,
    TTSHTTPResponse,
    TTSProviderConfig,
    TTSProviderError,
    GoogleGeminiTTSProvider,
    GoogleIdentity,
    GoogleTTSConfig,
    GoogleTransportError,
)
from backend.app.narration import TTSConsumptionReceipt


class FakeTransport:
    def __init__(self, responses: list[TTSHTTPResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> TTSHTTPResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json_body": json_body,
                "timeout_seconds": timeout_seconds,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def config(**overrides: object) -> TTSProviderConfig:
    values: dict[str, Any] = {
        "provider_id": "elevenlabs",
        "enabled": True,
        "api_key": "sk_" + ("a" * 32),
        "voice_id": "stock_voice_001",
        "voice_provenance": "stock",
        "model_id": "eleven_flash_v2_5",
        "model_version": "2026-07-21-source-facts",
        "supported_languages": ("en", "es", "fr", "hi"),
        "max_input_characters": 4_000,
        "max_audio_bytes": 128,
        "timeout_seconds": 2.0,
        "max_retries": 2,
        "retry_backoff_seconds": 0.0,
        "max_concurrent_requests": 1,
    }
    values.update(overrides)
    return TTSProviderConfig(**values)


def test_disabled_missing_and_invalid_key_states_do_not_call_transport() -> None:
    for provider_config, expected_code in (
        (config(enabled=False), "TTS_PROVIDER_DISABLED"),
        (config(api_key=""), "TTS_PROVIDER_KEY_MISSING"),
        (config(api_key="short"), "TTS_PROVIDER_KEY_INVALID"),
        (config(voice_provenance="cloned"), "TTS_VOICE_PROVENANCE_UNSUPPORTED"),
    ):
        transport = FakeTransport([])
        provider = ElevenLabsTTSProvider(
            config=provider_config,
            transport=transport,
            quota_ledger=InMemoryTTSQuotaLedger(character_limit=100),
        )

        with pytest.raises(TTSProviderError) as exc:
            provider.synthesize(
                text="Grounded script.",
                language="en",
                request_id="req_001",
                trace_id="trace_001",
            )

        assert exc.value.code == expected_code
        assert transport.calls == []


def test_quota_is_reserved_before_transport_and_committed_on_success() -> None:
    transport = FakeTransport(
        [
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "audio/mpeg", "history-item-id": "hist_001"},
                body=b"mp3-bytes",
            )
        ]
    )
    ledger = InMemoryTTSQuotaLedger(character_limit=100)
    provider = ElevenLabsTTSProvider(config=config(), transport=transport, quota_ledger=ledger)

    result = provider.synthesize(
        text="Grounded script.",
        language="en",
        request_id="req_001",
        trace_id="trace_001",
    )

    assert transport.calls
    assert ledger.reservations["req_001"].state == "COMMITTED"
    assert ledger.reservations["req_001"].reserved_characters == len("Grounded script.")
    assert result.provider_history_item_id == "hist_001"
    assert result.audio_bytes == b"mp3-bytes"


def test_quota_exhaustion_blocks_before_transport() -> None:
    transport = FakeTransport([])
    provider = ElevenLabsTTSProvider(
        config=config(),
        transport=transport,
        quota_ledger=InMemoryTTSQuotaLedger(character_limit=3),
    )

    with pytest.raises(TTSProviderError) as exc:
        provider.synthesize(text="too long", language="en", request_id="req_001", trace_id="trace_001")

    assert exc.value.code == "TTS_QUOTA_EXHAUSTED"
    assert transport.calls == []


def test_timeout_retries_are_capped_and_refund_unaccepted_jobs() -> None:
    transport = FakeTransport([TimeoutError("raw timeout secret"), TimeoutError("second timeout")])
    ledger = InMemoryTTSQuotaLedger(character_limit=100)
    provider = ElevenLabsTTSProvider(
        config=config(max_retries=1),
        transport=transport,
        quota_ledger=ledger,
        sleep=lambda _seconds: None,
    )

    with pytest.raises(TTSProviderError) as exc:
        provider.synthesize(text="Grounded script.", language="en", request_id="req_001", trace_id="trace_001")

    assert exc.value.code == "TTS_PROVIDER_TIMEOUT"
    assert len(transport.calls) == 2
    assert ledger.reservations["req_001"].state == "REFUNDED"
    assert "raw timeout secret" not in exc.value.message


def test_malformed_unsafe_url_and_oversized_responses_refund() -> None:
    cases = (
        (
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=b'{"audio_url":"https://example.com/audio.mp3"}',
            ),
            "TTS_PROVIDER_RESPONSE_UNSAFE",
        ),
        (
            TTSHTTPResponse(status_code=200, headers={"content-type": "audio/mpeg"}, body=b"x" * 129),
            "TTS_PROVIDER_AUDIO_TOO_LARGE",
        ),
        (
            TTSHTTPResponse(status_code=200, headers={"content-type": "text/plain"}, body=b"not audio"),
            "TTS_PROVIDER_RESPONSE_INVALID",
        ),
    )
    for response, expected_code in cases:
        transport = FakeTransport([response])
        ledger = InMemoryTTSQuotaLedger(character_limit=100)
        provider = ElevenLabsTTSProvider(
            config=config(),
            transport=transport,
            quota_ledger=ledger,
        )

        with pytest.raises(TTSProviderError) as exc:
            provider.synthesize(text="Grounded script.", language="en", request_id="req_001", trace_id="trace_001")

        assert exc.value.code == expected_code
        assert ledger.reservations["req_001"].state == "REFUNDED"


class FakeGoogleIdentityProvider:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, *, scope: str) -> GoogleIdentity:
        self.calls += 1
        return GoogleIdentity(
            access_token="synthetic-test-token-not-a-credential",
            identity_evidence_sha256="sha256:" + "1" * 64,
        )


class FakeGoogleTransport(FakeTransport):
    pass


def google_config(**overrides: object) -> GoogleTTSConfig:
    values: dict[str, object] = {
        "enabled": True,
        "activation_record_sha256": "sha256:" + "2" * 64,
        "activation_expires_at": "2099-01-01T00:00:00+00:00",
        "privacy_approved": True,
        "policy_approved": True,
        "budget_audio_tokens": 100_000,
        "quota_requests": 10,
        "max_concurrent_requests": 1,
        "timeout_seconds": 3.0,
    }
    values.update(overrides)
    return GoogleTTSConfig(**values)


def receipt(presenter_id: str = "meera") -> TTSConsumptionReceipt:
    return TTSConsumptionReceipt(
        tenant_id="tenant_local",
        actor_id="user_local",
        project_id="proj_narration",
        version=1,
        narration_checksum="sha256:" + "3" * 64,
        presenter_id=presenter_id,
        presenter_version="1.0.0",
        presenter_binding_checksum="sha256:" + "4" * 64,
        source_run_id="run_narration",
        source_evaluation_checksum="sha256:" + "5" * 64,
        evaluation_checksum="sha256:" + "6" * 64,
        approval_checksum="sha256:" + "7" * 64,
        request_id="consume_google_1",
        trace_id="trace_google_1",
        spoken_text="Approved grounded narration for NarraTwin AI.",
        duration_requirement_seconds=(90, 120),
        receipt_checksum="sha256:" + "8" * 64,
    )


def speech_wav(*, seconds: int = 90, sample_rate: int = 24_000) -> bytes:
    frame_count = seconds * sample_rate
    pattern = b"".join(struct.pack("<h", value) for value in (
        -9000, -7000, -3000, 1000, 6000, 10000, 5000, -1000,
        -4000, -8000, -2000, 3000, 8000, 4000, 500, -5000,
    ))
    pcm = (pattern * ((frame_count * 2 + len(pattern) - 1) // len(pattern)))[: frame_count * 2]
    return (
        b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
        + b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )


def google_response(audio: bytes | None = None) -> TTSHTTPResponse:
    body = json.dumps({"audioContent": base64.b64encode(audio or speech_wav()).decode("ascii")}).encode()
    return TTSHTTPResponse(200, {"content-type": "application/json; charset=utf-8"}, body)


def google_provider(
    transport: FakeGoogleTransport,
    identity: FakeGoogleIdentityProvider,
    *,
    config_value: GoogleTTSConfig | None = None,
) -> GoogleGeminiTTSProvider:
    return GoogleGeminiTTSProvider(
        config=config_value or google_config(),
        identity_provider=identity,
        transport=transport,
        receipt_validator=lambda value: value == receipt(value.presenter_id),
        prompt_contract_path=Path("docs/governance/cut1-google-gemini-tts-style-prompts-v1.json"),
    )


@pytest.mark.parametrize("presenter_id,voice", [("meera", "Despina"), ("myra", "Leda"), ("raj", "Achird")])
def test_g368_01_03_exact_semantic_mapping_and_unary_request(presenter_id: str, voice: str) -> None:
    transport = FakeGoogleTransport([google_response()])
    identity = FakeGoogleIdentityProvider()
    result = google_provider(transport, identity).synthesize(receipt=receipt(presenter_id))

    assert result.presenter_id == presenter_id
    assert result.requested_voice == voice
    assert result.effective_voice_verified is False
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["url"] == "https://eu-texttospeech.googleapis.com/v1/text:synthesize"
    assert list(call["json_body"]) == ["input", "voice", "audioConfig"]
    assert call["json_body"]["voice"] == {
        "languageCode": "en-IN", "modelName": "gemini-2.5-pro-tts", "name": voice,
    }
    assert call["json_body"]["audioConfig"] == {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000}
    assert set(call["headers"]) == {"Authorization", "Content-Type"}


@pytest.mark.parametrize("config_value,code", [
    (google_config(enabled=False), "GOOGLE_TTS_DISABLED"),
    (google_config(privacy_approved=False), "GOOGLE_TTS_PRIVACY_BLOCKED"),
    (google_config(policy_approved=False), "GOOGLE_TTS_POLICY_BLOCKED"),
    (google_config(budget_audio_tokens=0), "GOOGLE_TTS_BUDGET_BLOCKED"),
    (google_config(quota_requests=0), "GOOGLE_TTS_QUOTA_BLOCKED"),
])
def test_g368_03_05_all_activation_failures_precede_identity_and_transport(
    config_value: GoogleTTSConfig, code: str
) -> None:
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity, config_value=config_value).synthesize(receipt=receipt())
    assert caught.value.code == code
    assert identity.calls == 0 and transport.calls == []


def test_g368_08_09_completed_replay_does_not_egress_and_ambiguous_timeout_is_held() -> None:
    transport = FakeGoogleTransport([google_response()])
    identity = FakeGoogleIdentityProvider()
    provider = google_provider(transport, identity)
    first = provider.synthesize(receipt=receipt())
    replay = provider.synthesize(receipt=receipt())
    assert replay == first and len(transport.calls) == 1

    timeout_transport = FakeGoogleTransport([GoogleTransportError(egress_possible=True)])
    timeout_provider = google_provider(timeout_transport, FakeGoogleIdentityProvider())
    with pytest.raises(TTSProviderError) as caught:
        timeout_provider.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_BILLABLE_UNKNOWN"
    assert timeout_provider.request_state(receipt()) == "BILLABLE_UNKNOWN"
    with pytest.raises(TTSProviderError):
        timeout_provider.synthesize(receipt=receipt())
    assert len(timeout_transport.calls) == 1


@pytest.mark.parametrize("body,code", [
    (b"{}", "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID"),
    (b'{"audioContent":"%%%"}', "GOOGLE_TTS_RESPONSE_BASE64_INVALID"),
    (b'{"audioContent":"","extra":1}', "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID"),
])
def test_g368_06_response_schema_and_base64_fail_closed(body: bytes, code: str) -> None:
    transport = FakeGoogleTransport([TTSHTTPResponse(200, {"content-type": "application/json"}, body)])
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, FakeGoogleIdentityProvider()).synthesize(receipt=receipt())
    assert caught.value.code == code


@pytest.mark.parametrize("audio,code", [
    (b"", "GOOGLE_TTS_AUDIO_INVALID"),
    (b"not-wave", "GOOGLE_TTS_AUDIO_INVALID"),
    (speech_wav(seconds=89), "GOOGLE_TTS_AUDIO_DURATION_INVALID"),
    (speech_wav(seconds=90)[:1000], "GOOGLE_TTS_AUDIO_INVALID"),
])
def test_g368_06_malformed_truncated_and_duration_audio_fail_closed(audio: bytes, code: str) -> None:
    transport = FakeGoogleTransport([google_response(audio)])
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, FakeGoogleIdentityProvider()).synthesize(receipt=receipt())
    assert caught.value.code == code
