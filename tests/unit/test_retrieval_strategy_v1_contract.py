"""RED contract tests for the canonical Stage 4 retrieval lineage."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import math
from pathlib import Path
from typing import Any
import pytest
import backend.app.stage4 as stage4_module
from backend.app.rag.models import (
    RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT,
    RETRIEVAL_MIN_SCORE,
    RETRIEVAL_STRATEGY_VERSION,
    RETRIEVAL_TOP_K,
    KnowledgeChunk,
)
from backend.app.rag.retrieval import retrieve_context
from backend.app.stage4 import (
    LocalPrincipal,
    Stage4Error,
    Stage4Service,
    walkthrough_run_to_dict,
    walkthrough_to_api,
)
CANONICAL_LINEAGE = {
    "retrieval_strategy_version": "stage4-rag-v1",
    "retrieval_top_k": 6,
    "retrieval_score_threshold": 0.72,
}
class ScoreEmbeddingProvider:
    provider = "synthetic"
    model = "score-vector"
    model_version = "test-v1"
    dimension = 2
    def __init__(self, scores: dict[str, float]) -> None:
        self.scores = scores
    def embed(self, text: str) -> tuple[float, ...]:
        score = self.scores.get(text)
        if score is None:
            return (1.0, 0.0)
        return (score, math.sqrt(max(0.0, 1.0 - score * score)))
class CountingLlm:
    def __init__(self, delegate: Any) -> None:
        self.delegate = delegate
        self.calls = 0
    def generate_script(self, **kwargs: Any) -> Any:
        self.calls += 1
        return self.delegate.generate_script(**kwargs)
def _chunk(
    chunk_id: str,
    *,
    document_id: str = "doc-a",
    project_id: str = "proj-a",
    tenant_id: str = "tenant-a",
    approved_at: str = "2026-08-01T00:00:00Z",
    chunk_index: int = 0,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id,
        tenant_id=tenant_id,
        project_id=project_id,
        document_id=document_id,
        source_filename=f"{document_id}.md",
        source_document_checksum="sha256:" + "a" * 64,
        approved_at=approved_at,
        chunk_index=chunk_index,
        text=f"evidence-{chunk_id}",
        token_count=1,
        checksum="sha256:" + "b" * 64,
        heading_path=[],
        line_start=1,
        line_end=1,
    )
def _retrieve(chunks: list[KnowledgeChunk], scores: dict[str, float], *, top_k: int = 6) -> list[Any]:
    service = Stage4Service()
    embedder = ScoreEmbeddingProvider(scores)
    service.rag_store.add_chunks(chunks, embedder)
    return retrieve_context(
        store=service.rag_store,
        embedder=embedder,
        tenant_id="tenant-a",
        project_id="proj-a",
        query="qwerty",
        top_k=top_k,
        min_score=0.72,
    )
def _seed_service(state_path: Path) -> tuple[Stage4Service, LocalPrincipal, str, Any]:
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal, name="Lineage project", idempotency_key="create-lineage-project"
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="lineage.md",
        content_type="text/markdown",
        data=b"# Lineage\nCanonical lineage evidence supports a bounded walkthrough.",
        idempotency_key="upload-lineage-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-lineage-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-lineage-document",
    )
    chunks = service.rag_store.chunks_for_project(
        tenant_id=principal.tenant_id, project_id=project.project_id
    )
    service.rag_store.clear()
    service.embedder = ScoreEmbeddingProvider({chunk.text: 0.90 for chunk in chunks})
    service.rag_store.add_chunks([replace(chunk, embedding=()) for chunk in chunks], service.embedder)
    run = service.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Explain canonical lineage evidence.",
        idempotency_key="generate-lineage-walkthrough",
    )
    assert run.evaluation is not None
    return service, principal, project.project_id, run
def _state_row(value: Any, key: str, expected: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if value.get(key) == expected:
            return value
        for child in value.values():
            if found := _state_row(child, key, expected):
                return found
    elif isinstance(value, list):
        for child in value:
            if found := _state_row(child, key, expected):
                return found
    return None
def _legacy_snapshot(state_path: Path) -> tuple[LocalPrincipal, str, str, dict[str, Any], dict[str, Any]]:
    _service, principal, project_id, run = _seed_service(state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    run_row = next(row for row in state["walkthroughRuns"] if row["run_id"] == run.run_id)
    for field_name in CANONICAL_LINEAGE:
        run_row.pop(field_name, None)
        run_row["evaluation"].pop(field_name, None)
    idempotency_row = next(
        row
        for row in state["idempotencyRecords"]
        if row.get("value", {}).get("id") == run.run_id
    )
    legacy_run, legacy_idempotency = deepcopy(run_row), deepcopy(idempotency_row)
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return principal, project_id, run.run_id, legacy_run, legacy_idempotency
def test_a2_1_001_canonical_strategy_constants_are_not_silently_redefined() -> None:
    assert (RETRIEVAL_STRATEGY_VERSION, RETRIEVAL_TOP_K, RETRIEVAL_MIN_SCORE) == (
        "stage4-rag-v1",
        6,
        0.72,
    )
    assert RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT == 3
def test_a2_1_002_threshold_is_inclusive_at_point_72() -> None:
    chunks = [_chunk("at-boundary"), _chunk("below-boundary", chunk_index=1)]
    scores = {chunks[0].text: 0.72, chunks[1].text: 0.719999}
    assert [item.chunk.chunk_id for item in _retrieve(chunks, scores)] == ["at-boundary"]
def test_a2_1_003_equal_scores_use_the_canonical_total_order() -> None:
    chunks = [
        _chunk("late-index", document_id="doc-1", approved_at="2026-08-02T00:00:00Z", chunk_index=2),
        _chunk("z-id", document_id="doc-2", approved_at="2026-08-02T00:00:00Z", chunk_index=1),
        _chunk("a-id", document_id="doc-3", approved_at="2026-08-02T00:00:00Z", chunk_index=1),
        _chunk("older", document_id="doc-4", approved_at="2026-08-01T00:00:00Z", chunk_index=0),
    ]
    scores = {chunk.text: 0.80 for chunk in chunks}
    assert [item.chunk.chunk_id for item in _retrieve(chunks, scores)] == [
        "a-id",
        "z-id",
        "late-index",
        "older",
    ]
def test_a2_1_004_top_six_never_selects_more_than_three_chunks_per_document() -> None:
    chunks = [_chunk(f"a-{index}", chunk_index=index) for index in range(5)] + [
        _chunk(f"b-{index}", document_id="doc-b", chunk_index=index) for index in range(3)
    ]
    scores = {chunk.text: 0.95 - index * 0.01 for index, chunk in enumerate(chunks)}
    selected = _retrieve(chunks, scores)
    assert len(selected) == 6
    assert sum(item.chunk.document_id == "doc-a" for item in selected) == 3
def test_a2_1_005_retrieval_cannot_cross_project_or_tenant_boundaries() -> None:
    eligible = _chunk("eligible")
    chunks = [eligible, _chunk("other-project", project_id="proj-b"), _chunk("other-tenant", tenant_id="tenant-b")]
    scores = {chunk.text: 0.99 for chunk in chunks}
    assert [item.chunk.chunk_id for item in _retrieve(chunks, scores)] == ["eligible"]
def test_a2_1_006_small_corpus_does_not_expand_or_synthesize_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Stage4Service()
    principal = LocalPrincipal()
    project = service.create_project(principal=principal, name="Expansion probe", idempotency_key="create")
    high = _chunk("high", project_id=project.project_id, tenant_id=principal.tenant_id)
    low = _chunk("low", project_id=project.project_id, tenant_id=principal.tenant_id, chunk_index=1)
    service.embedder = ScoreEmbeddingProvider({high.text: 0.80, low.text: 0.71})
    service.rag_store.add_chunks([high, low], service.embedder)
    monkeypatch.setattr(stage4_module, "RETRIEVAL_MIN_SCORE", 0.72)
    run = service.generate_walkthrough(
        principal=principal, project_id=project.project_id, audience="RECRUITER",
        requested_language="en", depth="CONCISE", style="CONFIDENT", prompt="probe", idempotency_key="generate"
    )
    assert [(item.chunk.chunk_id, item.score) for item in run.retrieved_context] == [("high", 0.80)]
def test_a2_1_007_low_confidence_is_terminal_before_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Stage4Service()
    principal = LocalPrincipal()
    project = service.create_project(principal=principal, name="Refusal probe", idempotency_key="create")
    low = _chunk("low", project_id=project.project_id, tenant_id=principal.tenant_id)
    service.embedder = ScoreEmbeddingProvider({low.text: 0.71})
    service.rag_store.add_chunks([low], service.embedder)
    counting_llm = CountingLlm(service.llm)
    service.llm = counting_llm
    monkeypatch.setattr(stage4_module, "RETRIEVAL_MIN_SCORE", 0.72)
    run = service.generate_walkthrough(
        principal=principal, project_id=project.project_id, audience="RECRUITER",
        requested_language="en", depth="CONCISE", style="CONFIDENT", prompt="probe", idempotency_key="generate"
    )
    assert (run.status, run.failure_reason, counting_llm.calls) == (
        "REFUSED", Stage4Service.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL, 0
    )
def test_a2_1_008_walkthrough_run_persists_exact_retrieval_lineage(tmp_path: Path) -> None:
    _service, _principal, _project_id, run = _seed_service(tmp_path / "state.json")
    row = walkthrough_run_to_dict(run)
    assert {field: row.get(field) for field in CANONICAL_LINEAGE} == CANONICAL_LINEAGE
def test_a2_1_009_evaluation_persists_exact_retrieval_lineage(tmp_path: Path) -> None:
    _service, _principal, _project_id, run = _seed_service(tmp_path / "state.json")
    assert run.evaluation is not None
    row = walkthrough_run_to_dict(run)["evaluation"]
    assert {field: row.get(field) for field in CANONICAL_LINEAGE} == CANONICAL_LINEAGE
def test_a2_1_010_api_uses_stored_lineage_not_mutable_runtime_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _service, _principal, _project_id, run = _seed_service(tmp_path / "state.json")
    monkeypatch.setattr(stage4_module, "RETRIEVAL_STRATEGY_VERSION", "mutated-v2")
    monkeypatch.setattr(stage4_module, "RETRIEVAL_TOP_K", 99)
    monkeypatch.setattr(stage4_module, "RETRIEVAL_MIN_SCORE", 0.99)
    evaluation = walkthrough_to_api(run)["evaluation"]
    assert (evaluation["retrievalStrategyVersion"], evaluation["retrievalTopK"], evaluation["retrievalScoreThreshold"]) == (
        "stage4-rag-v1", 6, 0.72
    )
def test_a2_1_011_structurally_valid_legacy_rows_are_quarantined_and_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    _principal, _project_id, run_id, legacy_run, legacy_idempotency = _legacy_snapshot(state_path)
    restored = Stage4Service(state_path=state_path)
    assert run_id not in restored.walkthrough_runs
    assert all(record.value is not restored.walkthrough_runs.get(run_id) for record in restored.idempotency_records.values())
    round_tripped = json.loads(state_path.read_text(encoding="utf-8"))
    assert _state_row(round_tripped, "run_id", run_id) == legacy_run
    assert _state_row(round_tripped, "idempotency_record_id", legacy_idempotency["idempotency_record_id"]) == legacy_idempotency
def test_a2_1_012_quarantined_idempotency_replay_is_stale_and_does_not_generate(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    principal, project_id, _run_id, _legacy_run, _legacy_idempotency = _legacy_snapshot(state_path)
    restored = Stage4Service(state_path=state_path)
    counting_llm = CountingLlm(restored.llm)
    restored.llm = counting_llm
    with pytest.raises(Stage4Error) as caught:
        restored.generate_walkthrough(
            principal=principal, project_id=project_id, audience="RECRUITER", requested_language="en",
            depth="CONCISE", style="CONFIDENT", prompt="Explain canonical lineage evidence.",
            idempotency_key="generate-lineage-walkthrough",
        )
    assert (caught.value.code, counting_llm.calls) == ("STALE_RETRIEVAL_LINEAGE", 0)
@pytest.mark.parametrize("mutation", ["version", "top-k-type", "non-finite", "contradictory"])
def test_a2_1_013_forged_malformed_or_contradictory_lineage_is_quarantined(tmp_path: Path, mutation: str) -> None:
    state_path = tmp_path / "state.json"
    _service, _principal, _project_id, run = _seed_service(state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    row = next(candidate for candidate in state["walkthroughRuns"] if candidate["run_id"] == run.run_id)
    row.update(CANONICAL_LINEAGE)
    row["evaluation"].update(CANONICAL_LINEAGE)
    if mutation == "version":
        row["retrieval_strategy_version"] = row["evaluation"]["retrieval_strategy_version"] = "forged-v2"
    elif mutation == "top-k-type":
        row["retrieval_top_k"] = row["evaluation"]["retrieval_top_k"] = "6"
    elif mutation == "non-finite":
        row["retrieval_score_threshold"] = row["evaluation"]["retrieval_score_threshold"] = float("nan")
    else:
        row["evaluation"]["retrieval_score_threshold"] = 0.73
    state_path.write_text(json.dumps(state), encoding="utf-8")
    restored = Stage4Service(state_path=state_path)
    assert run.run_id not in restored.walkthrough_runs
    assert _state_row(json.loads(state_path.read_text(encoding="utf-8")), "run_id", run.run_id) is not None
