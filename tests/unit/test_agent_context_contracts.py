"""Behavioral RED for Issue #319 contracts and authority algebra."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_context import (
    build_packet,
    canonical_digest,
    detect_state_contradictions,
    intersect_authority,
    validate_capsule,
    validate_manifest,
    validate_receipt,
    validate_schema_instance,
)

JsonObject = dict[str, Any]
SHA = "a" * 40


def _codes(findings: list[Any]) -> set[str]:
    return {finding.code for finding in findings}


def _authority(*, writes: list[str] | None = None) -> JsonObject:
    return {
        "allows": {
            "readPaths": ["docs/STATUS.md"],
            "writePaths": writes or [],
            "actions": ["READ_REPOSITORY"],
            "externalActions": [],
            "claims": ["FINDING"],
            "reservedDecisions": [],
        },
        "denies": {
            "readPaths": [],
            "writePaths": [],
            "actions": ["MERGE"],
            "externalActions": ["GITHUB_MUTATION"],
            "claims": ["APPROVAL"],
            "reservedDecisions": ["RELEASE"],
        },
    }


def _manifest() -> JsonObject:
    return {
        "schemaVersion": "ContextPolicyManifestV1",
        "manifestId": "test-manifest",
        "repository": "imrohitagrawal/narratwin-ai",
        "currentStateModuleId": "current-state",
        "modules": [
            {
                "moduleId": "repo-constitution",
                "status": "active",
                "authorityLevel": "repository",
                "location": "AGENTS.md",
                "contentSha256": "1" * 64,
                "dependsOn": [],
                "supersedes": [],
                "conflictsWith": [],
                "ruleIds": ["CONST-001"],
            },
            {
                "moduleId": "current-state",
                "status": "active",
                "authorityLevel": "current-state",
                "location": "docs/agent-context/current-state-v1.json",
                "contentSha256": "2" * 64,
                "dependsOn": ["repo-constitution"],
                "supersedes": [],
                "conflictsWith": [],
                "ruleIds": ["STATE-001"],
            },
        ],
        "rules": [
            {"ruleId": "CONST-001", "moduleId": "repo-constitution", "status": "active"},
            {"ruleId": "STATE-001", "moduleId": "current-state", "status": "active"},
        ],
    }


def _capsule(*, mode: str = "READ_ONLY", head: str = SHA) -> JsonObject:
    authority = _authority()
    return {
        "schemaVersion": "AgentTaskCapsuleV1",
        "capsuleId": "capsule-child",
        "parentCapsuleId": "capsule-parent",
        "repository": "imrohitagrawal/narratwin-ai",
        "branch": "issue-branch",
        "baseCommit": SHA,
        "expectedHead": head,
        "actionMode": mode,
        "objective": "Inspect bounded evidence.",
        "deliverable": "Findings only.",
        "claims": ["FINDING"],
        "negativeInvariants": ["No approval claim."],
        "requiredPaths": ["docs/STATUS.md"],
        "authority": authority,
        "selectedRuleIds": ["CONST-001", "STATE-001"],
        "moduleHashes": {"repo-constitution": "1" * 64, "current-state": "2" * 64},
        "requiredTests": [],
        "assumptions": [],
        "budgets": {"lineCeiling": 600, "tokenCeiling": 6000},
        "stopConditions": ["STALE_HEAD"],
        "expiresAt": "2026-07-31T00:00:00Z",
        "expectedReceiptSchema": "HandoffReceiptV1",
        "authorityDigest": canonical_digest(authority),
    }


@pytest.mark.parametrize(
    ("layer", "expected"),
    [("parent", "CTX.AUTH.CHILD_WIDENS_PARENT"), ("repository", "CTX.AUTH.CHILD_WIDENS_REPOSITORY")],
)
def test_child_authority_cannot_widen_any_layer(layer: str, expected: str) -> None:
    repository = _authority()
    issue = _authority()
    parent = _authority()
    child = _authority(writes=["backend/app/escape.py"])
    if layer == "repository":
        repository["allows"]["readPaths"] = []
        child["allows"]["readPaths"] = ["docs/STATUS.md"]
    _, findings = intersect_authority(repository, issue, parent, child)
    assert expected in _codes(findings)


def test_inherited_deny_wins_over_child_allow() -> None:
    child = _authority()
    child["allows"]["actions"].append("MERGE")
    effective, findings = intersect_authority(_authority(), _authority(), _authority(), child)
    assert "MERGE" not in effective["allows"]["actions"]
    assert "CTX.AUTH.DENY_WINS" in _codes(findings)


def test_capsule_rejects_authority_snapshot_expansion() -> None:
    capsule = _capsule()
    capsule["authority"]["allows"]["writePaths"] = ["backend/"]
    findings = validate_capsule(
        capsule,
        repository_authority=_authority(),
        issue_authority=_authority(),
        parent_capsule=_capsule(),
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert "CTX.AUTH.SNAPSHOT_DRIFT" in _codes(findings)


def test_capsule_rejects_stale_base_or_head() -> None:
    findings = validate_capsule(
        _capsule(head="b" * 40),
        repository_authority=_authority(),
        issue_authority=_authority(),
        parent_capsule=_capsule(),
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert "CTX.STALE.HEAD" in _codes(findings)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda value: value.update({"surprise": True}), "CTX.SCHEMA.UNKNOWN_FIELD"),
        (lambda value: value["modules"].pop(), "CTX.MODULE.REQUIRED_MISSING"),
        (
            lambda value: value["modules"][1].update({"dependsOn": ["missing-module"]}),
            "CTX.MODULE.DEPENDENCY_MISSING",
        ),
        (
            lambda value: value["modules"][0].update({"contentSha256": "0" * 64}),
            "CTX.MODULE.HASH_MISMATCH",
        ),
        (
            lambda value: value["modules"][0].update({"dependsOn": ["current-state"]}),
            "CTX.GRAPH.CYCLE",
        ),
        (
            lambda value: value["modules"][0].update({"conflictsWith": ["current-state"]}),
            "CTX.CONFLICT.UNRESOLVED",
        ),
        (
            lambda value: value["rules"].append(copy.deepcopy(value["rules"][0])),
            "CTX.RULE.DUPLICATE_ACTIVE",
        ),
        (
            lambda value: value["modules"][0].update({"supersedes": ["absent"]}),
            "CTX.RULE.DANGLING_SUPERSESSION",
        ),
        (
            lambda value: value.update({"currentStateModuleId": "absent"}),
            "CTX.STATE.CURRENT_MISSING",
        ),
    ],
)
def test_manifest_fails_closed_on_structural_or_authority_defect(
    mutation: Any, expected: str
) -> None:
    manifest = _manifest()
    mutation(manifest)
    findings = validate_manifest(
        manifest,
        repository_root=Path("."),
        repository_commit=SHA,
        module_content={"repo-constitution": b"different", "current-state": b"different"},
    )
    assert expected in _codes(findings)


@pytest.mark.parametrize(
    ("current", "prose", "history", "expected"),
    [
        (None, [], [], "CTX.STATE.CURRENT_MISSING"),
        (
            {"claims": [{"id": "issue-317", "value": "complete"}]},
            [{"id": "issue-317", "value": "open"}],
            [],
            "CTX.STATE.CONTRADICTION",
        ),
        (
            {"claims": []},
            [],
            [{"id": "next-action", "value": "historical-action", "status": "historical"}],
            "CTX.STATE.HISTORY_AS_CURRENT",
        ),
    ],
)
def test_current_and_historical_state_are_separate(
    current: JsonObject | None,
    prose: list[JsonObject],
    history: list[JsonObject],
    expected: str,
) -> None:
    findings = detect_state_contradictions(
        current, prose_claims=prose, historical_entries=history
    )
    assert expected in _codes(findings)


def test_duplicate_current_fact_ids_fail_closed() -> None:
    findings = detect_state_contradictions(
        {"facts": [{"id": "issue-317", "value": "open"},
                   {"id": "issue-317", "value": "complete"}]},
        prose_claims=[],
        historical_entries=[],
    )
    assert "CTX.STATE.DUPLICATE_FACT" in _codes(findings)


def _receipt() -> JsonObject:
    capsule = _capsule()
    return {
        "schemaVersion": "HandoffReceiptV1",
        "receiptId": "receipt-1",
        "capsuleId": capsule["capsuleId"],
        "parentIdentity": "primary",
        "childIdentity": "child",
        "acceptedAuthorityDigest": capsule["authorityDigest"],
        "branch": "issue-branch",
        "head": SHA,
        "manifestVersion": "v1",
        "manifestHash": "3" * 64,
        "validatedRules": ["CONST-001", "STATE-001"],
        "moduleHashes": {"repo-constitution": "1" * 64, "current-state": "2" * 64},
        "additionalSources": [],
        "filesInspected": ["docs/STATUS.md"],
        "filesChanged": [],
        "commands": [{"argv": ["git", "status"], "exitCode": 0, "result": "PASS"}],
        "findings": [],
        "claimsProved": [],
        "claimsDisproved": [],
        "claimsNotTested": [],
        "assumptions": [],
        "blockers": [],
        "residualRisks": [],
        "preventedActions": [],
        "budget": {"estimatedLines": 10, "actualLines": 10, "estimatedTokens": 20, "actualTokens": 20},
        "worktreeCollisionCheck": "CLEAR",
        "suggestedFollowUp": "none",
        "selfCertification": [],
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda value: value.pop("filesInspected"), "CTX.RECEIPT.FIELD_MISSING"),
        (lambda value: value["commands"][0].pop("exitCode"), "CTX.RECEIPT.COMMAND_INCOMPLETE"),
        (
            lambda value: value.update({"acceptedAuthorityDigest": "0" * 64}),
            "CTX.RECEIPT.AUTHORITY_MISMATCH",
        ),
        (lambda value: value.update({"head": "b" * 40}), "CTX.RECEIPT.HEAD_MISMATCH"),
        (
            lambda value: value["selfCertification"].append("APPROVAL"),
            "CTX.RECEIPT.SELF_CERTIFICATION",
        ),
    ],
)
def test_receipt_fails_closed_on_incomplete_or_overclaiming_evidence(
    mutation: Any, expected: str
) -> None:
    receipt = _receipt()
    mutation(receipt)
    findings = validate_receipt(
        receipt,
        capsule=_capsule(),
        manifest_digest="3" * 64,
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert expected in _codes(findings)


def test_packet_budget_overflow_fails_closed() -> None:
    _, findings = build_packet(
        _manifest(),
        {"routeId": "test"},
        {"repo-constitution": "authority\n" * 50},
        line_ceiling=10,
        token_ceiling=20,
    )
    assert "CTX.BUDGET.OVERFLOW" in _codes(findings)


def test_incomplete_manifest_contract_fails_closed() -> None:
    incomplete = {
        "schemaVersion": "ContextPolicyManifestV1",
        "currentStateModuleId": "current-state",
        "modules": [{"moduleId": "current-state", "status": "active"}],
        "rules": [],
    }
    assert "CTX.SCHEMA.REQUIRED" in _codes(validate_manifest(incomplete))


def test_contract_validator_enforces_one_of_minimum_and_date_time() -> None:
    contract = json.loads(Path("docs/agent-context/contracts-v1.schema.json").read_text())
    assert "CTX.SCHEMA.ONE_OF" in _codes(
        validate_schema_instance(
            "not-a-commit",
            {"$defs": {"Candidate": {"oneOf": [{"const": "WORKTREE"}, {"$ref": "#/$defs/Commit"}]},
                        "Commit": contract["$defs"]["Commit"]}},
            "Candidate",
        )
    )
    capsule = _capsule()
    capsule.update(
        {
            "capsuleDigest": "0" * 64,
            "expiresAt": "not-a-date",
            "budgets": {
                "lineCeiling": 0,
                "tokenCeiling": 0,
                "actualLines": 0,
                "actualTokens": 0,
                "estimateAlgorithm": "ceil-utf8-bytes-divided-by-4",
            },
        }
    )
    codes = _codes(validate_schema_instance(capsule, contract, "AgentTaskCapsuleV1"))
    assert {"CTX.SCHEMA.MINIMUM", "CTX.SCHEMA.FORMAT"} <= codes


def test_capsule_digest_binds_objective_and_budget() -> None:
    capsule = _capsule()
    capsule["budgets"].update({"actualLines": 1, "actualTokens": 1})
    capsule["capsuleDigest"] = canonical_digest(capsule)
    capsule["objective"] = "Widened after capsule creation."
    capsule["budgets"].update({"actualLines": 9999, "actualTokens": 9999})
    findings = validate_capsule(
        capsule,
        repository_authority=_authority(),
        issue_authority=_authority(),
        parent_capsule=_capsule(),
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert "CTX.CAPSULE.DIGEST_MISMATCH" in _codes(findings)
    assert "CTX.BUDGET.CAPSULE_OVERFLOW" in _codes(findings)


def test_receipt_rejects_wrong_schema_empty_commands_and_reserved_claims() -> None:
    receipt = _receipt()
    receipt["schemaVersion"] = "Wrong"
    receipt["commands"] = []
    receipt["claimsProved"] = ["APPROVAL", "PRODUCTION_READINESS"]
    findings = validate_receipt(
        receipt,
        capsule=_capsule(),
        manifest_digest="3" * 64,
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert {
        "CTX.SCHEMA.VERSION",
        "CTX.RECEIPT.COMMAND_MISSING",
        "CTX.RECEIPT.RESERVED_CLAIM",
    }.issubset(_codes(findings))


def test_capsule_declarative_fields_must_match_typed_authority_and_route() -> None:
    capsule = _capsule()
    capsule["claims"] = ["APPROVAL"]
    capsule["requiredPaths"] = ["docs/SECRET.md"]
    findings = validate_capsule(
        capsule,
        repository_authority=_authority(),
        issue_authority=_authority(),
        parent_capsule=_capsule(),
        actual_branch="issue-branch",
        actual_head=SHA,
        expected_rule_ids={"CONST-001"},
        expected_module_hashes={"repo-constitution": "1" * 64},
    )
    assert {
        "CTX.CAPSULE.CLAIM_SCOPE_MISMATCH",
        "CTX.CAPSULE.REQUIRED_PATH_SCOPE_MISMATCH",
        "CTX.CAPSULE.RULE_SCOPE_MISMATCH",
        "CTX.CAPSULE.MODULE_SCOPE_MISMATCH",
    } <= _codes(findings)


def test_receipt_rejects_false_evidence_and_plain_language_reserved_claim() -> None:
    receipt = _receipt()
    receipt["claimsProved"] = ["production readiness"]
    receipt["validatedRules"] = ["BOGUS-999"]
    receipt["moduleHashes"] = {"bogus": "not-a-hash"}
    receipt["filesInspected"] = ["docs/SECRET.md"]
    receipt["commands"] = [{"argv": ["false"], "exitCode": 1, "result": "PASS"}]
    findings = validate_receipt(
        receipt,
        capsule=_capsule(),
        manifest_digest="3" * 64,
        actual_branch="issue-branch",
        actual_head=SHA,
    )
    assert {
        "CTX.RECEIPT.RESERVED_CLAIM",
        "CTX.RECEIPT.RULE_MISMATCH",
        "CTX.RECEIPT.MODULE_MISMATCH",
        "CTX.RECEIPT.READ_SCOPE_MISMATCH",
        "CTX.RECEIPT.COMMAND_RESULT_MISMATCH",
    } <= _codes(findings)


def test_contract_rejects_calendar_invalid_date_time() -> None:
    contract = json.loads(Path("docs/agent-context/contracts-v1.schema.json").read_text())
    capsule = _capsule()
    capsule.update(
        {
            "capsuleDigest": "0" * 64,
            "expiresAt": "2026-99-99T99:99:99Z",
            "budgets": {
                "lineCeiling": 1,
                "tokenCeiling": 1,
                "actualLines": 0,
                "actualTokens": 0,
                "estimateAlgorithm": "ceil-utf8-bytes-divided-by-4",
            },
        }
    )
    assert "CTX.SCHEMA.FORMAT" in _codes(
        validate_schema_instance(capsule, contract, "AgentTaskCapsuleV1")
    )


def test_packet_rejects_rule_without_owning_module() -> None:
    manifest = _manifest()
    manifest["rules"].append(
        {"ruleId": "SEC-001", "moduleId": "security-boundaries", "status": "active"}
    )
    _, findings = build_packet(
        manifest,
        {
            "includedModules": [{"moduleId": "repo-constitution"}],
            "selectedRuleIds": ["SEC-001"],
        },
        {"repo-constitution": "binding authority"},
        line_ceiling=100,
        token_ceiling=1000,
    )
    assert "CTX.PACKET.RULE_MODULE_MISSING" in _codes(findings)


def test_cli_capsule_binds_distinct_repository_base_and_head() -> None:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "scripts.agent_context.cli",
            "route",
            "--commit",
            "WORKTREE",
            "--fixture-id",
            "RFV1-06-COLD-PR-REVIEW",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["taskCapsule"]["baseCommit"] == "c293b4a62a5afdaf893af83f3f23efd65f11b950"
    assert payload["taskCapsule"]["expectedHead"] == subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert payload["taskCapsule"]["baseCommit"] != payload["taskCapsule"]["expectedHead"]
