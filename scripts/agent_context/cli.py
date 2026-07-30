"""Command-line validation and deterministic packet generation for Issue #319."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.agent_context.core import (
    Finding,
    build_capsule,
    build_packet,
    canonical_digest,
    content_digest,
    extract_binding,
    intersect_authority,
    load_json_bytes_strict,
    regular_file_within,
    route_request,
    detect_state_contradictions,
    validate_path,
    validate_capsule,
    validate_manifest,
    validate_schema_instance,
)

MANIFEST = Path("docs/agent-context/context-policy-manifest-v1.json")
FIXTURES = Path("docs/agent-context/fixtures/routing-fixtures-v1.json")
CURRENT_STATE = Path("docs/agent-context/current-state-v1.json")
HISTORY = Path("docs/agent-context/history-v1.jsonl")
CONTRACTS = Path("docs/agent-context/contracts-v1.schema.json")


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _resolve_commit(root: Path, commit: str) -> str:
    if commit == "WORKTREE":
        return commit
    return _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()


def _read_source(root: Path, commit: str, location: str) -> bytes:
    path_findings = validate_path(location, repository_root=root if commit == "WORKTREE" else None)
    if path_findings:
        raise ValueError(f"unsafe source path: {location}")
    if commit == "WORKTREE":
        if not regular_file_within(root, location):
            raise ValueError(f"source is not a confined regular file: {location}")
        return (root / location).read_bytes()
    tree_entry = _git(root, "ls-tree", commit, "--", location).decode().strip()
    if not tree_entry.startswith("100") or " blob " not in tree_entry:
        raise ValueError(f"source is not a committed regular file: {location}")
    return _git(root, "show", f"{commit}:{location}")


def _read_json(root: Path, commit: str, path: Path) -> dict[str, Any]:
    return load_json_bytes_strict(_read_source(root, commit, path.as_posix()))


def _materialize(
    root: Path, commit: str, manifest: dict[str, Any]
) -> tuple[dict[str, bytes], dict[str, str], list[Finding]]:
    raw: dict[str, bytes] = {}
    text: dict[str, str] = {}
    findings: list[Finding] = []
    for module in manifest.get("modules", []):
        module_id = str(module["moduleId"])
        location = str(module["location"])
        try:
            source = _read_source(root, commit, location)
            if content_digest(source) != module.get("sourceSha256"):
                findings.append(Finding("CTX.MODULE.SOURCE_HASH_MISMATCH", module_id))
            selected = extract_binding(source.decode("utf-8"), module["binding"])
        except (OSError, UnicodeDecodeError, ValueError, KeyError) as exc:
            findings.append(Finding("CTX.MODULE.SOURCE_UNAVAILABLE", f"{module_id}:{exc}"))
            continue
        raw[module_id] = selected.encode("utf-8")
        text[module_id] = selected
    return raw, text, sorted(set(findings))


def _validate(
    root: Path, commit: str
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any], dict[str, Any], list[Finding]]:
    contract = _read_json(root, commit, CONTRACTS)
    manifest = _read_json(root, commit, MANIFEST)
    raw, text, source_findings = _materialize(root, commit, manifest)
    findings = source_findings + validate_schema_instance(
        manifest, contract, "ContextPolicyManifestV1"
    ) + validate_manifest(
        manifest,
        repository_root=root if commit == "WORKTREE" else None,
        repository_commit=None if commit == "WORKTREE" else commit,
        module_content=raw,
    )
    current_state: dict[str, Any] = {}
    try:
        current_state = _read_json(root, commit, CURRENT_STATE)
        findings.extend(validate_schema_instance(current_state, contract, "CurrentStateV1"))
        status_text = _read_source(root, commit, "docs/STATUS.md").decode("utf-8")
        prose_claims: list[dict[str, str]] = []
        status_row = next(
            (line for line in status_text.splitlines() if line.startswith("| SSV1-NEXT |")),
            "",
        )
        if "semantic-repair-slice1-complete" in status_row:
            prose_claims.append(
                {"id": "issue-317-lifecycle", "value": "complete"}
            )
        findings.extend(
            detect_state_contradictions(
                current_state,
                prose_claims=prose_claims,
                historical_entries=[],
            )
        )
        history_text = _read_source(root, commit, HISTORY.as_posix()).decode("utf-8")
        for line_number, line in enumerate(history_text.splitlines(), 1):
            entry = load_json_bytes_strict(line.encode("utf-8"))
            findings.extend(validate_schema_instance(entry, contract, "HistoryEntryV1"))
            if not isinstance(entry, dict) or entry.get("status") != "historical" or entry.get("authorizing") is not False:
                findings.append(Finding("CTX.STATE.HISTORY_AS_CURRENT", str(line_number)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(Finding("CTX.STATE.CURRENT_MISSING", str(exc)))
    return manifest, text, contract, current_state, sorted(set(findings))


def _authority_layers(
    manifest: dict[str, Any], fixture: dict[str, Any], issue_scope: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    del fixture
    profiles = manifest.get("authorityProfiles", {})
    repository_authority = profiles.get("repository", {}) if isinstance(profiles, dict) else {}
    issue_authority = profiles.get("issue", {}) if isinstance(profiles, dict) else {}
    scope = issue_scope.get("scope", {})
    allowed = {str(item) for item in scope.get("allowed_prefixes", [])}
    writes = set(issue_authority.get("allows", {}).get("writePaths", []))
    if writes != allowed:
        raise ValueError("Issue authority does not match pinned preflight scope")
    return repository_authority, issue_authority, None


def _render(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _findings_payload(findings: list[Finding]) -> list[dict[str, str]]:
    return [{"code": finding.code, "detail": finding.detail} for finding in findings]


def _run_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    commit = _resolve_commit(root, args.commit)
    manifest, content, contract, _, findings = _validate(root, commit)
    _render(
        {
            "schemaVersion": "ContextValidationReceiptV1",
            "repositoryCommit": commit,
            "manifestDigest": canonical_digest(manifest),
            "contractSchemaDigest": canonical_digest(contract),
            "validatedModuleIds": sorted(content),
            "findings": _findings_payload(findings),
            "status": "PASS" if not findings else "FAIL_CLOSED",
        }
    )
    return 0 if not findings else 1


def _run_route(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    commit = _resolve_commit(root, args.commit)
    manifest, content, contract, current_state, findings = _validate(root, commit)
    if findings:
        _render({"schemaVersion": "ContextRouteCommandV1", "repositoryCommit": commit,
                 "findings": _findings_payload(findings), "status": "FAIL_CLOSED"})
        return 1
    fixture_set = _read_json(root, commit, FIXTURES)
    fixtures = [item for item in fixture_set.get("fixtures", []) if item.get("fixtureId") == args.fixture_id]
    if len(fixtures) != 1:
        findings.append(Finding("CTX.ROUTE.UNKNOWN", args.fixture_id))
        _render({"schemaVersion": "ContextRouteCommandV1", "findings": _findings_payload(findings)})
        return 1
    fixture = fixtures[0]
    request_findings = validate_schema_instance(
        fixture.get("request"), contract, "RoutingRequestV1"
    )
    if request_findings:
        _render({"schemaVersion": "ContextRouteCommandV1", "repositoryCommit": commit,
                 "findings": _findings_payload(request_findings), "status": "FAIL_CLOSED"})
        return 1
    route, route_findings = route_request(manifest, fixture["request"], fixture_set=fixture_set)
    if route_findings:
        _render({"schemaVersion": "ContextRouteCommandV1", "repositoryCommit": commit,
                 "routingReceipt": route, "findings": _findings_payload(route_findings),
                 "status": "FAIL_CLOSED"})
        return 1
    route["repositoryCommit"] = commit
    bootstrap = content["repo-constitution"]
    bootstrap_budget = manifest.get("budgets", {}).get("universalBootstrap", {})
    bootstrap_metrics = {
        "lines": len(bootstrap.splitlines()),
        "estimatedTokens": (len(bootstrap.encode("utf-8")) + 3) // 4,
        "lineCeiling": int(bootstrap_budget.get("lineCeiling", 0)),
        "tokenCeiling": int(bootstrap_budget.get("tokenCeiling", 0)),
    }
    route["bootstrapMetrics"] = bootstrap_metrics
    route["receiptDigest"] = canonical_digest({key: value for key, value in route.items() if key != "receiptDigest"})
    route_findings.extend(validate_schema_instance(route, contract, "RoutingReceiptV1"))
    issue_scope = json.loads(content["issue-scope"])
    branch = str(issue_scope["branch"])
    base_commit = _resolve_commit(root, str(current_state["baseCommit"]))
    head_commit = commit if commit != "WORKTREE" else _resolve_commit(root, "HEAD")
    repository_authority, issue_authority, parent_capsule = _authority_layers(
        manifest, fixture, issue_scope
    )
    modules_by_id = {str(item.get("moduleId")): item for item in manifest.get("modules", [])}
    role = str(fixture.get("request", {}).get("role", ""))
    if args.parent_capsule_json:
        parent_capsule = load_json_bytes_strict(args.parent_capsule_json.encode())
    if "CHILD" in role and parent_capsule is None:
        route_findings.append(Finding("CTX.CAPSULE.PARENT_REQUIRED"))
    if "CHILD" not in role and parent_capsule is not None:
        route_findings.append(Finding("CTX.CAPSULE.PARENT_UNEXPECTED"))
    if parent_capsule is not None:
        matches = [item for item in fixture_set.get("fixtures", []) if item.get("fixtureId") == parent_capsule.get("fixtureId")]
        if len(matches) != 1 or parent_capsule.get("parentCapsuleId") is not None:
            route_findings.append(Finding("CTX.CAPSULE.PARENT_ROUTE_INVALID"))
        else:
            parent_fixture = matches[0]
            parent_route, parent_route_findings = route_request(
                manifest, parent_fixture["request"], fixture_set=fixture_set
            )
            parent_route.update({"repositoryCommit": head_commit, "bootstrapMetrics": bootstrap_metrics})
            parent_route["receiptDigest"] = canonical_digest({k: v for k, v in parent_route.items() if k != "receiptDigest"})
            parent_hashes = {module_id: str(modules_by_id[module_id]["contentSha256"]) for module_id in parent_route["dependencyClosure"]}
            route_findings.extend(parent_route_findings)
            route_findings.extend(validate_capsule(
                parent_capsule, repository_authority=repository_authority,
                issue_authority=issue_authority, parent_capsule=None, actual_branch=branch,
                actual_head=head_commit, actual_base=base_commit, contract_schema=contract,
                expected_rule_ids=set(parent_route["selectedRuleIds"]),
                expected_module_hashes=parent_hashes, expected_fixture=parent_fixture,
                expected_route=parent_route, expected_repository=str(manifest.get("repository")),
            ))
    parent_id = f"{parent_capsule.get('capsuleId')}@{parent_capsule.get('capsuleDigest')}" if parent_capsule else None
    proposed_capsule = build_capsule(
        manifest, fixture, route, repository_commit=head_commit, base_commit=base_commit,
        branch=branch, parent_capsule_id=parent_id,
    )
    parent_authority = (
        parent_capsule.get("authority")
        if isinstance(parent_capsule, dict) and isinstance(parent_capsule.get("authority"), dict)
        else None
    )
    effective_authority, proposal_findings = intersect_authority(
        repository_authority,
        issue_authority,
        parent_authority,
        proposed_capsule["authority"],
    )
    capsule = build_capsule(
        manifest,
        fixture,
        route,
        repository_commit=head_commit,
        base_commit=base_commit,
        branch=branch,
        parent_capsule_id=parent_id,
        authority_override=effective_authority,
    )
    expected_module_hashes = {
        module_id: str(modules_by_id[module_id].get("contentSha256"))
        for module_id in route.get("dependencyClosure", [])
        if module_id in modules_by_id
    }
    capsule_findings = proposal_findings + validate_capsule(
        capsule,
        repository_authority=repository_authority,
        issue_authority=issue_authority,
        parent_capsule=parent_capsule,
        actual_branch=branch,
        actual_head=head_commit,
        actual_base=base_commit,
        repository_root=root if commit == "WORKTREE" else None,
        contract_schema=contract,
        expected_rule_ids={str(item) for item in route.get("selectedRuleIds", [])},
        expected_module_hashes=expected_module_hashes,
        expected_fixture=fixture, expected_route=route, expected_repository=str(manifest.get("repository")),
    )
    budget_name = str(route.get("packetBudget"))
    budget = manifest.get("budgets", {}).get(budget_name, {})
    selected_content = {
        module_id: content[module_id]
        for module_id in route.get("dependencyClosure", [])
        if module_id in content
    }
    packet, packet_findings = build_packet(
        manifest,
        route,
        selected_content,
        line_ceiling=int(budget.get("lineCeiling", 0)),
        token_ceiling=int(budget.get("tokenCeiling", 0)),
    )
    packet["repositoryCommit"] = commit
    packet["packetDigest"] = canonical_digest({key: value for key, value in packet.items() if key != "packetDigest"})
    packet_findings.extend(validate_schema_instance(packet, contract, "ContextPacketV1"))
    if bootstrap_metrics["lines"] > bootstrap_metrics["lineCeiling"] or bootstrap_metrics[
        "estimatedTokens"
    ] > bootstrap_metrics["tokenCeiling"]:
        packet_findings.append(Finding("CTX.BUDGET.BOOTSTRAP_OVERFLOW"))
    all_findings = sorted(set(findings + route_findings + capsule_findings + packet_findings))
    _render(
        {
            "schemaVersion": "ContextRouteCommandV1",
            "repositoryCommit": commit,
            "routingReceipt": route,
            "taskCapsule": capsule,
            "packet": packet,
            "findings": _findings_payload(all_findings),
            "status": "PASS" if not all_findings else "FAIL_CLOSED",
        }
    )
    return 0 if not all_findings else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--commit", default="HEAD")
    validate.set_defaults(handler=_run_validate)
    route = subparsers.add_parser("route")
    route.add_argument("--commit", default="HEAD")
    route.add_argument("--fixture-id", required=True)
    route.add_argument("--parent-capsule-json")
    route.set_defaults(handler=_run_route)
    return parser


def main() -> int:
    """Run the selected shadow command."""

    args = _parser().parse_args()
    try:
        return int(args.handler(args))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        _render(
            {
                "schemaVersion": "ContextRouteCommandV1",
                "status": "FAIL_CLOSED",
                "findings": [{"code": "CTX.COMMAND.INVALID", "detail": str(exc)}],
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
