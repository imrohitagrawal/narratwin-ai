#!/usr/bin/env python3
"""Typed RED interface for the Issue #434 offline evidence verifier.

This module intentionally contains no signing, key generation, persistence,
network, ambient-clock, provider, or authority-activation capability.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

RAW_JSON_MAX_BYTES = 262_144
PAYLOAD_MAX_BYTES = 131_072
RETAINED_BLOB_MAX_BYTES = 262_144
RETAINED_BLOBS_AGGREGATE_MAX_BYTES = 16_777_216
ACTIVATION = "NONE"
NO_AUTHORITY_EFFECT = "NO_AUTHORITY_EFFECT"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED: issue 434 authority-evidence trust verifier"


class ContentKind(StrEnum):
    """Closed content-hash domains owned by the Child B contract."""

    EVIDENCE_OBJECT = "NARRATWIN-AUTHORITY-EVIDENCE-OBJECT-V1"
    TRUST_ROOT = "NARRATWIN-AUTHORITY-TRUST-ROOT-V1"
    PRODUCER_KEY = "NARRATWIN-AUTHORITY-PRODUCER-KEY-V1"
    RECONSTRUCTION = "NARRATWIN-AUTHORITY-EVIDENCE-RECONSTRUCTION-V1"


class Verdict(StrEnum):
    """Closed fail-closed evidence verdicts in precedence order."""

    CONFLICTING = "CONFLICTING"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    VALID = "VALID"


class AuthorityEvidenceTrustError(ValueError):
    """Stable typed boundary error used by closed parsing and canonicalization."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NotImplementedResult:
    """Deterministic RED sentinel with no authority or activation effect."""

    implemented: Literal[False] = False
    code: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    detail: str = NOT_IMPLEMENTED
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = "NO_AUTHORITY_EFFECT"
    activation: Literal["NONE"] = "NONE"


@dataclass(frozen=True)
class Finding:
    """A stable bounded diagnostic that does not echo untrusted bytes."""

    code: str
    location: str | None = None


@dataclass(frozen=True)
class SignatureResult:
    """Public-key verification result."""

    valid: bool
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class HistoryHead:
    """An independently supplied root-and-producer-scoped history head."""

    root_content_hash: str
    producer_id: str
    history_sequence: int
    key_record_content_hash: str


@dataclass(frozen=True)
class IndependentTrustInputs:
    """Pins and heads supplied independently from all candidate evidence."""

    acceptance_root_pins: tuple[str, ...]
    acceptance_root_pin_set_hash: str | None
    current_root_pins: tuple[str, ...]
    current_root_pin_set_hash: str | None
    acceptance_head: HistoryHead | None
    current_head: HistoryHead | None


@dataclass(frozen=True)
class Evaluation:
    """Historical/current result with an immutable nonactivation boundary."""

    historical_verdict: Verdict
    current_verdict: Verdict
    findings: tuple[Finding, ...]
    authority_effect: str = NO_AUTHORITY_EFFECT
    activation: str = ACTIVATION


NOT_IMPLEMENTED_RESULT = NotImplementedResult()


def _not_implemented() -> NotImplementedResult:
    return NOT_IMPLEMENTED_RESULT


def canonical_bytes(value: object) -> bytes | NotImplementedResult:
    """Return the exact bounded ASCII canonical JSON bytes for ``value``."""

    return _not_implemented()


def parse_closed_json(
    raw: bytes,
    *,
    allowed_members: frozenset[str],
    required_members: frozenset[str],
    max_bytes: int = RAW_JSON_MAX_BYTES,
) -> Mapping[str, object] | NotImplementedResult:
    """Parse one untrusted JSON object with closed members and hard bounds."""

    return _not_implemented()


def content_hash(
    kind: ContentKind,
    schema_version: str,
    value: Mapping[str, object],
) -> str | NotImplementedResult:
    """Return the exact domain-separated SHA-256 content identity."""

    return _not_implemented()


def evidence_signature_input(envelope: Mapping[str, object]) -> bytes | NotImplementedResult:
    """Return the exact evidence-signature bytes with hash/signature omitted."""

    return _not_implemented()


def verify_ed25519_signature(
    *,
    public_key_hex: str,
    signature_hex: str,
    message: bytes,
) -> SignatureResult | NotImplementedResult:
    """Verify one public Ed25519 signature without any signing capability."""

    return _not_implemented()


def evaluate_evidence(
    *,
    envelope_bytes: bytes | None,
    payload_bytes: bytes | None,
    root_documents: Mapping[str, bytes],
    producer_key_records: Mapping[str, bytes],
    independent_trust: IndependentTrustInputs,
    acceptance_time: str,
    current_time: str,
    claimed_authority_sources: tuple[str, ...] = (),
) -> Evaluation | NotImplementedResult:
    """Evaluate evidence offline using only explicit bytes, pins, heads, and times."""

    return _not_implemented()


def main() -> int:
    """Expose a deterministic nonzero RED sentinel without reading external input."""

    print(NOT_IMPLEMENTED, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
