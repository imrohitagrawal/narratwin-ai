# ADR 0013: CH-01 Migration Baseline Runner for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#86`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. Planning for
`DUR-MIG-001` was completed in Context 3 through ADR `0010`, but the execution
strategy now requires an implementation chunk for `CH-01` before the ACID/CAS
storage kernel (`CH-02`) or any later runtime-state work can proceed.

This chunk needs a concrete, testable migration baseline that:

- is versioned,
- records applied revisions only after success,
- fails closed on tampered or out-of-order revision state,
- reflects the expand-first / forward-only posture from ADR `0010`,
- does not claim production rollout, down-migration safety, or storage-kernel
  semantics.

## Decision

Introduce a narrow migration-ledger runner in `backend/app/storage/migrations.py`.

### 1. Scope of the runner

The runner is an ordered revision ledger, not a production database migration
system. It provides:

- declared revision IDs,
- explicit `down_revision` ordering,
- `expand` and `contract` phases,
- persisted applied-revision history,
- idempotent replay for already-applied revisions,
- fail-closed validation for malformed or tampered ledger state.

It does not execute SQL DDL or own production rollout orchestration.

### 2. Persist-after-success contract

Applied migration state is written only after the revision's `apply` function
returns successfully.

If revision application raises an error:

- the revision is not recorded as applied,
- `currentRevision` is not advanced,
- later runs must replay from the last persisted good revision.

This preserves forward-repair posture and avoids false success evidence.

### 3. Ordered linear registry contract

For `CH-01`, the registry is intentionally linear and explicit:

- the first revision must have `down_revision = None`,
- each later revision must reference the immediately preceding revision,
- duplicate revision IDs are rejected,
- applied state must remain a prefix of the declared registry.

This keeps the baseline deterministic before broader storage/runtime branching
semantics arrive in later chunks.

### 4. Expand-first default

`contract` revisions are blocked by default and require explicit opt-in.

The baseline therefore encodes the advisory posture from ADR `0010`:

- expand-compatible work is the default,
- contract/destructive changes are not silently allowed,
- down-migration is not treated as the default safety path.

### 5. Local/test posture

The persisted migration ledger is local/test evidence only. It is intentionally
file-backed and does not claim:

- production PostgreSQL execution,
- Alembic environment wiring,
- schema lock management,
- mixed-worker rollout safety,
- rollback compatibility closure,
- release readiness.

Those remain owned by later chunks and rows, especially `CH-02` and `CH-09`.

## Non-Goals

- SQL DDL files or execution.
- Alembic environment bootstrapping.
- Runtime schema bootstrap in `backend/app/main.py`.
- Production database connectivity.
- ACID/CAS conflict handling for runtime metadata rows.
- Rollback-row closure for `DUR-ROLLBACK-001`.
- Stage 4/6/7 durable replay implementation.

## Consequences

Positive:

- `CH-01` now has executable evidence rather than planning-only guidance.
- Future chunks inherit a deterministic revision ledger and failure contract.
- Guardrails can bind a dedicated branch to the migration-baseline scope.

Negative:

- The runner is intentionally narrower than a full production migration system.
- Additional runtime work is still required before any production durability
  claim can move forward.

## Related Documents

- `docs/ADR/0010-context3-migrations-rollback-compatibility.md`
- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_storage_migrations.py`
