"""Assertion-level RED contract for Issue #434 evidence and producer trust."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import tomllib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

from scripts.quality import issue434_authority_evidence_trust as trust

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tests/fixtures/authority-evidence-trust-v1-cases.json"


def fixture_corpus() -> dict[str, object]:
    return cast(dict[str, object], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def fixture_cases() -> list[dict[str, object]]:
    return cast(list[dict[str, object]], fixture_corpus()["cases"])


def rfc_vector() -> dict[str, str]:
    return cast(dict[str, str], fixture_corpus()["rfc8032Section7_1Vector1"])


def all_member_names(value: object) -> set[str]:
    members: set[str] = set()
    if isinstance(value, dict):
        members.update(str(key) for key in value)
        for item in value.values():
            members.update(all_member_names(item))
    elif isinstance(value, list):
        for item in value:
            members.update(all_member_names(item))
    return members


def empty_trust_inputs() -> trust.IndependentTrustInputs:
    return trust.IndependentTrustInputs(
        acceptance_root_pins=(),
        acceptance_root_pin_set_hash=None,
        current_root_pins=(),
        current_root_pin_set_hash=None,
        acceptance_head=None,
        current_head=None,
    )


def evaluate_absent(
    *,
    envelope_bytes: bytes | None = None,
    payload_bytes: bytes | None = None,
    independent_trust: trust.IndependentTrustInputs | None = None,
    claimed_authority_sources: tuple[str, ...] = (),
) -> trust.Evaluation | trust.NotImplementedResult:
    return trust.evaluate_evidence(
        envelope_bytes=envelope_bytes,
        payload_bytes=payload_bytes,
        root_documents={},
        producer_key_records={},
        independent_trust=independent_trust or empty_trust_inputs(),
        acceptance_time="2026-08-17T00:00:00Z",
        current_time="2026-08-17T00:00:00Z",
        claimed_authority_sources=claimed_authority_sources,
    )


def valid_fixture_envelope(**mutations: object) -> dict[str, object]:
    """Return one schema-shaped, visibly synthetic R01 fixture envelope."""

    envelope: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceEnvelopeV1",
        "repository": "example.invalid/narratwin-authority-evidence-fixtures",
        "programId": "program:fixture-only",
        "generationId": "generation:fixture-only",
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
        "producerId": "producer:fixture-only",
        "rootId": "trust-root:fixture-only",
        "rootContentHash": "2" * 64,
        "signingKeyId": "3" * 64,
        "issuingKeyObjectId": "producer-key:fixture-only",
        "issuingKeyRevision": 1,
        "issuingKeyRecordContentHash": "4" * 64,
        "signatureAlgorithm": "Ed25519",
        "canonicalSignatureProfile": "NarraTwinAuthorityEvidenceSignatureV1",
        "payloadMediaType": (
            "application/vnd.narratwin.authority.content-reference-v1+json"
        ),
        "payloadSha256": "5" * 64,
        "payloadByteLength": 16,
        "observedAt": "2026-08-17T00:00:00Z",
        "capturedAt": "2026-08-17T00:00:01Z",
        "notBefore": "2026-08-17T00:00:00Z",
        "expiresAt": "2026-08-17T00:05:00Z",
        "sourceClass": "FIXTURE",
        "collectionMethod": "SYNTHETIC_PUBLIC_VECTOR",
        "limitations": ["FIXTURE_ONLY"],
        "fixtureOnly": True,
        "signature": "6" * 128,
    }
    envelope.update(mutations)
    return envelope


def envelope_bytes(**mutations: object) -> bytes:
    return json.dumps(
        valid_fixture_envelope(**mutations),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def deeply_nested_value() -> dict[str, object]:
    value: dict[str, object] = {"leaf": 1}
    for index in range(13):
        value = {f"level{index}": value}
    return value


def test_fixture_corpus_is_public_only_non_authoritative_and_complete_for_red() -> None:
    corpus = fixture_corpus()
    cases = fixture_cases()

    assert corpus["schemaVersion"] == "AuthorityEvidenceTrustFixtureCorpusV1"
    assert corpus["fixtureOnly"] is True
    assert corpus["repository"] == "example.invalid/narratwin-authority-evidence-fixtures"
    assert corpus["activation"] == "NONE"
    assert corpus["privateMaterialIncluded"] is False
    prohibited_members = {"privateKey", "privateKeyHex", "secretKey", "secretSeed", "seed"}
    assert not (prohibited_members & all_member_names(corpus))
    assert {cast(str, case["boundary"]) for case in cases} == {
        "B-001",
        "B-004",
        "B-005",
        "B-012",
        "B-015",
    }
    assert len({cast(str, case["id"]) for case in cases}) == len(cases)


def test_cryptography_is_an_exact_direct_development_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = cast(Mapping[str, list[str]], project["dependency-groups"])["dev"]

    assert dev.count("cryptography==50.0.0") == 1
    assert importlib.metadata.version("cryptography") == "50.0.0"


def test_canonical_bytes_are_ascii_stable_and_member_sorted() -> None:
    result = trust.canonical_bytes({"z": True, "a": [1, "ASCII"]})

    assert isinstance(result, bytes), result
    assert result == b'{"a":[1,"ASCII"],"z":true}'


@pytest.mark.parametrize("kind", list(trust.ContentKind))
def test_content_hash_uses_each_exact_closed_domain(kind: trust.ContentKind) -> None:
    value: dict[str, object] = {"schemaVersion": "ExampleV1", "value": "fixture-only"}
    expected = hashlib.sha256(
        kind.value.encode("ascii")
        + b"\0ExampleV1\0"
        + b'{"schemaVersion":"ExampleV1","value":"fixture-only"}'
    ).hexdigest()

    result = trust.content_hash(kind, "ExampleV1", value)

    assert isinstance(result, str), result
    assert result == expected


def test_evidence_signature_input_omits_only_hash_and_signature() -> None:
    envelope: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceEnvelopeV1",
        "contentHash": "0" * 64,
        "signature": "1" * 128,
        "subjectId": "subject:fixture-only",
    }
    expected = (
        b"NARRATWIN-AUTHORITY-EVIDENCE-SIGNATURE-V1\0"
        b"AuthorityEvidenceEnvelopeV1\0"
        b'{"schemaVersion":"AuthorityEvidenceEnvelopeV1",'
        b'"subjectId":"subject:fixture-only"}'
    )

    result = trust.evidence_signature_input(envelope)

    assert isinstance(result, bytes), result
    assert result == expected


def test_rfc8032_section_7_1_public_vector_verifies() -> None:
    vector = rfc_vector()

    result = trust.verify_ed25519_signature(
        public_key_hex=vector["publicKeyHex"],
        signature_hex=vector["signatureHex"],
        message=bytes.fromhex(vector["messageHex"]),
    )

    assert isinstance(result, trust.SignatureResult), result
    assert result.valid is True
    assert result.findings == ()


@pytest.mark.parametrize("mutation", ["signature", "public-key", "message"])
def test_rfc8032_mutations_fail_with_a_typed_finding(mutation: str) -> None:
    vector = rfc_vector()
    public_key = vector["publicKeyHex"]
    signature = vector["signatureHex"]
    message = bytes.fromhex(vector["messageHex"])
    if mutation == "signature":
        signature = ("f" if signature[0] != "f" else "e") + signature[1:]
    elif mutation == "public-key":
        public_key = ("f" if public_key[0] != "f" else "e") + public_key[1:]
    else:
        message = b"wrong-domain"

    result = trust.verify_ed25519_signature(
        public_key_hex=public_key,
        signature_hex=signature,
        message=message,
    )

    assert isinstance(result, trust.SignatureResult), result
    assert result.valid is False
    assert result.findings == (trust.Finding("SIGNATURE_INVALID", "signature"),)


@pytest.mark.parametrize(
    ("public_key_hex", "signature_hex", "message", "expected_finding"),
    [
        (
            None,
            "0" * 128,
            b"",
            trust.Finding("PUBLIC_KEY_FORMAT", "publicKey"),
        ),
        (
            "0" * 64,
            None,
            b"",
            trust.Finding("SIGNATURE_FORMAT", "signature"),
        ),
        (
            "0" * 64,
            "0" * 128,
            None,
            trust.Finding("MESSAGE_TYPE", "message"),
        ),
    ],
    ids=["public-key-runtime-type", "signature-runtime-type", "message-runtime-type"],
)
def test_signature_runtime_type_errors_are_typed_and_never_escape(
    public_key_hex: object,
    signature_hex: object,
    message: object,
    expected_finding: trust.Finding,
) -> None:
    result = trust.verify_ed25519_signature(
        public_key_hex=cast(str, public_key_hex),
        signature_hex=cast(str, signature_hex),
        message=cast(bytes, message),
    )

    assert isinstance(result, trust.SignatureResult), result
    assert result == trust.SignatureResult(False, (expected_finding,))


@pytest.mark.parametrize(
    ("raw", "allowed", "required", "expected_code"),
    [
        (b'{"a":1,"a":1}', frozenset({"a"}), frozenset({"a"}), "DUPLICATE_MEMBER"),
        (b'{"a":1,"b":2}', frozenset({"a"}), frozenset({"a"}), "UNKNOWN_MEMBER"),
    ],
)
def test_closed_json_rejects_duplicate_and_unknown_members(
    raw: bytes,
    allowed: frozenset[str],
    required: frozenset[str],
    expected_code: str,
) -> None:
    try:
        result = trust.parse_closed_json(raw, allowed_members=allowed, required_members=required)
    except trust.AuthorityEvidenceTrustError as exc:
        assert exc.code == expected_code
        assert str(exc) == expected_code
    else:
        if isinstance(result, trust.NotImplementedResult):
            pytest.fail(f"expected typed {expected_code} rejection; got {result.code}")
        pytest.fail(f"expected typed {expected_code} rejection")


def test_missing_envelope_is_unavailable_and_never_passes_b001() -> None:
    result = evaluate_absent(payload_bytes=b"fixture payload")

    assert isinstance(result, trust.Evaluation), result
    assert result.historical_verdict is trust.Verdict.UNAVAILABLE
    assert result.current_verdict is trust.Verdict.UNAVAILABLE
    assert trust.Finding("ENVELOPE_UNAVAILABLE", "envelope") in result.findings
    assert result.activation == "NONE"


def test_malformed_presented_input_precedes_unavailable_b001_b012() -> None:
    result = evaluate_absent(envelope_bytes=b'{"schemaVersion":', payload_bytes=None)

    assert isinstance(result, trust.Evaluation), result
    assert result.historical_verdict is trust.Verdict.INVALID
    assert result.current_verdict is trust.Verdict.INVALID
    assert trust.Finding("MALFORMED_JSON", "envelope") in result.findings
    assert trust.Finding("PAYLOAD_UNAVAILABLE", "payload") in result.findings


def test_absent_independent_pins_and_heads_never_backfill_from_candidates_b004() -> None:
    result = evaluate_absent(envelope_bytes=b"{}", payload_bytes=b"fixture payload")

    assert isinstance(result, trust.Evaluation), result
    codes = {finding.code for finding in result.findings}

    assert result.historical_verdict is not trust.Verdict.VALID
    assert result.current_verdict is not trust.Verdict.VALID
    assert {
        "ACCEPTANCE_ROOT_PIN_REQUIRED",
        "CURRENT_ROOT_PIN_REQUIRED",
        "ACCEPTANCE_HEAD_REQUIRED",
        "CURRENT_HEAD_REQUIRED",
    } <= codes


@pytest.mark.parametrize(
    ("raw", "expected_code"),
    [
        (envelope_bytes(payloadByteLength=True), "WRONG_SCALAR_TYPE"),
        (envelope_bytes(payloadByteLength=1.0), "FLOAT_PROHIBITED"),
        (envelope_bytes(payloadByteLength="1"), "WRONG_SCALAR_TYPE"),
        (envelope_bytes(payloadByteLength=None), "WRONG_SCALAR_TYPE"),
        (envelope_bytes(producerId="prod\u00e9"), "NON_ASCII_STRING"),
        (envelope_bytes(observedAt="2026-08-17"), "TIME_FORMAT"),
        (envelope_bytes(payloadSha256="NOT-HEX"), "HEX_FORMAT"),
        (envelope_bytes(unexpectedNested=deeply_nested_value()), "DEPTH_LIMIT"),
        (
            envelope_bytes(collectionMethod="a" * trust.RAW_JSON_MAX_BYTES),
            "SIZE_LIMIT",
        ),
    ],
    ids=[
        "boolean-as-integer",
        "float",
        "numeric-string",
        "null-substitution",
        "non-ascii",
        "malformed-time",
        "invalid-hex",
        "deeply-nested",
        "oversized",
    ],
)
def test_b012_untrusted_shapes_return_the_exact_bounded_typed_finding(
    raw: bytes,
    expected_code: str,
) -> None:
    first = evaluate_absent(envelope_bytes=raw, payload_bytes=b"fixture payload")
    second = evaluate_absent(envelope_bytes=raw, payload_bytes=b"fixture payload")

    assert isinstance(first, trust.Evaluation), first
    assert isinstance(second, trust.Evaluation), second
    assert first == second
    assert first.historical_verdict is trust.Verdict.INVALID
    assert first.current_verdict is trust.Verdict.INVALID
    assert first.findings
    assert all(len(finding.code) <= 64 for finding in first.findings)
    assert [finding.code for finding in first.findings].count(expected_code) == 1


@pytest.mark.parametrize(
    ("kind", "schema_version", "location", "mapping_name"),
    [
        (
            trust.ContentKind.TRUST_ROOT,
            "AuthorityProducerTrustRootV1",
            "rootDocuments",
            "root_documents",
        ),
        (
            trust.ContentKind.PRODUCER_KEY,
            "AuthorityProducerKeyV1",
            "producerKeyRecords",
            "producer_key_records",
        ),
    ],
    ids=["trust-root", "producer-key"],
)
def test_raw_sha_blob_keys_cannot_substitute_for_domain_content_identity(
    kind: trust.ContentKind,
    schema_version: str,
    location: str,
    mapping_name: str,
) -> None:
    blob = json.dumps(
        {"fixtureOnly": True, "schemaVersion": schema_version},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    raw_sha = hashlib.sha256(blob).hexdigest()
    expected_domain_hash = hashlib.sha256(
        kind.value.encode("ascii") + b"\0" + schema_version.encode("ascii") + b"\0" + blob
    ).hexdigest()
    assert raw_sha != expected_domain_hash

    inputs: dict[str, object] = {
        "envelope_bytes": None,
        "payload_bytes": None,
        "root_documents": {},
        "producer_key_records": {},
        "independent_trust": empty_trust_inputs(),
        "acceptance_time": "2026-08-17T00:00:00Z",
        "current_time": "2026-08-17T00:00:00Z",
    }
    inputs[mapping_name] = {raw_sha: blob}
    result = trust.evaluate_evidence(**cast(Any, inputs))

    assert isinstance(result, trust.Evaluation), result
    assert trust.Finding("BLOB_CONTENT_HASH_MISMATCH", location) in result.findings
    assert result.historical_verdict is trust.Verdict.INVALID
    assert result.current_verdict is trust.Verdict.INVALID


@pytest.mark.parametrize(
    ("field", "forged_value"),
    [("authority_effect", "AUTHORITY"), ("activation", "ACTIVE")],
)
def test_evaluation_nonactivation_fields_are_not_caller_initializable(
    field: str,
    forged_value: str,
) -> None:
    constructor = cast(Any, trust.Evaluation)

    with pytest.raises(TypeError, match=field):
        constructor(
            historical_verdict=trust.Verdict.VALID,
            current_verdict=trust.Verdict.VALID,
            findings=(),
            **{field: forged_value},
        )


def test_content_hash_rejects_argument_and_object_schema_version_mismatch() -> None:
    value: dict[str, object] = {
        "schemaVersion": "AuthorityEvidenceEnvelopeV1",
        "value": "fixture-only",
    }

    with pytest.raises(
        trust.AuthorityEvidenceTrustError,
        match="SCHEMA_VERSION_MISMATCH",
    ) as exc_info:
        trust.content_hash(
            trust.ContentKind.EVIDENCE_OBJECT,
            "AuthorityProducerTrustRootV1",
            value,
        )

    assert exc_info.value.code == "SCHEMA_VERSION_MISMATCH"


@pytest.mark.parametrize("source", ["FIXTURE", "SIGNATURE", "TEST", "CI", "FILE"])
def test_presented_artifacts_have_no_authority_effect_b015(source: str) -> None:
    result = evaluate_absent(claimed_authority_sources=(source,))

    assert isinstance(result, trust.Evaluation), result
    assert result.authority_effect == "NO_AUTHORITY_EFFECT"
    assert result.activation == "NONE"
    assert trust.Finding("NO_AUTHORITY_EFFECT", "authority") in result.findings
    assert result.historical_verdict is not trust.Verdict.VALID
    assert result.current_verdict is not trust.Verdict.VALID


class StructureResult(Protocol):
    findings: tuple[trust.Finding, ...]
    authorization_evaluated: bool
    root_invalidation_applied: bool
    authority_effect: str
    activation: str


ROOT_HASH = "a" * 64
OTHER_ROOT_HASH = "b" * 64
REPOSITORY = "example.invalid/narratwin-authority-evidence-fixtures"
PROGRAM = "program:fixture-only"
GENERATION = "generation:fixture-only"
PRODUCER = "producer:fixture-only"
T00, T09, T10 = "2026-08-17T00:00:00Z", "2026-08-17T00:09:59Z", "2026-08-17T00:10:00Z"
T14, T15 = "2026-08-17T00:14:59Z", "2026-08-17T00:15:00Z"
T19, T20 = "2026-08-17T00:19:59Z", "2026-08-17T00:20:00Z"
T29, T30 = "2026-08-17T00:29:59Z", "2026-08-17T00:30:00Z"


def public_key_id(public_key_hex: str) -> str:
    return hashlib.sha256(
        b"NARRATWIN-AUTHORITY-ED25519-PUBLIC-KEY-V1\0" + bytes.fromhex(public_key_hex)
    ).hexdigest()


def key_record(
    sequence: int,
    *,
    operation: str = "ISSUE_GENESIS",
    previous: Mapping[str, object] | None = None,
    key_object_id: str = "key:a:fixture-only",
    public_key_hex: str = "1" * 64,
    revision: object = 1,
    root_signature: object = "0" * 128,
    predecessor_signature: object = None,
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": "AuthorityProducerKeyV1",
        "repository": REPOSITORY,
        "programId": PROGRAM,
        "generationId": GENERATION,
        "rootContentHash": ROOT_HASH,
        "producerId": PRODUCER,
        "keyObjectId": key_object_id,
        "keyId": public_key_id(public_key_hex),
        "publicKeyHex": public_key_hex,
        "revision": revision,
        "predecessorContentHash": (
            previous["contentHash"] if previous and operation != "ROTATE" else None
        ),
        "historySequence": sequence,
        "historyPredecessorContentHash": previous["contentHash"] if previous else None,
        "rotationPredecessor": (
            {
                "keyObjectId": previous["keyObjectId"],
                "revision": previous["revision"],
                "contentHash": previous["contentHash"],
            }
            if previous and operation == "ROTATE"
            else None
        ),
        "operation": operation,
        "activationTime": T10 if operation == "ROTATE" else T00,
        "retiredAt": T20 if operation == "RETIRE" else None,
        "revokedAt": T30 if operation == "REVOKE" else None,
        "invalidatesFrom": T15 if operation == "REVOKE" else None,
        "signatureAlgorithm": "Ed25519",
        "rootAuthorizationSignature": root_signature,
        "predecessorAuthorizationSignature": predecessor_signature,
        "fixtureOnly": True,
    }
    value.update(changes)
    value["contentHash"] = trust.content_hash(
        trust.ContentKind.PRODUCER_KEY, "AuthorityProducerKeyV1", value
    )
    return value


def key_rows() -> dict[str, dict[str, object]]:
    k01 = key_record(1)
    k02 = key_record(
        2,
        operation="ROTATE",
        previous=k01,
        key_object_id="key:b:fixture-only",
        public_key_hex="2" * 64,
        predecessor_signature="0" * 128,
    )
    k03 = key_record(3, operation="RETIRE", previous=k02, key_object_id=cast(str, k02["keyObjectId"]), public_key_hex=cast(str, k02["publicKeyHex"]), revision=2, activationTime=T10)
    k04 = key_record(3, operation="REVOKE", previous=k02, key_object_id=cast(str, k02["keyObjectId"]), public_key_hex=cast(str, k02["publicKeyHex"]), revision=2, activationTime=T10)
    k05 = key_record(4, operation="REVOKE", previous=k03, key_object_id=cast(str, k03["keyObjectId"]), public_key_hex=cast(str, k03["publicKeyHex"]), revision=3, activationTime=T10, retiredAt=T20)
    return {"K01": k01, "K02": k02, "K03": k03, "K04": k04, "K05": k05}


def call_future(name: str, **kwargs: object) -> object:
    function = cast(Callable[..., object] | None, getattr(trust, name, None))
    if not callable(function):
        pytest.fail(f"{name} is NOT_IMPLEMENTED")
    return function(**kwargs)


def inspect_structure(
    records: tuple[Mapping[str, object], ...],
    *,
    expected_head: trust.HistoryHead | None,
    capture_time: str = T14,
    evaluation_time: str = T29,
    root_pins: tuple[str, ...] = (ROOT_HASH,),
    root_invalidations: tuple[Mapping[str, object], ...] = (),
) -> StructureResult:
    result = call_future(
        "inspect_key_history_structure",
        records=records,
        expected_head=expected_head,
        repository=REPOSITORY,
        program_id=PROGRAM,
        generation_id=GENERATION,
        producer_id=PRODUCER,
        root_content_hash=ROOT_HASH,
        capture_time=capture_time,
        evaluation_time=evaluation_time,
        independently_pinned_roots=root_pins,
        root_invalidations=root_invalidations,
    )
    required = ("findings", "authorization_evaluated", "root_invalidation_applied", "authority_effect", "activation")
    assert all(hasattr(result, name) for name in required)
    return cast(StructureResult, result)


def head(record: Mapping[str, object]) -> trust.HistoryHead:
    return trust.HistoryHead(
        cast(str, record["rootContentHash"]),
        cast(str, record["producerId"]),
        cast(int, record["historySequence"]),
        cast(str, record["contentHash"]),
    )


def assert_structure(result: StructureResult, expected_code: str | None) -> None:
    codes = [finding.code for finding in result.findings]
    if expected_code is None:
        assert codes == []
    else:
        assert expected_code in codes
    assert result.authorization_evaluated is False
    assert result.authority_effect == "NO_AUTHORITY_EFFECT"
    assert result.activation == "NONE"


@pytest.mark.parametrize(
    ("row", "capture", "evaluation", "expected"),
    [
        ("K02", T09, T19, "KEY_NOT_YET_ACTIVE"),
        ("K02", T10, T19, None),
        ("K02", T14, T19, None),
        ("K03", T19, T29, None),
        ("K03", T20, T29, "KEY_RETIRED"),
        ("K03", "2026-08-17T00:20:01Z", T29, "KEY_RETIRED"),
        ("K04", T15, T29, None),
        ("K04", T14, T30, None),
        ("K04", T15, T30, "KEY_REVOKED"),
        ("K04", "2026-08-17T00:15:01Z", "2026-08-17T00:30:01Z", "KEY_REVOKED"),
        ("K05", T14, "2026-08-17T00:30:01Z", None),
    ],
)
def test_k02_k03_k04_k05_half_open_structure_b002_b006_b007(
    row: str, capture: str, evaluation: str, expected: str | None
) -> None:
    rows = key_rows()
    records = {
        "K02": (rows["K01"], rows["K02"]),
        "K03": (rows["K01"], rows["K02"], rows["K03"]),
        "K04": (rows["K01"], rows["K02"], rows["K04"]),
        "K05": (rows["K01"], rows["K02"], rows["K03"], rows["K05"]),
    }[row]
    result = inspect_structure(records, expected_head=head(records[-1]), capture_time=capture, evaluation_time=evaluation)
    assert_structure(result, expected)


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("missing-predecessor-bytes", "HISTORY_PREDECESSOR_UNAVAILABLE"),
        ("sequence-jump", "HISTORY_SEQUENCE_JUMP"),
        ("fork", "HISTORY_FORK"),
        ("duplicate-key-id", "KEY_ID_MISMATCH"),
        ("duplicate-key-bytes", "KEY_ID_MISMATCH"),
        ("rotation-uses-same-key", "ROTATION_PREDECESSOR_RELATION"),
        ("same-key-missing-predecessor", "SAME_KEY_PREDECESSOR_REQUIRED"),
        ("malformed-fork", "WRONG_SCALAR_TYPE"),
        ("suppressed-suffix", "CURRENT_HEAD_ROLLBACK"),
        ("missing-head", "CURRENT_HEAD_REQUIRED"),
        ("over-64", "HISTORY_RECORD_LIMIT"),
        ("unknown-operation", "UNKNOWN_KEY_OPERATION"),
        ("revision-downgrade", "KEY_REVISION_DOWNGRADE"),
    ],
)
def test_graph_head_and_bound_failures_are_typed_b008(scenario: str, expected: str) -> None:
    rows = key_rows()
    records: tuple[Mapping[str, object], ...] = (rows["K01"], rows["K02"])
    expected_head: trust.HistoryHead | None = head(rows["K02"])
    same_key = {
        "key_object_id": cast(str, rows["K02"]["keyObjectId"]),
        "public_key_hex": cast(str, rows["K02"]["publicKeyHex"]),
    }
    if scenario == "missing-predecessor-bytes":
        records = (rows["K02"],)
    elif scenario == "sequence-jump":
        records = (rows["K01"], key_record(3, operation="ROTATE", previous=rows["K01"], key_object_id="key:c", public_key_hex="3" * 64))
        expected_head = head(records[-1])
    elif scenario in {"fork", "duplicate-key-id", "duplicate-key-bytes"}:
        other = key_record(2, operation="ROTATE", previous=rows["K01"], key_object_id="key:c", public_key_hex=(cast(str, rows["K02"]["publicKeyHex"]) if scenario == "duplicate-key-bytes" else "3" * 64), keyId=(rows["K02"]["keyId"] if scenario == "duplicate-key-id" else public_key_id("3" * 64)))
        records += (other,)
    elif scenario == "rotation-uses-same-key":
        records = (rows["K01"], key_record(2, operation="ROTATE", previous=rows["K01"], predecessorContentHash=rows["K01"]["contentHash"]))
        expected_head = head(records[-1])
    elif scenario == "same-key-missing-predecessor":
        records += (
            key_record(3, operation="RETIRE", previous=rows["K02"],
                       revision=2, predecessorContentHash=None, **same_key),
        )
        expected_head = head(records[-1])
    elif scenario == "malformed-fork":
        records += (key_record(2, operation="ROTATE", previous=rows["K01"], revision=True),)
    elif scenario == "suppressed-suffix":
        records += (rows["K03"],)
    elif scenario == "missing-head":
        expected_head = None
    elif scenario == "unknown-operation":
        records += (key_record(3, operation="REISSUE", previous=rows["K02"]),)
        expected_head = head(records[-1])
    elif scenario == "revision-downgrade":
        records += (
            key_record(3, operation="RETIRE", previous=rows["K02"],
                       revision=1, **same_key),
        )
        expected_head = head(records[-1])
    else:
        records = tuple(key_record(index + 1) for index in range(65))
    result = inspect_structure(records, expected_head=expected_head)
    if scenario in {"duplicate-key-id", "duplicate-key-bytes"}:
        assert {"DUPLICATE_KEY_ID", "DUPLICATE_PUBLIC_KEY", "CONFLICTING"}.isdisjoint(finding_codes(result))
    assert_structure(result, expected)


def test_cycle_mutated_after_hash_fails_integrity_before_graph_classification_b008() -> None:
    rows = key_rows()
    cycled = dict(rows["K02"])
    cycled["historyPredecessorContentHash"] = cycled["contentHash"]
    assert_structure(
        inspect_structure((rows["K01"], cycled), expected_head=head(cycled)),
        "CONTENT_HASH_MISMATCH",
    )


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("rootContentHash", OTHER_ROOT_HASH, "ROOT_SCOPE_MISMATCH"),
        ("producerId", "producer:other", "PRODUCER_SCOPE_MISMATCH"),
        ("repository", "example.invalid/other", "REPOSITORY_SCOPE_MISMATCH"),
        ("programId", "program:other", "PROGRAM_SCOPE_MISMATCH"),
        ("generationId", "generation:other", "GENERATION_SCOPE_MISMATCH"),
    ],
)
def test_scope_replay_is_typed_b009(field: str, replacement: str, expected: str) -> None:
    rows = key_rows()
    replay = key_record(2, operation="ROTATE", previous=rows["K01"], **{field: replacement})
    assert_structure(inspect_structure((rows["K01"], replay), expected_head=head(replay)), expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("root-missing", "ROOT_AUTHORIZATION_REQUIRED"),
        ("root-bad", "ROOT_AUTHORIZATION_INVALID"),
        ("root-wrong-domain", "ROOT_AUTHORIZATION_INVALID"),
        ("root-wrong-key", "ROOT_AUTHORIZATION_INVALID"),
        ("k02-predecessor-missing", "PREDECESSOR_AUTHORIZATION_REQUIRED"),
        ("k02-predecessor-bad", "PREDECESSOR_AUTHORIZATION_INVALID"),
        ("wrong-algorithm", "SIGNATURE_ALGORITHM"),
        ("wrong-key-id", "KEY_ID_MISMATCH"),
    ],
)
def test_key_authorization_substitutions_are_invalid_b005_b008(case: str, expected: str) -> None:
    # Positive cryptographic lineage waits for paths 4-8 to freeze canonical signed bytes.
    rows = key_rows()
    record = dict(rows["K02"] if case.startswith("k02") else rows["K01"])
    vector = rfc_vector()
    if case == "root-missing":
        record["rootAuthorizationSignature"] = None
    elif case == "root-wrong-domain":
        record["rootAuthorizationSignature"] = vector["signatureHex"]
    elif case == "root-wrong-key":
        record["rootAuthorizationSignature"] = vector["signatureHex"]
    elif case == "wrong-algorithm":
        record["signatureAlgorithm"] = "Ed448"
    elif case == "wrong-key-id":
        record["keyId"] = "f" * 64
    elif case == "k02-predecessor-missing":
        record["predecessorAuthorizationSignature"] = None
    else:
        signature_field = "predecessorAuthorizationSignature" if case == "k02-predecessor-bad" else "rootAuthorizationSignature"
        record[signature_field] = "f" * 128
    record.pop("contentHash", None)
    record["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, "AuthorityProducerKeyV1", record)
    # This low-level primitive proves only signatures against caller-supplied
    # public keys; it cannot establish identity, trust, authority, or activation.
    result = call_future(
        "verify_key_record_authorization_signatures",
        record=record,
        root_public_key_hex=("e" * 64 if case == "root-wrong-key" else vector["publicKeyHex"]),
        predecessor_public_key_hex=vector["publicKeyHex"],
    )
    assert isinstance(result, trust.SignatureResult)
    assert result.valid is False
    assert expected in {finding.code for finding in result.findings}


def test_unpinned_naked_successor_invalidation_has_no_effect_b007() -> None:
    # Positive successor invalidation waits for the independently pinned root schema freeze.
    rows = key_rows()
    declaration = {
        "successorRootContentHash": OTHER_ROOT_HASH,
        "priorRootContentHash": ROOT_HASH,
        "invalidatesPriorRootFrom": T20,
    }
    result = inspect_structure(
        (rows["K01"], rows["K02"]),
        expected_head=head(rows["K02"]),
        evaluation_time=T30,
        root_invalidations=(declaration,),
    )
    assert_structure(result, "ROOT_SUCCESSOR_PIN_REQUIRED")
    assert result.root_invalidation_applied is False


def test_exact_duplicate_is_idempotent_b009() -> None:
    rows = key_rows()
    records = (rows["K01"], rows["K02"])
    once = inspect_structure(records, expected_head=head(rows["K02"]))
    twice = inspect_structure(records + (rows["K02"],), expected_head=head(rows["K02"]))
    malformed = dict(rows["K02"], activationTime=None); rejected = inspect_structure(records + (malformed,), expected_head=head(rows["K02"]))  # noqa: E702
    assert twice == once
    assert "WRONG_SCALAR_TYPE" in finding_codes(rejected) and "DUPLICATE_CONTENT_HASH" not in finding_codes(rejected)


# Bounded reset RED: these pure interfaces freeze the trust inputs before GREEN.
def slice3_contract() -> dict[str, object]:
    return cast(dict[str, object], fixture_corpus()["slice3PublicContract"])


RESET_CANDIDATE_HASHES = {"docs/governance/AUTHORITY_EVIDENCE_AND_TRUST_V1.md": "e01e60c7281200e55d9f2d586e8082f02548ff7d97f35e4e4e657858d9c7c264", "docs/governance/authority-evidence-trust-state-matrices-v1.json": "31682fb423cb9a26ab14d0e6ea6e39b0848df23b46b2da3e296583ec82a7f473", "docs/governance/schemas/authority-evidence-envelope-v1.schema.json": "4e699c1223c20790b5dbcfb461fa72978448474a7de348aa0267e2befe334585", "docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json": "7951450388b8e78650a380e852ac95bd9114b67cdaae24c73122f365273ad65b", "docs/governance/schemas/authority-producer-key-v1.schema.json": "90c47cf64be8815fbbfe8a3e074929d767f71696ee8bfdeb63ebf09da30f4ba6", "docs/governance/schemas/authority-producer-trust-root-v1.schema.json": "a3d9f10fb09e4e1b26d4845c4c5953391be50959a826d2fbc323faa46d1ee329"}


class ResetResult(Protocol):
    findings: tuple[trust.Finding, ...]
    authority_effect: str
    activation: str


class RootInvalidationResult(ResetResult, Protocol):
    structural_invalidation_applies: bool


class IssuingResult(ResetResult, Protocol):
    issuing_key_eligible: bool


class TrustResult(ResetResult, Protocol):
    trusted: bool


def finding_codes(result: object) -> set[str]:
    return {item.code for item in cast(ResetResult, result).findings}


def assert_no_authority(result: object) -> None:
    typed = cast(ResetResult, result)
    assert typed.authority_effect == "NO_AUTHORITY_EFFECT"
    assert typed.activation == "NONE"


def contract_artifacts() -> dict[str, bytes]:
    if not callable(getattr(trust, "validate_contract_artifacts", None)):
        pytest.fail("validate_contract_artifacts is NOT_IMPLEMENTED")
    paths = cast(list[str], slice3_contract()["artifactPaths"])
    return {path: (ROOT / path).read_bytes() for path in paths}


def pin_hash(descriptor: Mapping[str, object]) -> str:
    canonical = json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(
        b"NARRATWIN-AUTHORITY-ROOT-PIN-SET-V1\0AuthorityRootPinSetV1\0" + canonical
    ).hexdigest()


def pin_descriptor_for(*hashes: object, phase: str = "ACCEPTANCE") -> dict[str, object]:
    descriptor = dict(cast(dict[str, object], slice3_contract()["rootPinDescriptor"]))
    descriptor.update({"evaluationPhase": phase, "rootContentHashes": sorted(cast(tuple[str, ...], hashes))})
    return descriptor


def valid_fixture_root(**changes: object) -> dict[str, object]:
    value = cast(dict[str, object], json.loads(json.dumps(slice3_contract()["trustRootTemplate"])))
    value.update(changes)
    value["contentHash"] = trust.content_hash(
        trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", value
    )
    return value


def test_phase_scoped_root_pin_descriptor_exact_known_vector() -> None:
    contract = slice3_contract()
    descriptor = cast(dict[str, object], contract["rootPinDescriptor"])
    assert len(descriptor) == 7
    assert pin_hash(descriptor) == contract["rootPinSetHash"]
    assert call_future("root_pin_set_hash", descriptor=descriptor) == contract["rootPinSetHash"]


@pytest.mark.parametrize(
    ("changes", "expected_hash", "source", "expected"),
    [
        (None, "FIXTURE", "INDEPENDENT", {"ROOT_PIN_DESCRIPTOR_REQUIRED"}),
        ({}, None, "INDEPENDENT", {"ROOT_PIN_SET_HASH_REQUIRED"}),
        ({"repository": "other.invalid/repository"}, "FIXTURE", "INDEPENDENT", {"ROOT_PIN_SCOPE_MISMATCH"}),
        ({"evaluationPhase": "CURRENT"}, "FIXTURE", "INDEPENDENT", {"ROOT_PIN_PHASE_MISMATCH"}),
        ({"rootContentHashes": ["2" * 64, "2" * 64]}, "REHASH", "INDEPENDENT", {"ROOT_PIN_DUPLICATE"}),
        ({"rootContentHashes": ["f" * 64, "2" * 64]}, "REHASH", "INDEPENDENT", {"ROOT_PIN_ORDER"}),
        ({}, "f" * 64, "INDEPENDENT", {"ROOT_PIN_SET_HASH_MISMATCH"}),
        ({}, None, "CANDIDATE", {"ROOT_PIN_SET_HASH_REQUIRED", "ROOT_PIN_SOURCE_PROHIBITED"}),
    ],
)
def test_root_pin_absence_scope_order_hash_and_source_fail_closed(
    changes: dict[str, object] | None, expected_hash: str | None, source: str, expected: set[str]
) -> None:
    descriptor = None if changes is None else dict(cast(dict[str, object], slice3_contract()["rootPinDescriptor"]))
    if descriptor is not None:
        descriptor.update(cast(dict[str, object], changes))
    if expected_hash == "FIXTURE":
        expected_hash = cast(str, slice3_contract()["rootPinSetHash"])
    elif expected_hash == "REHASH":
        expected_hash = pin_hash(cast(Mapping[str, object], descriptor))
    result = call_future(
        "validate_root_pin_set",
        descriptor=descriptor,
        expected_hash=expected_hash,
        expected_phase="ACCEPTANCE",
        expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER),
        source=source,
    )
    assert expected <= finding_codes(result)
    assert_no_authority(result)


def test_acceptance_current_pin_rollback_is_invalid() -> None:
    acceptance = dict(cast(dict[str, object], slice3_contract()["rootPinDescriptor"]))
    acceptance["rootContentHashes"] = ["2" * 64, "3" * 64]
    current = dict(acceptance)
    current.update({"evaluationPhase": "CURRENT", "rootContentHashes": ["2" * 64]})
    result = call_future(
        "validate_root_pin_transition",
        acceptance_descriptor=acceptance,
        acceptance_expected_hash=pin_hash(acceptance),
        current_descriptor=current,
        current_expected_hash=pin_hash(current),
    )
    assert "ROOT_PIN_ROLLBACK" in finding_codes(result)
    assert_no_authority(result)


@pytest.mark.parametrize(("when", "expected"), [(T09, "ROOT_NOT_YET_VALID"), (T10, None), ("2026-08-18T00:00:00Z", "ROOT_EXPIRED")])
def test_root_validity_is_half_open(when: str, expected: str | None) -> None:
    root = valid_fixture_root(validFrom=T10)
    descriptor = pin_descriptor_for(root["contentHash"])
    result = call_future("validate_trust_root", root_bytes=trust.canonical_bytes(root), expected_root_hash=root["contentHash"], pin_descriptor=descriptor, expected_pin_set_hash=pin_hash(descriptor), evaluation_time=when)
    assert (expected in finding_codes(result)) if expected else not ({"ROOT_NOT_YET_VALID", "ROOT_EXPIRED"} & finding_codes(result))
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("root-bytes", "ROOT_CONTENT_HASH_MISMATCH"),
        ("genesis", "GENESIS_KEY_BINDING_MISMATCH"),
        ("root-auth", "ROOT_AUTHORIZATION_KEY_ID_MISMATCH"),
    ],
)
def test_exact_root_bytes_genesis_and_root_authorization(case: str, expected: str) -> None:
    root = valid_fixture_root()
    expected_hash = cast(str, root["contentHash"])
    if case == "root-bytes":
        root["fixtureOnly"] = False
    else:
        member = "genesisCaptureKey" if case == "genesis" else "rootAuthorizationKey"
        binding = dict(cast(dict[str, object], root[member]))
        binding["keyId"] = "f" * 64
        root[member] = binding
        root["contentHash"] = trust.content_hash(
            trust.ContentKind.TRUST_ROOT, "AuthorityProducerTrustRootV1", root
        )
        expected_hash = cast(str, root["contentHash"])
    result = call_future(
        "validate_trust_root",
        root_bytes=trust.canonical_bytes(root),
        expected_root_hash=expected_hash,
        pin_descriptor=pin_descriptor_for(expected_hash),
        expected_pin_set_hash=pin_hash(pin_descriptor_for(expected_hash)),
        evaluation_time=T10,
    )
    assert expected in finding_codes(result)
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("when", "invalidated"), [(T19, False), (T20, True), ("2026-08-17T00:20:01Z", True)]
)
def test_pinned_successor_root_invalidation_before_at_after(
    when: str, invalidated: bool
) -> None:
    prior = valid_fixture_root()
    successor = valid_fixture_root(
        rootId="root:successor-fixture-only",
        rootVersion=2,
        predecessorRootContentHash=prior["contentHash"],
        priorRootCompromise={"priorRootContentHash": prior["contentHash"], "invalidatesPriorRootFrom": T20},
    )
    hashes = sorted((cast(str, prior["contentHash"]), cast(str, successor["contentHash"])))
    descriptor = dict(cast(dict[str, object], slice3_contract()["rootPinDescriptor"]))
    descriptor.update({"evaluationPhase": "CURRENT", "rootContentHashes": hashes})
    result = call_future(
        "resolve_root_invalidation_structure",
        root_documents={hashes[0]: trust.canonical_bytes(prior if prior["contentHash"] == hashes[0] else successor), hashes[1]: trust.canonical_bytes(successor if successor["contentHash"] == hashes[1] else prior)},
        pin_descriptor=descriptor,
        expected_pin_set_hash=pin_hash(descriptor),
        expected_scope=(REPOSITORY, PROGRAM, GENERATION, PRODUCER),
        prior_root_content_hash=prior["contentHash"],
        evaluation_time=when,
    )
    assert cast(RootInvalidationResult, result).structural_invalidation_applies is invalidated
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("row", "changes", "expected"),
    [
        ("K01", {"revision": 2}, "GENESIS_RELATION"),
        ("K01", {"retiredAt": T20}, "GENESIS_RELATION"),
        ("K02", {"rotationRevision": 99}, "ROTATION_PREDECESSOR_RELATION"),
        ("K02", {"predecessorAuthorizationSignature": None}, "PREDECESSOR_AUTHORIZATION_REQUIRED"),
        ("K03", {"retiredAt": None}, "RETIREMENT_REQUIRED"),
        ("K03", {"activationTime": T00}, "KEY_ACTIVATION_CHANGED"),
        ("K03", {"predecessorAuthorizationSignature": "0" * 128}, "PREDECESSOR_AUTHORIZATION_PROHIBITED"),
        ("K04", {"retiredAt": T20}, "REVOKE_SOURCE_STATE"),
        ("K04", {"invalidatesFrom": None}, "REVOCATION_BOUNDARY_REQUIRED"),
        ("K05", {"retiredAt": T10}, "RETIRED_STATE_NOT_PRESERVED"),
        ("K05", {"predecessorContentHash": "0" * 64}, "REVOKE_SOURCE_STATE"),
        ("K05", {"rootAuthorizationSignature": None}, "ROOT_AUTHORIZATION_REQUIRED"),
    ],
)
def test_k01_k05_exact_condition_and_carry_rules(
    row: str, changes: dict[str, object], expected: str
) -> None:
    rows = key_rows()
    record = dict(rows[row])
    if "rotationRevision" in changes:
        rotation = dict(cast(dict[str, object], record["rotationPredecessor"]))
        rotation["revision"] = changes.pop("rotationRevision")
        record["rotationPredecessor"] = rotation
    record.update(changes)
    record["contentHash"] = trust.content_hash(
        trust.ContentKind.PRODUCER_KEY, "AuthorityProducerKeyV1", record
    )
    prefix = {"K01": (), "K02": (rows["K01"],), "K03": (rows["K01"], rows["K02"]), "K04": (rows["K01"], rows["K02"]), "K05": (rows["K01"], rows["K02"], rows["K03"])}[row]
    assert expected in finding_codes(
        inspect_structure(prefix + (record,), expected_head=head(record))
    )


@pytest.mark.parametrize(("operation", "capture", "eligible"), [("ROTATE", T14, True), ("RETIRE", T19, True), ("RETIRE", T20, False), ("REVOKE", T14, True), ("REVOKE", T15, False)])
def test_issuing_key_overlap_retirement_and_revocation_use_raw_history(
    operation: str, capture: str, eligible: bool
) -> None:
    rows = key_rows()
    records: tuple[Mapping[str, object], ...] = (rows["K01"], rows["K02"])
    if operation != "ROTATE":
        event = key_record(3, operation=operation, previous=rows["K02"], key_object_id=cast(str, rows["K01"]["keyObjectId"]), public_key_hex=cast(str, rows["K01"]["publicKeyHex"]), revision=2, predecessorContentHash=rows["K01"]["contentHash"], activationTime=T00)
        records += (event,)
    result = call_future(
        "resolve_issuing_key_structure",
        records=records,
        expected_head=head(records[-1]),
        issuing_key=(rows["K01"]["keyObjectId"], rows["K01"]["keyId"], 1, rows["K01"]["contentHash"]),
        capture_time=capture,
    )
    assert cast(IssuingResult, result).issuing_key_eligible is eligible
    assert_no_authority(result)


@pytest.mark.parametrize(("field", "expected"), [(name, "PUBLIC_KEY_FORMAT" if name == "publicKeyHex" else "WRONG_SCALAR_TYPE") for name in ["contentHash", "historySequence", "revision", "keyId", "keyObjectId", "publicKeyHex", "signatureAlgorithm", "fixtureOnly", "rootAuthorizationSignature", "predecessorAuthorizationSignature", "activationTime", "historyPredecessorContentHash", "predecessorContentHash", "rotationPredecessor.contentHash", "rotationPredecessor.keyObjectId", "rotationPredecessor.revision", "expectedHead.root_content_hash", "expectedHead.producer_id", "expectedHead.history_sequence", "expectedHead.key_record_content_hash"]])
def test_every_graph_indexed_wrong_type_is_isolated(field: str, expected: str) -> None:
    rows = key_rows()
    malformed = dict(rows["K02"])
    if field.startswith("rotationPredecessor"):
        rotation = dict(cast(dict[str, object], malformed["rotationPredecessor"]))
        rotation[field.rsplit(".", 1)[1]] = {}
        malformed["rotationPredecessor"] = rotation
    elif field == "activationTime":
        malformed[field] = None
    elif not field.startswith("expectedHead"):
        malformed[field] = {}
    if field != "contentHash":
        malformed["contentHash"] = trust.content_hash(trust.ContentKind.PRODUCER_KEY, "AuthorityProducerKeyV1", malformed)
    expected_head = trust.HistoryHead(ROOT_HASH, PRODUCER, 2, cast(str, malformed["contentHash"]))
    if field == "contentHash":
        expected_head = head(rows["K02"])
    if field.startswith("expectedHead"):
        values: list[object] = [ROOT_HASH, PRODUCER, 2, rows["K02"]["contentHash"]]
        values[["root_content_hash", "producer_id", "history_sequence", "key_record_content_hash"].index(field.split(".")[1])] = {}
        expected_head = trust.HistoryHead(*cast(tuple[str, str, int, str], tuple(values)))
    try:
        result = inspect_structure((rows["K01"], malformed), expected_head=expected_head)
    except Exception as exc:  # noqa: BLE001 - RED converts any leak to assertion failure.
        pytest.fail(f"RAW_EXCEPTION:{type(exc).__name__}")
    assert {"HISTORY_FORK", "DUPLICATE_KEY_ID", "DUPLICATE_PUBLIC_KEY", "CONFLICTING"}.isdisjoint(finding_codes(result))
    assert expected in finding_codes(result)


def test_schema_collection_bound_precedes_item_work(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []; original = trust.canonical_bytes; monkeypatch.setattr(trust, "canonical_bytes", lambda value: (calls.__iadd__([value]), original(value))[1]); schema = {"$defs": {}, "root": {"type": "array", "minItems": 1, "maxItems": 64, "unique": True, "items": {"type": "string"}}}; result = trust.validate_closed_schema_value([str(index) for index in range(65)], schema)  # noqa: E702
    assert any(item.code == "COLLECTION_LIMIT" for item in result) and not calls

@pytest.mark.parametrize(("value", "schema", "expected"), [("ok", {"$defs": {}, "root": {"type": "string", "rogueKeyword": True}}, "SCHEMA_DESCRIPTOR_INVALID"), ({str(i): i for i in range(65)}, {"$defs": {}, "root": {"type": "object", "closed": True, "required": [], "properties": {}}}, "COLLECTION_LIMIT"), ([["bad"] * 64 for _ in range(64)], {"$defs": {}, "root": {"type": "array", "maxItems": 64, "items": {"type": "array", "maxItems": 64, "items": {"type": "boolean"}}}}, 256)])
def test_schema_executor_closes_descriptors_members_and_result_work(value: object, schema: Mapping[str, object], expected: str | int) -> None:
    findings = trust.validate_closed_schema_value(value, schema)
    assert len(findings) == expected if isinstance(expected, int) else expected in {item.code for item in findings}


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("missing-schema", "CONTRACT_ARTIFACT_MISSING"),
        ("corrupt-matrix", "CONTRACT_MATRIX_INVALID"),
        ("taxonomy-44", "TAXONOMY_CARDINALITY"),
        ("reverse-32", "REVERSE_ROW_CARDINALITY"),
        ("mime-12", "PAYLOAD_MIME_CARDINALITY"),
        ("coordinated", "CHILD_A_TAXONOMY_MISMATCH"),
    ],
)
def test_schema_matrix_deletion_corruption_and_coordinated_drift(
    mutation: str, expected: str
) -> None:
    artifacts = contract_artifacts()
    paths = cast(list[str], slice3_contract()["artifactPaths"])
    matrix_path = paths[1]
    if mutation == "missing-schema":
        artifacts.pop(paths[2], None)
    elif mutation == "corrupt-matrix":
        artifacts[matrix_path] = b"{"
    else:
        matrix: dict[str, Any]
        if artifacts[matrix_path] != b"{}":
            matrix = cast(dict[str, Any], json.loads(artifacts[matrix_path]))
        else:
            matrix = {
                "typedReferenceTypes": [f"REF_{index:02d}" for index in range(44)],
                "typedReferenceTaxonomy": [],
                "reverseTransitionRequirements": {f"R{index:02d}": [] for index in range(32)},
                "payloadMediaTypeByClass": {f"CLASS_{index:02d}": f"application/vnd.narratwin.fixture-{index:02d}+json" for index in range(12)},
            }
        if mutation == "taxonomy-44":
            matrix["typedReferenceTypes"].append("EXTRA_REFERENCE")
        elif mutation == "reverse-32":
            matrix["reverseTransitionRequirements"].pop(next(iter(matrix["reverseTransitionRequirements"])))
        elif mutation == "mime-12":
            matrix["payloadMediaTypeByClass"].pop(next(iter(matrix["payloadMediaTypeByClass"])))
        else:
            removed = matrix["typedReferenceTypes"].pop()
            for references in matrix["reverseTransitionRequirements"].values():
                if removed in references:
                    references.remove(removed)
        artifacts[matrix_path] = json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode()
    result = call_future(
        "validate_contract_artifacts",
        artifacts=artifacts,
        child_a_matrix_bytes=(ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_bytes(),
    )
    assert expected in finding_codes(result)
    assert_no_authority(result)


def replace_json(value: object, old: str, new: str) -> object:
    if isinstance(value, dict):
        return {key: replace_json(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_json(item, old, new) for item in value]
    return new if value == old else value


def test_reset_candidate_artifact_identities_compare_supplied_bytes() -> None:
    fixture_hashes = cast(dict[str, str], slice3_contract()["resetCandidateArtifactSha256"])
    assert fixture_hashes == RESET_CANDIDATE_HASHES
    synthetic = {path: f"synthetic-mutated:{path}".encode() for path in RESET_CANDIDATE_HASHES}
    result = call_future(
        "validate_contract_artifacts",
        artifacts=synthetic,
        expected_artifact_hashes=RESET_CANDIDATE_HASHES,
        child_a_matrix_bytes=(ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_bytes(),
    )
    assert "ARTIFACT_IDENTITY_MISMATCH" in finding_codes(result)
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [("nested", "NESTED_CLOSURE_REQUIRED"), ("required", "REQUIRED_SURFACE_MISMATCH"), ("pin-domain", "ROOT_PIN_DOMAIN_MISMATCH"), ("k-row", "K02_CONTRACT_MISMATCH"), ("mime-duplicate", "PAYLOAD_MIME_BIJECTION"), ("coordinated", "COORDINATED_CONTRACT_MUTATION"), ("predecessor", "ROOT_PREDECESSOR_COMPROMISE_DISTINCT"), ("recovery", "ROOT_RECOVERY_SEMANTICS_REQUIRED"), ("revocation", "ROOT_REVOCATION_SEMANTICS_REQUIRED"), ("k04-k05", "K04_K05_DISTINCT"), ("statuses", "RECONSTRUCTION_STATUS_SET"), ("retained-set", "RETAINED_EXACT_SET_REQUIRED"), ("historical-current", "HISTORICAL_CURRENT_SEPARATION_REQUIRED")],
)
def test_nested_schema_pin_domain_k_rows_and_mime_are_executable(
    mutation: str, expected: str
) -> None:
    artifacts = contract_artifacts()
    paths = cast(list[str], slice3_contract()["artifactPaths"])
    matrix = cast(dict[str, Any], json.loads(artifacts[paths[1]]))
    if mutation in {"nested", "required"}:
        envelope = cast(dict[str, Any], json.loads(artifacts[paths[2]]))
        if mutation == "nested":
            envelope["$defs"]["subject"].pop("closed")
        else:
            envelope["root"]["required"].remove("signature")
        artifacts[paths[2]] = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    elif mutation == "pin-domain":
        matrix["contentDomains"]["AuthorityRootPinSetV1"] = "WRONG"
    elif mutation == "k-row":
        matrix["keyLifecycle"][1]["predecessorEligibility"] = "IMPLICIT_RETIREMENT"
    elif mutation in {"predecessor", "recovery", "revocation"}:
        root = cast(dict[str, Any], json.loads(artifacts[paths[5]]))
        field = {"predecessor": "priorRootCompromise", "recovery": "recoverySemantics", "revocation": "revocationSemantics"}[mutation]
        root["root"]["properties"].pop(field)
        root["root"]["required"].remove(field)
        artifacts[paths[5]] = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    elif mutation == "k04-k05":
        matrix["keyLifecycle"][4]["source"] = "ACTIVE"
    elif mutation in {"statuses", "retained-set", "historical-current"}:
        reconstruction = cast(dict[str, Any], json.loads(artifacts[paths[3]]))
        if mutation == "statuses":
            reconstruction["root"]["properties"]["reconstructionStatus"]["enum"] = ["VALID", "INVALID", "CONFLICTING", "UNAVAILABLE"]
        elif mutation == "retained-set":
            reconstruction["root"]["conditions"] = [item for item in reconstruction["root"]["conditions"] if "exact set" not in item]
        else:
            reconstruction["root"]["required"].remove("currentVerdict")
        artifacts[paths[3]] = json.dumps(reconstruction, sort_keys=True, separators=(",", ":")).encode()
    else:
        old = matrix["payloadMediaTypeByClass"]["CONTENT_REFERENCE"]
        new = matrix["payloadMediaTypeByClass"]["CHECK_SET"] if mutation == "mime-duplicate" else "application/vnd.narratwin.authority.alias-v1+json"
        matrix["payloadMediaTypeByClass"]["CONTENT_REFERENCE"] = new
        if mutation == "coordinated":
            for path in paths[2:]:
                artifacts[path] = json.dumps(replace_json(json.loads(artifacts[path]), old, new), sort_keys=True, separators=(",", ":")).encode()
    artifacts[paths[1]] = json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode()
    result = call_future("validate_contract_artifacts", artifacts=artifacts, child_a_matrix_bytes=(ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_bytes())
    assert expected in finding_codes(result)
    assert_no_authority(result)


def test_valid_signature_alone_cannot_create_validated_key_trust() -> None:
    vector = rfc_vector()
    signature = trust.verify_ed25519_signature(
        public_key_hex=vector["publicKeyHex"],
        signature_hex=vector["signatureHex"],
        message=bytes.fromhex(vector["messageHex"]),
    )
    assert signature.valid is True
    root = valid_fixture_root()
    rows = key_rows()
    descriptor = dict(cast(dict[str, object], slice3_contract()["rootPinDescriptor"]))
    descriptor["rootContentHashes"] = [root["contentHash"]]
    result = call_future(
        "resolve_evidence_key_trust",
        envelope_bytes=envelope_bytes(signature=vector["signatureHex"]),
        root_documents={root["contentHash"]: trust.canonical_bytes(root)},
        key_record_documents={row["contentHash"]: trust.canonical_bytes(row) for row in rows.values()},
        acceptance_pin_descriptor=descriptor,
        acceptance_expected_pin_hash=pin_hash(descriptor),
        current_pin_descriptor={**descriptor, "evaluationPhase": "CURRENT"},
        current_expected_pin_hash=pin_hash({**descriptor, "evaluationPhase": "CURRENT"}),
        acceptance_head=head(rows["K02"]),
        current_head=head(rows["K05"]),
        acceptance_time=T19,
        current_time=T30,
    )
    assert {"EVIDENCE_SIGNATURE_INVALID", "ROOT_AUTHORIZATION_INVALID"} <= finding_codes(result)
    assert cast(TrustResult, result).trusted is False
    assert_no_authority(result)
