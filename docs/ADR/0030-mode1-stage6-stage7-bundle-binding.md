# ADR 0030: Product Mode 1 Stage 6 to Stage 7 Bundle Binding

## Status

Accepted for issue `#213`.

## Context

Product Mode 1 Checkpoint A through Checkpoint B must prove the local/mock demo
path from browser to frontend to backend to local state and artifacts. The
existing Stage 6 path creates translated scripts, subtitles, voice manifests,
and source/evaluation provenance. The existing Stage 7 path renders a mock/local
avatar demo from the source walkthrough run. That allowed a source-run avatar
export to exist without proving that the multilingual media bundle was validated
and bound to the avatar render.

Issue `#213` covers Checkpoint A, `CH-M1-03`, `CH-M1-04`, `CH-M1-05`,
`CH-M1-06`, and Checkpoint B in one authorized local/mock PR under controller
issue `#155`.

## Decision

The Stage 7 avatar render API requires a `multilingualBundle` object for the
Product Mode 1 checkpoint path. The backend validates the request bundle against
stored Stage 6 state before rendering:

- `sourceRunId`
- `multilingualRunId`
- `targetLanguage`
- translated script checksum
- subtitles checksum
- voice manifest checksum
- context ref IDs
- citation indexes
- evaluation ID and checksum
- mock/local translation and voice provider posture
- consent disclosure version

Stage 7 renders from the validated translated Stage 6 script text. The render
manifest, video placeholder, API trace, idempotency checksum, and local restore
state include the validated multilingual bundle provenance. Missing bundle
evidence fails with `MULTILINGUAL_BUNDLE_REQUIRED`; mismatched, stale, replayed,
or tampered bundle evidence fails with `MULTILINGUAL_BUNDLE_INVALID`.

## Non-Goals

- Product Mode 2.
- Real audio, real video, MP4/WebM export, STT, or imported video.
- External providers, provider keys, hosted/public launch, public distribution,
  or production-readiness claims.
- Mutating stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, or `#168`.
- Closing controller issue `#155` before Checkpoint B evidence and latest-head
  human approval exist.

## Consequences

The local/mock demo can now prove multilingual avatar provenance without
overclaiming real media or production readiness. The frontend must send the
Stage 6 bundle returned by the real backend and expose the six local artifacts:
translated script, subtitles, voice manifest, avatar demo HTML, render manifest,
and video placeholder JSON. Reviewers can inspect checksums and provenance from
the API response and downloaded JSON artifacts.
