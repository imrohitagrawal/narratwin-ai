from __future__ import annotations

from typing import Any

from scripts.quality import check_stage8_docs as stage8
from scripts.quality import stage8_node_security as security


def route(monkeypatch: Any, changed: list[str]) -> list[str]:
    monkeypatch.setattr(stage8, "current_branch", lambda: security.ISSUE374_SECURITY_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: changed)
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    return failures


def test_issue374_scope_and_pinned_images_fail_closed(monkeypatch: Any) -> None:
    assert route(monkeypatch, sorted(security.ISSUE374_SECURITY_FILES)) == []
    dockerfile = stage8.read("frontend/Dockerfile")
    assert security.frontend_node_image_valid(dockerfile)
    prior = (
        "node:26.4.0-alpine@sha256:"
        "725aeba2364a9b16beae49e180d83bd597dbd0b15c47f1f28875c290bfd255b9"
    )
    mutations = [
        dockerfile.replace(security.FRONTEND_NODE_BUILD_IMAGE, prior),
        dockerfile.replace(security.FRONTEND_NODE_BUILD_IMAGE, "node:26.6.0-alpine"),
        dockerfile.replace("sha512sum -c -", "REMOVED", 1),
        dockerfile.replace(
            security.FRONTEND_NODE_RUNTIME_IMAGE,
            security.FRONTEND_NODE_RUNTIME_IMAGE[:-1] + "0",
        ),
        dockerfile.replace(
            f"FROM {security.FRONTEND_NODE_RUNTIME_IMAGE} AS runner",
            f"FROM {prior} AS runner",
        ),
    ]
    mutations.extend(
        dockerfile + f"\n{prefix} {prior} AS bypass\n"
        for prefix in ("from", "FrOm", "  FROM", "\tFROM")
    )
    mutations.extend(
        dockerfile.replace(marker, "REMOVED")
        for marker in (
            *security.FRONTEND_BUILD_ARCHIVE_SHA512,
            *security.FRONTEND_BUILD_ARCHIVE_SHA512.values(),
        )
    )
    assert all(not security.frontend_node_image_valid(mutated) for mutated in mutations)


def test_issue374_reproducibility_and_runtime_policy_markers() -> None:
    next_config = stage8.read("frontend/next.config.ts")
    scan = stage8.read("scripts/ci/docker-image-scan.sh")
    consensus = stage8.read("scripts/ci/check_container_scan_consensus.py")
    assert "generateBuildId" in next_config
    assert "NARRATWIN_BUILD_ID_INPUTS" in next_config
    for marker in (
        'scan_trivy "${FRONTEND_IMAGE}"',
        '"CRITICAL,HIGH,MEDIUM"',
        'scan_grype "${FRONTEND_IMAGE}"',
        '"medium"',
        "previewModeSigningKey",
        "server action manifest mismatch",
        "--no-cache-filter build",
        "verify_frontend_reproducibility",
        "FRONTEND_BUILD_CONFIG",
        'scan_trivy "${FRONTEND_BUILD_CONFIG}"',
    ):
        assert marker in scan
    assert "FRONTEND_BUILD_SECRET_REUSED" in consensus


def test_issue389_fixed_runtime_pin_and_package_contract_fail_closed() -> None:
    expected_runtime = (
        "cgr.dev/chainguard/node:latest@sha256:"
        "d8d2883b26d4fde4e524d0068cd78abbb23c7c2113a22e67a02cc73a9182552d"
    )
    dockerfile = stage8.read("frontend/Dockerfile")
    scan = stage8.read("scripts/ci/docker-image-scan.sh")

    assert security.FRONTEND_NODE_RUNTIME_IMAGE == expected_runtime
    assert f"FROM {expected_runtime} AS runner" in dockerfile
    assert 'process.version!=="v26.7.0"' in scan
    assert '"org.opencontainers.image.created": "2026-08-05T21:53:32Z"' in scan
    assert security.FRONTEND_RUNTIME_NODE_VERSION == "26.7.0"
    assert security.FRONTEND_RUNTIME_NPM_PACKAGE == "npm-12 12.0.2-r2"
    for mutation in (
        dockerfile.replace(expected_runtime, expected_runtime[:-1] + "0"),
        dockerfile.replace(expected_runtime, "cgr.dev/chainguard/node:latest"),
        dockerfile.replace(expected_runtime, security.ISSUE389_VULNERABLE_RUNTIME_IMAGE),
    ):
        assert not security.frontend_node_image_valid(mutation)


def test_issue389_exact_route_scope_and_budgets_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: security.ISSUE389_SECURITY_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: sorted(security.ISSUE389_SECURITY_FILES),
    )
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []
    assert len(security.ISSUE389_SECURITY_FILES) == 14
    assert security.ISSUE389_CHARGE_LIMIT == 900
    assert security.ISSUE389_FILE_LIMITS == {
        "scripts/quality/stage8_node_security.py": 180,
        "tests/unit/test_stage8_node_security.py": 220,
        "scripts/quality/check_stage8_docs.py": 40,
    }
