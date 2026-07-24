# ADR 0037: PostCSS Audit Remediation

## Status

Accepted for issue `#289`.

## Context

The required frontend dependency audit failed on GitHub advisory
`GHSA-r28c-9q8g-f849`, which affects `postcss <=8.5.17`. The repository already
uses a frontend `overrides.postcss` entry to keep the Next.js and Vite dependency
graph audit-clean without downgrading the framework.

The split dependency-only and governance-only draft PRs could not become
merge-eligible independently: the dependency-only PR was blocked by inherited
Stage 8 governance marker drift, and the governance-only PR was blocked by the
same PostCSS audit finding still present on `main`.

## Decision

Update the frontend PostCSS override to exactly `8.5.23` and refresh
`frontend/package-lock.json` so Next.js and Vite resolve to the patched PostCSS
version. Keep Next.js at its current major version and reject audit suggestions
that would downgrade Next.

Bundle this dependency remediation with the minimum Stage 8 governance
marker/checker repair required for the same branch to pass required CI. This is
a security unblock, not product implementation.

## Non-Goals

- Product runtime code changes.
- Next.js downgrade.
- New frontend components, pages, routes, or user-facing behavior.
- Backend, provider, RAG, avatar, Docker, database, or Compose changes.
- Provider setup, provider keys, real provider calls, paid spend, hosted/public
  launch, public distribution, or production-readiness claims.
- Closing issues `#249` or `#280`.
- Modifying PR `#284`.

## Consequences

`npm audit` and `make dependency-audit` can pass without suppressing the
advisory. The Stage 8 quality gates can validate against an audit-clean
dependency graph and corrected governance markers in a single mergeable unit.
