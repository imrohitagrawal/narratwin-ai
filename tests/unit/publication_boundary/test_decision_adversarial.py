from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest


def policy(package: Any) -> Any:
    compiled, failures = package.contract.validate_contract_text(
        package.repository.read(package.CONTRACT_PATH)
    )
    assert failures == []
    assert compiled is not None
    return compiled


def approval(package: Any, compiled: Any, envelope: dict[str, Any]) -> Any:
    return package.PublicationApproval(
        approval_id="approval-test-001",
        policy_version=compiled.schema_version,
        approved_by="accountable-human:test",
        classification="PUBLIC",
        provenance_classifications=("PUBLIC",),
        surface=envelope["surface"],
        source_bindings=(("source-test-001", "a" * 64),),
        envelope_sha256=package.envelope_digest(envelope),
    )


def test_directly_forged_policy_cannot_expand_classes_or_surfaces(
    publication_boundary: Any,
) -> None:
    package = publication_boundary
    forged = package.CompiledPublicationPolicy(
        schema_version="AttackerPolicyV0",
        authority_order=("ATTACKER",),
        class_ids=("PUBLIC",),
        surface_ids=frozenset({"ATTACKER_SURFACE"}),
        human_approval_required=True,
    )
    envelope = {"surface": "ATTACKER_SURFACE", "payload": {}}
    record = approval(package, forged, envelope)

    assert package.publication_decision(
        forged,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == "BLOCK"


def test_registry_exception_fails_closed(publication_boundary: Any) -> None:
    package = publication_boundary
    compiled = policy(package)
    envelope = {"surface": "CANONICAL_DOCUMENTS", "payload": {}}

    class ExplodingRegistry(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("registry backend exploded")

    assert package.publication_decision(
        compiled,
        envelope,
        approval_id="approval-test-001",
        approvals=ExplodingRegistry(),
    ) == "BLOCK"


def test_deep_payload_serialization_exception_fails_closed(publication_boundary: Any) -> None:
    package = publication_boundary
    compiled = policy(package)
    nested: dict[str, Any] = {}
    cursor = nested
    for _index in range(20_000):
        child: dict[str, Any] = {}
        cursor["nested"] = child
        cursor = child
    envelope = {"surface": "CANONICAL_DOCUMENTS", "payload": nested}
    record = package.PublicationApproval(
        approval_id="approval-test-001",
        policy_version=compiled.schema_version,
        approved_by="accountable-human:test",
        classification="PUBLIC",
        provenance_classifications=("PUBLIC",),
        surface=envelope["surface"],
        source_bindings=(("source-test-001", "a" * 64),),
        envelope_sha256="a" * 64,
    )

    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == "BLOCK"


def test_digest_is_canonical_and_stops_at_byte_limit(publication_boundary: Any) -> None:
    package = publication_boundary
    envelope = {"surface": "CANONICAL_DOCUMENTS", "payload": {"text": "é"}}
    encoded = json.dumps(
        envelope,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert package.envelope_digest(envelope) == hashlib.sha256(encoded).hexdigest()

    oversized = {
        "surface": "CANONICAL_DOCUMENTS",
        "payload": {"text": "x" * (package.decision.MAX_ENVELOPE_BYTES + 1)},
    }
    with pytest.raises(ValueError, match="too large"):
        package.envelope_digest(oversized)
