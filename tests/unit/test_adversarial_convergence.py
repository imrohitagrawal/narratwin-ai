from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


ROOT = Path(__file__).parents[2]
CORPUS_PATH = ROOT / "docs/governance/adversarial-convergence-framework-cases-v1.json"
SCHEMA_PATH = ROOT / "docs/governance/adversarial-convergence-framework-v1.schema.json"
MODULE_PATH = ROOT / "scripts/quality/adversarial_convergence.py"
FREEZE_PATH = ROOT / "docs/governance/adversarial-convergence-red-freeze-v1.json"
ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"
ISSUE435_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
CORPUS_DOMAIN = b"NARRATWIN-ADVERSARIAL-CONVERGENCE-CASES-V1\0"
RAW_SHA256 = "59581f0530b9b56b68e9bfc313497b22d1be2ce371d0cb2c64ea2b3c01dc6a75"
SEMANTIC_SHA256 = "3b2a0c4b3b13cf6ab71ec4e7a3dd4e3566a0c8195e3c7bed6bf956575e5f9fc6"
STAGES = ("BOUNDS", "PARSE", "SCHEMA", "CANONICAL_IDENTITY", "INDEPENDENT_TRUST", "AUTHORIZATION", "GRAPH_CONFLICT", "PHASE_VERDICT")
STATE = {"A": "ACCEPTED", "R": "REJECTED", "N": "NOT_APPLICABLE", "X": "NOT_REACHED"}
JUSTIFICATION = {"A": "contract satisfied", "R": "rejected", "N": "not applicable", "X": "blocked by rejected predecessor"}
THREATS = tuple(f"ACP-T{number:02d}" for number in range(1, 13))
KINDS = ("FILESYSTEM", "JSON", "DOCUMENT", "PIPELINE", "OUTCOME", "MUTATION_SET", "EXECUTION_LEDGER", "REVIEWS", "EXPECTATION_BOUNDARY", "ROUTE", "CHECKPOINT", "RESOURCE")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate member: {key}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    assert isinstance(value, dict)
    return value


CORPUS = _load(CORPUS_PATH)
RAW_CASES = CORPUS["cases"]
assert isinstance(RAW_CASES, list)
CASES = cast(list[dict[str, object]], RAW_CASES)


# verdict, ordered (stage, code, location, blocker) findings, exact eight-stage trace.
SPEC: dict[str, tuple[str, tuple[tuple[str, str, str, str], ...], str]] = {
    "ACP-C001": ("VALID", (), "ANNNNNNA"),
    "ACP-C002": ("INVALID", (("BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds/0", "IMPLEMENTATION"),), "RXXXXXXX"),
    "ACP-C003": ("INVALID", (("BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds/1", "IMPLEMENTATION"),), "RXXXXXXX"),
    "ACP-C004": ("INVALID", (("BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds/1", "IMPLEMENTATION"),), "RXXXXXXX"),
    "ACP-C005": ("VALID", (), "AANANNNA"),
    "ACP-C006": ("INVALID", (("BOUNDS", "ACP.BOUNDS.INPUT_TOO_LARGE", "/payload/raw", "IMPLEMENTATION"),), "RXXXXXXX"),
    "ACP-C007": ("INVALID", (("PARSE", "ACP.PARSE.DUPLICATE_MEMBER", "/payload/raw", "IMPLEMENTATION"),), "ARXXXXXX"),
    "ACP-C008": ("INVALID", (("PARSE", "ACP.PARSE.MALFORMED_JSON", "/payload/raw", "IMPLEMENTATION"),), "ARXXXXXX"),
    "ACP-C009": ("INVALID", (("PARSE", "ACP.PARSE.RESOURCE_LIMIT", "/payload/raw", "IMPLEMENTATION"),), "ARXXXXXX"),
    "ACP-C010": ("VALID", (), "NNANNNNA"),
    "ACP-C011": ("INVALID", (("SCHEMA", "ACP.SCHEMA.DRIFT", "/payload/document/extra", "IMPLEMENTATION"),), "NNRXXXXX"),
    "ACP-C012": ("VALID", (), "NNNNNNAA"),
    "ACP-C013": ("INVALID", (("GRAPH_CONFLICT", "ACP.PIPELINE.PREDECESSOR_VIOLATION", "/payload/callbacks/1/predecessors", "IMPLEMENTATION"),), "NNNNNNRX"),
    "ACP-C014": ("INVALID", (("GRAPH_CONFLICT", "ACP.PIPELINE.LATE_STAGE_EXECUTION", "/payload/callbacks/1", "IMPLEMENTATION"),), "NNNNNNRX"),
    "ACP-C015": ("VALID", (), "NNNNNNNA"),
    "ACP-C016": ("INVALID", (("PHASE_VERDICT", "ACP.VERDICT.OUTCOME_NOT_EXACT", "/payload/observedFindings", "IMPLEMENTATION"),), "NNNNNNNR"),
    "ACP-C017": ("INVALID", (("PHASE_VERDICT", "ACP.VERDICT.OUTCOME_NOT_EXACT", "/payload/observedFindings", "IMPLEMENTATION"), ("PHASE_VERDICT", "ACP.VERDICT.SUBSET_OUTCOME", "/payload/observedFindings", "IMPLEMENTATION")), "NNNNNNNR"),
    "ACP-C018": ("VALID", (), "NNNNANNA"),
    "ACP-C019": ("INVALID", (("INDEPENDENT_TRUST", "ACP.VERDICT.MUTANT_NOT_EXECUTED", "/payload/receipts/1/executionCount", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C020": ("INVALID", (("INDEPENDENT_TRUST", "ACP.VERDICT.MUTANT_SURVIVED", "/payload/receipts/1/state", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C021": ("VALID", (), "NNNNANNA"),
    "ACP-C022": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.MOCK_LEDGER_INVALID", "/payload/rows", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C023": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.MOCK_LEDGER_INVALID", "/payload/rows/0/ordinal", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C024": ("BLOCKED_EVIDENCE", (("INDEPENDENT_TRUST", "ACP.VERDICT.REQUIRED_REVIEW_MISSING", "/payload/receipts", "EVIDENCE"),), "NNNNRXXX"),
    "ACP-C025": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_SELF_ATTESTED", "/payload/receipts/0/reviewer", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C026": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/2/head", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C027": ("VALID", (), "NNNNANNA"),
    "ACP-C028": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.EXPECTATION_NOT_INDEPENDENT", "/payload/executorMembers/2", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C029": ("INVALID", (("INDEPENDENT_TRUST", "ACP.TRUST.EXPECTATION_NOT_INDEPENDENT", "/payload/productionImports/0", "IMPLEMENTATION"),), "NNNNRXXX"),
    "ACP-C030": ("VALID", (), "NNNNNANA"),
    "ACP-C031": ("INVALID", (("AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/branch", "IMPLEMENTATION"),), "NNNNNRXX"),
    "ACP-C032": ("INVALID", (("AUTHORIZATION", "ACP.IDENTITY.MISMATCH", "/payload/preflightBlob", "IMPLEMENTATION"),), "NNNNNRXX"),
    "ACP-C033": ("BLOCKED_EVIDENCE", (("AUTHORIZATION", "ACP.AUTH.BUDGET_REVIEW_REQUIRED", "/payload/files/0/readabilityReviewed", "EVIDENCE"),), "NNNNNRXX"),
    "ACP-C034": ("BLOCKED_IMPLEMENTATION", (("AUTHORIZATION", "ACP.AUTH.BUDGET_STOP", "/payload/files/0/chargedLines", "IMPLEMENTATION"),), "NNNNNRXX"),
    "ACP-C035": ("VALID", (), "NNNNNNNA"),
    "ACP-C036": ("INVALID", (("PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/authorityEffect", "IMPLEMENTATION"),), "NNNNNNNR"),
    "ACP-C037": ("INVALID", (("PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/candidateHead", "IMPLEMENTATION"),), "NNNNNNNR"),
    "ACP-C038": ("VALID", (), "ANNNNNNA"),
    "ACP-C039": ("BLOCKED_IMPLEMENTATION", (("BOUNDS", "ACP.VERDICT.PLATFORM_FAILURE", "/payload/import/status", "IMPLEMENTATION"),), "RXXXXXXX"),
    "ACP-C040": ("BLOCKED_IMPLEMENTATION", (("BOUNDS", "ACP.VERDICT.RESOURCE_FAILURE", "/payload/operation/status", "IMPLEMENTATION"),), "RXXXXXXX"),
}


MUTATION_RECEIPTS: dict[str, tuple[tuple[object, ...], ...]] = {
    "ACP-C018": (("MU-A", "ASSERT-A", 1, 1, "KILLED", "INVALID", ("ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT",)), ("MU-B", "ASSERT-B", 1, 1, "KILLED", "INVALID", ("ACP.SCHEMA.DRIFT",))),
    "ACP-C019": (("MU-A", "ASSERT-A", 1, 1, "KILLED", "INVALID", ("ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT",)), ("MU-B", "ASSERT-B", 0, 0, "NOT_EXECUTED", "NOT_IMPLEMENTED", ())),
    "ACP-C020": (("MU-A", "ASSERT-A", 1, 1, "KILLED", "INVALID", ("ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT",)), ("MU-B", "ASSERT-B", 1, 0, "SURVIVED", "VALID", ())),
}
EXECUTION_RECEIPTS: dict[str, tuple[tuple[object, ...], ...]] = {
    "ACP-C021": (("tree-a", 1, "C2", "BOUNDS", 1, "ACCEPTED", ()), ("tree-a", 2, "C2", "PARSE", 1, "ACCEPTED", ())),
    "ACP-C022": (("tree-a", 1, "C2", "BOUNDS", 1, "ACCEPTED", ()),),
    "ACP-C023": (("tree-a", 2, "C2", "PARSE", 1, "ACCEPTED", ()), ("tree-a", 1, "C2", "BOUNDS", 1, "ACCEPTED", ())),
}


def _expected(case_id: str) -> dict[str, object]:
    verdict, raw_findings, trace = SPEC[case_id]
    findings = [{"stage": stage, "code": code, "location": location, "blocker": blocker} for stage, code, location, blocker in raw_findings]
    observations = []
    for stage, symbol in zip(STAGES, trace, strict=True):
        codes = [finding["code"] for finding in findings if finding["stage"] == stage] if symbol == "R" else []
        observations.append({"stage": stage, "state": STATE[symbol], "callbackCount": 0 if symbol == "X" else 1, "justification": JUSTIFICATION[symbol], "findingCodes": codes})
    executions = [{"candidate": a, "ordinal": b, "phase": c, "stage": d, "callbackCount": e, "observedState": f, "observedFindingCodes": list(cast(tuple[object, ...], g))} for a, b, c, d, e, f, g in EXECUTION_RECEIPTS.get(case_id, ())]
    mutations = [{"mutantId": a, "assertionId": b, "executionCount": c, "failureCount": d, "state": e, "observedVerdict": f, "observedFindingCodes": list(cast(tuple[object, ...], g))} for a, b, c, d, e, f, g in MUTATION_RECEIPTS.get(case_id, ())]
    return {"verdict": verdict, "findings": findings, "observations": observations, "executionReceipts": executions, "mutationReceipts": mutations, "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT"}


def _case(case_id: str) -> dict[str, object]:
    matches = [case for case in CASES if case["caseId"] == case_id]
    assert len(matches) == 1
    return matches[0]


def _invoke_candidate(stimulus: dict[str, object]) -> dict[str, object]:
    raw = json.dumps(stimulus, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONHASHSEED": "0"}
    completed = subprocess.run([sys.executable, "-I", "-P", str(MODULE_PATH), "--execute-stdin"], input=raw, text=True, capture_output=True, timeout=5, check=False, env=environment)
    assert completed.returncode in {0, 3}, f"ACP-A12-NO-EXCEPTION: rc={completed.returncode} stderr={completed.stderr[:500]}"
    assert len(completed.stdout.encode("utf-8")) <= 65_536, "ACP-A12-NO-EXCEPTION: oversized stdout"
    value = json.loads(completed.stdout, object_pairs_hook=_strict_object)
    assert isinstance(value, dict), "ACP-A00-ENVELOPE: result is not an object"
    canonical = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert completed.stdout.strip() == canonical, "ACP-A00-ENVELOPE: stdout is not canonical JSON"
    return value


def _module_probe(expression: str, *arguments: str, input_text: str = "", extra_env: dict[str, str] | None = None) -> object:
    runner = "import json,runpy,sys;m=runpy.run_path(sys.argv[1],run_name='issue435_probe');print(json.dumps(" + expression + "))"
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    environment.update(extra_env or {})
    completed = subprocess.run(
        [sys.executable, "-I", "-P", "-c", runner, str(MODULE_PATH), *arguments],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


Executor = Callable[[dict[str, object]], dict[str, object]]


def _assert_case(case: dict[str, object], executor: Executor = _invoke_candidate, expected_override: dict[str, object] | None = None) -> None:
    case_id = cast(str, case["caseId"])
    stimulus = cast(dict[str, object], case["stimulus"])
    expected = expected_override or _expected(case_id)
    try:
        actual = executor(copy.deepcopy(stimulus))
    except AssertionError:
        raise
    except Exception as error:
        raise AssertionError(f"ACP-A12-NO-EXCEPTION: {type(error).__name__}") from error
    threat = cast(str, case["threatId"])
    if threat == "ACP-T01":
        assert actual.get("verdict") == expected["verdict"], "ACP-A01-VERDICT"
    if threat == "ACP-T02":
        assert actual.get("observations") == expected["observations"], "ACP-A02-OBSERVATIONS"
    if threat == "ACP-T03":
        assert actual.get("findings") == expected["findings"], "ACP-A03-FINDINGS"
    if threat == "ACP-T04":
        actual_counts = [row.get("callbackCount") for row in cast(list[dict[str, object]], actual.get("observations", []))]
        expected_counts = [row["callbackCount"] for row in cast(list[dict[str, object]], expected["observations"])]
        assert actual_counts == expected_counts, "ACP-A04-CALLBACK-COUNTS"
    if threat == "ACP-T05":
        actual_codes = [row.get("code") for row in cast(list[dict[str, object]], actual.get("findings", []))]
        expected_codes = [row["code"] for row in cast(list[dict[str, object]], expected["findings"])]
        assert actual_codes == expected_codes, "ACP-A05-ORDERED-FINDINGS"
    if threat == "ACP-T06":
        assert actual.get("mutationReceipts") == expected["mutationReceipts"], "ACP-A06-MUTATION-RECEIPTS"
    if threat == "ACP-T07":
        assert actual.get("executionReceipts") == expected["executionReceipts"], "ACP-A07-EXECUTION-RECEIPTS"
    if threat == "ACP-T08":
        assert isinstance(actual.get("observations"), list) and cast(list[object], actual["observations"])[4:5] == cast(list[object], expected["observations"])[4:5], "ACP-A08-REVIEW-TRUST"
    if threat == "ACP-T09":
        assert isinstance(actual.get("observations"), list) and cast(list[object], actual["observations"])[4:5] == cast(list[object], expected["observations"])[4:5], "ACP-A09-EXPECTATION-BOUNDARY"
    if threat == "ACP-T10":
        assert isinstance(actual.get("observations"), list) and cast(list[object], actual["observations"])[5:6] == cast(list[object], expected["observations"])[5:6], "ACP-A10-AUTHORIZATION"
    if threat == "ACP-T11":
        assert (actual.get("verdict"), actual.get("findings")) == (expected["verdict"], expected["findings"]), "ACP-A11-CHECKPOINT"
    assert set(actual) == {"verdict", "findings", "observations", "executionReceipts", "mutationReceipts", "activation", "authorityEffect"}, "ACP-A00-ENVELOPE"
    assert actual["verdict"] == expected["verdict"], "ACP-A01-VERDICT"
    assert actual["findings"] == expected["findings"], "ACP-A03-FINDINGS"
    assert actual["observations"] == expected["observations"], "ACP-A02-OBSERVATIONS"
    assert actual["executionReceipts"] == expected["executionReceipts"], "ACP-A07-EXECUTION-RECEIPTS"
    assert actual["mutationReceipts"] == expected["mutationReceipts"], "ACP-A06-MUTATION-RECEIPTS"
    assert actual["activation"] == "NONE", "ACP-A13-ACTIVATION"
    assert actual["authorityEffect"] == "NO_AUTHORITY_EFFECT", "ACP-A14-AUTHORITY"


def _held_out(case: dict[str, object], expected: dict[str, object]) -> tuple[dict[str, object], dict[str, object]] | None:
    case_id = cast(str, case["caseId"])
    anchors = {"ACP-C002", "ACP-C006", "ACP-C011", "ACP-C013", "ACP-C016", "ACP-C019", "ACP-C022", "ACP-C024", "ACP-C028", "ACP-C031", "ACP-C037", "ACP-C039"}
    if case_id not in anchors:
        return None
    stimulus = copy.deepcopy(cast(dict[str, object], case["stimulus"]))
    payload = cast(dict[str, object], stimulus["payload"])
    held_expected = copy.deepcopy(expected)
    if case_id == "ACP-C002":
        payload["relativePath"] = "held-out/renamed.json"
    elif case_id == "ACP-C006":
        payload.update({"raw": "{\"b\":2}", "rawSha256": "0ab1a6d394cd30195f0642b67ae1180c375ffadf5dd7f39c390668b5fdb6da93"})
    elif case_id == "ACP-C011":
        cast(dict[str, object], payload["document"])["extra"] = "held-out-value"
    elif case_id == "ACP-C013":
        cast(list[dict[str, object]], payload["callbacks"])[2]["state"] = "NOT_APPLICABLE"
    elif case_id == "ACP-C016":
        payload["observedFindings"] = ["ACP.GENERIC.REJECTED"]
    elif case_id == "ACP-C019":
        cast(list[dict[str, object]], payload["receipts"])[1]["assertionId"] = "ASSERT-HELD-OUT"
        cast(list[dict[str, object]], held_expected["mutationReceipts"])[1]["assertionId"] = "ASSERT-HELD-OUT"
    elif case_id == "ACP-C022":
        payload["candidate"] = "tree-held-out"
        cast(list[dict[str, object]], payload["rows"])[0]["candidate"] = "tree-held-out"
        cast(list[dict[str, object]], held_expected["executionReceipts"])[0]["candidate"] = "tree-held-out"
    elif case_id == "ACP-C024":
        payload["candidateAuthor"] = "held-out-author"
    elif case_id == "ACP-C028":
        cast(list[str], payload["executorMembers"])[2] = "expectedFindings"
    elif case_id == "ACP-C031":
        payload["branch"] = "governance-435-adversarial-convergence-framework-v1-lookalike"
    elif case_id == "ACP-C037":
        payload["candidateHead"] = "f" * 40
    elif case_id == "ACP-C039":
        cast(dict[str, object], payload["import"])["errorType"] = "UnicodeError"
    return stimulus, held_expected


HostileExpected = tuple[str, str, str, str, str]
HostileRow = tuple[str, dict[str, object], HostileExpected]
HostileAdder = Callable[[str, str, Callable[[dict[str, object]], object], HostileExpected], None]


def _hostile_review_route_resource(add: HostileAdder) -> None:
    add("review-valid", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), ("VALID", "", "", "", "NNNNANNA"))
    add("review-block", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a", disposition="BLOCK")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/0/disposition", "NNNNRXXX"))
    add("review-fail", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a", disposition="FAIL"), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/0/disposition", "NNNNRXXX"))
    add("review-duplicate-source", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(source="issue:435:comment:9001")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/1/source", "NNNNRXXX"))
    add("review-duplicate-reviewer", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(reviewer="reviewer-a")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/1/reviewer", "NNNNRXXX"))
    add("review-empty-reviewer", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer=""), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("review-duplicate-role", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(role="ARCHITECTURE_SCOPE_PHASE")), ("BLOCKED_EVIDENCE", "INDEPENDENT_TRUST", "ACP.VERDICT.REQUIRED_REVIEW_MISSING", "/payload/receipts", "NNNNRXXX"))
    add("review-arbitrary-role", "ACP-C025", lambda p: p.update(requiredRoles=["ANY"], receipts=[dict(cast(list[dict[str, object]], p["receipts"])[0], role="ANY", reviewer="reviewer-a")]), ("BLOCKED_EVIDENCE", "INDEPENDENT_TRUST", "ACP.VERDICT.REQUIRED_REVIEW_MISSING", "/payload/receipts", "NNNNRXXX"))
    add("review-malformed-identities", "ACP-C025", lambda p: (p.update(head="x", tree="x"), [row.update(reviewer=f"reviewer-{index}", head="x", tree="x") for index, row in enumerate(cast(list[dict[str, object]], p["receipts"]))]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("review-boolean-identities", "ACP-C025", lambda p: (p.update(head=True, tree=1), [row.update(reviewer=f"reviewer-{index}", head=True, tree=1) for index, row in enumerate(cast(list[dict[str, object]], p["receipts"]))]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("expectation-boolean-import-count", "ACP-C027", lambda p: p.update(dynamicImportCalls=False), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-path", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(path="/etc/passwd"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/path", "NNNNNRXX"))
    add("route-mode", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(mode="120000"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/mode", "NNNNNRXX"))
    add("route-status", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(status="D"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/status", "NNNNNRXX"))
    add("route-paired-evil", "ACP-C030", lambda p: p.update(branch="evil", authorizedBranch="evil", base="b" * 40, authorizedBase="b" * 40, preflightBlob="c" * 40, authorizedPreflightBlob="c" * 40), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/branch", "NNNNNRXX"))
    add("route-extra-file", "ACP-C030", lambda p: cast(list[object], p["files"]).append(copy.deepcopy(cast(list[object], p["files"])[0])), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files", "NNNNNRXX"))
    add("route-negative-budget", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(chargedLines=-1, cap=-1), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-boolean-budget", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(chargedLines=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("resource-nofollow", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(nofollow=False), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/capabilities/nofollow", "RXXXXXXX"))
    add("resource-descriptor", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(descriptorRelative=False), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/capabilities/descriptorRelative", "RXXXXXXX"))
    add("resource-network", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(network=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("resource-import-contradiction", "ACP-C038", lambda p: cast(dict[str, object], p["import"]).update(errorType="OSError"), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.VERDICT.PLATFORM_FAILURE", "/payload/import/status", "RXXXXXXX"))
    add("resource-operation-contradiction", "ACP-C038", lambda p: cast(dict[str, object], p["operation"]).update(errorType="RecursionError"), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.VERDICT.RESOURCE_FAILURE", "/payload/operation/status", "RXXXXXXX"))
    add("checkpoint-extra", "ACP-C035", lambda p: p.update(unexpected="attacker"), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("checkpoint-malformed-identities", "ACP-C035", lambda p: p.update(boundHead=True, candidateHead=1), ("INVALID", "PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/candidateHead", "NNNNNNNR"))
    add("checkpoint-malformed-digest", "ACP-C035", lambda p: p.update(boundDiffSha256="", candidateDiffSha256=""), ("INVALID", "PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/candidateDiffSha256", "NNNNNNNR"))


def _hostile_regressions() -> list[HostileRow]:
    rows: list[HostileRow] = []

    def add(label: str, case_id: str, update: Callable[[dict[str, object]], object], expected: HostileExpected) -> None:
        stimulus = copy.deepcopy(cast(dict[str, object], _case(case_id)["stimulus"]))
        update(cast(dict[str, object], stimulus["payload"]))
        rows.append((label, stimulus, expected))

    add("filesystem-absolute", "ACP-C001", lambda p: p.update(relativePath="/etc/passwd"), ("INVALID", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/relativePath", "RXXXXXXX"))
    add("filesystem-relative-type", "ACP-C001", lambda p: p.update(relativePath=True), ("INVALID", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/relativePath", "RXXXXXXX"))
    add("filesystem-empty-components", "ACP-C001", lambda p: p.update(componentKinds=[]), ("INVALID", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds", "RXXXXXXX"))
    add("filesystem-extra-component", "ACP-C001", lambda p: p.update(componentKinds=["DIRECTORY", "REGULAR_FILE", "REGULAR_FILE"]), ("INVALID", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds/1", "RXXXXXXX"))
    add("filesystem-component-count", "ACP-C001", lambda p: p.update(componentKinds=["DIRECTORY", "DIRECTORY", "REGULAR_FILE"]), ("INVALID", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/componentKinds", "RXXXXXXX"))
    add("filesystem-negative", "ACP-C001", lambda p: p.update(declaredBytes=-1, readBytes=-1, limitBytes=-1), ("INVALID", "BOUNDS", "ACP.BOUNDS.INPUT_TOO_LARGE", "/payload/declaredBytes", "RXXXXXXX"))
    add("filesystem-inconsistent", "ACP-C001", lambda p: p.update(readBytes=63), ("INVALID", "BOUNDS", "ACP.VERDICT.RESOURCE_FAILURE", "/payload/readBytes", "RXXXXXXX"))
    add("pipeline-sticky-rejection", "ACP-C012", lambda p: p.update(callbacks=[{"stage": "BOUNDS", "predecessors": [], "state": "REJECTED"}, {"stage": "PARSE", "predecessors": ["BOUNDS"], "state": "NOT_REACHED"}, {"stage": "SCHEMA", "predecessors": ["BOUNDS", "PARSE"], "state": "ACCEPTED"}]), ("INVALID", "GRAPH_CONFLICT", "ACP.PIPELINE.LATE_STAGE_EXECUTION", "/payload/callbacks/2", "NNNNNNRX"))
    add("pipeline-declared-only", "ACP-C012", lambda p: p.update(callbacks=[{"stage": "PHASE_VERDICT", "predecessors": list(STAGES[:-1]), "state": "ACCEPTED"}]), ("INVALID", "GRAPH_CONFLICT", "ACP.PIPELINE.PREDECESSOR_VIOLATION", "/payload/callbacks/0/predecessors", "NNNNNNRX"))
    add("pipeline-duplicate-stage", "ACP-C012", lambda p: p.update(callbacks=[{"stage": "BOUNDS", "predecessors": [], "state": "ACCEPTED"}, {"stage": "PARSE", "predecessors": ["BOUNDS"], "state": "ACCEPTED"}, {"stage": "BOUNDS", "predecessors": [], "state": "ACCEPTED"}]), ("INVALID", "GRAPH_CONFLICT", "ACP.PIPELINE.PREDECESSOR_VIOLATION", "/payload/callbacks/2/predecessors", "NNNNNNRX"))
    add("pipeline-starts-at-parse", "ACP-C012", lambda p: p.update(callbacks=[{"stage": "PARSE", "predecessors": ["BOUNDS"], "state": "ACCEPTED"}]), ("INVALID", "GRAPH_CONFLICT", "ACP.PIPELINE.PREDECESSOR_VIOLATION", "/payload/callbacks/0/predecessors", "NNNNNNRX"))
    add("pipeline-unknown-state", "ACP-C012", lambda p: cast(list[dict[str, object]], p["callbacks"])[0].update(state="UNKNOWN"), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("pipeline-boolean-stage", "ACP-C012", lambda p: cast(list[dict[str, object]], p["callbacks"])[0].update(stage=False), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("outcome-null", "ACP-C015", lambda p: p.update({key: None for key in tuple(p)}), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("outcome-equal-boolean", "ACP-C015", lambda p: p.update(contractVerdict=True, observedVerdict=1, contractFindings=[], observedFindings=[]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("outcome-finding-equality", "ACP-C015", lambda p: p.update(contractVerdict="INVALID", observedVerdict="INVALID", contractFindings=[True], observedFindings=[1]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("outcome-duplicate-findings", "ACP-C015", lambda p: p.update(contractFindings=["ACP.SCHEMA.DRIFT", "ACP.SCHEMA.DRIFT"], observedFindings=["ACP.SCHEMA.DRIFT", "ACP.SCHEMA.DRIFT"]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-empty", "ACP-C018", lambda p: p.update(requiredMutantIds=[], receipts=[]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-duplicate", "ACP-C018", lambda p: p.update(requiredMutantIds=["MU-A", "MU-A"], receipts=[copy.deepcopy(cast(list[object], p["receipts"])[0]), copy.deepcopy(cast(list[object], p["receipts"])[0])]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-empty-assertion", "ACP-C018", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(assertionId=""), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-boolean-count", "ACP-C018", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(executionCount=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-float-execution-count", "ACP-C018", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(executionCount=1.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("mutation-float-failure-count", "ACP-C018", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(failureCount=1.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("ledger-forged", "ACP-C021", lambda p: cast(list[dict[str, object]], p["rows"])[0].update(callbackCount=0, observedState="REJECTED", observedFindingCodes=["ACP.SCHEMA.DRIFT"]), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.MOCK_LEDGER_INVALID", "/payload/rows/0", "NNNNRXXX"))
    add("ledger-callback-count", "ACP-C021", lambda p: cast(list[dict[str, object]], p["rows"])[0].update(callbackCount=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("ledger-float-ordinal", "ACP-C021", lambda p: cast(list[dict[str, object]], p["rows"])[0].update(ordinal=1.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("ledger-float-callback-count", "ACP-C021", lambda p: cast(list[dict[str, object]], p["rows"])[0].update(callbackCount=1.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("ledger-reordered-contract", "ACP-C021", lambda p: (p.update(contractOrder=["PARSE", "BOUNDS"]), cast(list[dict[str, object]], p["rows"])[0].update(stage="PARSE"), cast(list[dict[str, object]], p["rows"])[1].update(stage="BOUNDS")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.MOCK_LEDGER_INVALID", "/payload/rows/0", "NNNNRXXX"))
    add("ledger-duplicate-contract", "ACP-C021", lambda p: (p.update(contractOrder=["BOUNDS", "BOUNDS"]), cast(list[dict[str, object]], p["rows"])[1].update(stage="BOUNDS")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.MOCK_LEDGER_INVALID", "/payload/rows/0", "NNNNRXXX"))
    add("ledger-empty-identity", "ACP-C021", lambda p: (p.update(candidate="", phase=""), [row.update(candidate="", phase="") for row in cast(list[dict[str, object]], p["rows"])]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("review-valid", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), ("VALID", "", "", "", "NNNNANNA"))
    add("review-block", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a", disposition="BLOCK")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/0/disposition", "NNNNRXXX"))
    add("review-fail", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a", disposition="FAIL"), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/0/disposition", "NNNNRXXX"))
    add("review-duplicate-source", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(source="issue:435:comment:9001")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/1/source", "NNNNRXXX"))
    add("review-duplicate-reviewer", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(reviewer="reviewer-a")), ("INVALID", "INDEPENDENT_TRUST", "ACP.TRUST.REVIEW_IDENTITY_MISMATCH", "/payload/receipts/1/reviewer", "NNNNRXXX"))
    add("review-empty-reviewer", "ACP-C025", lambda p: cast(list[dict[str, object]], p["receipts"])[0].update(reviewer=""), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("review-duplicate-role", "ACP-C025", lambda p: (cast(list[dict[str, object]], p["receipts"])[0].update(reviewer="reviewer-a"), cast(list[dict[str, object]], p["receipts"])[1].update(role="ARCHITECTURE_SCOPE_PHASE")), ("BLOCKED_EVIDENCE", "INDEPENDENT_TRUST", "ACP.VERDICT.REQUIRED_REVIEW_MISSING", "/payload/receipts", "NNNNRXXX"))
    add("review-arbitrary-role", "ACP-C025", lambda p: p.update(requiredRoles=["ANY"], receipts=[dict(cast(list[dict[str, object]], p["receipts"])[0], role="ANY", reviewer="reviewer-a")]), ("BLOCKED_EVIDENCE", "INDEPENDENT_TRUST", "ACP.VERDICT.REQUIRED_REVIEW_MISSING", "/payload/receipts", "NNNNRXXX"))
    add("review-malformed-identities", "ACP-C025", lambda p: (p.update(head="x", tree="x"), [row.update(reviewer=f"reviewer-{index}", head="x", tree="x") for index, row in enumerate(cast(list[dict[str, object]], p["receipts"]))]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("review-boolean-identities", "ACP-C025", lambda p: (p.update(head=True, tree=1), [row.update(reviewer=f"reviewer-{index}", head=True, tree=1) for index, row in enumerate(cast(list[dict[str, object]], p["receipts"]))]), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("expectation-boolean-import-count", "ACP-C027", lambda p: p.update(dynamicImportCalls=False), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("expectation-float-import-count", "ACP-C027", lambda p: p.update(dynamicImportCalls=0.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-path", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(path="/etc/passwd"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/path", "NNNNNRXX"))
    add("route-mode", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(mode="120000"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/mode", "NNNNNRXX"))
    add("route-status", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(status="D"), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files/0/status", "NNNNNRXX"))
    add("route-paired-evil", "ACP-C030", lambda p: p.update(branch="evil", authorizedBranch="evil", base="b" * 40, authorizedBase="b" * 40, preflightBlob="c" * 40, authorizedPreflightBlob="c" * 40), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/branch", "NNNNNRXX"))
    add("route-extra-file", "ACP-C030", lambda p: cast(list[object], p["files"]).append(copy.deepcopy(cast(list[object], p["files"])[0])), ("INVALID", "AUTHORIZATION", "ACP.AUTH.ROUTE_DRIFT", "/payload/files", "NNNNNRXX"))
    add("route-negative-budget", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(chargedLines=-1, cap=-1), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-boolean-budget", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(chargedLines=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-float-charged-lines", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(chargedLines=509.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("route-float-cap", "ACP-C030", lambda p: cast(list[dict[str, object]], p["files"])[0].update(cap=600.0), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("resource-nofollow", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(nofollow=False), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/capabilities/nofollow", "RXXXXXXX"))
    add("resource-descriptor", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(descriptorRelative=False), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT", "/payload/capabilities/descriptorRelative", "RXXXXXXX"))
    add("resource-network", "ACP-C038", lambda p: cast(dict[str, object], p["capabilities"]).update(network=True), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("resource-import-contradiction", "ACP-C038", lambda p: cast(dict[str, object], p["import"]).update(errorType="OSError"), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.VERDICT.PLATFORM_FAILURE", "/payload/import/status", "RXXXXXXX"))
    add("resource-operation-contradiction", "ACP-C038", lambda p: cast(dict[str, object], p["operation"]).update(errorType="RecursionError"), ("BLOCKED_IMPLEMENTATION", "BOUNDS", "ACP.VERDICT.RESOURCE_FAILURE", "/payload/operation/status", "RXXXXXXX"))
    add("checkpoint-extra", "ACP-C035", lambda p: p.update(unexpected="attacker"), ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX"))
    add("checkpoint-malformed-identities", "ACP-C035", lambda p: p.update(boundHead=True, candidateHead=1), ("INVALID", "PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/candidateHead", "NNNNNNNR"))
    add("checkpoint-malformed-digest", "ACP-C035", lambda p: p.update(boundDiffSha256="", candidateDiffSha256=""), ("INVALID", "PHASE_VERDICT", "ACP.VERDICT.CHECKPOINT_INVALID", "/payload/candidateDiffSha256", "NNNNNNNR"))
    malformed: tuple[object, ...] = (None, True, 0, 1.5, "text", [], {}, ["nested"], {"nested": "value"})
    for index, value in enumerate(malformed):
        stimulus = copy.deepcopy(cast(dict[str, object], _case("ACP-C015")["stimulus"]))
        cast(dict[str, object], stimulus["payload"])["contractVerdict"] = copy.deepcopy(value)
        rows.append((f"outcome-type-{index}", stimulus, ("INVALID", "SCHEMA", "ACP.SCHEMA.DRIFT", "/payload", "NNRXXXXX")))
    return rows


HOSTILE_REGRESSIONS = _hostile_regressions()


def _draft202012_errors(instance: dict[str, object]) -> list[str]:
    runner = (
        "import json, sys\n"
        "from jsonschema import Draft202012Validator\n"
        "value = json.load(sys.stdin)\n"
        "Draft202012Validator.check_schema(value['schema'])\n"
        "errors = Draft202012Validator(value['schema']).iter_errors(value['instance'])\n"
        "print(json.dumps([error.message for error in errors]))\n"
    )
    envelope = json.dumps({"schema": _load(SCHEMA_PATH), "instance": instance}, ensure_ascii=True, separators=(",", ":"))
    completed = subprocess.run(["/usr/bin/python3", "-c", runner], input=envelope, text=True, capture_output=True, timeout=5, check=False, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    assert completed.returncode == 0, completed.stderr
    errors = json.loads(completed.stdout)
    assert isinstance(errors, list) and all(isinstance(error, str) for error in errors)
    return cast(list[str], errors)


def test_corpus_identity_materialization_and_closed_order() -> None:
    raw = CORPUS_PATH.read_bytes()
    canonical = json.dumps(CORPUS, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    assert hashlib.sha256(raw).hexdigest() == RAW_SHA256
    assert hashlib.sha256(CORPUS_DOMAIN + canonical).hexdigest() == SEMANTIC_SHA256
    assert len(raw) <= 49_152
    assert CORPUS["caseCount"] == 40 and CORPUS["threatUniverse"] == list(THREATS)
    assert [case["caseId"] for case in CASES] == [f"ACP-C{number:03d}" for number in range(1, 41)]
    actual_kinds = [cast(dict[str, object], case["stimulus"])["kind"] for case in CASES]
    assert actual_kinds == [kind for kind, count in zip(KINDS, (4, 5, 2, 3, 3, 3, 3, 3, 3, 5, 3, 3), strict=True) for _ in range(count)]
    assert all(set(cast(dict[str, object], case["stimulus"])) == {"kind", "payload"} and cast(dict[str, object], case["stimulus"])["payload"] for case in CASES)
    assert all("variant" not in json.dumps(case).lower() for case in CASES)
    assert set(SPEC) == {cast(str, case["caseId"]) for case in CASES}


def test_schema_draft202012_accepts_actual_corpus_and_closes_stimulus() -> None:
    assert _draft202012_errors(CORPUS) == []
    broken = copy.deepcopy(CORPUS)
    cast(dict[str, object], cast(list[dict[str, object]], broken["cases"])[0]["stimulus"])["variant"] = "lookup"
    assert _draft202012_errors(broken)


def _valid_freeze() -> dict[str, object]:
    paths = {"corpus": "docs/governance/adversarial-convergence-framework-cases-v1.json", "schema": "docs/governance/adversarial-convergence-framework-v1.schema.json",
        "acceptanceTest": "tests/unit/test_adversarial_convergence.py", "skeleton": "scripts/quality/adversarial_convergence.py",
        "dispatcher": "scripts/quality/check_quality_stage.py", "guardrail": "scripts/guardrails_check.py"}
    artifacts: dict[str, object] = {}
    for index, (name, path) in enumerate(paths.items(), start=1):
        artifacts[name] = {"path": path, "blob": str(index) * 40, "sha256": str(index) * 64}
    cast(dict[str, object], artifacts["corpus"])["semanticSha256"] = "7" * 64
    cast(dict[str, object], artifacts["skeleton"])["protectedSha256"] = "8" * 64
    roles = ("ARCHITECTURE_SCOPE_PHASE", "SECURITY_TRUST", "READABILITY_FEASIBILITY", "MUTATION_FALSE_PASS")
    reviews = []
    for index, role in enumerate(roles, start=1):
        reviewer = f"reviewer-{index} <reviewer-{index}@example.test>"
        url = f"https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-{index}"
        content = f"ISSUE435_REVIEW_V1\nrole={role}\ndisposition=PASS\nhead={'a' * 40}\ntree={'b' * 40}\nreviewer={reviewer}\nurl={url}"
        reviews.append({"role": role, "reviewer": reviewer, "disposition": "PASS", "head": "a" * 40, "tree": "b" * 40, "url": url, "content": content, "contentSha256": hashlib.sha256(content.encode()).hexdigest()})
    author = "rohit agrawal <rohit.ra.agrawal@gmail.com>"
    return {"schemaVersion": "AdversarialConvergenceRedFreezeV1", "issue": 435, "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT", "correction": {"rejectedHead": "8d83713ed09dc626e24f1fe063e6afd9cfa5e8e9", "wave": 1, "authors": [author]}, "c2": {"head": "a" * 40, "tree": "b" * 40, "diffSha256": "c" * 64}, "artifacts": artifacts, "reviews": reviews}


def test_schema_accepts_complete_freeze_and_rejects_duplicate_reviews() -> None:
    freeze = _valid_freeze()
    assert _draft202012_errors(freeze) == []
    duplicate = copy.deepcopy(freeze)
    reviews = cast(list[dict[str, object]], duplicate["reviews"])
    reviews[:] = [copy.deepcopy(reviews[0]) for _ in range(4)]
    assert _draft202012_errors(duplicate)


def test_application_freeze_shape_rejects_nested_drift_and_invalid_review_url() -> None:
    expression = "m['_closed_freeze_shape'](json.loads(sys.stdin.read()))"
    freeze = _valid_freeze()
    assert _module_probe(expression, input_text=json.dumps(freeze)) is True
    cast(dict[str, object], freeze["c2"])["unexpected"] = True
    assert _module_probe(expression, input_text=json.dumps(freeze)) is False


def test_application_freeze_values_enforce_schema_constraints_and_exact_pass() -> None:
    expression = "m['_closed_freeze_shape'](json.loads(sys.stdin.read()))"
    valid = _valid_freeze()
    assert _module_probe(expression, input_text=json.dumps(valid)) is True
    mutations: list[dict[str, object]] = []
    for mutate in ("unicode_url", "blocking_content", "boolean_wave", "long_author", "long_reviewer", "uppercase_oid", "uppercase_sha"):
        broken = copy.deepcopy(valid)
        reviews = cast(list[dict[str, object]], broken["reviews"])
        if mutate == "unicode_url":
            reviews[0]["url"] = "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-١"
        elif mutate == "blocking_content":
            reviews[0]["content"] = f"BLOCK: DO NOT PASS {'a' * 40} {'b' * 40}"
            reviews[0]["contentSha256"] = hashlib.sha256(cast(str, reviews[0]["content"]).encode()).hexdigest()
        elif mutate == "boolean_wave":
            cast(dict[str, object], broken["correction"])["wave"] = True
        elif mutate == "long_author":
            cast(dict[str, object], broken["correction"])["authors"] = ["x" * 161]
        elif mutate == "long_reviewer":
            reviews[0]["reviewer"] = "x" * 161
        elif mutate == "uppercase_oid":
            cast(dict[str, object], broken["c2"])["head"] = "A" * 40
        else:
            cast(dict[str, object], broken["c2"])["diffSha256"] = "C" * 64
        mutations.append(broken)
    assert _draft202012_errors(mutations[1]) == []
    assert all(_draft202012_errors(item) for index, item in enumerate(mutations) if index != 1)
    assert all(_module_probe(expression, input_text=json.dumps(item)) is False for item in mutations)
    fewer_reviews = copy.deepcopy(valid)
    cast(list[object], fewer_reviews["reviews"]).pop()
    assert _draft202012_errors(fewer_reviews) == []
    assert _module_probe(expression, input_text=json.dumps(fewer_reviews)) is False


def test_review_provenance_rejects_declared_author_omission_and_normalized_collision() -> None:
    expression = "m['_review_provenance'](json.loads(sys.stdin.read()),tuple(sys.argv[2:]))"
    freeze = _valid_freeze()
    author = "rohit agrawal <rohit.ra.agrawal@gmail.com>"
    assert _module_probe(expression, author, input_text=json.dumps(freeze)) is True
    cast(dict[str, object], freeze["correction"])["authors"] = ["declared other <other@example.test>"]
    assert _module_probe(expression, author, input_text=json.dumps(freeze)) is False
    freeze = _valid_freeze()
    cast(list[dict[str, object]], freeze["reviews"])[0]["reviewer"] = "rohit agrawal <other@example.test>"
    assert _module_probe(expression, author, input_text=json.dumps(freeze)) is False
    freeze = _valid_freeze()
    cast(list[dict[str, object]], freeze["reviews"])[0]["reviewer"] = "other reviewer <rohit.ra.agrawal@gmail.com>"
    assert _module_probe(expression, author, input_text=json.dumps(freeze)) is False


def test_candidate_authors_are_parsed_from_bounded_framed_git_history() -> None:
    expression = "(m['_candidate_authors'].__globals__.__setitem__('_git',lambda *_:m['GitResult']('OK',0,sys.stdin.buffer.read(),b'')),m['_candidate_authors'](m['Path']('.'),sys.argv[2]))[1]"
    head = "d" * 40
    hashes = (
        "205c02b3bac633d023d753356bc966c194ed36a7", "b099747812bcd97f812358908cb847c351190bc3",
        "8d83713ed09dc626e24f1fe063e6afd9cfa5e8e9", "134fbd91606eebbcdcff5f47b26b6d286acc1fa2",
        "6d741aec9a2a56d54034e0092a2e24d535079517", "9bd0a2786ca41e720a275e70a2c98470a3f3aa38", "6b681b4acc419d2fa63c35862d6b6185ce82dd50", "7a17fe323a8c9acd9ea887f9932e4ca79ff02853", "26347f466778e946cc3b5aa8fa110f4597b279e2", "e6821c579c7bc1a28778278954cb52de7bf41dbb", "55a3911c3b2b35ae681b647e143c492e6a4a8cad", "bf795a2760479784012fff6e644ec5d102b3caf2",
        "8fa7667b1d613b1470195ff712763aac5b5e048c", "0ae2593eca92c4e9657a04cb45152d7be839a48b", "a4d903dfb5b0c40aabb4117a29a901db0972182f",
        "dcbe15d58dff5ceafe7319e2baa3302ff01b6510",
        "8a9bdc41c63cb449afdc6bf7f806ef946a73faa2",
        "84f1430822d696537c41b5a022d3cc14d72becea",
        "c7886a86ad84f8c3e2ceb1a9f9c675e7f3d535da",
        "956aed3d78733259ba6a024dcbead6f2f6f43c40",
        "f82be816e349d13d8365b72fbeb51498d244755e", "cc394d4dadef3c32dc735fc84a2b9c49e3336985", "bf3a53ddac282a8daab61db2eaa5d030959eae0f", "f4eab6b3febb9feb78699930bf4a453a76ca6b9d", "6325fe3eddffc57d0ef066705b6bb3ca276f353b", "221ab84b75667176aaf1c34513bf6967d1390d5f", "317fb741327a599239fe3b86e5711821f5a2b226", "3f00bc5c2e88ee8598fdf12cedae5fcd1afa6d1e", "ce70e1dfee5fb6e88e86c7a86ca496cf103ea2bd", "1fd860ccb37418f5c59cc05e825b645bc02498ba", "8881dbbd9078c07cc956384675a3b7b6748a0951", "67efee0fae5d457ef1a2c63bd56784055ce989f2", "261f9935655e6219744fe02852452439744f441a", "6d9c79f6dba5d0793097f481cdc8a305cec4f467", "65cd6c84fed71227b0b6baddbe1755429131a229",
        head,
    )
    history = "".join(f"{commit}\0Rohit   Agrawal\0ROHIT.RA.AGRAWAL@GMAIL.COM\0" for commit in hashes)
    assert _module_probe(expression, head, input_text=history) == ["rohit agrawal <rohit.ra.agrawal@gmail.com>"]
    assert _module_probe(expression, head, input_text=history[:-1]) is None
    assert _module_probe(expression, head, input_text=history.replace(hashes[0], "e" * 40, 1)) is None


@pytest.mark.parametrize("value", [None, True, 0, 1.5, "text", [], {}, ["nested"], {"nested": "value"}], ids=("null", "bool", "int", "float", "string", "array", "object", "nested-array", "nested-object"))
def test_freeze_identity_fields_fail_closed_for_every_non_string_json_type(value: object) -> None:
    expression = "m['_closed_freeze_shape'](json.loads(sys.stdin.read()))"
    for field in ("authors", "author", "reviewer"):
        freeze = _valid_freeze()
        if field == "authors":
            cast(dict[str, object], freeze["correction"])["authors"] = copy.deepcopy(value)
        elif field == "author":
            cast(dict[str, object], freeze["correction"])["authors"] = [copy.deepcopy(value)]
        else:
            cast(list[dict[str, object]], freeze["reviews"])[0]["reviewer"] = copy.deepcopy(value)
        assert _module_probe(expression, input_text=json.dumps(freeze)) is False


@pytest.mark.parametrize(("order", "expected"), [((0, 1, 2, 3), True), ((3, 2, 1, 0), True), ((0, 0, 2, 3), False), ((0, 0, 0, 0), False)])
def test_review_urls_are_distinct_after_permutation(order: tuple[int, ...], expected: bool) -> None:
    freeze = _valid_freeze()
    reviews = cast(list[dict[str, object]], freeze["reviews"])
    urls = [cast(str, receipt["url"]) for receipt in reviews]
    for receipt, source in zip(reviews, order, strict=True):
        receipt["url"] = urls[source]
        receipt["content"] = f"ISSUE435_REVIEW_V1\nrole={receipt['role']}\ndisposition=PASS\nhead={receipt['head']}\ntree={receipt['tree']}\nreviewer={receipt['reviewer']}\nurl={receipt['url']}"
        receipt["contentSha256"] = hashlib.sha256(cast(str, receipt["content"]).encode("ascii")).hexdigest()
    assert _module_probe("m['_closed_freeze_shape'](json.loads(sys.stdin.read()))", input_text=json.dumps(freeze)) is expected


def test_review_url_rejects_noncanonical_decimal_identity() -> None:
    freeze = _valid_freeze()
    receipt = cast(list[dict[str, object]], freeze["reviews"])[0]
    receipt["url"] = cast(str, receipt["url"]).replace("issuecomment-1", "issuecomment-01")
    receipt["content"] = f"ISSUE435_REVIEW_V1\nrole={receipt['role']}\ndisposition=PASS\nhead={receipt['head']}\ntree={receipt['tree']}\nreviewer={receipt['reviewer']}\nurl={receipt['url']}"
    receipt["contentSha256"] = hashlib.sha256(cast(str, receipt["content"]).encode("ascii")).hexdigest()
    assert _module_probe("m['_closed_freeze_shape'](json.loads(sys.stdin.read()))", input_text=json.dumps(freeze)) is False


@pytest.mark.parametrize("identity", ["Reviewer <reviewer@example.test>", " reviewer <reviewer@example.test>", "reviewer  one <reviewer@example.test>", "reviewer < reviewer@example.test>", "reviewer <reviewer @example.test>", "reviewer <reviewer@ example.test>", "reviewer <reviewer@example.test >", "reviewer <reviewer>@example.test>", "reviewer <reviewer@@example.test>", "reviewer <.reviewer@example.test>", "reviewer <reviewer@example..test>", "reviewer <reviewer＠example.test>"])
def test_canonical_identity_rejects_case_whitespace_delimiter_and_confusable_aliases(identity: str) -> None:
    assert _module_probe("m['_canonical_identity'](sys.argv[2])", identity) is None


def test_test_oracle_is_literal_and_candidate_is_only_a_subprocess() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported_names = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert "scripts.quality.adversarial_convergence" not in imported
    assert {"PhaseVerdict", "FindingCode", "MutationState"}.isdisjoint(imported_names)
    assert "observed " + "!= expected" not in source and "MutationState." + "KILLED" not in source


def test_literal_oracle_covers_every_complete_result_field() -> None:
    for case in CASES:
        expected = _expected(cast(str, case["caseId"]))
        observations = cast(list[dict[str, object]], expected["observations"])
        findings = cast(list[dict[str, object]], expected["findings"])
        assert list(expected) == ["verdict", "findings", "observations", "executionReceipts", "mutationReceipts", "activation", "authorityEffect"]
        assert [row["stage"] for row in observations] == list(STAGES)
        assert len(observations) == 8
        assert all(row["state"] in STATE.values() and row["callbackCount"] in {0, 1} and row["justification"] in JUSTIFICATION.values() for row in observations)
        assert all(row["callbackCount"] == (0 if row["state"] == "NOT_REACHED" else 1) for row in observations)
        ordering = [(STAGES.index(cast(str, row["stage"])), cast(str, row["location"]), cast(str, row["code"])) for row in findings]
        assert ordering == sorted(ordering)
        assert expected["activation"] == "NONE"
        assert expected["authorityEffect"] == "NO_AUTHORITY_EFFECT"


def test_worker_contains_malformed_and_excessive_stdin() -> None:
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONHASHSEED": "0"}
    for raw in ("{", "x" * 65_537):
        completed = subprocess.run([sys.executable, "-I", "-P", str(MODULE_PATH), "--execute-stdin"], input=raw, text=True, capture_output=True, timeout=5, check=False, env=environment)
        assert completed.returncode != 0
        assert len(completed.stdout.encode("utf-8")) <= 65_536


def test_protected_executor_region_is_unique_closed_and_oracle_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    start, end = "# ISSUE435_EXECUTOR_V1_START\n", "# ISSUE435_EXECUTOR_V1_END"
    assert source.count(start) == source.count(end) == 1
    region = source.split(start, 1)[1].split(end, 1)[0]
    tree = ast.parse(region)
    assert all(isinstance(node, ast.FunctionDef) for node in tree.body)
    functions = cast(list[ast.FunctionDef], tree.body)
    assert [node.name for node in functions if node.name == "execute"] == ["execute"]
    assert all(node.name == "execute" or node.name.startswith("_execute_") for node in functions)
    assert not any(node.decorator_list or node.args.defaults or node.args.kw_defaults for node in functions)
    assert not any(isinstance(node, ast.Global | ast.Nonlocal | ast.NamedExpr | ast.Import | ast.ImportFrom) for node in ast.walk(tree))
    forbidden = ("caseId", "threatId", "testClass", "ACP-C", RAW_SHA256, SEMANTIC_SHA256, "__import__", "importlib", "eval(", "exec(", "compile(", "open(", "os.", "Path(", "socket", "urllib", "subprocess", "getattr(", "setattr(", "delattr(", "globals(", "locals(", "vars(", "__")
    assert not any(term in region for term in forbidden)
    if FREEZE_PATH.exists():
        freeze = _load(FREEZE_PATH)
        c2 = cast(dict[str, object], freeze["c2"])
        frozen = subprocess.run(["/usr/bin/git", "show", f"{c2['head']}:{MODULE_PATH.relative_to(ROOT)}"], cwd=ROOT, capture_output=True, check=False).stdout.decode()
        def normalize(text: str) -> str:
            return text.split(start, 1)[0] + start + "<C4_EXECUTOR_REGION>\n" + end + text.split(end, 1)[1]
        assert normalize(source) == normalize(frozen)


def test_revised_path_caps_executor_ceiling_and_aggregate_thresholds_are_exact() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    start, end = "# ISSUE435_EXECUTOR_V1_START\n", "# ISSUE435_EXECUTOR_V1_END"
    caps = _module_probe("[m['ISSUE435_CAPS']['scripts/quality/adversarial_convergence.py'],m['ISSUE435_CAPS']['tests/unit/test_adversarial_convergence.py']]")
    assert caps == [900, 1000]
    budget = "(lambda c:None if c is None else str(c))(m['_budget_code'](sys.argv[2],int(sys.argv[3]),sys.argv[4]=='true'))"
    module_path, test_path = "scripts/quality/adversarial_convergence.py", "tests/unit/test_adversarial_convergence.py"
    assert _module_probe(budget, module_path, "809", "true") is None
    assert _module_probe(budget, module_path, "809", "false") == "ACP.AUTH.BUDGET_REVIEW_REQUIRED"
    assert _module_probe(budget, module_path, "810", "true") == "ACP.AUTH.BUDGET_STOP"
    assert _module_probe(budget, test_path, "899", "true") is None
    assert _module_probe(budget, test_path, "899", "false") == "ACP.AUTH.BUDGET_REVIEW_REQUIRED"
    assert _module_probe(budget, test_path, "900", "true") == "ACP.AUTH.BUDGET_STOP"
    assert _module_probe("[m['_aggregate_over_budget'](3500,False),m['_aggregate_over_budget'](3501,False),m['_aggregate_over_budget'](3620,True),m['_aggregate_over_budget'](3621,True)]") == [False, True, False, True]
    probe = "m['_normalized_source'](sys.stdin.buffer.read()) is not None"
    assert _module_probe(probe, input_text="# ISSUE435_EXECUTOR_V1_START\n" + "pass\n" * 240 + "# ISSUE435_EXECUTOR_V1_END") is True
    assert _module_probe(probe, input_text="# ISSUE435_EXECUTOR_V1_START\n" + "pass\n" * 241 + "# ISSUE435_EXECUTOR_V1_END") is False
    region = source.split(start, 1)[1].split(end, 1)[0]
    assert len(source.splitlines()) - len(region.splitlines()) + 240 <= 790


def test_path_and_descriptor_boundaries_reject_hostile_nodes(tmp_path: Path) -> None:
    invalid = ("", "/root", "~/x", "a//b", "a/../b", "a\\b", "a/\x01b", "trailing/")
    for relative in invalid:
        assert _module_probe("m['_valid_relative_path'](sys.argv[2])", relative) is False
    (tmp_path / "regular.json").write_text("{}", encoding="utf-8")
    (tmp_path / "target.json").symlink_to(tmp_path / "regular.json")
    os.mkfifo(tmp_path / "fifo")
    probe = "(lambda r: None if r.finding is None else str(r.finding.code))(m['read_bounded_regular_file'](m['Path'](sys.argv[2]),sys.argv[3],8))"
    assert _module_probe(probe, str(tmp_path), "regular.json") is None
    assert _module_probe(probe, str(tmp_path), "target.json") == "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT"
    assert _module_probe(probe, str(tmp_path), "fifo") == "ACP.BOUNDS.UNSAFE_FILESYSTEM_INPUT"


def test_descriptor_boundary_detects_short_read_and_replacement(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    runner = "import json,os,runpy,sys;m=runpy.run_path(sys.argv[1],run_name='probe');old=os.read;os.read=lambda fd,n:b'';r=m['read_bounded_regular_file'](m['Path'](sys.argv[2]),'target.json',8);print(json.dumps(str(r.finding.code)))"
    completed = subprocess.run([sys.executable, "-I", "-P", "-c", runner, str(MODULE_PATH), str(tmp_path)], text=True, capture_output=True, check=False)
    assert completed.returncode == 0 and json.loads(completed.stdout) == "ACP.VERDICT.RESOURCE_FAILURE"
    replacement = tmp_path / "replacement.json"
    replacement.write_text("[]", encoding="utf-8")
    runner = "import json,os,runpy,sys;m=runpy.run_path(sys.argv[1],run_name='probe');old=os.read;done=[False];f=lambda fd,n:(os.replace(sys.argv[3],sys.argv[2]+'/target.json'),done.__setitem__(0,True),old(fd,n))[2] if not done[0] else old(fd,n);os.read=f;r=m['read_bounded_regular_file'](m['Path'](sys.argv[2]),'target.json',8);print(json.dumps(str(r.finding.code)))"
    completed = subprocess.run([sys.executable, "-I", "-P", "-c", runner, str(MODULE_PATH), str(tmp_path), str(replacement)], text=True, capture_output=True, check=False)
    assert completed.returncode == 0 and json.loads(completed.stdout) == "ACP.VERDICT.RESOURCE_FAILURE"


def test_event_branch_resolution_accepts_detached_and_rejects_conflict() -> None:
    expression = "m['_resolve_branch'](sys.argv[2],sys.argv[3])"
    assert _module_probe(expression, ISSUE435_BRANCH, "") == ISSUE435_BRANCH
    assert _module_probe(expression, ISSUE435_BRANCH, "conflict") == ""


def test_hosted_route_head_accepts_exact_detached_checkout_topologies(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    subprocess.run(["/usr/bin/git", "clone", "--quiet", "--no-local", str(ROOT), str(checkout)], check=True)
    head = os.environ.get("GITHUB_HEAD_SHA") or subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
    source_diff = subprocess.check_output(["/usr/bin/git", "diff", "--binary", "--full-index", ISSUE435_BASE, head, "--"], cwd=ROOT)
    cloned_diff = subprocess.check_output(["/usr/bin/git", "diff", "--binary", "--full-index", ISSUE435_BASE, head, "--"], cwd=checkout)
    assert source_diff == cloned_diff
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "--detach", ISSUE435_BASE], cwd=checkout, check=True)
    subprocess.run(
        ["/usr/bin/git", "-c", "user.name=CI", "-c", "user.email=ci@example.invalid", "merge", "--quiet", "--no-ff", "--no-edit", head],
        cwd=checkout,
        check=True,
    )
    expression = "m['_route_head'](m['Path'](sys.argv[2]),sys.argv[3])"
    environment = {"GITHUB_HEAD_REF": ISSUE435_BRANCH, "GITHUB_BASE_SHA": ISSUE435_BASE, "GITHUB_HEAD_SHA": head}
    missing_head = {"GITHUB_HEAD_REF": ISSUE435_BRANCH, "GITHUB_BASE_SHA": ISSUE435_BASE}
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=environment) == head
    hostile = (
        {**environment, "GITHUB_HEAD_REF": "wrong-branch"}, {**environment, "GITHUB_HEAD_REF": f" {ISSUE435_BRANCH} "},
        {**environment, "GITHUB_BASE_SHA": "0" * 40}, {**environment, "GITHUB_BASE_SHA": f" {ISSUE435_BASE} "},
        {**environment, "GITHUB_HEAD_SHA": "0" * 40},
        {**environment, "GITHUB_HEAD_SHA": head.upper()},
        missing_head,
    )
    assert all(_module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=item) == "" for item in hostile)
    unauthorized_base = subprocess.check_output(["/usr/bin/git", "rev-parse", f"{head}^"], cwd=checkout, text=True).strip()
    paired = subprocess.check_output(
        ["/usr/bin/git", "-c", "user.name=CI", "-c", "user.email=ci@example.invalid", "commit-tree", f"{head}^{{tree}}", "-p", unauthorized_base, "-p", head],
        cwd=checkout,
        input="synthetic paired base\n",
        text=True,
    ).strip()
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "--detach", paired], cwd=checkout, check=True)
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env={**environment, "GITHUB_BASE_SHA": unauthorized_base}) == ""
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "--detach", head], cwd=checkout, check=True)
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=environment) == head and _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=missing_head) == head and _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env={**missing_head, "GITHUB_BASE_SHA": unauthorized_base}) == head and _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env={**environment, "GITHUB_BASE_SHA": unauthorized_base}) == head
    reverse = subprocess.check_output(
        ["/usr/bin/git", "-c", "user.name=CI", "-c", "user.email=ci@example.invalid", "commit-tree", f"{head}^{{tree}}", "-p", head, "-p", ISSUE435_BASE, "-p", unauthorized_base],
        cwd=checkout,
        input="synthetic reverse\n",
        text=True,
    ).strip()
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "--detach", reverse], cwd=checkout, check=True)
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=environment) == ""
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "-B", "attached", head], cwd=checkout, check=True)
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env=missing_head) == ""
    subprocess.run(["/usr/bin/git", "checkout", "--quiet", "--detach", ISSUE435_BASE], cwd=checkout, check=True)
    assert _module_probe(expression, str(checkout), ISSUE435_BRANCH, extra_env={**environment, "GITHUB_HEAD_SHA": ISSUE435_BASE}) == ""


def test_route_inspector_never_reads_candidate_evidence_from_ambient_head() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    inspector = source.split("def inspect_issue435_repository", 1)[1].split("def _resolve_branch", 1)[0]
    assert '"HEAD:' not in inspector and "..HEAD" not in inspector and "commits[-1]" in inspector and "commits[-2]" in inspector and "commits[27]" not in inspector and "commits[28]" not in inspector
    freeze_validator = source.split("def _valid_freeze", 1)[1].split("def _budget_code", 1)[0]
    assert '"--full-index"' in freeze_validator


def test_matrix_cross_fields_reject_duplicates_missing_tests_and_coverage() -> None:
    matrix = {"schemaVersion": "AdversarialInvariantMatrixV1", "threatUniverse": ["SLICE-T01"], "invariants": [{"invariantId": "INV-ONE", "threatId": "SLICE-T01", "evidenceClass": "TEST", "testIds": ["test_one"]}]}
    expression = "m['validate_matrix_cross_fields'](json.loads(sys.stdin.read()))"
    assert _module_probe(expression, input_text=json.dumps(matrix)) is True
    duplicate = copy.deepcopy(matrix)
    cast(list[object], duplicate["invariants"]).append(copy.deepcopy(cast(list[object], duplicate["invariants"])[0]))
    assert _module_probe(expression, input_text=json.dumps(duplicate)) is False
    missing_test = copy.deepcopy(matrix)
    cast(dict[str, object], cast(list[object], missing_test["invariants"])[0])["testIds"] = []
    assert _module_probe(expression, input_text=json.dumps(missing_test)) is False
    uncovered = copy.deepcopy(matrix)
    cast(list[str], uncovered["threatUniverse"]).append("SLICE-T02")
    assert _module_probe(expression, input_text=json.dumps(uncovered)) is False


@pytest.mark.parametrize("case", CASES, ids=lambda case: cast(str, case["caseId"]))
def test_future_validator_matches_test_owned_expectation(case: dict[str, object]) -> None:
    expected = _expected(cast(str, case["caseId"]))
    _assert_case(case, expected_override=expected)
    held_out = _held_out(case, expected)
    if held_out is not None:
        stimulus, held_expected = held_out
        transformed = dict(case)
        transformed["stimulus"] = stimulus
        _assert_case(transformed, expected_override=held_expected)


@pytest.mark.parametrize("row", HOSTILE_REGRESSIONS, ids=lambda row: cast(str, row[0]))
def test_future_validator_rejects_hostile_regressions(row: tuple[str, dict[str, object], tuple[str, str, str, str, str]]) -> None:
    label, stimulus, (verdict, stage, code, location, trace) = row
    findings = [] if not code else [{"stage": stage, "code": code, "location": location, "blocker": "EVIDENCE" if verdict == "BLOCKED_EVIDENCE" else "IMPLEMENTATION"}]
    observations = []
    for stage_name, symbol in zip(STAGES, trace, strict=True):
        observations.append({"stage": stage_name, "state": STATE[symbol], "callbackCount": 0 if symbol == "X" else 1, "justification": JUSTIFICATION[symbol], "findingCodes": [code] if symbol == "R" and stage_name == stage else []})
    executions: list[dict[str, object]] = []
    if code == "ACP.TRUST.MOCK_LEDGER_INVALID":
        payload = cast(dict[str, object], stimulus["payload"])
        executions = [{"candidate": item["candidate"], "ordinal": item["ordinal"], "phase": item["phase"], "stage": item["stage"], "callbackCount": item["callbackCount"], "observedState": item["observedState"], "observedFindingCodes": item["observedFindingCodes"]} for item in cast(list[dict[str, object]], payload["rows"])]
    expected: dict[str, object] = {"verdict": verdict, "findings": findings, "observations": observations, "executionReceipts": executions, "mutationReceipts": [], "activation": "NONE", "authorityEffect": "NO_AUTHORITY_EFFECT"}
    _assert_case({"caseId": label, "threatId": "ACP-T03", "stimulus": stimulus}, expected_override=expected)


def _actual(case_id: str) -> dict[str, object]:
    return copy.deepcopy(_expected(case_id))


def _m01(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C002")
    result["verdict"] = "VALID"
    return result


def _m02(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C006")
    cast(list[dict[str, object]], result["observations"])[1]["state"] = "ACCEPTED"
    return result


def _m03(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C011")
    result["findings"] = []
    return result


def _m04(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C014")
    cast(list[dict[str, object]], result["observations"])[7]["callbackCount"] = 1
    return result


def _m05(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C017")
    cast(list[object], result["findings"]).reverse()
    return result


def _m06(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C019")
    receipt = cast(list[dict[str, object]], result["mutationReceipts"])[1]
    receipt.update({"executionCount": 1, "failureCount": 1, "state": "KILLED"})
    return result


def _m07(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C022")
    cast(list[object], result["executionReceipts"]).append({})
    return result


def _m08(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C025")
    cast(list[dict[str, object]], result["observations"])[4]["state"] = "ACCEPTED"
    return result


def _m09(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C028")
    cast(list[dict[str, object]], result["observations"])[4]["state"] = "ACCEPTED"
    return result


def _m10(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C031")
    cast(list[dict[str, object]], result["observations"])[5]["state"] = "ACCEPTED"
    return result


def _m11(_: dict[str, object]) -> dict[str, object]:
    result = _actual("ACP-C036")
    result["verdict"] = "VALID"
    return result


def _m12(_: dict[str, object]) -> dict[str, object]:
    raise MemoryError("controlled test-only mutant")


def _run_mutant(case_id: str, mutant: Executor, assertion_id: str) -> None:
    count = 0
    def measured(stimulus: dict[str, object]) -> dict[str, object]:
        nonlocal count
        count += 1
        return mutant(stimulus)
    caught: AssertionError | None = None
    try:
        _assert_case(_case(case_id), measured)
    except AssertionError as error:
        caught = error
    assert count == 1
    assert caught is not None
    assert assertion_id in str(caught)


def test_m01_real_unsafe_filesystem_mutant_is_killed() -> None:
    _run_mutant("ACP-C002", _m01, "ACP-A01-VERDICT")


def test_m02_real_parse_order_mutant_is_killed() -> None:
    _run_mutant("ACP-C006", _m02, "ACP-A02-OBSERVATIONS")


def test_m03_real_schema_mutant_is_killed() -> None:
    _run_mutant("ACP-C011", _m03, "ACP-A03-FINDINGS")


def test_m04_real_predecessor_mutant_is_killed() -> None:
    _run_mutant("ACP-C014", _m04, "ACP-A04-CALLBACK-COUNTS")


def test_m05_real_subset_mutant_is_killed() -> None:
    _run_mutant("ACP-C017", _m05, "ACP-A05-ORDERED-FINDINGS")


def test_m06_real_unexecuted_mutant_credit_is_killed() -> None:
    _run_mutant("ACP-C019", _m06, "ACP-A06-MUTATION-RECEIPTS")


def test_m07_real_fabricated_ledger_mutant_is_killed() -> None:
    _run_mutant("ACP-C022", _m07, "ACP-A07-EXECUTION-RECEIPTS")


def test_m08_real_self_review_mutant_is_killed() -> None:
    _run_mutant("ACP-C025", _m08, "ACP-A08-REVIEW-TRUST")


def test_m09_real_expectation_channel_mutant_is_killed() -> None:
    _run_mutant("ACP-C028", _m09, "ACP-A09-EXPECTATION-BOUNDARY")


def test_m10_real_route_mutant_is_killed() -> None:
    _run_mutant("ACP-C031", _m10, "ACP-A10-AUTHORIZATION")


def test_m11_real_checkpoint_mutant_is_killed() -> None:
    _run_mutant("ACP-C036", _m11, "ACP-A11-CHECKPOINT")


def test_m12_real_resource_exception_mutant_is_killed() -> None:
    _run_mutant("ACP-C040", _m12, "ACP-A12-NO-EXCEPTION")


def test_focused_test_helpers_respect_readability_limits() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    spans = [node.end_lineno - node.lineno + 1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.end_lineno]
    assert max(spans) <= 80
    assert {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.end_lineno and node.end_lineno - node.lineno + 1 > 50} <= {"_hostile_regressions"}
