from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.quality.semantic_closure import Classification, evaluate_closure
from scripts.quality import verify_issue280_output_correctness as issue280_verifier


HEAD = "f93653e8a11e697c88766b207fb01c18662339d6"


def valid_matrix() -> dict[str, object]:
    return {
        "schemaVersion": "SemanticClosureMatrixV1",
        "subject": "issue-280",
        "reviewedHead": HEAD,
        "requiredAtomicRowIds": ["STRUCT-1", "SEM-1"],
        "reviewFans": [
            {
                "id": "pm-ai-shipping:intended-vs-implemented",
                "reviewer": "intent-reviewer",
                "evidenceId": "intent-evidence",
                "exactHead": HEAD,
                "executionMode": "analytical",
            },
            {
                "id": "output-correctness",
                "reviewer": "execution-reviewer",
                "evidenceId": "execution-evidence",
                "exactHead": HEAD,
                "executionMode": "non-read-only",
            },
        ],
        "atomicRows": [
            {
                "id": "STRUCT-1",
                "claimKind": "structural",
                "requiredForClosure": True,
                "classification": "STRUCTURAL_PASS",
                "evidenceHead": HEAD,
                "evidenceFan": "pm-ai-shipping:intended-vs-implemented",
                "observation": "Schema parsed.",
            },
            {
                "id": "SEM-1",
                "claimKind": "semantic",
                "requiredForClosure": True,
                "classification": "SEMANTIC_PASS",
                "evidenceHead": HEAD,
                "evidenceFan": "output-correctness",
                "observation": "User-visible meaning matched the semantic oracle.",
            },
        ],
    }


def test_canonical_classifications_are_exact_and_load_bearing() -> None:
    assert {item.value for item in Classification} == {
        "STRUCTURAL_PASS",
        "SEMANTIC_PASS",
        "NOT_PROVEN",
        "FAILED",
    }
    assert evaluate_closure(valid_matrix(), expected_head=HEAD).closed is True


@pytest.mark.parametrize("classification", ["NOT_PROVEN", "FAILED"])
def test_non_passing_atomic_row_forces_non_closure(classification: str) -> None:
    matrix = valid_matrix()
    matrix["atomicRows"][1]["classification"] = classification  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert f"SEM-1:{classification}" in result.reasons


def test_editable_aggregate_satisfaction_claim_is_rejected() -> None:
    matrix = valid_matrix()
    matrix["satisfied"] = True

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "editable-aggregate-key:satisfied" in result.reasons


def test_structural_pass_cannot_satisfy_semantic_row() -> None:
    matrix = valid_matrix()
    matrix["atomicRows"][1]["classification"] = "STRUCTURAL_PASS"  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "SEM-1:semantic-requires-SEMANTIC_PASS" in result.reasons


def test_stale_row_and_fan_evidence_fail_exact_head_binding() -> None:
    matrix = valid_matrix()
    matrix["atomicRows"][1]["evidenceHead"] = "0" * 40  # type: ignore[index]
    matrix["reviewFans"][1]["exactHead"] = "0" * 40  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "SEM-1:stale-evidence-head" in result.reasons
    assert "output-correctness:stale-review-head" in result.reasons


def test_missing_required_atomic_row_fails_partial_execution() -> None:
    matrix = valid_matrix()
    matrix["atomicRows"] = matrix["atomicRows"][:-1]  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "missing-required-row:SEM-1" in result.reasons


def test_output_correctness_fan_must_be_non_read_only() -> None:
    matrix = valid_matrix()
    matrix["reviewFans"][1]["executionMode"] = "read-only"  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "output-correctness:must-be-non-read-only" in result.reasons


def test_review_fans_must_have_independent_reviewer_and_evidence() -> None:
    matrix = valid_matrix()
    matrix["reviewFans"][1]["reviewer"] = "intent-reviewer"  # type: ignore[index]
    matrix["reviewFans"][1]["evidenceId"] = "intent-evidence"  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "review-fans:not-independent" in result.reasons


def test_unknown_classification_fails_closed() -> None:
    matrix = valid_matrix()
    matrix["atomicRows"][1]["classification"] = "EXECUTABLE_CONTRACT_PASS"  # type: ignore[index]

    result = evaluate_closure(matrix, expected_head=HEAD)

    assert result.closed is False
    assert "SEM-1:unknown-classification" in result.reasons


def test_mutations_cannot_turn_known_issue280_failures_into_closure() -> None:
    baseline = valid_matrix()
    baseline["requiredAtomicRowIds"] = ["TRANSLATION", "AUDIENCE"]
    baseline["atomicRows"] = [
        {
            "id": "TRANSLATION",
            "claimKind": "semantic",
            "requiredForClosure": True,
            "classification": "FAILED",
            "evidenceHead": HEAD,
            "evidenceFan": "output-correctness",
            "observation": "308 of 525 combinations returned ISSUE280_TRANSLATION_REFUSED.",
        },
        {
            "id": "AUDIENCE",
            "claimKind": "semantic",
            "requiredForClosure": True,
            "classification": "FAILED",
            "evidenceHead": HEAD,
            "evidenceFan": "output-correctness",
            "observation": "All successful groups emitted identical text for seven audiences.",
        },
    ]
    mutations = []
    aggregate = deepcopy(baseline)
    aggregate["status"] = "PASSED"
    mutations.append(aggregate)
    partial = deepcopy(baseline)
    partial["atomicRows"] = partial["atomicRows"][:1]  # type: ignore[index]
    mutations.append(partial)
    structural = deepcopy(baseline)
    structural["atomicRows"][0]["classification"] = "STRUCTURAL_PASS"  # type: ignore[index]
    mutations.append(structural)

    for matrix in mutations:
        assert evaluate_closure(matrix, expected_head=HEAD).closed is False


def test_issue280_verifier_locks_the_required_semantic_row_set() -> None:
    assert issue280_verifier.SEMANTIC_CLOSURE_ROW_IDS == (
        "R280-AUDIENCE-001",
        "R280-DEPTH-002",
        "R280-AUDIENCE-DEPTH-001",
        "R280-S6-001",
        "R280-CONVERSION-001",
        "R280-QUALITY-001",
        "R280-OUTPUT-CORRECTNESS-001",
    )


def test_issue280_verifier_exits_nonzero_for_forensic_failed_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = valid_matrix()
    atomic_rows = matrix["atomicRows"]
    assert isinstance(atomic_rows, list)
    second_row = atomic_rows[1]
    assert isinstance(second_row, dict)
    path = tmp_path / "matrix.json"
    path.write_text(
        json.dumps({"semanticClosure": matrix | {
            "atomicRows": [
                atomic_rows[0],
                second_row | {"classification": "NOT_PROVEN"},
            ]
        }}),
        encoding="utf-8",
    )
    monkeypatch.setattr(issue280_verifier, "MATRIX_PATH", path)

    assert issue280_verifier.main(["--expected-head", HEAD]) == 1
