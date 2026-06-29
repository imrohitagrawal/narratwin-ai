# PRD Red-Team Review: NarraTwin AI

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## Review Target

This review attacks the load-bearing assumptions in `docs/PRD.md` v1.0 and
`docs/PRODUCT_STRATEGY.md` v1.0 before product implementation starts.

## Top Kill-assumptions

### 1. Creators can provide enough approved project knowledge

- Claim: A creator can upload markdown/text project knowledge that is rich enough to
  produce useful recruiter, hiring-manager, engineer, and product walkthroughs.
- Fails if: most projects only provide shallow README content that lacks ownership,
  impact, trade-offs, architecture, metrics, or FAQs.
- Evidence to get this week: collect 3 real project-avatar-pack examples and score
  whether each supports at least recruiter and engineer walkthroughs.
- Kill criterion: fewer than 2 of 3 packs can support a useful grounded recruiter
  walkthrough without inventing facts.
- Cheapest test: manually assemble markdown packs for existing projects and run a
  prompt-only dry run before building product code.

### 2. Grounded scripts are valuable before avatar video exists

- Claim: users will accept text scripts as the first valuable output because trust
  and reviewability matter before media polish.
- Fails if: target users only perceive value when a polished video/avatar is already
  available.
- Evidence to get this week: show 5 target reviewers a grounded script plus source
  references and ask whether it improves project understanding over README-only
  review.
- Kill criterion: fewer than 3 of 5 reviewers say the script is useful enough without
  video to justify the next slice.
- Cheapest test: compare README-only, script-only, and script-with-citations review
  flows.

### 3. Unsupported-claim evaluation can be good enough for a useful MVP

- Claim: the product can reliably flag or refuse unsupported project claims in early
  slices.
- Fails if: evaluation misses obvious invented claims or creates too many false
  positives for normal paraphrases.
- Evidence to get this week: create a small eval set with supported facts, unsupported
  facts, empty context, and malicious uploaded instructions.
- Kill criterion: evaluation misses any high-risk fabricated claim in the controlled
  set or blocks most valid summaries.
- Cheapest test: run deterministic fixtures before adding provider adapters.

### 4. Free-first mode can prove the product without premium providers

- Claim: the core workflow can be developed and tested with mocks/local defaults and
  optional free/low-cost providers.
- Fails if: the first meaningful user experience depends on paid avatar, TTS, or video
  providers.
- Evidence to get this week: define Stage 4 test fixtures and provider interfaces that
  run without real provider keys.
- Kill criterion: any local/CI test requires a premium provider key.
- Cheapest test: use mock generation/evaluation responses for CI and make provider
  mode visible in run metadata.

### 5. The two-mode vision will not over-expand Slice 1

- Claim: preserving pre-rendered video and interactive avatar Q&A in the PRD will not
  cause broad premature implementation.
- Fails if: Stage 4 starts scaffolding avatar, TTS, subtitle, video, and Q&A systems
  before the grounding loop works.
- Evidence to get this week: review Stage 4 task plan against the cut line in
  `docs/PHASE_PLAN.md`.
- Kill criterion: any Stage 4 task touches avatar rendering, TTS, subtitle export,
  premium provider adapters, or interactive Q&A product code.
- Cheapest test: enforce vertical-slice issue scope in PR review.

## What's Well-reasoned

- The PRD separates product vision from MVP scope.
- The first slice is narrow and user-facing: upload knowledge, retrieve context,
  generate grounded script, evaluate, store, and display.
- Security and privacy controls are tied to real risks: unsafe uploads, prompt
  injection, unsupported claims, secrets, provider data handling, and consent.
- Free-first and premium-provider modes are explicit, which protects local testing
  and prevents provider lock-in.
- The project-avatar-pack gives future modes a reusable source-of-truth contract.

## What Could Still Break The Plan

| Risk | Impact | Mitigation |
|---|---|---|
| Docs overpromise before implementation proves quality | High | Keep README/release claims tied to implemented stage evidence |
| RAG chunking loses important context | High | Add deterministic fixtures and source context checks in Stage 4 |
| Evaluation quality is too weak | High | Start with simple high-signal rules and controlled eval fixtures |
| Translation changes technical meaning | Medium | Add language sanity checks and human-reviewed examples in Stage 6 |
| Avatar provider terms are restrictive | Medium | Keep mock default and require license review before activation |
| Costs become unclear | Medium | Store provider mode, token usage when available, latency, cache hit, and estimated cost |
| Interactive Q&A broadens scope | Medium | Keep Q&A after grounded generation and evaluation are stable |

## Stage 1 Go/no-go

Go for Stage 1 PR review if:

- product strategy and PRD v1.0 are merged as docs/governance only
- requirements are traceable to stages and future slices
- `docs/PHASE_PLAN.md` keeps implementation blocked until approved later stages
- `docs/STATUS.md` records that Stage 1 product hardening is distinct from the
  separate Spec Kit gate in issue `#16`

Do not start product implementation if:

- Stage 2 architecture/security/AI-safety review is not complete
- Stage 3 repo foundation and quality gates are not complete
- Stage 4 issue, branch, PR, and vertical-slice task plan are not approved
