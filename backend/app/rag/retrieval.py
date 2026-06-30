"""Project-isolated deterministic retrieval."""

from __future__ import annotations

import hashlib
import heapq
import re
from collections import defaultdict

from backend.app.rag.models import RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT, RetrievedContext
from backend.app.rag.providers import EmbeddingProvider
from backend.app.rag.store import InMemoryRagStore

WORD_PATTERN = re.compile(r"[a-z0-9]+")


def retrieve_context(
    *,
    store: InMemoryRagStore,
    embedder: EmbeddingProvider,
    tenant_id: str,
    project_id: str,
    query: str,
    top_k: int,
    min_score: float,
) -> list[RetrievedContext]:
    query_embedding = embedder.embed(query)
    scored: list[tuple[float, str, int, str, RetrievedContext]] = []
    per_document_counts: defaultdict[str, int] = defaultdict(int)
    for chunk in store.chunks_for_project(tenant_id=tenant_id, project_id=project_id):
        score = _retrieval_score(query=query, query_embedding=query_embedding, text=chunk.text, embedding=chunk.embedding)
        context_ref_id = "ctx_" + hashlib.sha256(
            f"{tenant_id}:{project_id}:{chunk.chunk_id}:{query}".encode("utf-8")
        ).hexdigest()[:16]
        if score >= min_score:
            scored.append((score, chunk.approved_at, chunk.chunk_index, chunk.chunk_id, RetrievedContext(context_ref_id, chunk, score)))
    ranked = heapq.nsmallest(
        len(scored),
        scored,
        key=lambda item: (-item[0], _reverse_sort_text(item[1]), item[2], item[3]),
    )
    selected: list[RetrievedContext] = []
    for _score, _approved_at, _chunk_index, _chunk_id, context in ranked:
        if per_document_counts[context.chunk.document_id] >= RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT:
            continue
        selected.append(context)
        per_document_counts[context.chunk.document_id] += 1
        if len(selected) == top_k:
            break
    return selected


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))


def _retrieval_score(
    *,
    query: str,
    query_embedding: tuple[float, ...],
    text: str,
    embedding: tuple[float, ...],
) -> float:
    cosine = _cosine_similarity(query_embedding, embedding)
    query_terms = set(WORD_PATTERN.findall(query.lower()))
    text_terms = set(WORD_PATTERN.findall(text.lower()))
    if not query_terms:
        return cosine
    lexical_overlap = len(query_terms & text_terms) / len(query_terms)
    return min(1.0, cosine + lexical_overlap * 0.25)


def _reverse_sort_text(value: str) -> tuple[int, ...]:
    return tuple(-ord(char) for char in value)
