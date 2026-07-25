# ADR 0040: Issue 280 Semantic Local Demo Correction

## Status

Accepted for issue `#298` as corrective evidence for issue `#280`.

## Context

Issue `#280` PR E introduced the local/demo closure contract for arbitrary
bounded public-safe synthetic markdown, grounded English generation, 25-language
local-demo conversion, depth/audience adaptation, and browser-visible evidence.
Post-merge browser audits later showed that the contract was too weak for the
strongest semantic requirement: target transcripts could be metadata-only mock
sentences or English fallback templates while tests still passed.

The endpoint remains a checkpoint repair surface. It is not the production
Stage 6 translation provider, not a hosted/public demo, and not a human-grade
translation quality claim.

## Decision

Amend the issue `#280` local-demo closure contract so deterministic
multilingual conversion means deterministic local semantic clause rendering for
the supported bounded synthetic project clause families, not metadata-template
success.

The corrected contract:

- maps supported bounded public-safe synthetic source clauses to explicit
  semantic clause families;
- renders those clause families across all 25 supported Priority 1 local-demo
  languages with deterministic local phrasebook text;
- preserves glossary terms, citation markers, source segment count,
  context refs, claim supports, evaluation IDs/checksums, trace IDs, and
  artifact/report parity;
- rejects metadata-only target text, English fallback in non-English target
  transcripts, localized source-segment/protected-term templates, missing
  citations, unsupported semantic clauses, and unsafe output;
- fails closed with `ISSUE280_TRANSLATION_REFUSED` when a requested language or
  source clause is outside the deterministic local support set;
- strengthens `make issue280-output-correctness` and the Issue 280 Playwright
  verifier so browser-visible target text is checked for semantic markers across
  all 25 supported local-demo languages.

## Consequences

Issue `#298` can provide semantic correction evidence for the affected issue
`#280` rows only after local validation, GitHub CI, and human review pass on the
exact latest PR head. Matrix rows with user-visible output quality requirements
must distinguish semantic executable evidence from structural response-shape
evidence.

This ADR does not authorize provider setup, provider SDK installation, provider
keys, paid spend, real provider calls, hosted/public deployment, cloned identity
runtime, real media, public distribution, arbitrary human-grade translation
quality, provider quality, or production readiness. Unsupported clause families
must be implemented deterministically in a later reviewed slice or honestly
refused without marking semantic conversion rows complete.
