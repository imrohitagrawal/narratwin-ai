"""FastAPI application for NarraTwin AI local stages."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.stage4 import (
    LocalPrincipal,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_REQUEST_BYTES,
    Stage4Error,
    document_to_api,
    ingestion_to_api,
    project_to_api,
    stage4_service,
    walkthrough_to_api,
)

ErrorDetailValue = str | int | float | bool


class HealthResponse(BaseModel):
    """Stable health response shape used by CI smoke checks."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    service: Literal["narratwin-ai-backend"]
    stage: Literal["4"]


class ReadinessResponse(HealthResponse):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    checked_at: str = Field(alias="checkedAt")


class ErrorBody(BaseModel):
    """API error detail shape from the locked contract."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    code: str
    message: str
    details: dict[str, ErrorDetailValue] = Field(default_factory=dict)
    request_id: str = Field(alias="requestId")


class ErrorResponse(BaseModel):
    """Locked error envelope for future /api/v1 endpoints."""

    model_config = ConfigDict(frozen=True)

    error: ErrorBody


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    name: str
    description: str = ""
    default_audience: str = Field(default="RECRUITER", alias="defaultAudience")
    default_language: str = Field(default="en", alias="defaultLanguage")


class ApproveDocumentRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    approval_status: Literal["APPROVED"] = Field(alias="approvalStatus")
    review_note: str = Field(default="", alias="reviewNote")


class StartIngestionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_ids: list[str] = Field(alias="documentIds")


class GenerateWalkthroughRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    audience: Literal["RECRUITER", "HIRING_MANAGER", "ENGINEER", "PRODUCT_LEADER", "BEGINNER", "GLOBAL_VIEWER"] = "RECRUITER"
    requested_language: Literal["en"] = Field(default="en", alias="requestedLanguage")
    depth: Literal["CONCISE", "STANDARD", "DEEP"] = "CONCISE"
    style: Literal["PLAIN", "CONFIDENT", "TECHNICAL", "EXECUTIVE"] = "CONFIDENT"
    prompt: str = "Create a concise grounded walkthrough."


class ProjectResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    project_id: str = Field(alias="projectId")
    tenant_id: str = Field(alias="tenantId")
    owner_id: str = Field(alias="ownerId")
    name: str
    description: str
    project_status: Literal["ACTIVE"] = Field(alias="projectStatus")
    default_audience: str = Field(alias="defaultAudience")
    default_language: str = Field(alias="defaultLanguage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class DocumentResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_id: str = Field(alias="documentId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    source_filename: str = Field(alias="sourceFilename")
    content_type: str = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes")
    checksum: str
    document_status: Literal["STORED"] = Field(alias="documentStatus")
    approval_status: Literal["PENDING", "APPROVED"] = Field(alias="approvalStatus")
    ingestion_status: Literal["NOT_STARTED", "INGESTED"] = Field(alias="ingestionStatus")
    created_at: str = Field(alias="createdAt")
    approved_at: str | None = Field(default=None, alias="approvedAt")


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    ingestion_run_id: str = Field(alias="ingestionRunId")
    tenant_id: str = Field(alias="tenantId")
    actor_id: str = Field(alias="actorId")
    project_id: str = Field(alias="projectId")
    status: Literal["COMPLETED"]
    document_ids: list[str] = Field(alias="documentIds")
    chunk_count: int = Field(alias="chunkCount")
    embedding_count: int = Field(alias="embeddingCount")
    created_at: str = Field(alias="createdAt")


class EvidenceSnapshotResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    evidence_snapshot_id: str = Field(alias="evidenceSnapshotId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    document_id: str = Field(alias="documentId")
    chunk_id: str = Field(alias="chunkId")
    source_filename: str = Field(alias="sourceFilename")
    chunk_index: int = Field(alias="chunkIndex")
    source_document_checksum: str = Field(alias="sourceDocumentChecksum")
    chunk_checksum: str = Field(alias="chunkChecksum")
    chunking_strategy_version: str = Field(alias="chunkingStrategyVersion")
    retrieval_score: float = Field(alias="retrievalScore")
    redacted_excerpt: str = Field(alias="redactedExcerpt")
    excerpt_start: int = Field(alias="excerptStart")
    excerpt_end: int = Field(alias="excerptEnd")
    redaction_flags: list[str] = Field(alias="redactionFlags")
    captured_at: str = Field(alias="capturedAt")
    snapshot_checksum: str = Field(alias="snapshotChecksum")


class ContextRefResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    context_ref_id: str = Field(alias="contextRefId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    claim_id: str = Field(alias="claimId")
    chunk_id: str = Field(alias="chunkId")
    document_id: str = Field(alias="documentId")
    source_filename: str = Field(alias="sourceFilename")
    chunk_index: int = Field(alias="chunkIndex")
    checksum: str
    script_span_start: int = Field(alias="scriptSpanStart")
    script_span_end: int = Field(alias="scriptSpanEnd")
    evidence_snapshot: EvidenceSnapshotResponse = Field(alias="evidenceSnapshot")


class UnsupportedClaimResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_id: str = Field(alias="claimId")
    claim_text: str = Field(alias="claimText")
    reason: str


class ClaimSupportResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_support_id: str = Field(alias="claimSupportId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    run_id: str = Field(alias="runId")
    evaluation_id: str = Field(alias="evaluationId")
    claim_id: str = Field(alias="claimId")
    context_ref_id: str = Field(alias="contextRefId")
    chunk_id: str = Field(alias="chunkId")
    document_id: str = Field(alias="documentId")
    support_status: Literal["SUPPORTED"] = Field(alias="supportStatus")
    support_score: float = Field(alias="supportScore")
    support_reason: str = Field(alias="supportReason")
    evidence_snapshot: EvidenceSnapshotResponse = Field(alias="evidenceSnapshot")
    citation_index: int = Field(alias="citationIndex")


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_name: Literal["EvaluationSummary"] = Field(alias="schema")
    evaluation_id: str = Field(alias="evaluationId")
    evaluation_status: Literal["PASSED", "FAILED"] = Field(alias="evaluationStatus")
    groundedness_score: float = Field(alias="groundednessScore")
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")
    unsupported_claims: list[UnsupportedClaimResponse] = Field(alias="unsupportedClaims")
    claim_supports: list[ClaimSupportResponse] = Field(alias="claimSupports")
    context_ref_coverage: float = Field(alias="contextRefCoverage")
    embedding_provider: str = Field(alias="embeddingProvider")
    embedding_model: str = Field(alias="embeddingModel")
    embedding_model_version: str = Field(alias="embeddingModelVersion")
    embedding_dimension: int = Field(alias="embeddingDimension")
    vector_store: str = Field(alias="vectorStore")
    retrieval_strategy_version: str = Field(alias="retrievalStrategyVersion")
    retrieval_top_k: int = Field(alias="retrievalTopK")
    retrieval_score_threshold: float = Field(alias="retrievalScoreThreshold")
    policy_version: str = Field(alias="policyVersion")
    schema_version: str = Field(alias="schemaVersion")
    safety_policy_version: str = Field(alias="safetyPolicyVersion")
    context_refs: list[ContextRefResponse] = Field(alias="contextRefs")


class ProviderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: Literal["mock"]
    provider_mode: Literal["LOCAL"] = Field(alias="providerMode")


class TraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    trace_id: str = Field(alias="traceId")
    latency_ms: int = Field(alias="latencyMs")
    estimated_cost: int = Field(alias="estimatedCost")


class FailureResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    reason_code: str = Field(alias="reasonCode")
    message: str
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")


class WalkthroughRunResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    run_id: str = Field(alias="runId")
    tenant_id: str = Field(alias="tenantId")
    actor_id: str = Field(alias="actorId")
    project_id: str = Field(alias="projectId")
    status: Literal["COMPLETED", "FAILED", "REFUSED"]
    evaluation_status: Literal["PASSED", "FAILED"] | None = Field(alias="evaluationStatus")
    audience: str
    requested_language: str = Field(alias="requestedLanguage")
    depth: str
    style: str
    context_refs: list[ContextRefResponse] = Field(alias="contextRefs")
    provider: ProviderResponse
    trace: TraceResponse
    created_at: str = Field(alias="createdAt")
    accepted_script_text: str | None = Field(default=None, alias="acceptedScriptText")
    evaluation: EvaluationResponse | None = None
    failure: FailureResponse | None = None
    redacted_unsupported_excerpts: list[str] = Field(default_factory=list, alias="redactedUnsupportedExcerpts")


async def local_principal(x_local_user_id: str | None = Header(default=None, alias="X-Local-User-Id")) -> LocalPrincipal:
    actor_id = (x_local_user_id or "").strip()
    return LocalPrincipal(actor_id=actor_id or "user_local")


async def idempotency_key_header(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    key = (idempotency_key or "").strip()
    if not key:
        raise Stage4Error(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required for write requests.")
    return key


app = FastAPI(
    title="NarraTwin AI API",
    version="0.1.0",
    docs_url=None,
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)
API_V1_HEALTH_PATH = "/api/v1/healthz"
API_V1_READY_PATH = "/api/v1/readyz"
API_V1_PROJECTS_PATH = "/api/v1/projects"
api_v1 = APIRouter(prefix="/api/v1")
FOUNDATION_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


@app.middleware("http")
async def add_foundation_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = request_id
    if request.method == "POST" and request.url.path.endswith("/knowledge-documents"):
        content_length = request.headers.get("Content-Length")
        try:
            upload_request_bytes = int(content_length) if content_length is not None else 0
        except ValueError:
            upload_request_bytes = MAX_UPLOAD_REQUEST_BYTES + 1
        if upload_request_bytes > MAX_UPLOAD_REQUEST_BYTES:
            return error_response(
                request=request,
                status_code=413,
                code="UPLOAD_TOO_LARGE",
                message="Upload exceeds the Stage 4 size limit.",
            )
    response = await call_next(request)
    for header, value in FOUNDATION_HEADERS.items():
        response.headers[header] = value
    response.headers["X-Request-Id"] = request_id
    return response


def request_id_for(request: Request) -> str:
    return str(getattr(request.state, "request_id", "")) or str(uuid4())


def error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, ErrorDetailValue] | None = None,
) -> JSONResponse:
    request_id = request_id_for(request)
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
            requestId=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(by_alias=True),
        headers={**FOUNDATION_HEADERS, "X-Request-Id": request_id},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_SERVER_ERROR" if exc.status_code >= 500 else "HTTP_ERROR"
    message = "Internal server error." if exc.status_code >= 500 else str(exc.detail) if exc.detail else "Request failed."
    return error_response(request=request, status_code=exc.status_code, code=code, message=message)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_SERVER_ERROR" if exc.status_code >= 500 else "HTTP_ERROR"
    message = "Internal server error." if exc.status_code >= 500 else str(exc.detail) if exc.detail else "Request failed."
    return error_response(request=request, status_code=exc.status_code, code=code, message=message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details={"errorCount": len(exc.errors())},
    )


@app.exception_handler(Stage4Error)
async def stage4_error_handler(request: Request, exc: Stage4Error) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error.",
    )


def health_payload() -> HealthResponse:
    return HealthResponse(status="ok", service="narratwin-ai-backend", stage="4")


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz() -> HealthResponse:
    return health_payload()


@app.get("/readyz", response_model=ReadinessResponse, tags=["health"])
def readyz() -> ReadinessResponse:
    return ReadinessResponse(
        **health_payload().model_dump(),
        checkedAt=datetime.now(UTC).isoformat(),
    )


@api_v1.get("/healthz", response_model=HealthResponse, tags=["health"])
def api_healthz() -> HealthResponse:
    return health_payload()


@api_v1.get("/readyz", response_model=ReadinessResponse, tags=["health"])
def api_readyz() -> ReadinessResponse:
    return readyz()


@api_v1.post("/projects", status_code=201, response_model=ProjectResponse, tags=["projects"])
def create_project(
    request: CreateProjectRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> ProjectResponse:
    project = stage4_service.create_project(
        principal=principal,
        name=request.name,
        description=request.description,
        default_audience=request.default_audience,
        default_language=request.default_language,
        idempotency_key=idempotency_key,
    )
    return ProjectResponse.model_validate(project_to_api(project))


@api_v1.post(
    "/projects/{project_id}/knowledge-documents",
    status_code=201,
    response_model=DocumentResponse,
    tags=["knowledge"],
)
async def upload_knowledge_document(
    project_id: str,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
    file: UploadFile = File(...),
) -> DocumentResponse:
    data = await read_upload_with_limit(file)
    document = stage4_service.upload_document(
        principal=principal,
        project_id=project_id,
        source_filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        idempotency_key=idempotency_key,
    )
    return DocumentResponse.model_validate(document_to_api(document))


@api_v1.patch(
    "/projects/{project_id}/knowledge-documents/{document_id}/approval",
    response_model=DocumentResponse,
    tags=["knowledge"],
)
def approve_knowledge_document(
    project_id: str,
    document_id: str,
    request: ApproveDocumentRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> DocumentResponse:
    del request
    document = stage4_service.approve_document(
        principal=principal,
        project_id=project_id,
        document_id=document_id,
        idempotency_key=idempotency_key,
    )
    return DocumentResponse.model_validate(document_to_api(document))


@api_v1.post(
    "/projects/{project_id}/ingestion-runs",
    status_code=201,
    response_model=IngestionRunResponse,
    tags=["ingestion"],
)
def start_ingestion_run(
    project_id: str,
    request: StartIngestionRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> IngestionRunResponse:
    run = stage4_service.ingest_documents(
        principal=principal,
        project_id=project_id,
        document_ids=request.document_ids,
        idempotency_key=idempotency_key,
    )
    return IngestionRunResponse.model_validate(ingestion_to_api(run))


@api_v1.post(
    "/projects/{project_id}/walkthrough-runs",
    status_code=201,
    response_model=WalkthroughRunResponse,
    response_model_exclude_none=True,
    tags=["walkthrough"],
)
def generate_walkthrough_run(
    project_id: str,
    request: GenerateWalkthroughRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> WalkthroughRunResponse:
    run = stage4_service.generate_walkthrough(
        principal=principal,
        project_id=project_id,
        audience=request.audience,
        requested_language=request.requested_language,
        depth=request.depth,
        style=request.style,
        prompt=request.prompt,
        idempotency_key=idempotency_key,
    )
    return WalkthroughRunResponse.model_validate(walkthrough_to_api(run))


async def read_upload_with_limit(file: UploadFile) -> bytes:
    data = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise Stage4Error(413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit.")


def reset_app_state_for_tests() -> None:
    stage4_service.reset()


app.include_router(api_v1)
