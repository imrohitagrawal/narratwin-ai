import base64
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.stage4 import stage4_service
from backend.app.stage6 import stage6_service
from backend.app.stage7 import SYNTHETIC_AVATAR_CONSENT_VERSION, build_source_evaluation_checksum

IDEMPOTENCY_HEADER = "Idempotency-" + "Key"


def idempotency_headers(value: str) -> dict[str, str]:
    return {IDEMPOTENCY_HEADER: value}


def _create_completed_walkthrough(client: TestClient, *, key_prefix: str = "stage7") -> tuple[str, str]:
    fixture = Path("tests/fixtures/stage4_project.md")
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "NarraTwin AI",
            "description": "Grounded walkthrough generator",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers=idempotency_headers(f"{key_prefix}-project"),
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["projectId"]

    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", fixture.read_bytes(), "text/markdown")},
        headers=idempotency_headers(f"{key_prefix}-upload"),
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["documentId"]

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED"},
        headers=idempotency_headers(f"{key_prefix}-approval"),
    )
    assert approve_response.status_code == 200

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=idempotency_headers(f"{key_prefix}-ingest"),
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
        headers=idempotency_headers(f"{key_prefix}-generate"),
    )
    assert generation_response.status_code == 201
    assert generation_response.json()["status"] == "COMPLETED"
    return project_id, generation_response.json()["runId"]


def _capture_avatar_consent(
    client: TestClient,
    project_id: str,
    run_id: str,
    *,
    consent_to_use_synthetic_avatar: bool = True,
    idempotency_key: str = "stage7-consent",
    local_user_id: str | None = None,
) -> str:
    headers = idempotency_headers(idempotency_key)
    if local_user_id is not None:
        headers["X-Local-User-Id"] = local_user_id
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
        json={"consentToUseSyntheticAvatar": consent_to_use_synthetic_avatar},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    consent_record_id = body["consentRecordId"]
    assert isinstance(consent_record_id, str)
    source_run = stage4_service.walkthrough_runs[run_id]
    evaluation = source_run.evaluation
    assert evaluation is not None
    assert body["tenantId"] == "tenant_local"
    assert body["projectId"] == project_id
    assert body["actorId"] == (local_user_id or "user_local")
    assert body["sourceRunId"] == run_id
    assert body["traceId"] == source_run.trace_id
    assert body["sourceContextRefIds"] == [context.context_ref_id for context in source_run.retrieved_context]
    assert body["sourceCitationIndexes"] == [support.citation_index for support in evaluation.claim_supports]
    assert body["sourceEvaluationId"] == evaluation.evaluation_id
    assert body["sourceEvaluationChecksum"] == build_source_evaluation_checksum(
        source_evaluation_id=evaluation.evaluation_id,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        source_context_ref_ids=tuple(context.context_ref_id for context in source_run.retrieved_context),
        source_context_ref_count=len(source_run.retrieved_context),
        source_citation_indexes=tuple(support.citation_index for support in evaluation.claim_supports),
        source_citation_count=len(evaluation.claim_supports),
    )
    assert body["evaluationStatus"] == "PASSED"
    assert body["consentStatementVersion"] == "stage7-synthetic-avatar-consent-v1"
    assert body["consentStatementText"].startswith("I affirm that I am authorized")
    assert body["grantedAt"].endswith("Z")
    assert body["requestChecksum"].startswith("sha256:")
    assert body["avatarRenderId"] is None
    assert body["artifactChecksums"] == []
    return consent_record_id


def _create_multilingual_bundle(
    client: TestClient,
    project_id: str,
    run_id: str,
    *,
    key_prefix: str = "stage7",
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI", "source chunks"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers(f"{key_prefix}-multilingual"),
    )
    assert response.status_code == 201
    body = response.json()
    trace = body["trace"]
    artifacts = body["artifacts"]
    return {
        "sourceRunId": body["sourceRunId"],
        "multilingualRunId": body["multilingualRunId"],
        "targetLanguage": body["targetLanguage"],
        "translatedScriptChecksum": artifacts["translatedScript"]["checksum"],
        "subtitlesChecksum": artifacts["subtitles"]["checksum"],
        "voiceManifestChecksum": artifacts["voiceManifest"]["checksum"],
        "contextRefIds": trace["sourceContextRefIds"],
        "citationIndexes": trace["sourceCitationIndexes"],
        "evaluationId": trace["sourceEvaluationId"],
        "evaluationChecksum": trace["sourceEvaluationChecksum"],
        "providerPosture": {
            "translationProvider": body["translationProvider"]["provider"],
            "translationProviderMode": body["translationProvider"]["providerMode"],
            "voiceProvider": body["voice"]["provider"],
            "voiceProviderMode": body["voice"]["providerMode"],
        },
        "consentDisclosureVersion": SYNTHETIC_AVATAR_CONSENT_VERSION,
    }


def test_avatar_consent_api_replays_matching_idempotency_key() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents"

    first = client.post(
        path,
        json={"consentToUseSyntheticAvatar": True},
        headers=idempotency_headers("stage7-consent-replay"),
    )
    second = client.post(
        path,
        json={"consentToUseSyntheticAvatar": True},
        headers=idempotency_headers("stage7-consent-replay"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["consentRecordId"] == first.json()["consentRecordId"]


def test_avatar_consent_api_rejects_different_local_principal() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
        json={"consentToUseSyntheticAvatar": True},
        headers={"X-Local-User-Id": "other_user", **idempotency_headers("stage7-consent-forbidden")},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_avatar_consent_api_rejects_missing_walkthrough_run() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, _ = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/run_missing/avatar-consents",
        json={"consentToUseSyntheticAvatar": True},
        headers=idempotency_headers("stage7-consent-missing-run"),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_avatar_consent_api_rejects_non_affirmative_request() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
        json={"consentToUseSyntheticAvatar": False},
        headers=idempotency_headers("stage7-consent-false"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AVATAR_CONSENT_REQUIRED"


def test_avatar_render_api_returns_validated_demo_export_artifacts() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "clonedIdentityRequested": False,
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["consentRecordId"] == consent_record_id
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
    assert body["avatarVideoProvider"]["providerMode"] == "DISABLED"
    assert body["avatarVideoProvider"]["enabled"] is False
    assert body["avatarVideoProvider"]["allowNetworkEgress"] is False
    assert body["avatarVideoProvider"]["requiresApiKey"] is True
    assert body["avatarVideoProvider"]["supportsClonedIdentity"] is False
    assert body["avatarVideoProvider"]["assetProvenancePolicy"] == (
        "fully_synthetic_or_provider_stock_non_identifiable_only"
    )
    assert body["avatarVideoProvider"]["disclosureVersion"] == "stage7-avatar-video-disclosure-v1"
    assert body["avatarVideoProvider"]["retentionState"] == "NOT_CREATED"
    assert body["avatarVideoProvider"]["deletionState"] == "NOT_REQUESTED"
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
    source_run = stage4_service.walkthrough_runs[run_id]
    assert source_run.evaluation is not None
    expected_source_evaluation_checksum = build_source_evaluation_checksum(
        source_evaluation_id=source_run.evaluation.evaluation_id,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        source_context_ref_ids=tuple(context.context_ref_id for context in source_run.retrieved_context),
        source_context_ref_count=len(source_run.retrieved_context),
        source_citation_indexes=tuple(support.citation_index for support in source_run.evaluation.claim_supports),
        source_citation_count=len(source_run.evaluation.claim_supports),
    )
    assert body["trace"]["sourceEvaluationChecksum"] == expected_source_evaluation_checksum
    manifest = json.loads(base64.b64decode(body["artifacts"]["renderManifest"]["contentBase64"]).decode("utf-8"))
    assert body["sourceScriptText"] == stage6_service.multilingual_runs[str(multilingual_bundle["multilingualRunId"])].translated_script_text
    assert body["trace"]["multilingualRunId"] == multilingual_bundle["multilingualRunId"]
    assert body["trace"]["targetLanguage"] == "es"
    assert manifest["multilingualBundle"]["multilingualRunId"] == multilingual_bundle["multilingualRunId"]
    assert manifest["multilingualBundle"]["translatedScriptChecksum"] == multilingual_bundle["translatedScriptChecksum"]
    assert manifest["multilingualBundle"]["subtitlesChecksum"] == multilingual_bundle["subtitlesChecksum"]
    assert manifest["multilingualBundle"]["voiceManifestChecksum"] == multilingual_bundle["voiceManifestChecksum"]
    assert manifest["multilingualBundle"]["consentDisclosureVersion"] == SYNTHETIC_AVATAR_CONSENT_VERSION
    assert manifest["source"]["contextRefIds"] == body["trace"]["sourceContextRefIds"]
    assert manifest["source"]["citationIndexes"] == body["trace"]["sourceCitationIndexes"]
    assert manifest["source"]["evaluationId"] == body["trace"]["sourceEvaluationId"]
    assert manifest["source"]["evaluationChecksum"] == body["trace"]["sourceEvaluationChecksum"]
    assert manifest["avatarVideoProvider"] == body["avatarVideoProvider"]
    assert manifest["publicUseLicenseCheck"] == "mock-local-provider-only-no-third-party-media"
    placeholder = json.loads(
        base64.b64decode(body["artifacts"]["videoExportPlaceholder"]["contentBase64"]).decode("utf-8")
    )
    assert placeholder["providerConfig"] == manifest["providerConfig"]
    assert placeholder["avatarVideoProvider"] == manifest["avatarVideoProvider"]
    assert placeholder["source"] == manifest["source"]
    assert placeholder["multilingualBundle"] == manifest["multilingualBundle"]
    assert placeholder["disclosure"] == manifest["disclosure"]


def test_avatar_render_api_requires_validated_stage6_multilingual_bundle() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
        },
        headers=idempotency_headers("stage7-avatar-missing-bundle"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MULTILINGUAL_BUNDLE_REQUIRED"


def test_avatar_render_api_rejects_tampered_multilingual_bundle() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)

    tampered_bundle = {**multilingual_bundle, "targetLanguage": "fr"}
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": tampered_bundle,
        },
        headers=idempotency_headers("stage7-avatar-tampered-bundle"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MULTILINGUAL_BUNDLE_INVALID"


def test_avatar_render_api_rejects_unknown_multilingual_run_id() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    replayed_bundle = {**multilingual_bundle, "multilingualRunId": "mlrun_missing"}

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": replayed_bundle,
        },
        headers=idempotency_headers("stage7-avatar-unknown-multilingual-run"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MULTILINGUAL_BUNDLE_INVALID"


def test_avatar_render_api_rejects_replayed_multilingual_run_from_another_project() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client, key_prefix="stage7-a")
    other_project_id, other_run_id = _create_completed_walkthrough(client, key_prefix="stage7-b")
    other_bundle = _create_multilingual_bundle(client, other_project_id, other_run_id, key_prefix="stage7-b")
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    replayed_bundle = {**other_bundle, "sourceRunId": run_id}

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": replayed_bundle,
        },
        headers=idempotency_headers("stage7-avatar-replayed-multilingual-run"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MULTILINGUAL_BUNDLE_INVALID"


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_code"),
    [
        ("sourceRunId", "run_replayed", "MULTILINGUAL_BUNDLE_INVALID"),
        ("targetLanguage", "fr", "MULTILINGUAL_BUNDLE_INVALID"),
        ("translatedScriptChecksum", "sha256:tampered", "MULTILINGUAL_BUNDLE_INVALID"),
        ("subtitlesChecksum", "sha256:tampered", "MULTILINGUAL_BUNDLE_INVALID"),
        ("voiceManifestChecksum", "sha256:tampered", "MULTILINGUAL_BUNDLE_INVALID"),
        ("contextRefIds", ["context_ref_replayed"], "MULTILINGUAL_BUNDLE_INVALID"),
        ("citationIndexes", [999], "MULTILINGUAL_BUNDLE_INVALID"),
        ("evaluationId", "eval_replayed", "MULTILINGUAL_BUNDLE_INVALID"),
        ("evaluationChecksum", "sha256:tampered", "MULTILINGUAL_BUNDLE_INVALID"),
        (
            "providerPosture",
            {
                "translationProvider": "mock",
                "translationProviderMode": "LOCAL",
                "voiceProvider": "external-voice",
                "voiceProviderMode": "LOCAL",
            },
            "MULTILINGUAL_BUNDLE_INVALID",
        ),
        ("consentDisclosureVersion", "stage7-synthetic-avatar-consent-v0", "MULTILINGUAL_BUNDLE_INVALID"),
        ("missingSubtitlesChecksum", None, "VALIDATION_ERROR"),
        ("missingVoiceManifestChecksum", None, "VALIDATION_ERROR"),
    ],
)
def test_avatar_render_api_rejects_invalid_multilingual_bundle_fields(
    field_name: str,
    field_value: object,
    expected_code: str,
) -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    tampered_bundle = dict(multilingual_bundle)
    if field_name == "missingSubtitlesChecksum":
        tampered_bundle.pop("subtitlesChecksum")
    elif field_name == "missingVoiceManifestChecksum":
        tampered_bundle.pop("voiceManifestChecksum")
    else:
        tampered_bundle[field_name] = field_value

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": tampered_bundle,
        },
        headers=idempotency_headers(f"stage7-avatar-invalid-bundle-{field_name}"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == expected_code


def test_avatar_render_api_falls_back_to_mock_provider() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "external-avatar",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-fallback"),
    )

    assert response.status_code == 201
    avatar_provider = response.json()["avatarProvider"]
    assert avatar_provider["provider"] == "mock"
    assert avatar_provider["requestedProvider"] == "external-avatar"
    assert avatar_provider["fallbackReason"] == "REQUESTED_PROVIDER_UNAVAILABLE"
    assert response.json()["providerConfig"]["allowNetworkEgress"] is False


def test_avatar_render_api_requires_prior_durable_consent_record() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": False,
            "consentRecordId": "consent_unused",
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-no-consent"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AVATAR_CONSENT_REQUIRED"

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-missing-consent-record"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": "consent_missing",
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-invalid-consent-record"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AVATAR_CONSENT_RECORD_REQUIRED"


def test_avatar_render_api_rejects_cloned_identity_request() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "clonedIdentityRequested": True,
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-clone"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CLONED_IDENTITY_DISABLED"


def test_avatar_render_api_replays_matching_idempotency_key() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
    request = {
        "requestedAvatarProvider": "mock",
        "consentToUseSyntheticAvatar": True,
        "consentRecordId": consent_record_id,
        "multilingualBundle": multilingual_bundle,
    }

    first = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-replay"))
    second = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-replay"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["avatarRenderId"] == first.json()["avatarRenderId"]


def test_avatar_render_api_requires_evaluation_evidence() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    stage4_service.walkthrough_runs[run_id].evaluation = None

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        json={
            "requestedAvatarProvider": "mock",
            "consentToUseSyntheticAvatar": True,
            "consentRecordId": consent_record_id,
            "multilingualBundle": multilingual_bundle,
        },
        headers=idempotency_headers("stage7-avatar-missing-eval"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SOURCE_RUN_NOT_RENDERABLE"


def test_avatar_render_api_rejects_reuse_of_consumed_consent_record() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    multilingual_bundle = _create_multilingual_bundle(client, project_id, run_id)
    consent_record_id = _capture_avatar_consent(client, project_id, run_id)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
    request = {
        "requestedAvatarProvider": "mock",
        "consentToUseSyntheticAvatar": True,
        "consentRecordId": consent_record_id,
        "multilingualBundle": multilingual_bundle,
    }

    first = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-consumed-first"))
    second = client.post(path, json=request, headers=idempotency_headers("stage7-avatar-consumed-second"))

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "AVATAR_CONSENT_INVALID"
