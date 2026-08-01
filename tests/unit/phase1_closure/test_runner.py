from __future__ import annotations

from typing import Any

from scripts.quality.phase1_closure import runner


def test_runner_checks_publication_boundary_before_preserved_contracts(monkeypatch: Any) -> None:
    calls: list[str] = []

    def publication() -> int:
        calls.append("new")
        return 0

    def preserved() -> int:
        calls.append("legacy")
        return 0

    monkeypatch.setattr(runner, "check_publication_boundary", publication)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)

    assert runner.main() == 0
    assert calls == ["new", "legacy"]


def test_publication_failure_prevents_legacy_continuation(monkeypatch: Any) -> None:
    calls: list[str] = []

    def publication() -> int:
        calls.append("new")
        return 17

    def preserved() -> int:
        calls.append("legacy")
        return 0

    monkeypatch.setattr(runner, "check_publication_boundary", publication)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)

    assert runner.main() == 17
    assert calls == ["new"]


def test_runner_propagates_preserved_contract_failure(monkeypatch: Any) -> None:
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)
    monkeypatch.setattr(runner, "run_preserved_contracts", lambda: 19)

    assert runner.main() == 19


def test_runner_redacts_unhandled_exception(monkeypatch: Any, capsys: Any) -> None:
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)

    def fail() -> None:
        raise RuntimeError("sensitive implementation detail")

    monkeypatch.setattr(runner, "run_preserved_contracts", fail)

    assert runner.main() == 1
    output = capsys.readouterr().out
    assert "could not complete safely" in output
    assert "sensitive implementation detail" not in output
