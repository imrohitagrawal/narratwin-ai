import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_guardrails_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "guardrails_check.py"
    spec = importlib.util.spec_from_file_location("guardrails_check_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guardrails: Any = load_guardrails_module()
ROOT = Path(__file__).parents[2]
ISSUE_39_REFERENCE_ONLY_FAILURE = "Issue #39 pull requests must use reference-only wording and must not auto-close #39."
PREFLIGHT_FAILURE = "Non-trivial pull requests must include completed preflight evidence rows."
MISSING_REVIEWER_OVERVIEW = "Non-trivial pull requests must include a Reviewer overview section."
MISSING_RESOURCE_LIFECYCLE = (
    "Non-trivial pull requests must include a Resource lifecycle and cleanup section."
)
REVIEWER_OVERVIEW_ORDER = (
    "Reviewer overview must appear before detailed governance and evidence sections."
)
PR_SPECIFIC_PREFLIGHT_ARTIFACT = "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
REVIEWER_POINT_HEADINGS = (
    "1. What changed and why",
    "2. Scope",
    "3. Key files and components",
    "4. Reviewer focus",
    "5. Validation, limitations, and residual risks",
)
REVIEWER_POINT_CONTENT = (
    "Adds a local PR-body check so reviewers see the change before evidence tables.",
    "- In scope: PR template and guardrail behavior.\n- Out of scope: Product and runtime behavior.",
    "The PR template, repository guardrail, focused tests, and governance docs change.",
    "Check heading scope, placeholder rejection, and preservation of existing PR checks.",
    "Unit and forced-event checks cover the change; human judgment of clarity remains required.",
)
REVIEWER_MEANING_FAILURES = (
    "Reviewer overview point 1 must contain meaningful PR-specific content.",
    "Reviewer overview point 2 must contain meaningful PR-specific content, including both In scope and Out of scope.",
    "Reviewer overview point 3 must contain meaningful PR-specific content.",
    "Reviewer overview point 4 must contain meaningful PR-specific content.",
    "Reviewer overview point 5 must contain meaningful PR-specific content.",
)
PRODUCT_CONTEXT_HEADINGS = (
    "1. End product goal",
    "2. Current state",
    "3. Problem being addressed",
    "4. Exact changes in this PR",
    "5. What is complete after merge",
    "6. Expected outcome",
    "7. Not expected / out of scope",
    "8. End-goal impact",
    "9. Remaining gap",
    "10. Reviewer validation",
)
PRODUCT_CONTEXT_CONTENT = (
    "NarraTwin is progressing toward an end-to-end audience-aware multilingual demo and a separately approved production path.",
    "The repository blocks placeholder reviewer overviews, but it does not yet require self-contained product and end-goal context.",
    "Reviewers currently have to open nested issue and document links to reconstruct the product intent and expected outcome.",
    "#### Reviewer impact summary\n\n"
    "- **Purpose:** It gives reviewers a complete, concise explanation of why each non-trivial pull request matters.\n"
    "- **Behavior before/after:** Reviewers previously reconstructed behavior from technical evidence; afterward they receive an explicit observable comparison.\n"
    "- **Who and what is affected:** Authors and reviewers gain guidance and validation; runtime users, systems, and product data are unchanged.\n"
    "- **Artifacts/capabilities:** It adds reviewer guidance and validation while adding no product content, media artifact, or runtime capability.\n"
    "- **Operational impact:** No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.\n"
    "- **Scope boundaries:** This governance change adds no voices, narration, audio, captions, avatars, deployment, release, or production-readiness capability.\n"
    "- **End-to-end impact:** It removes a reviewer-context blocker while product delivery, release gates, and final acceptance remain separate.\n\n"
    "#### Technical change list\n\n"
    "This PR adds a product-context template, a local PR-body parser, negative tests, and matching governance documentation.",
    "After merge, policy-gates rejects non-trivial PRs that omit any required self-contained product-context field.",
    "Reviewers can understand the change, product impact, expected result, and validation target directly from the PR body.",
    "This PR does not change runtime behavior and does not authorize deployment, public release, or production readiness.",
    "This governance change removes review ambiguity; it does not directly add another step to the user-facing demo flow.",
    "The end-to-end demo and all independent production-readiness evidence remain separate product and release work.",
    "Expected behavior: incomplete product context blocks policy-gates.\n"
    "Prohibited behavior: issue-only or link-only text must not pass.\n"
    "Evidence: focused parser mutations and a forced pull-request event.\n"
    "Pass condition: every required field is specific and the complete body passes.\n"
    "Fail condition: any required field is missing, generic, or unsupported.",
)


ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"


def issue471_intended_cleanup_documents() -> dict[str, bytes]:
    current = {
        path: (ROOT / path).read_bytes() for path in guardrails.CLEANUP_AUTHORITY_SHA256
    }
    if guardrails.cleanup_authority_anchor_failures(current.__getitem__) == []:
        return current
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").replace(
        "   closeout instead of treating the merge as fully complete.\n",
        "   closeout instead of treating the merge as fully complete.\n"
        "   Merge cleanup must resolve scoped resource ownership before deletion;\n"
        "   prohibit broad prune operations; preserve dirty work with before-and-after\n"
        "   hashes and status counts; verify main...origin/main is 0 ahead / 0 behind;\n"
        "   and publish a retained, deleted, and recoverability report with proof of\n"
        "   absence for removed resources.\n",
    )
    playbook = (ROOT / "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md").read_text(encoding="utf-8")
    playbook = playbook.replace(
        "When a PR becomes approved and merge-eligible, do not wait for the owner to\n",
        "### Mandatory Merge-Closeout Checklist\n\nWhen a PR becomes approved and merge-eligible, do not wait for the owner to\n",
    ).replace(
        "- delete merged feature branches when no longer needed\n",
        "- delete merged feature branches when no longer needed\n"
        "- inventory every cleanup target and resolve its ownership to the completed PR\n"
        "  before deletion; retain anything whose ownership is unclear\n"
        "- remove completed implementation and verification worktrees\n"
        "- remove PR-owned Docker containers, images, volumes, and networks\n"
        "- remove PR-owned temporary clones, files, and isolated dependencies\n"
        "- do not run broad prune operations, including Docker system, image, builder,\n"
        "  volume, network, cache, worktree, branch, or recursive filesystem pruning; broad prune operations are prohibited\n"
        "  even when every cleanup target has asserted ownership\n"
        "- when local `main` owns dirty work, hash staged, unstaged, and untracked state\n"
        "  before and after preservation; also record the status-entry count, preserve\n"
        "  the exact index and files on a clearly named local branch, and reverify both\n"
        "  hashes and count before recreating clean local `main`\n"
        "- after synchronization, verify `main...origin/main` is `0` ahead and `0`\n"
        "  behind\n"
        "- prove scoped resources are absent after deletion without treating unrelated\n"
        "  retained resources as cleanup failures\n"
        "- publish a retained, deleted, and recoverability report that identifies each\n"
        "  scoped resource, its ownership basis, disposition, reason, and whether the\n"
        "  deletion is recoverable\n",
    )
    return {"AGENTS.md": agents.encode(), "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": playbook.encode()}


def test_issue471_cleanup_authority_anchor_is_independent_of_route_hashlib(monkeypatch: Any) -> None:
    documents = issue471_intended_cleanup_documents()
    assert guardrails.cleanup_authority_anchor_failures(documents.__getitem__) == []
    documents["AGENTS.md"] += b"\nThe preceding prohibition is waived.\n"
    monkeypatch.setattr(hashlib, "sha256", lambda data: type("Digest", (), {"hexdigest": lambda self: "0" * 64})())
    assert guardrails.cleanup_authority_anchor_failures(documents.__getitem__) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes."
    ]


def test_issue471_cleanup_authority_and_anchor_cannot_change_together() -> None:
    documents = issue471_intended_cleanup_documents()
    assert guardrails.cleanup_authority_change_failures(
        ["AGENTS.md", "scripts/guardrails_check.py"], documents.__getitem__
    ) == ["Merge-cleanup authority and its anchor require separate reviewed pull requests."]
    assert guardrails.cleanup_authority_change_failures(["docs/STATUS.md"], documents.__getitem__) == []


def test_issue391_cleanup_authority_accepts_final_and_pending_hashes(
    monkeypatch: Any,
) -> None:
    final = {
        "AGENTS.md": "57ea2bdddd7f0f3df91c75ecb0e434e25aa0779a54d0a2603a7e32a87b5c9ca7",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": (
            "e70d7c3045a4fec6b8c4feeb276244ea963a778f872955670cc2e209c0b03e2d"
        ),
    }
    assert guardrails.CLEANUP_AUTHORITY_SHA256 == final
    pending = {
        "AGENTS.md": "256d0c761f2f3218b38533e27ed72b2594282e56f9fbd95545002110f08804cc",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": (
            "131ff62af3c12b1d31bf3ed73cfc45d61f1fed13a7f405254346faa0b4e8493e"
        ),
    }
    assert guardrails.CLEANUP_AUTHORITY_PENDING_SHA256 == pending

    class Digest:
        def __init__(self, value: str) -> None:
            self.value = value

        def hexdigest(self) -> str:
            return self.value

    payloads = {path: f"final:{path}".encode() for path in final}
    final_by_payload = {payloads[path]: digest for path, digest in final.items()}
    monkeypatch.setattr(
        guardrails,
        "_cleanup_authority_sha256",
        lambda payload: Digest(final_by_payload.get(payload, "0" * 64)),
    )
    assert guardrails.cleanup_authority_anchor_failures(payloads.__getitem__) == []

    pending_by_payload = {payloads[path]: digest for path, digest in pending.items()}
    monkeypatch.setattr(
        guardrails,
        "_cleanup_authority_sha256",
        lambda payload: Digest(pending_by_payload.get(payload, "0" * 64)),
    )
    assert guardrails.cleanup_authority_anchor_failures(payloads.__getitem__) == []

    old = {
        "AGENTS.md": "7222909116385fe74cbc7df6bbccb759687d2e4a6bf0e0637465679434de33ab",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": (
            "30ba0f8e7b736293c4b6c110cbe9ce46bf7639507b0441bd37cb222bb62ae94f"
        ),
    }
    old_by_payload = {payloads[path]: digest for path, digest in old.items()}
    monkeypatch.setattr(
        guardrails,
        "_cleanup_authority_sha256",
        lambda payload: Digest(old_by_payload.get(payload, "0" * 64)),
    )
    assert guardrails.cleanup_authority_anchor_failures(payloads.__getitem__) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes.",
        "Merge-cleanup authority anchor rejected docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md bytes.",
    ]

    swapped_by_payload = {
        payloads["AGENTS.md"]: final["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        payloads["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"]: final["AGENTS.md"],
    }
    monkeypatch.setattr(
        guardrails,
        "_cleanup_authority_sha256",
        lambda payload: Digest(swapped_by_payload.get(payload, "0" * 64)),
    )
    assert guardrails.cleanup_authority_anchor_failures(payloads.__getitem__) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes.",
        "Merge-cleanup authority anchor rejected docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md bytes.",
    ]

    monkeypatch.setattr(
        guardrails,
        "_cleanup_authority_sha256",
        lambda payload: Digest("0" * 64),
    )
    assert guardrails.cleanup_authority_anchor_failures(payloads.__getitem__) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes.",
        "Merge-cleanup authority anchor rejected docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md bytes.",
    ]

    assert guardrails.cleanup_authority_anchor_failures(lambda _: None) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes.",
        "Merge-cleanup authority anchor rejected docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md bytes.",
    ]

    def unreadable(path: str) -> bytes:
        raise OSError(f"blocked {path}")

    assert guardrails.cleanup_authority_anchor_failures(unreadable) == [
        "Merge-cleanup authority anchor could not read AGENTS.md: blocked AGENTS.md.",
        (
            "Merge-cleanup authority anchor could not read "
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md: blocked "
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md."
        ),
    ]


def test_issue471_fixture_preserves_already_anchored_authority(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    intended = issue471_intended_cleanup_documents()
    for path, payload in intended.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    monkeypatch.setitem(issue471_intended_cleanup_documents.__globals__, "ROOT", tmp_path)
    assert issue471_intended_cleanup_documents() == intended


def _issue435_adapter_fixture(monkeypatch: Any, branch: str, returncode: int, stdout: bytes, event: str = "") -> list[object]:
    calls: list[object] = []
    monkeypatch.setattr(guardrails, "run_git", lambda args: branch)

    def run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.extend((args, kwargs))
        return subprocess.CompletedProcess([], returncode, stdout, b"")

    monkeypatch.setattr(guardrails.subprocess, "run", run)
    monkeypatch.setenv("GITHUB_HEAD_REF", event) if event else monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    return calls


def test_issue435_exact_route_uses_thin_isolated_adapter(monkeypatch: Any) -> None:
    calls = _issue435_adapter_fixture(monkeypatch, ISSUE435_BRANCH, 0, b'{"code":null}\n')
    monkeypatch.setenv("GITHUB_BASE_SHA", "b" * 40)
    monkeypatch.setenv("GITHUB_HEAD_SHA", "a" * 40)

    assert guardrails.issue435_route_findings() == []
    raw_args, raw_kwargs = calls
    assert isinstance(raw_args, tuple) and isinstance(raw_kwargs, dict)
    command = raw_args[0]
    assert isinstance(command, list)
    assert Path(command[-2]).name == "adversarial_convergence.py"
    assert command[-1] == "--route-only"
    assert command[1:3] == ["-I", "-P"]
    assert raw_kwargs["timeout"] == 10
    environment = raw_kwargs["env"]
    assert isinstance(environment, dict) and environment["GITHUB_BASE_SHA"] == "b" * 40
    assert environment["GITHUB_HEAD_SHA"] == "a" * 40 and "PYTHONPATH" not in environment


def test_issue435_unrelated_and_lookalike_branches_do_not_gain_authority(monkeypatch: Any) -> None:
    _issue435_adapter_fixture(monkeypatch, "stage8-unrelated", 0, b'{"code":null}')
    assert guardrails.issue435_route_findings() == []
    _issue435_adapter_fixture(monkeypatch, ISSUE435_BRANCH + "-evil", 0, b'{"code":null}')
    assert guardrails.issue435_route_findings() == ["ACP.AUTH.ROUTE_DRIFT"]


def test_issue435_exact_event_branch_accepts_detached_and_rejects_conflict(monkeypatch: Any) -> None:
    _issue435_adapter_fixture(monkeypatch, "", 0, b'{"code":null}', ISSUE435_BRANCH)
    assert guardrails.issue435_route_findings() == []
    _issue435_adapter_fixture(monkeypatch, "conflicting-branch", 0, b'{"code":null}', ISSUE435_BRANCH)
    assert guardrails.issue435_route_findings() == ["ACP.AUTH.ROUTE_DRIFT"]


def test_issue435_push_ref_is_bound_as_detached_event_branch(monkeypatch: Any) -> None:
    calls = _issue435_adapter_fixture(monkeypatch, "", 0, b'{"code":null}')
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", ISSUE435_BRANCH)

    assert guardrails.issue435_route_findings() == []
    _, raw_kwargs = calls
    assert isinstance(raw_kwargs, dict)
    environment = raw_kwargs["env"]
    assert isinstance(environment, dict)
    assert environment["GITHUB_HEAD_REF"] == ISSUE435_BRANCH
    assert environment["GITHUB_EVENT_NAME"] == "push"

    for hostile in (f" {ISSUE435_BRANCH}", f"{ISSUE435_BRANCH} ", ISSUE435_BRANCH + "-evil"):
        monkeypatch.setenv("GITHUB_REF_NAME", hostile)
        assert guardrails.issue435_route_findings() == ["ACP.AUTH.ROUTE_DRIFT"]


@pytest.mark.parametrize(
    ("returncode", "stdout", "finding"),
    (
        (1, b'{"code":"ACP.AUTH.BUDGET_STOP"}', "ACP.AUTH.BUDGET_STOP"),
        (0, b'{"code":"ACP.AUTH.ROUTE_DRIFT"}', "ACP.VERDICT.PLATFORM_FAILURE"),
        (2, b'{"code":"ACP.VERDICT.PLATFORM_FAILURE"}', "ACP.VERDICT.PLATFORM_FAILURE"),
        (0, b"not-json", "ACP.VERDICT.PLATFORM_FAILURE"),
    ),
)
def test_issue435_adapter_maps_only_typed_contract_results(
    monkeypatch: Any, returncode: int, stdout: bytes, finding: str
) -> None:
    _issue435_adapter_fixture(monkeypatch, ISSUE435_BRANCH, returncode, stdout)
    assert guardrails.issue435_route_findings() == [finding]


def test_issue435_adapter_contains_timeout(monkeypatch: Any) -> None:
    for name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME", "GITHUB_EVENT_NAME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(guardrails, "run_git", lambda args: ISSUE435_BRANCH)
    monkeypatch.setattr(
        guardrails.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired([], 10)),
    )
    assert guardrails.issue435_route_findings() == ["ACP.VERDICT.PLATFORM_FAILURE"]


def reviewer_overview_body(
    contents: tuple[str, ...] = REVIEWER_POINT_CONTENT,
    *,
    omit: int | None = None,
) -> str:
    rows = ["## Reviewer overview"]
    for index, (heading, content) in enumerate(zip(REVIEWER_POINT_HEADINGS, contents, strict=True)):
        if index != omit:
            rows.extend(("", f"### {heading}", "", content))
    return "\n".join(rows) + "\n"


def product_context_body(
    contents: tuple[str, ...] = PRODUCT_CONTEXT_CONTENT,
    *,
    omit: int | None = None,
) -> str:
    rows = ["## Product and reviewer context"]
    for index, (heading, content) in enumerate(zip(PRODUCT_CONTEXT_HEADINGS, contents, strict=True)):
        if index != omit:
            rows.extend(("", f"### {heading}", "", content))
    return "\n".join(rows) + "\n"


def resource_lifecycle_body(*, row: str | None = None) -> str:
    lifecycle_row = row or (
        "| issue-391 worktree | dedicated issue worktree created by this PR | success-clean | "
        '{"disposition":"delete","kind":"git-worktree","locator":"/tmp/issue-391",'
        '"trigger":"merged-main-green"} | '
        "PR and issue closeout comments with absence and reclaimed-space proof |"
    )
    return (
        "## Resource lifecycle and cleanup\n\n"
        "| Resource | Ownership proof | Retention class | Cleanup contract | "
        "Verification evidence |\n"
        "|---|---|---|---|---|\n"
        f"{lifecycle_row}\n"
    )


def exact_changes_with_summary(technical_changes: str) -> str:
    summary = PRODUCT_CONTEXT_CONTENT[3].split("#### Technical change list", maxsplit=1)[0]
    return f"{summary}#### Technical change list\n\n{technical_changes}"
ISSUE39_SENSITIVE_ROW_CELLS = {
    "DUR-ACID-001": [
        "ACID/CAS durable metadata",
        "Production transaction model for durable identifiers, versioning, and compare-and-set invariants",
        "Architecture + storage",
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist",
    ],
    "DUR-IDEMP-001": [
        "Production idempotency semantics",
        "Replay-safe request identity and dedupe behavior across retries and worker failover",
        "Runtime/state + Security",
        "Idempotency envelope contract including terminal/error/replay state transitions and failure dedupe proofs",
    ],
    "DUR-STAGE4-001": [
        "Durable Stage 4 project/document/RAG/run graph",
        "Durable project/document/chunk/run/eval graph and resume behavior",
        "Storage + API",
        "Entity/state graph contract with at-least-once execution and idempotent consumers; no exactly-once side-effect claim",
    ],
    "DUR-LEASE-001": [
        "Cross-worker job leases",
        "Lease acquisition, heartbeat renewal, expiry, reclaim, and stale-writer fencing",
        "Runtime/state",
        "Lease state machine with monotonic fencing token/epoch, stale-owner prevention, and ownership transfer proof",
    ],
    "DUR-OUTBOX-001": [
        "Committed outbox side effects",
        "Outbox transaction boundaries and side-effect dispatch contract",
        "Runtime/integrations",
        "Same-transaction outbox write with state change; at-least-once dispatch plus idempotent consumer policy",
    ],
    "DUR-STAGE6-001": [
        "Durable multilingual artifact replay",
        "Production replay of translated scripts/subtitles and derived assets",
        "Stage 6",
        "Replay contract with source-run linkage, checksum-based dedupe, and deterministic artifact provenance",
    ],
    "DUR-STAGE7-001": [
        "Durable render/artifact/provenance state",
        "Render status, artifact records, consent/disclosure binding",
        "Stage 7",
        "Persistent render/provenance record contract and synthetic-media release check points",
    ],
    "DUR-MIG-001": [
        "Migrations",
        "Versioned schema evolution, compatibility, and forward-only rollback safety",
        "Platform/storage",
        "Expand/contract migration plan with backward-compatible code windows, forward repair, and no mandatory down-migration claim",
    ],
    "DUR-ROLLBACK-001": [
        "Technical rollback compatibility",
        "Code rollback against migrated production metadata",
        "Platform + Release",
        "Evidence that the previous deploy can run against the expanded schema or that rollback is blocked until forward repair completes",
    ],
    "DUR-RESTORE-001": [
        "Backup/restore drill",
        "Backup scope, integrity, restore smoke, and RTO/RPO verification",
        "Ops",
        "Operable restore playbook with evidence of at least one successful restore drill",
    ],
    "OPS-METRICS-001": [
        "Production metrics",
        "Queue, lease, idempotency, outbox, and restore metrics",
        "Observability",
        "Reviewer-approved metric catalog and scrape/query mapping to each operational failure mode",
    ],
    "OPS-SLO-001": [
        "Production SLOs and error budgets",
        "Threshold bindings for queue lag, lease staleness, outbox age/backlog, restore RTO/RPO, rollback, and watch escalation",
        "SRE/Ops + Release",
        "Reviewed SLO/error-budget catalog with alert threshold mapping and rollback/watch escalation bindings",
    ],
    "OPS-ALERT-001": [
        "Dashboards and alerts",
        "Severity routing, alert ownership, and paging runbook",
        "SRE/Ops",
        "Dashboard + alert matrix with tested routing, evidence loop, and acknowledgment rules",
    ],
    "OPS-WATCH-001": [
        "First-hour watch with follow-up checkpoints",
        "Triage cadence and owner communication for the first 60 minutes, plus explicit 120/180-minute follow-up checkpoints",
        "Release/Operations",
        "Active watch log template, handoff rules, timeout actions, rollback escalation threshold",
    ],
    "OPS-ROLLBACK-001": [
        "Rollback communications",
        "Pre/post rollback comms and ownership confirmation",
        "Release/Operations",
        "Freeze-window criteria, comms template, and required evidence captures",
    ],
    "MEDIA-CONSENT-001": [
        "Consent capture",
        "Affirmative consent record for synthetic-media generation",
        "Security/Privacy",
        "Consent schema with actor, timestamp, consent text/version, artifact refs, source-run binding, scope, and audit retention",
    ],
    "MEDIA-REVOKE-001": [
        "Consent revocation behavior",
        "Revocation, takedown, retention, and already-published artifact handling",
        "Security/Privacy + Release",
        "Revocation decision table covering retain, block replay, takedown, and customer/user communication paths",
    ],
    "MEDIA-PROVENANCE-001": [
        "Provenance binding",
        "Durable source-run, prompt, provider, artifact checksum, cloned-identity denial provenance, and disclosure lineage",
        "Security/Privacy + Media",
        "Provenance schema and replay proof linking rendered artifacts to source run, consent record, and identity/likeness denial checks",
    ],
    "MEDIA-DISCLOSURE-001": [
        "Synthetic-media disclosure",
        "Durable disclosure text/version binding for exports and public-use posture",
        "Security/Privacy + Release",
        "Disclosure versioning record and validation that artifacts carry the expected disclosure state",
    ],
    "PROVIDER-POSTURE-001": [
        "Provider release posture",
        "External provider legal, license, network, egress, key, and rollout controls",
        "Security/Privacy + Platform",
        "Provider release checklist with legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and rollback disablement evidence",
    ],
    "SEC-RETENTION-001": [
        "Sensitive metadata retention/deletion/redaction",
        "PII/provenance/consent data in PostgreSQL, backups, logs, metrics, and restored environments",
        "Security/Privacy + Ops",
        "Data-class table with encryption, redaction, deletion/erasure scope, tombstone vs hard-delete policy, backup expiry, restore re-delete behavior, audit retention exceptions, access control, replay/export blocking after deletion, and restore-disclosure requirements",
    ],
    "SEC-UNTRUSTED-001": [
        "Untrusted durable/replayed input handling",
        "Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted",
        "Security/Privacy + Runtime + Ops",
        "Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content",
    ],
    "GOV-SCOPE-001": [
        "Scope split",
        "Context 0 does not absorb child PRs or remaining production blockers",
        "Governance",
        "Documented issue split with separate issue/PR mapping for every remaining blocker",
    ],
}


def write_issue39_closure_plan(
    root: Path,
    *,
    child_issue: str = "https://github.com/imrohitagrawal/narratwin-ai/issues/70",
    child_pr: str = "https://github.com/imrohitagrawal/narratwin-ai/pull/71",
    malformed_id: str | None = None,
    omitted_ids: set[str] | None = None,
    include_records: bool = True,
    generic_records: bool = False,
    generic_evidence_only: bool = False,
    padded_generic_evidence_only: bool = False,
    doc_only_evidence: bool = False,
    context0_pr64_evidence: bool = False,
    context0_pr64_text: str | None = None,
    weak_human_only_evidence: bool = False,
    valid_human_only_evidence: bool = False,
    artifact_id_only: bool = False,
    artifact_label_id_only: bool = False,
    weakened_id: str | None = None,
) -> None:
    omitted = omitted_ids or set()
    plan_path = root / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_rows = []
    record_rows = []
    for matrix_id in sorted(guardrails.REQUIRED_ISSUE_39_CLOSURE_MATRIX_IDS - omitted):
        matrix_cells = ISSUE39_SENSITIVE_ROW_CELLS.get(
            matrix_id,
            ["Requirement", "Evidence target", "Owner", "Minimum evidence contract"],
        )
        if matrix_id == weakened_id:
            matrix_cells = ["Requirement", "Evidence target", "Owner", "Minimum evidence contract"]
        if matrix_id == malformed_id:
            matrix_rows.append(
                f"| `{matrix_id}` | {' | '.join(matrix_cells)} | Closed | Open |"
            )
        else:
            matrix_rows.append(
                f"| `{matrix_id}` | {' | '.join(matrix_cells)} | Closed |"
            )
        evidence_path = root / f"docs/reviews/{matrix_id}-evidence.md"
        evidence_path.write_text(f"{matrix_id} closure evidence\n", encoding="utf-8")
        if artifact_label_id_only:
            shared_evidence_path = root / "docs/reviews/shared-evidence.md"
            shared_evidence_path.write_text("shared closure evidence\n", encoding="utf-8")
            artifact = f"[{matrix_id} evidence](docs/reviews/shared-evidence.md)"
        else:
            artifact = f"`docs/reviews/{matrix_id}-evidence.md`"
        if context0_pr64_text is not None:
            evidence = (
                f"{matrix_id} {closure_evidence_detail(matrix_id)} "
                f"with final proof copied from {context0_pr64_text}"
            )
        elif context0_pr64_evidence:
            evidence = (
                f"{matrix_id} Context 0 planning proof from PR #64 and "
                "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
            )
        elif doc_only_evidence:
            evidence = (
                f"{matrix_id} documented in docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md "
                "with reviewer notes and process signoff"
            )
        elif weak_human_only_evidence:
            evidence = f"{matrix_id} human only"
        elif valid_human_only_evidence:
            evidence = (
                f"{matrix_id} human-only evidence records owner approval "
                "with residual risk decision for this production-grade row"
            )
        elif artifact_id_only:
            evidence = "Concrete replay drill log shows invariant held under retry, failover, and reviewer audit conditions"
        elif padded_generic_evidence_only:
            evidence = f"{matrix_id} human-only evidence passed with reviewer evidence"
        elif generic_records or generic_evidence_only:
            evidence = f"{matrix_id} human-only evidence passed"
        else:
            evidence = (
                f"{matrix_id} {closure_evidence_detail(matrix_id)}"
            )
        if context0_pr64_evidence:
            reason = f"{matrix_id} Context 0 PR #64 planning artifact is cited as final row evidence"
        elif doc_only_evidence:
            reason = f"{matrix_id} documentation-only closure proof is cited with reviewer notes"
        elif generic_records:
            reason = f"{matrix_id} evidence satisfies the closure row"
        elif artifact_id_only:
            reason = "Closure artifact proves the named invariant with a concrete command, review owner, and residual-risk decision"
        else:
            reason = (
                f"{matrix_id} {closure_reason_detail(matrix_id)}"
            )
        record_rows.append(
            f"| `{matrix_id}` | {child_issue} / {child_pr} | {artifact} | {evidence} | production durability accountable engineer | security reliability review approver | {matrix_id} reviewed residual risk is bounded by linked follow-up evidence | merge commit abc1234 | {reason} |"
        )
    records = "\n".join(record_rows) if include_records else ""
    plan_path.write_text(
        "\n".join(
            [
                "# Issue #39 Production Closure Plan (Context 0)",
                "",
                "## Master Evidence Matrix",
                "",
                "| ID | Requirement | Evidence target | Owner | Minimum evidence contract | Status |",
                "|---|---|---|---|---|---|",
                *matrix_rows,
                "",
                "## Row Closure Records",
                "",
                "| Matrix ID | Child issue / PR | Artifact reference | Validation or human evidence | Owner | Reviewer | Residual-risk decision | Timestamp / merge commit | Satisfies row because |",
                "|---|---|---|---|---|---|---|---|---|",
                records,
                "",
            ]
        ),
        encoding="utf-8",
    )


def closure_evidence_detail(matrix_id: str) -> str:
    test_node = f"tests/unit/test_issue39_production_closure.py::test_{matrix_id.lower().replace('-', '_')}_closure"
    if matrix_id.startswith("DUR-"):
        return f"{test_node} durability replay evidence records the transaction, lease, outbox, restore, or migration invariant for that exact row"
    if matrix_id.startswith("OPS-SLO"):
        return f"{test_node} SLO and error-budget evidence binds queue lag, lease staleness, outbox age, restore targets, rollback, and watch thresholds"
    if matrix_id.startswith("OPS-"):
        return f"{test_node} operations evidence records metric, alert, watch, or rollback behavior with owner-reviewed production thresholds"
    if matrix_id.startswith("MEDIA-"):
        return f"{test_node} synthetic-media evidence records consent, revocation, provenance, or disclosure state with reviewer-approved privacy controls"
    if matrix_id.startswith("PROVIDER-"):
        return f"{test_node} provider-posture evidence records local mock defaults, production enablement, egress denial, key isolation, and rollback disablement"
    if matrix_id.startswith("SEC-RETENTION"):
        return f"{test_node} privacy evidence records deletion scope, tombstone policy, backup expiry, restore re-delete, audit exceptions, and replay blocking"
    if matrix_id.startswith("SEC-UNTRUSTED"):
        return f"{test_node} security evidence records validation, output encoding, log redaction, injection controls, poisoned-retrieval checks, and restore revalidation"
    return "governance evidence records scope split review and non-absorb signoff"


def closure_reason_detail(matrix_id: str) -> str:
    if matrix_id.startswith("DUR-"):
        return "the closure proof exercises the named durability invariant and links it to a concrete child issue and PR"
    if matrix_id.startswith("OPS-"):
        return "the closure proof maps the named operational invariant to tested thresholds, ownership, and escalation evidence"
    if matrix_id.startswith("MEDIA-") or matrix_id.startswith("SEC-") or matrix_id.startswith("PROVIDER-"):
        return "the closure proof preserves the named security/privacy invariant with concrete policy, validation, and reviewer evidence"
    return "the closure proof preserves the named governance boundary with reviewer signoff and a concrete scope decision"


def allow_github_reference_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    verified_refs = {("issues", "70"), ("pulls", "71")}
    calls: list[tuple[str, str]] = []

    def fake_github_reference_exists(resource: str, number: str) -> bool:
        calls.append((resource, number))
        return (resource, number) in verified_refs

    monkeypatch.setattr(guardrails, "github_reference_exists", fake_github_reference_exists)
    monkeypatch.setattr(guardrails, "github_pull_request_is_merged", lambda number: number == "71")
    monkeypatch.setattr(guardrails, "_test_github_reference_calls", calls, raising=False)


def allow_github_reference_verification_for_context0_pr64(monkeypatch: pytest.MonkeyPatch) -> None:
    verified_refs = {("issues", "70"), ("pulls", "64")}

    def fake_github_reference_exists(resource: str, number: str) -> bool:
        return (resource, number) in verified_refs

    monkeypatch.setattr(guardrails, "github_reference_exists", fake_github_reference_exists)
    monkeypatch.setattr(guardrails, "github_pull_request_is_merged", lambda number: number == "64")


def run_issue_link_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    title: str,
    body: str,
    head_ref: str = "phase-1-closure-39-durability-monitoring",
    base_ref: str = "main",
    base_sha: str = "0123456789abcdef0123456789abcdef01234567",
    commit_messages: str = "",
    changed_files: list[str] | None = None,
    event_name: str = "pull_request",
    force_pull_request_guards: bool = False,
) -> list[str]:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "pull_request": {
                    "title": title,
                    "body": body,
                    "head": {"ref": head_ref},
                    "base": {"ref": base_ref, "sha": base_sha},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    if force_pull_request_guards:
        monkeypatch.setenv(guardrails.FORCE_PULL_REQUEST_GUARDRAILS_ENV, "1")

    def fake_run_git(args: list[str]) -> str:
        if args and args[0] == "log":
            return commit_messages
        if args and args[0] == "diff":
            return "\n".join(changed_files or [])
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)
    guardrails.failures.clear()
    guardrails.check_issue_linked_pull_request()
    return list(guardrails.failures)


def completed_preflight_body(
    preflight_rows: str | None = None,
    *,
    human_rows: str | None = None,
    normalize_rows: bool = True,
) -> str:
    rows = preflight_rows or (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        f"| Failure matrix / invariant matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests / old-behavior proof | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 INV-2 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 INV-2 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    if normalize_rows:
        rows = normalize_preflight_rows_for_current_contract(rows)
    human_surface_rows = (
        human_rows
        if human_rows is not None
        else (
        "| Final squash message | CI cannot inspect the final merge dialog text before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | reference-only final message with no issue-closing keyword accepted for PR only | before merge |\n"
        )
    )
    return (
        "Refs #44\n\n"
        f"{product_context_body()}\n"
        f"{reviewer_overview_body()}\n"
        f"{resource_lifecycle_body()}\n"
        "## Status impact\n\n"
        "No repository-tracked status change is claimed by this PR. Routine post-merge facts go to "
        "PR/issue comments, with no successor status-only PR.\n\n"
        "## Preflight evidence\n\n"
        "| Evidence | Artifact reference | Reference type | Matrix IDs | Command / CI / Source | Reviewer | Evidence type | Completion status | Residual risk decision |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        f"{rows}\n"
        "## Human-only review surfaces\n\n"
        "| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |\n"
        "|---|---|---|---|---|---|\n"
        f"{human_surface_rows}\n"
        "## Pre-implementation evidence\n\n"
        "| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |\n"
        "|---|---|---|---|---|\n"
        f"| Invariant/failure matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1 | reviewer | pass |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | draft pr: https://github.com/imrohitagrawal/narratwin-ai/pull/60 | reviewer | pass |\n"
        "| Human-only surfaces, if any | `docs/ENGINEERING_PROCESS_RCA.md` | issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-2 | reviewer | pass |\n"
        "\n## Validation evidence\n\n"
        "```text\n"
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed\n"
        "uv run pytest tests/unit/test_phase1_closure_docs.py -> 14 passed\n"
        "python3 scripts/guardrails_check.py -> passed\n"
        "make quality -> passed\n"
        "uv run ruff check scripts tests -> passed\n"
        "uv run mypy scripts tests -> passed\n"
        "make ci -> passed\n"
        "make security -> passed\n"
        "make dependency-audit -> passed\n"
        "make container-scan -> passed\n"
        "make secrets-scan -> passed\n"
        "make eval -> passed\n"
        "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed\n"
        "```\n"
    )


def normalize_preflight_rows_for_current_contract(rows: str) -> str:
    rows = rows.replace(
        "| Failure matrix / invariant matrix | `docs/ENGINEERING_PROCESS_RCA.md`",
        f"| Failure matrix / invariant matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}`",
    ).replace(
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md`",
        f"| Failure matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}`",
    )
    missing_rows = []
    normalized_rows = rows.lower()
    if "| review prompt" not in normalized_rows:
        missing_rows.append(
            f"| Review prompt set | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | PROMPT-1 | adversarial prompt generated from invariant matrix | reviewer | source | pass | tracked |\n"
        )
    if "| stop rule" not in normalized_rows:
        missing_rows.append(
            f"| Stop rule / repeated blocker reset | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | STOP-1 | repeated-blocker stop rule reset requires contract update before next fix loop | reviewer | gate | pass | tracked |\n"
        )
    if "| skill/tool selection" not in normalized_rows:
        missing_rows.append(
            f"| Skill/tool selection | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | SKILL-1 | preinstalled skills and repo docs checked first with no custom skill creation | reviewer | gate | pass | tracked |\n"
        )
    return rows + "".join(missing_rows)


def insert_duplicate_matrix_row(plan_path: Path, matrix_id: str) -> None:
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    duplicate_line = next((line for line in lines if line.startswith(f"| `{matrix_id}` ")), None)
    assert duplicate_line is not None
    insert_index = next(i for i, line in enumerate(lines) if line.strip().startswith("## Row Closure Records"))
    lines.insert(insert_index, duplicate_line)
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def insert_matrix_row_before_closure_records(plan_path: Path, row: str) -> None:
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    insert_index = next(i for i, line in enumerate(lines) if line.strip().startswith("## Row Closure Records"))
    lines.insert(insert_index, row)
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replace_matrix_row_cell(plan_path: Path, matrix_id: str, index: int, replacement: str) -> None:
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    row_index = next(
        i for i, line in enumerate(lines) if line.startswith(f"| `{matrix_id}` ")
    )
    cells = [cell.strip() for cell in lines[row_index].strip("|").split("|")]
    assert len(cells) >= 6
    assert 0 <= index < len(cells)
    cells[index] = replacement
    lines[row_index] = "| " + " | ".join(cells) + " |"
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_reviewer_overview_accepts_meaningful_short_and_multiline_content() -> None:
    assert guardrails.reviewer_overview_failures(reviewer_overview_body()) == []
    multiline = (
        "Changed the guardrail.\n\n- Prevents evidence-first review\n- Keeps prose flexible",
        "In scope:\n- Markdown parsing\n- Stable findings\n\nOut of scope:\n- Runtime code",
        "- `.github/pull_request_template.md`\n- `scripts/guardrails_check.py`",
        "- Ordering boundaries\n- False passes from unrelated tables",
        "Tests pass locally.\n\nLimitations:\n- Human clarity remains a reviewer decision.",
    )
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(multiline)) == []


def test_reviewer_overview_rejects_missing_section_despite_evidence_table_words() -> None:
    body = (
        "## Preflight evidence\n\n"
        "| 1. What changed and why | 2. Scope | 3. Key files and components | "
        "4. Reviewer focus | 5. Validation, limitations, and residual risks |\n"
        "|---|---|---|---|---|\n| meaningful | meaningful | meaningful | meaningful | meaningful |\n"
    )
    assert guardrails.reviewer_overview_failures(body) == [MISSING_REVIEWER_OVERVIEW]

    table_inside_overview = body.replace("## Preflight evidence", "## Reviewer overview")
    assert guardrails.reviewer_overview_failures(table_inside_overview) == [
        f"Reviewer overview must include point {heading.replace('.', ':', 1)}."
        for heading in REVIEWER_POINT_HEADINGS
    ]


@pytest.mark.parametrize(("missing_index", "label"), tuple(enumerate(REVIEWER_POINT_HEADINGS)))
def test_reviewer_overview_rejects_each_missing_point_independently(
    missing_index: int,
    label: str,
) -> None:
    assert guardrails.reviewer_overview_failures(
        reviewer_overview_body(omit=missing_index)
    ) == [f"Reviewer overview must include point {label.replace('.', ':', 1)}."]


@pytest.mark.parametrize(
    "evidence_heading",
    (
        "Guardrail checklist",
        "Preflight evidence",
        "Human-only review surfaces",
        "Pre-implementation evidence",
        "Validation evidence",
    ),
)
def test_reviewer_overview_rejects_overview_after_detailed_evidence(
    evidence_heading: str,
) -> None:
    body = f"## {evidence_heading}\n\n| Evidence | Result |\n|---|---|\n| check | passed |\n\n"
    assert guardrails.reviewer_overview_failures(body + reviewer_overview_body()) == [
        REVIEWER_OVERVIEW_ORDER
    ]
    if evidence_heading == "Preflight evidence":
        placeholders = ("TODO", "In scope: TODO\nOut of scope: TBD", "TBD", "pending", "N/A")
        assert guardrails.reviewer_overview_failures(
            body + reviewer_overview_body(placeholders)
        ) == [REVIEWER_OVERVIEW_ORDER, *REVIEWER_MEANING_FAILURES]


@pytest.mark.parametrize("point_index", range(5))
@pytest.mark.parametrize(
    "placeholder",
    ("TODO", "tBd", "PENDING", "add text here", "describe the change", "N/A", "NA", "not applicable"),
)
def test_reviewer_overview_rejects_placeholder_only_content_for_each_point(
    point_index: int,
    placeholder: str,
) -> None:
    contents = list(REVIEWER_POINT_CONTENT)
    contents[point_index] = (
        f"In scope: {placeholder}\nOut of scope: {placeholder}"
        if point_index == 1
        else placeholder
    )
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(tuple(contents))) == [
        REVIEWER_MEANING_FAILURES[point_index]
    ]


@pytest.mark.parametrize(
    "scope_content",
    (
        "In scope: Guardrail behavior.",
        "Out of scope: Product behavior.",
        "In scope: TODO\nOut of scope: Product behavior.",
        "In scope: Guardrail behavior.\nOut of scope: TBD",
    ),
)
def test_reviewer_overview_requires_meaningful_in_and_out_of_scope(scope_content: str) -> None:
    contents = list(REVIEWER_POINT_CONTENT)
    contents[1] = scope_content
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(tuple(contents))) == [
        REVIEWER_MEANING_FAILURES[1]
    ]


def test_reviewer_overview_rejects_untouched_or_visible_template_instructions() -> None:
    comments = tuple(f"<!-- {content} -->" for content in REVIEWER_POINT_CONTENT)
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(comments)) == list(
        REVIEWER_MEANING_FAILURES
    )
    instructions = (
        "Explain the change and the problem or need it addresses in plain language.",
        "In scope: Describe what the PR changes.\nOut of scope: Describe what it intentionally does not change.",
        "Identify the main files, modules, workflows, or documents affected.",
        "Tell the reviewer which decisions, risks, invariants, or behaviors deserve close attention.",
        "Summarize tests and checks, known limitations, remaining risks, and human-only decisions.",
    )
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(instructions)) == list(
        REVIEWER_MEANING_FAILURES
    )
    fenced = tuple(f"```text\n{instruction}\n```" for instruction in instructions)
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(fenced)) == list(
        REVIEWER_MEANING_FAILURES
    )
    specific = (
        instructions[0] + " This PR prevents evidence tables from hiding the purpose.",
        "In scope: Describe what the PR changes. The template and local guardrail change.\n"
        "Out of scope: Describe what it intentionally does not change. Runtime behavior remains unchanged.",
        instructions[2] + " The template and local guardrail are affected.",
        instructions[3] + " Check parser boundaries and stable findings.",
        instructions[4] + " Focused tests pass; clarity remains human-reviewed.",
    )
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(specific)) == []


@pytest.mark.parametrize("point_index", range(5))
@pytest.mark.parametrize("wrapper", ("**{}**", "`{}`", "_{}_"))
def test_reviewer_overview_rejects_markdown_wrapped_placeholders(
    point_index: int,
    wrapper: str,
) -> None:
    contents = list(REVIEWER_POINT_CONTENT)
    wrapped = wrapper.format("TODO")
    contents[point_index] = (
        f"In scope: {wrapped}\nOut of scope: {wrapped}"
        if point_index == 1
        else wrapped
    )
    assert guardrails.reviewer_overview_failures(reviewer_overview_body(tuple(contents))) == [
        REVIEWER_MEANING_FAILURES[point_index]
    ]


def test_reviewer_overview_first_duplicate_is_authoritative_and_parsing_is_scoped() -> None:
    placeholder = ("TODO", "In scope: TODO\nOut of scope: TBD", "TBD", "pending", "N/A")
    body = (
        "## Unrelated section\n\n### 1. What changed and why\nUnrelated prose.\n\n"
        + reviewer_overview_body(placeholder)
        + "\n"
        + reviewer_overview_body()
    )
    assert guardrails.reviewer_overview_failures(body) == list(REVIEWER_MEANING_FAILURES)


def test_reviewer_overview_parsing_is_deterministic_across_unrelated_markdown() -> None:
    body = reviewer_overview_body().replace("## Reviewer overview", "##   rEvIeWeR OvErViEw   ")
    for heading in REVIEWER_POINT_HEADINGS:
        body = body.replace(f"### {heading}", f"###  {heading.swapcase()}  ")
    assert guardrails.reviewer_overview_failures(
        "## Stage\nGovernance\n\n## Summary\n| Note | Value |\n|---|---|\n| Scope | unrelated |\n\n"
        + body
        + "\n## Notes\nHuman review remains required.\n"
    ) == []

    multiple_missing = reviewer_overview_body(omit=0).replace(
        "### 3. Key files and components\n\n" + REVIEWER_POINT_CONTENT[2] + "\n",
        "",
    )
    assert guardrails.reviewer_overview_failures(multiple_missing) == [
        "Reviewer overview must include point 1: What changed and why.",
        "Reviewer overview must include point 3: Key files and components.",
    ]


def test_reviewer_overview_rejects_wrong_level_and_fenced_headings() -> None:
    for index, heading in enumerate(REVIEWER_POINT_HEADINGS):
        wrong_level = reviewer_overview_body().replace(f"### {heading}", f"#### {heading}")
        assert guardrails.reviewer_overview_failures(wrong_level) == [
            f"Reviewer overview must include point {heading.replace('.', ':', 1)}."
        ], index
    for marker in ("#", "###"):
        wrong_overview = reviewer_overview_body().replace("## Reviewer overview", f"{marker} Reviewer overview")
        assert guardrails.reviewer_overview_failures(wrong_overview) == [MISSING_REVIEWER_OVERVIEW]
    fenced = "```markdown\n" + reviewer_overview_body() + "```\n"
    assert guardrails.reviewer_overview_failures(fenced) == [MISSING_REVIEWER_OVERVIEW]


def test_reviewer_overview_preserves_existing_guarded_pr_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_finalized_body = completed_preflight_body().replace(
        "No repository-tracked status change is claimed by this PR. Routine post-merge facts go to "
        "PR/issue comments, with no successor status-only PR.",
        "`docs/STATUS.md` is finalized in this PR as the post-merge target state for the issue, "
        "including the next issue pointer. Routine post-merge facts go to PR/issue comments, "
        "with no successor status-only PR.",
    )
    valid = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=status_finalized_body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["scripts/guardrails_check.py", "docs/STATUS.md"],
    )
    assert valid == []
    prohibited = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=status_finalized_body.replace("Refs #44", "Refs #44\nFixes #44", 1),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["scripts/guardrails_check.py", "docs/STATUS.md"],
    )
    assert prohibited == [
        "Pull request title/body/commit messages must use reference-only issue wording."
    ]

    missing = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=status_finalized_body.replace(reviewer_overview_body() + "\n", ""),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["scripts/guardrails_check.py", "docs/STATUS.md"],
    )
    assert missing == [MISSING_REVIEWER_OVERVIEW]

    combined = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=status_finalized_body.replace("Refs #44", "Fixes #44", 1).replace(
            REVIEWER_POINT_CONTENT[0], "TODO", 1
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["scripts/guardrails_check.py", "docs/STATUS.md"],
    )
    assert combined == [
        "Pull request title/body/commit messages must use reference-only issue wording.",
        "Pull request body must link an issue using reference-only wording such as Refs #<issue>.",
        REVIEWER_MEANING_FAILURES[0],
    ]


def test_reviewer_overview_does_not_change_nontrivial_detection_or_add_external_lookups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert guardrails.is_nontrivial_pull_request(["scripts/guardrails_check.py"]) is True
    assert guardrails.is_nontrivial_pull_request(["docs/notes.md"]) is False

    def fail_external_lookup(*args: object, **kwargs: object) -> object:
        raise AssertionError("reviewer overview parsing must remain local")

    monkeypatch.setattr(guardrails, "urlopen", fail_external_lookup)
    monkeypatch.setattr(guardrails, "Request", fail_external_lookup)
    monkeypatch.setattr(guardrails, "run_git", fail_external_lookup)
    monkeypatch.setattr(guardrails, "github_reference_exists", fail_external_lookup)
    monkeypatch.setattr(guardrails, "github_pull_request_is_merged", fail_external_lookup)
    monkeypatch.setattr(guardrails, "os", type("NoEnvironment", (), {"__getattr__": fail_external_lookup})())
    assert guardrails.reviewer_overview_failures(reviewer_overview_body()) == []


def test_product_context_accepts_complete_self_contained_pr_specific_content() -> None:
    assert guardrails.product_context_failures(product_context_body()) == []


def test_resource_lifecycle_accepts_complete_owned_resource_row() -> None:
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body()) == []


def test_resource_lifecycle_accepts_one_exact_buildx_cache_id_selector() -> None:
    row = (
        "| cache 0123456789abcdefghijklmnop | created by issue 391 after a zero-cache baseline | "
        'success-clean | {"disposition":"delete","kind":"buildkit-cache-record",'
        '"locator":"0123456789abcdefghijklmnop","trigger":"merged-main-green"} | '
        "docker buildx du proves that exact ID absent |"
    )
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == []


def test_resource_lifecycle_accepts_one_exact_recursive_temporary_path() -> None:
    row = (
        "| /private/tmp/exact-issue-391-directory | created only for issue 391 | "
        'always-clean | {"disposition":"delete","kind":"filesystem-path",'
        '"locator":"/private/tmp/exact-issue-391-directory","trigger":"session-end"} | '
        "test -e proves the exact path absent |"
    )
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == []


@pytest.mark.parametrize(
    ("kind", "locator"),
    (
        ("git-worktree", "worktree:feature-safe"),
        ("python-venv", ".venv"),
        ("node-modules", "frontend/node_modules"),
        ("filesystem-path", "reports/security"),
    ),
)
def test_resource_lifecycle_accepts_public_safe_context_relative_locators(
    kind: str, locator: str,
) -> None:
    cleanup = json.dumps(
        {"disposition": "retain", "kind": kind, "locator": locator, "trigger": "owner-verified"},
        separators=(",", ":"),
    )
    row = f"| exact resource | exact ownership proof | shared-retain | {cleanup} | retained proof |"
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == []


@pytest.mark.parametrize(
    ("kind", "locator", "disposition", "retention"),
    (
        ("git-branch", "feature-safe", "delete", "success-clean"),
        ("docker-image", "sha256:0123456789abcdef", "delete", "always-clean"),
        ("docker-image", "narratwin-ai:repro-issue151-123", "delete", "always-clean"),
        ("docker-container", "citevyn-db", "retain", "persistent"),
    ),
)
def test_resource_lifecycle_accepts_structured_exact_locators(
    kind: str, locator: str, disposition: str, retention: str,
) -> None:
    cleanup = json.dumps(
        {"disposition": disposition, "kind": kind, "locator": locator, "trigger": "owner-verified"},
        separators=(",", ":"),
    )
    row = (
        f"| exact governed resource | independently inventoried ownership | {retention} | "
        f"{cleanup} | exact absence proof |"
    )
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == []


def test_resource_lifecycle_rejects_missing_section() -> None:
    assert guardrails.resource_lifecycle_failures(product_context_body()) == [
        MISSING_RESOURCE_LIFECYCLE
    ]


@pytest.mark.parametrize(
    ("cleanup", "retention"),
    (
        ("{}", "success-clean"),
        ('{"disposition":"delete","kind":"git-branch","locator":"feature-safe"}', "success-clean"),
        ('{"disposition":"delete","kind":"git-branch","locator":"feature-safe","trigger":"merged","command":"git branch -d feature-safe"}', "success-clean"),
        ('{"disposition":"purge","kind":"git-branch","locator":"feature-safe","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","kind":"shell-command","locator":"feature-safe","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","kind":"filesystem-path","locator":"/tmp/*","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","kind":"filesystem-path","locator":"$HOME","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","disposition":"retain","kind":"git-branch","locator":"feature-safe","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","kind":"filesystem-path","locator":"/","trigger":"merged"}', "success-clean"),
        ('{"disposition":"delete","kind":"git-branch","locator":"feature-safe","trigger":"merged;rm"}', "success-clean"),
        ('{"disposition":"delete","kind":"docker-container","locator":"citevyn-db","trigger":"owner"}', "persistent"),
        ('{"disposition":"retain","kind":"git-branch","locator":"feature-safe","trigger":"merged"}', "success-clean"),
        ("not-json", "success-clean"),
    ),
)
def test_resource_lifecycle_rejects_invalid_structured_cleanup_contract(
    cleanup: str, retention: str,
) -> None:
    row = f"| exact resource | exact ownership proof | {retention} | {cleanup} | exact proof |"
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


@pytest.mark.parametrize(
    "row",
    (
        '| Run docker system prune | exact owner | success-clean | {"disposition":"delete","kind":"git-branch","locator":"feature-safe","trigger":"merged"} | absence proof |',
        '| exact resource | Execute git branch -D main | success-clean | {"disposition":"delete","kind":"git-branch","locator":"feature-safe","trigger":"merged"} | absence proof |',
        '| exact resource | exact owner | success-clean | {"disposition":"delete","kind":"git-branch","locator":"feature-safe","trigger":"merged"} | Run docker system prune; exact absence proof |',
    ),
)
def test_resource_lifecycle_rejects_cross_cell_command_injection(row: str) -> None:
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


def test_resource_lifecycle_rejects_duplicate_or_conflicting_locator_decisions() -> None:
    first = (
        '| exact path | exact owner | success-clean | '
        '{"disposition":"delete","kind":"filesystem-path","locator":"reports/security",'
        '"trigger":"merged"} | absence proof |'
    )
    second = (
        '| same exact path | exact owner | shared-retain | '
        '{"disposition":"retain","kind":"filesystem-path","locator":"reports/security",'
        '"trigger":"owner"} | retained proof |'
    )
    for duplicate in (first, second):
        body = resource_lifecycle_body(row=first) + duplicate + "\n"
        assert guardrails.resource_lifecycle_failures(body) == [
            "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
        ]


def test_resource_lifecycle_rejects_delete_disposition_for_shared_resource_kind() -> None:
    row = (
        '| shared cache | exact shared ownership | success-clean | '
        '{"disposition":"delete","kind":"shared-resource","locator":"shared-cache",'
        '"trigger":"merged"} | absence proof |'
    )
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


@pytest.mark.parametrize("locator", (str(Path.home()), str(Path(__file__).parents[2])))
def test_resource_lifecycle_rejects_home_or_repository_root_deletion(locator: str) -> None:
    cleanup = json.dumps(
        {"disposition": "delete", "kind": "filesystem-path", "locator": locator, "trigger": "merged"},
        separators=(",", ":"),
    )
    row = f"| protected root | exact owner | success-clean | {cleanup} | absence proof |"
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


@pytest.mark.parametrize(
    "row",
    (
        "| issue-391 worktree | owner | success-clean | remove after merge | |",
        "| issue-391 worktree | TODO | success-clean | remove after merge | issue comment |",
        "| N/A | no resources | N/A | N/A | N/A |",
        "| issue-391 worktree | created by issue 391 | keep someday | remove after merge | issue comment |",
        "| issue-391 worktree | owner | success-clean | broad Docker prune | issue comment |",
        "| issue-391 cache | owner | success-clean | docker builder prune --all | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --all | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -D main | issue comment |",
        "| issue-391 worktree | owner | success-clean | git worktree remove --force issue-391 | issue comment |",
        "| issue-391 image | owner | success-clean | docker image rm --force issue-391:ci | issue comment |",
        '| issue-391 directory | owner | success-clean | rm -r -f "$HOME" | issue comment |',
        '| issue-391 directory | owner | success-clean | rm --recursive -f "$HOME" | issue comment |',
        "| issue-391 branch | owner | success-clean | git reset --hard | issue comment |",
        "| issue-391 branch | owner | success-clean | git switch main | issue comment |",
        "| issue-391 reports | owner | success-clean | remove reports/security/* | issue comment |",
        "| issue-391 directory | owner | success-clean | rm -r / | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id=ABCDEFGHIJKLMNOPQRST | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id==0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id=0123456789abcdefghijklmnop -af | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id=0123456789abcdefghijklmnop -fa | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id=0123456789abcdefghijklmnop && docker buildx prune | issue comment |",
        "| issue-391 cache | owner | success-clean | docker buildx prune --filter id=0123456789abcdefghijklmnop ; docker buildx prune | issue comment |",
        "| issue-391 branch | owner | success-clean | git -C /tmp/repo reset --hard | issue comment |",
        "| issue-391 branch | owner | success-clean | Git branch -D main | issue comment |",
        "| issue-391 image | owner | success-clean | docker --context default image rm -f shared:ci | issue comment |",
        '| issue-391 worktree | owner | success-clean | git worktree remove "$(pwd)" | issue comment |',
        "| issue-391 branch | owner | success-clean | git branch -df main | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -f -d main | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -Dmain | issue comment |",
        "| issue-391 image | owner | success-clean | docker -c default image rm -f shared:ci | issue comment |",
        "| issue-391 container | owner | success-clean | docker container rm -f shared-container | issue comment |",
        "| issue-391 container | owner | success-clean | docker container prune | issue comment |",
        "| issue-391 file | owner | success-clean | rm -f /private/tmp/exact-owned-file | issue comment |",
        "| issue-391 branch | owner | success-clean | after merge run `git branch -D main` and verify absence | issue comment |",
        "| issue-391 cache | owner | success-clean | run `docker buildx prune --all` and verify absence | issue comment |",
        "| issue-391 cache | owner | success-clean | (docker buildx prune --all) | issue comment |",
        "| issue-391 worktree | owner | success-clean | git worktree remove `pwd` | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch --force=true main | issue comment |",
        "| issue-391 image | owner | success-clean | docker image rm --force=true shared:ci | issue comment |",
        "| issue-391 file | owner | success-clean | rm --force=true /private/tmp/exact-owned-file | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -M old main | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -C source main | issue comment |",
        "| issue-391 container | owner | success-clean | docker --log-level debug container prune | issue comment |",
        "| issue-391 container | owner | success-clean | docker --tlscert cert.pem container prune | issue comment |",
        "| issue-391 cache | owner | success-clean | DOCKER_HOST=tcp://remote docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | sudo docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | sudo -n docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | doas docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | eval docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | bash -c 'docker buildx prune --filter id=0123456789abcdefghijklmnop' | issue comment |",
        "| issue-391 worktree | owner | success-clean | git worktree remove <(pwd) | issue comment |",
        "| issue-391 resource | owner | success-clean | remove exact resource | docker buildx prune --all | evidence |",
        r"| issue-391 resource | owner | success-clean | remove exact resource \| docker buildx prune --all | evidence |",
        "| issue-391 branch | owner | success-clean | git branch -d `printf main` | issue comment |",
        "| issue-391 image | owner | success-clean | docker image rm `docker images -q` | issue comment |",
        "| issue-391 file | owner | success-clean | rm `find /tmp -type f` | issue comment |",
        "| issue-391 cache | owner | success-clean | docker context use remote && docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | ssh host docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | find /tmp -exec docker buildx prune --filter id=0123456789abcdefghijklmnop ; | issue comment |",
        "| issue-391 cache | owner | success-clean | chroot /private/tmp/root docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 cache | owner | success-clean | timeout 30 docker buildx prune --filter id=0123456789abcdefghijklmnop | issue comment |",
        "| issue-391 image | owner | success-clean | docker --context remote image rm exact-owned | issue comment |",
        "| issue-391 image | owner | success-clean | docker -H tcp://remote image rm exact-owned | issue comment |",
        "| issue-391 branch | owner | success-clean | git -C /other/repository branch -d exact-owned | issue comment |",
        "| issue-391 branch | owner | success-clean | git --git-dir=/other/repository/.git branch -d exact-owned | issue comment |",
        "| issue-391 builder | owner | success-clean | docker buildx rm --all-inactive | issue comment |",
        "| issue-391 builder | owner | success-clean | docker builder rm --all-inactive | issue comment |",
        "| issue-391 cache | owner | success-clean | DOCKER_HOST=tcp://remote `docker buildx prune --filter id=0123456789abcdefghijklmnop` | issue comment |",
        "| issue-391 cache | owner | success-clean | DOCKER_CONTEXT=remote `docker buildx prune --filter id=0123456789abcdefghijklmnop` | issue comment |",
        "| issue-391 image | owner | success-clean | export DOCKER_HOST=tcp://remote; docker image rm exact-owned | issue comment |",
        "| issue-391 branch | owner | success-clean | cd /other/repository && git branch -d exact-owned | issue comment |",
        "| issue-391 image | owner | success-clean | docker context use remote && docker image rm exact-owned | issue comment |",
        "| issue-391 cache | owner | success-clean | BUILDX_BUILDER=remote `docker buildx prune --filter id=0123456789abcdefghijklmnop` | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -d `hostname` | issue comment |",
        "| issue-391 image | owner | success-clean | docker image rm `whoami` | issue comment |",
        "| issue-391 branch | owner | success-clean | git branch -d `uuidgen` | issue comment |",
        "| issue-391 resource | owner | success-clean | Execute the exact cleanup command listed in evidence | docker system prune |",
        "| issue-391 resource | owner | success-clean | Execute the command specified in evidence | git branch -D main |",
        "|| issue-391 resource | owner | success-clean | remove exact resource | proof |",
        "| issue-391 resource | owner | success-clean | remove exact resource | proof ||",
        "| issue-391 image | owner | success-clean | export DOCKER_HOST=tcp://remote && docker image rm exact-owned | issue comment |",
        "| issue-391 branch | owner | success-clean | export GIT_DIR=/other/.git && git branch -d issue-391-safe | issue comment |",
        "| issue-391 builder | owner | success-clean | docker buildx use remote && docker buildx rm issue-391-builder | issue comment |",
        "| issue-391 compose | owner | success-clean | docker compose down --volumes --remove-orphans | issue comment |",
        "| issue-391 network | owner | success-clean | docker network disconnect --force shared-net shared-container | issue comment |",
        "| issue-391 ref | owner | success-clean | git update-ref -d refs/heads/main | issue comment |",
        "| issue-391 reflog | owner | success-clean | git reflog expire --expire=now --all | issue comment |",
        "| issue-391 objects | owner | success-clean | git gc --prune=now | issue comment |",
        "| issue-391 files | owner | success-clean | find /tmp -delete | issue comment |",
        "| issue-391 resource | owner | success-clean | Run the cleanup action from the final column | sudo docker image rm exact-owned |",
        "| issue-391 resource | owner | success-clean | Use the command under verification | docker image rm exact-owned |",
        "| issue-391 resource | owner | success-clean | Perform cleanup per the proof field | git branch -D main |",
    ),
)
def test_resource_lifecycle_rejects_partial_placeholder_na_or_broad_cleanup_row(
    row: str,
) -> None:
    assert guardrails.resource_lifecycle_failures(resource_lifecycle_body(row=row)) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("| Resource | Ownership proof | Retention class | Cleanup contract | Verification evidence |", "| Resource | Extra | Ownership proof | Retention class | Cleanup contract | Verification evidence |"),
        ("| Resource | Ownership proof | Retention class | Cleanup contract | Verification evidence |", "| Item | Ownership | Retention | Cleanup | Evidence |"),
        ("|---|---|---|---|---|", "|---|---|---|---|---|---|"),
        ("|---|---|---|---|---|", "|---x|---|---|---|---|"),
        ("|---|---|---|---|---|\n", ""),
    ),
)
def test_resource_lifecycle_rejects_malformed_header_or_separator(old: str, new: str) -> None:
    body = resource_lifecycle_body().replace(old, new)
    assert guardrails.resource_lifecycle_failures(body) == [
        "Resource lifecycle rows must identify exact ownership, retention, bounded cleanup, and verification evidence."
    ]


def test_resource_lifecycle_contract_is_durable_across_policy_and_future_projects() -> None:
    root = Path(__file__).parents[2]
    required_markers = {
        ".github/pull_request_template.md": (
            "## Resource lifecycle and cleanup",
            "Ownership proof",
            "Cleanup contract",
            '"disposition"',
            '"locator"',
        ),
        "docs/RESOURCE_LIFECYCLE.md": (
            "## Creation-Time Inventory",
            "## Cleanup Contract",
            "## Finalization Gate",
            "shared-retain",
        ),
        "docs/templates/AI_SESSION_FINALIZER_PROMPT.md": (
            "FINAL RESOURCE LIFECYCLE PHASE",
            "non-executable cleanup contract",
            "before starting the next increment",
            "Prove target absence",
        ),
        "docs/QUALITY_GATES.md": (
            "resource_lifecycle_failures",
            "structured JSON cleanup contract",
            "evidence-until-merged-main",
            "does not grant destructive authority",
        ),
    }
    for relative_path, markers in required_markers.items():
        text = (root / relative_path).read_text(encoding="utf-8")
        normalized = " ".join(text.lower().split())
        for marker in markers:
            assert " ".join(marker.lower().split()) in normalized, (
                f"{relative_path} missing durable resource lifecycle marker: {marker}"
            )


def test_product_context_accepts_complete_reviewer_impact_summary() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = (
        "#### Reviewer impact summary\n\n"
        "- **Purpose:** It removes ambiguity about the practical effect of a pull request so reviewers can decide confidently.\n"
        "- **Behavior before/after:** Reviewers previously reconstructed behavior from technical evidence; after merge they receive a direct observable comparison.\n"
        "- **Who and what is affected:** Pull-request authors and reviewers gain guidance and validation; runtime users, systems, product data, and provider behavior are unchanged.\n"
        "- **Artifacts/capabilities:** It adds reviewer guidance and validation while adding no voices, narration, audio, captions, avatars, or product capability.\n"
        "- **Operational impact:** No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.\n"
        "- **Scope boundaries:** This governance change adds no voices, narration, audio, captions, avatars, deployment, release, or production-readiness capability.\n"
        "- **End-to-end impact:** It removes a reviewer-context blocker while final narration, media cells, local review, and exact-artifact acceptance remain.\n\n"
        "#### Technical change list\n\n"
        "The template, validator, tests, governance policy, route, and context binding change together."
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


def test_product_context_rejects_missing_reviewer_impact_summary() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = "This PR updates the template, parser, tests, and governance documentation."
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 4 must begin with a Reviewer impact summary before the Technical change list."
    ]


def test_product_context_rejects_behavior_summary_after_technical_change_list() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    summary, technical = contents[3].split("#### Technical change list", maxsplit=1)
    contents[3] = f"#### Technical change list{technical}\n\n{summary}"
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 4 must begin with a Reviewer impact summary before the Technical change list."
    ]


@pytest.mark.parametrize("bullet_count", (0, 1, 2, 3, 4, 5, 6, 8, 9))
def test_product_context_rejects_reviewer_impact_summary_outside_exactly_seven_bullets(
    bullet_count: int,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    bullets = "\n".join(
        f"- Behavior outcome {index} is explained with concrete reviewer-specific words."
        for index in range(1, bullet_count + 1)
    )
    contents[3] = (
        f"#### Reviewer impact summary\n\n{bullets}\n\n"
        "#### Technical change list\n\nThe parser and template change together."
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


@pytest.mark.parametrize("invalid_bullet", ("TODO", "Issue #486", "tests/unit/test_guardrails_check.py"))
def test_product_context_rejects_placeholder_or_reference_only_impact_bullets(
    invalid_bullet: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = contents[3].replace(
        "This governance change adds no voices, narration, audio, captions, avatars, deployment, release, or production-readiness capability.",
        invalid_bullet,
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


@pytest.mark.parametrize(
    "summary_bullets",
    (
        (
            "It changes future pull request behavior by requiring a practical summary before technical details.",
            "It changes future pull request behavior by requiring a practical summary before technical details.",
            "It changes future pull request behavior by requiring a practical summary before technical details.",
        ),
        (
            "**Purpose:** Explain why this pull request matters to reviewers and users.",
            "**Behavior before/after:** Describe the behavior before and after this pull request merges.",
            "**Who and what is affected:** List who and what is affected including users, systems, and data.",
            "**Artifacts/capabilities:** State what artifacts and capabilities are added, changed, removed, or absent.",
            "**Operational impact:** State runtime, external, persistence, migration, compatibility, failure, and rollback effects.",
            "**Scope boundaries:** State what this pull request deliberately excludes or does not authorize.",
            "**End-to-end impact:** Explain the blocker removed, capability unlocked, and remaining gap.",
        ),
        (
            "**Purpose:** The status file records why the pull request matters.",
            "**Behavior before/after:** The guardrails script changes the before and after parser behavior.",
            "**Who and what is affected:** The template file affects authors, reviewers, systems, and data.",
            "**Artifacts/capabilities:** The documentation file lists artifacts and capabilities added, changed, removed, or absent.",
            "**Operational impact:** The policy file records runtime, external, persistence, migration, compatibility, failure, and rollback effects.",
            "**Scope boundaries:** The test file lists excluded provider, media, deployment, and release behavior.",
            "**End-to-end impact:** The route file records the blocker, capability, and remaining gap.",
        ),
    ),
    ids=(
        "duplicate",
        "prefixed-copied-instructions",
        "keyword-stuffed-technical-file-list",
    ),
)
def test_product_context_rejects_non_specific_impact_summary_false_passes(
    summary_bullets: tuple[str, ...],
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    bullets = "\n".join(f"- {bullet}" for bullet in summary_bullets)
    contents[3] = (
        f"#### Reviewer impact summary\n\n{bullets}\n\n"
        "#### Technical change list\n\nThe parser and template change together."
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


@pytest.mark.parametrize(
    "missing_index",
    range(7),
    ids=("purpose", "before-after", "affected", "artifacts", "operations", "boundaries", "end-to-end"),
)
def test_product_context_requires_every_reviewer_impact_category(
    missing_index: int,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    summary, technical = contents[3].split("#### Technical change list", maxsplit=1)
    bullets = [line for line in summary.splitlines() if line.startswith("- ")]
    del bullets[missing_index]
    bullet_text = "\n".join(bullets)
    contents[3] = (
        "#### Reviewer impact summary\n\n"
        f"{bullet_text}\n\n"
        f"#### Technical change list{technical}"
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


@pytest.mark.parametrize("mutation", ("reordered", "wrong-label", "duplicate-label"))
def test_product_context_rejects_reviewer_impact_label_mutations(
    mutation: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    summary, technical = contents[3].split("#### Technical change list", maxsplit=1)
    bullets = [line for line in summary.splitlines() if line.startswith("- ")]
    if mutation == "reordered":
        bullets[0], bullets[1] = bullets[1], bullets[0]
    elif mutation == "wrong-label":
        bullets[0] = bullets[0].replace("**Purpose:**", "**Outcome:**")
    else:
        bullets[1] = bullets[1].replace("**Behavior before/after:**", "**Purpose:**")
    bullet_text = "\n".join(bullets)
    contents[3] = (
        "#### Reviewer impact summary\n\n"
        f"{bullet_text}\n\n"
        f"#### Technical change list{technical}"
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


def test_product_context_accepts_exactly_seven_distinct_labeled_impact_bullets() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


@pytest.mark.parametrize(
    "summary_bullets",
    (
        (
            "**Purpose:** The change makes upload validation understandable to reviewers and product owners.",
            "**Behavior before/after:** Upload failures were previously ambiguous; afterward users receive a clear validation result.",
            "**Who and what is affected:** Upload users, reviewers, the validation system, and submitted document data are affected.",
            "**Artifacts/capabilities:** It adds validation documentation and reviewer capability but no audio or media artifacts.",
            "**Operational impact:** The provider module performs no network calls, migrations, persistence, or runtime side effects.",
            "**Scope boundaries:** Deployment, release, provider activation, and production-readiness behavior remain excluded.",
            "**End-to-end impact:** It removes the upload-review blocker while final human acceptance still remains.",
        ),
        (
            "**Purpose:** It lets reviewers understand why the governance change is necessary before examining implementation details.",
            "**Behavior before/after:** Reviewers previously inferred behavior; afterward the pull request states the observable change directly.",
            "**Who and what is affected:** Authors and reviewers are affected while runtime users, systems, and product data remain unchanged.",
            "**Artifacts/capabilities:** It adds clear guidance but no voices, narration, audio, captions, avatars, or media.",
            "**Operational impact:** None: this governance-only pull request causes no provider call, network access, migration, or runtime change.",
            "**Scope boundaries:** It does not authorize synthesis, deployment, release, public access, or production readiness.",
            "**End-to-end impact:** It removes the clarity blocker while human truth review and product delivery still remain.",
        ),
    ),
    ids=("ordinary-technical-nouns", "ordinary-explain-what-phrase"),
)
def test_product_context_accepts_truthful_labeled_summaries_with_ordinary_prose(
    summary_bullets: tuple[str, ...],
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    bullets = "\n".join(f"- {bullet}" for bullet in summary_bullets)
    contents[3] = (
        f"#### Reviewer impact summary\n\n{bullets}\n\n"
        "#### Technical change list\n\nThe parser and template change together."
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


def test_product_context_rejects_none_without_category_specific_reason() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = contents[3].replace(
        "No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.",
        "None",
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


def test_product_context_rejects_none_with_arbitrary_non_reason_prose() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = contents[3].replace(
        "No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.",
        "None: alpha beta runtime gamma delta epsilon zeta eta.",
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Reviewer impact summary must contain exactly 7 distinct labeled Markdown bullets."
    ]


def test_product_context_does_not_treat_nonetheless_as_none() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = contents[3].replace(
        "No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.",
        "Nonetheless, this governance change causes no runtime or external effects whatsoever.",
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


@pytest.mark.parametrize(
    ("target", "replacement"),
    (
        (
            "It adds reviewer guidance and validation while adding no product content, media artifact, or runtime capability.",
            "None: no artifacts or capabilities are added by this governance change.",
        ),
        (
            "Authors and reviewers gain guidance and validation; runtime users, systems, and product data are unchanged.",
            "None: users and systems remain unchanged because this change is documentation only.",
        ),
        (
            "No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.",
            "None because this governance change has no runtime or provider behavior.",
        ),
        (
            "No runtime call, network access, persistence, migration, compatibility change, new failure mode, or rollback action occurs.",
            "None: this pull request only changes repository documentation and governance instructions.",
        ),
    ),
)
def test_product_context_accepts_none_with_ordinary_no_effect_reason(
    target: str,
    replacement: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = contents[3].replace(target, replacement)
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


def test_product_context_rejects_missing_section() -> None:
    assert guardrails.product_context_failures(reviewer_overview_body()) == [
        "Non-trivial pull requests must include a Product and reviewer context section."
    ]


@pytest.mark.parametrize(("missing_index", "heading"), tuple(enumerate(PRODUCT_CONTEXT_HEADINGS)))
def test_product_context_rejects_each_missing_subsection(
    missing_index: int,
    heading: str,
) -> None:
    assert guardrails.product_context_failures(product_context_body(omit=missing_index)) == [
        f"Product context must include point {heading.replace('.', ':', 1)}."
    ]


@pytest.mark.parametrize(
    "insufficient_content",
    (
        "Issue #315",
        "Refs #315",
        "https://github.com/imrohitagrawal/narratwin-ai/issues/315",
        "[Issue 315](https://github.com/imrohitagrawal/narratwin-ai/issues/315)",
        "Updates the project with the required changes.",
        "See the linked issue and other details for more information.",
        "TODO",
        "```text\nTBD\n```",
    ),
)
def test_product_context_rejects_non_self_contained_or_generic_content(
    insufficient_content: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[2] = insufficient_content
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 3 must contain self-contained PR-specific plain-English content; issue references and links are supplemental only."
    ]


@pytest.mark.parametrize(
    "unexpanded_claim",
    (
        "This PR adds ten mandatory product-context fields to the pull request template.",
        "This PR adds 10 required reviewer controls to the pull request template.",
    ),
)
def test_product_context_rejects_counted_exact_changes_without_complete_enumeration(
    unexpanded_claim: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = exact_changes_with_summary(unexpanded_claim)
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 4 must enumerate every item in a counted exact-change claim."
    ]


def test_product_context_accepts_counted_exact_changes_with_complete_enumeration() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = exact_changes_with_summary(
        "This PR adds ten mandatory product-context fields:\n"
        + "\n".join(
            f"{index}. Field {index} has a distinct reviewer outcome."
            for index in range(1, 11)
        )
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == []


@pytest.mark.parametrize(
    "invalid_items",
    (
        ["The same repeated field description."] * 10,
        [f"Field {index} has a distinct reviewer outcome." for index in range(1, 10)]
        + ["TBD"],
    ),
)
def test_product_context_rejects_duplicate_or_placeholder_counted_items(
    invalid_items: list[str],
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = exact_changes_with_summary(
        "This PR adds ten mandatory product-context fields:\n"
        + "\n".join(
            f"{index}. {item}" for index, item in enumerate(invalid_items, start=1)
        )
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 4 must enumerate every item in a counted exact-change claim."
    ]


def test_product_context_does_not_reuse_one_enumeration_for_another_counted_claim() -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[3] = exact_changes_with_summary(
        "This PR adds two required controls:\n"
        "1. The author supplies exact product context.\n"
        "2. The reviewer checks explicit pass conditions.\n\n"
        "This PR also changes three governance files:\n"
        "1. The pull request template changes.\n"
        "2. The local guardrail parser changes."
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context point 4 must enumerate every item in a counted exact-change claim."
    ]


@pytest.mark.parametrize(
    "missing_field",
    ("Expected behavior", "Prohibited behavior", "Evidence", "Pass condition", "Fail condition"),
)
def test_product_context_reviewer_validation_requires_each_outcome_field(
    missing_field: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[9] = "\n".join(
        line for line in contents[9].splitlines() if not line.startswith(f"{missing_field}:")
    )
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        f"Product context reviewer validation must include {missing_field.lower()}."
    ]


@pytest.mark.parametrize(
    "unsupported_claim",
    (
        "This PR makes NarraTwin production-ready for customers.",
        "NarraTwin is now ready for production deployment to external customers worldwide.",
        "The product is deployed to production by this change.",
        "This change makes NarraTwin publicly available to external users immediately.",
    ),
)
def test_product_context_rejects_unsupported_production_or_release_claims(
    unsupported_claim: str,
) -> None:
    contents = list(PRODUCT_CONTEXT_CONTENT)
    contents[7] = unsupported_claim
    assert guardrails.product_context_failures(product_context_body(tuple(contents))) == [
        "Product context must not claim production readiness, production deployment, release, or public availability without separate authorization."
    ]


def test_product_context_contract_is_durable_across_rules_template_and_policy_docs() -> None:
    root = Path(__file__).parents[2]
    template = (root / ".github/pull_request_template.md").read_text(encoding="utf-8")
    for heading in ("## Product and reviewer context", *PRODUCT_CONTEXT_HEADINGS):
        assert heading in template
    assert "#### Reviewer impact summary" in template
    assert "#### Technical change list" in template
    for label in (
        "**Purpose:**",
        "**Behavior before/after:**",
        "**Who and what is affected:**",
        "**Artifacts/capabilities:**",
        "**Operational impact:**",
        "**Scope boundaries:**",
        "**End-to-end impact:**",
    ):
        assert label in template

    required_markers = {
        "AGENTS.md": (
            "self-contained plain English",
            "end product goal",
            "issue references and links are supplemental",
        ),
        "docs/REPOSITORY_GUARDRAILS.md": (
            "Product and reviewer context",
            "issue-only",
            "policy-gates",
            "exactly seven distinct",
            "Behavior before/after",
            "Who and what is affected",
            "Artifacts/capabilities",
            "Operational impact",
            "Scope boundaries",
            "End-to-end impact",
        ),
        "docs/QUALITY_GATES.md": (
            "Product and reviewer context",
            "production path",
            "product_context_failures",
            "Reviewer impact summary",
            "exactly seven distinct",
            "Behavior before/after",
            "Who and what is affected",
            "Artifacts/capabilities",
            "Operational impact",
            "Scope boundaries",
            "End-to-end impact",
        ),
        "docs/SKILL_EXECUTION_PLAN.md": (
            "Issue 315",
            "product-context",
            "TDD",
        ),
        "docs/STATUS.md": (
            "issue #315",
            "self-contained product and end-goal context",
            "runtime and production authorization remain unchanged",
            "reviewer-impact summary",
            "exactly seven distinct",
        ),
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": (
            "End product goal",
            "Exact changes",
            "enumerate every counted item",
            "independent reviewer",
        ),
    }
    for relative_path, markers in required_markers.items():
        text = (root / relative_path).read_text(encoding="utf-8")
        normalized_text = " ".join(text.lower().split())
        for marker in markers:
            assert " ".join(marker.lower().split()) in normalized_text, (
                f"{relative_path} missing durable product-context marker: {marker}"
            )


def test_phase1_issue39_pull_request_allows_reference_only_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39",
    )

    assert failures == []


def test_phase1_issue39_pull_request_reference_only_body_still_fails_on_malformed_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, malformed_id="DUR-STAGE4-001")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
    )

    assert any("Issue #39 matrix row must have 6 columns:" in failure for failure in failures)


def test_phase1_issue39_pull_request_rejects_issue_39_matrix_placeholder_contract_without_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path)
    replace_matrix_row_cell(
        tmp_path / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
        "DUR-STAGE4-001",
        4,
        "TODO",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert (
        "Issue #39 matrix row DUR-STAGE4-001 has placeholder evidence contract content."
        in failures
    )


def test_phase1_issue39_pull_request_rejects_issue_39_matrix_missing_required_id_without_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, omitted_ids={"DUR-STAGE4-001"})
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert "Issue #39 production closure plan missing matrix IDs: DUR-STAGE4-001" in failures


def test_phase1_issue39_pull_request_rejects_issue_39_matrix_duplicate_row_without_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path)
    insert_duplicate_matrix_row(tmp_path / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md", "DUR-STAGE4-001")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert "Issue #39 production closure plan has duplicate matrix IDs: DUR-STAGE4-001" in failures


def test_phase1_issue39_pull_request_rejects_issue_39_matrix_unexpected_id_without_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path)
    insert_matrix_row_before_closure_records(
        tmp_path / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
        "| `OPS-BOGUS-001` | Synthetic matrix placeholder | Placeholder evidence target | Owner | Contract text for placeholder row | Open |",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert "Issue #39 production closure plan has unexpected matrix IDs: OPS-BOGUS-001" in failures


def test_phase1_issue39_pull_request_rejects_issue_39_matrix_invalid_status_without_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path)
    replace_matrix_row_cell(
        tmp_path / "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
        "DUR-STAGE4-001",
        5,
        "Done",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence",
        body="Refs #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert "Issue #39 matrix row DUR-STAGE4-001 status must be Open or Closed; got Done." in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_in_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve #39 local durability and ops status evidence",
        body="Refs #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_colon_closing_keyword_in_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve: #39 local durability and ops status evidence",
        body="Refs #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_in_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nFixes #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_allows_closing_keyword_only_after_matrix_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE not in failures
    assert "Pull request title/body/commit messages must use reference-only issue wording." not in failures
    assert ("issues", "70") in guardrails._test_github_reference_calls
    assert ("pulls", "71") in guardrails._test_github_reference_calls


def test_phase1_issue39_pull_request_rejects_id_prefixed_generic_closure_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, generic_records=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_id_prefixed_generic_evidence_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, generic_evidence_only=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_padded_generic_evidence_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, padded_generic_evidence_only=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_artifact_only_row_id_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, artifact_id_only=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_markdown_label_only_artifact_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, artifact_label_id_only=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_doc_only_sensitive_closure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, doc_only_evidence=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_context0_pr64_as_final_row_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification_for_context0_pr64(monkeypatch)
    write_issue39_closure_plan(
        tmp_path,
        child_pr="https://github.com/imrohitagrawal/narratwin-ai/pull/64",
        context0_pr64_evidence=True,
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


@pytest.mark.parametrize(
    "context0_text",
    [
        "PR number 64",
        "pull request 64",
        "pull request number 64",
    ],
)
def test_phase1_issue39_pull_request_rejects_context0_pr64_text_variants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    context0_text: str,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, context0_pr64_text=context0_text)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_context0_child_pr_number(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification_for_context0_pr64(monkeypatch)
    write_issue39_closure_plan(
        tmp_path,
        child_pr="https://github.com/imrohitagrawal/narratwin-ai/pull/64",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_unmerged_child_pr_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    monkeypatch.setattr(guardrails, "github_pull_request_is_merged", lambda number: False, raising=False)
    write_issue39_closure_plan(tmp_path)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_weak_human_only_sensitive_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, weak_human_only_evidence=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_accepts_valid_human_only_sensitive_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, valid_human_only_evidence=True)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE not in failures


def test_phase1_issue39_pull_request_rejects_bare_child_issue_pr_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, child_issue="#70", child_pr="PR #71")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_unverified_child_issue_pr_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guardrails, "github_reference_exists", lambda resource, number: False)
    write_issue39_closure_plan(tmp_path)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_issue39_required_matrix_ids_include_slo_and_untrusted_input_rows() -> None:
    assert "OPS-SLO-001" in guardrails.REQUIRED_ISSUE_39_CLOSURE_MATRIX_IDS
    assert "SEC-UNTRUSTED-001" in guardrails.REQUIRED_ISSUE_39_CLOSURE_MATRIX_IDS


class FakeGitHubResponse:
    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        self.status = status
        self.payload = payload

    def __enter__(self) -> "FakeGitHubResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_github_reference_exists_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("urlopen must not be called without a token")

    monkeypatch.setattr(guardrails, "urlopen", fail_urlopen)

    assert guardrails.github_reference_exists("issues", "70") is False


def test_github_reference_exists_distinguishes_issue_from_pr_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        request_url = getattr(request, "full_url", "")
        if request_url.endswith("/issues/70"):
            return FakeGitHubResponse(200, {"number": 70, "title": "child issue"})
        if request_url.endswith("/issues/71"):
            return FakeGitHubResponse(200, {"number": 71, "pull_request": {"url": "https://api.github.com/pr"}})
        if request_url.endswith("/pulls/71"):
            return FakeGitHubResponse(200, {"number": 71, "title": "evidence pr"})
        return FakeGitHubResponse(404, {})

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_reference_exists("issues", "70") is True
    assert guardrails.github_reference_exists("issues", "71") is False
    assert guardrails.github_reference_exists("pulls", "71") is True
    assert guardrails.github_reference_exists("pulls", "9999") is False


def test_github_pull_request_is_merged_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    def fail_urlopen(*args: object, **kwargs: object) -> object:
        raise AssertionError("urlopen must not be called without a token")

    monkeypatch.setattr(guardrails, "urlopen", fail_urlopen)

    assert guardrails.github_pull_request_is_merged("71") is False


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"number": 71, "merged": True, "merged_at": "2026-07-10T00:00:00Z"}, True),
        ({"number": 71, "merged": False, "merged_at": None}, False),
        ({"number": 71, "state": "open"}, False),
    ],
)
def test_github_pull_request_is_merged_uses_pull_payload(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, Any],
    expected: bool,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        assert getattr(request, "full_url", "").endswith("/pulls/71")
        return FakeGitHubResponse(200, payload)

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_pull_request_is_merged("71") is expected


def test_github_pull_request_numbers_for_commit_rejects_missing_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    assert guardrails.github_pull_request_numbers_for_commit("abcdef") == []


def test_is_merged_pull_request_merge_push_checks_only_merged_prs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guardrails, "github_pull_request_numbers_for_commit", lambda _sha: ["71", "72"])

    calls: list[str] = []

    def fake_github_pull_request_is_merged_to_main(number: str) -> bool:
        calls.append(number)
        return number == "72"

    monkeypatch.setattr(
        guardrails,
        "github_pull_request_is_merged_to_main",
        fake_github_pull_request_is_merged_to_main,
    )

    assert guardrails.is_merged_pull_request_merge_push("abcdef") is True
    assert calls == ["71", "72"]


def test_github_pull_request_is_merged_to_main_rejects_non_main_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        assert str(getattr(request, "full_url", "")).endswith("/pulls/71")
        return FakeGitHubResponse(
            200,
            {"number": 71, "merged": True, "base": {"ref": "release/v2"}},
        )

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_pull_request_is_merged_to_main("71") is False


def test_github_pull_request_is_merged_to_main_requires_merged_main_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        assert str(getattr(request, "full_url", "")).endswith("/pulls/72")
        return FakeGitHubResponse(
            200,
            {"number": 72, "merged": True, "base": {"ref": "main"}},
        )

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_pull_request_is_merged_to_main("72") is True


def test_github_pull_request_is_merged_to_main_rejects_non_dict_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        assert str(getattr(request, "full_url", "")).endswith("/pulls/73")
        return FakeGitHubResponse(
            200,
            {"number": 73, "merged": True, "base": "main"},
        )

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_pull_request_is_merged_to_main("73") is False


def test_github_pull_request_is_merged_to_main_rejects_missing_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_urlopen(request: object, timeout: int) -> FakeGitHubResponse:
        assert timeout == 5
        assert str(getattr(request, "full_url", "")).endswith("/pulls/74")
        return FakeGitHubResponse(200, {"number": 74, "merged": True})

    monkeypatch.setattr(guardrails, "urlopen", fake_urlopen)

    assert guardrails.github_pull_request_is_merged_to_main("74") is False


@pytest.mark.parametrize(
    "sensitive_id",
    sorted(guardrails.REQUIRED_ISSUE_39_ROW_CONTRACT_TERMS),
)
def test_phase1_issue39_pull_request_rejects_weakened_sensitive_matrix_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sensitive_id: str,
) -> None:
    allow_github_reference_verification(monkeypatch)
    write_issue39_closure_plan(tmp_path, weakened_id=sensitive_id)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_when_matrix_id_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, omitted_ids={"DUR-STAGE4-001"})
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


@pytest.mark.parametrize("missing_id", ["OPS-SLO-001", "SEC-UNTRUSTED-001"])
def test_phase1_issue39_pull_request_rejects_closing_keyword_when_new_required_id_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_id: str,
) -> None:
    write_issue39_closure_plan(tmp_path, omitted_ids={missing_id})
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_without_closure_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, include_records=False)
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_with_malformed_matrix_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, malformed_id="DUR-STAGE4-001")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_closing_keyword_with_parent_issue_as_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(
        tmp_path,
        child_issue="https://github.com/imrohitagrawal/narratwin-ai/issues/39",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Refs #39 final production durability disposition",
        body="Refs #39\nFixes #39",
        head_ref="phase-1-closure-39-final-production-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_colon_closing_keyword_in_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nFixes: #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_cross_repo_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nCloses imrohitagrawal/narratwin-ai#39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_url_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39\nResolves https://github.com/imrohitagrawal/narratwin-ai/issues/39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_phase1_issue39_pull_request_rejects_commit_message_closing_keyword(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Phase 1 closure: local durability and ops status evidence (Refs #39)",
        body="Refs #39",
        commit_messages="fix: add local durability\n\nFixed #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_issue39_closing_keyword_is_rejected_on_any_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Resolve #39 local durability and ops status evidence",
        body="Refs #39",
        head_ref="fix/local-durability",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_issue39_commit_message_closing_keyword_is_rejected_on_any_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Local durability and ops status evidence",
        body="Refs #39",
        head_ref="fix/local-durability",
        commit_messages="fix: local durability\n\nResolves #39",
    )

    assert ISSUE_39_REFERENCE_ONLY_FAILURE in failures


def test_general_pull_request_allows_reference_only_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert failures == []


def test_issue223_terminal_status_loop_breaker_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Post-PR-222 status reconciliation",
        body=(
            "Refs #223\n\n"
            "This is the terminal status loop-breaker. It establishes a no successor rule: "
            "routine post-merge facts go to PR/issue comments, not another status-only PR."
        ),
        head_ref="phase-1-closure-process-223-post-pr-222-status-reconciliation",
    )

    assert failures == []


def test_future_post_pr_status_reconciliation_loop_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Post-PR-224 status reconciliation",
        body="Refs #225",
        head_ref="phase-1-closure-process-225-post-pr-224-status-reconciliation",
    )

    assert (
        "Standalone post-merge status reconciliation PRs are disallowed after issue #223; "
        "record routine post-merge facts in PR/issue comments or bundle STATUS.md cleanup into material work."
    ) in failures


def test_issue223_status_loop_breaker_requires_terminal_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Post-PR-222 status reconciliation",
        body="Refs #223\n\nRecords PR #222 status.",
        head_ref="phase-1-closure-process-223-post-pr-222-status-reconciliation",
    )

    assert (
        "Issue #223 is allowed only as the terminal status loop-breaker; the PR body must state terminal, "
        "loop-breaker, no-successor, post-merge facts, PR/issue comments, and status-only boundaries."
    ) in failures


def test_general_pull_request_rejects_closing_keyword_as_only_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Fixes #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert (
        "Pull request body must link an issue using reference-only wording such as Refs #<issue>."
    ) in failures


def test_general_pull_request_rejects_closing_keyword_even_with_reference_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="Refs #44\nFixes #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_general_pull_request_rejects_title_closing_keyword_even_with_reference_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Fixes #44",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_canonical_stage_pull_request_rejects_extra_closing_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Stage 2 architecture closure",
        body="Refs #44\nCloses #2\nFixes #44",
        head_ref="stage2-architecture-security-ai-safety",
    )

    assert "Pull request title/body/commit messages must not close non-canonical issues." in failures


@pytest.mark.parametrize(
    ("head_ref", "canonical_issue"),
    [
        ("stage2-architecture-security-ai-safety", "2"),
        ("stage3-governance-hardening", "5"),
        ("stage4-multiple-state-contract", "4"),
        ("stage5-local-evaluation-foundation", "10"),
        ("stage6-multilingual-sourcing", "11"),
        ("stage7-avatar-export", "12"),
        ("stage8-release-hardening", "13"),
    ],
)
def test_canonical_stage_pull_request_accepts_only_canonical_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    head_ref: str,
    canonical_issue: str,
) -> None:
    accepted = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title=f"Stage closure work for {head_ref}",
        body=f"Closes #{canonical_issue}",
        head_ref=head_ref,
    )
    assert accepted == []

    rejected = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title=f"Stage closure work for {head_ref}",
        body=f"Closes #{int(canonical_issue) + 1}",
        head_ref=head_ref,
    )
    assert "Pull request title/body/commit messages must not close non-canonical issues." in rejected


def test_issue353_recovery_branch_is_exact_and_reference_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "stage8-353-r0c-a2-3b-evaluation-lineage-v2"
    assert run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Activate evaluation lineage v2",
        body="Refs #353",
        head_ref=branch,
    ) == []
    closing = run_issue_link_check(
        tmp_path, monkeypatch, title="Activate evaluation lineage v2", body="Closes #353", head_ref=branch
    )
    assert "Pull request title/body/commit messages must use reference-only issue wording." in closing
    near_match = run_issue_link_check(
        tmp_path, monkeypatch, title="Near match", body="Refs #353", head_ref=branch + "-extra"
    )
    assert "Stage 8 pull requests must close the canonical Stage 8 issue" in "\n".join(near_match)


def test_issue424_master_program_branch_is_exact_and_reference_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "stage8-424-master-program-authority-prelog"
    assert run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Bind the master program proposal",
        body="Refs #424",
        head_ref=branch,
    ) == []
    closing = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Bind the master program proposal",
        body="Refs #424\nCloses #13",
        head_ref=branch,
    )
    assert "Pull request title/body/commit messages must use reference-only issue wording." in closing
    near_match = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Near match",
        body="Refs #424",
        head_ref=branch + "-extra",
    )
    assert "Stage 8 pull requests must close the canonical Stage 8 issue" in "\n".join(near_match)


def test_force_pull_request_guardrails_enforced_in_non_pull_request_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Fixes #44",
        body="Refs #44",
        head_ref="phase-1-closure-44-telemetry-hardening",
        event_name="push",
        force_pull_request_guards=True,
        changed_files=["backend/app/main.py"],
        commit_messages="",
    )
    assert "Pull request title/body/commit messages must use reference-only issue wording." in failures


def test_issue_39_matrix_validation_runs_even_without_pr_event_guardrails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_issue39_closure_plan(tmp_path, malformed_id="DUR-STAGE4-001")
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    guardrails.failures.clear()
    guardrails.check_issue_linked_pull_request()

    assert any(
        "Issue #39 matrix row must have 6 columns:" in failure for failure in guardrails.failures
    )


def test_push_context_without_pull_request_payload_when_force_enabled_fails_fast(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.setenv(guardrails.FORCE_PULL_REQUEST_GUARDRAILS_ENV, "1")

    def fake_run_git(args: list[str]) -> str:
        if args and args[0] == "log":
            return ""
        if args and args[0] == "diff":
            return ""
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)
    guardrails.failures.clear()
    guardrails.check_issue_linked_pull_request()
    assert "Pull request event payload is unavailable; cannot verify issue linkage." in guardrails.failures


def test_general_pull_request_requires_issue_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body="No linked issue.",
        head_ref="phase-1-closure-44-telemetry-hardening",
    )

    assert (
        "Pull request body must link an issue using reference-only wording such as Refs #<issue>."
    ) in failures


def test_nontrivial_pull_request_requires_completed_preflight_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec |  |  |  |  |  |  |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_process_critical_docs_are_nontrivial_and_require_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden process review evidence",
        body="Refs #60",
        head_ref="phase-1-closure-process-60-phf-002-medium-low-hardening",
        changed_files=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_completed_preflight_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_requires_status_impact_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body().replace(
            "## Status impact\n\n"
            "No repository-tracked status change is claimed by this PR. Routine post-merge facts go to "
            "PR/issue comments, with no successor status-only PR.\n\n",
            "",
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert guardrails.STATUS_IMPACT_SECTION_FAILURE in failures


def test_status_impacted_pull_request_rejects_no_status_change_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden process review evidence",
        body=completed_preflight_body(),
        head_ref="phase-1-closure-process-60-phf-002-medium-low-hardening",
        changed_files=["docs/CODEX_OPERATING_MODEL.md", "docs/STATUS.md"],
    )

    assert guardrails.STATUS_IMPACT_UNSUPPORTED_NO_CHANGE_FAILURE in failures


def test_status_impacted_pull_request_requires_same_pr_status_finalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "No repository-tracked status change is claimed by this PR. Routine post-merge facts go to "
        "PR/issue comments, with no successor status-only PR.",
        "`docs/STATUS.md` is finalized in this PR as the post-merge target state for the issue, "
        "including the next issue pointer. Routine post-merge facts go to PR/issue comments, "
        "with no successor status-only PR.",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden process review evidence",
        body=body,
        head_ref="phase-1-closure-process-60-phf-002-medium-low-hardening",
        changed_files=["docs/CODEX_OPERATING_MODEL.md", "docs/STATUS.md"],
    )

    assert failures == []


def test_status_impacted_pull_request_rejects_missing_status_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "No repository-tracked status change is claimed by this PR. Routine post-merge facts go to "
        "PR/issue comments, with no successor status-only PR.",
        "`docs/STATUS.md` is finalized in this PR as the post-merge target state for the issue, "
        "including the next issue pointer. Routine post-merge facts go to PR/issue comments, "
        "with no successor status-only PR.",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden process review evidence",
        body=body,
        head_ref="phase-1-closure-process-60-phf-002-medium-low-hardening",
        changed_files=["docs/CODEX_OPERATING_MODEL.md"],
    )

    assert guardrails.STATUS_IMPACT_MISSING_STATUS_FILE_FAILURE in failures


def test_status_impact_section_requires_comment_only_closeout_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "Routine post-merge facts go to PR/issue comments, with no successor status-only PR.",
        "Closeout is handled later.",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert guardrails.STATUS_IMPACT_CLOSEOUT_FAILURE in failures


def test_nontrivial_pull_request_rejects_missing_required_preflight_categories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/spec.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/matrix.md` | FM-1 | red test | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_example.py` | T-1 | `uv run pytest` | reviewer | pass | none |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


@pytest.mark.parametrize(
    "row_label",
    [
        "Failure matrix",
        "Review prompt set",
        "Stop rule / repeated blocker reset",
        "Skill/tool selection",
    ],
)
def test_nontrivial_pull_request_rejects_generic_governance_docs_for_pr_specific_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    row_label: str,
) -> None:
    valid_rows = normalize_preflight_rows_for_current_contract(
        f"| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        f"| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        f"| Failure matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        f"| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        f"| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        f"| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    generic_rows = "\n".join(
        (
            rebind_preflight_artifact_to_generic_governance_doc(row, row_label)
            for row in valid_rows.splitlines()
        )
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(generic_rows + "\n", normalize_rows=False),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_generic_preimplementation_matrix_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        f"| Invariant/failure matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}`",
        "| Invariant/failure matrix | `docs/ENGINEERING_PROCESS_RCA.md`",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


@pytest.mark.parametrize(
    ("row_label", "replacement"),
    [
        (
            "Review prompt set",
            f"| Review prompt set | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | PROMPT-1 | review done | reviewer | source | pass | tracked |",
        ),
        (
            "Stop rule / repeated blocker reset",
            f"| Stop rule / repeated blocker reset | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | STOP-1 | stop rule checked | reviewer | gate | pass | tracked |",
        ),
        (
            "Skill/tool selection",
            f"| Skill/tool selection | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | SKILL-1 | skills checked | reviewer | gate | pass | tracked |",
        ),
    ],
)
def test_nontrivial_pull_request_rejects_shallow_process_preflight_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    row_label: str,
    replacement: str,
) -> None:
    rows = "\n".join(
        replacement if row.startswith(f"| {row_label} |") else row
        for row in normalize_preflight_rows_for_current_contract(
            f"| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            f"| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            f"| Failure matrix | `{PR_SPECIFIC_PREFLIGHT_ARTIFACT}` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            f"| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            f"| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            f"| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ).splitlines()
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows + "\n", normalize_rows=False),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def rebind_preflight_artifact_to_generic_governance_doc(row: str, row_label: str) -> str:
    if row.startswith(f"| {row_label} |"):
        return row.replace(
            f"`{PR_SPECIFIC_PREFLIGHT_ARTIFACT}`",
            "`docs/ENGINEERING_PROCESS_RCA.md`",
        )
    return row


def test_nontrivial_pull_request_accepts_pr_template_preflight_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix / invariant matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests / old-behavior proof | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_partial_matrix_id_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_matrix_id_range_shorthand(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 through INV-3 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 INV-3 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 INV-3 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_matrix_ids_covered_across_evidence_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs for SRC-1 | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 SRC-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-2 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_invariant_id_covered_only_by_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 INV-2 | official docs for source and invariant | reviewer | source | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 INV-2 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


@pytest.mark.parametrize("status", ["tracked", "accepted"])
def test_nontrivial_pull_request_rejects_non_completed_preflight_statuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
            f"| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | {status} | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_directory_preflight_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preflight_url_with_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | https://example.com/todo | URL | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_unknown_reference_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | definitely-not-a-reference-type | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_file_line_artifact_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md:334` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md#invariant-to-test-matrix-template` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_mismatched_reference_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | source-URL | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | ADV-1 | subagent review | reviewer | source | pass | tracked |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_human_only_evidence_without_surface_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    body = completed_preflight_body(rows, human_rows="")
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_accepts_valid_human_only_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            rows,
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | reference-only final message with no issue-closing keyword accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert failures == []


def test_nontrivial_pull_request_rejects_na_human_only_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            human_rows=(
                "| N/A | No human-only surface for this PR | reviewer | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | next process PR |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_final_merge_surface_without_reference_only_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_human_only_evidence_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INT-1 | source interview | reviewer | source | pass | accepted |\n"
        "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | repo-file | SRC-1 | official docs | reviewer | source | pass | accepted |\n"
        "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | INV-1 HUMAN-1 | invariant-to-test matrix | reviewer | matrix | pass | tracked |\n"
        "| Tests | `tests/unit/test_guardrails_check.py` | repo-file | INV-1 | old behavior fails under break-test evidence | reviewer | test | pass | none |\n"
        "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | repo-file | INV-1 | invariant test gate | reviewer | gate | pass | tracked |\n"
        "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | repo-file | HUMAN-1 | final squash message inspected manually | reviewer | human-only | pass | accepted |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(
            rows,
            human_rows=(
                "| Final squash message | CI cannot inspect the final message before merge | repo owner | https://example.com/todo | accepted | before merge |\n"
            ),
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_missing_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().split("## Pre-implementation evidence", maxsplit=1)[0]
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preimplementation_comment_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "issue comment: https://example.com/todo",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_bare_issue_preimplementation_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_placeholder_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
        "pre-code timestamp: 2026-07-09T10:00",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def body_with_commit_order_preimplementation_rows(commit_order_marker: str) -> str:
    return (
        completed_preflight_body()
        .replace(
            "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-1",
            commit_order_marker,
        )
        .replace(
            "draft pr: https://github.com/imrohitagrawal/narratwin-ai/pull/60",
            commit_order_marker,
        )
        .replace(
            "issue comment: https://github.com/imrohitagrawal/narratwin-ai/issues/60#issuecomment-2",
            commit_order_marker,
        )
    )


def test_nontrivial_pull_request_accepts_verified_commit_order_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earlier = "1111111"
    later = "2222222"

    def fake_git_command_succeeds(args: list[str]) -> bool:
        if args == ["cat-file", "-e", f"{earlier}^{{commit}}"]:
            return True
        if args == ["cat-file", "-e", f"{later}^{{commit}}"]:
            return True
        return args == ["merge-base", "--is-ancestor", earlier, later]

    monkeypatch.setattr(guardrails, "git_command_succeeds", fake_git_command_succeeds)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body_with_commit_order_preimplementation_rows(f"commit order: {earlier} before {later}"),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE not in failures


def test_nontrivial_pull_request_rejects_reversed_commit_order_preimplementation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earlier = "1111111"
    later = "2222222"

    def fake_git_command_succeeds(args: list[str]) -> bool:
        if args[0] == "cat-file":
            return True
        return args == ["merge-base", "--is-ancestor", earlier, later]

    monkeypatch.setattr(guardrails, "git_command_succeeds", fake_git_command_succeeds)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body_with_commit_order_preimplementation_rows(f"commit order: {later} before {earlier}"),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_missing_validation_evidence_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().split("## Validation evidence", maxsplit=1)[0]
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    "command",
    [
        "make ci",
        "make security",
        "make dependency-audit",
        "make container-scan",
        "make secrets-scan",
        "make eval",
    ],
)
def test_nontrivial_pull_request_rejects_missing_runtime_validation_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    body = completed_preflight_body().replace(f"{command} -> passed\n", "")
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_guarded_pull_request_allows_phase1_stacked_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden stacked phase closure branch",
        body=completed_preflight_body().replace(
            "make quality -> passed",
            f"GITHUB_BASE_SHA={base_sha} make quality -> passed",
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        base_ref="phase-1-closure-39-execution-strategy",
        base_sha=base_sha,
        changed_files=["backend/app/main.py"],
    )

    assert all("explicitly reviewed stacked base" not in failure for failure in failures)


def test_guarded_pull_request_rejects_stacked_base_with_stray_sha_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden stacked phase closure branch",
        body=completed_preflight_body() + f"\nGITHUB_BASE_SHA={base_sha}\n",
        head_ref="phase-1-closure-44-telemetry-hardening",
        base_ref="phase-1-closure-39-execution-strategy",
        base_sha=base_sha,
        changed_files=["backend/app/main.py"],
    )

    assert (
        "Pull requests for guarded work must target main or an explicitly reviewed stacked base with exact "
        "GITHUB_BASE_SHA evidence in the PR body."
    ) in failures


@pytest.mark.parametrize(
    ("base_sha", "body_sha"),
    [
        ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", None),
        ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        ("not-a-sha", "not-a-sha"),
    ],
)
def test_guarded_pull_request_rejects_stacked_base_without_exact_sha_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    base_sha: str,
    body_sha: str | None,
) -> None:
    body = completed_preflight_body()
    if body_sha:
        body += f"\nGITHUB_BASE_SHA={body_sha} make quality -> passed\n"
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden stacked phase closure branch",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        base_ref="phase-1-closure-39-execution-strategy",
        base_sha=base_sha,
        changed_files=["backend/app/main.py"],
    )

    assert (
        "Pull requests for guarded work must target main or an explicitly reviewed stacked base with exact "
        "GITHUB_BASE_SHA evidence in the PR body."
    ) in failures


@pytest.mark.parametrize("base_ref", ["feature/unreviewed-base", "phase-1-closure-unreviewed-base", "phase-1-closure-"])
def test_guarded_pull_request_rejects_unreviewed_stacked_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    base_ref: str,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden stacked phase closure branch",
        body=completed_preflight_body(),
        head_ref="phase-1-closure-44-telemetry-hardening",
        base_ref=base_ref,
        changed_files=["backend/app/main.py"],
    )

    assert (
        "Pull requests for guarded work must target main or an explicitly reviewed stacked base with exact "
        "GITHUB_BASE_SHA evidence in the PR body."
    ) in failures


def test_nontrivial_pull_request_rejects_unrun_validation_evidence_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "not run: uv run pytest tests/unit/test_guardrails_check.py",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_hyphenated_not_run_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "not-run: uv run pytest tests/unit/test_guardrails_check.py -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_substring_validation_pass_terms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "make quality -> passed",
        "make quality -> unsuccessful",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_unrelated_validation_example_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "Example only: uv run pytest tests/unit/test_guardrails_check.py -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_inline_validation_example_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "uv run pytest tests/unit/test_guardrails_check.py -> passed (Example only)",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_zero_pass_validation_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    "invalid_line",
    [
        "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed; rerun -> passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 tests collected, 0 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 00 passed "
            "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123"
        ),
    ],
)
def test_nontrivial_pull_request_rejects_same_line_zero_pass_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        invalid_line,
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_zero_pass_before_later_valid_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed\n"
            "uv run pytest tests/unit/test_guardrails_check.py -> 75 passed"
        ),
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_later_zero_pass_validation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "uv run pytest tests/unit/test_guardrails_check.py -> 58 passed",
        (
            "uv run pytest tests/unit/test_guardrails_check.py -> 75 passed\n"
            "uv run pytest tests/unit/test_guardrails_check.py -> 0 passed"
        ),
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    ("valid_line", "invalid_line"),
    [
        ("make quality -> passed", "make quality-check -> passed"),
        (
            "python3 scripts/guardrails_check.py -> passed",
            "python3 scripts/guardrails_check.py.bak -> passed",
        ),
    ],
)
def test_nontrivial_pull_request_rejects_validation_command_suffix_false_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_line: str,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(valid_line, invalid_line)
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_requires_full_forced_pr_validation_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
        "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 -> passed",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


@pytest.mark.parametrize(
    "invalid_line",
    [
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "python3 scripts/guardrails_check.py NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 -> passed"
        ),
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH= "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
    ],
)
def test_nontrivial_pull_request_rejects_malformed_forced_pr_validation_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_line: str,
) -> None:
    body = completed_preflight_body().replace(
        (
            "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json "
            "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed"
        ),
        invalid_line,
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_rejects_placeholder_validation_event_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = completed_preflight_body().replace(
        "GITHUB_EVENT_PATH=/tmp/pr-event.json",
        "GITHUB_EVENT_PATH=/path/to/pr-event.json",
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=body,
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include validation evidence commands." in failures


def test_nontrivial_pull_request_requires_final_merge_residual_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = (
        "| Final squash message | CI cannot inspect final merge text; reviewer checks reference-only no issue-closing wording | repo owner | `docs/ENGINEERING_PROCESS_RCA.md` | accepted | before merge |\n"
    )
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=completed_preflight_body(human_rows=rows),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert PREFLIGHT_FAILURE in failures


def test_nontrivial_pull_request_rejects_preflight_without_invariant_test_id_overlap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | INV-1 | invariant-to-test matrix | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | T-1 | negative test; old behavior fails | reviewer | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | INV-1 | invariant test gate | reviewer | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_nontrivial_pull_request_rejects_preflight_without_old_behavior_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | `docs/ENGINEERING_PROCESS_RCA.md` | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | `docs/ENGINEERING_PROCESS_RCA.md` | INV-1 | invariant-to-test matrix | reviewer | pass | tracked |\n"
            "| Tests | `tests/unit/test_guardrails_check.py` | INV-1 | `uv run pytest` | reviewer | pass | none |\n"
            "| Docs/gates | `scripts/quality/check_phase1_closure_docs.py` | INV-1 | invariant test gate | reviewer | pass | tracked |\n"
            "| Adversarial review | `docs/ENGINEERING_PROCESS_RCA.md` | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


def test_nontrivial_pull_request_rejects_placeholder_preflight_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures = run_issue_link_check(
        tmp_path,
        monkeypatch,
        title="Harden local workflow evidence",
        body=(
            "Refs #44\n\n"
            "## Preflight evidence\n\n"
            "| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Intent/spec | https:// | INT-1 | source interview | reviewer | pass | accepted |\n"
            "| Source facts | https:// | SRC-1 | official docs | reviewer | pass | accepted |\n"
            "| Failure matrix | https:// | FM-1 | red test | reviewer | pass | tracked |\n"
            "| Tests | https:// | T-1 | `uv run pytest` | reviewer | pass | none |\n"
            "| Docs/gates | https:// | DOC-1 | marker gate | reviewer | pass | tracked |\n"
            "| Adversarial review | https:// | ADV-1 | subagent | reviewer | pass | tracked |\n"
        ),
        head_ref="phase-1-closure-44-telemetry-hardening",
        changed_files=["backend/app/main.py"],
    )

    assert "Non-trivial pull requests must include completed preflight evidence rows." in failures


@pytest.mark.parametrize(
    "changed_file",
    [
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "tests/unit/test_guardrails_check.py",
        ".github/CODEOWNERS",
        "scripts/ci/verify_branch_protection.py",
    ],
)
def test_new_governance_artifacts_require_status_updates(changed_file: str) -> None:
    guardrails.failures.clear()
    guardrails.check_status_tracking_rules([changed_file])

    assert "Repository-tracked stage/governance changes require docs/STATUS.md to be updated in the same PR." in guardrails.failures


def test_new_governance_artifacts_pass_when_status_is_updated() -> None:
    guardrails.failures.clear()
    guardrails.check_status_tracking_rules(
        [
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
            "docs/STATUS.md",
        ]
    )

    assert guardrails.failures == []


def test_exact_cut1_presenter_media_paths_do_not_require_an_adr() -> None:
    guardrails.failures.clear()
    guardrails.check_traceability_rules(
        [
            "frontend/public/demo/myra-synthetic-presenter.webp",
            "frontend/public/demo/raj-synthetic-presenter.webp",
            "docs/TRACEABILITY.md",
        ]
    )

    assert guardrails.failures == []


@pytest.mark.parametrize(
    "changed_file",
    [
        "frontend/public/demo/myra-synthetic-presenter.png",
        "frontend/public/demo/myra-synthetic-presenter.WEBP",
        "frontend/public/demo/myrа-synthetic-presenter.webp",
        "frontend/public/demo/future-synthetic-presenter.webp",
        "frontend/src/app/page.tsx",
        "Frontend/public/demo/myra-synthetic-presenter.webp",
        "frontеnd/public/demo/myra-synthetic-presenter.webp",
    ],
)
def test_nearby_or_architectural_frontend_paths_still_require_an_adr(changed_file: str) -> None:
    guardrails.failures.clear()
    guardrails.check_traceability_rules([changed_file, "docs/TRACEABILITY.md"])

    assert "Architecture-impacting changes require an ADR update under docs/ADR/." in guardrails.failures


def test_exact_presenter_media_mixed_with_frontend_code_still_requires_an_adr() -> None:
    guardrails.failures.clear()
    guardrails.check_traceability_rules(
        [
            "frontend/public/demo/myra-synthetic-presenter.webp",
            "frontend/src/app/page.tsx",
            "docs/TRACEABILITY.md",
        ]
    )

    assert "Architecture-impacting changes require an ADR update under docs/ADR/." in guardrails.failures


@pytest.mark.parametrize(
    "changed_file",
    [
        "src/service.py",
        "app/service.py",
        "backend/app/main.py",
        "infra/runtime.tf",
        "terraform/main.tf",
        "docker/Dockerfile",
        "docs/ARCHITECTURE.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/PORTABILITY_STRATEGY.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
        "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
        "docs/AI_SAFETY_AND_EVALUATION.md",
        "docs/THREAT_MODEL.md",
    ],
)
def test_non_frontend_architecture_prefixes_still_require_an_adr(changed_file: str) -> None:
    guardrails.failures.clear()
    guardrails.check_traceability_rules([changed_file, "docs/TRACEABILITY.md"])

    assert "Architecture-impacting changes require an ADR update under docs/ADR/." in guardrails.failures


def test_workflows_least_privilege_rejects_commented_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "quality.yml").write_text(
        "name: quality\n"
        "# permissions:\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)

    guardrails.failures.clear()
    guardrails.check_workflows_least_privilege()

    assert ".github/workflows/quality.yml is missing explicit least-privilege permissions." in guardrails.failures


def test_quality_gates_bootstraps_locked_environment_after_stdlib_policy_checks() -> None:
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "quality-gates.yml").read_text(
        encoding="utf-8"
    )
    guardrails = workflow.index("run: python scripts/guardrails_check.py")
    preflight = workflow.index("run: python -m scripts.governance_preflight_github")
    install_uv = workflow.index("python -m pip install uv==0.11.18")
    locked_sync = workflow.index("uv sync --frozen")
    quality = workflow.index('run: GITHUB_HEAD_REF="$NARRATWIN_HEAD_REF" make quality')

    assert guardrails < install_uv and preflight < install_uv < locked_sync < quality
    assert 'echo "$GITHUB_WORKSPACE/.venv/bin" >> "$GITHUB_PATH"' in workflow


def test_workflows_least_privilege_ignores_commented_write_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "quality.yml").write_text(
        "name: quality\n"
        "permissions:\n"
        "  contents: read\n"
        "# permissions: write-all\n"
        "# contents: write\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)

    guardrails.failures.clear()
    guardrails.check_workflows_least_privilege()

    assert guardrails.failures == []


def test_workflows_least_privilege_rejects_permission_decoys_outside_permissions_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "quality.yml").write_text(
        "name: quality\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    env:\n"
        "      permissions: read\n"
        "    steps:\n"
        "      - run: echo permissions:\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)

    guardrails.failures.clear()
    guardrails.check_workflows_least_privilege()

    assert ".github/workflows/quality.yml is missing explicit least-privilege permissions." in guardrails.failures


@pytest.mark.parametrize("write_scope", ["contents", "issues", "pull-requests"])
def test_workflows_least_privilege_rejects_write_scopes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    write_scope: str,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "quality.yml").write_text(
        "name: quality\n"
        "permissions:\n"
        f"  {write_scope}: write\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(guardrails, "ROOT", tmp_path)

    guardrails.failures.clear()
    guardrails.check_workflows_least_privilege()

    assert (
        f".github/workflows/quality.yml grants {write_scope}: write. Use read or none unless a write "
        "permission is explicitly required."
    ) in guardrails.failures


def test_pr_branch_push_changed_files_uses_merge_base_not_previous_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "phase-1-closure-39-context0-production-durability")
    monkeypatch.setenv("GITHUB_BASE_SHA", "previous-pushed-commit")
    monkeypatch.setenv("GITHUB_HEAD_SHA", "current-head")
    calls: list[list[str]] = []

    def fake_run_git(args: list[str]) -> str:
        calls.append(args)
        if args == ["merge-base", "origin/main", "current-head"]:
            return "pr-merge-base"
        if args == ["diff", "--name-only", "pr-merge-base", "current-head"]:
            return "docs/STATUS.md\nscripts/guardrails_check.py"
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)

    assert guardrails.changed_files() == ["docs/STATUS.md", "scripts/guardrails_check.py"]
    assert ["rev-parse", "--verify", "previous-pushed-commit^{commit}"] not in calls


def test_main_push_changed_files_keeps_previous_commit_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_BASE_SHA", "previous-main")
    monkeypatch.setenv("GITHUB_HEAD_SHA", "current-main")

    def fake_run_git(args: list[str]) -> str:
        if args == ["rev-parse", "--verify", "previous-main^{commit}"]:
            return "previous-main"
        if args == ["merge-base", "previous-main", "current-main"]:
            return "previous-main"
        if args == ["diff", "--name-only", "previous-main", "current-main"]:
            return "docs/STATUS.md"
        return ""

    monkeypatch.setattr(guardrails, "run_git", fake_run_git)

    assert guardrails.changed_files() == ["docs/STATUS.md"]


def test_main_push_rejects_direct_push_to_main_without_pr_merge_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"head_commit": {"id": "abc123"}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr(guardrails, "is_merged_pull_request_merge_push", lambda _sha: False)

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert "Direct push to main detected. All work must go through issue + branch + PR." in guardrails.failures


def test_main_push_allows_merged_pr_push_to_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"head_commit": {"id": "abc123"}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr(guardrails, "is_merged_pull_request_merge_push", lambda _sha: True)

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert guardrails.failures == []


def test_main_push_without_event_payload_fails_push_merge_classification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert "Could not read push event payload; cannot verify whether this main push came from a merged PR." in guardrails.failures


def test_main_push_rejects_malformed_payload_without_head_sha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"not_head_commit": "broken"}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert "Push payload is missing a head commit SHA; cannot verify whether this main push came from a merged PR." in guardrails.failures


def test_main_push_uses_after_sha_when_head_commit_sha_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"after": "after-sha"}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setattr(
        guardrails,
        "is_merged_pull_request_merge_push",
        lambda sha: sha == "after-sha",
    )

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert guardrails.failures == []


def test_main_push_without_github_token_treated_as_direct_push(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"head_commit": {"id": "abc123"}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    guardrails.failures.clear()
    guardrails.check_no_direct_main_push()

    assert "Direct push to main detected. All work must go through issue + branch + PR." in guardrails.failures


def issue280_public_safe_pr_a_body(extra: str = "") -> str:
    return (
        "Refs #280\n"
        "Refs #249\n\n"
        "PR A does not implement runtime product behavior.\n"
        "No provider setup.\n"
        "No paid spend.\n"
        "No hosted deployment.\n"
        "No public demo.\n"
        "No production readiness.\n"
        "No cloned identity runtime.\n"
        "No real media.\n"
        f"{extra}"
    )


def test_issue280_pr_a_accepts_reference_only_public_safe_body() -> None:
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        issue280_public_safe_pr_a_body(),
        issue280_public_safe_pr_a_body(),
    )

    assert failures == []


def test_issue280_pr_a_rejects_closing_issue_280() -> None:
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        "Closes #280\n" + issue280_public_safe_pr_a_body(),
        issue280_public_safe_pr_a_body(),
    )

    assert guardrails.ISSUE_280_REFERENCE_ONLY_FAILURE in failures


def test_issue280_pr_a_rejects_closing_issue_249() -> None:
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        "Fixes #249\n" + issue280_public_safe_pr_a_body(),
        issue280_public_safe_pr_a_body(),
    )

    assert guardrails.ISSUE_249_REFERENCE_ONLY_FAILURE in failures


def test_issue280_pr_a_rejects_runtime_completion_claim() -> None:
    body = issue280_public_safe_pr_a_body("Runtime implementation complete.\n")
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        body,
        body,
    )

    assert guardrails.ISSUE_280_RUNTIME_COMPLETION_FAILURE in failures


def test_issue280_pr_a_rejects_runtime_completion_claim_in_visible_surface() -> None:
    body = issue280_public_safe_pr_a_body()
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        "Title says runtime implementation complete\n" + body,
        body,
    )

    assert guardrails.ISSUE_280_RUNTIME_COMPLETION_FAILURE in failures


def test_issue280_pr_a_requires_public_safe_non_goals() -> None:
    body = issue280_public_safe_pr_a_body().replace("No paid spend.\n", "")
    failures = guardrails.issue_280_pr_a_failures(
        guardrails.ISSUE_280_PR_A_BRANCH,
        body,
        body,
    )

    assert guardrails.ISSUE_280_PUBLIC_SAFE_BOUNDARY_FAILURE in failures
