import pytest

from backend.app.rag.chunking import chunk_document


def test_chunk_document_preserves_heading_and_line_metadata() -> None:
    text = "\n\n# Overview\n\nNarraTwin creates grounded scripts.\n\n## Safety\n\nClaims cite chunks."

    chunks = chunk_document(
        document_id="doc_test",
        project_id="proj_test",
        tenant_id="tenant_local",
        source_filename="overview.md",
        text=text,
        max_tokens=8,
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert chunks[0].heading_path == ["Overview"]
    assert chunks[0].line_start == 3
    assert chunks[0].line_end >= chunks[0].line_start
    assert "grounded scripts" in chunks[0].text
    assert chunks[1].heading_path == ["Overview", "Safety"]
    assert chunks[1].token_count <= 8
    assert chunks[0].checksum.startswith("sha256:")


def test_chunk_document_rejects_empty_content() -> None:
    chunks = chunk_document(
        document_id="doc_test",
        project_id="proj_test",
        tenant_id="tenant_local",
        source_filename="empty.md",
        text=" \n\t ",
        max_tokens=20,
    )

    assert chunks == []


def test_chunk_document_splits_single_long_line_with_overlap() -> None:
    words = [f"word{i}" for i in range(25)]

    chunks = chunk_document(
        document_id="doc_test",
        project_id="proj_test",
        tenant_id="tenant_local",
        source_filename="long.md",
        text=" ".join(words),
        max_tokens=10,
        overlap_tokens=2,
    )

    assert len(chunks) == 3
    assert all(chunk.token_count <= 10 for chunk in chunks)
    assert chunks[0].line_start == chunks[0].line_end == 1
    assert "word8" in chunks[1].text


def test_chunk_document_splits_single_long_heading() -> None:
    heading = "# " + " ".join(f"heading{i}" for i in range(25))

    chunks = chunk_document(
        document_id="doc_test",
        project_id="proj_test",
        tenant_id="tenant_local",
        source_filename="heading.md",
        text=heading,
        max_tokens=10,
        overlap_tokens=2,
    )

    assert len(chunks) == 3
    assert all(chunk.token_count <= 10 for chunk in chunks)
    assert all(chunk.heading_path for chunk in chunks)


def test_chunk_document_enforces_max_chunks_during_construction() -> None:
    words = [f"word{i}" for i in range(60)]

    with pytest.raises(ValueError, match="max_chunks exceeded"):
        chunk_document(
            document_id="doc_test",
            project_id="proj_test",
            tenant_id="tenant_local",
            source_filename="limited.md",
            text=" ".join(words),
            max_tokens=10,
            overlap_tokens=0,
            max_chunks=3,
        )


def test_chunk_document_overlaps_normal_rollover_chunks() -> None:
    text = "\n".join(" ".join(f"word{line}_{index}" for index in range(4)) for line in range(4))

    chunks = chunk_document(
        document_id="doc_test",
        project_id="proj_test",
        tenant_id="tenant_local",
        source_filename="overlap.md",
        text=text,
        max_tokens=8,
        overlap_tokens=2,
    )

    assert len(chunks) >= 2
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
