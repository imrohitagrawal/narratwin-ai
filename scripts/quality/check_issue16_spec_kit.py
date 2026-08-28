#!/usr/bin/env python3
"""Validate the governance-only Issue #16 specification kit."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "6f2bfebf794ca6263b6cb42f65bbdc8328cc8e5a"
ISSUE16_BRANCH = "stage1-16-spec-kit-gate"
PREFLIGHT = "docs/governance/preflights/issue-16.json"
TOTAL_CHARGED_LINE_CAP = 2_400

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
    """Load the closed Issue #16 scope contract or return an empty artifact."""

    try:
        value = json.loads((root / PREFLIGHT).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
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
    """Validate a materialized base/branch/path/budget snapshot without I/O."""

    failures: list[str] = []
    scope = artifact.get("scope")
    required = scope.get("required") if isinstance(scope, dict) else None
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
        not isinstance(required, list)
        or not all(isinstance(path, str) for path in required)
        or len(required) != len(set(required))
        or len(changed_files) != len(set(changed_files))
        or set(changed_files) != set(required)
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


def repository_snapshot(root: Path) -> tuple[str, bool, list[str], dict[str, int]]:
    """Materialize the complete Issue #16 worktree diff against its fixed base."""

    branch_result = _git(root, "branch", "--show-current")
    ancestor_result = _git(root, "merge-base", "--is-ancestor", BASE_SHA, "HEAD")
    names_result = _git(root, "diff", "--name-only", "-z", BASE_SHA, "--")
    untracked_result = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    numstat_result = _git(root, "diff", "--numstat", "-z", BASE_SHA, "--")
    results = (branch_result, names_result, untracked_result, numstat_result)
    if any(result.returncode != 0 or (result.stdout and not result.stdout.endswith(b"\0")) for result in results[1:]):
        raise RuntimeError("repository snapshot unavailable")
    if branch_result.returncode != 0:
        raise RuntimeError("branch unavailable")

    def paths(raw: bytes) -> list[str]:
        return [item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item]

    changed = paths(names_result.stdout)
    untracked = paths(untracked_result.stdout)
    changed.extend(path for path in untracked if path not in changed)
    charged: dict[str, int] = {}
    for record in numstat_result.stdout.split(b"\0"):
        if not record:
            continue
        fields = record.split(b"\t", 2)
        if len(fields) != 3 or fields[0] == b"-" or fields[1] == b"-" or not fields[2]:
            raise RuntimeError("unsupported numstat record")
        path = fields[2].decode("utf-8", errors="surrogateescape")
        charged[path] = int(fields[0]) + int(fields[1])
    return (
        branch_result.stdout.decode("utf-8", errors="replace").strip(),
        ancestor_result.returncode == 0,
        changed,
        charged,
    )


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
    """Return stable finding codes for an incomplete or mutated Issue #16 kit."""

    failures: list[str] = []
    content = _read_contract(root, failures)
    _check_markers(content, failures)
    _check_task_graph(
        content.get("specs/001-grounded-walkthrough-script/tasks.md"), failures
    )

    constitution = content.get(".specify/memory/constitution.md")
    if constitution is not None and _ACTIVATION_CLAIM.search(constitution):
        failures.append("I16.SPECKIT.ACTIVATION")

    if (root / ".git").exists():
        try:
            branch, ancestor, changed, charged = repository_snapshot(root)
        except (OSError, subprocess.SubprocessError, RuntimeError, ValueError):
            failures.append("I16.SCOPE.HISTORY")
        else:
            failures.extend(
                validate_scope_snapshot(
                    load_preflight(root),
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
