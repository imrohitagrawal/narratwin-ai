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

The PR is ready for human local-demo review after the corrected product
behavior, fresh executable gates, remote checks, and the final fan-out review
recorded below. Automated executable evidence remains primary; human review is
the requested final manual approval input.

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
| Downloadable `translatedScript` artifact contained only target text while metadata/UI contained the full transcript. | Runtime script artifact rendering and tests must require source English, target text, English reference, citations, context refs, claim-support ids, source run id, and evaluation id for every segment. |
| Hindi accepted transliterated English terms such as `जनरेट` and `वॉकथ्रू` in a completed transcript. | Hindi golden output and transcript validation must reject transliterated source-domain terms and require fully translated Hindi wording. |

Fresh final review status: `FINAL FAN-OUT PASS ON 041960a / HUMAN REVIEW REQUESTED`.

The final review restarted after pushed head `100c6059795e3d50e2c95f15ef6d203413de5bd6`
was blocked for CP8 default-path nondeterminism. Commit
`609961232e93c0a4efec32704b967dcc2112cb80` fixed that blocker by removing only
dead Next dev locks before the CP8 browser probe starts. A later final
Doubt-Driven sub-agent review on `d87a66e3e43a61ae3f404d3733f9de64c26cb7bc`
found that Russian and Ukrainian successful outputs could still contain the raw
English source-domain term `walkthrough`. Commit
`e8811841d2aa8786d78f4222bbd22b63aeb3d89b` fixes that blocker. In a later
main-session rerun, the sub-agent tool was not exposed, so the same
Doubt-Driven prompt was executed as an independent fallback review against
`e8811841`; it passed with the executable evidence recorded below. Full
current-head sub-agent fan-out then found that the downloadable
`translatedScript` markdown artifact was target-only instead of the same
trilingual transcript data exposed in the UI and metadata. That blocker is
being fixed locally and must be rerun through gates and final fan-out after the
next pushed PR head. Local gates for this fix now pass: `make quality`,
`make checkpoint3-acceptance`, `make ci`, focused Stage 6/API/output-correctness
tests, and the targeted CP8 browser smoke test. A later Output-Correctness
review on `aa9ba02` confirmed the artifact blocker was fixed but found Hindi
still accepted transliterated source-domain terms `जनरेट` and `वॉकथ्रू` in the
fourth transcript segment. That blocker is fixed locally by replacing the Hindi
fixture with fully translated wording and adding Hindi transliteration rejection
to transcript correctness validation. Commit
`c20c6c64ff73abd4c198445d8fa4988d2f004acd` passed local gates and its
mandatory fan-out, but that evidence was superseded by human local-demo review
finding that the exact NarraTwin four-line document needed broader all-language
golden coverage. Commit `a529ca8` fixed the Hindi/manual-review golden set but
was blocked by TDD and Doubt-Driven review for NarraTwin partial-substring
acceptance and audience-prefix leakage. Commit `a0e508e` fixed those issues but
was blocked by Doubt-Driven review for Atlas/Helio substring acceptance and an
invented Atlas engineer audience. Commit `29b830a` fixed Atlas all-three-segment
coverage, exact fixture matching, no invented Atlas audience, and mixed-script
contamination, but was blocked for unknown `For investors` audience prefixes
being silently dropped. Commit `09af5af` fixed unknown-audience refusal, but was
blocked by TDD review for duplicated Spanish Helio `Para reclutadores` visible
output. Commit `041960ae2bc69e6a2b6d42eaad4db3fc150e534b` fixed the Helio
duplicate-prefix gap and passed local gates, GitHub checks, and the final
mandatory Output-Correctness, TDD, Doubt-Driven, and False-Positive fan-out with
no findings. Human local-demo review remains the final manual approval input.

| Final reviewer | Latest result | Evidence summary |
|---|---|---|
| Output-Correctness Reviewer | `BLOCK` before latest fixes | Found the coverage matrix had `0` explicit positive rows and the original NarraTwin manual-review document still refused multilingual generation for representative Priority 1 languages. Fixed by adding one positive matrix row per Priority 1 language, original manual-review document fixture coverage for all Priority 1 local/demo translations, a runtime Hindi API regression for that exact document, native Hindi engineering terminology, and Stage 4 small-document expansion to all approved claim chunks within retrieval top-k. |
| TDD Reviewer | `BLOCK` before latest commit | Runtime tests were green, but reviewer correctly blocked PR-level signoff because the branch had uncommitted changes and evidence docs still said final review was pending. Final TDD signoff must be rerun after commit/push. |
| Doubt-Driven Reviewer | `BLOCK` before latest fixes | Found Playwright CP8 recorded `providers.voice` but did not assert it. Fixed by requiring `voice === "mock"` inside `assertBrowserEvidenceContract()` and adding a Playwright self-mutation that non-mock voice evidence throws. |
| False-Positive Reviewer | `PASS` with additive coverage | Added explicit per-field CP8 provider-posture spoofing tests for LLM, translation, voice, avatar, renderer, network egress, real video, and cloned identity; reran output-correctness, Stage 6 unit, checkpoint acceptance, and targeted Ruff successfully. |
| False-Positive Reviewer, rerun on `c276546` | `PASS` | Confirmed 400-row matrix with 25 `missing-target` rows and no remaining false-positive path in that scope. |
| Doubt-Driven Reviewer, rerun on `c276546` | `BLOCK` before latest local fix | Found `make checkpoint3-acceptance` could fail on the default CP8 browser path when stale local review servers occupied fixed ports `8120`/`3120`, even though the representative browser test passed on alternate ports. Fixed locally by assigning isolated loopback CP8 ports in the acceptance runner and adding a regression test. |
| Doubt-Driven independent fallback, rerun on `100c605` then `6099612` | `PASS` after fix | Reproduced the `100c605` default CP8 blocker, added stale Next dev lock cleanup with live-lock preservation tests, pushed `6099612`, and reran `make checkpoint3-acceptance` successfully at the pushed head. |
| Output-Correctness independent fallback, rerun on `6099612` | `PASS` | Reran exhaustive Priority 1 output-correctness acceptance, Stage 6 unit/API multilingual tests, browser probe, and matrix inspection. Verified 25 Priority 1 positive rows and 25 rows for every false-positive mutation including `missing-target`. |
| TDD independent fallback, rerun on `6099612` | `PASS` | Verified the CP8 failure has regression tests for stale dead-PID Next locks and live-lock preservation, and the existing behavior tests remain green for API/output correctness, artifact parity, browser contract, and provider posture spoofing. |
| False-Positive independent fallback, rerun on `6099612` | `PASS` | Reran output-correctness and acceptance-gate tests after the CP8 harness change. No metadata-only, artifact-only, fallback, partial, wrong-script, missing-source/reference/target/binding, citation-drift, glossary leakage, or provider-posture false-pass path was found. |
| Doubt-Driven Reviewer, rerun on `d87a66e` | `BLOCK` before latest local fix | Found Russian and Ukrainian deterministic fixture outputs leaked standalone English `walkthrough` inside otherwise Cyrillic successful target text. Fixed locally by replacing those target strings, removing the same source term from German, Dutch, and Filipino fixture strings, adding standalone `walkthrough` to forbidden source-term checks, extending the original manual-review document test, and adding runtime validation that rejects untranslated source-domain terms. |
| Doubt-Driven independent fallback, rerun on `e8811841` | `PASS` | Sub-agent tool was not exposed in the main session, so the final Doubt-Driven prompt was executed as fallback. Reran `make checkpoint3-acceptance`, focused Stage 6/API/output-correctness/language-quality/acceptance-gate tests, `git diff --check origin/main...HEAD`, matrix/summary inspection, CP8 port cleanup check, and a direct FastAPI runtime probe for the original NarraTwin manual-review document across Hindi, Arabic, Hebrew, Japanese, Korean, Russian, Ukrainian, French, and Thai. The probe verified four cited segments, source English, target text, English reference, native script, no standalone `walkthrough` leakage, citations `[1]` through `[4]`, source/eval/context/claim-support binding, artifact parity, mock providers, and Bengali unsupported refusal. No remaining doubt-driven finding was found in this fallback pass. |
| Output-Correctness Reviewer, rerun on `e8811841` | `BLOCK` before latest local fix | Executed FastAPI runtime multilingual generation and decoded artifacts. The API and metadata had four Hindi transcript segments, but `artifacts.translatedScript.contentBase64` decoded to only flat target-language text. It omitted per-segment source English, English reference/back-translation, citation/context/claim-support bindings, source run id, and evaluation id. Fixed locally by rendering the translated-script artifact as a trilingual transcript and hardening API, acceptance, media-artifact, and browser tests to reject target-only script artifacts. |
| False-Positive Reviewer, rerun on `aa9ba02` | `PASS` | Confirmed 400-row coverage matrix, target-only translated-script artifact rejection, and no false-positive path for metadata-only, artifact-only, partial, fallback, wrong-script, missing source/reference/target, citation drift, missing binding, and glossary leakage. |
| Output-Correctness Reviewer, rerun on `aa9ba02` | `BLOCK` before latest local fix | Confirmed full trilingual artifact parity was fixed across all Priority 1 languages, but found Hindi still accepted transliterated English source-domain terms `जनरेट` and `वॉकथ्रू` in the completed output for “Every generated walkthrough claim...”. Fixed locally by updating the Hindi golden fixture to “प्रत्येक उत्पन्न चरण-दर-चरण प्रस्तुति संबंधी दावे...” and adding runtime Hindi transliteration rejection. |
| TDD Reviewer, rerun on `c20c6c6` | `PASS` | Confirmed branch and origin both pointed to `c20c6c64ff73abd4c198445d8fa4988d2f004acd`; focused multilingual/API/output-correctness/media suites passed with 117 tests, `make checkpoint3-acceptance` passed 8 probes, direct probe confirmed old Hindi `जनरेट`/`वॉकथ्रू` output is rejected with `TRANSCRIPT_CORRECTNESS_FAILED`, and coverage matrix retained 25 Priority 1 languages and 400 rows. |
| False-Positive Reviewer, rerun on `c20c6c6` | `PASS` | Confirmed branch and origin both pointed to `c20c6c64ff73abd4c198445d8fa4988d2f004acd`; focused suites passed, Ruff/ESLint passed, `make checkpoint3-acceptance` passed, direct runtime Hindi API mutation probe rejected metadata-only success, artifact-only success, partial text, fallback, wrong script, missing source/reference/target, citation drift, missing binding, target-only `translatedScript`, and Hindi transliterated `जनरेट`/`वॉकथ्रू`; coverage matrix retained all required rows. |
| Doubt-Driven Reviewer, rerun on `c20c6c6` | `PASS` | Focused multilingual/API/media suites passed with 118 tests, `make checkpoint3-acceptance` passed 8 probes, targeted Playwright UI test passed, runtime API probe across all 25 Priority 1 languages verified 4-segment trilingual transcript, artifact parity, preserved bindings, Bengali unsupported refusal, Hindi with no `जनरेट`, `वॉकथ्रू`, `इंजीनियरों`, or English fallback, and browser evidence for Hindi, Arabic, Hebrew, Japanese, Korean, Russian, French, and Thai showed visible transcript/artifact parity. |
| Output-Correctness Reviewer, verdict retry on `c20c6c6` | `PASS` | Reviewed exact pushed head `c20c6c64ff73abd4c198445d8fa4988d2f004acd`; focused suites passed with 118 tests, direct runtime API probe for the exact user knowledge document produced 4 cited segments for all 25 Priority 1 languages, Hindi contained no `जनरेट`, `वॉकथ्रू`, or `इंजीनियरों`, translatedScript decoded as full trilingual transcript rather than target-only, per-segment source/target/reference/citation/context/claim/eval/source-run bindings were present, Bengali refused with `LOCAL_DEMO_LANGUAGE_UNSUPPORTED`, `make checkpoint3-acceptance` passed, targeted Playwright passed, and browser evidence confirmed representative visible transcript/artifact parity. |
| Doubt-Driven Reviewer, rerun on `a529ca8` | `BLOCK` before latest fixes | Found NarraTwin partial-substring acceptance could still return `COMPLETED` while dropping a new arbitrary source clause, and found non-Hindi audience-prefix leakage such as German/Dutch/Filipino English audience terms. Fixed by exact source-body fixture matching and all-Priority-1 audience-prefix tests. |
| Doubt-Driven Reviewer, rerun on `a0e508e` | `BLOCK` before latest fixes | Found Atlas/Helio fixtures still matched by substring and Atlas outputs invented an engineer audience when the source did not say `For engineers`. Fixed by exact Atlas/Helio source-body matching, all-three-segment Atlas golden translations, no-invented-audience tests, and mixed-script contamination checks. |
| Doubt-Driven Reviewer, rerun on `29b830a` | `BLOCK` before latest fixes | Found unknown source prefixes such as `For investors, ...` could be stripped and the base translation would still return `COMPLETED`, dropping visible source meaning. Fixed by refusing unknown audience prefixes for all non-English Priority 1 languages. |
| TDD Reviewer, rerun on `09af5af` | `BLOCK` before latest fix | Found Spanish Helio positive output duplicated `Para reclutadores` and the test only checked prefix presence. Fixed by making the Spanish Helio fixture body prefix-free and asserting the exact visible output with `Para reclutadores` appearing once. |
| Output-Correctness Reviewer, rerun on `041960a` | `PASS` | Reviewed exact pushed head `041960ae2bc69e6a2b6d42eaad4db3fc150e534b`; focused regression tests, 19 acceptance tests, custom runtime probes, `make checkpoint3-acceptance`, and browser evidence all passed. Verified 25 Priority 1 manual-review exact translations, 168 known audience prefixes, 24 unknown-audience refusals, NarraTwin/Atlas partial refusals, Atlas API all 25 languages with 3 segments and artifact parity, no invented Atlas engineer audience, Helio Spanish exactly one `Para reclutadores`, 23 Helio non-Spanish refusals, and 9 Priority 2 refusals. |
| TDD Reviewer, rerun on `041960a` | `PASS` | Verified behavior-focused tests and RED proof against prior bad heads: manual-review all-language exactness failed on `c20c6c6`, NarraTwin partial substring failed on `a529ca8`, Atlas partial and audience-prefixed partial failed on `a0e508e`, unknown audience refusal failed on `29b830a`, and Helio duplicate-prefix exact-output failed on `09af5af`. Current head passed Ruff, 305 Stage 6 unit tests, 37 API/acceptance tests, 19 frontend tests, targeted real-browser smoke, `make checkpoint3-acceptance`, and `make quality`. |
| Doubt-Driven Reviewer, rerun on `041960a` | `PASS` | Could not find a remaining false pass. Runtime adversarial probes showed `0` successes for `For investors`, NarraTwin extra-claim substrings, Atlas extra-claim substrings, Atlas audience-prefixed extra-claim substrings, and Helio extra-claim substrings; exact Atlas succeeded for non-English Priority 1 languages; full-document exact golden probe produced 4 transcript segments for all 25 Priority 1 languages with artifact parity and bindings; Priority 2 languages refused; `make checkpoint3-acceptance` passed including real-browser E2E. |
| False-Positive Reviewer, rerun on `041960a` | `PASS` | Confirmed 19 acceptance tests, 97 focused adversarial unit tests, exhaustive Priority 1 output-correctness acceptance, direct mutation probes, and `make checkpoint3-acceptance` passed. Mutations for metadata-only success, artifact-only success, partial text, fallback, wrong script, missing source/reference/target, citation drift, missing bindings, unknown audience, duplicated Helio prefix, and mixed-script contamination were rejected with no unexpected passes. |

The mandatory Output-Correctness, TDD, Doubt-Driven, and False-Positive reviews
passed against pushed head `041960ae2bc69e6a2b6d42eaad4db3fc150e534b` with no
findings. Human local-demo review is requested as the final manual approval
input.

## Corrective Evidence Snapshot

Status: `FINAL FAN-OUT PASS ON 041960a / HUMAN REVIEW REQUESTED`

Current corrective tests added after human review:

| Human-found failure | Executable evidence |
|---|---|
| Recruiter translated as engineer or wrong selected audience preserved. | `tests/unit/test_stage6_multilingual.py::test_hindi_local_demo_translation_preserves_selected_product_audience` and exact Priority 1 recruiter golden strings. |
| Transliterated or untranslated source phrases pass as target text. | `tests/unit/test_stage6_multilingual.py::test_priority1_local_demo_golden_translations_preserve_recruiter_meaning` forbidden-source-phrase assertions. |
| Standalone source-domain term `walkthrough` leaks in successful Cyrillic output. | `tests/unit/test_stage6_multilingual.py::test_cyrillic_transcript_validation_rejects_untranslated_walkthrough_term`, the original manual-review document test's forbidden-term assertions, and runtime `validate_target_script` source-domain term rejection. |
| One generated source line translated from a multi-paragraph approved source. | `tests/api/test_stage4_slice_api.py::test_grounded_script_generation_preserves_product_audience_surface` and Stage 6 API multi-segment transcript assertions. |
| Heading text becomes a generated claim and citation. | `tests/unit/test_retrieval_and_grounding.py::test_chunking_preserves_headings_as_metadata_without_heading_only_claim_chunks`. |
| Original NarraTwin manual-review document refused or only translated a subset of generated segments. | `tests/unit/test_stage6_multilingual.py::test_priority1_local_demo_supports_original_narratwin_manual_review_document`, `tests/api/test_stage6_multilingual_api.py::test_multilingual_walkthrough_api_translates_original_manual_review_document`, and Stage 4 small-document expansion within retrieval top-k. |
| Known audience prefixes leaked English or mapped to the wrong audience. | `tests/unit/test_stage6_multilingual.py::test_local_demo_translation_preserves_selected_audience_prefixes_without_english_leakage` checks all supported local/demo audiences across all Priority 1 languages. |
| Unknown audience prefixes were silently dropped while returning `COMPLETED`. | `tests/unit/test_stage6_multilingual.py::test_local_demo_translation_refuses_unknown_audience_prefix_instead_of_dropping_it`; the final fan-out verified `For investors, ...` refused for all 24 non-English Priority 1 languages. |
| Atlas acceptance translated one line or invented an engineer audience. | `tests/unit/test_stage6_multilingual.py::test_atlas_output_fixture_refuses_substring_with_extra_source_claim`, `test_atlas_output_fixture_refuses_audience_prefixed_substring_with_extra_source_claim`, `test_atlas_output_fixture_does_not_invent_engineer_audience`, `test_atlas_output_fixture_preserves_explicit_engineer_audience`, and exhaustive Priority 1 API output-correctness acceptance. |
| Latin-script output could contain unexpected foreign-script contamination. | `tests/unit/test_stage6_multilingual.py::test_atlas_output_fixture_latin_languages_have_no_foreign_script_contamination`. |
| Spanish Helio output duplicated the audience prefix. | `tests/unit/test_stage6_multilingual.py::test_helio_media_fixture_preserves_explicit_recruiter_audience` asserts the exact visible Spanish sentence and that `Para reclutadores` appears once. |
| Coverage matrix omitted positive rows while summary said API output passed. | `tests/acceptance/test_checkpoint3_output_correctness.py` now writes and asserts `positive` rows for every Priority 1 language; latest matrix has 400 rows including 25 positive rows and 25 `missing-target` false-positive rows. |
| Browser evidence accepted non-mock voice provider posture. | `frontend/tests/checkpoint3-real-browser.spec.ts` asserts `providers.voice === "mock"` and self-mutates `voice: "elevenlabs"` to prove the browser contract rejects it. |
| Default CP8 acceptance gate could fail from stale fixed local ports or dead Next dev locks. | `scripts/quality/check_checkpoint3_acceptance.py` allocates isolated loopback CP8 ports per run and removes only dead Next dev locks, while preserving live locks; `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_allocates_isolated_cp8_ports`, `test_checkpoint3_acceptance_removes_stale_next_dev_lock`, and `test_checkpoint3_acceptance_keeps_live_next_dev_lock` prove the harness behavior; `make checkpoint3-acceptance` passes on the default path at pushed head `6099612`. |

Commands rerun after the corrective fixes:

```text
uv run pytest tests/unit/test_retrieval_and_grounding.py tests/unit/test_stage6_multilingual.py -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/api/test_stage4_slice_api.py tests/api/test_stage6_multilingual_api.py -q
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py tests/unit/test_checkpoint3_acceptance_gate.py -q
uv run ruff check backend/app/main.py backend/app/rag/chunking.py backend/app/rag/providers.py backend/app/stage4.py backend/app/stage6.py tests/unit/test_retrieval_and_grounding.py tests/unit/test_stage6_multilingual.py tests/api/test_stage4_slice_api.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py
uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py -q
uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_removes_stale_next_dev_lock tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_keeps_live_next_dev_lock tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_allocates_isolated_cp8_ports -q
uv run ruff check scripts/quality/check_checkpoint3_acceptance.py tests/unit/test_checkpoint3_acceptance_gate.py
npm --prefix frontend run test -- page.test.tsx
npm --prefix frontend run lint
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
make quality
make checkpoint3-acceptance
make checkpoint3-acceptance
occupied default CP8 ports 8120/3120 + make checkpoint3-acceptance
make ci
uv run pytest tests/unit/test_stage6_multilingual.py::test_local_demo_translation_refuses_unknown_audience_prefix_instead_of_dropping_it tests/unit/test_stage6_multilingual.py::test_helio_media_fixture_preserves_explicit_recruiter_audience -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py tests/acceptance/test_checkpoint3_language_quality.py tests/acceptance/test_checkpoint3_media_artifacts.py -q
uv run ruff check backend/app/stage6.py tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py
make checkpoint3-acceptance
make quality
make ci
```

Results:

```text
retrieval + Stage 6 unit tests: 69 passed
Stage 6 unit + API + output-correctness after source-domain-term fix: passed
Stage 4 + Stage 6 API tests: 52 passed
output-correctness acceptance: 7 passed
targeted Ruff: passed
frontend page.test.tsx: 17 passed
frontend lint: passed
Stage 6 unit + API + output-correctness focused suite: passed
output-correctness + CP8 acceptance-gate focused suite: 53 passed
CP8 stale-lock focused unit tests: 3 passed
Priority 1 coverage matrix: 400 rows, 25 positive rows, 25 rows for each required mutation
Checkpoint 3A real-browser smoke: 1 passed
make quality: passed
make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
make checkpoint3-acceptance back-to-back rerun after CP8 port isolation: 8 passed, 0 planned, 0 failed
occupied default CP8 ports 8120/3120 + make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
latest focused unknown-audience + Helio exact-output tests: passed
latest Stage 6 unit/API/output-correctness/language-quality/media-artifact suite: passed
latest targeted Ruff: passed
latest make checkpoint3-acceptance: 8 passed, 0 planned, 0 failed
latest make quality: passed
latest make ci: passed
GitHub checks on pushed head 041960a: all passed
final mandatory fan-out on pushed head 041960a: Output-Correctness PASS, TDD PASS, Doubt-Driven PASS, False-Positive PASS
```

Pending before merge approval:

```text
manual local-demo smoke review by a human reviewer
```

## Manual Rehearsal

The durable human/demo checklist is
`docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md`.
Automated executable evidence remains primary. Human rehearsal should use that
checklist before merge review to spot-check Hindi, Arabic or Egyptian Arabic,
Korean, Japanese or Chinese, Russian or Ukrainian, and German/Spanish/French in
the local demo without making hosted, provider, paid, cloned-identity, real-media,
or production-readiness claims.
