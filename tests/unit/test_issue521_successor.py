"""Independent expectations for the bounded four-entry G1 correction."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest

from scripts.quality import issue521_master_program_v2 as predecessor
from scripts.quality import issue521_successor as successor
from scripts.quality.phase1_closure import runner

ROOT = Path(__file__).resolve().parents[2]
SUCCESSOR = "docs/governance/successors/g1-adr0000/superset-mapping-v2.json"
REMOVED = frozenset({
    "MPV2-6FD1AF1B119751D12FE6", "MPV2-29F6F8A4F175178310E3",
    "MPV2-7A08CF034D6B2A3D447D", "MPV2-D5086F6004054DDDA5F6",
})


def test_bibliography_candidate_excludes_exact_four_normative_rows() -> None:
    # Before the successor exists, exercise the actual predecessor's semantics.
    # This makes the recorded RED a source classification failure, not an import failure.
    candidate = ROOT / SUCCESSOR
    if not candidate.exists():
        candidate = ROOT / predecessor.MAPPING_PATH
    mapping = predecessor.decode_mapping_artifact(predecessor._load_json(candidate))
    rows = mapping["rows"]
    promoted = [row for row in rows if row["requirementId"] in REMOVED]
    assert not promoted, "Bibliography-only references remain promoted to normative mapping rows"
    assert len(rows) == 31_394
    partition = mapping["repositorySemanticDecisionPartition"]
    adr = next(entry for entry in partition["sources"] if entry[0] == "ADR_0000_ADR_PROCESS")
    assert adr[4][18:22] == "RRRR"
    assert len([row for row in rows if row["sourceId"] == "ADR_0000_ADR_PROCESS"]) == 17


@pytest.fixture(scope="module")
def candidate(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("successor")
    profile, _ = successor.registered_inputs(ROOT)
    paths = {item["path"] for item in profile["predecessorArtifacts"]}
    paths.update(profile["outputs"].values())
    paths.update({successor.PROFILE_PATH, profile["preflightPath"], predecessor.V1_PATH})
    for relative in paths:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    shutil.copyfile(ROOT / ".git", root / ".git")
    return root


@contextmanager
def changed(root: Path, relative: str, value: bytes) -> Iterator[None]:
    path = root / relative
    original = path.read_bytes()
    try:
        path.write_bytes(value)
        yield
    finally:
        path.write_bytes(original)


def decoded(path: Path) -> dict[str, Any]:
    return predecessor.decode_mapping_artifact(predecessor._load_json(path))


def test_complete_derivation_preserves_every_other_row_source_and_receipt() -> None:
    old, new = decoded(ROOT / predecessor.MAPPING_PATH), decoded(ROOT / SUCCESSOR)
    assert [row for row in old["rows"] if row["requirementId"] not in REMOVED] == new["rows"]
    assert [successor.canonical(row) for row in old["rows"] if row["requirementId"] not in REMOVED] == [successor.canonical(row) for row in new["rows"]]
    for key in ("repositoryContextDecisionPartition", "externalAuthorityManifest", "externalSemanticCorrectionOverlay", "certification", "ownerAuthority"):
        assert old[key] == new[key]
    old_sources, new_sources = copy.deepcopy(old["sources"]), copy.deepcopy(new["sources"])
    for source in new_sources:
        if source["sourceId"] == "ADR_0000_ADR_PROCESS":
            coverage = source["semanticCoverage"]
            assert (coverage["candidateUnitCount"], coverage["normativeRequirementCount"], coverage["excludedUnitCount"]) == (22, 17, 5)
            assert coverage["classCounts"]["REFERENCE"] == 4
            source["semanticCoverage"] = next(s["semanticCoverage"] for s in old_sources if s["sourceId"] == source["sourceId"])
    assert old_sources == new_sources
    assert sum(row["sourceKind"].startswith("EXTERNAL_") for row in new["rows"]) == 13_382
    assert predecessor.render_mapping(new).encode() == (ROOT / SUCCESSOR).read_bytes()
    census = new["semanticDuplicateCensus"]
    assert (census["groupCount"], census["occurrenceCount"], census["excessOccurrenceCount"]) == (859, 3099, 2240)
    groups: dict[tuple[str, str], list[str]] = {}
    for row in new["rows"]:
        groups.setdefault((row["atomicFocusSha256"], row["normalizedSourceContextSha256"]), []).append(row["sourceAtomId"])
    repeated = {key: sorted(ids) for key, ids in groups.items() if len(ids) > 1}
    assert len(repeated) == 859
    assert sorted(repeated.values()) == sorted(sorted(m["sourceAtomId"] for m in group["members"]) for group in census["groups"])
    partition = new["repositorySemanticDecisionPartition"]
    counts = dict.fromkeys(partition["classCounts"], 0)
    for entry in partition["sources"]:
        assert entry[5] == hashlib.sha256(successor.canonical(entry[:-1])).hexdigest()
        for code in entry[4]:
            counts[partition["classCodes"][code]] += 1
    assert counts == partition["classCounts"]
    assert (counts["NORMATIVE_REQUIREMENT"], counts["REFERENCE"]) == (13_370, 57)
    assert sum(counts.values()) == 19_668
    assert partition["partitionSha256"] == hashlib.sha256(successor.canonical({k: v for k, v in partition.items() if k != "partitionSha256"})).hexdigest()


def test_registered_candidate_and_predecessor_both_pass_without_certification(candidate: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert predecessor.validate_repository(candidate, certification=False) == []
    assert successor.validate_repository(candidate) == []
    assert predecessor.validate_repository(candidate, certification=False) == []
    output = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert output["result"] == "STRUCTURAL_PENDING"
    assert output["privateAvailability"] == "NOT_CHECKED"
    assert output["semanticAcceptance"] == "NOT_GRANTED"


@pytest.mark.parametrize("mutation", ["fifth", "coordinate", "source", "base", "unknown", "bool"])
def test_self_rehashed_profile_cannot_supply_its_own_trust(candidate: Path, mutation: str) -> None:
    profile, _ = successor.registered_inputs(candidate)
    if mutation == "fifth":
        profile["corrections"].append(copy.deepcopy(profile["corrections"][0]))
        profile["expectedCounts"]["successor"]["mappingRows"] -= 1
    elif mutation == "coordinate":
        profile["corrections"][0]["sourceSpan"]["startLine"] = 35
    elif mutation == "source":
        profile["source"]["repositoryPath"] = "docs/ADR/0001-codex-operating-model.md"
    elif mutation == "base":
        profile["baseCommit"] = "0" * 40
    elif mutation == "unknown":
        profile["selfReportedApproval"] = "APPROVED"
    else:
        profile["limits"]["gitTimeoutSeconds"] = True
    raw = successor.canonical(profile)
    # A coherent attacker may hash its changed profile; no production input accepts that digest.
    assert hashlib.sha256(raw).hexdigest() != successor.PROFILE_SHA256
    with changed(candidate, successor.PROFILE_PATH, raw):
        assert successor.validate_repository(candidate)[0] in {"G1.ARTIFACT.SIZE", "G1.REGISTRATION.PROFILE"}


def test_same_length_profile_and_preflight_replacement_fail_anchor(candidate: Path) -> None:
    profile, _ = successor.registered_inputs(candidate)
    for path, before, after, code in (
        (successor.PROFILE_PATH, b'"startLine": 36', b'"startLine": 35', "G1.REGISTRATION.PROFILE"),
        (profile["preflightPath"], b'"issue_number": 540', b'"issue_number": 541', "G1.REGISTRATION.PREFLIGHT"),
    ):
        original = (candidate / path).read_bytes()
        revised = original.replace(before, after)
        assert revised != original and len(revised) == len(original)
        with changed(candidate, path, revised):
            assert successor.validate_repository(candidate) == [code]


@pytest.mark.parametrize("mutation", ["fifth_row", "retained_row", "receipt_pass", "missing_receipt"])
def test_coherent_encoded_candidate_edits_are_rejected(candidate: Path, mutation: str) -> None:
    mapping = decoded(candidate / SUCCESSOR)
    if mutation == "fifth_row":
        mapping["rows"].pop(0)
    elif mutation == "retained_row":
        mapping["rows"][0]["accountableOwner"] = "REPLACEMENT_OWNER"
    elif mutation == "receipt_pass":
        mapping["externalSemanticCorrectionOverlay"]["exhaustiveReview"]["result"] = "PASS"
    else:
        mapping["externalSemanticCorrectionOverlay"].pop("exhaustiveReview")
    raw = predecessor.render_mapping(mapping).encode()
    # The attacker coherently regenerates the compact codec checksums.
    assert decoded_bytes(raw)["rows"] == mapping["rows"]
    with changed(candidate, SUCCESSOR, raw):
        assert successor.validate_repository(candidate) == ["G1.SUCCESSOR.DERIVATION:" + SUCCESSOR]


def decoded_bytes(raw: bytes) -> dict[str, Any]:
    return predecessor.decode_mapping_artifact(predecessor._load_json_text(raw.decode()))


@pytest.mark.parametrize("field,value", [("proposalState", "PASS"), ("authorityEffect", "ACTIVATED"), ("successorCounts", {"mappingRows": 31398}), ("externalSemanticInput", {"successorCertification": "PASS"})])
def test_lineage_cannot_replay_old_receipt_as_successor_acceptance(candidate: Path, field: str, value: Any) -> None:
    profile, _ = successor.registered_inputs(candidate)
    path = profile["outputs"]["integrationLineage"]
    lineage = predecessor._load_json(candidate / path)
    lineage[field] = value
    with changed(candidate, path, successor.canonical(lineage) + b"\n"):
        assert successor.validate_repository(candidate) == ["G1.SUCCESSOR.DERIVATION:" + path]


def test_stale_binding_and_schema_rejected(candidate: Path) -> None:
    profile, _ = successor.registered_inputs(candidate)
    for output, predecessor_path in (("binding", predecessor.BINDING_PATH), ("mappingSchema", predecessor.MAPPING_SCHEMA_PATH)):
        path = profile["outputs"][output]
        with changed(candidate, path, (candidate / predecessor_path).read_bytes()):
            assert successor.validate_repository(candidate) == ["G1.SUCCESSOR.DERIVATION:" + path]


def test_schema_changes_only_partition_hash_and_two_class_counts() -> None:
    profile, _ = successor.registered_inputs(ROOT)
    old = predecessor._load_json(ROOT / predecessor.MAPPING_SCHEMA_PATH)
    new = predecessor._load_json(ROOT / profile["outputs"]["mappingSchema"])
    old_props = old["$defs"]["repositorySemanticDecisionPartition"]["properties"]
    new_props = new["$defs"]["repositorySemanticDecisionPartition"]["properties"]
    assert old_props["partitionSha256"] != new_props["partitionSha256"]
    new_props["partitionSha256"] = old_props["partitionSha256"]
    new_props["classCounts"]["const"].update(NORMATIVE_REQUIREMENT=13_374, REFERENCE=53)
    assert new == old
    artifact = predecessor._load_json(ROOT / SUCCESSOR)
    schema = predecessor._load_json(ROOT / profile["outputs"]["mappingSchema"])
    artifact["repositorySemanticDecisionPartition"]["classCounts"]["REFERENCE"] = 58
    assert predecessor._schema_instance_failures(artifact, schema, definition="SupersetMappingV2Root", failure_code="INVALID") == ["INVALID"]


@pytest.mark.parametrize("value", [True, False, 0, -1, float("inf"), float("nan"), "5", None, 1e300, 10**1000])
def test_runtime_config_rejects_invalid_typed_values(value: Any) -> None:
    with pytest.raises(ValueError, match="G1.CONFIG.GIT_TIMEOUT"):
        successor.RuntimeConfig(value)


@pytest.mark.parametrize("raw", ["nan", "inf", "0", "-1", "oops", "1e300", ""])
def test_production_environment_invalid_override_fails_closed(raw: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NARRATWIN_G1_GIT_TIMEOUT_SECONDS", raw)
    assert successor.validate_repository(ROOT) == ["G1.CONFIG.GIT_TIMEOUT"]


def test_production_override_reaches_new_git_consumer_without_rewriting_lineage(candidate: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    profile, _ = successor.registered_inputs(candidate)
    path = candidate / profile["outputs"]["integrationLineage"]
    before = path.read_bytes()
    calls: list[float] = []
    original = successor.git
    def observed(root: Path, config: successor.RuntimeConfig, *args: str) -> bytes:
        calls.append(config.git_timeout_seconds)
        return original(root, config, *args)
    monkeypatch.setattr(successor, "git", observed)
    monkeypatch.setenv("NARRATWIN_G1_GIT_TIMEOUT_SECONDS", "7.25")
    assert successor.validate_repository(candidate) == []
    assert calls and set(calls) == {7.25}
    output = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert output["effectiveVerificationConfiguration"] == {"gitTimeoutSeconds": 7.25}
    assert output["effectiveGenerationConfiguration"] == {"gitTimeoutSeconds": 5.0}
    assert path.read_bytes() == before


def test_unavailable_frozen_git_is_not_hidden_by_predecessor_cache(candidate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert successor.validate_repository(candidate) == []
    def unavailable(*args: Any) -> bytes:
        raise ValueError("G1.SOURCE.UNAVAILABLE")
    monkeypatch.setattr(successor, "git", unavailable)
    assert successor.validate_repository(candidate) == ["G1.SOURCE.UNAVAILABLE"]


@pytest.mark.parametrize("path", ["../outside", "/tmp/outside", "docs/../outside", "docs//alias", "docs\\alias"])
def test_path_traversal_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="G1.PATH.INVALID"):
        successor.safe_path(ROOT, path)


def test_symlink_and_unknown_profile_are_rejected(candidate: Path) -> None:
    path = candidate / successor.PROFILE_PATH
    raw = path.read_bytes()
    path.unlink()
    path.symlink_to(ROOT / successor.PROFILE_PATH)
    try:
        assert successor.validate_repository(candidate) == ["G1.PATH.SYMLINK"]
    finally:
        path.unlink()
        path.write_bytes(raw)
    assert successor.validate_repository(candidate, profile_id="attacker") == ["G1.REGISTRATION.UNKNOWN"]

def test_main_runs_successor_validation_before_preserved_route(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(runner, "check_publication_boundary", lambda: 0)
    monkeypatch.setattr(runner, "check_cut1_presenter_contract", lambda: 0)
    def verify(root: Path) -> list[str]:
        calls.append("successor")
        return []
    def preserved() -> int:
        calls.append("preserved")
        return 0
    monkeypatch.setattr(successor, "validate_repository", verify)
    monkeypatch.setattr(runner, "run_preserved_contracts", preserved)
    assert runner.main() == 0
    assert calls == ["successor", "preserved"]
    monkeypatch.setattr(successor, "validate_repository", lambda root: ["G1.FAULT"])
    calls.clear()
    assert runner.main() != 0
    assert calls == []


def test_registered_branch_routes_to_manifest_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    profile, _ = successor.registered_inputs(runner.ROOT)
    monkeypatch.setattr(runner, "current_branch", lambda root: profile["branch"])
    monkeypatch.setattr(runner, "run_successor", lambda: 43)
    assert runner.run_preserved_contracts() == 43


def test_successor_manifest_budgets_are_generic_and_fail_closed() -> None:
    profile, artifact = successor.registered_inputs(runner.ROOT)
    limits = artifact["change_budget"]["per_file_charged_lines"]
    charges = dict.fromkeys(limits, 1)
    def check(values: dict[str, int]) -> list[str]:
        return successor.successor_budget_failures(artifact, values, profile["branch"], 540)
    assert check(charges) == []
    for value in (True, -1):
        broken = charges | {next(iter(charges)): value}
        assert check(broken) == ["G1.SCOPE.UNCOUNTABLE"]
    path = next(iter(charges))
    assert check(charges | {path: limits[path] + 1}) == ["G1.SCOPE.FILE_BUDGET"]
    assert check(limits) == ["G1.SCOPE.TOTAL_BUDGET"]
    assert check(charges | {"unapproved.py": 1})
    assert check({k: v for k, v in charges.items() if k != path})


def test_actual_git_scope_push_pr_dirty_and_first_commit_boundaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile, artifact = successor.registered_inputs(runner.ROOT)
    profile = copy.deepcopy(profile)
    root = tmp_path / "scope"
    root.mkdir()
    def git(*args: str) -> str:
        return subprocess.run(["/usr/bin/git", *args], cwd=root, check=True, capture_output=True).stdout.decode().strip()
    git("init", "-b", profile["branch"])
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Scope fixture")
    git("commit", "--allow-empty", "-m", "base")
    profile["baseCommit"] = git("rev-parse", "HEAD")
    preflight = root / profile["preflightPath"]
    preflight.parent.mkdir(parents=True)
    preflight.write_bytes((runner.ROOT / profile["preflightPath"]).read_bytes())
    git("add", ".")
    git("commit", "-m", "preflight only")
    # Registration itself is covered against immutable real bytes in successor tests.
    monkeypatch.setattr(successor, "registered_inputs", lambda root: (profile, artifact))
    assert "GPF.SCOPE.REQUIRED_NOT_CHANGED" in successor.successor_scope(root, profile["branch"])
    for relative in artifact["scope"]["required"]:
        if relative == profile["preflightPath"]:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n")
    git("add", ".")
    git("commit", "-m", "complete scope")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    for event, base in (("push", "0" * 40), ("pull_request", profile["baseCommit"])):
        monkeypatch.setenv("GITHUB_EVENT_NAME", event)
        monkeypatch.setenv("GITHUB_BASE_SHA", base)
        monkeypatch.setenv("GITHUB_HEAD_SHA", git("rev-parse", "HEAD"))
        assert successor.successor_scope(root, profile["branch"]) == []
    assert successor.successor_scope(root, profile["branch"] + "-near") == ["G1.SCOPE.BRANCH"]
    (root / "extra.txt").write_text("outside\n")
    assert successor.successor_scope(root, profile["branch"]) == ["G1.SCOPE.HOSTED_DIRTY"]
    monkeypatch.delenv("GITHUB_ACTIONS")
    assert successor.successor_scope(root, profile["branch"]) == ["G1.SCOPE.EXTRA_PATH"]


def test_malformed_encoded_rows_fail_both_schema_and_successor(candidate: Path) -> None:
    profile, _ = successor.registered_inputs(candidate)
    artifact = predecessor._load_json(candidate / SUCCESSOR)
    artifact["rows"][0][0] = True
    schema = predecessor._load_json(candidate / profile["outputs"]["mappingSchema"])
    assert predecessor._schema_instance_failures(artifact, schema, definition="SupersetMappingV2Root", failure_code="INVALID") == ["INVALID"]
    with changed(candidate, SUCCESSOR, successor.canonical(artifact) + b"\n"):
        assert successor.validate_repository(candidate) == ["G1.SUCCESSOR.DERIVATION:" + SUCCESSOR]


def test_default_runtime_config_is_reviewed_and_reported() -> None:
    profile, _ = successor.registered_inputs(ROOT)
    assert successor.RuntimeConfig.resolve(profile, {}).effective() == {"gitTimeoutSeconds": 5.0}


def alternate_history(tmp_path: Path, *, late_merge: bool = False) -> Path:
    """Real Git objects/index/history; borrow existing objects read-only, never clone."""
    root = tmp_path / "alternate-history"
    root.mkdir()
    environment = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_NO_LAZY_FETCH": "1"}
    def git(*args: str) -> str:
        return subprocess.run(["/usr/bin/git", *args], cwd=root, env=environment, check=True, capture_output=True, text=True).stdout.strip()
    git("init")
    common = subprocess.run(["/usr/bin/git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    (root / ".git/objects/info/alternates").write_text(str(Path(common) / "objects") + "\n")
    profile, preflight = successor.registered_inputs(ROOT)
    git("config", "user.name", "History fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("checkout", "-b", profile["branch"], successor.BASE_COMMIT)
    # Unlike the earlier empty-base scope fixture, the actual GPF adapter exists at base.
    git("cat-file", "-e", successor.BASE_COMMIT + ":scripts/governance_preflight_repository.py")
    git("cat-file", "-e", successor.PREFLIGHT_COMMIT)
    raw = (ROOT / profile["preflightPath"]).read_bytes()
    path = root / profile["preflightPath"]
    path.write_bytes(raw.replace(b'"issue_number": 540', b'"issue_number": 541'))
    git("add", "--", profile["preflightPath"])
    git("commit", "-m", "alternate first preflight")
    for relative in preflight["scope"]["required"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == profile["preflightPath"]:
            path.write_bytes(raw)
        elif relative == successor.PROFILE_PATH:
            path.write_bytes((ROOT / relative).read_bytes())
        else:
            addition = b"\nfixture change\n" if path.exists() else b"fixture change\n"
            with path.open("ab") as stream:
                stream.write(addition)
    git("add", "--", *preflight["scope"]["required"])
    git("commit", "-m", "restore final preflight bytes and complete scope")
    if late_merge:
        git("merge", "--no-ff", "-s", "ours", "-m", "late unrelated registered history", successor.PREFLIGHT_COMMIT)
    return root


@pytest.mark.parametrize("boundary", ["common", "scope", "late_merge"])
def test_registered_preflight_must_belong_to_actual_first_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str) -> None:
    root = alternate_history(tmp_path, late_merge=boundary == "late_merge")
    profile, _ = successor.registered_inputs(root)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    if boundary == "common":
        with pytest.raises(ValueError, match="G1.REGISTRATION.ANCESTRY"):
            successor.verify_inputs(root, profile, successor.RuntimeConfig(5.0))
    else:
        expected = "G1.REGISTRATION.FIRST_COMMIT" if boundary == "late_merge" else "G1.REGISTRATION.ANCESTRY"
        assert successor.successor_scope(root, profile["branch"]) == [expected]


def test_successor_binding_binds_exact_lineage_bytes() -> None:
    profile, _ = successor.registered_inputs(ROOT)
    binding = predecessor._load_json(ROOT / profile["outputs"]["binding"])
    raw = (ROOT / profile["outputs"]["integrationLineage"]).read_bytes()
    assert binding.get("integrationLineagePath") == profile["outputs"]["integrationLineage"]
    assert binding["artifactHashes"].get("integrationLineageSha256") == hashlib.sha256(raw).hexdigest()
    assert binding["artifactShape"].get("integrationLineageBytes") == len(raw)
