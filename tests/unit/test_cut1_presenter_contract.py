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
    validate_human_evaluation,
    validate_provider_acceptance,
)


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64
OID = "b" * 40
DIMENSIONS = (
    "IDENTITY", "VOICE_PROSODY", "GAZE", "BLINK", "EXPRESSION", "LIP_SYNC",
    "HEAD", "TORSO_POSTURE", "ARM", "HAND_FINGER", "BODY",
    "HAIR_CLOTHING_BACKGROUND", "TIMING", "ACCESSIBILITY", "GROUNDING",
    "LANGUAGE", "PROVENANCE",
)


def ref(value: str = "evidence") -> dict[str, str]:
    return {"id": value, "sha256": SHA}


def human_record() -> dict[str, Any]:
    def rater(value: str) -> dict[str, Any]:
        return {
            "raterId": value, "independenceRef": ref(f"{value}-independence"),
            "overallSensitivity": 1, "identitySensitivity": 1,
            "limbSensitivity": 1, "temporalSensitivity": 1, "specificity": 0.9,
        }

    def cell(presenter: str, aspect: str) -> dict[str, Any]:
        return {
            "presenterId": presenter, "language": "en", "aspectRatio": aspect,
            "candidate": {
                "artifactId": f"{presenter}-{aspect.lower()}", "artifactSha256": SHA,
                "controlSha256": "c" * 64, "controlManifestSha256": "d" * 64,
                "assetSha256": SHA, "scriptSha256": SHA, "audioSha256": SHA,
                "captionSha256": SHA, "providerCandidateId": "provider",
                "modelOrEngineVersion": "pinned-v1", "tenantId": "tenant-1",
                "projectId": "project-1", "runId": f"run-{presenter}-{aspect.lower()}",
            },
            "analysis": {
                "viewerCount": 200, "forcedChoiceCount": 400, "pairCount": 20,
                "minimumRatingsPerPair": 20, "maximumRatingsPerPair": 20,
                "viewerTrialManifestSha256": SHA, "correctCount": 200,
                "unsureConfidenceCount": 20, "missingCount": 0, "pointEstimate": 0.5,
                "ciLower": 0.41, "ciUpper": 0.59, "bootstrapSuccessfulDraws": 10000,
                "bootstrapSuccessRate": 1, "modelConverged": True, "modelSingular": False,
                "simulatedPower": 0.95, "powerWilsonLower": 0.91,
                "powerSimulationCount": 100000,
            },
            "exclusions": {
                "eligibleCount": 200, "excludedCount": 0, "totalRate": 0,
                "maximumSingleReasonRate": 0, "reasonRowsSha256": SHA,
            },
            "subgroups": [],
            "dimensions": [
                {"dimension": name, "scorableEventCount": 1, "passCount": 1,
                 "uncertainCount": 0, "failCount": 0, "evidenceSha256": SHA}
                for name in DIMENSIONS
            ],
            "objectiveMetrics": {
                "eligibleSpeakingMs": 1000, "gazeAlignedMs": 800,
                "lipOffsetP95Ms": 80, "lipOver80MsLongestMs": 200,
                "captionReferenceWords": 1000, "captionSubstitutions": 5,
                "captionDeletions": 5, "captionInsertions": 5,
                "captionWordAccuracy": 0.985, "captionSpokenWordCoverage": 0.995,
                "captionLongestUncaptionedSpeechMs": 1000,
                "captionCueEvidenceSha256": SHA, "wcagEvidenceSha256": SHA,
            },
            "defectReview": {
                "calibrationCorpusSha256": SHA, "calibrationExpectationSha256": SHA,
                "calibrationInitialLabelsSha256": SHA, "calibrationClipCount": 60,
                "severePerClassCount": 10, "cleanClipCount": 30,
                "calibrationRawAgreement": 0.9, "calibrationKappa": 0.8,
                "raters": [rater("rater-1"), rater("rater-2")], "liveClipCount": 20,
                "liveInitialLabelsSha256": SHA, "liveRawAgreement": 1,
                "liveKappa": None, "kappaDisposition": "NA_ALL_INITIAL_LABELS_NOT_SEVERE",
                "adjudicatorId": "rater-3", "adjudicatorIndependenceRef": ref("rater-3-independence"),
                "disagreementLedgerSha256": SHA,
                "adjudicatedSevereDefectCount": 0,
            },
            "retest": {
                "attemptNumber": 1, "operationalInvalidRerunCount": 0,
                "revisedCandidateRetestCount": 0, "attemptKind": "INITIAL",
                "priorAttemptRef": None, "priorArtifactSha256": None,
                "freshViewerManifestSha256": SHA,
                "priorFailureVisibility": "CONCEALED_FROM_VIEWERS_AND_PRIMARY_RATERS",
            },
            "decision": "PASSED_STATISTICAL",
        }

    return {
        "schemaVersion": "Cut1HumanRealismEvaluationV1", "evaluationId": "evaluation-1",
        "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT",
        "protocolBinding": {
            "protocolId": "cut1-blinded-human-evaluation-v1", "protocolVersion": "1.0.0",
            "protocolSha256": SHA, "frozenAt": "2026-08-28T09:00:00+05:30",
            "firstExposureAt": "2026-08-28T10:00:00+05:30", "baseCommit": OID,
            "headCommit": OID, "treeOid": OID,
            "ownerDecisionRefs": [
                "https://github.com/imrohitagrawal/narratwin-ai/issues/452#issuecomment-5444058376",
                "https://github.com/imrohitagrawal/narratwin-ai/issues/452#issuecomment-5444076231",
            ],
            "analysisCodeSha256": SHA, "analysisEnvironmentSha256": SHA,
            "randomizationCommitmentSha256": SHA, "candidateManifestSha256": SHA,
        },
        "cohort": {
            "totalUniqueViewerCount": 200, "totalRatingCount": 2400,
            "trialsPerViewerTotal": 12, "viewerManifestSha256": SHA,
            "allocationManifestSha256": SHA, "deviceCalibrationSha256": SHA,
        },
        "cells": [cell(p, a) for p in ("meera", "raj", "myra") for a in ("LANDSCAPE", "PORTRAIT")],
        "studyDisposition": "PASSED_STATISTICAL", "retentionEvidenceRef": ref("retention"),
    }


def provider_record() -> dict[str, Any]:
    screened = {key: {"contentRef": ref(key), "scannerRef": ref("scanner"), "result": "CLEAN"}
                for key in ("upload", "retrievedContext", "prompt", "transcript", "providerPayload", "evaluatorPayload")}
    return {
        "schemaVersion": "Cut1PresenterProviderAcceptanceV1", "candidateId": "google-pro",
        "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT",
        "presenter": {
            "presenterId": "meera", "role": "PRIMARY", "assetSha256": SHA,
            "identityKind": "SYNTHETIC_FICTIONAL", "cloned": False,
            "realPersonLikeness": False, "framing": "WAIST_UP", "handsVisible": True,
            "gesturesScored": True, "originalOverwritten": False,
            "derivativeAuthorityRef": ref("derivative"),
        },
        "provider": {
            "legalEntity": "Google LLC", "product": "Cloud TTS", "api": "Gemini TTS",
            "modelOrEngine": "gemini-2.5-pro-tts", "version": "pinned-v1", "lifecycle": "GA",
            "region": "us-central1", "endpoint": "https://example.invalid/tts",
            "identityOrVoiceId": "prebuilt-voice", "identityOrVoiceType": "PREBUILT_NON_CLONED",
            "modality": "VOICE", "role": "BASELINE",
            "officialSourceUrls": ["https://docs.cloud.google.com/text-to-speech/docs/gemini-tts"],
            "sourceCheckpoint": ref("source-checkpoint"),
        },
        "rights": {
            "provenanceRef": ref("provenance"), "rightsEvidenceRef": ref("rights"),
            "consentEvidenceRef": ref("consent"), "consentStatus": "CURRENT",
            "consentBinding": {
                "presenterId": "meera", "projectId": "project-1",
                "scope": "CONTROLLED_CUT1_EXPERIMENT", "mediaTypes": ["VOICE"],
                "version": "v1", "effectiveAt": "2026-08-01T00:00:00Z",
                "expiresAt": "2027-08-01T00:00:00Z", "revokedAt": None,
            },
            "identityCompatibility": "VERIFIED", "commercialUseDecision": "UNKNOWN",
            "derivativeUseDecision": "UNKNOWN", "termsRef": ref("terms"),
            "dpaRef": ref("dpa"), "licenseRef": ref("license"), "publicationAllowed": False,
        },
        "privacy": {
            "inputClassification": "APPROVED_SYNTHETIC_NON_SENSITIVE",
            "controllerProcessorRole": "PROVIDER_PROCESSOR", "trainingUse": "DISABLED_VERIFIED",
            "processingRegion": "us-central1", "storageRegion": "us-central1",
            "crossBorderTransfer": "NONE_VERIFIED", "subprocessorRef": ref("subprocessors"),
            "backupDeletionRef": ref("backup-deletion"), "retentionRef": ref("retention"),
            "providerDeletionSlaRef": ref("deletion-sla"),
        },
        "egress": {
            "enabled": False, "method": "POST", "endpoint": "https://example.invalid/tts",
            "redirectsAllowed": False, "proxy": "NONE", "dnsPolicyRef": ref("dns"),
            "tlsPolicyRef": ref("tls"), "approvalRef": None,
        },
        "credentialRef": {"scheme": "SecretRef", "id": "provider/key", "scope": "tts", "owner": "security"},
        "screening": screened,
        "experiment": {
            "enabled": False, "currency": "USD", "pricingRef": ref("pricing"),
            "rateSnapshotRef": ref("rate"), "maxCalls": 0, "maxSeconds": 0,
            "maxAttemptsPerCall": 1, "maxRetries": 0, "maxConcurrency": 1,
            "timeoutMs": 1, "perCallCeilingMicros": 0, "experimentCeilingMicros": 0,
            "providerHardCapMicros": None, "chargedOnFailure": "UNKNOWN",
            "spendState": "NOT_AUTHORIZED", "ownerApprovalRef": None,
        },
        "idempotency": {
            "key": "key-1", "requestFingerprint": SHA, "tenantId": "tenant-1",
            "projectId": "project-1", "actorId": "actor-1", "state": "FAILED_PRE_EGRESS",
            "persistedBeforeEgress": True, "egressPossible": False, "retryPermitted": False,
            "reservationDisposition": "RELEASED",
        },
        "lineage": {
            "tenantId": "tenant-1", "projectId": "project-1", "actorId": "actor-1",
            "runId": "run-1", "traceId": "trace-1", "requestId": "request-1",
            "sourceRef": ref("source"), "scriptRef": ref("script"),
            "evaluationRef": ref("evaluation"), "artifactRef": ref("artifact"),
        },
        "outputValidation": {
            "providerSuccess": False, "schemaValid": False, "contentSafe": False,
            "moderationRef": ref("moderation"), "checksumValid": False,
            "sizeValid": False, "accepted": False,
        },
        "disclosure": {
            "policyRef": ref("disclosure"), "textSha256": SHA, "artifactEmbedded": False,
            "complianceSurface": "APPROVED_COMPLIANCE_METADATA", "consistent": True,
        },
        "deletion": {
            "localState": "NOT_REQUESTED", "providerState": "NOT_REQUESTED",
            "providerJobId": "not-created", "tombstoneRef": ref("tombstone"),
            "confirmationRef": None, "cacheState": "ACTIVE",
            "resurrectionCheckRef": ref("resurrection"), "cleanupRef": ref("cleanup"),
        },
        "observability": {
            "eventRef": ref("event"), "redactionPolicyRef": ref("redaction"),
            "latencyMs": 0, "billableUnits": 0, "costMicros": 0,
            "rawContentLogged": False, "secretResolutionLogged": False, "raterPiiLogged": False,
        },
        "reproducibility": {
            "repeatCount": 3, "outputSha256s": ["1" * 64, "2" * 64, "3" * 64],
            "nondeterministic": True, "selectionDecision": "NOT_SCORED",
        },
        "eligibility": "NOT_AUTHORIZED",
    }


def changed(source: dict[str, Any], path: tuple[Any, ...], value: Any) -> dict[str, Any]:
    result = copy.deepcopy(source)
    cursor: Any = result
    for key in path[:-1]:
        cursor = cursor[key]
    if isinstance(cursor[path[-1]], dict) and isinstance(value, dict):
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


H = "CUT1.HUMAN."
P = "CUT1.PROVIDER."
CASES = (
    Case("human-valid", "human", (), None, (), None),
    Case("viewer-199", "human", ("cells", 0, "analysis", "viewerCount"), 199, (H + "SAMPLE",), "H01"),
    Case("cohort-199", "human", ("cohort", "totalUniqueViewerCount"), 199, (H + "COHORT",), "H01B"),
    Case("ratings-399", "human", ("cells", 0, "analysis", "forcedChoiceCount"), 399, (H + "SAMPLE",), "H02"),
    Case("pair-allocation-19", "human", ("cells", 0, "analysis", "pairCount"), 19, (H + "PAIR_ALLOCATION",), "H02B"),
    Case("lower-bound-inclusive", "human", ("cells", 0, "analysis", "ciLower"), 0.4, (H + "EQUIVALENCE",), "H03"),
    Case("upper-bound-inclusive", "human", ("cells", 0, "analysis", "ciUpper"), 0.6, (H + "EQUIVALENCE",), "H04"),
    Case("singular-model", "human", ("cells", 0, "analysis", "modelSingular"), True, (H + "MODEL",), "H05"),
    Case("bootstrap-9999", "human", ("cells", 0, "analysis", "bootstrapSuccessfulDraws"), 9999, (H + "BOOTSTRAP",), "H06"),
    Case("bootstrap-success-low", "human", ("cells", 0, "analysis", "bootstrapSuccessRate"), 0.989, (H + "BOOTSTRAP",), "H07"),
    Case("power-sims-low", "human", ("cells", 0, "analysis", "powerSimulationCount"), 99999, (H + "POWER",), "H08"),
    Case("power-wilson-low", "human", ("cells", 0, "analysis", "powerWilsonLower"), 0.899, (H + "POWER",), "H09"),
    Case("freeze-after-exposure", "human", ("protocolBinding", "frozenAt"), "2026-08-28T11:00:00+05:30", (H + "PREREGISTRATION",), "H10"),
    Case("duplicate-cell", "human", ("cells", 1, "aspectRatio"), "LANDSCAPE", (H + "CELL_SET",), "H11"),
    Case("dimension-fail", "human", ("cells", 0, "dimensions", 0, "failCount"), 1, (H + "DIMENSION",), "H12"),
    Case("dimension-uncertain", "human", ("cells", 0, "dimensions", 1, "uncertainCount"), 1, (H + "DIMENSION",), "H13"),
    Case("zero-scorable", "human", ("cells", 0, "dimensions", 2, "scorableEventCount"), 0, (H + "DIMENSION",), "H14"),
    Case("zero-gaze-denominator", "human", ("cells", 0, "objectiveMetrics", "eligibleSpeakingMs"), 0, (H + "GAZE",), "H15"),
    Case("lip-p95-high", "human", ("cells", 0, "objectiveMetrics", "lipOffsetP95Ms"), 81, (H + "LIP_SYNC",), "H16"),
    Case("lip-duration-high", "human", ("cells", 0, "objectiveMetrics", "lipOver80MsLongestMs"), 201, (H + "LIP_SYNC",), "H17"),
    Case("caption-accuracy-low", "human", ("cells", 0, "objectiveMetrics", "captionWordAccuracy"), 0.979, (H + "CAPTION_ACCURACY",), "H18"),
    Case("caption-coverage-low", "human", ("cells", 0, "objectiveMetrics", "captionSpokenWordCoverage"), 0.979, (H + "CAPTION_COVERAGE",), "H19"),
    Case("caption-gap-high", "human", ("cells", 0, "objectiveMetrics", "captionLongestUncaptionedSpeechMs"), 1001, (H + "CAPTION_GAP",), "H20"),
    Case("severe-veto", "human", ("cells", 0, "defectReview", "adjudicatedSevereDefectCount"), 1, (H + "SEVERE_DEFECT",), "H21"),
    Case("kappa-low", "human", ("cells", 0, "defectReview", "calibrationKappa"), 0.799, (H + "CALIBRATION",), "H22"),
    Case("rater-sensitivity-low", "human", ("cells", 0, "defectReview", "raters", 0, "identitySensitivity"), 0.99, (H + "CALIBRATION",), "H23"),
    Case("same-byte-retest", "human", ("cells", 0, "retest"), {"attemptNumber": 2, "revisedCandidateRetestCount": 1, "attemptKind": "REVISED_CANDIDATE_RETEST", "priorAttemptRef": ref("prior"), "priorArtifactSha256": SHA}, (H + "RETEST",), "H24"),
    Case("provider-valid", "provider", (), None, (), None),
    Case("role-substitution", "provider", ("presenter", "role"), "SECOND_BACKUP", (P + "PRESENTER_ROLE",), "P01"),
    Case("consent-expired", "provider", ("rights", "consentStatus"), "EXPIRED", (P + "CONSENT",), "P02"),
    Case("consent-subject-mismatch", "provider", ("rights", "consentBinding", "presenterId"), "raj", (P + "CONSENT_BINDING",), "P02B"),
    Case("identity-unverified", "provider", ("rights", "identityCompatibility"), "UNVERIFIED", (P + "IDENTITY_COMPATIBILITY",), "P03"),
    Case("training-unknown", "provider", ("privacy", "trainingUse"), "UNKNOWN", (P + "PRIVACY",), "P04"),
    Case("region-unknown", "provider", ("privacy", "processingRegion"), "UNKNOWN", (P + "PRIVACY",), "P05"),
    Case("raw-secret-scheme", "provider", ("credentialRef", "scheme"), "ApiKey", (P + "SECRET_REF",), "P06"),
    Case("prompt-screen-blocked", "provider", ("screening", "prompt", "result"), "BLOCKED", (P + "SCREENING",), "P07"),
    Case("provider-enabled", "provider", ("experiment", "enabled"), True, (P + "ACTIVATION",), "P08"),
    Case("egress-enabled", "provider", ("egress", "enabled"), True, (P + "EGRESS",), "P08B"),
    Case("call-cap-nonzero", "provider", ("experiment", "maxCalls"), 1, (P + "SPEND",), "P09"),
    Case("billable-unknown", "provider", ("experiment", "spendState"), "BILLABLE_UNKNOWN", (P + "BILLABLE_UNKNOWN",), "P10"),
    Case("tenant-mismatch", "provider", ("idempotency", "tenantId"), "tenant-2", (P + "TENANT_BOUNDARY",), "P11"),
    Case("not-persisted", "provider", ("idempotency", "persistedBeforeEgress"), False, (P + "IDEMPOTENCY",), "P12"),
    Case("pending-retry", "provider", ("idempotency",), {"state": "PENDING", "egressPossible": True, "retryPermitted": True}, (P + "IDEMPOTENCY",), "P13"),
    Case("unsafe-accepted", "provider", ("outputValidation", "accepted"), True, (P + "OUTPUT_DISTRUST",), "P14"),
    Case("disclosure-inconsistent", "provider", ("disclosure", "consistent"), False, (P + "DISCLOSURE",), "P15"),
    Case("pending-confirmation", "provider", ("deletion",), {"providerState": "PENDING", "confirmationRef": ref("premature-confirmation")}, (P + "DELETION",), "P16"),
    Case("confirmed-cache-active", "provider", ("deletion", "providerState"), "CONFIRMED", (P + "DELETION",), "P17"),
    Case("repeat-count-low", "provider", ("reproducibility", "repeatCount"), 2, (P + "REPRODUCIBILITY",), "P18"),
    Case("false-eligibility", "provider", ("eligibility",), "ELIGIBLE", (P + "FALSE_ELIGIBILITY",), "P19"),
)


def materialize(case: Case) -> dict[str, Any]:
    source = human_record() if case.contract == "human" else provider_record()
    return source if not case.path else changed(source, case.path, case.value)


def test_static_contract_schemas_and_literal_authority_hashes() -> None:
    for name in ("cut1-human-realism-evaluation-v1.schema.json", "cut1-presenter-provider-acceptance-v1.schema.json"):
        schema = json.loads((ROOT / "docs/governance/schemas" / name).read_text())
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object" and schema["additionalProperties"] is False
    protocol = json.loads((ROOT / "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json").read_text())
    assert protocol["authority"][1]["bodySha256"] == "4f599502ee3658a97c5dbfee8296193880a732641eea1a26b196e3ce9d79ab1c"
    assert protocol["authority"][2]["bodySha256"] == "391de2e22898416fa9192d9bd47f8bb3e97d6a73d263e65721ff4e6b99448a33"
    assert hashlib.sha256(protocol["endpoint"]["prompt"].encode()).hexdigest() == protocol["endpoint"]["promptSha256"]
    matrix = json.loads((ROOT / "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json").read_text())
    bakeoff = json.loads((ROOT / "docs/governance/cut1-provider-bakeoff-contract-v1.json").read_text())
    assert matrix["assetCheckpoint"]["bodySha256"] == "c6383a73611294f43bbd7528015f6e661f42d4c3d5b0000483f25a19daa748ee"
    assert bakeoff["sourceCheckpoint"]["bodySha256"] == "19f1619ce83591f4e70285603487d823b7ebe90b208030dd4370846aff425a77"


def test_finite_case_and_mutant_inventory() -> None:
    assert len(CASES) >= 36
    assert sum(case.mutant_id is not None for case in CASES) >= 15
    assert len({case.case_id for case in CASES}) == len(CASES)
    assert len({case.mutant_id for case in CASES if case.mutant_id}) == sum(case.mutant_id is not None for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_frozen_semantic_case(case: Case) -> None:
    validator = validate_human_evaluation if case.contract == "human" else validate_provider_acceptance
    assert finding_codes(validator(materialize(case))) == case.expected


def test_bundle_contract() -> None:
    assert finding_codes(validate_contract_bundle(ROOT)) == ()
