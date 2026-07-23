# Issue 276 C3A-R1 Review Evidence

Issue: `#276`  
Branch: `phase-1-closure-c3a-r1-major-market-multilingual-output-correctness`  
Scope: local/mock Checkpoint 3A multilingual output correctness repair.

## Fan-Out Review Status

The requested sub-agent fan-out was attempted after implementation. All four
spawned reviewers failed before returning review output because the account
usage limit was reached:

| Requested reviewer | Result | Fallback |
|---|---|---|
| Output-Correctness Reviewer | Tooling errored before review output. | Local independent output-correctness pass below. |
| TDD Reviewer | Tooling errored before review output. | Local independent TDD/order pass below. |
| Doubt-Driven Reviewer | Tooling errored before review output. | Local independent adversarial pass below. |
| False-Positive Reviewer | Tooling errored before review output. | Local independent mutation/false-positive pass below. |

## Output-Correctness Review

Status: `PASS`

Commands:

```text
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
```

Results:

```text
tests/acceptance/test_checkpoint3_output_correctness.py: 5 passed
frontend Checkpoint 3 real browser: 1 passed
```

Evidence inspected:

| Artifact | Finding |
|---|---|
| `reports/checkpoint3-multilingual/priority1-coverage-matrix.json` | 175 matrix rows covering Priority 1 positive and negative cases. |
| `reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json` | 25 Priority 1 language rows, including `hi`. |
| `reports/checkpoint3-real-browser/playwright-output/.../issue-269-c3a-cp8-browser-evidence.json` | Browser-visible source English, target transcript, English reference, citations, and matching metadata artifact are true for French/Latin, Hindi/Devanagari, Arabic/RTL Arabic script, Hebrew/RTL, Japanese/CJK, Korean/Hangul, Russian/Cyrillic, and Thai/Southeast Asia. |

Conclusion: Checkpoint 3A now executes real local/mock API and browser behavior
for multilingual output correctness. It no longer accepts metadata-only success
or a flat translated string as sufficient evidence.

## TDD Review

Status: `PASS`

Commands:

```text
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/unit/test_checkpoint3_acceptance_gate.py -q
npm --prefix frontend run test -- page.test.tsx
```

Results:

```text
Stage 6 unit/API/harness set: 80 passed
frontend page.test.tsx: 16 passed
```

Old-behavior proof:

| Commit | Evidence |
|---|---|
| `4868784 test: prove c3a multilingual output false passes` | Added behavior tests before implementation. The RED run failed on missing Priority 1 catalog/transcript validation and hardcoded UI catalog exports. |
| `e48b7af docs: add c3a multilingual repair preflight` | Recorded issue-scoped invariant and failure matrix before product/code edits. |

Conclusion: The tests prove behavior at API, artifact, validation, acceptance,
and UI rendering boundaries rather than private helper implementation details.

## Doubt-Driven Review

Status: `PASS with residual local-demo limitation`

Disproof attempts checked:

| Risk challenged | Evidence |
|---|---|
| Catalog presence is mistaken for generation support. | Priority 2 tags are cataloged as planned/unsupported and runtime refuses local/demo generation instead of fake success. |
| `COMPLETED` metadata overrules bad text. | Transcript correctness validation is required before completed multilingual result persistence. |
| Browser evidence remains Latin-only. | CP8 now requires representative script-family browser coverage for Devanagari, RTL Arabic/Hebrew, CJK, Hangul, Cyrillic, Latin, and Southeast Asia. |
| Artifact existence overrules artifact content. | Stage 6 metadata artifacts are compared against structured transcript segments and correctness metadata. |

Command:

```text
make checkpoint3-acceptance
```

Result:

```text
Checkpoint 3 acceptance complete: 8 passed, 0 planned, 0 failed.
```

Residual risk: deterministic translations are local/demo fixtures for controlled
accepted scripts only. Arbitrary input outside fixture coverage must remain an
unsupported local-demo limitation until a real reviewed provider stage exists.

## False-Positive Review

Status: `PASS`

Mutation/negative cases covered:

| False-positive class | Coverage |
|---|---|
| Partial or one-line target text | Mutation fixture rejects partial target coverage. |
| English fallback | Mutation fixture rejects English fallback for non-English languages. |
| Romanized or wrong-script native-language fallback | Native-script validators reject Hindi romanized text, RTL/script drift, CJK/Hangul/Cyrillic/Thai drift, and wrong-script mutations. |
| Missing source English | Mutation fixture rejects missing `sourceText`. |
| Missing English reference | Mutation fixture rejects missing `englishReferenceText`. |
| Citation drift | Mutation fixture rejects changed citation markers/indexes. |
| Missing source/eval/context/claim binding | Mutation fixture rejects missing `sourceRunId`, `evaluationId`, `contextRefIds`, and `claimSupportIds`. |
| Metadata-only success | `COMPLETED` is invalid unless transcript correctness passed. |
| Artifact-only success | Metadata artifact content must match transcript segments. |

Commands:

```text
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/unit/test_stage6_multilingual.py -q
```

Results:

```text
output-correctness acceptance: 5 passed
Stage 6 multilingual unit tests: passed in the combined Stage 6 unit/API/harness run
```

Conclusion: The acceptance gate now fails for the bad behaviors that previously
could pass Checkpoint 3A.

## Validation Snapshot

Final local validation after implementation:

```text
make quality
make checkpoint3-acceptance
make ci
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/unit/test_checkpoint3_acceptance_gate.py -q
npm --prefix frontend run test -- page.test.tsx
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
```

Results:

```text
make quality: passed
make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
make ci: passed
output-correctness acceptance: 5 passed
Stage 6 unit/API/harness set: 80 passed
frontend page.test.tsx: 16 passed
Checkpoint 3 real browser CP8: 1 passed
```

## Manual Rehearsal

The durable human/demo checklist is
`docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md`.
Automated executable evidence remains primary. Human rehearsal should use that
checklist before merge review to spot-check Hindi, Arabic or Egyptian Arabic,
Korean, Japanese or Chinese, Russian or Ukrainian, and German/Spanish/French in
the local demo without making hosted, provider, paid, cloned-identity, real-media,
or production-readiness claims.
