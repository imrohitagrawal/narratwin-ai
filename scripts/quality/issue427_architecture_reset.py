"""Fail-closed gate for the bounded, non-activating Issue #427 reset route."""

from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.quality.branch_identity import current_branch

BRANCH = "cut1-process-427-authority-architecture-reset"
BASE = "a02286240212ad8958915aec01aa5ebaf60fa705"
FIRST_COMMIT = "8954f0ab09c1c8c5d0d6ffeb54272d764140493d"
PREFLIGHT_PATH = "docs/governance/preflights/issue-427.json"
PROPOSAL_PATH = "docs/governance/AUTHORITY_RECONCILIATION_AND_STALE_ROUTE_PHASE_SPEC_V1.md"
BINDING_PATH = "docs/governance/authority-reconciliation-and-stale-route-phase-spec-v1.json"
ARCHITECTURE_REVIEW_PATH = "docs/reviews/ISSUE_427_AUTHORITY_ROUTE_SPEC_REVIEW.md"
SECURITY_REVIEW_PATH = "docs/reviews/ISSUE_427_FALSE_AUTHORITY_SECURITY_REVIEW.md"
PATHS = (
    PREFLIGHT_PATH,
    PROPOSAL_PATH,
    BINDING_PATH,
    ARCHITECTURE_REVIEW_PATH,
    SECURITY_REVIEW_PATH,
    "docs/ADR/0060-authority-reconciliation-and-stale-route-phase-spec.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/QUALITY_GATES.md",
    "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py",
    "scripts/quality/issue427_architecture_reset.py",
    "tests/unit/test_issue427_architecture_reset.py",
)
CHILDREN = (
    "A — Core schemas and state matrices",
    "B — Evidence and trust",
    "C — Projection, CAS and bootstrap",
    "D — Audit and closeout coordinator protocol",
    "E — Historical reconciliation",
    "F — Integrated offline kernel and oracle",
)


@dataclass(frozen=True)
class ProposalIdentity:
    sha256: str
    bytes: int
    lines: int


PROPOSAL = ProposalIdentity(
    "bb8513fb82402d9d3e34590569ec2a07b42688a46e395fe9243f0fc2f8408b45",
    17_847,
    326,
)
PREFLIGHT = ProposalIdentity(
    "6c8d3c93891f0555976a16068b7fa0100b984173aa19aaf8b8a20dcea61e0200",
    4_067,
    54,
)

ARCHITECTURE_REVIEW = ProposalIdentity(
    "766b19ce823dadba152631516bd5e2af658cbf073f770a713c76417abacc0f2e",
    1_540,
    28,
)
SECURITY_REVIEW = ProposalIdentity(
    "af5026a51d0319cbde0cd0e95d2eab84bcda0bfe3a3958300c055bc616b9e49f",
    1_809,
    35,
)
REVIEW_ARTIFACTS = (
    (ARCHITECTURE_REVIEW_PATH, ARCHITECTURE_REVIEW, "architecture"),
    (SECURITY_REVIEW_PATH, SECURITY_REVIEW, "false-authority security"),
)
GOVERNANCE_ARTIFACTS = (
    ("docs/ADR/0060-authority-reconciliation-and-stale-route-phase-spec.md",
     ProposalIdentity("70bf0d70a094eb13b4ba872ae8928b9b534347549d06433d6ca6cbcfe06481ab", 3_141, 66)),
    ("docs/STAGE_ISSUE_PLAN.md",
     ProposalIdentity("5baadf4810b870ac1c79b9101404a070e0f93babbb5ff1df17d562bb56ca73bf", 139_531, 2_708)),
    ("docs/STATUS.md",
     ProposalIdentity("6b3e769117171dd9201c3d2e4a023d3c9aec229645a6c281ac8243e8ca5f3926", 232_021, 1_478)),
    ("docs/TRACEABILITY.md",
     ProposalIdentity("b61b4cd57dc868c38fbf93b0587a53539b592f9537231250f0ad3441990f018a", 142_701, 585)),
    ("docs/QUALITY_GATES.md",
     ProposalIdentity("e740fa14d353d96abeffa4884af1e1ec1168994182dd710b5ea971ec0e785d77", 86_297, 1_386)),
)


def governance_artifact_findings(
    data: bytes, expected: ProposalIdentity, path: str
) -> list[str]:
    return [] if _identity(data) == expected else [
        f"Issue #427 governance artifact drifted or contains authority claims: {path}."
    ]


def required_governance_findings(
    root: Path,
    artifacts: tuple[tuple[str, ProposalIdentity], ...] = GOVERNANCE_ARTIFACTS,
) -> list[str]:
    findings: list[str] = []
    for path, expected in artifacts:
        try:
            data = (root / path).read_bytes()
        except OSError:
            findings.append(f"Issue #427 governance artifact is missing or unreadable: {path}.")
            continue
        findings.extend(governance_artifact_findings(data, expected, path))
    return findings


def review_artifact_findings(
    data: bytes, expected: ProposalIdentity, surface: str
) -> list[str]:
    if _identity(data) != expected:
        return [f"Issue #427 {surface} review identity drifted or contains appended claims."]
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return [f"Issue #427 {surface} review is not UTF-8."]
    return []


def required_review_findings(
    root: Path,
    reviews: tuple[tuple[str, ProposalIdentity, str], ...] = REVIEW_ARTIFACTS,
) -> list[str]:
    findings: list[str] = []
    for path, expected, surface in reviews:
        try:
            data = (root / path).read_bytes()
        except OSError:
            findings.append(f"Issue #427 {surface} review is missing or unreadable.")
            continue
        identity_findings = review_artifact_findings(data, expected, surface)
        findings.extend(identity_findings)
        if not identity_findings and surface == "architecture":
            findings.extend(review_findings(data.decode("utf-8")))
    return findings


@dataclass(frozen=True)
class RepositoryFacts:
    branch: str
    base: str
    changed_paths: tuple[str, ...]
    charged_lines: int
    numstat_valid: bool
    first_commit: str
    first_commit_paths: tuple[str, ...]
    first_parent: str
    shallow: bool
    replace_refs: tuple[str, ...]
    merge_commits: tuple[str, ...]
    history_ambiguous: bool


def repository_findings(facts: RepositoryFacts) -> list[str]:
    findings: list[str] = []
    if facts.branch != BRANCH:
        findings.append("Issue #427 branch does not match the exact reset route.")
    if facts.base != BASE:
        findings.append("Issue #427 base does not match the exact approved base.")
    if len(facts.changed_paths) != len(PATHS) or tuple(sorted(facts.changed_paths)) != tuple(sorted(PATHS)):
        findings.append("Issue #427 scope is missing, extra, duplicated, or reordered.")
    if facts.charged_lines > 2_000 or facts.charged_lines < 0:
        findings.append("Issue #427 charged-line budget is invalid or exceeds 2,000.")
    if not facts.numstat_valid:
        findings.append("Issue #427 Git numstat is failed, binary, or malformed.")
    if facts.first_commit != FIRST_COMMIT:
        findings.append("Issue #427 first commit identity does not match the preserved commit.")
    if facts.first_commit_paths != (PREFLIGHT_PATH,):
        findings.append("Issue #427 first commit must change only the preflight.")
    if facts.first_parent != BASE:
        findings.append("Issue #427 first parent is not the exact approved base.")
    if facts.shallow:
        findings.append("Issue #427 shallow history is not reviewable.")
    if facts.replace_refs:
        findings.append("Issue #427 replace-ref interference is forbidden.")
    if facts.merge_commits:
        findings.append("Issue #427 merge commits make route history ambiguous.")
    if facts.history_ambiguous:
        findings.append("Issue #427 history is unavailable or ambiguous.")
    return findings


def closed_json(raw: bytes, fields: set[str]) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, member in items:
            if key in value:
                raise ValueError(f"duplicate JSON member: {key}")
            value[key] = member
        return value

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("malformed UTF-8 JSON") from error
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("JSON members are missing or unknown")
    return value


def preflight_findings(raw: bytes) -> list[str]:
    fields = {"schema_version", "issue_number", "branch", "objective", "status_decision", "scope"}
    try:
        closed_json(raw, fields)
    except ValueError:
        return ["Issue #427 preflight is not strict UTF-8 JSON."]
    return [] if _identity(raw) == PREFLIGHT else [
        "Issue #427 preflight contract drifted or activates authority."
    ]


def _identity(data: bytes) -> ProposalIdentity:
    return ProposalIdentity(hashlib.sha256(data).hexdigest(), len(data), data.count(b"\n"))


def proposal_findings(data: bytes, *, expected: ProposalIdentity = PROPOSAL) -> list[str]:
    if _identity(data) != expected:
        return ["Issue #427 proposal identity does not match the approved SHA/bytes/lines."]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["Issue #427 proposal is not UTF-8."]
    findings: list[str] = []
    sections = [int(value) for value in re.findall(r"(?m)^## ([1-9][0-9]*)\.", text)]
    if sections != list(range(1, 13)):
        findings.append("Issue #427 proposal sections are missing, duplicated, or reordered.")
    invariants = re.findall(r"(?m)^\| `AK-([0-9]{3})` \|", text)
    if invariants != [f"{number:03d}" for number in range(1, 24)]:
        findings.append("Issue #427 AK invariants are missing, duplicated, or reordered.")
    positions = [text.find(f"`{child}`") for child in CHILDREN]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        findings.append("Issue #427 serialized children are missing or reordered.")
    if any(text.count(f"`{child}`") != 1 for child in CHILDREN):
        findings.append("Issue #427 serialized children are duplicated.")
    nonactivation = (
        "RESET_PROPOSAL_UNAPPROVED",
        "Authority effect | None",
        "No route may mutate governed state before activation.",
    )
    if any(marker not in text for marker in nonactivation):
        findings.append("Issue #427 proposal nonactivation contract drifted.")
    prohibited = ("runtime", "provider", "credential", "spend", "media", "deployment", "release", "production", "commercial")
    if any(marker not in text.lower() for marker in prohibited):
        findings.append("Issue #427 proposal prohibited-capability contract drifted.")
    return findings


def _exact_json_equal(value: object, expected: object) -> bool:
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        if not isinstance(value, dict) or value.keys() != expected.keys():
            return False
        return all(_exact_json_equal(value[key], member) for key, member in expected.items())
    if isinstance(expected, list):
        return isinstance(value, list) and len(value) == len(expected) and all(
            _exact_json_equal(item, member) for item, member in zip(value, expected, strict=True)
        )
    return value == expected


def binding_findings(raw: bytes) -> list[str]:
    top = {"schemaVersion", "state", "issue", "branch", "base", "proposal",
           "ownerApprovalRequestComment", "ownerApprovalComment",
           "correctionApprovalRequestComment", "correctionApprovalComment",
           "architectureReview", "securityReview", "children", "activation"}
    try:
        value = closed_json(raw, top)
        proposal = value["proposal"]
        review = value["architectureReview"]
        security_review = value["securityReview"]
        if not isinstance(proposal, dict) or set(proposal) != {"path", "sha256", "bytes", "lines"}:
            raise ValueError("proposal binding members")
        if not isinstance(review, dict) or set(review) != {
            "path", "sha256", "bytes", "lines", "proposalSha256", "disposition"
        }:
            raise ValueError("review binding members")
        if not isinstance(security_review, dict) or set(security_review) != {
            "path", "sha256", "bytes", "lines", "disposition"
        }:
            raise ValueError("security review binding members")
    except (KeyError, TypeError, ValueError):
        return ["Issue #427 binding JSON is malformed, duplicated, missing, or unknown."]
    expected = {
        "schemaVersion": "Issue427ArchitectureResetBindingV1",
        "state": "RESET_PROPOSAL_UNAPPROVED",
        "issue": 427,
        "branch": BRANCH,
        "base": BASE,
        "proposal": {"path": PROPOSAL_PATH, "sha256": PROPOSAL.sha256,
                     "bytes": PROPOSAL.bytes, "lines": PROPOSAL.lines},
        "ownerApprovalRequestComment": 5273122120,
        "ownerApprovalComment": 5273244742,
        "correctionApprovalRequestComment": 5273917279,
        "correctionApprovalComment": 5276469372,
        "architectureReview": {"path": ARCHITECTURE_REVIEW_PATH,
                               "sha256": ARCHITECTURE_REVIEW.sha256,
                               "bytes": ARCHITECTURE_REVIEW.bytes,
                               "lines": ARCHITECTURE_REVIEW.lines,
                               "proposalSha256": PROPOSAL.sha256,
                               "disposition": "PASS_ARCHITECTURE_DECOMPOSITION"},
        "securityReview": {"path": SECURITY_REVIEW_PATH,
                           "sha256": SECURITY_REVIEW.sha256,
                           "bytes": SECURITY_REVIEW.bytes,
                           "lines": SECURITY_REVIEW.lines,
                           "disposition": "NONACTIVATING_FALSE_AUTHORITY_REVIEW_SURFACE"},
        "children": list(CHILDREN),
        "activation": "NONE",
    }
    return [] if _exact_json_equal(value, expected) else [
        "Issue #427 binding drifted, has wrong scalar types, or activates authority."
    ]


def required_review_text() -> str:
    return (
        "PASS — architecture decomposition planning gate\n"
        f"proposal SHA-256: {PROPOSAL.sha256}\n"
        f"proposal bytes: {PROPOSAL.bytes}\nproposal LF lines: {PROPOSAL.lines}\n"
        "This disposition is non-activating and grants no runtime, provider, credential, spend, "
        "media, deployment, release, production, SLA, or commercial-readiness capability.\n"
    )


def review_findings(text: str) -> list[str]:
    required = required_review_text().splitlines()
    lowered = text.lower()
    if any(line not in text for line in required) or "production-ready" in lowered:
        return ["Issue #427 architecture review identity or nonactivation disposition is stale."]
    return []


def _bounded_process_output(
    process: subprocess.Popen[bytes], *, timeout: float = 5, limit: int = 1_000_000
) -> bytes:
    if process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise RuntimeError("bounded Git pipes are unavailable")
    selector = selectors.DefaultSelector()
    chunks: dict[int, list[bytes]] = {
        process.stdout.fileno(): [],
        process.stderr.fileno(): [],
    }
    total = 0
    deadline = time.monotonic() + timeout
    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout)
            events = selector.select(remaining)
            if not events:
                raise subprocess.TimeoutExpired(process.args, timeout)
            for key, _ in events:
                data = os.read(key.fd, min(65_536, limit - total + 1))
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                total += len(data)
                if total > limit:
                    raise RuntimeError("bounded Git command overflowed")
                chunks[key.fd].append(data)
        process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except BaseException:
        process.kill()
        process.wait()
        raise
    finally:
        selector.close()
    return b"".join(chunks[process.stdout.fileno()])


def _git(root: Path, *args: str) -> bytes:
    env = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    try:
        process = subprocess.Popen(
            ["/usr/bin/git", *args], cwd=root, env=env, shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout = _bounded_process_output(process)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("bounded Git command failed") from error
    if process.returncode:
        raise RuntimeError("bounded Git command failed")
    return stdout


def _zlist(raw: bytes) -> tuple[str, ...]:
    if raw and not raw.endswith(b"\0"):
        raise ValueError("malformed NUL list")
    try:
        return tuple(item.decode("utf-8") for item in raw.split(b"\0")[:-1])
    except UnicodeDecodeError as error:
        raise ValueError("non-UTF-8 Git path") from error


def collect_repository_facts(root: Path) -> RepositoryFacts:
    try:
        branch = current_branch(root)
        head = _git(root, "rev-parse", "HEAD").decode().strip()
        base = _git(root, "merge-base", BASE, head).decode().strip()
        shallow = _git(root, "rev-parse", "--is-shallow-repository").decode().strip() != "false"
        replaces = tuple(line for line in _git(root, "replace", "-l").decode().splitlines() if line)
        commits = tuple(line for line in _git(root, "rev-list", "--reverse", f"{BASE}..{head}").decode().splitlines() if line)
        if not commits:
            raise ValueError("no branch commits")
        first = commits[0]
        first_paths = _zlist(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", first, "--"))
        first_parent = _git(root, "rev-parse", f"{first}^").decode().strip()
        merges = tuple(line for line in _git(root, "rev-list", "--min-parents=2", f"{BASE}..{head}").decode().splitlines() if line)
        paths = tuple(sorted(_zlist(_git(root, "diff", "--name-only", "-z", BASE, head, "--"))))
        numstat = _git(root, "diff", "--numstat", "-z", BASE, head, "--")
        charged, valid = _charge(numstat)
        ambiguous = base != BASE or len(commits) > 100
    except (UnicodeDecodeError, ValueError, RuntimeError):
        return RepositoryFacts("", "", (), -1, False, "", (), "", True, (), (), True)
    return RepositoryFacts(branch, base, paths, charged, valid, first, first_paths, first_parent,
                           shallow, replaces, merges, ambiguous)


def _charge(raw: bytes) -> tuple[int, bool]:
    if raw and not raw.endswith(b"\0"):
        return -1, False
    total = 0
    for record in raw.split(b"\0")[:-1]:
        fields = record.split(b"\t", 2)
        if len(fields) != 3 or b"-" in fields[:2]:
            return -1, False
        try:
            total += int(fields[0]) + int(fields[1])
            fields[2].decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return -1, False
    return total, True


def check(root: Path, failures: list[str], active: bool) -> None:
    if not active:
        return
    failures.extend(repository_findings(collect_repository_facts(root)))
    try:
        failures.extend(proposal_findings((root / PROPOSAL_PATH).read_bytes()))
        failures.extend(binding_findings((root / BINDING_PATH).read_bytes()))
        failures.extend(required_review_findings(root))
        failures.extend(required_governance_findings(root))
        failures.extend(preflight_findings((root / PREFLIGHT_PATH).read_bytes()))
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        failures.append("Issue #427 preflight or required reset artifact is malformed or drifted.")
