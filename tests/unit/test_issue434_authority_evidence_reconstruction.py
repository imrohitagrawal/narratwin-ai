# ruff: noqa: E302, E305
from __future__ import annotations
import hashlib, importlib, json  # noqa: E401
from collections.abc import Callable, Mapping
from typing import Any, cast
import pytest
from scripts.quality import issue434_authority_evidence_trust as trust
import test_issue434_authority_evidence_trust as prior_tests
def future(name: str, **kwargs: object) -> object:
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
_BadMap=type("_BadMap",(Mapping,),{"__len__":lambda _:1,"__iter__":lambda _:iter([[]]),"__getitem__":lambda *_:None})
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
    assert cast(Any, result).valid is False and "temporal" not in importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction").validate_closed_root.__code__.co_varnames
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
    return (prior_tests.ROOT / "docs/governance/authority-evidence-trust-state-matrices-v1.json").read_bytes()
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
def test_all_ordered_pin_references_use_the_pin_hash_domain() -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload"); document = json.loads(manifest); created = [(references_name, digest, raw) for references_name, hash_name, fill in (("acceptanceRootPinReferences", "acceptanceRootPinSetHash", "f"), ("currentRootPinReferences", "currentRootPinSetHash", "e")) for n in range(1, 64) for base in [json.loads(blobs[document[hash_name]])] for descriptor in [dict(base, rootContentHashes=sorted([*base["rootContentHashes"], f"{n:063x}{fill}"]))] for raw in [trust.canonical_bytes(descriptor)] for digest in [pin_hash(descriptor)]]; blobs.update({digest: raw for _, digest, raw in created}); document.update({name: [*cast(list[dict[str, object]], document[name]), *(dict(cast(list[dict[str, object]], document[name])[0], contentHash=digest, byteLength=len(raw)) for reference_name, digest, raw in created if reference_name == name)] for name in ("acceptanceRootPinReferences", "currentRootPinReferences")}); references = [item for name in ("acceptanceRootPinReferences", "currentRootPinReferences", "rootReferences", "keyReferences") for item in document[name]] + [document["envelopeReference"], document["payloadReference"]]; [item.update(ordinal=index) for index, item in enumerate(references)]; document["retainedBlobCount"] = len(references); document["aggregateRetainedByteLength"] = sum(len(blob) for blob in blobs.values()); document["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", document); manifest = trust.canonical_bytes(document); result = future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=blobs, evaluation_time=T10); corruptions = [future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=dict(blobs, **{cast(str, cast(list[Mapping[str, object]], document[name])[position]["contentHash"]): trust.canonical_bytes(dict(json.loads(blobs[cast(str, cast(list[Mapping[str, object]], document[name])[position]["contentHash"])]), producerId="producer:fixture-evil"))}), evaluation_time=T10) for name in ("acceptanceRootPinReferences", "currentRootPinReferences") for position in (2, 63)]; assert len(cast(list[object], document["acceptanceRootPinReferences"])) == len(cast(list[object], document["currentRootPinReferences"])) == 64 and "RETAINED_BLOB_HASH_MISMATCH" not in codes(result) and all("RETAINED_BLOB_HASH_MISMATCH" in codes(item) for item in corruptions)  # noqa: B007, E702
def test_current_pin_failure_does_not_contaminate_history(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments(); arguments["current_expected_pin_hash"] = "f" * 64; module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction"); root_calls: list[str] = []; root_name = "_validate_closed_root" if hasattr(module, "_validate_closed_root") else "validate_closed_root"; original_root = getattr(module, root_name); monkeypatch.setattr(module, root_name, lambda **kw: (root_calls.__iadd__([cast(str, kw["expected_phase"])]), original_root(**kw))[1]); result = trusted_result(monkeypatch, arguments); invalid_hash_calls = tuple(root_calls); absent_hash, _ = complete_arguments(); absent_hash["acceptance_expected_pin_hash"] = None; absent_hash_result = trusted_result(monkeypatch, absent_hash); malformed_hash, _ = complete_arguments(); malformed_hash["acceptance_expected_pin_hash"] = {}; malformed_hash_result = trusted_result(monkeypatch, malformed_hash)  # noqa: E702
    missing, state = complete_arguments(); prior = cast(Mapping[str, object], state["root"]); successor = root_document(rootVersion=2, predecessorRootContentHash=prior["contentHash"]); descriptor = dict(cast(Mapping[str, object], missing["current_pin_descriptor"]), rootContentHashes=sorted([cast(str, prior["contentHash"]), cast(str, successor["contentHash"])])); missing.update(current_pin_descriptor=descriptor, current_expected_pin_hash=pin_hash(descriptor)); absent = trusted_result(monkeypatch, missing)  # noqa: E702
    misbound, _ = complete_arguments(); other = root_document(rootId="root:other"); descriptor = dict(cast(Mapping[str, object], misbound["acceptance_pin_descriptor"]), rootContentHashes=[other["contentHash"]]); misbound.update(acceptance_pin_descriptor=descriptor, acceptance_expected_pin_hash=pin_hash(descriptor)); cast(dict[str, bytes], misbound["root_documents"])[cast(str, other["contentHash"])] = trust.canonical_bytes(other); mismatch = trusted_result(monkeypatch, misbound)  # noqa: E702
    assert result.historical_verdict is trust.Verdict.VALID and result.current_verdict is not trust.Verdict.VALID and "CURRENT" not in invalid_hash_calls and absent_hash_result.historical_verdict is trust.Verdict.UNAVAILABLE and malformed_hash_result.historical_verdict is trust.Verdict.INVALID
    assert absent.historical_verdict is trust.Verdict.VALID and absent.current_verdict is trust.Verdict.UNAVAILABLE and mismatch.historical_verdict is trust.Verdict.INVALID
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
    result = trusted_result(monkeypatch, arguments); acceptance = dict(current, evaluationPhase="ACCEPTANCE"); both = dict(arguments, acceptance_pin_descriptor=acceptance, acceptance_expected_pin_hash=pin_hash(acceptance)); both_result = trusted_result(monkeypatch, both); prior_arguments, prior_state = complete_arguments(); prior_root = cast(dict[str, object], prior_state["root"]); later = root_document(rootId="root:later", rootVersion=2, predecessorRootContentHash=prior_root["contentHash"], priorRootCompromise={"priorRootContentHash": prior_root["contentHash"], "invalidatesPriorRootFrom": "2026-08-17T00:15:00Z"}); later["contentHash"] = trust.content_hash(trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", later); prior_hashes = sorted([cast(str, prior_root["contentHash"]), cast(str, later["contentHash"])]); prior_current = dict(cast(Mapping[str, object], prior_arguments["current_pin_descriptor"]), rootContentHashes=prior_hashes); prior_arguments.update(current_pin_descriptor=prior_current, current_expected_pin_hash=pin_hash(prior_current), current_time="2026-08-17T00:15:00Z"); cast(dict[str, bytes], prior_arguments["root_documents"])[cast(str, later["contentHash"])] = trust.canonical_bytes(later); prior_result = trusted_result(monkeypatch, prior_arguments); expired = root_document(expiresAt="2026-08-17T00:15:00Z"); policy = [{"transitionRowId": "R01", "evidenceRole": "INDEPENDENT_REVIEW", "freshnessClass": "TRANSITION_WINDOW", "maxCaptureDelaySeconds": 60, "maxObservationAgeSeconds": 1000, "maxEnvelopeLifetimeSeconds": 600}]; successor_arguments, successor_state = complete_arguments(_root_changes={"rootVersion": 2, "predecessorRootContentHash": expired["contentHash"], "validFrom": T10, "freshnessPolicies": policy}); signing_successor = cast(Mapping[str, object], successor_state["root"]); successor_hashes = sorted([cast(str, expired["contentHash"]), cast(str, signing_successor["contentHash"])]); successor_acceptance = dict(cast(Mapping[str, object], successor_arguments["acceptance_pin_descriptor"]), rootContentHashes=successor_hashes); successor_current = dict(cast(Mapping[str, object], successor_arguments["current_pin_descriptor"]), rootContentHashes=successor_hashes); successor_arguments.update(acceptance_pin_descriptor=successor_acceptance, acceptance_expected_pin_hash=pin_hash(successor_acceptance), current_pin_descriptor=successor_current, current_expected_pin_hash=pin_hash(successor_current), current_time="2026-08-17T00:19:59Z"); cast(dict[str, bytes], successor_arguments["root_documents"])[cast(str, expired["contentHash"])] = trust.canonical_bytes(expired); successor_result = trusted_result(monkeypatch, successor_arguments)  # noqa: E702
    assert result.historical_verdict is trust.Verdict.VALID and both_result.historical_verdict is trust.Verdict.INVALID and prior_result.current_verdict is trust.Verdict.VALID
    rotated = _rotated_arguments(); old_hash = cast(trust.HistoryHead, rotated["acceptance_head"]).root_content_hash; old_root = json.loads(cast(dict[str, bytes], rotated["root_documents"])[old_hash]); recovery = root_document(rootId=old_root["rootId"], rootVersion=2, predecessorRootContentHash=old_hash, priorRootCompromise={"priorRootContentHash": old_hash, "invalidatesPriorRootFrom": T20}); recovery_hashes = sorted([old_hash, cast(str, recovery["contentHash"])]); recovery_pin = dict(cast(Mapping[str, object], rotated["current_pin_descriptor"]), rootContentHashes=recovery_hashes); rotated.update(current_pin_descriptor=recovery_pin, current_expected_pin_hash=pin_hash(recovery_pin)); cast(dict[str, bytes], rotated["root_documents"])[cast(str, recovery["contentHash"])] = trust.canonical_bytes(recovery); rotated_result = trusted_result(monkeypatch, rotated); k02 = json.loads(cast(dict[str, bytes], rotated["key_record_documents"])[cast(trust.HistoryHead, rotated["current_head"]).key_record_content_hash]); k03 = dict(k02, revision=2, predecessorContentHash=k02["contentHash"], historySequence=3, historyPredecessorContentHash=k02["contentHash"], rotationPredecessor=None, operation="RETIRE", retiredAt="2026-08-17T00:20:01Z", predecessorAuthorizationSignature=None); k03["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, k03); cast(dict[str, bytes], rotated["key_record_documents"])[cast(str, k03["contentHash"])] = trust.canonical_bytes(k03); rotated.update(current_head=trust.HistoryHead(old_hash, PRODUCER, 3, cast(str, k03["contentHash"])), current_time="2026-08-17T00:20:01Z"); retired_result = trusted_result(monkeypatch, rotated); assert result.current_verdict is not trust.Verdict.VALID and rotated_result.historical_verdict is trust.Verdict.VALID and (successor_result.trusted, rotated_result.current_verdict, retired_result.current_verdict) == (True, trust.Verdict.INVALID, trust.Verdict.INVALID)  # noqa: E702
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
@pytest.mark.parametrize(("field", "value"), [("subject", {"objectId": "route:other"}), ("reconstructionStatus", "INVALID"), ("repository", "other.invalid/repo"), ("programId", "program:other"), ("generationId", "generation:other")])
def test_reconstruction_claims_bind_retained_envelope(monkeypatch: pytest.MonkeyPatch, field: str, value: object) -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload"); document = json.loads(manifest)  # noqa: E702
    document[field] = dict(document[field], **cast(dict[str, object], value)) if field == "subject" else value
    if field == "generationId": document["subject"]["generationId"] = value  # noqa: E701
    document["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", document)
    inputs, _ = complete_arguments(); monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ()))  # noqa: E702
    result = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(document), retained_blobs=blobs, evaluation_time=T10, trust_inputs=inputs)
    assert cast(Any, result).valid is False
def test_k02_does_not_retire_k01_before_explicit_boundary() -> None:
    rows = prior_tests.key_rows(); result = trust.resolve_issuing_key_structure(records=(rows["K01"], rows["K02"]), expected_head=prior_tests.head(rows["K02"]), issuing_key=(rows["K01"]["keyObjectId"], rows["K01"]["keyId"], 1, rows["K01"]["contentHash"]), capture_time=prior_tests.T09)  # noqa: E702
    assert result.issuing_key_eligible is True
@pytest.mark.parametrize("change", [{"payloadClass": {}}, {"limitations": [set()]}])
def test_public_subject_boundary_contains_unhashable_payload_class(change: dict[str, object]) -> None:
    try: result = future("validate_subject_phase", envelope=subject_envelope(**change), root=root_document(), taxonomy_matrix_bytes=taxonomy_matrix(), evaluation_time=T10); arguments, _ = complete_arguments(); high = future("resolve_complete_evidence", **dict(arguments, root_documents=_BadMap())); rows = prior_tests.key_rows(); low = prior_tests.inspect_structure((cast(Any, _BadMap()),), expected_head=prior_tests.head(rows["K01"])); bad_schema = trust.validate_closed_schema_value("x", cast(Any, _BadMap())); bad_artifacts = future("validate_artifact_set", artifacts=_BadMap(), child_a_matrix_bytes=taxonomy_matrix())  # noqa: E701, E702
    except Exception as exc: pytest.fail(f"RAW_EXCEPTION:{type(exc).__name__}")  # noqa: BLE001, E701
    malformed = cast(Any, trust.evaluate_evidence)(envelope_bytes={}, payload_bytes={}, root_documents={}, producer_key_records={}, independent_trust={}, acceptance_time=T10, current_time=T10); schema = trust.validate_closed_schema_value("x", cast(Any, [])); assert cast(Any, result).valid is False and malformed.historical_verdict is trust.Verdict.INVALID and schema[0].code == bad_schema[0].code == "SCHEMA_DOCUMENT_INVALID" and "CONTRACT_ARTIFACT_INVALID" in codes(bad_artifacts) and cast(Any, high).historical_verdict is trust.Verdict.INVALID and "UNSUPPORTED_JSON_TYPE" in prior_tests.finding_codes(low)  # noqa: E702
def test_replay_requires_exact_contiguous_predecessor(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, state = complete_arguments(); first = cast(bytes, arguments["envelope_bytes"]); second = dict(cast(Mapping[str, object], state["envelope"]), revision=2, predecessorContentHash="f" * 64)  # noqa: E702
    second["contentHash"] = trust.content_hash(trust.ContentKind.EVIDENCE_OBJECT, trust.ENVELOPE_SCHEMA_VERSION, second); raw = trust.canonical_bytes(second)  # noqa: E702
    results = [cast(Any, future("validate_evidence_replay_set", envelope_documents=documents)).valid for documents in ((raw,), (first, raw))]; calls: list[int] = []; monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: (calls.append(1), trust.SignatureResult(True, ()))[1]); high = future("resolve_complete_evidence", **dict(arguments, envelope_bytes=raw))  # noqa: E702
    assert results == [False, False] and cast(Any, high).trusted is False and "EVIDENCE_PREDECESSOR_MISMATCH" in codes(high) and not calls
@pytest.mark.parametrize(("missing", "preserved", "absent"), [("acceptance_head", "current_verdict", "historical_verdict"), ("current_head", "historical_verdict", "current_verdict"), ("acceptance_pin_descriptor", "current_verdict", "historical_verdict")])
def test_missing_head_does_not_contaminate_other_phase(monkeypatch: pytest.MonkeyPatch, missing: str, preserved: str, absent: str) -> None:
    arguments, _ = complete_arguments(); arguments[missing] = None; result = trusted_result(monkeypatch, arguments)  # noqa: E702
    expected = {"acceptance_head": "ACCEPTANCE_HEAD_REQUIRED", "current_head": "CURRENT_HEAD_REQUIRED", "acceptance_pin_descriptor": "ROOT_PIN_DESCRIPTOR_REQUIRED"}[missing]
    assert getattr(result, preserved) is trust.Verdict.VALID and getattr(result, absent) is trust.Verdict.UNAVAILABLE and expected in codes(result)
@pytest.mark.parametrize(("phase", "member"), [(phase, member) for phase in ("acceptance_head", "current_head") for member in ("root_content_hash", "producer_id", "history_sequence", "key_record_content_hash")])
def test_malformed_head_members_are_phase_local(monkeypatch: pytest.MonkeyPatch, phase: str, member: str) -> None:
    arguments, _ = complete_arguments(); head = cast(trust.HistoryHead, arguments[phase]); values: list[object] = [head.root_content_hash, head.producer_id, head.history_sequence, head.key_record_content_hash]; values[("root_content_hash", "producer_id", "history_sequence", "key_record_content_hash").index(member)] = {}; arguments[phase] = trust.HistoryHead(*cast(tuple[str, str, int, str], tuple(values))); result = trusted_result(monkeypatch, arguments)  # noqa: E702
    affected, preserved = (("historical_verdict", "current_verdict") if phase == "acceptance_head" else ("current_verdict", "historical_verdict")); assert getattr(result, affected) is trust.Verdict.INVALID and getattr(result, preserved) is trust.Verdict.VALID and f"{phase.split('_')[0].upper()}_HEAD_INVALID" in codes(result)  # noqa: E702
def test_missing_exact_key_bytes_are_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments(); result = trusted_result(monkeypatch, dict(arguments, key_record_documents={})); partial = _rotated_arguments(); current = cast(trust.HistoryHead, partial["current_head"]); cast(dict[str, bytes], partial["key_record_documents"]).pop(current.key_record_content_hash); partial_result = trusted_result(monkeypatch, partial); assert result.historical_verdict is trust.Verdict.UNAVAILABLE and result.current_verdict is trust.Verdict.UNAVAILABLE and "KEY_RECORD_UNAVAILABLE" in codes(result) and partial_result.historical_verdict is trust.Verdict.VALID and partial_result.current_verdict is trust.Verdict.UNAVAILABLE  # noqa: E702
def test_root_payload_limit_and_conflicting_successor_boundaries_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments(_root_changes={"maxPayloadBytes": 1}); payload_result = trusted_result(monkeypatch, arguments)  # noqa: E702
    arguments, state = complete_arguments(); prior = cast(dict[str, object], state["root"]); successors = [root_document(rootId=f"root:s{n}", rootVersion=2, predecessorRootContentHash=prior["contentHash"], priorRootCompromise={"priorRootContentHash": prior["contentHash"], "invalidatesPriorRootFrom": when}) for n, when in enumerate((T00, T20))]  # noqa: E702
    hashes = sorted([cast(str, prior["contentHash"]), *(cast(str, row["contentHash"]) for row in successors)]); descriptor = dict(cast(Mapping[str, object], arguments["current_pin_descriptor"]), rootContentHashes=hashes)  # noqa: E702
    arguments["current_pin_descriptor"] = descriptor; arguments["current_expected_pin_hash"] = pin_hash(descriptor); cast(dict[str, bytes], arguments["root_documents"]).update({cast(str, row["contentHash"]): trust.canonical_bytes(row) for row in successors})  # noqa: E702
    conflict_result = trusted_result(monkeypatch, arguments)
    assert payload_result.trusted is False and conflict_result.current_verdict is trust.Verdict.CONFLICTING
@pytest.mark.parametrize(("source", "expected"), [("K03", "RETIRE_SOURCE_STATE"), ("K04", "REVOKE_SOURCE_STATE")])
def test_terminal_key_states_cannot_repeat(source: str, expected: str) -> None:
    rows = prior_tests.key_rows(); prior = rows[source]; operation = cast(str, prior["operation"]); illegal = prior_tests.key_record(4, operation=operation, previous=prior, key_object_id=cast(str, prior["keyObjectId"]), public_key_hex=cast(str, prior["publicKeyHex"]), revision=3, activationTime=prior_tests.T10)  # noqa: E702
    assert prior_tests.finding_codes(prior_tests.inspect_structure((rows["K01"], rows["K02"], prior, illegal), expected_head=prior_tests.head(illegal))) == {expected}
def test_k04_observation_time_and_predecessor_overlap_are_high_level(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = prior_tests.key_rows(); result = future("resolve_issuing_key", records=(rows["K01"], rows["K02"], rows["K04"]), expected_head=prior_tests.head(rows["K04"]), issuing_key=(rows["K02"]["keyObjectId"], rows["K02"]["keyId"], 1, rows["K02"]["contentHash"]), capture_time=prior_tests.T15, evaluation_time=prior_tests.T29)  # noqa: E702
    malformed = [future("resolve_issuing_key", records=(rows["K01"], rows["K02"]), expected_head=prior_tests.head(rows["K02"]), issuing_key=(rows["K02"]["keyObjectId"], rows["K02"]["keyId"], 1, rows["K02"]["contentHash"]), capture_time=prior_tests.T15, evaluation_time=value) for value in cast(tuple[object, ...], ({}, "bad-time"))]
    assert cast(Any, result).issuing_key_eligible is True and all(not cast(Any, item).issuing_key_eligible and "TIME_FORMAT" in codes(item) for item in malformed)
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
def test_reconstruction_finding_arrays_use_exact_evidence_member_bound() -> None:
    manifest, _ = reconstruction_bundle(b"fixture-only payload"); document = json.loads(manifest); document["historicalFindings"] = [{"code": "FIXTURE_FINDING", "location": None} for _ in range(65)]  # noqa: E702
    try: raw = trust.canonical_bytes(document)  # noqa: E701
    except Exception as exc: pytest.fail(f"RAW_EXCEPTION:{type(exc).__name__}")  # noqa: BLE001, E701
    schema = json.loads(prior_tests.contract_artifacts()["docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json"]); findings = trust.validate_closed_schema_value(document, schema); assert raw and "COLLECTION_LIMIT" not in {item.code for item in findings}  # noqa: E702
    pytest.raises(trust.AuthorityEvidenceTrustError, trust.canonical_bytes, {"ordinary": {"currentFindings": document["historicalFindings"]}}); pytest.raises(trust.AuthorityEvidenceTrustError, trust.canonical_bytes, {"schemaVersion": "AuthorityEvidenceReconstructionV1", "historicalFindings": document["historicalFindings"]}); finding = json.loads(prior_tests.contract_artifacts()["docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json"])["$defs"]["finding"]; truncated = json.loads(json.dumps(schema)); properties = truncated["root"]["properties"]; truncated["root"].update(required=["historicalFindings", "currentFindings"], properties={name: properties[name] for name in ("historicalFindings", "currentFindings")}); escaped = {"contractVersion": "OtherV1", "$defs": {"finding": finding}, "root": {"type": "object", "closed": True, "required": ["historicalFindings"], "properties": {"historicalFindings": {"type": "array", "maxItems": 256, "items": {"$ref": "finding"}}}}}; wrong_item = {"contractVersion": "AuthorityEvidenceReconstructionV1", "$defs": {"finding": {"type": "string"}}, "root": {"type": "object", "closed": True, "required": ["historicalFindings"], "properties": {"historicalFindings": {"type": "array", "maxItems": 256, "items": {"$ref": "finding"}}}}}; transition = {"$defs": {}, "root": {"type": "array", "maxItems": 64, "order": "TRANSITION_ROW_THEN_EVIDENCE_ROLE_ASCENDING", "items": {"type": "object", "closed": True, "required": ["transitionRowId", "evidenceRole"], "properties": {"transitionRowId": {"type": "integer"}, "evidenceRole": {"type": "integer"}}}}}; assert all("SCHEMA_DESCRIPTOR_INVALID" in {item.code for item in trust.validate_closed_schema_value(value, candidate)} for value, candidate in (({"historicalFindings": document["historicalFindings"], "currentFindings": []}, truncated), ({"historicalFindings": document["historicalFindings"]}, escaped), ({"historicalFindings": ["x"] * 65}, wrong_item), ([{"transitionRowId": 2, "evidenceRole": 2}, {"transitionRowId": 1, "evidenceRole": 1}], transition)))  # noqa: E702
class _BoundedMap(dict[str, bytes]):
    traversed = False
    def items(self) -> Any: self.traversed = True; return super().items()  # noqa: E702
    def values(self) -> Any: self.traversed = True; return super().values()  # noqa: E702
def test_cardinality_bounds_precede_graph_and_crypto(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, _ = reconstruction_bundle(b"fixture-only payload"); blobs = _BoundedMap({f"{n:064x}": b"" for n in range(257)}); result = future("reconstruct_retained_evidence", manifest_bytes=manifest, retained_blobs=blobs, evaluation_time=T10); aggregate_manifest, aggregate_blobs = reconstruction_bundle(b"fixture-only payload"); aggregate = json.loads(aggregate_manifest); reference = aggregate["keyReferences"][0]; aggregate_blobs.pop(reference["contentHash"]); aggregate["keyReferences"] = []  # noqa: E702
    for n in range(64): blob = b" " * (trust.RETAINED_BLOB_MAX_BYTES - 64) + f"{n:064x}".encode(); digest = hashlib.sha256(blob).hexdigest(); aggregate["keyReferences"].append(dict(reference, contentHash=digest, byteLength=len(blob), ordinal=3 + n)); aggregate_blobs[digest] = blob  # noqa: E701, E702
    aggregate["envelopeReference"]["ordinal"] = 67; aggregate["payloadReference"]["ordinal"] = 68; aggregate["retainedBlobCount"] = 69; aggregate["aggregateRetainedByteLength"] = trust.RETAINED_BLOBS_AGGREGATE_MAX_BYTES; aggregate["contentHash"] = trust.content_hash(trust.ContentKind.RECONSTRUCTION, "AuthorityEvidenceReconstructionV1", aggregate); module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction"); original_parse = module._parse; parsed: list[int] = []; monkeypatch.setattr(module, "_parse", lambda raw, **kw: (parsed.__iadd__([len(raw)]) if isinstance(raw, bytes) and len(raw) == trust.RETAINED_BLOB_MAX_BYTES else parsed, original_parse(raw, **kw))[1]); aggregate_result = future("reconstruct_retained_evidence", manifest_bytes=trust.canonical_bytes(aggregate), retained_blobs=aggregate_blobs, evaluation_time=T10); original_json = trust._parse_json_object; core_parsed: list[int] = []; monkeypatch.setattr(trust, "_parse_json_object", lambda raw, **kw: (core_parsed.__iadd__([len(raw)]), original_json(raw, **kw))[1]); core_blobs = {f"{n:064x}": b" " * (trust.RETAINED_BLOB_MAX_BYTES - len(suffix)) + suffix for n in range(65) for suffix in [f'{{"n":{n}}}'.encode()]}; core_result = trust._validate_blob_mapping(core_blobs, "rootDocuments", trust.ContentKind.TRUST_ROOT, trust.TRUST_ROOT_SCHEMA_VERSION); core_parse_count = len(core_parsed)  # noqa: E702
    arguments, state = complete_arguments(); documents = cast(dict[str, bytes], arguments["key_record_documents"]); original = cast(Mapping[str, object], state["key"])  # noqa: E702
    for n in range(64): clone = dict(original, keyObjectId=f"key:extra:{n}"); clone["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, clone); documents[cast(str, clone["contentHash"])] = trust.canonical_bytes(clone)  # noqa: E701, E702
    calls: list[int] = []; monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: (calls.__iadd__([1]), trust.SignatureResult(True, ()))[1]); key_result = future("resolve_complete_evidence", **arguments); key_calls = len(calls); pin_args, state = complete_arguments(); root_hash = cast(str, cast(Mapping[str, object], state["root"])["contentHash"]); descriptor = dict(cast(Mapping[str, object], pin_args["current_pin_descriptor"]), rootContentHashes=sorted([root_hash, *(f"{n:064x}" for n in range(64))])); pin_args.update(current_pin_descriptor=descriptor, current_expected_pin_hash="f" * 64); root_calls: list[str] = []; root_name = "_validate_closed_root" if hasattr(module, "_validate_closed_root") else "validate_closed_root"; original_root = getattr(module, root_name); monkeypatch.setattr(module, root_name, lambda **kw: (root_calls.__iadd__([cast(str, kw["expected_phase"])]), original_root(**kw))[1]); pin_result = future("resolve_complete_evidence", **pin_args)  # noqa: E702
    assert "BLOB_COUNT_LIMIT" in codes(result) and not blobs.traversed and "BLOB_AGGREGATE_SIZE_LIMIT" in codes(aggregate_result) and not parsed and any(item.code == "BLOB_COUNT_LIMIT" for item in core_result) and not core_parse_count and "HISTORY_RECORD_LIMIT" in codes(key_result) and not key_calls and "ROOT_PIN_DESCRIPTOR_INVALID" in codes(pin_result) and "CURRENT" not in root_calls
def test_capture_and_root_must_be_valid_at_each_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    policy = [{"transitionRowId": "R01", "evidenceRole": "INDEPENDENT_REVIEW", "freshnessClass": "TRANSITION_WINDOW", "maxCaptureDelaySeconds": 60, "maxObservationAgeSeconds": 1200, "maxEnvelopeLifetimeSeconds": 1200}]
    future_args, _ = complete_arguments(_root_changes={"freshnessPolicies": policy}, observedAt=prior_tests.T19, capturedAt=prior_tests.T19, expiresAt=prior_tests.T30); early_args, _ = complete_arguments(_root_changes={"validFrom": T10, "freshnessPolicies": policy}, observedAt=T00, capturedAt=T00)  # noqa: E702
    results = [trusted_result(monkeypatch, item).trusted for item in (future_args, early_args)]; assert results == [False, False]  # noqa: E702
def test_current_only_malformed_key_is_phase_local(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments = _rotated_arguments(); head = cast(trust.HistoryHead, arguments["current_head"]); documents = cast(dict[str, bytes], arguments["key_record_documents"]); row = json.loads(documents.pop(head.key_record_content_hash)); row["operation"] = {}; row["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, row)  # noqa: E702
    documents[cast(str, row["contentHash"])] = trust.canonical_bytes(row); arguments["current_head"] = trust.HistoryHead(head.root_content_hash, head.producer_id, 2, cast(str, row["contentHash"])); result = trusted_result(monkeypatch, arguments); ordered = _rotated_arguments(); records = cast(dict[str, bytes], ordered["key_record_documents"]); current = cast(trust.HistoryHead, ordered["current_head"]); clone = dict(json.loads(records[current.key_record_content_hash]), keyObjectId="key:competing", publicKeyHex="4" * 64, keyId=prior_tests.public_key_id("4" * 64), rootAuthorizationSignature="f" * 128, predecessorAuthorizationSignature="e" * 128); clone["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, clone); clone_raw = trust.canonical_bytes(clone); permutations = [dict(records, **{cast(str, clone["contentHash"]): clone_raw}), {cast(str, clone["contentHash"]): clone_raw, **records}]; checked: list[str] = []; monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **kw: (checked.__iadd__([cast(str, kw["signature_hex"])]), trust.SignatureResult(kw["signature_hex"] not in {"e" * 128, "f" * 128}, ()))[1]); phase_results = [cast(Any, future("resolve_complete_evidence", **dict(ordered, key_record_documents=value))) for value in permutations]  # noqa: E702
    genesis_hash = cast(trust.HistoryHead, ordered["acceptance_head"]).key_record_content_hash; genesis = json.loads(records[genesis_hash]); headed_row = dict(clone, publicKeyHex=genesis["publicKeyHex"], keyId=genesis["keyId"]); headed_row["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, headed_row); headed = dict(ordered, key_record_documents={genesis_hash: records[genesis_hash], cast(str, headed_row["contentHash"]): trust.canonical_bytes(headed_row)}, current_head=trust.HistoryHead(current.root_content_hash, current.producer_id, 2, cast(str, headed_row["contentHash"]))); headed_result = future("resolve_complete_evidence", **headed); duplicate = _rotated_arguments(); duplicate_head = cast(trust.HistoryHead, duplicate["current_head"]); duplicate_docs = cast(dict[str, bytes], duplicate["key_record_documents"]); duplicate_row = json.loads(duplicate_docs.pop(duplicate_head.key_record_content_hash)); duplicate_row["keyId"] = json.loads(duplicate_docs[cast(trust.HistoryHead, duplicate["acceptance_head"]).key_record_content_hash])["keyId"]; duplicate_row["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, duplicate_row); duplicate_docs[cast(str, duplicate_row["contentHash"])] = trust.canonical_bytes(duplicate_row); duplicate["current_head"] = trust.HistoryHead(duplicate_head.root_content_hash, duplicate_head.producer_id, 2, cast(str, duplicate_row["contentHash"])); duplicate_result = trusted_result(monkeypatch, duplicate); nonhex = _rotated_arguments(); nonhex_head = cast(trust.HistoryHead, nonhex["current_head"]); nonhex_docs = cast(dict[str, bytes], nonhex["key_record_documents"]); nonhex_row = json.loads(nonhex_docs.pop(nonhex_head.key_record_content_hash)); nonhex_row["publicKeyHex"] = "g" * 64; nonhex_row["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, nonhex_row); nonhex_docs[cast(str, nonhex_row["contentHash"])] = trust.canonical_bytes(nonhex_row); nonhex["current_head"] = trust.HistoryHead(nonhex_head.root_content_hash, nonhex_head.producer_id, 2, cast(str, nonhex_row["contentHash"])); nonhex_result = trusted_result(monkeypatch, nonhex); assert result.historical_verdict is trust.Verdict.VALID and result.current_verdict is trust.Verdict.INVALID and all(item.historical_verdict is trust.Verdict.VALID and item.current_verdict is trust.Verdict.INVALID and "HISTORY_FORK" not in codes(item) for item in phase_results) and {"e" * 128, "f" * 128} <= set(checked) and headed_result.historical_verdict is trust.Verdict.VALID and headed_result.current_verdict is trust.Verdict.INVALID and "DUPLICATE_PUBLIC_KEY" not in codes(headed_result) and duplicate_result.current_verdict is trust.Verdict.INVALID and "DUPLICATE_KEY_ID" not in codes(duplicate_result) and nonhex_result.historical_verdict is trust.Verdict.VALID and nonhex_result.current_verdict is trust.Verdict.INVALID and "STRING_PATTERN" in codes(nonhex_result)  # noqa: E702
def test_rotation_and_global_history_predecessors_are_distinct() -> None:
    rows = prior_tests.key_rows(); k03 = prior_tests.key_record(3, operation="RETIRE", previous=rows["K01"], key_object_id=cast(str, rows["K01"]["keyObjectId"]), public_key_hex=cast(str, rows["K01"]["publicKeyHex"]), revision=2, historyPredecessorContentHash=rows["K02"]["contentHash"]); k04 = prior_tests.key_record(4, operation="ROTATE", previous=rows["K02"], key_object_id="key:c:fixture-only", public_key_hex="3" * 64, predecessor_signature="0" * 128, historyPredecessorContentHash=k03["contentHash"])  # noqa: E702
    assert not prior_tests.finding_codes(prior_tests.inspect_structure((rows["K01"], rows["K02"], k03, k04), expected_head=prior_tests.head(k04)))
@pytest.mark.parametrize(("field", "value"), [("subject", "route:other"), ("evidenceRole", "HUMAN_AUTHORITY"), ("producerId", "producer:other")])
def test_replay_revision_carries_all_immutable_bindings(field: str, value: str) -> None:
    arguments, state = complete_arguments(); first = cast(Mapping[str, object], state["envelope"]); second = dict(first, revision=2, predecessorContentHash=first["contentHash"]); second[field] = dict(cast(Mapping[str, object], second["subject"]), objectId=value) if field == "subject" else value; second["contentHash"] = trust.content_hash(trust.ContentKind.EVIDENCE_OBJECT, trust.ENVELOPE_SCHEMA_VERSION, second)  # noqa: E702
    assert cast(Any, future("validate_evidence_replay_set", envelope_documents=(arguments["envelope_bytes"], trust.canonical_bytes(second)))).valid is False
def test_artifact_aliases_and_root_history_topology_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = prior_tests.contract_artifacts(); aliases = dict(artifacts, **{f"duplicate/{name}": raw for name, raw in artifacts.items()}); renamed = {f"alias/{name.rsplit('/', 1)[-1]}": raw for name, raw in artifacts.items()}; child = (prior_tests.ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_bytes(); artifact_results = [future("validate_artifact_set", artifacts=value, child_a_matrix_bytes=child, expected_artifact_hashes=None) for value in (aliases, renamed)]  # noqa: E702
    arguments, state = complete_arguments(); prior = cast(Mapping[str, object], state["root"]); successors = [root_document(rootId=prior["rootId"], rootVersion=2, predecessorRootContentHash=prior["contentHash"], expiresAt=f"2026-08-{18 + n}T00:00:00Z") for n in range(2)]; hashes = sorted([cast(str, prior["contentHash"]), *(cast(str, row["contentHash"]) for row in successors)]); descriptor = dict(cast(Mapping[str, object], arguments["current_pin_descriptor"]), rootContentHashes=hashes); arguments.update(current_pin_descriptor=descriptor, current_expected_pin_hash=pin_hash(descriptor)); cast(dict[str, bytes], arguments["root_documents"]).update({cast(str, row["contentHash"]): trust.canonical_bytes(row) for row in successors}); topology = trusted_result(monkeypatch, arguments); genesis = root_document(rootId="root:unrelated"); roots = [cast(str, prior["contentHash"]), cast(str, genesis["contentHash"])]; descriptor = dict(cast(Mapping[str, object], complete_arguments()[0]["current_pin_descriptor"]), rootContentHashes=sorted(roots)); genesis_args, _ = complete_arguments(); genesis_args.update(current_pin_descriptor=descriptor, current_expected_pin_hash=pin_hash(descriptor)); cast(dict[str, bytes], genesis_args["root_documents"])[cast(str, genesis["contentHash"])] = trust.canonical_bytes(genesis); genesis_result = trusted_result(monkeypatch, genesis_args); malformed = dict(prior, surprise=True); malformed["contentHash"] = trust.content_hash(trust.ContentKind.TRUST_ROOT, trust.TRUST_ROOT_SCHEMA_VERSION, malformed); malformed_args, _ = complete_arguments(); roots = [cast(str, prior["contentHash"]), cast(str, malformed["contentHash"])]; descriptor = dict(cast(Mapping[str, object], malformed_args["current_pin_descriptor"]), rootContentHashes=sorted(roots)); malformed_args.update(current_pin_descriptor=descriptor, current_expected_pin_hash=pin_hash(descriptor)); cast(dict[str, bytes], malformed_args["root_documents"])[cast(str, malformed["contentHash"])] = trust.canonical_bytes(malformed); malformed_result = trusted_result(monkeypatch, malformed_args); identity_args, _ = complete_arguments(); identity_prior = cast(trust.HistoryHead, identity_args["current_head"]).root_content_hash; forged = "f" * 64; identity_descriptor = dict(cast(Mapping[str, object], identity_args["current_pin_descriptor"]), rootContentHashes=sorted([identity_prior, forged])); identity_args.update(current_pin_descriptor=identity_descriptor, current_expected_pin_hash=pin_hash(identity_descriptor)); cast(dict[str, bytes], identity_args["root_documents"])[forged] = cast(dict[str, bytes], identity_args["root_documents"])[identity_prior]; identity_result = trusted_result(monkeypatch, identity_args)  # noqa: E702
    assert all(cast(Any, result).valid is False for result in artifact_results) and topology.current_verdict is trust.Verdict.CONFLICTING and genesis_result.current_verdict is trust.Verdict.CONFLICTING and malformed_result.current_verdict is trust.Verdict.INVALID and identity_result.current_verdict is trust.Verdict.INVALID and "ROOT_CONTENT_HASH_MISMATCH" in codes(identity_result) and "ROOT_HISTORY_CONFLICT" not in codes(identity_result)
def test_competing_and_temporally_illegal_key_successors_fail_closed() -> None:
    rows = prior_tests.key_rows(); k02 = rows["K02"]; same = {"key_object_id": cast(str, k02["keyObjectId"]), "public_key_hex": cast(str, k02["publicKeyHex"])}  # noqa: E702
    rotate_fork = prior_tests.key_record(3, operation="ROTATE", previous=rows["K01"], key_object_id="key:c:fixture-only", public_key_hex="3" * 64, predecessor_signature="0" * 128, historyPredecessorContentHash=k02["contentHash"])
    revoke_fork = prior_tests.key_record(4, operation="REVOKE", previous=k02, revision=2, historyPredecessorContentHash=rows["K03"]["contentHash"], activationTime=prior_tests.T10, **same)
    retired_rotation = prior_tests.key_record(4, operation="ROTATE", previous=k02, key_object_id="key:c:fixture-only", public_key_hex="3" * 64, predecessor_signature="0" * 128, historyPredecessorContentHash=rows["K03"]["contentHash"])
    parent = prior_tests.key_record(1, activationTime=prior_tests.T10); early = prior_tests.key_record(2, operation="ROTATE", previous=parent, key_object_id="key:c:fixture-only", public_key_hex="3" * 64, predecessor_signature="0" * 128, activationTime=T00)  # noqa: E702
    bad_k05 = prior_tests.key_record(4, operation="REVOKE", previous=rows["K03"], revision=3, activationTime=prior_tests.T10, retiredAt=prior_tests.T20, invalidatesFrom=prior_tests.T10, revokedAt=prior_tests.T15, **same)
    bad_k04 = dict(rows["K04"], predecessorAuthorizationSignature="1" * 128); bad_k04["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, bad_k04); bad_k05_fields = dict(rows["K05"], rotationPredecessor={"keyObjectId": rows["K01"]["keyObjectId"], "revision": 1, "contentHash": rows["K01"]["contentHash"]}); bad_k05_fields["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, trust.PRODUCER_KEY_SCHEMA_VERSION, bad_k05_fields); cases = [((rows["K01"], k02, rotate_fork), rotate_fork), ((rows["K01"], k02, rows["K03"], revoke_fork), revoke_fork), ((rows["K01"], k02, rows["K03"], retired_rotation), retired_rotation), ((parent, early), early), ((rows["K01"], k02, bad_k04), bad_k04), ((rows["K01"], k02, rows["K03"], bad_k05_fields), bad_k05_fields)]  # noqa: E702
    findings = [prior_tests.finding_codes(prior_tests.inspect_structure(records, expected_head=prior_tests.head(head))) for records, head in cases]
    findings.append(prior_tests.finding_codes(prior_tests.inspect_structure((rows["K01"], k02, rows["K03"], bad_k05), expected_head=prior_tests.head(bad_k05), evaluation_time=prior_tests.T14))); expected = ("HISTORY_FORK", "HISTORY_FORK", "ROTATION_SOURCE_STATE", "ROTATION_TEMPORAL_ORDER", "PREDECESSOR_AUTHORIZATION_PROHIBITED", "PREDECESSOR_AUTHORIZATION_PROHIBITED", "REVOCATION_BOUNDARY_ORDER"); assert all(code in found for code, found in zip(expected, findings, strict=True)), findings  # noqa: E702
def test_taxonomy_mime_exactness_and_immutable_freshness() -> None:
    matrix = json.loads(taxonomy_matrix()); selected = next(row for row in matrix["typedReferenceTaxonomy"] if row["typedReferenceType"] == "REVIEW_SUBJECT"); truncated = trust.canonical_bytes({"typedReferenceTaxonomy": [selected], "payloadMediaTypeByClass": {"CONTENT_REFERENCE": matrix["payloadMediaTypeByClass"]["CONTENT_REFERENCE"]}})  # noqa: E702
    r01 = {"schemaVersion": "ActiveProgramRouteV1", "transitionRowId": "R01", "sourceState": "DRAFT", "operation": "REVIEW", "targetState": "REVIEWED"}; exact = future("validate_subject_phase", envelope=subject_envelope(subject=r01), root=root_document(), taxonomy_matrix_bytes=truncated, evaluation_time=T10); matrix["payloadMediaTypeByClass"]["CONTENT_REFERENCE"] = matrix["payloadMediaTypeByClass"]["OWNER_DECISION"]; mime = future("validate_subject_phase", envelope=subject_envelope(subject=r01, payloadMediaType=matrix["payloadMediaTypeByClass"]["OWNER_DECISION"]), root=root_document(allowedPayloadMediaTypes=[matrix["payloadMediaTypeByClass"]["OWNER_DECISION"]]), taxonomy_matrix_bytes=trust.canonical_bytes(matrix), evaluation_time=T10)  # noqa: E702
    policy = [{"transitionRowId": "R05", "evidenceRole": "TECHNICAL_VERIFICATION", "freshnessClass": "IMMUTABLE", "maxCaptureDelaySeconds": 1, "maxObservationAgeSeconds": 1, "maxEnvelopeLifetimeSeconds": 1200}]; subject = {"schemaVersion": "ActiveProgramRouteV1", "transitionRowId": "R05", "sourceState": "OWNER_APPROVED", "operation": "VERIFY_PREDECESSOR", "targetState": "PREDECESSOR_VERIFIED"}  # noqa: E702
    immutable = future("validate_subject_phase", envelope=subject_envelope(typedReferenceType="APPROVED_HASH", evidenceRole="TECHNICAL_VERIFICATION", producerTrustClass="CONTENT_EVALUATOR", freshnessClass="IMMUTABLE", subject=subject, observedAt=T00, capturedAt=T00, notBefore=T00), root=root_document(allowedTransitionRows=["R05"], allowedEvidenceRoles=["TECHNICAL_VERIFICATION"], freshnessPolicies=policy), taxonomy_matrix_bytes=taxonomy_matrix(), evaluation_time=T10)
    assert cast(Any, exact).valid is False and cast(Any, mime).valid is False and cast(Any, immutable).valid is True
def test_malformed_contract_artifact_is_typed() -> None:
    root_name = "docs/governance/schemas/authority-producer-trust-root-v1.schema.json"; envelope_name = "docs/governance/schemas/authority-evidence-envelope-v1.schema.json"; reconstruction_name = "docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json"; matrix_name = "docs/governance/authority-evidence-trust-state-matrices-v1.json"; mutations = [(root_name, ("root",), "not-an-object"), (matrix_name, ("typedReferenceTypes",), 1), (matrix_name, ("reverseTransitionRequirements",), 1), (matrix_name, ("keyLifecycle",), [1] * 5), (matrix_name, ("payloadMediaTypeByClass",), {str(n): [] for n in range(12)}), (envelope_name, ("contractVersion",), {}), (envelope_name, ("root", "required"), [{}]), (reconstruction_name, ("root", "conditions"), 1)]; results = []  # noqa: E702
    child = (prior_tests.ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_bytes()
    for name, path, value in mutations:
        artifacts = prior_tests.contract_artifacts(); malformed = json.loads(artifacts[name]); target = malformed if len(path) == 1 else cast(dict[str, object], malformed[path[0]]); target[path[-1]] = value; artifacts[name] = trust.canonical_bytes(malformed)  # noqa: E702
        try: results.append(future("validate_artifact_set", artifacts=artifacts, child_a_matrix_bytes=child))  # noqa: E701
        except Exception as exc: pytest.fail(f"RAW_EXCEPTION:{path}:{type(exc).__name__}")  # noqa: BLE001, E701
    for value in (1, None, [{"legalTransitions": 1}], [{"legalTransitions": [{"id": {}}]}]):
        malformed_child = json.loads(child); malformed_child["matrices"] = value  # noqa: E702
        try: results.append(future("validate_artifact_set", artifacts=prior_tests.contract_artifacts(), child_a_matrix_bytes=trust.canonical_bytes(malformed_child)))  # noqa: E701
        except Exception as exc: pytest.fail(f"RAW_EXCEPTION:child:{type(exc).__name__}")  # noqa: BLE001, E701
    assert all(cast(Any, result).valid is False for result in results)
def test_noncanonical_manifest_and_invalid_replay_fail_before_trust(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, blobs = reconstruction_bundle(b"fixture-only payload"); inputs, state = complete_arguments(); monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: trust.SignatureResult(True, ())); noncanonical = json.dumps(json.loads(manifest), indent=2).encode() + b"\n"; rebuilt = future("reconstruct_retained_evidence", manifest_bytes=noncanonical, retained_blobs=blobs, evaluation_time=T10, trust_inputs=inputs)  # noqa: E702
    envelope = cast(Mapping[str, object], state["envelope"]); variants = [trust.canonical_bytes(dict(envelope, signature=token * 128)) for token in ("1", "2")]; replay = future("validate_evidence_replay_set", envelope_documents=variants)  # noqa: E702
    assert cast(Any, rebuilt).valid is False and cast(Any, replay).historical_verdict is trust.Verdict.INVALID
def test_payload_bound_precedes_hash_and_findings_are_order_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    arguments, _ = complete_arguments(); module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction"); original = hashlib.sha256; oversized: list[int] = []; crypto: list[int] = []; monkeypatch.setattr(trust, "verify_ed25519_signature", lambda **_: (crypto.__iadd__([1]), trust.SignatureResult(True, ()))[1])  # noqa: E702
    def observed_hash(raw: bytes = b"") -> Any:
        if len(raw) > trust.PAYLOAD_MAX_BYTES: oversized.append(len(raw))  # noqa: E701
        return original(raw)
    monkeypatch.setattr(module.hashlib, "sha256", observed_hash); oversized_result = future("resolve_complete_evidence", **dict(arguments, payload_bytes=b"x" * (trust.PAYLOAD_MAX_BYTES + 1))); corrupted_payload = b"x" * len(cast(bytes, arguments["payload_bytes"])); corrupt = future("resolve_complete_evidence", **dict(arguments, payload_bytes=corrupted_payload)); corrupt_unavailable = future("resolve_complete_evidence", **dict(arguments, payload_bytes=corrupted_payload, root_documents={})); bad_pins = dict(arguments, acceptance_expected_pin_hash="f" * 64, current_expected_pin_hash="f" * 64); pin_result = future("resolve_complete_evidence", **bad_pins); malformed_root = dict(arguments); root_hash = cast(str, json.loads(cast(bytes, arguments["envelope_bytes"]))["rootContentHash"]); roots = dict(cast(Mapping[str, bytes], arguments["root_documents"])); root = json.loads(roots[root_hash]); root["allowedEvidenceRoles"] = {}; roots[root_hash] = trust.canonical_bytes(root); root_result = future("resolve_complete_evidence", **dict(malformed_root, root_documents=roots)); pre_crypto = len(crypto)  # noqa: E702
    documents = cast(dict[str, bytes], arguments["key_record_documents"]); malformed = {"a" * 64: b"{}", "b" * 64: b'{"schemaVersion":{}}'}; first = trusted_result(monkeypatch, dict(arguments, key_record_documents=dict(documents, **malformed))); second = trusted_result(monkeypatch, dict(arguments, key_record_documents=dict(reversed(list(dict(documents, **malformed).items())))))  # noqa: E702
    assert all(cast(Any, item).valid is False for item in (oversized_result, corrupt, pin_result, root_result)) and not oversized and not pre_crypto and first.current_findings == second.current_findings and cast(Any, corrupt_unavailable).historical_verdict is trust.Verdict.INVALID and "PAYLOAD_HASH_MISMATCH" in codes(corrupt_unavailable)
def test_root_invalidation_boundary_enforces_topology_count_and_order(monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: E704
    prior = root_document(); successor = root_document(rootVersion=99, predecessorRootContentHash=prior["contentHash"], priorRootCompromise={"priorRootContentHash": prior["contentHash"], "invalidatesPriorRootFrom": T00}); documents = {cast(str, prior["contentHash"]): trust.canonical_bytes(prior), cast(str, successor["contentHash"]): trust.canonical_bytes(successor)}; descriptor = pin_descriptor(cast(str, prior["contentHash"]), "CURRENT"); descriptor["rootContentHashes"] = sorted(documents); topology = future("resolve_root_invalidation", root_documents=documents, pin_descriptor=descriptor, expected_pin_set_hash=pin_hash(descriptor), expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER), prior_root_content_hash=prior["contentHash"], evaluation_time=T10); malformed = {"a" * 64: b"{}", "b" * 64: b'{"schemaVersion":{}}'}; malformed_descriptor = pin_descriptor("a" * 64, "CURRENT"); malformed_descriptor["rootContentHashes"] = sorted(malformed); outputs = [cast(Any, future("resolve_root_invalidation", root_documents=value, pin_descriptor=malformed_descriptor, expected_pin_set_hash=pin_hash(malformed_descriptor), expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER), prior_root_content_hash=prior["contentHash"], evaluation_time=T10)).findings for value in (malformed, dict(reversed(list(malformed.items()))))]; module = importlib.import_module("scripts.quality.issue434_authority_evidence_reconstruction"); calls: list[int] = []; root_name = "_validate_closed_root" if hasattr(module, "_validate_closed_root") else "validate_closed_root"; monkeypatch.setattr(module, root_name, lambda **_: (calls.__iadd__([1]), module._result([]))[1]); valid_documents = {cast(str, prior["contentHash"]): trust.canonical_bytes(prior)}; valid_descriptor = pin_descriptor(cast(str, prior["contentHash"]), "CURRENT"); invalid_pin = future("resolve_root_invalidation", root_documents=valid_documents, pin_descriptor=valid_descriptor, expected_pin_set_hash="f" * 64, expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER), prior_root_content_hash=prior["contentHash"], evaluation_time=T10); bounded = future("resolve_root_invalidation", root_documents={f"{n:064x}": b"{}" for n in range(65)}, pin_descriptor=pin_descriptor(cast(str, prior["contentHash"]), "CURRENT"), expected_pin_set_hash="f" * 64, expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER), prior_root_content_hash=prior["contentHash"], evaluation_time=T10); assert cast(Any, topology).structural_invalidation_applies is False and "ROOT_PREDECESSOR_MISMATCH" in codes(topology) and "ROOT_PIN_SET_HASH_MISMATCH" in codes(invalid_pin) and "ROOT_DOCUMENT_LIMIT" in codes(bounded) and not calls and outputs[0] == outputs[1]  # noqa: E702
def test_fixture_case_expectations_execute_governed_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    vector = prior_tests.rfc_vector(); signature_cases = {"RFC_VECTOR": (vector["publicKeyHex"], vector["signatureHex"], bytes.fromhex(vector["messageHex"])), "SIGNATURE_BIT_FLIP": (vector["publicKeyHex"], vector["signatureHex"][:-1] + ("0" if vector["signatureHex"][-1] != "0" else "1"), bytes.fromhex(vector["messageHex"])), "WRONG_PUBLIC_KEY": ("0" * 64, vector["signatureHex"], bytes.fromhex(vector["messageHex"])), "WRONG_MESSAGE": (vector["publicKeyHex"], vector["signatureHex"], b"x")}; actual: dict[str, tuple[str, set[str]]] = {}  # noqa: E702
    for probe, (public, signature, message) in signature_cases.items(): signature_result = trust.verify_ed25519_signature(public_key_hex=public, signature_hex=signature, message=message); actual[probe] = ("VALID" if signature_result.valid else "INVALID", {item.code for item in signature_result.findings})  # noqa: E701, E702
    malformed = {"DUPLICATE_MEMBER": b'{"schemaVersion":"AuthorityEvidenceEnvelopeV1","schemaVersion":"AuthorityEvidenceEnvelopeV1"}', "UNKNOWN_MEMBER": prior_tests.envelope_bytes(unexpected=True), "BOOLEAN_AS_INTEGER": prior_tests.envelope_bytes(payloadByteLength=True), "FLOAT": prior_tests.envelope_bytes(payloadByteLength=1.0), "NUMERIC_STRING": prior_tests.envelope_bytes(payloadByteLength="1"), "NULL_SUBSTITUTION": prior_tests.envelope_bytes(payloadByteLength=None), "NON_ASCII": prior_tests.envelope_bytes(producerId="prod\u00e9"), "MALFORMED_TIME": prior_tests.envelope_bytes(observedAt="2026-08-17"), "INVALID_HEX": prior_tests.envelope_bytes(payloadSha256="NOT-HEX"), "DEPTH_LIMIT": prior_tests.envelope_bytes(unexpectedNested=prior_tests.deeply_nested_value()), "SIZE_LIMIT": prior_tests.envelope_bytes(collectionMethod="a" * trust.RAW_JSON_MAX_BYTES)}  # noqa: E702
    for probe, raw in malformed.items(): malformed_result = cast(trust.Evaluation, prior_tests.evaluate_absent(envelope_bytes=raw, payload_bytes=b"fixture payload")); actual[probe] = (malformed_result.historical_verdict.value, {item.code for item in malformed_result.findings})  # noqa: E701, E702
    absent_cases = {"MISSING_ENVELOPE": prior_tests.evaluate_absent(payload_bytes=b"fixture payload"), "MISSING_PAYLOAD": prior_tests.evaluate_absent(envelope_bytes=prior_tests.envelope_bytes()), "MISSING_ACCEPTANCE_PIN": prior_tests.evaluate_absent(independent_trust=trust.IndependentTrustInputs((), None, ("0" * 64,), "0" * 64, trust.HistoryHead("0" * 64, PRODUCER, 1, "0" * 64), trust.HistoryHead("0" * 64, PRODUCER, 1, "0" * 64))), "MISSING_ACCEPTANCE_HEAD": prior_tests.evaluate_absent(independent_trust=trust.IndependentTrustInputs(("0" * 64,), "0" * 64, ("0" * 64,), "0" * 64, None, trust.HistoryHead("0" * 64, PRODUCER, 1, "0" * 64)))}  # noqa: E702
    for probe, absent_result in absent_cases.items(): evaluation = cast(trust.Evaluation, absent_result); actual[probe] = (evaluation.historical_verdict.value, {item.code for item in evaluation.findings})  # noqa: E701, E702
    arguments, _ = complete_arguments(); arguments["current_expected_pin_hash"] = "f" * 64; pin = trusted_result(monkeypatch, arguments); actual["CURRENT_PIN_MISMATCH"] = (pin.current_verdict.value, codes(pin)); arguments, _ = complete_arguments(); head = cast(trust.HistoryHead, arguments["current_head"]); arguments["current_head"] = trust.HistoryHead(head.root_content_hash, head.producer_id, 99, head.key_record_content_hash); rollback = trusted_result(monkeypatch, arguments); actual["CURRENT_HEAD_ROLLBACK"] = (rollback.current_verdict.value, codes(rollback))  # noqa: E702
    for probe, source in (("FIXTURE_AUTHORITY_CLAIM", "FIXTURE"), ("SIGNATURE_AUTHORITY_CLAIM", "SIGNATURE"), ("CHECK_AUTHORITY_CLAIM", "CHECK")): authority_result = cast(trust.Evaluation, prior_tests.evaluate_absent(claimed_authority_sources=(source,))); actual[probe] = (authority_result.historical_verdict.value, {item.code for item in authority_result.findings})  # noqa: E701, E702
    for case in prior_tests.fixture_cases(): verdict, findings = actual[cast(str, case["probe"])]; assert verdict == case["expectedVerdict"] and set(cast(list[str], case["expectedFindings"])) <= findings  # noqa: E701, E702
