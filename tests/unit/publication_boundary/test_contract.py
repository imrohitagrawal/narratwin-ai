from __future__ import annotations

import json
from typing import Any, Callable

import pytest


def source_and_contract(package: Any) -> tuple[str, dict[str, Any]]:
    source = package.repository.read(package.CONTRACT_PATH)
    return source, json.loads(source)


def test_contract_compiles_every_load_bearing_field(publication_boundary: Any) -> None:
    package = publication_boundary
    source, contract = source_and_contract(package)
    compiled, failures = package.contract.validate_contract_text(source)
    assert failures == []
    assert compiled is not None
    assert compiled.schema_version == "PublicationBoundaryV1"
    assert compiled.authority_order == tuple(contract["authorityOrder"])
    assert compiled.class_ids == ("PUBLIC", "INTERNAL", "RESTRICTED")
    assert compiled.surface_ids == frozenset(row["id"] for row in contract["surfaceFamilies"])
    assert compiled.human_approval_required is True
    assert contract["canonicalPublicSources"] == package.contract.CANONICAL_PUBLIC_SOURCES
    assert contract["legacyReplacement"] == package.contract.LEGACY_REPLACEMENT
    assert contract["launchPosture"] == package.contract.LAUNCH_POSTURE


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda row: row.update({"unexpected": True}), "strict top-level schema"),
        (lambda row: row.pop("schemaVersion"), "strict top-level schema"),
        (lambda row: row.update({"schemaVersion": "PublicationBoundaryV2"}), "schema version"),
        (lambda row: row.update({"publicProductStatement": "Generic avatar"}), "public product statement"),
        (lambda row: row["authorityOrder"].reverse(), "authority order"),
        (lambda row: row["authorityOrder"].append(row["authorityOrder"][0]), "authority order"),
        (lambda row: row["classes"][0].update({"destination": "ANYWHERE"}), "classification contract"),
        (lambda row: row["classes"][1].update({"defaultAction": "ALLOW"}), "classification contract"),
        (lambda row: row["classes"][2].update({"unexpected": True}), "classification contract"),
        (lambda row: row["surfaceFamilies"][0].update({"defaultClassification": "PUBLIC"}), "surface families"),
        (lambda row: row["surfaceFamilies"][1].update({"publicAction": "ALLOW"}), "surface families"),
        (lambda row: row["surfaceFamilies"][2].update({"unexpected": True}), "surface families"),
        (lambda row: row["promotionRules"].update({"modelMayReclassify": True}), "promotion rules"),
        (lambda row: row["canonicalPublicSources"].pop(), "canonical public sources"),
        (lambda row: row["legacyReplacement"].update({"removedPath": "active.md"}), "legacy replacement"),
        (lambda row: row["launchPosture"].update({"publicDistributionAuthorized": True}), "launch No-Go"),
    ],
)
def test_contract_mutations_fail_closed(
    publication_boundary: Any,
    mutation: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    package = publication_boundary
    _source, contract = source_and_contract(package)
    mutation(contract)
    compiled, failures = package.contract.validate_contract_text(json.dumps(contract))
    assert compiled is None
    assert any(expected in failure for failure in failures)


def test_duplicate_json_key_fails_closed(publication_boundary: Any) -> None:
    package = publication_boundary
    source, _contract = source_and_contract(package)
    duplicate = source.replace(
        '"schemaVersion": "PublicationBoundaryV1",',
        '"schemaVersion": "PublicationBoundaryV1",\n  "schemaVersion": "PublicationBoundaryV1",',
        1,
    )
    compiled, failures = package.contract.validate_contract_text(duplicate)
    assert compiled is None
    assert any("duplicate JSON key" in failure for failure in failures)


@pytest.mark.parametrize("source", ["{", "null", "[]", '"text"'])
def test_malformed_or_wrong_root_json_fails_closed(
    publication_boundary: Any, source: str
) -> None:
    compiled, failures = publication_boundary.contract.validate_contract_text(source)
    assert compiled is None
    assert failures


def test_oversized_contract_fails_before_parsing(publication_boundary: Any) -> None:
    package = publication_boundary
    oversized = " " * (package.contract.MAX_CONTRACT_BYTES + 1)
    compiled, failures = package.contract.validate_contract_text(oversized)
    assert compiled is None
    assert any("size limit" in failure for failure in failures)
