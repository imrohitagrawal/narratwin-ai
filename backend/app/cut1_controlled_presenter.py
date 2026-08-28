"""Canonical, pure Cut 1 controlled-presenter evidence evaluation.

An empty finding tuple means only that the frozen synthetic, blocked entry
fixture is internally coherent. It is not Cut 1 acceptance or media authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Finding:
    """One deterministic primary controlled-presenter finding."""

    code: str
    path: str
    message: str


SCHEMA_VERSION = "Cut1ControlledPresenterEvidenceV1"
BASE_COMMIT = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
SOURCE_SHA256 = "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e"
SCRIPT_SHA256 = "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435"
PROJECT_FACTS_SHA256 = "cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b"
LIVE_BINDING_SHA256 = "89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702"
REGISTRY_SHA256 = "eb31a953b85ffaf2c43f54e4da7fb89eda740c724967a9301f726c6091ab01c2"
FROZEN_EVIDENCE_REGISTER_SHA256 = (
    "a021bdfdefbdbf52d185f1a06434146ac4c7aa5313d5959f1b6d5918427784b8"
)
EXPECTED_CELLS = (
    ("meera", "LANDSCAPE"), ("meera", "PORTRAIT"),
    ("raj", "LANDSCAPE"), ("raj", "PORTRAIT"),
    ("myra", "LANDSCAPE"), ("myra", "PORTRAIT"),
)

TOP_KEYS = {"schemaVersion", "authority", "cells", "approvals", "dependencyPosture", "providerPosture", "observability", "acceptance"}
AUTHORITY_KEYS = {"baseCommit", "sourceSha256", "scriptSha256", "projectFactsSha256", "liveBindingSha256", "evidenceRegisterSha256", "evaluationSha256", "evaluationSourceSha256"}
CELL_KEYS = {"presenterId", "presenterVersion", "registrySha256", "language", "aspectRatio", "evidenceState", "lineage", "rights", "artifact", "metrics", "decision"}
LINEAGE_KEYS = {"retrievalSha256", "claimSupportSha256", "presenterBindingSha256", "narrationSha256", "voiceProfileId", "voiceProfileVersion", "audioSha256", "captionSha256", "captionCueEvidenceSha256", "manifestSha256", "evaluationSha256", "evaluatorVersion", "metricEvidenceSha256", "approvalId", "approvalRequestSha256", "approvalSha256", "approvedArtifactSha256", "approvedManifestSha256", "artifactAuthorId", "reviewerId", "approvedAt", "approvalCurrent", "approvalUseCount", "approvalValidUntil", "approvalRevoked"}
RIGHTS_KEYS = {"fictionalIdentity", "derivativeAuthorized", "originalOverwritten", "provenanceSha256", "deletionRef"}
ARTIFACT_KEYS = {"mediaKind", "mimeType", "regularFile", "decoded", "placeholder", "sha256", "createdAt", "byteCount", "durationMs", "width", "height", "audioPresent", "captionsPresent"}
ARTIFACT_DENY_KEYS = {"providerClass", "provider", "adapterKind", "supportsRealVideo", "realVideoProduced"}
METRIC_KEYS = {"gazeRatio", "maxOffCameraMs", "lipOffsetP95Ms", "maxLipErrorMs", "captionWordAccuracy", "captionCoverage", "maxCaptionGapMs", "citationCoverage", "acceptedUnsupportedClaims", "abstentionRate", "identityMismatchCount", "faceMismatchCount", "hairMismatchCount", "clothingMismatchCount", "backgroundMismatchCount", "presenterSwitchMismatchCount", "severeMotionDefectCount", "maxRepeatedGesture", "keyboardPassed", "screenReaderPassed", "visibleFocusPassed", "reducedMotionPassed", "captionsEnabledByDefaultPassed", "contrastRatio", "scriptEvaluationP95Ms", "previewAfterReadyMs", "repeatScriptSha256", "repeatPresenterBindingSha256", "repeatEvaluatorSha256", "repeatManifestSha256", "repeatBindingEqual"}
APPROVAL_KEYS = {"speechApprovalStatus", "artifactApprovalStatus", "humanApprovalStatus"}
DEPENDENCY_KEYS = {"audioOwnership", "providerAuthority", "humanStudyAuthority", "derivativeReadiness"}
PROVIDER_KEYS = {"mode", "model", "enabled", "configSha256", "credentialCount", "egressAttemptCount", "providerCallCount", "retryCount", "spendMicrousd"}
OBS_KEYS = {"tenantId", "projectId", "requestId", "traceId", "runId", "provenanceRef", "deletionRef", "outcomeReason", "refusalReason", "errorReason", "fallbackReason", "startedAt", "finishedAt", "durationMs", "rawSensitiveContentPresent", "providerPayloadPresent"}
ACCEPTANCE_KEYS = {"technicalDecision", "cut1Decision", "humanEvidencePresent"}


def finding_codes(findings: Sequence[Finding]) -> tuple[str, ...]:
    """Return stable finding codes for independent literal expectations."""

    return tuple(finding.code for finding in findings)


def _finding(code: str, path: str) -> Finding:
    return Finding(code=code, path=path, message=f"{path} failed {code}.")


def _one(code: str, path: str) -> tuple[Finding, ...]:
    return (_finding(code, path),)


def _framed_sha256(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _synthetic_digest(index: int, label: str) -> str:
    return _framed_sha256("Cut1SyntheticRedV1", str(index), label)


def _approval_request_sha256(cell: Mapping[str, Any]) -> str:
    lineage, artifact = cell["lineage"], cell["artifact"]
    return _framed_sha256("Cut1ApprovalRequestV1", artifact["sha256"], lineage["manifestSha256"], lineage["presenterBindingSha256"])


def _approval_sha256(cell: Mapping[str, Any]) -> str:
    lineage, artifact = cell["lineage"], cell["artifact"]
    return _framed_sha256("Cut1ApprovalV1", lineage["approvalId"], lineage["approvalRequestSha256"], lineage["reviewerId"], lineage["artifactAuthorId"], artifact["createdAt"], lineage["approvedAt"], lineage["approvalValidUntil"], str(lineage["approvalRevoked"]).lower(), str(lineage["approvalUseCount"]))


def _evidence_register_sha256(evidence: Mapping[str, Any]) -> str:
    cells = [{key: cell[key] for key in ("presenterId", "presenterVersion", "registrySha256", "language", "aspectRatio", "evidenceState", "lineage", "rights", "artifact")} for cell in sorted(evidence["cells"], key=lambda item: (item["presenterId"], item["aspectRatio"]))]
    canonical = json.dumps({"providerPosture": evidence["providerPosture"], "cells": cells}, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Mapping):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_non_finite(item) for item in value)
    return False


def _exact_mapping(value: Any, keys: set[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == keys


def _structure_is_closed(evidence: Mapping[str, Any]) -> bool:
    if not _exact_mapping(evidence, TOP_KEYS) or not _exact_mapping(evidence.get("authority"), AUTHORITY_KEYS) or not isinstance(evidence.get("cells"), list):
        return False
    for cell in evidence["cells"]:
        if not _exact_mapping(cell, CELL_KEYS) or not _exact_mapping(cell.get("lineage"), LINEAGE_KEYS) or not _exact_mapping(cell.get("rights"), RIGHTS_KEYS) or not _exact_mapping(cell.get("metrics"), METRIC_KEYS):
            return False
        artifact = cell.get("artifact")
        if not isinstance(artifact, Mapping) or not ARTIFACT_KEYS.issubset(artifact) or not set(artifact).issubset(ARTIFACT_KEYS | ARTIFACT_DENY_KEYS):
            return False
    return all(_exact_mapping(evidence.get(key), expected) for key, expected in (("approvals", APPROVAL_KEYS), ("dependencyPosture", DEPENDENCY_KEYS), ("providerPosture", PROVIDER_KEYS), ("observability", OBS_KEYS), ("acceptance", ACCEPTANCE_KEYS)))


def _artifact_deny_finding(cells: Sequence[Mapping[str, Any]]) -> Finding | None:
    for index, cell in enumerate(cells):
        artifact = cell.get("artifact")
        if not isinstance(artifact, Mapping):
            continue
        labels = " ".join(str(value).lower() for value in (artifact.get("providerClass"), artifact.get("provider"), artifact.get("adapterKind")) if value is not None)
        if "externalavatarproviderstub" in labels or "external-avatar-stub" in labels:
            return _finding("CUT1.PROVIDER.STUB_EVIDENCE", f"$.cells[{index}].artifact")
        if "mockavatarprovider" in labels or "mock_local" in labels or "mock" in labels:
            return _finding("CUT1.PROVIDER.MOCK_EVIDENCE", f"$.cells[{index}].artifact")
        if artifact.get("supportsRealVideo") is False or artifact.get("realVideoProduced") is False:
            return _finding("CUT1.MEDIA.REAL_VIDEO_REQUIRED", f"$.cells[{index}].artifact")
    return None


def _lineage_finding(cell: Mapping[str, Any], index: int) -> Finding | None:
    lineage, presenter = cell["lineage"], cell["presenterId"]
    expected = (
        ("narrationSha256", _synthetic_digest(index, "narration"), "CUT1.LINEAGE.NARRATION"),
        ("audioSha256", _synthetic_digest(index, "audio"), "CUT1.LINEAGE.AUDIO"),
        ("captionSha256", _synthetic_digest(index, "caption"), "CUT1.LINEAGE.CAPTION"),
        ("manifestSha256", _synthetic_digest(index, "manifest"), "CUT1.LINEAGE.MANIFEST"),
        ("evaluationSha256", _synthetic_digest(index, "evaluation"), "CUT1.LINEAGE.EVALUATION"),
        ("metricEvidenceSha256", _synthetic_digest(index, "metric-evidence"), "CUT1.LINEAGE.METRIC_EVIDENCE"),
        ("voiceProfileId", f"voice-{presenter}", "CUT1.LINEAGE.VOICE_PROFILE"),
        ("voiceProfileVersion", "v1", "CUT1.LINEAGE.VOICE_VERSION"),
        ("retrievalSha256", _synthetic_digest(index, "retrieval"), "CUT1.LINEAGE.RETRIEVAL"),
        ("claimSupportSha256", _synthetic_digest(index, "claim-support"), "CUT1.LINEAGE.CLAIM_SUPPORT"),
        ("captionCueEvidenceSha256", _synthetic_digest(index, "caption-cues"), "CUT1.LINEAGE.CAPTION_CUES"),
        ("evaluatorVersion", "v1", "CUT1.LINEAGE.EVALUATOR_VERSION"),
    )
    for field, wanted, code in expected:
        if lineage[field] != wanted:
            return _finding(code, f"$.cells[{index - 1}].lineage.{field}")
    if cell["registrySha256"] != REGISTRY_SHA256:
        return _finding("CUT1.LINEAGE.REGISTRY", f"$.cells[{index - 1}].registrySha256")
    if cell["presenterVersion"] != "v1":
        return _finding("CUT1.LINEAGE.PRESENTER_VERSION", f"$.cells[{index - 1}].presenterVersion")
    if lineage["presenterBindingSha256"] != _synthetic_digest(index, "presenter-binding"):
        return _finding("CUT1.LINEAGE.PRESENTER_BINDING", f"$.cells[{index - 1}].lineage.presenterBindingSha256")
    return None


def _media_finding(cell: Mapping[str, Any], index: int) -> Finding | None:
    artifact, path = cell["artifact"], f"$.cells[{index - 1}].artifact"
    if artifact["placeholder"] is not False:
        return _finding("CUT1.MEDIA.PLACEHOLDER", f"{path}.placeholder")
    if artifact["decoded"] is not True:
        return _finding("CUT1.MEDIA.CORRUPT", f"{path}.decoded")
    if artifact["mimeType"] != "video/mp4":
        return _finding("CUT1.MEDIA.TYPE", f"{path}.mimeType")
    if artifact["byteCount"] == 0:
        return _finding("CUT1.MEDIA.EMPTY", f"{path}.byteCount")
    if artifact["regularFile"] is not True:
        return _finding("CUT1.MEDIA.NONREGULAR", f"{path}.regularFile")
    if not isinstance(artifact["byteCount"], int) or isinstance(artifact["byteCount"], bool):
        return _finding("CUT1.INPUT.MALFORMED", f"{path}.byteCount")
    if artifact["byteCount"] < 0 or artifact["byteCount"] > 50_000_000:
        return _finding("CUT1.MEDIA.OVERSIZED", f"{path}.byteCount")
    if artifact["audioPresent"] is not True:
        return _finding("CUT1.MEDIA.NO_AUDIO", f"{path}.audioPresent")
    if artifact["captionsPresent"] is not True:
        return _finding("CUT1.MEDIA.NO_CAPTIONS", f"{path}.captionsPresent")
    if artifact["sha256"] != _synthetic_digest(index, "artifact") and cell["lineage"]["approvedArtifactSha256"] != artifact["sha256"]:
        return _finding("CUT1.MEDIA.FOREIGN", f"{path}.sha256")
    if not isinstance(artifact["durationMs"], int) or isinstance(artifact["durationMs"], bool) or artifact["durationMs"] <= 0:
        return _finding("CUT1.MEDIA.DURATION", f"{path}.durationMs")
    dimensions = (1920, 1080) if cell["aspectRatio"] == "LANDSCAPE" else (1080, 1920)
    if (artifact["width"], artifact["height"]) != dimensions:
        return _finding("CUT1.MEDIA.DIMENSIONS", path)
    if artifact["mediaKind"] != "VIDEO":
        return _finding("CUT1.MEDIA.KIND", f"{path}.mediaKind")
    return None


def _approval_finding(cell: Mapping[str, Any], index: int, started_at: datetime) -> Finding | None:
    lineage, artifact = cell["lineage"], cell["artifact"]
    path = f"$.cells[{index - 1}].lineage"
    if lineage["approvalCurrent"] is not True:
        return _finding("CUT1.APPROVAL.STALE", f"{path}.approvalCurrent")
    if lineage["approvedArtifactSha256"] != artifact["sha256"]:
        return _finding("CUT1.APPROVAL.ARTIFACT_MISMATCH", f"{path}.approvedArtifactSha256")
    if lineage["approvedManifestSha256"] != lineage["manifestSha256"]:
        return _finding("CUT1.APPROVAL.MANIFEST_MISMATCH", f"{path}.approvedManifestSha256")
    if lineage["reviewerId"] == lineage["artifactAuthorId"]:
        return _finding("CUT1.APPROVAL.SELF_AUTHORED", path)
    if lineage["approvalRequestSha256"] != _approval_request_sha256(cell):
        return _finding("CUT1.APPROVAL.REQUEST_MISMATCH", f"{path}.approvalRequestSha256")
    if lineage["approvalUseCount"] != 1:
        return _finding("CUT1.APPROVAL.REPLAYED", f"{path}.approvalUseCount")
    artifact_created = _parse_time(artifact["createdAt"])
    approved_at = _parse_time(lineage["approvedAt"])
    valid_until = _parse_time(lineage["approvalValidUntil"])
    if artifact_created is None or approved_at is None or valid_until is None:
        return _finding("CUT1.APPROVAL.TIME_INVALID", path)
    if approved_at != started_at:
        return _finding("CUT1.APPROVAL.TIME_INVALID", f"{path}.approvedAt")
    if lineage["approvalRevoked"] is not False:
        return _finding("CUT1.APPROVAL.REVOKED", f"{path}.approvalRevoked")
    if valid_until <= started_at:
        return _finding("CUT1.APPROVAL.EXPIRED", f"{path}.approvalValidUntil")
    if artifact_created >= approved_at:
        return _finding("CUT1.APPROVAL.PRE_ARTIFACT", f"$.cells[{index - 1}].artifact.createdAt")
    if lineage["approvalSha256"] != _approval_sha256(cell):
        return _finding("CUT1.APPROVAL.DIGEST_MISMATCH", f"{path}.approvalSha256")
    return None


def _rights_finding(cell: Mapping[str, Any], index: int) -> Finding | None:
    rights, path = cell["rights"], f"$.cells[{index - 1}].rights"
    if rights["originalOverwritten"] is not False:
        return _finding("CUT1.RIGHTS.ORIGINAL_OVERWRITTEN", f"{path}.originalOverwritten")
    provenance_changed = rights["provenanceSha256"] != _synthetic_digest(index, "provenance")
    deletion_changed = rights["deletionRef"] != f"delete-{index}"
    if provenance_changed and not deletion_changed:
        return _finding("CUT1.RIGHTS.PROVENANCE", f"{path}.provenanceSha256")
    if deletion_changed and not provenance_changed:
        return _finding("CUT1.RIGHTS.DELETION_REF", f"{path}.deletionRef")
    return None


def _provider_finding(provider: Mapping[str, Any]) -> Finding | None:
    path = "$.providerPosture"
    checks = (
        (provider["credentialCount"] != 0, "CUT1.PROVIDER.CREDENTIAL", "credentialCount"),
        (provider["egressAttemptCount"] != 0, "CUT1.PROVIDER.EGRESS", "egressAttemptCount"),
        (provider["spendMicrousd"] != 0, "CUT1.PROVIDER.SPEND", "spendMicrousd"),
        (provider["enabled"] is not False, "CUT1.PROVIDER.ACTIVATED", "enabled"),
        (provider["providerCallCount"] != 0, "CUT1.PROVIDER.CALL", "providerCallCount"),
        (provider["retryCount"] != 0, "CUT1.PROVIDER.RETRY", "retryCount"),
        (provider["model"] != "NONE", "CUT1.PROVIDER.MODEL", "model"),
        (provider["mode"] != "LOCAL_KEY_FREE_DISABLED_EXTERNAL", "CUT1.PROVIDER.MODE", "mode"),
    )
    for failed, code, field in checks:
        if failed:
            return _finding(code, f"{path}.{field}")
    config = _framed_sha256("Cut1ProviderPostureV1", provider["mode"], provider["model"], str(provider["enabled"]).lower(), str(provider["credentialCount"]), str(provider["egressAttemptCount"]), str(provider["providerCallCount"]), str(provider["retryCount"]), str(provider["spendMicrousd"]))
    if provider["configSha256"] != config:
        return _finding("CUT1.PROVIDER.CONFIG", f"{path}.configSha256")
    return None


def _observability_finding(observability: Mapping[str, Any]) -> Finding | None:
    path = "$.observability"
    if observability["rawSensitiveContentPresent"] is not False:
        return _finding("CUT1.PRIVACY.SENSITIVE_CONTENT", f"{path}.rawSensitiveContentPresent")
    if observability["providerPayloadPresent"] is not False:
        return _finding("CUT1.PRIVACY.PROVIDER_PAYLOAD", f"{path}.providerPayloadPresent")
    for field, code in (
        ("traceId", "CUT1.OBSERVABILITY.TRACE_MISSING"),
        ("tenantId", "CUT1.OBSERVABILITY.TENANT_MISSING"),
        ("projectId", "CUT1.OBSERVABILITY.PROJECT_MISSING"),
        ("requestId", "CUT1.OBSERVABILITY.REQUEST_MISSING"),
        ("runId", "CUT1.OBSERVABILITY.RUN_MISSING"),
        ("provenanceRef", "CUT1.OBSERVABILITY.PROVENANCE_MISSING"),
        ("deletionRef", "CUT1.OBSERVABILITY.DELETION_MISSING"),
    ):
        if not isinstance(observability[field], str) or not observability[field]:
            return _finding(code, f"{path}.{field}")
    for field, expected, code in (
        ("outcomeReason", "ENTRY_ORACLE_TARGET_ONLY", "CUT1.OBSERVABILITY.OUTCOME_INVALID"),
        ("refusalReason", "NONE", "CUT1.OBSERVABILITY.REFUSAL_INVALID"),
        ("errorReason", "NONE", "CUT1.OBSERVABILITY.ERROR_INVALID"),
        ("fallbackReason", "NONE", "CUT1.OBSERVABILITY.FALLBACK_INVALID"),
    ):
        if observability[field] != expected:
            return _finding(code, f"{path}.{field}")
    started, finished = _parse_time(observability["startedAt"]), _parse_time(observability["finishedAt"])
    if started is None:
        return _finding("CUT1.OBSERVABILITY.START_INVALID", f"{path}.startedAt")
    if finished is None or finished < started:
        return _finding("CUT1.OBSERVABILITY.FINISH_INVALID", f"{path}.finishedAt")
    duration = observability["durationMs"]
    if not isinstance(duration, int) or isinstance(duration, bool) or not 0 <= duration <= 300_000:
        return _finding("CUT1.OBSERVABILITY.DURATION_INVALID", f"{path}.durationMs")
    if duration != int((finished - started).total_seconds() * 1000):
        return _finding("CUT1.OBSERVABILITY.DURATION_INVALID", f"{path}.durationMs")
    return None


def _metric_finding(cell: Mapping[str, Any], index: int) -> Finding | None:
    metrics, path = cell["metrics"], f"$.cells[{index - 1}].metrics"
    numeric = ("gazeRatio", "maxOffCameraMs", "lipOffsetP95Ms", "maxLipErrorMs", "captionWordAccuracy", "captionCoverage", "maxCaptionGapMs", "citationCoverage", "acceptedUnsupportedClaims", "abstentionRate", "identityMismatchCount", "faceMismatchCount", "hairMismatchCount", "clothingMismatchCount", "backgroundMismatchCount", "presenterSwitchMismatchCount", "severeMotionDefectCount", "maxRepeatedGesture", "contrastRatio", "scriptEvaluationP95Ms", "previewAfterReadyMs")
    if not all(_is_number(metrics[key]) for key in numeric):
        return _finding("CUT1.INPUT.MALFORMED", path)
    if metrics["gazeRatio"] < 0.8 or metrics["maxOffCameraMs"] > 2000:
        return _finding("CUT1.METRIC.C1-M01", path)
    if metrics["lipOffsetP95Ms"] > 80 or metrics["maxLipErrorMs"] > 200:
        return _finding("CUT1.METRIC.C1-M02", path)
    if metrics["captionWordAccuracy"] < 0.98 or metrics["captionCoverage"] < 0.98 or metrics["maxCaptionGapMs"] > 1000:
        return _finding("CUT1.METRIC.C1-M03", path)
    if metrics["citationCoverage"] != 1 or metrics["acceptedUnsupportedClaims"] != 0:
        return _finding("CUT1.METRIC.C1-M04", path)
    if metrics["abstentionRate"] != 1:
        return _finding("CUT1.METRIC.C1-M05", path)
    if any(metrics[key] != 0 for key in ("identityMismatchCount", "faceMismatchCount", "hairMismatchCount", "clothingMismatchCount", "backgroundMismatchCount", "presenterSwitchMismatchCount")):
        return _finding("CUT1.METRIC.C1-M06", path)
    if metrics["severeMotionDefectCount"] != 0 or metrics["maxRepeatedGesture"] > 2:
        return _finding("CUT1.METRIC.C1-M07", path)
    if metrics["contrastRatio"] < 4.5 or any(metrics[key] is not True for key in ("keyboardPassed", "screenReaderPassed", "visibleFocusPassed", "reducedMotionPassed", "captionsEnabledByDefaultPassed")):
        return _finding("CUT1.METRIC.C1-M08", path)
    if metrics["scriptEvaluationP95Ms"] > 20_000 or metrics["previewAfterReadyMs"] > 5_000:
        return _finding("CUT1.METRIC.C1-M09", path)
    lineage = cell["lineage"]
    if metrics["repeatBindingEqual"] is not True or metrics["repeatScriptSha256"] != SCRIPT_SHA256 or metrics["repeatPresenterBindingSha256"] != lineage["presenterBindingSha256"] or metrics["repeatEvaluatorSha256"] != lineage["evaluationSha256"] or metrics["repeatManifestSha256"] != lineage["manifestSha256"]:
        return _finding("CUT1.METRIC.C1-M10", path)
    return None


def evaluate_controlled_presenter(evidence: Mapping[str, Any]) -> tuple[Finding, ...]:
    """Evaluate one materialized mapping with deterministic fail-closed precedence."""

    if not isinstance(evidence, Mapping):
        return _one("CUT1.INPUT.MALFORMED", "$")
    if _contains_non_finite(evidence):
        return _one("CUT1.INPUT.NON_FINITE", "$")
    cells_value = evidence.get("cells")
    cells = cells_value if isinstance(cells_value, list) else []
    denied = _artifact_deny_finding(cells)
    if denied is not None:
        return (denied,)
    if not _structure_is_closed(evidence):
        return _one("CUT1.INPUT.MALFORMED", "$")
    if evidence["schemaVersion"] != SCHEMA_VERSION:
        return _one("CUT1.DOCUMENT.SCHEMA_VERSION", "$.schemaVersion")
    if len(cells) != len(EXPECTED_CELLS):
        return _one("CUT1.CELL.SET", "$.cells")
    if len({cell["artifact"]["sha256"] for cell in cells}) == 1:
        return _one("CUT1.CELL.POOLED", "$.cells")
    keys = [(cell["presenterId"], cell["aspectRatio"]) for cell in cells]
    if len(set(keys)) != len(keys):
        return _one("CUT1.CELL.DUPLICATE", "$.cells")
    for index, cell in enumerate(cells):
        if cell["presenterId"] not in {"meera", "raj", "myra"}:
            return _one("CUT1.CELL.UNKNOWN", f"$.cells[{index}].presenterId")
        if cell["language"] != "en":
            return _one("CUT1.CELL.LANGUAGE", f"$.cells[{index}].language")
        if cell["aspectRatio"] not in {"LANDSCAPE", "PORTRAIT"}:
            return _one("CUT1.CELL.ASPECT", f"$.cells[{index}].aspectRatio")
    if set(keys) != set(EXPECTED_CELLS):
        return _one("CUT1.CELL.SET", "$.cells")
    ordered = [next(cell for cell in cells if (cell["presenterId"], cell["aspectRatio"]) == key) for key in EXPECTED_CELLS]
    for index, cell in enumerate(ordered):
        if cell["evidenceState"] != "SYNTHETIC_RED_TARGET_NOT_EXECUTED":
            return _one("CUT1.CELL.EVIDENCE_STATE", f"$.cells[{index}].evidenceState")
        if cell["decision"] != "NOT_EXECUTED":
            return _one("CUT1.CELL.DECISION", f"$.cells[{index}].decision")

    authority = evidence["authority"]
    for field, expected, code in (
        ("baseCommit", BASE_COMMIT, "CUT1.AUTHORITY.BASE_DRIFT"),
        ("sourceSha256", SOURCE_SHA256, "CUT1.AUTHORITY.SOURCE_DRIFT"),
        ("scriptSha256", SCRIPT_SHA256, "CUT1.AUTHORITY.SCRIPT_DRIFT"),
        ("evaluationSha256", "7" * 64, "CUT1.AUTHORITY.EVALUATION_DRIFT"),
        ("projectFactsSha256", PROJECT_FACTS_SHA256, "CUT1.AUTHORITY.PROJECT_FACTS_DRIFT"),
        ("liveBindingSha256", LIVE_BINDING_SHA256, "CUT1.AUTHORITY.LIVE_BINDING_DRIFT"),
        ("evaluationSourceSha256", "8" * 64, "CUT1.AUTHORITY.EVALUATION_SOURCE_DRIFT"),
        ("evidenceRegisterSha256", FROZEN_EVIDENCE_REGISTER_SHA256, "CUT1.AUTHORITY.EVIDENCE_REGISTER_DRIFT"),
    ):
        if authority[field] != expected:
            return _one(code, f"$.authority.{field}")

    bindings = {_synthetic_digest(index, "presenter-binding") for index in range(1, 7)}
    for index, cell in enumerate(ordered, start=1):
        binding = cell["lineage"]["presenterBindingSha256"]
        if binding != _synthetic_digest(index, "presenter-binding") and binding in bindings:
            return _one("CUT1.LINEAGE.PRESENTER_SUBSTITUTED", f"$.cells[{index - 1}].lineage")
    for validator in (_lineage_finding, _media_finding):
        for index, cell in enumerate(ordered, start=1):
            found = validator(cell, index)
            if found is not None:
                return (found,)

    observability = evidence["observability"]
    started_at = _parse_time(observability["startedAt"])
    if started_at is None:
        return _one("CUT1.OBSERVABILITY.START_INVALID", "$.observability.startedAt")
    for index, cell in enumerate(ordered, start=1):
        found = _approval_finding(cell, index, started_at)
        if found is not None:
            return (found,)
    for field, expected, code in (
        ("speechApprovalStatus", "MEERA_ONLY_EXISTING_RAJ_MYRA_BLOCKED", "CUT1.APPROVAL.SPEECH_STATUS"),
        ("artifactApprovalStatus", "SYNTHETIC_RED_FIXTURE_ONLY", "CUT1.APPROVAL.ARTIFACT_STATUS"),
        ("humanApprovalStatus", "NOT_AUTHORIZED_ISSUE_432", "CUT1.APPROVAL.HUMAN_STATUS"),
    ):
        if evidence["approvals"][field] != expected:
            return _one(code, f"$.approvals.{field}")
    for index, cell in enumerate(ordered, start=1):
        found = _rights_finding(cell, index)
        if found is not None:
            return (found,)
    for index, cell in enumerate(ordered):
        if cell["rights"]["fictionalIdentity"] is not True:
            return _one("CUT1.IDENTITY.UNAUTHORIZED", f"$.cells[{index}].rights.fictionalIdentity")
        if cell["rights"]["derivativeAuthorized"] is not False:
            return _one("CUT1.DERIVATIVE.UNAUTHORIZED", f"$.cells[{index}].rights.derivativeAuthorized")
    found = _provider_finding(evidence["providerPosture"])
    if found is not None:
        return (found,)
    if _evidence_register_sha256(evidence) != FROZEN_EVIDENCE_REGISTER_SHA256:
        return _one("CUT1.AUTHORITY.EVIDENCE_REGISTER_MISMATCH", "$.authority.evidenceRegisterSha256")
    found = _observability_finding(observability)
    if found is not None:
        return (found,)
    for index, cell in enumerate(ordered):
        if cell["metrics"]["acceptedUnsupportedClaims"] != 0:
            return _one("CUT1.GROUNDING.UNSUPPORTED", f"$.cells[{index}].metrics.acceptedUnsupportedClaims")
        if cell["metrics"]["keyboardPassed"] is not True:
            return _one("CUT1.A11Y.KEYBOARD", f"$.cells[{index}].metrics.keyboardPassed")
    for index, cell in enumerate(ordered, start=1):
        found = _metric_finding(cell, index)
        if found is not None:
            return (found,)

    dependency = evidence["dependencyPosture"]
    for field, expected, code in (
        ("audioOwnership", "ISSUE_368_HANDOFF_REQUIRED", "CUT1.DEPENDENCY.AUDIO_OWNERSHIP"),
        ("humanStudyAuthority", "ISSUE_432_NOT_AUTHORIZED", "CUT1.DEPENDENCY.HUMAN_STUDY_AUTHORITY"),
        ("providerAuthority", "ISSUE_449_NOT_AUTHORIZED", "CUT1.DEPENDENCY.PROVIDER_AUTHORITY"),
        ("derivativeReadiness", "RAJ_MYRA_NOT_READY", "CUT1.DEPENDENCY.DERIVATIVE_READINESS"),
    ):
        if dependency[field] != expected:
            return _one(code, f"$.dependencyPosture.{field}")
    acceptance = evidence["acceptance"]
    if acceptance["humanEvidencePresent"] is not False:
        return _one("CUT1.DEPENDENCY.HUMAN_STUDY", "$.acceptance.humanEvidencePresent")
    if acceptance["technicalDecision"] != "ENTRY_ORACLE_TARGET_ONLY":
        return _one("CUT1.ACCEPTANCE.TECHNICAL_DECISION", "$.acceptance.technicalDecision")
    if acceptance["cut1Decision"] != "BLOCKED_NOT_ACCEPTED":
        return _one("CUT1.ACCEPTANCE.CUT1_DECISION", "$.acceptance.cut1Decision")
    return ()


__all__ = ("Finding", "evaluate_controlled_presenter", "finding_codes")
