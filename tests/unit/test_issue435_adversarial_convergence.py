"""Fixed independent RED oracle for Issue #435 adversarial convergence."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from scripts.quality import issue435_adversarial_convergence as protocol


ROOT = Path(__file__).parents[2]
MATRIX_PATH = ROOT / "docs/governance/adversarial-convergence-invariant-matrix-v1.json"
FREEZE_PATH = ROOT / "docs/governance/adversarial-convergence-red-freeze-v1.json"
REPOSITORY_TEST_PATH = ROOT / "tests/unit/test_issue435_adversarial_convergence_repository.py"
IDENTITY_DOMAIN = b"NARRATWIN:ACP:IDENTITY:V1\x00"
SIGNATURE_DOMAIN = b"NARRATWIN:ACP:SIGNATURE:V1\x00"
EXPECTED_SEMANTIC_SHA256 = "93988fea30aa8a01a7ce43125f97f089a2d6ed320090aec5d73e57702d0f4bba"
EXPECTED_MUTANT_OUTCOMES_SHA256 = "82827fdb52e95398c0e0afe3ff79b9f46dede3abe814cb816bcc5b1bc270cd1c"
EXPECTED_FIXTURE_REGISTRY_SHA256 = (
    "a79c0cced07dd4ccfd953d94036fa01e90e4c7117f76cc43b20a3707e44eee33"
)
PIPELINE = (
    "bounds",
    "parse",
    "schema",
    "canonical_identity",
    "independent_trust",
    "authorization",
    "graph_conflict",
    "phase_verdict",
)
DIMENSIONS = (
    "validation_order",
    "lifecycle_state",
    "temporal_boundary",
    "phase_separation",
    "cardinality_limit",
    "malformed_input",
    "deletion_corruption",
    "reordering_duplication",
    "substitution",
    "cryptographic_eligibility",
    "authorization_eligibility",
    "graph_conflict_precedence",
    "reconstruction_replay",
)
TEST_CLASSES = (
    "positive",
    "negative",
    "boundary",
    "malformed",
    "deletion",
    "corruption",
    "reordering",
    "duplication",
    "substitution",
    "maximum_cardinality",
)
EXPECTED_RED_FAILURES = (
    "tests/unit/test_issue435_adversarial_convergence.py::test_matrix_cross_product_and_exact_outcomes_are_closed",
    "tests/unit/test_issue435_adversarial_convergence.py::test_closed_universe_shrink_fails_exactly",
    "tests/unit/test_issue435_adversarial_convergence.py::test_case_catalog_rejects_missing_duplicate_reordered_unknown_and_field_drift",
    "tests/unit/test_issue435_adversarial_convergence.py::test_zero_candidates_and_duplicate_identity_fail_exactly",
    "tests/unit/test_issue435_adversarial_convergence.py::test_every_early_rejection_has_zero_later_callbacks",
    "tests/unit/test_issue435_adversarial_convergence.py::test_lifecycle_and_explicit_time_boundaries_are_exact",
    "tests/unit/test_issue435_adversarial_convergence.py::test_all_resource_bounds_cover_exact_n_and_n_plus_one",
    "tests/unit/test_issue435_adversarial_convergence.py::test_hostile_input_families_stop_before_later_work",
    "tests/unit/test_issue435_adversarial_convergence.py::test_identity_substitution_never_reaches_crypto",
    "tests/unit/test_issue435_adversarial_convergence.py::test_crypto_spy_ledger_is_exact_and_self_trust_fails",
    "tests/unit/test_issue435_adversarial_convergence.py::test_real_rfc8032_vector_and_mutation",
    "tests/unit/test_issue435_adversarial_convergence.py::test_only_trusted_authorized_candidates_can_conflict",
    "tests/unit/test_issue435_adversarial_convergence.py::test_structured_crypto_probe_mixed_results_and_exception",
    "tests/unit/test_issue435_adversarial_convergence.py::test_graph_fork_cycle_orphan_duplicate_and_permutation",
    "tests/unit/test_issue435_adversarial_convergence.py::test_graph_result_is_permutation_invariant",
    "tests/unit/test_issue435_adversarial_convergence.py::test_phase_substitution_returns_exact_verdicts",
    "tests/unit/test_issue435_adversarial_convergence.py::test_all_three_phases_are_exact_and_isolated",
    "tests/unit/test_issue435_adversarial_convergence.py::test_reconstruction_exact_equality_kills_subset_replay",
    "tests/unit/test_issue435_adversarial_convergence.py::test_reconstruction_rejects_missing_extra_corrupt_and_substituted_inputs",
    "tests/unit/test_issue435_adversarial_convergence.py::test_semantic_identity_resists_coordinated_matrix_and_freeze_mutation",
    "tests/unit/test_issue435_adversarial_convergence.py::test_budget_thresholds_are_exact_at_85_and_90_percent",
    "tests/unit/test_issue435_adversarial_convergence.py::test_implementation_and_evidence_blockers_remain_separate_and_exact",
    "tests/unit/test_issue435_adversarial_convergence.py::test_controlled_mutation_anchors_are_executable_and_complete",
    "tests/unit/test_issue435_adversarial_convergence.py::test_repository_artifacts_join_only_after_c3_freeze",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_freeze_schema_closes_roles_red_nodes_and_separate_blockers",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_activation_authority_and_every_prohibition_fail_exactly",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_repository_validator_is_read_only_and_static_boundary_is_ast_exact",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_sensitive_route_uses_paths_and_exact_issue_artifacts",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-process-435-False]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-process-435-True]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-final-review-435-False]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-phase-1-closure-435-False]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-main-False]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-main-True]",
    "tests/unit/test_issue435_adversarial_convergence_repository.py::test_dispatcher_runs_protocol_first_and_fails_fast[8-neutral-435-False]",
)
MUTANT_ASSERTION_IDS = {
    "MUT-ORDER-REORDER": "MUT-ORDER-REORDER::exact-stage-ledger",
    "MUT-LIFECYCLE-REPLACE": "MUT-LIFECYCLE-REPLACE::exact-finding",
    "MUT-TIME-BYPASS": "MUT-TIME-BYPASS::exact-finding",
    "MUT-PHASE-REPLACE": "MUT-PHASE-REPLACE::exact-finding",
    "MUT-BOUNDS-BYPASS": "MUT-BOUNDS-BYPASS::exact-finding",
    "MUT-PARSE-REPLACE": "MUT-PARSE-REPLACE::exact-finding",
    "MUT-IDENTITY-BYPASS": "MUT-IDENTITY-BYPASS::exact-finding",
    "MUT-DUPLICATE-BYPASS": "MUT-DUPLICATE-BYPASS::exact-finding",
    "MUT-SUBSTITUTION-REMOVE": "MUT-SUBSTITUTION-REMOVE::exact-finding",
    "MUT-SELF-TRUST-REPLACE": "MUT-SELF-TRUST-REPLACE::exact-finding",
    "MUT-AUTH-BYPASS": "MUT-AUTH-BYPASS::exact-finding",
    "MUT-PRECEDENCE-REPLACE": "MUT-PRECEDENCE-REPLACE::exact-selection",
    "MUT-REPLAY-SUBSET": "MUT-REPLAY-SUBSET::exact-finding",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def strict_object(raw: bytes) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate:{key}")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=pairs)
    assert isinstance(value, dict)
    return value


def matrix_document() -> dict[str, Any]:
    return strict_object(MATRIX_PATH.read_bytes())


def independent_semantic_sha(document: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(document)).hexdigest()


def synthetic_freeze(document: dict[str, Any]) -> bytes:
    semantic_sha = independent_semantic_sha(document)
    matrix_sha = hashlib.sha256(MATRIX_PATH.read_bytes()).hexdigest()
    test_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    repository_test_sha = hashlib.sha256(REPOSITORY_TEST_PATH.read_bytes()).hexdigest()
    freeze = {
        "schemaVersion": "AdversarialRedFreezeV1",
        "matrixId": "issue-435-adversarial-convergence-v1",
        "redHead": "1" * 40,
        "redTree": "4" * 40,
        "matrixBlobOid": "2" * 40,
        "matrixSha256": matrix_sha,
        "focusedOracleBlobs": [
            {
                "path": "tests/unit/test_issue435_adversarial_convergence.py",
                "blobOid": "3" * 40,
                "sha256": test_sha,
            },
            {
                "path": "tests/unit/test_issue435_adversarial_convergence_repository.py",
                "blobOid": "5" * 40,
                "sha256": repository_test_sha,
            },
        ],
        "semanticSha256": semantic_sha,
        "implementationAuthor": "implementation-author",
        "reviewers": [
            {
                "role": "architecture",
                "identity": "reviewer-architecture",
                "commentUrl": "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-1",
                "disposition": "PASS",
                "reviewedRedHead": "1" * 40,
                "semanticSha256": semantic_sha,
            },
            {
                "role": "security_trust",
                "identity": "reviewer-security",
                "commentUrl": "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-2",
                "disposition": "PASS",
                "reviewedRedHead": "1" * 40,
                "semanticSha256": semantic_sha,
            },
            {
                "role": "mutation_false_pass",
                "identity": "reviewer-mutation",
                "commentUrl": "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-3",
                "disposition": "PASS",
                "reviewedRedHead": "1" * 40,
                "semanticSha256": semantic_sha,
            },
        ],
        "expectedRedFailures": list(EXPECTED_RED_FAILURES),
        "redCatalogSha256": hashlib.sha256(canonical(EXPECTED_RED_FAILURES)).hexdigest(),
        "redBlockers": {
            "IMPLEMENTATION_BLOCKER": len(EXPECTED_RED_FAILURES),
            "EVIDENCE_BLOCKER": 0,
        },
        "reviewBlockers": {"IMPLEMENTATION_BLOCKER": 0, "EVIDENCE_BLOCKER": 0},
        "reviewFindings": [],
        "activation": "NONE",
        "authorityEffect": "NO_AUTHORITY_EFFECT",
        "completionState": "PRE_GREEN_REVIEWS_COMPLETE",
    }
    return canonical(freeze) + b"\n"


def candidate(
    *,
    phase: str = "CURRENT",
    payload: str = "candidate-payload",
    predecessor_id: str | None = None,
    priority: int = 1,
    lifecycle_state: str = "ACTIVE",
    lifecycle_operation: str = "USE",
    valid_from: str = "2026-08-20T00:00:00Z",
    valid_until: str = "2026-08-22T00:00:00Z",
    fresh_until: str = "2026-08-22T00:00:00Z",
    compromised_at: str | None = None,
    signature: str = "aa" * 64,
    candidate_id: str | None = None,
) -> tuple[bytes, str, bytes]:
    identity_fields: dict[str, object] = {
        "schemaVersion": "AdversarialCandidateV1",
        "phase": phase,
        "payload": payload,
        "predecessorId": predecessor_id,
        "priority": priority,
        "lifecycleState": lifecycle_state,
        "lifecycleOperation": lifecycle_operation,
        "validFrom": valid_from,
        "validUntil": valid_until,
        "freshUntil": fresh_until,
        "compromisedAt": compromised_at,
    }
    identity_message = IDENTITY_DOMAIN + canonical(identity_fields)
    expected_id = hashlib.sha256(identity_message).hexdigest()
    document = {
        "schemaVersion": "AdversarialCandidateV1",
        "candidateId": candidate_id or expected_id,
        "phase": phase,
        "payload": payload,
        "predecessorId": predecessor_id,
        "priority": priority,
        "lifecycleState": lifecycle_state,
        "lifecycleOperation": lifecycle_operation,
        "validFrom": valid_from,
        "validUntil": valid_until,
        "freshUntil": fresh_until,
        "compromisedAt": compromised_at,
        "signature": signature,
    }
    signature_fields = {key: value for key, value in document.items() if key != "signature"}
    signature_message = SIGNATURE_DOMAIN + canonical(signature_fields)
    return canonical(document), expected_id, signature_message


class ExactCryptoSpy:
    def __init__(self, expected: list[tuple[protocol.CryptoProbe, bool]]) -> None:
        self.expected = expected
        self.calls: list[protocol.CryptoProbe] = []

    def __call__(self, probe: protocol.CryptoProbe) -> bool:
        ordinal = len(self.calls)
        assert ordinal < len(self.expected), f"unexpected crypto probe {probe!r}"
        expected_probe, result = self.expected[ordinal]
        assert probe == expected_probe
        self.calls.append(probe)
        return result


def expected_probe(
    candidate_id: str,
    message: bytes,
    *,
    ordinal: int = 0,
    count: int = 1,
    phase: protocol.Phase = protocol.Phase.CURRENT,
    result: bool = True,
) -> tuple[protocol.CryptoProbe, bool]:
    return (
        protocol.CryptoProbe(
            candidate_id=candidate_id,
            signature=bytes.fromhex("aa" * 64),
            ordinal=ordinal,
            candidate_count=count,
            phase=phase,
            public_key=bytes.fromhex("11" * 32),
            message=message,
        ),
        result,
    )


def expected_crypto_calls(
    candidate_ids: tuple[str, ...],
    messages: tuple[bytes, ...],
    results: tuple[bool, ...],
    *,
    phase: protocol.Phase = protocol.Phase.CURRENT,
) -> tuple[protocol.CryptoCall, ...]:
    key_sha = hashlib.sha256(bytes.fromhex("11" * 32)).hexdigest()
    return tuple(
        protocol.CryptoCall(
            candidate_id,
            "aa" * 64,
            ordinal,
            len(candidate_ids),
            phase.value,
            key_sha,
            hashlib.sha256(message).hexdigest(),
            result,
        )
        for ordinal, (candidate_id, message, result) in enumerate(
            zip(candidate_ids, messages, results, strict=True)
        )
    )


def context(
    candidate_ids: tuple[str, ...],
    *,
    phase: protocol.Phase = protocol.Phase.CURRENT,
    authorized: frozenset[str] | None = None,
    max_candidates: int = 4,
    evaluation_time: str = "2026-08-21T00:00:00Z",
) -> protocol.EvaluationContext:
    return protocol.EvaluationContext(
        expected_phase=phase,
        trusted_public_keys={
            candidate_id: bytes.fromhex("11" * 32) for candidate_id in candidate_ids
        },
        authorized_candidate_ids=authorized if authorized is not None else frozenset(candidate_ids),
        evaluation_time=evaluation_time,
        max_candidates=max_candidates,
    )


def exact_finding(stage: str, phase: str, code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding(stage, phase, code, location),)


def phase_verdicts(
    target: protocol.Phase, verdict: protocol.Verdict
) -> tuple[protocol.PhaseVerdict, ...]:
    return tuple(
        protocol.PhaseVerdict(phase, verdict if phase is target else protocol.Verdict.UNAVAILABLE)
        for phase in protocol.Phase
    )


def pipeline_calls(
    candidate_ids: tuple[str, ...], terminal: str = "phase_verdict"
) -> tuple[protocol.StageCall, ...]:
    calls: list[protocol.StageCall] = []
    stages = PIPELINE[: PIPELINE.index(terminal) + 1]
    for stage in stages:
        if stage in {"graph_conflict", "phase_verdict"}:
            calls.append(protocol.StageCall(stage, "candidate-set", 0))
            continue
        for ordinal, candidate_id in enumerate(candidate_ids):
            location = (
                f"candidate[{ordinal}]"
                if stage in {"bounds", "parse", "schema", "canonical_identity"}
                else candidate_id
            )
            calls.append(protocol.StageCall(stage, location, ordinal))
    return tuple(calls)


def retained_fixture(
    documents: tuple[bytes, ...],
    candidate_ids: tuple[str, ...],
    messages: tuple[bytes, ...],
    *,
    selected: str | None,
) -> protocol.RetainedEvaluation:
    key = bytes.fromhex("11" * 32)
    return protocol.RetainedEvaluation(
        candidate_sha256s=tuple(hashlib.sha256(item).hexdigest() for item in documents),
        evaluation_phase=protocol.Phase.CURRENT,
        evaluation_time="2026-08-21T00:00:00Z",
        trusted_key_sha256s=tuple(
            (candidate_id, hashlib.sha256(key).hexdigest()) for candidate_id in candidate_ids
        ),
        authorized_candidate_ids=candidate_ids,
        findings=(),
        phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, protocol.Verdict.VALID),
        eligible_candidate_ids=tuple(sorted(candidate_ids)),
        selected_candidate_id=selected,
        stage_calls=pipeline_calls(candidate_ids),
        crypto_calls=tuple(
            protocol.CryptoCall(
                candidate_id,
                ("aa" * 64),
                ordinal,
                len(candidate_ids),
                "CURRENT",
                hashlib.sha256(key).hexdigest(),
                hashlib.sha256(message).hexdigest(),
                True,
            )
            for ordinal, (candidate_id, message) in enumerate(
                zip(candidate_ids, messages, strict=True)
            )
        ),
        graph_call_count=1,
        max_candidates=4,
        max_candidate_bytes=2048,
        max_aggregate_bytes=4096,
        max_json_depth=4,
        max_json_members=13,
        max_findings=32,
        max_retained_materials=4,
    )


DIMENSION_CONTRACTS = (
    (
        "validation_order",
        "bounds",
        "ACP.ORDER",
        "test_every_early_rejection_has_zero_later_callbacks",
        "MUT-ORDER-REORDER",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "lifecycle_state",
        "schema",
        "ACP.LIFECYCLE",
        "test_lifecycle_and_explicit_time_boundaries_are_exact",
        "MUT-LIFECYCLE-REPLACE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "temporal_boundary",
        "schema",
        "ACP.TIME",
        "test_lifecycle_and_explicit_time_boundaries_are_exact",
        "MUT-TIME-BYPASS",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "phase_separation",
        "phase_verdict",
        "ACP.PHASE",
        "test_phase_substitution_returns_exact_verdicts",
        "MUT-PHASE-REPLACE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "cardinality_limit",
        "bounds",
        "ACP.BOUNDS",
        "test_all_resource_bounds_cover_exact_n_and_n_plus_one",
        "MUT-BOUNDS-BYPASS",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "malformed_input",
        "parse",
        "ACP.PARSE",
        "test_hostile_input_families_stop_before_later_work",
        "MUT-PARSE-REPLACE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "deletion_corruption",
        "canonical_identity",
        "ACP.IDENTITY",
        "test_identity_substitution_never_reaches_crypto",
        "MUT-IDENTITY-BYPASS",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "reordering_duplication",
        "graph_conflict",
        "ACP.ORDERING",
        "test_zero_candidates_and_duplicate_identity_fail_exactly",
        "MUT-DUPLICATE-BYPASS",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "substitution",
        "canonical_identity",
        "ACP.SUBSTITUTION",
        "test_reconstruction_rejects_missing_extra_corrupt_and_substituted_inputs",
        "MUT-SUBSTITUTION-REMOVE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "cryptographic_eligibility",
        "independent_trust",
        "ACP.TRUST",
        "test_crypto_spy_ledger_is_exact_and_self_trust_fails",
        "MUT-SELF-TRUST-REPLACE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "authorization_eligibility",
        "authorization",
        "ACP.AUTHORIZATION",
        "test_only_trusted_authorized_candidates_can_conflict",
        "MUT-AUTH-BYPASS",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "graph_conflict_precedence",
        "graph_conflict",
        "ACP.GRAPH",
        "test_graph_fork_cycle_orphan_duplicate_and_permutation",
        "MUT-PRECEDENCE-REPLACE",
        protocol.BlockerClass.IMPLEMENTATION,
    ),
    (
        "reconstruction_replay",
        "phase_verdict",
        "ACP.REPLAY",
        "test_reconstruction_exact_equality_kills_subset_replay",
        "MUT-REPLAY-SUBSET",
        protocol.BlockerClass.EVIDENCE,
    ),
)
CLASS_CONTRACTS = (
    ("positive", None, protocol.Verdict.VALID, True),
    ("negative", "NEGATIVE", protocol.Verdict.INVALID, False),
    ("boundary", "BOUNDARY", protocol.Verdict.INVALID, False),
    ("malformed", "MALFORMED", protocol.Verdict.INVALID, False),
    ("deletion", "DELETED", protocol.Verdict.UNAVAILABLE, False),
    ("corruption", "CORRUPT", protocol.Verdict.INVALID, False),
    ("reordering", None, protocol.Verdict.VALID, True),
    ("duplication", "DUPLICATE", protocol.Verdict.INVALID, False),
    ("substitution", "SUBSTITUTED", protocol.Verdict.INVALID, False),
    ("maximum_cardinality", None, protocol.Verdict.VALID, True),
)


def matrix_fixture_bytes(case_id: str, input_class: str) -> bytes:
    dimension, test_class = case_id.split(":", 1)
    raw, candidate_id, message = candidate(payload=case_id)
    return canonical(
        {
            "schemaVersion": "AdversarialMatrixFixtureV1",
            "caseId": case_id,
            "inputClass": input_class,
            "nonce": hashlib.sha256(f"issue435:{case_id}".encode()).hexdigest(),
            "candidateDocumentsHex": [raw.hex()],
            "evaluationContext": {
                "expectedPhase": "CURRENT",
                "evaluationTime": "2026-08-21T00:00:00Z",
                "trustedPublicKeys": {candidate_id: "11" * 32},
                "authorizedCandidateIds": [candidate_id],
            },
            "cryptoInputs": [
                {
                    "candidateId": candidate_id,
                    "signatureHex": "aa" * 64,
                    "publicKeyHex": "11" * 32,
                    "messageHex": message.hex(),
                }
            ],
            "hostileMutation": {"dimension": dimension, "testClass": test_class},
        }
    )


def matrix_fixture_registry() -> dict[str, bytes]:
    return {
        f"fixture://{dimension}:{test_class}": matrix_fixture_bytes(
            f"{dimension}:{test_class}", f"{dimension}.{test_class}"
        )
        for dimension in DIMENSIONS
        for test_class in TEST_CLASSES
    }


def expected_matrix_cases() -> tuple[protocol.MatrixCase, ...]:
    cases: list[protocol.MatrixCase] = []
    for dimension, stage, prefix, test_node, mutant, blocker in DIMENSION_CONTRACTS:
        for test_class, suffix, verdict, eligible in CLASS_CONTRACTS:
            case_id = f"{dimension}:{test_class}"
            if dimension == "reconstruction_replay" and test_class == "reordering":
                suffix, verdict, eligible = "REORDERED", protocol.Verdict.INVALID, False
            input_class = f"{dimension}.{test_class}"
            fixture_bytes = matrix_fixture_bytes(case_id, input_class)
            fixture = strict_object(fixture_bytes)
            candidate_id = fixture["cryptoInputs"][0]["candidateId"]
            message = bytes.fromhex(fixture["cryptoInputs"][0]["messageHex"])
            terminal_stage = "phase_verdict" if suffix is None else stage
            stage_ledger = pipeline_calls((candidate_id,), terminal_stage)
            crypto_ledger = (
                (
                    protocol.MatrixCryptoExpectation(
                        candidate_id,
                        "aa" * 64,
                        0,
                        1,
                        protocol.Phase.CURRENT,
                        hashlib.sha256(bytes.fromhex("11" * 32)).hexdigest(),
                        hashlib.sha256(message).hexdigest(),
                        terminal_stage != "independent_trust",
                    ),
                )
                if "independent_trust" in tuple(item.stage for item in stage_ledger)
                and not (dimension == "reconstruction_replay" and test_class == "reordering")
                else ()
            )
            findings = (
                ()
                if suffix is None
                else exact_finding(stage, "CURRENT", f"{prefix}.{suffix}", f"case[{case_id}]")
            )
            cases.append(
                protocol.MatrixCase(
                    case_id=case_id,
                    dimension=dimension,
                    test_class=test_class,
                    target_phase=protocol.Phase.CURRENT,
                    input_class=input_class,
                    input_reference=f"fixture://{case_id}",
                    input_sha256=hashlib.sha256(fixture_bytes).hexdigest(),
                    stage=stage,
                    findings=findings,
                    phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, verdict),
                    stage_calls=stage_ledger,
                    crypto_expectations=crypto_ledger,
                    graph_eligible=eligible,
                    graph_call_count=1 if eligible else 0,
                    selected_candidate_reference=candidate_id if eligible else None,
                    test_node=test_node,
                    mutant_id=mutant,
                    assertion_id=f"{test_node}::{case_id}::exact-outcome",
                    blocker_class=blocker,
                    evidence_state="RED_EXPECTED",
                )
            )
    return tuple(cases)


def expected_matrix_observation(case: protocol.MatrixCase) -> protocol.MatrixObservation:
    return protocol.MatrixObservation(
        case_id=case.case_id,
        input_class=case.input_class,
        input_sha256=case.input_sha256,
        findings=case.findings,
        phase_verdicts=case.phase_verdicts,
        stage_calls=case.stage_calls,
        crypto_calls=tuple(
            protocol.CryptoCall(
                item.candidate_reference,
                item.signature_hex,
                item.ordinal,
                item.candidate_count,
                item.phase.value,
                item.public_key_sha256,
                item.message_sha256,
                item.result,
            )
            for item in case.crypto_expectations
        ),
        graph_eligible=case.graph_eligible,
        graph_call_count=case.graph_call_count,
        selected_candidate_reference=case.selected_candidate_reference,
    )


def test_matrix_cross_product_and_exact_outcomes_are_closed() -> None:
    document = matrix_document()
    assert tuple(document["pipeline"]) == PIPELINE
    assert document["candidateContract"]["identityDomain"].encode() == IDENTITY_DOMAIN
    assert document["candidateContract"]["signatureDomain"].encode() == SIGNATURE_DOMAIN
    universes = document["closedUniverses"]
    assert tuple(universes["dimensions"]) == DIMENSIONS
    assert tuple(universes["testClasses"]) == TEST_CLASSES
    invariants = document["invariants"]
    assert tuple(invariant["dimension"] for invariant in invariants) == DIMENSIONS
    assert all(tuple(invariant["caseProfiles"]) == TEST_CLASSES for invariant in invariants)
    assert (
        len(
            {
                (invariant["dimension"], case)
                for invariant in invariants
                for case in invariant["caseProfiles"]
            }
        )
        == 130
    )
    expected = expected_matrix_cases()
    registry = matrix_fixture_registry()
    registry_identity = hashlib.sha256(
        canonical([(reference, payload.hex()) for reference, payload in registry.items()])
    ).hexdigest()
    assert registry_identity == EXPECTED_FIXTURE_REGISTRY_SHA256
    assert tuple(document["caseIndex"]) == tuple(case.case_id for case in expected)
    assert tuple(registry) == tuple(case.input_reference for case in expected)
    assert protocol.normalized_case_catalog(document) == expected
    for case in expected:
        fixture = registry[case.input_reference]
        assert hashlib.sha256(fixture).hexdigest() == case.input_sha256
        probes = [
            expected_probe(
                expectation.candidate_reference,
                fixture,
                ordinal=expectation.ordinal,
                count=expectation.candidate_count,
                phase=expectation.phase,
                result=expectation.result,
            )
            for expectation in case.crypto_expectations
        ]
        spy = ExactCryptoSpy(probes)
        candidate_ids = tuple(item.candidate_reference for item in case.crypto_expectations)
        if not candidate_ids:
            candidate_ids = (strict_object(fixture)["cryptoInputs"][0]["candidateId"],)
        observed = protocol.execute_matrix_fixture(
            fixture,
            context=context(candidate_ids),
            crypto_verifier=spy,
        )
        assert observed == expected_matrix_observation(case)
        assert spy.calls == [probe for probe, _ in probes]

    positive = expected[0]
    stimulus = strict_object(registry[positive.input_reference])
    stimulus_id = stimulus["cryptoInputs"][0]["candidateId"]
    perturbations: list[tuple[dict[str, Any], str, str]] = []
    for field, value, code, location in (
        ("nonce", "0" * 64, "ACP.FIXTURE.NONCE", "nonce"),
        ("candidateDocumentsHex", ["00"], "ACP.PARSE.INVALID_JSON", "candidate[0]"),
        ("cryptoInputs", [], "ACP.FIXTURE.CRYPTO_INPUT", "cryptoInputs"),
    ):
        changed = deepcopy(stimulus)
        changed[field] = value
        perturbations.append((changed, code, location))
    for field, value, code in (
        ("signatureHex", "bb" * 64, "ACP.FIXTURE.SIGNATURE_MISMATCH"),
        ("publicKeyHex", "22" * 32, "ACP.FIXTURE.KEY_MISMATCH"),
        ("messageHex", "00", "ACP.FIXTURE.MESSAGE_MISMATCH"),
    ):
        changed = deepcopy(stimulus)
        changed["cryptoInputs"][0][field] = value
        perturbations.append((changed, code, f"cryptoInputs[0].{field}"))
    changed = deepcopy(stimulus)
    changed["evaluationContext"]["authorizedCandidateIds"] = []
    perturbations.append(
        (changed, "ACP.FIXTURE.AUTHORIZATION_MISMATCH", "evaluationContext.authorizedCandidateIds")
    )
    for changed, code, location in perturbations:
        observed = protocol.execute_matrix_fixture(
            canonical(changed),
            context=context((stimulus_id,)),
            crypto_verifier=ExactCryptoSpy([]),
        )
        assert observed is not None
        assert observed.findings == exact_finding("matrix", "CURRENT", code, location)
    changed_context = context((stimulus_id,), evaluation_time="2026-08-21T00:00:01Z")
    observed = protocol.execute_matrix_fixture(
        canonical(stimulus), context=changed_context, crypto_verifier=ExactCryptoSpy([])
    )
    assert observed is not None
    assert observed.findings == exact_finding(
        "matrix", "CURRENT", "ACP.FIXTURE.CONTEXT_MISMATCH", "evaluationContext"
    )
    result_spy = ExactCryptoSpy(
        [
            expected_probe(
                stimulus_id,
                bytes.fromhex(stimulus["cryptoInputs"][0]["messageHex"]),
                result=False,
            )
        ]
    )
    observed = protocol.execute_matrix_fixture(
        canonical(stimulus), context=context((stimulus_id,)), crypto_verifier=result_spy
    )
    assert observed is not None
    assert observed.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.SIGNATURE_INVALID", f"candidate[{stimulus_id}]"
    )
    assert result_spy.calls == [item for item, _ in result_spy.expected]
    result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), synthetic_freeze(document))
    assert result.findings == ()
    assert result.semantic_sha256 == EXPECTED_SEMANTIC_SHA256
    assert result.invariant_ids == tuple(invariant["id"] for invariant in invariants)
    assert result.blocker_classes == (
        protocol.BlockerClass.IMPLEMENTATION,
        protocol.BlockerClass.EVIDENCE,
    )
    assert result.normalized_case_ids == tuple(case.case_id for case in expected)


def test_closed_universe_shrink_fails_exactly() -> None:
    document = matrix_document()
    document["closedUniverses"]["dimensions"].pop()
    result = protocol.validate_matrix_bytes(
        canonical(document), synthetic_freeze(matrix_document())
    )
    assert result.findings == exact_finding(
        "matrix", "CURRENT", "ACP.MATRIX.UNIVERSE_MISMATCH", "closedUniverses.dimensions"
    )


def test_case_catalog_rejects_missing_duplicate_reordered_unknown_and_field_drift() -> None:
    for mutation in ("missing", "duplicate", "reordered", "unknown"):
        document = matrix_document()
        if mutation == "missing":
            document["caseIndex"].pop()
        elif mutation == "duplicate":
            document["caseIndex"][-1] = document["caseIndex"][0]
        elif mutation == "reordered":
            document["caseIndex"][0], document["caseIndex"][1] = (
                document["caseIndex"][1],
                document["caseIndex"][0],
            )
        else:
            document["caseIndex"][-1] = "unknown:positive"
        result = protocol.validate_matrix_bytes(
            canonical(document), synthetic_freeze(matrix_document())
        )
        assert result.findings == exact_finding(
            "matrix", "CURRENT", "ACP.MATRIX.CASE_INDEX_MISMATCH", "caseIndex"
        )

    document = matrix_document()
    del document["invariants"][0]["killTest"]
    result = protocol.validate_matrix_bytes(
        canonical(document), synthetic_freeze(matrix_document())
    )
    assert result.findings == exact_finding(
        "matrix", "CURRENT", "ACP.MATRIX.CONTRACT_FIELD_MISSING", "invariants[0].killTest"
    )
    for path, value in (
        (("caseProfiles", "positive", "targetPhase"), "HISTORICAL"),
        (("caseProfiles", "positive", "laterStageCalls"), 1),
        (("caseProfiles", "positive", "graphCallCount"), 0),
        (("fixtureContract", "nonceDomain"), "other:"),
        (("fixtureContract", "signatureHex"), "bb" * 64),
        (("fixtureContract", "publicKeyHex"), "22" * 32),
        (("controlledMutants", 0, "assertionId"), "wrong-assertion"),
        (("mutantOutcomes", 0, "assertionId"), "wrong-assertion"),
        (("invariants", 0, "stage"), "parse"),
    ):
        document = matrix_document()
        target: Any = document
        for segment in path[:-1]:
            target = target[segment]
        target[path[-1]] = value
        result = protocol.validate_matrix_bytes(
            canonical(document), synthetic_freeze(matrix_document())
        )
        assert result.findings == exact_finding(
            "matrix", "CURRENT", "ACP.MATRIX.CASE_LEDGER_MISMATCH", ".".join(map(str, path))
        )


def test_zero_candidates_and_duplicate_identity_fail_exactly() -> None:
    empty = protocol.evaluate_candidates(
        (), context=context(()), crypto_verifier=ExactCryptoSpy([])
    )
    assert empty.findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.CANDIDATE_COUNT", "candidate-set"
    )
    assert empty.current_verdict is protocol.Verdict.UNAVAILABLE
    assert empty.stage_calls == (protocol.StageCall("bounds", "candidate-set", 0),)
    assert empty.graph_call_count == 0

    raw, candidate_id, _ = candidate()
    duplicate = protocol.evaluate_candidates(
        (raw, raw), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert duplicate.findings == exact_finding(
        "canonical_identity",
        "CURRENT",
        "ACP.IDENTITY.DUPLICATE",
        f"candidate[{candidate_id}]",
    )
    assert duplicate.current_verdict is protocol.Verdict.INVALID
    assert duplicate.crypto_calls == ()
    assert duplicate.graph_call_count == 0


def test_every_early_rejection_has_zero_later_callbacks() -> None:
    raw, candidate_id, _ = candidate()
    cases = (
        (
            (b"x" * 2049,),
            exact_finding("bounds", "CURRENT", "ACP.BOUNDS.CANDIDATE_BYTES", "candidate[0]"),
            1,
        ),
        (
            (b"{",),
            exact_finding("parse", "CURRENT", "ACP.PARSE.INVALID_JSON", "candidate[0]"),
            2,
        ),
        (
            (raw.replace(b'"priority":1', b'"priority":"1"'),),
            exact_finding("schema", "CURRENT", "ACP.SCHEMA.TYPE", "candidate[0].priority"),
            3,
        ),
        (
            (raw[:-1] + b',"unexpected":true}',),
            exact_finding(
                "schema", "CURRENT", "ACP.SCHEMA.UNKNOWN_FIELD", "candidate[0].unexpected"
            ),
            3,
        ),
    )
    for documents, expected, expected_stage_count in cases:
        result = protocol.evaluate_candidates(
            documents,
            context=context((candidate_id,)),
            crypto_verifier=ExactCryptoSpy([]),
        )
        assert result.findings == expected
        assert result.stage_calls == tuple(
            protocol.StageCall(PIPELINE[index], "candidate[0]", 0)
            for index in range(expected_stage_count)
        )
        assert result.crypto_calls == ()
        assert result.graph_call_count == 0


def test_lifecycle_and_explicit_time_boundaries_are_exact() -> None:
    for state in ("RETIRED", "REVOKED", "SUPERSEDED", "TERMINAL", "UNKNOWN"):
        raw, candidate_id, _ = candidate(lifecycle_state=state)
        result = protocol.evaluate_candidates(
            (raw,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
        )
        assert result.findings == exact_finding(
            "schema", "CURRENT", "ACP.LIFECYCLE.STATE", "candidate[0].lifecycleState"
        )
        assert result.crypto_calls == () and result.graph_call_count == 0

    raw, candidate_id, _ = candidate(lifecycle_operation="DELETE")
    illegal = protocol.evaluate_candidates(
        (raw,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert illegal.findings == exact_finding(
        "schema", "CURRENT", "ACP.LIFECYCLE.OPERATION", "candidate[0].lifecycleOperation"
    )
    missing_state = raw.replace(b'"lifecycleState":"ACTIVE",', b"")
    missing = protocol.evaluate_candidates(
        (missing_state,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert missing.findings == exact_finding(
        "schema", "CURRENT", "ACP.SCHEMA.REQUIRED", "candidate[0].lifecycleState"
    )

    for evaluation_time, code in (
        ("2026-08-19T23:59:59Z", "ACP.TIME.OUTSIDE_WINDOW"),
        ("2026-08-22T00:00:01Z", "ACP.TIME.OUTSIDE_WINDOW"),
        ("2026-08-21T00:00:00Z", "ACP.TIME.COMPROMISED"),
    ):
        raw, candidate_id, _ = candidate(
            compromised_at="2026-08-21T00:00:00Z" if "COMPROMISED" in code else None
        )
        result = protocol.evaluate_candidates(
            (raw,),
            context=context((candidate_id,), evaluation_time=evaluation_time),
            crypto_verifier=ExactCryptoSpy([]),
        )
        assert result.findings == exact_finding("schema", "CURRENT", code, "candidate[0].validity")
        assert result.crypto_calls == () and result.graph_call_count == 0

    stale_raw, stale_id, _ = candidate(fresh_until="2026-08-21T12:00:00Z")
    stale = protocol.evaluate_candidates(
        (stale_raw,),
        context=context((stale_id,), evaluation_time="2026-08-21T12:00:01Z"),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert stale.findings == exact_finding(
        "schema", "CURRENT", "ACP.TIME.STALE", "candidate[0].freshUntil"
    )

    for exact_time in ("2026-08-20T00:00:00Z", "2026-08-22T00:00:00Z"):
        raw, candidate_id, message = candidate()
        result = protocol.evaluate_candidates(
            (raw,),
            context=context((candidate_id,), evaluation_time=exact_time),
            crypto_verifier=ExactCryptoSpy([expected_probe(candidate_id, message)]),
        )
        assert result.findings == ()


def test_all_resource_bounds_cover_exact_n_and_n_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    items = tuple(candidate(payload=f"bounded-{index}", priority=index) for index in range(4))
    documents, ids, messages = tuple(zip(*items, strict=True))
    exact = protocol.evaluate_candidates(
        documents,
        context=context(ids),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(candidate_id, message, ordinal=index, count=4)
                for index, (candidate_id, message) in enumerate(zip(ids, messages, strict=True))
            ]
        ),
    )
    assert exact.findings == () and exact.graph_call_count == 1
    fifth, fifth_id, _ = candidate(payload="bounded-4", priority=4)
    over_count = protocol.evaluate_candidates(
        (*documents, fifth),
        context=context((*ids, fifth_id)),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert over_count.findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.CANDIDATE_COUNT", "candidate-set"
    )
    assert over_count.stage_calls == (protocol.StageCall("bounds", "candidate-set", 0),)

    raw, candidate_id, message = candidate()
    for bounded_context in (
        replace(context((candidate_id,)), max_candidate_bytes=len(raw)),
        replace(context((candidate_id,)), max_json_depth=1),
        replace(context((candidate_id,)), max_json_members=13),
    ):
        at_limit = protocol.evaluate_candidates(
            (raw,),
            context=bounded_context,
            crypto_verifier=ExactCryptoSpy([expected_probe(candidate_id, message)]),
        )
        assert at_limit.findings == () and at_limit.graph_call_count == 1
    second_raw, second_id, second_message = candidate(payload="aggregate-second")
    aggregate_limit = protocol.evaluate_candidates(
        (raw, second_raw),
        context=replace(
            context((candidate_id, second_id)),
            max_aggregate_bytes=len(raw) + len(second_raw),
        ),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(candidate_id, message, ordinal=0, count=2),
                expected_probe(second_id, second_message, ordinal=1, count=2),
            ]
        ),
    )
    assert aggregate_limit.findings == () and aggregate_limit.graph_call_count == 1
    cases = (
        (
            (raw + b" ",),
            replace(context((candidate_id,)), max_candidate_bytes=len(raw)),
            "ACP.BOUNDS.CANDIDATE_BYTES",
            "candidate[0]",
        ),
        (
            (raw, raw),
            replace(context((candidate_id,)), max_aggregate_bytes=(2 * len(raw)) - 1),
            "ACP.BOUNDS.AGGREGATE_BYTES",
            "candidate-set",
        ),
        (
            (b'{"a":{"b":{"c":{"d":{"e":1}}}}}',),
            context((candidate_id,)),
            "ACP.BOUNDS.JSON_DEPTH",
            "candidate[0]",
        ),
        (
            (
                b'{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6,"g":7,"h":8,"i":9,"j":10,"k":11,"l":12,"m":13,"n":14}',
            ),
            context((candidate_id,)),
            "ACP.BOUNDS.JSON_MEMBERS",
            "candidate[0]",
        ),
    )
    for documents, bounded_context, code, location in cases:
        result = protocol.evaluate_candidates(
            documents, context=bounded_context, crypto_verifier=ExactCryptoSpy([])
        )
        assert result.findings == exact_finding("bounds", "CURRENT", code, location)
        assert result.crypto_calls == () and result.graph_call_count == 0

    assert (
        protocol.artifact_bound_findings(
            matrix_bytes=b"m" * 65536,
            freeze_bytes=b"f" * 32768,
            finding_count=32,
            retained_material_count=4,
            matrix_row_count=130,
        )
        == ()
    )
    for matrix_size, freeze_size, finding_count, retained_count, row_count, code, location in (
        (65537, 32768, 32, 4, 130, "ACP.BOUNDS.MATRIX_BYTES", "matrix"),
        (65536, 32769, 32, 4, 130, "ACP.BOUNDS.FREEZE_BYTES", "freeze"),
        (65536, 32768, 33, 4, 130, "ACP.BOUNDS.FINDING_COUNT", "findings"),
        (65536, 32768, 32, 5, 130, "ACP.BOUNDS.RETAINED_COUNT", "retained-materials"),
        (65536, 32768, 32, 4, 131, "ACP.BOUNDS.MATRIX_ROWS", "caseIndex"),
    ):
        artifact_result = protocol.artifact_bound_findings(
            matrix_bytes=b"m" * matrix_size,
            freeze_bytes=b"f" * freeze_size,
            finding_count=finding_count,
            retained_material_count=retained_count,
            matrix_row_count=row_count,
        )
        assert artifact_result == exact_finding("bounds", "CURRENT", code, location)

    matrix = MATRIX_PATH.read_bytes()
    freeze = synthetic_freeze(matrix_document())
    calls: list[dict[str, object]] = []
    sentinel = exact_finding("bounds", "CURRENT", "ACP.BOUNDS.COMPOSED", "validator")

    def composed_bounds(**values: object) -> tuple[protocol.Finding, ...]:
        calls.append(values)
        return sentinel

    monkeypatch.setattr(protocol, "artifact_bound_findings", composed_bounds)
    matrix_result = protocol.validate_matrix_bytes(matrix, freeze)
    assert matrix_result.findings == sentinel
    assert len(calls) == 1
    assert calls[0]["matrix_bytes"] == matrix
    assert calls[0]["freeze_bytes"] == freeze
    assert calls[0]["matrix_row_count"] == 130


def test_hostile_input_families_stop_before_later_work() -> None:
    raw, candidate_id, _ = candidate()
    cases = (
        (b"\xff", "parse", "ACP.PARSE.INVALID_UTF8", "candidate[0]"),
        (b"[]", "parse", "ACP.PARSE.NON_OBJECT", "candidate[0]"),
        (
            raw[:-1] + b',"phase":"CURRENT"}',
            "parse",
            "ACP.PARSE.DUPLICATE_MEMBER",
            "candidate[0].phase",
        ),
        (
            raw.replace(b'"priority":1', b'"priority":true'),
            "schema",
            "ACP.SCHEMA.TYPE",
            "candidate[0].priority",
        ),
        (
            raw[:-1] + b',"unexpected":true}',
            "schema",
            "ACP.SCHEMA.UNKNOWN_FIELD",
            "candidate[0].unexpected",
        ),
    )
    for hostile, stage, code, location in cases:
        result = protocol.evaluate_candidates(
            (hostile,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
        )
        assert result.findings == exact_finding(stage, "CURRENT", code, location)
        assert result.crypto_calls == () and result.graph_call_count == 0


def test_identity_substitution_never_reaches_crypto() -> None:
    raw, expected_id, _ = candidate(candidate_id="f" * 64)
    result = protocol.evaluate_candidates(
        (raw,), context=context((expected_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert result.findings == exact_finding(
        "canonical_identity", "CURRENT", "ACP.IDENTITY.MISMATCH", "candidate[0].candidateId"
    )
    assert result.current_verdict is protocol.Verdict.INVALID
    assert result.crypto_calls == ()
    assert result.graph_call_count == 0

    _, unbound_id, _ = candidate(payload="edge-bound")
    _, rebound_id, _ = candidate(payload="edge-bound", predecessor_id="a" * 64)
    assert unbound_id != rebound_id
    forged, _, _ = candidate(payload="edge-bound", predecessor_id="a" * 64, candidate_id=unbound_id)
    result = protocol.evaluate_candidates(
        (forged,), context=context((unbound_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert result.findings == exact_finding(
        "canonical_identity", "CURRENT", "ACP.IDENTITY.MISMATCH", "candidate[0].candidateId"
    )
    assert result.crypto_calls == () and result.graph_call_count == 0


def test_crypto_spy_ledger_is_exact_and_self_trust_fails() -> None:
    raw, candidate_id, message = candidate()
    signature = bytes.fromhex("aa" * 64)
    key = bytes.fromhex("11" * 32)
    spy = ExactCryptoSpy([expected_probe(candidate_id, message)])
    result = protocol.evaluate_candidates(
        (raw,), context=context((candidate_id,)), crypto_verifier=spy
    )
    assert result.findings == ()
    assert result.crypto_calls == (
        protocol.CryptoCall(
            candidate_id,
            signature.hex(),
            0,
            1,
            "CURRENT",
            hashlib.sha256(key).hexdigest(),
            hashlib.sha256(message).hexdigest(),
            True,
        ),
    )
    assert result.eligible_candidate_ids == (candidate_id,)
    assert result.selected_candidate_id == candidate_id
    assert result.stage_calls == pipeline_calls((candidate_id,))
    assert result.graph_call_count == 1

    untrusted = protocol.EvaluationContext(
        expected_phase=protocol.Phase.CURRENT,
        trusted_public_keys={},
        authorized_candidate_ids=frozenset({candidate_id}),
        evaluation_time="2026-08-21T00:00:00Z",
    )
    rejected = protocol.evaluate_candidates(
        (raw,), context=untrusted, crypto_verifier=ExactCryptoSpy([])
    )
    assert rejected.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.KEY_UNAVAILABLE", f"candidate[{candidate_id}]"
    )
    assert rejected.current_verdict is protocol.Verdict.UNAVAILABLE
    assert rejected.crypto_calls == ()
    assert rejected.graph_call_count == 0


def test_real_rfc8032_vector_and_mutation() -> None:
    public_key = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    signature = bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    assert protocol.verify_ed25519(public_key, b"", signature) is True
    assert protocol.verify_ed25519(public_key, b"", signature[:-1] + b"\x0c") is False


def test_only_trusted_authorized_candidates_can_conflict() -> None:
    first, first_id, first_message = candidate(payload="first", priority=9)
    second, second_id, second_message = candidate(payload="second", priority=9)
    spy = ExactCryptoSpy(
        [
            expected_probe(first_id, first_message, ordinal=0, count=2),
            expected_probe(second_id, second_message, ordinal=1, count=2),
        ]
    )
    result = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id)),
        crypto_verifier=spy,
    )
    assert result.findings == exact_finding(
        "graph_conflict", "CURRENT", "ACP.GRAPH.CONFLICT", "eligible-candidates"
    )
    assert result.current_verdict is protocol.Verdict.CONFLICTING
    assert result.eligible_candidate_ids == tuple(sorted((first_id, second_id)))
    assert result.stage_calls == pipeline_calls((first_id, second_id))
    assert result.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, True)
    )
    assert result.graph_call_count == 1

    unauthorized = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id), authorized=frozenset({first_id})),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(first_id, first_message, ordinal=0, count=2),
                expected_probe(second_id, second_message, ordinal=1, count=2),
            ]
        ),
    )
    assert unauthorized.findings == exact_finding(
        "authorization", "CURRENT", "ACP.AUTHORIZATION.DENIED", f"candidate[{second_id}]"
    )
    assert unauthorized.current_verdict is protocol.Verdict.INVALID
    assert unauthorized.stage_calls == pipeline_calls(
        (first_id, second_id), terminal="authorization"
    )
    assert unauthorized.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, True)
    )
    assert unauthorized.graph_call_count == 0


def test_structured_crypto_probe_mixed_results_and_exception() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    mixed = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(first_id, first_message, ordinal=0, count=2),
                expected_probe(second_id, second_message, ordinal=1, count=2, result=False),
            ]
        ),
    )
    assert mixed.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.SIGNATURE_INVALID", f"candidate[{second_id}]"
    )
    assert mixed.stage_calls == pipeline_calls((first_id, second_id), terminal="independent_trust")
    assert mixed.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, False)
    )
    assert mixed.graph_call_count == 0

    def raising_verifier(probe: protocol.CryptoProbe) -> bool:
        assert probe == expected_probe(first_id, first_message)[0]
        raise RuntimeError("contained verifier failure")

    contained = protocol.evaluate_candidates(
        (first,), context=context((first_id,)), crypto_verifier=raising_verifier
    )
    assert contained.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.VERIFIER_ERROR", f"candidate[{first_id}]"
    )
    assert contained.stage_calls == pipeline_calls((first_id,), terminal="independent_trust")
    assert contained.crypto_calls == expected_crypto_calls((first_id,), (first_message,), (False,))
    assert contained.graph_call_count == 0

    malformed_key = protocol.evaluate_candidates(
        (first,),
        context=replace(context((first_id,)), trusted_public_keys={first_id: b"short"}),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert malformed_key.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.KEY_MALFORMED", f"candidate[{first_id}]"
    )
    malformed_signature, _, _ = candidate(payload="first", priority=1, signature="aa")
    result = protocol.evaluate_candidates(
        (malformed_signature,), context=context((first_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert result.findings == exact_finding(
        "schema", "CURRENT", "ACP.SCHEMA.SIGNATURE", "candidate[0].signature"
    )


def test_graph_fork_cycle_orphan_duplicate_and_permutation() -> None:
    root, root_id, root_message = candidate(payload="root", priority=1)
    first, first_id, first_message = candidate(payload="first", priority=2, predecessor_id=root_id)
    second, second_id, second_message = candidate(
        payload="second", priority=3, predecessor_id=root_id
    )
    fork = protocol.evaluate_candidates(
        (root, first, second),
        context=context((root_id, first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(root_id, root_message, ordinal=0, count=3),
                expected_probe(first_id, first_message, ordinal=1, count=3),
                expected_probe(second_id, second_message, ordinal=2, count=3),
            ]
        ),
    )
    assert fork.findings == exact_finding(
        "graph_conflict", "CURRENT", "ACP.GRAPH.FORK", f"predecessor[{root_id}]"
    )
    assert fork.stage_calls == pipeline_calls((root_id, first_id, second_id))
    assert fork.crypto_calls == expected_crypto_calls(
        (root_id, first_id, second_id),
        (root_message, first_message, second_message),
        (True, True, True),
    )
    assert fork.current_verdict is protocol.Verdict.CONFLICTING

    _, unbound_first_id, _ = candidate(payload="first", priority=2)
    _, unbound_second_id, _ = candidate(payload="second", priority=3)
    cycle_first, _, _ = candidate(
        payload="first",
        priority=2,
        predecessor_id=unbound_second_id,
        candidate_id=unbound_first_id,
    )
    cycle_second, _, _ = candidate(
        payload="second",
        priority=3,
        predecessor_id=unbound_first_id,
        candidate_id=unbound_second_id,
    )
    cycle = protocol.evaluate_candidates(
        (cycle_first, cycle_second),
        context=context((unbound_first_id, unbound_second_id)),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert cycle.findings == exact_finding(
        "canonical_identity", "CURRENT", "ACP.IDENTITY.MISMATCH", "candidate[0].candidateId"
    )
    assert cycle.crypto_calls == () and cycle.graph_call_count == 0
    orphan, orphan_id, orphan_message = candidate(predecessor_id="f" * 64)
    orphaned = protocol.evaluate_candidates(
        (orphan,),
        context=context((orphan_id,)),
        crypto_verifier=ExactCryptoSpy([expected_probe(orphan_id, orphan_message)]),
    )
    assert orphaned.findings == exact_finding(
        "graph_conflict", "CURRENT", "ACP.GRAPH.ORPHAN", f"candidate[{orphan_id}]"
    )


def test_graph_result_is_permutation_invariant() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    forward = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(first_id, first_message, ordinal=0, count=2),
                expected_probe(second_id, second_message, ordinal=1, count=2),
            ]
        ),
    )
    reverse = protocol.evaluate_candidates(
        (second, first),
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [
                expected_probe(second_id, second_message, ordinal=0, count=2),
                expected_probe(first_id, first_message, ordinal=1, count=2),
            ]
        ),
    )
    assert (
        forward.findings,
        forward.historical_verdict,
        forward.current_verdict,
        forward.eligible_candidate_ids,
        forward.selected_candidate_id,
        forward.graph_call_count,
    ) == (
        reverse.findings,
        reverse.historical_verdict,
        reverse.current_verdict,
        reverse.eligible_candidate_ids,
        reverse.selected_candidate_id,
        reverse.graph_call_count,
    )
    assert forward.current_verdict is protocol.Verdict.VALID
    assert forward.eligible_candidate_ids == tuple(sorted((first_id, second_id)))
    assert forward.selected_candidate_id == second_id
    assert reverse.selected_candidate_id == second_id
    assert forward.stage_calls == pipeline_calls((first_id, second_id))
    assert reverse.stage_calls == pipeline_calls((second_id, first_id))
    assert forward.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, True)
    )
    assert reverse.crypto_calls == expected_crypto_calls(
        (second_id, first_id), (second_message, first_message), (True, True)
    )


def test_phase_substitution_returns_exact_verdicts() -> None:
    raw, candidate_id, _ = candidate(phase="HISTORICAL")
    result = protocol.evaluate_candidates(
        (raw,),
        context=context((candidate_id,), phase=protocol.Phase.CURRENT),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert result.findings == exact_finding(
        "schema", "CURRENT", "ACP.SCHEMA.PHASE_MISMATCH", "candidate[0].phase"
    )
    assert result.historical_verdict is protocol.Verdict.UNAVAILABLE
    assert result.current_verdict is protocol.Verdict.INVALID
    assert result.crypto_calls == ()
    assert result.graph_call_count == 0


def test_all_three_phases_are_exact_and_isolated() -> None:
    for phase in protocol.Phase:
        raw, candidate_id, message = candidate(phase=phase.value)
        result = protocol.evaluate_candidates(
            (raw,),
            context=context((candidate_id,), phase=phase),
            crypto_verifier=ExactCryptoSpy([expected_probe(candidate_id, message, phase=phase)]),
        )
        assert result.findings == ()
        assert result.phase_verdicts == phase_verdicts(phase, protocol.Verdict.VALID)
        assert (
            result.historical_verdict,
            result.current_verdict,
            result.acceptance_verdict,
        ) == tuple(item.verdict for item in result.phase_verdicts)
        for evaluation_time in ("2026-08-19T23:59:59Z", "2026-08-22T00:00:01Z"):
            outside = protocol.evaluate_candidates(
                (raw,),
                context=context((candidate_id,), phase=phase, evaluation_time=evaluation_time),
                crypto_verifier=ExactCryptoSpy([]),
            )
            assert outside.findings == exact_finding(
                "schema", phase.value, "ACP.TIME.OUTSIDE_WINDOW", "candidate[0].validity"
            )
            assert outside.phase_verdicts == phase_verdicts(phase, protocol.Verdict.INVALID)
            assert outside.stage_calls == pipeline_calls((candidate_id,), terminal="schema")
            assert outside.crypto_calls == () and outside.graph_call_count == 0


def test_reconstruction_exact_equality_kills_subset_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw, candidate_id, message = candidate()
    retained = retained_fixture((raw,), (candidate_id,), (message,), selected=candidate_id)
    exact = protocol.reconstruct_candidates(
        (raw,),
        retained=retained,
        context=context((candidate_id,)),
        crypto_verifier=ExactCryptoSpy([expected_probe(candidate_id, message)]),
    )
    assert exact.findings == ()
    assert exact.phase_verdicts == retained.phase_verdicts

    second, second_id, second_message = candidate(payload="replay-second", priority=2)
    rich = replace(
        retained_fixture(
            (raw, second),
            (candidate_id, second_id),
            (message, second_message),
            selected=second_id,
        ),
        findings=(
            protocol.Finding("schema", "CURRENT", "ACP.TEST.FIRST", "candidate[0]"),
            protocol.Finding("authorization", "CURRENT", "ACP.TEST.SECOND", "candidate[1]"),
        ),
    )
    assert protocol.retained_equality_findings(rich, rich) == ()
    retained_mutations = (
        (replace(rich, candidate_sha256s=rich.candidate_sha256s[::-1]), "candidateSha256s"),
        (replace(rich, evaluation_phase=protocol.Phase.HISTORICAL), "evaluationPhase"),
        (replace(rich, evaluation_time="2026-08-21T00:00:01Z"), "evaluationTime"),
        (replace(rich, trusted_key_sha256s=rich.trusted_key_sha256s[::-1]), "trustedKeys"),
        (
            replace(rich, authorized_candidate_ids=rich.authorized_candidate_ids[::-1]),
            "authorizedIds",
        ),
        (replace(rich, findings=rich.findings[::-1]), "findings"),
        (replace(rich, findings=rich.findings[:1]), "findings"),
        (replace(rich, findings=(*rich.findings, rich.findings[0])), "findings"),
        (replace(rich, phase_verdicts=rich.phase_verdicts[::-1]), "phaseVerdicts"),
        (replace(rich, eligible_candidate_ids=rich.eligible_candidate_ids[::-1]), "eligibleIds"),
        (replace(rich, selected_candidate_id=candidate_id), "selectedId"),
        (replace(rich, stage_calls=rich.stage_calls[::-1]), "stageCalls"),
        (replace(rich, crypto_calls=rich.crypto_calls[::-1]), "cryptoCalls"),
        (replace(rich, graph_call_count=0), "graphCallCount"),
        (replace(rich, max_candidates=3), "maxCandidates"),
        (replace(rich, max_candidate_bytes=2047), "maxCandidateBytes"),
        (replace(rich, max_aggregate_bytes=4095), "maxAggregateBytes"),
        (replace(rich, max_json_depth=3), "maxJsonDepth"),
        (replace(rich, max_json_members=12), "maxJsonMembers"),
        (replace(rich, max_findings=31), "maxFindings"),
        (replace(rich, max_retained_materials=3), "maxRetainedMaterials"),
    )
    for observed, location in retained_mutations:
        assert protocol.retained_equality_findings(observed, rich) == exact_finding(
            "phase_verdict", "CURRENT", "ACP.REPLAY.EXACT_MISMATCH", location
        )

    replay_expected = retained_fixture(
        (raw, second),
        (candidate_id, second_id),
        (message, second_message),
        selected=second_id,
    )
    replay_mutations = tuple(
        (replace(replay_expected, **{field: getattr(observed, field)}), location)
        for (observed, location), field in zip(
            retained_mutations,
            (
                "candidate_sha256s",
                "evaluation_phase",
                "evaluation_time",
                "trusted_key_sha256s",
                "authorized_candidate_ids",
                "findings",
                "findings",
                "findings",
                "phase_verdicts",
                "eligible_candidate_ids",
                "selected_candidate_id",
                "stage_calls",
                "crypto_calls",
                "graph_call_count",
                "max_candidates",
                "max_candidate_bytes",
                "max_aggregate_bytes",
                "max_json_depth",
                "max_json_members",
                "max_findings",
                "max_retained_materials",
            ),
            strict=True,
        )
    )
    comparator = protocol.retained_equality_findings
    comparisons: list[tuple[protocol.RetainedEvaluation, protocol.RetainedEvaluation]] = []

    def observed_comparator(
        observed: protocol.RetainedEvaluation, expected: protocol.RetainedEvaluation
    ) -> tuple[protocol.Finding, ...]:
        comparisons.append((observed, expected))
        return comparator(observed, expected)

    monkeypatch.setattr(protocol, "retained_equality_findings", observed_comparator)
    for changed, location in replay_mutations:
        comparisons.clear()
        spy = ExactCryptoSpy(
            [
                expected_probe(candidate_id, message, ordinal=0, count=2),
                expected_probe(second_id, second_message, ordinal=1, count=2),
            ]
        )
        result = protocol.reconstruct_candidates(
            (raw, second),
            retained=changed,
            context=context((candidate_id, second_id)),
            crypto_verifier=spy,
        )
        assert result.findings == exact_finding(
            "phase_verdict", "CURRENT", "ACP.REPLAY.EXACT_MISMATCH", location
        )
        assert len(comparisons) == 1
        assert comparisons[0][1] is changed
        assert spy.calls == [item for item, _ in spy.expected]

    mismatch = protocol.reconstruct_candidates(
        (raw,),
        retained=retained,
        context=context((candidate_id,)),
        crypto_verifier=ExactCryptoSpy([expected_probe(candidate_id, message, result=False)]),
    )
    assert mismatch.findings == exact_finding(
        "phase_verdict", "CURRENT", "ACP.REPLAY.EXACT_MISMATCH", "findings"
    )


def test_reconstruction_rejects_missing_extra_corrupt_and_substituted_inputs() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    retained = retained_fixture((first,), (first_id,), (first_message,), selected=first_id)
    well_formed_corruption = first.replace(b'"payload":"first"', b'"payload":"firsx"')
    cases = (
        ((), "bounds", "ACP.REPLAY.MISSING", "candidate-set"),
        ((first, second), "bounds", "ACP.REPLAY.EXTRA", "candidate-set"),
        ((first[:-1],), "parse", "ACP.PARSE.INVALID_JSON", "candidate[0]"),
        ((well_formed_corruption,), "canonical_identity", "ACP.REPLAY.CORRUPT", "candidate[0]"),
        ((first, first), "canonical_identity", "ACP.REPLAY.DUPLICATE", f"candidate[{first_id}]"),
        ((second,), "canonical_identity", "ACP.REPLAY.IDENTITY_MISMATCH", "candidate[0]"),
    )
    for documents, stage, code, location in cases:
        result = protocol.reconstruct_candidates(
            documents,
            retained=retained,
            context=context((first_id, second_id)),
            crypto_verifier=ExactCryptoSpy([]),
        )
        assert result.findings == exact_finding(stage, "CURRENT", code, location)
        assert result.crypto_calls == () and result.graph_call_count == 0

    wrong_phase, _, _ = candidate(payload="first", priority=1, phase="HISTORICAL")
    cross_phase = protocol.reconstruct_candidates(
        (wrong_phase,),
        retained=retained,
        context=context((first_id,)),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert cross_phase.findings == exact_finding(
        "schema", "CURRENT", "ACP.REPLAY.PHASE_MISMATCH", "candidate[0].phase"
    )

    self_trust = protocol.reconstruct_candidates(
        (first,),
        retained=retained,
        context=replace(context((first_id,)), trusted_public_keys={}),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert self_trust.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.KEY_UNAVAILABLE", f"candidate[{first_id}]"
    )

    retained_pair = retained_fixture(
        (first, second),
        (first_id, second_id),
        (first_message, second_message),
        selected=second_id,
    )
    reordered = protocol.reconstruct_candidates(
        (second, first),
        retained=retained_pair,
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert reordered.findings == exact_finding(
        "canonical_identity", "CURRENT", "ACP.REPLAY.REORDERED", "candidateSha256s"
    )
    assert reordered.crypto_calls == () and reordered.graph_call_count == 0

    wrong_verdicts = replace(
        retained,
        phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, protocol.Verdict.INVALID),
    )
    mismatch = protocol.reconstruct_candidates(
        (first,),
        retained=wrong_verdicts,
        context=context((first_id,)),
        crypto_verifier=ExactCryptoSpy([expected_probe(first_id, first_message)]),
    )
    assert mismatch.findings == exact_finding(
        "phase_verdict", "CURRENT", "ACP.REPLAY.EXACT_MISMATCH", "phaseVerdicts"
    )


def test_semantic_identity_resists_coordinated_matrix_and_freeze_mutation() -> None:
    document = matrix_document()
    document["invariants"][0]["invariant"] = "coordinated self-approved replacement"
    changed_freeze = strict_object(synthetic_freeze(document))
    result = protocol.validate_matrix_bytes(canonical(document), canonical(changed_freeze))
    assert result.findings == exact_finding(
        "matrix", "CURRENT", "ACP.FREEZE.INDEPENDENT_SEMANTIC_MISMATCH", "semanticSha256"
    )
    assert independent_semantic_sha(document) != EXPECTED_SEMANTIC_SHA256


def test_budget_thresholds_are_exact_at_85_and_90_percent() -> None:
    document = matrix_document()
    assert document["budgetPolicy"] == {
        "chargeRule": "additions_plus_deletions_no_deletion_credit",
        "riskThresholdPercent": 85,
        "stopThresholdPercent": 90,
        "denseCompressionProhibited": True,
        "levels": ["per_file", "partition", "aggregate"],
    }
    result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), synthetic_freeze(document))
    assert result.findings == ()
    assert protocol.budget_disposition(84, 100) is protocol.BudgetDisposition.NORMAL
    assert protocol.budget_disposition(85, 100) is protocol.BudgetDisposition.RISK_REVIEW_REQUIRED
    assert protocol.budget_disposition(89, 100) is protocol.BudgetDisposition.RISK_REVIEW_REQUIRED
    assert protocol.budget_disposition(90, 100) is protocol.BudgetDisposition.STOP_BEFORE_GREEN
    assert protocol.budget_disposition(1, 0) is protocol.BudgetDisposition.STOP_BEFORE_GREEN


def test_implementation_and_evidence_blockers_remain_separate_and_exact() -> None:
    assert protocol.convergence_blockers(
        unresolved_implementation_nodes=("behavior",),
        unresolved_review_findings=(),
        surviving_mutants=(),
        focused_failures=(),
    ) == (1, 0)
    assert protocol.convergence_blockers(
        unresolved_implementation_nodes=(),
        unresolved_review_findings=("review",),
        surviving_mutants=("mutant",),
        focused_failures=("focused",),
    ) == (0, 3)
    assert protocol.convergence_blockers(
        unresolved_implementation_nodes=(),
        unresolved_review_findings=(),
        surviving_mutants=(),
        focused_failures=(),
    ) == (0, 0)


def test_controlled_mutation_anchors_are_executable_and_complete() -> None:
    document = matrix_document()
    source = (ROOT / "scripts/quality/issue435_adversarial_convergence.py").read_text()
    mutants = document["controlledMutants"]
    expected = {
        "MUT-ORDER-REORDER",
        "MUT-LIFECYCLE-REPLACE",
        "MUT-TIME-BYPASS",
        "MUT-PHASE-REPLACE",
        "MUT-BOUNDS-BYPASS",
        "MUT-PARSE-REPLACE",
        "MUT-IDENTITY-BYPASS",
        "MUT-DUPLICATE-BYPASS",
        "MUT-SUBSTITUTION-REMOVE",
        "MUT-SELF-TRUST-REPLACE",
        "MUT-AUTH-BYPASS",
        "MUT-PRECEDENCE-REPLACE",
        "MUT-REPLAY-SUBSET",
    }
    assert {mutant["id"] for mutant in mutants} == expected
    assert len({mutant["anchor"] for mutant in mutants}) == len(mutants)
    assert len({mutant["find"] for mutant in mutants}) == len(mutants)
    assert all(mutant["anchor"] in mutant["find"] for mutant in mutants)
    assert all(mutant["find"] != mutant["replace"] for mutant in mutants)
    assert all(
        mutant["expectedCode"] is None or mutant["expectedCode"].startswith("ACP.")
        for mutant in mutants
    )
    assert hashlib.sha256(canonical(document["mutantOutcomes"])).hexdigest() == (
        EXPECTED_MUTANT_OUTCOMES_SHA256
    )
    assert {outcome["id"] for outcome in document["mutantOutcomes"]} == expected
    mutants_by_id = {mutant["id"]: mutant for mutant in mutants}
    outcomes_by_id = {outcome["id"]: outcome for outcome in document["mutantOutcomes"]}
    assert len({mutant["assertionId"] for mutant in mutants}) == len(mutants)
    assert {item["id"]: item["assertionId"] for item in mutants} == MUTANT_ASSERTION_IDS
    assert all(
        mutant["assertionId"] == outcomes_by_id[mutant_id]["assertionId"]
        and mutant["expectedCode"]
        == (
            outcomes_by_id[mutant_id]["finding"][2]
            if outcomes_by_id[mutant_id]["finding"] is not None
            else None
        )
        for mutant_id, mutant in mutants_by_id.items()
    )
    assert all(
        outcome["finding"] is None or "identity" not in outcome["finding"][3]
        for outcome in document["mutantOutcomes"]
    )
    assert all(
        mutants_by_id[invariant["mutantId"]]["killTest"] == invariant["killTest"]
        for invariant in document["invariants"]
    )
    invariant_mutants = tuple(invariant["mutantId"] for invariant in document["invariants"])
    assert set(invariant_mutants) == expected
    assert len(set(invariant_mutants)) == len(invariant_mutants)
    assert document["mutantCommandTemplate"] == (
        "uv run pytest -q tests/unit/test_issue435_adversarial_convergence.py::{killTest}"
    )
    missing_or_duplicate = tuple(
        mutant["id"] for mutant in mutants if source.count(mutant["find"]) != 1
    )
    assert missing_or_duplicate == ()
    assert all(mutant["action"] in {"remove", "bypass", "reorder", "replace"} for mutant in mutants)


def test_repository_artifacts_join_only_after_c3_freeze() -> None:
    if not FREEZE_PATH.exists():
        result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), None)
        assert result.findings == exact_finding(
            "freeze", "CURRENT", "ACP.FREEZE.MISSING", "adversarial-convergence-red-freeze-v1.json"
        )
        assert protocol.validate_repository_freeze(ROOT) == exact_finding(
            "freeze", "CURRENT", "ACP.FREEZE.MISSING", "adversarial-convergence-red-freeze-v1.json"
        )
        return
    result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), FREEZE_PATH.read_bytes())
    assert result.findings == ()
    assert result.semantic_sha256 == EXPECTED_SEMANTIC_SHA256
    assert protocol.validate_repository_freeze(ROOT) == ()
