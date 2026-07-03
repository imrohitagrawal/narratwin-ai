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

    assert failures == []


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
