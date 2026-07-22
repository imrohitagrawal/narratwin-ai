from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage4 import stage4_service

# Generated walkthrough scripts must carry source_chunk citation evidence through contextRefs.

ATLAS_KNOWLEDGE = b"""# Atlas Notes

Atlas Notes ATLAS-SENTINEL-CP1 is a fictional local-first research notebook for field teams.
Atlas Notes imports markdown field notes, tags observations, and exports weekly insight briefs.
Atlas Notes requires every generated brief to cite approved source notes.
Atlas Notes uses the marker ATLAS-SENTINEL-CP1 for acceptance isolation checks.
"""

BEACON_KNOWLEDGE = b"""# Beacon Scheduler

Beacon Scheduler BEACON-SENTINEL-CP1 is a fictional volunteer-shift scheduler for neighborhood events.
Beacon Scheduler sends timezone-aware reminders and flags unfilled shifts.
Beacon Scheduler uses the marker BEACON-SENTINEL-CP1 for acceptance isolation checks.
"""


@pytest.fixture(autouse=True)
def local_only_acceptance_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()
    yield
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()


def create_project(client: TestClient, *, prefix: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Synthetic C3A-CP1 acceptance fixture.",
            "defaultAudience": "PRODUCT_LEADER",
            "defaultLanguage": "en",
        },
        headers={"Idempotency-Key": f"{prefix}-project"},
    )
    assert response.status_code == 201
    project = cast(dict[str, Any], response.json())
    assert project["projectId"].startswith("proj_")
    assert project["ownerId"] == "user_local"
    return project


def upload_document(
    client: TestClient,
    *,
    prefix: str,
    project_id: str,
    filename: str,
    content: bytes,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": (filename, content, "text/markdown")},
        headers={"Idempotency-Key": f"{prefix}-upload"},
    )
    assert response.status_code == 201
    document = cast(dict[str, Any], response.json())
    assert document["approvalStatus"] == "PENDING"
    assert document["ingestionStatus"] == "NOT_STARTED"
    assert document["sourceFilename"] == filename
    return document


def approve_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> dict[str, Any]:
    response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP1 knowledge."},
        headers={"Idempotency-Key": f"{prefix}-approval"},
    )
    assert response.status_code == 200
    document = cast(dict[str, Any], response.json())
    assert document["approvalStatus"] == "APPROVED"
    return document


def ingest_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers={"Idempotency-Key": f"{prefix}-ingest"},
    )
    assert response.status_code == 201
    ingestion = cast(dict[str, Any], response.json())
    assert ingestion["status"] == "COMPLETED"
    assert ingestion["chunkCount"] > 0
    assert ingestion["embeddingCount"] == ingestion["chunkCount"]
    return ingestion


def generate_walkthrough(
    client: TestClient,
    *,
    prefix: str,
    project_id: str,
    prompt: str,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "PRODUCT_LEADER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": prompt,
        },
        headers={"Idempotency-Key": f"{prefix}-generate"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def assert_passed_grounded_run(run: dict[str, Any], *, project_id: str, document: dict[str, Any]) -> None:
    assert run["status"] == "COMPLETED"
    assert run["evaluationStatus"] == "PASSED"
    assert run["acceptedScriptText"]
    assert "[1]" in run["acceptedScriptText"]
    assert "NarraTwin" not in run["acceptedScriptText"]
    assert run["provider"] == {"provider": "mock", "providerMode": "LOCAL"}
    assert run["trace"]["traceId"].startswith("trace_")
    assert run["trace"]["estimatedCost"] == 0
    assert run["trace"]["inputTokens"] > 0
    assert run["trace"]["outputTokens"] > 0
    assert run["evaluation"]["unsupportedClaimCount"] == 0
    assert run["evaluation"]["unsupportedClaims"] == []
    assert run["evaluation"]["contextRefCoverage"] == 1.0
    assert run["contextRefs"]

    context_ref_ids = {ref["contextRefId"] for ref in run["contextRefs"]}
    for ref in run["contextRefs"]:
        assert ref["tenantId"] == "tenant_local"
        assert ref["projectId"] == project_id
        assert ref["documentId"] == document["documentId"]
        assert ref["sourceFilename"] == document["sourceFilename"]
        assert ref["evidenceSnapshot"]["sourceDocumentChecksum"] == document["checksum"]
        assert ref["evidenceSnapshot"]["projectId"] == project_id
        assert ref["evidenceSnapshot"]["documentId"] == document["documentId"]

    assert run["evaluation"]["claimSupports"]
    for support in run["evaluation"]["claimSupports"]:
        assert support["supportStatus"] == "SUPPORTED"
        assert support["contextRefId"] in context_ref_ids
        assert support["projectId"] == project_id
        assert support["documentId"] == document["documentId"]
        assert support["evidenceSnapshot"]["sourceDocumentChecksum"] == document["checksum"]


def prepare_approved_project(
    client: TestClient,
    *,
    prefix: str,
    name: str,
    filename: str,
    content: bytes,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = create_project(client, prefix=prefix, name=name)
    document = upload_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        filename=filename,
        content=content,
    )
    approved_document = approve_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    ingestion = ingest_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    return project, approved_document, ingestion


def test_checkpoint3_api_e2e_executes_local_product_path() -> None:
    client = TestClient(app)
    project, document, ingestion = prepare_approved_project(
        client,
        prefix="atlas",
        name="Atlas Notes",
        filename="atlas_notes.md",
        content=ATLAS_KNOWLEDGE,
    )

    run = generate_walkthrough(
        client,
        prefix="atlas",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Notes using only approved source facts.",
    )

    assert ingestion["projectId"] == project["projectId"]
    assert_passed_grounded_run(run, project_id=project["projectId"], document=document)
    assert "Atlas Notes" in run["acceptedScriptText"]
    assert "ATLAS-SENTINEL-CP1" in run["acceptedScriptText"]

    replay = client.post(
        f"/api/v1/projects/{project['projectId']}/walkthrough-runs",
        json={
            "audience": "PRODUCT_LEADER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Create a grounded walkthrough for Atlas Notes using only approved source facts.",
        },
        headers={"Idempotency-Key": "atlas-generate"},
    )
    assert replay.status_code == 201
    assert replay.json() == run

    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    counts = ops.json()["durability"]["stage4"]["recordCounts"]
    assert counts["projects"] == 1
    assert counts["documents"] == 1
    assert counts["ingestionRuns"] == 1
    assert counts["walkthroughRuns"] == 1


def test_checkpoint3_api_e2e_rejects_unapproved_knowledge_before_ingestion() -> None:
    client = TestClient(app)
    project = create_project(client, prefix="unapproved", name="Atlas Notes")
    document = upload_document(
        client,
        prefix="unapproved",
        project_id=project["projectId"],
        filename="atlas_notes.md",
        content=ATLAS_KNOWLEDGE,
    )

    response = client.post(
        f"/api/v1/projects/{project['projectId']}/ingestion-runs",
        json={"documentIds": [document["documentId"]]},
        headers={"Idempotency-Key": "unapproved-ingest"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_APPROVED"
    assert stage4_service.rag_store.chunk_count_for_project(
        tenant_id="tenant_local",
        project_id=project["projectId"],
    ) == 0
    ops = client.get("/api/v1/ops/status")
    counts = ops.json()["durability"]["stage4"]["recordCounts"]
    assert counts["ingestionRuns"] == 0
    assert counts["walkthroughRuns"] == 0


def test_checkpoint3_api_e2e_rejects_cross_project_replay() -> None:
    client = TestClient(app)
    atlas, atlas_document, _atlas_ingestion = prepare_approved_project(
        client,
        prefix="cross-atlas",
        name="Atlas Notes",
        filename="atlas_notes.md",
        content=ATLAS_KNOWLEDGE,
    )
    beacon, beacon_document, _beacon_ingestion = prepare_approved_project(
        client,
        prefix="cross-beacon",
        name="Beacon Scheduler",
        filename="beacon_scheduler.md",
        content=BEACON_KNOWLEDGE,
    )

    run = generate_walkthrough(
        client,
        prefix="cross-atlas",
        project_id=atlas["projectId"],
        prompt="Create a grounded walkthrough for Atlas Notes without using any other project.",
    )

    assert_passed_grounded_run(run, project_id=atlas["projectId"], document=atlas_document)
    assert "BEACON-SENTINEL-CP1" not in run["acceptedScriptText"]
    assert "Beacon Scheduler" not in run["acceptedScriptText"]
    for ref in run["contextRefs"]:
        assert ref["projectId"] != beacon["projectId"]
        assert ref["documentId"] != beacon_document["documentId"]
        assert ref["evidenceSnapshot"]["sourceDocumentChecksum"] != beacon_document["checksum"]

    replay_attempt = client.post(
        f"/api/v1/projects/{beacon['projectId']}/ingestion-runs",
        json={"documentIds": [atlas_document["documentId"]]},
        headers={"Idempotency-Key": "cross-replay"},
    )
    assert replay_attempt.status_code == 404
    assert replay_attempt.json()["error"]["code"] == "NOT_FOUND"


def test_checkpoint3_api_e2e_rejects_unsupported_claim_acceptance() -> None:
    client = TestClient(app)
    project, document, _ingestion = prepare_approved_project(
        client,
        prefix="unsupported",
        name="Atlas Notes",
        filename="atlas_notes.md",
        content=ATLAS_KNOWLEDGE,
    )
    stage4_service.llm = MockLLMProvider(
        extra_unsupported_claim="Atlas Notes guarantees fictional grant funding."
    )

    run = generate_walkthrough(
        client,
        prefix="unsupported",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Notes using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert run["redactedUnsupportedExcerpts"]
    assert "fictional grant funding" in run["redactedUnsupportedExcerpts"][0]
    assert run["provider"] == {"provider": "mock", "providerMode": "LOCAL"}
    assert run["trace"]["estimatedCost"] == 0
    assert run["contextRefs"]
    for ref in run["contextRefs"]:
        assert ref["projectId"] == project["projectId"]
        assert ref["documentId"] == document["documentId"]
