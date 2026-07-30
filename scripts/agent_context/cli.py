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
    load_json_strict,
    route_request,
    detect_state_contradictions,
    validate_capsule,
    validate_manifest,
)

MANIFEST = Path("docs/agent-context/context-policy-manifest-v1.json")
FIXTURES = Path("docs/agent-context/fixtures/routing-fixtures-v1.json")
CURRENT_STATE = Path("docs/agent-context/current-state-v1.json")
HISTORY = Path("docs/agent-context/history-v1.jsonl")


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
    if commit == "WORKTREE":
        return (root / location).read_bytes()
    return _git(root, "show", f"{commit}:{location}")


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


def _validate(root: Path, commit: str) -> tuple[dict[str, Any], dict[str, str], list[Finding]]:
    manifest = load_json_strict(root / MANIFEST)
    raw, text, source_findings = _materialize(root, commit, manifest)
    findings = source_findings + validate_manifest(
        manifest,
        repository_root=root,
        repository_commit=None if commit == "WORKTREE" else commit,
        module_content=raw,
    )
    try:
        current_state = load_json_strict(root / CURRENT_STATE)
        status_text = (root / "docs/STATUS.md").read_text()
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
        for line_number, line in enumerate((root / HISTORY).read_text().splitlines(), 1):
            entry = json.loads(line)
            if not isinstance(entry, dict) or entry.get("status") != "historical" or entry.get("authorizing") is not False:
                findings.append(Finding("CTX.STATE.HISTORY_AS_CURRENT", str(line_number)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(Finding("CTX.STATE.CURRENT_MISSING", str(exc)))
    return manifest, text, sorted(set(findings))


def _render(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _findings_payload(findings: list[Finding]) -> list[dict[str, str]]:
    return [{"code": finding.code, "detail": finding.detail} for finding in findings]


def _run_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    commit = _resolve_commit(root, args.commit)
    manifest, content, findings = _validate(root, commit)
    _render(
        {
            "schemaVersion": "ContextValidationReceiptV1",
            "repositoryCommit": commit,
            "manifestDigest": canonical_digest(manifest),
            "validatedModuleIds": sorted(content),
            "findings": _findings_payload(findings),
            "status": "PASS" if not findings else "FAIL_CLOSED",
        }
    )
    return 0 if not findings else 1


def _run_route(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    commit = _resolve_commit(root, args.commit)
    manifest, content, findings = _validate(root, commit)
    fixture_set = load_json_strict(root / FIXTURES)
    fixtures = [item for item in fixture_set.get("fixtures", []) if item.get("fixtureId") == args.fixture_id]
    if len(fixtures) != 1:
        findings.append(Finding("CTX.ROUTE.UNKNOWN", args.fixture_id))
        _render({"schemaVersion": "ContextRouteCommandV1", "findings": _findings_payload(findings)})
        return 1
    fixture = fixtures[0]
    route, route_findings = route_request(manifest, fixture["request"], fixture_set=fixture_set)
    route["repositoryCommit"] = commit
    route["receiptDigest"] = canonical_digest({key: value for key, value in route.items() if key != "receiptDigest"})
    try:
        branch = _git(root, "branch", "--show-current").decode().strip() or "DETACHED"
    except ValueError:
        branch = "DETACHED"
    capsule = build_capsule(
        manifest,
        fixture,
        route,
        repository_commit=commit,
        branch=branch,
    )
    capsule_authority = capsule["authority"]
    capsule_findings = validate_capsule(
        capsule,
        repository_authority=capsule_authority,
        issue_authority=capsule_authority,
        parent_capsule=capsule,
        actual_branch=branch,
        actual_head=commit,
        actual_base=commit,
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
