# ADR 0051: js-yaml 4.3.1 transitive security refresh

- Status: Proposed for Issue #396 exact-head review
- Date: 2026-08-07
- Decision scope: frontend development-tool lock resolution only

## Context

Clean main and PR #395 resolve `js-yaml` 4.3.0 through
`eslint@9.39.4` → `@eslint/eslintrc@3.3.5`. GitHub-reviewed
`GHSA-5p4m-2wfm-xmqj` affects versions before 4.3.1. The existing
`@eslint/eslintrc` range `^4.1.1` already permits the patched release.

## Decision

Update only the sole `node_modules/js-yaml` lock record to exact 4.3.1 with
the npm-registry tarball and SHA-512 integrity. Preserve `package.json`, all
direct dependencies and overrides, and every unrelated lock record. Require
contract mutations, clean install, strict audit, full security/quality/CI,
exact-head review, eligible non-author approval, and merged-main acceptance.

## Alternatives and consequences

An advisory waiver, ignored audit, or lower severity threshold is rejected.
Adding a direct dependency or override is rejected because the existing
transitive range resolves 4.3.1 without manifest change. The package declares
MIT in npm metadata; controlled-local development/test use is permitted while
full dependency and public-distribution review remains pending.

Rollback may not restore affected 4.3.0. This decision adds no product runtime,
provider, presenter, media, deployment, release, public/LinkedIn, trademark,
Issue #391, or production authority; PR #395 remains blocked until #396 closes.
