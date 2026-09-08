# ADR 0081: httpx2 2.12 security refresh

- Status: Proposed for Issue #523 exact-head review
- Date: 2026-09-09
- Decision scope: development/test dependency and lock resolution only

## Context

The strict dependency audit began rejecting locked `httpx2` and `httpcore2`
2.5.0 after five public advisories appeared. The complete `httpx2` fix floor is
2.12.0. Repository reachability is limited to Starlette/FastAPI test transport;
the backend image installs with `--no-dev` and does not contain these packages.
The mandatory audit nevertheless fails closed on vulnerable development tools.

Official PyPI metadata requires `httpcore2==2.12.0` outside Emscripten and
`httpx2-jsfetch` 1.0 only on Emscripten. The universal lock therefore adds the
official browser-only transitive record even though ordinary hosted and local
tests do not install it.

## Decision

Raise the sole direct development requirement to `httpx2>=2.12.0` and refresh
only its resolved graph: `httpx2` 2.12.0, `httpcore2` 2.12.0, and required
`httpx2-jsfetch` 1.0. Bind exact official registry, version, dependency edge,
artifact URL, SHA-256, size, uniqueness, and unrelated-lock isolation in
mutation tests. Keep the advisory scan strict and preserve TestClient/API
behavior through focused, full-quality, and hosted-topology checks.

## Consequences

The update removes CVE-2026-84378, CVE-2026-84379, CVE-2026-84380,
CVE-2026-84381, and CVE-2026-84382 from the locked development graph without an
ignore or waiver. Rollback may not restore 2.5.0. This decision adds no product
runtime, provider, voice, narration, audio, avatar, media, credential, egress,
spend, deployment, release, public, or production authority.
