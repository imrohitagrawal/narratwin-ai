from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "frontend/Dockerfile"
CONSENSUS = ROOT / "scripts/ci/check_container_scan_consensus.py"
INDEX_DIGEST = "sha256:ce3cc39fe3b8b2602d3b1c4d63d301e46b48c550ecb627869853ddcdda418b63"
PLATFORM_DIGESTS = {
    "amd64": "sha256:beb1f82448d01c14c85266ee5ea8cca055e1e2dbf3880bbfcc6de85838f38c4f",
    "arm64": "sha256:0b88f68083e0d252401044f3a1b0b244f7d863134eb523e2c8012535f47b2d1c",
}
OPENSSL_PACKAGES = {"libcrypto3": "3.5.7-r0", "libssl3": "3.5.7-r0"}


def load_consensus() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue413_consensus", CONSENSUS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_pins_the_reviewed_official_node_multiarch_index() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    expected = f"FROM node:26.7.0-alpine3.23@{INDEX_DIGEST} AS runner"
    assert expected in source
    runner = source.split(" AS runner", 1)[0].rsplit("FROM ", 1)[1]
    assert ":latest" not in runner and "chainguard" not in runner


def test_runtime_contract_binds_platform_manifests_and_unaffected_openssl() -> None:
    module = load_consensus()
    assert module.FRONTEND_RUNTIME_INDEX == INDEX_DIGEST
    assert module.FRONTEND_RUNTIME_PLATFORM_DIGESTS == PLATFORM_DIGESTS
    assert module.FRONTEND_RUNTIME_OPENSSL_PACKAGES == OPENSSL_PACKAGES
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.7"
    assert module.frontend_openssl_is_acceptable(OPENSSL_PACKAGES)
    for vulnerable in ("3.6.0-r0", "3.6.3-r3"):
        assert not module.frontend_openssl_is_acceptable(
            {"libcrypto3": vulnerable, "libssl3": vulnerable}
        )


def test_runtime_preserves_package_identity_while_removing_tools() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    runner = source.split(" AS runner", 1)[1]
    assert 'fs.existsSync("/lib/apk/db/installed")' in runner
    assert 'fs.renameSync("/usr/local/bin/node","/usr/bin/node")' in runner
    assert 'p!=="/usr/bin/node"' in runner
    assert "/usr/local/lib/node_modules" in runner
    assert "ENTRYPOINT [\"/usr/bin/node\"]" in runner
    assert "USER 65532:65532" in runner
    assert "/lib/apk/db/installed" not in runner.split("fs.rmSync", 1)[-1]


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_OPENSSL_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
