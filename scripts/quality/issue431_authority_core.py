#!/usr/bin/env python3
"""Fail-closed Child A schema, canonicalization, matrix, and route gate."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "cut1-process-431-authority-core-schemas-state-matrices"
BASE = "4d239942eeda0c0b6c385b2d85dae873af076aa6"
FIRST_COMMIT = "7a5594357c24ac864c850a2e1cb92f9cd8acb940"
LIMIT = 4_000
MAX_BYTES = 131_072
MAX_DEPTH = 12
MAX_COLLECTION = 128
MAX_MEMBERS = 64
MAX_STRING = 2_048
SUPPORTED_SCHEMAS = {
    "MasterProgramAuthorityDecisionV1": (
        "docs/governance/schemas/master-program-authority-decision-v1.schema.json"
    ),
    "Cut1AuthorityManifestV1": "docs/governance/schemas/cut1-authority-manifest-v1.schema.json",
    "ActiveProgramRouteV1": "docs/governance/schemas/active-program-route-v1.schema.json",
}
MATRIX_PATH = "docs/governance/authority-core-state-matrices-v1.json"
ARTIFACT_SHA256 = {
    "docs/governance/schemas/master-program-authority-decision-v1.schema.json": "9bd0d4328b5966ba1029f0d62032fe540d1d838386ed52eeee24490d702626cc",
    "docs/governance/schemas/cut1-authority-manifest-v1.schema.json": "455a051ed9cc966b68457149a0a9f3883b3f0fea251c5120970e3af5e99abfa5",
    "docs/governance/schemas/active-program-route-v1.schema.json": "e7a094a4351ab4342eef9db68868a3204395443e259c7d9184108f8a98033175",
    MATRIX_PATH: "8bf72f95444887b0a0c92f7cdb31dc00ffbf86409504060fa3029321b08d7206",
}
FALSE_AUTHORITY_SOURCES = ("ISSUE", "COMMENT", "FILE", "FIXTURE", "TEST", "CI")
DECISION_STATES = (
    "PROPOSED",
    "REVIEWED",
    "OWNER_APPROVED",
    "MERGED",
    "ACCEPTED_CURRENT",
    "REJECTED",
    "SUPERSEDED",
    "REVOKED",
    "EXPIRED",
)
DECISION_OPERATIONS = (
    "REVIEW",
    "REJECT",
    "OWNER_APPROVE",
    "MERGE",
    "ACCEPT_CURRENT",
    "SUPERSEDE",
    "REVOKE",
    "EXPIRE",
)
DECISION_EDGES = (
    ("D01", "PROPOSED", "REVIEW", "REVIEWED"),
    ("D02", "PROPOSED", "REJECT", "REJECTED"),
    ("D03", "REVIEWED", "OWNER_APPROVE", "OWNER_APPROVED"),
    ("D04", "REVIEWED", "REJECT", "REJECTED"),
    ("D05", "OWNER_APPROVED", "MERGE", "MERGED"),
    ("D06", "OWNER_APPROVED", "REJECT", "REJECTED"),
    ("D07", "MERGED", "ACCEPT_CURRENT", "ACCEPTED_CURRENT"),
    ("D08", "MERGED", "REJECT", "REJECTED"),
    ("D09", "ACCEPTED_CURRENT", "SUPERSEDE", "SUPERSEDED"),
    ("D10", "ACCEPTED_CURRENT", "REVOKE", "REVOKED"),
    ("D11", "ACCEPTED_CURRENT", "EXPIRE", "EXPIRED"),
)
ROUTE_STATES = (
    "DRAFT",
    "REVIEWED",
    "OWNER_APPROVED",
    "PREDECESSOR_VERIFIED",
    "ACTIVE",
    "MERGED",
    "CLOSED",
    "REJECTED",
    "SUPERSEDED",
    "EXECUTION_EXPIRED",
)
ROUTE_OPERATIONS = (
    "REVIEW",
    "REJECT",
    "OWNER_APPROVE",
    "VERIFY_PREDECESSOR",
    "ACTIVATE",
    "MERGE",
    "CLOSE",
    "SUPERSEDE",
    "EXPIRE",
)
ROUTE_EDGES = (
    ("R01", "DRAFT", "REVIEW", "REVIEWED"),
    ("R02", "DRAFT", "REJECT", "REJECTED"),
    ("R03", "REVIEWED", "OWNER_APPROVE", "OWNER_APPROVED"),
    ("R04", "REVIEWED", "REJECT", "REJECTED"),
    ("R05", "OWNER_APPROVED", "VERIFY_PREDECESSOR", "PREDECESSOR_VERIFIED"),
    ("R06", "OWNER_APPROVED", "REJECT", "REJECTED"),
    ("R07", "PREDECESSOR_VERIFIED", "ACTIVATE", "ACTIVE"),
    ("R08", "PREDECESSOR_VERIFIED", "REJECT", "REJECTED"),
    ("R09", "ACTIVE", "MERGE", "MERGED"),
    ("R10", "MERGED", "CLOSE", "CLOSED"),
    ("R11", "DRAFT", "SUPERSEDE", "SUPERSEDED"),
    ("R12", "REVIEWED", "SUPERSEDE", "SUPERSEDED"),
    ("R13", "OWNER_APPROVED", "SUPERSEDE", "SUPERSEDED"),
    ("R14", "PREDECESSOR_VERIFIED", "SUPERSEDE", "SUPERSEDED"),
    ("R15", "ACTIVE", "SUPERSEDE", "SUPERSEDED"),
    ("R16", "DRAFT", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R17", "REVIEWED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R18", "OWNER_APPROVED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R19", "PREDECESSOR_VERIFIED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R20", "ACTIVE", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R21", "EXECUTION_EXPIRED", "CLOSE", "CLOSED"),
)
ROW_ACTORS = {
    **{row: "REPOSITORY_OWNER" for row in ("D02", "D03", "D04", "D06", "D08", "D10")},
    **{
        row: "REPOSITORY_OWNER"
        for row in ("R02", "R03", "R04", "R06", "R08", "R11", "R12", "R13", "R14", "R15")
    },
    "D01": "INDEPENDENT_REVIEWER",
    "D05": "MERGE_COORDINATOR",
    "D07": "AUTHORITY_ACCEPTOR",
    "D09": "AUTHORITY_ACCEPTOR",
    "D11": "EXPIRY_EVALUATOR",
    "R01": "INDEPENDENT_REVIEWER",
    "R05": "PREDECESSOR_VERIFIER",
    "R07": "ROUTE_ACTIVATOR",
    "R09": "MERGE_COORDINATOR",
    "R10": "CLOSEOUT_COORDINATOR",
    "R21": "CLOSEOUT_COORDINATOR",
    **{f"R{number:02d}": "EXPIRY_EVALUATOR" for number in range(16, 21)},
}
ROW_REFERENCES = {
    "D01": ("CANDIDATE_HASH", "SCHEMA_CANONICAL_PASS", "REVIEW_SUBJECT"),
    "D02": ("CANDIDATE_HASH", "REJECTION_REASON"),
    "D03": ("REVIEWED_HASH", "REVIEW_DISPOSITIONS", "APPROVAL_SUBJECT"),
    "D04": ("REVIEWED_HASH", "REJECTION_REASON"),
    "D05": ("APPROVED_HASH", "MERGE_REFERENCE", "EXACT_HEAD_OWNER_APPROVAL"),
    "D06": ("APPROVED_HASH", "WITHDRAWAL_OR_REJECTION"),
    "D07": (
        "MERGE_REFERENCE",
        "MERGED_MAIN_CHECK",
        "ISSUE_DISPOSITION",
        "VALIDITY_OBSERVATION",
        "DECISION_MANIFEST_LINKS",
    ),
    "D08": ("MERGED_HASH", "FAILED_ACCEPTANCE", "NO_CURRENT_ACCEPTANCE"),
    "D09": ("CURRENT_HASH", "ACCEPTED_SUCCESSOR", "RECIPROCAL_LINKAGE"),
    "D10": ("CURRENT_HASH", "REVOCATION_REFERENCE", "EFFECTIVE_TIME"),
    "D11": ("CURRENT_HASH", "TIME_OBSERVATION", "EXPIRY_THRESHOLD"),
    "R01": ("ROUTE_HASH", "SCHEMA_CANONICAL_PASS", "REVIEW_SUBJECT"),
    "R02": ("ROUTE_HASH", "REJECTION_REASON"),
    "R03": ("REVIEWED_HASH", "REVIEW_DISPOSITIONS", "APPROVAL_SUBJECT"),
    "R04": ("REVIEWED_HASH", "REJECTION_REASON"),
    "R05": ("APPROVED_HASH", "PREDECESSOR_MERGE", "PREDECESSOR_TREE", "MERGED_MAIN_CHECK"),
    "R06": ("APPROVED_HASH", "WITHDRAWAL_OR_REJECTION"),
    "R07": (
        "ACCEPTED_DECISION",
        "ACCEPTED_MANIFEST",
        "PREDECESSOR_VERIFICATION",
        "ROUTE_BOUNDARIES",
        "EXECUTION_DEADLINE_OBSERVATION",
    ),
    "R08": ("VERIFIED_HASH", "REJECTION_REASON"),
    "R09": (
        "ACTIVE_HASH",
        "EXACT_HEAD_APPROVALS",
        "PROTECTED_CHECK_TUPLES",
        "MERGE_REFERENCE",
        "EXECUTION_DEADLINE_OBSERVATION",
    ),
    "R10": ("MERGED_HASH", "MERGED_MAIN_CHECK", "STATUS_ISSUE_BRANCH_CLEANUP"),
    **{
        f"R{number:02d}": ("SOURCE_HASH", "REPLACEMENT_ROUTE", "NO_GOVERNED_MUTATION")
        for number in range(11, 16)
    },
    **{
        f"R{number:02d}": ("SOURCE_HASH", "TIME_OBSERVATION", "EXECUTION_DEADLINE")
        for number in range(16, 21)
    },
    "R21": ("EXPIRED_HASH", "ADMINISTRATIVE_CLOSEOUT", "NO_GOVERNED_MUTATION"),
}
SCHEMA_DOCUMENT_KEYS = {
    "$defs",
    "activation",
    "canonicalProfile",
    "closed",
    "contractVersion",
    "root",
    "schemaDocumentVersion",
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
TIMESTAMP_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
ORIGINAL_PATHS = (
    "docs/governance/preflights/issue-431.json",
    "docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md",
    "docs/governance/schemas/master-program-authority-decision-v1.schema.json",
    "docs/governance/schemas/cut1-authority-manifest-v1.schema.json",
    "docs/governance/schemas/active-program-route-v1.schema.json",
    "docs/governance/authority-core-state-matrices-v1.json",
    "tests/fixtures/authority-core-v1-cases.json",
    "scripts/quality/issue431_authority_core.py",
    "tests/unit/test_issue431_authority_core.py",
    "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/ADR/0061-core-authority-schemas-state-matrices.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
)
AMENDMENT_PATHS = (
    "scripts/quality/issue427_architecture_reset.py",
    "tests/unit/test_issue427_architecture_reset.py",
)
PATHS = (*ORIGINAL_PATHS, *AMENDMENT_PATHS)


class AuthorityValidationError(ValueError):
    """Stable fail-closed validation error with a machine-readable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def canonical_bytes(value: Any) -> bytes:
    """Produce the bounded ASCII-only Child A canonical JSON representation."""

    _check_value(value, 1)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _check_value(value: Any, depth: int) -> None:
    if depth > MAX_DEPTH:
        raise AuthorityValidationError("DEPTH_LIMIT")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not -(2**63) <= value <= 2**63 - 1:
            raise AuthorityValidationError("INTEGER_RANGE")
        return
    if isinstance(value, float):
        code = "FLOAT_PROHIBITED" if math.isfinite(value) else "NON_FINITE_NUMBER"
        raise AuthorityValidationError(code)
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_STRING:
            raise AuthorityValidationError("STRING_LIMIT")
        if any(ord(char) < 0x20 or ord(char) > 0x7E for char in value):
            raise AuthorityValidationError("NON_ASCII_STRING")
        return
    if isinstance(value, list):
        if len(value) > MAX_COLLECTION:
            raise AuthorityValidationError("COLLECTION_LIMIT")
        for item in value:
            _check_value(item, depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_MEMBERS:
            raise AuthorityValidationError("MEMBER_LIMIT")
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuthorityValidationError("NON_STRING_MEMBER")
            _check_value(key, depth + 1)
            _check_value(item, depth + 1)
        return
    raise AuthorityValidationError("UNSUPPORTED_SCALAR")


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AuthorityValidationError("DUPLICATE_MEMBER", key)
        value[key] = item
    return value


def _reject_float(_: str) -> None:
    raise AuthorityValidationError("FLOAT_PROHIBITED")


def _reject_constant(_: str) -> None:
    raise AuthorityValidationError("NON_FINITE_NUMBER")


def _parse_json(data: bytes) -> Any:
    if len(data) > MAX_BYTES:
        raise AuthorityValidationError("SIZE_LIMIT")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise AuthorityValidationError("INVALID_UTF8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_members,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except AuthorityValidationError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise AuthorityValidationError("MALFORMED_JSON") from error
    encoded = canonical_bytes(value)
    if data != encoded:
        raise AuthorityValidationError("NONCANONICAL_BYTES")
    return value


def _read_schema(path: Path, expected_schema: str) -> dict[str, Any]:
    try:
        value = json.loads(_bounded_text(path), object_pairs_hook=_reject_duplicate_members)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityValidationError("SCHEMA_UNAVAILABLE") from error
    if not isinstance(value, dict) or set(value) != SCHEMA_DOCUMENT_KEYS:
        raise AuthorityValidationError("SCHEMA_DOCUMENT_OPEN")
    if (
        value["schemaDocumentVersion"] != "NarraTwinClosedSchemaDocumentV1"
        or value["contractVersion"] != expected_schema
        or value["canonicalProfile"] != "NarraTwinAuthorityCanonicalJsonV1"
        or value["closed"] is not True
        or value["activation"] != "NONE"
    ):
        raise AuthorityValidationError("SCHEMA_DOCUMENT_MISMATCH")
    return value


def _wrong_type(value: Any, expected: str) -> None:
    actual = type(value).__name__
    raise AuthorityValidationError("WRONG_SCALAR_TYPE", f"expected {expected}, got {actual}")


def _validate_descriptor(
    value: Any, descriptor: dict[str, Any], definitions: dict[str, Any]
) -> None:
    if "$ref" in descriptor:
        reference = descriptor["$ref"]
        if reference not in definitions:
            raise AuthorityValidationError("SCHEMA_REFERENCE_UNKNOWN")
        _validate_descriptor(value, definitions[reference], definitions)
        required_type = descriptor.get("referenceType")
        if required_type is not None and value.get("referenceType") != required_type:
            raise AuthorityValidationError("REFERENCE_TYPE_MISMATCH")
        return
    kind = descriptor.get("type")
    if kind == "nullable":
        if value is not None:
            _validate_descriptor(value, descriptor["item"], definitions)
        return
    if kind in {"string", "sha256", "gitSha", "timestamp"}:
        if not isinstance(value, str):
            _wrong_type(value, "string")
        if kind == "sha256" and not SHA256_PATTERN.fullmatch(value):
            raise AuthorityValidationError("SHA256_FORMAT")
        if kind == "gitSha" and not GIT_SHA_PATTERN.fullmatch(value):
            raise AuthorityValidationError("GIT_SHA_FORMAT")
        if kind == "timestamp":
            if not TIMESTAMP_PATTERN.fullmatch(value):
                raise AuthorityValidationError("TIMESTAMP_FORMAT")
            try:
                datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            except ValueError as error:
                raise AuthorityValidationError("TIMESTAMP_FORMAT") from error
        pattern = descriptor.get("pattern")
        if pattern and re.fullmatch(pattern, value) is None:
            raise AuthorityValidationError("STRING_PATTERN")
        if len(value.encode("utf-8")) > descriptor.get("maxBytes", MAX_STRING):
            raise AuthorityValidationError("STRING_LIMIT")
    elif kind == "integer":
        if type(value) is not int:
            _wrong_type(value, "integer")
        if value < descriptor.get("minimum", -(2**63)) or value > descriptor.get(
            "maximum", 2**63 - 1
        ):
            raise AuthorityValidationError("INTEGER_RANGE")
    elif kind == "boolean":
        if type(value) is not bool:
            _wrong_type(value, "boolean")
    elif kind == "object":
        if not isinstance(value, dict):
            _wrong_type(value, "object")
        properties = descriptor.get("properties", {})
        unknown = set(value) - set(properties)
        missing = set(descriptor.get("required", ())) - set(value)
        if unknown:
            raise AuthorityValidationError("UNKNOWN_MEMBER", min(unknown))
        if missing:
            raise AuthorityValidationError("MISSING_MEMBER", min(missing))
        if descriptor.get("closed") is not True:
            raise AuthorityValidationError("SCHEMA_OBJECT_OPEN")
        for key, item in value.items():
            _validate_descriptor(item, properties[key], definitions)
    elif kind == "array":
        if not isinstance(value, list):
            _wrong_type(value, "array")
        if "exactItems" in descriptor and value != descriptor["exactItems"]:
            raise AuthorityValidationError("EXACT_COLLECTION_MISMATCH")
        if len(value) < descriptor.get("minItems", 0) or len(value) > descriptor.get(
            "maxItems", MAX_COLLECTION
        ):
            raise AuthorityValidationError("COLLECTION_LIMIT")
        if descriptor.get("unique") and len({canonical_bytes(item) for item in value}) != len(
            value
        ):
            raise AuthorityValidationError("DUPLICATE_COLLECTION_ITEM")
        if descriptor.get("sorted") and value != sorted(value, key=canonical_bytes):
            raise AuthorityValidationError("COLLECTION_ORDER_MISMATCH")
        if "items" in descriptor:
            for item in value:
                _validate_descriptor(item, descriptor["items"], definitions)
    else:
        raise AuthorityValidationError("SCHEMA_TYPE_UNKNOWN")
    if "const" in descriptor and value != descriptor["const"]:
        raise AuthorityValidationError("CONST_MISMATCH")
    if "enum" in descriptor and value not in descriptor["enum"]:
        raise AuthorityValidationError("ENUM_MISMATCH")


def content_hash(value: dict[str, Any]) -> str:
    if not isinstance(value.get("schemaVersion"), str):
        raise AuthorityValidationError("SCHEMA_VERSION_MISMATCH")
    unsigned = dict(value)
    unsigned.pop("contentHash", None)
    domain = b"NARRATWIN-AUTHORITY-OBJECT-V1\0" + value["schemaVersion"].encode("ascii") + b"\0"
    return hashlib.sha256(domain + canonical_bytes(unsigned)).hexdigest()


def _guard_scalar_hash(reference_type: str, value: str) -> str:
    domain = b"NARRATWIN-AUTHORITY-GUARD-V1\0" + reference_type.encode("ascii") + b"\0"
    return hashlib.sha256(domain + value.encode("ascii")).hexdigest()


def _validate_identity(value: dict[str, Any], expected_schema: str) -> None:
    incoming = value.get("schemaVersion")
    if incoming != expected_schema:
        prefix = expected_schema.removesuffix("V1")
        if incoming == f"{prefix}V0":
            raise AuthorityValidationError("DOWNGRADE_REJECTED")
        if isinstance(incoming, str) and incoming.startswith(prefix):
            raise AuthorityValidationError("UNSUPPORTED_VERSION")
        raise AuthorityValidationError("SCHEMA_VERSION_MISMATCH")
    if value.get("repository") != "github.com/imrohitagrawal/narratwin-ai":
        raise AuthorityValidationError("REPOSITORY_MISMATCH")
    if value.get("programId") != "narratwin-cut1":
        raise AuthorityValidationError("PROGRAM_MISMATCH")
    generation = value.get("generationId")
    if (
        not isinstance(generation, str)
        or re.fullmatch(r"generation:[a-z0-9][a-z0-9.-]{0,63}", generation) is None
    ):
        raise AuthorityValidationError("GENERATION_MISMATCH")


def _validate_semantics(value: dict[str, Any]) -> None:
    if value.get("contentHash") != content_hash(value):
        raise AuthorityValidationError("CONTENT_HASH_MISMATCH")
    revision = value["revision"]
    predecessor = value["predecessorContentHash"]
    transition = value["transition"]
    if revision == 1 and (predecessor is not None or transition is not None):
        raise AuthorityValidationError("GENESIS_LINK_MISMATCH")
    initial = "DRAFT" if value["schemaVersion"] == "ActiveProgramRouteV1" else "PROPOSED"
    if (
        revision == 1
        and value["lifecycleState"] != initial
        and value["schemaVersion"] != "ActiveProgramRouteV1"
    ):
        raise AuthorityValidationError("INITIAL_STATE_MISMATCH")
    if revision > 1 and (predecessor is None or transition is None):
        raise AuthorityValidationError("PREDECESSOR_REQUIRED")
    if predecessor == value["contentHash"]:
        raise AuthorityValidationError("CYCLIC_LINK")
    validity = value["validity"]
    if validity["notBefore"] >= validity["expiresAt"]:
        raise AuthorityValidationError("VALIDITY_ORDER")
    if (validity["revokedAt"] is None) != (validity["revocationReference"] is None):
        raise AuthorityValidationError("REVOCATION_LINK_MISMATCH")
    if (value["lifecycleState"] == "REVOKED") != (validity["revokedAt"] is not None):
        raise AuthorityValidationError("REVOCATION_STATE_MISMATCH")
    schema = value["schemaVersion"]
    if schema == "MasterProgramAuthorityDecisionV1":
        selected = value["decisionAction"] in {"SELECT_MANIFEST", "SUPERSEDE_CURRENT"}
        if (value["selectedManifest"] is not None) != selected:
            raise AuthorityValidationError("ACTION_LINK_MISMATCH")
        prior = value["decisionAction"] in {"SUPERSEDE_CURRENT", "REVOKE_CURRENT"}
        if (value["priorDecision"] is not None) != prior:
            raise AuthorityValidationError("ACTION_LINK_MISMATCH")
        _require_reference(value["sourceProposal"], "PROPOSAL")
        _require_reference(value["selectedManifest"], "MANIFEST", nullable=True)
        _require_reference(value["priorDecision"], "DECISION", nullable=True)
        if value["lifecycleState"] == "ACCEPTED_CURRENT" and value["selectedManifest"] is None:
            raise AuthorityValidationError("ACTION_LINK_MISMATCH")
    elif schema == "Cut1AuthorityManifestV1":
        _require_reference(value["sourceProposal"], "PROPOSAL")
        accepted = value["lifecycleState"] in {
            "ACCEPTED_CURRENT",
            "SUPERSEDED",
            "REVOKED",
            "EXPIRED",
        }
        if (value["decisionBacklink"] is not None) != accepted:
            raise AuthorityValidationError("MANIFEST_BACKLINK_STATE_MISMATCH")
        _require_reference(value["decisionBacklink"], "DECISION", nullable=True)
    else:
        _validate_route_semantics(value)
        if revision == 1 and value["lifecycleState"] != initial:
            raise AuthorityValidationError("INITIAL_STATE_MISMATCH")


def _require_reference(value: Any, expected: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, dict) or value.get("referenceType") != expected:
        raise AuthorityValidationError("REFERENCE_TYPE_MISMATCH")


def _validate_route_semantics(value: dict[str, Any]) -> None:
    _require_reference(value["decision"], "DECISION")
    _require_reference(value["selectedManifest"], "MANIFEST")
    _require_reference(value.get("supersededRoute"), "ROUTE", nullable=True)
    state = value["lifecycleState"]
    if state in {"ACTIVE", "MERGED"} and value["pullRequest"] is None:
        raise AuthorityValidationError("ROUTE_PR_STATE_MISMATCH")
    expired = value["executionWindow"]["expired"]
    if (state == "EXECUTION_EXPIRED" and not expired) or (
        state not in {"EXECUTION_EXPIRED", "CLOSED"} and expired
    ):
        raise AuthorityValidationError("EXECUTION_EXPIRY_MISMATCH")
    if (state == "SUPERSEDED") != (value.get("supersededRoute") is not None):
        raise AuthorityValidationError("ROUTE_SUPERSESSION_MISMATCH")
    paths = value["allowedPaths"]
    if value["maxPathCount"] != len(paths):
        raise AuthorityValidationError("PATH_COUNT_MISMATCH")
    for path in paths:
        parts = path.split("/")
        if path.startswith("/") or "" in parts or "." in parts or ".." in parts:
            raise AuthorityValidationError("REPOSITORY_PATH_INVALID")
        if len(path.encode("utf-8")) > 512:
            raise AuthorityValidationError("REPOSITORY_PATH_INVALID")
    window = value["executionWindow"]
    if window["approvedAt"] >= window["expiresAt"]:
        raise AuthorityValidationError("EXECUTION_WINDOW_ORDER")


def validate_authority_bytes(data: bytes, expected_schema: str) -> dict[str, Any]:
    """Parse canonical bytes and validate them against one exact supported schema."""

    if expected_schema not in SUPPORTED_SCHEMAS:
        raise AuthorityValidationError("UNSUPPORTED_VERSION")
    value = _parse_json(data)
    if not isinstance(value, dict):
        raise AuthorityValidationError("WRONG_ROOT_TYPE")
    schema_path = ROOT / SUPPORTED_SCHEMAS[expected_schema]
    if not schema_path.is_file():
        raise AuthorityValidationError("SCHEMA_UNAVAILABLE")
    schema = _read_schema(schema_path, expected_schema)
    _validate_identity(value, expected_schema)
    _validate_descriptor(value, schema["root"], schema["$defs"])
    _validate_semantics(value)
    return value


def matrix_findings(document: dict[str, Any]) -> list[str]:
    """Return closed, exhaustive, exact transition matrix defects without throwing."""

    findings: list[str] = []
    try:
        if set(document) != {"activation", "evaluationOutcomes", "matrices", "schemaVersion"}:
            return ["Matrix document root is not closed."]
        if (
            document["schemaVersion"] != "AuthorityCoreStateMatricesV1"
            or document["activation"] != "NONE"
        ):
            findings.append("Matrix version or nonactivation binding mismatches.")
        outcomes = document["evaluationOutcomes"]
        if outcomes != ["UNVERIFIED", "CONFLICTING"]:
            findings.append("Evaluation outcomes are incomplete or reordered.")
        expected = {
            "DecisionManifestLifecycleV1": (DECISION_STATES, DECISION_OPERATIONS, DECISION_EDGES),
            "ActiveProgramRouteLifecycleV1": (ROUTE_STATES, ROUTE_OPERATIONS, ROUTE_EDGES),
        }
        matrices = document["matrices"]
        if not isinstance(matrices, list) or len(matrices) != 2:
            return [*findings, "Matrix collection is incomplete."]
        if {item.get("id") for item in matrices if isinstance(item, dict)} != set(expected):
            findings.append("Matrix identifiers are incomplete or duplicate.")
        for item in matrices:
            if not isinstance(item, dict) or item.get("id") not in expected:
                findings.append("Matrix entry is malformed or unknown.")
                continue
            _matrix_item_findings(item, *expected[item["id"]], findings)
    except (AttributeError, KeyError, TypeError, ValueError):
        findings.append("Matrix document is malformed and rejected.")
    return findings


def lineage_findings(objects: list[dict[str, Any]]) -> list[str]:
    """Validate immutable bytes, unique identities, links, forks, and exact transitions."""

    findings: list[str] = []
    if not objects:
        return ["Lineage is empty."]
    by_hash: dict[str, dict[str, Any]] = {}
    identities: dict[tuple[Any, ...], set[str]] = {}
    successors: dict[str, list[dict[str, Any]]] = {}
    for value in objects:
        if not isinstance(value, dict):
            findings.append("Lineage member is malformed.")
            continue
        schema = value.get("schemaVersion")
        if not isinstance(schema, str):
            findings.append("Lineage schema version is missing.")
            continue
        try:
            validate_authority_bytes(canonical_bytes(value), schema)
        except AuthorityValidationError as error:
            findings.append(f"Lineage content hash or schema defect: {error.code}.")
        object_hash = value.get("contentHash")
        if not isinstance(object_hash, str):
            findings.append("Lineage content hash is missing.")
            continue
        if object_hash in by_hash and by_hash[object_hash] != value:
            findings.append("Two incompatible bytes claim one content hash.")
        by_hash[object_hash] = value
        identity = (
            schema,
            value.get("repository"),
            value.get("programId"),
            value.get("generationId"),
            value.get("objectId"),
            value.get("revision"),
        )
        identities.setdefault(identity, set()).add(object_hash)
        predecessor_hash = value.get("predecessorContentHash")
        if isinstance(predecessor_hash, str):
            successors.setdefault(predecessor_hash, []).append(value)
            if predecessor_hash == object_hash:
                findings.append("Cyclic predecessor hash is prohibited.")
    if any(len(hashes) > 1 for hashes in identities.values()):
        findings.append("Immutable identity collision has incompatible objects.")
    if any(len(items) > 1 for items in successors.values()):
        findings.append("Forked successors claim one predecessor hash.")
    for value in objects:
        if not isinstance(value, dict) or value.get("revision") == 1:
            continue
        predecessor_hash = value.get("predecessorContentHash")
        predecessor = by_hash.get(predecessor_hash) if isinstance(predecessor_hash, str) else None
        if predecessor is None:
            findings.append("Unlinked successor predecessor is absent.")
            continue
        stable = ("schemaVersion", "repository", "programId", "generationId", "objectId")
        if any(value.get(key) != predecessor.get(key) for key in stable):
            findings.append("Successor immutable identity differs from predecessor.")
        if value.get("revision") != predecessor.get("revision", 0) + 1:
            findings.append("Successor revision is not exactly predecessor plus one.")
        _lineage_transition_findings(predecessor, value, by_hash, findings)
        transition = value.get("transition")
        operation = transition.get("operation") if isinstance(transition, dict) else None
        if _stable_payload(predecessor, operation) != _stable_payload(value, operation):
            findings.append("Successor immutable payload differs from predecessor.")
    if len({item.get("schemaVersion") for item in objects if isinstance(item, dict)}) > 1:
        _cross_contract_findings(objects, by_hash, findings)
    return findings


def _stable_payload(value: dict[str, Any], operation: Any) -> dict[str, Any]:
    payload = deepcopy(value)
    for key in (
        "contentHash",
        "lifecycleState",
        "predecessorContentHash",
        "revision",
        "transition",
    ):
        payload.pop(key, None)
    if operation == "EXPIRE" and payload.get("schemaVersion") == "ActiveProgramRouteV1":
        payload["executionWindow"].pop("expired", None)
    if operation == "ACTIVATE":
        payload.pop("pullRequest", None)
    if operation == "SUPERSEDE" and payload.get("schemaVersion") == "ActiveProgramRouteV1":
        payload.pop("supersededRoute", None)
    if operation == "REVOKE":
        payload["validity"].pop("revokedAt", None)
        payload["validity"].pop("revocationReference", None)
    if operation == "ACCEPT_CURRENT" and payload.get("schemaVersion") == "Cut1AuthorityManifestV1":
        payload.pop("decisionBacklink", None)
    return payload


def _cross_contract_findings(
    objects: list[dict[str, Any]],
    by_hash: dict[str, dict[str, Any]],
    findings: list[str],
) -> None:
    schemas = {
        "DECISION": "MasterProgramAuthorityDecisionV1",
        "MANIFEST": "Cut1AuthorityManifestV1",
        "ROUTE": "ActiveProgramRouteV1",
    }

    def resolve(owner: dict[str, Any], field: str) -> dict[str, Any] | None:
        reference = owner.get(field)
        if reference is None:
            return None
        if not isinstance(reference, dict):
            findings.append(f"Cross-contract {field} reference is malformed.")
            return None
        reference_type = reference.get("referenceType")
        reference_hash = reference.get("sha256")
        expected_schema = schemas.get(reference_type) if isinstance(reference_type, str) else None
        target = by_hash.get(reference_hash) if isinstance(reference_hash, str) else None
        if (
            expected_schema is None
            or target is None
            or target.get("schemaVersion") != expected_schema
            or reference.get("subject") != target.get("objectId")
        ):
            findings.append(
                f"Cross-contract {field} reference for {reference.get('subject')} is unresolved."
            )
            return None
        for identity in ("repository", "programId", "generationId"):
            if owner.get(identity) != target.get(identity):
                findings.append(
                    f"Cross-contract {field} {identity} disagrees for {reference.get('subject')}."
                )
        return target

    def ancestor_in_state(value: dict[str, Any], state: str) -> dict[str, Any] | None:
        current: dict[str, Any] | None = value
        visited: set[str] = set()
        while current is not None:
            current_hash = current.get("contentHash")
            if not isinstance(current_hash, str) or current_hash in visited:
                return None
            visited.add(current_hash)
            if current.get("lifecycleState") == state:
                return current
            predecessor_hash = current.get("predecessorContentHash")
            current = by_hash.get(predecessor_hash) if isinstance(predecessor_hash, str) else None
        return None

    for value in objects:
        schema = value.get("schemaVersion")
        if schema == "MasterProgramAuthorityDecisionV1":
            selected_manifest = resolve(value, "selectedManifest")
            if (
                value.get("lifecycleState")
                in {"ACCEPTED_CURRENT", "SUPERSEDED", "REVOKED", "EXPIRED"}
                and selected_manifest is not None
                and selected_manifest.get("lifecycleState") != "MERGED"
            ):
                findings.append(
                    f"Cross-contract selected manifest lifecycle is not MERGED for {value.get('objectId')}."
                )
            resolve(value, "priorDecision")
        elif schema == "Cut1AuthorityManifestV1":
            decision = resolve(value, "decisionBacklink")
            if decision is not None:
                if decision.get("lifecycleState") != "ACCEPTED_CURRENT":
                    findings.append(
                        f"Cross-contract accepted decision lifecycle mismatches for {value.get('objectId')}."
                    )
                accepted_ancestor = ancestor_in_state(value, "ACCEPTED_CURRENT")
                selected = decision.get("selectedManifest")
                if (
                    accepted_ancestor is None
                    or not isinstance(selected, dict)
                    or selected.get("subject") != value.get("objectId")
                    or selected.get("sha256")
                    != accepted_ancestor.get("predecessorContentHash")
                ):
                    findings.append(
                        f"Cross-contract reciprocal decision/manifest linkage disagrees for {value.get('objectId')}."
                    )
        elif schema == "ActiveProgramRouteV1":
            decision = resolve(value, "decision")
            manifest = resolve(value, "selectedManifest")
            if decision is not None and manifest is not None:
                if decision.get("lifecycleState") != "ACCEPTED_CURRENT":
                    findings.append(
                        f"Cross-contract accepted decision lifecycle mismatches for {value.get('objectId')}."
                    )
                if manifest.get("lifecycleState") != "ACCEPTED_CURRENT":
                    findings.append(
                        f"Cross-contract accepted manifest lifecycle mismatches for {value.get('objectId')}."
                    )
                backlink = manifest.get("decisionBacklink")
                if (
                    not isinstance(backlink, dict)
                    or backlink.get("sha256") != decision.get("contentHash")
                    or backlink.get("subject") != decision.get("objectId")
                ):
                    findings.append(
                        f"Cross-contract route pair disagrees for {value.get('objectId')}."
                    )


def authority_effect_findings(source: str, claimed_effect: str) -> list[str]:
    """Prove that every Child A marker source has exactly no authority effect."""

    if source not in FALSE_AUTHORITY_SOURCES:
        return ["Unknown authority source is rejected."]
    if claimed_effect != "NONE":
        return [f"{source} cannot produce authority effect {claimed_effect}."]
    return []


def repository_findings(root: Path = ROOT) -> list[str]:
    """Validate Child A artifacts and, on its branch, the exact governed route."""

    findings: list[str] = []
    required = {
        "docs/governance/preflights/issue-431.json",
        "docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md",
        *SUPPORTED_SCHEMAS.values(),
        MATRIX_PATH,
        "tests/fixtures/authority-core-v1-cases.json",
        "scripts/quality/issue431_authority_core.py",
        "tests/unit/test_issue431_authority_core.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0061-core-authority-schemas-state-matrices.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        *AMENDMENT_PATHS,
    }
    if required != set(PATHS):
        findings.append("Child A code-owned path inventory mismatches the approved route.")
    missing = [path for path in PATHS if not (root / path).is_file()]
    findings.extend(f"Child A required path is missing: {path}." for path in missing)
    if missing:
        return findings
    try:
        preflight = _strict_file(root / "docs/governance/preflights/issue-431.json")
        if (
            preflight.get("schema_version") != "GovernancePreflightV1"
            or preflight.get("issue_number") != 431
            or preflight.get("branch") != BRANCH
            or preflight.get("scope", {}).get("required") != list(ORIGINAL_PATHS)
            or preflight.get("scope", {}).get("allowed_prefixes") != list(ORIGINAL_PATHS)
        ):
            findings.append("Child A preflight binding or exact scope mismatches.")
        preflight_bytes = (root / "docs/governance/preflights/issue-431.json").read_bytes()
        if (
            hashlib.sha256(preflight_bytes).hexdigest()
            != "35a241b0ab581e4eb2fdb08bbf4ba4850322ee58bd15b545865e7cc7a7d2832b"
        ):
            findings.append("Child A approved preflight bytes drifted.")
        objective = preflight.get("objective", "")
        for marker in (
            "5296984551",
            "209d4833e655404d05db50f12b1e7d58c8b45bf50c2d33fe08a4964722cc6e72",
            BASE,
            "AK-001/AK-004/AK-012",
            "Activation is NONE",
            "One correction wave only",
        ):
            if marker not in objective:
                findings.append(f"Child A preflight objective is missing {marker}.")
        for schema, relative in SUPPORTED_SCHEMAS.items():
            _read_schema(root / relative, schema)
        if set(ARTIFACT_SHA256) != {*SUPPORTED_SCHEMAS.values(), MATRIX_PATH}:
            findings.append("Child A frozen schema/matrix identity inventory is incomplete.")
        for relative, expected_hash in ARTIFACT_SHA256.items():
            if hashlib.sha256(_bounded_bytes(root / relative)).hexdigest() != expected_hash:
                findings.append(f"Child A frozen artifact bytes drifted: {relative}.")
        matrix = _strict_file(root / MATRIX_PATH)
        findings.extend(matrix_findings(matrix))
        fixture = _strict_file(root / "tests/fixtures/authority-core-v1-cases.json")
        findings.extend(_fixture_findings(fixture))
        findings.extend(fixture_execution_findings(fixture))
    except AuthorityValidationError as error:
        findings.append(f"Child A strict artifact validation failed: {error.code}.")
    spec = _bounded_text(root / "docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md")
    for marker in (
        "CHILD_A_CONTRACT_NONACTIVATING",
        "Activation: `NONE`",
        "AK-001",
        "AK-004",
        "AK-012",
        "NarraTwinAuthorityCanonicalJsonV1",
        "NARRATWIN-AUTHORITY-OBJECT-V1",
        "FIPS 180-4",
        "DecisionManifestLifecycleV1",
        "ActiveProgramRouteLifecycleV1",
        "R16–R20",
        "Child F",
    ):
        if marker not in spec:
            findings.append(f"Child A specification is missing {marker}.")
    stage8_source = _bounded_text(root / "scripts/quality/check_stage8_docs.py")
    if "issue431_authority_core.repository_findings" not in stage8_source:
        findings.append("Stage 8 does not invoke the semantic Child A repository gate.")
    branch = os.environ.get("GITHUB_HEAD_REF", "").strip() or _git(root, "branch", "--show-current")
    if branch == BRANCH:
        findings.extend(_route_findings(root))
    return findings


def _strict_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_bounded_text(path), object_pairs_hook=_reject_duplicate_members)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityValidationError("MALFORMED_JSON", path.as_posix()) from error
    if not isinstance(value, dict):
        raise AuthorityValidationError("WRONG_ROOT_TYPE", path.as_posix())
    return value


def _bounded_bytes(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
    except OSError as error:
        raise AuthorityValidationError("ARTIFACT_UNAVAILABLE", path.as_posix()) from error
    if len(data) > MAX_BYTES:
        raise AuthorityValidationError("SIZE_LIMIT", path.as_posix())
    return data


def _bounded_text(path: Path) -> str:
    try:
        return _bounded_bytes(path).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise AuthorityValidationError("INVALID_UTF8", path.as_posix()) from error


def _fixture_findings(fixture: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if set(fixture) != {"activation", "cases", "fixtureOnly", "repository", "schemaVersion"}:
        findings.append("Fixture corpus root is not closed.")
        return findings
    if (
        fixture["schemaVersion"] != "AuthorityCoreFixtureCorpusV1"
        or fixture["fixtureOnly"] is not True
        or fixture["activation"] != "NONE"
        or fixture["repository"] != "example.invalid/narratwin-authority-fixtures"
    ):
        findings.append("Fixture corpus could be confused with authority.")
    cases = fixture["cases"]
    if not isinstance(cases, list) or not cases:
        return [*findings, "Fixture case inventory is empty."]
    if any(
        not isinstance(case, dict)
        or set(case) != {"classification", "expect", "id", "probe", "target"}
        for case in cases
    ):
        findings.append("Fixture case is malformed or open.")
        return findings
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        findings.append("Fixture case identifiers are duplicate.")
    if {case["classification"] for case in cases} != {"positive", "negative", "adversarial"}:
        findings.append("Fixture classes are incomplete.")
    required_ids = {
        "positive-decision",
        "positive-manifest",
        "positive-route",
        "duplicate-member",
        "unknown-member",
        "malformed-json",
        "invalid-utf8",
        "non-finite-number",
        "scalar-confusion",
        "missing-required",
        "wrong-repository",
        "wrong-schema",
        "wrong-program",
        "wrong-generation",
        "unsupported-version",
        "downgrade",
        "equivalent-noncanonical",
        "normalization-ambiguity",
        "oversized",
        "deeply-nested",
        "excessive-collection",
        "accepted-byte-mutation",
        "missing-predecessor",
        "wrong-predecessor",
        "forked-predecessor",
        "cyclic-predecessor",
        "unlinked-successor",
        "identity-collision",
        "illegal-transition",
        "missing-actor",
        "missing-guard",
        "missing-effect",
        "missing-recovery",
        "wildcard-row",
        "duplicate-row",
        "incomplete-grid",
        "rejected-after-acceptance",
        "evaluation-outcome-state",
        "route-mutation-after-expiry",
        "closeout-as-authority",
        "marker-as-authority",
        "fixture-as-authority",
        "schema-binding-co-mutation",
        "scope-leakage",
    }
    if not required_ids.issubset(ids):
        findings.append("Fixture adversarial inventory is incomplete.")
    return findings


def fixture_execution_findings(fixture: dict[str, Any]) -> list[str]:
    """Execute every declared attack and compare its observed typed outcome."""

    findings: list[str] = []
    for case in fixture.get("cases", []):
        if not isinstance(case, dict) or case.get("probe") != case.get("id"):
            findings.append("Fixture probe is absent or ambiguously bound.")
            continue
        probe = case["probe"]
        try:
            observed = _execute_fixture_probe(probe)
        except (AssertionError, AuthorityValidationError, KeyError, TypeError, ValueError) as error:
            observed = f"PROBE_ERROR:{type(error).__name__}"
        if observed != case.get("expect"):
            findings.append(
                f"{probe} expected {case.get('expect')}, observed {observed}."
            )
    return findings


def _fixture_reference(kind: str, subject: str, sha256: str = "1" * 64) -> dict[str, str]:
    return {
        "referenceType": kind,
        "schemaVersion": "ContentAddressedReferenceV1",
        "sha256": sha256,
        "subject": subject,
    }


def _fixture_object(schema: str) -> dict[str, Any]:
    prohibited = [
        "ACCEPT_AUTHORITY_FROM_CI",
        "ACCEPT_AUTHORITY_FROM_COMMENT",
        "ACCEPT_AUTHORITY_FROM_FILE",
        "ACCEPT_AUTHORITY_FROM_FIXTURE",
        "ACCEPT_AUTHORITY_FROM_ISSUE",
        "ACCEPT_AUTHORITY_FROM_TEST",
        "ACTIVATE_AUTHORITY",
        "AUDIT_SERVICE",
        "CAS_STORAGE",
        "CREDENTIAL_USE",
        "DEPLOYMENT",
        "EVIDENCE_CAPTURE",
        "EXTERNAL_EGRESS",
        "GITHUB_ACQUISITION",
        "HISTORICAL_RECONCILIATION",
        "INFRASTRUCTURE",
        "INTEGRATED_KERNEL",
        "KEY_MANAGEMENT",
        "MEDIA_GENERATION",
        "PRODUCTION_OPERATION",
        "PROVIDER_CALL",
        "PUBLICATION",
        "RELEASE",
        "RUNTIME_SERVICE",
        "SPENDING",
    ]
    value: dict[str, Any] = {
        "contentHash": "0" * 64,
        "generationId": "generation:fixture-only",
        "lifecycleState": "DRAFT" if schema == "ActiveProgramRouteV1" else "PROPOSED",
        "objectId": {
            "MasterProgramAuthorityDecisionV1": "decision:fixture-only",
            "Cut1AuthorityManifestV1": "manifest:fixture-only",
            "ActiveProgramRouteV1": "route:fixture-only",
        }[schema],
        "predecessorContentHash": None,
        "programId": "narratwin-cut1",
        "prohibitedCapabilities": prohibited,
        "repository": "github.com/imrohitagrawal/narratwin-ai",
        "revision": 1,
        "schemaVersion": schema,
        "transition": None,
        "validity": {
            "expiresAt": "2026-09-15T00:00:00Z",
            "notBefore": "2026-08-15T00:00:00Z",
            "revocationReference": None,
            "revokedAt": None,
        },
    }
    if schema == "MasterProgramAuthorityDecisionV1":
        value.update(
            decisionAction="SELECT_MANIFEST",
            effectiveAt="2026-08-15T00:00:00Z",
            priorDecision=None,
            selectedManifest=_fixture_reference("MANIFEST", "manifest:fixture-only"),
            sourceProposal=_fixture_reference("PROPOSAL", "proposal:fixture-only"),
        )
    elif schema == "Cut1AuthorityManifestV1":
        names = (
            "canonicalNarration",
            "downstreamOrderPolicy",
            "finalRenderPolicy",
            "ownerAuthoritySource",
            "presenterSelection",
            "providerPolicy",
            "rendererPolicy",
            "revalidationPolicy",
            "spendPolicy",
            "supersededSourceSet",
        )
        value.update(
            authorityValues={
                name: _fixture_reference("POLICY", f"{name.lower()}:fixture-only")
                for name in names
            },
            capabilityClassifications={name: "DEFERRED" for name in names},
            decisionBacklink=None,
            sourceProposal=_fixture_reference("PROPOSAL", "proposal:fixture-only"),
        )
    else:
        value.update(
            aggregateTestCommands=["make stage8-quality"],
            allowedPaths=["docs/example.invalid"],
            baseSha="2" * 40,
            branch="example-invalid-authority-route",
            childIssue=431,
            controllerIssue=426,
            decision=_fixture_reference("DECISION", "decision:fixture-only"),
            executionWindow={
                "approvedAt": "2026-08-15T00:00:00Z",
                "expired": False,
                "expiresAt": "2026-09-15T00:00:00Z",
            },
            focusedTestCommands=["python3 -m pytest tests/unit/test_issue431_authority_core.py"],
            maxChargedLines=4000,
            maxPathCount=1,
            parentIssue=426,
            predecessorMergeSha="3" * 40,
            pullRequest=None,
            reviewerRoles=[
                "OWNER",
                "PRINCIPAL_ARCHITECT",
                "PRINCIPAL_TEST_ENGINEER",
                "NON_AUTHOR",
            ],
            selectedManifest=_fixture_reference("MANIFEST", "manifest:fixture-only"),
            supersededRoute=None,
            targetBranch="main",
        )
    value["contentHash"] = content_hash(value)
    return value


def _fixture_validation_code(value: dict[str, Any], expected_schema: str) -> str:
    try:
        validate_authority_bytes(canonical_bytes(value), expected_schema)
    except AuthorityValidationError as error:
        return error.code
    return "PASS"


def _fixture_successor(
    predecessor: dict[str, Any], edge: tuple[str, str, str, str]
) -> dict[str, Any]:
    row_id, source, operation, target = edge
    value = deepcopy(predecessor)
    value.update(
        revision=predecessor["revision"] + 1,
        predecessorContentHash=predecessor["contentHash"],
        lifecycleState=target,
    )
    guards = []
    source_types = {
        "ACTIVE_HASH",
        "APPROVED_HASH",
        "CANDIDATE_HASH",
        "CURRENT_HASH",
        "EXPIRED_HASH",
        "MERGED_HASH",
        "REVIEWED_HASH",
        "ROUTE_HASH",
        "SOURCE_HASH",
        "VERIFIED_HASH",
    }
    for kind in ROW_REFERENCES[row_id]:
        sha = predecessor["contentHash"] if kind in source_types else "1" * 64
        guards.append(
            _fixture_reference(
                kind,
                f"guard:{row_id.lower()}-{kind.lower().replace('_', '-')}",
                sha,
            )
        )
    value["transition"] = {
        "actorClass": ROW_ACTORS[row_id],
        "effectId": f"EFFECT_{row_id}_{target}",
        "guardReferences": guards,
        "idempotency": "IDEMPOTENT_SAME_BYTES",
        "operation": operation,
        "prohibitedSubstitutes": ["ISSUE", "COMMENT", "FILE", "FIXTURE", "TEST", "CI"],
        "recoveryClass": (
            "ADMINISTRATIVE_CLOSEOUT" if operation == "CLOSE" else "CREATE_HASH_LINKED_SUCCESSOR"
        ),
        "rejectionBehavior": "NO_MUTATION_TYPED_ERROR",
        "sourceState": source,
        "targetState": target,
    }
    if operation == "EXPIRE" and value["schemaVersion"] == "ActiveProgramRouteV1":
        value["executionWindow"]["expired"] = True
    value["contentHash"] = content_hash(value)
    return value


def _fixture_lineage_outcome(objects: list[dict[str, Any]], phrase: str, outcome: str) -> str:
    return outcome if any(phrase in item.lower() for item in lineage_findings(objects)) else "PASS"


def _fixture_matrix_outcome(
    mutator: Any, phrase: str, outcome: str
) -> str:
    document = deepcopy(_strict_file(ROOT / MATRIX_PATH))
    mutator(document)
    return outcome if any(phrase in item.lower() for item in matrix_findings(document)) else "PASS"


def _execute_fixture_probe(probe: str) -> str:
    parser_probes = {
        "duplicate-member": b'{"a":1,"a":2}',
        "malformed-json": b'{"a":',
        "invalid-utf8": b"\xff",
        "non-finite-number": b'{"a":NaN}',
        "equivalent-noncanonical": b' {"a":1}',
        "oversized": b'"' + b"a" * (MAX_BYTES + 1) + b'"',
        "deeply-nested": b"[" * 13 + b"]" * 13,
        "excessive-collection": b"[" + b",".join([b"0"] * 129) + b"]",
    }
    if probe in parser_probes:
        try:
            _parse_json(parser_probes[probe])
        except AuthorityValidationError as error:
            return error.code
        return "PASS"
    schema_by_positive = {
        "positive-decision": "MasterProgramAuthorityDecisionV1",
        "positive-manifest": "Cut1AuthorityManifestV1",
        "positive-route": "ActiveProgramRouteV1",
    }
    if probe in schema_by_positive:
        schema = schema_by_positive[probe]
        return _fixture_validation_code(_fixture_object(schema), schema)
    if probe == "normalization-ambiguity":
        try:
            canonical_bytes({"value": "caf\u00e9"})
        except AuthorityValidationError as error:
            return error.code
        return "PASS"
    if probe == "unsupported-version":
        return _fixture_validation_code({}, "MasterProgramAuthorityDecisionV2")
    decision = _fixture_object("MasterProgramAuthorityDecisionV1")
    simple_mutations = {
        "unknown-member": lambda value: value.update(extra="closed"),
        "scalar-confusion": lambda value: value.update(revision=True),
        "missing-required": lambda value: value.pop("objectId"),
        "extra-required": lambda value: value.update(extraRequired="closed"),
        "wrong-repository": lambda value: value.update(repository="example.invalid/wrong"),
        "wrong-schema": lambda value: value.update(schemaVersion="WrongAuthorityDecisionV1"),
        "wrong-program": lambda value: value.update(programId="wrong"),
        "wrong-generation": lambda value: value.update(generationId="wrong"),
        "downgrade": lambda value: value.update(schemaVersion="MasterProgramAuthorityDecisionV0"),
        "accepted-byte-mutation": lambda value: value["sourceProposal"].update(subject="proposal:mutated"),
        "missing-predecessor": lambda value: value.update(revision=2),
    }
    if probe in simple_mutations:
        simple_mutations[probe](decision)
        if probe == "missing-predecessor":
            decision["contentHash"] = content_hash(decision)
        return _fixture_validation_code(decision, "MasterProgramAuthorityDecisionV1")
    genesis = _fixture_object("MasterProgramAuthorityDecisionV1")
    reviewed = _fixture_successor(genesis, DECISION_EDGES[0])
    if probe in {"wrong-predecessor", "unlinked-successor"}:
        reviewed["predecessorContentHash"] = "f" * 64
        reviewed["contentHash"] = content_hash(reviewed)
        code = "PREDECESSOR_MISMATCH" if probe == "wrong-predecessor" else "UNLINKED_SUCCESSOR"
        return _fixture_lineage_outcome([genesis, reviewed], "unlinked", code)
    if probe == "forked-predecessor":
        rejected = _fixture_successor(genesis, DECISION_EDGES[1])
        return _fixture_lineage_outcome([genesis, reviewed, rejected], "fork", "FORKED_SUCCESSOR")
    if probe == "cyclic-predecessor":
        reviewed["predecessorContentHash"] = reviewed["contentHash"]
        return _fixture_lineage_outcome([genesis, reviewed], "cyclic", "CYCLIC_LINK")
    if probe == "identity-collision":
        rejected = _fixture_successor(genesis, DECISION_EDGES[1])
        return _fixture_lineage_outcome(
            [genesis, reviewed, rejected], "identity collision", "IDENTITY_COLLISION"
        )
    if probe == "illegal-transition":
        reviewed["lifecycleState"] = "ACCEPTED_CURRENT"
        reviewed["transition"]["targetState"] = "ACCEPTED_CURRENT"
        reviewed["contentHash"] = content_hash(reviewed)
        return _fixture_lineage_outcome([genesis, reviewed], "illegal", "ILLEGAL_TRANSITION")
    matrix_mutations: dict[str, tuple[Any, str, str]] = {
        "missing-actor": (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].pop("actorClass"),
            "actor is missing",
            "ACTOR_REQUIRED",
        ),
        "missing-guard": (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].update(requiredGuards=[]),
            "guard mismatch",
            "GUARD_REQUIRED",
        ),
        "missing-effect": (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].update(effect=""),
            "effect mismatch",
            "EFFECT_REQUIRED",
        ),
        "missing-recovery": (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].update(
                recoveryClassification=""
            ),
            "recovery mismatch",
            "RECOVERY_REQUIRED",
        ),
        "wildcard-row": (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].update(sourceState="*"),
            "wildcard",
            "WILDCARD_PROHIBITED",
        ),
        "duplicate-row": (
            lambda doc: doc["matrices"][0]["legalTransitions"].append(
                deepcopy(doc["matrices"][0]["legalTransitions"][0])
            ),
            "duplicate",
            "DUPLICATE_TRANSITION",
        ),
        "incomplete-grid": (
            lambda doc: doc["matrices"][0]["grid"]["PROPOSED"].pop("REVIEW"),
            "grid cell inventory",
            "INCOMPLETE_MATRIX",
        ),
        "rejected-after-acceptance": (
            lambda doc: doc["matrices"][0]["grid"]["ACCEPTED_CURRENT"].update(
                REJECT="D08"
            ),
            "illegal grid",
            "ILLEGAL_TRANSITION",
        ),
        "evaluation-outcome-state": (
            lambda doc: doc["matrices"][0]["states"].append("UNVERIFIED"),
            "evaluation outcome",
            "EVALUATION_STATE_PROHIBITED",
        ),
    }
    if probe in matrix_mutations:
        mutator, phrase, outcome = matrix_mutations[probe]
        return _fixture_matrix_outcome(mutator, phrase, outcome)
    if probe == "route-mutation-after-expiry":
        draft = _fixture_object("ActiveProgramRouteV1")
        expired = _fixture_successor(draft, ROUTE_EDGES[15])
        active = deepcopy(expired)
        active.update(revision=3, predecessorContentHash=expired["contentHash"], lifecycleState="ACTIVE")
        active["transition"]["sourceState"] = "EXECUTION_EXPIRED"
        active["transition"]["targetState"] = "ACTIVE"
        active["transition"]["operation"] = "ACTIVATE"
        active["contentHash"] = content_hash(active)
        return _fixture_lineage_outcome([draft, expired, active], "illegal", "EXECUTION_EXPIRED")
    if probe == "closeout-as-authority":
        matrix = _strict_file(ROOT / MATRIX_PATH)
        row = next(
            item
            for item in matrix["matrices"][1]["legalTransitions"]
            if item["id"] == "R21"
        )
        blocked = authority_effect_findings("FILE", "ACTIVE")
        return (
            "ADMIN_CLOSEOUT_ONLY"
            if row["recoveryClassification"] == "ADMINISTRATIVE_CLOSEOUT" and blocked
            else "PASS"
        )
    if probe in {"marker-as-authority", "fixture-as-authority"}:
        source = "FIXTURE" if probe.startswith("fixture") else "FILE"
        return "FALSE_AUTHORITY" if authority_effect_findings(source, "ACTIVE") else "PASS"
    if probe == "schema-binding-co-mutation":
        relative = SUPPORTED_SCHEMAS["MasterProgramAuthorityDecisionV1"]
        mutated = _bounded_bytes(ROOT / relative) + b"\n"
        return (
            "COORDINATED_MUTATION"
            if hashlib.sha256(mutated).hexdigest() != ARTIFACT_SHA256[relative]
            else "PASS"
        )
    if probe == "scope-leakage":
        route = _fixture_object("ActiveProgramRouteV1")
        route["providerCredential"] = "forbidden"
        return (
            "PROHIBITED_CAPABILITY"
            if _fixture_validation_code(route, "ActiveProgramRouteV1") == "UNKNOWN_MEMBER"
            else "PASS"
        )
    raise AuthorityValidationError("UNKNOWN_FIXTURE_PROBE", probe)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AuthorityValidationError("GIT_EVIDENCE_UNAVAILABLE", result.stderr.strip())
    return result.stdout.strip()


def _route_findings(root: Path) -> list[str]:
    findings: list[str] = []
    if _git(root, "merge-base", BASE, "HEAD") != BASE:
        findings.append("Child A exact base is not an ancestor of HEAD.")
    commits = _git(root, "rev-list", "--reverse", f"{BASE}..HEAD").splitlines()
    if not commits or commits[0] != FIRST_COMMIT:
        findings.append("Child A first commit identity mismatches.")
    first_parent = _git(root, "rev-parse", f"{FIRST_COMMIT}^")
    first_paths = _git(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r", FIRST_COMMIT
    ).splitlines()
    if first_parent != BASE or first_paths != ["docs/governance/preflights/issue-431.json"]:
        findings.append("Child A first commit is not preflight-only on the exact base.")
    changed = set(_git(root, "diff", "--name-only", f"{BASE}..HEAD", "--").splitlines())
    changed.update(_git(root, "diff", "--name-only", "HEAD", "--").splitlines())
    if changed != set(PATHS):
        findings.append("Child A changed paths do not equal the eighteen-path amended scope.")
    charge = 0
    for line in _git(root, "diff", "--numstat", BASE, "--").splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            findings.append("Child A charged-line evidence is malformed or binary.")
            break
        charge += int(fields[0]) + int(fields[1])
    if charge > LIMIT:
        findings.append(f"Child A charge {charge} exceeds {LIMIT}.")
    if _git(root, "rev-list", "--merges", f"{BASE}..HEAD"):
        findings.append("Child A route contains a merge commit.")
    if _git(root, "rev-parse", "--is-shallow-repository") != "false":
        findings.append("Child A history is shallow.")
    if _git(root, "replace", "-l"):
        findings.append("Child A history contains replace refs.")
    return findings


def _lineage_transition_findings(
    predecessor: dict[str, Any],
    successor: dict[str, Any],
    by_hash: dict[str, dict[str, Any]],
    findings: list[str],
) -> None:
    transition = successor.get("transition")
    if not isinstance(transition, dict):
        findings.append("Successor transition is missing or ambiguous.")
        return
    edges = (
        ROUTE_EDGES if successor.get("schemaVersion") == "ActiveProgramRouteV1" else DECISION_EDGES
    )
    edge = next(
        (
            item
            for item in edges
            if item[1] == predecessor.get("lifecycleState")
            and item[2] == transition.get("operation")
        ),
        None,
    )
    if (
        edge is None
        or transition.get("sourceState") != predecessor.get("lifecycleState")
        or transition.get("targetState") != successor.get("lifecycleState")
        or edge[3] != successor.get("lifecycleState")
    ):
        findings.append("Illegal lifecycle transition is rejected.")
        return
    row_id, _, operation, target = edge
    exact = {
        "actorClass": ROW_ACTORS[row_id],
        "effectId": f"EFFECT_{row_id}_{target}",
        "idempotency": "IDEMPOTENT_SAME_BYTES",
        "operation": operation,
        "prohibitedSubstitutes": ["ISSUE", "COMMENT", "FILE", "FIXTURE", "TEST", "CI"],
        "recoveryClass": "ADMINISTRATIVE_CLOSEOUT"
        if operation == "CLOSE"
        else "CREATE_HASH_LINKED_SUCCESSOR",
        "rejectionBehavior": "NO_MUTATION_TYPED_ERROR",
        "sourceState": edge[1],
        "targetState": target,
    }
    if any(transition.get(key) != expected for key, expected in exact.items()):
        findings.append(
            "Transition actor, guard-independent effect, or recovery mismatches exact row."
        )
    guards = transition.get("guardReferences")
    expected_guards = [
        (reference_type, f"guard:{row_id.lower()}-{reference_type.lower().replace('_', '-')}")
        for reference_type in ROW_REFERENCES[row_id]
    ]
    actual_guards = (
        [
            (guard.get("referenceType"), guard.get("subject"))
            for guard in guards
            if isinstance(guard, dict)
        ]
        if isinstance(guards, list)
        else []
    )
    if actual_guards != expected_guards:
        findings.append("Transition guard reference does not bind its exact row.")
        return
    source_hash_references = {
        "ACTIVE_HASH",
        "APPROVED_HASH",
        "CANDIDATE_HASH",
        "CURRENT_HASH",
        "EXPIRED_HASH",
        "MERGED_HASH",
        "REVIEWED_HASH",
        "ROUTE_HASH",
        "SOURCE_HASH",
        "VERIFIED_HASH",
    }
    expected_hashes: dict[str, Any] = {
        kind: predecessor.get("contentHash")
        for kind in ROW_REFERENCES[row_id]
        if kind in source_hash_references
    }
    if successor.get("schemaVersion") == "ActiveProgramRouteV1":
        decision = successor.get("decision")
        manifest = successor.get("selectedManifest")
        superseded = successor.get("supersededRoute")
        if isinstance(decision, dict):
            expected_hashes["ACCEPTED_DECISION"] = decision.get("sha256")
        if isinstance(manifest, dict):
            expected_hashes["ACCEPTED_MANIFEST"] = manifest.get("sha256")
        if isinstance(superseded, dict):
            expected_hashes["REPLACEMENT_ROUTE"] = superseded.get("sha256")
    validity = successor.get("validity")
    if isinstance(validity, dict) and isinstance(validity.get("revocationReference"), dict):
        expected_hashes["REVOCATION_REFERENCE"] = validity["revocationReference"].get("sha256")
    guards_by_type: dict[str, dict[str, Any]] = {}
    if isinstance(guards, list):
        for guard in guards:
            if isinstance(guard, dict) and isinstance(guard.get("referenceType"), str):
                guards_by_type[guard["referenceType"]] = guard
    if row_id == "D09":
        accepted_guard = guards_by_type.get("ACCEPTED_SUCCESSOR")
        accepted_hash = accepted_guard.get("sha256") if accepted_guard is not None else None
        accepted_successor = by_hash.get(accepted_hash) if isinstance(accepted_hash, str) else None
        stable = ("schemaVersion", "repository", "programId", "generationId")
        if (
            accepted_successor is None
            or accepted_successor.get("lifecycleState") != "ACCEPTED_CURRENT"
            or accepted_successor.get("objectId") == predecessor.get("objectId")
            or any(accepted_successor.get(key) != predecessor.get(key) for key in stable)
        ):
            findings.append("Transition accepted successor does not resolve to the exact accepted object.")
        else:
            expected_hashes["ACCEPTED_SUCCESSOR"] = accepted_successor.get("contentHash")
            if successor.get("schemaVersion") == "MasterProgramAuthorityDecisionV1":
                prior = accepted_successor.get("priorDecision")
                if (
                    not isinstance(prior, dict)
                    or prior.get("sha256") != predecessor.get("contentHash")
                    or prior.get("subject") != predecessor.get("objectId")
                ):
                    findings.append(
                        "Transition accepted successor does not carry the reciprocal prior-decision linkage."
                    )
                expected_hashes["RECIPROCAL_LINKAGE"] = predecessor.get("contentHash")
            elif successor.get("schemaVersion") == "Cut1AuthorityManifestV1":
                current_decision = predecessor.get("decisionBacklink")
                replacement_decision = accepted_successor.get("decisionBacklink")
                replacement_hash = (
                    replacement_decision.get("sha256")
                    if isinstance(replacement_decision, dict)
                    else None
                )
                replacement = by_hash.get(replacement_hash) if isinstance(replacement_hash, str) else None
                prior = replacement.get("priorDecision") if isinstance(replacement, dict) else None
                if (
                    not isinstance(current_decision, dict)
                    or not isinstance(replacement_decision, dict)
                    or not isinstance(replacement, dict)
                    or not isinstance(prior, dict)
                    or replacement_decision.get("subject") != replacement.get("objectId")
                    or prior.get("sha256") != current_decision.get("sha256")
                    or prior.get("subject") != current_decision.get("subject")
                ):
                    findings.append(
                        "Transition accepted successor does not carry the reciprocal manifest-pair linkage."
                    )
                else:
                    expected_hashes["RECIPROCAL_LINKAGE"] = current_decision.get("sha256")
    if row_id == "D10":
        validity = successor.get("validity")
        revocation_reference = (
            validity.get("revocationReference") if isinstance(validity, dict) else None
        )
        revoked_at = validity.get("revokedAt") if isinstance(validity, dict) else None
        if not isinstance(revocation_reference, dict) or not isinstance(revoked_at, str):
            findings.append("Transition revocation representation is absent or incomplete.")
        else:
            expected_hashes["REVOCATION_REFERENCE"] = revocation_reference.get("sha256")
            expected_hashes["EFFECTIVE_TIME"] = _guard_scalar_hash("EFFECTIVE_TIME", revoked_at)
    for reference_type, expected_hash in expected_hashes.items():
        if reference_type in guards_by_type and guards_by_type[reference_type].get(
            "sha256"
        ) != expected_hash:
            label = reference_type.lower().replace("_", " ")
            findings.append(f"Transition guard hash {label} does not bind the governed field.")


def _matrix_item_findings(
    item: dict[str, Any],
    states: tuple[str, ...],
    operations: tuple[str, ...],
    edges: tuple[tuple[str, str, str, str], ...],
    findings: list[str],
) -> None:
    keys = {
        "grid",
        "id",
        "illegalEffect",
        "illegalRecovery",
        "legalTransitions",
        "operations",
        "states",
    }
    if set(item) != keys:
        findings.append(f"{item['id']} matrix is not closed.")
    if item.get("states") != list(states) or item.get("operations") != list(operations):
        findings.append(f"{item['id']} state or operation inventory is incomplete.")
    if any(outcome in item.get("states", []) for outcome in ("UNVERIFIED", "CONFLICTING")):
        findings.append(f"{item['id']} persists an evaluation outcome as a lifecycle state.")
    if (
        item.get("illegalEffect") != "NO_MUTATION_TYPED_ERROR"
        or item.get("illegalRecovery") != "CORRECT_AND_RETRY_OR_CREATE_SUCCESSOR"
    ):
        findings.append(f"{item['id']} illegal transition effect or recovery mismatches.")
    rows = item.get("legalTransitions")
    if not isinstance(rows, list):
        findings.append(f"{item['id']} legal rows are malformed.")
        return
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        findings.append(f"{item['id']} has a duplicate transition row.")
    expected_by_id = {edge[0]: edge for edge in edges}
    if set(ids) != set(expected_by_id):
        findings.append(f"{item['id']} legal transition inventory is incomplete.")
    row_keys = {
        "actorClass",
        "effect",
        "id",
        "idempotency",
        "immutability",
        "legal",
        "operation",
        "prohibitedSubstitutes",
        "recoveryClassification",
        "rejectionBehavior",
        "requiredGuards",
        "requiredTypedReferences",
        "sourceState",
        "targetState",
    }
    for row in rows:
        if not isinstance(row, dict):
            findings.append(f"{item['id']} row is malformed.")
            continue
        missing = row_keys - set(row)
        if "actorClass" in missing:
            findings.append(f"{item['id']} row actor is missing.")
        if set(row) != row_keys:
            findings.append(f"{item['id']} row is not closed.")
            continue
        if "*" in row.values():
            findings.append(f"{item['id']} wildcard transition is prohibited.")
        edge = expected_by_id.get(row["id"])
        if (
            edge is None
            or tuple(row[name] for name in ("id", "sourceState", "operation", "targetState"))
            != edge
        ):
            findings.append(f"{item['id']} illegal or mismatched legal transition row.")
            continue
        row_id, _, operation, target = edge
        if row["actorClass"] != ROW_ACTORS[row_id]:
            findings.append(f"{row_id} actor mismatch.")
        expected_references = list(ROW_REFERENCES[row_id])
        if row["requiredGuards"] != [f"REQUIRE_{item}" for item in expected_references]:
            findings.append(f"{row_id} guard mismatch.")
        if row["requiredTypedReferences"] != expected_references:
            findings.append(f"{row_id} typed reference mismatch.")
        if row["effect"] != f"EFFECT_{row_id}_{target}":
            findings.append(f"{row_id} effect mismatch.")
        recovery = (
            "ADMINISTRATIVE_CLOSEOUT" if operation == "CLOSE" else "CREATE_HASH_LINKED_SUCCESSOR"
        )
        if row["recoveryClassification"] != recovery:
            findings.append(f"{row_id} recovery mismatch.")
        if row["idempotency"] != "IDEMPOTENT_SAME_BYTES":
            findings.append(f"{row_id} idempotency mismatch.")
        if row["immutability"] != "HASH_LINKED_SUCCESSOR_ONLY":
            findings.append(f"{row_id} immutability mismatch.")
        if row["rejectionBehavior"] != "NO_MUTATION_TYPED_ERROR":
            findings.append(f"{row_id} rejection mismatch.")
        if row["prohibitedSubstitutes"] != ["ISSUE", "COMMENT", "FILE", "FIXTURE", "TEST", "CI"]:
            findings.append(f"{row_id} prohibited substitutes mismatch.")
        if row["legal"] is not True:
            findings.append(f"{row_id} legal classification mismatch.")
    expected_grid = {state: {operation: "ILLEGAL" for operation in operations} for state in states}
    for row_id, source, operation, _ in edges:
        expected_grid[source][operation] = row_id
    grid = item.get("grid")
    if not isinstance(grid, dict) or set(grid) != set(states):
        findings.append(f"{item['id']} grid is incomplete.")
        return
    for state in states:
        if not isinstance(grid[state], dict) or set(grid[state]) != set(operations):
            findings.append(f"{item['id']} grid cell inventory is incomplete.")
            continue
        for operation in operations:
            if grid[state][operation] != expected_grid[state][operation]:
                kind = "illegal" if expected_grid[state][operation] == "ILLEGAL" else "legal"
                findings.append(f"{item['id']} {kind} grid classification mismatches.")
