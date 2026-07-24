# ADR 0038: Issue 280 PR E Local Demo Closure Contract

## Status

Accepted for issue `#280` PR E.

## Context

Issue `#280` PR A through PR D established the repair matrix, safe input/API
contract, local/mock API slice, and browser-visible UI slice. PR D intentionally
left the final output-correctness closure unresolved: the Issue 280 local demo
did not yet prove all 25 supported local-demo languages, material depth and
audience behavior, artifact/export parity, correctness-report parity, or full
browser-visible evidence for arbitrary bounded synthetic project knowledge.

The endpoint remains a checkpoint repair surface, not the Stage 6 production
translation service and not a hosted/public demo. PR E therefore needs a
bounded contract that is strong enough for local/demo closure evidence without
creating provider, media, cloned-identity, or production claims.

## Decision

Extend `/api/v1/checkpoint3/issue280/local-e2e-demo` as the Issue 280 PR E
closure contract:

- accept arbitrary bounded public-safe synthetic markdown through the existing
  PR B request and refusal taxonomy;
- generate a citation-bound English script from extracted source facts;
- deterministically convert that generated script across the 25 supported
  Priority 1 local-demo languages from the Stage 6 language catalog;
- make `CONCISE`, `STANDARD`, and `DEEP` output materially different while
  preserving source-grounded claim boundaries;
- make recruiter, hiring manager, engineer, product leader, customer,
  beginner, and global-viewer audiences materially different while preserving
  citation and context bindings;
- preserve citation markers, context refs, claim supports, evaluation IDs and
  checksums, trace IDs, glossary terms, and segment count across API response,
  stored metadata, UI, artifacts, and correctness report;
- emit seven local artifacts: translated script, subtitles, transcript
  metadata, voice manifest, avatar demo HTML, render manifest, and video
  placeholder;
- keep all provider posture fields local/mock or disabled and keep real media,
  cloned identity, paid providers, real provider calls, and network egress
  unavailable;
- use `make issue280-output-correctness` as the closure verifier that starts
  repo services, opens a real browser, submits arbitrary bounded synthetic
  markdown, observes the Issue 280 network path, checks desktop/mobile visible
  evidence, validates safe refusal/retry/replay states, and writes public-safe
  local evidence under ignored `reports/` paths.

The deterministic target-language text is local/mock conversion evidence only.
It is not a claim of arbitrary human-grade translation, real-world language
quality, provider quality, or production readiness.

## Consequences

PR E can mark the remaining Issue 280 matrix rows as executable local/demo
closure evidence when the verifier, local validation, GitHub CI, and human
review pass on the exact latest PR head.

The contract remains issue-scoped and local/mock. It does not authorize
Checkpoint 3B implementation, Checkpoint 3C, hosted/public deployment, provider
account setup, provider SDK installation, paid spend, real provider calls,
cloned identity runtime, cloned voice, cloned face, digital twin behavior,
real-person likeness, real media binaries, public distribution, arbitrary
human-grade or real-world translation quality, provider quality, or production
readiness.

Issue `#249` and issue `#280` remain open until merge closeout confirms the
reviewed status of this exact PR E head and records routine post-merge facts in
PR/issue comments rather than creating a successor status-only PR.
