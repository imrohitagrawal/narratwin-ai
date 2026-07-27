from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, cast

import pytest

ROOT = Path(__file__).parents[2]
MATRIX = ROOT / "reports/checkpoint3-issue280/requirement-matrix.json"
VERIFIER = ROOT / "scripts/quality/verify_issue280_output_correctness.py"
EVIDENCE_HEAD = "f93653e8a11e697c88766b207fb01c18662339d6"
GIST_REVISION = "1e35fac6ba71fc3c1d8c616650bf07f31c48544d"

def run_verifier(tmp_path: Path, artifact: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    matrix = tmp_path / "matrix.json"
    matrix.write_text(json.dumps(artifact), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--matrix", str(matrix), "--expected-head", EVIDENCE_HEAD],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def canonical_matrix() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MATRIX.read_text(encoding="utf-8")))


def test_valid_canonical_v2_reports_only_known_failure(tmp_path: Path) -> None:
    forensic = canonical_matrix()["forensicEvidence"]
    assert forensic["schemaVersion"] == "Issue280ForensicEvidenceV2"
    assert forensic["canonicalFixtureSha256"].startswith("e1b5b356")
    assert forensic["aggregateEvidenceSha256"].startswith("4d037de6")
    assert all(GIST_REVISION in ref for ref in forensic["forensicSourceRefs"])

    result = run_verifier(tmp_path, canonical_matrix())
    assert result.returncode == 1
    assert result.stdout == (
        "ISSUE_280_NOT_FIXED: 525-of-525-completed;zero-translation-refusals;"
        "accepted-scripts-audience-sensitive;visible-target-output-audience-invariant\n"
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a["forensicEvidence"].__setitem__("evidenceHead", "0" * 40),
        lambda a: a["forensicEvidence"].__setitem__("packetReviewedSourceHead", "1" * 40),
        lambda a: a["forensicEvidence"].__setitem__("pr299BaseHead", "2" * 40),
        lambda a: a["forensicEvidence"].__setitem__("approvedContractSha256", "3" * 64),
        lambda a: a["forensicEvidence"].__setitem__("canonicalFixtureSha256", "4" * 64),
        lambda a: a["forensicEvidence"].__setitem__("aggregateEvidenceSha256", "5" * 64),
        lambda a: a["forensicEvidence"].__setitem__("provenanceManifestSha256", "6" * 64),
        lambda a: a["forensicEvidence"]["forensicSourceRefs"].__setitem__(0, a["forensicEvidence"]["forensicSourceRefs"][0].replace(GIST_REVISION, "0" * 40)),
        lambda a: a["forensicEvidence"]["forensicSourceRefs"].__setitem__(0, a["forensicEvidence"]["forensicSourceRefs"][0].replace("EXECUTION_V1", "EXECUTION_V2")),
        lambda a: a["forensicEvidence"]["forensicSourceRefs"].__setitem__(1, "bad-manifest"),
        lambda a: a["forensicEvidence"]["forensicSourceRefs"].__setitem__(2, "bad-contract"),
    ],
)
def test_bound_identity_or_source_mutation_is_stale(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    artifact = canonical_matrix()
    mutate(artifact)
    result = run_verifier(tmp_path, artifact)
    assert result.returncode == 2
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_STALE:")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a.pop("forensicEvidence"),
        lambda a: a.__setitem__("schemaVersion", "Issue280NegativeForensicArtifactV1"),
        lambda a: a.__setitem__("overallVerdict", "PASSED"),
        lambda a: a.__setitem__("authorVerdict", "FIXED"),
        lambda a: a.__setitem__("renamedDecision", "ALL_GOOD"),
        lambda a: a.__setitem__("unknownTopLevel", True),
        lambda a: a["forensicEvidence"].__setitem__("unknownForensicKey", True),
        lambda a: a["forensicEvidence"]["observedExecution"].__setitem__("unknownObservation", 1),
    ],
)
def test_unknown_or_verdict_bearing_shape_is_malformed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], object]
) -> None:
    artifact = canonical_matrix()
    mutate(artifact)
    result = run_verifier(tmp_path, artifact)
    assert result.returncode == 3
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_MALFORMED:")


@pytest.mark.parametrize(
    ("field", "value"),
    [("uniqueAcceptedScriptBodiesPerSuccessfulGroup", 6), ("uniqueTargetBodiesPerSuccessfulGroup", 2)],
)
def test_audience_body_count_mutation_is_contradictory(
    tmp_path: Path, field: str, value: int
) -> None:
    artifact = canonical_matrix()
    artifact["forensicEvidence"]["observedExecution"][field] = value
    result = run_verifier(tmp_path, artifact)
    assert result.returncode == 4
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_CONTRADICTORY:")


def test_old_217_308_aggregate_is_contradictory(tmp_path: Path) -> None:
    artifact = canonical_matrix()
    artifact["forensicEvidence"]["observedExecution"].update(
        completedCombinations=217, refusedCombinations=308,
        refusalCode="ISSUE280_TRANSLATION_REFUSED", standardCompleted=21,
        deepCompleted=21, successfulLanguageDepthGroups=31,
    )
    result = run_verifier(tmp_path, artifact)
    assert result.returncode == 4
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_CONTRADICTORY:")


def test_no_evidence_variant_can_emit_exit_zero(tmp_path: Path) -> None:
    artifact = canonical_matrix()
    variants = [artifact]
    for field in ("completedCombinations", "refusedCombinations", "uniqueTargetBodiesPerSuccessfulGroup"):
        mutation = copy.deepcopy(artifact)
        mutation["forensicEvidence"]["observedExecution"][field] = -1
        variants.append(mutation)
    results = [run_verifier(tmp_path, variant) for variant in variants]
    assert all(result.returncode in {1, 2, 3, 4} for result in results)
    assert all("closure passed" not in result.stdout.lower() for result in results)
