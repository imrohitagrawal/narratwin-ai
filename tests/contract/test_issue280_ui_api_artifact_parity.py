from __future__ import annotations

import base64
import json
from typing import Any, cast

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests


def test_issue280_api_artifacts_report_and_ui_metadata_share_one_source_of_truth() -> None:
    reset_app_state_for_tests()
    client = TestClient(app)

    response = client.post(
        "/api/v1/checkpoint3/issue280/local-e2e-demo",
        json={
            "documents": [
                {
                    "filename": "atlas-demo.md",
                    "contentType": "text/markdown",
                    "markdown": "# Atlas Demo\n\nAtlas Demo explains adoption metrics, safety gates, and reviewer handoffs.",
                }
            ],
            "audience": "CUSTOMER",
            "depth": "DEEP",
            "targetLanguage": "he",
            "glossaryTerms": ["Atlas Demo"],
        },
        headers={"Idempotency-Key": "issue280-contract-parity", "X-Request-Id": "req-issue280-contract-parity"},
    )

    assert response.status_code == 201, response.text
    body = cast(dict[str, Any], response.json())
    metadata = json.loads(decode(body["artifacts"]["transcriptMetadata"]))
    report = body["correctnessReport"]

    assert body["request"]["audience"] == metadata["audience"] == report["audience"] == "CUSTOMER"
    assert body["request"]["depth"] == metadata["depth"] == report["depth"] == "DEEP"
    assert body["multilingual"]["targetLanguage"] == metadata["targetLanguage"] == report["targetLanguage"] == "he"
    assert body["multilingual"]["direction"] == metadata["direction"] == report["direction"] == "rtl"
    assert body["multilingual"]["preservedGlossaryTerms"] == metadata["preservedGlossaryTerms"]
    assert body["retrieval"]["contextRefs"] == metadata["contextRefs"]
    assert body["evaluation"]["claimSupports"] == metadata["claimSupports"]
    assert body["evaluation"]["evaluationId"] == report["evaluationId"]
    assert body["evaluation"]["evaluationChecksum"] == report["evaluationChecksum"]
    assert body["storage"]["outputChecksum"] == report["outputChecksum"]
    assert body["storage"]["metadataChecksum"] == report["metadataChecksum"]
    assert report["artifactBundleChecksum"] == body["storage"]["artifactBundleChecksum"]
    assert report["providerPosture"] == body["providerPosture"]


def decode(artifact: dict[str, Any]) -> str:
    return base64.b64decode(artifact["contentBase64"]).decode("utf-8")
