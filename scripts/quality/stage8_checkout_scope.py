"""Validate source-head and same-tree hosted merge checkouts before measuring scope."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable


def changed_files(
    run: Callable[[list[str]], Any],
    parse_name_status_z: Callable[[str], list[str]],
    parse_paths_z: Callable[[str], list[str]],
    null_git_sha: str,
    routes: Any,
) -> list[str]:
    head_result = run(["git", "rev-parse", "HEAD"])
    if head_result.returncode != 0 or not head_result.stdout.strip():
        raise RuntimeError(head_result.stderr.strip() or "git rev-parse HEAD failed")
    head = head_result.stdout.strip()
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    expected_head = os.environ.get("GITHUB_HEAD_SHA", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if event_path and event_name in {"pull_request", "pull_request_review", "push"}:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            event_head = (
                payload["after"] if event_name == "push" else payload["pull_request"]["head"]["sha"]
            )
        except (KeyError, OSError, TypeError, ValueError) as error:
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.") from error
        if not isinstance(event_head, str) or not event_head.strip():
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
        if expected_head and expected_head != event_head.strip():
            raise RuntimeError("GitHub exact head evidence contradicts GITHUB_HEAD_SHA.")
        expected_head = event_head.strip()
    if not expected_head and event_name in {"pull_request", "pull_request_review", "push"}:
        raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
    if expected_head:
        expected_result = run(["git", "rev-parse", f"{expected_head}^{{commit}}"])
        if expected_result.returncode != 0 or not expected_result.stdout.strip():
            raise RuntimeError(expected_result.stderr.strip() or "git rev-parse exact head failed")
        if expected_result.stdout.strip() != head:
            parents = run(["git", "rev-list", "--parents", "-n", "1", head])
            base = os.environ.get("GITHUB_BASE_SHA", "").strip()
            if event_path and event_name in {"pull_request", "pull_request_review"}:
                try:
                    event_base = payload["pull_request"]["base"]["sha"]
                except (KeyError, TypeError) as error:
                    raise RuntimeError(
                        "Stage 8 exact head merge base evidence unavailable."
                    ) from error
                if base and base != event_base:
                    raise RuntimeError("Stage 8 merge base contradicts the event.")
                base = event_base
            same_tree = run(["git", "diff", "--quiet", expected_result.stdout.strip(), head, "--"])
            if (
                event_name not in {"pull_request", "pull_request_review"}
                or parents.returncode
                or parents.stdout.split() != [head, base, expected_result.stdout.strip()]
                or same_tree.returncode
            ):
                raise RuntimeError("Stage 8 scope checkout does not match the exact head.")
            head = expected_result.stdout.strip()
    b = os.environ.get("GITHUB_BASE_SHA", "").strip()
    r = os.environ.get("NARRATWIN_HEAD_REF", os.environ.get("GITHUB_REF_NAME", "")).strip()
    f = (event_name == "push" and r != "main") or not b or b == null_git_sha
    candidates = (
        [routes.ISSUE459_TRANSITION_BASE]
        if event_name == "push" and r == routes.ISSUE459_BRANCH
        else ["origin/main", "main"]
        if f
        else [b]
    )
    merge_base = ""
    last_error = ""
    for candidate in candidates:
        result = run(["git", "merge-base", candidate, head])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
        last_error = result.stderr.strip()
    if not merge_base:
        raise RuntimeError(last_error or "git merge-base failed for Stage 8 scope.")
    diff_flags = ["--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"]
    paths: list[str] = []
    for args in (
        ["git", "diff", *diff_flags, f"{merge_base}..{head}", "--"],
        ["git", "diff", "--cached", *diff_flags, head, "--"],
        ["git", "diff", *diff_flags, "--"],
    ):
        result = run(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
        paths.extend(parse_name_status_z(result.stdout))
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files failed")
    paths.extend(parse_paths_z(untracked.stdout))
    return sorted(set(paths))
