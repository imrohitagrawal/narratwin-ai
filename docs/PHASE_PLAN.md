# Phase Plan

## Version

- Version: 1.1
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-07-15

## Purpose

This phase plan converts PRD v1.0 into gated, reviewable work. It uses
spec-driven development and vertical slicing. It is a plan only; it does not
authorize product implementation in Stage 1.

## Assumptions

1. NarraTwin AI remains a web application with backend, frontend, RAG, provider,
   storage, avatar, and media implementation blocked until later approved stages.
2. Stage 1 closes product/PRD hardening under issue `#1`.
3. Issue `#16` remains the follow-on Spec Kit constitution/spec/plan/tasks gate.
4. `.stage/current` is advanced to `1` in the Stage 1 PR because this PR implements
   the executable Stage 1 documentation quality gate.
5. Slice 1 implementation starts only after Stage 2 architecture/security/AI-safety
   and Stage 3 repo foundation gates are approved.

## Phase-to-stage mapping

The canonical delivery unit is the approved stage. This document uses numbered
phases only to order planning work within or across stages.

| Phase | Stage | Issue | Implementation permission |
|---|---|---|---|
| Phase 1 | Stage 1 | `#1` | No product implementation |
| Phase 2 | Stage 1 follow-on | `#16` | No product implementation |
| Phase 3 | Stage 2 | `#2` | No product implementation |
| Phase 4 | Stage 3 | `#5` | No product feature code |
| Phase 5 | Stage 4 | `#4` | First vertical slice only |
| Phase 6 | Stage 5 | `#10` | Slice-scoped evaluation, guardrails, observability |
| Phase 7 | Stage 6 | `#11`, `#17`, `#18` | Slice-scoped multilingual, subtitle, voice adapter |
| Phase 8 | Stage 7 | `#12`, `#19`, `#21` | Slice-scoped avatar/video and optional provider adapters |
| Phase 9 | Future approved stage | `#20` | Interactive Q&A only after stage-plan update |
| Phase 10 | Stage 8 and Final Review | `#13`, `#6` | Hardening and review only |

## Product Modes, Delivery Phases, And Closure Programs

These are separate taxonomies. Number similarity does not create scope or
dependency. The approved stage remains the delivery authority; numbered phases
order the historical plan; product modes describe user experiences; closure
programs reconcile evidence and risk.

| Term | Meaning | Canonical tracker or artifact | Must not be interpreted as |
|---|---|---|---|
| Phase 1 | Historical Stage 1 product/PRD hardening | `#1` and this plan | Product Mode 1 or current Phase 1 Closure |
| Phase 2 | Historical Stage 1 Spec Kit follow-on | `#16` | Product Mode 2 |
| Phase 1 Closure | Final Review remediation, evidence, and closeout program | Phase 1 Closure issues and `docs/reviews/PHASE_1_CLOSURE_REPORT.md` | Product Mode 1 or authority for unrelated future features |
| Product Mode 1 | Pre-rendered multilingual demo-video product direction; current checkpoint is artifact-only and local | `#155` | A claim that playable audio or MP4/WebM already exists |
| Product Mode 2 | Interactive grounded AI avatar walkthrough | `#20`, Phase 9 after an approved stage-plan update | Phase 2 or work authorized by the Mode 1 tracker |

Phase 1 Closure is a closure program, not Product Mode 1.
Phase 2 is the Spec Kit gate, not Product Mode 2.
Product Mode 2 remains Phase 9 future work under issue `#20`.

### Canonical tracker and duplicate reconciliation

`docs/PHASE_PLAN.md` is the canonical taxonomy and serial-order source for
cross-chat work. Issue `#155` is the canonical Product Mode 1 local-demo runtime
tracker. Issue `#20` is the existing Product Mode 2 implementation tracker and
must be re-baselined before Mode 2 code starts. Supporting issues such as `#17`,
`#18`, `#19`, and `#43` retain only their explicitly recorded child or later-track
scope; they do not replace either canonical tracker.

Before opening any GitHub, Jira, or other tracker item, search existing trackers
by objective, acceptance criteria, affected boundary, and parent. When a true
duplicate exists, add reciprocal links, identify the canonical owner, and
transfer every unique acceptance criterion to the canonical tracker before closing a true duplicate.
Do not invent an external tracker key or silently close an item whose unique
requirements have not been preserved. If an external tracker exists, record its
key and canonical GitHub link in both systems.

Closed issue `#157` and closed PR `#163` are historical, not active execution
paths. Security/evidence issues `#151`, `#158`, `#159`, and `#161`, plus PR
`#162`, retain their own scopes. They must not be mixed into a product-mode PR;
their verified residual risks may still be required checkpoint inputs.

### Serial execution contract

Only one product-mode implementation module is active in a chat, branch, and PR.
An independent governance or security task may proceed only when explicitly
assigned and must not cause the active product module to switch scope.

Mode 1 Checkpoint B must close before Mode 2 runtime implementation begins.
Mode 1 Checkpoint B is the approved artifact-only local checkpoint; playable
audio or MP4/WebM remains a separate owner decision after that checkpoint.

| Order | Module | Canonical scope | Completion gate before the next row |
|---:|---|---|---|
| 0 | Product-mode demarcation | `#8`; this plan, mandatory agent context, executable governance checks | Reviewed PR merged; duplicate/canonical map reconciled |
| 1 | `CH-M1-01` durable-consent request chain | `#155` child; frontend captures consent and submits `consentRecordId` | RED/GREEN tests, exact-head checks, fresh-context review, merge closeout |
| 2 | `CH-M1-02` real-stack browser path | `#43`; non-intercepted browser → proxy → backend success | Checkpoint A proves the real local request chain |
| 3 | `CH-M1-03` multilingual media-bundle contract | `#155` child; Stage 6→7 provenance, checksum, replay, and ownership contract | Contract PR independently reviewed and merged before consumers change |
| 4 | `CH-M1-04` backend multilingual binding | `#155` child; render only from the validated selected-language bundle | Backend/API/tamper evidence and fresh-context review pass |
| 5 | `CH-M1-05` frontend artifact consistency | `#155` child; expose voice manifest and language-consistent script/SRT/avatar artifacts | Component plus real-stack evidence and fresh-context review pass |
| 6 | Stage 6 controlled fallback | `#17`; honestly labelled translation/subtitle/voice failures | Residual fixed or explicitly accepted by the owner before Checkpoint B |
| 7 | `CH-M1-06` demonstration evidence | `#155` child; checklist, presenter script, synthetic seed, exact-commit Compose/browser evidence | Checkpoint B records conditional artifact-only local-demo Go/No-Go |
| 8 | Optional playable media | `#18` audio, then `#19` video assembly | Starts only after explicit post-Checkpoint-B owner approval; each issue remains separate |
| 9 | Mode 2 contract reset | `#20`; single-turn grounded local interaction before broader conversation scope | Approved stage-plan/contract PR; no runtime change in the contract module |
| 10 | Mode 2 grounded answer backend | `#20` child; retrieval, grounded answer/refusal, citations, evaluation, trace | Backend/API/prompt-injection evidence and fresh-context review pass |
| 11 | Mode 2 local language/presentation binding | `#20` child; mock/local language-consistent answer bundle and synthetic presentation contract | Contract and tamper/fallback evidence pass |
| 12 | Mode 2 question UI | `#20` child; question form, answer/refusal, citations, evaluation, synthetic-avatar panel | Component/accessibility review and real API integration pass |
| 13 | Mode 2 real-stack demonstration | `#20` child; non-intercepted Compose/browser success and refusal paths | Mode 2 local-demo Go/No-Go with honest no-audio/video/public/production limits |

The next row is not authorized merely because code exists. Its predecessor must
have an approved PR, exact-head required checks, post-merge verification, child
issue reconciliation, branch cleanup, and any genuinely required
`docs/STATUS.md` update.

### Fresh-context review boundary

Authoring and independent review are separate sessions for every non-trivial
implementation module. A fresh reviewer receives the approved contract, exact
diff, tests, command evidence, and declared residuals—not the author's reasoning
or conclusions—and attempts to disprove correctness, security, architecture,
scope, and evidence claims. The authoring agent classifies each finding against
the artifact rather than blindly implementing or rejecting it.

A maximum of three substantive review/correction cycles is allowed for one
reviewable artifact. A new defect class updates the contract, failure matrix, and
tests before correction. Substantive findings after the third cycle stop the
module for human decomposition or scope correction; they do not trigger an
open-ended patch loop. Human approval and branch protection remain final merge
conditions even when subagent review is clean.

### Cross-chat handoff contract

Every module closeout records, on its canonical issue or PR:

- exact base and head commits, branch, changed files, and scope exclusions;
- acceptance criteria and invariant-to-test mapping;
- RED/old-behavior proof when behavior changed;
- focused, full, CI, and manual evidence with honest residuals;
- fresh-context findings and their dispositions;
- merge/post-merge/issue/branch/status reconciliation state; and
- exactly one next authorized module, or an explicit stop decision.

A new chat reads `AGENTS.md`, this plan, the canonical tracker, and the last
closeout record. It independently verifies live state but does not restart
completed audits or begin a later row.

## Boundaries

Always:

- keep paid providers optional and disabled for local/dev/test
- treat uploaded docs and provider outputs as untrusted
- keep generated claims grounded in approved project context
- update docs and traceability for PRD-impacting changes
- use issue-linked branches and PRs

Ask first:

- adding dependencies
- adding provider SDKs
- changing stage gates
- changing data storage strategy
- enabling non-mock avatar, voice, or lip-sync tools

Never:

- commit secrets or provider keys
- implement product code in Stage 1
- enable Wav2Lip by default
- add voice or face cloning without consent controls
- merge AI generation features without evaluation evidence once evals exist

## Dependency Graph

```text
Stage 1 product definition
  -> Stage 2 architecture, security, AI safety
    -> Stage 3 repo foundation and executable quality gates
      -> Stage 4 Slice 1 grounded script generation
        -> Stage 5 blocking evals and observability
          -> Stage 6 multilingual script, subtitle, voice adapter
            -> Stage 7 avatar/video adapter and export
              -> Stage 8 performance/security/release hardening
                -> Final Review
```

## Phase 1: Product And PRD Hardening

Stage: Stage 1

Issue: `#1`

Scope:

- product strategy
- PRD v1.0
- PRD red-team review
- North Star metrics
- roadmap
- requirements traceability matrix
- phase plan

Acceptance:

- docs capture the two product modes
- docs capture upload, RAG, grounded generation, multilingual, voice, subtitle,
  avatar/lip-sync adapter, eval, security/privacy, portfolio/recruiter, free-first,
  and premium-provider requirements
- no product code is introduced

Verification:

- review `git diff --name-only` for docs/governance-only scope
- run `python3 -m py_compile scripts/guardrails_check.py scripts/quality/check_quality_stage.py scripts/quality/check_stage1_docs.py`
- run `python3 scripts/guardrails_check.py`
- run `make stage1-quality`
- run `make quality`

## Phase 2: Spec Kit Gate

Stage: Stage 1 follow-on

Issue: `#16`

Scope:

- NarraTwin constitution/spec alignment
- Slice 1 spec
- Slice 1 implementation plan
- Slice 1 task breakdown
- task-to-issue mapping

Acceptance:

- tasks have acceptance criteria
- tasks include verification steps
- tasks are dependency ordered
- spec artifacts identify commands, project structure, testing strategy, stage
  boundaries, success criteria, and implementation approval checkpoints
- implementation remains blocked until approved

## Phase 3: Architecture, Security, And AI Safety

Stage: Stage 2

Issue: `#2`

Scope:

- provider-agnostic interfaces
- data flow and trust boundaries
- upload safety architecture
- prompt-injection defense plan
- unsupported-claim evaluation plan
- observability and cost design
- ADRs

Acceptance:

- architecture supports both product modes without implementing them
- provider adapters remain optional and replaceable
- safety/eval gates are clear enough for TDD in Stage 4 and Stage 5

## Phase 4: Repo Foundation And CI/CD Gates

Stage: Stage 3

Issue: `#5`

Scope:

- local dev commands
- executable quality targets for implementation stages
- CI wrappers
- dependency/security scanning path
- mock/local provider defaults

Acceptance:

- future backend/frontend work has validation commands
- CI can run without real premium provider keys
- no product feature code is introduced

## Phase 5: First Vertical Slice

Stage: Stage 4

Issue: `#4`

Task breakdown:

1. Project creation and local storage contract
   - Acceptance: user can create/select a project
   - Verify: unit tests and UI smoke path
2. Markdown/text upload validation
   - Acceptance: safe files accepted; unsafe files rejected
   - Verify: upload type, size, filename, path tests
3. Prompt-injection handling for uploaded knowledge
   - Acceptance: malicious uploaded instructions are isolated as untrusted content
     and cannot override system/developer rules
   - Verify: malicious markdown fixture that attempts to override
     system/developer instructions
4. Knowledge ingestion and chunk storage
   - Acceptance: deterministic chunks with source metadata
   - Verify: fixture-based chunking tests
5. Project-scoped retrieval
   - Acceptance: request retrieves only selected project context
   - Verify: retrieval isolation tests
6. Grounded script generation with mock/default provider
   - Acceptance: script uses retrieved context and selected audience/depth/style,
     stores requested language in metadata, and keeps Stage 4 generated-script
     acceptance English-only
   - Verify: generation tests with mock provider and metadata assertions
7. Unsupported-claim evaluation and refusal paths
   - Acceptance: unsupported and empty-context outputs are flagged/refused
   - Verify: eval fixtures covering one supported claim, one unsupported claim,
     one mixed-claim response, no-chunk empty context, and retrieval miss
8. Stored output and minimal UI display
   - Acceptance: user sees script, context refs, warnings, and run metadata
   - Verify: UI smoke validation and storage tests

Checkpoint:

- all Stage 4 quality checks pass
- Slice 1 unsupported-claim, empty-context, and prompt-injection fixtures block merge
- docs include security notes, observability metadata, known limitations, and reviewer
  evidence

## Phase 6: Evaluation, Guardrails, And Observability

Stage: Stage 5

Issue: `#10`

Scope:

- stronger unsupported-claim evals
- prompt-injection regression suite
- trace/run metadata completeness
- source citation validation
- cost and latency reporting

Acceptance:

- eval failures block merge
- prompt injection does not override system/developer rules
- every run is traceable to project, context, provider mode, and evaluation result

## Phase 7: Multilingual Scripts, Subtitles, And Voice Adapter

Stage: Stage 6

Issues: `#11`, `#17`, `#18`

Scope:

- translation/localization
- subtitle-ready output
- mock/local TTS adapter
- AI voice disclosure

Acceptance:

- language sanity checks pass
- subtitle export validates
- voice generation is optional
- no real paid provider key is required for tests

## Phase 8: Avatar Rendering Adapter And Export

Stage: Stage 7

Issues: `#12`, `#19`, `#21` for approved adapter contracts only

Scope:

- mock/local avatar renderer
- adapter contract tests
- video export artifact path
- optional premium provider adapter contracts where explicitly approved
- AI media disclosure
- consent controls for any cloned identity feature

Acceptance:

- provider SDKs are isolated behind adapters
- premium providers are optional and disabled for local/dev/test
- Wav2Lip is not enabled by default
- third-party notices and license reviews are updated

## Phase 9: Interactive AI Avatar Walkthrough

Stage: Future approved stage after Stage 4/5 foundation

Issue: `#20`

Scope:

- viewer question input
- approved-context retrieval
- grounded answer generation
- unsupported-claim evaluation
- optional future TTS/avatar presentation

Acceptance:

- stage plan and `docs/STATUS.md` identify the approved implementation stage before
  code starts
- Q&A refuses unsupported answers
- context references are stored and shown
- prompt-injection tests pass

## Phase 10: Premium Providers, Hardening, And Release Readiness

Stage: Stage 8 and Final Review

Issues: `#13`, `#6`; `#21` only for hardening provider adapters already approved
in earlier stages

Scope:

- fallback behavior for existing adapters
- cost and latency review
- performance budgets
- security hardening
- release-readiness evidence
- independent review

Acceptance:

- premium providers remain optional
- release claims match implemented behavior
- unresolved risks have explicit disposition
