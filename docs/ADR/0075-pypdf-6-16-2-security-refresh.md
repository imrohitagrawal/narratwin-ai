# ADR 0075: pypdf 6.16.2 security refresh

- Status: Proposed for Issue #499 exact-head review
- Date: 2026-09-02
- Decision scope: root Python dependency and lock resolution only

## Context

Accepted main installs direct `pypdf` 6.15.0. The strict public advisory feed
now reports CVE-2026-84309, CVE-2026-84310, and CVE-2026-84311. The complete
fix floor is 6.16.1, and official PyPI currently publishes 6.16.2. Product code
does not import pypdf, and PDF uploads remain rejected, but the installed
dependency must remain audit-clean.

Official PyPI metadata binds the 6.16.2 wheel and source distribution to their
exact lockfile SHA-256 values. The package remains BSD-3-Clause.

## Decision

Raise only the direct lower bound to `pypdf>=6.16.2` and regenerate only the
root metadata plus sole pypdf lock record. Require exact source, filename,
size, and hash tests; unrelated project/lock isolation; strict audit; full
security and quality checks; independent exact-head review; eligible non-author
approval; and merged-main acceptance. Preserve Markdown/text ingestion and the
explicit PDF rejection.

## Alternatives and consequences

Removal, vendoring, an alternate index, advisory suppression, and remaining on
6.16.1 were considered. The official latest patch is the smallest durable
audit-clean correction and avoids an immediately stale floor. Rollback may not
restore vulnerable 6.15.0. This decision adds no PDF support, product/runtime
behavior, provider, voice, narration, media, deployment, release, public, or
production authority.
