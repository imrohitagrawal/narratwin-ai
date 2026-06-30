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
| RR-005 | Rename or clarify API `Ingestion status` so document-ingestion state and `IngestionRun` job lifecycle state cannot be confused. | Stage 4 | Open | Stage 2 portability/API review | Stage 4 API schema uses unambiguous enum names before implementation starts. |
| RR-006 | Expand Stage 2 review prompt pack coverage to include review-process artifacts and CI workflow files. | Stage 2 | Done | Stage 2 architecture/portability review | `docs/STAGE2_REVIEW_PROMPT_PACK.md` includes `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`, itself, and `.github/workflows/quality-gates.yml` in relevant prompts. |
| RR-007 | Tighten AI safety `WARNING` wording so unsupported project factual claims cannot be warnings. | Stage 2 | Done | Stage 2 architecture/API review | `docs/AI_SAFETY_AND_EVALUATION.md` reserves `WARNING` for non-factual presentation or ambiguity issues. |
| RR-008 | Clarify observability and audit acceptance semantics for generated output. | Stage 2 | Done | Stage 2 architecture/API review | `docs/ARCHITECTURE.md` states acceptance requires committed run, evaluation, audit, and outbox records, while external sink delivery can fail after commit. |
| RR-009 | Lock active ingestion/generation job uniqueness at the database transaction level. | Stage 4 | Open | Stage 3 ruthless architecture review | Stage 4 data model or migration defines partial unique constraints, advisory-lock strategy, or equivalent isolation rules for active `QUEUED`/`RUNNING` jobs before job endpoints are implemented. |
| RR-010 | Persist evaluation, schema, and safety policy version fields with evaluation results. | Stage 4 | Open | Stage 3 ruthless architecture review | Stage 4 evaluation result schema includes policy/schema version fields needed to prove which policy accepted cached or replayed output. |
| RR-011 | Lock vector-store tenant isolation strategy before RAG implementation. | Stage 4 | Open | Stage 3 ruthless architecture review | Stage 4 defines Chroma/provider mode, dependency approval, persistence path, required metadata fields, post-query SQL revalidation, and cross-project retrieval-isolation fixtures. |
| RR-012 | Re-evaluate the `httpx2` dev dependency before API test surface expands. | Stage 4 | Open | Stage 3 PR review | Stage 4 either removes `httpx2`, replaces it with the settled FastAPI/Starlette/httpx-compatible test stack, or records an explicit accepted rationale with passing API tests and notices updated. |
| RR-013 | Decide whether local Playwright browser installation cost remains acceptable for the first frontend slice. | Stage 4 | Open | Stage 3 PR review | Stage 4 frontend test strategy either keeps the current local Chromium install behavior with rationale, provides a faster documented local path that preserves CI parity, or supersedes it with an equivalent smoke/e2e gate. |
