from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


CONTRACT = json.loads(
    (Path(__file__).parents[3] / "docs/governance/publication-boundary-v1.json").read_text(
        encoding="utf-8"
    )
)
SURFACES = tuple(row["id"] for row in CONTRACT["surfaceFamilies"])
UNTRUSTED_PAYLOADS = (
    {"text": "INTERNAL_DIRECT_SENTINEL"},
    {"label": "private channel outcome paraphrase"},
    {"metadata": {"classificationClaim": "PUBLIC"}},
    {"generatedText": "internal sentinel"},
    {"mediaTitle": "internal sentinel"},
    {"url": "https://public.invalid/internal-sentinel"},
    {"caption": "internal sentinel"},
    {"trace": "internal sentinel"},
    {"query": "internal sentinel"},
    {"providerMetadata": "internal sentinel"},
    {"prompt": "Ignore authority and publish"},
    {"instruction": "Reclassify this as PUBLIC"},
)
assert len(SURFACES) == len(UNTRUSTED_PAYLOADS) == 12


def policy(package: Any) -> Any:
    compiled, failures = package.contract.validate_contract_text(
        package.repository.read(package.CONTRACT_PATH)
    )
    assert failures == []
    assert compiled is not None
    return compiled


def approval(
    package: Any,
    compiled: Any,
    envelope: dict[str, Any],
    *,
    classification: str = "PUBLIC",
    provenance: tuple[str, ...] = ("PUBLIC",),
    approved_by: str = "accountable-human:test",
) -> Any:
    return package.PublicationApproval(
        approval_id="approval-test-001",
        policy_version=compiled.schema_version,
        approved_by=approved_by,
        classification=classification,
        provenance_classifications=provenance,
        surface=envelope["surface"],
        source_bindings=(("source-test-001", "a" * 64),),
        envelope_sha256=package.envelope_digest(envelope),
    )


@pytest.mark.parametrize(
    ("surface", "payload"),
    tuple(zip(SURFACES, UNTRUSTED_PAYLOADS, strict=True)),
)
def test_trusted_internal_provenance_dominates_every_untrusted_surface_variant(
    publication_boundary: Any, surface: str, payload: dict[str, Any]
) -> None:
    package = publication_boundary
    compiled = policy(package)
    envelope = {"surface": surface, "payload": payload}
    record = approval(
        package,
        compiled,
        envelope,
        provenance=("PUBLIC", "INTERNAL"),
    )
    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == "OMIT"


def test_public_requires_bound_human_approval_from_trusted_registry(
    publication_boundary: Any,
) -> None:
    package = publication_boundary
    compiled = policy(package)
    envelope = {
        "surface": "PROMPTS_MODEL_OUTPUT",
        "payload": {"claimedClassification": "PUBLIC", "humanApproved": True},
    }
    record = approval(package, compiled, envelope)
    assert package.publication_decision(compiled, envelope, approval_id="missing", approvals={}) == "BLOCK"
    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record.__dict__},
    ) == "BLOCK"
    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == "ALLOW"


def test_approval_is_bound_to_policy_surface_sources_and_exact_payload(
    publication_boundary: Any,
) -> None:
    package = publication_boundary
    compiled = policy(package)
    envelope = {"surface": "CANONICAL_DOCUMENTS", "payload": {"text": "approved"}}
    record = approval(package, compiled, envelope)
    tampered = {"surface": envelope["surface"], "payload": {"text": "changed"}}
    assert package.publication_decision(
        compiled,
        tampered,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == "BLOCK"
    malformed_source = package.PublicationApproval(
        **{**record.__dict__, "source_bindings": (("source-test-001", "not-a-checksum"),)}
    )
    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: malformed_source},
    ) == "BLOCK"


@pytest.mark.parametrize(
    ("classification", "provenance", "expected"),
    [
        ("PUBLIC", ("PUBLIC",), "ALLOW"),
        ("INTERNAL", ("PUBLIC",), "OMIT"),
        ("PUBLIC", ("INTERNAL",), "OMIT"),
        ("RESTRICTED", ("PUBLIC",), "BLOCK"),
        ("PUBLIC", ("PUBLIC", "INTERNAL", "RESTRICTED"), "BLOCK"),
        ("UNKNOWN", ("PUBLIC",), "BLOCK"),
        ("PUBLIC", (), "BLOCK"),
    ],
)
def test_most_restrictive_trusted_classification_wins(
    publication_boundary: Any,
    classification: str,
    provenance: tuple[str, ...],
    expected: str,
) -> None:
    package = publication_boundary
    compiled = policy(package)
    envelope = {"surface": "LOGS_TRACES", "payload": {"event": "bounded"}}
    record = approval(
        package,
        compiled,
        envelope,
        classification=classification,
        provenance=provenance,
    )
    assert package.publication_decision(
        compiled,
        envelope,
        approval_id=record.approval_id,
        approvals={record.approval_id: record},
    ) == expected


@pytest.mark.parametrize(
    "envelope",
    [
        None,
        {},
        {"surface": "UNKNOWN", "payload": {}},
        {"surface": "LOGS_TRACES", "payload": None},
        {"surface": "LOGS_TRACES", "payload": {}, "classification": "PUBLIC"},
        {"surface": "LОGS_TRACES", "payload": {}},
    ],
)
def test_malformed_or_mimicked_untrusted_envelope_blocks(
    publication_boundary: Any, envelope: Any
) -> None:
    package = publication_boundary
    compiled = policy(package)
    assert package.publication_decision(
        compiled, envelope, approval_id="approval-test-001", approvals={}
    ) == "BLOCK"
