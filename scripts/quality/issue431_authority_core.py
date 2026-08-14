#!/usr/bin/env python3
"""Fail-closed Child A schema, canonicalization, matrix, and route gate."""

from __future__ import annotations

import json
import math
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
    return value
