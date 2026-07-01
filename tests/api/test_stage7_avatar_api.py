import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.stage4 import stage4_service

IDEMPOTENCY_HEADER = "Idempotency-" + "Key"


def idempotency_headers(value: str) -> dict[str, str]:
    return {IDEMPOTENCY_HEADER: value}


def _create_completed_walkthrough(client: TestClient) -> tuple[str, str]:
    fixture = Path("tests/fixtures/stage4_project.md")
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "NarraTwin AI",
            "description": "Grounded walkthrough generator",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers=idempotency_headers("stage7-project"),
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["projectId"]

    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", fixture.read_bytes(), "text/markdown")},
        headers=idempotency_headers("stage7-upload"),
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["documentId"]

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED"},
        headers=idempotency_headers("stage7-approval"),
    )
    assert approve_response.status_code == 200

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=idempotency_headers("stage7-ingest"),
    )
    assert ingestion_response.status_code == 201

    generation_response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "RECRUITER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Create a concise grounded walkthrough for a recruiter.",
        },
        headers=idempotency_headers("stage7-generate"),
    )
    assert generation_response.status_code == 201
    assert generation_response.json()["status"] == "COMPLETED"
    return project_id, generation_response.json()["runId"]


def test_avatar_render_api_returns_validated_demo_export_artifacts() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "clonedIdentityRequested": False,
        },
        headers=idempotency_headers("stage7-avatar"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["renderJobStatus"] == "COMPLETED"
    assert [event["status"] for event in body["renderJobStatusHistory"]] == ["QUEUED", "RUNNING", "COMPLETED"]
    assert body["sourceRunId"] == run_id
    assert body["avatarProvider"]["provider"] == "mock"
    assert body["avatarProvider"]["providerMode"] == "LOCAL"
    assert "fallbackReason" in body["avatarProvider"]
    assert body["avatarProvider"]["fallbackReason"] is None
    assert body["providerConfig"]["provider"] == "mock"
    assert body["providerConfig"]["adapterKind"] == "MOCK_LOCAL"
    assert body["providerConfig"]["allowNetworkEgress"] is False
    assert body["providerConfig"]["requiresApiKey"] is False
    assert body["providerConfig"]["supportsRealVideo"] is False
    assert body["videoRenderer"]["renderer"] == "local-html"
    assert body["disclosure"]["aiGenerated"] is True
    assert body["disclosure"]["clonedIdentity"] is False
    assert body["artifacts"]["demoExport"]["mimeType"] == "text/html"
    assert body["artifacts"]["demoExport"]["fileName"].endswith(".html")
    assert body["artifacts"]["renderManifest"]["mimeType"] == "application/json"
    assert body["artifacts"]["videoExportPlaceholder"]["mimeType"] == "application/json"
    assert body["artifacts"]["videoExportPlaceholder"]["fileName"].endswith("-video-export-placeholder.json")
    assert body["trace"]["sourceCitationCount"] >= 1
    assert body["trace"]["sourceContextRefIds"]
    assert body["trace"]["sourceCitationIndexes"]
    assert body["trace"]["sourceEvaluationId"].startswith("eval_")
    assert body["trace"]["sourceEvaluationChecksum"].startswith("sha256:")
    assert body["trace"]["evaluationStatus"] == "PASSED"
    manifest = json.loads(base64.b64decode(body["artifacts"]["renderManifest"]["contentBase64"]).decode("utf-8"))
    assert manifest["source"]["contextRefIds"] == body["trace"]["sourceContextRefIds"]
    assert manifest["source"]["citationIndexes"] == body["trace"]["sourceCitationIndexes"]
    assert manifest["source"]["evaluationId"] == body["trace"]["sourceEvaluationId"]
    assert manifest["source"]["evaluationChecksum"] == body["trace"]["sourceEvaluationChecksum"]
    assert manifest["publicUseLicenseCheck"] == "mock-local-provider-only-no-third-party-media"
    placeholder = json.loads(
        base64.b64decode(body["artifacts"]["videoExportPlaceholder"]["contentBase64"]).decode("utf-8")
    )
    assert placeholder["providerConfig"] == manifest["providerConfig"]
    assert placeholder["source"] == manifest["source"]
    assert placeholder["disclosure"] == manifest["disclosure"]


def test_avatar_render_api_falls_back_to_mock_provider() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "external-avatar",
            "consentToUseSyntheticAvatar": True,
        },
        headers=idempotency_headers("stage7-avatar-fallback"),
    )

    assert response.status_code == 201
    avatar_provider = response.json()["avatarProvider"]
    assert avatar_provider["provider"] == "mock"
    assert avatar_provider["requestedProvider"] == "external-avatar"
    assert avatar_provider["fallbackReason"] == "REQUESTED_PROVIDER_UNAVAILABLE"
    assert response.json()["providerConfig"]["allowNetworkEgress"] is False


def test_avatar_render_api_requires_synthetic_avatar_consent() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": False,
        },
        headers=idempotency_headers("stage7-avatar-no-consent"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AVATAR_CONSENT_REQUIRED"


def test_avatar_render_api_rejects_cloned_identity_request() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "clonedIdentityRequested": True,
        },
        headers=idempotency_headers("stage7-avatar-clone"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CLONED_IDENTITY_DISABLED"


def test_avatar_render_api_replays_matching_idempotency_key() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
    request = {"requestedAvatarProvider": "mock", "consentToUseSyntheticAvatar": True}

    first = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-replay"))
    second = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-replay"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["avatarRenderId"] == first.json()["avatarRenderId"]


def test_avatar_render_api_requires_evaluation_evidence() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    stage4_service.walkthrough_runs[run_id].evaluation = None

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
        },
        headers=idempotency_headers("stage7-avatar-missing-eval"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SOURCE_RUN_NOT_RENDERABLE"
