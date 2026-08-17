#!/usr/bin/env python3
"""Typed RED interface for the Issue #434 offline evidence verifier.

This module intentionally contains no signing, key generation, persistence,
network, ambient-clock, provider, or authority-activation capability.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal, Never, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

RAW_JSON_MAX_BYTES = 262_144
PAYLOAD_MAX_BYTES = 131_072
RETAINED_BLOB_MAX_BYTES = 262_144
RETAINED_BLOBS_AGGREGATE_MAX_BYTES = 16_777_216
MAX_DEPTH = 12
MAX_ARRAY_ITEMS = 64
MAX_OBJECT_MEMBERS = 64
MAX_STRING_BYTES = 2_048
ACTIVATION: Literal["NONE"] = "NONE"
NO_AUTHORITY_EFFECT: Literal["NO_AUTHORITY_EFFECT"] = "NO_AUTHORITY_EFFECT"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED: issue 434 authority-evidence trust verifier"
LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
UTC_SECOND = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
ENVELOPE_SCHEMA_VERSION = "AuthorityEvidenceEnvelopeV1"
TRUST_ROOT_SCHEMA_VERSION = "AuthorityProducerTrustRootV1"
PRODUCER_KEY_SCHEMA_VERSION = "AuthorityProducerKeyV1"
ENVELOPE_MEMBERS = frozenset(
    {
        "canonicalSignatureProfile",
        "capturedAt",
        "collectionMethod",
        "contentHash",
        "evidenceId",
        "evidenceRole",
        "expiresAt",
        "fixtureOnly",
        "freshnessClass",
        "generationId",
        "issuingKeyObjectId",
        "issuingKeyRecordContentHash",
        "issuingKeyRevision",
        "limitations",
        "notBefore",
        "observedAt",
        "payloadByteLength",
        "payloadClass",
        "payloadMediaType",
        "payloadSha256",
        "predecessorContentHash",
        "producerId",
        "producerTrustClass",
        "programId",
        "repository",
        "revision",
        "rootContentHash",
        "rootId",
        "schemaVersion",
        "signature",
        "signatureAlgorithm",
        "signingKeyId",
        "sourceClass",
        "subject",
        "typedReferenceType",
    }
)
ENVELOPE_STRING_MEMBERS = ENVELOPE_MEMBERS - {
    "fixtureOnly",
    "issuingKeyRevision",
    "limitations",
    "payloadByteLength",
    "predecessorContentHash",
    "revision",
    "subject",
}
ENVELOPE_HEX_MEMBERS = frozenset(
    {
        "contentHash",
        "issuingKeyRecordContentHash",
        "payloadSha256",
        "rootContentHash",
        "signingKeyId",
    }
)
ENVELOPE_TIME_MEMBERS = frozenset({"capturedAt", "expiresAt", "notBefore", "observedAt"})
SUBJECT_MEMBERS = frozenset(
    {
        "contentHash",
        "objectId",
        "operation",
        "revision",
        "schemaVersion",
        "sourceState",
        "targetState",
        "transitionRowId",
    }
)


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
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = field(
        default=NO_AUTHORITY_EFFECT,
        init=False,
    )
    activation: Literal["NONE"] = field(default=ACTIVATION, init=False)


def _check_json_value(value: object, depth: int = 1) -> None:
    if depth > MAX_DEPTH:
        raise AuthorityEvidenceTrustError("DEPTH_LIMIT")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not -(2**63) <= value <= 2**63 - 1:
            raise AuthorityEvidenceTrustError("INTEGER_RANGE")
        return
    if isinstance(value, float):
        code = "FLOAT_PROHIBITED" if math.isfinite(value) else "NON_FINITE_NUMBER"
        raise AuthorityEvidenceTrustError(code)
    if isinstance(value, str):
        if any(ord(char) < 0x20 or ord(char) > 0x7E for char in value):
            raise AuthorityEvidenceTrustError("NON_ASCII_STRING")
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise AuthorityEvidenceTrustError("STRING_LIMIT")
        return
    if isinstance(value, list):
        if len(value) > MAX_ARRAY_ITEMS:
            raise AuthorityEvidenceTrustError("COLLECTION_LIMIT")
        for item in value:
            _check_json_value(item, depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_OBJECT_MEMBERS:
            raise AuthorityEvidenceTrustError("MEMBER_LIMIT")
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuthorityEvidenceTrustError("NON_STRING_MEMBER")
            _check_json_value(key, depth + 1)
            _check_json_value(item, depth + 1)
        return
    raise AuthorityEvidenceTrustError("UNSUPPORTED_JSON_TYPE")


def _reject_float(_: str) -> Never:
    raise AuthorityEvidenceTrustError("FLOAT_PROHIBITED")


def _reject_constant(_: str) -> Never:
    raise AuthorityEvidenceTrustError("NON_FINITE_NUMBER")


def _bounded_integer(token: str) -> int:
    if len(token.lstrip("-")) > 19:
        raise AuthorityEvidenceTrustError("INTEGER_RANGE")
    value = int(token)
    if not -(2**63) <= value <= 2**63 - 1:
        raise AuthorityEvidenceTrustError("INTEGER_RANGE")
    return value


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise AuthorityEvidenceTrustError("DUPLICATE_MEMBER")
        value[key] = cast(object, item)
    return value


def _parse_json_object(raw: bytes, *, max_bytes: int) -> dict[str, object]:
    if len(raw) > max_bytes:
        raise AuthorityEvidenceTrustError("SIZE_LIMIT")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AuthorityEvidenceTrustError("INVALID_UTF8") from exc
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_closed_object,
            parse_float=_reject_float,
            parse_int=_bounded_integer,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise AuthorityEvidenceTrustError("MALFORMED_JSON") from exc
    except RecursionError as exc:
        raise AuthorityEvidenceTrustError("DEPTH_LIMIT") from exc
    if not isinstance(parsed, dict):
        raise AuthorityEvidenceTrustError("ROOT_OBJECT_REQUIRED")
    value = cast(dict[str, object], parsed)
    _check_json_value(value)
    return value


def canonical_bytes(value: object) -> bytes:
    """Return the exact bounded ASCII canonical JSON bytes for ``value``."""

    _check_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def parse_closed_json(
    raw: bytes,
    *,
    allowed_members: frozenset[str],
    required_members: frozenset[str],
    max_bytes: int = RAW_JSON_MAX_BYTES,
) -> Mapping[str, object]:
    """Parse one untrusted JSON object with closed members and hard bounds."""

    value = _parse_json_object(raw, max_bytes=max_bytes)
    unknown = set(value) - allowed_members
    if unknown:
        raise AuthorityEvidenceTrustError("UNKNOWN_MEMBER")
    missing = required_members - set(value)
    if missing:
        raise AuthorityEvidenceTrustError("MISSING_MEMBER")
    return value


def content_hash(
    kind: ContentKind,
    schema_version: str,
    value: Mapping[str, object],
) -> str:
    """Return the exact domain-separated SHA-256 content identity."""

    if not isinstance(kind, ContentKind):
        raise AuthorityEvidenceTrustError("CONTENT_KIND")
    if not isinstance(schema_version, str) or value.get("schemaVersion") != schema_version:
        raise AuthorityEvidenceTrustError("SCHEMA_VERSION_MISMATCH")
    _check_json_value(schema_version)
    unsigned = deepcopy(dict(value))
    unsigned.pop("contentHash", None)
    domain = kind.value.encode("ascii") + b"\0" + schema_version.encode("ascii") + b"\0"
    return hashlib.sha256(domain + canonical_bytes(unsigned)).hexdigest()


def evidence_signature_input(envelope: Mapping[str, object]) -> bytes:
    """Return the exact evidence-signature bytes with hash/signature omitted."""

    schema_version = envelope.get("schemaVersion")
    if not isinstance(schema_version, str):
        raise AuthorityEvidenceTrustError("SCHEMA_VERSION_REQUIRED")
    _check_json_value(schema_version)
    unsigned = deepcopy(dict(envelope))
    unsigned.pop("contentHash", None)
    unsigned.pop("signature", None)
    domain = (
        b"NARRATWIN-AUTHORITY-EVIDENCE-SIGNATURE-V1\0"
        + schema_version.encode("ascii")
        + b"\0"
    )
    return domain + canonical_bytes(unsigned)


def verify_ed25519_signature(
    *,
    public_key_hex: str,
    signature_hex: str,
    message: bytes,
) -> SignatureResult:
    """Verify one public Ed25519 signature without any signing capability."""

    if not isinstance(public_key_hex, str) or not re.fullmatch(
        r"[0-9a-f]{64}", public_key_hex
    ):
        return SignatureResult(False, (Finding("PUBLIC_KEY_FORMAT", "publicKey"),))
    if not isinstance(signature_hex, str) or not re.fullmatch(
        r"[0-9a-f]{128}", signature_hex
    ):
        return SignatureResult(False, (Finding("SIGNATURE_FORMAT", "signature"),))
    if not isinstance(message, bytes):
        return SignatureResult(False, (Finding("MESSAGE_TYPE", "message"),))
    public_key = bytes.fromhex(public_key_hex)
    signature = bytes.fromhex(signature_hex)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except InvalidSignature:
        return SignatureResult(False, (Finding("SIGNATURE_INVALID", "signature"),))
    except ValueError:
        return SignatureResult(False, (Finding("PUBLIC_KEY_INVALID", "publicKey"),))
    return SignatureResult(True, ())


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
) -> Evaluation:
    """Evaluate evidence offline using only explicit bytes, pins, heads, and times."""

    invalid: list[Finding] = []
    unavailable: list[Finding] = []

    if envelope_bytes is None:
        unavailable.append(Finding("ENVELOPE_UNAVAILABLE", "envelope"))
    else:
        try:
            envelope = _parse_json_object(envelope_bytes, max_bytes=RAW_JSON_MAX_BYTES)
        except AuthorityEvidenceTrustError as exc:
            invalid.append(Finding(exc.code, "envelope"))
        else:
            invalid.extend(_validate_envelope(envelope))

    if payload_bytes is None:
        unavailable.append(Finding("PAYLOAD_UNAVAILABLE", "payload"))
    elif len(payload_bytes) > PAYLOAD_MAX_BYTES:
        invalid.append(Finding("PAYLOAD_SIZE_LIMIT", "payload"))

    invalid.extend(_validate_explicit_time(acceptance_time, "acceptanceTime"))
    invalid.extend(_validate_explicit_time(current_time, "currentTime"))
    invalid.extend(
        _validate_blob_mapping(
            root_documents,
            "rootDocuments",
            ContentKind.TRUST_ROOT,
            TRUST_ROOT_SCHEMA_VERSION,
        )
    )
    invalid.extend(
        _validate_blob_mapping(
            producer_key_records,
            "producerKeyRecords",
            ContentKind.PRODUCER_KEY,
            PRODUCER_KEY_SCHEMA_VERSION,
        )
    )
    unavailable.extend(_missing_trust_findings(independent_trust))
    unavailable.append(Finding("FULL_VERIFICATION_UNAVAILABLE", "evidence"))

    authority_findings = (
        [Finding(NO_AUTHORITY_EFFECT, "authority")] if claimed_authority_sources else []
    )
    findings = tuple(invalid + unavailable + authority_findings)
    verdict = Verdict.INVALID if invalid else Verdict.UNAVAILABLE if unavailable else Verdict.INVALID
    return Evaluation(
        historical_verdict=verdict,
        current_verdict=verdict,
        findings=findings,
    )


def _validate_envelope(envelope: Mapping[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    unknown = set(envelope) - ENVELOPE_MEMBERS
    if unknown:
        findings.append(Finding("UNKNOWN_MEMBER", "envelope"))
    if ENVELOPE_MEMBERS - set(envelope):
        findings.append(Finding("MISSING_MEMBER", "envelope"))

    for name in sorted(ENVELOPE_STRING_MEMBERS):
        value = envelope.get(name)
        if not isinstance(value, str):
            findings.append(Finding("WRONG_SCALAR_TYPE", f"envelope.{name}"))

    for name in ("revision", "issuingKeyRevision", "payloadByteLength"):
        value = envelope.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            findings.append(Finding("WRONG_SCALAR_TYPE", f"envelope.{name}"))
        elif value < 0 or (name != "payloadByteLength" and value < 1):
            findings.append(Finding("INTEGER_RANGE", f"envelope.{name}"))

    predecessor = envelope.get("predecessorContentHash")
    if predecessor is not None and not isinstance(predecessor, str):
        findings.append(Finding("WRONG_SCALAR_TYPE", "envelope.predecessorContentHash"))
    elif isinstance(predecessor, str) and not LOWER_SHA256.fullmatch(predecessor):
        findings.append(Finding("HEX_FORMAT", "envelope.predecessorContentHash"))

    if not isinstance(envelope.get("fixtureOnly"), bool):
        findings.append(Finding("WRONG_SCALAR_TYPE", "envelope.fixtureOnly"))

    limitations = envelope.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) for item in limitations
    ):
        findings.append(Finding("WRONG_SCALAR_TYPE", "envelope.limitations"))

    for name in sorted(ENVELOPE_HEX_MEMBERS):
        value = envelope.get(name)
        if isinstance(value, str) and not LOWER_SHA256.fullmatch(value):
            findings.append(Finding("HEX_FORMAT", f"envelope.{name}"))

    signature = envelope.get("signature")
    if isinstance(signature, str) and not re.fullmatch(r"[0-9a-f]{128}", signature):
        findings.append(Finding("HEX_FORMAT", "envelope.signature"))

    for name in sorted(ENVELOPE_TIME_MEMBERS):
        value = envelope.get(name)
        if isinstance(value, str):
            findings.extend(_validate_explicit_time(value, f"envelope.{name}"))

    subject = envelope.get("subject")
    if not isinstance(subject, dict):
        findings.append(Finding("WRONG_SCALAR_TYPE", "envelope.subject"))
    else:
        findings.extend(_validate_subject(cast(dict[str, object], subject)))
    return findings


def _validate_subject(subject: Mapping[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    if set(subject) - SUBJECT_MEMBERS:
        findings.append(Finding("UNKNOWN_MEMBER", "envelope.subject"))
    if SUBJECT_MEMBERS - set(subject):
        findings.append(Finding("MISSING_MEMBER", "envelope.subject"))
    for name in SUBJECT_MEMBERS - {"revision"}:
        if not isinstance(subject.get(name), str):
            findings.append(Finding("WRONG_SCALAR_TYPE", f"envelope.subject.{name}"))
    revision = subject.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        findings.append(Finding("WRONG_SCALAR_TYPE", "envelope.subject.revision"))
    content_hash_value = subject.get("contentHash")
    if isinstance(content_hash_value, str) and not LOWER_SHA256.fullmatch(content_hash_value):
        findings.append(Finding("HEX_FORMAT", "envelope.subject.contentHash"))
    return findings


def _validate_explicit_time(value: object, location: str) -> list[Finding]:
    if not isinstance(value, str):
        return [Finding("WRONG_SCALAR_TYPE", location)]
    if not UTC_SECOND.fullmatch(value):
        return [Finding("TIME_FORMAT", location)]
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return [Finding("TIME_FORMAT", location)]
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        return [Finding("TIME_FORMAT", location)]
    return []


def _validate_blob_mapping(
    blobs: Mapping[str, bytes],
    location: str,
    kind: ContentKind,
    expected_schema_version: str,
) -> list[Finding]:
    findings: list[Finding] = []
    total = 0
    items = sorted(
        blobs.items(),
        key=lambda item: item[0] if isinstance(item[0], str) else "",
    )
    for expected_hash, blob in items:
        if not isinstance(expected_hash, str) or not isinstance(blob, bytes):
            findings.append(Finding("BLOB_MAPPING_TYPE", location))
            continue
        total += len(blob)
        if not LOWER_SHA256.fullmatch(expected_hash):
            findings.append(Finding("BLOB_REFERENCE_HASH_FORMAT", location))
        if len(blob) > RETAINED_BLOB_MAX_BYTES:
            findings.append(Finding("BLOB_SIZE_LIMIT", location))
            continue
        try:
            value = _parse_json_object(blob, max_bytes=RETAINED_BLOB_MAX_BYTES)
        except AuthorityEvidenceTrustError as exc:
            findings.append(Finding(f"BLOB_{exc.code}", location))
            continue
        if value.get("schemaVersion") != expected_schema_version:
            findings.append(Finding("BLOB_SCHEMA_VERSION_MISMATCH", location))
            continue
        actual_hash = content_hash(kind, expected_schema_version, value)
        if expected_hash != actual_hash:
            findings.append(Finding("BLOB_CONTENT_HASH_MISMATCH", location))
    if total > RETAINED_BLOBS_AGGREGATE_MAX_BYTES:
        findings.append(Finding("BLOB_AGGREGATE_SIZE_LIMIT", location))
    return findings


def _missing_trust_findings(inputs: IndependentTrustInputs) -> list[Finding]:
    findings: list[Finding] = []
    if not inputs.acceptance_root_pins or inputs.acceptance_root_pin_set_hash is None:
        findings.append(Finding("ACCEPTANCE_ROOT_PIN_REQUIRED", "independentTrust"))
    if not inputs.current_root_pins or inputs.current_root_pin_set_hash is None:
        findings.append(Finding("CURRENT_ROOT_PIN_REQUIRED", "independentTrust"))
    if inputs.acceptance_head is None:
        findings.append(Finding("ACCEPTANCE_HEAD_REQUIRED", "independentTrust"))
    if inputs.current_head is None:
        findings.append(Finding("CURRENT_HEAD_REQUIRED", "independentTrust"))
    return findings


def main() -> int:
    """Expose a deterministic nonzero RED sentinel without reading external input."""

    print(NOT_IMPLEMENTED, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
