# Requirements Traceability Matrix

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## Purpose

This matrix maps PRD v1.0 requirements to stages, validation evidence, and related
documentation. It is the product-facing companion to `docs/TRACEABILITY.md`.

## Requirement Matrix

| ID | PRD source | Requirement | Stage / issue | Verification evidence | Status |
|---|---|---|---|---|---|
| FR-001 | `docs/PRD.md` | Create and select a project | Stage 4 / `#4` | Backend/UI tests and manual slice validation | Planned |
| FR-002 | `docs/PRD.md` | Upload markdown/text project knowledge | Stage 4 / `#4` | Upload tests and UI smoke validation | Planned |
| FR-003 | `docs/PRD.md` | Validate upload type, filename, size, and path safety | Stage 4 / `#4` | Security tests for type, size, filename, path | Planned |
| FR-004 | `docs/PRD.md` | Ingest, chunk, and store approved knowledge with metadata | Stage 4 / `#4` | Ingestion unit tests and fixture checks | Planned |
| FR-005 | `docs/PRD.md` | Retrieve project-scoped context for a walkthrough request | Stage 4 / `#4` | Retrieval tests with project isolation | Planned |
| FR-006 | `docs/PRD.md` | Generate grounded walkthrough script by audience/language/depth/style | Stage 4 / `#4` | Generation tests with mock provider | Planned |
| FR-007 | `docs/PRD.md` | Include context references for project-specific claims | Stage 4 / `#4` | Citation/context-reference assertions | Planned |
| FR-008 | `docs/PRD.md` | Evaluate unsupported claims and empty-context output | Stage 4 / `#4`; Stage 5 / `#10` | Eval fixtures and refusal tests | Planned |
| FR-009 | `docs/PRD.md` | Detect or neutralize prompt injection inside uploaded documents | Stage 4 / `#4`; Stage 5 / `#10` | Prompt-injection regression tests | Planned |
| FR-010 | `docs/PRD.md` | Store output, request parameters, context refs, and evaluation metadata | Stage 4 / `#4` | Storage tests and run metadata inspection | Planned |
| FR-011 | `docs/PRD.md` | Display generated output and evaluation warnings in UI | Stage 4 / `#4` | UI smoke test/manual screenshot evidence | Planned |
| FR-012 | `docs/PRD.md` | Produce multilingual scripts from grounded source content | Stage 6 / `#11` | Translation/localization tests | Planned |
| FR-013 | `docs/PRD.md` | Export subtitle-ready output | Stage 6 / `#17` | Subtitle format validation | Planned |
| FR-014 | `docs/PRD.md` | Generate optional voice through mock/local-first TTS adapter | Stage 6 / `#18` | TTS adapter contract tests | Planned |
| FR-015 | `docs/PRD.md` | Render optional avatar/video output through adapter boundary | Stage 7 / `#12`; `#19` | Avatar/video adapter contract tests | Planned |
| FR-016 | `docs/PRD.md` | Support interactive Q&A over approved project knowledge | Stage 7 or later / `#20` | Q&A retrieval/eval tests | Planned |
| FR-017 | `docs/PRD.md` | Support optional premium providers without requiring them locally | Stage 8 or later / `#21` | Provider fallback and no-key CI tests | Planned |
| NFR-001 | `docs/PRD.md` | No mandatory paid provider APIs for local/dev/test/CI | All stages | CI/local quality evidence | Active guardrail |
| NFR-002 | `docs/PRD.md` | No committed secrets or credentials | All stages | Secret scanning and guardrails | Active guardrail |
| NFR-003 | `docs/PRD.md` | Provider keys read only from environment variables | Stage 3 onward | Guardrail and config tests | Planned |
| NFR-004 | `docs/PRD.md` | Uploaded docs, prompts, transcripts, filenames, and provider outputs are untrusted | Stage 2 onward | Security review and tests | Planned |
| NFR-005 | `docs/PRD.md` | Generated outputs include run metadata and source context references | Stage 4 onward | Run metadata and citation assertions | Planned |
| NFR-006 | `docs/PRD.md` | Evaluation failures block merge once evaluation exists | Stage 5 onward | Eval report gate | Planned |
| NFR-007 | `docs/PRD.md` | Critical/high security findings block merge once reports exist | Stage 8 onward | Security scan/report gate | Planned |
| NFR-008 | `docs/PRD.md` | Architecture-impacting changes require ADR updates | Stage 2 onward | ADR review | Active guardrail |
| NFR-009 | `docs/PRD.md` | PRD-impacting changes require traceability updates | All stages | `docs/TRACEABILITY.md` update | Active guardrail |
| NFR-010 | `docs/PRD.md` | Third-party tools, models, providers, APIs, datasets, and media assets are recorded | All stages | `docs/THIRD_PARTY_NOTICES.md` review | Active guardrail |
| NFR-011 | `docs/PRD.md` | Public avatar or voice output includes AI-generated media disclosure | Stage 6 onward | UI/output metadata checks | Planned |
| NFR-012 | `docs/PRD.md` | Costs and provider mode are traceable per run | Stage 4 onward | Observability metadata tests | Planned |

## Product Mode Coverage

| Product mode | Covered by requirements | First meaningful stage |
|---|---|---|
| Pre-rendered multilingual demo video | FR-006, FR-012, FR-013, FR-014, FR-015, NFR-011, NFR-012 | Stage 6, then Stage 7 |
| Interactive AI avatar walkthrough | FR-005, FR-006, FR-007, FR-008, FR-009, FR-016, NFR-005, NFR-011 | Stage 7 or later |

## Use Case Coverage

| Use case | Covered by requirements | Notes |
|---|---|---|
| Portfolio/recruiter walkthrough | FR-001 through FR-011 | First vertical slice proves this path in text form |
| Hiring manager review | FR-006, FR-007, FR-008 | Audience-specific prompt and source references |
| Engineer technical review | FR-005, FR-006, FR-007, FR-010 | Requires architecture/source context |
| Global localized walkthrough | FR-012, FR-013, FR-014 | Stage 6 after grounded script foundation |
| Avatar/video demo export | FR-015, NFR-011, NFR-012 | Stage 7 after license/provider review |
| Interactive Q&A | FR-016 | Future mode reusing retrieval and eval gates |

## Update Rules

- Add a row when the PRD adds a functional or non-functional requirement.
- Update status when a requirement moves from planned to implemented.
- Link validation evidence when tests, evals, or reviewer artifacts exist.
- Keep this file aligned with `docs/TRACEABILITY.md`.
