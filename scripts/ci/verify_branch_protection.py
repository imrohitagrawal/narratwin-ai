#!/usr/bin/env python3
"""Verify reviewer-reproducible branch-protection context evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, cast


EXPECTED_CONTEXTS = (
    "policy-gates",
    "quality / secrets",
    "quality / markdown",
    "lint / typecheck / unit / api",
    "frontend tests / playwright smoke",
    "ci / docker build",
    "secret scan / bandit / audit / semgrep",
    "security / docker build",
    "eval smoke",
    "stage8 / performance lighthouse",
)
GITHUB_ACTIONS_APP_ID = 15368


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate public branch summary protection evidence for a GitHub branch."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", "imrohitagrawal/narratwin-ai"),
        help="GitHub repository in owner/name form.",
    )
    parser.add_argument("--branch", default="main", help="Branch to validate.")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
        help="GitHub API base URL.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Optional branch API JSON fixture for offline validation.",
    )
    return parser.parse_args()


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("fixture payload must be a JSON object")
        return cast(dict[str, Any], payload)

    payload = load_branch_payload(args)
    protection_details = load_protection_payload(args)
    branch_protection = payload.get("protection")
    branch_status_checks = (
        branch_protection.get("required_status_checks")
        if isinstance(branch_protection, dict)
        else None
    )
    detail_status_checks = protection_details.get("required_status_checks")
    if isinstance(branch_status_checks, dict) and isinstance(detail_status_checks, dict):
        for key in ("enforcement_level",):
            if key not in detail_status_checks and key in branch_status_checks:
                detail_status_checks[key] = branch_status_checks[key]
    payload["protection_details"] = protection_details
    return payload


def load_branch_payload(args: argparse.Namespace) -> dict[str, Any]:
    api_base = args.api_url.rstrip("/")
    parsed_api_url = urllib.parse.urlparse(api_base)
    if parsed_api_url.scheme != "https" or not parsed_api_url.netloc:
        raise RuntimeError("GitHub API URL must use an https:// host")

    url = f"{api_base}/repos/{args.repository}/branches/{args.branch}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "narratwin-branch-protection-check",
        },
    )
    github_auth = os.environ.get("GITHUB_TOKEN", "").strip()
    if github_auth:
        request.add_header("Authorization", f"Bearer {github_auth}")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("GitHub branch API response must be a JSON object")
            return cast(dict[str, Any], payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return load_payload_with_gh(args)
        except RuntimeError as gh_exc:
            raise RuntimeError(
                f"GitHub branch API request failed: HTTP {exc.code}: {body}; "
                f"gh fallback failed: {gh_exc}"
            ) from exc
    except urllib.error.URLError as exc:
        try:
            return load_payload_with_gh(args)
        except RuntimeError as gh_exc:
            raise RuntimeError(
                f"GitHub branch API request failed: {exc.reason}; gh fallback failed: {gh_exc}"
            ) from exc


def load_protection_payload(args: argparse.Namespace) -> dict[str, Any]:
    api_base = args.api_url.rstrip("/")
    parsed_api_url = urllib.parse.urlparse(api_base)
    if parsed_api_url.scheme != "https" or not parsed_api_url.netloc:
        raise RuntimeError("GitHub API URL must use an https:// host")

    url = f"{api_base}/repos/{args.repository}/branches/{args.branch}/protection"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "narratwin-branch-protection-check",
        },
    )
    github_auth = os.environ.get("GITHUB_TOKEN", "").strip()
    if github_auth:
        request.add_header("Authorization", f"Bearer {github_auth}")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("GitHub branch protection API response must be a JSON object")
            return cast(dict[str, Any], payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return load_protection_payload_with_gh(args)
        except RuntimeError as gh_exc:
            raise RuntimeError(
                f"GitHub branch protection API request failed: HTTP {exc.code}: {body}; "
                f"gh fallback failed: {gh_exc}"
            ) from exc
    except urllib.error.URLError as exc:
        try:
            return load_protection_payload_with_gh(args)
        except RuntimeError as gh_exc:
            raise RuntimeError(
                f"GitHub branch protection API request failed: {exc.reason}; gh fallback failed: {gh_exc}"
            ) from exc


def load_payload_with_gh(args: argparse.Namespace) -> dict[str, Any]:
    if args.api_url.rstrip("/") != "https://api.github.com":
        raise RuntimeError("non-default GitHub API URL is not supported by gh fallback")
    result = subprocess.run(
        ["gh", "api", f"repos/{args.repository}/branches/{args.branch}"],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "no stderr"
        raise RuntimeError(stderr)
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("gh branch API response must be a JSON object")
    return cast(dict[str, Any], payload)


def load_protection_payload_with_gh(args: argparse.Namespace) -> dict[str, Any]:
    if args.api_url.rstrip("/") != "https://api.github.com":
        raise RuntimeError("non-default GitHub API URL is not supported by gh fallback")
    result = subprocess.run(
        ["gh", "api", f"repos/{args.repository}/branches/{args.branch}/protection"],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "no stderr"
        raise RuntimeError(stderr)
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("gh branch protection API response must be a JSON object")
    return cast(dict[str, Any], payload)


def required_status_checks(payload: dict[str, Any]) -> dict[str, Any]:
    protection = payload.get("protection_details")
    if not isinstance(protection, dict):
        protection = payload.get("protection")
    if not isinstance(protection, dict):
        return {}
    checks = protection.get("required_status_checks")
    return checks if isinstance(checks, dict) else {}


def validate(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    if payload.get("protected") is not True:
        failures.append("main branch must report protected: true.")

    protection = payload.get("protection_details")
    if not isinstance(protection, dict):
        protection = payload.get("protection")
    if not isinstance(protection, dict):
        failures.append("main branch protection summary must report protection.enabled: true.")
        protection = {}
    elif "enabled" in protection and protection.get("enabled") is not True:
        failures.append("main branch protection summary must report protection.enabled: true.")

    status_checks = required_status_checks(payload)
    if status_checks.get("enforcement_level") != "everyone":
        failures.append(
            "required status checks must enforce for everyone; "
            f"got {status_checks.get('enforcement_level')!r}."
        )
    if status_checks.get("strict") is not True:
        failures.append("required status checks must require branches to be up to date.")

    raw_contexts = status_checks.get("contexts")
    if not isinstance(raw_contexts, list) or not all(isinstance(item, str) for item in raw_contexts):
        failures.append("branch summary must expose required_status_checks.contexts as a string list.")
        actual_contexts: list[str] = []
    else:
        actual_contexts = raw_contexts

    expected = set(EXPECTED_CONTEXTS)
    actual = set(actual_contexts)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"required status checks missing contexts: {', '.join(missing)}.")
    if unexpected:
        failures.append(f"required status checks include unexpected contexts: {', '.join(unexpected)}.")

    check_entries = status_checks.get("checks")
    if isinstance(check_entries, list):
        check_contexts: dict[str, object] = {}
        for item in check_entries:
            if not isinstance(item, dict):
                continue
            context = item.get("context")
            if isinstance(context, str):
                check_contexts[context] = item.get("app_id")
        if set(check_contexts) != expected:
            missing_checks = sorted(expected - set(check_contexts))
            unexpected_checks = sorted(set(check_contexts) - expected)
            if missing_checks:
                failures.append(f"required status check bindings missing contexts: {', '.join(missing_checks)}.")
            if unexpected_checks:
                failures.append(
                    f"required status check bindings include unexpected contexts: {', '.join(unexpected_checks)}."
                )
        non_actions = sorted(
            context
            for context, app_id in check_contexts.items()
            if context in expected and app_id != GITHUB_ACTIONS_APP_ID
        )
        if non_actions:
            failures.append(
                "required status checks must bind to the GitHub Actions app "
                f"({GITHUB_ACTIONS_APP_ID}); mismatched contexts: {', '.join(non_actions)}."
            )
    else:
        failures.append("branch summary must expose required_status_checks.checks bindings.")

    reviews = protection.get("required_pull_request_reviews")
    if not isinstance(reviews, dict):
        failures.append("required pull request review must be enabled.")
    else:
        if int(reviews.get("required_approving_review_count", 0)) < 1:
            failures.append("at least one approving pull request review must be required.")
        if reviews.get("dismiss_stale_reviews") is not True:
            failures.append("stale pull request reviews must be dismissed.")
        if reviews.get("require_last_push_approval") is not True:
            failures.append("last push approval must be required.")

    enforce_admins = protection.get("enforce_admins")
    if not isinstance(enforce_admins, dict) or enforce_admins.get("enabled") is not True:
        failures.append("administrator enforcement must be enabled.")

    allow_force_pushes = protection.get("allow_force_pushes")
    if not isinstance(allow_force_pushes, dict) or allow_force_pushes.get("enabled") is not False:
        failures.append("force pushes must be blocked.")

    allow_deletions = protection.get("allow_deletions")
    if not isinstance(allow_deletions, dict) or allow_deletions.get("enabled") is not False:
        failures.append("branch deletions must be blocked.")

    required_conversation_resolution = protection.get("required_conversation_resolution")
    if (
        not isinstance(required_conversation_resolution, dict)
        or required_conversation_resolution.get("enabled") is not True
    ):
        failures.append("conversation resolution must be required.")

    return failures


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Branch protection verification failed: {exc}", file=sys.stderr)
        return 1

    failures = validate(payload)
    if failures:
        print("Branch protection verification failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "Branch protection settings verification passed for "
        f"{args.repository}@{args.branch}: {', '.join(EXPECTED_CONTEXTS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
