"""Behavioral contract for trusted PR-body reconciliation (Issue #415)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality import pr_body_consistency as subject
from scripts.quality import pr_body_consistency_cli as cli


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
    }
    value.update(changes)
    if "body" not in changes:
        value["body"] = subject.managed_block(subject.LiveState.from_pull(REPOSITORY, value))
    return value


def human(body: str) -> str:
    return "## Product and reviewer context\nStable human bytes.\n\n## Reviewer overview\nStable reviewer bytes.\n\n" + body


def test_render_is_deterministic_and_contains_only_live_facts() -> None:
    state = subject.LiveState.from_pull(REPOSITORY, live())
    assert subject.managed_block(state) == subject.managed_block(state)
    assert "schema_version: 1" in subject.managed_block(state)
    assert "ci_status" not in subject.managed_block(state).lower()


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


@pytest.mark.parametrize("bad", ["literal\\ntext", "TODO: replace", "/Users/alice/private", "Authorization: Bearer " + "abcdefghijkl" + "mnopqrstuvwxyz"])
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
        self.first, self.second = first, second or first
        self.writes: list[tuple[int, str]] = []
        self.reads = 0
    def pull(self, number: int) -> dict[str, object]:
        self.reads += 1
        return self.first if self.reads == 1 else self.second
    def update_body(self, number: int, body: str) -> None:
        self.writes.append((number, body))
        self.second["body"] = body


def test_apply_refuses_head_race_and_makes_zero_writes() -> None:
    initial, changed = live(), live(head={"ref": "branch", "sha": "c" * 40, "repo": {"full_name": REPOSITORY}})
    api = FakeApi(initial, changed)
    with pytest.raises(subject.HeadChanged):
        subject.apply(api, REPOSITORY, 415)
    assert api.writes == []


def test_apply_refuses_same_head_body_race_and_preserves_human_edit() -> None:
    initial = live(body=human("<!-- narratwin-live-state:start -->\nstale\n<!-- narratwin-live-state:end -->"))
    concurrent = live(body=str(initial["body"]).replace("Stable human bytes.", "Concurrent human edit."))
    api = FakeApi(initial, concurrent)
    with pytest.raises(subject.HeadChanged, match="body changed"):
        subject.apply(api, REPOSITORY, 415)
    assert api.writes == []
    assert concurrent["body"] == api.second["body"]


def test_apply_noop_makes_zero_writes() -> None:
    api = FakeApi(live())
    assert subject.apply(api, REPOSITORY, 415).changed is False
    assert api.writes == []


def test_apply_verifies_the_stored_body_after_a_single_write() -> None:
    stale = live(body=human("<!-- narratwin-live-state:start -->\nstale\n<!-- narratwin-live-state:end -->"))
    api = FakeApi(stale)
    assert subject.apply(api, REPOSITORY, 415).changed is True
    assert len(api.writes) == 1


def test_workflow_contract_is_trusted_base_and_least_privilege() -> None:
    text = Path(".github/workflows/pr-body-consistency.yml").read_text(encoding="utf-8")
    assert "pull_request_target" in text
    assert "contents: read" in text and "pull-requests: write" in text
    check_permissions = text.split("  check:\n", maxsplit=1)[1].split("    runs-on:", maxsplit=1)[0]
    assert "pull-requests: read" in check_permissions
    assert "ref: ${{ github.sha }}" in text
    assert "persist-credentials: false" in text
    assert "ref: ${{ github.event.pull_request.base.sha }}" not in text
    assert "ref: ${{ github.event.pull_request.head.sha }}" not in text
    assert "pr-body-consistency" in text
    assert "needs: reconcile" in text
    assert "uv run python" in Path("Makefile").read_text(encoding="utf-8")
    assert text.count("python3 -m scripts.quality.pr_body_consistency_cli") == 2
    assert "python3 scripts/quality/pr_body_consistency_cli.py" not in text


def test_workflow_records_bootstrap_boundary_and_fork_safe_skip() -> None:
    text = Path(".github/workflows/pr-body-consistency.yml").read_text(encoding="utf-8")
    assert "bootstrap PR" in text
    assert "head.repo.full_name == github.repository" in text
    assert "always()" in text


def test_workflow_rejects_untrusted_checkout_mutations() -> None:
    text = Path(".github/workflows/pr-body-consistency.yml").read_text(encoding="utf-8")
    for untrusted in ("github.event.pull_request.head.sha", "github.event.pull_request.base.sha"):
        assert untrusted not in text
    assert text.count("ref: ${{ github.sha }}") == 2


def test_fixture_has_no_duplicate_json_keys() -> None:
    raw = Path("tests/fixtures/pr_body_consistency/live_pr.json").read_text(encoding="utf-8")
    with pytest.raises(subject.DuplicateJsonKey):
        subject.decode_json('{"x": 1, "x": 2}')
    assert subject.decode_json(raw)["number"] == 415


def test_github_transport_retries_boundedly_without_leaking_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    class Response:
        def __enter__(self) -> "Response":
            return self
        def __exit__(self, *_: object) -> None:
            return None
        def read(self, _: int) -> bytes:
            return b'{"number":415}'

    def transport(*_: object, **__: object) -> Response:
        calls.append(None)
        if len(calls) == 1:
            raise TimeoutError("network timed out")
        return Response()

    monkeypatch.setattr(cli, "urlopen", transport)
    client = cli.GitHubApi(REPOSITORY, "private-auth-value", retries=2, sleeper=lambda _: None)
    assert client.pull(415)["number"] == 415
    assert len(calls) == 2


def test_github_transport_failure_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "urlopen", lambda *_a, **_kw: (_ for _ in ()).throw(TimeoutError("private-auth-value")))
    client = cli.GitHubApi(REPOSITORY, "private-auth-value", retries=1, sleeper=lambda _: None)
    with pytest.raises(RuntimeError, match="TimeoutError") as raised:
        client.pull(415)
    assert "private-auth-value" not in str(raised.value)
