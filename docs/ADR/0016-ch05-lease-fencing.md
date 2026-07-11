# ADR 0016: CH-05 Lease Fencing Kernel for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#95`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. `CH-02`
completed the ACID/CAS storage kernel in issue `#93` and PR `#94`.

`CH-05` must now add executable lease-fencing evidence for `DUR-LEASE-001`
without absorbing adjacent chunks:

- no `CH-04` idempotency semantics
- no `CH-06` committed outbox behavior
- no Stage 4/6/7 durable graph wiring
- no migrations, restore, monitoring, provider, media, or release-posture work

The contract therefore needs to freeze only the storage-kernel semantics for:

- lease acquire / heartbeat / expiry / reclaim
- monotonic fencing epoch advancement
- stale-writer rejection on lease-guarded mutations

## Decision

Extend `backend/app/storage/postgres_state.py` with a storage-only lease kernel
that composes with the existing ACID/CAS contract.

### 1. Lease scope

Leases are resource-scoped and intentionally generic. The kernel stores:

- `resource_id`
- `lease_id`
- `lease_epoch`
- `lease_ttl_ms`
- `acquired_at`
- `heartbeat_at`
- `expires_at`

`resource_id` is not an arbitrary caller label. It must use the canonical
durable row identity shape:

- `entity_type:tenant_id:owner_id:project_id:entity_id`

Example:

- `run:tenant-1:owner-1:project-1:run-1`

The lease API rejects non-canonical or partially empty identities so later
runtime workers cannot accidentally fence a different scope from the row they
intend to mutate.
Canonical means each identity part is already trimmed and non-empty;
whitespace-only or whitespace-padded fields are conflicts rather than alternate
lease scopes.
`lease_id` must be non-empty on acquire, heartbeat, release, and guarded writes.

The kernel remains PostgreSQL-compatible contract code only. It does not add SQL,
runtime worker orchestration, or Stage 4/6/7 service integration.

### 2. Acquire / heartbeat / expiry / reclaim semantics

- Acquire succeeds only when the resource has no active lease or the prior lease
  is expired.
- Every successful acquire increments the fencing epoch.
- Heartbeat requires matching owner and epoch, preserves the current epoch, and
  extends `expires_at` by the stored TTL.
- Expired leases immediately lose write authority.
- Lease expiry, stale-writer checks, and committed-at audit timestamps use the
  kernel-owned storage clock, not a caller-supplied timestamp. Tests may inject
  a deterministic kernel clock, but mutation callers cannot backdate lease
  authority or persisted commit time.
- Reclaim after expiry creates a new active lease with a higher epoch.
- Voluntary release removes the active lease while preserving the last epoch so
  the next acquire still increments monotonically.

### 3. Lease-guarded mutation contract

`TransactionWrite` may optionally carry:

- `lease_resource_id`
- `lease_id`
- `lease_epoch`

These fields are all-or-nothing. When present, the kernel validates the active
lease before any compare-and-set record staging happens:

- missing or partial lease guard fields are conflicts
- expired or missing lease ownership is stale
- mismatched epoch is stale
- mismatched owner is stale

This keeps stale writers from mutating durable rows even when their
`expected_version` would otherwise satisfy the ACID/CAS checks.

For this chunk, fencing becomes mandatory after a resource has entered the
lease-managed domain through acquisition. First creation of a never-leased row
does not itself create a lease requirement; runtime integration must decide
which user-facing paths require lease acquisition before creation.

Exact committed transaction replay remains the one reviewed exception:

- if `transaction_id`, `request_id`, `request_checksum`, and the full write
  fingerprint match a previously committed transaction exactly, the kernel may
  return the durable result without re-validating current lease ownership
- this replay path is read-only; it must not stage or mutate any row
- stale owners still lose authority for any fresh mutation attempt

### 4. Deterministic evidence

`CH-05` implementation evidence is limited to focused unit tests in
`tests/unit/test_postgres_state.py`:

- `test_context2_lease_renew_preserves_epoch_and_extends_expiry`
- `test_context2_lease_transfer_increments_epoch`
- `test_context2_lease_rejects_double_acquire_while_active`
- `test_context2_lease_rejects_non_canonical_resource_identity`
- `test_context2_lease_rejects_blank_lease_identity`
- `test_context2_lease_heartbeat_rejects_owner_mismatch`
- `test_context2_lease_rejects_stale_writer_epoch`
- `test_context2_lease_replays_guarded_transaction_after_lease_transfer`
  including replay fingerprint drift for lease fields
- `test_context2_lease_expiry_blocks_stale_owner_commit`
- `test_context2_lease_expiry_uses_kernel_clock_not_caller_timestamp`
- `test_context2_lease_commit_timestamp_uses_kernel_clock_not_caller_timestamp`
- `test_context2_lease_rejects_unrelated_live_lease_for_different_row`
- `test_context2_lease_rejects_unguarded_write_while_row_has_active_lease`
- `test_context2_lease_rejects_partial_fencing_tuple`
- `test_context2_lease_rejects_owner_mismatch_for_lease_guarded_write`
- `test_context2_lease_release_removes_active_lease_and_next_acquire_advances_epoch`
- `test_context2_lease_release_rejects_stale_owner`

These map directly to `CTX2-LEASE-EVID-001` in
`docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`.

## Non-Goals

- No runtime idempotency state machine or payload-hash semantics.
- No committed outbox rows, dispatch, or consumer dedupe.
- No Stage 4, Stage 6, or Stage 7 durable entity wiring.
- No SQL migrations, lock tables, or production database connectivity.
- No backup/restore, monitoring, alerts, watch, provider, media, retention, or
  release-readiness implementation.
- No issue `#39` closure or matrix-row closure.

## Consequences

Positive:

- `CH-05` gets executable proof for lease acquire/renew/expiry/reclaim and
  monotonic fencing behavior.
- Later runtime chunks can reuse one stale-writer fence instead of inventing
  service-local lease checks.
- Scope stays within the storage kernel and does not pull runtime orchestration
  forward.

Negative:

- Production worker coordination is still incomplete until later chunks add
  idempotency, outbox, and service wiring.
- Monitoring, restore, and release evidence remain open.

## Related Documents

- `docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md`
- `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_postgres_state.py`
