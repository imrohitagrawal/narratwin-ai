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
CANONICAL_FIXTURE_SHA256 = "e1b5b35615324cc7ad09a3ba7a4473ddae73ba8c2d02cc84a9c90deebcbc7e64"
AGGREGATE_EVIDENCE_SHA256 = "4d037de6d40d3098b327c2eb5e87ec8849082c08d206db8caac6d18e9be399b2"
PROVENANCE_MANIFEST_SHA256 = "61c92fdd428246dc54843118c508f82e908b8b9617415e6c6e5fe8d8d0ca26fc"

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
    "canonicalFixtureSha256",
    "aggregateEvidenceSha256",
    "provenanceManifestSha256",
    "forensicSourceRefs",
    "observedExecution",
}
FORENSIC_SOURCE_REFS = [
    "https://gist.githubusercontent.com/imrohitagrawal/4dab26b4ec26e9f1507482725da206b2/raw/"
    "1e35fac6ba71fc3c1d8c616650bf07f31c48544d/ISSUE280_AGGREGATE_EXECUTION_V1.json",
    "https://gist.githubusercontent.com/imrohitagrawal/4dab26b4ec26e9f1507482725da206b2/raw/"
    "1e35fac6ba71fc3c1d8c616650bf07f31c48544d/PUBLIC_PROVENANCE_MANIFEST.md",
    "https://gist.githubusercontent.com/imrohitagrawal/4dab26b4ec26e9f1507482725da206b2/raw/"
    "1e35fac6ba71fc3c1d8c616650bf07f31c48544d/32_FINAL_DEVELOPMENT_CONTRACT_CANDIDATE.md",
    "https://gist.githubusercontent.com/imrohitagrawal/4dab26b4ec26e9f1507482725da206b2/raw/"
    "1e35fac6ba71fc3c1d8c616650bf07f31c48544d/20_DELTA007_EXECUTION_EVIDENCE.json",
]
EXPECTED_EXECUTION = {
    "attemptedCombinations": 525,
    "completedCombinations": 525,
    "refusedCombinations": 0,
    "refusalCode": None,
    "conciseCompleted": 175,
    "standardCompleted": 175,
    "deepCompleted": 175,
    "successfulLanguageDepthGroups": 75,
    "audiencesPerSuccessfulGroup": 7,
    "uniqueAcceptedScriptBodiesPerSuccessfulGroup": 7,
    "uniqueTargetBodiesPerSuccessfulGroup": 1,
}


def evaluate_forensic_evidence(
    artifact: Any, *, expected_head: str
) -> tuple[int, tuple[str, ...]]:
    if not isinstance(artifact, dict):
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-not-object",)
    if set(artifact) != TOP_LEVEL_KEYS:
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-key-set",)
    if artifact.get("schemaVersion") != "Issue280NegativeForensicArtifactV2":
        return ISSUE_280_EVIDENCE_MALFORMED, ("root-schemaVersion",)
    if artifact.get("issue") != 280:
        return ISSUE_280_EVIDENCE_MALFORMED, ("issue",)

    forensic = artifact.get("forensicEvidence")
    if not isinstance(forensic, dict):
        return ISSUE_280_EVIDENCE_MALFORMED, ("forensicEvidence-not-object",)
    if set(forensic) != FORENSIC_KEYS:
        return ISSUE_280_EVIDENCE_MALFORMED, ("forensicEvidence-key-set",)
    if forensic.get("schemaVersion") != "Issue280ForensicEvidenceV2":
        return ISSUE_280_EVIDENCE_MALFORMED, ("schemaVersion",)
    if forensic.get("subject") != "issue-280":
        return ISSUE_280_EVIDENCE_MALFORMED, ("subject",)
    refs = forensic.get("forensicSourceRefs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        return ISSUE_280_EVIDENCE_MALFORMED, ("forensicSourceRefs-shape",)
    observed = forensic.get("observedExecution")
    if not isinstance(observed, dict) or set(observed) != set(EXPECTED_EXECUTION):
        return ISSUE_280_EVIDENCE_MALFORMED, ("observedExecution-shape",)
    wrong_types = any(
        type(observed[key]) is not type(value)
        for key, value in EXPECTED_EXECUTION.items()
        if key != "refusalCode"
    )
    if wrong_types or not isinstance(observed["refusalCode"], (str, type(None))):
        return ISSUE_280_EVIDENCE_MALFORMED, ("observedExecution-types",)

    if refs != FORENSIC_SOURCE_REFS:
        return ISSUE_280_EVIDENCE_STALE, ("forensicSourceRefs",)

    expected_identities = {
        "pr299BaseHead": PR299_BASE_HEAD,
        "evidenceHead": expected_head,
        "packetReviewedSourceHead": REVIEW_HEAD,
        "approvedContractSha256": APPROVED_CONTRACT_SHA256,
        "canonicalFixtureSha256": CANONICAL_FIXTURE_SHA256,
        "aggregateEvidenceSha256": AGGREGATE_EVIDENCE_SHA256,
        "provenanceManifestSha256": PROVENANCE_MANIFEST_SHA256,
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
        "525-of-525-completed",
        "zero-translation-refusals",
        "accepted-scripts-audience-sensitive",
        "visible-target-output-audience-invariant",
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
