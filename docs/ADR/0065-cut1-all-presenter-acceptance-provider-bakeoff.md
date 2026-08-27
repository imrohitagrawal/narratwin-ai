# ADR 0065: Cut 1 all-presenter acceptance and provider bake-off

- Status: Proposed by Issue #452; no activation until reviewed and merged
- Date: 2026-08-28
- Decision owners: Product, AI quality, media, security/privacy
- Scope: Lane B governance/readiness/evidence only

## Context

Meera is the primary presenter, Raj the first backup, and Myra the second.
Local/key-free providers remain valuable for CI and negative-path proof, but
their output is not evidence of the desired human-like presenter quality. The
project therefore needs one executable acceptance contract before any later
voice or video experiment. Stage 1 Issue #16 still blocks Lane A product work.

The three approved stills are checksum-bound fictional project identities.
They prove identity inputs, not motion, voice, captions or realism. Their
current framing is `HEAD_SHOULDERS_UPPER_TORSO`; Raj and Myra have no visible
hands. The contract must preserve this limitation rather than manufacture
hands-visible readiness or claim full-body realism.

## Decision

Adopt three closed machine-readable artifacts:

1. `cut1-all-presenter-acceptance-matrix-v1.json` binds presenter order,
   approved assets/inputs, current framing readiness, equal per-presenter
   criteria, fallback behavior and numeric media/accessibility gates.
2. `cut1-blinded-human-evaluation-protocol-v1.json` preregisters the exact
   six-cell matched-pair 2AFC study and its crossed model, bootstrap, power,
   exclusions, rater calibration, dimension, severe-defect and retest rules.
3. `cut1-provider-bakeoff-contract-v1.json` records the quality-first voice,
   video and future-Q&A candidates plus provider-specific constraints.

Future evidence records use the two closed JSON Schemas and the modular
validator. Every Meera/Raj/Myra × English × landscape/portrait cell passes
independently. No overall score or aggregate can hide a failing, invalid or
inconclusive cell. Passing supports only the checksum-bound controlled Cut 1
artifact; it does not establish literal indistinguishability, public release,
production readiness or unrestricted use.

The human endpoint is generated-presenter identification probability in a
matched-pair forced-choice task. Chance is 0.50. A crossed viewer/pair logistic
model must produce a model-standardized 90% bootstrap interval strictly inside
`(0.40, 0.60)`. The protocol requires 200 eligible viewers total, 400 ratings
per cell, at least 10,000 successful bootstrap draws, and at least 100,000 power
simulations whose estimated power and lower 95% Wilson bound are at least 0.90.
These constants are OWNER product-risk decisions, not external universal
standards.

Caption lexical accuracy and spoken-word coverage are separate measurements.
Neither substitutes for caption timing/cues or WCAG evidence. Blink,
expression, head, torso, arm, hand/finger, body, hair/clothing/background,
voice/prosody and language each require scorable events with zero confirmed
`FAIL` and zero `UNCERTAIN`; severe identity, limb/hand/finger or temporal
defects veto the affected cell.

## Provider and security posture

- Voice bake-off: Google Gemini 2.5 Pro TTS baseline and ElevenLabs challenger;
  Google Flash remains a separately authorized future latency option.
- Batch video: HeyGen first candidate, D-ID constrained talking-head fallback,
  Synthesia conditional, and Higgsfield exploratory-only.
- Tavus remains future interactive Q&A only.
- Non-cloned fictional voices only; no real-person likeness or asset overwrite.
- Every candidate remains disabled and `NOT_AUTHORIZED` or more restrictive.
  No account, key, provider call, egress, spend or media generation is granted.
- Later experiments require SecretRef-only credentials, segment screening,
  tenant/project/actor lineage, hard caps, idempotency, `BILLABLE_UNKNOWN`
  reconciliation, provider-output distrust, disclosure metadata, immutable
  hashes, retention/deletion confirmation, tombstones and resurrection checks.

## Consequences

Quality is evaluated before cost while cost remains hard-capped. Provider
choices stay replaceable. Selection ratings cannot double as confirmatory
acceptance; final evidence needs frozen candidate bytes and an independent
holdout. Raj/Myra hands-visible media remains blocked until a later Lane A issue
authorizes provenance-bound derivatives without overwriting the originals.

The C2 validator is intentionally `CUT1.NOT_IMPLEMENTED`. Independent reviews
must bind the exact C2 head/tree before C3 freezes expectations; C4 may change
only the marked validator region. Any post-freeze contract defect stops for
OWNER disposition.

OWNER corrective comment `5445887301` resolves the stopped post-freeze audit:
the validator receives a readability-only 480-line/<40 KB ceiling, Issue #452
dispatcher coverage moves to its own bounded test, and the fake secret mutant
uses a non-secret-shaped value. The aggregate budget and every authority,
activation, egress, spend, provider, media and release prohibition remain
unchanged. C2 RED and C3 hashes must be regenerated before readable C4 work.

## Alternatives rejected

- Treat local/mock renders as final quality evidence: they do not prove the
  desired human behavior.
- Select one permanent provider now: freshness, legal posture, identity
  compatibility and actual quality remain unproved.
- Aggregate presenters or aspects: this can hide backup or portrait failures.
- Reframe or replace approved inputs: no such asset or Lane A authority exists.

## References

Issue #452 OWNER comments `5443917600`, `5444058376`, `5444076231`, and
`5445887301` (body SHA-256
`6c667549e12c3db9478f69ea6dfe580ecf9e0b0e0b603550c7e62657df8d66e8`);
Issues #432, #449 and #450; ADR 0054; the Cut 1 presenter, AI-quality,
enterprise-readiness, roadmap and demo-acceptance contracts.
