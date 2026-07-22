from __future__ import annotations

# ruff: noqa: E402

import copy
import os
import re
from collections.abc import Iterator
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
from backend.app.rag.models import GeneratedScript, RetrievedContext, ScriptClaim
from backend.app.rag.providers import MockLLMProvider
from backend.app.stage4 import stage4_service


LUMEN_LANGUAGE_FACTS = (
    "Lumen Guide LANGUAGE-SENTINEL-CP3 is a fictional accessibility checklist coach for documentation teams.",
    "The walkthrough is written for engineers who need technical handoff steps.",
    "Lumen Guide helps teams convert release notes into clear onboarding walkthroughs.",
    "Lumen Guide requires each walkthrough to explain the workflow in plain, audience-appropriate language with citations.",
)
BEACON_LANGUAGE_FACT = "Beacon Language BEACON-LANGUAGE-CP3 is a fictional support digest for neighborhood teams."

LUMEN_LANGUAGE_KNOWLEDGE = (
    "# Lumen Language\n\n" + "\n".join(LUMEN_LANGUAGE_FACTS) + "\n"
).encode()
BEACON_LANGUAGE_KNOWLEDGE = (
    "# Beacon Language\n\n"
    f"{BEACON_LANGUAGE_FACT}\n"
    "Beacon Language uses digest wording that must not appear in Lumen Guide walkthroughs.\n"
).encode()

MIN_CP3_WORDS = 35
MIN_CP3_CITED_SENTENCES = 3
LANGUAGE_QUALITY_FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)\b(todo|tbd|placeholder|lorem ipsum|debug|internal)\b"),
    re.compile(r"(?i)\b(trace[_ -]?id|run[_ -]?id|contextrefs|claimsupports|acceptedscripttext)\b"),
    re.compile(r"(?i)(provider payload|raw prompt|raw upload|canned success|static snapshot)"),
    re.compile(r"\{\{|\}\}"),
)


@pytest.fixture(autouse=True)
def local_only_language_quality_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()
    yield
    stage4_service.llm = MockLLMProvider()
    reset_app_state_for_tests()


class StructuredLanguageQualityProvider:
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
        context = next(
            (
                candidate
                for candidate in retrieved_context
                if all(fact in candidate.chunk.text for fact in LUMEN_LANGUAGE_FACTS)
            ),
            retrieved_context[0],
        )
        parts: list[str] = []
        claims: list[ScriptClaim] = []
        cursor = 0
        for index, fact in enumerate(LUMEN_LANGUAGE_FACTS, start=1):
            sentence = f"{fact} [1]"
            parts.append(sentence)
            claims.append(
                ScriptClaim(
                    claim_id=f"claim_language_{index:03d}",
                    text=fact,
                    citation_index=1,
                    chunk_id=context.chunk.chunk_id,
                    script_span_start=cursor,
                    script_span_end=cursor + len(sentence),
                )
            )
            cursor += len(sentence) + 1
        return GeneratedScript(text=" ".join(parts), claims=claims)


def create_project(client: TestClient, *, prefix: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Synthetic C3A-CP3 language-quality fixture.",
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
        json={"approvalStatus": "APPROVED", "reviewNote": "Approved synthetic CP3 language-quality knowledge."},
        headers={"Idempotency-Key": f"{prefix}-approval"},
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


def ingest_document(client: TestClient, *, prefix: str, project_id: str, document_id: str) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers={"Idempotency-Key": f"{prefix}-ingest"},
    )
    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["status"] == "COMPLETED"
    assert ingestion["chunkCount"] > 0
    assert ingestion["embeddingCount"] == ingestion["chunkCount"]


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


def runtime_language_run(client: TestClient) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    project, document = prepare_approved_project(
        client,
        prefix="language-lumen",
        name="Lumen Guide",
        filename="lumen_language.md",
        content=LUMEN_LANGUAGE_KNOWLEDGE,
    )
    prepare_approved_project(
        client,
        prefix="language-beacon",
        name="Beacon Language",
        filename="beacon_language.md",
        content=BEACON_LANGUAGE_KNOWLEDGE,
    )
    stage4_service.llm = cast(Any, StructuredLanguageQualityProvider())
    prompt = "Create a grounded walkthrough for Lumen Guide using only approved source facts."
    run = generate_walkthrough(
        client,
        prefix="language-lumen",
        project_id=project["projectId"],
        prompt=prompt,
    )
    replay = generate_walkthrough(
        client,
        prefix="language-lumen",
        project_id=project["projectId"],
        prompt=prompt,
    )
    assert replay == run
    return project, document, replay


def assert_runtime_language_quality_contract(
    run: dict[str, Any],
    *,
    project_id: str,
    document: dict[str, Any],
) -> None:
    script = run.get("acceptedScriptText")
    assert isinstance(script, str), "language quality requires accepted runtime output"
    assert run.get("status") == "COMPLETED"
    assert run.get("evaluationStatus") == "PASSED"
    assert run.get("provider") == {"provider": "mock", "providerMode": "LOCAL"}
    assert isinstance(run.get("runId"), str) and run["runId"].startswith("run_"), "runtime runId is required"
    assert isinstance(run.get("createdAt"), str)
    assert run.get("trace", {}).get("estimatedCost") == 0
    assert isinstance(run.get("trace", {}).get("traceId"), str)

    words = re.findall(r"[A-Za-z0-9]+", script)
    assert len(words) >= MIN_CP3_WORDS, "walkthrough output is empty or trivially short"
    cited_sentences = re.findall(r"[.!?]\s+\[\d+\](?=\s|$)", script)
    assert len(cited_sentences) >= MIN_CP3_CITED_SENTENCES, "walkthrough lacks coherent cited structure"
    assert "engineers" in script.lower()
    assert "technical" in script.lower()
    for fact in LUMEN_LANGUAGE_FACTS:
        assert fact in script
    assert BEACON_LANGUAGE_FACT not in script

    for pattern in LANGUAGE_QUALITY_FORBIDDEN_PATTERNS:
        assert not pattern.search(script), "walkthrough leaks placeholder, boilerplate, or internal/debug text"

    marker_matches = tuple(re.finditer(r"\[(\d+)\]", script))
    assert marker_matches, "walkthrough must include readable citation markers"
    assert "[[" not in script and "]]" not in script
    for marker in marker_matches:
        assert marker.start() > 0 and script[marker.start() - 1].isspace(), "citation marker harms readability"
        assert marker.end() == len(script) or script[marker.end()].isspace(), "citation marker is malformed"

    context_refs = run.get("contextRefs")
    evaluation = run.get("evaluation")
    assert isinstance(context_refs, list) and context_refs, "runtime contextRefs are required"
    assert isinstance(evaluation, dict), "runtime evaluation evidence is required"
    assert evaluation.get("evaluationStatus") == "PASSED"
    assert evaluation.get("unsupportedClaimCount") == 0
    assert isinstance(evaluation.get("evaluationId"), str)
    claim_supports = evaluation.get("claimSupports")
    assert isinstance(claim_supports, list) and claim_supports, "claimSupports are required"
    supported_citation_indexes = {
        support["citationIndex"]
        for support in claim_supports
        if support.get("supportStatus") == "SUPPORTED"
    }
    assert {int(marker.group(1)) for marker in marker_matches} <= supported_citation_indexes

    for context in context_refs:
        assert context["projectId"] == project_id
        assert context["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["projectId"] == project_id
        assert context["evidenceSnapshot"]["documentId"] == document["documentId"]
        assert context["evidenceSnapshot"]["sourceDocumentChecksum"] == document["checksum"]
        assert "BEACON-LANGUAGE-CP3" not in context["evidenceSnapshot"]["redactedExcerpt"]
    for support in claim_supports:
        assert support["projectId"] == project_id
        assert support["documentId"] == document["documentId"]
        assert support["supportStatus"] == "SUPPORTED"
        assert support["evidenceSnapshot"]["projectId"] == project_id
        assert support["evidenceSnapshot"]["documentId"] == document["documentId"]


def mutated_run_with_script(run: dict[str, Any], script: str) -> dict[str, Any]:
    mutated = copy.deepcopy(run)
    mutated["acceptedScriptText"] = script
    return mutated


def test_checkpoint3_language_quality_executes_runtime_api_output_path() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)

    assert_runtime_language_quality_contract(
        run,
        project_id=project["projectId"],
        document=document,
    )
    ops = client.get("/api/v1/ops/status")
    assert ops.status_code == 200
    assert ops.json()["durability"]["stage4"]["recordCounts"]["walkthroughRuns"] == 1


def test_checkpoint3_language_quality_rejects_grounded_placeholder_boilerplate_output() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)
    placeholder_run = mutated_run_with_script(
        run,
        "TODO PLACEHOLDER: " + cast(str, run["acceptedScriptText"]),
    )

    with pytest.raises(AssertionError, match="placeholder"):
        assert_runtime_language_quality_contract(
            placeholder_run,
            project_id=project["projectId"],
            document=document,
        )


def test_checkpoint3_language_quality_rejects_trivially_short_citation_output() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)
    short_run = mutated_run_with_script(run, f"{LUMEN_LANGUAGE_FACTS[0]} [1]")

    with pytest.raises(AssertionError, match="trivially short|coherent cited structure"):
        assert_runtime_language_quality_contract(
            short_run,
            project_id=project["projectId"],
            document=document,
        )


def test_checkpoint3_language_quality_rejects_debug_or_internal_leakage() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)
    leaked_run = mutated_run_with_script(
        run,
        cast(str, run["acceptedScriptText"]) + " Debug trace_id=trace_private contextRefs={'chunk': 'raw'}.",
    )

    with pytest.raises(AssertionError, match="placeholder, boilerplate, or internal/debug"):
        assert_runtime_language_quality_contract(
            leaked_run,
            project_id=project["projectId"],
            document=document,
        )


def test_checkpoint3_language_quality_rejects_malformed_citation_placement() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)
    malformed_run = mutated_run_with_script(
        run,
        cast(str, run["acceptedScriptText"]).replace(" [1]", "[1]", 1),
    )

    with pytest.raises(AssertionError, match="citation marker harms readability"):
        assert_runtime_language_quality_contract(
            malformed_run,
            project_id=project["projectId"],
            document=document,
        )


def test_checkpoint3_language_quality_rejects_cross_project_or_unsupported_language_insertions() -> None:
    client = TestClient(app)
    project, document, run = runtime_language_run(client)
    cross_project_run = mutated_run_with_script(
        run,
        cast(str, run["acceptedScriptText"]) + f" {BEACON_LANGUAGE_FACT} [1]",
    )

    with pytest.raises(AssertionError):
        assert_runtime_language_quality_contract(
            cross_project_run,
            project_id=project["projectId"],
            document=document,
        )


def test_checkpoint3_language_quality_rejects_style_text_without_runtime_api_evidence() -> None:
    style_only = {
        "acceptedScriptText": (
            f"{LUMEN_LANGUAGE_FACTS[0]} [1] "
            f"{LUMEN_LANGUAGE_FACTS[1]} [1] "
            f"{LUMEN_LANGUAGE_FACTS[2]} [1] "
            f"{LUMEN_LANGUAGE_FACTS[3]} [1]"
        ),
        "status": "COMPLETED",
        "evaluationStatus": "PASSED",
        "provider": {"provider": "mock", "providerMode": "LOCAL"},
        "trace": {"estimatedCost": 0, "traceId": "trace_static"},
        "createdAt": "2026-07-22T00:00:00Z",
    }

    with pytest.raises(AssertionError, match="runtime runId"):
        assert_runtime_language_quality_contract(
            style_only,
            project_id="proj_static",
            document={"documentId": "doc_static", "checksum": "sha256:static"},
        )
