from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from scripts.quality.cut1_presenter_contract import (
    finding_codes,
    validate_contract_bundle,
    validate_contract_documents,
    validate_human_evaluation,
    validate_provider_acceptance,
)


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64
OID = "b" * 40
EFFECTIVE = "2026-08-01T00:00:00Z"
EXPIRY = "2027-08-01T00:00:00Z"
BASE = "97e8173c2ec1323aa9ced23d43059bca2e5a204f"
SCRIPT = "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435"
KNOWLEDGE = "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e"
PROTOCOL_SHA = "fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8"
BAKEOFF_SHA = "863dfa743770f52e1d4e9018a34e6f1002e5abdddcce6b845df400a423523bfb"
CELL, COHORT = ("cells", 0), ("cohort",)
ANALYSIS, METRICS, DEFECT, RETEST = (CELL + (name,) for name in ("analysis", "objectiveMetrics", "defectReview", "retest"))
CONSENT, IDEMPOTENCY, VIEWERS = ("rights", "consentBinding"), ("idempotency",), COHORT + ("viewers",)
DIM0, PAIR0, PROTOCOL, EXCLUSIONS, CALIBRATION = CELL + ("dimensions", 0), CELL + ("pairs", 0), ("protocolBinding",), CELL + ("exclusions",), ("sharedCalibration",)
CURRENT_ARTIFACT, OWNER = hashlib.sha256(b"meera-en-landscape").hexdigest(), "https://github.com/imrohitagrawal/narratwin-ai/issues/452#issuecomment-"
OPERATIONAL, REVISED, FAILED = "OPERATIONAL_INVALID_RERUN", "REVISED_CANDIDATE_RETEST", "FAILED_STATISTICAL"
ASSETS = {
    "meera": "d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1",
    "raj": "663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd",
    "myra": "30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97",
}
DIMENSIONS = (
    "IDENTITY", "VOICE_PROSODY", "GAZE", "BLINK", "EXPRESSION", "LIP_SYNC", "HEAD",
    "TORSO_POSTURE", "ARM", "HAND_FINGER", "BODY", "HAIR_CLOTHING_BACKGROUND", "TIMING",
    "ACCESSIBILITY", "GROUNDING", "LANGUAGE", "PROVENANCE",
)
TRIAL_BLOCK = (
    ("meera", "LANDSCAPE"), ("raj", "PORTRAIT"), ("myra", "LANDSCAPE"),
    ("meera", "PORTRAIT"), ("raj", "LANDSCAPE"), ("myra", "PORTRAIT"),
)
DELETE = object()


def ref(value: str = "evidence") -> dict[str, str]:
    return {"id": value, "sha256": SHA}


def checkpoint(value: str) -> dict[str, Any]:
    return {"id": value, "sha256": SHA, "accessedAt": EFFECTIVE, "effectiveAt": EFFECTIVE, "expiresAt": EXPIRY, "refreshRequired": True}


def sha_json(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def retest_patch(attempt: int, kind: str, disposition: str, artifact: str, operational: int = 0, revised: int = 0) -> dict[str, Any]:
    return {"attemptNumber": attempt, "operationalInvalidRerunCount": operational, "revisedCandidateRetestCount": revised, "attemptKind": kind, "priorDisposition": disposition, "priorAttemptRef": ref("prior"), "priorArtifactSha256": artifact, "priorViewerManifestSha256": "b" * 64}


def trial_rows(viewer: int, forced_offset: int | None = None, mode: str = "VALID") -> list[dict[str, Any]]:
    offset = viewer % len(TRIAL_BLOCK) if forced_offset is None else forced_offset
    sequence = (TRIAL_BLOCK[offset:] + TRIAL_BLOCK[:offset]) * 2
    rows = []
    for order, (presenter, aspect) in enumerate(sequence):
        cell, pair = f"{presenter}-en-{aspect.lower()}", (viewer * 2 + order // 6) % 20
        candidate = "A" if ((5 * viewer + 10 * order + 11 * (viewer // 10)) % 20) < 10 else "B"
        candidate = "A" if mode == "SIDE_ZERO" else candidate
        correct = ((viewer + 9 * order + 19 * (viewer // 10)) % 20) < 8 + pair % 5
        correct = ((5 * viewer + order + 12 * (viewer // 10)) % 20) < 10 if mode == "PAIR_ZERO" else correct
        if mode in {"PAIR_SEPARATED", "VIEWER_ZERO"}:
            correct = order < 6 if mode == "PAIR_SEPARATED" else viewer < 100
        response_id = f"response-{viewer}-{order}"
        payload = {"responseId": response_id, "viewerId": f"viewer-{viewer}", "cellId": cell, "pairId": f"{cell}-pair-{pair}", "excerptId": f"{cell}-excerpt-{pair}", "order": order + 1, "candidateSide": candidate, "forcedChoice": candidate if correct else ("B" if candidate == "A" else "A"), "correct": correct, "confidence": "UNSURE" if viewer % 20 == 0 else "SURE"}
        rows.append(payload | {"responseSha256": sha_json(payload)})
    return rows


def viewer_rows(mode: str = "VALID") -> list[dict[str, Any]]:
    return [{"viewerId": f"viewer-{viewer}", "age": 18, "consentRef": ref(f"viewer-consent-{viewer}"), "projectIndependent": True, "providerIndependent": True, "noPriorExposure": True, "languageScreenScore": 4, "trials": trial_rows(viewer, mode=mode)} for viewer in range(200)]


def raw_viewers(kind: str) -> list[dict[str, Any]]:
    viewers = viewer_rows()
    targets = [(0, 0)]
    if kind == "PARENT":
        viewers[0]["trials"][0]["viewerId"] = "viewer-1"
    elif kind == "UNKNOWN":
        viewers[0]["trials"][0].update(pairId="meera-en-landscape-unknown", excerptId="meera-en-landscape-unknown")
    elif kind == "LINK":
        viewers[0]["trials"][0]["excerptId"] = "meera-en-landscape-excerpt-1"
    elif kind == "CORRECT":
        targets = [(0, 0), (0, 6)]
        for viewer, index in targets:
            row = viewers[viewer]["trials"][index]
            row["correct"] = not row["correct"]
    elif kind == "REPEAT":
        targets = [(0, 6), (30, 0)]
        rows = [viewers[v]["trials"][i] for v, i in targets]
        refs = [(row["pairId"], row["excerptId"]) for row in rows][::-1]
        for row, (pair_id, excerpt_id) in zip(rows, refs, strict=True):
            row.update(pairId=pair_id, excerptId=excerpt_id)
    else:
        targets = [(31, 0)]
        viewers[31]["trials"][0]["responseId"] = viewers[1]["trials"][0]["responseId"]
    for viewer, index in targets:
        row = viewers[viewer]["trials"][index]
        row["responseSha256"] = sha_json({key: value for key, value in row.items() if key != "responseSha256"})
    return viewers


def clip_dimensions(cell_id: str, dimension: str) -> list[dict[str, Any]]:
    return [{"clipId": f"{cell_id}-clip-{i}", "clipSha256": hashlib.sha256(f"{cell_id}-clip-{i}".encode()).hexdigest(), "raterLabels": [{"raterId": rater, "qualificationRef": ref(f"{rater}-qualified"), "independenceRef": ref(f"{rater}-independent"), "label": "PASS"} for rater in ("dimension-rater-1", "dimension-rater-2")], "adjudicatedLabel": "PASS", "adjudicatorId": "dimension-adjudicator", "adjudicationEvidenceRef": ref(f"{dimension}-{i}-adjudication")} for i in range(20)]


def calibration_rows() -> list[dict[str, Any]]:
    classes = ("IDENTITY",) * 10 + ("LIMB",) * 10 + ("TEMPORAL",) * 10 + ("CLEAN",) * 30
    return [{"clipId": f"calibration-{i}", "expectedClass": expected, "raterLabels": [{"raterId": rater, "severe": expected != "CLEAN"} for rater in ("rater-1", "rater-2")]} for i, expected in enumerate(classes)]


def live_rows(cell_id: str) -> list[dict[str, Any]]:
    return [{"clipId": f"{cell_id}-clip-{i}", "clipSha256": hashlib.sha256(f"{cell_id}-clip-{i}".encode()).hexdigest(), "raterLabels": [{"raterId": rater, "severe": False} for rater in ("rater-1", "rater-2")], "adjudicatedSevere": False} for i in range(20)]


def human_record() -> dict[str, Any]:
    assert hashlib.sha256((ROOT / "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json").read_bytes()).hexdigest() == PROTOCOL_SHA
    def rater(value: str) -> dict[str, Any]:
        return {"raterId": value, "independenceRef": ref(f"{value}-independence"), "overallSensitivity": 1, "identitySensitivity": 1, "limbSensitivity": 1, "temporalSensitivity": 1, "specificity": 1}

    def cell(presenter: str, aspect: str) -> dict[str, Any]:
        cell_id = f"{presenter}-en-{aspect.lower()}"
        artifact = hashlib.sha256(cell_id.encode()).hexdigest()
        pairs = [{
            "pairId": f"{cell_id}-pair-{i}", "excerptId": f"{cell_id}-excerpt-{i}",
            "candidateClipSha256": hashlib.sha256(f"{cell_id}-clip-{i}".encode()).hexdigest(),
            "control": {"controlId": f"{cell_id}-control-{i}", "artifactSha256": hashlib.sha256(f"{cell_id}-control-{i}".encode()).hexdigest(), "manifestSha256": hashlib.sha256(f"{cell_id}-manifest-{i}".encode()).hexdigest(), "subjectId": f"subject-{i}", "projectId": "project-1", "scope": "MATCHED_HUMAN_CONTROL", "consentStatus": "CURRENT", "consentEvidenceRef": ref(f"control-consent-{i}"), "rightsEvidenceRef": ref(f"control-rights-{i}"), "effectiveAt": EFFECTIVE, "expiresAt": EXPIRY, "revokedAt": None, "publicationClass": "CONTROLLED_RESEARCH_ONLY"},
            "candidateDurationMs": 10000, "controlDurationMs": 10400, "candidateLufs": -16, "controlLufs": -15.5,
            "language": "en", "framing": "WAIST_UP", "resolution": "1920x1080", "frameRate": 30,
            "playerChrome": "matched-v1", "captureQualityBand": "high-v1",
            "sideChannelsStripped": True, "allocationId": f"allocation-{cell_id}-{i}",
        } for i in range(20)]
        return {
            "presenterId": presenter, "language": "en", "aspectRatio": aspect,
            "candidate": {
                "artifactId": cell_id, "artifactSha256": artifact, "controlSha256": "c" * 64,
                "controlManifestSha256": "d" * 64, "assetSha256": ASSETS[presenter],
                "knowledgeSha256": KNOWLEDGE, "scriptSha256": SCRIPT,
                "audioSha256": hashlib.sha256(f"{cell_id}-audio".encode()).hexdigest(),
                "captionSha256": SHA, "providerCandidateId": "provider", "modelOrEngineVersion": "pinned-v1",
                "tenantId": "tenant-1", "projectId": "project-1", "runId": f"run-{presenter}-{aspect.lower()}",
            },
            "pairs": pairs,
            "analysis": {
                "viewerCount": 200, "forcedChoiceCount": 400, "pairCount": 20, "minimumRatingsPerPair": 20,
                "maximumRatingsPerPair": 20, "viewerTrialManifestSha256": SHA, "correctCount": 200,
                "unsureConfidenceCount": 20, "missingCount": 0, "pointEstimate": 0.5, "ciLower": 0.41,
                "ciUpper": 0.59, "bootstrapAttemptedDraws": 10000, "bootstrapSuccessfulDraws": 10000,
                "bootstrapSuccessRate": 1, "bootstrapSeed": 4522026082802, "bootstrapResultSha256": SHA,
                "modelConverged": True, "modelSingular": False, "simulatedPower": 0.95,
                "powerWilsonLower": 0.9486318174896535, "powerSimulationCount": 100000, "powerSimulatedPassCount": 95000,
                "powerSeed": 4522026082803, "powerResultSha256": SHA, "powerModel": "CROSSED_LOGISTIC_MIXED_MODEL",
                "powerWilsonMethod": "BERNOULLI_SCORE_INTERVAL_TWO_SIDED", "powerWilsonConfidenceLevel": 0.95,
                "powerWilsonTolerance": 1e-12, "viewerIccPlanning": 0.05, "pairIccPlanning": 0.02,
            },
            "exclusions": {"eligibleCount": 200, "excludedCount": 0, "totalRate": 0,
                           "maximumSingleReasonRate": 0, "reasonRows": [], "reasonRowsSha256": SHA},
            "subgroups": [{"subgroupId": "all-eligible", "viewerCount": 200, "pointEstimate": 0.5, "ciLower": 0.41, "ciUpper": 0.59, "disposition": "PASSED"}],
            "dimensions": [{"dimension": name, "scorableEventCount": 20, "passCount": 20, "uncertainCount": 0, "failCount": 0, "clipRows": clip_dimensions(cell_id, name), "evidenceSha256": SHA} for name in DIMENSIONS],
            "objectiveMetrics": {
                "eligibleSpeakingMs": 1000, "gazeAlignedMs": 800, "maximumOffCameraMs": 2000,
                "lipOffsetP95Ms": 80, "lipOver80MsLongestMs": 200, "identicalGestureMaxConsecutive": 2,
                "captionReferenceWords": 1000, "captionSubstitutions": 5, "captionDeletions": 5,
                "captionInsertions": 5, "captionWordAccuracy": 0.985, "captionSpokenWordCoverage": 0.995,
                "captionLongestUncaptionedSpeechMs": 1000, "contrastRatio": 4.5, "keyboardPassed": True,
                "screenReaderPassed": True, "visibleFocusPassed": True, "reducedMotionPassed": True,
                "captionCuePassed": True, "wcagAuditPassed": True, "groundedClaimCount": 20,
                "groundedClaimCitedCount": 20, "groundedClaimCitationCoverage": 1,
                "acceptedUnsupportedClaimCount": 0, "insufficientContextCaseCount": 10,
                "insufficientContextAbstainCount": 10, "insufficientContextAbstention": 1,
                "groundingEvidenceSha256": SHA, "captionCueEvidenceSha256": SHA, "wcagEvidenceSha256": SHA,
            },
            "defectReview": {
                "liveClipCount": 20, "liveInitialLabelsSha256": SHA, "liveRows": live_rows(cell_id),
                "liveRawAgreement": 1, "liveKappa": None,
                "kappaDisposition": "NA_ALL_INITIAL_LABELS_NOT_SEVERE", "adjudicatorId": "rater-3",
                "adjudicatorIndependenceRef": ref("rater-3-independence"), "disagreementLedgerSha256": SHA,
                "adjudicatedSevereDefectCount": 0,
            },
            "retest": {
                "attemptNumber": 1, "operationalInvalidRerunCount": 0, "revisedCandidateRetestCount": 0,
                "attemptKind": "INITIAL", "priorDisposition": "NONE", "priorAttemptRef": None,
                "priorArtifactSha256": None, "priorViewerManifestSha256": None, "freshViewerManifestSha256": SHA,
                "priorFailureVisibility": "CONCEALED_FROM_VIEWERS_AND_PRIMARY_RATERS",
            },
            "decision": "PASSED_STATISTICAL",
        }

    return {
        "schemaVersion": "Cut1HumanRealismEvaluationV1", "evaluationId": "evaluation-1",
        "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT",
        "protocolBinding": {
            "protocolId": "cut1-blinded-human-evaluation-v1", "protocolVersion": "1.0.0",
            "protocolSha256": PROTOCOL_SHA, "frozenAt": "2026-08-28T09:00:00+05:30",
            "firstExposureAt": "2026-08-28T10:00:00+05:30", "baseCommit": BASE,
            "headCommit": OID, "treeOid": OID,
            "ownerDecisionRefs": [OWNER + value for value in ("5444058376", "5444076231", "5444690736")],
            "governedSubgroupIds": ["all-eligible"], "analysisCodeSha256": SHA, "analysisEnvironmentSha256": SHA,
            "randomizationSeed": 4522026082801, "randomizationCommitmentSha256": SHA, "candidateManifestSha256": SHA,
        },
        "cohort": {
            "totalUniqueViewerCount": 200, "totalRatingCount": 2400, "trialsPerViewerTotal": 12,
            "viewerManifestSha256": SHA, "tutorialCount": 2, "breakAfterTrial": 6,
            "scoredMediaMinutes": 18, "sessionHandlingFrozen": True, "viewers": viewer_rows(),
            "allocationManifestSha256": SHA, "deviceCalibrationSha256": SHA,
        },
        "sharedCalibration": {
            "corpusSha256": SHA, "expectationSha256": SHA, "initialLabelsSha256": SHA,
            "clipCount": 60, "severePerClassCount": 10, "cleanClipCount": 30,
            "rawAgreement": 1, "kappa": 1, "raters": [rater("rater-1"), rater("rater-2")],
            "rows": calibration_rows(),
        },
        "cells": [cell(p, a) for p in ("meera", "raj", "myra") for a in ("LANDSCAPE", "PORTRAIT")],
        "studyDisposition": "PASSED_STATISTICAL", "retentionEvidenceRef": ref("retention"),
    }


def provider_record(presenter: str = "meera") -> dict[str, Any]:
    bakeoff = ROOT / "docs/governance/cut1-provider-bakeoff-contract-v1.json"
    assert hashlib.sha256(bakeoff.read_bytes()).hexdigest() == BAKEOFF_SHA
    record: dict[str, Any] = copy.deepcopy(json.loads(bakeoff.read_text())["disabledAcceptanceRecordExample"])
    if presenter != "meera":
        record["presenter"].update(presenterId=presenter, role="FIRST_BACKUP" if presenter == "raj" else "SECOND_BACKUP", assetSha256=ASSETS[presenter], handsVisible=False)
        record["rights"]["consentBinding"]["presenterId"] = record["lineage"]["presenterId"] = presenter
    return record


def bundle_documents() -> dict[str, Any]:
    base, names = ROOT / "docs/governance", ("cut1-blinded-human-evaluation-protocol-v1.json", "cut1-all-presenter-acceptance-matrix-v1.json", "cut1-provider-bakeoff-contract-v1.json")
    return {name: json.loads((base / name).read_text()) for name in names}


def changed(source: dict[str, Any], path: tuple[Any, ...], value: Any) -> dict[str, Any]:
    result = copy.deepcopy(source)
    cursor: Any = result
    for key in path[:-1]:
        cursor = cursor[key]
    if value is DELETE:
        cursor.pop(path[-1]) if isinstance(cursor, list) else cursor.pop(path[-1], None)
    elif path[-1] in cursor and isinstance(cursor[path[-1]], dict) and isinstance(value, dict):
        cursor[path[-1]].update(value)
    else:
        cursor[path[-1]] = value
    return result


@dataclass(frozen=True)
class Case:
    case_id: str
    contract: str
    path: tuple[Any, ...]
    value: Any
    expected: tuple[str, ...]
    mutant_id: str | None


H, P, POW, DIM, CAL, RT, ACC, GND, EXCL = "CUT1.HUMAN.", "CUT1.PROVIDER.", "POWER", "DIMENSION", "CALIBRATION", "RETEST", "ACCESSIBILITY", "GROUNDING", "EXCLUSION"


def h(name: str, path: tuple[Any, ...], value: Any, code: str) -> Case:
    return Case(name, "human", path, value, (H + code,), "HX-" + name)


def p(name: str, path: tuple[Any, ...], value: Any, code: str) -> Case:
    return Case(name, "provider", path, value, (P + code,), "PX-" + name)


def ok(name: str, contract: str, path: tuple[Any, ...] = (), value: Any = None) -> Case:
    return Case(name, contract, path, value, (), None)


CASES = (
    ok("human-valid", "human"),
    h("cohort-199", ("cohort", "totalUniqueViewerCount"), 199, "COHORT"),
    h("ratings-399", ANALYSIS + ("forcedChoiceCount",), 399, "SAMPLE"),
    h("pair-allocation-19", ANALYSIS + ("pairCount",), 19, "PAIR_ALLOCATION"),
    h("lower-bound-inclusive", ANALYSIS + ("ciLower",), 0.4, "EQUIVALENCE"),
    h("upper-bound-inclusive", ANALYSIS + ("ciUpper",), 0.6, "EQUIVALENCE"),
    h("singular-model", ANALYSIS + ("modelSingular",), True, "MODEL"),
    h("bootstrap-9999", ANALYSIS + ("bootstrapSuccessfulDraws",), 9999, "BOOTSTRAP"),
    h("bootstrap-success-low", ANALYSIS + ("bootstrapSuccessRate",), 0.989, "BOOTSTRAP"),
    h("power-sims-low", ANALYSIS + ("powerSimulationCount",), 99999, POW),
    h("power-wilson-low", ANALYSIS + ("powerWilsonLower",), 0.899, POW),
    h("bootstrap-rate-drift", ANALYSIS, {"bootstrapAttemptedDraws": 10102, "bootstrapSuccessfulDraws": 10000, "bootstrapSuccessRate": 1}, "BOOTSTRAP"),
    h("power-count-drift", ANALYSIS + ("powerSimulatedPassCount",), 90000, POW),
    h("power-wilson-drift", ANALYSIS + ("powerWilsonLower",), 0.95, POW),
    h("zero-power-seed", ANALYSIS + ("powerSeed",), 0, "PREREGISTRATION"),
    h("freeze-after-exposure", PROTOCOL + ("frozenAt",), "2026-08-28T11:00:00+05:30", "PREREGISTRATION"),
    h("protocol-drift", PROTOCOL + ("protocolSha256",), "b" * 64, "AUTHORITY_BINDING"),
    h("base-drift", PROTOCOL + ("baseCommit",), OID, "AUTHORITY_BINDING"),
    h("script-drift", ("cells", 0, "candidate", "scriptSha256"), SHA, "SOURCE_BINDING"),
    h("knowledge-drift", ("cells", 0, "candidate", "knowledgeSha256"), SHA, "SOURCE_BINDING"),
    h("duplicate-cell", ("cells", 1, "aspectRatio"), "LANDSCAPE", "CELL_SET"),
    h("dimension-fail", DIM0 + ("failCount",), 1, DIM),
    h("dimension-uncertain", ("cells", 0, "dimensions", 1, "uncertainCount"), 1, DIM),
    h("zero-scorable", ("cells", 0, "dimensions", 2, "scorableEventCount"), 0, DIM),
    h("zero-gaze-denominator", METRICS + ("eligibleSpeakingMs",), 0, "GAZE"),
    h("lip-p95-high", METRICS + ("lipOffsetP95Ms",), 81, "LIP_SYNC"),
    h("lip-duration-high", METRICS + ("lipOver80MsLongestMs",), 201, "LIP_SYNC"),
    h("caption-accuracy-low", METRICS + ("captionWordAccuracy",), 0.979, "CAPTION_ACCURACY"),
    h("caption-coverage-low", METRICS + ("captionSpokenWordCoverage",), 0.979, "CAPTION_COVERAGE"),
    h("caption-coverage-drift", METRICS + ("captionSpokenWordCoverage",), 0.99, "CAPTION_COVERAGE"),
    h("caption-gap-high", METRICS + ("captionLongestUncaptionedSpeechMs",), 1001, "CAPTION_GAP"),
    h("caption-arithmetic", METRICS + ("captionSubstitutions",), 50, "CAPTION_ACCURACY"),
    h("severe-veto", DEFECT + ("adjudicatedSevereDefectCount",), 1, "SEVERE_DEFECT"),
    h("kappa-low", CALIBRATION + ("kappa",), 0.799, CAL),
    h("rater-sensitivity-low", CALIBRATION + ("raters", 0, "identitySensitivity"), 0.99, CAL),
    ok("operational-rerun-valid", "human", RETEST, retest_patch(2, OPERATIONAL, "INVALID", CURRENT_ARTIFACT, operational=1)),
    ok("revised-rerun-valid", "human", RETEST, retest_patch(2, REVISED, FAILED, "b" * 64, revised=1)),
    ok("attempt-three-valid", "human", RETEST, retest_patch(3, REVISED, "INCONCLUSIVE", "b" * 64, operational=1, revised=1)),
    h("same-byte-retest", RETEST, retest_patch(2, REVISED, FAILED, CURRENT_ARTIFACT, revised=1), RT),
    h("reused-viewers-retest", RETEST, retest_patch(2, REVISED, FAILED, "b" * 64, revised=1) | {"priorViewerManifestSha256": SHA}, RT),
    h("op-wrong-disposition", RETEST, retest_patch(2, OPERATIONAL, FAILED, CURRENT_ARTIFACT, operational=1), RT),
    h("op-changed-byte", RETEST, retest_patch(2, OPERATIONAL, "INVALID", "b" * 64, operational=1), RT),
    h("revised-after-invalid", RETEST, retest_patch(2, REVISED, "INVALID", "b" * 64, revised=1), RT),
    h("attempt-count-drift", RETEST + ("attemptNumber",), 2, RT),
    h("owner-bypass", ("studyDisposition",), "BYPASSED_BY_HUMAN_OWNER", "OWNER_EXCEPTION_UNAUTHORIZED"),
    h("asset-substitution", ("cells", 2, "candidate", "assetSha256"), ASSETS["meera"], "ASSET_BINDING"),
    h("pair-duplicate", ("cells", 0, "pairs", 1, "pairId"), "meera-en-landscape-pair-0", "PAIR_ALLOCATION"),
    h("control-expired", PAIR0 + ("control", "expiresAt"), "2020-01-01T00:00:00Z", "CONTROL_CONSENT"),
    h("control-project-drift", PAIR0 + ("control", "projectId"), "project-2", "CONTROL_CONSENT"),
    h("control-not-effective", PAIR0 + ("control", "effectiveAt"), "2027-01-01T00:00:00Z", "CONTROL_CONSENT"),
    h("duration-mismatch", PAIR0 + ("controlDurationMs",), 10501, "MATCHING"),
    h("loudness-mismatch", PAIR0 + ("controlLufs",), -14.9, "MATCHING"),
    h("cohort-total-drift", ("cohort", "totalRatingCount"), 2399, "COUNT_PARITY"),
    h("correct-overflow", ANALYSIS + ("correctCount",), 401, "COUNT_PARITY"),
    h("ci-order", ANALYSIS + ("pointEstimate",), 0.7, "EQUIVALENCE"),
    h("estimated-power-low", ANALYSIS + ("simulatedPower",), 0.899, POW),
    h("aggregate-not-run", ("cells", 0, "decision"), "NOT_RUN", "STUDY_DISPOSITION"),
    h("dimension-duplicate", ("cells", 0, "dimensions", 16, "dimension"), "IDENTITY", "DIMENSION_SET"),
    h("dimension-count-drift", DIM0 + ("passCount",), 0, DIM),
    h("dimension-clip-missing", DIM0 + ("clipRows", 19), DELETE, DIM),
    h("dimension-rater-duplicate", DIM0 + ("clipRows", 0, "raterLabels", 1, "raterId"), "dimension-rater-1", DIM),
    h("dimension-invalid-adjudication", DIM0 + ("clipRows", 0, "raterLabels", 0, "label"), "FAIL", DIM),
    h("gaze-below-boundary", METRICS + ("gazeAlignedMs",), 799, "GAZE"),
    h("off-camera-high", METRICS + ("maximumOffCameraMs",), 2001, "GAZE"),
    h("gesture-repeat-high", METRICS + ("identicalGestureMaxConsecutive",), 3, "GESTURE"),
    h("contrast-low", METRICS + ("contrastRatio",), 4.499, ACC),
    h("keyboard-failed", METRICS + ("keyboardPassed",), False, ACC),
    h("screen-reader-failed", METRICS + ("screenReaderPassed",), False, ACC),
    h("focus-failed", METRICS + ("visibleFocusPassed",), False, ACC),
    h("reduced-motion-failed", METRICS + ("reducedMotionPassed",), False, ACC),
    h("caption-cue-failed", METRICS + ("captionCuePassed",), False, ACC),
    h("wcag-audit-failed", METRICS + ("wcagAuditPassed",), False, ACC),
    h("citation-coverage-low", METRICS + ("groundedClaimCitationCoverage",), 0.99, GND),
    h("unsupported-claim", METRICS + ("acceptedUnsupportedClaimCount",), 1, GND),
    h("abstention-low", METRICS + ("insufficientContextAbstention",), 0.99, GND),
    h("abstention-count-drift", METRICS + ("insufficientContextAbstainCount",), 9, GND),
    h("grounding-count-drift", METRICS + ("groundedClaimCitedCount",), 19, GND),
    h("grounding-evidence-missing", METRICS + ("groundingEvidenceSha256",), DELETE, GND),
    h("adjacent-presenter", VIEWERS + (0, "trials", 1, "cellId"), "meera-en-portrait", "ORDER_FATIGUE"),
    h("schedule-collapsed", VIEWERS + (1, "trials"), trial_rows(1, 0), "ORDER_FATIGUE"),
    h("pair-separated", VIEWERS, viewer_rows("PAIR_SEPARATED"), "MODEL"),
    h("pair-zero", VIEWERS, viewer_rows("PAIR_ZERO"), "MODEL"),
    h("viewer-zero", VIEWERS, viewer_rows("VIEWER_ZERO"), "MODEL"),
    h("side-imbalance", VIEWERS, viewer_rows("SIDE_ZERO"), "RAW_RESPONSE"),
    h("response-correctness-drift", VIEWERS, raw_viewers("CORRECT"), "RAW_RESPONSE"),
    h("response-hash-drift", VIEWERS + (0, "trials", 0, "responseSha256"), SHA, "RAW_RESPONSE"),
    h("parent-drift", VIEWERS, raw_viewers("PARENT"), "RAW_RESPONSE"),
    h("response-unknown-pair", VIEWERS, raw_viewers("UNKNOWN"), "PAIR_ALLOCATION"),
    h("response-link-drift", VIEWERS, raw_viewers("LINK"), "PAIR_ALLOCATION"),
    h("response-repeat-pair", VIEWERS, raw_viewers("REPEAT"), "PAIR_ALLOCATION"),
    h("response-duplicate", VIEWERS, raw_viewers("DUPLICATE"), "RAW_RESPONSE"),
    h("unsure-favorable-recode", ANALYSIS + ("correctCount",), 190, "RAW_RESPONSE"),
    h("primary-rater-duplicate", CALIBRATION + ("raters", 1, "raterId"), "rater-1", CAL),
    h("adjudicator-not-independent", DEFECT + ("adjudicatorId",), "rater-1", "CALIBRATION"),
    h("live-kappa-low", DEFECT, {"liveKappa": 0.799, "kappaDisposition": "MEASURED"}, "LIVE_IRR"),
    h("live-na-disagreement", DEFECT + ("liveRawAgreement",), 0.9, "LIVE_IRR"),
    h("live-measured-null", DEFECT + ("kappaDisposition",), "MEASURED", "LIVE_IRR"),
    h("calibration-label-drift", CALIBRATION + ("rows", 0, "raterLabels", 0, "severe"), False, CAL),
    h("severe-count-drift", DEFECT + ("liveRows", 0, "adjudicatedSevere"), True, "SEVERE_DEFECT"),
    h("subgroup-omitted", ("cells", 0, "subgroups"), [], "SUBGROUP"),
    h("subgroup-failed", ("cells", 0, "subgroups", 0, "disposition"), "FAILED", "SUBGROUP"),
    h("exclusion-total-high", EXCLUSIONS + ("totalRate",), 0.101, EXCL),
    h("exclusion-reason-high", EXCLUSIONS + ("maximumSingleReasonRate",), 0.051, EXCL),
    h("exclusion-count-drift", EXCLUSIONS + ("excludedCount",), 1, EXCL),
    ok("nonzero-exclusion-valid", "human", EXCLUSIONS, {"eligibleCount": 200, "excludedCount": 10, "totalRate": 10 / 210, "maximumSingleReasonRate": 6 / 210, "reasonRows": [{"reason": "SCREEN", "count": 6}, {"reason": "QUALITY", "count": 4}], "reasonRowsSha256": SHA}),
    h("exclusion-reason-drift", EXCLUSIONS + ("maximumSingleReasonRate",), 0.01, EXCL),
    h("schema-required-missing", ("activation",), DELETE, "SCHEMA"),
    h("schema-extra", ("unexpected",), True, "SCHEMA"),
    h("schema-type", ("cohort", "totalUniqueViewerCount"), "200", "SCHEMA"),
    h("schema-format", PROTOCOL + ("frozenAt",), "not-a-date", "SCHEMA"),
    ok("provider-valid", "provider"),
    p("screen-segment-missing", ("screening", "upload"), DELETE, "SCREENING"),
)


def materialize(case: Case) -> dict[str, Any]:
    source = human_record() if case.contract == "human" else provider_record()
    return source if not case.path else changed(source, case.path, case.value)


def test_finite_case_and_mutant_inventory() -> None:
    assert len(CASES) >= 36
    assert sum(case.mutant_id is not None for case in CASES) >= 15
    assert len({case.case_id for case in CASES}) == len(CASES)
    assert len({case.mutant_id for case in CASES if case.mutant_id}) == sum(case.mutant_id is not None for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_frozen_semantic_case(case: Case) -> None:
    validator = validate_human_evaluation if case.contract == "human" else validate_provider_acceptance
    assert finding_codes(validator(materialize(case))) == case.expected


@pytest.mark.parametrize("mutation", json.loads((ROOT / "docs/governance/cut1-provider-bakeoff-contract-v1.json").read_text())["frozenProviderMutations"], ids=lambda row: row["id"])
def test_frozen_provider_mutation(mutation: dict[str, Any]) -> None:
    record = changed(provider_record(), tuple(mutation["path"]), mutation["value"])
    assert finding_codes(validate_provider_acceptance(record)) == (mutation["code"],)


@pytest.mark.parametrize("presenter", ("raj", "myra"))
def test_backup_provider_positive(presenter: str) -> None:
    assert finding_codes(validate_provider_acceptance(provider_record(presenter))) == ()


@pytest.mark.parametrize("mutation", bundle_documents()["cut1-blinded-human-evaluation-protocol-v1.json"]["frozenBundleMutations"], ids=lambda row: row["id"])
def test_frozen_bundle_mutation(mutation: dict[str, Any]) -> None:
    documents = bundle_documents()
    cursor = documents[mutation["document"]]
    for key in mutation["path"][:-1]:
        cursor = cursor[key]
    cursor[mutation["path"][-1]] = mutation["value"]
    assert finding_codes(validate_contract_documents(documents)) == (mutation["code"],)


def test_bundle_contract() -> None:
    assert finding_codes(validate_contract_bundle(ROOT)) == ()
