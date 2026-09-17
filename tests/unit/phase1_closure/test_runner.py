from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.quality import issue521_successor
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

    def successor_check(root: Any) -> list[str]:
        calls.append("successor")
        return []
    monkeypatch.setattr(issue521_successor, "validate_repository", successor_check)
    assert runner.main() == 0
    assert calls == ["new", "cut1", "successor", "legacy"]


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


def test_issue521_runs_v2_validator_and_preserves_frozen_contracts(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = SimpleNamespace(
        check_branch=lambda failures: calls.append("branch"),
        check_required_files=lambda failures: calls.append("required"),
        check_changed_files=lambda failures: calls.append("legacy-scope"),
        check_final_review_baseline=lambda failures: calls.append("preserved"),
    )
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE521_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_issue521_scope", lambda: (frozenset({"one"}), []))
    monkeypatch.setattr(runner, "_changed_paths_since", lambda base, head: frozenset({"one"}))
    monkeypatch.setattr(runner, "_charged_lines", lambda base, head: 1)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: [])
    monkeypatch.setattr(runner.legacy, "PRESERVED_CHECKS", ("check_final_review_baseline",))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)
    def validate_v2(root: Any, certification: bool) -> list[str]:
        calls.append("v2")
        return []

    monkeypatch.setattr("scripts.quality.issue521_master_program_v2.validate_repository", validate_v2)

    assert runner.run_preserved_contracts() == 0
    assert calls == ["v2", "branch", "required", "preserved"]


def test_issue521_scope_binds_owner_amended_twenty_seven_paths() -> None:
    paths, failures = runner._issue521_scope()

    assert failures == []
    assert len(paths) == 27
    assert {
        ".gitleaksignore",
        "scripts/ci/check_gitleaks_regression.py",
        "tests/unit/test_gitleaks_regression.py",
    }.issubset(paths)


def test_issue521_preserves_audit_base_and_uses_accepted_integration_base() -> None:
    from scripts.quality import issue521_master_program_v2 as v2

    assert (v2.BASE_SHA, runner.ISSUE521_INTEGRATION_BASE) == (
        "b6b0c05c7227428ff0841361f3970b0b2c40aa86", "77661700e1019e7e73894a928e4e6aef774c5e75",
    )


def test_issue521_extra_path_fails_before_validator(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE521_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_issue521_scope", lambda: (frozenset({"one"}), []))
    monkeypatch.setattr(runner, "_changed_paths_since", lambda base, head: frozenset({"one", "extra"}))
    monkeypatch.setattr(runner, "_charged_lines", lambda base, head: 1)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [])
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: (_ for _ in ()).throw(AssertionError("must not run")))

    assert runner.run_preserved_contracts() == 1


def test_issue521_validator_failure_blocks_preserved_checks(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: runner.ISSUE521_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_issue521_scope", lambda: (frozenset({"one"}), []))
    monkeypatch.setattr(runner, "_changed_paths_since", lambda base, head: frozenset({"one"}))
    monkeypatch.setattr(runner, "_charged_lines", lambda base, head: 1)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        "scripts.quality.issue521_master_program_v2.validate_repository",
        lambda root, certification: ["MPV2.TEST.BLOCKED"],
    )
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: 1 if failures else 0)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: (_ for _ in ()).throw(AssertionError("must not run")))

    assert runner.run_preserved_contracts() == 1


def test_archive_scope_failure_prevents_legacy_pass(monkeypatch: Any) -> None:
    from scripts.quality import work_archive_scope

    monkeypatch.setattr(runner, "current_branch", lambda root: work_archive_scope.BRANCH)
    monkeypatch.setattr(work_archive_scope, "validate_scope", lambda *args: ["ARCHIVE_SCOPE_FILE_BUDGET"])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: (_ for _ in ()).throw(AssertionError("must not run")))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: int(bool(failures)))
    assert runner.run_preserved_contracts() == 1


def test_archive_lookalike_retains_legacy_scope(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: "phase-1-closure-process-535-work-archive-other")
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    assert runner.run_preserved_contracts() == 31


ISSUE519_BRANCH = "phase-1-closure-process-519-experiment-first-package"
ISSUE519_PREFLIGHT = "docs/governance/preflights/issue-519.json"


@pytest.fixture
def issue519(monkeypatch: Any) -> dict[str, Any]:
    raw = (runner.ROOT / ISSUE519_PREFLIGHT).read_bytes()
    manifest = json.loads(raw)
    paths = manifest["scope"]["required"]
    state: dict[str, Any] = {
        "manifest": raw, "paths": paths, "calls": [], "findings": [],
        "numstat": "".join(f"1\t0\t{path}\0" for path in paths).encode(),
    }

    def git(*args: str) -> bytes | None:
        if args[0] == "show":
            return state["manifest"]
        if args[:2] == ("diff", "--name-only"):
            return "".join(f"{path}\0" for path in state["paths"]).encode()
        if args[:2] == ("diff", "--numstat"):
            return state["numstat"]
        raise AssertionError(f"Unexpected git boundary: {args}")

    checker = runner.legacy._load_checker()
    monkeypatch.setattr(checker, "current_branch", lambda: ISSUE519_BRANCH)
    monkeypatch.setattr(checker, "changed_files", lambda: list(state["paths"]))

    def old_route() -> int:
        failures: list[str] = []
        checker.check_changed_files(failures)
        return int(bool(failures))

    fake = SimpleNamespace(
        check_branch=lambda failures: state["calls"].append("branch"),
        check_required_files=lambda failures: state["calls"].append("required"),
        check_final_review_baseline=lambda failures: state["calls"].append("preserved"),
    )
    monkeypatch.setattr(runner, "current_branch", lambda root: ISSUE519_BRANCH)
    monkeypatch.setattr(runner, "_head", lambda: "a" * 40)
    monkeypatch.setattr(runner, "_git", git)
    monkeypatch.setattr(runner, "validate_governance_preflight_repository", lambda *a, **k: state["findings"])
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", old_route)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: fake)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: [])
    monkeypatch.setattr(runner.legacy, "PRESERVED_CHECKS", ("check_final_review_baseline",))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: int(bool(failures)))
    return state


def test_issue519_exact_manifest_replaces_frozen_scope_only(issue519: dict[str, Any]) -> None:
    assert runner.run_preserved_contracts() == 0
    assert issue519["calls"] == ["branch", "required", "preserved"]


@pytest.mark.parametrize("mutation", ["extra", "missing", "substituted", "duplicate"])
def test_issue519_rejects_path_mismatch_before_preserved(issue519: dict[str, Any], mutation: str) -> None:
    paths = issue519["paths"][:]
    if mutation == "extra":
        paths.append("extra.md")
    elif mutation == "missing":
        paths.pop()
    elif mutation == "substituted":
        paths[-1] = "substitute.md"
    else:
        paths.append(paths[0])
    issue519["paths"] = paths
    assert runner.run_preserved_contracts() == 1
    assert issue519["calls"] == []


@pytest.mark.parametrize("mutation", ["per-file", "aggregate", "binary", "malformed", "unavailable", "negative", "duplicate", "missing"])
def test_issue519_rejects_uncountable_or_excess_lines(issue519: dict[str, Any], mutation: str) -> None:
    manifest = json.loads(issue519["manifest"])
    caps = manifest["change_budget"]["per_file_charged_lines"]
    records = [f"1\t0\t{path}" for path in issue519["paths"]]
    first = issue519["paths"][0]
    if mutation == "per-file":
        records[0] = f"{caps[first]}\t1\t{first}"
    elif mutation == "aggregate":
        records = [f"{cap}\t0\t{path}" for path, cap in caps.items()]
    elif mutation == "binary":
        records[0] = f"-\t-\t{first}"
    elif mutation == "malformed":
        records[0] = "1\t0"
    elif mutation == "negative":
        records[0] = f"-1\t0\t{first}"
    elif mutation == "duplicate":
        records.append(records[0])
    elif mutation == "missing":
        records.pop()
    issue519["numstat"] = None if mutation == "unavailable" else ("\0".join(records) + "\0").encode()
    assert runner.run_preserved_contracts() == 1
    assert issue519["calls"] == []


@pytest.mark.parametrize("mutation", ["bytes", "coherent-swap"])
def test_issue519_final_preflight_cannot_change_c1_authority(issue519: dict[str, Any], mutation: str) -> None:
    if mutation == "bytes":
        issue519["manifest"] += b"\n"
    else:
        manifest = json.loads(issue519["manifest"])
        old = manifest["scope"]["required"][-1]
        for key in ("required", "allowed_prefixes"):
            manifest["scope"][key][-1] = "substitute.md"
        caps = manifest["change_budget"]["per_file_charged_lines"]
        caps["substitute.md"] = caps.pop(old)
        issue519["manifest"] = json.dumps(manifest).encode()
        issue519["paths"][-1] = "substitute.md"
    assert runner.run_preserved_contracts() == 1
    assert issue519["calls"] == []


def test_issue519_repository_finding_blocks_preserved(issue519: dict[str, Any]) -> None:
    issue519["findings"] = [SimpleNamespace(code="GPF.REPO.PREFLIGHT_NOT_FIRST")]
    assert runner.run_preserved_contracts() == 1
    assert issue519["calls"] == []


@pytest.mark.parametrize("branch", ["phase-1-closure-process-519-experiment-first-package-other", "cut1-519-experiment-first-package"])
def test_issue519_lookalikes_retain_legacy_fallback(monkeypatch: Any, branch: str) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: branch)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    assert runner.run_preserved_contracts() == 31
