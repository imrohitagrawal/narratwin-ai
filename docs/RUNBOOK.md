# Stage 8 Runbook

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

## Incident Response

- Security finding: stop release, keep the PR open, patch or document a reviewed exception, then rerun `make quality`.
- Container critical/high finding: rebuild from a patched base image or dependency lock, then rerun Docker image scan.
- Performance budget regression: profile the changed path, document the bottleneck, and keep the release blocked until the budget passes.
- Synthetic-media consent/provenance gap: keep external avatar/public export disabled.

## Deployment Limits

Stage 8 does not approve multi-worker production. Process-local idempotency, multilingual artifact replay, avatar render jobs, and avatar artifact metadata remain single-process only until durable persistence is implemented.
