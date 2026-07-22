from __future__ import annotations

# ruff: noqa: E402

import copy
import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

for _state_env_name in (
    "NARRATWIN_STATE_DIR",
    "NARRATWIN_STAGE4_STATE_FILE",
    "NARRATWIN_STAGE6_STATE_FILE",
    "NARRATWIN_STAGE7_STATE_FILE",
):
    os.environ.pop(_state_env_name, None)

from backend.app.hosted_demo import (
    HOSTED_DEMO_DISCLOSURE_VERSION,
    HostedDemoAccessConfig,
    HostedDemoAccessRequest,
    build_hosted_demo_artifact_checksum,
    build_hosted_demo_deletion_evidence_id,
    build_hosted_demo_evaluation_checksum,
    build_hosted_demo_session_binding_hash,
    build_hosted_demo_tombstone_checksum,
    build_hosted_demo_tombstone_id,
    hash_hosted_demo_secret,
    hosted_demo_service,
)
from backend.app.main import app, reset_app_state_for_tests
from backend.app.rag.chunking import checksum_text
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage4 import MAX_PROMPT_CHARS, MAX_UPLOAD_REQUEST_BYTES, stage4_service


ALPHA_KNOWLEDGE = b"""# Alpha Runtime Lab

Alpha Runtime Lab CP5-ALPHA-SENTINEL is a fictional local-only product evidence workspace.
Alpha Runtime Lab uploads approved markdown knowledge and generates grounded walkthroughs for product reviewers.
Alpha Runtime Lab requires every runtime script to cite approved source chunks before it can be shared.
"""

BETA_KNOWLEDGE = b"""# Alpha Boundary Lab

Alpha Boundary Lab CP5-BETA-SENTINEL is a fictional local-only product evidence workspace.
Alpha Boundary Lab uploads approved markdown knowledge and generates grounded walkthroughs for product reviewers.
Alpha Boundary Lab stores separate approved knowledge so access tests can prove project isolation.
"""

RAW_UPLOAD_CANARY = "CP5-RAW-UPLOAD-CANARY"
RAW_PROMPT_CANARY = "CP5-RAW-PROMPT-CANARY"


@pytest.fixture(autouse=True)
def local_only_access_quota_retention_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()
    hosted_demo_service.configure(HostedDemoAccessConfig(enabled=False))
    yield
    stage4_service.llm = MockLLMProvider()
    hosted_demo_service.configure(HostedDemoAccessConfig(enabled=False))
    reset_app_state_for_tests()


def headers(prefix: str, *, actor: str = "alice") -> dict[str, str]:
    return {"X-Local-User-Id": actor, "Idempotency-Key": prefix}


def create_project(client: TestClient, *, prefix: str, actor: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Synthetic C3A-CP5 acceptance fixture.",
            "defaultAudience": "PRODUCT_LEADER",
            "defaultLanguage": "en",
        },
        headers=headers(f"{prefix}-project", actor=actor),
    )
    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    assert body["ownerId"] == actor
    return body


def upload_document(
    client: TestClient,
    *,
    prefix: str,
    actor: str,
    project_id: str,
    filename: str,
    content: bytes,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": (filename, content, "text/markdown")},
        headers=headers(f"{prefix}-upload", actor=actor),
    )
    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    assert body["projectId"] == project_id
    assert body["approvalStatus"] == "PENDING"
    return body


def approve_document(
    client: TestClient,
    *,
    prefix: str,
    actor: str,
    project_id: str,
    document_id: str,
) -> dict[str, Any]:
    response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP5 knowledge."},
        headers=headers(f"{prefix}-approval", actor=actor),
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


def ingest_document(
    client: TestClient,
    *,
    prefix: str,
    actor: str,
    project_id: str,
    document_id: str,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=headers(f"{prefix}-ingest", actor=actor),
    )
    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    assert body["status"] == "COMPLETED", body.get("failure")
    assert body["chunkCount"] > 0
    return body


def generate_walkthrough(
    client: TestClient,
    *,
    prefix: str,
    actor: str,
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
        headers=headers(f"{prefix}-generate", actor=actor),
    )
    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    assert body["status"] == "COMPLETED", body.get("failure")
    assert body["evaluationStatus"] == "PASSED"
    assert body["trace"]["estimatedCost"] == 0
    return body


def prepare_runtime_project(
    client: TestClient,
    *,
    prefix: str,
    actor: str,
    name: str,
    filename: str,
    content: bytes,
    prompt: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = create_project(client, prefix=prefix, actor=actor, name=name)
    pending_document = upload_document(
        client,
        prefix=prefix,
        actor=actor,
        project_id=project["projectId"],
        filename=filename,
        content=content,
    )
    document = approve_document(
        client,
        prefix=prefix,
        actor=actor,
        project_id=project["projectId"],
        document_id=pending_document["documentId"],
    )
    ingestion = ingest_document(
        client,
        prefix=prefix,
        actor=actor,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    run = generate_walkthrough(client, prefix=prefix, actor=actor, project_id=project["projectId"], prompt=prompt)
    return project, document, ingestion, run


def patch_section(payload: dict[str, Any], section: str, patch: dict[str, Any]) -> None:
    current = cast(dict[str, Any], payload[section])
    payload[section] = {**current, **patch}


def hosted_demo_payload_from_run(
    *,
    project: dict[str, Any],
    run: dict[str, Any],
    idempotency_key: str,
    retention_record_id: str = "retention_cp5_active",
) -> dict[str, Any]:
    claim_supports = cast(list[dict[str, Any]], run["evaluation"]["claimSupports"])
    citation_refs = [cast(str, support["contextRefId"]) for support in claim_supports]
    citation_indexes = [cast(int, support["citationIndex"]) for support in claim_supports]
    script_checksum = checksum_text(cast(str, run["acceptedScriptText"]))
    evaluation_checksum = build_hosted_demo_evaluation_checksum(
        tenant_id=cast(str, run["tenantId"]),
        project_id=cast(str, project["projectId"]),
        actor_id=cast(str, run["actorId"]),
        source_run_id=cast(str, run["runId"]),
        trace_id=cast(str, run["trace"]["traceId"]),
        language=cast(str, run["requestedLanguage"]),
        audience=cast(str, run["audience"]),
        script_checksum=script_checksum,
        evaluation_id=cast(str, run["evaluation"]["evaluationId"]),
        evaluation_status=cast(str, run["evaluationStatus"]),
        citation_refs=tuple(citation_refs),
        citation_indexes=tuple(citation_indexes),
    )
    artifact_checksum = build_hosted_demo_artifact_checksum(
        artifact_id="artifact_cp5_runtime_script",
        artifact_kind="SCRIPT",
        artifact_file_name="cp5-runtime-script.md",
        source_run_id=cast(str, run["runId"]),
        script_checksum=script_checksum,
        evaluation_checksum=evaluation_checksum,
        disclosure_version=HOSTED_DEMO_DISCLOSURE_VERSION,
    )
    return {
        "artifact": {
            "artifactId": "artifact_cp5_runtime_script",
            "artifactKind": "SCRIPT",
            "artifactChecksum": artifact_checksum,
            "artifactMimeType": "text/markdown",
            "artifactFileName": "cp5-runtime-script.md",
            "artifactSizeBytes": len(cast(str, run["acceptedScriptText"]).encode("utf-8")),
            "artifactVisibility": "HOSTED_DEMO_REVIEWER",
        },
        "source": {
            "tenantId": cast(str, run["tenantId"]),
            "projectId": cast(str, project["projectId"]),
            "actorId": cast(str, run["actorId"]),
            "sourceRunId": cast(str, run["runId"]),
            "traceId": cast(str, run["trace"]["traceId"]),
            "language": cast(str, run["requestedLanguage"]),
            "audience": cast(str, run["audience"]),
            "scriptChecksum": script_checksum,
            "citationRefs": citation_refs,
            "citationIndexes": citation_indexes,
            "evaluationId": cast(str, run["evaluation"]["evaluationId"]),
            "evaluationStatus": cast(str, run["evaluationStatus"]),
            "evaluationChecksum": evaluation_checksum,
            "multilingualRunId": None,
            "translatedScriptChecksum": None,
            "subtitlesChecksum": None,
            "voiceManifestChecksum": None,
            "ttsAudioChecksum": None,
            "avatarRenderId": None,
            "avatarVideoProviderMetadataChecksum": None,
        },
        "disclosure": {
            "disclosureText": "AI-generated demo using local mock providers; no cloned identity or real provider call.",
            "disclosureVersion": HOSTED_DEMO_DISCLOSURE_VERSION,
        },
        "access": {
            "inviteId": "invite_cp5",
            "inviteSecret": "fake-invite-input",
            "sessionId": "session_cp5",
            "sessionSecret": "fake-session-input",
            "sessionState": "ACTIVE",
            "sessionExpiresAt": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
            "requestedOperation": "VIEW",
        },
        "retention": {
            "retentionRecordId": retention_record_id,
            "retentionState": "ACTIVE",
            "retentionExpiresAt": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "deletionState": "NOT_REQUESTED",
            "deletionRequestedAt": None,
            "deletedAt": None,
            "tombstoneId": None,
            "tombstoneChecksum": None,
            "deletionEvidenceId": None,
            "providerDeletionStatus": "NOT_REQUESTED",
            "localOnlyProviderEvidence": True,
        },
        "idempotencyKey": idempotency_key,
        "quotaUnits": 1,
        "localOutcome": "SUCCESS",
    }


def configure_hosted_demo_access(*, global_quota: int = 3, per_session_quota: int = 3) -> None:
    hosted_demo_service.configure(
        HostedDemoAccessConfig(
            enabled=True,
            allowed_invite_hashes=frozenset({hash_hosted_demo_secret("fake-invite-input")}),
            allowed_session_hashes=frozenset({hash_hosted_demo_secret("fake-session-input")}),
            allowed_session_binding_hashes=frozenset(
                {
                    build_hosted_demo_session_binding_hash(
                        tenant_id="tenant_local",
                        invite_id="invite_cp5",
                        session_id="session_cp5",
                        session_secret="fake-session-input",
                    )
                }
            ),
            per_session_quota=per_session_quota,
            global_quota=global_quota,
        )
    )


def deleted_payload_for(active_payload: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
    deleted_at = datetime.now(UTC)
    deletion_requested_at = deleted_at - timedelta(minutes=1)
    deletion_payload = copy.deepcopy(active_payload)
    deletion_payload["idempotencyKey"] = idempotency_key
    patch_section(
        deletion_payload,
        "retention",
        {
            "retentionState": "DELETED",
            "deletionState": "DELETED",
            "deletionRequestedAt": deletion_requested_at.isoformat(),
            "deletedAt": deleted_at.isoformat(),
            "providerDeletionStatus": "FAKE_LOCAL_DELETED",
        },
    )
    deletion_request_without_ids = HostedDemoAccessRequest.model_validate(deletion_payload)
    tombstone_checksum = build_hosted_demo_tombstone_checksum(
        request=deletion_request_without_ids,
        deleted_at=deleted_at,
    )
    patch_section(
        deletion_payload,
        "retention",
        {
            "tombstoneId": build_hosted_demo_tombstone_id(tombstone_checksum),
            "tombstoneChecksum": tombstone_checksum,
            "deletionEvidenceId": build_hosted_demo_deletion_evidence_id(tombstone_checksum),
        },
    )
    return deletion_payload


def assert_no_canary_leak(response_text: str) -> None:
    assert RAW_UPLOAD_CANARY not in response_text
    assert RAW_PROMPT_CANARY not in response_text
    assert "fake-invite-input" not in response_text
    assert "fake-session-input" not in response_text


def assert_runtime_access_quota_retention_evidence(evidence: dict[str, Any]) -> None:
    runtime_nonce = evidence.get("runtimeNonce")
    assert isinstance(runtime_nonce, str) and runtime_nonce.startswith("cp5-runtime-")
    assert evidence["runtimeSource"] == "fastapi-testclient"
    assert evidence["runtimeProjectsCreated"] >= 2, "runtime project creation evidence is required"
    assert evidence["runtimeRunsCreated"] >= 2, "runtime run evidence is required"
    assert evidence["accessBoundary"]["crossActorStatus"] == 403
    assert evidence["accessBoundary"]["crossProjectReplayCode"] == "NOT_FOUND"
    assert evidence["accessBoundary"]["idempotencyActorScoped"] is True
    assert evidence["accessBoundary"]["hostedDemoIdempotencyConflictCode"] == "IDEMPOTENCY_CONFLICT"
    assert evidence["quota"]["documentLimitCode"] == "PROJECT_DOCUMENT_LIMIT_EXCEEDED"
    assert evidence["quota"]["uploadLimitCode"] == "UPLOAD_TOO_LARGE"
    assert evidence["quota"]["promptLimitCode"] == "PROMPT_TOO_LARGE"
    assert evidence["quota"]["hostedDemoQuotaState"] == "COMMITTED"
    assert evidence["quota"]["hostedDemoExhaustedState"] == "EXHAUSTED"
    assert evidence["retention"]["activeAccessState"] == "GRANTED"
    assert evidence["retention"]["deletedReplayReason"] == "RETENTION_DELETED"
    assert evidence["retention"]["changedRetentionIdReason"] == "RETENTION_DELETED"
    assert evidence["retention"]["tombstoneVisible"] is True
    assert evidence["opsStatus"]["stage4RecordCounts"]["projects"] >= 2
    assert evidence["opsStatus"]["publicSafe"] is True


def test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path() -> None:
    client = TestClient(app)
    runtime_nonce = f"cp5-runtime-{uuid4().hex}"
    alpha, alpha_document, _alpha_ingestion, alpha_run = prepare_runtime_project(
        client,
        prefix="cp5-alpha",
        actor="alice",
        name="Alpha Runtime Lab",
        filename="alpha_runtime_lab.md",
        content=ALPHA_KNOWLEDGE,
        prompt="Create a grounded walkthrough for Alpha Runtime Lab using only approved source facts.",
    )
    beta, beta_document, _beta_ingestion, beta_run = prepare_runtime_project(
        client,
        prefix="cp5-beta",
        actor="alice",
        name="Alpha Boundary Lab",
        filename="alpha_boundary_lab.md",
        content=BETA_KNOWLEDGE,
        prompt="Create a grounded walkthrough for Alpha Boundary Lab using only approved source facts.",
    )
    assert alpha["projectId"] != beta["projectId"]
    assert alpha_document["documentId"] != beta_document["documentId"]
    assert "CP5-ALPHA-SENTINEL" in alpha_run["acceptedScriptText"]
    assert "CP5-BETA-SENTINEL" in beta_run["acceptedScriptText"]

    cross_actor = client.post(
        f"/api/v1/projects/{alpha['projectId']}/knowledge-documents",
        files={"file": ("bob.md", b"Bob cannot mutate Alice project.", "text/markdown")},
        headers=headers("cp5-cross-actor-upload", actor="bob"),
    )
    assert cross_actor.status_code == 403
    assert cross_actor.json()["error"]["code"] == "FORBIDDEN"

    bob_same_key = create_project(client, prefix="cp5-alpha", actor="bob", name="Bob Scoped Project")
    assert bob_same_key["projectId"] != alpha["projectId"]
    assert bob_same_key["ownerId"] == "bob"

    cross_project_replay = client.post(
        f"/api/v1/projects/{beta['projectId']}/ingestion-runs",
        json={"documentIds": [alpha_document["documentId"]]},
        headers=headers("cp5-cross-project-replay", actor="alice"),
    )
    assert cross_project_replay.status_code == 404
    assert cross_project_replay.json()["error"]["code"] == "NOT_FOUND"

    mismatched_source_run = client.post(
        f"/api/v1/projects/{beta['projectId']}/walkthrough-runs/{alpha_run['runId']}/multilingual-runs",
        json={"targetLanguage": "es", "glossaryTerms": ["Alpha Boundary Lab"], "requestedVoiceProvider": "mock"},
        headers=headers("cp5-mismatched-source-run", actor="alice"),
    )
    assert mismatched_source_run.status_code == 404
    assert mismatched_source_run.json()["error"]["code"] == "NOT_FOUND"

    blocked_idempotency_replay = client.post(
        f"/api/v1/projects/{alpha['projectId']}/walkthrough-runs",
        json={
            "audience": "PRODUCT_LEADER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Try to replay another actor with a valid-looking idempotency key.",
        },
        headers=headers("cp5-alpha-generate", actor="bob"),
    )
    assert blocked_idempotency_replay.status_code == 403
    assert blocked_idempotency_replay.json()["error"]["code"] == "FORBIDDEN"

    upload_limit = client.post(
        f"/api/v1/projects/{beta['projectId']}/knowledge-documents",
        files={
            "file": (
                "oversize.md",
                (RAW_UPLOAD_CANARY + "\n").encode() + (b"x" * (MAX_UPLOAD_REQUEST_BYTES + 1)),
                "text/markdown",
            )
        },
        headers=headers("cp5-upload-too-large", actor="alice"),
    )
    assert upload_limit.status_code == 413
    assert upload_limit.json()["error"]["code"] == "UPLOAD_TOO_LARGE"
    assert_no_canary_leak(upload_limit.text)

    document_limit_project = create_project(client, prefix="cp5-doc-limit", actor="alice", name="CP5 Doc Limit")
    for index in range(10):
        document_limit_upload = client.post(
            f"/api/v1/projects/{document_limit_project['projectId']}/knowledge-documents",
            files={"file": (f"limit{index}.md", f"bounded content {index}".encode(), "text/markdown")},
            headers=headers(f"cp5-doc-limit-{index}", actor="alice"),
        )
        assert document_limit_upload.status_code == 201
    document_limit = client.post(
        f"/api/v1/projects/{document_limit_project['projectId']}/knowledge-documents",
        files={"file": ("limit10.md", b"bounded overflow", "text/markdown")},
        headers=headers("cp5-doc-limit-10", actor="alice"),
    )
    assert document_limit.status_code == 413
    assert document_limit.json()["error"]["code"] == "PROJECT_DOCUMENT_LIMIT_EXCEEDED"

    prompt_limit = client.post(
        f"/api/v1/projects/{alpha['projectId']}/walkthrough-runs",
        json={
            "audience": "PRODUCT_LEADER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": RAW_PROMPT_CANARY + (" x" * (MAX_PROMPT_CHARS + 1)),
        },
        headers=headers("cp5-prompt-too-large", actor="alice"),
    )
    assert prompt_limit.status_code == 413
    assert prompt_limit.json()["error"]["code"] == "PROMPT_TOO_LARGE"
    assert_no_canary_leak(prompt_limit.text)

    configure_hosted_demo_access(global_quota=2, per_session_quota=2)
    active_payload = hosted_demo_payload_from_run(
        project=alpha,
        run=alpha_run,
        idempotency_key="cp5_access_active",
    )
    active = client.post("/api/v1/hosted-demo/access-decisions", json=active_payload)
    assert active.status_code == 200
    assert active.json()["access"]["accessState"] == "GRANTED"
    assert active.json()["quota"]["quotaState"] == "COMMITTED"
    assert active.json()["providerPosture"]["allowNetworkEgress"] is False
    assert_no_canary_leak(active.text)

    forged_artifact_replay = hosted_demo_payload_from_run(
        project=beta,
        run=beta_run,
        idempotency_key="cp5_access_active",
        retention_record_id="retention_cp5_forged",
    )
    forged_response = client.post("/api/v1/hosted-demo/access-decisions", json=forged_artifact_replay)
    assert forged_response.status_code == 409
    assert forged_response.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert_no_canary_leak(forged_response.text)

    quota_payload = copy.deepcopy(active_payload)
    quota_payload["idempotencyKey"] = "cp5_access_quota_second"
    quota_second = client.post("/api/v1/hosted-demo/access-decisions", json=quota_payload)
    assert quota_second.status_code == 200
    assert quota_second.json()["access"]["accessState"] == "GRANTED"
    exhausted_payload = copy.deepcopy(active_payload)
    exhausted_payload["idempotencyKey"] = "cp5_access_quota_exhausted"
    exhausted = client.post("/api/v1/hosted-demo/access-decisions", json=exhausted_payload)
    assert exhausted.status_code == 200
    assert exhausted.json()["access"]["accessState"] == "DENIED"
    assert exhausted.json()["quota"]["quotaState"] == "EXHAUSTED"
    assert exhausted.json()["access"]["denialReason"] == "QUOTA_EXHAUSTED"

    deleted_payload = deleted_payload_for(active_payload, idempotency_key="cp5_access_deleted")
    hosted_demo_service.record_local_retention_terminal_state(
        HostedDemoAccessRequest.model_validate(deleted_payload)
    )
    stale_replay = client.post("/api/v1/hosted-demo/access-decisions", json=active_payload)
    assert stale_replay.status_code == 200
    assert stale_replay.json()["access"]["accessState"] == "DENIED"
    assert stale_replay.json()["access"]["denialReason"] == "RETENTION_DELETED"
    assert stale_replay.json()["retention"]["retentionState"] == "DELETED"
    assert stale_replay.json()["retention"]["tombstoneChecksum"]
    assert stale_replay.json()["artifact"]["artifactVisibility"] == "DENIED"

    changed_retention_id = copy.deepcopy(active_payload)
    changed_retention_id["idempotencyKey"] = "cp5_access_changed_retention"
    patch_section(changed_retention_id, "retention", {"retentionRecordId": "retention_cp5_changed"})
    changed_retention = client.post("/api/v1/hosted-demo/access-decisions", json=changed_retention_id)
    assert changed_retention.status_code == 200
    assert changed_retention.json()["access"]["denialReason"] == "RETENTION_DELETED"
    assert changed_retention.json()["retention"]["retentionRecordId"] == "retention_cp5_active"

    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    ops_body = ops.json()
    assert ops_body["operationalPosture"] == "LOCAL_ONLY"
    assert_no_canary_leak(json.dumps(ops_body))

    runtime_evidence = {
        "runtimeNonce": runtime_nonce,
        "runtimeSource": "fastapi-testclient",
        "runtimeProjectsCreated": len({alpha["projectId"], beta["projectId"], document_limit_project["projectId"]}),
        "runtimeRunsCreated": len({alpha_run["runId"], beta_run["runId"]}),
        "accessBoundary": {
            "crossActorStatus": cross_actor.status_code,
            "crossProjectReplayCode": cross_project_replay.json()["error"]["code"],
            "mismatchedSourceRunStatus": mismatched_source_run.status_code,
            "idempotencyActorScoped": bob_same_key["projectId"] != alpha["projectId"]
            and blocked_idempotency_replay.status_code == 403,
            "hostedDemoIdempotencyConflictCode": forged_response.json()["error"]["code"],
        },
        "quota": {
            "documentLimitCode": document_limit.json()["error"]["code"],
            "uploadLimitCode": upload_limit.json()["error"]["code"],
            "promptLimitCode": prompt_limit.json()["error"]["code"],
            "hostedDemoQuotaState": active.json()["quota"]["quotaState"],
            "hostedDemoExhaustedState": exhausted.json()["quota"]["quotaState"],
        },
        "retention": {
            "activeAccessState": active.json()["access"]["accessState"],
            "deletedReplayReason": stale_replay.json()["access"]["denialReason"],
            "changedRetentionIdReason": changed_retention.json()["access"]["denialReason"],
            "tombstoneVisible": bool(stale_replay.json()["retention"]["tombstoneChecksum"]),
        },
        "opsStatus": {
            "stage4RecordCounts": ops_body["durability"]["stage4"]["recordCounts"],
            "publicSafe": "acceptedScriptText" not in json.dumps(ops_body),
        },
    }
    assert_runtime_access_quota_retention_evidence(runtime_evidence)


def test_checkpoint3_access_quota_retention_rejects_static_or_status_only_evidence() -> None:
    static_status = {
        "runtimeProjectsCreated": 0,
        "runtimeRunsCreated": 0,
        "runtimeSource": "status-only",
        "accessBoundary": {
            "crossActorStatus": 200,
            "crossProjectReplayCode": "STATIC_PASS",
            "idempotencyActorScoped": False,
        },
        "quota": {
            "documentLimitCode": "STATIC_PASS",
            "uploadLimitCode": "STATIC_PASS",
            "promptLimitCode": "STATIC_PASS",
            "hostedDemoQuotaState": "STATIC_PASS",
            "hostedDemoExhaustedState": "STATIC_PASS",
        },
        "retention": {
            "activeAccessState": "STATIC_PASS",
            "deletedReplayReason": "STATIC_PASS",
            "changedRetentionIdReason": "STATIC_PASS",
            "tombstoneVisible": False,
        },
        "opsStatus": {"stage4RecordCounts": {"projects": 0}, "publicSafe": True},
    }

    with pytest.raises(AssertionError):
        assert_runtime_access_quota_retention_evidence(static_status)
