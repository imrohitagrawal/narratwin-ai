# Traceability Register

This file maps product requirements to implementation slices, tests, evaluation
evidence, and documentation updates.

Update this file whenever a change impacts the PRD, product strategy, roadmap,
personas, core user journeys, acceptance criteria, or product behavior.

## Version

- Last updated: 2026-06-29
- Current PRD source: `docs/PRD.md` v1.0
- Canonical source: `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`

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

## Stage 2 Architecture And Safety Traceability

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `docs/ARCHITECTURE.md` | Provider-agnostic boundaries, first vertical slice flow, observability, CI quality gates, no product implementation, Stage 2 remediation locks | Stage 2 / `#2` | Hardened |
| `docs/ADR/0001-system-architecture.md` | System boundary decision for frontend, backend API, ingestion, RAG, generation, evaluator, adapters, observability | Stage 2 / `#2` | Added |
| `docs/ADR/0002-rag-storage.md` | RAG storage, chunk metadata, vector-store portability, project isolation | Stage 2 / `#2` | Added |
| `docs/ADR/0003-llm-provider-routing.md` | LLM, embedding, translation, and evaluation provider routing with mock/local defaults | Stage 2 / `#2` | Added |
| `docs/ADR/0004-avatar-provider-adapter.md` | Future avatar adapter boundary, consent, disclosure, premium-provider isolation | Stage 2 / `#2` | Added |
| `docs/ADR/0005-observability-and-evals.md` | Run metadata, structured events, evaluation statuses, merge-blocking eval posture | Stage 2 / `#2` | Added |
| `docs/THREAT_MODEL.md` | STRIDE-style risks for upload, RAG, provider, evaluation, observability, and future avatar flows | Stage 2 / `#2` | Added |
| `docs/SECURITY_AND_PRIVACY.md` | Secret scanning, prompt injection controls, upload validation, isolation, key isolation, logging, rate limits, audit logs, dependency and OWASP scan posture | Stage 2 / `#2` | Hardened |
| `docs/AI_SAFETY_AND_EVALUATION.md` | Unsupported-claim evaluation, prompt-injection resistance, claim-level context refs, refusal rules, eval schemas, fixture contract, UI state matrix | Stage 2 / `#2` | Hardened |
| `docs/PORTABILITY_STRATEGY.md` | Provider, data, storage, runtime, AI-output portability, tombstones, synthetic local tenant | Stage 2 / `#2` | Hardened |
| `docs/API_CONTRACT.md` | Contract-first REST resources, versioning, idempotency, typed schemas, generated-run outputs, future media placeholders | Stage 2 / `#2` | Hardened |
| `docs/DATA_MODEL.md` | Logical tenant, user, project, document, chunk, ingestion, run, eval, claim-support, artifact, consent, and audit entities | Stage 2 / `#2` | Hardened |

## Document Ownership

| Document | Owns | Other docs should |
|---|---|---|
| `docs/PRD.md` | Product requirements, user journeys, non-goals, and acceptance criteria | Link or summarize requirements without redefining them |
| `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Requirement IDs, stage mapping, and validation evidence | Treat this as the canonical requirement matrix |
| `docs/ROADMAP.md` | Stage outcome sequence and product-mode alignment | Summarize stage outcomes without duplicating task details |
| `docs/PHASE_PLAN.md` | Stage-to-phase mapping and future task breakdown | Link back to PRD and RTM for requirement definitions |
| `docs/STATUS.md` | Repository-tracked stage, issue, and PR ledger | Record durable state and explicit reconciliation needs |

## Requirement Map

The canonical requirement-level matrix lives in
`docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`. This file records cross-artifact and
change-level traceability only, to avoid duplicate requirement tables drifting.

## Product Mode Traceability

| Product mode | Requirements | Stages |
|---|---|---|
| Pre-rendered multilingual demo video | FR-006, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, NFR-011, NFR-012 | Stage 4 foundation, Stage 6, Stage 7, future approved STT/video-import stage |
| Interactive AI avatar walkthrough | FR-005, FR-006, FR-007, FR-008, FR-009, FR-016, NFR-005, NFR-011 | Stage 4 foundation, Stage 5, future approved stage / `#20` |

## Change Log

| Date | Issue / PR | Change | Traceability impact |
|---|---|---|---|
| 2026-06-29 | `#14` | Add repository guardrails and quality gates | Adds traceability enforcement before implementation starts |
| 2026-06-29 | `#1` | Harden product strategy and PRD v1.0 | Adds Stage 1 product requirement map and product-mode coverage |
| 2026-06-29 | `#2` | Draft Stage 2 architecture, security, AI safety, portability, API, and data-model artifacts | Maps PRD safety/provider/traceability requirements to pre-implementation architecture docs |
| 2026-06-30 | `#2` | Harden Stage 2 architecture/security/evaluation/performance/API/data-model contracts and add executable quality gate | Converts Stage 2 findings into enforceable acceptance checks before Stage 3/4 |
