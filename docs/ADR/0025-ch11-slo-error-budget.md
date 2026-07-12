# ADR 0025: CH-11 SLO and Error-Budget Contract for OPS-SLO-001

## Status

Accepted for Phase 1 Closure child issue `#127`, implementation slice only.

## Date

2026-07-12

## Context

Issue `#127` is the `CH-11` child slice for `OPS-SLO-001` under issue `#39`.
Issue `#128` already established the merged `CH-10` metric names and current
repo-supported emission points in `docs/ADR/0024-ch10-production-metrics-contract.md`.
This `OPS-SLO-001` contract is explicitly downstream of `OPS-METRICS-001` and
reuses the `CTX5-SLO-EVID-001` evidence row.

`docs/ADR/0011-context4-backup-restore-drill.md` and
`docs/ADR/0012-context5-metrics-slos-watch.md` already define planning-only
restore, SLO, alert, and watch expectations. This slice converts that advisory
planning into a reviewed contract that:

- binds named SLOs to the existing `CH-10` metrics,
- defines threshold and error budget semantics,
- distinguishes executable now signals from advisory-only production proof,
- records release-blocking breach actions,
- and leaves issue `#39` open until later chunks provide dashboard, watch,
  restore-drill, and rollback-communications evidence.

The matrix row `OPS-SLO-001` remains `Open`, and issue `#39` remains open.

## Decision

`CH-11` is a documentation-and-guardrail contract slice only. It does not add
new runtime metrics, dashboards, alert routing, paging, first-hour watch
automation, restore tooling, or rollback communications execution.

This ADR uses two status labels:

- `Executable now`: the repo already emits the named `CH-10` metrics, so the
  threshold semantics and breach actions are a manual review contract today.
- `Advisory-only`: the threshold depends on production queue infrastructure,
  dashboard/query execution, restore proof, watch execution, or rollback
  communications that the repo does not yet implement.
- The burn policy remains manual review contract logic in this slice; no live
  budget-burn automation is added here.

## SLO Catalog

| SLO ID | CH-10 metric binding | Threshold semantics | Error budget semantics | Current repo status | Breach action now | Deferred closure |
|---|---|---|---|---|---|---|
| `OPS-SLO-BACKLOG-01` | `narratwin_ops_run_backlog_gauge`; planned queue signals `narratwin_ops_ingestion_queue_lag_seconds` and `narratwin_ops_ingestion_queue_depth` from ADR `0012` | Production target remains p95 queue lag `< 30s` every `5m`, watch condition at `> 60s` for `10m`, and no sustained backlog growth without run starts. Current repo executable now proxy is the durable backlog gauge only: monotonic backlog growth across three sampled checkpoints after one bounded recovery window is a breach. | Planned monthly budget remains `<= 1.5%` bad `5m` windows per `30d`. Queue-lag budget math is advisory-only until `CH-12`; backlog-gauge breach is release-blocking now. | Mixed: durable backlog gauge is executable now; queue-lag and queue-depth remain advisory-only because no production queue emitter exists. | Hold release posture at No-Go, require `CH-12` dashboard/query evidence before claiming backlog SLO enforcement, and keep issue `#39` reference-only/open. | `CH-12`, `CH-13` |
| `OPS-SLO-LEASE-01` | `narratwin_ops_lease_state_count`, `narratwin_ops_lease_staleness_seconds`, `narratwin_ops_lease_reacquire_total`, `narratwin_ops_stale_writer_reject_total` | Lease freshness target remains p95 staleness `< 20s`, stale count `= 0`, and critical at `> 45s` for two windows. Any stale-writer rejection on a critical mutator surface is an immediate breach. | Planned monthly budget remains `<= 0.5%` bad `5m` windows per `30d`. Any increment of `narratwin_ops_stale_writer_reject_total` on release-critical surfaces burns budget immediately. | Executable now for named emission points, but still a manual review contract rather than live burn automation. | Freeze rollout, require reviewed mitigation notes, and defer final route/watch proof to later ops chunks. | `CH-12`, `CH-13` |
| `OPS-SLO-IDEMP-01` | `narratwin_ops_idempotency_contract_drift_total`, `narratwin_ops_idempotency_replay_total`, `narratwin_ops_idempotency_terminal_replay_fail_total`, `narratwin_ops_stale_writer_reject_total` | Contract-drift breach remains rate `> 0.02/minute` over `10m`; terminal replay failure breach remains `> 1.0%` of accepted operations in `15m`. Any stale-owner/stale-writer rejection on a release-critical idempotent mutator path is critical. | Error budget is zero for unresolved terminal replay mismatch during release review. Live rate evaluation is advisory-only until `CH-12`; emitted replay and drift counters are executable now. | Mixed: emission points are executable now; production rate windows remain advisory-only without query execution. | Stop rollout, preserve No-Go posture, and require `CH-12` query evidence plus `CH-13` watch handling before claiming idempotency SLO closure. | `CH-12`, `CH-13` |
| `OPS-SLO-OUTBOX-01` | `narratwin_ops_outbox_backlog_count`, `narratwin_ops_outbox_age_seconds`, `narratwin_ops_outbox_redelivery_total` | Backlog warning remains `> 120`, critical `> 200` for `15m`; age warning remains `> 90s`, critical `> 180s`; redelivery breach remains `> 3x` 30d p95 baseline. | Planned monthly budget remains `<= 1.0%` bad `5m` windows per `30d`. Baseline comparison is advisory-only until dashboard/query support exists; critical backlog or age evidence is release-blocking now. | Mixed: backlog, age, and redelivery emission points are executable now; rolling-baseline math is advisory-only. | Block release progression, require reviewer signoff on recovery evidence, and defer alert/watch proof. | `CH-12`, `CH-13` |
| `OPS-SLO-RESTORE-01` | `narratwin_ops_restore_attempts_total`, `narratwin_ops_restore_duration_seconds`; planned readiness and backup-lag signals from ADR `0011` and ADR `0012` | Production target remains restore completion within `75m` for `95%` of scoped attempts, `RPO <= 5m`, and readiness `ready` at handoff checkpoints. Current repo only supports local restore-adjacent load attempts and durations; those signals do not prove production RTO/RPO. | Planned monthly budget remains `<= 5.0%` scoped restore-attempt misses per `30d`. This budget is advisory-only until `CH-14` produces restore drill evidence. | Advisory-only for production restore posture; the current local load metrics are executable now only as preflight warnings. | Do not claim restore readiness, keep `OPS-SLO-001` and `DUR-RESTORE-001` open, and require `CH-14` evidence before any restore-go claim. | `CH-14` |
| `OPS-SLO-ROLLBACK-01` | `narratwin_ops_rollback_block_total`; planned rollback owner/comms evidence from Context 6 | Any increment of `narratwin_ops_rollback_block_total{reason}` during reviewed rollback compatibility checks is an immediate breach. No tolerated unresolved rollback block exists for release review. | Error budget is zero for unresolved rollback blocks. Technical block counting is executable now; communications and freeze-window evidence remain advisory-only. | Mixed: technical rollback block signal is executable now; human communications and freeze-window proof are advisory-only. | Stop rollout, require rollback/no-rollback decision capture, and defer communications closure until `CH-15`. | `CH-15` |

## Burn Policy And Breach Actions

- Any `Critical` breach or unresolved release-blocking breach consumes budget
  immediately and preserves the No-Go posture.
- More than `50%` planned monthly budget burn in any `24h` window requires a
  documented review-owner escalation before additional release claims.
- The current repo has no live dashboard/query runner, alert route, or watch
  automation, so budget evaluation is a manual review contract backed by named
  `CH-10` metrics rather than automated burn-rate enforcement.
- This section is the reviewed burn policy for `OPS-SLO-001`; it records budget
  semantics but does not claim live production burn policy automation.
- `OPS-SLO-001` is not closed by this ADR. The contract is executable now only
  where current metrics exist and advisory-only where production proof is still
  missing.

## Explicit Deferrals

- `CH-12` remains responsible for dashboard/query evidence, alert routing, and
  tested severity ownership.
- `CH-13` remains responsible for first-hour watch execution, 120/180-minute
  checkpoints, and owner handoff evidence.
- `CH-14` remains responsible for successful restore drill evidence, production
  RTO/RPO proof, and restore-related closure data.
- `CH-15` remains responsible for rollback communications, freeze-window
  evidence, and human rollback proof.

## Consequences

- The repo can now honestly claim that `OPS-SLO-001` has a reviewed SLO and
  error-budget contract bound to the merged `CH-10` metric catalog.
- The repo cannot claim live production SLO enforcement, dashboard/query proof,
  alert routing, first-hour watch execution, production restore proof, rollback
  communications closure, or issue `#39` closure.
- The matrix row `OPS-SLO-001` remains `Open`, issue `#127` remains a narrow
  reference-only child slice, and issue `#39` remains open.

## Related Documents

- `docs/ADR/0011-context4-backup-restore-drill.md`
- `docs/ADR/0012-context5-metrics-slos-watch.md`
- `docs/ADR/0024-ch10-production-metrics-contract.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
