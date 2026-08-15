"""RED contract for Issue #431 Child A routing and fail-closed fixture inventory."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from copy import deepcopy
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
    "scripts/quality/issue427_architecture_reset.py",
    "tests/unit/test_issue427_architecture_reset.py",
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


def test_content_hash_uses_the_exact_owner_approved_domain() -> None:
    value = authority_object("MasterProgramAuthorityDecisionV1")
    unsigned = dict(value)
    unsigned.pop("contentHash")
    expected = hashlib.sha256(
        b"NARRATWIN-AUTHORITY-OBJECT-V1\0"
        + b"MasterProgramAuthorityDecisionV1\0"
        + authority.canonical_bytes(unsigned)
    ).hexdigest()

    assert authority.content_hash(value) == expected


def test_canonical_bytes_reject_a_string_above_2048_utf8_bytes() -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.canonical_bytes({"value": "a" * 2049})

    assert caught.value.code == "STRING_LIMIT"


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


DECISION_STATES = [
    "PROPOSED",
    "REVIEWED",
    "OWNER_APPROVED",
    "MERGED",
    "ACCEPTED_CURRENT",
    "REJECTED",
    "SUPERSEDED",
    "REVOKED",
    "EXPIRED",
]
DECISION_OPERATIONS = [
    "REVIEW",
    "REJECT",
    "OWNER_APPROVE",
    "MERGE",
    "ACCEPT_CURRENT",
    "SUPERSEDE",
    "REVOKE",
    "EXPIRE",
]
DECISION_EDGES = [
    ("D01", "PROPOSED", "REVIEW", "REVIEWED"),
    ("D02", "PROPOSED", "REJECT", "REJECTED"),
    ("D03", "REVIEWED", "OWNER_APPROVE", "OWNER_APPROVED"),
    ("D04", "REVIEWED", "REJECT", "REJECTED"),
    ("D05", "OWNER_APPROVED", "MERGE", "MERGED"),
    ("D06", "OWNER_APPROVED", "REJECT", "REJECTED"),
    ("D07", "MERGED", "ACCEPT_CURRENT", "ACCEPTED_CURRENT"),
    ("D08", "MERGED", "REJECT", "REJECTED"),
    ("D09", "ACCEPTED_CURRENT", "SUPERSEDE", "SUPERSEDED"),
    ("D10", "ACCEPTED_CURRENT", "REVOKE", "REVOKED"),
    ("D11", "ACCEPTED_CURRENT", "EXPIRE", "EXPIRED"),
]
ROUTE_STATES = [
    "DRAFT",
    "REVIEWED",
    "OWNER_APPROVED",
    "PREDECESSOR_VERIFIED",
    "ACTIVE",
    "MERGED",
    "CLOSED",
    "REJECTED",
    "SUPERSEDED",
    "EXECUTION_EXPIRED",
]
ROUTE_OPERATIONS = [
    "REVIEW",
    "REJECT",
    "OWNER_APPROVE",
    "VERIFY_PREDECESSOR",
    "ACTIVATE",
    "MERGE",
    "CLOSE",
    "SUPERSEDE",
    "EXPIRE",
]
ROUTE_EDGES = [
    ("R01", "DRAFT", "REVIEW", "REVIEWED"),
    ("R02", "DRAFT", "REJECT", "REJECTED"),
    ("R03", "REVIEWED", "OWNER_APPROVE", "OWNER_APPROVED"),
    ("R04", "REVIEWED", "REJECT", "REJECTED"),
    ("R05", "OWNER_APPROVED", "VERIFY_PREDECESSOR", "PREDECESSOR_VERIFIED"),
    ("R06", "OWNER_APPROVED", "REJECT", "REJECTED"),
    ("R07", "PREDECESSOR_VERIFIED", "ACTIVATE", "ACTIVE"),
    ("R08", "PREDECESSOR_VERIFIED", "REJECT", "REJECTED"),
    ("R09", "ACTIVE", "MERGE", "MERGED"),
    ("R10", "MERGED", "CLOSE", "CLOSED"),
    ("R11", "DRAFT", "SUPERSEDE", "SUPERSEDED"),
    ("R12", "REVIEWED", "SUPERSEDE", "SUPERSEDED"),
    ("R13", "OWNER_APPROVED", "SUPERSEDE", "SUPERSEDED"),
    ("R14", "PREDECESSOR_VERIFIED", "SUPERSEDE", "SUPERSEDED"),
    ("R15", "ACTIVE", "SUPERSEDE", "SUPERSEDED"),
    ("R16", "DRAFT", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R17", "REVIEWED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R18", "OWNER_APPROVED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R19", "PREDECESSOR_VERIFIED", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R20", "ACTIVE", "EXPIRE", "EXECUTION_EXPIRED"),
    ("R21", "EXECUTION_EXPIRED", "CLOSE", "CLOSED"),
]

EXACT_ACTORS = {
    "D01": "INDEPENDENT_REVIEWER",
    "D02": "REPOSITORY_OWNER",
    "D03": "REPOSITORY_OWNER",
    "D04": "REPOSITORY_OWNER",
    "D05": "MERGE_COORDINATOR",
    "D06": "REPOSITORY_OWNER",
    "D07": "AUTHORITY_ACCEPTOR",
    "D08": "REPOSITORY_OWNER",
    "D09": "AUTHORITY_ACCEPTOR",
    "D10": "REPOSITORY_OWNER",
    "D11": "EXPIRY_EVALUATOR",
    "R01": "INDEPENDENT_REVIEWER",
    "R02": "REPOSITORY_OWNER",
    "R03": "REPOSITORY_OWNER",
    "R04": "REPOSITORY_OWNER",
    "R05": "PREDECESSOR_VERIFIER",
    "R06": "REPOSITORY_OWNER",
    "R07": "ROUTE_ACTIVATOR",
    "R08": "REPOSITORY_OWNER",
    "R09": "MERGE_COORDINATOR",
    "R10": "CLOSEOUT_COORDINATOR",
    "R11": "REPOSITORY_OWNER",
    "R12": "REPOSITORY_OWNER",
    "R13": "REPOSITORY_OWNER",
    "R14": "REPOSITORY_OWNER",
    "R15": "REPOSITORY_OWNER",
    "R16": "EXPIRY_EVALUATOR",
    "R17": "EXPIRY_EVALUATOR",
    "R18": "EXPIRY_EVALUATOR",
    "R19": "EXPIRY_EVALUATOR",
    "R20": "EXPIRY_EVALUATOR",
    "R21": "CLOSEOUT_COORDINATOR",
}


def transition_row(edge: tuple[str, str, str, str]) -> dict[str, object]:
    row_id, source, operation, target = edge
    actor = {
        "REVIEW": "ELIGIBLE_NON_AUTHOR_REVIEWER",
        "OWNER_APPROVE": "OWNER",
        "REJECT": "OWNER",
        "MERGE": "MERGE_COORDINATOR",
        "ACCEPT_CURRENT": "AUTHORITY_EVALUATOR",
        "SUPERSEDE": "OWNER",
        "REVOKE": "OWNER",
        "EXPIRE": "AUTHORITY_EVALUATOR",
        "VERIFY_PREDECESSOR": "AUTHORITY_EVALUATOR",
        "ACTIVATE": "OWNER",
        "CLOSE": "ADMINISTRATIVE_CLOSER",
    }[operation]
    return {
        "actorClass": actor,
        "effect": f"EFFECT_{row_id}_{target}",
        "id": row_id,
        "idempotency": "IDEMPOTENT_SAME_BYTES",
        "immutability": "HASH_LINKED_SUCCESSOR_ONLY",
        "legal": True,
        "operation": operation,
        "prohibitedSubstitutes": ["ISSUE", "COMMENT", "FILE", "FIXTURE", "TEST", "CI"],
        "recoveryClassification": (
            "ADMINISTRATIVE_CLOSEOUT" if operation == "CLOSE" else "CREATE_HASH_LINKED_SUCCESSOR"
        ),
        "rejectionBehavior": "NO_MUTATION_TYPED_ERROR",
        "requiredGuards": [f"GUARD_{row_id}_TYPED_REFERENCES"],
        "requiredTypedReferences": ["ContentAddressedReferenceV1"],
        "sourceState": source,
        "targetState": target,
    }


def matrix(
    matrix_id: str,
    states: list[str],
    operations: list[str],
    edges: list[tuple[str, str, str, str]],
) -> dict[str, object]:
    grid = {state: {operation: "ILLEGAL" for operation in operations} for state in states}
    for row_id, source, operation, _ in edges:
        grid[source][operation] = row_id
    return {
        "grid": grid,
        "id": matrix_id,
        "illegalEffect": "NO_MUTATION_TYPED_ERROR",
        "illegalRecovery": "CORRECT_AND_RETRY_OR_CREATE_SUCCESSOR",
        "legalTransitions": [transition_row(edge) for edge in edges],
        "operations": operations,
        "states": states,
    }


def matrix_document() -> dict[str, object]:
    return {
        "activation": "NONE",
        "evaluationOutcomes": ["UNVERIFIED", "CONFLICTING"],
        "matrices": [
            matrix(
                "DecisionManifestLifecycleV1", DECISION_STATES, DECISION_OPERATIONS, DECISION_EDGES
            ),
            matrix("ActiveProgramRouteLifecycleV1", ROUTE_STATES, ROUTE_OPERATIONS, ROUTE_EDGES),
        ],
        "schemaVersion": "AuthorityCoreStateMatricesV1",
    }


def test_state_matrices_are_complete_closed_and_exact() -> None:
    assert authority.matrix_findings(matrix_document()) == []


def test_persisted_matrix_uses_exact_approved_actor_classes_and_typed_guards() -> None:
    document = json.loads(
        (ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_text(
            encoding="utf-8"
        )
    )
    rows = {
        row["id"]: row
        for matrix_item in document["matrices"]
        for row in matrix_item["legalTransitions"]
    }

    assert {row_id: row["actorClass"] for row_id, row in rows.items()} == EXACT_ACTORS
    assert rows["D07"]["requiredTypedReferences"] == [
        "MERGE_REFERENCE",
        "MERGED_MAIN_CHECK",
        "ISSUE_DISPOSITION",
        "VALIDITY_OBSERVATION",
        "DECISION_MANIFEST_LINKS",
    ]
    assert rows["R07"]["requiredTypedReferences"] == [
        "ACCEPTED_DECISION",
        "ACCEPTED_MANIFEST",
        "PREDECESSOR_VERIFICATION",
        "ROUTE_BOUNDARIES",
        "EXECUTION_DEADLINE_OBSERVATION",
    ]


@pytest.mark.parametrize(
    ("mutator", "finding"),
    [
        (lambda doc: doc["matrices"][0]["grid"]["PROPOSED"].pop("REVIEW"), "incomplete"),
        (
            lambda doc: doc["matrices"][0]["legalTransitions"].append(
                deepcopy(doc["matrices"][0]["legalTransitions"][0])
            ),
            "duplicate",
        ),
        (lambda doc: doc["matrices"][0]["legalTransitions"][0].update(sourceState="*"), "wildcard"),
        (lambda doc: doc["matrices"][0]["legalTransitions"][0].pop("actorClass"), "actor"),
        (lambda doc: doc["matrices"][0]["legalTransitions"][0].update(requiredGuards=[]), "guard"),
        (lambda doc: doc["matrices"][0]["legalTransitions"][0].update(effect=""), "effect"),
        (
            lambda doc: doc["matrices"][0]["legalTransitions"][0].update(recoveryClassification=""),
            "recovery",
        ),
        (lambda doc: doc["matrices"][0]["states"].append("UNVERIFIED"), "evaluation"),
        (
            lambda doc: doc["matrices"][1]["grid"]["EXECUTION_EXPIRED"].update(ACTIVATE="R07"),
            "illegal",
        ),
    ],
)
def test_state_matrix_mutations_fail_closed(
    mutator: Callable[[dict[str, object]], object], finding: str
) -> None:
    document = matrix_document()
    mutator(document)

    assert any(finding in item.lower() for item in authority.matrix_findings(document))


def successor(predecessor: dict[str, object], edge: tuple[str, str, str, str]) -> dict[str, object]:
    row = transition_row(edge)
    value = deepcopy(predecessor)
    revision = predecessor["revision"]
    assert type(revision) is int
    value["revision"] = revision + 1
    value["predecessorContentHash"] = predecessor["contentHash"]
    value["lifecycleState"] = row["targetState"]
    value["transition"] = {
        "actorClass": row["actorClass"],
        "effectId": row["effect"],
        "guardReferences": [reference("GUARD", f"guard:{str(row['id']).lower()}")],
        "idempotency": row["idempotency"],
        "operation": row["operation"],
        "prohibitedSubstitutes": row["prohibitedSubstitutes"],
        "recoveryClass": row["recoveryClassification"],
        "rejectionBehavior": row["rejectionBehavior"],
        "sourceState": row["sourceState"],
        "targetState": row["targetState"],
    }
    if (
        value["schemaVersion"] == "ActiveProgramRouteV1"
        and row["targetState"] == "EXECUTION_EXPIRED"
    ):
        value["executionWindow"]["expired"] = True  # type: ignore[index]
    value["contentHash"] = authority.content_hash(value)
    return value


def test_hash_linked_successor_lineage_is_immutable_and_transition_bound() -> None:
    genesis = authority_object("MasterProgramAuthorityDecisionV1")
    reviewed = successor(genesis, DECISION_EDGES[0])

    assert authority.lineage_findings([genesis, reviewed]) == []


def test_hash_linked_successor_cannot_mutate_stable_payload_even_with_a_valid_hash() -> None:
    genesis = authority_object("MasterProgramAuthorityDecisionV1")
    reviewed = successor(genesis, DECISION_EDGES[0])
    reviewed["sourceProposal"] = reference("PROPOSAL", "proposal:mutated")
    reviewed["contentHash"] = authority.content_hash(reviewed)

    assert any(
        "immutable payload" in item.lower()
        for item in authority.lineage_findings([genesis, reviewed])
    )


@pytest.mark.parametrize(
    ("mutator", "finding"),
    [
        (lambda first, second: second.update(predecessorContentHash="f" * 64), "unlinked"),
        (lambda first, second: second.update(objectId="decision:different"), "identity"),
        (lambda first, second: second.update(revision=3), "revision"),
        (lambda first, second: second.update(lifecycleState="ACCEPTED_CURRENT"), "illegal"),
        (
            lambda first, second: second.update(predecessorContentHash=second["contentHash"]),
            "cyclic",
        ),
        (
            lambda first, second: second["sourceProposal"].update(subject="proposal:mutated"),
            "content hash",
        ),
    ],
)
def test_lineage_mutations_fail_closed(
    mutator: Callable[[dict[str, object], dict[str, object]], object], finding: str
) -> None:
    genesis = authority_object("MasterProgramAuthorityDecisionV1")
    reviewed = successor(genesis, DECISION_EDGES[0])
    mutator(genesis, reviewed)

    assert any(finding in item.lower() for item in authority.lineage_findings([genesis, reviewed]))


def test_two_incompatible_successors_are_a_fork_and_identity_collision() -> None:
    genesis = authority_object("MasterProgramAuthorityDecisionV1")
    reviewed = successor(genesis, DECISION_EDGES[0])
    rejected = successor(genesis, DECISION_EDGES[1])

    findings = authority.lineage_findings([genesis, reviewed, rejected])

    assert any("fork" in item.lower() for item in findings)
    assert any("identity" in item.lower() for item in findings)


def test_execution_expiry_allows_closeout_but_never_reactivation() -> None:
    draft = authority_object("ActiveProgramRouteV1")
    expired = successor(draft, ROUTE_EDGES[15])
    closed = successor(expired, ROUTE_EDGES[20])
    invalid_active = successor(expired, ("R07", "EXECUTION_EXPIRED", "ACTIVATE", "ACTIVE"))

    assert authority.lineage_findings([draft, expired, closed]) == []
    assert any(
        "illegal" in item.lower()
        for item in authority.lineage_findings([draft, expired, invalid_active])
    )


@pytest.mark.parametrize("source", authority.FALSE_AUTHORITY_SOURCES)
def test_issue_comment_file_fixture_test_and_ci_never_activate_authority(source: str) -> None:
    assert authority.authority_effect_findings(source, "NONE") == []
    assert authority.authority_effect_findings(source, "ACTIVE") == [
        f"{source} cannot produce authority effect ACTIVE."
    ]


def test_unknown_authority_source_and_marker_substitution_fail_closed() -> None:
    assert authority.authority_effect_findings("IMPLEMENTATION_DEFINED", "NONE") == [
        "Unknown authority source is rejected."
    ]


def test_exact_child_a_repository_gate_passes_only_the_complete_route() -> None:
    assert authority.repository_findings(ROOT) == []


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


def _assert_semantic_rejection(value: dict[str, object], code: str) -> None:
    value["contentHash"] = authority.content_hash(value)
    schema = value["schemaVersion"]
    assert isinstance(schema, str)
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(authority.canonical_bytes(value), schema)

    assert caught.value.code == code


@pytest.mark.parametrize(
    ("schema", "mutator", "code"),
    [
        (
            "MasterProgramAuthorityDecisionV1",
            lambda value: value.update(decisionAction="REJECT_MANIFEST"),
            "ACTION_LINK_MISMATCH",
        ),
        (
            "MasterProgramAuthorityDecisionV1",
            lambda value: value.update(lifecycleState="ACCEPTED_CURRENT"),
            "INITIAL_STATE_MISMATCH",
        ),
        (
            "MasterProgramAuthorityDecisionV1",
            lambda value: value.update(selectedManifest=reference("POLICY", "wrong:fixture")),
            "REFERENCE_TYPE_MISMATCH",
        ),
        (
            "ActiveProgramRouteV1",
            lambda value: value.update(lifecycleState="ACTIVE"),
            "ROUTE_PR_STATE_MISMATCH",
        ),
        (
            "ActiveProgramRouteV1",
            lambda value: value.update(lifecycleState="EXECUTION_EXPIRED"),
            "EXECUTION_EXPIRY_MISMATCH",
        ),
        (
            "ActiveProgramRouteV1",
            lambda value: value.update(allowedPaths=["../outside"]),
            "REPOSITORY_PATH_INVALID",
        ),
        (
            "ActiveProgramRouteV1",
            lambda value: value.update(maxPathCount=2),
            "PATH_COUNT_MISMATCH",
        ),
    ],
)
def test_cross_field_and_lifecycle_mutations_fail_closed(
    schema: str,
    mutator: Callable[[dict[str, object]], object],
    code: str,
) -> None:
    value = authority_object(schema)
    mutator(value)

    _assert_semantic_rejection(value, code)


def test_fixture_catalog_is_executable_not_metadata_only() -> None:
    corpus = json.loads(
        (ROOT / "tests/fixtures/authority-core-v1-cases.json").read_text(encoding="utf-8")
    )

    assert all(isinstance(case.get("probe"), str) for case in corpus["cases"])
    assert authority.fixture_execution_findings(corpus) == []


def test_schema_reads_are_bounded_before_parsing(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.schema.json"
    oversized.write_bytes(b" " * 131_073 + b"{}")

    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority._read_schema(oversized, "MasterProgramAuthorityDecisionV1")

    assert caught.value.code == "SIZE_LIMIT"


def test_schema_and_matrix_bytes_have_independently_frozen_identities() -> None:
    expected_paths = {
        *authority.SUPPORTED_SCHEMAS.values(),
        authority.MATRIX_PATH,
    }

    assert set(authority.ARTIFACT_SHA256) == expected_paths
    for relative, expected in authority.ARTIFACT_SHA256.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_quality_gate_records_the_actual_durable_red_commit_only() -> None:
    text = (ROOT / "docs/QUALITY_GATES.md").read_text(encoding="utf-8")

    assert "b7f122f704dc2168c64202c090e3e11164c67e80" in text
    assert "b7f122fe3aebbf958bb96950a569a3a818dbf046" not in text
