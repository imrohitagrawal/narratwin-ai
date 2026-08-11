"""CLI for local fixtures and trusted GitHub API reconciliation."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.quality.pr_body_consistency import LiveState, apply, decode_json, reconcile, validate_body


class GitHubApi:
    def __init__(
        self, repository: str, github_auth_value: str, timeout: float = 10.0,
        retries: int = 3, sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 0 < timeout <= 30 or not 1 <= retries <= 3:
            raise ValueError("unsafe GitHub transport limits")
        self.repository, self.github_auth_value, self.timeout = repository, github_auth_value, timeout
        self.retries, self.sleeper = retries, sleeper

    def _request(self, method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        request = Request(f"https://api.github.com{path}", data=data, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {self.github_auth_value}")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=self.timeout) as response:  # nosec B310: fixed GitHub origin
                    raw = response.read(1_000_000).decode("utf-8")
                return decode_json(raw)
            except (HTTPError, URLError, TimeoutError) as exc:
                retryable = not isinstance(exc, HTTPError) or exc.code in {429, 500, 502, 503, 504}
                if not retryable or attempt + 1 == self.retries:
                    raise RuntimeError(f"GitHub API request failed ({type(exc).__name__})") from None
                self.sleeper(float(attempt + 1))
        raise RuntimeError("GitHub API retry budget exhausted")

    def pull(self, number: int) -> dict[str, object]:
        return self._request("GET", f"/repos/{self.repository}/pulls/{number}")

    def update_body(self, number: int, body: str) -> None:
        self._request("PATCH", f"/repos/{self.repository}/pulls/{number}", {"body": body})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.fixture:
        pull = decode_json(args.fixture.read_text(encoding="utf-8"))
        state = LiveState.from_pull(args.repository, pull)
        result = reconcile(str(pull.get("body") or ""), state)
        failures = validate_body(result.body if args.apply else str(pull.get("body") or ""), state)
        print(json.dumps({"changed": result.changed, "failures": failures, "body": result.body if args.apply else None}, sort_keys=True))
        return 1 if failures else 0
    github_auth_value = os.environ.get("GITHUB_TOKEN")
    if not github_auth_value:
        print(json.dumps({"error": "GITHUB_TOKEN is required for live mode"}))
        return 2
    api = GitHubApi(args.repository, github_auth_value)
    if args.apply:
        result = apply(api, args.repository, args.pr)
        print(json.dumps({"changed": result.changed, "failures": []}, sort_keys=True))
        return 0
    pull = api.pull(args.pr)
    failures = validate_body(str(pull.get("body") or ""), LiveState.from_pull(args.repository, pull))
    print(json.dumps({"changed": False, "failures": failures}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
