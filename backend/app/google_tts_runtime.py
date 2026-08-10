"""Optional, fail-closed Google Gemini-TTS identity and transport runtime.

This module is deliberately separate from the narration-facing provider.  It
does not choose a model, voice, locale, URL, or provider for callers.  The
application keeps the Google provider disabled unless server-owned activation
evidence is supplied by a later authority.
No LLM, script, or citation generation occurs here; caller-owned trace metadata
stays at the provider boundary.
"""

from __future__ import annotations

import hashlib
import importlib
import ipaddress
import json
import logging
import re
import socket
import ssl
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import SplitResult, urlsplit

from backend.app.tts_provider import (
    GOOGLE_TTS_SCOPE,
    GOOGLE_TTS_URL,
    GoogleIdentity,
    GoogleTTSHTTPResponse,
    GoogleTTSPreparedTransport,
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
    quota_project_id: str | None = None
    quota_project_evidence_sha256: str | None = None


class _Credentials(Protocol):
    token: str | None

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
        kwargs: dict[str, object] = {"scopes": [GOOGLE_TTS_SCOPE]}
        if self.config.quota_project_id is not None:
            kwargs["quota_project_id"] = self.config.quota_project_id
        try:
            credentials, project_id = loader(**kwargs)
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ADC_UNAVAILABLE", "Google TTS ADC identity is unavailable."
            ) from None
        configured_quota = self.config.quota_project_id
        credential_quota = getattr(credentials, "quota_project_id", None)
        if configured_quota and credential_quota not in (None, configured_quota):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_QUOTA_PROJECT_MISMATCH",
                "Google TTS quota-project evidence is invalid.",
            )
        request_factory = self._request_factory or self._load_request_factory()
        try:
            credentials.refresh(request_factory())
        except Exception:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_REFRESH_FAILED", "Google TTS ADC refresh was unsuccessful."
            ) from None
        access_value = getattr(credentials, "token", None)
        if not isinstance(access_value, str) or not access_value or "\r" in access_value or "\n" in access_value:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_TOKEN_INVALID", "Google TTS ADC returned an invalid token."
            )
        evidence = {
            "credentialType": type(credentials).__name__,
            "projectIdPresent": bool(project_id),
            "quotaProjectId": configured_quota,
            "scope": GOOGLE_TTS_SCOPE,
        }
        identity_checksum = "sha256:" + hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return GoogleIdentity(access_token=access_value, identity_evidence_sha256=identity_checksum)

    def _validate_preconditions(self, scope: str) -> None:
        if not self.config.enabled:
            raise GoogleRuntimeError("GOOGLE_TTS_DISABLED", "Google TTS runtime is disabled.")
        if scope != GOOGLE_TTS_SCOPE:
            raise GoogleRuntimeError("GOOGLE_TTS_SCOPE_INVALID", "Google TTS scope is invalid.")
        if not _CHECKSUM.fullmatch(self.config.activation_evidence_sha256):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_ACTIVATION_INVALID", "Google TTS activation evidence is invalid."
            )
        if self.config.quota_project_id is not None:
            if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", self.config.quota_project_id):
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_QUOTA_PROJECT_INVALID",
                    "Google TTS quota-project evidence is invalid.",
                )
            if not _CHECKSUM.fullmatch(self.config.quota_project_evidence_sha256 or ""):
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_QUOTA_PROJECT_INVALID",
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
            module = importlib.import_module("google.auth.transport._http_client")
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

    def prepare(self, *, url: str, timeout_seconds: float) -> GoogleTTSPreparedTransport:
        self._validate_activation()
        parsed = self._parse_url(url)
        if timeout_seconds <= 0 or timeout_seconds > 30:
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
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise GoogleRuntimeError("GOOGLE_TTS_TIMEOUT_INVALID", "Google TTS timeout is invalid.")
        self._used = True
        payload = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request_headers = {"Host": _HOSTNAME, "Content-Length": str(len(payload)), "Connection": "close"}
        for name, value in headers.items():
            if name.lower() in {"host", "content-length", "connection"}:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_HEADER_INVALID", "Google TTS request headers are invalid.", egress_possible=False
                )
            if not isinstance(name, str) or not isinstance(value, str) or "\r" in value or "\n" in value:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_HEADER_INVALID", "Google TTS request headers are invalid."
                )
            request_headers[name] = value
        wire = (
            f"POST {_PATH} HTTP/1.1\r\n"
            + "".join(f"{name}: {value}\r\n" for name, value in request_headers.items())
            + "\r\n"
        ).encode("ascii") + payload
        sent = 0
        try:
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
            try:
                self._sock.close()
            except OSError:
                pass

    def _read_response(self) -> GoogleTTSHTTPResponse:
        header_bytes = bytearray()
        while b"\r\n\r\n" not in header_bytes:
            if len(header_bytes) >= _MAX_HEADER_BYTES:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response headers are invalid.", egress_possible=True
                )
            chunk = self._sock.recv(min(_READ_CHUNK_BYTES, _MAX_HEADER_BYTES - len(header_bytes)))
            if not chunk:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response headers are invalid.", egress_possible=True
                )
            header_bytes.extend(chunk)
        raw_headers, body_prefix = bytes(header_bytes).split(b"\r\n\r\n", 1)
        lines = raw_headers.split(b"\r\n")
        if not lines or not lines[0].startswith(b"HTTP/1.1 "):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response is malformed.", egress_possible=True
            )
        try:
            status = int(lines[0].split(b" ", 2)[1])
            response_headers: dict[str, str] = {}
            for line in lines[1:]:
                name, value = line.split(b":", 1)
                response_headers[name.decode("ascii").lower()] = value.decode("latin-1").strip()
        except (IndexError, ValueError, UnicodeDecodeError):
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response is malformed.", egress_possible=True
            ) from None
        if 300 <= status < 400:
            raise GoogleRuntimeError(
                "GOOGLE_TTS_REDIRECT_REJECTED", "Google TTS redirects are disabled.", egress_possible=True
            )
        transfer_encoding = response_headers.get("transfer-encoding", "").lower()
        if transfer_encoding and transfer_encoding != "identity":
            raise GoogleRuntimeError(
                "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response framing is unsupported.", egress_possible=True
            )
        content_length = response_headers.get("content-length")
        if content_length is not None:
            try:
                expected = int(content_length)
            except ValueError:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response length is invalid.", egress_possible=True
                ) from None
            if expected < 0 or expected > self._max_response_bytes:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_TOO_LARGE", "Google TTS response exceeds its byte limit.", egress_possible=True
                )
            body = bytearray(body_prefix[:expected])
            while len(body) < expected:
                chunk = self._sock.recv(min(_READ_CHUNK_BYTES, expected - len(body)))
                if not chunk:
                    raise GoogleRuntimeError(
                        "GOOGLE_TTS_RESPONSE_INVALID", "Google TTS response body is incomplete.", egress_possible=True
                    )
                body.extend(chunk)
        else:
            body = bytearray(body_prefix)
            if len(body) > self._max_response_bytes:
                raise GoogleRuntimeError(
                    "GOOGLE_TTS_RESPONSE_TOO_LARGE", "Google TTS response exceeds its byte limit.", egress_possible=True
                )
            while True:
                chunk = self._sock.recv(_READ_CHUNK_BYTES)
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > self._max_response_bytes:
                    raise GoogleRuntimeError(
                        "GOOGLE_TTS_RESPONSE_TOO_LARGE", "Google TTS response exceeds its byte limit.", egress_possible=True
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
