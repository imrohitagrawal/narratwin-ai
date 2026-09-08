from __future__ import annotations
import copy
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Callable
import pytest
from scripts.quality import issue521_master_program_v2 as program

REPO = Path(__file__).resolve().parents[2]

def _copy_candidate(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / ".git", root / ".git")
    paths = {*program.REQUIRED_ARTIFACTS, program.V1_PATH}
    for relative in sorted(paths):
        source = REPO / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return root

def _rewrite_json(root: Path, relative: str, mutate: Callable[[dict[str, Any]], None]) -> None:
    path = root / relative
    value = program._load_json_text(path.read_text(encoding="utf-8"))
    if relative == program.MAPPING_PATH:
        value = program.decode_mapping_artifact(value)
    mutate(value)
    if relative == program.MAPPING_PATH and isinstance(value.get("rows"), list):
        for row in value["rows"]:
            row["thresholdComparison"] = program._derived_threshold_comparison(row)
    rendered = (
        program.render_mapping(value)
        if relative == program.MAPPING_PATH
        else json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    )
    path.write_text(rendered, encoding="utf-8")

def _rewrite_mapping_artifact(
    root: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    path = root / program.MAPPING_PATH
    artifact = program._load_json(path)
    mutate(artifact)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )

def _row_text(row: dict[str, Any]) -> str:
    return program.decode_requirement(row["normalizedAtomicRequirement"])

def _read_mapping(root: Path = REPO) -> dict[str, Any]:
    artifact = program._load_json(root / program.MAPPING_PATH)
    return program.decode_mapping_artifact(artifact)
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
def test_unavailable_repository_commit_never_falls_back_to_worktree_bytes() -> None:
    source = {
        "sourceKind": "REPOSITORY_FILE",
        "repositoryPath": program.V1_PATH,
        "sourceCommit": "f" * 40,
    }
    assert (REPO / program.V1_PATH).is_file()
    with pytest.raises(ValueError, match="frozen repository source unavailable"):
        program.frozen_source_bytes(REPO, source)
    source["sourceCommit"] = "not-a-commit"
    with pytest.raises(ValueError, match="repository source commit invalid"):
        program.frozen_source_bytes(REPO, source)
def test_mapping_with_unavailable_source_object_reports_failure(
    tmp_path: Path,
) -> None:
    root = _copy_candidate(tmp_path)
    mapping = program.generate_mapping(REPO)
    source = next(
        item
        for item in mapping["sources"]
        if item["sourceKind"] == "REPOSITORY_FILE"
    )
    source["sourceCommit"] = "f" * 40
    document = (root / program.DOCUMENT_PATH).read_text(encoding="utf-8")
    assert "MPV2.SOURCE.MISSING" in program._mapping_failures(
        root, mapping, document
    )
def test_unadopted_candidate_cannot_authenticate_itself_as_owner_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(program, "OWNER_PLAN_ADOPTION_COMMENT_ID", 0)
    monkeypatch.setattr(
        program, "OWNER_PLAN_ADOPTION_BODY_SHA256", "PENDING_OWNER_ADOPTION"
    )
    monkeypatch.setattr(
        program, "OWNER_PLAN_ADOPTION_DOCUMENT_SHA256", "PENDING_OWNER_ADOPTION"
    )
    mapping = program.generate_mapping(REPO)
    owner_source = mapping["sources"][0]
    assert owner_source["sourceId"] == "OWNER_PLAN_2026_09_07"
    assert owner_source["sourceKind"] == "OWNER_PLAN_CANDIDATE"
    assert owner_source["sourceCommit"] is None
    assert owner_source["authorityRefs"] == ["OWNER_PLAN_ADOPTION_PENDING"]
    assert mapping["ownerAuthority"] == "OWNER_PLAN_ADOPTION_PENDING"
    assert "OWNER_DIRECTIVE" not in json.dumps(mapping)
def test_frozen_inventory_has_exact_source_coverage_and_lifecycles() -> None:
    sources = program._source_records(REPO)
    owner = [source for source in sources if source["sourceKind"] != "REPOSITORY_FILE"]
    repository = [source for source in sources if source["sourceKind"] == "REPOSITORY_FILE"]
    assert len(owner) == 1
    assert owner[0]["sourceId"] == "OWNER_PLAN_2026_09_07"
    assert owner[0]["authorityLifecycle"] == "OWNER_CANDIDATE"
    assert owner[0]["coverageStatus"] == "PENDING_EXTERNAL_ATTESTATION"
    assert len(repository) == 192
    assert {
        mode: sum(source["coverageMode"] == mode for source in repository)
        for mode in ("ATOMIC_MARKDOWN", "STRUCTURED_SCHEMA", "IMPLEMENTED_CODE", "MANIFEST_ONLY")
    } == {
        "ATOMIC_MARKDOWN": 90,
        "STRUCTURED_SCHEMA": 26,
        "IMPLEMENTED_CODE": 21,
        "MANIFEST_ONLY": 55,
    }
    assert len({source["sourceId"] for source in sources}) == 193
    assert len({source["repositoryPath"] for source in repository}) == 192
    assert all(source["sourceCommit"] == program.BASE_SHA for source in repository)
def test_mapping_artifact_round_trips_indexed_rows_below_github_warning_limit() -> None:
    logical = program.generate_mapping(REPO)
    rendered = program.render_mapping(logical).encode("utf-8")
    artifact = program._load_json_text(rendered.decode("utf-8"))
    assert len(rendered) < 50 * 1024 * 1024
    assert artifact["rowEncoding"]["kind"] == (
        "INDEXED_VALUE_TABLE_WITH_COMMITTED_DERIVED_THRESHOLD_V2"
    )
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        artifact["rowEncoding"]["derivedThresholdComparisonsSha256"],
    )
    assert artifact["rowEncoding"]["columns"] == list(program.STORED_ROW_COLUMNS)
    assert len(artifact["rows"]) == len(logical["rows"])
    assert program.decode_mapping_artifact(artifact) == logical
def test_mapping_artifact_commits_derived_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = program._load_json(REPO / program.MAPPING_PATH)
    monkeypatch.setattr(program, "expected_comparison_basis", lambda row: "WEAKENED")
    with pytest.raises(ValueError, match="derived threshold digest invalid"):
        program.decode_mapping_artifact(artifact)
def test_all_adrs_are_inventoried_with_duplicate_numbers_bound_by_path_and_blob() -> None:
    adrs = [
        source
        for source in program._source_records(REPO)
        if source["repositoryPath"].startswith("docs/ADR/")
    ]
    assert len(adrs) == 86
    assert sum(Path(source["repositoryPath"]).name.startswith("0001-") for source in adrs) == 2
    assert sum(Path(source["repositoryPath"]).name.startswith("0002-") for source in adrs) == 2
    assert sum(Path(source["repositoryPath"]).name.startswith("0003-") for source in adrs) == 2
    assert len({source["sourceId"] for source in adrs}) == 86
    assert len({(source["repositoryPath"], source["sourceGitBlob"]) for source in adrs}) == 86
    assert {
        source["coverageMode"] for source in adrs
    } == {"ATOMIC_MARKDOWN", "MANIFEST_ONLY"}
def test_manifest_only_sources_emit_no_requirement_rows() -> None:
    sources = program._source_records(REPO)
    manifest = [source for source in sources if source["coverageMode"] == "MANIFEST_ONLY"]
    assert manifest
    assert all(
        source["semanticCoverage"]["candidateUnitCount"] == 0
        and source["semanticCoverage"]["normativeRequirementCount"] == 0
        and source["semanticCoverage"]["excludedUnitCount"] == 0
        for source in manifest
    )
    assert all(
        program._atoms(
            source["sourceId"],
            source["atomizer"],
            program.frozen_source_bytes(REPO, source),
        )
        == []
        for source in manifest
    )
def test_structured_atomizer_distinguishes_constraints_and_instance_facts() -> None:
    schema = '{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Fixture","properties":{"name":{"type":"string","minLength":1}}}'
    atoms = program._json_pointer_atomizer("FIXTURE", schema)
    assert any("::INSTANCE_FACT:" in atom.anchor and '"Fixture"' == atom.text for atom in atoms)
    assert any("::SCHEMA_CONSTRAINT:" in atom.anchor and '"string"' == atom.text for atom in atoms)
    assert all(atom.atom_id.startswith("atom:") for atom in atoms)
    with pytest.raises(program.DuplicateJsonMember):
        program._json_pointer_atomizer("FIXTURE", '{"same":1,"same":2}')
def test_tree_inventory_is_sorted_digest_bound_and_mutation_detectable() -> None:
    tree = next(
        source
        for source in program._source_records(REPO)
        if source["repositoryPath"] == "docs/governance/preflights"
    )
    paths = [entry["repositoryPath"] for entry in tree["treeEntries"]]
    assert tree["objectKind"] == "GIT_TREE"
    assert paths == sorted(paths)
    assert tree["treeManifestSha256"] == hashlib.sha256(
        program._canonical_json(tree["treeEntries"]).encode("utf-8")
    ).hexdigest()
    mutated = copy.deepcopy(tree)
    mutated["treeEntries"][0]["objectId"] = "f" * 40
    assert hashlib.sha256(
        program._canonical_json(mutated["treeEntries"]).encode("utf-8")
    ).hexdigest() != mutated["treeManifestSha256"]
    assert "github-comment:5469182822" in tree["authorityRefs"]
def test_mapping_rows_are_exactly_repository_current_and_external_normative() -> None:
    mapping = _read_mapping()
    candidates = program.expected_source_atoms(REPO, mapping)
    expected_repository = program.expected_normative_atoms(REPO)
    expected_external = program._external_new_atoms(
        mapping["externalAuthorityManifest"]
    )
    expected = expected_repository | expected_external
    actual = [row["sourceAtomId"] for row in mapping["rows"]]
    assert len(actual) == len(set(actual)) == len(expected)
    assert set(actual) == set(expected)
    assert set(expected_repository) < set(candidates)
    assert all(
        source["semanticCoverage"]["candidateUnitCount"]
        == source["semanticCoverage"]["normativeRequirementCount"]
        + source["semanticCoverage"]["excludedUnitCount"]
        == sum(source["semanticCoverage"]["classCounts"].values())
        for source in mapping["sources"]
    )
def test_repeated_semantic_signatures_have_an_exact_pending_resolution_census(
    tmp_path: Path,
) -> None:
    mapping = program.generate_mapping(REPO)
    census = mapping["semanticDuplicateCensus"]
    assert census["groupCount"] == len(census["groups"]) > 0
    assert census["occurrenceCount"] == sum(len(group["members"]) for group in census["groups"])
    assert census["excessOccurrenceCount"] == census["occurrenceCount"] - census["groupCount"]
    assert all(
        len(group["members"]) >= 2
        and all(set(member) == {"sourceAtomId", "contextChainSha256"} and re.fullmatch(r"[0-9a-f]{64}", member["contextChainSha256"]) for member in group["members"])
        for group in census["groups"]
    )
    ai_source_id = "SOURCE_AI_SAFETY_AND_EVALUATION_93B2F6C5"
    member_hashes = {member["sourceAtomId"]: member["contextChainSha256"] for group in census["groups"] for member in group["members"]}
    scoped = [row for row in mapping["rows"] if row["sourceId"] == ai_source_id and row["sourceSpan"]["startLine"] in {257, 273}]
    assert len(scoped) == 2 and len({member_hashes[row["sourceAtomId"]] for row in scoped}) == 2
    assert census["resolutionOverlay"]["censusSha256"] == census["orderedGroupSha256"]
    root = _copy_candidate(tmp_path)
    _rewrite_json(
        root,
        program.MAPPING_PATH,
        lambda value: value["semanticDuplicateCensus"]["groups"][0]["members"][0].update({"contextChainSha256": "0" * 64}),
    )
    assert "MPV2.MAPPING.DUPLICATE_CENSUS_INVALID" in program.validate_repository(
        root, certification=False
    )
def test_external_authority_is_classified_atomized_and_never_emits_raw_bodies() -> None:
    mapping = _read_mapping()
    manifest = mapping["externalAuthorityManifest"]
    records = manifest["records"]
    assert manifest["closure"] == "CLASSIFIED_AND_ATOMIZED"
    assert manifest["referenceCount"] == manifest["recordCount"] == 605
    assert len(records) == len({record["reference"] for record in records}) == 605
    assert "github-issue:999" not in {record["reference"] for record in records}
    assert {record["sourceKind"] for record in records} == {
        "EXTERNAL_GITHUB_COMMENT",
        "EXTERNAL_GITHUB_ISSUE_BODY",
        "EXTERNAL_GITHUB_PULL_REQUEST_BODY",
    }
    assert all(
        record["contentAddressedRef"]
        == f"{record['reference']}@sha256:{record['contentSha256']}"
        and record["cutoffEligible"] is True
        and "body" not in record
        and record["authorityEffect"] != "PENDING_INDEPENDENT_CLASSIFICATION"
        for record in records
    )
    clauses = [clause for record in records for clause in record["clauses"]]
    assert clauses and len(clauses) == len({clause["clauseId"] for clause in clauses})
    row_by_atom = {row["sourceAtomId"]: row for row in mapping["rows"]}
    for record in records:
        for clause in record["clauses"]:
            alias = clause["suggestedAlias"]
            if isinstance(alias, dict) and alias.get("kind") == "EXISTING_REQUIREMENT":
                assert alias["equivalentCandidateCount"] == 1
                assert alias["matchBasis"] == "EXACT_CANONICAL_ATOMIC_FOCUS_AND_CONTEXT_AND_SCOPE"
                assert alias["sourceAtomId"] in row_by_atom
                candidates = [row for row in mapping["rows"] if not row["sourceKind"].startswith("EXTERNAL_") and row["atomicFocusSha256"] == clause["atomicFocusSha256"] and row["normalizedSourceContextSha256"] == clause["normalizedSourceContextSha256"]]
                assert candidates == [row_by_atom[alias["sourceAtomId"]]]
                assert record["contentAddressedRef"] in row_by_atom[
                    alias["sourceAtomId"]
                ]["sourceAuthorityRefs"]
            else:
                atom = program._external_clause_atom(record, clause)
                assert atom.atom_id in row_by_atom
    reclassified = [row for row in mapping["rows"] if row["requirementId"] in {"MPV2-EBF89EEC9E95E26A0F9D", "MPV2-0E3D0BD726CBD0E008BB", "MPV2-AA474AFCF10BF9049EDF", "MPV2-4902F39C170E14867575"}]
    assert (len(reclassified), {row["v2DestinationClause"] for row in reclassified}) == (4, {"MPV2-SECTION-10"})
    assert not program._external_authority_failures(mapping["sources"], manifest)
    mutated = copy.deepcopy(manifest)
    normative = next(record for record in mutated["records"] if record["clauses"])
    normative["clauses"][0]["atomicFocusEnd"] -= 1
    assert program._external_authority_failures(mapping["sources"], mutated)
    normative["clauses"][0]["atomicFocusEnd"] += 1
    normative["clauses"][0]["losslessNormalizationAttestation"] = {}
    assert program._external_classification_invalid(normative)
    for mutate in (
        lambda value: value["sanitization"].update({"redactionClasses": [[]]}),
        lambda value: value["semanticCoverage"].update(
            {"orderedCandidatePartitionSha256": []}
        ),
        lambda value: value["clauses"][0]["sourceSpan"].update(
            {"sanitizedSpanSha256": []}
        ),
    ):
        malformed = copy.deepcopy(next(record for record in records if record["clauses"]))
        mutate(malformed)
        assert program._external_classification_invalid(malformed)
def test_comment_governing_context_partition_is_complete_and_alias_safe() -> None:
    mapping = _read_mapping()
    manifest = mapping["externalAuthorityManifest"]
    partition = manifest["governingContextDecisionPartition"]
    assert program.EXTERNAL_CLASSIFICATION_PRECEDENCE_INPUT_SHA256 != program.DOCUMENT_SHA256
    for key, value in (("semanticPrecedenceInputRole", "WRONG"), ("semanticPrecedenceInputSha256", program.DOCUMENT_SHA256), ("semanticPrecedenceInputActivation", "ACTIVE")):
        mutated = copy.deepcopy(partition)
        next(item for item in mutated["parents"] if item["parentDisposition"] == "GOVERNING_INTRODUCER")[key] = value
        assert program._external_governing_context_bindings_invalid(manifest["records"], mutated)
    assert partition["schemaVersion"] == "CommentGoverningContextDecisionPartitionV1"
    assert (partition["parentCount"], partition["relationCount"], partition["uniqueChildCount"]) == (136, 814, 792)
    assert tuple(len(partition[key]) for key in ("parents", "relations", "childDecisions", "resolvedExactContextSuccessions")) == (136, 814, 792, 5)
    assert partition["contextSuccessionKindCounts"] == {"GOVERNING_CONTEXT_TO_GOVERNING_CONTEXT": 2, "GOVERNING_CONTEXT_TO_NORMATIVE_CLAUSE": 2, "NORMATIVE_CLAUSE_TO_GOVERNING_CONTEXT": 1}
    assert all(
        "GOVERNING_CONTEXT" in item["successionKind"]
        for item in partition["resolvedExactContextSuccessions"]
    )
    identities = [
        {
            "parentReference": relation["parentReference"],
            "parentCandidateUnitId": relation["parentCandidateUnitId"],
            "parentAtomicFocusSha256": relation["parentAtomicFocusSha256"],
            "childCandidateUnitId": relation["childCandidateUnitId"],
            "childAtomicFocusSha256": relation["childAtomicFocusSha256"],
        }
        for relation in partition["relations"]
    ]
    identities.sort(key=lambda item: tuple(item[key] for key in item))
    identity_sha256 = hashlib.sha256(program._canonical_json(identities).encode()).hexdigest()
    assert identity_sha256 == partition["orderedRelationIdentitySha256"]
    assert identity_sha256 == "e610c9852d8cea82e0f17d2b7b81626c5f166ff73b59736e78fe0b0bcd138600"
    assert partition["operatorCodeOrderSha256"] == hashlib.sha256(program._canonical_json(partition["operatorCodeOrder"]).encode()).hexdigest()
    assert partition["promotionSyntacticTypeCounts"] == {"PURE_DIGEST": 5, "PURE_PATH": 144}
    assert partition["orderedPromotedChildIdentitySha256"] == "52ff95cad9ca85a7f949ac6e123fb60dea2a4237eb61540e00e5f72a401193a0"
    assert partition["orderedPromotionDecisionSha256"] == "561eb9ad48ceb316e5fc2a925d0b074d530054d56ed08c602b3d170a6e41c63b"
    assert partition["parentFocusPrivacyCounts"] == {"emitted": 103, "withheld": 33}
    assert partition["contextSuccessionLeafDispositionCounts"] == {"INDEPENDENT_CURRENT_AUTHORITY": 1, "REMOVED_MEMBER_SUPERSEDED": 7, "RETAINED_MEMBER_OF_SUPERSEDING_SET": 15}
    assert partition["contextSuccessionLeafProofKindCounts"] == {"EXACT_LATER_CURRENT_AUTHORITY": 1, "EXACT_PREDECESSOR_MEMBER_RETAINED_BY_SUCCESSOR_SET_REFERENCE": 12, "EXACT_SUCCESSOR_CANDIDATE_MEMBER": 3}
    assert partition["orderedContextSuccessionLeafSemanticSha256"] == "7415ced2e067b6c2fd147f8b452f3b6474519421ff4c7aaa4a0acdacf80385d8"
    children = {item["childDecisionId"]: item for item in partition["childDecisions"]}
    promoted = [item for item in children.values() if item["inheritanceDisposition"] == "INHERITED_CURRENT_NORMATIVE"]
    assert partition["promotionCount"] == len(promoted) == 149
    assert {item["originalSemanticClass"] for item in promoted} == {"REFERENCE"}
    assert sum(item["originalSemanticClass"] == "REFERENCE" and item not in promoted for item in children.values()) == 14
    parents = {item["parentId"]: item for item in partition["parents"]}
    assert all(
        parents[item["parentId"]]["parentDisposition"] == "GOVERNING_INTRODUCER"
        for item in partition["relations"]
        if item["relationEffect"] == "GOVERNING_CONTEXT_PROMOTES_CHILD"
    )
    for record in manifest["records"]:
        for clause in record["clauses"]:
            reference = clause["governingContextDecisionRef"]
            if reference is None:
                continue
            assert clause["suggestedAlias"] == "NEW_ROW_REQUIRED"
            child = children[reference["childDecisionId"]]
            assert child["childDecisionSha256"] == reference["childDecisionSha256"]
    assert not program._external_governing_context_bindings_invalid(
        manifest["records"], partition
    )
    mutated_records = copy.deepcopy(manifest["records"])
    referenced = [
        clause
        for record in mutated_records
        for clause in record["clauses"]
        if clause["governingContextDecisionRef"] is not None
    ]
    referenced[0]["governingContextDecisionRef"] = copy.deepcopy(
        referenced[1]["governingContextDecisionRef"]
    )
    assert program._external_governing_context_bindings_invalid(
        mutated_records, partition
    )
    mutated_partition = copy.deepcopy(partition)
    mutated_partition["relations"][0]["childDecisionId"] = partition[
        "childDecisions"
    ][1]["childDecisionId"]
    assert program._external_governing_context_bindings_invalid(
        manifest["records"], mutated_partition
    )
    linked = [row for row in mapping["rows"] if row["atomicFocusSha256"] == "4738db38877a3fa143ee233b7984a3a9c5f4be7160a4eb0d26e8ea1b85d2eb66"]
    assert {row["sourceId"] for row in linked} == {"EXTERNAL_GITHUB_COMMENT_5485702633", "EXTERNAL_GITHUB_COMMENT_5495025249"}
    assert len({row["v2DestinationClause"] for row in linked}) == 1
    linked_atoms = {row["sourceAtomId"] for row in linked}
    assert sum(linked_atoms <= {member["sourceAtomId"] for member in group["members"]} for group in mapping["semanticDuplicateCensus"]["groups"]) == 1
def test_known_evidence_and_implementation_units_never_become_requirement_rows() -> None:
    rows = _read_mapping()["rows"]
    rendered = [program.decode_requirement(row["normalizedAtomicRequirement"]) for row in rows]
    assert not any("No product requirement" in value for value in rendered)
    assert not any("head_commit = event.get" in value for value in rendered)
    assert not any(row["semanticClass"] != "NORMATIVE_REQUIREMENT" for row in rows)
    assert not any(
        row["sourceId"] in {"AVATAR_PROVIDER_CODE", "TTS_PROVIDER_CODE"}
        for row in rows
    )
    assert {row["requirementId"] for row in rows if re.search(r":(?:Result|Status|Issue / PR):U[0-9]+$", row["sourceAnchor"])} == set("MPV2-D80D334B6E1FE62B143E MPV2-54D345526A13122829CA MPV2-9E3D610A9DA1FF615A61 MPV2-4B35D3CF4DE66C97FDD8 MPV2-A2C0B967DEF17FCFC4FB MPV2-EE837085B3B6AABBE786 MPV2-604FB24C5EABB10724BE MPV2-835D9BA34A269FB66C1E MPV2-57ACE808FC2EBF309DF2 MPV2-D57131E71C25196FF8C9 MPV2-EEE85E1FA9595BF8AA79 MPV2-36918597D1DB3012C4E6 MPV2-B9916D1EF66797F821BA MPV2-D3D7DB40B5727D5C8070".split())
    assert not any(
            _row_text(row).strip() in {"Fields:", "Positive:", "Controls:", "Negative:", "Indexes:", "Attack:", "N/A"}
            or "## Related Documents" in row["sourceAnchor"]
            or "## Version" in row["sourceAnchor"] and row["requirementId"] != "MPV2-D4C6D50703909651C2DC"
        for row in rows
    )
    assert {
        ("EXTERNAL_GITHUB_COMMENT_4968602415", "#142-#149 must retain explicit dependency and acceptance contracts"),
        ("EXTERNAL_GITHUB_COMMENT_5197776590", "final merge text and eligible latest-head approval remain human-only."),
        ("EXTERNAL_GITHUB_COMMENT_5207065123", "Permitted-use decision is narrow: repository-controlled local Cut 1 review only, with visible fictional/synthetic disclosure."),
    } <= {(row["sourceId"], _row_text(row).strip()) for row in rows}
    assert any(
        _row_text(row).strip() == "Rejected."
        and "Alternatives" in row["sourceAnchor"]
        for row in rows
    )
def test_markdown_atomizer_is_clause_atomic_and_keeps_full_heading_context() -> None:
    source = "# Root\n## 5. Parent contract\n### Child contract\nThe service must preserve A; it must preserve B. It must preserve C.\n- `contract.md` — Meera primary, Raj first backup, human review, and provenance.\n| Item | Requirement | Result |\n|---|---|---|\n| First | The first row must not disappear. | PASS |\n| Second | The second row must remain. | PASS |"
    atoms = program._markdown_atoms("FIXTURE", source)
    texts = [atom.text for atom in atoms]
    assert "The service must preserve A" in texts
    assert "it must preserve B." in texts
    assert "It must preserve C." in texts
    assert any("## 5. Parent contract > ### Child contract" in atom.anchor for atom in atoms)
    assert any(
        "Item=First" in atom.anchor
        and atom.text == "The first row must not disappear."
        and atom.source_clause
        == "Item=First | Requirement=The first row must not disappear. | Result=PASS"
        for atom in atoms
    )
    descriptor = next(atom for atom in atoms if atom.text.startswith("Meera primary"))
    assert descriptor.text == "Meera primary, Raj first backup, human review, and provenance."
    assert descriptor.source_clause == (
        "- `contract.md` — Meera primary, Raj first backup, human review, and provenance."
    )
    assert not any("preserve A" in atom.text and "preserve B" in atom.text for atom in atoms)
    assert not any(re.search(r":Item:U[0-9]+$", atom.anchor) for atom in atoms)
def test_semantic_first_table_columns_have_exact_frozen_coverage() -> None:
    sources = program._source_records(REPO)
    lifecycle = {source["sourceId"]: source["authorityLifecycle"] for source in sources}
    selected = []
    pattern = re.compile(
        r"::table:L[0-9]+:(?:Requirement|Requirement/decision)=.*:"
        r"(?:Requirement|Requirement/decision):U[0-9]+$"
    )
    for source in sources:
        selected.extend(
            atom
            for atom in program._atoms(
                source["sourceId"], source["atomizer"],
                program.frozen_source_bytes(REPO, source),
            )
            if pattern.search(atom.anchor)
        )
    projection = [
        {
            "sourceId": atom.source_id,
            "line": atom.source_span_start_line,
            "requirementId": atom.requirement_id,
            "sourceContextSha256": atom.source_context_sha256,
            "atomicFocusSha256": atom.clause_sha256,
            "focusStart": atom.focus_start,
            "focusEnd": atom.resolved_focus_end,
        }
        for atom in selected
    ]
    assert len(selected) == 164
    assert program._sha256(program._canonical_json(projection).encode()) == (
        "cd15f0db592734417b01d58b3dc0050730e30d256118f34a588a9136b9fcded1"
    )
    assert all(
        program._semantic_class(atom, lifecycle[atom.source_id])
        == "NORMATIVE_REQUIREMENT"
        for atom in selected
    )
def test_reviewed_semantic_sets_and_changelogs_have_effective_classes() -> None:
    sources = {item["sourceId"]: item for item in program._source_records(REPO)}
    atoms_by_source = {source_id: program._atoms(source_id, source["atomizer"], program.frozen_source_bytes(REPO, source)) for source_id, source in sources.items()}
    classes: dict[str, set[str]] = {}
    for source_id, atoms in atoms_by_source.items():
        for atom in atoms:
            classes.setdefault(atom.requirement_id, set()).add(program._semantic_class(atom, sources[source_id]["authorityLifecycle"]))
    groups = {"NORMATIVE_REQUIREMENT": program._REVIEWED_NORMATIVE_REQUIREMENT_IDS, "CURRENT_STATE_FACT": program._REVIEWED_CURRENT_STATE_IDS, "HISTORICAL_FACT": program._REVIEWED_HISTORICAL_IDS, "AUTOMATED_RESULT": program._REVIEWED_AUTOMATED_IDS, "IMPLEMENTED_BEHAVIOR": program._REVIEWED_IMPLEMENTED_IDS}
    reviewed = set().union(*groups.values())
    assert len(reviewed) == sum(map(len, groups.values()))
    assert reviewed <= classes.keys()
    assert all(classes[item] == {expected} for expected, ids in groups.items() for item in ids)
    for source_id, expected_count in (("STATUS", 345), ("SOURCE_TRACEABILITY_7B284BCF", 271)):
        atoms = [atom for atom in atoms_by_source[source_id] if "## Change Log" in atom.anchor]
        assert (len(atoms), {program._semantic_class(atom, sources[source_id]["authorityLifecycle"]) for atom in atoms}) == (expected_count, {"HISTORICAL_FACT"})
def test_clause_atomizer_switches_modal_predicates_without_inverting_prohibitions() -> None:
    source = (
        "It must keep issues #249/#280 open, must use reference-only wording, "
        "and must not authorize provider setup, provider SDKs, provider keys, "
        "real provider calls, or paid spend."
    )
    assert program._clause_units(source) == [source]
    mapping = program.generate_mapping(REPO)
    stage_rows = [
        _row_text(row)
        for row in mapping["rows"]
        if row["sourceId"] == "STAGE_ISSUE_PLAN"
    ]
    assert not any("must keep must" in row for row in stage_rows)
    assert not any(row in {"provider SDKs", "provider keys", "paid spend"} for row in stage_rows)
    stage_atoms = program._markdown_atoms(
        "STAGE_ISSUE_PLAN",
        program.frozen_source_bytes(
            REPO,
            {
                "repositoryPath": "docs/STAGE_ISSUE_PLAN.md",
                "sourceCommit": program.BASE_SHA,
            },
        ).decode("utf-8"),
    )
    provider_sdk = next(
        atom
        for atom in stage_atoms
        if "provider SDKs" in atom.text and ":L1482:" in atom.anchor
    )
    assert "must not authorize provider setup, provider SDKs" in provider_sdk.source_clause
    assert (
        provider_sdk.source_clause[
            provider_sdk.focus_start : provider_sdk.resolved_focus_end
        ]
        == provider_sdk.text
    )
def test_v1_compound_safety_clauses_preserve_each_evolving_predicate() -> None:
    v1 = program.frozen_source_bytes(
        REPO,
        {"repositoryPath": program.V1_PATH, "sourceCommit": program.BASE_SHA},
    ).decode("utf-8")
    atoms = program._markdown_atoms("MASTER_PROGRAM_V1", v1)
    billable = {
        atom.text for atom in atoms if "## 27. PaidOperationV1::prose:L616:" in atom.anchor
    }
    captions = {
        atom.text for atom in atoms if "## 31. Captions::prose:L675:" in atom.anchor
    }
    assert {
        "`BILLABLE_UNKNOWN` retains reservation",
        "prohibits retry/fallback/reroll/ duplicate create",
        "reconciles via signed webhook, polling, or manual provider evidence",
        "never treats requested refund as completed",
        "blocks dispatch when worst-case exposure exceeds authority.",
    } <= billable
    assert any(
        text.startswith("Cues are monotonic, nonoverlapping")
        and "obey readable line limits" in text
        for text in captions
    )
    assert not any(
        fragment in atom.text
        for atom in atoms
        for fragment in (
            "retains prohibits",
            "retains reconciles",
            "retains never treats",
            "retains blocks",
            "contain keep",
            "contain obey",
        )
    )
    for atom in atoms:
        if ":L616:" in atom.anchor or ":L675:" in atom.anchor:
            assert atom.source_clause[
                atom.focus_start : atom.resolved_focus_end
            ] == atom.text
    assert not any(
        re.fullmatch(r"(?:[-*+]|\d+[.)])", atom.text.strip())
        for atom in atoms
    )
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
    assert "control-path finally: self._semaphore.release()" in avatar
    assert "if error.retryable and attempt < attempts: continue" in avatar
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
    assert "control-path finally: self._semaphore.release()" in tts
    assert "if attempt < attempts: continue" in tts
def test_meera_duration_and_sibling_audio_requirements_remain_preserved() -> None:
    mapping = program.generate_mapping(REPO)
    duration_rows = [
        row
        for row in mapping["rows"]
        if row["sourceId"] == "MASTER_PROGRAM_V1"
        and "90.000–120.000 seconds" in row["normalizedAtomicRequirement"]
    ]
    assert len(duration_rows) == 1
    assert duration_rows[0]["disposition"] == "PRESERVED"
    assert duration_rows[0]["v2DestinationClause"] == "MPV2-CUT1-MEERA-CELL"
    assert "RIFF/WAVE" not in duration_rows[0]["normalizedAtomicRequirement"]
    assert "owner listening approval" not in duration_rows[0]["normalizedAtomicRequirement"]
    sibling_rows = [row for row in mapping["rows"] if row["sourceId"] == "MASTER_PROGRAM_V1" and any(phrase in row["normalizedAtomicRequirement"] for phrase in ("RIFF/WAVE", "owner listening approval"))]
    assert sibling_rows
    assert all(row["disposition"] == "PRESERVED" for row in sibling_rows)
def test_parenthetical_rule_does_not_absorb_following_historical_fact() -> None:
    context = (
        "Historical evidence only (superseded after merge; its current-stage "
        "restrictions remain binding where applicable): Issue `#1` merged."
    )
    units = program._contextual_clause_units(context)
    assert [unit.atomic_focus for unit in units] == [
        "Historical evidence only (superseded after merge",
        "its current-stage restrictions remain binding where applicable",
        "Issue `#1` merged.",
    ]
    assert all(
        context[unit.focus_start : unit.focus_end] == unit.atomic_focus
        for unit in units
    )
def test_table_atoms_bind_every_focus_to_the_complete_normalized_row() -> None:
    rows = program.generate_mapping(REPO)["rows"]
    wav2lip = [
        row
        for row in rows
        if row["sourceId"] == "REAL_MEDIA_HOSTED_DEMO_PLAN"
        and "Candidate=Wav2Lip" in program.decode_requirement(
            row["normalizedSourceContext"]
        )
        and "Official source=" in program.decode_requirement(
            row["normalizedSourceContext"]
        )
    ]
    assert wav2lip
    for row in wav2lip:
        context = program.decode_requirement(row["normalizedSourceContext"])
        assert "Current planning posture=rejected" in context
        assert row["governingContext"]["kind"] == (
            "FULL_NORMALIZED_TABLE_ROW_CONTEXT"
        )
        assert row["governingContext"]["normalization"] == (
            "MARKDOWN_TABLE_HEADER_VALUE_V1"
        )
def test_semantic_effect_and_legacy_conflicts_fail_closed() -> None:
    mapping = program.generate_mapping(REPO)
    rows = mapping["rows"]
    sources = {source["sourceId"]: source for source in mapping["sources"]}
    def classes(source_id: str, context_hash: str) -> set[str]:
        source = sources[source_id]
        atoms = program._atoms(
            source_id, source["atomizer"], program.frozen_source_bytes(REPO, source)
        )
        selected = [
            atom for atom in atoms if atom.source_context_sha256 == context_hash
        ]
        assert selected, (source_id, context_hash)
        return {
            program._semantic_class(atom, source["authorityLifecycle"])
            for atom in selected
        }
    assert classes(
        "OWNER_PLAN_2026_09_07",
        "f5ca0d433c93227a65d0ffab36aed88ba53ab8888fa3cb2f2992030a97082ad0",
    ) == {"NORMATIVE_REQUIREMENT"}
    for context_hash in (
        "af6ab6864870881c6d3426584d29cb2b8fd5d1f7316cc49fe9ccc17018b727f2",
        "aa4ad2aeee38886b9116108f3a29e2ef2cfd3c68b8dda360b2e027bd8e20c3f1",
        "cc26df47633e42a486777e6896031ea25ac5bbc759a6bfb455b892278fa4db80",
    ):
        assert classes("CUT1_T06_PROVIDER_LANDSCAPE", context_hash) == {
            "CURRENT_STATE_FACT"
        }
    assert classes(
        "OBSERVABILITY_COST",
        "e990b865241062b6048d760bf7f32308e3305d5f3db3b5c50fce1939da9d9f64",
    ) == {"COST_ESTIMATE"}
    for source_id, context_hash, expected in (
        ("STATUS", "05c68405eabd1c3f8a22998678c116c07365616a8866933e07ba021961fb9864", {"HISTORICAL_FACT", "NORMATIVE_REQUIREMENT"}),
        ("SOURCE_TRACEABILITY_7B284BCF", "bc70a38f50f156ebd0cff87c36f195e4a3036c3aee60dfafcb1c6ab2a2e48f3d", {"CURRENT_STATE_FACT", "NORMATIVE_REQUIREMENT"}),
        ("SOURCE_TRACEABILITY_7B284BCF", "d7d4802108035e4755df2238a4c9f456ccc0e3a1a82aa0a672247846b66dfb0b", {"CURRENT_STATE_FACT", "NORMATIVE_REQUIREMENT"}),
        ("SOURCE_TRACEABILITY_7B284BCF", "561583ede14d521aadd210164cb70a9985f0355d9c78fe38998718e2d7aa838d", {"CURRENT_STATE_FACT", "IMPLEMENTED_BEHAVIOR", "NORMATIVE_REQUIREMENT"}),
    ):
        assert classes(source_id, context_hash) == expected
    assert all(
        row["semanticClass"] == "NORMATIVE_REQUIREMENT"
        and row["normativeEffect"] in {
            "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE",
        }
        for row in rows
    )
    assert all(
        row["normativeEffect"] == "CURRENT_NORMATIVE"
        for row in rows
        if not row["sourceKind"].startswith("EXTERNAL_")
    )
    required_ids = {
        "MPV2-A845CC7997102EA6AC29", "MPV2-7C8FA2E96EF79C908783",
        "MPV2-6B500A05FE9638883A5F", "MPV2-54F4C334C9379D149B4F",
        "MPV2-DD70D43A1F9FBFA21E97", "MPV2-9A0D9F77C6677905FA3A",
        "MPV2-FDC8E3BB1FFE9BAE5900", "MPV2-8EC0B8E97C6A53C6FDBC",
        "MPV2-4359C1CFCA56AE26E784",
    }
    assert required_ids <= {row["requirementId"] for row in rows}
    security_source = sources["SECURITY_PRIVACY"]
    security_atoms = program._atoms(
        "SECURITY_PRIVACY", security_source["atomizer"],
        program.frozen_source_bytes(REPO, security_source),
    )
    screening_ids = {
        atom.atom_id for atom in security_atoms
        if "### Secret Screening Result" in atom.anchor
    }
    assert len(screening_ids) == 23
    assert screening_ids <= {row["sourceAtomId"] for row in rows}
    for context_hash in (
        "1b70f8b921ec712c3ebd9bf23d240162ddf5f0cb315a1dee9311630d760ed4f6",
        "95225178caeac1177083026d1ae7419524c9573e477ba5ec5f027378f4891138",
        "08aecd4a65e581f6fcb9f88205785a8da405cad4f6eb44300a289b884928cd63",
    ):
        conflicting = [
            row for row in rows
            if row["sourceId"] == "REAL_MEDIA_HOSTED_DEMO_PLAN"
            and row["normalizedSourceContextSha256"] == context_hash
            and row["disposition"] != "PRESERVED"
        ]
        assert conflicting and all(
            row["replacementId"] and row["ownerAuthorityRef"]
            for row in conflicting
        )
def test_destinations_are_resolvable_clause_ids_not_heading_presence() -> None:
    mapping = _read_mapping()
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
def test_structured_json_semantic_partition_is_exact_and_hash_bound() -> None:
    raw = "SOURCE_PRESENTER_REGISTRY_D3ECDDB1,119,113,6,16b519f609c427e7b04dd32304ec786803fcfbc3065aa8c5c623171f4de7952d,7cae42b4d025b823972ce1dfb83c1922cbf977bb46cb06677cf0a9946157a830|SOURCE_STAGE2_ARCHITECTURE_CONTRACT_F748F325,293,289,4,a9dffe6a571606f60e2e230b545c228328fdbeae276d32f3d386a6fe51c6d1d7,165a3e4f41dcf8aab29c9d8591159361dc253fad790c453fab7fcd18f86561e1|SOURCE_GOVERNANCE_PREFLIGHT_V1_SCHEMA_64752DA5,33,30,3,31dec69f72860c56267c46fec2ba76d9f000b4e5d75e8348c90b3be51ed893b2,68c859b8843ddee78d323539644393c623d6cfc7183cbd431fad79eb83631350|SOURCE_AUTHORITY_CORE_STATE_MATRICES_V1_7CD36E27,944,942,2,203c592598be6651c080025e0dc0f298357103a0151202438cbc6d2e9c028764,38818f29bde05e99b38b19108ac03ac8d54313f213d82ec1c0986eebe13b1ffc|SOURCE_AUTHORITY_RECONCILIATION_AND_STALE_ROUTE_PHASE_SPEC_V1_4FC31FFB,34,0,34,56d2d7d3b239c674da0b774aea93895485777ee2e9c6585819afe6a2085d8c46,4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945|SOURCE_CUT1_ALL_PRESENTER_ACCEPTANCE_MATRIX_V1_9597559E,122,115,7,284b37c177ec6e046b19894153e4f8792f409714abd2f99e82fe62b4edffc013,7b549b65032f81dc62b16312ac6605fe23c18ff43904b6698ba3fd54d8908029|SOURCE_CUT1_BLINDED_HUMAN_EVALUATION_PROTOCOL_V1_C374C7E7,370,345,25,20df56ce1190f30f867ec8f3c2ec7e9795f37934fb4f130256bde553a280ce40,09d4d45f826c3ddbbc113d21064b78cea15a91ce7d4e05675355bc8a359af5d7|SOURCE_CUT1_GOOGLE_GEMINI_TTS_STYLE_PROMPTS_V1_7A42BD24,61,47,14,305b470ace0313bc869da308efaf813863ae1c5538526f4c68bec6b228e499b0,332056deb3379ad0f376edd9d2c86dbfc585728b11cc51ef5069b42969bf94de|SOURCE_CUT1_PRESENTER_DERIVATIVES_V1_05780D7A,104,44,60,63663b8621653c3b4d1c794a93f90f3848e1c50af4dba8524160a00a849d05b7,74980b368dd82ac04a453fabc33c9836949747dcfd99c9fcfa450070bdc733dd|SOURCE_CUT1_PRESENTER_LIVE_BINDING_V2_FF41196F,19,8,11,5e8579da5c4e30110ac7d08c8b43e3b5beb574fe0852a4acea5d8c951231fb5e,2f135f9d453cd10183d1f7aac03b6ed9a7e1b6c95b08f89e2fea7cb186bca74d|SOURCE_CUT1_PROJECT_FACTS_V1_5A84887A,507,0,507,32093f77946ab00c2da1cf4b37a23f1a032abbd24d97db0be9d60026b9ff68d4,4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945|SOURCE_CUT1_PROVIDER_BAKEOFF_CONTRACT_V1_295A1DA2,674,345,329,afa3debf56970125116f164330de27a3847c1de5aff30e3c9456e0768fccc136,2ccdb29f65b24fec74a3b452bcc7606e17722ea50913e8d2b6ad01d129751f10|SOURCE_PUBLICATION_BOUNDARY_V1_1B85CD76,71,68,3,db1af1dfc17b4ad632d65ee9adb3b0312154ae0ff0b366647de5bf20d8d42113,522721f04d3de941c9cb51dad3f8e84bd9f24f70a0104da69208a3830eb85c34|SOURCE_ACTIVE_PROGRAM_ROUTE_V1_SCHEMA_A52A17D4,233,230,3,b7c5ce4515d20df7ff3395a90bb1474edb0cd90b12667109a0a439801314cee2,88490fe113f0db5be99e2aef3a3c33f97d4aba0d33b1ff0954af35789f863840|SOURCE_CUT1_AUTHORITY_MANIFEST_V1_SCHEMA_C042B903,226,223,3,a2ece86223e47ef60e7a9a929a8f13e185c279dd4f9fdcfa74dfadeffdc34636,8974ac7cecda4bcbb5cb7063753173bb201e91f0148a45b8d38e1cdbfd0316c9|SOURCE_CUT1_CONTROLLED_PRESENTER_EVIDENCE_V1_SCHEMA_F96F21B7,383,380,3,7b24161e5551cc3437fdc6d24048017e85885326cf3945b37cc753fa71da61f9,d7d90be7e4d53dbf31771139b6f67436eaed4f872efe85f635aac3ac63dcdbba|SOURCE_CUT1_HUMAN_REALISM_EVALUATION_V1_SCHEMA_CC861FC2,738,735,3,3f3150462cb3d36834a7aa1284566599c30794adf23a4dceeece0f3b7dcfee2c,6d83c8000d4ce092492f75a3209cd7de5a4e67601a52311396f4f6c2ea15ad2c|SOURCE_CUT1_PRESENTER_PROVIDER_ACCEPTANCE_V1_SCHEMA_A13FCC08,564,561,3,8327cdf3f8b01677e3383d00d7f862ff36fc82f279fc84d57f2637a91ac79c1a,5e918d62b560a1a8ccc4abf1547cba31af87bc684c002dd83fdd1cabdec4a304|SOURCE_MASTER_PROGRAM_AUTHORITY_DECISION_V1_SCHEMA_470B2053,170,167,3,ebf10dda00381c318f234956e26b114a3a2c64428767b611288da22e01a85a40,35f22a22be8ed48b98acb1f66553093c310b7b507dd3b943d8bbf2557493f85c"
    expected = {fields[0]: (int(fields[1]), int(fields[2]), int(fields[3]), fields[4], fields[5]) for record in raw.split("|") for fields in [record.split(",")]}
    sources = program.expected_source_records(REPO)
    role_policy = {"SOURCE_GOVERNANCE_PREFLIGHT_V1_SCHEMA_64752DA5", "SOURCE_CUT1_CONTROLLED_PRESENTER_EVIDENCE_V1_SCHEMA_F96F21B7", "SOURCE_CUT1_HUMAN_REALISM_EVALUATION_V1_SCHEMA_CC861FC2", "SOURCE_CUT1_PRESENTER_PROVIDER_ACCEPTANCE_V1_SCHEMA_A13FCC08"}
    assert set(program._JSON_INSTANCE_POLICY_SOURCE_IDS) == set(expected) - role_policy
    for source_id, receipt in expected.items():
        coverage = sources[source_id]["semanticCoverage"]
        assert (coverage["candidateUnitCount"], coverage["normativeRequirementCount"], coverage["excludedUnitCount"], coverage["orderedPartitionSha256"], coverage["orderedNormativeAtomSha256"]) == receipt
    assert tuple(sum(receipt[index] for receipt in expected.values()) for index in range(3)) == (5665, 4642, 1023)
    assert program._JSON_MIXED_DOMINANT_NORMATIVE_IDS == frozenset("MPV2-020C1D52989CF32F2F24 MPV2-F068002A4DEE85FB1898 MPV2-5B6F739CDE8F1600EEBF MPV2-A0E20012C8BEF9724E17 MPV2-024B6AB140D70C69FC57 MPV2-E666A52ADD63EE842B01".split())
    assert not program._json_instance_is_normative(program.Atom("UNKNOWN", "json-pointer:/unreviewed::INSTANCE_FACT:L1", "1"))
def test_dispositions_do_not_mechanically_claim_strengthening() -> None:
    mapping = _read_mapping()
    assert all(
        row["thresholdComparison"]["basis"]
        == program.expected_comparison_basis(row)
        for row in mapping["rows"]
    )
def test_known_legacy_conflicts_have_curated_resolutions() -> None:
    rows = program.generate_mapping(REPO)["rows"]
    expected = (
        ("MASTER_PROGRAM_V1", "Only one retry is allowed", "STRENGTHENED"),
        ("MASTER_PROGRAM_V1", "15-second audition excerpt", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("MASTER_PROGRAM_V1", "US$100 total audition ceiling", "STRENGTHENED"),
        ("MASTER_PROGRAM_V1", "The US$100 ceiling applies only to auditions", "PRESERVED"),
        ("MASTER_PROGRAM_V1", "The aggregate requires exactly one accepted canonical WAV", "STRENGTHENED"),
        ("MASTER_PROGRAM_V1", "one distinct accepted 1920×1080 MP4", "STRENGTHENED"),
        ("MASTER_PROGRAM_V1", "one distinct accepted 1080×1920 MP4", "STRENGTHENED"),
        ("FIVE_CUT_ROADMAP", "Meera primary", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("FIVE_CUT_ROADMAP", "Raj/Myra fallback", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("FIVE_CUT_ROADMAP", "paid providers", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("FIVE_CUT_ROADMAP", "Cuts 1/5 / UX/Legal", "RELOCATED"),
        ("FIVE_CUT_ROADMAP", "single roadmap and acceptance index for Cut 1 through Cut 5", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("CUT1_PRESENTER_CONTRACT", "Meera is the primary presenter", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("API_CONTRACT", "selected Meera narration", "PRESERVED"),
        ("API_CONTRACT", "Narration and TTS receipt authority additionally require selected Meera", "PRESERVED"),
        ("API_CONTRACT", "Create retries may run only when provider idempotency", "STRENGTHENED"),
        ("STATUS", "Meera primary", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("CUT1_ACCEPTANCE", "- Presenter: Meera", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("CUT1_ACCEPTANCE", "Raj is first backup", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("CUT1_ACCEPTANCE", "Myra is second backup", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("PHASE_PLAN", "The five-cut scope", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("CUT1_PRESENTER_CONTRACT", "Ordinary product UX does not label", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
        ("ARCHITECTURE", "retry budget of one retry", "STRENGTHENED"),
        ("MASTER_PROGRAM_V1", "clean master has no voluntary spoken", "RELOCATED"),
        ("MASTER_PROGRAM_V1", "adds disclosure only when a reviewed law", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"),
    )
    for source_id, needle, disposition in expected:
        matches = [
            row
            for row in rows
            if row["sourceId"] == source_id and needle in _row_text(row)
        ]
        resolved = [row for row in matches if row["disposition"] == disposition]
        assert len(resolved) == 1, (source_id, needle, len(matches), len(resolved))
        row = resolved[0]
        if disposition == "PRESERVED":
            assert row["replacementId"] is None
            assert row["ownerAuthorityRef"] is None
        else:
            assert row["replacementId"]
            assert row["ownerAuthorityRef"]
            assert row["thresholdComparison"]["basis"] != (
                "STRENGTHENED requires an exact retained-source and additive-control proof."
            )
def test_every_curated_conflict_rule_selects_one_unique_frozen_atom() -> None:
    sources = program._source_records(REPO)
    atoms_by_source = {
        source["sourceId"]: program._atoms(
            source["sourceId"],
            source["atomizer"],
            program.frozen_source_bytes(REPO, source),
        )
        for source in sources
    }
    program._validate_conflict_rules(atoms_by_source)
    first = program._CONFLICT_RULES[0]
    target = program._CONFLICT_TARGETS[0][0]
    atoms_by_source[first.source_id] = [
        atom
        for atom in atoms_by_source[first.source_id]
        if not (
            atom.source_context_sha256 == target.context_sha256
            and atom.focus_start == target.focus_start
            and atom.text == target.atomic_focus
        )
    ]
    with pytest.raises(ValueError, match="resolved 0 atoms"):
        program._validate_conflict_rules(atoms_by_source)
def test_v1_meera_route_keeps_cell_scope_and_cross_cut_governance_destinations() -> None:
    rows = program.generate_mapping(REPO)["rows"]
    meera_rows = [
        row
        for row in rows
        if row["sourceId"] == "MASTER_PROGRAM_V1"
        and any(
            f"## {section}." in row["sourceAnchor"]
            for section in range(20, 36)
        )
    ]
    assert meera_rows
    destinations = {row["v2DestinationClause"] for row in meera_rows}
    assert "MPV2-CUT1-MEERA-CELL" in destinations
    assert destinations <= {
        "MPV2-CUT1-MEERA-CELL", "MPV2-SECTION-6", "MPV2-SECTION-8",
        "MPV2-SECTION-9",
    }
def test_issue_references_keep_explicit_types_and_heading_context() -> None:
    refs = program._issue_refs(
        "PR #422 follows Issue `#421`; see #440 and issuecomment-5263752038.",
        "docs/example.md",
    )
    assert refs == [
        "github-comment:5263752038",
        "github-issue:421",
        "github-issue:440",
        "github-pull-request:422",
    ]
    status = next(
        item for item in program._source_records(REPO)
        if item["repositoryPath"] == "docs/STATUS.md"
    )
    assert {"github-comment:5197776590", "github-comment:5521588438"} <= set(status["authorityRefs"])
    mapping = program.generate_mapping(REPO)
    heading_row = next(
        row
        for row in mapping["rows"]
        if "Issue #475" in row["sourceAnchor"]
        and "Issue #475" not in _row_text(row)
    )
    assert any(
        reference.startswith("github-issue:475@sha256:")
        for reference in heading_row["sourceAuthorityRefs"]
    )
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Issues #366, #368, #421 and PR #422 remain exact.",
            {
                "github-issue:366",
                "github-issue:368",
                "github-issue:421",
                "github-pull-request:422",
            },
        ),
        (
            "PRs #443, #453 and #461 are predecessors.",
            {
                "github-pull-request:443",
                "github-pull-request:453",
                "github-pull-request:461",
            },
        ),
        (
            "Routes: Issues #512, #514, and #516.",
            {
                "github-issue:512",
                "github-issue:514",
                "github-issue:516",
            },
        ),
        (
            "PRs #230, #234, and #248 are immutable predecessors.",
            {
                "github-pull-request:230",
                "github-pull-request:234",
                "github-pull-request:248",
            },
        ),
        (
            "Issues #13, #6; #21 only records the later boundary.",
            {
                "github-issue:13",
                "github-issue:6",
                "github-issue:21",
            },
        ),
        (
            "OWNER amendment `5500512956` and correction `5500512957` control.",
            {"github-comment:5500512956", "github-comment:5500512957"},
        ),
        (
            "Issue comments `5521410237` and\n `5521588438` are the source.",
            {"github-comment:5521410237", "github-comment:5521588438"},
        ),
        ("Provider job 1234567890 and account 2345678901.", {f"repository:docs/example.md@{program.BASE_SHA}"}),
        (
            "Workflow 3408898351 and bare #440 are context only.",
            {"github-issue:440"},
        ),
    ],
)
def test_issue_reference_parser_is_typed_and_proximity_scoped(
    text: str, expected: set[str]
) -> None:
    assert set(program._issue_refs(text, "docs/example.md")) == expected
def test_legacy_enterprise_rows_resolve_only_to_cut6() -> None:
    mapping = program.generate_mapping(REPO)
    rows = [
        row
        for row in mapping["rows"]
        if row["sourceId"] == "FIVE_CUT_ROADMAP"
        and program._legacy_enterprise(program._row_atom(row))
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
def test_current_mapping_serialization_atomizes_clause_without_detector_text() -> None:
    raw = (REPO / program.MAPPING_PATH).read_bytes()
    assert b"credential exposure, duplicate/sybil" not in raw
    mapping = program.decode_mapping_artifact(program._load_json_text(raw.decode("utf-8")))
    rows = [
        row
        for row in mapping["rows"]
        if row["normalizedSourceContextSha256"]
        == program.GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256
        and ":L417:" in row["sourceAnchor"]
    ]
    assert len(rows) == 11
    assert {
        "screening for prompt injection and accidental credential exposure",
        "duplicate/sybil detection",
    } <= {_row_text(row) for row in rows}
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
            "reordered-row",
            lambda value: value["rows"].reverse(),
            "MPV2.MAPPING.SOURCE_ORDER_INVALID",
        ),
        (
            "wrong-destination-type",
            lambda value: value["rows"][0].update({"v2DestinationClause": []}),
            "MPV2.MAPPING.ROW_SCHEMA_INVALID",
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
def test_mapping_renderer_rejects_unrepresentable_weak_threshold() -> None:
    mapping = _read_mapping()
    mapping["rows"][0]["thresholdComparison"]["relation"] = "WEAKER"
    with pytest.raises(ValueError, match="threshold comparison invalid"):
        program.render_mapping(mapping)
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schemaVersion", "Bypass"),
        ("mappingId", "bypass"),
        ("proposalState", "ACTIVE"),
        ("cutoff", "2026-09-07T00:00:00+05:30"),
    ],
)
def test_mapping_renderer_rejects_unrepresentable_metadata(
    field: str, value: str
) -> None:
    mapping = _read_mapping()
    mapping[field] = value
    with pytest.raises(ValueError, match="logical mapping shape invalid"):
        program.render_mapping(mapping)
def test_source_and_destination_byte_mutations_fail_closed(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    source = root / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    assert "MPV2.SOURCE.V1_MUTATED" in program.validate_repository(
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
    assert "MPV2.MAPPING.SOURCE_BINDING_INVALID" in failures
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
def test_mapping_source_authority_and_rendering_are_exact(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(
        root,
        program.MAPPING_PATH,
        lambda value: value["sources"][0].update({"authorityRefs": ["unknown"]}),
    )
    failures = program.validate_repository(root, certification=False)
    assert "MPV2.MAPPING.SOURCE_BINDING_INVALID" in failures
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
        (
            lambda value: value["compatibilityMigration"]["requiredSurfaces"].pop(),
            "MPV2.TAXONOMY.COMPATIBILITY_MIGRATION_INVALID",
        ),
    ],
)
def test_taxonomy_mutations_fail_closed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.TAXONOMY_PATH, mutate)
    assert expected in program.validate_repository(root, certification=False)
def test_cut5_dependency_mutation_fails_closed(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(
        root,
        program.TAXONOMY_PATH,
        lambda value: next(
            cut for cut in value["cuts"] if cut["id"] == "Cut5"
        ).update({"dependsOn": ["Cut1", "Cut3", "Cut4"]}),
    )
    assert "MPV2.TAXONOMY.CUT_DEPENDENCY_INVALID" in program.validate_repository(
        root, certification=False
    )
@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(
            {"cutDependencySemantics": "CAPABILITY_ENTRY_PREREQUISITES"}
        ),
        lambda value: next(
            item
            for item in value["cut5CapabilityDependencies"]
            if item["id"] == "PREPARED_ENGLISH"
        ).update({"requiresCuts": ["Cut1", "Cut3"]}),
        lambda value: next(
            item
            for item in value["cut5CapabilityDependencies"]
            if item["id"] == "GROUNDED_REALTIME"
        ).update({"requiresCuts": ["Cut1"]}),
        lambda value: next(
            item
            for item in value["cut5CapabilityDependencies"]
            if item["id"] == "EXPANDED_MOTION"
        ).update({"requiredForCut5Completion": True}),
    ],
)
def test_cut5_capability_dependency_mutations_fail_closed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.TAXONOMY_PATH, mutate)
    assert (
        "MPV2.TAXONOMY.CUT5_CAPABILITY_DEPENDENCY_INVALID"
        in program.validate_repository(root, certification=False)
    )
def test_digital_twin_step_dependency_mutation_fails_closed(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(
        root,
        program.TAXONOMY_PATH,
        lambda value: next(
            item for item in value["digitalTwinSequence"] if item["id"] == "DT4"
        ).update({"dependsOnSteps": ["DT2"]}),
    )
    assert "MPV2.TAXONOMY.DT_DEPENDENCY_INVALID" in program.validate_repository(
        root, certification=False
    )
@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["laneA"][0].update({"state": "BROKEN"}),
        lambda value: value["productModes"][0].update({"providerAuthority": True}),
    ],
)
def test_taxonomy_schema_is_executed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.TAXONOMY_PATH, mutate)
    assert "MPV2.TAXONOMY.SCHEMA_INSTANCE_INVALID" in program.validate_repository(
        root, certification=False
    )
@pytest.mark.parametrize("mutate", [
    lambda value: value["rows"][0].__setitem__(0, "not-an-index"),
    lambda value: value["externalAuthorityManifest"]["governingContextDecisionPartition"].update({"unexpected": True}),
])
def test_mapping_schema_is_executed(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_mapping_artifact(root, mutate)
    assert "MPV2.MAPPING.SCHEMA_INSTANCE_INVALID" in program.validate_repository(
        root, certification=False
    )
def test_mapping_schema_destination_enum_matches_executable_registry() -> None:
    schema = json.loads(
        (REPO / program.MAPPING_SCHEMA_PATH).read_text(encoding="utf-8")
    )
    assert set(schema["$defs"]["destinationId"]["enum"]) == set(
        program.DESTINATION_CLAUSES
    )
def test_malformed_schema_fails_closed_without_crashing(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_json(root, program.MAPPING_SCHEMA_PATH, lambda value: value["properties"]["rows"].update({"minItems": "bad"}))
    assert "MPV2.MAPPING.SCHEMA_INSTANCE_INVALID" in program.validate_repository(
        root, certification=False
    )
    root = _copy_candidate(tmp_path / "unsupported")
    _rewrite_json(
        root,
        program.MAPPING_SCHEMA_PATH,
        lambda value: value.update({"allOf": []}),
    )
    assert "MPV2.MAPPING.SCHEMA_INSTANCE_INVALID" in program.validate_repository(
        root, certification=False
    )
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
def test_malformed_collections_fail_closed_without_validator_crash(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path)
    _rewrite_mapping_artifact(root, lambda value: value.pop("sources"))
    assert "MPV2.MAPPING.SCHEMA_INVALID" in program.validate_repository(
        root, certification=False
    )
    for index, field in enumerate(("sources", "rows")):
        root = _copy_candidate(tmp_path / f"null-{index}")
        _rewrite_mapping_artifact(root, lambda value, field=field: value.update({field: None}))
        failures = program.validate_repository(root, certification=False)
        assert "MPV2.BINDING.ARTIFACT_SHAPE_INVALID" in failures
    root = _copy_candidate(tmp_path / "root-list")
    (root / program.MAPPING_PATH).write_text("[]\n", encoding="utf-8")
    assert "MPV2.BINDING.ARTIFACT_SHAPE_INVALID" in program.validate_repository(
        root, certification=False
    )
    root = _copy_candidate(tmp_path)
    _rewrite_json(
        root, program.TAXONOMY_PATH, lambda value: value.update({"legacyAliases": {}})
    )
    assert "MPV2.TAXONOMY.SCHEMA_INSTANCE_INVALID" in program.validate_repository(
        root, certification=False
    )
    root = _copy_candidate(tmp_path / "unhashable-external")
    _rewrite_mapping_artifact(
        root,
        lambda value: value["externalAuthorityManifest"]["records"][0].update(
            {"authorityEffect": []}
        ),
    )
    assert "MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID" in (
        program.validate_repository(root, certification=False)
    )
    root = _copy_candidate(tmp_path / "null-external-records")
    _rewrite_mapping_artifact(
        root,
        lambda value: value["externalAuthorityManifest"].update({"records": None}),
    )
    assert "MPV2.MAPPING.ATOMIZATION_FAILED" in program.validate_repository(
        root, certification=False
    )
def test_taxonomy_malformed_collections_are_stable_failures() -> None:
    taxonomy = program._load_json(REPO / program.TAXONOMY_PATH)
    fields = ("cuts", "cut5CapabilityDependencies", "digitalTwinSequence", "historicalCheckpoints")
    for field in fields:
        malformed = copy.deepcopy(taxonomy)
        malformed[field] = None
        assert program._taxonomy_failures(malformed) == ["MPV2.TAXONOMY.SCHEMA_INVALID"]
        malformed = copy.deepcopy(taxonomy)
        malformed[field][0]["id"] = []
        assert program._taxonomy_failures(malformed) == ["MPV2.TAXONOMY.SCHEMA_INVALID"]
def test_missing_v1_and_invalid_review_utf8_fail_closed(tmp_path: Path) -> None:
    root = _copy_candidate(tmp_path / "missing-v1")
    (root / program.V1_PATH).unlink()
    assert "MPV2.SOURCE.V1_MUTATED" in program.validate_repository(
        root, certification=False
    )
    root = _copy_candidate(tmp_path / "invalid-review")
    review = root / program.REVIEW_PATHS[0]
    review.write_bytes(review.read_bytes() + b"\xff")
    assert f"MPV2.PUBLIC.UTF8_INVALID:{program.REVIEW_PATHS[0]}" in (
        program.validate_repository(root, certification=False)
    )
def test_unreadable_required_artifact_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, original = _copy_candidate(tmp_path), Path.read_bytes
    def read_bytes(path: Path) -> bytes:
        if path == root / program.DOCUMENT_PATH:
            raise PermissionError("denied")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    assert program.validate_repository(root, certification=False) == [f"MPV2.ARTIFACT.UNREADABLE:{program.DOCUMENT_PATH}"]
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
