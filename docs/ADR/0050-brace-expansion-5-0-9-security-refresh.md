# ADR 0050: brace-expansion 5.0.9 security refresh

- Status: Proposed for Issue #360 review
- Date: 2026-08-04
- Decision scope: frontend development tooling only

## Context and decision

The explicit npm override and generated lock select `brace-expansion` 5.0.8, affected by
GHSA-rgw5-rvv9-x895 / CVE-2026-69152. Refresh only that override to exact 5.0.9 and regenerate the lock
mechanically. Preserve `minimatch` 10.2.5 and every other direct/transitive version. Parsed-JSON comparison,
Node `20 || >=22` compatibility, clean installation, audit, frontend gates, and exact-head review provide evidence.

## Boundaries and limitations

No ignore, waiver, suppression, downgrade, override relaxation, or risk acceptance is permitted. This decision
changes no product or provider behavior and grants no product, provider, deployment, release, public-hosting, or
production-readiness authority. It does not complete Issue #358, Issue #359, or Cut 1.
