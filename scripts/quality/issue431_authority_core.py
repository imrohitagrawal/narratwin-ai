#!/usr/bin/env python3
"""Fail-closed Child A schema, canonicalization, matrix, and route gate."""

from __future__ import annotations

import json
import hashlib
import math
import re
from datetime import datetime
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
MAX_STRING = 4_096
SUPPORTED_SCHEMAS = {
    "MasterProgramAuthorityDecisionV1": (
        "docs/governance/schemas/master-program-authority-decision-v1.schema.json"
    ),
    "Cut1AuthorityManifestV1": "docs/governance/schemas/cut1-authority-manifest-v1.schema.json",
    "ActiveProgramRouteV1": "docs/governance/schemas/active-program-route-v1.schema.json",
}
MATRIX_PATH = "docs/governance/authority-core-state-matrices-v1.json"
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
PATHS = (
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
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_members
        )
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
                datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError as error:
                raise AuthorityValidationError("TIMESTAMP_FORMAT") from error
        pattern = descriptor.get("pattern")
        if pattern and re.fullmatch(pattern, value) is None:
            raise AuthorityValidationError("STRING_PATTERN")
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
            raise AuthorityValidationError("UNKNOWN_MEMBER", sorted(unknown)[0])
        if missing:
            raise AuthorityValidationError("MISSING_MEMBER", sorted(missing)[0])
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
    domain = b"NARRATWIN-AUTHORITY-V1\0" + value["schemaVersion"].encode("ascii") + b"\0"
    return hashlib.sha256(domain + canonical_bytes(unsigned)).hexdigest()


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
    if revision > 1 and (predecessor is None or transition is None):
        raise AuthorityValidationError("PREDECESSOR_REQUIRED")
    if predecessor == value["contentHash"]:
        raise AuthorityValidationError("CYCLIC_LINK")
    validity = value["validity"]
    if validity["notBefore"] >= validity["expiresAt"]:
        raise AuthorityValidationError("VALIDITY_ORDER")
    if (validity["revokedAt"] is None) != (validity["revocationReference"] is None):
        raise AuthorityValidationError("REVOCATION_LINK_MISMATCH")


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
        _lineage_transition_findings(predecessor, value, findings)
    return findings


def authority_effect_findings(source: str, claimed_effect: str) -> list[str]:
    """Return AK-001 false-authority defects; tests define the next behavior slice."""

    del source, claimed_effect
    return ["AUTHORITY_EFFECT_VALIDATOR_NOT_IMPLEMENTED"]


def repository_findings(root: Path = ROOT) -> list[str]:
    """Return exact Child A repository defects; tests define the next gate slice."""

    del root
    return ["REPOSITORY_GATE_NOT_IMPLEMENTED"]


def _lineage_transition_findings(
    predecessor: dict[str, Any], successor: dict[str, Any], findings: list[str]
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
        "actorClass": _expected_actor(operation),
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
    if (
        not isinstance(guards, list)
        or len(guards) != 1
        or not isinstance(guards[0], dict)
        or guards[0].get("subject") != f"guard:{row_id.lower()}"
    ):
        findings.append("Transition guard reference does not bind its exact row.")


def _expected_actor(operation: str) -> str:
    return {
        "REVIEW": "ELIGIBLE_NON_AUTHOR_REVIEWER",
        "OWNER_APPROVE": "OWNER",
        "REJECT": "OWNER",
        "MERGE": "MERGE_COORDINATOR",
        "ACCEPT_CURRENT": "AUTHORITY_EVALUATOR",
        "SUPERSEDE": "OWNER",
        "REVOKE": "OWNER",
        "EXPIRE": "AUTHORITY_EVALUATOR",
        "VERIFY_PREDECESSOR": "AUTHORITY_EVALUATOR",
        "ACTIVATE": "OWNER",
        "CLOSE": "ADMINISTRATIVE_CLOSER",
    }[operation]


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
        if row["actorClass"] != _expected_actor(operation):
            findings.append(f"{row_id} actor mismatch.")
        if row["requiredGuards"] != [f"GUARD_{row_id}_TYPED_REFERENCES"]:
            findings.append(f"{row_id} guard mismatch.")
        if row["requiredTypedReferences"] != ["ContentAddressedReferenceV1"]:
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
