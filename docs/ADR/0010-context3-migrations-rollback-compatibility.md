# ADR 0010: Migrations and Rollback Compatibility for Issue #39 Context 3 (Advisory Only)

## Status

Accepted for planning in Phase 1 Closure Context 3 (`#67`), advisory only.

## Date

2026-07-10

## Context

Issue `#39` remains open because production-grade durability and monitoring are not yet fully implemented.
Issue `#67` is the Context 3 decomposition target for migration and rollback compatibility planning for:

- `DUR-MIG-001`: migrations
- `DUR-ROLLBACK-001`: technical rollback compatibility
- where relevant: `DUR-STAGE6-001`, `DUR-STAGE7-001` artifact-state ordering

This context is advisory planning only. It defines compatibility posture, sequencing,
and proof expectations before runtime implementation contexts can schedule migration
or rollback execution.

Local/mock behavior remains unchanged by this ADR.

## Decision

Migrations are planned as a contract-first, versioned, compatibility-aware rollout
that supports **forward progress without default exact down-migration assumptions**.

### 1) Expand / contract migration strategy

#### Expand phase

All production-compatible schema changes start with an **expand** step:

- Additive, backward-compatible changes only in the initial deployment phase.
- New columns, indexes, enums, and nullable fields are introduced first.
- Existing readers and writers continue to function against previous schema shape.
- New features adopt write/read guards for optional fields while older producers
  coexist.

#### Contract checks during expand

- Any feature path reading new fields must tolerate null/unset values.
- Any feature path writing new columns must provide defaults and not block existing
  paths during partial rollout.
- No business-critical write path may depend on new constraints before all active
  versions can satisfy them.

#### Contract-safe contraction phase

Contraction (`drop`/tighten/rename) is only planned after:

- Compatibility evidence from prior expand is complete.
- All producers expected to remain in compatibility window are no longer deployed.
- No unresolved artifact state compatibility risk is present for Stage 6/7 artifacts.

Contraction is advisory-only in this context; runtime execution remains deferred.

### 2) Forward-only migration posture

This context uses a **forward-only posture** for production planning:

- Runtime implementation must not assume reversible DDL for business-safe rollback.
- Downgrade-only claims are not used as mandatory proof.
- Compatibility windows and repair actions are required when rollback is unsafe.
- No mandatory down-migration is recorded as the default safety mechanism.

Rollback posture:

- prefer forward deployment + forward repair where possible,
- permit rollback only where it preserves contract invariants and does not violate
  data integrity.

### 3) Schema versioning and compatibility windows

Every migration plan includes:

1. `schema_version` contract boundary in storage state,
2. compatibility windows per service image and migration generation,
3. a minimum supported writer compatibility floor for mixed-version windows,
4. explicit feature-flag and migration-version preconditions.

Compatibility window requirement:

- At least one deploy step must keep new reads and old writes compatible.
- At least one deploy step must keep rollback-capable code paths valid if rollback is attempted.
- Any incompatible code+schema combination is treated as a **known-unsafe rollback**
  condition and must be documented before production rollout.

### 4) Application rollback compatibility after schema expansion

After schema expansion:

- Code that relies on expanded columns must include fallback read logic for older
  schema versions and absent values.
- New domain events and durable-state records must include version-bearing fields.
- Rollback must prove replay safety for already-terminal durable states.
- If a version mismatch prevents safe rewind, deployment is blocked from rollback
  and moved into forward-repair mode.

Rollback compatibility is valid only when:

- idempotency state transitions remain replay-safe under the older binary,
- lease/outbox metadata expectations remain satisfiable,
- Stage 6/Stage 7 artifact provenance links remain intact.

### 5) Forward-repair strategy when rollback is unsafe

When rollback is unsafe due to incompatible data history:

- **Do not** attempt forced destructive rollback.
- Enter **forward repair mode**:
  - apply a bounded corrective migration with explicit evidence,
  - route affected work units through a reviewed repair runbook,
  - keep producer-side idempotent replay and lease-owner fences in effect,
  - complete a replay-safe evidence check before declaring repair complete.

Forward repair requires evidence of:

- safe contract path for existing terminal states,
- resolved artifact-state integrity for Stage 6/7 outputs,
- re-established rollback criteria if and only if compatibility is restored.

### 6) Migration ordering relative to idempotency, lease, outbox, Stage 6, and Stage 7 state

Because this issue sequence already split Context 1/2 planning and runtime state
contracts, migration ordering must remain consistent with those contracts:

1. Stage 1: define boundary, state transitions, and idempotency/lease/outbox
   contracts before runtime mutation of tables or migration-dependent behavior.
2. Stage 2: run **idempotency and lease-compatible** migration planning before
   making durability transitions dependent on migration version checks.
3. Stage 3: keep outbox row shape and dispatch ownership compatible with migration
   sequence; outbox delivery is at least-once and idempotency replays must remain deterministic.
4. Stage 4: migrate durable references required by Stage 6/7 replay/state artifacts only after their
   producer-readers have explicit version guards.
5. Stage 5: only after above compatibility checks are satisfied, allow migration
   execution handoff to implementation context.

This order is planning-only and does not authorize migration runtime in this branch.

### 7) Deterministic evidence expectations

For advisory acceptance and planning handoff, issue `#67` must bind each migration
row to one deterministic evidence row in the `Issue #39` closure plan:

- `CTX3-MIG-EVID-001`: planned mapping for `DUR-MIG-001` with planned tests
  `test_context3_expand_then_contract_strategy`, `test_context3_expand_is_backward_compatible`, and `test_context3_migration_ordering_with_idempotency_lease_outbox`.
- `CTX3-ROLLBACK-EVID-001`: planned mapping for `DUR-ROLLBACK-001` with planned tests
  `test_context3_backward_compatible_window_enforced`, `test_context3_rollback_blocks_when_unsafe_without_repair`, and `test_context3_forward_repair_restores_rollback_compatibility`.
- `CTX3-STAGE6-EVID-001` / `CTX3-STAGE7-EVID-001`: optional compatibility mappings when migration artifacts
  touch Stage 6/7 state, with planned tests
  `test_context3_stage6_artifact_state_readers_tolerate_schema_version_gap` and
  `test_context3_stage7_artifact_state_readers_tolerate_schema_version_gap`.

The optional Stage 6/7 artifact compatibility row is required only if the migration
plan introduces schema columns or constraints that can affect artifact-state read/write
shape.

### 8) Non-goals and deferred runtime items

The following remain deferred to later implementation contexts and are out of scope
for this planning issue:

- SQL DDL and migration script execution.
- Migration runners, migration checksums, and production rollout scheduling.
- Lock table/queue table worker implementations.
- Endpoints, schema files, runtime schema bootstrap, runtime migration lock/lease table integration.
- Provider activation, provider runtime changes, local/dev/test runtime behavior change.

Paid providers remain optional/disabled by default outside production enablement.

## Alternatives Considered

### "Exact down-migration first"

Rejected: it creates unsafe assumptions for artifact-linked durable state and does not
address the practical reality that some schema evolutions are only safely reversible
through forward repair.

### "Migrate only after all feature rollout complete"

Rejected: this delays deterministic compatibility validation and keeps production
state uncertain across long mixed-version windows.

## Consequences

Positive:

- Context 3 gets explicit migration and rollback compatibility contracts before
  implementation starts, separate from runtime migration execution.
- Matrix owners can evaluate `DUR-MIG-001` and `DUR-ROLLBACK-001` with deterministic
  evidence plans and known fallback posture.
- Rollback decisions are grounded in concrete compatibility criteria rather than
  assumptions that every migration is reversible.

Negative:

- No migration runtime, migration runner, or rollout action is performed in this issue.
- Forward-repair evidence is conceptual until implementation contexts add operational code,
  tests, and release runbooks.

## Related Documents

- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
