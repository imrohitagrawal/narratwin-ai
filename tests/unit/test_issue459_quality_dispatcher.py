from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from scripts.quality import check_quality_stage as dispatcher


BRANCH = "lane-a-cut1-459-controlled-presenter"
ROUTE = [sys.executable, "scripts/quality/check_stage8_docs.py"]
T04 = [sys.executable, "-I", "-P", "-m", "pytest", "-p", "no:cacheprovider",
       "-o", "addopts=", "-q", "tests/unit/test_cut1_controlled_presenter_red.py",
       "tests/unit/test_cut1_controlled_presenter.py"]


def invoke(
    monkeypatch: Any, tmp_path: Path, branch: str, *, policy_only: bool
) -> tuple[int, list[list[str]]]:
    current = tmp_path / "current"
    current.write_text("8\n", encoding="utf-8")
    calls: list[list[str]] = []

    def succeed(command: list[str], **_kwargs: object) -> int:
        calls.append(list(command))
        return 0

    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", current)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda _stage: 0)
    monkeypatch.setattr(getattr(dispatcher, "subprocess"), "call", succeed)
    monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1" if policy_only else "0")
    return dispatcher.main(), calls


@pytest.mark.parametrize(
    ("branch", "policy_only", "expected"),
    ((BRANCH, False, [ROUTE, T04]), (BRANCH, True, [ROUTE]),
     (BRANCH + "-evil", False, [["make", "stage8-quality"]])),
)
def test_issue459_dispatch_is_exact_and_policy_aware(
    monkeypatch: Any, tmp_path: Path, branch: str, policy_only: bool,
    expected: list[list[str]],
) -> None:
    exit_code, calls = invoke(monkeypatch, tmp_path, branch, policy_only=policy_only)
    assert exit_code == 0
    assert calls == expected


def test_issue459_route_failure_short_circuits_red(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fail(command: list[str], **_kwargs: object) -> int:
        calls.append(list(command))
        return 17

    monkeypatch.setattr(getattr(dispatcher, "subprocess"), "call", fail)
    assert dispatcher.run_cut1_controlled_presenter_entry_gate() == 17
    assert calls == [ROUTE]
