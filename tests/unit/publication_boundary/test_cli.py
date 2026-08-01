from __future__ import annotations

from typing import Any


def configure_success(cli: Any, monkeypatch: Any, *, branch: str) -> None:
    monkeypatch.setattr(cli, "check_publication_boundary", lambda failures: None)
    monkeypatch.setattr(cli, "check_context_budgets", lambda failures: None)
    monkeypatch.setattr(cli, "current_branch", lambda: branch)
    monkeypatch.setattr(cli, "resolve_base", lambda: "base")
    monkeypatch.setattr(cli, "changed_files", lambda _base: ["docs/STATUS.md"])
    monkeypatch.setattr(cli, "charged_lines", lambda _base: 1)
    monkeypatch.setattr(cli, "validate_issue_scope", lambda **_kwargs: [])


def test_cli_runs_scope_only_for_issue324_family(
    publication_boundary: Any, monkeypatch: Any
) -> None:
    package = publication_boundary
    configure_success(package.cli, monkeypatch, branch=package.ISSUE_324_BRANCH)
    calls: list[dict[str, Any]] = []

    def record_scope(**kwargs: Any) -> list[str]:
        calls.append(kwargs)
        return []

    monkeypatch.setattr(
        package.cli,
        "validate_issue_scope",
        record_scope,
    )
    assert package.cli.main() == 0
    assert calls == [
        {
            "branch": package.ISSUE_324_BRANCH,
            "changed_files": ["docs/STATUS.md"],
            "charged_line_count": 1,
        }
    ]

    configure_success(package.cli, monkeypatch, branch="phase-1-closure-process-321-other")
    monkeypatch.setattr(
        package.cli,
        "validate_issue_scope",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("scope bypass")),
    )
    assert package.cli.main() == 0


def test_cli_rejects_unavailable_or_inconsistent_branch(
    publication_boundary: Any, monkeypatch: Any, capsys: Any
) -> None:
    package = publication_boundary
    configure_success(package.cli, monkeypatch, branch="")

    assert package.cli.main() == 1
    assert "branch evidence is unavailable or inconsistent" in capsys.readouterr().out


def test_cli_fails_closed_on_missing_evidence_or_internal_exception(
    publication_boundary: Any, monkeypatch: Any, capsys: Any
) -> None:
    package = publication_boundary
    configure_success(package.cli, monkeypatch, branch=package.ISSUE_324_BRANCH)
    monkeypatch.setattr(package.cli, "resolve_base", lambda: None)
    assert package.cli.main() == 1
    assert "diff base is unavailable" in capsys.readouterr().out

    monkeypatch.setattr(
        package.cli,
        "check_publication_boundary",
        lambda _failures: (_ for _ in ()).throw(RuntimeError("private detail")),
    )
    assert package.cli.main() == 1
    output = capsys.readouterr().out
    assert "could not complete safely" in output
    assert "private detail" not in output


def test_cli_bounds_failure_output(publication_boundary: Any, monkeypatch: Any, capsys: Any) -> None:
    package = publication_boundary
    monkeypatch.setattr(
        package.cli,
        "check_publication_boundary",
        lambda failures: failures.extend(f"failure-{index}" for index in range(200)),
    )
    monkeypatch.setattr(package.cli, "check_context_budgets", lambda failures: None)
    monkeypatch.setattr(package.cli, "current_branch", lambda: "main")
    assert package.cli.main() == 1
    output = capsys.readouterr().out.splitlines()
    assert len(output) <= package.reporting.MAX_FAILURES + 2
    assert output[-1] == "- Additional failures omitted."
