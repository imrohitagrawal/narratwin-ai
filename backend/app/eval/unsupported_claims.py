"""Unsupported-claim detector helpers used by Stage 5 gate checks."""

from __future__ import annotations

from backend.app.rag.models import EvaluationResult, UnsupportedClaim


def detect_unsupported_claims(*, evaluation: EvaluationResult) -> list[UnsupportedClaim]:
    """Return all unsupported claims from a grounding evaluation result."""
    return [claim for claim in evaluation.unsupported_claims]


def unsupported_claim_count(*, evaluation: EvaluationResult) -> int:
    """Return the unsupported-claim count from a grounding evaluation."""
    return len(detect_unsupported_claims(evaluation=evaluation))
