"""Standalone evaluator metrics for Stage 5."""

from __future__ import annotations

from collections.abc import Sequence

from dataclasses import dataclass

from backend.app.rag.chunking import count_tokens
from backend.app.rag.models import KnowledgeChunk


def calculate_script_faithfulness(
    *,
    candidate_claim_count: int,
    claim_support_count: int,
    unsupported_claim_count: int,
) -> float:
    """Compute a deterministic faithfulness score from claim support evidence."""
    if candidate_claim_count <= 0:
        return 0.0
    if unsupported_claim_count > 0:
        return max(0.0, claim_support_count / max(candidate_claim_count, 1))
    return 1.0


def calculate_answer_relevancy(*, candidate_text: str, prompt: str) -> float:
    """Estimate answer relevancy from token overlap with the user prompt."""
    if not candidate_text.strip():
        return 0.0
    prompt_terms = _normalize_relevance_terms(prompt)
    if not prompt_terms:
        return 1.0
    response_terms = _normalize_relevance_terms(candidate_text)
    if not response_terms:
        return 0.0
    overlap = prompt_terms & response_terms
    if not overlap:
        return 0.0
    ratio = len(overlap) / max(len(prompt_terms), 1)
    return max(0.0, min(1.0, ratio))


def calculate_context_precision_recall(
    *,
    candidate_text: str,
    retrieved_context: Sequence[object],
    all_chunks: Sequence[KnowledgeChunk],
) -> tuple[float, float]:
    """Compute lightweight context precision and recall style metrics."""
    if not retrieved_context:
        return 0.0, 0.0

    response_terms = set(_normalize_terms(candidate_text))
    if not response_terms:
        return 0.0, 0.0

    def overlaps_text(raw_text: str) -> bool:
        if not raw_text:
            return False
        return bool(response_terms.intersection(_normalize_terms(raw_text)))

    relevant_retrieved = []
    for context in retrieved_context:
        context_chunk = getattr(context, "chunk", context)
        if hasattr(context_chunk, "text") and overlaps_text(context_chunk.text):
            relevant_retrieved.append(context)

    corpus_chunks = list(all_chunks) if all_chunks else []
    relevant_corpus = [chunk for chunk in corpus_chunks if overlaps_text(chunk.text)]

    precision = len(relevant_retrieved) / len(retrieved_context)
    recall = (len(relevant_retrieved) / len(relevant_corpus)) if relevant_corpus else 0.0
    return min(1.0, precision), min(1.0, recall)


def _normalize_relevance_terms(text: str) -> set[str]:
    """Normalize prompt/candidate terms with relevance-focused filtering."""
    terms = set()
    for token in _simple_terms(text):
        normalized = _normalize_term(token.lower())
        if not normalized:
            continue
        if len(normalized) < 3:
            continue
        if _is_relevance_stopword(normalized):
            continue
        terms.add(_normalize_plural(normalized))
    return terms


def evaluate_token_usage(
    *,
    prompt: str,
    retrieved_context: Sequence[object],
    candidate_text: str,
) -> tuple[int, int]:
    """Estimate prompt + output token usage for local Stage 5 telemetry."""
    input_tokens = count_tokens(prompt)
    for context in retrieved_context:
        chunk = getattr(context, "chunk", context)
        if hasattr(chunk, "text"):
            input_tokens += count_tokens(chunk.text)
    output_tokens = count_tokens(candidate_text)
    return input_tokens, output_tokens


def estimate_cost_usd(*, input_tokens: int, output_tokens: int) -> float:
    """Return deterministic local cost estimates.

    Local/mock provider runs are free in Stage 5; we still report a numeric estimate.
    """
    del input_tokens
    del output_tokens
    return 0.0


def _normalize_terms(text: str) -> set[str]:
    return {term for term in _simple_terms(text) if len(term) >= 3}


def _simple_terms(text: str) -> set[str]:
    tokens: set[str] = set()
    clean_text = text.replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ")
    for token in clean_text.split():
        normalized = _normalize_term(token.lower())
        if normalized:
            tokens.add(normalized)
    return tokens


def _normalize_term(token: str) -> str:
    term = "".join(char for char in token if char.isalnum())
    if not term:
        return ""
    return term


def _normalize_plural(token: str) -> str:
    """Apply minimal stemming to avoid trivial plural mismatches in prompt intent."""
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def _is_relevance_stopword(token: str) -> bool:
    return token.lower() in {
        "create",
        "creates",
        "creating",
        "concise",
        "confident",
        "for",
        "and",
        "with",
        "into",
        "that",
        "this",
        "these",
        "those",
        "your",
        "about",
        "from",
        "have",
        "has",
        "have",
        "were",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "their",
        "there",
        "here",
        "their",
        "there",
        "while",
        "into",
        "the",
        "then",
        "than",
        "them",
        "they",
        "them",
        "their",
        "them",
        "when",
        "where",
        "which",
        "while",
        "your",
        "all",
        "any",
        "can",
        "not",
        "too",
        "now",
        "use",
        "used",
        "using",
        "make",
        "made",
        "step",
        "steps",
        "kind",
        "kindly",
        "guide",
        "helps",
        "help",
        "please",
    }


@dataclass(frozen=True)
class EvaluationRunPayload:
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    latency_ms: int

    @property
    def total_tokens(self) -> int:
        return max(0, self.input_tokens) + max(0, self.output_tokens)

    @property
    def estimated_cost(self) -> float:
        return max(0.0, self.input_cost_usd) + max(0.0, self.output_cost_usd)

    @property
    def token_usage(self) -> dict[str, int]:
        return {
            "inputTokens": max(0, self.input_tokens),
            "outputTokens": max(0, self.output_tokens),
            "totalTokens": self.total_tokens,
        }

    @property
    def metadata(self) -> dict[str, float | int]:
        return {
            "estimatedCostUsd": self.estimated_cost,
            "latencyMs": max(0, self.latency_ms),
            "inputTokens": max(0, self.input_tokens),
            "outputTokens": max(0, self.output_tokens),
            "totalTokens": self.total_tokens,
        }
