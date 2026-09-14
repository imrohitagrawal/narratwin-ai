"""Registered four-entry successor. Structural verification grants no activation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from scripts.governance_preflight_repository import validate_governance_preflight_repository
from scripts.governance_preflight_v1 import validate_governance_preflight
from scripts.quality import issue521_master_program_v2 as predecessor

# Immutable identity reviewed before implementation, independently of candidate data.
# Altering this registration changes code and requires a new exact-head review.
PROFILE_ID = "g1-adr0000-bibliography-successor"
PROFILE_PATH = "docs/governance/successors/g1-adr0000/profile.json"
PROFILE_SHA256 = "51ac965848046e6b5ad06c029ca10a78ae432a840200820be0f0e89ca7fb8c8c"
PROFILE_BYTES = 6558
PREFLIGHT_SHA256 = "87c4dc10beb76875cb51244d6f538a1eb9d67f8d138c2d5de2d078e1e31ba527"
PREFLIGHT_BYTES = 7015
PREFLIGHT_COMMIT = "8add659eec90a21514d3cea193d5f6ffb5a724e7"
BASE_COMMIT = "57c7dcb8302bce6f007f8443965981fe60b12e23"
ROOT = Path(__file__).resolve().parents[2]
TRIGGER_PATHS = frozenset({
    PROFILE_PATH, "docs/governance/preflights/issue-540.json",
    "scripts/quality/issue521_successor.py",
})


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return predecessor._canonical_json(value).encode("utf-8")


def safe_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or "\\" in relative or str(path) != relative:
        raise ValueError("G1.PATH.INVALID")
    root = root.resolve()
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("G1.PATH.SYMLINK")
    return current


def read_bytes(root: Path, relative: str, maximum: int, *, exact: int | None = None) -> bytes:
    path = safe_path(root, relative)
    size = path.stat().st_size
    if not path.is_file() or size > maximum or (exact is not None and size != exact):
        raise ValueError("G1.ARTIFACT.SIZE")
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if len(data) != size:
        raise ValueError("G1.ARTIFACT.SIZE")
    return data


@dataclass(frozen=True)
class RuntimeConfig:
    git_timeout_seconds: float

    def __post_init__(self) -> None:
        value = self.git_timeout_seconds
        try:
            valid = type(value) in (int, float) and math.isfinite(value) and 0 < value <= threading.TIMEOUT_MAX
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError("G1.CONFIG.GIT_TIMEOUT")

    @classmethod
    def resolve(cls, profile: Mapping[str, Any], environment: Mapping[str, str] | None = None) -> RuntimeConfig:
        environment = os.environ if environment is None else environment
        raw = environment.get("NARRATWIN_G1_GIT_TIMEOUT_SECONDS")
        try:
            value = profile["limits"]["gitTimeoutSeconds"] if raw is None else float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("G1.CONFIG.GIT_TIMEOUT") from exc
        return cls(value)

    def effective(self) -> dict[str, float]:
        return {"gitTimeoutSeconds": self.git_timeout_seconds}


def git(root: Path, config: RuntimeConfig, *args: str) -> bytes:
    # Explicit environment prevents inherited Git object/config redirection.
    return subprocess.run(
        ["/usr/bin/git", *args], cwd=root, check=True, capture_output=True,
        timeout=config.git_timeout_seconds,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"},
    ).stdout


def registered_inputs(root: Path, profile_id: str = PROFILE_ID) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile_id != PROFILE_ID:
        raise ValueError("G1.REGISTRATION.UNKNOWN")
    raw = read_bytes(root, PROFILE_PATH, PROFILE_BYTES, exact=PROFILE_BYTES)
    if digest(raw) != PROFILE_SHA256:
        raise ValueError("G1.REGISTRATION.PROFILE")
    profile: dict[str, Any] = predecessor._load_json_text(raw.decode())
    # Raw identity makes unknown fields/types or self-consistent rehashes ineligible.
    if profile["baseCommit"] != BASE_COMMIT or profile["profileId"] != profile_id:
        raise ValueError("G1.REGISTRATION.IDENTITY")
    raw = read_bytes(root, profile["preflightPath"], PREFLIGHT_BYTES, exact=PREFLIGHT_BYTES)
    if digest(raw) != PREFLIGHT_SHA256:
        raise ValueError("G1.REGISTRATION.PREFLIGHT")
    preflight: dict[str, Any] = predecessor._load_json_text(raw.decode())
    return profile, preflight


def verify_inputs(root: Path, profile: dict[str, Any], config: RuntimeConfig) -> None:
    raw = git(root, config, "show", f"{PREFLIGHT_COMMIT}:{profile['preflightPath']}")
    if digest(raw) != PREFLIGHT_SHA256:
        raise ValueError("G1.REGISTRATION.FIRST_BLOB")
    if git(root, config, "rev-parse", f"{PREFLIGHT_COMMIT}^").decode().strip() != BASE_COMMIT:
        raise ValueError("G1.REGISTRATION.BASE")
    for item in profile["predecessorArtifacts"]:
        raw = read_bytes(root, item["path"], item["byteCount"], exact=item["byteCount"])
        if digest(raw) != item["sha256"]:
            raise ValueError("G1.PREDECESSOR.IDENTITY")
    failures = predecessor.validate_repository(root, certification=False)
    if failures:
        raise ValueError("G1.PREDECESSOR.INVALID:" + ",".join(failures))


def derive_mapping(root: Path, profile: dict[str, Any], config: RuntimeConfig) -> dict[str, Any]:
    mapping = predecessor.decode_mapping_artifact(predecessor._load_json(root / predecessor.MAPPING_PATH))
    source_spec = profile["source"]
    source = next(item for item in mapping["sources"] if item["sourceId"] == source_spec["sourceId"])
    if any(source[key] != value for key, value in source_spec.items()):
        raise ValueError("G1.SOURCE.IDENTITY")
    raw = git(root, config, "show", f"{source_spec['sourceCommit']}:{source_spec['repositoryPath']}")
    blob = git(root, config, "rev-parse", f"{source_spec['sourceCommit']}:{source_spec['repositoryPath']}").decode().strip()
    if digest(raw) != source_spec["contentSha256"] or blob != source_spec["sourceGitBlob"]:
        raise ValueError("G1.SOURCE.BYTES")
    atoms = predecessor._atoms(source["sourceId"], source["atomizer"], raw)
    partition = mapping["repositorySemanticDecisionPartition"]
    entry = next(item for item in partition["sources"] if item[0] == source["sourceId"])
    vector = list(entry[4])
    rows = {row["requirementId"]: row for row in mapping["rows"]}
    for correction in profile["corrections"]:
        index = correction["zeroBasedVectorIndex"]
        atom = atoms[index]
        row = rows[correction["requirementId"]]
        if (atom.atom_id != correction["sourceAtomId"] or row["sourceAtomId"] != atom.atom_id
                or row["sourceSpan"] != correction["sourceSpan"] or vector[index] != correction["fromCode"]):
            raise ValueError("G1.CORRECTION.COORDINATE")
        vector[index] = correction["toCode"]
    entry[4] = "".join(vector)
    entry[5] = digest(canonical(entry[:-1]))
    partition["classCounts"] = {name: 0 for name in partition["classCounts"]}
    for item in partition["sources"]:
        for code in item[4]:
            partition["classCounts"][partition["classCodes"][code]] += 1
    partition["orderedSourceDecisionSha256"] = digest(canonical([item[5] for item in partition["sources"]]))
    partition["partitionSha256"] = digest(canonical({k: v for k, v in partition.items() if k != "partitionSha256"}))
    classes = {atom.atom_id: partition["classCodes"][code] for atom, code in zip(atoms, vector, strict=True)}
    source["semanticCoverage"] = predecessor._semantic_coverage(atoms, source["authorityLifecycle"], source["coverageMode"], classes)
    removed = {item["requirementId"] for item in profile["corrections"]}
    mapping["rows"] = [row for row in mapping["rows"] if row["requirementId"] not in removed]
    context_hashes = {member["sourceAtomId"]: member["contextChainSha256"] for group in mapping["semanticDuplicateCensus"]["groups"] for member in group["members"]}
    mapping["semanticDuplicateCensus"] = predecessor.semantic_duplicate_census(mapping["rows"], context_hashes)
    counts = {
        "mappingRows": len(mapping["rows"]),
        "repositoryOwnerRows": sum(not row["sourceKind"].startswith("EXTERNAL_") for row in mapping["rows"]),
        "externalRows": sum(row["sourceKind"].startswith("EXTERNAL_") for row in mapping["rows"]),
        "normativeRequirements": partition["classCounts"]["NORMATIVE_REQUIREMENT"],
        "references": partition["classCounts"]["REFERENCE"],
        "duplicateGroups": mapping["semanticDuplicateCensus"]["groupCount"],
        "duplicateOccurrences": mapping["semanticDuplicateCensus"]["occurrenceCount"],
        "duplicateExcess": mapping["semanticDuplicateCensus"]["excessOccurrenceCount"],
    }
    if counts != profile["expectedCounts"]["successor"]:
        raise ValueError("G1.CORRECTION.COUNTS")
    return mapping


def derive_artifacts(root: Path, profile: dict[str, Any], config: RuntimeConfig, generation: RuntimeConfig) -> dict[str, bytes]:
    mapping = derive_mapping(root, profile, config)
    schema = predecessor._load_json(root / predecessor.MAPPING_SCHEMA_PATH)
    properties = schema["$defs"]["repositorySemanticDecisionPartition"]["properties"]
    properties["partitionSha256"]["const"] = mapping["repositorySemanticDecisionPartition"]["partitionSha256"]
    properties["classCounts"]["const"] = copy.deepcopy(mapping["repositorySemanticDecisionPartition"]["classCounts"])
    rendered = predecessor.render_mapping(mapping).encode()
    failures = predecessor._schema_instance_failures(predecessor._load_json_text(rendered.decode()), schema, definition="SupersetMappingV2Root", failure_code="G1.SCHEMA.INSTANCE")
    if failures:
        raise ValueError(",".join(failures))
    schema_bytes = canonical(schema) + b"\n"
    binding = predecessor._load_json(root / predecessor.BINDING_PATH)
    outputs = profile["outputs"]
    binding.update(controllerIssue=profile["issueNumber"], bootstrapBranch=profile["branch"], mappingPath=outputs["mapping"], mappingSchemaPath=outputs["mappingSchema"])
    binding["artifactHashes"].update(mappingSha256=digest(rendered), mappingSchemaSha256=digest(schema_bytes))
    binding["artifactShape"].update(mappingBytes=len(rendered), mappingRows=len(mapping["rows"]), mappingSchemaBytes=len(schema_bytes))
    receipt = mapping["externalSemanticCorrectionOverlay"]["exhaustiveReview"]
    lineage = {
        "schemaVersion": "G1BibliographyIntegrationLineageV1", "profileId": PROFILE_ID,
        "profileSha256": PROFILE_SHA256, "firstPreflightSha256": PREFLIGHT_SHA256,
        "baseCommit": BASE_COMMIT, "firstPreflightCommit": PREFLIGHT_COMMIT,
        "proposalState": "PENDING", "authorityEffect": "NONE", "localVerdict": "STRUCTURAL_PENDING",
        "predecessorArtifacts": profile["predecessorArtifacts"],
        "predecessorCounts": profile["expectedCounts"]["predecessor"],
        "successorCounts": profile["expectedCounts"]["successor"],
        "orderedRequirementSha256": predecessor.ordered_requirement_digest(mapping),
        "repositoryPartitionSha256": mapping["repositorySemanticDecisionPartition"]["partitionSha256"],
        "contextPartitionSha256": mapping["repositoryContextDecisionPartition"]["partitionSha256"],
        "externalSemanticInput": {"role": "HISTORICAL_PREDECESSOR_INPUT_ONLY", "receiptSha256": digest(canonical(receipt)), "successorCertification": "PENDING", "legacyValidationTransferred": False},
        "effectiveGenerationConfiguration": generation.effective(),
        "inheritedPredecessorConfiguration": "UNCHANGED_LEGACY_GIT_LIMITS",
        "operationalAuthority": profile["operationalAuthority"],
    }
    artifacts = {outputs["mapping"]: rendered, outputs["mappingSchema"]: schema_bytes, outputs["binding"]: canonical(binding) + b"\n", outputs["integrationLineage"]: canonical(lineage) + b"\n"}
    if len(rendered) >= profile["limits"]["maximumMappingBytesExclusive"] or sum(map(len, artifacts.values())) > profile["limits"]["maximumGeneratedBytes"]:
        raise ValueError("G1.ARTIFACT.BUDGET")
    return artifacts


def validate_repository(root: Path, *, config: RuntimeConfig | None = None, profile_id: str = PROFILE_ID) -> list[str]:
    try:
        profile, _ = registered_inputs(root, profile_id)
        effective = RuntimeConfig.resolve(profile) if config is None else config
        if type(effective) is not RuntimeConfig:
            raise ValueError("G1.CONFIG.TYPE")
        verify_inputs(root, profile, effective)
        lineage_raw = read_bytes(root, profile["outputs"]["integrationLineage"], profile["limits"]["maximumDescriptorBytes"])
        lineage = predecessor._load_json_text(lineage_raw.decode())
        generation_record = lineage["effectiveGenerationConfiguration"]
        if not isinstance(generation_record, dict) or set(generation_record) != {"gitTimeoutSeconds"}:
            raise ValueError("G1.CONFIG.GENERATION")
        generation = RuntimeConfig(generation_record["gitTimeoutSeconds"])
        expected = derive_artifacts(root, profile, effective, generation)
        for path, data in expected.items():
            maximum = profile["limits"]["maximumMappingBytesExclusive"] - 1 if path == profile["outputs"]["mapping"] else profile["limits"]["maximumDescriptorBytes"]
            if read_bytes(root, path, maximum) != data:
                return ["G1.SUCCESSOR.DERIVATION:" + path]
        print(predecessor._canonical_json({"profileId": PROFILE_ID, "profileSha256": PROFILE_SHA256, "firstPreflightSha256": PREFLIGHT_SHA256, "result": "STRUCTURAL_PENDING", "effectiveVerificationConfiguration": effective.effective(), "effectiveGenerationConfiguration": generation.effective(), "inheritedPredecessorConfiguration": "UNCHANGED_LEGACY_GIT_LIMITS", "privateAvailability": "NOT_CHECKED", "semanticAcceptance": "NOT_GRANTED"}))
        return []
    except (OSError, ValueError, KeyError, TypeError, StopIteration, IndexError, subprocess.SubprocessError) as exc:
        # Do not print subprocess output, paths outside the governed packet or secrets.
        return [str(exc) if isinstance(exc, ValueError) and str(exc).startswith("G1.") else "G1.VERIFICATION.UNAVAILABLE"]


def generate(root: Path, *, profile_id: str = PROFILE_ID) -> None:
    profile, _ = registered_inputs(root, profile_id)
    config = RuntimeConfig.resolve(profile)
    verify_inputs(root, profile, config)
    artifacts = derive_artifacts(root, profile, config, config)
    # Check every destination before the first write; generation is an explicit action.
    destinations = {safe_path(root, path): data for path, data in artifacts.items()}
    for path, data in destinations.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(predecessor._canonical_json({"generatedBytes": sum(map(len, artifacts.values())), "result": "STRUCTURAL_PENDING", "effectiveGenerationConfiguration": config.effective()}))


def successor_scope(root: Path, branch: str) -> list[str]:
    """Use the registered issue manifest, including clean push and PR checkouts."""
    try:
        profile, artifact = registered_inputs(root)
        config = RuntimeConfig.resolve(profile)
        if branch != profile["branch"]:
            return ["G1.SCOPE.BRANCH"]
        def run_git(*args: str) -> bytes:
            return git(root, config, *args)
        head = run_git("rev-parse", "HEAD").decode().strip()
        base = profile["baseCommit"]
        run_git("merge-base", "--is-ancestor", base, head)
        dirty = bool(run_git("status", "--porcelain", "--untracked-files=all"))
        hosted = os.environ.get("GITHUB_ACTIONS") == "true"
        if hosted and dirty:
            return ["G1.SCOPE.HOSTED_DIRTY"]
        findings = validate_governance_preflight_repository(
            root, base_sha=base, head_sha=head, issue_number=profile["issueNumber"], branch=branch,
        )
        if dirty and not hosted:
            findings = [item for item in findings if item.code != "GPF.SCOPE.REQUIRED_NOT_CHANGED"]
        if findings:
            return [item.code for item in findings]
        args = ["diff", "--no-renames", "--numstat", "-z", base]
        if not dirty:
            args.append(head)
        charges: dict[str, int] = {}
        for row in run_git(*args, "--").split(b"\0"):
            if row:
                added, removed, path = row.decode().split("\t", 2)
                charges[path] = int(added) + int(removed)
        if dirty:
            for raw_path in run_git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
                if raw_path:
                    relative = raw_path.decode()
                    if relative not in artifact["scope"]["required"]:
                        return ["G1.SCOPE.EXTRA_PATH"]
                    data = safe_path(root, relative).read_bytes()
                    if b"\0" in data:
                        return ["G1.SCOPE.BINARY"]
                    charges[relative] = len(data.decode().splitlines())
        failures = successor_budget_failures(artifact, charges, branch, profile["issueNumber"])
        for relative in charges:
            if not safe_path(root, relative).is_file():
                failures.append("G1.SCOPE.MISSING_FILE")
        print(json.dumps({"scopeMode": "WORKTREE_CHECK_ONLY" if dirty else "COMMITTED_SCOPE_CHECK", "chargedLines": sum(charges.values()), "effectiveConfiguration": config.effective()}))
        return failures
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return ["G1.SCOPE.UNAVAILABLE"]


def successor_budget_failures(artifact: dict[str, Any], charges: dict[str, int], branch: str, issue: int) -> list[str]:
    findings = validate_governance_preflight(artifact, context={"issue_number": issue, "branch": branch, "changed_files": list(charges)})
    if findings:
        return [item.code for item in findings]
    budget = artifact["change_budget"]
    limits = budget["per_file_charged_lines"]
    if set(charges) != set(limits) or artifact["scope"]["required"] != artifact["scope"]["allowed_prefixes"]:
        return ["G1.SCOPE.EXACT_PATHS"]
    if any(type(value) is not int or value < 0 for value in charges.values()):
        return ["G1.SCOPE.UNCOUNTABLE"]
    if any(charges[path] > limits[path] for path in charges):
        return ["G1.SCOPE.FILE_BUDGET"]
    if sum(charges.values()) > budget["maximum_additions_plus_deletions"]:
        return ["G1.SCOPE.TOTAL_BUDGET"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=PROFILE_ID)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    if args.generate:
        try:
            generate(ROOT, profile_id=args.profile)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            print("G1.GENERATION.FAILED")
            return 1
        return 0
    failures = validate_repository(ROOT, profile_id=args.profile)
    for failure in failures:
        print(failure)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
