from __future__ import annotations

import importlib.util
import json
import stat
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_evidence_module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts" / "ci" / "heartbeat1_evidence.py"
    spec = importlib.util.spec_from_file_location("heartbeat1_evidence_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_safe_error(error: Exception, marker: bytes) -> None:
    rendered = str(error)
    assert marker.decode() not in rendered
    assert marker.hex() not in rendered


def test_authority_encoding_set_is_exact_and_every_form_is_detected(tmp_path: Path) -> None:
    evidence: Any = load_evidence_module()
    marker = b"synthetic private scan marker 306"
    canary = b"synthetic-canary-306"

    assert evidence.ENCODING_NAMES == (
        "UTF-8 bytes",
        "hex",
        "Base64",
        "url-safe Base64",
        "percent-encoded",
        "JSON-escaped UTF-8",
    )
    canonical = evidence.encoded_patterns(marker)
    variants = list(canonical.values()) + [
        canonical["percent-encoded"].lower(), canonical["Base64"].rstrip(b"="),
        evidence.quote_plus(marker.decode(), safe="").lower().encode(),
    ]
    for index, encoded in enumerate(variants):
        candidate = tmp_path / f"candidate-{index}.bin"
        candidate.write_bytes(encoded)
        with pytest.raises(evidence.EvidenceError) as caught:
            evidence.scan_evidence([candidate], controlled=marker, canary=canary)
        assert caught.value.code == "CONTROLLED_MATCH"
        assert_safe_error(caught.value, marker)


def test_recursive_zip_scan_passes_clean_members_and_blocks_member_match(tmp_path: Path) -> None:
    evidence: Any = load_evidence_module()
    marker = b"synthetic-private-archive-marker-306"
    canary = b"synthetic-canary-archive-306"
    clean = tmp_path / "clean.zip"
    blocked = tmp_path / "blocked.zip"
    metadata_blocked = tmp_path / "metadata-blocked.zip"
    with zipfile.ZipFile(clean, "w") as archive:
        archive.writestr("safe/member.txt", b"bounded public-safe evidence")
    with zipfile.ZipFile(blocked, "w") as archive:
        archive.writestr("safe/member.txt", marker)
    with zipfile.ZipFile(metadata_blocked, "w") as archive:
        member = zipfile.ZipInfo(marker.decode())
        archive.writestr(member, b"bounded public-safe evidence")

    result = evidence.scan_evidence([clean], controlled=marker, canary=canary)
    assert result["matchCount"] == 0
    assert result["archiveCount"] == 1
    assert result["memberCount"] == 1
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_evidence([blocked], controlled=marker, canary=canary)
    assert caught.value.code == "CONTROLLED_MATCH"
    assert_safe_error(caught.value, marker)
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_evidence([metadata_blocked], controlled=marker, canary=canary)
    assert caught.value.code == "CONTROLLED_MATCH"


def test_malformed_archive_and_symlink_fail_closed(tmp_path: Path) -> None:
    evidence: Any = load_evidence_module()
    malformed = tmp_path / "broken.zip"
    malformed.write_bytes(b"bounded-non-archive")
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_evidence([malformed], controlled=b"synthetic private 306", canary=b"canary 306")
    assert caught.value.code == "ARCHIVE_INVALID"
    nested = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("resources/blob.bin", b"PK\x03\x04bounded-non-archive")
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_evidence([nested], controlled=b"synthetic private 306", canary=b"canary 306")
    assert caught.value.code == "ARCHIVE_INVALID"
    link = tmp_path / "link.zip"
    link.symlink_to(malformed)
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_evidence([link], controlled=b"synthetic private 306", canary=b"canary 306")
    assert caught.value.code == "SCAN_INPUT_INVALID"


def test_ast_materialization_is_restricted_and_writes_mode_0600(tmp_path: Path) -> None:
    evidence: Any = load_evidence_module()
    source = tmp_path / "fixture_source.py"
    source.write_text(
        "PUBLIC_FIXTURE = b'public-synthetic-306'\n"
        "INTERNAL_FIXTURE = b'synthetic-private-materialized-306'\n"
        "def canary_holder():\n"
        "    canary = b'synthetic-canary-materialized-306'\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"

    metadata = evidence.materialize(source, runtime)

    assert metadata["publicBytes"] == len(b"public-synthetic-306")
    assert metadata["internalBytes"] == len(b"synthetic-private-materialized-306")
    assert metadata["canaryBytes"] == len(b"synthetic-canary-materialized-306")
    assert stat.S_IMODE(runtime.stat().st_mode) == 0o700
    assert {stat.S_IMODE(path.stat().st_mode) for path in runtime.iterdir()} == {0o600}


def test_browser_source_scan_rejects_success_interception_without_echoing_source(tmp_path: Path) -> None:
    evidence: Any = load_evidence_module()
    entry = tmp_path / "browser.spec.ts"
    helper = tmp_path / "helper.ts"
    entry.write_text("import './helper';\n")
    for source in (
        "const method = ['ro', 'ute'].join(''); const blocked = context/* bounded */[method];\n",
        "const method = ['ro', 'ute'].join(''); const blocked = context // bounded\n[method];\n",
    ):
        helper.write_text(source)
        with pytest.raises(evidence.EvidenceError) as caught:
            evidence.scan_browser_sources(entry)
        assert caught.value.code == "FORBIDDEN_BROWSER_SOURCE"
    assert "page.route" not in str(caught.value)
    with pytest.raises(evidence.EvidenceError) as caught:
        evidence.scan_browser_sources(Path("frontend/tests/heartbeat1-browser.spec.ts"), "0" * 40)
    assert caught.value.code == "BROWSER_HEAD_MISMATCH"


def test_safe_failure_summary_never_contains_marker_or_encoding() -> None:
    evidence: Any = load_evidence_module()
    marker = b"synthetic-private-failure-marker-306"

    summary = evidence.failure_summary("run-306", "CONTROLLED_MATCH", files=3, members=2, byte_count=99)
    rendered = json.dumps(summary, sort_keys=True)

    assert summary["outcome"] == "WITHHELD"
    assert marker.decode() not in rendered
    assert marker.hex() not in rendered
