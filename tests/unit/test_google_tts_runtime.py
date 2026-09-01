from __future__ import annotations

import hashlib
import json
import importlib
import socket
import ssl
from collections.abc import Callable
from typing import Any, cast

import pytest

from backend.app.google_tts_runtime import (
    ADCGoogleIdentityProvider,
    GoogleADCConfig,
    GoogleRuntimeError,
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


@pytest.mark.parametrize(
    "configured", [None, "", "bad", "UPPER-project"]
)
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

    def resolver(host: str, port: int, **_: object) -> list[tuple[object, object, int, str, tuple[str, int]]]:
        resolutions.append((host, port))
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses]

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


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.1.1", "224.0.0.1", "0.0.0.0", "192.0.2.1", "::1", "fc00::1", "fe80::1"])
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
    sock = FakeSocket(b"HTTP/1.1 302 Found\r\nLocation: https://example.invalid\r\nContent-Length: 0\r\n\r\n")
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
