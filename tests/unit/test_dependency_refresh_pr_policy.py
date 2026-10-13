"""RED: maintenance must not demand unrelated stage closure or allow automatic closure."""

import json
from pathlib import Path

import pytest

from scripts import guardrails_check as policy


def test_refresh_pr_reference_only_and_canonical_near_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    event = tmp_path / "event.json"
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setattr(policy, "run_git", lambda args: "")

    def failures(branch: str, body: str) -> list[str]:
        event.write_text(
            json.dumps(
                {
                    "pull_request": {
                        "title": "Dependency container maintenance",
                        "body": body,
                        "head": {"ref": branch},
                        "base": {"ref": "main"},
                    }
                }
            )
        )
        policy.failures.clear()
        policy.check_issue_linked_pull_request()
        return list(policy.failures)

    branch = "stage8-561-dependency-container-refresh"
    assert failures(branch, "Refs #561") == []
    for number in ("561", "13", "999"):
        assert "Pull request title/body/commit messages must use reference-only issue wording." in (
            failures(branch, "Refs #561\nCloses #" + number)
        )
    for near in (
        branch + "-extra",
        "stage8-abc-dependency-container-refresh",
        "stage8-release-hardening",
    ):
        assert any("canonical Stage 8 issue" in item for item in failures(near, "Refs #561"))
    assert failures("stage8-release-hardening", "Closes #13") == []
