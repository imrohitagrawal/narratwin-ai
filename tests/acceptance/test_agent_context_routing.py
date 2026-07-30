"""Behavioral RED for deterministic Issue #319 routing fixtures."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.agent_context import build_packet, canonical_digest, intersect_authority, route_request

FIXTURE_PATH = Path("docs/agent-context/fixtures/routing-fixtures-v1.json")


def _fixture_set() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text()))


def _manifest(fixture_set: dict[str, Any]) -> dict[str, Any]:
    module_by_rule = {
        rule_id: module["moduleId"]
        for module in fixture_set["moduleVocabulary"]
        for rule_id in module["ruleIds"]
    }
    return {
        "schemaVersion": "ContextPolicyManifestV1",
        "modules": fixture_set["moduleVocabulary"],
        "rules": [
            {**rule, "moduleId": module_by_rule[rule["ruleId"]], "status": "active"}
            for rule in fixture_set["ruleVocabulary"]
        ],
        "budgets": fixture_set["budgets"],
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
    assert {finding.code for finding in findings} == {
        "CTX.FIXTURE.DRIFT",
        "CTX.ROUTE.AMBIGUOUS",
    }


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


@pytest.mark.parametrize(
    ("fixture_id", "expected_code"),
    [
        ("RFV1-02-BACKEND-TDD", "CTX.AUTH.CHILD_WIDENS_ISSUE"),
        ("RFV1-07-MERGE-CLOSEOUT", "CTX.AUTH.EXTERNAL_NOT_GRANTED"),
    ],
)
def test_cli_fails_closed_when_representative_authority_exceeds_issue_319(
    fixture_id: str, expected_code: str
) -> None:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "scripts.agent_context.cli",
            "route",
            "--commit",
            "WORKTREE",
            "--fixture-id",
            fixture_id,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "FAIL_CLOSED"
    assert expected_code in {finding["code"] for finding in payload["findings"]}


def test_cli_requires_real_parent_for_write_child_authority() -> None:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "scripts.agent_context.cli",
            "route",
            "--commit",
            "WORKTREE",
            "--fixture-id",
            "RFV1-09-DISJOINT-WRITE-CHILD",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "CTX.CAPSULE.PARENT_REQUIRED" in {item["code"] for item in payload["findings"]}


def test_cli_intersects_child_with_supplied_narrower_parent_capsule() -> None:
    base = ["python3", "-m", "scripts.agent_context.cli", "route", "--commit", "WORKTREE"]
    parent_run = subprocess.run(
        [*base, "--fixture-id", "RFV1-06-COLD-PR-REVIEW"],
        check=True, capture_output=True, text=True,
    )
    parent = json.loads(parent_run.stdout)["taskCapsule"]
    child_run = subprocess.run(
        [*base, "--fixture-id", "RFV1-08-READONLY-CHILD",
         "--parent-capsule-json", json.dumps(parent)],
        check=False, capture_output=True, text=True,
    )
    payload = json.loads(child_run.stdout)
    codes = {item["code"] for item in payload["findings"]}
    assert child_run.returncode == 1 and "CTX.AUTH.CHILD_WIDENS_PARENT" in codes and payload["taskCapsule"]["parentCapsuleId"].endswith(parent["capsuleDigest"])
def test_cli_rejects_digest_consistent_semantically_invalid_parent() -> None:
    base = ["python3", "-m", "scripts.agent_context.cli", "route", "--commit", "WORKTREE"]
    run = subprocess.run([*base, "--fixture-id", "RFV1-06-COLD-PR-REVIEW"], check=True, capture_output=True, text=True)
    parent = json.loads(run.stdout)["taskCapsule"]
    manifest = json.loads(Path("docs/agent-context/context-policy-manifest-v1.json").read_text())
    repository, issue = (manifest["authorityProfiles"][key] for key in ("repository", "issue"))
    parent["authority"], _ = intersect_authority(repository, issue, None, issue)
    parent["authorityDigest"] = canonical_digest(parent["authority"])
    parent["capsuleDigest"] = canonical_digest({k: v for k, v in parent.items() if k != "capsuleDigest"})
    child = subprocess.run([*base, "--fixture-id", "RFV1-09-DISJOINT-WRITE-CHILD", "--parent-capsule-json", json.dumps(parent)], check=False, capture_output=True, text=True)
    codes = {item["code"] for item in json.loads(child.stdout)["findings"]}
    assert child.returncode == 1
    assert "CTX.MODE.READ_ONLY_WRITE" in codes


def test_emitted_capsule_records_inherited_repository_denies() -> None:
    result = subprocess.run(
        [
            "python3", "-m", "scripts.agent_context.cli", "route",
            "--commit", "WORKTREE", "--fixture-id", "RFV1-06-COLD-PR-REVIEW",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    manifest = json.loads(Path("docs/agent-context/context-policy-manifest-v1.json").read_text())
    inherited = set(manifest["authorityProfiles"]["repository"]["denies"]["reservedDecisions"])
    recorded = set(payload["taskCapsule"]["authority"]["denies"]["reservedDecisions"])
    assert inherited <= recorded
    assert payload["taskCapsule"]["budgets"]["actualLines"] == len(json.dumps(payload["taskCapsule"], indent=2, sort_keys=True).splitlines())
