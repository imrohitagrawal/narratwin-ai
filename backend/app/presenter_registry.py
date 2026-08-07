"""Fail-closed provider-neutral presenter registry for the controlled-local Cut 1."""
from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, NoReturn, cast


MAX_REGISTRY_BYTES, MAX_ASSET_BYTES = 65_536, 500_000
REGISTRY_SCHEMA_VERSION = "cut1-presenter-registry-v1"
PRODUCTION_IDS = frozenset({"meera", "myra", "raj"})
TEST_PERSONAL_ID = "future-personal-test"
VERSION_PATTERN = re.compile(r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$")
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
TRACE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_PRODUCTION_SHA256 = "14838d74e2ff35ca4af5336d937eb206ec77a8351ba6b7cd86bfdc6929913855"
CANONICAL_ASSETS = {
    "meera": ("frontend/public/demo/narratwin-synthetic-presenter.webp",
              "d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1"),
    "myra": ("frontend/public/demo/myra-synthetic-presenter.webp",
             "30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97"),
    "raj": ("frontend/public/demo/raj-synthetic-presenter.webp",
            "663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd"),
}
REQUIRED_PERSONA_ANCHORS = {
    "meera": {"royal-blue saree", "gold jewelry"},
    "myra": {"Indian identity", "long open naturally black hair below shoulders",
              "deep-red or deep-maroon Indian saree", "refined gold-zari border",
              "coordinated premium necklace and earrings"},
    "raj": {"Indian identity", "tall slim fit build",
            "exceptionally handsome smart charismatic presence",
            "dark non-gray well-groomed hair", "tailored dark Indian formal jacket"},
}

class PresenterRegistryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PresenterLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    DELETED = "DELETED"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class PersonaMetadata:
    apparent_age: str
    summary: str
    visual_anchors: tuple[str, ...]


@dataclass(frozen=True)
class AssetMetadata:
    path: str
    sha256: str
    width: int
    height: int
    media_type: str
    provenance_ref: str


@dataclass(frozen=True)
class VoiceReference:
    reference_id: str
    version: str
    kind: str
    cloned: bool
    provider: str | None
    description: str


@dataclass(frozen=True)
class DisclosureMetadata:
    ai_generated: bool
    fictional: bool
    cloned_identity: bool
    text: str


@dataclass(frozen=True)
class PermissionMetadata:
    consent_basis: str
    permitted_use: str
    publication_allowed: bool
    provenance_review: str


@dataclass(frozen=True)
class RendererNeutralSettings:
    schema_version: str
    provider: str | None
    framing: str
    eye_level: bool
    mouth_and_jaw_unobstructed: bool


@dataclass(frozen=True)
class PresenterIdentity:
    id: str
    display_name: str
    version: str
    identity_kind: str
    lifecycle: PresenterLifecycle
    test_only: bool
    persona: PersonaMetadata
    asset: AssetMetadata | None
    voice: VoiceReference
    disclosure: DisclosureMetadata
    permission: PermissionMetadata
    renderer: RendererNeutralSettings


@dataclass(frozen=True)
class PresenterTraceBinding:
    presenter_id: str
    presenter_version: str
    trace_id: str
    asset_sha256: str
    voice_reference_id: str
    voice_reference_version: str
    registry_version: str
    registry_sha256: str
    binding_sha256: str


class _DuplicateKey(ValueError):
    pass


def _fail(code: str, message: str) -> NoReturn:
    raise PresenterRegistryError(code, message)


def _object(value: Any, keys: set[str], code: str = "REGISTRY_SCHEMA") -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        _fail(code, "Registry object fields are missing or unknown.")
    return cast(dict[str, Any], value)


def _text(value: Any, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _fail("REGISTRY_SCHEMA", "Registry text is empty or non-canonical.")
    if pattern is not None and pattern.match(value) is None:
        _fail("REGISTRY_SCHEMA", "Registry text does not match its required format.")
    return value


def _flag(value: Any) -> bool:
    if not isinstance(value, bool):
        _fail("REGISTRY_SCHEMA", "Registry boolean has the wrong type.")
    return value


def _integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _fail("REGISTRY_SCHEMA", "Registry integer must be positive.")
    return value


def _optional_text(value: Any) -> str | None:
    return None if value is None else _text(value)


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _persona(value: Any, presenter_id: str) -> PersonaMetadata:
    row = _object(value, {"apparent_age", "summary", "visual_anchors"})
    anchors_value = row["visual_anchors"]
    if not isinstance(anchors_value, list) or not anchors_value:
        _fail("PERSONA_CONTRACT", "Persona anchors are missing.")
    anchors = tuple(_text(item) for item in anchors_value)
    if len(set(anchors)) != len(anchors):
        _fail("PERSONA_CONTRACT", "Persona anchors must be unique.")
    if presenter_id in REQUIRED_PERSONA_ANCHORS and not REQUIRED_PERSONA_ANCHORS[
        presenter_id
    ].issubset(anchors):
        _fail("PERSONA_CONTRACT", "Owner-approved persona anchors drifted.")
    age = _text(row["apparent_age"])
    if presenter_id in {"myra", "raj"} and age != "24-28":
        _fail("PERSONA_CONTRACT", "Selected presenter apparent age drifted.")
    return PersonaMetadata(age, _text(row["summary"]), anchors)


def _asset(value: Any, presenter_id: str, *, test_only: bool) -> AssetMetadata | None:
    if value is None:
        if test_only and presenter_id == TEST_PERSONAL_ID:
            return None
        _fail("ASSET_METADATA", "Active presenter asset metadata is missing.")
    row = _object(value, {"path", "sha256", "width", "height", "media_type", "provenance_ref"})
    path = _text(row["path"])
    if presenter_id not in CANONICAL_ASSETS or path != CANONICAL_ASSETS[presenter_id][0]:
        _fail("ASSET_PATH", "Presenter asset path is not canonical.")
    if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path:
        _fail("ASSET_PATH", "Presenter asset path escapes the repository.")
    digest = _text(row["sha256"], pattern=SHA256_PATTERN)
    if digest != CANONICAL_ASSETS[presenter_id][1]:
        _fail("ASSET_CHECKSUM", "Presenter asset checksum metadata drifted.")
    width, height = _integer(row["width"]), _integer(row["height"])
    media_type = _text(row["media_type"])
    if (width, height, media_type) != (1536, 1024, "image/webp"):
        _fail("ASSET_METADATA", "Presenter asset media metadata drifted.")
    provenance_ref = _text(row["provenance_ref"])
    if not provenance_ref.startswith("docs/THIRD_PARTY_NOTICES.md#"):
        _fail("ASSET_METADATA", "Presenter provenance reference is not governed.")
    return AssetMetadata(path, digest, width, height, media_type, provenance_ref)


def _voice(value: Any) -> VoiceReference:
    row = _object(value, {"reference_id", "version", "kind", "cloned", "provider", "description"})
    voice = VoiceReference(
        _text(row["reference_id"], pattern=IDENTIFIER_PATTERN),
        _text(row["version"], pattern=VERSION_PATTERN),
        _text(row["kind"]),
        _flag(row["cloned"]),
        _optional_text(row["provider"]),
        _text(row["description"]),
    )
    if voice.kind != "SYNTHETIC_NON_CLONED" or voice.cloned or voice.provider is not None:
        _fail("VOICE_REFERENCE", "Voice reference is cloned or provider-specific.")
    return voice


def _identity(value: Any) -> PresenterIdentity:
    row = _object(value, {"id", "display_name", "version", "identity_kind", "lifecycle",
                          "test_only", "persona", "asset", "voice", "disclosure",
                          "permission", "renderer"})
    presenter_id = _text(row["id"], pattern=IDENTIFIER_PATTERN)
    test_only = _flag(row["test_only"])
    try:
        lifecycle = PresenterLifecycle(_text(row["lifecycle"]))
    except ValueError:
        _fail("REGISTRY_SCHEMA", "Presenter lifecycle is unknown.")
    identity_kind = _text(row["identity_kind"])
    if presenter_id in PRODUCTION_IDS:
        if identity_kind != "SYNTHETIC" or test_only or lifecycle is not PresenterLifecycle.ACTIVE:
            _fail("REGISTRY_SCHEMA", "Production presenter posture drifted.")
    elif presenter_id != TEST_PERSONAL_ID:
        _fail("REGISTRY_ID_SET", "Only the three production identities are registered.")
    elif not (identity_kind == "PERSONAL" and test_only
              and lifecycle is PresenterLifecycle.DISABLED):
        _fail("TEST_ONLY", "Only the disabled future-personal test fixture is permitted.")
    disclosure_row = _object(row["disclosure"],
                             {"ai_generated", "fictional", "cloned_identity", "text"})
    disclosure = DisclosureMetadata(
        _flag(disclosure_row["ai_generated"]), _flag(disclosure_row["fictional"]),
        _flag(disclosure_row["cloned_identity"]), _text(disclosure_row["text"]),
    )
    if not disclosure.ai_generated or not disclosure.fictional or disclosure.cloned_identity \
            or "synthetic" not in disclosure.text.lower():
        _fail("REGISTRY_SCHEMA", "Synthetic disclosure is incomplete.")
    permission_row = _object(row["permission"], {"consent_basis", "permitted_use",
                                                  "publication_allowed", "provenance_review"})
    permission = PermissionMetadata(
        _text(permission_row["consent_basis"]), _text(permission_row["permitted_use"]),
        _flag(permission_row["publication_allowed"]), _text(permission_row["provenance_review"]),
    )
    if permission.consent_basis != "PROJECT_OWNED_SYNTHETIC_IDENTITY" \
            or permission.permitted_use != "CONTROLLED_LOCAL_CUT1" \
            or permission.publication_allowed:
        _fail("REGISTRY_SCHEMA", "Permission boundary is incomplete.")
    renderer_row = _object(row["renderer"], {"schema_version", "provider", "framing",
                                             "eye_level", "mouth_and_jaw_unobstructed"})
    renderer = RendererNeutralSettings(
        _text(renderer_row["schema_version"]), _optional_text(renderer_row["provider"]),
        _text(renderer_row["framing"]), _flag(renderer_row["eye_level"]),
        _flag(renderer_row["mouth_and_jaw_unobstructed"]),
    )
    if renderer != RendererNeutralSettings("renderer-neutral-v1", None,
                                           "HEAD_SHOULDERS_UPPER_TORSO", True, True):
        _fail("RENDERER_SETTINGS", "Renderer settings are not provider-neutral.")
    return PresenterIdentity(
        presenter_id, _text(row["display_name"]), _text(row["version"], pattern=VERSION_PATTERN),
        identity_kind, lifecycle, test_only, _persona(row["persona"], presenter_id),
        _asset(row["asset"], presenter_id, test_only=test_only), _voice(row["voice"]),
        disclosure, permission, renderer,
    )


def _probe_webp(data: bytes) -> tuple[int, int]:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP" \
            or int.from_bytes(data[4:8], "little") + 8 != len(data):
        _fail("ASSET_METADATA", "Presenter asset is not an exact WebP container.")
    offset = 12
    dimensions: tuple[int, int] | None = None
    while offset < len(data):
        if offset + 8 > len(data):
            _fail("ASSET_METADATA", "Presenter WebP chunk header is truncated.")
        kind = data[offset:offset + 4]
        size = int.from_bytes(data[offset + 4:offset + 8], "little")
        start, end = offset + 8, offset + 8 + size
        if end > len(data):
            _fail("ASSET_METADATA", "Presenter WebP chunk is truncated.")
        payload = data[start:end]
        if dimensions is None and kind == b"VP8 " and len(payload) >= 10 \
                and payload[3:6] == b"\x9d\x01\x2a":
            dimensions = (int.from_bytes(payload[6:8], "little") & 0x3FFF,
                          int.from_bytes(payload[8:10], "little") & 0x3FFF)
        offset = end + size % 2
    if offset != len(data) or dimensions is None:
        _fail("ASSET_METADATA", "Presenter WebP image payload is malformed.")
    return dimensions


def _validate_asset(identity: PresenterIdentity, asset_root: Path) -> None:
    if identity.asset is None:
        _fail("PRESENTER_INACTIVE", "Test-only presenter has no selectable asset.")
    asset = identity.asset
    root, candidate = asset_root.resolve(), asset_root / asset.path
    if not candidate.exists():
        _fail("ASSET_MISSING", "Presenter asset is missing.")
    if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root):
        _fail("ASSET_UNSAFE", "Presenter asset must be a repository-contained regular file.")
    with candidate.open("rb") as stream:
        data = stream.read(MAX_ASSET_BYTES + 1)
    if not 0 < len(data) <= MAX_ASSET_BYTES:
        _fail("ASSET_METADATA", "Presenter asset size is outside the controlled bound.")
    if hashlib.sha256(data).hexdigest() != asset.sha256:
        _fail("ASSET_CHECKSUM", "Presenter asset bytes do not match the registry.")
    if _probe_webp(data) != (asset.width, asset.height):
        _fail("ASSET_METADATA", "Presenter asset dimensions do not match the registry.")


def _identity_payload(identity: PresenterIdentity) -> dict[str, Any]:
    payload = asdict(identity)
    payload["lifecycle"] = identity.lifecycle.value
    return payload


def _sha256_json(value: Mapping[str, Any]) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(serialized).hexdigest()


class PresenterRegistry:
    def __init__(self, registry_version: str, identities: Mapping[str, PresenterIdentity],
                 *, asset_root: Path) -> None:
        self.registry_version = registry_version
        self._identities = dict(identities)
        self._asset_root = asset_root
        self._issued_bindings: dict[str, str] = {}
        self._lock = threading.Lock()
        for identity in self._identities.values():
            if not identity.test_only:
                _validate_asset(identity, asset_root)

    @property
    def identities(self) -> Mapping[str, PresenterIdentity]:
        return MappingProxyType(self._identities)

    @property
    def serialized_manifest(self) -> str:
        payload = {"schema_version": REGISTRY_SCHEMA_VERSION,
                   "registry_version": self.registry_version,
                   "presenters": [_identity_payload(self._identities[key])
                                  for key in sorted(self._identities)]}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def manifest_sha256(self) -> str:
        return hashlib.sha256(self.serialized_manifest.encode("utf-8")).hexdigest()

    def get(self, presenter_id: str, presenter_version: str) -> PresenterIdentity:
        identity = self._identities.get(presenter_id)
        if identity is None:
            _fail("PRESENTER_NOT_FOUND", "Presenter identity is not registered.")
        if identity.version != presenter_version:
            _fail("PRESENTER_STALE", "Presenter version is stale or unknown.")
        if identity.lifecycle is not PresenterLifecycle.ACTIVE or identity.test_only:
            _fail("PRESENTER_INACTIVE", "Presenter identity is not active.")
        _validate_asset(identity, self._asset_root)
        return identity

    def transition(self, presenter_id: str, target: PresenterLifecycle) -> None:
        with self._lock:
            identity = self._identities.get(presenter_id)
            if identity is None:
                _fail("PRESENTER_NOT_FOUND", "Presenter identity is not registered.")
            allowed = ((identity.lifecycle is PresenterLifecycle.ACTIVE
                        and target in {PresenterLifecycle.REVOKED, PresenterLifecycle.DELETED})
                       or (identity.lifecycle is PresenterLifecycle.REVOKED
                           and target is PresenterLifecycle.DELETED))
            if not allowed:
                _fail("LIFECYCLE_INVALID", "Presenter lifecycle cannot move backward or resurrect.")
            self._identities[presenter_id] = replace(identity, lifecycle=target)

    def bind_for_trace(self, *, presenter_id: str, presenter_version: str, trace_id: str,
                       asset_sha256: str, voice_reference_id: str,
                       voice_reference_version: str) -> PresenterTraceBinding:
        if TRACE_PATTERN.match(trace_id) is None:
            _fail("TRACE_INVALID", "Trace identifier is empty, malformed, or oversized.")
        with self._lock:
            if trace_id in self._issued_bindings:
                _fail("TRACE_REPLAY", "Trace identifier has already selected a presenter.")
            identity = self.get(presenter_id, presenter_version)
            if (asset_sha256, voice_reference_id, voice_reference_version) != (
                cast(AssetMetadata, identity.asset).sha256,
                identity.voice.reference_id,
                identity.voice.version,
            ):
                _fail("BINDING_MISMATCH", "Caller presenter binding does not match the registry.")
            values = {
                "presenter_id": presenter_id, "presenter_version": presenter_version,
                "trace_id": trace_id, "asset_sha256": asset_sha256,
                "voice_reference_id": voice_reference_id,
                "voice_reference_version": voice_reference_version,
                "registry_version": self.registry_version,
                "registry_sha256": self.manifest_sha256,
            }
            binding = PresenterTraceBinding(**values, binding_sha256=_sha256_json(values))
            self._issued_bindings[trace_id] = binding.binding_sha256
            return binding

    def verify_binding(self, binding: PresenterTraceBinding) -> None:
        patterns = ((binding.presenter_id, IDENTIFIER_PATTERN), (binding.presenter_version, VERSION_PATTERN),
                    (binding.trace_id, TRACE_PATTERN), (binding.asset_sha256, SHA256_PATTERN), (binding.voice_reference_id, IDENTIFIER_PATTERN),
                    (binding.voice_reference_version, VERSION_PATTERN), (binding.registry_version, VERSION_PATTERN),
                    (binding.registry_sha256, SHA256_PATTERN), (binding.binding_sha256, SHA256_PATTERN),
        ) if isinstance(binding, PresenterTraceBinding) else ()
        if not patterns or any(not isinstance(value, str) or pattern.fullmatch(value) is None
                               for value, pattern in patterns):
            _fail("BINDING_MISMATCH", "Presenter trace binding is malformed.")
        try:
            identity = self.get(binding.presenter_id, binding.presenter_version)
        except PresenterRegistryError:
            _fail("BINDING_MISMATCH", "Binding presenter is no longer valid.")
        asset = cast(AssetMetadata, identity.asset)
        values = {"presenter_id": binding.presenter_id, "presenter_version": binding.presenter_version,
                  "trace_id": binding.trace_id, "asset_sha256": binding.asset_sha256,
                  "voice_reference_id": binding.voice_reference_id, "voice_reference_version": binding.voice_reference_version,
                  "registry_version": binding.registry_version, "registry_sha256": binding.registry_sha256}
        if (self._issued_bindings.get(binding.trace_id) != binding.binding_sha256
                or binding.asset_sha256 != asset.sha256
                or binding.voice_reference_id != identity.voice.reference_id
                or binding.voice_reference_version != identity.voice.version
                or binding.registry_version != self.registry_version
                or binding.registry_sha256 != self.manifest_sha256
                or binding.binding_sha256 != _sha256_json(values)):
            _fail("BINDING_MISMATCH", "Presenter trace binding is stale or mismatched.")


def load_presenter_registry(path: Path, *, asset_root: Path,
                            allow_test_fixtures: bool = False) -> PresenterRegistry:
    if path.is_symlink() or not path.is_file():
        _fail("REGISTRY_MALFORMED", "Presenter registry must be a regular file.")
    with path.open("rb") as stream:
        data = stream.read(MAX_REGISTRY_BYTES + 1)
    if len(data) > MAX_REGISTRY_BYTES:
        _fail("REGISTRY_TOO_LARGE", "Presenter registry exceeds its byte limit.")
    try:
        payload = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKey):
        _fail("REGISTRY_MALFORMED", "Presenter registry JSON is malformed.")
    root = _object(payload, {"schema_version", "registry_version", "presenters"})
    if root["schema_version"] != REGISTRY_SCHEMA_VERSION or root["registry_version"] != "1.0.0":
        _fail("REGISTRY_SCHEMA", "Presenter registry schema or version is unknown.")
    registry_version = _text(root["registry_version"], pattern=VERSION_PATTERN)
    rows = root["presenters"]
    if not isinstance(rows, list):
        _fail("REGISTRY_SCHEMA", "Presenter registry rows must be a list.")
    parsed = [_identity(row) for row in rows]
    identities = {identity.id: identity for identity in parsed}
    ids = set(identities)
    if len(identities) != len(parsed):
        _fail("REGISTRY_ID_SET", "Presenter identities must be unique.")
    if ids == PRODUCTION_IDS | {TEST_PERSONAL_ID} and not allow_test_fixtures:
        _fail("TEST_ONLY", "Future personal identity shape is test-only.")
    expected = PRODUCTION_IDS | ({TEST_PERSONAL_ID} if allow_test_fixtures else set())
    if ids != expected:
        _fail("REGISTRY_ID_SET", "Active registry identity set is not exact.")
    voice_ids = [identities[key].voice.reference_id for key in sorted(PRODUCTION_IDS)]
    if len(set(voice_ids)) != len(voice_ids):
        _fail("VOICE_REFERENCE", "Production voice references must be distinct.")
    canonical = {item.id: row for item, row in zip(parsed, rows, strict=True)
                 if item.id in PRODUCTION_IDS}
    if _sha256_json(canonical) != CANONICAL_PRODUCTION_SHA256:
        _fail("CANONICAL_REGISTRY", "Owner-approved production registry fields drifted.")
    return PresenterRegistry(registry_version, identities, asset_root=asset_root)


def load_cut1_presenter_registry(*, asset_root: Path | None = None) -> PresenterRegistry:
    repository_root = Path(__file__).resolve().parents[2]
    return load_presenter_registry(Path(__file__).with_name("presenter_registry.json"),
                                   asset_root=asset_root or repository_root)
