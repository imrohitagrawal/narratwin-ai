# Issue 280 Semantic Gap Memory

Date: 2026-07-25

Scope: Post-merge intended-vs-implemented review of Issue `#280` / PR E after
real browser UI audits found a gap between the closure plan and browser-visible
behavior.

## Executive Memory

Issue `#280` / PR E was marked satisfied by the repository matrix/status, but
post-merge browser execution showed the local/demo multilingual outcome did not
meet the body-level translation requirement.

The structural local/mock path works: bounded synthetic markdown reaches the UI,
grounded English script generation works, depth and audience settings change the
English script, citations/context refs/claim supports/evaluation metadata are
preserved, artifacts are downloadable, provider posture remains local/mock, and
safe refusal states are browser-visible.

The semantic user-visible multilingual outcome does not work: all 24
non-English supported languages fail full source-sentence conversion in the
browser-visible target transcript.

## Observed Evidence

Manual deep browser audit:

- `reports/checkpoint3-issue280/deep-browser-ui-e2e-report-2026-07-25T06-27-41-892Z.json`
- Status: `STRUCTURAL_UI_PASS_TRANSLATION_QUALITY_FAIL`
- Desktop language count: 25
- Mobile language count: 25
- Non-English full-sentence translation failures: 24
- Console/page errors: 0
- Structural failures: 0

Representative failure classes:

- `hi`, `es`, `fr`, `ja`, `ar`, and `he` render localized mock metadata
  sentences such as source segment/protected term evidence rather than
  translating the actual source clause.
- `de`, `pt-BR`, `it`, `nl`, `pl`, `uk`, `ru`, `zh-Hans`, `zh-Hant`, `ko`,
  `arz`, `fa`, `tr`, `vi`, `id`, `fil`, `th`, and `ms` render English default
  fallback text beginning with `Local mock conversion (...)`.

Implementation evidence:

- `backend/app/issue280.py` uses `_LOCAL_TRANSLATION_TEMPLATES`.
- Only six non-English target languages have localized templates.
- The fallback template is English: `Local mock conversion ({native_name},
  {english_name}): source segment {section}; protected term {glossary}{citation}`.
- `_translate_fact()` formats section/glossary/citation metadata; it does not
  translate the source fact body.

Test weakness evidence:

- `tests/acceptance/test_issue280_pr_e_closure.py` checks that a few fixture
  source snippets are absent, but it does not reject generic English fallback
  phrases such as `Local mock conversion`, `source segment`, or `protected term`.
- The test also does not assert source-clause semantic preservation in the target
  language, so metadata-only success can pass.

## Requirements That Were Not Actually Met

These rows were marked pass in the matrix but are not proven by observed
browser-visible behavior:

- `R280-S6-001`: requires body-level translation, no English fallback except
  protected terms, no romanized fallback where native script is required, and no
  partial/metadata/artifact-only success.
- `R280-QUALITY-001`: requires rejecting untranslated English fallback,
  partial success, metadata-only success, artifact-only success, and UI/export
  mismatch.
- `R280-CONVERSION-001`: structurally passes the chain but does not satisfy the
  target transcript semantic conversion implied by the closure objective.
- `R280-OUTPUT-CORRECTNESS-001`: the verifier exists and executes, but its
  assertions are insufficient because it accepts metadata-correct output as
  success.

## Why This Recurred

The failure was not caused by lack of user instruction. The user repeatedly
asked for output correctness and real execution, including a non-read-only
verifier that proves the user-visible path.

The process failed because:

1. Tests optimized for response shape, metadata parity, and artifact/checksum
   presence instead of browser-visible semantic output.
2. The requirement matrix treated a passing command as proof even when the
   command did not prove the row's strongest claim.
3. The PR E closure language overclaimed deterministic 25-language conversion
   while the implementation only provided deterministic mock metadata/fallback
   templates.
4. The output-correctness verifier did not classify evidence as structural vs.
   semantic.
5. No mandatory independent intended-vs-implemented audit blocked the final
   closure status before merge.

## Required Quality-Gate Improvements

Add a semantic output-correctness layer before any future matrix row can be
marked satisfied:

1. Matrix row status taxonomy
   - Add statuses such as `STRUCTURAL_PASS`, `SEMANTIC_PASS`, `NOT_PROVEN`,
     `FAILED`, and `RE_SCOPED`.
   - A row whose requirement is user-visible output quality cannot close on
     `STRUCTURAL_PASS`.

2. Semantic verifier gate
   - Add a dedicated verifier script that opens the browser, submits arbitrary
     bounded synthetic markdown, expands the full transcript, extracts rendered
     target text, and classifies every language.
   - The verifier must fail on target text containing generic metadata/fallback
     markers such as `Local mock conversion`, `source segment`, `protected term`,
     or their localized equivalents when full sentence conversion is claimed.
   - The verifier must fail if the target text omits the source clause meaning
     while preserving only section/glossary/citation metadata.

3. Test fixture design
   - Use per-run arbitrary synthetic source facts with unique semantic clauses.
   - Assert that each semantic clause is represented in target output by a
     deterministic expected phrasebook or by an explicit honest refusal.
   - For local/mock mode, either implement deterministic per-language phrasebook
     conversion for bounded clauses or downgrade the claim to mock metadata only.

4. Output-correctness verifier authority
   - `make issue280-output-correctness` should fail unless the stronger semantic
     verifier passes.
   - The verifier report must contain row-level statuses, not one global
     `PASSED` status.

5. PR and docs overclaim guardrail
   - `scripts/guardrails_check.py` and/or
     `scripts/quality/check_phase1_closure_docs.py` should reject docs/status
     claims such as `25-language conversion`, `body-level translation`, or
     `output correctness` unless a matching semantic verifier report exists and
     shows `SEMANTIC_PASS`.

6. Independent closure audit
   - Before closing any final slice, run an intended-vs-implemented audit that
     compares the exact row text against browser-observed output and code
     enforcement points.
   - This audit must not accept docs, screenshots, metadata, or green CI as
     proof of semantic behavior by themselves.

7. Mandatory fan-out review shape
   - Every final closure PR must include at least one independent
     intended-vs-implemented review pass.
   - The intended-vs-implemented pass must lead with a direct verdict:
     `MEETS_REQUIREMENTS`, `STRUCTURAL_ONLY`, `SEMANTIC_GAP`, or `FAILED`.
   - The pass must map documented intent to implementation evidence and
     browser-observed output. It must name the exact requirement rows that are
     satisfied, not proven, failed, or re-scoped.
   - The implementation agent cannot be the sole authority marking its own PR
     complete. A separate adversarial verifier/reviewer must have closure
     authority for output-correctness claims.

8. No mock metadata as conversion evidence
   - If the requirement says deterministic 25-language conversion of arbitrary
     source clauses, target text must convert the source clause meaning.
   - Target text that says `Local mock conversion`, `source segment`,
     `protected term`, translated equivalents of those metadata labels, or any
     heading/glossary/citation-only metadata sentence is a failure.
   - Mock provider posture is allowed. Mock metadata-only target text is not
     allowed when the row claims multilingual conversion.
   - The only acceptable outcomes for unsupported semantic conversion are:
     implement deterministic bounded conversion for the claimed languages, or
     honestly refuse and keep the semantic conversion row open.

## Suggested Implementation Locations

- `scripts/quality/verify_issue280_output_correctness.py`
  - Wire in a stricter semantic browser verifier and fail on semantic gaps.

- `frontend/tests/issue280-ui-browser.spec.ts`
  - Expand browser assertions from five-language structural checks to all
    supported languages or to a batched all-language semantic matrix.

- `tests/acceptance/test_issue280_pr_e_closure.py`
  - Add semantic false-pass tests for English fallback, metadata-only target
    text, missing source clauses, and per-language phrasebook expectations.

- `reports/checkpoint3-issue280/requirement-matrix.json`
  - Replace binary pass claims with structural/semantic row statuses.

- `scripts/quality/check_phase1_closure_docs.py`
  - Enforce that matrix rows with semantic requirements cannot be marked pass
    without a semantic verifier report.

- `scripts/guardrails_check.py`
  - Add overclaim detection for docs/status/PR body language that asserts
    multilingual conversion without semantic verifier evidence.

- `.github/pull_request_template.md`
  - Require a dedicated "Semantic user-visible output evidence" section for
    output-correctness PRs.

- `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`
  - Add this memory as a reusable lesson: a green gate is not evidence unless it
    proves the strongest user-visible claim in the requirement row.

## Corrective Resolution In Issue #298

Issue `#298` applies the immediate corrective pattern for the issue `#280`
semantic gap:

- Replace metadata/mock target transcript templates with deterministic local
  semantic clause conversion for bounded public-safe synthetic project clauses
  across all 25 supported local-demo languages.
- Fail closed with `ISSUE280_TRANSLATION_REFUSED` when a source clause is
  outside the supported deterministic local semantic set instead of falling back
  to an English mock template.
- Add backend acceptance coverage that submits new bounded synthetic project
  markdown and rejects metadata-only target text, English source-clause leakage,
  missing citation markers, and broken language-specific semantic markers.
- Expand browser-visible Playwright coverage to all 25 supported local-demo
  languages, with explicit rejection of `Local mock conversion`,
  `source segment`, `protected term`, localized metadata-template markers, and
  untranslated source clauses.
- Strengthen `make issue280-output-correctness` so its report asserts semantic
  clause conversion, all-25 language verification, metadata-only rejection, and
  English-fallback rejection in addition to network/artifact/citation parity.
- Update the requirement matrix to distinguish `SEMANTIC_EXECUTABLE_PASS` from
  structural executable pass for the affected issue `#280` rows.
- Update status/traceability/quality-gate docs so issue `#280` is not treated as
  semantically satisfied until issue `#298` is reviewed and merged, or the
  requirement is explicitly re-scoped.

This resolution remains a deterministic local-demo correction, not a provider
quality or arbitrary human-grade translation claim.

## Intended-vs-Implemented Review Pattern

Future final-slice PRs should include a review section with this minimum shape:

1. Documented intent
   - Cite the exact plan, matrix row, PR preflight, PR body, or status claim.

2. Implementation evidence
   - Cite the code path that actually enforces or produces the behavior.

3. Browser-observed evidence
   - Cite the report/screenshot/network evidence from a real browser run.

4. Verdict by row
   - `SEMANTIC_PASS`: user-visible behavior proves the strongest row claim.
   - `STRUCTURAL_PASS`: plumbing/metadata/artifacts work but user-visible
     semantic behavior is not proven.
   - `NOT_PROVEN`: the gate did not test the claim.
   - `FAILED`: browser-observed behavior contradicts the requirement.
   - `RE_SCOPED`: the row was explicitly narrowed and docs/matrix/status were
     updated before closure.

5. Closure decision
   - A row cannot close on `STRUCTURAL_PASS`.
   - A final closure PR cannot close the parent issue if any owned semantic row
     is `STRUCTURAL_PASS`, `NOT_PROVEN`, or `FAILED`.

## Future Assurance Boundary

No prompt, agent, or process can guarantee that no future gap will ever exist.
The realistic goal is to make this class of gap fail before merge and before
status/matrix closure.

The proposed gates are sufficient to prevent the specific `#280` failure mode
only if they are made executable and required in CI:

- semantic browser verifier runs on every final closure PR;
- matrix rows cannot be marked satisfied unless the verifier gives
  `SEMANTIC_PASS` for semantic rows;
- docs/status overclaim checks fail when claims exceed verifier evidence;
- independent intended-vs-implemented review is required before merge.

For controlled/demo-hosted work, these gates can prove expected behavior inside
the declared bounded scope. They do not prove production readiness unless the
requirements also include production infrastructure, provider, durability,
security, monitoring, cost, abuse, privacy, and operational evidence.

## Future Prompt Reminder

For future work, use this exact closure rule:

> Treat metadata-correct output as failure unless the browser-visible user text
> itself satisfies the requirement. For multilingual work, fail if target text is
> a template, English fallback, source-heading summary, or metadata-only sentence.
> The verifier must classify every relevant requirement as `STRUCTURAL_PASS`,
> `SEMANTIC_PASS`, `NOT_PROVEN`, or `FAILED`, and matrix rows may not be marked
> satisfied unless the row's strongest claim is proven.

Additional hard rule for multilingual claims:

> Do not accept mock conversion evidence as multilingual conversion. If the
> product requirement says deterministic 25-language conversion of arbitrary
> source clauses, then browser-visible target text and decoded artifacts must
> contain deterministic target-language renderings of those source clauses. A
> local/mock provider posture is fine; metadata-only target text is not.
