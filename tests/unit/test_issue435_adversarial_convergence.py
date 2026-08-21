"""Fixed independent RED oracle for Issue #435 adversarial convergence."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from scripts.quality import issue435_adversarial_convergence as protocol


ROOT = Path(__file__).parents[2]
MATRIX_PATH = ROOT / "docs/governance/adversarial-convergence-invariant-matrix-v1.json"
FREEZE_PATH = ROOT / "docs/governance/adversarial-convergence-red-freeze-v1.json"
DOMAIN = b"NARRATWIN:ACP:CANDIDATE:V1\x00"
EXPECTED_SEMANTIC_SHA256 = "ae9abdf8136d444f5cb5425a3d477026473329cc210b997ecf96cfdce09906f7"
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
    freeze = {
        "schemaVersion": "AdversarialRedFreezeV1",
        "matrixId": "issue-435-adversarial-convergence-v1",
        "redHead": "1" * 40,
        "matrixBlobOid": "2" * 40,
        "matrixSha256": matrix_sha,
        "testBlobOid": "3" * 40,
        "testSha256": test_sha,
        "semanticSha256": semantic_sha,
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
        "blockers": {"implementation": 0, "evidence": 0},
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
    signature: str = "aa" * 64,
    candidate_id: str | None = None,
) -> tuple[bytes, str, bytes]:
    identity_fields: dict[str, object] = {
        "schemaVersion": "AdversarialCandidateV1",
        "phase": phase,
        "payload": payload,
        "predecessorId": predecessor_id,
        "priority": priority,
    }
    message = DOMAIN + canonical(identity_fields)
    expected_id = hashlib.sha256(message).hexdigest()
    document = {
        "schemaVersion": "AdversarialCandidateV1",
        "candidateId": candidate_id or expected_id,
        "phase": phase,
        "payload": payload,
        "predecessorId": predecessor_id,
        "priority": priority,
        "signature": signature,
    }
    return canonical(document), expected_id, message


class ExactCryptoSpy:
    def __init__(self, expected: list[tuple[bytes, bytes, bytes, bool]]) -> None:
        self.expected = expected
        self.calls: list[tuple[bytes, bytes, bytes]] = []

    def __call__(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        ordinal = len(self.calls)
        expected_key, expected_message, expected_signature, result = self.expected[ordinal]
        assert (public_key, message, signature) == (
            expected_key,
            expected_message,
            expected_signature,
        )
        self.calls.append((public_key, message, signature))
        return result


def context(
    candidate_ids: tuple[str, ...],
    *,
    phase: protocol.Phase = protocol.Phase.CURRENT,
    authorized: frozenset[str] | None = None,
    max_candidates: int = 4,
) -> protocol.EvaluationContext:
    return protocol.EvaluationContext(
        expected_phase=phase,
        trusted_public_keys={
            candidate_id: bytes.fromhex("11" * 32) for candidate_id in candidate_ids
        },
        authorized_candidate_ids=authorized if authorized is not None else frozenset(candidate_ids),
        evaluation_time="2026-08-21T00:00:00Z",
        max_candidates=max_candidates,
    )


def exact_finding(stage: str, phase: str, code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding(stage, phase, code, location),)


def test_matrix_cross_product_and_exact_outcomes_are_closed() -> None:
    document = matrix_document()
    assert tuple(document["pipeline"]) == PIPELINE
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
        == 120
    )
    result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), synthetic_freeze(document))
    assert result.findings == ()
    assert result.semantic_sha256 == EXPECTED_SEMANTIC_SHA256
    assert result.invariant_ids == tuple(invariant["id"] for invariant in invariants)
    assert result.blocker_classes == (
        protocol.BlockerClass.IMPLEMENTATION,
        protocol.BlockerClass.EVIDENCE,
    )


def test_closed_universe_shrink_fails_exactly() -> None:
    document = matrix_document()
    document["closedUniverses"]["dimensions"].pop()
    result = protocol.validate_matrix_bytes(
        canonical(document), synthetic_freeze(matrix_document())
    )
    assert result.findings == exact_finding(
        "matrix", "CURRENT", "ACP.MATRIX.UNIVERSE_MISMATCH", "closedUniverses.dimensions"
    )


def test_duplicate_json_member_fails_before_identity() -> None:
    raw, candidate_id, _ = candidate()
    duplicate = raw[:-1] + b',"phase":"CURRENT"}'
    spy = ExactCryptoSpy([])
    result = protocol.evaluate_candidates(
        (duplicate,), context=context((candidate_id,)), crypto_verifier=spy
    )
    assert result.findings == exact_finding(
        "parse", "CURRENT", "ACP.PARSE.DUPLICATE_MEMBER", "candidate[0].phase"
    )
    assert result.current_verdict is protocol.Verdict.INVALID
    assert result.stage_calls == (
        protocol.StageCall("bounds", "candidate[0]", 0),
        protocol.StageCall("parse", "candidate[0]", 0),
    )
    assert result.crypto_calls == ()
    assert result.graph_call_count == 0
    assert spy.calls == []


def test_bounds_n_plus_one_stops_before_all_work() -> None:
    documents_and_ids = [candidate(payload=f"candidate-{index}") for index in range(5)]
    documents = tuple(item[0] for item in documents_and_ids)
    ids = tuple(item[1] for item in documents_and_ids)
    result = protocol.evaluate_candidates(
        documents,
        context=context(ids, max_candidates=4),
        crypto_verifier=ExactCryptoSpy([]),
    )
    assert result.findings == exact_finding(
        "bounds", "CURRENT", "ACP.BOUNDS.CANDIDATE_COUNT", "candidate-set"
    )
    assert result.current_verdict is protocol.Verdict.INVALID
    assert result.stage_calls == (protocol.StageCall("bounds", "candidate-set", 0),)
    assert result.crypto_calls == ()
    assert result.graph_call_count == 0


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
        assert len(result.stage_calls) == expected_stage_count
        assert result.crypto_calls == ()
        assert result.graph_call_count == 0


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


def test_crypto_spy_ledger_is_exact_and_self_trust_fails() -> None:
    raw, candidate_id, message = candidate()
    signature = bytes.fromhex("aa" * 64)
    key = bytes.fromhex("11" * 32)
    spy = ExactCryptoSpy([(key, message, signature, True)])
    result = protocol.evaluate_candidates(
        (raw,), context=context((candidate_id,)), crypto_verifier=spy
    )
    assert result.findings == ()
    assert result.crypto_calls == (
        protocol.CryptoCall(candidate_id, signature.hex(), 0, 1, "CURRENT", True),
    )
    assert result.eligible_candidate_ids == (candidate_id,)
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
    key = bytes.fromhex("11" * 32)
    signature = bytes.fromhex("aa" * 64)
    spy = ExactCryptoSpy(
        [
            (key, first_message, signature, True),
            (key, second_message, signature, True),
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
    assert result.graph_call_count == 1

    unauthorized = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id), authorized=frozenset({first_id})),
        crypto_verifier=ExactCryptoSpy(
            [
                (key, first_message, signature, True),
                (key, second_message, signature, True),
            ]
        ),
    )
    assert unauthorized.findings == exact_finding(
        "authorization", "CURRENT", "ACP.AUTHORIZATION.DENIED", f"candidate[{second_id}]"
    )
    assert unauthorized.current_verdict is protocol.Verdict.INVALID
    assert unauthorized.graph_call_count == 0


def test_graph_result_is_permutation_invariant() -> None:
    first, first_id, first_message = candidate(payload="first", priority=1)
    second, second_id, second_message = candidate(payload="second", priority=2)
    key = bytes.fromhex("11" * 32)
    signature = bytes.fromhex("aa" * 64)
    forward = protocol.evaluate_candidates(
        (first, second),
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [(key, first_message, signature, True), (key, second_message, signature, True)]
        ),
    )
    reverse = protocol.evaluate_candidates(
        (second, first),
        context=context((first_id, second_id)),
        crypto_verifier=ExactCryptoSpy(
            [(key, second_message, signature, True), (key, first_message, signature, True)]
        ),
    )
    assert (
        forward.findings,
        forward.historical_verdict,
        forward.current_verdict,
        forward.eligible_candidate_ids,
        forward.graph_call_count,
    ) == (
        reverse.findings,
        reverse.historical_verdict,
        reverse.current_verdict,
        reverse.eligible_candidate_ids,
        reverse.graph_call_count,
    )
    assert forward.current_verdict is protocol.Verdict.VALID
    assert forward.eligible_candidate_ids == tuple(sorted((first_id, second_id)))


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


def test_exact_findings_and_historical_current_verdicts_are_equal() -> None:
    raw, candidate_id, message = candidate()
    key = bytes.fromhex("11" * 32)
    signature = bytes.fromhex("aa" * 64)
    first = protocol.evaluate_candidates(
        (raw,),
        context=context((candidate_id,)),
        crypto_verifier=ExactCryptoSpy([(key, message, signature, False)]),
    )
    replay = protocol.evaluate_candidates(
        (raw,),
        context=context((candidate_id,)),
        crypto_verifier=ExactCryptoSpy([(key, message, signature, False)]),
    )
    expected = exact_finding(
        "independent_trust", "CURRENT", "ACP.TRUST.SIGNATURE_INVALID", f"candidate[{candidate_id}]"
    )
    assert first.findings == expected
    assert replay.findings == expected
    assert (first.historical_verdict, first.current_verdict) == (
        protocol.Verdict.UNAVAILABLE,
        protocol.Verdict.INVALID,
    )
    assert (replay.historical_verdict, replay.current_verdict) == (
        protocol.Verdict.UNAVAILABLE,
        protocol.Verdict.INVALID,
    )


def test_activation_authority_and_successor_boundaries_fail_exactly() -> None:
    for field, value, code in (
        ("activation", "ACTIVE", "ACP.BOUNDARY.ACTIVATION"),
        ("authorityEffect", "AUTHORITY_CREATED", "ACP.BOUNDARY.AUTHORITY_EFFECT"),
    ):
        document = matrix_document()
        document[field] = value
        result = protocol.validate_matrix_bytes(
            canonical(document), synthetic_freeze(matrix_document())
        )
        assert result.findings == exact_finding("matrix", "CURRENT", code, field)

    document = matrix_document()
    document["prohibitedCapabilities"].remove("issue_432")
    result = protocol.validate_matrix_bytes(
        canonical(document), synthetic_freeze(matrix_document())
    )
    assert result.findings == exact_finding(
        "matrix", "CURRENT", "ACP.BOUNDARY.PROHIBITION_MISSING", "prohibitedCapabilities.issue_432"
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


def test_freeze_overlay_is_closed_exact_and_distinct() -> None:
    document = matrix_document()
    valid = strict_object(synthetic_freeze(document))
    duplicate_identities = deepcopy(valid)
    duplicate_identities["reviewers"][2]["identity"] = duplicate_identities["reviewers"][1][
        "identity"
    ]
    result = protocol.validate_matrix_bytes(
        MATRIX_PATH.read_bytes(), canonical(duplicate_identities)
    )
    assert result.findings == exact_finding(
        "freeze", "CURRENT", "ACP.FREEZE.REVIEWER_NOT_DISTINCT", "reviewers[2].identity"
    )
    missing = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), None)
    assert missing.findings == exact_finding(
        "freeze", "CURRENT", "ACP.FREEZE.MISSING", "adversarial-convergence-red-freeze-v1.json"
    )


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


def test_sensitive_route_without_matrix_and_freeze_fails_exactly(tmp_path: Path) -> None:
    preflight = tmp_path / "docs/governance/preflights/issue-900.json"
    preflight.parent.mkdir(parents=True)
    preflight.write_text(
        json.dumps(
            {
                "schema_version": "GovernancePreflightV1",
                "issue_number": 900,
                "branch": "process-900-security-sensitive",
                "objective": "security and replay work",
                "status_decision": "update-minimally",
                "scope": {
                    "required": ["docs/STATUS.md"],
                    "allowed_prefixes": ["docs/STATUS.md"],
                    "forbidden": [],
                },
            }
        ),
        encoding="utf-8",
    )
    findings = protocol.route_findings(
        tmp_path, changed_paths=("docs/governance/preflights/issue-900.json",)
    )
    assert findings == (
        protocol.Finding(
            "route",
            "CURRENT",
            "ACP.ROUTE.MATRIX_REQUIRED",
            "docs/governance/preflights/issue-900.json",
        ),
        protocol.Finding(
            "route",
            "CURRENT",
            "ACP.ROUTE.FREEZE_REQUIRED",
            "docs/governance/preflights/issue-900.json",
        ),
    )


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
        "MUT-REPLAY-SUBSET",
    }
    assert {mutant["id"] for mutant in mutants} == expected
    missing_or_duplicate = tuple(
        mutant["anchor"] for mutant in mutants if source.count(mutant["anchor"]) != 1
    )
    assert missing_or_duplicate == ()
    assert all(mutant["action"] in {"remove", "bypass", "reorder", "replace"} for mutant in mutants)


def test_repository_artifacts_join_only_after_c3_freeze() -> None:
    if not FREEZE_PATH.exists():
        result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), None)
        assert result.findings == exact_finding(
            "freeze", "CURRENT", "ACP.FREEZE.MISSING", "adversarial-convergence-red-freeze-v1.json"
        )
        return
    result = protocol.validate_matrix_bytes(MATRIX_PATH.read_bytes(), FREEZE_PATH.read_bytes())
    assert result.findings == ()
    assert result.semantic_sha256 == EXPECTED_SEMANTIC_SHA256
