from __future__ import annotations

import base64
import copy
import json
import re
from pathlib import Path
from typing import Any, cast

import pytest

from backend.app.rag.chunking import checksum_text
from backend.app.stage6 import (
    FULL_PROJECT_REPORT_SCHEMA_VERSION,
    LANGUAGE_CATALOG_BY_TAG,
    LANGUAGE_CATALOG_VERSION,
    PRIORITY2_LANGUAGE_TAGS,
    STAGE6_TRANSLATED_ARTIFACT_SCHEMA_VERSION,
    SUPPORTED_LANGUAGES,
    TRANSCRIPT_VALIDATOR_VERSION,
    Stage6Error,
    create_stage6_service,
    get_language_catalog,
    multilingual_to_api,
    translate_demo_segment_text,
    validate_multilingual_transcript_correctness,
)
from backend.app.stage7 import build_source_evaluation_checksum


FIXTURE_PATH = Path("tests/fixtures/checkpoint3_full_project_multilingual_corpus.json")
REPORT_DIR = Path("reports/checkpoint3-multilingual")
COVERAGE_MATRIX_PATH = REPORT_DIR / "full-project-coverage-matrix.json"
REPORT_PATH = REPORT_DIR / "full-project-correctness-report.json"


def test_checkpoint3_full_project_multilingual_corpus_proves_all_supported_languages() -> None:
    fixture = load_fixture()
    assert_evidence_lock_current(fixture)
    assert_fixture_thresholds(fixture)

    source_script = full_project_source_script(fixture)
    evidence_kwargs = source_evidence_kwargs(fixture)
    supported_tags = supported_catalog_tags()
    assert set(supported_tags) == set(SUPPORTED_LANGUAGES)

    coverage_rows: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schemaVersion": FULL_PROJECT_REPORT_SCHEMA_VERSION,
        "fixtureId": fixture["fixtureId"],
        "fixtureHash": fixture["evidenceLock"]["fixtureHash"],
        "expectedOutputHash": fixture["evidenceLock"]["expectedOutputHash"],
        "languageCatalogVersion": LANGUAGE_CATALOG_VERSION,
        "validatorVersion": TRANSCRIPT_VALIDATOR_VERSION,
        "artifactSchemaVersion": STAGE6_TRANSLATED_ARTIFACT_SCHEMA_VERSION,
        "supportedLanguages": [],
        "priority2Refusals": [],
        "languageClassCoverage": {},
        "surfaceParity": [],
        "provenanceNotes": fixture["provenanceNotes"],
        "nonGoals": [
            "does not prove arbitrary-project translation quality",
            "does not prove provider quality",
            "does not authorize hosted/public demo",
            "does not prove raw uploaded knowledge-document translation API behavior",
        ],
    }

    for language_tag in supported_tags:
        result = create_stage6_service().generate_multilingual_walkthrough(
            source_script=source_script,
            target_language=language_tag,
            glossary_terms=["NarraTwin AI", "Atlas Output", "OUTPUT-SENTINEL-CP2", "Stage 4"],
            requested_voice_provider="mock",
            **evidence_kwargs,
        )
        assert result.status == "COMPLETED", language_tag
        assert result.transcript_correctness.validation_status == "PASSED", language_tag
        assert len(result.transcript_segments) == fixture["thresholds"]["transcriptSegmentCount"]
        assert result.source_context_ref_count == fixture["thresholds"]["claimSupportCount"]
        assert len(result.source_claim_support_ids) == fixture["thresholds"]["claimSupportCount"]
        assert len(result.source_context_ref_ids) == fixture["thresholds"]["claimSupportCount"]

        record = LANGUAGE_CATALOG_BY_TAG[language_tag]
        assert record.local_demo_support_status == "SUPPORTED"
        assert record.provider_support_status == "LOCAL_DEMO_FIXTURE"
        assert record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"
        assert_supported_language_output(result=result, fixture=fixture, language_tag=language_tag)
        parity = surface_parity_record(result=result, fixture=fixture, language_tag=language_tag)
        report["surfaceParity"].append(parity)
        report["languageClassCoverage"].setdefault(language_class(language_tag), set()).add(language_tag)
        report["supportedLanguages"].append(
            {
                "languageTag": language_tag,
                "script": record.script,
                "direction": record.direction,
                "localDemoSupportStatus": record.local_demo_support_status,
                "providerSupportStatus": record.provider_support_status,
                "testCoverageLevel": record.test_coverage_level,
                "segmentCount": len(result.transcript_segments),
                "artifactExportCount": parity["artifactExportCount"],
            }
        )
        coverage_rows.append(
            coverage_row(
                language_tag,
                "positive",
                "passed",
                fixture["sourceTranscriptSegments"][0],
            )
        )
        coverage_rows.extend(false_pass_coverage_rows(result=result, fixture=fixture, language_tag=language_tag))

    for priority2_tag in PRIORITY2_LANGUAGE_TAGS:
        with pytest.raises(Stage6Error) as exc:
            create_stage6_service().generate_multilingual_walkthrough(
                source_script=source_script,
                target_language=priority2_tag,
                glossary_terms=["NarraTwin AI", "Atlas Output"],
                requested_voice_provider="mock",
                **evidence_kwargs,
            )
        assert exc.value.code == "LOCAL_DEMO_LANGUAGE_UNSUPPORTED"
        report["priority2Refusals"].append({"languageTag": priority2_tag, "result": "refused"})
        coverage_rows.append(
            coverage_row(
                priority2_tag,
                "unsupported-planned-language-fake-success",
                "failed-as-expected",
                fixture["sourceTranscriptSegments"][0],
            )
        )

    for class_name in tuple(report["languageClassCoverage"]):
        report["languageClassCoverage"][class_name] = sorted(report["languageClassCoverage"][class_name])

    assert len(coverage_rows) >= fixture["thresholds"]["coverageRowCountMinimum"]
    assert {"Hindi/Devanagari", "RTL", "CJK", "Latin-script"}.issubset(report["languageClassCoverage"])
    assert all(row["languageTag"] for row in coverage_rows)
    assert all(row["fixtureRow"] for row in coverage_rows)
    assert all(row["segmentId"] for row in coverage_rows)
    assert all(row["sourceRef"] for row in coverage_rows)
    assert all(row["expectedCondition"] for row in coverage_rows)
    assert all(row["observedViolation"] for row in coverage_rows)
    assert all(row["remediationCategory"] for row in coverage_rows)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    COVERAGE_MATRIX_PATH.write_text(json.dumps(coverage_rows, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


@pytest.mark.parametrize(
    "field",
    (
        "fixtureHash",
        "expectedOutputHash",
        "languageCatalogVersion",
        "validatorVersion",
        "artifactSchemaVersion",
        "reportSchemaVersion",
    ),
)
def test_checkpoint3_full_project_multilingual_rejects_stale_evidence_lock(field: str) -> None:
    fixture = load_fixture()
    fixture["evidenceLock"][field] = "sha256:stale" if field.endswith("Hash") else "stale-version"

    with pytest.raises(AssertionError) as exc:
        assert_evidence_lock_current(fixture)

    assert "stale evidence" in str(exc.value)
    assert field in str(exc.value)


def load_fixture() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def assert_fixture_thresholds(fixture: dict[str, Any]) -> None:
    documents = fixture["project"]["documents"]
    sections = [section for document in documents for section in document["sections"]]
    segments = fixture["sourceTranscriptSegments"]
    citation_count = sum(len(segment["citationIndexes"]) for segment in segments)
    source_refs = [source_ref for segment in segments for source_ref in segment["sourceRefs"]]
    assert len(documents) >= fixture["thresholds"]["documentCount"]
    assert len(sections) >= fixture["thresholds"]["sectionCount"]
    assert len(segments) >= fixture["thresholds"]["transcriptSegmentCount"]
    assert citation_count >= fixture["thresholds"]["citedClaimCount"]
    assert len(source_refs) >= fixture["thresholds"]["claimSupportCount"]
    assert any(len(set(source_ref.split("#", maxsplit=1)[0] for source_ref in segment["sourceRefs"])) > 1 for segment in segments)
    assert any("heading-only-or-missing-body" in segment["exposes"] for segment in segments)
    assert any("private strategy" in note for note in fixture["provenanceNotes"])


def assert_evidence_lock_current(fixture: dict[str, Any]) -> None:
    lock = fixture["evidenceLock"]
    expected = {
        "fixtureHash": fixture_hash(fixture),
        "expectedOutputHash": expected_output_hash(fixture),
        "languageCatalogVersion": LANGUAGE_CATALOG_VERSION,
        "validatorVersion": TRANSCRIPT_VALIDATOR_VERSION,
        "artifactSchemaVersion": STAGE6_TRANSLATED_ARTIFACT_SCHEMA_VERSION,
        "reportSchemaVersion": FULL_PROJECT_REPORT_SCHEMA_VERSION,
    }
    for field, expected_value in expected.items():
        assert lock[field] == expected_value, f"stale evidence: {field}"


def fixture_hash(fixture: dict[str, Any]) -> str:
    stable = copy.deepcopy(fixture)
    stable.pop("evidenceLock")
    return checksum_text(json.dumps(stable, sort_keys=True, ensure_ascii=False))


def expected_output_hash(fixture: dict[str, Any]) -> str:
    expected = []
    for language_tag in supported_catalog_tags():
        translated_segments = []
        for index, segment in enumerate(fixture["sourceTranscriptSegments"], start=1):
            markers = tuple(f"[{citation_index}]" for citation_index in segment["citationIndexes"])
            translated_segments.append(
                {
                    "segmentId": segment["segmentId"],
                    "sourceText": segment["sourceText"],
                    "targetLanguage": language_tag,
                    "targetText": translate_demo_segment_text(
                        segment_number=index,
                        source_segment=segment["sourceText"],
                        target_language=language_tag,
                        citation_markers=markers,
                    ),
                    "englishReferenceText": segment["sourceText"],
                    "citationIndexes": segment["citationIndexes"],
                    "citationMarkers": list(markers),
                    "sourceRefs": segment["sourceRefs"],
                    "contextRefIds": list(expected_context_ref_ids(segment)),
                    "claimSupportIds": list(expected_claim_support_ids(segment)),
                }
            )
        expected.append({"languageTag": language_tag, "segments": translated_segments})
    return checksum_text(json.dumps(expected, sort_keys=True, ensure_ascii=False))


def full_project_source_script(fixture: dict[str, Any]) -> str:
    return " ".join(segment["sourceText"] for segment in fixture["sourceTranscriptSegments"])


def source_evidence_kwargs(fixture: dict[str, Any]) -> dict[str, Any]:
    citation_pairs = citation_source_ref_pairs(fixture)
    citation_indexes = tuple(index for index, _source_ref in citation_pairs)
    context_ref_ids = tuple(context_ref_id(citation_index, source_ref) for citation_index, source_ref in citation_pairs)
    claim_support_ids = tuple(
        claim_support_id(citation_index, source_ref) for citation_index, source_ref in citation_pairs
    )
    return {
        "source_run_id": "run_c3a_r2_full_project",
        "trace_id": "trace_c3a_r2_full_project",
        "source_context_ref_count": len(context_ref_ids),
        "source_citation_count": len(citation_indexes),
        "source_context_ref_ids": context_ref_ids,
        "source_citation_indexes": citation_indexes,
        "source_claim_support_ids": claim_support_ids,
        "source_evaluation_id": "eval_c3a_r2_full_project",
        "source_evaluation_checksum": build_source_evaluation_checksum(
            source_evaluation_id="eval_c3a_r2_full_project",
            source_run_id="run_c3a_r2_full_project",
            trace_id="trace_c3a_r2_full_project",
            evaluation_status="PASSED",
            source_context_ref_ids=context_ref_ids,
            source_context_ref_count=len(context_ref_ids),
            source_citation_indexes=citation_indexes,
            source_citation_count=len(citation_indexes),
        ),
        "evaluation_status": "PASSED",
    }


def citation_source_ref_pairs(fixture: dict[str, Any]) -> tuple[tuple[int, str], ...]:
    pairs: list[tuple[int, str]] = []
    for segment in fixture["sourceTranscriptSegments"]:
        pairs.extend(
            (int(citation_index), str(source_ref))
            for citation_index, source_ref in zip(segment["citationIndexes"], segment["sourceRefs"], strict=True)
        )
    return tuple(pairs)


def context_ref_id(citation_index: int, source_ref: str) -> str:
    return f"ctx_{citation_index:03d}:{source_ref}"


def claim_support_id(citation_index: int, source_ref: str) -> str:
    return f"claimsup_{citation_index:03d}:{source_ref}"


def expected_context_ref_ids(fixture_segment: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        context_ref_id(int(citation_index), str(source_ref))
        for citation_index, source_ref in zip(
            fixture_segment["citationIndexes"],
            fixture_segment["sourceRefs"],
            strict=True,
        )
    )


def expected_claim_support_ids(fixture_segment: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        claim_support_id(int(citation_index), str(source_ref))
        for citation_index, source_ref in zip(
            fixture_segment["citationIndexes"],
            fixture_segment["sourceRefs"],
            strict=True,
        )
    )


def supported_catalog_tags() -> tuple[str, ...]:
    return tuple(
        record.language_tag
        for record in get_language_catalog()
        if (
            record.local_demo_support_status == "SUPPORTED"
            and record.provider_support_status == "LOCAL_DEMO_FIXTURE"
            and record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"
        )
    )


def assert_supported_language_output(*, result: Any, fixture: dict[str, Any], language_tag: str) -> None:
    source_segments = fixture["sourceTranscriptSegments"]
    assert tuple(segment.segment_id for segment in result.transcript_segments) == tuple(
        segment["segmentId"] for segment in source_segments
    )
    for observed, expected in zip(result.transcript_segments, source_segments, strict=True):
        assert observed.source_text == expected["sourceText"]
        assert observed.english_reference_text == expected["sourceText"]
        assert observed.citation_indexes == tuple(expected["citationIndexes"])
        assert observed.citation_markers == tuple(f"[{index}]" for index in expected["citationIndexes"])
        assert observed.context_ref_ids == expected_context_ref_ids(expected)
        assert observed.claim_support_ids == expected_claim_support_ids(expected)
        assert observed.source_run_id == result.source_run_id
        assert observed.evaluation_id == result.source_evaluation_id
        assert observed.target_text
        if language_tag != "en":
            assert observed.target_text != observed.source_text
    if language_tag == "hi":
        assert all(any("\u0900" <= char <= "\u097f" for char in segment.target_text) for segment in result.transcript_segments)
        assert "global viewers ke liye" not in result.translated_script_text.lower()
        assert "वॉकथ्रू" not in result.translated_script_text
    if language_tag in {"ar", "arz", "he", "fa"}:
        assert result.transcript_correctness.direction == "rtl"
        assert "[2] [5]" in result.transcript_segments[1].target_text
        assert "Direction: rtl" in decoded_artifact_text(result.artifacts.translated_script)
    if language_tag in {"ja", "zh-Hans", "zh-Hant", "ko"}:
        assert "  " not in result.translated_script_text
        assert "[7]" in result.transcript_segments[-1].target_text
        if language_tag == "ko":
            assert all(any("\uac00" <= char <= "\ud7af" for char in segment.target_text) for segment in result.transcript_segments)
        else:
            assert not re.search(r"[\u3040-\u30ff\u3400-\u9fff] [\u3040-\u30ff\u3400-\u9fff]", result.translated_script_text)
    if language_tag in {"es", "de", "fr", "pt-BR", "it", "nl", "pl", "tr", "vi", "id", "fil", "ms"}:
        assert "For global viewers" not in result.translated_script_text
        assert result.transcript_segments[1].citation_markers == ("[2]", "[5]")
    if language_tag == "fr":
        assert "vérifications" in result.translated_script_text


def surface_parity_record(*, result: Any, fixture: dict[str, Any], language_tag: str) -> dict[str, Any]:
    api_payload = multilingual_to_api(result)
    assert_api_payload_has_body_parity(api_payload=api_payload, result=result)
    metadata_text = decoded_artifact_text(result.artifacts.metadata)
    metadata = json.loads(metadata_text)
    translated_artifact_text = decoded_artifact_text(result.artifacts.translated_script)
    subtitles_text = decoded_artifact_text(result.artifacts.subtitles)
    voice_manifest = json.loads(decoded_artifact_text(result.artifacts.voice_manifest))
    api_transcript = api_payload["transcriptSegments"]
    stored_output = {
        "sourceScriptText": result.source_script_text,
        "translatedScriptText": result.translated_script_text,
        "transcriptSegments": api_transcript,
    }
    assert metadata["sourceScriptText"] == stored_output["sourceScriptText"]
    assert metadata["translatedScriptText"] == stored_output["translatedScriptText"]
    assert metadata["transcriptSegments"] == api_transcript
    assert metadata["sourceContextRefIds"] == list(result.source_context_ref_ids)
    assert metadata["sourceClaimSupportIds"] == list(result.source_claim_support_ids)
    assert metadata["sourceCitationIndexes"] == list(result.source_citation_indexes)
    assert subtitles_text == result.subtitles_text
    assert voice_manifest["language"] == language_tag
    assert voice_manifest["provider"] == "mock"
    assert voice_manifest["providerMode"] == "LOCAL"
    assert voice_manifest["textChecksum"] == checksum_text(result.translated_script_text)
    for segment in result.transcript_segments:
        assert f"Source English: {segment.source_text}" in translated_artifact_text
        assert f"Target ({language_tag}): {segment.target_text}" in translated_artifact_text
        assert f"English reference: {segment.english_reference_text}" in translated_artifact_text
        assert f"Citations: {', '.join(segment.citation_markers)}" in translated_artifact_text
        assert f"Context refs: {', '.join(segment.context_ref_ids)}" in translated_artifact_text
        assert f"Claim support ids: {', '.join(segment.claim_support_ids)}" in translated_artifact_text
    return {
        "languageTag": language_tag,
        "apiTranscriptSurfaceMatchesStoredOutput": True,
        "metadataMatchesStoredOutput": True,
        "translatedScriptArtifactMatchesTranscript": True,
        "subtitlesArtifactMatchesTranscript": True,
        "voiceManifestMatchesTranscript": True,
        "artifactExportCount": len(cast(dict[str, Any], api_payload["artifacts"])),
    }


def decoded_artifact_text(artifact: Any) -> str:
    return base64.b64decode(artifact.content_base64, validate=True).decode("utf-8")


def assert_api_payload_has_body_parity(*, api_payload: dict[str, object], result: Any) -> None:
    transcript_segments = cast(list[dict[str, Any]], api_payload["transcriptSegments"])
    artifacts = cast(dict[str, dict[str, str]], api_payload["artifacts"])
    assert transcript_segments
    assert api_payload["sourceScriptText"] == result.source_script_text
    assert api_payload["translatedScriptText"] == result.translated_script_text
    assert api_payload["subtitlesText"] == result.subtitles_text
    assert transcript_segments == [segment_to_api(segment) for segment in result.transcript_segments]
    assert set(artifacts) == {"translatedScript", "subtitles", "voiceManifest", "metadata"}
    artifact_texts = {
        name: base64.b64decode(artifact["contentBase64"], validate=True).decode("utf-8")
        for name, artifact in artifacts.items()
    }
    assert artifact_texts["subtitles"] == result.subtitles_text
    assert json.loads(artifact_texts["metadata"])["transcriptSegments"] == transcript_segments
    assert json.loads(artifact_texts["voiceManifest"])["textChecksum"] == checksum_text(result.translated_script_text)
    for segment in result.transcript_segments:
        assert segment.source_text in artifact_texts["translatedScript"]
        assert segment.target_text in artifact_texts["translatedScript"]
        assert segment.english_reference_text in artifact_texts["translatedScript"]


def false_pass_coverage_rows(*, result: Any, fixture: dict[str, Any], language_tag: str) -> list[dict[str, Any]]:
    body_segments = [segment_to_api(segment) for segment in result.transcript_segments]
    heading_exposure_segment = next(
        segment for segment in body_segments if segment["segmentId"] == "seg_004"
    )
    heading_exposure_fixture = next(
        segment for segment in fixture["sourceTranscriptSegments"] if segment["segmentId"] == "seg_004"
    )
    first_fixture_segment = fixture["sourceTranscriptSegments"][0]
    mutations: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {
        "partial-project-translation": (body_segments[:-1], fixture["sourceTranscriptSegments"][-1]),
        "missing-document-translation": (
            [segment for segment in body_segments if not segment["segmentId"].startswith(("seg_005", "seg_006"))],
            fixture["sourceTranscriptSegments"][4],
        ),
        "missing-section-translation": ([segment for segment in body_segments if segment["segmentId"] != "seg_004"], heading_exposure_fixture),
        "single-segment-partial-success": (body_segments[:1], fixture["sourceTranscriptSegments"][1]),
        "heading-only-success": (
            [dict(heading_exposure_segment, targetText="Narration Safety [4]")],
            heading_exposure_fixture,
        ),
        "partial-section-body-success": (
            [dict(heading_exposure_segment, targetText="The narration safety document [4]")],
            heading_exposure_fixture,
        ),
        "missing-body-success": ([dict(heading_exposure_segment, targetText="[4]")], heading_exposure_fixture),
        "wrong-script": ([dict(body_segments[0], targetText="romanized fallback [1]")], first_fixture_segment),
        "romanized-fallback": (
            [dict(body_segments[0], targetText="global viewers ke liye NarraTwin AI badalta hai [1]")],
            first_fixture_segment,
        ),
        "illegitimate-source-term-leakage": (
            [dict(body_segments[0], targetText=f"{body_segments[0]['targetText']} walkthrough")],
            first_fixture_segment,
        ),
        "altered-claim-loses-source-support": (
            [dict(body_segments[0], targetText=body_segments[-1]["targetText"])],
            first_fixture_segment,
        ),
        "citation-drift": (
            [dict(body_segments[1], citationMarkers=["[5]", "[2]"], citationIndexes=[5, 2])],
            fixture["sourceTranscriptSegments"][1],
        ),
        "citation-id-without-source-span": (
            [dict(body_segments[1], sourceText=body_segments[0]["sourceText"])],
            fixture["sourceTranscriptSegments"][1],
        ),
        "missing-source": ([dict(body_segments[0], sourceText="")], first_fixture_segment),
        "missing-target": ([dict(body_segments[0], targetText="")], first_fixture_segment),
        "missing-english-reference": ([dict(body_segments[0], englishReferenceText="")], first_fixture_segment),
        "missing-context-ref": ([dict(body_segments[0], contextRefIds=[])], first_fixture_segment),
        "missing-claim-support-binding": ([dict(body_segments[0], claimSupportIds=[])], first_fixture_segment),
        "stale-coverage-row": (body_segments[:-1], fixture["sourceTranscriptSegments"][-1]),
    }
    if language_tag != "en":
        mutations["untranslated-english-fallback"] = [
            dict(segment, targetText=segment["sourceText"]) for segment in body_segments
        ], first_fixture_segment
    rows: list[dict[str, Any]] = []
    for mutation_name, (mutated_segments, fixture_segment) in mutations.items():
        try:
            validate_multilingual_transcript_correctness(
                language_tag=language_tag,
                source_text=result.source_script_text,
                segments=mutated_segments,
                source_run_id=result.source_run_id,
                evaluation_id=result.source_evaluation_id,
                context_ref_ids=result.source_context_ref_ids,
                citation_indexes=result.source_citation_indexes,
                claim_support_ids=result.source_claim_support_ids,
            )
        except Stage6Error as exc:
            rows.append(coverage_row(language_tag, mutation_name, exc.code, fixture_segment))
            continue
        pytest.fail(f"{language_tag} false-pass mutation was accepted: {mutation_name}")
    api_payload = multilingual_to_api(result)
    for mutation_name, mutated_payload in {
        "metadata-only-success": dict(api_payload, transcriptSegments=[], translatedScriptText=""),
        "artifact-only-success": dict(api_payload, transcriptSegments=[], sourceScriptText="", translatedScriptText=""),
    }.items():
        with pytest.raises(AssertionError):
            assert_api_payload_has_body_parity(api_payload=mutated_payload, result=result)
        rows.append(coverage_row(language_tag, mutation_name, "surface-parity-failed", first_fixture_segment))
    return rows


def segment_to_api(segment: Any) -> dict[str, Any]:
    return {
        "segmentId": segment.segment_id,
        "sourceText": segment.source_text,
        "targetLanguage": segment.target_language,
        "targetText": segment.target_text,
        "englishReferenceText": segment.english_reference_text,
        "citationMarkers": list(segment.citation_markers),
        "citationIndexes": list(segment.citation_indexes),
        "contextRefIds": list(segment.context_ref_ids),
        "claimSupportIds": list(segment.claim_support_ids),
        "sourceRunId": segment.source_run_id,
        "evaluationId": segment.evaluation_id,
    }


def coverage_row(
    language_tag: str,
    condition: str,
    result: str,
    fixture_segment: dict[str, Any],
) -> dict[str, str]:
    return {
        "languageTag": language_tag,
        "fixtureRow": fixture_segment["fixtureRow"],
        "segmentId": fixture_segment["segmentId"],
        "sourceRef": ";".join(fixture_segment["sourceRefs"]),
        "expectedCondition": condition,
        "observedViolation": result,
        "remediationCategory": remediation_category(condition),
    }


def remediation_category(condition: str) -> str:
    if "stale" in condition:
        return "refresh-evidence"
    if "unsupported" in condition:
        return "demote-or-refuse-language"
    if "citation" in condition or "source" in condition or "claim" in condition or "context" in condition:
        return "repair-source-binding"
    if "artifact" in condition or "metadata" in condition:
        return "repair-surface-parity"
    return "repair-transcript-body"


def language_class(language_tag: str) -> str:
    record = LANGUAGE_CATALOG_BY_TAG[language_tag]
    if language_tag == "hi":
        return "Hindi/Devanagari"
    if record.direction == "rtl":
        return "RTL"
    if language_tag in {"ja", "zh-Hans", "zh-Hant", "ko"}:
        return "CJK"
    if record.script == "Latin":
        return "Latin-script"
    return record.script
