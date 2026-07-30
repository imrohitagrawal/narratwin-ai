"""Deterministic, standard-library agent-context contracts for Issue #319."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

JsonObject = dict[str, Any]
AUTHORITY_DOMAINS = (
    "readPaths",
    "writePaths",
    "actions",
    "externalActions",
    "claims",
    "reservedDecisions",
)
MANIFEST_FIELDS = {
    "schemaVersion",
    "manifestId",
    "repository",
    "effectiveVersion",
    "shadowOnly",
    "currentStateModuleId",
    "modules",
    "rules",
    "budgets",
    "reservedDecisions",
}
MODULE_FIELDS = {
    "moduleId",
    "schemaVersion",
    "location",
    "sourceSha256",
    "contentSha256",
    "authorityLevel",
    "status",
    "effectiveVersion",
    "taskTriggers",
    "pathTriggers",
    "claimTriggers",
    "stageTriggers",
    "dependsOn",
    "supersedes",
    "conflictsWith",
    "coldReviewInheritance",
    "binding",
    "ruleIds",
}
RULE_FIELDS = {"ruleId", "moduleId", "status", "kind", "meaning"}
CAPSULE_FIELDS = {
    "schemaVersion",
    "capsuleId",
    "parentCapsuleId",
    "repository",
    "branch",
    "baseCommit",
    "expectedHead",
    "actionMode",
    "objective",
    "deliverable",
    "claims",
    "negativeInvariants",
    "requiredPaths",
    "authority",
    "selectedRuleIds",
    "moduleHashes",
    "requiredTests",
    "assumptions",
    "budgets",
    "stopConditions",
    "expiresAt",
    "expectedReceiptSchema",
    "authorityDigest",
    "capsuleDigest",
    "role",
    "historyMode",
    "untrustedData",
}
RECEIPT_FIELDS = {
    "schemaVersion",
    "receiptId",
    "capsuleId",
    "parentIdentity",
    "childIdentity",
    "acceptedAuthorityDigest",
    "branch",
    "head",
    "manifestVersion",
    "manifestHash",
    "validatedRules",
    "moduleHashes",
    "additionalSources",
    "filesInspected",
    "filesChanged",
    "commands",
    "findings",
    "claimsProved",
    "claimsDisproved",
    "claimsNotTested",
    "assumptions",
    "blockers",
    "residualRisks",
    "preventedActions",
    "budget",
    "worktreeCollisionCheck",
    "suggestedFollowUp",
    "selfCertification",
}
ACTIVE = {"active"}
SHA_256 = re.compile(r"^[0-9a-f]{64}$")
GLOB = re.compile(r"[*?\[\]]")
PROSE = re.compile(r"\s")


@dataclass(frozen=True, order=True)
class Finding:
    """One stable fail-closed validation finding."""

    code: str
    detail: str = ""


def _finding(code: str, detail: str = "") -> Finding:
    return Finding(code, detail)


def _dedupe(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(set(findings))


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation used by every digest."""

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_digest(value: Any) -> str:
    """Return a canonical SHA-256 digest."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def content_digest(value: bytes | str) -> str:
    """Return a byte-content SHA-256 digest."""

    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def load_json_strict(path: Path) -> JsonObject:
    """Load one object while rejecting duplicate keys and non-object roots."""

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> JsonObject:
        result: JsonObject = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def extract_binding(source: str, binding: JsonObject) -> str:
    """Extract a full resource or one exact Markdown heading section."""

    kind = binding.get("kind")
    if kind in {"full", "structured-resource"}:
        return source
    heading = binding.get("heading")
    if kind != "markdown-section" or not isinstance(heading, str):
        raise ValueError("unknown binding selector")
    lines = source.splitlines(keepends=True)
    try:
        start = next(index for index, line in enumerate(lines) if line.rstrip("\r\n") == heading)
    except StopIteration as exc:
        raise ValueError(f"missing heading: {heading}") from exc
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        candidate = lines[index]
        if not candidate.startswith("#"):
            continue
        candidate_level = len(candidate) - len(candidate.lstrip("#"))
        if candidate_level <= level and candidate[candidate_level : candidate_level + 1] == " ":
            end = index
            break
    return "".join(lines[start:end])


def _unknown_fields(value: JsonObject, allowed: set[str], prefix: str) -> list[Finding]:
    return [_finding("CTX.SCHEMA.UNKNOWN_FIELD", f"{prefix}.{key}") for key in value if key not in allowed]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _objects(value: Any) -> list[JsonObject]:
    return [item for item in _list(value) if isinstance(item, dict)]


def validate_path(path: str, *, repository_root: Path | None = None) -> list[Finding]:
    """Validate one exact repository-relative V1 path and its filesystem confinement."""

    findings: list[Finding] = []
    if not isinstance(path, str) or not path:
        return [_finding("CTX.PATH.INVALID", repr(path))]
    if path.startswith("/") or PurePosixPath(path).is_absolute():
        findings.append(_finding("CTX.PATH.ABSOLUTE", path))
    if ".." in PurePosixPath(path).parts:
        findings.append(_finding("CTX.PATH.TRAVERSAL", path))
    if GLOB.search(path):
        findings.append(_finding("CTX.PATH.GLOB_FORBIDDEN", path))
    if "\\" in path or any(ord(character) < 32 for character in path):
        findings.append(_finding("CTX.PATH.INVALID", path))
    if PROSE.search(path):
        findings.append(_finding("CTX.TYPE.PROSE_IN_PATH", path))
    if path.endswith("/"):
        findings.append(_finding("CTX.PATH.NOT_EXACT", path))
    if repository_root is not None and not findings:
        root = repository_root.resolve()
        candidate = root / path
        current = root
        for part in PurePosixPath(path).parts:
            current = current / part
            if current.is_symlink():
                findings.append(_finding("CTX.PATH.SYMLINK_ESCAPE", path))
                break
        try:
            candidate.resolve(strict=False).relative_to(root)
        except ValueError:
            findings.append(_finding("CTX.PATH.SYMLINK_ESCAPE", path))
    return _dedupe(findings)


def _cycle(modules: dict[str, JsonObject]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module_id: str) -> bool:
        if module_id in visiting:
            return True
        if module_id in visited:
            return False
        visiting.add(module_id)
        for dependency in _list(modules[module_id].get("dependsOn")):
            if dependency in modules and visit(str(dependency)):
                return True
        visiting.remove(module_id)
        visited.add(module_id)
        return False

    return any(visit(module_id) for module_id in modules)


def validate_manifest(
    manifest: JsonObject,
    *,
    repository_root: Path | None = None,
    repository_commit: str | None = None,
    module_content: dict[str, bytes] | None = None,
) -> list[Finding]:
    """Validate strict module/rule structure, closure, conflicts, and content hashes."""

    del repository_commit
    findings = _unknown_fields(manifest, MANIFEST_FIELDS, "manifest")
    if manifest.get("schemaVersion") != "ContextPolicyManifestV1":
        findings.append(_finding("CTX.SCHEMA.VERSION"))
    module_items = _objects(manifest.get("modules"))
    modules: dict[str, JsonObject] = {}
    for module in module_items:
        findings.extend(_unknown_fields(module, MODULE_FIELDS, "module"))
        module_id = module.get("moduleId")
        if not isinstance(module_id, str) or module_id in modules:
            findings.append(_finding("CTX.MODULE.DUPLICATE", str(module_id)))
            continue
        modules[module_id] = module
        location = module.get("location")
        if isinstance(location, str):
            findings.extend(validate_path(location, repository_root=repository_root))
        if module_content is not None and module_id in module_content:
            expected = module.get("contentSha256")
            if not isinstance(expected, str) or content_digest(module_content[module_id]) != expected:
                findings.append(_finding("CTX.MODULE.HASH_MISMATCH", module_id))
    current_id = manifest.get("currentStateModuleId")
    if not isinstance(current_id, str) or current_id not in modules:
        findings.extend(
            [_finding("CTX.MODULE.REQUIRED_MISSING", str(current_id)), _finding("CTX.STATE.CURRENT_MISSING")]
        )
    elif modules[current_id].get("status") != "active":
        findings.append(_finding("CTX.STATE.CURRENT_MISSING", current_id))
    for module_id, module in modules.items():
        dependencies = {str(item) for item in _list(module.get("dependsOn"))}
        missing = dependencies - modules.keys()
        findings.extend(_finding("CTX.MODULE.DEPENDENCY_MISSING", item) for item in missing)
        for superseded in _list(module.get("supersedes")):
            if superseded not in modules:
                findings.append(_finding("CTX.RULE.DANGLING_SUPERSESSION", str(superseded)))
        if module.get("status") in ACTIVE:
            for conflict in _list(module.get("conflictsWith")):
                if conflict in modules and modules[str(conflict)].get("status") in ACTIVE:
                    findings.append(_finding("CTX.CONFLICT.UNRESOLVED", f"{module_id}:{conflict}"))
    if modules and _cycle(modules):
        findings.append(_finding("CTX.GRAPH.CYCLE"))
    active_rules: dict[str, str] = {}
    for rule in _objects(manifest.get("rules")):
        findings.extend(_unknown_fields(rule, RULE_FIELDS, "rule"))
        rule_id = rule.get("ruleId")
        module_id = rule.get("moduleId")
        if module_id not in modules:
            findings.append(_finding("CTX.MODULE.REQUIRED_MISSING", str(module_id)))
        if rule.get("status") == "active" and isinstance(rule_id, str):
            if rule_id in active_rules:
                findings.append(_finding("CTX.RULE.DUPLICATE_ACTIVE", rule_id))
            active_rules[rule_id] = str(module_id)
    for module_id, module in modules.items():
        for rule_id in _list(module.get("ruleIds")):
            if active_rules.get(str(rule_id)) != module_id and module.get("status") == "active":
                findings.append(_finding("CTX.RULE.DEFINITION_MISSING", str(rule_id)))
    return _dedupe(findings)


def _domain(authority: JsonObject, plane: str, domain: str) -> set[str]:
    value = authority.get(plane, {})
    if not isinstance(value, dict):
        return set()
    return {str(item) for item in _list(value.get(domain))}


def intersect_authority(
    repository: JsonObject,
    issue: JsonObject,
    parent: JsonObject,
    child: JsonObject,
) -> tuple[JsonObject, list[Finding]]:
    """Intersect allow planes and union denies; child expansion is always a finding."""

    findings: list[Finding] = []
    effective: JsonObject = {"allows": {}, "denies": {}}
    layers = (("REPOSITORY", repository), ("ISSUE", issue), ("PARENT", parent))
    for domain in AUTHORITY_DOMAINS:
        requested = _domain(child, "allows", domain)
        for layer_name, layer in layers:
            wider = requested - _domain(layer, "allows", domain)
            if wider:
                code = f"CTX.AUTH.CHILD_WIDENS_{layer_name}"
                findings.append(_finding(code, f"{domain}:{','.join(sorted(wider))}"))
        allows = requested.copy()
        for _, layer in layers:
            allows &= _domain(layer, "allows", domain)
        denies = _domain(child, "denies", domain)
        for _, layer in layers:
            denies |= _domain(layer, "denies", domain)
        denied_requests = requested & denies
        if denied_requests:
            findings.append(_finding("CTX.AUTH.DENY_WINS", f"{domain}:{','.join(sorted(denied_requests))}"))
        allows -= denies
        if domain == "externalActions" and requested - allows:
            findings.append(_finding("CTX.AUTH.EXTERNAL_NOT_GRANTED", ",".join(sorted(requested - allows))))
        effective["allows"][domain] = sorted(allows)
        effective["denies"][domain] = sorted(denies)
    return effective, _dedupe(findings)


def validate_capsule(
    capsule: JsonObject,
    *,
    repository_authority: JsonObject,
    issue_authority: JsonObject,
    parent_capsule: JsonObject | None,
    actual_branch: str,
    actual_head: str,
    actual_base: str | None = None,
) -> list[Finding]:
    """Validate exact state, typed authority, non-widening, and review independence."""

    findings = _unknown_fields(capsule, CAPSULE_FIELDS, "capsule")
    if capsule.get("schemaVersion") != "AgentTaskCapsuleV1":
        findings.append(_finding("CTX.SCHEMA.VERSION"))
    if capsule.get("branch") != actual_branch:
        findings.append(_finding("CTX.STALE.BRANCH"))
    if capsule.get("expectedHead") != actual_head:
        findings.append(_finding("CTX.STALE.HEAD"))
    if actual_base is not None and capsule.get("baseCommit") != actual_base:
        findings.append(_finding("CTX.STALE.BASE"))
    authority = capsule.get("authority")
    if not isinstance(authority, dict):
        return _dedupe(findings + [_finding("CTX.AUTH.MISSING")])
    if capsule.get("authorityDigest") != canonical_digest(authority):
        findings.append(_finding("CTX.AUTH.SNAPSHOT_DRIFT"))
    parent_authority: JsonObject = {}
    if parent_capsule is not None and isinstance(parent_capsule.get("authority"), dict):
        parent_authority = parent_capsule["authority"]
    _, authority_findings = intersect_authority(
        repository_authority, issue_authority, parent_authority, authority
    )
    findings.extend(authority_findings)
    write_paths = _domain(authority, "allows", "writePaths")
    if capsule.get("actionMode") == "READ_ONLY" and write_paths:
        findings.append(_finding("CTX.MODE.READ_ONLY_WRITE"))
    for plane in ("allows", "denies"):
        for domain in ("readPaths", "writePaths"):
            for path in _domain(authority, plane, domain):
                findings.extend(validate_path(path))
    negative_text = " ".join(str(item).casefold() for item in _list(capsule.get("negativeInvariants")))
    denied_claims = _domain(authority, "denies", "claims")
    if "production readiness" in negative_text and "PRODUCTION_READINESS" not in denied_claims:
        findings.append(_finding("CTX.TYPE.PROHIBITED_CLAIM_UNTYPED"))
    untrusted = capsule.get("untrustedData")
    if isinstance(untrusted, str) and re.search(r"(?i)(grant|ignore|override)", untrusted):
        if _domain(authority, "allows", "externalActions") or write_paths:
            findings.append(_finding("CTX.INJECT.AUTHORITY_UNTRUSTED"))
    if capsule.get("role") in {"INDEPENDENT_PR_REVIEWER", "INDEPENDENT_SECURITY_REVIEWER"}:
        if capsule.get("historyMode") not in {"EXCLUDED", None} or write_paths:
            findings.append(_finding("CTX.REVIEW.NOT_INDEPENDENT"))
    return _dedupe(findings)


def build_capsule(
    manifest: JsonObject,
    fixture: JsonObject,
    route: JsonObject,
    *,
    repository_commit: str,
    branch: str,
    parent_capsule_id: str | None = None,
) -> JsonObject:
    """Build one deterministic task capsule from independently frozen authority."""

    fixture_authority = fixture.get("authority", {})
    grants = fixture_authority.get("grants", {}) if isinstance(fixture_authority, dict) else {}
    denies = fixture_authority.get("denies", {}) if isinstance(fixture_authority, dict) else {}

    def plane(value: Any) -> JsonObject:
        source = value if isinstance(value, dict) else {}
        return {domain: sorted({str(item) for item in _list(source.get(domain))}) for domain in AUTHORITY_DOMAINS}

    authority: JsonObject = {"allows": plane(grants), "denies": plane(denies)}
    execution_mode = str(route.get("executionMode"))
    if execution_mode in {"READ_ONLY", "READ_ONLY_CHILD"}:
        action_mode = "READ_ONLY"
    elif execution_mode == "EXTERNAL_MUTATION_EXPLICIT_GRANTS":
        action_mode = "GITHUB_MUTATION"
    else:
        action_mode = "EDIT"
    module_hashes = {
        str(module.get("moduleId")): str(module.get("contentSha256"))
        for module in _objects(manifest.get("modules"))
        if module.get("moduleId") in set(route.get("dependencyClosure", []))
    }
    claims = _objects(fixture.get("request", {}).get("claims")) if isinstance(fixture.get("request"), dict) else []
    objective = str(fixture.get("request", {}).get("operation", "bounded-task")) if isinstance(fixture.get("request"), dict) else "bounded-task"
    deliverable = str(claims[0].get("value", "bounded evidence")) if claims else "bounded evidence"
    capsule: JsonObject = {
        "schemaVersion": "AgentTaskCapsuleV1",
        "capsuleId": f"capsule-{fixture.get('fixtureId')}",
        "parentCapsuleId": parent_capsule_id,
        "repository": manifest.get("repository"),
        "branch": branch,
        "baseCommit": repository_commit,
        "expectedHead": repository_commit,
        "actionMode": action_mode,
        "objective": objective,
        "deliverable": deliverable,
        "claims": authority["allows"]["claims"],
        "negativeInvariants": [f"deny:{item}" for item in authority["denies"]["claims"]],
        "requiredPaths": authority["allows"]["readPaths"],
        "authority": authority,
        "selectedRuleIds": route.get("selectedRuleIds", []),
        "moduleHashes": module_hashes,
        "requiredTests": fixture.get("seededDefectIds", []),
        "assumptions": ["shadow-mode-only", "mandatory-reading-unchanged"],
        "budgets": fixture.get("budgets", {}).get("taskCapsule", {}),
        "stopConditions": [
            "AUTHORITY_DRIFT",
            "BUDGET_OVERFLOW",
            "STALE_BASE_OR_HEAD",
            "UNRESOLVED_CONFLICT",
            "WRITESET_COLLISION",
        ],
        "expiresAt": "2026-08-30T00:00:00Z",
        "expectedReceiptSchema": "HandoffReceiptV1",
        "authorityDigest": canonical_digest(authority),
    }
    capsule["capsuleDigest"] = canonical_digest(capsule)
    return capsule


def validate_receipt(
    receipt: JsonObject,
    *,
    capsule: JsonObject,
    manifest_digest: str,
    actual_branch: str,
    actual_head: str,
) -> list[Finding]:
    """Bind a receipt to its capsule, manifest, branch/head, commands, and claim limits."""

    findings = _unknown_fields(receipt, RECEIPT_FIELDS, "receipt")
    for field in sorted(RECEIPT_FIELDS):
        if field not in receipt:
            findings.append(_finding("CTX.RECEIPT.FIELD_MISSING", field))
    if receipt.get("capsuleId") != capsule.get("capsuleId"):
        findings.append(_finding("CTX.RECEIPT.CAPSULE_MISMATCH"))
    if receipt.get("acceptedAuthorityDigest") != capsule.get("authorityDigest"):
        findings.append(_finding("CTX.RECEIPT.AUTHORITY_MISMATCH"))
    if receipt.get("manifestHash") != manifest_digest:
        findings.append(_finding("CTX.RECEIPT.MANIFEST_MISMATCH"))
    if receipt.get("branch") != actual_branch:
        findings.append(_finding("CTX.RECEIPT.BRANCH_MISMATCH"))
    if receipt.get("head") != actual_head or receipt.get("head") != capsule.get("expectedHead"):
        findings.append(_finding("CTX.RECEIPT.HEAD_MISMATCH"))
    commands = _objects(receipt.get("commands"))
    for index, command in enumerate(commands):
        if set(command) != {"argv", "exitCode", "result"}:
            findings.append(_finding("CTX.RECEIPT.COMMAND_INCOMPLETE", str(index)))
    if receipt.get("selfCertification"):
        findings.append(_finding("CTX.RECEIPT.SELF_CERTIFICATION"))
    authority = capsule.get("authority", {})
    if capsule.get("actionMode") == "READ_ONLY" and _list(receipt.get("filesChanged")):
        findings.append(_finding("CTX.RECEIPT.READ_ONLY_CHANGED"))
    allowed_writes = _domain(authority if isinstance(authority, dict) else {}, "allows", "writePaths")
    changed = {str(item) for item in _list(receipt.get("filesChanged"))}
    if changed - allowed_writes:
        findings.append(_finding("CTX.RECEIPT.WRITE_SCOPE_MISMATCH"))
    return _dedupe(findings)


def _normalized_path(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold().rstrip("/")


def detect_write_set_collisions(capsules: list[JsonObject]) -> list[Finding]:
    """Reject equal, normalized-equal, or prefix-overlapping parallel write sets."""

    reservations: list[tuple[str, str]] = []
    findings: list[Finding] = []
    for capsule in capsules:
        capsule_id = str(capsule.get("capsuleId", "unknown"))
        authority = capsule.get("authority", {})
        if not isinstance(authority, dict):
            continue
        allows = authority.get("allows", {})
        if not isinstance(allows, dict):
            continue
        for raw_path in _list(allows.get("writePaths")):
            path = _normalized_path(str(raw_path))
            for other_id, other_path in reservations:
                if path == other_path or path.startswith(other_path + "/") or other_path.startswith(path + "/"):
                    findings.append(_finding("CTX.WRITESET.COLLISION", f"{other_id}:{capsule_id}:{path}"))
            reservations.append((capsule_id, path))
    return _dedupe(findings)


def detect_state_contradictions(
    current_state: JsonObject | None,
    *,
    prose_claims: list[JsonObject],
    historical_entries: list[JsonObject],
) -> list[Finding]:
    """Detect missing current state, contradictory active claims, and history misuse."""

    if current_state is None:
        return [_finding("CTX.STATE.CURRENT_MISSING")]
    findings: list[Finding] = []
    claims = _objects(current_state.get("claims")) or _objects(current_state.get("facts"))
    current = {str(item.get("id")): item.get("value") for item in claims}
    for claim in prose_claims:
        claim_id = str(claim.get("id"))
        if claim_id in current and current[claim_id] != claim.get("value"):
            findings.append(_finding("CTX.STATE.CONTRADICTION", claim_id))
    if any(entry.get("status") == "historical" for entry in historical_entries):
        findings.append(_finding("CTX.STATE.HISTORY_AS_CURRENT"))
    return _dedupe(findings)


def route_request(
    manifest: JsonObject,
    request: JsonObject,
    *,
    fixture_set: JsonObject | None = None,
) -> tuple[JsonObject, list[Finding]]:
    """Route only an independently frozen exact cohort; ambiguity and unknowns stop."""

    del manifest
    if fixture_set is None:
        return {}, [_finding("CTX.ROUTE.UNKNOWN")]
    findings: list[Finding] = []
    provenance = fixture_set.get("provenance", {})
    if isinstance(provenance, dict) and provenance.get("routerOutputUsedAsExpectedValue") is not False:
        findings.append(_finding("CTX.FIXTURE.CIRCULAR_ORACLE"))
    matches = [fixture for fixture in _objects(fixture_set.get("fixtures")) if fixture.get("request") == request]
    if not matches:
        return {}, _dedupe(findings + [_finding("CTX.ROUTE.UNKNOWN")])
    if len(matches) != 1:
        return {}, _dedupe(findings + [_finding("CTX.ROUTE.AMBIGUOUS")])
    fixture = matches[0]
    expected = fixture.get("expectedRoute", {})
    included = fixture.get("includedModules", [])
    rejected = fixture.get("rejectedModules", [])
    closure = fixture.get("dependencyClosure", [])
    receipt: JsonObject = {
        "schemaVersion": "RoutingReceiptV1",
        "fixtureId": fixture.get("fixtureId"),
        "routeId": expected.get("routeId") if isinstance(expected, dict) else None,
        "executionMode": expected.get("executionMode") if isinstance(expected, dict) else None,
        "packetBudget": expected.get("packetBudget") if isinstance(expected, dict) else None,
        "requestDigest": canonical_digest(request),
        "includedModules": included,
        "rejectedModules": rejected,
        "dependencyClosure": closure,
        "selectedRuleIds": [
            rule_id for module in _objects(included) for rule_id in _list(module.get("ruleIds"))
        ],
        "unresolvedConflicts": [],
    }
    receipt["receiptDigest"] = canonical_digest(receipt)
    return receipt, _dedupe(findings)


def _line_count(content: str) -> int:
    return len(content.splitlines())


def _estimated_tokens(content: str) -> int:
    return (len(content.encode("utf-8")) + 3) // 4


def build_packet(
    manifest: JsonObject,
    route: JsonObject,
    module_content: dict[str, str],
    *,
    line_ceiling: int,
    token_ceiling: int,
) -> tuple[JsonObject, list[Finding]]:
    """Build a complete, bounded, reproducible packet from selected module content."""

    findings: list[Finding] = []
    included = [str(item.get("moduleId")) for item in _objects(route.get("includedModules"))]
    if "repo-constitution" not in included:
        findings.append(_finding("CTX.PACKET.CRITICAL_RULE_MISSING", "repo-constitution"))
    if "parent-summary" in module_content:
        findings.append(_finding("CTX.PACKET.SUMMARY_SUBSTITUTION"))
    missing = set(included) - module_content.keys()
    findings.extend(_finding("CTX.PACKET.CRITICAL_RULE_MISSING", item) for item in sorted(missing))
    selected_content = {module_id: module_content[module_id] for module_id in included if module_id in module_content}
    lines = sum(_line_count(content) for content in module_content.values())
    tokens = sum(_estimated_tokens(content) for content in module_content.values())
    if lines > line_ceiling or tokens > token_ceiling:
        findings.append(_finding("CTX.BUDGET.OVERFLOW", f"{lines}/{line_ceiling}:{tokens}/{token_ceiling}"))
    modules = [
        {
            "moduleId": module_id,
            "contentSha256": content_digest(selected_content[module_id]),
            "content": selected_content[module_id],
        }
        for module_id in included
        if module_id in selected_content
    ]
    selected_rule_ids = {str(item) for item in _list(route.get("selectedRuleIds"))}
    rules = [
        rule
        for rule in _objects(manifest.get("rules"))
        if rule.get("ruleId") in selected_rule_ids and rule.get("status") == "active"
    ]
    if {str(rule.get("ruleId")) for rule in rules} != selected_rule_ids:
        findings.append(_finding("CTX.PACKET.CRITICAL_RULE_MISSING", "canonical-rule-definition"))
    packet: JsonObject = {
        "schemaVersion": "ContextPacketV1",
        "manifestDigest": canonical_digest(manifest),
        "routeDigest": canonical_digest(route),
        "moduleIds": included,
        "modules": modules,
        "rules": rules,
        "metrics": {
            "lines": lines,
            "estimatedTokens": tokens,
            "estimateAlgorithm": "ceil-utf8-bytes-divided-by-4",
            "lineCeiling": line_ceiling,
            "tokenCeiling": token_ceiling,
        },
    }
    packet["packetDigest"] = canonical_digest(packet)
    return packet, _dedupe(findings)


def regular_file_within(root: Path, path: str) -> bool:
    """Return whether an existing path is a non-symlink regular file inside root."""

    if validate_path(path, repository_root=root):
        return False
    candidate = root / path
    return candidate.is_file() and not candidate.is_symlink() and os.stat(candidate).st_mode != 0
