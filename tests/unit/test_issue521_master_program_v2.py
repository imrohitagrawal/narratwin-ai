from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any, Callable

import pytest

from scripts.quality import issue521_master_program_v2 as program


REPO = Path(__file__).resolve().parents[2]


def _copy_candidate(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    mapping = json.loads((REPO / program.MAPPING_PATH).read_text(encoding="utf-8"))
    paths = set(program.REQUIRED_ARTIFACTS)
    for relative in sorted(paths):
        source = REPO / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    for source_record in mapping["sources"]:
        if source_record["sourceKind"] != "REPOSITORY_FILE":
            continue
        relative = source_record["repositoryPath"]
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(program.frozen_source_bytes(REPO, source_record))
    return root


def _rewrite_json(root: Path, relative: str, mutate: Callable[[dict[str, Any]], None]) -> None:
    path = root / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_candidate_repository_is_structurally_complete_and_non_activating() -> None:
    assert program.validate_repository(REPO, certification=False) == []
    certification = program.validate_repository(REPO, certification=True)
    assert "MPV2.CERTIFICATION.INDEPENDENT_REVIEW_PENDING" in certification
    assert "MPV2.CERTIFICATION.OWNER_EXACT_BYTES_PENDING" in certification
    assert "MPV2.CERTIFICATION.ELIGIBLE_NON_AUTHOR_PENDING" in certification


def test_frozen_baseline_hashes_are_exact() -> None:
    binding = json.loads((REPO / program.BINDING_PATH).read_text(encoding="utf-8"))
    assert binding["acceptedBaseSha"] == "b6b0c05c7227428ff0841361f3970b0b2c40aa86"
    assert binding["predecessor"]["v1GitBlob"] == "2216951d9716b7c946098ab454265eafa25975bd"
    assert binding["predecessor"]["v1DocumentSha256"] == "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
    assert binding["predecessor"]["fiveCutRoadmapSha256"] == "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b"
    assert binding["predecessor"]["adr0079Sha256"] == "a20ae1b9fae9e12e9e50baa372b0672c43a9417a21b36a2dc4276f5be1529fd5"
    assert binding["proposalState"] == "PROPOSED"
    assert binding["implementationAuthority"] == "NONE"
    assert binding["activeProgramRoute"] is None
    assert binding["supersedesV1"] is False


def test_mapping_has_one_unique_row_for_every_deterministic_source_atom() -> None:
    mapping = json.loads((REPO / program.MAPPING_PATH).read_text(encoding="utf-8"))
    expected = program.expected_source_atoms(REPO, mapping)
    actual = [row["sourceAtomId"] for row in mapping["rows"]]
    assert len(actual) == len(set(actual)) == len(expected)
    assert set(actual) == set(expected)


@pytest.mark.parametrize(
    ("name", "mutate", "expected"),
    [
        (
            "missing-row",
            lambda value: value["rows"].pop(),
            "MPV2.MAPPING.SOURCE_ATOM_MISSING",
        ),
        (
            "duplicate-row",
            lambda value: value["rows"].append(copy.deepcopy(value["rows"][0])),
            "MPV2.MAPPING.SOURCE_ATOM_DUPLICATE",
        ),
        (
            "unclassified",
            lambda value: value["rows"][0].update({"disposition": "UNKNOWN"}),
            "MPV2.MAPPING.DISPOSITION_INVALID",
        ),
        (
            "missing-destination",
            lambda value: value["rows"][0].update({"v2DestinationClause": "§ missing"}),
            "MPV2.MAPPING.DESTINATION_MISSING",
        ),
        (
            "weak-threshold",
            lambda value: value["rows"][0]["thresholdComparison"].update(
                {"relation": "WEAKER"}
            ),
            "MPV2.MAPPING.THRESHOLD_WEAKENED",
        ),
        (
            "relocated-without-replacement",
            lambda value: value["rows"][0].update(
                {"disposition": "RELOCATED", "replacementId": None}
            ),
            "MPV2.MAPPING.REPLACEMENT_REQUIRED",
        ),
        (
            "superseded-without-owner-authority",
            lambda value: value["rows"][0].update(
                {
                    "disposition": "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
                    "replacementId": "MPV2-001",
                    "ownerAuthorityRef": None,
                }
            ),
            "MPV2.MAPPING.OWNER_AUTHORITY_REQUIRED",
        ),
    ],
)
def test_mapping_mutations_fail_closed(
    tmp_path: Path, name: str, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    del name
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.MAPPING_PATH, mutate)
    assert expected in program.validate_repository(root, certification=False)


def test_source_and_destination_byte_mutations_fail_closed(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    source = root / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    assert "MPV2.SOURCE.HASH_MISMATCH" in program.validate_repository(
        root, certification=False
    )

    root = _copy_candidate(tmp_path)
    v2 = root / program.DOCUMENT_PATH
    v2.write_text(
        v2.read_text(encoding="utf-8").replace(
            "## 3. Universal prototype-before-code gate",
            "## removed prototype gate",
            1,
        ),
        encoding="utf-8",
    )
    failures = program.validate_repository(root, certification=False)
    assert "MPV2.BINDING.DOCUMENT_HASH_MISMATCH" in failures
    assert "MPV2.MAPPING.DESTINATION_MISSING" in failures


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda value: value["legacyAliases"][0].update({"canonicalCut": "Cut5"}),
            "MPV2.TAXONOMY.LEGACY_CUT5_TARGET_INVALID",
        ),
        (
            lambda value: value["legacyAliases"][0].update(
                {"canSatisfyNewCut5": True}
            ),
            "MPV2.TAXONOMY.LEGACY_EVIDENCE_CROSSED",
        ),
        (
            lambda value: value["legacyAliases"][0].update(
                {"cut6MigrationValidationRequired": False}
            ),
            "MPV2.TAXONOMY.CUT6_MIGRATION_BYPASSED",
        ),
        (
            lambda value: value["cuts"].append(copy.deepcopy(value["cuts"][0])),
            "MPV2.TAXONOMY.DUPLICATE_ID",
        ),
        (
            lambda value: value["digitalTwinSequence"].pop(),
            "MPV2.TAXONOMY.DT_SEQUENCE_INCOMPLETE",
        ),
    ],
)
def test_taxonomy_mutations_fail_closed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.TAXONOMY_PATH, mutate)
    assert expected in program.validate_repository(root, certification=False)


def test_mapping_and_taxonomy_reject_duplicate_json_members(tmp_path: Path) -> None:
    for relative, needle, duplicate in (
        (program.MAPPING_PATH, '"schemaVersion":', '"schemaVersion":"Bypass",'),
        (program.TAXONOMY_PATH, '"schemaVersion":', '"schemaVersion":"Bypass",'),
    ):
        root = _copy_candidate(tmp_path)
        path = root / relative
        path.write_text(
            path.read_text(encoding="utf-8").replace(needle, duplicate + needle, 1),
            encoding="utf-8",
        )
        assert "MPV2.JSON.DUPLICATE_MEMBER" in program.validate_repository(
            root, certification=False
        )


def test_public_candidate_contains_no_private_path_or_provider_authority() -> None:
    failures = program.public_sanitization_failures(REPO)
    assert failures == []
    document = (REPO / program.DOCUMENT_PATH).read_text(encoding="utf-8")
    for required in (
        "Default authority is zero uploads, zero create operations, and USD 0.",
        "Current authority permits repository governance work only.",
        "V1 remains effective until V2 certification and activation complete.",
        "No provider is selected or activated.",
        "Generated UI must never be used as evidence of actual NarraTwin behavior.",
    ):
        assert required in document


def test_review_surfaces_are_pending_and_cannot_self_certify() -> None:
    binding = json.loads((REPO / program.BINDING_PATH).read_text(encoding="utf-8"))
    assert {review["state"] for review in binding["requiredReviews"]} == {
        "PENDING_INDEPENDENT_REVIEW"
    }
    assert binding["requiredApprovals"] == {
        "ownerExactBytes": "PENDING",
        "eligibleNonAuthorExactHead": "PENDING",
        "referenceOnlyMergeWording": "PENDING",
    }


def test_issue_521_preflight_is_exact_and_bounded() -> None:
    preflight = json.loads(
        (REPO / "docs/governance/preflights/issue-521.json").read_text(encoding="utf-8")
    )
    assert preflight["issue_number"] == 521
    assert preflight["branch"] == "phase-1-closure-process-521-master-program-v2"
    assert len(preflight["scope"]["required"]) == 24
    assert preflight["scope"]["required"] == preflight["scope"]["allowed_prefixes"]
    assert "AGENTS.md" in preflight["scope"]["forbidden"]
