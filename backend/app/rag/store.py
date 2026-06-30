"""In-memory local store for the Stage 4 slice."""

from __future__ import annotations

from dataclasses import replace

from backend.app.rag.models import KnowledgeChunk
from backend.app.rag.providers import EmbeddingProvider


class InMemoryRagStore:
    def __init__(self) -> None:
        self._chunks: dict[str, KnowledgeChunk] = {}

    def clear(self) -> None:
        self._chunks.clear()

    def add_chunks(self, chunks: list[KnowledgeChunk], embedder: EmbeddingProvider) -> list[KnowledgeChunk]:
        stored: list[KnowledgeChunk] = []
        for chunk in chunks:
            chunk_with_embedding = replace(chunk, embedding=embedder.embed(chunk.text))
            self._chunks[chunk_with_embedding.chunk_id] = chunk_with_embedding
            stored.append(chunk_with_embedding)
        return stored

    def chunks_for_project(self, *, tenant_id: str, project_id: str) -> list[KnowledgeChunk]:
        return [
            chunk
            for chunk in self._chunks.values()
            if chunk.tenant_id == tenant_id and chunk.project_id == project_id
        ]
