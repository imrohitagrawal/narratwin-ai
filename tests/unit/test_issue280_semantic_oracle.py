from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.eval.issue280_semantic_oracle import OracleContractError, evaluate, validate_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs/evals/issue280_semantic_repair_slice1.json"


@pytest.fixture
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def valid_observations(manifest: dict[str, Any]) -> dict[str, Any]:
    propositions = {item["id"]: item for item in manifest["propositions"]}
    rows: list[dict[str, Any]] = []
    for row in manifest["mandatoryRows"]:
        segments: list[dict[str, Any]] = []
        supports: list[dict[str, Any]] = []
        for proposition_id in row["requiredPropositionIds"]:
            proposition = propositions[proposition_id]
            support_id = f"support-{row['rowId']}-{proposition_id}"
            context_id = f"context-{proposition_id}"
            segments.append(
                {
                    "propositionId": proposition_id,
                    "sourceText": proposition["sourceText"],
                    "targetText": f"{proposition['targetClause']} [{proposition['citationIndex']}].",
                    "citationIndexes": [proposition["citationIndex"]],
                    "contextRefIds": [context_id],
                    "claimSupportIds": [support_id],
                }
            )
            supports.append(
                {
                    "claimSupportId": support_id,
                    "propositionId": proposition_id,
                    "supportStatus": "SUPPORTED",
                    "contextRefId": context_id,
                    "citationIndex": proposition["citationIndex"],
                }
            )
        target_texts = [segment["targetText"] for segment in segments]
        rows.append(
            {
                "rowId": row["rowId"],
                "audience": row["audience"],
                "depth": "STANDARD",
                "targetLanguage": "es",
                "runId": f"run-{row['rowId']}",
                "outputId": f"output-{row['rowId']}",
                "sourceChecksum": "sha256:fixture-source",
                "apiSegments": segments,
                "visibleTargetTexts": target_texts,
                "artifactScriptText": "\n".join(target_texts),
                "artifactSegments": copy.deepcopy(segments),
                "claimSupports": supports,
                "unsupportedClaimCount": 0,
                "stored": True,
                "replayed": True,
            }
        )
    return {"schemaVersion": "Issue280SemanticOracleObservationsV1", "rows": rows}


def test_oracle_accepts_only_the_complete_independent_manifest(manifest: dict[str, Any]) -> None:
    assert validate_manifest(manifest) is manifest
    weakened = copy.deepcopy(manifest)
    weakened["thresholds"]["essentialPropositionRecall"] = 0.9
    with pytest.raises(OracleContractError, match="thresholds:weakened"):
        validate_manifest(weakened)


def test_oracle_computes_semantic_pass_for_all_mandatory_rows(
    manifest: dict[str, Any], valid_observations: dict[str, Any]
) -> None:
    result = evaluate(manifest, valid_observations)
    assert result.classification == "SEMANTIC_PASS"
    assert result.failures == ()
    assert result.metrics == manifest["thresholds"]


@pytest.mark.parametrize(
    ("mutation", "failure_fragment"),
    [
        ("missing-essential", "essentialPropositionRecall"),
        ("missing-audience-emphasis", "audienceRequiredEmphasisRecall"),
        ("unsupported-proposition", "unsupportedPropositionCount"),
        ("incorrect-citation-binding", "citationSupportPrecision"),
        ("glossary-loss", "glossaryLossCount"),
        ("english-fallback", "targetScriptViolationCount"),
        ("surface-disagreement", "surface-disagreement"),
        ("source-identity-disagreement", "source-identity"),
    ],
)
def test_oracle_rejects_semantic_and_surface_false_passes(
    manifest: dict[str, Any],
    valid_observations: dict[str, Any],
    mutation: str,
    failure_fragment: str,
) -> None:
    observations = copy.deepcopy(valid_observations)
    row = observations["rows"][0]
    if mutation == "missing-essential":
        row["apiSegments"].pop(0)
        row["visibleTargetTexts"].pop(0)
        row["artifactSegments"].pop(0)
        row["artifactScriptText"] = "\n".join(row["visibleTargetTexts"])
        row["claimSupports"].pop(0)
    elif mutation == "missing-audience-emphasis":
        row["apiSegments"].pop()
        row["visibleTargetTexts"].pop()
        row["artifactSegments"].pop()
        row["artifactScriptText"] = "\n".join(row["visibleTargetTexts"])
        row["claimSupports"].pop()
    elif mutation == "unsupported-proposition":
        bad = copy.deepcopy(row["apiSegments"][0])
        bad["targetText"] = "Una afirmación inventada sin respaldo [1]."
        row["apiSegments"].append(bad)
        row["visibleTargetTexts"].append(bad["targetText"])
        row["artifactSegments"].append(copy.deepcopy(bad))
        row["artifactScriptText"] = "\n".join(row["visibleTargetTexts"])
    elif mutation == "incorrect-citation-binding":
        row["apiSegments"][0]["citationIndexes"] = [9]
        row["artifactSegments"][0]["citationIndexes"] = [9]
    elif mutation == "glossary-loss":
        for surface in (row["apiSegments"], row["artifactSegments"]):
            surface[0]["targetText"] = surface[0]["targetText"].replace(
                "NarraTwin", "la plataforma"
            )
        row["visibleTargetTexts"][0] = row["apiSegments"][0]["targetText"]
        row["artifactScriptText"] = "\n".join(row["visibleTargetTexts"])
    elif mutation == "english-fallback":
        for surface in (row["apiSegments"], row["artifactSegments"]):
            surface[0]["targetText"] = "Local mock conversion: source segment protected term [1]."
        row["visibleTargetTexts"][0] = row["apiSegments"][0]["targetText"]
        row["artifactScriptText"] = "\n".join(row["visibleTargetTexts"])
    elif mutation == "surface-disagreement":
        row["visibleTargetTexts"][0] = "Texto visible diferente [1]."
    else:
        observations["rows"][1]["sourceChecksum"] = "sha256:different-source"

    result = evaluate(manifest, observations)
    assert result.classification == "FAILED"
    assert failure_fragment in " ".join(result.failures)


def test_oracle_rejects_identical_and_prefix_only_audience_bodies(
    manifest: dict[str, Any], valid_observations: dict[str, Any]
) -> None:
    identical = copy.deepcopy(valid_observations)
    first = identical["rows"][0]
    for row in identical["rows"][1:]:
        row["apiSegments"] = copy.deepcopy(first["apiSegments"])
        row["visibleTargetTexts"] = list(first["visibleTargetTexts"])
        row["artifactSegments"] = copy.deepcopy(first["artifactSegments"])
        row["artifactScriptText"] = first["artifactScriptText"]
        row["claimSupports"] = copy.deepcopy(first["claimSupports"])
    result = evaluate(manifest, identical)
    assert result.classification == "FAILED"
    assert result.metrics["pairwiseAudienceCollapseCount"] == 21

    prefix_only = copy.deepcopy(identical)
    for index, row in enumerate(prefix_only["rows"]):
        prefix = f"Audiencia {index + 1}: "
        row["visibleTargetTexts"] = [prefix + text for text in row["visibleTargetTexts"]]
        row["apiSegments"] = copy.deepcopy(first["apiSegments"])
        row["artifactSegments"] = copy.deepcopy(row["apiSegments"])
        row["artifactScriptText"] = "\n".join(
            row["apiSegments"][item]["targetText"] for item in range(3)
        )
    assert evaluate(manifest, prefix_only).classification == "FAILED"


def test_oracle_rejects_caller_scope_row_omission_and_duplicate_rows(
    manifest: dict[str, Any], valid_observations: dict[str, Any]
) -> None:
    omitted = copy.deepcopy(valid_observations)
    omitted["rows"].pop()
    result = evaluate(manifest, omitted)
    assert result.classification == "FAILED"
    assert result.metrics["mandatoryRowCoverage"] < 1.0

    duplicated = copy.deepcopy(valid_observations)
    duplicated["rows"].append(copy.deepcopy(duplicated["rows"][0]))
    with pytest.raises(OracleContractError, match="duplicate-row"):
        evaluate(manifest, duplicated)


def test_oracle_rejects_unknown_fields_and_author_editable_verdict(
    manifest: dict[str, Any], valid_observations: dict[str, Any]
) -> None:
    unknown = copy.deepcopy(valid_observations)
    unknown["rows"][0]["optional"] = True
    with pytest.raises(OracleContractError, match="closed-schema"):
        evaluate(manifest, unknown)

    verdict = copy.deepcopy(valid_observations)
    verdict["verdict"] = "SEMANTIC_PASS"
    with pytest.raises(OracleContractError, match="closed-schema"):
        evaluate(manifest, verdict)


def test_runtime_and_oracle_sources_cannot_import_each_other() -> None:
    runtime = (ROOT / "backend/app/issue280.py").read_text(encoding="utf-8")
    oracle = (ROOT / "scripts/eval/issue280_semantic_oracle.py").read_text(encoding="utf-8")
    assert "issue280_semantic_repair_slice1.json" not in runtime
    assert "issue280_semantic_oracle" not in runtime
    assert "backend.app.issue280" not in oracle
