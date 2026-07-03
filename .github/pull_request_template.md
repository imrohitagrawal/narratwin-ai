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
- [ ] Implementation or release-readiness changes completed invariant, exploit-matrix, and contract/gate review per `docs/REVIEW_RIGOR_RETROSPECTIVE.md`.
- [ ] PR title, body, branch commit messages, and final merge/squash message plan were checked for automation-sensitive wording such as issue-closing keywords.

## Preflight evidence

For non-trivial changes, link the artifact and summarize matrix coverage:

| Evidence | Artifact path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual risk decision |
|---|---|---|---|---|---|---|
| Intent/spec |  |  |  |  |  |  |
| Source facts |  |  |  |  |  |  |
| Failure matrix |  |  |  |  |  |  |
| Tests |  |  |  |  |  |  |
| Docs/gates |  |  |  |  |  |  |
| Adversarial review |  |  |  |  |  |  |

## Validation evidence

Paste commands/results or link CI run:

```text

```

## Notes for reviewer

- Add notes here, or write `N/A`.
