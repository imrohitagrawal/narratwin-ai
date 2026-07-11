"""Stage 4 durable graph adapter for Phase 1 Closure CH-03."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    OutboxEventWrite,
    StoredRecord,
    TransactionCommitResult,
    TransactionWrite,
    outbox_payload_hash,
)


@dataclass(frozen=True, slots=True)
class Stage4ProjectMetadata:
    project_id: str
    tenant_id: str
    owner_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Stage4DocumentMetadata:
    document_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    source_filename: str
    source_document_checksum: str
    approved_at: str


@dataclass(frozen=True, slots=True)
class Stage4ChunkMetadata:
    chunk_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    document_id: str
    source_filename: str
    source_document_checksum: str
    approved_at: str
    chunk_checksum: str
    chunk_index: int
    token_count: int


@dataclass(frozen=True, slots=True)
class Stage4ContextRefMetadata:
    context_ref_id: str
    chunk_id: str
    document_id: str


@dataclass(frozen=True, slots=True)
class Stage4ClaimSupportMetadata:
    claim_id: str
    context_ref_id: str
    chunk_id: str
    document_id: str


@dataclass(frozen=True, slots=True)
class Stage4RunMetadata:
    run_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    generated_claim_ids: tuple[str, ...]
    status: Literal["COMPLETED"] = "COMPLETED"


@dataclass(frozen=True, slots=True)
class Stage4EvaluationMetadata:
    evaluation_id: str
    run_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    evaluation_status: Literal["PASSED", "FAILED"]
    context_refs: tuple[Stage4ContextRefMetadata, ...]
    claim_supports: tuple[Stage4ClaimSupportMetadata, ...]


class Stage4DurableGraphStore:
    """Validated Stage 4 graph writes backed by the ACID/CAS kernel."""

    def __init__(self, kernel: AcidCasKernel) -> None:
        self._kernel = kernel

    def commit_project_document_chunks(
        self,
        *,
        transaction_id: str,
        request_id: str,
        project: Stage4ProjectMetadata,
        document: Stage4DocumentMetadata,
        chunks: tuple[Stage4ChunkMetadata, ...],
    ) -> TransactionCommitResult:
        self._validate_project_document(project=project, document=document)
        if not chunks:
            raise AcidCasConflictError("Stage 4 graph requires at least one chunk.")
        for chunk in chunks:
            self._validate_document_chunk(document=document, chunk=chunk)

        writes = (
            self._project_write(project),
            self._document_write(document),
            *(self._chunk_write(chunk) for chunk in chunks),
        )
        return self._kernel.commit(
            transaction_id=transaction_id,
            request_id=request_id,
            request_checksum=_request_checksum(writes),
            writes=writes,
        )

    def commit_completed_run_evaluation(
        self,
        *,
        transaction_id: str,
        request_id: str,
        run: Stage4RunMetadata,
        evaluation: Stage4EvaluationMetadata,
        graph_events: tuple[OutboxEventWrite, ...] = (),
    ) -> TransactionCommitResult:
        self._validate_run_evaluation(run=run, evaluation=evaluation)
        writes = (self._run_write(run), self._evaluation_write(evaluation))
        return self._kernel.commit(
            transaction_id=transaction_id,
            request_id=request_id,
            request_checksum=_request_checksum(writes),
            writes=writes,
            outbox_events=graph_events,
        )

    def run_completed_event(
        self,
        *,
        event_id: str,
        run_id: str,
        tenant_id: str,
        owner_id: str,
        project_id: str,
        operation_id: str,
        payload: dict[str, object],
    ) -> OutboxEventWrite:
        return OutboxEventWrite(
            event_id=event_id,
            event_type="stage4.run.completed",
            resource_id=_resource_id("run", tenant_id, owner_id, project_id, run_id),
            resource_version=1,
            operation_id=operation_id,
            payload_hash=outbox_payload_hash(payload),
            payload=payload,
        )

    def get_project(self, tenant_id: str, owner_id: str, project_id: str) -> StoredRecord:
        return self._kernel.get(
            entity_type="project",
            entity_id=project_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            project_id=project_id,
        )

    def get_chunk(self, tenant_id: str, owner_id: str, project_id: str, chunk_id: str) -> StoredRecord:
        return self._kernel.get(
            entity_type="chunk",
            entity_id=chunk_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            project_id=project_id,
        )

    def get_run(self, tenant_id: str, owner_id: str, project_id: str, run_id: str) -> StoredRecord:
        return self._kernel.get(
            entity_type="run",
            entity_id=run_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            project_id=project_id,
        )

    def _validate_project_document(
        self, *, project: Stage4ProjectMetadata, document: Stage4DocumentMetadata
    ) -> None:
        _validate_identity(project.project_id, "project_id")
        _validate_identity(project.tenant_id, "tenant_id")
        _validate_identity(project.owner_id, "owner_id")
        _validate_identity(document.document_id, "document_id")
        if (document.tenant_id, document.owner_id, document.project_id) != (
            project.tenant_id,
            project.owner_id,
            project.project_id,
        ):
            raise AcidCasConflictError("Stage 4 document scope must match the durable project.")
        _validate_document_fields(document)

    def _validate_document_chunk(self, *, document: Stage4DocumentMetadata, chunk: Stage4ChunkMetadata) -> None:
        _validate_identity(chunk.chunk_id, "chunk_id")
        if (chunk.tenant_id, chunk.owner_id, chunk.project_id, chunk.document_id) != (
            document.tenant_id,
            document.owner_id,
            document.project_id,
            document.document_id,
        ):
            raise AcidCasConflictError("Stage 4 chunk scope must match the durable document.")
        if chunk.source_filename != document.source_filename:
            raise AcidCasConflictError("Stage 4 chunk source filename must match the durable document.")
        if chunk.source_document_checksum != document.source_document_checksum:
            raise AcidCasConflictError("Stage 4 chunk document checksum must match the durable document.")
        if chunk.approved_at != document.approved_at:
            raise AcidCasConflictError("Stage 4 chunk approval timestamp must match the durable document.")
        if chunk.chunk_index < 0 or chunk.token_count <= 0:
            raise AcidCasConflictError("Stage 4 chunk metadata must use non-negative index and positive token count.")
        _validate_checksum(chunk.chunk_checksum, "chunk_checksum")

    def _validate_run_evaluation(
        self, *, run: Stage4RunMetadata, evaluation: Stage4EvaluationMetadata
    ) -> None:
        _validate_identity(run.run_id, "run_id")
        _validate_identity(evaluation.evaluation_id, "evaluation_id")
        self.get_project(run.tenant_id, run.owner_id, run.project_id)
        if (
            evaluation.run_id,
            evaluation.tenant_id,
            evaluation.owner_id,
            evaluation.project_id,
        ) != (run.run_id, run.tenant_id, run.owner_id, run.project_id):
            raise AcidCasConflictError("Stage 4 evaluation scope must match the durable run.")
        if run.status != "COMPLETED" or evaluation.evaluation_status != "PASSED":
            raise AcidCasConflictError("CH-03 only records completed Stage 4 runs with passing evaluations.")
        context_by_ref = {context.context_ref_id: context for context in evaluation.context_refs}
        if len(context_by_ref) != len(evaluation.context_refs):
            raise AcidCasConflictError("Stage 4 evaluation context refs must be unique.")
        claim_ids = set(run.generated_claim_ids)
        if not claim_ids:
            raise AcidCasConflictError("Stage 4 completed run must include generated claim IDs.")
        for context in evaluation.context_refs:
            _validate_identity(context.context_ref_id, "context_ref_id")
            chunk = self.get_chunk(run.tenant_id, run.owner_id, run.project_id, context.chunk_id)
            if chunk.payload["documentId"] != context.document_id:
                raise AcidCasConflictError("Stage 4 context ref chunk must match the durable document.")
        for support in evaluation.claim_supports:
            if support.context_ref_id not in context_by_ref:
                raise AcidCasConflictError("Stage 4 claim support references an unknown context ref.")
            if support.claim_id not in claim_ids:
                raise AcidCasConflictError("Stage 4 claim support references an unknown generated claim.")
            context = context_by_ref[support.context_ref_id]
            if (support.chunk_id, support.document_id) != (context.chunk_id, context.document_id):
                raise AcidCasConflictError("Stage 4 claim support must match its context ref chunk and document.")

    def _project_write(self, project: Stage4ProjectMetadata) -> TransactionWrite:
        return TransactionWrite(
            entity_type="project",
            entity_id=project.project_id,
            tenant_id=project.tenant_id,
            owner_id=project.owner_id,
            project_id=project.project_id,
            expected_version=None,
            state="OPEN",
            payload={"projectId": project.project_id, "name": project.name},
        )

    def _document_write(self, document: Stage4DocumentMetadata) -> TransactionWrite:
        return TransactionWrite(
            entity_type="document",
            entity_id=document.document_id,
            tenant_id=document.tenant_id,
            owner_id=document.owner_id,
            project_id=document.project_id,
            expected_version=None,
            state="OPEN",
            payload={
                "documentId": document.document_id,
                "sourceFilename": document.source_filename,
                "sourceDocumentChecksum": document.source_document_checksum,
                "approvedAt": document.approved_at,
            },
        )

    def _chunk_write(self, chunk: Stage4ChunkMetadata) -> TransactionWrite:
        return TransactionWrite(
            entity_type="chunk",
            entity_id=chunk.chunk_id,
            tenant_id=chunk.tenant_id,
            owner_id=chunk.owner_id,
            project_id=chunk.project_id,
            expected_version=None,
            state="TERMINAL",
            payload={
                "chunkId": chunk.chunk_id,
                "documentId": chunk.document_id,
                "sourceFilename": chunk.source_filename,
                "sourceDocumentChecksum": chunk.source_document_checksum,
                "approvedAt": chunk.approved_at,
                "chunkChecksum": chunk.chunk_checksum,
                "chunkIndex": chunk.chunk_index,
                "tokenCount": chunk.token_count,
            },
            terminal_reason="INDEXED",
        )

    def _run_write(self, run: Stage4RunMetadata) -> TransactionWrite:
        return TransactionWrite(
            entity_type="run",
            entity_id=run.run_id,
            tenant_id=run.tenant_id,
            owner_id=run.owner_id,
            project_id=run.project_id,
            expected_version=None,
            state="TERMINAL",
            payload={
                "runId": run.run_id,
                "status": run.status,
                "generatedClaimIds": list(run.generated_claim_ids),
            },
            terminal_reason=run.status,
        )

    def _evaluation_write(self, evaluation: Stage4EvaluationMetadata) -> TransactionWrite:
        return TransactionWrite(
            entity_type="evaluation",
            entity_id=evaluation.evaluation_id,
            tenant_id=evaluation.tenant_id,
            owner_id=evaluation.owner_id,
            project_id=evaluation.project_id,
            expected_version=None,
            state="TERMINAL",
            payload={
                "evaluationId": evaluation.evaluation_id,
                "runId": evaluation.run_id,
                "evaluationStatus": evaluation.evaluation_status,
                "contextRefs": [asdict(context) for context in evaluation.context_refs],
                "claimSupports": [asdict(support) for support in evaluation.claim_supports],
            },
            terminal_reason=evaluation.evaluation_status,
        )


def _request_checksum(writes: tuple[TransactionWrite, ...]) -> str:
    payload = [
        {
            "entityType": write.entity_type,
            "entityId": write.entity_id,
            "tenantId": write.tenant_id,
            "ownerId": write.owner_id,
            "projectId": write.project_id,
            "payload": write.payload,
            "state": write.state,
            "terminalReason": write.terminal_reason,
        }
        for write in writes
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _resource_id(entity_type: str, tenant_id: str, owner_id: str, project_id: str, entity_id: str) -> str:
    return f"{entity_type}:{tenant_id}:{owner_id}:{project_id}:{entity_id}"


def _validate_document_fields(document: Stage4DocumentMetadata) -> None:
    _validate_text_field(document.source_filename, "source_filename")
    _validate_checksum(document.source_document_checksum, "source_document_checksum")
    if not document.approved_at.strip() or document.approved_at != document.approved_at.strip():
        raise AcidCasConflictError("Stage 4 approved_at must be non-empty and trimmed.")


def _validate_checksum(value: str, label: str) -> None:
    if not value.startswith("sha256:") or not value.removeprefix("sha256:").strip():
        raise AcidCasConflictError(f"Stage 4 {label} must be a sha256-prefixed checksum.")


def _validate_identity(value: str, label: str) -> None:
    if not value.strip() or value != value.strip() or ":" in value:
        raise AcidCasConflictError(f"Stage 4 {label} must be non-empty, trimmed, and colon-free.")


def _validate_text_field(value: str, label: str) -> None:
    if not value.strip() or value != value.strip():
        raise AcidCasConflictError(f"Stage 4 {label} must be non-empty and trimmed.")
