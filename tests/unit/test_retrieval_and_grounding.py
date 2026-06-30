from backend.app.rag.chunking import chunk_document
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.providers import MockEmbeddingProvider, MockLLMProvider
from backend.app.rag.retrieval import retrieve_context
from backend.app.rag.store import InMemoryRagStore


def test_retrieval_returns_project_scoped_relevant_chunks() -> None:
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text=(
            "# Product\n"
            "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n\n"
            "# Other\n"
            "Unrelated deployment notes are not useful for recruiter walkthroughs."
        ),
        max_tokens=12,
    )
    other_project_chunks = chunk_document(
        document_id="doc_b",
        project_id="proj_b",
        tenant_id="tenant_local",
        source_filename="other.md",
        text="Other projects must never leak into retrieval.",
        max_tokens=12,
    )
    store.add_chunks(chunks, embedder)
    store.add_chunks(other_project_chunks, embedder)

    results = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts for recruiters",
        top_k=2,
        min_score=0.1,
    )

    assert results
    assert all(result.chunk.project_id == "proj_a" for result in results)
    assert "grounded walkthrough" in results[0].chunk.text


def test_grounding_fails_unsupported_claims_from_llm_output() -> None:
    # Grounding evaluation requires retrieved source_chunk citations plus run_id trace metadata.
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    llm = MockLLMProvider(extra_unsupported_claim="NarraTwin guarantees hiring outcomes.")
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text="NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        max_tokens=20,
    )
    store.add_chunks(chunks, embedder)
    retrieved = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts",
        top_k=3,
        min_score=0.1,
    )

    candidate = llm.generate_script(
        audience="RECRUITER",
        prompt="Create a grounded script.",
        retrieved_context=retrieved,
    )
    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_a",
        run_id="run_test",
        candidate=candidate,
        retrieved_context=retrieved,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert evaluation.unsupported_claim_count == 1
    assert "guarantees hiring outcomes" in evaluation.unsupported_claims[0].claim_text
