# Roadmap

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## Roadmap Principle

Build NarraTwin AI through reviewed vertical slices. Each phase must produce a
working, tested, documented outcome before the next phase starts. The roadmap
preserves two product modes while implementing the grounded script loop first:

- pre-rendered multilingual demo video
- interactive AI avatar walkthrough

## Outcome Roadmap

| Stage | Outcome statement | Primary evidence |
|---|---|---|
| Stage 0 | Enable safe agent work by establishing operating model, skill lock, guardrails, and Stage 0 quality checks | Merged Stage 0 docs and CI |
| Stage 1 | Enable reviewers to approve a focused product definition before implementation | Product strategy, PRD v1.0, red-team, metrics, roadmap, RTM, phase plan |
| Stage 2 | Enable secure architecture decisions before code | Architecture, ADRs, security/privacy, AI safety/evaluation |
| Stage 3 | Enable repeatable local and CI validation before product code | Repo foundation, quality wrappers, dependency/security scan path |
| Stage 4 | Enable a creator to generate a grounded walkthrough from uploaded project knowledge | First vertical slice with tests, docs, UI, evaluation, storage |
| Stage 5 | Enable generated AI outputs to be blocked or warned when unsafe or unsupported | Blocking evals, prompt-injection tests, observability metadata |
| Stage 6 | Enable global viewers to consume localized scripts with subtitle and voice-ready outputs | Translation/localization, subtitle export, mock/local voice adapter |
| Stage 7 | Enable optional avatar/video rendering without provider lock-in | Mock/local avatar renderer, video export path, consent/disclosure controls |
| Stage 8 | Enable a release-ready product with performance, security, cost, and provider hardening | Security/performance evidence, provider fallback, release readiness |
| Final Review | Enable an independent release decision | Independent review report and unresolved risk disposition |

## Stage Details

### Stage 0: Codex Operating Model And Skill Lock

Outcome:

- issue-linked branch and PR workflow
- Stage 0 operating model
- skill governance
- guardrail checks
- no product implementation

Status:

- complete on `main`

### Stage 1: Product Strategy And PRD v1.0

Outcome:

- hardened product strategy
- PRD v1.0
- PRD red-team review
- North Star metrics
- outcome roadmap
- requirements traceability matrix
- phase plan

Exit gate:

- documents are reviewed through issue `#1`
- `make stage1-quality` and `make quality` pass with `.stage/current = 1`
- no product code is introduced
- product implementation remains blocked until later gates pass
- issue `#16` remains the follow-on Spec Kit constitution/spec/plan/tasks gate

### Stage 2: Architecture, Security, And AI Safety

Outcome:

- provider-agnostic architecture
- trust boundaries and data flow
- ADRs for architecture-impacting choices
- upload safety model
- prompt-injection and unsupported-claim evaluation plan
- provider, storage, observability, and cost-control boundaries

Exit gate:

- architecture and safety docs are reviewed
- provider interfaces are defined before implementation
- no product implementation starts

### Stage 3: Repo Foundation And CI/CD Quality Gates

Outcome:

- local development setup
- executable quality targets for implementation stages
- CI wrappers for future backend/frontend checks
- dependency and security scan path
- mock/local provider defaults

Exit gate:

- future product code has a validation path
- no product feature code is introduced

### Stage 4: Slice 1, Project Upload To Grounded Script Generation

Outcome:

```text
project creation
-> markdown/text upload
-> validation
-> ingestion/chunking/storage
-> retrieval
-> grounded walkthrough script generation
-> unsupported-claim evaluation
-> stored output
-> UI display
```

Exit gate:

- user-facing happy path works
- empty-context, unsupported-claim, and prompt-injection refusal paths pass
- generated output has context refs and run metadata
- tests pass without real paid provider keys
- docs include security notes, observability metadata, known limitations, and reviewer
  evidence

### Stage 5: Evaluations, Guardrails, And Observability

Outcome:

- blocking unsupported-claim evaluation
- prompt-injection regression tests
- trace/run metadata
- source chunk/context citation validation
- structured events and cost metadata

Exit gate:

- evaluation failures block merge
- unsafe uploaded instructions cannot override system rules
- runs are debuggable from stored metadata

### Stage 6: Multilingual Scripts, Subtitles, And Voice Adapter

Outcome:

- grounded script translation/localization
- subtitle-ready export
- mock/local TTS adapter boundary
- AI voice disclosure where audio exists
- no voice cloning

Exit gate:

- language consistency checks pass for selected test cases
- subtitle format validates
- audio remains optional
- no real paid provider key is required for tests

### Stage 7: Avatar Rendering Adapter And Export

Outcome:

- mock/local avatar rendering adapter
- video export artifact path
- adapter contract tests
- optional premium provider adapter contracts where explicitly approved
- AI-generated media disclosure
- consent controls for any cloned identity feature

Exit gate:

- avatar/video output remains provider-agnostic
- premium providers remain optional and disabled for local/dev/test
- Wav2Lip is not enabled by default
- third-party notices and license review are complete for any used tool

### Stage 8: Performance, Security Hardening, And Release Readiness

Outcome:

- dependency/security scan evidence
- performance budgets
- provider fallback behavior for existing adapters
- cost and latency review
- release-readiness report
- known limitations and rollback notes

Exit gate:

- critical/high security findings are resolved or block release
- release claims match implemented behavior

### Final Review: Independent Release Review

Outcome:

- independent review of product claims, quality evidence, safety, security, provider
  risks, and release readiness

Exit gate:

- unresolved risks have explicit disposition
- no new feature implementation occurs during final review

## Product Mode Alignment

| Roadmap stage | Pre-rendered multilingual demo video | Interactive AI avatar walkthrough |
|---|---|---|
| Stage 4 | Produces grounded script foundation | Produces reusable retrieval/generation/eval foundation |
| Stage 5 | Hardens evaluation and traceability | Hardens answer safety and refusal behavior |
| Stage 6 | Adds translation, subtitles, voice-ready output | Adds multilingual answer foundations |
| Stage 7 | Adds avatar/video render adapter and export | Adds avatar presentation boundary |
| Future approved stage | N/A | Adds interactive Q&A after stage-plan update |
| Stage 8 | Hardens existing provider/cost/security behavior | Hardens existing provider/cost/security behavior |

## Roadmap Guardrails

- No implementation before approved gates.
- No broad horizontal scaffolding.
- No mandatory paid providers.
- No unreviewed third-party avatar/lip-sync tools.
- No face or voice cloning in MVP.
- No generated claims without approved context support.
- Every implementation slice includes tests, docs, security notes, observability
  metadata, known limitations, and reviewer pass.
