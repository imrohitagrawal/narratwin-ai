# ADR 0062: Nano ID 3.3.18 security refresh

## Status

Accepted for Issue #428 review on 2026-08-14. This is a security prerequisite,
not product, release, or production authority.

## Context

Accepted main contains transitive Nano ID 3.3.17 through PostCSS. The current
reviewed advisory `GHSA-2v37-7h3g-55p8` / `CVE-2026-67213` marks releases below
3.3.18 affected by an infinite-loop denial of service. The fail-closed frontend
audit therefore blocks Issue #150 even though 3.3.17 satisfied the advisory
range reviewed during Issue #403.

## Decision

Refresh only `node_modules/nanoid` in `frontend/package-lock.json` to official
3.3.18 with registry integrity
`sha512-DTg4MJbGMWkfi6VZFdNt2/caMbQy4Ou+Op/hJQvGEWcnVfoA1QA+xzRKAzw9jD6+GVOOeYr/mIcuDSdug6F6+w==`.
Do not add a direct dependency or override. Preserve every other lock record,
audit threshold, scanner, workflow, Dockerfile, and product/runtime surface.

Current frontend container evidence validates a bounded inventory shape tied to
the reported architecture rather than an exact package-tree hash. The focused
container contract passes unchanged, so this route does not reintroduce the
superseded exact-inventory binding used by Issue #403.

## Consequences

The High dependency finding is removed without suppressing it. Issue #150 may
resume only after Issue #428 passes local and hosted gates, independent review,
eligible approval, merge, and merged-main verification. Issue #427 remains
frozen and inactive. Deployment, release, public availability, and production
readiness remain No-Go.

