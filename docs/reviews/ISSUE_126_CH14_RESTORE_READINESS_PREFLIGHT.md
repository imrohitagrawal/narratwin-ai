# Issue #126 CH-14 Restore Readiness Preflight

## Scope

- Issue: `#126`
- Branch: `phase-1-closure-39-ch-14-restore-readiness-contract`
- Matrix ID: `DUR-RESTORE-001`
- Parent issue `#39` remains open and reference-only.

## Intent

Define the narrowest executable `CH-14` slice the repo can honestly support now
after merged issue `#125`: a restore-readiness contract that prevents
production-like overclaim while documenting the human-only evidence still
required for final `DUR-RESTORE-001` closure.

## Non-Goals

- No successful production restore drill claim.
- No backup platform, snapshot orchestration, or managed restore claim.
- No final restore metrics, RTO/RPO, dashboard, alert, watch, or rollback
  communications closure.
- No retention/re-delete, provider posture, provenance/disclosure, consent
  revocation, or untrusted-input closure.
- No closure of issue `#39` or matrix row `DUR-RESTORE-001`.

## Source Facts

- `docs/ADR/0011-context4-backup-restore-drill.md` defines the final production
  restore evidence target and keeps runtime proof deferred.
- `docs/ADR/0023-local-restore-integrity-drill.md` records that merged issue
  `#125` proved only local file-backed Stage 4/6/7 restore integrity.
- `docs/ADR/0024-ch10-production-metrics-contract.md` records that current
  restore metrics are local restore-adjacent load signals only and do not
  satisfy `CH-14`.
- `docs/ADR/0025-ch11-slo-error-budget.md` records that restore SLO terms stay
  advisory-only until `CH-14` produces real drill evidence.
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` still defines final `CH-14`
  done-when as successful restore drill evidence with timings and review.

## Invariant / Failure Matrix

| Matrix ID | Type | Invariant / failure mode | Coverage |
|---|---|---|---|
| `RESTORE-READINESS-INV-001` | Positive invariant | `#126` must explicitly compose merged local restore evidence plus the current repo-baselined restore-adjacent metrics/SLO contracts instead of pretending the repo starts from zero. | `docs/ADR/0026-ch14-restore-readiness-contract.md`; `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`; `tests/unit/test_phase1_closure_docs.py` |
| `RESTORE-READINESS-INV-002` | Positive invariant | `#126` must enumerate the human-only proof surfaces still required before any production restore-go claim. | `docs/ADR/0026-ch14-restore-readiness-contract.md`; `docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md`; `tests/unit/test_phase1_closure_docs.py` |
| `RESTORE-READINESS-INV-003` | Negative invariant | `#126` must keep matrix row `DUR-RESTORE-001` and issue `#39` open. | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`; `tests/unit/test_phase1_closure_docs.py` |
| `RESTORE-READINESS-INV-004` | Negative invariant | `#126` must not represent local file-backed replay, local restore-adjacent metrics, or advisory SLO text as successful production restore proof. | `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`; `tests/unit/test_phase1_closure_docs.py` |
| `RESTORE-READINESS-NONGOAL-001` | Non-goal | Production backup tooling, successful restore execution, RTO/RPO proof, dashboards/alerts/watch, rollback comms, retention/re-delete, and privacy/provider closures remain out of scope. | `docs/ADR/0026-ch14-restore-readiness-contract.md`; `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` |

## Old-Behavior Proof

- Before this slice, repo docs named issue `#126` as a production-like restore
  drill but did not define the narrow in-repo claim boundary after merged
  `#125` and the current repo-baselined restore-adjacent contracts.
- That gap allowed a false reading that local restore evidence plus advisory
  metrics/SLO docs might be enough to imply restore readiness, even though the
  repo still lacks final `CTX4-RESTORE-EVID-001` proof.

## Review Prompt Set

1. Adversarial review prompt: prove or disprove that any updated wording can be
   read as a successful production restore drill.
2. Governance review prompt: prove or disprove that issue `#39` and
   `DUR-RESTORE-001` remain explicitly open after the `#126` slice.
3. Operations review prompt: prove or disprove that the documented human-only
   surfaces are concrete enough to block fake restore closure.

## Independent Review Disposition

- Independent review must attack false production-readiness implications first,
  not only text consistency.
- Any fresh finding that identifies a new overclaim path resets this slice to
  the matrix-update step before more wording changes land.

## Stop Rule

If review finds another way the repo could imply production restore closure
without actual drill proof, stop, rewrite the matrix and no-go criteria, and
then continue from the updated contract.

## Skill / Tool Selection

- Checked repo docs first: `docs/AI_BUILD_BRIEF.md`, `docs/STATUS.md`,
  `docs/REPOSITORY_GUARDRAILS.md`, `docs/STAGE_ISSUE_PLAN.md`,
  `docs/ENGINEERING_PROCESS_RCA.md`, and
  `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`.
- Checked approved review tooling first: repo-approved sub-agent review and the
  active `code-review-and-quality` skill.
- No custom skill or plugin was created or installed for issue `#126`.
