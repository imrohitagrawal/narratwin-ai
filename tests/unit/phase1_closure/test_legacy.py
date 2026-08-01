from __future__ import annotations

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


def test_issue324_uses_modular_scope_and_every_preserved_check_once(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: legacy.ISSUE_324_BRANCH)
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


def test_other_branches_keep_legacy_scope_check(monkeypatch: Any) -> None:
    calls: list[str] = []
    checker = fake_checker(calls)
    monkeypatch.setattr(legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(legacy, "current_branch", lambda: "main")
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
    checker = SimpleNamespace(
        read=lambda path: paths.append(path) or "\n".join(legacy.DEMO_MARKERS)
    )
    failures: list[str] = []

    legacy.check_active_demo_docs(checker, failures)

    assert failures == []
    assert legacy.ACTIVE_DEMO_DOCUMENT in paths
    assert legacy.LEGACY_DEMO_DOCUMENT not in paths
