# Issue #39 Production Closure Plan (Context 0)

## Objective

Create a durable, reviewed production-closure contract for GitHub issue `#39` that is reusable by later contexts and PRs.

- It is a context-0 planning contract only.
- It defines production durability and monitoring requirements before any durable runtime implementation starts.
- It explicitly excludes all runtime product/database/provider/monitoring implementations.

## Current State (as of 2026-07-10)

- `#39` remains open and is the remaining Phase 1 P1 production blocker.
- Execution sequencing, per-chunk Definition of Done, parallelization rules,
  review-agent protocol, and production transition strategy are tracked in
  `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`.
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

1. **Context 0 (this context):** Contract-only planning for durability/monitoring; matrix and child decomposition only. The chunk execution strategy is maintained in `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`.
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
The rows below are historical planning-context mappings only. Implementation
closure must use the per-chunk execution rows in
`docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`; final row closure records must
cite concrete chunk implementation PRs rather than treating planning PRs
`#64` through `#80` as production evidence.

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
| `DUR-ROLLBACK-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Rollback and forward-repair section; superseded for execution evidence by ADR `0022` and the CH-09 matrix below) | `CTX3-ROLLBACK-EVID-001`: planned tests `test_context3_previous_code_runs_against_backward_compatible_expanded_schema`, `test_context3_schema_version_and_compatibility_window_enforced`, `test_context3_schema_version_support_window_rejects_newer_expanded_schema`, `test_context3_rollback_blocks_when_unsafe_without_repair`, `test_context3_forward_repair_restores_rollback_compatibility`, `test_context3_forward_repair_restores_rollback_compatibility_from_reviewed_proof_source`, `test_context3_no_false_down_migration_support_without_tested_path`, `test_context3_rollback_blocks_when_required_legacy_field_is_missing`, `test_context3_rollback_blocks_when_required_legacy_field_has_wrong_type`, `test_context3_rollback_blocks_when_required_legacy_int_field_is_boolean`, `test_context3_rollback_blocks_when_proof_reference_or_revision_mismatch`, `test_context3_rollback_blocks_when_proof_revision_missing_from_trusted_ledger`, `test_context3_rollback_blocks_when_state_proof_revision_is_missing_from_state_ledger`, `test_context3_rollback_blocks_when_state_proof_is_not_trusted`, `test_context3_rollback_blocks_when_blocked_payload_field_is_present`, `test_context3_forward_repair_requires_material_change_before_widening_window`, `test_context3_forward_repair_does_not_widen_compatibility_ceiling`, `test_context3_forward_repair_blocks_when_repaired_payload_is_still_incompatible`, `test_ch09_runner_persists_and_loads_rollback_compatibility`, `test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source`, `test_ch09_runner_blocks_when_persisted_rollback_compatibility_is_missing`, `test_ch09_runner_blocks_when_reviewed_proof_source_entry_is_missing`, `test_ch09_runner_rejects_self_attested_proof_reconstructed_from_persisted_metadata`, `test_ch09_runner_rejects_reviewed_proof_source_payload_fingerprint_mismatch`, and `test_ch09_runner_rejects_tampered_persisted_rollback_compatibility_ledger_on_read`. |
| `DUR-STAGE6-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Optional Stage 6 compatibility section) | `CTX3-STAGE6-EVID-001`: planned test `test_context3_stage6_artifact_state_readers_tolerate_schema_version_gap`. |
| `DUR-STAGE7-001` | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` (Optional Stage 7 compatibility section) | `CTX3-STAGE7-EVID-001`: planned test `test_context3_stage7_artifact_state_readers_tolerate_schema_version_gap`. |

### Planning-only runtime posture for Issue #67

- Runtime migration execution (migration runners, schema upgrades, lock-table migration
  scripts, data backfills, and downgrade scripts) is explicitly deferred to later
  production implementation contexts.
- ADRs, planning matrices, and branch allowlist/checker updates are the only artifacts
  added in this context.

## CH-07 Pre-Implementation Invariant Matrix

This section is the repo-tracked pre-implementation artifact for child issue
`#109` / chunk `CH-07`. It does not close `DUR-STAGE6-001`. It defines the
required invariant-to-test mapping before Stage 6 durable replay implementation.
The statuses below track branch-level implementation evidence only. Issue `#39`
and matrix row `DUR-STAGE6-001` remain open until PR review, merge, and final
row-level closure evidence are completed.

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Gate / source / human-only evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `S6-SOURCE-001` | Stage 6 source evidence binding | Multilingual replay remains bound to source run ID, trace ID, retrieved context refs, citation indexes, evaluation ID/status/checksum, and claim-support records before replay/export. | Restored artifacts can remain internally consistent while pointing at mismatched source or evaluation evidence. | `test_stage6_replays_valid_source_bound_artifact` | `test_stage6_drops_artifact_with_mismatched_source_run`; mutate evaluation checksum or claim-support IDs and prove old behavior failed | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Stage 6 + architecture/state | Implemented on branch |
| `S6-ARTIFACT-001` | Stage 6 derived artifact consistency | Translated text, provider text, subtitle text, metadata artifact, downloadable artifacts, checksums, language tags, provider mode/config, glossary, citations, and voice manifest mutually agree. | A tampered provider/artifact payload can replay if only a subset of fields is validated. | `test_stage6_replays_valid_source_bound_artifact` | `test_stage6_file_state_drops_inconsistent_restored_artifact_payload`; mutate metadata/checksum/glossary or citation preservation and prove replay is dropped | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 6 | Implemented on branch |
| `S6-IDEMP-001` | Stage 6 idempotency replay | Replay uses only terminal valid records with matching operation scope and request checksum; changed payloads conflict; stale pending/running and corrupt failed records do not replay. | Stale in-flight rows or invalid failed rows can masquerade as durable success/failure. | `test_stage6_file_state_replays_completed_multilingual_idempotency` | `test_stage6_file_state_drops_failed_idempotency_with_missing_error`; `test_stage6_drops_running_idempotency_record_on_restore`; checksum conflict regression | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/API_CONTRACT.md` idempotency contract | Stage 6 + test/evidence | Implemented on branch |
| `S6-DEDUPE-001` | Stage 6 durable dedupe | Identical source/request payloads within scope dedupe to the same durable multilingual run and artifacts without claiming exactly-once side effects. | Different idempotency keys can create duplicate durable derived artifacts for the same request payload. | `test_stage6_dedupes_identical_request_checksum_to_existing_durable_run` | `test_multilingual_walkthrough_api_rejects_secret_like_glossary_terms`; cross-scope non-dedupe regression | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `uv run pytest -p no:cacheprovider tests/api/test_stage6_multilingual_api.py`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Stage 6 + architecture/state | Implemented on branch |
| `S6-RESTORE-001` | Stage 6 restore hardening | Corrupted, tampered, cross-run, cross-project, cross-language, stale-counter, missing-error, and provider-mode-invalid restored rows are dropped or rejected safely. | Restore can treat wrong-shape or cross-boundary data as trusted durable state. | `test_stage6_restore_derives_missing_counters_from_restored_ids` | `test_stage6_file_state_drops_tampered_nonlocal_provider_result`; `test_stage6_file_state_drops_failed_idempotency_with_missing_error`; `test_stage6_file_state_drops_inconsistent_restored_artifact_payload`; stale-low counter regression | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 6 + security/runtime | Implemented on branch |

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

### Issue `#125` local restore-integrity drill status and evidence mapping

- Matrix status remains exactly `Open` for `DUR-RESTORE-001`.
- Issue `#125` is an executable local-only evidence slice for the optional
  file-backed Stage 4/6/7 state already present in the repo.
- Issue `#125` does not satisfy the production `CH-14` closure bar from
  `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` and must not be represented as
  production backup/restore evidence.

| Matrix ID | Issue #125 evidence artifact | Narrow executable evidence row |
|---|---|---|
| `DUR-RESTORE-001` | `docs/ADR/0023-local-restore-integrity-drill.md`, `docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md`, and `backend/app/storage/local_restore_drill.py` | `CTX4-LOCAL-RESTORE-EVID-001`: `uv run python -m backend.app.storage.local_restore_drill --output outputs/restore-drill.json` seeds Stage 4/6/7 local state, copies source JSON state into a restored directory, verifies byte-identical file checksums, restores the services, replays the same Stage 4 `create_project`/`upload_document`/`approve_document`/`ingest_documents`/`generate_walkthrough` operations plus the Stage 6/7 replay paths without creating new durable identifiers, checks record-count parity before and after replay, and persists inspectable evidence paths. Production backup platform evidence, restore metrics, RTO/RPO proof, retention/re-delete behavior, and operational signoff remain open. |

### Issue `#126` CH-14 restore-readiness contract status and evidence mapping

- Matrix status remains exactly `Open` for `DUR-RESTORE-001`.
- Issue `#126` is a narrow repo-checked restore-readiness contract slice for
  the current repo-supported `CH-14` boundary after merged issue `#125`,
  plus the current repo-baselined `CH-10` and `CH-11` contract artifacts.
- Issue `#126` does not satisfy final `CH-14` restore-drill closure, does not
  satisfy `CTX4-RESTORE-EVID-001`, and must not be represented as successful
  production backup/restore evidence or production restore readiness.

| Matrix ID | Issue #126 evidence artifact | Narrow executable evidence row |
|---|---|---|
| `DUR-RESTORE-001` | `docs/ADR/0026-ch14-restore-readiness-contract.md` and `docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md` | `CTX4-RESTORE-READINESS-EVID-001`: reviewed repo docs compose the merged `CTX4-LOCAL-RESTORE-EVID-001` local restore drill with the current repo-baselined `CTX5-METRICS-EVID-001` restore-adjacent metric names and `CTX5-SLO-EVID-001` advisory restore SLO contract, enumerate the required human-only production drill surfaces (backup platform, restore target, operator roster, successful drill timestamp, restore metrics export, measured RTO/RPO, and operations/security signoff), and define explicit no-go criteria that keep issue `#39` and matrix row `DUR-RESTORE-001` open until final production drill evidence exists. Successful production restore execution, actual RTO/RPO proof, restore metrics export, retention/re-delete evidence, and operational signoff remain open. |

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

### Issue `#128` CH-10 production metrics contract status and evidence mapping

- Matrix status remains exactly `Open` for `OPS-METRICS-001`.
- Issue `#128` is the narrow executable `CH-10` slice for metric names and
  emission points only. It does not close `OPS-METRICS-001`, does not satisfy
  `OPS-SLO-001`, `OPS-ALERT-001`, or `OPS-WATCH-001`, and does not create
  production restore-drill or rollback-communications evidence.

| Matrix ID | Issue #128 evidence artifact | Narrow executable evidence row |
|---|---|---|
| `OPS-METRICS-001` | `docs/ADR/0024-ch10-production-metrics-contract.md`, `backend/app/storage/ops_metrics.py`, `backend/app/storage/postgres_state.py`, `backend/app/storage/file_state.py`, `backend/app/storage/migrations.py`, and `tests/unit/test_ops_metrics.py` | `CTX5-METRICS-EVID-001`: focused tests prove named emission points for durable run backlog, lease state/staleness/reacquire, idempotency conflict/replay/stale-owner rejection, outbox backlog/age/redelivery, local restore-adjacent state-load attempts/duration, and rollback block counters. Queue-lag worker metrics, backup-lag metrics, SLO/error-budget thresholds, dashboard queries, alert routing, watch execution, successful restore drill timings, and rollback communications remain deferred to `CH-11`, `CH-12`, `CH-13`, `CH-14`, and `CH-15`. |

### Issue `#127` CH-11 SLO and error-budget contract status and evidence mapping

- Matrix status remains exactly `Open` for `OPS-SLO-001`.
- Issue `#127` is the narrow executable `CH-11` slice for the reviewed SLO
  catalog, threshold semantics, error-budget semantics, and release-breach
  actions bound to the merged `CH-10` metric contract.
- Issue `#127` does not close `OPS-SLO-001`, does not satisfy `OPS-ALERT-001` or `OPS-WATCH-001`, and does not create production restore-drill or rollback-communications evidence.

| Matrix ID | Issue #127 evidence artifact | Narrow executable evidence row |
|---|---|---|
| `OPS-SLO-001` | `docs/ADR/0025-ch11-slo-error-budget.md` | `CTX5-SLO-EVID-001`: reviewed SLO catalog binds the merged `CH-10` metric names to executable now versus advisory-only threshold semantics, manual review contract error budget burn policy, and release-blocking breach actions for backlog, lease, idempotency, outbox, restore, and rollback decisions. Dashboard/query execution, alert routing, watch execution, successful restore drill timings, and rollback communications remain deferred to `CH-12`, `CH-13`, `CH-14`, and `CH-15`. |

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

## CH-08 Pre-Implementation Invariant Matrix

This section is the repo-tracked pre-implementation artifact for closed child
issue `#115` and the implementation evidence map for child issue `#119` /
chunk `CH-08`, merged through PR `#120` at
`af7215a5ceb7cefa81306773c1cfa8260435291e`. It does not close
`DUR-STAGE7-001`. The statuses below track merged chunk implementation evidence
only. Issue `#39` and matrix row `DUR-STAGE7-001` remain open until the later
provenance/disclosure rows provide the missing closure evidence.

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Gate / source / human-only evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| `S8-RENDER-001` | Stage 7 render state binding | Render records preserve source-run, trace, evaluation, consent, legal render-status history, canonical source-evaluation checksum, mandatory request checksum, and original idempotency scope/key, and restore replays only terminal render rows that still match their request checksum and ownership scope. | Restored render state can look complete while pointing at the wrong source run or replaying stale in-flight work. | `test_stage7_file_state_replays_completed_avatar_idempotency`; `test_stage7_file_state_replays_completed_avatar_idempotency_after_canonicalizing_request`; `test_stage7_file_state_replays_idempotency_when_replay_supplies_canonical_evaluation_checksum`; `test_stage7_file_state_replays_requested_provider_unavailable_fallback_history`; `test_stage7_file_state_replays_provider_failed_fallback_history`; `test_stage7_file_state_replays_pure_provider_failed_fallback_history` | `test_stage7_file_state_drops_tampered_nonlocal_provider_result`; `test_stage7_file_state_drops_artifact_metadata_for_missing_render`; `test_stage7_file_state_drops_completed_idempotency_with_mismatched_request_checksum`; `test_stage7_file_state_drops_render_missing_request_checksum`; `test_stage7_file_state_drops_render_without_terminal_status_history`; `test_stage7_file_state_drops_render_with_malformed_status_history_item`; `test_stage7_file_state_drops_render_with_impossible_status_history_order`; `test_stage7_file_state_drops_cross_scope_render_idempotency_record`; `test_stage7_file_state_drops_render_idempotency_with_wrong_endpoint`; `test_stage7_file_state_drops_render_with_forged_local_idempotency_scope`; `test_stage7_file_state_drops_render_with_self_consistent_cross_scope_without_idempotency`; `test_stage7_file_state_drops_render_with_noncanonical_source_evaluation_checksum`; `test_stage7_file_state_prunes_idempotency_records_for_invalidated_render`; `test_stage7_file_state_drops_failed_render_idempotency_after_restart` | PR `#120`; `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/ENGINEERING_PROCESS_RCA.md`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Stage 7 + architecture/state | Merged through PR `#120` |
| `S8-ARTIFACT-001` | Derived artifact consistency | Demo export, render manifest, and placeholder artifact metadata remain checksum-bound and reject mismatch, missing-render, malformed metadata, or non-local provider drift. | A tampered artifact row can survive restore if only one file shape is checked. | `test_stage7_file_state_drops_artifact_metadata_that_mismatches_render` | `test_stage7_file_state_drops_malformed_artifact_metadata_without_clearing_valid_render`; `test_provider_artifacts_must_use_safe_expected_export_shapes`; `test_provider_html_export_must_exactly_match_trusted_renderer` | PR `#120`; `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/API_CONTRACT.md`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 7 + test/evidence | Merged through PR `#120` |
| `S8-CONSENT-001` | Consent checkpoint binding | Render artifacts stay bound to the consumed durable consent record and are rejected when the record is cross-scope, stale, or tampered. | A render can restore with a consent link that no longer matches the artifact state. | `test_stage7_restores_consumed_durable_consent_binding_after_successful_render` | `test_stage7_drops_tampered_consumed_consent_binding_on_restore`; `test_stage7_rejects_cross_scope_or_stale_version_consent_record`; `test_stage7_rejects_reuse_of_consumed_durable_consent_record`; `test_stage7_file_state_drops_cross_scope_consent_idempotency_record`; `test_stage7_file_state_drops_consent_idempotency_with_wrong_endpoint` | PR `#120`; `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/API_CONTRACT.md`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 7 + security/privacy | Merged through PR `#120` |
| `S8-ROLLBACK-001` | Terminal persist rollback | A failed terminal persist removes orphan render state while preserving concurrent successful render work. | A write failure can leave an orphan avatar render or erase a later committed success. | `test_stage7_file_state_terminal_persist_failure_preserves_concurrent_success` | `test_stage7_file_state_terminal_persist_failure_does_not_leave_orphan_render` | PR `#120`; `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 7 + security/runtime | Merged through PR `#120` |

## CH-09 Pre-Implementation Invariant Matrix

This section is the repo-tracked pre-implementation artifact for child issue
`#123` / chunk `CH-09`. It does not close `DUR-ROLLBACK-001`. It defines the
required invariant-to-test mapping before CH-09 technical rollback
compatibility closure can be claimed for issue `#123`. Issue `#39` and matrix
row `DUR-ROLLBACK-001` remain open until PR review, merge, and final row-level
closure evidence are completed.

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Gate / source / human-only evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| `RBK-COMPAT-001` | Previous-code compatibility | Previous code is rollback-safe only when the expanded schema remains inside both declared version windows, binds to a reviewed compatibility proof in the applied migration ledger, and still carries the typed legacy fields older code requires. | Additive schema changes can appear compatible while silently dropping fields or proof bindings that the previous deploy still reads. | `test_context3_previous_code_runs_against_backward_compatible_expanded_schema` | `test_context3_rollback_blocks_when_required_legacy_field_is_missing`; `test_context3_rollback_blocks_when_required_legacy_field_has_wrong_type`; `test_context3_rollback_blocks_when_required_legacy_int_field_is_boolean`; `test_context3_rollback_blocks_when_proof_reference_or_revision_mismatch`; `test_context3_rollback_blocks_when_proof_revision_missing_from_trusted_ledger`; `test_context3_rollback_blocks_when_state_proof_is_not_trusted` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/ADR/0010-context3-migrations-rollback-compatibility.md`; `docs/ADR/0022-ch09-technical-rollback-compatibility.md` | Platform/storage | Implemented on branch |
| `RBK-BLOCK-001` | Unsafe rollback block | Rollback fails closed when compatibility cannot be proven and remains blocked until forward repair completes. | Release decisions can treat missing compatibility proof as advisory and still attempt rollback. | `test_context3_rollback_blocks_when_unsafe_without_repair`; `test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source` | mutate compatibility-floor or required-field state and prove the block fires; `test_ch09_runner_blocks_when_persisted_rollback_compatibility_is_missing`; `test_ch09_runner_rejects_tampered_persisted_rollback_compatibility_ledger_on_read` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Release safety | Implemented on branch |
| `RBK-TRUST-001` | Reviewed proof source boundary | Runner-side rollback preflight resolves reviewed proof entries from an out-of-band proof source, so restored durable metadata cannot satisfy the trusted path by self-attestation alone. | Persisted rollback metadata can be internally consistent while still being reconstructed from tampered restored state. | `test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source`; `test_context3_forward_repair_restores_rollback_compatibility_from_reviewed_proof_source` | `test_ch09_runner_blocks_when_reviewed_proof_source_entry_is_missing`; `test_ch09_runner_rejects_self_attested_proof_reconstructed_from_persisted_metadata`; `test_ch09_runner_rejects_reviewed_proof_source_payload_fingerprint_mismatch` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/ADR/0022-ch09-technical-rollback-compatibility.md` | Platform/storage + release | Implemented on branch |
| `RBK-REPAIR-001` | Forward repair | Forward repair can restore the legacy-compatible payload, record a reviewed repair revision, and reopen the compatibility window for the previous code version without destructive rollback. | Repair can backfill a field but still leave the previous deploy outside the allowed version window or without reviewed proof. | `test_context3_forward_repair_restores_rollback_compatibility` | `test_context3_forward_repair_requires_material_change_before_widening_window`; `test_context3_forward_repair_does_not_widen_compatibility_ceiling`; `test_context3_forward_repair_blocks_when_repaired_payload_is_still_incompatible` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/ADR/0010-context3-migrations-rollback-compatibility.md` | Platform/storage + release | Implemented on branch |
| `RBK-WINDOW-001` | Schema/window enforcement | Schema-version floors and ceilings plus compatibility-window bounds are enforced before rollback compatibility is claimed. | Newer expanded schema can pass rollback checks because only one side of the window is validated. | `test_context3_previous_code_runs_against_backward_compatible_expanded_schema` | `test_context3_schema_version_and_compatibility_window_enforced`; `test_context3_schema_version_support_window_rejects_newer_expanded_schema` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py` | Platform/storage | Implemented on branch |
| `RBK-NODOWN-001` | No false down-migration claim | Down-migration support remains false throughout CH-09. | Reviewers can overread rollback compatibility as full down-migration support. | `test_context3_no_false_down_migration_support_without_tested_path` | supply a down-migration marker and prove the result still stays false | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; human review of PR wording | Release safety + governance | Implemented on branch |

## CH-16 Pre-Implementation Invariant Matrix

This section is the repo-tracked pre-implementation artifact for child issue
`#111` / chunk `CH-16`. It does not close `MEDIA-CONSENT-001`. It defines the
required invariant-to-test mapping before durable synthetic-media consent
capture implementation. Issue `#39` and matrix row `MEDIA-CONSENT-001` remain
open until PR review, merge, and final row-level closure evidence are
completed.

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Gate / source / human-only evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| `S16-CONSENT-001` | Durable consent record schema | Durable consent records bind actor ID, tenant/project/source-run scope, timestamp, consent text/version, source trace/evaluation hooks, request checksum, and artifact/reference hooks before Stage 7 generation can succeed. | A render can succeed with only a process-local boolean or with a record that omits actor/scope/text/version linkage. | `test_stage7_records_durable_synthetic_media_consent_and_replays_it` | `test_stage7_rejects_render_when_durable_consent_record_is_missing_or_invalid`; `test_stage7_file_state_terminal_persist_failure_restores_consent_bound_render_state`; mutate consent text/version or remove actor/source hook fields and prove old behavior fails | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/ENGINEERING_PROCESS_RCA.md`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Stage 7 + security/privacy | Implemented on branch |
| `S16-SCOPE-001` | Consent scope binding | Consent scope is explicit and rejects cross-project, cross-run, cross-actor, stale-version, consumed-consent, or ambiguous consent replay. | A valid-looking consent row can be replayed against a different actor, project, run, or superseded consent statement version, or reused after it has already been bound to a successful render. | `test_stage7_accepts_matching_consent_scope_for_render_gate` | `test_stage7_rejects_cross_scope_or_stale_version_consent_record`; `test_stage7_rejects_scope_mismatches_for_durable_consent`; `test_stage7_rejects_reuse_of_consumed_durable_consent_record` | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/API_CONTRACT.md` | Stage 7 + architecture/state | Implemented on branch |
| `S16-IDEMP-001` | Consent idempotency semantics | Consent create/replay uses terminal valid idempotency semantics with payload conflict rejection and no stale pending/running replay as success. | Reused consent idempotency keys can silently mutate consent scope, or stale in-flight rows can masquerade as durable success. | `test_stage7_consent_idempotency_replays_terminal_success` | `test_stage7_consent_idempotency_conflicts_on_changed_payload`; `test_stage7_drops_running_consent_idempotency_record_on_restore` | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage7_avatar.py`; `docs/API_CONTRACT.md` idempotency contract | Stage 7 + test/evidence | Implemented on branch |
| `S16-RESTORE-001` | Consent restore hardening | Corrupted, tampered, incomplete, cross-run, cross-project, cross-actor, malformed-timestamp, request-checksum-mismatched, or consumed-binding-mismatched restored consent rows are dropped or rejected safely. | Restore can trust wrong-shape or cross-boundary consent rows, or keep a consumed consent/render pair whose stored binding no longer matches. | `test_stage7_restores_consumed_durable_consent_binding_after_successful_render` | `test_stage7_drops_malformed_or_cross_boundary_consent_record_on_restore`; `test_stage7_drops_tampered_consumed_consent_binding_on_restore`; mutate record shape/scope/timestamp/request checksum/render hook and prove old behavior fails | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 7 + security/runtime | Implemented on branch |
| `S16-GATE-001` | Stage 7 durable consent gate | Stage 7 paths that require durable synthetic-media consent reject missing or invalid durable consent state even if the request flag is true. | The request boolean can bypass durable consent gating and let synthetic-media generation proceed without a valid stored consent record. | `test_avatar_render_api_requires_prior_durable_consent_record` | `test_stage7_rejects_render_when_durable_consent_record_is_missing_or_invalid` | `uv run pytest -p no:cacheprovider tests/unit/test_stage7_avatar.py tests/api/test_stage7_avatar_api.py`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Stage 7 + security/privacy | Implemented on branch |

## CH-07 Stage 6 Durable Replay Evidence Matrix

This branch-local matrix records the durable replay evidence for child issue
`#109`. It is branch evidence only. It does not close `DUR-STAGE6-001` or
issue `#39`.

| ID | Area | Invariant | Positive test | Negative / mutation test | Gate / source / human-only evidence | Owner | Status |
|---|---|---|---|---|---|---|---|
| `S7-REPLAY-001` | Stage 6 durable replay | Stage 6 translated script, subtitle, voice metadata, and derived metadata replay from durable state without recomputation when request identity and payload checksum match. | `test_stage6_file_state_replays_completed_multilingual_idempotency` | `test_reused_idempotency_key_with_changed_payload_conflicts`; `test_multilingual_walkthrough_api_rejects_changed_payload_for_reused_idempotency_key` | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py`; `docs/ENGINEERING_PROCESS_RCA.md`; `docs/API_CONTRACT.md` | Stage 6 + test/evidence | Implemented on branch |
| `S7-SOURCE-001` | Stage 6 source binding | Durable Stage 6 records bind tenant/project/actor/source run ID, source language, target language, source text checksum, source evaluation/checksum hooks, and trace identity. | `test_multilingual_walkthrough_api_returns_downloadable_script_and_subtitle_artifacts` | `test_stage6_file_state_drops_cross_boundary_or_checksum_mismatched_rows_on_restore` | `uv run pytest -p no:cacheprovider tests/api/test_stage6_multilingual_api.py tests/unit/test_local_durability.py`; `docs/API_CONTRACT.md`; `docs/TRACEABILITY.md`; human-review of trace payload surfaces | Stage 6 + architecture/state | Implemented on branch |
| `S7-IDEMP-001` | Stage 6 idempotency | Stage 6 idempotency follows terminal valid replay semantics with changed-payload conflict rejection and no stale pending/running replay as success. | `test_stage6_file_state_replays_completed_multilingual_idempotency` | `test_reused_idempotency_key_with_changed_payload_conflicts`; `test_stage6_drops_running_idempotency_record_on_restore`; `test_stage6_file_state_drops_failed_idempotency_with_missing_error` | `uv run pytest -p no:cacheprovider tests/unit/test_stage6_multilingual.py tests/unit/test_local_durability.py`; `docs/API_CONTRACT.md`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 6 + test/evidence | Implemented on branch |
| `S7-RESTORE-001` | Stage 6 restore hardening | Malformed, incomplete, corrupted, cross-run, cross-project, cross-actor, stale-source, or checksum-mismatched restored Stage 6 rows are dropped or rejected safely. | `test_stage6_file_state_drops_cross_boundary_or_checksum_mismatched_rows_on_restore`; `test_stage6_file_state_drops_corrupted_metadata_artifact_on_restore` | `test_stage6_file_state_drops_tampered_nonlocal_provider_result`; `test_stage6_file_state_drops_inconsistent_restored_artifact_payload`; `test_stage6_file_state_drops_subtitle_checksum_mismatch_on_restore` | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py`; `docs/ENGINEERING_PROCESS_RCA.md`; human-review of restored-row rejection behavior | Stage 6 + security/runtime | Implemented on branch |
| `S7-ARTIFACT-001` | Stage 6 derived artifacts | Subtitle and derived artifact metadata are checksum-bound, size-bounded, safely encoded, and not trusted as HTML or provider-trusted content. | `test_stage6_replays_valid_source_bound_artifact`; `test_multilingual_walkthrough_api_returns_downloadable_script_and_subtitle_artifacts` | `test_stage6_file_state_drops_subtitle_checksum_mismatch_on_restore`; `test_stage6_file_state_drops_corrupted_metadata_artifact_on_restore` | `uv run pytest -p no:cacheprovider tests/unit/test_local_durability.py tests/api/test_stage6_multilingual_api.py`; `docs/API_CONTRACT.md`; `docs/ENGINEERING_PROCESS_RCA.md` | Stage 6 + security/runtime | Implemented on branch |
| `S7-GATE-001` | Stage 6 source-run gating | Stage 6 replay depends on durable source-run linkage and does not replay outputs against an invalid, missing, failed, or mismatched Stage 4 source run. | `test_multilingual_walkthrough_api_returns_downloadable_script_and_subtitle_artifacts` | `test_stage6_drops_artifact_with_mismatched_source_run`; `test_stage6_file_state_drops_cross_boundary_or_checksum_mismatched_rows_on_restore` | `uv run pytest -p no:cacheprovider tests/api/test_stage6_multilingual_api.py tests/unit/test_local_durability.py`; `docs/API_CONTRACT.md`; `docs/STATUS.md`; human review of source-run authorization and gating | Stage 6 + architecture/state | Implemented on branch |

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
