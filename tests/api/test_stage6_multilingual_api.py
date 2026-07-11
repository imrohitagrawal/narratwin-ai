from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.stage6 import TranslationProviderResult, stage6_service

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
        headers=idempotency_headers("stage6-project"),
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["projectId"]

    upload_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": ("stage4_project.md", fixture.read_bytes(), "text/markdown")},
        headers=idempotency_headers("stage6-upload"),
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["documentId"]

    approve_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED"},
        headers=idempotency_headers("stage6-approval"),
    )
    assert approve_response.status_code == 200

    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers=idempotency_headers("stage6-ingest"),
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
        headers=idempotency_headers("stage6-generate"),
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
            "glossaryTerms": ["NarraTwin AI", "project knowledge"],
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
    assert "project knowledge" in body["translatedScriptText"]
    assert body["subtitlesText"].startswith("1\n00:00:00,000 -->")
    assert body["translationProvider"]["provider"] == "mock"
    assert body["voice"]["provider"] == "mock"
    assert body["artifacts"]["translatedScript"]["mimeType"] == "text/markdown"
    assert body["artifacts"]["subtitles"]["fileName"].endswith(".srt")
    assert body["artifacts"]["subtitles"]["contentBase64"]
    assert body["artifacts"]["metadata"]["fileName"].endswith("-metadata.json")
    assert body["artifacts"]["metadata"]["mimeType"] == "application/json"


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
                translated_text=source_text,
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
