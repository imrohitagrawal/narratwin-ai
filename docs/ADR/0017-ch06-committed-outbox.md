# ADR 0017: CH-06 Committed Outbox Kernel for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#96`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. `CH-02`
completed the ACID/CAS storage kernel in issue `#93`; `CH-04` completed
storage-kernel idempotency semantics in issue `#97`; `CH-05` completed
storage-kernel lease fencing in issue `#95`.

`CH-06` implements only the committed outbox subset for `DUR-OUTBOX-001`:

- same-transaction durable state and outbox event writes,
- outbox row envelope and replay fingerprinting,
- at-least-once dispatch acquisition/retry semantics,
- idempotent consumer-delivery recording.

It must not absorb Stage 4 durable graph wiring, CH-03 runtime state graph,
lease lifecycle semantics, operation idempotency semantics, provider/media
behavior, backup/restore, operations monitoring, or final issue `#39`
disposition work.

## Source Facts

| ID | Source | Fact used | Design impact | Status |
|---|---|---|---|---|
| SRC-OUTBOX-001 | `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md` | Outbox rows are written in the same commit boundary as durable target state; dispatch is at least once; consumers dedupe by scoped deterministic key. | `commit(...)` accepts outbox events and stores them only after all staged state writes validate. | pass |
| SRC-OUTBOX-002 | `docs/ADR/0014-ch02-acid-cas-storage-kernel.md` | The shared kernel is the transaction boundary for durable row versions, replay fingerprints, and stale-write rejection. | CH-06 extends the shared kernel instead of adding a parallel outbox store. | pass |
| SRC-OUTBOX-003 | `docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md` | CH-06 does not reimplement CH-05 lease fencing; dispatcher expiry uses the kernel clock; consumer dedupe identity is `(event_type, resource_id, event_id, consumer_name, resource_version)`. | Outbox tests focus on state/event atomicity, dispatch locks, stale dispatch rejection, and scoped dedupe without lease acquisition changes. | pass |

## Decision

Extend `backend/app/storage/postgres_state.py` with storage-only outbox
semantics that reuse the CH-02 transaction boundary.

### 1. Outbox event write contract

`TransactionWrite` remains the durable state mutation primitive. CH-06 adds an
outbox event envelope that may be supplied to `commit(...)` in the same call as
state writes.

Each outbox event records:

- `event_id`
- `event_type`
- `resource_id`
- `resource_version`
- `operation_id`
- `payload_hash`
- `payload`
- dispatch state, attempt, lock, and error metadata
- created and updated timestamps from the kernel-owned clock

`payload_hash` is the canonical SHA-256 hash of the event payload encoded as
sorted compact JSON. The event must bind to a durable state row staged in the
same `commit(...)` call; CH-06 does not allow appending an outbox event to a
previously committed row without a same-transaction state transition.

Outbox `resource_id` must use the canonical durable row identity shape:

`entity_type:tenant_id:owner_id:project_id:entity_id`

The `resource_version` must match the version of a durable row staged in the
same transaction. This binds the event to the state it describes and prevents
event-only side effects from claiming a previously committed resource version.

### 2. Same-transaction atomicity

If any durable state write or any outbox event fails validation, neither state
nor event rows are committed. Duplicate event identity inside one transaction,
duplicate event identity across committed history, conflicting transaction
replay fingerprints, and events that do not match a same-transaction staged
resource version all fail closed.

Exact committed transaction replay remains read-only and returns the prior state
records plus the prior event rows. A changed outbox event payload, payload hash,
identity, or resource binding under the same `transaction_id` is rejected as a
conflicting replay.

### 3. Dispatch state machine

Dispatch is at least once. The kernel stores row state and ownership, not an
external queue runtime:

- `PENDING` rows can be acquired by a dispatcher and become `DELIVERING`.
- `DELIVERING` rows can be completed as `SUCCEEDED`, retried as `PENDING`, or
  terminalized as `FAILED` only with the current `lock_token`.
- Expired `locked_until` allows reclaim to a new `lock_token`.
- Stale dispatchers cannot complete or retry a row after expiry/reclaim even if
  they use the same dispatcher name.

The kernel-owned clock controls dispatch expiry checks.

### 4. Idempotent consumer policy

Consumer delivery recording dedupes by:

`(event_type, resource_id, event_id, consumer_name, resource_version)`

Delivery recording requires an actively owned `DELIVERING` event with the
current `lock_token`. Duplicate delivery with the same scoped key returns the
existing consumer record without repeating consumer action. Same `event_id`
values on different resources remain separate.

## Invariant-To-Test Matrix

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| OUTBOX-ATOMIC-001 | Transaction boundary | Durable state and outbox events commit in one kernel transaction, and replay returns both without restaging. | State can commit while event write is lost, making external side effects invisible after restart. | `test_context2_outbox_writes_state_and_event_atomically` | `test_context2_outbox_rolls_back_state_when_event_identity_is_duplicate`; RED confirmed before implementation because `commit(...)` had no `outbox_events` argument. | `uv run pytest tests/unit/test_postgres_state.py -k outbox` | Runtime/state | pass |
| OUTBOX-BIND-001 | Event binding | Outbox event resource/version/payload hash matches the same-transaction durable row version it describes. | A valid event row can point at a stale or unrelated resource version while tests only assert event existence. | `test_context2_outbox_binds_event_to_staged_resource_payload` | `test_context2_outbox_rejects_unmatched_resource_version`; `test_context2_outbox_rejects_event_without_same_transaction_state_change`; `test_context2_outbox_rejects_payload_hash_that_does_not_match_payload`; RED confirmed before implementation because no event binding API existed, and reviewer-added RED tests reproduced same-transaction and hash-binding false-pass risks before the fix. | `uv run pytest tests/unit/test_postgres_state.py -k outbox` | Runtime/state | pass |
| OUTBOX-REPLAY-001 | Replay fingerprint | Transaction replay fingerprint includes outbox event identity, payload, payload hash, and resource version. | Same transaction ID can replay with a changed event and falsely appear idempotent. | `test_context2_outbox_replays_committed_state_and_event` | `test_context2_outbox_rejects_replay_when_event_payload_changes`; RED confirmed before implementation because no outbox fingerprint was present. | `uv run pytest tests/unit/test_postgres_state.py -k outbox` | Runtime/state | pass |
| OUTBOX-DISPATCH-001 | At-least-once dispatch | Dispatch acquire/retry supports redelivery and increments attempt count without exactly-once claims. | Failed dispatch could be treated as terminal loss or duplicate delivery could be suppressed before consumer success. | `test_context2_outbox_redelivery_is_at_least_once` | `test_context2_outbox_rejects_stale_dispatch_completion_after_reclaim`; RED confirmed before implementation because no dispatcher state machine existed. | `uv run pytest tests/unit/test_postgres_state.py -k outbox` | Runtime/integration | pass |
| OUTBOX-CONSUMER-001 | Consumer dedupe | Consumer delivery dedupes by event type, resource ID, event ID, consumer name, and resource version. | Dedupe by event ID alone suppresses different resources or accepts duplicate action after replay. | `test_context2_outbox_consumer_dedupes_duplicate_delivery` | `test_context2_outbox_consumer_dedupe_keeps_same_event_id_cross_resource_separate`; RED confirmed before implementation because no consumer delivery record existed. | `uv run pytest tests/unit/test_postgres_state.py -k outbox` | Runtime/integration | pass |
| NONGOAL-OUTBOX-001 | Scope | CH-06 does not implement Stage 4 graph, lease lifecycle, provider/media side effects, operations metrics, or final issue `#39` closure. | A narrow outbox PR could overclaim production readiness or close `#39`. | N/A | N/A | `docs/STATUS.md`, PR body, and reference-only merge message keep `Refs #39` posture. | Governance | pass |
| HUMAN-OUTBOX-001 | Merge wording | Final merge/squash text remains reference-only for `#39`. | CI cannot inspect text typed into the final merge dialog before merge. | N/A | N/A | Human-only owner: repo owner; residual risk accepted for PR only with no issue-closing keyword. | Governance | pass |

## Review Prompt Set

Use these review prompts after implementation:

1. Guardrail/security bypass risk: verify no secrets, provider enablement,
   untrusted payload trust expansion, issue-closing wording, or release
   overclaim entered the diff.
2. Process/CI/regression risk: verify the PR evidence includes preflight,
   old-behavior RED proof, validation results, human-only merge wording, and
   no weakened Phase 1 closure gate.
3. Test quality and false-pass coverage: verify each `OUTBOX-*` matrix row has
   positive and negative tests that would fail under the previous no-outbox
   kernel and that tests assert state, not private implementation calls.
4. Architecture/state review: verify state rows and outbox rows share one
   transaction boundary, dispatch ownership is lock-token fenced, at-least-once
   semantics are explicit, and consumer dedupe is scoped.

## Stop Rule

Stop implementation and update this ADR before another code patch if review
finds any new defect class in:

- transaction atomicity,
- event/resource binding,
- dispatch ownership/fencing,
- consumer dedupe scope,
- issue `#39` reference-only posture,
- or CH-06 scope boundaries.

Two distinct blocker classes after green local checks require a contract reset
and re-review before further implementation.

## Non-Goals

- No Stage 4/6/7 runtime service integration.
- No production SQL adapter, worker, external queue, metrics, dashboard, alert,
  backup, restore, or release enablement.
- No paid-provider calls, real provider keys, media export, consent/provenance,
  retention, or untrusted-input closure.
- No issue `#39` closure or `DUR-OUTBOX-001` row closure.

## Consequences

Positive:

- `CH-06` gets executable proof for committed outbox state/event atomicity,
  at-least-once dispatch, stale dispatcher rejection, and scoped consumer
  dedupe.
- Later runtime chunks can compose CH-04 idempotency, CH-05 lease fencing, and
  CH-06 outbox rows through one storage-kernel transaction boundary.

Negative:

- Production runtime outbox workers and operations monitoring remain open.
- The matrix row `DUR-OUTBOX-001` remains open until final issue `#39`
  closure evidence is recorded.

## Related Documents

- `docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md`
- `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/ADR/0015-ch04-idempotency-semantics.md`
- `docs/ADR/0016-ch05-lease-fencing.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_postgres_state.py`
