# Issue #39 CH-04/CH-05/CH-06 Contract Decisions

## Status

Accepted for Phase 1 Closure planning and review evidence.

## Date

2026-07-11

## Scope

This record freezes the reviewed contract choices for the parallel `CH-04`,
`CH-05`, and `CH-06` issue `#39` chunks. It does not close issue `#39`, does
not claim production readiness, and does not authorize Stage 4/6/7 runtime
integration.

## Decision Table

| Question | Selected decision | Why this is the right Phase 1 choice | Main loophole to watch | Reviewer acceptance criteria |
|---|---|---|---|---|
| Can terminal idempotency replay cross worker-owner changes? | Yes, exact terminal replay is read-only and lease-owner-agnostic. Scope `owner_id` remains part of durable operation identity and cannot change. | A finished answer is immutable history. Returning the cached success/error does not create work, change state, or grant write authority. This supports retries after worker failover without widening tenant/owner/project scope. | A replay path could accidentally mutate state, skip payload-hash checks, treat a different logical operation as the same operation, or confuse lease owner with scoped owner. | Terminal replay lookup must use `(operation_id, scope)`, then require matching `payload_hash` and exact terminal payload equality; `request_id` may differ because it identifies an attempt, not the durable replay identity; mutating non-terminal transitions remain stale-owner guarded. |
| Must CH-04 operation state use the CH-02 kernel? | Yes, operation rows are stored through the shared ACID/CAS row kernel. | Later chunks need one transaction boundary for durable state, idempotency state, and outbox publication. A parallel operation store would force coordination bugs. | A helper may write directly to operation storage and bypass transaction replay metadata. | Operation persistence must route through `commit(...)`/`TransactionWrite` semantics or an equivalent shared transaction path, not a separate operation store. |
| Must every first write have a lease token? | No. CH-05 makes fencing mandatory after a resource enters the lease-managed domain. | Creation and worker assignment are different lifecycle moments. Requiring leases before a resource is lease-managed pulls runtime orchestration into this storage chunk. | A runtime path could forget to acquire a lease before updates that should be worker-owned. | Once a resource has a lease epoch, unguarded mutations fail; stale owner, stale epoch, expired lease, and partial lease tuples fail. |
| Who controls lease and dispatcher expiry time? | The storage kernel controls expiry time; tests may inject a deterministic kernel clock. | Expiry is an authority boundary. If mutation callers can backdate `now`, stale workers can revive expired leases or dispatcher locks. | Test-only clocks could leak into production wiring as caller-controlled timestamps. | Lease and outbox ownership expiry checks must use a kernel-owned clock, not per-call caller timestamps. |
| Can exact committed transaction replay succeed after lease transfer? | Yes, if the replay fingerprint is exact and read-only. | A retry of an already committed transaction must be able to return the durable result even after ownership changes. It does not create a new mutation. | A replay path could ignore changed lease fields or restage writes under a stale owner. | Replay must require exact transaction identity and full fingerprint, including lease fields, and must return before staging or mutating rows. |
| Does CH-06 re-implement CH-05 lease fencing? | No. CH-06 proves atomic state-plus-event and outbox dispatch semantics; lease authorization composes at integration time. | The execution strategy allows CH-04/05/06 to run in parallel after CH-02. That only works if CH-06 does not absorb CH-05. | A later runtime integration could call CH-06 state+event writes without first enforcing the relevant lease policy. | CH-06 must document lease fencing as a non-goal and later integration must combine CH-05 fencing with CH-06 state/event writes. |
| What is the consumer dedupe identity? | `(event_type, resource_id, event_id, consumer_name, resource_version)`. | `event_id` alone can collide across tenants/resources. Including `resource_id` preserves scoped row identity and prevents cross-resource false duplicates. | Callers could record dedupe before a real dispatch or after a stale/expired dispatch. | Consumer delivery recording requires a committed event identity match and active dispatcher ownership; stale, expired, pending, and superseded dispatches fail. |

## Assumptions

- These decisions are storage-kernel contract decisions only.
- Idempotency lookup identity is `(operation_id, scope)`. `payload_hash` is a
  required conflict/replay guard, and `request_id` is attempt metadata rather
  than a replay key.
- Canonical durable resource identity is
  `entity_type:tenant_id:owner_id:project_id:entity_id`. Each component is
  non-empty and colon-free. Lease resource IDs and outbox resource IDs use this
  exact shape.
- Operation IDs, payload hashes, lease owners, lease IDs, outbox event IDs,
  event types, operation IDs, dispatcher IDs, and consumer names are non-empty
  durable identities.
- Paid providers remain optional and disabled for local, test, and CI paths.
- Uploaded documents, prompts, transcripts, and provider outputs remain
  untrusted input and must not influence durable identity without validation.
- `CH-04`, `CH-05`, and `CH-06` stay independently reviewable because the
  execution strategy marks them parallel after completed `CH-02`.
- Later Stage 4/6/7 runtime work must compose these contracts explicitly
  instead of relying on service-local best effort checks.

## Rejected Alternatives

### Owner-gated terminal replay

Rejected for Phase 1 because it treats immutable replay like a write. It blocks
legitimate failover: a replacement worker could not retrieve a cached terminal
result even though no durable state would change. This rejection applies to
lease owner / worker owner, not to scoped `owner_id`; scoped owner remains part
of the operation identity.

### Lease required before first-ever write

Rejected for this chunk because it merges creation semantics with worker
assignment semantics. It is valid for a stricter future runtime policy, but
`CH-05` only owns the storage proof that lease-managed resources reject stale
or unguarded mutations.

### CH-06 duplicates CH-05 lease checks

Rejected because it breaks the planned parallel chunk boundary. CH-06 must prove
that state and outbox rows commit atomically and dispatch at least once; lease
authorization remains the CH-05 contract and must be composed by later runtime
integration.

### Dedupe by event ID without resource identity

Rejected because scoped tenants/projects can legitimately reuse the same event
identifier string. The dedupe key must include `resource_id` to avoid
cross-resource suppression.

## Required Evidence

- `CH-04` tests must cover payload-hash conflict, terminal success replay,
  terminal error replay, terminal replay across changed lease owner/epoch,
  terminal payload drift rejection, stale-owner rejection for non-terminal
  paths, and operation storage through the shared row kernel.
- `CH-05` tests must cover acquire, heartbeat, release, expiry, reclaim,
  monotonic epoch advancement, canonical resource ID validation, mandatory
  fencing after lease creation, exact replay after transfer, and fingerprint
  drift for lease fields.
- `CH-06` tests must cover same-transaction state/event write, duplicate event
  rollback, payload/hash binding to the staged durable row, outbox replay
  fingerprint drift, at-least-once redelivery, active dispatcher ownership,
  stale dispatch rejection, and scoped consumer dedupe with same-event-id
  cross-resource collisions.

## Combined Kernel Composition Contract

When the chunk branches are composed after review, the shared storage-kernel
transaction API must preserve one transaction boundary:

- `TransactionWrite` may carry lease guard fields when a row is lease-managed.
- `commit(...)` may carry outbox events that reference staged durable rows.
- Operation rows created by `CH-04` are idempotency-control rows for a target
  resource. `CH-05` resource leases fence the target durable resource row; they
  do not implicitly fence the operation-control row by operation row identity.
- Later runtime integration that changes a lease-managed resource, publishes an
  outbox event, and terminalizes an idempotent operation must expose one atomic
  storage operation that writes all three participants together: operation row,
  lease-guarded resource row, and outbox event row. These chunks deliberately
  stop short of that runtime API so they remain parallelizable.
- The transaction replay fingerprint must cover request identity/checksum, each
  durable write, all lease guard fields, and each outbox event's identity,
  resource version, payload, and payload hash.
- CH-06 does not reimplement CH-05 fencing, but any later runtime path that
  writes lease-managed state and publishes outbox events must call the combined
  lease-guarded state-plus-event transaction path.

## Follow-Up Boundaries

- Stage 4/6/7 runtime integrations must prove that user-facing mutation paths
  invoke the CH-05 lease policy before committing CH-06 state/event writes.
- Production migrations, SQL adapter behavior, operational metrics, restore,
  provider posture, media consent, and retention remain later issue `#39`
  chunks.
- Issue `#39` remains open until every production closure matrix row has
  concrete reviewed evidence.
