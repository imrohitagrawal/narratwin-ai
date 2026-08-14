#!/usr/bin/env python3
"""Fail-closed Child A schema, canonicalization, matrix, and route gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BRANCH = "cut1-process-431-authority-core-schemas-state-matrices"
BASE = "4d239942eeda0c0b6c385b2d85dae873af076aa6"
FIRST_COMMIT = "7a5594357c24ac864c850a2e1cb92f9cd8acb940"
LIMIT = 4_000
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
    """Produce Child A canonical bytes once its tests define the closed profile."""

    del value
    raise AuthorityValidationError("NOT_IMPLEMENTED")


def validate_authority_bytes(data: bytes, expected_schema: str) -> dict[str, Any]:
    """Validate canonical bytes once the closed schemas define the contract."""

    del data, expected_schema
    raise AuthorityValidationError("NOT_IMPLEMENTED")
