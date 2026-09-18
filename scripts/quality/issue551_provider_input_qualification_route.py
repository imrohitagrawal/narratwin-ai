"""Exact Issue551 scope only; qualification prose never grants operation authority."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from scripts.governance_preflight_repository import _git, validate_governance_preflight_repository
from scripts.governance_preflight_v1 import validate_governance_preflight
from scripts.quality.phase1_closure import legacy

BRANCH = "phase-1-closure-process-551-provider-input-environment-qualification"
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
C1 = "c459ca12568985334b7f33287808d9960f37bca4"
PREFLIGHT = "docs/governance/preflights/issue-551.json"
PREFLIGHT_SHA256 = "f370303c61329342ff08753432d77b5af43ed368b43ee3656cb126f171d86427"


def validate_scope(root: Path, branch: str) -> list[str]:
    """Reuse bounded offline Git/preflight checks; distinguish working from hosted scope."""
    if branch != BRANCH:
        return ["ISSUE551_BRANCH"]
    try:
        path = root / PREFLIGHT
        raw = path.read_bytes()
        if path.is_symlink() or hashlib.sha256(raw).hexdigest() != PREFLIGHT_SHA256:
            return ["ISSUE551_PREFLIGHT_IDENTITY"]
        artifact = json.loads(raw)
        head = (_git(root, "rev-parse", "HEAD") or b"").decode().strip()
        first = (_git(root, "rev-list", "--reverse", f"{BASE}..{head}") or b"").decode().splitlines()
        if not re.fullmatch(r"[0-9a-f]{40}", head) or not first or first[0] != C1:
            return ["ISSUE551_C1_IDENTITY"]
        if ((_git(root, "merge-base", BASE, head) or b"").decode().strip() != BASE
                or (_git(root, "rev-parse", f"{C1}^") or b"").decode().strip() != BASE
                or (_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", C1) or b"").decode().splitlines() != [PREFLIGHT]
                or _git(root, "show", f"{C1}:{PREFLIGHT}") != raw):
            return ["ISSUE551_ANCESTRY_OR_C1_BYTES"]
        status = _git(root, "status", "--porcelain", "--untracked-files=all")
        if status is None or (status and os.environ.get("GITHUB_ACTIONS") == "true"):
            return ["ISSUE551_UNAVAILABLE_OR_HOSTED_DIRTY"]
        findings = validate_governance_preflight_repository(
            root, base_sha=BASE, head_sha=head, issue_number=551, branch=branch,
        )
        # Local preparation measures every working path below, not incomplete HEAD alone.
        failures = [f.code for f in findings if not (status and f.code == "GPF.SCOPE.REQUIRED_NOT_CHANGED")]
        if failures:
            return failures
        args = ["diff", "--no-renames", "--numstat", "-z", BASE]
        if not status:
            args.append(head)
        diff = _git(root, *args, "--")
        if diff is None or len(diff) > 65_536 or (diff and not diff.endswith(b"\0")):
            return ["ISSUE551_UNCOUNTABLE"]
        charges: dict[str, int] = {}
        for row in diff.split(b"\0")[:-1]:
            added, removed, name = row.decode("utf-8").split("\t")
            if name in charges or not re.fullmatch(r"[0-9]+", added) or not re.fullmatch(r"[0-9]+", removed):
                return ["ISSUE551_UNCOUNTABLE"]
            charges[name] = int(added) + int(removed)
        if status:
            untracked = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
            if untracked is None or len(untracked) > 65_536 or (untracked and not untracked.endswith(b"\0")):
                return ["ISSUE551_UNAVAILABLE"]
            for value in untracked.split(b"\0")[:-1]:
                name = value.decode("utf-8")
                file = root / name
                if name not in artifact["scope"]["required"] or file.is_symlink() or not file.is_file():
                    return ["ISSUE551_UNTRACKED_SCOPE"]
                data = file.read_bytes()
                if len(data) > 65_536 or b"\0" in data:
                    return ["ISSUE551_UNCOUNTABLE"]
                charges[name] = len(data.decode("utf-8").splitlines())
        failures = [f.code for f in validate_governance_preflight(artifact, context={
            "issue_number": 551, "branch": branch, "changed_files": list(charges),
        })]
        budget = artifact["change_budget"]
        caps = budget["per_file_charged_lines"]
        if set(charges) != set(caps):
            failures.append("ISSUE551_EXACT_PATHS")
        elif any(charges[name] > cap for name, cap in caps.items()):
            failures.append("ISSUE551_FILE_BUDGET")
        if sum(charges.values()) > budget["maximum_additions_plus_deletions"]:
            failures.append("ISSUE551_TOTAL_BUDGET")
        return failures
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return ["ISSUE551_UNAVAILABLE"]


def run(root: Path) -> int:
    failures = validate_scope(root, BRANCH)
    if not failures:
        checker = legacy._load_checker()
        failures = legacy.legacy_parity_failures(checker)
        checker.check_branch(failures)
        checker.check_required_files(failures)
        if not failures:
            for name in legacy.PRESERVED_CHECKS:
                if name == "check_active_demo_docs":
                    legacy.check_active_demo_docs(checker, failures)
                else:
                    getattr(checker, name)(failures)
    return legacy._print_result(failures)
