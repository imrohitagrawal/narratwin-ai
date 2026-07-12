# ADR 0024: CH-10 Production Metrics Contract for OPS-METRICS-001

## Status

Accepted for Phase 1 Closure child issue `#128`, implementation slice only.

## Date

2026-07-12

## Context

Issue `#128` is the `CH-10` child slice for `OPS-METRICS-001` under issue
`#39`. The execution strategy requires a narrow contract-and-emission slice:

- define the metric names and contract boundaries now,
- bind them to real runtime or executable restore/rollback-adjacent code paths
  where the repo can honestly emit them now,
- and keep final row closure blocked on later chunks.

`docs/ADR/0011-context4-backup-restore-drill.md` and
`docs/ADR/0012-context5-metrics-slos-watch.md` already define planning-only
metric expectations. They do not bind those names to executable code. This ADR
adds only the narrow executable contract the current repo can support without
claiming dashboards, alerting, first-hour watch, successful production restore
drills, rollback communications, or production-ready observability.

## Decision

`CH-10` is implemented as one shared metrics-contract helper plus emission
points in the existing storage/runtime boundaries that already exist in-repo:

- `backend/app/storage/postgres_state.py` for run backlog, lease, idempotency,
  and outbox signals.
- `backend/app/storage/file_state.py` for restore-adjacent local state load
  attempts and durations only.
- `backend/app/storage/migrations.py` for rollback block signals on reviewed
  rollback compatibility assertions.

The matrix row `OPS-METRICS-001` remains `Open`. This slice establishes contract
names and proves emission boundaries only.

## Metric Catalog

| Metric | Kind | Contract boundary now | Notes |
|---|---|---|---|
| `narratwin_ops_run_backlog_gauge{state}` | Gauge | ACID/CAS commits of durable `run` rows | Current repo can honestly emit durable run backlog only from `AcidCasKernel`; no production worker queue exists yet. |
| `narratwin_ops_lease_state_count{state}` | Gauge | Lease acquire, heartbeat, release | Current states are `active` and `stale`. |
| `narratwin_ops_lease_staleness_seconds{event}` | Histogram | Stale lease and stale-writer rejection paths | Current event label is `stale-rejection`. |
| `narratwin_ops_lease_reacquire_total{resource_type}` | Counter | Lease reacquire after expiry | Tracks durable lease reacquisition, not paging or incident handling. |
| `narratwin_ops_idempotency_contract_drift_total{surface}` | Counter | Payload-hash conflict against committed durable operation state | Covers conflict signals only. |
| `narratwin_ops_idempotency_replay_total{state}` | Counter | Durable replay against previously committed operation state | Gives a positive replay signal for `RUNNING`, `FAILED_TRANSIENT`, or terminal records. |
| `narratwin_ops_idempotency_terminal_replay_fail_total{surface}` | Counter | Terminal replay payload mismatch | Tracks terminal replay failure only. |
| `narratwin_ops_stale_writer_reject_total{surface}` | Counter | Owner, lease, lease-guard, and recovery-epoch stale rejections | Shared stale-owner/stale-writer rejection signal. |
| `narratwin_ops_outbox_backlog_count{state}` | Gauge | Outbox stage, acquire, retry, complete | Current states are `pending` and `delivering`. |
| `narratwin_ops_outbox_age_seconds{event_type,phase}` | Histogram | Outbox acquire, retry, complete | Measures durable outbox row age at those boundaries. |
| `narratwin_ops_outbox_redelivery_total{event_type}` | Counter | Outbox retry scheduling | Captures retry/redelivery attempts only. |
| `narratwin_ops_restore_attempts_total{surface,result}` | Counter | Local restore-adjacent `load_state` boundary only | This is not production backup/restore proof and does not satisfy `CH-14`. |
| `narratwin_ops_restore_duration_seconds{surface,result}` | Histogram | Local restore-adjacent `load_state` boundary only | Measures local state load time only, not production restore RTO. |
| `narratwin_ops_rollback_block_total{reason}` | Counter | Reviewed rollback compatibility assertion blocks | Technical rollback block signal only; rollback communications remain deferred to `CH-15`. |

## Explicit Scope Boundary

### In scope for issue `#128`

- metric names and label contracts,
- shared helper used by current storage/runtime surfaces,
- executable tests that prove emission points exist and fire,
- restore and rollback signals only at the current repo-supported contract
  boundaries.

### Out of scope for issue `#128`

- final SLO or error-budget closure (`CH-11`),
- dashboards, queries, alert routing, or paging (`CH-12`),
- first-hour watch execution (`CH-13`),
- successful production restore drill evidence, RTO, or RPO proof (`CH-14`),
- rollback communications or freeze-window evidence (`CH-15`),
- backup lag metrics, external scrape config, or production Go posture change.

## Consequences

- The repo can now honestly claim that `OPS-METRICS-001` has a concrete metric
  contract with real emission points for the currently implemented durability
  kernel, local restore-adjacent state loader, and rollback block boundary.
- The repo cannot claim complete operations monitoring. Queue-lag, backup-lag,
  dashboards, alerts, watch, production restore evidence, and rollback comms
  remain open.

## Related Documents

- `docs/ADR/0011-context4-backup-restore-drill.md`
- `docs/ADR/0012-context5-metrics-slos-watch.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_ops_metrics.py`
