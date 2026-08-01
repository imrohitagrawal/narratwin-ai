from __future__ import annotations

import json
from typing import Any, Callable

import pytest


def test_contract_has_exact_classes_surfaces_and_authority(publication_boundary: Any) -> None:
    package = publication_boundary
    source = package.repository.read(package.CONTRACT_PATH)
    contract, failures = package.contract.validate_contract_text(source)
    assert failures == []
    assert contract is not None
    assert [row["id"] for row in contract["classes"]] == ["PUBLIC", "INTERNAL", "RESTRICTED"]
    assert {row["id"] for row in contract["surfaceFamilies"]} == package.SURFACE_IDS
    assert len(contract["surfaceFamilies"]) == 12
    assert contract["promotionRules"] == package.PROMOTION_RULES


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda row: row.update({"unexpected": True}), "strict top-level schema"),
        (lambda row: row.update({"schemaVersion": "PublicationBoundaryV2"}), "schema version"),
        (lambda row: row.update({"publicProductStatement": "Generic avatar product"}), "public product statement"),
        (lambda row: row["classes"][0].update({"id": "OPEN"}), "classification contract"),
        (lambda row: row["promotionRules"].update({"modelMayReclassify": True}), "promotion rules"),
    ],
)
def test_contract_mutations_fail_closed(
    publication_boundary: Any,
    mutation: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    package = publication_boundary
    contract = json.loads(package.repository.read(package.CONTRACT_PATH))
    mutation(contract)
    _parsed, failures = package.contract.validate_contract_text(json.dumps(contract))
    assert any(expected in failure for failure in failures)


def test_duplicate_json_key_fails_closed(publication_boundary: Any) -> None:
    package = publication_boundary
    source = package.repository.read(package.CONTRACT_PATH)
    duplicate = source.replace(
        '"schemaVersion": "PublicationBoundaryV1",',
        '"schemaVersion": "PublicationBoundaryV1",\n  "schemaVersion": "PublicationBoundaryV1",',
        1,
    )
    _contract, failures = package.contract.validate_contract_text(duplicate)
    assert any("duplicate JSON key" in failure for failure in failures)


@pytest.mark.parametrize("operation", ["duplicate", "missing"])
def test_surface_inventory_mutations_fail_closed(
    publication_boundary: Any, operation: str
) -> None:
    package = publication_boundary
    contract = json.loads(package.repository.read(package.CONTRACT_PATH))
    if operation == "duplicate":
        contract["surfaceFamilies"].append(dict(contract["surfaceFamilies"][0]))
    else:
        contract["surfaceFamilies"].pop()
    _parsed, failures = package.contract.validate_contract_text(json.dumps(contract))
    assert any("surface families" in failure for failure in failures)

