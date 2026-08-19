from __future__ import annotations

from pathlib import Path

from scripts.quality import stage8_backend_security as security


ROOT = Path(__file__).parents[2]


def test_issue436_backend_image_contract_is_exact_and_fail_closed() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    assert security.BACKEND_BASE_IMAGE == (
        "docker.io/library/alpine:3.21@sha256:"
        "48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d"
    )
    assert security.CPYTHON_VERSION == "3.13.15"
    assert security.CPYTHON_SHA256 == (
        "1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76"
    )
    assert security.backend_dockerfile_valid(dockerfile)


def test_issue436_rejects_image_source_tls_and_metadata_mutations() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    mutations = (
        dockerfile.replace(security.BACKEND_BASE_IMAGE, "alpine:3.21"),
        dockerfile.replace(security.BACKEND_BASE_IMAGE, security.BACKEND_BASE_IMAGE[:-1] + "0"),
        dockerfile.replace(security.CPYTHON_VERSION, "3.13.14"),
        dockerfile.replace(security.CPYTHON_SHA256, "0" * 64),
        dockerfile.replace("sha256sum -c -", "REMOVED"),
        dockerfile.replace("libssl3=3.3.7-r0", "libssl3=3.5.7-r0"),
        dockerfile.replace("libcrypto3=3.3.7-r0", "libcrypto3=3.5.7-r0"),
        dockerfile.replace("/lib/apk/db/installed", "/tmp/concealed"),
        dockerfile + "\nFROM alpine:latest AS bypass\n",
    )
    assert all(not security.backend_dockerfile_valid(value) for value in mutations)


def test_issue436_runtime_probe_requires_tls_and_safe_openssl_line() -> None:
    probe = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(encoding="utf-8")
    for marker in (
        "ssl.OPENSSL_VERSION",
        'startswith("OpenSSL 3.3.7 ")',
        "ssl.create_default_context()",
        "/lib/apk/db/installed",
        'packages["libcrypto3"] == "3.3.7-r0"',
        'packages["libssl3"] == "3.3.7-r0"',
    ):
        assert marker in probe
