"""RED contract for Issue #431 Child A routing and fail-closed fixture inventory."""

from __future__ import annotations

import json
import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.quality import check_stage8_docs as stage8
from scripts.quality import issue431_authority_core as authority


ROOT = Path(__file__).resolve().parents[2]
BRANCH = "cut1-process-431-authority-core-schemas-state-matrices"
PATHS = {
    "docs/governance/preflights/issue-431.json",
    "docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md",
    "docs/governance/schemas/master-program-authority-decision-v1.schema.json",
    "docs/governance/schemas/cut1-authority-manifest-v1.schema.json",
    "docs/governance/schemas/active-program-route-v1.schema.json",
    "docs/governance/authority-core-state-matrices-v1.json",
    "tests/fixtures/authority-core-v1-cases.json",
    "scripts/quality/issue431_authority_core.py",
    "tests/unit/test_issue431_authority_core.py",
    "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/ADR/0061-core-authority-schemas-state-matrices.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
PROHIBITED = [
    "ACCEPT_AUTHORITY_FROM_CI",
    "ACCEPT_AUTHORITY_FROM_COMMENT",
    "ACCEPT_AUTHORITY_FROM_FILE",
    "ACCEPT_AUTHORITY_FROM_FIXTURE",
    "ACCEPT_AUTHORITY_FROM_ISSUE",
    "ACCEPT_AUTHORITY_FROM_TEST",
    "ACTIVATE_AUTHORITY",
    "AUDIT_SERVICE",
    "CAS_STORAGE",
    "CREDENTIAL_USE",
    "DEPLOYMENT",
    "EVIDENCE_CAPTURE",
    "EXTERNAL_EGRESS",
    "GITHUB_ACQUISITION",
    "HISTORICAL_RECONCILIATION",
    "INFRASTRUCTURE",
    "INTEGRATED_KERNEL",
    "KEY_MANAGEMENT",
    "MEDIA_GENERATION",
    "PRODUCTION_OPERATION",
    "PROVIDER_CALL",
    "PUBLICATION",
    "RELEASE",
    "RUNTIME_SERVICE",
    "SPENDING",
]


def reference(kind: str, subject: str) -> dict[str, str]:
    return {
        "referenceType": kind,
        "schemaVersion": "ContentAddressedReferenceV1",
        "sha256": "1" * 64,
        "subject": subject,
    }


def authority_object(schema: str) -> dict[str, object]:
    common: dict[str, object] = {
        "contentHash": "0" * 64,
        "generationId": "generation:fixture-only",
        "lifecycleState": "DRAFT" if schema == "ActiveProgramRouteV1" else "PROPOSED",
        "objectId": {
            "MasterProgramAuthorityDecisionV1": "decision:fixture-only",
            "Cut1AuthorityManifestV1": "manifest:fixture-only",
            "ActiveProgramRouteV1": "route:fixture-only",
        }[schema],
        "predecessorContentHash": None,
        "programId": "narratwin-cut1",
        "prohibitedCapabilities": PROHIBITED,
        "repository": "github.com/imrohitagrawal/narratwin-ai",
        "revision": 1,
        "schemaVersion": schema,
        "transition": None,
        "validity": {
            "expiresAt": "2026-09-15T00:00:00Z",
            "notBefore": "2026-08-15T00:00:00Z",
            "revocationReference": None,
            "revokedAt": None,
        },
    }
    if schema == "MasterProgramAuthorityDecisionV1":
        common.update(
            decisionAction="SELECT_MANIFEST",
            priorDecision=None,
            selectedManifest=reference("MANIFEST", "manifest:fixture-only"),
            sourceProposal=reference("PROPOSAL", "proposal:fixture-only"),
        )
    elif schema == "Cut1AuthorityManifestV1":
        common.update(
            authorityValues={
                name: reference("POLICY", f"{name.lower()}:fixture-only")
                for name in (
                    "canonicalNarration",
                    "downstreamOrderPolicy",
                    "finalRenderPolicy",
                    "ownerAuthoritySource",
                    "presenterSelection",
                    "providerPolicy",
                    "rendererPolicy",
                    "revalidationPolicy",
                    "spendPolicy",
                    "supersededSourceSet",
                )
            },
            decisionBacklink=reference("DECISION", "decision:fixture-only"),
            sourceProposal=reference("PROPOSAL", "proposal:fixture-only"),
        )
    else:
        common.update(
            allowedPaths=["docs/example.invalid"],
            baseSha="2" * 40,
            branch="example-invalid-authority-route",
            childIssue=431,
            controllerIssue=426,
            decision=reference("DECISION", "decision:fixture-only"),
            executionWindow={
                "approvedAt": "2026-08-15T00:00:00Z",
                "expired": False,
                "expiresAt": "2026-09-15T00:00:00Z",
            },
            maxChargedLines=4000,
            maxPathCount=16,
            parentIssue=426,
            predecessorMergeSha="3" * 40,
            pullRequest=None,
            reviewerRoles=["OWNER", "PRINCIPAL_ARCHITECT", "PRINCIPAL_TEST_ENGINEER", "NON_AUTHOR"],
            selectedManifest=reference("MANIFEST", "manifest:fixture-only"),
            targetBranch="main",
            testCommands=["make stage8-quality"],
        )
    unsigned = dict(common)
    del unsigned["contentHash"]
    domain = b"NARRATWIN-AUTHORITY-V1\0" + schema.encode("ascii") + b"\0"
    common["contentHash"] = hashlib.sha256(domain + authority.canonical_bytes(unsigned)).hexdigest()
    return common


def test_fixture_corpus_is_explicitly_non_authoritative_and_adversarial() -> None:
    corpus = json.loads(
        (ROOT / "tests/fixtures/authority-core-v1-cases.json").read_text(encoding="utf-8")
    )

    assert corpus["schemaVersion"] == "AuthorityCoreFixtureCorpusV1"
    assert corpus["fixtureOnly"] is True
    assert corpus["repository"].endswith(".invalid/narratwin-authority-fixtures")
    assert corpus["activation"] == "NONE"
    assert {case["classification"] for case in corpus["cases"]} == {
        "positive",
        "negative",
        "adversarial",
    }
    assert len({case["id"] for case in corpus["cases"]}) == len(corpus["cases"])


def test_child_a_route_is_exactly_registered() -> None:
    assert stage8.PROCESS_BRANCH_ALLOWED_FILES[BRANCH] == PATHS


def test_child_a_branch_is_stage8_eligible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: BRANCH)
    failures: list[str] = []

    stage8.check_stage_marker_and_branch(failures)

    assert failures == []


def test_canonical_bytes_are_ascii_stable_and_member_sorted() -> None:
    assert authority.canonical_bytes({"z": True, "a": [1, "ASCII"]}) == (
        b'{"a":[1,"ASCII"],"z":true}'
    )


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"value": 1.0}, "FLOAT_PROHIBITED"),
        ({"value": float("nan")}, "NON_FINITE_NUMBER"),
        ({"value": float("inf")}, "NON_FINITE_NUMBER"),
        ({"value": "caf\u00e9"}, "NON_ASCII_STRING"),
        ({"value": [0] * 129}, "COLLECTION_LIMIT"),
    ],
)
def test_canonical_bytes_fail_closed(value: object, code: str) -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.canonical_bytes(value)

    assert caught.value.code == code


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"\xff", "INVALID_UTF8"),
        (b'{"a":1,"a":2}', "DUPLICATE_MEMBER"),
        (b'{"a":', "MALFORMED_JSON"),
        (b'{"value":NaN}', "NON_FINITE_NUMBER"),
        (b'{"value":1.0}', "FLOAT_PROHIBITED"),
        (b' {"a":1}', "NONCANONICAL_BYTES"),
        (b"[" * 13 + b"]" * 13, "DEPTH_LIMIT"),
        (b'"' + b"a" * 131_073 + b'"', "SIZE_LIMIT"),
    ],
)
def test_parser_rejects_malformed_or_noncanonical_bytes(data: bytes, code: str) -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(data, "MasterProgramAuthorityDecisionV1")

    assert caught.value.code == code


def test_parser_rejects_an_unsupported_future_schema_before_semantic_use() -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(b"{}", "MasterProgramAuthorityDecisionV2")

    assert caught.value.code == "UNSUPPORTED_VERSION"


@pytest.mark.parametrize("schema", sorted(authority.SUPPORTED_SCHEMAS))
def test_closed_schema_accepts_one_fixture_only_blueprint(schema: str) -> None:
    value = authority_object(schema)

    assert authority.validate_authority_bytes(authority.canonical_bytes(value), schema) == value


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.update(extra="closed"), "UNKNOWN_MEMBER"),
        (lambda value: value.update(revision=True), "WRONG_SCALAR_TYPE"),
        (lambda value: value.update(repository="example.invalid/wrong"), "REPOSITORY_MISMATCH"),
        (lambda value: value.update(programId="wrong"), "PROGRAM_MISMATCH"),
        (lambda value: value.update(generationId="wrong"), "GENERATION_MISMATCH"),
        (lambda value: value.update(contentHash="f" * 64), "CONTENT_HASH_MISMATCH"),
    ],
)
def test_closed_schema_rejects_identity_type_closure_and_hash_mutations(
    mutation: Callable[[dict[str, object]], object], code: str
) -> None:
    value = authority_object("MasterProgramAuthorityDecisionV1")
    mutation(value)

    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(
            authority.canonical_bytes(value),
            "MasterProgramAuthorityDecisionV1",
        )

    assert caught.value.code == code
