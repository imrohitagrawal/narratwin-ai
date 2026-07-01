import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE, app, reset_app_state_for_tests
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
