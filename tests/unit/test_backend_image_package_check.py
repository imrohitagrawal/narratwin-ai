from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_backend_runtime_probe_fails_closed_on_tls_and_inventory_drift() -> None:
    probe = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(encoding="utf-8")
    required = (
        "ssl.OPENSSL_VERSION",
        'startswith("OpenSSL " + expected["opensslVersion"] + " ")',
        "ssl.create_default_context()",
        "ssl.CERT_REQUIRED",
        "/lib/apk/db/installed",
        'packages["libcrypto3"] == expected["opensslApkVersion"]',
        'packages["libssl3"] == expected["opensslApkVersion"]',
        'find_spec("pip")',
        'find_spec("_sqlite3")',
        'version("click")',
        'version("semgrep")',
    )
    assert all(marker in probe for marker in required)


def test_backend_runtime_has_no_package_manager_shell_or_sqlite_capability() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    assert "FROM scratch" in dockerfile
    assert "rm -rf /runtime/usr/local/lib/python3.13/site-packages/pip" in dockerfile
    assert "rm -f /usr/local/lib/python3.13/lib-dynload/_sqlite3*.so" in dockerfile
    assert "apk add" not in dockerfile.split("FROM scratch", maxsplit=1)[1]
    assert "USER 10001:10001" in dockerfile


def test_probe_propagates_validated_profile_to_actual_docker_invocation(tmp_path: Path) -> None:
    import hashlib
    import json
    import os
    import shutil
    import subprocess
    import sys

    from scripts.ci.check_semgrep_security import load_security_profile

    for relative in (
        "scripts/ci/check_semgrep_security.py",
        "scripts/ci/backend-image-package-check.sh",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    policy = load_security_profile(ROOT)
    # A synthetic override proves propagation, never current source eligibility.
    policy["apk"]["opensslApkVersion"] = "3.3.7-r99"
    path = tmp_path / "docs/security/DEPENDENCY_REFRESH.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(policy))
    capture = tmp_path / "capture.json"
    binary = tmp_path / "bin"
    binary.mkdir()
    docker = binary / "docker"
    docker.write_text(
        f"#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\n"
        "Path(os.environ['TASK_PROBE_CAPTURE']).write_text(json.dumps(sys.argv[1:]))\n"
    )
    docker.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(binary) + os.pathsep + os.environ["PATH"],
        "TASK_PROBE_CAPTURE": str(capture),
        "PYTHONPATH": str(tmp_path),
    }
    result = subprocess.run(
        ["bash", "scripts/ci/backend-image-package-check.sh"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    args = json.loads(capture.read_text())
    passed = json.loads(args[-1])
    assert passed["apk"]["opensslApkVersion"] == "3.3.7-r99"
    assert passed["profileSha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'expected = profile["apk"]' in args[-2]
    assert 'packages["libcrypto3"] == expected["opensslApkVersion"]' in args[-2]
    capture.unlink()
    path.write_text("{}")
    result = subprocess.run(
        ["bash", "scripts/ci/backend-image-package-check.sh"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0 and not capture.exists()
