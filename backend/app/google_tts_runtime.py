"""Optional, fail-closed Google Gemini-TTS identity and transport runtime.

This module is deliberately separate from the narration-facing provider.  It
does not choose a model, voice, locale, URL, or provider for callers.  The
application keeps the Google provider disabled unless server-owned activation
evidence is supplied by a later authority.
No LLM, script, or citation generation occurs here; caller-owned trace metadata
stays at the provider boundary.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import ipaddress
import json
import logging
import re
import socket
import ssl
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast
from urllib.parse import SplitResult, urlsplit

from backend.app.tts_provider import (
    GOOGLE_TTS_SCOPE,
    GOOGLE_TTS_URL,
    GoogleIdentity,
    GoogleTTSHTTPResponse,
    GoogleTransportError,
)

LOGGER = logging.getLogger(__name__ + ".google")
_CHECKSUM = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HOSTNAME = "eu-texttospeech.googleapis.com"
_PORT = 443
_PATH = "/v1/text:synthesize"
_MAX_HEADER_BYTES = 32_768
_DEFAULT_MAX_RESPONSE_BYTES = 6_000_000
_READ_CHUNK_BYTES = 64 * 1024
_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]\Z")


def _valid_timeout(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 < value <= threading.TIMEOUT_MAX
    )


class GoogleRuntimeError(RuntimeError):
    """Bounded runtime error; no credential or provider response is retained."""

    def __init__(self, code: str, message: str, *, egress_possible: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.egress_possible = egress_possible


@dataclass(frozen=True)
class GoogleADCConfig:
    """Server-owned activation evidence for optional ADC resolution."""

    enabled: bool = False
    activation_evidence_sha256: str = ""
    quota_project_id: str | None = field(default=None, repr=False)
    quota_project_evidence_sha256: str | None = None


class _Credentials(Protocol):
    token: str | None
    quota_project_id: str | None

    def refresh(self, request: object) -> None: ...


class ADCGoogleIdentityProvider:
    """Resolve ADC lazily only after the provider has passed its gates."""

    def __init__(
        self,
        *,
        config: GoogleADCConfig = GoogleADCConfig(),
        default_loader: Callable[..., tuple[_Credentials, str | None]] | None = None,
        request_factory: Callable[[], object] | None = None,
    ) -> None:
        self.config = config
        self._default_loader = default_loader
        self._request_factory = request_factory

    def resolve(self, *, scope: str) -> GoogleIdentity:
        self._validate_preconditions(scope)
        loader = self._default_loader or self._load_default_loader()
        try:
            credentials, project_id = loader(scopes=[GOOGLE_TTS_SCOPE])
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ADC_UNAVAILABLE", "Google TTS ADC identity is unavailable."
            ) from None
        configured_quota = cast(str, self.config.quota_project_id)
        self._validate_credential_quota(credentials, configured_quota)
        request_factory = self._request_factory or self._load_request_factory()
        try:
            credentials.refresh(request_factory())
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_REFRESH_FAILED", "Google TTS ADC refresh was unsuccessful."
            ) from None
        access_value = getattr(credentials, "token", None)
        if (
            not isinstance(access_value, str)
            or not access_value
            or "\r" in access_value
            or "\n" in access_value
        ):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_TOKEN_INVALID", "Google TTS ADC returned an invalid token."
            )
        evidence = {
            "credentialType": type(credentials).__name__,
            "projectIdPresent": bool(project_id),
            "quotaProjectSha256": self.config.quota_project_evidence_sha256,
            "scope": GOOGLE_TTS_SCOPE,
        }
        identity_checksum = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        )
        return GoogleIdentity(
            access_token=access_value,
            identity_evidence_sha256=identity_checksum,
            quota_project_id=configured_quota,
            quota_project_sha256=cast(str, self.config.quota_project_evidence_sha256),
        )

    def revalidate_quota_project(self, identity: GoogleIdentity) -> None:
        """Reload ADC and fail closed if its quota binding changed before egress."""
        self._validate_preconditions(GOOGLE_TTS_SCOPE)
        configured_quota = cast(str, self.config.quota_project_id)
        if (
            not isinstance(identity, GoogleIdentity)
            or identity.quota_project_id != configured_quota
            or identity.quota_project_sha256 != self.config.quota_project_evidence_sha256
        ):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH",
                "Google TTS quota-project evidence is invalid.",
            )
        loader = self._default_loader or self._load_default_loader()
        try:
            credentials, _project_id = loader(scopes=[GOOGLE_TTS_SCOPE])
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ADC_UNAVAILABLE", "Google TTS ADC identity is unavailable."
            ) from None
        self._validate_credential_quota(credentials, configured_quota)

    def _validate_preconditions(self, scope: str) -> None:
        if not self.config.enabled:
            raise GoogleRuntimeError("GOOGLE_TTS_DISABLED", "Google TTS runtime is disabled.")
        if scope != GOOGLE_TTS_SCOPE:
            raise GoogleRuntimeError("GOOGLE_TTS_SCOPE_INVALID", "Google TTS scope is invalid.")
        if not _CHECKSUM.fullmatch(self.config.activation_evidence_sha256):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ACTIVATION_INVALID", "Google TTS activation evidence is invalid."
            )
        configured_quota = self.config.quota_project_id
        approved_hash = self.config.quota_project_evidence_sha256
        if (
            not isinstance(configured_quota, str)
            or not _PROJECT_ID.fullmatch(configured_quota)
            or not isinstance(approved_hash, str)
            or not _CHECKSUM.fullmatch(approved_hash)
            or not hmac.compare_digest(
                approved_hash,
                "sha256:" + hashlib.sha256(configured_quota.encode("utf-8")).hexdigest(),
            )
        ):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_QUOTA_PROJECT_INVALID",
                "Google TTS quota-project evidence is invalid.",
            )

    @staticmethod
    def _validate_credential_quota(credentials: _Credentials, configured_quota: str) -> None:
        credential_quota = getattr(credentials, "quota_project_id", None)
        if not isinstance(credential_quota, str) or not hmac.compare_digest(
            credential_quota, configured_quota
        ):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH",
                "Google TTS quota-project evidence is invalid.",
            )

    @staticmethod
    def _load_default_loader() -> Callable[..., tuple[_Credentials, str | None]]:
        try:
            auth = importlib.import_module("google.auth")
            loader = getattr(auth, "default")
        except (ImportError, AttributeError):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE",
                "Google TTS optional dependency is unavailable.",
            ) from None
        return cast(Callable[..., tuple[_Credentials, str | None]], loader)

    @staticmethod
    def _load_request_factory() -> Callable[[], object]:
        try:
            module = importlib.import_module("google.auth.transport.requests")
            request_type = getattr(module, "Request")
        except (ImportError, AttributeError):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE",
                "Google TTS optional transport dependency is unavailable.",
            ) from None
        return cast(Callable[[], object], request_type)


class _TLSContext(Protocol):
    def wrap_socket(self, sock: socket.socket, *, server_hostname: str) -> socket.socket: ...


class RegionalGoogleTTSTransport:
    """Direct stdlib HTTPS transport bound to the approved EU Google endpoint."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        activation_evidence_sha256: str = "",
        resolver: Callable[..., Sequence[tuple[Any, ...]]] = socket.getaddrinfo,
        socket_factory: Callable[..., Any] = socket.socket,
        tls_context_factory: Callable[[], Any] = ssl.create_default_context,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        self.enabled = enabled
        self.activation_evidence_sha256 = activation_evidence_sha256
        self._resolver = resolver
        self._socket_factory = socket_factory
        self._tls_context_factory = tls_context_factory
        self._max_response_bytes = max(1, max_response_bytes)

    def prepare(self, *, url: str, timeout_seconds: float) -> _PreparedGoogleSession:
        self._validate_activation()
        parsed = self._parse_url(url)
        if not _valid_timeout(timeout_seconds):
            raise GoogleRuntimeError("GOOGLE_TTS_TIMEOUT_INVALID", "Google TTS timeout is invalid.")
        try:
            answers = list(self._resolver(parsed.hostname or "", _PORT, type=socket.SOCK_STREAM))
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_DNS_FAILED", "Google TTS DNS resolution failed."
            ) from None
        checked: list[tuple[int, int, int, tuple[Any, ...], str]] = []
        try:
            for answer in answers:
                family, kind, protocol, _, sockaddr = answer
                address = ipaddress.ip_address(str(sockaddr[0]))
                if (
                    not address.is_global
                    or address.is_private
                    or address.is_loopback
                    or address.is_link_local
                    or address.is_multicast
                    or address.is_unspecified
                    or address.is_reserved
                ):
                    raise ValueError("non-global address")
                checked.append((int(family), int(kind), int(protocol), sockaddr, str(address)))
        except (IndexError, TypeError, ValueError):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ADDRESS_INVALID", "Google TTS resolved address policy failed."
            ) from None
        if not checked:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ADDRESS_INVALID", "Google TTS resolved address policy failed."
            )
        family, kind, protocol, sockaddr, checked_peer = checked[0]
        raw: socket.socket | None = None
        try:
            raw = self._socket_factory(family, kind, protocol)
            raw.settimeout(timeout_seconds)
            raw.connect(sockaddr)
            peer_name = raw.getpeername()
            actual_peer = str(peer_name[0])
            if ipaddress.ip_address(actual_peer) != ipaddress.ip_address(checked_peer):
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_PEER_MISMATCH", "Google TTS checked peer changed."
                )
            context = self._tls_context_factory()
            if hasattr(context, "check_hostname"):
                setattr(context, "check_hostname", True)
            tls_socket = context.wrap_socket(raw, server_hostname=_HOSTNAME)
        except GoogleRuntimeError:
            self._close(raw)
            raise
        except ssl.SSLError:
            self._close(raw)
            raise GoogleRuntimeError(
                "GOOGLE_TTS_TLS_FAILED", "Google TTS TLS verification failed."
            ) from None
        except (OSError, TimeoutError):
            self._close(raw)
            raise GoogleRuntimeError(
                "GOOGLE_TTS_CONNECT_FAILED", "Google TTS connection failed before egress."
            ) from None
        return _PreparedGoogleSession(
            sock=tls_socket,
            url=GOOGLE_TTS_URL,
            resolved_addresses=tuple(item[4] for item in checked),
            peer_ip=checked_peer,
            max_response_bytes=self._max_response_bytes,
        )

    def _validate_activation(self) -> None:
        if not self.enabled:
            raise GoogleRuntimeError("GOOGLE_TTS_DISABLED", "Google TTS runtime is disabled.")
        if not _CHECKSUM.fullmatch(self.activation_evidence_sha256):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ACTIVATION_INVALID", "Google TTS activation evidence is invalid."
            )

    @staticmethod
    def _parse_url(url: str) -> SplitResult:
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ENDPOINT_INVALID", "Google TTS endpoint is invalid."
            ) from None
        if (
            parsed.scheme != "https"
            or parsed.hostname != _HOSTNAME
            or port not in (None, _PORT)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path != _PATH
            or parsed.query
            or parsed.fragment
        ):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ENDPOINT_INVALID", "Google TTS endpoint is invalid."
            )
        return parsed

    @staticmethod
    def _close(sock: socket.socket | None) -> None:
        if sock is None:
            return
        try:
            sock.close()
        except OSError:
            pass


class _PreparedGoogleSession:
    """Single-use opaque capability holding the already-attested TLS socket."""

    url = GOOGLE_TTS_URL
    proxy_used = False
    tls_verified = True
    tls_server_name = _HOSTNAME
    peer_port = _PORT
    redirects_disabled = True
    dns_pinned = True
    transport_kind = "REST_HTTP_1_1"

    def __init__(
        self,
        *,
        sock: socket.socket,
        url: str,
        resolved_addresses: tuple[str, ...],
        peer_ip: str,
        max_response_bytes: int,
    ) -> None:
        self._sock = sock
        self.url = url
        self.resolved_addresses = resolved_addresses
        self.peer_ip = peer_ip
        self._max_response_bytes = max_response_bytes
        self._used = False

    def close(self) -> None:
        """Consume and close this capability without writing provider data."""
        self._used = True
        try:
            self._sock.close()
        except OSError:
            pass

    def send(
        self,
        *,
        headers: Mapping[str, str],
        json_body: Mapping[str, object],
        timeout_seconds: float,
    ) -> GoogleTTSHTTPResponse:
        if self._used:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_SESSION_INVALID", "Google TTS prepared session is not reusable."
            )
        if not _valid_timeout(timeout_seconds):
            raise GoogleRuntimeError("GOOGLE_TTS_TIMEOUT_INVALID", "Google TTS timeout is invalid.")
        self._used = True
        try:
            try:
                payload = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode(
                    "utf-8"
                )
                request_headers = {
                    "Host": _HOSTNAME,
                    "Content-Length": str(len(payload)),
                    "Connection": "close",
                }
                for name, value in headers.items():
                    if (
                        not isinstance(name, str)
                        or not isinstance(value, str)
                        or not _HEADER_NAME.fullmatch(name)
                        or name.lower() in {"host", "content-length", "connection"}
                        or "\r" in value
                        or "\n" in value
                    ):
                        raise ValueError("invalid header")
                    request_headers[name] = value
                wire = (
                    f"POST {_PATH} HTTP/1.1\r\n"
                    + "".join(f"{name}: {value}\r\n" for name, value in request_headers.items())
                    + "\r\n"
                ).encode("ascii") + payload
            except (TypeError, ValueError, UnicodeEncodeError):
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_REQUEST_INVALID",
                    "Google TTS request is invalid.",
                    egress_possible=False,
                ) from None
            sent = 0
            while sent < len(wire):
                count = self._sock.send(wire[sent:])
                if count <= 0:
                    raise OSError("socket made no progress")
                sent += count
            return self._read_response()
        except GoogleRuntimeError:
            raise
        except (OSError, TimeoutError, socket.timeout):
            # Once a write syscall is attempted, the kernel may have accepted
            # bytes even when it reports an error; classify that ambiguity as
            # possible egress and let the provider suppress retries.
            raise GoogleTransportError(egress_possible=True) from None
        finally:
            self.close()

    def _read_response(self) -> GoogleTTSHTTPResponse:
        header_bytes = bytearray()
        while b"\r\n\r\n" not in header_bytes:
            if len(header_bytes) >= _MAX_HEADER_BYTES:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID",
                    "Google TTS response headers are invalid.",
                    egress_possible=True,
                )
            chunk = self._sock.recv(min(_READ_CHUNK_BYTES, _MAX_HEADER_BYTES - len(header_bytes)))
            if not chunk:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID",
                    "Google TTS response headers are invalid.",
                    egress_possible=True,
                )
            header_bytes.extend(chunk)
        raw_headers, body_prefix = bytes(header_bytes).split(b"\r\n\r\n", 1)
        lines = raw_headers.split(b"\r\n")
        if not lines or not lines[0].startswith(b"HTTP/1.1 "):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID",
                "Google TTS response is malformed.",
                egress_possible=True,
            )
        try:
            status = int(lines[0].split(b" ", 2)[1])
            response_headers: dict[str, str] = {}
            for line in lines[1:]:
                name, value = line.split(b":", 1)
                response_headers[name.decode("ascii").lower()] = value.decode("latin-1").strip()
        except (IndexError, ValueError, UnicodeDecodeError):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID",
                "Google TTS response is malformed.",
                egress_possible=True,
            ) from None
        if 300 <= status < 400:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_REDIRECT_REJECTED",
                "Google TTS redirects are disabled.",
                egress_possible=True,
            )
        transfer_encoding = response_headers.get("transfer-encoding", "").lower()
        if transfer_encoding and transfer_encoding != "identity":
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID",
                "Google TTS response framing is unsupported.",
                egress_possible=True,
            )
        content_length = response_headers.get("content-length")
        if content_length is not None:
            try:
                expected = int(content_length)
            except ValueError:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID",
                    "Google TTS response length is invalid.",
                    egress_possible=True,
                ) from None
            if expected < 0 or expected > self._max_response_bytes:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_TOO_LARGE",
                    "Google TTS response exceeds its byte limit.",
                    egress_possible=True,
                )
            body = bytearray(body_prefix[:expected])
            while len(body) < expected:
                chunk = self._sock.recv(min(_READ_CHUNK_BYTES, expected - len(body)))
                if not chunk:
                    raise GoogleRuntimeError(
                        "GOOGLE_TTS_RESPONSE_INVALID",
                        "Google TTS response body is incomplete.",
                        egress_possible=True,
                    )
                body.extend(chunk)
        else:
            body = bytearray(body_prefix)
            if len(body) > self._max_response_bytes:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_TOO_LARGE",
                    "Google TTS response exceeds its byte limit.",
                    egress_possible=True,
                )
            while True:
                chunk = self._sock.recv(_READ_CHUNK_BYTES)
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > self._max_response_bytes:
                    raise GoogleRuntimeError(
                        "GOOGLE_TTS_RESPONSE_TOO_LARGE",
                        "Google TTS response exceeds its byte limit.",
                        egress_possible=True,
                    )
        return GoogleTTSHTTPResponse(
            status_code=status,
            headers=response_headers,
            body=bytes(body),
            final_url=GOOGLE_TTS_URL,
            redirect_count=0,
            peer_ip=self.peer_ip,
            resolved_addresses=self.resolved_addresses,
            proxy_used=False,
            tls_verified=True,
            tls_server_name=_HOSTNAME,
            peer_port=_PORT,
        )


class _GrpcBindings(Protocol):
    """Narrow wrapper around the optional official Google/gRPC dependency."""

    def open_client(
        self, *, target_ip: str, hostname: str, timeout_seconds: float
    ) -> tuple[object, object]: ...

    def synthesize(
        self,
        *,
        client: object,
        json_body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> bytes: ...

    def failure_status(self, error: Exception) -> str | None: ...

    def close(self, channel: object) -> None: ...


class _OfficialGoogleGrpcBindings:
    """Validated adapter for Google Cloud TTS's public unary gRPC client."""

    def __init__(self, *, grpc_module: Any, tts_module: Any, transport_type: Any) -> None:
        self._grpc = grpc_module
        self._tts = tts_module
        self._transport_type = transport_type

    def open_client(
        self, *, target_ip: str, hostname: str, timeout_seconds: float
    ) -> tuple[object, object]:
        address = ipaddress.ip_address(target_ip)
        target = (
            f"ipv4:{address.compressed}:{_PORT}"
            if address.version == 4
            else f"ipv6:[{address.compressed}]:{_PORT}"
        )
        channel = self._grpc.secure_channel(
            target,
            self._grpc.ssl_channel_credentials(),
            options=(
                ("grpc.ssl_target_name_override", hostname),
                ("grpc.default_authority", hostname),
                ("grpc.enable_http_proxy", 0),
                ("grpc.enable_retries", 0),
            ),
        )
        try:
            self._grpc.channel_ready_future(channel).result(timeout=timeout_seconds)
            transport = self._transport_type(channel=channel)
            return self._tts.TextToSpeechClient(transport=transport), channel
        except Exception:
            self.close(channel)
            raise

    def synthesize(
        self,
        *,
        client: object,
        json_body: Mapping[str, object],
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> bytes:
        request = self._request(json_body)
        authorization, quota_project = self._metadata_values(headers)
        call = getattr(client, "synthesize_speech", None)
        if not callable(call):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE",
                "Google TTS optional dependency is unavailable.",
            )
        response = call(
            request=request,
            retry=None,
            timeout=timeout_seconds,
            metadata=(
                ("authorization", authorization),
                ("x-goog-user-project", quota_project),
            ),
        )
        audio = getattr(response, "audio_content", None)
        if not isinstance(audio, bytes):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID",
                "Google TTS response is malformed.",
                egress_possible=True,
            )
        return audio

    def _request(self, body: Mapping[str, object]) -> object:
        if set(body) != {"input", "voice", "audioConfig"}:
            raise self._invalid_request()
        input_value = body.get("input")
        voice_value = body.get("voice")
        audio_value = body.get("audioConfig")
        if (
            not isinstance(input_value, Mapping)
            or set(input_value) != {"text", "prompt"}
            or not isinstance(input_value.get("text"), str)
            or not input_value.get("text")
            or not isinstance(input_value.get("prompt"), str)
            or not input_value.get("prompt")
            or not isinstance(voice_value, Mapping)
            or set(voice_value) != {"languageCode", "modelName", "name"}
            or voice_value.get("languageCode") != "en-IN"
            or voice_value.get("modelName") != "gemini-2.5-pro-tts"
            or voice_value.get("name") not in {"Despina", "Leda", "Achird"}
            or not isinstance(audio_value, Mapping)
            or set(audio_value) != {"audioEncoding", "sampleRateHertz"}
            or audio_value.get("audioEncoding") != "LINEAR16"
            or audio_value.get("sampleRateHertz") != 24_000
        ):
            raise self._invalid_request()
        return self._tts.SynthesizeSpeechRequest(
            input=self._tts.SynthesisInput(
                text=input_value["text"],
                prompt=input_value["prompt"],
            ),
            voice=self._tts.VoiceSelectionParams(
                language_code=voice_value["languageCode"],
                model_name=voice_value["modelName"],
                name=voice_value["name"],
            ),
            audio_config=self._tts.AudioConfig(
                audio_encoding=self._tts.AudioEncoding.LINEAR16,
                sample_rate_hertz=audio_value["sampleRateHertz"],
            ),
        )

    @staticmethod
    def _metadata_values(headers: Mapping[str, str]) -> tuple[str, str]:
        if set(headers) != {"Authorization", "Content-Type", "x-goog-user-project"}:
            raise _OfficialGoogleGrpcBindings._invalid_request()
        authorization = headers.get("Authorization")
        content_type = headers.get("Content-Type")
        quota_project = headers.get("x-goog-user-project")
        if (
            not isinstance(authorization, str)
            or not authorization.startswith("Bearer ")
            or len(authorization) <= len("Bearer ")
            or "\r" in authorization
            or "\n" in authorization
            or content_type != "application/json; charset=utf-8"
            or not isinstance(quota_project, str)
            or not _PROJECT_ID.fullmatch(quota_project)
        ):
            raise _OfficialGoogleGrpcBindings._invalid_request()
        return authorization, quota_project

    @staticmethod
    def _invalid_request() -> GoogleRuntimeError:
        return GoogleRuntimeError(
            "GOOGLE_TTS_REQUEST_INVALID",
            "Google TTS request is invalid.",
            egress_possible=False,
        )

    @staticmethod
    def failure_status(error: Exception) -> str | None:
        code = getattr(error, "code", None)
        if not callable(code):
            return None
        try:
            value = code()
        except Exception:
            return None
        name = getattr(value, "name", None)
        return name if isinstance(name, str) else None

    @staticmethod
    def close(channel: object) -> None:
        close = getattr(channel, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                LOGGER.debug("Google TTS channel close was unsuccessful.")


def _load_official_grpc_bindings() -> _GrpcBindings:
    try:
        grpc_module = importlib.import_module("grpc")
        tts_module = importlib.import_module("google.cloud.texttospeech_v1")
        transport_module = importlib.import_module(
            "google.cloud.texttospeech_v1.services.text_to_speech.transports.grpc"
        )
        transport_type = getattr(transport_module, "TextToSpeechGrpcTransport")
    except (ImportError, AttributeError):
        pass
    else:
        return _OfficialGoogleGrpcBindings(
            grpc_module=grpc_module,
            tts_module=tts_module,
            transport_type=transport_type,
        )
    raise GoogleRuntimeError(
        "GOOGLE_TTS_DEPENDENCY_UNAVAILABLE",
        "Google TTS optional dependency is unavailable.",
    )


class OfficialUnaryGoogleTTSTransport:
    """Explicit official unary gRPC transport with a pinned EU channel target."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        activation_evidence_sha256: str = "",
        resolver: Callable[..., Sequence[tuple[Any, ...]]] = socket.getaddrinfo,
        bindings_factory: Callable[[], _GrpcBindings] = _load_official_grpc_bindings,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        self.enabled = enabled
        self.activation_evidence_sha256 = activation_evidence_sha256
        self._resolver = resolver
        self._bindings_factory = bindings_factory
        self._max_response_bytes = max(1, max_response_bytes)

    def prepare(self, *, url: str, timeout_seconds: float) -> _PreparedGoogleGrpcSession:
        if not self.enabled:
            raise GoogleRuntimeError("GOOGLE_TTS_DISABLED", "Google TTS runtime is disabled.")
        if not _CHECKSUM.fullmatch(self.activation_evidence_sha256):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ACTIVATION_INVALID", "Google TTS activation evidence is invalid."
            )
        RegionalGoogleTTSTransport._parse_url(url)
        if not _valid_timeout(timeout_seconds):
            raise GoogleRuntimeError("GOOGLE_TTS_TIMEOUT_INVALID", "Google TTS timeout is invalid.")
        bindings = self._bindings_factory()
        addresses = self._resolved_addresses()
        peer_ip = addresses[0]
        try:
            connection = bindings.open_client(
                target_ip=peer_ip,
                hostname=_HOSTNAME,
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            pass
        else:
            client, channel = connection
            return _PreparedGoogleGrpcSession(
                bindings=bindings,
                client=client,
                channel=channel,
                resolved_addresses=addresses,
                peer_ip=peer_ip,
                max_response_bytes=self._max_response_bytes,
            )
        raise GoogleRuntimeError(
            "GOOGLE_TTS_CONNECT_FAILED", "Google TTS connection failed before egress."
        )

    def _resolved_addresses(self) -> tuple[str, ...]:
        try:
            answers = list(self._resolver(_HOSTNAME, _PORT, type=socket.SOCK_STREAM))
            addresses = tuple(str(ipaddress.ip_address(str(answer[4][0]))) for answer in answers)
        except Exception:
            pass
        else:
            if not addresses:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_ADDRESS_INVALID", "Google TTS resolved address policy failed."
                )
            for raw in addresses:
                address = ipaddress.ip_address(raw)
                if (
                    not address.is_global
                    or address.is_private
                    or address.is_loopback
                    or address.is_link_local
                    or address.is_multicast
                    or address.is_unspecified
                    or address.is_reserved
                ):
                    raise GoogleRuntimeError(
                        "GOOGLE_TTS_ADDRESS_INVALID",
                        "Google TTS resolved address policy failed.",
                    )
            return addresses
        raise GoogleRuntimeError("GOOGLE_TTS_DNS_FAILED", "Google TTS DNS resolution failed.")


class _PreparedGoogleGrpcSession:
    """Single-use gRPC capability with no automatic retry or fallback."""

    url = GOOGLE_TTS_URL
    proxy_used = False
    tls_verified = True
    tls_server_name = _HOSTNAME
    peer_port = _PORT
    redirects_disabled = True
    dns_pinned = True
    transport_kind = "OFFICIAL_GRPC_UNARY"

    def __init__(
        self,
        *,
        bindings: _GrpcBindings,
        client: object,
        channel: object,
        resolved_addresses: tuple[str, ...],
        peer_ip: str,
        max_response_bytes: int,
    ) -> None:
        self._bindings = bindings
        self._client = client
        self._channel = channel
        self.resolved_addresses = resolved_addresses
        self.peer_ip = peer_ip
        self._max_response_bytes = max_response_bytes
        self._used = False

    def close(self) -> None:
        if self._used:
            return
        self._used = True
        self._bindings.close(self._channel)

    def send(
        self,
        *,
        headers: Mapping[str, str],
        json_body: Mapping[str, object],
        timeout_seconds: float,
    ) -> GoogleTTSHTTPResponse:
        if self._used:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_SESSION_INVALID", "Google TTS prepared session is not reusable."
            )
        if not _valid_timeout(timeout_seconds):
            raise GoogleRuntimeError("GOOGLE_TTS_TIMEOUT_INVALID", "Google TTS timeout is invalid.")
        self._used = True
        try:
            failed = False
            failure_egress_possible = True
            grpc_status: str | None = None
            audio: bytes | None = None
            try:
                audio = self._bindings.synthesize(
                    client=self._client,
                    json_body=json_body,
                    headers=headers,
                    timeout_seconds=timeout_seconds,
                )
            except GoogleRuntimeError as error:
                failed = True
                failure_egress_possible = error.egress_possible
            except Exception as error:
                failed = True
                try:
                    grpc_status = self._bindings.failure_status(error)
                except Exception:
                    grpc_status = None
            if failed:
                sanitized_error = GoogleTransportError(
                    egress_possible=failure_egress_possible,
                    grpc_status=grpc_status,
                )
                del headers, json_body, audio
                raise sanitized_error
            if not audio or len(audio) > self._max_response_bytes:
                sanitized_error = GoogleTransportError(egress_possible=True)
                del headers, json_body, audio
                raise sanitized_error
            body = json.dumps(
                {"audioContent": base64.b64encode(audio).decode("ascii")},
                separators=(",", ":"),
            ).encode("utf-8")
            return GoogleTTSHTTPResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=body,
                final_url=GOOGLE_TTS_URL,
                redirect_count=0,
                peer_ip=self.peer_ip,
                resolved_addresses=self.resolved_addresses,
                proxy_used=False,
                tls_verified=True,
                tls_server_name=_HOSTNAME,
                peer_port=_PORT,
                transport_kind="OFFICIAL_GRPC_UNARY",
            )
        finally:
            self._bindings.close(self._channel)
