# ADR 0053: nanoid 3.3.17 security refresh

- Status: Accepted for Issue #403
- Date: 2026-08-08
- Decision owners: repository owner and eligible non-author reviewer

## Context

Accepted main locks transitive nanoid 3.3.16 through PostCSS. GitHub's reviewed
GHSA-2v37-7h3g-55p8 / CVE-2026-67213 classifies versions below 3.3.17 in the
3.x line as affected by an unbounded custom-generator zero-size loop. The
repository's High-severity npm audit reproduces the finding locally and in
hosted run `31240954921`.

PostCSS already permits `nanoid ^3.3.16`; no direct nanoid dependency exists.
Official npm metadata for 3.3.17 supplies a registry signature and SLSA
provenance and binds the tarball to SHA-512
`xQLf0A3HOMlgHq0n247/LRuAOYmB7dXJ/DvAxGvsSBij45XtBSmQycu+F8ODbHwns/XyFZagyL1+J0Offw1E0g==`.
A fresh official download independently hashes to SHA-256
`fd821dc3644ff456a61cd8ac67f3741f939d9ce2fb4cbb9c6b3e6c8111285ef6`.
Upstream declares MIT.

## Decision

Refresh only the transitive nanoid lock record from 3.3.16 to 3.3.17. Keep
`frontend/package.json`, the PostCSS range, direct dependencies, and every
unrelated lock entry byte-equivalent to accepted main. Bind that isolation and
official artifact identity in an executable regression contract.

## Rejected alternatives

- Audit suppression or threshold reduction would leave the installed finding.
- Adding nanoid directly would distort ownership of a transitive toolchain dependency.
- Removing or replacing PostCSS would expand the frontend architecture unnecessarily.
- Vendoring a patch is unjustified because an official compatible release exists.

## Consequences

The frontend lock graph becomes audit-clean for this advisory without product,
runtime, UI, provider, container, deployment, release, or public-use behavior.
PR #400 remains serialized until this prerequisite passes merged-main acceptance.
