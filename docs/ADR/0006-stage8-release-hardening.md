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
  `400 INVALID_CONTENT_LENGTH`, oversized declared length fails with
  `413 REQUEST_TOO_LARGE`, and actual ASGI body bytes are counted so
  under-reported length cannot bypass the local budget.
- Local write rate limiting is keyed by client IP instead of caller-supplied
  headers, rejects over-budget writes with `429 RATE_LIMIT_EXCEEDED`, and bounds
  retained key state.
- Provider-bound walkthrough prompts and multilingual glossary terms get
  secret-like content screening before provider execution.
- Stage 4 and Stage 6 idempotency retains terminal semantic validation
  failures so exact request replays return the same failure and changed-body key
  reuse returns `IDEMPOTENCY_CONFLICT`; unexpected implementation exceptions
  still release the reservation.
- Stage 6 voice provider manifests are exact-schema validated before
  response/artifact exposure, including top-level and nested field rejection for
  unknown provider output.
- Performance smoke tests run both focused API latency tests and a headless
  Locust health-endpoint p95 budget check.
- Frontend Lighthouse checks enforce category scores and named audit budgets,
  including request count through the audit details table when no numeric value
  is provided by Lighthouse.
- Docker image scanning is required in the Stage 8 local gate and PR security
  workflow. The scan attempts local Trivy, Grype, pinned Dockerized Trivy, and
  Docker Scout per image. A confirmed critical/high SARIF report fails the gate;
  a scanner/tool failure without a usable SARIF report can fall through to the
  next scanner. Scanner exit codes are captured before fallback evaluation so a
  nonzero scan result with usable SARIF cannot be converted into a pass.
- PR CI emits a dedicated `stage8 / performance lighthouse` status when
  `.stage/current` is `8`, running the Locust and Lighthouse budget scripts
  outside the policy-only static quality job.
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

## Phase 1 Closure Addendum For Issue #39

Date: 2026-07-03

Phase 1 Closure issue `#39` adds a local durability and monitoring remediation
without changing the production No-Go decision.

Decision:

- Stage 4, Stage 6, and Stage 7 services may opt into single-node JSON state
  snapshots through `NARRATWIN_STATE_DIR` or service-specific state-file
  variables.
- Persistence remains disabled by default for test isolation and unchanged local
  behavior.
- Snapshot writes use atomic local file replacement and may contain sensitive
  local data needed for restart recovery and idempotency replay: uploaded
  document text, chunks/context, generated scripts, evaluation details,
  translations/subtitles, avatar artifact payloads, base64 content, and
  metadata. These files must remain local and uncommitted.
- `GET /api/v1/ops/status` exposes local durability enablement, non-sensitive
  backend type, bounded record counts, and monitoring flags.
- The ops endpoint must not expose state-file paths, raw uploads, prompts,
  generated outputs, provider payloads, environment values, or secrets.

Consequences:

- Local/mock review can now demonstrate restart recovery for Stage 4 project,
  document, ingestion, walkthrough, RAG, and idempotency state; Stage 6
  multilingual idempotency replay; and Stage 7 avatar render, idempotency, and
  artifact metadata.
- JSON snapshots are not a production database. They do not provide ACID/CAS
  semantics, cross-worker locks, schema migrations, backup/restore policy, or
  production idempotency guarantees.
- Production go-live remains No-Go until a reviewed release phase adds
  production-grade durable metadata and deployment monitoring.

## Phase 1 Closure Addendum For Issue #55

Date: 2026-07-09

Issue `#55` is a follow-up triage issue for additional local restore-invariant
hardening discovered after PR `#54` merged. It remains under the issue `#39`
local-durability evidence scope and does not change the production No-Go
decision.

Decision:

- Stage 4 restore may prune RAG chunks whose restored payload no longer matches
  the owning document text and metadata, and may drop restored document,
  ingestion, walkthrough, evaluation, claim-support, and idempotency rows whose
  relationship graph no longer has the evidence needed to justify terminal
  state.
- Stage 6 restore may drop multilingual idempotency records whose restored
  derivative text, provider payload, artifacts, language tags, citations,
  glossary terms, or checksums no longer agree.
- Stage 7 restore may drop artifact metadata and terminal idempotency records
  that no longer match restored render artifacts, checksums, or serialized
  terminal error details.
- Stale-low counters must be derived from restored IDs, and failed-operation
  rollback must remain operation-scoped so it does not erase later successful
  operations.

Consequences:

- Local restart-recovery evidence becomes stricter about restored graph and
  artifact consistency.
- Corrupt local snapshot rows may be pruned in memory and re-written on the
  next successful persist; this is still not a migration, backup, repair, or
  production recovery system.
- Production go-live remains No-Go until ACID/CAS durable metadata,
  cross-worker locking, migrations, backup/restore, production idempotency,
  dashboards/alerts, first-hour watch, and rollback communications are reviewed.

## Related Documents

- `docs/QUALITY_GATES.md`
- `docs/API_CONTRACT.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/RUNBOOK.md`
- `docs/TRACEABILITY.md`
- `scripts/ci/docker-image-scan.sh`
- `.github/workflows/security.yml`
