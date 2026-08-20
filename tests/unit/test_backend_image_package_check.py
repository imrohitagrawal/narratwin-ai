from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_backend_runtime_probe_fails_closed_on_tls_and_inventory_drift() -> None:
    probe = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(encoding="utf-8")
    required = (
        "ssl.OPENSSL_VERSION",
        'startswith("OpenSSL 3.3.7 ")',
        "ssl.create_default_context()",
        "ssl.CERT_REQUIRED",
        "/lib/apk/db/installed",
        'packages["libcrypto3"] == "3.3.7-r0"',
        'packages["libssl3"] == "3.3.7-r0"',
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
