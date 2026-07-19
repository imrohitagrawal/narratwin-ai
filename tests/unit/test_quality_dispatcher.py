import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_dispatcher() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_quality_stage.py"
    spec = importlib.util.spec_from_file_location("quality_dispatcher_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_dispatcher(
    monkeypatch: Any,
    tmp_path: Path,
    *,
    branch: str,
    stage_marker: str = "8",
    status_text: str,
    policy_only: bool = False,
) -> list[list[str]]:
    dispatcher = load_dispatcher()
    stage_file = tmp_path / "current"
    stage_file.write_text(stage_marker, encoding="utf-8")
    status_file = tmp_path / "STATUS.md"
    status_file.write_text(status_text, encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status_file, raising=False)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda stage: 0)
    monkeypatch.setattr(dispatcher.subprocess, "call", lambda args, cwd=None: calls.append(list(args)) or 0)
    if policy_only:
        monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1")
    else:
        monkeypatch.delenv("NARRATWIN_POLICY_ONLY", raising=False)

    assert dispatcher.main() == 0
    return calls


PHASE1_STATUS = """
# Program Status

## StatusStateV1

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure | Phase 1 Closure remains active; release posture remains No-Go. |
""".strip()


STAGE8_STATUS = """
# Program Status

## StatusStateV1

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
| SSV1-MODE | repo-mode | Stage 8 | stage8 | stage8 | Stage 8 hardening mode. |
""".strip()


def test_main_dispatches_phase1_closure_when_status_state_says_phase1(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=PHASE1_STATUS)

    assert len(calls) == 1
    assert calls[0][-1] == "scripts/quality/check_phase1_closure_docs.py"


def test_phase1_closure_branch_dispatch_still_uses_phase1_gate(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch="phase-1-closure-208-ch-m1-02-demo-evidence",
        status_text=STAGE8_STATUS,
    )

    assert calls[0][-1] == "scripts/quality/check_phase1_closure_docs.py"


def test_main_stage8_dispatch_is_preserved_when_status_state_is_not_phase1(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=STAGE8_STATUS)

    assert calls == [["make", "stage8-quality"]]


def test_stage8_policy_only_dispatch_is_preserved_when_status_state_is_not_phase1(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=STAGE8_STATUS, policy_only=True)

    assert calls[0][-1] == "scripts/quality/check_stage8_docs.py"


def test_stage8_branch_dispatch_is_not_weakened_by_phase1_status(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch="stage8-performance-security-release-readiness",
        status_text=PHASE1_STATUS,
    )

    assert calls == [["make", "stage8-quality"]]
