# ADR 0039: Frontend Brace Expansion Audit Remediation

## Status

Accepted for issue `#296`.

## Context

The required frontend dependency audit began failing on GitHub advisory
`GHSA-mh99-v99m-4gvg`, reported through transitive `brace-expansion` in the
frontend ESLint/minimatch tooling graph. The audit suggestion included broad
major upgrades, but the branch scope is only to restore the required local and
CI security gates without changing product runtime behavior.

A direct override of `brace-expansion` alone made `npm audit` pass but broke
ESLint because older `minimatch` callers expected the legacy
`brace-expansion` function export shape. The remediation therefore needs the
compatible pair: a modern `minimatch` version that expects the modern
`brace-expansion` API.

## Decision

Pin frontend npm overrides to `minimatch@10.2.5` and
`brace-expansion@5.0.8`, then refresh `frontend/package-lock.json`.

Keep Next.js, ESLint, eslint-config-next, Playwright, Vitest, and TypeScript at
their existing declared dependency versions. Validate with `npm audit`,
frontend lint, typecheck, unit tests, and production build.

## Non-Goals

- Product runtime code changes.
- Backend, provider, RAG, avatar, Docker, database, or Compose changes.
- New frontend components, routes, pages, or user-facing behavior.
- Provider setup, provider keys, real provider calls, paid spend,
  hosted/public launch, public distribution, or production-readiness claims.
- PR `#295` branch mutation.
- Closing issue `#249`.

## Consequences

The frontend dependency graph is audit-clean without suppressing the advisory
or replacing the existing frontend quality toolchain. The override is dev-tool
scope and remains subject to the existing dependency license review before any
release claim.
