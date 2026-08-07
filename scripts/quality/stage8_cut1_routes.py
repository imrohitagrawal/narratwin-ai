"""Fail-closed Stage 8 scope and budget routes for governed Cut 1 prerequisites."""
from __future__ import annotations

import re
import stat
from pathlib import Path
from typing import Any, Callable

ISSUE386_BRANCH = "cut1-process-386-modular-route-enforcement"
ISSUE396_BRANCH = "cut1-process-396-js-yaml-4-3-1-security"
ISSUE385_BRANCH = "stage8-385-issue280-language-oracle"
ISSUE384_BRANCH = "stage8-384-presenter-asset-route"
ISSUE383_BRANCH = "stage8-383-presenter-assets"
ISSUE386_BASE = "48fc32a2689c9bbc03742d774f3eadb8a500dafc"

ROUTES = {
    ISSUE396_BRANCH: {
        "docs/governance/preflights/issue-396.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE386_BRANCH: {
        "docs/governance/preflights/issue-386.json",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    ISSUE385_BRANCH: {
        "docs/governance/preflights/issue-385.json",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    ISSUE384_BRANCH: {
        "docs/governance/preflights/issue-384.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE383_BRANCH: {
        "docs/governance/preflights/issue-383.json",
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "tests/unit/test_cut1_presenter_assets.py",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
}
ROUTE_ISSUES = {ISSUE396_BRANCH: 396, ISSUE386_BRANCH: 386, ISSUE385_BRANCH: 385, ISSUE384_BRANCH: 384, ISSUE383_BRANCH: 383}
TOTAL_LIMITS = {ISSUE396_BRANCH: 500, ISSUE386_BRANCH: 700, ISSUE385_BRANCH: 350, ISSUE384_BRANCH: 500, ISSUE383_BRANCH: 700}
ISSUE383_BINARY_FILES = {
    "frontend/public/demo/myra-synthetic-presenter.webp",
    "frontend/public/demo/raj-synthetic-presenter.webp",
}
TEXT_LIMITS = {
    ISSUE396_BRANCH: {
        path: 180 if path.endswith("issue-396.json") else 80 if path.startswith("tests/unit/") else 40
        for path in ROUTES[ISSUE396_BRANCH]
    },
    ISSUE386_BRANCH: {
        path: 300 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py"
        else 20 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path == "scripts/quality/check_stage8_docs.py" else 120
        for path in ROUTES[ISSUE386_BRANCH]
    },
    ISSUE385_BRANCH: {
        path: 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py" else 100
        for path in ROUTES[ISSUE385_BRANCH]
    },
    ISSUE384_BRANCH: {
        path: 10 if path == "scripts/quality/check_stage8_docs.py"
        else 20 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 160 for path in ROUTES[ISSUE384_BRANCH]
    },
    ISSUE383_BRANCH: {
        path: 260 if path == "tests/unit/test_cut1_presenter_assets.py" else 160
        for path in ROUTES[ISSUE383_BRANCH] - ISSUE383_BINARY_FILES
    },
}


def parse_paths_z(output: str) -> list[str]:
    if not output:
        return []
    if not output.endswith("\0"):
        raise RuntimeError("Malformed NUL-delimited Git path output.")
    paths = output[:-1].split("\0")
    if any(not path for path in paths):
        raise RuntimeError("Malformed empty Git path.")
    return paths


def parse_name_status_z(output: str) -> list[str]:
    fields = parse_paths_z(output)
    paths: list[str] = []
    index = 0
    while index < len(fields):
        status_value = fields[index]
        index += 1
        if status_value in {"A", "B", "D", "M", "T", "U"}:
            arity = 1
        elif re.fullmatch(r"[RC]\d{1,3}", status_value) and int(status_value[1:]) <= 100:
            arity = 2
        else:
            raise RuntimeError(f"Malformed Git name-status record: {status_value!r}")
        record_paths = fields[index : index + arity]
        if len(record_paths) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status_value!r}")
        paths.extend(record_paths)
        index += arity
    return paths


def route_base(run: Callable[[list[str]], Any], branch: str) -> str:
    if branch == ISSUE386_BRANCH:
        fixed = run(["git", "rev-parse", f"{ISSUE386_BASE}^{{commit}}"])
        common = run(["git", "merge-base", ISSUE386_BASE, "HEAD"])
        fixed_value = str(fixed.stdout).strip()
        common_value = str(common.stdout).strip()
        if fixed.returncode or common.returncode or fixed_value != ISSUE386_BASE or common_value != ISSUE386_BASE:
            raise RuntimeError("Issue #386 fixed base evidence is unavailable or inconsistent.")
        return ISSUE386_BASE
    current = run(["git", "rev-parse", "origin/main^{commit}"])
    common = run(["git", "merge-base", "origin/main", "HEAD"])
    current_value = str(current.stdout).strip()
    common_value = str(common.stdout).strip()
    if current.returncode or common.returncode or not re.fullmatch(r"[0-9a-f]{40}", current_value):
        raise RuntimeError("Cut 1 current main evidence is unavailable.")
    if common_value != current_value:
        raise RuntimeError("Cut 1 route does not descend from current main.")
    return current_value


def route_text_charges(
    run: Callable[[list[str]], Any], base: str, paths: set[str]
) -> tuple[int, dict[str, int]]:
    ordered = sorted(paths)
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard", "--", *ordered])
    if untracked.returncode:
        raise RuntimeError(untracked.stderr.strip() or "Route untracked-text evidence failed.")
    if untracked.stdout:
        found = parse_paths_z(untracked.stdout)
        raise RuntimeError(f"Route required text path is untracked: {found[0]}")
    snapshots: list[dict[str, int]] = []
    for cached in (True, False):
        charges: dict[str, int] = {}
        for path in ordered:
            args = ["git", "diff"] + (["--cached"] if cached else [])
            result = run([*args, "--numstat", "--no-renames", base, "--", path])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Route charged-line evidence failed.")
            rows = result.stdout.splitlines()
            if len(rows) > 1:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not rows:
                continue
            fields = rows[0].split("\t")
            if len(fields) != 3 or fields[2] != path:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not fields[0].isdigit() or not fields[1].isdigit():
                raise RuntimeError("Route charged-line evidence is malformed or binary.")
            charges[path] = int(fields[0]) + int(fields[1])
        snapshots.append(charges)
    all_paths = set().union(*snapshots)
    return max(sum(snapshot.values()) for snapshot in snapshots), {
        path: max(snapshot.get(path, 0) for snapshot in snapshots) for path in all_paths
    }


def cut1_transition_charges(
    run: Callable[[list[str]], Any], base: str, _paths: set[str]
) -> tuple[int, dict[str, int]]:
    merge = run(["git", "merge-base", base, "HEAD"])
    if merge.returncode or merge.stdout.strip() != base:
        raise RuntimeError("Issue #366 base diff unavailable.")
    results = (
        run(["git", "diff", "--cached", "--numstat", base, "--"]),
        run(["git", "diff", "--numstat", base, "--"]),
    )
    if any(result.returncode for result in results):
        raise RuntimeError("Issue #366 base diff unavailable.")
    try:
        charges = [
            {path: int(added) + int(deleted) for added, deleted, path in
             (line.split("\t") for line in result.stdout.splitlines())}
            for result in results
        ]
    except ValueError as error:
        raise RuntimeError("Issue #366 malformed or binary numstat.") from error
    charged_paths = set().union(*charges)
    return max(sum(snapshot.values()) for snapshot in charges), {
        path: max(snapshot.get(path, 0) for snapshot in charges) for path in charged_paths
    }


def route_binary_sizes(root: Path, paths: set[str]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for path in sorted(paths):
        target = root / path
        try:
            metadata = target.lstat()
        except FileNotFoundError as error:
            raise RuntimeError(f"Route binary is missing: {path}") from error
        if target.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"Route binary must be a regular non-symlink file: {path}")
        if metadata.st_size <= 0:
            raise RuntimeError(f"Route binary is empty: {path}")
        sizes[path] = metadata.st_size
    return sizes


def check_exact_route(
    root: Path, run: Callable[[list[str]], Any], branch: str, changed: set[str], failures: list[str]
) -> None:
    if branch not in ROUTES:
        return
    issue = ROUTE_ISSUES[branch]
    files = ROUTES[branch]
    failures.extend(f"Issue #{issue} route is missing required path: {path}" for path in sorted(files - changed))
    try:
        base = route_base(run, branch)
        total, charges = route_text_charges(run, base, set(TEXT_LIMITS[branch]))
        if total > TOTAL_LIMITS[branch]:
            failures.append(f"Issue #{issue} charge {total} exceeds {TOTAL_LIMITS[branch]}.")
        failures.extend(
            f"Issue #{issue} charge for {path} exceeds {limit}."
            for path, limit in TEXT_LIMITS[branch].items() if charges.get(path, 0) > limit
        )
        if branch == ISSUE383_BRANCH:
            sizes = route_binary_sizes(root, ISSUE383_BINARY_FILES)
            failures.extend(
                f"Issue #383 binary {path} exceeds 500000 bytes."
                for path, size in sizes.items() if size > 500000
            )
    except RuntimeError as error:
        failures.append(f"Issue #{issue} route evidence failed closed: {error}")
