# Program Status

This file is the canonical repository-tracked governance and delivery ledger for NarraTwin AI.

It is maintained from the repository itself, not from live GitHub state. Repo checks can verify only repository-tracked changes and internal document consistency. Out-of-band issue and pull request state changes must be reconciled in the next governance update.

Use it to answer:

- what has been completed in the repository-tracked governance plan
- what is currently open in the repository-tracked governance plan
- which issue and pull request delivered each durable governance milestone
- what is blocked or ambiguous
- what the next approved action is

## Current Baseline

- Last reviewed date: 2026-06-30
- Current stage marker: `.stage/current = 3`
- Current implementation permission: blocked for product features; Stage 3 repo foundation only
- Current repo mode: governance-first, documentation-first, quality-gate-first
- Product implementation merged to `main`: no
- Tracker enforcement scope: repository-tracked stage and governance changes in checked-in files
- Out-of-band GitHub reconciliation: required in the next governance update
- No backend, RAG, provider, avatar, or database product code has been merged to `main`.
- Stage 3 may add dependency manifests, CI wrappers, Docker build files, and
  health-check-only backend/frontend foundation scaffolding, but product feature
  implementation remains blocked.

## Source Of Truth

Use these files together with this tracker:

- [AI Build Brief](AI_BUILD_BRIEF.md)
- [Codex Operating Model](CODEX_OPERATING_MODEL.md)
- [Stage Issue Plan](STAGE_ISSUE_PLAN.md)
- [Quality Gates](QUALITY_GATES.md)
- [Traceability Register](TRACEABILITY.md)
- GitHub issues and pull requests for execution history

## Executive Status

- Stage 0 governance is complete in the current repository state, and Stage 1 product/PRD hardening artifacts are represented by PR `#26`.
- `docs/STATUS.md` is the in-repo governance ledger for stage coverage, issue and PR references, open gaps, and next approved actions.
- Repository checks enforce updates to this file only for repository-tracked governance changes that are visible in the CI diff range.
- GitHub-side state that changes outside a repository diff must be reconciled in the next governance update; the local Stage 0 gate does not claim live synchronization.
- Stage 1 quality is executable locally and enforced in CI.
- Stage 2 completed through merged PR `#27`; architecture, security, AI safety,
  portability, API, data model, observability, branch scope, provider defaults,
  and ADR canon are hardened for issue `#2`.
- Stage 3 quality is executable locally through `make stage3-quality`, which now
  runs the full Stage 3 wrapper set rather than only metadata checks.
- Stage 3 repo foundation work is in progress on branch
  `stage3-repo-foundation-ci-cd` for issue `#5`.
- Stage 1 allows narrowly scoped CI wrapper compatibility fixes only where the
  Stage 1 marker activates pre-existing governance checks.
- The repository remains blocked from product feature implementation because Stage
  3 and the Stage 4 implementation gate have not passed.
- Stage 1 is split into product/PRD hardening under `#1` and the follow-on Spec Kit constitution/spec/plan/tasks gate under `#16`.
- Stage 3 repository-foundation work builds on the partial Stage 0 CI baseline and
  is now adding dependency manifests, health checks, Docker build paths, CI
  wrappers, local setup docs, pre-commit, security scans, eval smoke, and an
  executable Stage 3 quality gate.
- Stage 3 hardening now reconciles inherited quality workflows, pins checked-in
  GitHub Actions by immutable SHA, narrows branch scope to exact scaffold files,
  pins `uv` and container images, narrows branch scope to exact scaffold files,
  hardens local containers, disables premature Chroma defaults, and makes eval
  smoke fixture/report backed.
- Stage 3 preserves inherited compatibility status contexts for `quality /
  secrets` and `security / docker build` while the authoritative Stage 3 secret
  scan and Docker gates remain owned by the `security` and `ci` workflows.
- Stage 4 through Stage 8 and Final Review remain open with no merged implementation work.

## Stage Ledger

| Stage | Status | Issue ledger | Pull request ledger | Quality gate state | Notes |
|---|---|---|---|---|---|
| Stage 0 | Complete, governance baseline active | `#14` closed | `#15` merged, `#23` merged | Executable and green | Operating model, quality gate, and repository guardrails are in place; product implementation remains blocked. |
| Stage 1 | Product/PRD hardening represented by PR `#26` | `#1` open, `#16` open | `#26` | Executable | `#1` is product strategy and PRD v1.0 hardening; `#16` remains the follow-on Spec Kit gate. Reconcile merge state after the GitHub merge event. |
| Stage 2 | Complete, merged to `main` | `#2` reconcile after merge | `#27` merged | Executable locally | Architecture, ADRs, threat model, security/privacy, AI safety/evaluation, portability, API, data model, observability, machine-readable semantic contract, human review checklist, branch scope, and provider defaults are hardened. |
| Stage 3 | In progress | `#5` open | Branch `stage3-repo-foundation-ci-cd`; PR pending | Executable locally | Adds repo foundation manifests, health checks, frontend foundation, Docker build path, pre-commit, CI/security/eval workflows, dependency/security scan path, local setup docs, hardened workflow pins, exact-file scope checks, non-root containers, and fixture-backed eval smoke without product features beyond health checks. |
| Stage 4 | Pending | `#4` open | None merged | Placeholder target only | No product slice has been merged. |
| Stage 5 | Pending | `#10` open | None merged | Placeholder target only | Eval, guardrail, and observability work remains future scope. |
| Stage 6 | Pending | `#11` open | None merged | Placeholder target only | Translation, subtitles, and voice adapter remain future scope. |
| Stage 7 | Pending | `#12` open | None merged | Placeholder target only | Avatar rendering and export remain future scope. |
| Stage 8 | Pending | `#13` open | None merged | Placeholder target only | Performance, hardening, and release readiness remain future scope. |
| Final Review | Pending | `#6` open | None merged | Placeholder target only | Independent release review has not started. |

## Issue Ledger

### Stage Issues

| Issue | State | Intended stage | Current interpretation |
|---|---|---|---|
| `#14` | Closed | Stage 0 | Canonical completed Stage 0 issue for repository guardrails and CI quality gates. |
| `#1` | Open | Stage 1 | Canonical Stage 1 product strategy and PRD v1.0 hardening issue. |
| `#16` | Open | Stage 1 follow-on | Spec Kit constitution/spec/plan/tasks gate that follows product/PRD hardening. |
| `#2` | Reconcile after merge | Stage 2 | Architecture, security, AI safety completed by merged PR `#27`; issue state must be reconciled with GitHub. |
| `#5` | Open | Stage 3 | Repo foundation and CI/CD gates. |
| `#4` | Open | Stage 4 | First grounded-script vertical slice. |
| `#10` | Open | Stage 5 | Evaluation, guardrails, observability. |
| `#11` | Open | Stage 6 | Multilingual scripts, subtitles, voice adapter. |
| `#12` | Open | Stage 7 | Avatar rendering adapter and demo export. |
| `#13` | Open | Stage 8 | Performance, security, release readiness. |
| `#6` | Open | Final Review | Independent reviewer pass. |

### Additional Backlog And Governance Issues

| Issue | State | Role | Notes |
|---|---|---|---|
| `#3` | Open | Legacy governance issue | Uses obsolete `Stage -1` naming and should be reconciled or closed. |
| `#8` | Open | Product-definition support | Captures two product modes and project-avatar-pack contract; concept already exists in docs but issue remains open. |
| `#9` | Closed | Superseded placeholder | Explicitly marked as superseded. |
| `#17` | Open | Future slice | Translation/localization and subtitles. |
| `#18` | Open | Future slice | Optional TTS audio provider boundary. |
| `#19` | Open | Future slice | Mock avatar video and FFmpeg assembly. |
| `#20` | Open | Future slice | Interactive Q&A over approved project knowledge. |
| `#21` | Open | Future slice | Premium adapters, observability dashboard, and cost controls. |

## Pull Request Ledger

| PR | State | Merge date | Outcome |
|---|---|---|---|
| `#7` | Merged | 2026-06-28 | Hardened the NarraTwin operational blueprint in docs before governance gating matured. |
| `#15` | Merged | 2026-06-28 | Added repository guardrails and CI quality gates under Stage 0 governance issue `#14`. |
| `#22` | Closed | Not merged | Earlier Stage 0 operating-model PR superseded by the Stage 0 redo path. |
| `#23` | Merged | 2026-06-29 | Redid Stage 0 operating model and executable quality gates; green in both `Quality Gates` and `quality` workflows before merge. |
| `#26` | Delivery PR | Reconcile after merge | Stage 1 product strategy and PRD v1.0 hardening; includes executable Stage 1 docs quality gate. |
| `#27` | Merged | 2026-06-30 | Stage 2 architecture/security/AI-safety remediation; includes executable Stage 2 docs quality gate, semantic architecture contract checks, and no product implementation. |

## Completed Work

### Completed Governance Milestones

- Branch/PR-only workflow is documented and enforced through repository checks where possible, with direct-push prevention delegated to repository settings.
- Local `make quality` exists and dispatches by `.stage/current`.
- Stage 0 quality is executable through `scripts/quality/check_stage0_docs.py`.
- GitHub Actions enforce:
  - repository guardrails
  - Stage 0 quality gate
  - stage-aware backend contract behavior for Stage 0 governance scripts
  - secret scanning
  - markdown validation
- Required Stage 0 operating docs exist in the current repository state.
- Canonical repository-tracked governance status now has a dedicated ledger in this file.
- Skill governance exists through:
  - [Skill Lock](SKILL_LOCK.md)
  - [Skill Execution Plan](SKILL_EXECUTION_PLAN.md)
  - [Skill Trust Review](SKILL_TRUST_REVIEW.md)
- Third-party governance inventory exists in [Third-Party Notices](THIRD_PARTY_NOTICES.md).
- Stage 0 merged with green CI and no product implementation.
- PR `#26` represents the Stage 1 product/PRD hardening artifact set and contains no product implementation; its only CI wrapper changes keep pre-existing governance checks compatible with the Stage 1 marker.
- PR `#27` merged Stage 2 architecture/security/AI-safety remediation into
  `main` with no product implementation.

### Stage 0 Governance Artifacts In Current Repository State

- [AGENTS.md](../AGENTS.md)
- [CODEX_OPERATING_MODEL.md](CODEX_OPERATING_MODEL.md)
- [QUALITY_GATES.md](QUALITY_GATES.md)
- [STAGE_ISSUE_PLAN.md](STAGE_ISSUE_PLAN.md)
- [SKILL_LOCK.md](SKILL_LOCK.md)
- [SKILL_EXECUTION_PLAN.md](SKILL_EXECUTION_PLAN.md)
- [SKILL_TRUST_REVIEW.md](SKILL_TRUST_REVIEW.md)
- [REPOSITORY_GUARDRAILS.md](REPOSITORY_GUARDRAILS.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [check_quality_stage.py](../scripts/quality/check_quality_stage.py)
- [check_stage0_docs.py](../scripts/quality/check_stage0_docs.py)
- [stage_not_implemented.py](../scripts/quality/stage_not_implemented.py)
- [check_stage1_docs.py](../scripts/quality/check_stage1_docs.py)
- [check_stage2_docs.py](../scripts/quality/check_stage2_docs.py)
- [check_recommended_review_items.py](../scripts/quality/check_recommended_review_items.py)

## Pre-Implementation Document Inventory

| Document | State | Notes |
|---|---|---|
| `docs/PRODUCT_STRATEGY.md` | Present | Stage 1 product strategy v1.0 in PR `#26`. |
| `docs/PRD.md` | Present | Stage 1 PRD v1.0 in PR `#26`. |
| `docs/PRD_RED_TEAM_REVIEW.md` | Present | Stage 1 red-team review in PR `#26`. |
| `docs/NORTH_STAR_METRICS.md` | Present | Stage 1 metrics doc in PR `#26`. |
| `docs/METHODOLOGY.md` | Present | Seed methodology exists. |
| `docs/ARCHITECTURE.md` | Present | Stage 2 architecture v1.0 drafted. |
| `docs/PROJECT_AVATAR_PACK.md` | Present | Reusable project-avatar-pack concept is documented. |
| `docs/SECURITY_AND_PRIVACY.md` | Present | Stage 2 security/privacy v1.0 drafted. |
| `docs/AI_SAFETY_AND_EVALUATION.md` | Present | Stage 2 AI safety/evaluation v1.0 drafted. |
| `docs/THREAT_MODEL.md` | Present | Stage 2 threat model drafted. |
| `docs/PORTABILITY_STRATEGY.md` | Present | Stage 2 portability strategy drafted. |
| `docs/API_CONTRACT.md` | Present | Stage 2 API contract drafted. |
| `docs/DATA_MODEL.md` | Present | Stage 2 logical data model drafted. |
| `docs/OBSERVABILITY_AND_COST.md` | Present | Seed observability/cost doc exists. |
| `docs/ROADMAP.md` | Present | Stage 1 outcome roadmap in PR `#26`. |
| `docs/RELEASE_QUALITY_BAR.md` | Present | Seed release-quality bar exists. |
| `docs/TRACEABILITY.md` | Present | Seed traceability register exists and contains guardrail mappings. |
| `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Present | Stage 1 product requirement-to-stage matrix. |
| `docs/PHASE_PLAN.md` | Present | Stage 1 spec-driven phase plan and vertical-slice breakdown. |

## Known Gaps And Reconciliation Items

- Stage 1 is split across two open issues: `#1` for product/PRD hardening and `#16` for the follow-on Spec Kit constitution/spec/plan/tasks gate.
- Legacy issue `#3` still uses `Stage -1` naming that no longer matches the operating model.
- Stage 3 has its own open issue `#5`, but some repo-foundation work has already landed under Stage 0 governance. The eventual Stage 3 plan should explicitly acknowledge that inherited baseline.
- `.stage/current` is `3` for the Stage 3 repo foundation and CI/CD artifact set
  because it implements the executable Stage 3 quality gate.
- PR `#27` completed second-pass remediation after independent sub-agent and
  Claude cross-model review identified idempotency, approved-knowledge state,
  failed-output exposure, retrieval, cache, provider-bound secret screening,
  evaluation evidence, and guardrail semantic gaps.
- Stage 2 sub-agent and cross-model finding disposition is captured in
  `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`; PR `#27` has merged and any GitHub
  issue-state drift must be reconciled in the next governance update.
- Stage 2 reusable review prompts now live in
  `docs/STAGE2_REVIEW_PROMPT_PACK.md` for future parallel review runs.
- Non-blocking review recommendations are now tracked in
  `docs/RECOMMENDED_REVIEW_ITEMS.md` and checked by stage quality so each item
  must be resolved, accepted, or superseded at the correct future stage.
- GitHub issue and pull request state can drift from this file until the next governance PR updates the ledger, because repository checks are diff-scoped rather than GitHub-event-synced.

## Next Approved Actions

1. Finish Stage 3 repo foundation and CI/CD quality gates through issue `#5`.
2. Reconcile GitHub issue state for Stage 2 issue `#2` after merged PR `#27`.
3. Confirm issue `#1` disposition after the Stage 1 product/PRD hardening merge.
4. Run the follow-on Spec Kit constitution/spec/plan/tasks gate through issue `#16` before product implementation planning is treated as ready.
5. Close or supersede stale governance issues that conflict with the current operating model, especially `#3`.
6. Keep this file updated at every stage boundary, every stage-issue change, and every merged stage PR.

## Maintenance Protocol

Update this file in the same branch or PR whenever any repository-tracked governance change happens, including:

- a stage plan, stage policy, or guardrail contract changes in checked-in files
- a stage marker or stage gate contract changes
- a stage issue or PR mapping in this repository ledger changes
- `.stage/current` changes
- a stage status changes from pending to in progress, blocked, complete, or superseded
- a new governance artifact becomes required or an old one becomes obsolete
- a major blocker or ambiguity is discovered or resolved

Reconcile this file in the next governance PR after any out-of-band GitHub event that changes issue or pull request state without a repository diff.

Required update rules:

- keep the current-baseline section merge-stable; do not record branch-local or pre-merge transient states there
- preserve historical entries; do not rewrite merged history to look cleaner
- call out inconsistencies explicitly instead of hiding them
- use exact issue and PR numbers when recording durable history or current ledger mappings
- state whether work is merged to `main`, merely documented, or still pending
- keep the tracker factual and source-backed

## Change Log

| Date | Change |
|---|---|
| 2026-06-29 | Initial canonical program status tracker added to consolidate stage, issue, PR, and governance status. |
| 2026-06-29 | Tracker contract refined to be merge-stable and repository-scoped, with explicit limits on what local checks can enforce. |
| 2026-06-29 | Stage 1 product/PRD hardening split clarified: `#1` covers PRD v1.0 hardening, while `#16` remains the follow-on Spec Kit gate. |
| 2026-06-29 | PR `#26` advanced `.stage/current` to `1` and added executable Stage 1 documentation quality checks. |
| 2026-06-29 | Stage 2 architecture, security, AI safety, portability, API, and data-model v1.0 docs drafted under issue `#2`; product implementation remains blocked. |
| 2026-06-30 | Stage 2 remediation added executable local quality gate and hardened architecture/security/eval/performance/API/data-model contracts under issue `#2`; product implementation remains blocked. |
| 2026-06-30 | Draft PR `#27` opened for Stage 2 remediation and linked to issue `#2`; CI and review remain required before Stage 2 completion. |
| 2026-06-30 | Second-pass Stage 2 remediation added a machine-readable architecture contract, stronger semantic gate checks, idempotency and job lifecycle locks, safe failed-output contracts, retrieval thresholds, and guardrail self-scanning. |
| 2026-06-30 | Stage 2 review rerun blockers were remediated for idempotency indexes, evaluation/evidence API consistency, key/cert guardrails, and checker exact-lock coverage; final human PR reviewer signoff remains pending. |
| 2026-06-30 | Added a recommended-review-item register and stage quality checker so non-blocking review findings are enforced at their assigned stages. |
| 2026-06-30 | Stage 3 restored required compatibility status contexts for inherited branch-protection checks while retaining the newer authoritative CI and security gates. |
| 2026-06-30 | Latest Stage 2 review rerun remediated API schema-list and evaluation-result field contract gaps and tightened recommendation-checker governance coverage. |
| 2026-06-30 | Latest Stage 2 review rerun remediated failed/refused response status wording, idempotency response optionality, AI safety evaluation-schema coverage, claim-support shape consistency, and lease vocabulary drift. |
| 2026-06-30 | ADR 0005 updated to record the latest Stage 2 evaluation, response-shape, idempotency, and lease-vocabulary hardening decisions. |
| 2026-06-30 | PR `#27` merged Stage 2 to `main`; Stage 3 started on `stage3-repo-foundation-ci-cd` for issue `#5` with repo foundation manifests, health checks, Docker build path, CI/security/eval workflows, frontend scaffold, executable Stage 3 quality gate, hardened action pins, exact-file scope checks, non-root containers, and fixture-backed eval smoke. |
