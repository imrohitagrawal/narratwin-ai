# Issue 276 C3A-R1 Review Evidence

Issue: `#276`
Branch: `phase-1-closure-c3a-r1-major-market-multilingual-output-correctness`
Scope: local/mock Checkpoint 3A multilingual output correctness repair.

## Fan-Out Review Status

The requested sub-agent fan-out was attempted after implementation. The first
spawned reviewer set failed before returning review output because the account
usage limit was reached. Those obsolete sessions were closed and the required
fan-out was restarted.

The restarted fan-out found blockers; the PR was not treated as ready for human
review at that point.

| Requested reviewer | Result | Fallback |
|---|---|---|
| Output-Correctness Reviewer | `BLOCK` on Atlas source receiving NarraTwin target text; later `BLOCK` on Spanish NarraTwin fixture containing untranslated `project knowledge`. | Fixed source-specific Atlas fixtures, complete Spanish fixture text, and added regression assertions. |
| TDD Reviewer | `BLOCK` because original RED evidence failed at import/collection and follow-up behavior tests were uncommitted. | Added behavior-level tests that fail on the prior implementation and recorded this explicitly; final commit carries the follow-up tests. |
| Doubt-Driven Reviewer | `BLOCK` on provider script/transcript divergence, arbitrary NarraTwin pseudo-translation, weak browser artifact comparison, and UI hardcoded catalog fallback. | Added provider/transcript parity validation, arbitrary-fixture refusal, stronger browser artifact parity, and removed frontend catalog fallback. |
| False-Positive Reviewer | `BLOCK` on missing metadata-only/artifact-only response mutations; rerun returned `PASS`. | Added response-level false-pass mutations and required coverage rows. |

Final review status after rerun on pushed commit `c066d26`: `PASS` across all
required reviewer angles.

| Final reviewer | Final result | Evidence summary |
|---|---|---|
| Output-Correctness Reviewer | `PASS` | Ran API, artifact, UI/browser, unsupported-language, provider-divergence, and catalog probes; no output-correctness findings remained. |
| TDD Reviewer | `PASS` | Replayed the committed follow-up test diffs against prior implementation commit `8a4b3d4`; they failed at behavior assertions, not import/collection. |
| Doubt-Driven Reviewer | `PASS` | Attempted to disprove arbitrary-fixture refusal, provider parity, UI catalog, browser artifact parity, Hindi, and Priority 2 refusal; no blockers found. |
| False-Positive Reviewer | `PASS` | Verified false-positive mutations, coverage matrix rows, metadata-only/artifact-only rejection, and checkpoint gate. |

## Output-Correctness Review

Status: `PASS`

Commands:

```text
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
```

Results:

```text
tests/acceptance/test_checkpoint3_output_correctness.py: 7 passed
frontend Checkpoint 3 real browser: 1 passed
```

Evidence inspected:

| Artifact | Finding |
|---|---|
| `reports/checkpoint3-multilingual/priority1-coverage-matrix.json` | 225 matrix rows covering Priority 1 positive and negative cases. |
| `reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json` | 25 Priority 1 language rows, including `hi`. |
| `reports/checkpoint3-real-browser/playwright-output/.../issue-269-c3a-cp8-browser-evidence.json` | Browser-visible source English, target transcript, English reference, citations, decoded metadata artifact parity, and decoded translated-script artifact parity are true for French/Latin, Hindi/Devanagari, Arabic/RTL Arabic script, Hebrew/RTL, Japanese/CJK, Korean/Hangul, Russian/Cyrillic, and Thai/Southeast Asia. |

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
Stage 6 unit/API/harness set: 81 passed
frontend page.test.tsx: 16 passed
```

Old-behavior proof:

| Commit | Evidence |
|---|---|
| `4868784 test: prove c3a multilingual output false passes` | Added behavior tests before implementation. The RED run failed on missing Priority 1 catalog/transcript validation and hardcoded UI catalog exports. |
| `e48b7af docs: add c3a multilingual repair preflight` | Recorded issue-scoped invariant and failure matrix before product/code edits. |

Conclusion: The follow-up behavior tests prove the old bad behavior. The TDD
reviewer reran against pushed commit `c066d26` and confirmed the final committed
state passes behavior-focused coverage.

## Doubt-Driven Review

Status: `PASS`

Disproof attempts checked:

| Risk challenged | Evidence |
|---|---|
| Catalog presence is mistaken for generation support. | Priority 2 tags are cataloged as planned/unsupported and runtime refuses local/demo generation instead of fake success. |
| `COMPLETED` metadata overrules bad text. | Transcript correctness validation is required before completed multilingual result persistence. |
| Browser evidence remains Latin-only. | CP8 now requires representative script-family browser coverage for Devanagari, RTL Arabic/Hebrew, CJK, Hangul, Cyrillic, Latin, and Southeast Asia. |
| Artifact existence overrules artifact content. | Stage 6 metadata artifacts are compared against structured transcript segments and correctness metadata. |
| Arbitrary local-demo input is translated with a generic fixture. | Arbitrary NarraTwin/Jupiter fixture now returns `LOCAL_DEMO_TRANSLATION_UNSUPPORTED`. |
| UI catalog is hardcoded. | UI selector starts empty and requires `/api/v1/languages`; no local full-catalog fallback remains. |
| Browser artifact proof only checks metadata shape. | CP8 evidence now checks decoded metadata and translated-script artifact text against the visible transcript. |

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
output-correctness acceptance: 7 passed
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
output-correctness acceptance: 7 passed
Stage 6 unit/API/harness set: 81 passed
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
