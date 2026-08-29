# ADR 0069: Bind Cut 1 presenter derivatives separately from source identity

- Status: Accepted for Issue #459 T03 controlled-local readiness
- Date: 2026-08-29
- Decision owner: Issue #459 OWNER checkpoint `5463568867`

## Context

The source presenter registry is immutable authority used by the T04 controller.
Raj and Myra need hands-visible waist-up portraits for later controlled Cut 1
work, while Meera's existing source is already suitable and must not receive a
new binary. Replacing the source registry or changing its digest would silently
invalidate the reviewed T04 authority.

## Decision

Keep `backend/app/presenter_registry.json` and all three original assets
byte-identical. Add an immutable derivative manifest with a separate canonical
digest and additive loader. The loader binds every derivative to the exact
source-registry manifest, source asset, presenter ID/version, reviewed candidate,
converted WebP, privacy/provenance record, and controlled-local posture.

Meera reports `SOURCE_READY_NO_DERIVATIVE`; Raj and Myra report
`DERIVATIVE_READY`. Raj/Myra bindings carry both source and derivative hashes so
callers cannot substitute one authority for the other. Assets must be regular
non-symlink single-frame WebPs below 500,000 bytes, without upscaling or embedded
metadata. Any manifest, identity, path, hash, dimensions, size, rights, review,
source-registry, or binding drift fails closed.

## Consequences

T04's raw registry SHA, source-registry runtime SHA, original assets, evaluator,
and frozen oracle remain unchanged. T03 establishes design-time derivative
readiness only. It does not select or call a provider, generate video or audio,
grant credentials/egress/spend, publish media, run a human study, or prove Cut 1
acceptance, release, deployment, public availability, or production readiness.

Private candidate PNGs remain outside Git pending owner cleanup after merge.
Later narration, audio, rendering, and acceptance increments must consume the
typed readiness/binding and satisfy their own reviewed gates.
