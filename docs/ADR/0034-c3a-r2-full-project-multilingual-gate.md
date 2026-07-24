# ADR 0034: C3A-R2 Full-Project Multilingual Gate

## Status

Accepted for issue `#278` review.

## Date

2026-07-24

## Context

PR `#277` repaired the local/mock Stage 6 multilingual output path for
supported controlled generated walkthrough scripts. The next risk was process
recurrence: future work could treat full-project multilingual correctness as a
chat-only concern, rely on representative language classes, or keep catalog
support labels without current executable evidence.

Issue `#278` adds a public-safe full-project corpus gate for Checkpoint 3A
without changing provider posture, hosted-demo posture, real-media posture,
cloned-identity posture, public distribution, raw uploaded knowledge-document
translation API behavior, or production readiness.

## Decision

Stage 6 supported-language evidence is catalog-locked:

- `LANGUAGE_CATALOG_VERSION`, `TRANSCRIPT_VALIDATOR_VERSION`,
  `STAGE6_TRANSLATED_ARTIFACT_SCHEMA_VERSION`, and
  `FULL_PROJECT_REPORT_SCHEMA_VERSION` are explicit evidence invalidators.
- Languages marked `SUPPORTED`, `LOCAL_DEMO_FIXTURE`, and
  `CHECKPOINT3A_EXHAUSTIVE` must pass the C3A-R2 full-project corpus gate.
- Priority 2 local-demo languages remain planned/unsupported unless a future
  issue adds equivalent executable evidence.
- The full-project fixture and checked reports are synthetic and public-safe.
- Context refs and claim-support ids in the gate encode fixture source refs, so
  citation preservation without source-span preservation is not enough.
- Expected-output freshness covers deterministic target transcript outputs for
  every supported language, not only source English rows.
- On the issue `#278` branch, the Phase 1 `make quality` path executes the
  full-project corpus acceptance test so PR CI runs the same C3A-R2 gate.

## Consequences

Positive:

- supported local-demo language claims cannot remain green after catalog,
  validator, fixture, expected-output, artifact-schema, or report-schema drift
- representative language-class evidence cannot substitute for all supported
  languages
- checked coverage/report artifacts become durable repository evidence
- metadata-only, artifact-only, heading-only, missing-body, citation-drift, and
  source-span drift false passes are executable failures

Negative:

- Phase 1 quality on the issue `#278` branch runs an acceptance test in addition
  to static governance checks
- deterministic local/mock fixture support remains narrower than arbitrary
  translation quality and must be described that way

## Non-Goals

This ADR does not authorize provider setup, provider calls, paid spend, hosted
deployment, public URLs, public demos, cloned identity runtime, real media,
public distribution, arbitrary-project translation quality, raw uploaded
knowledge-document translation API claims, or production readiness.
