# Issue #72 Closure Evidence Hardening Preflight

## Intent

Harden future `#39` row-closure records so durability, operations, media,
security, and provider rows cannot close with generic documentation, Context 0
planning artifacts, placeholder PR references, or unverified child PRs.

## Scope

In scope:

- `scripts/guardrails_check.py` closure-record validation.
- Unit tests for weak evidence and child PR provenance false-pass cases.
- Evidence-contract text in `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`.
- Status/guardrail documentation updates for this process-only change.

Out of scope:

- Runtime, database, backend, frontend, provider, monitoring, or migration code.
- Production implementation for issue `#39`.
- Closing issue `#39`.

## Source Facts

| ID | Source | Fact Used | Design Impact | Verified Date |
|---|---|---|---|---|
| SRC-GH-001 | GitHub REST API pull request endpoint, `GET /repos/{owner}/{repo}/pulls/{pull_number}` | Pull request payloads include state and merged metadata fields. | Guardrail can prefer merged child PR evidence when token/API access is available. | 2026-07-10 |
| SRC-GH-002 | Existing `scripts/guardrails_check.py` GitHub reference verifier | Current verifier only proves a same-repository issue exists and a PR endpoint exists. | Row closure needs stricter PR-number and merge-state validation for production-grade rows. | 2026-07-10 |
| SRC-PROC-001 | `docs/ENGINEERING_PROCESS_RCA.md` and `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | Marker strings and generic docs are not sufficient process evidence. | Closure rows must map to concrete test, CI, drill, or human-only evidence with owner/risk decision. | 2026-07-10 |

## Positive Claims

- Sensitive closure rows accept concrete automated test node IDs, CI run/artifact
  URLs, drill logs, or explicit `human-only` evidence with owner and
  residual-risk decision.
- Sensitive closure rows require same-repository child issue and child PR URLs.
- Sensitive closure rows reject child PR `#64` and require child PR numbers
  distinct from `#64`.
- When GitHub API access is available, sensitive closure rows require child PR
  payloads that prove the PR is merged.

## Negative Invariants

- A row must not close with generic docs-only or Context 0 artifact-only proof.
- A row must not close with `PR #64`, pull request `#64`, or a Context 0 PR URL.
- A row must not close with a child PR URL that exists but is open or unmerged.
- A row must not close with weak human-only wording that lacks owner and
  residual-risk decision language.
- This work must not change product/runtime behavior or close issue `#39`.

## Failure Matrix

| ID | Area | False-Pass Risk | Required Evidence | Planned Test / Gate | Status |
|---|---|---|---|---|---|
| CEH-001 | Evidence type | Docs-only or Context 0 artifact reference appears specific because it names the row ID. | Reject unless validation evidence contains a test node, CI artifact/run, drill log, or explicit human-only owner/risk decision. | `test_phase1_issue39_pull_request_rejects_doc_only_sensitive_closure_evidence` | pass |
| CEH-002 | Context 0 proof | `PR #64` or Context 0 artifact-only references are reused as final row proof. | Reject PR `#64` and Context 0 artifact-only references for sensitive rows. | `test_phase1_issue39_pull_request_rejects_context0_pr64_as_final_row_proof` | pass |
| CEH-003 | Child PR provenance | Existing same-repo PR URL passes even when it is unmerged. | Prefer GitHub API validation and require merged child PR evidence when present. | `test_phase1_issue39_pull_request_rejects_unmerged_child_pr_url` | pass |
| CEH-004 | Child PR distinction | Placeholder or parent/context child PR reference stands in for production-grade child work. | Require same-repo child PR number distinct from `#64`. | `test_phase1_issue39_pull_request_rejects_context0_child_pr_number` | pass |
| CEH-005 | Human-only evidence | Human-only text passes without concrete owner and residual-risk decision. | Accept only explicit `human-only` evidence with owner and risk/residual decision text. | `test_phase1_issue39_pull_request_rejects_weak_human_only_sensitive_evidence` | pass |

## Review Prompt Set

Review the closure-record contract for false-pass paths. Try to disprove that
the guardrail rejects doc-only evidence, Context 0/PR `#64` proof, unmerged child
PRs, and weak human-only evidence. Confirm that `#39` remains reference-only
unless every matrix row is closed by production-grade evidence.

## Stop Rule

Stop and update this contract before further implementation if a review or test
finds a new false-pass class, if a row can close without concrete evidence, or
if the fix would change runtime/product scope.

## Skill / Tool Selection

Preinstalled repo docs and approved skills were checked first:

- `git-workflow-and-versioning`
- `incremental-implementation`
- `test-driven-development`
- `docs/ENGINEERING_PROCESS_RCA.md`
- `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`

No custom skill or plugin is needed.

## Human-Only Surfaces

| Surface | Automation Gap | Owner | Evidence | Residual Risk Decision | Expiry / Revisit Trigger |
|---|---|---|---|---|---|
| Final squash/merge message | CI cannot inspect the final merge dialog text before merge | repo owner | This preflight and PR body reviewer confirmation | Reference-only final message with no issue-closing keyword accepted for PR only | Before merge |

## Pre-Implementation Evidence

| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix | `docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md` | commit order: this preflight file added before guardrail/test edits | Codex | pass |
| Source facts | `docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md` | commit order: this preflight file added before guardrail/test edits | Codex | pass |
| Human-only surfaces, if any | `docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md` | commit order: this preflight file added before guardrail/test edits | Codex | pass |
