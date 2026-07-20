# ADR 0031: Frontend Lighthouse Audit Remediation

## Status

Accepted for issue `#219`.

## Context

PR `#218` could not become merge-eligible because the required dependency audit
path failed on the existing frontend dev-tool dependency graph. The blocking
findings were in Lighthouse transitives: a high-severity `brace-expansion`
advisory and moderate OpenTelemetry/Sentry/Lighthouse advisories.

Waiting for a third party is not acceptable when the repository can move to an
available audit-clean dependency graph without changing product runtime behavior.
The affected dependency is Stage 8 Lighthouse tooling used for local/CI frontend
performance, accessibility, best-practices, and SEO checks.

## Decision

Update the frontend Lighthouse dev dependency from `^13.4.0` to `^13.4.1` and
refresh `frontend/package-lock.json` so installs resolve to an audit-clean
transitive graph. The lock now resolves Lighthouse through updated Sentry,
OpenTelemetry, and brace-expansion transitives that clear `npm audit`.

This is a development and CI tooling remediation only. It does not change
application runtime code, product mode behavior, provider posture, media
capabilities, or launch posture.

## Non-Goals

- Product Mode 2.
- Real audio, real video, MP4/WebM export, STT, or imported video.
- External providers, provider keys, hosted/public launch, public distribution,
  or production-readiness claims.
- Runtime frontend component changes.
- Backend, provider, RAG, avatar, Docker, database, or Compose changes.
- Mutating stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, or `#168`.

## Consequences

`make dependency-audit` can pass without suppressing or ignoring the advisory.
The repository keeps the dependency-security gate meaningful while avoiding a
third-party waiting path. PR `#218` can be refreshed after this remediation
merges so its status reconciliation can run against an audit-clean baseline.
