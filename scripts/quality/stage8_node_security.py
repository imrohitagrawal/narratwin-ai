"""Issue #374/#389 frontend build/runtime pin and branch-scope contracts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

ISSUE374_SECURITY_BRANCH = "stage8-374-node-image-cve-2026-58043"
ISSUE374_SECURITY_FILES = {
    "frontend/Dockerfile",
    "frontend/next.config.ts",
    "scripts/ci/docker-image-scan.sh",
    "scripts/ci/check_container_scan_consensus.py",
    "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_node_security.py",
    "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_container_scan_consensus.py",
    "tests/unit/test_stage8_node_security.py",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
ISSUE389_SECURITY_BRANCH = "cut1-process-389-frontend-runtime-npm12-security"
ISSUE389_BASE = "48fc32a2689c9bbc03742d774f3eadb8a500dafc"
ISSUE389_CHARGE_LIMIT = 900
ISSUE389_FILE_LIMITS = {
    "scripts/quality/stage8_node_security.py": 180,
    "tests/unit/test_stage8_node_security.py": 220,
    "scripts/quality/check_stage8_docs.py": 40,
}
ISSUE389_SECURITY_FILES = {
    "docs/governance/preflights/issue-389.json", "frontend/Dockerfile", "scripts/ci/docker-image-scan.sh",
    "scripts/ci/check_container_scan_consensus.py", "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_node_security.py", "tests/unit/test_container_scan_consensus.py",
    "tests/unit/test_stage8_node_security.py", "docs/ADR/0006-stage8-release-hardening.md",
    "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md", "docs/THIRD_PARTY_NOTICES.md",
}
I389_ROUTES = {ISSUE389_SECURITY_BRANCH: ISSUE389_SECURITY_FILES}
ISSUE376_SECURITY_BRANCH = "stage8-376-builder-security-isolation-r2"
ISSUE376_BASE = "87b8504ca8d5e094394343aeaa4ef5bad46133d5"
ISSUE376_PREFLIGHT_COMMIT = "39fd81b06e6d7995d49c76cad638bd70f739d6ca"
ISSUE376_CHARGE_LIMIT = 1400
ISSUE376_SECURITY_FILES = {
    "docs/governance/preflights/issue-376.json", "frontend/Dockerfile",
    "scripts/ci/prepare_frontend_npm.mjs", "scripts/quality/stage8_node_security.py",
    "scripts/quality/check_stage8_docs.py", "tests/unit/test_frontend_npm_preparation.py",
    "tests/unit/test_stage8_node_security.py", "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_frontend_container_runtime.py",
    "docs/ADR/0006-stage8-release-hardening.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
I376_ROUTES = {ISSUE376_SECURITY_BRANCH: ISSUE376_SECURITY_FILES}
FRONTEND_NODE_RUNTIME_IMAGE = (
    "node:26.7.0-alpine3.24@sha256:"
    "aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
)
FRONTEND_NODE_BUILD_IMAGE = "scratch"
FRONTEND_NODE_SOURCE_IMAGE = (
    "node:26.7.0-alpine3.24@sha256:"
    "aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
)
ISSUE389_VULNERABLE_RUNTIME_IMAGE = (
    "cgr.dev/chainguard/node:latest@sha256:"
    "cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734"
)
FRONTEND_RUNTIME_NODE_VERSION = "26.7.0"
FRONTEND_RUNTIME_PACKAGES = {
    "alpine-keys": "2.6-r0", "alpine-release": "3.24.1-r0",
    "ca-certificates-bundle": "20260611-r0", "libgcc": "15.2.0-r5",
    "libstdc++": "15.2.0-r5", "musl": "1.2.6-r2",
}
FRONTEND_BUILD_ARCHIVE_SHA512 = {
    "npm@12.0.2": (
        "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b"
        "1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943"
    ),
    "brace-expansion@5.0.9": (
        "49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2cea"
        "de8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6"
    ),
    "ip-address@10.3.1": (
        "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d"
        "800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea"
    ),
    "tar@7.5.21": (
        "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b"
        "09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c"
    ),
    "undici@6.28.0": (
        "2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e2"
        "74e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28"
    ),
}
FRONTEND_BUILD_ARCHIVE_SHA256 = {
    "npm-12.0.2.tgz": "5dbb86c71d07a1957f2e90734092dd6a58bdcd9ebc2d8d41ca1c6e6a21d364e1",
    "brace-expansion-5.0.9.tgz": "5d06001fddd25cbee90c96db4dc5b7b57711b984c3141e28d10f143deb52dbaf",
    "ip-address-10.3.1.tgz": "ad1790063beea11a312c801df30d58e147de762f4f77787552376eb7424623e5",
    "tar-7.5.21.tgz": "bcedf25a21daecd1a18fb5e19ab855b7d79ec8ef1da175e8ba85cfc0ed0069d1",
    "undici-6.28.0.tgz": "32a86c6fa28fd48b915555048c05bbd37ad35457d9e945953831a4374c886a9c",
}
FRONTEND_NODE_IMAGE_FAILURE = (
    "Stage 8 frontend build and runtime images must retain the reviewed Node image pin."
)


def frontend_node_image_valid(dockerfile: str) -> bool:
    expected = [
        f"FROM {FRONTEND_NODE_SOURCE_IMAGE} AS node-source",
        "FROM scratch AS deps",
        "FROM scratch AS build",
    ]
    actual = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"(?i)^from(?:\s|$)", line.lstrip())
    ]
    return (
        actual == expected
        and ISSUE389_VULNERABLE_RUNTIME_IMAGE not in dockerfile
        and dockerfile.count("COPY --from=node-source /runtime/ /") == 2
        and "process.config.variables.node_use_quic!==false" in dockerfile
        and "process.config.variables.node_shared_openssl!==false" in dockerfile
        and dockerfile.count("apk add --root /runtime --initdb --no-cache --no-scripts") == 1
        and all(
            dockerfile.count(f"{name}={version}") == 1
            for name, version in FRONTEND_RUNTIME_PACKAGES.items()
        )
        and "test -s /runtime/lib/apk/db/installed" in dockerfile
        and "chmod 1777 /runtime/tmp" in dockerfile
        and dockerfile.count("libvips-cpp.so.8.18.3") == 1
        and "COPY scripts/ci/prepare_frontend_npm.mjs /tmp/prepare_frontend_npm.mjs" in dockerfile
        and '["/usr/bin/node", "/tmp/prepare_frontend_npm.mjs"]' in dockerfile
        and '["/usr/bin/node", "/usr/local/lib/node_modules/npm/bin/npm-cli.js", "ci", "--ignore-scripts"]' in dockerfile
        and "--mount=from=deps,source=/app,target=/mnt/deps,readonly" in dockerfile
        and "--mount=type=bind,source=frontend,target=/mnt/frontend,readonly" in dockerfile
        and "await m.assembleFrontendRuntime()" in dockerfile
        and all(
            f"ADD --checksum=sha256:{digest} https://registry.npmjs.org/" in dockerfile
            and f"/tmp/frontend-npm-archives/{filename}" in dockerfile
            for filename, digest in FRONTEND_BUILD_ARCHIVE_SHA256.items()
        )
        and all(marker not in dockerfile.lower() for marker in (
            "glibc", "gcompat", "libatomic", "apt-get", "sha512sum", "npm ci --", "libcrypto", "libssl", "busybox",
            "narratwin-build-nonce", "from deps as build", " as runner",
        ))
    )


def issue376_frontend_builder_valid(dockerfile: str) -> bool:
    return frontend_node_image_valid(dockerfile)


def check_frontend_node_image(dockerfile: str, failures: list[str]) -> None:
    if not frontend_node_image_valid(dockerfile):
        failures.append(FRONTEND_NODE_IMAGE_FAILURE)


def check(root: Path, run: Callable[[list[str]], Any], branch: str, changed_files: list[str], failures: list[str]) -> None:
    check_frontend_node_image((root / "frontend/Dockerfile").read_text(encoding="utf-8"), failures)
    if branch == ISSUE376_SECURITY_BRANCH:
        failures.extend(f"Issue #376 route is missing required path: {path}" for path in sorted(ISSUE376_SECURITY_FILES - set(changed_files)))
        check_issue376_route(root, run, failures, True)
        return
    if branch != ISSUE389_SECURITY_BRANCH:
        return
    failures.extend(f"Issue #389 route is missing required path: {path}" for path in sorted(ISSUE389_SECURITY_FILES - set(changed_files)))
    check_issue389_route(root, run, failures, True)


def _charges(
    output: str, failures: list[str], files: set[str] = ISSUE389_SECURITY_FILES, issue: int = 389
) -> tuple[int, dict[str, int]]:
    total, paths = 0, {}
    for row in output.splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            failures.append(f"Issue #{issue} charged-line evidence is malformed or binary.")
            return 0, {}
        if fields[2] not in files or fields[2] in paths:
            failures.append(f"Issue #{issue} charged-line evidence has a foreign or duplicate path.")
            return 0, {}
        charge = int(fields[0]) + int(fields[1])
        total += charge
        paths[fields[2]] = charge
    return total, paths


def check_issue376_route(
    root: Path, run: Callable[[list[str]], Any], failures: list[str], active: bool
) -> None:
    if not active:
        return
    try:
        preflight = json.loads((root / "docs/governance/preflights/issue-376.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        failures.append("Issue #376 GovernancePreflightV1 is unreadable.")
        return
    scope = preflight.get("scope", {})
    if (
        preflight.get("schema_version") != "GovernancePreflightV1"
        or preflight.get("issue_number") != 376
        or preflight.get("branch") != ISSUE376_SECURITY_BRANCH
        or preflight.get("objective", "").count(ISSUE376_BASE) != 1
        or set(scope.get("required", ())) != ISSUE376_SECURITY_FILES
        or set(scope.get("allowed_prefixes", ())) != ISSUE376_SECURITY_FILES
    ):
        failures.append("Issue #376 preflight identity or exact scope drifted.")
    head = run(["git", "rev-parse", "HEAD^{commit}"])
    merge = run(["git", "merge-base", ISSUE376_BASE, "HEAD"])
    commits = run(["git", "rev-list", "--reverse", f"{ISSUE376_BASE}..HEAD"])
    first_paths = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", ISSUE376_PREFLIGHT_COMMIT])
    rows = commits.stdout.splitlines()
    if (
        head.returncode or merge.returncode or merge.stdout.strip() != ISSUE376_BASE
        or commits.returncode or not rows or rows[0] != ISSUE376_PREFLIGHT_COMMIT
        or first_paths.returncode
        or first_paths.stdout.splitlines() != ["docs/governance/preflights/issue-376.json"]
    ):
        failures.append("Issue #376 must descend from the exact base with a preflight-only first commit.")
        return
    results = [
        run(["git", "diff", "--numstat", "--no-renames", f"{ISSUE376_BASE}..HEAD", "--"]),
        run(["git", "diff", "--cached", "--numstat", "--no-renames", ISSUE376_BASE, "--"]),
        run(["git", "diff", "--numstat", "--no-renames", ISSUE376_BASE, "--"]),
    ]
    untracked = run(["git", "ls-files", "--others", "--exclude-standard", "--"])
    if any(result.returncode for result in results) or untracked.returncode:
        failures.append("Issue #376 charged-line evidence failed closed.")
        return
    if untracked.stdout.strip():
        failures.append("Issue #376 untracked-path evidence is not allowed.")
    snapshots = [_charges(result.stdout, failures, ISSUE376_SECURITY_FILES, 376) for result in results]
    observed = set().union(*(set(snapshot[1]) for snapshot in snapshots))
    if observed != ISSUE376_SECURITY_FILES:
        failures.append("Issue #376 charged-line snapshots do not cover the exact route.")
    if max(snapshot[0] for snapshot in snapshots) > ISSUE376_CHARGE_LIMIT:
        failures.append("Issue #376 exceeds its 1,400 charged-line budget.")


def check_issue389_route(
    root: Path, run: Callable[[list[str]], Any], failures: list[str], active: bool
) -> None:
    if not active:
        return
    try:
        preflight = json.loads((root / "docs/governance/preflights/issue-389.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        failures.append("Issue #389 GovernancePreflightV1 is unreadable.")
        return
    scope = preflight.get("scope", {})
    if (
        preflight.get("schema_version") != "GovernancePreflightV1"
        or preflight.get("issue_number") != 389
        or preflight.get("branch") != ISSUE389_SECURITY_BRANCH
        or preflight.get("objective", "").count(ISSUE389_BASE) != 1
        or set(scope.get("required", ())) != ISSUE389_SECURITY_FILES
        or set(scope.get("allowed_prefixes", ())) != ISSUE389_SECURITY_FILES
    ):
        failures.append("Issue #389 preflight identity or exact scope drifted.")
    head = run(["git", "rev-parse", "HEAD^{commit}"])
    merge = run(["git", "merge-base", ISSUE389_BASE, "HEAD"])
    if (
        head.returncode or merge.returncode
        or not re.fullmatch(r"[0-9a-f]{40}", head.stdout.strip())
        or merge.stdout.strip() != ISSUE389_BASE
    ):
        failures.append("Issue #389 must descend from the exact authorized base.")
        return
    results = [
        run(["git", "diff", "--numstat", "--no-renames", f"{ISSUE389_BASE}..HEAD", "--"]),
        run(["git", "diff", "--cached", "--numstat", "--no-renames", ISSUE389_BASE, "--"]),
        run(["git", "diff", "--numstat", "--no-renames", ISSUE389_BASE, "--"]),
    ]
    untracked = run(["git", "ls-files", "--others", "--exclude-standard", "--"])
    if any(result.returncode for result in results) or untracked.returncode:
        failures.append("Issue #389 charged-line evidence failed closed.")
        return
    if untracked.stdout.strip():
        failures.append("Issue #389 untracked-path evidence is not allowed.")
    charge_sets = [_charges(result.stdout, failures) for result in results]
    observed_paths = set().union(*(set(value[1]) for value in charge_sets))
    if observed_paths != ISSUE389_SECURITY_FILES:
        failures.append("Issue #389 charged-line snapshots do not cover the exact route.")
    total = max(value[0] for value in charge_sets)
    per_file = {
        path: max(values[1].get(path, 0) for values in charge_sets)
        for path in ISSUE389_SECURITY_FILES
    }
    if total > ISSUE389_CHARGE_LIMIT:
        failures.append("Issue #389 exceeds its 900 charged-line budget.")
    for path, limit in ISSUE389_FILE_LIMITS.items():
        if per_file[path] > limit:
            failures.append(f"Issue #389 charge for {path} exceeds {limit}.")
