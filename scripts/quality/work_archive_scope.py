"""Exact issue535 scope; preserve existing acceptance, never certify private evidence."""
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.governance_preflight_repository import validate_governance_preflight_repository
from scripts.governance_preflight_v1 import validate_governance_preflight

BRANCH = "phase-1-closure-process-535-work-archive"
PREFLIGHT = "docs/governance/preflights/issue-535.json"


def budget_failures(artifact: Any, charges: dict[str, int], branch: str) -> list[str]:
    if branch != BRANCH:
        return ["ARCHIVE_SCOPE_BRANCH"]
    findings = validate_governance_preflight(artifact, context={
        "issue_number": 535, "branch": branch, "changed_files": list(charges),
    })
    if findings:
        return [finding.code for finding in findings]
    budget = artifact.get("change_budget")
    if not isinstance(budget, dict):
        return ["ARCHIVE_SCOPE_BUDGET_REQUIRED"]
    limits = budget["per_file_charged_lines"]
    if set(charges) != set(limits) or artifact["scope"]["required"] != artifact["scope"]["allowed_prefixes"]:
        return ["ARCHIVE_SCOPE_EXACT_PATHS"]
    if any(type(value) is not int or value < 0 for value in charges.values()):
        return ["ARCHIVE_SCOPE_UNCOUNTABLE"]
    if any(charges[path] > limits[path] for path in charges):
        return ["ARCHIVE_SCOPE_FILE_BUDGET"]
    if sum(charges.values()) > budget["maximum_additions_plus_deletions"]:
        return ["ARCHIVE_SCOPE_TOTAL_BUDGET"]
    return []


def validate_scope(root: Path, branch: str) -> list[str]:
    """Measure working changes locally; hosted checks require a clean committed tree."""
    try:
        timeout = float(os.environ.get("NARRATWIN_ARCHIVE_GIT_TIMEOUT_SECONDS", "5"))
        if not math.isfinite(timeout) or timeout <= 0:
            return ["ARCHIVE_SCOPE_CONFIG"]

        def git(*args: str) -> bytes:
            result = subprocess.run(
                ["git", *args], cwd=root, check=True, capture_output=True, timeout=timeout,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"},
            )
            return result.stdout

        artifact = json.loads((root / PREFLIGHT).read_text())
        head = git("rev-parse", "HEAD").decode().strip()
        base = git("merge-base", "HEAD", "refs/remotes/origin/main").decode().strip()
        dirty = bool(git("status", "--porcelain", "--untracked-files=all"))
        hosted = os.environ.get("GITHUB_ACTIONS") == "true"
        if hosted and dirty:
            return ["ARCHIVE_SCOPE_HOSTED_DIRTY"]
        # Before the first commit local files can be checked without claiming
        # immutable commit ordering. Committed candidates always verify ordering.
        if head != base:
            findings = validate_governance_preflight_repository(
                root, base_sha=base, head_sha=head, issue_number=535, branch=branch,
            )
            # A preflight-only first commit is valid local preparation, but it
            # cannot pass committed/hosted final-scope verification until complete.
            if dirty and not hosted:
                findings = [f for f in findings if f.code != "GPF.SCOPE.REQUIRED_NOT_CHANGED"]
            if findings:
                return [f.code for f in findings]
        elif hosted or not dirty:
            return ["ARCHIVE_SCOPE_NO_CANDIDATE"]
        args = ["diff", "--no-renames", "--numstat", "-z", base]
        if not dirty:
            args.append(head)
        raw = git(*args, "--")
        charges: dict[str, int] = {}
        for row in raw.split(b"\0"):
            if not row:
                continue
            added, removed, path = row.decode("utf-8").split("\t", 2)
            charges[path] = int(added) + int(removed)
        if dirty:
            untracked = git("ls-files", "--others", "--exclude-standard", "-z")
            for raw_path in untracked.split(b"\0"):
                if not raw_path:
                    continue
                path = raw_path.decode("utf-8")
                if path not in artifact["scope"]["required"]:
                    return ["ARCHIVE_SCOPE_UNTRACKED_EXTRA"]
                file = root / path
                if file.is_symlink():
                    return ["ARCHIVE_SCOPE_SYMLINK"]
                data = file.read_bytes()
                if b"\0" in data:
                    return ["ARCHIVE_SCOPE_UNCOUNTABLE"]
                charges[path] = len(data.decode("utf-8").splitlines())
        failures = budget_failures(artifact, charges, branch)
        if not failures:
            mode = "WORKTREE_CHECK_ONLY" if dirty else "COMMITTED_SCOPE_CHECK"
            print(f"Archive scope: {mode}; {len(charges)} paths; {sum(charges.values())} charged lines.")
        return failures
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, subprocess.SubprocessError):
        return ["ARCHIVE_SCOPE_UNAVAILABLE"]
