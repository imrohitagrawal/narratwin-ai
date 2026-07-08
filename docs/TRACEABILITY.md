# Traceability Register

This file maps product requirements to implementation slices, tests, evaluation
evidence, and documentation updates.

Update this file whenever a change impacts the PRD, product strategy, roadmap,
personas, core user journeys, acceptance criteria, or product behavior.

## Version

- Last updated: 2026-07-02
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

## Traceability for Stage 7

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/stage7.py` | Mock/local avatar rendering adapter, disabled external adapter stub, strict local-only provider config validation, provider metadata/config cross-checks, enum fallback reasons, render job status lifecycle, provider failure fallback, process-local render/artifact metadata storage, exact trusted HTML renderer validation with active content rejection, semantically bound strict JSON render manifest, self-contained strict JSON video export placeholder, AI-generated avatar/video disclosure, synthetic avatar consent, cloned identity disablement, artifact MIME/extension/size/checksum validation, safe filename checks, source citation/evaluation IDs and checksums, trace metadata, evaluation status preservation, and capped locked idempotency with semantic-validation and terminal failure replay | Stage 7 / `#12` | Added |
| `backend/app/main.py` | `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders` API endpoint with project/run authorization, completed-and-passed source run checks, evaluation evidence requirement, source context-ref IDs, citation indexes, evaluation ID/checksum propagation, request boundary constraints, synthetic avatar consent controls, cloned identity rejection, provider fallback, provider config response schema, render job status history, and avatar demo artifact payloads | Stage 7 / `#12` | Updated |
| `tests/unit/test_stage7_avatar.py` | Mock avatar export shape, disclosure metadata, render job lifecycle, provider config validation, provider fallback behavior, failed provider fallback, unexpected provider exception fallback, malformed provider output rejection, fallback reason enum validation, provider metadata/config mismatch rejection, active HTML/CSS/base/srcset rejection, benign escaped web-term allowance, exact trusted HTML mismatch rejection, manifest mismatch rejection, strict JSON extra-field rejection, cloned identity rejection, synthetic avatar consent requirement, hostile provider artifact rejection, artifact metadata storage, in-flight duplicate idempotency rejection, semantic-validation failure idempotency replay/conflict, and terminal failed idempotency replay | Stage 7 / `#12` | Added |
| `tests/api/test_stage7_avatar_api.py` | End-to-end API coverage for validated avatar demo artifacts, provider config, render job status, trace evidence IDs/checksums, self-contained video placeholder artifact metadata, mock/local provider fallback, consent failure, cloned identity failure, missing evaluation evidence rejection, and idempotency replay | Stage 7 / `#12` | Added |
| `frontend/src/app/page.tsx`, `frontend/src/app/page.test.tsx`, and `frontend/tests/smoke.spec.ts` | User-facing avatar demo export workflow, affirmative synthetic avatar consent control with material local/no-clone terms, disclosure display, avatar metadata, source-matched demo preview, export artifacts page section, live error status, busy state, visible blocked artifact reasons, distinct accessible download labels, avatar demo/render-manifest/video-placeholder download links, and artifact MIME/extension/base64/UTF-8/size/checksum/JSON-schema/active-HTML/filename validation before downloads are enabled | Stage 7 / `#12` | Updated |
| `scripts/quality/check_stage7_docs.py` | Static Stage 7 quality gate for provider adapter markers, provider config, render job status, tests, UI controls, docs metadata, disclosure, consent, cloned identity rejection, artifact validation, mock/local defaults, branch scope, recommended review items, and UI/UX Pro Max skill-lock governance | Stage 7 / `#12` | Added |
| `docs/API_CONTRACT.md`, `docs/ADR/0002-provider-agnostic-adapters.md`, `docs/QUALITY_GATES.md`, and `docs/RECOMMENDED_REVIEW_ITEMS.md` | Contract and governance updates for avatar render runs, mock/local adapters, provider config validation, render job lifecycle, no-real-video limitation and placeholder artifact, provider-extension surfaces, failure modes, AI disclosure, consent controls, downloadable HTML/JSON artifacts, public-use license checks, no paid-provider hardcoding, and Stage 8 follow-up recommendations | Stage 7 / `#12` | Updated |

## Traceability for Stage 8

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/main.py` and `backend/app/stage4.py` | Stage 8 health marker, client-IP keyed and bounded write rate limiting, fail-closed request `Content-Length` limits plus actual ASGI body-byte counting, upload limit enforcement, strict upload MIME validation, provider-bound prompt secret screening, request ID/error envelope preservation, and Stage 4 idempotent terminal semantic failures | Stage 8 / `#13` | Hardened |
| `backend/app/stage6.py` and `tests/unit/test_stage6_multilingual.py` | RR-029 direct domain-service rejection of blank glossary terms, secret-like glossary rejection before provider calls, Stage 6 idempotent terminal semantic failures, and exact-schema voice manifest validation | Stage 8 / `#13` | Hardened |
| `tests/api/test_stage8_hardening_api.py` | health endpoint < 200 ms local, mocked script generation < 2 sec, upload MIME rejection, request-size rejection including missing and under-reported `Content-Length`, prompt secret screening, and rate-limit behavior | Stage 8 / `#13` | Added |
| `perf/stage8_locustfile.py` and `scripts/ci/performance-smoke.sh` | Performance smoke tests and headless Locust p95 health-budget profile for local API checks | Stage 8 / `#13` | Added |
| `.github/workflows/ci.yml`, `frontend/scripts/run-lighthouse.mjs`, and `scripts/ci/frontend-lighthouse.sh` | Frontend Lighthouse checks for performance, accessibility, best practices, SEO, named audit budgets, and the PR CI `stage8 / performance lighthouse` budget status | Stage 8 / `#13` | Added |
| `.github/workflows/security.yml`, `scripts/ci/dependency-security.sh`, and `scripts/ci/docker-image-scan.sh` | Dependency audit and Docker image scan gates for no critical/high dependency or container vulnerabilities, including PR CI execution and pinned Dockerized Trivy fallback | Stage 8 / `#13` | Hardened |
| `docs/RELEASE_CHECKLIST.md`, `docs/RUNBOOK.md`, `docs/RELEASE_READINESS_REVIEW.md`, and `docs/REVIEW_RIGOR_RETROSPECTIVE.md` | release checklist, rollback notes, runbook, known limitations, multi-worker deployment blocked posture, real video export/license posture block, persistent synthetic-media consent/provenance block, source-run based avatar export decision, and durable review-rigor remediation guidance | Stage 8 / `#13` | Added |
| `demo/stage8_seed_project.md` and `portfolio/README.md` | demo seed data and portfolio README for local, provider-free showcase path | Stage 8 / `#13` | Added |
| `docs/ADR/0006-stage8-release-hardening.md`, `scripts/quality/check_stage8_docs.py`, `docs/QUALITY_GATES.md`, `docs/PROJECT_LEARNINGS_TRACKER.md`, `docs/PROJECT_GOVERNANCE_LEARNINGS.md`, `docs/STAGE_ISSUE_PLAN.md`, `docs/SKILL_LOCK.md`, `docs/THIRD_PARTY_NOTICES.md`, and `docs/RECOMMENDED_REVIEW_ITEMS.md` | Stage 8 hardening decision record, executable Stage 8 gate, reusable project-learning tracker, governance learnings, stage branch scope, active skill/tool lock, third-party notices, and RR-029 through RR-035 dispositions | Stage 8 / `#13` | Added and updated |

## Phase 1 Closure Traceability

| Artifact | Requirement coverage | Stage / issue | Status |
|---|---|---|---|
| `backend/app/main.py` | Trusted local multi-principal simulation keeps `tenant_local`, defaults to `user_local`, validates `X-Local-User-Id`, gates non-empty header use to local/dev/test via `APP_ENV`, and rejects production header identity while preserving tenant/project/owner authorization predicates | Phase 1 Closure / `#37`, PR `#47` | Hardened |
| `tests/api/test_stage4_slice_api.py` | API evidence for missing and whitespace-only local header fallback, alice/bob isolation, invalid header validation, production header rejection, and production default fallback without `X-Local-User-Id` | Phase 1 Closure / `#37`, PR `#47` | Added |
| `docs/ADR/0007-local-principal-contract.md`, `docs/API_CONTRACT.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_AND_PRIVACY.md`, `docs/DATA_MODEL.md`, `docs/THREAT_MODEL.md`, and `docs/PORTABILITY_STRATEGY.md` | Contract and security documentation for trusted local-only principal simulation, non-authentication limits, production rejection, and unchanged authorization predicates | Phase 1 Closure / `#37`, PR `#47` | Updated |
| `scripts/quality/check_phase1_closure_docs.py`, `docs/QUALITY_GATES.md`, and `docs/STAGE_ISSUE_PLAN.md` | Phase 1 Closure gate scope expanded for Module F issue `#37` implementation and contract files without allowing Phase 2 feature work | Phase 1 Closure / `#37`, PR `#47` | Updated |
| `backend/app/stage7.py` and `backend/app/main.py` | Canonical Stage 7 source-evaluation checksum helper binds normalized evaluation ID/status, source run ID, trace ID, normalized source context ref IDs, and normalized source citation indexes; avatar render route, service, and mock provider use the same helper while requiring explicit evidence IDs for positive counts, preserving manifest/artifact validation, duplicate-key JSON rejection, consent, cloned-identity rejection, provider-output validation, source-run authorization, and structured idempotency request checksums | Phase 1 Closure / `#42`, PR `#50` | Hardened |
| `tests/unit/test_stage7_avatar.py` and `tests/api/test_stage7_avatar_api.py` | Regression evidence that source run ID, trace ID, evaluation ID, evaluation status, context ref IDs, and citation indexes independently affect the checksum, positive evidence counts without explicit IDs/indexes are rejected, direct mock-provider checksum mismatches are rejected, duplicate-key provider JSON artifacts are rejected, structured idempotency request checksums avoid delimiter collisions, and API `trace.sourceEvaluationChecksum` equals the helper result for the created source run's actual evidence metadata | Phase 1 Closure / `#42`, PR `#50` | Added |
| `docs/API_CONTRACT.md`, `docs/ADR/0004-avatar-provider-adapter.md`, `docs/QUALITY_GATES.md`, `docs/STAGE_ISSUE_PLAN.md`, and `docs/reviews/PHASE_1_CLOSURE_REPORT.md` | Contract and governance documentation for the shared Stage 7 checksum definition and the narrow issue `#42` Phase 1 closure scope without upgrading release posture | Phase 1 Closure / `#42`, PR `#50` | Updated |
| `.github/workflows/quality-gates.yml`, `scripts/ci/verify_branch_protection.py`, `docs/STATUS.md`, `docs/reviews/PHASE_1_CLOSURE_REPORT.md`, `docs/RELEASE_READINESS_REVIEW.md`, `docs/RELEASE_CHECKLIST.md`, `docs/RISK_REGISTER.md`, `docs/RUNBOOK.md`, and `docs/evals/phase1_golden_questions.jsonl` | Post-PR `#47`/`#50` reconciliation records `#37` and `#42` as closed, records live branch-protection evidence for `#38`, adds required-context drift checking to `policy-gates`, records the user-repository limitation on direct pusher restrictions, keeps `#39` release-blocking, classifies `#48` and `#49` as pre-production/P2 hardening, and preserves the production No-Go posture while local/mock demo readiness remains separate from production go-live | Phase 1 Closure / `#37`, `#38`, `#39`, `#42`, `#48`, `#49` | Updated |
| `backend/app/storage/file_state.py`, `backend/app/rag/store.py`, `backend/app/stage4.py`, `backend/app/stage6.py`, `backend/app/stage7.py`, and `backend/app/main.py` | Optional file-backed JSON snapshots provide local restart recovery for Stage 4 project/document/ingestion/walkthrough/RAG and idempotency state, Stage 6 multilingual idempotency replay state, and Stage 7 avatar render/idempotency/artifact metadata. Snapshot files may contain uploaded text, chunks/context, generated outputs, eval details, subtitles, artifact payloads, and metadata, so they are sensitive local files. `/api/v1/ops/status` exposes bounded durability and monitoring posture without state-file paths, raw content, or secrets. | Phase 1 Closure / `#39` | Added |
| `.env.example`, `tests/unit/test_local_durability.py`, and `tests/api/test_health_api.py` | Runtime configuration and regression evidence for `NARRATWIN_STATE_DIR`, Stage 4/6/7 restart replay, and the ops status API contract. | Phase 1 Closure / `#39` | Added |
| `backend/app/rag/store.py`, `backend/app/stage4.py`, `backend/app/stage6.py`, `backend/app/stage7.py`, and `tests/unit/test_local_durability.py` | Follow-up local restore-invariant hardening for issue `#55`: Stage 4 restored document/project relationships, chunk/document derivation checks, ingestion/run/evaluation/support survival, failed-idempotency drops, stale-low counter derivation, operation-scoped rollback, all-or-nothing RAG chunk insertion when local embedding fails, Stage 6 derived artifact/provider payload consistency, and Stage 7 artifact metadata consistency. Public regression tests now cover both partial chunk rollback after an embedding failure and preservation of a concurrent successful public create after a slow terminal persist failure. This remains local single-process durability evidence and does not satisfy production-grade issue `#39` durability requirements. | Phase 1 Closure / `#39`, `#55` | In progress |

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
| 2026-07-01 | `#12` | Start Stage 7 avatar rendering adapter and export implementation | Adds mock/local avatar rendering, strict provider config validation, render lifecycle status, provider failure fallback, local HTML demo export with active content rejection, semantically bound JSON render manifest, semantically bound video placeholder artifact, source-matched demo preview/export-artifact UI, AI disclosure, affirmative synthetic avatar consent controls, cloned identity rejection, artifact validation, API/UI tests, and executable Stage 7 quality gate |
| 2026-07-01 | `#13` | Start Stage 8 performance, security hardening, and release readiness | Adds performance smoke tests, API latency budget checks, frontend Lighthouse checks, rate limiting, request size limits, strict upload MIME validation, dependency audit, Docker image scan, release checklist, runbook, demo seed data, portfolio README, release-readiness review, and explicit blockers for multi-worker state, real video export, external avatar providers, and public synthetic-media consent/provenance |
| 2026-07-01 | `#40` | Reconcile canonical RTM during Phase 1 Closure | Updates `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` from stale planned statuses to implemented/local-demo statuses for Stage 4-8 behavior while preserving production No-Go limits. |
| 2026-07-02 | `#37` / PR `#47` | Reconcile local principal contract during Phase 1 Closure | Documents and tests trusted local/dev/test-only `X-Local-User-Id` simulation, production rejection, default `user_local` fallback, and unchanged tenant/project/owner authorization predicates. |
| 2026-07-02 | `#42` / PR `#50` | Harden Stage 7 source evidence checksum binding during Phase 1 Closure | Adds the canonical `build_source_evaluation_checksum` helper, routes avatar render checksum computation through it, rejects direct mock-provider checksum mismatches, rejects synthesized evidence for positive counts, rejects duplicate-key provider JSON artifacts, uses structured idempotency request checksums, and adds unit/API regression coverage for source run ID, trace ID, evaluation ID/status, context refs, and citation indexes. |
| 2026-07-02 | `#37`, `#42`, `#48`, `#49` | Reconcile Phase 1 closure state after PRs `#47` and `#50` merged | Marks `#37` and `#42` closed with evidence, keeps `#38` and `#39` as release-blocking, and classifies `#48` and `#49` as pre-production/P2 hardening rather than local/mock Phase 1 demo blockers. |
| 2026-07-02 | `#38` / PR `#53` | Verify GitHub `main` branch protection and required CI contexts | Records live branch-protection evidence for strict required checks, required PR review, admin enforcement, blocked force pushes, blocked deletions, and conversation resolution; direct pusher restrictions were attempted but are unavailable on this user-owned repository per GitHub API validation; `#39` remains the remaining original Phase 1 P0/P1 production blocker. |
| 2026-07-03 | `#38` / PR `#53` | Add reproducible required-context drift checking | Adds `scripts/ci/verify_branch_protection.py` to the required `policy-gates` workflow so pull requests fail if the branch summary API no longer reports `main` protected with exact required CI contexts, `enforcement_level: everyone`, and GitHub Actions app bindings. |
| 2026-07-03 | `#39` | Add local durability and ops status evidence | Adds optional single-node JSON state snapshots for Stage 4/6/7 local restart recovery and `/api/v1/ops/status` for bounded local durability/monitoring metadata; production release remains No-Go pending ACID/CAS metadata, cross-worker locking, migrations, backup/restore, production idempotency, dashboards/alerts, first-hour watch, and rollback communications. |
| 2026-07-09 | `#55` | Triage additional local restore invariants after PR `#54` | Maps preserved stash work to Stage 4/6/7 restore graph, derived artifact, idempotency, counter, and rollback invariants before a follow-up PR decides which hunks to adopt. |
| 2026-07-09 | `#55` / PR `#56` | Address blind-review rollback findings | Stages Stage 4 RAG chunk embeddings before store mutation, adds RED-confirmed public regression coverage for partial chunk rollback on embedding failure, and adds public API concurrency coverage that a failed terminal persist does not erase a later committed create. Issue `#39` remains open and production durability remains No-Go. |
