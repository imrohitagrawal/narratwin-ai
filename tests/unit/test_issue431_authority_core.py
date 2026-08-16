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
BASE = "4d239942eeda0c0b6c385b2d85dae873af076aa6"
HEAD = "65b8d2ba965f8089372cf60f88cbb9d28c0317ba"
REPOSITORY = "imrohitagrawal/narratwin-ai"
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
            effectiveAt="2026-08-15T00:00:00Z",
            priorDecision=None,
            selectedManifest=reference("MANIFEST", "manifest:fixture-only"),
            sourceProposal=reference("PROPOSAL", "proposal:fixture-only"),
        )
    elif schema == "Cut1AuthorityManifestV1":
        names = (
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
        common.update(
            authorityValues={
                name: reference("POLICY", f"{name.lower()}:fixture-only") for name in names
            },
            capabilityClassifications={name: "DEFERRED" for name in names},
            decisionBacklink=None,
            sourceProposal=reference("PROPOSAL", "proposal:fixture-only"),
        )
    else:
        common.update(
            aggregateTestCommands=["make stage8-quality"],
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
            focusedTestCommands=["python3 -m pytest tests/unit/test_issue431_authority_core.py"],
            maxChargedLines=4000,
            maxPathCount=1,
            parentIssue=426,
            predecessorMergeSha="3" * 40,
            pullRequest=None,
            reviewerRoles=["OWNER", "PRINCIPAL_ARCHITECT", "PRINCIPAL_TEST_ENGINEER", "NON_AUTHOR"],
            selectedManifest=reference("MANIFEST", "manifest:fixture-only"),
            supersededRoute=None,
            targetBranch="main",
        )
    unsigned = dict(common)
    del unsigned["contentHash"]
    domain = b"NARRATWIN-AUTHORITY-OBJECT-V1\0" + schema.encode("ascii") + b"\0"
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
    references = list(authority.ROW_REFERENCES[row_id])
    return {
        "actorClass": EXACT_ACTORS[row_id],
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
        "requiredGuards": [f"REQUIRE_{item}" for item in references],
        "requiredTypedReferences": references,
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
        (ROOT / "docs/governance/authority-core-state-matrices-v1.json").read_text(encoding="utf-8")
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
    reference_types = row["requiredTypedReferences"]
    assert isinstance(reference_types, list)
    source_hash_references = {
        "ACTIVE_HASH",
        "APPROVED_HASH",
        "CANDIDATE_HASH",
        "CURRENT_HASH",
        "EXPIRED_HASH",
        "MERGED_HASH",
        "REVIEWED_HASH",
        "ROUTE_HASH",
        "SOURCE_HASH",
        "VERIFIED_HASH",
    }

    def guard(kind: str) -> dict[str, str]:
        item = reference(kind, f"guard:{str(row['id']).lower()}-{kind.lower().replace('_', '-')}")
        if kind in source_hash_references:
            predecessor_hash = predecessor["contentHash"]
            assert isinstance(predecessor_hash, str)
            item["sha256"] = predecessor_hash
        elif kind == "ACCEPTED_DECISION":
            decision = value["decision"]
            assert isinstance(decision, dict)
            item["sha256"] = decision["sha256"]
        elif kind == "ACCEPTED_MANIFEST":
            manifest = value["selectedManifest"]
            assert isinstance(manifest, dict)
            item["sha256"] = manifest["sha256"]
        return item

    value["transition"] = {
        "actorClass": row["actorClass"],
        "effectId": row["effect"],
        "guardReferences": [guard(kind) for kind in reference_types],
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


def test_transition_guard_hash_binds_the_exact_predecessor_bytes() -> None:
    genesis = authority_object("MasterProgramAuthorityDecisionV1")
    reviewed = successor(genesis, DECISION_EDGES[0])
    assert authority.lineage_findings([genesis, reviewed]) == []

    reviewed["transition"]["guardReferences"][0]["sha256"] = "f" * 64  # type: ignore[index]
    reviewed["contentHash"] = authority.content_hash(reviewed)

    assert any(
        "guard hash" in item.lower() for item in authority.lineage_findings([genesis, reviewed])
    )


def _manifest_lineage_through_merge() -> list[dict[str, object]]:
    proposed = authority_object("Cut1AuthorityManifestV1")
    reviewed = successor(proposed, DECISION_EDGES[0])
    approved = successor(reviewed, DECISION_EDGES[2])
    merged = successor(approved, DECISION_EDGES[4])
    return [proposed, reviewed, approved, merged]


def _decision_lineage_for_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    proposed = authority_object("MasterProgramAuthorityDecisionV1")
    selected = proposed["selectedManifest"]
    assert isinstance(selected, dict)
    selected["sha256"] = manifest["contentHash"]
    selected["subject"] = manifest["objectId"]
    proposed["contentHash"] = authority.content_hash(proposed)
    reviewed = successor(proposed, DECISION_EDGES[0])
    approved = successor(reviewed, DECISION_EDGES[2])
    merged = successor(approved, DECISION_EDGES[4])
    accepted = successor(merged, DECISION_EDGES[6])
    return [proposed, reviewed, approved, merged, accepted]


def test_manifest_backlink_is_lifecycle_safe_and_added_only_at_acceptance() -> None:
    manifests = _manifest_lineage_through_merge()
    decision = _decision_lineage_for_manifest(manifests[-1])[-1]
    accepted = successor(manifests[-1], DECISION_EDGES[6])
    accepted["decisionBacklink"] = reference("DECISION", str(decision["objectId"]))
    accepted["decisionBacklink"]["sha256"] = decision["contentHash"]  # type: ignore[index]
    accepted["contentHash"] = authority.content_hash(accepted)

    assert authority.lineage_findings([*manifests, accepted]) == []

    missing = deepcopy(accepted)
    missing["decisionBacklink"] = None
    _assert_semantic_rejection(missing, "MANIFEST_BACKLINK_STATE_MISMATCH")


def _linked_contract_objects() -> list[dict[str, object]]:
    manifests = _manifest_lineage_through_merge()
    decisions = _decision_lineage_for_manifest(manifests[-1])
    accepted_manifest = successor(manifests[-1], DECISION_EDGES[6])
    accepted_manifest["decisionBacklink"] = reference(
        "DECISION", str(decisions[-1]["objectId"])
    )
    accepted_manifest["decisionBacklink"]["sha256"] = decisions[-1]["contentHash"]  # type: ignore[index]
    accepted_manifest["contentHash"] = authority.content_hash(accepted_manifest)
    route = authority_object("ActiveProgramRouteV1")
    route["decision"] = reference("DECISION", str(decisions[-1]["objectId"]))
    route["decision"]["sha256"] = decisions[-1]["contentHash"]  # type: ignore[index]
    route["selectedManifest"] = reference("MANIFEST", str(accepted_manifest["objectId"]))
    route["selectedManifest"]["sha256"] = accepted_manifest["contentHash"]  # type: ignore[index]
    route["contentHash"] = authority.content_hash(route)
    return [*manifests, *decisions, accepted_manifest, route]


def test_decision_manifest_and_route_hashes_agree_across_contracts() -> None:
    linked = _linked_contract_objects()
    assert authority.lineage_findings(linked) == []

    manifest = linked[3]
    decision = linked[8]
    route = linked[-1]
    selected = decision["selectedManifest"]
    assert isinstance(selected, dict)
    selected["sha256"] = "f" * 64
    decision["contentHash"] = authority.content_hash(decision)
    route_decision = route["decision"]
    assert isinstance(route_decision, dict)
    route_decision["sha256"] = decision["contentHash"]
    route["contentHash"] = authority.content_hash(route)

    assert any(
        "cross-contract" in item.lower() and str(manifest["objectId"]) in item
        for item in authority.lineage_findings(linked)
    )


def test_decision_acceptance_requires_the_selected_manifest_merged_revision() -> None:
    proposed_manifest = authority_object("Cut1AuthorityManifestV1")
    decisions = _decision_lineage_for_manifest(proposed_manifest)

    assert any(
        "selected manifest lifecycle" in item.lower()
        for item in authority.lineage_findings([proposed_manifest, *decisions])
    )


def test_route_and_manifest_references_resolve_to_the_exact_accepted_pair() -> None:
    manifests = _manifest_lineage_through_merge()
    proposed_decision = authority_object("MasterProgramAuthorityDecisionV1")
    selected = proposed_decision["selectedManifest"]
    assert isinstance(selected, dict)
    selected["sha256"] = manifests[-1]["contentHash"]
    selected["subject"] = manifests[-1]["objectId"]
    proposed_decision["contentHash"] = authority.content_hash(proposed_decision)
    accepted_manifest = successor(manifests[-1], DECISION_EDGES[6])
    accepted_manifest["decisionBacklink"] = reference(
        "DECISION", str(proposed_decision["objectId"])
    )
    accepted_manifest["decisionBacklink"]["sha256"] = proposed_decision["contentHash"]  # type: ignore[index]
    accepted_manifest["contentHash"] = authority.content_hash(accepted_manifest)
    route = authority_object("ActiveProgramRouteV1")
    route["decision"] = reference("DECISION", str(proposed_decision["objectId"]))
    route["decision"]["sha256"] = proposed_decision["contentHash"]  # type: ignore[index]
    route["selectedManifest"] = reference("MANIFEST", str(accepted_manifest["objectId"]))
    route["selectedManifest"]["sha256"] = accepted_manifest["contentHash"]  # type: ignore[index]
    route["contentHash"] = authority.content_hash(route)

    assert any(
        "accepted decision lifecycle" in item.lower()
        for item in authority.lineage_findings(
            [*manifests, proposed_decision, accepted_manifest, route]
        )
    )


def test_terminal_manifest_backlink_resolves_through_acceptance_ancestor() -> None:
    linked = _linked_contract_objects()
    accepted_manifest = linked[-2]
    expired_manifest = successor(accepted_manifest, DECISION_EDGES[10])

    assert authority.lineage_findings([*linked[:-1], expired_manifest]) == []


def _replacement_decision_lineage(
    manifest: dict[str, object], current: dict[str, object]
) -> list[dict[str, object]]:
    proposed = authority_object("MasterProgramAuthorityDecisionV1")
    proposed["objectId"] = "decision:replacement-fixture-only"
    proposed["decisionAction"] = "SUPERSEDE_CURRENT"
    proposed["priorDecision"] = reference("DECISION", str(current["objectId"]))
    proposed["priorDecision"]["sha256"] = current["contentHash"]  # type: ignore[index]
    selected = proposed["selectedManifest"]
    assert isinstance(selected, dict)
    selected["sha256"] = manifest["contentHash"]
    selected["subject"] = manifest["objectId"]
    proposed["contentHash"] = authority.content_hash(proposed)
    reviewed = successor(proposed, DECISION_EDGES[0])
    approved = successor(reviewed, DECISION_EDGES[2])
    merged = successor(approved, DECISION_EDGES[4])
    accepted = successor(merged, DECISION_EDGES[6])
    return [proposed, reviewed, approved, merged, accepted]


def test_decision_supersession_guards_bind_the_accepted_reciprocal_successor() -> None:
    manifests = _manifest_lineage_through_merge()
    current_lineage = _decision_lineage_for_manifest(manifests[-1])
    replacement_lineage = _replacement_decision_lineage(manifests[-1], current_lineage[-1])
    superseded = successor(current_lineage[-1], DECISION_EDGES[8])
    guards = superseded["transition"]["guardReferences"]  # type: ignore[index]
    by_type = {guard["referenceType"]: guard for guard in guards}
    by_type["ACCEPTED_SUCCESSOR"]["sha256"] = replacement_lineage[-1]["contentHash"]
    by_type["RECIPROCAL_LINKAGE"]["sha256"] = current_lineage[-1]["contentHash"]
    superseded["contentHash"] = authority.content_hash(superseded)
    objects = [*manifests, *current_lineage, *replacement_lineage, superseded]

    assert authority.lineage_findings(objects) == []

    by_type["ACCEPTED_SUCCESSOR"]["sha256"] = "f" * 64
    superseded["contentHash"] = authority.content_hash(superseded)
    assert any(
        "accepted successor" in item.lower() for item in authority.lineage_findings(objects)
    )

    by_type["ACCEPTED_SUCCESSOR"]["sha256"] = replacement_lineage[-1]["contentHash"]
    by_type["RECIPROCAL_LINKAGE"]["sha256"] = "f" * 64
    superseded["contentHash"] = authority.content_hash(superseded)
    assert any(
        "reciprocal linkage" in item.lower() for item in authority.lineage_findings(objects)
    )


def _route_supersession_bundle() -> tuple[
    dict[str, object], dict[str, object], dict[str, object]
]:
    source = authority_object("ActiveProgramRouteV1")
    replacement = authority_object("ActiveProgramRouteV1")
    replacement["objectId"] = "route:replacement-fixture-only"
    replacement["contentHash"] = authority.content_hash(replacement)
    superseded = successor(source, ROUTE_EDGES[10])
    superseded["supersededRoute"] = reference(
        "ROUTE", str(replacement["objectId"])
    )
    superseded["supersededRoute"]["sha256"] = replacement["contentHash"]  # type: ignore[index]
    guards = superseded["transition"]["guardReferences"]  # type: ignore[index]
    by_type = {guard["referenceType"]: guard for guard in guards}
    by_type["REPLACEMENT_ROUTE"]["sha256"] = replacement["contentHash"]
    superseded["contentHash"] = authority.content_hash(superseded)
    return source, replacement, superseded


def test_route_supersession_requires_the_exact_replacement_object() -> None:
    source, replacement, superseded = _route_supersession_bundle()

    assert authority.lineage_findings([source, replacement, superseded]) == []
    assert any(
        "replacement route" in item.lower()
        for item in authority.lineage_findings([source, superseded])
    )


@pytest.mark.parametrize("mutation", ["same-object", "wrong-subject", "wrong-generation"])
def test_route_supersession_requires_distinct_matching_replacement(mutation: str) -> None:
    source, replacement, superseded = _route_supersession_bundle()
    route_reference = superseded["supersededRoute"]
    assert isinstance(route_reference, dict)
    guards = superseded["transition"]["guardReferences"]  # type: ignore[index]
    by_type = {guard["referenceType"]: guard for guard in guards}
    if mutation == "same-object":
        route_reference["subject"] = source["objectId"]
        route_reference["sha256"] = source["contentHash"]
    elif mutation == "wrong-subject":
        route_reference["subject"] = "route:wrong-subject"
    else:
        replacement["generationId"] = "generation:replacement-mismatch"
        replacement["contentHash"] = authority.content_hash(replacement)
        route_reference["sha256"] = replacement["contentHash"]
    by_type["REPLACEMENT_ROUTE"]["sha256"] = route_reference["sha256"]
    superseded["contentHash"] = authority.content_hash(superseded)

    assert any(
        "replacement route" in item.lower()
        for item in authority.lineage_findings([source, replacement, superseded])
    )


def test_route_supersession_requires_a_draft_replacement() -> None:
    source, replacement, superseded = _route_supersession_bundle()
    reviewed_replacement = successor(replacement, ROUTE_EDGES[0])
    route_reference = superseded["supersededRoute"]
    assert isinstance(route_reference, dict)
    route_reference["sha256"] = reviewed_replacement["contentHash"]
    route_reference["subject"] = reviewed_replacement["objectId"]
    guards = superseded["transition"]["guardReferences"]  # type: ignore[index]
    by_type = {guard["referenceType"]: guard for guard in guards}
    by_type["REPLACEMENT_ROUTE"]["sha256"] = reviewed_replacement["contentHash"]
    superseded["contentHash"] = authority.content_hash(superseded)

    assert any(
        "replacement route" in item.lower()
        for item in authority.lineage_findings(
            [source, replacement, reviewed_replacement, superseded]
        )
    )


@pytest.mark.parametrize(
    "schema",
    [
        "MasterProgramAuthorityDecisionV1",
        "Cut1AuthorityManifestV1",
        "ActiveProgramRouteV1",
    ],
)
def test_revocation_reference_is_exactly_typed_for_every_contract(schema: str) -> None:
    value = authority_object(schema)
    value["validity"]["revokedAt"] = "2026-08-16T00:00:00Z"  # type: ignore[index]
    value["validity"]["revocationReference"] = reference(  # type: ignore[index]
        "POLICY", "policy:revocation-lookalike"
    )
    value["contentHash"] = authority.content_hash(value)

    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(authority.canonical_bytes(value), schema)

    assert caught.value.code == "REFERENCE_TYPE_MISMATCH"


def test_revocation_requires_representation_and_binds_both_exact_guards() -> None:
    manifests = _manifest_lineage_through_merge()
    decisions = _decision_lineage_for_manifest(manifests[-1])
    revoked = successor(decisions[-1], DECISION_EDGES[9])

    assert any(
        "revocation representation" in item.lower()
        for item in authority.lineage_findings([*manifests, *decisions, revoked])
    )

    revoked_at = "2026-08-16T00:00:00Z"
    revoked["validity"]["revokedAt"] = revoked_at  # type: ignore[index]
    revoked["validity"]["revocationReference"] = reference(  # type: ignore[index]
        "REVOCATION", "revocation:fixture-only"
    )
    guards = revoked["transition"]["guardReferences"]  # type: ignore[index]
    by_type = {guard["referenceType"]: guard for guard in guards}
    by_type["REVOCATION_REFERENCE"]["sha256"] = revoked["validity"][  # type: ignore[index]
        "revocationReference"
    ]["sha256"]
    by_type["EFFECTIVE_TIME"]["sha256"] = hashlib.sha256(
        b"NARRATWIN-AUTHORITY-GUARD-V1\0EFFECTIVE_TIME\0" + revoked_at.encode("ascii")
    ).hexdigest()
    revoked["contentHash"] = authority.content_hash(revoked)
    objects = [*manifests, *decisions, revoked]

    assert authority.lineage_findings(objects) == []

    by_type["REVOCATION_REFERENCE"]["sha256"] = "f" * 64
    revoked["contentHash"] = authority.content_hash(revoked)
    assert any(
        "revocation reference" in item.lower() for item in authority.lineage_findings(objects)
    )

    by_type["REVOCATION_REFERENCE"]["sha256"] = revoked["validity"][  # type: ignore[index]
        "revocationReference"
    ]["sha256"]
    by_type["EFFECTIVE_TIME"]["sha256"] = "f" * 64
    revoked["contentHash"] = authority.content_hash(revoked)
    assert any("effective time" in item.lower() for item in authority.lineage_findings(objects))

    by_type["EFFECTIVE_TIME"]["sha256"] = hashlib.sha256(
        b"NARRATWIN-AUTHORITY-GUARD-V1\0EFFECTIVE_TIME\0" + revoked_at.encode("ascii")
    ).hexdigest()
    revoked["validity"]["revocationReference"]["referenceType"] = "POLICY"  # type: ignore[index]
    revoked["contentHash"] = authority.content_hash(revoked)
    assert any(
        "reference_type_mismatch" in item.lower()
        for item in authority.lineage_findings(objects)
    )


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


def pull_request_event() -> dict[str, object]:
    return {
        "repository": {"full_name": REPOSITORY},
        "pull_request": {
            "base": {"ref": "main", "sha": BASE},
            "head": {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": REPOSITORY}},
        },
    }


def test_pull_request_merge_ref_uses_the_exact_event_head_for_route_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    event_path = tmp_path / "pull-request.json"
    event_path.write_text(json.dumps(pull_request_event()), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_HEAD_REF", BRANCH)
    revisions: list[str] = []

    def route_findings(root: Path, revision: str = "HEAD") -> list[str]:
        revisions.append(revision)
        return []

    def git(root: Path, *args: str) -> str:
        if args == ("rev-parse", "--verify", f"{HEAD}^{{commit}}"):
            return HEAD
        if args == ("merge-base", BASE, HEAD):
            return BASE
        if args == ("rev-parse", "--verify", "HEAD^{commit}"):
            return "a" * 40
        if args == ("rev-list", "--parents", "-n", "1", "a" * 40):
            return f"{'a' * 40} {BASE} {HEAD}"
        raise AssertionError(f"unexpected git arguments: {args}")

    monkeypatch.setattr(authority, "_git", git)
    monkeypatch.setattr(authority, "_route_findings", route_findings)

    assert authority.repository_findings(ROOT) == []
    assert revisions == [HEAD]


def test_pull_request_event_head_must_match_the_checked_out_commit_or_merge_parent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    event_path = tmp_path / "pull-request.json"
    event_path.write_text(json.dumps(pull_request_event()), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    def git(root: Path, *args: str) -> str:
        if args == ("rev-parse", "--verify", f"{HEAD}^{{commit}}"):
            return HEAD
        if args == ("merge-base", BASE, HEAD):
            return BASE
        if args == ("rev-parse", "--verify", "HEAD^{commit}"):
            return "a" * 40
        if args == ("rev-list", "--parents", "-n", "1", "a" * 40):
            return f"{'a' * 40} {BASE} {'b' * 40}"
        raise AssertionError(f"unexpected git arguments: {args}")

    monkeypatch.setattr(authority, "_git", git)

    assert authority._trusted_pull_request_head(ROOT) == (
        None,
        "Child A trusted pull-request head does not match the checked-out commit or synthetic merge.",
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "malformed",
        "wrong-repository",
        "forked-head",
        "wrong-branch",
        "wrong-base",
        "invalid-head-sha",
    ],
)
def test_pull_request_event_identity_failures_stop_route_validation(
    mutation: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    event = pull_request_event()
    pull_request = event["pull_request"]
    assert isinstance(pull_request, dict)
    if mutation == "wrong-repository":
        event["repository"] = {"full_name": "attacker/example"}
    elif mutation == "forked-head":
        pull_request["head"] = {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": "fork/example"}}
    elif mutation == "wrong-branch":
        pull_request["head"] = {"ref": "attacker", "sha": HEAD, "repo": {"full_name": REPOSITORY}}
    elif mutation == "wrong-base":
        pull_request["base"] = {"ref": "main", "sha": "f" * 40}
    elif mutation == "invalid-head-sha":
        pull_request["head"] = {"ref": BRANCH, "sha": "not-a-sha", "repo": {"full_name": REPOSITORY}}
    event_path = tmp_path / "pull-request.json"
    event_path.write_text("{" if mutation == "malformed" else json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_HEAD_REF", BRANCH)
    revisions: list[str] = []

    def route_findings(root: Path, revision: str = "HEAD") -> list[str]:
        revisions.append(revision)
        return []

    monkeypatch.setattr(authority, "_route_findings", route_findings)

    assert authority.repository_findings(ROOT) == [
        "Child A trusted pull-request head identity is unavailable or invalid."
    ]
    assert revisions == []


def test_pull_request_head_must_exist_on_the_exact_base(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    event_path = tmp_path / "pull-request.json"
    event_path.write_text(json.dumps(pull_request_event()), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_HEAD_REF", BRANCH)
    monkeypatch.setattr(authority, "_git", lambda root, *args: "f" * 40)
    monkeypatch.setattr(authority, "_route_findings", lambda root, revision="HEAD": [])

    assert authority.repository_findings(ROOT) == [
        "Child A trusted pull-request head is unavailable or not based on the exact approved base."
    ]


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


@pytest.mark.parametrize(
    "data",
    [
        b'"\\ud800"',
        b'"\\udfff"',
        b'{"value":"\\ud800"}',
        b'{"\\ud800":1}',
    ],
)
def test_parser_rejects_escaped_lone_surrogates_through_typed_error(
    data: bytes,
) -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(data, "MasterProgramAuthorityDecisionV1")

    assert caught.value.code == "NON_ASCII_STRING"


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


def test_set_like_route_paths_must_be_lexicographically_sorted() -> None:
    route = authority_object("ActiveProgramRouteV1")
    route["allowedPaths"] = ["z/example.invalid", "a/example.invalid"]
    route["maxPathCount"] = 2

    _assert_semantic_rejection(route, "COLLECTION_ORDER_MISMATCH")


def test_fixture_catalog_is_executable_not_metadata_only() -> None:
    corpus = json.loads(
        (ROOT / "tests/fixtures/authority-core-v1-cases.json").read_text(encoding="utf-8")
    )

    assert all(isinstance(case.get("probe"), str) for case in corpus["cases"])
    assert authority.fixture_execution_findings(corpus) == []


def test_every_fixture_expectation_is_verified_by_its_behavior_probe() -> None:
    corpus = json.loads(
        (ROOT / "tests/fixtures/authority-core-v1-cases.json").read_text(encoding="utf-8")
    )

    for index, case in enumerate(corpus["cases"]):
        mutated = deepcopy(corpus)
        mutated["cases"][index]["expect"] = "WRONG_EXPECTATION"
        findings = authority.fixture_execution_findings(mutated)
        assert any(case["id"] in finding for finding in findings), case["id"]


def test_schema_reads_are_bounded_before_parsing(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.schema.json"
    oversized.write_bytes(b" " * 131_073 + b"{}")

    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority._read_schema(oversized, "MasterProgramAuthorityDecisionV1")

    assert caught.value.code == "SIZE_LIMIT"


def test_schema_and_matrix_bytes_have_independently_frozen_identities() -> None:
    expected = {
        "docs/governance/schemas/master-program-authority-decision-v1.schema.json": "59b5c761fbf772cac9780dcbb3028eea0a2059f54fc5fc7b82ccac4ae8ee8872",
        "docs/governance/schemas/cut1-authority-manifest-v1.schema.json": "3bde62593557058250258bed96eb5e51185873cf6e8504f3cc362ee9cf8f1513",
        "docs/governance/schemas/active-program-route-v1.schema.json": "6723637f628bb484598c37a73174e520c6fa9f5cc8458b9c79d509c6c2bd8cb2",
        "docs/governance/authority-core-state-matrices-v1.json": "8bf72f95444887b0a0c92f7cdb31dc00ffbf86409504060fa3029321b08d7206",
    }

    assert authority.ARTIFACT_SHA256 == expected
    for relative, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash


def test_quality_gate_records_the_actual_durable_red_commit_only() -> None:
    text = (ROOT / "docs/QUALITY_GATES.md").read_text(encoding="utf-8")

    assert "b7f122f704dc2168c64202c090e3e11164c67e80" in text
    assert "b7f122fe3aebbf958bb96950a569a3a818dbf046" not in text
