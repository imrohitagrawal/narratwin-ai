# ADR 0017: CH-06 Committed Outbox for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#96`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. `CH-02`
completed the ACID/CAS storage kernel in issue `#93` and PR `#94`, which
provides the transaction boundary that `CH-06` now extends.

`CH-06` must add executable committed-outbox evidence for `DUR-OUTBOX-001`
without absorbing neighboring chunks:

- no durable API idempotency semantics (`CH-04`)
- no lease fencing or heartbeat ownership (`CH-05`)
- no Stage 4, Stage 6, or Stage 7 runtime integration work
- no migrations, restore, monitoring, provider, media, or release-posture work

The smallest contract needed here is:

- same-transaction durable state and outbox-event writes
- explicit outbox dispatcher acquire, retry, success, and fail transitions
- at-least-once redelivery after lock expiry
- deterministic consumer dedupe primitives

## Decision

Extend `backend/app/storage/postgres_state.py` with a storage-only committed
outbox contract layered on top of the existing ACID/CAS kernel.

### 1. Transactional state and outbox writes

The kernel commit path now accepts outbox-event writes in addition to durable
state writes.

Each outbox event must:

- have a stable `event_id`
- reference the same scoped durable row identity as a staged state write, using
  `entity_type:tenant_id:owner_id:project_id:entity_id`
- use non-empty and colon-free scoped identity fields
- bind to the staged durable `resource_version`
- carry the same payload as the staged durable row
- carry the canonical payload hash for that payload
- be committed in the same transaction result as the state row

If any outbox event is invalid, neither the state row nor the outbox row is
committed.

### 2. Dispatcher state transitions

Committed outbox rows use these states:

- `PENDING`
- `DELIVERING`
- `SUCCEEDED`
- `FAILED`

Dispatcher transitions are storage-kernel primitives only:

- `acquire_outbox_events(...)` moves eligible rows from `PENDING` to
  `DELIVERING`
- expired `DELIVERING` rows may be acquired again, which provides
  at-least-once redelivery
- dispatcher lock expiry and consumer-delivery ownership checks use the
  kernel-owned storage clock, not caller-supplied timestamps
- `retry_outbox_event(...)` moves a dispatcher-owned row back to `PENDING`
  with a new `next_attempt_at`
- `mark_outbox_event_succeeded(...)` moves a dispatcher-owned row to terminal
  `SUCCEEDED`
- `mark_outbox_event_failed(...)` moves a dispatcher-owned row to terminal
  `FAILED`

This chunk does not add cross-worker lease fencing; dispatcher ownership here is
limited to the row-level lock metadata required for outbox retries.

### 3. Consumer dedupe primitive

The kernel now records consumer-delivery attempts by deterministic key:

- `(event_type, resource_id, event_id, consumer_name, resource_version)`

`record_consumer_delivery(...)` returns whether the attempted delivery is a
duplicate and increments the observed delivery count for that key.

This is a storage primitive for idempotent consumers. It requires a committed
event identity match and active dispatcher ownership; pending, expired,
superseded, or terminal-failed dispatches cannot pre-seed consumer dedupe. It
does not execute the consumer side effect itself.

Outbox `event_id`, `event_type`, `operation_id`, dispatcher ID, and consumer
name must be non-empty so ownership and dedupe keys cannot collapse to blank
identities.

### 4. Evidence contract

`CH-06` adds focused `CTX2-OUTBOX-EVID-001` proof in
`tests/unit/test_postgres_state.py`:

- `test_context2_outbox_writes_state_and_event_atomically`
- `test_context2_outbox_rejects_forged_payload_or_hash`
- `test_context2_outbox_rejects_duplicate_events_in_same_transaction_atomically`
- `test_context2_outbox_rejects_non_canonical_resource_identity`
- `test_context2_outbox_replays_committed_transaction_without_duplicate_events`
  including outbox replay fingerprint drift
- `test_context2_outbox_redelivery_is_at_least_once`
- `test_context2_outbox_rejects_wrong_dispatcher_transition`
- `test_context2_outbox_rejects_blank_dispatcher_and_consumer_identity`
- `test_context2_outbox_scopes_duplicate_event_ids_by_resource_identity`
- `test_context2_outbox_consumer_dedupe_scopes_same_event_id_by_resource_identity`
- `test_context2_outbox_consumer_dedupes_duplicate_delivery`
- `test_context2_outbox_consumer_delivery_requires_matching_committed_event`
- `test_context2_outbox_consumer_delivery_rejects_expired_or_superseded_dispatch`
- `test_context2_outbox_marks_dispatch_failure_terminal`
- `test_context2_outbox_rejects_transition_after_lock_expiry`
- `test_context2_outbox_lock_expiry_uses_kernel_clock_not_caller_timestamp`
- `test_context2_outbox_rejects_transition_at_exact_lock_expiry`

An additional terminal-failure regression covers the explicit dispatcher fail
transition without widening scope beyond the kernel contract.

## Non-Goals

- No durable request identity or terminal replay semantics beyond transaction
  replay; `CH-04` still owns API-level idempotency behavior.
- No fencing token, heartbeat renewal, expiry ownership transfer, or
  stale-writer rejection beyond outbox row ownership checks; `CH-05` still owns
  lease semantics.
- No queue worker, middleware, network dispatcher, or external side-effect
  integration.
- No SQL DDL, driver wiring, migrations, or production database connectivity.
- No issue `#39` closure or matrix-row closure.

## Consequences

Positive:

- `CH-06` turns the advisory outbox contract from ADR `0009` into executable
  kernel-level proof.
- Later runtime chunks can reuse one transactional state-plus-event boundary
  instead of inventing side-effect ordering ad hoc.
- At-least-once redelivery and consumer dedupe rules are now explicit and
  test-backed before runtime integrations begin.

Negative:

- Durable outbox rows are still in-memory kernel objects, not SQL-backed
  production state.
- Cross-worker lease fencing and API idempotency remain open in `CH-05` and
  `CH-04`.

## Related Documents

- `docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md`
- `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_postgres_state.py`
