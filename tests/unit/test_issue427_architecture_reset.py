"""Behavioral contract for the bounded Issue #427 architecture reset gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

from scripts.quality import issue427_architecture_reset as reset


def proposal_text() -> str:
    sections = [f"## {number}. Section {number}" for number in range(1, 13)]
    invariants = [f"| `AK-{number:03d}` | invariant | A | proof |" for number in range(1, 24)]
    children = [
        "`A — Core schemas and state matrices`",
        "`B — Evidence and trust`",
        "`C — Projection, CAS and bootstrap`",
        "`D — Audit and closeout coordinator protocol`",
        "`E — Historical reconciliation`",
        "`F — Integrated offline kernel and oracle`",
    ]
    boundaries = [
        "RESET_PROPOSAL_UNAPPROVED",
        "Authority effect | None",
        "No route may mutate governed state before activation.",
        (
            "This document grants no runtime, product, provider, credential, egress, spend, media, "
            "infrastructure, deployment, publication, release, commercial-readiness, SLA, or "
            "production capability."
        ),
        "No child is automatically activated.",
    ]
    return "\n".join([*sections, *invariants, *children, *boundaries]) + "\n"


def identity(data: bytes) -> reset.ProposalIdentity:
    return reset.ProposalIdentity(
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
        lines=data.count(b"\n"),
    )


def facts() -> reset.RepositoryFacts:
    return reset.RepositoryFacts(
        branch=reset.BRANCH,
        base=reset.BASE,
        changed_paths=reset.PATHS,
        charged_lines=2000,
        numstat_valid=True,
        first_commit_paths=(reset.PREFLIGHT_PATH,),
        first_parent=reset.BASE,
        shallow=False,
        replace_refs=(),
        merge_commits=(),
        history_ambiguous=False,
    )


@pytest.mark.parametrize(
    ("mutation", "finding"),
    [
        (lambda value: replace(value, branch=f"{reset.BRANCH}-retry"), "branch"),
        (lambda value: replace(value, base="0" * 40), "base"),
        (lambda value: replace(value, changed_paths=reset.PATHS[:-1]), "scope"),
        (lambda value: replace(value, changed_paths=(*reset.PATHS, "extra.txt")), "scope"),
        (lambda value: replace(value, charged_lines=2001), "budget"),
        (lambda value: replace(value, numstat_valid=False), "numstat"),
        (lambda value: replace(value, first_commit_paths=(reset.PREFLIGHT_PATH, "extra.txt")), "first commit"),
        (lambda value: replace(value, first_parent="0" * 40), "first parent"),
        (lambda value: replace(value, shallow=True), "shallow"),
        (lambda value: replace(value, replace_refs=("refs/replace/x",)), "replace"),
        (lambda value: replace(value, merge_commits=("f" * 40,)), "merge"),
        (lambda value: replace(value, history_ambiguous=True), "history"),
    ],
)
def test_repository_facts_fail_closed(
    mutation: Callable[[reset.RepositoryFacts], reset.RepositoryFacts], finding: str
) -> None:
    assert any(finding in item.lower() for item in reset.repository_findings(mutation(facts())))


def test_repository_facts_accept_only_the_exact_route() -> None:
    assert reset.repository_findings(facts()) == []


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"a":1,"unknown":2}',
        b'{"a":',
        b"\xff",
    ],
)
def test_closed_json_rejects_duplicates_unknown_members_and_malformed_bytes(raw: bytes) -> None:
    with pytest.raises(ValueError):
        reset.closed_json(raw, {"a"})


def test_closed_json_accepts_exact_members() -> None:
    assert reset.closed_json(b'{"a":1}', {"a"}) == {"a": 1}


@pytest.mark.parametrize(
    "raw",
    [b"1\t-\tbinary\0", b"1\t2", b"bad\t2\tpath\0", b"1\t2\t\xff\0", b"1\t2\0"],
)
def test_numstat_parser_rejects_binary_malformed_and_non_utf8_output(raw: bytes) -> None:
    assert reset._charge(raw)[1] is False


def test_numstat_parser_charges_additions_plus_deletions() -> None:
    assert reset._charge(b"3\t4\tone\0" + b"5\t6\ttwo\0") == (18, True)


def test_git_runner_is_bounded_allowlisted_and_fails_on_overflow(monkeypatch: Any, tmp_path: Any) -> None:
    captured: dict[str, Any] = {}

    def overflow(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        captured.update({"args": args, **kwargs})
        return subprocess.CompletedProcess(args, 0, b"x" * 1_000_001, b"")

    monkeypatch.setattr(subprocess, "run", overflow)
    with pytest.raises(RuntimeError):
        reset._git(tmp_path, "status")
    assert captured["args"] == ["/usr/bin/git", "status"]
    assert captured["shell"] is False and captured["timeout"] == 5
    assert set(captured["env"]) == {
        "PATH", "LC_ALL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_OPTIONAL_LOCKS",
        "GIT_NO_LAZY_FETCH", "GIT_NO_REPLACE_OBJECTS",
    }

    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired("git", 5)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError):
        reset._git(tmp_path, "status")


def test_proposal_identity_and_structure_are_exact() -> None:
    data = proposal_text().encode()
    assert reset.proposal_findings(data, expected=identity(data)) == []
    assert reset.proposal_findings(data + b"drift", expected=identity(data)) == [
        "Issue #427 proposal identity does not match the approved SHA/bytes/lines."
    ]


@pytest.mark.parametrize(
    ("mutate", "finding"),
    [
        (lambda text: text.replace("## 2. Section 2", "## 13. Section 2"), "sections"),
        (lambda text: text.replace("## 2. Section 2", "## 1. Section 2"), "sections"),
        (lambda text: text.replace("| `AK-007` | invariant | A | proof |\n", ""), "AK"),
        (
            lambda text: text.replace(
                "| `AK-007` | invariant | A | proof |",
                "| `AK-006` | invariant | A | proof |",
            ),
            "AK",
        ),
        (
            lambda text: text.replace(
                "`B — Evidence and trust`\n`C — Projection, CAS and bootstrap`",
                "`C — Projection, CAS and bootstrap`\n`B — Evidence and trust`",
            ),
            "children",
        ),
        (lambda text: text.replace("RESET_PROPOSAL_UNAPPROVED", "APPROVED"), "nonactivation"),
        (lambda text: text.replace("Authority effect | None", "Authority effect | Active"), "nonactivation"),
        (
            lambda text: text.replace(
                "No route may mutate governed state before activation.",
                "The route may mutate governed state before activation.",
            ),
            "nonactivation",
        ),
        (lambda text: text.replace("provider", "vendor"), "prohibited"),
    ],
)
def test_proposal_structure_rejects_reorder_duplicate_and_activation_drift(
    mutate: Callable[[str], str], finding: str
) -> None:
    original = proposal_text()
    changed = mutate(original)
    data = changed.encode()
    assert any(finding.lower() in item.lower() for item in reset.proposal_findings(data, expected=identity(data)))


def binding() -> dict[str, object]:
    return {
        "schemaVersion": "Issue427ArchitectureResetBindingV1",
        "state": "RESET_PROPOSAL_UNAPPROVED",
        "issue": 427,
        "branch": reset.BRANCH,
        "base": reset.BASE,
        "proposal": {
            "path": reset.PROPOSAL_PATH,
            "sha256": reset.PROPOSAL.sha256,
            "bytes": reset.PROPOSAL.bytes,
            "lines": reset.PROPOSAL.lines,
        },
        "ownerApprovalRequestComment": 5273122120,
        "ownerApprovalComment": 5273244742,
        "correctionApprovalRequestComment": 5273917279,
        "correctionApprovalComment": 5276469372,
        "architectureReview": {
            "path": reset.ARCHITECTURE_REVIEW_PATH,
            "sha256": reset.ARCHITECTURE_REVIEW.sha256,
            "bytes": reset.ARCHITECTURE_REVIEW.bytes,
            "lines": reset.ARCHITECTURE_REVIEW.lines,
            "proposalSha256": reset.PROPOSAL.sha256,
            "disposition": "PASS_ARCHITECTURE_DECOMPOSITION",
        },
        "securityReview": {
            "path": reset.SECURITY_REVIEW_PATH,
            "sha256": reset.SECURITY_REVIEW.sha256,
            "bytes": reset.SECURITY_REVIEW.bytes,
            "lines": reset.SECURITY_REVIEW.lines,
            "disposition": "NONACTIVATING_FALSE_AUTHORITY_REVIEW_SURFACE",
        },
        "children": list(reset.CHILDREN),
        "activation": "NONE",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"extra": True}),
        lambda value: value.update({"state": "ACCEPTED"}),
        lambda value: value.update({"branch": "wrong"}),
        lambda value: value["proposal"].update({"sha256": "0" * 64}),
        lambda value: value["architectureReview"].update({"proposalSha256": "0" * 64}),
        lambda value: value["securityReview"].update({"sha256": "0" * 64}),
        lambda value: value.update({"correctionApprovalComment": 0}),
        lambda value: value.update({"children": list(reversed(reset.CHILDREN))}),
        lambda value: value.update({"activation": "ACTIVE"}),
    ],
)
def test_binding_rejects_unknown_drift_stale_review_and_activation(
    mutation: Callable[[dict[str, Any]], None]
) -> None:
    value = binding()
    mutation(value)
    assert reset.binding_findings(json.dumps(value).encode())


def test_binding_accepts_only_the_approved_nonactivating_identity() -> None:
    assert reset.binding_findings(json.dumps(binding()).encode()) == []


def test_review_and_claim_surfaces_reject_stale_or_accidental_authority() -> None:
    valid = reset.required_review_text()
    assert reset.review_findings(valid) == []
    assert reset.review_findings(valid.replace(reset.PROPOSAL.sha256, "0" * 64))
    assert reset.review_findings(valid.replace("non-activating", "production-ready"))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data + b"Activation: ACTIVE\n",
        lambda data: data + b"This review authorizes runtime execution.\n",
        lambda data: data + b"Accepted authority decision.\n",
        lambda data: data[:-1],
        lambda data: data.replace(b"review", b"authority", 1),
        lambda data: data + b"\xff",
    ],
)
def test_exact_review_identity_rejects_append_truncate_replace_and_invalid_utf8(
    mutation: Callable[[bytes], bytes],
) -> None:
    original = b"frozen non-activating review\n"
    expected = identity(original)
    assert reset.review_artifact_findings(original, expected, "architecture") == []
    assert reset.review_artifact_findings(mutation(original), expected, "architecture")


def test_required_review_surfaces_validate_false_authority_security_review(tmp_path: Any) -> None:
    security = b"false-authority security review\n"
    (tmp_path / "security.md").write_bytes(security)
    reviews = (
        ("security.md", identity(security), "false-authority security"),
    )
    assert reset.required_review_findings(tmp_path, reviews) == []
    (tmp_path / "security.md").write_bytes(security + b"Activation: ACTIVE\n")
    assert any("security" in item for item in reset.required_review_findings(tmp_path, reviews))


def test_coordinated_security_review_and_binding_mutation_fails_closed() -> None:
    original = b"false-authority security review\n"
    changed = original + b"Activation: ACTIVE\n"
    value = binding()
    security_review = value["securityReview"]
    assert isinstance(security_review, dict)
    security_review["sha256"] = identity(changed).sha256
    assert reset.review_artifact_findings(changed, identity(original), "false-authority security")
    assert reset.binding_findings(json.dumps(value).encode())
