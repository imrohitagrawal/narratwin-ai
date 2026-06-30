from backend.app.rag.chunking import chunk_document


def test_chunk_document_preserves_heading_and_line_metadata() -> None:
    text = "# Overview\n\nNarraTwin creates grounded scripts.\n\n## Safety\n\nClaims cite chunks."

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
    assert chunks[0].line_start == 1
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
