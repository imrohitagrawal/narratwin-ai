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
    "docs/governance/preflights/issue-389.json", "frontend/Dockerfile",
    "scripts/ci/docker-image-scan.sh", "scripts/ci/check_container_scan_consensus.py",
    "scripts/quality/check_stage8_docs.py", "scripts/quality/stage8_node_security.py",
    "tests/unit/test_container_scan_consensus.py", "tests/unit/test_stage8_node_security.py",
    "docs/ADR/0006-stage8-release-hardening.md", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
I389_ROUTES = {ISSUE389_SECURITY_BRANCH: ISSUE389_SECURITY_FILES}
FRONTEND_NODE_BUILD_IMAGE = (
    "node:26.6.0-alpine@sha256:"
    "a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8"
)
FRONTEND_NODE_RUNTIME_IMAGE = (
    "cgr.dev/chainguard/node:latest@sha256:"
    "d8d2883b26d4fde4e524d0068cd78abbb23c7c2113a22e67a02cc73a9182552d"
)
ISSUE389_VULNERABLE_RUNTIME_IMAGE = (
    "cgr.dev/chainguard/node:latest@sha256:"
    "cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734"
)
FRONTEND_RUNTIME_NODE_VERSION = "26.7.0"
FRONTEND_RUNTIME_NPM_PACKAGE = "npm-12 12.0.2-r2"
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
FRONTEND_NODE_IMAGE_FAILURE = (
    "Stage 8 frontend build and runtime images must retain the reviewed Node image pin."
)


def frontend_node_image_valid(dockerfile: str) -> bool:
    expected = [
        f"FROM {FRONTEND_NODE_BUILD_IMAGE} AS deps",
        "FROM deps AS build",
        f"FROM {FRONTEND_NODE_RUNTIME_IMAGE} AS runner",
    ]
    actual = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"(?i)^from(?:\s|$)", line.lstrip())
    ]
    return (
        actual == expected
        and dockerfile.count("sha512sum -c -") == len(FRONTEND_BUILD_ARCHIVE_SHA512)
        and all(
            package in dockerfile and f"echo '{digest}  /tmp/" in dockerfile
            for package, digest in FRONTEND_BUILD_ARCHIVE_SHA512.items()
        )
    )


def check_frontend_node_image(dockerfile: str, failures: list[str]) -> None:
    if not frontend_node_image_valid(dockerfile):
        failures.append(FRONTEND_NODE_IMAGE_FAILURE)


def check(
    root: Path,
    run: Callable[[list[str]], Any],
    branch: str,
    changed_files: list[str],
    failures: list[str],
) -> None:
    check_frontend_node_image(
        (root / "frontend/Dockerfile").read_text(encoding="utf-8"), failures
    )
    if branch != ISSUE389_SECURITY_BRANCH:
        return
    failures.extend(
        f"Issue #389 route is missing required path: {path}"
        for path in sorted(ISSUE389_SECURITY_FILES - set(changed_files))
    )
    check_issue389_route(root, run, failures, True)


def _charges(output: str, failures: list[str]) -> tuple[int, dict[str, int]]:
    total, paths = 0, {}
    for row in output.splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            failures.append("Issue #389 charged-line evidence is malformed or binary.")
            return 0, {}
        if fields[2] not in ISSUE389_SECURITY_FILES or fields[2] in paths:
            failures.append("Issue #389 charged-line evidence has a foreign or duplicate path.")
            return 0, {}
        charge = int(fields[0]) + int(fields[1])
        total += charge
        paths[fields[2]] = charge
    return total, paths


def check_issue389_route(
    root: Path, run: Callable[[list[str]], Any], failures: list[str], active: bool
) -> None:
    if not active:
        return
    try:
        preflight = json.loads(
            (root / "docs/governance/preflights/issue-389.json").read_text(encoding="utf-8")
        )
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
