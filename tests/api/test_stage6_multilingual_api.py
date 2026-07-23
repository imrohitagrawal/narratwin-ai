from pathlib import Path
import base64
import json
from typing import Any, cast

from fastapi.testclient import TestClient

from backend.app.rag.chunking import checksum_text
from backend.app.main import app, reset_app_state_for_tests
from backend.app.stage6 import PRIORITY1_LANGUAGE_TAGS, PRIORITY2_LANGUAGE_TAGS
from backend.app.stage4 import stage4_service
from backend.app.stage6 import TranslationProviderResult, stage6_service, translate_demo_source_text
from backend.app.tts_provider import ElevenLabsTTSProvider, InMemoryTTSQuotaLedger, TTSHTTPResponse, TTSProviderConfig

IDEMPOTENCY_HEADER = "Idempotency-" + "Key"


def idempotency_headers(value: str) -> dict[str, str]:
    return {IDEMPOTENCY_HEADER: value}


def assert_translated_script_artifact_contains_transcript(body: dict[str, object]) -> None:
    artifacts = body["artifacts"]
    assert isinstance(artifacts, dict)
    translated_script_artifact = artifacts["translatedScript"]
    assert isinstance(translated_script_artifact, dict)
    artifact_text = base64.b64decode(translated_script_artifact["contentBase64"]).decode("utf-8")
    assert translated_script_artifact["checksum"] == checksum_text(artifact_text)
    transcript_correctness = cast(dict[str, object], body["transcriptCorrectness"])
    transcript_segments = cast(list[dict[str, Any]], body["transcriptSegments"])
    assert "# Multilingual transcript" in artifact_text
    assert f"Target language: {body['targetLanguage']}" in artifact_text
    assert f"Script: {transcript_correctness['script']}" in artifact_text
    assert f"Direction: {transcript_correctness['direction']}" in artifact_text
    assert artifact_text != body["translatedScriptText"]
    for segment in transcript_segments:
        assert f"## {segment['segmentId']}" in artifact_text
        assert f"Source English: {segment['sourceText']}" in artifact_text
        assert f"Target ({segment['targetLanguage']}): {segment['targetText']}" in artifact_text
        assert f"English reference: {segment['englishReferenceText']}" in artifact_text
        assert f"Citations: {', '.join(segment['citationMarkers'])}" in artifact_text
        assert f"Context refs: {', '.join(segment['contextRefIds'])}" in artifact_text
        assert f"Claim support ids: {', '.join(segment['claimSupportIds'])}" in artifact_text
        assert f"Source run id: {segment['sourceRunId']}" in artifact_text
        assert f"Evaluation id: {segment['evaluationId']}" in artifact_text


class FakeTTSTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout_seconds: float,
    ) -> TTSHTTPResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json_body": json_body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return TTSHTTPResponse(
            status_code=200,
            headers={"content-type": "audio/mpeg", "history-item-id": "hist_api_001"},
            body=b"api-mp3-bytes",
        )


def configure_api_external_tts(transport: FakeTTSTransport) -> None:
    stage6_service.external_tts_provider = ElevenLabsTTSProvider(
        config=TTSProviderConfig(
            provider_id="elevenlabs",
            enabled=True,
            api_key="sk_" + ("a" * 32),
            voice_id="stock_voice_001",
            voice_provenance="stock",
            model_id="eleven_flash_v2_5",
            model_version="2026-07-21-source-facts",
            supported_languages=("en", "es", "fr", "hi"),
            max_input_characters=4_000,
            max_audio_bytes=256,
            timeout_seconds=2.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
            max_concurrent_requests=1,
        ),
        transport=transport,
        quota_ledger=InMemoryTTSQuotaLedger(character_limit=1_000),
        sleep=lambda _seconds: None,
    )


def _create_completed_walkthrough(
    client: TestClient,
    *,
    prefix: str = "stage6",
    content: bytes | None = None,
) -> tuple[str, str]:
    fixture = Path("tests/fixtures/stage4_project.md")
    document_content = content if content is not None else fixture.read_bytes()
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "NarraTwin AI",
            "description": "Grounded walkthrough generator",
            "defaultAudience": "RECRUITER",
            "defaultLanguage": "en",
        },
        headers=idempotency_headers(f"{prefix}-project"),
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["projectId"]

    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", document_content, "text/markdown")},
        headers=idempotency_headers(f"{prefix}-upload"),
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["documentId"]

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED"},
        headers=idempotency_headers(f"{prefix}-approval"),
    )
    assert approve_response.status_code == 200

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=idempotency_headers(f"{prefix}-ingest"),
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
        headers=idempotency_headers(f"{prefix}-generate"),
    )
    assert generation_response.status_code == 201
    assert generation_response.json()["status"] == "COMPLETED"
    return project_id, generation_response.json()["runId"]


def test_multilingual_walkthrough_api_returns_downloadable_script_and_subtitle_artifacts() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-multilingual"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["sourceLanguage"] == "en"
    assert body["targetLanguage"] == "es"
    assert "NarraTwin AI" in body["translatedScriptText"]
    assert "project knowledge" not in body["translatedScriptText"]
    assert body["subtitlesText"].startswith("1\n00:00:00,000 -->")
    assert body["translationProvider"]["provider"] == "mock"
    assert body["voice"]["provider"] == "mock"
    assert body["artifacts"]["translatedScript"]["mimeType"] == "text/markdown"
    assert body["artifacts"]["subtitles"]["fileName"].endswith(".srt")
    assert body["artifacts"]["subtitles"]["contentBase64"]
    assert_translated_script_artifact_contains_transcript(body)
    assert body["trace"]["tenantId"] == "tenant_local"
    assert body["trace"]["projectId"] == project_id
    assert body["trace"]["actorId"] == "user_local"
    assert body["trace"]["sourceRunId"] == run_id
    assert body["trace"]["sourceTextChecksum"] == checksum_text(
        stage4_service.walkthrough_runs[run_id].accepted_script_text or ""
    )
    assert body["trace"]["sourceContextRefIds"]
    assert body["trace"]["sourceCitationIndexes"]
    assert body["trace"]["sourceClaimSupportIds"]
    assert body["trace"]["sourceEvaluationId"]
    assert body["trace"]["sourceEvaluationChecksum"]
    assert body["trace"]["evaluationStatus"] == "PASSED"
    assert body["artifacts"]["metadata"]["fileName"].endswith("-metadata.json")
    assert body["artifacts"]["metadata"]["mimeType"] == "application/json"


def test_language_catalog_api_exposes_support_status_without_fake_priority2_success() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    response = client.get("/api/v1/languages")

    assert response.status_code == 200
    body = response.json()
    catalog = {record["languageTag"]: record for record in body["languages"]}
    assert set(PRIORITY1_LANGUAGE_TAGS).issubset(catalog)
    assert set(PRIORITY2_LANGUAGE_TAGS).issubset(catalog)
    assert catalog["ko"]["label"] == "Korean / 한국어"
    assert catalog["hi"]["script"] == "Devanagari"
    assert catalog["ar"]["direction"] == "rtl"
    assert catalog["bn"]["localDemoSupportStatus"] == "PLANNED_UNSUPPORTED_LOCAL_DEMO"
    assert catalog["bn"]["providerSupportStatus"] == "UNSUPPORTED_LOCAL_DEMO"


def test_multilingual_walkthrough_api_returns_structured_transcript_and_matching_metadata_artifact() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "hi",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-hindi-structured"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["transcriptCorrectness"]["validationStatus"] == "PASSED"
    assert body["transcriptCorrectness"]["script"] == "Devanagari"
    assert body["transcriptCorrectness"]["direction"] == "ltr"
    assert body["transcriptSegments"]

    source_text = body["sourceScriptText"]
    target_text = body["translatedScriptText"]
    assert source_text
    assert target_text
    assert target_text != source_text
    assert "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]" in source_text
    assert "NarraTwin AI NarraTwin AI" not in source_text
    assert len(body["transcriptSegments"]) >= 2
    assert len(body["transcriptSegments"]) == body["transcriptCorrectness"]["segmentCount"]
    assert (
        "भर्ती विशेषज्ञों के लिए, NarraTwin AI स्वीकृत परियोजना-जानकारी को "
        "तथ्य-आधारित, चरण-दर-चरण प्रस्तुति की पटकथाओं में बदलता है। [1]"
    ) in target_text
    assert not body["transcriptSegments"][0]["targetText"].startswith("इंजीनियरों के लिए")
    assert "ग्राउंडेड वॉकथ्रू स्क्रिप्ट" not in target_text
    assert any("\u0900" <= char <= "\u097f" for char in target_text)
    assert "badalta hai" not in target_text

    for segment in body["transcriptSegments"]:
        assert segment["sourceText"]
        assert segment["targetLanguage"] == "hi"
        assert segment["targetText"]
        assert segment["targetText"] != segment["sourceText"]
        assert segment["englishReferenceText"]
        assert segment["citationMarkers"]
        assert segment["citationIndexes"]
        assert segment["contextRefIds"]
        assert segment["claimSupportIds"]
        assert set(segment["contextRefIds"]).issubset(set(body["trace"]["sourceContextRefIds"]))
        assert set(segment["claimSupportIds"]).issubset(set(body["trace"]["sourceClaimSupportIds"]))
        assert segment["sourceRunId"] == run_id
        assert segment["evaluationId"] == body["trace"]["sourceEvaluationId"]

    metadata = json.loads(base64.b64decode(body["artifacts"]["metadata"]["contentBase64"]).decode("utf-8"))
    assert metadata["transcriptSegments"] == body["transcriptSegments"]
    assert metadata["transcriptCorrectness"] == body["transcriptCorrectness"]
    assert_translated_script_artifact_contains_transcript(body)


def test_multilingual_walkthrough_api_translates_original_manual_review_document() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(
        client,
        prefix="stage6-original-manual-doc",
        content=b"""# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.

It supports recruiter and engineering audiences with audience-aware explanations.

The local demo uses mock local LLM, translation, voice, and avatar adapters for deterministic review.

Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.
""",
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "hi",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-original-manual-doc-hi"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["transcriptCorrectness"]["validationStatus"] == "PASSED"
    assert len(body["transcriptSegments"]) >= 3
    assert "भर्ती विशेषज्ञों के लिए" in body["translatedScriptText"]
    assert "भर्ती विशेषज्ञों और अभियांत्रिकी दर्शकों" in body["translatedScriptText"]
    assert "मॉक स्थानीय LLM, अनुवाद, आवाज़ और अवतार" in body["translatedScriptText"]
    assert "प्रत्येक उत्पन्न चरण-दर-चरण प्रस्तुति संबंधी दावे" in body["translatedScriptText"]
    assert "For recruiters" not in body["translatedScriptText"]
    assert "recruiter and engineering audiences" not in body["translatedScriptText"]
    assert "इंजीनियरों" not in body["translatedScriptText"]
    assert "जनरेट" not in body["translatedScriptText"]
    assert "वॉकथ्रू" not in body["translatedScriptText"]
    assert body["translatedScriptText"] != body["sourceScriptText"]
    metadata = json.loads(base64.b64decode(body["artifacts"]["metadata"]["contentBase64"]).decode("utf-8"))
    assert metadata["transcriptSegments"] == body["transcriptSegments"]
    assert_translated_script_artifact_contains_transcript(body)


def test_priority2_language_refuses_honestly_instead_of_generating_fake_success() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "bn",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-bn-unsupported"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "LOCAL_DEMO_LANGUAGE_UNSUPPORTED"
    assert "Bengali" in body["error"]["message"]


def test_multilingual_walkthrough_api_falls_back_to_mock_voice_provider() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "fr",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "external",
        },
        headers=idempotency_headers("stage6-fallback"),
    )

    assert response.status_code == 201
    voice = response.json()["voice"]
    assert voice["provider"] == "mock"
    assert voice["requestedProvider"] == "external"
    assert voice["fallbackReason"] == "REQUESTED_PROVIDER_UNAVAILABLE"


def test_multilingual_walkthrough_api_named_real_tts_fails_closed_by_default() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "elevenlabs",
        },
        headers=idempotency_headers("stage6-elevenlabs-disabled"),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TTS_PROVIDER_DISABLED"


def test_multilingual_walkthrough_api_returns_real_tts_manifest_and_audio_for_injected_fake() -> None:
    reset_app_state_for_tests()
    transport = FakeTTSTransport()
    configure_api_external_tts(transport)
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "elevenlabs",
        },
        headers=idempotency_headers("stage6-elevenlabs-fake"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["voice"]["provider"] == "elevenlabs"
    assert body["voice"]["providerMode"] == "OPTIONAL_EXTERNAL"
    assert body["artifacts"]["voiceAudio"]["mimeType"] == "audio/mpeg"
    assert body["artifacts"]["voiceAudio"]["contentBase64"]
    assert body["artifacts"]["voiceManifest"]["mimeType"] == "application/json"
    assert len(transport.calls) == 1


def test_multilingual_walkthrough_api_accepts_non_mock_local_translation_adapter() -> None:
    class LocalTranslationProvider:
        provider = "local-rule-based"
        provider_mode = "LOCAL"

        def translate(
            self,
            *,
            source_text: str,
            source_language: str,
            target_language: str,
            glossary_terms: list[str],
        ) -> TranslationProviderResult:
                return TranslationProviderResult(
                    provider=self.provider,
                    provider_mode=self.provider_mode,
                    source_language=source_language,
                    target_language=target_language,
                    translated_text=translate_demo_source_text(
                        source_text=source_text,
                        target_language=target_language,
                    ),
                    preserved_terms=[term for term in glossary_terms if term in source_text],
                )

    reset_app_state_for_tests()
    stage6_service.translation_provider = LocalTranslationProvider()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-local-adapter"),
    )

    assert response.status_code == 201
    assert response.json()["translationProvider"]["provider"] == "local-rule-based"


def test_multilingual_walkthrough_api_replays_matching_idempotency_key() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
    request = {
        "targetLanguage": "es",
        "glossaryTerms": ["NarraTwin AI"],
        "requestedVoiceProvider": "mock",
    }

    first = client.post(path, json=request, headers=idempotency_headers("replay"))
    second = client.post(path, json=request, headers=idempotency_headers("replay"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["multilingualRunId"] == first.json()["multilingualRunId"]


def test_multilingual_walkthrough_api_replays_equivalent_canonicalized_request() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"

    first = client.post(
        path,
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("canon-1"),
    )
    second = client.post(
        path,
        json={
            "targetLanguage": "es-ES",
            "glossaryTerms": [" NarraTwin AI "],
            "requestedVoiceProvider": "Mock",
        },
        headers=idempotency_headers("canon-2"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["multilingualRunId"] == first.json()["multilingualRunId"]


def test_multilingual_walkthrough_api_rejects_changed_payload_for_reused_idempotency_key() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
    request = {
        "targetLanguage": "es",
        "glossaryTerms": ["NarraTwin AI"],
        "requestedVoiceProvider": "mock",
    }

    first = client.post(path, json=request, headers=idempotency_headers("stage6-conflict"))
    conflict = client.post(
        path,
        json={
            **request,
            "targetLanguage": "fr",
        },
        headers=idempotency_headers("stage6-conflict"),
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_multilingual_walkthrough_api_rejects_non_translatable_source_run() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    stage4_service.walkthrough_runs[run_id].status = "FAILED"

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-source-run-failed"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SOURCE_RUN_NOT_TRANSLATABLE"


def test_multilingual_walkthrough_api_rejects_oversized_boundary_fields() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": [""] * 26,
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-too-many-blank-terms"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_multilingual_walkthrough_api_rejects_secret_like_glossary_terms() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)
    path = f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
    request = {
        "targetLanguage": "es",
        "glossaryTerms": ["api" + "_key=visible-secret-token-value"],
        "requestedVoiceProvider": "mock",
    }

    response = client.post(path, json=request, headers=idempotency_headers("stage6-secret-glossary"))
    replay = client.post(path, json=request, headers=idempotency_headers("stage6-secret-glossary"))
    conflict = client.post(
        path,
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-secret-glossary"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SECRET_LIKE_CONTENT"
    assert replay.status_code == 422
    assert replay.json()["error"]["code"] == "SECRET_LIKE_CONTENT"
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_multilingual_walkthrough_api_rejects_invalid_provider_name_at_boundary() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "x" * 65,
        },
        headers=idempotency_headers("stage6-provider-name-too-long"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_multilingual_walkthrough_api_rejects_whitespace_only_glossary_terms() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={
            "targetLanguage": "es",
            "glossaryTerms": ["   "],
            "requestedVoiceProvider": "mock",
        },
        headers=idempotency_headers("stage6-whitespace-term"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_multilingual_walkthrough_api_rejects_unsupported_language_cleanly() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)
    project_id, run_id = _create_completed_walkthrough(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        json={"targetLanguage": "tlh"},
        headers=idempotency_headers("stage6-unsupported-language"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "UNSUPPORTED_LANGUAGE"
    assert "Unsupported target language" in body["error"]["message"]
