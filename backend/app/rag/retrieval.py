"""Project-isolated deterministic retrieval."""

from __future__ import annotations

import hashlib

from backend.app.rag.models import RetrievedContext
from backend.app.rag.providers import EmbeddingProvider
from backend.app.rag.store import InMemoryRagStore


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
    scored: list[tuple[float, str, RetrievedContext]] = []
    for chunk in store.chunks_for_project(tenant_id=tenant_id, project_id=project_id):
        score = _cosine_similarity(query_embedding, chunk.embedding)
        context_ref_id = "ctx_" + hashlib.sha256(
            f"{project_id}:{chunk.chunk_id}:{query}".encode("utf-8")
        ).hexdigest()[:16]
        if score >= min_score:
            scored.append((score, chunk.chunk_id, RetrievedContext(context_ref_id, chunk, score)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored[:top_k]]


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
