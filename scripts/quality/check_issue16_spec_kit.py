#!/usr/bin/env python3
"""Validate the governance-only Issue #16 specification kit."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "6f2bfebf794ca6263b6cb42f65bbdc8328cc8e5a"
ACCEPTED_SHA = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
ISSUE16_BRANCH = "stage1-16-spec-kit-gate"
PREFLIGHT = "docs/governance/preflights/issue-16.json"
TOTAL_CHARGED_LINE_CAP = 2_400
EXPECTED_PATHS = (
    "docs/governance/preflights/issue-16.json", ".specify/memory/constitution.md",
    "specs/001-grounded-walkthrough-script/spec.md", "specs/001-grounded-walkthrough-script/plan.md",
    "specs/001-grounded-walkthrough-script/tasks.md", "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md",
    "scripts/quality/check_issue16_spec_kit.py", "tests/unit/test_issue16_spec_kit_gate.py",
    "scripts/quality/check_quality_stage.py", "Makefile", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
)
EXPECTED_FORBIDDEN = (
    "backend/", "frontend/", "rag/", "providers/", "avatar/", "assets/", "data/",
    ".github/workflows/", "docker-compose.yml", "pyproject.toml", "uv.lock",
    "package.json", "package-lock.json", ".env", ".env.example",
)

REQUIRED_MARKDOWN = (
    ".specify/memory/constitution.md",
    "specs/001-grounded-walkthrough-script/spec.md",
    "specs/001-grounded-walkthrough-script/plan.md",
    "specs/001-grounded-walkthrough-script/tasks.md",
    "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
)

REQUIRED_FILES = (*REQUIRED_MARKDOWN, "Makefile", ".stage/current")

_MARKERS = {
    ".specify/memory/constitution.md": (
        "No implementation before the gate",
        "I16.CONSTITUTION.PRINCIPLE",
    ),
    "specs/001-grounded-walkthrough-script/plan.md": (
        "Gate order: constitution -> spec -> plan -> tasks -> review checkpoint -> future issue",
        "I16.PLAN.ORDER",
    ),
    "specs/001-grounded-walkthrough-script/tasks.md": (
        "Future Lane A Cut 1 issue: TBD after Issue #16 closes",
        "I16.ISSUE.SEQUENCING",
    ),
    "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md": (
        "REVIEWED_PENDING_IMPLEMENTATION_ISSUE",
        "I16.REVIEW.CHECKPOINT",
    ),
    "docs/STATUS.md": (
        "Issue #16 specification-gate target state",
        "I16.STATUS.TARGET",
    ),
    "docs/TRACEABILITY.md": ("I16-GATE-01", "I16.TRACEABILITY"),
    "docs/QUALITY_GATES.md": ("make issue16-spec-quality", "I16.QUALITY.DOC"),
    "docs/STAGE_ISSUE_PLAN.md": ("Post-gate Lane A sequencing", "I16.STAGE.PLAN"),
}

_STALE_STATUS_MARKER = "Issue #456 Cut 1 live-binding prerequisite — merged and closed"
_TASK_ID = re.compile(r"LA-C1-T\d{2}")
_TASK_ROW = re.compile(r"^\|\s*(LA-C1-T\d{2})\s*\|")
_EXPECTED_TASK_IDS = tuple(f"LA-C1-T{number:02d}" for number in range(1, 9))
_REQUIREMENT_ID = re.compile(r"\b(?:N?FR)-\d{3}\b")
_EXPECTED_REQUIREMENT_IDS = {
    *(f"FR-{number:03d}" for number in range(1, 10)),
    *(f"NFR-{number:03d}" for number in range(1, 13)),
}
_ACTIVATION_CLAIM = re.compile(
    r"\b(?:github\s+)?spec kit is installed and activated for this repository\b",
    re.IGNORECASE,
)


def load_preflight(root: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / PREFLIGHT).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_preflight(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _path_cap(path: str) -> int:
    if path in {
        "scripts/quality/check_issue16_spec_kit.py",
        "tests/unit/test_issue16_spec_kit_gate.py",
    }:
        return 320
    if path.startswith("specs/001-grounded-walkthrough-script/"):
        return 420
    return 300


def validate_scope_snapshot(
    artifact: dict[str, Any],
    *,
    branch: str,
    base_is_ancestor: bool,
    changed_files: list[str],
    charged_lines: dict[str, int],
) -> list[str]:
    failures: list[str] = []
    scope = artifact.get("scope")
    required = scope.get("required") if isinstance(scope, dict) else None
    allowed = scope.get("allowed_prefixes") if isinstance(scope, dict) else None
    forbidden = scope.get("forbidden") if isinstance(scope, dict) else None
    binding_valid = (
        artifact.get("schema_version") == "GovernancePreflightV1"
        and artifact.get("issue_number") == 16
        and artifact.get("branch") == ISSUE16_BRANCH
        and branch == ISSUE16_BRANCH
    )
    if not binding_valid:
        failures.append("I16.SCOPE.BINDING")
    if not base_is_ancestor:
        failures.append("I16.SCOPE.HISTORY")
    if (
        not isinstance(required, list) or tuple(required) != EXPECTED_PATHS
        or not isinstance(allowed, list) or tuple(allowed) != EXPECTED_PATHS
        or not isinstance(forbidden, list) or tuple(forbidden) != EXPECTED_FORBIDDEN
        or len(changed_files) != len(set(changed_files))
        or set(changed_files) != set(EXPECTED_PATHS)
        or set(charged_lines) != set(changed_files)
    ):
        failures.append("I16.SCOPE.PATHS")
    if any(
        not isinstance(lines, int) or lines < 0 or lines > _path_cap(path)
        for path, lines in charged_lines.items()
    ):
        failures.append("I16.SCOPE.FILE_BUDGET")
    if sum(lines for lines in charged_lines.values() if isinstance(lines, int)) > TOTAL_CHARGED_LINE_CAP:
        failures.append("I16.SCOPE.TOTAL_BUDGET")
    return failures


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["/usr/bin/git", *args],
        cwd=root,
        env={
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_LAZY_FETCH": "1",
        },
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )


def _branch_identity(git_branch: str) -> str:
    if git_branch or os.environ.get("GITHUB_ACTIONS") != "true":
        return git_branch
    return os.environ.get("GITHUB_HEAD_REF", "")


def current_branch(root: Path) -> str:
    result = _git(root, "branch", "--show-current")
    if result.returncode != 0:
        raise RuntimeError("branch unavailable")
    return _branch_identity(result.stdout.decode("utf-8", errors="replace").strip())


def _paths(raw: bytes) -> list[str]:
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    ]


def _charged_lines(raw: bytes) -> dict[str, int]:
    charged: dict[str, int] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        fields = record.split(b"\t", 2)
        if len(fields) != 3 or fields[0] == b"-" or fields[1] == b"-" or not fields[2]:
            raise RuntimeError("unsupported numstat record")
        path = fields[2].decode("utf-8", errors="surrogateescape")
        if path in charged:
            raise RuntimeError("duplicate numstat record")
        charged[path] = int(fields[0]) + int(fields[1])
    return charged


def repository_snapshot(root: Path) -> tuple[str, bool, list[str], dict[str, int]]:
    ancestor_result = _git(root, "merge-base", "--is-ancestor", BASE_SHA, "HEAD")
    names_result = _git(root, "diff", "--name-only", "-z", BASE_SHA, "--")
    untracked_result = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    numstat_result = _git(root, "diff", "--numstat", "-z", BASE_SHA, "--")
    results = (names_result, untracked_result, numstat_result)
    if any(result.returncode != 0 or (result.stdout and not result.stdout.endswith(b"\0")) for result in results):
        raise RuntimeError("repository snapshot unavailable")
    changed = _paths(names_result.stdout)
    untracked = _paths(untracked_result.stdout)
    changed.extend(path for path in untracked if path not in changed)
    return (
        current_branch(root),
        ancestor_result.returncode == 0,
        changed,
        _charged_lines(numstat_result.stdout),
    )


def _historical_text(root: Path, relative: str) -> str:
    result = _git(root, "show", f"{ACCEPTED_SHA}:{relative}")
    if result.returncode != 0:
        raise RuntimeError(f"accepted artifact unavailable: {relative}")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"accepted artifact is not UTF-8: {relative}") from error


def historical_snapshot(
    root: Path,
) -> tuple[dict[str, str], dict[str, Any], bool, list[str], dict[str, int]]:
    """Return the immutable accepted Issue #16 contract and exact route."""

    content = {relative: _historical_text(root, relative) for relative in REQUIRED_FILES}
    artifact = _parse_preflight(_historical_text(root, PREFLIGHT))
    ancestor = _git(root, "merge-base", "--is-ancestor", BASE_SHA, ACCEPTED_SHA)
    names = _git(root, "diff", "--name-only", "-z", BASE_SHA, ACCEPTED_SHA, "--")
    numstat = _git(root, "diff", "--numstat", "-z", BASE_SHA, ACCEPTED_SHA, "--")
    if ancestor.returncode not in {0, 1}:
        raise RuntimeError("accepted ancestry unavailable")
    for result in (names, numstat):
        if result.returncode != 0 or (result.stdout and not result.stdout.endswith(b"\0")):
            raise RuntimeError("accepted route unavailable")
    return content, artifact, ancestor.returncode == 0, _paths(names.stdout), _charged_lines(numstat.stdout)


def _read_contract(root: Path, failures: list[str]) -> dict[str, str]:
    content: dict[str, str] = {}
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            if "I16.ARTIFACT.MISSING" not in failures:
                failures.append("I16.ARTIFACT.MISSING")
            continue
        try:
            content[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            if "I16.ARTIFACT.MISSING" not in failures:
                failures.append("I16.ARTIFACT.MISSING")
    return content


def _check_markers(content: dict[str, str], failures: list[str]) -> None:
    for relative, (markers, code) in _MARKERS.items():
        text = content.get(relative)
        if text is None:
            continue
        required = (markers,) if isinstance(markers, str) else markers
        if any(marker not in text for marker in required):
            failures.append(code)

    status = content.get("docs/STATUS.md")
    if status is not None and _STALE_STATUS_MARKER not in status:
        failures.append("I16.STATUS.STALE_456")

    spec = content.get("specs/001-grounded-walkthrough-script/spec.md")
    if spec is not None and set(_REQUIREMENT_ID.findall(spec)) != _EXPECTED_REQUIREMENT_IDS:
        failures.append("I16.SPEC.REQUIREMENT")

    makefile = content.get("Makefile")
    if makefile is not None and not re.search(r"^issue16-spec-quality:\s*$", makefile, re.MULTILINE):
        failures.append("I16.MAKE.TARGET")

    stage = content.get(".stage/current")
    if stage is not None and stage.strip() != "8":
        failures.append("I16.STAGE.CURRENT")


def _check_task_graph(tasks: str | None, failures: list[str]) -> None:
    if tasks is None:
        return

    rows: list[tuple[str, str]] = []
    for line in tasks.splitlines():
        match = _TASK_ROW.match(line)
        if match:
            rows.append((match.group(1), line[match.end() :]))

    task_ids = tuple(task_id for task_id, _ in rows)
    if task_ids != _EXPECTED_TASK_IDS:
        failures.append("I16.TASK.IDS")

    known: set[str] = set()
    dependency_error = False
    for task_id, remaining_cells in rows:
        for dependency in _TASK_ID.findall(remaining_cells):
            if dependency not in known:
                dependency_error = True
        known.add(task_id)
    if dependency_error:
        failures.append("I16.TASK.DEPENDENCY")


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    scope_snapshot: tuple[dict[str, Any], str, bool, list[str], dict[str, int]] | None = None
    if (root / ".git").exists():
        try:
            branch = current_branch(root)
        except (OSError, subprocess.SubprocessError, RuntimeError, ValueError):
            return ["I16.SCOPE.HISTORY"]
        if branch == ISSUE16_BRANCH:
            content = _read_contract(root, failures)
            try:
                live_branch, ancestor, changed, charged = repository_snapshot(root)
            except (OSError, subprocess.SubprocessError, RuntimeError, ValueError):
                failures.append("I16.SCOPE.HISTORY")
            else:
                scope_snapshot = (load_preflight(root), live_branch, ancestor, changed, charged)
        else:
            try:
                content, artifact, ancestor, changed, charged = historical_snapshot(root)
            except (OSError, subprocess.SubprocessError, RuntimeError, ValueError):
                return ["I16.HISTORICAL.SNAPSHOT"]
            scope_snapshot = (artifact, ISSUE16_BRANCH, ancestor, changed, charged)
    else:
        content = _read_contract(root, failures)

    _check_markers(content, failures)
    _check_task_graph(
        content.get("specs/001-grounded-walkthrough-script/tasks.md"), failures
    )

    constitution = content.get(".specify/memory/constitution.md")
    if constitution is not None and _ACTIVATION_CLAIM.search(constitution):
        failures.append("I16.SPECKIT.ACTIVATION")

    if scope_snapshot is not None:
        artifact, branch, ancestor, changed, charged = scope_snapshot
        failures.extend(
            validate_scope_snapshot(
                artifact,
                branch=branch,
                base_is_ancestor=ancestor,
                changed_files=changed,
                charged_lines=charged,
            )
        )

    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Issue #16 specification kit gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
