# Issue #39 Production Closure Plan (Context 0)

## Objective

Create a durable, reviewed production-closure contract for GitHub issue `#39` that is reusable by later contexts and PRs.

- It is a context-0 planning contract only.
- It defines production durability and monitoring requirements before any durable runtime implementation starts.
- It explicitly excludes all runtime product/database/provider/monitoring implementations.

## Current State (as of 2026-07-10)

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
- Issue `#66` is the completed planning context for Context 2 (`DUR-IDEMP-001`,
  `DUR-LEASE-001`, `DUR-OUTBOX-001`), closed through PR `#76`; runtime
  implementation remains deferred.
- Issue `#67` is the completed planning context for migrations and rollback
  compatibility (`DUR-MIG-001`, `DUR-ROLLBACK-001`, plus optional artifact-state
  compatibility for `DUR-STAGE6-001` and `DUR-STAGE7-001`), closed through PR
  `#77`.
- Issue `#68` is the completed planning context for backup/restore drill planning
  (`DUR-RESTORE-001`, `OPS-METRICS-001`, `OPS-SLO-001`), closed through PR
  `#78`; runtime backup tooling and restore execution remain deferred.
- Issue `#69` is the completed planning context for operations monitoring and first-hour watch
  for issue `#39` (`OPS-METRICS-001`, `OPS-SLO-001`, `OPS-ALERT-001`,
  `OPS-WATCH-001`), closed through PR `#79`.
- Issue `#70` is the completed planning context for rollback/media/privacy,
  provider posture, retention/deletion/erasure planning, and untrusted durable/replayed
  input handling, closed through PR `#80`. No runtime/product implementation
  was authorized in that context.

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
3. **Context 2:** Durable state transitions and outbox contracts for production
   metadata plus rerun semantics. This context is planning-only in Issue `#66`.
4. **Context 3:** Migrations and rollback compatibility planning for `DUR-MIG-001`,
   `DUR-ROLLBACK-001`, and artifact-state sequencing for `DUR-STAGE6-001` / `DUR-STAGE7-001`.
5. **Context 4:** Backup and restore drill planning with durability artifacts,
   RTO/RPO targets, restore integrity checks, metrics/events contracts, and escalation runbook.
6. **Context 5:** Operations monitoring, SLO/error-budget, alert-routing, and first-hour watch planning for Issue `#69`.
7. **Context 6:** Rollback communications, media/privacy/provider/revocation/release controls, retention/deletion/erasure planning, and untrusted durable/replayed input handling for Issue `#70`.

## Context 1: PostgreSQL Durability ADR and Schema Boundary

Context 1 is now assigned to Issue `#65` and is implemented as the following:

- Production durability boundary decision and contract: `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- Non-production artifacts remain in local file state and do not claim production
  semantics.
- Open/terminal/error transitions and replay-safe conflict handling for
  `project`, `document`, `chunk`, `run`, and `evaluation` are defined as a
  pre-implementation handoff.

Boundary split for this design:

| Surface | In-production durable boundary | Deferred/outside this context |
|---|---|---|
| `project` metadata | ✅ | - |
| `document` metadata | ✅ | Raw upload/source document content |
| `chunk` indices | ✅ | Provider/raw chunk payload binaries |
| `run` state graph | ✅ | Provider/model outputs and transcripts |
| `evaluation` records | ✅ | Generated scripts/subtitles/audio/video artifacts |
| Migration DDL and rollout | ❌ | Migration/order scripts and execution |

Approval requirement: this context is approved for architecture handoff only and
must not introduce runtime implementation, SQL DDL execution, or API behavior
change in this issue.

## Master Evidence Matrix

All IDs are mandatory. `Status` is machine-relevant and may be changed from
`Open` to `Closed` only in the final disposition PR after the row has a concrete
artifact reference, reviewer, owner, validation command or human-only evidence
record, and residual-risk decision.

| ID | Requirement | Evidence target | Owner | Minimum evidence contract | Status |
|---|---|---|---|---|---|
| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |
| `DUR-STAGE4-001` | Durable Stage 4 project/document/RAG/run graph | Durable project/document/chunk/run/eval graph and resume behavior | Storage + API | Entity/state graph contract with at-least-once execution and idempotent consumers; no exactly-once side-effect claim | Open |
| `DUR-IDEMP-001` | Production idempotency semantics | Replay-safe request identity and dedupe behavior across retries and worker failover | Runtime/state + Security | Canonical `(operation_id, scope)` idempotency key, payload-hash conflict guard, terminal replay behavior, transient recovery state, stale-owner rejection, plus Issue `#66` ADR/evidence table | Open |
| `DUR-LEASE-001` | Cross-worker job leases | Lease acquisition, heartbeat renewal, expiry, reclaim, and stale-writer fencing | Runtime/state | Lease state machine with acquire/renew/expiry, monotonic fencing token, ownership transfer, stale-writer rejection, plus Issue `#66` ADR/evidence table | Open |
| `DUR-OUTBOX-001` | Committed outbox side effects | Outbox transaction boundaries and side-effect dispatch contract | Runtime/integrations | Same-transaction state/event write, outbox row envelope, explicit dispatch transitions, at-least-once retry, idempotent consumer policy, plus Issue `#66` ADR/evidence table | Open |
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
| `ISSUE-39-1` | Postgres durability architecture | PostgreSQL durability ADR + production schema boundary (`docs/ADR/0008-postgresql-durability-schema-boundary.md`) | DUR-ACID-001, DUR-STAGE4-001 | Architecture | ADR + schema boundary design checklist |
| `#66` | Idempotency, leases, and outbox context2 decomposition for production durability | Replay-safe idempotency contract, lease fencing/ownership transfer contract, outbox-at-least-once contract, and one-to-one test/evidence matrix mapping | DUR-IDEMP-001, DUR-LEASE-001, DUR-OUTBOX-001 | Runtime | Advisory-only ADR + planned contract tests for implementation context |
| `#67` | Migrations and rollback compatibility decomposition for production durability | Versioned expand/contract migration strategy, migration ordering constraints, rollback safety posture, and optional artifact-state compatibility planning for Stage 6/Stage 7 | DUR-MIG-001, DUR-ROLLBACK-001, DUR-STAGE6-001, DUR-STAGE7-001 | Runtime + Storage | Advisory-only migration ADR + planned execution-handoff matrix mapping |
| `#68` | Backup and restore drill planning and context handoff | Backup scope boundaries, exclusion policy, restore integrity checks, RTO/RPO targets, evidence pack definitions, and escalation protocol | DUR-RESTORE-001, OPS-METRICS-001, OPS-SLO-001 | Operations | `docs/ADR/0011-context4-backup-restore-drill.md` + row-specific planned evidence IDs |
| `#69` | Operations monitoring and first-hour watch planning | Metric catalog, SLO/error-budget thresholds, alert routing, watch checkpoints, escalation, and rollout handoff with deferred runtime implementers | OPS-METRICS-001, OPS-SLO-001, OPS-ALERT-001, OPS-WATCH-001 | Observability/Operations | `docs/ADR/0012-context5-metrics-slos-watch.md` + stable planned evidence IDs |
| `#70` | Rollback + media/privacy + provider posture + scope | Rollback comms, consent/revocation/provenance schema, provider release posture, retention/deletion/redaction, and untrusted-input handling | MEDIA-CONSENT-001, MEDIA-REVOKE-001, MEDIA-PROVENANCE-001, MEDIA-DISCLOSURE-001, PROVIDER-POSTURE-001, SEC-RETENTION-001, SEC-UNTRUSTED-001, OPS-ROLLBACK-001, GOV-SCOPE-001 | Security + Release + Governance | Planning-only evidence anchors in this issue file plus stable IDs (`CTX6-*`) |

## Issue #66 (Context 2) Status and Evidence Mapping

### Matrix planning annotations for `DUR-IDEMP-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001`

- Matrix status remains exactly `Open` for `DUR-IDEMP-001`, `DUR-LEASE-001`,
  and `DUR-OUTBOX-001`.
- Issue `#66` is closed for context planning and was completed in PR `#76`; this file records
  planning-only contracts and test hypotheses. No runtime closure evidence is
  added yet.

### One-to-one test/evidence row mappings

| Matrix ID | Issue #66 evidence artifact | Planned deterministic evidence row |
|---|---|---|
| `DUR-IDEMP-001` | `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md` (Replay-safe idempotency section) | `CTX2-IDEMP-EVID-001`: planned tests `test_context2_idempotency_replays_terminal_success`, `test_context2_idempotency_replays_terminal_error`, `test_context2_idempotency_rejects_payload_hash_conflict`, and `test_context2_idempotency_recovery_rejects_stale_owner`. |
| `DUR-LEASE-001` | `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md` (Lease ownership section) | `CTX2-LEASE-EVID-001`: planned tests `test_context2_lease_rejects_stale_writer_epoch`, `test_context2_lease_renew_preserves_epoch_and_extends_expiry`, `test_context2_lease_transfer_increments_epoch`, and `test_context2_lease_expiry_blocks_stale_owner_commit`. |
| `DUR-OUTBOX-001` | `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md` (Outbox contract section) | `CTX2-OUTBOX-EVID-001`: planned tests `test_context2_outbox_writes_state_and_event_atomically`, `test_context2_outbox_redelivery_is_at_least_once`, and `test_context2_outbox_consumer_dedupes_duplicate_delivery`. |

All Context 2 runtime behavior is explicitly deferred. Local/test provider posture
and paid-provider activation policy remain unchanged.

## Issue #67 (Context 3) Status and Evidence Mapping

### Matrix planning annotations for `DUR-MIG-001` and `DUR-ROLLBACK-001`

- Matrix status remains exactly `Open` for `DUR-MIG-001` and `DUR-ROLLBACK-001`.
- Issue `#67` is closed for context planning and was completed in PR `#77`; this context is
  advisory-only and does not authorize migration execution.
- Optional Stage 6 / Stage 7 compatibility planning is limited to artifact-shape
  compatibility planning for migration ordering and rollback safety.

### One-to-one test/evidence row mappings

| Matrix ID | Issue #67 evidence artifact | Planned deterministic evidence row |
|---|---|---|
| `DUR-MIG-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Expand/contract strategy and schema-versioning section) | `CTX3-MIG-EVID-001`: planned tests `test_context3_expand_then_contract_strategy`, `test_context3_expand_is_backward_compatible`, and `test_context3_migration_ordering_with_idempotency_lease_outbox`. |
| `DUR-ROLLBACK-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Rollback and forward-repair section) | `CTX3-ROLLBACK-EVID-001`: planned tests `test_context3_backward_compatible_window_enforced`, `test_context3_rollback_blocks_when_unsafe_without_repair`, and `test_context3_forward_repair_restores_rollback_compatibility`. |
| `DUR-STAGE6-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Optional Stage 6 compatibility section) | `CTX3-STAGE6-EVID-001`: planned test `test_context3_stage6_artifact_state_readers_tolerate_schema_version_gap`. |
| `DUR-STAGE7-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Optional Stage 7 compatibility section) | `CTX3-STAGE7-EVID-001`: planned test `test_context3_stage7_artifact_state_readers_tolerate_schema_version_gap`. |

### Planning-only runtime posture for Issue #67

- Runtime migration execution (migration runners, schema upgrades, lock-table migration
  scripts, data backfills, and downgrade scripts) is explicitly deferred to later
  production implementation contexts.
- ADRs, planning matrices, and branch allowlist/checker updates are the only artifacts
  added in this context.

## Issue #68 (Context 4) Status and Evidence Mapping

### Matrix planning annotations for `DUR-RESTORE-001`, `OPS-METRICS-001`, and `OPS-SLO-001`

- Matrix status remains exactly `Open` for `DUR-RESTORE-001`, `OPS-METRICS-001`, and
  `OPS-SLO-001`.
- Issue `#68` is closed for context planning and was completed in PR `#78`;
  this context records context handoff artifacts and evidence pack contracts only.
  Runtime implementation remains deferred.
- Runtime backup tooling, restore automation, storage operators, and restore execution
  are explicitly deferred to follow-up implementation contexts.

### One-to-one test/evidence row mappings

| Matrix ID | Issue #68 evidence artifact | Planned deterministic evidence row |
|---|---|---|
| `DUR-RESTORE-001` | `docs/ADR/0011-context4-backup-restore-drill.md` (Scope, restore protocol, and evidence pack section) | `CTX4-RESTORE-EVID-001`: planned restore manifest, restore target definition, drill replay checklist, and evidence pack index. |
| `OPS-METRICS-001` | `docs/ADR/0011-context4-backup-restore-drill.md` (Restore and operational metric contracts) | `CTX4-METRICS-EVID-001`: planned command/event catalog, queue/lease/outbox metric sampling, and restore-lag validation snapshots. |
| `OPS-SLO-001` | `docs/ADR/0011-context4-backup-restore-drill.md` (RTO/RPO and escalation thresholds) | `CTX4-ESCALATION-EVID-001` plus `CTX4-POSTDRILL-EVID-001`: planned RTO/RPO proof pack, escalation matrix, and watch/closure summary. |

## Issue #69 (Context 5) Status and Evidence Mapping

### Matrix planning annotations for `OPS-METRICS-001`, `OPS-SLO-001`, `OPS-ALERT-001`, and `OPS-WATCH-001`

- Matrix status remains exactly `Open` for `OPS-METRICS-001`, `OPS-SLO-001`,
  `OPS-ALERT-001`, and `OPS-WATCH-001`.
- Issue `#69` is closed for planning and was completed in PR `#79`; this context records
  testable evidence contracts and review artifacts only. Runtime implementation,
  integrations, automation execution, and external tooling changes are explicitly
  deferred.
- Runtime dashboards, alert integrations, metrics emitters, watch automation, and
  alert-routing execution are explicitly deferred to follow-up production contexts.

### One-to-one test/evidence row mappings

| Matrix ID | Issue #69 evidence artifact | Planned deterministic evidence row |
|---|---|---|
| `OPS-METRICS-001` | `docs/ADR/0012-context5-metrics-slos-watch.md` (Metric catalog, failure-mode mapping, and advisory scrape/query contracts) | `CTX5-METRICS-EVID-001`: planned queue/lease/idempotency/restore/outbox metric catalog with advisory query contracts, backlog/backpressure thresholds, and ownership/failure-mode tests. |
| `OPS-SLO-001` | `docs/ADR/0012-context5-metrics-slos-watch.md` (SLO/error-budget thresholds) | `CTX5-SLO-EVID-001`: planned SLO threshold matrix, per-SLO error-budget windows, burn policy, and evidence-row with watch-state escalation linkage. |
| `OPS-ALERT-001` | `docs/ADR/0012-context5-metrics-slos-watch.md` (Alert severity matrix and routing) | `CTX5-ALERT-EVID-001`: planned severity matrix, ownership routing, ack SLA, and closure evidence requirements tied to watch log state. |
| `OPS-WATCH-001` | `docs/ADR/0012-context5-metrics-slos-watch.md` (First-hour watch protocol) | `CTX5-WATCH-EVID-001`: planned 120m/180m checkpoint workflow, handoff path, unresolved-condition escalation, and closure evidence sequence. |

## Issue #70 (Context 6) Status and Evidence Mapping

### Matrix planning annotations for rollback/media/privacy/release controls

- Matrix status remains exactly `Open` for `OPS-ROLLBACK-001`, `MEDIA-CONSENT-001`,
  `MEDIA-REVOKE-001`, `MEDIA-PROVENANCE-001`, `MEDIA-DISCLOSURE-001`,
  `PROVIDER-POSTURE-001`, `SEC-RETENTION-001`, `SEC-UNTRUSTED-001`, and
  `GOV-SCOPE-001`.
- Issue `#70` was the planning handoff target for these rows and was completed
  through PR `#80`; this context records testable governance and contract
  planning only. No runtime implementation is authorized.

### One-to-one test/evidence row mappings

| Matrix ID | Issue #70 evidence artifact | Planned deterministic evidence row |
|---|---|---|
| `OPS-ROLLBACK-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-rollback` | `CTX6-ROLLBACK-EVID-001`: planned freeze-window rubric, rollback ownership confirmation path, comms template, and evidence capture checklist. |
| `MEDIA-CONSENT-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-media-consent` | `CTX6-MEDIA-CONSENT-EVID-001`: planned affirmative consent schema including actor, timestamp, artifact references, text/version, and scope binding. |
| `MEDIA-REVOKE-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-media-revoke` | `CTX6-MEDIA-REVOKE-EVID-001`: planned revocation decision table for retain/block-replay/takedown and communications paths. |
| `MEDIA-PROVENANCE-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-media-provenance` | `CTX6-MEDIA-PROVENANCE-EVID-001`: planned provenance binding for source-run/providerversion/artifact checksums and identity/likeness denial evidence. |
| `MEDIA-DISCLOSURE-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-media-disclosure` | `CTX6-MEDIA-DISCLOSURE-EVID-001`: planned disclosure text/version binding and artifact-flag validation for export/public-use posture. |
| `PROVIDER-POSTURE-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-provider-posture` | `CTX6-PROVIDER-POSTURE-EVID-001`: planned provider release checklist for legal/license review, mock/local defaults, egress control, key isolation, prompt exclusion, and rollback disablement evidence. |
| `SEC-RETENTION-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-retention` | `CTX6-SEC-RETENTION-EVID-001`: planned deletion/erasure and redaction matrix across metadata, backups, logs, restored environments, and replay/export controls. |
| `SEC-UNTRUSTED-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-untrusted-input` | `CTX6-SEC-UNTRUSTED-EVID-001`: planned durable-replayed-input validation model, output encoding, prompt-injection controls, restore-time revalidation, and replay/export safety evidence. |
| `GOV-SCOPE-001` | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md#ctx6-governance-scope` | `CTX6-GOV-SCOPE-EVID-001`: planned governance split check with one-to-one follow-on issue/PR mapping and explicit scope-separation evidence requirements. |

### Context 6 Evidence Pack

#### ctx6-rollback

- `CTX6-ROLLBACK-EVID-001`: freeze-window rubric, rollback ownership confirmation path, comms template, and evidence capture checklist.

#### ctx6-media-consent

- `CTX6-MEDIA-CONSENT-EVID-001`: consent schema includes actor identity, timestamp, artifact refs, versioned consent text, scope binding, and replay retention rules.

#### ctx6-media-revoke

- `CTX6-MEDIA-REVOKE-EVID-001`: revocation table covers block-replay vs takedown vs retain-only outcomes, plus customer/provisioner communication paths.

#### ctx6-media-provenance

- `CTX6-MEDIA-PROVENANCE-EVID-001`: provenance binding policy for source-run, provider version, artifact checksums, and identity/likeness denial evidence.

#### ctx6-media-disclosure

- `CTX6-MEDIA-DISCLOSURE-EVID-001`: disclosure text/version binding, artifact flagging, and release posture validation controls.

#### ctx6-provider-posture

- `CTX6-PROVIDER-POSTURE-EVID-001`: provider-disabled default for local/dev/test, legal/license review check, mock/local adapter posture, key isolation, prompt exclusion, and rollback disablement criteria.

#### ctx6-retention

- `CTX6-SEC-RETENTION-EVID-001`: retention/deletion/redaction matrix for metadata, consent, provenance, logs, backups, and restored environments.

#### ctx6-untrusted-input

- `CTX6-SEC-UNTRUSTED-EVID-001`: durable/replayed-input validation, output encoding, prompt-injection controls, restore-time revalidation, and replay/export safety controls.

#### ctx6-governance-scope

- `CTX6-GOV-SCOPE-EVID-001`: governance handoff matrix linking each remaining blocker to follow-on issue/PR ownership and explicit scope-delimitation checks.

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
- validation command, automated test node ID, CI run/artifact URL, drill log, or
  explicit human-only evidence reference,
- owner,
- reviewer,
- residual-risk decision,
- timestamp or merge commit,
- explicit reason the evidence satisfies the row.

For durability, operations, media, security, and provider rows (`DUR-*`,
`OPS-*`, `MEDIA-*`, `SEC-*`, and `PROVIDER-*`), final row closure requires
production-grade evidence rather than generic documentation. Valid final proof
must include at least one concrete evidence form:

- automated test node ID,
- GitHub Actions CI run or artifact URL,
- drill log,
- explicit `human-only` evidence with owner and residual-risk decision.

Rows in those domains must not use Context 0 planning artifacts, PR `#64`, or
`docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` alone as sufficient final
proof. They also require same-repository child issue and child PR URLs, with a
child PR number distinct from `#64`; when GitHub API validation is available,
the child PR must be verified as merged before the row can support final
closure.

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
  - map `GOV-SCOPE-001` to ownership in Issue `#70`.
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
