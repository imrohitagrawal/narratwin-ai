"""Bounded offline Git validation; no LLM, trace, script-generation, or citation behavior."""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from scripts.governance_preflight_v1 import GovernanceFinding, validate_governance_preflight


_PR_B_BRANCH = "phase-1-closure-process-176-gpf-v1-repository-integration"
_FAMILY = re.compile(r"^phase-1-closure-process-(\d+)-.+$")
_PREFLIGHT = re.compile(r"docs/governance/preflights/issue-(\d+)\.json$")
_ADAPTER = "scripts/governance_preflight_repository.py"
_SHA = re.compile(r"[0-9a-fA-F]{40}")
_GIT = "/usr/bin/git"
_TIMEOUT = 5
_MAX_COMMITS, _MAX_PATHS = 1_000, 2_000
_MAX_DIFF_BYTES = (_MAX_PATHS + 1) * 4_097


def _finding(code: str) -> GovernanceFinding:
    return GovernanceFinding(code)


def _git(repository: Path, *args: str) -> bytes | None:
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"}
    try:
        result = subprocess.run([_GIT, *args], cwd=repository, env=env, shell=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, timeout=_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _paths(raw: bytes | None) -> list[str] | None:
    return None if raw is None or (raw and not raw.endswith(b"\0")) else [
        item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0")[:-1]]


def _valid_path(path: str) -> bool:
    return (not path.startswith(("/", "\\", "~/")) and not re.match(r"^[A-Za-z]:", path)
            and "\\" not in path and all(part not in {"", ".", ".."} for part in path.split("/"))
            and not any(unicodedata.category(char).startswith("C") for char in path))


def _matches(path: str, rules: list[str]) -> bool:
    return any(path.startswith(rule) if rule.endswith("/") else path == rule for rule in rules)


def _dedupe(findings: list[GovernanceFinding]) -> list[GovernanceFinding]:
    return [_finding(code) for code in dict.fromkeys(finding.code for finding in findings)]


def _core(artifact: Any, issue: int, branch: str, changed: list[str]) -> list[GovernanceFinding]:
    context = {"issue_number": issue, "branch": branch, "changed_files": changed}
    if len(changed) <= 128:
        return validate_governance_preflight(artifact, context=context)
    probe = validate_governance_preflight(artifact, context={**context, "changed_files": []})
    if probe and probe[0].code.startswith(("GPF.SCHEMA.", "GPF.PATH.", "GPF.STATUS.")):
        return probe
    required = artifact["scope"]["required"]
    core = validate_governance_preflight(
        artifact, context={**context, "changed_files": [path for path in changed if path in required]})
    extras = [path for path in changed if path not in required]
    if any(not _valid_path(path) for path in extras):
        return [_finding("GPF.PATH.INVALID")]
    forbidden, allowed = artifact["scope"]["forbidden"], artifact["scope"]["allowed_prefixes"]
    extra_codes: list[str] = []
    if any(_matches(path, forbidden) for path in extras):
        extra_codes.append("GPF.SCOPE.CHANGE_FORBIDDEN")
    if any(not _matches(path, allowed) and not _matches(path, forbidden) for path in extras):
        extra_codes.append("GPF.SCOPE.CHANGE_NOT_ALLOWED")
    split = next((index for index, finding in enumerate(core) if finding.code.startswith("GPF.BINDING.")), len(core))
    return core[:split] + [_finding(code) for code in extra_codes] + core[split:]


def validate_governance_preflight_repository(
    repository: Path, *, base_sha: str, head_sha: str, issue_number: int, branch: str,
) -> list[GovernanceFinding]:
    """Validate one prospective governance branch without network or mutation."""
    branch_match = _FAMILY.fullmatch(branch)
    if branch != _PR_B_BRANCH and branch_match is None:
        return []
    exact = branch == _PR_B_BRANCH
    if not repository.is_dir() or not _SHA.fullmatch(base_sha):
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")] if exact else []
    if _git(repository, "cat-file", "-e", f"{base_sha}^{{commit}}") is None:
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")] if exact else []
    if not exact and _git(repository, "cat-file", "-e", f"{base_sha}:{_ADAPTER}") is None:
        return []
    if not _SHA.fullmatch(head_sha):
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    if _git(repository, "cat-file", "-e", f"{head_sha}^{{commit}}") is None:
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    if _git(repository, "merge-base", "--is-ancestor", base_sha, head_sha) is None:
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    raw_count = _git(repository, "rev-list", "--count", "--max-count=1001", f"{base_sha}..{head_sha}")
    try:
        count = int(raw_count or b"")
    except ValueError:
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    if count > _MAX_COMMITS:
        return [_finding("GPF.REPO.LIMIT_EXCEEDED")]
    raw_changed = _git(repository, "diff", "--name-only", "-z", base_sha, head_sha, "--")
    if raw_changed is not None and len(raw_changed) > _MAX_DIFF_BYTES:
        return [_finding("GPF.REPO.LIMIT_EXCEEDED")]
    changed = _paths(raw_changed)
    if changed is None:
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    if len(changed) > _MAX_PATHS:
        return [_finding("GPF.REPO.LIMIT_EXCEEDED")]
    artifacts = [(path, _PREFLIGHT.fullmatch(path)) for path in changed if _PREFLIGHT.fullmatch(path)]
    if not artifacts:
        return [_finding("GPF.REPO.PREFLIGHT_MISSING")]
    if len(artifacts) > 1:
        return [_finding("GPF.REPO.PREFLIGHT_MULTIPLE")]
    artifact_path, filename_match = artifacts[0]
    raw_commits = _git(repository, "rev-list", "--reverse", f"{base_sha}..{head_sha}")
    if raw_commits is None or not raw_commits.splitlines():
        return [_finding("GPF.REPO.HISTORY_UNAVAILABLE")]
    first_paths = _paths(_git(repository, "diff-tree", "--root", "--no-commit-id",
                              "--name-only", "-r", "-z", raw_commits.splitlines()[0].decode(), "--"))
    if first_paths != [artifact_path]:
        return [_finding("GPF.REPO.PREFLIGHT_NOT_FIRST")]
    findings: list[GovernanceFinding] = []
    if (filename_match is None or int(filename_match.group(1)) != issue_number
            or branch_match is None or int(branch_match.group(1)) != issue_number):
        findings.append(_finding("GPF.REPO.ISSUE_REF_MISMATCH"))
    raw_artifact = _git(repository, "show", f"{head_sha}:{artifact_path}")
    if raw_artifact is None:
        return [_finding("GPF.REPO.PREFLIGHT_MISSING")]
    if len(raw_artifact) > 65_536:
        return _dedupe(findings + [_finding("GPF.SCHEMA.LIMIT")])
    try:
        artifact = json.loads(raw_artifact.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        artifact = None
    return _dedupe(findings + _core(artifact, issue_number, branch, changed))
