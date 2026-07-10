# ADR 0009: Context 2 Runtime Contracts for Issue #39 (Advisory Only)

## Status

Accepted (advisory) for planning in Issue `#66` (`DUR-IDEMP-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001`).

## Date

2026-07-10

## Context

Issue `#39` remains open for production-grade durability and monitoring.

Issue `#66` is the Context 2 decomposition work for:

- `DUR-IDEMP-001` (replay-safe idempotency),
- `DUR-LEASE-001` (cross-worker ownership control),
- `DUR-OUTBOX-001` (same-transaction event publication).

Context 1 fixed the durable boundary and replay-state model as a planning contract.
Context 2 now defines execution-order and failure-order semantics for durable
operations before any runtime implementation work.

Local/demonstration behavior is explicitly unchanged in this contract.

## Decision

This ADR defines advisory contracts only. It describes required semantics for
production-style idempotency, lease ownership, and outbox delivery; it does not
authorize runtime or DB code to be added in this issue.

### 1) Replay-safe idempotent execution contract (`DUR-IDEMP-001`)

Each request-bearing durable action must have an explicit operation identity and a
single canonical retry envelope:

- `operation_id`: stable identifier from API caller contract
- `scope`: canonical identity tuple of resource + tenant + actor
- `payload_hash`: canonicalized request payload hash used for collision defense
- `state`: durable operation lifecycle
- `version`: monotonic compare-and-set integer for replay conflict control

The canonical idempotency lookup key is `(operation_id, scope)`. The
`payload_hash` is a conflict guard for that key, not an independent dedupe key;
the `version` guards compare-and-set transitions after the record is found.

Allowed states:

| State | Allowed transitions | Replay behavior |
|---|---|---|
| `NEW` | `RUNNING` | only one writer starts execution; duplicate `NEW` requests with same `operation_id` and same hash become no-op reads |
| `RUNNING` | `TERMINAL_SUCCESS`, `TERMINAL_ERROR`, `REPLAYING`, `FAILED_TRANSIENT` | same writer may continue; failed execution with explicit terminal error moves to terminal states |
| `REPLAYING` | `TERMINAL_SUCCESS`, `TERMINAL_ERROR`, `FAILED_TRANSIENT` | active recovery/resume state for an in-flight or transiently failed operation before a terminal result is materialized |
| `TERMINAL_SUCCESS` | terminal | must return cached terminal output exactly for unchanged payload; caller-visible errors are not retried as successful replay |
| `TERMINAL_ERROR` | terminal | must return serialized terminal error shape for unchanged payload; unchanged caller receives the same terminal error and does not resume this operation |
| `FAILED_TRANSIENT` | `RUNNING`, `REPLAYING`, `TERMINAL_ERROR` | non-terminal failure before committed side effects; recovery requires explicit lease ownership handoff and compare-and-set transition |

Replay and failover behavior:

- Repeated request with same `operation_id` and same `scope`:
  - If transition is terminal, replay returns terminal materialized response/error
  - If transition is non-terminal but lease ownership changed, operation is retried only after explicit recovery ownership transfer
  - If `payload_hash` changes under same `operation_id`, response must be a
    dedicated conflict outcome (`IDEMPOTENCY_CONFLICT`), not silent success.
- Replays after worker crash/failover:
  - the winning writer may resume from `RUNNING` if lease token is valid and
    state is consistent
  - a stale writer must not commit or mutate terminal state
- Terminal/error/retry transitions are monotonic:
  - `NEW`/`RUNNING`/`REPLAYING` may become terminal
  - terminal states cannot transition back to active states in this ADR
  - `FAILED_TRANSIENT` is not terminal; if recovery cannot prove no committed
    side effects and valid ownership, it must become `TERMINAL_ERROR` or a new
    operation with a new `operation_id`
  - any transition outside this matrix is rejected with conflict and replay

Failure dedupe rule:

- For identical `(operation_id, scope, payload_hash)`, a second terminalization attempt must either be
  deduplicated to the existing terminal payload/error or rejected as replay of a
  terminal state.
- For identical `(operation_id, scope)` with conflicting `payload_hash`, fail with
  conflict and provide evidence of latest terminal state.

### 2) Lease ownership contract (`DUR-LEASE-001`)

Leases protect only one active writer per resource slice in concurrent execution.

Lease envelope:

- `resource_id`
- `lease_id` (owner identity)
- `lease_epoch` (monotonic fencing token)
- `acquired_at`
- `lease_ttl_ms`
- `expires_at`
- `heartbeat_at`

Acquire/renew/expiry behavior:

- `acquire`: succeeds only if no lease exists or the existing lease is expired;
  successful acquisition assigns `lease_id` to the caller, sets `acquired_at`,
  `heartbeat_at`, and `expires_at`, and increments `lease_epoch`
- `renew`: requires current `lease_epoch` and owner identity match; renewal keeps
  the same `lease_epoch` and updates `heartbeat_at` plus `expires_at`
- `expiry`: automatically valid at `expires_at`; stale owner loses effective
  rights immediately at expiry
- `abandon`: owner may voluntarily release before expiry; rights end at release

Fencing and stale owner prevention:

- Every successful ownership acquisition increments `lease_epoch`; renewal by the
  same owner does not increment the epoch.
- All state-mutating operations must include the caller’s current `lease_epoch`;
  if not equal to current record epoch, the commit is rejected as stale owner.
- Stale owners may continue local read-only operations but cannot perform durable
  writes or outbox publication.

Ownership transfer:

- On expiry, next caller may acquire with incremented epoch.
- Transfer is accepted only if stale writes are rejected by fencing checks.
- If transfer collides with in-flight work, contract requires caller to follow
  failure dedupe and replay paths, not forceful overwrite.

### 3) Outbox contract (`DUR-OUTBOX-001`)

All side effects visible outside the local process must have outbox participation:

1. In one durable operation path:
   - write durable target state,
   - write one or more outbox event rows in the same commit boundary.
2. Dispatch workers consume outbox rows asynchronously.
3. Dispatch is **at least once**:
   - duplicate dispatch attempts are expected and allowed.
4. Consumers must be idempotent:
   - dedupe by `(event_type, event_id, consumer_name, resource_version)` or
     equivalent deterministic key
   - repeated delivery of same logical message must preserve final system state.

Outbox row envelope:

- `event_id`
- `event_type`
- `resource_id`
- `resource_version`
- `operation_id`
- `payload_hash`
- `state`
- `attempt_count`
- `next_attempt_at`
- `locked_by`
- `locked_until`
- `last_error`
- `created_at`
- `updated_at`

Outbox row states:

| State | Meaning | Transition rule |
|---|---|---|
| `PENDING` | recorded, not yet dispatched | generated by same transaction as durable state transition; may transition to `DELIVERING` when a dispatcher acquires it |
| `DELIVERING` | in-flight dispatch attempt | may transition to `SUCCEEDED`, `FAILED`, or back to `PENDING` when `locked_until` expires for retry |
| `SUCCEEDED` | confirmed by consumer outcome | terminal for that dispatch row |
| `FAILED` | bounded retry exhausted without success | terminal until explicit remediation resets it to `PENDING` under a reviewed playbook |

Evidence of contract:

- Dispatcher/read/write boundaries must reference both operation state and event row.
- Consumer implementations are required to de-duplicate before action execution.

### 4) Deterministic evidence contract and non-goals

For this advisory contract, each `DUR-*` row must have deterministic test/evidence
mappings:

- Deterministic matrix entries and test names must be declared in the
  `Issue #39` closure plan before implementation.
- Evidence IDs for this planning context are `CTX2-IDEMP-EVID-001`,
  `CTX2-LEASE-EVID-001`, and `CTX2-OUTBOX-EVID-001`; follow-on implementation
  contexts must either implement the named tests from the closure plan or update
  the plan before writing runtime code.
- No runtime DB migrations, lock tables, queue implementations, worker
  middleware, queue/lease table execution code, endpoints, or provider/runtime
  behavior changes are covered by this ADR.
- Paid providers remain optional/disabled in local/dev/test defaults.
- Local and local-dev behavior remains non-production and unchanged by these contracts.

## Alternatives Considered

### Continue with Context 0 local snapshot semantics only

Rejected for production contexts because local snapshots do not provide
cross-worker lease fencing, durable replay contract proof, or durable outbox side-effect ordering.

### Permit unbounded exactly-once delivery promises

Rejected. At-least-once with strict consumer idempotency provides stronger
operational tractability under restarts and retries than a brittle exactly-once
assumption.

## Consequences

Positive:

- Issue `#66` now has an explicit contract baseline for idempotency replay,
  lease ownership, stale-owner protection, and outbox semantics before runtime code is written.
- Runtime implementation contexts can map their tests and evidence to explicit
  state-transition constraints.
- Product/runtime claims remain non-production until follow-on contexts satisfy
  implementation-stage gates.

Negative:

- No implementation evidence is added in this issue.
- Outbox/lease/idempotency runtime code remains pending by design.

## Related Documents

- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/STATUS.md`
