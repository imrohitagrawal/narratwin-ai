"""Behavioral contract for the bounded Issue #427 architecture reset gate."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
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


def test_current_main_route_reset_identities_are_exact() -> None:
    assert reset.BASE == "f2a32b8c022c015dfa4e87c700fbfe1ed0d85183"
    assert reset.FIRST_COMMIT == "ec6e4140488e96fee9b979125c37a7572c5c7a30"
    assert reset.PREFLIGHT == reset.ProposalIdentity(
        "e347d0b01205d84d655e862384f3797dc623f5839c66ec58756065d9baa2925e",
        4_260,
        54,
    )
    assert reset.PROPOSAL == reset.ProposalIdentity(
        "794c2e90034a8012363a6a859dd3bac826280452e787b8a7afe5a49164849b29",
        17_853,
        326,
    )
    assert reset.MERGED_HEAD == "6635e98c0eb6f45d9b046da0f78e2f3d3adba236"
    assert reset.MERGE_COMMIT == "4d239942eeda0c0b6c385b2d85dae873af076aa6"


def test_serialized_successor_uses_only_the_merged_frozen_reset_head(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    assert reset.ci_route_head(source) == reset.MERGED_HEAD
    checkout = tmp_path / "premerge"
    subprocess.run(
        ["/usr/bin/git", "clone", "--quiet", "--no-local", str(source), str(checkout)], check=True
    )
    subprocess.run(
        ["/usr/bin/git", "checkout", "--quiet", "--detach", reset.BASE], cwd=checkout, check=True
    )
    assert reset.ci_route_head(checkout) == reset.BASE


def test_current_main_base_contains_the_reviewed_security_renewal() -> None:
    root = Path(__file__).resolve().parents[2]
    lock = json.loads((root / "frontend/package-lock.json").read_text())
    assert lock["packages"]["node_modules/nanoid"]["version"] == "3.3.18"
    assert "OVERRIDE_EXPIRY = dt.date(2026, 8, 28)" in (
        root / "scripts/ci/check_semgrep_security.py"
    ).read_text()


def facts() -> reset.RepositoryFacts:
    return reset.RepositoryFacts(
        branch=reset.BRANCH,
        base=reset.BASE,
        changed_paths=reset.PATHS,
        charged_lines=2000,
        numstat_valid=True,
        first_commit=reset.FIRST_COMMIT,
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


def test_repository_facts_reject_a_rewritten_first_commit_identity() -> None:
    findings = reset.repository_findings(replace(facts(), first_commit="0" * 40))

    assert any("first commit identity" in item.lower() for item in findings)


def test_repository_facts_accept_the_ci_detached_head(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = Path(__file__).resolve().parents[2]
    checkout = tmp_path / "checkout"
    head = reset.ci_route_head(source)
    subprocess.run(
        ["/usr/bin/git", "clone", "--quiet", "--no-local", str(source), str(checkout)], check=True
    )
    subprocess.run(
        ["/usr/bin/git", "checkout", "--quiet", "--detach", head], cwd=checkout, check=True
    )
    monkeypatch.setenv("GITHUB_HEAD_REF", reset.BRANCH)

    assert reset.repository_findings(reset.collect_repository_facts(checkout)) == []


def test_ci_detached_fixture_uses_route_parent_of_synthetic_merge(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = Path(__file__).resolve().parents[2]
    route_head = reset.ci_route_head(source)
    synthetic = tmp_path / "synthetic"
    subprocess.run(
        ["/usr/bin/git", "clone", "--quiet", "--no-local", str(source), str(synthetic)], check=True
    )
    subprocess.run(
        ["/usr/bin/git", "checkout", "--quiet", "--detach", reset.BASE], cwd=synthetic, check=True
    )
    subprocess.run(
        ["/usr/bin/git", "-c", "user.name=CI", "-c", "user.email=ci@example.invalid",
         "merge", "--quiet", "--no-ff", "--no-edit", route_head], cwd=synthetic, check=True
    )
    monkeypatch.setenv("GITHUB_HEAD_REF", reset.BRANCH)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {
        "base": {"sha": reset.BASE}, "head": {"sha": route_head, "ref": reset.BRANCH},
    }}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)

    assert reset.ci_route_head(synthetic) == route_head
    assert reset.repository_findings(reset.collect_repository_facts(synthetic)) == []
    valid = event.read_bytes()
    configured_base = reset.BASE
    monkeypatch.setenv("GITHUB_BASE_SHA", configured_base)
    invalid = (
        b'{"pull_request":NaN}',
        b'{"pull_request":{},"pull_request":{}}',
        b'{"pull_request":',
        valid.replace(reset.BASE.encode(), b"0" * 40),
        valid.replace(route_head.encode(), b"0" * 40),
        valid.replace(reset.BRANCH.encode(), b"wrong-branch"),
        valid.replace(f'"{reset.BASE}"'.encode(), b"427"),
    )
    for hostile in invalid:
        event.write_bytes(hostile)
        assert reset.ci_route_head(synthetic) != route_head
    event.write_bytes(b"x" * (reset.EVENT_MAX_BYTES + 1))
    assert reset.ci_route_head(synthetic) != route_head
    target = tmp_path / "event-target.json"
    target.write_bytes(valid)
    event.unlink()
    event.symlink_to(target)
    assert reset.ci_route_head(synthetic) != route_head
    event.unlink()
    os.mkfifo(event)
    assert reset.ci_route_head(synthetic) != route_head
    event.unlink()
    monkeypatch.delenv("GITHUB_EVENT_PATH")
    assert reset.ci_route_head(synthetic) == route_head


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


def test_closed_json_rejects_non_finite_constants() -> None:
    with pytest.raises(ValueError):
        reset.closed_json(b'{"a":NaN}', {"a"})


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"schema_version": "GovernancePreflightV2"}),
        lambda value: value["scope"].update({"forbidden": value["scope"]["forbidden"][:-1]}),
        lambda value: value.update(
            {"objective": value["objective"] + " This preflight activates production authority."}
        ),
    ],
)
def test_preflight_rejects_schema_forbidden_and_activation_drift(
    mutation: Callable[[dict[str, Any]], None]
) -> None:
    root = Path(__file__).resolve().parents[2]
    value = json.loads((root / reset.PREFLIGHT_PATH).read_bytes())
    mutation(value)

    assert reset.preflight_findings(json.dumps(value).encode())


@pytest.mark.parametrize(
    "raw",
    [
        b"1\t-\tbinary\0",
        b"1\t2",
        b"bad\t2\tpath\0",
        b"1\t2\t\xff\0",
        b"1\t2\0",
        b"-100\t2100\tpath\0",
        b"+1\t2\tpath\0",
        b" 1\t2\tpath\0",
        b"1 \t2\tpath\0",
        b"1\t2\t\0",
    ],
)
def test_numstat_parser_rejects_binary_malformed_and_non_utf8_output(raw: bytes) -> None:
    assert reset._charge(raw)[1] is False


def test_numstat_parser_charges_additions_plus_deletions() -> None:
    assert reset._charge(b"3\t4\tone\0" + b"5\t6\ttwo\0") == (18, True)


def test_git_runner_is_absolute_allowlisted_and_uses_bounded_reader(monkeypatch: Any, tmp_path: Any) -> None:
    captured: dict[str, Any] = {}

    class Process:
        returncode = 0

    def popen(args: list[str], **kwargs: Any) -> Process:
        captured.update({"args": args, **kwargs})
        return Process()

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(reset, "_bounded_process_output", lambda process: b"ok")
    assert reset._git(tmp_path, "status") == b"ok"
    assert captured["args"] == ["/usr/bin/git", "status"]
    assert captured["shell"] is False
    assert set(captured["env"]) == {
        "PATH", "LC_ALL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_OPTIONAL_LOCKS",
        "GIT_NO_LAZY_FETCH", "GIT_NO_REPLACE_OBJECTS",
    }


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_process_output_is_stopped_while_crossing_the_bound(
    stream: str, tmp_path: Path
) -> None:
    sentinel = tmp_path / f"{stream}-completed"
    script = (
        "import pathlib,sys,time; "
        f"stream=sys.{stream}.buffer; "
        "stream.write(b'x'*1_000_001); stream.flush(); "
        "time.sleep(1); "
        f"pathlib.Path({str(sentinel)!r}).write_text('completed')"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    with pytest.raises(RuntimeError):
        reset._bounded_process_output(process, timeout=3)
    assert not sentinel.exists()


def test_frozen_file_reader_rejects_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"safe")
    (tmp_path / "linked").symlink_to(target)

    with pytest.raises(OSError):
        reset.read_frozen_file(tmp_path, "linked", 4)


def test_frozen_file_reader_rejects_oversized_regular_files(tmp_path: Path) -> None:
    (tmp_path / "oversized").write_bytes(b"12345")

    with pytest.raises(OSError):
        reset.read_frozen_file(tmp_path, "oversized", 4)


def test_frozen_file_reader_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    root = Path(__file__).resolve().parents[2]
    script = (
        "from pathlib import Path; "
        "from scripts.quality.issue427_architecture_reset import read_frozen_file; "
        f"read_frozen_file(Path({str(tmp_path)!r}), 'fifo', 4)"
    )

    process = subprocess.Popen(
        [sys.executable, "-c", script], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        pytest.fail("frozen file reader blocked while opening a FIFO")
    result = process
    assert result.returncode != 0


def test_proposal_identity_and_structure_are_exact() -> None:
    data = proposal_text().encode()
    assert reset.proposal_findings(data, expected=identity(data)) == []
    assert reset.proposal_findings(data + b"drift", expected=identity(data)) == [
        "Issue #427 proposal identity does not match the approved SHA/bytes/lines."
    ]


OWNER_RESET_PROPOSAL = reset.ProposalIdentity(
    "794c2e90034a8012363a6a859dd3bac826280452e787b8a7afe5a49164849b29", 17_853, 326
)
OWNER_RESET_REVIEWS = {
    reset.ARCHITECTURE_REVIEW_PATH: reset.ProposalIdentity(
        "31e09cec832ee7367251bab9f3514fe4619c42dd59f94d5739c8564010eab94b", 1_639, 29
    ),
    reset.SECURITY_REVIEW_PATH: reset.ProposalIdentity(
        "750878d6acd4a2360860f1446ec15535183024794f1cfdbdf5f826f136cef6c3", 1_997, 37
    ),
}


def route_bytes(path: str) -> bytes:
    root = Path(__file__).resolve().parents[2]
    return reset._git(root, "show", f"{reset.ci_route_head(root)}:{path}")


def test_owner_markdown_reset_proposal_is_exact() -> None:
    data = route_bytes(reset.PROPOSAL_PATH)
    assert identity(data) == OWNER_RESET_PROPOSAL
    assert b"\nIssue #426. The new issue must have" in data
    assert b"\n#426. The new issue must have" not in data


@pytest.mark.parametrize(("path", "expected"), OWNER_RESET_REVIEWS.items())
def test_owner_markdown_reset_review_identity_is_exact(
    path: str, expected: reset.ProposalIdentity
) -> None:
    assert identity(route_bytes(path)) == expected


def test_owner_markdown_reset_is_bound_to_approval_comment() -> None:
    value = json.loads(route_bytes(reset.BINDING_PATH))
    assert value.get("markdownResetRequestComment") == 5287631143
    assert value.get("markdownResetApprovalComment") == 5289686674
    assert value.get("ciRouteResetComment") == 5292268215
    assert value["proposal"] == {
        "path": reset.PROPOSAL_PATH,
        "sha256": OWNER_RESET_PROPOSAL.sha256,
        "bytes": OWNER_RESET_PROPOSAL.bytes,
        "lines": OWNER_RESET_PROPOSAL.lines,
    }


@pytest.mark.parametrize(
    "path",
    [
        reset.PREFLIGHT_PATH,
        "docs/ADR/0060-authority-reconciliation-and-stale-route-phase-spec.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    ],
)
def test_every_active_proposal_identity_surface_names_only_owner_reset(path: str) -> None:
    data = route_bytes(path)
    for marker in (
        OWNER_RESET_PROPOSAL.sha256.encode(), b"17,853", b"5287631143", b"5289686674",
        b"5292268215",
    ):
        assert marker in data
    assert b"bb8513fb82402d9d3e34590569ec2a07b42688a46e395fe9243f0fc2f8408b45" not in data
    assert b"4796ba7847611a1b18882d2164b7f6a94f98c5d0670d226f75c7c558c67feac8" not in data
    assert b"17,847" not in data


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
        "markdownResetRequestComment": 5287631143,
        "markdownResetApprovalComment": 5289686674,
        "ciRouteResetComment": 5292268215,
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
        lambda value: value.update({"markdownResetApprovalComment": 0}),
        lambda value: value.update({"ciRouteResetComment": 0}),
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


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("issue",), 427.0),
        (("issue",), True),
        (("ownerApprovalRequestComment",), 5273122120.0),
        (("ownerApprovalComment",), 5273244742.0),
        (("correctionApprovalRequestComment",), 5273917279.0),
        (("correctionApprovalComment",), 5276469372.0),
        (("markdownResetRequestComment",), 5287631143.0),
        (("markdownResetApprovalComment",), 5289686674.0),
        (("ciRouteResetComment",), 5292268215.0),
        (("proposal", "bytes"), 17_853.0),
        (("proposal", "lines"), 326.0),
        (("architectureReview", "bytes"), 1_639.0),
        (("architectureReview", "lines"), 29.0),
        (("securityReview", "bytes"), 1_997.0),
        (("securityReview", "lines"), 37.0),
    ],
)
def test_binding_rejects_numerically_equal_wrong_scalar_types(
    path: tuple[str, ...], replacement: object
) -> None:
    value = binding()
    target: dict[str, Any] = value
    for member in path[:-1]:
        child = target[member]
        assert isinstance(child, dict)
        target = child
    target[path[-1]] = replacement

    assert reset.binding_findings(json.dumps(value).encode())


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


@pytest.mark.parametrize(
    ("path", "expected"),
    reset.GOVERNANCE_ARTIFACTS,
)
def test_governance_artifacts_reject_appended_authority_claims(
    path: str, expected: reset.ProposalIdentity
) -> None:
    root = Path(__file__).resolve().parents[2]
    route_head = reset.ci_route_head(root)
    original = reset._git(root, "show", f"{route_head}:{path}")
    assert reset.governance_artifact_findings(original, expected, path) == []

    changed = original + b"\nActivation: ACTIVE. Runtime and production authority approved.\n"
    assert reset.governance_artifact_findings(changed, expected, path)


def test_coordinated_security_review_and_binding_mutation_fails_closed() -> None:
    original = b"false-authority security review\n"
    changed = original + b"Activation: ACTIVE\n"
    value = binding()
    security_review = value["securityReview"]
    assert isinstance(security_review, dict)
    security_review["sha256"] = identity(changed).sha256
    assert reset.review_artifact_findings(changed, identity(original), "false-authority security")
    assert reset.binding_findings(json.dumps(value).encode())
