# Recommended Review Items

This file is the canonical register for non-blocking review recommendations that
must be reconsidered at the correct future stage. Stage quality gates must check
this file before running the stage-specific gate.

## Policy

- Every non-blocking recommendation from sub-agent, cross-model, human, or PR
  review must be recorded here unless it is fixed immediately.
- Residual risks called out in PR review are non-blocking recommendations and
  must be tracked here before the PR is treated as ready for review.
- `Required stage` is the first stage where the item must be resolved,
  accepted as non-blocking with rationale, or superseded.
- Stage quality must fail when an item is still `Open` or `In Progress` at or
  after its required stage.
- Do not delete completed items; mark them `Done`, `Accepted Non-blocking`, or
  `Superseded` so future reviewers retain the decision history.

## Status Values

- `Open`: not started; quality fails at or after the required stage.
- `In Progress`: actively being addressed; quality fails at or after the
  required stage.
- `Done`: completed and validated.
- `Accepted Non-blocking`: explicitly accepted with rationale.
- `Superseded`: replaced by another item or stage decision.

## Items

| ID | Recommendation | Required stage | Status | Source | Acceptance criteria |
|---|---|---|---|---|---|
| RR-001 | Align CI local storage and vector-store environment defaults, including `LOCAL_STORAGE_ROOT` and a no-vector Stage 3 default. | Stage 3 | Done | Stage 2 portability/performance review | Stage 3 quality validates `.env.example` local storage defaults and requires `VECTOR_STORE=disabled` until the Stage 4 vector-store decision is locked. |
| RR-002 | Strengthen dependency lockfile and security-scan behavior before product dependency manifests are introduced. | Stage 3 | Done | Stage 2 security review | Stage 3 adds `uv.lock`, `frontend/package-lock.json`, and `scripts/ci/dependency-security.sh` with `pip-audit`, `npm audit --audit-level=high`, and Gitleaks coverage. |
| RR-003 | Pin GitHub Actions by immutable SHA or document an explicit exception. | Stage 3 | Done | Stage 2 security review | Checked-in workflow action refs are pinned to 40-character SHAs and `scripts/quality/check_stage3_docs.py` rejects mutable action refs. |
| RR-004 | Expand generic repository guardrails to scan untracked local files, not only tracked files. | Stage 3 | Done | Stage 2 security/AI-safety review | `scripts/guardrails_check.py` covers `git ls-files --others --exclude-standard` in addition to tracked files. |
| RR-005 | Rename or clarify API `Ingestion status` so document-ingestion state and `IngestionRun` job lifecycle state cannot be confused. | Stage 4 | Done | Stage 2 portability/API review | Stage 4 implementation uses `KnowledgeDocument.ingestionStatus` for document-derived state and `IngestionRun.status` for the synchronous run lifecycle; API tests cover both fields. |
| RR-006 | Expand Stage 2 review prompt pack coverage to include review-process artifacts and CI workflow files. | Stage 2 | Done | Stage 2 architecture/portability review | `docs/STAGE2_REVIEW_PROMPT_PACK.md` includes `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`, itself, and `.github/workflows/quality-gates.yml` in relevant prompts. |
| RR-007 | Tighten AI safety `WARNING` wording so unsupported project factual claims cannot be warnings. | Stage 2 | Done | Stage 2 architecture/API review | `docs/AI_SAFETY_AND_EVALUATION.md` reserves `WARNING` for non-factual presentation or ambiguity issues. |
| RR-008 | Clarify observability and audit acceptance semantics for generated output. | Stage 2 | Done | Stage 2 architecture/API review | `docs/ARCHITECTURE.md` states acceptance requires committed run, evaluation, audit, and outbox records, while external sink delivery can fail after commit. |
| RR-009 | Lock active ingestion/generation job uniqueness at the database transaction level. | Stage 4 | Accepted Non-blocking | Stage 3 ruthless architecture review | Stage 4 Slice 1 executes ingestion and generation synchronously in a single-process local store, so no `QUEUED` or `RUNNING` job can overlap. Durable database transaction constraints remain required before asynchronous jobs or migrations are introduced. |
| RR-010 | Persist evaluation, schema, and safety policy version fields with evaluation results. | Stage 4 | Done | Stage 3 ruthless architecture review | Stage 4 `EvaluationResult` includes `policyVersion`, `schemaVersion`, and `safetyPolicyVersion`, and accepted walkthrough responses expose those fields. |
| RR-011 | Lock vector-store tenant isolation strategy before RAG implementation. | Stage 4 | Done | Stage 3 ruthless architecture review | Stage 4 uses an in-memory local vector store partitioned by `tenantId` and `projectId`; retrieval tests verify cross-project chunks are excluded. Chroma remains dependency-prep only until a later persistence decision. |
| RR-012 | Re-evaluate the `httpx2` dev dependency before API test surface expands. | Stage 4 | Accepted Non-blocking | Stage 3 PR review | API tests continue to pass with the inherited `httpx2` test transport dependency; replacement is deferred until the FastAPI/Starlette/httpx compatibility stack settles, with no runtime dependency exposure. |
| RR-013 | Decide whether local Playwright browser installation cost remains acceptable for the first frontend slice. | Stage 4 | Accepted Non-blocking | Stage 3 PR review | Stage 4 keeps Playwright Chromium smoke coverage because the first UI slice needs browser verification; local runs may reuse the installed browser and CI parity is preserved. |
