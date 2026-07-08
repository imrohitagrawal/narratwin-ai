## Linked issue

Refs #

If this PR is intentionally meant to close an issue, state the exact closing
keyword and issue here and explain why closure is correct. Otherwise use
reference-only wording.

## Stage / slice

- Stage:
- Branch:
- Scope:

## Summary

- Describe the change in one or two bullets.

## Guardrail checklist

- [ ] This PR was created from a tracked GitHub issue.
- [ ] No direct commits were made to `main`.
- [ ] CI passes before merge.
- [ ] No secrets, tokens, credentials, or provider keys are committed.
- [ ] Tests run without paid providers or real provider keys.
- [ ] External services use mock/local adapters by default.
- [ ] Provider keys are read only from environment variables.
- [ ] LLM outputs include trace/run metadata where applicable.
- [ ] Generated scripts/answers cite source chunks where applicable.
- [ ] Eval failures block this PR.
- [ ] Security critical/high findings block this PR.
- [ ] Architecture-impacting changes include an ADR update under `docs/ADR/`.
- [ ] PRD-impacting changes update `docs/TRACEABILITY.md`.
- [ ] Repository-tracked stage/governance changes update `docs/STATUS.md`.
- [ ] Implementation or release-readiness changes checked `docs/PROJECT_LEARNINGS_TRACKER.md`.
- [ ] Non-trivial changes link a completed preflight artifact per `docs/ENGINEERING_PROCESS_RCA.md` and `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`.
- [ ] Durability, restore/replay, artifact, release, CI, or governance/process work includes an invariant-to-test matrix link before implementation.
- [ ] Negative tests were added or explicitly marked human-only/source/non-goal in the invariant matrix.
- [ ] Old behavior fails, RED, mutation, break-test, or regression-reproduction evidence is listed for changed guardrails and bug fixes.
- [ ] Human-only review surfaces are listed with owner and residual-risk decision.
- [ ] Process/durability/governance work considered whether `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` should receive reusable lessons for future projects/apps.
- [ ] Implementation or release-readiness changes completed invariant, exploit-matrix, and contract/gate review per `docs/REVIEW_RIGOR_RETROSPECTIVE.md`.
- [ ] PR title, body, branch commit messages, and final merge/squash message plan were checked for automation-sensitive wording such as issue-closing keywords.

## Preflight evidence

For non-trivial changes, link concrete artifacts and summarize matrix coverage.
Artifact path / URL values must be real repo files, file line/anchor refs, PR or
CI links, or source links; placeholder rows do not count. Completion status must
be `pass` or `passed`.

| Evidence | Artifact reference | Reference type | Matrix IDs | Command / CI / Source | Reviewer | Evidence type | Completion status | Residual risk decision |
|---|---|---|---|---|---|---|---|---|
| Intent/spec |  | repo-file / PR-comment / CI-run / source-URL |  |  |  | source |  |  |
| Source facts |  | repo-file / PR-comment / CI-run / source-URL |  |  |  | source |  |  |
| Failure matrix / invariant matrix |  | repo-file / PR-comment |  |  |  | matrix |  |  |
| Tests / old-behavior proof |  | repo-file / CI-run |  |  |  | test |  |  |
| Docs/gates |  | repo-file / CI-run |  |  |  | gate |  |  |
| Adversarial review |  | repo-file / PR-comment |  |  |  | source / human-only |  |  |

## Human-only review surfaces

List surfaces CI cannot fully verify, such as final squash/merge message text,
repository settings unavailable to CI, provider dashboards, legal/license
approval, or release communications. Use an explicit `N/A` row only when no
human-only surface remains.

| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Pre-implementation evidence

For process-sensitive work, show that the invariant/failure matrix and source
facts existed before implementation code or guardrail edits began.

| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix |  |  |  |  |
| Source facts |  |  |  |  |
| Human-only surfaces, if any |  |  |  |  |

## Validation evidence

Paste commands/results or link CI run:

```text

```

## Notes for reviewer

- Add notes here, or write `N/A`.
