# ADR 0006: Stage 8 Release Hardening Gates

## Status

Accepted for Stage 8.

## Date

2026-07-01

## Context

Stage 8 moves NarraTwin AI from feature-slice implementation into
release-readiness hardening. The product still runs in local/mock mode, but the
review surface now includes performance budgets, request abuse controls,
dependency audits, Docker image scanning, frontend Lighthouse checks, and launch
evidence.

The Stage 8 review found that header-only request-size checks, caller-controlled
rate-limit keys, optional container scanning, and shallow performance smoke tests
would leave release risk hidden behind passing local unit tests.

## Decision

Stage 8 hardening is part of the architecture contract, not only test coverage.

- API write requests under `/api/v1/` require a valid non-negative
  `Content-Length` before body parsing; missing length fails with
  `411 CONTENT_LENGTH_REQUIRED`, malformed length fails with
  `400 INVALID_CONTENT_LENGTH`, and oversized length fails with
  `413 REQUEST_TOO_LARGE`.
- Local write rate limiting is keyed by client IP instead of caller-supplied
  headers, rejects over-budget writes with `429 RATE_LIMIT_EXCEEDED`, and bounds
  retained key state.
- Provider-bound walkthrough prompts get secret-like content screening before
  generation.
- Performance smoke tests run both focused API latency tests and a headless
  Locust health-endpoint p95 budget check.
- Frontend Lighthouse checks enforce category scores and named audit budgets,
  including request count through the audit details table when no numeric value
  is provided by Lighthouse.
- Docker image scanning is required in the Stage 8 local gate and PR security
  workflow. The scanner order is local Trivy, Grype, pinned Dockerized Trivy, then
  Docker Scout fallback.
- Release checklist, runbook, status, traceability, skill lock, and third-party
  notices must remain consistent with the executable gates.

## Alternatives Considered

### Keep request-size checks on `Content-Length` only when present

Rejected. ASGI clients can send a body without that header, so fail-open behavior
would bypass the Stage 8 upload/request budget.

### Use caller-controlled local user headers for rate-limit identity

Rejected. It is acceptable for local demos to be unauthenticated, but rate-limit
identity must not be trivially rotated by changing a request header.

### Treat Docker scans as local-only evidence

Rejected. Stage 8 requires release-readiness evidence in PR CI, so the security
workflow must invoke the same image scan gate.

## Consequences

Positive:

- request budget enforcement fails closed
- local abuse controls are harder to bypass
- container vulnerability evidence is available in CI artifacts
- performance and Lighthouse checks measure concrete budgets, not just tool
  availability
- release reviewers have a single documented decision for Stage 8 hardening

Negative:

- clients that omit `Content-Length` on write requests must be fixed or routed
  through a supported upload path
- local rate limiting remains process-local and is not approved for multi-worker
  production deployment
- Dockerized Trivy introduces an additional third-party CI/tooling dependency
  that needs final release license review

## Related Documents

- `docs/QUALITY_GATES.md`
- `docs/API_CONTRACT.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/RUNBOOK.md`
- `docs/TRACEABILITY.md`
- `scripts/ci/docker-image-scan.sh`
- `.github/workflows/security.yml`
