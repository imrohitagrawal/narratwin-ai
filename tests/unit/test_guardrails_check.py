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


def run_issue_link_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    title: str,
    body: str,
    head_ref: str = "phase-1-closure-39-durability-monitoring",
    commit_messages: str = "",
    changed_files: list[str] | None = None,
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
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

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
    human_surface_rows = human_rows or (
        "| N/A | No human-only surface for this PR | reviewer | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | next process PR |\n"
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
        "| Invariant/failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | pre-code timestamp: 2026-07-09T10:00 | reviewer | pass |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | reviewer signoff: reviewer 2026-07-09 | reviewer | pass |\n"
        "| Human-only surfaces, if any | `docs/ENGINEERING_PROCESS_RCA.md` | commit order: 1234567 before 89abcde | reviewer | pass |\n"
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
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


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
        "pre-code timestamp: 2026-07-09T10:00",
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


def test_nontrivial_pull_request_rejects_placeholder_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "pre-code timestamp: 2026-07-09T10:00",
        "checked before implementation",
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
