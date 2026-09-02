from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from scripts.quality.phase1_closure import runner


def test_runner_checks_publication_and_cut1_before_preserved_contracts(monkeypatch: Any) -> None:
    calls: list[str] = []

    def publication() -> int:
        calls.append("new")
        return 0

    def preserved() -> int:
        calls.append("legacy")
        return 0

    def cut1() -> int:
        calls.append("cut1")
        return 0

    monkeypatch.setattr(runner, "check_publication_boundary", publication)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", cut1)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)

    assert runner.main() == 0
    assert calls == ["new", "cut1", "legacy"]


def test_publication_failure_prevents_legacy_continuation(monkeypatch: Any) -> None:
    calls: list[str] = []

    def publication() -> int:
        calls.append("new")
        return 17

    def preserved() -> int:
        calls.append("legacy")
        return 0

    def cut1() -> int:
        calls.append("cut1")
        return 0

    monkeypatch.setattr(runner, "check_publication_boundary", publication)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", cut1)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)

    assert runner.main() == 17
    assert calls == ["new"]


def test_cut1_failure_prevents_preserved_contract_continuation(monkeypatch: Any) -> None:
    calls: list[str] = []

    def publication() -> int:
        calls.append("publication")
        return 0

    def cut1() -> int:
        calls.append("cut1")
        return 23

    def preserved() -> int:
        calls.append("legacy")
        return 0

    monkeypatch.setattr(runner, "check_publication_boundary", publication)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", cut1)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)

    assert runner.main() == 23
    assert calls == ["publication", "cut1"]


def test_runner_propagates_preserved_contract_failure(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", lambda: 0)
    monkeypatch.setattr(runner, "run_preserved_contracts", lambda: 19)

    assert runner.main() == 19


def test_runner_redacts_unhandled_exception(monkeypatch: Any, capsys: Any) -> None:
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", lambda: 0)

    def fail() -> None:
        raise RuntimeError("sensitive implementation detail")

    monkeypatch.setattr(runner, "run_preserved_contracts", fail)

    assert runner.main() == 1
    output = capsys.readouterr().out
    assert "could not complete safely" in output
    assert "sensitive implementation detail" not in output


def test_issue456_preflight_supersedes_only_legacy_path_list(monkeypatch: Any) -> None:
    calls: list[str] = []

    def record(name: str) -> Any:
        return lambda failures: calls.append(name)

    checker = SimpleNamespace(
        check_branch=record("branch"),
        check_required_files=record("required"),
        check_changed_files=record("prohibited-legacy-scope"),
        check_final_review_baseline=record("preserved"),
    )
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE456_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_changed_paths", lambda head: runner.ISSUE456_PATHS)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: [])
    monkeypatch.setattr(runner.legacy, "PRESERVED_CHECKS", ("check_final_review_baseline",))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)

    assert runner.run_preserved_contracts() == 0
    assert calls == ["branch", "required", "preserved"]


def test_issue456_preflight_failure_blocks_preserved_checks(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE456_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_changed_paths", lambda head: runner.ISSUE456_PATHS)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [object()])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: (_ for _ in ()).throw(AssertionError("must not run")))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)

    assert runner.run_preserved_contracts() == 1


def test_coherent_preflight_with_extra_path_cannot_bypass_legacy_scope(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE456_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_changed_paths", lambda head: runner.ISSUE456_PATHS | {"extra/path"})
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: (_ for _ in ()).throw(AssertionError("must not run")))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)

    assert runner.run_preserved_contracts() == 1


def test_other_branch_retains_frozen_legacy_scope(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: "phase-1-closure-process-455-other")
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)

    assert runner.run_preserved_contracts() == 31


def test_issue391_route_validates_exact_scope_without_mutating_frozen_legacy(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []

    def record(name: str) -> Any:
        return lambda failures: calls.append(name)

    checker = SimpleNamespace(
        check_branch=record("branch"),
        check_required_files=record("required"),
        check_changed_files=record("prohibited-legacy-scope"),
        check_final_review_baseline=record("preserved"),
    )
    branch = "phase-1-closure-process-391-resource-lifecycle-enforcement"
    monkeypatch.setattr(runner, "current_branch", lambda root: branch)
    monkeypatch.setattr(runner, "_head", lambda: "b" * 40)
    monkeypatch.setattr(
        runner,
        "_changed_paths",
        lambda head, base: runner.ISSUE391_PATHS,
    )
    monkeypatch.setattr(
        runner,
        "validate_governance_preflight_repository",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: [])
    monkeypatch.setattr(
        runner.legacy,
        "PRESERVED_CHECKS",
        ("check_final_review_baseline",),
    )
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)
    monkeypatch.setattr(
        runner.legacy,
        "run_preserved_contracts",
        lambda: (_ for _ in ()).throw(AssertionError("must use exact Issue #391 route")),
    )

    assert runner.run_preserved_contracts() == 0
    assert calls == ["branch", "required", "preserved"]


def test_issue391_preflight_or_extra_path_blocks_preserved_checks(
    monkeypatch: Any,
) -> None:
    branch = runner.ISSUE391_BRANCH
    monkeypatch.setattr(runner, "current_branch", lambda root: branch)
    monkeypatch.setattr(runner, "_head", lambda: "b" * 40)
    monkeypatch.setattr(
        runner.legacy,
        "_load_checker",
        lambda: (_ for _ in ()).throw(AssertionError("must not run")),
    )
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1)

    monkeypatch.setattr(
        runner,
        "validate_governance_preflight_repository",
        lambda *args, **kwargs: [object()],
    )
    assert runner.run_preserved_contracts() == 1

    monkeypatch.setattr(
        runner,
        "validate_governance_preflight_repository",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        runner,
        "_changed_paths",
        lambda head, base: runner.ISSUE391_PATHS | {"extra/path"},
    )
    assert runner.run_preserved_contracts() == 1


def test_issue391_near_match_retains_frozen_legacy_scope(monkeypatch: Any) -> None:
    near_match = "phase-1-closure-process-392-resource-lifecycle-enforcement"
    monkeypatch.setattr(runner, "current_branch", lambda root: near_match)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 37)

    assert runner.run_preserved_contracts() == 37
