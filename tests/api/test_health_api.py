from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import BaseModel

from backend.app.main import app


class _ValidationProbe(BaseModel):
    name: int


@app.get("/_test/runtime-error", include_in_schema=False)
def _runtime_error() -> None:
    raise RuntimeError("raw internal detail")


@app.get("/_test/http-500", include_in_schema=False)
def _http_500() -> None:
    raise HTTPException(status_code=500, detail="raw http exception detail")


@app.post("/_test/validation-error", include_in_schema=False)
def _validation_error(_payload: _ValidationProbe) -> None:
    return None


FOUNDATION_SECURITY_HEADERS = {
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


def assert_foundation_headers(response: Response) -> None:
    for header, expected in FOUNDATION_SECURITY_HEADERS.items():
        assert response.headers[header] == expected
    assert response.headers["x-request-id"]


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
            "status": "ok",
            "service": "narratwin-ai-backend",
            "stage": "8",
    }
    assert_foundation_headers(response)


def test_ready_endpoint_returns_timestamped_ok() -> None:
    client = TestClient(app)

    before_request = datetime.now(UTC)
    response = client.get("/readyz")
    after_request = datetime.now(UTC)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "narratwin-ai-backend"
    assert body["stage"] == "8"
    checked_at = datetime.fromisoformat(body["checkedAt"])
    assert checked_at.tzinfo == UTC
    assert before_request <= checked_at <= after_request
    assert_foundation_headers(response)


def test_api_v1_health_endpoint_matches_root_health_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {
            "status": "ok",
            "service": "narratwin-ai-backend",
            "stage": "8",
    }
    assert_foundation_headers(response)


def test_api_v1_ready_endpoint_returns_timestamped_ok() -> None:
    client = TestClient(app)

    before_request = datetime.now(UTC)
    response = client.get("/api/v1/readyz")
    after_request = datetime.now(UTC)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "narratwin-ai-backend"
    assert body["stage"] == "8"
    checked_at = datetime.fromisoformat(body["checkedAt"])
    assert checked_at.tzinfo == UTC
    assert before_request <= checked_at <= after_request
    assert_foundation_headers(response)


def test_api_v1_ops_status_reports_durability_and_monitoring_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ops/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "narratwin-ai-backend"
    assert body["stage"] == "8"
    assert body["operationalPosture"] == "LOCAL_ONLY"
    datetime.fromisoformat(body["checkedAt"])
    assert set(body["durability"]) == {"stage4", "stage6", "stage7"}
    for service_status in body["durability"].values():
        assert "stateFile" not in service_status
        assert service_status["stateBackend"] in {"memory", "json-file"}
        assert service_status["durableStateEnabled"] is (service_status["stateBackend"] == "json-file")
    assert body["durability"]["stage4"]["recordCounts"].keys() >= {
        "projects",
        "documents",
        "ingestionRuns",
        "walkthroughRuns",
        "idempotencyRecords",
    }
    assert body["durability"]["stage6"]["recordCounts"].keys() == {"idempotencyRecords"}
    assert body["durability"]["stage7"]["recordCounts"].keys() >= {
        "avatarRenders",
        "artifactMetadata",
        "idempotencyRecords",
    }
    assert body["monitoring"] == {
        "healthEndpoint": True,
        "readinessEndpoint": True,
        "opsStatusEndpoint": True,
        "structuredLoggingConfigured": True,
        "walkthroughMetricsInstrumented": True,
        "metricsEndpointExposed": False,
        "productionAlertsConfigured": False,
        "langfuseConfigured": body["monitoring"]["langfuseConfigured"],
    }
    assert_foundation_headers(response)


def test_not_found_uses_locked_error_envelope_and_request_id_header() -> None:
    client = TestClient(app)

    response = client.get("/missing")

    assert response.status_code == 404
    body = response.json()
    request_id = response.headers["x-request-id"]
    assert body == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "details": {},
            "requestId": request_id,
        }
    }
    assert_foundation_headers(response)


def test_http_500_errors_use_generic_locked_error_envelope() -> None:
    client = TestClient(app)

    response = client.get("/_test/http-500")

    assert response.status_code == 500
    body = response.json()
    request_id = response.headers["x-request-id"]
    assert body == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error.",
            "details": {},
            "requestId": request_id,
        }
    }
    assert "raw http exception detail" not in response.text
    assert_foundation_headers(response)


def test_unhandled_errors_use_generic_locked_error_envelope() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/_test/runtime-error")

    assert response.status_code == 500
    body = response.json()
    request_id = response.headers["x-request-id"]
    assert body == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error.",
            "details": {},
            "requestId": request_id,
        }
    }
    assert "raw internal detail" not in response.text
    assert_foundation_headers(response)


def test_validation_errors_do_not_echo_rejected_input() -> None:
    client = TestClient(app)
    raw_input = "raw-secret-like-rejected-input"

    response = client.post("/_test/validation-error", json={"name": raw_input})

    assert response.status_code == 422
    body = response.json()
    request_id = response.headers["x-request-id"]
    assert body == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": {"errorCount": 1},
            "requestId": request_id,
        }
    }
    assert raw_input not in response.text
    assert_foundation_headers(response)
