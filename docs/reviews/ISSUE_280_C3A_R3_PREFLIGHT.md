# Issue #280 C3A-R3 PR A Preflight

## Objective

PR A converts issue #280 comments into repository-tracked, public-safe planning
artifacts for the faithful local end-to-end multilingual demo contract. It
locks the persona/audience/depth research basis, requirement matrix, UI behavior
coverage, conversion/parity coverage, and merge-safe red-evidence framework.

PR A does not implement runtime product behavior.

## Scope

In scope:

- Planning/preflight evidence for issue #280 PR A.
- Research-backed static persona/audience/depth contract.
- Machine-checkable requirement matrix under
  `reports/checkpoint3-issue280/requirement-matrix.json`.
- Reviewer-facing checklist for later PR slices.
- Merge-safe red-evidence framework with no permanently failing CI tests.
- Guardrail and phase quality tests for the PR A artifact contract.

Out of scope:

- Runtime backend, frontend, RAG, avatar, provider, database, Docker, hosted, or
  deployment behavior.
- Provider setup, provider SDKs, provider calls, provider outputs, paid spend,
  hosted/public demo, public URL, real media, cloned identity runtime, public
  distribution, production-readiness claims, or arbitrary real-world translation
  quality.
- Closing issue #249 or issue #280.

Public-safe non-goals are explicit: no provider setup, no paid spend, no
hosted/public demo, no production-readiness claim, no cloned identity runtime,
no real media, no private strategy, no provider payloads, no provider outputs,
no secrets, no credentials, and no tokens.

## Positive Claims

| ID | Claim | Evidence |
|---|---|---|
| R280A-PREFLIGHT-001 | First branch commit contains only `docs/governance/preflights/issue-280.json`. | Git history and forced governance preflight. |
| R280A-MATRIX-001 | Every required `R280-*` section is represented in the requirement matrix. | `reports/checkpoint3-issue280/requirement-matrix.json`; phase quality check. |
| R280A-PERSONA-001 | Persona/audience rows are public-source researched and avoid private personality inference. | `docs/reviews/ISSUE_280_C3A_R3_PERSONA_AUDIENCE_RESEARCH.md`; phase quality check. |
| R280A-RED-001 | Red evidence is merge-safe and cannot break CI permanently. | `reports/checkpoint3-issue280/red-evidence-plan.json`; `docs/reviews/ISSUE_280_C3A_R3_RED_EVIDENCE_REVIEW.md`. |
| R280A-GOV-001 | PR A cannot claim runtime completion or close #249/#280. | Guardrail tests and PR body wording. |

## Failure Matrix

| ID | Failure case | Expected result | Planned evidence |
|---|---|---|---|
| R280A-FM-001 | PR A edits runtime product files. | Phase 1 allowlist fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_pr_a_rejects_runtime_product_files`. |
| R280A-FM-002 | PR A claims runtime implementation is complete. | Guardrail/phase check fails. | `tests/unit/test_guardrails_check.py::test_issue280_pr_a_rejects_runtime_completion_claim`. |
| R280A-FM-003 | PR A closes #280 or #249. | Guardrail fails with issue-specific message. | `tests/unit/test_guardrails_check.py::test_issue280_pr_a_rejects_closing_issue_280` and `test_issue280_pr_a_rejects_closing_issue_249`. |
| R280A-FM-004 | Matrix row cites issue comments alone as evidence. | Phase quality fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_matrix_rejects_issue_comment_only_evidence`. |
| R280A-FM-005 | Matrix row lacks planned executable evidence or reviewed re-scope. | Phase quality fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_matrix_requires_planned_executable_evidence`. |
| R280A-FM-006 | Public-safe non-goals are removed. | Phase quality fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_preflight_requires_public_safe_boundaries`. |
| R280A-FM-007 | Red evidence framework commits permanent failing tests. | Phase quality fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_red_evidence_rejects_permanent_failing_tests`. |
| R280A-FM-008 | Future implementation testing strategy omits positive/negative/corner, API, contract, exact UI, E2E flow, or regression coverage expectations. | Phase quality fails. | `tests/unit/test_phase1_closure_docs.py::test_issue280_matrix_requires_future_implementation_test_strategy`. |

## Matrix-To-Test Mapping

| Matrix group | PR A evidence | Later owner |
|---|---|---|
| R280-SCOPE, R280-GOV | Static matrix, PR guardrails, status wording | PR A plus all later PRs |
| R280-INPUT, R280-ERROR | Static contract rows and planned executable commands | PR B |
| R280-AUDIENCE, R280-PERSONA, R280-DEPTH, R280-AUDIENCE-DEPTH | Persona research and matrix rows | PR B and PR D |
| R280-S4, R280-S6, R280-GLOSSARY, R280-CONVERSION, R280-CRITICAL-CONNECTIONS | Static row contracts | PR B and PR C |
| R280-UI, R280-CONVERSATION-UX | Checklist and matrix rows | PR D |
| R280-QUALITY, R280-EVIL-SET, R280-OUTPUT-CORRECTNESS | Matrix and red-evidence plan | PR B through PR E |
| R280-TEST-STRATEGY | Static future-development contract covering positive/negative/corner, API, contract, exact UI, E2E flow, and regression test coverage | PR A defines; PR B through PR E execute |

## Future Implementation Test Strategy Contract

PR A does not implement runtime product behavior, but it now makes the later
development bar explicit. Every future `#280` implementation PR must show the
test strategy for the rows it owns before it can claim those rows are satisfied.
The required coverage families are:

- positive cases, negative cases, corner cases, and regression tests;
- API tests for request bounds, response shapes, status codes, safe errors,
  provider-disabled/local posture, unsafe input rejection, and anti-leak
  guarantees;
- contract tests for API, stored output, UI-visible metadata, exports, reports,
  citations, context refs, claim supports, run IDs, language, audience, depth,
  glossary, and checksums;
- exact UI validation tests using real browser evidence for what users see and
  act upon, including form values, tooltips, transcript expansion, truncation,
  safe errors/remediation, citations, exports/downloads, keyboard behavior, and
  mobile/touch behavior;
- the final local/mock E2E output-correctness gate:
  `create project -> upload markdown -> approve -> ingest -> generate ->
  translate -> render UI -> download/decode artifacts -> compare reports`.

The planning assumption is that local/mock APIs are first-class contracts even
while providers remain disabled and runtime remains deterministic/local.

## Skill And Tool Selection Ledger

Invoked:

- `planning-and-task-breakdown`: decomposed #280 into PR slices and matrix rows.
- `spec-driven-development`: converted issue comments into positive claims and
  negative invariants.
- `test-driven-development`: added validator regression tests before broadening
  guardrails.
- `source-driven-development`: used public sources for persona/audience facts.
- `security-and-hardening`: preserved untrusted input and anti-leak boundaries.
- `api-and-interface-design`: shaped the planned error and evidence contracts.
- `observability-and-instrumentation`: required run/eval/checksum parity fields.
- `code-review-and-quality`, `doubt-driven-development`, and `taste-check`:
  used for adversarial scope and quality review.
- `git-workflow-and-versioning`: preserved branch and first-commit invariants.
- `user-personas`: used for research-backed persona artifact structure.

Rejected or prevented:

- Runtime implementation in PR A.
- Provider setup, provider calls, paid or hosted evidence.
- Issue-comment-only evidence.
- Permanent failing tests.
- Closing-keyword wording for #249 or #280.

## Red-Evidence Strategy

PR A records current gaps as public-safe reviewed red evidence without breaking
CI. Later PRs may use strict `xfail` or skipped tests only when the skip reason,
owner PR slice, and removal criteria are machine-checkable. Matrix rows use
`RED_EVIDENCE_CAPTURED`, `PLANNED_IMPLEMENTATION`, or
`PLANNED_EXECUTABLE_GATE` until executable evidence exists.

## Completion Criteria

- First commit invariant is preserved.
- Required artifact files exist and pass the static validator.
- Matrix contains every required `R280-*` section.
- Every row has status, evidence type, planned command or reviewed re-scope, and
  owner PR slice.
- #249 and #280 remain open after PR A.
- PR body states PR A does not implement runtime product behavior and does not
  authorize public/demo/provider/paid/production/cloned-identity scope.

## Stop Rule

If review finds a missing #280 requirement class, pause implementation, update
the matrix and reviewer checklist, then rerun the static artifact checks before
adding runtime work in a later PR.

Stop and open a new issue if #280 PR A requires runtime backend, frontend, RAG,
avatar, provider, database, Docker, hosted deployment, public demo, paid spend,
cloned identity runtime, real media, private data, private strategy, provider
payload/output evidence, or production-readiness claims.
