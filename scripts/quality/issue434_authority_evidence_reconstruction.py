#!/usr/bin/env python3
"""Closed offline trust and retained-evidence verification for Issue #434."""
# ruff: noqa: E302, E305

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, cast

from scripts.quality import issue431_authority_core as child_a
from scripts.quality import issue434_authority_evidence_trust as core

PIN_MEMBERS = frozenset("schemaVersion repository programId generationId producerId evaluationPhase rootContentHashes".split())
PROHIBITED = ["ACTIVATE_AUTHORITY", "DERIVE_ROOT_PIN", "GENERATE_KEY", "NETWORK_LOOKUP", "PERSIST_EVIDENCE", "SIGN"]
FROZEN_ARTIFACT_SHA256 = {"AUTHORITY_EVIDENCE_AND_TRUST_V1.md":"68379644c1827fc2f35d619186717f74cd44754db9508183a7a10b40fb6833fc","authority-evidence-trust-state-matrices-v1.json":"34a60bb3318b6c7477519238839f034496d2c36507dd4ae1f87144a448de7cf4","authority-evidence-envelope-v1.schema.json":"4e699c1223c20790b5dbcfb461fa72978448474a7de348aa0267e2befe334585","authority-evidence-reconstruction-v1.schema.json":"7951450388b8e78650a380e852ac95bd9114b67cdaae24c73122f365273ad65b","authority-producer-key-v1.schema.json":"90c47cf64be8815fbbfe8a3e074929d767f71696ee8bfdeb63ebf09da30f4ba6","authority-producer-trust-root-v1.schema.json":"5b39ebcf62de1e515ed453ab9700c2dfea5364e85419f4b2d6083bf49074f8ed"}
MEDIA = {
    name: f"application/vnd.narratwin.authority.{name.lower().replace('_', '-')}-v1+json"
    for name in "BOUNDARY_SET CHECK_SET CLOSEOUT_RECEIPT CONTENT_REFERENCE ISSUE_STATUS LINKAGE_SET MERGE_RECEIPT NEGATIVE_ASSERTION OWNER_DECISION REASON REVIEW_ATTESTATION TIME_ASSERTION".split()
}
ROOT_AUTH_MEMBERS = frozenset({"keyId", "publicKeyHex"})
GENESIS_MEMBERS = frozenset({"activationTime", "keyId", "keyObjectId", "publicKeyHex", "revision"})
GOVERNANCE = Path(__file__).resolve().parents[2] / "docs" / "governance"
@dataclass(frozen=True)
class ClosedResult:
    findings: tuple[core.Finding, ...]
    valid: bool = False; structural_invalidation_applies: bool = False  # noqa: E702
    issuing_key_eligible: bool = False; trusted: bool = False  # noqa: E702
    historical_verdict: core.Verdict | None = None; current_verdict: core.Verdict | None = None  # noqa: E702
    historical_findings: tuple[core.Finding, ...] = (); current_findings: tuple[core.Finding, ...] = ()  # noqa: E702
    reconstruction_status: str | None = None; authorization_evaluated: bool = False  # noqa: E702
    root_invalidation_applied: bool = False
    authority_effect: Literal["NO_AUTHORITY_EFFECT"] = field(default=core.NO_AUTHORITY_EFFECT, init=False)
    activation: Literal["NONE"] = field(default=core.ACTIVATION, init=False)
def _result(codes: list[str] | tuple[str, ...], *, valid: bool = False, structural_invalidation_applies: bool = False, issuing_key_eligible: bool = False, trusted: bool = False, historical_verdict: core.Verdict | None = None, current_verdict: core.Verdict | None = None, reconstruction_status: str | None = None, historical_findings: list[str] | None = None, current_findings: list[str] | None = None) -> ClosedResult:
    findings = tuple(core.Finding(code) for code in sorted(set(codes)))
    return ClosedResult(findings, valid=valid and not findings,
                        structural_invalidation_applies=structural_invalidation_applies and not findings,
                        issuing_key_eligible=issuing_key_eligible and not findings,
                        trusted=trusted and not findings, historical_verdict=historical_verdict,
                        current_verdict=current_verdict, reconstruction_status=reconstruction_status,
                        historical_findings=tuple(core.Finding(code) for code in sorted(set(historical_findings if historical_findings is not None else ([] if historical_verdict is core.Verdict.VALID else codes)))), current_findings=tuple(core.Finding(code) for code in sorted(set(current_findings if current_findings is not None else ([] if current_verdict is core.Verdict.VALID else codes)))))
def _parse(raw: object, *, code: str) -> tuple[dict[str, object] | None, list[str]]:
    if not isinstance(raw, bytes):
        return None, [code]
    try:
        return core._parse_json_object(raw, max_bytes=core.RETAINED_BLOB_MAX_BYTES), []
    except core.AuthorityEvidenceTrustError as exc:
        return None, [f"{code}_{exc.code}"]
def _schema_codes(value: object, filename: str) -> list[str]:
    try:
        raw = (GOVERNANCE / "schemas" / filename).read_bytes()
    except OSError:
        return ["CONTRACT_SCHEMA_UNAVAILABLE"]
    if hashlib.sha256(raw).hexdigest() != FROZEN_ARTIFACT_SHA256[filename]: return ["CONTRACT_ARTIFACT_IDENTITY_MISMATCH"]  # noqa: E701
    schema, codes = _parse(raw, code="CONTRACT_SCHEMA_INVALID")
    return codes if schema is None else [item.code for item in core.validate_closed_schema_value(value, schema)]
def _time(value: object) -> datetime | None:
    return core._utc_value(value)
def _strings(value: object) -> set[str] | None:
    return set(value) if isinstance(value, list) and all(isinstance(item, str) for item in value) else None
def _pin_hash(descriptor: Mapping[str, object]) -> str:
    return hashlib.sha256(core.PIN_DOMAIN + core.canonical_bytes(descriptor)).hexdigest()
def _pin_codes(descriptor: object, expected_hash: object, phase: str,
               scope: tuple[str, str, str, str]) -> list[str]:
    codes: list[str] = []
    if not isinstance(descriptor, dict):
        return ["ROOT_PIN_DESCRIPTOR_REQUIRED" if descriptor is None else "ROOT_PIN_DESCRIPTOR_INVALID"]
    try:
        core._check_json_value(descriptor)
    except core.AuthorityEvidenceTrustError:
        codes.append("ROOT_PIN_DESCRIPTOR_INVALID");return codes  # noqa: E702
    if set(descriptor) != PIN_MEMBERS or descriptor.get("schemaVersion") != "AuthorityRootPinSetV1":
        codes.append("ROOT_PIN_DESCRIPTOR_INVALID")
    actual_scope = tuple(descriptor.get(name) for name in ("repository", "programId", "generationId", "producerId"))
    if any(not isinstance(item, str) or not minimum <= len(item) <= maximum for item, (minimum, maximum) in zip(actual_scope, ((3, 512), (3, 128), (3, 128), (3, 128)), strict=True)): codes.append("ROOT_PIN_DESCRIPTOR_INVALID")  # noqa: E701
    if actual_scope != scope or any(not isinstance(item, str) for item in actual_scope):
        codes.append("ROOT_PIN_SCOPE_MISMATCH")
    if descriptor.get("evaluationPhase") != phase:
        codes.append("ROOT_PIN_PHASE_MISMATCH")
    hashes = descriptor.get("rootContentHashes")
    if not isinstance(hashes, list) or not hashes or len(hashes) > 64 or any(not isinstance(item, str) or not core.LOWER_SHA256.fullmatch(item) for item in hashes):
        codes.append("ROOT_PIN_DESCRIPTOR_INVALID")
    else:
        if len(hashes) != len(set(hashes)):
            codes.append("ROOT_PIN_DUPLICATE")
        if hashes != sorted(hashes):
            codes.append("ROOT_PIN_ORDER")
    if expected_hash is None:
        codes.append("ROOT_PIN_SET_HASH_REQUIRED")
    elif not isinstance(expected_hash, str) or not core.LOWER_SHA256.fullmatch(expected_hash):
        codes.append("ROOT_PIN_SET_HASH_INVALID")
    else:
        try:
            if "ROOT_PIN_DESCRIPTOR_INVALID" not in codes and _pin_hash(descriptor) != expected_hash:
                codes.append("ROOT_PIN_SET_HASH_MISMATCH")
        except core.AuthorityEvidenceTrustError:
            codes.append("ROOT_PIN_DESCRIPTOR_INVALID")
    return codes
def validate_pin_transition(*, acceptance_descriptor: object, acceptance_expected_hash: object,
                            current_descriptor: object, current_expected_hash: object,
                            expected_scope: tuple[str, str, str, str]) -> ClosedResult:
    codes = _pin_codes(acceptance_descriptor, acceptance_expected_hash, "ACCEPTANCE", expected_scope)
    codes += _pin_codes(current_descriptor, current_expected_hash, "CURRENT", expected_scope)
    if isinstance(acceptance_descriptor, Mapping) and isinstance(current_descriptor, Mapping):
        acceptance = acceptance_descriptor.get("rootContentHashes")
        current = current_descriptor.get("rootContentHashes")
        if isinstance(acceptance, list) and isinstance(current, list) and all(isinstance(item, str) for item in acceptance + current) and not set(acceptance) <= set(current):
            codes.append("ROOT_PIN_ROLLBACK")
    return _result(codes, valid=not codes)
def _root_history_codes(documents: Mapping[str, object]) -> list[str]:
    roots = {digest: root for digest, raw in documents.items() if isinstance(digest, str) and (root := _parse(raw, code="ROOT_DOCUMENT_INVALID")[0]) is not None}; codes: list[str] = []  # noqa: E702
    roots = {digest: root for digest, root in roots.items() if not _schema_codes(root, "authority-producer-trust-root-v1.schema.json")}
    predecessors: dict[object, int] = {}; identities: set[tuple[object, object]] = set()  # noqa: E702
    for digest, root in roots.items():
        predecessor = root.get("predecessorRootContentHash"); version = root.get("rootVersion"); identity = (root.get("rootId"), version); prior = roots.get(predecessor) if isinstance(predecessor, str) else None  # noqa: E702
        if predecessor is not None and (isinstance(version, bool) or not isinstance(version, int) or prior is None or prior.get("rootVersion") != version - 1): codes.append("ROOT_PREDECESSOR_MISMATCH")  # noqa: E701
        if predecessor is not None: predecessors[predecessor] = predecessors.get(predecessor, 0) + 1  # noqa: E701
        if identity in identities: codes.append("ROOT_HISTORY_CONFLICT")  # noqa: E701
        identities.add(identity)
    if any(count > 1 for count in predecessors.values()) or sum(root.get("predecessorRootContentHash") is None for root in roots.values()) > 1: codes.append("ROOT_HISTORY_CONFLICT")  # noqa: E701
    return codes
def _key_binding_codes(root: Mapping[str, object]) -> list[str]:
    codes: list[str] = []
    for name, members, code in (
        ("rootAuthorizationKey", ROOT_AUTH_MEMBERS, "ROOT_AUTHORIZATION_KEY_ID_MISMATCH"),
        ("genesisCaptureKey", GENESIS_MEMBERS, "GENESIS_KEY_BINDING_MISMATCH"),
    ):
        binding = root.get(name)
        if not isinstance(binding, Mapping) or set(binding) != members:
            codes.append(code)
            continue
        public_key = binding.get("publicKeyHex")
        if (
            not isinstance(public_key, str)
            or not core.LOWER_SHA256.fullmatch(public_key)
            or binding.get("keyId") != core._public_key_id(public_key)
        ):
            codes.append(code)
        if name == "genesisCaptureKey" and (
            binding.get("revision") != 1
            or not isinstance(binding.get("keyObjectId"), str)
            or _time(binding.get("activationTime")) is None
        ):
            codes.append(code)
    return codes
def _validate_closed_root(*, root_bytes: object, expected_root_hash: object, pin_descriptor: object, expected_pin_set_hash: object, expected_phase: str, expected_scope: tuple[str, str, str, str], evaluation_time: object, temporal: bool) -> ClosedResult:
    root, codes = _parse(root_bytes, code="ROOT_DOCUMENT_INVALID")
    codes += _pin_codes(
        pin_descriptor,
        expected_pin_set_hash,
        expected_phase,
        expected_scope,
    )
    if root is None:
        return _result(codes)
    schema_codes = _schema_codes(root, "authority-producer-trust-root-v1.schema.json"); codes += schema_codes + (["ROOT_CLOSED_SHAPE"] if {"MISSING_MEMBER", "UNKNOWN_MEMBER"} & set(schema_codes) else [])  # noqa: E702
    if tuple(
        root.get(name)
        for name in ("repository", "programId", "generationId", "producerId")
    ) != expected_scope:
        codes.append("ROOT_PIN_SCOPE_MISMATCH")
    try:
        actual_hash = core.content_hash(
            core.ContentKind.TRUST_ROOT,
            core.TRUST_ROOT_SCHEMA_VERSION,
            root,
        )
    except core.AuthorityEvidenceTrustError:
        actual_hash = None
    if (
        not isinstance(expected_root_hash, str)
        or not core.LOWER_SHA256.fullmatch(expected_root_hash)
        or actual_hash != expected_root_hash
        or root.get("contentHash") != expected_root_hash
        or root_bytes != core.canonical_bytes(root)
    ):
        codes.append("ROOT_CONTENT_HASH_MISMATCH")
    hashes = (
        pin_descriptor.get("rootContentHashes")
        if isinstance(pin_descriptor, Mapping)
        else None
    )
    if not isinstance(hashes, list) or expected_root_hash not in hashes:
        codes.append("ROOT_PIN_REQUIRED")
    codes += _key_binding_codes(root)
    if (
        root.get("signatureAlgorithm") != "Ed25519"
        or root.get("publicKeyEncoding") != "RAW_32_BYTE_LOWER_HEX"
    ):
        codes.append("ROOT_ALGORITHM_PROFILE")
    if (
        root.get("recoverySemantics") != "INDEPENDENT_SUCCESSOR_PIN_ONLY"
        or root.get("revocationSemantics")
        != "INDEPENDENT_SUCCESSOR_PIN_WITH_EXACT_PRIOR_ROOT_BOUNDARY_ONLY"
    ):
        codes.append("ROOT_RECOVERY_SEMANTICS")
    if root.get("prohibitedCapabilities") != PROHIBITED:
        codes.append("ROOT_CAPABILITY_BOUNDARY")
    version = root.get("rootVersion")
    predecessor = root.get("predecessorRootContentHash")
    compromise = root.get("priorRootCompromise")
    if (version == 1) != (predecessor is None):
        codes.append("ROOT_PREDECESSOR_VERSION_MISMATCH")
    if compromise is not None and (
        not isinstance(compromise, Mapping)
        or set(compromise) != {"priorRootContentHash", "invalidatesPriorRootFrom"}
        or compromise.get("priorRootContentHash") != predecessor
        or _time(compromise.get("invalidatesPriorRootFrom")) is None
    ):
        codes.append("ROOT_COMPROMISE_INVALID")
    now, valid_from, expires = (
        _time(evaluation_time),
        _time(root.get("validFrom")),
        _time(root.get("expiresAt")),
    )
    if valid_from is None or expires is None or (temporal and now is None) or (
        valid_from is not None and expires is not None and valid_from >= expires
    ):
        codes.append("TIME_FORMAT")
    elif temporal and cast(datetime, now) < valid_from:
        codes.append("ROOT_NOT_YET_VALID")
    elif temporal and cast(datetime, now) >= expires:
        codes.append("ROOT_EXPIRED")
    return _result(codes, valid=not codes)
def validate_closed_root(*, root_bytes: object, expected_root_hash: object, pin_descriptor: object, expected_pin_set_hash: object, expected_phase: str, expected_scope: tuple[str, str, str, str], evaluation_time: object) -> ClosedResult:
    return _validate_closed_root(root_bytes=root_bytes, expected_root_hash=expected_root_hash, pin_descriptor=pin_descriptor, expected_pin_set_hash=expected_pin_set_hash, expected_phase=expected_phase, expected_scope=expected_scope, evaluation_time=evaluation_time, temporal=True)
def resolve_root_invalidation(*, root_documents: object, pin_descriptor: object, expected_pin_set_hash: object, expected_scope: tuple[str, str, str, str], prior_root_content_hash: object, evaluation_time: object, expected_phase: object = "CURRENT", authorization_time: object = None) -> ClosedResult:
    phase = expected_phase if isinstance(expected_phase, str) else "INVALID"
    codes = _pin_codes(
        pin_descriptor,
        expected_pin_set_hash,
        phase if phase in {"ACCEPTANCE", "CURRENT"} else "INVALID",
        expected_scope,
    )
    if not isinstance(root_documents, dict) or not isinstance(pin_descriptor, dict):
        return _result(codes + ["ROOT_DOCUMENT_INVALID"])
    if len(root_documents) > 64: return _result(codes + ["ROOT_DOCUMENT_LIMIT"])  # noqa: E701
    if codes: return _result(codes)  # noqa: E701
    pins = pin_descriptor.get("rootContentHashes")
    if not isinstance(pins, list) or any(not isinstance(item, str) for item in pins):
        return _result(codes + ["ROOT_PIN_DESCRIPTOR_INVALID"])
    if set(root_documents) != set(pins):
        codes.append("ROOT_DOCUMENT_SET_MISMATCH")
    codes += _root_history_codes(root_documents)
    now, authorization = _time(evaluation_time), _time(authorization_time) if authorization_time is not None else _time(evaluation_time)
    if now is None or authorization is None:
        codes.append("TIME_FORMAT")
    applies = False; boundaries: list[datetime] = []  # noqa: E702
    for expected_hash, raw in root_documents.items():
        root, _ = _parse(raw, code="ROOT_DOCUMENT_INVALID"); compromise = root.get("priorRootCompromise") if root is not None else None; relevant = root is not None and root.get("predecessorRootContentHash") == prior_root_content_hash and isinstance(compromise, Mapping) and compromise.get("priorRootContentHash") == prior_root_content_hash  # noqa: E702
        result = _validate_closed_root(
            root_bytes=raw,
            expected_root_hash=expected_hash,
            pin_descriptor=pin_descriptor,
            expected_pin_set_hash=expected_pin_set_hash,
            expected_phase=phase,
            expected_scope=expected_scope,
            evaluation_time=evaluation_time,
            temporal=relevant,
        )
        codes += [item.code for item in result.findings]
        if not result.valid or root is None:
            continue
        if relevant and isinstance(compromise, Mapping):
            boundary = _time(compromise.get("invalidatesPriorRootFrom"))
            if boundary is not None: boundaries.append(boundary)  # noqa: E701
    if len(set(boundaries)) > 1: codes.append("ROOT_INVALIDATION_CONFLICT")  # noqa: E701
    applies = not codes and authorization is not None and any(authorization >= boundary for boundary in boundaries)
    return _result(codes, structural_invalidation_applies=applies)
def inspect_key_history(**kwargs: object) -> ClosedResult:
    result = core.inspect_key_history_structure(**cast(Any, kwargs))
    codes = [item.code for item in result.findings]
    return _result(codes, valid=not codes)
def resolve_issuing_key(*, records: object, expected_head: object, issuing_key: object,
                        capture_time: object,
                        evaluation_time: object | None = None) -> ClosedResult:
    if not isinstance(records, tuple) or not all(isinstance(item, Mapping) for item in records):
        return _result(["KEY_RECORD_INVALID"])
    if not isinstance(expected_head, core.HistoryHead) or not isinstance(issuing_key, tuple):
        return _result(["KEY_RECORD_INVALID"])
    result = core.resolve_issuing_key_structure(
        records=cast(tuple[Mapping[str, object], ...], records),
        expected_head=expected_head,
        issuing_key=issuing_key,
        capture_time=cast(str, capture_time),
        evaluation_time=cast(str | None, evaluation_time),
    )
    return _result(
        [item.code for item in result.findings],
        issuing_key_eligible=result.issuing_key_eligible,
    )
def validate_subject_phase(*, envelope: object, root: object, taxonomy_matrix_bytes: object, evaluation_time: object) -> ClosedResult:
    codes: list[str] = []
    if not isinstance(envelope, Mapping) or not isinstance(root, Mapping):
        return _result(["SUBJECT_BINDING_INVALID"])
    try: core.canonical_bytes(envelope)  # noqa: E701
    except core.AuthorityEvidenceTrustError: return _result(["SUBJECT_BINDING_INVALID"])  # noqa: E701
    if set(core.ENVELOPE_MEMBERS).issubset(envelope):
        codes += _schema_codes(envelope, "authority-evidence-envelope-v1.schema.json")
    matrix, parse_codes = _parse(taxonomy_matrix_bytes, code="TAXONOMY_INVALID")
    codes += parse_codes
    if matrix is None:
        return _result(codes)
    taxonomy = matrix.get("typedReferenceTaxonomy")
    rows = taxonomy if isinstance(taxonomy, list) else []
    reference_type = envelope.get("typedReferenceType")
    row = next(
        (
            item
            for item in rows
            if isinstance(item, Mapping)
            and item.get("typedReferenceType") == reference_type
        ),
        None,
    )
    subject = envelope.get("subject")
    transition = subject.get("transitionRowId") if isinstance(subject, Mapping) else None
    permitted = row.get("permittedRows") if isinstance(row, Mapping) else None
    fields = ("evidenceRole", "producerTrustClass", "freshnessClass", "payloadClass")
    if (
        row is None
        or not isinstance(permitted, list)
        or transition not in permitted
        or any(envelope.get(name) != row.get(name) for name in fields)
    ):
        codes.append("TAXONOMY_BINDING_MISMATCH")
    media = matrix.get("payloadMediaTypeByClass")
    payload_class = envelope.get("payloadClass"); expected_media = media.get(payload_class) if isinstance(media, Mapping) and isinstance(payload_class, str) else None  # noqa: E702
    if envelope.get("payloadMediaType") != expected_media:
        codes.append("PAYLOAD_MEDIA_TYPE_MISMATCH")
    try:
        frozen_raw = (GOVERNANCE / "authority-evidence-trust-state-matrices-v1.json").read_bytes()
    except OSError:
        frozen_raw = b""
    frozen, frozen_codes = _parse(frozen_raw, code="TAXONOMY_CONTRACT_INVALID")
    if hashlib.sha256(frozen_raw).hexdigest() != FROZEN_ARTIFACT_SHA256["authority-evidence-trust-state-matrices-v1.json"]:
        codes.append("CONTRACT_ARTIFACT_IDENTITY_MISMATCH")
    elif taxonomy_matrix_bytes != frozen_raw: codes.append("TAXONOMY_CONTRACT_MISMATCH")  # noqa: E701
    elif frozen is None:
        codes += frozen_codes
    else:
        frozen_rows = frozen.get("typedReferenceTaxonomy")
        expected_row = next((item for item in frozen_rows if isinstance(item, Mapping) and item.get("typedReferenceType") == reference_type), None) if isinstance(frozen_rows, list) else None
        frozen_permitted = expected_row.get("permittedRows") if isinstance(expected_row, Mapping) else None
        if not isinstance(frozen_permitted, list) or transition not in frozen_permitted or any(envelope.get(name) != cast(Mapping[str, object], expected_row).get(name) for name in fields):
            codes.append("TAXONOMY_CONTRACT_MISMATCH")
    allowed = (
        ("allowedSubjectSchemaVersions", subject.get("schemaVersion") if isinstance(subject, Mapping) else None),
        ("allowedTransitionRows", transition),
        ("allowedEvidenceRoles", envelope.get("evidenceRole")),
        ("allowedPayloadMediaTypes", envelope.get("payloadMediaType")),
    )
    if any(not isinstance(root.get(name), list) or value not in root.get(name, []) for name, value in allowed):
        codes.append("ROOT_POLICY_MISMATCH")
    if isinstance(subject, Mapping):
        edges = child_a.ROUTE_EDGES if subject.get("schemaVersion") == "ActiveProgramRouteV1" else child_a.DECISION_EDGES
        expected_edge = next((edge for edge in edges if edge[0] == transition), None)
        if expected_edge is None or tuple(subject.get(name) for name in ("sourceState", "operation", "targetState")) != expected_edge[1:]:
            codes.append("SUBJECT_TRANSITION_MISMATCH")
    observed, captured, not_before, expires, now = (
        _time(envelope.get("observedAt")),
        _time(envelope.get("capturedAt")),
        _time(envelope.get("notBefore")),
        _time(envelope.get("expiresAt")),
        _time(evaluation_time),
    )
    if None in (observed, captured, not_before, expires, now):
        codes.append("TIME_FORMAT")
    else:
        if cast(datetime, captured) < cast(datetime, observed):
            codes.append("CAPTURE_PRECEDES_OBSERVATION")
        if cast(datetime, captured) > cast(datetime, now): codes.append("CAPTURE_AFTER_EVALUATION")  # noqa: E701
        root_start, root_end = _time(root.get("validFrom")), _time(root.get("expiresAt"))
        if root_start is None or root_end is None or not root_start <= cast(datetime, captured) < root_end: codes.append("ROOT_CAPTURE_WINDOW")  # noqa: E701
        if cast(datetime, not_before) >= cast(datetime, expires):
            codes.append("ENVELOPE_TIME_WINDOW")
        if cast(datetime, now) < cast(datetime, not_before):
            codes.append("ENVELOPE_NOT_YET_VALID")
        if cast(datetime, now) >= cast(datetime, expires):
            codes.append("ENVELOPE_EXPIRED")
        policies = root.get("freshnessPolicies")
        policy = next((item for item in policies if isinstance(item, Mapping) and item.get("transitionRowId") == transition and item.get("evidenceRole") == envelope.get("evidenceRole") and item.get("freshnessClass") == envelope.get("freshnessClass")), None) if isinstance(policies, list) else None
        if not isinstance(policy, Mapping):
            codes.append("FRESHNESS_POLICY_REQUIRED")
        else:
            limits = tuple(policy.get(name) for name in ("maxCaptureDelaySeconds", "maxObservationAgeSeconds", "maxEnvelopeLifetimeSeconds"))
            if any(isinstance(limit, bool) or not isinstance(limit, int) for limit in limits): codes.append("FRESHNESS_POLICY_INVALID")  # noqa: E701
            elif ((cast(datetime, captured) - cast(datetime, observed)).total_seconds() > cast(int, limits[0]) or (envelope.get("freshnessClass") != "IMMUTABLE" and (cast(datetime, now) - cast(datetime, observed)).total_seconds() > cast(int, limits[1])) or (cast(datetime, expires) - cast(datetime, not_before)).total_seconds() > cast(int, limits[2])): codes.append("FRESHNESS_EXCEEDED")  # noqa: E701
    return _result(codes, valid=not codes)
def _object_nodes(value: object) -> list[Mapping[str, object]]:
    nodes: list[Mapping[str, object]] = []
    if isinstance(value, Mapping):
        if value.get("type") == "object":
            nodes.append(value)
        for child in value.values():
            nodes += _object_nodes(child)
    elif isinstance(value, list):
        for child in value:
            nodes += _object_nodes(child)
    return nodes
def validate_artifact_set(*, artifacts: object, child_a_matrix_bytes: object,
                          expected_artifact_hashes: object = None) -> ClosedResult:
    if not isinstance(artifacts, Mapping):
        return _result(["CONTRACT_ARTIFACT_INVALID"])
    required = {
        "docs/governance/AUTHORITY_EVIDENCE_AND_TRUST_V1.md",
        "docs/governance/authority-evidence-trust-state-matrices-v1.json",
        "docs/governance/schemas/authority-evidence-envelope-v1.schema.json",
        "docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json",
        "docs/governance/schemas/authority-producer-key-v1.schema.json",
        "docs/governance/schemas/authority-producer-trust-root-v1.schema.json",
    }
    if len(artifacts) > len(required): return _result(["CONTRACT_ARTIFACT_INVALID"])  # noqa: E701
    codes: list[str] = []
    if set(artifacts) != required:
        codes.append("CONTRACT_ARTIFACT_MISSING")
    if any(not isinstance(path, str) or not isinstance(raw, bytes) for path, raw in artifacts.items()):
        return _result(codes + ["CONTRACT_ARTIFACT_INVALID"])
    if any(FROZEN_ARTIFACT_SHA256.get(path.rsplit("/", 1)[-1]) != hashlib.sha256(raw).hexdigest() for path, raw in artifacts.items()):
        codes.append("ARTIFACT_IDENTITY_MISMATCH")
    if isinstance(expected_artifact_hashes, Mapping):
        if set(artifacts) != set(expected_artifact_hashes) or any(
            not isinstance(expected_artifact_hashes.get(path), str)
            or hashlib.sha256(raw).hexdigest() != expected_artifact_hashes.get(path)
            for path, raw in artifacts.items()
        ):
            codes.append("ARTIFACT_IDENTITY_MISMATCH")
    markdown = next((raw for path, raw in artifacts.items() if path.endswith("AUTHORITY_EVIDENCE_AND_TRUST_V1.md")), None)
    if not isinstance(markdown, bytes):
        codes.append("CONTRACT_ARTIFACT_MISSING")
    else:
        try:
            text = markdown.decode("ascii")
        except UnicodeDecodeError:
            codes.append("NORMATIVE_CONTRACT_INVALID")
        else:
            for marker in (
                "Activation is `NONE`",
                "NO_AUTHORITY_EFFECT",
                "CONFLICTING > INVALID > UNAVAILABLE > VALID",
                "## Key lifecycle and heads",
                "## Closed objects",
            ):
                if marker not in text:
                    codes.append("NORMATIVE_CONTRACT_INVALID")
    json_values: dict[str, dict[str, object]] = {}
    for path, raw in artifacts.items():
        if not path.endswith(".json"):
            continue
        value, parse_codes = _parse(raw, code="CONTRACT_MATRIX_INVALID")
        parse_codes = ["CONTRACT_MATRIX_INVALID" if code.startswith("CONTRACT_MATRIX_INVALID_") else code for code in parse_codes]
        codes += parse_codes
        if value is not None:
            json_values[path.rsplit("/", 1)[-1]] = value
    child, child_codes = _parse(child_a_matrix_bytes, code="CHILD_A_MATRIX_INVALID")
    codes += child_codes
    matrix = json_values.get("authority-evidence-trust-state-matrices-v1.json")
    if matrix is None or child is None:
        return _result(codes or ["CONTRACT_MATRIX_INVALID"])
    transitions = [
        row
        for table in cast(list[object], child.get("matrices") if isinstance(child.get("matrices"), list) else [])
        if isinstance(table, Mapping)
        for row in cast(list[object], table.get("legalTransitions") if isinstance(table.get("legalTransitions"), list) else [])
        if isinstance(row, Mapping)
    ]
    child_rows = {cast(str, row["id"]): row.get("requiredTypedReferences") for row in transitions if isinstance(row.get("id"), str)}
    child_types = sorted({
        item
        for values in child_rows.values()
        if isinstance(values, list)
        for item in values
        if isinstance(item, str)
    })
    if matrix.get("typedReferenceTypes") != child_types or matrix.get("reverseTransitionRequirements") != child_rows:
        codes.append("CHILD_A_TAXONOMY_MISMATCH")
    if not isinstance(matrix.get("typedReferenceTypes"), list) or len(cast(list[object], matrix["typedReferenceTypes"])) != 44:
        codes.append("TAXONOMY_CARDINALITY")
    if not isinstance(matrix.get("reverseTransitionRequirements"), Mapping) or len(cast(Mapping[object, object], matrix["reverseTransitionRequirements"])) != 32:
        codes.append("REVERSE_ROW_CARDINALITY")
    taxonomy = matrix.get("typedReferenceTaxonomy")
    if not isinstance(taxonomy, list) or len(taxonomy) != 44:
        codes.append("TAXONOMY_CARDINALITY")
    else:
        for row in taxonomy:
            if not isinstance(row, Mapping):
                codes.append("CHILD_A_TAXONOMY_MISMATCH")
                continue
            ref = row.get("typedReferenceType")
            permitted = sorted(
                key for key, values in child_rows.items()
                if isinstance(key, str) and isinstance(values, list) and ref in values
            )
            if set(row) != {"typedReferenceType", "permittedRows", "evidenceRole", "producerTrustClass", "freshnessClass", "payloadClass"} or row.get("permittedRows") != permitted:
                codes.append("CHILD_A_TAXONOMY_MISMATCH")
    media = matrix.get("payloadMediaTypeByClass")
    if not isinstance(media, Mapping) or len(media) != 12:
        codes.append("PAYLOAD_MIME_CARDINALITY")
    elif any(not isinstance(value, str) for value in media.values()) or len(set(media.values())) != 12:
        codes.append("PAYLOAD_MIME_BIJECTION")
    if media != MEDIA:
        codes.append("COORDINATED_CONTRACT_MUTATION")
    if matrix.get("verdictPrecedence") != ["CONFLICTING", "INVALID", "UNAVAILABLE", "VALID"]:
        codes.append("VERDICT_PRECEDENCE_MISMATCH")
    domains = matrix.get("contentDomains")
    if not isinstance(domains, Mapping) or domains.get("AuthorityRootPinSetV1") != "NARRATWIN-AUTHORITY-ROOT-PIN-SET-V1":
        codes.append("ROOT_PIN_DOMAIN_MISMATCH")
    lifecycle = matrix.get("keyLifecycle")
    if not isinstance(lifecycle, list) or len(lifecycle) != 5 or any(not isinstance(row, Mapping) for row in lifecycle):
        codes.append("K02_CONTRACT_MISMATCH")
    else:
        if lifecycle[0].get("operation") != "ISSUE_GENESIS" or lifecycle[1].get("predecessorEligibility") != "UNTIL_EXPLICIT_K03_RETIREMENT":
            codes.append("K02_CONTRACT_MISMATCH")
        if lifecycle[3].get("source") != "ACTIVE" or lifecycle[4].get("source") != "RETIRED":
            codes.append("K04_K05_DISTINCT")
    schemas = [value for name, value in json_values.items() if name.endswith("schema.json")]
    if any(node.get("closed") is not True for schema in schemas for node in _object_nodes(schema)):
        codes.append("NESTED_CLOSURE_REQUIRED")
    if any(
        not isinstance(schema.get("root"), Mapping)
        or _strings(cast(Mapping[str, object], schema["root"]).get("required"))
        != set(cast(Mapping[object, object], cast(Mapping[str, object], schema["root"]).get("properties", {})))
        for schema in schemas
    ):
        codes.append("REQUIRED_SURFACE_MISMATCH")
    by_contract = {cast(str, schema["contractVersion"]): schema for schema in schemas if isinstance(schema.get("contractVersion"), str)}
    root_schema = by_contract.get(core.TRUST_ROOT_SCHEMA_VERSION, {})
    root_node = cast(Mapping[str, object], root_schema).get("root", {}) if isinstance(root_schema, Mapping) else {}
    root_properties = root_node.get("properties", {}) if isinstance(root_node, Mapping) else {}
    if not isinstance(root_properties, Mapping) or not {"predecessorRootContentHash", "priorRootCompromise"} <= set(root_properties):
        codes.append("ROOT_PREDECESSOR_COMPROMISE_DISTINCT")
    if not isinstance(root_properties, Mapping) or "recoverySemantics" not in root_properties:
        codes.append("ROOT_RECOVERY_SEMANTICS_REQUIRED")
    if not isinstance(root_properties, Mapping) or "revocationSemantics" not in root_properties:
        codes.append("ROOT_REVOCATION_SEMANTICS_REQUIRED")
    reconstruction = cast(Mapping[str, object], by_contract.get("AuthorityEvidenceReconstructionV1", {})).get("root", {})
    reconstruction_map = cast(Mapping[str, object], reconstruction) if isinstance(reconstruction, Mapping) else {}
    reconstruction_properties = reconstruction_map.get("properties", {})
    status = cast(Mapping[str, object], reconstruction_properties).get("reconstructionStatus", {}) if isinstance(reconstruction_properties, Mapping) else {}
    if not isinstance(status, Mapping) or status.get("enum") != ["COMPLETE", "UNAVAILABLE", "CONFLICTING", "INVALID"]:
        codes.append("RECONSTRUCTION_STATUS_SET")
    conditions = reconstruction_map.get("conditions") if isinstance(reconstruction_map.get("conditions"), list) else []
    if not any("exact set" in item for item in cast(list[object], conditions) if isinstance(item, str)):
        codes.append("RETAINED_EXACT_SET_REQUIRED")
    if not {"historicalVerdict", "currentVerdict", "historicalFindings", "currentFindings"} <= (_strings(reconstruction_map.get("required")) or set()):
        codes.append("HISTORICAL_CURRENT_SEPARATION_REQUIRED")
    return _result(codes, valid=not codes)
def reconstruct_retained_evidence(*, manifest_bytes: object, retained_blobs: object,
                                  evaluation_time: object, trust_inputs: object = None) -> ClosedResult:
    manifest, codes = _parse(manifest_bytes, code="RECONSTRUCTION_INVALID")
    if manifest is None or not isinstance(retained_blobs, Mapping):
        return _result(codes + ["RETAINED_BLOB_SET_MISMATCH"], reconstruction_status="INVALID")
    if len(retained_blobs) > 256: return _result(codes + ["BLOB_COUNT_LIMIT"], reconstruction_status="INVALID")  # noqa: E701
    codes += _schema_codes(manifest, "authority-evidence-reconstruction-v1.schema.json")
    if (manifest.get("revision") == 1) != (manifest.get("predecessorContentHash") is None): codes.append("RECONSTRUCTION_PREDECESSOR_REVISION_MISMATCH")  # noqa: E701
    if codes: return _result(codes, reconstruction_status="INVALID")  # noqa: E701
    try:
        if not isinstance(manifest_bytes, bytes) or manifest_bytes != core.canonical_bytes(manifest) or manifest.get("contentHash") != core.content_hash(core.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", manifest):
            codes.append("RECONSTRUCTION_CONTENT_HASH_MISMATCH")
    except core.AuthorityEvidenceTrustError:
        codes.append("RECONSTRUCTION_CONTENT_HASH_MISMATCH")
    groups = [manifest.get(name) for name in ("acceptanceRootPinReferences", "currentRootPinReferences", "rootReferences", "keyReferences")]
    pin_hashes = {item.get("contentHash") for group in groups[:2] if isinstance(group, list) for item in group if isinstance(item, Mapping)}
    references = [item for group in groups if isinstance(group, list) for item in group] + [manifest.get("envelopeReference"), manifest.get("payloadReference")]
    if any(not isinstance(item, Mapping) for item in references):
        return _result(codes + ["RECONSTRUCTION_REFERENCE_INVALID"], reconstruction_status="INVALID")
    expected = [cast(Mapping[str, object], item).get("contentHash") for item in references]
    if any(not isinstance(item, str) or not core.LOWER_SHA256.fullmatch(item) for item in expected):
        return _result(codes + ["RECONSTRUCTION_REFERENCE_INVALID"], reconstruction_status="INVALID")
    expected_hashes = cast(list[str], expected)
    if len(set(expected_hashes)) != len(expected_hashes) or [item.get("ordinal") for item in cast(list[Mapping[str, object]], references)] != list(range(len(references))):
        codes.append("RECONSTRUCTION_REFERENCE_INVALID")
    expected_roles = [("acceptanceRootPinReferences", "PAYLOAD", MEDIA["CONTENT_REFERENCE"]), ("currentRootPinReferences", "PAYLOAD", MEDIA["CONTENT_REFERENCE"]), ("rootReferences", "TRUST_ROOT", "application/vnd.narratwin.authority.producer-trust-root-v1+json"), ("keyReferences", "PRODUCER_KEY", "application/vnd.narratwin.authority.producer-key-v1+json")]
    if any(not isinstance(manifest.get(name), list) or any(not isinstance(item, Mapping) or item.get("role") != role or item.get("mediaType") != media for item in cast(list[object], manifest.get(name))) for name, role, media in expected_roles) or cast(Mapping[str, object], manifest.get("envelopeReference")).get("role") != "EVIDENCE_ENVELOPE" or cast(Mapping[str, object], manifest.get("envelopeReference")).get("mediaType") != "application/vnd.narratwin.authority.evidence-envelope-v1+json" or cast(Mapping[str, object], manifest.get("payloadReference")).get("role") != "PAYLOAD":
        codes.append("RECONSTRUCTION_REFERENCE_ROLE_MISMATCH")
    payload_media = MEDIA.get(cast(str, manifest.get("payloadClass")))
    if cast(Mapping[str, object], manifest.get("payloadReference")).get("mediaType") != payload_media:
        codes.append("RECONSTRUCTION_REFERENCE_MEDIA_MISMATCH")
    if any(not isinstance(digest, str) or not isinstance(blob, bytes) for digest, blob in retained_blobs.items()):
        return _result(codes + ["RETAINED_BLOB_INVALID"], reconstruction_status="INVALID")
    missing = set(expected_hashes) - set(retained_blobs)
    extra = set(retained_blobs) - set(expected_hashes)
    if missing:
        codes.append("RETAINED_BLOB_UNAVAILABLE")
    if extra:
        codes.append("RETAINED_BLOB_SET_MISMATCH")
    total = sum(len(cast(bytes, blob)) for blob in retained_blobs.values())
    if total > core.RETAINED_BLOBS_AGGREGATE_MAX_BYTES: return _result(codes + ["BLOB_AGGREGATE_SIZE_LIMIT"], reconstruction_status="INVALID")  # noqa: E701
    for index, reference in enumerate(cast(list[Mapping[str, object]], references)):
        digest = cast(str, reference["contentHash"])
        blob = retained_blobs.get(digest)
        if not isinstance(blob, bytes):
            continue
        maximum = core.PAYLOAD_MAX_BYTES if index == len(references) - 1 else core.RETAINED_BLOB_MAX_BYTES
        if len(blob) != reference.get("byteLength") or len(blob) > maximum:
            codes += ["RETAINED_BLOB_LENGTH_MISMATCH", "RETAINED_BLOB_HASH_MISMATCH"]; continue  # noqa: E702
        role, identity = reference.get("role"), None
        parsed: dict[str, object] | None = None
        if digest in pin_hashes or role in {"TRUST_ROOT", "PRODUCER_KEY", "EVIDENCE_ENVELOPE"}:
            parsed, parse_codes = _parse(blob, code="RETAINED_BLOB_INVALID")
            codes += parse_codes
            if parsed is not None and blob != core.canonical_bytes(parsed):
                codes.append("RETAINED_BLOB_CANONICAL_MISMATCH")
        if parsed is not None and digest in pin_hashes:
            identity = _pin_hash(parsed)
        elif parsed is not None and role in {"TRUST_ROOT", "PRODUCER_KEY", "EVIDENCE_ENVELOPE"}:
            kind = {"TRUST_ROOT": core.ContentKind.TRUST_ROOT, "PRODUCER_KEY": core.ContentKind.PRODUCER_KEY, "EVIDENCE_ENVELOPE": core.ContentKind.EVIDENCE_OBJECT}[role]
            schema = {"TRUST_ROOT": core.TRUST_ROOT_SCHEMA_VERSION, "PRODUCER_KEY": core.PRODUCER_KEY_SCHEMA_VERSION, "EVIDENCE_ENVELOPE": core.ENVELOPE_SCHEMA_VERSION}[role]
            codes += _schema_codes(parsed, {"TRUST_ROOT": "authority-producer-trust-root-v1.schema.json", "PRODUCER_KEY": "authority-producer-key-v1.schema.json", "EVIDENCE_ENVELOPE": "authority-evidence-envelope-v1.schema.json"}[role])
            try:
                identity = core.content_hash(kind, schema, parsed)
            except core.AuthorityEvidenceTrustError:
                identity = None
        else:
            identity = hashlib.sha256(blob).hexdigest()
        if identity != digest:
            codes.append("RETAINED_BLOB_HASH_MISMATCH")
    declared_total = sum(cast(int, item.get("byteLength", -1)) for item in cast(list[Mapping[str, object]], references))
    if manifest.get("retainedBlobCount") != len(references) or manifest.get("aggregateRetainedByteLength") != declared_total:
        codes.append("RECONSTRUCTION_COUNT_MISMATCH")
    now, retention = _time(evaluation_time), _time(manifest.get("retentionUntil"))
    if now is None or retention is None:
        codes.append("TIME_FORMAT")
    elif now >= retention:
        codes.append("RETENTION_EXPIRED")
    if not codes:
        if not isinstance(trust_inputs, Mapping):
            codes.append("RECONSTRUCTION_TRUST_INPUTS_UNAVAILABLE")
        else:
            trust_keys = {"envelope_bytes", "payload_bytes", "root_documents", "key_record_documents", "acceptance_pin_descriptor", "acceptance_expected_pin_hash", "current_pin_descriptor", "current_expected_pin_hash", "acceptance_head", "current_head", "acceptance_time", "current_time", "taxonomy_matrix_bytes"}
            if set(trust_inputs) != trust_keys: return _result(["RECONSTRUCTION_TRUST_INPUTS_INVALID"], reconstruction_status="INVALID")  # noqa: E701
            pin_bindings = (("acceptanceRootPinSetHash", "acceptanceRootPinReferences", "acceptance_expected_pin_hash"), ("currentRootPinSetHash", "currentRootPinReferences", "current_expected_pin_hash"))
            if any(manifest.get(digest_name) != trust_inputs.get(input_name) or manifest.get(digest_name) not in [item.get("contentHash") for item in cast(list[Mapping[str, object]], manifest.get(refs_name))] for digest_name, refs_name, input_name in pin_bindings) or any(not isinstance(trust_inputs.get(input_name), core.HistoryHead) or manifest.get(head_name) != {"rootContentHash": trust_inputs[input_name].root_content_hash, "producerId": trust_inputs[input_name].producer_id, "historySequence": trust_inputs[input_name].history_sequence, "keyRecordContentHash": trust_inputs[input_name].key_record_content_hash} for head_name, input_name in (("acceptanceHead", "acceptance_head"), ("currentHead", "current_head"))) or manifest.get("historicalEvaluationTime") != trust_inputs.get("acceptance_time") or manifest.get("currentEvaluationTime") != trust_inputs.get("current_time"): codes.append("RECONSTRUCTION_PIN_BINDING_MISMATCH")  # noqa: E701
            supplied = dict(trust_inputs)
            ref_blob: Callable[[object], object] = lambda value: retained_blobs.get(value.get("contentHash")) if isinstance(value, Mapping) else None  # noqa: E731
            retained_envelope, retained_codes = _parse(ref_blob(manifest.get("envelopeReference")), code="RETAINED_ENVELOPE_INVALID"); codes += retained_codes  # noqa: E702
            expected_subject = dict(cast(Mapping[str, object], retained_envelope.get("subject")), generationId=manifest.get("generationId")) if retained_envelope is not None and isinstance(retained_envelope.get("subject"), Mapping) else None
            if retained_envelope is None or manifest.get("subject") != expected_subject or any(manifest.get(name) != retained_envelope.get(name) for name in ("repository", "programId", "generationId", "typedReferenceType", "evidenceRole", "producerTrustClass", "freshnessClass", "payloadClass")): codes.append("RECONSTRUCTION_ENVELOPE_BINDING_MISMATCH")  # noqa: E701
            supplied.update(envelope_bytes=ref_blob(manifest.get("envelopeReference")), payload_bytes=ref_blob(manifest.get("payloadReference")), root_documents={item["contentHash"]: ref_blob(item) for item in cast(list[Mapping[str, object]], manifest.get("rootReferences"))}, key_record_documents={item["contentHash"]: ref_blob(item) for item in cast(list[Mapping[str, object]], manifest.get("keyReferences"))})
            trust = resolve_complete_evidence(**cast(Any, supplied))
            historical_claims = [{"code": item.code, "location": item.location} for item in trust.historical_findings]; current_claims = [{"code": item.code, "location": item.location} for item in trust.current_findings]  # noqa: E702
            if manifest.get("reconstructionStatus") != "COMPLETE" or manifest.get("historicalVerdict") != getattr(trust.historical_verdict, "value", None) or manifest.get("currentVerdict") != getattr(trust.current_verdict, "value", None) or manifest.get("historicalFindings") != historical_claims or manifest.get("currentFindings") != current_claims:
                codes.append("RECONSTRUCTED_TRUST_MISMATCH")
    status = "INVALID" if any("UNAVAILABLE" not in code and code != "RETENTION_EXPIRED" for code in codes) else "UNAVAILABLE" if codes else "COMPLETE"
    return _result(codes, valid=not codes, reconstruction_status=status)
def validate_evidence_replay_set(*, envelope_documents: object) -> ClosedResult:
    if not isinstance(envelope_documents, (tuple, list)) or len(envelope_documents) > 256: return _result(["EVIDENCE_REPLAY_SET_INVALID"])  # noqa: E701
    identities: dict[tuple[object, ...], bytes] = {}; lineage: dict[tuple[object, ...], Mapping[str, object]] = {}  # noqa: E702
    codes: list[str] = []
    for raw in envelope_documents:
        envelope, parsed = _parse(raw, code="ENVELOPE_INVALID")
        codes += parsed
        if envelope is None or not isinstance(raw, bytes): continue  # noqa: E701
        envelope_codes = _schema_codes(envelope, "authority-evidence-envelope-v1.schema.json")
        if envelope_codes: codes += envelope_codes; continue  # noqa: E701, E702
        try: identity_valid = raw == core.canonical_bytes(envelope) and envelope.get("contentHash") == core.content_hash(core.ContentKind.EVIDENCE_OBJECT, core.ENVELOPE_SCHEMA_VERSION, envelope)  # noqa: E701
        except core.AuthorityEvidenceTrustError: identity_valid = False  # noqa: E701
        if not identity_valid or (envelope.get("revision") == 1) != (envelope.get("predecessorContentHash") is None): codes.append("ENVELOPE_CONTENT_HASH_MISMATCH"); continue  # noqa: E701, E702
        identity = tuple(envelope.get(name) for name in ("repository", "programId", "generationId", "evidenceId", "revision"))
        prior = identities.setdefault(identity, raw)
        if prior != raw: codes.append("EVIDENCE_IDENTITY_CONFLICT")  # noqa: E701
        lineage.setdefault(identity, envelope)
    for identity, replay_document in lineage.items():
        revision = cast(int, identity[-1]); predecessor = lineage.get(identity[:-1] + (revision - 1,))  # noqa: E702
        if revision > 1 and (predecessor is None or replay_document.get("predecessorContentHash") != predecessor.get("contentHash")): codes.append("EVIDENCE_PREDECESSOR_MISMATCH")  # noqa: E701
        elif predecessor is not None and any(replay_document.get(name) != predecessor.get(name) for name in core.ENVELOPE_MEMBERS - {"contentHash", "predecessorContentHash", "revision", "signature"}): codes.append("EVIDENCE_BINDING_MISMATCH")  # noqa: E701
    codes = list(dict.fromkeys(codes))
    verdict = _verdict(codes)
    return _result(codes, valid=not codes, historical_verdict=verdict, current_verdict=verdict)
def _verdict(codes: list[str]) -> core.Verdict:
    if any("CONFLICT" in code or "FORK" in code or code in {"DUPLICATE_CONTENT_HASH", "DUPLICATE_KEY_ID", "DUPLICATE_PUBLIC_KEY"} for code in codes):
        return core.Verdict.CONFLICTING
    invalid = [code for code in codes if "UNAVAILABLE" not in code and code not in {"ROOT_PIN_DESCRIPTOR_REQUIRED", "ROOT_PIN_SET_HASH_REQUIRED", "ACCEPTANCE_HEAD_REQUIRED", "CURRENT_HEAD_REQUIRED"}]
    if invalid:
        return core.Verdict.INVALID
    return core.Verdict.UNAVAILABLE if codes else core.Verdict.VALID
def _phase_result(historical_codes: list[str], current_codes: list[str]) -> ClosedResult:
    historical_codes = sorted(set(historical_codes)); current_codes = sorted(set(current_codes)); historical = _verdict(historical_codes); current = _verdict(current_codes); trusted = historical is core.Verdict.VALID and current is core.Verdict.VALID  # noqa: E702
    return _result(list(dict.fromkeys(historical_codes + current_codes)), valid=trusted, trusted=trusted, historical_verdict=historical, current_verdict=current, historical_findings=historical_codes, current_findings=current_codes)
def _history_chain(documents: Mapping[str, Mapping[str, object]], head: core.HistoryHead) -> tuple[Mapping[str, object], ...]:
    chain: list[Mapping[str, object]] = []
    seen: set[str] = set()
    digest: object = head.key_record_content_hash
    while isinstance(digest, str) and digest not in seen and digest in documents:
        seen.add(digest)
        record = documents[digest]
        chain.append(record)
        digest = record.get("historyPredecessorContentHash")
    chain.reverse()
    return tuple(chain)
def _valid_head(value: object) -> bool:
    return isinstance(value, core.HistoryHead) and isinstance(value.producer_id, str) and bool(value.producer_id) and isinstance(value.history_sequence, int) and not isinstance(value.history_sequence, bool) and value.history_sequence > 0 and isinstance(value.root_content_hash, str) and core.LOWER_SHA256.fullmatch(value.root_content_hash) is not None and isinstance(value.key_record_content_hash, str) and core.LOWER_SHA256.fullmatch(value.key_record_content_hash) is not None


def resolve_complete_evidence(*, envelope_bytes: object, payload_bytes: object, root_documents: object, key_record_documents: object, acceptance_pin_descriptor: object, acceptance_expected_pin_hash: object, current_pin_descriptor: object, current_expected_pin_hash: object, acceptance_head: object, current_head: object, acceptance_time: object, current_time: object, taxonomy_matrix_bytes: object) -> ClosedResult:
    envelope, common = _parse(envelope_bytes, code="ENVELOPE_INVALID")
    if envelope is None:
        verdict = _verdict(common)
        return _result(common, historical_verdict=verdict, current_verdict=verdict)
    common += [item.code for item in core._validate_envelope(envelope)]
    envelope_schema_codes = _schema_codes(envelope, "authority-evidence-envelope-v1.schema.json"); common += envelope_schema_codes  # noqa: E702
    if (envelope.get("revision") == 1) != (envelope.get("predecessorContentHash") is None): common.append("ENVELOPE_PREDECESSOR_REVISION_MISMATCH")  # noqa: E701
    try:
        if envelope_bytes != core.canonical_bytes(envelope) or envelope.get("contentHash") != core.content_hash(
            core.ContentKind.EVIDENCE_OBJECT,
            core.ENVELOPE_SCHEMA_VERSION,
            envelope,
        ):
            common.append("ENVELOPE_CONTENT_HASH_MISMATCH")
    except core.AuthorityEvidenceTrustError:
        common.append("ENVELOPE_CONTENT_HASH_MISMATCH")
    if not isinstance(payload_bytes, bytes):
        common.append("PAYLOAD_UNAVAILABLE")
    else:
        if len(payload_bytes) > core.PAYLOAD_MAX_BYTES or envelope.get("payloadByteLength") != len(payload_bytes):
            common.append("PAYLOAD_LENGTH_MISMATCH")
    if envelope_schema_codes or "ENVELOPE_PREDECESSOR_REVISION_MISMATCH" in common or "PAYLOAD_LENGTH_MISMATCH" in common:
        verdict = _verdict(common)
        return _result(common, historical_verdict=verdict, current_verdict=verdict)
    scope_values = tuple(envelope.get(name) for name in (
        "repository", "programId", "generationId", "producerId"
    ))
    if any(not isinstance(item, str) for item in scope_values):
        common.append("ENVELOPE_SCOPE_INVALID")
        verdict = _verdict(common)
        return _result(common, historical_verdict=verdict, current_verdict=verdict)
    scope = cast(tuple[str, str, str, str], scope_values)
    if not isinstance(root_documents, dict) or not isinstance(key_record_documents, dict):
        common.append("TRUST_DOCUMENT_MAPPING_INVALID")
        verdict = _verdict(common)
        return _result(common, historical_verdict=verdict, current_verdict=verdict)
    if len(root_documents) > 64 or len(key_record_documents) > 64:
        common.append("HISTORY_RECORD_LIMIT"); verdict = _verdict(common)  # noqa: E702
        return _result(common, historical_verdict=verdict, current_verdict=verdict)
    root_hash = envelope.get("rootContentHash")
    root_raw = root_documents.get(root_hash) if isinstance(root_hash, str) else None
    acceptance_pin_codes = _pin_codes(acceptance_pin_descriptor, acceptance_expected_pin_hash, "ACCEPTANCE", scope); current_pin_codes = _pin_codes(current_pin_descriptor, current_expected_pin_hash, "CURRENT", scope)  # noqa: E702
    historical_codes = list(common) + acceptance_pin_codes; current_codes = list(common) + current_pin_codes  # noqa: E702
    if isinstance(acceptance_head, core.HistoryHead) and not _valid_head(acceptance_head): historical_codes.append("ACCEPTANCE_HEAD_INVALID")  # noqa: E701
    if isinstance(current_head, core.HistoryHead) and not _valid_head(current_head): current_codes.append("CURRENT_HEAD_INVALID")  # noqa: E701
    acceptance_pins = acceptance_pin_descriptor.get("rootContentHashes") if isinstance(acceptance_pin_descriptor, Mapping) else None
    current_pins = current_pin_descriptor.get("rootContentHashes") if isinstance(current_pin_descriptor, Mapping) else None
    if isinstance(acceptance_pins, list) and isinstance(current_pins, list) and all(isinstance(item, str) for item in acceptance_pins + current_pins) and not set(acceptance_pins).issubset(current_pins):
        current_codes.append("ROOT_PIN_ROLLBACK")
    if isinstance(acceptance_pins, list) and root_hash not in acceptance_pins: historical_codes.append("ROOT_PIN_REQUIRED")  # noqa: E701
    if isinstance(current_pins, list) and root_hash not in current_pins: current_codes.append("ROOT_PIN_REQUIRED")  # noqa: E701
    if isinstance(acceptance_pins, list) and isinstance(current_pins, list) and all(isinstance(item, str) for item in acceptance_pins + current_pins) and set(root_documents) - set(acceptance_pins + current_pins):
        historical_codes.append("ROOT_DOCUMENT_SET_MISMATCH"); current_codes.append("ROOT_DOCUMENT_SET_MISMATCH")  # noqa: E702
    for phase, descriptor, expected_hash, when, target, pin_codes in (
        ("ACCEPTANCE", acceptance_pin_descriptor, acceptance_expected_pin_hash, acceptance_time, historical_codes, acceptance_pin_codes),
        ("CURRENT", current_pin_descriptor, current_expected_pin_hash, current_time, current_codes, current_pin_codes),
    ):
        pins = descriptor.get("rootContentHashes") if isinstance(descriptor, Mapping) else None
        if isinstance(pins, list) and not pin_codes:
            for pinned_hash in pins:
                raw = root_documents.get(pinned_hash) if isinstance(pinned_hash, str) else None
                if raw is None:
                    target.append("ROOT_DOCUMENT_UNAVAILABLE")
                    continue
                pinned_root, _ = _parse(raw, code="ROOT_DOCUMENT_INVALID"); compromise = pinned_root.get("priorRootCompromise") if pinned_root is not None else None; temporal = pinned_hash == root_hash or (pinned_root is not None and pinned_root.get("predecessorRootContentHash") == root_hash and isinstance(compromise, Mapping) and compromise.get("priorRootContentHash") == root_hash); root_result = _validate_closed_root(root_bytes=raw, expected_root_hash=pinned_hash, pin_descriptor=descriptor, expected_pin_set_hash=expected_hash, expected_phase=phase, expected_scope=scope, evaluation_time=when, temporal=temporal)  # noqa: E702
                target += [item.code for item in root_result.findings]
            if all(isinstance(item, str) for item in pins): target += _root_history_codes({cast(str, item): root_documents.get(item) for item in pins})  # noqa: E701
            if all(isinstance(item, str) and item in root_documents for item in pins):
                invalidation = resolve_root_invalidation(root_documents={cast(str, item): root_documents[item] for item in pins}, pin_descriptor=descriptor, expected_pin_set_hash=expected_hash, expected_scope=scope, prior_root_content_hash=root_hash, evaluation_time=when, expected_phase=phase, authorization_time=envelope.get("capturedAt"))
                target += [item.code for item in invalidation.findings]
                if invalidation.structural_invalidation_applies: target.append("ROOT_COMPROMISE_INVALIDATION")  # noqa: E701
    root, _ = _parse(root_raw, code="ROOT_DOCUMENT_INVALID")
    if root is not None and root.get("rootId") != envelope.get("rootId"):
        historical_codes.append("ROOT_ID_MISMATCH"); current_codes.append("ROOT_ID_MISMATCH")  # noqa: E702
    if isinstance(payload_bytes, bytes) and len(payload_bytes) <= core.PAYLOAD_MAX_BYTES and envelope.get("payloadSha256") != hashlib.sha256(payload_bytes).hexdigest(): historical_codes.append("PAYLOAD_HASH_MISMATCH"); current_codes.append("PAYLOAD_HASH_MISMATCH")  # noqa: E701, E702
    if root is not None and isinstance(payload_bytes, bytes) and isinstance(root.get("maxPayloadBytes"), int) and not isinstance(root.get("maxPayloadBytes"), bool) and len(payload_bytes) > cast(int, root["maxPayloadBytes"]):
        historical_codes.append("ROOT_PAYLOAD_LIMIT"); current_codes.append("ROOT_PAYLOAD_LIMIT")  # noqa: E702
    if root_raw is None and "ROOT_DOCUMENT_UNAVAILABLE" not in historical_codes + current_codes: historical_codes += ["ROOT_AUTHORIZATION_INVALID", "EVIDENCE_SIGNATURE_INVALID"]; current_codes += ["ROOT_AUTHORIZATION_INVALID", "EVIDENCE_SIGNATURE_INVALID"]  # noqa: E701, E702
    if _verdict(historical_codes) is not core.Verdict.VALID and _verdict(current_codes) is not core.Verdict.VALID: return _phase_result(historical_codes, current_codes)  # noqa: E701
    parsed_keys: dict[str, Mapping[str, object]] = {}; key_candidates: dict[str, Mapping[str, object]] = {}; key_errors: dict[str, list[str]] = {}  # noqa: E702
    for digest, raw in key_record_documents.items():
        record, parse_codes = _parse(raw, code="KEY_RECORD_INVALID")
        if not isinstance(digest, str): current_codes += parse_codes or ["KEY_DOCUMENT_IDENTITY_MISMATCH"]; continue  # noqa: E701, E702
        key_errors[digest] = list(parse_codes)
        if record is not None:
            key_candidates[digest] = record
            record_codes = _schema_codes(record, "authority-producer-key-v1.schema.json")
            if isinstance(record.get("publicKeyHex"), str) and record.get("keyId") != core._public_key_id(cast(str, record["publicKeyHex"])): record_codes.append("KEY_ID_MISMATCH")  # noqa: E701
            if record.get("contentHash") != digest or raw != core.canonical_bytes(record): record_codes.append("KEY_DOCUMENT_IDENTITY_MISMATCH")  # noqa: E701
            key_errors[digest] += record_codes
            if not key_errors[digest]: parsed_keys[digest] = record  # noqa: E701
    current_codes += sorted(code for errors in key_errors.values() for code in errors)
    if _valid_head(acceptance_head):
        cursor: object = cast(core.HistoryHead, acceptance_head).key_record_content_hash; seen: set[str] = set()  # noqa: E702
        while isinstance(cursor, str) and cursor not in seen:
            seen.add(cursor); historical_codes += key_errors.get(cursor, []); candidate = key_candidates.get(cursor)  # noqa: E702
            if candidate is None: break  # noqa: E701
            cursor = candidate.get("historyPredecessorContentHash")
    if not isinstance(acceptance_head, core.HistoryHead): historical_codes.append("ACCEPTANCE_HEAD_REQUIRED")  # noqa: E701
    if not isinstance(current_head, core.HistoryHead): current_codes.append("CURRENT_HEAD_REQUIRED")  # noqa: E701
    for head, when, target, descriptor, expected_hash, pins, phase in (
        (acceptance_head, acceptance_time, historical_codes, acceptance_pin_descriptor, acceptance_expected_pin_hash, acceptance_pins, "ACCEPTANCE"),
        (current_head, current_time, current_codes, current_pin_descriptor, current_expected_pin_hash, current_pins, "CURRENT"),
    ):
        if _valid_head(head):
            valid_head = cast(core.HistoryHead, head)
            if valid_head.key_record_content_hash not in key_record_documents: target.append("KEY_RECORD_UNAVAILABLE"); continue  # noqa: E701, E702
            chain = _history_chain(parsed_keys, valid_head)
            history = inspect_key_history(
                records=chain,
                expected_head=head,
                repository=scope[0],
                program_id=scope[1],
                generation_id=scope[2],
                producer_id=scope[3],
                root_content_hash=cast(str, root_hash),
                capture_time=envelope.get("capturedAt"),
                evaluation_time=when,
                independently_pinned_roots=(root_hash,),
                root_invalidations=(),
            )
            target += [item.code for item in history.findings if item.code not in {"KEY_NOT_YET_ACTIVE", "KEY_RETIRED", "KEY_REVOKED"}]
            if isinstance(descriptor, Mapping) and isinstance(pins, list) and all(isinstance(item, str) and item in root_documents for item in pins):
                for item in chain:
                    field = {"ISSUE_GENESIS": "activationTime", "ROTATE": "activationTime", "RETIRE": "retiredAt", "REVOKE": "revokedAt"}.get(cast(str, item.get("operation"))); invalidation = resolve_root_invalidation(root_documents={cast(str, digest): root_documents[digest] for digest in pins}, pin_descriptor=descriptor, expected_pin_set_hash=expected_hash, expected_scope=scope, prior_root_content_hash=root_hash, evaluation_time=when, expected_phase=phase, authorization_time=item.get(field) if field is not None else None); target += [finding.code for finding in invalidation.findings]; target += ["ROOT_COMPROMISE_INVALIDATION"] if invalidation.structural_invalidation_applies else []  # noqa: E702
    if _verdict(historical_codes) is not core.Verdict.VALID and _verdict(current_codes) is not core.Verdict.VALID: return _phase_result(historical_codes, current_codes)  # noqa: E701
    if _valid_head(current_head) and "KEY_RECORD_UNAVAILABLE" not in current_codes:
        full_history = inspect_key_history(
            records=tuple(parsed_keys.values()),
            expected_head=current_head,
            repository=scope[0],
            program_id=scope[1],
            generation_id=scope[2],
            producer_id=scope[3],
            root_content_hash=cast(str, root_hash),
            capture_time=envelope.get("capturedAt"),
            evaluation_time=current_time,
            independently_pinned_roots=(root_hash,),
            root_invalidations=(),
        )
        current_codes += [item.code for item in full_history.findings if item.code not in {"KEY_NOT_YET_ACTIVE", "KEY_RETIRED", "KEY_REVOKED"}]
    issuing_tuple = (
        envelope.get("issuingKeyObjectId"),
        envelope.get("signingKeyId"),
        envelope.get("issuingKeyRevision"),
        envelope.get("issuingKeyRecordContentHash"),
    )
    if _valid_head(acceptance_head) and "KEY_RECORD_UNAVAILABLE" not in historical_codes:
        issuing_a = resolve_issuing_key(
            records=_history_chain(parsed_keys, cast(core.HistoryHead, acceptance_head)),
            expected_head=acceptance_head,
            issuing_key=issuing_tuple,
            capture_time=envelope.get("capturedAt"),
            evaluation_time=acceptance_time,
        )
        historical_codes += [item.code for item in issuing_a.findings]
        if not issuing_a.issuing_key_eligible:
            historical_codes.append("ISSUING_KEY_INELIGIBLE")
    if _valid_head(current_head) and "KEY_RECORD_UNAVAILABLE" not in current_codes:
        issuing_c = resolve_issuing_key(
            records=_history_chain(parsed_keys, cast(core.HistoryHead, current_head)),
            expected_head=current_head,
            issuing_key=issuing_tuple,
            capture_time=envelope.get("capturedAt"),
            evaluation_time=current_time,
        )
        current_codes += [item.code for item in issuing_c.findings]
        if not issuing_c.issuing_key_eligible:
            current_codes.append("ISSUING_KEY_INELIGIBLE")
    issuing = parsed_keys.get(cast(str, envelope.get("issuingKeyRecordContentHash")))
    if root is not None and issuing is not None:
        genesis = root.get("genesisCaptureKey")
        root_key = root.get("rootAuthorizationKey")
        root_public = root_key.get("publicKeyHex") if isinstance(root_key, Mapping) else None
        for head, target in ((acceptance_head, historical_codes), (current_head, current_codes)):
            if "KEY_RECORD_UNAVAILABLE" in target: continue  # noqa: E701
            chain = _history_chain(parsed_keys, cast(core.HistoryHead, head)) if _valid_head(head) else (); genesis_record = next((row for row in chain if row.get("operation") == "ISSUE_GENESIS"), None)  # noqa: E702
            if _valid_head(head) and (not isinstance(genesis, Mapping) or genesis_record is None or any(genesis.get(name) != genesis_record.get(name) for name in ("keyObjectId", "keyId", "publicKeyHex", "revision", "activationTime"))): target.append("GENESIS_KEY_BINDING_MISMATCH")  # noqa: E701
            for item in chain:
                rotation = item.get("rotationPredecessor"); predecessor = parsed_keys.get(cast(str, rotation.get("contentHash"))) if isinstance(rotation, Mapping) and isinstance(rotation.get("contentHash"), str) else None  # noqa: E702
                signatures = core.verify_key_record_authorization_signatures(record=item, root_public_key_hex=cast(str, root_public), predecessor_public_key_hex=(cast(str, predecessor.get("publicKeyHex")) if predecessor is not None else None))
                if not signatures.valid: target.append("ROOT_AUTHORIZATION_INVALID")  # noqa: E701
        signature = core.verify_ed25519_signature(
            public_key_hex=cast(str, issuing.get("publicKeyHex")),
            signature_hex=cast(str, envelope.get("signature")),
            message=core.evidence_signature_input(envelope),
        )
        if not signature.valid:
            historical_codes.append("EVIDENCE_SIGNATURE_INVALID")
            current_codes.append("EVIDENCE_SIGNATURE_INVALID")
        for when, target in ((acceptance_time, historical_codes), (current_time, current_codes)):
            subject = validate_subject_phase(
                envelope=envelope,
                root=root,
                taxonomy_matrix_bytes=taxonomy_matrix_bytes,
                evaluation_time=when,
            )
            target += [item.code for item in subject.findings]
    elif root_raw is not None or "ROOT_DOCUMENT_UNAVAILABLE" not in historical_codes + current_codes:
        historical_codes += ["ROOT_AUTHORIZATION_INVALID", "EVIDENCE_SIGNATURE_INVALID"]; current_codes += ["ROOT_AUTHORIZATION_INVALID", "EVIDENCE_SIGNATURE_INVALID"]  # noqa: E702
    return _phase_result(historical_codes, current_codes)
