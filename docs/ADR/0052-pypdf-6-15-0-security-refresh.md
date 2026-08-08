# ADR 0052: pypdf 6.15.0 security refresh

- Status: Proposed for Issue #401 exact-head review
- Date: 2026-08-08
- Decision scope: root Python dependency and lock resolution only

## Context

Accepted main installs direct `pypdf` 6.14.2. Strict `pip-audit` reports
CVE-2026-71852 and CVE-2026-71870; both reviewed advisories identify 6.15.0 as
the first patched release. Repository search finds no product import, and PDF
uploads remain rejected, but an installed unreachable vulnerable dependency is
not audit-clean.

Official PyPI JSON/simple metadata, fresh artifact downloads, and PEP 740
provenance bind the 6.15.0 wheel and source distribution to `py-pdf/pypdf` and
their exact lockfile SHA-256 values. The upstream release tag is
maintainer-PGP-verified and the package remains BSD-3-Clause.

## Decision

Raise only the direct lower bound to `pypdf>=6.15.0` and regenerate only the
root metadata plus sole pypdf lock record. Require exact artifact identity and
hash tests, unrelated-dependency isolation, strict audit, full security,
quality, CI, exact-head review, eligible non-author approval, and merged-main
acceptance. Preserve Markdown/text ingestion and the explicit PDF rejection.

## Alternatives and consequences

Removal with fail-closed PDF behavior, a pinned reviewed upstream patch, and a
replacement parser were evaluated under owner fail-forward authority. They are
rejected because the verified official patched release is available and
compatible. Unofficial artifacts, mutable VCS references, vendored binaries,
advisory waivers, ignores, and severity reductions remain prohibited.

Rollback may not restore vulnerable 6.14.2. This decision adds no PDF support,
product/runtime behavior, provider, RAG, presenter, media, Docker/workflow,
deployment, release, public, trademark, Issue #391, or production authority.
