#!/usr/bin/env python3
"""Offline, deterministic checks for Issue #521 Master Program V2 candidate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast


DOCUMENT_PATH = "docs/governance/NARRATWIN_MASTER_PROGRAM_V2.md"
BINDING_PATH = "docs/governance/narratwin-master-program-v2.json"
MAPPING_PATH = "docs/governance/superset-mapping-v2.json"
TAXONOMY_PATH = "docs/governance/cut-taxonomy-v2.json"
MAPPING_SCHEMA_PATH = "docs/governance/schemas/superset-mapping-v2.schema.json"
TAXONOMY_SCHEMA_PATH = "docs/governance/schemas/cut-taxonomy-v2.schema.json"
REVIEW_PATHS = (
    "docs/reviews/ISSUE_521_SUPERSET_SEMANTIC_REVIEW.md",
    "docs/reviews/ISSUE_521_FALSE_SUCCESS_SECURITY_REVIEW.md",
)
REQUIRED_ARTIFACTS = (
    DOCUMENT_PATH,
    BINDING_PATH,
    MAPPING_PATH,
    TAXONOMY_PATH,
    MAPPING_SCHEMA_PATH,
    TAXONOMY_SCHEMA_PATH,
    *REVIEW_PATHS,
)
BASE_SHA = "b6b0c05c7227428ff0841361f3970b0b2c40aa86"
V1_PATH = "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
V1_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
DOCUMENT_SHA256 = "0e1e7ab79503764c99ad5c9bf0185dbf518f1a02f70fbbcfb9d45500a4a1cdcc"
MAPPING_SHA256 = "9c5490da888f2011373e04524b9e12f0c03912502d254360d85533b97cb9e8cd"
TAXONOMY_SHA256 = "860940f84420f925969d79902a4ee68d9844b62113dd9cf6293be347a1b61ce1"
ROADMAP_PATH = "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md"
ROADMAP_SHA256 = "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b"
ADR0079_PATH = "docs/ADR/0079-cut1-t06-dual-plan-video-strategy.md"
ADR0079_SHA256 = "a20ae1b9fae9e12e9e50baa372b0672c43a9417a21b36a2dc4276f5be1529fd5"

_SOURCE_SPECS = (
    ("OWNER_PLAN_2026_09_07", "OWNER_DIRECTIVE", DOCUMENT_PATH, "MARKDOWN_ATOMIC_V1", "## 1. Certification status and authority"),
    ("MASTER_PROGRAM_V1", "REPOSITORY_FILE", V1_PATH, "MARKDOWN_ATOMIC_V1", "## 1. Certification status and authority"),
    ("FIVE_CUT_ROADMAP", "REPOSITORY_FILE", ROADMAP_PATH, "MARKDOWN_ATOMIC_V1", "## 5. Six-cut product roadmap"),
    ("CUT1_PRESENTER_CONTRACT", "REPOSITORY_FILE", "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md", "MARKDOWN_ATOMIC_V1", "### Cut 1 — Fictional English prepared walkthrough"),
    ("AI_QUALITY_CONTRACT", "REPOSITORY_FILE", "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md", "MARKDOWN_ATOMIC_V1", "## 11. Test and acceptance plan"),
    ("ENTERPRISE_REGISTER", "REPOSITORY_FILE", "docs/ENTERPRISE_READINESS_REGISTER.md", "MARKDOWN_ATOMIC_V1", "### Cut 6 — Enterprise and commercial readiness"),
    ("SECURITY_PRIVACY", "REPOSITORY_FILE", "docs/SECURITY_AND_PRIVACY.md", "MARKDOWN_ATOMIC_V1", "## 11. Test and acceptance plan"),
    ("ARCHITECTURE", "REPOSITORY_FILE", "docs/ARCHITECTURE.md", "MARKDOWN_ATOMIC_V1", "## 7. Architecture and provider strategy"),
    ("STATUS", "REPOSITORY_FILE", "docs/STATUS.md", "MARKDOWN_ATOMIC_V1", "## 4. Canonical current inputs, evidence, and gaps"),
    ("PHASE_PLAN", "REPOSITORY_FILE", "docs/PHASE_PLAN.md", "MARKDOWN_ATOMIC_V1", "## 10. Implementation sequence"),
    ("STAGE_ISSUE_PLAN", "REPOSITORY_FILE", "docs/STAGE_ISSUE_PLAN.md", "MARKDOWN_ATOMIC_V1", "## 10. Implementation sequence"),
    ("CUT1_ACCEPTANCE", "REPOSITORY_FILE", "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md", "MARKDOWN_ATOMIC_V1", "## 11. Test and acceptance plan"),
    ("ADR_0079", "REPOSITORY_FILE", ADR0079_PATH, "MARKDOWN_ATOMIC_V1", "### Cut 4 — Rich motion, real scenes, and provider portability"),
    ("PRD", "REPOSITORY_FILE", "docs/PRD.md", "MARKDOWN_ATOMIC_V1", "## 2. Product definition and complete taxonomy"),
    ("API_CONTRACT", "REPOSITORY_FILE", "docs/API_CONTRACT.md", "MARKDOWN_ATOMIC_V1", "## 9. Public contracts and internal interfaces"),
    ("OBSERVABILITY_COST", "REPOSITORY_FILE", "docs/OBSERVABILITY_AND_COST.md", "MARKDOWN_ATOMIC_V1", "## 8. Cost model and spend governance"),
    ("PORTABILITY", "REPOSITORY_FILE", "docs/PORTABILITY_STRATEGY.md", "MARKDOWN_ATOMIC_V1", "## 7. Architecture and provider strategy"),
    ("AVATAR_PROVIDER_CODE", "REPOSITORY_FILE", "backend/app/avatar_video_provider.py", "PYTHON_CONTRACT_V1", "## 9. Public contracts and internal interfaces"),
    ("TTS_PROVIDER_CODE", "REPOSITORY_FILE", "backend/app/tts_provider.py", "PYTHON_CONTRACT_V1", "## 9. Public contracts and internal interfaces"),
)

_V1_DESTINATIONS = {
    **{number: "## 1. Certification status and authority" for number in (1, 2, 3, 4, 5, 6)},
    7: "## 4. Canonical current inputs, evidence, and gaps",
    8: "## 7. Architecture and provider strategy",
    9: "## 9. Public contracts and internal interfaces",
    10: "## 7. Architecture and provider strategy",
    11: "## 9. Public contracts and internal interfaces",
    12: "## 9. Public contracts and internal interfaces",
    13: "## 7. Architecture and provider strategy",
    14: "## 7. Architecture and provider strategy",
    15: "## 2. Product definition and complete taxonomy",
    16: "## 7. Architecture and provider strategy",
    17: "## 9. Public contracts and internal interfaces",
    18: "## 11. Test and acceptance plan",
    19: "## 11. Test and acceptance plan",
    **{number: "### Cut 1 — Fictional English prepared walkthrough" for number in range(20, 36)},
    **{number: "## 10. Implementation sequence" for number in range(36, 41)},
    41: "## 12. Stop conditions, assumptions, and completion claim",
    42: "## 1. Certification status and authority",
}

_ROW_FIELDS = {
    "requirementId", "sourceAtomId", "sourceId", "sourceKind", "sourcePath",
    "sourceAuthorityRefs", "sourceCommit", "sourceGitBlob", "sourceContentSha256",
    "sourceAnchor", "sourceClauseSha256", "normalizedAtomicRequirement",
    "v2DestinationClause", "disposition", "replacementId", "ownerAuthorityRef",
    "thresholdComparison", "rationale", "accountableOwner", "reviewer",
    "reviewTime", "result",
}
_DISPOSITIONS = {
    "PRESERVED", "STRENGTHENED", "RELOCATED",
    "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
}
_THRESHOLD_RELATIONS = {"EQUAL_OR_STRONGER", "OWNER_AUTHORIZED_CHANGE"}
_PRIVATE_PATTERNS = (
    re.compile(r"/Users/", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"https?://[^\s]+(?:token|signature|credential|key)=", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class DuplicateJsonMember(ValueError):
    pass


@dataclass(frozen=True)
class Atom:
    source_id: str
    anchor: str
    text: str

    @property
    def clause_sha256(self) -> str:
        return _sha256(self.text.encode("utf-8"))

    @property
    def atom_id(self) -> str:
        material = f"{self.source_id}\0{self.anchor}\0{self.text}".encode("utf-8")
        return "atom:" + _sha256(material)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _normalize(lines: Iterable[str]) -> str:
    return " ".join(part for line in lines if (part := " ".join(line.strip().split())))


def _markdown_atoms(source_id: str, text: str) -> list[Atom]:
    lines = text.splitlines()
    atoms: list[Atom] = []
    heading = "# document"
    block: list[str] = []
    block_start = 1
    in_fence = False
    table_header_pending = False

    def flush() -> None:
        nonlocal block
        normalized = _normalize(block)
        if normalized:
            atoms.append(Atom(source_id, f"{heading}::L{block_start}", normalized))
        block = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                flush()
                block_start = index
                block = [line]
                in_fence = True
            else:
                block.append(line)
                flush()
                in_fence = False
            continue
        if in_fence:
            block.append(line)
            continue
        if re.match(r"^#{1,6}\s+\S", stripped):
            flush()
            heading = stripped
            table_header_pending = False
            continue
        if not stripped:
            flush()
            table_header_pending = False
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush()
            if re.fullmatch(r"\|?[\s:|-]+\|?", stripped):
                table_header_pending = False
                continue
            if not table_header_pending:
                table_header_pending = True
                continue
            atoms.append(Atom(source_id, f"{heading}::L{index}", _normalize([line])))
            continue
        table_header_pending = False
        if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", stripped):
            flush()
            atoms.append(Atom(source_id, f"{heading}::L{index}", _normalize([line])))
            continue
        if not block:
            block_start = index
        block.append(line)
    flush()
    return atoms


def _python_atoms(source_id: str, text: str) -> list[Atom]:
    tree = ast.parse(text)
    lines = text.splitlines()
    atoms: list[Atom] = []
    interesting: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Raise)):
            interesting.add(node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"enabled", "timeout_seconds", "retry_attempts", "max_attempts"}:
                interesting.add(node.lineno)
        elif isinstance(node, ast.If):
            segment = ast.get_source_segment(text, node.test) or ""
            if "enabled" in segment or "credential" in segment or "retry" in segment:
                interesting.add(node.lineno)
    for line_number in sorted(interesting):
        value = lines[line_number - 1].strip()
        if value:
            atoms.append(Atom(source_id, f"python:L{line_number}", _normalize([value])))
    return atoms


def _atoms(source_id: str, atomizer: str, data: bytes) -> list[Atom]:
    text = data.decode("utf-8")
    if atomizer == "MARKDOWN_ATOMIC_V1":
        return _markdown_atoms(source_id, text)
    if atomizer == "PYTHON_CONTRACT_V1":
        return _python_atoms(source_id, text)
    raise ValueError(f"unknown atomizer: {atomizer}")


def frozen_source_bytes(root: Path, source: dict[str, Any]) -> bytes:
    """Read repository sources at their frozen commit; fixture roots fall back to files."""
    commit = source.get("sourceCommit")
    relative = source["repositoryPath"]
    if source.get("sourceKind") == "REPOSITORY_FILE" and isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit):
        result = subprocess.run(
            ["/usr/bin/git", "show", f"{commit}:{relative}"],
            cwd=root,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_NO_LAZY_FETCH": "1"},
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if result.returncode == 0:
            return bytes(result.stdout)
    return cast(bytes, (root / relative).read_bytes())


def _issue_refs(text: str, source_path: str) -> list[str]:
    comments = {
        f"github-comment:{match}"
        for match in re.findall(r"issuecomment-(\d+)", text)
    }
    issues = {f"github-issue:{match}" for match in re.findall(r"(?<![A-Za-z0-9])#(\d+)", text)}
    refs = sorted(comments | issues)
    return refs or [f"repository:{source_path}@{BASE_SHA}"]


def _destination(source_id: str, heading: str, text: str, default: str) -> str:
    if source_id == "OWNER_PLAN_2026_09_07":
        return heading if heading.startswith("##") else default
    if source_id == "MASTER_PROGRAM_V1":
        match = re.match(r"## (\d+)\.", heading)
        if match:
            return _V1_DESTINATIONS[int(match.group(1))]
    if source_id == "FIVE_CUT_ROADMAP" and "Cut 5" in text:
        return "### Cut 6 — Enterprise and commercial readiness"
    if source_id in {"SECURITY_PRIVACY", "PRD"} and re.search(
        r"clone|likeness|voice|biometric|consent", text, re.IGNORECASE
    ):
        return "### Cut 5 — Owner personal Digital Twin"
    return default


def _disposition(source_id: str, text: str) -> tuple[str, str | None, str | None]:
    if source_id == "OWNER_PLAN_2026_09_07":
        return "PRESERVED", None, None
    if source_id == "FIVE_CUT_ROADMAP" and "Cut 5" in text:
        return "RELOCATED", "MPV2-CUT6", "OWNER_PLAN_2026-09-07"
    explicit_change = (
        "selected presenter Meera only",
        "90.000–120.000 seconds",
        "US$100 total audition ceiling",
        "no voluntary spoken, burned-in, or adjacent visible AI-use statement",
    )
    if source_id == "MASTER_PROGRAM_V1" and any(value in text for value in explicit_change):
        return (
            "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
            "MPV2-OWNER-CHANGE-2026-09-07",
            "OWNER_PLAN_2026-09-07",
        )
    return "STRENGTHENED", None, None


def _source_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source_id, kind, relative, atomizer, default in _SOURCE_SPECS:
        commit = "OWNER_DIRECTIVE_2026-09-07" if kind == "OWNER_DIRECTIVE" else BASE_SHA
        data = frozen_source_bytes(
            root,
            {"sourceKind": kind, "sourceCommit": commit, "repositoryPath": relative},
        )
        atoms = _atoms(source_id, atomizer, data)
        refs = ["owner-directive:OWNER_PLAN_2026-09-07"] if kind == "OWNER_DIRECTIVE" else _issue_refs(data.decode("utf-8"), relative)
        records.append(
            {
                "sourceId": source_id,
                "sourceKind": kind,
                "repositoryPath": relative,
                "sourceCommit": commit,
                "sourceGitBlob": _git_blob(data),
                "contentSha256": _sha256(data),
                "atomizer": atomizer,
                "atomicRequirementCount": len(atoms),
                "authorityRefs": refs,
                "defaultV2Destination": default,
            }
        )
    return records


def generate_mapping(root: Path) -> dict[str, Any]:
    sources = _source_records(root)
    rows: list[dict[str, Any]] = []
    for source in sources:
        data = frozen_source_bytes(root, source)
        for atom in _atoms(source["sourceId"], source["atomizer"], data):
            disposition, replacement, owner_ref = _disposition(source["sourceId"], atom.text)
            destination = _destination(
                source["sourceId"], atom.anchor.split("::", 1)[0], atom.text,
                source["defaultV2Destination"],
            )
            rows.append(
                {
                    "requirementId": "MPV2-" + atom.atom_id.removeprefix("atom:")[:20].upper(),
                    "sourceAtomId": atom.atom_id,
                    "sourceId": source["sourceId"],
                    "sourceKind": source["sourceKind"],
                    "sourcePath": source["repositoryPath"],
                    "sourceAuthorityRefs": _issue_refs(atom.text, source["repositoryPath"])
                    if source["sourceKind"] == "REPOSITORY_FILE"
                    else ["owner-directive:OWNER_PLAN_2026-09-07"],
                    "sourceCommit": source["sourceCommit"],
                    "sourceGitBlob": source["sourceGitBlob"],
                    "sourceContentSha256": source["contentSha256"],
                    "sourceAnchor": atom.anchor,
                    "sourceClauseSha256": atom.clause_sha256,
                    "normalizedAtomicRequirement": atom.text,
                    "v2DestinationClause": destination,
                    "disposition": disposition,
                    "replacementId": replacement,
                    "ownerAuthorityRef": owner_ref,
                    "thresholdComparison": {
                        "relation": "OWNER_AUTHORIZED_CHANGE"
                        if disposition == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"
                        else "EQUAL_OR_STRONGER",
                        "basis": "Explicit owner change is isolated and review-gated."
                        if disposition == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"
                        else "The destination preserves this source obligation and adds prototype, evidence, or acceptance controls.",
                    },
                    "rationale": "Canonical V2 preservation row generated from frozen source bytes; semantic disposition remains independently reviewable.",
                    "accountableOwner": "REPOSITORY_OWNER",
                    "reviewer": "INDEPENDENT_REVIEWER_PENDING",
                    "reviewTime": None,
                    "result": "PENDING",
                }
            )
    rows.sort(key=lambda item: (item["sourceId"], item["sourceAnchor"], item["sourceAtomId"]))
    return {
        "schemaVersion": "SupersetMappingV2",
        "mappingId": "narratwin-master-program-v2-superset",
        "proposalState": "PROPOSED",
        "cutoff": "2026-09-06T23:59:59+05:30",
        "ownerAuthority": "OWNER_PLAN_2026-09-07",
        "sources": sources,
        "rows": rows,
        "certification": {
            "structuralResult": "PASS",
            "semanticReview": "PENDING_INDEPENDENT_REVIEW",
            "ownerExactBytesApproval": "PENDING",
            "eligibleNonAuthorExactHead": "PENDING",
            "activation": "NONE",
        },
    }


def render_mapping(mapping: dict[str, Any]) -> str:
    def compact(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    lines = ["{", '  "schemaVersion":"SupersetMappingV2",', '  "mappingId":"narratwin-master-program-v2-superset",', '  "proposalState":"PROPOSED",', '  "cutoff":"2026-09-06T23:59:59+05:30",', '  "ownerAuthority":"OWNER_PLAN_2026-09-07",', '  "sources":[']
    for index, source in enumerate(mapping["sources"]):
        lines.append("    " + compact(source) + ("," if index + 1 < len(mapping["sources"]) else ""))
    lines.append("  ],")
    lines.append('  "rows":[')
    for index, row in enumerate(mapping["rows"]):
        lines.append("    " + compact(row) + ("," if index + 1 < len(mapping["rows"]) else ""))
    lines.extend(["  ],", '  "certification":' + compact(mapping["certification"]), "}"])
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonMember(key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def expected_source_records(root: Path) -> dict[str, dict[str, Any]]:
    return {source["sourceId"]: source for source in _source_records(root)}


def expected_source_atoms(root: Path, mapping: dict[str, Any] | None = None) -> dict[str, Atom]:
    del mapping
    result: dict[str, Atom] = {}
    for source in expected_source_records(root).values():
        data = frozen_source_bytes(root, source)
        for atom in _atoms(source["sourceId"], source["atomizer"], data):
            result[atom.atom_id] = atom
    return result


def _taxonomy_failures(value: Any) -> list[str]:
    if not isinstance(value, dict) or value.get("schemaVersion") != "CutTaxonomyV2":
        return ["MPV2.TAXONOMY.SCHEMA_INVALID"]
    failures: list[str] = []
    collections = ("engineeringStages", "productModes", "cuts", "laneA", "historicalCheckpoints", "adrPlans", "digitalTwinSequence")
    ids: list[str] = []
    for name in collections:
        items = value.get(name)
        if not isinstance(items, list):
            failures.append("MPV2.TAXONOMY.SCHEMA_INVALID")
            continue
        local = [item.get("id") for item in items if isinstance(item, dict)]
        if len(local) != len(set(local)):
            failures.append("MPV2.TAXONOMY.DUPLICATE_ID")
        ids.extend(item for item in local if isinstance(item, str))
    if len(ids) != len(set(ids)):
        failures.append("MPV2.TAXONOMY.DUPLICATE_ID")
    cuts = {item.get("id"): item for item in value.get("cuts", []) if isinstance(item, dict)}
    if cuts.get("Cut5", {}).get("name") != "Owner personal Digital Twin" or cuts.get("Cut6", {}).get("name") != "Enterprise and commercial readiness":
        failures.append("MPV2.TAXONOMY.CUT_MEANING_INVALID")
    aliases = value.get("legacyAliases", [])
    alias = aliases[0] if len(aliases) == 1 and isinstance(aliases[0], dict) else {}
    if alias.get("alias") != "LegacyCut5Enterprise" or alias.get("canonicalCut") != "Cut6":
        failures.append("MPV2.TAXONOMY.LEGACY_CUT5_TARGET_INVALID")
    if alias.get("canSatisfyNewCut5") is not False:
        failures.append("MPV2.TAXONOMY.LEGACY_EVIDENCE_CROSSED")
    if alias.get("cut6MigrationValidationRequired") is not True:
        failures.append("MPV2.TAXONOMY.CUT6_MIGRATION_BYPASSED")
    if [item.get("id") for item in value.get("digitalTwinSequence", [])] != [f"DT{i}" for i in range(8)]:
        failures.append("MPV2.TAXONOMY.DT_SEQUENCE_INCOMPLETE")
    checkpoints = {item.get("id"): item.get("v2Destinations") for item in value.get("historicalCheckpoints", []) if isinstance(item, dict)}
    for checkpoint in ("Checkpoint2", "Checkpoint3B", "Checkpoint3C"):
        if checkpoints.get(checkpoint) != ["Cut5"]:
            failures.append("MPV2.TAXONOMY.CHECKPOINT_MIGRATION_INVALID")
            break
    activation = value.get("activation", {})
    if activation != {"authority": "NONE", "v1RemainsEffective": True, "candidatePresenceActivates": False, "requiresSeparateAcceptedCurrentTransition": True}:
        failures.append("MPV2.TAXONOMY.ACTIVATION_INVALID")
    return failures


def _mapping_failures(root: Path, mapping: Any, document: str) -> list[str]:
    if not isinstance(mapping, dict) or mapping.get("schemaVersion") != "SupersetMappingV2":
        return ["MPV2.MAPPING.SCHEMA_INVALID"]
    failures: list[str] = []
    sources = mapping.get("sources")
    rows = mapping.get("rows")
    if not isinstance(sources, list) or not isinstance(rows, list):
        return ["MPV2.MAPPING.SCHEMA_INVALID"]
    try:
        expected_sources = expected_source_records(root)
    except (KeyError, OSError, UnicodeError, SyntaxError, ValueError):
        return ["MPV2.MAPPING.SOURCE_INVENTORY_FAILED"]
    source_by_id: dict[str, dict[str, Any]] = {}
    if set(source.get("sourceId") for source in sources if isinstance(source, dict)) != set(expected_sources):
        failures.append("MPV2.MAPPING.SOURCE_INVENTORY_INVALID")
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("sourceId"), str):
            failures.append("MPV2.MAPPING.SOURCE_INVALID")
            continue
        source_by_id[source["sourceId"]] = source
        expected_source = expected_sources.get(source["sourceId"])
        if expected_source is None or any(source.get(key) != expected_source.get(key) for key in (
            "sourceKind", "repositoryPath", "sourceCommit", "sourceGitBlob", "contentSha256",
            "atomizer", "atomicRequirementCount", "defaultV2Destination",
        )):
            failures.append("MPV2.MAPPING.SOURCE_BINDING_INVALID")
        try:
            data = frozen_source_bytes(root, source)
        except (KeyError, OSError, TypeError):
            failures.append("MPV2.SOURCE.MISSING")
            continue
        if _sha256(data) != source.get("contentSha256") or _git_blob(data) != source.get("sourceGitBlob"):
            failures.append("MPV2.SOURCE.HASH_MISMATCH")
    try:
        expected = expected_source_atoms(root, mapping)
    except (KeyError, OSError, UnicodeError, SyntaxError, ValueError):
        expected = {}
        failures.append("MPV2.MAPPING.ATOMIZATION_FAILED")
    actual_ids: list[str] = []
    requirement_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != _ROW_FIELDS:
            failures.append("MPV2.MAPPING.ROW_SCHEMA_INVALID")
            continue
        atom_id = row["sourceAtomId"]
        actual_ids.append(atom_id)
        requirement_ids.append(row["requirementId"])
        if row["v2DestinationClause"] not in document:
            failures.append("MPV2.MAPPING.DESTINATION_MISSING")
        atom = expected.get(atom_id)
        if atom is None:
            continue
        source = expected_sources.get(row["sourceId"], {})
        exact_source = (
            row["sourcePath"] == source.get("repositoryPath")
            and row["sourceKind"] == source.get("sourceKind")
            and row["sourceCommit"] == source.get("sourceCommit")
            and row["sourceGitBlob"] == source.get("sourceGitBlob")
            and row["sourceContentSha256"] == source.get("contentSha256")
            and row["sourceAnchor"] == atom.anchor
            and row["sourceClauseSha256"] == atom.clause_sha256
            and row["normalizedAtomicRequirement"] == atom.text
        )
        if not exact_source:
            failures.append("MPV2.MAPPING.SOURCE_BINDING_INVALID")
        expected_destination = _destination(
            atom.source_id, atom.anchor.split("::", 1)[0], atom.text,
            source.get("defaultV2Destination", "## 1. Certification status and authority"),
        )
        if row["v2DestinationClause"] != expected_destination:
            failures.append("MPV2.MAPPING.DESTINATION_INVALID")
        if row["disposition"] not in _DISPOSITIONS:
            failures.append("MPV2.MAPPING.DISPOSITION_INVALID")
        comparison = row["thresholdComparison"]
        if not isinstance(comparison, dict) or comparison.get("relation") not in _THRESHOLD_RELATIONS or not comparison.get("basis"):
            failures.append("MPV2.MAPPING.THRESHOLD_WEAKENED")
        if row["disposition"] in {"RELOCATED", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"} and not row["replacementId"]:
            failures.append("MPV2.MAPPING.REPLACEMENT_REQUIRED")
        if row["disposition"] in {"RELOCATED", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"} and not row["ownerAuthorityRef"]:
            failures.append("MPV2.MAPPING.OWNER_AUTHORITY_REQUIRED")
        if row["result"] not in {"PENDING", "PASS", "FAIL"}:
            failures.append("MPV2.MAPPING.REVIEW_RESULT_INVALID")
    if len(actual_ids) != len(set(actual_ids)):
        failures.append("MPV2.MAPPING.SOURCE_ATOM_DUPLICATE")
    if len(requirement_ids) != len(set(requirement_ids)):
        failures.append("MPV2.MAPPING.REQUIREMENT_ID_DUPLICATE")
    missing = set(expected) - set(actual_ids)
    extra = set(actual_ids) - set(expected)
    if missing:
        failures.append("MPV2.MAPPING.SOURCE_ATOM_MISSING")
    if extra:
        failures.append("MPV2.MAPPING.SOURCE_ATOM_UNKNOWN")
    for source in expected_sources.values():
        count = sum(row.get("sourceId") == source.get("sourceId") for row in rows if isinstance(row, dict))
        if count != source.get("atomicRequirementCount"):
            failures.append("MPV2.MAPPING.SOURCE_COUNT_MISMATCH")
    certification = mapping.get("certification")
    expected_certification = {
        "structuralResult": "PASS",
        "semanticReview": "PENDING_INDEPENDENT_REVIEW",
        "ownerExactBytesApproval": "PENDING",
        "eligibleNonAuthorExactHead": "PENDING",
        "activation": "NONE",
    }
    if certification != expected_certification:
        failures.append("MPV2.MAPPING.CERTIFICATION_STATE_INVALID")
    return failures


def public_sanitization_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_ARTIFACTS:
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if any(pattern.search(text) for pattern in _PRIVATE_PATTERNS):
            failures.append(f"MPV2.PUBLIC.PRIVATE_DATA:{relative}")
    return failures


def _binding_failures(root: Path, binding: Any, document_bytes: bytes, mapping_bytes: bytes, taxonomy_bytes: bytes) -> list[str]:
    if not isinstance(binding, dict):
        return ["MPV2.BINDING.SCHEMA_INVALID"]
    failures: list[str] = []
    expected = {
        "schemaVersion": "MasterProgramProposalBindingV2",
        "controllerIssue": 521,
        "bootstrapBranch": "phase-1-closure-process-521-master-program-v2",
        "acceptedBaseSha": BASE_SHA,
        "proposalState": "PROPOSED",
        "implementationAuthority": "NONE",
        "activeProgramRoute": None,
        "supersedesV1": False,
    }
    for key, value in expected.items():
        if binding.get(key) != value:
            failures.append("MPV2.BINDING.AUTHORITY_INVALID")
    hashes = binding.get("artifactHashes", {})
    if hashes.get("documentSha256") != _sha256(document_bytes):
        failures.append("MPV2.BINDING.DOCUMENT_HASH_MISMATCH")
    if hashes.get("mappingSha256") != _sha256(mapping_bytes):
        failures.append("MPV2.BINDING.MAPPING_HASH_MISMATCH")
    if hashes.get("taxonomySha256") != _sha256(taxonomy_bytes):
        failures.append("MPV2.BINDING.TAXONOMY_HASH_MISMATCH")
    predecessor = binding.get("predecessor", {})
    if predecessor.get("v1DocumentSha256") != V1_SHA256 or predecessor.get("fiveCutRoadmapSha256") != ROADMAP_SHA256 or predecessor.get("adr0079Sha256") != ADR0079_SHA256:
        failures.append("MPV2.BINDING.PREDECESSOR_INVALID")
    approvals = binding.get("requiredApprovals", {})
    if approvals != {"ownerExactBytes": "PENDING", "eligibleNonAuthorExactHead": "PENDING", "referenceOnlyMergeWording": "PENDING"}:
        failures.append("MPV2.BINDING.APPROVAL_STATE_INVALID")
    if binding.get("activationTransition", {}).get("createdBy") != "separately-governed accepted-current transition after protected merge":
        failures.append("MPV2.BINDING.ACTIVATION_PATH_INVALID")
    return failures


def validate_repository(root: Path, *, certification: bool) -> list[str]:
    failures: list[str] = []
    missing = [relative for relative in REQUIRED_ARTIFACTS if not (root / relative).is_file()]
    if missing:
        return [f"MPV2.ARTIFACT.MISSING:{relative}" for relative in missing]
    try:
        mapping = _load_json(root / MAPPING_PATH)
        taxonomy = _load_json(root / TAXONOMY_PATH)
        binding = _load_json(root / BINDING_PATH)
    except DuplicateJsonMember:
        return ["MPV2.JSON.DUPLICATE_MEMBER"]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ["MPV2.JSON.INVALID"]
    document_bytes = (root / DOCUMENT_PATH).read_bytes()
    mapping_bytes = (root / MAPPING_PATH).read_bytes()
    taxonomy_bytes = (root / TAXONOMY_PATH).read_bytes()
    if _sha256(document_bytes) != DOCUMENT_SHA256:
        failures.append("MPV2.SOURCE.DOCUMENT_HASH_DRIFT")
    if _sha256(mapping_bytes) != MAPPING_SHA256:
        failures.append("MPV2.SOURCE.MAPPING_HASH_DRIFT")
    if _sha256(taxonomy_bytes) != TAXONOMY_SHA256:
        failures.append("MPV2.SOURCE.TAXONOMY_HASH_DRIFT")
    try:
        document = document_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return ["MPV2.DOCUMENT.UTF8_INVALID"]
    failures.extend(_mapping_failures(root, mapping, document))
    failures.extend(_taxonomy_failures(taxonomy))
    failures.extend(_binding_failures(root, binding, document_bytes, mapping_bytes, taxonomy_bytes))
    failures.extend(public_sanitization_failures(root))
    if _sha256((root / V1_PATH).read_bytes()) != V1_SHA256:
        failures.append("MPV2.SOURCE.V1_MUTATED")
    if certification:
        certification_state = mapping.get("certification", {})
        if certification_state.get("semanticReview") != "PASS" or any(row.get("result") != "PASS" for row in mapping.get("rows", []) if isinstance(row, dict)):
            failures.append("MPV2.CERTIFICATION.INDEPENDENT_REVIEW_PENDING")
        if certification_state.get("ownerExactBytesApproval") != "PASS":
            failures.append("MPV2.CERTIFICATION.OWNER_EXACT_BYTES_PENDING")
        if certification_state.get("eligibleNonAuthorExactHead") != "PASS":
            failures.append("MPV2.CERTIFICATION.ELIGIBLE_NON_AUTHOR_PENDING")
        if certification_state.get("activation") != "ACCEPTED_CURRENT":
            failures.append("MPV2.CERTIFICATION.ACTIVATION_PENDING")
    return list(dict.fromkeys(failures))


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--emit-mapping", action="store_true")
    parser.add_argument("--certification", action="store_true")
    args = parser.parse_args(argv)
    if args.emit_mapping:
        sys.stdout.write(render_mapping(generate_mapping(args.root)))
        return 0
    failures = validate_repository(args.root, certification=args.certification)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print("PASS Master Program V2 candidate structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
