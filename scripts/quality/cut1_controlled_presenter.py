#!/usr/bin/env python3
"""Typed Issue #459 T02 RED boundary with no product or provider behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Finding:
    """One deterministic controlled-presenter finding."""

    code: str
    path: str
    message: str


NOT_IMPLEMENTED = Finding(
    code="CUT1.ENTRY.NOT_IMPLEMENTED",
    path="$",
    message="Issue #459 T02 RED executor; GREEN product behavior is not authorized.",
)


def finding_codes(findings: Sequence[Finding]) -> tuple[str, ...]:
    """Return stable finding codes for independent literal expectations."""

    return tuple(finding.code for finding in findings)


def evaluate_controlled_presenter(
    _materialized_stimulus: Mapping[str, Any],
) -> tuple[Finding, ...]:
    """Return the frozen typed RED result without reading corpus or tests."""

    return (NOT_IMPLEMENTED,)
