#!/usr/bin/env python3
"""Pure offline public verifier for Issue #434 authority evidence.

This module intentionally contains no signing, key generation, persistence,
network, ambient-clock, provider, or authority-activation capability.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
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
    implemented: Literal[False] = False
    code: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    detail: str = "NOT_IMPLEMENTED: issue 434 authority-evidence trust verifier"
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = "NO_AUTHORITY_EFFECT"
    activation: Literal["NONE"] = "NONE"


@dataclass(frozen=True)
class Finding:
    code: str
    location: str | None = None


@dataclass(frozen=True)
class SignatureResult:
    valid: bool
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class HistoryHead:
    root_content_hash: str
    producer_id: str
    history_sequence: int
    key_record_content_hash: str


@dataclass(frozen=True)
class IndependentTrustInputs:
    acceptance_root_pins: tuple[str, ...]
    acceptance_root_pin_set_hash: str | None
    current_root_pins: tuple[str, ...]
    current_root_pin_set_hash: str | None
    acceptance_head: HistoryHead | None
    current_head: HistoryHead | None


@dataclass(frozen=True)
class Evaluation:
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
    if not isinstance(root_documents, Mapping) or not isinstance(producer_key_records, Mapping) or not isinstance(independent_trust, IndependentTrustInputs) or not (envelope_bytes is None or isinstance(envelope_bytes, bytes)) or not (payload_bytes is None or isinstance(payload_bytes, bytes)):
        return Evaluation(Verdict.INVALID, Verdict.INVALID, (Finding("TRUST_INPUT_INVALID", "independentTrust"),))

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
    if len(blobs) > 64: return [Finding("BLOB_COUNT_LIMIT", location)]  # noqa: E701
    items = sorted(
        blobs.items(),
        key=lambda item: item[0] if isinstance(item[0], str) else "",
    )
    if sum(len(blob) for _, blob in items if isinstance(blob, bytes)) > RETAINED_BLOBS_AGGREGATE_MAX_BYTES: return [Finding("BLOB_AGGREGATE_SIZE_LIMIT", location)]  # noqa: E701
    for expected_hash, blob in items:
        if not isinstance(expected_hash, str) or not isinstance(blob, bytes):
            findings.append(Finding("BLOB_MAPPING_TYPE", location))
            continue
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


KEY_RECORD_MEMBERS = frozenset(("activationTime contentHash fixtureOnly generationId historyPredecessorContentHash historySequence invalidatesFrom keyId keyObjectId operation predecessorAuthorizationSignature predecessorContentHash producerId programId publicKeyHex repository retiredAt revision revokedAt rootAuthorizationSignature rootContentHash rotationPredecessor schemaVersion signatureAlgorithm").split())
KEY_OPERATIONS = frozenset({"ISSUE_GENESIS", "ROTATE", "RETIRE", "REVOKE"})


@dataclass(frozen=True)
class KeyHistoryStructureResult:
    findings: tuple[Finding, ...]
    authorization_evaluated: Literal[False] = field(default=False, init=False)
    root_invalidation_applied: Literal[False] = field(default=False, init=False)
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = field(default=NO_AUTHORITY_EFFECT, init=False)
    activation: Literal["NONE"] = field(default=ACTIVATION, init=False)


@dataclass(frozen=True)
class TrustBoundaryResult:
    findings: tuple[Finding, ...]
    valid: bool = False
    structural_invalidation_applies: bool = False
    issuing_key_eligible: bool = False
    trusted: bool = False
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = field(default=NO_AUTHORITY_EFFECT, init=False)
    activation: Literal["NONE"] = field(default=ACTIVATION, init=False)


def _public_key_id(public_key_hex: str) -> str:
    return hashlib.sha256(b"NARRATWIN-AUTHORITY-ED25519-PUBLIC-KEY-V1\0" + bytes.fromhex(public_key_hex)).hexdigest()


def _key_authorization_input(record: Mapping[str, object], domain: bytes) -> bytes:
    schema_version = record.get("schemaVersion")
    if schema_version != PRODUCER_KEY_SCHEMA_VERSION:
        raise AuthorityEvidenceTrustError("SCHEMA_VERSION_MISMATCH")
    unsigned = deepcopy(dict(record))
    for name in (
        "contentHash",
        "rootAuthorizationSignature",
        "predecessorAuthorizationSignature",
    ):
        unsigned.pop(name, None)
    return domain + b"\0" + PRODUCER_KEY_SCHEMA_VERSION.encode("ascii") + b"\0" + canonical_bytes(unsigned)


def verify_key_record_authorization_signatures(*, record: Mapping[str, object], root_public_key_hex: str, predecessor_public_key_hex: str | None) -> SignatureResult:
    """Verify caller-supplied public signatures; never establish trust or identity."""

    findings: list[Finding] = []
    if record.get("signatureAlgorithm") != "Ed25519":
        findings.append(Finding("SIGNATURE_ALGORITHM", "keyRecord"))
    public_key_hex = record.get("publicKeyHex")
    key_id = record.get("keyId")
    if not isinstance(public_key_hex, str) or not re.fullmatch(
        r"[0-9a-f]{64}", public_key_hex
    ):
        findings.append(Finding("PUBLIC_KEY_FORMAT", "keyRecord.publicKeyHex"))
    elif key_id != _public_key_id(public_key_hex):
        findings.append(Finding("KEY_ID_MISMATCH", "keyRecord.keyId"))
    try:
        root_message = _key_authorization_input(record, b"NARRATWIN-AUTHORITY-KEY-ROOT-AUTHORIZATION-V1")
        predecessor_message = _key_authorization_input(record, b"NARRATWIN-AUTHORITY-KEY-PREDECESSOR-AUTHORIZATION-V1")
    except AuthorityEvidenceTrustError as exc:
        findings.append(Finding(exc.code, "keyRecord"))
        return SignatureResult(False, tuple(findings))

    root_signature = record.get("rootAuthorizationSignature")
    if root_signature is None:
        findings.append(Finding("ROOT_AUTHORIZATION_REQUIRED", "keyRecord"))
    else:
        root_result = verify_ed25519_signature(
            public_key_hex=root_public_key_hex,
            signature_hex=cast(str, root_signature),
            message=root_message,
        )
        if not root_result.valid:
            findings.append(Finding("ROOT_AUTHORIZATION_INVALID", "keyRecord"))

    if record.get("operation") == "ROTATE":
        predecessor_signature = record.get("predecessorAuthorizationSignature")
        if predecessor_signature is None or predecessor_public_key_hex is None:
            findings.append(Finding("PREDECESSOR_AUTHORIZATION_REQUIRED", "keyRecord"))
        else:
            predecessor_result = verify_ed25519_signature(
                public_key_hex=predecessor_public_key_hex,
                signature_hex=cast(str, predecessor_signature),
                message=predecessor_message,
            )
            if not predecessor_result.valid:
                findings.append(Finding("PREDECESSOR_AUTHORIZATION_INVALID", "keyRecord"))
    return SignatureResult(not findings, tuple(findings))


def _utc_value(value: object) -> datetime | None:
    if _validate_explicit_time(value, "time"):
        return None
    return datetime.strptime(cast(str, value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def inspect_key_history_structure(
    *,
    records: tuple[Mapping[str, object], ...],
    expected_head: HistoryHead | None,
    repository: str, program_id: str, generation_id: str, producer_id: str,
    root_content_hash: str, capture_time: str, evaluation_time: str,
    independently_pinned_roots: tuple[str, ...],
    root_invalidations: tuple[Mapping[str, object], ...],
) -> KeyHistoryStructureResult:
    """Inspect a bounded history without evaluating signatures, trust, or authority."""

    findings: list[Finding] = []

    def add(code: str, location: str = "keyHistory") -> None:
        finding = Finding(code, location)
        if finding not in findings:
            findings.append(finding)

    if len(records) > 64:
        add("HISTORY_RECORD_LIMIT")
        return KeyHistoryStructureResult(tuple(findings))
    capture, evaluation = _utc_value(capture_time), _utc_value(evaluation_time)
    if capture is None:
        add("TIME_FORMAT", "captureTime")
    if evaluation is None:
        add("TIME_FORMAT", "evaluationTime")
    pinned_roots = independently_pinned_roots[:64]
    if len(independently_pinned_roots) > 64 or len(root_invalidations) > 64:
        add("ROOT_PIN_SET_LIMIT")
    if root_content_hash not in pinned_roots:
        add("ROOT_PIN_REQUIRED")

    unique: list[Mapping[str, object]] = []
    for candidate in records:
        if not isinstance(candidate, Mapping):
            add("WRONG_SCALAR_TYPE", "keyHistory.record")
            continue
        unique.append(candidate)

    valid: list[Mapping[str, object]] = []
    for record in unique:
        local: list[Finding] = []

        def reject(code: str, member: str = "keyRecord") -> None:
            local.append(Finding(code, member))

        try:
            _check_json_value(record)
        except AuthorityEvidenceTrustError as exc:
            reject(exc.code)
        if set(record) - KEY_RECORD_MEMBERS:
            reject("UNKNOWN_MEMBER")
        if KEY_RECORD_MEMBERS - set(record):
            reject("MISSING_MEMBER")
        for name in ("historySequence", "revision"):
            value = record.get(name)
            if isinstance(value, bool) or not isinstance(value, int):
                reject("WRONG_SCALAR_TYPE", f"keyRecord.{name}")
        for name in ("contentHash", "keyId", "keyObjectId", "publicKeyHex", "repository", "programId", "generationId", "producerId", "rootContentHash"):
            if not isinstance(record.get(name), str):
                reject("WRONG_SCALAR_TYPE", f"keyRecord.{name}")
        for name in ("historyPredecessorContentHash", "predecessorContentHash"):
            value = record.get(name)
            if value is not None and not isinstance(value, str):
                reject("WRONG_SCALAR_TYPE", f"keyRecord.{name}")
        rotation_value = record.get("rotationPredecessor")
        if rotation_value is not None:
            if not isinstance(rotation_value, Mapping):
                reject("WRONG_SCALAR_TYPE", "keyRecord.rotationPredecessor")
            else:
                if set(rotation_value) != {"contentHash", "keyObjectId", "revision"}:
                    reject("ROTATION_PREDECESSOR_RELATION")
                for name, expected_type in (("contentHash", str), ("keyObjectId", str), ("revision", int)):
                    value = rotation_value.get(name)
                    if isinstance(value, bool) or not isinstance(value, expected_type):
                        reject("WRONG_SCALAR_TYPE", f"keyRecord.rotationPredecessor.{name}")
        operation = record.get("operation")
        if not isinstance(operation, str) or operation not in KEY_OPERATIONS:
            reject("UNKNOWN_KEY_OPERATION", "keyRecord.operation")
        activation_value = record.get("activationTime")
        if _utc_value(activation_value) is None: reject("WRONG_SCALAR_TYPE" if activation_value is None else "TIME_FORMAT", "keyRecord.activationTime")  # noqa: E701
        for name in ("retiredAt", "revokedAt", "invalidatesFrom"):
            value = record.get(name)
            if value is not None and _utc_value(value) is None:
                reject("TIME_FORMAT", f"keyRecord.{name}")
        if operation == "ISSUE_GENESIS" and any((record.get("revision") != 1, record.get("historySequence") != 1, record.get("historyPredecessorContentHash") is not None, record.get("predecessorContentHash") is not None, record.get("rotationPredecessor") is not None, record.get("predecessorAuthorizationSignature") is not None, record.get("retiredAt") is not None, record.get("revokedAt") is not None, record.get("invalidatesFrom") is not None)):
            reject("GENESIS_RELATION")
        if operation == "ROTATE":
            if record.get("predecessorAuthorizationSignature") is None:
                reject("PREDECESSOR_AUTHORIZATION_REQUIRED")
            if record.get("revision") != 1 or record.get("predecessorContentHash") is not None or record.get("rotationPredecessor") is None or any(record.get(name) is not None for name in ("retiredAt", "revokedAt", "invalidatesFrom")):
                reject("ROTATION_PREDECESSOR_RELATION")
        if isinstance(operation, str) and operation in KEY_OPERATIONS and record.get("rootAuthorizationSignature") is None:
            reject("ROOT_AUTHORIZATION_REQUIRED")
        if operation == "RETIRE":
            if record.get("retiredAt") is None:
                reject("RETIREMENT_REQUIRED")
            if any(record.get(name) is not None for name in ("rotationPredecessor", "revokedAt", "invalidatesFrom", "predecessorAuthorizationSignature")):
                reject("PREDECESSOR_AUTHORIZATION_PROHIBITED")
        if operation == "REVOKE":
            if record.get("revokedAt") is None or record.get("invalidatesFrom") is None:
                reject("REVOCATION_BOUNDARY_REQUIRED")
            if record.get("rotationPredecessor") is not None or record.get("predecessorAuthorizationSignature") is not None: reject("PREDECESSOR_AUTHORIZATION_PROHIBITED")  # noqa: E701
            activation, invalidates, revoked = (_utc_value(record.get(name)) for name in ("activationTime", "invalidatesFrom", "revokedAt"))
            if None not in (activation, invalidates, revoked) and not cast(datetime, activation) <= cast(datetime, invalidates) <= cast(datetime, revoked):
                reject("REVOCATION_BOUNDARY_ORDER")
        scope = {"repository": (repository, "REPOSITORY_SCOPE_MISMATCH"), "programId": (program_id, "PROGRAM_SCOPE_MISMATCH"), "generationId": (generation_id, "GENERATION_SCOPE_MISMATCH"), "producerId": (producer_id, "PRODUCER_SCOPE_MISMATCH"), "rootContentHash": (root_content_hash, "ROOT_SCOPE_MISMATCH")}
        for name, (expected, code) in scope.items():
            if record.get(name) != expected:
                reject(code, f"keyRecord.{name}")
        public_key_hex = record.get("publicKeyHex")
        if not isinstance(public_key_hex, str) or not re.fullmatch(
            r"[0-9a-f]{64}", public_key_hex
        ):
            reject("PUBLIC_KEY_FORMAT", "keyRecord.publicKeyHex")
        elif record.get("keyId") != _public_key_id(public_key_hex):
            reject("KEY_ID_MISMATCH", "keyRecord.keyId")
        try:
            actual_hash = content_hash(
                ContentKind.PRODUCER_KEY, PRODUCER_KEY_SCHEMA_VERSION, record
            )
        except AuthorityEvidenceTrustError as exc:
            reject(exc.code)
        else:
            if record.get("contentHash") != actual_hash:
                reject("CONTENT_HASH_MISMATCH", "keyRecord.contentHash")
        for finding in local:
            add(finding.code, finding.location or "keyRecord")
        if {finding.code for finding in local} <= {"ROOT_AUTHORIZATION_REQUIRED", "PREDECESSOR_AUTHORIZATION_REQUIRED"}:
            valid.append(record)

    deduplicated: dict[str, Mapping[str, object]] = {}
    for record in valid:
        digest = cast(str, record["contentHash"]); prior = deduplicated.get(digest)  # noqa: E702
        if prior is not None and prior != record: add("DUPLICATE_CONTENT_HASH")  # noqa: E701
        elif prior is None: deduplicated[digest] = record  # noqa: E701
    valid = list(deduplicated.values())
    by_hash = {cast(str, row["contentHash"]): row for row in valid}
    children: dict[str, list[str]] = {}; rotation_children: dict[str, list[str]] = {}; same_key_children: dict[str, list[str]] = {}  # noqa: E702
    key_ids: dict[str, tuple[str, str]] = {}
    public_keys: dict[str, str] = {}
    for record in valid:
        record_hash = cast(str, record["contentHash"])
        sequence = cast(int, record["historySequence"])
        predecessor_hash = record.get("historyPredecessorContentHash")
        if sequence == 1:
            if predecessor_hash is not None:
                add("HISTORY_SEQUENCE_JUMP")
        elif not isinstance(predecessor_hash, str) or predecessor_hash not in by_hash:
            add("HISTORY_PREDECESSOR_UNAVAILABLE")
        else:
            children.setdefault(predecessor_hash, []).append(record_hash)
            if by_hash[predecessor_hash].get("historySequence") != sequence - 1:
                add("HISTORY_SEQUENCE_JUMP")

        key_id = cast(str, record["keyId"])
        public_key = cast(str, record["publicKeyHex"])
        key_object = cast(str, record["keyObjectId"])
        prior_identity = key_ids.get(key_id)
        if prior_identity and prior_identity[0] != public_key:
            add("DUPLICATE_KEY_ID")
        elif prior_identity and prior_identity[1] != key_object:
            add("DUPLICATE_PUBLIC_KEY")
        key_ids.setdefault(key_id, (public_key, key_object))
        if public_key in public_keys and public_keys[public_key] != key_object:
            add("DUPLICATE_PUBLIC_KEY")
        public_keys.setdefault(public_key, key_object)

        operation = record["operation"]
        if operation == "ROTATE":
            rotation = record.get("rotationPredecessor")
            rotation_hash = rotation.get("contentHash") if isinstance(rotation, Mapping) else None
            prior = by_hash.get(rotation_hash) if isinstance(rotation_hash, str) else None
            if isinstance(rotation_hash, str): rotation_children.setdefault(rotation_hash, []).append(record_hash)  # noqa: E701
            wrong_relation = (
                not isinstance(rotation, Mapping)
                or record.get("predecessorContentHash") is not None
                or record.get("revision") != 1
                or prior is None
                or rotation.get("keyObjectId") != prior.get("keyObjectId")
                or prior.get("keyObjectId") == key_object
                or prior.get("publicKeyHex") == public_key
                or rotation.get("revision") != prior.get("revision")
            )
            if wrong_relation:
                add("ROTATION_PREDECESSOR_RELATION")
            elif prior is not None and prior.get("operation") not in {"ISSUE_GENESIS", "ROTATE"}:
                add("ROTATION_SOURCE_STATE")
            elif prior is not None and any(row.get("keyObjectId") == prior.get("keyObjectId") and row.get("operation") in {"RETIRE", "REVOKE"} and cast(int, row["historySequence"]) < sequence for row in valid): add("ROTATION_SOURCE_STATE")  # noqa: E701
            elif prior is not None and cast(datetime, _utc_value(record.get("activationTime"))) < cast(datetime, _utc_value(prior.get("activationTime"))): add("ROTATION_TEMPORAL_ORDER")  # noqa: E701
        elif operation in {"RETIRE", "REVOKE"}:
            same_predecessor = record.get("predecessorContentHash")
            prior = by_hash.get(same_predecessor) if isinstance(same_predecessor, str) else None
            if isinstance(same_predecessor, str): same_key_children.setdefault(same_predecessor, []).append(record_hash)  # noqa: E701
            if prior is None:
                add("SAME_KEY_PREDECESSOR_REQUIRED")
                if operation == "REVOKE":
                    add("REVOKE_SOURCE_STATE")
            elif prior.get("keyObjectId") != key_object or prior.get("publicKeyHex") != public_key:
                add("SAME_KEY_PREDECESSOR_RELATION")
            elif cast(int, record["revision"]) <= cast(int, prior["revision"]):
                add("KEY_REVISION_DOWNGRADE")
            elif cast(int, record["revision"]) != cast(int, prior["revision"]) + 1:
                add("KEY_REVISION_GAP")
            else:
                if record.get("activationTime") != prior.get("activationTime"):
                    add("KEY_ACTIVATION_CHANGED")
                if operation == "RETIRE" and prior.get("operation") not in {"ISSUE_GENESIS", "ROTATE"}:
                    add("RETIRE_SOURCE_STATE")
                if operation == "REVOKE":
                    if prior.get("operation") not in {"ISSUE_GENESIS", "ROTATE", "RETIRE"}:
                        add("REVOKE_SOURCE_STATE")
                    if prior.get("retiredAt") is None and record.get("retiredAt") is not None:
                        add("REVOKE_SOURCE_STATE")
                    if prior.get("retiredAt") is not None and record.get("retiredAt") != prior.get("retiredAt"):
                        add("RETIRED_STATE_NOT_PRESERVED")
                    if prior.get("retiredAt") is not None and cast(datetime, _utc_value(record.get("revokedAt"))) < cast(datetime, _utc_value(prior.get("retiredAt"))): add("REVOCATION_BOUNDARY_ORDER")  # noqa: E701

    if any(len(successors) > 1 for graph in (children, rotation_children, same_key_children) for successors in graph.values()) or sum(row.get("historySequence") == 1 for row in valid) > 1:
        add("HISTORY_FORK")
    for record in valid:
        seen: set[str] = set()
        cursor: Mapping[str, object] | None = record
        while cursor is not None:
            cursor_hash = cast(str, cursor["contentHash"])
            if cursor_hash in seen:
                add("HISTORY_CYCLE")
                break
            seen.add(cursor_hash)
            predecessor = cursor.get("historyPredecessorContentHash")
            cursor = by_hash.get(predecessor) if isinstance(predecessor, str) else None

    head_record: Mapping[str, object] | None = None
    if expected_head is not None and not isinstance(expected_head, HistoryHead):
        add("WRONG_SCALAR_TYPE", "expectedHead")
        expected_head = None
    if expected_head is None:
        add("CURRENT_HEAD_REQUIRED")
    else:
        head_strings = (expected_head.root_content_hash, expected_head.producer_id, expected_head.key_record_content_hash)
        if any(not isinstance(value, str) for value in head_strings) or isinstance(expected_head.history_sequence, bool) or not isinstance(expected_head.history_sequence, int):
            add("WRONG_SCALAR_TYPE", "expectedHead")
            return KeyHistoryStructureResult(tuple(sorted(findings, key=lambda item: (item.code, item.location or ""))))
        head_record = by_hash.get(expected_head.key_record_content_hash)
        if (
            expected_head.root_content_hash != root_content_hash
            or expected_head.producer_id != producer_id
            or head_record is None
            or head_record.get("historySequence") != expected_head.history_sequence
        ):
            add("CURRENT_HEAD_MISMATCH")
            head_record = None
        else:
            head_chain: set[str] = set()
            head_cursor: Mapping[str, object] | None = head_record
            while head_cursor is not None and cast(str, head_cursor["contentHash"]) not in head_chain:
                head_chain.add(cast(str, head_cursor["contentHash"]))
                predecessor = head_cursor.get("historyPredecessorContentHash")
                head_cursor = by_hash.get(predecessor) if isinstance(predecessor, str) else None
            if set(by_hash) != head_chain:
                add("CURRENT_HEAD_ROLLBACK")

    if head_record is not None and capture is not None and evaluation is not None:
        activation = _utc_value(head_record.get("activationTime"))
        retired = _utc_value(head_record.get("retiredAt"))
        revoked = _utc_value(head_record.get("revokedAt"))
        invalidates = _utc_value(head_record.get("invalidatesFrom"))
        if activation is not None and capture < activation:
            add("KEY_NOT_YET_ACTIVE")
        if retired is not None and capture >= retired:
            add("KEY_RETIRED")
        if revoked is not None and invalidates is not None and evaluation >= revoked and capture >= invalidates:
            add("KEY_REVOKED")

    for declaration in root_invalidations[:64]:
        if not isinstance(declaration, Mapping):
            add("WRONG_SCALAR_TYPE", "rootInvalidation")
            continue
        successor = declaration.get("successorRootContentHash")
        if not isinstance(successor, str) or successor not in pinned_roots:
            add("ROOT_SUCCESSOR_PIN_REQUIRED", "rootInvalidation")
    return KeyHistoryStructureResult(tuple(sorted(findings, key=lambda item: (item.code, item.location or ""))))


def validate_closed_schema_value(
    value: object, schema_document: Mapping[str, object]
) -> tuple[Finding, ...]:
    """Execute the bounded closed-schema vocabulary used by Child B artifacts."""

    findings: list[Finding] = []
    if not isinstance(schema_document, Mapping): return (Finding("SCHEMA_DOCUMENT_INVALID"),)  # noqa: E701
    try:
        _check_json_value(schema_document)
    except AuthorityEvidenceTrustError:
        return (Finding("SCHEMA_DOCUMENT_INVALID"),)
    definitions = schema_document.get("$defs")
    root = schema_document.get("root")
    if not isinstance(definitions, Mapping) or not isinstance(root, Mapping):
        return (Finding("SCHEMA_DOCUMENT_INVALID"),)

    def add(code: str, location: str) -> None:
        findings.append(Finding(code, location))

    def walk(item: object, descriptor: object, location: str, depth: int = 1) -> None:
        if depth > MAX_DEPTH or not isinstance(descriptor, Mapping):
            add("SCHEMA_DESCRIPTOR_INVALID", location)
            return
        reference = descriptor.get("$ref")
        if reference is not None:
            target = definitions.get(reference) if isinstance(reference, str) else None
            if not isinstance(target, Mapping):
                add("SCHEMA_REFERENCE_UNKNOWN", location)
            else:
                walk(item, target, location, depth + 1)
            return
        kind = descriptor.get("type")
        if kind == "nullable":
            if item is not None:
                walk(item, descriptor.get("item"), location, depth + 1)
            return
        if kind in {"string", "sha256", "timestamp"}:
            if not isinstance(item, str):
                add("WRONG_SCALAR_TYPE", location)
                return
            size = len(item.encode("utf-8"))
            if size < descriptor.get("minLength", 0) or size > descriptor.get("maxLength", MAX_STRING_BYTES):
                add("STRING_LIMIT", location)
            pattern = descriptor.get("pattern")
            if isinstance(pattern, str) and re.fullmatch(pattern, item) is None:
                add("STRING_PATTERN", location)
            if kind == "sha256" and LOWER_SHA256.fullmatch(item) is None:
                add("HEX_FORMAT", location)
            if kind == "timestamp" and _utc_value(item) is None:
                add("TIME_FORMAT", location)
        elif kind == "integer":
            if isinstance(item, bool) or not isinstance(item, int):
                add("WRONG_SCALAR_TYPE", location)
                return
            if item < descriptor.get("minimum", -(2**63)) or item > descriptor.get("maximum", 2**63 - 1):
                add("INTEGER_RANGE", location)
        elif kind == "boolean":
            if not isinstance(item, bool):
                add("WRONG_SCALAR_TYPE", location)
        elif kind == "object":
            if not isinstance(item, Mapping):
                add("WRONG_SCALAR_TYPE", location)
                return
            properties = descriptor.get("properties")
            required = descriptor.get("required")
            if not isinstance(properties, Mapping) or not isinstance(required, list) or descriptor.get("closed") is not True:
                add("SCHEMA_DESCRIPTOR_INVALID", location)
                return
            if set(item) - set(properties):
                add("UNKNOWN_MEMBER", location)
            if set(required) - set(item):
                add("MISSING_MEMBER", location)
            for name, child in item.items():
                child_descriptor = properties.get(name)
                if child_descriptor is not None:
                    walk(child, child_descriptor, f"{location}.{name}", depth + 1)
        elif kind == "array":
            if not isinstance(item, list):
                add("WRONG_SCALAR_TYPE", location)
                return
            if len(item) < descriptor.get("minItems", 0) or len(item) > descriptor.get("maxItems", MAX_ARRAY_ITEMS):
                add("COLLECTION_LIMIT", location)
                return
            encoded = [canonical_bytes(child) for child in item]
            if descriptor.get("unique") is True and len(set(encoded)) != len(encoded):
                add("DUPLICATE_COLLECTION_ITEM", location)
            exact = descriptor.get("exactItems")
            if exact is not None and item != exact:
                add("EXACT_COLLECTION_MISMATCH", location)
            order = descriptor.get("order")
            if order == "LEXICOGRAPHIC_ASCENDING" and all(isinstance(child, str) for child in item) and item != sorted(item):
                add("COLLECTION_ORDER_MISMATCH", location)
            if order == "TRANSITION_ROW_THEN_EVIDENCE_ROLE_ASCENDING" and all(isinstance(child, Mapping) and isinstance(child.get("transitionRowId"), str) and isinstance(child.get("evidenceRole"), str) for child in item):
                ordered = sorted(item, key=lambda child: (cast(Mapping[str, object], child).get("transitionRowId", ""), cast(Mapping[str, object], child).get("evidenceRole", "")))
                if item != ordered:
                    add("COLLECTION_ORDER_MISMATCH", location)
            unique_by = descriptor.get("uniqueBy")
            if isinstance(unique_by, list) and all(isinstance(child, Mapping) for child in item):
                keys = [canonical_bytes([cast(Mapping[str, object], child).get(cast(str, name)) for name in unique_by]) for child in item]
                if len(set(keys)) != len(keys):
                    add("DUPLICATE_COLLECTION_ITEM", location)
            child_descriptor = descriptor.get("items")
            if child_descriptor is not None:
                for index, child in enumerate(item):
                    walk(child, child_descriptor, f"{location}[{index}]", depth + 1)
        else:
            add("SCHEMA_TYPE_UNKNOWN", location)
            return
        if "const" in descriptor and item != descriptor["const"]:
            add("CONST_MISMATCH", location)
        values = descriptor.get("enum")
        if isinstance(values, list) and item not in values:
            add("ENUM_MISMATCH", location)

    try:
        walk(value, root, "document")
    except (AuthorityEvidenceTrustError, TypeError, ValueError, re.error):
        findings.append(Finding("SCHEMA_DESCRIPTOR_INVALID", "document"))
    return tuple(dict.fromkeys(findings))


PIN_MEMBERS = frozenset({"schemaVersion", "repository", "programId", "generationId", "producerId", "evaluationPhase", "rootContentHashes"})
PIN_DOMAIN = b"NARRATWIN-AUTHORITY-ROOT-PIN-SET-V1\0AuthorityRootPinSetV1\0"


def root_pin_set_hash(*, descriptor: Mapping[str, object]) -> str:
    return hashlib.sha256(PIN_DOMAIN + canonical_bytes(descriptor)).hexdigest()


def _codes(*codes: str, valid: bool = False, **flags: bool) -> TrustBoundaryResult:
    return TrustBoundaryResult(tuple(Finding(code) for code in dict.fromkeys(codes)), valid=valid, **flags)


def _closed_boundary(result: object) -> TrustBoundaryResult:
    from scripts.quality.issue434_authority_evidence_reconstruction import ClosedResult

    closed = cast(ClosedResult, result)
    return TrustBoundaryResult(
        closed.findings,
        valid=closed.valid,
        structural_invalidation_applies=closed.structural_invalidation_applies,
        issuing_key_eligible=closed.issuing_key_eligible,
        trusted=closed.trusted,
    )


def validate_root_pin_set(*, descriptor: Mapping[str, object] | None, expected_hash: str | None, expected_phase: str, expected_scope: tuple[str, str, str, str], source: str) -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    codes = (["ROOT_PIN_DESCRIPTOR_REQUIRED"] if descriptor is None else closed._pin_codes(descriptor, expected_hash, expected_phase, expected_scope))
    if source != "INDEPENDENT":
        codes.append("ROOT_PIN_SOURCE_PROHIBITED")
    return _codes(*dict.fromkeys(codes), valid=not codes)


def validate_root_pin_transition(*, acceptance_descriptor: Mapping[str, object], acceptance_expected_hash: str, current_descriptor: Mapping[str, object], current_expected_hash: str) -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    values = tuple(acceptance_descriptor.get(name) for name in ("repository", "programId", "generationId", "producerId")) if isinstance(acceptance_descriptor, Mapping) else ()
    scope = cast(tuple[str, str, str, str], values) if len(values) == 4 and all(isinstance(item, str) for item in values) else ("", "", "", "")
    return _closed_boundary(closed.validate_pin_transition(acceptance_descriptor=acceptance_descriptor, acceptance_expected_hash=acceptance_expected_hash, current_descriptor=current_descriptor, current_expected_hash=current_expected_hash, expected_scope=scope))


def validate_trust_root(*, root_bytes: bytes, expected_root_hash: object, pin_descriptor: Mapping[str, object], expected_pin_set_hash: str, evaluation_time: str) -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    values = tuple(pin_descriptor.get(name) for name in ("repository", "programId", "generationId", "producerId")) if isinstance(pin_descriptor, Mapping) else ()
    scope = cast(tuple[str, str, str, str], values) if len(values) == 4 and all(isinstance(item, str) for item in values) else ("", "", "", "")
    phase = pin_descriptor.get("evaluationPhase") if isinstance(pin_descriptor, Mapping) and pin_descriptor.get("evaluationPhase") in {"ACCEPTANCE", "CURRENT"} else "ACCEPTANCE"
    return _closed_boundary(closed.validate_closed_root(root_bytes=root_bytes, expected_root_hash=expected_root_hash, pin_descriptor=pin_descriptor, expected_pin_set_hash=expected_pin_set_hash, expected_phase=cast(str, phase), expected_scope=scope, evaluation_time=evaluation_time))


def resolve_root_invalidation_structure(*, root_documents: Mapping[str, bytes], pin_descriptor: Mapping[str, object], expected_pin_set_hash: str, expected_scope: tuple[str, str, str, str], prior_root_content_hash: object, evaluation_time: str) -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    return _closed_boundary(closed.resolve_root_invalidation(root_documents=root_documents, pin_descriptor=pin_descriptor, expected_pin_set_hash=expected_pin_set_hash, expected_scope=expected_scope, prior_root_content_hash=prior_root_content_hash, evaluation_time=evaluation_time))


def resolve_issuing_key_structure(*, records: tuple[Mapping[str, object], ...], expected_head: HistoryHead, issuing_key: tuple[object, object, object, object], capture_time: str, evaluation_time: str | None = None) -> TrustBoundaryResult:
    if not records or not all(isinstance(row, Mapping) for row in records) or not isinstance(expected_head, HistoryHead) or not isinstance(issuing_key, tuple) or len(issuing_key) != 4:
        return _codes("KEY_RECORD_INVALID")
    if evaluation_time is not None and _utc_value(evaluation_time) is None: return _codes("TIME_FORMAT")  # noqa: E701
    first = records[0]
    values = tuple(first.get(name) for name in ("repository", "programId", "generationId", "producerId", "rootContentHash"))
    if any(not isinstance(item, str) for item in values):
        return _codes("KEY_RECORD_INVALID")
    structure = inspect_key_history_structure(records=records, expected_head=expected_head, repository=cast(str, values[0]), program_id=cast(str, values[1]), generation_id=cast(str, values[2]), producer_id=cast(str, values[3]), root_content_hash=cast(str, values[4]), capture_time=capture_time, evaluation_time=capture_time, independently_pinned_roots=(cast(str, values[4]),), root_invalidations=())
    findings = [item.code for item in structure.findings]
    key_object, key_id, revision, record_hash = issuing_key
    capture = _utc_value(capture_time)
    selected = next((row for row in records if row.get("keyObjectId") == key_object and row.get("keyId") == key_id and row.get("revision") == revision and row.get("contentHash") == record_hash), None)
    if selected is not None and selected.get("contentHash") != expected_head.key_record_content_hash:
        findings = [code for code in findings if code not in {"KEY_NOT_YET_ACTIVE", "KEY_RETIRED", "KEY_REVOKED"}]
    eligible = capture is not None and selected is not None and not findings
    if selected is None:
        findings.append("ISSUING_KEY_IDENTITY_MISMATCH")
    elif capture is not None and (activation := _utc_value(selected.get("activationTime"))) is not None and capture < activation:
        findings.append("KEY_NOT_YET_ACTIVE")
        eligible = False
    for row in records:
        if row.get("keyObjectId") != key_object or row.get("operation") not in {"RETIRE", "REVOKE"}:
            continue
        observed = _utc_value(row.get("retiredAt") if row.get("operation") == "RETIRE" else row.get("revokedAt"))
        if evaluation_time is not None and (evaluation := _utc_value(evaluation_time)) is not None and observed is not None and evaluation < observed:
            continue
        boundary = _utc_value(row.get("retiredAt") if row.get("operation") == "RETIRE" else row.get("invalidatesFrom"))
        if capture is not None and boundary is not None and capture >= boundary:
            eligible = False
    return _codes(*dict.fromkeys(findings), issuing_key_eligible=eligible)


def validate_contract_artifacts(*, artifacts: Mapping[str, bytes], child_a_matrix_bytes: bytes, expected_artifact_hashes: Mapping[str, str] | None = None) -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    return _closed_boundary(closed.validate_artifact_set(artifacts=artifacts, child_a_matrix_bytes=child_a_matrix_bytes, expected_artifact_hashes=expected_artifact_hashes))


def resolve_evidence_key_trust(*, envelope_bytes: bytes, root_documents: Mapping[str, bytes], key_record_documents: Mapping[str, bytes], acceptance_pin_descriptor: Mapping[str, object], acceptance_expected_pin_hash: str, current_pin_descriptor: Mapping[str, object], current_expected_pin_hash: str, acceptance_head: HistoryHead, current_head: HistoryHead, acceptance_time: str, current_time: str, payload_bytes: bytes | None = None, taxonomy_matrix_bytes: bytes = b"{}") -> TrustBoundaryResult:
    from scripts.quality import issue434_authority_evidence_reconstruction as closed

    return _closed_boundary(closed.resolve_complete_evidence(envelope_bytes=envelope_bytes, payload_bytes=payload_bytes, root_documents=root_documents, key_record_documents=key_record_documents, acceptance_pin_descriptor=acceptance_pin_descriptor, acceptance_expected_pin_hash=acceptance_expected_pin_hash, current_pin_descriptor=current_pin_descriptor, current_expected_pin_hash=current_expected_pin_hash, acceptance_head=acceptance_head, current_head=current_head, acceptance_time=acceptance_time, current_time=current_time, taxonomy_matrix_bytes=taxonomy_matrix_bytes))


def main() -> int:
    """Report availability without reading input or activating authority."""

    print("AuthorityEvidenceTrustV1: READY; authorityEffect=NO_AUTHORITY_EFFECT; activation=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
