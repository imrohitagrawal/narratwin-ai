# ADR 0074: Browserslist 4.28.8 security refresh

## Status

Accepted for Issue #495 review on 2026-09-02. This is a dependency-security
prerequisite, not product, provider, release, or production authority.

## Context

Accepted main resolves transitive `browserslist` 4.28.4 through frontend build
tooling. On 2026-09-01, the strict npm audit began reporting two High findings:

- `GHSA-c83g-rgw3-j3cx`, unbounded query-cache memory growth; and
- `GHSA-73wf-gq98-2v4g`, crash/prototype write through untrusted custom stats.

Both advisories affect versions through 4.28.6. The required security gate must
remain fail closed; suppression or an audit-threshold reduction is unacceptable.

## Decision

Refresh only the transitive Browserslist resolution to 4.28.8. Its declared
dependency ranges require five corresponding browser-data/tool records:
`baseline-browser-mapping` 2.11.20, `caniuse-lite` 1.0.30001810,
`electron-to-chromium` 1.5.419, `node-releases` 2.0.54, and
`update-browserslist-db` 1.3.2.

Keep `frontend/package.json` byte-identical. Add no direct dependency or
override. Exact record identity, registry URL, integrity, and six-record-only
lock drift are executable contracts. Historical js-yaml, brace-expansion, and
nanoid isolation tests validate this delta before normalization and continue to
reject every unrelated record change.

## Consequences

Deterministic install, frontend build, audit, container build, and image scan
use the patched resolution. Application behavior, provider configuration,
credentials, narration, speech, audio, captions, avatars, persistence, and
network/spend authority do not change.

Rollback means reverting the reviewed PR only if the resulting lock still
passes the then-current strict security gates; restoring an affected version is
not an acceptable rollback. T05 audio/listening, T06, T07, T08, deployment,
release, production readiness, and Cut 1 completion remain separate gates.
