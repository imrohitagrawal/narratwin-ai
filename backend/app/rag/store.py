"""In-memory local store for the Stage 4 slice."""

from __future__ import annotations

from dataclasses import replace

from backend.app.rag.models import KnowledgeChunk
from backend.app.rag.providers import EmbeddingProvider


class InMemoryRagStore:
    def __init__(self) -> None:
        self._chunks: dict[tuple[str, str, str], KnowledgeChunk] = {}
        self._chunks_by_project: dict[tuple[str, str], set[str]] = {}

    def clear(self) -> None:
        self._chunks.clear()
        self._chunks_by_project.clear()

    def add_chunks(self, chunks: list[KnowledgeChunk], embedder: EmbeddingProvider) -> list[KnowledgeChunk]:
        stored: list[KnowledgeChunk] = []
        for chunk in chunks:
            chunk_key = (chunk.tenant_id, chunk.project_id, chunk.chunk_id)
            if chunk_key in self._chunks:
                continue
            chunk_with_embedding = replace(chunk, embedding=embedder.embed(chunk.text))
            self._chunks[chunk_key] = chunk_with_embedding
            key = (chunk_with_embedding.tenant_id, chunk_with_embedding.project_id)
            self._chunks_by_project.setdefault(key, set()).add(chunk_with_embedding.chunk_id)
            stored.append(chunk_with_embedding)
        return stored

    def chunks_for_project(self, *, tenant_id: str, project_id: str) -> list[KnowledgeChunk]:
        return [
            self._chunks[(tenant_id, project_id, chunk_id)]
            for chunk_id in sorted(self._chunks_by_project.get((tenant_id, project_id), set()))
            if (tenant_id, project_id, chunk_id) in self._chunks
        ]

    def chunk_count_for_project(self, *, tenant_id: str, project_id: str) -> int:
        return len(self._chunks_by_project.get((tenant_id, project_id), set()))
