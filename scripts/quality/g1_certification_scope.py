"""Fresh #533 repository scope admission; never acquire or interpret receipts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from scripts.governance_preflight_repository import validate_governance_preflight_repository
from scripts.quality.branch_identity import current_branch
from scripts.quality.issue521_successor import (
    RuntimeConfig, git, read_bytes, safe_path, successor_budget_failures,
)

BRANCH = "phase-1-closure-process-533-fresh-g1-certification"
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
FIRST_COMMIT = "68e4c947b751b94e60d91a27ebce5ce6e2c21f0d"
PREFLIGHT = "docs/governance/preflights/issue-533.json"
PREFLIGHT_SHA256 = "c2f43651499ff30470b76bcf4be35d306496fc8d26554143889f58df94515428"
PREFLIGHT_BYTES = 4511
ROOT = Path(__file__).resolve().parents[2]


def hosted_pr_head(root: Path, config: RuntimeConfig, checkout: str) -> str:
    """Bind direct or merge checkout to GitHub's actual PR event, not a guessed DAG."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    pr = event["pull_request"]
    head, base = pr["head"]["sha"], pr["base"]["sha"]
    number = event["number"]
    if (type(number) is not int or number <= 0
            or any(not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha)
                   for sha in (head, base))
            or pr["head"]["ref"] != BRANCH
            or any(pr[side]["repo"]["full_name"] != "imrohitagrawal/narratwin-ai" for side in ("head", "base"))
            or os.environ.get("GITHUB_HEAD_SHA", head) != head):
        raise ValueError("G1.CARRIER.EVENT")
    if checkout != head:
        parents = git(root, config, "rev-list", "--parents", "-n", "1", checkout).decode().split()
        if (os.environ.get("GITHUB_REF") != f"refs/pull/{number}/merge"
                or os.environ.get("GITHUB_SHA") != checkout or parents != [checkout, base, head]):
            raise ValueError("G1.CARRIER.CHECKOUT")
    return str(head)


def registered_preflight(root: Path) -> dict[str, Any]:
    raw = read_bytes(root, PREFLIGHT, PREFLIGHT_BYTES, exact=PREFLIGHT_BYTES)
    if hashlib.sha256(raw).hexdigest() != PREFLIGHT_SHA256:
        raise ValueError("G1.CARRIER.PREFLIGHT_IDENTITY")
    artifact: dict[str, Any] = json.loads(raw)
    return artifact


def candidate_head(root: Path, config: RuntimeConfig) -> str:
    raw = git(root, config, "show", f"{FIRST_COMMIT}:{PREFLIGHT}")
    if hashlib.sha256(raw).hexdigest() != PREFLIGHT_SHA256:
        raise ValueError("G1.CARRIER.FIRST_BLOB")
    if git(root, config, "rev-parse", f"{FIRST_COMMIT}^").decode().strip() != BASE:
        raise ValueError("G1.CARRIER.BASE")
    checkout = git(root, config, "rev-parse", "HEAD").decode().strip()
    head = checkout
    if os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        head = hosted_pr_head(root, config, checkout)
    git(root, config, "merge-base", "--is-ancestor", FIRST_COMMIT, checkout)
    git(root, config, "merge-base", "--is-ancestor", FIRST_COMMIT, head)
    commits = git(root, config, "rev-list", "--first-parent", "--reverse", f"{BASE}..{head}")
    if not commits.splitlines() or commits.splitlines()[0].decode() != FIRST_COMMIT:
        raise ValueError("G1.CARRIER.FIRST_COMMIT")
    return head


def measured_charges(root: Path, config: RuntimeConfig, head: str, dirty: bool,
                     artifact: dict[str, Any]) -> dict[str, int]:
    args = ["diff", "--no-renames", "--numstat", "-z", BASE]
    if not dirty:
        args.append(head)
    charges: dict[str, int] = {}
    for row in git(root, config, *args, "--").split(b"\0"):
        if row:
            added, removed, path = row.decode("utf-8").split("\t", 2)
            charges[path] = int(added) + int(removed)
    if dirty:
        for raw_path in git(root, config, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
            if not raw_path:
                continue
            path = raw_path.decode("utf-8")
            if path not in artifact["scope"]["required"]:
                raise ValueError("G1.CARRIER.EXTRA_PATH")
            data = safe_path(root, path).read_bytes()
            if b"\0" in data:
                raise ValueError("G1.CARRIER.BINARY")
            charges[path] = len(data.decode("utf-8").splitlines())
    for path in charges:
        if not safe_path(root, path).is_file():
            raise ValueError("G1.CARRIER.MISSING_FILE")
    return charges


def validate_scope(root: Path, branch: str, *, config: RuntimeConfig | None = None) -> list[str]:
    """Verify measured scope with a reviewed identity, not caller-supplied authority."""
    try:
        if branch != BRANCH:
            return ["G1.CARRIER.BRANCH"]
        artifact = registered_preflight(root)
        # Safe local default; existing typed production environment override remains available.
        effective = RuntimeConfig.resolve({"limits": {"gitTimeoutSeconds": 5}}) if config is None else config
        if type(effective) is not RuntimeConfig:
            raise ValueError("G1.CONFIG.TYPE")
        head = candidate_head(root, effective)
        dirty = bool(git(root, effective, "status", "--porcelain", "--untracked-files=all"))
        hosted = os.environ.get("GITHUB_ACTIONS") == "true"
        if hosted and dirty:
            return ["G1.CARRIER.HOSTED_DIRTY"]
        findings = validate_governance_preflight_repository(
            root, base_sha=BASE, head_sha=head, issue_number=533, branch=branch,
        )
        if dirty and not hosted:
            findings = [item for item in findings if item.code != "GPF.SCOPE.REQUIRED_NOT_CHANGED"]
        if findings:
            return [item.code for item in findings]
        charges = measured_charges(root, effective, head, dirty, artifact)
        failures = successor_budget_failures(artifact, charges, branch, 533)
        print(json.dumps({
            "scopeMode": "WORKTREE_CHECK_ONLY" if dirty else "COMMITTED_SCOPE_CHECK",
            "chargedLines": sum(charges.values()), "paths": len(charges),
            "effectiveConfiguration": effective.effective(),
            "inheritedRepositoryHelperConfiguration": "UNCHANGED_LEGACY_GIT_LIMITS",
            "receiptConsumption": "NONE", "certification": "NOT_GRANTED",
        }))
        return failures
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as exc:
        return [str(exc) if isinstance(exc, ValueError) and str(exc).startswith("G1.")
                else "G1.CARRIER.UNAVAILABLE"]


if __name__ == "__main__":
    result = validate_scope(ROOT, current_branch(ROOT))
    for finding in result:
        print(finding)
    raise SystemExit(int(bool(result)))
