# Stage 2 Human Review Checklist

Version: 1.0
Stage: 2 - Architecture, security, AI safety
Canonical issue: `#2`
Canonical PR: `#27`
Product implementation allowed: no

Use this checklist for the human review before Stage 2 merge. A reviewer must mark
each Required item complete or record an explicit blocking finding in the PR.

## Review Evidence

Required local evidence:

- [ ] `make quality` passes on the Stage 2 branch.
- [ ] `python3 scripts/guardrails_check.py` passes on the Stage 2 branch.
- [ ] `python3 -m py_compile scripts/quality/check_stage2_docs.py scripts/quality/check_quality_stage.py scripts/guardrails_check.py` passes.
- [ ] `python3 -m json.tool docs/STAGE2_ARCHITECTURE_CONTRACT.json` passes.
- [ ] `git diff --check` passes.
- [ ] PR links to issue `#2` with a closing keyword.
- [ ] PR contains no backend, frontend, RAG, avatar, provider, Docker, database, runtime, or product feature implementation code.

## Architecture Review

Required:

- [ ] Architecture covers frontend, backend API, ingestion worker, RAG service,
      script generation service, evaluator service, avatar rendering adapter,
      provider abstraction, observability pipeline, and CI quality gates.
- [ ] ADRs match the current architecture and do not contradict
      `docs/STAGE2_ARCHITECTURE_CONTRACT.json`.
- [ ] Stage 4 implementation boundaries are explicit enough to start the first
      vertical slice without inventing state machines, IDs, or provider policy.
- [ ] Idempotency, job leasing, retry attempts, outbox dispatch, and backpressure
      semantics are documented for mutating operations.
- [ ] Retrieval strategy v1 defines eligibility, thresholds, tie-breaks,
      evidence snapshots, and refusal behavior before generation.
- [ ] Provider fallback fails closed across egress classes and never silently
      moves from mock/local to non-local providers.

## API And Data Review

Required:

- [ ] API resource IDs, status enums, idempotency endpoints, failure responses,
      and typed schemas match the machine-readable contract.
- [ ] Data model entities, indexes, lifecycle fields, tombstones, and deletion
      semantics match the API contract.
- [ ] Project and document mutations define replay-safe idempotency behavior.
- [ ] Public failed or refused walkthrough responses omit raw generated output
      and accepted script text.
- [ ] EvidenceSnapshot, ContextRef, ClaimSupport, UnsupportedClaim, and
      EvaluationResult fields are aligned across API, data model, and AI safety docs.

## Security And Privacy Review

Required:

- [ ] Secret scanning covers repository content, governance scripts, and provider
      key patterns without allowlisting real secrets.
- [ ] Prompt injection controls treat uploads, prompts, transcripts, retrieved
      chunks, provider outputs, and generated scripts as untrusted input.
- [ ] File upload validation covers type, size, parsing, quarantine, approval,
      storage, and deletion constraints.
- [ ] Tenant, owner, and project isolation use the exact project-scoped predicate
      before lookup, retrieval, generation, evaluation, export, and delete.
- [ ] Provider key isolation, no-secret-logging rules, audit logs, rate limits,
      dependency scanning, and OWASP baseline scan posture are documented.
- [ ] Non-local provider egress requires mandatory secret screening, explicit
      configuration, budget checks, audit events, and provider metadata.

## AI Safety And Evaluation Review

Required:

- [ ] Evaluation blocks unsupported project-specific claims before accepted output.
- [ ] Every extracted claim is evaluated or the run fails with the documented
      claim-budget behavior.
- [ ] Claim-level context references include immutable evidence snapshots with
      source, checksum, retrieval, and redaction metadata.
- [ ] Prompt-injection and unsafe-context refusals are represented in API,
      data, architecture, and safety docs.
- [ ] UI state matrix prevents failed, refused, or unsafe model output from being
      presented as an accepted walkthrough script.
- [ ] Evaluation fixtures and semantic gates are sufficient to prevent Stage 4
      implementation drift.

## Portability, Performance, And Observability Review

Required:

- [ ] Local/dev/test defaults are mock or local, paid providers are optional, and
      portability docs define migration paths for storage, vector store, provider,
      artifacts, and exports.
- [ ] Stage 4 budgets cover file size, corpus size, chunking, retrieval, output,
      evaluation, queue depth, pagination, cache limits, timeouts, retries, and
      provider cost controls.
- [ ] Cache keys include tenant/project identity, approved corpus version,
      document and chunk checksums, retrieval strategy, embedding model, prompt
      template, provider/model, evaluator, and safety policy.
- [ ] Cache invalidation covers approval changes, rejection, quarantine, deletion,
      checksum changes, chunking changes, embedding changes, retrieval policy
      changes, prompt template changes, evaluator changes, and safety changes.
- [ ] RunMetadata, EventEnvelope, and MetricPoint are distinct schemas and do not
      carry secrets, raw uploads, raw provider payloads, or hidden prompts.

## Final Signoff

Required:

- [ ] All required sub-agent findings are resolved or explicitly accepted as
      non-blocking with reviewer rationale.
- [ ] Cross-model second-opinion findings are resolved or explicitly accepted as
      non-blocking with reviewer rationale.
- [ ] The reviewer used `docs/STAGE2_REVIEW_PROMPT_PACK.md` or an equivalent
      prompt set for parallel review coverage.
- [ ] Human reviewer confirms Stage 2 is documentation/governance only and is
      ready for PR review, CI, and merge.

Reviewer:
Date:
Decision: approve / request changes
