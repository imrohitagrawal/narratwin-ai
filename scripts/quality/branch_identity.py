"""Trusted branch identity shared by quality-gate dispatch and scope checks."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GIT = "/usr/bin/git"
GIT_TIMEOUT_SECONDS = 5
MAX_BRANCH_LENGTH = 255
SAFE_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,254}")


def _valid_branch(branch: str) -> bool:
    if not branch or len(branch) > MAX_BRANCH_LENGTH or SAFE_BRANCH.fullmatch(branch) is None:
        return False
    if branch.endswith((".", "/")) or ".." in branch or "//" in branch or "@{" in branch:
        return False
    return all(
        component and not component.startswith(".") and not component.endswith(".lock")
        for component in branch.split("/")
    )


def _git_branch(root: Path) -> str:
    env = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
    }
    try:
        result = subprocess.run(
            [GIT, "branch", "--show-current"],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    try:
        return result.stdout.decode("utf-8").strip()
    except UnicodeError:
        return ""


def current_branch(root: Path = ROOT) -> str:
    """Return one consistent event/Git branch, or empty fail-closed evidence."""
    event_branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    git_branch = _git_branch(root)
    if event_branch and not _valid_branch(event_branch):
        return ""
    if git_branch and not _valid_branch(git_branch):
        return ""
    if event_branch and git_branch and event_branch != git_branch:
        return ""
    return event_branch or git_branch
