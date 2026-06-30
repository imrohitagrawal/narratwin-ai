"""Stage 4 local product slice orchestration with source_chunk citations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Any, Literal

from backend.app.rag.chunking import checksum_text, chunk_document
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import (
    CHUNKING_STRATEGY_VERSION,
    MOCK_EMBEDDING_MODEL,
    MOCK_EMBEDDING_MODEL_VERSION,
    OWNER_LOCAL,
    RETRIEVAL_STRATEGY_VERSION,
    TENANT_LOCAL,
    EvaluationResult,
    GeneratedScript,
    KnowledgeChunk,
    RetrievedContext,
)
from backend.app.rag.providers import MockEmbeddingProvider, MockLLMProvider
from backend.app.rag.retrieval import retrieve_context
from backend.app.rag.store import InMemoryRagStore

MAX_UPLOAD_BYTES = 1_048_576
ALLOWED_EXTENSIONS = {".md", ".txt"}
ALLOWED_CONTENT_TYPES = {"text/markdown", "text/plain", "application/octet-stream"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Stage4Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass
class ProjectRecord:
    project_id: str
    name: str
    description: str
    default_audience: str
    default_language: str
    created_at: str
    updated_at: str


@dataclass
class DocumentRecord:
    document_id: str
    project_id: str
    source_filename: str
    content_type: str
    size_bytes: int
    checksum: str
    text: str
    document_status: Literal["STORED"] = "STORED"
    approval_status: Literal["PENDING", "APPROVED"] = "PENDING"
    ingestion_status: Literal["NOT_STARTED", "INGESTED"] = "NOT_STARTED"
    created_at: str = field(default_factory=_now)
    ingested_at: str | None = None


@dataclass
class IngestionRunRecord:
    ingestion_run_id: str
    project_id: str
    document_ids: list[str]
    status: Literal["COMPLETED"]
    chunk_count: int
    embedding_count: int
    created_at: str


@dataclass
class WalkthroughRunRecord:
    run_id: str
    project_id: str
    status: Literal["COMPLETED", "FAILED", "REFUSED"]
    evaluation_status: Literal["PASSED", "FAILED"] | None
    audience: str
    requested_language: str
    depth: str
    style: str
    accepted_script_text: str | None
    generated_script: GeneratedScript | None
    retrieved_context: list[RetrievedContext]
    evaluation: EvaluationResult | None
    created_at: str


class Stage4Service:
    def __init__(self) -> None:
        self.embedder = MockEmbeddingProvider()
        self.llm = MockLLMProvider()
        self.rag_store = InMemoryRagStore()
        self.projects: dict[str, ProjectRecord] = {}
        self.documents: dict[str, DocumentRecord] = {}
        self.ingestion_runs: dict[str, IngestionRunRecord] = {}
        self.walkthrough_runs: dict[str, WalkthroughRunRecord] = {}
        self.idempotency_records: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._project_counter = 0
        self._document_counter = 0
        self._ingestion_counter = 0
        self._run_counter = 0

    def reset(self) -> None:
        self.rag_store.clear()
        self.projects.clear()
        self.documents.clear()
        self.ingestion_runs.clear()
        self.walkthrough_runs.clear()
        self.idempotency_records.clear()
        self._project_counter = 0
        self._document_counter = 0
        self._ingestion_counter = 0
        self._run_counter = 0

    def create_project(
        self,
        *,
        name: str,
        description: str = "",
        default_audience: str = "RECRUITER",
        default_language: str = "en",
    ) -> ProjectRecord:
        if not name.strip():
            raise Stage4Error(422, "VALIDATION_ERROR", "Project name is required.")
        self._project_counter += 1
        now = _now()
        project = ProjectRecord(
            project_id=f"proj_{self._project_counter:06d}",
            name=name.strip(),
            description=description.strip(),
            default_audience=default_audience,
            default_language=default_language,
            created_at=now,
            updated_at=now,
        )
        self.projects[project.project_id] = project
        return project

    def upload_document(
        self,
        *,
        project_id: str,
        source_filename: str,
        content_type: str,
        data: bytes,
    ) -> DocumentRecord:
        self._require_project(project_id)
        safe_filename = sanitize_filename(source_filename)
        suffix = PurePath(safe_filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS or content_type not in ALLOWED_CONTENT_TYPES:
            raise Stage4Error(415, "UNSUPPORTED_MEDIA_TYPE", "Only markdown and plain text files are accepted.")
        if len(data) > MAX_UPLOAD_BYTES:
            raise Stage4Error(413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit.")
        text = decode_upload(data)
        if not text.strip():
            raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document is empty.")
        self._document_counter += 1
        document = DocumentRecord(
            document_id=f"doc_{self._document_counter:06d}",
            project_id=project_id,
            source_filename=safe_filename,
            content_type="text/markdown" if suffix == ".md" else "text/plain",
            size_bytes=len(data),
            checksum=checksum_text(text),
            text=text,
        )
        self.documents[document.document_id] = document
        return document

    def approve_document(self, *, project_id: str, document_id: str) -> DocumentRecord:
        document = self._require_document(project_id, document_id)
        document.approval_status = "APPROVED"
        return document

    def ingest_documents(self, *, project_id: str, document_ids: list[str]) -> IngestionRunRecord:
        self._require_project(project_id)
        if not document_ids:
            raise Stage4Error(422, "VALIDATION_ERROR", "At least one document is required.")
        stored_chunks: list[KnowledgeChunk] = []
        for document_id in document_ids:
            document = self._require_document(project_id, document_id)
            if document.approval_status != "APPROVED":
                raise Stage4Error(422, "DOCUMENT_NOT_APPROVED", "Document must be approved before ingestion.")
            chunks = chunk_document(
                document_id=document.document_id,
                project_id=project_id,
                tenant_id=TENANT_LOCAL,
                source_filename=document.source_filename,
                text=parse_document_text(document.text),
            )
            stored_chunks.extend(self.rag_store.add_chunks(chunks, self.embedder))
            document.ingestion_status = "INGESTED"
            document.ingested_at = _now()
        self._ingestion_counter += 1
        run = IngestionRunRecord(
            ingestion_run_id=f"ing_{self._ingestion_counter:06d}",
            project_id=project_id,
            document_ids=document_ids,
            status="COMPLETED",
            chunk_count=len(stored_chunks),
            embedding_count=len(stored_chunks),
            created_at=_now(),
        )
        self.ingestion_runs[run.ingestion_run_id] = run
        return run

    def generate_walkthrough(
        self,
        *,
        project_id: str,
        audience: str,
        requested_language: str,
        depth: str,
        style: str,
        prompt: str,
    ) -> WalkthroughRunRecord:
        self._require_project(project_id)
        self._run_counter += 1
        run_id = f"run_{self._run_counter:06d}"
        retrieved = retrieve_context(
            store=self.rag_store,
            embedder=self.embedder,
            tenant_id=TENANT_LOCAL,
            project_id=project_id,
            query=f"{audience} {prompt}",
            top_k=6,
            min_score=0.1,
        )
        if not retrieved:
            run = WalkthroughRunRecord(
                run_id=run_id,
                project_id=project_id,
                status="REFUSED",
                evaluation_status=None,
                audience=audience,
                requested_language=requested_language,
                depth=depth,
                style=style,
                accepted_script_text=None,
                generated_script=None,
                retrieved_context=[],
                evaluation=None,
                created_at=_now(),
            )
            self.walkthrough_runs[run_id] = run
            return run
        generated = self.llm.generate_script(
            audience=audience,
            prompt=prompt,
            retrieved_context=retrieved,
        )
        evaluation = evaluate_grounding(
            tenant_id=TENANT_LOCAL,
            project_id=project_id,
            run_id=run_id,
            candidate=generated,
            retrieved_context=retrieved,
        )
        run = WalkthroughRunRecord(
            run_id=run_id,
            project_id=project_id,
            status="COMPLETED" if evaluation.evaluation_status == "PASSED" else "FAILED",
            evaluation_status=evaluation.evaluation_status,
            audience=audience,
            requested_language=requested_language,
            depth=depth,
            style=style,
            accepted_script_text=generated.text if evaluation.evaluation_status == "PASSED" else None,
            generated_script=generated,
            retrieved_context=retrieved,
            evaluation=evaluation,
            created_at=_now(),
        )
        self.walkthrough_runs[run_id] = run
        return run

    def _require_project(self, project_id: str) -> ProjectRecord:
        project = self.projects.get(project_id)
        if project is None:
            raise Stage4Error(404, "NOT_FOUND", "Project not found.")
        return project

    def _require_document(self, project_id: str, document_id: str) -> DocumentRecord:
        document = self.documents.get(document_id)
        if document is None or document.project_id != project_id:
            raise Stage4Error(404, "NOT_FOUND", "Knowledge document not found.")
        return document


def sanitize_filename(filename: str) -> str:
    name = PurePath(filename).name.strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise Stage4Error(422, "VALIDATION_ERROR", "Invalid filename.")
    return name


def decode_upload(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document must be UTF-8 text.") from exc


def parse_document_text(text: str) -> str:
    return text.replace("\x00", "").strip()


def project_to_api(project: ProjectRecord) -> dict[str, Any]:
    return {
        "projectId": project.project_id,
        "tenantId": TENANT_LOCAL,
        "ownerId": OWNER_LOCAL,
        "name": project.name,
        "description": project.description,
        "projectStatus": "ACTIVE",
        "defaultAudience": project.default_audience,
        "defaultLanguage": project.default_language,
        "createdAt": project.created_at,
        "updatedAt": project.updated_at,
    }


def document_to_api(document: DocumentRecord) -> dict[str, Any]:
    return {
        "documentId": document.document_id,
        "tenantId": TENANT_LOCAL,
        "projectId": document.project_id,
        "sourceFilename": document.source_filename,
        "contentType": document.content_type,
        "sizeBytes": document.size_bytes,
        "checksum": document.checksum,
        "documentStatus": document.document_status,
        "approvalStatus": document.approval_status,
        "ingestionStatus": document.ingestion_status,
        "createdAt": document.created_at,
    }


def ingestion_to_api(run: IngestionRunRecord) -> dict[str, Any]:
    return {
        "ingestionRunId": run.ingestion_run_id,
        "tenantId": TENANT_LOCAL,
        "projectId": run.project_id,
        "status": run.status,
        "documentIds": run.document_ids,
        "chunkCount": run.chunk_count,
        "embeddingCount": run.embedding_count,
        "createdAt": run.created_at,
    }


def walkthrough_to_api(run: WalkthroughRunRecord) -> dict[str, Any]:
    base: dict[str, Any] = {
        "runId": run.run_id,
        "tenantId": TENANT_LOCAL,
        "projectId": run.project_id,
        "status": run.status,
        "evaluationStatus": run.evaluation_status,
        "audience": run.audience,
        "requestedLanguage": run.requested_language,
        "depth": run.depth,
        "style": run.style,
        "contextRefs": [_context_ref_to_api(context, run) for context in run.retrieved_context],
        "provider": {"provider": "mock", "providerMode": "LOCAL"},
        "trace": {
            "traceId": "trace_" + run.run_id.removeprefix("run_"),
            "latencyMs": 0,
            "estimatedCost": 0,
        },
        "createdAt": run.created_at,
    }
    if run.accepted_script_text is not None and run.evaluation is not None:
        base["acceptedScriptText"] = run.accepted_script_text
        base["evaluation"] = evaluation_to_api(run.evaluation, run)
    elif run.status == "REFUSED":
        base["failure"] = {
            "reasonCode": "EMPTY_CONTEXT",
            "message": "No approved ingested context was available for generation.",
            "unsupportedClaimCount": 0,
        }
    elif run.evaluation is not None:
        base["failure"] = {
            "reasonCode": "UNSUPPORTED_PROJECT_FACT",
            "message": "Generated output contained unsupported project facts.",
            "unsupportedClaimCount": run.evaluation.unsupported_claim_count,
        }
        base["redactedUnsupportedExcerpts"] = [
            claim.claim_text for claim in run.evaluation.unsupported_claims
        ]
    return base


def evaluation_to_api(evaluation: EvaluationResult, run: WalkthroughRunRecord) -> dict[str, Any]:
    return {
        "schema": "EvaluationSummary",
        "evaluationId": evaluation.evaluation_id,
        "evaluationStatus": evaluation.evaluation_status,
        "groundednessScore": evaluation.groundedness_score,
        "unsupportedClaimCount": evaluation.unsupported_claim_count,
        "unsupportedClaims": [
            {
                "claimId": claim.claim_id,
                "claimText": claim.claim_text,
                "reason": claim.reason,
            }
            for claim in evaluation.unsupported_claims
        ],
        "claimSupports": [
            {
                "claimSupportId": support.claim_support_id,
                "tenantId": TENANT_LOCAL,
                "projectId": evaluation.project_id,
                "runId": evaluation.run_id,
                "evaluationId": evaluation.evaluation_id,
                "claimId": support.claim_id,
                "contextRefId": support.context_ref_id,
                "chunkId": support.chunk_id,
                "documentId": support.document_id,
                "supportStatus": support.support_status,
                "supportScore": support.support_score,
                "supportReason": support.support_reason,
            }
            for support in evaluation.claim_supports
        ],
        "contextRefCoverage": evaluation.context_ref_coverage,
        "embeddingProvider": "mock",
        "embeddingModel": MOCK_EMBEDDING_MODEL,
        "embeddingModelVersion": MOCK_EMBEDDING_MODEL_VERSION,
        "embeddingDimension": 16,
        "vectorStore": "memory",
        "retrievalStrategyVersion": RETRIEVAL_STRATEGY_VERSION,
        "retrievalTopK": 6,
        "retrievalScoreThreshold": 0.1,
        "policyVersion": evaluation.policy_version,
        "schemaVersion": evaluation.schema_version,
        "safetyPolicyVersion": evaluation.safety_policy_version,
        "contextRefs": [_context_ref_to_api(context, run) for context in run.retrieved_context],
    }


def _context_ref_to_api(context: RetrievedContext, run: WalkthroughRunRecord) -> dict[str, Any]:
    claim = None
    if run.generated_script is not None:
        claim = next(
            (candidate for candidate in run.generated_script.claims if candidate.chunk_id == context.chunk.chunk_id),
            None,
        )
    excerpt = context.chunk.text[:240]
    return {
        "contextRefId": context.context_ref_id,
        "tenantId": TENANT_LOCAL,
        "projectId": context.chunk.project_id,
        "claimId": claim.claim_id if claim is not None else "",
        "chunkId": context.chunk.chunk_id,
        "documentId": context.chunk.document_id,
        "sourceFilename": context.chunk.source_filename,
        "chunkIndex": context.chunk.chunk_index,
        "checksum": context.chunk.checksum,
        "scriptSpanStart": claim.script_span_start if claim is not None else 0,
        "scriptSpanEnd": claim.script_span_end if claim is not None else 0,
        "evidenceSnapshot": {
            "evidenceSnapshotId": "evsnap_" + context.context_ref_id.removeprefix("ctx_"),
            "tenantId": TENANT_LOCAL,
            "projectId": context.chunk.project_id,
            "documentId": context.chunk.document_id,
            "chunkId": context.chunk.chunk_id,
            "sourceFilename": context.chunk.source_filename,
            "chunkIndex": context.chunk.chunk_index,
            "sourceDocumentChecksum": _document_checksum_from_chunk(context.chunk),
            "chunkChecksum": context.chunk.checksum,
            "chunkingStrategyVersion": CHUNKING_STRATEGY_VERSION,
            "retrievalScore": round(context.score, 4),
            "redactedExcerpt": excerpt,
            "excerptStart": 0,
            "excerptEnd": len(excerpt),
            "redactionFlags": [],
            "capturedAt": run.created_at,
            "snapshotChecksum": checksum_text(excerpt),
        },
    }


def _document_checksum_from_chunk(chunk: KnowledgeChunk) -> str:
    return "sha256:" + hashlib.sha256(f"{chunk.document_id}:{chunk.source_filename}".encode()).hexdigest()


stage4_service = Stage4Service()
