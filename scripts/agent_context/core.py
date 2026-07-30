"""Initial executable seam for Issue #319 behavioral RED.

This deliberately small baseline mirrors the current repository gap: data can be
hashed and echoed, but authority and routing invariants are not yet enforced.
Committed RED tests demonstrate the missing behavior before the GREEN replacement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class Finding:
    """One deterministic validation finding."""

    code: str
    detail: str = ""


def canonical_digest(value: Any) -> str:
    """Return the stable SHA-256 digest used by shadow artifacts."""

    payload = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_manifest(
    manifest: JsonObject,
    *,
    repository_root: Path | None = None,
    repository_commit: str | None = None,
    module_content: dict[str, bytes] | None = None,
) -> list[Finding]:
    """Return manifest findings; the RED baseline does not enforce them yet."""

    del manifest, repository_root, repository_commit, module_content
    return []


def intersect_authority(
    repository: JsonObject,
    issue: JsonObject,
    parent: JsonObject,
    child: JsonObject,
) -> tuple[JsonObject, list[Finding]]:
    """Return the requested child envelope in the permissive RED baseline."""

    del repository, issue, parent
    return child, []


def validate_capsule(
    capsule: JsonObject,
    *,
    repository_authority: JsonObject,
    issue_authority: JsonObject,
    parent_capsule: JsonObject | None,
    actual_branch: str,
    actual_head: str,
) -> list[Finding]:
    """Return capsule findings; the RED baseline accepts every capsule."""

    del capsule, repository_authority, issue_authority, parent_capsule
    del actual_branch, actual_head
    return []


def validate_receipt(
    receipt: JsonObject,
    *,
    capsule: JsonObject,
    manifest_digest: str,
    actual_branch: str,
    actual_head: str,
) -> list[Finding]:
    """Return receipt findings; the RED baseline accepts every receipt."""

    del receipt, capsule, manifest_digest, actual_branch, actual_head
    return []


def validate_path(path: str, *, repository_root: Path | None = None) -> list[Finding]:
    """Return path findings; the RED baseline treats paths as inert strings."""

    del path, repository_root
    return []


def detect_write_set_collisions(capsules: list[JsonObject]) -> list[Finding]:
    """Return collision findings; the RED baseline has no reservation model."""

    del capsules
    return []


def detect_state_contradictions(
    current_state: JsonObject | None,
    *,
    prose_claims: list[JsonObject],
    historical_entries: list[JsonObject],
) -> list[Finding]:
    """Return state findings; the RED baseline does not distinguish time planes."""

    del current_state, prose_claims, historical_entries
    return []


def route_request(
    manifest: JsonObject,
    request: JsonObject,
    *,
    fixture_set: JsonObject | None = None,
) -> tuple[JsonObject, list[Finding]]:
    """Echo a generic route so fixture comparisons fail behaviorally in RED."""

    del manifest, fixture_set
    receipt = {
        "schemaVersion": "RoutingReceiptV1",
        "routeId": "generic",
        "requestDigest": canonical_digest(request),
        "includedModules": [],
        "rejectedModules": [],
        "dependencyClosure": [],
        "unresolvedConflicts": [],
    }
    return receipt, []


def build_packet(
    manifest: JsonObject,
    route: JsonObject,
    module_content: dict[str, str],
    *,
    line_ceiling: int,
    token_ceiling: int,
) -> tuple[JsonObject, list[Finding]]:
    """Build an unbounded packet in the permissive RED baseline."""

    packet = {
        "schemaVersion": "ContextPacketV1",
        "manifestDigest": canonical_digest(manifest),
        "routeDigest": canonical_digest(route),
        "modules": module_content,
        "lineCeiling": line_ceiling,
        "tokenCeiling": token_ceiling,
    }
    return packet, []
