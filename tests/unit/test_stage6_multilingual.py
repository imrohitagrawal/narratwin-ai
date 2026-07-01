import base64
import json
import threading
from datetime import timedelta

import pytest
import srt  # type: ignore[import-untyped]

from backend.app.stage6 import (
    DownloadableArtifact,
    MAX_CAPTION_CHARS,
    Stage6Error,
    TranslationProviderResult,
    VoiceProviderResult,
    create_stage6_service,
    generate_subtitles,
    normalize_language_tag,
    split_captions,
)

# Stage 6 multilingual tests preserve source run_id trace metadata and citation
# counts from the accepted grounded walkthrough script.


def test_translation_preserves_project_terms_from_glossary() -> None:
    service = create_stage6_service()
    source_script = (
        "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. "
        "NarraTwin AI keeps generated claims tied to source chunks."
    )

    result = service.generate_multilingual_walkthrough(
        source_script=source_script,
        target_language="es",
        glossary_terms=["NarraTwin AI", "project knowledge", "source chunks"],
        requested_voice_provider="mock",
    )

    assert result.target_language == "es"
    assert "NarraTwin AI" in result.translated_script_text
    assert "project knowledge" in result.translated_script_text
    assert "source chunks" in result.translated_script_text
    assert "convierte" in result.translated_script_text
    assert result.translated_script_text != source_script


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
        source_script="NarraTwin AI creates grounded walkthrough scripts.",
        target_language="fr",
        glossary_terms=["NarraTwin AI"],
        requested_voice_provider="external",
    )

    assert result.voice.provider == "mock"
    assert result.voice.requested_provider == "external"
    assert result.voice.fallback_reason == "REQUESTED_PROVIDER_UNAVAILABLE"
    assert result.voice.provider_mode == "LOCAL"
    assert result.voice.artifact.content_base64
    manifest = json.loads(base64.b64decode(result.voice.artifact.content_base64).decode("utf-8"))
    assert manifest["languageDisplayName"] == "French"
    assert manifest["mockAudioProfile"]["sampleRateHz"] == 16000


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
                translated_text=source_text,
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
                source_script="NarraTwin AI creates grounded walkthrough scripts.",
                target_language="es",
                glossary_terms=["NarraTwin AI"],
                idempotency_scope="tenant:user:project:run",
                idempotency_key="same-key",
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
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
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
            source_script="NarraTwin AI creates grounded walkthrough scripts.",
            target_language="es",
            glossary_terms=["NarraTwin AI"],
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
