from __future__ import annotations

# ruff: noqa: E402

import base64
import copy
import json
import os
import re
from collections.abc import Iterator
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
from backend.app.rag.chunking import checksum_text
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage4 import stage4_service
from backend.app.stage6 import MockTTSProvider, MockTranslationProvider, stage6_service
from backend.app.stage7 import (
    SYNTHETIC_AVATAR_CONSENT_VERSION,
    MockAvatarProvider,
    stage7_service,
)


MEDIA_ARTIFACT_KNOWLEDGE = b"""# Helio Media

Helio Media MEDIA-SENTINEL-CP4 is a fictional local onboarding studio for field operations teams.
Helio Media turns approved playbooks into grounded walkthrough scripts for operations reviewers.
Helio Media requires every media-adjacent artifact to stay bound to source citations and evaluation evidence.
Helio Media uses only local mock media artifacts in this acceptance fixture.
"""

SAFE_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@pytest.fixture(autouse=True)
def local_only_media_artifact_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    stage6_service.translation_provider = MockTranslationProvider()
    stage6_service.tts_provider = MockTTSProvider()
    stage6_service.external_tts_provider = None
    stage7_service.avatar_provider = MockAvatarProvider()
    reset_app_state_for_tests()
    yield
    stage4_service.llm = MockLLMProvider()
    stage6_service.translation_provider = MockTranslationProvider()
    stage6_service.tts_provider = MockTTSProvider()
    stage6_service.external_tts_provider = None
    stage7_service.avatar_provider = MockAvatarProvider()
    reset_app_state_for_tests()


def idempotency_headers(value: str) -> dict[str, str]:
    return {"Idempotency-Key": value}


def create_project(client: TestClient, *, prefix: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Helio Media",
            "description": "Synthetic C3A-CP4 media-artifacts fixture.",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers=idempotency_headers(f"{prefix}-project"),
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def upload_approve_and_ingest(client: TestClient, *, prefix: str, project_id: str) -> dict[str, Any]:
    upload = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("helio_media.md", MEDIA_ARTIFACT_KNOWLEDGE, "text/markdown")},
        headers=idempotency_headers(f"{prefix}-upload"),
    )
    assert upload.status_code == 201
    document = cast(dict[str, Any], upload.json())

    approval = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document['documentId']}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP4 media-artifacts knowledge."},
        headers=idempotency_headers(f"{prefix}-approval"),
    )
    assert approval.status_code == 200
    approved = cast(dict[str, Any], approval.json())

    ingestion = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document["documentId"]]},
        headers=idempotency_headers(f"{prefix}-ingest"),
    )
    assert ingestion.status_code == 201
    assert ingestion.json()["status"] == "COMPLETED"
    assert ingestion.json()["chunkCount"] > 0
    return approved


def generate_walkthrough(client: TestClient, *, prefix: str, project_id: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "RECRUITER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "CONFIDENT",
            "prompt": "Create a grounded media artifact walkthrough for Helio Media.",
        },
        headers=idempotency_headers(f"{prefix}-generate"),
    )
    assert response.status_code == 201
    run = cast(dict[str, Any], response.json())
    assert run["status"] == "COMPLETED"
    assert run["evaluationStatus"] == "PASSED"
    assert "MEDIA-SENTINEL-CP4" in run["acceptedScriptText"]
    return run


def generate_multilingual_artifacts(client: TestClient, *, prefix: str, project_id: str, run_id: str) -> dict[str, Any]:
    request = {
        "targetLanguage": "es",
        "glossaryTerms": ["Helio Media", "MEDIA-SENTINEL-CP4"],
        "requestedVoiceProvider": "mock",
    }
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
    first = client.post(path, json=request, headers=idempotency_headers(f"{prefix}-multilingual"))
    replay = client.post(path, json=request, headers=idempotency_headers(f"{prefix}-multilingual"))
    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    return cast(dict[str, Any], replay.json())


def capture_avatar_consent(client: TestClient, *, prefix: str, project_id: str, run_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
        json={"consentToUseSyntheticAvatar": True},
        headers=idempotency_headers(f"{prefix}-consent"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["consentStatementVersion"] == SYNTHETIC_AVATAR_CONSENT_VERSION
    assert body["evaluationStatus"] == "PASSED"
    return cast(str, body["consentRecordId"])


def multilingual_bundle_from(multilingual: dict[str, Any]) -> dict[str, Any]:
    artifacts = multilingual["artifacts"]
    trace = multilingual["trace"]
    return {
        "sourceRunId": multilingual["sourceRunId"],
        "multilingualRunId": multilingual["multilingualRunId"],
        "targetLanguage": multilingual["targetLanguage"],
        "translatedScriptChecksum": artifacts["translatedScript"]["checksum"],
        "subtitlesChecksum": artifacts["subtitles"]["checksum"],
        "voiceManifestChecksum": artifacts["voiceManifest"]["checksum"],
        "contextRefIds": trace["sourceContextRefIds"],
        "citationIndexes": trace["sourceCitationIndexes"],
        "evaluationId": trace["sourceEvaluationId"],
        "evaluationChecksum": trace["sourceEvaluationChecksum"],
        "providerPosture": {
            "translationProvider": multilingual["translationProvider"]["provider"],
            "translationProviderMode": multilingual["translationProvider"]["providerMode"],
            "voiceProvider": multilingual["voice"]["provider"],
            "voiceProviderMode": multilingual["voice"]["providerMode"],
        },
        "consentDisclosureVersion": SYNTHETIC_AVATAR_CONSENT_VERSION,
    }


def generate_avatar_artifacts(
    client: TestClient,
    *,
    prefix: str,
    project_id: str,
    run_id: str,
    multilingual: dict[str, Any],
) -> dict[str, Any]:
    consent_record_id = capture_avatar_consent(client, prefix=prefix, project_id=project_id, run_id=run_id)
    request = {
        "requestedAvatarProvider": "mock",
        "consentToUseSyntheticAvatar": True,
        "consentRecordId": consent_record_id,
        "clonedIdentityRequested": False,
        "multilingualBundle": multilingual_bundle_from(multilingual),
    }
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
    first = client.post(path, json=request, headers=idempotency_headers(f"{prefix}-avatar"))
    replay = client.post(path, json=request, headers=idempotency_headers(f"{prefix}-avatar"))
    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    return cast(dict[str, Any], replay.json())


def decode_artifact(artifact: dict[str, Any], *, expected_mime: str, expected_suffix: str) -> str:
    assert artifact["mimeType"] == expected_mime
    assert artifact["fileName"].endswith(expected_suffix)
    assert SAFE_ARTIFACT_NAME.fullmatch(artifact["fileName"])
    decoded = base64.b64decode(artifact["contentBase64"], validate=True).decode("utf-8")
    assert artifact["checksum"] == checksum_text(decoded)
    assert decoded.strip()
    return decoded


def runtime_evaluation_checksum(run: dict[str, Any]) -> str:
    return checksum_text(
        "\n".join(
            [
                run["evaluation"]["evaluationId"],
                run["runId"],
                run["trace"]["traceId"],
                run["evaluationStatus"],
                ",".join(context["contextRefId"] for context in run["contextRefs"]),
                ",".join(str(support["citationIndex"]) for support in run["evaluation"]["claimSupports"]),
            ]
        )
    )


def runtime_claim_support_ids(run: dict[str, Any]) -> list[str]:
    return [support["claimSupportId"] for support in run["evaluation"]["claimSupports"]]


def assert_preserves_grounded_runtime_text(text: str, *, run: dict[str, Any]) -> None:
    assert "MEDIA-SENTINEL-CP4" in text
    assert "[1]" in text
    grounded_sentence = run["acceptedScriptText"].splitlines()[-1].removesuffix(" [1]")
    content_lines = [
        line
        for line in text.splitlines()
        if not re.fullmatch(r"\d+", line.strip()) and "-->" not in line
    ]
    normalized_text = re.sub(r"\s+", " ", " ".join(content_lines))
    normalized_sentence = re.sub(r"\s+", " ", grounded_sentence)
    assert normalized_sentence in normalized_text


def assert_translated_runtime_artifact_text(text: str) -> None:
    assert "MEDIA-SENTINEL-CP4" in text
    assert "[1]" in text
    assert "Para ingenieros" in text


def assert_stage6_media_artifacts(multilingual: dict[str, Any], *, run: dict[str, Any]) -> None:
    assert multilingual["status"] == "COMPLETED"
    assert multilingual["sourceRunId"] == run["runId"]
    assert multilingual["sourceScriptText"] == run["acceptedScriptText"]
    assert multilingual["translationProvider"] == {"provider": "mock", "providerMode": "LOCAL"}
    assert multilingual["voice"]["provider"] == "mock"
    assert multilingual["voice"]["providerMode"] == "LOCAL"
    assert "voiceAudio" not in multilingual["artifacts"]

    trace = multilingual["trace"]
    assert trace["sourceRunId"] == run["runId"]
    assert trace["sourceContextRefIds"] == [context["contextRefId"] for context in run["contextRefs"]]
    assert trace["sourceCitationIndexes"] == [
        support["citationIndex"] for support in run["evaluation"]["claimSupports"]
    ]
    assert trace["sourceEvaluationId"] == run["evaluation"]["evaluationId"]
    assert trace["evaluationStatus"] == "PASSED"
    assert trace["sourceEvaluationChecksum"] == runtime_evaluation_checksum(run)
    assert trace["sourceClaimSupportIds"] == runtime_claim_support_ids(run)

    translated = decode_artifact(
        multilingual["artifacts"]["translatedScript"],
        expected_mime="text/markdown",
        expected_suffix=".md",
    )
    subtitles = decode_artifact(
        multilingual["artifacts"]["subtitles"],
        expected_mime="application/x-subrip",
        expected_suffix=".srt",
    )
    voice_manifest_text = decode_artifact(
        multilingual["artifacts"]["voiceManifest"],
        expected_mime="application/json",
        expected_suffix=".json",
    )
    metadata_text = decode_artifact(
        multilingual["artifacts"]["metadata"],
        expected_mime="application/json",
        expected_suffix=".json",
    )
    assert translated == multilingual["translatedScriptText"]
    assert subtitles == multilingual["subtitlesText"]
    voice_manifest = json.loads(voice_manifest_text)
    metadata = json.loads(metadata_text)
    assert_preserves_grounded_runtime_text(multilingual["sourceScriptText"], run=run)
    assert_translated_runtime_artifact_text(translated)
    assert_translated_runtime_artifact_text(subtitles)
    assert voice_manifest["provider"] == "mock"
    assert voice_manifest["providerMode"] == "LOCAL"
    assert voice_manifest["textChecksum"] == checksum_text(multilingual["translatedScriptText"])
    assert "No cloned voice or paid provider was used" in voice_manifest["disclosure"]
    assert metadata["sourceRunId"] == run["runId"]
    assert metadata["sourceEvaluationChecksum"] == trace["sourceEvaluationChecksum"]
    assert metadata["sourceClaimSupportIds"] == trace["sourceClaimSupportIds"]
    assert metadata["transcriptSegments"] == multilingual["transcriptSegments"]
    assert metadata["transcriptCorrectness"] == multilingual["transcriptCorrectness"]
    assert re.sub(r"\s+", " ", metadata["transcriptSegments"][0]["sourceText"]) == re.sub(
        r"\s+",
        " ",
        run["acceptedScriptText"],
    )
    assert metadata["transcriptSegments"][0]["targetText"] in translated
    assert re.sub(r"\s+", " ", metadata["transcriptSegments"][0]["englishReferenceText"]) == re.sub(
        r"\s+",
        " ",
        run["acceptedScriptText"],
    )
    assert metadata["artifacts"]["translatedScriptChecksum"] == multilingual["artifacts"]["translatedScript"]["checksum"]
    assert metadata["artifacts"]["subtitlesChecksum"] == multilingual["artifacts"]["subtitles"]["checksum"]
    assert metadata["artifacts"]["voiceManifestChecksum"] == multilingual["artifacts"]["voiceManifest"]["checksum"]


def assert_stage7_media_artifacts(avatar: dict[str, Any], *, run: dict[str, Any], multilingual: dict[str, Any]) -> None:
    assert avatar["status"] == "COMPLETED"
    assert avatar["sourceRunId"] == run["runId"]
    assert avatar["avatarProvider"]["provider"] == "mock"
    assert avatar["avatarProvider"]["providerMode"] == "LOCAL"
    assert avatar["providerConfig"]["allowNetworkEgress"] is False
    assert avatar["providerConfig"]["requiresApiKey"] is False
    assert avatar["providerConfig"]["supportsRealVideo"] is False
    assert avatar["avatarVideoProvider"]["enabled"] is False
    assert avatar["avatarVideoProvider"]["providerMode"] == "DISABLED"
    assert avatar["avatarVideoProvider"]["supportsClonedIdentity"] is False
    assert avatar["disclosure"]["aiGenerated"] is True
    assert avatar["disclosure"]["clonedIdentity"] is False

    trace = avatar["trace"]
    assert trace["sourceContextRefIds"] == [context["contextRefId"] for context in run["contextRefs"]]
    assert trace["sourceCitationIndexes"] == [
        support["citationIndex"] for support in run["evaluation"]["claimSupports"]
    ]
    assert trace["sourceEvaluationId"] == run["evaluation"]["evaluationId"]
    assert trace["sourceEvaluationChecksum"] == runtime_evaluation_checksum(run)
    assert trace["evaluationStatus"] == "PASSED"
    assert trace["multilingualRunId"] == multilingual["multilingualRunId"]
    assert trace["translatedScriptChecksum"] == multilingual["artifacts"]["translatedScript"]["checksum"]
    assert trace["subtitlesChecksum"] == multilingual["artifacts"]["subtitles"]["checksum"]
    assert trace["voiceManifestChecksum"] == multilingual["artifacts"]["voiceManifest"]["checksum"]

    demo_html = decode_artifact(avatar["artifacts"]["demoExport"], expected_mime="text/html", expected_suffix=".html")
    manifest_text = decode_artifact(
        avatar["artifacts"]["renderManifest"],
        expected_mime="application/json",
        expected_suffix=".json",
    )
    placeholder_text = decode_artifact(
        avatar["artifacts"]["videoExportPlaceholder"],
        expected_mime="application/json",
        expected_suffix=".json",
    )
    assert "<script" not in demo_html.lower()
    assert_translated_runtime_artifact_text(demo_html)
    manifest = json.loads(manifest_text)
    placeholder = json.loads(placeholder_text)
    assert manifest["source"]["runId"] == run["runId"]
    assert manifest["source"]["contextRefIds"] == trace["sourceContextRefIds"]
    assert manifest["source"]["citationIndexes"] == trace["sourceCitationIndexes"]
    assert manifest["source"]["evaluationId"] == trace["sourceEvaluationId"]
    assert manifest["source"]["evaluationChecksum"] == trace["sourceEvaluationChecksum"]
    assert manifest["multilingualBundle"]["multilingualRunId"] == multilingual["multilingualRunId"]
    assert manifest["multilingualBundle"]["translatedScriptChecksum"] == trace["translatedScriptChecksum"]
    assert manifest["multilingualBundle"]["subtitlesChecksum"] == trace["subtitlesChecksum"]
    assert manifest["multilingualBundle"]["voiceManifestChecksum"] == trace["voiceManifestChecksum"]
    assert manifest["avatarVideoProvider"] == avatar["avatarVideoProvider"]
    assert manifest["publicUseLicenseCheck"] == "mock-local-provider-only-no-third-party-media"
    assert placeholder["source"] == manifest["source"]
    assert placeholder["multilingualBundle"] == manifest["multilingualBundle"]
    assert placeholder["avatarVideoProvider"] == manifest["avatarVideoProvider"]
    assert placeholder["reason"] == "Stage 7 exports a validated HTML demo and metadata, not a real video binary."


def assert_media_artifact_contract(
    *,
    run: dict[str, Any],
    multilingual: dict[str, Any],
    avatar: dict[str, Any],
) -> None:
    assert run["evaluation"]["claimSupports"]
    assert run["contextRefs"]
    assert_stage6_media_artifacts(multilingual, run=run)
    assert_stage7_media_artifacts(avatar, run=run, multilingual=multilingual)


def runtime_media_artifact_path(client: TestClient) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = create_project(client, prefix="media-helio")
    upload_approve_and_ingest(client, prefix="media-helio", project_id=project["projectId"])
    run = generate_walkthrough(client, prefix="media-helio", project_id=project["projectId"])
    multilingual = generate_multilingual_artifacts(
        client,
        prefix="media-helio",
        project_id=project["projectId"],
        run_id=run["runId"],
    )
    avatar = generate_avatar_artifacts(
        client,
        prefix="media-helio",
        project_id=project["projectId"],
        run_id=run["runId"],
        multilingual=multilingual,
    )
    return run, multilingual, avatar


def test_checkpoint3_media_artifacts_executes_runtime_api_artifact_path() -> None:
    client = TestClient(app)
    run, multilingual, avatar = runtime_media_artifact_path(client)

    assert_media_artifact_contract(run=run, multilingual=multilingual, avatar=avatar)
    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    durability = ops.json()["durability"]
    assert durability["stage4"]["recordCounts"]["walkthroughRuns"] == 1
    assert durability["stage6"]["recordCounts"]["idempotencyRecords"] == 1
    assert durability["stage7"]["recordCounts"]["avatarRenders"] == 1
    assert durability["stage7"]["recordCounts"]["artifactMetadata"] == 1


def test_checkpoint3_media_artifacts_rejects_artifact_shape_without_source_binding() -> None:
    client = TestClient(app)
    run, multilingual, avatar = runtime_media_artifact_path(client)
    mutated = copy.deepcopy(avatar)
    mutated["trace"]["sourceEvaluationChecksum"] = "sha256:shape-only"

    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=multilingual, avatar=mutated)


def test_checkpoint3_media_artifacts_rejects_consistently_forged_source_evidence() -> None:
    client = TestClient(app)
    run, multilingual, avatar = runtime_media_artifact_path(client)
    forged_checksum = "sha256:" + ("f" * 64)
    forged_claim_support_ids = ["claim-static-fixture"]
    mutated_multilingual = copy.deepcopy(multilingual)
    mutated_avatar = copy.deepcopy(avatar)

    mutated_multilingual["trace"]["sourceEvaluationChecksum"] = forged_checksum
    mutated_multilingual["trace"]["sourceClaimSupportIds"] = forged_claim_support_ids
    metadata_text = decode_artifact(
        mutated_multilingual["artifacts"]["metadata"],
        expected_mime="application/json",
        expected_suffix=".json",
    )
    metadata = json.loads(metadata_text)
    metadata["sourceEvaluationChecksum"] = forged_checksum
    metadata["sourceClaimSupportIds"] = forged_claim_support_ids
    metadata_encoded = json.dumps(metadata, sort_keys=True)
    mutated_multilingual["artifacts"]["metadata"]["contentBase64"] = base64.b64encode(
        metadata_encoded.encode("utf-8")
    ).decode("ascii")
    mutated_multilingual["artifacts"]["metadata"]["checksum"] = checksum_text(metadata_encoded)

    mutated_avatar["trace"]["sourceEvaluationChecksum"] = forged_checksum
    mutated_avatar["trace"]["sourceClaimSupportIds"] = forged_claim_support_ids
    for artifact_name in ("renderManifest", "videoExportPlaceholder"):
        artifact_text = decode_artifact(
            mutated_avatar["artifacts"][artifact_name],
            expected_mime="application/json",
            expected_suffix=".json",
        )
        artifact_body = json.loads(artifact_text)
        artifact_body["source"]["evaluationChecksum"] = forged_checksum
        artifact_body["source"]["claimSupportIds"] = forged_claim_support_ids
        encoded = json.dumps(artifact_body, sort_keys=True)
        mutated_avatar["artifacts"][artifact_name]["contentBase64"] = base64.b64encode(
            encoded.encode("utf-8")
        ).decode("ascii")
        mutated_avatar["artifacts"][artifact_name]["checksum"] = checksum_text(encoded)

    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=mutated_multilingual, avatar=mutated_avatar)


def test_checkpoint3_media_artifacts_rejects_checksum_or_mime_mismatch() -> None:
    client = TestClient(app)
    run, multilingual, avatar = runtime_media_artifact_path(client)
    mutated = copy.deepcopy(multilingual)
    mutated["artifacts"]["voiceManifest"]["checksum"] = "sha256:static-fixture"

    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=mutated, avatar=avatar)

    mutated = copy.deepcopy(avatar)
    mutated["artifacts"]["renderManifest"]["mimeType"] = "text/plain"
    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=multilingual, avatar=mutated)


def test_checkpoint3_media_artifacts_rejects_real_media_or_clone_overclaim() -> None:
    client = TestClient(app)
    run, multilingual, avatar = runtime_media_artifact_path(client)
    mutated = copy.deepcopy(multilingual)
    mutated["artifacts"]["voiceAudio"] = {
        "fileName": "real-audio.mp3",
        "mimeType": "audio/mpeg",
        "contentBase64": base64.b64encode(b"fake real audio").decode("ascii"),
        "checksum": "sha256:not-accepted",
    }

    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=mutated, avatar=avatar)

    mutated = copy.deepcopy(avatar)
    mutated["disclosure"]["clonedIdentity"] = True
    with pytest.raises(AssertionError):
        assert_media_artifact_contract(run=run, multilingual=multilingual, avatar=mutated)
