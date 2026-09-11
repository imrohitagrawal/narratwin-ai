from __future__ import annotations

import hashlib
import json
import re
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
                "FROM scratch AS build",
                f"FROM {prior} AS build",
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
    expected_runtime = "node:26.7.0-alpine3.24@sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
    dockerfile = stage8.read("frontend/Dockerfile")
    scan = stage8.read("scripts/ci/docker-image-scan.sh")
    assert security.FRONTEND_NODE_RUNTIME_IMAGE == expected_runtime and f"FROM {expected_runtime} AS node-source" in dockerfile
    assert 'process.version!=="v26.7.0"' in scan and "Sharp transform invalid" in scan
    assert security.FRONTEND_RUNTIME_NODE_VERSION == "26.7.0"
    assert security.FRONTEND_RUNTIME_PACKAGES == {"alpine-keys":"2.6-r0","alpine-release":"3.24.1-r0","ca-certificates-bundle":"20260611-r0","libgcc":"15.2.0-r5","libstdc++":"15.2.0-r5","musl":"1.2.6-r2"}
    for mutation in (dockerfile.replace(expected_runtime, expected_runtime[:-1]+"1"), dockerfile.replace(expected_runtime, "node:26.7.0-alpine3.24:latest"), dockerfile.replace("FROM scratch AS build", f"FROM {security.ISSUE389_VULNERABLE_RUNTIME_IMAGE} AS build"), dockerfile.replace("/lib/apk/db/installed", "REMOVED")):
        assert not security.frontend_node_image_valid(mutation)


def test_issue502_musl_closure_and_real_sharp_transform_fail_closed() -> None:
    dockerfile = stage8.read("frontend/Dockerfile")
    scan = stage8.read("scripts/ci/docker-image-scan.sh")
    pins = tuple(f"{name}={version}" for name, version in security.FRONTEND_RUNTIME_PACKAGES.items())
    assert all(dockerfile.count(pin) == 1 for pin in pins)
    copy_call = "m.copySharpLibvips('/mnt/deps','/app',process.arch)"
    assert copy_call in dockerfile
    assert "libvips-cpp.so.8.18.3" not in dockerfile
    assert all(marker in scan for marker in ("sharp(input).resize(2,2).png()", "Sharp transform invalid", "2x2:png"))
    mutations = [dockerfile.replace(pin, "REMOVED", 1) for pin in pins]
    mutations += [
        dockerfile.replace(pins[0], f"{pins[0]} {pins[0]}", 1),
        dockerfile.replace(copy_call, "REMOVED", 1),
    ]
    assert all(not security.frontend_node_image_valid(candidate) for candidate in mutations)


def _security_job_blocks(workflow: str) -> dict[str, str]:
    jobs = workflow.split("\njobs:\n", 1)
    assert len(jobs) == 2
    matches = list(re.finditer(r"(?m)^  ([a-z][a-z0-9_-]*):\n", jobs[1]))
    return {
        match.group(1): jobs[1][match.start() : matches[index + 1].start()]
        if index + 1 < len(matches)
        else jobs[1][match.start() :]
        for index, match in enumerate(matches)
    }


def _assert_issue529_native_security_topology(workflow: str) -> None:
    prefix = workflow.split("\njobs:\n", 1)[0] + "\njobs:\n"
    blocks = _security_job_blocks(workflow)
    assert hashlib.sha256(prefix.encode()).hexdigest() == (
        "2ae2b00b7a296147edc29479c0aa23ce4cff1d44487a12cce430665c80f4e3ce"
    )
    assert {name: hashlib.sha256(block.encode()).hexdigest() for name, block in blocks.items()} == {
        "security": "d4effe5b5dbfa6afaf0b7e314b1cf75428e9c03aecc2d499e26f1ef5f19fdb63",
        "docker": "5e3a8f837a4cd7b7fc5fc98195882de6ace6cbe2f4e803414e5d2bd08de76b0b",
        "docker-arm64": "3c593b6dc35f4ca0e52d278da11afa0364fce173d7de93728ace0a78f1bae76c",
    }
    assert set(blocks) == {"security", "docker", "docker-arm64"}
    amd64, arm64 = blocks["docker"], blocks["docker-arm64"]
    assert amd64.splitlines().count("    name: security / docker build") == 1
    assert amd64.splitlines().count("    runs-on: ubuntu-latest") == 1
    assert arm64.splitlines().count("    name: security / docker build (ARM64 native)") == 1
    assert arm64.splitlines().count("    runs-on: ubuntu-24.04-arm") == 1
    assert "setup-qemu-action" not in workflow
    assert "--platform linux/arm64" not in workflow

    for block, architecture in ((amd64, "amd64"), (arm64, "arm64")):
        lines = block.splitlines()
        assert lines.count("    timeout-minutes: 30") == 1
        assert re.search(r"(?m)^    if:", block) is None
        assert lines.count(
            "      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4"
        ) == 1
        assert lines.count("        run: bash scripts/ci/docker-build.sh") == 1
        assert lines.count("        run: bash scripts/ci/docker-image-scan.sh") == 1
        assert lines.count(f"          REPORT_DIR: reports/security/{architecture}") == 1
        assert lines.count(f"          BACKEND_ARCH: {architecture}") == 1
        assert lines.count(f"          FRONTEND_ARCH: {architecture}") == 1
        assert lines.count(f"          SESSION: issue529-hosted-{architecture}") == 1
        assert lines.count(f"          BACKEND_IMAGE: narratwin-ai-backend:ci-{architecture}") == 2
        assert lines.count(f"          FRONTEND_IMAGE: narratwin-ai-frontend:ci-{architecture}") == 2
        assert lines.count(
            f"          FRONTEND_BUILD_IMAGE: narratwin-ai-frontend-build:ci-{architecture}"
        ) == 1
        assert lines.count(
            f"          FRONTEND_REPRO_IMAGE: narratwin-ai-frontend:repro-ci-{architecture}"
        ) == 1
        assert lines.count(f"          name: docker-image-scan-reports-{architecture}") == 1
        assert lines.count(f"          path: reports/security/{architecture}") == 1
        assert lines.count(
            "        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4"
        ) == 1
        assert block.count("\n        if:") == 1
        upload_index = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("      - name: Upload Docker image scan reports (")
        )
        assert lines[upload_index + 1] == "        if: always()"
        assert lines.count("          if-no-files-found: error") == 1
        for prohibited in ("continue-on-error", "SKIP_POLICY_EVALUATION", "|| true"):
            assert prohibited not in block


def test_issue529_security_workflow_runs_complete_native_architecture_jobs() -> None:
    _assert_issue529_native_security_topology(stage8.read(".github/workflows/security.yml"))


@pytest.mark.parametrize(
    ("before", "after"),
    (
        ("runs-on: ubuntu-24.04-arm", "runs-on: ubuntu-latest"),
        ("timeout-minutes: 30", "timeout-minutes: 31"),
        ("bash scripts/ci/docker-image-scan.sh", "true"),
        ("name: docker-image-scan-reports-arm64", "name: docker-image-scan-reports-amd64"),
        ("BACKEND_ARCH: arm64", "BACKEND_ARCH: amd64"),
        ("    runs-on: ubuntu-24.04-arm", "    runs-on: ubuntu-24.04-arm\n    if: false"),
        (
            "    runs-on: ubuntu-24.04-arm",
            "    runs-on: ubuntu-latest # runs-on: ubuntu-24.04-arm",
        ),
        (
            "        run: bash scripts/ci/docker-image-scan.sh",
            "        if: false\n        run: bash scripts/ci/docker-image-scan.sh",
        ),
        ("        if: always()", "        if: false"),
        ("if-no-files-found: error", "if-no-files-found: warn"),
        ("run: bash scripts/ci/dependency-security.sh", "run: true"),
        ("  push:\n", "  # push removed:\n"),
        ("          persist-credentials: false\n      - name: Docker build compatibility context (ARM64 native)", "          persist-credentials: true\n      - name: Docker build compatibility context (ARM64 native)"),
        ("          persist-credentials: false\n      - name: Docker build compatibility context", "          persist-credentials: false\n          ref: main\n      - name: Docker build compatibility context"),
        ("    name: secret scan / bandit / audit / semgrep", "    name: secret scan / bandit / audit / semgrep\n    if: github.ref == 'refs/heads/__never__'"),
        ("jobs:\n", 'env:\n  SKIP_POLICY_EVALUATION: "1"\n\njobs:\n'),
        (
            "    runs-on: ubuntu-24.04-arm",
            "    needs: bypass\n    runs-on: ubuntu-24.04-arm",
        ),
        (
            "jobs:\n",
            "defaults:\n  run:\n    shell: 'bash {0}; true'\n\njobs:\n",
        ),
        (
            "    runs-on: ubuntu-24.04-arm",
            "    runs-on: ubuntu-24.04-arm\n    defaults:\n      run:\n        shell: 'bash {0}; true'",
        ),
        (
            "      - name: Docker image vulnerability scan (ARM64 native)",
            "      - name: Docker image vulnerability scan (ARM64 native)\n        shell: 'bash {0}; true'",
        ),
        (
            "      - name: Docker image vulnerability scan (ARM64 native)",
            "      - name: Rewrite checked-out scanner\n        run: printf bypass > scripts/ci/docker-image-scan.sh\n"
            "      - name: Docker image vulnerability scan (ARM64 native)",
        ),
        (
            "  docker-arm64:\n",
            "  bypass-arm64:\n    name: security / docker build (ARM64 native)\n"
            "    runs-on: ubuntu-latest\n    steps:\n      - run: true\n\n  docker-arm64:\n",
        ),
    ),
)
def test_issue529_security_workflow_rejects_native_topology_mutations(
    before: str, after: str
) -> None:
    workflow = stage8.read(".github/workflows/security.yml")
    assert before in workflow
    with pytest.raises(AssertionError):
        _assert_issue529_native_security_topology(workflow.replace(before, after, 1))


def _assert_issue529_active_docs(security_doc: str, stage_plan: str) -> None:
    security_section = security_doc.split("## Issue #502", 1)[1].split("## Issue #509", 1)[0]
    stage_section = stage_plan.split("### Issue #502", 1)[1].split("### Issue #509", 1)[0]
    for section in (security_section, stage_section):
        normalized = section.lower()
        assert "native arm64" in normalized
        assert "separate required" in normalized
        assert "all image, runtime, scanner, consensus, and severity" in normalized
        assert "QEMU-emulated ARM64" not in section
        assert "emulated ARM64 must" not in section


def test_issue529_active_security_and_stage_contracts_use_native_topology() -> None:
    security_doc = stage8.read("docs/SECURITY_AND_PRIVACY.md")
    stage_plan = stage8.read("docs/STAGE_ISSUE_PLAN.md")
    _assert_issue529_active_docs(security_doc, stage_plan)
    for original, stale in (
        ("native ARM64", "QEMU-emulated ARM64"),
        ("separate required", "unchanged single hosted"),
    ):
        with pytest.raises(AssertionError):
            _assert_issue529_active_docs(
                security_doc.replace(original, stale, 1),
                stage_plan.replace(original, stale, 1),
            )


def test_issue376_shell_free_dependency_builder_contract_fails_closed() -> None:
    dockerfile = stage8.read("frontend/Dockerfile")
    assert security.issue376_frontend_builder_valid(dockerfile)
    assert security.FRONTEND_NODE_BUILD_IMAGE == "scratch"
    required = (
        "FROM scratch AS deps",
        "prepare_frontend_npm.mjs",
        '"ci", "--ignore-scripts"',
        "/runtime/lib/apk/db/installed",
        "musl=1.2.6-r2",
        "process.config.variables.node_use_quic!==false",
        "--mount=from=deps,source=/app,target=/mnt/deps,readonly",
        "assembleFrontendRuntime",
    )
    prohibited = ("glibc", "gcompat", "libatomic", "apt-get", "sha512sum", "npm ci --", "libcrypto3", "libssl3", "busybox", "narratwin-build-nonce")
    assert all(marker in dockerfile for marker in required)
    assert all(marker not in dockerfile.lower() for marker in prohibited)
    mutations = [
        dockerfile.replace("--ignore-scripts", "--strict-allow-scripts=true"),
        dockerfile.replace("prepare_frontend_npm.mjs", "missing.mjs", 1),
        dockerfile.replace(security.FRONTEND_NODE_RUNTIME_IMAGE, "node:26.7.0-alpine3.24:latest", 1),
        dockerfile + "\nFROM alpine AS bypass\n",
        dockerfile + "\nCOPY --from=node-source /lib/libssl.so.3 /lib/\n",
        dockerfile.replace("/runtime/lib/apk/db/installed", "/tmp/installed", 1),
        dockerfile.replace("process.config.variables.node_use_quic!==false", "true"),
        dockerfile.replace("assembleFrontendRuntime", "removedAssembler"),
    ]
    assert all(not security.issue376_frontend_builder_valid(candidate) for candidate in mutations)


def test_issue376_preflight_identity_scope_and_budget_are_exact() -> None:
    preflight = json.loads((stage8.ROOT / "docs/governance/preflights/issue-376.json").read_text())
    assert security.ISSUE376_SECURITY_BRANCH == "stage8-376-builder-security-isolation-r2"
    assert security.ISSUE376_BASE == "87b8504ca8d5e094394343aeaa4ef5bad46133d5"
    assert security.ISSUE376_PREFLIGHT_COMMIT == "39fd81b06e6d7995d49c76cad638bd70f739d6ca"
    assert security.ISSUE376_CHARGE_LIMIT == 1400
    assert len(security.ISSUE376_SECURITY_FILES) == 13
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
