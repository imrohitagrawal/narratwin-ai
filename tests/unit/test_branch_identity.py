from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality import branch_identity


def test_branch_identity_requires_event_and_git_consistency(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "expected-branch")
    monkeypatch.setattr(branch_identity, "_git_branch", lambda _root: "other-branch")

    assert branch_identity.current_branch(Path(".")) == ""


def test_detached_ci_uses_event_identity(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "expected-branch")
    monkeypatch.setattr(branch_identity, "_git_branch", lambda _root: "")

    assert branch_identity.current_branch(Path(".")) == "expected-branch"


def test_local_run_uses_git_identity(monkeypatch: Any) -> None:
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.setattr(branch_identity, "_git_branch", lambda _root: "local-branch")

    assert branch_identity.current_branch(Path(".")) == "local-branch"


def test_malformed_or_unbounded_branch_identity_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(branch_identity, "_git_branch", lambda _root: "")
    for value in ("x" * 256, "bad\nbranch", "bad..branch", "bad//branch", ".hidden"):
        monkeypatch.setenv("GITHUB_HEAD_REF", value)
        assert branch_identity.current_branch(Path(".")) == ""
