"""Exact branch, path, and charged-line policy for Issue #324."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT_PATH = "docs/governance/preflights/issue-324.json"
ISSUE_324_BRANCH = "phase-1-closure-process-324-publication-boundary-v2"
ISSUE_324_LINE_CAP = 3700


def _preflight_required_files() -> tuple[str, ...]:
    try:
        artifact = json.loads((ROOT / PREFLIGHT_PATH).read_text(encoding="utf-8"))
        required = artifact["scope"]["required"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return ()
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        return ()
    return tuple(required)


PREFLIGHT_REQUIRED_FILES = _preflight_required_files()
ISSUE_324_ALLOWED_CHANGED_FILES = frozenset(PREFLIGHT_REQUIRED_FILES)


def _valid_path(path: str) -> bool:
    if (
        not path
        or len(path) > 512
        or path.startswith(("/", "\\", "~/"))
        or re.match(r"^[A-Za-z]:", path)
    ):
        return False
    if "\\" in path or any(unicodedata.category(char).startswith("C") for char in path):
        return False
    return all(part not in {"", ".", ".."} for part in path.split("/"))


def validate_issue_scope(
    *, branch: str, changed_files: list[str], charged_line_count: int | None
) -> list[str]:
    failures: list[str] = []
    if branch != ISSUE_324_BRANCH:
        failures.append("Publication-boundary work requires the exact Issue #324 branch.")
    if len(changed_files) != len(set(changed_files)):
        failures.append("Issue #324 has duplicate changed-file evidence.")
    invalid = sorted(path for path in changed_files if not isinstance(path, str) or not _valid_path(path))
    if invalid:
        failures.append("Issue #324 has invalid changed-file evidence.")
    changed = {path for path in changed_files if isinstance(path, str) and _valid_path(path)}
    for path in sorted(ISSUE_324_ALLOWED_CHANGED_FILES - changed):
        failures.append(f"Issue #324 required path {path} must change.")
    for path in sorted(changed - ISSUE_324_ALLOWED_CHANGED_FILES):
        failures.append(f"Issue #324 path {path} may not change.")
    if (
        isinstance(charged_line_count, bool)
        or not isinstance(charged_line_count, int)
        or charged_line_count < 0
    ):
        failures.append("Issue #324 charged-line evidence is unavailable.")
    elif charged_line_count > ISSUE_324_LINE_CAP:
        failures.append(f"Issue #324 exceeds its {ISSUE_324_LINE_CAP}-line cap.")
    return failures
