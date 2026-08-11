"""Behavioral contract for trusted PR-body reconciliation (Issue #415)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality import pr_body_consistency as subject


REPOSITORY = "owner/repository"
BASE = "a" * 40
HEAD = "b" * 40


def live(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "number": 415,
        "state": "open",
        "draft": False,
        "base": {"ref": "main", "sha": BASE},
        "head": {"ref": "governance-415-pr-body-live-state", "sha": HEAD, "repo": {"full_name": REPOSITORY}},
        "changed_files": 13,
        "additions": 100,
        "deletions": 10,
        "body": subject.managed_block(subject.LiveState.from_pull(REPOSITORY, value)),
    }
    value.update(changes)
    return value


def human(body: str) -> str:
    return "## Product and reviewer context\nStable human bytes.\n\n## Reviewer overview\nStable reviewer bytes.\n\n" + body


def test_render_is_deterministic_and_contains_only_live_facts() -> None:
    state = subject.LiveState.from_pull(REPOSITORY, live())
    assert subject.managed_block(state) == subject.managed_block(state)
    assert "schema_version: 1" in subject.managed_block(state)
    assert "ci" not in subject.managed_block(state).lower()


@pytest.mark.parametrize("body", ["", "<!-- narratwin-live-state:start -->", "<!-- narratwin-live-state:end -->"])
def test_missing_or_unpaired_markers_fail_closed(body: str) -> None:
    assert "managed-block" in " ".join(subject.validate_body(human(body), subject.LiveState.from_pull(REPOSITORY, live()))).lower()


@pytest.mark.parametrize("body", [
    "<!-- narratwin-live-state:start -->x<!-- narratwin-live-state:start --><!-- narratwin-live-state:end -->",
    "<!-- narratwin-live-state:end --><!-- narratwin-live-state:start -->",
])
def test_duplicate_or_reversed_markers_fail_closed(body: str) -> None:
    assert subject.validate_body(human(body), subject.LiveState.from_pull(REPOSITORY, live()))


@pytest.mark.parametrize(("field", "value"), [("head_sha", "c" * 40), ("base_sha", "c" * 40), ("changed_files", "14"), ("additions", "101"), ("deletions", "11")])
def test_stale_live_metadata_fails_closed(field: str, value: str) -> None:
    state = subject.LiveState.from_pull(REPOSITORY, live())
    stale = subject.managed_block(state).replace(f"{field}: {getattr(state, field)}", f"{field}: {value}")
    assert subject.validate_body(human(stale), state)


@pytest.mark.parametrize("bad", [r"literal\\ntext", "TODO: replace", "/Users/alice/private", "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"])
def test_unsafe_or_template_content_fails_closed(bad: str) -> None:
    body = human(subject.managed_block(subject.LiveState.from_pull(REPOSITORY, live()))) + "\n" + bad
    assert subject.validate_body(body, subject.LiveState.from_pull(REPOSITORY, live()))


def test_historical_sha_is_allowed_when_explicitly_historical() -> None:
    body = human(subject.managed_block(subject.LiveState.from_pull(REPOSITORY, live()))) + "\nHistorical evidence: `" + "c" * 40 + "`."
    assert subject.validate_body(body, subject.LiveState.from_pull(REPOSITORY, live())) == []


def test_reconcile_preserves_every_human_byte_and_is_idempotent() -> None:
    state = subject.LiveState.from_pull(REPOSITORY, live())
    before = human("<!-- narratwin-live-state:start -->\nstale\n<!-- narratwin-live-state:end -->")
    result = subject.reconcile(before, state)
    assert result.changed
    assert result.body.startswith("## Product and reviewer context\nStable human bytes.")
    assert subject.reconcile(result.body, state).changed is False


class FakeApi:
    def __init__(self, first: dict[str, object], second: dict[str, object] | None = None) -> None:
        self.first, self.second, self.writes = first, second or first, []
        self.reads = 0
    def pull(self, number: int) -> dict[str, object]:
        self.reads += 1
        return self.first if self.reads == 1 else self.second
    def update_body(self, number: int, body: str) -> None:
        self.writes.append((number, body))


def test_apply_refuses_head_race_and_makes_zero_writes() -> None:
    initial, changed = live(), live(head={"ref": "branch", "sha": "c" * 40, "repo": {"full_name": REPOSITORY}})
    api = FakeApi(initial, changed)
    with pytest.raises(subject.HeadChanged):
        subject.apply(api, REPOSITORY, 415)
    assert api.writes == []


def test_apply_noop_makes_zero_writes() -> None:
    api = FakeApi(live())
    assert subject.apply(api, REPOSITORY, 415).changed is False
    assert api.writes == []


def test_workflow_contract_is_trusted_base_and_least_privilege() -> None:
    text = Path(".github/workflows/pr-body-consistency.yml").read_text(encoding="utf-8")
    assert "pull_request_target" in text
    assert "contents: read" in text and "pull-requests: write" in text
    assert "actions/checkout" not in text
    assert "github.event.pull_request.head" not in text
    assert "pr-body-consistency" in text


def test_fixture_has_no_duplicate_json_keys() -> None:
    raw = Path("tests/fixtures/pr_body_consistency/live_pr.json").read_text(encoding="utf-8")
    with pytest.raises(subject.DuplicateJsonKey):
        subject.decode_json('{"x": 1, "x": 2}')
    assert subject.decode_json(raw)["number"] == 415
