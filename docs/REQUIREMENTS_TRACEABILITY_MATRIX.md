# Requirements Traceability Matrix

## Version

- Version: 1.1
- Stage: Phase 1 Closure governance reconciliation
- Canonical issue: `#40`
- Last updated: 2026-07-01

## Purpose

This matrix maps PRD v1.0 requirements to stages, validation evidence, and related
documentation. It is the product-facing companion to `docs/TRACEABILITY.md`.

## Canonical Requirement Matrix

| ID | PRD source | Requirement | Stage / issue | Verification evidence | Status |
|---|---|---|---|---|---|
| FR-001 | `docs/PRD.md` | Create and select a project | Stage 4 / `#4` | `tests/api/test_stage4_slice_api.py`, `frontend/tests/smoke.spec.ts`, `docs/TRACEABILITY.md` Stage 4 | Implemented |
| FR-002 | `docs/PRD.md` | Upload markdown/text project knowledge | Stage 4 / `#4` | Upload API tests, frontend smoke workflow, Stage 4 eval fixture | Implemented |
| FR-003 | `docs/PRD.md` | Validate upload type, filename, size, and path safety | Stage 4 and Stage 8 / `#4`, `#13` | Stage 4 upload tests plus Stage 8 MIME/request-size tests | Implemented and hardened |
| FR-004 | `docs/PRD.md` | Ingest, chunk, and store approved knowledge with metadata | Stage 4 / `#4` | `tests/unit/test_chunking.py`, `tests/api/test_stage4_slice_api.py` | Implemented |
| FR-005 | `docs/PRD.md` | Retrieve project-scoped context for a walkthrough request | Stage 4 / `#4` | `tests/unit/test_retrieval_and_grounding.py`, API generation tests | Implemented |
| FR-006 | `docs/PRD.md` | Generate grounded walkthrough script by audience, stored requested language, depth, and style; Stage 4 script acceptance is English-only | Stage 4 / `#4` | Mock provider generation tests, API response metadata, UI display tests | Implemented |
| FR-007 | `docs/PRD.md` | Include context references for project-specific claims | Stage 4 and Stage 5 / `#4`, `#10` | Citation/context-reference assertions, eval smoke report, UI citation display | Implemented and hardened |
| FR-008 | `docs/PRD.md` | Evaluate unsupported claims and empty-context output | Stage 4 and Stage 5 / `#4`, `#10` | Unsupported-claim, no-context, retrieval-miss, and Stage 5 eval fixtures | Implemented and hardened |
| FR-009 | `docs/PRD.md` | Detect or neutralize prompt injection inside uploaded documents | Stage 4 and Stage 5 / `#4`, `#10` | Prompt-injection upload/retrieval fixtures and eval smoke | Implemented and hardened |
| FR-010 | `docs/PRD.md` | Store output, request parameters, context refs, and evaluation metadata | Stage 4 and Stage 5 / `#4`, `#10` | Walkthrough run response tests, trace metadata, eval result storage | Implemented |
| FR-011 | `docs/PRD.md` | Display generated output and evaluation warnings in UI | Stage 4 / `#4` | `frontend/src/app/page.test.tsx`, `frontend/tests/smoke.spec.ts` | Implemented |
| FR-012 | `docs/PRD.md` | Produce multilingual scripts from grounded source content | Stage 6 / `#11` | `tests/unit/test_stage6_multilingual.py`, `tests/api/test_stage6_multilingual_api.py`, frontend tests | Implemented with mock/local providers |
| FR-013 | `docs/PRD.md` | Export subtitle-ready output | Stage 6 / `#11`, future issue `#17` | Subtitle serialization tests and API artifact tests | Implemented for deterministic untimed/draft subtitle artifacts; future expansion remains open |
| FR-014 | `docs/PRD.md` | Generate optional voice through mock/local-first TTS adapter | Stage 6 / `#11`, future issue `#18` | Mock/local voice manifest tests and provider fallback tests | Implemented as JSON manifest only; real audio remains blocked |
| FR-015 | `docs/PRD.md` | Render optional avatar/video output through adapter boundary | Stage 7 / `#12`, future issue `#19` | Stage 7 API/unit tests, local HTML demo export, JSON render manifest, video placeholder artifact | Implemented as mock/local demo export; real video remains blocked |
| FR-016 | `docs/PRD.md` | Support interactive Q&A over approved project knowledge | Future approved stage / `#20` | Q&A retrieval/eval tests after stage plan update | Planned |
| FR-017 | `docs/PRD.md` | Support optional premium providers without requiring them locally | Stage 7 adapter scope / `#21` | Mock/local adapter defaults and disabled external stubs | Partially implemented as disabled/local adapter boundaries; real premium providers remain planned |
| FR-018 | `docs/PRD.md` | Import an existing demo script or transcript and clean it into approved grounded source material | Stage 6 or later | Script/transcript cleanup fixtures and source-reference checks | Planned |
| FR-019 | `docs/PRD.md` | Support optional STT/transcription boundary for demo video or audio input before script cleanup | Future approved stage after provider and license review | STT adapter contract, consent, disclosure, retention, and no-key CI tests | Planned |
| NFR-001 | `docs/PRD.md` | No mandatory paid provider APIs for local/dev/test/CI | All stages | Mock/local provider defaults, `.env.example`, local/CI gates | Active guardrail |
| NFR-002 | `docs/PRD.md` | No committed secrets or credentials | All stages | `scripts/guardrails_check.py`, dependency/security wrapper, Final Review evidence | Active guardrail |
| NFR-003 | `docs/PRD.md` | Provider keys read only from environment variables | All stages | `.env.example`, guardrail checks, provider defaults | Active guardrail |
| NFR-004 | `docs/PRD.md` | Uploaded docs, prompts, transcripts, filenames, and provider outputs are untrusted | Stage 2 onward | Upload validation, prompt-injection tests, provider-output schema validation, artifact validation | Implemented for current local slice; future providers remain blocked |
| NFR-005 | `docs/PRD.md` | Generated outputs include run metadata and source context references | Stage 4 onward | Walkthrough response tests, trace metadata, citation assertions, Stage 7 artifact metadata | Implemented |
| NFR-006 | `docs/PRD.md` | Evaluation failures block merge once evaluation exists | Stage 4 onward | Eval smoke wrapper, stage quality gates, Final Review evidence | Active guardrail |
| NFR-007 | `docs/PRD.md` | Critical/high security findings block merge once reports exist | All stages where reports exist | Dependency/security wrapper and Docker image scan gate | Active guardrail |
| NFR-008 | `docs/PRD.md` | Architecture-impacting changes require ADR updates | Stage 2 onward | Guardrail check and ADR updates through Stage 8 | Active guardrail |
| NFR-009 | `docs/PRD.md` | PRD-impacting changes require traceability updates | All stages | `docs/TRACEABILITY.md` and this RTM | Active guardrail |
| NFR-010 | `docs/PRD.md` | Third-party tools, models, providers, APIs, datasets, and media assets are recorded | All stages | `docs/THIRD_PARTY_NOTICES.md` | Active guardrail |
| NFR-011 | `docs/PRD.md` | Public avatar or voice output includes AI-generated media disclosure | Stage 6 onward | Stage 6 voice manifest and Stage 7 avatar disclosure metadata/tests | Implemented for local/mock artifacts; public distribution remains blocked |
| NFR-012 | `docs/PRD.md` | Costs and provider mode are traceable per run | Stage 4 onward | Observability metadata, provider mode in responses, mock/local cost posture | Implemented for local/mock mode; external provider cost controls remain planned |

## Product Mode Coverage

| Product mode | Covered by requirements | First meaningful stage | Current status |
|---|---|---|---|
| Pre-rendered multilingual demo video | FR-006, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, NFR-011, NFR-012 | Stage 6, then Stage 7; STT/video import requires a future approved stage | Local script/subtitle/voice-manifest/avatar-demo placeholder path exists; real video and STT/video import remain blocked. |
| Interactive AI avatar walkthrough | FR-005, FR-006, FR-007, FR-008, FR-009, FR-016, NFR-005, NFR-011 | Future approved stage after Stage 4/5 foundation | Retrieval/generation/eval foundation exists; interactive Q&A remains planned under `#20`. |

## Use Case Coverage

| Use case | Covered by requirements | Current status |
|---|---|---|
| Portfolio/recruiter walkthrough | FR-001 through FR-011 | Implemented for local mock-provider demo with citations and eval result. |
| Hiring manager review | FR-006, FR-007, FR-008 | Implemented through audience parameter and grounded script generation; usefulness scoring remains future review work. |
| Engineer technical review | FR-005, FR-006, FR-007, FR-010 | Implemented for uploaded technical source context. |
| Global localized walkthrough | FR-012, FR-013, FR-014 | Implemented for mock/local translation, subtitle, and voice-manifest artifacts. |
| Avatar/video demo export | FR-015, FR-018, FR-019, NFR-011, NFR-012 | Mock/local avatar demo export exists; real video, STT/video import, and public synthetic-media distribution remain blocked. |
| Interactive Q&A | FR-016 | Planned future mode; requires stage-plan update before implementation. |

## Phase 1 Closure Notes

Final Review issue `#40` found this RTM stale after Stage 4-8 implementation.
This revision reconciles statuses with the implemented local/mock baseline while
preserving No-Go limits from `docs/reviews/GO_NO_GO.md`.

## Update Rules

- Add a row when the PRD adds a functional or non-functional requirement.
- Update status when a requirement moves from planned to implemented.
- Link validation evidence when tests, evals, or reviewer artifacts exist.
- Keep this file aligned with `docs/TRACEABILITY.md`.
