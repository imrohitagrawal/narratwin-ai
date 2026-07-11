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
- [ ] Preinstalled repo docs/approved skills were checked first; no custom skill/plugin was created or used unless the gap, rejected existing options, approval, `docs/SKILL_LOCK.md`, and `docs/THIRD_PARTY_NOTICES.md` updates are linked.
- [ ] Repeated-review stop rule was evaluated; if a fresh review found a new defect class after a fix, implementation paused for contract rewrite before another bug-fix loop.
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
| Review prompt set |  | repo-file / PR-comment |  |  |  | source / human-only |  |  |
| Stop rule / repeated blocker reset |  | repo-file / PR-comment |  |  |  | gate / human-only |  |  |
| Skill/tool selection |  | repo-file / PR-comment |  |  |  | source / gate |  |  |

## Human-only review surfaces

List surfaces CI cannot fully verify, such as final squash/merge message text,
repository settings unavailable to CI, provider dashboards, legal/license
approval, or release communications. Guarded non-trivial PRs must include the
final squash/merge message row because CI cannot inspect the merge dialog text
before merge.

| Surface | Automation gap | Owner | Evidence | Residual risk decision | Expiry / revisit trigger |
|---|---|---|---|---|---|
| Final squash/merge message | CI cannot inspect the final merge dialog text before merge | repo owner | PR body / reviewer confirmation | reference-only final message with no issue-closing keyword accepted for PR only | before merge |

## Pre-implementation evidence

For process-sensitive work, show that the invariant/failure matrix and source
facts existed before implementation code or guardrail edits began. Use a
specific `#issuecomment-...` URL, PR URL, or verified commit-order statement;
generic issue-page URLs do not count.

| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix |  |  |  |  |
| Source facts |  |  |  |  |
| Human-only surfaces, if any |  |  |  |  |

## Validation evidence

Paste commands/results or link CI run. Bare command names, `TODO`/`not run`
markers, and placeholder event paths do not satisfy PR guardrails:

```text
uv run pytest tests/unit/test_guardrails_check.py
uv run pytest tests/unit/test_phase1_closure_docs.py
python3 scripts/guardrails_check.py
make quality
uv run ruff check scripts tests
uv run mypy scripts tests
make ci
make security
make dependency-audit
make container-scan
make secrets-scan
make eval
GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/path/to/pr-event.json NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py
# Optional when changed:
# uv run pytest tests/unit/test_branch_protection_verifier.py
```

## Notes for reviewer

- Add notes here, or write `N/A`.
