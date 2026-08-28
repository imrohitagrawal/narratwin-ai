from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from scripts.quality.cut1_presenter_contract import _valid as schema_valid


REPO = Path(__file__).parents[2]
CORPUS_PATH = REPO / "docs/governance/cut1-controlled-presenter-red-corpus-v1.json"
SCHEMA_PATH = REPO / "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json"
EXECUTOR_PATH = REPO / "scripts/quality/cut1_controlled_presenter.py"

EXPECTED_CODES = {
    "VALID-01": (),
    "CELL-01": ("CUT1.CELL.SET",),
    "CELL-02": ("CUT1.CELL.POOLED",),
    "CELL-03": ("CUT1.CELL.DUPLICATE",),
    "CELL-04": ("CUT1.CELL.UNKNOWN",),
    "AUTH-01": ("CUT1.AUTHORITY.BASE_DRIFT",),
    "AUTH-02": ("CUT1.AUTHORITY.SOURCE_DRIFT",),
    "LINEAGE-01": ("CUT1.LINEAGE.PRESENTER_SUBSTITUTED",),
    "APPROVAL-01": ("CUT1.APPROVAL.STALE",),
    "MEDIA-01": ("CUT1.MEDIA.PLACEHOLDER",),
    "MEDIA-02": ("CUT1.MEDIA.CORRUPT",),
    "GROUND-01": ("CUT1.GROUNDING.UNSUPPORTED",),
    "IDENTITY-01": ("CUT1.IDENTITY.UNAUTHORIZED",),
    "DERIVATIVE-01": ("CUT1.DERIVATIVE.UNAUTHORIZED",),
    "PROVIDER-01": ("CUT1.PROVIDER.CREDENTIAL",),
    "PROVIDER-02": ("CUT1.PROVIDER.EGRESS",),
    "PROVIDER-03": ("CUT1.PROVIDER.SPEND",),
    "A11Y-01": ("CUT1.A11Y.KEYBOARD",),
    "OBS-01": ("CUT1.PRIVACY.SENSITIVE_CONTENT",),
    "INPUT-01": ("CUT1.INPUT.NON_FINITE",),
    "M01-01": ("CUT1.METRIC.C1-M01",),
    "M02-01": ("CUT1.METRIC.C1-M02",),
    "M03-01": ("CUT1.METRIC.C1-M03",),
    "M04-01": ("CUT1.METRIC.C1-M04",),
    "M05-01": ("CUT1.METRIC.C1-M05",),
    "M06-01": ("CUT1.METRIC.C1-M06",),
    "M07-01": ("CUT1.METRIC.C1-M07",),
    "M08-01": ("CUT1.METRIC.C1-M08",),
    "M09-01": ("CUT1.METRIC.C1-M09",),
    "M10-01": ("CUT1.METRIC.C1-M10",),
    "BLOCKED-01": ("CUT1.DEPENDENCY.AUDIO_OWNERSHIP",),
    "BLOCKED-02": ("CUT1.DEPENDENCY.HUMAN_STUDY",),
}


def strict_loads(value: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in items:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = item
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(value, object_pairs_hook=pairs, parse_constant=reject_constant)


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue459_red_executor", EXECUTOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def baseline() -> dict[str, Any]:
    metrics = {
        "gazeRatio": 0.8, "maxOffCameraMs": 2000,
        "lipOffsetP95Ms": 80, "maxLipErrorMs": 200,
        "captionWordAccuracy": 0.98, "captionCoverage": 0.98,
        "maxCaptionGapMs": 1000, "citationCoverage": 1,
        "acceptedUnsupportedClaims": 0, "abstentionRate": 1,
        "identityMismatchCount": 0, "severeMotionDefectCount": 0,
        "maxRepeatedGesture": 2, "keyboardPassed": True,
        "screenReaderPassed": True, "visibleFocusPassed": True,
        "reducedMotionPassed": True, "contrastRatio": 4.5,
        "scriptEvaluationP95Ms": 20000, "previewAfterReadyMs": 5000,
        "repeatBindingEqual": True,
    }
    cells = []
    for index, (presenter, aspect) in enumerate(
        (("meera", "LANDSCAPE"), ("meera", "PORTRAIT"),
         ("raj", "LANDSCAPE"), ("raj", "PORTRAIT"),
         ("myra", "LANDSCAPE"), ("myra", "PORTRAIT")), start=1
    ):
        digest = f"{index:x}" * 64
        cells.append({
            "presenterId": presenter, "language": "en", "aspectRatio": aspect,
            "lineage": {"presenterBindingSha256": digest, "narrationSha256": digest,
                        "audioSha256": digest, "captionSha256": digest,
                        "manifestSha256": digest, "evaluationSha256": digest,
                        "metricEvidenceSha256": digest, "approvalCurrent": True},
            "rights": {"fictionalIdentity": True, "derivativeAuthorized": True,
                       "originalOverwritten": False, "provenanceSha256": digest,
                       "deletionRef": f"delete-{index}"},
            "artifact": {"mediaKind": "VIDEO", "mimeType": "video/mp4",
                         "regularFile": True, "decoded": True, "placeholder": False,
                         "sha256": digest, "byteCount": 1000, "durationMs": 10000,
                         "width": 1920 if aspect == "LANDSCAPE" else 1080,
                         "height": 1080 if aspect == "LANDSCAPE" else 1920,
                         "audioPresent": True, "captionsPresent": True},
            "metrics": copy.deepcopy(metrics), "decision": "PASSED_INDEPENDENTLY",
        })
    return {
        "schemaVersion": "Cut1ControlledPresenterEvidenceV1",
        "authority": {"baseCommit": "ab97b6eecba6db9c66c37d19b29257c7398f3ab7",
                      "sourceSha256": "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e",
                      "scriptSha256": "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435",
                      "evaluationSha256": "cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b",
                      "approvalSha256": "89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702"},
        "cells": cells,
        "approvals": {"speechApprovalCurrent": True,
                      "artifactApprovalStatus": "TECHNICAL_ONLY",
                      "humanApprovalStatus": "NOT_AUTHORIZED_ISSUE_432"},
        "dependencyPosture": {"audioOwnership": "ISSUE_368_HANDOFF_REQUIRED",
                              "providerAuthority": "ISSUE_449_NOT_AUTHORIZED",
                              "humanStudyAuthority": "ISSUE_432_NOT_AUTHORIZED",
                              "derivativeReadiness": "RAJ_MYRA_NOT_READY"},
        "providerPosture": {"mode": "LOCAL_KEY_FREE_DISABLED_EXTERNAL",
                            "enabled": False, "configSha256": "e" * 64,
                            "credentialCount": 0, "egressAttemptCount": 0,
                            "providerCallCount": 0, "retryCount": 0,
                            "spendMicrousd": 0},
        "observability": {"tenantId": "tenant-459", "projectId": "project-459",
                          "requestId": "request-459", "traceId": "trace-459",
                          "runId": "run-459", "provenanceRef": "provenance-459",
                          "deletionRef": "deletion-459",
                          "rawSensitiveContentPresent": False,
                          "providerPayloadPresent": False},
        "acceptance": {"technicalDecision": "ENTRY_ORACLE_TARGET_ONLY",
                       "cut1Decision": "BLOCKED_NOT_ACCEPTED",
                       "humanEvidencePresent": False},
    }


def set_path(value: dict[str, Any], path: str, replacement: Any) -> None:
    cursor: Any = value
    for part in path.split(".")[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    final = path.split(".")[-1]
    if isinstance(cursor, list):
        cursor[int(final)] = replacement
    else:
        cursor[final] = replacement


def materialize(mutation: dict[str, Any]) -> dict[str, Any]:
    value = baseline()
    operation = mutation["op"]
    if operation == "SET":
        set_path(value, mutation["path"], mutation["value"])
    elif operation == "DELETE_CELL":
        cell_id = mutation["cell"]
        value["cells"] = [cell for cell in value["cells"] if
                          f'{cell["presenterId"]}-en-{cell["aspectRatio"].lower()}' != cell_id]
    elif operation == "POOL_CELLS":
        for cell in value["cells"]:
            cell["artifact"]["sha256"] = "f" * 64
    elif operation == "DUPLICATE_CELL_KEY":
        value["cells"][-1]["presenterId"] = value["cells"][0]["presenterId"]
        value["cells"][-1]["aspectRatio"] = value["cells"][0]["aspectRatio"]
    elif operation == "SET_NON_FINITE":
        set_path(value, mutation["path"], float("nan"))
    elif operation == "COPY_MEERA_LINEAGE":
        target = next(cell for cell in value["cells"] if
                      f'{cell["presenterId"]}-en-{cell["aspectRatio"].lower()}' == mutation["cell"])
        target["lineage"] = copy.deepcopy(value["cells"][0]["lineage"])
    else:
        assert operation == "NONE"
    return value


def test_bootstrap_schema_corpus_and_oracle_are_closed() -> None:
    schema = strict_loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    corpus = strict_loads(CORPUS_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object" and schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "schemaVersion", "authority", "cells", "approvals", "dependencyPosture",
        "providerPosture", "observability", "acceptance"
    }
    assert schema["properties"]["cells"]["minItems"] == 6
    assert schema["properties"]["cells"]["maxItems"] == 6
    assert len(schema["properties"]["cells"]["allOf"]) == 6
    assert schema["$defs"]["cell"]["additionalProperties"] is False
    assert len(baseline()["cells"]) == 6
    assert schema_valid(baseline(), schema, schema)
    assert {(cell["presenterId"], cell["aspectRatio"]) for cell in baseline()["cells"]} == {
        (presenter, aspect) for presenter in ("meera", "raj", "myra")
        for aspect in ("LANDSCAPE", "PORTRAIT")
    }
    assert not schema_valid(materialize({"op": "SET_NON_FINITE",
                                         "path": "cells.0.metrics.gazeRatio"}), schema, schema)
    with pytest.raises(ValueError, match="duplicate JSON member"):
        strict_loads('{"case": 1, "case": 2}')
    with pytest.raises(ValueError, match="non-finite JSON number"):
        strict_loads('{"case": NaN}')
    assert corpus["authorityEffect"] == "NO_AUTHORITY_EFFECT"
    assert corpus["expectationsLocation"] == "TEST_OWNED_LITERAL_MAP"
    assert {case["id"] for case in corpus["cases"]} == set(EXPECTED_CODES)
    assert all("expected" not in case and "finding" not in case for case in corpus["cases"])
    executor = EXECUTOR_PATH.read_text(encoding="utf-8")
    assert "cut1-controlled-presenter-red-corpus" not in executor
    assert "from tests" not in executor and "import tests" not in executor
    assert "CUT1.ENTRY.NOT_IMPLEMENTED" in executor


CORPUS = strict_loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_future_behavior_rejects_each_frozen_mutation(case: dict[str, Any]) -> None:
    executor = load_module()
    actual = executor.finding_codes(executor.evaluate_controlled_presenter(
        materialize(case["mutation"])
    ))
    assert actual == EXPECTED_CODES[case["id"]]
