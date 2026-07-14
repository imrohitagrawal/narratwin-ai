# ADR 0011: Backup and Restore Drill for Issue #39 Context 4 (Advisory Only)

## Status

Accepted for planning in Phase 1 Closure Context 4 (`#68`), advisory only.

## Date

2026-07-10

## Context

Issue `#39` remains open for production-grade durability and operations. Context 4
covers `DUR-RESTORE-001`, `OPS-METRICS-001`, and `OPS-SLO-001` planning.

This context is advisory-only planning for issue `#68` and defines
production-readiness expectations before runtime implementation contexts can execute.
No runtime, backend, frontend, provider, database, Docker, schema, endpoint, worker,
or restore tooling changes are permitted in this issue.

## Decision

Context 4 will produce a planning-only backup and restore protocol that is scoped to
production durability artifacts and explicit about:

- backup scope boundaries,
- excluded mock/local artifacts,
- retention assumptions,
- RTO/RPO targets,
- integrity checks,
- drill execution protocol,
- evidence packaging,
- escalation points,
- and the metrics/events needed for proof.

The protocol is documented only as a handoff artifact and is not operationalized
in this context.

### 1) Production backup scope boundaries

#### Included in production backup targets

- PostgreSQL durability-state tables and their operational metadata:
  `projects`, `documents`, `chunks`, `ingestions`, `runs`, `evaluations`,
  `idempotency_records`, `leases`, `outbox`, `retry_and_replay_metadata`.
- Restore-sensitive event and audit evidence:
  integrity signatures, backup manifest metadata, restore-run IDs, and audit
  verification hashes.
- Operational checkpoints needed for `DUR-ACID-001`, `DUR-IDEMP-001`,
  `DUR-LEASE-001`, and `DUR-OUTBOX-001` proof if restore is required.

#### Excluded from backup scope (deliberate)

- local JSON snapshot files under `.state/` and other local debug snapshots,
- `.env`-derived runtime paths and non-persistent in-memory state,
- local provider output caches, prompt/transcript caches, and unbounded local logs,
- generated presentation files and UX artifacts used only for Stage 4/6/7 local preview,
- unreviewed third-party artifacts and untrusted runtime caches.

### 2) Retention assumptions for durability artifacts

- **Cold snapshot retention:** 14 days for durable-state point-in-time snapshots
  for planning and staged drill validation.
- **Change-log retention:** 7 days of change history required for restoration planning
  and consistency checks.
- **Vault/evidence retention:** 90 days minimum for drill packets,
  restore checklists, and evidence logs.
- **Deletion carve-out:** restore logs and evidence are retained through the end of
  the closure cycle for matrix proof, then governed by issue-`#39` risk-retention
  follow-up evidence.

### 3) RTO/RPO targets (target planning values)

| Target | Definition | Threshold |
|---|---|---|
| `RTO` | End-to-end production restore completion from a qualified backup to a restored read/write-ready graph | 75 minutes |
| `RPO` | Maximum allowed durability data loss in an accepted restore event | ≤ 5 minutes |
| `Restore integrity window` | Duration between manifest validation start and evidence pack finalization | ≤ 30 minutes |

These are planning targets for issue `#68`; runtime implementation must prove actual
attainment before runtime handoff.

### 4) Restore integrity verification contract

Every planned drill must verify:

- identity and completeness:
  object/count parity for all durability tables included in scope,
- state transition safety:
  no duplicate/partial terminal replay and preserved terminal semantics,
- idempotency and lease safety:
  replay-safe reruns of terminal state transitions with no duplicate durable side effects,
- outbox/effect safety:
  outbound effect envelope preserved and redelivery is safe to replay,
- provenance preservation:
  evidence manifests, restore attempt IDs, and manual approval markers retained in durable storage,
- and post-restore operational posture:
  `ops status` indicators remain bounded and non-disclosive.

### 5) Restore drill protocol

1. **Pre-drill holdpoint**  
   Freeze non-idempotent mutation paths, notify ops and on-call owners, capture a
   context handoff, and validate that planned evidence IDs are available.
2. **Restore rehearsal (staging-only)**  
   Execute a restore of a selected snapshot into a planning-only environment,
   replaying representative durable state subsets for stage 4/6/7 identifiers and
   outbox/integration metadata.
3. **Post-replay validation**  
   Run integrity checks listed in Section 4 and validate matrix-linked evidence
   targets in the issue plan.
4. **Watch and escalation**  
   Run a 60/120/180 minute post-drill stability watch to monitor metric backslide.
5. **Closeout**  
   Record the runbook execution outcomes, proof artifacts, deviations, and escalation
   decisions in the issue evidence pack.

### 6) Evidence pack format

Issue `#68` evidence pack requires:

- `CTX4-RESTORE-EVID-001`: drill manifest, evidence IDs, and restore target definition,
- `CTX4-METRICS-EVID-001`: metric snapshot before/after and queue/lease/outbox proof,
- `CTX4-ESCALATION-EVID-001`: escalation decisions with owners, timestamps, and rationale,
- `CTX4-POSTDRILL-EVID-001`: post-drill closure evidence with signed checklists.

Evidence packs remain advisory until runtime proof is produced in follow-up contexts.

### 7) Escalation points

Escalation is required when any planning check fails or exceeds target bounds:

- **Green/Yellow boundary breach:** any failed integrity check, missing evidence pack item,
  or metric deviation requires immediate escalation to issue owner + operations.
- **RTO/RPO breach:** first miss triggers watch escalation and production handoff freeze.
- **Restore-replay safety gap:** observed replay ambiguity requires an explicit design
  gap ticket before any runtime implementation signoff.

### 8) Metrics/events required for restore proof

Context 4 readiness proof must bind to planned metric/event evidence:

- planned metrics:
  `narratwin_ops_restore_attempts_total`,
  `narratwin_ops_restore_duration_seconds`,
  `narratwin_ops_backup_lag_seconds`,
  `narratwin_ops_queue_lag`,
  `narratwin_ops_outbox_lag`,
  `narratwin_ops_lease_staleness_seconds`.
- planned events:
  `restore.start`, `restore.completed`, `restore.blocked`,
  `restore.intg_replay_validation_failed`,
  `restore.evidence_pack_finalized`.

These names are planning contracts; event/metric implementations are not added in this context.

### 9) Explicit non-goals and deferred runtime items

For issue `#68`, the following remain deferred:

- writing backup tooling, restore automation, retention workers, or storage operators,
- schema migration scripts, database runbooks, or runtime rollout automation,
- dashboards, alert integrations, paging automation, and on-call tooling code,
- API endpoints, runtime worker changes, frontend changes, Docker workflow changes,
  and provider posture changes.

Paid providers remain mock/local only and disabled by default in local/dev/test/posture as
currently documented.

## Issue #141 platform and retention specialization

ADR `0027` specializes this advisory plan as RDS automated backups/PITR plus S3
Versioning with at least a 15-day artifact-version recovery window, an immutable
UTC restore point and S3 Version IDs, a Platform/Storage-owned restricted
catalog plus allowlisted reviewer export, and a same-account/region separately
isolated restore landing zone whose later PITR invocation creates a new target.
The previously listed seven-day change-log assumption is superseded by the
14-day RDS/15-day S3 windows. Manual drill snapshots must be
deleted after accepted evidence or within 14 days, restore targets within 24
hours (72 hours only by dated exception), and sanitized evidence is retained for
at least 90 days.

CH-14 owns backup/catalog/restore-target lifecycle, measurement, and the handoff
of records/objects requiring re-delete. That handoff comes from the unique-key,
last-contiguous, integrity-linked control-bucket deletion journal, not the
point-in-time-restored database. CH-17 owns current consent-revocation state and
CH-21 owns erasure enforcement plus proof that restored deleted or revoked
records/objects are re-deleted or remain blocked. This preserves the dependency
direction: CH-14 produces the handoff and CH-21 proves retention/erasure
behavior later.

RTO `<= 75 minutes` and RPO `<= 5 minutes` remain unmeasured planning targets.
No environment, backup, target, or restore evidence exists merely because this
amendment is documented.

## Consequences

This ADR creates a bounded, reviewable context handoff for Context 4 planning.
Implementation context is deferred until matrix evidence, tooling, metrics, and runtime
runbooks are added in separate issue slices. No behavior change is introduced by this ADR.

## Related Documents

- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/ADR/0027-production-like-durability-platform-ownership.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
