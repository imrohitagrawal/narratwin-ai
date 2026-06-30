"""FastAPI application for NarraTwin AI local stages."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.stage4 import (
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

    audience: Literal["RECRUITER", "ENGINEER", "PRODUCT_LEADER", "CUSTOMER"] = "RECRUITER"
    requested_language: Literal["en"] = Field(default="en", alias="requestedLanguage")
    depth: Literal["CONCISE", "STANDARD", "DETAILED"] = "CONCISE"
    style: Literal["CONFIDENT", "TECHNICAL", "FRIENDLY"] = "CONFIDENT"
    prompt: str = "Create a concise grounded walkthrough."


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


@api_v1.post("/projects", status_code=201, tags=["projects"])
def create_project(request: CreateProjectRequest) -> dict[str, object]:
    project = stage4_service.create_project(
        name=request.name,
        description=request.description,
        default_audience=request.default_audience,
        default_language=request.default_language,
    )
    return project_to_api(project)


@api_v1.post(
    "/projects/{project_id}/knowledge-documents",
    status_code=201,
    tags=["knowledge"],
)
async def upload_knowledge_document(
    project_id: str,
    file: UploadFile = File(...),
) -> dict[str, object]:
    data = await file.read()
    document = stage4_service.upload_document(
        project_id=project_id,
        source_filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return document_to_api(document)


@api_v1.patch(
    "/projects/{project_id}/knowledge-documents/{document_id}/approval",
    tags=["knowledge"],
)
def approve_knowledge_document(
    project_id: str,
    document_id: str,
    request: ApproveDocumentRequest,
) -> dict[str, object]:
    del request
    document = stage4_service.approve_document(project_id=project_id, document_id=document_id)
    return document_to_api(document)


@api_v1.post("/projects/{project_id}/ingestion-runs", status_code=201, tags=["ingestion"])
def start_ingestion_run(project_id: str, request: StartIngestionRequest) -> dict[str, object]:
    run = stage4_service.ingest_documents(project_id=project_id, document_ids=request.document_ids)
    return ingestion_to_api(run)


@api_v1.post("/projects/{project_id}/walkthrough-runs", status_code=201, tags=["walkthrough"])
def generate_walkthrough_run(
    project_id: str,
    request: GenerateWalkthroughRequest,
) -> dict[str, object]:
    run = stage4_service.generate_walkthrough(
        project_id=project_id,
        audience=request.audience,
        requested_language=request.requested_language,
        depth=request.depth,
        style=request.style,
        prompt=request.prompt,
    )
    return walkthrough_to_api(run)


def reset_app_state_for_tests() -> None:
    stage4_service.reset()


app.include_router(api_v1)
