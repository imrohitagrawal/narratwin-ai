from __future__ import annotations

from typing import Any


def test_owned_modules_replace_phase1_monolith_changes(publication_boundary: Any) -> None:
    package = publication_boundary
    expected = set(package.repository.PREFLIGHT_REQUIRED_FILES)
    assert package.ISSUE_324_BRANCH == "phase-1-closure-process-324-publication-boundary-v2"
    assert package.ISSUE_324_ALLOWED_CHANGED_FILES == expected
    assert package.ISSUE_324_LINE_CAP == 1800
    assert "tests/unit/test_phase1_closure_docs.py" not in expected
    assert "scripts/quality/check_phase1_closure_docs.py" not in expected


def test_per_file_context_budgets_are_executable(publication_boundary: Any) -> None:
    package = publication_boundary
    assert package.IMPLEMENTATION_FILE_LINE_CAP == 250
    assert package.TEST_FILE_LINE_CAP == 250
    assert package.ENTRYPOINT_LINE_CAP == 40
    failures: list[str] = []
    package.check_context_budgets(failures)
    assert failures == []


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
