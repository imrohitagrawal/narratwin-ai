from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests


def test_create_upload_ingest_generate_grounded_script_with_citations() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    fixture = Path("tests/fixtures/stage4_project.md")

    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "NarraTwin AI",
            "description": "Grounded walkthrough generator",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers={"Idempotency-Key": "test-project-create"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["projectId"]

    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", fixture.read_bytes(), "text/markdown")},
        headers={"Idempotency-Key": "test-doc-upload"},
    )
    assert upload_response.status_code == 201
    document = upload_response.json()
    assert document["approvalStatus"] == "PENDING"
    assert document["ingestionStatus"] == "NOT_STARTED"

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document['documentId']}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved fixture."},
        headers={"Idempotency-Key": "test-doc-approval"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["approvalStatus"] == "APPROVED"

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document["documentId"]]},
        headers={"Idempotency-Key": "test-ingest"},
    )
    assert ingestion_response.status_code == 201
    ingestion = ingestion_response.json()
    assert ingestion["status"] == "COMPLETED"
    assert ingestion["chunkCount"] > 0

    generation_response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "RECRUITER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Create a concise grounded walkthrough for a recruiter.",
        },
        headers={"Idempotency-Key": "test-generate"},
    )
    assert generation_response.status_code == 201
    run = generation_response.json()
    assert run["status"] == "COMPLETED"
    assert run["evaluationStatus"] == "PASSED"
    assert run["acceptedScriptText"]
    assert run["evaluation"]["unsupportedClaimCount"] == 0
    assert run["contextRefs"]
    assert "[1]" in run["acceptedScriptText"]
    assert all(ref["chunkId"].startswith("chunk_") for ref in run["contextRefs"])


def test_upload_rejects_non_markdown_files_without_echoing_content() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_response = client.post(
        "/api/v1/projects",
        json={"name": "NarraTwin AI"},
        headers={"Idempotency-Key": "test-project-create"},
    )
    project_id = project_response.json()["projectId"]
    rejected_text = "rejected-upload-content-should-not-echo"

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("bad.html", rejected_text.encode(), "text/html")},
        headers={"Idempotency-Key": "test-bad-upload"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert rejected_text not in response.text
