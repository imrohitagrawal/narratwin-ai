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
