import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


ROOT = Path(__file__).parents[2]
BRANCH = "phase-1-closure-process-159-phf-mode1-release-evidence"
DECISION_VALUES = {
    "implementation_152": "merged",
    "issue_151": "open",
    "explicit_dated_acceptance": "absent",
    "historical_scan_role": "dated-history-not-current-absence",
    "hosted_release": "blocked",
    "production": "blocked",
    "public_distribution": "blocked",
}


def load_phase1_module() -> ModuleType:
    module_path = ROOT / "scripts" / "quality" / "check_phase1_closure_docs.py"
    spec = importlib.util.spec_from_file_location("issue159_phase1_docs_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


phase1: Any = load_phase1_module()


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def validate(*, checklist: str | None = None, readiness: str | None = None) -> list[str]:
    failures: list[str] = []
    phase1.check_issue159_release_security_evidence(
        failures,
        checklist if checklist is not None else read("docs/RELEASE_CHECKLIST.md"),
        readiness if readiness is not None else read("docs/RELEASE_READINESS_REVIEW.md"),
    )
    return failures


def decision_row(key: str) -> str:
    return f"| `{key}` | `{DECISION_VALUES[key]}` |"


def mutate_decision_record(document: str, *, key: str, mutation: str) -> str:
    row = decision_row(key)
    if mutation == "change":
        return document.replace(row, f"| `{key}` | `invalid` |", 1)
    if mutation == "remove":
        return document.replace(row + "\n", "", 1)
    if mutation == "duplicate":
        return document.replace(row, row + "\n" + row, 1)
    raise AssertionError(f"Unknown mutation: {mutation}")


def validate_document(relative_path: str, document: str) -> list[str]:
    if relative_path.endswith("RELEASE_CHECKLIST.md"):
        return validate(checklist=document)
    return validate(readiness=document)


def decision_record_block(document: str) -> str:
    start = document.index("## Current Security Decision Record")
    end = document.find("\n## ", start + 3)
    return document[start:] if end == -1 else document[start:end]


def test_issue159_release_evidence_accepts_reviewed_documents() -> None:
    assert validate() == []


def test_issue159_branch_accepts_only_its_exact_owned_files(monkeypatch: Any) -> None:
    expected_files = {
        "docs/RELEASE_CHECKLIST.md",
        "docs/RELEASE_READINESS_REVIEW.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_issue159_release_evidence.py",
    }
    assert phase1.ISSUE_159_ALLOWED_CHANGED_FILES == expected_files
    monkeypatch.setattr(phase1, "current_branch", lambda: BRANCH)
    monkeypatch.setattr(
        phase1,
        "changed_files",
        lambda: sorted(expected_files),
    )
    failures: list[str] = []

    phase1.check_changed_files(failures)

    assert failures == []


@pytest.mark.parametrize(
    "unexpected_file",
    (
        "docs/STATUS.md",
        "docs/PRD.md",
        "AGENTS.md",
        "scripts/guardrails_check.py",
        "backend/app/main.py",
        "docs/reviews/GO_NO_GO.md",
    ),
)
def test_issue159_branch_rejects_files_outside_exact_scope(
    monkeypatch: Any, unexpected_file: str
) -> None:
    monkeypatch.setattr(phase1, "current_branch", lambda: BRANCH)
    monkeypatch.setattr(phase1, "changed_files", lambda: [unexpected_file])
    failures: list[str] = []

    phase1.check_changed_files(failures)

    assert failures == [f"Phase 1 Closure branch {BRANCH} may not change {unexpected_file}."]


@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
@pytest.mark.parametrize("key", tuple(DECISION_VALUES))
@pytest.mark.parametrize("mutation", ("change", "remove", "duplicate"))
def test_issue159_rejects_changed_missing_or_duplicate_decision_fields(
    relative_path: str, key: str, mutation: str
) -> None:
    document = mutate_decision_record(read(relative_path), key=key, mutation=mutation)
    if relative_path.endswith("RELEASE_CHECKLIST.md"):
        failures = validate(checklist=document)
    else:
        failures = validate(readiness=document)

    assert any("Current Security Decision Record" in item for item in failures)


@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
def test_issue159_rejects_unknown_decision_field(relative_path: str) -> None:
    document = read(relative_path).replace(
        decision_row("public_distribution"),
        decision_row("public_distribution") + "\n| `unknown_claim` | `approved` |",
        1,
    )
    if relative_path.endswith("RELEASE_CHECKLIST.md"):
        failures = validate(checklist=document)
    else:
        failures = validate(readiness=document)

    assert any("unknown decision key" in item for item in failures)


@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
def test_issue159_rejects_free_form_claim_inside_decision_record(relative_path: str) -> None:
    document = read(relative_path).replace(
        "## Current Security Decision Record\n",
        "## Current Security Decision Record\n\nProduction deployment has been approved.\n",
        1,
    )
    if relative_path.endswith("RELEASE_CHECKLIST.md"):
        failures = validate(checklist=document)
    else:
        failures = validate(readiness=document)

    assert any("non-table claim" in item for item in failures)


@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
def test_issue159_rejects_second_decision_record_section(relative_path: str) -> None:
    document = read(relative_path)
    document += "\n\n" + decision_record_block(document) + "\n"

    failures = validate_document(relative_path, document)

    assert any("exactly one Current Security Decision Record section" in item for item in failures)


@pytest.mark.parametrize(
    "unexpected_row",
    (
        "| `extra_claim` | `approved` |",
        "| `unknown---claim` | `approved` |",
        "| `issue_151` | `open` | `extra` |",
    ),
)
@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
def test_issue159_rejects_any_noncanonical_pipe_row(
    relative_path: str, unexpected_row: str
) -> None:
    document = read(relative_path).replace(
        decision_row("public_distribution"),
        decision_row("public_distribution") + "\n" + unexpected_row,
        1,
    )

    failures = validate_document(relative_path, document)

    assert any("unexpected pipe row" in item for item in failures)


@pytest.mark.parametrize(
    ("mutation", "expected_failure"),
    (
        ("missing_section", "exactly one Current Security Decision Record section"),
        ("duplicate_header", "exactly one canonical header row"),
        ("changed_header", "exactly one canonical header row"),
        ("missing_separator", "exactly one canonical separator row"),
        ("duplicate_separator", "exactly one canonical separator row"),
        ("changed_separator", "exactly one canonical separator row"),
    ),
)
@pytest.mark.parametrize(
    "relative_path",
    ("docs/RELEASE_CHECKLIST.md", "docs/RELEASE_READINESS_REVIEW.md"),
)
def test_issue159_requires_exact_section_header_and_separator_counts(
    relative_path: str, mutation: str, expected_failure: str
) -> None:
    document = read(relative_path)
    if mutation == "missing_section":
        document = document.replace("## Current Security Decision Record", "## Removed Record", 1)
    elif mutation == "duplicate_header":
        document = document.replace(
            "| Decision key | Required value |",
            "| Decision key | Required value |\n| Decision key | Required value |",
            1,
        )
    elif mutation == "changed_header":
        document = document.replace(
            "| Decision key | Required value |",
            "| Decision | Value |",
            1,
        )
    elif mutation == "missing_separator":
        document = document.replace("|---|---|\n", "", 1)
    elif mutation == "duplicate_separator":
        document = document.replace("|---|---|", "|---|---|\n|---|---|", 1)
    elif mutation == "changed_separator":
        document = document.replace("|---|---|", "|:---|---:|", 1)
    else:
        raise AssertionError(f"Unknown mutation: {mutation}")

    failures = validate_document(relative_path, document)

    assert any(expected_failure in item for item in failures)


@pytest.mark.parametrize(
    "valid_boundary",
    (
        "Neither merge nor approval constitutes acceptance.",
        "Merge and approval never constitute acceptance.",
        "Historical evidence remains valid as dated history, not for current claims.",
    ),
)
def test_issue159_accepts_valid_boundary_prose_outside_decision_record(
    valid_boundary: str,
) -> None:
    readiness = read("docs/RELEASE_READINESS_REVIEW.md") + f"\n{valid_boundary}\n"

    assert validate(readiness=readiness) == []


@pytest.mark.parametrize("document", ("checklist", "readiness"))
def test_issue159_requires_negative_acceptance_boundary(document: str) -> None:
    checklist = read("docs/RELEASE_CHECKLIST.md")
    readiness = read("docs/RELEASE_READINESS_REVIEW.md")
    if document == "checklist":
        checklist = checklist.replace(
            "issue closure do not constitute",
            "issue closure constitute",
            1,
        )
    else:
        readiness = readiness.replace(
            "issue closure do not constitute",
            "issue closure constitute",
            1,
        )

    failures = validate(checklist=checklist, readiness=readiness)

    expected_location = "preamble" if document == "checklist" else "Decision section"
    assert any(
        expected_location in item and "missing issue #159 release-evidence marker" in item
        for item in failures
    )


@pytest.mark.parametrize("issue", ("#39", "#151"))
def test_issue159_checklist_opening_requires_both_live_conditions(issue: str) -> None:
    checklist = read("docs/RELEASE_CHECKLIST.md")
    opening, remainder = checklist.split("##", maxsplit=1)
    checklist = opening.replace(issue, "#removed", 1) + "##" + remainder

    failures = validate(checklist=checklist)

    assert any("preamble missing issue #159 release-evidence marker" in item for item in failures)
