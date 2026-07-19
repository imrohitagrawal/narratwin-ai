# Issue #204 CH-M1-01 Preflight

## Objective

Repair the frontend Product Mode 1 local/mock avatar request chain so the UI
captures a durable synthetic-avatar consent record before requesting a Stage 7
avatar render, then sends the returned `consentRecordId` with the render
request.

Parent controller: issue `#155`.

Selected issue: issue `#204`, `CH-M1-01`.

## Scope

In scope:

- `frontend/src/app/page.tsx` request sequencing only.
- `frontend/tests/smoke.spec.ts` mocked browser evidence for the UI request
  chain and render idempotency seed.
- `docs/ADR/0019-ch16-consent-capture.md` addendum documenting that the
  existing two-step consent architecture also applies to the local/mock UI path.
- Phase 1 Closure branch allowlist tests and documentation for this narrow
  local/mock Mode 1 slice.

Out of scope:

- Backend consent semantics, storage, provider, avatar adapter, Docker,
  database, hosted deployment, production durability, backup/restore,
  monitoring, security posture closure, Product Mode 2, real audio, real video,
  imported media, cloned identity, external providers, public launch, and public
  media distribution.
- Stopped predecessor evidence in issue `#167`, PR `#168`, PR `#166`, issue
  `#159`, or PR `#162`.

## Source Facts

| Fact | Source | Engineering consequence |
|---|---|---|
| Phase 1 Closure is active and the release posture remains No-Go. | `docs/STATUS.md` and live post-PR `#203` closeout evidence | This PR may improve local/mock Mode 1 flow only; it must not claim production/public release readiness. |
| Issue `#155` is the serialized Product Mode 1 checkpoint controller. | issue `#155`, `docs/STATUS.md`, `docs/PHASE_PLAN.md` | CH-M1-01 is the next controlled local/mock child slice. |
| `/avatar-consents` stores or replays an affirmative durable consent record. | `docs/API_CONTRACT.md` | The UI must call this endpoint before durable avatar rendering. |
| `/avatar-renders` requires `consentRecordId` on the durable API path. | `docs/API_CONTRACT.md` | A boolean-only frontend render request is the old invalid behavior. |
| Missing or invalid durable consent state returns `AVATAR_CONSENT_RECORD_REQUIRED` or `AVATAR_CONSENT_INVALID`. | `docs/API_CONTRACT.md` | UI error display must treat these backend codes as safe bounded errors. |
| ADR `0019` owns the durable synthetic-avatar consent-capture architecture. | `docs/ADR/0019-ch16-consent-capture.md` | The frontend repair must update that ADR without changing backend consent semantics. |
| PR `#203`/issue `#202` closeout does not require another pure STATUS reconciliation issue. | issue `#202` closeout comment and current user instruction | This work records only material CH-M1-01 issue mapping and validation evidence. |

## Invariant And Failure Matrix

| ID | Claim or failure mode | Required proof |
|---|---|---|
| M1C01-CHAIN-001 | UI captures durable consent before render and sends returned `consentRecordId` to `/avatar-renders`. | Mocked Playwright smoke asserts request order and render body. |
| M1C01-IDEMP-002 | Render idempotency no longer reuses the old boolean-only seed; it includes the durable consent record identity. | Mocked Playwright smoke asserts the new render idempotency key. |
| M1C01-ERROR-003 | Durable consent backend errors are safe to display through the existing bounded error path. | Mocked Playwright smoke returns `AVATAR_CONSENT_INVALID` from `/avatar-renders` and asserts the bounded alert path. |
| M1C01-SCOPE-004 | CH-M1-01 branch can touch only the approved frontend, smoke, governance, and traceability files. | `tests/unit/test_phase1_closure_docs.py` and `scripts/quality/check_phase1_closure_docs.py`. |
| M1C01-EVIDENCE-005 | Mocked browser evidence is not mislabeled as real-stack E2E evidence. | PR body and status text must call it mocked browser smoke; CH-M1-02 remains the real-stack step. |
| HUMAN-MERGE-001 | Merge and issue closeout remain human-gated and reference-only unless approval explicitly makes closeout eligible. | Reviewer approval, green CI, and final merge message review. |

## Red Evidence Plan

Before the implementation change, the updated smoke expectation would fail
because `frontend/src/app/page.tsx` calls `/avatar-renders` directly after the
multilingual run and does not call `/avatar-consents` or pass
`consentRecordId`.

## Validation Plan

- `uv run pytest tests/unit/test_phase1_closure_docs.py`
- `python3 scripts/guardrails_check.py`
- `make quality`
- Focused mocked frontend smoke covering the CH-M1-01 request chain.
- Forced pull-request guardrail event after the PR body exists.

## Human-Only Surfaces

| Surface | Why automation cannot complete it | Owner |
|---|---|---|
| GitHub PR approval | Repository policy requires human review before merge. | repo owner/reviewer |
| Final squash/merge wording | The final merge dialog is outside local test control. | repo owner/merger |
| Checkpoint A decision | Requires CH-M1-01 and CH-M1-02 evidence review. | repo owner/reviewer |
| Production/public release approval | Requires external accounts, platform, backup/restore, monitoring, security, and release authorization not available in this local slice. | repo owner/release authority |

## Advisory Sub-Agent Final Review

Sub-agent final review for PR `#205` covered frontend/API correctness,
governance/guardrails, security/release posture, and validation adequacy before
manual approval was requested. The review found two required gaps: executable
durable-consent render-error smoke coverage and clearer governance handoff
evidence for the parent `#155` ledger. Both were re-reviewed after correction:
the smoke coverage now exercises the bounded `AVATAR_CONSENT_INVALID` alert
path, the PR body records the preflight-order caveat, and the `#155` ledger has
a durable handoff comment.

This sub-agent review is advisory pre-manual-review evidence only. A
self-authored GitHub `COMMENTED` review is not approval evidence and is rejected
by the GovernancePreflightV1 `pull_request_review` guardrail by design. Human
approval, final merge wording, and issue closeout remain human-only surfaces.

## Skill Selection Evidence

| Skill | Decision | Evidence or reason |
|---|---|---|
| `planning-and-task-breakdown` | Used | Needed to select the smallest unblocked #155 child issue from live issue/PR/worktree state. |
| `git-workflow-and-versioning` | Used as workflow guidance | Needed branch/PR hygiene and dirty-worktree preservation discipline. |
| `test-driven-development` | Used | CH-M1-01 is a request-chain bug fix with an old-behavior smoke failure expectation. |
| `incremental-implementation` | Used | Scope is a narrow frontend sequence plus guardrail allowlist rather than a broader Mode 1 rewrite. |
| `frontend-ui-engineering` | Used | The change is in the user-facing frontend workflow, though no visual redesign is intended. |
| `security-and-hardening` | Used | Consent IDs and backend error exposure affect synthetic-media safety boundaries. |
| `code-review-and-quality` | Used | Final self-review must check overclaim, scope drift, and missing negative evidence. |
| Deployment/shipping skills | Rejected | This issue cannot and should not change hosted/public release posture. |
| Production durability/security closure skills | Rejected | Issues `#39`, `#126`, and `#139`-`#149` remain production/posture blockers, not local/mock blockers. |

## Stop Rule

Stop and open a new issue instead of expanding this one if the repair requires
backend consent semantics, real provider behavior, production infrastructure,
media distribution, Product Mode 2, or any mutation of stopped predecessor
surfaces.
