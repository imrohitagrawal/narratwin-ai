"""Stage 6 multilingual walkthrough generation with mock/local providers."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import threading
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import langcodes
from babel import Locale
from pydub import AudioSegment  # type: ignore[import-untyped]
import srt  # type: ignore[import-untyped]

from backend.app.rag.chunking import checksum_text
from backend.app.storage import load_state, resolve_state_file, write_state
from backend.app.stage4 import contains_secret_like_content

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "hi": "Hindi",
}
MAX_GLOSSARY_TERMS = 25
MAX_GLOSSARY_TERM_CHARS = 80
MAX_SOURCE_SCRIPT_CHARS = 20_000
MAX_CAPTION_CHARS = 96
MAX_CAPTION_COUNT = 250
MAX_PROVIDER_ID_CHARS = 64
MAX_IDEMPOTENCY_RECORDS_PER_SCOPE = 100
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
LOGGER = logging.getLogger(__name__)
VOICE_MANIFEST_KEYS = frozenset(
    {
        "provider",
        "providerMode",
        "language",
        "languageDisplayName",
        "textChecksum",
        "durationSecondsEstimate",
        "mockAudioProfile",
        "disclosure",
    }
)
MOCK_AUDIO_PROFILE_KEYS = frozenset({"durationMillisecondsEstimate", "sampleRateHz", "channels"})
ProviderMode = Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"]


class Stage6Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DownloadableArtifact:
    file_name: str
    mime_type: str
    content_base64: str
    checksum: str


@dataclass(frozen=True)
class TranslationProviderResult:
    provider: str
    provider_mode: str
    source_language: str
    target_language: str
    translated_text: str
    preserved_terms: list[str]


@dataclass(frozen=True)
class VoiceProviderResult:
    provider: str
    provider_mode: str
    requested_provider: str
    fallback_reason: str | None
    language: str
    artifact: DownloadableArtifact


@dataclass(frozen=True)
class MultilingualArtifacts:
    translated_script: DownloadableArtifact
    subtitles: DownloadableArtifact
    voice_manifest: DownloadableArtifact


@dataclass(frozen=True)
class MultilingualWalkthroughResult:
    multilingual_run_id: str
    source_run_id: str
    source_language: str
    target_language: str
    status: str
    source_script_text: str
    translated_script_text: str
    subtitles_text: str
    glossary_terms: list[str]
    preserved_terms: list[str]
    translation_provider: TranslationProviderResult
    voice: VoiceProviderResult
    artifacts: MultilingualArtifacts
    trace_id: str
    source_context_ref_count: int
    source_citation_count: int


@dataclass
class Stage6IdempotencyRecord:
    idempotency_scope: str
    endpoint: str
    idempotency_key: str
    request_checksum: str
    status: Literal["PENDING", "COMPLETED", "FAILED"]
    value: MultilingualWalkthroughResult | Stage6Error | None


class TranslationProvider(Protocol):
    provider: str
    provider_mode: str

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        glossary_terms: list[str],
    ) -> TranslationProviderResult:
        ...


class TTSProvider(Protocol):
    provider: str
    provider_mode: str

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        requested_provider: str,
        fallback_reason: str | None,
    ) -> VoiceProviderResult:
        ...


class MockTranslationProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    _REPLACEMENTS = {
        "es": (
            ("turns", "convierte"),
            ("approved", "aprobado"),
            ("into", "en"),
            ("grounded", "fundamentados"),
            ("walkthrough scripts", "guiones de recorrido"),
            ("keeps", "mantiene"),
            ("generated claims", "afirmaciones generadas"),
            ("tied to", "vinculadas a"),
            ("creates", "crea"),
            ("every", "cada"),
            ("must cite", "debe citar"),
        ),
        "fr": (
            ("turns", "transforme"),
            ("approved", "approuve"),
            ("into", "en"),
            ("grounded", "ancres"),
            ("walkthrough scripts", "scripts de presentation"),
            ("keeps", "garde"),
            ("generated claims", "affirmations generees"),
            ("tied to", "liees a"),
            ("creates", "cree"),
            ("every", "chaque"),
            ("must cite", "doit citer"),
        ),
        "hi": (
            ("turns", "badalta hai"),
            ("approved", "sweekrit"),
            ("into", "mein"),
            ("grounded", "aadharrit"),
            ("walkthrough scripts", "walkthrough scripts"),
            ("keeps", "rakhta hai"),
            ("generated claims", "generated claims"),
            ("tied to", "se juda"),
            ("creates", "banata hai"),
            ("every", "har"),
            ("must cite", "cite karna chahiye"),
        ),
    }

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        glossary_terms: list[str],
    ) -> TranslationProviderResult:
        if target_language == source_language:
            translated = source_text
        else:
            protected, placeholders = protect_terms(source_text, glossary_terms)
            translated = protected
            for source, target in self._REPLACEMENTS.get(target_language, ()):
                translated = re.sub(rf"\b{re.escape(source)}\b", target, translated, flags=re.IGNORECASE)
            translated = restore_terms(translated, placeholders)
        return TranslationProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated,
            preserved_terms=[term for term in glossary_terms if term in translated],
        )


class MockTTSProvider:
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
            "languageDisplayName": language_display_name(language),
            "textChecksum": checksum_text(text),
            "durationSecondsEstimate": estimate_duration_seconds(text),
            "mockAudioProfile": mock_audio_profile(estimate_duration_seconds(text)),
            "disclosure": "Mock local TTS placeholder. No cloned voice or paid provider was used.",
        }
        return VoiceProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            requested_provider=requested_provider,
            fallback_reason=fallback_reason,
            language=language,
            artifact=artifact_from_text(
                file_name=f"voice-manifest-{language}.json",
                mime_type="application/json",
                text=json.dumps(manifest, sort_keys=True),
            ),
        )


class Stage6Service:
    def __init__(
        self,
        *,
        translation_provider: TranslationProvider | None = None,
        tts_provider: TTSProvider | None = None,
        state_path: Path | None = None,
    ) -> None:
        self.translation_provider = translation_provider or MockTranslationProvider()
        self.tts_provider = tts_provider or MockTTSProvider()
        self.state_path = state_path
        self.idempotency_records: dict[tuple[str, str, str], Stage6IdempotencyRecord] = {}
        self._operation_lock = threading.Lock()
        self._run_counter = 0
        self._restore()

    def reset(self) -> None:
        with self._operation_lock:
            self.translation_provider = MockTranslationProvider()
            self.tts_provider = MockTTSProvider()
            self._clear_runtime_state()
            self._persist_locked()

    def _clear_runtime_state(self) -> None:
        self.idempotency_records.clear()
        self._run_counter = 0

    def _restore(self) -> None:
        payload = load_state(self.state_path)
        if payload is None:
            return
        try:
            if payload.get("schema") != "stage6-local-state-v1":
                raise ValueError("Stage 6 state schema mismatch.")
            counters = payload.get("counters", {})
            run_counter = 0
            if isinstance(counters, dict):
                run_counter = int(counters.get("run", 0))
            for row in payload.get("idempotencyRecords", []):
                if not isinstance(row, dict):
                    continue
                if row.get("status") == "PENDING":
                    continue
                try:
                    record = stage6_idempotency_record_from_dict(row)
                except (KeyError, TypeError, ValueError, Stage6Error) as exc:
                    LOGGER.warning("Skipping incompatible Stage 6 idempotency record at %s: %s", self.state_path, exc)
                    continue
                key = (record.idempotency_scope, record.endpoint, record.idempotency_key)
                self.idempotency_records[key] = record
            self._run_counter = max(run_counter, max_multilingual_run_suffix(self.idempotency_records))
        except (KeyError, TypeError, ValueError, Stage6Error) as exc:
            LOGGER.warning("Ignoring incompatible Stage 6 local state snapshot at %s: %s", self.state_path, exc)
            self._clear_runtime_state()

    def _runtime_snapshot_locked(self) -> dict[str, Any]:
        return {
            "idempotencyRecords": self.idempotency_records.copy(),
            "runCounter": self._run_counter,
        }

    def _restore_runtime_snapshot_locked(self, snapshot: dict[str, Any]) -> None:
        self.idempotency_records = snapshot["idempotencyRecords"].copy()
        self._run_counter = int(snapshot["runCounter"])

    def _restore_failed_operation_locked(
        self,
        snapshot: dict[str, Any] | None,
        *,
        record_key: tuple[str, str, str] | None,
        result: MultilingualWalkthroughResult | None,
    ) -> None:
        if snapshot is None:
            return
        if record_key is not None:
            prior_record = snapshot["idempotencyRecords"].get(record_key)
            if prior_record is None:
                self.idempotency_records.pop(record_key, None)
            else:
                self.idempotency_records[record_key] = prior_record
        if result is not None:
            for key, record in list(self.idempotency_records.items()):
                if (
                    key != record_key
                    and isinstance(record.value, MultilingualWalkthroughResult)
                    and record.value.multilingual_run_id == result.multilingual_run_id
                ):
                    self.idempotency_records.pop(key, None)
        self._run_counter = max(
            int(snapshot["runCounter"]),
            max_multilingual_run_suffix(self.idempotency_records),
        )

    def _persist_locked(self) -> None:
        write_state(
            self.state_path,
            {
                "schema": "stage6-local-state-v1",
                "idempotencyRecords": [
                    stage6_idempotency_record_to_dict(record)
                    for record in self.idempotency_records.values()
                    if record.status != "PENDING"
                ],
                "counters": {"run": self._run_counter},
            },
        )

    def generate_multilingual_walkthrough(
        self,
        *,
        source_script: str,
        target_language: str,
        glossary_terms: Iterable[str] = (),
        source_language: str = "en",
        requested_voice_provider: str = "mock",
        source_run_id: str = "local_source_run",
        trace_id: str = "local_trace",
        source_context_ref_count: int = 0,
        idempotency_scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> MultilingualWalkthroughResult:
        raw_glossary_terms = list(glossary_terms)
        request_checksum = checksum_text(
            json.dumps(
                {
                    "sourceScript": source_script,
                    "sourceLanguage": source_language,
                    "targetLanguage": target_language,
                    "requestedVoiceProvider": requested_voice_provider,
                    "glossaryTerms": raw_glossary_terms,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        endpoint = "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
        record_key: tuple[str, str, str] | None = None
        snapshot: dict[str, Any] | None = None
        result: MultilingualWalkthroughResult | None = None
        if idempotency_scope and idempotency_key:
            record_key = (idempotency_scope, endpoint, idempotency_key)
            with self._operation_lock:
                existing = self.idempotency_records.get(record_key)
                if existing is not None:
                    if existing.request_checksum != request_checksum:
                        raise Stage6Error(
                            409,
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency key was reused with a different request.",
                        )
                    if existing.status == "PENDING":
                        raise Stage6Error(
                            409,
                            "IDEMPOTENCY_IN_PROGRESS",
                            "Idempotency key is already in progress.",
                        )
                    if existing.status == "FAILED":
                        raise cast(Stage6Error, existing.value)
                    return cast(MultilingualWalkthroughResult, existing.value)
                if self._idempotency_count_for_scope(idempotency_scope) >= MAX_IDEMPOTENCY_RECORDS_PER_SCOPE:
                    raise Stage6Error(
                        429,
                        "RESOURCE_LIMIT_EXCEEDED",
                        "Idempotency record limit exceeded for this Stage 6 scope.",
                    )
                snapshot = self._runtime_snapshot_locked()
                self.idempotency_records[record_key] = Stage6IdempotencyRecord(
                    idempotency_scope=idempotency_scope,
                    endpoint=endpoint,
                    idempotency_key=idempotency_key,
                    request_checksum=request_checksum,
                    status="PENDING",
                    value=None,
                )

        try:
            normalized_source_language = normalize_language_tag(source_language)
            normalized_target_language = normalize_language_tag(target_language)
            normalized_terms = normalize_glossary_terms(raw_glossary_terms)
            if any(contains_secret_like_content(term) for term in normalized_terms):
                raise Stage6Error(422, "SECRET_LIKE_CONTENT", "Glossary terms contain secret-like content.")
            source_text = source_script.strip()
            if not source_text:
                raise Stage6Error(422, "VALIDATION_ERROR", "Source English script is required.")
            if len(source_text) > MAX_SOURCE_SCRIPT_CHARS:
                raise Stage6Error(413, "SOURCE_SCRIPT_TOO_LARGE", "Source English script exceeds the Stage 6 limit.")
        except Stage6Error as exc:
            if record_key is not None:
                self._store_idempotent_failure(record_key, exc, snapshot)
            raise

        try:
            result = self._create_multilingual_walkthrough(
                source_text=source_text,
                normalized_source_language=normalized_source_language,
                normalized_target_language=normalized_target_language,
                normalized_terms=normalized_terms,
                requested_voice_provider=requested_voice_provider,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
            )
        except Stage6Error as exc:
            if record_key is not None:
                self._store_idempotent_failure(record_key, exc, snapshot)
            raise
        except OSError:
            if snapshot is not None:
                with self._operation_lock:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
            raise
        except Exception:
            if record_key is not None:
                with self._operation_lock:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
                    self._persist_locked()
            raise
        assert result is not None
        if record_key is not None:
            with self._operation_lock:
                record = self.idempotency_records[record_key]
                record.status = "COMPLETED"
                record.value = result
                try:
                    self._persist_locked()
                except OSError:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
                    raise
        return result

    def _store_idempotent_failure(
        self,
        record_key: tuple[str, str, str],
        error: Stage6Error,
        snapshot: dict[str, Any] | None,
    ) -> None:
        with self._operation_lock:
            record = self.idempotency_records[record_key]
            record.status = "FAILED"
            record.value = error
            try:
                self._persist_locked()
            except OSError:
                self._restore_failed_operation_locked(snapshot, record_key=record_key, result=None)
                raise error

    def _create_multilingual_walkthrough(
        self,
        *,
        source_text: str,
        normalized_source_language: str,
        normalized_target_language: str,
        normalized_terms: list[str],
        requested_voice_provider: str,
        source_run_id: str,
        trace_id: str,
        source_context_ref_count: int,
    ) -> MultilingualWalkthroughResult:
        translation = self.translation_provider.translate(
            source_text=source_text,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            glossary_terms=normalized_terms,
        )
        validated_text, preserved_terms, citation_count = validate_translation_output(
            source_text=source_text,
            translated_text=translation.translated_text,
            glossary_terms=normalized_terms,
        )
        translation = TranslationProviderResult(
            provider=validate_provider_id(translation.provider, field_name="translation provider"),
            provider_mode=validate_provider_mode(translation.provider_mode),
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            translated_text=validated_text,
            preserved_terms=preserved_terms,
        )
        subtitles_text = generate_subtitles(
            script_text=translation.translated_text,
            language=normalized_target_language,
        )
        provider_name, fallback_reason = resolve_voice_provider(requested_voice_provider)
        voice = self.tts_provider.synthesize(
            text=translation.translated_text,
            language=normalized_target_language,
            requested_provider=provider_name,
            fallback_reason=fallback_reason,
        )
        voice = VoiceProviderResult(
            provider=validate_provider_id(voice.provider, field_name="voice provider"),
            provider_mode=validate_provider_mode(voice.provider_mode),
            requested_provider=provider_name,
            fallback_reason=voice.fallback_reason,
            language=normalized_target_language,
            artifact=validate_voice_manifest_artifact(voice.artifact),
        )
        with self._operation_lock:
            self._run_counter += 1
            multilingual_run_id = f"mlrun_{self._run_counter:06d}"
        script_artifact = artifact_from_text(
            file_name=f"{source_run_id}-{normalized_target_language}-script.md",
            mime_type="text/markdown",
            text=translation.translated_text,
        )
        subtitle_artifact = artifact_from_text(
            file_name=f"{source_run_id}-{normalized_target_language}.srt",
            mime_type="application/x-subrip",
            text=subtitles_text,
        )
        return MultilingualWalkthroughResult(
            multilingual_run_id=multilingual_run_id,
            source_run_id=source_run_id,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            status="COMPLETED",
            source_script_text=source_text,
            translated_script_text=translation.translated_text,
            subtitles_text=subtitles_text,
            glossary_terms=normalized_terms,
            preserved_terms=translation.preserved_terms,
            translation_provider=translation,
            voice=voice,
            artifacts=MultilingualArtifacts(
                translated_script=script_artifact,
                subtitles=subtitle_artifact,
                voice_manifest=voice.artifact,
            ),
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=citation_count,
        )

    def _idempotency_count_for_scope(self, idempotency_scope: str) -> int:
        return sum(record.idempotency_scope == idempotency_scope for record in self.idempotency_records.values())


def stage6_idempotency_record_to_dict(record: Stage6IdempotencyRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "idempotency_scope": record.idempotency_scope,
        "endpoint": record.endpoint,
        "idempotency_key": record.idempotency_key,
        "request_checksum": record.request_checksum,
        "status": record.status,
    }
    if isinstance(record.value, Stage6Error):
        row["value"] = {
            "kind": "error",
            "status_code": record.value.status_code,
            "code": record.value.code,
            "message": record.value.message,
        }
    elif isinstance(record.value, MultilingualWalkthroughResult):
        row["value"] = {"kind": "result", "result": multilingual_result_to_dict(record.value)}
    else:
        row["value"] = {"kind": "none"}
    return row


def stage6_idempotency_record_from_dict(row: dict[str, Any]) -> Stage6IdempotencyRecord:
    value_ref = row.get("value", {})
    value: MultilingualWalkthroughResult | Stage6Error | None = None
    if isinstance(value_ref, dict):
        if value_ref.get("kind") == "error":
            value = Stage6Error(
                int(value_ref.get("status_code", 500)),
                str(value_ref.get("code", "INTERNAL_SERVER_ERROR")),
                str(value_ref.get("message", "Request failed.")),
            )
        elif value_ref.get("kind") == "result" and isinstance(value_ref.get("result"), dict):
            value = multilingual_result_from_dict(cast(dict[str, Any], value_ref["result"]))
    status = str(row["status"])
    if status not in {"PENDING", "COMPLETED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 6 idempotency status: {status}")
    if status == "COMPLETED" and value is None:
        raise ValueError("Completed Stage 6 idempotency record references missing value.")
    if status == "FAILED" and not isinstance(value, Stage6Error):
        raise ValueError("Failed Stage 6 idempotency record references missing error.")
    return Stage6IdempotencyRecord(
        idempotency_scope=str(row["idempotency_scope"]),
        endpoint=str(row["endpoint"]),
        idempotency_key=str(row["idempotency_key"]),
        request_checksum=str(row["request_checksum"]),
        status=cast(Literal["PENDING", "COMPLETED", "FAILED"], status),
        value=value,
    )


def max_multilingual_run_suffix(records: dict[tuple[str, str, str], Stage6IdempotencyRecord]) -> int:
    maximum = 0
    for record in records.values():
        if not isinstance(record.value, MultilingualWalkthroughResult):
            continue
        identifier = record.value.multilingual_run_id
        if not identifier.startswith("mlrun_"):
            continue
        try:
            maximum = max(maximum, int(identifier.removeprefix("mlrun_")))
        except ValueError:
            continue
    return maximum


def multilingual_result_to_dict(result: MultilingualWalkthroughResult) -> dict[str, Any]:
    return asdict(result)


def multilingual_result_from_dict(row: dict[str, Any]) -> MultilingualWalkthroughResult:
    artifacts = cast(dict[str, Any], row["artifacts"])
    voice = cast(dict[str, Any], row["voice"])
    translation_provider = cast(dict[str, Any], row["translation_provider"])
    source_language = normalize_language_tag(str(row["source_language"]))
    target_language = normalize_language_tag(str(row["target_language"]))
    status = str(row["status"])
    if status != "COMPLETED":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 result status is invalid.")
    translation_provider_id = validate_provider_id(
        str(translation_provider["provider"]),
        field_name="translation provider",
    )
    translation_provider_mode = validate_local_provider_mode(
        str(translation_provider["provider_mode"]),
        field_name="translation provider mode",
    )
    voice_provider_id = validate_provider_id(str(voice["provider"]), field_name="voice provider")
    voice_provider_mode = validate_local_provider_mode(str(voice["provider_mode"]), field_name="voice provider mode")
    requested_voice_provider = validate_provider_id(str(voice["requested_provider"]), field_name="requested voice provider")
    fallback_reason = validate_voice_fallback_reason(
        str(voice["fallback_reason"]) if voice.get("fallback_reason") is not None else None
    )
    if translation_provider_id != "mock" or voice_provider_id != "mock":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 provider must be mock local.")
    voice_artifact = validate_voice_manifest_artifact(
        downloadable_artifact_from_dict(
            cast(dict[str, Any], voice["artifact"]),
            expected_mime_type="application/json",
            expected_extension=".json",
        )
    )
    translated_script_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], artifacts["translated_script"]),
        expected_mime_type="text/markdown",
        expected_extension=".md",
    )
    subtitles_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], artifacts["subtitles"]),
        expected_mime_type="application/x-subrip",
        expected_extension=".srt",
    )
    translated_script_text = str(row["translated_script_text"])
    subtitles_text = str(row["subtitles_text"])
    provider_translated_text = str(translation_provider["translated_text"])
    if translated_script_text != provider_translated_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 translated text is inconsistent.")
    if artifact_text(translated_script_artifact) != translated_script_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 script artifact is inconsistent.")
    if artifact_text(subtitles_artifact) != subtitles_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 subtitle artifact is inconsistent.")
    if subtitles_text != generate_subtitles(script_text=translated_script_text, language=target_language):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 subtitles are inconsistent.")
    voice_manifest = json.loads(artifact_text(voice_artifact))
    if (
        normalize_language_tag(str(translation_provider["source_language"])) != source_language
        or normalize_language_tag(str(translation_provider["target_language"])) != target_language
        or normalize_language_tag(str(voice["language"])) != target_language
        or str(voice_manifest["textChecksum"]) != checksum_text(translated_script_text)
        or normalize_language_tag(str(voice_manifest["language"])) != target_language
        or str(voice_manifest["provider"]) != voice_provider_id
        or validate_local_provider_mode(str(voice_manifest["providerMode"]), field_name="voice manifest provider mode")
        != voice_provider_mode
    ):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 voice manifest is inconsistent.")
    return MultilingualWalkthroughResult(
        multilingual_run_id=str(row["multilingual_run_id"]),
        source_run_id=str(row["source_run_id"]),
        source_language=source_language,
        target_language=target_language,
        status=status,
        source_script_text=str(row["source_script_text"]),
        translated_script_text=translated_script_text,
        subtitles_text=subtitles_text,
        glossary_terms=[str(term) for term in row.get("glossary_terms", [])],
        preserved_terms=[str(term) for term in row.get("preserved_terms", [])],
        translation_provider=TranslationProviderResult(
            provider=translation_provider_id,
            provider_mode=translation_provider_mode,
            source_language=normalize_language_tag(str(translation_provider["source_language"])),
            target_language=normalize_language_tag(str(translation_provider["target_language"])),
            translated_text=provider_translated_text,
            preserved_terms=[str(term) for term in translation_provider.get("preserved_terms", [])],
        ),
        voice=VoiceProviderResult(
            provider=voice_provider_id,
            provider_mode=voice_provider_mode,
            requested_provider=requested_voice_provider,
            fallback_reason=fallback_reason,
            language=normalize_language_tag(str(voice["language"])),
            artifact=voice_artifact,
        ),
        artifacts=MultilingualArtifacts(
            translated_script=translated_script_artifact,
            subtitles=subtitles_artifact,
            voice_manifest=voice_artifact,
        ),
        trace_id=str(row["trace_id"]),
        source_context_ref_count=int(row["source_context_ref_count"]),
        source_citation_count=int(row["source_citation_count"]),
    )


def artifact_text(artifact: DownloadableArtifact) -> str:
    try:
        return base64.b64decode(artifact.content_base64, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact content is invalid.") from exc


def downloadable_artifact_from_dict(
    row: dict[str, Any],
    *,
    expected_mime_type: str,
    expected_extension: str,
) -> DownloadableArtifact:
    artifact = DownloadableArtifact(
        file_name=str(row["file_name"]),
        mime_type=str(row["mime_type"]),
        content_base64=str(row["content_base64"]),
        checksum=str(row["checksum"]),
    )
    return validate_downloadable_artifact(
        artifact,
        expected_mime_type=expected_mime_type,
        expected_extension=expected_extension,
    )


def create_stage6_service(*, state_path: Path | None = None) -> Stage6Service:
    return Stage6Service(state_path=state_path)


def normalize_language_tag(language: str) -> str:
    raw_language = language.strip()
    if not raw_language:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.")
    try:
        normalized = langcodes.standardize_tag(raw_language)
        base_language = langcodes.Language.get(normalized).language
    except (LookupError, ValueError) as exc:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.") from exc
    if base_language not in SUPPORTED_LANGUAGES:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.")
    return base_language


def normalize_glossary_terms(terms: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for term in terms:
        candidate = " ".join(term.strip().split())
        if not candidate:
            raise Stage6Error(422, "VALIDATION_ERROR", "Glossary terms must not be blank.")
        if len(candidate) > MAX_GLOSSARY_TERM_CHARS:
            raise Stage6Error(422, "VALIDATION_ERROR", "Glossary term exceeds the Stage 6 limit.")
        if candidate not in normalized:
            normalized.append(candidate)
        if len(normalized) > MAX_GLOSSARY_TERMS:
            raise Stage6Error(422, "VALIDATION_ERROR", "Too many glossary terms for Stage 6.")
    return normalized


def validate_translation_output(
    *,
    source_text: str,
    translated_text: str,
    glossary_terms: list[str],
) -> tuple[str, list[str], int]:
    cleaned = translated_text.strip()
    if not cleaned:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider returned empty output.")
    if len(cleaned) > MAX_SOURCE_SCRIPT_CHARS:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", "Translation provider output exceeds the Stage 6 limit.")

    missing_terms = [term for term in glossary_terms if term in source_text and term not in cleaned]
    if missing_terms:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider did not preserve required glossary terms.")

    source_markers = citation_markers(source_text)
    translated_markers = citation_markers(cleaned)
    if not source_markers.issubset(translated_markers):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider did not preserve citation markers.")

    return cleaned, [term for term in glossary_terms if term in cleaned], len(source_markers)


def citation_markers(text: str) -> set[str]:
    return set(re.findall(r"\[(\d+)\]", text))


def validate_provider_id(provider: str, *, field_name: str) -> str:
    candidate = provider.strip().lower()
    if not PROVIDER_ID_PATTERN.fullmatch(candidate):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name} identifier.")
    return candidate


def validate_provider_mode(provider_mode: str) -> ProviderMode:
    candidate = provider_mode.strip().upper()
    if candidate not in {"LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"}:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider mode.")
    return cast(ProviderMode, candidate)


def validate_local_provider_mode(provider_mode: str, *, field_name: str) -> ProviderMode:
    candidate = validate_provider_mode(provider_mode)
    if candidate != "LOCAL":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"{field_name} must be local.")
    return candidate


def validate_voice_fallback_reason(fallback_reason: str | None) -> str | None:
    if fallback_reason is None:
        return None
    candidate = fallback_reason.strip().upper()
    if candidate != "REQUESTED_PROVIDER_UNAVAILABLE":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid voice provider fallback reason.")
    return candidate


def validate_downloadable_artifact(
    artifact: DownloadableArtifact,
    *,
    expected_mime_type: str,
    expected_extension: str,
) -> DownloadableArtifact:
    if artifact.mime_type != expected_mime_type:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact MIME type is invalid.")
    if not artifact.file_name.endswith(expected_extension) or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact filename is invalid.")
    try:
        decoded = base64.b64decode(artifact.content_base64, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact content is invalid.") from exc
    if artifact.checksum != checksum_text(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact checksum is invalid.")
    return artifact


def validate_voice_manifest_artifact(artifact: DownloadableArtifact) -> DownloadableArtifact:
    if artifact.mime_type != "application/json":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact must be a JSON manifest.")
    if not artifact.file_name.endswith(".json") or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact filename is invalid.")
    try:
        decoded = base64.b64decode(artifact.content_base64, validate=True).decode("utf-8")
        parsed = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact must contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest must be a JSON object.")
    if set(parsed) != VOICE_MANIFEST_KEYS:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest schema is invalid.")
    if parsed["provider"] != "mock":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest provider is invalid.")
    validate_provider_mode(str(parsed["providerMode"]))
    normalize_language_tag(str(parsed["language"]))
    if not isinstance(parsed["languageDisplayName"], str) or not parsed["languageDisplayName"].strip():
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest language display name is invalid.")
    if not isinstance(parsed["textChecksum"], str) or not parsed["textChecksum"].startswith("sha256:"):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest text checksum is invalid.")
    duration_estimate = parsed["durationSecondsEstimate"]
    if not isinstance(duration_estimate, int | float) or duration_estimate <= 0:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest duration is invalid.")
    audio_profile = parsed["mockAudioProfile"]
    if not isinstance(audio_profile, dict) or set(audio_profile) != MOCK_AUDIO_PROFILE_KEYS:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio profile schema is invalid.")
    if audio_profile["sampleRateHz"] != 16000 or audio_profile["channels"] != 1:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio profile is invalid.")
    profile_duration = audio_profile["durationMillisecondsEstimate"]
    if not isinstance(profile_duration, int) or profile_duration <= 0:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio duration is invalid.")
    if not isinstance(parsed["disclosure"], str) or "Mock local TTS placeholder" not in parsed["disclosure"]:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest disclosure is invalid.")
    if artifact.checksum != checksum_text(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact checksum is invalid.")
    return artifact


def is_safe_artifact_filename(file_name: str) -> bool:
    if not file_name or "/" in file_name or "\\" in file_name:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in file_name)


def protect_terms(text: str, glossary_terms: list[str]) -> tuple[str, dict[str, str]]:
    protected = text
    placeholders: dict[str, str] = {}
    for index, term in enumerate(sorted(glossary_terms, key=len, reverse=True), start=1):
        if term not in protected:
            continue
        placeholder = f"__NT_TERM_{index:03d}__"
        protected = protected.replace(term, placeholder)
        placeholders[placeholder] = term
    return protected, placeholders


def restore_terms(text: str, placeholders: dict[str, str]) -> str:
    restored = text
    for placeholder, term in placeholders.items():
        restored = restored.replace(placeholder, term)
    return restored


def generate_subtitles(
    *,
    script_text: str,
    language: str,
    seconds_per_caption: int = 4,
) -> str:
    normalize_language_tag(language)
    captions = split_captions(script_text)
    if len(captions) > MAX_CAPTION_COUNT:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider output creates too many subtitles.")
    entries = []
    for index, caption in enumerate(captions, start=1):
        start = timedelta(seconds=(index - 1) * seconds_per_caption)
        end = timedelta(seconds=index * seconds_per_caption)
        entries.append(srt.Subtitle(index=index, start=start, end=end, content=caption))
    return cast(str, srt.compose(entries))


def split_captions(script_text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", script_text.strip()) if part.strip()]
    if not sentences:
        return []
    captions: list[str] = []
    for sentence in sentences:
        if len(sentence) <= MAX_CAPTION_CHARS:
            captions.append(sentence)
            continue
        words = sentence.split()
        current: list[str] = []
        for word in words:
            if len(word) > MAX_CAPTION_CHARS:
                if current:
                    captions.append(" ".join(current))
                    current = []
                captions.extend(split_long_token(word))
                continue
            candidate = " ".join([*current, word])
            if current and len(candidate) > MAX_CAPTION_CHARS:
                captions.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            captions.append(" ".join(current))
    return captions


def split_long_token(token: str) -> list[str]:
    return [token[index : index + MAX_CAPTION_CHARS] for index in range(0, len(token), MAX_CAPTION_CHARS)]


def resolve_voice_provider(requested_provider: str) -> tuple[str, str | None]:
    normalized = validate_provider_id(requested_provider or "mock", field_name="requested voice provider")
    if normalized == "mock":
        return "mock", None
    return normalized or "mock", "REQUESTED_PROVIDER_UNAVAILABLE"


def estimate_duration_seconds(text: str) -> int:
    word_count = len(text.split())
    return max(1, int(word_count / 2.4))


def language_display_name(language: str) -> str:
    return cast(str, Locale.parse(normalize_language_tag(language)).get_display_name("en"))


def mock_audio_profile(duration_seconds: int) -> dict[str, int]:
    duration_ms = max(1, duration_seconds) * 1000
    segment = AudioSegment.silent(duration=duration_ms, frame_rate=16_000).set_channels(1)
    return {
        "durationMillisecondsEstimate": len(segment),
        "sampleRateHz": segment.frame_rate,
        "channels": segment.channels,
    }


def artifact_from_text(*, file_name: str, mime_type: str, text: str) -> DownloadableArtifact:
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return DownloadableArtifact(
        file_name=file_name,
        mime_type=mime_type,
        content_base64=encoded,
        checksum=checksum_text(text),
    )


def multilingual_to_api(result: MultilingualWalkthroughResult) -> dict[str, object]:
    return {
        "multilingualRunId": result.multilingual_run_id,
        "sourceRunId": result.source_run_id,
        "sourceLanguage": result.source_language,
        "targetLanguage": result.target_language,
        "status": result.status,
        "sourceScriptText": result.source_script_text,
        "translatedScriptText": result.translated_script_text,
        "subtitlesText": result.subtitles_text,
        "glossaryTerms": result.glossary_terms,
        "preservedTerms": result.preserved_terms,
        "translationProvider": {
            "provider": result.translation_provider.provider,
            "providerMode": result.translation_provider.provider_mode,
        },
        "voice": {
            "provider": result.voice.provider,
            "providerMode": result.voice.provider_mode,
            "requestedProvider": result.voice.requested_provider,
            "fallbackReason": result.voice.fallback_reason,
            "language": result.voice.language,
            "artifact": artifact_to_api(result.voice.artifact),
        },
        "artifacts": {
            "translatedScript": artifact_to_api(result.artifacts.translated_script),
            "subtitles": artifact_to_api(result.artifacts.subtitles),
            "voiceManifest": artifact_to_api(result.artifacts.voice_manifest),
        },
        "trace": {
            "traceId": result.trace_id,
            "sourceContextRefCount": result.source_context_ref_count,
            "sourceCitationCount": result.source_citation_count,
        },
    }


def artifact_to_api(artifact: DownloadableArtifact) -> dict[str, str]:
    return {
        "fileName": artifact.file_name,
        "mimeType": artifact.mime_type,
        "contentBase64": artifact.content_base64,
        "checksum": artifact.checksum,
    }


stage6_service = create_stage6_service(state_path=resolve_state_file("stage6"))
