# Issue #39 Execution Strategy

## Objective

Make the issue `#39` Phase 1 No-Go to Go execution plan durable outside chat.
This is an execution strategy for `Refs #39` work only. It does not close
issue `#39`, does not authorize production deployment, and does not change any
matrix row from `Open` to `Closed`.

The strategy answers four questions for every smallest chunk:

- what must be implemented
- what can run in parallel
- which planning, implementation, and review agents are required
- what proof is required before the work can move to the next chunk or release
  gate

## Tracking Contract

`docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` remains the source of truth
for the mandatory production-closure failure matrix, matrix row status, and
final row-closure records.

This document is the source of truth for execution sequencing. It tracks how
the matrix rows are decomposed into independently reviewable chunks, how the
chunks move through planning, implementation, review, fix, re-review, and
deployment transition, and which chunks are safe to execute in parallel.

Each chunk must use:

- a child GitHub issue or explicitly scoped issue comment linked with
  reference-only `Refs #39` wording
- a dedicated branch named `phase-1-closure-39-<chunk-slug>` after the chunk
  has an explicit checker allowlist; unknown generic `phase-1-closure-39-*`
  branches intentionally default to docs/checker/test scope until a reviewed
  allowlist update binds that branch to one chunk
- a pull request linked to the child issue or issue `#39`
- a pre-code planning artifact in the issue or pull request before coding
- row-specific evidence updates in the production closure plan only after the
  implementation evidence exists

New per-chunk files are allowed only after the Phase 1 changed-file allowlist is
updated by reviewed PR. Until then, pre-code artifacts may live in the child
issue, PR body, PR comments, and row-closure updates to the existing issue `#39`
closure documents.

## Chunk Definition Of Done

A chunk is done only when all of these conditions are satisfied. This is the
per-chunk Definition of Done, also referred to as DoD or DEN in planning notes.

- Scope is bound to one chunk row in this document and one or more explicit
  issue `#39` matrix IDs.
- The pre-code plan exists before implementation and contains source facts,
  non-goals, positive invariants, negative invariants, failure or false-pass
  cases, test mapping, review-agent plan, and stop rules.
- The first implementation pass adds RED tests, executable negative tests, or a
  documented human-only evidence surface before changing behavior.
- The implementation touches only files allowed for the branch and only the
  surfaces needed by the chunk.
- The PR uses `Refs #39` reference-only language unless it is the final
  disposition PR and every matrix row is already eligible for closure.
- Validation includes the chunk-specific tests plus the standing Phase 1 gate:
  `uv run pytest tests/unit/test_guardrails_check.py`,
  `uv run pytest tests/unit/test_phase1_closure_docs.py`,
  `python3 scripts/guardrails_check.py`, `make quality`,
  `uv run ruff check scripts tests`, `uv run mypy scripts tests`, and forced
  PR guardrail execution with `NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1`.
- Deployable/runtime chunks also run the relevant broader gates before merge:
  `make ci`, `make security`, `make dependency-audit`,
  `make container-scan`, `make secrets-scan`, and `make eval` when the chunk
  affects runtime, provider, media, security, or release behavior.
- Required review agents have reviewed the implementation and tests, not only
  the plan.
- Every review finding has a recorded disposition: fixed, rejected with evidence,
  non-goal with rationale, or human-only follow-up.
- Any fix after review is re-reviewed by a fresh reviewer or fresh-context
  agent before the chunk is marked complete.
- The production closure plan row is updated from `Open` to `Closed` only when
  concrete row evidence exists, reviewer evidence is recorded, and residual
  risk is accepted.

## Execution State Machine

Every chunk must move through this state machine:

`planned -> issue-created -> preflight-ready -> preflight-reviewed -> red-tests -> implementation -> self-review -> adversarial-review -> fix-loop -> re-review -> ci-green -> human-gates -> merged -> row-closure-recorded`

The chunk stops instead of advancing when:

- scope expands beyond the matrix IDs named for the chunk
- implementation discovers a missing architecture decision
- a fix changes a contract that was already reviewed
- two or more new defect classes appear after a green review
- runtime or production deployment is required before the relevant matrix rows
  have concrete evidence

When a stop rule triggers, the next step is a planning update or new child
chunk, not a larger implementation PR.

## Parallelization Model

Parallel execution is allowed only after the dependency boundary is explicit.
The safe default is small sequential work until the shared contract is stable,
then parallel implementation by domain.

Sequential foundation:

- `CH-00` must happen first because it establishes governance, tracking, and
  review discipline for the remaining chunks.
- `CH-01` and `CH-02` must establish migration and ACID/CAS storage boundaries
  before runtime state, lease, outbox, restore, retention, or replay chunks
  claim production evidence.

Parallel groups after foundation:

- Runtime state chunks `CH-04`, `CH-05`, and `CH-06` can run in parallel after
  `CH-02` if their shared transaction and identifier contracts are frozen.
- Derived artifact chunks `CH-07` and `CH-08` can run in parallel after the
  Stage 4 durable graph and source-run linkage are stable, with `CH-08` also
  waiting for consent capture.
- Operations chunks can start metric catalog planning early, but runtime alert,
  watch, restore, and rollback evidence must wait for the relevant durable
  state and metrics to exist.
- Media, provider, retention, and untrusted-input chunks can run in parallel
  after consent, provenance, and artifact-state dependencies are explicit.
- `CH-23` is always last because it is the final Go/No-Go disposition.

## Agent Review Protocol

Each chunk uses at least three roles:

- Planning agent: writes or reviews the pre-code plan, matrix mapping, source
  facts, invariants, non-goals, and stop rules.
- Implementation agent: writes the smallest code, docs, and tests required for
  the accepted pre-code plan.
- Review agent: reviews tests first, then implementation, then evidence.

Required review agents by domain:

| Domain | Required review agents |
|---|---|
| Governance and release posture | Governance/false-pass reviewer, release reviewer |
| Durability and state | Architecture/state reviewer, test/evidence reviewer, governance reviewer |
| Migrations and rollback | Platform/storage reviewer, release reviewer, operations reviewer |
| Operations | SRE/observability reviewer, release reviewer, test/evidence reviewer |
| Media, privacy, provider, retention | Security/privacy reviewer, provider/platform reviewer, release reviewer |
| Final disposition | Governance reviewer, release reviewer, security reviewer, operations reviewer |

The review prompt for each PR must include the branch, commit, changed files,
matrix IDs, pre-code plan, negative invariants, validation commands, and known
human-only evidence surfaces.

## Re-Review After Fixes

Review fixes are not complete when the author says they are complete. Every
fix must pass a second review pass.

The re-review must inspect:

- the original finding
- the exact fix diff
- any tests added or changed for the fix
- whether the fix created a new failure mode or weakened an invariant
- whether the production closure plan evidence still matches the implemented
  behavior

If a fix changes a reviewed contract, the chunk returns to `preflight-reviewed`
instead of continuing from `fix-loop`. If a fix creates a new defect class, the
chunk opens a follow-up finding and cannot be marked done until that finding is
reviewed or explicitly deferred with owner and risk.

## Chunk Work Plan

| Chunk | Matrix IDs | Dependencies | Parallel group | Required planning artifact | Required review agents | Done when |
|---|---|---|---|---|---|---|
| `CH-00` governance execution tracker | `GOV-SCOPE-001` | None | Foundation sequential | This execution strategy, child issue map, branch allowlist plan | Governance/false-pass reviewer, release reviewer | Strategy and checker are merged; future chunks have reference-only `Refs #39` rules and one chunk per context. |
| `CH-01` migration baseline | `DUR-MIG-001` | `CH-00` | Foundation sequential | Migration preflight covering expand/contract order, version table, compatibility window | Platform/storage reviewer, operations reviewer, release reviewer | Versioned migration runner and migration evidence exist with rollback-safe forward repair posture. |
| `CH-02` ACID/CAS storage kernel | `DUR-ACID-001` | `CH-01` | Foundation sequential | Storage contract preflight covering IDs, versions, transactions, CAS conflict examples | Architecture/state reviewer, test/evidence reviewer, governance reviewer | Production metadata writes use ACID/CAS semantics with conflict, replay, and stale-write tests. |
| `CH-03` Stage 4 durable graph | `DUR-STAGE4-001` | `CH-02`, `CH-04`, `CH-06` | Runtime graph | Stage 4 state-graph preflight for project, document, chunk, run, evaluation, and RAG state | Architecture/state reviewer, API reviewer, test/evidence reviewer | Stage 4 project/upload/ingest/retrieve/generate/evaluate state resumes from durable metadata without exactly-once side-effect claims. |
| `CH-04` idempotency semantics | `DUR-IDEMP-001` | `CH-02` | Runtime state parallel | Idempotency preflight covering operation scope, payload hash, terminal replay, recovery state | Runtime/state reviewer, security reviewer, test/evidence reviewer | Retry and failover tests prove dedupe, conflict rejection, terminal replay, and stale-owner behavior. |
| `CH-05` lease fencing | `DUR-LEASE-001` | `CH-02` | Runtime state parallel | Lease preflight covering acquire, heartbeat, expiry, reclaim, monotonic fencing token | Runtime/state reviewer, concurrency reviewer, test/evidence reviewer | Cross-worker lease tests reject stale writers and prove ownership transfer and expiry semantics. |
| `CH-06` committed outbox | `DUR-OUTBOX-001` | `CH-02` | Runtime state parallel | Outbox preflight covering state/event transaction boundary and idempotent consumer policy | Runtime/integration reviewer, operations reviewer, test/evidence reviewer | Same-transaction state/event write, at-least-once dispatch, retry, and consumer dedupe evidence exists. |
| `CH-07` Stage 6 durable replay | `DUR-STAGE6-001` | `CH-03`, `CH-04` | Derived artifacts parallel | Stage 6 replay preflight covering source-run linkage, checksums, deterministic provenance | Stage 6 reviewer, architecture/state reviewer, test/evidence reviewer | Translated scripts, subtitles, and derived metadata replay from durable source state with checksum-based dedupe. |
| `CH-08` Stage 7 render artifact state | `DUR-STAGE7-001` | `CH-03`, `CH-04`, `CH-16` | Derived artifacts parallel | Stage 7 render preflight covering render status, artifact records, consent checkpoint, and export blocking until disclosure/provenance chunks land | Stage 7 reviewer, security/privacy reviewer, test/evidence reviewer | Render/artifact state is durable and bound to consent checkpoints without claiming provenance or disclosure closure. |
| `CH-09` technical rollback compatibility | `DUR-ROLLBACK-001` | `CH-01`, `CH-02`, `CH-03` | Release safety | Rollback compatibility preflight for previous-code-on-expanded-schema and forward repair | Platform/storage reviewer, release reviewer, operations reviewer | Previous deploy compatibility or explicit forward-only rollback block is proven with evidence. |
| `CH-10` production metrics contract | `OPS-METRICS-001` | `CH-04`, `CH-05`, `CH-06` | Operations sequence | Metric catalog preflight mapping queue, lease, idempotency, outbox, restore, rollback failure contracts | SRE/observability reviewer, runtime reviewer, test/evidence reviewer | Metric catalog and shared instrumentation contracts are named and documented; restore and rollback metric emissions close with `CH-14` and `CH-15` evidence before final row closure. |
| `CH-11` SLO and error budget | `OPS-SLO-001` | `CH-10` | Operations sequence | SLO preflight binding queue lag, lease staleness, outbox age, restore RTO/RPO, rollback | SRE/observability reviewer, release reviewer | SLO thresholds and error-budget actions are reviewed and tied to alert and rollback decisions. |
| `CH-12` dashboards and alerts | `OPS-ALERT-001` | `CH-10`, `CH-11` | Operations sequence | Alert preflight covering severity, owner, route, acknowledgment, and evidence loop | SRE/operations reviewer, release reviewer, test/evidence reviewer | Dashboard or query evidence and tested alert routing exist for each critical threshold. |
| `CH-13` first-hour watch | `OPS-WATCH-001` | `CH-12` | Operations sequence | Watch preflight covering 0-60 minute cadence plus 120 and 180 minute checkpoints | Release reviewer, operations reviewer | Watch log template, owner handoff, timeout action, and rollback escalation threshold are tested. |
| `CH-14` backup and restore drill | `DUR-RESTORE-001` | `CH-01`, `CH-02`, `CH-10`; environment readiness issues `#141`-`#149` | Operations/storage | Restore drill preflight covering RDS/S3 backup scope, integrity, RTO/RPO, smoke checks, restore metric emission, and a re-delete handoff derived from the current independent deletion journal rather than restored state | Operations reviewer, platform/storage reviewer, security reviewer | At least one successful restore drill has evidence, timings, database/object integrity checks, restore metrics, journal-derived re-delete handoff, and residual-risk decision. CH-21 owns erasure behavior proof. |
| `CH-15` rollback communications | `OPS-ROLLBACK-001` | `CH-09`, `CH-12`, `CH-13` | Release safety | Rollback comms preflight covering freeze window, comms templates, ownership confirmation, and rollback metric evidence | Release reviewer, operations reviewer, governance reviewer | Pre/post rollback comms, rollback metrics, freeze criteria, and evidence capture rules are reviewed and executable. |
| `CH-16` consent capture | `MEDIA-CONSENT-001` | `CH-02` | Media/security parallel | Consent preflight covering actor, timestamp, text version, scope, source run, artifact refs | Security/privacy reviewer, media reviewer, test/evidence reviewer | Affirmative consent records are durable, auditable, scoped, and required before synthetic-media generation. |
| `CH-17` consent revocation | `MEDIA-REVOKE-001` | `CH-16` | Media/security parallel | Revocation preflight covering block replay, takedown, retention, published artifacts, communications | Security/privacy reviewer, release reviewer, media reviewer | Revoked consent blocks replay/export and has reviewed takedown, retention, and customer/user comms behavior. |
| `CH-18` provenance binding | `MEDIA-PROVENANCE-001` | `CH-08`, `CH-16` | Media/security parallel | Provenance preflight covering source run, prompt/provider reference, checksum, denial checks, and disclosure lineage | Security/privacy reviewer, media reviewer, test/evidence reviewer | Rendered artifacts prove linkage to source run, consent, checksum, and identity/likeness denial checks without claiming provider release posture. |
| `CH-19` disclosure binding | `MEDIA-DISCLOSURE-001` | `CH-18` | Media/security parallel | Disclosure preflight covering text version, export binding, public-use posture, validation | Security/privacy reviewer, release reviewer, media reviewer | Exported artifacts carry or bind the expected synthetic-media disclosure state and version. |
| `CH-20` provider release posture | `PROVIDER-POSTURE-001` | `CH-18` | Provider/security | Provider preflight covering legal/license, egress, keys, local mocks, rollout, rollback disablement | Security/privacy reviewer, platform reviewer, release reviewer | External providers are deny-by-default, key-isolated, mock/local in dev/test/CI, and reviewed before production enablement. |
| `CH-21` retention and erasure | `SEC-RETENTION-001` | `CH-02`, `CH-14`, `CH-16`, `CH-18` | Security/privacy | Retention preflight covering data classes, encryption, redaction, deletion, backups, restores, audit exceptions, and the CH-14 re-delete handoff | Security/privacy reviewer, operations reviewer, test/evidence reviewer | PII, consent, provenance, logs, metrics, backups, restores, and replay/export blocks follow a reviewed erasure contract, including proof that restored deleted records are re-deleted. |
| `CH-22` untrusted replayed input | `SEC-UNTRUSTED-001` | `CH-03`, `CH-07`, `CH-08`, `CH-21` | Security/runtime | Untrusted-input preflight covering uploads, prompts, transcripts, provider outputs, restored artifacts, metadata | Security/privacy reviewer, runtime reviewer, operations reviewer | Durable and replayed content is revalidated, encoded, redacted, and protected from poisoned retrieval and prompt injection. |
| `CH-23` final disposition and production transition | `DUR-ACID-001`, `DUR-IDEMP-001`, `DUR-STAGE4-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001`, `DUR-STAGE6-001`, `DUR-STAGE7-001`, `DUR-MIG-001`, `DUR-ROLLBACK-001`, `DUR-RESTORE-001`, `OPS-METRICS-001`, `OPS-SLO-001`, `OPS-ALERT-001`, `OPS-WATCH-001`, `OPS-ROLLBACK-001`, `MEDIA-CONSENT-001`, `MEDIA-REVOKE-001`, `MEDIA-PROVENANCE-001`, `MEDIA-DISCLOSURE-001`, `PROVIDER-POSTURE-001`, `SEC-RETENTION-001`, `SEC-UNTRUSTED-001`, `GOV-SCOPE-001` | `CH-00`, `CH-01`, `CH-02`, `CH-03`, `CH-04`, `CH-05`, `CH-06`, `CH-07`, `CH-08`, `CH-09`, `CH-10`, `CH-11`, `CH-12`, `CH-13`, `CH-14`, `CH-15`, `CH-16`, `CH-17`, `CH-18`, `CH-19`, `CH-20`, `CH-21`, `CH-22` | Final sequential | Final Go/No-Go preflight with row-closure evidence pack and release checklist | Governance reviewer, release reviewer, security reviewer, operations reviewer | All rows have concrete evidence, all gates pass, release checklist is reviewed, and the Go/No-Go artifact is updated by PR. |

## Deployment Transition Plan

Production deployment remains blocked while issue `#39` is open and any matrix
row remains `Open`.

Staging/pre-production transition is allowed only after the relevant chunk rows
have merged evidence and the PR has passed:

- `make quality`
- `make ci`
- `make security`
- `make dependency-audit`
- `make container-scan`
- `make secrets-scan`
- `make eval` when runtime/eval behavior is touched
- migration dry run or staging migration execution when schema changes are
  included
- backup/restore drill evidence when durable production metadata is included
- dashboard, alert, and watch evidence when operational thresholds are included

Production Go requires a final disposition PR that:

- keeps all issue `#39` closure references intentional and reviewed
- changes matrix rows only with concrete evidence, reviewer, owner, validation,
  and residual-risk decision
- updates `docs/reviews/GO_NO_GO.md`, `docs/RELEASE_CHECKLIST.md`,
  `docs/STATUS.md`, and release-readiness docs by reviewed PR
- proves provider keys, egress, paid providers, media export, and public
  synthetic-media distribution remain disabled until explicitly enabled by the
  reviewed production plan
- records first-hour watch owners, 120/180 minute checkpoints, rollback
  criteria, and rollback communication owner before release

The production rollout order is:

1. Freeze scope and confirm all matrix rows are closed with evidence.
2. Apply expand-only migrations and verify compatibility.
3. Deploy durable runtime behind disabled or constrained production flags.
4. Verify health, readiness, migrations, metrics, alerts, backup, restore, and
   rollback probes.
5. Enable only the approved production slice.
6. Run first-hour watch plus 120 and 180 minute checkpoints.
7. Update final release status only after watch evidence is complete.

Failed production transition probes halt before enablement. A failed migration,
health, readiness, metric, alert, backup, restore, or rollback probe freezes the
rollout, records owner and evidence, and requires a reviewed rollback/no-rollback
decision before continuing. Any breached watch or SLO threshold after enablement
triggers the rollback decision path and rollback communications before final
status can move to Go.

## Stop Rules And Handoffs

The next chat or agent context must receive the chunk row, matrix IDs,
dependencies, pre-code plan, current branch, changed files, validation commands,
open findings, and evidence status before it starts work.

A chunk must be split smaller when the pre-code plan contains more than one
independent state machine, more than one reviewer domain with unrelated files,
or more than one deployable risk boundary.

Do not move to the next chunk when:

- the current chunk has unreviewed fixes
- the closure plan row evidence is stale or stronger than the implementation
- a test was weakened to pass
- a human-only evidence surface lacks owner and follow-up trigger
- a release claim depends on local/mock-only behavior

The intended result is a controlled transition from Phase 1 production No-Go to
Go: each chunk closes one bounded risk, every fix is reviewed again, and the
final release posture changes only after all issue `#39` production evidence is
present.
