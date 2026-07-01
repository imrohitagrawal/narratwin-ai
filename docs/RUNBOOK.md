# Stage 8 And Phase 1 Runbook

Status: Stage 8 and Final Review are merged. Phase 1 Closure is active and the
release posture is No-Go until P0/P1 issues `#35` through `#42` close or are
explicitly downgraded with evidence.

## Local Verification

1. Run `make quality`.
2. If Lighthouse fails, inspect `reports/lighthouse/stage8-lighthouse.json` and `reports/lighthouse/frontend-server.log`.
3. If dependency audit fails, inspect `pip-audit`, `npm audit --audit-level=high`, and `reports/security`.
4. If Docker image scan fails, inspect the SARIF files in `reports/security`.

## Operational Checks

- Health: `GET /api/v1/healthz` must return stage `8` and stay under 200 ms locally.
- Readiness: `GET /api/v1/readyz` must return a timestamp and security headers.
- Generation: mocked grounded script generation must stay under 2 sec locally.
- Uploads: accepted files remain markdown/text only, UTF-8 only, size limited, and secret/prompt-injection screened.
- Rate limiting: excessive local write requests return `RATE_LIMIT_EXCEEDED`.
- Monitoring owner: the Phase 1 closure reviewer watches the first local/demo run and records failures in the active Phase 1 closure PR.
- Logs: local API logs and CI artifacts are the authoritative Stage 8 evidence; production dashboards and alert routes are Final Review blockers.
- First-hour production monitoring is not approved in Stage 8 because no production deployment is approved.

## Incident Response

- Security finding: stop release, keep the PR open, patch or document a reviewed exception, then rerun `make quality`.
- Container critical/high finding: rebuild from a patched base image or dependency lock, then rerun Docker image scan.
- Performance budget regression: profile the changed path, document the bottleneck, and keep the release blocked until the budget passes.
- Synthetic-media consent/provenance gap: keep external avatar/public export disabled.

## Rollback

Stage 8 has no schema migration, external provider state, or durable media output to roll back.

1. Revert PR `#33` or check out PR `#32` baseline commit `7f7196a`.
2. Rebuild the previous backend/frontend images with `bash scripts/ci/docker-build.sh`.
3. Redeploy the previous local/demo image pair.
4. Run `GET /api/v1/healthz`, `bash scripts/ci/eval-smoke.sh`, `bash scripts/ci/dependency-security.sh`, and `bash scripts/ci/docker-image-scan.sh`.
5. Post rollback status and remaining blockers in the PR or release thread.

Rollback owner: the release reviewer for the active PR. Expected local/demo rollback time: under 15 minutes with warm Docker cache.

## Monitoring Blockers

Production launch remains blocked until Phase 1 or a later reviewed release phase
defines dashboard locations, alert thresholds, paging/ownership, first-hour watch
procedure, and rollback communication channels for a real deployment environment.

## Deployment Limits

Stage 8 does not approve multi-worker production. Process-local idempotency, multilingual artifact replay, avatar render jobs, and avatar artifact metadata remain single-process only until durable persistence is implemented.
