from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "frontend/Dockerfile"
CONSENSUS = ROOT / "scripts/ci/check_container_scan_consensus.py"
INDEX_DIGEST = "sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70"
PLATFORM_DIGESTS = {
    "amd64": "sha256:f95c554213997aeb84b4c146819f08481e99a6f9b0a7a7524cdcc02632cfac5d",
    "arm64": "sha256:4edabf15b30c80cc70a24d0614a6f911d306f58a1613d72a653a0e135eccdde8",
}
NODE_SOURCE_INDEX = "sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341"
NODE_SOURCE_PLATFORM_DIGESTS = {
    "amd64": "sha256:c00614442a3c693109886209462dd1b15462f6726347fa9cb9fc0125ca26f275",
    "arm64": "sha256:9e7720738fbcb12e8122beb5194cfa58ab0029c78c3ed39f8986aa68713e31bc",
}
ATOMIC_SOURCE_INDEX = "sha256:8cfe0b01dcf3ad08aa8d51811175749f7390228be059497ddc6d94551a68f66e"
ATOMIC_SOURCE_PLATFORM_DIGESTS = {
    "amd64": "sha256:9ea374ada3432e4877777fbef5cfe7c5e23047b8aaf247cc609ffe0564542794",
    "arm64": "sha256:c88d6308aa590caf0e5591934f9d7802b12108d6124601b3015626b6bab70421",
}
RUNTIME_PACKAGES = {
    "ca-certificates-bundle": "20260413-r0", "glibc": "2.43-r12",
    "glibc-locale-posix": "2.43-r12", "ld-linux": "2.43-r12",
    "libatomic": "16.1.0-r4", "libgcc": "16.1.0-r4", "libstdc++": "16.1.0-r4",
    "wolfi-baselayout": "20230201-r29",
}


def load_consensus() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue413_consensus", CONSENSUS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_pins_the_reviewed_node_source_and_minimal_final_stage() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    assert f"FROM node:26.7.0-bookworm-slim@{NODE_SOURCE_INDEX} AS node-source" in source
    assert f"FROM cgr.dev/chainguard/gcc-glibc@{ATOMIC_SOURCE_INDEX} AS atomic-source" in source
    assert f"FROM cgr.dev/chainguard/glibc-dynamic@{INDEX_DIGEST} AS runner" in source
    assert ":latest" not in source.split(" AS runner", 1)[0].rsplit("FROM ", 1)[1]


def test_runtime_contract_binds_platform_manifests_and_unaffected_openssl() -> None:
    module = load_consensus()
    assert module.FRONTEND_RUNTIME_INDEX == INDEX_DIGEST
    assert module.FRONTEND_RUNTIME_PLATFORM_DIGESTS == PLATFORM_DIGESTS
    assert module.FRONTEND_NODE_SOURCE_INDEX == NODE_SOURCE_INDEX
    assert module.FRONTEND_NODE_SOURCE_PLATFORM_DIGESTS == NODE_SOURCE_PLATFORM_DIGESTS
    assert module.FRONTEND_ATOMIC_SOURCE_INDEX == ATOMIC_SOURCE_INDEX
    assert module.FRONTEND_ATOMIC_SOURCE_PLATFORM_DIGESTS == ATOMIC_SOURCE_PLATFORM_DIGESTS
    assert module.FRONTEND_RUNTIME_PACKAGES == RUNTIME_PACKAGES
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.7"
    assert module.frontend_openssl_is_acceptable("3.5.7")
    for vulnerable in ("3.6.0", "3.6.3"):
        assert not module.frontend_openssl_is_acceptable(vulnerable)


def test_runtime_preserves_package_identity_while_removing_tools() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    runner = source.split(" AS runner", 1)[1]
    assert "COPY --from=node-source --chown=0:0 /usr/local/bin/node /usr/bin/node" in runner
    assert "COPY --from=atomic-source --chown=0:0 /runtime/ /" in runner
    assert "ENTRYPOINT [\"/usr/bin/node\"]" in runner
    assert "USER 65532:65532" in runner
    assert "fs.appendFileSync(p" in runner
    assert "fs.rmSync('/usr/lib/apk/db/installed')" not in runner


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
    assert "actual_architecture" in script
    assert 'actual_architecture}" != "${FRONTEND_ARCH}' in script
