# Stage 8 Release Checklist

Status: pre-release hardening review for issue `#13`.

## Required Gates

- [ ] `make quality` passes on `stage8-performance-security-release-readiness`.
- [ ] Health endpoint < 200 ms local.
- [ ] Script generation mocked path < 2 sec.
- [ ] API write requests without valid `Content-Length` are rejected before body parsing (`Content-Length is required` when missing), and actual ASGI body bytes are counted so under-reported `Content-Length` cannot bypass local budgets.
- [ ] Upload MIME validation rejects `.md`/`.txt` octet-stream compatibility by default.
- [ ] Write rate limiting returns `RATE_LIMIT_EXCEEDED`.
- [ ] `uv run pip-audit` reports no critical/high active dependency vulnerabilities.
- [ ] `npm --prefix frontend audit --audit-level=high` reports no high/critical frontend dependency vulnerabilities.
- [ ] Docker image scan reports no critical/high vulnerabilities for backend and frontend images locally and in PR CI.
- [ ] Lighthouse checks run and meet Stage 8 local category and named audit thresholds.
- [ ] Locust headless smoke records health endpoint traffic and keeps local p95 under 200 ms.
- [ ] Eval/security gates pass without paid providers or real provider keys.

## Release Blockers

- Multi-worker production deployment is blocked until Stage 6 multilingual state and Stage 7 avatar render/job/idempotency/artifact state are durable.
- Real video export remains blocked until the selected renderer/provider path and license posture are reviewed.
- External avatar providers and public synthetic-media distribution remain blocked until persistent consent/provenance is implemented.
- Release readiness is blocked until `main` branch protection or repository rulesets are enabled and require the emitted Stage 8 status contexts, including `quality / secrets`, `security / docker build`, and `stage8 / performance lighthouse`.

## Rollback

Stage 8 has no database migration or durable data rollback. Rollback is code-only:

1. Revert PR `#33` or deploy the previous `main` image pair from PR `#32` commit `7f7196a`.
2. Rebuild/redeploy backend and frontend images from the previous commit.
3. Notify the reviewer/owner in the PR thread that Stage 8 was rolled back.
4. Verify `/api/v1/healthz`, eval smoke, dependency audit, Docker image scan, and frontend smoke.

Expected rollback time: under 15 minutes for local/demo deployments, assuming Docker image build cache is warm.
