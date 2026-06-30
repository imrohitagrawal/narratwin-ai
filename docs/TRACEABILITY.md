# Traceability Register

This file maps product requirements to implementation slices, tests, evaluation
evidence, and documentation updates.

Update this file whenever a change impacts the PRD, product strategy, roadmap,
personas, core user journeys, acceptance criteria, or product behavior.

## Version

- Last updated: 2026-07-01
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
| `docs/STAGE2_ARCHITECTURE_CONTRACT.json` | Machine-readable Stage 2 semantic contract for states, idempotency, provider defaults, budgets, evidence, cache keys, and review invariants | Stage 2 / `#2` | Added |
| `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md` | Human review checklist for architecture, security, AI safety, API/data, portability, performance, observability, sub-agent, and cross-model signoff | Stage 2 / `#2` | Added |
| `docs/STAGE2_REVIEW_PROMPT_PACK.md` | Reusable prompt pack for parallel sub-agent review and cross-model second opinion | Stage 2 / `#2` | Added |

## Stage 3 Repo Foundation Traceability

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/` | Health checks only for the backend FastAPI skeleton; no product feature workflow | Stage 3 / `#5` | Added |
| `pyproject.toml` and `uv.lock` | Backend foundation dependencies and Python quality tooling needed before Slice 1 implementation | Stage 3 / `#5` | Added |
| `frontend/` | Stage 3 frontend foundation aligned to the Next.js architecture decision; no product feature workflow | Stage 3 / `#5` | Added |
| `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | Local health-check-only container build path, localhost-bound Compose services, writable local artifact volume, digest-pinned images, non-root runtime images, and Docker build gate | Stage 3 / `#5` | Hardened |
| `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/workflows/eval-smoke.yml`, `.github/workflows/quality.yml`, `.github/workflows/quality-gates.yml` | PR-blocking CI, security, Docker build, Playwright smoke, eval smoke, inherited quality gates, and immutable action pinning | Stage 3 / `#5` | Hardened |
| `.pre-commit-config.yaml` | Local pre-commit quality hooks for lint, typecheck, tests, frontend, and guardrails | Stage 3 / `#5` | Added |
| `scripts/ci/*` | Backend lint/typecheck, backend unit/API tests, frontend build/tests, Playwright smoke, Docker build, eval smoke, and dependency/security scan wrappers required before implementation slices | Stage 3 / `#5` | Hardened |
| `scripts/quality/check_stage3_docs.py` | Executable Stage 3 gate for exact-file repo foundation scope, action pinning, Docker hardening, eval smoke fixture, and dependency/CI contracts | Stage 3 / `#5` | Hardened |
| `docs/LOCAL_DEVELOPMENT.md` | Local setup commands for `uv sync`, frontend install, and Stage 3 quality gates | Stage 3 / `#5` | Updated |

## Stage 4 First Slice Traceability

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/stage4.py` and `backend/app/rag/*` | Project creation, markdown/txt upload, parsing, chunking, mock embeddings, project-scoped retrieval, mock LLM generation, claim grounding, citations, and no unsupported claims | Stage 4 / `#4` | Added |
| `tests/unit/test_chunking.py` | Chunking behavior, heading metadata, token caps, and empty-input handling | Stage 4 / `#4` | Added |
| `tests/unit/test_retrieval_and_grounding.py` | Project-isolated retrieval and unsupported-claim failure behavior | Stage 4 / `#4` | Added |
| `tests/api/test_stage4_slice_api.py` | Create project, upload docs, approve docs, ingest/chunk/embed/store, generate grounded script, return citations, and reject unsafe uploads | Stage 4 / `#4` | Added |
| `frontend/src/app/page.tsx` and `frontend/tests/smoke.spec.ts` | User-facing grounded script workflow and citation/evaluation display | Stage 4 / `#4` | Added |
| `evals/smoke/stage4_grounded_script_dataset.json` and `scripts/ci/eval-smoke.sh` | Deterministic RAG eval smoke dataset requiring zero unsupported claims and at least one citation | Stage 4 / `#4` | Added |
| `scripts/quality/check_stage4_docs.py` | Executable Stage 4 static gate for slice artifacts, mocks, dependencies, tests, eval fixture, docs, and review-item disposition | Stage 4 / `#4` | Added |
| `backend/app/stage4.py`, `frontend/next.config.ts`, `docker-compose.yml`, and Stage 4 tests | Verification hardening for mandatory idempotency, atomic multi-document ingestion, bounded local memory/chunks, stronger redaction and prompt-injection refusal, tenant-safe retrieval IDs, same-origin UI API routing for local and Compose paths, and refusal eval fixtures | Stage 4 / `#4` | Hardened |

## Traceability for Stage 5

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/eval/runner.py` and `backend/app/eval/script_faithfulness.py` | RAG-grounded answer metrics (faithfulness, answer relevancy, context precision, recall), unsupported-claim behavior, and golden-happy-path threshold reporting | Stage 5 / `#10` | Added |
| `backend/app/observability/*` | Trace ID, structured event logging, Langfuse adapter behavior, token/cost and latency metrics, and refusal/acceptance observability surfaces | Stage 5 / `#10` | Added |
| `backend/app/stage4.py` | Run telemetry capture for trace metadata, cost/tokens, and refusal/eval status in response payloads | Stage 5 / `#10` | Updated |
| `evals/smoke/stage5_grounded_script_dataset.json`, `evals/smoke/stage5_prompt_injection_set.json`, `evals/smoke/stage5_file_upload_abuse_set.json` | Runtime eval fixture coverage for happy-path quality, prompt injection, and file upload abuse guardrails | Stage 5 / `#10` | Added |
| `scripts/ci/eval-smoke.sh` and `docs/EVAL_REPORT.md` | Stage 5 CI smoke generation, artifact emission, and evidence collection for quality review | Stage 5 / `#10` | Added |
| `scripts/quality/check_stage5_docs.py` | Static Stage 5 quality and artifact presence checks used by local and CI gate dispatch | Stage 5 / `#10` | Added |
| `docs/QUALITY_GATES.md` | Stage 5 gate criteria (faithfulness/relevancy/precision/recall thresholds and guardrail classes) | Stage 5 / `#10` | Updated |

## Traceability for Stage 6

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/stage6.py` | Source English script localization, target-language validation, glossary/project-term preservation, deterministic SubRip subtitle export, `TranslationProvider` adapter, `TTSProvider` adapter, mock/local voice fallback, post-provider glossary/citation validation, bounded captions, capped locked idempotency, and downloadable artifact packaging | Stage 6 / `#11` | Added and hardened |
| `backend/app/main.py` | `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/multilingual-runs` API endpoint with project/run authorization, request boundary constraints, unsupported-language error handling, provider fallback, provider-ready response schemas, and artifact response payloads | Stage 6 / `#11` | Updated |
| `tests/unit/test_stage6_multilingual.py` | Translation preserves product terms, subtitle timing format is valid, provider fallback works, unsupported language tags fail cleanly, in-flight duplicate idempotency is rejected, hostile provider output is refused, and long subtitle tokens stay bounded | Stage 6 / `#11` | Added and hardened |
| `tests/api/test_stage6_multilingual_api.py` | End-to-end API coverage for source English walkthrough translation, downloadable script/subtitle artifacts, mock voice fallback, non-mock local adapter response validation, boundary validation, idempotency replay, and unsupported-language errors | Stage 6 / `#11` | Added and hardened |
| `frontend/src/app/page.tsx`, `frontend/src/app/page.test.tsx`, and `frontend/tests/smoke.spec.ts` | User-facing target language selection, glossary terms, generated multilingual script display, glossary-aware multilingual idempotency keys, artifact MIME allowlisting, and downloadable script/subtitle artifact links only when artifacts are available | Stage 6 / `#11` | Updated and hardened |
| `scripts/quality/check_stage6_docs.py` | Static Stage 6 quality gate for provider adapter markers, dependencies, tests, UI controls, docs metadata, provider-output validation, idempotency hardening, mock voice limitations, accessibility notes, and branch scope | Stage 6 / `#11` | Added and hardened |
| `docs/API_CONTRACT.md`, `docs/ADR/0002-provider-agnostic-adapters.md`, and `docs/QUALITY_GATES.md` | Contract and governance updates for multilingual runs, mock/local adapters, no-real-audio voice limitation, provider-extension surfaces, failure modes, subtitle accessibility, downloadable artifacts, and no paid-provider hardcoding | Stage 6 / `#11` | Updated and hardened |

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
| 2026-06-30 | `#2` / `#27` | Add machine-readable Stage 2 semantic contract and remediate second-pass architecture review findings | Locks idempotency, approved-knowledge state, failed-output safety, evidence snapshots, retrieval thresholds, provider fallback, cache invalidation, and semantic gate checks |
| 2026-06-30 | `#2` / `#27` | Add Stage 2 human review checklist | Adds explicit human signoff criteria for sub-agent, cross-model, architecture, security, AI safety, API/data, portability, performance, observability, and no-product-code review |
| 2026-06-30 | `#2` / `#27` | Resolve final sub-agent and Claude cross-model review findings | Hardens provider-bound secret screening, evaluator evidence, enum parity, cache invalidation, rate limits, deterministic evaluator posture, and Stage 2 checker negative-path behavior |
| 2026-06-30 | `#2` / `#27` | Add reusable Stage 2 review prompt pack | Standardizes the ruthless architecture, security, API/data, portability, and cross-model prompts for future Stage 2 reviews |
| 2026-06-30 | `#5` | Start Stage 3 repo foundation and CI/CD gates | Adds Stage 3 health checks, frontend foundation, dependency manifests, CI wrappers, dependency/security scan path, Docker build path, eval smoke, and executable Stage 3 quality gate |
| 2026-06-30 | `#4` | Start Stage 4 grounded-script Slice 1 implementation | Adds first-slice backend RAG pipeline, mock providers, API tests, frontend workflow, deterministic eval smoke, and Stage 4 quality gate |
| 2026-06-30 | `#4` / PR `#29` | Resolve Stage 4 sub-agent verification blockers | Hardens write idempotency, atomic ingestion, upload/request limits, prompt-injection refusal, redaction, resource budgets, tenant-safe retrieval, same-origin UI routing, and negative eval smoke coverage |
| 2026-07-01 | `#11` | Start Stage 6 multilingual walkthrough implementation | Adds provider-adapter based translation, glossary preservation, subtitle generation, mock/local voice fallback, downloadable artifacts, API/UI tests, and executable Stage 6 quality gate |
| 2026-07-01 | `#11` | Resolve Stage 6 independent review findings | Hardens idempotency, provider-output validation, request boundary constraints, provider-ready response schemas, frontend artifact safety, docs clarity, and executable Stage 6 gate checks |
