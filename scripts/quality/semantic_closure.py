"""Fail-closed semantic closure computed from atomic evidence rows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence


class Classification(str, Enum):
    STRUCTURAL_PASS = "STRUCTURAL_PASS"
    SEMANTIC_PASS = "SEMANTIC_PASS"
    NOT_PROVEN = "NOT_PROVEN"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ClosureResult:
    closed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class OutputCorrectnessExecution:
    """Result returned by an invoked, non-read-only semantic verifier."""

    exact_head: str
    reviewer: str
    evidence_id: str
    execution_mode: str
    classifications: Mapping[str, Classification]
    observations: Mapping[str, str]


_REQUIRED_FANS = {
    "pm-ai-shipping:intended-vs-implemented",
    "output-correctness",
}
_EDITABLE_AGGREGATE_KEYS = {
    "complete",
    "completed",
    "iscomplete",
    "issatisfied",
    "issue280satisfiedbypre",
    "passed",
    "satisfied",
    "status",
}


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _is_editable_aggregate(key: str) -> bool:
    normalized = "".join(character for character in key.lower() if character.isalnum())
    return (
        normalized in _EDITABLE_AGGREGATE_KEYS
        or normalized.endswith("satisfied")
        or normalized.endswith("satisfiedbypre")
        or normalized.endswith("implemented")
    )


def evaluate_closure(
    matrix: Mapping[str, object],
    *,
    expected_head: str,
    expected_row_ids: Sequence[str] | None = None,
    output_correctness_verifier: Callable[[], OutputCorrectnessExecution] | None = None,
) -> ClosureResult:
    """Evaluate closure without trusting aggregate pass/satisfaction fields."""

    reasons: list[str] = []

    for key in matrix:
        if _is_editable_aggregate(key):
            reasons.append(f"editable-aggregate-key:{key}")

    if matrix.get("schemaVersion") != "SemanticClosureMatrixV1":
        reasons.append("invalid-schema-version")
    if _text(matrix.get("reviewedHead")) != expected_head:
        reasons.append("matrix:stale-reviewed-head")

    declared = matrix.get("requiredAtomicRowIds")
    declared_ids = (
        declared
        if isinstance(declared, list)
        and all(isinstance(item, str) and item for item in declared)
        and len(declared) == len(set(declared))
        else []
    )
    if not declared_ids:
        reasons.append("required-row-ids:missing-or-invalid")

    authoritative_ids = list(expected_row_ids) if expected_row_ids is not None else list(declared_ids)
    if expected_row_ids is not None and set(declared_ids) != set(authoritative_ids):
        reasons.append("required-row-ids:contract-mismatch")

    fans_value = matrix.get("reviewFans")
    fans = fans_value if isinstance(fans_value, list) else []
    fan_by_id: dict[str, Mapping[str, object]] = {}
    for value in fans:
        if not isinstance(value, Mapping):
            reasons.append("review-fan:malformed")
            continue
        fan_id = _text(value.get("id"))
        if not fan_id or fan_id in fan_by_id:
            reasons.append("review-fan:missing-or-duplicate-id")
            continue
        fan_by_id[fan_id] = value

    for fan_id in sorted(_REQUIRED_FANS):
        fan = fan_by_id.get(fan_id)
        if fan is None:
            reasons.append(f"missing-review-fan:{fan_id}")
            continue
        if _text(fan.get("exactHead")) != expected_head:
            reasons.append(f"{fan_id}:stale-review-head")
    output_fan = fan_by_id.get("output-correctness")
    if output_fan is not None and output_fan.get("executionMode") != "non-read-only":
        reasons.append("output-correctness:must-be-non-read-only")

    required_fans = [fan_by_id.get(fan_id) for fan_id in sorted(_REQUIRED_FANS)]
    if all(fan is not None for fan in required_fans):
        reviewers = {_text(fan.get("reviewer")) for fan in required_fans if fan is not None}
        evidence_ids = {_text(fan.get("evidenceId")) for fan in required_fans if fan is not None}
        if "" in reviewers or "" in evidence_ids or len(reviewers) != 2 or len(evidence_ids) != 2:
            reasons.append("review-fans:not-independent")

    rows_value = matrix.get("atomicRows")
    rows = rows_value if isinstance(rows_value, list) else []
    row_by_id: dict[str, Mapping[str, object]] = {}
    for value in rows:
        if not isinstance(value, Mapping):
            reasons.append("atomic-row:malformed")
            continue
        row_id = _text(value.get("id"))
        if not row_id or row_id in row_by_id:
            reasons.append("atomic-row:missing-or-duplicate-id")
            continue
        row_by_id[row_id] = value

    for row_id in authoritative_ids:
        if row_id not in row_by_id:
            reasons.append(f"missing-required-row:{row_id}")
    for row_id in row_by_id:
        if row_id not in declared_ids:
            reasons.append(f"undeclared-atomic-row:{row_id}")

    semantic_pass_ids: list[str] = []
    for row_id, row in row_by_id.items():
        raw_classification = _text(row.get("classification"))
        try:
            classification = Classification(raw_classification)
        except ValueError:
            reasons.append(f"{row_id}:unknown-classification")
            continue

        if classification in {Classification.NOT_PROVEN, Classification.FAILED}:
            reasons.append(f"{row_id}:{classification.value}")

        claim_kind = row.get("claimKind")
        if claim_kind not in {"structural", "semantic"}:
            reasons.append(f"{row_id}:invalid-claim-kind")
        if row.get("requiredForClosure") is not True:
            reasons.append(f"{row_id}:must-be-required-for-closure")

        if claim_kind == "semantic" and classification is not Classification.SEMANTIC_PASS:
            reasons.append(f"{row_id}:semantic-requires-SEMANTIC_PASS")
        if claim_kind == "structural" and classification not in {
            Classification.STRUCTURAL_PASS,
            Classification.SEMANTIC_PASS,
        }:
            reasons.append(f"{row_id}:structural-requires-pass")

        if _text(row.get("evidenceHead")) != expected_head:
            reasons.append(f"{row_id}:stale-evidence-head")
        evidence_fan = _text(row.get("evidenceFan"))
        if evidence_fan not in fan_by_id:
            reasons.append(f"{row_id}:unknown-evidence-fan")
        if claim_kind == "semantic" and classification is Classification.SEMANTIC_PASS:
            semantic_pass_ids.append(row_id)
            if evidence_fan != "output-correctness":
                reasons.append(f"{row_id}:semantic-pass-requires-output-correctness-fan")
            if not _text(row.get("observation")).strip():
                reasons.append(f"{row_id}:semantic-pass-missing-observation")

    if semantic_pass_ids:
        if output_correctness_verifier is None:
            reasons.append("output-correctness:execution-not-provided")
        else:
            execution = output_correctness_verifier()
            if execution.exact_head != expected_head:
                reasons.append("output-correctness:execution-stale-head")
            if execution.execution_mode != "non-read-only":
                reasons.append("output-correctness:execution-must-be-non-read-only")
            if output_fan is not None:
                if execution.reviewer != _text(output_fan.get("reviewer")):
                    reasons.append("output-correctness:execution-reviewer-mismatch")
                if execution.evidence_id != _text(output_fan.get("evidenceId")):
                    reasons.append("output-correctness:execution-evidence-mismatch")
            for row_id in semantic_pass_ids:
                if execution.classifications.get(row_id) is not Classification.SEMANTIC_PASS:
                    reasons.append(f"{row_id}:execution-did-not-prove-SEMANTIC_PASS")
                if not execution.observations.get(row_id, "").strip():
                    reasons.append(f"{row_id}:execution-missing-observation")

    return ClosureResult(closed=not reasons, reasons=tuple(dict.fromkeys(reasons)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-row-id", action="append", default=[])
    args = parser.parse_args(argv)

    try:
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"closed": False, "reasons": [f"matrix-unreadable:{exc}"]}))
        return 2
    if not isinstance(matrix, dict):
        print(json.dumps({"closed": False, "reasons": ["matrix:not-an-object"]}))
        return 2

    result = evaluate_closure(
        matrix,
        expected_head=args.expected_head,
        expected_row_ids=args.expected_row_id or None,
    )
    print(json.dumps({"closed": result.closed, "reasons": result.reasons}, sort_keys=True))
    return 0 if result.closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
