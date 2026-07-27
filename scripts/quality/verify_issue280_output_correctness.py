#!/usr/bin/env python3
"""Validate the retained Issue #280 forensic evidence; never assert closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "reports" / "checkpoint3-issue280" / "requirement-matrix.json"
PR299_BASE_HEAD = "cc89b2dd52da38e8d8a9acbd813e327737cf0ca1"
EVIDENCE_HEAD = "f93653e8a11e697c88766b207fb01c18662339d6"
REVIEW_HEAD = "16536867dc2f3bca8c19281b58e924615475c158"
APPROVED_CONTRACT_SHA256 = "14ca82c43768975f4a904a308db10aab77ef50cdedd97e92601ecba67ab7e75a"

ISSUE_280_NOT_FIXED = 1
ISSUE_280_EVIDENCE_STALE = 2
ISSUE_280_EVIDENCE_MALFORMED = 3
ISSUE_280_EVIDENCE_CONTRADICTORY = 4

TOP_LEVEL_KEYS = {"schemaVersion", "issue", "forensicEvidence"}
FORENSIC_KEYS = {
    "schemaVersion",
    "subject",
    "pr299BaseHead",
    "evidenceHead",
    "packetReviewedSourceHead",
    "approvedContractSha256",
    "historicalSourceRefs",
    "observedExecution",
}
HISTORICAL_SOURCE_REFS = [
    "https://github.com/imrohitagrawal/narratwin-ai/blob/"
    "f93653e8a11e697c88766b207fb01c18662339d6/"
    "reports/checkpoint3-issue280/requirement-matrix.json",
    "docs/reviews/ISSUE_300_GOVERNANCE_RESET_PREFLIGHT.md#preserved-behavioral-red-evidence",
]
EXPECTED_EXECUTION = {
    "attemptedCombinations": 525,
    "completedCombinations": 217,
    "refusedCombinations": 308,
    "refusalCode": "ISSUE280_TRANSLATION_REFUSED",
    "conciseCompleted": 175,
    "standardCompleted": 21,
    "deepCompleted": 21,
    "successfulLanguageDepthGroups": 31,
    "audiencesPerSuccessfulGroup": 7,
    "uniqueTargetBodiesPerSuccessfulGroup": 1,
}


def evaluate_forensic_evidence(
    artifact: Any, *, expected_head: str
) -> tuple[int, tuple[str, ...]]:
    if not isinstance(artifact, dict):
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-not-object",)
    if set(artifact) != TOP_LEVEL_KEYS:
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-key-set",)
    if artifact.get("schemaVersion") != "Issue280NegativeForensicArtifactV1":
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-schemaVersion",)
    if artifact.get("issue") != 280:
        return ISSUE_280_EVIDENCE_MALFORMED, ("issue",)

    forensic = artifact.get("forensicEvidence")
    if not isinstance(forensic, dict):
        return ISSUE_280_EVIDENCE_MALFORMED, ("forensicEvidence-not-object",)
    if set(forensic) != FORENSIC_KEYS:
        return ISSUE_280_EVIDENCE_MALFORMED, ("forensicEvidence-key-set",)
    if forensic.get("schemaVersion") != "Issue280ForensicEvidenceV1":
        return ISSUE_280_EVIDENCE_MALFORMED, ("schemaVersion",)
    if forensic.get("subject") != "issue-280":
        return ISSUE_280_EVIDENCE_MALFORMED, ("subject",)
    refs = forensic.get("historicalSourceRefs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        return ISSUE_280_EVIDENCE_MALFORMED, ("historicalSourceRefs-shape",)
    observed = forensic.get("observedExecution")
    if not isinstance(observed, dict) or set(observed) != set(EXPECTED_EXECUTION):
        return ISSUE_280_EVIDENCE_MALFORMED, ("observedExecution-shape",)
    if any(type(observed[key]) is not type(value) for key, value in EXPECTED_EXECUTION.items()):
        return ISSUE_280_EVIDENCE_MALFORMED, ("observedExecution-types",)

    if refs != HISTORICAL_SOURCE_REFS:
        return ISSUE_280_EVIDENCE_STALE, ("historicalSourceRefs",)

    expected_identities = {
        "pr299BaseHead": PR299_BASE_HEAD,
        "evidenceHead": expected_head,
        "packetReviewedSourceHead": REVIEW_HEAD,
        "approvedContractSha256": APPROVED_CONTRACT_SHA256,
    }
    stale = tuple(
        key for key, expected in expected_identities.items() if forensic.get(key) != expected
    )
    if expected_head != EVIDENCE_HEAD:
        stale = ("expectedHead", *stale)
    if stale:
        return ISSUE_280_EVIDENCE_STALE, stale

    contradictions = tuple(
        key for key, expected in EXPECTED_EXECUTION.items() if observed[key] != expected
    )
    if contradictions:
        return ISSUE_280_EVIDENCE_CONTRADICTORY, contradictions
    return ISSUE_280_NOT_FIXED, (
        "217-of-525-completed",
        "308-translation-refusals",
        "audience-output-invariant",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--expected-head", default=EVIDENCE_HEAD)
    args = parser.parse_args(argv)
    try:
        artifact = json.loads(args.matrix.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ISSUE_280_EVIDENCE_MALFORMED: unreadable:{exc}")
        return ISSUE_280_EVIDENCE_MALFORMED

    code, reasons = evaluate_forensic_evidence(artifact, expected_head=args.expected_head)
    labels = {
        ISSUE_280_NOT_FIXED: "ISSUE_280_NOT_FIXED",
        ISSUE_280_EVIDENCE_STALE: "ISSUE_280_EVIDENCE_STALE",
        ISSUE_280_EVIDENCE_MALFORMED: "ISSUE_280_EVIDENCE_MALFORMED",
        ISSUE_280_EVIDENCE_CONTRADICTORY: "ISSUE_280_EVIDENCE_CONTRADICTORY",
    }
    print(f"{labels[code]}: {';'.join(reasons)}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
