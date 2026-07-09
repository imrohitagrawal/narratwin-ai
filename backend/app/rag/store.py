"""In-memory local store for the Stage 4 slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

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
        prepared: list[tuple[tuple[str, str, str], KnowledgeChunk]] = []
        for chunk in chunks:
            chunk_key = (chunk.tenant_id, chunk.project_id, chunk.chunk_id)
            if chunk_key in self._chunks:
                continue
            chunk_with_embedding = replace(chunk, embedding=embedder.embed(chunk.text))
            prepared.append((chunk_key, chunk_with_embedding))
        stored: list[KnowledgeChunk] = []
        for chunk_key, chunk_with_embedding in prepared:
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

    def prune(self, predicate: Callable[[KnowledgeChunk], bool]) -> None:
        for chunk_key, chunk in list(self._chunks.items()):
            if not predicate(chunk):
                self._chunks.pop(chunk_key, None)
        self._chunks_by_project.clear()
        for tenant_id, project_id, chunk_id in self._chunks:
            self._chunks_by_project.setdefault((tenant_id, project_id), set()).add(chunk_id)

    def has_chunk(self, *, tenant_id: str, project_id: str, chunk_id: str) -> bool:
        return (tenant_id, project_id, chunk_id) in self._chunks

    def chunk_count_for_project(self, *, tenant_id: str, project_id: str) -> int:
        return len(self._chunks_by_project.get((tenant_id, project_id), set()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunks": [
                {
                    "chunkId": chunk.chunk_id,
                    "tenantId": chunk.tenant_id,
                    "projectId": chunk.project_id,
                    "documentId": chunk.document_id,
                    "sourceFilename": chunk.source_filename,
                    "sourceDocumentChecksum": chunk.source_document_checksum,
                    "approvedAt": chunk.approved_at,
                    "chunkIndex": chunk.chunk_index,
                    "text": chunk.text,
                    "tokenCount": chunk.token_count,
                    "checksum": chunk.checksum,
                    "headingPath": chunk.heading_path,
                    "lineStart": chunk.line_start,
                    "lineEnd": chunk.line_end,
                    "embedding": list(chunk.embedding),
                }
                for chunk in self._chunks.values()
            ]
        }

    @classmethod
    def from_dict(cls, payload: object) -> InMemoryRagStore:
        store = cls()
        if not isinstance(payload, dict):
            return store
        chunks = payload.get("chunks", [])
        if not isinstance(chunks, list):
            return store
        for row in chunks:
            if not isinstance(row, dict):
                continue
            chunk = KnowledgeChunk(
                chunk_id=str(row["chunkId"]),
                tenant_id=str(row["tenantId"]),
                project_id=str(row["projectId"]),
                document_id=str(row["documentId"]),
                source_filename=str(row["sourceFilename"]),
                source_document_checksum=str(row["sourceDocumentChecksum"]),
                approved_at=str(row["approvedAt"]),
                chunk_index=int(row["chunkIndex"]),
                text=str(row["text"]),
                token_count=int(row["tokenCount"]),
                checksum=str(row["checksum"]),
                heading_path=[str(part) for part in row.get("headingPath", [])],
                line_start=int(row["lineStart"]),
                line_end=int(row["lineEnd"]),
                embedding=tuple(float(value) for value in row.get("embedding", ())),
            )
            chunk_key = (chunk.tenant_id, chunk.project_id, chunk.chunk_id)
            store._chunks[chunk_key] = chunk
            store._chunks_by_project.setdefault((chunk.tenant_id, chunk.project_id), set()).add(chunk.chunk_id)
        return store
