# ADR 0015: CH-04 Idempotency Semantics for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#97`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. Context 2
planning in ADR `0009` defined the advisory replay-safe idempotency contract for
`DUR-IDEMP-001`, and `CH-02` delivered the ACID/CAS row kernel in ADR `0014`.

`CH-04` must now add executable storage-kernel evidence for the idempotency
subset without absorbing adjacent chunks:

- no Stage 4/6/7 runtime integration,
- no lease acquire/heartbeat/expiry ownership transfer (`CH-05`),
- no committed outbox/event dispatch (`CH-06`),
- no issue `#39` closure or production-readiness claim.

The smallest reviewed contract for this chunk is:

- canonical `(operation_id, scope)` identity,
- `payload_hash` conflict guarding,
- deterministic terminal success replay,
- deterministic terminal error replay,
- stale-owner rejection fields compatible with later lease fencing,
- focused RED/GREEN evidence aligned with `CTX2-IDEMP-EVID-001`.

## Decision

Extend `backend/app/storage/postgres_state.py` with operation-level
idempotency semantics stored as operation-scoped durable rows inside the same
CH-02 record kernel. `CH-04` does not introduce a parallel durability store;
it reuses the shared row-versioning boundary while keeping the operation API
surface local to this chunk.

### 1. Canonical operation identity

Each durable operation record is keyed by:

- `operation_id`
- `scope.tenant_id`
- `scope.owner_id`
- `scope.project_id`
- `scope.resource_id`

This materializes the planning contract that idempotency identity is
`(operation_id, scope)`, while keeping `payload_hash` as a conflict guard rather
than a second dedupe key.

For CH-04, `scope.resource_id` is a canonical scoped row-identity string in the
same field order as the CH-02 durable row key:

- `entity_type:tenant_id:owner_id:project_id:entity_id`

Example:

- `run:tenant-1:owner-1:project-1:run-1`

The operation kernel rejects non-canonical `scope.resource_id` values and
rejects canonical resource IDs whose embedded tenant, owner, or project fields
do not match `OperationScope`.
`operation_id`, `payload_hash`, and `lease_owner_id` must also be non-empty so
identity, conflict guarding, and stale-owner checks cannot collapse to blank
values.

### 2. Executable state subset

`CH-04` implements only the minimal executable subset needed for the planned
evidence:

- `RUNNING`
- `FAILED_TRANSIENT`
- `REPLAYING`
- `TERMINAL_SUCCESS`
- `TERMINAL_ERROR`

The advisory `NEW` state from ADR `0009` remains deferred until runtime request
admission is wired. This chunk starts the durable record at `RUNNING` when the
first writer wins.

### 3. Terminal replay contract

If a later request presents the same `(operation_id, scope)` and matching
`payload_hash`, and the durable state is terminal:

- `TERMINAL_SUCCESS` replays the cached success payload exactly,
- `TERMINAL_ERROR` replays the cached serialized error exactly.
- exact terminal replay is read-only and may be returned across later lease
  owner / worker owner changes because it does not stage or mutate any durable
  row
- scoped `owner_id` remains part of `scope` and therefore remains part of the
  durable operation identity
- `request_id` is attempt metadata; it may differ across retries and does not
  replace `(operation_id, scope)` lookup identity or the required
  `payload_hash` replay guard

If a second terminalization attempt presents a different cached success/error
payload for the same durable terminal record, the kernel rejects it as a
conflict instead of silently overwriting the prior terminal materialization.

### 4. Conflict and stale-owner rules

If a later request reuses the same `(operation_id, scope)` with a different
`payload_hash`, the kernel raises a dedicated conflict rather than silently
accepting the new payload.

Mutating non-terminal transitions also persist:

- `lease_owner_id`
- `lease_epoch`

Every mutating non-terminal transition except reviewed recovery requires an
exact match on both fields. Mismatches are rejected as stale-owner writes.

`FAILED_TRANSIENT -> REPLAYING` is the one reviewed exception in `CH-04`:

- recovery may persist a same-owner epoch advance
- the durable `lease_owner_id` must remain unchanged in `CH-04`
- the new `lease_epoch` must be strictly greater than the durable epoch
- same-owner/same-epoch, cross-owner recovery, or non-advancing epochs are
  rejected

Cross-owner handoff remains deferred to `CH-05`, where durable lease transfer
and fencing evidence exist. This keeps CH-04 compatible with later reclaim
behavior without inventing unauthenticated ownership transfer ahead of the lease
lifecycle chunk.

### 5. Local/test posture

The operation kernel is executable local/test evidence only. It does not claim:

- runtime endpoint idempotency wiring,
- crash recovery ownership transfer,
- worker heartbeat or lease expiry,
- resource-row lease fencing for the operation-control row,
- the later combined runtime API that must atomically terminalize an operation,
  mutate a lease-guarded target resource, and publish outbox events,
- production PostgreSQL adapter behavior,
- side-effect ordering with committed outbox dispatch.

Those remain open until later chunks land and are reviewed.

## Non-Goals

- Lease lifecycle implementation (`CH-05`).
- Outbox persistence or dispatcher behavior (`CH-06`).
- Stage 4/6/7 route/service integration.
- Production migration or backup/restore closure.
- Issue `#39` matrix-row closure.

## Consequences

Positive:

- `CH-04` now has executable proof for terminal replay, payload-hash conflict,
  stale-owner rejection semantics, and explicit recovery handoff.
- Later chunks inherit one durable idempotency key and replay contract instead
  of redefining one per runtime path.
- Ownership transfer can extend the persisted `lease_owner_id` and
  `lease_epoch` fields without replacing the operation identity model.

Negative:

- Recovery remains intentionally narrow until `CH-05` introduces lease
  acquisition, expiry, and full fencing-transfer semantics.
- Runtime/API layers still need separate integration work before callers
  actually receive these semantics through Stage 4/6/7 endpoints.

## Related Documents

- `docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md`
- `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_postgres_state.py`
