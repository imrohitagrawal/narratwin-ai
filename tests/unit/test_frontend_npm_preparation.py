from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPARER = ROOT / "scripts/ci/prepare_frontend_npm.mjs"

EXPECTED_ARCHIVES = {
    "http-cache-semantics-4.3.0.tgz": "339b792e52694b5507323bf045055d147bcf21219e2c0c4d72b5ae2647868742b1b2a0876753b7357654ffcc7b703d010dc196f246a9c4c293bf096aacd90790",
    "npm-12.0.2.tgz": "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943",
    "brace-expansion-5.0.12.tgz": "628bd0debce168b308ac38cd0cc90d4b4d6d79af77aa11211b9c72f1febe47497e770dca8bee6c0a822823de368ae2d94c75a881692d830543854d3d88d12299",
    "ip-address-10.3.1.tgz": "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea",
    "tar-7.5.21.tgz": "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c",
    "undici-6.28.1.tgz": "cd6a5d4d50f9e07e3c088c9b2f4ad6437ba4a5bf5ddb7c0cede1f946d7dd99e3fbd1c587363b5fa3b3f8bd95fee42a0370ee772783eee6e5e9ee535f8dce8344",
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


def test_runtime_assembler_is_ephemeral_and_shell_free() -> None:
    source = PREPARER.read_text(encoding="utf-8")
    required = (
        "assembleFrontendRuntime",
        "copySharpLibvips",
        "spawnSync",
        "lstatSync",
        "readdirSync",
        "/mnt/deps",
        "/mnt/frontend",
        "/tmp/frontend-build",
    )
    prohibited = ("shell: true", "execSync", "/bin/sh", "narratwin-build-nonce")
    assert all(marker in source for marker in required)
    assert all(marker not in source for marker in prohibited)


def test_sharp_libvips_copy_uses_the_one_locked_regular_soname(tmp_path: Path) -> None:
    dependencies = tmp_path / "dependencies"
    runtime = tmp_path / "runtime"
    library = (
        dependencies
        / "node_modules/@img/sharp-libvips-linuxmusl-x64/lib/libvips-cpp.so.8.18.6"
    )
    library.parent.mkdir(parents=True)
    library.write_bytes(b"reviewed libvips fixture")
    expression = (
        "console.log(module.copySharpLibvips("
        "process.argv[1], process.argv[2], process.argv[3]));"
    )

    result = run_module(expression, str(dependencies), str(runtime), "x64")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "libvips-cpp.so.8.18.6"
    copied = runtime / library.relative_to(dependencies)
    assert copied.read_bytes() == library.read_bytes()


def test_sharp_libvips_copy_rejects_ambiguous_or_unsafe_input(tmp_path: Path) -> None:
    dependencies = tmp_path / "dependencies"
    runtime = tmp_path / "runtime"
    library_dir = dependencies / "node_modules/@img/sharp-libvips-linuxmusl-x64/lib"
    library_dir.mkdir(parents=True)
    expression = (
        "module.copySharpLibvips(process.argv[1], process.argv[2], process.argv[3]);"
    )

    assert run_module(expression, str(dependencies), str(runtime), "s390x").returncode != 0
    (library_dir / "libvips-cpp.so.latest").write_bytes(b"malformed")
    assert run_module(expression, str(dependencies), str(runtime), "x64").returncode != 0
    (library_dir / "libvips-cpp.so.8.18.6").write_bytes(b"one")
    (library_dir / "libvips-cpp.so.8.18.7").write_bytes(b"two")
    assert run_module(expression, str(dependencies), str(runtime), "x64").returncode != 0
    (library_dir / "libvips-cpp.so.8.18.6").unlink()
    (library_dir / "libvips-cpp.so.8.18.7").unlink()
    target = tmp_path / "outside"
    target.write_bytes(b"outside")
    (library_dir / "libvips-cpp.so.8.18.6").symlink_to(target)
    assert run_module(expression, str(dependencies), str(runtime), "x64").returncode != 0
