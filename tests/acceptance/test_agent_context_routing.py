"""Behavioral RED for deterministic Issue #319 routing fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.agent_context import build_packet, route_request

FIXTURE_PATH = Path("docs/agent-context/fixtures/routing-fixtures-v1.json")


def _fixture_set() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text()))


def _manifest(fixture_set: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": "ContextPolicyManifestV1",
        "modules": fixture_set["moduleVocabulary"],
        "rules": fixture_set["ruleVocabulary"],
    }


@pytest.mark.parametrize("fixture_index", range(9))
def test_router_matches_independently_frozen_cohort(fixture_index: int) -> None:
    fixture_set = _fixture_set()
    fixture = fixture_set["fixtures"][fixture_index]
    receipt, findings = route_request(
        _manifest(fixture_set), fixture["request"], fixture_set=fixture_set
    )
    assert findings == []
    assert receipt["routeId"] == fixture["expectedRoute"]["routeId"]
    assert receipt["includedModules"] == fixture["includedModules"]
    assert receipt["rejectedModules"] == fixture["rejectedModules"]
    assert receipt["dependencyClosure"] == fixture["dependencyClosure"]


def test_unknown_task_class_fails_closed() -> None:
    fixture_set = _fixture_set()
    request = copy.deepcopy(fixture_set["fixtures"][0]["request"])
    request["operation"] = "UNKNOWN_OPERATION"
    _, findings = route_request(_manifest(fixture_set), request, fixture_set=fixture_set)
    assert {finding.code for finding in findings} == {"CTX.ROUTE.UNKNOWN"}


def test_ambiguous_task_class_fails_closed() -> None:
    fixture_set = _fixture_set()
    duplicated = copy.deepcopy(fixture_set["fixtures"][0])
    duplicated["fixtureId"] = "RFV1-DUPLICATE"
    fixture_set["fixtures"].append(duplicated)
    _, findings = route_request(
        _manifest(fixture_set), duplicated["request"], fixture_set=fixture_set
    )
    assert {finding.code for finding in findings} == {"CTX.ROUTE.AMBIGUOUS"}


def test_packet_rejects_omitted_critical_rule() -> None:
    fixture_set = _fixture_set()
    fixture = fixture_set["fixtures"][7]
    route, _ = route_request(
        _manifest(fixture_set), fixture["request"], fixture_set=fixture_set
    )
    route["includedModules"] = [
        module for module in fixture["includedModules"] if module["moduleId"] != "repo-constitution"
    ]
    _, findings = build_packet(
        _manifest(fixture_set),
        route,
        {module["moduleId"]: module["reason"] for module in route["includedModules"]},
        line_ceiling=600,
        token_ceiling=6000,
    )
    assert "CTX.PACKET.CRITICAL_RULE_MISSING" in {finding.code for finding in findings}


def test_parent_summary_cannot_replace_binding_module() -> None:
    fixture_set = _fixture_set()
    fixture = fixture_set["fixtures"][7]
    route, _ = route_request(
        _manifest(fixture_set), fixture["request"], fixture_set=fixture_set
    )
    _, findings = build_packet(
        _manifest(fixture_set),
        route,
        {"parent-summary": "All repository rules were followed."},
        line_ceiling=600,
        token_ceiling=6000,
    )
    assert "CTX.PACKET.SUMMARY_SUBSTITUTION" in {finding.code for finding in findings}


def test_router_output_cannot_become_expected_fixture() -> None:
    fixture_set = _fixture_set()
    fixture_set["provenance"]["routerOutputUsedAsExpectedValue"] = True
    request = fixture_set["fixtures"][0]["request"]
    _, findings = route_request(_manifest(fixture_set), request, fixture_set=fixture_set)
    assert "CTX.FIXTURE.CIRCULAR_ORACLE" in {finding.code for finding in findings}


def test_frozen_fixture_content_drift_fails_closed() -> None:
    fixture_set = _fixture_set()
    fixture_set["fixtures"][0]["includedModules"][0]["reason"] = "Synchronized oracle edit."
    _, findings = route_request(
        _manifest(fixture_set), fixture_set["fixtures"][0]["request"], fixture_set=fixture_set
    )
    assert "CTX.FIXTURE.DRIFT" in {finding.code for finding in findings}


def test_router_derives_manifest_closure_instead_of_trusting_fixture_copy() -> None:
    fixture_set = _fixture_set()
    fixture = fixture_set["fixtures"][7]
    fixture["dependencyClosure"] = ["repo-constitution"]
    receipt, findings = route_request(
        _manifest(fixture_set), fixture["request"], fixture_set=fixture_set
    )
    assert "CTX.ROUTE.CLOSURE_MISMATCH" in {finding.code for finding in findings}
    assert receipt["dependencyClosure"] != fixture["dependencyClosure"]
