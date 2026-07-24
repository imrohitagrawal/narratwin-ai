from __future__ import annotations

import base64
import copy
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from backend.app.rag.chunking import checksum_text
from backend.app.stage6 import (
    LANGUAGE_CATALOG_BY_TAG,
    LANGUAGE_CATALOG_VERSION,
    PRIORITY2_LANGUAGE_TAGS,
    STAGE6_TRANSLATED_ARTIFACT_SCHEMA_VERSION,
    SUPPORTED_LANGUAGES,
    TRANSCRIPT_VALIDATOR_VERSION,
    FULL_PROJECT_REPORT_SCHEMA_VERSION,
    Stage6Error,
    create_stage6_service,
    get_language_catalog,
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
    citation_indexes = full_project_citation_indexes(fixture)
    evidence_kwargs = source_evidence_kwargs(citation_indexes)
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
        coverage_rows.append(coverage_row(language_tag, "positive", "passed", fixture["sourceTranscriptSegments"][0]))
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
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
    stable["evidenceLock"] = {
        key: value
        for key, value in stable["evidenceLock"].items()
        if key not in {"fixtureHash", "expectedOutputHash"}
    }
    return checksum_text(json.dumps(stable, sort_keys=True, ensure_ascii=False))


def expected_output_hash(fixture: dict[str, Any]) -> str:
    expected = [
        {
            "segmentId": segment["segmentId"],
            "sourceText": segment["sourceText"],
            "citationIndexes": segment["citationIndexes"],
            "sourceRefs": segment["sourceRefs"],
        }
        for segment in fixture["sourceTranscriptSegments"]
    ]
    return checksum_text(json.dumps(expected, sort_keys=True, ensure_ascii=False))


def full_project_source_script(fixture: dict[str, Any]) -> str:
    return " ".join(segment["sourceText"] for segment in fixture["sourceTranscriptSegments"])


def full_project_citation_indexes(fixture: dict[str, Any]) -> tuple[int, ...]:
    return tuple(
        citation_index
        for segment in fixture["sourceTranscriptSegments"]
        for citation_index in segment["citationIndexes"]
    )


def source_evidence_kwargs(citation_indexes: tuple[int, ...]) -> dict[str, Any]:
    context_ref_ids = tuple(f"ctx_{index:03d}" for index in citation_indexes)
    claim_support_ids = tuple(f"claimsup_{index:03d}" for index in citation_indexes)
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
        assert observed.context_ref_ids
        assert observed.claim_support_ids
        assert observed.source_run_id == result.source_run_id
        assert observed.evaluation_id == result.source_evaluation_id
        assert observed.target_text
        if language_tag != "en":
            assert observed.target_text != observed.source_text
    if language_tag == "hi":
        assert any("\u0900" <= char <= "\u097f" for char in result.translated_script_text)
        assert "global viewers ke liye" not in result.translated_script_text.lower()
        assert "वॉकथ्रू" not in result.translated_script_text
    if language_tag in {"ar", "arz", "he", "fa"}:
        assert result.transcript_correctness.direction == "rtl"
        assert "[2] [5]" in result.transcript_segments[1].target_text
    if language_tag in {"ja", "zh-Hans", "zh-Hant", "ko"}:
        assert "  " not in result.translated_script_text
        assert "[7]" in result.transcript_segments[-1].target_text
    if language_tag in {"es", "de", "fr", "pt-BR", "it", "nl", "pl", "tr", "vi", "id", "fil", "ms"}:
        assert "For global viewers" not in result.translated_script_text
        assert result.transcript_segments[1].citation_markers == ("[2]", "[5]")
    if language_tag == "fr":
        assert "vérifications" in result.translated_script_text


def surface_parity_record(*, result: Any, fixture: dict[str, Any], language_tag: str) -> dict[str, Any]:
    metadata_text = base64.b64decode(result.artifacts.metadata.content_base64, validate=True).decode("utf-8")
    metadata = json.loads(metadata_text)
    translated_artifact_text = base64.b64decode(
        result.artifacts.translated_script.content_base64,
        validate=True,
    ).decode("utf-8")
    ui_transcript = [asdict(segment) for segment in result.transcript_segments]
    stored_output = {
        "sourceScriptText": result.source_script_text,
        "translatedScriptText": result.translated_script_text,
        "transcriptSegments": ui_transcript,
    }
    assert metadata["sourceScriptText"] == stored_output["sourceScriptText"]
    assert metadata["translatedScriptText"] == stored_output["translatedScriptText"]
    assert metadata["transcriptSegments"] == [
        {
            "segmentId": segment["segment_id"],
            "sourceText": segment["source_text"],
            "targetLanguage": segment["target_language"],
            "targetText": segment["target_text"],
            "englishReferenceText": segment["english_reference_text"],
            "citationMarkers": list(segment["citation_markers"]),
            "citationIndexes": list(segment["citation_indexes"]),
            "contextRefIds": list(segment["context_ref_ids"]),
            "claimSupportIds": list(segment["claim_support_ids"]),
            "sourceRunId": segment["source_run_id"],
            "evaluationId": segment["evaluation_id"],
        }
        for segment in ui_transcript
    ]
    for segment in result.transcript_segments:
        assert f"Source English: {segment.source_text}" in translated_artifact_text
        assert f"Target ({language_tag}): {segment.target_text}" in translated_artifact_text
        assert f"English reference: {segment.english_reference_text}" in translated_artifact_text
        assert f"Citations: {', '.join(segment.citation_markers)}" in translated_artifact_text
        assert f"Context refs: {', '.join(segment.context_ref_ids)}" in translated_artifact_text
        assert f"Claim support ids: {', '.join(segment.claim_support_ids)}" in translated_artifact_text
    return {
        "languageTag": language_tag,
        "uiTranscriptMatchesStoredOutput": True,
        "metadataMatchesStoredOutput": True,
        "translatedScriptArtifactMatchesTranscript": True,
        "artifactExportCount": fixture["thresholds"]["artifactExportCount"],
    }


def false_pass_coverage_rows(*, result: Any, fixture: dict[str, Any], language_tag: str) -> list[dict[str, Any]]:
    body_segments = [segment_to_api(segment) for segment in result.transcript_segments]
    mutations = {
        "partial-project-translation": body_segments[:-1],
        "missing-document-translation": [
            segment for segment in body_segments if not segment["segmentId"].startswith(("seg_005", "seg_006"))
        ],
        "missing-section-translation": [segment for segment in body_segments if segment["segmentId"] != "seg_004"],
        "single-segment-partial-success": body_segments[:1],
        "heading-only-success": [dict(body_segments[0], targetText="Product Overview [1]")],
        "untranslated-english-fallback": [dict(segment, targetText=segment["sourceText"]) for segment in body_segments],
        "wrong-script": [dict(body_segments[0], targetText="romanized fallback [1]")],
        "romanized-fallback": [dict(body_segments[0], targetText="global viewers ke liye NarraTwin AI badalta hai [1]")],
        "illegitimate-source-term-leakage": [dict(body_segments[0], targetText=f"{body_segments[0]['targetText']} walkthrough")],
        "altered-claim-loses-source-support": [dict(body_segments[0], targetText=body_segments[-1]["targetText"])],
        "citation-drift": [dict(body_segments[1], citationMarkers=["[5]", "[2]"], citationIndexes=[5, 2])],
        "citation-id-without-source-span": [dict(body_segments[1], sourceText=body_segments[0]["sourceText"])],
        "missing-source": [dict(body_segments[0], sourceText="")],
        "missing-target": [dict(body_segments[0], targetText="")],
        "missing-english-reference": [dict(body_segments[0], englishReferenceText="")],
        "missing-context-ref": [dict(body_segments[0], contextRefIds=[])],
        "missing-claim-support-binding": [dict(body_segments[0], claimSupportIds=[])],
        "metadata-only-success": [],
        "artifact-only-success": [],
        "stale-coverage-row": body_segments[:-1],
    }
    rows: list[dict[str, Any]] = []
    for mutation_name, mutated_segments in mutations.items():
        with pytest.raises(Exception):
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
        rows.append(coverage_row(language_tag, mutation_name, "failed-as-expected", fixture["sourceTranscriptSegments"][0]))
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
        "sourceRef": fixture_segment["sourceRefs"][0],
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
