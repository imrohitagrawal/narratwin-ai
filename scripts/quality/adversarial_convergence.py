#!/usr/bin/env python3
"""Finite offline adversarial-convergence worker and fail-closed route inspector."""
from __future__ import annotations
import hashlib
import json
import os
import select
import stat
import subprocess
import sys
import time
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple, TypeAlias, cast
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
class StageState(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_REACHED = "NOT_REACHED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
class PhaseVerdict(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    BLOCKED_IMPLEMENTATION = "BLOCKED_IMPLEMENTATION"
    BLOCKED_EVIDENCE = "BLOCKED_EVIDENCE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
class BlockerClass(StrEnum):
    IMPLEMENTATION = "IMPLEMENTATION"
    EVIDENCE = "EVIDENCE"
class MutationState(StrEnum):
    NOT_EXECUTED = "NOT_EXECUTED"
    SURVIVED = "SURVIVED"
    KILLED = "KILLED"

class FindingCode(StrEnum):
    UNSAFE_FILESYSTEM_INPUT = "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT"
    INPUT_TOO_LARGE = "ACP.BOUNDS.INPUT_TOO_LARGE"
    INVALID_UTF8 = "ACP.PARSE.INVALID_UTF8"
    MALFORMED_JSON = "ACP.PARSE.MALFORMED_JSON"
    DUPLICATE_MEMBER = "ACP.PARSE.DUPLICATE_MEMBER"
    RESOURCE_LIMIT = "ACP.PARSE.RESOURCE_LIMIT"
    SCHEMA_DRIFT = "ACP.SCHEMA.DRIFT"
    IDENTITY_MISMATCH = "ACP.IDENTITY.MISMATCH"
    EXPECTATION_NOT_INDEPENDENT = "ACP.TRUST.EXPECTATION_NOT_INDEPENDENT"
    MOCK_LEDGER_INVALID = "ACP.TRUST.MOCK_LEDGER_INVALID"
    REVIEW_SELF_ATTESTED = "ACP.TRUST.REVIEW_SELF_ATTESTED"
    REVIEW_IDENTITY_MISMATCH = "ACP.TRUST.REVIEW_IDENTITY_MISMATCH"
    ROUTE_DRIFT = "ACP.AUTH.ROUTE_DRIFT"
    BUDGET_REVIEW_REQUIRED = "ACP.AUTH.BUDGET_REVIEW_REQUIRED"
    BUDGET_STOP = "ACP.AUTH.BUDGET_STOP"
    PREDECESSOR_VIOLATION = "ACP.PIPELINE.PREDECESSOR_VIOLATION"
    LATE_STAGE_EXECUTION = "ACP.PIPELINE.LATE_STAGE_EXECUTION"
    OUTCOME_NOT_EXACT = "ACP.VERDICT.OUTCOME_NOT_EXACT"
    SUBSET_OUTCOME = "ACP.VERDICT.SUBSET_OUTCOME"
    MUTANT_NOT_EXECUTED = "ACP.VERDICT.MUTANT_NOT_EXECUTED"
    MUTANT_SURVIVED = "ACP.VERDICT.MUTANT_SURVIVED"
    REQUIRED_REVIEW_MISSING = "ACP.VERDICT.REQUIRED_REVIEW_MISSING"
    CHECKPOINT_INVALID = "ACP.VERDICT.CHECKPOINT_INVALID"
    PLATFORM_FAILURE = "ACP.VERDICT.PLATFORM_FAILURE"
    RESOURCE_FAILURE = "ACP.VERDICT.RESOURCE_FAILURE"
    NOT_IMPLEMENTED = "ACP.NOT_IMPLEMENTED"

Stimulus = NamedTuple("Stimulus", [("kind", str), ("payload", dict[str, JsonValue])])
Finding = NamedTuple("Finding", [("stage", ProcessingStage), ("code", FindingCode), ("location", str), ("blocker", BlockerClass)])
StageObservation = NamedTuple("StageObservation", [("stage", ProcessingStage), ("state", StageState), ("callback_count", int), ("justification", str), ("finding_codes", tuple[FindingCode, ...])])
ExecutionReceipt = NamedTuple("ExecutionReceipt", [("candidate", str), ("ordinal", int), ("phase", str), ("stage", ProcessingStage), ("callback_count", int), ("observed_state", StageState), ("observed_finding_codes", tuple[FindingCode, ...])])
MutationReceipt = NamedTuple("MutationReceipt", [("mutant_id", str), ("assertion_id", str), ("execution_count", int), ("failure_count", int), ("state", MutationState), ("observed_verdict", PhaseVerdict), ("observed_finding_codes", tuple[FindingCode, ...])])
ValidationResult = NamedTuple("ValidationResult", [("verdict", PhaseVerdict), ("findings", tuple[Finding, ...]), ("observations", tuple[StageObservation, ...]), ("execution_receipts", tuple[ExecutionReceipt, ...]), ("mutation_receipts", tuple[MutationReceipt, ...]), ("activation", str), ("authority_effect", str)])

ParseLimits = NamedTuple("ParseLimits", [("max_bytes", int), ("max_depth", int), ("max_members", int)])
DEFAULT_PARSE_LIMITS = ParseLimits(65_536, 32, 4_096)

BoundaryResult = NamedTuple("BoundaryResult", [("data", bytes | None), ("finding", Finding | None)])
ParseResult = NamedTuple("ParseResult", [("document", JsonValue | None), ("findings", tuple[Finding, ...]), ("semantic_sha256", str)])
GitResult = NamedTuple("GitResult", [("state", str), ("returncode", int), ("stdout", bytes), ("stderr", bytes)])
RouteInspection = NamedTuple("RouteInspection", [("phase", str), ("findings", tuple[FindingCode, ...]), ("charged_lines", int)])
PathCharge = NamedTuple("PathCharge", [("path", str), ("status", str), ("additions", int), ("deletions", int), ("mode", str)])

def _finding(
    code: FindingCode,
    stage: ProcessingStage,
    location: str,
    blocker: BlockerClass = BlockerClass.IMPLEMENTATION,
) -> Finding:
    return Finding(stage, code, location, blocker)

def _valid_relative_path(relative: str) -> bool:
    if not relative or len(relative) > 512 or relative.startswith(("/", "~")):
        return False
    if "\\" in relative or any(ord(character) < 32 or ord(character) == 127 for character in relative):
        return False
    parts = relative.split("/")
    return len(parts) <= 64 and all(part not in {"", ".", ".."} for part in parts)

def _safe_close(descriptor: int) -> None:
    try:
        os.close(descriptor)
    except OSError:
        pass

def _open_regular_descriptor(root: Path, relative: str) -> tuple[int, os.stat_result, int, str] | None:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory or not _valid_relative_path(relative):
        return None
    parents: list[int] = []
    try:
        parent = os.open(root, os.O_RDONLY | directory | nofollow)
        parents.append(parent)
        parts = relative.split("/")
        for component in parts[:-1]:
            parent = os.open(component, os.O_RDONLY | directory | nofollow, dir_fd=parent)
            parents.append(parent)
        target = os.open(parts[-1], os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0), dir_fd=parent)
        opened = os.fstat(target)
        current = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino) == (current.st_dev, current.st_ino):
            parents.pop()
            return target, opened, parent, parts[-1]
        _safe_close(target)
    except (OSError, ValueError, OverflowError, MemoryError):
        return None
    finally:
        for descriptor in reversed(parents):
            _safe_close(descriptor)
    return None

def read_bounded_regular_file(root: Path, relative: str, max_bytes: int) -> BoundaryResult:
    opened = _open_regular_descriptor(root, relative)
    if opened is None:
        return BoundaryResult(None, _finding(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, relative))
    descriptor, before, parent, leaf = opened
    try:
        if max_bytes < 1 or before.st_size > max_bytes:
            return BoundaryResult(None, _finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, relative))
        data = bytearray()
        while len(data) <= max_bytes:
            chunk = os.read(descriptor, min(65_536, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        after = os.fstat(descriptor)
        current = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        observed = (after.st_dev, after.st_ino, len(data), after.st_mtime_ns, after.st_ctime_ns)
        if len(data) > max_bytes:
            return BoundaryResult(None, _finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, relative))
        if identity != observed or (after.st_dev, after.st_ino) != (current.st_dev, current.st_ino):
            return BoundaryResult(None, _finding(FindingCode.RESOURCE_FAILURE, ProcessingStage.BOUNDS, relative))
        return BoundaryResult(bytes(data), None)
    except (OSError, ValueError, OverflowError, MemoryError):
        return BoundaryResult(None, _finding(FindingCode.RESOURCE_FAILURE, ProcessingStage.BOUNDS, relative))
    finally:
        _safe_close(descriptor)
        _safe_close(parent)

def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise KeyError(key)
        result[key] = value
    return result

def _normalize_json(value: object, depth: int, limits: ParseLimits) -> tuple[JsonValue, int]:
    if depth > limits.max_depth:
        raise RecursionError
    if value is None or isinstance(value, str | bool | int | float):
        return value, 1
    if isinstance(value, list):
        children = [_normalize_json(item, depth + 1, limits) for item in cast(list[object], value)]
        count = 1 + sum(child_count for _, child_count in children)
        if count > limits.max_members:
            raise OverflowError
        return [child for child, _ in children], count
    if isinstance(value, dict):
        children_by_key = {key: _normalize_json(item, depth + 1, limits) for key, item in cast(dict[str, object], value).items()}
        count = 1 + sum(child_count for _, child_count in children_by_key.values())
        if count > limits.max_members:
            raise OverflowError
        return {key: child for key, (child, _) in children_by_key.items()}, count
    raise TypeError

def parse_json_bytes(raw: bytes, expected_sha256: str, limits: ParseLimits = DEFAULT_PARSE_LIMITS) -> ParseResult:
    if len(raw) > limits.max_bytes:
        return ParseResult(None, (_finding(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, "/"),), "")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        return ParseResult(None, (_finding(FindingCode.IDENTITY_MISMATCH, ProcessingStage.CANONICAL_IDENTITY, "/"),), "")
    try:
        parsed: object = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
        document, _ = _normalize_json(parsed, 1, limits)
        canonical = json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    except UnicodeError:
        return ParseResult(None, (_finding(FindingCode.INVALID_UTF8, ProcessingStage.PARSE, "/"),), "")
    except KeyError:
        return ParseResult(None, (_finding(FindingCode.DUPLICATE_MEMBER, ProcessingStage.PARSE, "/"),), "")
    except json.JSONDecodeError:
        return ParseResult(None, (_finding(FindingCode.MALFORMED_JSON, ProcessingStage.PARSE, "/"),), "")
    except (OverflowError, RecursionError, TypeError, ValueError, MemoryError):
        return ParseResult(None, (_finding(FindingCode.RESOURCE_LIMIT, ProcessingStage.PARSE, "/"),), "")
    return ParseResult(document, (), hashlib.sha256(CORPUS_DOMAIN + canonical).hexdigest())

def validate_matrix_cross_fields(document: JsonValue) -> bool:
    if not isinstance(document, dict) or document.get("schemaVersion") != "AdversarialInvariantMatrixV1":
        return False
    threats, invariants = document.get("threatUniverse"), document.get("invariants")
    if not isinstance(threats, list) or not isinstance(invariants, list) or not all(isinstance(row, dict) for row in invariants):
        return False
    rows = cast(list[dict[str, JsonValue]], invariants)
    identifiers = [row.get("invariantId") for row in rows]
    covered_threats = {row.get("threatId") for row in rows}
    tests_are_bound = all(row.get("evidenceClass") != "TEST" or isinstance(row.get("testIds"), list) and bool(row.get("testIds")) for row in rows)
    return len(set(identifiers)) == len(identifiers) and covered_threats == set(threats) and tests_are_bound

# ISSUE435_EXECUTOR_V1_START
def execute(stimulus: Stimulus) -> ValidationResult:
    """C2 boundary: C4 may replace only this marked executor region."""
    del stimulus
    finding = _finding(FindingCode.NOT_IMPLEMENTED, ProcessingStage.PHASE_VERDICT, "/")
    return ValidationResult(PhaseVerdict.NOT_IMPLEMENTED, (finding,), (), (), (), ACTIVATION, AUTHORITY_EFFECT)
# ISSUE435_EXECUTOR_V1_END

ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"
ISSUE435_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
ISSUE435_C1 = "205c02b3bac633d023d753356bc966c194ed36a7"
ISSUE435_REJECTED = "8d83713ed09dc626e24f1fe063e6afd9cfa5e8e9"
ISSUE435_BLOCKED = "134fbd91606eebbcdcff5f47b26b6d286acc1fa2"
ISSUE435_PREFLIGHT = "docs/governance/preflights/issue-435.json"
ISSUE435_PREFLIGHT_BLOB = "c554eaf7f73ea081434b1e2f818441fe0bc3eee9"
ISSUE435_FREEZE = "docs/governance/adversarial-convergence-red-freeze-v1.json"
ISSUE435_CAPS = {
    "docs/governance/preflights/issue-435.json": 220, "AGENTS.md": 45,
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md": 320, "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md": 180,
    "docs/governance/adversarial-convergence-framework-v1.schema.json": 260,
    "docs/governance/adversarial-convergence-framework-cases-v1.json": 300,
    ISSUE435_FREEZE: 120, "scripts/quality/adversarial_convergence.py": 600,
    "tests/unit/test_adversarial_convergence.py": 760, "scripts/quality/check_quality_stage.py": 60,
    "tests/unit/test_quality_dispatcher.py": 100, "scripts/guardrails_check.py": 60,
    "tests/unit/test_guardrails_check.py": 140, ".github/pull_request_template.md": 45,
    "docs/ADR/0064-adversarial-convergence-protocol.md": 160, "docs/QUALITY_GATES.md": 80,
    "docs/ENGINEERING_PROCESS_RCA.md": 80, "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 100,
    "docs/STAGE_ISSUE_PLAN.md": 70, "docs/STATUS.md": 80,
}
ISSUE435_NONFREEZE = frozenset(ISSUE435_CAPS) - {ISSUE435_FREEZE}
ISSUE435_READABILITY_REVIEWED = {"docs/ENGINEERING_PROCESS_RCA.md", "scripts/quality/adversarial_convergence.py", "tests/unit/test_quality_dispatcher.py"}
FREEZE_ARTIFACT_PATHS = {"corpus": "docs/governance/adversarial-convergence-framework-cases-v1.json", "schema": "docs/governance/adversarial-convergence-framework-v1.schema.json", "acceptanceTest": "tests/unit/test_adversarial_convergence.py", "skeleton": "scripts/quality/adversarial_convergence.py", "dispatcher": "scripts/quality/check_quality_stage.py", "guardrail": "scripts/guardrails_check.py"}
FREEZE_ROLES = ("ARCHITECTURE_SCOPE_PHASE", "SECURITY_TRUST", "READABILITY_FEASIBILITY", "MUTATION_FALSE_PASS")

def _git(root: Path, *args: str) -> GitResult:
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1"}
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(["/usr/bin/git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", *args], cwd=root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process.stdout is None:
            raise OSError
        output = bytearray()
        descriptor = process.stdout.fileno()
        deadline = time.monotonic() + 5
        while True:
            ready, _, _ = select.select([descriptor], [], [], max(0, deadline - time.monotonic()))
            if not ready:
                raise subprocess.TimeoutExpired(process.args, 5)
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            output.extend(chunk)
            if len(output) > 262_144:
                process.kill()
                process.wait()
                return GitResult("OVERSIZE", 128, b"", b"")
        process.wait(timeout=max(0.001, deadline - time.monotonic()))
        stdout = bytes(output)
        stdout.decode("utf-8", errors="strict")
        return GitResult("OK", process.returncode, stdout, b"")
    except subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
            process.wait()
        return GitResult("TIMEOUT", 128, b"", b"")
    except UnicodeError:
        return GitResult("DECODE_ERROR", 128, b"", b"")
    except (OSError, ValueError, OverflowError, MemoryError):
        return GitResult("FAILED", 128, b"", b"")

def _text(result: GitResult) -> str | None:
    if result.state != "OK" or result.returncode:
        return None
    try:
        return result.stdout.decode("utf-8", errors="strict")
    except UnicodeError:
        return None

def _collect_changes(root: Path, head: str) -> tuple[PathCharge, ...] | None:
    names = _text(_git(root, "diff", "--name-status", "-M", "-C", ISSUE435_BASE, head, "--"))
    numbers = _text(_git(root, "diff", "--numstat", "--no-renames", ISSUE435_BASE, head, "--"))
    if names is None or numbers is None:
        return None
    statuses: dict[str, str] = {}
    for row in (line.split("\t") for line in names.splitlines()):
        if len(row) != 2 or row[0] not in {"A", "M"} or row[1] in statuses:
            return None
        statuses[row[1]] = row[0]
    charges: list[PathCharge] = []
    for row in (line.split("\t") for line in numbers.splitlines()):
        if len(row) != 3 or not row[0].isdigit() or not row[1].isdigit() or row[2] not in statuses:
            return None
        tree = _text(_git(root, "ls-tree", head, "--", row[2]))
        fields = tree.split() if tree is not None else []
        if len(fields) < 3:
            return None
        charges.append(PathCharge(row[2], statuses[row[2]], int(row[0]), int(row[1]), fields[0]))
    return tuple(charges) if set(statuses) == {item.path for item in charges} else None

def _normalized_source(raw: bytes) -> bytes | None:
    start_marker = b"# ISSUE435_EXECUTOR_V1_START\n"
    end_marker = b"# ISSUE435_EXECUTOR_" + b"V1_END"
    if raw.count(start_marker) != 1 or raw.count(end_marker) != 1:
        return None
    prefix, rest = raw.split(start_marker)
    _, suffix = rest.split(end_marker)
    return prefix + start_marker + b"<C4_EXECUTOR_REGION>\n" + end_marker + suffix

def _closed_freeze_shape(document: JsonValue) -> bool:
    top = {"schemaVersion", "issue", "activation", "authorityEffect", "correction", "c2", "artifacts", "reviews"}
    if not isinstance(document, dict) or set(document) != top:
        return False
    correction, c2, artifacts, reviews = (document.get(key) for key in ("correction", "c2", "artifacts", "reviews"))
    if not isinstance(correction, dict) or set(correction) != {"rejectedHead", "wave", "authors"} or not isinstance(c2, dict) or set(c2) != {"head", "tree", "diffSha256"} or not isinstance(artifacts, dict) or set(artifacts) != set(FREEZE_ARTIFACT_PATHS) or not isinstance(reviews, list) or len(reviews) != 4:
        return False
    for name, item in artifacts.items():
        extra = {"semanticSha256"} if name == "corpus" else {"protectedSha256"} if name == "skeleton" else set()
        if not isinstance(item, dict) or set(item) != {"path", "blob", "sha256"} | extra:
            return False
    review_keys = {"role", "reviewer", "disposition", "head", "tree", "url", "content", "contentSha256"}
    prefix = "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-"
    for index, receipt in enumerate(reviews):
        url = receipt.get("url") if isinstance(receipt, dict) else None
        if not isinstance(receipt, dict) or set(receipt) != review_keys or receipt.get("role") != FREEZE_ROLES[index] or not isinstance(url, str) or not url.startswith(prefix) or not url.removeprefix(prefix).isdigit():
            return False
    return True

def _valid_freeze(document: JsonValue, root: Path, head: str) -> bool:
    if not _closed_freeze_shape(document):
        return False
    if not isinstance(document, dict) or document.get("schemaVersion") != "AdversarialConvergenceRedFreezeV1" or document.get("issue") != 435 or document.get("activation") != ACTIVATION or document.get("authorityEffect") != AUTHORITY_EFFECT:
        return False
    c2 = document.get("c2")
    correction = document.get("correction")
    artifacts = document.get("artifacts")
    reviews = document.get("reviews")
    if not isinstance(c2, dict) or not isinstance(correction, dict) or not isinstance(artifacts, dict) or not isinstance(reviews, list):
        return False
    c2_head, c2_tree = c2.get("head"), c2.get("tree")
    if correction.get("rejectedHead") != ISSUE435_REJECTED or correction.get("wave") != 1 or not isinstance(c2_head, str) or not isinstance(c2_tree, str) or len(c2_head) != 40 or len(c2_tree) != 40 or any(character not in "0123456789abcdef" for character in c2_head + c2_tree):
        return False
    roles = set(FREEZE_ROLES)
    seen_roles: set[str] = set()
    seen_reviewers: set[str] = set()
    seen_urls: set[str] = set()
    authors = correction.get("authors")
    if not isinstance(authors, list) or not authors or len(set(authors)) != len(authors) or not all(isinstance(item, str) for item in authors):
        return False
    for receipt in reviews:
        if not isinstance(receipt, dict) or receipt.get("disposition") != "PASS" or receipt.get("head") != c2_head or receipt.get("tree") != c2_tree:
            return False
        role, reviewer, url, content, digest = (receipt.get(key) for key in ("role", "reviewer", "url", "content", "contentSha256"))
        if not all(isinstance(item, str) for item in (role, reviewer, url, content, digest)):
            return False
        role_text, reviewer_text, url_text, content_text, digest_text = cast(tuple[str, str, str, str, str], (role, reviewer, url, content, digest))
        if reviewer_text in authors or hashlib.sha256(content_text.encode()).hexdigest() != digest_text or not all(token in content_text for token in ("PASS", c2_head, c2_tree)):
            return False
        seen_roles.add(role_text)
        seen_reviewers.add(reviewer_text)
        seen_urls.add(url_text)
    if seen_roles != roles or len(seen_reviewers) != 4 or len(seen_urls) != 4 or len(reviews) != 4:
        return False
    tree = _text(_git(root, "rev-parse", f"{c2_head}^{{tree}}"))
    if tree is None or tree.strip() != c2_tree:
        return False
    diff = _git(root, "diff", "--binary", ISSUE435_BASE, c2_head, "--")
    if diff.state != "OK" or diff.returncode or hashlib.sha256(diff.stdout).hexdigest() != c2.get("diffSha256"):
        return False
    for name, item in artifacts.items():
        if not isinstance(item, dict) or item.get("path") != FREEZE_ARTIFACT_PATHS[name] or not all(isinstance(item.get(key), str) for key in ("path", "blob", "sha256")):
            return False
        raw = _git(root, "show", f"{c2_head}:{item['path']}")
        blob = _text(_git(root, "rev-parse", f"{c2_head}:{item['path']}"))
        if raw.state != "OK" or raw.returncode or blob is None or blob.strip() != item["blob"] or hashlib.sha256(raw.stdout).hexdigest() != item["sha256"]:
            return False
        if item is artifacts["corpus"] and parse_json_bytes(raw.stdout, item["sha256"]).semantic_sha256 != item.get("semanticSha256"):
            return False
    skeleton = cast(dict[str, JsonValue], artifacts["skeleton"])
    source = _git(root, "show", f"{head}:{skeleton['path']}")
    normalized = _normalized_source(source.stdout) if source.state == "OK" and not source.returncode else None
    return normalized is not None and hashlib.sha256(normalized).hexdigest() == skeleton.get("protectedSha256")

def inspect_issue435_repository(root: Path, branch: str) -> RouteInspection:
    if branch != ISSUE435_BRANCH:
        return RouteInspection("UNKNOWN", (FindingCode.ROUTE_DRIFT,), 0)
    commands = {
        "head": _git(root, "rev-parse", "HEAD"),
        "history": _git(root, "rev-list", "--reverse", f"{ISSUE435_BASE}..HEAD"),
        "merges": _git(root, "rev-list", "--min-parents=2", f"{ISSUE435_BASE}..HEAD"),
        "preflight": _git(root, "rev-parse", f"HEAD:{ISSUE435_PREFLIGHT}"),
        "status": _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
    }
    values = {key: _text(value) for key, value in commands.items()}
    if any(value is None for value in values.values()):
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    head = cast(str, values["head"]).strip()
    commits = cast(str, values["history"]).splitlines()
    changes = _collect_changes(root, head)
    if changes is None:
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    paths = {item.path for item in changes}
    freeze_present = ISSUE435_FREEZE in paths
    expected = set(ISSUE435_CAPS if freeze_present else ISSUE435_NONFREEZE)
    charged = sum(item.additions + item.deletions for item in changes)
    findings: list[FindingCode] = []
    event_head = os.environ.get("GITHUB_HEAD_SHA", "").strip()
    if event_head and event_head != head:
        findings.append(FindingCode.IDENTITY_MISMATCH)
    if commits[:4] != [ISSUE435_C1, "b099747812bcd97f812358908cb847c351190bc3", ISSUE435_REJECTED, ISSUE435_BLOCKED]:
        findings.append(FindingCode.IDENTITY_MISMATCH)
    if cast(str, values["merges"]).strip() or cast(str, values["status"]) or cast(str, values["preflight"]).strip() != ISSUE435_PREFLIGHT_BLOB:
        findings.append(FindingCode.ROUTE_DRIFT)
    if paths != expected or any(item.status not in {"A", "M"} or item.mode != "100644" for item in changes):
        findings.append(FindingCode.ROUTE_DRIFT)
    if any((item.additions + item.deletions) * 10 >= ISSUE435_CAPS.get(item.path, 0) * 9 for item in changes):
        findings.append(FindingCode.BUDGET_STOP)
    elif any((item.additions + item.deletions) * 20 >= ISSUE435_CAPS.get(item.path, 0) * 17 and item.path not in ISSUE435_READABILITY_REVIEWED for item in changes):
        findings.append(FindingCode.BUDGET_REVIEW_REQUIRED)
    if charged > (3_620 if freeze_present else 3_500):
        findings.append(FindingCode.BUDGET_STOP)
    phase = "C2"
    if not freeze_present:
        parent = _text(_git(root, "rev-parse", "HEAD^"))
        if len(commits) != 5 or parent is None or parent.strip() != ISSUE435_BLOCKED:
            findings.append(FindingCode.ROUTE_DRIFT)
    else:
        raw = _git(root, "show", f"HEAD:{ISSUE435_FREEZE}")
        parsed = parse_json_bytes(raw.stdout, hashlib.sha256(raw.stdout).hexdigest(), ParseLimits(65_536, 32, 4_096)) if raw.state == "OK" and not raw.returncode else ParseResult(None, (), "")
        if parsed.document is None or not _valid_freeze(parsed.document, root, head):
            findings.append(FindingCode.REVIEW_IDENTITY_MISMATCH)
        c2_value = parsed.document.get("c2") if isinstance(parsed.document, dict) else None
        c2_head = c2_value.get("head") if isinstance(c2_value, dict) else ""
        if len(commits) == 6 and commits[4] == c2_head:
            phase = "C3"
            delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[5]))
            if delta is None or delta.splitlines() != [ISSUE435_FREEZE]:
                findings.append(FindingCode.ROUTE_DRIFT)
        elif len(commits) == 7 and commits[4] == c2_head:
            phase = "C4"
            c3_delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[5]))
            c4_delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[6]))
            if c3_delta is None or c3_delta.splitlines() != [ISSUE435_FREEZE] or c4_delta is None or c4_delta.splitlines() != ["scripts/quality/adversarial_convergence.py"]:
                findings.append(FindingCode.ROUTE_DRIFT)
        else:
            findings.append(FindingCode.ROUTE_DRIFT)
    return RouteInspection(phase, tuple(dict.fromkeys(findings)), charged)

def _resolve_branch(event: str, local: str) -> str:
    return "" if event and local and event != local else event or local

def _current_branch(root: Path) -> str:
    event = os.environ.get("GITHUB_HEAD_REF", "").strip()
    local = _text(_git(root, "branch", "--show-current"))
    local_branch = local.strip() if local is not None else ""
    return _resolve_branch(event, local_branch)

def _result_document(result: ValidationResult) -> dict[str, JsonValue]:
    findings: list[JsonValue] = [{"stage": item.stage, "code": item.code, "location": item.location, "blocker": item.blocker} for item in result.findings]
    observations: list[JsonValue] = [{"stage": item.stage, "state": item.state, "callbackCount": item.callback_count, "justification": item.justification, "findingCodes": list(item.finding_codes)} for item in result.observations]
    executions: list[JsonValue] = [{"candidate": item.candidate, "ordinal": item.ordinal, "phase": item.phase, "stage": item.stage, "callbackCount": item.callback_count, "observedState": item.observed_state, "observedFindingCodes": list(item.observed_finding_codes)} for item in result.execution_receipts]
    mutations: list[JsonValue] = [{"mutantId": item.mutant_id, "assertionId": item.assertion_id, "executionCount": item.execution_count, "failureCount": item.failure_count, "state": item.state, "observedVerdict": item.observed_verdict, "observedFindingCodes": list(item.observed_finding_codes)} for item in result.mutation_receipts]
    return {"verdict": result.verdict, "findings": findings, "observations": observations, "executionReceipts": executions, "mutationReceipts": mutations, "activation": result.activation, "authorityEffect": result.authority_effect}

def _emit(document: dict[str, JsonValue]) -> None:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(raw) > 131_072:
        raw = b'{"code":"ACP.VERDICT.RESOURCE_FAILURE","kind":"INFRASTRUCTURE_FAILURE"}'
    sys.stdout.buffer.write(raw + b"\n")

def _worker_main() -> int:
    try:
        raw = sys.stdin.buffer.read(65_537)
        parsed = parse_json_bytes(raw, hashlib.sha256(raw).hexdigest())
        if parsed.document is None or not isinstance(parsed.document, dict) or set(parsed.document) != {"kind", "payload"}:
            _emit({"code": FindingCode.SCHEMA_DRIFT, "kind": "CONTRACT_FAILURE"})
            return 1
        kind, payload = parsed.document["kind"], parsed.document["payload"]
        if not isinstance(kind, str) or not isinstance(payload, dict):
            _emit({"code": FindingCode.SCHEMA_DRIFT, "kind": "CONTRACT_FAILURE"})
            return 1
        result = execute(Stimulus(kind, payload))
        _emit(_result_document(result))
        return 3 if result.verdict is PhaseVerdict.NOT_IMPLEMENTED else 0
    except (OSError, UnicodeError, RecursionError, MemoryError, ValueError, OverflowError):
        _emit({"code": FindingCode.RESOURCE_FAILURE, "kind": "INFRASTRUCTURE_FAILURE"})
        return 2

def _route_main() -> int:
    try:
        branch = _current_branch(ROOT)
        inspection = inspect_issue435_repository(ROOT, branch)
        code = inspection.findings[0] if inspection.findings else None
        _emit({"activation": ACTIVATION, "authorityEffect": AUTHORITY_EFFECT, "code": code, "phase": inspection.phase})
        if code is None:
            return 0
        return 2 if code in {FindingCode.PLATFORM_FAILURE, FindingCode.RESOURCE_FAILURE} else 1
    except (OSError, UnicodeError, RecursionError, MemoryError, ValueError, OverflowError):
        _emit({"code": FindingCode.PLATFORM_FAILURE, "kind": "INFRASTRUCTURE_FAILURE"})
        return 2

def main() -> int:
    if sys.argv[1:] == ["--execute-stdin"]:
        return _worker_main()
    if sys.argv[1:] == ["--route-only"]:
        return _route_main()
    _emit({"code": "ACP.RUNNER_REQUIRED", "kind": "CONTRACT_FAILURE"})
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
