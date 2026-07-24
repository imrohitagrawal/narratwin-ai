from __future__ import annotations

import base64
import json
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.stage6 import LANGUAGE_CATALOG


ISSUE280_E2E_PATH = "/api/v1/checkpoint3/issue280/local-e2e-demo"
SUPPORTED_LOCAL_DEMO_LANGUAGES = tuple(
    record.language_tag
    for record in LANGUAGE_CATALOG
    if record.local_demo_support_status == "SUPPORTED"
    and record.provider_support_status == "LOCAL_DEMO_FIXTURE"
    and record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"
)


@pytest.fixture(autouse=True)
def issue280_state() -> None:
    reset_app_state_for_tests()


def arbitrary_markdown() -> str:
    return """# Meridian Planner

## Upload workflow

Meridian Planner accepts bounded public-safe markdown from product teams.

## Retrieval workflow

The local demo extracts source-backed claims about release rituals, adoption signals, and evidence handoffs.

## Evaluation workflow

Unsupported claims are refused before the stored walkthrough is shown in the browser.

## Export workflow

Local mock artifacts keep citations, context references, claim supports, and checksums aligned.
"""


def payload(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "documents": [
            {
                "filename": "meridian-planner.md",
                "contentType": "text/markdown",
                "markdown": arbitrary_markdown(),
            }
        ],
        "audience": "ENGINEER",
        "depth": "STANDARD",
        "targetLanguage": "fr",
        "glossaryTerms": ["Meridian Planner"],
    }
    value.update(overrides)
    return value


def post_demo(body: dict[str, Any], seed: str) -> dict[str, Any]:
    client = TestClient(app)
    response = client.post(
        ISSUE280_E2E_PATH,
        json=body,
        headers={"Idempotency-Key": f"issue280-pr-e-{seed}", "X-Request-Id": f"req-issue280-pr-e-{seed}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_issue280_pr_e_supports_all_25_local_demo_languages_without_target_english_fallback() -> None:
    assert len(SUPPORTED_LOCAL_DEMO_LANGUAGES) == 25

    for language in SUPPORTED_LOCAL_DEMO_LANGUAGES:
        body = post_demo(payload(targetLanguage=language), f"lang-{language.lower()}")
        assert body["multilingual"]["targetLanguage"] == language
        assert body["multilingual"]["direction"] in {"ltr", "rtl"}
        segments = body["multilingual"]["segments"]
        assert len(segments) == len(body["evaluation"]["claimSupports"])
        assert len(segments) == len(body["retrieval"]["contextRefs"])
        for segment in segments:
            assert segment["citationIndexes"]
            assert segment["contextRefIds"]
            assert segment["claimSupportIds"]
            assert f"[{segment['citationIndexes'][0]}]" in segment["targetText"]
            if language != "en":
                assert "accepts bounded public-safe markdown" not in segment["targetText"]
                assert "source-backed claims about release rituals" not in segment["targetText"]
                assert "Unsupported claims are refused" not in segment["targetText"]
                assert "Local mock artifacts keep citations" not in segment["targetText"]
                assert "Meridian Planner" in segment["targetText"]


def test_issue280_pr_e_depth_changes_output_materially_without_losing_evidence() -> None:
    concise = post_demo(payload(depth="CONCISE", targetLanguage="es"), "depth-concise")
    standard = post_demo(payload(depth="STANDARD", targetLanguage="es"), "depth-standard")
    deep = post_demo(payload(depth="DEEP", targetLanguage="es"), "depth-deep")

    concise_text = concise["generated"]["acceptedScriptText"]
    standard_text = standard["generated"]["acceptedScriptText"]
    deep_text = deep["generated"]["acceptedScriptText"]

    assert concise_text != standard_text
    assert standard_text != deep_text
    assert len(concise_text.split()) < len(standard_text.split()) < len(deep_text.split())
    assert "source-grounded detail" in deep_text
    assert "tradeoff" in deep_text
    for body in (concise, standard, deep):
        assert body["evaluation"]["unsupportedClaimCount"] == 0
        assert len(body["evaluation"]["claimSupports"]) == len(body["multilingual"]["segments"])


@pytest.mark.parametrize(
    ("audience", "expected_marker"),
    [
        ("RECRUITER", "hiring signal"),
        ("HIRING_MANAGER", "delivery confidence"),
        ("ENGINEER", "implementation evidence"),
        ("PRODUCT_LEADER", "portfolio narrative"),
        ("CUSTOMER", "customer value"),
        ("BEGINNER", "plain-language orientation"),
        ("GLOBAL_VIEWER", "globally understandable context"),
    ],
)
def test_issue280_pr_e_audience_modes_have_distinct_source_grounded_emphasis(
    audience: str,
    expected_marker: str,
) -> None:
    body = post_demo(payload(audience=audience, targetLanguage="ja"), f"aud-{audience.lower()}")

    script = body["generated"]["acceptedScriptText"]
    assert expected_marker in script
    assert body["request"]["audience"] == audience
    assert body["evaluation"]["unsupportedClaimCount"] == 0
    assert body["evaluation"]["claimSupports"][0]["contextRefId"] in body["multilingual"]["segments"][0]["contextRefIds"]


def test_issue280_pr_e_preserves_eval_trace_glossary_and_artifact_parity() -> None:
    body = post_demo(payload(targetLanguage="ar", depth="DEEP", audience="PRODUCT_LEADER"), "parity")

    artifacts = body["artifacts"]
    report = body["correctnessReport"]
    assert body["multilingual"]["direction"] == "rtl"
    assert body["multilingual"]["multilingualRunId"].startswith("issue280_multi_")
    assert body["multilingual"]["preservedGlossaryTerms"] == ["Meridian Planner"]
    assert body["evaluation"]["evaluationChecksum"].startswith("sha256:")
    assert report["status"] == "PASSED"
    assert report["targetLanguage"] == "ar"
    assert report["traceId"] == body["trace"]["requestId"]
    assert report["segmentCount"] == len(body["multilingual"]["segments"])
    assert set(artifacts) == {
        "translatedScript",
        "subtitles",
        "transcriptMetadata",
        "voiceManifest",
        "avatarDemo",
        "renderManifest",
        "videoPlaceholder",
    }
    translated_text = decode_artifact(artifacts["translatedScript"])
    metadata = json.loads(decode_artifact(artifacts["transcriptMetadata"]))
    voice_manifest = json.loads(decode_artifact(artifacts["voiceManifest"]))
    render_manifest = json.loads(decode_artifact(artifacts["renderManifest"]))
    video_placeholder = json.loads(decode_artifact(artifacts["videoPlaceholder"]))

    assert body["storage"]["artifactBundleChecksum"].startswith("sha256:")
    assert body["storage"]["reportChecksum"].startswith("sha256:")
    assert body["storage"]["outputChecksum"] == report["outputChecksum"]
    assert metadata["segments"] == body["multilingual"]["segments"]
    assert metadata["evaluationId"] == body["evaluation"]["evaluationId"]
    assert metadata["evaluationChecksum"] == body["evaluation"]["evaluationChecksum"]
    assert voice_manifest["providerMode"] == "LOCAL_MOCK_DISABLED_EXTERNAL"
    assert render_manifest["sourceEvaluationId"] == body["evaluation"]["evaluationId"]
    assert video_placeholder["realMedia"] is False
    assert translated_text.count("[") >= len(body["multilingual"]["segments"])


def test_issue280_pr_e_refuses_planned_language_without_fake_success() -> None:
    client = TestClient(app)
    response = client.post(
        ISSUE280_E2E_PATH,
        json=payload(targetLanguage="bn"),
        headers={"Idempotency-Key": "issue280-pr-e-bn", "X-Request-Id": "req-issue280-pr-e-bn"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "ISSUE280_TRANSLATION_REFUSED"
    assert "Meridian Planner accepts bounded public-safe markdown" not in str(body)


def decode_artifact(artifact: dict[str, Any]) -> str:
    return base64.b64decode(artifact["contentBase64"]).decode("utf-8")
