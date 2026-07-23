# Issue 276 C3A-R1 Preflight

## Objective

C3A-R1 repairs Checkpoint 3A for public tracker issue `#249` and child issue
`#276`: local/mock multilingual output correctness must be proved by executable
product behavior, not docs-only planning, metadata-only acceptance,
phrase-replacement pseudo-translation, English fallback, or romanized fallback.

The claim remains local/demo only. It does not authorize hosted deployment,
public URLs, provider setup, real provider calls, paid spend, cloned identity,
real media, public distribution, Checkpoint 3B, Checkpoint 3C, Product Mode 2,
or production-readiness claims.

## Positive Claims

| ID | Claim |
| --- | --- |
| C3A-R1-CATALOG-001 | The language selector consumes a backend-driven catalog; UI labels show English name and native name, support status is explicit, and unsupported local/demo languages cannot generate fake success. |
| C3A-R1-P1-API-001 | Every Priority 1 language has exhaustive local/mock API output-correctness coverage for source English, target transcript, English reference/back-translation, native script/direction, full segment coverage, citations, context refs, claim support IDs, source run ID, evaluation ID, artifact parity, and correctness-gated `COMPLETED`. |
| C3A-R1-STRUCTURE-001 | Successful non-English multilingual runs return structured transcript segments with `segmentId`, `sourceText`, `targetLanguage`, `targetText`, `englishReferenceText`, `citationMarkers`, `citationIndexes`, `contextRefIds`, `claimSupportIds`, `sourceRunId`, and `evaluationId`. |
| C3A-R1-SCRIPT-001 | Native-script languages reject romanized-only output: Hindi uses Devanagari; Arabic/Egyptian Arabic/Persian use Arabic script and RTL; Hebrew uses Hebrew script and RTL; Chinese/Japanese/Korean/Cyrillic/Thai scripts are validated; Latin languages are complete non-English fixture output and not English fallback. |
| C3A-R1-ARTIFACT-001 | Downloadable artifacts contain the same transcript data visible in the API/UI; artifact existence cannot overrule partial/fallback/wrong-script content. |
| C3A-R1-BROWSER-001 | Representative browser E2E drives the real local UI with no success-path interception and inspects visible source English, target text, English reference/back-translation, adjacent citations, RTL/CJK/Hangul/Cyrillic/Devanagari/Thai/Latin rendering, and artifact content. |
| C3A-R1-MATRIX-001 | Tests generate a coverage matrix and checkpoint summary artifact proving every Priority 1 language has positive, fallback, partial, wrong-script, missing-reference, and citation-drift coverage. |

## Non-Goals

- No hosted deployment, public URL, external provider setup, provider SDKs, real
  provider calls, provider outputs, paid spend, real media, cloned identity,
  public distribution, Checkpoint 3B/3C implementation, Product Mode 2, or
  production-readiness claim.
- No support claim for Priority 2 languages unless they meet the same local/demo
  output-correctness bar; this issue catalogs them as planned/unsupported.
- No romanization mode; romanized fallback remains invalid.
- No broad word-substitution translation engine; deterministic local/demo
  fixtures are allowed only for controlled acceptance scripts.

## Source And Repository Facts

Accessed date: 2026-07-23.

| Source | Fact used |
| --- | --- |
| `docs/QUALITY_GATES.md` | `make checkpoint3-acceptance` is the Checkpoint 3A local/mock acceptance harness and currently dispatches CP1 through CP8. |
| `docs/STAGE_ISSUE_PLAN.md` | Checkpoint 3A work remains Phase 1 Closure local/mock evidence and forbids hosted/public/provider/paid/cloned/real-media/production scope. |
| `backend/app/stage6.py` | Existing multilingual output is Stage 6 local/mock behavior and is the correct product boundary to repair for deterministic local/demo translation output. |
| `frontend/src/app/page.tsx` | The UI currently owns the target-language selector and rendered multilingual transcript/artifact surfaces. |
| `tests/acceptance/test_checkpoint3_output_correctness.py` | Current Checkpoint 3A output-correctness coverage focuses on English grounded output and must be extended to exhaustive Priority 1 multilingual transcript correctness. |

## Failure Matrix

| ID | False-pass / failure mode | Required evidence |
| --- | --- | --- |
| C3A-R1-FM-001 | Partial or one-line translation passes. | Mutation fixture removes one segment; API and artifact validation fail before `COMPLETED`. |
| C3A-R1-FM-002 | English fallback passes as translated output. | Per-language fallback mutation fails for every Priority 1 language. |
| C3A-R1-FM-003 | Phrase replacement pseudo-translation passes. | Local/demo fixture equality and full-segment coverage reject broad substitution output. |
| C3A-R1-FM-004 | Romanized native-script language passes. | Native-script validators reject romanized Hindi/Arabic/Hebrew/Persian/CJK/Hangul/Cyrillic/Thai fixtures. |
| C3A-R1-FM-005 | Missing source English text passes. | Structured segment validation fails and artifact parity fails. |
| C3A-R1-FM-006 | Missing English reference/back-translation passes. | Structured segment validation fails and UI/browser assertions fail. |
| C3A-R1-FM-007 | Missing target transcript or wrong target language tag passes. | API contract and artifact parity fail. |
| C3A-R1-FM-008 | Wrong script or wrong direction passes. | Script/direction validator fails by language group. |
| C3A-R1-FM-009 | Citation marker drift passes. | Segment citation marker/index sequence and source cited sentence coverage fail. |
| C3A-R1-FM-010 | Source/eval/context/claim-support binding is missing. | Segment validation rejects missing `sourceRunId`, `evaluationId`, `contextRefIds`, or `claimSupportIds`. |
| C3A-R1-FM-011 | Metadata says `COMPLETED` while visible text is bad. | Completion status is derived from correctness validation; metadata-only success mutation fails. |
| C3A-R1-FM-012 | Artifact exists but content is partial/fallback/wrong-script. | Artifact content is parsed and compared with the transcript, not merely checked for presence. |
| C3A-R1-FM-013 | UI hardcoded language options drift from backend support contract. | Component test mocks backend catalog and asserts rendered options/status use that response. |
| C3A-R1-FM-014 | Unsupported Priority 2 language generates fake success. | API/UI tests assert clear local/demo unsupported refusal and disabled/explained UI state. |
| C3A-R1-FM-015 | Browser E2E proves API metadata but not visible transcript correctness. | Representative browser tests inspect actual visible source, target, reference, citations, layout direction, and downloaded artifact content. |

## Matrix-To-Test Mapping

| Matrix IDs | Evidence target | Old-behavior proof |
| --- | --- | --- |
| C3A-R1-CATALOG-001, C3A-R1-FM-013, C3A-R1-FM-014 | `tests/unit/test_stage6_multilingual.py` and `frontend/src/app/page.test.tsx` catalog tests | RED: current hardcoded language options and unsupported generation behavior fail the new backend-driven catalog assertions. |
| C3A-R1-P1-API-001, C3A-R1-STRUCTURE-001, C3A-R1-SCRIPT-001, C3A-R1-FM-001 through C3A-R1-FM-012 | `tests/acceptance/test_checkpoint3_output_correctness.py` Priority 1 exhaustive API/output-correctness tests | RED: current bad behavior lacks structured bilingual/trilingual transcript segments and cannot satisfy per-language native-script/artifact/binding assertions. |
| C3A-R1-SCRIPT-001, C3A-R1-FM-004, C3A-R1-FM-008 | `tests/unit/test_stage6_multilingual.py` script validation unit tests | RED: romanized native-script fixtures and wrong-script fixtures currently pass or lack a validator. |
| C3A-R1-ARTIFACT-001, C3A-R1-FM-012 | `tests/api/test_stage6_multilingual_api.py` and Checkpoint 3A output-correctness artifact assertions | RED: artifact existence alone is insufficient and current artifacts lack full structured transcript parity. |
| C3A-R1-BROWSER-001, C3A-R1-FM-015 | `frontend/tests/checkpoint3-real-browser.spec.ts` representative visible-output tests | RED: current CP8 browser flow does not inspect complete multilingual visible transcript correctness by script family. |
| C3A-R1-MATRIX-001 | `scripts/quality/check_checkpoint3_acceptance.py` and `tests/unit/test_checkpoint3_acceptance_gate.py` | RED: current harness does not require the multilingual coverage matrix or checkpoint summary artifacts. |

## Priority Languages

Priority 1 supported local/demo tags:
`en`, `hi`, `es`, `de`, `fr`, `pt-BR`, `it`, `nl`, `pl`, `uk`, `ru`,
`zh-Hans`, `zh-Hant`, `ja`, `ko`, `ar`, `arz`, `he`, `fa`, `tr`, `vi`, `id`,
`fil`, `th`, `ms`.

Priority 2 cataloged unsupported/planned tags:
`bn`, `ta`, `te`, `kn`, `mr`, `gu`, `ml`, `ur`, `pa`.

## Review Prompt Set

- Output-Correctness Reviewer: execute runtime API and browser flows; inspect
  actual source English, target-language text, English reference, visible UI,
  artifacts, full-script coverage, native script correctness, citations, and
  source/eval/context/claim-support binding.
- TDD Reviewer: verify RED tests existed and failed before implementation; check
  behavior focus across positive, negative, false-positive, API, artifact,
  rendering, and browser coverage.
- Doubt-Driven Reviewer: try to disprove the checkpoint through catalog support
  ambiguity, partial transcripts, script/direction errors, metadata-only success,
  artifact-only success, and representative browser gaps.
- False-Positive Reviewer: mutate metadata-only success, artifact-only success,
  partial text, fallback text, wrong-script text, missing source/reference text,
  missing binding, and citation drift; confirm acceptance fails.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| test-driven-development | Invoked | RED tests are required before implementation and must catch current weak Checkpoint 3A behavior. |
| frontend-ui-engineering | Invoked | UI selector, support status, visible transcript, RTL/script rendering, and artifact visibility are user-facing. |
| git-workflow-and-versioning | Invoked | Issue `#276`, dedicated branch, and preflight-before-code workflow preserve repository governance. |
| code-review-and-quality | Invoked | Fan-out review will be recorded as PR evidence before completion. |
| doubt-driven-development | Invoked | False-pass matrix and mutation fixtures attack ways bad multilingual output could still pass. |
| source-driven-development | Considered | No external provider/platform semantics are introduced; repository facts and executable tests are the source of truth for local/mock behavior. |
| security-and-hardening | Considered | No new provider egress or secrets are introduced; untrusted uploaded content and generated output remain bounded by existing local/mock paths. |
| shipping-and-launch | Rejected | Hosted/public/production launch remains forbidden. |
| plugin/skill creation | Rejected | Existing repo docs and skills cover the work; no custom skill/plugin is needed. |

## Stop Rule

Stop and open or update a new issue if the repair requires hosted deployment,
public URLs, provider setup, provider SDKs, real provider calls, paid spend,
real provider outputs, cloned identity, real media, Product Mode 2, Checkpoint
3B/3C implementation, Docker/runtime/dependency changes, secrets, private media,
or production-readiness claims.

If review finds a new false-pass class after implementation, update this matrix
and add a failing test before patching code.
