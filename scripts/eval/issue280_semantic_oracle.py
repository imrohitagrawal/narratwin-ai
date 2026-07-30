#!/usr/bin/env python3
"""Independent semantic oracle for the Issue #280 slice-1 cohort."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "docs/evals/issue280_semantic_repair_slice1.json"

MANIFEST_KEYS = {
    "schemaVersion",
    "authority",
    "fixture",
    "propositions",
    "mandatoryRows",
    "thresholds",
    "disallowedTargetText",
}
AUTHORITY_KEYS = {
    "controllingIssue",
    "architectureDecision",
    "dataClass",
    "language",
    "depth",
    "glossaryTerms",
}
FIXTURE_KEYS = {"fixtureId", "filename", "contentType", "markdown"}
PROPOSITION_KEYS = {
    "id",
    "sourceText",
    "targetClause",
    "citationIndex",
    "essential",
    "audience",
    "depthRoles",
    "glossaryTerms",
}
ROW_KEYS = {"rowId", "audience", "requiredPropositionIds"}
THRESHOLD_KEYS = {
    "essentialPropositionRecall",
    "unsupportedPropositionCount",
    "citationSupportPrecision",
    "audienceRequiredEmphasisRecall",
    "pairwiseAudienceCollapseCount",
    "depthRoleViolationCount",
    "glossaryLossCount",
    "targetScriptViolationCount",
    "mandatoryRowCoverage",
}
OBSERVATION_KEYS = {"schemaVersion", "rows"}
OBSERVATION_ROW_KEYS = {
    "rowId",
    "audience",
    "depth",
    "targetLanguage",
    "runId",
    "outputId",
    "sourceChecksum",
    "apiSegments",
    "visibleTargetTexts",
    "artifactScriptText",
    "artifactSegments",
    "claimSupports",
    "unsupportedClaimCount",
    "stored",
    "replayed",
}
SEGMENT_KEYS = {
    "propositionId",
    "sourceText",
    "targetText",
    "citationIndexes",
    "contextRefIds",
    "claimSupportIds",
}
SUPPORT_KEYS = {
    "claimSupportId",
    "propositionId",
    "supportStatus",
    "contextRefId",
    "citationIndex",
}


class OracleContractError(ValueError):
    """Raised when the oracle contract or observation envelope is malformed."""


@dataclass(frozen=True)
class OracleResult:
    classification: str
    metrics: dict[str, float | int]
    row_metrics: dict[str, dict[str, float | int]]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": "Issue280SemanticOracleResultV1",
            "classification": self.classification,
            "metrics": self.metrics,
            "rowMetrics": self.row_metrics,
            "failures": list(self.failures),
        }


def _require_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise OracleContractError(f"{label}:closed-schema")
    return value


def validate_manifest(value: Any) -> dict[str, Any]:
    manifest = _require_keys(value, MANIFEST_KEYS, "manifest")
    if manifest["schemaVersion"] != "Issue280SemanticRepairSlice1ManifestV1":
        raise OracleContractError("manifest:schema-version")
    authority = _require_keys(manifest["authority"], AUTHORITY_KEYS, "authority")
    fixture = _require_keys(manifest["fixture"], FIXTURE_KEYS, "fixture")
    if authority != {
        "controllingIssue": 317,
        "architectureDecision": "ADR-0044",
        "dataClass": "public-safe synthetic only",
        "language": "es",
        "depth": "STANDARD",
        "glossaryTerms": ["NarraTwin"],
    }:
        raise OracleContractError("authority:identity")
    if fixture["contentType"] != "text/markdown" or not fixture["markdown"].strip():
        raise OracleContractError("fixture:invalid")
    propositions = manifest["propositions"]
    rows = manifest["mandatoryRows"]
    if not isinstance(propositions, list) or not isinstance(rows, list):
        raise OracleContractError("manifest:list-shape")
    for proposition in propositions:
        _require_keys(proposition, PROPOSITION_KEYS, "proposition")
    for row in rows:
        _require_keys(row, ROW_KEYS, "mandatory-row")
    proposition_ids = [item["id"] for item in propositions]
    row_ids = [item["rowId"] for item in rows]
    audiences = [item["audience"] for item in rows]
    if len(proposition_ids) != len(set(proposition_ids)) or len(row_ids) != len(set(row_ids)):
        raise OracleContractError("manifest:duplicate-id")
    if len(rows) != 7 or len(audiences) != len(set(audiences)):
        raise OracleContractError("manifest:mandatory-row-set")
    if any(set(row["requiredPropositionIds"]) - set(proposition_ids) for row in rows):
        raise OracleContractError("manifest:unknown-proposition")
    thresholds = _require_keys(manifest["thresholds"], THRESHOLD_KEYS, "thresholds")
    expected_thresholds = {
        "essentialPropositionRecall": 1.0,
        "unsupportedPropositionCount": 0,
        "citationSupportPrecision": 1.0,
        "audienceRequiredEmphasisRecall": 1.0,
        "pairwiseAudienceCollapseCount": 0,
        "depthRoleViolationCount": 0,
        "glossaryLossCount": 0,
        "targetScriptViolationCount": 0,
        "mandatoryRowCoverage": 1.0,
    }
    if thresholds != expected_thresholds:
        raise OracleContractError("thresholds:weakened")
    if not isinstance(manifest["disallowedTargetText"], list):
        raise OracleContractError("manifest:disallowed-text-shape")
    return manifest


def _normalized(text: str) -> str:
    text = re.sub(r"\s*\[\d+\]\s*\.?$", "", text.strip())
    text = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"[^\wáéíóúüñ]+", " ", text, flags=re.UNICODE).strip()


def _observed_proposition(
    segment: dict[str, Any], propositions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    target = _normalized(str(segment["targetText"]))
    matches = [
        item
        for item in propositions
        if item["id"] == segment["propositionId"]
        and _normalized(item["sourceText"]) == _normalized(str(segment["sourceText"]))
        and _normalized(item["targetClause"]) == target
    ]
    return matches[0] if len(matches) == 1 else None


def _source_proposition(
    segment: dict[str, Any], propositions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    matches = [
        item
        for item in propositions
        if item["id"] == segment["propositionId"]
        and _normalized(item["sourceText"]) == _normalized(str(segment["sourceText"]))
    ]
    return matches[0] if len(matches) == 1 else None


def evaluate(manifest_value: Any, observation_value: Any) -> OracleResult:
    manifest = validate_manifest(manifest_value)
    observations = _require_keys(observation_value, OBSERVATION_KEYS, "observations")
    if observations["schemaVersion"] != "Issue280SemanticOracleObservationsV1":
        raise OracleContractError("observations:schema-version")
    rows = observations["rows"]
    if not isinstance(rows, list):
        raise OracleContractError("observations:rows-shape")
    for row in rows:
        _require_keys(row, OBSERVATION_ROW_KEYS, "observation-row")
    expected_rows = {row["rowId"]: row for row in manifest["mandatoryRows"]}
    observed_ids = [row["rowId"] for row in rows]
    if len(observed_ids) != len(set(observed_ids)):
        raise OracleContractError("observations:duplicate-row")

    propositions = manifest["propositions"]
    essential_ids = {item["id"] for item in propositions if item["essential"]}
    failures: list[str] = []
    row_metrics: dict[str, dict[str, float | int]] = {}
    semantic_sets: dict[str, frozenset[str]] = {}

    for row in rows:
        row_id = row["rowId"]
        expected = expected_rows.get(row_id)
        if expected is None:
            failures.append(f"{row_id}:unexpected-row")
            continue
        if (
            row["audience"] != expected["audience"]
            or row["depth"] != "STANDARD"
            or row["targetLanguage"] != "es"
        ):
            failures.append(f"{row_id}:axis-mismatch")
        segments = row["apiSegments"]
        supports = row["claimSupports"]
        if not isinstance(segments, list) or not isinstance(supports, list):
            raise OracleContractError(f"{row_id}:list-shape")
        for segment in segments:
            _require_keys(segment, SEGMENT_KEYS, "segment")
        for support in supports:
            _require_keys(support, SUPPORT_KEYS, "claim-support")

        observed: list[str] = []
        supported_citations = 0
        script_violations = 0
        glossary_loss = 0
        depth_violations = 0
        support_by_id = {item["claimSupportId"]: item for item in supports}
        for segment in segments:
            proposition = _observed_proposition(segment, propositions)
            source_proposition = _source_proposition(segment, propositions)
            text = str(segment["targetText"])
            if any(
                disallowed.casefold() in text.casefold()
                for disallowed in manifest["disallowedTargetText"]
            ):
                script_violations += 1
            if source_proposition is not None and any(
                term not in text for term in source_proposition["glossaryTerms"]
            ):
                glossary_loss += 1
            if proposition is None:
                continue
            proposition_id = proposition["id"]
            observed.append(proposition_id)
            if "STANDARD" not in proposition["depthRoles"]:
                depth_violations += 1
            citation_ok = segment["citationIndexes"] == [proposition["citationIndex"]]
            source_ok = _normalized(str(segment["sourceText"])) == _normalized(
                proposition["sourceText"]
            )
            support_ids = segment["claimSupportIds"]
            context_ids = segment["contextRefIds"]
            support_ok = False
            if (
                isinstance(support_ids, list)
                and len(support_ids) == 1
                and isinstance(context_ids, list)
                and len(context_ids) == 1
            ):
                support = support_by_id.get(support_ids[0])
                support_ok = bool(
                    support
                    and support["propositionId"] == proposition_id
                    and support["supportStatus"] == "SUPPORTED"
                    and support["citationIndex"] == proposition["citationIndex"]
                    and support["contextRefId"] == context_ids[0]
                )
            if citation_ok and source_ok and support_ok:
                supported_citations += 1

        observed_set = frozenset(observed)
        semantic_sets[row_id] = observed_set
        required = set(expected["requiredPropositionIds"])
        required_essential = required & essential_ids
        required_audience = required - essential_ids
        unsupported = len(observed) - len([item for item in observed if item in required])
        metrics: dict[str, float | int] = {
            "essentialPropositionRecall": len(observed_set & required_essential)
            / len(required_essential),
            "unsupportedPropositionCount": unsupported
            + sum(_observed_proposition(item, propositions) is None for item in segments),
            "citationSupportPrecision": supported_citations / len(segments) if segments else 0.0,
            "audienceRequiredEmphasisRecall": len(observed_set & required_audience)
            / len(required_audience),
            "pairwiseAudienceCollapseCount": 0,
            "depthRoleViolationCount": depth_violations,
            "glossaryLossCount": glossary_loss,
            "targetScriptViolationCount": script_violations,
            "mandatoryRowCoverage": 0.0,
        }
        if row["unsupportedClaimCount"] != 0 or not row["stored"] or not row["replayed"]:
            metrics["unsupportedPropositionCount"] = int(metrics["unsupportedPropositionCount"]) + 1
        api_texts = [item["targetText"] for item in segments]
        artifact_segments = row["artifactSegments"]
        if (
            row["visibleTargetTexts"] != api_texts
            or artifact_segments != segments
            or row["artifactScriptText"] != "\n".join(api_texts)
        ):
            failures.append(f"{row_id}:surface-disagreement")
        row_metrics[row_id] = metrics

    collapse_count = 0
    semantic_values = list(semantic_sets.items())
    for index, (_, left) in enumerate(semantic_values):
        for _, right in semantic_values[index + 1 :]:
            if left == right:
                collapse_count += 1
    coverage = len(set(observed_ids) & set(expected_rows)) / len(expected_rows)
    source_checksums = {row["sourceChecksum"] for row in rows}
    if len(source_checksums) != 1 or not all(
        isinstance(value, str) and value for value in source_checksums
    ):
        failures.append("source-identity")
    for metrics in row_metrics.values():
        metrics["pairwiseAudienceCollapseCount"] = collapse_count
        metrics["mandatoryRowCoverage"] = coverage

    aggregate = {
        "essentialPropositionRecall": min(
            (item["essentialPropositionRecall"] for item in row_metrics.values()), default=0.0
        ),
        "unsupportedPropositionCount": sum(
            int(item["unsupportedPropositionCount"]) for item in row_metrics.values()
        ),
        "citationSupportPrecision": min(
            (item["citationSupportPrecision"] for item in row_metrics.values()), default=0.0
        ),
        "audienceRequiredEmphasisRecall": min(
            (item["audienceRequiredEmphasisRecall"] for item in row_metrics.values()), default=0.0
        ),
        "pairwiseAudienceCollapseCount": collapse_count,
        "depthRoleViolationCount": sum(
            int(item["depthRoleViolationCount"]) for item in row_metrics.values()
        ),
        "glossaryLossCount": sum(int(item["glossaryLossCount"]) for item in row_metrics.values()),
        "targetScriptViolationCount": sum(
            int(item["targetScriptViolationCount"]) for item in row_metrics.values()
        ),
        "mandatoryRowCoverage": coverage,
    }
    thresholds = manifest["thresholds"]
    for row_id, metrics in row_metrics.items():
        for metric, threshold in thresholds.items():
            if metrics[metric] != threshold:
                failures.append(f"{row_id}:{metric}")
    if set(observed_ids) != set(expected_rows):
        failures.append("mandatory-row-set")
    classification = "SEMANTIC_PASS" if not failures else "FAILED"
    return OracleResult(classification, aggregate, row_metrics, tuple(sorted(set(failures))))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        observations = json.loads(args.observations.read_text(encoding="utf-8"))
        result = evaluate(manifest, observations)
    except (OSError, json.JSONDecodeError, OracleContractError) as exc:
        print(json.dumps({"classification": "NOT_PROVEN", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.classification == "SEMANTIC_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
