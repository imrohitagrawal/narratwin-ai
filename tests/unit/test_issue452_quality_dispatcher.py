import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


BRANCH = "docs/cut1-acceptance-provider-contract-452"
ROUTE = [sys.executable, "scripts/quality/check_stage8_docs.py"]
ACCEPTANCE = [
    sys.executable,
    *"-I -P -m pytest -p no:cacheprovider -o addopts= -q tests/unit/test_cut1_presenter_contract.py".split(),
]
STATUS = """
# Program Status

## StatusStateV1

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
| SSV1-MODE | repo-mode | Stage 8 | stage8 | stage8 | Stage 8 hardening mode. |
""".strip()


def load_dispatcher() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts/quality/check_quality_stage.py"
    spec = importlib.util.spec_from_file_location("issue452_dispatcher", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dispatch(monkeypatch: Any, tmp_path: Path, branch: str, policy_only: bool = False) -> list[list[str]]:
    module = load_dispatcher()
    stage = tmp_path / "current"
    status = tmp_path / "STATUS.md"
    stage.write_text("8", encoding="utf-8")
    status.write_text(STATUS, encoding="utf-8")
    calls: list[list[str]] = []

    def record(args: list[str], **_kwargs: object) -> int:
        calls.append(list(args))
        return 0

    monkeypatch.setattr(module, "CURRENT_STAGE", stage)
    monkeypatch.setattr(module, "STATUS_DOC", status, raising=False)
    monkeypatch.setattr(module, "current_branch", lambda: branch)
    monkeypatch.setattr(module, "run_recommended_review_item_check", lambda _stage: 0)
    monkeypatch.setattr(module.subprocess, "call", record)
    if policy_only:
        monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1")
    else:
        monkeypatch.delenv("NARRATWIN_POLICY_ONLY", raising=False)
    assert module.main() == 0
    return calls


def test_exact_branch_dispatches_dedicated_gate(monkeypatch: Any, tmp_path: Path) -> None:
    assert dispatch(monkeypatch, tmp_path, BRANCH) == [ROUTE, ACCEPTANCE]


def test_policy_only_cannot_bypass_gate(monkeypatch: Any, tmp_path: Path) -> None:
    assert dispatch(monkeypatch, tmp_path, BRANCH, True) == [ROUTE, ACCEPTANCE]


def test_route_failure_stops_acceptance(monkeypatch: Any) -> None:
    module = load_dispatcher()
    calls: list[list[str]] = []

    def fail(args: list[str], **_kwargs: object) -> int:
        calls.append(args)
        return 17

    monkeypatch.setattr(module.subprocess, "call", fail)
    assert module.run_cut1_presenter_contract_gate() == 17
    assert calls == [ROUTE]


def test_near_match_has_no_authority(monkeypatch: Any, tmp_path: Path) -> None:
    assert dispatch(monkeypatch, tmp_path, BRANCH + "-evil") == [["make", "stage8-quality"]]
