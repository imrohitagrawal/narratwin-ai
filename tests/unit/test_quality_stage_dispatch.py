from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from scripts.quality import check_quality_stage as quality_stage


def configure_phase1_dispatch(
    monkeypatch: Any,
    tmp_path: Path,
    statuses: list[int],
    *,
    branch: str = "phase-1-closure-process-324-publication-boundary-v2",
) -> list[list[str]]:
    stage_file = tmp_path / "current"
    stage_file.write_text("8\n", encoding="utf-8")
    monkeypatch.setattr(quality_stage, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(quality_stage, "current_branch", lambda: branch)
    monkeypatch.setattr(quality_stage, "phase1_closure_mode_active", lambda: True)
    monkeypatch.setattr(quality_stage, "run_recommended_review_item_check", lambda _stage: 0)
    calls: list[list[str]] = []

    def fake_call(args: list[str], *, cwd: Path) -> int:
        assert cwd == quality_stage.ROOT
        calls.append(args)
        return statuses.pop(0)

    monkeypatch.setattr(quality_stage.subprocess, "call", fake_call)
    return calls


def test_phase1_quality_dispatch_runs_modular_phase1_runner(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls = configure_phase1_dispatch(monkeypatch, tmp_path, [0])
    assert quality_stage.main() == 0
    assert calls == [[sys.executable, "scripts/quality/check_phase1_quality.py"]]


def test_phase1_quality_dispatch_propagates_runner_failure(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls = configure_phase1_dispatch(monkeypatch, tmp_path, [17])
    assert quality_stage.main() == 17
    assert calls == [[sys.executable, "scripts/quality/check_phase1_quality.py"]]


def test_merged_main_phase1_mode_still_runs_modular_gate(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls = configure_phase1_dispatch(monkeypatch, tmp_path, [0], branch="main")
    assert quality_stage.main() == 0
    assert calls[-1] == [sys.executable, "scripts/quality/check_phase1_quality.py"]
