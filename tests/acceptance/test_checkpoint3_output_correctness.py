from __future__ import annotations

# ruff: noqa: E402

import os
from collections.abc import Iterator
from copy import deepcopy
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

for _state_env_name in (
    "NARRATWIN_STATE_DIR",
    "NARRATWIN_STAGE4_STATE_FILE",
    "NARRATWIN_STAGE6_STATE_FILE",
    "NARRATWIN_STAGE7_STATE_FILE",
):
    os.environ.pop(_state_env_name, None)

from backend.app.main import app, reset_app_state_for_tests
from backend.app.rag.models import GeneratedScript, RetrievedContext, ScriptClaim
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage4 import stage4_service


ATLAS_OUTPUT_KNOWLEDGE = b"""# Atlas Output

Atlas Output OUTPUT-SENTINEL-CP2 is a fictional local checklist builder for launch rehearsals.
Atlas Output requires each generated checklist item to cite approved launch-note evidence.
Atlas Output uses the marker OUTPUT-SENTINEL-CP2 for output-correctness isolation checks.
"""

BEACON_OUTPUT_KNOWLEDGE = b"""# Beacon Output

Beacon Output BEACON-OUTPUT-CP2 is a fictional community alert console.
Beacon Output sends timezone-aware reminder packets for neighborhood coordinators.
Beacon Output uses the marker BEACON-OUTPUT-CP2 for cross-project replay checks.
"""

REQUIRED_ATLAS_FACT = (
    "Atlas Output OUTPUT-SENTINEL-CP2 is a fictional local checklist builder for launch rehearsals."
)
BEACON_CROSS_PROJECT_FACT = (
    "Beacon Output sends timezone-aware reminder packets for neighborhood coordinators."
)


@pytest.fixture(autouse=True)
def local_only_output_correctness_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()
    yield
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()


class CrossProjectFactProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[RetrievedContext],
    ) -> GeneratedScript:
        del audience, prompt
        context = retrieved_context[0]
        sentence = f"{BEACON_CROSS_PROJECT_FACT} [1]"
        return GeneratedScript(
            text=sentence,
            claims=[
                ScriptClaim(
                    claim_id="claim_cross_project_001",
                    text=BEACON_CROSS_PROJECT_FACT,
                    citation_index=1,
                    chunk_id=context.chunk.chunk_id,
                    script_span_start=0,
                    script_span_end=len(sentence),
                )
            ],
        )


def create_project(client: TestClient, *, prefix: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Synthetic C3A-CP2 output-correctness fixture.",
            "defaultAudience": "ENGINEER",
            "defaultLanguage": "en",
        },
        headers={"Idempotency-Key": f"{prefix}-project"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


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
    return cast(dict[str, Any], response.json())


def approve_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> dict[str, Any]:
    response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP2 knowledge."},
        headers={"Idempotency-Key": f"{prefix}-approval"},
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


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


def prepare_approved_project(
    client: TestClient,
    *,
    prefix: str,
    name: str,
    filename: str,
    content: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project = create_project(client, prefix=prefix, name=name)
    document = upload_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        filename=filename,
        content=content,
    )
    approved = approve_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    ingest_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    return project, approved


def generate_walkthrough(client: TestClient, *, prefix: str, project_id: str, prompt: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "ENGINEER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "TECHNICAL",
            "prompt": prompt,
        },
        headers={"Idempotency-Key": f"{prefix}-generate"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def replay_walkthrough(client: TestClient, *, prefix: str, project_id: str, prompt: str) -> dict[str, Any]:
    return generate_walkthrough(client, prefix=prefix, project_id=project_id, prompt=prompt)


def assert_runtime_output_fact_is_grounded(
    run: dict[str, Any],
    *,
    project_id: str,
    document: dict[str, Any],
    required_fact: str,
) -> None:
    script = run.get("acceptedScriptText")
    assert isinstance(script, str)
    assert required_fact in script
    assert "[1]" in script
    assert run["status"] == "COMPLETED"
    assert run["evaluationStatus"] == "PASSED"
    assert run["provider"] == {"provider": "mock", "providerMode": "LOCAL"}
    assert run["trace"]["estimatedCost"] == 0

    context_refs = run["contextRefs"]
    claim_supports = run["evaluation"]["claimSupports"]
    assert context_refs
    assert claim_supports
    assert run["evaluation"]["unsupportedClaimCount"] == 0
    assert run["evaluation"]["contextRefCoverage"] == 1.0

    context_by_id = {context["contextRefId"]: context for context in context_refs}
    supporting_rows = [
        support
        for support in claim_supports
        if required_fact in support["evidenceSnapshot"]["redactedExcerpt"]
    ]
    assert supporting_rows

    for support in supporting_rows:
        context = context_by_id[support["contextRefId"]]
        assert support["projectId"] == project_id
        assert support["documentId"] == document["documentId"]
        assert support["chunkId"] == context["chunkId"]
        assert support["citationIndex"] == 1
        assert support["supportStatus"] == "SUPPORTED"
        assert context["projectId"] == project_id
        assert context["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["projectId"] == project_id
        assert context["evidenceSnapshot"]["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["sourceDocumentChecksum"] == document["checksum"]
        assert context["evidenceSnapshot"]["chunkChecksum"] == context["checksum"]
        assert support["evidenceSnapshot"]["snapshotChecksum"] == context["evidenceSnapshot"]["snapshotChecksum"]


def test_checkpoint3_output_correctness_executes_runtime_api_evidence_path() -> None:
    client = TestClient(app)
    project, document = prepare_approved_project(
        client,
        prefix="output-atlas",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    prompt = "Create a grounded walkthrough for Atlas Output using only approved source facts."

    run = generate_walkthrough(
        client,
        prefix="output-atlas",
        project_id=project["projectId"],
        prompt=prompt,
    )
    replay = replay_walkthrough(
        client,
        prefix="output-atlas",
        project_id=project["projectId"],
        prompt=prompt,
    )

    assert replay == run
    assert_runtime_output_fact_is_grounded(
        replay,
        project_id=project["projectId"],
        document=document,
        required_fact=REQUIRED_ATLAS_FACT,
    )
    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    assert ops.json()["durability"]["stage4"]["recordCounts"]["walkthroughRuns"] == 1


def test_checkpoint3_output_correctness_rejects_correct_text_without_evidence_binding() -> None:
    client = TestClient(app)
    project, document = prepare_approved_project(
        client,
        prefix="output-binding",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    run = generate_walkthrough(
        client,
        prefix="output-binding",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    missing_support = deepcopy(run)
    missing_support["evaluation"]["claimSupports"] = []
    with pytest.raises(AssertionError):
        assert_runtime_output_fact_is_grounded(
            missing_support,
            project_id=project["projectId"],
            document=document,
            required_fact=REQUIRED_ATLAS_FACT,
        )

    mismatched_evidence = deepcopy(run)
    mismatched_evidence["evaluation"]["claimSupports"][0]["evidenceSnapshot"]["redactedExcerpt"] = (
        "Correct-looking script text without bound runtime evidence."
    )
    with pytest.raises(AssertionError):
        assert_runtime_output_fact_is_grounded(
            mismatched_evidence,
            project_id=project["projectId"],
            document=document,
            required_fact=REQUIRED_ATLAS_FACT,
        )


def test_checkpoint3_output_correctness_rejects_unsupported_claim_acceptance() -> None:
    client = TestClient(app)
    project, _document = prepare_approved_project(
        client,
        prefix="output-unsupported",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    stage4_service.llm = MockLLMProvider(
        extra_unsupported_claim="Atlas Output guarantees external revenue growth."
    )

    run = generate_walkthrough(
        client,
        prefix="output-unsupported",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert "external revenue growth" in run["redactedUnsupportedExcerpts"][0]


def test_checkpoint3_output_correctness_rejects_cross_project_fact_replay() -> None:
    client = TestClient(app)
    atlas, _atlas_document = prepare_approved_project(
        client,
        prefix="output-cross-atlas",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    prepare_approved_project(
        client,
        prefix="output-cross-beacon",
        name="Beacon Output",
        filename="beacon_output.md",
        content=BEACON_OUTPUT_KNOWLEDGE,
    )
    stage4_service.llm = cast(Any, CrossProjectFactProvider())

    run = generate_walkthrough(
        client,
        prefix="output-cross-atlas",
        project_id=atlas["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert BEACON_CROSS_PROJECT_FACT in run["redactedUnsupportedExcerpts"][0]
    for context in run["contextRefs"]:
        assert context["projectId"] == atlas["projectId"]
        assert "BEACON-OUTPUT-CP2" not in context["evidenceSnapshot"]["redactedExcerpt"]
