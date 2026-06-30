"""Deterministic markdown/text chunking for local Stage 4 ingestion."""

from __future__ import annotations

import hashlib
import re

from backend.app.rag.models import CHUNKING_STRATEGY_VERSION, KnowledgeChunk

TOKEN_PATTERN = re.compile(r"\S+")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def count_tokens(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def checksum_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_id(document_id: str, chunk_index: int, text: str) -> str:
    digest = hashlib.sha256(
        f"{document_id}:{chunk_index}:{CHUNKING_STRATEGY_VERSION}:{text}".encode("utf-8")
    ).hexdigest()[:16]
    return f"chunk_{digest}"


def _current_heading_path(path: list[str], level: int, title: str) -> list[str]:
    next_path = path[: max(level - 1, 0)]
    next_path.append(title)
    return next_path


def _flush_chunk(
    *,
    chunks: list[KnowledgeChunk],
    tenant_id: str,
    project_id: str,
    document_id: str,
    source_filename: str,
    source_document_checksum: str,
    approved_at: str,
    lines: list[str],
    heading_path: list[str],
    line_start: int,
    line_end: int,
) -> None:
    text = "\n".join(line.strip() for line in lines if line.strip()).strip()
    if not text:
        return
    chunk_index = len(chunks)
    chunks.append(
        KnowledgeChunk(
            chunk_id=_chunk_id(document_id, chunk_index, text),
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
            source_filename=source_filename,
            source_document_checksum=source_document_checksum,
            approved_at=approved_at,
            chunk_index=chunk_index,
            text=text,
            token_count=count_tokens(text),
            checksum=checksum_text(text),
            heading_path=heading_path.copy(),
            line_start=line_start,
            line_end=line_end,
        )
    )


def chunk_document(
    *,
    document_id: str,
    project_id: str,
    tenant_id: str,
    source_filename: str,
    text: str,
    source_document_checksum: str | None = None,
    approved_at: str = "",
    max_tokens: int = 800,
    overlap_tokens: int = 100,
) -> list[KnowledgeChunk]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        return []
    if source_document_checksum is None:
        source_document_checksum = checksum_text(text)
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    overlap = max(0, min(overlap_tokens, max_tokens - 1))

    chunks: list[KnowledgeChunk] = []
    heading_path: list[str] = []
    active_lines: list[str] = []
    active_heading_path: list[str] = []
    active_line_start = 1
    active_line_end = 1
    active_token_count = 0

    for line_number, line in enumerate(normalized.split("\n"), start=1):
        heading_match = HEADING_PATTERN.match(line)
        line_token_count = count_tokens(line)
        if heading_match:
            if active_lines:
                _flush_chunk(
                    chunks=chunks,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    document_id=document_id,
                    source_filename=source_filename,
                    source_document_checksum=source_document_checksum,
                    approved_at=approved_at,
                    lines=active_lines,
                    heading_path=active_heading_path,
                    line_start=active_line_start,
                    line_end=active_line_end,
                )
            level = len(heading_match.group(1))
            heading_path = _current_heading_path(heading_path, level, heading_match.group(2))
            if line_token_count > max_tokens:
                words = TOKEN_PATTERN.findall(line)
                step = max_tokens - overlap
                for start_index in range(0, len(words), step):
                    window = words[start_index : start_index + max_tokens]
                    if not window:
                        continue
                    _flush_chunk(
                        chunks=chunks,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        document_id=document_id,
                        source_filename=source_filename,
                        source_document_checksum=source_document_checksum,
                        approved_at=approved_at,
                        lines=[" ".join(window)],
                        heading_path=heading_path,
                        line_start=line_number,
                        line_end=line_number,
                    )
                    if start_index + max_tokens >= len(words):
                        break
                active_lines = []
                active_heading_path = []
                active_token_count = 0
                continue
            active_lines = [line]
            active_heading_path = heading_path.copy()
            active_line_start = line_number
            active_line_end = line_number
            active_token_count = line_token_count
            continue

        if not line.strip():
            active_line_end = line_number
            continue

        if line_token_count > max_tokens:
            if active_lines:
                _flush_chunk(
                    chunks=chunks,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    document_id=document_id,
                    source_filename=source_filename,
                    source_document_checksum=source_document_checksum,
                    approved_at=approved_at,
                    lines=active_lines,
                    heading_path=active_heading_path,
                    line_start=active_line_start,
                    line_end=active_line_end,
                )
                active_lines = []
                active_token_count = 0
            words = TOKEN_PATTERN.findall(line)
            step = max_tokens - overlap
            for start_index in range(0, len(words), step):
                window = words[start_index : start_index + max_tokens]
                if not window:
                    continue
                _flush_chunk(
                    chunks=chunks,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    document_id=document_id,
                    source_filename=source_filename,
                    source_document_checksum=source_document_checksum,
                    approved_at=approved_at,
                    lines=[" ".join(window)],
                    heading_path=heading_path,
                    line_start=line_number,
                    line_end=line_number,
                )
                if start_index + max_tokens >= len(words):
                    break
            continue

        if active_lines and active_token_count + line_token_count > max_tokens:
            _flush_chunk(
                chunks=chunks,
                tenant_id=tenant_id,
                project_id=project_id,
                document_id=document_id,
                source_filename=source_filename,
                source_document_checksum=source_document_checksum,
                approved_at=approved_at,
                lines=active_lines,
                heading_path=active_heading_path,
                line_start=active_line_start,
                line_end=active_line_end,
            )
            active_lines = []
            active_token_count = 0

        if not active_lines:
            active_line_start = line_number
            active_heading_path = heading_path.copy()
        active_lines.append(line)
        active_line_end = line_number
        active_token_count += line_token_count

    if active_lines:
        _flush_chunk(
            chunks=chunks,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
            source_filename=source_filename,
            source_document_checksum=source_document_checksum,
            approved_at=approved_at,
            lines=active_lines,
            heading_path=active_heading_path,
            line_start=active_line_start,
            line_end=active_line_end,
        )
    return chunks
