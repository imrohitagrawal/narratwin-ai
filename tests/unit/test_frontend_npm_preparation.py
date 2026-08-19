from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPARER = ROOT / "scripts/ci/prepare_frontend_npm.mjs"

EXPECTED_ARCHIVES = {
    "npm-12.0.2.tgz": "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943",
    "brace-expansion-5.0.9.tgz": "49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2ceade8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6",
    "ip-address-10.3.1.tgz": "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea",
    "tar-7.5.21.tgz": "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c",
    "undici-6.28.0.tgz": "2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e274e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28",
}


def run_module(expression: str, *args: str) -> subprocess.CompletedProcess[str]:
    source = f'import * as module from {json.dumps(PREPARER.as_uri())};\n{expression}'
    return subprocess.run(
        ["node", "--input-type=module", "--eval", source, "--", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_archive_contract_is_exact_and_immutable() -> None:
    result = run_module("console.log(JSON.stringify(module.ARCHIVES))")
    assert result.returncode == 0, result.stderr
    archives = json.loads(result.stdout)
    assert {item["filename"]: item["sha512"] for item in archives} == EXPECTED_ARCHIVES
    assert archives[0]["package"] == "npm" and archives[0]["version"] == "12.0.2"
    assert all(set(item) == {"filename", "package", "version", "sha512", "destination"} for item in archives)


def test_checksum_verification_accepts_exact_bytes_and_rejects_drift(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tgz"
    archive.write_bytes(b"trusted fixture bytes")
    digest = hashlib.sha512(archive.read_bytes()).hexdigest()
    expression = "module.verifyArchiveChecksum(process.argv[1], process.argv[2]);"
    accepted = run_module(expression, str(archive), digest)
    assert accepted.returncode == 0, accepted.stderr
    rejected = run_module(expression, str(archive), "0" * 128)
    assert rejected.returncode != 0
    assert "checksum mismatch" in rejected.stderr.lower()


def test_destination_guard_rejects_escape_and_aliases(tmp_path: Path) -> None:
    root = tmp_path / "npm"
    root.mkdir()
    inside = root / "node_modules" / "tar"
    expression = "module.assertSafeDestination(process.argv[1], process.argv[2]);"
    assert run_module(expression, str(root), str(inside)).returncode == 0
    for destination in (tmp_path / "outside", root, root / ".." / "outside"):
        rejected = run_module(expression, str(root), str(destination))
        assert rejected.returncode != 0
        assert "destination" in rejected.stderr.lower()


def test_preparer_rejects_unexpected_cli_arguments() -> None:
    result = subprocess.run(
        ["node", str(PREPARER), "unexpected"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "arguments" in result.stderr.lower()
