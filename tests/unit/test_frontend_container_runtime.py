from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "frontend/Dockerfile"
CONSENSUS = ROOT / "scripts/ci/check_container_scan_consensus.py"
INDEX_DIGEST = "sha256:c6ad9e9c1d80f6eb607c26b4b0a132ff7a2344fad1c78ea3baa2a7d4c8de6d94"
PLATFORM_DIGESTS = {
    "amd64": "sha256:d431b1d60cd8de74dc66d271c236f66227998c308e011e60faa9c60dc4d37382",
    "arm64": "sha256:81aab771be4f445efddcecc1f9efbace81be8d184bd9ec7a8e77b67890334c67",
}
NODE_SOURCE_INDEX = INDEX_DIGEST
NODE_SOURCE_PLATFORM_DIGESTS = PLATFORM_DIGESTS
RUNTIME_PACKAGES = {
    "alpine-keys": "2.6-r0", "alpine-release": "3.24.2-r0",
    "ca-certificates-bundle": "20260909-r0", "libgcc": "15.2.0-r5",
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
    assert f"FROM node:26.13.0-alpine3.24@{NODE_SOURCE_INDEX} AS node-source" in source
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
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.9"
    assert module.frontend_openssl_is_acceptable("3.5.9")
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


def test_runtime_discards_volatile_apk_install_log() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    node_source = source.split("FROM scratch AS deps", 1)[0]

    assert "rm -f /runtime/var/log/apk.log" in node_source
    assert node_source.index("apk add --root /runtime") < node_source.index(
        "rm -f /runtime/var/log/apk.log"
    )
    assert "/runtime/lib/apk/db/installed" in node_source


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
    assert "actual_architecture" in script
    assert 'actual_architecture}" != "${FRONTEND_ARCH}' in script


def test_scan_normalises_only_preview_secret_fields_of_next_preview_props() -> None:
    """RED: dropping the preview-props branch makes every reproduction check fail on Next 16.4."""
    scan = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert 'previewProps=B("/app/.next/server/preview-props.json")' in scan
    assert "same(prerender)||same(previewProps)" in scan
    assert 'keys!=="previewModeEncryptionKey,previewModeId,previewModeSigningKey"' in scan


def test_image_scan_thresholds_stay_pinned() -> None:
    """RED: lowering any scanner threshold or the consensus cut-offs, which a clean scan would hide."""
    scan = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    consensus = CONSENSUS.read_text(encoding="utf-8")
    for marker in (
        'local image="$1" output="$2" severity="${3:-CRITICAL,HIGH}"\n'
        '  trivy image --severity "${severity}" --exit-code 1',
        'local image="$1" output="$2" severity="${3:-high}"\n  grype "${image}" --fail-on "${severity}"',
        'scan_trivy "${FRONTEND_BUILD_CONFIG}" "${REPORT_DIR}/frontend-build-trivy.raw.sarif.json"\n',
        'scan_grype "${FRONTEND_BUILD_CONFIG}" "${REPORT_DIR}/frontend-build-grype.raw.sarif.json"\n',
        'scan_trivy "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-trivy.raw.sarif.json"\n',
        'scan_grype "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-grype.raw.sarif.json"\n',
        'scan_trivy "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-trivy.raw.sarif.json" "CRITICAL,HIGH,MEDIUM"\n',
        'scan_grype "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-grype.raw.sarif.json" "medium"\n',
    ):
        assert marker in scan
    assert 'name.startswith("frontend") and rule_id and severity >= 4.0' in consensus
    assert "elif rule_id and severity >= 7.0" in consensus
