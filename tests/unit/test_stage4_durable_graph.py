from __future__ import annotations

import pytest

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleWriteError,
    OutboxEventWrite,
    TransactionWrite,
    outbox_payload_hash,
)
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


def _document(
    *,
    document_id: str = "document-1",
    checksum: str = "sha256:doc-1",
    source_filename: str = "project.md",
) -> Stage4DocumentMetadata:
    return Stage4DocumentMetadata(
        document_id=document_id,
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        source_filename=source_filename,
        source_document_checksum=checksum,
        approved_at="2026-07-11T00:00:00+00:00",
    )


def _chunk(
    *,
    chunk_id: str = "chunk-1",
    document_id: str = "document-1",
    checksum: str = "sha256:doc-1",
    source_filename: str = "project.md",
) -> Stage4ChunkMetadata:
    return Stage4ChunkMetadata(
        chunk_id=chunk_id,
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        document_id=document_id,
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


def test_ch03_stage4_graph_appends_second_document_to_existing_project() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    result = store.commit_project_document_chunks(
        transaction_id="tx-graph-2",
        request_id="req-graph-2",
        project=_project(),
        document=_document(
            document_id="document-2",
            checksum="sha256:doc-2",
            source_filename="follow-up.md",
        ),
        chunks=(
            _chunk(
                chunk_id="chunk-2",
                document_id="document-2",
                checksum="sha256:doc-2",
                source_filename="follow-up.md",
            ),
        ),
    )

    assert result.outcome == "applied"
    assert [record.entity_type for record in result.records] == ["document", "chunk"]
    assert store.get_document("tenant-1", "owner-1", "project-1", "document-2").payload["sourceFilename"] == (
        "follow-up.md"
    )
    assert store.get_chunk("tenant-1", "owner-1", "project-1", "chunk-1").payload["documentId"] == "document-1"
    assert store.get_chunk("tenant-1", "owner-1", "project-1", "chunk-2").payload["documentId"] == "document-2"


def test_ch03_stage4_graph_replays_append_document_transaction() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)
    append_document = _document(
        document_id="document-2",
        checksum="sha256:doc-2",
        source_filename="follow-up.md",
    )
    append_chunks = (
        _chunk(
            chunk_id="chunk-2",
            document_id="document-2",
            checksum="sha256:doc-2",
            source_filename="follow-up.md",
        ),
    )

    first = store.commit_project_document_chunks(
        transaction_id="tx-graph-2",
        request_id="req-graph-2",
        project=_project(),
        document=append_document,
        chunks=append_chunks,
    )
    second = store.commit_project_document_chunks(
        transaction_id="tx-graph-2",
        request_id="req-graph-2",
        project=_project(),
        document=append_document,
        chunks=append_chunks,
    )

    assert first.outcome == "applied"
    assert second.outcome == "replayed"
    assert second.records == first.records


def test_ch03_stage4_graph_records_approved_document_as_terminal_metadata() -> None:
    kernel = AcidCasKernel()
    store = Stage4DurableGraphStore(kernel)
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasStaleWriteError, match="TERMINAL"):
        kernel.commit(
            transaction_id="tx-mutate-doc",
            request_id="req-mutate-doc",
            request_checksum="sha256:mutate-doc",
            writes=(
                TransactionWrite(
                    entity_type="document",
                    entity_id="document-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="OPEN",
                    payload={
                        "documentId": "document-1",
                        "sourceFilename": "project.md",
                        "sourceDocumentChecksum": "sha256:changed",
                        "approvedAt": "2026-07-11T00:00:00+00:00",
                    },
                ),
            ),
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


def test_ch03_stage4_graph_rejects_passed_evaluation_without_context_refs() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="context refs"):
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
                context_refs=(),
                claim_supports=(),
            ),
        )


def test_ch03_stage4_graph_rejects_passed_evaluation_without_claim_supports() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="claim supports"):
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
                claim_supports=(),
            ),
        )


def test_ch03_stage4_graph_rejects_generated_claim_without_support() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="must have support"):
        store.commit_completed_run_evaluation(
            transaction_id="tx-run-1",
            request_id="req-run-1",
            run=Stage4RunMetadata(
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                generated_claim_ids=("claim-1", "claim-2"),
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
        )


def test_ch03_stage4_graph_rejects_unbounded_context_refs() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="context refs"):
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
                context_refs=tuple(
                    Stage4ContextRefMetadata(f"ctx-{index}", "chunk-1", "document-1")
                    for index in range(7)
                ),
                claim_supports=(Stage4ClaimSupportMetadata("claim-1", "ctx-1", "chunk-1", "document-1"),),
            ),
        )


def test_ch03_stage4_graph_rejects_unbounded_generated_claim_ids() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="generated claim IDs"):
        store.commit_completed_run_evaluation(
            transaction_id="tx-run-1",
            request_id="req-run-1",
            run=Stage4RunMetadata(
                run_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                generated_claim_ids=tuple(f"claim-{index}" for index in range(25)),
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
        )


def test_ch03_stage4_graph_rejects_unbounded_claim_supports() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)

    with pytest.raises(AcidCasConflictError, match="claim supports"):
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
                claim_supports=tuple(
                    Stage4ClaimSupportMetadata("claim-1", "ctx-1", "chunk-1", "document-1")
                    for _ in range(25)
                ),
            ),
        )


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


def test_ch03_stage4_graph_bounds_run_completed_event_payload_by_encoded_size() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())

    accepted = store.run_completed_event(
        event_id="event-1",
        run_id="run-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        operation_id="operation-1",
        payload={"body": "x" * 4085},
    )

    assert accepted.payload_hash == outbox_payload_hash({"body": "x" * 4085})
    with pytest.raises(AcidCasConflictError, match="event payload"):
        store.run_completed_event(
            event_id="event-2",
            run_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            operation_id="operation-1",
            payload={"body": "x" * 4086},
        )


def test_ch03_stage4_graph_rejects_direct_oversized_graph_event_payload() -> None:
    store = Stage4DurableGraphStore(AcidCasKernel())
    _commit_project_document_chunk(store)
    oversized_payload: dict[str, object] = {"body": "x" * 4086}

    with pytest.raises(AcidCasConflictError, match="event payload"):
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
                OutboxEventWrite(
                    event_id="event-1",
                    event_type="stage4.run.completed",
                    resource_id="run:tenant-1:owner-1:project-1:run-1",
                    resource_version=1,
                    operation_id="operation-1",
                    payload_hash=outbox_payload_hash(oversized_payload),
                    payload=oversized_payload,
                ),
            ),
        )


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
