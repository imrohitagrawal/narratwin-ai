from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

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
        dockerfile.replace("--checksum=sha256:", "--checksum=sha256:0", 1),
        dockerfile.replace(
            security.FRONTEND_NODE_RUNTIME_IMAGE,
            security.FRONTEND_NODE_RUNTIME_IMAGE[:-1] + "1",
        ),
        dockerfile.replace(
            security.FRONTEND_NODE_SOURCE_IMAGE,
            security.FRONTEND_NODE_SOURCE_IMAGE[:-1] + "0",
        ),
        dockerfile.replace(
            security.FRONTEND_ATOMIC_SOURCE_IMAGE,
            security.FRONTEND_ATOMIC_SOURCE_IMAGE[:-1] + "0",
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
            *security.FRONTEND_BUILD_ARCHIVE_SHA256,
            *security.FRONTEND_BUILD_ARCHIVE_SHA256.values(),
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
    expected_runtime = "cgr.dev/chainguard/glibc-dynamic@sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70"
    dockerfile = stage8.read("frontend/Dockerfile")
    scan = stage8.read("scripts/ci/docker-image-scan.sh")
    assert security.FRONTEND_NODE_RUNTIME_IMAGE == expected_runtime and f"FROM {expected_runtime} AS runner" in dockerfile
    assert 'process.version!=="v26.7.0"' in scan and '"org.opencontainers.image.created": "2026-08-07T21:12:55Z"' in scan
    assert security.FRONTEND_RUNTIME_NODE_VERSION == "26.7.0"
    assert security.FRONTEND_RUNTIME_PACKAGES == {"ca-certificates-bundle":"20260413-r0","glibc":"2.43-r12","glibc-locale-posix":"2.43-r12","ld-linux":"2.43-r12","libatomic":"16.1.0-r4","libgcc":"16.1.0-r4","libstdc++":"16.1.0-r4","wolfi-baselayout":"20230201-r29"}
    for mutation in (dockerfile.replace(expected_runtime, expected_runtime[:-1]+"1"), dockerfile.replace(expected_runtime, "cgr.dev/chainguard/glibc-dynamic:latest"), dockerfile.replace(expected_runtime, security.ISSUE389_VULNERABLE_RUNTIME_IMAGE), dockerfile.replace("fs.appendFileSync(p", "REMOVED")):
        assert not security.frontend_node_image_valid(mutation)


def test_issue376_shell_free_dependency_builder_contract_fails_closed() -> None:
    dockerfile = stage8.read("frontend/Dockerfile")
    assert security.issue376_frontend_builder_valid(dockerfile)
    assert security.FRONTEND_NODE_BUILD_IMAGE == security.FRONTEND_NODE_RUNTIME_IMAGE
    required = (
        "AS deps",
        "prepare_frontend_npm.mjs",
        '"ci", "--ignore-scripts"',
        '"node_modules/next/dist/bin/next", "build"',
        "/runtime/libatomic-record",
        "/runtime/var/lib/db/sbom/",
        "process.config.variables.node_use_quic!==false",
        "--mount=from=deps,source=/app,target=/mnt/deps,readonly",
        "assembleFrontendRuntime",
    )
    prohibited = ("/bin/sh", "apk ", "apt-get", "sha512sum", "npm ci --", "libcrypto3", "libssl3", "busybox", "narratwin-build-nonce")
    assert all(marker in dockerfile for marker in required)
    assert all(marker not in dockerfile.lower() for marker in prohibited)
    mutations = [
        dockerfile.replace("--ignore-scripts", "--strict-allow-scripts=true"),
        dockerfile.replace("prepare_frontend_npm.mjs", "missing.mjs", 1),
        dockerfile.replace(security.FRONTEND_NODE_RUNTIME_IMAGE, "cgr.dev/chainguard/glibc-dynamic:latest", 1),
        dockerfile + "\nRUN apk add openssl\n",
        dockerfile + "\nCOPY --from=node-source /lib/libssl.so.3 /lib/\n",
        dockerfile.replace("/runtime/libatomic-record", "/tmp/libatomic-record", 1),
        dockerfile.replace("process.config.variables.node_use_quic!==false", "true"),
        dockerfile.replace("assembleFrontendRuntime", "removedAssembler"),
    ]
    assert all(not security.issue376_frontend_builder_valid(candidate) for candidate in mutations)


def test_issue376_preflight_identity_scope_and_budget_are_exact() -> None:
    preflight = json.loads((stage8.ROOT / "docs/governance/preflights/issue-376.json").read_text())
    assert security.ISSUE376_SECURITY_BRANCH == "stage8-376-builder-security-isolation"
    assert security.ISSUE376_BASE == "87b8504ca8d5e094394343aeaa4ef5bad46133d5"
    assert security.ISSUE376_CHARGE_LIMIT == 1200
    assert len(security.ISSUE376_SECURITY_FILES) == 12
    assert preflight["issue_number"] == 376 and preflight["branch"] == security.ISSUE376_SECURITY_BRANCH
    assert set(preflight["scope"]["required"]) == security.ISSUE376_SECURITY_FILES
    assert set(preflight["scope"]["allowed_prefixes"]) == security.ISSUE376_SECURITY_FILES


def test_issue389_exact_route_scope_and_budgets_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: security.ISSUE389_SECURITY_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(security.ISSUE389_SECURITY_FILES))
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []
    assert len(security.ISSUE389_SECURITY_FILES) == 14
    assert security.ISSUE389_CHARGE_LIMIT == 900
    assert security.ISSUE389_FILE_LIMITS == {"scripts/quality/stage8_node_security.py":180, "tests/unit/test_stage8_node_security.py":220, "scripts/quality/check_stage8_docs.py":40}


def _runner(*, staged: str = "", untracked: str = "", failed: bool = False) -> Any:
    rows = "\n".join(f"1\t0\t{p}" for p in sorted(security.ISSUE389_SECURITY_FILES))
    def run(command: list[str]) -> SimpleNamespace:
        if command[:3] == ["git", "rev-parse", "HEAD^{commit}"]:
            return SimpleNamespace(stdout="f" * 40 + "\n", returncode=0)
        if command[:2] == ["git", "merge-base"]:
            return SimpleNamespace(stdout=security.ISSUE389_BASE + "\n", returncode=0)
        output = untracked if command[:3] == ["git", "ls-files", "--others"] else staged if "--cached" in command and staged else rows
        return SimpleNamespace(stdout=output, returncode=2 if failed else 0)
    return run


@pytest.mark.parametrize(("staged", "untracked", "failed", "want"), [
    ("901\t0\tfrontend/Dockerfile\n", "", False, "exceeds its 900"),
    ("181\t0\tscripts/quality/stage8_node_security.py\n", "", False, "exceeds 180"),
    ("", "frontend/Dockerfile\n", False, "untracked-path"), ("", "", True, "evidence failed closed")])
def test_issue389_all_git_snapshots_fail_closed(staged: str, untracked: str, failed: bool, want: str) -> None:
    failures: list[str] = []
    security.check_issue389_route(stage8.ROOT, _runner(staged=staged, untracked=untracked, failed=failed), failures, True)
    assert any(want in failure for failure in failures)


@pytest.mark.parametrize("output", ["1\t0\tfrontend/Dockerfile\n2\t0\tfrontend/Dockerfile\n", "1\t0\tforeign/path.py\n", "-\t-\tfrontend/Dockerfile\n"])
def test_issue389_charge_evidence_rejects_malformed_or_unscoped(output: str) -> None:
    failures: list[str] = []
    security._charges(output, failures)
    assert failures
