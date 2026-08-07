from __future__ import annotations

import copy
import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, cast

import pytest

from backend.app.presenter_registry import (
    PresenterLifecycle,
    PresenterRegistry,
    PresenterRegistryError,
    load_cut1_presenter_registry,
    load_presenter_registry,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "backend/app/presenter_registry.json"
ASSET_ROOT = ROOT
EXPECTED_ASSETS = {
    "meera": (
        "frontend/public/demo/narratwin-synthetic-presenter.webp",
        "d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1",
    ),
    "myra": (
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97",
    ),
    "raj": (
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd",
    ),
}


def _payload() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _load_payload(
    tmp_path: Path,
    payload: dict[str, Any],
    *,
    asset_root: Path = ASSET_ROOT,
    allow_test_fixtures: bool = False,
) -> PresenterRegistry:
    return load_presenter_registry(
        _write_payload(tmp_path, payload),
        asset_root=asset_root,
        allow_test_fixtures=allow_test_fixtures,
    )


def _presenter(payload: dict[str, Any], presenter_id: str) -> dict[str, Any]:
    return next(row for row in payload["presenters"] if row["id"] == presenter_id)


def _assert_code(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(PresenterRegistryError) as caught:
        operation()
    assert caught.value.code == code


def test_registry_binds_exact_active_cut1_identities_and_assets() -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    assert registry.registry_version == "1.0.0"
    assert set(registry.identities) == {"meera", "myra", "raj"}
    assert len(registry.manifest_sha256) == 64
    for presenter_id, (path, digest) in EXPECTED_ASSETS.items():
        identity = registry.get(presenter_id, "1.0.0")
        assert identity.display_name == presenter_id.title()
        assert identity.identity_kind == "SYNTHETIC"
        assert identity.lifecycle is PresenterLifecycle.ACTIVE
        assert identity.test_only is False
        assert identity.asset is not None
        asset = identity.asset
        assert asset.path == path
        assert asset.sha256 == digest
        assert asset.media_type == "image/webp"
        assert (asset.width, asset.height) == (1536, 1024)
        assert asset.provenance_ref.startswith("docs/THIRD_PARTY_NOTICES.md#")
        assert hashlib.sha256((ASSET_ROOT / path).read_bytes()).hexdigest() == digest


def test_registry_preserves_disclosure_permission_voice_and_renderer_boundaries() -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    voice_ids: set[str] = set()
    for identity in registry.identities.values():
        assert identity.disclosure.ai_generated is True
        assert identity.disclosure.fictional is True
        assert identity.disclosure.cloned_identity is False
        assert "synthetic" in identity.disclosure.text.lower()
        assert identity.permission.consent_basis == "PROJECT_OWNED_SYNTHETIC_IDENTITY"
        assert identity.permission.permitted_use == "CONTROLLED_LOCAL_CUT1"
        assert identity.permission.publication_allowed is False
        assert identity.voice.kind == "SYNTHETIC_NON_CLONED"
        assert identity.voice.cloned is False
        assert identity.voice.provider is None
        assert identity.voice.reference_id not in voice_ids
        voice_ids.add(identity.voice.reference_id)
        assert identity.renderer.schema_version == "renderer-neutral-v1"
        assert identity.renderer.provider is None
        assert identity.renderer.mouth_and_jaw_unobstructed is True


def test_registry_preserves_owner_approved_persona_anchors() -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    meera = registry.get("meera", "1.0.0")
    myra = registry.get("myra", "1.0.0")
    raj = registry.get("raj", "1.0.0")
    assert {"royal-blue saree", "gold jewelry"} <= set(meera.persona.visual_anchors)
    assert myra.persona.apparent_age == "24-28"
    assert {
        "Indian identity",
        "long open naturally black hair below shoulders",
        "deep-red or deep-maroon Indian saree",
        "refined gold-zari border",
        "coordinated premium necklace and earrings",
    } <= set(myra.persona.visual_anchors)
    assert raj.persona.apparent_age == "24-28"
    assert {
        "Indian identity",
        "tall slim fit build",
        "exceptionally handsome smart charismatic presence",
        "dark non-gray well-groomed hair",
        "tailored dark Indian formal jacket",
    } <= set(raj.persona.visual_anchors)
    assert "Aashna" not in registry.serialized_manifest
    assert "Veer" not in registry.serialized_manifest


def test_trace_binding_recomputes_every_identity_component_and_rejects_replay() -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    myra = registry.get("myra", "1.0.0")
    assert myra.asset is not None
    myra_asset_sha256 = myra.asset.sha256
    binding = registry.bind_for_trace(
        presenter_id="myra",
        presenter_version="1.0.0",
        trace_id="trace_cut1_myra_001",
        asset_sha256=myra_asset_sha256,
        voice_reference_id=myra.voice.reference_id,
        voice_reference_version=myra.voice.version,
    )
    registry.verify_binding(binding)
    for field, value in (
        ("presenter_id", "raj"),
        ("presenter_version", "9.9.9"),
        ("asset_sha256", "0" * 64),
        ("voice_reference_id", "foreign-voice"),
        ("voice_reference_version", "9.9.9"),
        ("registry_sha256", "f" * 64),
        ("binding_sha256", "e" * 64),
    ):
        _assert_code(
            "BINDING_MISMATCH",
            lambda: registry.verify_binding(
                cast(Any, replace)(binding, **{field: value})
            ),
        )
    _assert_code(
        "TRACE_REPLAY",
        lambda: registry.bind_for_trace(
            presenter_id="myra",
            presenter_version="1.0.0",
            trace_id=binding.trace_id,
            asset_sha256=myra_asset_sha256,
            voice_reference_id=myra.voice.reference_id,
            voice_reference_version=myra.voice.version,
        ),
    )


@pytest.mark.parametrize("trace_id", ["", " ", "../trace", "trace\nvalue", "x" * 129])
def test_trace_binding_rejects_malformed_trace_ids(trace_id: str) -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    meera = registry.get("meera", "1.0.0")
    assert meera.asset is not None
    meera_asset_sha256 = meera.asset.sha256
    _assert_code(
        "TRACE_INVALID",
        lambda: registry.bind_for_trace(
            presenter_id="meera",
            presenter_version="1.0.0",
            trace_id=trace_id,
            asset_sha256=meera_asset_sha256,
            voice_reference_id=meera.voice.reference_id,
            voice_reference_version=meera.voice.version,
        ),
    )


def test_missing_stale_revoked_deleted_and_disabled_identities_fail_closed() -> None:
    registry = load_cut1_presenter_registry(asset_root=ASSET_ROOT)
    _assert_code("PRESENTER_NOT_FOUND", lambda: registry.get("missing", "1.0.0"))
    _assert_code("PRESENTER_STALE", lambda: registry.get("meera", "0.9.0"))
    myra = registry.get("myra", "1.0.0")
    assert myra.asset is not None
    binding = registry.bind_for_trace(
        presenter_id="myra",
        presenter_version="1.0.0",
        trace_id="trace_before_revocation",
        asset_sha256=myra.asset.sha256,
        voice_reference_id=myra.voice.reference_id,
        voice_reference_version=myra.voice.version,
    )
    registry.transition("myra", PresenterLifecycle.REVOKED)
    _assert_code("PRESENTER_INACTIVE", lambda: registry.get("myra", "1.0.0"))
    _assert_code("BINDING_MISMATCH", lambda: registry.verify_binding(binding))
    registry.transition("myra", PresenterLifecycle.DELETED)
    _assert_code("PRESENTER_INACTIVE", lambda: registry.get("myra", "1.0.0"))
    _assert_code(
        "LIFECYCLE_INVALID",
        lambda: registry.transition("myra", PresenterLifecycle.ACTIVE),
    )


@pytest.mark.parametrize(
    ("mutation", "code"),
    (
        (lambda data: data.update({"unknown": True}), "REGISTRY_SCHEMA"),
        (lambda data: data.update({"schema_version": "future"}), "REGISTRY_SCHEMA"),
        (lambda data: data.update({"registry_version": "9.9.9"}), "REGISTRY_SCHEMA"),
        (lambda data: data["presenters"].pop(), "REGISTRY_ID_SET"),
        (
            lambda data: data["presenters"].append(copy.deepcopy(data["presenters"][0])),
            "REGISTRY_ID_SET",
        ),
        (lambda data: _presenter(data, "meera").update({"version": "bad"}), "REGISTRY_SCHEMA"),
        (
            lambda data: _presenter(data, "meera")["asset"].update({"path": "../escape.webp"}),
            "ASSET_PATH",
        ),
        (
            lambda data: _presenter(data, "meera")["asset"].update({"sha256": "0" * 64}),
            "ASSET_CHECKSUM",
        ),
        (
            lambda data: _presenter(data, "myra")["asset"].update({"width": 1}),
            "ASSET_METADATA",
        ),
        (
            lambda data: _presenter(data, "raj")["voice"].update({"cloned": True}),
            "VOICE_REFERENCE",
        ),
        (
            lambda data: _presenter(data, "raj")["renderer"].update({"provider": "vendor"}),
            "RENDERER_SETTINGS",
        ),
        (
            lambda data: _presenter(data, "myra").update({"unknown": "field"}),
            "REGISTRY_SCHEMA",
        ),
    ),
)
def test_registry_metadata_mutations_fail_closed(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None], code: str
) -> None:
    payload = _payload()
    mutation(payload)
    _assert_code(code, lambda: _load_payload(tmp_path, payload))


@pytest.mark.parametrize(
    "mutation",
    (
        lambda data: _presenter(data, "meera").update({"display_name": "Mira"}),
        lambda data: _presenter(data, "myra")["persona"].update(
            {"summary": "Contradictory replacement persona."}
        ),
        lambda data: _presenter(data, "raj")["persona"]["visual_anchors"].append(
            "older salt-and-pepper casual executive"
        ),
        lambda data: _presenter(data, "raj")["voice"].update(
            {"reference_id": "cut1-raj-replacement-voice"}
        ),
        lambda data: _presenter(data, "raj")["voice"].update(
            {"reference_id": _presenter(data, "myra")["voice"]["reference_id"]}
        ),
        lambda data: _presenter(data, "myra")["voice"].update(
            {"description": "Different voice direction."}
        ),
        lambda data: _presenter(data, "myra")["asset"].update(
            {"provenance_ref": "docs/THIRD_PARTY_NOTICES.md#replacement"}
        ),
        lambda data: _presenter(data, "raj")["permission"].update(
            {"provenance_review": "Untrusted replacement authority"}
        ),
        lambda data: _presenter(data, "myra").update({"display_name": "Myra A"}),
        lambda data: _presenter(data, "raj").update({"display_name": "Raj C"}),
    ),
)
def test_authoritative_production_registry_mutations_fail_closed(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None]
) -> None:
    payload = _payload()
    mutation(payload)
    with pytest.raises(PresenterRegistryError) as caught:
        _load_payload(tmp_path, payload)
    assert caught.value.code in {"CANONICAL_REGISTRY", "VOICE_REFERENCE"}


def test_registry_rejects_duplicate_json_keys_malformed_utf8_and_oversize(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    _assert_code(
        "REGISTRY_MALFORMED",
        lambda: load_presenter_registry(duplicate, asset_root=ASSET_ROOT),
    )
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b"\xff\xfe")
    _assert_code(
        "REGISTRY_MALFORMED",
        lambda: load_presenter_registry(malformed, asset_root=ASSET_ROOT),
    )
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * 65_537)
    _assert_code(
        "REGISTRY_TOO_LARGE",
        lambda: load_presenter_registry(oversized, asset_root=ASSET_ROOT),
    )


def test_registry_revalidates_missing_symlinked_and_mutated_assets(tmp_path: Path) -> None:
    payload = _payload()
    asset_root = tmp_path / "assets"
    for path, _digest in EXPECTED_ASSETS.values():
        target = asset_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ASSET_ROOT / path, target)
    (asset_root / EXPECTED_ASSETS["raj"][0]).unlink()
    _assert_code("ASSET_MISSING", lambda: _load_payload(tmp_path, payload, asset_root=asset_root))
    shutil.copy2(ASSET_ROOT / EXPECTED_ASSETS["raj"][0], asset_root / EXPECTED_ASSETS["raj"][0])
    myra_path = asset_root / EXPECTED_ASSETS["myra"][0]
    myra_path.unlink()
    myra_path.symlink_to(ASSET_ROOT / EXPECTED_ASSETS["myra"][0])
    _assert_code("ASSET_UNSAFE", lambda: _load_payload(tmp_path, payload, asset_root=asset_root))
    myra_path.unlink()
    shutil.copy2(ASSET_ROOT / EXPECTED_ASSETS["myra"][0], myra_path)
    myra_path.write_bytes(myra_path.read_bytes()[:-1] + b"x")
    _assert_code("ASSET_CHECKSUM", lambda: _load_payload(tmp_path, payload, asset_root=asset_root))


def test_voice_references_must_be_distinct_and_persona_anchors_complete(tmp_path: Path) -> None:
    payload = _payload()
    _presenter(payload, "raj")["voice"] = copy.deepcopy(_presenter(payload, "myra")["voice"])
    _assert_code("VOICE_REFERENCE", lambda: _load_payload(tmp_path, payload))
    payload = _payload()
    _presenter(payload, "myra")["persona"]["visual_anchors"].remove(
        "coordinated premium necklace and earrings"
    )
    _assert_code("PERSONA_CONTRACT", lambda: _load_payload(tmp_path, payload))


def test_aashna_and_veer_cannot_enter_the_active_registry(tmp_path: Path) -> None:
    for name in ("Aashna", "Veer"):
        payload = _payload()
        extra = copy.deepcopy(payload["presenters"][0])
        extra.update({"id": name.lower(), "display_name": name})
        payload["presenters"].append(extra)
        _assert_code("REGISTRY_ID_SET", lambda: _load_payload(tmp_path, payload))


def test_future_personal_shape_is_test_only_disabled_and_never_selectable(tmp_path: Path) -> None:
    payload = _payload()
    fixture = copy.deepcopy(payload["presenters"][0])
    fixture.update(
        {
            "id": "future-personal-test",
            "display_name": "Future Personal Test Fixture",
            "identity_kind": "PERSONAL",
            "lifecycle": "DISABLED",
            "test_only": True,
            "asset": None,
            "persona": {
                "apparent_age": "adult",
                "summary": "Fictional schema fixture with no real-person attributes.",
                "visual_anchors": ["no likeness or biometric data"],
            },
        }
    )
    payload["presenters"].append(fixture)
    _assert_code("TEST_ONLY", lambda: _load_payload(tmp_path, payload))
    registry = _load_payload(tmp_path, payload, allow_test_fixtures=True)
    assert "future-personal-test" in registry.identities
    _assert_code(
        "PRESENTER_INACTIVE",
        lambda: registry.get("future-personal-test", "1.0.0"),
    )
