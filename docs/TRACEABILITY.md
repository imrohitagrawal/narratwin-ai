# Traceability Register

This file maps product requirements to implementation slices, tests, evaluation
evidence, and documentation updates.

Update this file whenever a change impacts the PRD, product strategy, roadmap,
personas, core user journeys, acceptance criteria, or product behavior.

## Version

- Last updated: 2026-06-29
- Current PRD source: `docs/PRD.md` v1.0
- Detailed product matrix: `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`

## Traceability Rules

- Every PRD-impacting PR must update this file.
- Every implementation slice must map back to at least one PRD requirement.
- Every generated-script feature must show how source chunk citations are validated.
- Every LLM output feature must show how tracing metadata is produced and stored.
- Every provider integration must show the mock/local adapter used in CI.
- Every product-mode change must preserve the distinction between pre-rendered demo
  video and interactive AI avatar walkthrough.

## Stage 1 Product Traceability

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `docs/PRODUCT_STRATEGY.md` | Product modes, segments, value proposition, trade-offs, provider modes | Stage 1 / `#1` | Updated |
| `docs/PRD.md` | PRD v1.0 requirements, journeys, MVP scope, safety rules, metrics | Stage 1 / `#1` | Updated |
| `docs/PRD_RED_TEAM_REVIEW.md` | Load-bearing assumptions and kill criteria | Stage 1 / `#1` | Updated |
| `docs/NORTH_STAR_METRICS.md` | North Star, OMTM, metric tree, release thresholds | Stage 1 / `#1` | Updated |
| `docs/ROADMAP.md` | Outcome roadmap and gated stage sequence | Stage 1 / `#1` | Updated |
| `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Requirement-to-stage matrix | Stage 1 / `#1` | Added |
| `docs/PHASE_PLAN.md` | Spec-driven phase plan and vertical-slice breakdown | Stage 1 / `#1` | Added |

## Requirement Map

| Requirement ID | Source | Requirement | Slice / issue | Test evidence | Eval evidence | Status |
|---|---|---|---|---|---|---|
| FR-001 | `docs/PRD.md` | Create and select a project | Stage 4 / `#4` | TBD | N/A | Planned |
| FR-002 | `docs/PRD.md` | Upload markdown/text project knowledge | Stage 4 / `#4` | TBD | N/A | Planned |
| FR-003 | `docs/PRD.md` | Validate upload type, filename, size, and path safety | Stage 4 / `#4` | TBD | N/A | Planned |
| FR-004 | `docs/PRD.md` | Ingest, chunk, and store approved knowledge with metadata | Stage 4 / `#4` | TBD | N/A | Planned |
| FR-005 | `docs/PRD.md` | Retrieve project-scoped context for a walkthrough request | Stage 4 / `#4` | TBD | TBD | Planned |
| FR-006 | `docs/PRD.md` | Generate grounded walkthrough script by audience/language/depth/style | Stage 4 / `#4` | TBD | TBD | Planned |
| FR-007 | `docs/PRD.md` | Include context references for project-specific claims | Stage 4 / `#4` | TBD | TBD | Planned |
| FR-008 | `docs/PRD.md` | Evaluate unsupported claims and empty-context output | Stage 4 / `#4`, Stage 5 / `#10` | TBD | TBD | Planned |
| FR-009 | `docs/PRD.md` | Detect or neutralize prompt injection inside uploaded documents | Stage 4 / `#4`, Stage 5 / `#10` | TBD | TBD | Planned |
| FR-010 | `docs/PRD.md` | Store output, request parameters, context refs, and evaluation metadata | Stage 4 / `#4` | TBD | TBD | Planned |
| FR-011 | `docs/PRD.md` | Display generated output and evaluation warnings in UI | Stage 4 / `#4` | TBD | TBD | Planned |
| FR-012 | `docs/PRD.md` | Produce multilingual scripts from grounded source content | Stage 6 / `#11` | TBD | TBD | Planned |
| FR-013 | `docs/PRD.md` | Export subtitle-ready output | Stage 6 / `#17` | TBD | TBD | Planned |
| FR-014 | `docs/PRD.md` | Generate optional voice through mock/local-first TTS adapter | Stage 6 / `#18` | TBD | TBD | Planned |
| FR-015 | `docs/PRD.md` | Render optional avatar/video output through adapter boundary | Stage 7 / `#12`, `#19` | TBD | TBD | Planned |
| FR-016 | `docs/PRD.md` | Support interactive Q&A over approved project knowledge | Stage 7+ / `#20` | TBD | TBD | Planned |
| FR-017 | `docs/PRD.md` | Support optional premium providers without requiring them locally | Stage 8+ / `#21` | TBD | TBD | Planned |
| NFR-001 | `docs/PRD.md` | No mandatory paid provider APIs for local/dev/test/CI | All stages | Quality gates and no-key tests | Guardrail policy | Active |
| NFR-002 | `docs/PRD.md` | No committed secrets or credentials | All stages | Secret scan | Guardrail policy | Active |
| NFR-003 | `docs/PRD.md` | Provider keys read only from environment variables | Stage 3+ | TBD | Guardrail policy | Planned |
| NFR-004 | `docs/PRD.md` | Uploaded docs, prompts, transcripts, filenames, and provider outputs are untrusted | Stage 2+ | TBD | Security/eval tests | Planned |
| NFR-005 | `docs/PRD.md` | Generated outputs include run metadata and source context references | Stage 4+ | TBD | TBD | Planned |
| NFR-006 | `docs/PRD.md` | Evaluation failures block merge once evaluation exists | Stage 5+ | Eval report gate | Eval report gate | Planned |
| NFR-007 | `docs/PRD.md` | Critical/high security findings block merge once reports exist | Stage 8+ | Security report gate | N/A | Planned |
| NFR-008 | `docs/PRD.md` | Architecture-impacting changes require ADR updates | Stage 2+ | ADR review | N/A | Active |
| NFR-009 | `docs/PRD.md` | PRD-impacting changes require traceability updates | All stages | This file | N/A | Active |
| NFR-010 | `docs/PRD.md` | Third-party packages, tools, models, providers, APIs, datasets, media assets, and generated samples are recorded | All stages | Third-party notice review | N/A | Active |
| NFR-011 | `docs/PRD.md` | Public avatar or voice output includes AI-generated media disclosure | Stage 6+ | TBD | TBD | Planned |
| NFR-012 | `docs/PRD.md` | Costs and provider mode are traceable per run | Stage 4+ | TBD | TBD | Planned |

## Product Mode Traceability

| Product mode | Requirements | Stages |
|---|---|---|
| Pre-rendered multilingual demo video | FR-006, FR-012, FR-013, FR-014, FR-015, NFR-011, NFR-012 | Stage 4 foundation, Stage 6, Stage 7 |
| Interactive AI avatar walkthrough | FR-005, FR-006, FR-007, FR-008, FR-009, FR-016, NFR-005, NFR-011 | Stage 4 foundation, Stage 5, Stage 7+ |

## Change Log

| Date | Issue / PR | Change | Traceability impact |
|---|---|---|---|
| 2026-06-29 | `#14` | Add repository guardrails and quality gates | Adds traceability enforcement before implementation starts |
| 2026-06-29 | `#1` | Harden product strategy and PRD v1.0 | Adds Stage 1 product requirement map and product-mode coverage |
