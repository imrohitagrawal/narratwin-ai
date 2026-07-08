# Process Hardening Review Findings

This register deduplicates the governance/process hardening feedback collected
for PR `#54` follow-up work. It is intentionally separate from product
durability findings so the process defects can be tracked without implying new
product implementation.

## Review Sources

| Source ID | Review Type | Scope | Date | Notes |
|---|---|---|---|---|
| R1 | Sub-agent docs review | RCA and new-project playbook | 2026-07-08 | Focused on completeness and future-project reuse. |
| R2 | Sub-agent enforcement review | PR template, guardrails, quality docs, Phase 1 gate | 2026-07-08 | Focused on false-pass and false-positive behavior. |
| R3 | Sub-agent test review | Guardrail tests and validation story | 2026-07-08 | Focused on missing negative tests and misleading local validation. |
| R4 | Cross-model Codex review | Same process artifact scope | 2026-07-08 | Read-only `codex exec`; confirmed live parser false-passes. |
| R5 | Blind review | Remote branch `3acee0e` over `main` | 2026-07-09 | Independent clone; did not receive prior findings. Some rows are superseded by current local edits. |

## Status Values

- `Open`: accepted finding that still needs a fix or explicit risk decision.
- `Partially addressed`: current working tree reduces the issue but does not
  close it.
- `Closed by local edits`: current working tree includes executable or
  documented remediation that satisfies the acceptance criteria.
- `Superseded by local edits`: valid against the blind-review snapshot, but the
  current working tree already contains a direct remediation.
- `Needs triage`: may be valid, but needs an owner decision before changing
  gates or docs.

## Findings Register

| ID | Severity | Status | Finding | Primary Files | Sources | Acceptance Criteria |
|---|---|---|---|---|---|---|
| PHF-001 | Critical | Closed by local edits | Preflight invariant/test mapping can still false-pass with partial ID overlap, marker words, or copied matrix IDs. | `scripts/guardrails_check.py`, `tests/unit/test_guardrails_check.py` | R2, R3, R4 | Guardrail now requires every failure-matrix ID to map to test/gate/source/human-only/non-goal evidence and tests reject partial coverage and range shorthand. |
| PHF-002 | Critical | Closed by local edits | `tracked` and `accepted` statuses count as completed preflight evidence. | `scripts/guardrails_check.py`, `tests/unit/test_guardrails_check.py` | R3, R4 | Guardrail now counts only `pass`/`passed` as completed and tests reject `tracked`/`accepted`. |
| PHF-003 | High | Closed by local edits | Preflight artifact validation accepts syntactic placeholder URLs and broad existing paths. | `scripts/guardrails_check.py`, `tests/unit/test_guardrails_check.py` | R2, R3, R4 | Guardrail now rejects directories, invalid reference types, mismatched reference types, and placeholder hosts while accepting concrete file line/anchor references. |
| PHF-004 | High | Closed by local edits | Human-only review surfaces are documented, but the guardrail does not parse or enforce the human-only table, and docs need a stricter rule for when human-only is allowed. | `.github/pull_request_template.md`, `docs/ENGINEERING_PROCESS_RCA.md`, `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`, `scripts/guardrails_check.py` | R1, R2, R4, R5 | Guardrail now requires a concrete human-only surface row when human-only evidence is used, or an explicit `N/A` row otherwise, and rejects placeholder evidence URLs. |
| PHF-005 | High | Closed by local edits | "Before implementation" can be backfilled because no temporal evidence is required. | `docs/ENGINEERING_PROCESS_RCA.md`, `.github/pull_request_template.md`, `scripts/guardrails_check.py` | R1, R4 | PR template and guardrail now require pre-implementation evidence with pre-code timestamp, reviewer signoff, concrete issue/draft PR link, or commit ordering. |
| PHF-006 | High | Closed by local edits | The Phase 1 gate cannot prove a governance-only follow-up because `phase-1-closure-39-*` still allowlists runtime/product durability files. | `scripts/quality/check_phase1_closure_docs.py`, `docs/QUALITY_GATES.md`, `docs/STAGE_ISSUE_PLAN.md` | R2, R3, R4 | Phase 1 gate now has a `phase-1-closure-process-*` mode that allows governance guardrail files and rejects product runtime files. |
| PHF-007 | Medium | Open | Stage 6 restore invariants cover derived artifacts internally but do not bind them back to source run, retrieved context, evaluation, citation, and claim-support graph evidence. | `docs/ENGINEERING_PROCESS_RCA.md`, `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | R1, R4 | Add Stage 6 source-evidence binding invariants and matrix rows comparable to Stage 7 source run/evaluation/citation binding. |
| PHF-008 | Medium | Partially addressed | RCA and playbook matrix examples are too omnibus, and sample rows using `pending` conflict with rules that pending rows block implementation. | `docs/ENGINEERING_PROCESS_RCA.md`, `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | R1, R4 | Examples now avoid `pending` status and state that partial overlap is insufficient; future work should split any remaining omnibus rows into narrower one-invariant examples. |
| PHF-009 | Medium | Open | Canonical issue-closing exceptions are hard-coded only for Stage 2 and Stage 3, despite docs describing canonical-stage exceptions generally. | `scripts/guardrails_check.py`, `tests/unit/test_guardrails_check.py`, `docs/REPOSITORY_GUARDRAILS.md` | R2, R4 | Either document that only Stage 2/3 may auto-close, or extend canonical issue mapping/tests for all approved stage branches that intentionally close their canonical issue. |
| PHF-010 | Medium | Open | Local `python3 scripts/guardrails_check.py` does not exercise PR-body checks without a synthetic `pull_request` event payload. | `scripts/guardrails_check.py`, `Makefile`, `docs/QUALITY_GATES.md`, `tests/unit/test_guardrails_check.py` | R3, R4 | Document the limitation clearly and add a local fixture command or test path that runs the PR-body guardrail through the CLI/event payload path. |
| PHF-011 | Medium | Open | Required validation command evidence is not enforced by the PR template or Phase 1 process gate. | `.github/pull_request_template.md`, `scripts/quality/check_phase1_closure_docs.py` | R3 | Add explicit validation evidence rows or gate checks for the required commands when guardrail/process files change. |
| PHF-012 | Medium | Open | The Phase 1 process-doc gate remains marker-heavy and brittle, including exact workflow event string checks and substring checks for process docs. | `scripts/quality/check_phase1_closure_docs.py` | R2, R5 | Parse workflow YAML or otherwise check for `pull_request.edited` semantically, and require required headings/tables rather than incidental marker strings. |
| PHF-013 | Medium | Needs triage | Non-trivial PR classification may be too broad for trivial governance-doc edits. | `scripts/guardrails_check.py` | R5 | Decide whether trivial pure-doc edits need a skip path, small-change exemption, or the full preflight table. |
| PHF-014 | Medium | Closed by local edits | Branch-protection process docs should explicitly require fail-closed behavior for API, permission, partial-data, and renamed-context failures. | `docs/ENGINEERING_PROCESS_RCA.md`, `docs/QUALITY_GATES.md`, `scripts/ci/verify_branch_protection.py` | R1 | Verifier tests now reject context-only/partial payloads, live CI remains fail-closed for branch-summary context drift, and protected-branch detail endpoint permission limits are documented as human-only. |
| PHF-015 | Low | Superseded by local edits | Blind review found the PR template missing human-only surfaces, negative tests, old-behavior proof, and playbook-reuse checks. | `.github/pull_request_template.md` | R5 | Current working tree adds those template surfaces; keep covered by `PHF-004`, `PHF-011`, and process-gate checks. |
| PHF-016 | Low | Superseded by local edits | Blind review found no concrete RCA durability restore checklist. | `docs/ENGINEERING_PROCESS_RCA.md` | R5 | Current working tree adds the checklist; remaining improvements are tracked in `PHF-007` and `PHF-008`. |
| PHF-017 | Low | Superseded by local edits | Blind review found missing playbook sections for executable invariants, derived artifacts, governance false-pass, human-only surfaces, and Definition of Done. | `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` | R5 | Current working tree adds those sections; remaining enforcement/precision gaps are tracked in `PHF-004`, `PHF-007`, and `PHF-008`. |
| PHF-018 | Low | Superseded by local edits | Blind review found bad partial fixes and invariant-to-test matrix template were implicit rather than labeled in the RCA. | `docs/ENGINEERING_PROCESS_RCA.md` | R5 | Current working tree adds labeled sections; keep examples granular per `PHF-008`. |

## Current Priority

Keep `PHF-007` through `PHF-013` available for follow-up triage. `PHF-001`
through `PHF-006` and `PHF-014` are closed in the current working tree and
should stay covered by guardrail, branch-protection, and Phase 1 closure-gate
tests before merge.
