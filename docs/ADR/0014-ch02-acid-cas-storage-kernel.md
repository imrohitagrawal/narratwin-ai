# ADR 0014: CH-02 ACID/CAS Storage Kernel for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#93`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. `CH-01`
completed the migration baseline in issue `#86` and PR `#87`, which satisfies
the execution-strategy prerequisite for `CH-02`.

`CH-02` must now add executable ACID/CAS storage-kernel evidence for
`DUR-ACID-001` without absorbing later chunks:

- no Stage 4 durable graph (`CH-03`)
- no idempotency, lease, or outbox runtime behavior (`CH-04` through `CH-06`)
- no backup/restore, monitoring, provider, media, or release-posture work

The kernel therefore needs to freeze only the smallest durable-write contract:

- stable identifiers per entity row
- monotonic versions
- explicit transaction identity
- replay-safe commit semantics
- stale-write rejection
- atomic multi-row validation before commit

## Decision

Introduce a storage-only ACID/CAS kernel in
`backend/app/storage/postgres_state.py`.

### 1. Scope of the kernel

The kernel is a PostgreSQL-compatible metadata contract, not a full database
adapter. It provides:

- transaction IDs and request IDs
- explicit request checksums for replay fingerprinting
- compare-and-set writes using expected versions
- atomic multi-row validation before any record becomes durable
- replay of an already committed transaction when the fingerprint matches
- stale-write rejection when a caller writes against an older durable version

It does not open database connections, execute SQL, bootstrap runtime schema, or
wire Stage 4/6/7 services yet.

### 2. Identifier and version contract

Each write names:

- `entity_type`
- `entity_id`
- `tenant_id`
- `owner_id`
- `project_id`
- `expected_version`

Durable row identity is the full scoped tuple:

- `(entity_type, tenant_id, owner_id, project_id, entity_id)`

Create semantics use `expected_version = None` and produce `version = 1`.
Update semantics require `expected_version` to match the current durable row
exactly before the kernel increments the version.

### 3. Replay and conflict contract

Transactions are keyed by `transaction_id`.

- Same `transaction_id` plus identical request fingerprint returns the original
  committed records as a replay.
- Same `transaction_id` with a different checksum or write set is rejected as a
  conflict.
- Missing-row updates or duplicate writes inside one transaction are conflicts.

This keeps replay behavior deterministic before later chunks introduce broader
idempotency ownership and cross-worker lease rules.

### 4. Stale-write contract

If a durable row exists at a higher version than the caller expects, the kernel
rejects the write as stale and commits nothing from that transaction.

If a row is already `TERMINAL` or `ERROR`, the kernel rejects additional writes
for that row. Recovery ownership remains deferred to later chunks.

### 5. Atomicity contract

All writes in one transaction are validated against the same pre-commit durable
view. If any write fails conflict or stale checks, none of the writes in that
transaction are committed.

This supplies the ACID/CAS kernel boundary needed before Stage 4 durable graph
and later runtime-state chunks reuse it.

## Non-Goals

- No Stage 4 entity graph persistence or resume semantics.
- No runtime idempotency, lease fencing, or outbox dispatch.
- No SQL DDL, driver wiring, or production database connectivity.
- No backup, restore, metrics, alerts, watch, provider, media, retention, or
  untrusted-input implementation.
- No issue `#39` closure or matrix-row closure.

## Consequences

Positive:

- `CH-02` gets executable conflict, replay, stale-write, and atomicity proof.
- Later chunks can build on one storage-kernel contract instead of inventing
  their own CAS behavior.
- Scope stays storage-only and does not pull Stage 4/6/7 runtime behavior
  forward.

Negative:

- Production runtime persistence is still incomplete until later chunks wire the
  kernel into durable entity flows.
- Cross-worker ownership, side effects, and operations evidence remain open.

## Related Documents

- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/ADR/0013-ch01-migration-baseline-runner.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_postgres_state.py`
