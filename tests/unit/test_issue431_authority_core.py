"""RED contract for Issue #431 Child A routing and fail-closed fixture inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality import check_stage8_docs as stage8
from scripts.quality import issue431_authority_core as authority


ROOT = Path(__file__).resolve().parents[2]
BRANCH = "cut1-process-431-authority-core-schemas-state-matrices"
PATHS = {
    "docs/governance/preflights/issue-431.json",
    "docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md",
    "docs/governance/schemas/master-program-authority-decision-v1.schema.json",
    "docs/governance/schemas/cut1-authority-manifest-v1.schema.json",
    "docs/governance/schemas/active-program-route-v1.schema.json",
    "docs/governance/authority-core-state-matrices-v1.json",
    "tests/fixtures/authority-core-v1-cases.json",
    "scripts/quality/issue431_authority_core.py",
    "tests/unit/test_issue431_authority_core.py",
    "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/ADR/0061-core-authority-schemas-state-matrices.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}


def test_fixture_corpus_is_explicitly_non_authoritative_and_adversarial() -> None:
    corpus = json.loads(
        (ROOT / "tests/fixtures/authority-core-v1-cases.json").read_text(encoding="utf-8")
    )

    assert corpus["schemaVersion"] == "AuthorityCoreFixtureCorpusV1"
    assert corpus["fixtureOnly"] is True
    assert corpus["repository"].endswith(".invalid/narratwin-authority-fixtures")
    assert corpus["activation"] == "NONE"
    assert {case["classification"] for case in corpus["cases"]} == {
        "positive",
        "negative",
        "adversarial",
    }
    assert len({case["id"] for case in corpus["cases"]}) == len(corpus["cases"])


def test_child_a_route_is_exactly_registered() -> None:
    assert stage8.PROCESS_BRANCH_ALLOWED_FILES[BRANCH] == PATHS


def test_child_a_branch_is_stage8_eligible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: BRANCH)
    failures: list[str] = []

    stage8.check_stage_marker_and_branch(failures)

    assert failures == []


def test_canonical_bytes_are_ascii_stable_and_member_sorted() -> None:
    assert authority.canonical_bytes({"z": True, "a": [1, "ASCII"]}) == (
        b'{"a":[1,"ASCII"],"z":true}'
    )


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"value": 1.0}, "FLOAT_PROHIBITED"),
        ({"value": float("nan")}, "NON_FINITE_NUMBER"),
        ({"value": float("inf")}, "NON_FINITE_NUMBER"),
        ({"value": "caf\u00e9"}, "NON_ASCII_STRING"),
        ({"value": [0] * 129}, "COLLECTION_LIMIT"),
    ],
)
def test_canonical_bytes_fail_closed(value: object, code: str) -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.canonical_bytes(value)

    assert caught.value.code == code


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"\xff", "INVALID_UTF8"),
        (b'{"a":1,"a":2}', "DUPLICATE_MEMBER"),
        (b'{"a":', "MALFORMED_JSON"),
        (b'{"value":NaN}', "NON_FINITE_NUMBER"),
        (b'{"value":1.0}', "FLOAT_PROHIBITED"),
        (b' {"a":1}', "NONCANONICAL_BYTES"),
        (b"[" * 13 + b"]" * 13, "DEPTH_LIMIT"),
        (b'"' + b"a" * 131_073 + b'"', "SIZE_LIMIT"),
    ],
)
def test_parser_rejects_malformed_or_noncanonical_bytes(data: bytes, code: str) -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(data, "MasterProgramAuthorityDecisionV1")

    assert caught.value.code == code


def test_parser_rejects_an_unsupported_future_schema_before_semantic_use() -> None:
    with pytest.raises(authority.AuthorityValidationError) as caught:
        authority.validate_authority_bytes(b"{}", "MasterProgramAuthorityDecisionV2")

    assert caught.value.code == "UNSUPPORTED_VERSION"
