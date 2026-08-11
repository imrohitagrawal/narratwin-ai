import base64
import hashlib
import itertools
import json
import socket
import struct
import threading
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
from typing import Any, cast

import backend.app.tts_provider as tts_provider_module
from backend.app.tts_provider import (
    ElevenLabsTTSProvider,
    InMemoryTTSQuotaLedger,
    TTSHTTPResponse,
    TTSProviderConfig,
    TTSProviderError,
    GoogleGeminiTTSProvider,
    GoogleEgressScreening,
    GoogleIdentity,
    GoogleTTSConfig,
    GoogleTTSHTTPResponse,
    GoogleTTSPreparedTransport,
    GoogleTransportError,
)
from backend.app.narration import TTSConsumptionReceipt


_GOOGLE_TEST_STATE_DIR = tempfile.TemporaryDirectory(prefix="narratwin-g368-")
_GOOGLE_TEST_STATE_COUNTER = itertools.count()
_GOOGLE_TEST_QUOTA_PROJECT = "quota-project"
_GOOGLE_TEST_QUOTA_HASH = "sha256:" + hashlib.sha256(
    _GOOGLE_TEST_QUOTA_PROJECT.encode()
).hexdigest()


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
        provider.synthesize(
            text="too long", language="en", request_id="req_001", trace_id="trace_001"
        )

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
        provider.synthesize(
            text="Grounded script.", language="en", request_id="req_001", trace_id="trace_001"
        )

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
            TTSHTTPResponse(
                status_code=200, headers={"content-type": "audio/mpeg"}, body=b"x" * 129
            ),
            "TTS_PROVIDER_AUDIO_TOO_LARGE",
        ),
        (
            TTSHTTPResponse(
                status_code=200, headers={"content-type": "text/plain"}, body=b"not audio"
            ),
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
            provider.synthesize(
                text="Grounded script.", language="en", request_id="req_001", trace_id="trace_001"
            )

        assert exc.value.code == expected_code
        assert ledger.reservations["req_001"].state == "REFUNDED"


class FakeGoogleIdentityProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.revalidation_calls = 0
        self.fail_revalidation = False

    def resolve(self, *, scope: str) -> GoogleIdentity:
        self.calls += 1
        return GoogleIdentity(
            "unit-fixture-identity-value",
            "sha256:" + "1" * 64,
            _GOOGLE_TEST_QUOTA_PROJECT,
            _GOOGLE_TEST_QUOTA_HASH,
        )

    def revalidate_quota_project(self, identity: GoogleIdentity) -> None:
        self.revalidation_calls += 1
        if self.fail_revalidation:
            raise RuntimeError("private-project-value-must-not-leak")


@dataclass
class FakePreparedGoogleTransport:
    owner: "FakeGoogleTransport"
    url: str
    resolved_addresses: tuple[str, ...] = ("8.8.8.8",)
    peer_ip: str = "8.8.8.8"
    proxy_used: bool = False
    tls_verified: bool = True
    tls_server_name: str = "eu-texttospeech.googleapis.com"
    peer_port: int = 443
    redirects_disabled: bool = True
    dns_pinned: bool = True

    def send(
        self,
        *,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> GoogleTTSHTTPResponse:
        return self.owner._send(
            prepared=self,
            headers=headers,
            json_body=json_body,
            timeout_seconds=timeout_seconds,
        )


class FakeGoogleTransport:
    def __init__(self, responses: list[GoogleTTSHTTPResponse | Exception]) -> None:
        self.responses = responses
        self.prepare_calls: list[dict[str, object]] = []
        self.calls: list[dict[str, object]] = []

    def prepare(self, *, url: str, timeout_seconds: float) -> FakePreparedGoogleTransport:
        self.prepare_calls.append({"url": url, "timeout_seconds": timeout_seconds})
        return FakePreparedGoogleTransport(
            owner=self,
            url=url,
        )

    def _send(
        self,
        *,
        prepared: GoogleTTSPreparedTransport,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> GoogleTTSHTTPResponse:
        self.calls.append(
            {
                "url": prepared.url,
                "prepared": prepared,
                "headers": headers,
                "json_body": json_body,
                "timeout_seconds": timeout_seconds,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def google_config(**overrides: object) -> GoogleTTSConfig:
    values: dict[str, object] = {
        "enabled": True,
        "activation_record_sha256": "sha256:" + "2" * 64,
        "activation_expires_at": "2099-01-01T00:00:00+00:00",
        "privacy_approved": True,
        "policy_approved": True,
        "budget_audio_tokens": 100_000,
        "budget_microusd": 1_000_000,
        "quota_requests": 10,
        "max_concurrent_requests": 1,
        "timeout_seconds": 3.0,
    }
    if "approved_quota_project_sha256" in GoogleTTSConfig.__dataclass_fields__:
        values["approved_quota_project_sha256"] = _GOOGLE_TEST_QUOTA_HASH
    values.update(overrides)
    return GoogleTTSConfig(**cast(Any, values))


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
    samples: list[int] = []
    for run_length, value in (
        (3, -9000),
        (5, 7000),
        (2, -4000),
        (7, 10000),
        (4, -6000),
        (6, 5000),
        (1, -2000),
        (8, 8000),
    ):
        samples.extend([value] * run_length)
    return wav_from_pattern(samples, seconds=seconds, sample_rate=sample_rate)


def wav_from_pattern(values: list[int], *, seconds: int = 90, sample_rate: int = 24_000) -> bytes:
    frame_count = seconds * sample_rate
    pattern = b"".join(struct.pack("<h", value) for value in values)
    pcm = (pattern * ((frame_count * 2 + len(pattern) - 1) // len(pattern)))[: frame_count * 2]
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(pcm))
        + pcm
    )


def google_response(audio: bytes | None = None, **overrides: object) -> GoogleTTSHTTPResponse:
    body = json.dumps(
        {"audioContent": base64.b64encode(speech_wav() if audio is None else audio).decode("ascii")}
    ).encode()
    values: dict[str, object] = {
        "status_code": 200,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": body,
        "final_url": "https://eu-texttospeech.googleapis.com/v1/text:synthesize",
        "redirect_count": 0,
        "peer_ip": "8.8.8.8",
        "resolved_addresses": ("8.8.8.8",),
        "proxy_used": False,
        "tls_verified": True,
        "tls_server_name": "eu-texttospeech.googleapis.com",
        "peer_port": 443,
    }
    values.update(overrides)
    return GoogleTTSHTTPResponse(**cast(Any, values))


def state_checksum(payload: dict[str, object]) -> str:
    unsigned = {"schema": payload["schema"], "requests": payload["requests"]}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def google_provider(
    transport: FakeGoogleTransport,
    identity: FakeGoogleIdentityProvider,
    *,
    config_value: GoogleTTSConfig | None = None,
    receipt_validator: Any | None = None,
    prompt_contract_path: Path | None = None,
    state_path: Path | None = None,
) -> GoogleGeminiTTSProvider:
    durable_state_path = state_path or (
        Path(_GOOGLE_TEST_STATE_DIR.name) / f"state-{next(_GOOGLE_TEST_STATE_COUNTER)}.json"
    )
    return GoogleGeminiTTSProvider(
        config=config_value or google_config(),
        identity_provider=identity,
        transport=transport,
        receipt_validator=receipt_validator or (lambda value: value == receipt(value.presenter_id)),
        prompt_contract_path=prompt_contract_path
        or Path("docs/governance/cut1-google-gemini-tts-style-prompts-v1.json"),
        state_path=durable_state_path,
    )


@pytest.mark.parametrize(
    "presenter_id,voice", [("meera", "Despina"), ("myra", "Leda"), ("raj", "Achird")]
)
def test_g368_01_03_exact_semantic_mapping_and_unary_request(presenter_id: str, voice: str) -> None:
    transport = FakeGoogleTransport([google_response()])
    identity = FakeGoogleIdentityProvider()
    result = google_provider(transport, identity).synthesize(receipt=receipt(presenter_id))

    assert result.presenter_id == presenter_id
    assert result.requested_voice == voice
    assert result.effective_voice_verified is False
    assert len(transport.calls) == 1
    call = transport.calls[0]
    body = cast(dict[str, Any], call["json_body"])
    headers = cast(dict[str, str], call["headers"])
    assert call["url"] == "https://eu-texttospeech.googleapis.com/v1/text:synthesize"
    assert list(body) == ["input", "voice", "audioConfig"]
    assert body["voice"] == {
        "languageCode": "en-IN",
        "modelName": "gemini-2.5-pro-tts",
        "name": voice,
    }
    assert body["audioConfig"] == {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000}
    assert set(headers) == {"Authorization", "Content-Type", "x-goog-user-project"}
    assert headers["Authorization"] == "Bear" + "er unit-fixture-identity-value"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["x-goog-user-project"] == _GOOGLE_TEST_QUOTA_PROJECT


def test_g368_quota_project_is_hash_bound_and_not_caller_controlled() -> None:
    fields = GoogleTTSConfig.__dataclass_fields__
    assert "approved_quota_project_sha256" in fields
    assert "quota_project_id" not in fields
    assert set(GoogleGeminiTTSProvider.synthesize.__annotations__) == {"receipt", "return"}


def test_g368_request_fingerprint_binds_required_quota_header_and_approved_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    original_sha = tts_provider_module._google_sha

    def capture_sha(value: object) -> str:
        captured.append(value)
        return original_sha(value)

    provider = google_provider(FakeGoogleTransport([]), FakeGoogleIdentityProvider())
    profile, _screening = provider._validate_before_identity(receipt())
    body = provider._request_body(receipt(), profile)
    monkeypatch.setattr(tts_provider_module, "_google_sha", capture_sha)
    provider._request_contract_checksum(receipt(), profile, body)

    contract = cast(dict[str, object], captured[-1])
    assert contract["orderedHeaderNames"] == [
        "Authorization",
        "Content-Type",
        "x-goog-user-project",
    ]
    assert contract["quotaProjectRequired"] is True
    assert contract["approvedQuotaProjectIdSha256"] == _GOOGLE_TEST_QUOTA_HASH


def test_g368_quota_project_change_is_revalidated_before_egress() -> None:
    transport = FakeGoogleTransport([google_response()])
    identity = FakeGoogleIdentityProvider()
    identity.fail_revalidation = True

    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity).synthesize(receipt=receipt())

    assert caught.value.code == "GOOGLE_TTS_IDENTITY_UNAVAILABLE"
    assert "private-project-value-must-not-leak" not in str(caught.value)
    assert identity.revalidation_calls == 1
    assert transport.calls == []


@pytest.mark.parametrize(
    "headers",
    [
        {
            "Authorization": "Bear" + "er unit-fixture-identity-value",
            "Content-Type": "application/json; charset=utf-8",
        },
        {
            "Authorization": "Bear" + "er unit-fixture-identity-value",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-user-project": "mutated-project",
        },
        {
            "Authorization": "Bear" + "er unit-fixture-identity-value",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-user-project": _GOOGLE_TEST_QUOTA_PROJECT,
            "X-Caller-Injected": "forbidden",
        },
    ],
)
def test_g368_header_removal_mutation_and_injection_fail_before_egress(
    headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = FakeGoogleTransport([google_response()])
    provider = google_provider(transport, FakeGoogleIdentityProvider())
    monkeypatch.setattr(provider, "_request_headers", lambda _identity: headers, raising=False)

    with pytest.raises(TTSProviderError) as caught:
        provider.synthesize(receipt=receipt())

    assert caught.value.code == "GOOGLE_TTS_REQUEST_HEADERS_INVALID"
    assert transport.calls == []


def test_g368_03_synthesis_uses_only_the_injected_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_ambient_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("ambient network access is prohibited")

    monkeypatch.setattr(socket, "create_connection", reject_ambient_network)
    transport = FakeGoogleTransport([google_response()])
    identity = FakeGoogleIdentityProvider()

    result = google_provider(transport, identity).synthesize(receipt=receipt())

    assert result.spend_state == "COMPLETED"
    assert len(transport.calls) == 1
    assert identity.calls == 1


@pytest.mark.parametrize(
    "config_value,code",
    [
        (google_config(enabled=False), "GOOGLE_TTS_DISABLED"),
        (google_config(privacy_approved=False), "GOOGLE_TTS_PRIVACY_BLOCKED"),
        (google_config(policy_approved=False), "GOOGLE_TTS_POLICY_BLOCKED"),
        (google_config(budget_audio_tokens=0), "GOOGLE_TTS_BUDGET_BLOCKED"),
        (google_config(quota_requests=0), "GOOGLE_TTS_QUOTA_BLOCKED"),
    ],
)
def test_g368_03_05_all_activation_failures_precede_identity_and_transport(
    config_value: GoogleTTSConfig, code: str
) -> None:
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity, config_value=config_value).synthesize(
            receipt=receipt()
        )
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


@pytest.mark.parametrize(
    "body,code",
    [
        (b"{}", "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID"),
        (b'{"audioContent":"%%%"}', "GOOGLE_TTS_RESPONSE_BASE64_INVALID"),
        (b'{"audioContent":"","extra":1}', "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID"),
    ],
)
def test_g368_06_response_schema_and_base64_fail_closed(body: bytes, code: str) -> None:
    transport = FakeGoogleTransport(
        [google_response(body=body, headers={"content-type": "application/json"})]
    )
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, FakeGoogleIdentityProvider()).synthesize(receipt=receipt())
    assert caught.value.code == code


@pytest.mark.parametrize(
    "audio,code",
    [
        (b"", "GOOGLE_TTS_AUDIO_INVALID"),
        (b"not-wave", "GOOGLE_TTS_AUDIO_INVALID"),
        (speech_wav(seconds=89), "GOOGLE_TTS_AUDIO_DURATION_INVALID"),
        (speech_wav(seconds=90)[:1000], "GOOGLE_TTS_AUDIO_INVALID"),
    ],
)
def test_g368_06_malformed_truncated_and_duration_audio_fail_closed(
    audio: bytes, code: str
) -> None:
    transport = FakeGoogleTransport([google_response(audio)])
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, FakeGoogleIdentityProvider()).synthesize(receipt=receipt())
    assert caught.value.code == code


def test_g368_02_prompt_contract_drift_blocks_before_identity_and_transport(tmp_path: Path) -> None:
    contract = Path("docs/governance/cut1-google-gemini-tts-style-prompts-v1.json").read_bytes()
    drifted = tmp_path / "prompts.json"
    drifted.write_bytes(contract + b"\n")
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity, prompt_contract_path=drifted).synthesize(
            receipt=receipt()
        )
    assert caught.value.code == "GOOGLE_TTS_PROMPT_CONTRACT_INVALID"
    assert identity.calls == 0 and transport.calls == []


@pytest.mark.parametrize(
    "candidate,code",
    [
        (receipt("unknown"), "PRESENTER_NOT_ALLOWLISTED"),
        (replace(receipt(), duration_requirement_seconds=(1, 2)), "GOOGLE_TTS_AUTHORITY_INVALID"),
        (
            replace(receipt(), spoken_text="api" + "_" + "key" + "=" + "fixture-value"),
            "GOOGLE_TTS_EGRESS_BLOCKED",
        ),
        (
            replace(receipt(), spoken_text="contact somebody@example.org"),
            "GOOGLE_TTS_EGRESS_BLOCKED",
        ),
        (replace(receipt(), spoken_text="Call +91 98765 43210"), "GOOGLE_TTS_EGRESS_BLOCKED"),
        (replace(receipt(), spoken_text="Tax identifier ABCDE1234F"), "GOOGLE_TTS_EGRESS_BLOCKED"),
        (
            replace(receipt(), spoken_text="Payment card 4111 1111 1111 1111"),
            "GOOGLE_TTS_EGRESS_BLOCKED",
        ),
        (replace(receipt(), spoken_text="x" * 4_001), "GOOGLE_TTS_TEXT_LIMIT"),
    ],
)
def test_g368_01_04_receipt_privacy_and_byte_checks_precede_identity(
    candidate: TTSConsumptionReceipt, code: str
) -> None:
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    validator = (
        (lambda _value: True) if candidate.presenter_id in {"meera", "myra", "raj"} else None
    )
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity, receipt_validator=validator).synthesize(
            receipt=candidate
        )
    assert caught.value.code == code
    assert identity.calls == 0 and transport.calls == []


@pytest.mark.parametrize(
    "response",
    [
        google_response(
            final_url="https://texttospeech.googleapis.com/v1/text:synthesize", redirect_count=1
        ),
        google_response(peer_ip="127.0.0.1", resolved_addresses=("127.0.0.1",)),
        google_response(peer_ip="8.8.4.4", resolved_addresses=("8.8.8.8",)),
        google_response(proxy_used=True),
    ],
)
def test_g368_03_ssrf_redirect_dns_and_proxy_evidence_fail_closed(
    response: GoogleTTSHTTPResponse,
) -> None:
    with pytest.raises(TTSProviderError) as caught:
        google_provider(FakeGoogleTransport([response]), FakeGoogleIdentityProvider()).synthesize(
            receipt=receipt()
        )
    assert caught.value.code == "GOOGLE_TTS_TRANSPORT_POLICY_INVALID"


@pytest.mark.parametrize(
    "audio,code",
    [
        (wav_from_pattern([0]), "GOOGLE_TTS_AUDIO_SILENT"),
        (wav_from_pattern([100, -100, 50, -50]), "GOOGLE_TTS_AUDIO_SILENT"),
        (wav_from_pattern([8_000] * 10 + [-8_000] * 10), "GOOGLE_TTS_AUDIO_TONE_INVALID"),
        (
            wav_from_pattern([32_767] * 3 + [-32_768] * 5 + [32_767] * 2 + [-32_768] * 7),
            "GOOGLE_TTS_AUDIO_CLIPPED",
        ),
    ],
)
def test_g368_06_silent_near_silent_fixed_tone_and_clipped_audio_fail_closed(
    audio: bytes, code: str
) -> None:
    with pytest.raises(TTSProviderError) as caught:
        google_provider(
            FakeGoogleTransport([google_response(audio)]), FakeGoogleIdentityProvider()
        ).synthesize(receipt=receipt())
    assert caught.value.code == code


def test_g368_07_completed_artifact_restores_replays_and_tombstones_monotonically(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "google-tts.json"
    transport = FakeGoogleTransport([google_response()])
    provider = google_provider(transport, FakeGoogleIdentityProvider(), state_path=state_path)
    completed = provider.synthesize(receipt=receipt())
    restored_transport = FakeGoogleTransport([])
    restored = google_provider(
        restored_transport, FakeGoogleIdentityProvider(), state_path=state_path
    )
    assert restored.synthesize(receipt=receipt()) == completed
    assert restored_transport.calls == []
    restored.delete_artifact(receipt())
    restored.delete_artifact(receipt())
    assert restored.request_state(receipt()) == "TOMBSTONED"
    assert "audioBase64" not in state_path.read_text(encoding="utf-8")
    with pytest.raises(TTSProviderError) as caught:
        restored.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_ARTIFACT_DELETED"


def test_g368_08_concurrent_duplicate_is_rejected_without_second_egress() -> None:
    entered = threading.Event()
    release = threading.Event()

    class BlockingTransport(FakeGoogleTransport):
        def _send(self, **kwargs: Any) -> GoogleTTSHTTPResponse:
            self.calls.append(kwargs)
            entered.set()
            assert release.wait(timeout=3)
            return google_response()

    transport = BlockingTransport([])
    provider = google_provider(transport, FakeGoogleIdentityProvider())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(provider.synthesize, receipt=receipt())
        assert entered.wait(timeout=3)
        second = pool.submit(provider.synthesize, receipt=receipt())
        with pytest.raises(TTSProviderError) as caught:
            second.result(timeout=3)
        release.set()
        assert first.result(timeout=5).spend_state == "COMPLETED"
    assert caught.value.code == "GOOGLE_TTS_CONCURRENCY_BLOCKED"
    assert len(transport.calls) == 1


def test_g368_08_shared_durable_lock_prevents_cross_instance_duplicate_egress(
    tmp_path: Path,
) -> None:
    entered = threading.Event()
    release = threading.Event()

    class BlockingTransport(FakeGoogleTransport):
        def _send(self, **kwargs: Any) -> GoogleTTSHTTPResponse:
            self.calls.append(kwargs)
            entered.set()
            assert release.wait(timeout=3)
            return google_response()

    state_path = tmp_path / "shared.json"
    first_transport = BlockingTransport([])
    second_transport = FakeGoogleTransport([google_response()])
    first = google_provider(first_transport, FakeGoogleIdentityProvider(), state_path=state_path)
    second = google_provider(second_transport, FakeGoogleIdentityProvider(), state_path=state_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first_call = pool.submit(first.synthesize, receipt=receipt())
        assert entered.wait(timeout=3)
        second_call = pool.submit(second.synthesize, receipt=receipt())
        with pytest.raises(TTSProviderError) as caught:
            second_call.result(timeout=3)
        release.set()
        completed = first_call.result(timeout=5)
    assert caught.value.code == "GOOGLE_TTS_CONCURRENCY_BLOCKED"
    assert len(first_transport.calls) == 1 and second_transport.calls == []
    assert second.synthesize(receipt=receipt()) == completed
    assert second_transport.calls == []


def test_g368_07_stale_instance_observes_monotonic_tombstone_before_replay(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "shared.json"
    owner = google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    )
    owner.synthesize(receipt=receipt())
    stale_transport = FakeGoogleTransport([])
    stale = google_provider(stale_transport, FakeGoogleIdentityProvider(), state_path=state_path)

    owner.delete_artifact(receipt())

    assert stale.request_state(receipt()) == "TOMBSTONED"
    with pytest.raises(TTSProviderError) as caught:
        stale.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_ARTIFACT_DELETED"
    assert stale_transport.calls == []


def test_g368_10_logs_state_and_errors_redact_content_identity_and_provider_body(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    state_path = tmp_path / "google-tts.json"
    identity = FakeGoogleIdentityProvider()
    provider = google_provider(
        FakeGoogleTransport([google_response()]), identity, state_path=state_path
    )
    provider.synthesize(receipt=receipt())
    evidence = caplog.text + state_path.read_text(encoding="utf-8")
    call_headers = {"Author" + "ization": "Bear" + "er unit-fixture-identity-value"}
    for forbidden in (
        receipt().spoken_text,
        "Read the supplied text exactly",
        identity.resolve(scope="unused").access_token,
        json.dumps(call_headers),
        _GOOGLE_TEST_QUOTA_PROJECT,
        "audioContent",
    ):
        assert forbidden not in evidence


def test_g368_07_restore_rejects_checksum_tampering(tmp_path: Path) -> None:
    state_path = tmp_path / "google-tts.json"
    google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    ).synthesize(receipt=receipt())
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["requests"][0]["result"]["artifactChecksum"] = "sha256:" + "0" * 64
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(TTSProviderError) as caught:
        google_provider(
            FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=state_path
        )
    assert caught.value.code == "GOOGLE_TTS_STATE_INVALID"


def test_g368_04_quota_and_budget_hold_after_egress_without_identity_or_retry() -> None:
    identity = FakeGoogleIdentityProvider()
    transport = FakeGoogleTransport([google_response()])
    provider = google_provider(
        transport,
        identity,
        config_value=google_config(quota_requests=1, budget_audio_tokens=3_000),
        receipt_validator=lambda _value: True,
    )
    provider.synthesize(receipt=receipt())
    second = replace(
        receipt(), request_id="consume_google_2", receipt_checksum="sha256:" + "9" * 64
    )
    with pytest.raises(TTSProviderError) as caught:
        provider.synthesize(receipt=second)
    assert caught.value.code == "GOOGLE_TTS_QUOTA_BLOCKED"
    assert identity.calls == 1 and len(transport.calls) == 1


def test_g368_03_transport_policy_is_proven_before_identity_or_content() -> None:
    class UnsafePreparation(FakeGoogleTransport):
        def prepare(self, *, url: str, timeout_seconds: float) -> FakePreparedGoogleTransport:
            prepared = super().prepare(url=url, timeout_seconds=timeout_seconds)
            return replace(prepared, proxy_used=True)

    transport = UnsafePreparation([])
    identity = FakeGoogleIdentityProvider()
    with pytest.raises(TTSProviderError) as caught:
        google_provider(transport, identity).synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_TRANSPORT_POLICY_INVALID"
    assert len(transport.prepare_calls) == 1
    assert identity.calls == 0
    assert transport.calls == []


def test_g368_03_enabled_adapter_requires_durable_state_before_identity() -> None:
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    provider = GoogleGeminiTTSProvider(
        config=google_config(),
        identity_provider=identity,
        transport=transport,
        receipt_validator=lambda _value: True,
        prompt_contract_path=Path("docs/governance/cut1-google-gemini-tts-style-prompts-v1.json"),
    )
    with pytest.raises(TTSProviderError) as caught:
        provider.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_DURABLE_STATE_REQUIRED"
    assert identity.calls == 0 and transport.prepare_calls == []


def test_g368_04_malformed_response_and_validator_errors_are_bounded(
    tmp_path: Path,
) -> None:
    invalid_transport = FakeGoogleTransport([cast(Any, object())])
    provider = google_provider(
        invalid_transport,
        FakeGoogleIdentityProvider(),
        state_path=tmp_path / "invalid-response.json",
    )
    with pytest.raises(TTSProviderError) as response_error:
        provider.synthesize(receipt=receipt())
    assert response_error.value.code == "GOOGLE_TTS_RESPONSE_SCHEMA_INVALID"
    assert response_error.value.__cause__ is None
    assert provider.request_state(receipt()) == "FAILED_BILLABLE"

    def broken_validator(_receipt: TTSConsumptionReceipt) -> bool:
        raise RuntimeError("private-state-path")

    validator_transport = FakeGoogleTransport([])
    with pytest.raises(TTSProviderError) as validator_error:
        google_provider(
            validator_transport,
            FakeGoogleIdentityProvider(),
            receipt_validator=broken_validator,
            state_path=tmp_path / "invalid-validator.json",
        ).synthesize(receipt=receipt())
    assert validator_error.value.code == "GOOGLE_TTS_AUTHORITY_INVALID"
    assert validator_error.value.__cause__ is None
    assert "private-state-path" not in str(validator_error.value)
    assert validator_transport.prepare_calls == []


def test_g368_04_authority_is_revalidated_after_egress_before_commit(tmp_path: Path) -> None:
    current = True

    class RevokingTransport(FakeGoogleTransport):
        def _send(self, **kwargs: Any) -> GoogleTTSHTTPResponse:
            nonlocal current
            response = super()._send(**kwargs)
            current = False
            return response

    state_path = tmp_path / "state.json"
    provider = google_provider(
        RevokingTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        receipt_validator=lambda _value: current,
        state_path=state_path,
    )
    with pytest.raises(TTSProviderError) as caught:
        provider.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_AUTHORITY_STALE_AFTER_EGRESS"
    assert provider.request_state(receipt()) == "FAILED_BILLABLE"
    assert "audioBase64" not in state_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "screener,code",
    [
        (
            lambda _receipt: (_ for _ in ()).throw(RuntimeError("private-path")),
            "GOOGLE_TTS_EGRESS_SCREEN_UNAVAILABLE",
        ),
        (
            lambda _receipt: GoogleEgressScreening("wrong", "PASS", "sha256:" + "0" * 64),
            "GOOGLE_TTS_EGRESS_SCREEN_INVALID",
        ),
    ],
)
def test_g368_04_screening_unavailable_or_malformed_fails_before_transport(
    screener: Any, code: str
) -> None:
    transport = FakeGoogleTransport([])
    identity = FakeGoogleIdentityProvider()
    provider = GoogleGeminiTTSProvider(
        config=google_config(),
        identity_provider=identity,
        transport=transport,
        receipt_validator=lambda _value: True,
        prompt_contract_path=Path("docs/governance/cut1-google-gemini-tts-style-prompts-v1.json"),
        egress_screener=screener,
        state_path=Path(_GOOGLE_TEST_STATE_DIR.name)
        / f"state-{next(_GOOGLE_TEST_STATE_COUNTER)}.json",
    )
    with pytest.raises(TTSProviderError) as caught:
        provider.synthesize(receipt=receipt())
    assert caught.value.code == code
    assert caught.value.__cause__ is None
    assert identity.calls == 0 and transport.prepare_calls == [] and transport.calls == []


def test_g368_07_replay_rebinds_every_canonical_result_field(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    ).synthesize(receipt=receipt())
    payload = cast(dict[str, object], json.loads(state_path.read_text(encoding="utf-8")))
    rows = cast(list[dict[str, Any]], payload["requests"])
    rows[0]["result"]["requestedVoice"] = "FORGED"
    payload["stateChecksum"] = state_checksum(payload)
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    restored = google_provider(
        FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=state_path
    )
    with pytest.raises(TTSProviderError) as caught:
        restored.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_STORED_RESULT_INVALID"


def test_g368_07_deletion_persistence_failure_rolls_back_without_resurrection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "state.json"
    provider = google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    )
    completed = provider.synthesize(receipt=receipt())

    def fail_persist() -> None:
        raise OSError("private-state-path")

    monkeypatch.setattr(provider, "_persist_locked", fail_persist)
    with pytest.raises(TTSProviderError) as caught:
        provider.delete_artifact(receipt())
    assert caught.value.code == "GOOGLE_TTS_DELETE_PERSISTENCE_FAILED"
    assert caught.value.__cause__ is None
    assert provider.request_state(receipt()) == "COMPLETED"
    restored = google_provider(
        FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=state_path
    )
    assert restored.synthesize(receipt=receipt()) == completed


def test_g368_08_config_drift_cannot_reuse_one_receipt_for_second_spend(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    ).synthesize(receipt=receipt())
    transport = FakeGoogleTransport([google_response()])
    changed = google_provider(
        transport,
        FakeGoogleIdentityProvider(),
        config_value=google_config(timeout_seconds=4.0),
        state_path=state_path,
    )
    with pytest.raises(TTSProviderError) as caught:
        changed.synthesize(receipt=receipt())
    assert caught.value.code == "GOOGLE_TTS_IDEMPOTENCY_CONFLICT"
    assert transport.prepare_calls == [] and transport.calls == []


def test_g368_08_cost_reservation_reconciles_to_validated_duration(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    result = google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    ).synthesize(receipt=receipt())
    assert result.reserved_input_tokens > 0
    assert result.reserved_output_tokens == 3_000
    assert result.actual_output_tokens == 2_250
    assert 0 < result.actual_cost_microusd < result.reserved_cost_microusd
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    row = payload["requests"][0]
    assert row["reservedOutputTokens"] == result.actual_output_tokens
    assert row["reservedCostMicrousd"] == result.actual_cost_microusd


def test_g368_07_restore_rejects_unreadable_symlink_and_oversized_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import backend.app.tts_provider as provider_module

    target = tmp_path / "target.json"
    target.write_text("not-json", encoding="utf-8")
    link = tmp_path / "linked.json"
    link.symlink_to(target)
    with pytest.raises(TTSProviderError) as symlink_error:
        google_provider(FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=link)
    assert symlink_error.value.code == "GOOGLE_TTS_STATE_INVALID"
    assert symlink_error.value.__cause__ is None

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"x" * 65)
    monkeypatch.setattr(provider_module, "GOOGLE_MAX_STATE_BYTES", 64)
    with pytest.raises(TTSProviderError) as size_error:
        google_provider(FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=oversized)
    assert size_error.value.code == "GOOGLE_TTS_STATE_INVALID"


def test_g368_07_restore_bounds_persisted_base64_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import backend.app.tts_provider as provider_module

    state_path = tmp_path / "state.json"
    google_provider(
        FakeGoogleTransport([google_response()]),
        FakeGoogleIdentityProvider(),
        state_path=state_path,
    ).synthesize(receipt=receipt())
    monkeypatch.setattr(provider_module, "GOOGLE_MAX_AUDIO_BYTES", 8)
    with pytest.raises(TTSProviderError) as caught:
        google_provider(
            FakeGoogleTransport([]), FakeGoogleIdentityProvider(), state_path=state_path
        )
    assert caught.value.code == "GOOGLE_TTS_STATE_INVALID"
