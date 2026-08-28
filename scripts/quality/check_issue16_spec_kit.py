#!/usr/bin/env python3
"""Validate the governance-only Issue #16 specification kit."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

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
