import base64
import json
import logging
import threading
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
import srt  # type: ignore[import-untyped]

from backend.app.rag.chunking import checksum_text
from backend.app.stage6 import (
    DownloadableArtifact,
    MAX_CAPTION_CHARS,
    PRIORITY1_LANGUAGE_TAGS,
    PRIORITY2_LANGUAGE_TAGS,
    Stage6Error,
    TranslationProviderResult,
    VoiceProviderResult,
    create_stage6_service,
    get_language_catalog,
    generate_subtitles,
    translate_demo_source_text,
    validate_multilingual_transcript_correctness,
    normalize_language_tag,
    split_captions,
)
from backend.app.stage7 import build_source_evaluation_checksum
from backend.app.tts_provider import ElevenLabsTTSProvider, InMemoryTTSQuotaLedger, TTSHTTPResponse, TTSProviderConfig

# Stage 6 multilingual tests preserve source run_id trace metadata and citation
# counts from the accepted grounded walkthrough script.

GOLDEN_RECRUITER_NARRATWIN_TRANSLATIONS = {
    "en": "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
    "hi": "भर्ती विशेषज्ञों के लिए, NarraTwin AI स्वीकृत परियोजना-जानकारी को तथ्य-आधारित, चरण-दर-चरण प्रस्तुति की पटकथाओं में बदलता है। [1]",
    "es": "Para reclutadores, NarraTwin AI convierte el conocimiento aprobado del proyecto en guiones de recorrido fundamentados con citas de origen. [1]",
    "de": "Für Recruiter, NarraTwin AI wandelt genehmigtes Projektwissen in fundierte Präsentationsskripte mit Quellenzitaten um. [1]",
    "fr": "Pour les recruteurs, NarraTwin AI transforme les connaissances approuvées du projet en scripts de présentation fondés avec des citations de source. [1]",
    "pt-BR": "Para recrutadores, O NarraTwin AI transforma conhecimento aprovado do projeto em roteiros de apresentação fundamentados com citações de fonte. [1]",
    "it": "Per i recruiter, NarraTwin AI trasforma la conoscenza approvata del progetto in copioni di presentazione fondati con citazioni delle fonti. [1]",
    "nl": "Voor recruiters, NarraTwin AI zet goedgekeurde projectkennis om in onderbouwde presentatiescripts met broncitaten. [1]",
    "pl": "Dla rekruterów, NarraTwin AI przekształca zatwierdzoną wiedzę projektową w ugruntowane skrypty prezentacyjne z cytatami źródłowymi. [1]",
    "uk": "Для рекрутерів, NarraTwin AI перетворює затверджені знання про проект на обґрунтовані сценарії презентації з посиланнями на джерела. [1]",
    "ru": "Для рекрутеров, NarraTwin AI превращает утвержденные знания проекта в обоснованные сценарии презентации с ссылками на источники. [1]",
    "zh-Hans": "面向招聘人员, NarraTwin AI 将已批准的项目知识转换为带有来源引用的有依据讲解脚本。 [1]",
    "zh-Hant": "面向招募人員, NarraTwin AI 將已核准的專案知識轉換為帶有來源引用的有根據導覽腳本。 [1]",
    "ja": "採用担当者向けに, NarraTwin AI は承認済みのプロジェクト知識を出典引用付きの根拠ある説明台本に変換します。 [1]",
    "ko": "채용 담당자를 위해, NarraTwin AI는 승인된 프로젝트 지식을 출처 인용이 있는 근거 기반 설명 대본으로 변환합니다. [1]",
    "ar": "لمسؤولي التوظيف, يحوّل NarraTwin AI المعرفة المعتمدة للمشروع إلى نصوص شرح موثقة باقتباسات من المصدر. [1]",
    "arz": "لمسؤولي التوظيف, NarraTwin AI بيحوّل معرفة المشروع المعتمدة لنصوص شرح موثقة ومعاها اقتباسات من المصدر. [1]",
    "he": "עבור מגייסים, NarraTwin AI הופך ידע פרויקט מאושר לתסריטי הסבר מבוססים עם ציטוטי מקור. [1]",
    "fa": "برای جذب‌کنندگان نیرو, NarraTwin AI دانش تأییدشده پروژه را به متن‌های توضیحی مستند با ارجاع به منبع تبدیل می‌کند. [1]",
    "tr": "İşe alım uzmanları için, NarraTwin AI, onaylanmış proje bilgisini kaynak alıntılı temellendirilmiş anlatım metinlerine dönüştürür. [1]",
    "vi": "Dành cho nhà tuyển dụng, NarraTwin AI chuyển kiến thức dự án đã phê duyệt thành kịch bản hướng dẫn có căn cứ kèm trích dẫn nguồn. [1]",
    "id": "Untuk perekrut, NarraTwin AI mengubah pengetahuan proyek yang disetujui menjadi naskah panduan berlandaskan bukti dengan kutipan sumber. [1]",
    "fil": "Para sa mga recruiter, Ginagawang may-batayang script ng pagpapaliwanag ng NarraTwin AI ang aprubadong kaalaman sa proyekto na may sipi ng pinagmulan. [1]",
    "th": "สำหรับผู้สรรหาบุคลากร, NarraTwin AI แปลงความรู้โครงการที่อนุมัติแล้วเป็นสคริปต์อธิบายที่มีหลักฐานพร้อมการอ้างอิงแหล่งที่มา [1]",
    "ms": "Untuk perekrut, NarraTwin AI menukar pengetahuan projek yang diluluskan kepada skrip penerangan berasas dengan petikan sumber. [1]",
}

FORBIDDEN_RAW_SOURCE_PHRASES_BY_LANGUAGE = {
    language_tag: (
        "For recruiters",
        "project knowledge",
        "grounded walkthrough scripts",
        "walkthrough scripts",
    )
    for language_tag in PRIORITY1_LANGUAGE_TAGS
    if language_tag != "en"
}


class FakeTTSTransport:
    def __init__(self, responses: list[TTSHTTPResponse | Exception]) -> None:
        self.responses = responses
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
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def external_tts_config(**overrides: object) -> TTSProviderConfig:
    values: dict[str, Any] = {
        "provider_id": "elevenlabs",
        "enabled": True,
        "api_key": "sk_" + ("a" * 32),
        "voice_id": "stock_voice_001",
        "voice_provenance": "stock",
        "model_id": "eleven_flash_v2_5",
        "model_version": "2026-07-21-source-facts",
        "supported_languages": ("en", "es", "fr", "hi"),
        "max_input_characters": 4_000,
        "max_audio_bytes": 256,
        "timeout_seconds": 2.0,
        "max_retries": 0,
        "retry_backoff_seconds": 0.0,
        "max_concurrent_requests": 1,
    }
    values.update(overrides)
    return TTSProviderConfig(**values)


def passed_eval_kwargs(*, citation_indexes: tuple[int, ...] = (1,)) -> dict[str, Any]:
    source_context_ref_ids = tuple(f"ctx_{index:03d}" for index in citation_indexes)
    source_claim_support_ids = tuple(f"claimsup_{index:03d}" for index in citation_indexes)
    return {
        "source_run_id": "run_001",
        "trace_id": "trace_001",
        "source_context_ref_count": len(source_context_ref_ids),
        "source_citation_count": len(citation_indexes),
        "source_context_ref_ids": source_context_ref_ids,
        "source_citation_indexes": citation_indexes,
        "source_claim_support_ids": source_claim_support_ids,
        "source_evaluation_id": "eval_001",
        "source_evaluation_checksum": build_source_evaluation_checksum(
            source_evaluation_id="eval_001",
            source_run_id="run_001",
            trace_id="trace_001",
            evaluation_status="PASSED",
            source_context_ref_ids=source_context_ref_ids,
            source_context_ref_count=len(source_context_ref_ids),
            source_citation_indexes=citation_indexes,
            source_citation_count=len(citation_indexes),
        ),
        "evaluation_status": "PASSED",
    }


def configure_external_tts(
    service: Any,
    transport: FakeTTSTransport,
    *,
    quota_limit: int = 1_000,
    **config_overrides: object,
) -> None:
    service.external_tts_provider = ElevenLabsTTSProvider(
        config=external_tts_config(**config_overrides),
        transport=transport,
        quota_ledger=InMemoryTTSQuotaLedger(character_limit=quota_limit),
        sleep=lambda _seconds: None,
    )


def test_translation_preserves_project_terms_from_glossary() -> None:
    service = create_stage6_service()
    source_script = (
        "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]"
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="mock",
        **passed_eval_kwargs(),
    )

    assert result.target_language == "es"
    assert "NarraTwin AI" in result.translated_script_text
    assert "project knowledge" not in result.translated_script_text
    assert "convierte" in result.translated_script_text
    assert result.translated_script_text != source_script
    assert result.artifacts.metadata.mime_type == "application/json"


@pytest.mark.parametrize("language_tag", PRIORITY1_LANGUAGE_TAGS)
def test_priority1_local_demo_golden_translations_preserve_recruiter_meaning(
    language_tag: str,
) -> None:
    service = create_stage6_service()
    source_script = (
        "For recruiters, NarraTwin AI turns approved project knowledge "
        "into grounded walkthrough scripts. [1]"
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language=language_tag,
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="mock",
        **passed_eval_kwargs(),
    )

    assert result.status == "COMPLETED"
    assert result.transcript_correctness.validation_status == "PASSED"
    assert result.translated_script_text == GOLDEN_RECRUITER_NARRATWIN_TRANSLATIONS[language_tag]
    assert result.transcript_segments[0].target_text == result.translated_script_text
    assert result.transcript_segments[0].source_text == source_script
    assert result.transcript_segments[0].english_reference_text == source_script
    assert result.transcript_segments[0].citation_markers == ("[1]",)
    assert result.transcript_segments[0].citation_indexes == (1,)
    for forbidden_phrase in FORBIDDEN_RAW_SOURCE_PHRASES_BY_LANGUAGE.get(language_tag, ()):
        assert forbidden_phrase not in result.translated_script_text


@pytest.mark.parametrize("language_tag", PRIORITY1_LANGUAGE_TAGS)
def test_priority1_local_demo_supports_original_narratwin_manual_review_document(
    language_tag: str,
) -> None:
    service = create_stage6_service()
    source_script = (
        "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1] "
        "For recruiters, It supports recruiter and engineering audiences with audience-aware explanations. [2] "
        "For recruiters, The local demo uses mock local LLM, translation, voice, and avatar adapters for deterministic review. [3] "
        "For recruiters, Every generated walkthrough claim must cite retrieved source chunks from approved knowledge. [4]"
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language=language_tag,
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="mock",
        **passed_eval_kwargs(citation_indexes=(1, 2, 3, 4)),
    )

    assert result.status == "COMPLETED"
    assert result.transcript_correctness.validation_status == "PASSED"
    assert len(result.transcript_segments) == 4
    assert result.transcript_segments[1].source_text.endswith("[2]")
    if language_tag != "en":
        assert result.translated_script_text != source_script
        assert "recruiter and engineering audiences" not in result.translated_script_text
        assert "The local demo uses" not in result.translated_script_text
        assert "Every generated walkthrough claim" not in result.translated_script_text
    if language_tag == "hi":
        assert "भर्ती विशेषज्ञों और अभियांत्रिकी दर्शकों" in result.translated_script_text
        assert "अभियंताओं के लिए" not in result.translated_script_text


@pytest.mark.parametrize(
    ("source_audience", "expected_hindi_prefix", "forbidden_hindi_prefix"),
    [
        ("recruiters", "भर्ती विशेषज्ञों के लिए", "अभियंताओं के लिए"),
        ("hiring managers", "नियुक्ति प्रबंधकों के लिए", "अभियंताओं के लिए"),
        ("engineers", "अभियंताओं के लिए", "भर्ती विशेषज्ञों के लिए"),
        ("product leaders", "उत्पाद नेतृत्वकर्ताओं के लिए", "अभियंताओं के लिए"),
        ("customers", "ग्राहकों के लिए", "अभियंताओं के लिए"),
        ("beginners", "नए उपयोगकर्ताओं के लिए", "अभियंताओं के लिए"),
        ("global viewers", "वैश्विक दर्शकों के लिए", "अभियंताओं के लिए"),
    ],
)
def test_hindi_local_demo_translation_preserves_selected_product_audience(
    source_audience: str,
    expected_hindi_prefix: str,
    forbidden_hindi_prefix: str,
) -> None:
    service = create_stage6_service()
    source_script = (
        f"For {source_audience}, NarraTwin AI turns approved project knowledge "
        "into grounded walkthrough scripts. [1]"
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language="hi",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="mock",
        **passed_eval_kwargs(),
    )

    assert result.status == "COMPLETED"
    assert result.transcript_correctness.validation_status == "PASSED"
    assert result.translated_script_text.startswith(expected_hindi_prefix)
    assert forbidden_hindi_prefix not in result.translated_script_text
    assert "ग्राउंडेड वॉकथ्रू स्क्रिप्ट" not in result.translated_script_text


def test_hindi_local_demo_translation_supports_cp8_stage4_sentence_with_audience_prefix() -> None:
    service = create_stage6_service()
    source_script = (
        "For recruiters, The Stage 4 slice uses a mock local LLM "
        "and mock local embeddings for deterministic tests. [2]"
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language="hi",
        glossary_terms=["Stage 4"],
        requested_voice_provider="mock",
        **passed_eval_kwargs(citation_indexes=(2,)),
    )

    assert result.status == "COMPLETED"
    assert result.transcript_correctness.validation_status == "PASSED"
    assert (
        result.translated_script_text
        == "भर्ती विशेषज्ञों के लिए, Stage 4 स्लाइस निर्धारक परीक्षणों के लिए मॉक स्थानीय LLM और मॉक स्थानीय एम्बेडिंग का उपयोग करता है। [2]"
    )
    assert "अभियंताओं के लिए" not in result.translated_script_text


def test_stage6_rejects_uncited_trailing_source_text_before_completion() -> None:
    service = create_stage6_service()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script=(
                "NarraTwin AI creates grounded walkthrough scripts. [1] "
                "TRAILING UNCITED ENGLISH SHOULD NOT DISAPPEAR."
            ),
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            requested_voice_provider="mock",
            **passed_eval_kwargs(),
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "TRANSCRIPT_CORRECTNESS_FAILED"


def test_stage6_service_rejects_success_without_passed_source_evidence() -> None:
    class WrongSemanticProvider:
        provider = "wrong-local"
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
                translated_text="NarraTwin AI WRONG SEMANTIC LOCAL OUTPUT",
                preserved_terms=glossary_terms,
            )

    service = create_stage6_service()
    service.translation_provider = WrongSemanticProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            requested_voice_provider="mock",
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_language_catalog_marks_priority1_supported_and_priority2_planned() -> None:
    catalog = {record.language_tag: record for record in get_language_catalog()}

    assert set(PRIORITY1_LANGUAGE_TAGS).issubset(catalog)
    assert set(PRIORITY2_LANGUAGE_TAGS).issubset(catalog)
    assert catalog["hi"].english_name == "Hindi"
    assert catalog["hi"].native_name == "हिन्दी"
    assert catalog["hi"].script == "Devanagari"
    assert catalog["hi"].local_demo_support_status == "SUPPORTED"
    assert catalog["ar"].direction == "rtl"
    assert catalog["he"].direction == "rtl"
    assert catalog["ko"].native_name == "한국어"

    for language_tag in PRIORITY1_LANGUAGE_TAGS:
        record = catalog[language_tag]
        assert record.market_priority == 1
        assert record.local_demo_support_status == "SUPPORTED"
        assert record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"

    for language_tag in PRIORITY2_LANGUAGE_TAGS:
        record = catalog[language_tag]
        assert record.market_priority == 2
        assert record.local_demo_support_status == "PLANNED_UNSUPPORTED_LOCAL_DEMO"
        assert record.test_coverage_level == "CATALOG_ONLY"


def test_hindi_transcript_validation_rejects_romanized_fallback() -> None:
    segment: dict[str, Any] = {
        "segmentId": "seg_001",
        "sourceText": "For engineers, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
        "targetLanguage": "hi",
        "targetText": "Engineers ke liye, NarraTwin AI sweekrit project knowledge ko grounded walkthrough scripts mein badalta hai. [1]",
        "englishReferenceText": "For engineers, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
        "citationMarkers": ["[1]"],
        "citationIndexes": [1],
        "contextRefIds": ["ctx_001"],
        "claimSupportIds": ["claimsup_001"],
        "sourceRunId": "run_001",
        "evaluationId": "eval_001",
    }

    with pytest.raises(Stage6Error) as exc:
        validate_multilingual_transcript_correctness(
            language_tag="hi",
            source_text=segment["sourceText"],
            segments=[segment],
            source_run_id="run_001",
            evaluation_id="eval_001",
            context_ref_ids=("ctx_001",),
            citation_indexes=(1,),
            claim_support_ids=("claimsup_001",),
        )

    assert exc.value.code == "TRANSCRIPT_CORRECTNESS_FAILED"


def test_transcript_validation_rejects_metadata_only_completed_success() -> None:
    segment: dict[str, Any] = {
        "segmentId": "seg_001",
        "sourceText": "For engineers, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
        "targetLanguage": "ja",
        "targetText": "For engineers, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
        "englishReferenceText": "",
        "citationMarkers": ["[1]"],
        "citationIndexes": [1],
        "contextRefIds": [],
        "claimSupportIds": ["claimsup_001"],
        "sourceRunId": "run_001",
        "evaluationId": "eval_001",
    }

    with pytest.raises(Stage6Error) as exc:
        validate_multilingual_transcript_correctness(
            language_tag="ja",
            source_text=segment["sourceText"],
            segments=[segment],
            source_run_id="run_001",
            evaluation_id="eval_001",
            context_ref_ids=("ctx_001",),
            citation_indexes=(1,),
            claim_support_ids=("claimsup_001",),
        )

    assert exc.value.code == "TRANSCRIPT_CORRECTNESS_FAILED"


def test_domain_service_rejects_blank_glossary_terms_directly() -> None:
    service = create_stage6_service()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI", "   "],
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "VALIDATION_ERROR"


def test_domain_service_rejects_secret_like_glossary_terms_directly() -> None:
    service = create_stage6_service()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["api" + "_key=visible-secret-token-value"],
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "SECRET_LIKE_CONTENT"


def test_subtitle_timing_format_is_valid_subrip() -> None:
    subtitles = generate_subtitles(
        script_text=(
            "NarraTwin AI creates a grounded walkthrough. "
            "Every generated claim keeps citation evidence."
        ),
        language="en",
        seconds_per_caption=3,
    )

    parsed = list(srt.parse(subtitles))

    assert subtitles.startswith("1\n00:00:00,000 --> 00:00:03,000")
    assert len(parsed) == 2
    assert parsed[0].start == timedelta(seconds=0)
    assert parsed[0].end == timedelta(seconds=3)
    assert parsed[1].start == parsed[0].end
    assert parsed[1].end > parsed[1].start


def test_requested_voice_provider_falls_back_to_mock_provider() -> None:
    service = create_stage6_service()

    result = service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="fr",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="external",
        **passed_eval_kwargs(),
    )

    assert result.voice.provider == "mock"
    assert result.voice.requested_provider == "external"
    assert result.voice.fallback_reason == "REQUESTED_PROVIDER_UNAVAILABLE"
    assert result.voice.provider_mode == "LOCAL"
    assert result.voice.artifact.content_base64
    manifest = json.loads(base64.b64decode(result.voice.artifact.content_base64).decode("utf-8"))
    assert manifest["languageDisplayName"] == "French"
    assert manifest["mockAudioProfile"]["sampleRateHz"] == 16000


def test_named_real_tts_provider_fails_closed_when_disabled_by_default() -> None:
    service = create_stage6_service()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            requested_voice_provider="elevenlabs",
            **passed_eval_kwargs(),
        )

    assert exc.value.status_code == 403
    assert exc.value.code == "TTS_PROVIDER_DISABLED"


def test_named_real_tts_provider_requires_passed_eval_and_source_evidence_before_transport() -> None:
    service = create_stage6_service()
    transport = FakeTTSTransport(
        [TTSHTTPResponse(status_code=200, headers={"content-type": "audio/mpeg"}, body=b"audio")]
    )
    configure_external_tts(service, transport)

    for evaluation_status in ("FAILED", "UNKNOWN"):
        with pytest.raises(Stage6Error) as exc:
            service.generate_multilingual_walkthrough(
                source_script="NarraTwin AI creates grounded walkthrough scripts.",
                target_language="es",
                glossary_terms=["NarraTwin AI"],
                requested_voice_provider="elevenlabs",
                evaluation_status=evaluation_status,
            )

        assert exc.value.status_code == 422
        assert exc.value.code == "PROVIDER_OUTPUT_INVALID"

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            requested_voice_provider="elevenlabs",
            **{**passed_eval_kwargs(), "source_evaluation_checksum": ""},
    )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"
    assert transport.calls == []


def test_translation_output_must_not_add_new_citation_markers_before_tts() -> None:
    class CitationAddingTranslationProvider:
        provider = "citation-adding-local"
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
                translated_text=source_text + " Unsupported extra claim. [999]",
                preserved_terms=glossary_terms,
            )

    service = create_stage6_service()
    service.translation_provider = CitationAddingTranslationProvider()
    transport = FakeTTSTransport(
        [TTSHTTPResponse(status_code=200, headers={"content-type": "audio/mpeg"}, body=b"audio")]
    )
    configure_external_tts(service, transport)

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            requested_voice_provider="elevenlabs",
            **passed_eval_kwargs(),
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"
    assert transport.calls == []


def test_real_tts_audio_and_manifest_bind_source_eval_and_artifact_metadata() -> None:
    service = create_stage6_service()
    transport = FakeTTSTransport(
        [
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "audio/mpeg", "history-item-id": "hist_001"},
                body=b"mp3-bytes",
            )
        ]
    )
    configure_external_tts(service, transport)

    result = service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="elevenlabs",
        actor_id="audience_recruiter",
        **passed_eval_kwargs(),
    )

    assert result.voice.provider == "elevenlabs"
    assert result.voice.provider_mode == "OPTIONAL_EXTERNAL"
    assert result.voice.audio_artifact is not None
    assert result.artifacts.voice_audio == result.voice.audio_artifact
    manifest = json.loads(base64.b64decode(result.voice.artifact.content_base64).decode("utf-8"))
    assert manifest["schemaVersion"] == "stage6-tts-manifest-v2"
    assert manifest["provider"] == "elevenlabs"
    assert manifest["providerModelId"] == "eleven_flash_v2_5"
    assert manifest["providerModelVersion"] == "2026-07-21-source-facts"
    assert manifest["providerHistoryItemId"] == "hist_001"
    assert manifest["voiceProvenance"] == "stock"
    assert manifest["sourceRunId"] == "run_001"
    assert manifest["traceId"] == "trace_001"
    assert manifest["audienceId"] == "audience_recruiter"
    assert manifest["sourceEvaluationStatus"] == "PASSED"
    assert manifest["sourceEvaluationChecksum"] == passed_eval_kwargs()["source_evaluation_checksum"]
    assert manifest["sourceCitationIndexes"] == [1]
    assert manifest["artifactChecksum"] == result.voice.audio_artifact.checksum
    assert result.voice.audio_artifact.mime_type == "audio/mpeg"


def test_real_tts_idempotency_replay_does_not_duplicate_provider_spend() -> None:
    service = create_stage6_service()
    transport = FakeTTSTransport(
        [
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "audio/mpeg", "history-item-id": "hist_001"},
                body=b"mp3-bytes",
            )
        ]
    )
    configure_external_tts(service, transport)
    request = {
        "source_script": "NarraTwin AI creates grounded walkthrough scripts. [1]",
        "target_language": "es",
        "glossary_terms": ["NarraTwin AI"],
        "requested_voice_provider": "elevenlabs",
        "idempotency_scope": "tenant:user:project:run_001",
        "idempotency_key": "tts-spend",
        **passed_eval_kwargs(),
    }

    first = service.generate_multilingual_walkthrough(**request)
    second = service.generate_multilingual_walkthrough(**request)

    assert second.multilingual_run_id == first.multilingual_run_id
    assert len(transport.calls) == 1


def test_tts_artifact_deletion_tombstones_audio_and_records_provider_evidence() -> None:
    service = create_stage6_service()
    transport = FakeTTSTransport(
        [
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "audio/mpeg", "history-item-id": "hist_001"},
                body=b"mp3-bytes",
            )
        ]
    )
    configure_external_tts(service, transport)
    result = service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="elevenlabs",
        **passed_eval_kwargs(),
    )

    deletion = service.delete_tts_artifacts(
        multilingual_run_id=result.multilingual_run_id,
        requested_by="auditor",
        reason="retention-test",
    )

    assert deletion.multilingual_run_id == result.multilingual_run_id
    assert deletion.provider == "elevenlabs"
    assert deletion.provider_history_item_id == "hist_001"
    assert deletion.local_tombstone is True
    assert deletion.provider_deletion_status == "PENDING_PROVIDER_DELETE"
    assert service.multilingual_runs[result.multilingual_run_id].voice.audio_artifact is None
    assert service.tts_deletions[result.multilingual_run_id] == deletion


def test_tts_artifact_deletion_updates_idempotency_replay_result() -> None:
    service = create_stage6_service()
    transport = FakeTTSTransport(
        [
            TTSHTTPResponse(
                status_code=200,
                headers={"content-type": "audio/mpeg", "history-item-id": "hist_001"},
                body=b"mp3-bytes",
            )
        ]
    )
    configure_external_tts(service, transport)
    request = {
        "source_script": "NarraTwin AI creates grounded walkthrough scripts. [1]",
        "target_language": "es",
        "glossary_terms": ["NarraTwin AI"],
        "requested_voice_provider": "elevenlabs",
        "idempotency_scope": "tenant:user:project:run_001",
        "idempotency_key": "tts-delete",
        **passed_eval_kwargs(),
    }
    result = service.generate_multilingual_walkthrough(**request)

    service.delete_tts_artifacts(
        multilingual_run_id=result.multilingual_run_id,
        requested_by="auditor",
        reason="retention-test",
    )
    replayed = service.generate_multilingual_walkthrough(**request)

    assert replayed.multilingual_run_id == result.multilingual_run_id
    assert replayed.voice.audio_artifact is None
    assert replayed.artifacts.voice_audio is None
    assert len(transport.calls) == 1


def test_restore_warning_redacts_poisoned_state_values(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    state_path = tmp_path / "stage6.json"
    secret_like_value = "api" + "_key=" + "visible" + "-secret-token-value"
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage6-local-state-v2",
                "multilingualRuns": [],
                "requestDedupeIndex": [],
                "idempotencyRecords": [
                    {
                        "idempotency_scope": "tenant:user:project:run",
                        "endpoint": "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
                        "idempotency_key": "poisoned",
                        "request_checksum": "sha256:test",
                        "status": secret_like_value,
                        "value": {"kind": "none"},
                    }
                ],
                "counters": {"run": 0},
            }
        ),
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING, logger="backend.app.stage6"):
        create_stage6_service(state_path=state_path)

    assert caplog.records
    assert secret_like_value not in caplog.text
    assert "visible-secret-token-value" not in caplog.text
    assert "Stage 6 idempotency record" in caplog.text


def test_concurrent_duplicate_idempotency_key_is_rejected_in_flight() -> None:
    class SlowTranslationProvider:
        provider = "slow-local"
        provider_mode = "LOCAL"

        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()
            self.call_count = 0
            self.lock = threading.Lock()

        def translate(
            self,
            *,
            source_text: str,
            source_language: str,
            target_language: str,
            glossary_terms: list[str],
        ) -> TranslationProviderResult:
            with self.lock:
                self.call_count += 1
            self.entered.set()
            assert self.release.wait(timeout=2)
            return TranslationProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                source_language=source_language,
                target_language=target_language,
                translated_text=translate_demo_source_text(
                    source_text=source_text,
                    target_language=target_language,
                ),
                preserved_terms=glossary_terms,
            )

    provider = SlowTranslationProvider()
    service = create_stage6_service()
    service.translation_provider = provider
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def generate() -> None:
        try:
            result = service.generate_multilingual_walkthrough(
                source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
                target_language="es",
                glossary_terms=["NarraTwin AI"],
                idempotency_scope="tenant:user:project:run",
                idempotency_key="same-key",
                **passed_eval_kwargs(),
            )
            value = result.multilingual_run_id
        except Stage6Error as exc:
            value = exc.code
        with outcomes_lock:
            outcomes.append(value)

    first = threading.Thread(target=generate)
    second = threading.Thread(target=generate)
    first.start()
    assert provider.entered.wait(timeout=2)
    second.start()
    second.join(timeout=2)
    provider.release.set()
    first.join(timeout=2)

    assert sorted(outcomes) == ["IDEMPOTENCY_IN_PROGRESS", "mlrun_000001"]
    assert provider.call_count == 1


def test_reused_idempotency_key_with_changed_payload_conflicts() -> None:
    service = create_stage6_service()
    first = service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        idempotency_scope="tenant:user:project:run",
        idempotency_key="same-key",
        **passed_eval_kwargs(),
    )

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="fr",
            glossary_terms=["NarraTwin AI"],
            idempotency_scope="tenant:user:project:run",
            idempotency_key="same-key",
            **passed_eval_kwargs(),
        )

    assert first.multilingual_run_id == "mlrun_000001"
    assert exc.value.status_code == 409
    assert exc.value.code == "IDEMPOTENCY_CONFLICT"


def test_provider_output_must_preserve_glossary_terms_present_in_source() -> None:
    class DroppingTranslationProvider:
        provider = "dropping-local"
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
                translated_text="Producto traducido sin el nombre requerido.",
                preserved_terms=[],
            )

    service = create_stage6_service()
    service.translation_provider = DroppingTranslationProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            **passed_eval_kwargs(),
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_output_must_preserve_source_citation_markers() -> None:
    class CitationDroppingTranslationProvider:
        provider = "citation-dropping-local"
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
                translated_text="Guion traducido sin marcador.",
                preserved_terms=glossary_terms,
            )

    service = create_stage6_service()
    service.translation_provider = CitationDroppingTranslationProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            source_context_ref_count=1,
            source_citation_count=1,
            source_context_ref_ids=("ctx_001",),
            source_citation_indexes=(1,),
            source_claim_support_ids=("claimsup_001",),
            source_evaluation_id="eval_001",
            source_evaluation_checksum=build_source_evaluation_checksum(
                source_evaluation_id="eval_001",
                source_run_id="local_source_run",
                trace_id="local_trace",
                evaluation_status="PASSED",
                source_context_ref_ids=("ctx_001",),
                source_context_ref_count=1,
                source_citation_indexes=(1,),
                source_citation_count=1,
            ),
            evaluation_status="PASSED",
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_output_must_not_exceed_stage6_size_limit() -> None:
    class OversizedTranslationProvider:
        provider = "oversized-local"
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
                translated_text="x" * 20_001,
                preserved_terms=glossary_terms,
            )

    service = create_stage6_service()
    service.translation_provider = OversizedTranslationProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
            **passed_eval_kwargs(),
        )

    assert exc.value.status_code == 413
    assert exc.value.code == "PROVIDER_OUTPUT_TOO_LARGE"


def test_tts_provider_output_must_be_a_valid_json_manifest_artifact() -> None:
    class InvalidTTSProvider:
        provider = "invalid-local"
        provider_mode = "LOCAL"

        def synthesize(
            self,
            *,
            text: str,
            language: str,
            requested_provider: str,
            fallback_reason: str | None,
        ) -> VoiceProviderResult:
            return VoiceProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                language=language,
                artifact=DownloadableArtifact(
                    file_name="../voice.wav",
                    mime_type="audio/wav",
                    content_base64=base64.b64encode(b"not-json").decode("ascii"),
                    checksum="sha256:not-the-content",
                ),
            )

    service = create_stage6_service()
    service.tts_provider = InvalidTTSProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_tts_provider_manifest_rejects_unknown_schema_fields() -> None:
    class ExtraFieldTTSProvider:
        provider = "mock"
        provider_mode = "LOCAL"

        def synthesize(
            self,
            *,
            text: str,
            language: str,
            requested_provider: str,
            fallback_reason: str | None,
        ) -> VoiceProviderResult:
            manifest = {
                "provider": self.provider,
                "providerMode": self.provider_mode,
                "language": language,
                "languageDisplayName": "Spanish",
                "textChecksum": checksum_text(text),
                "durationSecondsEstimate": 2.0,
                "mockAudioProfile": {
                    "durationMillisecondsEstimate": 2000,
                    "sampleRateHz": 16000,
                    "channels": 1,
                    "unexpectedNested": "value",
                },
                "disclosure": "Mock local TTS placeholder. No cloned voice or paid provider was used.",
                "unexpectedTopLevel": "value",
            }
            decoded = json.dumps(manifest, sort_keys=True)
            return VoiceProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                language=language,
                artifact=DownloadableArtifact(
                    file_name="voice-manifest-es.json",
                    mime_type="application/json",
                    content_base64=base64.b64encode(decoded.encode("utf-8")).decode("ascii"),
                    checksum=checksum_text(decoded),
                ),
            )

    service = create_stage6_service()
    service.tts_provider = ExtraFieldTTSProvider()

    with pytest.raises(Stage6Error) as exc:
        service.generate_multilingual_walkthrough(
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_caption_splitting_bounds_single_long_tokens() -> None:
    captions = split_captions("https://example.com/" + ("a" * 180))

    assert captions
    assert all(len(caption) <= MAX_CAPTION_CHARS for caption in captions)


def test_unsupported_language_is_rejected_cleanly() -> None:
    with pytest.raises(Stage6Error) as exc:
        normalize_language_tag("tlh")

    assert exc.value.status_code == 422
    assert exc.value.code == "UNSUPPORTED_LANGUAGE"
    assert "Unsupported target language" in exc.value.message


def test_local_demo_translation_refuses_arbitrary_cited_source_without_fixture() -> None:
    with pytest.raises(Stage6Error) as exc:
        translate_demo_source_text(
            source_text="For reviewers, NarraTwin AI acquired Jupiter Labs for moon-base onboarding. [1]",
            target_language="es",
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "LOCAL_DEMO_TRANSLATION_UNSUPPORTED"
