# Stage 2 Review Prompt Pack

Version: 1.0
Stage: 2 - Architecture, security, AI safety
Canonical issue: `#2`
Canonical PR: `#27`
Product implementation allowed: no

This pack turns the Stage 2 review strategy into reusable prompts. Use it when
spawning sub-agents or asking for an external second opinion. The goal is to force
independent, line-level, failure-mode review instead of broad opinions.

## Operating Rules

- Review only the current repository state.
- Do not edit files during review.
- Return only actionable findings.
- Every finding must include a severity label and file:line reference.
- Prefer required blockers over general commentary.
- If nothing remains, say `No remaining required blockers.`

## Review Matrix

Run the prompts below in parallel when possible.

### 1. Ruthless Architecture Reviewer

Use this prompt:

```text
Read-only review. Do not edit files. You are the special ruthless architecture/system-design reviewer for NarraTwin AI Stage 2. Review the current branch against best-practice architecture and system design principles for an AI/RAG/video-generation platform. Focus on docs/ARCHITECTURE.md, docs/ADR/*.md, docs/STAGE2_ARCHITECTURE_CONTRACT.json, docs/API_CONTRACT.md, docs/DATA_MODEL.md, docs/PORTABILITY_STRATEGY.md, docs/OBSERVABILITY_AND_COST.md, docs/QUALITY_GATES.md, docs/STAGE_ISSUE_PLAN.md. Stage 2 allows documentation/governance only, no product implementation. Return only actionable findings, ordered by severity, with file:line references where possible. Classify each as REQUIRED before merge or RECOMMENDED later. Pay particular attention to boundaries, state machines, async jobs/idempotency/outbox, provider fallback, RAG retrieval/evidence, isolation, operability, portability, and whether the architecture is locked enough for Stage 4 implementation without ambiguity.
```

### 2. Security And AI Safety Reviewer

Use this prompt:

```text
Read-only review. Do not edit files. Review NarraTwin AI Stage 2 for security, privacy, AI safety, prompt-injection controls, provider key isolation, no secret logging, upload validation, auditability, rate limiting, dependency/OWASP gates, and evaluation guardrails. Focus on docs/SECURITY_AND_PRIVACY.md, docs/THREAT_MODEL.md, docs/AI_SAFETY_AND_EVALUATION.md, docs/API_CONTRACT.md, docs/STAGE2_ARCHITECTURE_CONTRACT.json, scripts/guardrails_check.py, scripts/quality/check_stage2_docs.py, .env.example. Return actionable findings only, ordered by severity, with file:line references where possible. Classify REQUIRED before merge vs RECOMMENDED later. Look for semantic drift and anything that would let Stage 4 leak secrets, cross projects, expose raw unsafe model output, or bypass review.
```

### 3. API, Data, And Evaluation Reviewer

Use this prompt:

```text
Read-only review. Do not edit files. Review Stage 2 API/data/evaluation contract consistency across docs/API_CONTRACT.md, docs/DATA_MODEL.md, docs/AI_SAFETY_AND_EVALUATION.md, docs/STAGE2_ARCHITECTURE_CONTRACT.json, docs/ARCHITECTURE.md, docs/ADR/0002-rag-storage.md, docs/ADR/0005-observability-and-evals.md, scripts/quality/check_stage2_docs.py. Return actionable findings only, ordered by severity, with file:line references where possible. Classify REQUIRED before merge vs RECOMMENDED later. Specifically verify ID prefixes, status enums, idempotency endpoints and states, delete/patch semantics, failed/refused public output semantics, evidence snapshot fields, claim/evaluation fields, retrieval parameters/refusal reasons, and whether checks are semantic enough.
```

### 4. Portability, Performance, And Observability Reviewer

Use this prompt:

```text
Read-only review. Do not edit files. Review Stage 2 for portability, performance, observability, cost controls, CI quality gates, and implementation-readiness. Focus on docs/PORTABILITY_STRATEGY.md, docs/OBSERVABILITY_AND_COST.md, docs/ARCHITECTURE.md, docs/API_CONTRACT.md, docs/DATA_MODEL.md, docs/STAGE2_ARCHITECTURE_CONTRACT.json, docs/QUALITY_GATES.md, scripts/quality/check_stage2_docs.py, scripts/guardrails_check.py, .env.example. Return actionable findings only, ordered by severity, with file:line references where possible. Classify REQUIRED before merge vs RECOMMENDED later. Look for missing budgets, queue/backpressure semantics, cache invalidation, deterministic local mode, CI enforceability, and portability gaps that could block Stage 4.
```

### 5. Cross-Model Second Opinion

Use this prompt after local fixes:

```text
Read-only cross-model second opinion for NarraTwin AI Stage 2. Do not edit files and do not run shell commands. Review the current branch for remaining REQUIRED before-merge blockers only. Stage 2 is docs/governance only; no product implementation allowed. Focus on docs/STAGE2_ARCHITECTURE_CONTRACT.json, docs/ARCHITECTURE.md, docs/API_CONTRACT.md, docs/DATA_MODEL.md, docs/SECURITY_AND_PRIVACY.md, docs/AI_SAFETY_AND_EVALUATION.md, docs/PORTABILITY_STRATEGY.md, docs/OBSERVABILITY_AND_COST.md, docs/ADR/0001-system-architecture.md, docs/ADR/0002-rag-storage.md, docs/ADR/0003-llm-provider-routing.md, docs/ADR/0004-avatar-provider-adapter.md, docs/ADR/0005-observability-and-evals.md, docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md, docs/STAGE2_REVIEW_PROMPT_PACK.md, scripts/quality/check_stage2_docs.py, scripts/guardrails_check.py, .github/workflows/quality-gates.yml, .env.example. Verify architecture, security/privacy, AI safety, API/data/eval consistency, portability/performance/observability, quality gates, and no product-code implementation. Return only actionable REQUIRED blockers with file:line references, or exactly: No remaining required blockers.
```

## Review Order

Recommended sequence:

1. Run architecture, security, API/data, and portability prompts in parallel.
2. Fix required findings.
3. Run the cross-model second opinion.
4. Record the result in `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`.

## Reviewer Output Contract

Each reviewer should answer with:

- severity
- file:line reference
- invariant violated
- why it matters
- minimal fix

If a reviewer cannot find a blocker, it should say `No remaining required blockers.`
