"""Assertion-level RED contract for Issue #434 evidence and producer trust."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

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
