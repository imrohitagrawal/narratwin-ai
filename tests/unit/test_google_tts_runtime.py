from __future__ import annotations

import base64
import hashlib
import json
import importlib
import socket
import ssl
import threading
from collections.abc import Callable, Mapping
from typing import Any, cast

import pytest

import backend.app.google_tts_runtime as google_tts_runtime_module
from backend.app.google_tts_runtime import (
    ADCGoogleIdentityProvider,
    GoogleADCConfig,
    GoogleRuntimeError,
    OfficialUnaryGoogleTTSTransport,
    RegionalGoogleTTSTransport,
)
from backend.app.tts_provider import (
    GOOGLE_TTS_ENDPOINT,
    GOOGLE_TTS_SCOPE,
    GOOGLE_TTS_URL,
    GoogleIdentity,
    GoogleTransportError,
)


CHECKSUM = "sha256:" + "a" * 64
ACCESS_VALUE = "sensitive-test-token"
QUOTA_PROJECT = "quota-project"
QUOTA_PROJECT_HASH = "sha256:" + hashlib.sha256(QUOTA_PROJECT.encode()).hexdigest()


class FakeCredentials:
    def __init__(
        self,
        *,
        access_value: str | None = ACCESS_VALUE,
        refresh_error: Exception | None = None,
        quota_project_id: str | None = QUOTA_PROJECT,
    ) -> None:
        setattr(self, "token", access_value)
        self.refresh_error = refresh_error
        self.refresh_calls: list[object] = []
        self.quota_project_id = quota_project_id

    def refresh(self, request: object) -> None:
        self.refresh_calls.append(request)
        if self.refresh_error:
            raise self.refresh_error


def identity_provider(
    *,
    enabled: bool = True,
    loader: Callable[..., tuple[FakeCredentials, str | None]] | None = None,
    credentials: FakeCredentials | None = None,
    **kwargs: object,
) -> ADCGoogleIdentityProvider:
    supplied = credentials or FakeCredentials()
    default_loader = loader or (lambda **_: (supplied, "project-id"))
    config_values: dict[str, object] = {
        "enabled": enabled,
        "activation_evidence_sha256": CHECKSUM if enabled else "",
    }
    if enabled:
        config_values.update(
            quota_project_id=QUOTA_PROJECT,
            quota_project_evidence_sha256=QUOTA_PROJECT_HASH,
        )
    config_values.update(kwargs)
    return ADCGoogleIdentityProvider(
        config=GoogleADCConfig(**cast(Any, config_values)),
        default_loader=cast(Callable[..., tuple[Any, str | None]], default_loader),
        request_factory=lambda: object(),
    )


def test_disabled_identity_never_imports_or_touches_adc(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def loader(**_: object) -> tuple[FakeCredentials, str]:
        calls.append(object())
        return FakeCredentials(), "project-id"

    provider = identity_provider(enabled=False, loader=loader)
    with pytest.raises(GoogleRuntimeError, match="disabled") as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_DISABLED"
    assert calls == []


def test_missing_google_auth_fails_closed_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    original = importlib.import_module

    def missing(name: str) -> Any:
        if name == "google.auth":
            raise ModuleNotFoundError(name)
        return original(name)

    monkeypatch.setattr(importlib, "import_module", missing)
    provider = ADCGoogleIdentityProvider(
        config=GoogleADCConfig(
            enabled=True,
            activation_evidence_sha256=CHECKSUM,
            quota_project_id=QUOTA_PROJECT,
            quota_project_evidence_sha256=QUOTA_PROJECT_HASH,
        ),
        request_factory=lambda: object(),
    )
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE"
    assert ACCESS_VALUE not in str(error.value)


def test_default_refresh_factory_uses_supported_requests_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imports: list[str] = []

    class PublicRequest:
        pass

    class PublicTransportModule:
        Request = PublicRequest

    def load_public_transport(name: str) -> object:
        imports.append(name)
        if name != "google.auth.transport.requests":
            raise ModuleNotFoundError(name)
        return PublicTransportModule

    monkeypatch.setattr(importlib, "import_module", load_public_transport)

    factory = ADCGoogleIdentityProvider._load_request_factory()

    assert factory is PublicRequest
    assert imports == ["google.auth.transport.requests"]


def test_adc_resolution_binds_exact_scope_and_identity_checksum() -> None:
    calls: list[dict[str, object]] = []
    credentials = FakeCredentials()

    def loader(**kwargs: object) -> tuple[FakeCredentials, str]:
        calls.append(kwargs)
        return credentials, "project-id"

    provider = identity_provider(loader=loader)
    identity = provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert isinstance(identity, GoogleIdentity)
    assert identity.access_token == ACCESS_VALUE
    assert identity.identity_evidence_sha256.startswith("sha256:")
    assert len(identity.identity_evidence_sha256) == len(CHECKSUM)
    assert calls == [{"scopes": [GOOGLE_TTS_SCOPE]}]
    assert len(credentials.refresh_calls) == 1
    assert getattr(identity, "quota_project_id", None) == QUOTA_PROJECT
    assert getattr(identity, "quota_project_sha256", None) == QUOTA_PROJECT_HASH
    assert QUOTA_PROJECT not in repr(identity)
    assert ACCESS_VALUE not in repr(identity)


def test_adc_loader_cannot_mask_absent_native_quota_with_configured_override() -> None:
    native_quota: str | None = None
    calls: list[dict[str, object]] = []

    def loader(**kwargs: object) -> tuple[FakeCredentials, str]:
        calls.append(kwargs)
        effective = cast(str | None, kwargs.get("quota_project_id", native_quota))
        return FakeCredentials(quota_project_id=effective), "project-id"

    provider = identity_provider(loader=loader)
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH"
    assert calls == [{"scopes": [GOOGLE_TTS_SCOPE]}]


def test_adc_loader_cannot_mask_native_project_drift_during_revalidation() -> None:
    current = {"quota": QUOTA_PROJECT}

    def loader(**kwargs: object) -> tuple[FakeCredentials, str]:
        effective = cast(str | None, kwargs.get("quota_project_id", current["quota"]))
        return FakeCredentials(quota_project_id=effective), "project-id"

    provider = identity_provider(loader=loader)
    identity = provider.resolve(scope=GOOGLE_TTS_SCOPE)
    current["quota"] = "changed-project"
    with pytest.raises(GoogleRuntimeError) as error:
        provider.revalidate_quota_project(identity)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH"


def test_adc_rejects_wrong_scope_and_unbound_quota_project() -> None:
    provider = identity_provider()
    with pytest.raises(GoogleRuntimeError) as scope_error:
        provider.resolve(scope="https://example.invalid/scope")
    assert scope_error.value.code == "GOOGLE_TTS_SCOPE_INVALID"
    provider = identity_provider(quota_project_evidence_sha256="")
    with pytest.raises(GoogleRuntimeError) as quota_error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert quota_error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_INVALID"


@pytest.mark.parametrize("configured", [None, "", "bad", "UPPER-project"])
def test_enabled_adc_requires_nonempty_well_formed_configured_quota_project(
    configured: str | None,
) -> None:
    provider = identity_provider(quota_project_id=configured)
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_INVALID"


def test_adc_rejects_31_character_project_with_matching_hash_and_credential() -> None:
    configured = "a" + "1" * 29 + "z"
    approved_hash = "sha256:" + hashlib.sha256(configured.encode()).hexdigest()
    provider = identity_provider(
        quota_project_id=configured,
        quota_project_evidence_sha256=approved_hash,
        credentials=FakeCredentials(quota_project_id=configured),
    )
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_INVALID"


@pytest.mark.parametrize("configured", ["a1234z", "a" + "1" * 28 + "z"])
def test_adc_accepts_six_and_thirty_character_project_id_boundaries(
    configured: str,
) -> None:
    approved_hash = "sha256:" + hashlib.sha256(configured.encode()).hexdigest()
    provider = identity_provider(
        quota_project_id=configured,
        quota_project_evidence_sha256=approved_hash,
        credentials=FakeCredentials(quota_project_id=configured),
    )
    assert provider.resolve(scope=GOOGLE_TTS_SCOPE).quota_project_sha256 == approved_hash


def test_adc_config_repr_redacts_raw_project() -> None:
    config = GoogleADCConfig(
        enabled=True,
        activation_evidence_sha256=CHECKSUM,
        quota_project_id=QUOTA_PROJECT,
        quota_project_evidence_sha256=QUOTA_PROJECT_HASH,
    )
    assert QUOTA_PROJECT not in repr(config)


def test_adc_rejects_absent_or_mismatched_credential_quota_project() -> None:
    for credential_project in (None, "different-project"):
        provider = identity_provider(
            credentials=FakeCredentials(quota_project_id=credential_project)
        )
        with pytest.raises(GoogleRuntimeError) as error:
            provider.resolve(scope=GOOGLE_TTS_SCOPE)
        assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH"


def test_adc_rejects_approved_quota_project_hash_mismatch_without_leaking_raw_value() -> None:
    raw_project = "private-quota-project"
    provider = identity_provider(
        quota_project_id=raw_project,
        quota_project_evidence_sha256="sha256:" + "f" * 64,
        credentials=FakeCredentials(quota_project_id=raw_project),
    )
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_INVALID"
    assert raw_project not in str(error.value)


def test_adc_revalidates_credential_quota_project_immediately_before_egress() -> None:
    current = FakeCredentials()

    def loader(**_: object) -> tuple[FakeCredentials, str]:
        return current, "project-id"

    provider = identity_provider(loader=loader)
    identity = provider.resolve(scope=GOOGLE_TTS_SCOPE)
    current.quota_project_id = "changed-project"

    with pytest.raises(GoogleRuntimeError) as error:
        provider.revalidate_quota_project(identity)
    assert error.value.code == "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH"


@pytest.mark.parametrize("failure", [RuntimeError("refresh failed"), TimeoutError("timeout")])
def test_adc_refresh_failure_is_bounded_and_redacted(failure: Exception) -> None:
    provider = identity_provider(credentials=FakeCredentials(refresh_error=failure))
    with pytest.raises(GoogleRuntimeError) as error:
        provider.resolve(scope=GOOGLE_TTS_SCOPE)
    assert error.value.code == "GOOGLE_TTS_REFRESH_FAILED"
    assert ACCESS_VALUE not in str(error.value)
    assert str(failure) not in str(error.value)


class FakeSocket:
    def __init__(self, response: bytes = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok") -> None:
        self.response = response
        self.sent = bytearray()
        self.connected: object | None = None
        self.closed = False
        self.timeout: float | None = None
        self.send_error: Exception | None = None
        self.connect_error: Exception | None = None
        self.peer = "8.8.8.8"
        self.fail_after = 0

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def connect(self, address: object) -> None:
        if self.connect_error:
            raise self.connect_error
        self.connected = address

    def send(self, data: bytes) -> int:
        if self.send_error:
            if self.fail_after:
                self.sent.extend(data[: self.fail_after])
            raise self.send_error
        self.sent.extend(data)
        return len(data)

    def recv(self, size: int) -> bytes:
        if not self.response:
            return b""
        result, self.response = self.response[:size], self.response[size:]
        return result

    def getpeername(self) -> tuple[str, int]:
        return self.peer, 443

    def shutdown(self, _: int) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class FakeTLSContext:
    def __init__(self, sock: FakeSocket, *, error: Exception | None = None) -> None:
        self.sock = sock
        self.error = error
        self.server_names: list[str] = []

    def wrap_socket(self, raw: FakeSocket, *, server_hostname: str) -> FakeSocket:
        if self.error:
            raise self.error
        self.server_names.append(server_hostname)
        return raw


def transport(
    *,
    socket_value: FakeSocket | None = None,
    addresses: tuple[str, ...] = ("8.8.8.8",),
    tls_error: Exception | None = None,
    max_response_bytes: int = 1000,
) -> tuple[RegionalGoogleTTSTransport, FakeSocket, FakeTLSContext, list[object]]:
    sock = socket_value or FakeSocket()
    context = FakeTLSContext(sock, error=tls_error)
    resolutions: list[object] = []

    def resolver(
        host: str, port: int, **_: object
    ) -> list[tuple[object, object, int, str, tuple[str, int]]]:
        resolutions.append((host, port))
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses
        ]

    def socket_factory(*_: object) -> FakeSocket:
        return sock

    instance = RegionalGoogleTTSTransport(
        enabled=True,
        activation_evidence_sha256=CHECKSUM,
        resolver=resolver,
        socket_factory=socket_factory,
        tls_context_factory=lambda: context,
        max_response_bytes=max_response_bytes,
    )
    return instance, sock, context, resolutions


def test_disabled_transport_never_resolves_or_opens_socket() -> None:
    calls: list[object] = []

    def resolver(*_: object, **__: object) -> list[tuple[Any, ...]]:
        calls.append(object())
        return []

    instance = RegionalGoogleTTSTransport(enabled=False, resolver=resolver)
    with pytest.raises(GoogleRuntimeError) as error:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_DISABLED"
    assert calls == []


def test_transport_accepts_only_pinned_eu_https_url_and_port() -> None:
    instance, _, _, _ = transport()
    for url in (
        "http://eu-texttospeech.googleapis.com/v1/text:synthesize",
        GOOGLE_TTS_ENDPOINT + ":8443/v1/text:synthesize",
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        GOOGLE_TTS_URL + "?redirect=https://example.invalid",
    ):
        with pytest.raises(GoogleRuntimeError) as error:
            instance.prepare(url=url, timeout_seconds=1)
        assert error.value.code == "GOOGLE_TTS_ENDPOINT_INVALID"


@pytest.mark.parametrize("timeout", [600.0, threading.TIMEOUT_MAX])
def test_transport_accepts_configured_finite_long_response_timeout(timeout: float) -> None:
    instance, sock, _, _ = transport()

    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=timeout)
    response = prepared.send(
        headers={"Content-Type": "application/json"},
        json_body={"input": {"text": "fake"}},
        timeout_seconds=timeout,
    )

    assert sock.timeout == timeout
    assert response.status_code == 200


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        threading.TIMEOUT_MAX + 1,
        10**1000,
        float("nan"),
        float("inf"),
        True,
        "180",
        None,
    ],
)
def test_transport_rejects_invalid_timeout(timeout: object) -> None:
    instance, _, _, _ = transport()

    with pytest.raises(GoogleRuntimeError) as error:
        instance.prepare(
            url=GOOGLE_TTS_URL,
            timeout_seconds=cast(float, timeout),
        )

    assert error.value.code == "GOOGLE_TTS_TIMEOUT_INVALID"


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.1.1",
        "224.0.0.1",
        "0.0.0.0",
        "192.0.2.1",
        "::1",
        "fc00::1",
        "fe80::1",
    ],
)
def test_all_prohibited_dns_answers_are_rejected(address: str) -> None:
    instance, _, _, _ = transport(addresses=("8.8.8.8", address))
    with pytest.raises(GoogleRuntimeError) as error:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_ADDRESS_INVALID"


def test_prepared_session_binds_checked_peer_tls_sni_and_exact_port() -> None:
    instance, sock, context, resolutions = transport()
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=2)
    assert prepared.url == GOOGLE_TTS_URL
    assert prepared.peer_ip == "8.8.8.8"
    assert prepared.peer_port == 443
    assert prepared.tls_server_name == "eu-texttospeech.googleapis.com"
    assert prepared.dns_pinned is True
    assert prepared.redirects_disabled is True
    assert resolutions == [("eu-texttospeech.googleapis.com", 443)]
    assert context.server_names == ["eu-texttospeech.googleapis.com"]
    assert sock.connected == ("8.8.8.8", 443)
    response = prepared.send(
        headers={"Authorization": f"Bearer {ACCESS_VALUE}", "Content-Type": "application/json"},
        json_body={"input": {"text": "fake"}},
        timeout_seconds=2,
    )
    assert response.status_code == 200
    assert response.body == b"ok"
    assert response.final_url == GOOGLE_TTS_URL
    assert response.proxy_used is False
    assert ACCESS_VALUE.encode() in sock.sent


def test_proxy_environment_is_not_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "https://127.0.0.1:9")
    instance, _, _, _ = transport()
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert prepared.proxy_used is False


def test_peer_mismatch_and_tls_failures_fail_closed() -> None:
    sock = FakeSocket()
    sock.peer = "1.1.1.1"
    instance, _, _, _ = transport(socket_value=sock)
    with pytest.raises(GoogleRuntimeError) as mismatch:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert mismatch.value.code == "GOOGLE_TTS_PEER_MISMATCH"
    instance, _, _, _ = transport(tls_error=ssl.SSLError("certificate failed"))
    with pytest.raises(GoogleRuntimeError) as tls_error:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert tls_error.value.code == "GOOGLE_TTS_TLS_FAILED"


def test_redirect_is_reported_without_following() -> None:
    sock = FakeSocket(
        b"HTTP/1.1 302 Found\r\nLocation: https://example.invalid\r\nContent-Length: 0\r\n\r\n"
    )
    instance, _, _, _ = transport(socket_value=sock)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_REDIRECT_REJECTED"
    assert b"example.invalid" not in bytes(sock.sent)


def test_partial_write_is_egress_possible_and_not_retryable() -> None:
    sock = FakeSocket()
    sock.send_error = TimeoutError("write timeout")
    sock.fail_after = 5
    instance, _, _, _ = transport(socket_value=sock)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    with pytest.raises(GoogleTransportError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.egress_possible is True


def test_timeout_before_write_is_not_egress_possible() -> None:
    sock = FakeSocket()
    sock.connect_error = TimeoutError("connect timeout")
    instance, _, _, _ = transport(socket_value=sock)
    with pytest.raises(GoogleRuntimeError) as error:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_CONNECT_FAILED"
    assert error.value.egress_possible is False


def test_response_size_is_strictly_bounded() -> None:
    sock = FakeSocket(b"HTTP/1.1 200 OK\r\nContent-Length: 9\r\n\r\ntoo large")
    instance, _, _, _ = transport(socket_value=sock, max_response_bytes=8)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_RESPONSE_TOO_LARGE"


class FakeOfficialGrpcBindings:
    def __init__(
        self,
        *,
        audio: bytes = b"RIFF-fake",
        failure: Exception | None = None,
        grpc_status: str | None = None,
    ) -> None:
        self.audio = audio
        self.failure = failure
        self.grpc_status = grpc_status
        self.open_calls: list[tuple[str, str, float]] = []
        self.synthesis_calls: list[dict[str, object]] = []
        self.closed: list[object] = []

    def open_client(
        self, *, target_ip: str, hostname: str, timeout_seconds: float
    ) -> tuple[object, object]:
        self.open_calls.append((target_ip, hostname, timeout_seconds))
        return object(), object()

    def synthesize(
        self,
        *,
        client: object,
        json_body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> bytes:
        self.synthesis_calls.append(
            {
                "client": client,
                "json_body": json_body,
                "headers": headers,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.failure is not None:
            raise self.failure
        return self.audio

    def failure_status(self, error: Exception) -> str | None:
        return self.grpc_status if self.grpc_status is not None else str(error)

    def close(self, channel: object) -> None:
        self.closed.append(channel)


def official_grpc_transport(
    bindings: FakeOfficialGrpcBindings,
    *,
    enabled: bool = True,
    addresses: tuple[str, ...] = ("8.8.8.8",),
    max_response_bytes: int = 6_000_000,
) -> tuple[OfficialUnaryGoogleTTSTransport, list[tuple[str, int]]]:
    resolutions: list[tuple[str, int]] = []

    def resolver(
        host: str, port: int, **_: object
    ) -> list[tuple[object, object, int, str, tuple[str, int]]]:
        resolutions.append((host, port))
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses
        ]

    return (
        OfficialUnaryGoogleTTSTransport(
            enabled=enabled,
            activation_evidence_sha256=CHECKSUM if enabled else "",
            resolver=resolver,
            bindings_factory=lambda: bindings,
            max_response_bytes=max_response_bytes,
        ),
        resolutions,
    )


def test_official_grpc_disabled_never_imports_resolves_or_opens_channel() -> None:
    bindings = FakeOfficialGrpcBindings()
    instance, resolutions = official_grpc_transport(bindings, enabled=False)

    with pytest.raises(GoogleRuntimeError) as caught:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    assert caught.value.code == "GOOGLE_TTS_DISABLED"
    assert resolutions == [] and bindings.open_calls == []


def test_official_grpc_missing_dependency_fails_before_dns() -> None:
    resolutions: list[object] = []

    def missing() -> FakeOfficialGrpcBindings:
        raise GoogleRuntimeError(
            "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE",
            "Google TTS optional dependency is unavailable.",
        )

    def resolver(*_args: object, **_kwargs: object) -> list[tuple[Any, ...]]:
        resolutions.append(object())
        return []

    instance = OfficialUnaryGoogleTTSTransport(
        enabled=True,
        activation_evidence_sha256=CHECKSUM,
        resolver=resolver,
        bindings_factory=missing,
    )

    with pytest.raises(GoogleRuntimeError) as caught:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    assert caught.value.code == "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE"
    assert resolutions == []


def test_official_grpc_rejects_private_dns_before_opening_channel() -> None:
    bindings = FakeOfficialGrpcBindings()
    instance, _ = official_grpc_transport(bindings, addresses=("10.0.0.1",))

    with pytest.raises(GoogleRuntimeError) as caught:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    assert caught.value.code == "GOOGLE_TTS_ADDRESS_INVALID"
    assert bindings.open_calls == []


def test_official_grpc_uses_exact_pinned_unary_contract_and_wraps_audio() -> None:
    bindings = FakeOfficialGrpcBindings(audio=b"RIFF-exact-audio")
    instance, resolutions = official_grpc_transport(bindings)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)
    request = {
        "input": {"text": "canonical narration", "prompt": "governed style"},
        "voice": {
            "languageCode": "en-IN",
            "modelName": "gemini-2.5-pro-tts",
            "name": "Despina",
        },
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000},
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_VALUE}",
        "Content-Type": "application/json; charset=utf-8",
        "x-goog-user-project": QUOTA_PROJECT,
    }

    response = prepared.send(
        headers=headers,
        json_body=request,
        timeout_seconds=600,
    )

    assert prepared.transport_kind == "OFFICIAL_GRPC_UNARY"
    assert prepared.dns_pinned is True and prepared.proxy_used is False
    assert prepared.redirects_disabled is True and prepared.tls_verified is True
    assert prepared.tls_server_name == "eu-texttospeech.googleapis.com"
    assert prepared.peer_ip == "8.8.8.8" and prepared.peer_port == 443
    assert resolutions == [("eu-texttospeech.googleapis.com", 443)]
    assert bindings.open_calls == [("8.8.8.8", "eu-texttospeech.googleapis.com", 600)]
    assert bindings.synthesis_calls[0]["json_body"] == request
    assert bindings.synthesis_calls[0]["headers"] == headers
    assert bindings.synthesis_calls[0]["timeout_seconds"] == 600
    assert response.transport_kind == "OFFICIAL_GRPC_UNARY"
    assert response.status_code == 200
    assert base64.b64decode(json.loads(response.body)["audioContent"]) == b"RIFF-exact-audio"
    assert response.resolved_addresses == ("8.8.8.8",) and response.peer_ip == "8.8.8.8"
    assert len(bindings.closed) == 1


def test_official_sdk_binding_builds_exact_public_request_without_network() -> None:
    from google.cloud import texttospeech_v1 as texttospeech

    captured: dict[str, object] = {}

    class FakeClient:
        def synthesize_speech(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return type("Response", (), {"audio_content": b"RIFF-sdk"})()

    binding = google_tts_runtime_module._OfficialGoogleGrpcBindings(
        grpc_module=object(),
        tts_module=texttospeech,
        transport_type=object(),
    )
    body = {
        "input": {"text": "canonical narration", "prompt": "governed style"},
        "voice": {
            "languageCode": "en-IN",
            "modelName": "gemini-2.5-pro-tts",
            "name": "Despina",
        },
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000},
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_VALUE}",
        "Content-Type": "application/json; charset=utf-8",
        "x-goog-user-project": QUOTA_PROJECT,
    }

    assert (
        binding.synthesize(
            client=FakeClient(),
            json_body=body,
            headers=headers,
            timeout_seconds=600,
        )
        == b"RIFF-sdk"
    )

    request = cast(Any, captured["request"])
    assert request.input.text == "canonical narration"
    assert request.input.prompt == "governed style"
    assert request.voice.language_code == "en-IN"
    assert request.voice.model_name == "gemini-2.5-pro-tts"
    assert request.voice.name == "Despina"
    assert request.audio_config.audio_encoding == texttospeech.AudioEncoding.LINEAR16
    assert request.audio_config.sample_rate_hertz == 24000
    assert captured["retry"] is None and captured["timeout"] == 600
    assert captured["metadata"] == (
        ("authorization", f"Bearer {ACCESS_VALUE}"),
        ("x-goog-user-project", QUOTA_PROJECT),
    )


def test_official_sdk_binding_pins_tls_channel_and_disables_proxy() -> None:
    captured: dict[str, object] = {}

    class FakeChannel:
        def close(self) -> None:
            captured["closed"] = True

    class FakeReady:
        def result(self, *, timeout: float) -> None:
            captured["ready_timeout"] = timeout

    class FakeGrpc:
        @staticmethod
        def ssl_channel_credentials() -> str:
            return "tls-credentials"

        @staticmethod
        def secure_channel(
            target: str, credentials: object, *, options: tuple[tuple[str, object], ...]
        ) -> FakeChannel:
            captured.update(target=target, credentials=credentials, options=options)
            return FakeChannel()

        @staticmethod
        def channel_ready_future(channel: object) -> FakeReady:
            captured["ready_channel"] = channel
            return FakeReady()

    class FakeTransport:
        def __init__(self, *, channel: object) -> None:
            captured["transport_channel"] = channel

    class FakeTTS:
        @staticmethod
        def TextToSpeechClient(*, transport: object) -> object:
            captured["client_transport"] = transport
            return object()

    binding = google_tts_runtime_module._OfficialGoogleGrpcBindings(
        grpc_module=FakeGrpc,
        tts_module=FakeTTS,
        transport_type=FakeTransport,
    )
    client, channel = binding.open_client(
        target_ip="8.8.8.8",
        hostname="eu-texttospeech.googleapis.com",
        timeout_seconds=600,
    )

    assert client is not None and channel is captured["ready_channel"]
    assert captured["target"] == "ipv4:8.8.8.8:443"
    assert captured["credentials"] == "tls-credentials"
    assert captured["options"] == (
        ("grpc.ssl_target_name_override", "eu-texttospeech.googleapis.com"),
        ("grpc.default_authority", "eu-texttospeech.googleapis.com"),
        ("grpc.enable_http_proxy", 0),
        ("grpc.enable_retries", 0),
    )
    assert captured["ready_timeout"] == 600
    assert captured.get("closed") is None


def test_official_sdk_binding_closes_channel_when_readiness_fails() -> None:
    captured: dict[str, object] = {}

    class FakeChannel:
        def close(self) -> None:
            captured["closed"] = True

    class FakeReady:
        def result(self, *, timeout: float) -> None:
            captured["timeout"] = timeout
            raise TimeoutError("private-channel-detail")

    class FakeGrpc:
        ssl_channel_credentials = staticmethod(object)
        secure_channel = staticmethod(lambda *_args, **_kwargs: FakeChannel())
        channel_ready_future = staticmethod(lambda _channel: FakeReady())

    binding = google_tts_runtime_module._OfficialGoogleGrpcBindings(
        grpc_module=FakeGrpc,
        tts_module=object(),
        transport_type=object(),
    )

    with pytest.raises(TimeoutError):
        binding.open_client(
            target_ip="8.8.8.8",
            hostname="eu-texttospeech.googleapis.com",
            timeout_seconds=600,
        )

    assert captured == {"timeout": 600, "closed": True}


@pytest.mark.parametrize(
    ("body_mutation", "header_mutation"),
    (
        (("voice", "modelName", "alternate-model"), None),
        (("voice", "languageCode", "en-US"), None),
        (("audioConfig", "sampleRateHertz", 22_050), None),
        (("audioConfig", "audioEncoding", "MP3"), None),
        (("input", "prompt", ""), None),
        (None, ("Content-Type", "application/json")),
        (None, ("Authorization", "Bearer fake\nInjected: yes")),
        (None, ("x-goog-user-project", "UPPER-project")),
        (None, ("X-Injected", "forbidden")),
    ),
)
def test_official_sdk_binding_rejects_request_and_metadata_mutations_before_call(
    body_mutation: tuple[str, str, object] | None,
    header_mutation: tuple[str, str] | None,
) -> None:
    from google.cloud import texttospeech_v1 as texttospeech

    class RejectCallClient:
        def synthesize_speech(self, **_: object) -> object:
            raise AssertionError("invalid request reached the official client")

    binding = google_tts_runtime_module._OfficialGoogleGrpcBindings(
        grpc_module=object(),
        tts_module=texttospeech,
        transport_type=object(),
    )
    body: dict[str, object] = {
        "input": {"text": "canonical narration", "prompt": "governed style"},
        "voice": {
            "languageCode": "en-IN",
            "modelName": "gemini-2.5-pro-tts",
            "name": "Despina",
        },
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000},
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_VALUE}",
        "Content-Type": "application/json; charset=utf-8",
        "x-goog-user-project": QUOTA_PROJECT,
    }
    if body_mutation is not None:
        parent, leaf, value = body_mutation
        cast(dict[str, object], body[parent])[leaf] = value
    if header_mutation is not None:
        name, value = header_mutation
        headers[name] = value

    with pytest.raises(GoogleRuntimeError) as caught:
        binding.synthesize(
            client=RejectCallClient(),
            json_body=body,
            headers=headers,
            timeout_seconds=600,
        )

    assert caught.value.code == "GOOGLE_TTS_REQUEST_INVALID"
    assert caught.value.egress_possible is False


def test_official_grpc_is_single_use_and_bounds_raw_audio() -> None:
    bindings = FakeOfficialGrpcBindings(audio=b"12345")
    instance, _ = official_grpc_transport(bindings, max_response_bytes=4)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    with pytest.raises(GoogleTransportError) as oversized:
        prepared.send(headers={}, json_body={}, timeout_seconds=600)
    assert oversized.value.egress_possible is True
    assert oversized.value.__context__ is None

    with pytest.raises(GoogleRuntimeError) as replay:
        prepared.send(headers={}, json_body={}, timeout_seconds=600)
    assert replay.value.code == "GOOGLE_TTS_SESSION_INVALID"


def test_official_grpc_failure_retains_only_allowlisted_status() -> None:
    private_detail = "private-provider-debug-detail"
    bindings = FakeOfficialGrpcBindings(
        failure=RuntimeError(private_detail),
        grpc_status="DEADLINE_EXCEEDED",
    )
    instance, _ = official_grpc_transport(bindings)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    with pytest.raises(GoogleTransportError) as caught:
        prepared.send(headers={}, json_body={}, timeout_seconds=600)

    assert caught.value.egress_possible is True
    assert caught.value.grpc_status == "DEADLINE_EXCEEDED"
    assert caught.value.__context__ is None
    assert private_detail not in str(caught.value)
    frames: list[str] = []
    traceback = caught.value.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name == "send":
            frames.append(repr(traceback.tb_frame.f_locals))
        traceback = traceback.tb_next
    assert frames and private_detail not in "".join(frames)
    assert len(bindings.closed) == 1


def test_official_grpc_prepare_discards_raw_exception_context() -> None:
    private_detail = "private-channel-detail-DO-NOT-RETAIN"

    class FailingOpenBindings(FakeOfficialGrpcBindings):
        def open_client(
            self, *, target_ip: str, hostname: str, timeout_seconds: float
        ) -> tuple[object, object]:
            raise RuntimeError(private_detail)

    instance, _ = official_grpc_transport(FailingOpenBindings())
    with pytest.raises(GoogleRuntimeError) as caught:
        instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    assert caught.value.code == "GOOGLE_TTS_CONNECT_FAILED"
    assert caught.value.__context__ is None
    assert private_detail not in repr(caught.value)


@pytest.mark.parametrize("egress_possible", [False, True])
def test_official_grpc_normalizes_runtime_failure_with_exact_egress_state(
    egress_possible: bool,
) -> None:
    bindings = FakeOfficialGrpcBindings(
        failure=GoogleRuntimeError(
            "GOOGLE_TTS_REQUEST_INVALID" if not egress_possible else "GOOGLE_TTS_RESPONSE_INVALID",
            "bounded runtime failure",
            egress_possible=egress_possible,
        )
    )
    instance, _ = official_grpc_transport(bindings)
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=600)

    with pytest.raises(GoogleTransportError) as caught:
        prepared.send(headers={}, json_body={}, timeout_seconds=600)

    assert caught.value.egress_possible is egress_possible
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "wire",
    [b"not-http", b"HTTP/1.1 nope\r\n\r\n", b"HTTP/1.1 200 OK\r\nContent-Length: nope\r\n\r\n"],
)
def test_malformed_response_is_normalized(wire: bytes) -> None:
    instance, _, _, _ = transport(socket_value=FakeSocket(wire))
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_RESPONSE_INVALID"


def test_prepared_session_cannot_be_reused_after_response() -> None:
    instance, _, _, _ = transport()
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    prepared.send(headers={}, json_body={}, timeout_seconds=1)
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_SESSION_INVALID"


def test_prepared_session_explicit_close_is_idempotent_and_prevents_send() -> None:
    instance, sock, _, _ = transport()
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    prepared.close()
    prepared.close()
    assert sock.closed is True
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers={}, json_body={}, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_SESSION_INVALID"


@pytest.mark.parametrize(
    "headers,json_body",
    [
        ({"X-Unsafe\r\nInjected": "value"}, {}),
        ({"X-Non-Ascii": "snowman-\N{SNOWMAN}"}, {}),
        ({}, {"not-json": object()}),
    ],
)
def test_pre_send_validation_failure_closes_session(
    headers: dict[str, str], json_body: dict[str, object]
) -> None:
    instance, sock, _, _ = transport()
    prepared = instance.prepare(url=GOOGLE_TTS_URL, timeout_seconds=1)
    with pytest.raises(GoogleRuntimeError) as error:
        prepared.send(headers=headers, json_body=json_body, timeout_seconds=1)
    assert error.value.code == "GOOGLE_TTS_REQUEST_INVALID"
    assert error.value.egress_possible is False
    assert sock.closed is True
    assert sock.sent == b""


def test_runtime_constants_keep_model_locale_voice_and_endpoint_out_of_caller_control() -> None:
    assert GOOGLE_TTS_URL == "https://eu-texttospeech.googleapis.com/v1/text:synthesize"
    assert GOOGLE_TTS_SCOPE == "https://www.googleapis.com/auth/cloud-platform"
    assert GOOGLE_TTS_ENDPOINT == "https://eu-texttospeech.googleapis.com"
    assert "model" not in RegionalGoogleTTSTransport.__init__.__annotations__
    assert json.dumps({"model": "caller-controlled"}) not in str(GoogleRuntimeError)
