"""Pure, fail-closed PR-body live-state reconciliation primitives.

The module deliberately accepts GitHub data as data, never as shell/template input.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol, cast

START = "<!-- narratwin-live-state:start -->"
END = "<!-- narratwin-live-state:end -->"
MAX_BODY_BYTES = 65_536
SHA = re.compile(r"^[0-9a-f]{40}$")
ESCAPED = re.compile(r"(?<!\\)\\[nrt]")
PLACEHOLDER = re.compile(r"(?i)\b(?:todo|tbd|replace me|add text here)\b|<[^>\n]{1,80}>")
PRIVATE_PATH = re.compile(r"(?:(?:/Users|/home|/private|[A-Za-z]:\\\\)[^\s`]+)")
SENSITIVE_EVIDENCE_PATTERN = re.compile(r"(?i)(?:authorization:\s*bearer|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")


class DuplicateJsonKey(ValueError):
    """JSON duplicate keys are ambiguous and therefore rejected."""


class HeadChanged(RuntimeError):
    """The PR changed between deterministic calculation and mutation."""


def decode_json(raw: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonKey(key)
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


@dataclass(frozen=True)
class LiveState:
    repository: str
    number: int
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    changed_files: int
    additions: int
    deletions: int
    draft: bool
    state: str

    @property
    def charged_lines(self) -> int:
        return self.additions + self.deletions

    @classmethod
    def from_pull(cls, repository: str, pull: dict[str, Any]) -> "LiveState":
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("unexpected repository")
        base, head = pull.get("base"), pull.get("head")
        values = (pull.get("number"), pull.get("state"), pull.get("draft"), base, head)
        if not isinstance(values[0], int) or isinstance(values[0], bool) or not isinstance(values[1], str) or not isinstance(values[2], bool):
            raise ValueError("malformed PR identity")
        if not isinstance(base, dict) or not isinstance(head, dict):
            raise ValueError("malformed PR refs")
        fields = (base.get("ref"), base.get("sha"), head.get("ref"), head.get("sha"))
        if not all(isinstance(item, str) and item for item in fields) or not SHA.fullmatch(base["sha"]) or not SHA.fullmatch(head["sha"]):
            raise ValueError("malformed PR SHA")
        changed_files, additions, deletions = pull.get("changed_files"), pull.get("additions"), pull.get("deletions")
        if any(type(item) is not int or item < 0 for item in (changed_files, additions, deletions)):
            raise ValueError("malformed PR counts")
        changed_files = cast(int, changed_files)
        additions = cast(int, additions)
        deletions = cast(int, deletions)
        return cls(repository, pull["number"], base["ref"], base["sha"], head["ref"], head["sha"], changed_files, additions, deletions, pull["draft"], pull["state"])


def managed_block(state: LiveState) -> str:
    """Render byte-stable facts; ordering is part of the contract."""
    rows = (
        START,
        "<!-- automation-owned: do not edit; run make pr-reconcile PR=<number> -->",
        "```text",
        "schema_version: 1",
        f"repository: {state.repository}",
        f"pr_number: {state.number}",
        f"base_ref: {state.base_ref}",
        f"base_sha: {state.base_sha}",
        f"head_ref: {state.head_ref}",
        f"head_sha: {state.head_sha}",
        f"changed_files: {state.changed_files}",
        f"additions: {state.additions}",
        f"deletions: {state.deletions}",
        f"charged_lines: {state.charged_lines}",
        f"draft: {str(state.draft).lower()}",
        f"state: {state.state}",
        "```",
        END,
    )
    return "\n".join(rows)


def _block_span(body: str) -> tuple[int, int] | None:
    starts, ends = [m.start() for m in re.finditer(re.escape(START), body)], [m.start() for m in re.finditer(re.escape(END), body)]
    if len(starts) != 1 or len(ends) != 1 or (starts and starts[0] >= ends[0]):
        return None
    return starts[0], ends[0] + len(END)


def validate_body(body: str, state: LiveState) -> list[str]:
    failures: list[str] = []
    if not isinstance(body, str) or len(body.encode("utf-8", errors="surrogatepass")) > MAX_BODY_BYTES:
        return ["PR body is missing or exceeds the safe size limit."]
    span = _block_span(body)
    if span is None:
        failures.append("Managed-block markers must appear exactly once in start-before-end order.")
    elif body[span[0] : span[1]] != managed_block(state):
        failures.append("Managed live-state metadata does not match current GitHub state.")
    human_text = body if span is None else body[: span[0]] + body[span[1] :]
    if ESCAPED.search(human_text):
        failures.append("PR body contains literal escaped formatting.")
    if PLACEHOLDER.search(human_text):
        failures.append("PR body contains unresolved template placeholder or instruction.")
    if PRIVATE_PATH.search(human_text) or SENSITIVE_EVIDENCE_PATTERN.search(human_text):
        failures.append("PR body contains private path or credential-like evidence.")
    for heading in ("## Reviewer overview", "## Product and reviewer context"):
        if len(re.findall(rf"(?mi)^\s*{re.escape(heading)}\s*$", body)) != 1:
            failures.append(f"PR body must contain exactly one {heading[3:]} section.")
    return failures


@dataclass(frozen=True)
class ReconcileResult:
    body: str
    changed: bool


def reconcile(body: str, state: LiveState) -> ReconcileResult:
    if not isinstance(body, str) or len(body.encode("utf-8", errors="surrogatepass")) > MAX_BODY_BYTES:
        raise ValueError("unsafe PR body")
    span = _block_span(body)
    if span is None:
        raise ValueError("managed block must be unique and well formed")
    replacement = managed_block(state)
    updated = body[: span[0]] + replacement + body[span[1] :]
    return ReconcileResult(updated, updated != body)


class PullApi(Protocol):
    def pull(self, number: int) -> dict[str, Any]: ...
    def update_body(self, number: int, body: str) -> None: ...


def apply(api: PullApi, repository: str, number: int) -> ReconcileResult:
    source = api.pull(number)
    state = LiveState.from_pull(repository, source)
    result = reconcile(str(source.get("body") or ""), state)
    latest = LiveState.from_pull(repository, api.pull(number))
    if latest.head_sha != state.head_sha:
        raise HeadChanged("head changed before update")
    if not result.changed:
        return result
    api.update_body(number, result.body)
    stored = api.pull(number)
    stored_state = LiveState.from_pull(repository, stored)
    if stored_state.head_sha != state.head_sha or stored.get("body") != result.body:
        raise HeadChanged("stored PR body could not be verified at the expected head")
    return result
