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
Because the lock is an input to the final frontend build, also replace the
reviewed inventories with independently reproduced architecture-bound values.
The native arm64 value is
`1803:ad570be227d414b9e0100f21fa1f03aa42e85acad9128f6c01524d780b7ea064`;
the provisional Docker Desktop amd64 measurement is
`1805:9a18413ff9fefd9c665595ab2564c72bb706dcf81b490fffd59b23653ad73858`
and must be replaced by a repeatable native hosted value before acceptance.
Stale and cross-architecture values remain rejected rather than accumulated.

## Rejected alternatives

- Audit suppression or threshold reduction would leave the installed finding.
- Adding nanoid directly would distort ownership of a transitive toolchain dependency.
- Removing or replacing PostCSS would expand the frontend architecture unnecessarily.
- Vendoring a patch is unjustified because an official compatible release exists.

## Consequences

The frontend lock graph becomes audit-clean for this advisory without product,
runtime, UI, provider, Dockerfile, deployment, release, or public-use behavior.
The inventory renewal changes only the exact accepted output of the existing
canonical runtime-tree measurement.
PR #400 remains serialized until this prerequisite passes merged-main acceptance.
