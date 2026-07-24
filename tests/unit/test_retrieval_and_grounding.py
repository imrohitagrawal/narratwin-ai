from opentelemetry import trace
from prometheus_client import generate_latest

from backend.app.eval import calculate_groundedness
from backend.app.observability.metrics import record_walkthrough_metrics
from backend.app.observability.traces import with_trace
from backend.app.rag.chunking import chunk_document
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import GeneratedScript, ScriptClaim
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


def test_chunking_preserves_headings_as_metadata_without_heading_only_claim_chunks() -> None:
    chunks = chunk_document(
        document_id="doc_headings",
        project_id="proj_headings",
        tenant_id="tenant_local",
        source_filename="project.md",
        text=(
            "# NarraTwin AI\n\n"
            "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n\n"
            "Every generated walkthrough claim must cite retrieved source chunks from approved knowledge."
        ),
        max_tokens=30,
    )

    assert len(chunks) == 2
    assert all(not chunk.text.startswith("#") for chunk in chunks)
    assert chunks[0].text == "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts."
    assert chunks[0].heading_path == ["NarraTwin AI"]


def test_rag_store_keeps_same_document_chunks_isolated_by_tenant() -> None:
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    tenant_a_chunks = chunk_document(
        document_id="doc_shared",
        project_id="proj_shared",
        tenant_id="tenant_a",
        source_filename="project.md",
        text="Tenant A grounded walkthrough scripts.",
        max_tokens=12,
    )
    tenant_b_chunks = chunk_document(
        document_id="doc_shared",
        project_id="proj_shared",
        tenant_id="tenant_b",
        source_filename="project.md",
        text="Tenant B grounded walkthrough scripts.",
        max_tokens=12,
    )

    store.add_chunks(tenant_a_chunks, embedder)
    store.add_chunks(tenant_b_chunks, embedder)

    assert store.chunk_count_for_project(tenant_id="tenant_a", project_id="proj_shared") == 1
    assert store.chunk_count_for_project(tenant_id="tenant_b", project_id="proj_shared") == 1
    assert store.chunks_for_project(tenant_id="tenant_a", project_id="proj_shared")[0].tenant_id == "tenant_a"
    assert store.chunks_for_project(tenant_id="tenant_b", project_id="proj_shared")[0].tenant_id == "tenant_b"


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
        prompt="Create a grounded script.",
        all_chunks=chunks,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert evaluation.unsupported_claim_count == 1
    assert "guarantees hiring outcomes" in evaluation.unsupported_claims[0].claim_text


def test_grounding_fails_visible_script_text_without_claim_metadata() -> None:
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text="NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        max_tokens=20,
    )
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    stored = store.add_chunks(chunks, embedder)
    retrieved = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts",
        top_k=3,
        min_score=0.1,
    )
    supported = "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts."
    hallucinated = "NarraTwin guarantees hiring outcomes. [1]"
    candidate = GeneratedScript(
        text=f"For recruiters, {supported} [1] {hallucinated}",
        claims=[
            ScriptClaim(
                claim_id="claim_001",
                text=supported,
                citation_index=1,
                chunk_id=stored[0].chunk_id,
                script_span_start=0,
                script_span_end=len(f"For recruiters, {supported} [1]"),
            )
        ],
    )

    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_a",
        run_id="run_test",
        candidate=candidate,
        retrieved_context=retrieved,
        prompt="Create a grounded script.",
        all_chunks=stored,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert any("no provider claim metadata" in claim.reason for claim in evaluation.unsupported_claims)


def test_grounding_fails_visible_citation_marker_mismatch() -> None:
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text=(
            "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n"
            "Every generated walkthrough claim must cite retrieved source chunks from approved knowledge."
        ),
        max_tokens=9,
    )
    stored = store.add_chunks(chunks, embedder)
    retrieved = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts cite retrieved source chunks",
        top_k=3,
        min_score=0.1,
    )
    claim_text = stored[0].text.rstrip(".") + "."
    script = f"For recruiters, {claim_text} [2]"
    candidate = GeneratedScript(
        text=script,
        claims=[
            ScriptClaim(
                claim_id="claim_001",
                text=claim_text,
                citation_index=1,
                chunk_id=stored[0].chunk_id,
                script_span_start=0,
                script_span_end=len(script),
            )
        ],
    )

    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_a",
        run_id="run_test",
        candidate=candidate,
        retrieved_context=retrieved,
        prompt="Create a grounded script.",
        all_chunks=stored,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert any("citation marker" in claim.reason for claim in evaluation.unsupported_claims)


def test_grounding_fails_unsupported_text_blended_into_supported_sentence() -> None:
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text="NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        max_tokens=20,
    )
    stored = store.add_chunks(chunks, embedder)
    retrieved = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts",
        top_k=3,
        min_score=0.1,
    )
    claim_text = "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts."
    script = f"For recruiters, {claim_text.rstrip('.')} and guarantees hiring outcomes. [1]"
    candidate = GeneratedScript(
        text=script,
        claims=[
            ScriptClaim(
                claim_id="claim_001",
                text=claim_text,
                citation_index=1,
                chunk_id=stored[0].chunk_id,
                script_span_start=0,
                script_span_end=len(script),
            )
        ],
    )

    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_a",
        run_id="run_test",
        candidate=candidate,
        retrieved_context=retrieved,
        prompt="Create a grounded script.",
        all_chunks=stored,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert any("does not exactly match" in claim.reason for claim in evaluation.unsupported_claims)


def test_grounding_fails_trailing_unpunctuated_unsupported_text() -> None:
    store = InMemoryRagStore()
    embedder = MockEmbeddingProvider()
    chunks = chunk_document(
        document_id="doc_a",
        project_id="proj_a",
        tenant_id="tenant_local",
        source_filename="project.md",
        text="NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        max_tokens=20,
    )
    stored = store.add_chunks(chunks, embedder)
    retrieved = retrieve_context(
        store=store,
        embedder=embedder,
        tenant_id="tenant_local",
        project_id="proj_a",
        query="grounded walkthrough scripts",
        top_k=3,
        min_score=0.1,
    )
    claim_text = "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts."
    supported_sentence = f"For recruiters, {claim_text} [1]"
    candidate = GeneratedScript(
        text=f"{supported_sentence} NarraTwin guarantees hiring outcomes",
        claims=[
            ScriptClaim(
                claim_id="claim_001",
                text=claim_text,
                citation_index=1,
                chunk_id=stored[0].chunk_id,
                script_span_start=0,
                script_span_end=len(supported_sentence),
            )
        ],
    )

    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_a",
        run_id="run_test",
        candidate=candidate,
        retrieved_context=retrieved,
        prompt="Create a grounded script.",
        all_chunks=stored,
    )

    assert evaluation.evaluation_status == "FAILED"
    assert any("no provider claim metadata" in claim.reason for claim in evaluation.unsupported_claims)


def test_walkthrough_trace_id_comes_from_active_span() -> None:
    with with_trace(scope="narratwin.test", name="unit-trace") as trace_id:
        active_span = trace.get_current_span()
        active_trace_id = active_span.get_span_context().trace_id

    assert trace_id == f"trace_{active_trace_id:032x}"


def test_stage5_eval_package_exposes_groundedness_metric() -> None:
    assert calculate_groundedness(supported_claim_count=2, candidate_claim_count=4) == 0.5
    assert calculate_groundedness(supported_claim_count=0, candidate_claim_count=0) == 0.0


def test_refused_walkthrough_metrics_use_bounded_labels() -> None:
    record_walkthrough_metrics(
        tenant_id="tenant_should_not_be_label",
        run_id="run_should_not_be_label",
        status="REFUSED",
        evaluation_status=None,
        reason_code="PROMPT_INJECTION_DETECTED_UNIT",
        latency_ms=0,
        token_usage={"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
        estimated_cost=0.0,
    )

    metrics_text = generate_latest().decode("utf-8")

    assert 'status="REFUSED"' in metrics_text
    assert 'reason_code="OTHER"' in metrics_text
    assert "PROMPT_INJECTION_DETECTED_UNIT" not in metrics_text
    assert "tenant_should_not_be_label" not in metrics_text
    assert "run_should_not_be_label" not in metrics_text
