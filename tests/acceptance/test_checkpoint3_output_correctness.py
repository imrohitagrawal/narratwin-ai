from __future__ import annotations

# ruff: noqa: E402

import os
import base64
import copy
import json
from collections.abc import Iterator
from pathlib import Path
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
from backend.app.rag.models import GeneratedScript, RetrievedContext, ScriptClaim
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage6 import (
    PRIORITY1_LANGUAGE_TAGS,
    TranslationProviderResult,
    stage6_service,
    validate_multilingual_transcript_correctness,
)
from backend.app.stage4 import stage4_service


ATLAS_OUTPUT_KNOWLEDGE = b"""# Atlas Output

Atlas Output OUTPUT-SENTINEL-CP2 is a fictional local checklist builder for launch rehearsals.

Atlas Output OUTPUT-SENTINEL-CP2 requires each generated checklist item to cite approved launch-note evidence.

Atlas Output uses the marker OUTPUT-SENTINEL-CP2 for output-correctness isolation checks.
"""

BEACON_OUTPUT_KNOWLEDGE = b"""# Beacon Output

Beacon Output BEACON-OUTPUT-CP2 is a fictional community alert console.
Beacon Output sends timezone-aware reminder packets for neighborhood coordinators.
Beacon Output uses the marker BEACON-OUTPUT-CP2 for cross-project replay checks.
"""

ARBITRARY_NARRATWIN_KNOWLEDGE = b"""# NarraTwin AI

NarraTwin AI acquired Jupiter Labs to build moon-base onboarding scripts for Mars pilots.
"""

REQUIRED_ATLAS_FACT = (
    "Atlas Output OUTPUT-SENTINEL-CP2 is a fictional local checklist builder for launch rehearsals."
)
BEACON_CROSS_PROJECT_FACT = (
    "Beacon Output sends timezone-aware reminder packets for neighborhood coordinators."
)
CHECKPOINT3_MULTILINGUAL_REPORT_DIR = Path("reports/checkpoint3-multilingual")


@pytest.fixture(autouse=True)
def local_only_output_correctness_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()
    yield
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()


class CrossProjectFactProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[RetrievedContext],
    ) -> GeneratedScript:
        del audience, prompt
        context = retrieved_context[0]
        sentence = f"{BEACON_CROSS_PROJECT_FACT} [1]"
        return GeneratedScript(
            text=sentence,
            claims=[
                ScriptClaim(
                    claim_id="claim_cross_project_001",
                    text=BEACON_CROSS_PROJECT_FACT,
                    citation_index=1,
                    chunk_id=context.chunk.chunk_id,
                    script_span_start=0,
                    script_span_end=len(sentence),
                )
            ],
        )


class CorrectTextMissingEvidenceProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[RetrievedContext],
    ) -> GeneratedScript:
        del audience, prompt, retrieved_context
        sentence = f"{REQUIRED_ATLAS_FACT} [1]"
        return GeneratedScript(
            text=sentence,
            claims=[
                ScriptClaim(
                    claim_id="claim_correct_text_missing_evidence_001",
                    text=REQUIRED_ATLAS_FACT,
                    citation_index=1,
                    chunk_id="missing-runtime-evidence-chunk",
                    script_span_start=0,
                    script_span_end=len(sentence),
                )
            ],
        )


class DivergentTranslationProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        glossary_terms: list[str],
    ) -> TranslationProviderResult:
        del source_text, glossary_terms
        return TranslationProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            source_language=source_language,
            target_language=target_language,
            translated_text="Atlas Output OUTPUT-SENTINEL-CP2 WRONG SEMANTIC PROVIDER OUTPUT [1]",
            preserved_terms=["Atlas Output", "OUTPUT-SENTINEL-CP2"],
        )


def create_project(client: TestClient, *, prefix: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Synthetic C3A-CP2 output-correctness fixture.",
            "defaultAudience": "ENGINEER",
            "defaultLanguage": "en",
        },
        headers={"Idempotency-Key": f"{prefix}-project"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def upload_document(
    client: TestClient,
    *,
    prefix: str,
    project_id: str,
    filename: str,
    content: bytes,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={"file": (filename, content, "text/markdown")},
        headers={"Idempotency-Key": f"{prefix}-upload"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def approve_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> dict[str, Any]:
    response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP2 knowledge."},
        headers={"Idempotency-Key": f"{prefix}-approval"},
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


def ingest_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers={"Idempotency-Key": f"{prefix}-ingest"},
    )
    assert response.status_code == 201
    ingestion = cast(dict[str, Any], response.json())
    assert ingestion["status"] == "COMPLETED"
    assert ingestion["chunkCount"] > 0
    assert ingestion["embeddingCount"] == ingestion["chunkCount"]
    return ingestion


def prepare_approved_project(
    client: TestClient,
    *,
    prefix: str,
    name: str,
    filename: str,
    content: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project = create_project(client, prefix=prefix, name=name)
    document = upload_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        filename=filename,
        content=content,
    )
    approved = approve_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    ingest_document(
        client,
        prefix=prefix,
        project_id=project["projectId"],
        document_id=document["documentId"],
    )
    return project, approved


def generate_walkthrough(client: TestClient, *, prefix: str, project_id: str, prompt: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json={
            "audience": "ENGINEER",
            "requestedLanguage": "en",
            "depth": "CONCISE",
            "style": "TECHNICAL",
            "prompt": prompt,
        },
        headers={"Idempotency-Key": f"{prefix}-generate"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def replay_walkthrough(client: TestClient, *, prefix: str, project_id: str, prompt: str) -> dict[str, Any]:
    return generate_walkthrough(client, prefix=prefix, project_id=project_id, prompt=prompt)


def assert_runtime_output_fact_is_grounded(
    run: dict[str, Any],
    *,
    project_id: str,
    document: dict[str, Any],
    required_fact: str,
) -> None:
    script = run.get("acceptedScriptText")
    assert isinstance(script, str)
    assert required_fact in script
    assert "[1]" in script
    assert run["status"] == "COMPLETED"
    assert run["evaluationStatus"] == "PASSED"
    assert run["provider"] == {"provider": "mock", "providerMode": "LOCAL"}
    assert run["trace"]["estimatedCost"] == 0

    context_refs = run["contextRefs"]
    claim_supports = run["evaluation"]["claimSupports"]
    assert context_refs
    assert claim_supports
    assert run["evaluation"]["unsupportedClaimCount"] == 0
    assert run["evaluation"]["contextRefCoverage"] == 1.0

    context_by_id = {context["contextRefId"]: context for context in context_refs}
    supporting_rows = [
        support
        for support in claim_supports
        if required_fact in support["evidenceSnapshot"]["redactedExcerpt"]
    ]
    assert supporting_rows

    for support in supporting_rows:
        context = context_by_id[support["contextRefId"]]
        assert support["projectId"] == project_id
        assert support["documentId"] == document["documentId"]
        assert support["chunkId"] == context["chunkId"]
        assert support["citationIndex"] == 1
        assert support["supportStatus"] == "SUPPORTED"
        assert context["projectId"] == project_id
        assert context["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["projectId"] == project_id
        assert context["evidenceSnapshot"]["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["sourceDocumentChecksum"] == document["checksum"]
        assert context["evidenceSnapshot"]["chunkChecksum"] == context["checksum"]
        assert support["evidenceSnapshot"]["snapshotChecksum"] == context["evidenceSnapshot"]["snapshotChecksum"]


def test_checkpoint3_output_correctness_executes_runtime_api_evidence_path() -> None:
    client = TestClient(app)
    project, document = prepare_approved_project(
        client,
        prefix="output-atlas",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    prompt = "Create a grounded walkthrough for Atlas Output using only approved source facts."

    run = generate_walkthrough(
        client,
        prefix="output-atlas",
        project_id=project["projectId"],
        prompt=prompt,
    )
    replay = replay_walkthrough(
        client,
        prefix="output-atlas",
        project_id=project["projectId"],
        prompt=prompt,
    )

    assert replay == run
    assert_runtime_output_fact_is_grounded(
        replay,
        project_id=project["projectId"],
        document=document,
        required_fact=REQUIRED_ATLAS_FACT,
    )
    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    assert ops.json()["durability"]["stage4"]["recordCounts"]["walkthroughRuns"] == 1


def test_checkpoint3_output_correctness_rejects_correct_text_without_evidence_binding() -> None:
    client = TestClient(app)
    project, _document = prepare_approved_project(
        client,
        prefix="output-binding",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    stage4_service.llm = cast(Any, CorrectTextMissingEvidenceProvider())

    run = generate_walkthrough(
        client,
        prefix="output-binding",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert "evaluation" not in run
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert REQUIRED_ATLAS_FACT in run["redactedUnsupportedExcerpts"][0]


def test_checkpoint3_output_correctness_rejects_unsupported_claim_acceptance() -> None:
    client = TestClient(app)
    project, _document = prepare_approved_project(
        client,
        prefix="output-unsupported",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    stage4_service.llm = MockLLMProvider(
        extra_unsupported_claim="Atlas Output guarantees external revenue growth."
    )

    run = generate_walkthrough(
        client,
        prefix="output-unsupported",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert "external revenue growth" in run["redactedUnsupportedExcerpts"][0]


def test_checkpoint3_output_correctness_rejects_cross_project_fact_replay() -> None:
    client = TestClient(app)
    atlas, _atlas_document = prepare_approved_project(
        client,
        prefix="output-cross-atlas",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    prepare_approved_project(
        client,
        prefix="output-cross-beacon",
        name="Beacon Output",
        filename="beacon_output.md",
        content=BEACON_OUTPUT_KNOWLEDGE,
    )
    stage4_service.llm = cast(Any, CrossProjectFactProvider())

    run = generate_walkthrough(
        client,
        prefix="output-cross-atlas",
        project_id=atlas["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )

    assert run["status"] == "FAILED"
    assert run["evaluationStatus"] == "FAILED"
    assert "acceptedScriptText" not in run
    assert run["failure"]["reasonCode"] == "UNSUPPORTED_PROJECT_FACT"
    assert run["failure"]["unsupportedClaimCount"] > 0
    assert BEACON_CROSS_PROJECT_FACT in run["redactedUnsupportedExcerpts"][0]
    for context in run["contextRefs"]:
        assert context["projectId"] == atlas["projectId"]
        assert "BEACON-OUTPUT-CP2" not in context["evidenceSnapshot"]["redactedExcerpt"]


def test_checkpoint3_output_correctness_rejects_provider_script_that_diverges_from_transcript() -> None:
    client = TestClient(app)
    project, document = prepare_approved_project(
        client,
        prefix="output-divergent-provider",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    run = generate_walkthrough(
        client,
        prefix="output-divergent-provider",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )
    assert_runtime_output_fact_is_grounded(
        run,
        project_id=project["projectId"],
        document=document,
        required_fact=REQUIRED_ATLAS_FACT,
    )

    stage6_service.translation_provider = cast(Any, DivergentTranslationProvider())
    response = client.post(
        f"/api/v1/projects/{project['projectId']}/walkthrough-runs/{run['runId']}/multilingual-runs",
        json={
            "targetLanguage": "fr",
            "glossaryTerms": ["Atlas Output", "OUTPUT-SENTINEL-CP2"],
            "requestedVoiceProvider": "mock",
        },
        headers={"Idempotency-Key": "output-divergent-provider-fr"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PROVIDER_OUTPUT_INVALID"


def test_checkpoint3_output_correctness_refuses_arbitrary_narratwin_fixture_translation() -> None:
    client = TestClient(app)
    project, _document = prepare_approved_project(
        client,
        prefix="output-arbitrary-narratwin",
        name="NarraTwin AI",
        filename="arbitrary_narratwin.md",
        content=ARBITRARY_NARRATWIN_KNOWLEDGE,
    )
    run = generate_walkthrough(
        client,
        prefix="output-arbitrary-narratwin",
        project_id=project["projectId"],
        prompt="Jupiter Labs moon-base onboarding scripts Mars pilots",
    )
    assert run["status"] == "COMPLETED"
    assert "Jupiter Labs" in run["acceptedScriptText"]

    response = client.post(
        f"/api/v1/projects/{project['projectId']}/walkthrough-runs/{run['runId']}/multilingual-runs",
        json={
            "targetLanguage": "fr",
            "glossaryTerms": ["NarraTwin AI"],
            "requestedVoiceProvider": "mock",
        },
        headers={"Idempotency-Key": "output-arbitrary-narratwin-fr"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "LOCAL_DEMO_TRANSLATION_UNSUPPORTED"


def test_checkpoint3_output_correctness_exhaustively_proves_priority1_multilingual_outputs() -> None:
    client = TestClient(app)
    project, document = prepare_approved_project(
        client,
        prefix="output-multilingual-p1",
        name="Atlas Output",
        filename="atlas_output.md",
        content=ATLAS_OUTPUT_KNOWLEDGE,
    )
    run = generate_walkthrough(
        client,
        prefix="output-multilingual-p1",
        project_id=project["projectId"],
        prompt="Create a grounded walkthrough for Atlas Output using only approved source facts.",
    )
    assert_runtime_output_fact_is_grounded(
        run,
        project_id=project["projectId"],
        document=document,
        required_fact=REQUIRED_ATLAS_FACT,
    )

    coverage_rows: list[dict[str, Any]] = []
    summary: dict[str, dict[str, Any]] = {}
    for language_tag in PRIORITY1_LANGUAGE_TAGS:
        response = client.post(
            f"/api/v1/projects/{project['projectId']}/walkthrough-runs/{run['runId']}/multilingual-runs",
            json={
                "targetLanguage": language_tag,
                "glossaryTerms": ["Atlas Output"],
                "requestedVoiceProvider": "mock",
            },
            headers={"Idempotency-Key": f"output-multilingual-p1-{language_tag}"},
        )

        assert response.status_code == 201, language_tag
        body = response.json()
        assert body["status"] == "COMPLETED"
        assert body["transcriptCorrectness"]["validationStatus"] == "PASSED"
        assert body["sourceScriptText"]
        assert body["translatedScriptText"]
        assert len(body["transcriptSegments"]) >= 2
        assert body["artifacts"]["metadata"]["contentBase64"]

        if language_tag != "en":
            assert body["translatedScriptText"] != body["sourceScriptText"]
        assert body["trace"]["sourceRunId"] == run["runId"]
        assert body["trace"]["sourceEvaluationId"] == run["evaluation"]["evaluationId"]
        assert body["trace"]["sourceContextRefIds"]
        assert body["trace"]["sourceClaimSupportIds"]

        metadata = json.loads(base64.b64decode(body["artifacts"]["metadata"]["contentBase64"]).decode("utf-8"))
        assert metadata["transcriptSegments"] == body["transcriptSegments"]
        assert metadata["transcriptCorrectness"] == body["transcriptCorrectness"]
        assert_successful_multilingual_contract(body, run=run)
        coverage_rows.append(
            {
                "languageTag": language_tag,
                "mutation": "positive",
                "result": "passed",
            }
        )

        for segment in body["transcriptSegments"]:
            assert segment["segmentId"]
            assert segment["sourceText"]
            assert segment["targetLanguage"] == language_tag
            assert segment["targetText"]
            if language_tag != "en":
                assert "Atlas Output" in segment["targetText"]
                assert "OUTPUT-SENTINEL-CP2" in segment["targetText"]
                assert "NarraTwin AI" not in segment["targetText"]
            assert segment["englishReferenceText"]
            assert segment["citationMarkers"]
            assert segment["citationIndexes"]
            assert segment["contextRefIds"]
            assert segment["claimSupportIds"]
            assert set(segment["contextRefIds"]).issubset(set(body["trace"]["sourceContextRefIds"]))
            assert set(segment["claimSupportIds"]).issubset(set(body["trace"]["sourceClaimSupportIds"]))
            assert segment["sourceRunId"] == run["runId"]
            assert segment["evaluationId"] == run["evaluation"]["evaluationId"]

        for mutation_name, mutated_segments in multilingual_false_pass_mutations(body):
            if language_tag == "en" and mutation_name in {"english-fallback", "wrong-script"}:
                coverage_rows.append(
                    {
                        "languageTag": language_tag,
                        "mutation": mutation_name,
                        "result": "not-applicable-for-source-language",
                    }
                )
                continue
            with pytest.raises(Exception):
                validate_multilingual_transcript_correctness(
                    language_tag=language_tag,
                    source_text=body["sourceScriptText"],
                    segments=mutated_segments,
                    source_run_id=run["runId"],
                    evaluation_id=run["evaluation"]["evaluationId"],
                    context_ref_ids=tuple(body["trace"]["sourceContextRefIds"]),
                    citation_indexes=tuple(body["trace"]["sourceCitationIndexes"]),
                    claim_support_ids=tuple(body["trace"]["sourceClaimSupportIds"]),
                )
            coverage_rows.append(
                {
                    "languageTag": language_tag,
                    "mutation": mutation_name,
                    "result": "failed-as-expected",
                }
            )
        for mutation_name, mutated_body in multilingual_response_false_pass_mutations(body):
            with pytest.raises(Exception):
                assert_successful_multilingual_contract(mutated_body, run=run)
            coverage_rows.append(
                {
                    "languageTag": language_tag,
                    "mutation": mutation_name,
                    "result": "failed-as-expected",
                }
            )

        summary[language_tag] = {
            "script": body["transcriptCorrectness"]["script"],
            "direction": body["transcriptCorrectness"]["direction"],
            "localDemoSupportStatus": "SUPPORTED",
            "apiOutputTestResult": "passed",
            "artifactTestResult": "passed",
            "representativeBrowserCoverageGroup": representative_browser_group(language_tag),
        }

    required_mutations = {
        "positive",
        "english-fallback",
        "partial",
        "single-segment-partial",
        "wrong-script",
        "missing-reference",
        "missing-source",
        "missing-target",
        "missing-binding",
        "missing-source-run-binding",
        "missing-evaluation-binding",
        "missing-claim-support-binding",
        "citation-drift",
        "glossary-forced-english-leakage",
        "metadata-only-success",
        "artifact-only-success",
    }
    for language_tag in PRIORITY1_LANGUAGE_TAGS:
        covered = {row["mutation"] for row in coverage_rows if row["languageTag"] == language_tag}
        assert required_mutations.issubset(covered)

    CHECKPOINT3_MULTILINGUAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (CHECKPOINT3_MULTILINGUAL_REPORT_DIR / "priority1-coverage-matrix.json").write_text(
        json.dumps(coverage_rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (CHECKPOINT3_MULTILINGUAL_REPORT_DIR / "checkpoint3a-multilingual-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def assert_successful_multilingual_contract(body: dict[str, Any], *, run: dict[str, Any]) -> None:
    assert body["status"] == "COMPLETED"
    assert body["transcriptCorrectness"]["validationStatus"] == "PASSED"
    correctness = validate_multilingual_transcript_correctness(
        language_tag=body["targetLanguage"],
        source_text=body["sourceScriptText"],
        segments=body["transcriptSegments"],
        source_run_id=run["runId"],
        evaluation_id=run["evaluation"]["evaluationId"],
        context_ref_ids=tuple(body["trace"]["sourceContextRefIds"]),
        citation_indexes=tuple(body["trace"]["sourceCitationIndexes"]),
        claim_support_ids=tuple(body["trace"]["sourceClaimSupportIds"]),
    )
    assert body["transcriptCorrectness"] == {
        "validationStatus": correctness.validation_status,
        "script": correctness.script,
        "direction": correctness.direction,
        "segmentCount": correctness.segment_count,
        "citationIndexes": list(correctness.citation_indexes),
    }
    metadata_artifact = body["artifacts"]["metadata"]
    metadata_text = base64.b64decode(metadata_artifact["contentBase64"], validate=True).decode("utf-8")
    assert metadata_artifact["checksum"] == checksum_text(metadata_text)
    metadata = json.loads(metadata_text)
    assert metadata["transcriptSegments"] == body["transcriptSegments"]
    assert metadata["transcriptCorrectness"] == body["transcriptCorrectness"]
    assert metadata["sourceScriptText"] == body["sourceScriptText"]
    assert metadata["translatedScriptText"] == body["translatedScriptText"]
    translated_script_artifact = body["artifacts"]["translatedScript"]
    translated_script_text = base64.b64decode(
        translated_script_artifact["contentBase64"],
        validate=True,
    ).decode("utf-8")
    assert translated_script_artifact["checksum"] == checksum_text(translated_script_text)
    assert translated_script_text == body["translatedScriptText"]
    if body["targetLanguage"] != "en":
        assert translated_script_text == " ".join(
            segment["targetText"] for segment in body["transcriptSegments"]
        )
    validate_multilingual_transcript_correctness(
        language_tag=metadata["targetLanguage"],
        source_text=metadata["sourceScriptText"],
        segments=metadata["transcriptSegments"],
        source_run_id=metadata["sourceRunId"],
        evaluation_id=metadata["sourceEvaluationId"],
        context_ref_ids=tuple(metadata["sourceContextRefIds"]),
        citation_indexes=tuple(metadata["sourceCitationIndexes"]),
        claim_support_ids=tuple(metadata["sourceClaimSupportIds"]),
    )


def multilingual_false_pass_mutations(body: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    original_segments = [dict(segment) for segment in body["transcriptSegments"]]
    first = dict(original_segments[0])
    english_fallback = [dict(segment, targetText=segment["sourceText"]) for segment in original_segments]
    partial: list[dict[str, Any]] = []
    single_segment_partial = [first]
    wrong_script = [dict(segment, targetText="romanized fallback [1]") for segment in original_segments]
    missing_reference = [dict(segment, englishReferenceText="") for segment in original_segments]
    missing_target = [dict(segment, targetText="") for segment in original_segments]
    citation_drift = [dict(first, citationMarkers=["[2]"], citationIndexes=[2])]
    missing_source = [dict(first, sourceText="")]
    missing_binding = [dict(first, contextRefIds=[])]
    missing_source_run_binding = [dict(first, sourceRunId="")]
    missing_evaluation_binding = [dict(first, evaluationId="")]
    missing_claim_support_binding = [dict(first, claimSupportIds=[])]
    glossary_forced_english_leakage = [dict(first, targetText=f"{first['targetText']} source chunks")]
    return [
        ("english-fallback", english_fallback),
        ("partial", partial),
        ("single-segment-partial", single_segment_partial),
        ("wrong-script", wrong_script),
        ("missing-reference", missing_reference),
        ("missing-target", missing_target),
        ("citation-drift", citation_drift),
        ("missing-source", missing_source),
        ("missing-binding", missing_binding),
        ("missing-source-run-binding", missing_source_run_binding),
        ("missing-evaluation-binding", missing_evaluation_binding),
        ("missing-claim-support-binding", missing_claim_support_binding),
        ("glossary-forced-english-leakage", glossary_forced_english_leakage),
    ]


def multilingual_response_false_pass_mutations(body: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    metadata_only_success = copy.deepcopy(body)
    metadata_only_success["transcriptSegments"] = []
    metadata_only_success["transcriptCorrectness"] = {
        **metadata_only_success["transcriptCorrectness"],
        "validationStatus": "PASSED",
    }

    artifact_only_success = copy.deepcopy(body)
    artifact_metadata = json.loads(
        base64.b64decode(artifact_only_success["artifacts"]["metadata"]["contentBase64"]).decode("utf-8")
    )
    artifact_metadata["transcriptSegments"] = []
    artifact_metadata["transcriptCorrectness"] = {
        **artifact_metadata["transcriptCorrectness"],
        "validationStatus": "PASSED",
    }
    artifact_only_success["artifacts"]["metadata"]["contentBase64"] = base64.b64encode(
        json.dumps(artifact_metadata, sort_keys=True).encode("utf-8")
    ).decode("ascii")
    return [
        ("metadata-only-success", metadata_only_success),
        ("artifact-only-success", artifact_only_success),
    ]


def representative_browser_group(language_tag: str) -> str:
    if language_tag == "hi":
        return "Devanagari"
    if language_tag in {"ar", "arz"}:
        return "RTL Arabic"
    if language_tag in {"he", "fa"}:
        return "RTL Hebrew/Persian"
    if language_tag in {"ja", "zh-Hans", "zh-Hant"}:
        return "CJK"
    if language_tag == "ko":
        return "Hangul"
    if language_tag in {"ru", "uk"}:
        return "Cyrillic"
    if language_tag == "th":
        return "Southeast Asia"
    return "Latin"
