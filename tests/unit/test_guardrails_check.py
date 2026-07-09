import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_guardrails_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "guardrails_check.py"
    spec = importlib.util.spec_from_file_location("guardrails_check_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guardrails: Any = load_guardrails_module()
ISSUE_39_REFERENCE_ONLY_FAILURE = "Issue #39 pull requests must use reference-only wording and must not auto-close #39."
PREFLIGHT_FAILURE = "Non-trivial pull requests must include completed preflight evidence rows."


def write_issue39_closure_plan(
    root: Path,
    *,
    child_issue: str = "#70",
    malformed_id: str | None = None,
    omitted_ids: set[str] | None = None,
    include_records: bool = True,
) -> None:
    omitted = omitted_ids or set()
    plan_path = root / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_rows = []
    record_rows = []
    for matrix_id in sorted(guardrails.REQUIRED_ISSUE_39_CLOSURE_MATRIX_IDS - omitted):
        if matrix_id == malformed_id:
            matrix_rows.append(
                f"| `{matrix_id}` | Requirement | Evidence target | Owner | Minimum evidence contract | Closed | Open |"
            )
        else:
            matrix_rows.append(
                f"| `{matrix_id}` | Requirement | Evidence target | Owner | Minimum evidence contract | Closed |"
            )
        evidence_path = root / f"docs/reviews/{matrix_id}-evidence.md"
        evidence_path.write_text(f"{matrix_id} closure evidence\n", encoding="utf-8")
        record_rows.append(
            f"| `{matrix_id}` | {child_issue} / PR #71 | `docs/reviews/{matrix_id}-evidence.md` | {matrix_id} human-only evidence passed | {matrix_id.lower()}-owner | {matrix_id.lower()}-reviewer | {matrix_id} residual risk accepted | merge commit abc1234 | {matrix_id} evidence satisfies the closure row |"
        )
    records = "\n".join(record_rows) if include_records else ""
    plan_path.write_text(
        "\n".join(
            [
                "# Issue #39 Production Closure Plan (Context 0)",
                "",
                "## Master Evidence Matrix",
                "",
                "| ID | Requirement | Evidence target | Owner | Minimum evidence contract | Status |",
                "|---|---|---|---|---|---|",
                *matrix_rows,
                "",
                "## Row Closure Records",
                "",
                "| Matrix ID | Child issue / PR | Artifact reference | Validation or human evidence | Owner | Reviewer | Residual-risk decision | Timestamp / merge commit | Satisfies row because |",
                "|---|---|---|---|---|---|---|---|---|",
                records,
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_issue_link_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    title: str,
    body: str,
    head_ref: str = "phase-1-closure-39-durability-monitoring",
    commit_messages: str = "",
    changed_files: list[str] | None = None,
    event_name: str = "pull_request",
    force_pull_request_guards: bool = False,
) -> list[str]:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "pull_request": {
                    "title": title,
                    "body": body,
                    "head": {"ref": head_ref},
                    "base": {"ref": "main"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    if force_pull_request_guards:
        monkeypatch.setenv(guardrails.FORCE_PULL_REQUEST_GUARDRAILS_ENV, "1")

    def fake_run_git(args: list[str]) -> str:
        if args and args[0] == "log":
            return commit_messages
        if args and args[0] == "diff":
            return "\n".join(changed_files or [])
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)
    guardrails.failures.clear()
    guardrails.check_issue_linked_pull_request()
    return list(guardrails.failures)


def completed_preflight_body(preflight_rows: str | None = None, *, human_rows: str | None = None) -> str:
    rows = preflight_rows or (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix / invariant matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests / old-behavior proof | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 INV-2 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 INV-2 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    human_surface_rows = (
        human_rows
        if human_rows is not None
        else (
        "| Final squash message | CI cannot inspect the final merge dialog text before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | reference-only final message with no issue-closing keyword accepted for PR only | before merge |\n"
        )
    )
    return (
        "Refs #44\n\n"
        "## Preflight evidence\n\n"
        "| Evidence | Artifact reference | Reference type | Matrix IDs | Command / CI / Source | Reviewer | Evidence type | Completion status | Residual risk decision |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        f"{rows}\n"
        "## Human-only review surfaces\n\n"
        "| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |\n"
        "|---|---|---|---|---|---|\n"
        f"{human_surface_rows}\n"
        "## Pre-implementation evidence\n\n"
        "| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |\n"
        "|---|---|---|---|---|\n"
        "| Invariant/failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1 | reviewer | pass |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | draft pr: https://github.com/imrohitagrawal/narratwin-ai/pull/60 | reviewer | pass |\n"
        "| Human-only surfaces, if any | `docs/ENGINEERING_PROCESS_RCA.md` | issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-2 | reviewer | pass |\n"
        "\n## Validation evidence\n\n"
        "```text\n"
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed\n"
        "uv run pytest tests/unit/test_phase1_closure_docs.py -> 14 passed\n"
        "python3 scripts/guardrails_check.py -> passed\n"
        "make quality -> passed\n"
        "uv run ruff check scripts tests -> passed\n"
        "uv run mypy scripts tests -> passed\n"
        "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed\n"
        "```\n"
    )


def test_phase1_issue39_pull_request_allows_reference_only_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39",
    )

    assert failures == []


def test_phase1_issue39_pull_request_rejects_closing_keyword_in_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve #39 local durability and ops status evidence",
        body="Refs #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_colon_closing_keyword_in_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve: #39 local durability and ops status evidence",
        body="Refs #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_in_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nFixes #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_allows_closing_keyword_only_after_matrix_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE not in failures
    assert "Pull request title/body/commit messages must use reference-only issue wording." not in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_when_matrix_id_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, omitted_ids={"DUR-STAGE4-001"})
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_without_closure_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, include_records=False)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_with_malformed_matrix_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, malformed_id="DUR-STAGE4-001")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_with_parent_issue_as_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, child_issue="#39")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_colon_closing_keyword_in_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nFixes: #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_cross_repo_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nCloses imrohitagrawal/narratwin-ai#39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_url_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nResolves https://github.com/imrohitagrawal/narratwin-ai/issues/39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_commit_message_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39",
        commit_messages="fix: add local durability\n\nFixed #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_issue39_closing_keyword_is_rejected_on_any_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve #39 local durability and ops status evidence",
        body="Refs #39",
        head_ref="fix/local-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_issue39_commit_message_closing_keyword_is_rejected_on_any_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Local durability and ops status evidence",
        body="Refs #39",
        head_ref="fix/local-durability",
        commit_messages="fix: local durability\n\nResolves #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_general_pull_request_allows_reference_only_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert failures == []


def test_general_pull_request_rejects_closing_keyword_as_only_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Fixes #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert (
        "Pull request body must link an issue using reference-only wording such as Refs #<issue>."
    ) in failures


def test_general_pull_request_rejects_closing_keyword_even_with_reference_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Refs #44\nFixes #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_general_pull_request_rejects_title_closing_keyword_even_with_reference_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Fixes #44",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_canonical_stage_pull_request_rejects_extra_closing_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Stage 2 architecture closure",
        body="Refs #44\nCloses #2\nFixes #44",
        head_ref="stage2-architecture-security-ai-safety",
    )

    assert "Pull request title/body/commit messages must not close non-canonical issues." in failures


@pytest.mark.parametrize(
    ("head_ref", "canonical_issue"),
    [
        ("stage2-architecture-security-ai-safety", "2"),
        ("stage3-governance-hardening", "5"),
        ("stage4-multiple-state-contract", "4"),
        ("stage5-local-evaluation-foundation", "10"),
        ("stage6-multilingual-sourcing", "11"),
        ("stage7-avatar-export", "12"),
        ("stage8-release-hardening", "13"),
    ],
)
def test_canonical_stage_pull_request_accepts_only_canonical_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    head_ref: str,
    canonical_issue: str,
) -> None:
    accepted = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title=f"Stage closure work for {head_ref}",
        body=f"Closes #{canonical_issue}",
        head_ref=head_ref,
    )
    assert accepted == []

    rejected = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title=f"Stage closure work for {head_ref}",
        body=f"Closes #{int(canonical_issue) + 1}",
        head_ref=head_ref,
    )
    assert "Pull request title/body/commit messages must not close non-canonical issues." in rejected


def test_force_pull_request_guardrails_enforced_in_non_pull_request_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Fixes #44",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
        event_name="push",
        force_pull_request_guards=True,
        changed_files=["backend/app/main.py"],
        commit_messages="",
    )
    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_push_context_without_pull_request_payload_when_force_enabled_fails_fast(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.setenv(guardrails.FORCE_PULL_REQUEST_GUARDRAILS_ENV, "1")

    def fake_run_git(args: list[str]) -> str:
        if args and args[0] == "log":
            return ""
        if args and args[0] == "diff":
            return ""
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)
    guardrails.failures.clear()
    guardrails.check_issue_linked_pull_request()
    assert "Pull request event payload is unavailable; cannot verify issue linkage." in guardrails.failures


def test_general_pull_request_requires_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="No linked issue.",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert (
        "Pull request body must link an issue using reference-only wording such as Refs #<issue>."
    ) in failures


def test_nontrivial_pull_request_requires_completed_preflight_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec |  |  |  |  |  |  |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_process_critical_docs_are_nontrivial_and_require_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden process review evidence",
        body="Refs #60",
        head_ref="phase-1-closure-process-60-phf-002-medium-low-hardening",
        changed_files=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_completed_preflight_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_missing_required_preflight_categories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/spec.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/matrix.md` | FM-1 | red test | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_example.py` | T-1 | `uv run pytest` | reviewer | pass | none |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_nontrivial_pull_request_accepts_pr_template_preflight_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix / invariant matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests / old-behavior proof | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_partial_matrix_id_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_matrix_id_range_shorthand(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 through INV-3 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 INV-3 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 INV-3 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_matrix_ids_covered_across_evidence_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs for SRC-1 | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 SRC-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-2 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_invariant_id_covered_only_by_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 INV-2 | official docs for source and invariant | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


@pytest.mark.parametrize("status", ["tracked", "accepted"])
def test_nontrivial_pull_request_rejects_non_completed_preflight_statuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            f"| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | {status} | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_directory_preflight_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preflight_url_with_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | https://example.com/todo | URL | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_unknown_reference_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | definitely-not-a-reference-type | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_file_line_artifact_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md:334` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md#invariant-to-test-matrix-template` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_mismatched_reference_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | source-URL | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_human_only_evidence_without_surface_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    body = completed_preflight_body(rows, human_rows="")
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_valid_human_only_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            rows,
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | reference-only final message with no issue-closing keyword accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_na_human_only_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            human_rows=(
                "| N/A | No human-only surface for this PR | reviewer | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | next process PR |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_final_merge_surface_without_reference_only_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_human_only_evidence_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            rows,
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | https://example.com/todo | accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_missing_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().split("## Pre-implementation evidence", maxsplit=1)[0]
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preimplementation_comment_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "issue comment: https://example.com/todo",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_bare_issue_preimplementation_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "pre-code timestamp: 2026-07-09T10:00",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def body_with_commit_order_preimplementation_rows(commit_order_marker: str) -> str:
    return (
        completed_preflight_body()
        .replace(
            "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
            commit_order_marker,
        )
        .replace(
            "draft pr: https://github.com/imrohitagrawal/narratwin-ai/pull/60",
            commit_order_marker,
        )
        .replace(
            "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-2",
            commit_order_marker,
        )
    )


def test_nontrivial_pull_request_accepts_verified_commit_order_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earlier = "1111111"
    later = "2222222"

    def fake_git_command_succeeds(args: list[str]) -> bool:
        if args == ["cat-file", "-e", f"{earlier}^{{commit}}"]:
            return True
        if args == ["cat-file", "-e", f"{later}^{{commit}}"]:
            return True
        return args == ["merge-base", "--is-ancestor", earlier, later]

    monkeypatch.setattr(guardrails, "git_command_succeeds", fake_git_command_succeeds)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body_with_commit_order_preimplementation_rows(f"commit order: {earlier} before {later}"),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE not in failures


def test_nontrivial_pull_request_rejects_reversed_commit_order_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earlier = "1111111"
    later = "2222222"

    def fake_git_command_succeeds(args: list[str]) -> bool:
        if args[0] == "cat-file":
            return True
        return args == ["merge-base", "--is-ancestor", earlier, later]

    monkeypatch.setattr(guardrails, "git_command_succeeds", fake_git_command_succeeds)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body_with_commit_order_preimplementation_rows(f"commit order: {later} before {earlier}"),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_missing_validation_evidence_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().split("## Validation evidence", maxsplit=1)[0]
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_unrun_validation_evidence_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "not run: uv run pytest tests/unit/test_guardrails_check.py",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_hyphenated_not_run_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "not-run: uv run pytest tests/unit/test_guardrails_check.py -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_substring_validation_pass_terms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "make quality -> passed",
        "make quality -> unsuccessful",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_unrelated_validation_example_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "Example only: uv run pytest tests/unit/test_guardrails_check.py -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_inline_validation_example_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "uv run pytest tests/unit/test_guardrails_check.py -> passed (Example only)",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_zero_pass_validation_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    "invalid_line",
    [
        "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed; rerun -> passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 tests collected, 0 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 00 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
    ],
)
def test_nontrivial_pull_request_rejects_same_line_zero_pass_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        invalid_line,
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_zero_pass_before_later_valid_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed\n"
            "uv run pytest tests/unit/test_guardrails_check.py -> 75 passed"
        ),
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_later_zero_pass_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 75 passed\n"
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed"
        ),
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    ("valid_line", "invalid_line"),
    [
        ("make quality -> passed", "make quality-check -> passed"),
        (
            "python3 scripts/guardrails_check.py -> passed",
            "python3 scripts/guardrails_check.py.bak -> passed",
        ),
    ],
)
def test_nontrivial_pull_request_rejects_validation_command_suffix_false_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_line: str,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(valid_line, invalid_line)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_requires_full_forced_pr_validation_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
        "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    "invalid_line",
    [
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "python3 scripts/guardrails_check.py NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 -> passed"
        ),
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH= "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
    ],
)
def test_nontrivial_pull_request_rejects_malformed_forced_pr_validation_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
        invalid_line,
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_placeholder_validation_event_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "GITHUB_EVENT_PATH=/tmp/pr-event.json",
        "GITHUB_EVENT_PATH=/path/to/pr-event.json",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_requires_final_merge_residual_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Final squash message | CI cannot inspect final merge text; reviewer checks reference-only no issue-closing wording | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | before merge |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(human_rows=rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_preflight_without_invariant_test_id_overlap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | INV-1 | invariant-to-test matrix | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | T-1 | negative test; old behavior fails | reviewer | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | INV-1 | invariant test gate | reviewer | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_nontrivial_pull_request_rejects_preflight_without_old_behavior_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | INV-1 | invariant-to-test matrix | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | INV-1 | `uv run pytest` | reviewer | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | INV-1 | invariant test gate | reviewer | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_nontrivial_pull_request_rejects_placeholder_preflight_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | https:// | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | https:// | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | https:// | FM-1 | red test | reviewer | pass | tracked |\n"
            "| Tests | https:// | T-1 | `uv run pytest` | reviewer | pass | none |\n"
            "| Docs/gates | https:// | DOC-1 | marker gate | reviewer | pass | tracked |\n"
            "| Adversarial review | https:// | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


@pytest.mark.parametrize(
    "changed_file",
    [
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "tests/unit/test_guardrails_check.py",
        ".github/CODEOWNERS",
        "scripts/ci/verify_branch_protection.py",
    ],
)
def test_new_governance_artifacts_require_status_updates(changed_file: str) -> None:
    guardrails.failures.clear()
    guardrails.check_status_tracking_rules([changed_file])

    assert "Repository-tracked stage/governance changes require docs/STATUS.md to be updated." in guardrails.failures


def test_new_governance_artifacts_pass_when_status_is_updated() -> None:
    guardrails.failures.clear()
    guardrails.check_status_tracking_rules(
        [
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
            "docs/STATUS.md",
        ]
    )

    assert guardrails.failures == []
