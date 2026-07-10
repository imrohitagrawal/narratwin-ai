from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_stage8_quality_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_stage8_docs.py"
    spec = importlib.util.spec_from_file_location("stage8_quality_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage8: Any = load_stage8_quality_module()


def test_issue84_guardrail_branch_allows_process_guardrail_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: [
            "docs/STATUS.md",
            "scripts/guardrails_check.py",
            "scripts/quality/check_stage8_docs.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_stage8_quality_gate.py",
        ],
    )

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)

    assert failures == []


def test_issue84_guardrail_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/stage4.py"])

    failures: list[str] = []
    stage8.check_stage_scope(failures)

    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/stage4.py"]


def test_non_stage8_non_process_branch_still_rejected(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/untracked-stage8-work")

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)

    assert failures == [
        "Stage 8 work must run on a stage8-* branch or main after merge; got feature/untracked-stage8-work."
    ]
