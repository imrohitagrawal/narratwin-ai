"""Fail-closed Stage 8 scope and budget routes for governed Cut 1 prerequisites."""
from __future__ import annotations

import re
import stat
from pathlib import Path
from typing import Any, Callable

ISSUE386_BRANCH = "cut1-process-386-modular-route-enforcement"
ISSUE405_BRANCH = "process-405-heartbeat2-main-reliability"
ISSUE403_BRANCH = "cut1-process-403-nanoid-3-3-17-security"
ISSUE401_BRANCH = "cut1-process-401-pypdf-6-15-0-security"
ISSUE396_BRANCH = "cut1-process-396-js-yaml-4-3-1-security"
ISSUE385_BRANCH = "stage8-385-issue280-language-oracle"
ISSUE384_BRANCH = "stage8-384-presenter-asset-route"
ISSUE383_BRANCH = "stage8-383-presenter-assets"
ISSUE382_BRANCH = "stage8-382-cut1-narration-lock"
ISSUE367_BRANCH = "stage8-367-presenter-registry"
ISSUE397_BRANCH = "stage8-397-presenter-asset-adr-classifier"
ISSUE393_BRANCH = "stage8-393-historical-digest-test-isolation"
ISSUE368_BRANCH = "stage8-368-cut1-local-tts-audio"
ISSUE386_BASE = "48fc32a2689c9bbc03742d774f3eadb8a500dafc"
ISSUE368_BASE = "ef9cabc23762560912d99f10831241b8a65b869c"

ROUTES = {
    ISSUE368_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE382_BRANCH: {
        "docs/governance/preflights/issue-382.json",
        "backend/app/narration.py",
        "tests/unit/test_cut1_narration.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0055-cut1-narration-speech-lock.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE405_BRANCH: {
        "docs/governance/preflights/issue-405.json",
        ".github/workflows/ci.yml",
        "scripts/ci/heartbeat2-browser.sh",
        "scripts/ci/heartbeat2_evidence.py",
        "tests/unit/test_heartbeat2_evidence.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
    },
    ISSUE403_BRANCH: {
        "docs/governance/preflights/issue-403.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/ADR/0053-nanoid-3-3-17-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE401_BRANCH: {
        "docs/governance/preflights/issue-401.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0052-pypdf-6-15-0-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE396_BRANCH: {
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
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
    ISSUE367_BRANCH: {
        "docs/governance/preflights/issue-367.json",
        "backend/app/presenter_registry.py",
        "backend/app/presenter_registry.json",
        "tests/unit/test_cut1_presenter_registry.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0054-cut1-presenter-registry.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE397_BRANCH: {
        "docs/governance/preflights/issue-397.json",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE393_BRANCH: {
        "docs/governance/preflights/issue-393.json",
        "docs/governance/preflights/issue-396.json",
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
}
ROUTE_ISSUES = {ISSUE368_BRANCH: 368, ISSUE405_BRANCH: 405, ISSUE403_BRANCH: 403, ISSUE401_BRANCH: 401, ISSUE396_BRANCH: 396,
                ISSUE386_BRANCH: 386, ISSUE385_BRANCH: 385,
                ISSUE384_BRANCH: 384, ISSUE383_BRANCH: 383, ISSUE397_BRANCH: 397,
                ISSUE393_BRANCH: 393, ISSUE382_BRANCH: 382, ISSUE367_BRANCH: 367}
TOTAL_LIMITS = {ISSUE368_BRANCH: 3200, ISSUE405_BRANCH: 800, ISSUE403_BRANCH: 650, ISSUE401_BRANCH: 600, ISSUE396_BRANCH: 500,
                ISSUE386_BRANCH: 700, ISSUE385_BRANCH: 350,
                ISSUE384_BRANCH: 500, ISSUE383_BRANCH: 700, ISSUE397_BRANCH: 500,
                ISSUE393_BRANCH: 700, ISSUE382_BRANCH: 3200, ISSUE367_BRANCH: 2000}
ISSUE383_BINARY_FILES = {
    "frontend/public/demo/myra-synthetic-presenter.webp",
    "frontend/public/demo/raj-synthetic-presenter.webp",
}
TEXT_LIMITS = {
    ISSUE368_BRANCH: {
        path: 1200 if path == "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md"
        else 500 if path == "docs/ADR/0056-cut1-google-gemini-tts.md"
        else 300 if path == "docs/governance/preflights/issue-368.json"
        else 220 if path in {"docs/SECURITY_AND_PRIVACY.md", "docs/OBSERVABILITY_AND_COST.md",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 180 if path == "scripts/quality/stage8_cut1_routes.py" else 160
        for path in ROUTES[ISSUE368_BRANCH]
    },
    ISSUE382_BRANCH: {
        path: 220 if path.endswith("issue-382.json") or path.startswith("docs/ADR/0055-")
        else 750 if path == "backend/app/narration.py"
        else 900 if path == "tests/unit/test_cut1_narration.py"
        else 120 for path in ROUTES[ISSUE382_BRANCH]
    },
    ISSUE405_BRANCH: {
        path: 220 if path.endswith("issue-405.json") else 160
        for path in ROUTES[ISSUE405_BRANCH]
    },
    ISSUE403_BRANCH: {
        path: 180 if path.endswith("issue-403.json")
        else 110 if path == "tests/unit/test_frontend_dependency_security_contract.py"
        else 80 if path in {"scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"}
        else 70 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE403_BRANCH]
    },
    ISSUE401_BRANCH: {
        path: 190 if path.endswith("issue-401.json")
        else 100 if path.startswith("tests/unit/")
        else 80 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE401_BRANCH]
    },
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
    ISSUE367_BRANCH: {
        path: 500 if path in {"backend/app/presenter_registry.py",
                              "tests/unit/test_cut1_presenter_registry.py"}
        else 260 if path == "backend/app/presenter_registry.json"
        else 220 if path in {"docs/governance/preflights/issue-367.json",
                             "docs/ADR/0054-cut1-presenter-registry.md"}
        else 180 if path in {"scripts/quality/stage8_cut1_routes.py",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 120 for path in ROUTES[ISSUE367_BRANCH]
    },
    ISSUE397_BRANCH: {
        path: 160 if path in {"docs/governance/preflights/issue-397.json",
                             "tests/unit/test_guardrails_check.py"}
        else 100 if path == "scripts/guardrails_check.py"
        else 10 if path == "docs/agent-context/context-policy-manifest-v1.json" else 80
        for path in ROUTES[ISSUE397_BRANCH]
    },
    ISSUE393_BRANCH: {
        path: 180 if path.endswith(("issue-393.json", "issue-396.json"))
        else 160 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
                            "tests/unit/test_dependency_security_contract.py",
                            "scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"} else 40
        for path in ROUTES[ISSUE393_BRANCH]
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
    fixed_routes = {ISSUE368_BRANCH: (368, ISSUE368_BASE), ISSUE386_BRANCH: (386, ISSUE386_BASE)}
    if branch in fixed_routes:
        issue, base = fixed_routes[branch]
        fixed = run(["git", "rev-parse", f"{base}^{{commit}}"])
        common = run(["git", "merge-base", base, "HEAD"])
        fixed_value = str(fixed.stdout).strip()
        common_value = str(common.stdout).strip()
        branch_point_invalid = False
        if branch == ISSUE368_BRANCH:
            branch_point = run(["git", "merge-base", "origin/main", "HEAD"])
            branch_point_invalid = branch_point.returncode != 0 or str(branch_point.stdout).strip() != base
        if (fixed.returncode or common.returncode or fixed_value != base or common_value != base
                or branch_point_invalid):
            raise RuntimeError(f"Issue #{issue} fixed base evidence is unavailable or inconsistent.")
        return base
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
