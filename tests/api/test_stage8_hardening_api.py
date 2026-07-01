import asyncio
import json
import time
from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from backend.app.main import (
    MAX_STAGE8_RATE_LIMIT_KEYS,
    MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE,
    app,
    rate_limit_key_from_scope,
    reset_app_state_for_tests,
    stage8_write_rate_limiter,
)
from backend.app.stage4 import MAX_API_REQUEST_BYTES


IDEMPOTENCY_HEADER = "Idempotency-" + "Key"


def idempotency_headers(value: str) -> dict[str, str]:
    return {IDEMPOTENCY_HEADER: value}


def _create_project(client: TestClient, *, key: str = "stage8-project") -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": "NarraTwin AI", "description": "Stage 8 hardening fixture"},
        headers=idempotency_headers(key),
    )
    assert response.status_code == 201
    return str(response.json()["projectId"])


def _upload_approve_ingest_fixture(client: TestClient, project_id: str) -> None:
    fixture = Path("tests/fixtures/stage4_project.md")
    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", fixture.read_bytes(), "text/markdown")},
        headers=idempotency_headers("stage8-upload"),
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["documentId"]

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED"},
        headers=idempotency_headers("stage8-approval"),
    )
    assert approve_response.status_code == 200

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=idempotency_headers("stage8-ingest"),
    )
    assert ingestion_response.status_code == 201


async def _call_app_with_raw_body(
    path: str,
    body: bytes,
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> tuple[int, dict[str, object]]:
    messages: list[Message] = []
    body_sent = False

    async def receive() -> Message:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.disconnect"}
        body_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: Message) -> None:
        messages.append(message)

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers
        or [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"idempotency-key", b"stage8-missing-length"),
        ],
        "client": ("127.0.0.1", 43210),
        "server": ("testserver", 80),
    }
    await app(scope, cast(Receive, receive), cast(Send, send))

    status = next(
        cast(int, message["status"])
        for message in messages
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, cast(dict[str, object], json.loads(response_body.decode("utf-8")))


def test_health_reports_stage8_with_local_latency_budget() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    started = time.perf_counter()
    response = client.get("/api/v1/healthz")
    latency_ms = (time.perf_counter() - started) * 1000

    assert response.status_code == 200
    assert response.json()["stage"] == "8"
    assert latency_ms < 200


def test_write_rate_limit_rejects_excess_requests_without_provider_calls() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    last_response = None
    for index in range(MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE + 1):
        last_response = client.post(
            "/api/v1/projects",
            json={"name": f"Rate limited project {index}"},
        )

    assert last_response is not None
    assert last_response.status_code == 429
    assert last_response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_write_rate_limit_uses_client_ip_and_bounds_retained_keys() -> None:
    reset_app_state_for_tests()

    first_scope: Scope = {"type": "http", "client": ("203.0.113.10", 40000)}
    second_scope: Scope = {
        "type": "http",
        "client": ("203.0.113.10", 40000),
        "headers": [(b"x-local-user-id", b"rotated-user")],
    }

    assert rate_limit_key_from_scope(first_scope) == "ip:203.0.113.10"
    assert rate_limit_key_from_scope(second_scope) == "ip:203.0.113.10"

    for index in range(MAX_STAGE8_RATE_LIMIT_KEYS):
        assert stage8_write_rate_limiter.allow(key=f"ip:198.51.100.{index}", now=1.0)
    assert not stage8_write_rate_limiter.allow(key="ip:203.0.113.200", now=1.0)
    assert stage8_write_rate_limiter.allow(key="ip:203.0.113.200", now=62.0)


def test_json_request_size_limit_is_enforced_before_validation() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    oversized_name = "x" * (MAX_API_REQUEST_BYTES + 1)

    response = client.post(
        "/api/v1/projects",
        json={"name": oversized_name},
        headers=idempotency_headers("stage8-oversized-json"),
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_json_request_size_limit_rejects_missing_content_length_before_body_parsing() -> None:
    reset_app_state_for_tests()
    body = json.dumps({"name": "x" * (MAX_API_REQUEST_BYTES + 1)}).encode("utf-8")

    status, payload = asyncio.run(_call_app_with_raw_body("/api/v1/projects", body))

    assert status == 411
    error = cast(dict[str, object], payload["error"])
    assert error["code"] == "CONTENT_LENGTH_REQUIRED"


def test_json_request_size_limit_rejects_underreported_content_length() -> None:
    reset_app_state_for_tests()
    body = json.dumps({"name": "x" * (MAX_API_REQUEST_BYTES + 1)}).encode("utf-8")

    status, payload = asyncio.run(
        _call_app_with_raw_body(
            "/api/v1/projects",
            body,
            headers=[
                (b"host", b"testserver"),
                (b"content-type", b"application/json"),
                (b"content-length", b"2"),
                (b"idempotency-key", b"stage8-underreported-length"),
            ],
        )
    )

    assert status == 413
    error = cast(dict[str, object], payload["error"])
    assert error["code"] == "REQUEST_TOO_LARGE"


def test_upload_mime_validation_rejects_octet_stream_markdown_compatibility() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id = _create_project(client, key="stage8-mime-project")

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage8_project.md", b"# NarraTwin\nGrounded content.", "application/octet-stream")},
        headers=idempotency_headers("stage8-octet-upload"),
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_upload_mime_validation_accepts_allowed_media_type_parameters() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id = _create_project(client, key="stage8-mime-parameter-project")

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage8_project.txt", b"NarraTwin grounded content.", "text/plain; charset=utf-8")},
        headers=idempotency_headers("stage8-text-upload-with-charset"),
    )

    assert response.status_code == 201
    assert response.json()["contentType"] == "text/plain"


def test_provider_bound_prompt_rejects_secret_like_content_before_generation() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id = _create_project(client, key="stage8-secret-prompt-project")

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "RECRUITER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Use api" + "_key=visible-secret-token-value in the walkthrough.",
        },
        headers=idempotency_headers("stage8-secret-prompt"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SECRET_LIKE_CONTENT"


def test_mocked_script_generation_path_stays_under_two_seconds() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id = _create_project(client, key="stage8-latency-project")
    _upload_approve_ingest_fixture(client, project_id)

    started = time.perf_counter()
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "RECRUITER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Create a concise grounded walkthrough for a recruiter.",
        },
        headers=idempotency_headers("stage8-generate"),
    )
    latency_ms = (time.perf_counter() - started) * 1000

    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETED"
    assert latency_ms < 2_000
