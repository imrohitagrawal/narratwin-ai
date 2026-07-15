from __future__ import annotations

import copy
import json
import random
import time
from dataclasses import dataclass
from typing import Any

import pytest

from scripts.governance_preflight_v1 import validate_governance_preflight


Artifact = dict[str, Any]
Context = dict[str, Any]

ISSUE_NUMBER = 172
BRANCH = "phase-1-closure-process-172-gpf-v1-offline-core"
RANDOM_SEEDS = tuple(range(172001, 172011))


@dataclass(frozen=True)
class MutationCase:
    test_id: str
    code: str


MUTATION_CASES = (
    MutationCase("required-objective", "GPF.SCHEMA.REQUIRED"),
    MutationCase("unknown-root", "GPF.SCHEMA.UNKNOWN"),
    MutationCase("issue-type", "GPF.SCHEMA.TYPE"),
    MutationCase("blank-objective", "GPF.SCHEMA.BLANK"),
    MutationCase("version-const", "GPF.SCHEMA.VERSION"),
    MutationCase("objective-limit", "GPF.SCHEMA.LIMIT"),
    MutationCase("scope-list-limit", "GPF.SCHEMA.LIMIT"),
    MutationCase("path-limit", "GPF.SCHEMA.LIMIT"),
    MutationCase("duplicate-required", "GPF.SCHEMA.DUPLICATE"),
    MutationCase("parent-segment", "GPF.PATH.INVALID"),
    MutationCase("absolute-path", "GPF.PATH.INVALID"),
    MutationCase("required-not-allowed", "GPF.SCOPE.REQUIRED_NOT_ALLOWED"),
    MutationCase("required-forbidden", "GPF.SCOPE.REQUIRED_FORBIDDEN"),
    MutationCase("required-not-changed", "GPF.SCOPE.REQUIRED_NOT_CHANGED"),
    MutationCase("change-not-allowed", "GPF.SCOPE.CHANGE_NOT_ALLOWED"),
    MutationCase("change-forbidden", "GPF.SCOPE.CHANGE_FORBIDDEN"),
    MutationCase("status-decision", "GPF.STATUS.DECISION_INVALID"),
    MutationCase("status-required", "GPF.STATUS.REQUIRED_MISSING"),
    MutationCase("status-allowed", "GPF.STATUS.ALLOWED_MISSING"),
    MutationCase("issue-binding", "GPF.BINDING.ISSUE_MISMATCH"),
    MutationCase("branch-binding", "GPF.BINDING.BRANCH_MISMATCH"),
)


def _artifact() -> Artifact:
    return {
        "schema_version": "GovernancePreflightV1",
        "issue_number": ISSUE_NUMBER,
        "branch": BRANCH,
        "objective": "Prove a small offline governance preflight validator.",
        "status_decision": "update-minimally",
        "scope": {
            "required": ["docs/STATUS.md", "scripts/example.py"],
            "allowed_prefixes": ["docs/STATUS.md", "scripts/", "tests/unit/"],
            "forbidden": ["backend/", "frontend/"],
        },
    }


def _context() -> Context:
    return {
        "issue_number": ISSUE_NUMBER,
        "branch": BRANCH,
        "changed_files": [
            "docs/STATUS.md",
            "scripts/example.py",
            "tests/unit/test_example.py",
        ],
    }


def _codes(artifact: Artifact, context: Context) -> list[str]:
    return [
        finding.code
        for finding in validate_governance_preflight(artifact, context=context)
    ]


def _baseline_for(case: MutationCase) -> tuple[Artifact, Context]:
    artifact = _artifact()
    if case.test_id == "scope-list-limit":
        prefixes = artifact["scope"]["allowed_prefixes"]
        prefixes.extend(f"unused/prefix-{index}/" for index in range(3, 128))
    return artifact, _context()


def _apply_mutation(case: MutationCase, artifact: Artifact, context: Context) -> None:
    scope = artifact["scope"]
    test_id = case.test_id

    if test_id == "required-objective":
        del artifact["objective"]
    elif test_id == "unknown-root":
        artifact["unexpected"] = True
    elif test_id == "issue-type":
        artifact["issue_number"] = "172"
    elif test_id == "blank-objective":
        artifact["objective"] = " "
    elif test_id == "version-const":
        artifact["schema_version"] = "GovernancePreflightV2"
    elif test_id == "objective-limit":
        artifact["objective"] = "x" * 2001
    elif test_id == "scope-list-limit":
        scope["allowed_prefixes"].append("unused/prefix-128/")
    elif test_id == "path-limit":
        scope["required"][1] = f"scripts/{'x' * 502}.py"
    elif test_id == "duplicate-required":
        scope["required"].append("scripts/example.py")
    elif test_id == "parent-segment":
        scope["required"][1] = "../escape.py"
    elif test_id == "absolute-path":
        scope["required"][1] = "/tmp/escape.py"
    elif test_id == "required-not-allowed":
        scope["allowed_prefixes"][1] = "tools/"
    elif test_id == "required-forbidden":
        scope["forbidden"].append("scripts/example.py")
    elif test_id == "required-not-changed":
        context["changed_files"].remove("scripts/example.py")
    elif test_id == "change-not-allowed":
        context["changed_files"].append("tools/unapproved.py")
    elif test_id == "change-forbidden":
        context["changed_files"].append("backend/forbidden.py")
    elif test_id == "status-decision":
        artifact["status_decision"] = "skip"
    elif test_id == "status-required":
        scope["required"].remove("docs/STATUS.md")
    elif test_id == "status-allowed":
        scope["allowed_prefixes"].remove("docs/STATUS.md")
    elif test_id == "issue-binding":
        context["issue_number"] = 173
    elif test_id == "branch-binding":
        context["branch"] = "phase-1-closure-process-999-wrong"
    else:  # pragma: no cover - the table and dispatcher must stay synchronized
        raise AssertionError(f"unhandled mutation case: {test_id}")


def test_exact_contract_baseline_has_zero_findings() -> None:
    assert _codes(_artifact(), _context()) == []


@pytest.mark.parametrize("case", MUTATION_CASES, ids=lambda case: case.test_id)
def test_each_single_mutation_returns_only_its_stable_code(
    case: MutationCase,
) -> None:
    baseline_artifact, baseline_context = _baseline_for(case)
    assert _codes(baseline_artifact, baseline_context) == []

    mutated_artifact = copy.deepcopy(baseline_artifact)
    mutated_context = copy.deepcopy(baseline_context)
    _apply_mutation(case, mutated_artifact, mutated_context)

    assert _codes(mutated_artifact, mutated_context) == [case.code]


@pytest.mark.parametrize(
    ("test_id", "code", "mutate"),
    (
        (
            "control-character-path",
            "GPF.PATH.INVALID",
            lambda artifact, _context: artifact["scope"]["required"].__setitem__(
                1, "scripts/bad\nname.py"
            ),
        ),
        (
            "changed-file-type-confusion",
            "GPF.SCHEMA.TYPE",
            lambda _artifact, context: context["changed_files"].__setitem__(1, 172),
        ),
        (
            "serialized-artifact-limit",
            "GPF.SCHEMA.LIMIT",
            lambda artifact, _context: artifact.__setitem__("objective", "x" * 65537),
        ),
    ),
)
def test_untrusted_input_mutations_fail_closed_with_one_code(
    test_id: str,
    code: str,
    mutate: Any,
) -> None:
    del test_id
    baseline_artifact = _artifact()
    baseline_context = _context()
    assert _codes(baseline_artifact, baseline_context) == []

    mutated_artifact = copy.deepcopy(baseline_artifact)
    mutated_context = copy.deepcopy(baseline_context)
    mutate(mutated_artifact, mutated_context)

    assert _codes(mutated_artifact, mutated_context) == [code]


def test_valid_boundaries_unicode_and_nested_paths() -> None:
    artifact = _artifact()
    context = _context()
    artifact["objective"] = "界"
    artifact["scope"]["required"][1] = f"scripts/{'x' * 501}.py"
    context["changed_files"][1] = artifact["scope"]["required"][1]
    artifact["scope"]["allowed_prefixes"].extend(
        f"unused/prefix-{index}/" for index in range(3, 128)
    )
    artifact["scope"]["forbidden"].extend(
        f"forbidden/prefix-{index}/" for index in range(2, 128)
    )

    assert len(artifact["scope"]["required"][1]) == 512
    assert len(artifact["scope"]["allowed_prefixes"]) == 128
    assert len(artifact["scope"]["forbidden"]) == 128
    assert _codes(artifact, context) == []

    artifact["objective"] = "界" * 2000
    artifact["scope"]["required"][1] = "scripts/nested/path/example.py"
    context["changed_files"][1] = "scripts/nested/path/example.py"
    assert _codes(artifact, context) == []


def test_ordering_and_json_round_trip_preserve_zero_findings() -> None:
    artifact = _artifact()
    context = _context()
    reordered_artifact = json.loads(json.dumps(artifact, sort_keys=True))
    reordered_artifact["scope"]["required"].reverse()
    reordered_artifact["scope"]["allowed_prefixes"].reverse()
    reordered_artifact["scope"]["forbidden"].reverse()
    reordered_context = copy.deepcopy(context)
    reordered_context["changed_files"].reverse()

    assert _codes(artifact, context) == []
    assert _codes(reordered_artifact, reordered_context) == []


def test_ordering_permutations_preserve_exact_finding_vector() -> None:
    artifact = _artifact()
    context = _context()
    context["changed_files"].extend(
        ["tools/unapproved.py", "backend/forbidden.py"]
    )
    expected = _codes(artifact, context)

    permuted_artifact = copy.deepcopy(artifact)
    permuted_context = copy.deepcopy(context)
    permuted_artifact["scope"]["allowed_prefixes"].reverse()
    permuted_artifact["scope"]["forbidden"].reverse()
    permuted_context["changed_files"].reverse()

    assert expected != []
    assert _codes(permuted_artifact, permuted_context) == expected


def test_unused_allowed_prefix_preserves_zero_findings() -> None:
    artifact = _artifact()
    context = _context()
    assert _codes(artifact, context) == []

    artifact["scope"]["allowed_prefixes"].append("unused/")
    assert _codes(artifact, context) == []


@pytest.mark.parametrize("invalid_path", ("scripts/./example.py", "scripts/a/../b.py"))
def test_dot_segments_are_rejected_without_normalization(invalid_path: str) -> None:
    artifact = _artifact()
    context = _context()
    assert _codes(artifact, context) == []

    artifact["scope"]["required"][1] = invalid_path
    assert _codes(artifact, context) == ["GPF.PATH.INVALID"]


@pytest.mark.parametrize("seed", RANDOM_SEEDS)
def test_seeded_valid_and_single_fault_documents(seed: int) -> None:
    rng = random.Random(seed)
    started = time.perf_counter()

    for case_index in range(50):
        artifact = _artifact()
        context = _context()
        artifact["objective"] = f"Valid generated case {seed}:{case_index} 界"
        if rng.choice((False, True)):
            artifact["scope"]["allowed_prefixes"].reverse()
            context["changed_files"].reverse()
        assert _codes(artifact, context) == [], (
            f"seed={seed} case={case_index} artifact={json.dumps(artifact)}"
        )

    for case_index in range(50):
        case = rng.choice(MUTATION_CASES)
        baseline_artifact, baseline_context = _baseline_for(case)
        assert _codes(baseline_artifact, baseline_context) == []
        artifact = copy.deepcopy(baseline_artifact)
        context = copy.deepcopy(baseline_context)
        _apply_mutation(case, artifact, context)
        actual = _codes(artifact, context)
        assert actual == [case.code], (
            f"seed={seed} case={case_index} mutation={case.test_id} "
            f"artifact={json.dumps(artifact)} context={json.dumps(context)} "
            f"actual={actual}"
        )

    assert time.perf_counter() - started < 10.0


def test_maximum_fixture_completes_within_hard_ceiling() -> None:
    artifact = _artifact()
    context = _context()
    required = ["docs/STATUS.md"] + [
        f"scripts/path-{index:03d}.py" for index in range(1, 128)
    ]
    artifact["objective"] = "x" * 2000
    artifact["scope"]["required"] = required
    artifact["scope"]["allowed_prefixes"].extend(
        f"unused/prefix-{index}/" for index in range(3, 128)
    )
    artifact["scope"]["forbidden"].extend(
        f"forbidden/prefix-{index}/" for index in range(2, 128)
    )
    context["changed_files"] = required

    started = time.perf_counter()
    assert _codes(artifact, context) == []
    assert time.perf_counter() - started < 1.0
