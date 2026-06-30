"""Health-only FastAPI skeleton for Stage 3 repo foundation."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

ErrorDetailValue = str | int | float | bool


class HealthResponse(BaseModel):
    """Stable health response shape used by CI smoke checks."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    service: Literal["narratwin-ai-backend"]
    stage: Literal["3"]


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


app = FastAPI(
    title="NarraTwin AI API",
    version="0.1.0",
    docs_url=None,
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)
API_V1_HEALTH_PATH = "/api/v1/healthz"
API_V1_READY_PATH = "/api/v1/readyz"
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


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error.",
    )


def health_payload() -> HealthResponse:
    return HealthResponse(status="ok", service="narratwin-ai-backend", stage="3")


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


app.include_router(api_v1)
