from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from scripts.quality.phase1_closure import legacy


EXPECTED_PRESERVED_CHECKS = (
    "check_final_review_baseline",
    "check_closure_report",
    "check_golden_questions",
    "check_active_demo_docs",
    "check_real_media_demo_plan",
    "check_release_docs",
    "check_issue39_closure_plan",
    "check_issue125_local_restore_contract",
    "check_issue141_platform_ownership_contract",
    "check_issue126_restore_readiness_contract",
    "check_issue39_execution_strategy",
    "check_issue39_ch11_slo_contract",
    "check_phf020a_policy_contract",
    "check_status_state_v1_contract",
    "check_process_docs",
    "check_issue158_security_history_contract",
    "check_issue300_semantic_governance",
    "check_issue313_repair_feasibility",
    "check_issue319_agent_context",
)


def fake_checker(calls: list[str]) -> SimpleNamespace:
    module = SimpleNamespace()
    for name in (
        "check_branch",
        "check_required_files",
        "check_changed_files",
        *[item for item in EXPECTED_PRESERVED_CHECKS if item != "check_active_demo_docs"],
    ):
        setattr(module, name, lambda _failures, marker=name: calls.append(marker))
    module.read = lambda _path: "\n".join(legacy.DEMO_MARKERS)
    return module


def test_preserved_check_registry_matches_legacy_main_order() -> None:
    assert legacy.PRESERVED_CHECKS == EXPECTED_PRESERVED_CHECKS


def test_real_legacy_source_matches_runner_parity_contract() -> None:
    checker = legacy._load_checker()

    assert legacy.legacy_parity_failures(checker) == []


def test_whole_legacy_files_are_frozen_against_silent_growth(
    monkeypatch: Any, tmp_path: Path
) -> None:
    assert legacy.frozen_file_failures() == []
    monkeypatch.setattr(legacy, "ROOT", tmp_path)
    for relative_path, _digest, _lines in legacy.FROZEN_LEGACY_FILES:
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("appended responsibility\n", encoding="utf-8")

    failures = legacy.frozen_file_failures()

    assert len(failures) == 2
    assert all("receipt drifted" in failure for failure in failures)


def test_issue324_uses_modular_scope_and_every_preserved_check_once(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: legacy.ISSUE_324_BRANCH)
    monkeypatch.setattr(legacy, "legacy_parity_failures", lambda _checker: [])
    monkeypatch.setattr(
        legacy,
        "check_active_demo_docs",
        lambda _checker, _failures: calls.append("check_active_demo_docs"),
    )

    assert legacy.run_preserved_contracts() == 0
    assert calls == [
        "check_branch",
        "check_required_files",
        *EXPECTED_PRESERVED_CHECKS,
    ]
    assert calls.count("check_changed_files") == 0


def test_issue324_preserves_internal_changed_file_evidence_calls(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)

    def changed_files() -> set[str]:
        calls.append("internal_changed_files")
        return set()

    def check_process_docs(_failures: list[str]) -> None:
        calls.append("check_process_docs")
        checker.changed_files()

    checker.changed_files = changed_files
    checker.check_process_docs = check_process_docs
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: legacy.ISSUE_324_BRANCH)
    monkeypatch.setattr(legacy, "legacy_parity_failures", lambda _checker: [])
    monkeypatch.setattr(legacy, "check_active_demo_docs", lambda _checker, _failures: None)

    assert legacy.run_preserved_contracts() == 0
    assert calls.count("internal_changed_files") == 1
    assert calls.count("check_process_docs") == 1


def test_inconsistent_branch_evidence_stops_before_legacy_checks(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: "")
    monkeypatch.setattr(legacy, "legacy_parity_failures", lambda _checker: [])

    assert legacy.run_preserved_contracts() == 1
    assert calls == []


def test_other_branches_keep_legacy_scope_check(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: "main")
    monkeypatch.setattr(legacy, "legacy_parity_failures", lambda _checker: [])
    monkeypatch.setattr(
        legacy,
        "check_active_demo_docs",
        lambda _checker, _failures: calls.append("check_active_demo_docs"),
    )

    assert legacy.run_preserved_contracts() == 0
    assert calls[:3] == ["check_branch", "check_required_files", "check_changed_files"]


def test_active_demo_contract_rejects_each_missing_marker() -> None:
    for missing in legacy.DEMO_MARKERS:
        checker = SimpleNamespace(
            read=lambda _path, omitted=missing: "\n".join(
                marker for marker in legacy.DEMO_MARKERS if marker != omitted
            )
        )
        failures: list[str] = []

        legacy.check_active_demo_docs(checker, failures)

        assert failures == [f"Phase 1 demo docs missing marker: {missing}"]


def test_active_demo_contract_uses_only_neutral_replacement() -> None:
    paths: list[str] = []

    def read(path: str) -> str:
        paths.append(path)
        return "\n".join(legacy.DEMO_MARKERS)

    checker = SimpleNamespace(
        read=read
    )
    failures: list[str] = []

    legacy.check_active_demo_docs(checker, failures)

    assert failures == []
    assert legacy.ACTIVE_DEMO_DOCUMENT in paths
    assert legacy.LEGACY_DEMO_DOCUMENT not in paths


def test_legacy_parity_mutations_fail_closed(monkeypatch: Any) -> None:
    checker = legacy._load_checker()
    source = "def main():\n    check_branch([])\n"
    monkeypatch.setattr(getattr(legacy, "inspect"), "getsource", lambda _function: source)

    failures = legacy.legacy_parity_failures(checker)

    assert "Frozen Phase 1 checker source digest drifted." in failures
    assert "Frozen Phase 1 demo source digest drifted." in failures
    assert "Frozen Phase 1 checker call order drifted." in failures
    assert "Frozen Phase 1 demo marker contract drifted." in failures


def test_failure_output_is_bounded(capsys: Any) -> None:
    failures = [f"failure-{index}" for index in range(legacy.MAX_FAILURES + 5)]

    assert legacy._print_result(failures) == 1
    output = capsys.readouterr().out
    assert "failure-49" in output
    assert "failure-50" not in output
    assert "Additional failures omitted." in output
