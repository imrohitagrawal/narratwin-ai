"""Issue #436 backend CPython and TLS capability-isolation contracts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from scripts.quality import stage8_node_security as node_security

ISSUE436_BRANCH = "stage8-436-backend-tls-capability-isolation-r4"
ISSUE436_BASE = "87b8504ca8d5e094394343aeaa4ef5bad46133d5"
ISSUE436_STACK_BASE = "6bcdb8d60ebb4d1e5fef3725cffc459dd5525987"
ISSUE436_PREFLIGHT_COMMIT = "733122fb3e743813bcd54ea0cd69a558d9625fe9"
ISSUE436_CHARGE_LIMIT = 1400
ISSUE436_FILES = {
    "docs/governance/preflights/issue-436.json",
    "backend/Dockerfile",
    "scripts/quality/stage8_backend_security.py",
    "scripts/quality/check_stage8_docs.py",
    "scripts/ci/backend-image-package-check.sh",
    "tests/unit/test_stage8_backend_security.py",
    "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_backend_image_package_check.py",
    "tests/unit/test_cpython_security_backports.py",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
ISSUE436_STACK_FILES = ISSUE436_FILES | node_security.ISSUE376_SECURITY_FILES
ISSUE436_ROUTES = {ISSUE436_BRANCH: ISSUE436_STACK_FILES}
BACKEND_BASE_IMAGE = (
    "docker.io/library/alpine:3.21@sha256:"
    "48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d"
)
CPYTHON_VERSION = "3.13.15"
CPYTHON_SHA256 = "1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76"


def backend_dockerfile_valid(dockerfile: str) -> bool:
    from_lines = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"(?i)^from(?:\s|$)", line.lstrip())
    ]
    required = (
        f"ENV PYTHON_VERSION={CPYTHON_VERSION}",
        f"ENV PYTHON_SHA256={CPYTHON_SHA256}",
        '"https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"',
        'echo "$PYTHON_SHA256 *python.tar.xz" | sha256sum -c -',
        "gpg --batch --verify python.tar.xz.asc python.tar.xz",
        "libcrypto3=3.3.7-r0",
        "libssl3=3.3.7-r0",
        "/runtime/lib/apk/db/installed",
        "COPY --from=cpython-build /runtime/ /",
        "USER 10001:10001",
        "SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt",
    )
    return (
        from_lines
        == [
            f"FROM {BACKEND_BASE_IMAGE} AS cpython-build",
            "FROM cpython-build AS backend-build",
            "FROM scratch",
        ]
        and dockerfile.count(BACKEND_BASE_IMAGE) == 1
        and all(marker in dockerfile for marker in required)
        and "3.5.7-r0" not in dockerfile
        and "python:3.13-alpine" not in dockerfile
        and not re.search(r"(?i)rm[^\n]*(?:/lib/apk/db|/runtime/lib/apk/db)", dockerfile)
    )


def _charge(output: str, failures: list[str]) -> tuple[int, set[str]]:
    total = 0
    paths: set[str] = set()
    for row in output.splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            failures.append("Issue #436 charged-line evidence is malformed or binary.")
            return 0, set()
        path = fields[2]
        if path not in ISSUE436_FILES or path in paths:
            failures.append("Issue #436 charged-line evidence has a foreign or duplicate path.")
            return 0, set()
        total += int(fields[0]) + int(fields[1])
        paths.add(path)
    return total, paths


def check_route(root: Path, run: Callable[[list[str]], Any], failures: list[str]) -> None:
    try:
        preflight = json.loads(
            (root / "docs/governance/preflights/issue-436.json").read_text(encoding="utf-8")
        )
    except (OSError, TypeError, ValueError):
        failures.append("Issue #436 GovernancePreflightV1 is unreadable.")
        return
    scope = preflight.get("scope", {})
    if (
        preflight.get("schema_version") != "GovernancePreflightV1"
        or preflight.get("issue_number") != 436
        or preflight.get("branch") != ISSUE436_BRANCH
        or preflight.get("objective", "").count(ISSUE436_BASE) != 1
        or set(scope.get("required", ())) != ISSUE436_FILES
        or set(scope.get("allowed_prefixes", ())) != ISSUE436_FILES
    ):
        failures.append("Issue #436 preflight identity or exact scope drifted.")
    merge = run(["git", "merge-base", ISSUE436_STACK_BASE, "HEAD"])
    ancestry = run(["git", "merge-base", "--is-ancestor", ISSUE436_STACK_BASE, "HEAD"])
    commits = run(["git", "rev-list", "--first-parent", "--reverse", f"{ISSUE436_BASE}..HEAD"])
    first_paths = run(
        [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            ISSUE436_PREFLIGHT_COMMIT,
        ]
    )
    results = [
        run(["git", "diff", "--numstat", "--no-renames", f"{ISSUE436_STACK_BASE}..HEAD", "--"]),
        run(["git", "diff", "--cached", "--numstat", "--no-renames", ISSUE436_STACK_BASE, "--"]),
        run(["git", "diff", "--numstat", "--no-renames", ISSUE436_STACK_BASE, "--"]),
    ]
    untracked = run(["git", "ls-files", "--others", "--exclude-standard", "--"])
    commit_rows = commits.stdout.splitlines()
    if (
        merge.returncode
        or merge.stdout.strip() != ISSUE436_STACK_BASE
        or ancestry.returncode
        or commits.returncode
        or not commit_rows
        or commit_rows[0] != ISSUE436_PREFLIGHT_COMMIT
        or first_paths.returncode
        or first_paths.stdout.splitlines() != ["docs/governance/preflights/issue-436.json"]
        or any(result.returncode for result in (*results, untracked))
    ):
        failures.append("Issue #436 base, first commit, or charged-line evidence failed closed.")
        return
    if untracked.stdout.strip():
        failures.append("Issue #436 untracked-path evidence is not allowed.")
    charges = [_charge(result.stdout, failures) for result in results]
    observed = set().union(*(paths for _, paths in charges))
    if observed != ISSUE436_FILES:
        failures.append("Issue #436 charged-line snapshots do not cover the exact route.")
    if max(total for total, _ in charges) > ISSUE436_CHARGE_LIMIT:
        failures.append("Issue #436 exceeds its 1,400 charged-line budget.")


def check(
    root: Path,
    run: Callable[[list[str]], Any],
    branch: str,
    failures: list[str],
) -> None:
    dockerfile = (root / "backend/Dockerfile").read_text(encoding="utf-8")
    if not backend_dockerfile_valid(dockerfile):
        failures.append("Stage 8 backend CPython and TLS image contract drifted.")
    if branch == ISSUE436_BRANCH:
        check_route(root, run, failures)
