# Phase Plan

## Version

- Version: 1.2
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

`docs/PHASE_PLAN.md` is the canonical cross-chat taxonomy and cross-mode boundary
source. Issue `#155` is the canonical Product Mode 1 execution and current-action
tracker. Issue `#20` is the existing Product Mode 2 implementation tracker and
must be re-baselined before Mode 2 code starts. Supporting issues such as `#17`,
`#18`, `#19`, and `#43` retain only their explicitly recorded child or later-track
scope; they do not replace either canonical tracker.

The exact duplicate-reconciliation duties are defined in the next subsection.
Do not silently close an item whose unique requirements have not been preserved.

Closed issue `#157` and closed PR `#163` are historical, not active execution
paths. Security/evidence issues `#151`, `#158`, `#159`, and `#161`, plus PR
`#162`, retain their own scopes. They must not be mixed into a product-mode PR;
their verified residual risks may still be required checkpoint inputs.

Issue `#8` remains open until its original acceptance criteria are reconciled as
follows. After the reviewed demarcation PR merges, the repository owner may close
`#8` manually with reference-only merge wording and a comment linking every row.

| Original `#8` acceptance criterion | Durable evidence | Disposition |
|---|---|---|
| PRD explicitly names both product modes. | `docs/PRD.md` | Existing evidence retained |
| Project-avatar-pack contract is documented. | `docs/PROJECT_AVATAR_PACK.md` | Existing evidence retained |
| Roadmap keeps Slice 1 focused while preserving later video and interactive avatar phases. | `docs/ROADMAP.md` | Existing evidence retained |
| AI build brief instructs Codex to preserve the full product vision. | `docs/AI_BUILD_BRIEF.md` | Existing evidence retained |
| Skill execution plan requires PM/spec validation of product modes and project-avatar-pack before coding. | `docs/SKILL_EXECUTION_PLAN.md` | Reconciled by the issue `#8` demarcation PR |
| No application code is changed. | Exact issue `#8` PR diff and process allowlist | Verify again before merge |

### Duplicate reconciliation contract

These rows are the authoritative minimum. Each obligation applies before a new
tracker is created or a true duplicate is closed.

| Obligation ID | Required action | Completion rule |
|---|---|---|
| `DUP-SEARCH` | Search existing trackers by objective, acceptance criteria, affected boundary, and parent. | Complete before opening a GitHub, Jira, or other tracker item. |
| `DUP-LINK` | Add reciprocal links between the canonical tracker and each true duplicate. | Complete before closing the duplicate. |
| `DUP-CANON` | Identify the canonical owner for the shared objective. | Record the owner in every affected tracker. |
| `DUP-TRANSFER` | Transfer every unique acceptance criterion to the canonical tracker before closing a true duplicate. | Do not close until no unique requirement remains only on the duplicate. |
| `DUP-EXTERNAL` | Do not invent an external tracker key; record a supplied key in both systems. | Leave the external mapping absent when no real key is evidenced. |

### Authority and concurrency contract

Only one product-mode implementation module is active in a chat, branch, and PR.
Issue `#155` owns sequencing inside Product Mode 1, including its current
`CH-M1-00` next action, dependency-safe preparation lanes, contract freezes, and
merge/checkpoint order. Separate implementation or preparation lanes may overlap
only when `#155` explicitly authorizes them, each lane has an isolated issue,
branch, PR, and file/symbol boundary, and dependent work still merges in the
tracker's declared order. This plan does not replace those within-Mode-1 rules.

Issue `#20` owns Product Mode 2 only after its contract-reset gate is authorized.
An independent governance, security, or review task may proceed only when
explicitly assigned and must not silently switch the active product module.

### Cross-mode execution order

Mode 1 Checkpoint B must close before Mode 2 runtime implementation begins.
Mode 1 Checkpoint B is the approved artifact-only local checkpoint; playable
audio or MP4/WebM remains a separate owner decision after that checkpoint.

| Order | Required gate | Canonical owner | Completion effect |
|---:|---|---|---|
| 0 | Product-mode demarcation | `#8` | Reviewed PR merged and original `#8` criteria reconciled |
| 1 | Mode 1 artifact-only Checkpoint B | `#155` | Must close before the Mode 2 contract reset |
| 2 | Mode 2 contract reset | `#20` | Approved stage/contract plan; no runtime change in the reset module |
| 3 | Mode 2 local mock demo | `#20` children | Grounded local Q&A, refusal, citations, evaluation, synthetic presentation, and real-stack evidence |

Each required row needs its approved PR, exact-head checks, post-merge
verification, child-issue reconciliation, branch cleanup, and any genuinely
required `docs/STATUS.md` update. Within row 1, issue `#155` remains authoritative
for preparation concurrency and dependency-ordered merges.

### Optional post-checkpoint media branch

Playable media is a separate owner-approved branch after Checkpoint B:

| Branch order | Optional module | Canonical owner | Start gate |
|---:|---|---|---|
| 1 | Mock/local audio binary | `#18` | Explicit owner approval after Checkpoint B |
| 2 | Mock/local video assembly | `#19` | Audio contract/evidence plus separate owner approval |

This branch is not a predecessor to the Mode 2 contract reset. The owner may
approve, defer, or decline it without changing the Checkpoint-B-to-Mode-2 gate.

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

A new chat reads `AGENTS.md`, this plan, the active canonical tracker, and the
last closeout record. It independently verifies live state but does not restart
completed audits or begin a later cross-mode gate. Within Mode 1 it follows the
current action and dependency-safe wave rules recorded by `#155`.

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
