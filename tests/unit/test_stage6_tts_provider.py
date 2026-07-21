import pytest
from typing import Any

from backend.app.tts_provider import (
    ElevenLabsTTSProvider,
    InMemoryTTSQuotaLedger,
    TTSHTTPResponse,
    TTSProviderConfig,
    TTSProviderError,
)


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
