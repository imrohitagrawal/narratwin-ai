from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.rag.chunking import checksum_text
from scripts.eval.issue280_semantic_oracle import evaluate


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads(
    (ROOT / "docs/evals/issue280_semantic_repair_slice1.json").read_text(encoding="utf-8")
)
PATH = "/api/v1/checkpoint3/issue280/local-e2e-demo"


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_app_state_for_tests()


def request_body(
    *,
    audience: str,
    target_language: str = "es",
    depth: str = "STANDARD",
    markdown: str | None = None,
) -> dict[str, Any]:
    return {
        "documents": [
            {
                "filename": MANIFEST["fixture"]["filename"],
                "contentType": MANIFEST["fixture"]["contentType"],
                "markdown": markdown if markdown is not None else MANIFEST["fixture"]["markdown"],
            }
        ],
        "audience": audience,
        "depth": depth,
        "targetLanguage": target_language,
        "glossaryTerms": MANIFEST["authority"]["glossaryTerms"],
    }


def post(body: dict[str, Any], key: str) -> dict[str, Any]:
    response = TestClient(app).post(
        PATH,
        json=body,
        headers={"Idempotency-Key": key, "X-Request-Id": f"request-{key}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def observation(
    row: dict[str, Any], response: dict[str, Any], replay: dict[str, Any]
) -> dict[str, Any]:
    metadata = json.loads(decode(response["artifacts"]["transcriptMetadata"]))
    script = decode(response["artifacts"]["translatedScript"])
    api_segments = oracle_segments(response["multilingual"]["segments"])
    artifact_segments = oracle_segments(metadata["segments"])
    return {
        "rowId": row["rowId"],
        "audience": response["request"]["audience"],
        "depth": response["request"]["depth"],
        "targetLanguage": response["request"]["targetLanguage"],
        "runId": response["multilingual"]["multilingualRunId"],
        "outputId": response["storage"]["outputId"],
        "sourceChecksum": response["retrieval"]["contextRefs"][0]["sourceChecksum"],
        "apiSegments": api_segments,
        "visibleTargetTexts": [
            segment["targetText"] for segment in response["multilingual"]["segments"]
        ],
        "artifactScriptText": script,
        "artifactSegments": artifact_segments,
        "claimSupports": oracle_supports(response["evaluation"]["claimSupports"]),
        "unsupportedClaimCount": response["evaluation"]["unsupportedClaimCount"],
        "stored": response["storage"]["stored"],
        "replayed": replay["session"]["replayed"],
    }


def oracle_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = {
        "propositionId",
        "sourceText",
        "targetText",
        "citationIndexes",
        "contextRefIds",
        "claimSupportIds",
    }
    return [{key: segment[key] for key in keys} for segment in segments]


def oracle_supports(supports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = {
        "claimSupportId",
        "propositionId",
        "supportStatus",
        "contextRefId",
        "citationIndex",
    }
    return [{key: support[key] for key in keys} for support in supports]


def test_current_runtime_red_reproduces_visible_target_audience_collapse() -> None:
    target_bodies = {
        tuple(
            segment["targetText"]
            for segment in post(
                request_body(audience=row["audience"]),
                f"issue317-collapse-{row['audience'].lower()}",
            )["multilingual"]["segments"]
        )
        for row in MANIFEST["mandatoryRows"]
    }
    assert len(target_bodies) == 7


def test_current_runtime_red_requires_semantic_frame_and_oracle_pass() -> None:
    observations: list[dict[str, Any]] = []
    target_bodies: set[tuple[str, ...]] = set()
    for row in MANIFEST["mandatoryRows"]:
        key = f"issue317-{row['audience'].lower()}"
        response = post(request_body(audience=row["audience"]), key)
        replay = post(request_body(audience=row["audience"]), key)
        assert response["generated"]["semanticFrameVersion"] == "Issue280SemanticFrameV1"
        assert [
            segment["propositionId"] for segment in response["multilingual"]["segments"]
        ] == row["requiredPropositionIds"]
        target_bodies.add(
            tuple(segment["targetText"] for segment in response["multilingual"]["segments"])
        )
        observations.append(observation(row, response, replay))

    assert len(target_bodies) == 7
    result = evaluate(
        MANIFEST,
        {"schemaVersion": "Issue280SemanticOracleObservationsV1", "rows": observations},
    )
    assert result.classification == "SEMANTIC_PASS"
    assert result.metrics == MANIFEST["thresholds"]


def test_semantic_route_passes_the_exact_compiled_frame_to_one_renderer_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.app import issue280

    original_compile = issue280._compile_semantic_frame
    original_render = issue280._render_grounded_script
    captured: dict[str, Any] = {"calls": 0}

    def compile_spy(**kwargs: Any) -> issue280.Issue280SemanticFrame | None:
        frame = original_compile(**kwargs)
        captured["compiled_frame"] = frame
        return frame

    def render_spy(
        *,
        facts: tuple[issue280.Issue280GroundedFact, ...],
        audience: str,
        depth: str,
        semantic_frame: issue280.Issue280SemanticFrame,
    ) -> str:
        captured["calls"] += 1
        captured["rendered_frame"] = semantic_frame
        return original_render(
            facts=facts,
            audience=audience,
            depth=depth,
            semantic_frame=semantic_frame,
        )

    monkeypatch.setattr(issue280, "_compile_semantic_frame", compile_spy)
    monkeypatch.setattr(issue280, "_render_grounded_script", render_spy)

    response = TestClient(app).post(
        PATH,
        json=request_body(audience="ENGINEER"),
        headers={"Idempotency-Key": "issue321-exact-semantic-frame"},
    )

    assert response.status_code == 201, response.text
    assert captured["calls"] == 1
    assert captured["compiled_frame"] is not None
    assert captured["rendered_frame"] is captured["compiled_frame"]
    assert captured["rendered_frame"].version == "Issue280SemanticFrameV1"


def test_internal_semantic_renderer_type_error_is_safe_and_never_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.app import issue280

    calls = 0

    def broken_renderer(
        *,
        facts: tuple[issue280.Issue280GroundedFact, ...],
        audience: str,
        depth: str,
        semantic_frame: issue280.Issue280SemanticFrame,
    ) -> str:
        nonlocal calls
        del facts, audience, depth, semantic_frame
        calls += 1
        raise TypeError("private-issue321-renderer-marker")

    monkeypatch.setattr(issue280, "_render_grounded_script", broken_renderer)

    response = TestClient(app).post(
        PATH,
        json=request_body(audience="ENGINEER"),
        headers={"Idempotency-Key": "issue321-internal-type-error"},
    )

    assert calls == 1
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ISSUE280_INTERNAL_ERROR_SAFE"
    assert "private-issue321-renderer-marker" not in response.text
    assert "correctnessReport" not in response.text


@pytest.mark.parametrize(
    ("override", "value"),
    [("targetLanguage", "hi"), ("depth", "DEEP")],
)
def test_semantic_repair_slice_refuses_unsupported_language_and_depth(
    override: str, value: str
) -> None:
    body = request_body(audience="ENGINEER")
    body[override] = value
    response = TestClient(app).post(
        PATH,
        json=body,
        headers={"Idempotency-Key": f"issue317-refuse-{override}"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ISSUE280_TRANSLATION_REFUSED"
    assert "correctnessReport" not in response.text


def test_semantic_repair_slice_refuses_unsupported_clause_instead_of_false_success() -> None:
    markdown = (
        MANIFEST["fixture"]["markdown"]
        + "\n## Unsupported\n\nThe product predicts revenue growth.\n"
    )
    response = TestClient(app).post(
        PATH,
        json=request_body(audience="CUSTOMER", markdown=markdown),
        headers={"Idempotency-Key": "issue317-refuse-clause"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ISSUE280_TRANSLATION_REFUSED"
    assert "correctnessReport" not in response.text


def test_manifest_source_checksum_is_the_runtime_source_identity() -> None:
    response = post(request_body(audience="RECRUITER"), "issue317-source-identity")
    assert {item["sourceChecksum"] for item in response["retrieval"]["contextRefs"]} == {
        checksum_text(MANIFEST["fixture"]["markdown"])
    }


def decode(artifact: dict[str, Any]) -> str:
    return base64.b64decode(artifact["contentBase64"]).decode("utf-8")
