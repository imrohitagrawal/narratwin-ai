# Traceability Register

This file maps product requirements to implementation slices, tests, evaluation evidence, and documentation updates.

Update this file whenever a change impacts the PRD, product strategy, roadmap, personas, core user journeys, acceptance criteria, or product behavior.

## Traceability rules

- Every PRD-impacting PR must update this file.
- Every implementation slice must map back to at least one PRD requirement.
- Every generated-script feature must show how source chunk citations are validated.
- Every LLM output feature must show how tracing metadata is produced and stored.
- Every provider integration must show the mock/local adapter used in CI.

## Requirement map

| Requirement ID | Source | Requirement | Slice / Issue | Test evidence | Eval evidence | Status |
|---|---|---|---|---|---|---|
| PRD-MVP-001 | `docs/PRD.md` | Create/select project | TBD | TBD | TBD | Planned |
| PRD-MVP-002 | `docs/PRD.md` | Upload markdown/text knowledge safely | TBD | TBD | TBD | Planned |
| PRD-MVP-003 | `docs/PRD.md` | Ingest, chunk, and store approved knowledge | TBD | TBD | TBD | Planned |
| PRD-MVP-004 | `docs/PRD.md` | Retrieve relevant source chunks | TBD | TBD | TBD | Planned |
| PRD-MVP-005 | `docs/PRD.md` | Generate grounded walkthrough script | TBD | TBD | TBD | Planned |
| PRD-MVP-006 | `docs/PRD.md` | Generated scripts cite source chunks/context IDs | TBD | TBD | TBD | Planned |
| PRD-MVP-007 | `docs/PRD.md` | Evaluate unsupported claims | TBD | TBD | TBD | Planned |
| PRD-MVP-008 | `docs/PRD.md` | Store output, citations, and evaluation metadata | TBD | TBD | TBD | Planned |
| PRD-MVP-009 | `docs/PRD.md` | Display output and unsupported-claim warnings in UI | TBD | TBD | TBD | Planned |
| PRD-NFR-001 | `docs/PRD.md` | Tests run without real paid provider keys | #14 | Quality Gates workflow | Guardrail policy | In progress |
| PRD-NFR-002 | `docs/PRD.md` | Quality workflow passes before merge | #14 | `policy-gates` | Guardrail policy | In progress |
| PRD-NFR-003 | `docs/PRD.md` | No secrets committed | #14 | Secret scan | Guardrail policy | In progress |

## Change log

| Date | Issue / PR | Change | Traceability impact |
|---|---|---|---|
| 2026-06-29 | #14 | Add repository guardrails and quality gates | Adds traceability enforcement before implementation starts |
