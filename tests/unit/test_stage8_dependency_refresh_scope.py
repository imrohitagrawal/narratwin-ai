"""RED: invalid scope, cancelled staged excess and foreign merges must fail closed."""

from pathlib import Path
from typing import Any
import json
import subprocess as sp
import pytest
from scripts.quality import check_stage8_docs as stage8


def git(root: Path, *args: str) -> str:
    return sp.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()


def put(root: Path, path: str, value: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value)


def test_dependency_refresh_scope_uses_real_first_commit_and_manifest_budgets(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """RED: legacy scope rejects valid preflight; permissive routing admits runtime or excess."""
    branch = "stage8-901-dependency-container-refresh"

    def g(*args: str) -> str:
        return git(tmp_path, *args)

    g("init", "-b", "main")
    g("config", "user.name", "Scope Test")
    g("config", "user.email", "scope@example.invalid")
    put(tmp_path, "docs/STATUS.md", "base\n")
    put(tmp_path, "pyproject.toml", "base\n")
    g("add", ".")
    g("commit", "-m", "base")
    base = g("rev-parse", "HEAD")
    g("update-ref", "refs/remotes/origin/main", base)
    g("checkout", "-b", branch)
    path = "docs/governance/preflights/issue-901.json"
    paths = [path, "docs/STATUS.md", "pyproject.toml"]
    artifact = {
        "schema_version": "GovernancePreflightV1",
        "issue_number": 901,
        "branch": branch,
        "objective": "Bounded dependency hardening.",
        "status_decision": "update-minimally",
        "change_budget": {
            "exact_paths": 3,
            "maximum_additions_plus_deletions": 100,
            "deletions_grant_credit": False,
            "per_file_charged_lines": {p: 90 if p == path else 5 for p in paths},
        },
        "scope": {"required": paths, "allowed_prefixes": paths, "forbidden": ["backend/app/"]},
    }
    put(tmp_path, path, json.dumps(artifact) + "\n")
    g("add", path)
    g("commit", "-m", "preflight")
    put(tmp_path, "pyproject.toml", "patched\n")
    put(tmp_path, "docs/STATUS.md", "patched\n")
    g("add", ".")
    g("commit", "-m", "implementation")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(
        stage8, "run", lambda a: sp.run(a, cwd=tmp_path, text=True, capture_output=True)
    )
    for variable in (
        "GITHUB_EVENT_PATH",
        "GITHUB_HEAD_SHA",
        "GITHUB_BASE_SHA",
        "GITHUB_EVENT_NAME",
        "GITHUB_ACTIONS",
    ):
        monkeypatch.delenv(variable, raising=False)

    def findings() -> list[str]:
        failures: list[str] = []
        stage8.check_stage_scope(failures)
        return failures

    assert findings() == []
    # Every committed/index/worktree layer is charged even when a later layer cancels it.
    put(tmp_path, "pyproject.toml", "excess\n" * 6)
    g("add", "pyproject.toml")
    put(tmp_path, "pyproject.toml", "patched\n")
    assert findings()
    g("add", "pyproject.toml")
    put(tmp_path, "backend/app/main.py", "forbidden\n")
    assert findings()
    (tmp_path / "backend/app/main.py").unlink()
    put(tmp_path, path, json.dumps({**artifact, "issue_number": 902}) + "\n")
    assert findings()
    put(tmp_path, path, json.dumps(artifact) + "\n")
    assert findings() == []
    amended = {**artifact, "objective": "Documented later scope amendment retains valid C1."}
    put(tmp_path, path, json.dumps(amended) + "\n")
    g("add", path)
    assert findings() == []
    g("commit", "-m", "valid preflight amendment")
    event = tmp_path.parent / (tmp_path.name + "-push-event.json")
    event.write_text(json.dumps({"after": g("rev-parse", "HEAD"), "ref": "refs/heads/" + branch}))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert findings() == []
    # RED: a staged allowed-file change canceled in the worktree is still a dirty checkout.
    put(tmp_path, "docs/STATUS.md", "base\n")
    g("add", "docs/STATUS.md")
    put(tmp_path, "docs/STATUS.md", "patched\n")
    assert findings() == ["Dependency refresh hosted checkout is dirty."]
    g("add", "docs/STATUS.md")
    assert findings() == []


def test_exact_merge_checkout_requires_both_event_parents_and_rejects_foreign_checkout(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """RED: hosted PR merge checkout is rejected; forged parent/checkouts must stay rejected."""

    def g(*args: str) -> str:
        return git(tmp_path, *args)

    g("init", "-b", "main")
    g("config", "user.name", "Topology Test")
    g("config", "user.email", "topology@example.invalid")
    put(tmp_path, "base.txt", "base\n")
    g("add", ".")
    g("commit", "-m", "base")
    base = g("rev-parse", "HEAD")
    g("checkout", "-b", "feature")
    put(tmp_path, "head.txt", "head\n")
    g("add", ".")
    g("commit", "-m", "head")
    head = g("rev-parse", "HEAD")
    g("checkout", "main")
    g("merge", "--no-ff", "feature", "-m", "merge topology")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.setattr(
        stage8, "run", lambda a: sp.run(a, cwd=tmp_path, text=True, capture_output=True)
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_HEAD_SHA", head)
    monkeypatch.setenv("GITHUB_BASE_SHA", base)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    assert stage8.changed_files_for_stage_scope() == ["head.txt"]
    monkeypatch.setenv("GITHUB_BASE_SHA", head)
    pytest.raises(RuntimeError, stage8.changed_files_for_stage_scope)


@pytest.mark.parametrize("missing_budget", [False, True])
def test_invalid_historical_preflight_cannot_be_repaired_after_implementation(
    monkeypatch: Any,
    tmp_path: Path,
    missing_budget: bool,
) -> None:
    """RED: a filename-only C1 check accepts a late valid preflight after empty C1."""
    branch = "stage8-903-dependency-container-refresh"

    def g(*args: str) -> str:
        return git(tmp_path, *args)

    g("init", "-b", "main")
    g("config", "user.name", "History Test")
    g("config", "user.email", "history@example.invalid")
    put(tmp_path, "docs/STATUS.md", "base\n")
    g("add", ".")
    g("commit", "-m", "base")
    g("update-ref", "refs/remotes/origin/main", g("rev-parse", "HEAD"))
    g("checkout", "-b", branch)
    path = "docs/governance/preflights/issue-903.json"
    paths = [path, "docs/STATUS.md"]
    valid = {
        "schema_version": "GovernancePreflightV1",
        "issue_number": 903,
        "branch": branch,
        "objective": "Late valid preflight must not erase invalid C1.",
        "status_decision": "update-minimally",
        "change_budget": {
            "exact_paths": 2,
            "maximum_additions_plus_deletions": 100,
            "deletions_grant_credit": False,
            "per_file_charged_lines": {p: 50 for p in paths},
        },
        "scope": {"required": paths, "allowed_prefixes": paths, "forbidden": ["backend/app/"]},
    }
    historical = {key: value for key, value in valid.items() if key != "change_budget"}
    put(tmp_path, path, json.dumps(historical if missing_budget else {}) + "\n")
    g("add", ".")
    g("commit", "-m", "invalid preflight only")
    put(tmp_path, path, json.dumps(valid) + "\n")
    put(tmp_path, "docs/STATUS.md", "changed\n")
    g("add", ".")
    g("commit", "-m", "implementation and first valid preflight together")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.setattr(
        stage8, "run", lambda args: sp.run(args, cwd=tmp_path, text=True, capture_output=True)
    )
    for variable in (
        "GITHUB_EVENT_PATH",
        "GITHUB_HEAD_SHA",
        "GITHUB_BASE_SHA",
        "GITHUB_EVENT_NAME",
        "GITHUB_ACTIONS",
    ):
        monkeypatch.delenv(variable, raising=False)
    failures: list[str] = []
    stage8.check_refresh_scope(branch, failures)
    assert failures == ["Dependency refresh historical preflight invalid."]
