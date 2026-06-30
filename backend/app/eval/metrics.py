"""Evaluation metrics and token/cost helpers for Stage 5 observability."""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.eval.script_faithfulness import calculate_context_precision_recall, calculate_script_faithfulness, calculate_answer_relevancy

__all__ = [
    "calculate_answer_relevancy",
    "calculate_context_precision_recall",
    "calculate_groundedness",
    "calculate_script_faithfulness",
    "evaluate_token_usage",
    "estimate_cost_usd",
]


def calculate_groundedness(*, supported_claim_count: int, candidate_claim_count: int) -> float:
    """Compute deterministic claim-level groundedness from support coverage."""
    if candidate_claim_count <= 0:
        return 0.0
    return max(0.0, min(1.0, supported_claim_count / candidate_claim_count))


def evaluate_token_usage(
    *,
    prompt: str,
    retrieved_context: Sequence[object],
    candidate_text: str,
) -> tuple[int, int]:
    """Estimate input/output token usage for a walkthrough run."""
    from backend.app.rag.chunking import count_tokens

    input_tokens = count_tokens(prompt)
    for context in retrieved_context:
        chunk = getattr(context, "chunk", context)
        if hasattr(chunk, "text"):
            input_tokens += count_tokens(chunk.text)
    output_tokens = count_tokens(candidate_text)
    return input_tokens, output_tokens


def estimate_cost_usd(*, input_tokens: int, output_tokens: int) -> float:
    """Return deterministic token-cost estimate for local runs.

    Local mocked provider runs are currently cost-free; this function intentionally
    returns 0.0 while still exposing a numeric traceable value for CI checks.
    """
    del input_tokens
    del output_tokens
    return 0.0
