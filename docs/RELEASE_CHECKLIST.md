# Stage 8 Release Checklist

Status: pre-release hardening review for issue `#13`.

## Required Gates

- [ ] `make quality` passes on `stage8-performance-security-release-readiness`.
- [ ] Health endpoint < 200 ms local.
- [ ] Script generation mocked path < 2 sec.
- [ ] Upload limit enforced by `Content-Length` and streaming read checks.
- [ ] Upload MIME validation rejects `.md`/`.txt` octet-stream compatibility by default.
- [ ] Write rate limiting returns `RATE_LIMIT_EXCEEDED`.
- [ ] `uv run pip-audit` reports no critical/high active dependency vulnerabilities.
- [ ] `npm --prefix frontend audit --audit-level=high` reports no high/critical frontend dependency vulnerabilities.
- [ ] Docker image scan reports no critical/high vulnerabilities for backend and frontend images.
- [ ] Lighthouse checks run and meet Stage 8 local thresholds.
- [ ] Eval/security gates pass without paid providers or real provider keys.

## Release Blockers

- Multi-worker production deployment is blocked until Stage 6 multilingual state and Stage 7 avatar render/job/idempotency/artifact state are durable.
- Real video export remains blocked until the selected renderer/provider path and license posture are reviewed.
- External avatar providers and public synthetic-media distribution remain blocked until persistent consent/provenance is implemented.

## Rollback

Rollback is code-only for Stage 8: revert the Stage 8 PR, redeploy the previous image pair, and verify `/api/v1/healthz`, eval smoke, dependency audit, and Docker image scan.
