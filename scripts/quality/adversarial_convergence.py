#!/usr/bin/env python3
"""Finite offline adversarial-convergence framework and Issue #435 route gate."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import TypeAlias, cast


ROOT = Path(__file__).resolve().parents[2]
ACTIVATION = "NONE"
AUTHORITY_EFFECT = "NO_AUTHORITY_EFFECT"
CORPUS_DOMAIN = b"NARRATWIN-ADVERSARIAL-CONVERGENCE-CASES-V1\0"

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class ProcessingStage(StrEnum):
    BOUNDS = "BOUNDS"
    PARSE = "PARSE"
    SCHEMA = "SCHEMA"
    CANONICAL_IDENTITY = "CANONICAL_IDENTITY"
    INDEPENDENT_TRUST = "INDEPENDENT_TRUST"
    AUTHORIZATION = "AUTHORIZATION"
    GRAPH_CONFLICT = "GRAPH_CONFLICT"
    PHASE_VERDICT = "PHASE_VERDICT"


class PhaseVerdict(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    PENDING_EXTERNAL_REVIEW = "PENDING_EXTERNAL_REVIEW"
    BLOCKED_IMPLEMENTATION = "BLOCKED_IMPLEMENTATION"
    BLOCKED_EVIDENCE = "BLOCKED_EVIDENCE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class BlockerClass(StrEnum):
    NONE = "NONE"
    IMPLEMENTATION = "IMPLEMENTATION"
    EVIDENCE = "EVIDENCE"


class MutationState(StrEnum):
    NOT_EXECUTED = "NOT_EXECUTED"
    SURVIVED = "SURVIVED"
    KILLED = "KILLED"


class ReviewDisposition(StrEnum):
    PENDING_EXTERNAL_REVIEW = "PENDING_EXTERNAL_REVIEW"
    PASS = "PASS"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class FindingCode(StrEnum):
    UNSAFE_FILESYSTEM_INPUT = "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT"
    INPUT_TOO_LARGE = "ACP.BOUNDS.INPUT_TOO_LARGE"
    RESOURCE_UNAVAILABLE = "ACP.BOUNDS.RESOURCE_UNAVAILABLE"
    INVALID_UTF8 = "ACP.PARSE.INVALID_UTF8"
    MALFORMED_JSON = "ACP.PARSE.MALFORMED_JSON"
    DUPLICATE_MEMBER = "ACP.PARSE.DUPLICATE_MEMBER"
    RESOURCE_LIMIT = "ACP.PARSE.RESOURCE_LIMIT"
    SCHEMA_DRIFT = "ACP.SCHEMA.DRIFT"
    CLOSED_UNIVERSE = "ACP.SCHEMA.CLOSED_UNIVERSE"
    NON_CANONICAL = "ACP.IDENTITY.NON_CANONICAL"
    IDENTITY_MISMATCH = "ACP.IDENTITY.MISMATCH"
    EXPECTATION_NOT_INDEPENDENT = "ACP.TRUST.EXPECTATION_NOT_INDEPENDENT"
    MOCK_LEDGER_INVALID = "ACP.TRUST.MOCK_LEDGER_INVALID"
    REVIEW_SELF_ATTESTED = "ACP.TRUST.REVIEW_SELF_ATTESTED"
    REVIEW_IDENTITY_MISMATCH = "ACP.TRUST.REVIEW_IDENTITY_MISMATCH"
    ROUTE_DRIFT = "ACP.AUTH.ROUTE_DRIFT"
    BUDGET_REVIEW_REQUIRED = "ACP.AUTH.BUDGET_REVIEW_REQUIRED"
    BUDGET_STOP = "ACP.AUTH.BUDGET_STOP"
    AUTHORITY_DRIFT = "ACP.AUTH.AUTHORITY_DRIFT"
    PREDECESSOR_VIOLATION = "ACP.PIPELINE.PREDECESSOR_VIOLATION"
    LATE_STAGE_EXECUTION = "ACP.PIPELINE.LATE_STAGE_EXECUTION"
    INELIGIBLE_CANDIDATE = "ACP.GRAPH.INELIGIBLE_CANDIDATE"
    CONFLICT_PRECEDENCE = "ACP.GRAPH.CONFLICT_PRECEDENCE"
    OUTCOME_NOT_EXACT = "ACP.VERDICT.OUTCOME_NOT_EXACT"
    SUBSET_OUTCOME = "ACP.VERDICT.SUBSET_OUTCOME"
    MUTANT_NOT_EXECUTED = "ACP.VERDICT.MUTANT_NOT_EXECUTED"
    MUTANT_SURVIVED = "ACP.VERDICT.MUTANT_SURVIVED"
    REQUIRED_REVIEW_MISSING = "ACP.VERDICT.REQUIRED_REVIEW_MISSING"
    CHECKPOINT_INVALID = "ACP.VERDICT.CHECKPOINT_INVALID"
    PLATFORM_FAILURE = "ACP.VERDICT.PLATFORM_FAILURE"
    RESOURCE_FAILURE = "ACP.VERDICT.RESOURCE_FAILURE"
    NOT_IMPLEMENTED = "ACP.NOT_IMPLEMENTED"


@dataclass(frozen=True)
class Stimulus:
    operation: str
    variant: str
    input: JsonValue = None


@dataclass(frozen=True)
class Finding:
    stage: ProcessingStage
    code: FindingCode
    location: str
    blocker: BlockerClass


@dataclass(frozen=True)
class StageObservation:
    stage: ProcessingStage
    state: str
    callback_count: int
    justification: str
    finding_codes: tuple[FindingCode, ...]


@dataclass(frozen=True)
class MutationReceipt:
    mutant_id: str
    test_id: str
    executed_count: int
    state: MutationState
    observed_finding: FindingCode
    observed_verdict: PhaseVerdict


@dataclass(frozen=True)
class ReviewReceipt:
    role: str
    reviewer: str
    head: str
    tree: str
    disposition: ReviewDisposition
    source: str


@dataclass(frozen=True)
class ValidationResult:
    verdict: PhaseVerdict
    findings: tuple[Finding, ...]
    observations: tuple[StageObservation, ...]
    mutation_receipts: tuple[MutationReceipt, ...]
    activation: str = ACTIVATION
    authority_effect: str = AUTHORITY_EFFECT


@dataclass(frozen=True)
class ParseLimits:
    max_bytes: int = 65_536
    max_depth: int = 32
    max_members: int = 4_096


@dataclass(frozen=True)
class BoundaryResult:
    data: bytes | None
    finding: Finding | None


@dataclass(frozen=True)
class ParseResult:
    document: JsonValue | None
    findings: tuple[Finding, ...]
    semantic_sha256: str


class DuplicateMemberError(ValueError):
    """Raised by the strict JSON hook before a duplicate can be overwritten."""


def _finding(
    code: FindingCode,
    stage: ProcessingStage,
    location: str,
    blocker: BlockerClass = BlockerClass.IMPLEMENTATION,
) -> Finding:
    return Finding(stage=stage, code=code, location=location, blocker=blocker)


def _valid_relative_path(relative: str) -> bool:
    path = PurePosixPath(relative)
    return bool(relative) and not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _open_regular_descriptor(root: Path, relative: str) -> tuple[int, os.stat_result] | None:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory or not _valid_relative_path(relative):
        return None
    descriptors: list[int] = []
    try:
        parent = os.open(root, os.O_RDONLY | directory | nofollow)
        descriptors.append(parent)
        parts = PurePosixPath(relative).parts
        for component in parts[:-1]:
            parent = os.open(component, os.O_RDONLY | directory | nofollow, dir_fd=parent)
            descriptors.append(parent)
        target = os.open(parts[-1], os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0), dir_fd=parent)
        opened = os.fstat(target)
        current = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            os.close(target)
            return None
        return target, opened
    except OSError:
        return None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def read_bounded_regular_file(root: Path, relative: str, max_bytes: int) -> BoundaryResult:
    opened = _open_regular_descriptor(root, relative)
    if opened is None:
        return BoundaryResult(None, _finding(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, relative))
    descriptor, before = opened
    try:
        if max_bytes < 1 or before.st_size > max_bytes:
            return BoundaryResult(None, _finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, relative))
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(data) > max_bytes:
            return BoundaryResult(None, _finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, relative))
        if (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, len(data)):
            return BoundaryResult(None, _finding(FindingCode.RESOURCE_UNAVAILABLE, ProcessingStage.BOUNDS, relative))
        return BoundaryResult(data, None)
    except OSError:
        return BoundaryResult(None, _finding(FindingCode.RESOURCE_FAILURE, ProcessingStage.BOUNDS, relative))
    finally:
        os.close(descriptor)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateMemberError(key)
        result[key] = value
    return result


def _normalize_json(value: object, depth: int, limits: ParseLimits) -> tuple[JsonValue, int]:
    if depth > limits.max_depth:
        raise RecursionError
    if value is None or isinstance(value, str | bool | int | float):
        return value, 1
    if isinstance(value, list):
        normalized: list[JsonValue] = []
        members = 1
        for item in cast(list[object], value):
            child, count = _normalize_json(item, depth + 1, limits)
            normalized.append(child)
            members += count
        if members > limits.max_members:
            raise OverflowError
        return normalized, members
    if isinstance(value, dict):
        normalized_object: dict[str, JsonValue] = {}
        members = 1
        for key, item in cast(dict[str, object], value).items():
            child, count = _normalize_json(item, depth + 1, limits)
            normalized_object[key] = child
            members += count
        if members > limits.max_members:
            raise OverflowError
        return normalized_object, members
    raise TypeError


def parse_json_bytes(raw: bytes, expected_sha256: str, limits: ParseLimits = ParseLimits()) -> ParseResult:
    if len(raw) > limits.max_bytes:
        finding = _finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, "/")
        return ParseResult(None, (finding,), "")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        finding = _finding(FindingCode.IDENTITY_MISMATCH, ProcessingStage.CANONICAL_IDENTITY, "/")
        return ParseResult(None, (finding,), "")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        finding = _finding(FindingCode.INVALID_UTF8, ProcessingStage.PARSE, "/")
        return ParseResult(None, (finding,), "")
    try:
        parsed: object = json.loads(text, object_pairs_hook=_strict_object)
        document, _ = _normalize_json(parsed, 1, limits)
        canonical = json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    except DuplicateMemberError:
        finding = _finding(FindingCode.DUPLICATE_MEMBER, ProcessingStage.PARSE, "/")
        return ParseResult(None, (finding,), "")
    except json.JSONDecodeError:
        finding = _finding(FindingCode.MALFORMED_JSON, ProcessingStage.PARSE, "/")
        return ParseResult(None, (finding,), "")
    except (OverflowError, RecursionError, TypeError, ValueError):
        finding = _finding(FindingCode.RESOURCE_LIMIT, ProcessingStage.PARSE, "/")
        return ParseResult(None, (finding,), "")
    return ParseResult(document, (), hashlib.sha256(CORPUS_DOMAIN + canonical).hexdigest())


def execute(stimulus: Stimulus) -> ValidationResult:
    """C2 boundary: C4 replaces only this NOT_IMPLEMENTED executor."""
    del stimulus
    finding = _finding(FindingCode.NOT_IMPLEMENTED, ProcessingStage.PHASE_VERDICT, "/")
    return ValidationResult(PhaseVerdict.NOT_IMPLEMENTED, (finding,), (), ())


# ISSUE435_ROUTE_ADAPTER_V1_START
ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"
ISSUE435_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
ISSUE435_C1 = "205c02b3bac633d023d753356bc966c194ed36a7"
ISSUE435_PREFLIGHT = "docs/governance/preflights/issue-435.json"
ISSUE435_PREFLIGHT_BLOB = "c554eaf7f73ea081434b1e2f818441fe0bc3eee9"
ISSUE435_FREEZE = "docs/governance/adversarial-convergence-red-freeze-v1.json"
ISSUE435_CAPS = {
    "docs/governance/preflights/issue-435.json": 220,
    "AGENTS.md": 45,
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md": 320,
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md": 180,
    "docs/governance/adversarial-convergence-framework-v1.schema.json": 260,
    "docs/governance/adversarial-convergence-framework-cases-v1.json": 300,
    "docs/governance/adversarial-convergence-red-freeze-v1.json": 120,
    "scripts/quality/adversarial_convergence.py": 600,
    "tests/unit/test_adversarial_convergence.py": 760,
    "scripts/quality/check_quality_stage.py": 60,
    "tests/unit/test_quality_dispatcher.py": 100,
    "scripts/guardrails_check.py": 60,
    "tests/unit/test_guardrails_check.py": 140,
    ".github/pull_request_template.md": 45,
    "docs/ADR/0064-adversarial-convergence-protocol.md": 160,
    "docs/QUALITY_GATES.md": 80,
    "docs/ENGINEERING_PROCESS_RCA.md": 80,
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 100,
    "docs/STAGE_ISSUE_PLAN.md": 70,
    "docs/STATUS.md": 80,
}
ISSUE435_NONFREEZE = frozenset(ISSUE435_CAPS) - {ISSUE435_FREEZE}


@dataclass(frozen=True)
class PathCharge:
    path: str
    status: str
    additions: int
    deletions: int
    mode: str


@dataclass(frozen=True)
class RouteEvidence:
    branch: str
    ancestor: bool
    first_commit: str
    merge_commits: tuple[str, ...]
    preflight_blob: str
    changes: tuple[PathCharge, ...]
    dirty: bool
    freeze_present: bool


@dataclass(frozen=True)
class RouteInspection:
    phase: str
    findings: tuple[FindingCode, ...]
    charged_lines: int


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


def validate_route_evidence(evidence: RouteEvidence) -> RouteInspection:
    findings: list[FindingCode] = []
    exact_paths = frozenset(ISSUE435_CAPS) if evidence.freeze_present else ISSUE435_NONFREEZE
    actual_paths = frozenset(change.path for change in evidence.changes)
    charged = sum(change.additions + change.deletions for change in evidence.changes)
    if evidence.branch != ISSUE435_BRANCH or not evidence.ancestor or evidence.first_commit != ISSUE435_C1:
        findings.append(FindingCode.IDENTITY_MISMATCH)
    if evidence.merge_commits or evidence.preflight_blob != ISSUE435_PREFLIGHT_BLOB or evidence.dirty:
        findings.append(FindingCode.ROUTE_DRIFT)
    if actual_paths != exact_paths:
        findings.append(FindingCode.ROUTE_DRIFT)
    if any(change.status not in {"A", "M"} or change.mode != "100644" for change in evidence.changes):
        findings.append(FindingCode.ROUTE_DRIFT)
    if any(change.additions + change.deletions > ISSUE435_CAPS.get(change.path, -1) for change in evidence.changes):
        findings.append(FindingCode.BUDGET_STOP)
    hard_cap = 3_620 if evidence.freeze_present else 3_500
    if charged > hard_cap:
        findings.append(FindingCode.BUDGET_STOP)
    phase = "C3_OR_C4" if evidence.freeze_present else "C2"
    return RouteInspection(phase, tuple(dict.fromkeys(findings)), charged)


def _git(root: Path, *args: str) -> GitResult:
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"}
    try:
        result = subprocess.run(["/usr/bin/git", *args], cwd=root, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as error:
        return GitResult(128, "", type(error).__name__)
    return GitResult(result.returncode, result.stdout, result.stderr)


def _collect_changes(root: Path, head: str) -> tuple[PathCharge, ...] | None:
    names = _git(root, "diff", "--name-status", "--find-renames", "--find-copies", "--find-copies-harder", ISSUE435_BASE, head, "--")
    numbers = _git(root, "diff", "--numstat", "--no-renames", ISSUE435_BASE, head, "--")
    if names.returncode or numbers.returncode:
        return None
    statuses: dict[str, str] = {}
    for line in names.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in {"A", "M"} or fields[1] in statuses:
            return None
        statuses[fields[1]] = fields[0]
    charges: list[PathCharge] = []
    for line in numbers.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            return None
        additions, deletions, path = int(fields[0]), int(fields[1]), fields[2]
        tree = _git(root, "ls-tree", head, "--", path)
        tree_fields = tree.stdout.split()
        if path not in statuses or len(tree_fields) < 3:
            return None
        charges.append(PathCharge(path, statuses[path], additions, deletions, tree_fields[0]))
    return tuple(charges) if set(statuses) == {change.path for change in charges} else None


def inspect_issue435_repository(root: Path, branch: str) -> RouteInspection:
    head_result = _git(root, "rev-parse", "HEAD")
    if head_result.returncode:
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    head = head_result.stdout.strip()
    history = _git(root, "rev-list", "--reverse", f"{ISSUE435_BASE}..{head}")
    merges = _git(root, "rev-list", "--min-parents=2", f"{ISSUE435_BASE}..{head}")
    ancestor = _git(root, "merge-base", "--is-ancestor", ISSUE435_BASE, head).returncode == 0
    blob = _git(root, "rev-parse", f"{head}:{ISSUE435_PREFLIGHT}")
    dirty = bool(_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    changes = _collect_changes(root, head)
    if history.returncode or merges.returncode or blob.returncode or changes is None:
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    commits = tuple(history.stdout.splitlines())
    evidence = RouteEvidence(
        branch=branch,
        ancestor=ancestor,
        first_commit=commits[0] if commits else "",
        merge_commits=tuple(merges.stdout.splitlines()),
        preflight_blob=blob.stdout.strip(),
        changes=changes,
        dirty=dirty,
        freeze_present=ISSUE435_FREEZE in {change.path for change in changes},
    )
    return validate_route_evidence(evidence)


def issue435_branch_kind(branch: str) -> str:
    if branch == ISSUE435_BRANCH:
        return "EXACT"
    if branch.startswith("governance-435"):
        return "LOOKALIKE"
    return "UNRELATED"


# ISSUE435_ROUTE_ADAPTER_V1_END
def _current_branch(root: Path) -> str:
    event_branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    git_branch = _git(root, "branch", "--show-current").stdout.strip()
    if event_branch and git_branch and event_branch != git_branch:
        return ""
    return event_branch or git_branch
def _json_output(kind: str, code: FindingCode, phase: str) -> str:
    return json.dumps(
        {"activation": ACTIVATION, "authorityEffect": AUTHORITY_EFFECT, "code": code, "kind": kind, "phase": phase, "reviewState": ReviewDisposition.PENDING_EXTERNAL_REVIEW},
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> int:
    branch = _current_branch(ROOT)
    if not branch:
        print(_json_output("INFRASTRUCTURE_FAILURE", FindingCode.PLATFORM_FAILURE, "UNKNOWN"))
        return 2
    inspection = inspect_issue435_repository(ROOT, branch)
    if inspection.findings:
        code = inspection.findings[0]
        kind = "INFRASTRUCTURE_FAILURE" if code in {FindingCode.PLATFORM_FAILURE, FindingCode.RESOURCE_FAILURE} else "CONTRACT_FAILURE"
        print(_json_output(kind, code, inspection.phase))
        return 2 if kind == "INFRASTRUCTURE_FAILURE" else 1
    result = execute(Stimulus(operation="framework_gate", variant="c2_boundary"))
    print(_json_output("INTENTIONAL_RED", result.findings[0].code, inspection.phase))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
