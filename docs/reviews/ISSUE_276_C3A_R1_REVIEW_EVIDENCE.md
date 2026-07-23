# Issue 276 C3A-R1 Review Evidence

Issue: `#276`
Branch: `phase-1-closure-c3a-r1-major-market-multilingual-output-correctness`
Scope: local/mock Checkpoint 3A multilingual output correctness repair.

## Fan-Out Review Status

The earlier final `PASS` evidence for this PR is superseded. Human manual review
after that pass found user-visible semantic failures that the prior
output-correctness fan-out did not catch: Hindi recruiter output could become
engineer output, transliterated or untranslated source terms could survive in the
target text, only one generated line could be translated from a multi-paragraph
approved source, and tests were too willing to trust fixture self-consistency.

The PR is not ready for human approval until the corrected product behavior,
fresh executable gates, manual smoke evidence, and a fresh fan-out review are
recorded below.

The requested sub-agent fan-out had also previously hit usage limits. Obsolete
or completed sessions must be stopped before restarting the required reviewers.

| Requested reviewer | Result | Fallback |
|---|---|---|
| Output-Correctness Reviewer | `BLOCK` on Atlas source receiving NarraTwin target text; later `BLOCK` on Spanish NarraTwin fixture containing untranslated `project knowledge`. | Fixed source-specific Atlas fixtures, complete Spanish fixture text, and added regression assertions. |
| TDD Reviewer | `BLOCK` because original RED evidence failed at import/collection and follow-up behavior tests were uncommitted. | Added behavior-level tests that fail on the prior implementation and recorded this explicitly; final commit carries the follow-up tests. |
| Doubt-Driven Reviewer | `BLOCK` on provider script/transcript divergence, arbitrary NarraTwin pseudo-translation, weak browser artifact comparison, and UI hardcoded catalog fallback. | Added provider/transcript parity validation, arbitrary-fixture refusal, stronger browser artifact parity, and removed frontend catalog fallback. |
| False-Positive Reviewer | `BLOCK` on missing metadata-only/artifact-only response mutations; rerun returned `PASS`. | Added response-level false-pass mutations and required coverage rows. |

Superseding human-review blockers found after the prior final pass:

| Blocker | Corrective evidence required |
|---|---|
| Wrong selected audience in target text, including recruiter translated as engineer. | Exact semantic golden tests for supported controlled scripts and audience-prefix drift tests. |
| Transliteration or untranslated source terms passing because script presence was treated as enough. | Forbidden source-phrase checks and exact target golden strings for every Priority 1 language. |
| One generated source line translated while the approved source supported multiple cited segments. | Stage 4 generated-script coverage tests, heading-only chunk rejection, and Stage 6 multi-segment transcript/artifact assertions. |
| Fixture self-consistency mistaken for independent output correctness. | Test-owned golden strings that fail when implementation fixtures regress to previous bad output. |

Fresh final review status: `BLOCKERS FIXED LOCALLY / PR-HEAD FAN-OUT PENDING`.

| Final reviewer | Latest result | Evidence summary |
|---|---|---|
| Output-Correctness Reviewer | `BLOCK` before latest fixes | Found the coverage matrix had `0` explicit positive rows and the original NarraTwin manual-review document still refused multilingual generation for representative Priority 1 languages. Fixed by adding one positive matrix row per Priority 1 language, original manual-review document fixture coverage for all Priority 1 local/demo translations, a runtime Hindi API regression for that exact document, native Hindi engineering terminology, and Stage 4 small-document expansion to all approved claim chunks within retrieval top-k. |
| TDD Reviewer | `BLOCK` before latest commit | Runtime tests were green, but reviewer correctly blocked PR-level signoff because the branch had uncommitted changes and evidence docs still said final review was pending. Final TDD signoff must be rerun after commit/push. |
| Doubt-Driven Reviewer | `BLOCK` before latest fixes | Found Playwright CP8 recorded `providers.voice` but did not assert it. Fixed by requiring `voice === "mock"` inside `assertBrowserEvidenceContract()` and adding a Playwright self-mutation that non-mock voice evidence throws. |
| False-Positive Reviewer | `PASS` with additive coverage | Added explicit per-field CP8 provider-posture spoofing tests for LLM, translation, voice, avatar, renderer, network egress, real video, and cloned identity; reran output-correctness, Stage 6 unit, checkpoint acceptance, and targeted Ruff successfully. |
| False-Positive Reviewer, rerun on `c276546` | `PASS` | Confirmed 400-row matrix with 25 `missing-target` rows and no remaining false-positive path in that scope. |
| Doubt-Driven Reviewer, rerun on `c276546` | `BLOCK` before latest local fix | Found `make checkpoint3-acceptance` could fail on the default CP8 browser path when stale local review servers occupied fixed ports `8120`/`3120`, even though the representative browser test passed on alternate ports. Fixed locally by assigning isolated loopback CP8 ports in the acceptance runner and adding a regression test. |

Final mandatory Output-Correctness, TDD, Doubt-Driven, and False-Positive review
must be rerun after these fixes are committed and pushed so the review signs off
against the PR head rather than a local working tree.

## Corrective Evidence Snapshot

Status: `LOCAL-GATES-PASS / PR-HEAD-FANOUT-PENDING`

Current corrective tests added after human review:

| Human-found failure | Executable evidence |
|---|---|
| Recruiter translated as engineer or wrong selected audience preserved. | `tests/unit/test_stage6_multilingual.py::test_hindi_local_demo_translation_preserves_selected_product_audience` and exact Priority 1 recruiter golden strings. |
| Transliterated or untranslated source phrases pass as target text. | `tests/unit/test_stage6_multilingual.py::test_priority1_local_demo_golden_translations_preserve_recruiter_meaning` forbidden-source-phrase assertions. |
| One generated source line translated from a multi-paragraph approved source. | `tests/api/test_stage4_slice_api.py::test_grounded_script_generation_preserves_product_audience_surface` and Stage 6 API multi-segment transcript assertions. |
| Heading text becomes a generated claim and citation. | `tests/unit/test_retrieval_and_grounding.py::test_chunking_preserves_headings_as_metadata_without_heading_only_claim_chunks`. |
| Original NarraTwin manual-review document refused or only translated a subset of generated segments. | `tests/unit/test_stage6_multilingual.py::test_priority1_local_demo_supports_original_narratwin_manual_review_document`, `tests/api/test_stage6_multilingual_api.py::test_multilingual_walkthrough_api_translates_original_manual_review_document`, and Stage 4 small-document expansion within retrieval top-k. |
| Coverage matrix omitted positive rows while summary said API output passed. | `tests/acceptance/test_checkpoint3_output_correctness.py` now writes and asserts `positive` rows for every Priority 1 language; latest matrix has 400 rows including 25 positive rows and 25 `missing-target` false-positive rows. |
| Browser evidence accepted non-mock voice provider posture. | `frontend/tests/checkpoint3-real-browser.spec.ts` asserts `providers.voice === "mock"` and self-mutates `voice: "elevenlabs"` to prove the browser contract rejects it. |
| Default CP8 acceptance gate could fail from stale fixed local ports. | `scripts/quality/check_checkpoint3_acceptance.py` allocates isolated loopback CP8 ports per run, `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_allocates_isolated_cp8_ports` proves the subprocess receives them, `make checkpoint3-acceptance` passed twice back-to-back on the default path, and an occupied-port reproduction with listeners on `8120`/`3120` still passed 8/8. |

Commands rerun after the corrective fixes:

```text
uv run pytest tests/unit/test_retrieval_and_grounding.py tests/unit/test_stage6_multilingual.py -q
uv run pytest tests/api/test_stage4_slice_api.py tests/api/test_stage6_multilingual_api.py -q
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py tests/unit/test_checkpoint3_acceptance_gate.py -q
uv run ruff check backend/app/main.py backend/app/rag/chunking.py backend/app/rag/providers.py backend/app/stage4.py backend/app/stage6.py tests/unit/test_retrieval_and_grounding.py tests/unit/test_stage6_multilingual.py tests/api/test_stage4_slice_api.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py
uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py -q
uv run ruff check scripts/quality/check_checkpoint3_acceptance.py tests/unit/test_checkpoint3_acceptance_gate.py
npm --prefix frontend run test -- page.test.tsx
npm --prefix frontend run lint
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
make quality
make checkpoint3-acceptance
make checkpoint3-acceptance
occupied default CP8 ports 8120/3120 + make checkpoint3-acceptance
```

Results:

```text
retrieval + Stage 6 unit tests: 69 passed
Stage 4 + Stage 6 API tests: 52 passed
output-correctness acceptance: 7 passed
targeted Ruff: passed
frontend page.test.tsx: 17 passed
frontend lint: passed
Stage 6 unit + API + output-correctness focused suite: passed
output-correctness + CP8 acceptance-gate focused suite: 53 passed
Priority 1 coverage matrix: 400 rows, 25 positive rows, 25 rows for each required mutation
Checkpoint 3A real-browser smoke: 1 passed
make quality: passed
make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
make checkpoint3-acceptance back-to-back rerun after CP8 port isolation: 8 passed, 0 planned, 0 failed
occupied default CP8 ports 8120/3120 + make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
```

Pending before final review:

```text
make ci after CP8 port isolation fix
commit and push latest local fixes
fresh Output-Correctness, TDD, Doubt-Driven, and False-Positive review fan-out against pushed PR head
manual local-demo smoke review
```

## Manual Rehearsal

The durable human/demo checklist is
`docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md`.
Automated executable evidence remains primary. Human rehearsal should use that
checklist before merge review to spot-check Hindi, Arabic or Egyptian Arabic,
Korean, Japanese or Chinese, Russian or Ukrainian, and German/Spanish/French in
the local demo without making hosted, provider, paid, cloned-identity, real-media,
or production-readiness claims.
