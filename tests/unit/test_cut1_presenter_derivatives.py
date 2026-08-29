from __future__ import annotations

import copy
import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, cast

import pytest
from PIL import Image, UnidentifiedImageError, features

import backend.app.presenter_registry as registry_module
from backend.app.cut1_controlled_presenter import REGISTRY_SHA256 as T04_REGISTRY_SHA256
from backend.app.presenter_registry import PresenterRegistryError


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs/governance/cut1-presenter-derivatives-v1.json"
SOURCE_REGISTRY_PATH = ROOT / "backend/app/presenter_registry.json"
SOURCE_REGISTRY_FILE_SHA256 = (
    "eb31a953b85ffaf2c43f54e4da7fb89eda740c724967a9301f726c6091ab01c2"
)
MYRA_ATTEMPT1_SHA256 = "4f4fbd0f1f125cfb39b052b4717d8d30feb43dc226fcd940c1ef28b7ca48e360"
MYRA_ATTEMPT2_AUTHORITY_REF = (
    "https://github.com/imrohitagrawal/narratwin-ai/issues/459"
    "#issuecomment-5464690216"
)
SOURCE_ASSETS = {
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
DERIVATIVES = {
    "myra": (
        "frontend/public/demo/cut1/myra-waist-up.webp",
        "46390ac627662bff38c9bb4ec904520a808e42030ff698741b5c32519f0be4c3",
        1086,
        1448,
        150_246,
        "00d71d0e6d25ff3772c2f6e05617853a240248e5e4ffa3ac623f7de5d7eed6bf",
    ),
    "raj": (
        "frontend/public/demo/cut1/raj-waist-up.webp",
        "f9060b3c0fb5d9cf0231f8142fff17a88c61537d12c6b90ad6be359085c86413",
        1024,
        1536,
        50_406,
        "d4ae828f1043a6191136956dc936a22e1b849cb5c9b9775a846efe403fd76196",
    ),
}


def _api(name: str) -> Any:
    value = getattr(registry_module, name, None)
    assert value is not None, f"T03 RED: presenter_registry.{name} is not implemented"
    return value


def _manifest() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def _write_manifest(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "derivatives.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _load(
    path: Path = MANIFEST_PATH,
    *,
    asset_root: Path = ROOT,
    source_registry_path: Path = SOURCE_REGISTRY_PATH,
) -> Any:
    return _api("load_presenter_derivatives")(
        path,
        asset_root=asset_root,
        source_registry_path=source_registry_path,
    )


def _assert_code(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(PresenterRegistryError) as caught:
        operation()
    assert caught.value.code == code


def _row(payload: dict[str, Any], presenter_id: str) -> dict[str, Any]:
    return next(row for row in payload["derivatives"] if row["presenter_id"] == presenter_id)


def _copy_bound_files(tmp_path: Path) -> None:
    for relative, _digest in SOURCE_ASSETS.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    for relative, _digest, _width, _height, _size, _candidate in DERIVATIVES.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    target = tmp_path / "backend/app/presenter_registry.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_REGISTRY_PATH, target)


def _webp_chunks(path: Path) -> list[bytes]:
    data = path.read_bytes()
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    assert int.from_bytes(data[4:8], "little") + 8 == len(data)
    offset, chunks = 12, []
    while offset < len(data):
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        chunks.append(data[offset : offset + 4])
        offset += 8 + size + size % 2
    assert offset == len(data)
    return chunks


def _decode_webp(path: Path) -> tuple[str | None, tuple[int, int], int]:
    with Image.open(path) as image:
        image.load()
        return image.format, image.size, getattr(image, "n_frames", 1)


def test_original_identity_anchors_and_source_registry_remain_byte_identical() -> None:
    assert hashlib.sha256(SOURCE_REGISTRY_PATH.read_bytes()).hexdigest() == (
        SOURCE_REGISTRY_FILE_SHA256
    )
    for path, expected in SOURCE_ASSETS.values():
        candidate = ROOT / path
        assert candidate.is_file() and not candidate.is_symlink()
        assert hashlib.sha256(candidate.read_bytes()).hexdigest() == expected


def test_source_and_derivative_digest_meanings_remain_distinct() -> None:
    source = registry_module.load_cut1_presenter_registry(asset_root=ROOT)
    derivatives = _load()
    assert T04_REGISTRY_SHA256 == SOURCE_REGISTRY_FILE_SHA256
    assert registry_module.CANONICAL_PRODUCTION_SHA256 == (
        "14838d74e2ff35ca4af5336d937eb206ec77a8351ba6b7cd86bfdc6929913855"
    )
    assert source.manifest_sha256 == (
        "9671da9ef076a56d86c2e81307d71e83356e0b88050e1bae7ef8960919e50caa"
    )
    assert derivatives.manifest_sha256 not in {
        SOURCE_REGISTRY_FILE_SHA256,
        registry_module.CANONICAL_PRODUCTION_SHA256,
        source.manifest_sha256,
    }


def test_default_derivative_registry_binds_exact_raj_and_myra_assets() -> None:
    registry = _api("load_cut1_presenter_derivatives")(asset_root=ROOT)
    assert set(registry.derivatives) == {"myra", "raj"}
    assert "meera" not in registry.derivatives
    assert registry.source_registry_file_sha256 == SOURCE_REGISTRY_FILE_SHA256
    assert registry.source_registry_manifest_sha256 != registry.manifest_sha256
    assert len(registry.manifest_sha256) == 64
    for presenter_id, expected in DERIVATIVES.items():
        derivative = registry.get(presenter_id, "1.0.0")
        path, digest, width, height, size, candidate_sha256 = expected
        assert (
            derivative.path,
            derivative.sha256,
            derivative.width,
            derivative.height,
            derivative.byte_count,
            derivative.candidate_sha256,
        ) == (path, digest, width, height, size, candidate_sha256)
        asset = ROOT / path
        assert asset.is_file() and not asset.is_symlink()
        assert asset.stat().st_size == size < 500_000
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == digest
        assert derivative.media_type == "image/webp"
        assert derivative.width <= derivative.candidate_width
        assert derivative.height <= derivative.candidate_height


def test_derivative_webps_are_single_frame_and_metadata_free() -> None:
    for path, _digest, _width, _height, _size, _candidate in DERIVATIVES.values():
        chunks = _webp_chunks(ROOT / path)
        assert chunks == [b"VP8 "]
        assert not {b"EXIF", b"XMP ", b"ANIM", b"ANMF", b"ICCP"} & set(chunks)


def test_derivative_webps_decode_one_complete_frame() -> None:
    assert features.check("webp") is True
    for path, _digest, width, height, _size, _candidate in DERIVATIVES.values():
        assert _decode_webp(ROOT / path) == ("WEBP", (width, height), 1)


def test_corrupt_compressed_webp_payload_fails_executable_decode(tmp_path: Path) -> None:
    source = ROOT / DERIVATIVES["raj"][0]
    data = bytearray(source.read_bytes())
    assert data[12:16] == b"VP8 "
    payload_size = int.from_bytes(data[16:20], "little")
    payload_start, payload_end = 20, 20 + payload_size
    assert data[payload_start + 3 : payload_start + 6] == b"\x9d\x01\x2a"
    data[payload_start + 10 : payload_end] = b"\xff" * (payload_size - 10)
    corrupt = tmp_path / "corrupt-compressed-payload.webp"
    corrupt.write_bytes(data)

    assert _webp_chunks(corrupt) == [b"VP8 "]
    assert registry_module._probe_webp(bytes(data)) == (1024, 1536)
    with pytest.raises((UnidentifiedImageError, OSError)):
        _decode_webp(corrupt)


def test_meera_is_explicitly_source_ready_without_a_derivative() -> None:
    readiness = _api("DerivativeReadiness")
    registry = _load()
    assert registry.source_ready_without_derivative == frozenset({"meera"})
    assert registry.readiness("meera", "1.0.0") is readiness.SOURCE_READY_NO_DERIVATIVE
    assert registry.readiness("myra", "1.0.0") is readiness.DERIVATIVE_READY
    assert registry.readiness("raj", "1.0.0") is readiness.DERIVATIVE_READY
    _assert_code("DERIVATIVE_STALE", lambda: registry.readiness("meera", "0.9.0"))
    _assert_code("DERIVATIVE_NOT_FOUND", lambda: registry.readiness("other", "1.0.0"))


def test_derivative_readiness_is_controlled_local_reviewed_and_provider_free() -> None:
    registry = _load()
    assert registry.posture == {
        "permitted_use": "CONTROLLED_LOCAL_CUT1",
        "publication_allowed": False,
        "runtime_provider": None,
        "credential_count": 0,
        "egress_attempt_count": 0,
        "spend_microusd": 0,
    }
    for presenter_id, derivative in registry.derivatives.items():
        assert derivative.generation_method == "OpenAI built-in image edit (gpt-image-2.0)"
        expected_attempts = (2, 2, 1) if presenter_id == "myra" else (1, 2, 0)
        assert (
            derivative.attempt_count,
            derivative.max_attempts,
            derivative.retry_count,
        ) == expected_attempts
        assert derivative.visual_review == "INDEPENDENT_ACCEPTED"
        assert derivative.provenance_privacy_review == "INDEPENDENT_ACCEPTED"
        assert derivative.reviewed_candidate_sha256 == derivative.candidate_sha256
        expected_review_date = "2026-08-30" if presenter_id == "myra" else "2026-08-29"
        assert derivative.review_current_as_of == expected_review_date
        assert derivative.hands_visible is True
        assert derivative.professional_gesture is True
        assert derivative.complete_head_and_hands is True
        assert derivative.identity_preserved is True
        assert derivative.metadata_stripped is True
        assert derivative.consent_basis == "PROJECT_OWNED_SYNTHETIC_IDENTITY"
        assert derivative.permitted_use == "CONTROLLED_LOCAL_CUT1"
        assert derivative.publication_allowed is False
        assert derivative.private_source_committed is False
        expected_disposition = (
            f"OWNER_SUPERSEDED_VISUAL_REFINEMENT:{MYRA_ATTEMPT1_SHA256}"
            if presenter_id == "myra"
            else "NONE_REJECTED_ONE_ATTEMPT_USED"
        )
        assert derivative.rejected_candidate_disposition == expected_disposition
        assert derivative.deletion_posture == (
            "PRIVATE_SOURCE_RETAINED_PENDING_OWNER_CLEANUP_AFTER_MERGE"
        )


def test_provenance_privacy_and_authority_references_are_exact_and_resolve() -> None:
    manifest = _manifest()
    notice = ROOT / "docs/THIRD_PARTY_NOTICES.md"
    heading = "## Issue #459 T03 controlled-local presenter derivatives"
    assert heading in notice.read_text(encoding="utf-8")
    for row in manifest["derivatives"]:
        expected_authority = (
            MYRA_ATTEMPT2_AUTHORITY_REF
            if row["presenter_id"] == "myra"
            else "https://github.com/imrohitagrawal/narratwin-ai/issues/459"
            "#issuecomment-5463568867"
        )
        assert row["review"]["authority_ref"] == expected_authority
        assert row["review"]["provenance_privacy_review"] == "INDEPENDENT_ACCEPTED"
        assert row["rights"]["privacy_posture"] == (
            "PRIVATE_GENERATED_SOURCE_RESTRICTED_LOCAL_ONLY"
        )
        assert row["rights"]["provenance_ref"] == (
            "docs/THIRD_PARTY_NOTICES.md"
            "#issue-459-t03-controlled-local-presenter-derivatives"
        )


def test_myra_attempt2_lineage_is_exact_and_raj_remains_attempt1() -> None:
    manifest = _manifest()
    myra, raj = _row(manifest, "myra"), _row(manifest, "raj")

    assert myra["candidate"]["attempt_count"] == 2
    assert myra["candidate"]["max_attempts"] == 2
    assert myra["candidate"]["retry_count"] == 1
    assert myra["candidate"]["sha256"] != MYRA_ATTEMPT1_SHA256
    assert myra["rights"]["rejected_candidate_disposition"] == (
        f"OWNER_SUPERSEDED_VISUAL_REFINEMENT:{MYRA_ATTEMPT1_SHA256}"
    )
    assert myra["review"]["authority_ref"] == MYRA_ATTEMPT2_AUTHORITY_REF

    assert raj["candidate"]["attempt_count"] == 1
    assert raj["candidate"]["retry_count"] == 0
    assert raj["candidate"]["sha256"] == DERIVATIVES["raj"][5]
    assert raj["asset"]["sha256"] == DERIVATIVES["raj"][1]


def test_binding_keeps_source_registry_and_derivative_authorities_distinct() -> None:
    registry = _load()
    binding = registry.bind("raj", "1.0.0")
    registry.verify_binding(binding)
    assert binding.source_registry_sha256 == registry.source_registry_manifest_sha256
    assert binding.derivative_manifest_sha256 == registry.manifest_sha256
    assert binding.source_registry_sha256 != binding.derivative_manifest_sha256
    assert binding.source_asset_sha256 == SOURCE_ASSETS["raj"][1]
    assert binding.derivative_asset_sha256 == DERIVATIVES["raj"][1]
    for field, value in (
        ("presenter_id", "myra"),
        ("presenter_version", "9.9.9"),
        ("source_registry_sha256", "0" * 64),
        ("source_asset_sha256", "1" * 64),
        ("derivative_manifest_sha256", "2" * 64),
        ("derivative_asset_sha256", "3" * 64),
        ("derivative_path", DERIVATIVES["myra"][0]),
        ("binding_sha256", "4" * 64),
    ):
        _assert_code(
            "DERIVATIVE_BINDING_MISMATCH",
            lambda: registry.verify_binding(cast(Any, replace)(binding, **{field: value})),
        )
    _assert_code("DERIVATIVE_NOT_FOUND", lambda: registry.bind("meera", "1.0.0"))
    _assert_code("DERIVATIVE_STALE", lambda: registry.bind("raj", "0.9.0"))


@pytest.mark.parametrize(
    "mutation",
    (
        lambda data: data.update({"unknown": True}),
        lambda data: data.update({"schema_version": "future"}),
        lambda data: data.update({"manifest_version": "9.9.9"}),
        lambda data: data.update({"source_ready_without_derivative": []}),
        lambda data: data.update({"source_ready_without_derivative": ["meera", "raj"]}),
        lambda data: data["source_registry"].update({"file_sha256": "0" * 64}),
        lambda data: data["source_registry"].update({"manifest_sha256": "1" * 64}),
        lambda data: data["posture"].update({"publication_allowed": True}),
        lambda data: data["posture"].update({"runtime_provider": "vendor"}),
        lambda data: data["posture"].update({"credential_count": 1}),
        lambda data: data["posture"].update({"egress_attempt_count": 1}),
        lambda data: data["posture"].update({"spend_microusd": 1}),
        lambda data: data["derivatives"].pop(),
        lambda data: data["derivatives"].append(copy.deepcopy(data["derivatives"][0])),
        lambda data: data["derivatives"].reverse(),
        lambda data: _row(data, "raj").update({"presenter_id": "meera"}),
        lambda data: _row(data, "raj")["source_asset"].update({"sha256": "2" * 64}),
        lambda data: _row(data, "raj")["candidate"].update({"sha256": "3" * 64}),
        lambda data: _row(data, "raj")["candidate"].update({"attempt_count": 2}),
        lambda data: _row(data, "raj")["candidate"].update({"retry_count": 1}),
        lambda data: _row(data, "myra")["candidate"].update(
            {"sha256": MYRA_ATTEMPT1_SHA256}
        ),
        lambda data: _row(data, "myra")["candidate"].update({"attempt_count": 1}),
        lambda data: _row(data, "myra")["candidate"].update({"max_attempts": 3}),
        lambda data: _row(data, "myra")["candidate"].update({"retry_count": 0}),
        lambda data: _row(data, "myra")["review"].update(
            {"reviewed_candidate_sha256": MYRA_ATTEMPT1_SHA256}
        ),
        lambda data: _row(data, "myra")["review"].update(
            {
                "authority_ref": "https://github.com/imrohitagrawal/narratwin-ai/"
                "issues/459#issuecomment-5463568867"
            }
        ),
        lambda data: _row(data, "myra")["rights"].update(
            {"rejected_candidate_disposition": "NONE_REJECTED_ONE_ATTEMPT_USED"}
        ),
        lambda data: _row(data, "raj")["asset"].update({"path": "../escape.webp"}),
        lambda data: _row(data, "raj")["asset"].update({"sha256": "4" * 64}),
        lambda data: _row(data, "raj")["asset"].update({"width": 2048}),
        lambda data: _row(data, "raj")["asset"].update({"height": 2048}),
        lambda data: _row(data, "raj")["asset"].update({"byte_count": 500_000}),
        lambda data: _row(data, "raj")["asset"].update({"media_type": "image/png"}),
        lambda data: _row(data, "raj")["review"].update({"hands_visible": False}),
        lambda data: _row(data, "raj")["review"].update({"identity_preserved": False}),
        lambda data: _row(data, "raj")["review"].update({"review_current_as_of": "2026-08-28"}),
        lambda data: _row(data, "raj")["rights"].update({"publication_allowed": True}),
        lambda data: _row(data, "raj")["rights"].update({"private_source_committed": True}),
        lambda data: _row(data, "raj")["rights"].update({"deletion_posture": "unknown"}),
        lambda data: _row(data, "raj")["rights"].update(
            {"rejected_candidate_disposition": "rejected candidate omitted"}
        ),
        lambda data: _row(data, "raj")["conversion"].update({"upscaled": True}),
        lambda data: _row(data, "raj")["conversion"].update({"metadata_stripped": False}),
    ),
)
def test_manifest_substitution_and_authority_mutations_fail_closed(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None]
) -> None:
    payload = _manifest()
    mutation(payload)
    with pytest.raises(PresenterRegistryError):
        _load(_write_manifest(tmp_path, payload))


def test_manifest_rejects_duplicate_keys_malformed_utf8_and_oversize(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    _assert_code("DERIVATIVE_MALFORMED", lambda: _load(duplicate))
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b"\xff\xfe")
    _assert_code("DERIVATIVE_MALFORMED", lambda: _load(malformed))
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * 65_537)
    _assert_code("DERIVATIVE_TOO_LARGE", lambda: _load(oversized))


def test_derivative_assets_reject_missing_symlink_checksum_and_source_registry_drift(
    tmp_path: Path,
) -> None:
    _copy_bound_files(tmp_path)
    manifest = _write_manifest(tmp_path, _manifest())
    raj = tmp_path / DERIVATIVES["raj"][0]
    raj.unlink()
    _assert_code(
        "DERIVATIVE_ASSET_MISSING",
        lambda: _load(
            manifest,
            asset_root=tmp_path,
            source_registry_path=tmp_path / "backend/app/presenter_registry.json",
        ),
    )
    shutil.copy2(ROOT / DERIVATIVES["raj"][0], raj)
    myra = tmp_path / DERIVATIVES["myra"][0]
    myra.unlink()
    myra.symlink_to(ROOT / DERIVATIVES["myra"][0])
    _assert_code(
        "DERIVATIVE_ASSET_UNSAFE",
        lambda: _load(
            manifest,
            asset_root=tmp_path,
            source_registry_path=tmp_path / "backend/app/presenter_registry.json",
        ),
    )
    myra.unlink()
    shutil.copy2(ROOT / DERIVATIVES["myra"][0], myra)
    myra.write_bytes(myra.read_bytes()[:-1] + b"x")
    _assert_code(
        "DERIVATIVE_ASSET_CHECKSUM",
        lambda: _load(
            manifest,
            asset_root=tmp_path,
            source_registry_path=tmp_path / "backend/app/presenter_registry.json",
        ),
    )
    shutil.copy2(ROOT / DERIVATIVES["myra"][0], myra)
    source_registry = tmp_path / "backend/app/presenter_registry.json"
    source_registry.write_bytes(source_registry.read_bytes() + b"\n")
    _assert_code(
        "DERIVATIVE_SOURCE_REGISTRY",
        lambda: _load(manifest, asset_root=tmp_path, source_registry_path=source_registry),
    )
