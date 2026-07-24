# Checkpoint 3A Full-Project Multilingual Rehearsal Checklist

This checklist is reviewer-facing secondary evidence for issue `#278`. The
primary evidence is executable:
`tests/acceptance/test_checkpoint3_full_project_multilingual.py`,
`reports/checkpoint3-multilingual/full-project-coverage-matrix.json`, and
`reports/checkpoint3-multilingual/full-project-correctness-report.json`.

## Scope

- Local/mock Checkpoint 3A product path only.
- Governed public-safe full-project corpus only.
- No arbitrary-project translation quality claim.
- No provider quality claim.
- No hosted/public demo, provider setup, paid spend, cloned identity runtime,
  real media, public distribution, or production-readiness claim.
- No raw uploaded knowledge-document translation API claim.

## Corpus Checks

Confirm the report records:

- at least three source documents
- at least seven sections
- at least six transcript segments
- at least seven cited claims
- at least seven claim-support bindings
- at least four exported artifacts
- at least 450 coverage rows
- a claim whose support spans multiple source documents
- a row that exposes heading-only, partial-section, or missing-body translation
- public-safe provenance notes

## Language Checks

For every supported language in `backend/app/stage6.py`:

1. Confirm the catalog row is `SUPPORTED`, `LOCAL_DEMO_FIXTURE`, and
   `CHECKPOINT3A_EXHAUSTIVE`.
2. Confirm source English, target segment, and English reference are present for
   every segment.
3. Confirm citations preserve order and point to the same source spans.
4. Confirm `contextRefs` and `claimSupports` remain bound to the same source
   evidence.
5. Confirm output is not heading-only, partial, metadata-only, or artifact-only.
6. Confirm the Stage 6 API transcript surface consumed by the UI, stored
   output, metadata, durable report, and exported artifacts agree.

## Class-Specific Checks

- Hindi/Devanagari: native script, no romanized fallback, and handled domain
  terms.
- RTL: direction metadata, citation punctuation/order, exported artifact
  rendering, and no LTR-only assumptions.
- CJK: sentence segmentation, citation attachment, line wrapping, and no
  artificial word-spacing assumptions.
- Latin-script languages: diacritics, untranslated-English leakage checks,
  represented false-friend risk, and locale punctuation/formatting.
- Priority 2 languages: planned/unsupported local-demo refusal unless a future
  issue introduces equivalent evidence.

## Failure Review

Review at least these negative rows in the coverage matrix:

- partial project translation
- missing document translation
- missing section translation
- single-segment partial success
- heading-only success
- untranslated English fallback for non-English targets
- wrong script
- romanized fallback
- altered claim support
- citation drift
- citation id preservation without source-span preservation
- missing source, target, English reference, context ref, or claim-support
  binding
- metadata-only success
- artifact-only success
- stale coverage row
- unsupported or planned-language fake success

## Stale Evidence Checks

The gate must fail if any of these change without refreshed evidence:

- fixture hash
- expected-output hash
- language catalog version
- validator version
- artifact schema version
- report schema

## Human-Only Checklist

- Confirm the PR body uses reference-only wording for issues `#249` and `#278`.
- Confirm issue `#249` remains open.
- Confirm no provider, hosted/public demo, paid spend, cloned identity, real
  media, public distribution, or production-readiness claim appears.
- Confirm final validation and CI evidence are attached before approval.
