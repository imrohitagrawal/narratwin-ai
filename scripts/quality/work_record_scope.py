"""Exact manifest scope for work-record documentation; never provider authority."""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from scripts import governance_preflight_repository as repo
from scripts.governance_preflight_v1 import validate_governance_preflight
from scripts.quality.check_phase1_closure_docs import PROCESS_ONLY_ALLOWED_CHANGED_FILES

HELPER = "scripts/quality/work_record_scope.py"
KERNEL = frozenset(
    {
        HELPER,
        "scripts/quality/phase1_closure/legacy.py",
        "tests/unit/test_work_record_scope.py",
        "tests/unit/phase1_closure/test_legacy.py",
    }
)
FAMILY = re.compile(r"phase-1-closure-process-(\d+)-.+")
DOCUMENTS = frozenset(
    p for p in PROCESS_ONLY_ALLOWED_CHANGED_FILES if p.startswith("docs/") and p.endswith(".md")
) | {"docs/THIRD_PARTY_NOTICES.md"}


class ScopeError(ValueError):
    """Fixed codes contain no source payloads or sensitive locators."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ScopeError(code)


def git(root: Path, *args: str) -> bytes:
    raw = repo._git(root, *args)
    require(raw is not None, "WRS.HISTORY_UNAVAILABLE")
    assert raw is not None
    return raw


def sha(root: Path, ref: str) -> str:
    value = git(root, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
    require(re.fullmatch("[0-9a-f]{40}", value) is not None, "WRS.HISTORY_UNAVAILABLE")
    return value


def names(root: Path, *args: str) -> set[str]:
    value = repo._paths(git(root, *args))
    require(value is not None and all(repo._valid_path(p) for p in value), "WRS.PATH_INVALID")
    assert value is not None
    return set(value)


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "WRS.DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def decode(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique)


def tree_mode(root: Path, ref: str, path: str) -> str | None:
    rows = git(root, "ls-tree", "-z", ref, "--", path).split(b"\0")
    if rows == [b""]:
        return None
    require(len(rows) == 2 and rows[-1] == b"", "WRS.FILE_TYPE")
    mode, kind, _blob = rows[0].split(b"\t")[0].split()
    require(kind == b"blob", "WRS.FILE_TYPE")
    return mode.decode()


def file_bytes(root: Path, path: str) -> bytes:
    current = root
    for part in path.split("/"):
        current = current / part
        require(not current.is_symlink(), "WRS.FILE_TYPE")
    mode = current.stat().st_mode
    require(stat.S_ISREG(mode) and not mode & 0o111, "WRS.FILE_TYPE")
    raw = current.read_bytes()
    require(b"\0" not in raw, "WRS.FILE_TYPE")
    raw.decode("utf-8")
    return raw


def charges(root: Path, base: str, target: str | None, untracked: set[str]) -> dict[str, int]:
    args = ["diff", "--numstat", "--no-renames", "-z", base]
    if target:
        args.append(target)
    rows = git(root, *args, "--").split(b"\0")
    require(rows[-1] == b"", "WRS.UNCOUNTABLE_DIFF")
    measured: dict[str, int] = {}
    for row in rows[:-1]:
        fields = row.split(b"\t", 2)
        require(
            len(fields) == 3 and fields[0].isdigit() and fields[1].isdigit(), "WRS.UNCOUNTABLE_DIFF"
        )
        path = fields[2].decode("utf-8")
        require(repo._valid_path(path) and path not in measured, "WRS.UNCOUNTABLE_DIFF")
        measured[path] = int(fields[0]) + int(fields[1])
    for path in untracked:
        require(
            path not in measured and tree_mode(root, base, path) is None, "WRS.UNCOUNTABLE_DIFF"
        )
        raw = file_bytes(root, path)
        measured[path] = raw.count(b"\n") + bool(raw and not raw.endswith(b"\n"))
    return measured


def event_identity(root: Path, branch: str, checkout: str) -> tuple[str, str, bool]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    hosted = bool(event_name) or os.environ.get("GITHUB_ACTIONS") == "true"
    require(
        not hosted or event_name in {"push", "pull_request", "pull_request_review"},
        "WRS.EVENT_INVALID",
    )
    if hosted:
        event = decode(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        if event_name == "push":
            head = event["after"]
            require(event["ref"] == "refs/heads/" + branch, "WRS.EVENT_INVALID")
            base = sha(root, "origin/main")
        else:
            pr = event["pull_request"]
            head, base = pr["head"]["sha"], pr["base"]["sha"]
            require(pr["head"]["ref"] == branch, "WRS.EVENT_INVALID")
        require(sha(root, head) == head and sha(root, base) == base, "WRS.EVENT_INVALID")
        explicit = os.environ.get("GITHUB_HEAD_SHA")
        require(not explicit or explicit == head, "WRS.EVENT_INVALID")
        require(
            not os.environ.get("GITHUB_HEAD_REF") or os.environ["GITHUB_HEAD_REF"] == branch,
            "WRS.EVENT_INVALID",
        )
        if checkout != head:
            parents = git(root, "rev-list", "--parents", "-n", "1", checkout).decode().split()[1:]
            require(event_name != "push" and parents == [base, head], "WRS.CHECKOUT_MISMATCH")
            require(
                git(root, "diff", "--name-only", head, checkout, "--") == b"",
                "WRS.CHECKOUT_MISMATCH",
            )
    else:
        head, base = checkout, sha(root, "origin/main")
        require(
            git(root, "branch", "--show-current").decode().strip() == branch, "WRS.EVENT_INVALID"
        )
    require(git(root, "merge-base", "--is-ancestor", base, head) == b"", "WRS.HISTORY_UNAVAILABLE")
    integration = git(root, "merge-base", base, head).decode().strip()
    require(integration == base, "WRS.HISTORY_UNAVAILABLE")
    require(
        tree_mode(root, base, "scripts/governance_preflight_repository.py") == "100644",
        "WRS.HISTORY_UNAVAILABLE",
    )
    return head, base, hosted


def _scope(root: Path, branch: str, issue: int) -> list[str] | None:
    checkout = sha(root, "HEAD")
    # Unrelated historical process branches keep their frozen route. Identify applicability
    # from actual file evidence, never from a self-authored manifest grant.
    main = sha(root, "origin/main")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name in {"pull_request", "pull_request_review"}:
        event = decode(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        main = sha(root, event["pull_request"]["base"]["sha"])
    paths = names(root, "diff", "--name-only", "-z", main, "--")
    paths |= names(root, "diff", "--name-only", "-z", main, checkout, "--")
    paths |= names(root, "diff", "--cached", "--name-only", "-z", main, "--")
    untracked = names(root, "ls-files", "--others", "--exclude-standard", "-z")
    paths |= untracked
    if not any(p.startswith("docs/work/") or p in KERNEL for p in paths):
        return None
    head, base, hosted = event_identity(root, branch, checkout)
    committed = names(root, "diff", "--name-only", "-z", base, head, "--")
    current = names(root, "diff", "--name-only", "-z", base, "--") | untracked
    indexed = names(root, "diff", "--cached", "--name-only", "-z", base, "--")
    artifact = f"docs/governance/preflights/issue-{issue}.json"
    findings = repo.validate_governance_preflight_repository(
        root, base_sha=base, head_sha=head, issue_number=issue, branch=branch
    )
    pending = {f.code for f in findings} == {"GPF.SCOPE.REQUIRED_NOT_CHANGED"}
    require(
        not findings or (pending and not hosted and committed == {artifact}),
        "WRS.PREFLIGHT_HISTORY",
    )
    require(tree_mode(root, head, artifact) == "100644", "WRS.FILE_TYPE")
    raw = git(root, "show", head + ":" + artifact)
    current_artifact = file_bytes(root, artifact)
    require(not hosted or raw == current_artifact, "WRS.PREFLIGHT_DIRTY")
    data = decode(current_artifact)
    core = validate_governance_preflight(
        data, context=dict(issue_number=issue, branch=branch, changed_files=sorted(current))
    )
    require(not core, "WRS.MANIFEST_INVALID")
    required = set(data["scope"]["required"])
    budget = data.get("change_budget")
    require(isinstance(budget, dict), "WRS.BUDGET_MISSING")
    require(
        set(data["scope"]["allowed_prefixes"])
        == required
        == set(budget["per_file_charged_lines"])
        == current,
        "WRS.EXACT_PATHS",
    )
    require(
        committed <= required and indexed <= required and (pending or committed == required),
        "WRS.EXACT_PATHS",
    )
    for path in indexed:
        rows = git(root, "ls-files", "-s", "-z", "--", path).split(b"\0")
        require(len(rows) == 2 and rows[-1] == b"", "WRS.FILE_TYPE")
        mode, _oid, stage = rows[0].split(b"\t")[0].split()
        require(mode == b"100644" and stage == b"0", "WRS.FILE_TYPE")
        raw_index = git(root, "show", ":" + path)
        require(b"\0" not in raw_index, "WRS.FILE_TYPE")
        raw_index.decode("utf-8")
        if path == artifact:
            index_findings = validate_governance_preflight(
                decode(raw_index),
                context=dict(issue_number=issue, branch=branch, changed_files=sorted(indexed)),
            )
            require(
                not index_findings
                or (
                    not hosted
                    and {f.code for f in index_findings} == {"GPF.SCOPE.REQUIRED_NOT_CHANGED"}
                ),
                "WRS.MANIFEST_INVALID",
            )
    require(not budget["deletions_grant_credit"], "WRS.DELETION_CREDIT")
    installed = tree_mode(root, base, HELPER) is not None
    code = required & KERNEL
    require(
        not code or (not installed and code == KERNEL and KERNEL <= current), "WRS.KERNEL_FORBIDDEN"
    )
    for path in required:
        allowed = path.startswith("docs/work/") or path in DOCUMENTS or path == artifact
        allowed |= bool(
            code and (path in KERNEL or path.startswith("docs/ADR/") and path.endswith(".md"))
        )
        require(allowed, "WRS.ENVELOPE_FORBIDDEN")
        if not pending:
            require(tree_mode(root, head, path) == "100644", "WRS.FILE_TYPE")
            raw_head = git(root, "show", head + ":" + path)
            require(b"\0" not in raw_head, "WRS.FILE_TYPE")
            raw_head.decode("utf-8")
        file_bytes(root, path)
        old_mode = tree_mode(root, base, path)
        require(old_mode in {None, "100644"}, "WRS.FILE_TYPE")
    if hosted:
        require(
            git(root, "diff", "--name-only", "HEAD", "--") == b""
            and git(root, "diff", "--cached", "--name-only", "HEAD", "--") == b""
            and not untracked,
            "WRS.HOSTED_DIRTY",
        )
    for measurement in (
        charges(root, base, head, set()),
        charges(root, base, "--cached", set()),
        charges(root, base, None, untracked),
    ):
        require(set(measurement) <= required, "WRS.EXACT_PATHS")
        require(
            all(n <= budget["per_file_charged_lines"][p] for p, n in measurement.items())
            and sum(measurement.values()) <= budget["maximum_additions_plus_deletions"],
            "WRS.LINE_BUDGET",
        )
    print("Work-record scope: " + ("COMMITTED_SCOPE_CHECK" if hosted else "WORKTREE_CHECK_ONLY"))
    return []


def scope_findings(root: Path, branch: str) -> list[str] | None:
    match = FAMILY.fullmatch(branch)
    if match is None:
        return None
    try:
        return _scope(root, branch, int(match[1]))
    except ScopeError as exc:
        return [str(exc)]
    except (OSError, ValueError, UnicodeError, KeyError, TypeError):
        return ["WRS.EVIDENCE_UNAVAILABLE"]
