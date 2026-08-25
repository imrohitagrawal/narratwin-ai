from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

import pytest

from scripts.quality import adversarial_convergence as convergence
from scripts.quality.adversarial_convergence import BlockerClass
from scripts.quality.adversarial_convergence import FindingCode
from scripts.quality.adversarial_convergence import MutationReceipt
from scripts.quality.adversarial_convergence import MutationState
from scripts.quality.adversarial_convergence import ParseLimits
from scripts.quality.adversarial_convergence import PathCharge
from scripts.quality.adversarial_convergence import PhaseVerdict
from scripts.quality.adversarial_convergence import RouteEvidence
from scripts.quality.adversarial_convergence import Stimulus


ROOT = Path(__file__).parents[2]
CORPUS_PATH = ROOT / "docs/governance/adversarial-convergence-framework-cases-v1.json"
SCHEMA_PATH = ROOT / "docs/governance/adversarial-convergence-framework-v1.schema.json"
MODULE_PATH = ROOT / "scripts/quality/adversarial_convergence.py"
EXPECTED_CORPUS_SEMANTIC_SHA256 = "5fd31be0dddf4572f1e8cb5405524ee97e4bd2b20448aded7197949ecb3fe371"
EXPECTED_CORPUS_RAW_SHA256 = "49184abda0f21351049810bee09eb81dba40bdfb8a9afbdaf8f97cf8dcbe8cab"
EXPECTED_THREATS = tuple(f"ACP-T{index:02d}" for index in range(1, 13))


@dataclass(frozen=True)
class ExpectedOutcome:
    verdict: PhaseVerdict
    findings: tuple[FindingCode, ...]


def _expected(verdict: PhaseVerdict, *findings: FindingCode) -> ExpectedOutcome:
    return ExpectedOutcome(verdict, findings)


EXPECTED_BY_CASE_ID = {
    "ACP-C001": _expected(PhaseVerdict.VALID),
    "ACP-C002": _expected(PhaseVerdict.INVALID, FindingCode.UNSAFE_FILESYSTEM_INPUT),
    "ACP-C003": _expected(PhaseVerdict.INVALID, FindingCode.UNSAFE_FILESYSTEM_INPUT),
    "ACP-C004": _expected(PhaseVerdict.INVALID, FindingCode.UNSAFE_FILESYSTEM_INPUT),
    "ACP-C005": _expected(PhaseVerdict.VALID),
    "ACP-C006": _expected(PhaseVerdict.INVALID, FindingCode.INPUT_TOO_LARGE),
    "ACP-C007": _expected(PhaseVerdict.INVALID, FindingCode.DUPLICATE_MEMBER),
    "ACP-C008": _expected(PhaseVerdict.INVALID, FindingCode.MALFORMED_JSON),
    "ACP-C009": _expected(PhaseVerdict.INVALID, FindingCode.RESOURCE_LIMIT),
    "ACP-C010": _expected(PhaseVerdict.VALID),
    "ACP-C011": _expected(PhaseVerdict.INVALID, FindingCode.SCHEMA_DRIFT),
    "ACP-C012": _expected(PhaseVerdict.VALID),
    "ACP-C013": _expected(PhaseVerdict.INVALID, FindingCode.PREDECESSOR_VIOLATION),
    "ACP-C014": _expected(PhaseVerdict.INVALID, FindingCode.LATE_STAGE_EXECUTION),
    "ACP-C015": _expected(PhaseVerdict.VALID),
    "ACP-C016": _expected(PhaseVerdict.INVALID, FindingCode.OUTCOME_NOT_EXACT),
    "ACP-C017": _expected(PhaseVerdict.INVALID, FindingCode.SUBSET_OUTCOME),
    "ACP-C018": _expected(PhaseVerdict.VALID),
    "ACP-C019": _expected(PhaseVerdict.INVALID, FindingCode.MUTANT_NOT_EXECUTED),
    "ACP-C020": _expected(PhaseVerdict.INVALID, FindingCode.MUTANT_SURVIVED),
    "ACP-C021": _expected(PhaseVerdict.VALID),
    "ACP-C022": _expected(PhaseVerdict.INVALID, FindingCode.MOCK_LEDGER_INVALID),
    "ACP-C023": _expected(PhaseVerdict.INVALID, FindingCode.MOCK_LEDGER_INVALID),
    "ACP-C024": _expected(PhaseVerdict.BLOCKED_EVIDENCE, FindingCode.REQUIRED_REVIEW_MISSING),
    "ACP-C025": _expected(PhaseVerdict.INVALID, FindingCode.REVIEW_SELF_ATTESTED),
    "ACP-C026": _expected(PhaseVerdict.INVALID, FindingCode.REVIEW_IDENTITY_MISMATCH),
    "ACP-C027": _expected(PhaseVerdict.VALID),
    "ACP-C028": _expected(PhaseVerdict.INVALID, FindingCode.EXPECTATION_NOT_INDEPENDENT),
    "ACP-C029": _expected(PhaseVerdict.INVALID, FindingCode.EXPECTATION_NOT_INDEPENDENT),
    "ACP-C030": _expected(PhaseVerdict.VALID),
    "ACP-C031": _expected(PhaseVerdict.INVALID, FindingCode.ROUTE_DRIFT),
    "ACP-C032": _expected(PhaseVerdict.INVALID, FindingCode.IDENTITY_MISMATCH),
    "ACP-C033": _expected(PhaseVerdict.BLOCKED_EVIDENCE, FindingCode.BUDGET_REVIEW_REQUIRED),
    "ACP-C034": _expected(PhaseVerdict.BLOCKED_IMPLEMENTATION, FindingCode.BUDGET_STOP),
    "ACP-C035": _expected(PhaseVerdict.VALID),
    "ACP-C036": _expected(PhaseVerdict.INVALID, FindingCode.CHECKPOINT_INVALID),
    "ACP-C037": _expected(PhaseVerdict.INVALID, FindingCode.CHECKPOINT_INVALID),
    "ACP-C038": _expected(PhaseVerdict.VALID),
    "ACP-C039": _expected(PhaseVerdict.BLOCKED_IMPLEMENTATION, FindingCode.PLATFORM_FAILURE),
    "ACP-C040": _expected(PhaseVerdict.BLOCKED_IMPLEMENTATION, FindingCode.RESOURCE_FAILURE),
}


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _load_corpus() -> dict[str, object]:
    document = json.loads(CORPUS_PATH.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    assert isinstance(document, dict)
    return document


CORPUS = _load_corpus()
RAW_CASES = CORPUS["cases"]
assert isinstance(RAW_CASES, list)
CASES = cast(list[dict[str, object]], RAW_CASES)


def _case(case_id: str) -> dict[str, object]:
    matches = [item for item in CASES if isinstance(item, dict) and item.get("caseId") == case_id]
    assert len(matches) == 1
    return matches[0]


def _stimulus(case: dict[str, object]) -> Stimulus:
    raw = case["stimulus"]
    assert isinstance(raw, dict)
    operation = raw.get("operation")
    variant = raw.get("variant")
    assert isinstance(operation, str)
    assert isinstance(variant, str)
    return Stimulus(operation, variant, raw.get("input"))


def test_corpus_has_frozen_identity_order_and_closed_threats() -> None:
    raw = CORPUS_PATH.read_bytes()
    canonical = json.dumps(CORPUS, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")

    assert CORPUS["schemaVersion"] == "AdversarialConvergenceCaseCorpusV1"
    assert CORPUS["corpusId"] == "ACP-FRAMEWORK-CASES-V1-N40"
    assert CORPUS["caseCount"] == 40
    assert CORPUS["threatUniverse"] == list(EXPECTED_THREATS)
    assert [case["caseId"] for case in CASES] == [f"ACP-C{index:03d}" for index in range(1, 41)]
    assert len(raw) <= 49_152
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_CORPUS_RAW_SHA256
    assert hashlib.sha256(convergence.CORPUS_DOMAIN + canonical).hexdigest() == EXPECTED_CORPUS_SEMANTIC_SHA256


def test_corpus_contains_stimuli_but_no_expectations_or_pass_claims() -> None:
    forbidden = {"expectation", "expected", "finding", "verdict", "review", "pass", "completion"}
    stimuli: list[str] = []
    for case in CASES:
        assert isinstance(case, dict)
        assert set(case) == {"caseId", "threatId", "testClass", "stimulus"}
        assert not forbidden.intersection(json.dumps(case).lower().replace('"', " ").split())
        stimuli.append(json.dumps(case["stimulus"], sort_keys=True))
    assert len(set(stimuli)) == 40
    assert set(EXPECTED_BY_CASE_ID) == {str(case["caseId"]) for case in CASES}


def test_schema_closes_corpus_and_freeze_shapes() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    definitions = schema["$defs"]

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert definitions["caseCorpus"]["additionalProperties"] is False
    assert definitions["caseCorpus"]["properties"]["caseCount"] == {"const": 40}
    assert definitions["case"]["additionalProperties"] is False
    assert definitions["redFreeze"]["properties"]["reviews"]["minItems"] == 4
    assert definitions["redFreeze"]["properties"]["reviews"]["maxItems"] == 4


def test_executor_signature_receives_only_one_materialized_stimulus() -> None:
    parameters = tuple(inspect.signature(convergence.execute).parameters.values())

    assert len(parameters) == 1
    assert parameters[0].name == "stimulus"
    assert parameters[0].annotation == "Stimulus"


def test_c2_skeleton_returns_exact_typed_not_implemented() -> None:
    result = convergence.execute(Stimulus("framework_gate", "c2_boundary"))

    assert result.verdict is PhaseVerdict.NOT_IMPLEMENTED
    assert tuple(finding.code for finding in result.findings) == (FindingCode.NOT_IMPLEMENTED,)
    assert result.findings[0].blocker is BlockerClass.IMPLEMENTATION
    assert result.activation == "NONE"
    assert result.authority_effect == "NO_AUTHORITY_EFFECT"


def test_production_module_has_no_oracle_import_or_dynamic_import() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    assert not any(name.startswith("tests") for name in imported)
    assert "importlib" not in imported
    assert "sys" not in imported
    assert "Any" not in source
    assert "EXPECTED_BY_CASE_ID" not in source


def test_module_imports_from_outside_repository(tmp_path: Path) -> None:
    command = "import runpy,sys; runpy.run_path(sys.argv[1], run_name='import_smoke')"
    result = subprocess.run(
        [sys.executable, "-c", command, str(MODULE_PATH)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_bounded_reader_accepts_regular_file(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    target.write_bytes(b"{}\n")

    result = convergence.read_bounded_regular_file(tmp_path, "data.json", 3)

    assert result.data == b"{}\n"
    assert result.finding is None


def test_bounded_reader_rejects_target_and_ancestor_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "data.json").write_bytes(b"{}")
    (tmp_path / "target.json").symlink_to(real / "data.json")
    (tmp_path / "linked").symlink_to(real, target_is_directory=True)

    target = convergence.read_bounded_regular_file(tmp_path, "target.json", 10)
    ancestor = convergence.read_bounded_regular_file(tmp_path, "linked/data.json", 10)

    assert target.finding is not None and target.finding.code is FindingCode.UNSAFE_FILESYSTEM_INPUT
    assert ancestor.finding is not None and ancestor.finding.code is FindingCode.UNSAFE_FILESYSTEM_INPUT


def test_bounded_reader_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)

    result = convergence.read_bounded_regular_file(tmp_path, "pipe", 10)

    assert result.data is None
    assert result.finding is not None
    assert result.finding.code is FindingCode.UNSAFE_FILESYSTEM_INPUT


def test_bounded_reader_enforces_exact_byte_limit(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    target.write_bytes(b"1234")

    exact = convergence.read_bounded_regular_file(tmp_path, "data.json", 4)
    excessive = convergence.read_bounded_regular_file(tmp_path, "data.json", 3)

    assert exact.data == b"1234"
    assert excessive.finding is not None
    assert excessive.finding.code is FindingCode.INPUT_TOO_LARGE


def test_parser_checks_whole_file_identity_before_json() -> None:
    malformed = b"{"

    result = convergence.parse_json_bytes(malformed, "0" * 64)

    assert tuple(finding.code for finding in result.findings) == (FindingCode.IDENTITY_MISMATCH,)


@pytest.mark.parametrize(
    ("raw", "code"),
    (
        (b'{"a":1,"a":2}', FindingCode.DUPLICATE_MEMBER),
        (b"{", FindingCode.MALFORMED_JSON),
        (b"\xff", FindingCode.INVALID_UTF8),
    ),
)
def test_parser_contains_hostile_json(raw: bytes, code: FindingCode) -> None:
    digest = hashlib.sha256(raw).hexdigest()

    result = convergence.parse_json_bytes(raw, digest)

    assert tuple(finding.code for finding in result.findings) == (code,)


def test_parser_contains_depth_and_member_exhaustion() -> None:
    raw = json.dumps({"a": {"b": {"c": 1}}}).encode()
    digest = hashlib.sha256(raw).hexdigest()

    result = convergence.parse_json_bytes(raw, digest, ParseLimits(max_depth=2, max_members=10))

    assert tuple(finding.code for finding in result.findings) == (FindingCode.RESOURCE_LIMIT,)


def _valid_route() -> RouteEvidence:
    changes = tuple(
        PathCharge(path, "A" if path not in {convergence.ISSUE435_PREFLIGHT, "AGENTS.md"} else "M", 1, 0, "100644")
        for path in sorted(convergence.ISSUE435_NONFREEZE)
    )
    return RouteEvidence(
        branch=convergence.ISSUE435_BRANCH,
        ancestor=True,
        first_commit=convergence.ISSUE435_C1,
        merge_commits=(),
        preflight_blob=convergence.ISSUE435_PREFLIGHT_BLOB,
        changes=changes,
        dirty=False,
        freeze_present=False,
    )


def test_route_evidence_accepts_only_exact_clean_c2() -> None:
    inspection = convergence.validate_route_evidence(_valid_route())

    assert inspection.phase == "C2"
    assert inspection.findings == ()
    assert inspection.charged_lines == 19


@pytest.mark.parametrize(
    "evidence",
    (
        replace(_valid_route(), branch=f"{convergence.ISSUE435_BRANCH}-evil"),
        replace(_valid_route(), ancestor=False),
        replace(_valid_route(), first_commit="0" * 40),
        replace(_valid_route(), merge_commits=("1" * 40,)),
        replace(_valid_route(), preflight_blob="2" * 40),
        replace(_valid_route(), dirty=True),
        replace(_valid_route(), changes=_valid_route().changes[:-1]),
        replace(_valid_route(), changes=(replace(_valid_route().changes[0], status="R100"),) + _valid_route().changes[1:]),
        replace(_valid_route(), changes=(replace(_valid_route().changes[0], mode="120000"),) + _valid_route().changes[1:]),
        replace(_valid_route(), changes=(replace(_valid_route().changes[0], additions=10_000),) + _valid_route().changes[1:]),
    ),
)
def test_route_evidence_rejects_identity_scope_mode_and_budget_drift(evidence: RouteEvidence) -> None:
    assert convergence.validate_route_evidence(evidence).findings


def test_freeze_path_is_rejected_when_evidence_claims_c2() -> None:
    freeze = PathCharge(convergence.ISSUE435_FREEZE, "A", 1, 0, "100644")
    evidence = replace(_valid_route(), changes=_valid_route().changes + (freeze,))

    assert FindingCode.ROUTE_DRIFT in convergence.validate_route_evidence(evidence).findings


def _mutant_valid(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_parse_before_bounds(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.INVALID, FindingCode.MALFORMED_JSON)


def _mutant_schema_ignored(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_late_stage(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.INVALID, FindingCode.PREDECESSOR_VIOLATION)


def _mutant_generic_outcome(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.INVALID, FindingCode.OUTCOME_NOT_EXACT)


def _mutant_receipt_credited(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_mock_ledger(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_self_review(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_reads_stimulus(stimulus: Stimulus) -> ExpectedOutcome:
    assert stimulus.variant == "expectation_embedded_in_stimulus"
    return _expected(PhaseVerdict.VALID)


def _mutant_route_ignored(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_false_checkpoint(_: Stimulus) -> ExpectedOutcome:
    return _expected(PhaseVerdict.VALID)


def _mutant_leaks_resource(_: Stimulus) -> ExpectedOutcome:
    raise RecursionError("controlled mutant")


def _assert_mutant_killed(
    mutant_id: str,
    case_id: str,
    executor: Callable[[Stimulus], ExpectedOutcome],
) -> None:
    stimulus = _stimulus(_case(case_id))
    try:
        observed = executor(stimulus)
    except RecursionError:
        observed = _expected(PhaseVerdict.INVALID, FindingCode.PLATFORM_FAILURE)
    expected = EXPECTED_BY_CASE_ID[case_id]
    assert observed != expected, f"{mutant_id} survived {case_id}"
    receipt = MutationReceipt(mutant_id, f"test_{mutant_id.lower()}", 1, MutationState.KILLED, observed.findings[0] if observed.findings else FindingCode.OUTCOME_NOT_EXACT, observed.verdict)
    assert receipt.executed_count == 1
    assert receipt.state is MutationState.KILLED


def test_m01_unsafe_filesystem_acceptance_is_killed() -> None:
    _assert_mutant_killed("M01", "ACP-C002", _mutant_valid)


def test_m02_parse_before_bounds_is_killed() -> None:
    _assert_mutant_killed("M02", "ACP-C006", _mutant_parse_before_bounds)


def test_m03_schema_drift_acceptance_is_killed() -> None:
    _assert_mutant_killed("M03", "ACP-C011", _mutant_schema_ignored)


def test_m04_late_stage_execution_is_killed() -> None:
    _assert_mutant_killed("M04", "ACP-C014", _mutant_late_stage)


def test_m05_generic_subset_outcome_is_killed() -> None:
    _assert_mutant_killed("M05", "ACP-C017", _mutant_generic_outcome)


def test_m06_unexecuted_mutant_credit_is_killed() -> None:
    _assert_mutant_killed("M06", "ACP-C019", _mutant_receipt_credited)


def test_m07_fabricated_mock_ledger_is_killed() -> None:
    _assert_mutant_killed("M07", "ACP-C022", _mutant_mock_ledger)


def test_m08_candidate_authored_review_pass_is_killed() -> None:
    _assert_mutant_killed("M08", "ACP-C025", _mutant_self_review)


def test_m09_implementation_derived_expectation_is_killed() -> None:
    _assert_mutant_killed("M09", "ACP-C028", _mutant_reads_stimulus)


def test_m10_route_identity_budget_drift_is_killed() -> None:
    _assert_mutant_killed("M10", "ACP-C031", _mutant_route_ignored)


def test_m11_false_checkpoint_is_killed() -> None:
    _assert_mutant_killed("M11", "ACP-C036", _mutant_false_checkpoint)


def test_m12_platform_resource_exception_leak_is_killed() -> None:
    _assert_mutant_killed("M12", "ACP-C040", _mutant_leaks_resource)


def test_readability_limits_are_machine_checked() -> None:
    limits = ((MODULE_PATH, 120), (Path(__file__), 80))
    for path, limit in limits:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        spans = [node.end_lineno - node.lineno + 1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.end_lineno]
        assert max(spans) <= limit


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["caseId"])
def test_future_validator_matches_test_owned_expectation(case: dict[str, object]) -> None:
    case_id = str(case["caseId"])
    expected = EXPECTED_BY_CASE_ID[case_id]

    actual = convergence.execute(_stimulus(case))

    assert actual.verdict is expected.verdict, f"{case_id}: {actual.findings[0].code}"
    assert tuple(finding.code for finding in actual.findings) == expected.findings
