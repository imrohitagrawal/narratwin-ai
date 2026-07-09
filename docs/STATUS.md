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

- Last reviewed date: 2026-07-09
- Current stage marker: `.stage/current = 8`
- Current implementation permission: Phase 1 Closure only. No Phase 2 feature
  work, external provider enablement, production release tag, or public
  synthetic-media distribution claim is permitted until Phase 1 P0/P1 blockers
  close or are explicitly downgraded with evidence.
- Current repo mode: Final Review has merged; Phase 1 Closure is active and
  release posture is No-Go.
- Product implementation merged to `main`: Stage 8 performance, security
  hardening, and release-readiness work merged through PR `#33` at commit
  `fb40113`.
- Tracker enforcement scope: repository-tracked stage and governance changes in checked-in files
- Out-of-band GitHub reconciliation: PR `#45` merged the Final Review artifacts at
  commit `5a294c72d2b4b8cbbc0339f7bcb3f17089bddece`; Final Review issue `#6`
  is closed. Phase 1 Closure issues `#35`, `#36`, `#37`, `#40`, `#41`, and
  `#42` are closed through merged PRs `#46`, `#47`, and `#50`; issue `#38`
  has live GitHub branch-protection evidence and required-context drift checking
  recorded through merged PR `#53` at merge commit `b5205083d0d11db060c83c1a5156394263b50de5`,
  including the user-repository limitation on direct pusher restrictions; PR
  `#54` merged local file-backed restart recovery, `/api/v1/ops/status`, and
  process-hardening evidence at merge commit `8b4ba05`, while issue `#39`
  remains open for production-grade durability and monitoring; issue `#55`
  closed through PR `#56` for additional local restore-invariant hardening; PR
  `#59` merged the governance-learning allowlist follow-up for issue `#58` at
  merge commit `38ec53b`; issues `#43`, `#44`, `#48`, and `#49` remain open.
- Stage 8 may add performance smoke tests, API latency budgets, frontend
  Lighthouse checks, rate limiting, request size limits, upload MIME validation,
  dependency audit, Docker image scan, release checklist, runbook, demo seed
  data, portfolio README, and release-readiness review evidence.
- Stage 8 PR `#33` is merged and Stage 8 issue `#13` is closed.
- Stage 8 final exhaustive review remediation is recorded in ADR `0006`,
  including semantic-failure idempotency replay, exact Stage 6 voice-manifest
  validation, Docker scan exit-code handling, and branch-protection context
  documentation.

## Source Of Truth

Use these files together with this tracker:

- [AI Build Brief](AI_BUILD_BRIEF.md)
- [Codex Operating Model](CODEX_OPERATING_MODEL.md)
- [Stage Issue Plan](STAGE_ISSUE_PLAN.md)
- [Quality Gates](QUALITY_GATES.md)
- [Traceability Register](TRACEABILITY.md)
- [Project Learnings Tracker](PROJECT_LEARNINGS_TRACKER.md)
- [Project Governance Learnings](PROJECT_GOVERNANCE_LEARNINGS.md)
- [Review Rigor Retrospective](REVIEW_RIGOR_RETROSPECTIVE.md)
- [Engineering Process RCA](ENGINEERING_PROCESS_RCA.md)
- [New Project Engineering Playbook](templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md)
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
- Stage 3 repo foundation is treated as complete in the Stage 4 branch baseline;
  reconcile the exact Stage 3 PR ledger after the GitHub merge event if needed.
- Stage 1 allows narrowly scoped CI wrapper compatibility fixes only where the
  Stage 1 marker activates pre-existing governance checks.
- Stage 4 first-slice work merged to `main` through PR `#29` on 2026-06-30.
- Stage 5 completed through merged PR `#30`; issue `#10` is closed.
- Stage 6 completed through merged PR `#31`; issue `#11` is closed.
- Stage 7 has started on branch `stage7-avatar-rendering-adapter-export` for
  issue `#12`; initial governance activation records the UI/UX Pro Max CLI and
  Codex skill for Stage 7 design guidance.
- Stage 7 implementation now adds `backend/app/stage7.py`, the
  `/avatar-renders` API route, provider config validation, render job lifecycle
  status, local HTML demo exports, JSON render manifests, JSON video export
  placeholders, synthetic avatar consent controls, cloned identity rejection,
  artifact validation, frontend preview/export-artifact UI, frontend download
  safety checks, and executable Stage 7 quality.
- Stage 7 fresh-review remediation tightened successful render validation:
  provider metadata must match local provider config, fallback reasons are enum
  validated, demo HTML must exactly match trusted renderer output, manifests and
  video placeholders carry source context-ref IDs, citation indexes, evaluation
  ID/checksum, disclosure, provider config, and public-use license checks,
  unexpected JSON artifact fields are rejected, semantic validation failures are
  idempotently retained, failed idempotent attempts replay terminal errors
  without another provider call, and frontend downloads validate decoded size,
  checksum, JSON schema markers, active HTML content, and visible blocked
  reasons before enabling links.
- Ragas and Giskard were evaluated for Stage 5 but are not active dependencies:
  `ragas==0.4.3` currently fails `pip-audit`, and fixed Giskard releases require
  `scipy<1.12.0`, which is incompatible with the repo's Python 3.13 baseline.
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
- Final Review PR `#45` is merged and records a No-Go outcome until Phase 1
  Closure resolves required blockers.
- Phase 1 Closure starts from issues `#35` through `#44`; P0/P1 items must close
  or be explicitly downgraded with evidence before Phase 2. After PRs `#46`,
  `#47`, and `#50`, and live branch-protection verification for `#38`, the
  remaining original open P0/P1 blocker is `#39`.
- Phase 1 Closure issue `#37` is closed through merged PR `#47` at merge commit
  `cb53e33a75ff6837a5498dfb0cc01c06decab8c5`, reconciling the trusted
  local/dev/test-only principal simulation contract with API behavior, tests,
  and contract docs.
- Phase 1 Closure issue `#42` is closed through merged PR `#50` at merge commit
  `b6235da1a5202ffc9dbde6284ad39f3e3ad70486`, hardening Stage 7 source
  evidence checksum binding with a shared canonical route/service/mock-provider
  helper, explicit evidence IDs/indexes, duplicate-key JSON rejection, and
  structured idempotency request checksums.
- Release posture remains No-Go until the remaining production-grade portion of
  Phase 1 P0/P1 blocker `#39` is resolved or explicitly downgraded with
  evidence.
- PR `#47` independent review residual risks are now durable follow-ups:
  issue `#48` for scoped project-lookup hardening and issue `#49` for
  simulated-actor idempotency resource caps, mirrored as `RR-036` and `RR-037`.

## Stage Ledger

| Stage | Status | Issue ledger | Pull request ledger | Quality gate state | Notes |
|---|---|---|---|---|---|
| Stage 0 | Complete, governance baseline active | `#14` closed | `#15` merged, `#23` merged | Executable and green | Operating model, quality gate, and repository guardrails are in place; product implementation remains blocked. |
| Stage 1 | Product/PRD hardening represented by PR `#26` | `#1` open, `#16` open | `#26` | Executable | `#1` is product strategy and PRD v1.0 hardening; `#16` remains the follow-on Spec Kit gate. Reconcile merge state after the GitHub merge event. |
| Stage 2 | Complete, merged to `main` | `#2` reconcile after merge | `#27` merged | Executable locally | Architecture, ADRs, threat model, security/privacy, AI safety/evaluation, portability, API, data model, observability, machine-readable semantic contract, human review checklist, branch scope, and provider defaults are hardened. |
| Stage 3 | Complete in Stage 4 branch baseline; GitHub reconciliation required | `#5` reconcile after merge | Reconcile after merge | Executable locally | Adds repo foundation manifests, health checks, frontend foundation, Docker build path, pre-commit, CI/security/eval workflows, dependency/security scan path, local setup docs, hardened workflow pins, exact-file scope checks, non-root containers, and fixture-backed eval smoke without product features beyond health checks. |
| Stage 4 | Complete, merged to `main` | `#4` reconcile after merge | PR `#29` merged | Executable locally at merge | First-slice backend RAG pipeline, mock providers, API tests, frontend workflow, deterministic eval smoke, Docker build coverage, quality gate, atomic-ingestion hardening, and sub-agent verification hardening merged through PR `#29`. |
| Stage 5 | Complete, merged to `main` | `#10` closed | PR `#30` merged | Executable at merge | RAG eval runner, prompt-injection guardrails, file-upload abuse tests, and observability metadata merged through PR `#30`. |
| Stage 6 | Complete, merged to `main` | `#11` closed | PR `#31` merged | Executable at merge | Translation, subtitles, mock/local voice adapter, downloadable artifacts, and Stage 6 quality checks merged through PR `#31`. |
| Stage 7 | Complete, merged to `main` | `#12` reconcile after merge | PR `#32` merged | Executable at merge | Mock/local avatar rendering adapter, demo export artifacts, provider config validation, render job status, consent/disclosure controls, artifact validation, UI preview/export workflow, and Stage 7 quality gate merged through commit `7f7196a`. |
| Stage 8 | Complete, merged to `main` | `#13` closed | PR `#33` merged | Executable at merge | Performance smoke tests, API latency budget checks, rate limiting, request size limits, upload MIME validation, dependency audit, Docker image scan, frontend Lighthouse checks, release checklist, runbook, demo seed data, portfolio README, and release-readiness review merged at `fb40113`. |
| Final Review | Complete, merged to `main` | `#6` closed | PR `#45` merged | Executable artifact gate | Independent review artifacts merged at `5a294c7`; outcome is No-Go until Phase 1 Closure resolves blockers. |
| Phase 1 Closure | In progress | `#35`, `#36`, `#37`, `#40`, `#41`, `#42`, `#55`, and `#58` closed; `#38` resolved with live settings evidence and required-context drift checking through merged PR `#53`; `#39`, `#43`, `#44`, `#48`, and `#49` open | PRs `#46`, `#47`, `#50`, `#53`, `#54`, `#56`, and `#59` merged | Executable governance gate added | `#39` now covers remaining production-grade durability/monitoring gaps after local restart recovery and ops status evidence. `#43`, `#44`, `#48`, and `#49` remain P2/follow-up unless they block Phase 1 correctness. |

## Issue Ledger

### Stage Issues

| Issue | State | Intended stage | Current interpretation |
|---|---|---|---|
| `#14` | Closed | Stage 0 | Canonical completed Stage 0 issue for repository guardrails and CI quality gates. |
| `#1` | Open | Stage 1 | Canonical Stage 1 product strategy and PRD v1.0 hardening issue. |
| `#16` | Open | Stage 1 follow-on | Spec Kit constitution/spec/plan/tasks gate that follows product/PRD hardening. |
| `#2` | Reconcile after merge | Stage 2 | Architecture, security, AI safety completed by merged PR `#27`; issue state must be reconciled with GitHub. |
| `#5` | Reconcile after merge | Stage 3 | Repo foundation and CI/CD gates are treated as complete in this Stage 4 branch baseline; reconcile exact GitHub state. |
| `#4` | Reconcile after merge | Stage 4 | First grounded-script vertical slice merged through PR `#29`; issue state must be reconciled with GitHub. |
| `#10` | Closed | Stage 5 | Evaluation, guardrails, observability completed by merged PR `#30`. |
| `#11` | Closed | Stage 6 | Multilingual scripts, subtitles, voice adapter completed by merged PR `#31`. |
| `#12` | Reconcile after merge | Stage 7 | Avatar rendering adapter and demo export completed by merged PR `#32`; issue state must be reconciled with GitHub. |
| `#13` | Closed | Stage 8 | Performance, security, release readiness completed by merged PR `#33`. |
| `#6` | Closed | Final Review | Independent reviewer pass completed by merged PR `#45`; outcome is No-Go pending Phase 1 Closure. |
| `#35` | Closed | Phase 1 P0 | Reconciled Stage 8 merge state in governance and release docs through merged PR `#46`. |
| `#36` | Closed | Phase 1 P0 | Reconciled executable Final Review gate and repository-tracked branch-policy evidence posture through merged PR `#46`; live branch-protection proof is recorded under issue `#38`. |
| `#37` | Closed | Phase 1 P1 | Trusted local/dev/test-only `X-Local-User-Id` simulation reconciled with API behavior, docs, and tests through merged PR `#47`. |
| `#38` | Resolved with evidence | Phase 1 P1 | Live GitHub `main` branch protection is enabled with strict required CI contexts, required PR review, admin enforcement, blocked force pushes, blocked deletions, and required conversation resolution through PR `#53`; `policy-gates` now runs `scripts/ci/verify_branch_protection.py` to fail on required-context and app-binding drift visible through GitHub's branch summary API, while strict/up-to-date and protected-branch detail settings remain human-only when GitHub denies the detail endpoint to the workflow token; direct pusher restrictions are unavailable on this user-owned repository per GitHub API validation. |
| `#39` | Open, partially remediated | Phase 1 P1 | Optional local JSON snapshots now cover Stage 4 project/document/run/RAG state, Stage 6 multilingual idempotency replay, and Stage 7 render/idempotency/artifact metadata; `/api/v1/ops/status` exposes bounded local posture metadata. Production go-live remains blocked until ACID/CAS durable metadata, cross-worker locking, migrations, backup/restore, production idempotency semantics, dashboards/alerts, first-hour watch, and rollback communications are reviewed. |
| `#40` | Closed | Phase 1 P0 | Canonical requirements traceability matrix reconciled through merged PR `#46`. |
| `#41` | Closed | Phase 1 P0 | Local demo durability and provider limits disclosed in portfolio/demo docs through merged PR `#46`. |
| `#42` | Closed | Phase 1 P1 | Stage 7 source evidence checksum binding hardened through merged PR `#50` by sharing one canonical route/service/mock-provider checksum definition, requiring explicit evidence IDs for positive counts, using structured idempotency checksums, and rejecting duplicate-key provider JSON artifacts. |
| `#43` | Open | Phase 1 P2 | Expand performance and integrated E2E evidence beyond local smoke. |
| `#44` | Open | Phase 1 P2 | Track telemetry, CSP, log-envelope, and stale risk-register hardening. |
| `#48` | Open | Pre-production/P2 hardening | Track scoped project-lookup hardening before production auth, durable storage, or stronger authorization-proof claims; created from PR `#47` independent API integrity review. It does not block local/mock Phase 1 demo review while production remains No-Go. |
| `#49` | Open | Pre-production/P2 hardening | Bound local idempotency records across simulated actors before local-demo durability, multi-worker, or production-readiness claims; created from PR `#47` independent performance/security review. It does not block local/mock Phase 1 demo review while production and multi-worker release remain No-Go. |
| `#55` | Closed | Phase 1 #39 follow-up | Preserved local durability restore-invariant work was triaged and hardened through PR `#56`, including Stage 4 graph/chunk/evaluation consistency, all-or-nothing local RAG chunk insertion across one or more prepared documents on embedding failure, terminal local snapshot write failure cleanup for failed-ingestion chunks, Stage 6 derived artifact consistency, Stage 7 artifact metadata consistency, failed-idempotency drops, stale-low counters, and operation-scoped rollback. It did not close `#39` or claim production durability. |
| `#58` | Closed | Phase 1 process follow-up | Governance-learning process scope for `PHF-006` merged through PR `#59`: added the reusable learning, allowed `docs/PROJECT_GOVERNANCE_LEARNINGS.md` in Phase 1 process-only branches, and covered that allowance with focused tests without expanding runtime/product scope. |

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
| `#29` | Merged | 2026-06-30 | Stage 4 first vertical slice from project upload to grounded script display merged to `main`; Stage 5 starts from this baseline. |
| `#30` | Merged | Reconcile exact merge date | Stage 5 evaluations, guardrails, observability, and quality evidence merged to `main`; Stage 6 starts from this baseline. |
| `#31` | Merged | Reconcile exact merge date | Stage 6 multilingual scripts, subtitles, mock/local voice adapter, downloadable artifacts, and quality evidence merged to `main`; Stage 7 starts from this baseline. |
| `#32` | Merged | 2026-07-01 | Stage 7 avatar rendering adapter and export merged to `main` at commit `7f7196a`; Stage 8 starts from this baseline. |
| `#33` | Merged | 2026-07-01 | Stage 8 performance, security hardening, and release-readiness PR linked to issue `#13`; merged at `fb40113`. |
| `#45` | Merged | 2026-07-01 | Final Review artifacts and executable review gate merged; outcome is No-Go until Phase 1 Closure. |
| `#46` | Merged | 2026-07-01 | Phase 1 Closure Module A governance and traceability PR for issues `#35`, `#36`, `#40`, and `#41`, with release-readiness, demo, golden-question, and quality-gate hardening; merged at `3131b3932c921a33fb6f45142d7fd7dbedb41792`. |
| `#47` | Merged | 2026-07-01 | Phase 1 Closure Module F security PR for issue `#37`; reconciles trusted local/dev/test-only principal simulation with implementation, API tests, and contract docs; merged at `cb53e33a75ff6837a5498dfb0cc01c06decab8c5`. |
| `#50` | Merged | 2026-07-01 | Phase 1 Closure Module B functional-flow PR for issue `#42`; hardens Stage 7 source evidence checksum binding through a canonical helper shared by the API route, service, and mock provider, with explicit evidence IDs, structured idempotency checksums, and duplicate-key provider JSON rejection; merged at `b6235da1a5202ffc9dbde6284ad39f3e3ad70486`. |
| `#53` | Merged | 2026-07-02 | Phase 1 Closure Module A governance PR for issue `#38`; merged at `b5205083d0d11db060c83c1a5156394263b50de5`, records live `main` branch protection evidence, adds required-context drift checking to `policy-gates`, documents strict required CI contexts, required PR review, admin enforcement, blocked force pushes/deletions, required conversation resolution, and the user-repository limitation on direct pusher restrictions. |
| `#54` | Merged | 2026-07-08 | Phase 1 Closure PR for issue `#39`; merged at `8b4ba05`, adding optional local JSON restart recovery, sensitive-snapshot documentation, redacted ops status evidence, monitoring posture visibility, process-hardening RCA/playbook gates, and reference-only `#39` protection so the production blocker is not auto-closed. |
| `#59` | Merged | 2026-07-09 | Phase 1 Closure process follow-up for issue `#58`; merged at `38ec53b`, adding governance-learning allowlist coverage for `docs/PROJECT_GOVERNANCE_LEARNINGS.md` without runtime-scope expansion. |

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
- Stage 3 issue/PR state still needs GitHub reconciliation after the Stage 3
  merge event.
- `.stage/current` is `8` in the Stage 8 branch. `make quality` dispatches to
  the executable `make stage8-quality` gate outside policy-only CI mode.
- Stage 8 PR CI now includes the `stage8 / performance lighthouse` budget status
  for Locust and Lighthouse checks; live GitHub `main` branch protection has
  been verified for issue `#38`, and `policy-gates` now checks required context
  drift through the branch summary API.
- Stage 8 final exhaustive review remediation updated ADR `0006` to document
  semantic-failure idempotency replay, exact Stage 6 voice-manifest schema
  validation, and Docker scanner fallback semantics as release-hardening
  architecture decisions.
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
- Stage 4 dependency preparation has added direct document-ingestion, provider,
  vector-type, and evaluation-fixture packages; ChromaDB and Ragas were removed
  from active dependencies because `pip-audit` reported vulnerabilities with no
  fixed versions.
- Stage 4 due recommended review items `RR-005` and `RR-009` through `RR-013`
  now have branch-local dispositions in `docs/RECOMMENDED_REVIEW_ITEMS.md`.
- Stage 6 dependency preparation has added `babel`, `langcodes`, `pydub`,
  `audioop-lts`, and `srt` for localization, language-code normalization,
  Python 3.13-compatible audio handling, and subtitle serialization;
  implementation and quality gates remain in progress.
- Stage 6 implementation now includes `TranslationProvider` and `TTSProvider`
  adapter interfaces, mock/local provider defaults, glossary preservation,
  SubRip subtitle export, unsupported-language handling, provider fallback, UI
  target-language controls, downloadable script/subtitle artifacts, locked
  pending/completed idempotency, post-provider glossary/citation validation,
  request boundary constraints, and safe artifact-link enablement.
- Stage 6 final PR review produced no Critical or Required findings; optional
  follow-ups are tracked as `RR-029` through `RR-031` in
  `docs/RECOMMENDED_REVIEW_ITEMS.md` for Stage 8 hardening/release readiness.
- Stage 7 UI/UX tooling activation installed `ui-ux-pro-max-cli@2.10.0`
  globally, initialized `.codex/skills/ui-ux-pro-max` with
  `uipro init --ai codex`, and recorded the tool in `docs/SKILL_LOCK.md` and
  `docs/THIRD_PARTY_NOTICES.md`; generated `.codex` skill files remain ignored
  and must not be committed.
- Stage 7 implementation now includes a mock/local avatar rendering adapter,
  `/avatar-renders` API route, strict local-only provider config model, render job
  status history, validated `text/html` demo export with active HTML content
  rejection, semantically bound `application/json` render manifest,
  self-contained `application/json` video export placeholder, provider
  metadata/config cross-checks, enum fallback reason validation, AI-generated
  avatar/video disclosure, affirmative synthetic avatar consent control, cloned
  identity disablement, idempotency replay/in-flight rejection and terminal
  failed-attempt replay, provider failure fallback, process-local render/artifact
  metadata storage, source citation/evaluation IDs and checksums, frontend
  source-matched demo preview, export artifact list, frontend artifact safety
  checks with checksum/content validation and blocked reasons, API/UI tests, and
  `scripts/quality/check_stage7_docs.py`.
- Stage 7 applies the Stage 6 provider-output validation learning from the
  start: provider config, render manifest, video placeholder, and downloadable
  artifacts are all validated before storage, response, or display.
- Stage 7 optional follow-ups are tracked as `RR-032` through `RR-035` in
  `docs/RECOMMENDED_REVIEW_ITEMS.md` for Stage 8 hardening/release readiness.
- Stage 7 post-review product-source follow-up is tracked as `RR-035` for the
  Stage 8 decision on source-run versus multilingual/subtitle-bound avatar
  rendering before real timed media export.
- GitHub issue and pull request state can drift from this file until the next governance PR updates the ledger, because repository checks are diff-scoped rather than GitHub-event-synced.

## Next Approved Actions

1. Complete the remaining production-grade portion of Phase 1 Closure P0/P1
   issue `#39` through an issue-linked `phase-1-closure-*` branch and PR, or
   record a reviewed No-Go exception with evidence.
   Closed follow-up issue `#55` hardened additional local restore invariants
   under the existing `#39` local-durability scope, but did not close `#39` or
   change the production No-Go posture.
2. Keep Phase 2 feature work blocked until P0/P1 items are closed or explicitly
   downgraded with evidence.
3. Keep production, multi-worker deployment, external provider use, real video
   export, and public synthetic-media distribution No-Go.
4. Run local quality and CI before merging each Phase 1 closure PR.
5. Create a release tag only after all Phase 1 gates pass and the Go/No-Go
   decision is updated by reviewed PR.

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
| 2026-06-30 | Stage 4 branch `stage4-grounded-script-generation` started for issue `#4`, advanced `.stage/current` to `4`, added first-slice dependency preparation, backend RAG/API workflow, frontend result display, deterministic eval smoke, and executable Stage 4 quality gate. |
| 2026-07-01 | Stage 6 branch `stage6-multilingual-subtitles-voice-adapter` advanced `.stage/current` to `6` and added multilingual generation, glossary preservation, subtitle artifacts, mock/local voice fallback, downloadable UI artifacts, and executable Stage 6 quality gate work under issue `#11`. |
| 2026-07-01 | Stage 6 independent review findings were remediated for idempotency, provider-output validation, request-boundary limits, provider-ready response schemas, frontend artifact safety, and docs/gate clarity. |
| 2026-07-01 | Stage 6 final PR review optional recommendations were tracked as `RR-029` through `RR-031` for Stage 8 hardening/release readiness. |
| 2026-07-01 | PR `#31` merged Stage 6 to `main`; Stage 7 branch `stage7-avatar-rendering-adapter-export` started for issue `#12`, advanced `.stage/current` to `7`, and activated UI/UX Pro Max CLI/skill guidance for avatar rendering and demo export design. |
| 2026-07-01 | Stage 7 implementation added mock/local avatar rendering, strict provider config validation, render lifecycle status, provider failure fallback, exact active-content-checked local HTML demo export, semantically bound strict JSON render manifest, self-contained strict JSON video placeholder artifact, source evidence IDs/checksums, source-matched preview/export-artifact UI, affirmative disclosure/consent controls, cloned identity rejection, semantic-validation and terminal failed idempotency replay, frontend checksum/content artifact validation, API/UI tests, and executable Stage 7 quality checks. |
| 2026-07-01 | PR `#32` merged Stage 7 to `main` at commit `7f7196a`; Stage 8 branch `stage8-performance-security-release-readiness` started for issue `#13`, advanced `.stage/current` to `8`, activated release-readiness skill guidance, and began performance/security/release hardening. |
| 2026-07-01 | PR `#33` opened for Stage 8 performance, security hardening, and release readiness; sub-agent review findings are being remediated before merge. |
| 2026-07-01 | Stage 8 review remediation added ADR `0006` for release hardening gates and removed a synthetic secret-assignment fixture that tripped repository guardrails. |
| 2026-07-01 | Stage 8 captured review-process failure analysis and the future ruthless-review protocol in `docs/REVIEW_RIGOR_RETROSPECTIVE.md`. |
| 2026-07-01 | Stage 8 added `docs/PROJECT_LEARNINGS_TRACKER.md` and linked it from `README.md` so reusable project learnings are discoverable for future applications. |
| 2026-07-01 | Stage 8 added `docs/PROJECT_GOVERNANCE_LEARNINGS.md` to capture reusable governance patterns including status tracking, recommended-review registers, stage gates, ADRs, traceability, third-party/tool locks, release evidence, and repository settings checks. |
| 2026-07-01 | Stage 8 final exhaustive review remediation updated ADR `0006` and status tracking for semantic-failure idempotency replay, exact Stage 6 voice-manifest validation, Docker scan exit-code handling, and branch-protection context documentation. |
| 2026-07-01 | Stage 8 final PR review reconciled `docs/REPOSITORY_GUARDRAILS.md` and the Stage 8 quality checker so the canonical branch-protection checklist includes `stage8 / performance lighthouse`. |
| 2026-07-01 | Final Review artifact branch added independent review reports under `docs/reviews/` and wired an executable Final Review artifact gate for `final-review-*` branches; Phase 1 closure remains tracked separately by Final Review follow-up issues. |
| 2026-07-01 | Phase 1 Closure started after PR `#45` merged; issues `#35` through `#44` classified and mapped to closure modules; release posture remains No-Go. |
| 2026-07-01 | Phase 1 Closure governance gate was hardened after cross-model review to protect Final Review No-Go inputs, parse issue/module tables, validate the golden-question schema, and distinguish governance checks from full CI/eval execution. |
| 2026-07-02 | PR `#46` recorded as the Phase 1 Closure Module A governance/traceability delivery PR for issues `#35`, `#36`, `#40`, and `#41`; later closure entries reconcile subsequent implementation blockers. |
| 2026-07-02 | Phase 1 Closure issue `#37` started on branch `phase-1-closure-37-local-principal-contract` and draft PR `#47` to reconcile the trusted local principal contract; later closure entries supersede this branch-start state. |
| 2026-07-02 | PR `#47` independent review residual risks were converted into GitHub issues `#48` and `#49` and recorded as `RR-036` and `RR-037` in `docs/RECOMMENDED_REVIEW_ITEMS.md`. |
| 2026-07-02 | Phase 1 Closure issue `#42` started through PR `#50` on branch `phase-1-closure-42-stage7-checksum-binding` to harden Stage 7 source evidence checksum binding through a canonical helper shared by the API route, Stage 7 service, and mock provider, plus explicit evidence IDs, structured idempotency checksums, and duplicate-key provider JSON rejection; later closure entries supersede this branch-start state. |
| 2026-07-02 | PRs `#47` and `#50` reconciled as merged and issues `#37` and `#42` reconciled as closed; original Phase 1 P0/P1 blockers now remain limited to `#38` branch-protection/ruleset evidence and `#39` production durability/monitoring, while `#48` and `#49` are classified as pre-production/P2 hardening that do not block local/mock Phase 1 demo review under the continuing production No-Go posture. |
| 2026-07-02 | Live GitHub `main` branch protection was enabled and verified for issue `#38` through PR `#53`, requiring strict status checks for `policy-gates`, `quality / secrets`, `quality / markdown`, `lint / typecheck / unit / api`, `frontend tests / playwright smoke`, `ci / docker build`, `secret scan / bandit / audit / semgrep`, `security / docker build`, `eval smoke`, and `stage8 / performance lighthouse`, with required PR review, admin enforcement, blocked force pushes, blocked deletions, and conversation resolution; direct pusher restrictions were attempted but GitHub rejected them for this user-owned repository because only organization repositories can have users and team restrictions. |
| 2026-07-03 | PR `#53` review feedback added `scripts/ci/verify_branch_protection.py` to the required `policy-gates` workflow so the branch summary API now fails CI if `main` loses `protected: true`, exact required CI contexts, `enforcement_level: everyone`, or GitHub Actions app bindings; the top-level risk register now treats Final Review risk artifacts as historical baseline for issue dispositions rather than the unreconciled current source. |
| 2026-07-03 | Phase 1 Closure issue `#39` branch `phase-1-closure-39-durability-monitoring` added optional file-backed JSON snapshots for Stage 4/6/7 local restart recovery, `/api/v1/ops/status` for bounded durability/monitoring posture metadata, and direct unit/API evidence; production release remains No-Go pending ACID/CAS durable metadata, cross-worker locking, migrations, backup/restore, production idempotency, dashboards/alerts, first-hour watch, and rollback communications. |
| 2026-07-08 | PR `#54` process-loop RCA added `docs/ENGINEERING_PROCESS_RCA.md` as a standing NarraTwin preflight reference and `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` as a reusable project-start operating model; release posture remains No-Go and issue `#39` remains open pending production-grade durability/monitoring review. |
| 2026-07-08 | PR `#54` external-review hardening linked the RCA/playbook from `AGENTS.md`, added CODEOWNERS coverage for process-critical guardrail files, made the `#39` auto-close guard issue-based rather than branch-name-only, and added a Stage 7 concurrent persist-failure regression so one failed render cannot erase another committed render from memory. |
| 2026-07-08 | PR `#54` adversarial sub-agent review hardening added `pull_request.edited` coverage for `policy-gates`, completed-preflight PR body validation, CODEOWNERS/status tracking for `.github/workflows/` and `scripts/ci/verify_branch_protection.py`, explicit issue `#39` branch-scope docs, Stage 6 concurrent rollback protection, and Stage 6/7 restore validation for tampered non-local provider claims. |
| 2026-07-08 | PR `#54` independent review follow-up hardened malformed local snapshot restore for Stage 4/6 failed idempotency rows and Stage 4/7 dangling references; guardrails now reject generic issue-closing keywords outside explicitly allowed canonical stage closures, require concrete preflight evidence categories with existing repo paths or URLs, and verify documented branch-protection settings drift rather than required status contexts alone. |
| 2026-07-08 | PR `#54` process-hardening follow-up made the RCA and new-project playbook require an executable durability restore and invariant-to-test matrix before future durability/process implementation; the PR template, repository guardrails, quality docs, Phase 1 gate, and guardrail tests now require shared matrix/test IDs, negative or old-behavior proof, and explicit human-only surfaces. |
| 2026-07-09 | PR `#54` review consolidation added `docs/reviews/PROCESS_HARDENING_FINDINGS.md` to track deduplicated sub-agent, cross-model, and blind-review process-hardening findings, with acceptance criteria and statuses for remaining false-pass risks. |
| 2026-07-09 | PR `#54` process-hardening follow-up closed the main false-pass loop by requiring full failure-matrix ID coverage, `pass`/`passed` completion statuses, concrete file/URL artifact references, human-only surface rows or explicit `N/A`, pre-implementation matrix/source evidence, and a separate `phase-1-closure-process-*` governance-only branch mode that rejects product runtime files. |
| 2026-07-09 | PR `#54` branch-protection verifier follow-up preserves live required-context drift checks while treating protected-branch detail fields as human-only when GitHub returns `Resource not accessible by integration` to the CI workflow token. |
| 2026-07-09 | PR `#54` guardrail follow-up marked the placeholder-host `0.0.0.0` string as a Bandit `B104` false positive because it is rejected input data, not a runtime bind address. |
| 2026-07-09 | Issue `#55` started to triage preserved post-PR `#54` local durability restore-invariant work on a fresh `phase-1-closure-39-*` branch, with a pre-implementation matrix recorded in the issue before applying the runtime stash. |
| 2026-07-09 | PR `#56` blind-review follow-up staged Stage 4 local RAG chunk embeddings before mutating the in-memory store, staged all prepared ingestion chunks before marking documents ingested, pruned failed-ingestion chunks after terminal local snapshot write failures without restoring the whole RAG store, and added public rollback regressions for single-document embedding failure cleanup, multi-document embedding failure cleanup, terminal-persist failed-ingestion chunk cleanup, concurrent ingestion chunk preservation, and concurrent-success preservation; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | PR `#56` governance-learning follow-up added a proactive next-step closeout practice to the new-project engineering playbook so agents state current state, recommended next action, alternatives, agent-owned next work, and human-owned gates before the owner has to ask. |
| 2026-07-09 | PR `#56` final review-note cleanup removed the unused local RAG `prune_to_documents` helper before merge; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | PR `#56` final blind-review cleanup removed unused Stage 4, Stage 6, and Stage 7 full-snapshot restore helpers so operation-scoped rollback remains the only retained local rollback path; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | Issue `#58` process-follow-up added a reusable governance lesson to `docs/PROJECT_GOVERNANCE_LEARNINGS.md` and updated the Phase 1 process-only allowlist in `docs/STAGE_ISSUE_PLAN.md` plus `scripts/quality/check_phase1_closure_docs.py` so governance-learning-only PRs are valid without runtime-scope expansion. |
| 2026-07-09 | PR `#59` merged the issue `#58` governance-learning allowlist follow-up at `38ec53b`; issue `#58` is closed and issue `#39` remains open with production durability still No-Go. |
