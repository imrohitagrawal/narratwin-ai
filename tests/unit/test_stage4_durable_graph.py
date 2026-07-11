from __future__ import annotations

import pytest

from backend.app.storage.postgres_state import AcidCasConflictError, AcidCasKernel, outbox_payload_hash
from backend.app.storage.stage4_graph import (
    Stage4ChunkMetadata,
    Stage4ClaimSupportMetadata,
    Stage4ContextRefMetadata,
    Stage4DocumentMetadata,
    Stage4DurableGraphStore,
    Stage4EvaluationMetadata,
    Stage4ProjectMetadata,
    Stage4RunMetadata,
)


def _project() -> Stage4ProjectMetadata:
    return Stage4ProjectMetadata(
        project_id="project-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        name="NarraTwin AI",
    )


def _document(*, checksum: str = "sha256:doc-1", source_filename: str = "project.md") -> Stage4DocumentMetadata:
    return Stage4DocumentMetadata(
        document_id="document-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        source_filename=source_filename,
        source_document_checksum=checksum,
        approved_at="2026-07-11T00:00:00+00:00",
    )


def _chunk(*, checksum: str = "sha256:doc-1", source_filename: str = "project.md") -> Stage4ChunkMetadata:
    return Stage4ChunkMetadata(
        chunk_id="chunk-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        document_id="document-1",
        source_filename=source_filename,
        source_document_checksum=checksum,
        approved_at="2026-07-11T00:00:00+00:00",
        chunk_checksum="sha256:chunk-1",
        chunk_index=0,
        token_count=42,
    )


def _commit_project_document_chunk(store: Stage4DurableGraphStore) -> None:
    store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(),
        chunks=(_chunk(),),
    )


def test_ch03_stage4_graph_commits_project_document_and_chunks_atomically() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())

    result = store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(),
        chunks=(_chunk(),),
    )

    assert result.outcome == "applied"
    assert [record.entity_type for record in result.records] == ["project", "document", "chunk"]
    assert store.get_chunk("tenant-1", "owner-1", "project-1", "chunk-1").payload["documentId"] == "document-1"


def test_ch03_stage4_graph_rejects_chunk_with_mismatched_document_checksum() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())

    with pytest.raises(AcidCasConflictError, match="document checksum"):
        store.commit_project_document_chunks(
            transaction_id="tx-graph-1",
            request_id="req-graph-1",
            project=_project(),
            document=_document(checksum="sha256:doc-1"),
            chunks=(_chunk(checksum="sha256:other-doc"),),
        )

    with pytest.raises(KeyError):
        store.get_project("tenant-1", "owner-1", "project-1")


def test_ch03_stage4_graph_preserves_colon_bearing_source_filename_metadata() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())

    store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(source_filename="meeting:notes.md"),
        chunks=(_chunk(source_filename="meeting:notes.md"),),
    )

    assert (
        store.get_chunk("tenant-1", "owner-1", "project-1", "chunk-1").payload["sourceFilename"]
        == "meeting:notes.md"
    )


def test_ch03_stage4_graph_commits_completed_run_with_evaluation_supports() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    result = store.commit_completed_run_evaluation(
        transaction_id="tx-run-1",
        request_id="req-run-1",
        run=Stage4RunMetadata(
            run_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            generated_claim_ids=("claim-1",),
        ),
        evaluation=Stage4EvaluationMetadata(
            evaluation_id="eval-1",
            run_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            evaluation_status="PASSED",
            context_refs=(
                Stage4ContextRefMetadata(
                    context_ref_id="ctx-1",
                    chunk_id="chunk-1",
                    document_id="document-1",
                ),
            ),
            claim_supports=(
                Stage4ClaimSupportMetadata(
                    claim_id="claim-1",
                    context_ref_id="ctx-1",
                    chunk_id="chunk-1",
                    document_id="document-1",
                ),
            ),
        ),
    )

    assert [record.entity_type for record in result.records] == ["run", "evaluation"]
    assert store.get_run("tenant-1", "owner-1", "project-1", "run-1").payload["status"] == "COMPLETED"


def test_ch03_stage4_graph_rejects_evaluation_support_for_unknown_context_ref() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="context ref"):
        store.commit_completed_run_evaluation(
            transaction_id="tx-run-1",
            request_id="req-run-1",
            run=Stage4RunMetadata(
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                generated_claim_ids=("claim-1",),
            ),
            evaluation=Stage4EvaluationMetadata(
                evaluation_id="eval-1",
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                evaluation_status="PASSED",
                context_refs=(
                    Stage4ContextRefMetadata(
                        context_ref_id="ctx-1",
                        chunk_id="chunk-1",
                        document_id="document-1",
                    ),
                ),
                claim_supports=(
                    Stage4ClaimSupportMetadata(
                        claim_id="claim-1",
                        context_ref_id="ctx-missing",
                        chunk_id="chunk-1",
                        document_id="document-1",
                    ),
                ),
            ),
        )

    with pytest.raises(KeyError):
        store.get_run("tenant-1", "owner-1", "project-1", "run-1")


def test_ch03_stage4_graph_replays_exact_transaction() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    first = store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(),
        chunks=(_chunk(),),
    )
    second = store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(),
        chunks=(_chunk(),),
    )

    assert first.outcome == "applied"
    assert second.outcome == "replayed"
    assert second.records == first.records


def test_ch03_stage4_graph_rejects_changed_replay_payload() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    store.commit_project_document_chunks(
        transaction_id="tx-graph-1",
        request_id="req-graph-1",
        project=_project(),
        document=_document(),
        chunks=(_chunk(),),
    )

    with pytest.raises(AcidCasConflictError, match="checksum"):
        store.commit_project_document_chunks(
            transaction_id="tx-graph-1",
            request_id="req-graph-1",
            project=Stage4ProjectMetadata(
                project_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                name="Changed",
            ),
            document=_document(),
            chunks=(_chunk(),),
        )


def test_ch03_stage4_graph_binds_outbox_event_to_run_version() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)
    payload: dict[str, object] = {"runId": "run-1", "status": "COMPLETED", "generatedClaimIds": ["claim-1"]}

    result = store.commit_completed_run_evaluation(
        transaction_id="tx-run-1",
        request_id="req-run-1",
        run=Stage4RunMetadata(
            run_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            generated_claim_ids=("claim-1",),
        ),
        evaluation=Stage4EvaluationMetadata(
            evaluation_id="eval-1",
            run_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            evaluation_status="PASSED",
            context_refs=(Stage4ContextRefMetadata("ctx-1", "chunk-1", "document-1"),),
            claim_supports=(Stage4ClaimSupportMetadata("claim-1", "ctx-1", "chunk-1", "document-1"),),
        ),
        graph_events=(
            store.run_completed_event(
                event_id="event-1",
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                operation_id="operation-1",
                payload=payload,
            ),
        ),
    )

    assert result.outbox_events[0].resource_id == "run:tenant-1:owner-1:project-1:run-1"
    assert result.outbox_events[0].resource_version == 1
    assert result.outbox_events[0].payload_hash == outbox_payload_hash(payload)


def test_ch03_stage4_graph_rejects_outbox_event_without_matching_graph_write() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="same transaction"):
        store.commit_completed_run_evaluation(
            transaction_id="tx-run-1",
            request_id="req-run-1",
            run=Stage4RunMetadata(
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                generated_claim_ids=("claim-1",),
            ),
            evaluation=Stage4EvaluationMetadata(
                evaluation_id="eval-1",
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                evaluation_status="PASSED",
                context_refs=(Stage4ContextRefMetadata("ctx-1", "chunk-1", "document-1"),),
                claim_supports=(Stage4ClaimSupportMetadata("claim-1", "ctx-1", "chunk-1", "document-1"),),
            ),
            graph_events=(
                store.run_completed_event(
                    event_id="event-1",
                    run_id="run-other",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    operation_id="operation-1",
                    payload={"runId": "run-other", "status": "COMPLETED"},
                ),
            ),
        )
