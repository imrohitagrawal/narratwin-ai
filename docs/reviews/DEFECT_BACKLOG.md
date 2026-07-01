# Final Review Defect Backlog

Date: 2026-07-01

Linked stage issue: `#6`

## Open Defects

| ID | Severity | Title | Evidence | Issue |
|---|---|---|---|---|
| FR-DEF-001 | Blocker | Governance and release docs are stale after Stage 8 merge. | Git shows `fb40113` merged PR `#33` on `main`, but `docs/STATUS.md` still records PR `#33` as open/not merged and Final Review as pending; `docs/RELEASE_CHECKLIST.md` remains unchecked pre-release; `docs/RUNBOOK.md` still points monitoring at PR `#33`. | `#35` |
| FR-DEF-002 | Blocker | Final Review has no executable quality gate. | `make final-review-quality` intentionally fails with `Final Review quality gate is not implemented yet`; `make quality` dispatches to Stage 8 and rejects `final-review-independent-review`. | `#36` |
| FR-DEF-003 | High | Local principal contract does not match implementation/tests. | Docs require fixed `tenant_local` / `user_local`; `backend/app/main.py` accepts `X-Local-User-Id`; tests assert `alice` and `bob` local principals. | `#37` |
| FR-DEF-004 | Blocker | Canonical requirements traceability matrix is stale. | `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` still marks implemented Stage 4-7/NFR rows as `Planned`, while `docs/TRACEABILITY.md` contains later implementation evidence. | `#40` |
| FR-DEF-005 | Blocker | Portfolio demo docs omit required durability disclosure. | `docs/reviews/GO_NO_GO.md` requires single-process/non-durable disclosure for conditional demo use, but `portfolio/README.md` does not state that limit. | `#41` |
| FR-DEF-006 | High | Stage 7 source evidence checksum binding is weaker than contract. | API route passes a source evaluation checksum derived from evaluation/status/context/citation fields, while the service default includes source run and trace identity. | `#42` |

## Non-Blocking Defects And Follow-Ups

| ID | Severity | Title | Evidence | Follow-up |
|---|---|---|---|---|
| FR-DEF-007 | Medium | Release evidence cannot prove GitHub branch protection from local repo state. | Stage 8 release checklist requires branch protection/rulesets for specific contexts, but no local artifact proves repository settings. | Issue `#38`. |
| FR-DEF-008 | Medium | Production runbook is intentionally incomplete for real deployment. | `docs/RUNBOOK.md` says production dashboards, alert routes, and first-hour monitoring are Final Review blockers. | Issue `#39`. |
| FR-DEF-009 | Low | Playwright smoke path emits Next standalone warning. | Escalated smoke test passed, but Next warned that `next start` does not match standalone output guidance. | Update smoke command or document accepted local behavior. |
| FR-DEF-010 | Medium | CI issue-link guardrail does not map every later stage to the canonical issue. | `scripts/guardrails_check.py` has explicit canonical branch issue checks for Stage 2/3 only. | Extend governance check when implementing Final Review gate. |
| FR-DEF-011 | Medium | Frontend smoke is UI workflow coverage, not full integrated backend E2E. | Playwright intercepts `**/api/v1/**` and fulfills mock responses in-browser. | Issue `#43`. |

## Verification Snapshot

Passing checks during this pass:

- `python3 scripts/guardrails_check.py`
- `python3 scripts/quality/check_recommended_review_items.py "Final Review"`
- `uv run pytest tests/unit tests/api` with 103 passing tests
- `bash scripts/ci/backend-lint.sh`
- `bash scripts/ci/eval-smoke.sh`
- `bash scripts/ci/frontend-build.sh`
- `bash scripts/ci/dependency-security.sh` after network escalation
- `PLAYWRIGHT_SKIP_INSTALL=1 bash scripts/ci/frontend-smoke.sh` after local-port escalation
- `uv run pytest --cov=backend --cov=scripts --cov-report=term-missing tests/unit tests/api`; 103 passed, aggregate coverage 75%
- `npm --prefix frontend audit --audit-level=high` after network escalation; no high/critical audit failure, 17 moderate dev-tool transitive findings

Expected failing checks during this pass:

- `make quality`, because `.stage/current = 8` dispatches to Stage 8 and rejects the `final-review-*` branch.
- `make final-review-quality`, because Final Review quality is intentionally not implemented.

Sub-agent review added issues `#40` through `#44`; no additional product fixes were made in this pass.
