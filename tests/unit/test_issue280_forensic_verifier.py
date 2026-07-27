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


def test_valid_forensic_evidence_reports_issue280_not_fixed(tmp_path: Path) -> None:
    result = run_verifier(tmp_path, canonical_matrix())

    assert result.returncode == 1
    assert result.stdout.startswith("ISSUE_280_NOT_FIXED:")
    assert "passed" not in result.stdout.lower()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda artifact: artifact["forensicEvidence"].__setitem__("evidenceHead", "0" * 40),
        lambda artifact: artifact["forensicEvidence"].__setitem__("packetReviewedSourceHead", "1" * 40),
        lambda artifact: artifact["forensicEvidence"].__setitem__("pr299BaseHead", "2" * 40),
        lambda artifact: artifact["forensicEvidence"].__setitem__("approvedContractSha256", "3" * 64),
    ],
)
def test_stale_identity_has_distinct_exit(
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
        lambda artifact: artifact.pop("forensicEvidence"),
        lambda artifact: artifact["forensicEvidence"].__setitem__("observedExecution", []),
        lambda artifact: artifact.__setitem__("semanticClosure", {}),
        lambda artifact: artifact["forensicEvidence"].__setitem__("status", "FAILED"),
        lambda artifact: artifact.__setitem__("overallVerdict", "PASSED"),
        lambda artifact: artifact.__setitem__("authorVerdict", "FIXED"),
        lambda artifact: artifact.__setitem__("renamedDecision", "ALL_GOOD"),
        lambda artifact: artifact.__setitem__("unknownTopLevel", True),
        lambda artifact: artifact["forensicEvidence"].__setitem__("unknownForensicKey", True),
        lambda artifact: artifact["forensicEvidence"]["observedExecution"].__setitem__(
            "unknownObservation", 1
        ),
        lambda artifact: (
            artifact["forensicEvidence"].__setitem__("evidenceHead", "0" * 40),
            artifact["forensicEvidence"]["observedExecution"].__setitem__(
                "unknownObservation", 1
            ),
        ),
    ],
)
def test_malformed_or_verdict_bearing_evidence_has_distinct_exit(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], object]
) -> None:
    artifact = canonical_matrix()
    mutate(artifact)

    result = run_verifier(tmp_path, artifact)

    assert result.returncode == 3
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_MALFORMED:")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("attemptedCombinations", 524),
        ("completedCombinations", 218),
        ("refusedCombinations", 307),
        ("conciseCompleted", 174),
        ("standardCompleted", 22),
        ("deepCompleted", 22),
        ("successfulLanguageDepthGroups", 30),
        ("audiencesPerSuccessfulGroup", 6),
        ("uniqueTargetBodiesPerSuccessfulGroup", 7),
    ],
)
def test_contradictory_observation_has_distinct_exit(
    tmp_path: Path, field: str, value: int
) -> None:
    artifact = canonical_matrix()
    artifact["forensicEvidence"]["observedExecution"][field] = value

    result = run_verifier(tmp_path, artifact)

    assert result.returncode == 4
    assert result.stdout.startswith("ISSUE_280_EVIDENCE_CONTRADICTORY:")


def test_no_evidence_variant_can_emit_positive_semantic_closure(tmp_path: Path) -> None:
    artifact = canonical_matrix()
    variants = [artifact]
    for field in ("completedCombinations", "refusedCombinations", "uniqueTargetBodiesPerSuccessfulGroup"):
        mutation = copy.deepcopy(artifact)
        mutation["forensicEvidence"]["observedExecution"][field] = 0
        variants.append(mutation)

    results = [run_verifier(tmp_path, variant) for variant in variants]

    assert all(result.returncode in {1, 2, 3, 4} for result in results)
    assert all("closure passed" not in result.stdout.lower() for result in results)
