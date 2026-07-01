# ADR 0007: Trusted Local Principal Simulation

## Status

Accepted for Phase 1 Closure issue `#37`.

## Date

2026-07-02

## Context

Final Review issue `#37` found drift between the documented local principal
contract and the API implementation. The active docs described a fixed
`tenant_local` / `user_local` principal, while the backend accepted
`X-Local-User-Id` and API tests used it to prove `alice` and `bob` project
isolation.

The useful behavior is local multi-principal simulation for isolation tests and
local demos. The risk is treating a caller-controlled header as authentication
outside trusted local execution.

## Decision

NarraTwin AI keeps the trusted local multi-principal header contract with an
explicit environment gate:

- local/dev/test always use `tenant_id = tenant_local`
- `APP_ENV` is read from the environment and unset or blank values default to
  the effective environment `local`
- missing or whitespace-only `X-Local-User-Id` resolves to `actor_id = user_local`
- valid non-empty `X-Local-User-Id` is accepted only when the effective
  `APP_ENV` is `local`, `dev`, or `test`
- valid local simulated principal IDs contain only ASCII letters, digits,
  underscore, or dash and are at most 64 characters
- invalid non-empty local header values return `400 VALIDATION_ERROR`
- non-empty local-principal headers outside local/dev/test return
  `400 LOCAL_PRINCIPAL_HEADER_NOT_ALLOWED`
- `X-Local-User-Id` is not authentication and must never be accepted as
  production identity
- future real authentication replaces only the principal source, not the
  authorization predicate

Project-scoped authorization remains `(tenant_id, owner_id, project_id)`.
Generated IDs are not authorization proof.

## Consequences

Positive:

- existing alice/bob local isolation tests remain meaningful
- production cannot silently accept a spoofable local principal header
- future authentication can swap principal resolution without weakening
  project-scoped predicates

Negative:

- local callers using characters outside the allowed simulation ID set must
  rename their test principals
- the contract remains a trusted local simulation only, not a production auth
  story

## Related Documents

- `docs/API_CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/DATA_MODEL.md`
- `docs/THREAT_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/TRACEABILITY.md`
