# Checkpoint 3A Multilingual Rehearsal Checklist

This checklist is secondary manual evidence for issue `#276`. Automated evidence
from `make checkpoint3-acceptance`, targeted API tests, and Playwright remains
primary.

## Scope

- Local/mock demo only.
- No hosted deployment, public URL, provider setup, real provider calls, paid
  spend, cloned identity, real media, public distribution, or production
  readiness claim.
- Use the backend language catalog as the source of truth.

## Reviewer Questions

For each reviewed language:

1. Which language was selected?
2. Is the source English text visible?
3. Is the target-language transcript visible?
4. Is the English reference/back-translation visible for every segment?
5. Does the target text use the expected script?
6. Does the full source script appear covered segment-by-segment?
7. Are citations visible next to translated segments?
8. Do downloaded artifacts contain the same transcript data?
9. Does unsupported local/demo language behavior refuse honestly?
10. Are provider, hosted, paid, cloned, real-media, and production claims absent?

## Minimum Manual Sample

- Hindi / Devanagari
- Arabic or Egyptian Arabic / RTL Arabic script
- Korean / Hangul
- Japanese or Chinese / CJK
- Russian or Ukrainian / Cyrillic
- German, Spanish, or French / Latin
- Bengali or another Priority 2 language as planned/unsupported local-demo

## Evidence Links

- Exhaustive API/output-correctness:
  `tests/acceptance/test_checkpoint3_output_correctness.py`
- Browser visible-output path:
  `frontend/tests/checkpoint3-real-browser.spec.ts`
- Coverage matrix:
  `reports/checkpoint3-multilingual/priority1-coverage-matrix.json`
- Checkpoint summary:
  `reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json`
