from __future__ import annotations

from typing import Any

import pytest


def test_owned_modules_replace_phase1_monolith_changes(publication_boundary: Any) -> None:
    package = publication_boundary
    expected = set(package.scope.PREFLIGHT_REQUIRED_FILES)
    assert package.ISSUE_324_BRANCH == "phase-1-closure-process-324-publication-boundary-v2"
    assert package.ISSUE_324_BASE_SHA == "11385d661e1da23f9be4101d9e8d3b3d2ca679e4"
    assert package.ISSUE_324_ALLOWED_CHANGED_FILES == expected
    assert len(expected) == 42
    assert "tests/unit/test_phase1_closure_docs.py" not in expected
    assert "scripts/quality/check_phase1_closure_docs.py" not in expected


def test_per_file_context_budgets_are_executable(publication_boundary: Any) -> None:
    package = publication_boundary
    assert package.IMPLEMENTATION_FILE_LINE_CAP == 250
    assert package.TEST_FILE_LINE_CAP == 250
    assert package.ENTRYPOINT_LINE_CAP == 40
    assert package.FILE_BYTE_CAP == 32_000
    assert package.MAX_LINE_LENGTH == 120
    failures: list[str] = []
    package.check_context_budgets(failures)
    assert failures == []


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        ((251, 1_000, 80), "exceeds 250 lines"),
        ((10, 32_001, 80), "exceeds 32000 bytes"),
        ((10, 1_000, 121), "contains a line over 120 characters"),
    ],
)
def test_context_budget_mutations_fail_closed(
    publication_boundary: Any,
    monkeypatch: pytest.MonkeyPatch,
    metrics: tuple[int, int, int],
    expected: str,
) -> None:
    package = publication_boundary
    monkeypatch.setattr(package.scope, "file_metrics", lambda _path: package.scope.FileMetrics(*metrics))
    failures: list[str] = []
    package.check_context_budgets(failures)
    assert any(expected in failure for failure in failures)


def test_scope_accepts_only_exact_branch_files_and_budget(publication_boundary: Any) -> None:
    package = publication_boundary
    assert package.validate_issue_scope(
        branch=package.ISSUE_324_BRANCH,
        changed_files=sorted(package.ISSUE_324_ALLOWED_CHANGED_FILES),
        charged_line_count=package.ISSUE_324_LINE_CAP,
    ) == []


def test_scope_rejects_near_branch_missing_extra_and_over_budget(
    publication_boundary: Any,
) -> None:
    package = publication_boundary
    expected = sorted(package.ISSUE_324_ALLOWED_CHANGED_FILES)
    failures = package.validate_issue_scope(
        branch=f"{package.ISSUE_324_BRANCH}-copy",
        changed_files=expected[1:] + ["backend/app/main.py"],
        charged_line_count=package.ISSUE_324_LINE_CAP + 1,
    )
    assert any("exact Issue #324 branch" in failure for failure in failures)
    assert any(expected[0] in failure and "must change" in failure for failure in failures)
    assert any("backend/app/main.py" in failure and "may not change" in failure for failure in failures)
    assert any("1800-line cap" in failure for failure in failures)


@pytest.mark.parametrize("count", [None, True, -1, 1.5])
def test_scope_rejects_untrusted_charged_line_counts(
    publication_boundary: Any, count: Any
) -> None:
    package = publication_boundary
    failures = package.validate_issue_scope(
        branch=package.ISSUE_324_BRANCH,
        changed_files=sorted(package.ISSUE_324_ALLOWED_CHANGED_FILES),
        charged_line_count=count,
    )
    assert failures == ["Issue #324 charged-line evidence is unavailable."]


def test_scope_rejects_duplicate_and_invalid_paths(publication_boundary: Any) -> None:
    package = publication_boundary
    expected = sorted(package.ISSUE_324_ALLOWED_CHANGED_FILES)
    failures = package.validate_issue_scope(
        branch=package.ISSUE_324_BRANCH,
        changed_files=expected + [expected[0], "../escape", "/absolute"],
        charged_line_count=0,
    )
    assert any("duplicate changed-file evidence" in failure for failure in failures)
    assert any("invalid changed-file path" in failure for failure in failures)


@pytest.mark.parametrize(
    ("numstat", "expected"),
    [("2\t3\tdocs/file.md\n", 5), ("-\t-\tbinary.bin\n", None), ("bad\n", None)],
)
def test_numstat_charging_fails_closed(numstat: str, expected: int | None, publication_boundary: Any) -> None:
    assert publication_boundary.scope.parse_numstat(numstat) == expected
