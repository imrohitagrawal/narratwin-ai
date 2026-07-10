import importlib.util
import json
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
ISSUE_39_REFERENCE_ONLY_FAILURE = "Issue #39 pull requests must use reference-only wording and must not auto-close #39."
PREFLIGHT_FAILURE = "Non-trivial pull requests must include completed preflight evidence rows."
PR_SPECIFIC_PREFLIGHT_ARTIFACT = "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
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
                    "base": {"ref": "main"},
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

    assert "Repository-tracked stage/governance changes require docs/STATUS.md to be updated." in guardrails.failures


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
