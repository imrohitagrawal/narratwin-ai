"""Continuation RED for complete Issue #434 trust and reconstruction."""

from __future__ import annotations

import hashlib, importlib, json  # noqa: E401
from collections.abc import Callable, Mapping
from typing import Any, cast

import pytest

from scripts.quality import issue434_authority_evidence_trust as trust
from tests.unit import test_issue434_authority_evidence_trust as prior_tests


def future(name: str, **kwargs: object) -> object:
    """Keep RED importable while returning the repository's typed sentinel."""

    try:
        module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction")
    except ModuleNotFoundError:
        return trust.NotImplementedResult()
    function = cast(Callable[..., object] | None, getattr(module, name, None))
    return function(**kwargs) if callable(function) else trust.NotImplementedResult()


def codes(result: object) -> set[str]:
    return {item.code for item in cast(Any, result).findings}


def assert_boundary(result: object) -> None:
    assert not isinstance(result, trust.NotImplementedResult), result
    assert cast(Any, result).authority_effect == "NO_AUTHORITY_EFFECT"
    assert cast(Any, result).activation == "NONE"


REPOSITORY = "example.invalid/narratwin-authority-evidence-fixtures"
PROGRAM = "program:fixture-only"
GENERATION = "generation:fixture-only"
PRODUCER = "producer:fixture-only"
T00 = "2026-08-17T00:00:00Z"
T10 = "2026-08-17T00:10:00Z"
T20 = "2026-08-17T00:20:00Z"


def pin_descriptor(root_hash: str, phase: str) -> dict[str, object]:
    return {
        "schemaVersion": "AuthorityRootPinSetV1",
        "repository": REPOSITORY,
        "programId": PROGRAM,
        "generationId": GENERATION,
        "producerId": PRODUCER,
        "evaluationPhase": phase,
        "rootContentHashes": [root_hash],
    }


def pin_hash(descriptor: Mapping[str, object]) -> str:
    return hashlib.sha256(
        b"NARRATWIN-AUTHORITY-ROOT-PIN-SET-V1\0AuthorityRootPinSetV1\0"
        + trust.canonical_bytes(descriptor)
    ).hexdigest()


def root_document(**changes: object) -> dict[str, object]:
    public_key = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    key_id = hashlib.sha256(
        b"NARRATWIN-AUTHORITY-ED25519-PUBLIC-KEY-V1\0" + bytes.fromhex(public_key)
    ).hexdigest()
    value: dict[str, object] = {
        "schemaVersion": "AuthorityProducerTrustRootV1", "repository": REPOSITORY,
        "programId": PROGRAM, "generationId": GENERATION, "rootId": "root:fixture-only",
        "rootVersion": 1, "contentHash": "0" * 64, "producerId": PRODUCER,
        "validFrom": T00, "expiresAt": "2026-08-18T00:00:00Z",
        "signatureAlgorithm": "Ed25519", "publicKeyEncoding": "RAW_32_BYTE_LOWER_HEX",
        "rootAuthorizationKey": {"keyId": key_id, "publicKeyHex": public_key},
        "genesisCaptureKey": {
            "activationTime": T00,
            "keyId": key_id,
            "keyObjectId": "key:a:fixture-only",
            "publicKeyHex": public_key,
            "revision": 1,
        },
        "predecessorRootContentHash": None, "priorRootCompromise": None,
        "allowedSubjectSchemaVersions": ["ActiveProgramRouteV1"], "allowedTransitionRows": ["R01"],
        "allowedEvidenceRoles": ["INDEPENDENT_REVIEW"],
        "allowedPayloadMediaTypes": ["application/vnd.narratwin.authority.content-reference-v1+json"],
        "freshnessPolicies": [
            {
                "transitionRowId": "R01",
                "evidenceRole": "INDEPENDENT_REVIEW",
                "freshnessClass": "TRANSITION_WINDOW",
                "maxCaptureDelaySeconds": 60,
                "maxObservationAgeSeconds": 300,
                "maxEnvelopeLifetimeSeconds": 600,
            }
        ],
        "maxPayloadBytes": 131072, "recoverySemantics": "INDEPENDENT_SUCCESSOR_PIN_ONLY",
        "revocationSemantics": "INDEPENDENT_SUCCESSOR_PIN_WITH_EXACT_PRIOR_ROOT_BOUNDARY_ONLY",
        "prohibitedCapabilities": ["ACTIVATE_AUTHORITY", "DERIVE_ROOT_PIN", "GENERATE_KEY", "NETWORK_LOOKUP", "PERSIST_EVIDENCE", "SIGN"],
        "fixtureOnly": True,
    }
    value.update(changes)
    value["contentHash"] = trust.content_hash(
        trust.ContentKind.TRUST_ROOT,
        "AuthorityProducerTrustRootV1",
        value,
    )
    return value


@pytest.mark.parametrize("mutation", ["missing", "unknown"])
def test_closed_root_contract_executes_before_trust(mutation: str) -> None:
    root = root_document()
    if mutation == "missing":
        root.pop("rootId")
    else:
        root["surprise"] = "candidate-controlled"
    root["contentHash"] = trust.content_hash(
        trust.ContentKind.TRUST_ROOT,
        "AuthorityProducerTrustRootV1",
        root,
    )
    descriptor = pin_descriptor(cast(str, root["contentHash"]), "ACCEPTANCE")
    result = future(
        "validate_closed_root",
        root_bytes=trust.canonical_bytes(root),
        expected_root_hash=root["contentHash"],
        pin_descriptor=descriptor,
        expected_pin_set_hash=pin_hash(descriptor),
        expected_phase="ACCEPTANCE",
        expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER),
        evaluation_time=T10,
    )
    assert_boundary(result)
    assert "ROOT_CLOSED_SHAPE" in codes(result)
    assert cast(Any, result).valid is False


@pytest.mark.parametrize(
    ("name", "kwargs", "expected"),
    [
        (
            "validate_pin_transition",
            {
                "acceptance_descriptor": {"rootContentHashes": [{}]},
                "acceptance_expected_hash": "0" * 64,
                "current_descriptor": {"rootContentHashes": set()},
                "current_expected_hash": "0" * 64,
                "expected_scope": (REPOSITORY, PROGRAM, GENERATION, PRODUCER),
            },
            "ROOT_PIN_DESCRIPTOR_INVALID",
        ),
        (
            "resolve_issuing_key",
            {
                "records": (1,),
                "expected_head": trust.HistoryHead("0" * 64, PRODUCER, 1, "1" * 64),
                "issuing_key": ("key:a", "2" * 64, 1, "3" * 64),
                "capture_time": T10,
                "evaluation_time": T20,
            },
            "KEY_RECORD_INVALID",
        ),
        (
            "validate_artifact_set",
            {
                "artifacts": {"authority-evidence-envelope-v1.schema.json": {}},
                "child_a_matrix_bytes": b"{}",
                "expected_artifact_hashes": {},
            },
            "CONTRACT_ARTIFACT_INVALID",
        ),
    ],
)
def test_all_public_boundaries_contain_malformed_values(
    name: str, kwargs: dict[str, object], expected: str
) -> None:
    try:
        first = future(name, **kwargs)
        second = future(name, **kwargs)
    except Exception as exc:  # noqa: BLE001 - RED proves no raw exception escapes.
        pytest.fail(f"RAW_EXCEPTION:{type(exc).__name__}")
    assert_boundary(first)
    assert first == second
    assert expected in codes(first)


def taxonomy_matrix() -> bytes:
    row = {"typedReferenceType": "REVIEW_SUBJECT", "permittedRows": ["R01"], "evidenceRole": "INDEPENDENT_REVIEW", "producerTrustClass": "INDEPENDENT_REVIEWER", "freshnessClass": "TRANSITION_WINDOW", "payloadClass": "CONTENT_REFERENCE"}
    return json.dumps({"typedReferenceTaxonomy": [row], "payloadMediaTypeByClass": {"CONTENT_REFERENCE": "application/vnd.narratwin.authority.content-reference-v1+json"}}, sort_keys=True, separators=(",", ":")).encode()


def subject_envelope(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "typedReferenceType": "REVIEW_SUBJECT",
        "evidenceRole": "INDEPENDENT_REVIEW",
        "producerTrustClass": "INDEPENDENT_REVIEWER",
        "freshnessClass": "TRANSITION_WINDOW",
        "payloadClass": "CONTENT_REFERENCE",
        "payloadMediaType": "application/vnd.narratwin.authority.content-reference-v1+json",
        "subject": {
            "schemaVersion": "ActiveProgramRouteV1",
            "transitionRowId": "R01",
        },
        "observedAt": T10,
        "capturedAt": T10,
        "notBefore": T10,
        "expiresAt": T20,
    }
    value.update(changes)
    return value


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"typedReferenceType": "ROUTE_HASH"}, "TAXONOMY_BINDING_MISMATCH"),
        ({"evidenceRole": "HUMAN_AUTHORITY"}, "TAXONOMY_BINDING_MISMATCH"),
        ({"payloadClass": "CHECK_SET"}, "PAYLOAD_MEDIA_TYPE_MISMATCH"),
        ({"capturedAt": T00}, "CAPTURE_PRECEDES_OBSERVATION"),
        ({"expiresAt": T10}, "ENVELOPE_EXPIRED"),
    ],
)
def test_subject_taxonomy_phase_and_freshness_are_one_binding(changes: dict[str, object], expected: str) -> None:
    result = future(
        "validate_subject_phase",
        envelope=subject_envelope(**changes),
        root=root_document(),
        taxonomy_matrix_bytes=taxonomy_matrix(),
        evaluation_time=T10,
    )
    assert_boundary(result)
    assert expected in codes(result)
    assert cast(Any, result).valid is False


def reconstruction_bundle(payload: bytes) -> tuple[bytes, dict[str, bytes]]:
    root = root_document()
    root_hash = cast(str, root["contentHash"])
    key = key_record(root_hash, root)
    envelope = complete_envelope(root_hash, key, payload)
    pin_a, pin_c = pin_descriptor(root_hash, "ACCEPTANCE"), pin_descriptor(root_hash, "CURRENT")
    objects = [pin_a, pin_c, root, key, envelope]
    blobs = {pin_hash(pin_a): trust.canonical_bytes(pin_a), pin_hash(pin_c): trust.canonical_bytes(pin_c)}
    for item in objects[2:]:
        blobs[cast(str, item["contentHash"])] = trust.canonical_bytes(item)
    blobs[hashlib.sha256(payload).hexdigest()] = payload
    digests = list(blobs)
    roles = ["PAYLOAD", "PAYLOAD", "TRUST_ROOT", "PRODUCER_KEY", "EVIDENCE_ENVELOPE", "PAYLOAD"]
    media = ["application/vnd.narratwin.authority.content-reference-v1+json"] * 2 + [
        "application/vnd.narratwin.authority.producer-trust-root-v1+json",
        "application/vnd.narratwin.authority.producer-key-v1+json",
        "application/vnd.narratwin.authority.evidence-envelope-v1+json",
        "application/vnd.narratwin.authority.content-reference-v1+json",
    ]
    refs = [{"contentHash": digest, "byteLength": len(blobs[digest]), "mediaType": media[n], "ordinal": n, "role": roles[n]} for n, digest in enumerate(digests)]
    head = {"rootContentHash": root_hash, "producerId": PRODUCER, "historySequence": 1, "keyRecordContentHash": key["contentHash"]}
    subject = dict(cast(Mapping[str, object], envelope["subject"]), generationId=GENERATION)
    value: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceReconstructionV1", "repository": REPOSITORY,
        "programId": PROGRAM, "generationId": GENERATION, "reconstructionId": "reconstruction:fixture-only",
        "revision": 1, "predecessorContentHash": None, "contentHash": "0" * 64, "subject": subject,
        "typedReferenceType": "REVIEW_SUBJECT", "evidenceRole": "INDEPENDENT_REVIEW",
        "producerTrustClass": "INDEPENDENT_REVIEWER", "freshnessClass": "TRANSITION_WINDOW",
        "payloadClass": "CONTENT_REFERENCE", "acceptanceRootPinSetHash": digests[0],
        "acceptanceRootPinReferences": [refs[0]], "currentRootPinSetHash": digests[1],
        "currentRootPinReferences": [refs[1]], "acceptanceHead": head, "currentHead": head,
        "rootReferences": [refs[2]], "keyReferences": [refs[3]], "envelopeReference": refs[4],
        "payloadReference": refs[5], "retainedBlobCount": len(refs),
        "aggregateRetainedByteLength": sum(len(blob) for blob in blobs.values()),
        "historicalEvaluationTime": T10, "currentEvaluationTime": T10,
        "historicalVerdict": "VALID", "currentVerdict": "VALID", "historicalFindings": [],
        "currentFindings": [], "retentionUntil": "2026-08-18T00:00:00Z",
        "reconstructionStatus": "COMPLETE", "limitations": ["FIXTURE_ONLY"], "fixtureOnly": True,
    }
    value["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", value)
    return trust.canonical_bytes(value), blobs


@pytest.mark.parametrize(
    ("mutation", "expected", "status"),
    [
        ("delete", "RETAINED_BLOB_UNAVAILABLE", "UNAVAILABLE"),
        ("extra", "RETAINED_BLOB_SET_MISMATCH", "INVALID"),
        ("corrupt", "RETAINED_BLOB_HASH_MISMATCH", "INVALID"),
        ("expired", "RETENTION_EXPIRED", "UNAVAILABLE"),
    ],
)
def test_reconstruction_exact_set_deletion_corruption_and_retention(
    mutation: str, expected: str, status: str
) -> None:
    payload = b"fixture-only payload"
    manifest, original = reconstruction_bundle(payload)
    digest = hashlib.sha256(payload).hexdigest()
    blobs = dict(original)
    evaluation_time = T10
    if mutation == "delete":
        blobs.clear()
    elif mutation == "extra":
        blobs[hashlib.sha256(b"extra").hexdigest()] = b"extra"
    elif mutation == "corrupt":
        blobs[digest] = b"corrupt"
    else:
        evaluation_time = "2026-08-19T00:00:00Z"
    result = future(
        "reconstruct_retained_evidence",
        manifest_bytes=manifest,
        retained_blobs=blobs,
        evaluation_time=evaluation_time,
    )
    assert_boundary(result)
    assert expected in codes(result)
    assert cast(Any, result).reconstruction_status == status


def test_partial_signature_success_can_never_become_trusted() -> None:
    result = future(
        "resolve_complete_evidence",
        envelope_bytes=b"{}",
        payload_bytes=b"fixture-only",
        root_documents={},
        key_record_documents={},
        acceptance_pin_descriptor={},
        acceptance_expected_pin_hash="0" * 64,
        current_pin_descriptor={},
        current_expected_pin_hash="0" * 64,
        acceptance_head=trust.HistoryHead("0" * 64, PRODUCER, 1, "1" * 64),
        current_head=trust.HistoryHead("0" * 64, PRODUCER, 1, "1" * 64),
        acceptance_time=T10,
        current_time=T20,
        taxonomy_matrix_bytes=taxonomy_matrix(),
    )
    assert_boundary(result)
    assert cast(Any, result).trusted is False
    assert cast(Any, result).historical_verdict is not trust.Verdict.VALID
    assert cast(Any, result).current_verdict is not trust.Verdict.VALID


def key_record(root_hash: str, root: Mapping[str, object]) -> dict[str, object]:
    genesis = cast(Mapping[str, object], root["genesisCaptureKey"])
    value: dict[str, object] = {
        "schemaVersion": "AuthorityProducerKeyV1",
        "repository": REPOSITORY,
        "programId": PROGRAM,
        "generationId": GENERATION,
        "rootContentHash": root_hash,
        "producerId": PRODUCER,
        "keyObjectId": genesis["keyObjectId"],
        "keyId": genesis["keyId"],
        "publicKeyHex": genesis["publicKeyHex"],
        "revision": 1,
        "predecessorContentHash": None,
        "historySequence": 1,
        "historyPredecessorContentHash": None,
        "rotationPredecessor": None,
        "operation": "ISSUE_GENESIS",
        "activationTime": T00,
        "retiredAt": None,
        "revokedAt": None,
        "invalidatesFrom": None,
        "signatureAlgorithm": "Ed25519",
        "rootAuthorizationSignature": "0" * 128,
        "predecessorAuthorizationSignature": None,
        "fixtureOnly": True,
        "contentHash": "0" * 64,
    }
    value["contentHash"] = trust.content_hash(
        trust.ContentKind.PRODUCER_KEY,
        "AuthorityProducerKeyV1",
        value,
    )
    return value


def complete_envelope(
    root_hash: str,
    key: Mapping[str, object],
    payload: bytes,
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceEnvelopeV1", "repository": REPOSITORY,
        "programId": PROGRAM, "generationId": GENERATION, "evidenceId": "evidence:fixture-only",
        "revision": 1, "predecessorContentHash": None, "contentHash": "0" * 64,
        "subject": {
            "schemaVersion": "ActiveProgramRouteV1",
            "objectId": "route:fixture-only",
            "revision": 1,
            "contentHash": "1" * 64,
            "sourceState": "DRAFT",
            "operation": "REVIEW",
            "targetState": "REVIEWED",
            "transitionRowId": "R01",
        },
        "typedReferenceType": "REVIEW_SUBJECT", "evidenceRole": "INDEPENDENT_REVIEW",
        "producerTrustClass": "INDEPENDENT_REVIEWER", "freshnessClass": "TRANSITION_WINDOW",
        "payloadClass": "CONTENT_REFERENCE", "producerId": PRODUCER, "rootId": "root:fixture-only",
        "rootContentHash": root_hash, "signingKeyId": key["keyId"], "issuingKeyObjectId": key["keyObjectId"],
        "issuingKeyRevision": 1, "issuingKeyRecordContentHash": key["contentHash"],
        "signatureAlgorithm": "Ed25519", "canonicalSignatureProfile": "NarraTwinAuthorityEvidenceSignatureV1",
        "payloadMediaType": "application/vnd.narratwin.authority.content-reference-v1+json",
        "payloadSha256": hashlib.sha256(payload).hexdigest(), "payloadByteLength": len(payload),
        "observedAt": T10, "capturedAt": T10, "notBefore": T10, "expiresAt": T20,
        "sourceClass": "FIXTURE", "collectionMethod": "SYNTHETIC_PUBLIC_VECTOR",
        "limitations": ["FIXTURE_ONLY"], "fixtureOnly": True, "signature": "0" * 128,
    }
    value.update(changes)
    value["contentHash"] = trust.content_hash(
        trust.ContentKind.EVIDENCE_OBJECT,
        "AuthorityEvidenceEnvelopeV1",
        value,
    )
    return value


@pytest.mark.parametrize(
    "mutation",
    ["none", "missing-genesis", "wrong-head", "issuing-object", "signing-key"],
)
def test_only_complete_chain_can_promote_public_signature_success(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    try:
        module = importlib.import_module(
            "scripts.quality.issue434_authority_evidence_reconstruction"
        )
    except ModuleNotFoundError:
        result: object = trust.NotImplementedResult()
    else:
        # Orchestration-only control: RFC8032 tests prove real crypto separately.
        monkeypatch.setattr(
            trust,
            "verify_ed25519_signature",
            lambda **_: trust.SignatureResult(True, ()),
        )
        root = root_document()
        root_hash = cast(str, root["contentHash"])
        key = key_record(root_hash, root)
        payload = b"fixture-only payload"
        changes: dict[str, object] = {}
        if mutation == "issuing-object":
            changes["issuingKeyObjectId"] = "key:other"
        elif mutation == "signing-key":
            changes["signingKeyId"] = "f" * 64
        envelope = complete_envelope(root_hash, key, payload, **changes)
        descriptor_a = pin_descriptor(root_hash, "ACCEPTANCE")
        descriptor_c = pin_descriptor(root_hash, "CURRENT")
        head = trust.HistoryHead(root_hash, PRODUCER, 1, cast(str, key["contentHash"]))
        result = cast(Callable[..., object], module.resolve_complete_evidence)(
            envelope_bytes=trust.canonical_bytes(envelope),
            payload_bytes=payload,
            root_documents={root_hash: trust.canonical_bytes(root)},
            key_record_documents=(
                {} if mutation == "missing-genesis" else {
                    key["contentHash"]: trust.canonical_bytes(key)
                }
            ),
            acceptance_pin_descriptor=descriptor_a,
            acceptance_expected_pin_hash=pin_hash(descriptor_a),
            current_pin_descriptor=descriptor_c,
            current_expected_pin_hash=pin_hash(descriptor_c),
            acceptance_head=head,
            current_head=(
                trust.HistoryHead(root_hash, PRODUCER, 2, head.key_record_content_hash)
                if mutation == "wrong-head"
                else head
            ),
            acceptance_time=T10,
            current_time=T10,
            taxonomy_matrix_bytes=taxonomy_matrix(),
        )
    assert_boundary(result)
    should_trust = mutation == "none"
    assert cast(Any, result).trusted is should_trust
    if mutation == "wrong-head":
        assert cast(Any, result).historical_verdict is trust.Verdict.VALID
        assert cast(Any, result).current_verdict is not trust.Verdict.VALID
    else:
        assert (cast(Any, result).historical_verdict is trust.Verdict.VALID) is should_trust
        assert (cast(Any, result).current_verdict is trust.Verdict.VALID) is should_trust


def complete_arguments(**envelope_changes: object) -> tuple[dict[str, object], dict[str, object]]:
    root_changes = cast(Mapping[str, object], envelope_changes.pop("_root_changes", {})); root = root_document(**dict(root_changes))  # noqa: E702
    root_hash = cast(str, root["contentHash"])
    key = key_record(root_hash, root)
    payload = b"fixture-only payload"
    envelope = complete_envelope(root_hash, key, payload, **envelope_changes)
    pin_a, pin_c = pin_descriptor(root_hash, "ACCEPTANCE"), pin_descriptor(root_hash, "CURRENT")
    head = trust.HistoryHead(root_hash, PRODUCER, 1, cast(str, key["contentHash"]))
    return {
        "envelope_bytes": trust.canonical_bytes(envelope), "payload_bytes": payload,
        "root_documents": {root_hash: trust.canonical_bytes(root)},
        "key_record_documents": {key["contentHash"]: trust.canonical_bytes(key)},
        "acceptance_pin_descriptor": pin_a, "acceptance_expected_pin_hash": pin_hash(pin_a),
        "current_pin_descriptor": pin_c, "current_expected_pin_hash": pin_hash(pin_c),
        "acceptance_head": head, "current_head": head, "acceptance_time": T10,
        "current_time": T10, "taxonomy_matrix_bytes": taxonomy_matrix(),
    }, {"root": root, "key": key, "envelope": envelope}


def trusted_result(monkeypatch: pytest.MonkeyPatch, arguments: Mapping[str, object]) -> Any:
    monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ()))
    return cast(Any, future("resolve_complete_evidence", **dict(arguments)))


def test_full_reconstruction_contract_is_required_and_malformed_values_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload")
    trust_inputs, _ = complete_arguments()
    monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ()))
    valid = future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=blobs, evaluation_time=T10, trust_inputs=trust_inputs)
    assert_boundary(valid)
    assert cast(Any, valid).valid is True
    unbound = future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=blobs, evaluation_time=T10)
    assert_boundary(unbound)
    assert cast(Any, unbound).valid is False
    assert cast(Any, unbound).reconstruction_status == "UNAVAILABLE"
    document = json.loads(manifest)
    document["payloadReference"]["contentHash"] = {}
    malformed = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(document), retained_blobs=blobs, evaluation_time=T10)
    assert_boundary(malformed)
    assert cast(Any, malformed).valid is False


@pytest.mark.parametrize("change", [{"maxPayloadBytes": False}, {"freshnessPolicies": [{}]}, {"rootId": {}}])
def test_closed_root_schema_rejects_invalid_scalars(change: dict[str, object]) -> None:
    root = root_document(**change)
    root["contentHash"] = trust.content_hash(trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", root)
    descriptor = pin_descriptor(cast(str, root["contentHash"]), "CURRENT")
    result = future("validate_closed_root", root_bytes=trust.canonical_bytes(root), expected_root_hash=root["contentHash"], pin_descriptor=descriptor, expected_pin_set_hash=pin_hash(descriptor), expected_phase="CURRENT", expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER), evaluation_time=T10)
    assert_boundary(result)
    assert cast(Any, result).valid is False


def test_freshness_policy_and_child_a_transition_are_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    for changes in ({"observedAt": T00}, {"operation": "REJECT"}):
        if "operation" in changes:
            _, state = complete_arguments()
            envelope = cast(Mapping[str, object], state["envelope"])
            subject = dict(cast(Mapping[str, object], envelope["subject"]), operation="REJECT")
            arguments, _ = complete_arguments(subject=subject)
        else:
            arguments, _ = complete_arguments(**changes)
        result = trusted_result(monkeypatch, arguments)
        assert result.trusted is False
        assert result.historical_verdict is not trust.Verdict.VALID


def test_current_pin_failure_does_not_contaminate_history(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments()
    arguments["current_expected_pin_hash"] = "f" * 64
    result = trusted_result(monkeypatch, arguments)
    assert result.historical_verdict is trust.Verdict.VALID
    assert result.current_verdict is not trust.Verdict.VALID


def test_current_successor_compromise_invalidates_only_current(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, state = complete_arguments()
    prior = cast(dict[str, object], state["root"])
    successor = root_document(rootId="root:successor", rootVersion=2, predecessorRootContentHash=prior["contentHash"], priorRootCompromise={"priorRootContentHash": prior["contentHash"], "invalidatesPriorRootFrom": T10})
    successor["contentHash"] = trust.content_hash(trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", successor)
    hashes = sorted([cast(str, prior["contentHash"]), cast(str, successor["contentHash"])])
    current = dict(cast(Mapping[str, object], arguments["current_pin_descriptor"]), rootContentHashes=hashes)
    arguments["current_pin_descriptor"] = current
    arguments["current_expected_pin_hash"] = pin_hash(current)
    cast(dict[str, bytes], arguments["root_documents"])[cast(str, successor["contentHash"])] = trust.canonical_bytes(successor)
    result = trusted_result(monkeypatch, arguments)
    assert result.historical_verdict is trust.Verdict.VALID
    assert result.current_verdict is not trust.Verdict.VALID


def test_replay_identity_is_idempotent_only_for_exact_bytes() -> None:
    arguments, state = complete_arguments()
    first = cast(bytes, arguments["envelope_bytes"])
    root = cast(Mapping[str, object], state["root"])
    changed = complete_envelope(cast(str, root["contentHash"]), cast(Mapping[str, object], state["key"]), cast(bytes, arguments["payload_bytes"]), collectionMethod="OTHER_FIXTURE")
    same = future("validate_evidence_replay_set", envelope_documents=(first, first))
    conflict = future("validate_evidence_replay_set", envelope_documents=(first, trust.canonical_bytes(changed)))
    assert_boundary(same)
    assert cast(Any, same).valid is True
    assert_boundary(conflict)
    assert cast(Any, conflict).valid is False
    assert cast(Any, conflict).historical_verdict is trust.Verdict.CONFLICTING


def test_invalid_findings_precede_unavailable_findings() -> None:
    arguments, _ = complete_arguments()
    arguments["envelope_bytes"], arguments["payload_bytes"] = b"{}", None
    result = future("resolve_complete_evidence", **arguments)
    assert_boundary(result)
    assert cast(Any, result).historical_verdict is trust.Verdict.INVALID
    assert cast(Any, result).current_verdict is trust.Verdict.INVALID


@pytest.mark.parametrize(("field", "bad"), [("issuingKeyRecordContentHash", {}), ("payloadClass", {}), ("schemaVersion", {})])
def test_malformed_envelope_values_are_typed(field: str, bad: object) -> None:
    arguments, state = complete_arguments()
    envelope = dict(cast(Mapping[str, object], state["envelope"])); envelope[field] = bad  # noqa: E702
    result = future("resolve_complete_evidence", **dict(arguments, envelope_bytes=trust.canonical_bytes(envelope)))
    assert_boundary(result)
    assert cast(Any, result).trusted is False


@pytest.mark.parametrize("phase", ["acceptance", "current"])
def test_signing_root_requires_each_exact_pin_set(monkeypatch: pytest.MonkeyPatch, phase: str) -> None:
    arguments, _ = complete_arguments(); other = root_document(rootId="root:other")  # noqa: E702
    other["contentHash"] = trust.content_hash(trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", other)
    descriptor = pin_descriptor(cast(str, other["contentHash"]), phase.upper()); arguments[f"{phase}_pin_descriptor"] = descriptor; arguments[f"{phase}_expected_pin_hash"] = pin_hash(descriptor)  # noqa: E702
    cast(dict[str, bytes], arguments["root_documents"])[cast(str, other["contentHash"])] = trust.canonical_bytes(other)
    assert trusted_result(monkeypatch, arguments).trusted is False


@pytest.mark.parametrize(("field", "value"), [("subject", {"objectId": "route:other"}), ("reconstructionStatus", "INVALID")])
def test_reconstruction_claims_bind_retained_envelope(monkeypatch: pytest.MonkeyPatch, field: str, value: object) -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload"); document = json.loads(manifest)  # noqa: E702
    document[field] = dict(document[field], **cast(dict[str, object], value)) if field == "subject" else value
    document["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", document)
    inputs, _ = complete_arguments(); monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ()))  # noqa: E702
    result = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(document), retained_blobs=blobs, evaluation_time=T10, trust_inputs=inputs)
    assert cast(Any, result).valid is False


def test_k02_does_not_retire_k01_before_explicit_boundary() -> None:
    rows = prior_tests.key_rows(); result = trust.resolve_issuing_key_structure(records=(rows["K01"], rows["K02"]), expected_head=prior_tests.head(rows["K02"]), issuing_key=(rows["K01"]["keyObjectId"], rows["K01"]["keyId"], 1, rows["K01"]["contentHash"]), capture_time=prior_tests.T09)  # noqa: E702
    assert result.issuing_key_eligible is True


def test_public_subject_boundary_contains_unhashable_payload_class() -> None:
    try: result = future("validate_subject_phase", envelope=subject_envelope(payloadClass={}), root=root_document(), taxonomy_matrix_bytes=taxonomy_matrix(), evaluation_time=T10)  # noqa: E701
    except Exception as exc: pytest.fail(f"RAW_EXCEPTION:{type(exc).__name__}")  # noqa: BLE001, E701
    assert cast(Any, result).valid is False


def test_replay_requires_exact_contiguous_predecessor() -> None:
    arguments, state = complete_arguments(); first = cast(bytes, arguments["envelope_bytes"]); second = dict(cast(Mapping[str, object], state["envelope"]), revision=2, predecessorContentHash="f" * 64)  # noqa: E702
    second["contentHash"] = trust.content_hash(trust.ContentKind.EVIDENCE_OBJECT, trust.ENVELOPE_SCHEMA_VERSION, second); raw = trust.canonical_bytes(second)  # noqa: E702
    results = [cast(Any, future("validate_evidence_replay_set", envelope_documents=documents)).valid for documents in ((raw,), (first, raw))]
    assert results == [False, False]


@pytest.mark.parametrize(("missing", "preserved", "absent"), [("acceptance_head", "current_verdict", "historical_verdict"), ("current_head", "historical_verdict", "current_verdict"), ("acceptance_pin_descriptor", "current_verdict", "historical_verdict")])
def test_missing_head_does_not_contaminate_other_phase(monkeypatch: pytest.MonkeyPatch, missing: str, preserved: str, absent: str) -> None:
    arguments, _ = complete_arguments(); arguments[missing] = None; result = trusted_result(monkeypatch, arguments)  # noqa: E702
    assert getattr(result, preserved) is trust.Verdict.VALID and getattr(result, absent) is trust.Verdict.UNAVAILABLE


def test_root_payload_limit_and_conflicting_successor_boundaries_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments(_root_changes={"maxPayloadBytes": 1}); payload_result = trusted_result(monkeypatch, arguments)  # noqa: E702
    arguments, state = complete_arguments(); prior = cast(dict[str, object], state["root"]); successors = [root_document(rootId=f"root:s{n}", rootVersion=2, predecessorRootContentHash=prior["contentHash"], priorRootCompromise={"priorRootContentHash": prior["contentHash"], "invalidatesPriorRootFrom": when}) for n, when in enumerate((T00, T20))]  # noqa: E702
    hashes = sorted([cast(str, prior["contentHash"]), *(cast(str, row["contentHash"]) for row in successors)]); descriptor = dict(cast(Mapping[str, object], arguments["current_pin_descriptor"]), rootContentHashes=hashes)  # noqa: E702
    arguments["current_pin_descriptor"] = descriptor; arguments["current_expected_pin_hash"] = pin_hash(descriptor); cast(dict[str, bytes], arguments["root_documents"]).update({cast(str, row["contentHash"]): trust.canonical_bytes(row) for row in successors})  # noqa: E702
    conflict_result = trusted_result(monkeypatch, arguments)
    assert payload_result.trusted is False and conflict_result.current_verdict is trust.Verdict.CONFLICTING


@pytest.mark.parametrize("source", ["K03", "K04"])
def test_terminal_key_states_cannot_repeat(source: str) -> None:
    rows = prior_tests.key_rows(); prior = rows[source]; operation = cast(str, prior["operation"]); illegal = prior_tests.key_record(4, operation=operation, previous=prior, key_object_id=cast(str, prior["keyObjectId"]), public_key_hex=cast(str, prior["publicKeyHex"]), revision=3, activationTime=prior_tests.T10)  # noqa: E702
    assert prior_tests.finding_codes(prior_tests.inspect_structure((rows["K01"], rows["K02"], prior, illegal), expected_head=prior_tests.head(illegal)))


def test_k04_observation_time_and_predecessor_overlap_are_high_level(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = prior_tests.key_rows(); result = future("resolve_issuing_key", records=(rows["K01"], rows["K02"], rows["K04"]), expected_head=prior_tests.head(rows["K04"]), issuing_key=(rows["K02"]["keyObjectId"], rows["K02"]["keyId"], 1, rows["K02"]["contentHash"]), capture_time=prior_tests.T15, evaluation_time=prior_tests.T29)  # noqa: E702
    assert cast(Any, result).issuing_key_eligible is True


def _rotated_arguments() -> dict[str, object]:
    policy = [{"transitionRowId": "R01", "evidenceRole": "INDEPENDENT_REVIEW", "freshnessClass": "TRANSITION_WINDOW", "maxCaptureDelaySeconds": 60, "maxObservationAgeSeconds": 1200, "maxEnvelopeLifetimeSeconds": 1200}]
    arguments, state = complete_arguments(_root_changes={"freshnessPolicies": policy}, expiresAt=prior_tests.T30); prior = cast(Mapping[str, object], state["key"]); public = "2" * 64  # noqa: E702
    rotated = dict(prior, keyObjectId="key:b:fixture-only", keyId=prior_tests.public_key_id(public), publicKeyHex=public, predecessorContentHash=None, historySequence=2, historyPredecessorContentHash=prior["contentHash"], rotationPredecessor={"keyObjectId": prior["keyObjectId"], "revision": 1, "contentHash": prior["contentHash"]}, operation="ROTATE", activationTime=T20, predecessorAuthorizationSignature="0" * 128); rotated["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, rotated)  # noqa: E702
    cast(dict[str, bytes], arguments["key_record_documents"])[cast(str, rotated["contentHash"])] = trust.canonical_bytes(rotated); arguments["current_head"] = trust.HistoryHead(cast(str, prior["rootContentHash"]), PRODUCER, 2, cast(str, rotated["contentHash"])); arguments["current_time"] = T20  # noqa: E702
    return arguments


def test_high_level_overlap_and_current_authorization_are_phase_local(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments = _rotated_arguments(); monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ())); overlap = cast(Any, future("resolve_complete_evidence", **arguments))  # noqa: E702
    monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **kw: trust.SignatureResult(b'"keyObjectId":"key:b' not in cast(bytes, kw["message"]), ())); suffix = cast(Any, future("resolve_complete_evidence", **arguments))  # noqa: E702
    assert overlap.trusted is True and suffix.historical_verdict is trust.Verdict.VALID and suffix.current_verdict is trust.Verdict.INVALID


def test_reconstruction_lineage_and_status_are_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload"); document = json.loads(manifest); document.update(revision=2, predecessorContentHash=None); document["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", document)  # noqa: E702
    lineage = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(document), retained_blobs=blobs, evaluation_time=T10); document = json.loads(manifest); document.update(currentVerdict="INVALID", currentFindings=[{"code": "KEY_REVOKED", "location": None}]); document["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", document)  # noqa: E702
    module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction"); monkeypatch.setattr(module, "resolve_complete_evidence", lambda **_: module._result(["KEY_REVOKED"], historical_verdict=trust.Verdict.VALID, current_verdict=trust.Verdict.INVALID)); inputs, _ = complete_arguments(); status = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(document), retained_blobs=blobs, evaluation_time=T10, trust_inputs=inputs); assert cast(Any, lineage).valid is False and cast(Any, status).valid is True  # noqa: E702


class _BoundedMap(dict[str, bytes]):
    traversed = False
    def items(self) -> Any: self.traversed = True; return super().items()  # noqa: E702
    def values(self) -> Any: self.traversed = True; return super().values()  # noqa: E702


def test_cardinality_bounds_precede_graph_and_crypto(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, _ = reconstruction_bundle(b"fixture-only payload"); blobs = _BoundedMap({f"{n:064x}": b"" for n in range(257)}); result = future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=blobs, evaluation_time=T10)  # noqa: E702
    arguments, state = complete_arguments(); documents = cast(dict[str, bytes], arguments["key_record_documents"]); original = cast(Mapping[str, object], state["key"])  # noqa: E702
    for n in range(64): clone = dict(original, keyObjectId=f"key:extra:{n}"); clone["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, clone); documents[cast(str, clone["contentHash"])] = trust.canonical_bytes(clone)  # noqa: E701, E702
    calls: list[int] = []; monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: (calls.__iadd__([1]), trust.SignatureResult(True, ()))[1]); key_result = future("resolve_complete_evidence", **arguments)  # noqa: E702
    assert "BLOB_COUNT_LIMIT" in codes(result) and not blobs.traversed and "HISTORY_RECORD_LIMIT" in codes(key_result) and not calls
