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
ALPINE_INDEX_DIGEST = "sha256:d77617aef5805191da75fbbfe2f9dc2043582ecad0f4d381b27c151034765a76"
ALPINE_PLATFORM_DIGESTS = {
    "amd64": "sha256:266f29255458134745f2bf588cb23ed1ed1768b96ff2580a05d70a8aba59e145",
    "arm64": "sha256:42d86a3173522de4786cfba0b5d631dbadb3d03a86d218dafb070dafd9809c7e",
}
RUNTIME_PACKAGES = {
    "ca-certificates-bundle": "20260611-r0",
    "libgcc": "15.2.0-r2",
    "libstdc++": "15.2.0-r2",
    "musl": "1.2.6-r2",
}


def load_consensus() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue413_consensus", CONSENSUS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_pins_the_reviewed_source_and_uses_a_scratch_final_stage() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    expected = f"FROM node:26.7.0-alpine3.23@{INDEX_DIGEST} AS runtime-source"
    assert expected in source
    assert f"FROM alpine:edge@{ALPINE_INDEX_DIGEST} AS musl-source" in source
    assert "FROM scratch AS runner" in source
    assert ":latest" not in source.split(" AS runtime-source", 1)[0].rsplit("FROM ", 1)[1]


def test_runtime_contract_binds_platform_manifests_and_unaffected_openssl() -> None:
    module = load_consensus()
    assert module.FRONTEND_RUNTIME_INDEX == INDEX_DIGEST
    assert module.FRONTEND_RUNTIME_PLATFORM_DIGESTS == PLATFORM_DIGESTS
    assert module.FRONTEND_MUSL_INDEX == ALPINE_INDEX_DIGEST
    assert module.FRONTEND_MUSL_PLATFORM_DIGESTS == ALPINE_PLATFORM_DIGESTS
    assert module.FRONTEND_RUNTIME_PACKAGES == RUNTIME_PACKAGES
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.7"
    assert module.frontend_openssl_is_acceptable("3.5.7")
    for vulnerable in ("3.6.0", "3.6.3"):
        assert not module.frontend_openssl_is_acceptable(vulnerable)


def test_runtime_preserves_package_identity_while_removing_tools() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    assembly, runner = source.split("FROM scratch AS runner", 1)
    assert 'selected=new Set(["ca-certificates-bundle","libgcc","libstdc++","musl"])' in assembly
    assert 'fs.writeFileSync("/runtime/lib/apk/db/installed"' in assembly
    assert "COPY --from=runtime-source --chown=0:0 /runtime/ /" in runner
    assert "ENTRYPOINT [\"/usr/bin/node\"]" in runner
    assert "USER 65532:65532" in runner
    assert "/lib/apk/db/installed" not in runner.split("COPY --from=runtime-source", 1)[-1]


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
