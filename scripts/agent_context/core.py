"""Deterministic, standard-library agent-context contracts for Issue #319."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
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
    "authorityProfiles",
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
    "fixtureId",
    "requestDigest",
    "routeDigest",
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
DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
FROZEN_FIXTURE_DIGEST = "aac018e816ea393daa6de560aed6a13834222219be0ec67b8a8b0a186d072d37"
RESERVED_RECEIPT_CLAIMS = {
    "APPROVAL", "COMPLETION", "MERGE_ELIGIBILITY", "RELEASE", "PRODUCTION_READINESS"
}


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


def load_json_bytes_strict(raw: bytes) -> JsonObject:
    """Load one UTF-8 object while rejecting duplicate keys and non-object roots."""

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> JsonObject:
        result: JsonObject = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def load_json_strict(path: Path) -> JsonObject:
    """Load one strict JSON object from a local path."""

    return load_json_bytes_strict(path.read_bytes())


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


def _required_fields(value: JsonObject, required: set[str], prefix: str) -> list[Finding]:
    return [_finding("CTX.SCHEMA.REQUIRED", f"{prefix}.{key}") for key in sorted(required - value.keys())]


def validate_schema_instance(value: Any, contract: JsonObject, definition: str) -> list[Finding]:
    """Validate the JSON-Schema subset used by the checked-in V1 contracts."""

    definitions = contract.get("$defs", {})
    schema = definitions.get(definition) if isinstance(definitions, dict) else None
    if not isinstance(schema, dict):
        return [_finding("CTX.SCHEMA.CONTRACT_MISSING", definition)]
    findings: list[Finding] = []

    def walk(instance: Any, rule: JsonObject, path: str) -> None:
        alternatives = rule.get("oneOf")
        if isinstance(alternatives, list):
            matches = 0
            for alternative in alternatives:
                if not isinstance(alternative, dict):
                    continue
                checkpoint = len(findings)
                walk(instance, alternative, path)
                if len(findings) == checkpoint:
                    matches += 1
                del findings[checkpoint:]
            if matches != 1:
                findings.append(_finding("CTX.SCHEMA.ONE_OF", path))
            return
        ref = rule.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            target = definitions.get(ref.removeprefix("#/$defs/"))
            if not isinstance(target, dict):
                findings.append(_finding("CTX.SCHEMA.CONTRACT_MISSING", ref))
                return
            walk(instance, target, path)
            return
        expected = rule.get("type")
        expected_types = expected if isinstance(expected, list) else [expected]
        checks = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        if expected is not None and not any(
            checks.get(str(kind), lambda _: False)(instance) for kind in expected_types
        ):
            findings.append(_finding("CTX.SCHEMA.TYPE", path))
            return
        if "const" in rule and instance != rule["const"]:
            findings.append(_finding("CTX.SCHEMA.CONST", path))
        if "enum" in rule and instance not in rule["enum"]:
            findings.append(_finding("CTX.SCHEMA.ENUM", path))
        minimum = rule.get("minimum")
        if isinstance(instance, (int, float)) and not isinstance(instance, bool) and isinstance(
            minimum, (int, float)
        ) and instance < minimum:
            findings.append(_finding("CTX.SCHEMA.MINIMUM", path))
        if isinstance(instance, dict):
            required = rule.get("required", [])
            for key in required if isinstance(required, list) else []:
                if key not in instance:
                    findings.append(_finding("CTX.SCHEMA.REQUIRED", f"{path}.{key}"))
            properties = rule.get("properties", {})
            properties = properties if isinstance(properties, dict) else {}
            additional = rule.get("additionalProperties", True)
            for key, item in instance.items():
                child_rule = properties.get(key)
                if isinstance(child_rule, dict):
                    walk(item, child_rule, f"{path}.{key}")
                elif additional is False:
                    findings.append(_finding("CTX.SCHEMA.UNKNOWN_FIELD", f"{path}.{key}"))
                elif isinstance(additional, dict):
                    walk(item, additional, f"{path}.{key}")
        if isinstance(instance, list):
            if len(instance) < int(rule.get("minItems", 0)):
                findings.append(_finding("CTX.SCHEMA.MIN_ITEMS", path))
            if "maxItems" in rule and len(instance) > int(rule["maxItems"]):
                findings.append(_finding("CTX.SCHEMA.MAX_ITEMS", path))
            if rule.get("uniqueItems") and len({canonical_json(item) for item in instance}) != len(instance):
                findings.append(_finding("CTX.SCHEMA.UNIQUE", path))
            items = rule.get("items")
            if isinstance(items, dict):
                for index, item in enumerate(instance):
                    walk(item, items, f"{path}[{index}]")
        if isinstance(instance, str):
            if len(instance) < int(rule.get("minLength", 0)):
                findings.append(_finding("CTX.SCHEMA.MIN_LENGTH", path))
            pattern = rule.get("pattern")
            if isinstance(pattern, str) and re.search(pattern, instance) is None:
                findings.append(_finding("CTX.SCHEMA.PATTERN", path))
            if rule.get("format") == "date-time":
                valid_date_time = DATE_TIME.match(instance) is not None
                if valid_date_time:
                    try:
                        valid_date_time = datetime.fromisoformat(
                            instance.replace("Z", "+00:00")
                        ).tzinfo is not None
                    except ValueError:
                        valid_date_time = False
                if not valid_date_time:
                    findings.append(_finding("CTX.SCHEMA.FORMAT", path))

    walk(value, schema, definition)
    return _dedupe(findings)


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
    if unicodedata.normalize("NFC", path) != path:
        findings.append(_finding("CTX.PATH.NONCANONICAL", path))
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
    findings.extend(_required_fields(manifest, MANIFEST_FIELDS, "manifest"))
    if manifest.get("schemaVersion") != "ContextPolicyManifestV1":
        findings.append(_finding("CTX.SCHEMA.VERSION"))
    module_items = _objects(manifest.get("modules"))
    modules: dict[str, JsonObject] = {}
    for module in module_items:
        findings.extend(_unknown_fields(module, MODULE_FIELDS, "module"))
        findings.extend(_required_fields(module, MODULE_FIELDS, "module"))
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
        findings.extend(_required_fields(rule, RULE_FIELDS, "rule"))
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
    items = {str(item) for item in _list(value.get(domain))}
    if domain in {"readPaths", "writePaths"}:
        return {_authority_path(item) for item in items}
    return items


def intersect_authority(
    repository: JsonObject,
    issue: JsonObject,
    parent: JsonObject | None,
    child: JsonObject,
) -> tuple[JsonObject, list[Finding]]:
    """Intersect allow planes and union denies; child expansion is always a finding."""

    findings: list[Finding] = []
    effective: JsonObject = {"allows": {}, "denies": {}}
    layers = [("REPOSITORY", repository), ("ISSUE", issue)]
    if parent is not None:
        layers.append(("PARENT", parent))
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
    repository_root: Path | None = None,
    contract_schema: JsonObject | None = None,
    expected_rule_ids: set[str] | None = None,
    expected_module_hashes: JsonObject | None = None,
    expected_fixture: JsonObject | None = None, expected_route: JsonObject | None = None, expected_repository: str | None = None,
) -> list[Finding]:
    """Validate exact state, typed authority, non-widening, and review independence."""

    findings = _unknown_fields(capsule, CAPSULE_FIELDS, "capsule")
    required = CAPSULE_FIELDS - {"untrustedData"}
    findings.extend(_required_fields(capsule, required, "capsule"))
    if contract_schema is not None:
        findings.extend(validate_schema_instance(capsule, contract_schema, "AgentTaskCapsuleV1"))
    if capsule.get("schemaVersion") != "AgentTaskCapsuleV1":
        findings.append(_finding("CTX.SCHEMA.VERSION"))
    if capsule.get("branch") != actual_branch:
        findings.append(_finding("CTX.STALE.BRANCH"))
    if capsule.get("expectedHead") != actual_head:
        findings.append(_finding("CTX.STALE.HEAD"))
    if actual_base is not None and capsule.get("baseCommit") != actual_base:
        findings.append(_finding("CTX.STALE.BASE"))
    if expected_repository is not None and capsule.get("repository") != expected_repository:
        findings.append(_finding("CTX.CAPSULE.REPOSITORY_MISMATCH"))
    authority = capsule.get("authority")
    if not isinstance(authority, dict):
        return _dedupe(findings + [_finding("CTX.AUTH.MISSING")])
    if capsule.get("authorityDigest") != canonical_digest(authority):
        findings.append(_finding("CTX.AUTH.SNAPSHOT_DRIFT"))
    digest_payload = {key: value for key, value in capsule.items() if key != "capsuleDigest"}
    if capsule.get("capsuleDigest") != canonical_digest(digest_payload):
        findings.append(_finding("CTX.CAPSULE.DIGEST_MISMATCH"))
    parent_authority = parent_capsule.get("authority") if parent_capsule is not None else None
    expected_parent = f"{parent_capsule.get('capsuleId')}@{parent_capsule.get('capsuleDigest')}" if parent_capsule else None
    if capsule.get("parentCapsuleId") != expected_parent:
        findings.append(_finding("CTX.CAPSULE.PARENT_BINDING_MISMATCH"))
    _, authority_findings = intersect_authority(repository_authority, issue_authority, parent_authority, authority)
    findings.extend(authority_findings)
    write_paths = _domain(authority, "allows", "writePaths")
    external_actions = _domain(authority, "allows", "externalActions")
    mode = capsule.get("actionMode")
    if mode == "READ_ONLY" and (write_paths or external_actions):
        findings.append(_finding("CTX.MODE.READ_ONLY_MUTATION"))
    elif mode == "EDIT" and not write_paths:
        findings.append(_finding("CTX.MODE.EDIT_WITHOUT_WRITE"))
    elif mode == "GITHUB_MUTATION" and not _domain(authority, "allows", "externalActions"):
        findings.append(_finding("CTX.MODE.GITHUB_WITHOUT_EXTERNAL"))
    for plane in ("allows", "denies"):
        for domain in ("readPaths", "writePaths"):
            for path in _domain(authority, plane, domain):
                findings.extend(validate_path(path, repository_root=repository_root))
    declared_claims = {str(item) for item in _list(capsule.get("claims"))}
    allowed_claims = _domain(authority, "allows", "claims")
    denied_claims = _domain(authority, "denies", "claims")
    if declared_claims - allowed_claims or declared_claims & denied_claims:
        findings.append(_finding("CTX.CAPSULE.CLAIM_SCOPE_MISMATCH"))
    required_paths = {_authority_path(str(item)) for item in _list(capsule.get("requiredPaths"))}
    if required_paths - _domain(authority, "allows", "readPaths"):
        findings.append(_finding("CTX.CAPSULE.REQUIRED_PATH_SCOPE_MISMATCH"))
    if expected_rule_ids is not None and {
        str(item) for item in _list(capsule.get("selectedRuleIds"))
    } != expected_rule_ids:
        findings.append(_finding("CTX.CAPSULE.RULE_SCOPE_MISMATCH"))
    if expected_module_hashes is not None and capsule.get("moduleHashes") != expected_module_hashes:
        findings.append(_finding("CTX.CAPSULE.MODULE_SCOPE_MISMATCH"))
    if (
        expected_rule_ids is None
        or expected_module_hashes is None
        or expected_fixture is None
        or expected_route is None
    ):
        findings.append(_finding("CTX.CAPSULE.ROUTE_BINDING_MISSING"))
    else:
        expected_binding = _task_binding(expected_fixture, expected_route)
        if any(capsule.get(field) != value for field, value in expected_binding.items()):
            findings.append(_finding("CTX.CAPSULE.TASK_SCOPE_MISMATCH"))
        expected_mode = "READ_ONLY" if expected_route.get("executionMode") in {"READ_ONLY", "READ_ONLY_CHILD"} else "GITHUB_MUTATION" if expected_route.get("executionMode") == "EXTERNAL_MUTATION_EXPLICIT_GRANTS" else "EDIT"
        if mode != expected_mode:
            findings.append(_finding("CTX.CAPSULE.TASK_SCOPE_MISMATCH"))
    if any(not _list(capsule.get(field)) for field in ("claims", "requiredPaths", "selectedRuleIds")) or not capsule.get(
        "moduleHashes"
    ):
        findings.append(_finding("CTX.CAPSULE.EMPTY_BINDING"))
    budget = capsule.get("budgets", {})
    if isinstance(budget, dict):
        expected_budget = expected_fixture.get("budgets", {}).get("taskCapsule", {}) if expected_fixture else {}
        if expected_budget and any(budget.get(key) != expected_budget.get(key) for key in ("lineCeiling", "tokenCeiling")):
            findings.append(_finding("CTX.BUDGET.CAPSULE_SCOPE_MISMATCH"))
        lines = budget.get("actualLines")
        tokens = budget.get("actualTokens")
        if not isinstance(lines, int) or not isinstance(tokens, int):
            findings.append(_finding("CTX.BUDGET.CAPSULE_MISSING"))
        elif lines > int(budget.get("lineCeiling", 0)) or tokens > int(budget.get("tokenCeiling", 0)):
            findings.append(_finding("CTX.BUDGET.CAPSULE_OVERFLOW"))
        measured_lines, measured_tokens = _capsule_metrics(capsule)
        if lines != measured_lines or tokens != measured_tokens:
            findings.append(_finding("CTX.BUDGET.CAPSULE_MISMATCH"))
    negative_text = str(capsule.get("negativeInvariants", "")).casefold()
    if "production readiness" in negative_text and "PRODUCTION_READINESS" not in denied_claims:
        findings.append(_finding("CTX.TYPE.PROHIBITED_CLAIM_UNTYPED"))
    untrusted = capsule.get("untrustedData")
    if isinstance(untrusted, str) and re.search(r"(?i)(grant|ignore|override)", untrusted):
        if _domain(authority, "allows", "externalActions") or write_paths:
            findings.append(_finding("CTX.INJECT.AUTHORITY_UNTRUSTED"))
    if capsule.get("role") in {"INDEPENDENT_PR_REVIEWER", "INDEPENDENT_SECURITY_REVIEWER"}:
        if capsule.get("historyMode") != "EXCLUDED" or write_paths:
            findings.append(_finding("CTX.REVIEW.NOT_INDEPENDENT"))
    return _dedupe(findings)


def _capsule_metrics(capsule: JsonObject) -> tuple[int, int]:
    rendered = json.dumps(capsule, ensure_ascii=False, indent=2, sort_keys=True)
    return _line_count(rendered), _estimated_tokens(rendered)


def _task_binding(fixture: JsonObject, route: JsonObject) -> JsonObject:
    request = fixture.get("request", {})
    request = request if isinstance(request, dict) else {}
    claims = _objects(request.get("claims"))
    posture = fixture.get("coldHistoryPosture", {})
    posture = posture if isinstance(posture, dict) else {}
    return {
        "capsuleId": f"capsule-{fixture.get('fixtureId')}",
        "fixtureId": fixture.get("fixtureId"),
        "requestDigest": canonical_digest(request),
        "routeDigest": canonical_digest(route),
        "objective": str(request.get("operation", "bounded-task")),
        "deliverable": str(claims[0].get("value", "bounded evidence")) if claims else "bounded evidence",
        "role": request.get("role"),
        "historyMode": posture.get("authorReasoning"),
    }


def build_capsule(
    manifest: JsonObject,
    fixture: JsonObject,
    route: JsonObject,
    *,
    repository_commit: str,
    base_commit: str,
    branch: str,
    parent_capsule_id: str | None = None,
    authority_override: JsonObject | None = None,
) -> JsonObject:
    """Build one deterministic task capsule from independently frozen authority."""

    fixture_authority = fixture.get("authority", {})
    grants = fixture_authority.get("grants", {}) if isinstance(fixture_authority, dict) else {}
    denies = fixture_authority.get("denies", {}) if isinstance(fixture_authority, dict) else {}

    def plane(value: Any) -> JsonObject:
        source = value if isinstance(value, dict) else {}
        return {domain: sorted({str(item) for item in _list(source.get(domain))}) for domain in AUTHORITY_DOMAINS}

    proposed_authority: JsonObject = {"allows": plane(grants), "denies": plane(denies)}
    authority = authority_override if authority_override is not None else proposed_authority
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
    task_binding = _task_binding(fixture, route)
    capsule: JsonObject = {
        "schemaVersion": "AgentTaskCapsuleV1",
        "parentCapsuleId": parent_capsule_id,
        "repository": manifest.get("repository"),
        "branch": branch,
        "baseCommit": base_commit,
        "expectedHead": repository_commit,
        **task_binding,
        "actionMode": action_mode,
        "claims": authority["allows"]["claims"],
        "negativeInvariants": "All typed authority denies remain binding.",
        "requiredPaths": fixture.get("requiredPaths", authority["allows"]["readPaths"]),
        "authority": authority,
        "selectedRuleIds": route.get("selectedRuleIds", []),
        "moduleHashes": module_hashes,
        "requiredTests": f"fixture:{fixture.get('fixtureId')}.seededDefectIds",
        "assumptions": None,
        "budgets": dict(fixture.get("budgets", {}).get("taskCapsule", {})),
        "stopConditions": ["AUTHORITY_SCOPE_BUDGET_STATE_CONFLICT_OR_COLLISION"],
        "expiresAt": "2026-08-30T00:00:00Z",
        "expectedReceiptSchema": "HandoffReceiptV1",
        "authorityDigest": canonical_digest(authority),
    }
    capsule["budgets"].update({"actualLines": 0, "actualTokens": 0,
                               "estimateAlgorithm": "ceil-utf8-bytes-divided-by-4"})
    for _ in range(4):
        capsule["capsuleDigest"] = canonical_digest({key: value for key, value in capsule.items() if key != "capsuleDigest"})
        measured_lines, measured_tokens = _capsule_metrics(capsule)
        if (measured_lines, measured_tokens) == (capsule["budgets"]["actualLines"], capsule["budgets"]["actualTokens"]):
            break
        capsule["budgets"].update({"actualLines": measured_lines, "actualTokens": measured_tokens})
    capsule["capsuleDigest"] = canonical_digest({key: value for key, value in capsule.items() if key != "capsuleDigest"})
    return capsule


def validate_receipt(
    receipt: JsonObject,
    *,
    capsule: JsonObject,
    manifest_digest: str,
    actual_branch: str,
    actual_head: str,
    contract_schema: JsonObject | None = None,
) -> list[Finding]:
    """Bind a receipt to its capsule, manifest, branch/head, commands, and claim limits."""

    findings = _unknown_fields(receipt, RECEIPT_FIELDS, "receipt")
    if contract_schema is not None:
        findings.extend(validate_schema_instance(receipt, contract_schema, "HandoffReceiptV1"))
    else:
        findings.append(_finding("CTX.SCHEMA.CONTRACT_MISSING", "HandoffReceiptV1"))
    if receipt.get("schemaVersion") != "HandoffReceiptV1":
        findings.append(_finding("CTX.SCHEMA.VERSION"))
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
    if not commands:
        findings.append(_finding("CTX.RECEIPT.COMMAND_MISSING"))
    for index, command in enumerate(commands):
        if set(command) != {"argv", "exitCode", "result"}:
            findings.append(_finding("CTX.RECEIPT.COMMAND_INCOMPLETE", str(index)))
        elif (command.get("result") == "PASS") != (command.get("exitCode") == 0):
            findings.append(_finding("CTX.RECEIPT.COMMAND_RESULT_MISMATCH", str(index)))
    self_certification = receipt.get("selfCertification")
    if not isinstance(self_certification, list) or self_certification:
        findings.append(_finding("CTX.RECEIPT.SELF_CERTIFICATION"))
    proved_text = re.sub(r"[^A-Z0-9]+", "_", canonical_json(_list(receipt.get("claimsProved"))).upper())
    reserved_proved = {
        claim for claim in RESERVED_RECEIPT_CLAIMS if claim in proved_text
    }
    if reserved_proved:
        findings.append(_finding("CTX.RECEIPT.RESERVED_CLAIM", ",".join(sorted(reserved_proved))))
    claim_sets = [
        {str(item) for item in _list(receipt.get(field)) if isinstance(item, str)}
        for field in ("claimsProved", "claimsDisproved", "claimsNotTested")
    ]
    proved_claims = set().union(*claim_sets)
    authority = capsule.get("authority", {})
    allowed_claims = _domain(authority if isinstance(authority, dict) else {}, "allows", "claims")
    denied_claims = _domain(authority if isinstance(authority, dict) else {}, "denies", "claims")
    if proved_claims - allowed_claims or proved_claims & denied_claims:
        findings.append(_finding("CTX.RECEIPT.CLAIM_SCOPE_MISMATCH"))
    if any(claim_sets[left] & claim_sets[right] for left, right in ((0, 1), (0, 2), (1, 2))):
        findings.append(_finding("CTX.RECEIPT.CLAIM_CLASSIFICATION_CONFLICT"))
    budget = receipt.get("budget", {})
    capsule_budget = capsule.get("budgets", {})
    if isinstance(budget, dict) and isinstance(capsule_budget, dict):
        actual_lines = budget.get("actualLines")
        actual_tokens = budget.get("actualTokens")
        values = [budget.get(key) for key in ("estimatedLines", "actualLines", "estimatedTokens", "actualTokens")]
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            findings.append(_finding("CTX.BUDGET.RECEIPT_INVALID"))
        elif isinstance(actual_lines, int) and isinstance(actual_tokens, int) and (
            actual_lines > int(capsule_budget.get("lineCeiling", 0)) or actual_tokens > int(
            capsule_budget.get("tokenCeiling", 0)
            )
        ):
            findings.append(_finding("CTX.BUDGET.RECEIPT_OVERFLOW"))
    if capsule.get("actionMode") == "READ_ONLY" and _list(receipt.get("filesChanged")):
        findings.append(_finding("CTX.RECEIPT.READ_ONLY_CHANGED"))
    allowed_writes = _domain(authority if isinstance(authority, dict) else {}, "allows", "writePaths")
    changed = {_authority_path(str(item)) for item in _list(receipt.get("filesChanged"))}
    if changed - allowed_writes:
        findings.append(_finding("CTX.RECEIPT.WRITE_SCOPE_MISMATCH"))
    allowed_reads = _domain(authority if isinstance(authority, dict) else {}, "allows", "readPaths")
    inspected = {
        _authority_path(str(item))
        for field in ("filesInspected", "additionalSources")
        for item in _list(receipt.get(field))
    }
    if inspected - allowed_reads:
        findings.append(_finding("CTX.RECEIPT.READ_SCOPE_MISMATCH"))
    required = {_authority_path(str(item)) for item in _list(capsule.get("requiredPaths"))}
    if required - inspected:
        findings.append(_finding("CTX.RECEIPT.REQUIRED_EVIDENCE_MISSING"))
    if {str(item) for item in _list(receipt.get("validatedRules"))} != {
        str(item) for item in _list(capsule.get("selectedRuleIds"))
    }:
        findings.append(_finding("CTX.RECEIPT.RULE_MISMATCH"))
    if receipt.get("moduleHashes") != capsule.get("moduleHashes"):
        findings.append(_finding("CTX.RECEIPT.MODULE_MISMATCH"))
    return _dedupe(findings)


def _normalized_path(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold().rstrip("/")


def _authority_path(path: str) -> str:
    return unicodedata.normalize("NFC", path)


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
    current: dict[str, Any] = {}
    for item in claims:
        claim_id = str(item.get("id"))
        if claim_id in current:
            findings.append(_finding("CTX.STATE.DUPLICATE_FACT", claim_id))
        current[claim_id] = item.get("value")
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

    if fixture_set is None:
        return {}, [_finding("CTX.ROUTE.UNKNOWN")]
    findings: list[Finding] = []
    if canonical_digest(fixture_set) != FROZEN_FIXTURE_DIGEST:
        findings.append(_finding("CTX.FIXTURE.DRIFT"))
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
    modules = {str(item.get("moduleId")): item for item in _objects(manifest.get("modules"))}
    included_ids = [str(item.get("moduleId")) for item in _objects(included)]
    closure_ids = set(included_ids)
    pending = list(included_ids)
    while pending:
        module_id = pending.pop()
        module = modules.get(module_id)
        if module is None:
            findings.append(_finding("CTX.MODULE.REQUIRED_MISSING", module_id))
            continue
        for dependency in _list(module.get("dependsOn")):
            dependency_id = str(dependency)
            if dependency_id not in closure_ids:
                closure_ids.add(dependency_id)
                pending.append(dependency_id)
    closure = [module_id for module_id in modules if module_id in closure_ids]
    if closure != fixture.get("dependencyClosure"):
        findings.append(_finding("CTX.ROUTE.CLOSURE_MISMATCH"))
    if str(expected.get("packetBudget")) not in manifest.get("budgets", {}):
        findings.append(_finding("CTX.BUDGET.UNKNOWN"))
    active_rules = {
        str(rule.get("ruleId")): str(rule.get("moduleId"))
        for rule in _objects(manifest.get("rules")) if rule.get("status") == "active"
    }
    selected_rule_ids = [rule_id for module in _objects(included) for rule_id in _list(module.get("ruleIds"))]
    for rule_id in selected_rule_ids:
        if active_rules.get(str(rule_id)) not in closure_ids:
            findings.append(_finding("CTX.ROUTE.RULE_MODULE_MISMATCH", str(rule_id)))
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
        "selectedRuleIds": selected_rule_ids,
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
    if any(str(rule.get("moduleId")) not in included for rule in rules):
        findings.append(_finding("CTX.PACKET.RULE_MODULE_MISSING"))
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
