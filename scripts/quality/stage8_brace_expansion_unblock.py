"""Exact Stage 8 route for the Issue #360 dependency-security convergence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

BRANCH = "cut1-process-360-security-brace-expansion-5-0-9-unblock"
BASE, LINE_CAP = "b9a2a8cd4aa05328116565990fc30ae44592c875", 650
ALLOWED_FILES = {
    "docs/governance/preflights/issue-360.json", "docs/QUALITY_GATES.md", "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
    "docs/ADR/0049-semgrep-cryptography-50-lock-refresh.md",
    "docs/ADR/0050-brace-expansion-5-0-9-security-refresh.md", "frontend/package.json", "frontend/package-lock.json",
    "scripts/ci/check_semgrep_security.py", "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_brace_expansion_unblock.py", "tests/unit/test_dependency_security_contract.py",
    "tests/unit/test_stage8_brace_expansion_unblock.py", "tools/semgrep/reviewed-inputs.sha256",
    "tools/semgrep/uv.lock",
}
BRACE_EXPANSION_ROUTES = {BRANCH: ALLOWED_FILES}


def validate_preflight(data: dict[str, Any], failures: list[str]) -> None:
    scope = data.get("scope", {})
    if data.get("schema_version") != "GovernancePreflightV1" or data.get("issue_number") != 360:
        failures.append("Issue #360 GovernancePreflightV1 identity is invalid.")
    if data.get("branch") != BRANCH or data.get("objective", "").count(BASE) != 1:
        failures.append("Issue #360 preflight must bind the exact branch and base once.")
    if set(scope.get("required", ())) != ALLOWED_FILES or set(scope.get("allowed_prefixes", ())) != ALLOWED_FILES:
        failures.append("Issue #360 preflight must require exactly the authorized 18 paths.")


def _git(run: Callable[[list[str]], Any], args: list[str], failures: list[str]) -> str:
    result = run(["git", *args])
    value = result.stdout.strip()
    if result.returncode or not value or "\n" in value:
        failures.append(f"Issue #360 Git evidence failed closed: {' '.join(args)}")
        return ""
    return value


def _check_budget(root: Path, run: Callable[[list[str]], Any], head: str, failures: list[str]) -> None:
    result = run(["git", "diff", "--numstat", "--no-renames", f"{BASE}..{head}", "--"])
    paths: set[str] = set()
    charged = 0
    if result.returncode:
        failures.append("Issue #360 charged-line evidence failed closed.")
        return
    for row in result.stdout.splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not all(value.isdigit() for value in fields[:2]):
            failures.append("Issue #360 charged-line evidence is malformed or binary.")
            return
        charged += int(fields[0]) + int(fields[1])
        paths.add(fields[2])
    if paths != ALLOWED_FILES or charged > LINE_CAP:
        failures.append(f"Issue #360 requires exactly 18 paths and at most {LINE_CAP} charged lines.")
    budgets = {"scripts/quality/check_stage8_docs.py": 500,
               "scripts/quality/stage8_brace_expansion_unblock.py": 120,
               "tests/unit/test_stage8_brace_expansion_unblock.py": 160}
    for path, limit in budgets.items():
        lines = (root / path).read_text(encoding="utf-8").splitlines()
        too_wide = path != "scripts/quality/check_stage8_docs.py" and any(len(line) > 120 for line in lines)
        if len(lines) > limit or too_wide:
            failures.append(f"Issue #360 context budget exceeded for {path}.")


def check_exact_route(
    root: Path, run: Callable[[list[str]], Any], failures: list[str], active: bool
) -> None:
    if not active:
        return
    try:
        data = json.loads((root / "docs/governance/preflights/issue-360.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        failures.append("Issue #360 GovernancePreflightV1 is unreadable.")
        return
    validate_preflight(data, failures)
    base = _git(run, ["rev-parse", f"{BASE}^{{commit}}"], failures)
    head = _git(run, ["rev-parse", "HEAD^{commit}"], failures)
    common = _git(run, ["merge-base", BASE, head], failures) if head else ""
    if base != BASE or common != BASE or not re.fullmatch(r"[0-9a-f]{40}", head):
        failures.append("Issue #360 must descend from the exact authorized base.")
    if head:
        _check_budget(root, run, head, failures)
