from __future__ import annotations

import copy
import hashlib
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


def test_markdown_atomizer_is_clause_atomic_and_keeps_full_heading_context() -> None:
    source = "# Root\n## 5. Parent contract\n### Child contract\nThe service must preserve A; it must preserve B. It must preserve C.\n| Item | Requirement | Result |\n|---|---|---|\n| First | The first row must not disappear. | PASS |\n| Second | The second row must remain. | PASS |"
    atoms = program._markdown_atoms("FIXTURE", source)
    texts = [atom.text for atom in atoms]
    assert "The service must preserve A" in texts
    assert "it must preserve B." in texts
    assert "It must preserve C." in texts
    assert any("## 5. Parent contract > ### Child contract" in atom.anchor for atom in atoms)
    assert any(
        "Item=First" in atom.anchor
        and "Requirement=The first row must not disappear." in atom.text
        for atom in atoms
    )
    assert not any("preserve A" in atom.text and "preserve B" in atom.text for atom in atoms)


def test_python_atomizer_covers_provider_defaults_signatures_and_fail_closed_branches() -> None:
    expected = program.expected_source_atoms(REPO)
    by_source = {
        source: "\n".join(atom.text for atom in expected.values() if atom.source_id == source)
        for source in ("AVATAR_PROVIDER_CODE", "TTS_PROVIDER_CODE")
    }
    avatar = by_source["AVATAR_PROVIDER_CODE"]
    for clause in (
        'model_id: str = "disabled"',
        'model_version: str = "disabled"',
        'base_url: str = "https://provider.invalid"',
        "max_script_characters: int = 5_000",
        "max_video_bytes: int = 10 * 1024 * 1024",
        "max_retries: int = 1",
        "max_poll_attempts: int = 3",
        "max_concurrent_jobs: int = 1",
        "provider_supports_hard_delete: bool = False",
        "provider_supports_idempotency: bool = False",
    ):
        assert clause in avatar

    tts = by_source["TTS_PROVIDER_CODE"]
    for clause in (
        "privacy_approved: bool = False",
        "policy_approved: bool = False",
        "budget_audio_tokens: int = 0",
        "budget_microusd: int = 0",
        "quota_requests: int = 0",
        "max_concurrent_requests: int = 1",
    ):
        assert clause in tts
    assert "if not self.config.enabled" in tts
    assert "raise TTSProviderError" in tts


def test_partial_supersession_cannot_consume_sibling_audio_requirements() -> None:
    mapping = program.generate_mapping(REPO)
    duration_rows = [
        row
        for row in mapping["rows"]
        if row["sourceId"] == "MASTER_PROGRAM_V1"
        and "90.000–120.000 seconds" in row["normalizedAtomicRequirement"]
    ]
    assert len(duration_rows) == 1
    assert duration_rows[0]["disposition"] == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"
    assert "RIFF/WAVE" not in duration_rows[0]["normalizedAtomicRequirement"]
    assert "owner listening approval" not in duration_rows[0]["normalizedAtomicRequirement"]
    sibling_rows = [row for row in mapping["rows"] if row["sourceId"] == "MASTER_PROGRAM_V1" and any(phrase in row["normalizedAtomicRequirement"] for phrase in ("RIFF/WAVE", "owner listening approval"))]
    assert sibling_rows
    assert all(row["disposition"] == "PRESERVED" for row in sibling_rows)


def test_destinations_are_resolvable_clause_ids_not_heading_presence() -> None:
    mapping = json.loads((REPO / program.MAPPING_PATH).read_text(encoding="utf-8"))
    document = (REPO / program.DOCUMENT_PATH).read_text(encoding="utf-8")
    assert set(row["v2DestinationClause"] for row in mapping["rows"]) <= set(
        program.DESTINATION_CLAUSES
    )
    for clause_id in program.DESTINATION_CLAUSES:
        assert f"<!-- MPV2-DESTINATION:{clause_id} -->" in document
    headings_only = "\n".join(
        line for line in document.splitlines() if line.startswith("#")
    )
    assert "MPV2.MAPPING.DESTINATION_REGISTRY_MISSING" in program._mapping_failures(
        REPO, mapping, headings_only
    )


def test_dispositions_do_not_mechanically_claim_strengthening() -> None:
    mapping = json.loads((REPO / program.MAPPING_PATH).read_text(encoding="utf-8"))
    assert not [row for row in mapping["rows"] if row["disposition"] == "STRENGTHENED"]
    assert all(
        row["thresholdComparison"]["basis"]
        == program.expected_comparison_basis(row)
        for row in mapping["rows"]
    )


def test_legacy_enterprise_rows_resolve_only_to_cut6() -> None:
    mapping = json.loads((REPO / program.MAPPING_PATH).read_text(encoding="utf-8"))
    rows = [
        row
        for row in mapping["rows"]
        if row["sourceId"] == "FIVE_CUT_ROADMAP"
        and (
            "Enterprise and tenant targets" in row["sourceAnchor"]
            or "Cut 5" in row["sourceAnchor"]
            or "Cut 5" in row["normalizedAtomicRequirement"]
        )
    ]
    assert rows
    assert {row["v2DestinationClause"] for row in rows} == {"MPV2-CUT6"}
    assert {row["disposition"] for row in rows} == {"RELOCATED"}


@pytest.mark.parametrize(("field", "expected"), [
    ("replacementId", "MPV2.MAPPING.REPLACEMENT_UNRESOLVED"),
    ("ownerAuthorityRef", "MPV2.MAPPING.OWNER_AUTHORITY_UNRESOLVED"),
])
def test_replacement_and_owner_authority_references_resolve_exactly(
    tmp_path: Path, field: str, expected: str
) -> None:
    root = _copy_candidate(tmp_path)
    def mutate(value: dict[str, Any]) -> None:
        row = next(item for item in value["rows"] if item["disposition"] in {"RELOCATED", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"})
        row[field] = "DOES-NOT-RESOLVE"
    _rewrite_json(root, program.MAPPING_PATH, mutate)
    assert expected in program.validate_repository(root, certification=False)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda value: value.update({"providerAuthority": "ACTIVE"}), "MPV2.BINDING.SCHEMA_INVALID"),
        (lambda value: value.update({"spendAuthorityUsd": 100}), "MPV2.BINDING.SCHEMA_INVALID"),
        (lambda value: value.update({"privateProviderProfileId": "restricted"}), "MPV2.BINDING.SCHEMA_INVALID"),
        (lambda value: value["predecessor"].update({"v1RemainsEffective": False}), "MPV2.BINDING.PREDECESSOR_INVALID"),
        (lambda value: value["activationTransition"].update({"proposalMayActivate": True}), "MPV2.BINDING.ACTIVATION_PATH_INVALID"),
        (lambda value: value["activationTransition"]["requiredEvidence"].pop(), "MPV2.BINDING.ACTIVATION_PATH_INVALID"),
        (lambda value: value["prohibitedClaims"].pop(), "MPV2.BINDING.PROHIBITED_CLAIMS_INVALID"),
    ],
)
def test_binding_authority_mutations_fail_closed(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.BINDING_PATH, mutate)
    assert expected in program.validate_repository(root, certification=False)


def test_review_surface_replacement_breaks_exact_binding(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    path = root / program.REVIEW_PATHS[1]
    path.write_text("PASS; provider and spend authorized.\n", encoding="utf-8")
    assert "MPV2.REVIEW.HASH_MISMATCH" in program.validate_repository(
        root, certification=False
    )


def test_current_mapping_serialization_preserves_clause_without_detector_text() -> None:
    raw = (REPO / program.MAPPING_PATH).read_bytes()
    assert b"credential exposure, duplicate/sybil" not in raw
    mapping = json.loads(raw)
    rows = [
        row
        for row in mapping["rows"]
        if row["sourceClauseSha256"]
        == "845855204badc3593c9f4e729d2395d4c443ab2f83771cb1731f7a560f3089c1"
    ]
    assert len(rows) == 1
    assert (
        hashlib.sha256(rows[0]["normalizedAtomicRequirement"].encode()).hexdigest()
        == "845855204badc3593c9f4e729d2395d4c443ab2f83771cb1731f7a560f3089c1"
    )


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


def test_mapping_cannot_self_certify_or_change_destination(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)

    def mutate(value: dict[str, Any]) -> None:
        value["certification"] = {
            "structuralResult": "PASS",
            "semanticReview": "PASS",
            "ownerExactBytesApproval": "PASS",
            "eligibleNonAuthorExactHead": "PASS",
            "activation": "ACCEPTED_CURRENT",
        }
        for row in value["rows"]:
            row["result"] = "PASS"
            row["v2DestinationClause"] = "## 12. Stop conditions, assumptions, and completion claim"

    _rewrite_json(root, program.MAPPING_PATH, mutate)
    failures = program.validate_repository(root, certification=False)
    assert "MPV2.SOURCE.MAPPING_HASH_DRIFT" in failures
    assert "MPV2.MAPPING.CERTIFICATION_STATE_INVALID" in failures
    assert "MPV2.MAPPING.DESTINATION_INVALID" in failures


def test_mapping_source_inventory_is_frozen_to_authoritative_sources(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)

    def mutate(value: dict[str, Any]) -> None:
        value["sources"] = [source for source in value["sources"] if source["sourceId"] != "TTS_PROVIDER_CODE"]

    _rewrite_json(root, program.MAPPING_PATH, mutate)
    failures = program.validate_repository(root, certification=False)
    assert "MPV2.SOURCE.MAPPING_HASH_DRIFT" in failures
    assert "MPV2.MAPPING.SOURCE_INVENTORY_INVALID" in failures


def test_taxonomy_hash_and_semantics_cannot_be_rewritten_together(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)

    def mutate(value: dict[str, Any]) -> None:
        value["cuts"] = [cut for cut in value["cuts"] if cut["id"] != "Cut4"]
        value["cuts"][0]["dependencies"] = []
        value["legacyAliases"][0]["canonicalCut"] = "Cut5"

    _rewrite_json(root, program.TAXONOMY_PATH, mutate)
    failures = program.validate_repository(root, certification=False)
    assert "MPV2.SOURCE.TAXONOMY_HASH_DRIFT" in failures
    assert "MPV2.TAXONOMY.LEGACY_CUT5_TARGET_INVALID" in failures


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
    assert len(preflight["scope"]["required"]) == 27
    assert preflight["scope"]["required"] == preflight["scope"]["allowed_prefixes"]
    assert "AGENTS.md" in preflight["scope"]["forbidden"]
    assert "owner checkpoint 5574559059" in preflight["objective"]
    assert "72a3144b556c93b09678eaa7cfa495cfc3ff8cc981f50f86b4cbe64a1e2d217f" in preflight["objective"]
    assert {
        ".gitleaksignore",
        "scripts/ci/check_gitleaks_regression.py",
        "tests/unit/test_gitleaks_regression.py",
    }.issubset(preflight["scope"]["required"])
