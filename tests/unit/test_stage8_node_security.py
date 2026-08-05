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
    assert "generateBuildId" in next_config
    assert "NARRATWIN_BUILD_ID_INPUTS" in next_config
    for marker in (
        'scan_trivy "${FRONTEND_IMAGE}"',
        '"CRITICAL,HIGH,MEDIUM"',
        'scan_grype "${FRONTEND_IMAGE}"',
        '"medium"',
        "previewModeSigningKey",
        "server action manifest mismatch",
    ):
        assert marker in scan
