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

- Last reviewed date: 2026-06-29
- Current stage marker: `.stage/current = 1`
- Current implementation permission: blocked
- Current repo mode: governance-first, documentation-first, quality-gate-first
- Product implementation merged to `main`: no
- Tracker enforcement scope: repository-tracked stage and governance changes in checked-in files
- Out-of-band GitHub reconciliation: required in the next governance update
- No application runtime, backend, frontend, RAG, provider, avatar, or database product code has been merged to `main`.

## Source Of Truth

Use these files together with this tracker:

- [AI Build Brief](AI_BUILD_BRIEF.md)
- [Codex Operating Model](CODEX_OPERATING_MODEL.md)
- [Stage Issue Plan](STAGE_ISSUE_PLAN.md)
- [Quality Gates](QUALITY_GATES.md)
- [Traceability Register](TRACEABILITY.md)
- GitHub issues and pull requests for execution history

## Executive Status

- Stage 0 governance is complete in the current repository state, and Stage 1 product/PRD hardening is in review.
- `docs/STATUS.md` is the in-repo governance ledger for stage coverage, issue and PR references, open gaps, and next approved actions.
- Repository checks enforce updates to this file only for repository-tracked governance changes that are visible in the CI diff range.
- GitHub-side state that changes outside a repository diff must be reconciled in the next governance update; the local Stage 0 gate does not claim live synchronization.
- Stage 1 quality is executable locally and enforced in CI.
- The repository remains blocked from product implementation because Stage 2, Stage 3, and the Stage 4 implementation gate have not passed.
- Stage 1 is split into product/PRD hardening under `#1` and the follow-on Spec Kit constitution/spec/plan/tasks gate under `#16`.
- Stage 3 repository-foundation work is partially pre-delivered under Stage 0 governance, but the dedicated Stage 3 issue is still open.
- Stage 4 through Stage 8 and Final Review remain open with no merged implementation work.

## Stage Ledger

| Stage | Status | Issue ledger | Pull request ledger | Quality gate state | Notes |
|---|---|---|---|---|---|
| Stage 0 | Complete, governance baseline active | `#14` closed | `#15` merged, `#23` merged | Executable and green | Operating model, quality gate, and repository guardrails are in place; product implementation remains blocked. |
| Stage 1 | In progress, product hardening delivery PR | `#1` open, `#16` open | `#26` delivery PR | Executable | `#1` is product strategy and PRD v1.0 hardening; `#16` remains the follow-on Spec Kit gate. |
| Stage 2 | Pending, seed docs exist | `#2` open | None merged | Placeholder target only | Architecture and safety docs exist as seeds, but Stage 2 gate is not implemented. |
| Stage 3 | Pending, partially pre-scaffolded | `#5` open | Work partially landed in `#15` and `#23` | Placeholder target only | CI and quality scaffolding started early under Stage 0 governance. |
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
| `#2` | Open | Stage 2 | Architecture, security, AI safety. |
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
- PR `#26` is the Stage 1 product/PRD hardening delivery PR and contains no product implementation.

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

## Pre-Implementation Document Inventory

| Document | State | Notes |
|---|---|---|
| `docs/PRODUCT_STRATEGY.md` | Present | Stage 1 product strategy v1.0 in PR `#26`. |
| `docs/PRD.md` | Present | Stage 1 PRD v1.0 in PR `#26`. |
| `docs/PRD_RED_TEAM_REVIEW.md` | Present | Stage 1 red-team review in PR `#26`. |
| `docs/NORTH_STAR_METRICS.md` | Present | Stage 1 metrics doc in PR `#26`. |
| `docs/METHODOLOGY.md` | Present | Seed methodology exists. |
| `docs/ARCHITECTURE.md` | Present | Seed architecture doc exists. |
| `docs/PROJECT_AVATAR_PACK.md` | Present | Reusable project-avatar-pack concept is documented. |
| `docs/SECURITY_AND_PRIVACY.md` | Present | Seed security/privacy doc exists. |
| `docs/AI_SAFETY_AND_EVALUATION.md` | Present | Seed AI safety/evaluation doc exists. |
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
- `.stage/current` is `1` in PR `#26` because this branch implements the executable Stage 1 documentation gate.
- The repository contains seed docs for later stages, but those docs are not proof that the corresponding stage gate has passed.
- GitHub issue and pull request state can drift from this file until the next governance PR updates the ledger, because repository checks are diff-scoped rather than GitHub-event-synced.

## Next Approved Actions

1. Complete review of PR `#26` for Stage 1 product/PRD hardening under issue `#1`.
2. After PR `#26` merges, reconcile GitHub issue and PR state in the next governance update if needed.
3. Run the follow-on Spec Kit constitution/spec/plan/tasks gate through issue `#16` before product implementation planning is treated as ready.
4. Start Stage 2 architecture/security/AI-safety only through issue + branch + PR with no product code.
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
