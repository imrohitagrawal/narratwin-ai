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
accepted scripts only. Arbitrary input remains unsupported locally unless a later
reviewed provider stage implements real translation. The requested sub-agent
fan-out was attempted, but all sub-agents errored on account usage limits; the
equivalent local independent review passes are recorded in
`docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md`.

## Human verification checklist

| Focus area | What to verify | Data/source/artifact to verify | Pass condition | Fail condition | Residual-risk owner |
|---|---|---|---|---|---|
| Priority 1 output correctness | Every Priority 1 language has source English, target text, English reference, citations, binding, artifact parity, and negative coverage. | `reports/checkpoint3-multilingual/priority1-coverage-matrix.json`; `reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json` | Matrix has 25 Priority 1 languages and rejects fallback, partial, wrong script, missing reference, and citation drift. | Any Priority 1 language lacks positive or negative coverage. | reviewer |
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
| Intent/spec | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | repo-file | C3A-R1 | pre-code preflight commit `e48b7af` | implementer | source | passed | Issue #276 owns this repair only. |
| Failure matrix / invariant matrix | `docs/governance/preflights/issue-276.json` | repo-file | C3A-R1-FM | pre-code preflight commit `e48b7af` | implementer | matrix | passed | Local/mock fixture scope only. |
| Tests / old-behavior proof | commit `4868784` | repo-file | C3A-R1-FM | RED tests failed before implementation | implementer | test | passed | Old behavior captured before code edits. |
| Tests / current behavior | `tests/acceptance/test_checkpoint3_output_correctness.py` | repo-file | C3A-R1-FM | `uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q` | implementer | test | passed | API/output correctness is exhaustive for Priority 1. |
| Browser behavior | `frontend/tests/checkpoint3-real-browser.spec.ts` | repo-file | C3A-R1-UI | `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts` | implementer | test | passed | Browser coverage is representative by script family. |
| Docs/gates | `scripts/quality/check_checkpoint3_acceptance.py` | repo-file | C3A-R1-GATE | `make checkpoint3-acceptance` | implementer | gate | passed | Gate rejects missing representative browser evidence. |
| Adversarial review | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | repo-file | C3A-R1-REVIEW | fallback independent review passes | implementer | source / human-only | passed | Sub-agent fan-out blocked by usage limit. |
| Review prompt set | `docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md` | repo-file | C3A-R1-REVIEW | requested reviewer roles recorded | implementer | source / human-only | passed | Human reviewer may repeat prompts if usage limits reset. |
| Skill/tool selection | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | repo-file | C3A-R1-SKILL | repo-approved skills only | implementer | gate | passed | No custom skills/plugins or dependencies added. |

## Human-only review surfaces

| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |
|---|---|---|---|---|---|
| Final squash/merge message | CI cannot inspect the final merge dialog text before merge | repo owner | PR body / reviewer confirmation | Reference-only final message with no issue-closing keyword accepted for PR only | before merge |
| Manual local-demo rehearsal | CI can drive the browser, but a human reviewer should still inspect the local demo for readability | reviewer | `docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md` | Automated evidence is primary; human checklist is secondary | before merge approval |

## Pre-implementation evidence

| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix | `docs/governance/preflights/issue-276.json` | `e48b7af` | implementer | Complete before product/code edits. |
| Source facts | `docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md` | `e48b7af` | implementer | Complete before product/code edits. |
| Old-behavior proof | RED test commit | `4868784` | implementer | Tests failed before implementation. |
| Human-only surfaces | PR-body draft and review evidence | this branch | reviewer | Manual rehearsal remains secondary reviewer-owned evidence. |

## Validation evidence

```text
make quality
# passed

make checkpoint3-acceptance
# Checkpoint 3 acceptance complete: 8 passed, 0 planned, 0 failed.

make ci
# passed; unit tests 1770 passed, API tests 101 passed, frontend tests 18 passed, frontend smoke 4 passed / 2 intentionally skipped, Docker image consensus scan status pass

uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q
# 5 passed

uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py tests/unit/test_checkpoint3_acceptance_gate.py -q
# 80 passed

npm --prefix frontend run test -- page.test.tsx
# 16 passed

NARRATWIN_CP3_PRODUCT_FAITHFUL=1 NARRATWIN_REAL_STACK=1 npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts
# 1 passed
```

## Notes for reviewer

No new third-party packages, tools, providers, assets, or generated samples were
introduced, so `docs/THIRD_PARTY_NOTICES.md` was not changed.
