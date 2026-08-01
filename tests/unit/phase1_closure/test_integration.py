from __future__ import annotations

from typing import Any

from scripts.quality import check_phase1_closure_docs as legacy_gate
from scripts.quality.phase1_closure import integration


def test_issue324_scope_is_owned_outside_the_legacy_monolith() -> None:
    scope = integration.branch_scope(integration.ISSUE_324_BRANCH)

    assert scope is not None
    assert scope.allowed_files == integration.ISSUE_324_ALLOWED_CHANGED_FILES
    assert integration.branch_scope(f"{integration.ISSUE_324_BRANCH}-copy") is None
    assert integration.branch_scope("main") is None


def test_legacy_gate_delegates_issue324_scope_to_modular_policy(monkeypatch: Any) -> None:
    monkeypatch.setattr(legacy_gate, "current_branch", lambda: integration.ISSUE_324_BRANCH)
    monkeypatch.setattr(
        legacy_gate,
        "changed_files",
        lambda: sorted(integration.ISSUE_324_ALLOWED_CHANGED_FILES),
    )
    failures: list[str] = []

    legacy_gate.check_changed_files(failures)

    assert failures == []


def test_legacy_gate_rejects_extra_issue324_path(monkeypatch: Any) -> None:
    monkeypatch.setattr(legacy_gate, "current_branch", lambda: integration.ISSUE_324_BRANCH)
    monkeypatch.setattr(legacy_gate, "changed_files", lambda: ["backend/app/main.py"])
    failures: list[str] = []

    legacy_gate.check_changed_files(failures)

    assert failures == [
        f"Phase 1 Closure branch {integration.ISSUE_324_BRANCH} "
        "may not change backend/app/main.py."
    ]


def test_active_demo_document_is_neutral_and_legacy_markers_still_pass() -> None:
    assert integration.ACTIVE_DEMO_DOCUMENT == "docs/demo/CONTROLLED_LOCAL_DEMO.md"
    failures: list[str] = []

    legacy_gate.check_demo_docs(failures)

    assert failures == []
