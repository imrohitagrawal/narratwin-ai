# Final Review Risk Register

Date: 2026-07-01

Linked stage issue: `#6`

| ID | Risk | Severity | Likelihood | Impact | Status | GitHub issue | Mitigation |
|---|---|---|---|---|---|---|---|
| FR-RISK-001 | Repository branch protection/rulesets may not require the documented Stage 8 status contexts. | High | Unknown | Merges or direct pushes could bypass the intended release gates. | Open | `#38` | Capture repository settings evidence for `main`, including required checks and direct-push prevention. |
| FR-RISK-002 | Stage 4/6/7 state is process-local rather than durable ACID/CAS-backed metadata. | High | Certain for current implementation | Multi-worker deployment, restart recovery, and production idempotency are unsafe. | Open | `#39` | Implement durable metadata/job/idempotency/artifact state before production or multi-worker release. |
| FR-RISK-003 | Production dashboards, alert routes, first-hour watch procedure, and rollback communication channels are undefined. | High | Certain for current implementation | Operators cannot detect or respond to release regressions with production-grade evidence. | Open | `#39` | Define ownership, dashboards, alerts, paging/escalation, and rollback communications. |
| FR-RISK-004 | AI safety evaluation remains deterministic/local and not representative of external provider behavior. | Medium | High if external providers are enabled | Unsupported or unsafe generated media/script behavior may not be caught under real provider variability. | Open | `#39` | Keep external providers disabled; add provider-specific evals and red-team cases before enabling them. |
| FR-RISK-005 | Moderate npm vulnerabilities exist in the Lighthouse dev-tool dependency chain. | Medium | Medium | Local/CI tooling dependency exposure remains below current high/critical blocking threshold but should not be ignored. | Accepted non-blocking for current gate | None | Reassess when Lighthouse updates are compatible; keep runtime image free of dev dependencies. |
| FR-RISK-006 | Frontend smoke uses `next start` while Next reports standalone-output guidance. | Low | Medium | Future smoke portability may degrade across environments. | Open | None | Align Playwright webServer command with standalone output or document why local smoke intentionally uses `next start`. |
| FR-RISK-007 | Large shared modules increase review and maintenance risk. | Medium | Medium | Security and behavior changes are harder to isolate in `backend/app/main.py`, `stage4.py`, and `stage7.py`. | Open | None | Split by stable ownership boundaries after release blockers are resolved, without changing behavior. |
| FR-RISK-008 | Performance evidence is too narrow for production-like confidence. | Medium | High | Health-only Locust and mocked frontend smoke can overstate integrated path readiness. | Open | `#43` | Add scoped load/E2E evidence for upload, ingestion, generation, multilingual, and avatar export paths before stronger release claims. |
| FR-RISK-009 | Optional telemetry can egress when Langfuse credentials are configured. | Medium | Medium | Local/demo privacy claims may be ambiguous if telemetry opt-in boundaries are not explicit. | Open | `#44` | Document opt-in telemetry behavior and keep raw prompts/uploads out of external telemetry. |
| FR-RISK-010 | Frontend CSP allows `script-src 'unsafe-inline'`. | Medium | Medium | XSS defense-in-depth is weaker than a stricter CSP. | Open | `#44` | Tighten CSP or document why the current Next.js local/demo posture needs the exception. |
| FR-RISK-011 | Structured logs do not fully match the documented EventEnvelope shape. | Medium | Medium | Incident review and audit trails are weaker than the observability contract implies. | Open | `#44` | Align log event schema with the documented event envelope before production monitoring claims. |
| FR-RISK-012 | Top-level `docs/RISK_REGISTER.md` is stale relative to Stage 4-8 and Final Review state. | Medium | High | Readers may consult the wrong risk source and miss current release blockers. | Open | `#44` | Reconcile or explicitly supersede the top-level risk register with the Final Review register. |

## Release Blocking Risks

The risks that block production/public release are:

- FR-RISK-001
- FR-RISK-002
- FR-RISK-003
- FR-RISK-004 if any external provider or public synthetic-media path is enabled
- FR-RISK-008 before production-like performance or integrated E2E claims

## Accepted Local-Demo Limits

For local mock-provider portfolio use only, the following limits are acceptable
when clearly disclosed:

- process-local in-memory state
- mock/local providers only
- local deterministic evals
- no real video export
- no external avatar provider
- no public synthetic-media distribution claim
- telemetry remains local/no-op unless explicitly configured and disclosed
