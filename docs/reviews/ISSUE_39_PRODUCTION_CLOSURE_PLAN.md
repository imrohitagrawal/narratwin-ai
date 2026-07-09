# Issue #39 Production Closure Plan (Context 0)

## Objective

Create a durable, reviewed production-closure contract for GitHub issue `#39` that is reusable by later contexts and PRs.

- It is a context-0 planning contract only.
- It defines production durability and monitoring requirements before any durable runtime implementation starts.
- It explicitly excludes all runtime product/database/provider/monitoring implementations.

## Current State (as of 2026-07-09)

- `#39` remains open and is the remaining Phase 1 P1 production blocker.
- Current implementation for `#39` is local/mock only:
  - optional local JSON snapshots for Stage 4 project/document/run/RAG state,
  - local optional restart recovery for Stage 6 multilingual artifacts,
  - local optional Stage 7 artifact/render metadata persistence,
  - `/api/v1/ops/status` exposing bounded local posture metadata.
- Open production-grade gaps are:
  - ACID/CAS durable metadata,
  - production idempotency semantics,
  - cross-worker job leases,
  - committed outbox side effects,
  - production migrations,
  - durable Stage 4/6/7 replay state,
  - backup/restore, monitoring, SLO/error-budget thresholds, alerts, first-hour watch with follow-up checkpoints, rollback comms,
  - consent/provenance/provider release controls.
  - deletion/erasure semantics and untrusted-input handling across durable/replayed artifacts.
- `Context 0` does not close `#39`; it defines the contract only.

## Non-Goals

- DB schema, migrations, backend runtime, provider runtime, worker runtime, frontend runtime, or monitoring runtime implementation.
- Backup tooling, dashboard tooling, alert integrations, or alert runbooks implemented in code in this context.
- Production release, production deployment, or release-tag activity.
- Any implementation that changes behavior outside durability and monitoring closure planning.

## PostgreSQL-Compatible Production Storage Recommendation

### Recommendation

Use PostgreSQL for production durability metadata.

### Rationale

- ACID + transaction isolation supports CAS semantics for idempotent write flows.
- Row locks support deterministic lease ownership and re-assignment logic.
- Constraint and uniqueness enforcement aligns with duplicate protection and request identity semantics.
- JSONB supports flexible metadata (evidence refs, consent provenance, run metadata) while preserving indexed relational joins.
- Operational maturity for backup, restore, retention, and observability in production.
- Existing architecture documents already treat project/artefact state as relational state with explicit transitions.

Local/test defaults (`in-memory`, local JSON, staged files, local mocks) remain allowed as defaults for non-production contexts, but they are explicitly documented as non-production durability.

## Context Breakdown

1. **Context 0 (this context):** Contract-only planning for durability/monitoring; matrix and child decomposition only.
2. **Context 1:** Storage ADR and schema blueprint, durable lease/state transition design, and migration ordering plan.
3. **Context 2:** Durable state and outbox implementation for production metadata and rerun semantics.
4. **Context 3:** Monitoring stack rollout, metrics, alerts, first-hour watch with follow-up checkpoints, and operations runbook.
5. **Context 4:** Final closure evidence sweep, cross-context reconciliation, and final `#39` disposition decision.

## Master Evidence Matrix

All IDs are mandatory. `Status` is machine-relevant and may be changed from
`Open` to `Closed` only in the final disposition PR after the row has a concrete
artifact reference, reviewer, owner, validation command or human-only evidence
record, and residual-risk decision.

| ID | Requirement | Evidence target | Owner | Minimum evidence contract | Status |
|---|---|---|---|---|---|
| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |
| `DUR-IDEMP-001` | Production idempotency semantics | Replay-safe request identity and dedupe behavior across retries and worker failover | Runtime/state + Security | Idempotency envelope contract including terminal/error/replay state transitions and failure dedupe proofs | Open |
| `DUR-STAGE4-001` | Durable Stage 4 project/document/RAG/run graph | Durable project/document/chunk/run/eval graph and resume behavior | Storage + API | Entity/state graph contract with at-least-once execution and idempotent consumers; no exactly-once side-effect claim | Open |
| `DUR-LEASE-001` | Cross-worker job leases | Lease acquisition, heartbeat renewal, expiry, reclaim, and stale-writer fencing | Runtime/state | Lease state machine with monotonic fencing token/epoch, stale-owner prevention, and ownership transfer proof | Open |
| `DUR-OUTBOX-001` | Committed outbox side effects | Outbox transaction boundaries and side-effect dispatch contract | Runtime/integrations | Same-transaction outbox write with state change; at-least-once dispatch plus idempotent consumer policy | Open |
| `DUR-STAGE6-001` | Durable multilingual artifact replay | Production replay of translated scripts/subtitles and derived assets | Stage 6 | Replay contract with source-run linkage, checksum-based dedupe, and deterministic artifact provenance | Open |
| `DUR-STAGE7-001` | Durable render/artifact/provenance state | Render status, artifact records, consent/disclosure binding | Stage 7 | Persistent render/provenance record contract and synthetic-media release check points | Open |
| `DUR-MIG-001` | Migrations | Versioned schema evolution, compatibility, and forward-only rollback safety | Platform/storage | Expand/contract migration plan with backward-compatible code windows, forward repair, and no mandatory down-migration claim | Open |
| `DUR-ROLLBACK-001` | Technical rollback compatibility | Code rollback against migrated production metadata | Platform + Release | Evidence that the previous deploy can run against the expanded schema or that rollback is blocked until forward repair completes | Open |
| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |
| `OPS-METRICS-001` | Production metrics | Queue, lease, idempotency, outbox, and restore metrics | Observability | Reviewer-approved metric catalog and scrape/query mapping to each operational failure mode | Open |
| `OPS-SLO-001` | Production SLOs and error budgets | Threshold bindings for queue lag, lease staleness, outbox age/backlog, restore RTO/RPO, rollback, and watch escalation | SRE/Ops + Release | Reviewed SLO/error-budget catalog with alert threshold mapping and rollback/watch escalation bindings | Open |
| `OPS-ALERT-001` | Dashboards and alerts | Severity routing, alert ownership, and paging runbook | SRE/Ops | Dashboard + alert matrix with tested routing, evidence loop, and acknowledgment rules | Open |
| `OPS-WATCH-001` | First-hour watch with follow-up checkpoints | Triage cadence and owner communication for the first 60 minutes, plus explicit 120/180-minute follow-up checkpoints | Release/Operations | Active watch log template, handoff rules, timeout actions, rollback escalation threshold | Open |
| `OPS-ROLLBACK-001` | Rollback communications | Pre/post rollback comms and ownership confirmation | Release/Operations | Freeze-window criteria, comms template, and required evidence captures | Open |
| `MEDIA-CONSENT-001` | Consent capture | Affirmative consent record for synthetic-media generation | Security/Privacy | Consent schema with actor, timestamp, consent text/version, artifact refs, source-run binding, scope, and audit retention | Open |
| `MEDIA-REVOKE-001` | Consent revocation behavior | Revocation, takedown, retention, and already-published artifact handling | Security/Privacy + Release | Revocation decision table covering retain, block replay, takedown, and customer/user communication paths | Open |
| `MEDIA-PROVENANCE-001` | Provenance binding | Durable source-run, prompt, provider, artifact checksum, cloned-identity denial provenance, and disclosure lineage | Security/Privacy + Media | Provenance schema and replay proof linking rendered artifacts to source run, consent record, and identity/likeness denial checks | Open |
| `MEDIA-DISCLOSURE-001` | Synthetic-media disclosure | Durable disclosure text/version binding for exports and public-use posture | Security/Privacy + Release | Disclosure versioning record and validation that artifacts carry the expected disclosure state | Open |
| `PROVIDER-POSTURE-001` | Provider release posture | External provider legal, license, network, egress, key, and rollout controls | Security/Privacy + Platform | Provider release checklist with legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and rollback disablement evidence | Open |
| `SEC-RETENTION-001` | Sensitive metadata retention/deletion/redaction | PII/provenance/consent data in PostgreSQL, backups, logs, metrics, and restored environments | Security/Privacy + Ops | Data-class table with encryption, redaction, retention, deletion/erasure scope, tombstone vs hard-delete policy, backup expiry, restore re-delete behavior, audit retention exceptions, access control, replay/export blocking after deletion, and restore-disclosure requirements | Open |
| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted | Security/Privacy + Runtime + Ops | Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content | Open |
| `GOV-SCOPE-001` | Scope separation from small governance/process cleanup | Context 0 does not absorb child PRs or remaining blockers | Governance | Documented issue split with separate issue/PR mapping for every remaining blocker, plus reviewer signoff before scope extension | Open |

## Child Issue / PR Mapping Template

All follow-on work must map every matrix ID to one or more child issues/PRs.

| Child Issue / PR | Domain | Required Deliverables | Matrix IDs | Owner | Required Evidence |
|---|---|---|---|---|---|
| `ISSUE-39-1` (template) | Postgres durability architecture | PostgreSQL durability ADR + production schema boundary | DUR-ACID-001, DUR-STAGE4-001 | Architecture | ADR + storage design checklist |
| `ISSUE-39-2` (template) | Idempotency and leasing | Request identity, conflict rules, lease state machine, outbox skeleton contract | DUR-IDEMP-001, DUR-LEASE-001, DUR-OUTBOX-001 | Runtime | Contract tests and invariants |
| `ISSUE-39-3` (template) | Migrations | Versioned expand/contract migration sequence and code-rollback posture | DUR-MIG-001, DUR-ROLLBACK-001, DUR-STAGE6-001, DUR-STAGE7-001 | Storage + API | Migration plan + backward-compatible deployment window proof |
| `ISSUE-39-4` (template) | Backup and restore | RPO/RTO targets, backup design, restore drill evidence | DUR-RESTORE-001, OPS-METRICS-001, OPS-SLO-001 | Operations | Runbook + drill log + evidence bundle |
| `ISSUE-39-5` (template) | Monitoring and alerts | Dashboard schema, SLO/error-budget thresholds, alert routing, first-hour watch SOP with 120/180-minute follow-up checkpoints | OPS-METRICS-001, OPS-SLO-001, OPS-ALERT-001, OPS-WATCH-001 | Observability | Dashboard definition + alert tests + watch evidence |
| `ISSUE-39-6` (template) | Rollback + media/privacy + scope | Rollback comms, consent/provenance schema, provider posture, retention/deletion/redaction, untrusted-input handling, governance scope gate | MEDIA-CONSENT-001, MEDIA-REVOKE-001, MEDIA-PROVENANCE-001, MEDIA-DISCLOSURE-001, PROVIDER-POSTURE-001, SEC-RETENTION-001, SEC-UNTRUSTED-001, OPS-ROLLBACK-001, GOV-SCOPE-001 | Security + Release + Governance | Signed schema, comms evidence, scope gate |

## Human-Only Gates

- Matrix coverage is complete when every required ID has a mapped child issue/PR owner and a planned evidence artifact.
- Template rows do not satisfy closure; final disposition requires real child issue/PR numbers and artifact links for every row.
- PostgreSQL production durability and lock semantics must be reviewed and accepted by architecture/reliability reviewers before migration execution.
- Rollback/freeze decision criteria and watch comms must be human-reviewed before any production deployment plan is approved.
- Consent/provenance and provider release posture must be reviewed by security/privacy before any non-local synthetic-media release path can go active.
- `#39` cannot be closed by branch name, PR title/body text, or commit text until all matrix rows in this file are marked `Closed` by review evidence.

## Row Closure Record Schema

Every final matrix row must have a row-level closure record before its status can
change to `Closed`. The record must include:

- matrix ID,
- child issue and PR number,
- concrete same-repository child issue URL and PR URL,
- artifact reference,
- validation command, CI run, drill log, or human-only evidence reference,
- owner,
- reviewer,
- residual-risk decision,
- timestamp or merge commit,
- explicit reason the evidence satisfies the row.

Future final-disposition PRs must fill this table. Context 0 intentionally
leaves it empty because all matrix rows are `Open`.

## Row Closure Records

| Matrix ID | Child issue / PR | Artifact reference | Validation or human evidence | Owner | Reviewer | Residual-risk decision | Timestamp / merge commit | Satisfies row because |
|---|---|---|---|---|---|---|---|---|

The repository guardrail checks PR title, body, and commit messages for issue
`#39` closing keywords. A final disposition PR can use those keywords only after
all rows in the Master Evidence Matrix are already marked `Closed`.

## Final Closure Criteria

Final disposition for `#39` is eligible only when all IDs below have evidence references (repo docs/PRs/tests/incident logs) and all required human gates above are signed:

`DUR-ACID-001`, `DUR-IDEMP-001`, `DUR-STAGE4-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001`, `DUR-STAGE6-001`, `DUR-STAGE7-001`, `DUR-MIG-001`, `DUR-ROLLBACK-001`, `DUR-RESTORE-001`, `OPS-METRICS-001`, `OPS-SLO-001`, `OPS-ALERT-001`, `OPS-WATCH-001`, `OPS-ROLLBACK-001`, `MEDIA-CONSENT-001`, `MEDIA-REVOKE-001`, `MEDIA-PROVENANCE-001`, `MEDIA-DISCLOSURE-001`, `PROVIDER-POSTURE-001`, `SEC-RETENTION-001`, `SEC-UNTRUSTED-001`, `GOV-SCOPE-001`

Closure is incomplete until:
- every local/test default artifact remains marked non-production in release-facing documentation,
- all non-local synthetic-media output paths are explicitly tied to provenance/consent/provider-posture review,
- all durable/replayed content remains treated as untrusted input with validation, output encoding, log redaction, restore-time revalidation, and replay/export safety evidence,
- paid/external providers remain mock/local by default outside production, real keys stay out of local/dev/test/CI, production enablement is explicit, egress is deny-by-default, and rollback disablement is proven,
- deletion/erasure behavior is proven for source uploads, generated artifacts, provider/model outputs, consent/provenance records, logs/metrics, backups, restored environments, and replay/export blocking after deletion,
- cross-worker and replay semantics are proven with operational evidence,
- SLO/error-budget thresholds bind queue, lease, outbox, restore, rollback, and watch escalation evidence,
- backup/restore and first-hour watch plus follow-up checkpoints are executed as a recorded drill.
- every row has a final row-level closure record with owner, reviewer, concrete same-repository child issue/PR URLs, artifact reference, validation result, and residual-risk decision.

## Explicit Scope Separation

This context is limited to `#39` production durability and monitoring closure planning.

- It does not absorb small process/governance cleanup unless that cleanup directly blocks one matrix row.
- Governance process leftovers continue through existing process-hardening mechanisms.

## Required Adversarial Reviews

- Architecture/state review: completed. Findings to close in child contexts:
  - fix table parseability for `OPS-WATCH-001`,
  - map `GOV-SCOPE-001` to ownership in `ISSUE-39-6`.
- Ops/release review: completed. Findings to close:
  - add concrete metric catalog, dashboard query mapping, and alert-action tests,
  - define first-hour watch evidence log, follow-up checkpoints, and escalation thresholds,
  - add explicit rollback comms protocol and freeze-window rules.
- Security/privacy review: completed. Findings to close:
  - define consent/provenance record schema (actor, timestamp, artifact refs, revocation),
  - define provider release posture gates,
  - add retention/redaction requirements for backups, logs, consent/provenance fields.
- Governance/false-pass review: completed. Findings to close:
  - normalize matrix formatting,
  - resolve any one-to-one coverage ambiguity in child mapping.

## Sub-agent / Reviewer Prompts (if further tooling is unavailable)

Keep these prompts and evidence in `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` if automation is rerun.

1. Architecture/state review prompt: confirm transactional boundaries, lease states, migration ordering, and outbox invariants.
2. Ops/release review prompt: confirm metric catalog, dashboard, alert routing, watch protocol, and rollback evidence.
3. Security/privacy review prompt: confirm consent/provenance schema, provider posture gates, and backup/restore data handling.
4. Governance/false-pass review prompt: confirm no scope bleed into unrelated process cleanup and confirm all matrix IDs are represented in child work.

## Context 0 Status

- Artifact created: `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- Purpose: reusable production-closure contract for `#39`.
- Context 0 does **not** close `#39`.
