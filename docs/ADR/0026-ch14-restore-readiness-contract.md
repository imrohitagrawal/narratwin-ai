# ADR 0026: CH-14 Restore Readiness Contract for DUR-RESTORE-001

## Status

Accepted for Phase 1 Closure child issue `#126`, implementation slice only.

## Date

2026-07-13

## Context

Issue `#125` merged to `main` through PR `#135` at
`f94776f6602d4c6feec2412b4764a7368049a080`. That slice proved only the current
repo-supported local restore surface:

- copied-file parity,
- restored count parity,
- replay-safe idempotent re-execution,
- and persisted inspectable local evidence paths.

It did not prove production backup platform behavior, successful production
restore execution, restore metrics, RTO/RPO attainment, retention/re-delete,
operations signoff, or final production restore readiness.

Issue `#126` is nominally the `CH-14` child issue for `DUR-RESTORE-001`, but
the current repository still cannot honestly execute a production-like backup
and restore drill. The narrowest defensible slice left in-repo is therefore a
documentation-and-guardrail contract that:

- composes the merged `#125` local restore evidence with the current
  repo-baselined `CH-10` and `CH-11` restore-adjacent metrics/SLO contracts,
- defines the human-only evidence surfaces that still must exist before any
  production restore claim,
- records explicit no-go criteria that keep `DUR-RESTORE-001` and issue `#39`
  open,
- and prevents repo docs from accidentally overstating local evidence as final
  `CH-14` proof.

## Decision

This slice establishes a repo-checked restore-readiness contract for issue
`#126`. It does not close issue `#126` unless the live issue scope is formally
updated to accept contract-only readiness evidence.

The contract is represented by:

- this ADR,
- `docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md`,
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`,
- branch-scoped Phase 1 Closure allowlists,
- and focused guardrail tests.

The narrow executable evidence row for this slice is
`CTX4-RESTORE-READINESS-EVID-001`.

## Restore Readiness Contract

Issue `#126` may honestly claim only the following:

1. The repo has a reviewed preflight that binds `CH-14` to concrete prerequisite
   evidence already available in-repo:
   `CTX4-LOCAL-RESTORE-EVID-001`, `CTX5-METRICS-EVID-001`, and
   `CTX5-SLO-EVID-001`.
2. The repo has a checked list of human-only evidence that must still be
   captured out of band before any production restore-go statement:
   backup source/target platform, restore operator identities, restore target
   environment, successful drill timestamp, restore metrics export, actual
   RTO/RPO measurement, and operations/security residual-risk signoff.
3. The repo defines explicit no-go criteria for `DUR-RESTORE-001`:
   if evidence is limited to local file-backed replay, local restore-adjacent
   load metrics, or advisory SLO text, the row stays `Open` and issue `#39`
   stays open.
4. The repo records that final `CH-14` closure still requires the original
   Context 4 production evidence target `CTX4-RESTORE-EVID-001` plus the
   associated timing and review artifacts.

## Human-Only Surfaces That Remain Mandatory

- Production backup platform and snapshot provenance.
- Restore target environment and access-control boundary.
- Successful restore drill timestamp and operator roster.
- Actual restore metric export and log capture.
- Measured RTO and RPO results for the scoped drill.
- Operations owner review and security/privacy review decisions.

## Explicit Scope Boundary

### In scope for issue `#126`

- restore-readiness preflight and evidence-pack contract,
- no-go criteria and anti-overclaim wording,
- branch-scope guardrails and tests that preserve those boundaries,
- status and traceability reconciliation for merged `#125`.

### Out of scope for issue `#126`

- backup tooling, cloud snapshots, or database-managed restore services,
- successful production restore execution,
- restore metrics export beyond the current repo-baselined local restore-adjacent
  emission points,
- production RTO/RPO proof,
- dashboards, alerts, watch, rollback communications, retention/re-delete,
  provider posture, provenance/disclosure, consent revocation, or untrusted-input
  closure.

## Consequences

- The repo can honestly claim that `#126` adds a checked `CH-14` readiness
  contract and overclaim guardrails on top of merged `#125` evidence plus the
  current repo-baselined `CH-10` and `CH-11` contract artifacts.
- The repo cannot claim a successful production restore drill, production
  restore readiness, or closure of `DUR-RESTORE-001`.
- Issue `#39` remains open.

## Related Documents

- `docs/ADR/0011-context4-backup-restore-drill.md`
- `docs/ADR/0023-local-restore-integrity-drill.md`
- `docs/ADR/0024-ch10-production-metrics-contract.md`
- `docs/ADR/0025-ch11-slo-error-budget.md`
- `docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
