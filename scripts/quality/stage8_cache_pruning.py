"""Fail-closed Stage 8 route and repository-owned Python iterator for Issue #375."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Iterator

BRANCH = "stage8-375-prune-ignored-caches"
BASE, LINE_CAP = "f2312947ef670becfa0373000c8ae6ef1f411e20", 600
ALLOWED_FILES = {
    "docs/governance/preflights/issue-375.json", "docs/QUALITY_GATES.md", "docs/STATUS.md",
    "scripts/quality/check_stage8_docs.py", "scripts/quality/stage8_a23b.py",
    "scripts/quality/stage8_cache_pruning.py", "tests/unit/test_stage8_cache_pruning.py",
}
CACHE_PRUNING_ROUTES = {BRANCH: ALLOWED_FILES}
IGNORED_DIRECTORY_NAMES = {
    ".git", ".venv", "venv", ".uv-cache", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__",
    "node_modules", "outputs", "reports", ".codex", ".next", "dist", "build", ".chroma",
    ".wednesday", ".claude",
}


def _raise_walk_error(error: OSError) -> None:
    raise error


def repository_python_files(root: Path) -> Iterator[Path]:
    """Yield owned Python files deterministically without entering ignored or linked directories."""
    for directory, directories, files in root.walk(
        top_down=True, on_error=_raise_walk_error, follow_symlinks=False
    ):
        directories[:] = sorted(
            name for name in directories
            if name not in IGNORED_DIRECTORY_NAMES and not (directory / name).is_symlink()
        )
        for name in sorted(files):
            path = directory / name
            if path.suffix == ".py" and not path.is_symlink():
                yield path


def validate_preflight(data: dict[str, Any], failures: list[str]) -> None:
    scope = data.get("scope", {})
    if data.get("schema_version") != "GovernancePreflightV1" or data.get("issue_number") != 375:
        failures.append("Issue #375 GovernancePreflightV1 identity is invalid.")
    if data.get("branch") != BRANCH or data.get("objective", "").count(BASE) != 1:
        failures.append("Issue #375 preflight must bind the exact branch and base once.")
    if set(scope.get("required", ())) != ALLOWED_FILES or set(scope.get("allowed_prefixes", ())) != ALLOWED_FILES:
        failures.append("Issue #375 preflight must require exactly the authorized 7 paths.")


def _git(run: Callable[[list[str]], Any], args: list[str], failures: list[str]) -> str:
    result = run(["git", *args])
    value = str(getattr(result, "stdout", "")).strip()
    if getattr(result, "returncode", 1) or not re.fullmatch(r"[0-9a-f]{40}", value):
        failures.append(f"Issue #375 Git evidence failed closed: {' '.join(args)}")
        return ""
    return value


def _check_budget(root: Path, run: Callable[[list[str]], Any], head: str, failures: list[str]) -> None:
    result = run(["git", "diff", "--numstat", "--no-renames", f"{BASE}..{head}", "--"])
    paths: set[str] = set()
    charged = 0
    if getattr(result, "returncode", 1):
        failures.append("Issue #375 charged-line evidence failed closed.")
        return
    for row in str(result.stdout).splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not all(value.isdigit() for value in fields[:2]):
            failures.append("Issue #375 charged-line evidence is malformed or binary.")
            return
        charged += int(fields[0]) + int(fields[1])
        paths.add(fields[2])
    if paths != ALLOWED_FILES or charged > LINE_CAP:
        failures.append(f"Issue #375 requires exactly 7 paths and at most {LINE_CAP} charged lines.")
    budgets = {
        "scripts/quality/check_stage8_docs.py": 500,
        "scripts/quality/stage8_cache_pruning.py": 140,
        "tests/unit/test_stage8_cache_pruning.py": 180,
    }
    for path, limit in budgets.items():
        lines = (root / path).read_text(encoding="utf-8").splitlines()
        too_wide = path != "scripts/quality/check_stage8_docs.py" and any(len(line) > 120 for line in lines)
        if len(lines) > limit or too_wide:
            failures.append(f"Issue #375 context budget exceeded for {path}.")


def check_exact_route(
    root: Path, run: Callable[[list[str]], Any], failures: list[str], active: bool
) -> None:
    if not active:
        return
    try:
        data = json.loads((root / "docs/governance/preflights/issue-375.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        failures.append("Issue #375 GovernancePreflightV1 is unreadable.")
        return
    validate_preflight(data, failures)
    base = _git(run, ["rev-parse", f"{BASE}^{{commit}}"], failures)
    head = _git(run, ["rev-parse", "HEAD^{commit}"], failures)
    common = _git(run, ["merge-base", BASE, head], failures) if head else ""
    if base != BASE or common != BASE or not head:
        failures.append("Issue #375 must descend from the exact authorized base.")
    if head:
        _check_budget(root, run, head, failures)
