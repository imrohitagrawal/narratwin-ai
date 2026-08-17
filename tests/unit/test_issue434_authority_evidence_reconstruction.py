"""Continuation RED for complete Issue #434 trust and reconstruction."""

from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import Callable, Mapping
from typing import Any, cast

import pytest

from scripts.quality import issue434_authority_evidence_trust as trust


def future(name: str, **kwargs: object) -> object:
    """Keep RED importable while returning the repository's typed sentinel."""

    try:
        module = importlib.import_module(
            "scripts.quality.issue434_authority_evidence_reconstruction"
        )
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
        "schemaVersion": "AuthorityProducerTrustRootV1",
        "repository": REPOSITORY,
        "programId": PROGRAM,
        "generationId": GENERATION,
        "rootId": "root:fixture-only",
        "rootVersion": 1,
        "contentHash": "0" * 64,
        "producerId": PRODUCER,
        "validFrom": T00,
        "expiresAt": "2026-08-18T00:00:00Z",
        "signatureAlgorithm": "Ed25519",
        "publicKeyEncoding": "RAW_32_BYTE_LOWER_HEX",
        "rootAuthorizationKey": {"keyId": key_id, "publicKeyHex": public_key},
        "genesisCaptureKey": {
            "activationTime": T00,
            "keyId": key_id,
            "keyObjectId": "key:a:fixture-only",
            "publicKeyHex": public_key,
            "revision": 1,
        },
        "predecessorRootContentHash": None,
        "priorRootCompromise": None,
        "allowedSubjectSchemaVersions": ["ActiveProgramRouteV1"],
        "allowedTransitionRows": ["R01"],
        "allowedEvidenceRoles": ["INDEPENDENT_REVIEW"],
        "allowedPayloadMediaTypes": [
            "application/vnd.narratwin.authority.content-reference-v1+json"
        ],
        "freshnessPolicies": [
            {
                "transitionRowId": "R01",
                "evidenceRole": "INDEPENDENT_REVIEW",
                "freshnessClass": "TRANSITION_WINDOW",
                "maxCaptureDelaySeconds": 60,
                "maxObservationAgeSeconds": 300,
                "maxEnvelopeLifetimeSeconds": 300,
            }
        ],
        "maxPayloadBytes": 131072,
        "recoverySemantics": "INDEPENDENT_SUCCESSOR_PIN_ONLY",
        "revocationSemantics": (
            "INDEPENDENT_SUCCESSOR_PIN_WITH_EXACT_PRIOR_ROOT_BOUNDARY_ONLY"
        ),
        "prohibitedCapabilities": [
            "ACTIVATE_AUTHORITY",
            "DERIVE_ROOT_PIN",
            "GENERATE_KEY",
            "NETWORK_LOOKUP",
            "PERSIST_EVIDENCE",
            "SIGN",
        ],
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
    return json.dumps(
        {
            "typedReferenceTaxonomy": [
                {
                    "typedReferenceType": "REVIEW_SUBJECT",
                    "permittedRows": ["R01"],
                    "evidenceRole": "INDEPENDENT_REVIEW",
                    "producerTrustClass": "INDEPENDENT_REVIEWER",
                    "freshnessClass": "TRANSITION_WINDOW",
                    "payloadClass": "CONTENT_REFERENCE",
                }
            ],
            "payloadMediaTypeByClass": {
                "CONTENT_REFERENCE": (
                    "application/vnd.narratwin.authority.content-reference-v1+json"
                )
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def subject_envelope(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "typedReferenceType": "REVIEW_SUBJECT",
        "evidenceRole": "INDEPENDENT_REVIEW",
        "producerTrustClass": "INDEPENDENT_REVIEWER",
        "freshnessClass": "TRANSITION_WINDOW",
        "payloadClass": "CONTENT_REFERENCE",
        "payloadMediaType": (
            "application/vnd.narratwin.authority.content-reference-v1+json"
        ),
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
def test_subject_taxonomy_phase_and_freshness_are_one_binding(
    changes: dict[str, object], expected: str
) -> None:
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


def reconstruction_manifest(blobs: Mapping[str, bytes], **changes: object) -> bytes:
    references = [
        {
            "contentHash": digest,
            "byteLength": len(blob),
            "ordinal": ordinal,
            "role": "PAYLOAD",
        }
        for ordinal, (digest, blob) in enumerate(sorted(blobs.items()))
    ]
    value: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceReconstructionV1",
        "references": references,
        "retainedBlobCount": len(references),
        "aggregateRetainedByteLength": sum(len(blob) for blob in blobs.values()),
        "retentionUntil": "2026-08-18T00:00:00Z",
    }
    value.update(changes)
    return trust.canonical_bytes(value)


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
    digest = hashlib.sha256(payload).hexdigest()
    original = {digest: payload}
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
        manifest_bytes=reconstruction_manifest(original),
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
        "schemaVersion": "AuthorityEvidenceEnvelopeV1",
        "repository": REPOSITORY,
        "programId": PROGRAM,
        "generationId": GENERATION,
        "evidenceId": "evidence:fixture-only",
        "revision": 1,
        "predecessorContentHash": None,
        "contentHash": "0" * 64,
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
        "typedReferenceType": "REVIEW_SUBJECT",
        "evidenceRole": "INDEPENDENT_REVIEW",
        "producerTrustClass": "INDEPENDENT_REVIEWER",
        "freshnessClass": "TRANSITION_WINDOW",
        "payloadClass": "CONTENT_REFERENCE",
        "producerId": PRODUCER,
        "rootId": "root:fixture-only",
        "rootContentHash": root_hash,
        "signingKeyId": key["keyId"],
        "issuingKeyObjectId": key["keyObjectId"],
        "issuingKeyRevision": 1,
        "issuingKeyRecordContentHash": key["contentHash"],
        "signatureAlgorithm": "Ed25519",
        "canonicalSignatureProfile": "NarraTwinAuthorityEvidenceSignatureV1",
        "payloadMediaType": (
            "application/vnd.narratwin.authority.content-reference-v1+json"
        ),
        "payloadSha256": hashlib.sha256(payload).hexdigest(),
        "payloadByteLength": len(payload),
        "observedAt": T10,
        "capturedAt": T10,
        "notBefore": T10,
        "expiresAt": T20,
        "sourceClass": "FIXTURE",
        "collectionMethod": "SYNTHETIC_PUBLIC_VECTOR",
        "limitations": ["FIXTURE_ONLY"],
        "fixtureOnly": True,
        "signature": "0" * 128,
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
