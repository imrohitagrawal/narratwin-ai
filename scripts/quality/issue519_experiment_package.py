"""Pinned, offline scope for the nonactivating Issue 519 comparison successor."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from scripts.governance_preflight_repository import validate_governance_preflight_repository
from scripts.quality.phase1_closure import legacy

BRANCH = "phase-1-closure-process-519-experiment-first-package-v2"
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
PREFLIGHT = "docs/governance/preflights/issue-519.json"
C1 = "a05cd088a7131b0d7736c8d53341326608f022a6"
C1_SHA256 = "4feef3a10c1c506c94695f7634275b693a4b7a19a58dba76ab707a49c3966bfd"


def _git(root: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["/usr/bin/git", *args], cwd=root, capture_output=True, check=False, timeout=5,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _records(raw: bytes | None) -> list[str] | None:
    if not raw or not raw.endswith(b"\0"):
        return None
    try:
        return raw[:-1].decode("utf-8").split("\0")
    except UnicodeError:
        return None


def validate_scope(root: Path, branch: str) -> list[str]:
    if branch != BRANCH:
        return ["Issue #519 exact branch required."]
    raw_head = _git(root, "rev-parse", "HEAD")
    if raw_head is None or not re.fullmatch(rb"[0-9a-f]{40}\n?", raw_head):
        return ["Issue #519 HEAD unavailable."]
    head = raw_head.decode("ascii").strip()
    first = _git(root, "show", f"{C1}:{PREFLIGHT}")
    if (first is None or hashlib.sha256(first).hexdigest() != C1_SHA256
            or _git(root, "merge-base", "--is-ancestor", C1, head) is None):
        return ["Issue #519 pinned C1 custody/ancestry unavailable."]
    raw = _git(root, "show", f"{head}:{PREFLIGHT}")
    if raw is None or hashlib.sha256(raw).hexdigest() != C1_SHA256:
        return ["Issue #519 HEAD preflight differs from pinned C1."]
    try:
        manifest = json.loads(raw)
        required = manifest["scope"]["required"]
        budget = manifest["change_budget"]
        caps = budget["per_file_charged_lines"]
        if (required != manifest["scope"]["allowed_prefixes"] or len(set(required)) != 14
                or len(required) != 14 or set(caps) != set(required)
                or budget["exact_paths"] != 14 or budget["maximum_additions_plus_deletions"] != 2300
                or budget["deletions_grant_credit"] is not False
                or any(type(cap) is not int or cap <= 0 for cap in caps.values())):
            return ["Issue #519 pinned scope/budget shape invalid."]
    except (ValueError, KeyError, TypeError):
        return ["Issue #519 pinned preflight unreadable."]
    findings = validate_governance_preflight_repository(
        root, base_sha=BASE, head_sha=head, issue_number=519, branch=branch,
    )
    if findings:
        return [f"Issue #519 repository preflight: {finding.code}" for finding in findings]
    paths = _records(_git(root, "diff", "--name-only", "-z", "--no-renames", BASE, head, "--"))
    if paths is None or len(paths) != len(required) or set(paths) != set(required):
        return ["Issue #519 exact fixed-base path set failed."]
    records = _records(_git(root, "diff", "--numstat", "-z", "--no-renames", BASE, head, "--"))
    if records is None:
        return ["Issue #519 charged lines unavailable."]
    charged: dict[str, int] = {}
    for record in records:
        fields = record.split("\t")
        if (len(fields) != 3 or not re.fullmatch(r"[0-9]+", fields[0])
                or not re.fullmatch(r"[0-9]+", fields[1]) or fields[2] not in caps
                or fields[2] in charged):
            return ["Issue #519 charged lines malformed or binary."]
        try:
            charged[fields[2]] = int(fields[0]) + int(fields[1])
        except ValueError:
            return ["Issue #519 charged lines uncountable."]
    if set(charged) != set(required):
        return ["Issue #519 charged-line path set failed."]
    if any(total > caps[path] for path, total in charged.items()):
        return ["Issue #519 per-path charged-line cap exceeded."]
    if sum(charged.values()) > budget["maximum_additions_plus_deletions"]:
        return ["Issue #519 aggregate charged-line cap exceeded."]
    return []


def run(root: Path, branch: str) -> int:
    failures = validate_scope(root, branch)
    if failures:
        return legacy._print_result(failures)
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
