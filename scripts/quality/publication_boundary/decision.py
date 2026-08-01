"""Pure fail-closed decisions using trusted, payload-bound approvals."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .contract import AUTHORITY_ORDER, CLASS_ROWS, SURFACE_ORDER
from .contract import CompiledPublicationPolicy


ENVELOPE_FIELDS = {"surface", "payload"}
MAX_ENVELOPE_BYTES = 65_536
IDENTIFIER = re.compile(r"[A-Za-z0-9._:-]{1,128}")
SHA256 = re.compile(r"[0-9a-f]{64}")
EXPECTED_CLASSES = tuple(row["id"] for row in CLASS_ROWS)
EXPECTED_SURFACES = frozenset(SURFACE_ORDER)


@dataclass(frozen=True)
class PublicationApproval:
    """Server-side approval record; untrusted payloads cannot supply this type."""

    approval_id: str
    policy_version: str
    approved_by: str
    classification: str
    provenance_classifications: tuple[str, ...]
    surface: str
    source_bindings: tuple[tuple[str, str], ...]
    envelope_sha256: str


def envelope_digest(envelope: dict[str, Any]) -> str:
    """Return a stable digest for an exact bounded JSON publication envelope."""
    encoder = json.JSONEncoder(
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256()
    encoded_bytes = 0
    for chunk in encoder.iterencode(envelope):
        encoded = chunk.encode("utf-8")
        encoded_bytes += len(encoded)
        if encoded_bytes > MAX_ENVELOPE_BYTES:
            raise ValueError("publication envelope is too large")
        digest.update(encoded)
    return digest.hexdigest()


def _valid_sources(bindings: Any) -> bool:
    if not isinstance(bindings, tuple) or not bindings or len(bindings) > 64:
        return False
    identifiers: list[str] = []
    for binding in bindings:
        if not isinstance(binding, tuple) or len(binding) != 2:
            return False
        source_id, checksum = binding
        if (
            not isinstance(source_id, str)
            or IDENTIFIER.fullmatch(source_id) is None
            or not isinstance(checksum, str)
            or SHA256.fullmatch(checksum) is None
        ):
            return False
        identifiers.append(source_id)
    return len(identifiers) == len(set(identifiers))


def _decide(
    policy: CompiledPublicationPolicy,
    envelope: Any,
    *,
    approval_id: str,
    approvals: Mapping[str, PublicationApproval],
) -> str:
    if (
        not isinstance(policy, CompiledPublicationPolicy)
        or policy.schema_version != "PublicationBoundaryV1"
        or policy.authority_order != tuple(AUTHORITY_ORDER)
        or policy.class_ids != EXPECTED_CLASSES
        or policy.surface_ids != EXPECTED_SURFACES
        or policy.human_approval_required is not True
    ):
        return "BLOCK"
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE_FIELDS:
        return "BLOCK"
    surface = envelope.get("surface")
    if surface not in policy.surface_ids or not isinstance(envelope.get("payload"), dict):
        return "BLOCK"
    if not isinstance(approval_id, str) or IDENTIFIER.fullmatch(approval_id) is None:
        return "BLOCK"
    record = approvals.get(approval_id)
    if not isinstance(record, PublicationApproval):
        return "BLOCK"
    if (
        record.approval_id != approval_id
        or record.policy_version != policy.schema_version
        or record.surface != surface
        or not isinstance(record.approved_by, str)
        or IDENTIFIER.fullmatch(record.approved_by) is None
        or record.classification not in policy.class_ids
        or not isinstance(record.provenance_classifications, tuple)
        or not record.provenance_classifications
        or any(item not in policy.class_ids for item in record.provenance_classifications)
        or not _valid_sources(record.source_bindings)
        or record.envelope_sha256 != envelope_digest(envelope)
    ):
        return "BLOCK"
    combined = set(record.provenance_classifications) | {record.classification}
    if "RESTRICTED" in combined:
        return "BLOCK"
    if "INTERNAL" in combined:
        return "OMIT"
    return "ALLOW"


def publication_decision(
    policy: CompiledPublicationPolicy,
    envelope: Any,
    *,
    approval_id: str,
    approvals: Mapping[str, PublicationApproval],
) -> str:
    """Fail closed on malformed payload, authority, registry, or serialization."""
    try:
        return _decide(
            policy,
            envelope,
            approval_id=approval_id,
            approvals=approvals,
        )
    except Exception:
        return "BLOCK"
