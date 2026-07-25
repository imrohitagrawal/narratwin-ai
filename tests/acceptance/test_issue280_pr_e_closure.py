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
FORBIDDEN_METADATA_ONLY_MARKERS = (
    "Local mock conversion",
    "source segment",
    "protected term",
    "Conversion local simulada",
    "segmento fuente",
    "terme protege",
    "segment source",
    "مقطع المصدر",
    "مصطلح محفوظ",
    "ローカルモック変換",
    "ソース区分",
    "מקטע מקור",
    "स्रोत खंड",
)
PUBLIC_SAFE_MARKDOWN_MARKERS_BY_LANGUAGE = {
    "hi": "सार्वजनिक-सुरक्षित मार्कडाउन",
    "es": "markdown publico seguro",
    "de": "offentlich sichere Markdown",
    "fr": "markdown public sur",
    "pt-BR": "markdown publico seguro",
    "it": "markdown pubblico sicuro",
    "nl": "publiek veilige markdown",
    "pl": "publicznie bezpieczny markdown",
    "uk": "публічно безпечний markdown",
    "ru": "публично безопасный markdown",
    "zh-Hans": "公共安全 Markdown",
    "zh-Hant": "公共安全 Markdown",
    "ja": "公開安全なMarkdown",
    "ko": "공개 안전 Markdown",
    "ar": "ماركداون عام آمن",
    "arz": "ماركداون عام آمن",
    "he": "מרקדאון ציבורי בטוח",
    "fa": "مارکداون عمومی امن",
    "tr": "herkese acik guvenli markdown",
    "vi": "markdown cong khai an toan",
    "id": "markdown aman publik",
    "fil": "pampublikong ligtas na markdown",
    "th": "มาร์กดาวน์สาธารณะที่ปลอดภัย",
    "ms": "markdown selamat awam",
}


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


def arbitrary_semantic_markdown() -> str:
    return """# Solstice Beacon

## Intake controls

Solstice Beacon accepts bounded public-safe markdown from launch teams.

## Evidence routing

The workspace links adoption metrics and release blockers to cited markdown sections.
"""


def depth_semantic_markdown() -> str:
    return """# Meridian Planner

## Upload workflow

Meridian Planner accepts bounded public-safe markdown from product teams.

## Retrieval workflow

The local demo extracts source-backed claims about release rituals, adoption signals, and evidence handoffs.

## Evaluation workflow

Unsupported claims are refused before the stored walkthrough is shown in the browser.

## Source-backed example

For example, Meridian Planner links weekly adoption metrics to cited release review sections.

## Benefit and tradeoff

The benefit of cited release reviews is traceable adoption evidence, while the tradeoff is added reviewer effort.

## Way forward

A practical way forward is to review release blockers weekly before sharing the walkthrough.
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


def depth_semantic_payload(**overrides: Any) -> dict[str, Any]:
    value = payload(
        documents=[
            {
                "filename": "meridian-planner-depth.md",
                "contentType": "text/markdown",
                "markdown": depth_semantic_markdown(),
            }
        ],
    )
    value.update(overrides)
    return value


def semantic_payload(**overrides: Any) -> dict[str, Any]:
    value = payload(
        documents=[
            {
                "filename": "solstice-beacon.md",
                "contentType": "text/markdown",
                "markdown": arbitrary_semantic_markdown(),
            }
        ],
        glossaryTerms=["Solstice Beacon"],
    )
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


def test_issue280_pr_e_all_25_languages_convert_arbitrary_source_clauses_not_metadata_templates() -> None:
    assert len(SUPPORTED_LOCAL_DEMO_LANGUAGES) == 25

    for language in SUPPORTED_LOCAL_DEMO_LANGUAGES:
        body = post_demo(semantic_payload(targetLanguage=language), f"semantic-{language.lower()}")
        segments = body["multilingual"]["segments"]
        visible_target_text = "\n".join(segment["targetText"] for segment in segments)
        assert len(segments) == 2
        assert "Solstice Beacon" in visible_target_text
        assert "[1]" in visible_target_text
        assert "[2]" in visible_target_text
        assert not any(marker in visible_target_text for marker in FORBIDDEN_METADATA_ONLY_MARKERS)
        if language != "en":
            assert "accepts bounded public-safe markdown" not in visible_target_text
            assert "links adoption metrics and release blockers" not in visible_target_text
            assert PUBLIC_SAFE_MARKDOWN_MARKERS_BY_LANGUAGE[language] in visible_target_text


@pytest.mark.parametrize(
    ("target_language", "example_marker", "tradeoff_marker", "way_forward_marker"),
    [
        ("es", "Ejemplo respaldado por la fuente", "contrapartida", "Siguiente paso"),
        ("hi", "स्रोत-समर्थित उदाहरण", "समझौता", "आगे का रास्ता"),
    ],
)
def test_issue280_pr_e_depth_semantics_are_visible_and_source_bound(
    target_language: str,
    example_marker: str,
    tradeoff_marker: str,
    way_forward_marker: str,
) -> None:
    concise = post_demo(
        depth_semantic_payload(depth="CONCISE", targetLanguage=target_language),
        f"depth-{target_language}-concise",
    )
    standard = post_demo(
        depth_semantic_payload(depth="STANDARD", targetLanguage=target_language),
        f"depth-{target_language}-standard",
    )
    deep = post_demo(
        depth_semantic_payload(depth="DEEP", targetLanguage=target_language),
        f"depth-{target_language}-deep",
    )

    target_by_depth = {
        "CONCISE": "\n".join(segment["targetText"] for segment in concise["multilingual"]["segments"]),
        "STANDARD": "\n".join(segment["targetText"] for segment in standard["multilingual"]["segments"]),
        "DEEP": "\n".join(segment["targetText"] for segment in deep["multilingual"]["segments"]),
    }

    assert len(concise["multilingual"]["segments"]) == 3
    assert len(standard["multilingual"]["segments"]) == 4
    assert len(deep["multilingual"]["segments"]) == 6
    assert example_marker not in target_by_depth["CONCISE"]
    assert tradeoff_marker not in target_by_depth["CONCISE"]
    assert way_forward_marker not in target_by_depth["CONCISE"]
    assert example_marker in target_by_depth["STANDARD"]
    assert tradeoff_marker not in target_by_depth["STANDARD"]
    assert way_forward_marker not in target_by_depth["STANDARD"]
    assert example_marker in target_by_depth["DEEP"]
    assert tradeoff_marker in target_by_depth["DEEP"]
    assert way_forward_marker in target_by_depth["DEEP"]

    for body in (concise, standard, deep):
        segments = body["multilingual"]["segments"]
        supports = body["evaluation"]["claimSupports"]
        assert body["evaluation"]["unsupportedClaimCount"] == 0
        assert body["evaluation"]["evaluationId"]
        assert body["evaluation"]["evaluationChecksum"]
        assert len(supports) == len(segments)
        for segment, support in zip(segments, supports, strict=True):
            assert segment["citationIndexes"] == [support["citationIndex"]]
            assert segment["contextRefIds"] == [support["contextRefId"]]
            assert segment["claimSupportIds"] == [support["claimSupportId"]]
            assert f"[{support['citationIndex']}]" in segment["targetText"]
        assert set(body["correctnessReport"]["checks"].values()) == {"PASSED"}


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
