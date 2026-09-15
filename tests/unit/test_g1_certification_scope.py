from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.quality import g1_certification_scope as scope
from scripts.quality.issue521_successor import RuntimeConfig, git
from scripts.quality.phase1_closure import runner


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: Any) -> Any:
    for key in tuple(os.environ):
        if key.startswith("GITHUB_") or key == "NARRATWIN_G1_GIT_TIMEOUT_SECONDS":
            monkeypatch.delenv(key)
    root = tmp_path / "standalone"
    root.mkdir()
    env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_NO_LAZY_FETCH": "1", "GIT_AUTHOR_NAME": "Fixture", "GIT_COMMITTER_NAME": "Fixture",
           "GIT_AUTHOR_EMAIL": "fixture@example.invalid", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
    def git(*args: str) -> str:
        return subprocess.check_output(["/usr/bin/git", "-c", "commit.gpgsign=false", *args],
                                       cwd=root, env=env, stderr=subprocess.PIPE, timeout=5).decode().strip()
    def write(path: str, value: str) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
    def commit() -> str:
        git("add", ".")
        git("commit", "-m", "fixture")
        return git("rev-parse", "HEAD")
    git("init", "-b", "main")
    write("scripts/governance_preflight_repository.py", "adapter exists at base\n")
    base = commit()
    git("checkout", "-b", scope.BRANCH)
    raw = (scope.ROOT / scope.PREFLIGHT).read_text()
    write(scope.PREFLIGHT, raw)
    first = commit()
    for path in json.loads(raw)["scope"]["required"]:
        if path != scope.PREFLIGHT:
            write(path, "changed\n")
    head = commit()
    monkeypatch.setattr(scope, "BASE", base)
    monkeypatch.setattr(scope, "FIRST_COMMIT", first)
    return SimpleNamespace(root=root, git=git, write=write, commit=commit, base=base, first=first, head=head)


@pytest.mark.parametrize("topology", ["direct", "custom", "merge", "initial-push", "forced-push"])
def test_actual_checkout_topologies(repository: Any, monkeypatch: Any, tmp_path: Path, topology: str) -> None:
    r = repository
    r.git("checkout", "main")
    r.write("main-only", "new main content\n")
    main = r.commit()
    r.git("merge", "--no-ff", "-m", "merge", r.head)
    merge = r.git("rev-parse", "HEAD")
    linked = tmp_path / "linked"
    r.git("worktree", "add", "--detach", str(linked), r.head)
    event = {"number": 542, "pull_request": {
        side: {"sha": sha, "ref": scope.BRANCH if side == "head" else "main",
               "repo": {"full_name": "imrohitagrawal/narratwin-ai"}}
        for side, sha in (("head", r.head), ("base", main))}}
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_REF", "refs/pull/542/merge")
    monkeypatch.setenv("GITHUB_SHA", merge)
    if topology == "custom":
        monkeypatch.setenv("GITHUB_HEAD_SHA", r.head)
    if topology.endswith("push"):
        monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
        monkeypatch.setenv("GITHUB_REF_NAME", scope.BRANCH)
        monkeypatch.setenv("GITHUB_BASE_SHA", "0" * 40 if topology == "initial-push" else r.head)
    checkout = r.root if topology == "merge" else linked
    assert scope.validate_scope(checkout, scope.BRANCH) == []
    assert git(linked, RuntimeConfig(5), "rev-parse", "HEAD").decode().strip() == r.head
    if topology == "merge":
        monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
        assert scope.validate_scope(checkout, scope.BRANCH) == ["G1.CARRIER.CHECKOUT"]
    else:
        monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
        monkeypatch.setenv("GITHUB_HEAD_SHA", main)
        assert scope.validate_scope(checkout, scope.BRANCH) == ["G1.CARRIER.EVENT"]


@pytest.mark.parametrize("late_merge", [False, True])
def test_available_pin_cannot_authorize_alternate_first_history(repository: Any, late_merge: bool) -> None:
    r = repository
    r.git("checkout", "-b", "alternate", r.base)
    raw = (scope.ROOT / scope.PREFLIGHT).read_text()
    r.write(scope.PREFLIGHT, raw.replace('"issue_number": 533', '"issue_number": 534'))
    r.commit()
    r.write(scope.PREFLIGHT, raw)
    r.commit()
    if late_merge:
        r.git("merge", "--no-ff", "-m", "late pin", r.first)
    assert r.git("cat-file", "-t", r.first) == "commit"
    findings = scope.validate_scope(r.root, scope.BRANCH)
    assert findings == (["G1.CARRIER.FIRST_COMMIT"] if late_merge else ["G1.CARRIER.UNAVAILABLE"])


@pytest.mark.parametrize("mutation", ["extra", "over-budget", "missing", "symlink", "rehashed-preflight"])
def test_measured_changes_fail_closed(repository: Any, mutation: str) -> None:
    r = repository
    path = r.root / "docs/STATUS.md"
    if mutation == "extra":
        r.write("unauthorized.txt", "extra\n")
    elif mutation == "over-budget":
        path.write_text("over limit\n" * 81)
    elif mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to("STAGE_ISSUE_PLAN.md")
    else:
        preflight = r.root / scope.PREFLIGHT
        preflight.write_text(preflight.read_text().replace('"exact_paths": 11', '"exact_paths": 12'))
    assert scope.validate_scope(r.root, scope.BRANCH)


def test_default_override_reaches_actual_git_and_reports_effective_values(repository: Any, monkeypatch: Any,
                                                                       capsys: Any) -> None:
    seen: list[float] = []
    real = subprocess.run
    def invoke(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs["timeout"])
        return real(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", invoke)
    assert scope.validate_scope(repository.root, scope.BRANCH) == []
    assert set(seen) == {5}
    seen.clear()
    monkeypatch.setenv("NARRATWIN_G1_GIT_TIMEOUT_SECONDS", "7.25")
    assert scope.validate_scope(repository.root, scope.BRANCH) == []
    assert set(seen) == {5, 7.25}  # Generic helper retains its separately reported inherited timeout.
    assert '"gitTimeoutSeconds": 7.25' in capsys.readouterr().out


@pytest.mark.parametrize("value", ["0", "nan", "inf", "-1", "true", "2147484", "1e9999"])
def test_invalid_runtime_environment_rejected(repository: Any, monkeypatch: Any, value: str) -> None:
    monkeypatch.setenv("NARRATWIN_G1_GIT_TIMEOUT_SECONDS", value)
    assert scope.validate_scope(repository.root, scope.BRANCH) == ["G1.CONFIG.GIT_TIMEOUT"]


def test_actual_git_maximum_and_dependency_absent_bootstrap(repository: Any, tmp_path: Path) -> None:
    assert scope.validate_scope(repository.root, scope.BRANCH, config=RuntimeConfig(2147483)) == []
    assert scope.validate_scope(repository.root, scope.BRANCH, config=False) == ["G1.CONFIG.TYPE"]  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="G1.CONFIG.GIT_TIMEOUT"):
        RuntimeConfig(True)
    r = repository
    linked = tmp_path / "bootstrap-linked"
    r.git("worktree", "add", "--detach", str(linked), r.head)
    r.git("checkout", "main")
    r.git("merge", "--no-ff", "-m", "normal merge", r.head)
    result = subprocess.run([sys.executable, "-S", "-c",
        "from pathlib import Path; from scripts.quality import g1_certification_scope as s; "
        f"s.BASE={r.base!r}; s.FIRST_COMMIT={r.first!r}; s.ROOT=Path({str(linked)!r}); "
        "assert s.registered_preflight(s.ROOT)['issue_number']==533; "
        "print(s.candidate_head(s.ROOT,s.RuntimeConfig(5)))"],
        cwd=scope.ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_admission_failure_prevents_preserved_continuation(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: scope.BRANCH)
    monkeypatch.setattr(scope, "validate_scope", lambda *args: ["G1.CARRIER.PREFLIGHT_IDENTITY"])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: pytest.fail("must not continue"))
    assert runner.run_preserved_contracts() == 1


def test_fresh533_exact_admission_replaces_only_frozen_path_rejection(monkeypatch: Any) -> None:
    artifact = json.loads((runner.ROOT / scope.PREFLIGHT).read_text())
    checker = runner.legacy._load_checker()
    calls: list[str] = []
    monkeypatch.setattr(runner, "current_branch", lambda root: scope.BRANCH)
    monkeypatch.setattr(checker, "current_branch", lambda: scope.BRANCH)
    monkeypatch.setattr(checker, "changed_files", lambda: artifact["scope"]["required"])
    monkeypatch.setattr(checker, "check_required_files", lambda failures: None)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(runner.legacy, "PRESERVED_CHECKS", ())
    def admission(*args: Any) -> list[str]:
        calls.append("exact-admission")
        return []
    monkeypatch.setattr(scope, "validate_scope", admission)
    assert runner.run_preserved_contracts() == 0
    assert calls == ["exact-admission"]
