from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from scripts.quality import r0c_a1_scope as scope
from scripts.quality.phase1_closure import legacy, runner


CURRENT_BRANCH = "phase-1-closure-process-330-r0c-a1-1a-freshness-scope-freeze"
CURRENT_FILES = {
    "docs/governance/preflights/issue-330.json",
    "scripts/quality/r0c_a1_scope.py",
    "tests/unit/test_r0c_a1_scope.py",
    "scripts/quality/phase1_closure/runner.py",
    "scripts/quality/phase1_closure/legacy.py",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
}
B_FILES = {
    "docs/governance/preflights/issue-998.json",
    "docs/agent-context/contracts-v1.schema.json",
    "docs/agent-context/current-state-v1.json",
    "docs/agent-context/context-policy-manifest-v1.json",
    "scripts/agent_context/core.py",
    "scripts/agent_context/cli.py",
    "tests/unit/test_agent_context_freshness.py",
    "docs/STATUS.md",
}
C_FILES = {
    "docs/governance/preflights/issue-999.json",
    "scripts/agent_context/github.py",
    "tests/unit/test_agent_context_github.py",
    ".github/workflows/quality-gates.yml",
    "docs/QUALITY_GATES.md",
    "docs/STATUS.md",
}


@pytest.mark.parametrize(
    ("branch", "files", "cap"),
    [
        (CURRENT_BRANCH, CURRENT_FILES, 500),
        ("phase-1-closure-process-998-r0c-a1-1b-offline-freshness", B_FILES, 800),
        ("phase-1-closure-process-999-r0c-a1-1c-live-freshness", C_FILES, 650),
    ],
)
def test_exact_recovery_scopes_are_derived_green(
    branch: str, files: set[str], cap: int
) -> None:
    assert scope.validate_scope(
        branch=branch, changed_files=sorted(files), charged_line_count=cap
    ) == scope.ScopeEvaluation(True, ())
    assert scope.is_managed_branch(branch)


def test_scope_rejects_near_match_missing_extra_duplicate_and_over_budget() -> None:
    files = sorted(B_FILES)
    result = scope.validate_scope(
        branch="phase-1-closure-process-998-r0c-a1-1b-offline-freshness-copy",
        changed_files=files[1:] + [files[1], "backend/app/main.py"],
        charged_line_count=801,
    )
    assert result.managed
    assert any("exact" in failure for failure in result.failures)
    assert any("duplicate" in failure for failure in result.failures)
    assert any(files[0] in failure and "must change" in failure for failure in result.failures)
    assert any("backend/app/main.py" in failure and "may not change" in failure for failure in result.failures)
    assert any("800-line cap" in failure for failure in result.failures)
    assert not scope.is_managed_branch(
        "phase-1-closure-process-998-r0c-a1-1b-offline-freshness-copy"
    )


@pytest.mark.parametrize("files, lines", [(None, 10), ([], None), ([], True), ([], -1)])
def test_managed_scope_fails_closed_when_git_evidence_is_unavailable(
    files: list[str] | None, lines: int | None
) -> None:
    result = scope.validate_scope(
        branch=CURRENT_BRANCH, changed_files=files, charged_line_count=lines
    )
    assert result.managed
    assert result.failures
    assert any("unavailable" in failure for failure in result.failures)


def test_unrelated_branch_is_not_managed() -> None:
    assert scope.validate_scope(
        branch="phase-1-closure-process-400-unrelated",
        changed_files=["backend/app/main.py"],
        charged_line_count=1,
    ) == scope.ScopeEvaluation(False, ())


def test_repository_evaluation_derives_scope_from_git(monkeypatch: Any) -> None:
    monkeypatch.setattr(scope, "current_branch", lambda: CURRENT_BRANCH, raising=False)
    monkeypatch.setattr(
        scope, "legacy_checker", SimpleNamespace(resolve_base=lambda: "verified-base"), raising=False
    )
    monkeypatch.setattr(
        scope,
        "git_evidence",
        SimpleNamespace(
            changed_files=lambda base: sorted(CURRENT_FILES) if base == "verified-base" else None,
            charged_lines=lambda base: 500 if base == "verified-base" else None,
        ),
        raising=False,
    )
    assert scope.evaluate_repository_scope() == scope.ScopeEvaluation(True, ())


def test_runner_orders_scope_before_preserved_contracts(monkeypatch: Any) -> None:
    calls: list[object] = []
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: calls.append("publication") or 0)
    monkeypatch.setattr(
        runner,
        "evaluate_repository_scope",
        lambda: calls.append("recovery") or scope.ScopeEvaluation(True, ()),
        raising=False,
    )
    monkeypatch.setattr(runner, "run_preserved_contracts", lambda: calls.append("legacy") or 0)
    assert runner.main() == 0
    assert calls == ["publication", "recovery", "legacy"]


def test_runner_scope_failure_stops_preserved_contracts(monkeypatch: Any) -> None:
    calls: list[str] = []
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)
    monkeypatch.setattr(
        runner,
        "evaluate_repository_scope",
        lambda: scope.ScopeEvaluation(True, ("scope failed",)),
        raising=False,
    )
    monkeypatch.setattr(runner, "run_preserved_contracts", lambda: calls.append("legacy") or 0)
    assert runner.main() == 1
    assert calls == []


@pytest.mark.parametrize(("branch", "changed_calls"), [(CURRENT_BRANCH, 0), ("main", 1)])
def test_legacy_dispatch_skips_only_exact_managed_branch(
    monkeypatch: Any, branch: str, changed_calls: int
) -> None:
    calls: list[str] = []
    checker = SimpleNamespace(read=lambda _path: "\n".join(legacy.DEMO_MARKERS))
    for name in ("check_branch", "check_required_files", "check_changed_files", *legacy.PRESERVED_CHECKS):
        if name != "check_active_demo_docs":
            setattr(checker, name, lambda _failures, marker=name: calls.append(marker))
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "legacy_parity_failures", lambda _checker: [])
    monkeypatch.setattr(legacy, "current_branch", lambda: branch)
    monkeypatch.setattr(legacy, "check_active_demo_docs", lambda *_args: None)
    assert legacy.run_preserved_contracts() == 0
    assert calls.count("check_changed_files") == changed_calls


def test_frozen_legacy_receipts_remain_exact() -> None:
    assert legacy.frozen_file_failures() == []
