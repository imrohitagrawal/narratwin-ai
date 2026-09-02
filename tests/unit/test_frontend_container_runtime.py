from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "frontend/Dockerfile"
CONSENSUS = ROOT / "scripts/ci/check_container_scan_consensus.py"
INDEX_DIGEST = "sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
PLATFORM_DIGESTS = {
    "amd64": "sha256:b4fea132199070b0c8ea9ac66f363fe2cd6d1e4f994e61d8c87976c2157a1b8a",
    "arm64": "sha256:d778881fd638833a2a0ed0fbb30577718729ab08112776dea4555eb5551826da",
}
NODE_SOURCE_INDEX = INDEX_DIGEST
NODE_SOURCE_PLATFORM_DIGESTS = PLATFORM_DIGESTS
RUNTIME_PACKAGES = {
    "alpine-keys": "2.6-r0", "alpine-release": "3.24.1-r0",
    "ca-certificates-bundle": "20260611-r0", "libgcc": "15.2.0-r5",
    "libstdc++": "15.2.0-r5", "musl": "1.2.6-r2",
}


def load_consensus() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue413_consensus", CONSENSUS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_pins_the_reviewed_node_source_and_minimal_final_stage() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    assert f"FROM node:26.7.0-alpine3.24@{NODE_SOURCE_INDEX} AS node-source" in source
    assert source.count("FROM scratch AS") == 2
    assert "FROM scratch AS deps" in source and "FROM scratch AS build" in source
    assert all(value not in source.lower() for value in ("glibc", "gcompat", "libatomic"))


def test_runtime_contract_binds_platform_manifests_and_unaffected_openssl() -> None:
    module = load_consensus()
    assert module.FRONTEND_RUNTIME_INDEX == INDEX_DIGEST
    assert module.FRONTEND_RUNTIME_PLATFORM_DIGESTS == PLATFORM_DIGESTS
    assert module.FRONTEND_NODE_SOURCE_INDEX == NODE_SOURCE_INDEX
    assert module.FRONTEND_NODE_SOURCE_PLATFORM_DIGESTS == NODE_SOURCE_PLATFORM_DIGESTS
    assert module.FRONTEND_RUNTIME_PACKAGES == RUNTIME_PACKAGES
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.7"
    assert module.frontend_openssl_is_acceptable("3.5.7")
    for vulnerable in ("3.6.0", "3.6.3"):
        assert not module.frontend_openssl_is_acceptable(vulnerable)


def test_runtime_preserves_package_identity_while_removing_tools() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    final = source.split(" AS build", 1)[1]
    assert "COPY --from=node-source /runtime/ /" in final
    assert "ENTRYPOINT [\"/usr/bin/node\"]" in final
    assert "USER 65532:65532" in final
    assert "apk" not in final and "/bin/sh" not in final
    assert "/lib/apk/db/installed" in source


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
    assert "actual_architecture" in script
    assert 'actual_architecture}" != "${FRONTEND_ARCH}' in script
