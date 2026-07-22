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

- Last reviewed date: 2026-07-22
- Current stage marker: `.stage/current = 8`
- Current implementation permission: Phase 1 Closure governance only. Demo
  Phase 0 planning for issue `#225` completed through PR `#226`; Checkpoint 1
  is accepted as local/fake disabled-default reviewer evidence only through
  merged PRs `#230`, `#236`, `#238`, `#242`, `#244`, `#246`, and `#248`.
  Issue `#247` is closed after the safe refusal UX repair. Issue `#249` remains
  open as the public Checkpoint 3 tracker after C3-PR1 planning/guardrails
  completed through merged PR `#250` at
  `41b262fa2431f55cd1c813eab4071968c1c96ba0`, with post-PR-250 status
  reconciliation tracked by issue `#251` and PR `#252`. The approved sequence
  remains Checkpoint 3A Non-Cloned Product-Faithful Controlled Demo first,
  followed by Checkpoint 3B cloned identity consent/provenance planning later,
  Checkpoint 3C clone-integrated controlled demo after those gates, and
  production later. Issue `#253` is closed after PR `#254` merged the first
  Checkpoint 3A child implementation checkpoint for the executable acceptance
  harness and API E2E foundation only; it does not complete Checkpoint 3A and leaves later
  language, media, access/quota/retention, security/observability,
  performance, browser, and output-correctness probes planned.
  No Phase 2 feature work, hosted
  deployment, production release tag, real avatar/video generation, cloned
  voice, cloned face, digital twin, real-person likeness, public URL, provider
  setup, provider SDKs, provider keys, provider account work, dashboard
  configuration, paid plan activation, wallet funding, model or voice selection,
  real provider calls, paid spend, public distribution, or production-readiness
  claim is permitted by issues `#225`, `#229`, `#235`, `#237`, `#241`, `#243`,
  `#245`, `#247`, `#249`, `#251`, `#253`, or `#255`.
  Issue `#39`
  media/provider/security rows are non-downgradeable for production Go unless
  the affected provider, media, export, and replay paths remain disabled.
- Current repo mode: Final Review has merged; Phase 1 Closure is active,
  PHF-020A structured-policy replacement has merged through issue `#184` and
  PR `#185`, PHF-020B StatusStateV1 normalization has merged through issue
  `#188` and PR `#189`, post-PR-189 status reconciliation has merged through
  issue `#190` and PR `#191`, post-PR-191 status reconciliation has merged
  through issue `#192` and PR `#193`, post-PR-193 status reconciliation has
  merged through issue `#194` and PR `#195`, post-PR-195 status reconciliation
  has merged through issue `#196` and PR `#197`, post-PR-197 status
  reconciliation has merged through issue `#198` and PR `#199`, post-PR-199
  status reconciliation has merged through issue `#200` and PR `#201`,
  post-PR-201 status reconciliation has merged through issue `#202` and PR
  `#203`, CH-M1-01 local/mock durable consent-chain repair has merged through
  issue `#204` and PR `#205`, post-PR-205 status reconciliation has merged
  through issue `#206` and PR `#207`, CH-M1-02 real-stack local evidence and
  the directly related quality-dispatch clarification have merged through PR
  `#210` with issues `#208` and `#209` closed, post-PR-210 status
  reconciliation has merged through issue `#211` and PR `#212`, Checkpoint A
  through Checkpoint B completed through issue `#213` and PR `#214`, issue
  `#155` is closed for the controlled local/mock Product Mode 1 checkpoint,
  post-PR-214 status reconciliation has merged through issue `#215` and PR
  `#216`, post-PR-216 status reconciliation has merged through issue `#217`
  and PR `#218`, post-PR-218 status reconciliation has merged through issue
  `#221` and PR `#222`, the terminal post-PR-222 loop-breaker issue `#223`
  and PR `#224` have merged and closed, issue `#225` completed Demo Phase 0
  planning through merged PR `#226`, issue `#229` completed Demo Checkpoint 1 PR
  1 through merged PR `#230`, issue `#235` completed Demo Checkpoint 1 PR 2
  through merged PR `#236`, issue `#237` completed Demo Checkpoint 1 PR 3
  through merged PR `#238`, issue `#241` completed Demo Checkpoint 1 PR 4
  through merged PR `#242`, issue `#243` completed Demo Checkpoint 1 PR 5
  through merged PR `#244`, issue `#245` completed Checkpoint 1
  acceptance hardening through merged PR `#246`, issue `#247` completed the
  local demo refused-run UX repair through merged PR `#248`, issue `#249`
  completed public-safe C3-PR1 planning/guardrails through merged PR `#250`,
  and issue `#251` completed post-PR-250 status reconciliation through PR
  `#252`,
  mutable current-state authority is normalized through the StatusStateV1 table
  below, and release posture is No-Go.
- Product implementation merged to `main`: Stage 8 performance, security
  hardening, and release-readiness work merged through PR `#33` at commit
  `fb40113`.
- Tracker enforcement scope: repository-tracked stage and governance changes in checked-in files.
  The PR that completes an issue must finalize `docs/STATUS.md` in the same PR
  with the intended post-merge target state and next approved work item.
  Routine post-merge facts such as merge SHA, issue closeout, branch deletion,
  and post-merge workflow URLs are recorded in PR/issue comments and must not
  create a successor status-only PR unless they change durable repository state
  and a human explicitly approves a terminal exception.
- Out-of-band GitHub reconciliation: PR `#45` merged the Final Review artifacts at
  commit `5a294c72d2b4b8cbbc0339f7bcb3f17089bddece`; Final Review issue `#6`
  is closed. Phase 1 Closure issues `#35`, `#36`, `#37`, `#40`, `#41`, and
  `#42` are closed through merged PRs `#46`, `#47`, and `#50`; issue `#38`
  has live GitHub branch-protection evidence and required-context drift checking
  recorded through merged PR `#53` at merge commit `b5205083d0d11db060c83c1a5156394263b50de5`,
  including the user-repository limitation on direct pusher restrictions; PR
  `#54` merged local file-backed restart recovery, `/api/v1/ops/status`, and
  process-hardening evidence at merge commit `8b4ba05`, while issue `#39`
  remains open for production-grade durability and monitoring; PR `#110`
  merged `CH-07` Stage 6 durable replay at merge commit
  `acccd6939ebe172b9a2d95f51fa96212035f55b0`, issue `#109` is closed, and
  PR `#116` merged the `CH-08` Stage 7 render artifact-state preflight at
  merge commit `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50`; issue `#115` is
  closed;
  issue `#55` closed through PR `#56` for additional local restore-invariant hardening; PR
  `#59` merged the governance-learning allowlist follow-up for issue `#58` at
  merge commit `38ec53b`; PR `#62` merged the Medium/Low PHF process-hardening
  follow-up for issue `#60` at merge commit `cf07ab8`; PR `#64` merged the
  issue `#39` Context 0 production-closure matrix; PR `#73` closed issue
  `#71`; PR `#74` closed issue `#72`; issues `#65`, `#66`, `#67`, `#68`,
  `#69`, and `#70` are closed through PRs `#75`, `#76`, `#77`, `#78`, `#79`,
  and `#80` respectively; PR `#85` merged the issue `#84` post-merge-main
  guardrail false-positive fix at merge commit `9cc2d767134c49dee234e59159b5010b6894bd2c`;
  PR `#87` merged the issue `#86` `CH-01` migration-baseline execution at
  merge commit `824a07c2bd546648b96d9ab555b63a8f2415898e`; PR `#90` merged the
  issue `#89` merge-closeout ownership codification at merge commit
  `c36a663df0b1a999db0042ca9e9d02fc508a0490`; issues `#84`, `#86`, and `#89`
  are closed; issue `#93` is closed for `CH-02` ACID/CAS storage-kernel
  execution; issue `#97` is closed for `CH-04` idempotency semantics through
  PR `#102`; issue `#95` is closed for `CH-05` lease fencing through PR
  `#103`; issue `#96` is closed for `CH-06` committed outbox through PR
  `#106`; issue `#107` is closed for `CH-03` Stage 4 durable graph through PR
  `#108` at merge commit `6449786069dd38eeaa5a4a31f5ed73cbfc52d248`; issue
  `#109` is closed for `CH-07` Stage 6 durable replay through PR `#110` at
  merge commit `acccd6939ebe172b9a2d95f51fa96212035f55b0`; issue `#115` is
  closed for the `CH-08` Stage 7 render artifact-state preflight through PR
  `#116` at merge commit `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50`; issue
  `#119` is closed for the `CH-08` Stage 7 render artifact-state implementation
  through PR `#120` at merge commit
  `af7215a5ceb7cefa81306773c1cfa8260435291e`; PR `#135` merged issue `#125`
  to `main` at merge commit `f94776f6602d4c6feec2412b4764a7368049a080`; issue
  `#138` and prerequisite issue `#151` are closed; issue `#181` is closed
  through PR `#182` at merge commit
  `3ea049cff0bf2157bea0bb5aedf73eb562753d17`, unblocking issue `#155`
  validation after the local Lighthouse `NO_FCP` prerequisite without product
  runtime, launch, provider, or production-posture change; GPF-A issue `#172`/PR
  `#173`, HPR issue `#174`/PR `#175`, GPF-B issue `#176`/PR `#177`, and GPF-C
  issue `#178`/PR `#179` are merged and closed out on `main` at
  `22d48b9edc0338d613d4926059fa9ef1ef329d1f`; stopped PRs `#166`, `#168`, and
  `#170` remain preserved evidence, not active implementation branches; issue
  `#155` is the serialized Product Mode 1 checkpoint controller; issue `#184`
  is complete through merged PR `#185` at
  `1179760d342d126c78ff7bd09002d064dc7aaa0e`; issue `#188` is closed after
  PR `#189` merged PHF-020B StatusStateV1 normalization at
  `a5a25bd95787d065c92733f9bcd655820659e5b0`; issue `#190` is closed after
  PR `#191` merged the post-PR-189 status reconciliation at
  `5d6704e746fac76d8c6703df81b16f21eb2dba60`; issue `#192` is closed after
  PR `#193` merged the post-PR-191 status reconciliation at
  `7131924937e5433d7de2517e14dd1a328d97a063`; issue `#194` is closed after
  PR `#195` merged the post-PR-193 status reconciliation at
  `409376eac66ffb17d80e816ec87b0e54df2ebb22` with post-merge main workflow
  quality run `29684509339` passing; issue `#196` is closed after PR `#197`
  merged the post-PR-195 status reconciliation at
  `924e378af611930decaba428ffcd1b5b69c00512` with post-merge main workflow
  quality run `29686868800` passing; issue `#198` is closed after PR `#199`
  merged the post-PR-197 status reconciliation at
  `a295bd18b6491ee794610d366d19c9548e046c56` with post-merge main workflow
  quality run `29689512124` passing; issue `#200` is closed after PR `#201`
  merged the post-PR-199 status reconciliation at
  `f01236756fa268bd4b90c7f536c57c0f96ba9cdc` with post-merge main workflow
  quality run `29691443045` passing; live GitHub also shows issue
  `#123` closed through PR `#124` at
  `ec2456cba9874d4289c91236de43f73786556503`, issue `#128` closed through PR
  `#133` at `384c15ac67810d30096794500da1c90ce056dd54`, and issue `#127`
  closed through PR `#134` at
  `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9`; issue `#8` remains open; and
  issues `#43`, `#44`, `#48`, and `#49` remain open.
- Stage 8 may add performance smoke tests, API latency budgets, frontend
  Lighthouse checks, rate limiting, request size limits, upload MIME validation,
  dependency audit, Docker image scan, release checklist, runbook, demo seed
  data, portfolio README, and release-readiness review evidence.
- Stage 8 PR `#33` is merged and Stage 8 issue `#13` is closed.
- Stage 8 final exhaustive review remediation is recorded in ADR `0006`,
  including semantic-failure idempotency replay, exact Stage 6 voice-manifest
  validation, Docker scan exit-code handling, and branch-protection context
  documentation.

## StatusStateV1

This table is the normalized mutable current-state authority for PHF-020B. It
does not replace the PHF-020A Product Mode policy tables in `docs/PHASE_PLAN.md`;
it records only the current repository state, open issue boundaries, preserved
evidence, next action posture, and prohibited work.

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
| SSV1-BASELINE | merge-baseline | PR #187 | merged | merged | Current mutable state starts after PR #187 merged at 24bc1f581d005777ef16df2a2228a936eb86d926. |
| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure | Phase 1 Closure remains active; release posture remains No-Go. |
| SSV1-NEXT | next-action | issue #249 / checkpoint3a-next-child-selection | checkpoint3a-cp1-acceptance-api-e2e-complete | checkpoint3a-cp1-acceptance-api-e2e-complete | Demo Phase 0 planning completed through issue #225 and PR #226. Checkpoint 1 local/fake disabled-default reviewer evidence is complete through merged PRs #230, #236, #238, #242, #244, #246, and #248, with issue #247 closed after the safe refusal UX repair. C3-PR1 planning and guardrails completed through issue #249 and merged PR #250 at 41b262fa2431f55cd1c813eab4071968c1c96ba0, with post-merge status reconciliation through issue #251 and PR #252. Issue #253 closed after PR #254 merged the first Checkpoint 3A child implementation checkpoint: an executable Checkpoint 3 acceptance harness plus API E2E foundation only. Issue #249 remains open as the public Checkpoint 3 tracker and the next approved action is a future issue-linked Checkpoint 3A child slice for one of the remaining planned probes. This state does not complete Checkpoint 3A. Hosted deployment, public URLs, provider account setup, dashboard configuration, paid plan activation, wallet funding, paid spend, real provider calls, cloned voice, cloned face, digital twin, real-person likeness, public distribution, and production-readiness claims remain forbidden. |
| SSV1-ISSUE8 | product-definition-parent | #8 | open | open | Issue #8 remains open for its separate product-definition acceptance contract. |
| SSV1-ISSUE155 | product-mode-controller | #155 | closed | closed | Issue #155 is closed for the controlled local/mock Product Mode 1 checkpoint after issue #213 and PR #214 completed Checkpoint A through Checkpoint B with latest-head human approval and evidence. |
| SSV1-PREDECESSOR | stopped-evidence | #162/#163/#166/#167/#168 | preserved | preserved | Stopped predecessor evidence remains preserved and must not be resumed, patched, rebased, merged, closed, deleted, or rewritten. |
| SSV1-FORBIDDEN | prohibited-work | repository | forbidden | forbidden | Product Mode 2, hosted launch, provider enablement, public media distribution, production-readiness claims, and product/runtime implementation outside approved follow-up scope remain forbidden. |

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
- [Skill Selection And Evidence](SKILL_SELECTION_AND_EVIDENCE.md)
- [New Project Engineering Playbook](templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md)
- GitHub issues and pull requests for execution history

## Executive Status

- Stage 0 governance is complete in the current repository state, and Stage 1 product/PRD hardening artifacts are represented by PR `#26`.
- `docs/STATUS.md` is the in-repo governance ledger for stage coverage, issue and PR references, open gaps, and next approved actions.
- Repository checks enforce updates to this file only for repository-tracked governance changes that are visible in the CI diff range.
- GitHub-side state that changes outside a repository diff must be recorded in
  the relevant PR/issue comments first. Update this file later only when stale
  checked-in state would misdirect active work, when a material governance
  state changes, or when the correction is bundled into a substantive PR; the
  local quality gate does not claim live GitHub synchronization.
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
  `#47`, `#50`, and `#108`, and live branch-protection verification for `#38`,
  the remaining original open P0/P1 blocker is `#39`.
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
- PR `#108` closed issue `#107` for `CH-03` Stage 4 durable graph after the
  scoped durable-graph adapter, metadata validation, replay binding, outbox
  binding, and supporting docs/tests were merged.

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
| Phase 1 Closure | In progress | `#35`, `#36`, `#37`, `#40`, `#41`, `#42`, `#55`, `#58`, `#60`, `#65`, `#66`, `#67`, `#68`, `#69`, `#70`, `#71`, `#72`, `#84`, `#86`, `#89`, `#93`, `#95`, `#96`, `#97`, `#107`, `#109`, `#111`, `#115`, `#119`, `#123`, `#125`, `#127`, `#128`, `#155`, `#184`, `#188`, `#190`, `#192`, `#194`, `#196`, `#198`, `#200`, `#202`, `#204`, `#206`, `#208`, `#209`, `#211`, `#213`, `#215`, `#217`, `#219`, `#221`, `#223`, and `#225` closed; `#38` resolved with live settings evidence and required-context drift checking through merged PR `#53`; `#39`, `#43`, `#44`, `#48`, `#49`, and `#126` open | PRs `#46`, `#47`, `#50`, `#53`, `#54`, `#56`, `#59`, `#62`, `#63`, `#64`, `#73`, `#74`, `#75`, `#76`, `#77`, `#78`, `#79`, `#80`, `#85`, `#87`, `#90`, `#92`, `#94`, `#98`, `#102`, `#103`, `#106`, `#108`, `#110`, `#112`, `#116`, `#120`, `#124`, `#133`, `#134`, `#135`, `#185`, `#189`, `#191`, `#193`, `#195`, `#197`, `#199`, `#201`, `#203`, `#205`, `#207`, `#210`, `#212`, `#214`, `#216`, `#218`, `#220`, `#222`, `#224`, and `#226` merged | Executable governance gate added | `#39` remains open as the remaining P1 production blocker despite context planning progress across `#65`-`#70`. Issues `#65`-`#70` are closed through PRs `#75`-`#80` respectively. `#71` and `#72` are closed process-hardening follow-ups through PRs `#73` and `#74`. Issue `#86` completed `CH-01` migration-baseline execution for `DUR-MIG-001` through merged PR `#87`. Issue `#93` completed `CH-02` ACID/CAS storage-kernel execution for `DUR-ACID-001` through merged PR `#94`. Issue `#97` completed `CH-04` idempotency semantics for `DUR-IDEMP-001` through merged PR `#102`. Issue `#95` completed `CH-05` lease fencing for `DUR-LEASE-001` through merged PR `#103`. Issue `#96` completed `CH-06` committed outbox for `DUR-OUTBOX-001` through merged PR `#106`. Issue `#107` completed `CH-03` Stage 4 durable graph for `DUR-STAGE4-001` through merged PR `#108`. Issue `#109` is closed for `CH-07` Stage 6 durable replay through PR `#110` at merge commit `acccd6939ebe172b9a2d95f51fa96212035f55b0`. Issue `#115` completed `CH-08` Stage 7 render artifact-state preflight through PR `#116` at merge commit `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50`, scoped to branch reservation and evidence mapping for render-status history, artifact metadata consistency, consumed-consent binding, and terminal persist rollback. Issue `#119` completed `CH-08` Stage 7 render artifact-state implementation through merged PR `#120` at `af7215a5ceb7cefa81306773c1cfa8260435291e`, keeping issue `#39` and provenance/disclosure/provider/retention/untrusted-input closure rows open. Issue `#123` is closed through merged PR `#124` at `ec2456cba9874d4289c91236de43f73786556503` for the narrow `CH-09` technical rollback compatibility trust-boundary slice while `DUR-ROLLBACK-001` and issue `#39` remain open. Issue `#128` is closed through merged PR `#133` at `384c15ac67810d30096794500da1c90ce056dd54` for the narrow `CH-10` production metrics contract slice while `OPS-METRICS-001` and issue `#39` remain open. Issue `#127` is closed through merged PR `#134` at `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9` for the narrow `CH-11` SLO and error-budget contract slice while `OPS-SLO-001` and issue `#39` remain open. Issue `#125` is closed through merged PR `#135` at `f94776f6602d4c6feec2412b4764a7368049a080` for a local restore-integrity drill that exercises only the existing file-backed Stage 4/6/7 state surface for `DUR-RESTORE-001` without claiming production backup/restore closure. Issue `#184` completed PHF-020A structured Product Mode policy authority through merged PR `#185` at `1179760d342d126c78ff7bd09002d064dc7aaa0e`; issue `#188` completed PHF-020B StatusStateV1 normalization through merged PR `#189`; issue `#190`, `#192`, `#194`, `#196`, `#198`, `#200`, `#202`, `#206`, and `#211` completed repository-ledger reconciliations through merged PRs `#191`, `#193`, `#195`, `#197`, `#199`, `#201`, `#203`, `#207`, and `#212`; issue `#204` completed CH-M1-01 through PR `#205`; issues `#208` and `#209` completed CH-M1-02 through PR `#210`; issue `#213` completed Checkpoint A through Checkpoint B local/mock evidence through PR `#214` at merge commit `cb0d94b5e5963473de41f1a1a3d4aebec714677e`, and controller issue `#155` is closed for the controlled local/mock checkpoint only. Issue `#8`, stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`, issue `#39`, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, and production boundaries remain unchanged. Issue `#126` remains open for the narrow repo-checked `CH-14` restore-readiness contract above the local `#125` drill while final production restore proof remains open. Issue `#215` completed the post-PR-214 status reconciliation through PR `#216` at merge commit `6e42b452d6cfac357a26b5da6c3ab77407d7d975`; issue `#217` completed the post-PR-216 status reconciliation through PR `#218` at merge commit `f396adb9bd9edd98b1e7fa20e27b81d83a6aa81e` after PR `#220` removed the inherited dependency-audit blocker; issue `#221` completed the post-PR-218 status reconciliation through PR `#222` at merge commit `f279097357b32c64e29b194618cfb36eee071adb`; issue `#223` completed the terminal post-PR-222 loop-breaker through merged PR `#224` at `7cb19e86844e75a5766ec732ca08b18dd931680f`; issue `#225` completed Demo Phase 0 planning through merged PR `#226` at `8d8f1d3dc1a1393356a7e5b95e7404d6b92e40dc`. |

| GPF prerequisite | Capability | Issue | Pull request | Repository-tree evidence |
|---|---|---|---|---|
| GPF-A | Offline GovernancePreflightV1 core | `#172` closed | PR `#173` merged | offline schema and semantic validator present |
| GPF-B | Prospective repository integration | `#176` closed | PR `#177` merged | offline prospective preflight enforcement present |
| GPF-C | CI-only GitHub evidence | `#178` closed | PR `#179` merged | CI GitHub evidence verifier present |
| HPR | Human-readable pull-request reviewer overview | `#174` closed | PR `#175` merged | five-point template, agent policy, and bounded PR-body enforcement |

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
| `#39` | Open, partially remediated | Phase 1 P1 | Production durability/monitoring contract for Context 0 lives in `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`; execution sequencing, per-chunk Definition of Done, parallelization, review-agent protocol, fix re-review, and deployment transition strategy live in `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`. PR guardrails bind issue-closing wording for `#39` to all matrix rows being marked `Closed` with row-specific evidence, canonical sensitive-row contract terms, and verified concrete same-repository child issue/PR URLs. Optional local JSON snapshots now cover Stage 4 project/document/run/RAG state, Stage 6 multilingual idempotency replay, and Stage 7 render/idempotency/artifact metadata; `/api/v1/ops/status` exposes bounded local posture metadata. Context 2 planning for `DUR-IDEMP-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001` is tracked in Issue `#66` (`docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`, `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`). Context 6 planning for rollback/media/provider/retention and untrusted-input governance completed in Issue `#70` and PR `#80`. Issue `#109` is closed through PR `#110` at merge commit `acccd6939ebe172b9a2d95f51fa96212035f55b0`; Issue `#115` is closed through PR `#116` at merge commit `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50` for `CH-08` Stage 7 render artifact-state preflight only; Issue `#119` is closed through PR `#120` at merge commit `af7215a5ceb7cefa81306773c1cfa8260435291e` for the `CH-08` Stage 7 render artifact-state implementation chunk; Issue `#123` is closed through PR `#124` at merge commit `ec2456cba9874d4289c91236de43f73786556503` for the narrow `CH-09` technical rollback compatibility trust-boundary slice; Issue `#128` is closed through PR `#133` at merge commit `384c15ac67810d30096794500da1c90ce056dd54` for the narrow `CH-10` production metrics contract slice; Issue `#127` is closed through PR `#134` at merge commit `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9` for the narrow `CH-11` SLO and error-budget contract slice; Issue `#125` is closed through PR `#135` at merge commit `f94776f6602d4c6feec2412b4764a7368049a080` for a local restore-integrity drill for the existing file-backed Stage 4/6/7 state surface under `DUR-RESTORE-001` without changing the production closure posture; and Issue `#126` now tracks the later repo-checked `CH-14` restore-readiness contract, while successful production restore proof still remains open. Issue `#39`, matrix row `OPS-METRICS-001`, matrix row `OPS-SLO-001`, matrix row `DUR-STAGE7-001`, matrix row `DUR-ROLLBACK-001`, matrix row `DUR-RESTORE-001`, and provenance/disclosure/provider/retention/untrusted-input closure remain open. Production go-live remains blocked until ACID/CAS durable metadata, cross-worker locking, migrations, backup/restore, production idempotency semantics, SLO/error-budget thresholds, dashboards/alerts, first-hour watch, rollback communications (`CTX6-ROLLBACK-EVID-001`), deletion/erasure semantics (`CTX6-SEC-RETENTION-EVID-001`), provider-disabled posture (`CTX6-PROVIDER-POSTURE-EVID-001`), untrusted durable/replayed input controls (`CTX6-SEC-UNTRUSTED-EVID-001`), and final successful restore drill evidence (`CTX4-RESTORE-EVID-001`) are reviewed. |
| `#40` | Closed | Phase 1 P0 | Canonical requirements traceability matrix reconciled through merged PR `#46`. |
| `#41` | Closed | Phase 1 P0 | Local demo durability and provider limits disclosed in portfolio/demo docs through merged PR `#46`. |
| `#42` | Closed | Phase 1 P1 | Stage 7 source evidence checksum binding hardened through merged PR `#50` by sharing one canonical route/service/mock-provider checksum definition, requiring explicit evidence IDs for positive counts, using structured idempotency checksums, and rejecting duplicate-key provider JSON artifacts. |
| `#43` | Open | Phase 1 P2 | Expand performance and integrated E2E evidence beyond local smoke. |
| `#44` | Open | Phase 1 P2 | Track telemetry, CSP, log-envelope, and stale risk-register hardening. |
| `#48` | Open | Pre-production/P2 hardening | Track scoped project-lookup hardening before production auth, durable storage, or stronger authorization-proof claims; created from PR `#47` independent API integrity review. It does not block local/mock Phase 1 demo review while production remains No-Go. |
| `#49` | Open | Pre-production/P2 hardening | Bound local idempotency records across simulated actors before local-demo durability, multi-worker, or production-readiness claims; created from PR `#47` independent performance/security review. It does not block local/mock Phase 1 demo review while production and multi-worker release remain No-Go. |
| `#55` | Closed | Phase 1 #39 follow-up | Preserved local durability restore-invariant work was triaged and hardened through PR `#56`, including Stage 4 graph/chunk/evaluation consistency, all-or-nothing local RAG chunk insertion across one or more prepared documents on embedding failure, terminal local snapshot write failure cleanup for failed-ingestion chunks, Stage 6 derived artifact consistency, Stage 7 artifact metadata consistency, failed-idempotency drops, stale-low counters, and operation-scoped rollback. It did not close `#39` or claim production durability. |
| `#58` | Closed | Phase 1 process follow-up | Governance-learning process scope for `PHF-006` merged through PR `#59`: added the reusable learning, allowed `docs/PROJECT_GOVERNANCE_LEARNINGS.md` in Phase 1 process-only branches, and covered that allowance with focused tests without expanding runtime/product scope. |
| `#60` | Closed | Phase 1 process follow-up | Medium/Low PHF process-hardening completed through merged PR `#62` at `cf07ab8`: PHF matrix parsing, stricter result-bearing PR-body validation evidence, source-evidence binding inheritance, human-only merge-message surfacing, and related process-loop reduction landed without product/runtime feature implementation. |
| `#71` | Closed | Phase 1 process follow-up | Always-on repository-guardrail structural checks for `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` (`#39` matrix IDs, row shape, status, duplicates, unexpected IDs, and placeholders) merged through PR `#73` while keeping `#39` close-attempt behavior unchanged. |
| `#72` | Closed | Phase 1 process follow-up | PR `#74` hardened future `#39` final row-closure records so durability, operations, media, security, and provider rows require concrete evidence types, child PRs distinct from Context 0 PR `#64`, and merged child PR provenance when GitHub API validation is available. Runtime and infrastructure scope remain untouched. |
| `#84` | Closed | Phase 1 process follow-up | PR `#85` fixed the post-merge `main` push guardrail false positive so GitHub-generated merge pushes from PRs merged to `main` are allowed while true direct pushes remain rejected. Issue `#39` remains open and Phase 1 No-Go posture is unchanged. |
| `#89` | Closed | Phase 1 process follow-up | Codified approved-PR merge-closeout as agent-owned baseline work through merged PR `#90`, updating repo instructions and the reusable project playbook so future sessions and future projects do not rely on user reminders for post-approval hygiene. |
| `#65` | Closed | Phase 1 follow-on | PostgreSQL durability ADR and production schema-boundary contract for issue `#39` context 1 (`docs/ADR/0008-postgresql-durability-schema-boundary.md`), closed through PR `#75`. |
| `#66` | Closed | Phase 1 follow-on | Context 2 decomposition for issue `#39`: advisory idempotency/lease/outbox contract and one-to-one evidence mapping (`docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`, `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`), closed through PR `#76`. |
| `#67` | Closed | Phase 1 follow-on | Context 3 migration/rollback compatibility planning for issue `#39`, completed in PR `#77`; advisory-only `DUR-MIG-001` and `DUR-ROLLBACK-001` planning. Runtime migration execution remains deferred. |
| `#68` | Closed | Phase 1 follow-on | Context 4 backup/restore planning for issue `#39` completed in PR `#78`; advisory-only `DUR-RESTORE-001`, `OPS-METRICS-001`, and `OPS-SLO-001` planning. Runtime backup tooling, restore execution, and storage operators remain deferred. |
| `#69` | Closed | Phase 1 follow-on | Context 5 operations monitoring and watch planning for issue `#39`, completed in PR `#79`; advisory planning only, runtime dashboards/alert integrations/watch automation deferred. |
| `#70` | Closed | Phase 1 follow-on | Context 6 rollback/media/privacy/provider-posture/replay-input planning for issue `#39` completed through PR `#80` in `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`; planned evidence IDs are `CTX6-ROLLBACK-EVID-001`, `CTX6-MEDIA-CONSENT-EVID-001`, `CTX6-MEDIA-REVOKE-EVID-001`, `CTX6-MEDIA-PROVENANCE-EVID-001`, `CTX6-MEDIA-DISCLOSURE-EVID-001`, `CTX6-PROVIDER-POSTURE-EVID-001`, `CTX6-SEC-RETENTION-EVID-001`, `CTX6-SEC-UNTRUSTED-EVID-001`, and `CTX6-GOV-SCOPE-EVID-001`. Issue `#39` remains open and these production-grade matrix rows remain `Open`. |
| `#86` | Closed | Phase 1 follow-on | `CH-01` migration baseline execution for `DUR-MIG-001` completed through merged PR `#87` at `824a07c2bd546648b96d9ab555b63a8f2415898e`; scope remained limited to a versioned migration runner, focused tests, branch-scope guardrails, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#93` | Closed | Phase 1 follow-on | `CH-02` ACID/CAS storage-kernel execution for `DUR-ACID-001` completed through merged PR `#94`; scope remained limited to the storage contract kernel, conflict/replay/stale-write tests, branch-scope guardrails, and supporting ADR/status/traceability updates while issue `#39` remained open. |
| `#95` | Closed | Phase 1 follow-on | `CH-05` lease fencing execution for `DUR-LEASE-001` completed through merged PR `#103` at `3146a91b7fa3cf55d3aab3feae48d196e82b0f36`; scope remained limited to storage-kernel lease acquire/heartbeat/expiry/reclaim semantics, monotonic fencing tokens, stale-writer rejection, branch-scope guardrails, and supporting ADR/status/traceability updates while issue `#39` remained open. |
| `#96` | Closed | Phase 1 follow-on | `CH-06` committed outbox execution for `DUR-OUTBOX-001` completed through merged PR `#106` at `d0a2c80f084d8ec9e25b24b841e4f22031953a73`; scope remained limited to same-transaction state/event writes, at-least-once dispatch semantics, idempotent consumer policy, branch-scope guardrails, and supporting ADR/status/traceability updates while issue `#39` remained open. |
| `#97` | Closed | Phase 1 follow-on | `CH-04` idempotency semantics execution for `DUR-IDEMP-001` completed through merged PR `#102` at `947a96891fd84085b6fce433e604a8e249b25c23`; scope remained limited to canonical operation identity, payload-hash conflict guarding, terminal replay behavior, stale-owner rejection, branch-scope guardrails, and supporting ADR/status/traceability updates while issue `#39` remained open. |
| `#107` | Closed | Phase 1 follow-on | `CH-03` Stage 4 durable graph execution for `DUR-STAGE4-001` completed through merged PR `#108` at `6449786069dd38eeaa5a4a31f5ed73cbfc52d248`; scope remained limited to project/document/chunk/run/evaluation durable graph metadata, replay/conflict behavior, outbox binding, branch-scope guardrails, and supporting ADR/status/traceability updates while issue `#39` remains open. |
| `#109` | Closed | Phase 1 follow-on | `CH-07` Stage 6 durable replay execution for `DUR-STAGE6-001` completed through merged PR `#110` at `acccd6939ebe172b9a2d95f51fa96212035f55b0`; scope remained limited to Stage 6 durable replay state, source/evaluation provenance binding, tenant/project/actor/source-run linkage, source-text checksum validation, terminal idempotency replay, checksum-based dedupe, branch-scope guardrails, and supporting API/status/traceability updates while issue `#39` remained open. |
| `#111` | Closed | Phase 1 follow-on | `CH-16` consent capture completed through merged PR `#112` at `1f3d66d9b1b545e5d5c41e88a83cc731a2a8b31a`; scope remained limited to durable affirmative synthetic-avatar consent records, scoped/idempotent consent replay, restore hardening, Stage 7 durable consent gating, and supporting ADR/status/traceability updates while issue `#39` remained open. |
| `#115` | Closed | Phase 1 follow-on | `CH-08` Stage 7 render artifact-state preflight for `DUR-STAGE7-001` completed through merged PR `#116` at `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50`; scope remained limited to branch reservation, invariant/evidence mapping, dependency ancestry, and guardrail coverage for render-status history, artifact metadata consistency, consumed-consent binding, and terminal persist rollback while issue `#39` remained open and provenance/disclosure/provider/retention/untrusted-input rows remained open. |
| `#119` | Closed | Phase 1 follow-on | `CH-08` Stage 7 render artifact-state implementation for `DUR-STAGE7-001` completed through merged PR `#120` at `af7215a5ceb7cefa81306773c1cfa8260435291e`; scope remained limited to restored legal terminal render-status history validation, mandatory persisted render request-checksum/idempotency binding, restored render ownership-scope validation, restored render idempotency request-checksum and cross-scope rejection, restored failed idempotency dropping, artifact metadata consistency, consumed-consent binding evidence, terminal persist rollback evidence, and supporting API/status/traceability updates while issue `#39` remained open. |
| `#123` | Closed | Phase 1 follow-on | `CH-09` technical rollback compatibility for `DUR-ROLLBACK-001` completed through merged PR `#124` at `ec2456cba9874d4289c91236de43f73786556503`; scope was limited to a reviewed out-of-band proof-source boundary, self-attested rollback-proof blocking, forward repair, schema-version/compatibility-window enforcement, no false down-migration support claim, and supporting migration/traceability/status updates while issue `#39` and the broader `DUR-ROLLBACK-001` production closure row remain open. |
| `#125` | Closed | Phase 1 follow-on | Local restore-integrity drill for `DUR-RESTORE-001` completed through merged PR `#135` at `f94776f6602d4c6feec2412b4764a7368049a080`; scope stayed limited to the existing optional file-backed Stage 4/6/7 state, copied-file checksum parity, restored record-count parity, and replay-safe idempotent re-execution after restore. It did not claim production backup/restore, restore metrics, RTO/RPO proof, retention/re-delete behavior, or issue `#39` closure. |
| `#126` | Open | Phase 1 follow-on | `CH-14` restore-readiness contract merged through PR `#137`; scope is limited to repo-checked composition of merged `#125` local restore evidence plus the current repo-baselined `CH-10` and `CH-11` restore-adjacent contract artifacts, explicit human-only proof surfaces, and anti-overclaim guardrails. It does not claim successful production restore execution, final RTO/RPO proof, restore metrics export, operational signoff, or issue `#39` closure. |
| `#127` | Closed | Phase 1 follow-on | `CH-11` SLO and error-budget contract for `OPS-SLO-001` completed through merged PR `#134` at `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9`; scope stayed limited to repo-checked threshold semantics and breach-action contract evidence while dashboards, watch execution, restore proof, rollback communications, issue `#39`, and the broader `OPS-SLO-001` production closure row remain open. |
| `#128` | Closed | Phase 1 follow-on | `CH-10` production metrics contract for `OPS-METRICS-001` completed through merged PR `#133` at `384c15ac67810d30096794500da1c90ce056dd54`; scope stayed limited to metric names and current emission boundaries while downstream CH-11 through CH-15 evidence, issue `#39`, and the broader `OPS-METRICS-001` production closure row remain open. |
| `#139` | Open, blocked on production-like prerequisites | Phase 1 follow-on | Parent tracker for production-like restore readiness. Issues `#141`-`#149` separate platform choice, adapters, environment, backups, synthetic validation, runbook, observability, and readiness review. It does not itself satisfy `DUR-RESTORE-001`. |
| `#141` | Open, architecture recorded; human approvals blocked | Phase 1 follow-on | Documentation baseline merged through PR `#153` at `2fb5569`. Selects Amazon RDS for PostgreSQL 17.10 Multi-AZ plus versioned S3 artifact/control buckets in `ap-south-1` for production-like durability evidence; defines Stage 4/6/7 state/object ownership, separately signed contiguous deletion journal plus current CH-17 revocation handoff, restricted catalog/reviewer export, PITR IAM-auth/post-create engine checks, exact OIDC workflow/environment controls, bounded S3 copy, pre-create cleanup/inventory proof, complete RTO boundary, immutable-cutoff RPO calculation, and acceptance handoffs for `#142`-`#149`. AWS is not required for local development or the controlled local mock demo; `docs/LAUNCH_LEVELS.md` separates local, hosted-internal, soft-launch, production-like-validation, and production boundaries. No environment, backup/version source, restore target, or restore evidence has been verified. Cost/account/region, role assignment, and same-account/shared-RDS-key Security exception approvals block the AWS production-like path, not local demo use. |
| `#142` | Open, depends on `#141` | Phase 1 follow-on | Implement real connection-backed PostgreSQL and migration execution after the platform decision is approved. |
| `#143` | Open, depends on `#141`, `#142` | Phase 1 follow-on | Move Stage 4/6/7 business state onto PostgreSQL; publish approved bytes through an S3-version-first durable-intent/compensation contract; deliver contiguous integrity-linked deletion events with crash/retry/orphan/unavailable-object evidence. |
| `#144` | Open, depends on `#141` and Security approval | Phase 1 follow-on | Provision the private Multi-AZ RDS source and isolated restore landing zone/template plus distinct source/restore/control S3 buckets through reviewed IaC. Verify exact workflow/environment OIDC, IAM-auth target input, pre/post engine version and live configuration; PITR later creates the target. |
| `#145` | Open, depends on `#141`, `#144` | Phase 1 follow-on | Configure 14-day RDS PITR, at least 15-day S3 version retention, unique-key/version-aware Object-Locked journal, separately signed integrity manifest/rollback anchor, KMS safeguards, restricted catalog and reviewer-export boundary; no backup/version source is currently evidenced. |
| `#146` | Open, depends on `#141`, `#143`, `#144`, `#145` | Phase 1 follow-on | Create the synthetic Stage 4/6/7 database/object seed, contiguous integrity-linked deletion event, immutable source cutoff/server commit sequence, checksums, corruption cases, and validator in the selected landing zone. |
| `#147` | Open, depends on `#144`, `#145`, `#146` | Phase 1 follow-on | Implement the not-yet-executed PITR/exact-S3-Version runbook, explicit supported target parameters and live checks, `<=5,000,000,000 bytes` copy bound, journal/revocation handoff, source deny, pre-create deadline, exact no-snapshot/no-backup teardown, separately scoped RDS/S3 cleanup/live-inventory authority and next-exercise block. |
| `#148` | Open, depends on `#130`, `#141`, `#144`, `#145`, `#146`, `#147` | Phase 1 follow-on | Implement RDS/S3/journal/cleanup and live target-configuration/isolation observability, restricted reviewer export, tested CH-12 routes with severity/ack/escalation/runbook links, and immutable-cutoff RTO/RPO calculations that invalidate negative or mismatched watermarks. |
| `#149` | Open, depends on `#130`, `#141`-`#148` | Phase 1 follow-on | Independently review actual environment/tooling/calculation-test readiness, tested CH-12 alert routes, and approvals without recording actual restore or RTO/RPO results; must leave issue `#126`, `DUR-RESTORE-001`, and issue `#39` open for the later exercise. |
| `#138` | Closed | Security follow-up | `PYSEC-2026-2132` Click command-injection remediation completed and closed on 2026-07-14. This did not change production or restore readiness. |
| `#150` | Open | Security follow-up | Remove the Semgrep Click and MCP compatibility overrides by `2026-08-13` or earlier when upstream supports fixed compatible dependencies; any tool version, lock, rule, target, invocation, or advisory change triggers immediate re-review. |
| `#151` | Closed | Security follow-up | CPython `3.13.14` security remediation and scanner-consensus work closed on 2026-07-16. This does not change production, restore, hosted launch, or Product Mode 1 local-demo posture. |

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
| `#155` | Closed | Product Mode 1 checkpoint controller | Controlled local, synthetic, artifact-only Product Mode 1 checkpoint completed through issue `#213` and merged PR `#214` at `cb0d94b5e5963473de41f1a1a3d4aebec714677e`; closure is limited to the local/mock checkpoint and does not authorize Product Mode 2, real media, providers, hosted/public launch, public distribution, or production readiness. |
| `#167` | Open, stopped predecessor evidence | Product Mode 1 governance predecessor | Original PHF-020A attempt superseded by stopped PR `#168`; do not resume, patch, merge, rebase, or delete its evidence. |
| `#169` | Closed, frozen feasibility evidence | GovernancePreflight feasibility predecessor | Closed/stopped feasibility evidence for PR `#170`; do not modify its frozen evidence. |
| `#181` | Closed | Phase 1 process prerequisite | Bounded local Lighthouse browser-selection maintenance completed through PR `#182` at merge commit `3ea049cff0bf2157bea0bb5aedf73eb562753d17`; it unblocked issue `#155` validation and changed no product runtime, launch level, provider posture, or production claim. |
| `#184` | Closed | PHF-020A structured-policy replacement | Replacement for stopped issue `#167` and draft PR `#168` completed through merged PR `#185` at `1179760d342d126c78ff7bd09002d064dc7aaa0e`; created closed Product Mode policy authority in `docs/PHASE_PLAN.md` and `docs/SKILL_EXECUTION_PLAN.md` while keeping PHF-020B, Product Mode 2, runtime, media, providers, hosted/public launch, and production out of scope. |
| `#188` | Closed | PHF-020B StatusStateV1 successor | StatusStateV1 mutable current-state normalization completed through merged PR `#189` at `a5a25bd95787d065c92733f9bcd655820659e5b0`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, Product Mode 2, runtime, media, providers, hosted/public launch, and production remain out of scope. |
| `#190` | Closed | Post-PR-189 status reconciliation | Post-PR-189 repository-ledger reconciliation completed through merged PR `#191` at `5d6704e746fac76d8c6703df81b16f21eb2dba60`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, providers, hosted/public launch, and production remain out of scope. |
| `#192` | Closed | Post-PR-191 status reconciliation | Post-PR-191 repository-ledger reconciliation completed through merged PR `#193` at `7131924937e5433d7de2517e14dd1a328d97a063`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, providers, hosted/public launch, public distribution, and production remain out of scope. |
| `#194` | Closed | Post-PR-193 status reconciliation | Post-PR-193 repository-ledger reconciliation completed through merged PR `#195` at `409376eac66ffb17d80e816ec87b0e54df2ebb22`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, providers, hosted/public launch, public distribution, and production remain out of scope. |
| `#196` | Closed | Post-PR-195 status reconciliation | Post-PR-195 repository-ledger reconciliation completed through merged PR `#197` at `924e378af611930decaba428ffcd1b5b69c00512`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, providers, hosted/public launch, public distribution, and production remain out of scope. |
| `#198` | Closed | Post-PR-197 status reconciliation | Post-PR-197 repository-ledger reconciliation completed through merged PR `#199` at `a295bd18b6491ee794610d366d19c9548e046c56`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, providers, hosted/public launch, public distribution, and production remain out of scope. |
| `#200` | Closed | Post-PR-199 status reconciliation | Post-PR-199 repository-ledger reconciliation completed through merged PR `#201` at `f01236756fa268bd4b90c7f536c57c0f96ba9cdc`; issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, providers, hosted/public launch, public distribution, and production remain out of scope. |
| `#202` | Closed | Post-PR-201 status reconciliation | Post-PR-201 repository-ledger reconciliation completed through merged PR `#203` at `9041718387776f50beb34a2403f69c47232ef26d`; the next-action selection proceeds to issue `#204` rather than another pure status-only reconciliation. |
| `#204` | Closed | Product Mode 1 CH-M1-01 child | Local/mock frontend durable consent-chain repair completed through merged PR `#205` at `bba8cc5baf9bdfc6cbb0cf442ded91e6a01afb63`; post-merge main quality run `29703386168` passed. It calls existing `/avatar-consents` before `/avatar-renders` and passes the returned `consentRecordId`, without changing backend consent semantics, real media, providers, hosted/public launch, Product Mode 2, or production release posture. |
| `#206` | Closed | Post-PR-205 status reconciliation | Repository-ledger reconciliation completed through merged PR `#207` at `066e1c1ed5d1ac8843df3bc6f7362921f5b99eae`; issue `#206` is closed, post-merge main quality run `29704911759` passed, and the next serialized Product Mode 1 child is issue `#208` for CH-M1-02. |
| `#208` | Closed | Product Mode 1 CH-M1-02 child | Controlled local/mock real-stack evidence completed through merged PR `#210` at `6ecb3fcae6f5a581b129aa6967ef8bbcde32076d`; post-merge main quality run `29721085707` passed. The evidence proves browser -> frontend -> backend -> Compose behavior without application API interception and does not authorize Product Mode 2, real audio/video, external providers, hosted/public launch, public distribution, or production release posture changes. |
| `#209` | Closed | Phase 1 Closure local quality follow-up | Directly related governance/local-quality issue completed through merged PR `#210` at `6ecb3fcae6f5a581b129aa6967ef8bbcde32076d`; plain local `make quality` on `main` is unambiguous for Phase 1 Closure mode while Stage 8 and CI policy behavior remain preserved. |
| `#211` | Closed | Post-PR-210 status reconciliation | Repository-ledger reconciliation for PR `#210` and issues `#208`/`#209` completed through merged PR `#212` at `67d2c196752f96a05dc580d00b4b4aa0b4174c0e`; no product/runtime, Product Mode 2, provider, media, hosted/public launch, or production posture change was authorized. |
| `#213` | Closed | Product Mode 1 Checkpoint A through Checkpoint B child | Combined local/mock demo completion issue under controller `#155`, scoped to Checkpoint A, `CH-M1-03`, `CH-M1-04`, `CH-M1-05`, `CH-M1-06`, and Checkpoint B, completed through merged PR `#214` at `cb0d94b5e5963473de41f1a1a3d4aebec714677e`. Evidence includes Stage 6-to-Stage 7 multilingual bundle binding, backend validation tests, frontend voice-manifest/artifact exposure, demo-doc updates, Checkpoint A baseline evidence, Checkpoint B local real-stack no-interception evidence, and latest-head human approval. Product Mode 2, real audio/video, external providers, hosted launch, public distribution, production readiness, and stopped evidence mutation remained out of scope. |
| `#215` | Closed | Post-PR-214 status reconciliation | Repository-ledger reconciliation for PR `#214`, issue `#213`, and issue `#155` closure state completed through merged PR `#216` at `6e42b452d6cfac357a26b5da6c3ab77407d7d975`; post-merge main quality workflow run `29781070328` passed. No runtime, Product Mode 2, real media, providers, hosted/public launch, public distribution, or production-readiness scope was authorized. |
| `#217` | Closed | Post-PR-216 status reconciliation | Narrow repository-ledger follow-up completed through merged PR `#218` at `f396adb9bd9edd98b1e7fa20e27b81d83a6aa81e`; issue `#217` was closed after latest-head approval and post-merge main quality workflow run `29786342169` passed. It records PR `#216`, issue `#215`, PR `#220`, and issue `#219` disposition only; no runtime, Product Mode 2, real media, providers, hosted/public launch, public distribution, or production-readiness scope was authorized. |
| `#219` | Closed | Frontend dependency audit unblocker | Narrow security/dependency remediation completed through merged PR `#220` at `96bde3180f7a15953b4551382ced36fd7e1e3b6e`; issue `#219` was closed after latest-head approval and green checks. Scope was limited to audit-clean frontend dependency metadata and required docs; it did not authorize runtime product code, Product Mode 2, real media, providers, hosted/public launch, public distribution, production readiness, or stopped evidence mutation. |
| `#221` | Closed | Post-PR-218 status reconciliation | Narrow repository-ledger follow-up completed through merged PR `#222` at `f279097357b32c64e29b194618cfb36eee071adb`; issue `#221` was closed after latest-head approval and post-merge main quality workflow run `29808004038` passed. It records PR `#218` and issue `#217` disposition only; no runtime, Product Mode 2, real media, providers, hosted/public launch, public distribution, or production-readiness scope was authorized. |
| `#223` | Closed | Post-PR-222 terminal loop-breaker | Completed through merged PR `#224` at `7cb19e86844e75a5766ec732ca08b18dd931680f`; records PR `#222` merge state, issue `#221` closure, post-merge main quality workflow evidence, and the terminal rule that future issue-completing PRs finalize `docs/STATUS.md` in the same PR while routine post-merge facts are recorded in PR/issue comments instead of successor status-only PRs. No runtime, Product Mode 2, real media, providers, hosted/public launch, public distribution, or production-readiness scope was authorized. |
| `#225` | Closed | Demo Phase 0 planning | Completed through merged PR `#226` at `8d8f1d3dc1a1393356a7e5b95e7404d6b92e40dc`. It documented the controlled reviewer demo contract, source facts, cost/terms research, checkpoint sequencing, failure-matrix categories, and fan-out review expectations only; no runtime, provider SDK, provider key, hosted deployment, real audio/video generation, cloned identity implementation, Product Mode 2, public synthetic-media distribution, or production-readiness scope was authorized. |
| `#231` | Closed | Process governance follow-up | Human verification checklist practice completed through merged PR `#232` at `fde56c0eb438ccc521172f0262c543fe2f81412b`; issue `#231` is closed and the durable practice now requires non-trivial PR bodies to include exact data/source/artifact references, official URLs and verified/accessed dates for changeable facts, pass/fail criteria, residual-risk owners, and high-risk-surface coverage. Scope was docs/process only and did not authorize runtime, provider, media, hosted deployment, Product Mode 2, public distribution, production-readiness, or PR `#230` branch mutation. |
| `#229` | Closed | Demo Checkpoint 1 PR 1 spec/source-facts/governance | Completed through merged PR `#230` at `bcc14834063ef1f8ef1852267d9ddada3db7c3ae`; scope was preflight plus governance/spec docs only. It established Checkpoint 1 PR 1 source facts, sequence, and governance while authorizing no backend, frontend, provider abstraction implementation, provider SDKs, provider keys, hosted deployment, real audio/video generation, avatar/video provider integration, cloned identity, Product Mode 2, public distribution, or production-readiness claims. |
| `#235` | Closed | Demo Checkpoint 1 PR 2 latency/capacity/cost/access/quota contract | Completed through merged PR `#236` at `e62885f04076a31e7d146ddf18fd770f1a8e6762`; scope was contract-only: preflight, demo contract, launch-level alignment, status/stage/third-party governance docs, and narrow branch allowlist checker/test. It authorized no provider SDKs, provider keys, provider account setup, dashboard configuration, paid plan activation, wallet funding, model or voice selection, real provider calls, paid spend, hosted deployment, avatar/video, cloned identity, Product Mode 2, public distribution, or production-readiness claims. |
| `#237` | Closed | Demo Checkpoint 1 PR 3 provider abstraction plus real TTS | Completed through merged PR `#238` at `8a24f3ab3d25e73a47ffc3d6aced30c03748899e`; scope was server-side Stage 6 TTS provider abstraction plus optional real TTS adapter boundary only. Mock/local TTS remains default for local/dev/test/CI. Paid providers remain optional and disabled by default, tests use fake/local transports only, no provider SDKs or keys were added, and PR3 excluded avatar/video provider work, hosted deployment, hosted access/quota/retention/demo polish, public URLs, provider account setup, dashboard configuration, paid plan activation, wallet funding, paid spend, cloned identity, Product Mode 2, public distribution, and production-readiness claims. Post-merge main quality workflow run `29854403531` passed. |
| `#241` | Closed | Demo Checkpoint 1 PR 4 avatar/video provider boundary | Completed through merged PR `#242` as a disabled-default server-side avatar/video provider boundary with mock/local default. It authorized no hosted deployment, public URL, provider account setup, paid spend, real provider calls, cloned voice, cloned face/avatar, digital twin, replica-profile creation, Product Mode 2, public distribution, or production-readiness claim. |
| `#243` | Closed | Demo Checkpoint 1 PR 5 hosted-demo access/quota/retention polish | Completed through merged PR `#244` as local/fake hosted-demo access, quota, retention, disclosure, and redacted-observability evidence. It created no hosted deployment, public URL, provider setup, paid spend, real provider call, cloned identity, Product Mode 2, public distribution, or production-readiness claim. |
| `#245` | Closed | Checkpoint 1 acceptance hardening | Completed through merged PR `#246` for post-PR244 local/fake acceptance hardening, preserving the disabled-default local reviewer boundary and authorizing no provider setup, hosted deployment, public URL, cloned identity, paid spend, real provider calls, or production-readiness claim. |
| `#247` | Closed | Local demo safe refusal UX | Completed through merged PR `#248` at `5456760e4b1f16f708b3c0cff8abe5f31ae29abc`; low-confidence grounded-generation refusals now stop before downstream media calls and show bounded refusal UI instead of a generic `422`. Checkpoint 1 remains local/fake disabled-default reviewer evidence only. |
| `#249` | Open | Checkpoint 3 tracker after C3-PR1 planning/guardrails | C3-PR1 planning and guardrails completed through merged PR `#250` at `41b262fa2431f55cd1c813eab4071968c1c96ba0`. Issue `#249` remains open as the public Checkpoint 3 tracker for future issue-linked Checkpoint 3A child implementation selection. It must not expose private plan details and authorizes no cloned identity, real-person likeness, provider setup, real provider call, paid spend, public URL, product runtime implementation beyond PR `#250`'s failing-by-design acceptance-gate skeleton, public distribution, or production-readiness claim. |
| `#251` | Closed | Post-PR-250 status reconciliation | Completed through PR `#252`, reconciling the repository ledger after PR `#250` merged while leaving issue `#249` open and preserving no-runtime, no-provider, no-paid-spend, no-public-URL, no-cloned-identity, and no-production-readiness boundaries. |
| `#253` | Closed | Checkpoint 3A child CP1 acceptance harness/API E2E foundation | Completed through merged PR `#254` at `28695fbfec2af63de646a21859c80dd9c6e97a14`. The C3A-CP1 branch added an executable `make checkpoint3-acceptance` dispatcher and the first local/mock API E2E acceptance probe for synthetic approved knowledge, ingestion/chunk/store, retrieval, grounded walkthrough generation, unsupported-claim evaluation, stored API replay evidence, bounded ops evidence, and negative coverage for docs/static false-pass, missing approval, cross-project replay, and unsupported-claim acceptance. It keeps issue `#249` open and leaves language quality, media artifacts, access/quota/retention, security/observability, performance, real-browser E2E, and output-correctness probes planned/non-passing. It authorizes no hosted deployment, public URL, provider setup, real provider call, paid spend, cloned identity, public distribution, or production-readiness claim. |

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
| `#108` | Merged | 2026-07-11 | `CH-03` Stage 4 durable graph execution PR for issue `#107` / issue `#39`; merged at `6449786069dd38eeaa5a4a31f5ed73cbfc52d248`, adding project/document/chunk/run/evaluation durable graph metadata, immutable approved-document metadata, replay/conflict behavior, outbox binding, bounded graph payload checks, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#59` | Merged | 2026-07-09 | Phase 1 Closure process follow-up for issue `#58`; merged at `38ec53b`, adding governance-learning allowlist coverage for `docs/PROJECT_GOVERNANCE_LEARNINGS.md` without runtime-scope expansion. |
| `#62` | Merged | 2026-07-09 | Phase 1 Closure process follow-up PR for issue `#60` on branch `phase-1-closure-process-60-phf-002-medium-low-hardening`; merged at `cf07ab8`, hardening Medium/Low PHF process gaps without product/runtime scope. |
| `#63` | Merged | 2026-07-09 | Status ledger reconciliation PR for issue `#60` final disposition and PR/issue mapping consistency in `docs/STATUS.md`. |
| `#64` | Merged | 2026-07-09 | Phase 1 Closure Context 0 contract PR for issue `#39`; docs/guardrails/tests/workflow-only scope, no runtime implementation, reference-only `Refs #39` posture, and always-on Phase 1 quality validation for the required `#39` production-closure matrix shape and ID set. |
| `#73` | Merged | 2026-07-09 | Phase 1 Closure process PR for issue `#71`; repository-guardrail-only updates to `scripts/guardrails_check.py`, tests, and docs to enforce `#39` matrix structural validation on every applicable PR-body validation path while keeping `#39` open. |
| `#74` | Merged | 2026-07-09 | Phase 1 Closure process PR for issue `#72`; repository-guardrail-only updates to harden future `#39` final row-closure proof for durability, operations, media, security, and provider rows while keeping `#39` open and preserving no-runtime scope. |
| `#85` | Merged | 2026-07-11 | Issue `#84` guardrail false-positive fix; allows verified GitHub PR merge pushes to `main` only when the pushed head SHA maps to a PR merged into `main`, rejects missing/malformed metadata and true direct pushes, and preserves issue `#39` reference-only No-Go posture. |
| `#87` | Merged | 2026-07-11 | `CH-01` migration-baseline execution PR for issue `#86` / issue `#39`; added the versioned migration runner, focused tests, branch-scope guardrails, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#94` | Merged | 2026-07-11 | `CH-02` ACID/CAS storage-kernel execution PR for issue `#93` / issue `#39`; added the storage-only CAS kernel, focused replay/conflict/stale-write tests, branch-scope guardrails, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#98` | Merged | 2026-07-11 | Phase 1 Closure CH-04/CH-05/CH-06 execution-strategy base PR; merged at `b5992a599be06ea444ca66d3f088956eee8c70e6`, preserving reference-only `Refs #39` posture and establishing the reviewed dependency base for child implementation PRs after PR `#94`. |
| `#90` | Merged | 2026-07-11 | Process-only PR for issue `#89`; codified approved-PR merge-closeout as agent-owned baseline repository behavior in repo instructions and the reusable new-project engineering playbook without changing runtime/product scope. |
| `#102` | Merged | 2026-07-11 | `CH-04` idempotency semantics execution PR for issue `#97` / issue `#39`; merged at `947a96891fd84085b6fce433e604a8e249b25c23`, adding storage-kernel operation identity, payload-hash conflict guard, terminal replay, transient recovery, stale-owner tests, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#103` | Merged | 2026-07-11 | `CH-05` lease fencing execution PR for issue `#95` / issue `#39`; merged at `3146a91b7fa3cf55d3aab3feae48d196e82b0f36`, adding storage-kernel lease acquire/heartbeat/expiry/reclaim, monotonic fencing epochs, stale-writer rejection, operation-transition lease binding, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#106` | Merged | 2026-07-11 | `CH-06` committed outbox execution PR for issue `#96` / issue `#39`; merged at `d0a2c80f084d8ec9e25b24b841e4f22031953a73`, adding storage-kernel state/event atomicity, outbox replay fingerprinting, at-least-once dispatch retry, stale-dispatch rejection, scoped consumer dedupe, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#112` | Merged | 2026-07-11 | `CH-16` consent capture execution PR for issue `#111` / issue `#39`; merged at `1f3d66d9b1b545e5d5c41e88a83cc731a2a8b31a`, adding durable synthetic-avatar consent capture, replay-safe consent idempotency, restore validation, explicit consent-capture API flow, Stage 7 durable consent gating, and supporting ADR/docs with reference-only `Refs #39` posture. |
| `#124` | Merged | 2026-07-12 | `CH-09` rollback proof-boundary hardening PR for issue `#123` / issue `#39`; merged at `ec2456cba9874d4289c91236de43f73786556503`, proving only the narrow technical rollback compatibility trust-boundary slice while issue `#39` and broader `DUR-ROLLBACK-001` production closure remain open. |
| `#133` | Merged | 2026-07-12 | `CH-10` production metrics contract PR for issue `#128` / issue `#39`; merged at `384c15ac67810d30096794500da1c90ce056dd54`, adding metric names and current emission boundaries while issue `#39` and broader `OPS-METRICS-001` production closure remain open. |
| `#134` | Merged | 2026-07-12 | `CH-11` SLO and error-budget contract PR for issue `#127` / issue `#39`; merged at `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9`, adding repo-checked threshold semantics while issue `#39` and broader `OPS-SLO-001` production closure remain open. |
| `#135` | Merged | 2026-07-13 | Local restore-integrity drill execution PR for issue `#125` / issue `#39`; merged at `f94776f6602d4c6feec2412b4764a7368049a080`, proving only the existing file-backed Stage 4/6/7 restore surface, copied-file checksum parity, restored record-count parity, replay-safe idempotent re-execution, and persisted inspectable evidence paths without claiming production restore closure. |
| `#137` | Merged | 2026-07-13 | Restore-readiness contract PR for issue `#126`; added only repo-checked composition and anti-overclaim evidence. Issue `#126`, `DUR-RESTORE-001`, and issue `#39` remain open. |
| `#75` | Merged | 2026-07-10 | Context 1 planning PR for issue `#65` / issue `#39`; advisory-only PostgreSQL production durability planning, ADR + issue-status updates, and matrix scope allowlist updates only. |
| `#76` | Merged | 2026-07-10 | Context 2 planning PR for issue `#66` / issue `#39`; advisory-only idempotency/lease/outbox production contracts and planning matrix mapping, no runtime implementation. |
| `#77` | Merged | 2026-07-10 | Context 3 migration/rollback compatibility planning PR for issue `#67` / issue `#39`; advisory-only ADR + planned evidence mapping, branch-scope checks update only. |
| `#78` | Merged | 2026-07-10 | Context 4 backup/restore drill planning PR for issue `#68` / issue `#39`; advisory-only ADR + planning matrix updates and branch-scope checks only. |
| `#79` | Merged | 2026-07-10 | Context 5 operations monitoring and first-hour watch planning PR for issue `#69` / issue `#39`; advisory-only ADR + planning matrix updates and branch-scope checks only. |
| `#80` | Merged | 2026-07-10 | Context 6 rollback/media/privacy/provider posture/retention/untrusted-input planning PR for issue `#70` / issue `#39`; advisory-only planning updates and branch-scope checks only. |
| `#166` | Open draft, stopped | Not merged | Stopped predecessor evidence for the superseded PHF-020 attempt under issue `#8`; preserve evidence and do not resume or merge. |
| `#168` | Open draft, stopped | Not merged | Stopped predecessor evidence for issue `#167` / PHF-020A; preserve evidence and do not resume, patch, rebase, or merge. |
| `#170` | Closed, stopped | Not merged | Frozen GovernancePreflight feasibility evidence for issue `#169`; preserve evidence and do not modify. |
| `#173` | Merged | 2026-07-16 | GPF-A offline GovernancePreflightV1 core for issue `#172`; merged at `022d9b61519fa72e094e078ba5ca62802a6f2030`. |
| `#175` | Merged | 2026-07-16 | HPR reviewer-overview hardening for issue `#174`; merged at `93ec63e2574701bf62bd3fa745f18cca560d5f09`. |
| `#177` | Merged | 2026-07-16 | GPF-B prospective repository integration for issue `#176`; merged at `cee9fa099de6c3f01cbd2e5d670fa407ffa54d54`. |
| `#179` | Merged | 2026-07-17 | GPF-C supported pull-request CI evidence for issue `#178`; merged at `22d48b9edc0338d613d4926059fa9ef1ef329d1f` after exact-head approval and closeout. |
| `#185` | Merged | 2026-07-19 | PHF-020A structured-policy replacement for issue `#184`; merged at `1179760d342d126c78ff7bd09002d064dc7aaa0e` after local gates, exact-head CI, latest-head approval, post-merge main workflow verification, and branch cleanup. |
| `#189` | Merged | 2026-07-19 | PHF-020B StatusStateV1 current-state normalization for issue `#188`; merged at `a5a25bd95787d065c92733f9bcd655820659e5b0` with issue `#188` closed during post-merge closeout and no Product Mode 2, runtime, media, provider, hosted/public launch, or production authorization. |
| `#191` | Merged | 2026-07-19 | Post-PR-189 status reconciliation for issue `#190`; merged at `5d6704e746fac76d8c6703df81b16f21eb2dba60` with issue `#190` closed during post-merge closeout and no Product Mode 2, runtime, media, provider, hosted/public launch, or production authorization. |
| `#193` | Merged | 2026-07-19 | Post-PR-191 status reconciliation for issue `#192`; merged at `7131924937e5433d7de2517e14dd1a328d97a063` with issue `#192` closed during post-merge closeout, post-merge main workflow quality run passing at `https://github.com/imrohitagrawal/narratwin-ai/actions/runs/29683438416`, and no Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, or production authorization. |
| `#195` | Merged | 2026-07-19 | Post-PR-193 status reconciliation for issue `#194`; merged at `409376eac66ffb17d80e816ec87b0e54df2ebb22` with issue `#194` closed during post-merge closeout, post-merge main workflow quality run passing at `https://github.com/imrohitagrawal/narratwin-ai/actions/runs/29684509339`, and no Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, or production authorization. |
| `#197` | Merged | 2026-07-19 | Post-PR-195 status reconciliation for issue `#196`; merged at `924e378af611930decaba428ffcd1b5b69c00512` with issue `#196` closed during post-merge closeout, post-merge main workflow quality run passing at `https://github.com/imrohitagrawal/narratwin-ai/actions/runs/29686868800`, and no Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, or production authorization. |
| `#199` | Merged | 2026-07-19 | Post-PR-197 status reconciliation for issue `#198`; merged at `a295bd18b6491ee794610d366d19c9548e046c56` with issue `#198` closed during post-merge closeout, post-merge main workflow quality run passing at `https://github.com/imrohitagrawal/narratwin-ai/actions/runs/29689512124`, and no Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, or production authorization. |
| `#201` | Merged | 2026-07-19 | Post-PR-199 status reconciliation for issue `#200`; merged at `f01236756fa268bd4b90c7f536c57c0f96ba9cdc` with issue `#200` closed during post-merge closeout, post-merge main workflow quality run passing at `https://github.com/imrohitagrawal/narratwin-ai/actions/runs/29691443045`, and no Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, or production authorization. |
| `#203` | Merged | 2026-07-19 | Post-PR-201 status reconciliation for issue `#202`; merged at `9041718387776f50beb34a2403f69c47232ef26d` with issue `#202` closed during post-merge closeout, post-merge main workflow quality run `29700261138` passing, and next-action selection proceeding to issue `#204`. |
| `#205` | Merged | 2026-07-19 | CH-M1-01 local/mock durable consent-chain repair for issue `#204`; merged at `bba8cc5baf9bdfc6cbb0cf442ded91e6a01afb63` with issue `#204` closed during post-merge closeout, post-merge main workflow quality run `29703386168` passing, and no CH-M1-02 real-stack, Product Mode 2, real media, provider, hosted/public launch, or production authorization. |
| `#207` | Merged | 2026-07-19 | Post-PR-205 status reconciliation for issue `#206`; merged at `066e1c1ed5d1ac8843df3bc6f7362921f5b99eae` with issue `#206` closed during post-merge closeout, post-merge main quality workflow run `29704911759` passing, and issue `#208` selected as the next CH-M1-02 child. |
| `#210` | Merged | 2026-07-20 | CH-M1-02 controlled local/mock real-stack evidence and issue `#209` quality-dispatch clarification; merged at `6ecb3fcae6f5a581b129aa6967ef8bbcde32076d` with issues `#208` and `#209` closed during post-merge closeout, post-merge main quality workflow run `29721085707` passing, and no Product Mode 2, real media, provider, hosted/public launch, public distribution, production readiness, or production/public release authorization. |
| `#212` | Merged | 2026-07-20 | Post-PR-210 status reconciliation for issue `#211`; merged at `67d2c196752f96a05dc580d00b4b4aa0b4174c0e` with issue `#211` closed during post-merge closeout and no Product Mode 2, real media, provider, hosted/public launch, public distribution, production readiness, or production/public release authorization. |
| `#214` | Merged | 2026-07-20 | Issue `#213` Checkpoint A through Checkpoint B local/mock demo completion PR under controller issue `#155`; merged at `cb0d94b5e5963473de41f1a1a3d4aebec714677e` after latest-head human approval on head `efab2c3302d5833a1607918962181ec717476fe5`, with post-merge main quality workflow run `29735533818` passing. It closes `#213` and closes `#155` only for the controlled local/mock checkpoint; Product Mode 2, real audio/video, external providers, hosted/public launch, public distribution, production readiness, and stopped evidence mutation remain out of scope. |
| `#216` | Merged | 2026-07-20 | Post-PR-214 repository-ledger reconciliation for issue `#215`; merged at `6e42b452d6cfac357a26b5da6c3ab77407d7d975` after human approval on head `185ee6996b231c74d3c388ab87723c6d45f978f7`, with issue `#215` closed during post-merge closeout and post-merge main quality workflow run `29781070328` passing. It records PR `#214`, issue `#213`, and issue `#155` disposition only; Product Mode 2, real audio/video, external providers, hosted/public launch, public distribution, production readiness, and stopped evidence mutation remain out of scope. |
| `#218` | Merged | 2026-07-21 | Post-PR-216 repository-ledger reconciliation for issue `#217`; merged at `f396adb9bd9edd98b1e7fa20e27b81d83a6aa81e` after human approval on head `8007ac7c1d52a71aafff61a7065d5b0e2debc1cc`, with issue `#217` closed during post-merge closeout and post-merge main quality workflow run `29786342169` passing. It records PR `#216`, issue `#215`, PR `#220`, and issue `#219` disposition only; Product Mode 2, real audio/video, external providers, hosted/public launch, public distribution, production readiness, and stopped evidence mutation remain out of scope. |
| `#220` | Merged | 2026-07-21 | Frontend dependency-audit unblocker for issue `#219`; merged at `96bde3180f7a15953b4551382ced36fd7e1e3b6e` after human approval on head `32b62c2a27314b8485042029699b6544857be6b9`, with issue `#219` closed during post-merge closeout and post-merge main quality workflow run `29785381427` passing. Scope was limited to audit-clean dependency metadata and required docs without runtime product, Product Mode 2, real media, provider, hosted/public launch, public distribution, production-readiness, or stopped-evidence mutation authorization. |
| `#222` | Merged | 2026-07-21 | Post-PR-218 repository-ledger reconciliation for issue `#221`; merged at `f279097357b32c64e29b194618cfb36eee071adb` after human approval on head `14a299fb00f53c54001d11a782c73cfe225e5972`, with issue `#221` closed during post-merge closeout and post-merge main quality workflow run `29808004038` passing. It records PR `#218` and issue `#217` disposition only; Product Mode 2, real audio/video, external providers, hosted/public launch, public distribution, production readiness, and stopped evidence mutation remain out of scope. |
| `#224` | Merged | 2026-07-21 | Terminal post-PR-222 loop-breaker for issue `#223`; merged at `7cb19e86844e75a5766ec732ca08b18dd931680f`, records PR `#222` and issue `#221` disposition, updates the operating model and repository guardrails so future issue-completing PRs finalize `docs/STATUS.md` in the same PR, records ordinary post-merge facts in PR/issue comments rather than successor status-only PRs, and adds executable guardrails for both rules. |
| `#226` | Merged | 2026-07-21 | Demo Phase 0 real-media hosted plan for issue `#225`; merged at `8d8f1d3dc1a1393356a7e5b95e7404d6b92e40dc` after latest-head human approval on head `dd206399e45ac7d0bcc4059d4a2ff49f943012d1`, with post-merge main quality workflow run `29823341000` passing. It documented the controlled reviewer demo contract, first-month cost-minimized target, view-first pre-generated media path, launch-level boundary, Checkpoint 1 and Checkpoint 2 sequencing, failure matrix, and fan-out review expectations only; provider implementation, hosted deployment, real audio/video generation, cloned identity implementation, Product Mode 2, public distribution, and production-readiness claims remain out of scope. |
| `#232` | Merged | 2026-07-21 | Process-governance PR for issue `#231`; merged at `fde56c0eb438ccc521172f0262c543fe2f81412b` and made the Human verification checklist practice durable for non-trivial PR bodies with exact source/data/artifact references, official URL and verified/accessed date where facts can change, pass/fail criteria, residual-risk owner, and high-risk-surface coverage. Scope was docs/process only; it did not authorize runtime, provider, media, hosted/public launch, Product Mode 2, public distribution, production-readiness, or PR `#230` branch mutation. |
| `#230` | Merged | 2026-07-21 | Demo Checkpoint 1 PR 1 for issue `#229`; merged at `bcc14834063ef1f8ef1852267d9ddada3db7c3ae` after latest-head human approval. Scope was spec/source-facts/governance only: preflight, demo plan, stage issue plan, status ledger, third-party notices, and issue-specific branch allowlist tests. It authorized no runtime, provider abstraction implementation, provider SDK/key, hosted deployment, real media, avatar/video, cloned identity, Product Mode 2, public distribution, or production-readiness scope. |
| `#236` | Merged | 2026-07-21 | Demo Checkpoint 1 PR 2 for issue `#235`; merged at `e62885f04076a31e7d146ddf18fd770f1a8e6762`. Scope was latency/capacity/cost/access/quota/cache/pre-generation/retention/launch-level contract only and did not authorize provider SDKs, provider keys, provider account setup, dashboard configuration, paid plan activation, wallet funding, model or voice selection, real provider calls, paid spend, hosted deployment, avatar/video, cloned identity, Product Mode 2, public distribution, or production-readiness claims. |
| `#238` | Merged | 2026-07-21 | Demo Checkpoint 1 PR 3 for issue `#237`; merged at `8a24f3ab3d25e73a47ffc3d6aced30c03748899e` after latest-head human approval on head `8c704bac1b8944a2f8c70d464ad12ec8c2d92a46`, with post-merge main quality workflow run `29854403531` passing. Scope was server-side Stage 6 TTS provider abstraction plus optional real TTS adapter boundary only. It added no provider SDK, provider key, provider account setup, dashboard configuration, paid plan activation, wallet funding, paid spend, real provider call, avatar/video provider work, hosted deployment, cloned identity, Product Mode 2, public distribution, or production-readiness claim. |
| `#242` | Merged | 2026-07-22 | Demo Checkpoint 1 PR 4 for issue `#241`; scope was disabled-default avatar/video provider boundary only with mock/local default and no hosted deployment, public URL, provider setup, paid spend, real provider call, cloned identity, public distribution, or production-readiness claim. |
| `#244` | Merged | 2026-07-22 | Demo Checkpoint 1 PR 5 for issue `#243`; scope was local/fake hosted-demo access/quota/retention/demo-polish evidence only with no hosted deployment, public URL, paid spend, real provider call, cloned identity, Product Mode 2, public distribution, or production-readiness claim. |
| `#246` | Merged | 2026-07-22 | Checkpoint 1 acceptance hardening for issue `#245`; scope was post-PR244 local/fake evidence hardening only and did not authorize provider setup, public URL, paid spend, real provider call, cloned identity, product runtime expansion, or production-readiness claim. |
| `#248` | Merged | 2026-07-22 | Local demo safe refusal UX for issue `#247`; merged at `5456760e4b1f16f708b3c0cff8abe5f31ae29abc`, replacing generic low-confidence `422` presentation with bounded refusal UI before downstream media calls. Checkpoint 1 remains local/fake disabled-default reviewer evidence only. |
| `#250` | Merged | 2026-07-22 | Public-safe Checkpoint 3A planning/guardrails PR for issue `#249`; merged at `41b262fa2431f55cd1c813eab4071968c1c96ba0` after latest-head human approval on head `4de895e3f3c96197ec05253b6319c50621854a16`, with post-merge main quality workflow run `29913327246` passing. It added the Checkpoint 3A acceptance matrix, failing-by-design `make checkpoint3-acceptance` skeleton, output-correctness execution probe plan, fan-out findings, and branch allowlist tests only; issue `#249` remains open as the public Checkpoint 3 tracker, and no runtime implementation, provider setup, real provider calls, paid spend, public URL, cloned identity, public distribution, or production-readiness claim was authorized. |
| `#252` | Merged | 2026-07-22 | Post-PR-250 repository-ledger reconciliation for issue `#251`; records PR `#250` and issue `#249` disposition while preserving issue `#249` as open public tracker and preserving the no-runtime, no-provider, no-paid-spend, no-public-URL, no-cloned-identity, public-distribution, and production-readiness No-Go boundaries. |
| `#254` | Merged | 2026-07-22 | C3A-CP1 executable Checkpoint 3 acceptance harness plus local/mock API E2E foundation for issue `#253`; merged at `28695fbfec2af63de646a21859c80dd9c6e97a14` after latest-head human approval on head `1e4ede741acc28a9a43bcc003ae094d943267c23`, with post-merge main quality workflow run `29925008358` passing. Later Checkpoint 3A probes remain planned/non-passing, issue `#249` remains open, and no provider setup, real provider calls, paid spend, hosted deployment, public URL, cloned identity, public distribution, or production-readiness claim is made. |

## Completed Work

### Completed Governance Milestones

- Branch/PR-only workflow is documented and enforced through repository checks where possible, with direct-push prevention delegated to repository settings.
- Local `make quality` exists and dispatches by `.stage/current`, with Phase 1
  Closure branch-prefix overrides and Phase 1 Closure `main` dispatch while
  StatusStateV1 records `SSV1-MODE` as `phase1-closure`.
- Plain local `make quality` on `main` dispatches Phase 1 Closure while StatusStateV1 records `SSV1-MODE` as `phase1-closure`.
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
  - [Skill Selection And Evidence](SKILL_SELECTION_AND_EVIDENCE.md)
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
- `.stage/current` remains `8`. Stage 8 branches dispatch to the executable
  `make stage8-quality` gate outside policy-only CI mode. Plain local `make
  quality` on `main` dispatches Phase 1 Closure while StatusStateV1 records
  `SSV1-MODE` as `phase1-closure`.
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
- Issue `#155` is closed for the controlled local/mock Product Mode 1 checkpoint
  after issue `#213` and PR `#214`; this file must stay aligned with its
  serialized ledger after each material decision, PR, blocker decomposition,
  merge, and checkpoint.
- Issue `#181` is closed through merged PR `#182`; the local Lighthouse
  prerequisite is no longer the current action.
- Issue `#192` is closed through merged PR `#193`, issue `#194` is closed
  through merged PR `#195`, and issue `#196` is closed through merged PR
  `#197`; issue `#198` is closed through merged PR `#199`; issue `#200` is
  closed through merged PR `#201`; issue `#202` is closed through merged PR
  `#203`; issue `#204` is closed through merged PR `#205`; those completed
  status and CH-M1-01 items are no longer the current action.
- Issue `#206` is closed through merged PR `#207`.
- Issues `#208` and `#209` are closed through merged PR `#210`; CH-M1-02
  controlled local/mock real-stack evidence and the directly related local
  Phase 1 Closure quality-dispatch clarification are complete.
- Issue `#211` is closed through merged PR `#212`.
- Issue `#213` is closed through merged PR `#214`; it completed CH-M1-03,
  CH-M1-04, CH-M1-05, CH-M1-06, Checkpoint A evidence, and Checkpoint B
  local/mock real-stack evidence.
- Issue `#215` is closed through merged PR `#216`; it completed the
  post-PR-214 repository-ledger reconciliation for issue `#213`, PR `#214`,
  and issue `#155` closure state.
- Issue `#219` is closed through merged PR `#220`; it completed the
  frontend dependency-audit unblocker that prevented PR `#218` from becoming
  merge-eligible.
- Issue `#217` is closed through merged PR `#218`; it completed the
  post-PR-216 repository-ledger reconciliation after PR `#220` removed the
  dependency-audit blocker.
- Issue `#221` is closed through merged PR `#222`; it completed the post-PR-218 repository-ledger reconciliation.
- Issue `#223` is closed through merged PR `#224`; it completed the terminal
  post-PR-222 loop-breaker and requires future issue-completing PRs to finalize
  `docs/STATUS.md` in the same PR with the intended post-merge target state and
  next-work pointer.
- Issue `#225` is closed through merged PR `#226`; it completed Demo Phase 0
  planning for the hosted controlled real-media demo path by recording the demo
  contract, source-fact strategy, provider/local-model analysis, checkpoint
  sequencing, failure matrix, and fan-out review requirements before
  implementation.
- Issue `#231` is closed through merged PR `#232`; it completed the
  self-serve Human verification checklist practice for non-trivial PR bodies and
  new-project playbooks without changing product/runtime, provider, media,
  hosted/public launch, Product Mode 2, public distribution,
  production-readiness, or the demo checkpoint implementation sequence.
- Issue `#229` is closed through merged PR `#230`; it completed Demo Checkpoint
  1 PR 1 as spec/source-facts/governance only.
- Issue `#235` is closed through merged PR `#236`; it completed Demo Checkpoint
  1 PR 2 as latency/capacity/cost/access/quota/cache/pre-generation/retention/
  launch-level contract only.
- Issue `#237` is closed through merged PR `#238`; it completed Demo Checkpoint
  1 PR 3 as server-side TTS provider abstraction plus optional real TTS adapter
  boundary only. Mock/local TTS remains default for local/dev/test/CI; tests use
  fake/local transports only; no provider SDK, provider key, provider setup,
  paid spend, avatar/video provider work, hosted deployment, cloned identity,
  Product Mode 2, public distribution, or production-readiness scope was
  authorized.

## Next Approved Actions

1. Preserve stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and
   `#168` as evidence only. Do not resume, patch, rebase, merge, close, delete,
   or rewrite that implementation history.
2. Keep issue `#8` open until its actual acceptance contract is satisfied.
3. Complete issue `#247` local demo refused-run UX repair through its dedicated
   branch and pull request. After that merge, the next approved action remains a
   new Checkpoint 2 consent/provenance planning issue only.
4. Keep production,
   multi-worker deployment, hosted launch, Product Mode 2, external provider
   use, real audio/video export, and public synthetic-media distribution No-Go
   until later issue-linked PRs explicitly authorize narrow demo-only changes.

## Maintenance Protocol

Update this file in the same branch or PR whenever any repository-tracked governance change happens, including:

- a stage plan, stage policy, or guardrail contract changes in checked-in files
- a stage marker or stage gate contract changes
- a stage issue or PR mapping in this repository ledger changes
- `.stage/current` changes
- a stage status changes from pending to in progress, blocked, complete, or superseded
- a new governance artifact becomes required or an old one becomes obsolete
- a major blocker or ambiguity is discovered or resolved
- a new reusable workflow default is adopted for merge and post-merge closeout

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
| 2026-07-22 | PR `#250` merged issue `#249` C3-PR1 Checkpoint 3A planning/guardrails at `41b262fa2431f55cd1c813eab4071968c1c96ba0` after latest-head human approval on `4de895e3f3c96197ec05253b6319c50621854a16`; live GitHub shows post-merge main quality workflow run `29913327246` passed. Issue `#249` remains open as the public Checkpoint 3 tracker, and PR `#250` authorized no product runtime implementation beyond a failing-by-design acceptance-gate skeleton, no provider setup, no real provider calls, no paid spend, no public URL, no cloned identity, no public distribution, and no production-readiness claim. |
| 2026-07-22 | Issue `#251` and PR `#252` reconcile the repository ledger after PR `#250` so `docs/STATUS.md` records the merge and next-action posture in public-safe wording while leaving issue `#249` open as the public Checkpoint 3 tracker. |
| 2026-07-21 | Issue `#241` started as Demo Checkpoint 1 PR 4 on branch `phase-1-closure-process-241-demo-checkpoint1-pr4-avatar-video`; the first branch commit contains only `docs/governance/preflights/issue-241.json`. Scope is server-side Stage 7 avatar/video provider boundary plus optional disabled-by-default real provider adapter controls only; mock/local avatar/video remains default for local/dev/test/CI, provider SDKs are not installed, tests use fake/local transports, and hosted access/quota/retention demo polish, provider setup, paid spend, cloned identity, Product Mode 2, public distribution, and production-readiness claims remain forbidden. |
| 2026-07-21 | PR `#238` merged issue `#237` at `8a24f3ab3d25e73a47ffc3d6aced30c03748899e`, completing Demo Checkpoint 1 PR 3 as server-side Stage 6 TTS provider abstraction plus optional real TTS adapter boundary only. Live GitHub shows issue `#237` closed, the PR branch deleted, and post-merge main quality workflow run `29854403531` passed. The next approved action is a future issue-linked avatar/video provider integration PR only after fresh source facts and executable safeguards are recorded; hosted deployment, access-system implementation, provider setup, paid spend, cloned identity, Product Mode 2, public distribution, and production-readiness claims remain forbidden. |
| 2026-07-21 | Issue `#237` started as Demo Checkpoint 1 PR 3 on branch `phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts`; the first branch commit contains only `docs/governance/preflights/issue-237.json`. Scope is server-side Stage 6 TTS provider abstraction plus optional real TTS adapter boundary only; mock/local TTS remains default for local/dev/test/CI, provider SDKs are not installed, tests use fake/local transports, and avatar/video, hosted deployment, access-system implementation, provider setup, paid spend, cloned identity, Product Mode 2, public distribution, and production-readiness claims remain forbidden. |
| 2026-07-21 | PR `#236` merged issue `#235` at `e62885f04076a31e7d146ddf18fd770f1a8e6762`, completing Demo Checkpoint 1 PR 2 as latency/capacity/cost/access/quota/cache/pre-generation/retention/launch-level contract only. Live GitHub shows issue `#235` closed, and the next repository-tracked work is issue `#237` for provider abstraction plus real TTS. |
| 2026-07-21 | Issue `#235` is active as Demo Checkpoint 1 PR 2 on branch `phase-1-closure-process-235-demo-checkpoint1-contract`; the first branch commit contains only `docs/governance/preflights/issue-235.json`. Scope is latency/capacity/cost/access/quota/cache/pre-generation/retention/launch-level contract plus exact branch allowlist checks only; provider abstraction, TTS implementation, avatar/video, hosted deployment, provider SDKs, provider keys, provider account setup, dashboard configuration, paid plan activation, wallet funding, model or voice selection, real provider test calls, paid spend, cloned identity, Product Mode 2, public distribution, and production-readiness claims remain forbidden. |
| 2026-07-21 | PR `#230` merged issue `#229` at `bcc14834063ef1f8ef1852267d9ddada3db7c3ae`, completing Demo Checkpoint 1 PR 1 as spec/source-facts/governance only. Live GitHub shows issue `#229` closed, and the next repository-tracked work is issue `#235` for the latency/capacity/cost/access/quota/cache/pre-generation/retention/launch-level contract before provider abstraction plus real TTS. |
| 2026-07-21 | PR `#232` merged issue `#231` at `fde56c0eb438ccc521172f0262c543fe2f81412b`, making PR-body Human verification checklists durable with residual-risk owners, official URLs and verified/accessed dates for changeable facts, pass/fail criteria, and high-risk-surface coverage. Routine post-merge facts are recorded in PR/issue comments; the attempted status-only follow-up PR `#234` / issue `#233` was closed unmerged under the post-issue-`#223` no-successor rule. |
| 2026-07-21 | PR `#230` opened as Demo Checkpoint 1 PR 1 for issue `#229` on branch `phase-1-closure-process-229-demo-checkpoint1-spec-governance`. The first branch commit contains only `docs/governance/preflights/issue-229.json`; allowed follow-up files are limited to the demo plan, stage issue plan, status ledger, and third-party notices. Provider abstraction implementation, TTS implementation, avatar/video provider integration, hosted-demo access/quota/retention/demo polish, provider SDKs, provider keys, real media, cloned identity, Product Mode 2, public distribution, and production-readiness claims remain forbidden in this PR. |
| 2026-07-21 | PR `#226` merged issue `#225` Demo Phase 0 real-media hosted plan at `8d8f1d3dc1a1393356a7e5b95e7404d6b92e40dc` after latest-head human approval on `dd206399e45ac7d0bcc4059d4a2ff49f943012d1`; live GitHub shows issue `#225` closed and post-merge main quality workflow run `29823341000` passed. The next approved action is a future issue-linked Checkpoint 1 PR 1 for spec/source-facts/governance only; provider SDKs, provider keys, hosted deployment, real audio/video generation, cloned identity implementation, Product Mode 2, public distribution, and production-readiness claims remain forbidden until explicitly approved by later PRs. |
| 2026-07-21 | Issue `#225` opened as the active Demo Phase 0 planning issue for the hosted controlled real-media demo path. The plan target is: user uploads or uses project knowledge, selects language and audience, and NarraTwin generates a grounded walkthrough delivered by an avatar/voice clone with citations and evaluation evidence behind it. Scope is planning/source facts/governance only; implementation, provider SDKs, provider keys, hosted deployment, real audio/video generation, cloned identity implementation, Product Mode 2, public synthetic-media distribution, and production-readiness claims remain forbidden. |
| 2026-07-21 | PR `#224` merged issue `#223` terminal post-PR-222 loop-breaker at `7cb19e86844e75a5766ec732ca08b18dd931680f`; live GitHub shows issue `#223` closed and PR `#224` merged. Future issue-completing PRs must finalize `docs/STATUS.md` in the same PR with post-merge target state and next-work pointer instead of spawning standalone status-only follow-ups. |
| 2026-07-21 | PR `#224` amended from a routine post-PR-222 status reconciliation into the terminal loop-breaker for status-only follow-ups. The operating model and repository guardrails now require future issue-completing PRs to finalize `docs/STATUS.md` in the same PR with the post-merge target state and next-work pointer, require ordinary post-merge facts to be recorded in PR/issue comments rather than successor docs-only PRs, and guardrails reject new `post-pr-*-status-reconciliation` branches after issue `#223`. |
| 2026-07-21 | Issue `#223` opened as the post-PR-222 repository-ledger reconciliation because PR `#222` could not record its own future merge and issue-closure state before merge; scope is docs/status and guardrail-expectation alignment only, with no product/runtime, provider, media, hosted/public launch, public distribution, or production-readiness authorization. |
| 2026-07-21 | PR `#222` merged the issue `#221` post-PR-218 repository-ledger reconciliation at `f279097357b32c64e29b194618cfb36eee071adb` after human approval on `14a299fb00f53c54001d11a782c73cfe225e5972`; live GitHub shows issue `#221` closed and post-merge main quality workflow run `29808004038` passed, while issue `#8`, issue `#39`, issue `#126`, stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-21 | Issue `#221` opened as the post-PR-218 repository-ledger reconciliation because PR `#218` could not record its own future merge and issue-closure state before merge; scope is docs/status and guardrail-expectation alignment only, with no product/runtime, provider, media, hosted/public launch, public distribution, or production-readiness authorization. |
| 2026-07-21 | PR `#218` merged the issue `#217` post-PR-216 repository-ledger reconciliation at `f396adb9bd9edd98b1e7fa20e27b81d83a6aa81e` after human approval on `8007ac7c1d52a71aafff61a7065d5b0e2debc1cc`; live GitHub shows issue `#217` closed and post-merge main quality workflow run `29786342169` passed, while issue `#8`, issue `#39`, issue `#126`, stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-21 | PR `#220` merged the issue `#219` frontend npm audit remediation at `96bde3180f7a15953b4551382ced36fd7e1e3b6e` after latest-head human approval on `32b62c2a27314b8485042029699b6544857be6b9`; live GitHub shows issue `#219` closed and post-merge main quality workflow run `29785381427` passed. The remediation stayed dependency/governance-only and did not authorize product runtime, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, production readiness, or stopped-evidence mutation. |
| 2026-07-20 | PR `#216` merged issue `#215` post-PR-214 repository-ledger reconciliation at `6e42b452d6cfac357a26b5da6c3ab77407d7d975` after human approval on `185ee6996b231c74d3c388ab87723c6d45f978f7`; live GitHub shows issue `#215` closed and post-merge main quality workflow run `29781070328` passed, while issue `#8`, issue `#39`, issue `#126`, stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-20 | Issue `#217` opened as the post-PR-216 repository-ledger reconciliation because PR `#216` could not record its own future merge and issue-closure state before merge; scope is docs/status and guardrail-expectation alignment only, with no product/runtime, provider, media, hosted/public launch, public distribution, or production-readiness authorization. |
| 2026-07-20 | PR `#214` merged issue `#213` Checkpoint A through Checkpoint B local/mock demo completion at `cb0d94b5e5963473de41f1a1a3d4aebec714677e` after latest-head human approval on `efab2c3302d5833a1607918962181ec717476fe5`; live GitHub shows issue `#213` closed, issue `#155` closed for the controlled local/mock checkpoint only, and post-merge main quality workflow run `29735533818` passed, while issue `#8`, issue `#39`, issue `#126`, stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`, Product Mode 2, real media, provider enablement, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-20 | Issue `#215` opened as the post-PR-214 repository-ledger reconciliation because PR `#214` could not record its own future merge and issue-closure state before merge; scope is docs/status and guardrail-expectation alignment only, with no product/runtime, provider, media, hosted/public launch, public distribution, or production-readiness authorization. |
| 2026-07-19 | PR `#201` merged the issue `#200` post-PR-199 status reconciliation at `f01236756fa268bd4b90c7f536c57c0f96ba9cdc`; live GitHub shows issue `#200` closed and post-merge main workflow run `29691443045` passed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | PR `#199` merged the issue `#198` post-PR-197 status reconciliation at `a295bd18b6491ee794610d366d19c9548e046c56`; live GitHub shows issue `#198` closed and post-merge main workflow run `29689512124` passed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | PR `#197` merged the issue `#196` post-PR-195 status reconciliation at `924e378af611930decaba428ffcd1b5b69c00512`; live GitHub shows issue `#196` closed and post-merge main workflow run `29686868800` passed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, issue `#126`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | PR `#195` merged the issue `#194` post-PR-193 status reconciliation at `409376eac66ffb17d80e816ec87b0e54df2ebb22`; live GitHub shows issue `#194` closed and post-merge main workflow run `29684509339` passed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | PR `#193` merged the issue `#192` post-PR-191 status reconciliation at `7131924937e5433d7de2517e14dd1a328d97a063`; live GitHub shows issue `#192` closed and post-merge main workflow run `29683438416` passed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | PR `#191` merged the issue `#190` post-PR-189 status reconciliation at `5d6704e746fac76d8c6703df81b16f21eb2dba60`; live GitHub shows issue `#190` closed, while issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries remain unchanged. |
| 2026-07-19 | Live GitHub reconciliation records issue `#123` closed through PR `#124` at `ec2456cba9874d4289c91236de43f73786556503`, issue `#128` closed through PR `#133` at `384c15ac67810d30096794500da1c90ce056dd54`, and issue `#127` closed through PR `#134` at `4b7594c8ae14c6a91dff9f0916447b0e6dec39a9`; these were narrow child slices only, and issue `#39`, `DUR-ROLLBACK-001`, `OPS-METRICS-001`, and `OPS-SLO-001` remain open for broader production closure evidence. |
| 2026-07-19 | PR `#203` merged the issue `#202` post-PR-201 status reconciliation at `9041718387776f50beb34a2403f69c47232ef26d`; live GitHub shows issue `#202` closed and post-merge main workflow run `29700261138` passed, and next-action selection proceeded to issue `#204` rather than another pure PR `#203` closeout reconciliation. |
| 2026-07-19 | PR `#205` merged the issue `#204` CH-M1-01 local/mock durable consent-chain repair at `bba8cc5baf9bdfc6cbb0cf442ded91e6a01afb63`; live GitHub shows issue `#204` closed and post-merge main workflow run `29703386168` passed, while issue `#155` remains open, CH-M1-02 real-stack local evidence is next, and production/public release posture remains No-Go. |
| 2026-07-17 | Issue `#181` opened as a prerequisite maintenance item after local `frontend-lighthouse` failed with Lighthouse `NO_FCP` on both the issue `#155` branch and clean `origin/main` at `22d48b9edc0338d613d4926059fa9ef1ef329d1f`; scope is limited to local Lighthouse browser selection and guardrail/status updates, with no product runtime, launch, provider, or production-posture change. |
| 2026-07-17 | PR `#182` merged issue `#181` at `3ea049cff0bf2157bea0bb5aedf73eb562753d17`, closing the bounded local Lighthouse browser-selection prerequisite and unblocking issue `#155` validation without product runtime, launch, provider, or production-posture change. |
| 2026-07-17 | Post-PR-C reconciliation verified GPF-A `#172`/`#173`, HPR `#174`/`#175`, GPF-B `#176`/`#177`, and GPF-C `#178`/`#179` as merged and closed out on `origin/main` at `22d48b9edc0338d613d4926059fa9ef1ef329d1f`; preserved stopped predecessor evidence in `#166`, `#168`, and `#170`; reconciled issue `#155` as the serialized Product Mode 1 checkpoint controller; repaired the Phase 1 process-branch allowlist so a branch may change only its matching GovernancePreflightV1 artifact; and kept issue `#8` open with Product Mode 2, real audio/video, providers, hosted launch, and production out of scope. |
| 2026-07-19 | Issue `#184` and PR `#185` are active as the replacement PHF-020A structured-policy branch. The repository now tracks closed Product Mode authority in `docs/PHASE_PLAN.md` and `docs/SKILL_EXECUTION_PLAN.md`, keeps `docs/STATUS.md` as mutable current-state authority until PHF-020B, and does not claim issue `#8`, issue `#155`, Product Mode 2, runtime, media, provider, hosted/public launch, or production completion. |
| 2026-07-19 | PR `#185` merged PHF-020A structured Product Mode policy authority at `1179760d342d126c78ff7bd09002d064dc7aaa0e`; issue `#184` is complete, issue `#8` and issue `#155` remain open for their separate acceptance contracts, stopped issue `#167` and PR `#168` remain preserved evidence, and the next approved policy action is the smallest PHF-020B/StatusStateV1 successor. |
| 2026-07-19 | Issue `#188` started the PHF-020B/StatusStateV1 successor after PR `#187`; the repository now records a normalized StatusStateV1 current-state table in `docs/STATUS.md`, keeps PHF-020A Product Mode authority in `docs/PHASE_PLAN.md`, preserves stopped issue `#167` and PR `#168`, keeps issue `#8` and issue `#155` open, and does not authorize Product Mode 2, runtime, providers, media, hosted/public launch, or production work. |
| 2026-07-19 | PR `#189` merged PHF-020B StatusStateV1 normalization for issue `#188` at `a5a25bd95787d065c92733f9bcd655820659e5b0`; live GitHub shows issue `#188` closed during post-merge closeout, so the repository ledger now records that disposition while preserving issue `#8`, issue `#155`, stopped issue `#167`, PR `#168`, issue `#39`, Product Mode 2, runtime, media, provider, hosted/public launch, public distribution, and production No-Go boundaries. |
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
| 2026-07-09 | PR `#54` process-hardening follow-up closed the main false-pass loop by requiring full failure-matrix ID coverage, `pass`/`passed` completion statuses, concrete file/URL artifact references, explicit human-only surface rows, pre-implementation matrix/source evidence, and a separate `phase-1-closure-process-*` governance-only branch mode that rejects product runtime files. |
| 2026-07-09 | PR `#54` branch-protection verifier follow-up preserves live required-context drift checks while treating protected-branch detail fields as human-only when GitHub returns `Resource not accessible by integration` to the CI workflow token. |
| 2026-07-09 | PR `#64` process recurrence review added the load-bearing governance rule: governance docs are not considered followed unless the PR adapts them into a source-fact table, invariant/false-pass matrix, evidence mapping, adversarial review prompts, and stop rule before implementation. `docs/PROJECT_GOVERNANCE_LEARNINGS.md` now records the governance-document hierarchy for this project and future applications. |
| 2026-07-09 | PR `#64` blind-review follow-up made the Phase 1 closure quality gate validate the `#39` production-closure matrix on every run, rejecting missing required IDs, malformed rows, duplicate or unexpected IDs, and invalid status values even when the PR body remains reference-only. |
| 2026-07-09 | Issue `#60` process-hardening follow-up started on branch `phase-1-closure-process-60-phf-002-medium-low-hardening` to reduce review/fix loops by making PHF Medium/Low process lessons executable through register parsing, PR-body validation evidence, stricter matrix-template checks, force-mode PR guardrail documentation, and required human-only merge-message surfacing. |
| 2026-07-09 | PR `#54` guardrail follow-up marked the placeholder-host `0.0.0.0` string as a Bandit `B104` false positive because it is rejected input data, not a runtime bind address. |
| 2026-07-09 | Issue `#55` started to triage preserved post-PR `#54` local durability restore-invariant work on a fresh `phase-1-closure-39-*` branch, with a pre-implementation matrix recorded in the issue before applying the runtime stash. |
| 2026-07-09 | PR `#56` blind-review follow-up staged Stage 4 local RAG chunk embeddings before mutating the in-memory store, staged all prepared ingestion chunks before marking documents ingested, pruned failed-ingestion chunks after terminal local snapshot write failures without restoring the whole RAG store, and added public rollback regressions for single-document embedding failure cleanup, multi-document embedding failure cleanup, terminal-persist failed-ingestion chunk cleanup, concurrent ingestion chunk preservation, and concurrent-success preservation; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | PR `#56` governance-learning follow-up added a proactive next-step closeout practice to the new-project engineering playbook so agents state current state, recommended next action, alternatives, agent-owned next work, and human-owned gates before the owner has to ask. |
| 2026-07-09 | PR `#56` final review-note cleanup removed the unused local RAG `prune_to_documents` helper before merge; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | PR `#56` final blind-review cleanup removed unused Stage 4, Stage 6, and Stage 7 full-snapshot restore helpers so operation-scoped rollback remains the only retained local rollback path; issue `#39` remains open and production durability remains No-Go. |
| 2026-07-09 | Issue `#58` process-follow-up added a reusable governance lesson to `docs/PROJECT_GOVERNANCE_LEARNINGS.md` and updated the Phase 1 process-only allowlist in `docs/STAGE_ISSUE_PLAN.md` plus `scripts/quality/check_phase1_closure_docs.py` so governance-learning-only PRs are valid without runtime-scope expansion. |
| 2026-07-09 | PR `#59` merged the issue `#58` governance-learning allowlist follow-up at `38ec53b`; issue `#58` is closed and issue `#39` remains open with production durability still No-Go. |
| 2026-07-09 | PR `#62` narrow review follow-up hardened process evidence parsers against validation command suffix false-passes, malformed forced-PR guardrail command evidence, inline example-only validation text, nested workflow decoys under `on.pull_request`, and non-path pytest targets without product/runtime scope. |
| 2026-07-09 | PR `#62` residual process-trust cleanup rejected zero-count validation evidence and bound pytest node-id evidence to the cited test file, keeping the follow-up process-only and outside product/runtime scope. |
| 2026-07-09 | PR `#62` blind-review follow-up added commit-order preimplementation evidence regression coverage so reversed or unrelated commit ancestry cannot silently satisfy process-sensitive PR evidence. |
| 2026-07-09 | PR `#62` merged at `cf07ab8`; issue `#60` final disposition is complete/closed as a process-only PHF Medium/Low hardening follow-up, with no product/runtime scope and no change to the Phase 1 production No-Go posture. |
| 2026-07-10 | PR `#73` started for issue `#71` process follow-up on branch `phase-1-closure-process-71-issue39-matrix-integrity`; repository-guardrail validation now enforces `#39` matrix row shape, ID set, duplicate/unexpected entry checks, status validity, and placeholder contract detection on every guardrail run while `#39` stays open. |
| 2026-07-11 | PR `#85` merged for issue `#84` at commit `9cc2d767134c49dee234e59159b5010b6894bd2c`; the direct-main-push guardrail now allows legitimate GitHub PR merge pushes to `main` while still rejecting true direct pushes, and issue `#39` Phase 1 No-Go posture remains unchanged. |
| 2026-07-11 | Issue `#89` started on branch `phase-1-closure-process-89-implicit-merge-closeout` to codify approved-PR merge-closeout as repository process and future-project playbook guidance, so merge, post-merge verification, branch cleanup, issue closeout, and status reconciliation are treated as agent-owned baseline work rather than session-specific reminders. |
| 2026-07-11 | PR `#90` merged for issue `#89` at commit `c36a663df0b1a999db0042ca9e9d02fc508a0490`; merge-closeout ownership is now codified as repository baseline process, issue `#89` is closed, and issue `#39` remains open with no change to the Phase 1 No-Go posture. |
| 2026-07-11 | PR `#87` merged for issue `#86` at commit `824a07c2bd546648b96d9ab555b63a8f2415898e`; `CH-01` migration-baseline execution for `DUR-MIG-001` is complete, issue `#86` is closed, and issue `#39` remains open pending later closure chunks and matrix evidence. |
| 2026-07-11 | Issue `#86` started on branch `phase-1-closure-39-ch01-migration-baseline` as the first post-planning implementation chunk for issue `#39`; `CH-01` is limited to the `DUR-MIG-001` migration baseline, a versioned migration runner, focused RED/GREEN test evidence, and branch-scope guardrail updates only. |
| 2026-07-11 | Issue `#93` completed through merged PR `#94` on branch `phase-1-closure-39-ch-02-acid-cas-kernel`; `CH-02` stayed limited to the `DUR-ACID-001` storage kernel, conflict/replay/stale-write RED/GREEN evidence, and branch-scope guardrail updates only. |
| 2026-07-11 | Issue `#97` started on branch `phase-1-closure-39-ch-04-idempotency-semantics` to execute `CH-04` for `DUR-IDEMP-001`; scope is limited to canonical `(operation_id, scope)` identity, payload-hash conflict guarding, terminal success/error replay, transient recovery state, stale-owner rejection hooks, and supporting ADR/traceability updates while issue `#39` remains open. |
| 2026-07-11 | PR `#98` merged the reviewed CH-04/CH-05/CH-06 execution-strategy base at `b5992a599be06ea444ca66d3f088956eee8c70e6`; replacement child PRs after the squash merge use that commit as the exact dependency base and keep issue `#39` reference-only/open. |
| 2026-07-11 | Issues `#97`, `#95`, and `#96` were opened as the next parallel post-`CH-02` implementation chunks for issue `#39`, carrying `CH-04` idempotency semantics, `CH-05` lease fencing, and `CH-06` committed outbox scope respectively while Phase 1 No-Go posture remains unchanged. |
| 2026-07-11 | Issue `#95` started on branch `phase-1-closure-39-ch-05-lease-fencing` to execute `CH-05` for `DUR-LEASE-001`; scope is limited to storage-kernel lease acquire/heartbeat/expiry/reclaim semantics, monotonic fencing epochs, focused `CTX2-LEASE-EVID-001` RED/GREEN tests, and supporting ADR/status/traceability updates only. |
| 2026-07-11 | Issue `#97` completed through merged PR `#102` at `947a96891fd84085b6fce433e604a8e249b25c23`; `CH-04` stayed limited to `DUR-IDEMP-001` idempotency semantics, issue `#97` is closed, and issue `#39` remains open. |
| 2026-07-11 | Issue `#95` completed through merged PR `#103` at `3146a91b7fa3cf55d3aab3feae48d196e82b0f36`; `CH-05` stayed limited to `DUR-LEASE-001` lease fencing, issue `#95` is closed, and issue `#39` remains open. |
| 2026-07-11 | Issue `#96` started on branch `phase-1-closure-39-ch-06-outbox-96` to execute `CH-06` for `DUR-OUTBOX-001`; scope is limited to storage-kernel committed outbox state/event atomicity, event/resource binding, at-least-once dispatch retry, lock-token stale-dispatch rejection, scoped consumer dedupe, focused `CTX2-OUTBOX-EVID-001` RED/GREEN tests, and supporting ADR/status/traceability updates only. |
| 2026-07-11 | Issue `#96` completed through merged PR `#106` at `d0a2c80f084d8ec9e25b24b841e4f22031953a73`; `CH-06` stayed limited to `DUR-OUTBOX-001` committed outbox semantics, issue `#96` is closed, and issue `#39` remains open. |
| 2026-07-11 | Issue `#107` started on branch `phase-1-closure-39-ch-03-stage4-durable-graph` to execute `CH-03` for `DUR-STAGE4-001`; scope is limited to Stage 4 durable graph metadata, replay/conflict behavior, outbox binding, focused RED/GREEN tests, and supporting ADR/status/traceability updates only. |
| 2026-07-11 | Issue `#107` completed through merged PR `#108` at `6449786069dd38eeaa5a4a31f5ed73cbfc52d248`; `CH-03` stayed limited to the Stage 4 durable graph chunk for `DUR-STAGE4-001`, issue `#107` is closed, and issue `#39` remains open. |
| 2026-07-12 | Issue `#109` started on branch `phase-1-closure-39-ch-07-stage6-durable-replay` to execute `CH-07` for `DUR-STAGE6-001`; scope is limited to Stage 6 durable replay state, source/evaluation provenance binding, metadata/checksum validation, terminal idempotency replay, checksum-based dedupe, focused RED/GREEN tests, and supporting API/status/traceability updates only. |
| 2026-07-12 | CH-07 evidence refresh for issue `#109` recorded tenant/project/actor/source-run binding, source-text checksum binding, trace payload exposure, changed-payload conflict rejection, stale `PENDING`/`RUNNING` replay rejection, and checksum-mismatched restore rejection for Stage 6 durable replay while issue `#39` remains open. |
| 2026-07-12 | Issue `#115` completed through merged PR `#116` at `7a2f2a338de3b5f1bbff82f57dd1d977182d8c50`; `CH-08` stayed limited to Stage 7 render artifact-state preflight, branch-scope guardrails, and invariant/evidence mapping while issue `#39` remains open and production closure rows for provenance/disclosure/provider/retention/untrusted-input remain open. |
| 2026-07-12 | Issue `#119` opened for `CH-08` Stage 7 render artifact-state implementation on branch `phase-1-closure-39-ch-08-stage7-render-artifact-state-implementation`; implementation scope remains limited to `DUR-STAGE7-001` legal render-status history, mandatory request-checksum-bound idempotency restore, render ownership-scope validation, cross-scope idempotency rejection, failed restored idempotency dropping, malformed artifact metadata isolation, artifact metadata consistency, consent checkpoint binding, and terminal persist rollback while issue `#39` remains open. |
| 2026-07-12 | Issue `#119` completed through merged PR `#120` at `af7215a5ceb7cefa81306773c1cfa8260435291e`; `CH-08` Stage 7 render artifact-state implementation is merged, issue `#119` is closed, and issue `#39` remains open with provenance/disclosure/provider/retention/untrusted-input closure rows still open. |
| 2026-07-12 | Issue `#123` opened on branch `phase-1-closure-39-ch-09-technical-rollback-compatibility` as the next unblocked release-safety chunk for issue `#39`; scope is limited to `DUR-ROLLBACK-001` previous-code compatibility proof, unsafe rollback blocking, forward repair, compatibility-window enforcement, no false down-migration support claim, and supporting migration/traceability/status updates only. |
| 2026-07-12 | Issue `#125` opened on branch `phase-1-closure-39-restore-local-drill` to add the narrowest executable `DUR-RESTORE-001` slice the repo can honestly support now: a local file-backed Stage 4/6/7 restore-integrity drill with copied-file checksum parity, restored record-count parity, and replay-safe idempotent re-execution, while production backup/restore, metrics, SLOs, alerts, watch, retention, and untrusted-input closure remain open. |
| 2026-07-12 | Issue `#127` opened on branch `phase-1-closure-39-ch-11-slo-error-budget` as the narrowest executable `OPS-SLO-001` slice the repo can honestly support now: a reviewed SLO/error-budget contract bound to merged `CH-10` metric names, with executable now versus advisory-only threshold semantics and release-breach actions, while `CH-12` through `CH-15` evidence and issue `#39` remain open. |
| 2026-07-12 | Issue `#128` opened on branch `phase-1-closure-39-ch-10-production-metrics-contract` as the narrowest executable `OPS-METRICS-001` slice the repo can honestly support now: shared metric names plus tested emission points for durable backlog, lease, idempotency, outbox, local restore-adjacent, and rollback block boundaries, while `CH-11` through `CH-15` evidence and issue `#39` remain open. |
| 2026-07-13 | Issue `#125` completed through merged PR `#135` at `f94776f6602d4c6feec2412b4764a7368049a080`; the merged slice proves only local file-backed restore integrity, replay safety, and persisted evidence paths, while production restore proof and issue `#39` remain open. |
| 2026-07-13 | Issue `#126` opened on branch `phase-1-closure-39-ch-14-restore-readiness-contract` as the narrowest repo-checked `DUR-RESTORE-001` slice still honestly supportable after merged `#125`: a restore-readiness contract that composes existing local restore evidence with the current repo-baselined restore-adjacent metric and SLO artifacts, records mandatory human-only proof surfaces, and blocks production overclaim while final successful restore-drill evidence remains open. |
| 2026-07-14 | Issue `#141` started on branch `phase-1-closure-141-durability-platform-ownership`: ADR `0027` selects the proposed RDS PostgreSQL 17.10 Multi-AZ plus versioned S3 source/restore/control `ap-south-1` durability boundary, defines the external deletion journal, owners, isolation, access, retention/integrity and invalidating RTO/RPO measurement, and gates issues `#142`-`#149`. It creates no cloud/runtime/backup/version/restore evidence; human account, cost, region, role and Security approvals remain blockers, and issue `#126`, `DUR-RESTORE-001`, and issue `#39` remain open. |
| 2026-07-14 | PR `#153` six-angle independent review register `REV141-JOURNAL-001` through `REV141-LAUNCH-001` was recorded on issue `#141`. Remediation loop 2 corrects PITR-created target lifecycle, journal continuity/integrity, PostgreSQL/S3 publication failures, immutable RPO cutoff, access/evidence boundaries, child dependencies, threat coverage and structural/anti-overclaim false passes while preserving the draft/no-environment/no-drill posture. |
| 2026-07-14 | PR `#153` launch-boundary clarification adds `docs/LAUNCH_LEVELS.md`: AWS remains the selected production-like durability evidence platform but is explicitly not a prerequisite for local development or the controlled local mock demo. Hosted internal synthetic demo, external/invite-only soft launch, production-like validation, and production each require distinct decisions and cannot inherit local-demo approval. |
| 2026-07-14 | PR `#153` re-review wave 1 at `3b0a3e0` recorded `REV141-OIDC-002` through `REV141-SIGN-002`. Remediation loop 3 adds exact workflow/environment OIDC limits, supported PITR IAM-auth/post-create engine checks, exact-byte bounded S3 copy, crash-window publication reconciliation, separately signed journal manifests, pre-create cleanup and no-snapshot/no-backup inventory proof, separately scoped RDS/S3 cleanup authority, complete RTO readiness, and executable security/operations mutations; human blockers and the no-drill posture remain unchanged. |
| 2026-07-14 | PR `#153` final guardrail/operations review added affirmative dependency grammar, proposition-bound negation handling, and explicit tested `#130`/CH-12 severity/ack/escalation/runbook routes as `#148` acceptance and a `#149` Go prerequisite. No environment or drill evidence was created. |
| 2026-07-14 | PR `#153` merged the issue `#141` documentation baseline at `2fb5569`; issue `#141` stays open for the recorded cost/account/region, ownership, Security exception and live-environment approvals, while issue `#139`, issue `#126`, `DUR-RESTORE-001`, and issue `#39` remain open. The merge created no infrastructure, backup, restore, RTO/RPO or launch evidence. |
| 2026-07-15 | Issue `#164`, under Mode 1 tracker `#155`, established the skill-selection and evidence-governance contract: claim/boundary-based routing, positive and negative usage outcomes, raw evidence measures, and an initial `ARMED` verification-skill evaluation trigger at 0 eligible PRs and 0 qualifying escapes. This records no Superpowers installation or activation and changes no Mode 1 runtime, launch, or production posture. |
| 2026-07-10 | PR `#76` opened for issue `#66` Context 2 planning for issue `#39` on branch `phase-1-closure-39-context2-idempotency-lease-outbox`; ADR `0009` defines advisory-only idempotency, lease, and outbox contracts while `#39` remains open and all runtime implementation remains deferred. |
| 2026-07-10 | PR `#77` merged migration/rollback context planning for issue `#67`; issue `#67` is closed and runtime migration tooling remains deferred pending later implementation contexts. |
| 2026-07-10 | PR `#78` opened for issue `#68` on branch `phase-1-closure-39-context4-backup-restore-drill`; advisory-only ADR and evidence-planning updates for `DUR-RESTORE-001`, `OPS-METRICS-001`, and `OPS-SLO-001` added no runtime implementation. |
