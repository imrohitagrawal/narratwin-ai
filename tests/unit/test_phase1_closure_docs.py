import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, cast

import pytest


def load_phase1_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_phase1_closure_docs.py"
    spec = importlib.util.spec_from_file_location("phase1_closure_docs_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


phase1: Any = load_phase1_module()


def read_with_overrides(phase1_module: Any, overrides: dict[str, str]) -> Callable[[str], str]:
    original_read = cast(Callable[[str], str], phase1_module.read)

    def patched_read(rel: str) -> str:
        if rel in overrides:
            return overrides[rel]
        return original_read(rel)

    return patched_read


def replace_text(text: str, search: str, replacement: str) -> str:
    return text.replace(search, replacement, 1)


def run_changed_files_check(monkeypatch: Any, *, branch: str, files: list[str]) -> list[str]:
    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "changed_files", lambda: files)
    failures: list[str] = []
    phase1.check_changed_files(failures)
    return failures


def run_process_docs_check(
    monkeypatch: Any, *, branch: str, changed: list[str], read_overrides: dict[str, str] | None = None
) -> list[str]:
    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "changed_files", lambda: changed)
    if read_overrides:
        monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_process_docs(failures)
    return failures


def run_issue39_closure_plan_check(monkeypatch: Any, *, plan_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": plan_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue39_closure_plan(failures)
    return failures


def run_issue39_execution_strategy_check(monkeypatch: Any, *, strategy_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md": strategy_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue39_execution_strategy(failures)
    return failures


def run_release_docs_check(monkeypatch: Any, *, read_overrides: dict[str, str]) -> list[str]:
    monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_release_docs(failures)
    return failures


def issue39_plan_with_closed_row_and_record(
    plan_text: str,
    *,
    matrix_id: str = "DUR-ACID-001",
    row_status_search: str,
    row_status_replacement: str,
    child_reference: str = (
        "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
        "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
    ),
    artifact_reference: str = "docs/ADR/0013-production-durability.md",
    evidence: str = (
        "tests/unit/test_phase1_closure_docs.py::test_issue39_closure_plan_accepts_current_matrix "
        "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123456789"
    ),
    owner: str = "Storage owner",
    reviewer: str = "Architecture reviewer",
    residual_risk: str = "Accepted with production row evidence",
    timestamp: str = "merge commit abc123",
    satisfies: str = "production-grade evidence satisfies the row",
) -> str:
    plan_text = replace_text(plan_text, row_status_search, row_status_replacement)
    record = (
        f"| `{matrix_id}` | {child_reference} | {artifact_reference} | {evidence} | "
        f"{owner} | {reviewer} | {residual_risk} | {timestamp} | {satisfies} |\n"
    )
    return plan_text.replace(
        "|---|---|---|---|---|---|---|---|---|\n",
        "|---|---|---|---|---|---|---|---|---|\n" + record,
        1,
    )


def test_process_only_phase1_branch_allows_governance_guardrail_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-55-phf-006-scope-gate",
        files=[
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue72_process_branch_allows_closure_evidence_contract_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-72-closure-evidence-hardening",
        files=[
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue72_process_branch_rejects_unrelated_review_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-72-closure-evidence-hardening",
        files=["docs/reviews/unrelated.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-process-72-closure-evidence-hardening may not change "
        "docs/reviews/unrelated.md."
    ]


def test_issue39_closure_plan_accepts_current_matrix() -> None:
    failures: list[str] = []
    phase1.check_issue39_closure_plan(failures)

    assert failures == []


def test_issue39_closure_plan_rejects_missing_required_matrix_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `OPS-WATCH-001` | First-hour watch with follow-up checkpoints | Triage cadence and owner communication for the first 60 minutes, plus explicit 120/180-minute follow-up checkpoints | Release/Operations | Active watch log template, handoff rules, timeout actions, rollback escalation threshold | Open |\n",
            "",
        ),
    )

    assert "Issue #39 production closure plan missing matrix IDs: OPS-WATCH-001" in failures


def test_issue39_closure_plan_rejects_invalid_matrix_status(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |",
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Done |",
        ),
    )

    assert "Issue #39 matrix row DUR-ACID-001 status must be Open or Closed; got Done." in failures


def test_issue39_closure_plan_rejects_closed_row_without_closure_record(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |",
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Closed |",
        ),
    )

    assert "Issue #39 matrix row DUR-ACID-001 is Closed without a row closure record." in failures


def test_issue39_closure_plan_accepts_closed_row_with_valid_closure_record(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    row_closed = row_open.replace("| Open |", "| Closed |")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_closed,
        ),
    )

    assert failures == []


def test_issue39_closure_plan_rejects_closed_row_with_external_repo_pr(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/example/other-repo/pull/102"
            ),
        ),
    )

    assert (
        "Issue #39 closed row DUR-ACID-001 must cite concrete same-repository child issue and PR URLs."
        in failures
    )


def test_issue39_closure_plan_rejects_context0_pr_as_final_proof(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/64"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must not use Context 0 PR #64 as final proof." in failures


def test_issue39_closure_plan_rejects_planning_pr_as_final_proof(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/80"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must not use planning PRs #64-#80 as final proof: #80" in failures


def test_issue39_closure_plan_rejects_parent_issue_as_child_issue(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/39 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must cite a child issue distinct from #39." in failures


def test_issue39_closure_plan_rejects_vague_artifact_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="artifact attached in PR",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_test_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_nonexistent_evidence",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_test_even_with_artifact_url(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence=(
                "test_issue39_nonexistent_evidence "
                "https://github.com/imrohitagrawal/narratwin-ai/blob/main/docs/STATUS.md"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_bare_existing_test_name_without_node_and_ci(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix restore drill rto rpo",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_node_id_without_ci_or_drill_artifact(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="tests/unit/test_phase1_closure_docs.py::test_issue39_closure_plan_accepts_current_matrix",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_issue_pr_urls_as_validation_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_bare_drill_log_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="drill log reviewed",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_drill_log_path(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/reviews/no_such_drill.md drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_drill_log_path_traversal(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/../.git/config drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_existing_unrelated_drill_log_file(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/evals/phase1_golden_questions.jsonl drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_malformed_actions_run_url(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123fake",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_ops_row_without_row_specific_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="human-only evidence reviewed",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        "Issue #39 closed row DUR-RESTORE-001 missing operational closure evidence terms: "
        "restore drill; rto; rpo"
    ) in failures


def test_issue39_closure_plan_rejects_operational_human_only_keyword_prose(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="human-only restore drill rto rpo reviewed by ops",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_sensitive_row_without_row_specific_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `PROVIDER-POSTURE-001` | Provider release posture | External provider legal, license, network, "
        "egress, key, and rollout controls | Security/Privacy + Platform | Provider release checklist with "
        "legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production "
        "enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and "
        "rollback disablement evidence | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="PROVIDER-POSTURE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        "Issue #39 closed row PROVIDER-POSTURE-001 missing operational closure evidence terms: "
        "provider; legal/license; egress; key; explicit production enablement"
    ) in failures


@pytest.mark.parametrize(
    ("matrix_id", "row_open", "expected_terms"),
    [
        (
            "MEDIA-CONSENT-001",
            "| `MEDIA-CONSENT-001` | Consent capture | Affirmative consent record for synthetic-media generation | Security/Privacy | Consent schema with actor, timestamp, consent text/version, artifact refs, source-run binding, scope, and audit retention | Open |",
            "consent; actor; scope; audit",
        ),
        (
            "SEC-UNTRUSTED-001",
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted | Security/Privacy + Runtime + Ops | Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content | Open |",
            "untrusted; validation; output encoding; log redaction",
        ),
    ],
)
def test_issue39_closure_plan_rejects_media_and_sec_rows_without_row_specific_evidence(
    monkeypatch: Any,
    matrix_id: str,
    row_open: str,
    expected_terms: str,
) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id=matrix_id,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        f"Issue #39 closed row {matrix_id} missing operational closure evidence terms: "
        f"{expected_terms}"
    ) in failures


def test_issue39_closure_plan_rejects_provider_closure_without_enablement_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `PROVIDER-POSTURE-001` | Provider release posture | External provider legal, license, network, "
        "egress, key, and rollout controls | Security/Privacy + Platform | Provider release checklist with "
        "legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production "
        "enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and "
        "rollback disablement evidence | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="PROVIDER-POSTURE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="provider legal/license egress key evidence",
        ),
    )

    assert (
        "Issue #39 closed row PROVIDER-POSTURE-001 missing operational closure evidence terms: "
        "explicit production enablement"
    ) in failures


def test_issue39_closure_plan_rejects_weakened_sensitive_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(plan_text, "restored artifacts", "restored records"),
    )

    assert (
        "Issue #39 matrix row SEC-UNTRUSTED-001 missing required contract terms: restored artifacts"
        in failures
    )


def test_issue39_closure_plan_rejects_weakened_provider_enablement(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(plan_text, "explicit production enablement", "production review"),
    )

    assert (
        "Issue #39 matrix row PROVIDER-POSTURE-001 missing required contract terms: "
        "explicit production enablement"
    ) in failures


def test_issue39_closure_plan_rejects_malformed_matrix_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted | Security/Privacy + Runtime + Ops | Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content | Open |",
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Open |",
        ),
    )

    assert "Issue #39 matrix row must have 6 columns:" in failures[0]


def test_issue39_execution_strategy_accepts_current_chunk_plan() -> None:
    failures: list[str] = []
    phase1.check_issue39_execution_strategy(failures)

    assert failures == []


def test_issue39_execution_strategy_rejects_missing_matrix_id(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("`SEC-UNTRUSTED-001`", "`SEC-RETENTION-001`"),
    )

    assert "Issue #39 execution strategy missing matrix IDs: SEC-UNTRUSTED-001" in failures


def test_issue39_execution_strategy_rejects_missing_chunk_even_with_matrix_id_preserved(
    monkeypatch: Any,
) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    strategy_text = strategy_text.replace(
        "| `CH-21` retention and erasure | `SEC-RETENTION-001` |",
        "| `CH-21` retention and erasure | `SEC-RETENTION-001`, `SEC-UNTRUSTED-001` |",
        1,
    )
    strategy_text = strategy_text.replace(
        "| `CH-22` untrusted replayed input | `SEC-UNTRUSTED-001` | `CH-03`, `CH-07`, `CH-08`, `CH-21` | Security/runtime | Untrusted-input preflight covering uploads, prompts, transcripts, provider outputs, restored artifacts, metadata | Security/privacy reviewer, runtime reviewer, operations reviewer | Durable and replayed content is revalidated, encoded, redacted, and protected from poisoned retrieval and prompt injection. |\n",
        "",
        1,
    )
    failures = run_issue39_execution_strategy_check(monkeypatch, strategy_text=strategy_text)

    assert "Issue #39 execution strategy missing chunks: CH-22" in failures
    assert (
        "Issue #39 execution strategy chunk CH-21 matrix IDs must be SEC-RETENTION-001; "
        "got SEC-RETENTION-001, SEC-UNTRUSTED-001."
    ) in failures


def test_issue39_execution_strategy_rejects_dependency_cycle(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(
            "| `CH-08` Stage 7 render artifact state | `DUR-STAGE7-001` | `CH-03`, `CH-04`, `CH-16` |",
            "| `CH-08` Stage 7 render artifact state | `DUR-STAGE7-001` | `CH-03`, `CH-04`, `CH-16`, `CH-18` |",
            1,
        ),
    )

    assert "Issue #39 execution strategy has dependency cycle:" in "\n".join(failures)


def test_issue39_execution_strategy_rejects_missing_final_dependency(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(", `CH-22` | Final sequential", " | Final sequential", 1),
    )

    assert "Issue #39 execution strategy chunk CH-23 dependencies must be" in "\n".join(failures)


def test_issue39_execution_strategy_rejects_missing_deployment_stop_rule(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("Failed production transition probes halt before enablement", "Probe failures are handled", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Deployment Transition Plan missing required terms: "
        "Failed production transition probes halt before enablement"
    ) in failures


def test_issue39_execution_strategy_rejects_weakened_dod_review_loop(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("re-reviewed by a fresh reviewer", "checked again", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Chunk Definition Of Done missing required terms: "
        "re-reviewed by a fresh reviewer"
    ) in failures


@pytest.mark.parametrize(
    "term",
    [
        "documented human-only evidence surface",
        "fixed",
        "rejected with evidence",
        "non-goal with rationale",
        "human-only follow-up",
    ],
)
def test_issue39_execution_strategy_rejects_weakened_dod_disposition_terms(
    monkeypatch: Any,
    term: str,
) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(term, "removed required DoD term", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Chunk Definition Of Done missing required terms: "
        f"{term}"
    ) in failures


def test_issue39_execution_strategy_rejects_weakened_ch10_metric_contract(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(
            "restore and rollback metric emissions close with `CH-14` and `CH-15` evidence",
            "restore and rollback metric emissions are complete in this chunk",
            1,
        ),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md CH-10 row missing required terms: "
        "restore and rollback metric emissions close with `ch-14` and `ch-15`"
    ) in failures


def test_issue39_execution_strategy_rejects_missing_rereview_protocol(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("## Re-Review After Fixes", "## Review Fix Handling", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md missing required heading: Re-Review After Fixes"
        in failures
    )


def test_issue39_execution_strategy_branch_allows_strategy_doc(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        files=[
            "docs/QUALITY_GATES.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_execution_strategy_branch_rejects_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-execution-strategy may not change backend/app/stage4.py."
    ]


def test_issue39_unknown_generic_chunk_branch_rejects_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-99-unreviewed-kernel",
        files=["backend/app/storage/postgres_state.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-99-unreviewed-kernel may not change "
        "backend/app/storage/postgres_state.py."
    ]


def test_issue39_ch02_branch_allows_storage_kernel_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0014-ch02-acid-cas-storage-kernel.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_postgres_state.py",
        ],
    )

    assert failures == []


def test_issue39_ch02_branch_rejects_stage_runtime_or_later_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change backend/app/stage4.py."
    ]


def test_issue39_ch02_branch_rejects_adjacent_chunk_or_issue39_doc_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=[
            "backend/app/storage/migrations.py",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change backend/app/storage/migrations.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md.",
    ]


def test_status_keeps_issue39_open_while_matrix_rows_are_open(monkeypatch: Any) -> None:
    status_text = phase1.read("docs/STATUS.md")
    failures = run_release_docs_check(
        monkeypatch,
        read_overrides={
            "docs/STATUS.md": status_text.replace(
                "| `#39` | Open, partially remediated |",
                "| `#39` | Closed |",
                1,
            )
        },
    )

    assert "docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open." in failures


def test_status_rejects_closed_issue39_with_open_substring(monkeypatch: Any) -> None:
    status_text = phase1.read("docs/STATUS.md")
    failures = run_release_docs_check(
        monkeypatch,
        read_overrides={
            "docs/STATUS.md": status_text.replace(
                "| `#39` | Open, partially remediated |",
                "| `#39` | Closed (no reopening planned) |",
                1,
            )
        },
    )

    assert "docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open." in failures


def test_process_only_phase1_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-55-phf-006-scope-gate",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-process-55-phf-006-scope-gate may not change backend/app/stage4.py."
    ]


def test_issue39_durability_branch_keeps_existing_runtime_allowlist(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-durability-monitoring",
        files=["backend/app/stage4.py"],
    )

    assert failures == []


def test_issue39_context1_issue65_branch_allows_schema_boundary_adr(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context1-postgresql-durability-adr",
        files=["docs/ADR/0008-postgresql-durability-schema-boundary.md"],
    )

    assert failures == []


def test_issue39_context1_issue65_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context1-postgresql-durability-adr",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context1-postgresql-durability-adr may not change backend/app/stage4.py."
    ]


def test_issue39_context2_issue66_branch_allows_idempotency_lease_outbox_adr(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context2-idempotency-lease-outbox",
        files=[
            "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context2_issue66_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context2-idempotency-lease-outbox",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context2-idempotency-lease-outbox may not change backend/app/stage4.py."
    ]


def test_issue39_context3_issue67_branch_allows_migrations_and_plan_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=[
            "docs/ADR/0010-context3-migrations-rollback-compatibility.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context3_issue67_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=["backend/app/stage6.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context3-migrations-rollback may not change backend/app/stage6.py."
    ]


def test_issue39_context3_issue67_branch_rejects_unrelated_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=["docs/unrelated-runtime-plan.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context3-migrations-rollback may not change "
        "docs/unrelated-runtime-plan.md."
    ]


def test_issue39_ch01_branch_allows_migration_baseline_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/migrations.py",
            "docs/ADR/0013-ch01-migration-baseline-runner.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_storage_migrations.py",
        ],
    )

    assert failures == []


def test_issue39_ch01_branch_rejects_unrelated_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch01-migration-baseline may not change backend/app/stage4.py."
    ]


def test_issue39_ch01_branch_rejects_broader_issue39_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=["backend/app/storage/file_state.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch01-migration-baseline may not change "
        "backend/app/storage/file_state.py."
    ]


def test_issue39_context4_issue68_branch_allows_backup_restore_drill_artifacts(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context4-backup-restore-drill",
        files=[
            "docs/ADR/0011-context4-backup-restore-drill.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context4_issue68_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context4-backup-restore-drill",
        files=["backend/app/stage7.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context4-backup-restore-drill may not change backend/app/stage7.py."
    ]


def test_issue39_context5_issue69_branch_allows_metrics_slos_watch_planning_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context5-metrics-slos-watch",
        files=[
            "docs/ADR/0012-context5-metrics-slos-watch.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context5_issue69_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context5-metrics-slos-watch",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context5-metrics-slos-watch may not change backend/app/stage4.py."
    ]


def test_issue39_context6_issue70_branch_allows_planning_and_governance_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context6-media-provider-posture-retention",
        files=[
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context6_issue70_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context6-media-provider-posture-retention",
        files=["backend/app/stage7.py", "backend/app/main.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context6-media-provider-posture-retention may not change backend/app/stage7.py.",
        "Phase 1 Closure branch phase-1-closure-39-context6-media-provider-posture-retention may not change backend/app/main.py.",
    ]


def test_issue39_context0_branch_allows_targeted_process_and_skill_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=[
            ".github/workflows/quality.yml",
            ".github/workflows/security.yml",
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "docs/PROJECT_LEARNINGS_TRACKER.md",
            "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
            "docs/SKILLS_AND_CODEX_SETUP.md",
            "docs/SKILL_EXECUTION_PLAN.md",
            "docs/SKILL_LOCK.md",
            "docs/SKILL_TRUST_REVIEW.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context0_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context0-production-durability may not change backend/app/stage4.py."
    ]


def test_issue39_context0_branch_still_rejects_unrelated_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=["docs/unrelated-process-note.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context0-production-durability may not change "
        "docs/unrelated-process-note.md."
    ]


def test_workflow_pull_request_edited_detected_from_multiline_yaml(monkeypatch: Any) -> None:
    workflow_text = """
name: test

on:
  pull_request:
    types:
      - opened
      - edited
"""

    assert phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_detected_from_inline_yaml_list(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    types: [opened, synchronize, edited, reopened]
"""

    assert phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_missing_is_detected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    types:
      - opened
      - synchronize
      - reopened
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_decoy_under_jobs_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  push:
    branches: [main]

jobs:
  test:
    pull_request:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_decoy_under_push_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  push:
    pull_request:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_nested_decoy_under_pull_request_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    branches:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_guardrail_workflow_without_pull_request_edited(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("edited, ", "").replace(", edited", ""),
        },
    )

    assert f"{workflow_path} must rerun guardrails on pull_request.edited" in failures


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_guardrail_workflow_without_token_permissions(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("  issues: read\n", "").replace("  pull-requests: read\n", ""),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/quality-gates.yml",
        ".github/workflows/security.yml",
    ],
)
def test_process_docs_rejects_guardrail_step_without_token_even_when_other_steps_have_token(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: remove_guardrail_step_token(workflow_text),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


def remove_guardrail_step_token(workflow_text: str) -> str:
    lines = workflow_text.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        step_match = re.match(r"^(?P<indent>\s*)-\s+name:\s+.*$", line)
        if not step_match:
            output.append(line)
            index += 1
            continue
        step_indent = len(step_match.group("indent"))
        block = [line]
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and not current.lstrip().startswith("#"):
                current_indent = len(current) - len(current.lstrip(" "))
                if current_indent <= step_indent:
                    break
            block.append(current)
            index += 1
        if any("scripts/guardrails_check.py" in item for item in block):
            block = [item for item in block if "GITHUB_TOKEN:" not in item]
        output.extend(block)
    return "\n".join(output) + "\n"


def test_process_docs_rejects_missing_validation_command(monkeypatch: Any) -> None:
    original_template = phase1.read(".github/pull_request_template.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=[
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        ],
        read_overrides={
            ".github/pull_request_template.md": replace_text(
                original_template,
                "uv run mypy scripts tests",
                "uv run mypy scripts scripts/unit",
            )
        },
    )

    assert ".github/pull_request_template.md Validation evidence section missing required commands:" in failures[0]


def test_process_docs_rejects_optional_branch_protection_validation_when_relevant(monkeypatch: Any) -> None:
    original_template = phase1.read(".github/pull_request_template.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=[
            "docs/ENGINEERING_PROCESS_RCA.md",
            "tests/unit/test_branch_protection_verifier.py",
        ],
        read_overrides={
            ".github/pull_request_template.md": replace_text(
                original_template,
                "# Optional when changed:\n# uv run pytest tests/unit/test_branch_protection_verifier.py",
                "# Optional when changed:\n# ",
            )
        },
    )

    assert (
        "Validation evidence section in .github/pull_request_template.md should include optional command "
        "uv run pytest tests/unit/test_branch_protection_verifier.py when branch-protection verifier evidence is relevant."
        in failures
    )


def test_process_docs_rejects_pending_matrix_template_status(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "| DERIVED-SOURCE-001 | Derived source binding | Source run, retrieved context refs, evaluation status/checksum, citation indexes, and claim-support records stay bound to the derived artifact | A valid export/artifact ID can replay with source evidence from another run | `test_replay_valid_source_bound_artifact` | `test_drop_artifact_with_mismatched_source_run`; break-test proves old behavior failed | `make test`; source-evidence gate | owner | pass |",
                "| DERIVED-SOURCE-001 | Derived source binding | Source run, retrieved context refs, evaluation status/checksum, citation indexes, and claim-support records stay bound to the derived artifact | A valid export/artifact ID can replay with source evidence from another run | `test_replay_valid_source_bound_artifact` | `test_drop_artifact_with_mismatched_source_run`; break-test proves old behavior failed | `make test`; source-evidence gate | owner | pending |",
            )
        },
    )

    assert (
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix row DERIVED-SOURCE-001 must use status pass, not pending."
        in failures
    )


def test_process_docs_rejects_matrix_template_without_source_binding(monkeypatch: Any) -> None:
    original_rca = phase1.read("docs/ENGINEERING_PROCESS_RCA.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/ENGINEERING_PROCESS_RCA.md"],
        read_overrides={
            "docs/ENGINEERING_PROCESS_RCA.md": replace_text(
                original_rca,
                "Source run, retrieved context refs, evaluation ID/status/checksum, citation indexes, and claim-support records agree before translated or subtitle artifacts replay",
                "Source artifact, retrieved context refs, evaluation ID/status/checksum, citation indexes, and claim-support records agree before translated or subtitle artifacts replay",
            )
        },
    )

    assert (
        "docs/ENGINEERING_PROCESS_RCA.md matrix template missing one row with required binding terms: source run, retrieved context, evaluation, citation, claim-support"
        in failures
    )


def test_process_docs_rejects_duplicate_matrix_template_id(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "| DERIVED-SOURCE-001 | Derived source binding |",
                "| DERIVED-ARTIFACT-001 | Derived source binding |",
            )
        },
    )

    assert "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix row duplicates ID: DERIVED-ARTIFACT-001" in failures


def test_process_docs_rejects_agents_missing_merge_closeout_follow_up_marker(monkeypatch: Any) -> None:
    original_agents = phase1.read("AGENTS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-89-implicit-merge-closeout",
        changed=["AGENTS.md"],
        read_overrides={
            "AGENTS.md": replace_text(
                original_agents,
                "new issue, branch, or pull request",
                "follow-up governance work",
            )
        },
    )

    assert "AGENTS.md missing process marker: new issue, branch, or pull request" in failures


def test_process_docs_rejects_playbook_missing_merge_closeout_follow_up_marker(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-89-implicit-merge-closeout",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "required follow-up issue/branch/PR",
                "required follow-up work",
            )
        },
    )

    assert (
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md missing merge-closeout marker: "
        "open the required follow-up issue/branch/pr"
    ) in failures


def test_process_docs_rejects_open_medium_low_phf_register_status(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "| PHF-013 | Medium | Closed by local edits |",
                "| PHF-013 | Medium | Needs triage |",
            )
        },
    )

    assert "PHF-013 must be closed or superseded in the findings register; got needs triage." in failures


def test_process_docs_rejects_placeholder_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_nontrivial_pull_request_rejects_missing_validation_evidence_commands` fails actual PR bodies without command evidence; `test_process_docs_rejects_missing_validation_command` and `test_process_docs_rejects_optional_branch_protection_validation_when_relevant` enforce template/gate command evidence.",
                "TBD",
            )
        },
    )

    assert "PHF-011 Medium/Low matrix has placeholder automated test / guardrail." in failures


def test_process_docs_rejects_bare_scripts_directory_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_workflow_pull_request_edited_detected_from_inline_yaml_list`, `test_workflow_pull_request_edited_detected_from_multiline_yaml`, and `test_workflow_pull_request_edited_missing_is_detected` verify parsed workflow events; table-header checks now fail on missing required section columns.",
                "`scripts/`",
            )
        },
    )

    assert "PHF-012 Medium/Low matrix must map to an automated test/guardrail or human-only surface." in failures


def test_process_docs_rejects_nonexistent_test_name_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_missing_validation_command`",
                "`test_this_does_not_exist_anywhere`",
            )
        },
    )

    assert "PHF-011 Medium/Low matrix cites unknown test evidence: test_this_does_not_exist_anywhere" in failures


def test_process_docs_rejects_nonexistent_test_name_on_human_only_phf_row(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_pending_matrix_template_status`",
                "`test_this_human_only_row_fake_does_not_exist`",
            )
        },
    )

    assert (
        "PHF-008 Medium/Low matrix cites unknown test evidence: "
        "test_this_human_only_row_fake_does_not_exist"
    ) in failures


def test_process_docs_rejects_nonexistent_script_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "table-header checks now fail on missing required section columns.",
                "`scripts/quality/does_not_exist.py`",
            )
        },
    )

    assert "PHF-012 Medium/Low matrix cites missing script evidence: scripts/quality/does_not_exist.py" in failures


def test_process_docs_rejects_nonexistent_script_on_human_only_phf_row(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "guardrail tests reject partial matrix-ID coverage",
                "`scripts/quality/does_not_exist_for_human_only.py` rejects partial matrix-ID coverage",
            )
        },
    )

    assert (
        "PHF-008 Medium/Low matrix cites missing script evidence: "
        "scripts/quality/does_not_exist_for_human_only.py"
    ) in failures


def test_process_docs_rejects_nonexistent_pytest_node_id_target(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_matrix_template_without_source_binding`",
                "uv run pytest tests/unit/does_not_exist.py::test_missing",
            )
        },
    )

    assert "PHF-007 Medium/Low matrix cites missing pytest target: tests/unit/does_not_exist.py" in failures


def test_phf_automated_evidence_rejects_non_path_pytest_target() -> None:
    failures = phase1.phf_automated_evidence_failures("PHF-X", "uv run pytest not_a_real_target")

    assert "PHF-X Medium/Low matrix cites unsupported pytest target: not_a_real_target" in failures


def test_phf_automated_evidence_rejects_pytest_node_id_test_from_wrong_file() -> None:
    failures = phase1.phf_automated_evidence_failures(
        "PHF-X",
        "uv run pytest tests/unit/test_guardrails_check.py::"
        "test_workflow_pull_request_edited_decoy_under_jobs_is_rejected",
    )

    assert (
        "PHF-X Medium/Low matrix cites pytest node id with test outside target: "
        "tests/unit/test_guardrails_check.py::test_workflow_pull_request_edited_decoy_under_jobs_is_rejected"
    ) in failures


def test_phf_automated_evidence_accepts_dot_prefixed_pytest_target() -> None:
    failures = phase1.phf_automated_evidence_failures(
        "PHF-X",
        "uv run pytest "
        "./tests/unit/test_phase1_closure_docs.py::test_phf_automated_evidence_accepts_dot_prefixed_pytest_target",
    )

    assert failures == []
