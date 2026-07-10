# ADR 0012: Operations Metrics, SLOs, Alerts, and First-Hour Watch for Issue #39 Context 5 (Advisory Only)

## Status

Accepted for planning in Issue `#69`, advisory only.

## Date

2026-07-10

## Context

Issue `#39` remains open and partially remediated for production durability and
release readiness. Context 5 is the planning-only operations contract for
`OPS-METRICS-001`, `OPS-SLO-001`, `OPS-ALERT-001`, and `OPS-WATCH-001`.

This context is advisory-only planning for Issue `#69` and binds all monitoring,
SLO, alerting, and first-hour watch requirements to concrete evidence IDs and
failure-mode coverage. It does not permit runtime metric pipelines, alert
integrations, dashboards, or watch automation code in this phase.

## Decision

Context 5 will produce a testable operations planning contract that:

- defines one metric catalog and one failure-mode mapping per ID,
- defines failure thresholds and error-budget boundaries for production handoff,
- defines routing, on-call ownership, acknowledgment SLA, and closure evidence,
- defines first-hour handoff and 120/180-minute follow-up watch checkpoints,
- and explicitly defers all runtime runtime implementation.

### 1) Operations failure-mode → metric catalog

The tables below are explicit planning contracts only.

#### 1.1 Queue and worker pressure

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Queue buildup blocks ingestion/run progress | `narratwin_ops_ingestion_queue_lag_seconds` | Stage 4 queue/state planner instrumentation | Trigger when p95 queue lag exceeds 30s for 5m; treat 60s sustained as watch condition. |
| Queue depth starved despite workers available | `narratwin_ops_ingestion_queue_depth` | Ingestion scheduler | Trigger when 5m average depth remains > 500 without dequeue rate improvement; treat as medium-severity if sustained and high. |
| Run backlog stalls | `narratwin_ops_run_backlog_gauge` | Run lifecycle state store | Trigger when backlog grows and no `RUN-START` events are observed for 10m. |

#### 1.2 Lease state and ownership safety

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Stale leases block progress | `narratwin_ops_lease_state_count{state}` | Lease owner table | Trigger when `state="stale"` gauge > 0 for 2 consecutive checks. |
| Lease renewal starvation | `narratwin_ops_lease_staleness_seconds` | Lease heartbeat contract | Trigger when p95 staleness > 20s for 10m. |
| Lease transfer thrash | `narratwin_ops_lease_reacquire_total` | Lease owner transitions | Trigger when acquires per lease_id exceed 3/minute for 15m and progress is flat. |

#### 1.3 Idempotency and contract drift

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Contract-drift payload conflicts | `narratwin_ops_idempotency_contract_drift_total` | Idempotency state contract validation | Trigger when rate > 0.02 per minute over 10m. |
| Non-terminal replay mismatch | `narratwin_ops_idempotency_terminal_replay_fail_total` | Idempotency terminal transitions | Trigger when ratio of terminal replay failures to accepted operations exceeds 1.0% in 15m. |
| Stale writer writes | `narratwin_ops_stale_writer_reject_total` | Lease + idempotency writer validation | Trigger when any stale-writer rejection occurs in critical mutator surface. |

#### 1.4 Outbox and durable side effects

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Outbox backlog blocks durability progress | `narratwin_ops_outbox_backlog_count` | Outbox persistence and dispatch state | Trigger when backlog > 200 for 20m. |
| Outbox stuck age | `narratwin_ops_outbox_age_seconds` | Outbox oldest row age | Trigger when p95 age > 120s for 15m. |
| Dispatch idempotency drift | `narratwin_ops_outbox_redelivery_total` | Outbox/dispatch worker | Trigger when redelivery spike exceeds 3x 95th-percentile baseline over 30m. |

#### 1.5 Restore, rollback, and watch readiness

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Restore readiness unknown | `narratwin_ops_restore_readiness_state` | Restore readiness marker | Trigger when state is not `ready` at handoff review checkpoints. |
| Restore attempt stall | `narratwin_ops_restore_duration_seconds` | Restore run marker | Trigger when in-progress attempt exceeds 75m and remains incomplete. |
| Watch escalation backlog | `narratwin_ops_watch_escalation_count` | Watch log ingestion | Trigger when 120m checkpoint has unresolved `high` or `critical` items. |

#### 1.6 Ownership, state, and evidence integrity

| Failure mode | Metric | Source | Contract |
|---|---|---|---|
| Missing watch evidence | `narratwin_ops_watch_log_incomplete_total` | Watch log completeness check | Trigger when evidence gaps exist at 120m or 180m checkpoints. |
| Non-closed critical condition | `narratwin_ops_critical_conditions_open_total` | Aggregated on-call state | Trigger on any non-zero persisted across two checkpoints without closure timestamp. |

### 2) SLO and error-budget definitions

#### 2.1 SLO definitions

| SLO ID | Domain | Target |
|---|---|---|
| `OPS-SLO-QUEUE-01` | Queue and run backlog | p95 queue lag < 30s every 5m, error budget ≤ 1.5%/30d |
| `OPS-SLO-LEASE-01` | Lease freshness | p95 lease staleness < 20s and stale-leases count = 0 sustained for 24h |
| `OPS-SLO-OUTBOX-01` | Outbox reliability | p95 outbox age < 90s and backlog < 100 at 95th percentile |
| `OPS-SLO-RESTORE-01` | Restore execution | Restore completion within 75m for 95% of scoped restore attempts |
| `OPS-SLO-WATCH-01` | Watch response | 120m watch checkpoint complete and documented for any critical event |

#### 2.2 Alert and escalation thresholds

| Metric | Breach threshold | Action |
|---|---|---|
| `narratwin_ops_ingestion_queue_lag_seconds` | warning: >30s (5m), critical: >60s (10m) | Medium/High owner; page SRE for critical.
| `narratwin_ops_ingestion_queue_depth` | warning: >250, critical: >500 for 10m | Escalate to release owner if critical remains after 120m.
| `narratwin_ops_lease_staleness_seconds` | warning: >20s, critical: >45s for 2 windows | Move to watch `High` state; freeze non-essential changes.
| `narratwin_ops_outbox_backlog_count` | warning: >120, critical: >200 for 15m | Escalate to runtime implementer + release owner.
| `narratwin_ops_outbox_age_seconds` | warning: >90s, critical: >180s sustained | Pause deploys until dispatch recovery evidence exists.
| `narratwin_ops_restore_duration_seconds` | warning: >45m, critical: >75m | Enter watch `Critical` and require resume plan.

#### 2.3 Error-budget burn policy

- **SLO breach tolerance:** any `Critical` condition consumes budget immediately and requires closure evidence before any `#39` release posture change.
- **Burn alert:** >50% monthly budget burn in any 24h window requires review-owner notification and explicit handoff updates.
- **Budget recovery evidence:** each recovery event must include timestamp, owner, intervention, and observed rollback-to-green metric.

### 3) Alert severity matrix, owner routing, and closure evidence

| Severity | Primary owner | Routing | Ack SLA | Initial response target | Closure evidence | Escalation owner |
|---|---|---|---|---|---|---|
| `Critical` | SRE/Production Owner | Pager + on-call + release owner + #39 release steward | 10 minutes | 30 minutes or by 120m checkpoint | `watch-log` entry, root-cause hypothesis, rollback decision | CTO-adjacent on-call lead |
| `High` | SRE/Observability Owner | Pager + issue #39 context owner | 30 minutes | 60 minutes or first-hour watch | closure plan + remediation action + evidence row IDs | Release owner |
| `Medium` | Operations Owner | Shared team channel + #39 context owner | 60 minutes | 120 minutes + 120m checkpoint | triage notes + expected metric move | Escalation owner or SRE |
| `Low` | Product/Run owner | Channel alert + context owner weekly summary | 90 minutes | next business checkpoint | watch note + follow-up plan | Release owner |

### 4) First-hour watch protocol and checkpoints

#### 4.1 Trigger model

Watch starts on any `High` or `Critical` alert tied to `OPS-*` rows or `#39`
handoff events.

#### 4.2 Cadence

- **T+0:** assign incident owner, confirm alert truth, and create a watch log.
- **T+30:** confirm evidence contract mapping and lock runtime posture changes.
- **T+60:** owner handoff with first corrective action and next checkpoint plan.
- **T+120 (required):** checkpoint must include severity status, metrics moved,
  owner ACKs, and unresolved action list.
- **T+180 (required):** checkpoint must include rollback decision for unresolved
  `Critical` conditions, communication confirmation, and evidence row references.

#### 4.3 Escalation and closure gates

- unresolved `High`/`Critical` conditions at 120m move to `watch-prolonged` state
  and require release-owner review before normal operations resume.
- unresolved `Critical` at 180m requires explicit rollback or freeze decision and
  closed-loop evidence in matrix-linked rows.
- watch log must explicitly cite `OPS-METRICS-001`, `OPS-SLO-001`,
  `OPS-ALERT-001`, and `OPS-WATCH-001` evidence IDs.

### 5) Evidence contract and handoff mapping

| Row | Evidence ID | Planned evidence contract |
|---|---|---|
| `OPS-METRICS-001` | `CTX5-METRICS-EVID-001` | Metric catalog, per-failure-mode mapping, and sample query contracts in `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`. |
| `OPS-SLO-001` | `CTX5-SLO-EVID-001` | SLO table, error-budget table, and budget burn policy signed by release steward. |
| `OPS-ALERT-001` | `CTX5-ALERT-EVID-001` | Alert severity matrix, routing policy, ack SLA, and evidence completion requirements. |
| `OPS-WATCH-001` | `CTX5-WATCH-EVID-001` | First-hour watch protocol with 120/180m checkpoint requirements and owner handoff evidence. |

### 6) Runtime and runtime-adjacent deferrals

The following remain deferred in this context:

- dashboard implementations,
- alert integrations and paging wiring,
- monitor query runners,
- watch automation tooling,
- restoration tooling,
- middleware/worker endpoints,
- and all production runtime behavior changes.

Local/dev/test posture, provider defaults, and paid-provider gates remain unchanged.

## Consequences

This ADR adds the required operations planning boundary for context 5 and is
explicitly reviewable as advisory-only. The mappings are concrete and reusable for
runtime context handoff, and no production behavior is changed by this ADR.

## Related Documents

- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
