# Stage 8 And Phase 1 Release Checklist

Status: Stage 8 merged through PR `#33`; Final Review merged through PR `#45`;
Phase 1 Closure remains No-Go until P0/P1 issues `#35` through `#42` close or are
explicitly downgraded with evidence.

## Required Gates

- [x] Stage 8 `make quality` passed on `stage8-performance-security-release-readiness` before PR `#33` merge.
- [x] Health endpoint < 200 ms local.
- [x] Script generation mocked path < 2 sec.
- [x] API write requests without valid `Content-Length` are rejected before body parsing (`Content-Length is required` when missing), and actual ASGI body bytes are counted so under-reported `Content-Length` cannot bypass local budgets.
- [x] Upload MIME validation rejects `.md`/`.txt` octet-stream compatibility by default.
- [x] Write rate limiting returns `RATE_LIMIT_EXCEEDED`.
- [x] `uv run pip-audit` reports no critical/high active dependency vulnerabilities in recorded Stage 8 evidence.
- [x] `npm --prefix frontend audit --audit-level=high` reports no high/critical frontend dependency vulnerabilities in recorded Stage 8 evidence.
- [x] Docker image scan reports no critical/high vulnerabilities for backend and frontend images locally and in PR CI.
- [x] Lighthouse checks run and meet Stage 8 local category and named audit thresholds.
- [x] Locust headless smoke records health endpoint traffic and keeps local p95 under 200 ms.
- [x] Eval/security gates pass without paid providers or real provider keys in recorded Stage 8 and Final Review evidence.
- [ ] Phase 1 P0/P1 blockers `#35` through `#42` are closed or explicitly downgraded with evidence.
- [ ] `make lint`, `make typecheck`, `make test`, `make api-test`, `make ui-test`, `make e2e`, `make eval`, `make security`, and `make ci` pass for the closure branch.
- [ ] `make secrets-scan`, `make security-scan`, `make dependency-audit`, and `make container-scan` pass for the closure branch.
- [ ] Docker Compose local readiness is verified or unused services are documented honestly.
- [ ] `docs/reviews/GO_NO_GO.md` is updated by a reviewed PR before any release tag.

## Release Blockers

- Multi-worker production deployment is blocked until Stage 6 multilingual state and Stage 7 avatar render/job/idempotency/artifact state are durable.
- Real video export remains blocked until the selected renderer/provider path and license posture are reviewed.
- External avatar providers and public synthetic-media distribution remain blocked until persistent consent/provenance is implemented.
- Release readiness is blocked until `main` branch protection or repository rulesets are enabled and require the emitted Stage 8 status contexts, including `quality / secrets`, `security / docker build`, and `stage8 / performance lighthouse`, or until a reviewed No-Go exception is recorded.
- Phase 2 is blocked until Phase 1 P0/P1 issues are closed or explicitly downgraded with evidence.
- A release tag is blocked until all Phase 1 gates pass locally and in CI.

## Rollback

Stage 8 has no database migration or durable data rollback. Rollback is code-only:

1. Revert PR `#33` or deploy the previous `main` image pair from PR `#32` commit `7f7196a`.
2. Rebuild/redeploy backend and frontend images from the previous commit.
3. Notify the reviewer/owner in the PR thread that Stage 8 was rolled back.
4. Verify `/api/v1/healthz`, eval smoke, dependency audit, Docker image scan, and frontend smoke.

Expected rollback time: under 15 minutes for local/demo deployments, assuming Docker image build cache is warm.
