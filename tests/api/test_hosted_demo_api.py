from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi.testclient import TestClient

from backend.app.hosted_demo import (
    HOSTED_DEMO_DISCLOSURE_VERSION,
    HostedDemoAccessConfig,
    build_hosted_demo_artifact_checksum,
    build_hosted_demo_evaluation_checksum,
    build_hosted_demo_session_binding_hash,
    hash_hosted_demo_secret,
    hosted_demo_service,
)
from backend.app.main import app, reset_app_state_for_tests


def valid_request_payload(**overrides: object) -> dict[str, object]:
    citation_refs = ["ctx_001", "ctx_002"]
    citation_indexes = [1, 2]
    source: dict[str, object] = {
        "tenantId": "tenant_local",
        "projectId": "project_001",
        "actorId": "user_local",
        "sourceRunId": "run_001",
        "traceId": "trace_001",
        "language": "en",
        "audience": "RECRUITER",
        "scriptChecksum": "sha256:" + "a" * 64,
        "citationRefs": citation_refs,
        "citationIndexes": citation_indexes,
        "evaluationId": "eval_001",
        "evaluationStatus": "PASSED",
        "multilingualRunId": "ml_001",
        "translatedScriptChecksum": "sha256:" + "b" * 64,
        "subtitlesChecksum": "sha256:" + "c" * 64,
        "voiceManifestChecksum": "sha256:" + "d" * 64,
        "ttsAudioChecksum": None,
        "avatarRenderId": "avatar_001",
        "avatarVideoProviderMetadataChecksum": "sha256:" + "e" * 64,
    }
    evaluation_checksum = build_hosted_demo_evaluation_checksum(
        tenant_id=cast(str, source["tenantId"]),
        project_id=cast(str, source["projectId"]),
        actor_id=cast(str, source["actorId"]),
        source_run_id=cast(str, source["sourceRunId"]),
        trace_id=cast(str, source["traceId"]),
        language=cast(str, source["language"]),
        audience=cast(str, source["audience"]),
        script_checksum=cast(str, source["scriptChecksum"]),
        evaluation_id=cast(str, source["evaluationId"]),
        evaluation_status=cast(str, source["evaluationStatus"]),
        citation_refs=tuple(citation_refs),
        citation_indexes=tuple(citation_indexes),
        multilingual_run_id=cast(str, source["multilingualRunId"]),
        translated_script_checksum=cast(str, source["translatedScriptChecksum"]),
        subtitles_checksum=cast(str, source["subtitlesChecksum"]),
        voice_manifest_checksum=cast(str, source["voiceManifestChecksum"]),
        tts_audio_checksum=cast(str | None, source["ttsAudioChecksum"]),
        avatar_render_id=cast(str, source["avatarRenderId"]),
        avatar_video_provider_metadata_checksum=cast(str, source["avatarVideoProviderMetadataChecksum"]),
    )
    source["evaluationChecksum"] = evaluation_checksum
    artifact_checksum = build_hosted_demo_artifact_checksum(
        artifact_id="artifact_001",
        artifact_kind="AVATAR_DEMO",
        artifact_file_name="demo.html",
        source_run_id=cast(str, source["sourceRunId"]),
        script_checksum=cast(str, source["scriptChecksum"]),
        evaluation_checksum=evaluation_checksum,
        disclosure_version=HOSTED_DEMO_DISCLOSURE_VERSION,
    )
    payload: dict[str, object] = {
        "artifact": {
            "artifactId": "artifact_001",
            "artifactKind": "AVATAR_DEMO",
            "artifactChecksum": artifact_checksum,
            "artifactMimeType": "text/html",
            "artifactFileName": "demo.html",
            "artifactSizeBytes": 2048,
            "artifactVisibility": "HOSTED_DEMO_REVIEWER",
        },
        "source": source,
        "disclosure": {
            "disclosureText": "AI-generated demo using local mock providers; no cloned identity or real provider call.",
            "disclosureVersion": HOSTED_DEMO_DISCLOSURE_VERSION,
        },
        "access": {
            "inviteId": "invite_001",
            "inviteSecret": "fake-invite-input",
            "sessionId": "session_001",
            "sessionSecret": "fake-session-input",
            "sessionState": "ACTIVE",
            "sessionExpiresAt": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
            "requestedOperation": "VIEW",
        },
        "retention": {
            "retentionRecordId": "retention_001",
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
        "idempotencyKey": "idem_001",
        "quotaUnits": 1,
        "localOutcome": "SUCCESS",
    }
    payload.update(overrides)
    return payload


def patched_section(payload: dict[str, object], section: str, patch: dict[str, object]) -> None:
    current = cast(dict[str, object], payload[section])
    payload[section] = {**current, **patch}


def test_hosted_demo_api_disabled_default_returns_denial_without_mutating_projects() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    response = client.post(
        "/api/v1/hosted-demo/access-decisions",
        json=valid_request_payload(),
        headers={"X-Local-User-Id": "forged_reviewer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access"]["accessState"] == "DENIED"
    assert body["access"]["denialReason"] == "HOSTED_DEMO_DISABLED"
    assert body["quota"]["quotaState"] == "NOT_RESERVED"
    assert "contentBase64" not in json.dumps(body)
    assert "raw script canary" not in json.dumps(body)

    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Local remains local",
            "description": "",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers={"Idempotency-Key": "hosted-demo-local-project"},
    )
    assert project_response.status_code == 201


def test_hosted_demo_api_rejects_duplicate_json_keys_and_unexpected_fields() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    duplicate = client.post(
        "/api/v1/hosted-demo/access-decisions",
        content=b'{"access": {}, "access": {}}',
        headers={"content-type": "application/json"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["error"]["code"] == "DUPLICATE_JSON_KEY"

    malformed = client.post(
        "/api/v1/hosted-demo/access-decisions",
        content=b"{",
        headers={"content-type": "application/json"},
    )
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "MALFORMED_JSON"

    non_object = client.post(
        "/api/v1/hosted-demo/access-decisions",
        content=b"[]",
        headers={"content-type": "application/json"},
    )
    assert non_object.status_code == 400
    assert non_object.json()["error"]["code"] == "INVALID_JSON_OBJECT"

    payload = valid_request_payload()
    payload["unexpected"] = True
    unexpected = client.post("/api/v1/hosted-demo/access-decisions", json=payload)
    assert unexpected.status_code == 422
    assert unexpected.json()["error"]["code"] == "VALIDATION_ERROR"

    delete_operation = valid_request_payload()
    patched_section(delete_operation, "access", {"requestedOperation": "DELETE"})
    delete_response = client.post("/api/v1/hosted-demo/access-decisions", json=delete_operation)
    assert delete_response.status_code == 422
    assert delete_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_hosted_demo_api_enabled_access_is_metadata_only_and_source_bound() -> None:
    reset_app_state_for_tests()
    hosted_demo_service.configure(
        HostedDemoAccessConfig(
            enabled=True,
            allowed_invite_hashes=frozenset({hash_hosted_demo_secret("fake-invite-input")}),
            allowed_session_hashes=frozenset({hash_hosted_demo_secret("fake-session-input")}),
            allowed_session_binding_hashes=frozenset(
                {
                    build_hosted_demo_session_binding_hash(
                        tenant_id="tenant_local",
                        invite_id="invite_001",
                        session_id="session_001",
                        session_secret="fake-session-input",
                    )
                }
            ),
            per_session_quota=2,
            global_quota=2,
        )
    )
    client = TestClient(app)

    granted = client.post("/api/v1/hosted-demo/access-decisions", json=valid_request_payload())

    assert granted.status_code == 200
    body = granted.json()
    assert body["access"]["accessState"] == "GRANTED"
    assert body["artifact"]["artifactId"] == "artifact_001"
    assert body["artifact"]["artifactChecksum"].startswith("sha256:")
    assert body["source"]["sourceRunId"] == "run_001"
    assert body["source"]["evaluationStatus"] == "PASSED"
    assert body["providerPosture"]["allowNetworkEgress"] is False
    assert body["providerPosture"]["realProviderCallsEnabled"] is False
    assert body["quota"]["idempotencyScope"].startswith("idem_scope_")
    encoded = json.dumps(body)
    assert "contentBase64" not in encoded
    assert "sourceScriptText" not in encoded
    assert "translatedScriptText" not in encoded
    assert "fake-invite-input" not in encoded
    assert "fake-session-input" not in encoded
    assert "session_001" not in encoded
    assert "idem_001" not in encoded


def test_hosted_demo_api_maps_failed_eval_and_pending_deletion_to_safe_errors() -> None:
    reset_app_state_for_tests()
    hosted_demo_service.configure(
        HostedDemoAccessConfig(
            enabled=True,
            allowed_invite_hashes=frozenset({hash_hosted_demo_secret("fake-invite-input")}),
            allowed_session_hashes=frozenset({hash_hosted_demo_secret("fake-session-input")}),
            allowed_session_binding_hashes=frozenset(
                {
                    build_hosted_demo_session_binding_hash(
                        tenant_id="tenant_local",
                        invite_id="invite_001",
                        session_id="session_001",
                        session_secret="fake-session-input",
                    )
                }
            ),
        )
    )
    client = TestClient(app)

    failed_eval = valid_request_payload()
    patched_section(failed_eval, "source", {"evaluationStatus": "FAILED"})
    failed_response = client.post("/api/v1/hosted-demo/access-decisions", json=failed_eval)
    assert failed_response.status_code == 422
    assert failed_response.json()["error"]["code"] == "EVALUATION_NOT_PASSED"
    assert "raw" not in json.dumps(failed_response.json()).lower()

    pending = valid_request_payload(idempotencyKey="pending_deletion")
    patched_section(
        pending,
        "retention",
        {
            "retentionState": "PENDING_DELETION",
            "deletionState": "PENDING",
            "deletionRequestedAt": datetime.now(UTC).isoformat(),
            "providerDeletionStatus": "PENDING",
        },
    )
    pending_response = client.post("/api/v1/hosted-demo/access-decisions", json=pending)
    assert pending_response.status_code == 200
    assert pending_response.json()["access"]["accessState"] == "DENIED"
    assert pending_response.json()["access"]["denialReason"] == "RETENTION_PENDING_DELETION"
