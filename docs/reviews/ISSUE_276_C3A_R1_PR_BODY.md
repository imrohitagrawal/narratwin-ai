## Linked issue

Refs #276

This PR intentionally uses reference-only wording until reviewer approval and
merge eligibility are confirmed.

## Reviewer overview

### 1. What changed and why

Checkpoint 3A previously allowed multilingual “success” even when the
user-visible output was partial, English fallback, romanized native-script
fallback, or only artifact/metadata bound. This PR repairs the local/mock
multilingual contract so successful output includes source English, target
native-language transcript text, English reference/back-translation, citations,
and source/eval/context/claim-support binding for every segment.

### 2. Scope

- In scope: backend-driven language catalog, deterministic local/demo Priority 1
  translations for controlled acceptance scripts, structured transcript segments,
  transcript correctness validation, artifact parity checks, UI rendering, RTL
  and script-family browser evidence, negative mutation tests, coverage reports,
  and Checkpoint 3A gate updates.
- Out of scope: hosted deployment, public URL, paid providers, real provider
  calls, production readiness, cloned identity, real media, arbitrary-input
  machine translation, and romanization mode.

### 3. Key files and components

Backend contract: `backend/app/stage6.py`, `backend/app/main.py`
Frontend UI/rendering: `frontend/src/app/page.tsx`,
`frontend/src/app/page.module.css`, `frontend/src/app/page.test.tsx`,
`frontend/tests/checkpoint3-real-browser.spec.ts`
Acceptance/gates: `tests/acceptance/test_checkpoint3_output_correctness.py`,
`tests/acceptance/test_checkpoint3_media_artifacts.py`,
`scripts/quality/check_checkpoint3_acceptance.py`,
`tests/unit/test_checkpoint3_acceptance_gate.py`
Docs/evidence: `docs/STATUS.md`, `docs/QUALITY_GATES.md`,
`docs/TRACEABILITY.md`, `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`,
`docs/ADR/0033-checkpoint3-real-browser-acceptance-evidence.md`,
`docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md`,
`docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md`

### 4. Reviewer focus

Review whether `COMPLETED` is impossible without transcript correctness
validation, whether catalog presence stays distinct from local/demo generation
support, whether Priority 2 Indian regional languages are visible but unsupported
locally, whether artifacts contain the same structured transcript as the UI, and
whether browser evidence proves visible output across representative scripts
rather than trusting backend metadata.

### 5. Validation, limitations, and residual risks

Validation passed locally:

```text
make quality
make checkpoint3-acceptance
make ci
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/unit/test_checkpoint3_acceptance_gate.py -q
npm --prefix frontend run test -- page.test.tsx
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
```

Residual risk: local/demo translations are deterministic fixtures for controlled
accepted generated walkthrough scripts only. Arbitrary input remains unsupported
locally unless a later reviewed provider stage implements real translation. For
small approved local/demo source documents within retrieval top-k, the generated
walkthrough path now expands to all approved claim chunks before multilingual
generation; a separate raw uploaded-document translation API is not claimed by
this Stage 6 surface. The earlier final fan-out PASS is superseded because human
manual review found semantic output failures after that review. The latest
fan-out and independent fallback review found additional blockers around explicit positive matrix
rows, original manual-review document support, browser voice-provider posture,
uncommitted evidence state, and fixed CP8 browser ports that made the default
acceptance gate nondeterministic when stale local review servers were present.
The latest final Doubt-Driven sub-agent review on `d87a66e` then found
standalone English `walkthrough` leaking in successful Russian/Ukrainian target
text. Commit `e8811841` fixed that blocker. A main-session independent fallback
Doubt-Driven rerun against `e8811841` passed because the sub-agent tool was not
exposed in that turn. A subsequent Output-Correctness fan-out pass found the
downloadable `translatedScript` artifact still contained only flat target text
instead of the same source English, target text, English reference,
citations, and trace bindings exposed in the UI and metadata. That blocker is
fixed in later pushed commits; local gates, GitHub checks, and behavior-head
fan-out were rerun after the subsequent blockers below were fixed.
The next Output-Correctness fan-out on `aa9ba02` confirmed that artifact fix but
blocked because Hindi still accepted transliterated source-domain terms
`जनरेट` and `वॉकथ्रू` in the citation-requirement segment. That Hindi blocker
was fixed in `c20c6c6`, but human local-demo review and subsequent fan-out
reviews found additional visible-output gaps: the original NarraTwin four-line
document needed exact all-language golden coverage, NarraTwin/Atlas/Helio
fixtures could still pass partial substrings, some audience prefixes leaked or
were silently dropped, Atlas could invent an engineer audience, Vietnamese Atlas
had mixed-script contamination, and Spanish Helio duplicated `Para reclutadores`.
The final behavior-reviewed head
`041960ae2bc69e6a2b6d42eaad4db3fc150e534b` fixes those blockers. `make quality`,
`make checkpoint3-acceptance`, `make ci`, GitHub checks, and the mandatory
Output-Correctness, TDD, Doubt-Driven, and False-Positive final fan-out passed
on that behavior head with no findings. Later commits are evidence-only PR body
and review-evidence updates.
Human local-demo review remains the final manual approval input.
Final evidence is recorded in
`docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md`.

## Human verification checklist

| Focus area | What to verify | Data/source/artifact to verify | Pass condition | Fail condition | Residual-risk owner |
|---|---|---|---|---|---|
| Priority 1 output correctness | Every Priority 1 language has source English, target text, English reference, citations, binding, artifact parity, positive coverage, and negative coverage. | `reports/checkpoint3-multilingual/priority1-coverage-matrix.json`; `reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json` | Matrix has 25 Priority 1 languages, 25 positive rows, and rejects fallback, partial, one-segment partial, wrong script, missing reference, citation drift, missing binding, glossary-forced English leakage, metadata-only success, and artifact-only success. | Any Priority 1 language lacks positive or negative coverage. | reviewer |
| Browser visible behavior | Representative script families are exercised through the real UI without route fulfillment. | `reports/checkpoint3-real-browser/playwright-output/.../issue-269-c3a-cp8-browser-evidence.json` | French, Hindi, Arabic, Hebrew, Japanese, Korean, Russian, and Thai groups all have visible source/target/reference/citation/artifact parity booleans true. | Any required group is absent or has a false visible-output boolean. | reviewer |
| Unsupported local/demo languages | Priority 2 languages are cataloged but not falsely supported. | `/api/v1/languages`; UI selector; `tests/api/test_stage6_multilingual_api.py` | Priority 2 tags show planned/unsupported and refuse generation honestly. | Unsupported language generates fake success. | reviewer |
| Local/mock boundaries | No hosted/provider/paid/cloned/real-media/prod claims were introduced. | PR diff; `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`; CP8 evidence providers block | Providers remain mock/local, network egress false, realVideo false, clonedIdentity false. | Any real provider setup, public URL, paid spend, or production-readiness claim appears. | reviewer |
| Human rehearsal | Manual demo script is usable for secondary review. | `docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md` | Reviewer can answer the checklist questions for selected local/demo languages. | Checklist is missing required source/target/reference/script/citation/artifact/unsupported-language questions. | reviewer |

## Stage / slice

- Stage: Phase 1 Closure / Checkpoint 3A repair
- Branch: `phase-1-closure-c3a-r1-major-market-multilingual-output-correctness`
- Scope: issue `#276` local/mock multilingual output correctness

## Summary

- Added backend-driven language catalog and structured multilingual transcript
  validation for 25 Priority 1 languages, with Hindi in Priority 1 and Priority 2
  Indian regional languages cataloged as planned/unsupported locally.
- Hardened API, artifact, UI, acceptance, and browser tests so Checkpoint 3A
  cannot pass with partial translation, English fallback, romanized/wrong-script
  fallback, citation drift, missing bindings, metadata-only success, or
  artifact-only success.

## Status impact

`docs/STATUS.md` is updated in this PR and records the target state for issue
`#276` as satisfied by this PR. Routine post merge facts must be recorded in
PR issue comments, and this work must not create a successor status only PR when
there is no successor status-only follow-up needed.

## Guardrail checklist

- [x] This PR was created from a tracked GitHub issue.
- [x] No direct commits were made to `main`.
- [x] CI passes before merge.
- [x] No secrets, tokens, credentials, or provider keys are committed.
- [x] Tests run without paid providers or real provider keys.
- [x] External services use mock/local adapters by default.
- [x] Provider keys are read only from environment variables.
- [x] LLM outputs include trace/run metadata where applicable.
- [x] Generated scripts/answers cite source chunks where applicable.
- [x] Eval failures block this PR.
- [x] Security critical/high findings block this PR.
- [x] Architecture-impacting changes include an ADR update under `docs/ADR/`.
- [x] PRD-impacting changes update `docs/TRACEABILITY.md`.
- [x] Repository-tracked stage/governance changes update `docs/STATUS.md`.
- [x] Implementation or release-readiness changes checked `docs/PROJECT_LEARNINGS_TRACKER.md`.
- [x] Non-trivial changes link a completed preflight artifact per `docs/ENGINEERING_PROCESS_RCA.md` and `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`.
- [x] Durability, restore/replay, artifact, release, CI, or governance/process work includes an invariant-to-test matrix link before implementation.
- [x] Negative tests were added or explicitly marked human-only/source/non-goal in the invariant matrix.
- [x] Old behavior fails, RED, mutation, break-test, or regression-reproduction evidence is listed for changed guardrails and bug fixes.
- [x] Human-only review surfaces are listed with owner and residual-risk decision.
- [x] Non-trivial reviewer-focus points and changed high-risk surfaces are captured in the Human verification checklist with exact data/source/artifact references, official URL and verified/accessed date where facts can change, pass/fail criteria, and residual-risk owner.
- [x] Preinstalled repo docs/approved skills were checked first; no custom skill/plugin was created or used unless the gap, rejected existing options, approval, `docs/SKILL_LOCK.md`, and `docs/THIRD_PARTY_NOTICES.md` updates are linked.
- [x] Repeated-review stop rule was evaluated; if a fresh review found a new defect class after a fix, implementation paused for contract rewrite before another bug-fix loop.
- [x] Process/durability/governance work considered whether `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` should receive reusable lessons for future projects/apps.
- [x] Implementation or release-readiness changes completed invariant, exploit-matrix, and contract/gate review per `docs/REVIEW_RIGOR_RETROSPECTIVE.md`.
- [x] PR title, body, branch commit messages, and final merge/squash message plan were checked for automation-sensitive wording such as issue-closing keywords.

## Preflight evidence

| Evidence | Artifact reference | Reference type | Matrix IDs | Command / CI / Source | Reviewer | Evidence type | Completion status | Residual risk decision |
|---|---|---|---|---|---|---|---|---|
| Intent/spec | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | repo-file | C3A-R1-FM | pre-code preflight commit `e48b7af` | implementer | source | pass | Issue #276 owns this repair only. |
| Source facts | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | repo-file | C3A-R1-FM | source facts for local/mock boundary and Priority 1/2 catalog contract | implementer | source | pass | Local/mock fixture scope only. |
| Failure matrix / invariant matrix | `docs/governance/preflights/issue-276.json` | repo-file | C3A-R1-FM | invariant-to-test matrix from pre-code preflight commit `e48b7af` | implementer | matrix | pass | Local/mock fixture scope only. |
| Tests / old-behavior proof | `tests/acceptance/test_checkpoint3_output_correctness.py` | repo-file | C3A-R1-FM | old behavior fails under RED failing test evidence in commit `4868784` | implementer | test | pass | Old behavior captured before code edits. |
| Tests / current behavior | `tests/acceptance/test_checkpoint3_output_correctness.py` | repo-file | C3A-R1-FM | `uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q` | implementer | test | pass | API/output correctness is exhaustive for Priority 1. |
| Browser behavior | `frontend/tests/checkpoint3-real-browser.spec.ts` | repo-file | C3A-R1-FM | `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts` | implementer | test | pass | Browser coverage is representative by script family. |
| Docs/gates | `scripts/quality/check_checkpoint3_acceptance.py` | repo-file | C3A-R1-FM | invariant test gate `make checkpoint3-acceptance` plus back-to-back default rerun after CP8 port isolation | implementer | gate | pass | Gate rejects missing representative browser evidence and no longer depends on fixed default CP8 ports. |
| Adversarial review | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | repo-file | C3A-R1-REVIEW | earlier final PASS evidence was superseded by human-found semantic blockers and later fan-out blockers; behavior-reviewed head `041960a` fixes Hindi/manual-review exactness, partial substring false positives, audience leakage/dropped unknown audiences, Atlas invented audience, mixed-script contamination, and Helio duplicate prefix; final Output-Correctness, TDD, Doubt-Driven, and False-Positive reviewers passed with no findings | implementer | source / human-only | pass | Human local-demo review remains the final manual approval input. |
| Review prompt set | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | repo-file | C3A-R1-REVIEW | review prompt matrix for false pass and adversarial output correctness review | implementer | source / human-only | pass | Human reviewer may repeat prompts if usage limits reset. |
| Stop rule / repeated blocker reset | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | repo-file | C3A-R1-REVIEW | stop rule checked; each human-found or fan-out blocker class updated the executable contract before another fix loop; same-head gates/fan-out passed on `041960a` | implementer | gate | pass | Manual local-demo review remains before approval. |
| Skill/tool selection | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | repo-file | C3A-R1-SKILL | preinstalled approved skills and repo docs checked first; no custom skill creation | implementer | gate | pass | No custom skills/plugins or dependencies added. |

## Human-only review surfaces

| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |
|---|---|---|---|---|---|
| Final squash/merge message | CI cannot inspect the final merge dialog text before merge | repo owner | `docs/reviews/ISSUE_276_C3A_R1_PR_BODY.md` | Reference-only final message with no issue-closing keyword accepted for PR only | before merge |
| Manual local-demo rehearsal | CI can drive the browser, but a human reviewer should still inspect the local demo for readability | reviewer | `docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md` | Automated evidence is primary; human checklist is secondary | before merge approval |

## Pre-implementation evidence

| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix | `docs/governance/preflights/issue-276.json` | commit order: e48b7af before 4868784 | implementer | pass |
| Source facts | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | commit order: e48b7af before 4868784 | implementer | pass |
| Human-only surfaces, if any | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | commit order: e48b7af before 8683b4b | reviewer | pass |

## Validation evidence

```text
uv run pytest tests/unit/test_guardrails_check.py -> passed
uv run pytest tests/unit/test_phase1_closure_docs.py -> passed
python3 scripts/guardrails_check.py -> passed
make quality -> passed
uv run ruff check scripts tests -> passed
uv run mypy scripts tests -> passed
make ci -> passed
make security -> passed
make dependency-audit -> passed
make container-scan -> passed
make secrets-scan -> passed
make eval -> passed
GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/tmp/pr-event.json NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py -> passed
make checkpoint3-acceptance -> passed
make checkpoint3-acceptance at pushed head 6099612 -> passed
make ci at pushed head 6099612 -> passed
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q -> 7 passed
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -q -> passed
uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py tests/unit/test_checkpoint3_acceptance_gate.py -q -> 53 passed
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -q -> passed after source-domain-term fix
uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py -q -> 47 passed
uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_removes_stale_next_dev_lock tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_keeps_live_next_dev_lock tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_allocates_isolated_cp8_ports -q -> 3 passed
uv run ruff check scripts/quality/check_checkpoint3_acceptance.py tests/unit/test_checkpoint3_acceptance_gate.py -> passed
coverage matrix check -> 400 rows, including 25 positive rows and 25 missing-target false-positive rows
npm --prefix frontend run test -- page.test.tsx -> 16 passed
NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts -> 1 passed
make checkpoint3-acceptance back-to-back after CP8 port isolation -> passed twice
occupied default CP8 ports 8120/3120 + make checkpoint3-acceptance -> passed
uv run pytest tests/unit/test_stage6_multilingual.py::test_local_demo_translation_refuses_unknown_audience_prefix_instead_of_dropping_it tests/unit/test_stage6_multilingual.py::test_helio_media_fixture_preserves_explicit_recruiter_audience -q -> passed
uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py tests/acceptance/test_checkpoint3_language_quality.py tests/acceptance/test_checkpoint3_media_artifacts.py -q -> passed
uv run ruff check backend/app/stage6.py tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/acceptance/test_checkpoint3_output_correctness.py -> passed
make checkpoint3-acceptance on behavior-reviewed head 041960a -> 8 passed, 0 planned, 0 failed
make quality on behavior-reviewed head 041960a -> passed
make ci on behavior-reviewed head 041960a -> passed
GitHub checks on behavior-reviewed head 041960a -> all passed
final mandatory fan-out on behavior-reviewed head 041960a -> Output-Correctness PASS, TDD PASS, Doubt-Driven PASS, False-Positive PASS
```

## Notes for reviewer

No new third-party packages, tools, providers, assets, or generated samples were
introduced, so `docs/THIRD_PARTY_NOTICES.md` was not changed.
