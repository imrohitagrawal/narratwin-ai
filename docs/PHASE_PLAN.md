# Phase Plan

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## Purpose

This phase plan converts PRD v1.0 into gated, reviewable work. It uses
spec-driven development and vertical slicing. It is a plan only; it does not
authorize product implementation in Stage 1.

## Assumptions

1. NarraTwin AI remains a web application with backend, frontend, RAG, provider,
   storage, avatar, and media implementation blocked until later approved stages.
2. Stage 1 closes product/PRD hardening under issue `#1`.
3. Issue `#16` remains the follow-on Spec Kit constitution/spec/plan/tasks gate.
4. `.stage/current` remains `0` until the repository intentionally advances stage
   quality gates through a reviewed PR.
5. Slice 1 implementation starts only after Stage 2 architecture/security/AI-safety
   and Stage 3 repo foundation gates are approved.

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

- review `git diff --name-only` for docs-only scope
- run `python -m py_compile scripts/guardrails_check.py`
- run `python scripts/guardrails_check.py`
- run `make quality` and record whether Stage 0 branch-pattern rules block this
  Stage 1 branch

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
3. Knowledge ingestion and chunk storage
   - Acceptance: deterministic chunks with source metadata
   - Verify: fixture-based chunking tests
4. Project-scoped retrieval
   - Acceptance: request retrieves only selected project context
   - Verify: retrieval isolation tests
5. Grounded script generation with mock/default provider
   - Acceptance: script uses retrieved context and selected audience/language/depth/style
   - Verify: generation tests with mock provider
6. Unsupported-claim evaluation and refusal paths
   - Acceptance: unsupported and empty-context outputs are flagged/refused
   - Verify: eval fixtures
7. Stored output and minimal UI display
   - Acceptance: user sees script, context refs, warnings, and run metadata
   - Verify: UI smoke validation and storage tests

Checkpoint:

- all Stage 4 quality checks pass
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

Issues: `#12`, `#19`

Scope:

- mock/local avatar renderer
- adapter contract tests
- video export artifact path
- AI media disclosure
- consent controls for any cloned identity feature

Acceptance:

- provider SDKs are isolated behind adapters
- Wav2Lip is not enabled by default
- third-party notices and license reviews are updated

## Phase 9: Interactive AI Avatar Walkthrough

Stage: Stage 7 or later

Issue: `#20`

Scope:

- viewer question input
- approved-context retrieval
- grounded answer generation
- unsupported-claim evaluation
- optional future TTS/avatar presentation

Acceptance:

- Q&A refuses unsupported answers
- context references are stored and shown
- prompt-injection tests pass

## Phase 10: Premium Providers, Hardening, And Release Readiness

Stage: Stage 8 and Final Review

Issues: `#21`, `#13`, `#6`

Scope:

- optional premium provider adapters
- fallback behavior
- cost and latency review
- performance budgets
- security hardening
- release-readiness evidence
- independent review

Acceptance:

- premium providers remain optional
- release claims match implemented behavior
- unresolved risks have explicit disposition
