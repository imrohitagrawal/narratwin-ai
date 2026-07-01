# Stage 8 Release Readiness Review

Issue: `#13`
Branch: `stage8-performance-security-release-readiness`
Review date: 2026-07-01

## Decision

Stage 8 adds release-readiness hardening evidence, but does not approve production multi-worker deployment or real public media export. The local mock/provider path can be demoed after `make quality` and CI pass. Stage 8 records multi-worker deployment blocked until durable Stage 6 and Stage 7 state exists.

## Budget Evidence

| Budget | Evidence |
|---|---|
| health endpoint < 200 ms local | `tests/api/test_stage8_hardening_api.py::test_health_reports_stage8_with_local_latency_budget` |
| script generation mocked path < 2 sec | `tests/api/test_stage8_hardening_api.py::test_mocked_script_generation_path_stays_under_two_seconds` |
| upload limit enforced | `Content-Length is required` for write requests before body parsing, uploads keep streaming read limit, and Stage 8 API tests cover both paths |
| no critical/high dependency vulnerabilities | `scripts/ci/dependency-security.sh` |
| no critical/high container vulnerabilities | `scripts/ci/docker-image-scan.sh` using Trivy, Grype, pinned Dockerized Trivy, or Docker Scout; PR CI runs the image scan in the security workflow |
| all eval/security gates pass | `make stage8-quality` runs security and eval smoke gates |

## Hardening Added

- Stage 8 health marker.
- Write rate limiting for local API write methods.
- General request size limits that fail closed on missing/invalid `Content-Length`, plus existing upload streaming limit.
- Strict markdown/plain-text upload MIME validation remains enforced; `application/octet-stream` compatibility is explicitly rejected.
- Provider-bound prompt text is screened for secret-like content before generation.
- Performance smoke tests and headless Locust profile with health p95 threshold.
- Frontend Lighthouse checks with category and named audit thresholds.
- Dependency audit and Docker image scan wrappers.
- Frontend production image strips npm/npx from the runner layer so vulnerable package-manager-only dependencies such as npm-bundled `undici` are not shipped with the standalone server.
- Release checklist, runbook, demo seed data, and portfolio README.

## RR-029 Through RR-035 Disposition

- RR-029: Done. `Stage6Service` now rejects blank glossary terms through direct domain calls.
- RR-030: Done. Frontend artifact safety tests were expanded in Stage 7 and Stage 8 keeps backend validation authoritative.
- RR-031: Accepted Non-blocking. Multi-worker deployment is explicitly blocked until Stage 6 state is durable.
- RR-032: Accepted Non-blocking. Multi-worker deployment is explicitly blocked until Stage 7 render/job/idempotency/artifact state is durable.
- RR-033: Accepted Non-blocking. Real video export remains blocked; local HTML plus JSON placeholder is the only approved Stage 8 posture.
- RR-034: Accepted Non-blocking. External providers and public synthetic-media distribution remain blocked until persistent consent/provenance exists.
- RR-035: Accepted Non-blocking. Avatar export remains source-run based; this source-run based avatar export posture is documented for Stage 8, and multilingual/subtitle-bound rendering is a future explicit product decision before timed media export.

## Independent Security And Release Review

The Stage 8 review checked untrusted upload boundaries, request size handling, rate limiting, dependency audit, Docker scan posture, mock/local provider defaults, synthetic-media consent/provenance blockers, release rollback notes, and no paid-provider credential dependency. Follow-up review also checked sub-agent findings for request-size bypass, rate-limit key trust, CI scan enforcement, performance-smoke depth, rollback actionability, and status-ledger drift. Residual risk is documented as release-blocking limits rather than hidden UI/API behavior.
