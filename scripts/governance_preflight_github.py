#!/usr/bin/env python3
"""CI-only verification of live GovernancePreflightV1 GitHub evidence."""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
from collections.abc import Callable, Mapping, Sequence
from typing import Any
from scripts.ci.verify_branch_protection import EXPECTED_CONTEXTS, GITHUB_ACTIONS_APP_ID
from scripts.governance_preflight_v1 import GovernanceFinding
Transport = Callable[[str, Mapping[str, str], float], tuple[int, Mapping[str, str], bytes]]
__all__ = ["GovernanceFinding", "verify_governance_preflight_github", "main"]
_ORDER = (
    "GPF.GH.PAGINATION_NEXT_INVALID", "GPF.GH.PAGINATION_LIMIT", "GPF.GH.RATE_LIMITED", "GPF.GH.REQUEST_TIMEOUT", "GPF.GH.RESPONSE_INVALID", "GPF.GH.API_ERROR", "GPF.GH.PR_AUTHOR_MISMATCH", "GPF.GH.PR_HEAD_MISMATCH", "GPF.GH.LIFECYCLE_INVALID", "GPF.GH.REVIEW_MISSING",
    "GPF.GH.REVIEW_IDENTITY_MISMATCH", "GPF.GH.REVIEW_SELF_APPROVAL", "GPF.GH.REVIEW_ASSOCIATION_INVALID", "GPF.GH.REVIEW_STATE_INVALID", "GPF.GH.REVIEW_STALE", "GPF.GH.CHECK_MISSING", "GPF.GH.CHECK_APP_MISMATCH", "GPF.GH.CHECK_PENDING_TIMEOUT",
    "GPF.GH.CHECK_NOT_SUCCESSFUL",
)
_ACTIONS = {"pull_request": {"opened", "synchronize", "reopened", "edited", "ready_for_review", "converted_to_draft"}, "pull_request_review": {"submitted", "dismissed"}}
def _findings(codes: Sequence[str]) -> list[GovernanceFinding]:
    unique = set(codes)
    return [GovernanceFinding(code) for code in _ORDER if code in unique]
def _user(value: Any) -> tuple[str, int] | None:
    if not isinstance(value, dict) or not isinstance(value.get("login"), str):
        return None
    user_id = value.get("id")
    return (value["login"], user_id) if value["login"] and isinstance(user_id, int) and not isinstance(user_id, bool) else None
def _event_values(event: object, event_name: str, repository: str) -> tuple[dict[str, Any], int, str] | None:
    if not isinstance(event, dict) or event_name not in _ACTIONS or event.get("action") not in _ACTIONS[event_name]:
        return None
    pull, repo, number = event.get("pull_request"), event.get("repository"), event.get("number")
    if not isinstance(pull, dict) or not isinstance(repo, dict) or repo.get("full_name") != repository:
        return None
    if not isinstance(number, int) or isinstance(number, bool) or number < 1 or pull.get("number", number) != number:
        return None
    head, base = pull.get("head"), pull.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict) or not isinstance(pull.get("draft"), bool):
        return None
    head_repo, base_repo, sha, base_ref = head.get("repo"), base.get("repo"), head.get("sha"), base.get("ref")
    valid_base = base_ref == "main" or isinstance(base_ref, str) and base_ref.startswith("phase-1-closure-")
    if not isinstance(head_repo, dict) or not isinstance(base_repo, dict) or not valid_base:
        return None
    if head_repo.get("full_name") != repository or base_repo.get("full_name") != repository:
        return None
    if not isinstance(sha, str) or re.match(r"[0-9a-fA-F]{40}\Z", sha) is None or _user(pull.get("user")) is None:
        return None
    if event_name == "pull_request_review":
        review = event.get("review")
        if not isinstance(review, dict) or _user(review.get("user")) is None or _user(event.get("sender")) is None:
            return None
        if not isinstance(review.get("id"), int) or isinstance(review.get("id"), bool):
            return None
        if not all(isinstance(review.get(key), str) for key in ("state", "commit_id", "author_association")):
            return None
    return pull, number, sha.lower()
def _header(headers: Mapping[str, str], name: str) -> str:
    return next((str(value) for key, value in headers.items() if key.lower() == name.lower()), "")
def _load(url: str, token: str, transport: Transport) -> tuple[Any, Mapping[str, str], str | None]:
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "narratwin-gpf-ci"}
    try:
        status, response_headers, body = transport(url, headers, 10.0)
    except TimeoutError:
        return None, {}, "GPF.GH.REQUEST_TIMEOUT"
    except Exception:
        return None, {}, "GPF.GH.API_ERROR"
    if status == 429 or status == 403 and _header(response_headers, "X-RateLimit-Remaining") == "0":
        return None, {}, "GPF.GH.RATE_LIMITED"
    if status != 200:
        return None, {}, "GPF.GH.API_ERROR"
    if not isinstance(body, bytes) or len(body) > 1 << 20:
        return None, {}, "GPF.GH.RESPONSE_INVALID"
    try:
        return json.loads(body), response_headers, None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, {}, "GPF.GH.RESPONSE_INVALID"
def _next_url(current: str, value: str, origin: tuple[str, str], path: str) -> str | None:
    match = re.search(r'<([^>]*)>\s*;\s*rel=["\']next["\']', value)
    if not match:
        return None
    try:
        result = urllib.parse.urljoin(current, match.group(1))
        parsed = urllib.parse.urlsplit(result)
    except ValueError:
        return ""
    if parsed.scheme != "https" or parsed.username or parsed.password or (parsed.scheme, parsed.netloc.lower()) != origin:
        return ""
    try:
        query = urllib.parse.parse_qs(parsed.query, strict_parsing=True, keep_blank_values=True)
        bounded = set(query) <= {"page", "per_page"} and all(len(values) == 1 and len(values[0]) <= 6 and 0 < int(values[0]) <= (100 if key == "per_page" else 999999) for key, values in query.items())
    except ValueError:
        bounded = False
    return result if parsed.path == path and not parsed.fragment and bounded else ""
def _pages(url: str, kind: str, token: str, transport: Transport, origin: tuple[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    path, rows, page = urllib.parse.urlsplit(url).path, [], 0
    while url:
        page += 1
        if page > 10:
            return [], ["GPF.GH.PAGINATION_LIMIT"]
        payload, headers, failure = _load(url, token, transport)
        if failure:
            return [], [failure]
        values = payload if kind == "reviews" else payload.get("check_runs") if isinstance(payload, dict) else None
        if not isinstance(values, list) or len(values) > 100 or any(not isinstance(item, dict) for item in values):
            return [], ["GPF.GH.RESPONSE_INVALID" if not isinstance(values, list) or any(not isinstance(item, dict) for item in values or []) else "GPF.GH.PAGINATION_LIMIT"]
        if kind == "reviews" and any(not isinstance(item.get("id"), int) or isinstance(item.get("id"), bool) or _user(item.get("user")) is None or not all(isinstance(item.get(key), str) for key in ("state", "commit_id", "author_association")) for item in values):
            return [], ["GPF.GH.RESPONSE_INVALID"]
        if kind == "checks" and any(not isinstance(item.get("id"), int) or isinstance(item.get("id"), bool) or not all(isinstance(item.get(key), str) for key in ("name", "head_sha", "status")) for item in values):
            return [], ["GPF.GH.RESPONSE_INVALID"]
        rows.extend(values)
        if len(rows) > 1000:
            return [], ["GPF.GH.PAGINATION_LIMIT"]
        link = _header(headers, "Link")
        next_value = _next_url(url, link, origin, path) if link else None
        if next_value == "":
            return [], ["GPF.GH.PAGINATION_NEXT_INVALID"]
        url = next_value or ""
    return rows, []
def _review_codes(event: dict[str, Any], live_pull: dict[str, Any], record: dict[str, Any] | None) -> list[str]:
    if record is None:
        return ["GPF.GH.REVIEW_MISSING"]
    codes: list[str] = []
    reviewer, author = _user(record.get("user")), _user(live_pull.get("user"))
    event_review: dict[str, Any] = event["review"] if isinstance(event.get("review"), dict) else record
    if event.get("review") is not None and (reviewer != _user(event_review.get("user")) or reviewer != _user(event.get("sender"))):
        codes.append("GPF.GH.REVIEW_IDENTITY_MISMATCH")
    if reviewer is not None and reviewer == author:
        codes.append("GPF.GH.REVIEW_SELF_APPROVAL")
    if record.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"} or event_review.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"}:
        codes.append("GPF.GH.REVIEW_ASSOCIATION_INVALID")
    if record.get("state") != "APPROVED" or str(event_review.get("state", "")).upper() != "APPROVED":
        codes.append("GPF.GH.REVIEW_STATE_INVALID")
    if record.get("commit_id") != live_pull["head"]["sha"] or event_review.get("commit_id") != record.get("commit_id"):
        codes.append("GPF.GH.REVIEW_STALE")
    return codes
def _self_check(run: dict[str, Any], repository: str, run_id: int | None) -> bool:
    if run_id is None or run.get("name") != "policy-gates" or not isinstance(run.get("details_url"), str):
        return False
    parsed = urllib.parse.urlsplit(run["details_url"])
    prefix = f"/{repository}/actions/runs/{run_id}/job/"
    return parsed.scheme == "https" and parsed.netloc == "github.com" and not parsed.username and parsed.path.startswith(prefix) and parsed.path[len(prefix):].isdigit()
def _check_codes(rows: list[dict[str, Any]], head: str, contexts: tuple[str, ...], app_id: int, repository: str,
                 run_id: int | None, *, expired: bool) -> tuple[list[str], bool]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("head_sha") != head or row.get("name") not in contexts:
            continue
        key = (str(row.get("completed_at") or row.get("started_at") or ""), row.get("id", -1))
        old = selected.get(row["name"])
        old_key = (str(old.get("completed_at") or old.get("started_at") or ""), old.get("id", -1)) if old else None
        if old_key is None or key > old_key:
            selected[row["name"]] = row
    codes, pending = [], False
    for context in contexts:
        run = selected.get(context)
        if run is None:
            codes.append("GPF.GH.CHECK_MISSING")
            continue
        app = run.get("app")
        if not isinstance(app, dict) or app.get("id") != app_id:
            codes.append("GPF.GH.CHECK_APP_MISMATCH")
        if run.get("status") != "completed":
            if not _self_check(run, repository, run_id):
                pending = True
                if expired:
                    codes.append("GPF.GH.CHECK_PENDING_TIMEOUT")
        elif run.get("conclusion") != "success":
            codes.append("GPF.GH.CHECK_NOT_SUCCESSFUL")
    return codes, pending
def verify_governance_preflight_github(event: object, *, event_name: str, repository: str, api_url: str,
    required_contexts: tuple[str, ...], expected_app_id: int, run_id: int | None,
    token_provider: Callable[[], str | None], transport: Callable[[str, Mapping[str, str], float], tuple[int, Mapping[str, str], bytes]],
    clock: Callable[[], float], sleeper: Callable[[float], None]) -> list[GovernanceFinding]:
    if event_name not in _ACTIONS or isinstance(event, dict) and event.get("action") not in _ACTIONS[event_name]:
        return [GovernanceFinding("GPF.GH.EVENT_UNSUPPORTED")]
    values = _event_values(event, event_name, repository)
    if values is None:
        return [GovernanceFinding("GPF.GH.EVENT_PAYLOAD_INVALID")]
    try:
        auth_value = token_provider()
    except Exception:
        auth_value = None
    if not isinstance(auth_value, str) or not auth_value.strip():
        return [GovernanceFinding("GPF.GH.AUTH_UNAVAILABLE")]
    auth_value = auth_value.strip()
    base = api_url.rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
        return [GovernanceFinding("GPF.GH.EVENT_PAYLOAD_INVALID")]
    event_pull, number, event_head = values
    pull_url = f"{base}/repos/{repository}/pulls/{number}"
    payload, _, failure = _load(pull_url, auth_value, transport)
    if failure:
        return _findings([failure])
    live = payload if isinstance(payload, dict) else None
    if live is None or _user(live.get("user")) is None or not isinstance(live.get("head"), dict):
        return _findings(["GPF.GH.RESPONSE_INVALID"])
    live_head, live_head_repo, live_base = live["head"].get("sha"), live["head"].get("repo"), live.get("base")
    if live.get("number") != number or not isinstance(live_head, str) or re.match(r"[0-9a-fA-F]{40}\Z", live_head) is None or not isinstance(live.get("draft"), bool) or not isinstance(live.get("merged"), bool):
        return _findings(["GPF.GH.RESPONSE_INVALID"])
    if not isinstance(live_head_repo, dict) or live_head_repo.get("full_name") != repository or not isinstance(live_base, dict) or not isinstance(live_base.get("repo"), dict) or live_base["repo"].get("full_name") != repository:
        return _findings(["GPF.GH.RESPONSE_INVALID"])
    origin = (parsed.scheme, parsed.netloc.lower())
    reviews_url = f"{pull_url}/reviews?per_page=100"
    reviews, terminal = _pages(reviews_url, "reviews", auth_value, transport, origin)
    event_dict = event if isinstance(event, dict) else {}
    review_event = event_name == "pull_request_review"
    submitted = review_event and event_dict.get("action") == "submitted"
    event_record = next((row for row in reviews if isinstance(event_dict.get("review"), dict) and row.get("id") == event_dict["review"].get("id")), None)
    record = event_record
    if not submitted:
        current = [row for row in reviews if row.get("state") == "APPROVED" and row.get("commit_id") == live_head]
        record = max(current, key=lambda row: (str(row.get("submitted_at", "")), row.get("id", -1)), default=None)
    ready = submitted or record is not None
    checks: list[dict[str, Any]] = []
    check_url = f"{base}/repos/{repository}/commits/{live_head}/check-runs?per_page=100"
    if ready and not live.get("draft"):
        checks, check_terminal = _pages(check_url, "checks", auth_value, transport, origin)
        terminal.extend(check_terminal)
    if terminal:
        return _findings(terminal)
    codes: list[str] = []
    if _user(event_pull.get("user")) != _user(live.get("user")):
        codes.append("GPF.GH.PR_AUTHOR_MISMATCH")
    if event_head != live_head.lower():
        codes.append("GPF.GH.PR_HEAD_MISMATCH")
    if live.get("state") != "open" or live.get("merged"):
        codes.append("GPF.GH.LIFECYCLE_INVALID")
    if review_event and not submitted:
        codes.extend(["GPF.GH.REVIEW_MISSING"] if event_record is None else ["GPF.GH.REVIEW_IDENTITY_MISMATCH"] if not (_user(event_record.get("user")) == _user(event_dict.get("review", {}).get("user")) == _user(event_dict.get("sender"))) else [])
    if ready and not live.get("draft"):
        codes.extend(_review_codes(event_dict, live, record))
        start = clock()
        for attempt in range(73):
            elapsed = max(0.0, clock() - start)
            expired = elapsed >= 360 or attempt == 72
            check_findings, pending = _check_codes(checks, live_head, required_contexts, expected_app_id, repository, run_id, expired=expired)
            if not pending or expired:
                codes.extend(check_findings)
                break
            sleeper(min(5.0, max(0.0, 360 - elapsed)))
            checks, check_terminal = _pages(check_url, "checks", auth_value, transport, origin)
            if check_terminal:
                return _findings(check_terminal + codes)
    return _findings(codes)
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None
def _https(url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, headers=dict(headers))
    try:
        response = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler()).open(request, timeout=timeout)  # nosec B310
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read((1 << 20) + 1)
    except urllib.error.URLError as exc:
        raise (TimeoutError() if isinstance(exc.reason, TimeoutError) else exc) from None
    with response:
        return response.status, dict(response.headers), response.read((1 << 20) + 1)
def main(
    argv: Sequence[str] | None = None, *, environ: Mapping[str, str] = os.environ,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run, transport: Transport | None = None,
    clock: Callable[[], float] = time.monotonic, sleeper: Callable[[float], None] = time.sleep,
) -> int:
    del argv
    try:
        with open(environ.get("GITHUB_EVENT_PATH", ""), encoding="utf-8") as handle:
            event: object = json.load(handle)
    except (OSError, json.JSONDecodeError):
        event = None
    def token_source() -> str | None:
        for name in ("GITHUB_TOKEN", "GH_TOKEN"):
            if environ.get(name, "").strip():
                return environ[name].strip()
        try:
            result = run_command(["gh", "auth", "token"], shell=False, timeout=10, capture_output=True, text=True, check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        value = result.stdout.strip() if result.returncode == 0 else ""
        return value if value and not any(ord(char) < 32 for char in value) else None
    try:
        run_id = int(environ["GITHUB_RUN_ID"]) if environ.get("GITHUB_RUN_ID") else None
    except ValueError:
        run_id = None
    findings = verify_governance_preflight_github(
        event, event_name=environ.get("GITHUB_EVENT_NAME", ""), repository=environ.get("GITHUB_REPOSITORY", ""),
        api_url=environ.get("GITHUB_API_URL", "https://api.github.com"), required_contexts=EXPECTED_CONTEXTS,
        expected_app_id=GITHUB_ACTIONS_APP_ID, run_id=run_id, token_provider=token_source,
        transport=transport or _https, clock=clock, sleeper=sleeper,
    )
    for finding in findings:
        print(finding.code)
    return int(bool(findings))
if __name__ == "__main__":
    sys.exit(main())
