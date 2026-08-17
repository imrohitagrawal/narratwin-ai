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
    k03 = key_record(3, operation="RETIRE", previous=k02, key_object_id=cast(str, k02["keyObjectId"]), public_key_hex=cast(str, k02["publicKeyHex"]), revision=2)
    k04 = key_record(3, operation="REVOKE", previous=k02, key_object_id=cast(str, k02["keyObjectId"]), public_key_hex=cast(str, k02["publicKeyHex"]), revision=2)
    k05 = key_record(4, operation="REVOKE", previous=k03, key_object_id=cast(str, k03["keyObjectId"]), public_key_hex=cast(str, k03["publicKeyHex"]), revision=3)
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
        ("duplicate-key-id", "DUPLICATE_KEY_ID"),
        ("duplicate-key-bytes", "DUPLICATE_PUBLIC_KEY"),
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
    assert_structure(inspect_structure(records, expected_head=expected_head), expected)


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
    assert twice == once
