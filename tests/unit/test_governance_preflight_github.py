from __future__ import annotations
import copy
import email.message
import io
import inspect
import json
import os
import random
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit
import pytest
import scripts.governance_preflight_github as github
from scripts.governance_preflight_github import main, verify_governance_preflight_github
from scripts.governance_preflight_v1 import GovernanceFinding
REPOSITORY = "imrohitagrawal/narratwin-ai"
API = "https://api.github.com"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
CONTEXTS = ("policy-gates", "quality / secrets")
APP_ID = 15368
SEEDS = tuple(range(33001, 33011))
class Clock:
    def __init__(self) -> None:
        self.now = 0.0
    def __call__(self) -> float:
        return self.now
    def sleep(self, seconds: float) -> None:
        self.now += seconds
class Transport:
    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture
        self.calls: list[tuple[str, Mapping[str, str], float]] = []
    def __call__(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, Mapping[str, str], bytes]:
        self.calls.append((url, headers, timeout))
        path = urlsplit(url).path
        key = "reviews" if path.endswith("/reviews") else "checks" if path.endswith("/check-runs") else "pr"
        queue = self.fixture.setdefault("responses", {}).setdefault(key, [])
        value = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(value, BaseException):
            raise value
        status, response_headers, payload = value
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return status, response_headers, raw
def _identity(login: str, user_id: int) -> dict[str, Any]:
    return {"login": login, "id": user_id}
def _event(event_name: str = "pull_request", action: str = "opened") -> dict[str, Any]:
    pull = {
        "number": 178,
        "user": _identity("author", 1),
        "draft": False,
        "head": {"sha": HEAD, "repo": {"full_name": REPOSITORY}},
        "base": {"ref": "main", "repo": {"full_name": REPOSITORY}},
    }
    event: dict[str, Any] = {
        "action": action,
        "number": 178,
        "repository": {"full_name": REPOSITORY},
        "pull_request": pull,
        "sender": _identity("author", 1),
    }
    if event_name == "pull_request_review":
        event["sender"] = _identity("reviewer", 2)
        event["review"] = {
            "id": 20,
            "user": _identity("reviewer", 2),
            "state": "approved" if action == "submitted" else "dismissed",
            "commit_id": HEAD,
            "author_association": "OWNER",
        }
    return event
def _review(state: str = "APPROVED", commit: str = HEAD) -> dict[str, Any]:
    return {
        "id": 20,
        "user": _identity("reviewer", 2),
        "state": state,
        "commit_id": commit,
        "author_association": "OWNER",
        "submitted_at": "2026-07-16T00:00:00Z",
    }
def _check(name: str, **overrides: Any) -> dict[str, Any]:
    value = {
        "id": 100 + CONTEXTS.index(name),
        "name": name,
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "app": {"id": APP_ID},
        "details_url": "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/999/job/1",
        "started_at": "2026-07-16T00:00:00Z",
        "completed_at": "2026-07-16T00:00:01Z",
    }
    value.update(overrides)
    return value
def _fixture(lifecycle: str = "implementing") -> dict[str, Any]:
    event_name, action = ("pull_request_review", "submitted") if lifecycle == "ready" else ("pull_request", "opened")
    event = _event(event_name, action)
    live = copy.deepcopy(event["pull_request"])
    live.update({"state": "open", "merged": False})
    reviews: list[dict[str, Any]] = []
    if lifecycle == "ready":
        reviews = [_review()]
    elif lifecycle == "correcting":
        reviews = [_review(commit=OTHER_HEAD)]
    elif lifecycle == "draft":
        live["draft"] = True
    elif lifecycle == "closed":
        live["state"] = "closed"
    checks = [_check(name) for name in CONTEXTS]
    return {
        "event_name": event_name,
        "event": event,
        "responses": {
            "pr": [(200, {}, live)],
            "reviews": [(200, {}, reviews)],
            "checks": [(200, {}, {"total_count": len(checks), "check_runs": checks})],
        },
    }
def _codes(fixture: dict[str, Any], *, auth_value: str | None | BaseException = "sentinel-token",
           clock: Clock | None = None, api_url: str = API) -> list[str]:
    boundary = Transport(fixture)
    fake_clock = clock or Clock()
    def provide() -> str | None:
        if isinstance(auth_value, BaseException):
            raise auth_value
        return auth_value
    findings = verify_governance_preflight_github(
        fixture["event"], event_name=fixture["event_name"], repository=REPOSITORY,
        api_url=api_url, required_contexts=CONTEXTS, expected_app_id=APP_ID, run_id=999,
        token_provider=provide, transport=boundary, clock=fake_clock, sleeper=fake_clock.sleep,
    )
    fixture["calls"] = boundary.calls
    return [finding.code for finding in findings]
def _single(fixture: dict[str, Any], mutation: Any) -> dict[str, Any]:
    baseline = copy.deepcopy(fixture)
    assert _codes(baseline) == []
    changed = copy.deepcopy(fixture)
    mutation(changed)
    return changed
def _self_reviewer(fixture: dict[str, Any]) -> None:
    for value in (fixture["event"]["review"]["user"], fixture["event"]["sender"], fixture["responses"]["reviews"][0][2][0]["user"]):
        value.update(_identity("author", 1))
@pytest.mark.parametrize("action", ("opened", "synchronize", "reopened", "edited", "ready_for_review", "converted_to_draft"))
def test_supported_pull_request_events_are_non_circular(action: str) -> None:
    fixture = _fixture("draft" if action == "converted_to_draft" else "implementing")
    fixture["event"] = _event("pull_request", action)
    assert _codes(fixture) == []
@pytest.mark.parametrize("lifecycle", ("draft", "implementing", "ready", "correcting"))
def test_named_lifecycle_states_are_valid(lifecycle: str) -> None:
    assert _codes(_fixture(lifecycle)) == []
def test_review_dismissed_enters_correcting_without_counting_approval() -> None:
    fixture = _fixture("correcting")
    fixture["event_name"], fixture["event"] = "pull_request_review", _event("pull_request_review", "dismissed")
    fixture["responses"]["reviews"] = [(200, {}, [_review(state="DISMISSED")])]
    assert _codes(fixture) == []
    assert _codes(_single(fixture, lambda f: f["event"].__setitem__("sender", _identity("other", 3)))) == ["GPF.GH.REVIEW_IDENTITY_MISMATCH"]
def test_draft_with_historical_approval_defers_failing_checks() -> None:
    fixture = _fixture("ready")
    fixture["event_name"], fixture["event"] = "pull_request", _event("pull_request", "converted_to_draft")
    fixture["responses"]["pr"][0][2]["draft"] = True
    fixture["responses"]["checks"][0][2]["check_runs"][0]["conclusion"] = "failure"
    assert _codes(fixture) == []
@pytest.mark.parametrize("action", ("opened", "synchronize", "reopened", "edited", "ready_for_review"))
def test_original_pr_events_enforce_current_live_approval_and_checks(action: str) -> None:
    fixture = _fixture("ready")
    fixture["event_name"], fixture["event"] = "pull_request", _event("pull_request", action)
    assert _codes(copy.deepcopy(fixture)) == []
    changed = _single(fixture, lambda f: f["responses"]["checks"][0][2]["check_runs"][1].__setitem__("conclusion", "failure"))
    assert _codes(changed) == ["GPF.GH.CHECK_NOT_SUCCESSFUL"]
@pytest.mark.parametrize(("mutation", "expected"), (
    (lambda f: f.update(event_name="push"), "GPF.GH.EVENT_UNSUPPORTED"),
    (lambda f: f["event"].__setitem__("action", "closed"), "GPF.GH.EVENT_UNSUPPORTED"),
    (lambda f: f["event"].pop("pull_request"), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["repository"].__setitem__("full_name", "attacker/repo"), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["pull_request"]["head"]["repo"].__setitem__("full_name", "attacker/repo"), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["pull_request"]["base"]["repo"].__setitem__("full_name", "attacker/repo"), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["pull_request"]["base"].__setitem__("ref", "attacker"), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"].__setitem__("number", 179), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f.__setitem__("event", None), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["pull_request"].__setitem__("draft", None), "GPF.GH.EVENT_PAYLOAD_INVALID"),
    (lambda f: f["event"]["pull_request"]["head"].__setitem__("sha", "bad"), "GPF.GH.EVENT_PAYLOAD_INVALID"),))
def test_event_single_faults_short_circuit_auth(mutation: Any, expected: str) -> None:
    fixture = _fixture()
    assert _codes(copy.deepcopy(fixture)) == []
    mutation(fixture)
    def forbidden() -> str:
        raise AssertionError("AUTH_LOOKUP")
    transport = Transport(fixture)
    findings = verify_governance_preflight_github(
        fixture["event"], event_name=fixture["event_name"], repository=REPOSITORY, api_url=API,
        required_contexts=CONTEXTS, expected_app_id=APP_ID, run_id=999, token_provider=forbidden,
        transport=transport, clock=Clock(), sleeper=lambda _: None,
    )
    assert [item.code for item in findings] == [expected]
    assert transport.calls == []
def test_auth_unavailable_is_exact() -> None:
    fixture = _fixture()
    assert _codes(copy.deepcopy(fixture)) == []
    assert _codes(fixture, auth_value=None) == ["GPF.GH.AUTH_UNAVAILABLE"]
    assert fixture["calls"] == []
    assert _codes(_fixture(), auth_value=RuntimeError("sentinel-token")) == ["GPF.GH.AUTH_UNAVAILABLE"]
    assert _codes(_fixture(), api_url="http://api.github.com") == ["GPF.GH.EVENT_PAYLOAD_INVALID"]
@pytest.mark.parametrize(("field", "value"), (("user", None), ("id", True), ("state", None)))
def test_malformed_review_event_payload_is_rejected(field: str, value: Any) -> None:
    fixture = _fixture("ready")
    fixture["event"]["review"][field] = value
    assert _codes(fixture) == ["GPF.GH.EVENT_PAYLOAD_INVALID"]
@pytest.mark.parametrize("event_name", ("", "push", "workflow_dispatch"))
def test_push_and_local_paths_make_no_auth_or_transport_attempt(event_name: str) -> None:
    fixture = _fixture()
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError((args, kwargs))
    findings = verify_governance_preflight_github(
        fixture["event"], event_name=event_name, repository=REPOSITORY, api_url=API,
        required_contexts=CONTEXTS, expected_app_id=APP_ID, run_id=999,
        token_provider=forbidden, transport=forbidden, clock=Clock(), sleeper=forbidden,
    )
    assert [item.code for item in findings] == ["GPF.GH.EVENT_UNSUPPORTED"]
@pytest.mark.parametrize(("name", "mutate", "expected"), (
    ("author-id", lambda f: f["event"]["pull_request"]["user"].__setitem__("id", 9), "GPF.GH.PR_AUTHOR_MISMATCH"),
    ("author-login", lambda f: f["event"]["pull_request"]["user"].__setitem__("login", "other"), "GPF.GH.PR_AUTHOR_MISMATCH"),
    ("head", lambda f: f["event"]["pull_request"]["head"].__setitem__("sha", OTHER_HEAD), "GPF.GH.PR_HEAD_MISMATCH"),
    ("live-number", lambda f: f["responses"]["pr"][0][2].__setitem__("number", 179), "GPF.GH.RESPONSE_INVALID"),
    ("lifecycle", lambda f: f["responses"]["pr"][0][2].__setitem__("state", "closed"), "GPF.GH.LIFECYCLE_INVALID"),
    ("merged", lambda f: f["responses"]["pr"][0][2].__setitem__("merged", True), "GPF.GH.LIFECYCLE_INVALID"),))
def test_pr_identity_and_lifecycle_single_faults(name: str, mutate: Any, expected: str) -> None:
    del name
    fixture = _fixture()
    assert _codes(_single(fixture, mutate)) == [expected]
@pytest.mark.parametrize(("name", "mutate", "expected"), (
    ("missing", lambda f: f["responses"].__setitem__("reviews", [(200, {}, [])]), "GPF.GH.REVIEW_MISSING"),
    ("review-id", lambda f: f["event"]["review"].__setitem__("id", 21), "GPF.GH.REVIEW_MISSING"),
    ("reviewer-id", lambda f: f["event"]["review"]["user"].__setitem__("id", 3), "GPF.GH.REVIEW_IDENTITY_MISMATCH"),
    ("reviewer-login", lambda f: f["event"]["review"]["user"].__setitem__("login", "other"), "GPF.GH.REVIEW_IDENTITY_MISMATCH"),
    ("sender-id", lambda f: f["event"]["sender"].__setitem__("id", 3), "GPF.GH.REVIEW_IDENTITY_MISMATCH"),
    ("sender-login", lambda f: f["event"]["sender"].__setitem__("login", "other"), "GPF.GH.REVIEW_IDENTITY_MISMATCH"),
    ("self", _self_reviewer, "GPF.GH.REVIEW_SELF_APPROVAL"),
    ("association", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("author_association", "CONTRIBUTOR"), "GPF.GH.REVIEW_ASSOCIATION_INVALID"),
    ("commented", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("state", "COMMENTED"), "GPF.GH.REVIEW_STATE_INVALID"),
    ("changes", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("state", "CHANGES_REQUESTED"), "GPF.GH.REVIEW_STATE_INVALID"),
    ("dismissed", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("state", "DISMISSED"), "GPF.GH.REVIEW_STATE_INVALID"),
    ("stale", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("commit_id", OTHER_HEAD), "GPF.GH.REVIEW_STALE"),))
def test_review_single_fault_matrix(name: str, mutate: Any, expected: str) -> None:
    del name
    fixture = _fixture("ready")
    assert _codes(_single(fixture, mutate)) == [expected]
@pytest.mark.parametrize("association", ("OWNER", "MEMBER", "COLLABORATOR"))
def test_all_approved_reviewer_associations_are_valid(association: str) -> None:
    fixture = _fixture("ready")
    fixture["event"]["review"]["author_association"] = association
    fixture["responses"]["reviews"][0][2][0]["author_association"] = association
    assert _codes(fixture) == []
def test_approval_like_mutable_prose_never_counts() -> None:
    fixture = _fixture()
    fixture["event"]["pull_request"]["body"] = "APPROVED by reviewer"
    fixture["event"]["comment"] = {"body": "reviewer approved exact head"}
    assert _codes(fixture) == []
@pytest.mark.parametrize(("name", "mutate", "expected"), (
    ("missing", lambda runs: runs.pop(), "GPF.GH.CHECK_MISSING"),
    ("app", lambda runs: runs[0]["app"].__setitem__("id", 9), "GPF.GH.CHECK_APP_MISMATCH"),
    ("stale", lambda runs: runs[0].__setitem__("head_sha", OTHER_HEAD), "GPF.GH.CHECK_MISSING"),
    ("failed", lambda runs: runs[0].__setitem__("conclusion", "failure"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("cancelled", lambda runs: runs[0].__setitem__("conclusion", "cancelled"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("skipped", lambda runs: runs[0].__setitem__("conclusion", "skipped"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("neutral", lambda runs: runs[0].__setitem__("conclusion", "neutral"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("timed-out", lambda runs: runs[0].__setitem__("conclusion", "timed_out"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("action-required", lambda runs: runs[0].__setitem__("conclusion", "action_required"), "GPF.GH.CHECK_NOT_SUCCESSFUL"),
    ("success-incomplete", lambda runs: runs[1].__setitem__("status", "queued"), "GPF.GH.CHECK_PENDING_TIMEOUT"),))
def test_check_single_fault_matrix(name: str, mutate: Any, expected: str) -> None:
    del name
    fixture = _fixture("ready")
    changed = _single(fixture, lambda f: mutate(f["responses"]["checks"][0][2]["check_runs"]))
    assert _codes(changed) == [expected]
def test_pending_checks_poll_to_success_with_fake_clock() -> None:
    fixture = _fixture("ready")
    def mutate(value: dict[str, Any]) -> None:
        pending = copy.deepcopy(value["responses"]["checks"][0][2])
        pending["check_runs"][1].update(status="in_progress", conclusion=None)
        value["responses"]["checks"] = [(200, {}, pending), value["responses"]["checks"][0]]
    fixture = _single(fixture, mutate)
    clock = Clock()
    assert _codes(fixture, clock=clock) == []
    assert clock.now == 5
def test_pending_checks_expire_at_fake_deadline() -> None:
    fixture = _fixture("ready")
    fixture = _single(
        fixture,
        lambda f: f["responses"]["checks"][0][2]["check_runs"][1].update(status="in_progress", conclusion=None),
    )
    clock = Clock()
    assert _codes(fixture, clock=clock) == ["GPF.GH.CHECK_PENDING_TIMEOUT"]
    assert clock.now == 360
def test_policy_self_check_requires_exact_run_identity() -> None:
    fixture = _fixture("ready")
    current = _single(
        fixture,
        lambda f: f["responses"]["checks"][0][2]["check_runs"][0].update(status="in_progress", conclusion=None),
    )
    assert _codes(current) == []
    wrong = copy.deepcopy(current)
    wrong["responses"]["checks"][0][2]["check_runs"][0]["details_url"] = (
        "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/998/job/1"
    )
    assert _codes(wrong) == ["GPF.GH.CHECK_PENDING_TIMEOUT"]
def test_duplicate_attempts_choose_latest_deterministically() -> None:
    fixture = _fixture("ready")
    runs = fixture["responses"]["checks"][0][2]["check_runs"]
    old = copy.deepcopy(runs[1])
    old.update(id=1, conclusion="failure", completed_at="2026-07-15T00:00:01Z")
    runs.insert(0, old)
    assert _codes(fixture) == []
    fixture = _fixture("ready")
    runs = fixture["responses"]["checks"][0][2]["check_runs"]
    tied = copy.deepcopy(runs[1])
    tied.update(id=runs[1]["id"] + 1, conclusion="failure")
    runs.append(tied)
    assert _codes(fixture) == ["GPF.GH.CHECK_NOT_SUCCESSFUL"]
@pytest.mark.parametrize("url", (
    "https://evil.example/imrohitagrawal/narratwin-ai/actions/runs/999/job/1",
    "https://github.com/attacker/repo/actions/runs/999/job/1",
    "https://github.com/imrohitagrawal/narratwin-ai/actions/workflows/999",
    "http://github.com/imrohitagrawal/narratwin-ai/actions/runs/999/job/1",
    "https://x@github.com/imrohitagrawal/narratwin-ai/actions/runs/999/job/1",))
def test_policy_self_check_rejects_hostile_same_run_links(url: str) -> None:
    fixture = _fixture("ready")
    def mutate(value: dict[str, Any]) -> None:
        run = value["responses"]["checks"][0][2]["check_runs"][0]
        run.update(status="in_progress", conclusion=None, details_url=url)
    assert _codes(_single(fixture, mutate)) == ["GPF.GH.CHECK_PENDING_TIMEOUT"]
@pytest.mark.parametrize(("case", "link", "expected"), (
    ("relative", "</repos/imrohitagrawal/narratwin-ai/pulls/178/reviews?per_page=100&page=2>; rel=\"next\"", []),
    ("absolute", "<https://api.github.com/repos/imrohitagrawal/narratwin-ai/pulls/178/reviews?per_page=100&page=2>; rel=\"next\"", []),
    ("cross", "<https://evil.example/reviews?page=2>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),
    ("http", "<http://api.github.com/repos/imrohitagrawal/narratwin-ai/pulls/178/reviews?page=2>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),
    ("userinfo", "<https://x@api.github.com/repos/imrohitagrawal/narratwin-ai/pulls/178/reviews?page=2>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),
    ("wrong-path", "<https://api.github.com/repos/imrohitagrawal/narratwin-ai/pulls/179/reviews?page=2>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),
    ("bad-query", "</repos/imrohitagrawal/narratwin-ai/pulls/178/reviews?page=x>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),
    ("malformed", "<::::>; rel=\"next\"", ["GPF.GH.PAGINATION_NEXT_INVALID"]),))
def test_pagination_origin_contract(case: str, link: str, expected: list[str]) -> None:
    del case
    fixture = _fixture("ready")
    def mutation(f: dict[str, Any]) -> None:
        f["responses"]["reviews"] = [(200, {"Link": link}, [_review()]), (200, {}, [])]
    changed = _single(fixture, mutation) if expected else copy.deepcopy(fixture)
    if not expected:
        mutation(changed)
    assert _codes(changed) == expected
@pytest.mark.parametrize(("fault", "response", "expected"), (
    ("rate403", (403, {"X-RateLimit-Remaining": "0"}, {}), "GPF.GH.RATE_LIMITED"),
    ("rate429", (429, {}, {}), "GPF.GH.RATE_LIMITED"),
    ("bad-json", (200, {}, b"{"), "GPF.GH.RESPONSE_INVALID"),
    ("wrong-shape", (200, {}, {}), "GPF.GH.RESPONSE_INVALID"),
    ("redirect", (302, {"Location": "https://evil.example/x"}, {}), "GPF.GH.API_ERROR"),
    ("api", (500, {}, {"message": "sentinel-token hostile"}), "GPF.GH.API_ERROR"),))
@pytest.mark.parametrize("endpoint", ("pr", "reviews", "checks"))
def test_terminal_transport_faults_are_sanitized(fault: str, response: Any, expected: str, endpoint: str, capsys: Any) -> None:
    fixture = _fixture("ready")
    changed = _single(fixture, lambda f: f["responses"].__setitem__(endpoint, [response]))
    clock = Clock()
    assert _codes(changed, clock=clock) == [expected]
    if fault.startswith("rate"):
        suffix = "/reviews" if endpoint == "reviews" else "/check-runs" if endpoint == "checks" else "/pulls/178"
        assert sum(urlsplit(call[0]).path.endswith(suffix) for call in changed["calls"]) == 1
        assert clock.now == 0
    output = capsys.readouterr()
    assert "sentinel-token" not in output.out + output.err
def test_timeout_maps_exactly_without_exposing_exception(capsys: Any) -> None:
    fixture = _fixture("ready")
    changed = _single(fixture, lambda f: f["responses"].__setitem__("reviews", [TimeoutError("sentinel-token")]))
    assert _codes(changed) == ["GPF.GH.REQUEST_TIMEOUT"]
    output = capsys.readouterr()
    assert "sentinel-token" not in output.out + output.err
@pytest.mark.parametrize(("endpoint", "record"), (("reviews", {"id": True}), ("checks", {"id": True})))
def test_malformed_collection_record_is_response_invalid(endpoint: str, record: dict[str, Any]) -> None:
    fixture = _fixture("ready")
    payload: Any = [record] if endpoint == "reviews" else {"check_runs": [record]}
    assert _codes(_single(fixture, lambda f: f["responses"].__setitem__(endpoint, [(200, {}, payload)]))) == ["GPF.GH.RESPONSE_INVALID"]
def test_live_cross_repository_response_is_invalid() -> None:
    fixture = _fixture()
    assert _codes(_single(fixture, lambda f: f["responses"]["pr"][0][2]["head"]["repo"].__setitem__("full_name", "evil/repo"))) == ["GPF.GH.RESPONSE_INVALID"]
def _padded(payload: Any, size: int) -> bytes:
    value = copy.deepcopy(payload)
    target = value[0] if isinstance(value, list) else value
    target["padding"] = ""
    raw = json.dumps(value, separators=(",", ":")).encode()
    target["padding"] = "x" * (size - len(raw))
    result = json.dumps(value, separators=(",", ":")).encode()
    assert len(result) == size
    return result
@pytest.mark.parametrize("endpoint", ("pr", "reviews", "checks"))
@pytest.mark.parametrize(("size", "expected"), ((1 << 20, []), ((1 << 20) + 1, ["GPF.GH.RESPONSE_INVALID"])))
def test_each_response_byte_boundary(endpoint: str, size: int, expected: list[str]) -> None:
    fixture = _fixture("ready")
    payload = fixture["responses"][endpoint][0][2]
    def mutation(f: dict[str, Any]) -> None:
        f["responses"][endpoint] = [(200, {}, _padded(payload, size))]
    changed = _single(fixture, mutation) if expected else copy.deepcopy(fixture)
    if not expected:
        mutation(changed)
    assert _codes(changed) == expected
@pytest.mark.parametrize("collection", ("reviews", "checks"))
def test_collection_page_record_and_timeout_bounds(collection: str) -> None:
    fixture = _fixture("ready")
    path = "/repos/imrohitagrawal/narratwin-ai/pulls/178/reviews" if collection == "reviews" else f"/repos/imrohitagrawal/narratwin-ai/commits/{HEAD}/check-runs"
    records = [_review() for _ in range(100)] if collection == "reviews" else [_check(CONTEXTS[i % 2]) for i in range(100)]
    wrap = (lambda rows: rows) if collection == "reviews" else (lambda rows: {"total_count": len(rows), "check_runs": rows})
    def pages(count: int, next_on_last: bool = False) -> list[Any]:
        result = []
        for index in range(count):
            more = index + 1 < count or next_on_last
            headers = {"Link": f"<{path}?per_page=100&page={index + 2}>; rel=\"next\""} if more else {}
            result.append((200, headers, wrap(copy.deepcopy(records))))
        return result
    accepted = copy.deepcopy(fixture)
    accepted["responses"][collection] = pages(10)
    assert _codes(accepted) == []
    assert all(call[2] == 10 for call in accepted["calls"])
    assert all("per_page=100" in call[0] for call in accepted["calls"] if path in call[0])
    over_page = _single(fixture, lambda f: f["responses"].__setitem__(collection, [(200, {}, wrap(records + [records[0]]))]))
    assert _codes(over_page) == ["GPF.GH.PAGINATION_LIMIT"]
    over_pages = _single(fixture, lambda f: f["responses"].__setitem__(collection, pages(10, True)))
    assert _codes(over_pages) == ["GPF.GH.PAGINATION_LIMIT"]
def test_global_precedence_and_deduplication_complete_vector() -> None:
    fixture = _fixture("ready")
    live = fixture["responses"]["pr"][0][2]
    live["user"] = _identity("other", 9)
    fixture["event"]["pull_request"]["head"]["sha"] = OTHER_HEAD
    live["state"] = "closed"
    review = fixture["responses"]["reviews"][0][2][0]
    review.update(user=_identity("author", 1), author_association="CONTRIBUTOR", state="COMMENTED", commit_id=OTHER_HEAD)
    runs = fixture["responses"]["checks"][0][2]["check_runs"]
    runs.pop()
    runs[0]["app"]["id"] = 9
    assert _codes(fixture) == [
        "GPF.GH.PR_AUTHOR_MISMATCH", "GPF.GH.PR_HEAD_MISMATCH", "GPF.GH.LIFECYCLE_INVALID",
        "GPF.GH.REVIEW_IDENTITY_MISMATCH", "GPF.GH.REVIEW_SELF_APPROVAL",
        "GPF.GH.REVIEW_ASSOCIATION_INVALID", "GPF.GH.REVIEW_STATE_INVALID", "GPF.GH.REVIEW_STALE",
        "GPF.GH.CHECK_MISSING", "GPF.GH.CHECK_APP_MISMATCH",
    ]
def test_terminal_and_complete_check_precedence_vectors() -> None:
    fixture = _fixture("ready")
    assert _codes(copy.deepcopy(fixture)) == []
    terminal = copy.deepcopy(fixture)
    terminal["responses"]["reviews"] = [(200, {"Link": "<https://evil.example/x>; rel=\"next\""}, [_review()])]
    terminal["responses"]["checks"] = [(429, {}, {})]
    assert _codes(terminal) == ["GPF.GH.PAGINATION_NEXT_INVALID", "GPF.GH.RATE_LIMITED"]
    checks = copy.deepcopy(fixture)
    runs = checks["responses"]["checks"][0][2]["check_runs"]
    runs[0].update(status="in_progress", conclusion=None)
    runs[0]["details_url"] = "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/998/job/1"
    runs[1]["conclusion"] = "failure"
    assert _codes(checks) == ["GPF.GH.CHECK_PENDING_TIMEOUT", "GPF.GH.CHECK_NOT_SUCCESSFUL"]
    deduped = copy.deepcopy(fixture)
    for run in deduped["responses"]["checks"][0][2]["check_runs"]:
        run["app"]["id"] = 9
    assert _codes(deduped) == ["GPF.GH.CHECK_APP_MISMATCH"]
def test_exactly_200_seeded_sequences_have_reproducible_oracles() -> None:
    results: list[bool] = []
    durations: list[float] = []
    mutations = (
        ("author", lambda f: f["responses"]["pr"][0][2].__setitem__("user", _identity("x", 9)), "GPF.GH.PR_AUTHOR_MISMATCH"),
        ("review-self", _self_reviewer, "GPF.GH.REVIEW_SELF_APPROVAL"),
        ("review-stale", lambda f: f["responses"]["reviews"][0][2][0].__setitem__("commit_id", OTHER_HEAD), "GPF.GH.REVIEW_STALE"),
        ("check-app", lambda f: f["responses"]["checks"][0][2]["check_runs"][0]["app"].__setitem__("id", 9), "GPF.GH.CHECK_APP_MISMATCH"),
        ("check-missing", lambda f: f["responses"]["checks"][0][2]["check_runs"].pop(), "GPF.GH.CHECK_MISSING"),
    )
    for seed in SEEDS:
        rng = random.Random(seed)
        for index in range(20):
            valid = index < 10
            lifecycle = ("draft", "implementing", "ready", "correcting")[index % 4] if valid else "ready"
            baseline_fixture = _fixture(lifecycle)
            if valid and lifecycle == "ready" and index % 2:
                baseline_fixture["event_name"] = "pull_request"
                baseline_fixture["event"] = _event("pull_request", "synchronize")
            baseline = _codes(copy.deepcopy(baseline_fixture))
            fixture = copy.deepcopy(baseline_fixture)
            mutation, expected = "none", []
            if not valid:
                mutation, apply, code = mutations[rng.randrange(len(mutations))]
                apply(fixture)
                expected = [code]
            serialized = json.dumps(
                {"event_name": fixture["event_name"], "event": fixture["event"], "responses": fixture["responses"]},
                sort_keys=True, default=str,
            )
            started = time.perf_counter()
            actual = _codes(fixture)
            durations.append(time.perf_counter() - started)
            detail = json.dumps({"seed": seed, "sequence": index, "lifecycle": lifecycle, "mutation": mutation,
                                 "expected": expected, "actual": actual, "fixture": serialized}, sort_keys=True)
            assert baseline == [], detail
            assert actual == expected, detail
            results.append(valid)
    assert len(results) == 200 and results.count(True) == results.count(False) == 100
    assert max(durations) < 1
@pytest.mark.parametrize(("github_token", "gh_token", "cli_token", "expected"), (
    ("g", "h", "c", "g"), (" ", "h", "c", "h"), ("", " ", "c", "c"),))
def test_cli_auth_precedence_and_fixed_fallback(tmp_path: Path, github_token: str, gh_token: str, cli_token: str, expected: str) -> None:
    fixture = _fixture()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(fixture["event"]), encoding="utf-8")
    transport = Transport(fixture)
    calls: list[tuple[Any, Any]] = []
    def runner(argv: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, cli_token + "\n", "")
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event_path), "GITHUB_REPOSITORY": REPOSITORY,
           "GITHUB_API_URL": API, "GITHUB_RUN_ID": "999", "GITHUB_TOKEN": github_token, "GH_TOKEN": gh_token}
    assert main(environ=env, run_command=runner, transport=transport, clock=Clock(), sleeper=lambda _: None) == 0
    assert transport.calls[0][1]["Authorization"] == f"Bearer {expected}"
    if expected == cli_token:
        argv, kwargs = calls[0]
        assert argv == ["gh", "auth", "token"] and kwargs["shell"] is False and kwargs["timeout"] == 10
        assert kwargs["capture_output"] is True
    else:
        assert calls == []
@pytest.mark.parametrize(("returncode", "stdout", "exception"), (
    (1, "x", None), (0, " ", None), (0, "\x00bad", None),
    (0, "x", subprocess.TimeoutExpired("gh", 10)),))
def test_cli_auth_failure_is_sanitized(tmp_path: Path, returncode: int, stdout: str, exception: BaseException | None, capsys: Any) -> None:
    fixture = _fixture()
    assert _codes(copy.deepcopy(fixture)) == []
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(fixture["event"]), encoding="utf-8")
    def runner(argv: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if exception:
            raise exception
        return subprocess.CompletedProcess(argv, returncode, stdout, "sentinel-secret")
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event_path), "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_API_URL": API}
    assert main(environ=env, run_command=runner, transport=Transport(fixture), clock=Clock(), sleeper=lambda _: None) == 1
    output = capsys.readouterr()
    assert "GPF.GH.AUTH_UNAVAILABLE" in output.out
    assert "sentinel-secret" not in output.out + output.err
def test_default_transport_network_attempt_is_observed_blocked_and_sanitized(tmp_path: Path, monkeypatch: Any, capsys: Any) -> None:
    fixture = _fixture()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(fixture["event"]), encoding="utf-8")
    attempted: list[bool] = []
    class Denied(socket.socket):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any:
            attempted.append(True)
            raise github.urllib.error.URLError(TimeoutError("sentinel-token NETWORK_ATTEMPT"))  # type: ignore[attr-defined]
    monkeypatch.setattr(socket, "socket", Denied)
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event_path),
           "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_API_URL": API, "GITHUB_TOKEN": "sentinel-token"}
    assert main(environ=env, clock=Clock(), sleeper=lambda _: None) == 1
    output = capsys.readouterr()
    assert attempted and "sentinel-token" not in output.out + output.err
    assert "sentinel-token" not in event_path.read_text(encoding="utf-8")
    config = subprocess.run(["git", "config", "--local", "--list"], capture_output=True, text=True, check=True)
    assert "sentinel-token" not in config.stdout + config.stderr
def test_default_https_transport_refuses_cross_origin_redirect(tmp_path: Path, monkeypatch: Any) -> None:
    fixture = _fixture()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(fixture["event"]), encoding="utf-8")
    seen: list[str] = []
    real_build_opener = github.urllib.request.build_opener  # type: ignore[attr-defined]
    class Probe(github.urllib.request.BaseHandler):  # type: ignore[name-defined,misc]
        def https_open(self, request: Any) -> Any:
            seen.append(request.full_url)
            if request.full_url.startswith("https://evil.example"):
                raise AssertionError("FOREIGN_REDIRECT")
            headers = email.message.Message()
            headers["Location"] = "https://evil.example/x"
            response = github.urllib.response.addinfourl(io.BytesIO(b"{}"), headers, request.full_url, 302)  # type: ignore[attr-defined]
            response.msg = "Found"
            return response
    monkeypatch.setattr(github.urllib.request, "build_opener", lambda *handlers: real_build_opener(Probe(), *handlers))  # type: ignore[attr-defined]
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event_path),
           "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_API_URL": API, "GITHUB_TOKEN": "token"}
    assert main(environ=env, clock=Clock(), sleeper=lambda _: None) == 1
    assert len(seen) == 1 and seen[0].startswith(f"{API}/repos/{REPOSITORY}/pulls/178")
def test_public_interface_is_exact_and_has_no_mutation_surface() -> None:
    verify = inspect.signature(verify_governance_preflight_github)
    cli = inspect.signature(main)
    assert list(verify.parameters) == [
        "event", "event_name", "repository", "api_url", "required_contexts", "expected_app_id",
        "run_id", "token_provider", "transport", "clock", "sleeper",
    ]
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in list(verify.parameters.values())[1:])
    assert all(value.default is inspect.Parameter.empty for value in verify.parameters.values())
    assert {name: str(value.annotation).strip("'") for name, value in verify.parameters.items()} == {
        "event": "object", "event_name": "str", "repository": "str", "api_url": "str",
        "required_contexts": "tuple[str, ...]", "expected_app_id": "int", "run_id": "int | None",
        "token_provider": "Callable[[], str | None]",
        "transport": "Callable[[str, Mapping[str, str], float], tuple[int, Mapping[str, str], bytes]]",
        "clock": "Callable[[], float]", "sleeper": "Callable[[float], None]",
    }
    assert list(cli.parameters) == ["argv", "environ", "run_command", "transport", "clock", "sleeper"]
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in list(cli.parameters.values())[1:])
    assert all(value.annotation is not inspect.Parameter.empty for value in (*verify.parameters.values(), *cli.parameters.values()))
    assert verify.return_annotation is not inspect.Signature.empty and cli.return_annotation is not inspect.Signature.empty
    assert str(verify.return_annotation).strip("'") == "list[GovernanceFinding]"
    assert str(cli.return_annotation).strip("'") == "int"
    assert {name: str(value.annotation).strip("'") for name, value in cli.parameters.items()} == {
        "argv": "Sequence[str] | None", "environ": "Mapping[str, str]",
        "run_command": "Callable[..., subprocess.CompletedProcess[str]]", "transport": "Transport | None",
        "clock": "Callable[[], float]", "sleeper": "Callable[[float], None]",
    }
    assert [value.default for value in cli.parameters.values()] == [
        None, os.environ, subprocess.run, None, time.monotonic, time.sleep,
    ]
    assert github.__all__ == ["GovernanceFinding", "verify_governance_preflight_github", "main"]
    assert github.GovernanceFinding is GovernanceFinding
    assert not {"correct", "mutate", "approve", "dismiss", "persist"} & set(dir(github))
def test_workflow_contract_is_exact_not_comment_or_nesting_text() -> None:
    workflow = Path(".github/workflows/quality-gates.yml").read_text(encoding="utf-8")
    permissions = workflow.split("permissions:\n", 1)[1].split("\n\n", 1)[0].splitlines()
    assert permissions == ["  contents: read", "  issues: read", "  pull-requests: read", "  checks: read"]
    assert "types: [opened, synchronize, reopened, edited, ready_for_review, converted_to_draft]" in workflow
    assert "pull_request_review:\n    types: [submitted, dismissed]\n    branches:\n      - main\n      - phase-1-closure-**" in workflow
    assert "persist-credentials: false" in workflow and "governance_preflight_github.py" in workflow
    assert workflow.index("verify_branch_protection.py") < workflow.index("governance_preflight_github.py")
    assert workflow.count("python scripts/governance_preflight_github.py") == 1
    step = workflow.split("- name: Verify GovernancePreflightV1 GitHub evidence", 1)[1].split("\n      - name:", 1)[0]
    assert "if: github.event_name == 'pull_request' || github.event_name == 'pull_request_review'" in step
    assert "python scripts/governance_preflight_github.py" in step
    assert "GITHUB_TOKEN: ${{ github.token }}" in step
    assert workflow.count("\npermissions:\n") == 1
    assert "write-all" not in workflow and not any(": write" in line for line in workflow.splitlines())
    assert "actions: read" not in workflow and "github.event.issue" not in workflow
def test_phase_scope_exact_branch_and_near_match(monkeypatch: Any) -> None:
    from scripts.quality import check_phase1_closure_docs as phase1
    files = set(json.loads(Path("docs/governance/preflights/issue-178.json").read_text())["scope"]["required"])
    assert phase1.ISSUE_178_ALLOWED_CHANGED_FILES == files
    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-process-178-gpf-v1-ci-evidence")
    monkeypatch.setattr(phase1, "changed_files", lambda: sorted(files))
    failures: list[str] = []
    phase1.check_changed_files(failures)
    assert failures == []
    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-process-178-gpf-v1-ci-evidence-extra")
    failures = []
    phase1.check_changed_files(failures)
    assert any("may not change scripts/governance_preflight_github.py" in item for item in failures)
def test_pr_a_pr_b_and_branch_protection_regressions_remain_importable() -> None:
    from scripts.ci.verify_branch_protection import EXPECTED_CONTEXTS, GITHUB_ACTIONS_APP_ID
    from scripts.governance_preflight_repository import validate_governance_preflight_repository
    from scripts.governance_preflight_v1 import validate_governance_preflight
    assert len(EXPECTED_CONTEXTS) == 10 and GITHUB_ACTIONS_APP_ID == APP_ID
    assert callable(validate_governance_preflight) and callable(validate_governance_preflight_repository)
