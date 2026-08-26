#!/usr/bin/env python3
"""Finite offline adversarial-convergence worker and fail-closed route inspector."""
from __future__ import annotations
import hashlib
import json
import os
import re
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
IDENTITY_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9._'-]*[a-z0-9])?(?: [a-z0-9](?:[a-z0-9._'-]*[a-z0-9])?)* <[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+>\Z", re.ASCII)
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
def _execute_result(verdict: PhaseVerdict, findings: tuple[Finding, ...], trace: str, *evidence: object) -> ValidationResult:
    states = {"A": StageState.ACCEPTED, "R": StageState.REJECTED, "N": StageState.NOT_APPLICABLE, "X": StageState.NOT_REACHED}
    reasons = {"A": "contract satisfied", "R": "rejected", "N": "not applicable", "X": "blocked by rejected predecessor"}
    observations = tuple(StageObservation(stage, states[symbol], 0 if symbol == "X" else 1, reasons[symbol], tuple(item.code for item in findings if item.stage is stage) if symbol == "R" else ()) for stage, symbol in zip(ProcessingStage, trace, strict=True))
    executions = cast(tuple[ExecutionReceipt, ...], evidence[0]) if evidence else ()
    mutations = cast(tuple[MutationReceipt, ...], evidence[1]) if len(evidence) > 1 else ()
    return ValidationResult(verdict, findings, observations, executions, mutations, ACTIVATION, AUTHORITY_EFFECT)
def _execute_invalid(code: FindingCode, stage: ProcessingStage, location: str, *settings: object) -> ValidationResult:
    verdict = next((item for item in settings if isinstance(item, PhaseVerdict)), PhaseVerdict.INVALID)
    blocker = next((item for item in settings if isinstance(item, BlockerClass)), BlockerClass.IMPLEMENTATION)
    trace = next((item for item in settings if isinstance(item, str) and not isinstance(item, PhaseVerdict | BlockerClass)), "NNRXXXXX")
    return _execute_result(verdict, (_finding(code, stage, location, blocker),), trace)
def _execute_closed(value: JsonValue, keys: str) -> bool:
    return isinstance(value, dict) and set(value) == set(keys.split())
def _execute_strings(value: JsonValue, *requirements: bool) -> bool:
    nonempty, unique = (requirements + (False, False))[:2]
    return isinstance(value, list) and (bool(value) or not nonempty) and all(isinstance(item, str) and (bool(item) or not nonempty) for item in value) and (not unique or len(value) == len(set(cast(list[str], value))))
def _execute_schema_invalid() -> ValidationResult:
    return _execute_invalid(FindingCode.SCHEMA_DRIFT, ProcessingStage.SCHEMA, "/payload")
def _execute_filesystem(payload: dict[str, JsonValue]) -> ValidationResult:
    relative, kinds = payload["relativePath"], payload["componentKinds"]
    if not isinstance(relative, str) or not _valid_relative_path(relative):
        return _execute_invalid(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, "/payload/relativePath", "RXXXXXXX")
    if not isinstance(kinds, list) or not kinds:
        return _execute_invalid(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, "/payload/componentKinds", "RXXXXXXX")
    bad = next((index for index, kind in enumerate(kinds) if not isinstance(kind, str) or kind != ("DIRECTORY" if index < len(kinds) - 1 else "REGULAR_FILE")), None)
    if bad is not None or payload["nofollowAvailable"] is not True or payload["stableIdentity"] is not True:
        location = f"/payload/componentKinds/{bad}" if bad is not None else "/payload"
        return _execute_invalid(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, location, "RXXXXXXX")
    if len(kinds) != len(relative.split("/")):
        return _execute_invalid(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, "/payload/componentKinds", "RXXXXXXX")
    sizes = payload["declaredBytes"], payload["readBytes"], payload["limitBytes"]
    if not all(type(value) is int for value in sizes):
        return _execute_schema_invalid()
    declared, read, limit = cast(tuple[int, int, int], sizes)
    if min(declared, read, limit) < 0 or declared > limit:
        return _execute_invalid(FindingCode.INPUT_TOO_LARGE, ProcessingStage.BOUNDS, "/payload/declaredBytes", "RXXXXXXX")
    if declared != read:
        return _execute_invalid(FindingCode.RESOURCE_FAILURE, ProcessingStage.BOUNDS, "/payload/readBytes", "RXXXXXXX")
    return _execute_result(PhaseVerdict.VALID, (), "ANNNNNNA")
def _execute_json(payload: dict[str, JsonValue]) -> ValidationResult:
    raw, digest = payload["raw"], payload["rawSha256"]
    limits = payload["maxBytes"], payload["maxDepth"], payload["maxMembers"]
    if not isinstance(raw, str) or not _hex_text(digest, 64) or not all(type(value) is int for value in limits):
        return _execute_schema_invalid()
    parsed_limits = cast(tuple[int, int, int], limits)
    if min(parsed_limits) <= 0:
        return _execute_schema_invalid()
    parsed = parse_json_bytes(raw.encode("utf-8"), cast(str, digest), ParseLimits(*parsed_limits))
    if not parsed.findings:
        return _execute_result(PhaseVerdict.VALID, (), "AANANNNA")
    finding = parsed.findings[0]
    stage = ProcessingStage.BOUNDS if finding.code is FindingCode.INPUT_TOO_LARGE else ProcessingStage.PARSE
    return _execute_invalid(finding.code, stage, "/payload/raw", "RXXXXXXX" if stage is ProcessingStage.BOUNDS else "ARXXXXXX")
def _execute_document(payload: dict[str, JsonValue]) -> ValidationResult:
    document = payload["document"]
    expected = {"schemaVersion": "FrameworkEvidenceV1", "reviewState": "PENDING_EXTERNAL_REVIEW"}
    if document == expected and isinstance(document, dict):
        return _execute_result(PhaseVerdict.VALID, (), "NNANNNNA")
    extra = next((key for key in document if key not in expected), "document") if isinstance(document, dict) else "document"
    return _execute_invalid(FindingCode.SCHEMA_DRIFT, ProcessingStage.SCHEMA, f"/payload/document/{extra}")
def _execute_pipeline(payload: dict[str, JsonValue]) -> ValidationResult:
    callbacks = payload["callbacks"]
    if not isinstance(callbacks, list) or not callbacks or len(callbacks) > len(ProcessingStage):
        return _execute_schema_invalid()
    rejected = False
    stages = list(ProcessingStage)
    for index, value in enumerate(callbacks):
        if not _execute_closed(value, "stage predecessors state"):
            return _execute_schema_invalid()
        row = cast(dict[str, JsonValue], value)
        stage, predecessors, state = row["stage"], row["predecessors"], row["state"]
        if not isinstance(stage, str) or stage not in ProcessingStage or not _execute_strings(predecessors) or not isinstance(state, str) or state not in StageState:
            return _execute_schema_invalid()
        expected = [str(item) for item in stages[:index]]
        if stage != str(stages[index]) or predecessors != expected or state == StageState.NOT_REACHED and not rejected:
            return _execute_invalid(FindingCode.PREDECESSOR_VIOLATION, ProcessingStage.GRAPH_CONFLICT, f"/payload/callbacks/{index}/predecessors", "NNNNNNRX")
        if rejected and state != StageState.NOT_REACHED:
            return _execute_invalid(FindingCode.LATE_STAGE_EXECUTION, ProcessingStage.GRAPH_CONFLICT, f"/payload/callbacks/{index}", "NNNNNNRX")
        rejected = rejected or state == StageState.REJECTED
    return _execute_result(PhaseVerdict.VALID, (), "NNNNNNAA")
def _execute_outcome(payload: dict[str, JsonValue]) -> ValidationResult:
    contract_verdict, observed_verdict = payload["contractVerdict"], payload["observedVerdict"]
    contract, observed = payload["contractFindings"], payload["observedFindings"]
    if not isinstance(contract_verdict, str) or contract_verdict not in PhaseVerdict or not isinstance(observed_verdict, str) or observed_verdict not in PhaseVerdict or not _execute_strings(contract, False, True) or not _execute_strings(observed, False, True):
        return _execute_schema_invalid()
    if contract_verdict == observed_verdict and contract == observed:
        return _execute_result(PhaseVerdict.VALID, (), "NNNNNNNA")
    findings = [_finding(FindingCode.OUTCOME_NOT_EXACT, ProcessingStage.PHASE_VERDICT, "/payload/observedFindings")]
    if set(cast(list[str], observed)) < set(cast(list[str], contract)):
        findings.append(_finding(FindingCode.SUBSET_OUTCOME, ProcessingStage.PHASE_VERDICT, "/payload/observedFindings"))
    return _execute_result(PhaseVerdict.INVALID, tuple(findings), "NNNNNNNR")
def _execute_mutations(payload: dict[str, JsonValue]) -> ValidationResult:
    required, values = payload["requiredMutantIds"], payload["receipts"]
    keys = "mutantId assertionId executionCount failureCount state observedVerdict observedFindingCodes"
    if not _execute_strings(required, True, True) or not isinstance(values, list) or len(values) != len(cast(list[str], required)) or any(not _execute_closed(value, keys) for value in values):
        return _execute_schema_invalid()
    rows = cast(list[dict[str, JsonValue]], values)
    for index, row in enumerate(rows):
        if row["mutantId"] != cast(list[str], required)[index] or not isinstance(row["assertionId"], str) or not row["assertionId"] or type(row["executionCount"]) is not int or type(row["failureCount"]) is not int or row["state"] not in MutationState or row["observedVerdict"] not in PhaseVerdict or not _execute_strings(row["observedFindingCodes"], False, True):
            return _execute_schema_invalid()
    receipts = tuple(MutationReceipt(cast(str, row["mutantId"]), cast(str, row["assertionId"]), cast(int, row["executionCount"]), cast(int, row["failureCount"]), MutationState(cast(str, row["state"])), PhaseVerdict(cast(str, row["observedVerdict"])), tuple(FindingCode(code) for code in cast(list[str], row["observedFindingCodes"]))) for row in rows)
    bad = next((index for index, row in enumerate(rows) if row["executionCount"] != 1 or row["failureCount"] != 1 or row["state"] != MutationState.KILLED), None)
    if bad is None:
        return _execute_result(PhaseVerdict.VALID, (), "NNNNANNA", (), receipts)
    field = "executionCount" if rows[bad]["executionCount"] != 1 else "state"
    code = FindingCode.MUTANT_NOT_EXECUTED if field == "executionCount" else FindingCode.MUTANT_SURVIVED
    finding = _finding(code, ProcessingStage.INDEPENDENT_TRUST, f"/payload/receipts/{bad}/{field}")
    return _execute_result(PhaseVerdict.INVALID, (finding,), "NNNNRXXX", (), receipts)
def _execute_ledger(payload: dict[str, JsonValue]) -> ValidationResult:
    candidate, phase, order, values = payload["candidate"], payload["phase"], payload["contractOrder"], payload["rows"]
    keys = "candidate ordinal phase stage callbackCount observedState observedFindingCodes"
    if not isinstance(candidate, str) or not candidate or not isinstance(phase, str) or not phase or not _execute_strings(order, True, False) or not isinstance(values, list) or any(not _execute_closed(value, keys) for value in values):
        return _execute_schema_invalid()
    rows = cast(list[dict[str, JsonValue]], values)
    for row in rows:
        if not isinstance(row["candidate"], str) or not row["candidate"] or type(row["ordinal"]) is not int or not isinstance(row["phase"], str) or not row["phase"] or row["stage"] not in ProcessingStage or type(row["callbackCount"]) is not int or row["callbackCount"] not in {0, 1} or row["observedState"] not in StageState or not _execute_strings(row["observedFindingCodes"], False, True):
            return _execute_schema_invalid()
    receipts = tuple(ExecutionReceipt(cast(str, row["candidate"]), cast(int, row["ordinal"]), cast(str, row["phase"]), ProcessingStage(cast(str, row["stage"])), cast(int, row["callbackCount"]), StageState(cast(str, row["observedState"])), tuple(FindingCode(code) for code in cast(list[str], row["observedFindingCodes"]))) for row in rows)
    expected_order = [str(stage) for stage in list(ProcessingStage)[:len(cast(list[str], order))]]
    location = "/payload/rows"
    if order == expected_order and len(rows) == len(cast(list[str], order)):
        for index, row in enumerate(rows):
            semantic = row["candidate"] == candidate and row["phase"] == phase and row["ordinal"] == index + 1 and row["stage"] == cast(list[str], order)[index]
            semantic = semantic and (row["callbackCount"] == 0) == (row["observedState"] == StageState.NOT_REACHED)
            semantic = semantic and (row["observedState"] == StageState.REJECTED or not row["observedFindingCodes"])
            if not semantic:
                location = f"/payload/rows/{index}/ordinal" if row["ordinal"] != index + 1 else f"/payload/rows/{index}"
                break
        else:
            return _execute_result(PhaseVerdict.VALID, (), "NNNNANNA", receipts)
    elif rows:
        location = "/payload/rows/0" if len(rows) == len(cast(list[str], order)) else location
    finding = _finding(FindingCode.MOCK_LEDGER_INVALID, ProcessingStage.INDEPENDENT_TRUST, location)
    return _execute_result(PhaseVerdict.INVALID, (finding,), "NNNNRXXX", receipts)
def _execute_reviews(payload: dict[str, JsonValue]) -> ValidationResult:
    author, head, tree, required, values = payload["candidateAuthor"], payload["head"], payload["tree"], payload["requiredRoles"], payload["receipts"]
    roles = ["ARCHITECTURE_SCOPE_PHASE", "SECURITY_TRUST", "READABILITY_FEASIBILITY", "MUTATION_FALSE_PASS"]
    keys = "role reviewer source disposition head tree"
    if not isinstance(author, str) or not author or not _hex_text(head, 40) or not _hex_text(tree, 40) or not _execute_strings(required, True, False) or not isinstance(values, list):
        return _execute_schema_invalid()
    if required != roles or len(values) != 4 or [value.get("role") for value in values if isinstance(value, dict)] != roles:
        return _execute_invalid(FindingCode.REQUIRED_REVIEW_MISSING, ProcessingStage.INDEPENDENT_TRUST, "/payload/receipts", PhaseVerdict.BLOCKED_EVIDENCE, "NNNNRXXX", BlockerClass.EVIDENCE)
    if any(not _execute_closed(value, keys) for value in values):
        return _execute_schema_invalid()
    rows = cast(list[dict[str, JsonValue]], values)
    reviewers: set[str] = set()
    sources: set[str] = set()
    for index, row in enumerate(rows):
        if any(not isinstance(row[field], str) or not row[field] for field in keys.split()) or not _hex_text(row["head"], 40) or not _hex_text(row["tree"], 40):
            return _execute_schema_invalid()
        if row["reviewer"] == author:
            return _execute_invalid(FindingCode.REVIEW_SELF_ATTESTED, ProcessingStage.INDEPENDENT_TRUST, f"/payload/receipts/{index}/reviewer", "NNNNRXXX")
        field = "disposition" if row["disposition"] != "PASS" else "head" if row["head"] != head else "tree" if row["tree"] != tree else "reviewer" if cast(str, row["reviewer"]) in reviewers else "source" if cast(str, row["source"]) in sources else ""
        if field:
            return _execute_invalid(FindingCode.REVIEW_IDENTITY_MISMATCH, ProcessingStage.INDEPENDENT_TRUST, f"/payload/receipts/{index}/{field}", "NNNNRXXX")
        reviewers.add(cast(str, row["reviewer"]))
        sources.add(cast(str, row["source"]))
    return _execute_result(PhaseVerdict.VALID, (), "NNNNANNA")
def _execute_expectation(payload: dict[str, JsonValue]) -> ValidationResult:
    members, imports, calls, identifiers = payload["executorMembers"], payload["productionImports"], payload["dynamicImportCalls"], payload["oracleIdentifiers"]
    if not _execute_strings(members) or not _execute_strings(imports) or type(calls) is not int or not _execute_strings(identifiers):
        return _execute_schema_invalid()
    if members != ["kind", "payload"]:
        bad = next((index for index, value in enumerate(cast(list[str], members)) if index > 1 or value not in {"kind", "payload"}), 0)
        return _execute_invalid(FindingCode.EXPECTATION_NOT_INDEPENDENT, ProcessingStage.INDEPENDENT_TRUST, f"/payload/executorMembers/{bad}", "NNNNRXXX")
    if imports != ["hashlib", "json"] or calls != 0 or identifiers:
        return _execute_invalid(FindingCode.EXPECTATION_NOT_INDEPENDENT, ProcessingStage.INDEPENDENT_TRUST, "/payload/productionImports/0", "NNNNRXXX")
    return _execute_result(PhaseVerdict.VALID, (), "NNNNANNA")
def _execute_route(payload: dict[str, JsonValue]) -> ValidationResult:
    trusted = {"branch": ISSUE435_BRANCH, "authorizedBranch": ISSUE435_BRANCH, "base": ISSUE435_BASE, "authorizedBase": ISSUE435_BASE, "preflightBlob": ISSUE435_PREFLIGHT_BLOB, "authorizedPreflightBlob": ISSUE435_PREFLIGHT_BLOB}
    for field, trusted_value in trusted.items():
        if payload[field] != trusted_value:
            code = FindingCode.IDENTITY_MISMATCH if field == "preflightBlob" else FindingCode.ROUTE_DRIFT
            return _execute_invalid(code, ProcessingStage.AUTHORIZATION, f"/payload/{field}", "NNNNNRXX")
    values = payload["files"]
    if not isinstance(values, list) or len(values) != 1 or not _execute_closed(values[0], "path status mode chargedLines cap readabilityReviewed"):
        return _execute_invalid(FindingCode.ROUTE_DRIFT, ProcessingStage.AUTHORIZATION, "/payload/files", "NNNNNRXX")
    row = cast(dict[str, JsonValue], values[0])
    if type(row["chargedLines"]) is not int or type(row["cap"]) is not int or type(row["readabilityReviewed"]) is not bool:
        return _execute_schema_invalid()
    charged, cap = row["chargedLines"], row["cap"]
    if charged < 0 or cap <= 0:
        return _execute_schema_invalid()
    expected_route = {"path": "scripts/quality/adversarial_convergence.py", "status": "M", "mode": "100644"}
    for field, value in expected_route.items():
        if row[field] != value:
            return _execute_invalid(FindingCode.ROUTE_DRIFT, ProcessingStage.AUTHORIZATION, f"/payload/files/0/{field}", "NNNNNRXX")
    if charged * 10 >= cap * 9:
        return _execute_invalid(FindingCode.BUDGET_STOP, ProcessingStage.AUTHORIZATION, "/payload/files/0/chargedLines", PhaseVerdict.BLOCKED_IMPLEMENTATION, "NNNNNRXX")
    if charged * 20 >= cap * 17 and row["readabilityReviewed"] is not True:
        return _execute_invalid(FindingCode.BUDGET_REVIEW_REQUIRED, ProcessingStage.AUTHORIZATION, "/payload/files/0/readabilityReviewed", PhaseVerdict.BLOCKED_EVIDENCE, "NNNNNRXX", BlockerClass.EVIDENCE)
    return _execute_result(PhaseVerdict.VALID, (), "NNNNNANA")
def _execute_checkpoint(payload: dict[str, JsonValue]) -> ValidationResult:
    keys = "reviewState activation authorityEffect expectedRed implementationBlockers evidenceBlockers boundHead candidateHead boundDiffSha256 candidateDiffSha256"
    if set(payload) - set(keys.split()) or set(keys.split()) - set(payload) not in (set(), {"authorityEffect"}):
        return _execute_schema_invalid()
    constants = {"reviewState": "PENDING_EXTERNAL_REVIEW", "activation": ACTIVATION, "expectedRed": ["ACP.NOT_IMPLEMENTED"], "implementationBlockers": ["IMPLEMENTATION"], "evidenceBlockers": ["FOUR_EXTERNAL_REVIEWS"]}
    if any(payload.get(field) != value for field, value in constants.items()):
        return _execute_invalid(FindingCode.CHECKPOINT_INVALID, ProcessingStage.PHASE_VERDICT, "/payload", "NNNNNNNR")
    if payload.get("authorityEffect") != AUTHORITY_EFFECT:
        return _execute_invalid(FindingCode.CHECKPOINT_INVALID, ProcessingStage.PHASE_VERDICT, "/payload/authorityEffect", "NNNNNNNR")
    for bound, candidate, width in (("boundHead", "candidateHead", 40), ("boundDiffSha256", "candidateDiffSha256", 64)):
        if not _hex_text(payload.get(bound), width) or not _hex_text(payload.get(candidate), width) or payload[bound] != payload[candidate]:
            return _execute_invalid(FindingCode.CHECKPOINT_INVALID, ProcessingStage.PHASE_VERDICT, f"/payload/{candidate}", "NNNNNNNR")
    return _execute_result(PhaseVerdict.VALID, (), "NNNNNNNA")
def _execute_resource(payload: dict[str, JsonValue]) -> ValidationResult:
    capabilities, imported, operation = payload["capabilities"], payload["import"], payload["operation"]
    if not _execute_closed(capabilities, "nofollow descriptorRelative") or not _execute_closed(imported, "module origin status errorType") or not _execute_closed(operation, "status errorType"):
        return _execute_schema_invalid()
    caps, imp, op = cast(dict[str, JsonValue], capabilities), cast(dict[str, JsonValue], imported), cast(dict[str, JsonValue], operation)
    if type(caps["nofollow"]) is not bool or type(caps["descriptorRelative"]) is not bool or not isinstance(imp["module"], str) or not isinstance(imp["origin"], str) or not isinstance(imp["status"], str) or not (imp["errorType"] is None or isinstance(imp["errorType"], str)) or not isinstance(op["status"], str) or not (op["errorType"] is None or isinstance(op["errorType"], str)):
        return _execute_schema_invalid()
    for field in ("nofollow", "descriptorRelative"):
        if caps[field] is not True:
            return _execute_invalid(FindingCode.UNSAFE_FILESYSTEM_INPUT, ProcessingStage.BOUNDS, f"/payload/capabilities/{field}", PhaseVerdict.BLOCKED_IMPLEMENTATION, "RXXXXXXX")
    import_valid = imp["module"] == "scripts.quality.adversarial_convergence" and imp["origin"] == "scripts/quality/adversarial_convergence.py" and imp["status"] == "AVAILABLE" and imp["errorType"] is None
    if not import_valid:
        return _execute_invalid(FindingCode.PLATFORM_FAILURE, ProcessingStage.BOUNDS, "/payload/import/status", PhaseVerdict.BLOCKED_IMPLEMENTATION, "RXXXXXXX")
    if op["status"] != "COMPLETED" or op["errorType"] is not None:
        return _execute_invalid(FindingCode.RESOURCE_FAILURE, ProcessingStage.BOUNDS, "/payload/operation/status", PhaseVerdict.BLOCKED_IMPLEMENTATION, "RXXXXXXX")
    return _execute_result(PhaseVerdict.VALID, (), "ANNNNNNA")
def execute(stimulus: Stimulus) -> ValidationResult:
    handlers = {"FILESYSTEM": _execute_filesystem, "JSON": _execute_json, "DOCUMENT": _execute_document, "PIPELINE": _execute_pipeline, "OUTCOME": _execute_outcome, "MUTATION_SET": _execute_mutations, "EXECUTION_LEDGER": _execute_ledger, "REVIEWS": _execute_reviews, "EXPECTATION_BOUNDARY": _execute_expectation, "ROUTE": _execute_route, "CHECKPOINT": _execute_checkpoint, "RESOURCE": _execute_resource}
    shapes = {"FILESYSTEM": "relativePath componentKinds nofollowAvailable declaredBytes readBytes limitBytes stableIdentity", "JSON": "raw rawSha256 maxBytes maxDepth maxMembers", "DOCUMENT": "document", "PIPELINE": "callbacks", "OUTCOME": "contractVerdict contractFindings observedVerdict observedFindings", "MUTATION_SET": "requiredMutantIds receipts", "EXECUTION_LEDGER": "candidate phase contractOrder rows", "REVIEWS": "candidateAuthor head tree requiredRoles receipts", "EXPECTATION_BOUNDARY": "executorMembers productionImports dynamicImportCalls oracleIdentifiers", "ROUTE": "branch authorizedBranch base authorizedBase preflightBlob authorizedPreflightBlob files", "RESOURCE": "capabilities import operation"}
    handler = handlers.get(stimulus.kind)
    if handler is None:
        return _execute_invalid(FindingCode.SCHEMA_DRIFT, ProcessingStage.SCHEMA, "/kind")
    if stimulus.kind in shapes and set(stimulus.payload) != set(shapes[stimulus.kind].split()):
        return _execute_schema_invalid()
    try:
        return handler(stimulus.payload)
    except (AttributeError, KeyError, TypeError, ValueError, IndexError, OverflowError, MemoryError):
        return _execute_schema_invalid()
# ISSUE435_EXECUTOR_V1_END
ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"
ISSUE435_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
ISSUE435_C1 = "205c02b3bac633d023d753356bc966c194ed36a7"
ISSUE435_REJECTED = "8d83713ed09dc626e24f1fe063e6afd9cfa5e8e9"
ISSUE435_BLOCKED = "134fbd91606eebbcdcff5f47b26b6d286acc1fa2"
ISSUE435_H6, ISSUE435_C2_BASE, ISSUE435_C2_HARDENED, ISSUE435_C2_TYPED, ISSUE435_C2 = "7a17fe323a8c9acd9ea887f9932e4ca79ff02853", "26347f466778e946cc3b5aa8fa110f4597b279e2", "e6821c579c7bc1a28778278954cb52de7bf41dbb", "55a3911c3b2b35ae681b647e143c492e6a4a8cad", "bf795a2760479784012fff6e644ec5d102b3caf2"
ISSUE435_PRIOR_C2, ISSUE435_PRIOR_C3, ISSUE435_PRIOR_C4 = "8fa7667b1d613b1470195ff712763aac5b5e048c", "0ae2593eca92c4e9657a04cb45152d7be839a48b", "a4d903dfb5b0c40aabb4117a29a901db0972182f"
ISSUE435_ROUTE_RED, ISSUE435_ROUTE_C2, ISSUE435_ROUTE_BASE_BOUND, ISSUE435_ROUTE_HEAD_BOUND, ISSUE435_ROUTE_ADAPTER, ISSUE435_PORTABLE_C2, ISSUE435_BLOCKED_C3, ISSUE435_FALSE_RED_C2 = "dcbe15d58dff5ceafe7319e2baa3302ff01b6510", "8a9bdc41c63cb449afdc6bf7f806ef946a73faa2", "84f1430822d696537c41b5a022d3cc14d72becea", "c7886a86ad84f8c3e2ceb1a9f9c675e7f3d535da", "956aed3d78733259ba6a024dcbead6f2f6f43c40", "f82be816e349d13d8365b72fbeb51498d244755e", "cc394d4dadef3c32dc735fc84a2b9c49e3336985", "bf3a53ddac282a8daab61db2eaa5d030959eae0f"
ISSUE435_HISTORY = (ISSUE435_C1, "b099747812bcd97f812358908cb847c351190bc3", ISSUE435_REJECTED, ISSUE435_BLOCKED, "6d741aec9a2a56d54034e0092a2e24d535079517", "9bd0a2786ca41e720a275e70a2c98470a3f3aa38", "6b681b4acc419d2fa63c35862d6b6185ce82dd50", ISSUE435_H6, ISSUE435_C2_BASE, ISSUE435_C2_HARDENED, ISSUE435_C2_TYPED, ISSUE435_C2, ISSUE435_PRIOR_C2, ISSUE435_PRIOR_C3, ISSUE435_PRIOR_C4, ISSUE435_ROUTE_RED, ISSUE435_ROUTE_C2, ISSUE435_ROUTE_BASE_BOUND, ISSUE435_ROUTE_HEAD_BOUND, ISSUE435_ROUTE_ADAPTER, ISSUE435_PORTABLE_C2, ISSUE435_BLOCKED_C3, ISSUE435_FALSE_RED_C2)
ISSUE435_PREFLIGHT = "docs/governance/preflights/issue-435.json"
ISSUE435_PREFLIGHT_BLOB = "c554eaf7f73ea081434b1e2f818441fe0bc3eee9"
ISSUE435_FREEZE = "docs/governance/adversarial-convergence-red-freeze-v1.json"
ISSUE435_CAPS = {
    "docs/governance/preflights/issue-435.json": 220, "AGENTS.md": 45,
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md": 320, "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md": 180,
    "docs/governance/adversarial-convergence-framework-v1.schema.json": 260,
    "docs/governance/adversarial-convergence-framework-cases-v1.json": 300,
    ISSUE435_FREEZE: 120, "scripts/quality/adversarial_convergence.py": 900,
    "tests/unit/test_adversarial_convergence.py": 1000, "scripts/quality/check_quality_stage.py": 60,
    "tests/unit/test_quality_dispatcher.py": 100, "scripts/guardrails_check.py": 60,
    "tests/unit/test_guardrails_check.py": 140, ".github/pull_request_template.md": 45,
    "docs/ADR/0064-adversarial-convergence-protocol.md": 160, "docs/QUALITY_GATES.md": 80,
    "docs/ENGINEERING_PROCESS_RCA.md": 80, "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 100,
    "docs/STAGE_ISSUE_PLAN.md": 70, "docs/STATUS.md": 80,
}
ISSUE435_NONFREEZE = frozenset(ISSUE435_CAPS) - {ISSUE435_FREEZE}
ISSUE435_READABILITY_REVIEWED = {"docs/ENGINEERING_PROCESS_RCA.md", "scripts/quality/adversarial_convergence.py", "tests/unit/test_adversarial_convergence.py", "tests/unit/test_quality_dispatcher.py"}
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
    region, suffix = rest.split(end_marker)
    return prefix + start_marker + b"<C4_EXECUTOR_REGION>\n" + end_marker + suffix if len(region.splitlines()) <= 240 else None
def _hex_text(value: JsonValue, width: int) -> bool:
    return isinstance(value, str) and len(value) == width and all(character in "0123456789abcdef" for character in value)
def _identity(name: str, email: str) -> tuple[str, str] | None:
    if not name.isascii() or not email.isascii() or not name.isprintable() or not email.isprintable() or "<" in name or ">" in name:
        return None
    normalized = " ".join(name.split()).casefold(), email.strip().casefold()
    rendered = f"{normalized[0]} <{normalized[1]}>"
    return normalized if len(rendered) <= 160 and IDENTITY_PATTERN.fullmatch(rendered) is not None else None
def _canonical_identity(value: JsonValue) -> tuple[str, str] | None:
    if not isinstance(value, str) or not 1 <= len(value) <= 160 or not value.endswith(">") or " <" not in value:
        return None
    identity = _identity(*value[:-1].rsplit(" <", 1))
    return identity if identity is not None and value == f"{identity[0]} <{identity[1]}>" else None
def _pass_content(role: str, head: str, tree: str, reviewer: str, url: str) -> str:
    return f"ISSUE435_REVIEW_V1\nrole={role}\ndisposition=PASS\nhead={head}\ntree={tree}\nreviewer={reviewer}\nurl={url}"
def _closed_freeze_shape(document: JsonValue) -> bool:
    top = {"schemaVersion", "issue", "activation", "authorityEffect", "correction", "c2", "artifacts", "reviews"}
    if not isinstance(document, dict) or set(document) != top or document.get("schemaVersion") != "AdversarialConvergenceRedFreezeV1" or document.get("issue") != 435 or document.get("activation") != ACTIVATION or document.get("authorityEffect") != AUTHORITY_EFFECT:
        return False
    correction, c2, artifacts, reviews = (document.get(key) for key in ("correction", "c2", "artifacts", "reviews"))
    if not isinstance(correction, dict) or set(correction) != {"rejectedHead", "wave", "authors"} or correction.get("rejectedHead") != ISSUE435_REJECTED or type(correction.get("wave")) is not int or correction.get("wave") != 1 or not isinstance(c2, dict) or set(c2) != {"head", "tree", "diffSha256"} or not isinstance(artifacts, dict) or set(artifacts) != set(FREEZE_ARTIFACT_PATHS) or not isinstance(reviews, list) or len(reviews) != 4:
        return False
    authors = correction.get("authors")
    if not isinstance(authors, list) or not 1 <= len(authors) <= 8 or any(_canonical_identity(item) is None for item in authors) or len(set(cast(list[str], authors))) != len(authors):
        return False
    if not _hex_text(c2.get("head"), 40) or not _hex_text(c2.get("tree"), 40) or not _hex_text(c2.get("diffSha256"), 64):
        return False
    for name, item in artifacts.items():
        extra = {"semanticSha256"} if name == "corpus" else {"protectedSha256"} if name == "skeleton" else set()
        if not isinstance(item, dict) or set(item) != {"path", "blob", "sha256"} | extra or item.get("path") != FREEZE_ARTIFACT_PATHS[name] or not _hex_text(item.get("blob"), 40) or not _hex_text(item.get("sha256"), 64) or any(not _hex_text(item.get(key), 64) for key in extra):
            return False
    keys = {"role", "reviewer", "disposition", "head", "tree", "url", "content", "contentSha256"}
    prefix = "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-"
    for index, receipt in enumerate(reviews):
        if not isinstance(receipt, dict) or set(receipt) != keys:
            return False
        role, reviewer, url, content = (receipt.get(key) for key in ("role", "reviewer", "url", "content"))
        suffix = url.removeprefix(prefix) if isinstance(url, str) and url.startswith(prefix) else ""
        if role != FREEZE_ROLES[index] or _canonical_identity(reviewer) is None or receipt.get("disposition") != "PASS" or receipt.get("head") != c2.get("head") or receipt.get("tree") != c2.get("tree") or not suffix or suffix.startswith("0") or any(character not in "0123456789" for character in suffix) or not isinstance(content, str) or not 1 <= len(content) <= 8192:
            return False
        expected = _pass_content(role, cast(str, c2["head"]), cast(str, c2["tree"]), cast(str, reviewer), cast(str, url))
        if content != expected or not _hex_text(receipt.get("contentSha256"), 64) or hashlib.sha256(expected.encode("ascii")).hexdigest() != receipt.get("contentSha256"):
            return False
    return len({cast(str, cast(dict[str, JsonValue], receipt)["url"]) for receipt in reviews}) == 4
def _review_provenance(document: JsonValue, candidate_authors: tuple[str, ...]) -> bool:
    if not isinstance(document, dict) or not isinstance(document.get("correction"), dict) or not isinstance(document.get("reviews"), list):
        return False
    correction = cast(dict[str, JsonValue], document["correction"])
    reviews = cast(list[JsonValue], document["reviews"])
    declared = correction.get("authors")
    identities = [_canonical_identity(receipt.get("reviewer")) for receipt in reviews if isinstance(receipt, dict)]
    author_identities = [_canonical_identity(author) for author in candidate_authors]
    if not isinstance(declared, list) or tuple(declared) != candidate_authors or len(identities) != 4 or any(item is None for item in identities + author_identities):
        return False
    reviewers = cast(list[tuple[str, str]], identities)
    authors = cast(list[tuple[str, str]], author_identities)
    return len({item[0] for item in reviewers}) == len({item[1] for item in reviewers}) == 4 and all(name != author_name and email != author_email for name, email in reviewers for author_name, author_email in authors)
def _candidate_authors(root: Path, c2_head: str) -> tuple[str, ...] | None:
    result = _git(root, "log", "--no-show-signature", "--no-notes", "--reverse", "-z", "--format=%H%x00%an%x00%ae", f"{ISSUE435_BASE}..{c2_head}", "--")
    text = _text(result)
    if text is None or len(result.stdout) > 8_192 or not text.endswith("\0"):
        return None
    fields = text[:-1].split("\0")
    if len(fields) % 3 or fields[::3] != [*ISSUE435_HISTORY, c2_head]:
        return None
    identities = [_identity(fields[index], fields[index + 1]) for index in range(1, len(fields), 3)]
    if any(identity is None for identity in identities):
        return None
    rendered = [f"{identity[0]} <{identity[1]}>" for identity in cast(list[tuple[str, str]], identities)]
    return tuple(dict.fromkeys(rendered))
def _valid_freeze(document: JsonValue, root: Path, head: str) -> bool:
    if not _closed_freeze_shape(document) or not isinstance(document, dict):
        return False
    c2 = cast(dict[str, JsonValue], document["c2"])
    artifacts = cast(dict[str, JsonValue], document["artifacts"])
    c2_head, c2_tree = cast(str, c2["head"]), cast(str, c2["tree"])
    candidate_authors = _candidate_authors(root, c2_head)
    if candidate_authors is None or not _review_provenance(document, candidate_authors):
        return False
    tree = _text(_git(root, "rev-parse", f"{c2_head}^{{tree}}"))
    if tree is None or tree.strip() != c2_tree:
        return False
    diff = _git(root, "diff", "--binary", "--full-index", ISSUE435_BASE, c2_head, "--")
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
def _budget_code(path: str, charged: int, readability_reviewed: bool) -> FindingCode | None: return FindingCode.BUDGET_STOP if charged * 10 >= ISSUE435_CAPS.get(path, 0) * 9 else FindingCode.BUDGET_REVIEW_REQUIRED if charged * 20 >= ISSUE435_CAPS.get(path, 0) * 17 and not readability_reviewed else None
def _aggregate_over_budget(charged: int, freeze_present: bool) -> bool: return charged > (3_620 if freeze_present else 3_500)
def _route_head(root: Path, branch: str) -> str:
    ambient = _text(_git(root, "rev-parse", "HEAD"))
    local = _text(_git(root, "branch", "--show-current"))
    if ambient is None or local is None:
        return ""
    head = ambient.strip()
    event_branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    event_base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    event_head = os.environ.get("GITHUB_HEAD_SHA", "").strip()
    if not any((event_branch, event_base, event_head)):
        return head
    parents = _text(_git(root, "rev-list", "--parents", "-n", "1", head))
    fields = parents.split() if parents is not None else []
    valid = branch == event_branch == ISSUE435_BRANCH and event_base == ISSUE435_BASE and _hex_text(event_head, 40)
    return event_head if valid and not local.strip() and fields == [head, event_base, event_head] else ""
def inspect_issue435_repository(root: Path, branch: str) -> RouteInspection:
    if branch != ISSUE435_BRANCH:
        return RouteInspection("UNKNOWN", (FindingCode.ROUTE_DRIFT,), 0)
    head = _route_head(root, branch)
    if not head:
        return RouteInspection("UNKNOWN", (FindingCode.IDENTITY_MISMATCH,), 0)
    commands = {
        "history": _git(root, "rev-list", "--reverse", f"{ISSUE435_BASE}..{head}"),
        "merges": _git(root, "rev-list", "--min-parents=2", f"{ISSUE435_BASE}..{head}"),
        "preflight": _git(root, "rev-parse", f"{head}:{ISSUE435_PREFLIGHT}"),
        "status": _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
    }
    values = {key: _text(value) for key, value in commands.items()}
    if any(value is None for value in values.values()):
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    commits = cast(str, values["history"]).splitlines()
    changes = _collect_changes(root, head)
    if changes is None:
        return RouteInspection("UNKNOWN", (FindingCode.PLATFORM_FAILURE,), 0)
    paths = {item.path for item in changes}
    freeze_present = ISSUE435_FREEZE in paths
    expected = set(ISSUE435_CAPS if freeze_present else ISSUE435_NONFREEZE)
    charged = sum(item.additions + item.deletions for item in changes)
    findings: list[FindingCode] = []
    if commits[:len(ISSUE435_HISTORY)] != list(ISSUE435_HISTORY):
        findings.append(FindingCode.IDENTITY_MISMATCH)
    if cast(str, values["merges"]).strip() or cast(str, values["status"]) or cast(str, values["preflight"]).strip() != ISSUE435_PREFLIGHT_BLOB:
        findings.append(FindingCode.ROUTE_DRIFT)
    if paths != expected or any(item.status not in {"A", "M"} or item.mode != "100644" for item in changes):
        findings.append(FindingCode.ROUTE_DRIFT)
    budget_codes = [_budget_code(item.path, item.additions + item.deletions, item.path in ISSUE435_READABILITY_REVIEWED) for item in changes]
    if FindingCode.BUDGET_STOP in budget_codes:
        findings.append(FindingCode.BUDGET_STOP)
    elif FindingCode.BUDGET_REVIEW_REQUIRED in budget_codes:
        findings.append(FindingCode.BUDGET_REVIEW_REQUIRED)
    if _aggregate_over_budget(charged, freeze_present):
        findings.append(FindingCode.BUDGET_STOP)
    phase = "C2"
    if not freeze_present:
        parent = _text(_git(root, "rev-parse", f"{head}^"))
        if len(commits) != 24 or commits[-1] != head or parent is None or parent.strip() != ISSUE435_FALSE_RED_C2:
            findings.append(FindingCode.ROUTE_DRIFT)
    else:
        raw = _git(root, "show", f"{head}:{ISSUE435_FREEZE}")
        parsed = parse_json_bytes(raw.stdout, hashlib.sha256(raw.stdout).hexdigest(), ParseLimits(65_536, 32, 4_096)) if raw.state == "OK" and not raw.returncode else ParseResult(None, (), "")
        if parsed.document is None or not _valid_freeze(parsed.document, root, head):
            findings.append(FindingCode.REVIEW_IDENTITY_MISMATCH)
        c2_value = parsed.document.get("c2") if isinstance(parsed.document, dict) else None
        c2_head = c2_value.get("head") if isinstance(c2_value, dict) else ""
        if len(commits) == 25 and commits[23] == c2_head:
            phase = "C3"
            delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[24]))
            if delta is None or delta.splitlines() != [ISSUE435_FREEZE]:
                findings.append(FindingCode.ROUTE_DRIFT)
        elif len(commits) == 26 and commits[23] == c2_head:
            phase = "C4"
            c3_delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[24]))
            c4_delta = _text(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits[25]))
            if c3_delta is None or c3_delta.splitlines() != [ISSUE435_FREEZE] or c4_delta is None or c4_delta.splitlines() != ["scripts/quality/adversarial_convergence.py"]:
                findings.append(FindingCode.ROUTE_DRIFT)
        else:
            findings.append(FindingCode.ROUTE_DRIFT)
    return RouteInspection(phase, tuple(dict.fromkeys(findings)), charged)
def _resolve_branch(event: str, local: str) -> str: return "" if event and local and event != local else event or local
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
