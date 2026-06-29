# Recommended Review Items

This file is the canonical register for non-blocking review recommendations that
must be reconsidered at the correct future stage. Stage quality gates must check
this file before running the stage-specific gate.

## Policy

- Every non-blocking recommendation from sub-agent, cross-model, human, or PR
  review must be recorded here unless it is fixed immediately.
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
| RR-001 | Align CI local storage and vector-store environment defaults, including `LOCAL_STORAGE_ROOT` and `CHROMA_PATH`. | Stage 3 | Open | Stage 2 portability/performance review | CI validates or sets documented local storage/vector defaults without requiring paid providers. |
| RR-002 | Strengthen dependency lockfile and security-scan behavior before product dependency manifests are introduced. | Stage 3 | Open | Stage 2 security review | CI fails on manifests without approved lockfiles or wrappers and documents dependency scan behavior. |
| RR-003 | Pin GitHub Actions by immutable SHA or document an explicit exception. | Stage 3 | Open | Stage 2 security review | Workflow action refs are SHA-pinned or a Stage 3 security rationale records why tag refs remain acceptable. |
| RR-004 | Expand generic repository guardrails to scan untracked local files, not only tracked files. | Stage 3 | Open | Stage 2 security/AI-safety review | `scripts/guardrails_check.py` covers `git ls-files --others --exclude-standard` or documents why Stage-specific untracked scanning is sufficient. |
| RR-005 | Rename or clarify API `Ingestion status` so document-ingestion state and `IngestionRun` job lifecycle state cannot be confused. | Stage 4 | Open | Stage 2 portability/API review | Stage 4 API schema uses unambiguous enum names before implementation starts. |
| RR-006 | Expand Stage 2 review prompt pack coverage to include review-process artifacts and CI workflow files. | Stage 2 | Done | Stage 2 architecture/portability review | `docs/STAGE2_REVIEW_PROMPT_PACK.md` includes `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`, itself, and `.github/workflows/quality-gates.yml` in relevant prompts. |
| RR-007 | Tighten AI safety `WARNING` wording so unsupported project factual claims cannot be warnings. | Stage 2 | Done | Stage 2 architecture/API review | `docs/AI_SAFETY_AND_EVALUATION.md` reserves `WARNING` for non-factual presentation or ambiguity issues. |
| RR-008 | Clarify observability and audit acceptance semantics for generated output. | Stage 2 | Done | Stage 2 architecture/API review | `docs/ARCHITECTURE.md` states acceptance requires committed run, evaluation, audit, and outbox records, while external sink delivery can fail after commit. |
