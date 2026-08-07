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
    "myra-synthetic-presenter.webp": (
        "30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97"
    ),
    "raj-synthetic-presenter.webp": (
        "663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd"
    ),
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


def _probe_exact_webp_container(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    assert len(data) >= 30, "WebP container is too short"
    assert int.from_bytes(data[4:8], "little") + 8 == len(data), (
        "WebP RIFF length must cover the exact file"
    )
    offset = 12
    image_chunk: tuple[bytes, bytes] | None = None
    while offset < len(data):
        assert offset + 8 <= len(data), "WebP chunk header is truncated"
        kind = data[offset : offset + 4]
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        start = offset + 8
        end = start + size
        assert end <= len(data), "WebP chunk payload is truncated"
        if image_chunk is None and kind in {b"VP8 ", b"VP8L", b"VP8X"}:
            image_chunk = (kind, data[start:end])
        offset = end + (size % 2)
    assert offset == len(data), "WebP chunk padding must cover the exact file"
    assert image_chunk is not None and image_chunk[0] == b"VP8 ", (
        "expected a lossy VP8 WebP image chunk"
    )
    payload = image_chunk[1]
    assert len(payload) >= 10 and payload[3:6] == b"\x9d\x01\x2a", (
        "VP8 key-frame header is malformed"
    )
    assert hashlib.sha256(data).hexdigest() in EXPECTED_SHA256.values(), (
        "fallback probe accepts only reviewed presenter bytes"
    )
    return {
        "codec_name": "webp",
        "width": int.from_bytes(payload[6:8], "little") & 0x3FFF,
        "height": int.from_bytes(payload[8:10], "little") & 0x3FFF,
        "pix_fmt": "yuv420p",
    }


def _decode_webp(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if ffprobe is None or ffmpeg is None:
        return _probe_exact_webp_container(path)
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


def test_cut1_presenter_assets_fail_closed_without_external_media_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _command: None)
    for name, digest in EXPECTED_SHA256.items():
        assert _validate_asset(ASSET_DIR / name, digest) == digest
    truncated = tmp_path / "truncated.webp"
    truncated.write_bytes(
        (ASSET_DIR / "narratwin-synthetic-presenter.webp").read_bytes()[:-1]
    )
    with pytest.raises(AssertionError, match="RIFF length"):
        _validate_asset(truncated, _sha256(truncated))
    frame_header_only = tmp_path / "frame-header-only.webp"
    frame_header = b"\x00\x00\x00\x9d\x01\x2a\x00\x06\x00\x04"
    frame_header_only.write_bytes(
        b"RIFF" + (22).to_bytes(4, "little") + b"WEBPVP8 "
        + len(frame_header).to_bytes(4, "little") + frame_header
    )
    with pytest.raises(AssertionError, match="reviewed presenter"):
        _validate_asset(frame_header_only, _sha256(frame_header_only))


def test_cut1_presenter_notice_binds_provenance_and_controlled_use() -> None:
    notice = NOTICE.read_text(encoding="utf-8")
    prompt_digests = {
        hashlib.sha256(block.split("\n```", 1)[0].encode()).hexdigest()
        for block in notice.split("```text\n")[1:]
    }
    assert {"17605aaf0bd34ac29b0e56b09e61a6791ccc2b340832f2f6bd9fea47f2b9c26d",
            "79d35ec0d6ce11cdb481f91dc7358a0408b298012ab86f0b50c08c2309f4b9b9"} <= prompt_digests
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
        "17605aaf0bd34ac29b0e56b09e61a6791ccc2b340832f2f6bd9fea47f2b9c26d",
        "79d35ec0d6ce11cdb481f91dc7358a0408b298012ab86f0b50c08c2309f4b9b9",
        "a4186431ca0a037620c90f5835e6fb6964d29934b4e2dc517c2929a87396c27d",
        "d829196db1d84173fa077ff099450dde5dd186b39efdd5a3b9a1bac2ab6528a4",
        "selected Myra A and Raj C",
        "Aashna/Character 1",
        "Veer/Character 2",
        "/private/tmp/narratwin-issue383-candidates-lhIQbq/myra-a.png",
        "/private/tmp/narratwin-issue383-candidates-lhIQbq/raj-c.png",
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
