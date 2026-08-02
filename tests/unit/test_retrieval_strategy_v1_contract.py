from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from backend.app.rag import models, retrieval
from backend.app.rag.models import KnowledgeChunk, RetrievedContext
from backend.app.stage4 import LocalPrincipal, Stage4Error, Stage4Service, walkthrough_to_api
import backend.app.stage4 as stage4


V1 = ("stage4-rag-v1", 6, 0.72, 3)
STALE_MESSAGE = "Stored walkthrough cannot be replayed because its retrieval lineage is stale or unavailable."
REQUEST = dict(
    audience="RECRUITER",
    requested_language="en",
    depth="CONCISE",
    style="CONFIDENT",
    prompt="Create a concise grounded walkthrough for a recruiter.",
)


class Embedder:
    def embed(self, _text: str) -> tuple[float, ...]:
        return (1.0,)


class Store:
    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        self.chunks = chunks

    def chunks_for_project(self, *, tenant_id: str, project_id: str) -> list[KnowledgeChunk]:
        return [c for c in self.chunks if (c.tenant_id, c.project_id) == (tenant_id, project_id)]


def chunk(chunk_id: str, document_id: str, index: int, approved: str, text: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id, "tenant_local", "proj_000001", document_id, f"{document_id}.md", "sha256:doc",
        approved, index, text, 4, f"sha256:{chunk_id}", [], 1, 1, (1.0,),
    )


def select(monkeypatch: pytest.MonkeyPatch, chunks: list[KnowledgeChunk], scores: dict[str, float]) -> list[RetrievedContext]:
    monkeypatch.setattr(retrieval, "_retrieval_score", lambda **kw: scores[kw["text"]])
    return retrieval.retrieve_context(
        store=Store(chunks), embedder=Embedder(), tenant_id="tenant_local", project_id="proj_000001",
        query="query", top_k=6, min_score=0.72,
    )


def seed(path: Path) -> tuple[Stage4Service, LocalPrincipal, str]:
    service, principal = Stage4Service(state_path=path), LocalPrincipal()
    project = service.create_project(
        principal=principal, name="NarraTwin AI", description="Grounded walkthrough generator", idempotency_key="p",
    )
    document = service.upload_document(
        principal=principal, project_id=project.project_id, source_filename="stage4_project.md",
        content_type="text/markdown", data=Path("tests/fixtures/stage4_project.md").read_bytes(), idempotency_key="d",
    )
    service.approve_document(
        principal=principal, project_id=project.project_id, document_id=document.document_id, idempotency_key="a",
    )
    service.ingest_documents(
        principal=principal, project_id=project.project_id, document_ids=[document.document_id], idempotency_key="i",
    )
    run = service.generate_walkthrough(principal=principal, project_id=project.project_id, idempotency_key="walk", **REQUEST)
    assert run.status == "COMPLETED"
    return service, principal, project.project_id


def canonical_payload(path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text())
    run = payload["walkthroughRuns"][0]
    lineage = {"retrieval_strategy_version": V1[0], "retrieval_top_k": V1[1], "retrieval_score_threshold": V1[2]}
    run.update(lineage)
    run["evaluation"].update(lineage)
    idem = next(row for row in payload["idempotencyRecords"] if row["idempotency_key"] == "walk")
    return payload, deepcopy(run), deepcopy(idem)


def mutate(payload: dict[str, Any], case: str) -> None:
    run, evaluation = payload["walkthroughRuns"][0], payload["walkthroughRuns"][0]["evaluation"]
    names = ("retrieval_strategy_version", "retrieval_top_k", "retrieval_score_threshold")
    if case in {"both_missing", "run_missing", "evaluation_missing"}:
        targets = (run, evaluation) if case == "both_missing" else (run,) if case == "run_missing" else (evaluation,)
        for target in targets:
            for name in names:
                target.pop(name)
    elif case == "mismatch":
        evaluation["retrieval_top_k"] = 7
    elif case in {"topk7", "bool_topk"}:
        run["retrieval_top_k"] = evaluation["retrieval_top_k"] = 7 if case == "topk7" else True
    elif case in {"threshold60", "bool_threshold", "nan", "positive_inf", "negative_inf"}:
        value = {"threshold60": 0.60, "bool_threshold": True, "nan": math.nan,
                 "positive_inf": math.inf, "negative_inf": -math.inf}[case]
        run["retrieval_score_threshold"] = evaluation["retrieval_score_threshold"] = value
    elif case == "wrong_version":
        run["retrieval_strategy_version"] = evaluation["retrieval_strategy_version"] = "stage4-rag-v2"
    else:
        payload["walkthroughRuns"][0]["retrieved_context"][0]["score"] = {
            "low_score": 0.719999, "bool_score": True, "infinite_score": math.inf,
        }[case]


def test_v1_literals_boundary_cap_and_tie_order(monkeypatch: pytest.MonkeyPatch) -> None:
    assert (models.RETRIEVAL_STRATEGY_VERSION, models.RETRIEVAL_TOP_K, models.RETRIEVAL_MIN_SCORE,
            models.RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT) == V1
    caps = [chunk(f"a{i}", "doc_a", i, "2026-01-01", f"a{i}") for i in range(4)]
    caps += [chunk("boundary", "doc_b", 0, "2026-01-01", "boundary"),
             chunk("low", "doc_c", 0, "2026-01-01", "low")]
    scores = {f"a{i}": 0.99 - i / 100 for i in range(4)} | {"boundary": 0.72, "low": 0.719999}
    assert [c.chunk.chunk_id for c in select(monkeypatch, caps, scores)] == ["a0", "a1", "a2", "boundary"]
    ordered = [
        chunk("score", "d0", 9, "2025-01-01", "score"),
        chunk("approval-old", "d1", 9, "2025-01-01", "approval-old"),
        chunk("approval-new", "d2", 9, "2026-01-01", "approval-new"),
        chunk("index-two", "d3", 2, "2025-01-01", "index-two"),
        chunk("id-z", "d4", 1, "2025-01-01", "id-z"),
        chunk("id-a", "d5", 1, "2025-01-01", "id-a"),
    ]
    tie_scores = {"score": 0.95, "approval-old": 0.90, "approval-new": 0.90,
                  "index-two": 0.80, "id-z": 0.80, "id-a": 0.80}
    assert [c.chunk.chunk_id for c in select(monkeypatch, ordered, tie_scores)] == [
        "score", "approval-new", "approval-old", "id-a", "id-z", "index-two",
    ]


def test_orchestration_preserves_rank_and_never_expands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, principal = Stage4Service(state_path=tmp_path / "order.json"), LocalPrincipal()
    project = service.create_project(principal=principal, name="Order", idempotency_key="p")
    raw = [chunk("rank-first", "d1", 9, "2026-01-01", "First fact."),
           chunk("rank-second", "d2", 1, "2026-01-01", "Second fact."),
           chunk("below", "d3", 0, "2026-01-01", "Below fact.")]
    stored = service.rag_store.add_chunks(raw, service.embedder)
    ranked = [RetrievedContext("c1", stored[0], 0.95), RetrievedContext("c2", stored[1], 0.90)]
    monkeypatch.setattr(stage4, "retrieve_context", lambda **_kw: ranked)
    original, seen = service.llm.generate_script, []
    monkeypatch.setattr(service.llm, "generate_script", lambda **kw: (seen.extend(kw["retrieved_context"]), original(**kw))[1])
    service.generate_walkthrough(principal=principal, project_id=project.project_id, idempotency_key="w", **REQUEST)
    assert [(c.chunk.chunk_id, c.score) for c in seen] == [("rank-first", 0.95), ("rank-second", 0.90)]


def test_all_low_refuses_before_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, principal = Stage4Service(state_path=tmp_path / "refuse.json"), LocalPrincipal()
    project = service.create_project(principal=principal, name="Refuse", idempotency_key="p")
    monkeypatch.setattr(stage4, "retrieve_context", lambda **_kw: [])
    monkeypatch.setattr(service.llm, "generate_script", lambda **_kw: pytest.fail("generation after refusal"))
    run = service.generate_walkthrough(principal=principal, project_id=project.project_id, idempotency_key="w", **REQUEST)
    assert (run.status, run.failure_reason, service.walkthrough_runs[run.run_id]) == (
        "REFUSED", "LOW_RETRIEVAL_CONFIDENCE", run,
    )


def test_new_lineage_survives_restart_and_global_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "valid.json"
    _, principal, project_id = seed(path)
    restored = Stage4Service(state_path=path)
    run = next(iter(restored.walkthrough_runs.values()))
    assert (run.retrieval_strategy_version, run.retrieval_top_k, run.retrieval_score_threshold) == V1[:3]
    assert (run.evaluation.retrieval_strategy_version, run.evaluation.retrieval_top_k,
            run.evaluation.retrieval_score_threshold) == V1[:3]
    monkeypatch.setattr(restored.llm, "generate_script", lambda **_kw: pytest.fail("duplicate generation"))
    monkeypatch.setattr(stage4, "RETRIEVAL_STRATEGY_VERSION", "mutant")
    monkeypatch.setattr(stage4, "RETRIEVAL_TOP_K", 7)
    monkeypatch.setattr(stage4, "RETRIEVAL_MIN_SCORE", 0.60)
    replay = restored.generate_walkthrough(principal=principal, project_id=project_id, idempotency_key="walk", **REQUEST)
    assert replay.run_id == run.run_id
    api = walkthrough_to_api(replay)["evaluation"]
    assert (api["retrievalStrategyVersion"], api["retrievalTopK"], api["retrievalScoreThreshold"]) == V1[:3]


@pytest.mark.parametrize("case", [
    "both_missing", "run_missing", "evaluation_missing", "mismatch", "topk7", "bool_topk",
    "threshold60", "bool_threshold", "nan", "positive_inf", "negative_inf", "wrong_version",
    "low_score", "bool_score", "infinite_score",
])
def test_stale_lineage_is_preserved_but_inactive_twice(case: str, tmp_path: Path) -> None:
    path = tmp_path / f"{case}.json"
    _, _, project_id = seed(path)
    payload, _, _ = canonical_payload(path)
    mutate(payload, case)
    expected_run = deepcopy(payload["walkthroughRuns"][0])
    expected_idem = next(row for row in payload["idempotencyRecords"] if row["idempotency_key"] == "walk")
    path.write_text(json.dumps(payload))
    for _ in range(2):
        restored = Stage4Service(state_path=path)
        persisted = json.loads(path.read_text())
        assert not restored.walkthrough_runs and project_id in restored.projects
        assert persisted["quarantinedWalkthroughRuns"] == [expected_run]
        assert persisted["quarantinedIdempotencyRecords"] == [expected_idem]


@pytest.mark.parametrize("changed,code", [(False, "STALE_RETRIEVAL_LINEAGE"), (True, "IDEMPOTENCY_CONFLICT")])
def test_stale_key_blocks_exact_and_changed_payload(changed: bool, code: str, tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / f"block-{changed}.json"
    _, principal, project_id = seed(path)
    payload, _, _ = canonical_payload(path)
    payload["walkthroughRuns"][0]["retrieval_top_k"] = 7
    payload["walkthroughRuns"][0]["evaluation"]["retrieval_top_k"] = 7
    path.write_text(json.dumps(payload))
    restored = Stage4Service(state_path=path)
    monkeypatch.setattr(restored.llm, "generate_script", lambda **_kw: pytest.fail("stale replay generated"))
    request = REQUEST | ({"prompt": "Changed payload."} if changed else {})
    with pytest.raises(Stage4Error) as raised:
        restored.generate_walkthrough(principal=principal, project_id=project_id, idempotency_key="walk", **request)
    assert (raised.value.status_code, raised.value.code) == (409, code)
    if not changed:
        assert raised.value.message == STALE_MESSAGE
