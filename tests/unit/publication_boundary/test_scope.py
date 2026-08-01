from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest


def test_owned_modules_replace_phase1_monolith_changes(publication_boundary: Any) -> None:
    package = publication_boundary
    expected = set(package.scope.PREFLIGHT_REQUIRED_FILES)
    assert package.ISSUE_324_BRANCH == "phase-1-closure-process-324-publication-boundary-v2"
    assert package.ISSUE_324_BASE_SHA == "11385d661e1da23f9be4101d9e8d3b3d2ca679e4"
    assert package.ISSUE_324_ALLOWED_CHANGED_FILES == expected
    assert len(expected) == 58
    assert "tests/unit/test_phase1_closure_docs.py" not in expected
    assert "scripts/quality/check_phase1_closure_docs.py" not in expected


def test_per_file_context_budgets_are_executable(publication_boundary: Any) -> None:
    package = publication_boundary
    context = package.context
    assert context.IMPLEMENTATION_FILE_LINE_CAP == 250
    assert context.TEST_FILE_LINE_CAP == 250
    assert context.ENTRYPOINT_LINE_CAP == 40
    assert context.EXISTING_INTEGRATION_FILE_LINE_CAP == 500
    assert context.FILE_BYTE_CAP == 32_000
    assert context.MAX_LINE_LENGTH == 120
    failures: list[str] = []
    package.check_context_budgets(failures)
    assert failures == []


def test_context_budgets_cover_both_modular_packages_and_entrypoints(
    publication_boundary: Any,
) -> None:
    context = publication_boundary.context
    assert {path.name for path in context.IMPLEMENTATION_DIRECTORIES} == {
        "phase1_closure",
        "publication_boundary",
    }
    assert {path.name for path in context.TEST_DIRECTORIES} == {
        "phase1_closure",
        "publication_boundary",
    }
    assert {path.name for path in context.ENTRYPOINTS} == {
        "check_phase1_quality.py",
        "check_publication_boundary.py",
    }
    assert {path.name for path in context.EXISTING_INTEGRATION_FILES} == {
        "check_quality_stage.py",
        "check_stage8_docs.py",
    }
    assert {path.name for path in context.SHARED_IMPLEMENTATION_FILES} == {
        "branch_identity.py",
    }
    assert {path.name for path in context.FOCUSED_TEST_FILES} == {
        "test_branch_identity.py",
        "test_issue324_stage8_quality.py",
        "test_quality_dispatcher.py",
        "test_quality_stage_dispatch.py",
        "test_stage8_quality_gate.py",
    }


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
    monkeypatch.setattr(
        package.context,
        "file_metrics",
        lambda _path: package.context.FileMetrics(*metrics),
    )
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
    assert any("may not change" in failure for failure in failures)
    assert any("3700-line cap" in failure for failure in failures)


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
    assert any("invalid changed-file evidence" in failure for failure in failures)


def test_required_scope_files_must_be_regular_not_symlinks(
    publication_boundary: Any, monkeypatch: Any, tmp_path: Path
) -> None:
    context = publication_boundary.context
    target = tmp_path / "target.md"
    target.write_text("content", encoding="utf-8")
    alias = tmp_path / "docs" / "evidence.md"
    alias.parent.mkdir()
    alias.symlink_to(target)
    monkeypatch.setattr(context, "ROOT", tmp_path)
    monkeypatch.setattr(context, "PREFLIGHT_REQUIRED_FILES", ("docs/evidence.md",))
    for name in (
        "IMPLEMENTATION_DIRECTORIES",
        "TEST_DIRECTORIES",
        "ENTRYPOINTS",
        "EXISTING_INTEGRATION_FILES",
        "SHARED_IMPLEMENTATION_FILES",
        "FOCUSED_TEST_FILES",
    ):
        monkeypatch.setattr(context, name, ())
    failures: list[str] = []

    context.check_context_budgets(failures)

    assert failures == ["Issue #324 required regular file unavailable: docs/evidence.md."]


def test_new_owned_module_must_be_preflight_indexed(
    publication_boundary: Any, monkeypatch: Any
) -> None:
    context = publication_boundary.context
    omitted = "scripts/quality/publication_boundary/reporting.py"
    monkeypatch.setattr(
        context,
        "PREFLIGHT_REQUIRED_FILES",
        tuple(path for path in context.PREFLIGHT_REQUIRED_FILES if path != omitted),
    )
    failures: list[str] = []

    context.check_context_budgets(failures)

    assert f"Issue #324 owned context file is not indexed: {omitted}." in failures


@pytest.mark.parametrize(
    ("numstat", "expected"),
    [("2\t3\tdocs/file.md\n", 5), ("-\t-\tbinary.bin\n", None), ("bad\n", None)],
)
def test_numstat_charging_fails_closed(numstat: str, expected: int | None, publication_boundary: Any) -> None:
    assert publication_boundary.git_evidence.parse_numstat(numstat) == expected


@pytest.mark.parametrize("unsafe_kind", ["symlink", "oversized"])
def test_untracked_charging_rejects_unsafe_files_before_reading(
    publication_boundary: Any,
    monkeypatch: Any,
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    evidence = publication_boundary.git_evidence
    relative_path = "unsafe.txt"
    target = tmp_path / relative_path
    if unsafe_kind == "symlink":
        source = tmp_path / "source.txt"
        source.write_text("outside", encoding="utf-8")
        target.symlink_to(source)
    else:
        target.write_bytes(b"x" * (evidence.MAX_UNTRACKED_FILE_BYTES + 1))

    def git_result(*args: str) -> subprocess.CompletedProcess[bytes]:
        output = b"" if args[0] == "diff" else f"{relative_path}\0".encode()
        return subprocess.CompletedProcess([], 0, output, b"")

    monkeypatch.setattr(evidence, "ROOT", tmp_path)
    monkeypatch.setattr(evidence, "_run_git", git_result)

    assert evidence.charged_lines("base") is None
