from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests


ISSUE280_PATH = "/api/v1/checkpoint3/issue280/input-contract"


@pytest.fixture(autouse=True)
def issue280_api_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ELEVENLABS_API_KEY",
        "HEYGEN_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    reset_app_state_for_tests()
    yield
    reset_app_state_for_tests()


def issue280_payload() -> dict[str, Any]:
    return {
        "documents": [
            {
                "filename": "beacon-scheduler.md",
                "contentType": "text/markdown",
                "markdown": "# Beacon Scheduler\n\nBeacon Scheduler is synthetic public-safe project knowledge.",
            }
        ],
        "audience": "PRODUCT_LEADER",
        "depth": "DEEP",
        "targetLanguage": "es",
        "glossaryTerms": ["Beacon Scheduler"],
    }


def test_issue280_api_response_shape_and_local_provider_posture_are_contractual() -> None:
    client = TestClient(app)

    response = client.post(
        ISSUE280_PATH,
        json=issue280_payload(),
        headers={"Idempotency-Key": "issue280-api-positive", "X-Request-Id": "req-issue280-api-positive"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req-issue280-api-positive"
    body = cast(dict[str, Any], response.json())
    assert set(body) == {
        "schema",
        "status",
        "accepted",
        "contractVersion",
        "limits",
        "request",
        "documents",
        "providerPosture",
        "trace",
    }
    assert body["providerPosture"] == {
        "llm": "mock",
        "translation": "mock",
        "voice": "mock",
        "avatar": "mock",
        "videoRenderer": "local-html",
        "networkEgress": False,
        "paidProvidersEnabled": False,
        "realProviderCalls": False,
        "clonedIdentity": False,
        "realMedia": False,
    }
    assert body["trace"] == {
        "requestId": "req-issue280-api-positive",
        "evidenceLevel": "input-api-error-contract",
        "runtimeProviderMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
    }


@pytest.mark.parametrize(
    ("payload_patch", "status_code", "error_code", "raw_values"),
    [
        (
            {
                "documents": [
                    {
                        "filename": "too-large.md",
                        "contentType": "text/markdown",
                        "markdown": "A" * 20001,
                    }
                ]
            },
            413,
            "ISSUE280_INPUT_TOO_LARGE",
            ("A" * 20001,),
        ),
        (
            {
                "documents": [
                    {
                        "filename": "wrong.txt",
                        "contentType": "text/plain",
                        "markdown": "# Wrong type",
                    }
                ]
            },
            415,
            "ISSUE280_UNSUPPORTED_FILE_TYPE",
            ("# Wrong type",),
        ),
        (
            {
                "documents": [
                    {"filename": f"doc-{index}.md", "contentType": "text/markdown", "markdown": f"# Doc {index}"}
                    for index in range(4)
                ]
            },
            422,
            "ISSUE280_TOO_MANY_DOCUMENTS",
            ("# Doc 0", "# Doc 3"),
        ),
        (
            {"glossaryTerms": ["Translate everything casually for recruiters."]},
            422,
            "ISSUE280_GLOSSARY_INVALID",
            ("Translate everything casually for recruiters.",),
        ),
    ],
)
def test_issue280_api_maps_request_contract_failures_to_safe_error_codes(
    payload_patch: dict[str, Any],
    status_code: int,
    error_code: str,
    raw_values: tuple[str, ...],
) -> None:
    client = TestClient(app)
    payload = issue280_payload()
    payload.update(payload_patch)

    response = client.post(
        ISSUE280_PATH,
        json=payload,
        headers={"Idempotency-Key": f"issue280-api-{error_code}", "X-Request-Id": f"req-{error_code}"},
    )

    assert response.status_code == status_code
    body = cast(dict[str, Any], response.json())
    assert body["error"]["code"] == error_code
    assert body["error"]["requestId"] == f"req-{error_code}"
    for raw_value in raw_values:
        assert raw_value not in str(body)
    assert "Traceback" not in str(body)


def test_issue280_api_request_validation_uses_issue280_safe_error_shape() -> None:
    client = TestClient(app)

    response = client.post(
        ISSUE280_PATH,
        json={"documents": "not-a-list"},
        headers={"Idempotency-Key": "issue280-api-wrong-shape", "X-Request-Id": "req-issue280-api-wrong-shape"},
    )

    assert response.status_code == 422
    body = cast(dict[str, Any], response.json())
    assert body["error"]["code"] == "ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED"
    assert body["error"]["details"] == {"field": "request"}
    assert "not-a-list" not in str(body)
