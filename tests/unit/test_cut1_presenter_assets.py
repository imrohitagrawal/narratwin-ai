from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "frontend/public/demo"
NOTICE = ROOT / "docs/THIRD_PARTY_NOTICES.md"
MAX_BYTES = 500_000
EXPECTED_SIZE = (1536, 1024)
EXPECTED_SHA256 = {
    "narratwin-synthetic-presenter.webp": (
        "d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1"
    ),
    "myra-synthetic-presenter.webp": "0" * 64,
    "raj-synthetic-presenter.webp": "f" * 64,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_media_tool(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _decode_webp(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    assert ffprobe is not None, "ffprobe is required for independent WebP validation"
    assert ffmpeg is not None, "ffmpeg is required for independent WebP decode"
    probe = _run_media_tool(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt",
            "-of",
            "json",
            str(path),
        ]
    )
    assert probe.returncode == 0, "asset must be independently probeable WebP"
    payload = json.loads(probe.stdout)
    streams = payload.get("streams")
    assert isinstance(streams, list) and len(streams) == 1, "asset must have one image stream"
    stream = streams[0]
    assert isinstance(stream, dict), "image stream metadata must be an object"
    decode = _run_media_tool(
        [ffmpeg, "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "null", "-"]
    )
    assert decode.returncode == 0, "asset must decode one complete frame"
    return stream


def _validate_asset(path: Path, expected_sha256: str) -> str:
    assert path.exists(), f"missing presenter asset: {path.name}"
    assert path.is_file() and not path.is_symlink(), "presenter asset must be a regular file"
    assert path.suffix == ".webp", "presenter asset must use the WebP extension"
    size = path.stat().st_size
    assert 0 < size <= MAX_BYTES, "presenter asset size is outside its bounded budget"
    header = path.read_bytes()[:12]
    assert header[:4] == b"RIFF" and header[8:12] == b"WEBP", "invalid WebP container"
    digest = _sha256(path)
    assert digest == expected_sha256, "presenter asset checksum mismatch"
    stream = _decode_webp(path)
    assert stream.get("codec_name") == "webp", "presenter asset codec must be WebP"
    assert (stream.get("width"), stream.get("height")) == EXPECTED_SIZE
    assert stream.get("pix_fmt") in {"yuv420p", "yuv444p", "gbrp", "rgb24"}
    return digest


def test_cut1_presenter_assets_are_exact_distinct_and_decodable() -> None:
    digests = [
        _validate_asset(ASSET_DIR / name, digest)
        for name, digest in EXPECTED_SHA256.items()
    ]
    assert len(set(digests)) == len(digests), "presenter assets must be byte-distinct"


def test_cut1_presenter_notice_binds_provenance_and_controlled_use() -> None:
    notice = NOTICE.read_text(encoding="utf-8")
    for name, digest in EXPECTED_SHA256.items():
        assert name in notice
        assert digest in notice
    for marker in (
        "OpenAI Rest-of-World Terms of Use",
        "OpenAI Service Terms",
        "Sharp `0.35.3`",
        "Apache-2.0",
        "text-only",
        "no uploaded or real-person reference",
        "fictional synthetic",
        "controlled-local",
        "public-distribution and legal review",
        "not intended to depict or endorse a real person",
    ):
        assert marker in notice


def test_cut1_presenter_asset_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="missing presenter asset"):
        _validate_asset(tmp_path / "missing.webp", "0" * 64)


@pytest.mark.parametrize("payload", [b"", b"RIFF\x04\x00\x00\x00WEBP"])
def test_cut1_presenter_asset_rejects_empty_or_malformed_bytes(
    tmp_path: Path, payload: bytes
) -> None:
    path = tmp_path / "malformed.webp"
    path.write_bytes(payload)
    with pytest.raises(AssertionError):
        _validate_asset(path, hashlib.sha256(payload).hexdigest())


def test_cut1_presenter_asset_rejects_oversized_bytes(tmp_path: Path) -> None:
    path = tmp_path / "oversized.webp"
    path.write_bytes(b"x" * (MAX_BYTES + 1))
    with pytest.raises(AssertionError, match="bounded budget"):
        _validate_asset(path, _sha256(path))


def test_cut1_presenter_asset_rejects_wrong_extension(tmp_path: Path) -> None:
    path = tmp_path / "portrait.png"
    path.write_bytes((ASSET_DIR / "narratwin-synthetic-presenter.webp").read_bytes())
    with pytest.raises(AssertionError, match="WebP extension"):
        _validate_asset(path, _sha256(path))


def test_cut1_presenter_asset_rejects_checksum_mismatch() -> None:
    with pytest.raises(AssertionError, match="checksum mismatch"):
        _validate_asset(ASSET_DIR / "narratwin-synthetic-presenter.webp", "0" * 64)


def test_cut1_presenter_asset_rejects_wrong_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        __name__ + "._decode_webp",
        lambda _path: {"codec_name": "webp", "width": 1, "height": 1, "pix_fmt": "yuv420p"},
    )
    path = ASSET_DIR / "narratwin-synthetic-presenter.webp"
    with pytest.raises(AssertionError):
        _validate_asset(path, EXPECTED_SHA256[path.name])


def test_cut1_presenter_asset_rejects_symlink(tmp_path: Path) -> None:
    target = ASSET_DIR / "narratwin-synthetic-presenter.webp"
    link = tmp_path / "linked.webp"
    link.symlink_to(target)
    with pytest.raises(AssertionError, match="regular file"):
        _validate_asset(link, EXPECTED_SHA256[target.name])


def test_cut1_presenter_asset_rejects_duplicate_portraits() -> None:
    meera = _sha256(ASSET_DIR / "narratwin-synthetic-presenter.webp")
    with pytest.raises(AssertionError, match="byte-distinct"):
        assert len({meera, meera, "1" * 64}) == 3, "presenter assets must be byte-distinct"
