"""Fixed independent RED oracle for Issue #435 adversarial convergence."""

from __future__ import annotations

import hashlib
import json
import ast
from dataclasses import astuple, dataclass, replace
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.quality import issue435_adversarial_convergence as protocol


ROOT = Path(__file__).parents[2]
MATRIX_PATH = ROOT / "docs/governance/adversarial-convergence-invariant-matrix-v1.json"
FREEZE_PATH = ROOT / "docs/governance/adversarial-convergence-red-freeze-v1.json"
REPOSITORY_TEST_PATH = ROOT / "tests/unit/test_issue435_adversarial_convergence_repository.py"
IDENTITY_DOMAIN = b"NARRATWIN:ACP:IDENTITY:V1\x00"
SIGNATURE_DOMAIN = b"NARRATWIN:ACP:SIGNATURE:V1\x00"
EXPECTED_SEMANTIC_SHA256 = "1d9c159e270a633e87eb1906acfe46efd51ac5873f21e909d982ba5a7abd4267"
EXPECTED_MUTANT_OUTCOMES_SHA256 = "2afd329343e566e79e507450ad9c10a1b44de4e5941dd17b0d0769da546ab5d9"
EXPECTED_FIXTURE_REGISTRY_SHA256 = (
    "1407395b3714f9a56aee5ac9f1da0f78e0d116f2431016c0bf8cbc17c746e6b1"
)
EXPECTED_DISTINCT_FIXTURE_COUNT = 28
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
SHARED_STIMULUS_CONTENT = "neutral-stimulus-content"
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


def assert_mutant(
    assertion_id: str,
    evaluation: protocol.Evaluation,
) -> None:
    assert assertion_id in MUTANT_ASSERTION_IDS.values()
    document = matrix_document()
    outcome = next(
        item for item in document["mutantOutcomes"] if item["assertionId"] == assertion_id
    )
    expected_finding = outcome["finding"]
    assert evaluation.findings == (
        () if expected_finding is None else (protocol.Finding(*expected_finding),)
    ), assertion_id
    assert tuple(item.verdict.value for item in evaluation.phase_verdicts) == tuple(
        outcome["phaseVerdicts"]
    ), assertion_id
    mutant_id = next(key for key, value in MUTANT_ASSERTION_IDS.items() if value == assertion_id)
    claim = document["mutantExecutionClaims"][mutant_id]
    assert evaluation.stage_calls == tuple(
        protocol.StageCall(*item) for item in claim["stageCalls"]
    ), assertion_id
    assert evaluation.crypto_calls == tuple(
        protocol.CryptoCall(*item) for item in claim["cryptoCalls"]
    ), assertion_id
    assert evaluation.eligible_candidate_ids == tuple(claim["eligibleCandidateIds"]), assertion_id
    assert evaluation.selected_candidate_id == claim["selectedCandidateId"], assertion_id
    assert evaluation.graph_call_count == claim["graphCallCount"], assertion_id


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

    def assert_exhausted(self) -> None:
        assert self.calls == [probe for probe, _ in self.expected]


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


def evaluate_with_spy(
    documents: tuple[bytes, ...],
    evaluation_context: protocol.EvaluationContext,
    probes: list[tuple[protocol.CryptoProbe, bool]],
) -> protocol.Evaluation:
    spy = ExactCryptoSpy(probes)
    result = protocol.evaluate_candidates(
        documents, context=evaluation_context, crypto_verifier=spy
    )
    spy.assert_exhausted()
    assert result.crypto_calls == tuple(
        protocol.CryptoCall(
            probe.candidate_id,
            probe.signature.hex(),
            probe.ordinal,
            probe.candidate_count,
            probe.phase.value,
            hashlib.sha256(probe.public_key).hexdigest(),
            hashlib.sha256(probe.message).hexdigest(),
            outcome,
        )
        for probe, outcome in probes
    )
    return result


def reconstruct_with_spy(
    documents: tuple[bytes, ...],
    retained: protocol.RetainedEvaluation,
    evaluation_context: protocol.EvaluationContext,
    probes: list[tuple[protocol.CryptoProbe, bool]],
) -> protocol.Evaluation:
    spy = ExactCryptoSpy(probes)
    result = protocol.reconstruct_candidates(
        documents,
        retained=retained,
        context=evaluation_context,
        crypto_verifier=spy,
    )
    spy.assert_exhausted()
    assert result.crypto_calls == tuple(
        protocol.CryptoCall(
            probe.candidate_id,
            probe.signature.hex(),
            probe.ordinal,
            probe.candidate_count,
            probe.phase.value,
            hashlib.sha256(probe.public_key).hexdigest(),
            hashlib.sha256(probe.message).hexdigest(),
            outcome,
        )
        for probe, outcome in probes
    )
    return result


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


@dataclass(frozen=True)
class MatrixVector:
    stimulus: protocol.MatrixStimulus
    evaluation: protocol.Evaluation
    probes: tuple[tuple[protocol.CryptoProbe, bool], ...]


def expected_evaluation(
    findings: tuple[protocol.Finding, ...],
    verdict: protocol.Verdict,
    candidate_ids: tuple[str, ...],
    stage_calls: tuple[protocol.StageCall, ...],
    crypto_calls: tuple[protocol.CryptoCall, ...] = (),
    *,
    selected: str | None = None,
    graph_calls: int = 0,
) -> protocol.Evaluation:
    return protocol.Evaluation(
        findings=findings,
        historical_verdict=protocol.Verdict.UNAVAILABLE,
        current_verdict=verdict,
        acceptance_verdict=protocol.Verdict.UNAVAILABLE,
        phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, verdict),
        eligible_candidate_ids=tuple(sorted(candidate_ids)) if graph_calls else (),
        selected_candidate_id=selected,
        stage_calls=stage_calls,
        crypto_calls=crypto_calls,
        graph_call_count=graph_calls,
    )


def positive_matrix_vector(token: str, test_class: str) -> MatrixVector:
    count = 4 if test_class == "maximum_cardinality" else 2 if test_class == "reordering" else 1
    entries = tuple(candidate(payload=f"{token}-{index}", priority=index) for index in range(count))
    selected_id = entries[-1][1]
    documents, candidate_ids, messages = tuple(zip(*entries, strict=True))
    if test_class == "reordering":
        documents = documents[::-1]
        candidate_ids = candidate_ids[::-1]
        messages = messages[::-1]
    probes = tuple(
        expected_probe(candidate_id, message, ordinal=index, count=count)
        for index, (candidate_id, message) in enumerate(zip(candidate_ids, messages, strict=True))
    )
    evaluation = expected_evaluation(
        (),
        protocol.Verdict.VALID,
        candidate_ids,
        pipeline_calls(candidate_ids),
        expected_crypto_calls(candidate_ids, messages, (True,) * count),
        selected=selected_id,
        graph_calls=1,
    )
    return MatrixVector(
        protocol.MatrixStimulus(documents, context(candidate_ids), None), evaluation, probes
    )


def positive_replay_vector(token: str, test_class: str) -> MatrixVector:
    count = 4 if test_class == "maximum_cardinality" else 2 if test_class == "reordering" else 1
    entries = tuple(candidate(payload=f"{token}-{index}", priority=index) for index in range(count))
    documents, candidate_ids, messages = tuple(zip(*entries, strict=True))
    selected_id = candidate_ids[-1]
    retained = retained_fixture(documents, candidate_ids, messages, selected=selected_id)
    if test_class == "reordering":
        reordered_ids = candidate_ids[::-1]
        evaluation = expected_evaluation(
            exact_finding(
                "canonical_identity", "CURRENT", "ACP.REPLAY.REORDERED", "candidateSha256s"
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls(reordered_ids, "canonical_identity"),
        )
        return MatrixVector(
            protocol.MatrixStimulus(documents[::-1], context(candidate_ids), retained),
            evaluation,
            (),
        )
    probes = tuple(
        expected_probe(candidate_id, message, ordinal=index, count=count)
        for index, (candidate_id, message) in enumerate(zip(candidate_ids, messages, strict=True))
    )
    evaluation = expected_evaluation(
        (),
        protocol.Verdict.VALID,
        candidate_ids,
        pipeline_calls(candidate_ids),
        expected_crypto_calls(candidate_ids, messages, (True,) * count),
        selected=selected_id,
        graph_calls=1,
    )
    return MatrixVector(
        protocol.MatrixStimulus(documents, context(candidate_ids), retained), evaluation, probes
    )


def positive_graph_vector(token: str, test_class: str) -> MatrixVector:
    count = 4 if test_class == "maximum_cardinality" else 2
    entries: list[tuple[bytes, str, bytes]] = []
    predecessor: str | None = None
    for index in range(count):
        item = candidate(payload=f"{token}-{index}", priority=index, predecessor_id=predecessor)
        entries.append(item)
        predecessor = item[1]
    documents, candidate_ids, messages = tuple(zip(*entries, strict=True))
    if test_class == "reordering":
        documents = documents[::-1]
        candidate_ids = candidate_ids[::-1]
        messages = messages[::-1]
    probes = tuple(
        expected_probe(candidate_id, message, ordinal=index, count=count)
        for index, (candidate_id, message) in enumerate(zip(candidate_ids, messages, strict=True))
    )
    selected_id = entries[-1][1]
    evaluation = expected_evaluation(
        (),
        protocol.Verdict.VALID,
        candidate_ids,
        pipeline_calls(candidate_ids),
        expected_crypto_calls(candidate_ids, messages, (True,) * count),
        selected=selected_id,
        graph_calls=1,
    )
    return MatrixVector(
        protocol.MatrixStimulus(documents, context(candidate_ids), None), evaluation, probes
    )


def boundary_matrix_vector(dimension: str, token: str) -> MatrixVector:
    if dimension == "cardinality_limit":
        return positive_matrix_vector(token, "maximum_cardinality")
    if dimension in {"deletion_corruption", "reconstruction_replay"}:
        return positive_replay_vector(token, "positive")
    if dimension == "reordering_duplication":
        return positive_matrix_vector(token, "reordering")
    if dimension in {"substitution", "graph_conflict_precedence"}:
        return positive_graph_vector(token, "positive")
    if dimension == "phase_separation":
        raw, candidate_id, message = candidate(payload=token, phase="ACCEPTANCE")
        probes = (expected_probe(candidate_id, message, phase=protocol.Phase.ACCEPTANCE),)
        evaluation = protocol.Evaluation(
            findings=(),
            historical_verdict=protocol.Verdict.UNAVAILABLE,
            current_verdict=protocol.Verdict.UNAVAILABLE,
            acceptance_verdict=protocol.Verdict.VALID,
            phase_verdicts=phase_verdicts(protocol.Phase.ACCEPTANCE, protocol.Verdict.VALID),
            eligible_candidate_ids=(candidate_id,),
            selected_candidate_id=candidate_id,
            stage_calls=pipeline_calls((candidate_id,)),
            crypto_calls=expected_crypto_calls(
                (candidate_id,), (message,), (True,), phase=protocol.Phase.ACCEPTANCE
            ),
            graph_call_count=1,
        )
        return MatrixVector(
            protocol.MatrixStimulus(
                (raw,), context((candidate_id,), phase=protocol.Phase.ACCEPTANCE), None
            ),
            evaluation,
            probes,
        )
    if dimension == "temporal_boundary":
        raw, candidate_id, message = candidate(payload=token, valid_from="2026-08-21T00:00:00Z")
        vector = positive_matrix_vector(token, "positive")
        return replace(
            vector,
            stimulus=protocol.MatrixStimulus(
                (raw,), context((candidate_id,), evaluation_time="2026-08-21T00:00:00Z"), None
            ),
            evaluation=replace(
                vector.evaluation,
                eligible_candidate_ids=(candidate_id,),
                selected_candidate_id=candidate_id,
                stage_calls=pipeline_calls((candidate_id,)),
                crypto_calls=expected_crypto_calls((candidate_id,), (message,), (True,)),
            ),
            probes=(expected_probe(candidate_id, message),),
        )
    return positive_matrix_vector(token, "positive")


def hostile_matrix_vector(dimension: str, test_class: str) -> MatrixVector:
    token = SHARED_STIMULUS_CONTENT
    if test_class == "boundary":
        return boundary_matrix_vector(dimension, token)
    if test_class in {"positive", "reordering", "maximum_cardinality"}:
        if dimension in {"deletion_corruption", "reconstruction_replay"}:
            return positive_replay_vector(token, test_class)
        if dimension == "graph_conflict_precedence":
            return positive_graph_vector(token, test_class)
        return positive_matrix_vector(token, test_class)
    raw, candidate_id, message = candidate(payload=token)
    candidate_context = context((candidate_id,))
    replay_retained = (
        retained_fixture((raw,), (candidate_id,), (message,), selected=candidate_id)
        if dimension in {"deletion_corruption", "reconstruction_replay"}
        else None
    )
    no_crypto: tuple[tuple[protocol.CryptoProbe, bool], ...] = ()
    if test_class == "malformed":
        return MatrixVector(
            protocol.MatrixStimulus((b"{",), candidate_context, replay_retained),
            expected_evaluation(
                exact_finding("parse", "CURRENT", "ACP.PARSE.INVALID_JSON", "candidate[0]"),
                protocol.Verdict.INVALID,
                (),
                pipeline_calls((candidate_id,), "parse"),
            ),
            no_crypto,
        )
    if test_class == "deletion":
        retained = replay_retained
        code = "ACP.REPLAY.MISSING" if retained else "ACP.BOUNDS.CANDIDATE_COUNT"
        return MatrixVector(
            protocol.MatrixStimulus((), candidate_context, retained),
            expected_evaluation(
                exact_finding("bounds", "CURRENT", code, "candidate-set"),
                protocol.Verdict.UNAVAILABLE,
                (),
                (protocol.StageCall("bounds", "candidate-set", 0),),
            ),
            no_crypto,
        )
    if test_class in {"corruption", "substitution"}:
        supplied_id = "0" * 64 if test_class == "corruption" else "f" * 64
        hostile, expected_id, _ = candidate(payload=token, candidate_id=supplied_id)
        code = (
            "ACP.REPLAY.CORRUPT"
            if replay_retained is not None and test_class == "corruption"
            else "ACP.REPLAY.IDENTITY_MISMATCH"
            if replay_retained is not None
            else "ACP.IDENTITY.MISMATCH"
        )
        location = "candidate[0]" if replay_retained is not None else "candidate[0].candidateId"
        return MatrixVector(
            protocol.MatrixStimulus((hostile,), context((expected_id,)), replay_retained),
            expected_evaluation(
                exact_finding(
                    "canonical_identity",
                    "CURRENT",
                    code,
                    location,
                ),
                protocol.Verdict.INVALID,
                (),
                pipeline_calls((expected_id,), "canonical_identity"),
            ),
            no_crypto,
        )
    if test_class == "duplication":
        code = "ACP.REPLAY.DUPLICATE" if replay_retained is not None else "ACP.IDENTITY.DUPLICATE"
        return MatrixVector(
            protocol.MatrixStimulus((raw, raw), candidate_context, replay_retained),
            expected_evaluation(
                exact_finding(
                    "canonical_identity",
                    "CURRENT",
                    code,
                    f"candidate[{candidate_id}]",
                ),
                protocol.Verdict.INVALID,
                (),
                pipeline_calls((candidate_id, candidate_id), "canonical_identity"),
            ),
            no_crypto,
        )
    if dimension in {"validation_order", "cardinality_limit"}:
        stimulus = protocol.MatrixStimulus((), candidate_context, None)
        evaluation = expected_evaluation(
            exact_finding("bounds", "CURRENT", "ACP.BOUNDS.CANDIDATE_COUNT", "candidate-set"),
            protocol.Verdict.UNAVAILABLE,
            (),
            (protocol.StageCall("bounds", "candidate-set", 0),),
        )
    elif dimension == "lifecycle_state":
        raw, candidate_id, _ = candidate(payload=token, lifecycle_state="RETIRED")
        stimulus = protocol.MatrixStimulus((raw,), context((candidate_id,)), None)
        evaluation = expected_evaluation(
            exact_finding(
                "schema", "CURRENT", "ACP.LIFECYCLE.STATE", "candidate[0].lifecycleState"
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "schema"),
        )
    elif dimension == "temporal_boundary":
        stimulus = protocol.MatrixStimulus(
            (raw,), context((candidate_id,), evaluation_time="2026-08-19T23:59:59Z"), None
        )
        evaluation = expected_evaluation(
            exact_finding("schema", "CURRENT", "ACP.TIME.OUTSIDE_WINDOW", "candidate[0].validity"),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "schema"),
        )
    elif dimension == "phase_separation":
        raw, candidate_id, _ = candidate(payload=token, phase="HISTORICAL")
        stimulus = protocol.MatrixStimulus((raw,), context((candidate_id,)), None)
        evaluation = expected_evaluation(
            exact_finding("schema", "CURRENT", "ACP.SCHEMA.PHASE_MISMATCH", "candidate[0].phase"),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "schema"),
        )
    elif dimension == "malformed_input":
        stimulus = protocol.MatrixStimulus((b"{",), candidate_context, None)
        evaluation = expected_evaluation(
            exact_finding("parse", "CURRENT", "ACP.PARSE.INVALID_JSON", "candidate[0]"),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "parse"),
        )
    elif dimension == "deletion_corruption":
        retained = retained_fixture((raw,), (candidate_id,), (message,), selected=candidate_id)
        stimulus = protocol.MatrixStimulus((), candidate_context, retained)
        evaluation = expected_evaluation(
            exact_finding("bounds", "CURRENT", "ACP.REPLAY.MISSING", "candidate-set"),
            protocol.Verdict.UNAVAILABLE,
            (),
            (protocol.StageCall("bounds", "candidate-set", 0),),
        )
    elif dimension == "reordering_duplication":
        stimulus = protocol.MatrixStimulus((raw, raw), candidate_context, None)
        evaluation = expected_evaluation(
            exact_finding(
                "canonical_identity",
                "CURRENT",
                "ACP.IDENTITY.DUPLICATE",
                f"candidate[{candidate_id}]",
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id, candidate_id), "canonical_identity"),
        )
    elif dimension == "substitution":
        hostile, expected_id, _ = candidate(payload=token, candidate_id="f" * 64)
        stimulus = protocol.MatrixStimulus((hostile,), context((expected_id,)), None)
        evaluation = expected_evaluation(
            exact_finding(
                "canonical_identity", "CURRENT", "ACP.IDENTITY.MISMATCH", "candidate[0].candidateId"
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((expected_id,), "canonical_identity"),
        )
    elif dimension == "cryptographic_eligibility":
        probes = (expected_probe(candidate_id, message, result=False),)
        crypto = expected_crypto_calls((candidate_id,), (message,), (False,))
        stimulus = protocol.MatrixStimulus((raw,), candidate_context, None)
        evaluation = expected_evaluation(
            exact_finding(
                "independent_trust",
                "CURRENT",
                "ACP.TRUST.SIGNATURE_INVALID",
                f"candidate[{candidate_id}]",
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "independent_trust"),
            crypto,
        )
        return MatrixVector(stimulus, evaluation, probes)
    elif dimension == "authorization_eligibility":
        probes = (expected_probe(candidate_id, message),)
        crypto = expected_crypto_calls((candidate_id,), (message,), (True,))
        stimulus = protocol.MatrixStimulus(
            (raw,), context((candidate_id,), authorized=frozenset()), None
        )
        evaluation = expected_evaluation(
            exact_finding(
                "authorization", "CURRENT", "ACP.AUTHORIZATION.DENIED", f"candidate[{candidate_id}]"
            ),
            protocol.Verdict.INVALID,
            (),
            pipeline_calls((candidate_id,), "authorization"),
            crypto,
        )
        return MatrixVector(stimulus, evaluation, probes)
    elif dimension == "graph_conflict_precedence":
        raw, candidate_id, message = candidate(payload=token, predecessor_id="f" * 64)
        probes = (expected_probe(candidate_id, message),)
        crypto = expected_crypto_calls((candidate_id,), (message,), (True,))
        stimulus = protocol.MatrixStimulus((raw,), context((candidate_id,)), None)
        evaluation = expected_evaluation(
            exact_finding(
                "graph_conflict", "CURRENT", "ACP.GRAPH.ORPHAN", f"candidate[{candidate_id}]"
            ),
            protocol.Verdict.INVALID,
            (candidate_id,),
            pipeline_calls((candidate_id,), "graph_conflict"),
            crypto,
            graph_calls=1,
        )
        return MatrixVector(stimulus, evaluation, probes)
    else:
        retained = replace(
            retained_fixture((raw,), (candidate_id,), (message,), selected=candidate_id),
            phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, protocol.Verdict.INVALID),
        )
        probes = (expected_probe(candidate_id, message),)
        crypto = expected_crypto_calls((candidate_id,), (message,), (True,))
        stimulus = protocol.MatrixStimulus((raw,), candidate_context, retained)
        evaluation = expected_evaluation(
            exact_finding("phase_verdict", "CURRENT", "ACP.REPLAY.EXACT_MISMATCH", "phaseVerdicts"),
            protocol.Verdict.INVALID,
            (candidate_id,),
            pipeline_calls((candidate_id,)),
            crypto,
            selected=candidate_id,
            graph_calls=1,
        )
        return MatrixVector(stimulus, evaluation, probes)
    return MatrixVector(stimulus, evaluation, no_crypto)


DIMENSION_MATERIALIZERS = {
    dimension: (lambda test_class, bound=dimension: hostile_matrix_vector(bound, test_class))
    for dimension in DIMENSIONS
}


def retained_wire(retained: protocol.RetainedEvaluation | None) -> object:
    if retained is None:
        return None
    return {
        "candidateSha256s": list(retained.candidate_sha256s),
        "evaluationPhase": retained.evaluation_phase.value,
        "evaluationTime": retained.evaluation_time,
        "trustedKeySha256s": [list(item) for item in retained.trusted_key_sha256s],
        "authorizedCandidateIds": list(retained.authorized_candidate_ids),
        "findings": [list(astuple(item)) for item in retained.findings],
        "phaseVerdicts": [
            [item.phase.value, item.verdict.value] for item in retained.phase_verdicts
        ],
        "eligibleCandidateIds": list(retained.eligible_candidate_ids),
        "selectedCandidateId": retained.selected_candidate_id,
        "stageCalls": [list(astuple(item)) for item in retained.stage_calls],
        "cryptoCalls": [list(astuple(item)) for item in retained.crypto_calls],
        "graphCallCount": retained.graph_call_count,
        "limits": {
            "candidates": retained.max_candidates,
            "candidateBytes": retained.max_candidate_bytes,
            "aggregateBytes": retained.max_aggregate_bytes,
            "jsonDepth": retained.max_json_depth,
            "jsonMembers": retained.max_json_members,
            "findings": retained.max_findings,
            "retainedMaterials": retained.max_retained_materials,
        },
    }


def matrix_fixture_bytes(dimension: str, test_class: str) -> bytes:
    stimulus = DIMENSION_MATERIALIZERS[dimension](test_class).stimulus
    return canonical(
        {
            "schemaVersion": "AdversarialMatrixStimulusV1",
            "candidateDocumentsHex": [item.hex() for item in stimulus.candidate_documents],
            "evaluationContext": {
                "expectedPhase": stimulus.context.expected_phase.value,
                "evaluationTime": stimulus.context.evaluation_time,
                "trustedPublicKeys": {
                    key: value.hex() for key, value in stimulus.context.trusted_public_keys.items()
                },
                "authorizedCandidateIds": sorted(stimulus.context.authorized_candidate_ids),
                "limits": {
                    "candidates": stimulus.context.max_candidates,
                    "candidateBytes": stimulus.context.max_candidate_bytes,
                    "aggregateBytes": stimulus.context.max_aggregate_bytes,
                    "jsonDepth": stimulus.context.max_json_depth,
                    "jsonMembers": stimulus.context.max_json_members,
                    "findings": stimulus.context.max_findings,
                    "retainedMaterials": stimulus.context.max_retained_materials,
                },
            },
            "retainedEvaluation": retained_wire(stimulus.retained),
        }
    )


def matrix_fixture_registry() -> dict[str, bytes]:
    return {
        f"fixture://{dimension}:{test_class}": matrix_fixture_bytes(dimension, test_class)
        for dimension in DIMENSIONS
        for test_class in TEST_CLASSES
    }


def expected_matrix_cases() -> tuple[protocol.MatrixCase, ...]:
    cases: list[protocol.MatrixCase] = []
    for dimension, stage, _, test_node, mutant, blocker in DIMENSION_CONTRACTS:
        for test_class in TEST_CLASSES:
            case_id = f"{dimension}:{test_class}"
            fixture_bytes = matrix_fixture_bytes(dimension, test_class)
            vector = DIMENSION_MATERIALIZERS[dimension](test_class)
            cases.append(
                protocol.MatrixCase(
                    case_id=case_id,
                    dimension=dimension,
                    test_class=test_class,
                    target_phase=vector.stimulus.context.expected_phase,
                    input_class=f"{dimension}.{test_class}",
                    input_reference=f"fixture://{case_id}",
                    input_sha256=hashlib.sha256(fixture_bytes).hexdigest(),
                    execution_mode=(
                        "reconstruct" if vector.stimulus.retained is not None else "evaluate"
                    ),
                    stage=(
                        vector.evaluation.findings[0].stage if vector.evaluation.findings else stage
                    ),
                    findings=vector.evaluation.findings,
                    phase_verdicts=vector.evaluation.phase_verdicts,
                    stage_calls=vector.evaluation.stage_calls,
                    crypto_expectations=tuple(
                        protocol.MatrixCryptoExpectation(
                            item.candidate_id,
                            item.signature_hex,
                            item.ordinal,
                            item.candidate_count,
                            protocol.Phase(item.phase),
                            item.public_key_sha256,
                            item.message_sha256,
                            item.result,
                        )
                        for item in vector.evaluation.crypto_calls
                    ),
                    graph_eligible=bool(vector.evaluation.eligible_candidate_ids),
                    graph_call_count=vector.evaluation.graph_call_count,
                    selected_candidate_reference=vector.evaluation.selected_candidate_id,
                    test_node=test_node,
                    mutant_id=mutant,
                    assertion_id=f"{test_node}::{case_id}::exact-outcome",
                    blocker_class=blocker,
                    evidence_state="RED_EXPECTED",
                )
            )
    return tuple(cases)


def resolved_matrix_contract(
    document: dict[str, Any], case: protocol.MatrixCase, vector: MatrixVector
) -> tuple[str, str, str | None, str | None, str, str]:
    contracts = document["materializedOutcomeContracts"]
    mode = contracts["dimensionExecutionModes"][case.dimension]
    if case.test_class == "boundary":
        boundary = contracts["materializedBoundaryContracts"][case.dimension]
        return (
            boundary["executionMode"],
            boundary["terminalStage"],
            None,
            None,
            boundary["verdict"],
            boundary["targetPhase"],
        )
    exception = contracts["exceptions"].get(case.case_id)
    if exception is not None:
        return (*exception, case.target_phase.value)
    if case.test_class in contracts["successClasses"]:
        return mode, "phase_verdict", None, None, "VALID", case.target_phase.value
    if case.test_class == "negative":
        resolved = contracts["dimensions"][case.dimension]
    elif case.test_class in contracts["reconstructionClassOverrides"] and mode == "reconstruct":
        resolved = (mode, *contracts["reconstructionClassOverrides"][case.test_class])
    else:
        precedence = contracts["classPrecedence"][case.test_class]
        resolved = (mode, *precedence[mode]) if isinstance(precedence, dict) else precedence
    resolved_mode, stage, code, location, verdict = resolved
    if location is not None and "exact-id" in location:
        candidate_id = strict_object(vector.stimulus.candidate_documents[0])["candidateId"]
        location = location.replace("exact-id", candidate_id)
    return resolved_mode, stage, code, location, verdict, case.target_phase.value


def test_matrix_cross_product_and_exact_outcomes_are_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert len(set(registry.values())) == EXPECTED_DISTINCT_FIXTURE_COUNT
    assert tuple(document["caseIndex"]) == tuple(case.case_id for case in expected)
    assert tuple(registry) == tuple(case.input_reference for case in expected)
    assert protocol.normalized_case_catalog(document) == expected
    forbidden_wire_keys = {
        "caseId",
        "dimension",
        "testClass",
        "inputClass",
        "hostileMutation",
        "expectedFindings",
        "mutantId",
    }
    modes = document["materializedOutcomeContracts"]["dimensionExecutionModes"]

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value).union(*(all_keys(item) for item in value.values()))
        if isinstance(value, list):
            return set().union(*(all_keys(item) for item in value))
        return set()

    def all_strings(value: object) -> set[str]:
        if isinstance(value, dict):
            return {item for key, nested in value.items() for item in (key, *all_strings(nested))}
        if isinstance(value, list):
            return set().union(*(all_strings(item) for item in value))
        return {value} if isinstance(value, str) else set()

    original_parse = protocol.parse_matrix_stimulus
    original_evaluate = protocol.evaluate_candidates
    original_reconstruct = protocol.reconstruct_candidates
    parser_calls: list[tuple[bytes, protocol.MatrixStimulusParse]] = []
    engine_calls: list[tuple[str, object, protocol.Evaluation]] = []
    execution_events: list[str] = []

    def observe_parse(raw: bytes) -> protocol.MatrixStimulusParse:
        parsed = original_parse(raw)
        if parsed.stimulus is not None:
            original = parsed.stimulus
            parsed = protocol.MatrixStimulusParse(
                protocol.MatrixStimulus(
                    tuple(list(original.candidate_documents)),
                    replace(original.context),
                    None if original.retained is None else replace(original.retained),
                ),
                parsed.findings,
            )
        parser_calls.append((raw, parsed))
        execution_events.append("parse")
        return parsed

    def observe_evaluate(
        documents: tuple[bytes, ...],
        *,
        context: protocol.EvaluationContext,
        crypto_verifier: protocol.CryptoVerifier,
    ) -> protocol.Evaluation:
        result = original_evaluate(documents, context=context, crypto_verifier=crypto_verifier)
        engine_calls.append(("evaluate", (documents, context, None, crypto_verifier), result))
        execution_events.append("evaluate")
        return result

    def observe_reconstruct(
        documents: tuple[bytes, ...],
        *,
        retained: protocol.RetainedEvaluation,
        context: protocol.EvaluationContext,
        crypto_verifier: protocol.CryptoVerifier,
    ) -> protocol.Evaluation:
        result = original_reconstruct(
            documents,
            retained=retained,
            context=context,
            crypto_verifier=crypto_verifier,
        )
        engine_calls.append(
            ("reconstruct", (documents, context, retained, crypto_verifier), result)
        )
        execution_events.append("reconstruct")
        return result

    monkeypatch.setattr(protocol, "parse_matrix_stimulus", observe_parse)
    monkeypatch.setattr(protocol, "evaluate_candidates", observe_evaluate)
    monkeypatch.setattr(protocol, "reconstruct_candidates", observe_reconstruct)
    observations: dict[str, protocol.MatrixObservation] = {}

    for case in expected:
        fixture = registry[case.input_reference]
        fixture_document = strict_object(fixture)
        assert not (all_keys(fixture_document) & forbidden_wire_keys)
        scalar_strings = all_strings(fixture_document)
        label = f"{case.dimension}:{case.test_class}"
        assert case.dimension not in scalar_strings
        assert case.test_class not in scalar_strings
        assert label not in scalar_strings
        assert hashlib.sha256(label.encode()).hexdigest() not in scalar_strings
        assert hashlib.sha256(fixture).hexdigest() == case.input_sha256
        vector = DIMENSION_MATERIALIZERS[case.dimension](case.test_class)
        mode, stage, code, location, verdict, target_phase = resolved_matrix_contract(
            document, case, vector
        )
        assert mode == case.execution_mode
        assert target_phase == case.target_phase.value
        assert stage == (case.findings[0].stage if case.findings else "phase_verdict")
        assert case.findings == (
            ()
            if code is None
            else exact_finding(stage, case.target_phase.value, code, cast(str, location))
        )
        assert (
            next(
                item.verdict.value
                for item in case.phase_verdicts
                if item.phase is case.target_phase
            )
            == verdict
        )
        assert case.execution_mode == modes[case.dimension]
        assert case.execution_mode == (
            "reconstruct" if vector.stimulus.retained is not None else "evaluate"
        )
        if case.test_class == "boundary":
            boundary_contract = document["materializedOutcomeContracts"][
                "materializedBoundaryContracts"
            ][case.dimension]
            assert boundary_contract == {
                "executionMode": case.execution_mode,
                "terminalStage": "phase_verdict",
                "finding": None,
                "verdict": "VALID",
                "targetPhase": case.target_phase.value,
            }
        if case.test_class == "malformed":
            assert vector.stimulus.candidate_documents == (b"{",)
        elif case.test_class == "deletion":
            assert vector.stimulus.candidate_documents == ()
        elif case.test_class == "duplication":
            assert len(vector.stimulus.candidate_documents) == 2
            assert len(set(vector.stimulus.candidate_documents)) == 1
        elif case.test_class == "maximum_cardinality":
            assert len(vector.stimulus.candidate_documents) == 4
        if case.dimension in {"deletion_corruption", "reconstruction_replay"}:
            assert vector.stimulus.retained is not None
        if case.dimension == "graph_conflict_precedence" and case.test_class in {
            "positive",
            "reordering",
            "maximum_cardinality",
            "negative",
            "boundary",
        }:
            assert any(
                strict_object(item)["predecessorId"] is not None
                for item in vector.stimulus.candidate_documents
            )
        spy = ExactCryptoSpy(list(vector.probes))
        prior_parse_count = len(parser_calls)
        prior_call_count = len(engine_calls)
        prior_event_count = len(execution_events)
        execution = protocol.execute_matrix_fixture(fixture, crypto_verifier=spy)
        assert execution.findings == ()
        assert execution.observation == protocol.MatrixObservation(
            case.input_sha256, vector.evaluation
        )
        assert execution.observation is not None
        assert len(parser_calls) == prior_parse_count + 1
        assert len(engine_calls) == prior_call_count + 1
        assert execution_events[prior_event_count:] == ["parse", case.execution_mode]
        parsed_raw, parsed = parser_calls[-1]
        assert parsed_raw == fixture
        assert parsed == protocol.MatrixStimulusParse(vector.stimulus, ())
        assert parsed.stimulus is not None
        called_mode, called_arguments, delegated_result = engine_calls[-1]
        assert called_mode == case.execution_mode
        documents, called_context, called_retained, called_verifier = cast(
            tuple[object, object, object, object], called_arguments
        )
        assert documents is parsed.stimulus.candidate_documents
        assert called_context is parsed.stimulus.context
        assert called_retained is parsed.stimulus.retained
        assert called_verifier is spy
        assert execution.observation.evaluation is delegated_result
        spy.assert_exhausted()
        assert tuple(hashlib.sha256(probe.message).hexdigest() for probe in spy.calls) == tuple(
            item.message_sha256 for item in case.crypto_expectations
        )
        observations[case.case_id] = execution.observation

    for index, source in enumerate(expected):
        target = next(
            candidate_case
            for offset in range(1, len(expected))
            if (candidate_case := expected[(index + offset) % len(expected)]).case_id
            != source.case_id
            and DIMENSION_MATERIALIZERS[candidate_case.dimension](
                candidate_case.test_class
            ).evaluation
            != observations[source.case_id].evaluation
        )
        assert (
            observations[source.case_id].evaluation
            != DIMENSION_MATERIALIZERS[target.dimension](target.test_class).evaluation
        )

    for dimension in DIMENSIONS:
        negative = observations[f"{dimension}:negative"].evaluation
        boundary = observations[f"{dimension}:boundary"].evaluation
        assert negative != boundary
        assert (
            DIMENSION_MATERIALIZERS[dimension]("negative").stimulus
            != DIMENSION_MATERIALIZERS[dimension]("boundary").stimulus
        )
    temporal_negative = DIMENSION_MATERIALIZERS["temporal_boundary"]("negative")
    temporal_boundary = DIMENSION_MATERIALIZERS["temporal_boundary"]("boundary")
    assert temporal_negative.stimulus.context.evaluation_time != (
        temporal_boundary.stimulus.context.evaluation_time
    )
    phase_negative = DIMENSION_MATERIALIZERS["phase_separation"]("negative")
    phase_boundary = DIMENSION_MATERIALIZERS["phase_separation"]("boundary")
    assert phase_negative.stimulus.context.expected_phase is protocol.Phase.CURRENT
    assert phase_boundary.stimulus.context.expected_phase is protocol.Phase.ACCEPTANCE
    crypto_negative = DIMENSION_MATERIALIZERS["cryptographic_eligibility"]("negative")
    crypto_boundary = DIMENSION_MATERIALIZERS["cryptographic_eligibility"]("boundary")
    assert tuple(result for _, result in crypto_negative.probes) == (False,)
    assert tuple(result for _, result in crypto_boundary.probes) == (True,)
    auth_negative = DIMENSION_MATERIALIZERS["authorization_eligibility"]("negative")
    auth_boundary = DIMENSION_MATERIALIZERS["authorization_eligibility"]("boundary")
    assert auth_negative.stimulus.context.authorized_candidate_ids == frozenset()
    assert auth_boundary.stimulus.context.authorized_candidate_ids
    graph_negative = DIMENSION_MATERIALIZERS["graph_conflict_precedence"]("negative")
    graph_boundary = DIMENSION_MATERIALIZERS["graph_conflict_precedence"]("boundary")
    assert len(graph_negative.stimulus.candidate_documents) == 1
    assert len(graph_boundary.stimulus.candidate_documents) == 2
    replay_negative = DIMENSION_MATERIALIZERS["reconstruction_replay"]("negative")
    replay_boundary = DIMENSION_MATERIALIZERS["reconstruction_replay"]("boundary")
    assert replay_negative.stimulus.retained != replay_boundary.stimulus.retained

    monkeypatch.undo()
    valid_document = strict_object(registry["fixture://validation_order:positive"])
    retained_document = strict_object(registry["fixture://reconstruction_replay:positive"])
    hostile_stimuli: list[tuple[bytes, str, str, str]] = [
        (b"\xff", "parse", "ACP.STIMULUS.INVALID_UTF8", "fixture"),
        (b"{", "parse", "ACP.STIMULUS.INVALID_JSON", "fixture"),
        (b"[]", "schema", "ACP.STIMULUS.OBJECT_REQUIRED", "fixture"),
    ]

    def changed_case(
        source: dict[str, Any], path: tuple[str, ...], value: object, code: str
    ) -> None:
        changed = json.loads(json.dumps(source))
        target = changed
        for segment in path[:-1]:
            target = target[segment]
        target[path[-1]] = value
        hostile_stimuli.append((canonical(changed), "schema", code, ".".join(path)))

    def missing_case(source: dict[str, Any], path: tuple[str, ...]) -> None:
        changed = json.loads(json.dumps(source))
        target = changed
        for segment in path[:-1]:
            target = target[segment]
        del target[path[-1]]
        hostile_stimuli.append(
            (canonical(changed), "schema", "ACP.STIMULUS.REQUIRED_FIELD", ".".join(path))
        )

    object_paths: tuple[tuple[dict[str, Any], tuple[str, ...]], ...] = (
        (valid_document, ()),
        (valid_document, ("evaluationContext",)),
        (valid_document, ("evaluationContext", "limits")),
        (retained_document, ("retainedEvaluation",)),
        (retained_document, ("retainedEvaluation", "limits")),
    )
    for source_document, path in object_paths:
        for key in document["fixtureContract"]["forbiddenRecursiveFields"]:
            changed_case(source_document, (*path, key), "forbidden", "ACP.STIMULUS.FORBIDDEN_FIELD")
        changed_case(source_document, (*path, "unknown"), "value", "ACP.STIMULUS.UNKNOWN_FIELD")

    top_fields = tuple(document["fixtureContract"]["orderedFields"])
    context_fields = (
        "expectedPhase",
        "evaluationTime",
        "trustedPublicKeys",
        "authorizedCandidateIds",
        "limits",
    )
    limit_fields = tuple(valid_document["evaluationContext"]["limits"])
    retained_fields = tuple(retained_document["retainedEvaluation"])
    typed_objects: tuple[tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]], ...] = (
        (valid_document, (), top_fields),
        (valid_document, ("evaluationContext",), context_fields),
        (valid_document, ("evaluationContext", "limits"), limit_fields),
        (retained_document, ("retainedEvaluation",), retained_fields),
        (retained_document, ("retainedEvaluation", "limits"), limit_fields),
    )
    for source_document, prefix, fields in typed_objects:
        for field in fields:
            missing_case(source_document, (*prefix, field))
            changed_case(source_document, (*prefix, field), True, "ACP.STIMULUS.TYPE")

    changed_case(valid_document, ("schemaVersion",), "OtherV1", "ACP.STIMULUS.SCHEMA_VERSION")
    changed_case(valid_document, ("candidateDocumentsHex",), ["zz"], "ACP.STIMULUS.HEX")
    changed_case(
        valid_document,
        ("evaluationContext", "expectedPhase"),
        "OTHER",
        "ACP.STIMULUS.ENUM",
    )
    trusted_id = next(iter(valid_document["evaluationContext"]["trustedPublicKeys"]))
    changed_case(
        valid_document,
        ("evaluationContext", "trustedPublicKeys", trusted_id),
        "zz",
        "ACP.STIMULUS.HEX",
    )
    for source_document, path, value, code in (
        (
            valid_document,
            ("evaluationContext", "trustedPublicKeys", "invalid-id"),
            "11" * 32,
            "ACP.STIMULUS.ID",
        ),
        (valid_document, ("candidateDocumentsHex",), [1], "ACP.STIMULUS.TYPE"),
        (
            valid_document,
            ("evaluationContext", "authorizedCandidateIds"),
            [1],
            "ACP.STIMULUS.TYPE",
        ),
        (
            retained_document,
            ("retainedEvaluation", "candidateSha256s"),
            ["short"],
            "ACP.STIMULUS.SHA256",
        ),
        (
            retained_document,
            ("retainedEvaluation", "trustedKeySha256s"),
            [["short"]],
            "ACP.STIMULUS.TUPLE_SHAPE",
        ),
        (
            retained_document,
            ("retainedEvaluation", "findings"),
            [["schema"]],
            "ACP.STIMULUS.TUPLE_SHAPE",
        ),
        (
            retained_document,
            ("retainedEvaluation", "phaseVerdicts"),
            [["CURRENT"]],
            "ACP.STIMULUS.TUPLE_SHAPE",
        ),
        (
            retained_document,
            ("retainedEvaluation", "stageCalls"),
            [["bounds", "candidate[0]"]],
            "ACP.STIMULUS.TUPLE_SHAPE",
        ),
        (
            retained_document,
            ("retainedEvaluation", "cryptoCalls"),
            [[]],
            "ACP.STIMULUS.TUPLE_SHAPE",
        ),
    ):
        changed_case(source_document, path, value, code)

    def duplicated(source: dict[str, Any], path: tuple[str, ...]) -> bytes:
        target: Any = source
        for segment in path[:-1]:
            target = target[segment]
        member = canonical(path[-1]).decode() + ":" + canonical(target[path[-1]]).decode()
        return canonical(source).replace(member.encode(), f"{member},{member}".encode(), 1)

    duplicate_objects: tuple[tuple[dict[str, Any], tuple[str, ...]], ...] = (
        (valid_document, ("schemaVersion",)),
        (valid_document, ("evaluationContext", "expectedPhase")),
        (valid_document, ("evaluationContext", "limits", "candidates")),
        (retained_document, ("retainedEvaluation", "evaluationPhase")),
    )
    for source_document, path in duplicate_objects:
        hostile_stimuli.append(
            (
                duplicated(source_document, path),
                "parse",
                "ACP.STIMULUS.DUPLICATE_MEMBER",
                ".".join(path),
            )
        )

    stimulus_cap = document["limits"]["stimulusBytes"]
    hostile_stimuli.append(
        (
            b"{" + b" " * stimulus_cap,
            "bounds",
            "ACP.BOUNDS.MATRIX_STIMULUS_BYTES",
            "fixture",
        )
    )
    parse_calls: list[tuple[bytes, protocol.MatrixStimulusParse]] = []
    unexpected_engines: list[str] = []
    unexpected_crypto: list[protocol.CryptoProbe] = []

    def observe_rejection_parse(raw: bytes) -> protocol.MatrixStimulusParse:
        result = original_parse(raw)
        parse_calls.append((raw, result))
        return result

    def unexpected_evaluate(*args: object, **kwargs: object) -> protocol.Evaluation:
        del args, kwargs
        unexpected_engines.append("evaluate")
        return DIMENSION_MATERIALIZERS["validation_order"]("positive").evaluation

    def observe_unexpected_crypto(probe: protocol.CryptoProbe) -> bool:
        unexpected_crypto.append(probe)
        return True

    monkeypatch.setattr(protocol, "parse_matrix_stimulus", observe_rejection_parse)
    monkeypatch.setattr(protocol, "evaluate_candidates", unexpected_evaluate)
    monkeypatch.setattr(protocol, "reconstruct_candidates", unexpected_evaluate)
    for raw, stage, code, location in hostile_stimuli:
        expected_findings = exact_finding(stage, "CURRENT", code, location)
        assert original_parse(raw) == protocol.MatrixStimulusParse(None, expected_findings)
        prior_parses = len(parse_calls)
        execution = protocol.execute_matrix_fixture(raw, crypto_verifier=observe_unexpected_crypto)
        assert execution == protocol.MatrixFixtureExecution(None, expected_findings)
        assert parse_calls[prior_parses:] == [
            (raw, protocol.MatrixStimulusParse(None, expected_findings))
        ]
        assert unexpected_engines == []
        assert unexpected_crypto == []

    valid_raw = canonical(valid_document)
    at_cap = valid_raw[:-1] + (b" " * (stimulus_cap - len(valid_raw))) + b"}"
    assert len(at_cap) == stimulus_cap
    parsed_at_cap = original_parse(at_cap)
    assert parsed_at_cap == protocol.MatrixStimulusParse(
        DIMENSION_MATERIALIZERS["validation_order"]("positive").stimulus, ()
    )
    prior_parses = len(parse_calls)
    at_cap_execution = protocol.execute_matrix_fixture(at_cap, crypto_verifier=ExactCryptoSpy([]))
    assert parse_calls[prior_parses:][0][0] == at_cap
    assert unexpected_engines == ["evaluate"]
    assert at_cap_execution == protocol.MatrixFixtureExecution(
        protocol.MatrixObservation(
            hashlib.sha256(at_cap).hexdigest(),
            DIMENSION_MATERIALIZERS["validation_order"]("positive").evaluation,
        ),
        (),
    )

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
        (("fixtureContract", "schemaVersion"), "OtherStimulusV1"),
        (("fixtureContract", "orderedFields"), ["schemaVersion"]),
        (("fixtureContract", "forbiddenRecursiveFields"), []),
        (("limits", "stimulusBytes"), 65535),
        (
            ("materializedOutcomeContracts", "dimensions", "authorization_eligibility", 2),
            "ACP.AUTHORIZATION.ALLOW",
        ),
        (
            ("materializedOutcomeContracts", "dimensionExecutionModes", "deletion_corruption"),
            "evaluate",
        ),
        (
            (
                "materializedOutcomeContracts",
                "materializedBoundaryContracts",
                "phase_separation",
                "targetPhase",
            ),
            "CURRENT",
        ),
        (
            ("materializedOutcomeContracts", "classPrecedence", "malformed", "reconstruct", 1),
            "ACP.PARSE.OTHER",
        ),
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
    assert_mutant(
        "MUT-DUPLICATE-BYPASS::exact-finding",
        duplicate,
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
        expected_calls = tuple(
            protocol.StageCall(PIPELINE[index], "candidate[0]", 0)
            for index in range(expected_stage_count)
        )
        if expected_stage_count == 1:
            assert_mutant(
                "MUT-ORDER-REORDER::exact-stage-ledger",
                result,
            )
        else:
            assert result.stage_calls == expected_calls
        assert result.crypto_calls == ()
        assert result.graph_call_count == 0


def test_lifecycle_and_explicit_time_boundaries_are_exact() -> None:
    for state in ("RETIRED", "REVOKED", "SUPERSEDED", "TERMINAL", "UNKNOWN"):
        raw, candidate_id, _ = candidate(lifecycle_state=state)
        result = protocol.evaluate_candidates(
            (raw,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
        )
        if state == "RETIRED":
            assert_mutant(
                "MUT-LIFECYCLE-REPLACE::exact-finding",
                result,
            )
        else:
            assert result.findings == exact_finding(
                "schema", "CURRENT", "ACP.LIFECYCLE.STATE", "candidate[0].lifecycleState"
            )
        assert result.stage_calls == pipeline_calls((candidate_id,), terminal="schema")
        assert result.crypto_calls == () and result.graph_call_count == 0

    raw, candidate_id, _ = candidate(lifecycle_operation="DELETE")
    illegal = protocol.evaluate_candidates(
        (raw,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert illegal.findings == exact_finding(
        "schema", "CURRENT", "ACP.LIFECYCLE.OPERATION", "candidate[0].lifecycleOperation"
    )
    assert illegal.stage_calls == pipeline_calls((candidate_id,), terminal="schema")
    missing_state = raw.replace(b'"lifecycleState":"ACTIVE",', b"")
    missing = protocol.evaluate_candidates(
        (missing_state,), context=context((candidate_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert missing.findings == exact_finding(
        "schema", "CURRENT", "ACP.SCHEMA.REQUIRED", "candidate[0].lifecycleState"
    )
    assert missing.stage_calls == pipeline_calls((candidate_id,), terminal="schema")

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
        if code == "ACP.TIME.OUTSIDE_WINDOW":
            assert_mutant(
                "MUT-TIME-BYPASS::exact-finding",
                result,
            )
        else:
            assert result.findings == exact_finding(
                "schema", "CURRENT", code, "candidate[0].validity"
            )
        assert result.stage_calls == pipeline_calls((candidate_id,), terminal="schema")
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
    assert stale.stage_calls == pipeline_calls((stale_id,), terminal="schema")

    for exact_time in ("2026-08-20T00:00:00Z", "2026-08-22T00:00:00Z"):
        raw, candidate_id, message = candidate()
        result = evaluate_with_spy(
            (raw,),
            context((candidate_id,), evaluation_time=exact_time),
            [expected_probe(candidate_id, message)],
        )
        assert result.findings == ()


def test_all_resource_bounds_cover_exact_n_and_n_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    items = tuple(candidate(payload=f"bounded-{index}", priority=index) for index in range(4))
    documents, ids, messages = tuple(zip(*items, strict=True))
    exact = evaluate_with_spy(
        documents,
        context(ids),
        [
            expected_probe(candidate_id, message, ordinal=index, count=4)
            for index, (candidate_id, message) in enumerate(zip(ids, messages, strict=True))
        ],
    )
    assert exact.findings == () and exact.graph_call_count == 1
    fifth, fifth_id, _ = candidate(payload="bounded-4", priority=4)
    over_count = protocol.evaluate_candidates(
        (*documents, fifth),
        context=context((*ids, fifth_id)),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert_mutant(
        "MUT-BOUNDS-BYPASS::exact-finding",
        over_count,
    )
    assert over_count.stage_calls == (protocol.StageCall("bounds", "candidate-set", 0),)

    raw, candidate_id, message = candidate()
    for bounded_context in (
        replace(context((candidate_id,)), max_candidate_bytes=len(raw)),
        replace(context((candidate_id,)), max_json_depth=1),
        replace(context((candidate_id,)), max_json_members=13),
    ):
        at_limit = evaluate_with_spy(
            (raw,), bounded_context, [expected_probe(candidate_id, message)]
        )
        assert at_limit.findings == () and at_limit.graph_call_count == 1
    second_raw, second_id, second_message = candidate(payload="aggregate-second")
    aggregate_limit = evaluate_with_spy(
        (raw, second_raw),
        replace(
            context((candidate_id, second_id)),
            max_aggregate_bytes=len(raw) + len(second_raw),
        ),
        [
            expected_probe(candidate_id, message, ordinal=0, count=2),
            expected_probe(second_id, second_message, ordinal=1, count=2),
        ],
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
    assert calls[0]["finding_count"] == 32
    assert calls[0]["retained_material_count"] == 4
    assert calls[0]["matrix_row_count"] == 130
    monkeypatch.undo()
    matrix_at_cap = matrix + b" " * (65536 - len(matrix))
    matrix_over_cap = matrix_at_cap + b" "
    freeze_at_cap = freeze + b" " * (32768 - len(freeze))
    freeze_over_cap = freeze_at_cap + b" "
    assert protocol.validate_matrix_bytes(matrix_at_cap, freeze).findings != exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.MATRIX_BYTES", "matrix"
    )
    assert protocol.validate_matrix_bytes(matrix_over_cap, freeze).findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.MATRIX_BYTES", "matrix"
    )
    assert protocol.validate_matrix_bytes(matrix, freeze_at_cap).findings != exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.FREEZE_BYTES", "freeze"
    )
    assert protocol.validate_matrix_bytes(matrix, freeze_over_cap).findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.FREEZE_BYTES", "freeze"
    )
    for field, value, code, location in (
        ("findingCount", 33, "ACP.BOUNDS.FINDING_COUNT", "findings"),
        ("retainedMaterialCount", 5, "ACP.BOUNDS.RETAINED_COUNT", "retained-materials"),
    ):
        document = matrix_document()
        document["limits"][field] = value
        bounded_result = protocol.validate_matrix_bytes(canonical(document), freeze)
        assert bounded_result.findings == exact_finding("bounds", "CURRENT", code, location)
    document = matrix_document()
    assert len(document["caseIndex"]) == 130
    document["caseIndex"].append("unknown:overflow")
    assert protocol.validate_matrix_bytes(canonical(document), freeze).findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.MATRIX_ROWS", "caseIndex"
    )


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
        if code == "ACP.PARSE.DUPLICATE_MEMBER":
            assert_mutant(
                "MUT-PARSE-REPLACE::exact-finding",
                result,
            )
        else:
            assert result.findings == exact_finding(stage, "CURRENT", code, location)
        assert result.stage_calls == pipeline_calls((candidate_id,), terminal=stage)
        assert result.crypto_calls == () and result.graph_call_count == 0


def test_identity_substitution_never_reaches_crypto() -> None:
    raw, expected_id, _ = candidate(candidate_id="f" * 64)
    result = protocol.evaluate_candidates(
        (raw,), context=context((expected_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert_mutant(
        "MUT-IDENTITY-BYPASS::exact-finding",
        result,
    )
    assert result.stage_calls == pipeline_calls((expected_id,), terminal="canonical_identity")
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
    assert result.stage_calls == pipeline_calls((unbound_id,), terminal="canonical_identity")
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
    spy.assert_exhausted()

    untrusted = protocol.EvaluationContext(
        expected_phase=protocol.Phase.CURRENT,
        trusted_public_keys={},
        authorized_candidate_ids=frozenset({candidate_id}),
        evaluation_time="2026-08-21T00:00:00Z",
    )
    rejected = protocol.evaluate_candidates(
        (raw,), context=untrusted, crypto_verifier=ExactCryptoSpy([])
    )
    assert_mutant(
        "MUT-SELF-TRUST-REPLACE::exact-finding",
        rejected,
    )
    assert rejected.current_verdict is protocol.Verdict.UNAVAILABLE
    assert rejected.stage_calls == pipeline_calls((candidate_id,), terminal="independent_trust")
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
    spy.assert_exhausted()

    unauthorized_spy = ExactCryptoSpy(
        [
            expected_probe(first_id, first_message, ordinal=0, count=2),
            expected_probe(second_id, second_message, ordinal=1, count=2),
        ]
    )
    unauthorized = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id), authorized=frozenset({first_id})),
        crypto_verifier=unauthorized_spy,
    )
    assert_mutant(
        "MUT-AUTH-BYPASS::exact-finding",
        unauthorized,
    )
    assert unauthorized.current_verdict is protocol.Verdict.INVALID
    assert unauthorized.stage_calls == pipeline_calls(
        (first_id, second_id), terminal="authorization"
    )
    assert unauthorized.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, True)
    )
    assert unauthorized.graph_call_count == 0
    unauthorized_spy.assert_exhausted()


def test_structured_crypto_probe_mixed_results_and_exception() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    mixed = evaluate_with_spy(
        (first, second),
        context((first_id, second_id)),
        [
            expected_probe(first_id, first_message, ordinal=0, count=2),
            expected_probe(second_id, second_message, ordinal=1, count=2, result=False),
        ],
    )
    assert mixed.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.SIGNATURE_INVALID", f"candidate[{second_id}]"
    )
    assert mixed.stage_calls == pipeline_calls((first_id, second_id), terminal="independent_trust")
    assert mixed.crypto_calls == expected_crypto_calls(
        (first_id, second_id), (first_message, second_message), (True, False)
    )
    assert mixed.graph_call_count == 0

    verifier_calls: list[protocol.CryptoProbe] = []

    def raising_verifier(probe: protocol.CryptoProbe) -> bool:
        assert probe == expected_probe(first_id, first_message)[0]
        verifier_calls.append(probe)
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
    assert verifier_calls == [expected_probe(first_id, first_message)[0]]

    malformed_key = protocol.evaluate_candidates(
        (first,),
        context=replace(context((first_id,)), trusted_public_keys={first_id: b"short"}),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert malformed_key.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.KEY_MALFORMED", f"candidate[{first_id}]"
    )
    assert malformed_key.stage_calls == pipeline_calls((first_id,), terminal="independent_trust")
    malformed_signature, _, _ = candidate(payload="first", priority=1, signature="aa")
    result = protocol.evaluate_candidates(
        (malformed_signature,), context=context((first_id,)), crypto_verifier=ExactCryptoSpy([])
    )
    assert result.findings == exact_finding(
        "schema", "CURRENT", "ACP.SCHEMA.SIGNATURE", "candidate[0].signature"
    )
    assert result.stage_calls == pipeline_calls((first_id,), terminal="schema")


def test_graph_fork_cycle_orphan_duplicate_and_permutation() -> None:
    root, root_id, root_message = candidate(payload="root", priority=1)
    first, first_id, first_message = candidate(payload="first", priority=2, predecessor_id=root_id)
    second, second_id, second_message = candidate(
        payload="second", priority=3, predecessor_id=root_id
    )
    fork = evaluate_with_spy(
        (root, first, second),
        context((root_id, first_id, second_id)),
        [
            expected_probe(root_id, root_message, ordinal=0, count=3),
            expected_probe(first_id, first_message, ordinal=1, count=3),
            expected_probe(second_id, second_message, ordinal=2, count=3),
        ],
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
    assert cycle.stage_calls == pipeline_calls(
        (unbound_first_id, unbound_second_id), terminal="canonical_identity"
    )
    assert cycle.crypto_calls == () and cycle.graph_call_count == 0
    orphan, orphan_id, orphan_message = candidate(predecessor_id="f" * 64)
    orphaned = evaluate_with_spy(
        (orphan,), context((orphan_id,)), [expected_probe(orphan_id, orphan_message)]
    )
    assert orphaned.findings == exact_finding(
        "graph_conflict", "CURRENT", "ACP.GRAPH.ORPHAN", f"candidate[{orphan_id}]"
    )


def test_graph_result_is_permutation_invariant() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    forward = evaluate_with_spy(
        (first, second),
        context((first_id, second_id)),
        [
            expected_probe(first_id, first_message, ordinal=0, count=2),
            expected_probe(second_id, second_message, ordinal=1, count=2),
        ],
    )
    reverse = evaluate_with_spy(
        (second, first),
        context((first_id, second_id)),
        [
            expected_probe(second_id, second_message, ordinal=0, count=2),
            expected_probe(first_id, first_message, ordinal=1, count=2),
        ],
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
    assert_mutant(
        "MUT-PRECEDENCE-REPLACE::exact-selection",
        forward,
    )
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
    assert_mutant(
        "MUT-PHASE-REPLACE::exact-finding",
        result,
    )
    assert result.stage_calls == pipeline_calls((candidate_id,), terminal="schema")
    assert result.historical_verdict is protocol.Verdict.UNAVAILABLE
    assert result.current_verdict is protocol.Verdict.INVALID
    assert result.crypto_calls == ()
    assert result.graph_call_count == 0


def test_all_three_phases_are_exact_and_isolated() -> None:
    for phase in protocol.Phase:
        raw, candidate_id, message = candidate(phase=phase.value)
        result = evaluate_with_spy(
            (raw,),
            context((candidate_id,), phase=phase),
            [expected_probe(candidate_id, message, phase=phase)],
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
    exact = reconstruct_with_spy(
        (raw,),
        retained,
        context((candidate_id,)),
        [expected_probe(candidate_id, message)],
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
        spy.assert_exhausted()

    mismatch = reconstruct_with_spy(
        (raw,),
        retained,
        context((candidate_id,)),
        [expected_probe(candidate_id, message, result=False)],
    )
    assert_mutant(
        "MUT-REPLAY-SUBSET::exact-finding",
        mismatch,
    )


def test_reconstruction_rejects_missing_extra_corrupt_and_substituted_inputs() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    retained = retained_fixture((first,), (first_id,), (first_message,), selected=first_id)
    well_formed_corruption = first.replace(b'"payload":"first"', b'"payload":"firsx"')
    cases = (
        (
            (),
            "bounds",
            "ACP.REPLAY.MISSING",
            "candidate-set",
            (protocol.StageCall("bounds", "candidate-set", 0),),
        ),
        (
            (first, second),
            "bounds",
            "ACP.REPLAY.EXTRA",
            "candidate-set",
            (protocol.StageCall("bounds", "candidate-set", 0),),
        ),
        (
            (first[:-1],),
            "parse",
            "ACP.PARSE.INVALID_JSON",
            "candidate[0]",
            pipeline_calls((first_id,), "parse"),
        ),
        (
            (well_formed_corruption,),
            "canonical_identity",
            "ACP.REPLAY.CORRUPT",
            "candidate[0]",
            pipeline_calls((first_id,), "canonical_identity"),
        ),
        (
            (first, first),
            "canonical_identity",
            "ACP.REPLAY.DUPLICATE",
            f"candidate[{first_id}]",
            pipeline_calls((first_id, first_id), "canonical_identity"),
        ),
        (
            (second,),
            "canonical_identity",
            "ACP.REPLAY.IDENTITY_MISMATCH",
            "candidate[0]",
            pipeline_calls((second_id,), "canonical_identity"),
        ),
    )
    for documents, stage, code, location, expected_calls in cases:
        result = protocol.reconstruct_candidates(
            documents,
            retained=retained,
            context=context((first_id, second_id)),
            crypto_verifier=ExactCryptoSpy([]),
        )
        assert result.findings == exact_finding(stage, "CURRENT", code, location)
        assert result.stage_calls == expected_calls
        assert result.crypto_calls == () and result.graph_call_count == 0
    assert_mutant(
        "MUT-SUBSTITUTION-REMOVE::exact-finding",
        result,
    )

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
    assert cross_phase.stage_calls == pipeline_calls((first_id,), "schema")

    self_trust = protocol.reconstruct_candidates(
        (first,),
        retained=retained,
        context=replace(context((first_id,)), trusted_public_keys={}),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert self_trust.findings == exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.KEY_UNAVAILABLE", f"candidate[{first_id}]"
    )
    assert self_trust.stage_calls == pipeline_calls((first_id,), "independent_trust")

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
    assert reordered.stage_calls == pipeline_calls((second_id, first_id), "canonical_identity")
    assert reordered.crypto_calls == () and reordered.graph_call_count == 0

    wrong_verdicts = replace(
        retained,
        phase_verdicts=phase_verdicts(protocol.Phase.CURRENT, protocol.Verdict.INVALID),
    )
    mismatch = reconstruct_with_spy(
        (first,),
        wrong_verdicts,
        context((first_id,)),
        [expected_probe(first_id, first_message)],
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
    mutant_identity = {
        "outcomes": document["mutantOutcomes"],
        "executionClaims": document["mutantExecutionClaims"],
    }
    assert hashlib.sha256(canonical(mutant_identity)).hexdigest() == EXPECTED_MUTANT_OUTCOMES_SHA256
    assert {outcome["id"] for outcome in document["mutantOutcomes"]} == expected
    mutants_by_id = {mutant["id"]: mutant for mutant in mutants}
    outcomes_by_id = {outcome["id"]: outcome for outcome in document["mutantOutcomes"]}
    assert len({mutant["assertionId"] for mutant in mutants}) == len(mutants)
    assert {item["id"]: item["assertionId"] for item in mutants} == MUTANT_ASSERTION_IDS
    syntax = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in syntax.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    bound_assertions: dict[str, str] = {}
    for mutant in mutants:
        kill_test = functions[mutant["killTest"]]
        calls = [
            node
            for node in ast.walk(kill_test)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "assert_mutant"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ]
        matching = [
            call
            for call in calls
            if cast(ast.Constant, call.args[0]).value == mutant["assertionId"]
        ]
        assert len(matching) == 1
        assert matching[0].keywords == []
        assertion = cast(ast.Constant, matching[0].args[0]).value
        assert isinstance(assertion, str)
        bound_assertions[mutant["id"]] = assertion
    assert bound_assertions == MUTANT_ASSERTION_IDS
    assert set(document["mutantExecutionClaims"]) == expected
    assert all(
        set(claim)
        == {
            "stageCalls",
            "cryptoCalls",
            "eligibleCandidateIds",
            "selectedCandidateId",
            "graphCallCount",
        }
        for claim in document["mutantExecutionClaims"].values()
    )
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
