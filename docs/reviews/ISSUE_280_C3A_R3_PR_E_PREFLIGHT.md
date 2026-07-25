# Issue 280 C3A-R3 PR E Preflight

Date: 2026-07-25

Issue: `#280` C3A-R3

Branch: `phase-1-closure-280-c3a-r3-pr-e-arbitrary-demo-closure`

Refs: `#249`, `#280`

## Objective

PR E is the final local/mock closure slice for issue `#280` if the evidence
holds. It must make bounded public-safe synthetic markdown work through the
browser-visible Issue 280 demo path for arbitrary synthetic project knowledge,
all 25 supported local-demo languages, material depth differences, material
audience differences, and conversion parity across API, stored output, UI,
downloadable artifacts, verifier report, and local/mock provider posture.

This is local/demo deployment quality only. PR E does not claim arbitrary
real-world translation quality, provider quality, hosted/public demo readiness,
provider setup, paid spend, real provider calls, cloned identity runtime, real
media, public distribution, Checkpoint 3B, Checkpoint 3C, Product Mode 2, or
production readiness.

## Gap Audit

| Row | Current observed behavior | Required behavior | Failing evidence before PR E | Owner | Test plan |
|---|---|---|---|---|---|
| `R280-CONVERSION-001` | `/checkpoint3/issue280/local-e2e-demo` returns generated English and target segments, but target conversion is limited to `en`, `hi`, and `es`; artifacts are absent. | Source facts flow through grounded English, target transcript, stored output, UI, downloadable artifacts, Stage 7 placeholder/export evidence, citations, context refs, and claim supports. | RED: API/browser/verifier tests fail on non-`en/hi/es` languages and missing artifacts. | PR E | `tests/acceptance/test_issue280_pr_e_closure.py`; `tests/contract/test_issue280_ui_api_artifact_parity.py`; `make issue280-output-correctness`. |
| `R280-CRITICAL-CONNECTIONS-001` | IDs/checksums exist for core response only; multilingual run ID, glossary preservation, transcript metadata, subtitles, voice manifest, avatar demo, render manifest, video placeholder, coverage matrix, and correctness report are not bound. | Parity fields must match across API, stored output, UI, artifacts, and reports. | RED: parity tests fail because response has no artifact bundle or parity report. | PR E | Contract parity test plus verifier report comparison. |
| `R280-QUALITY-001` | Target text can preserve English body text as a mock prefix; unsupported local languages refuse; depth/audience false-pass cases are not exhaustively rejected. | Reject untranslated fallback, lost citations, broken segment count, metadata-only success, artifact-only success, stale evidence, planned-language fake success, and binding drift. | RED: quality tests fail on English leakage and all-25 supported-language coverage. | PR E | API quality tests and all-25 language verifier. |
| `R280-TEST-STRATEGY-003` | Contract test path is planned but absent. | Contract tests prove API, stored output, UI-visible metadata, exports, reports, citations, context refs, claim supports, IDs, language, audience, depth, glossary, and checksum parity. | RED: `uv run pytest tests/contract/test_issue280_ui_api_artifact_parity.py -q` fails before file/behavior exists. | PR E | Add contract test and gate wiring. |
| `R280-TEST-STRATEGY-005` | `make issue280-output-correctness` is planned but absent. | Gate executes local/mock flow and preserves regression coverage. | RED: `make issue280-output-correctness` fails before target exists. | PR E | Add dedicated verifier script and Make target. |
| `R280-OUTPUT-CORRECTNESS-001` | PR D browser verifier proves the PR C endpoint only; screenshots are evidence adjuncts, not full closure proof. | Dedicated verifier starts repo services, opens real browser, submits arbitrary markdown, observes network/API, verifies output/depth/audience/parity/errors, writes report/screenshots, and rejects unsafe leakage. | RED: existing verifier lacks all-25, artifacts, depth/audience comparisons, and final closure report. | PR E | `scripts/quality/verify_issue280_output_correctness.py` plus Playwright Issue 280 spec. |
| `R280-GOV-005` | Phase 1 gate knows PR A-D branch allowlists only and matrix keeps PR E rows planned. | PR E branch allowlist, matrix, docs/status/traceability, validation, PR body, and issue closure wording must match actual evidence. | RED: `tests/unit/test_phase1_closure_docs.py` fails for PR E branch before allowlist exists. | PR E | Add branch allowlist tests and update matrix only after executable evidence passes. |

## Positive Claims

- Bounded public-safe synthetic markdown that is not a controlled acceptance
  fixture can complete the Issue 280 local/mock demo path.
- The endpoint supports every Stage 6 Priority 1 supported local-demo language
  and refuses planned/unsupported languages without fake success.
- `CONCISE`, `STANDARD`, and `DEEP` produce visibly different English scripts
  while preserving citation, context-ref, claim-support, and evaluation binding.
- Recruiter, hiring manager, engineer, product leader, customer, beginner, and
  global viewer modes produce distinct source-grounded emphasis.
- Target transcript segments preserve citations, context refs, claim supports,
  evaluation IDs/checksums, trace IDs, glossary metadata, and segment count.
- Artifact bundle contents match the API response and verifier report.
- Browser evidence observes real local network calls and visible output; it is
  not metadata-only, screenshot-only, API-only, mocked-status-only, or docs-only.

## Negative Invariants

- No paid providers, real provider calls, provider SDK setup, hosted/public
  demo, public URL, real media, cloned identity runtime, private data, provider
  payloads, secrets, credentials, tokens, filesystem paths, stack traces, or
  production-readiness claims.
- Target transcript text must not be an untranslated English fallback except
  protected glossary/project terms and citation markers.
- Planned/unsupported languages must refuse with a safe taxonomy error.
- Prompt injection, unsafe/private input, unsupported file type, malformed
  request, glossary-as-instruction, missing evidence, citation drift,
  context-ref drift, claim-support drift, artifact mismatch, and stale reports
  must fail before a success claim.

## Skill And Tool Selection

Used: `test-driven-development`, `frontend-ui-engineering`,
`security-and-hardening`, and `code-review-and-quality` guidance. The repo
governance docs, PR A-D preflights, ADRs, matrix, existing tests, and local
FastAPI/Playwright patterns are the source of truth. Skill invocation is not
evidence; result-bearing tests and verifier reports are.

Rejected: provider, hosted, media, cloned-identity, public-launch, dependency,
and production-readiness work because issue `#280` explicitly excludes those
surfaces.

## Stop Rule

Stop before PR-ready state if a supported local-demo language cannot pass
without English fallback, if artifacts are not bound to source/evaluation
metadata, if browser evidence uses success-path interception, if raw markdown
or sensitive-looking values leak, or if the implementation requires provider,
hosted, real-media, or production scope.
