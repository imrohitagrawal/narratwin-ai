## Linked issue

Refs #

If this PR is intentionally meant to close an issue, state the exact closing
keyword and issue here and explain why closure is correct. Otherwise use
reference-only wording.

<!-- narratwin-live-state:start -->
<!-- Automation-owned managed block. Do not edit its contents. The trusted
workflow replaces it after every head change; use `make pr-reconcile PR=<number>`
after the final push. Do not duplicate current CI status in prose. -->
<!-- narratwin-live-state:end -->

## Product and reviewer context

<!-- Required for non-trivial PRs. Complete every point with self-contained,
PR-specific plain English. Issue references and links are supplemental evidence,
not substitutes for the explanation. -->

### 1. End product goal
<!-- Describe NarraTwin's end product goal and how this PR relates to it. -->

### 2. Current state
<!-- State what works today and what remains incomplete before this PR. -->

### 3. Problem being addressed
<!-- Describe the user or product problem without relying on an issue number or link. -->

### 4. Exact changes in this PR

#### Reviewer impact summary
<!-- Required: replace each instruction below with a distinct, PR-specific
answer. Keep all seven labels and their order. Use `None` only with a specific
reason. Automation verifies structure and known false-pass mutations; the
reviewer judges truth, completeness, and clarity. -->

- **Purpose:** <!-- Why does this change matter now? State the reviewer/user/product need. -->
- **Behavior before/after:** <!-- What observable behavior or governed state existed before, and what will exist after merge? -->
- **Who and what is affected:** <!-- Name affected users, operators, reviewers, systems, interfaces, workflows, and data. State what is unchanged. -->
- **Artifacts/capabilities:** <!-- What content, media, outputs, files, evidence, or capabilities are added, changed, removed, or explicitly absent? -->
- **Operational impact:** <!-- State runtime/provider/network/spend/persistence effects, migrations, compatibility, failure behavior, rollback, and rollout needs. Governance/docs-only PRs must explain why these are unchanged. -->
- **Scope boundaries:** <!-- What does this PR deliberately not change, authorize, prove, deploy, release, or make production-ready? -->
- **End-to-end impact:** <!-- What blocker is removed, what later capability is unlocked, and what gap or gate remains? -->

<!-- A file/test list, issue/link reference, implementation detail, copied
instruction, or evidence table is not a substitute for truthful answers. -->

#### Technical change list
<!-- List the concrete behavior, documents, components, and boundaries changed by this PR.
If this section claims a number of fields, changes, controls, checks, items,
components, files, paths, rules, or requirements, enumerate every counted item
as a distinct, meaningful Markdown list entry. -->

### 5. What is complete after merge
<!-- State the verified repository or product state that will exist after merge. -->

### 6. Expected outcome
<!-- Describe what users, operators, reviewers, or later work should be able to expect. -->

### 7. Not expected / out of scope
<!-- State what this PR deliberately does not change, authorize, or prove. -->

### 8. End-goal impact
<!-- Explain whether this PR advances the end-to-end demo, removes a dependency,
establishes production-path evidence, or does not directly advance product behavior. -->

### 9. Remaining gap
<!-- State what still prevents the end-to-end demo, production readiness, or release. -->

### 10. Reviewer validation

Expected behavior: <!-- State the expected product or repository behavior. -->

Prohibited behavior: <!-- State what must remain false or unchanged. -->

Evidence: <!-- Name the tests, artifacts, or observations that prove the claims. -->

Pass condition: <!-- State the exact outcome that makes review pass. -->

Fail condition: <!-- State the exact outcome that must block approval. -->

## Reviewer overview

<!-- Required for non-trivial PRs. Complete all five points with PR-specific content before the evidence tables. -->

### 1. What changed and why
<!-- Explain the change and the problem or need it addresses in plain language. -->

### 2. Scope
- In scope: <!-- Describe what the PR changes. -->
- Out of scope: <!-- Describe what it intentionally does not change. -->

### 3. Key files and components
<!-- Identify the main files, modules, workflows, or documents affected. -->

### 4. Reviewer focus
<!-- Tell the reviewer which decisions, risks, invariants, or behaviors deserve close attention. -->

### 5. Validation, limitations, and residual risks
<!-- Summarize tests and checks, known limitations, remaining risks, and human-only decisions. -->

## Human verification checklist

For non-trivial PRs, turn the reviewer-focus points above and every changed
high-risk surface into a self-serve verification checklist. Do not leave
reviewers dependent on implementer memory, private notes, or follow-up questions
for load-bearing facts. Each row must state the exact source/data/artifact to
inspect, including official source URL and verified/accessed date when the fact
can change, what would make the claim pass or fail, and who owns the residual
risk decision. Use `N/A - trivial change` only for genuinely trivial PRs.

Add rows when relevant for provider/tool choice, pricing, quota, latency,
capacity, retry/backoff/timeout behavior, user-facing/demo/recruiter flows,
uploads, prompts, transcripts, provider outputs, model outputs, consent,
deletion/erasure, disclosure, provenance, AI/RAG/generated-media claims,
citations, source-run/eval/media binding, launch boundaries, production posture,
and final merge-message wording.

| Focus area | What to verify | Data/source/artifact to verify | Pass condition | Fail condition | Residual-risk owner |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

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
- [ ] Non-trivial reviewer-focus points and changed high-risk surfaces are captured in the Human verification checklist with exact data/source/artifact references, official URL and verified/accessed date where facts can change, pass/fail criteria, and residual-risk owner.
- [ ] Preinstalled repo docs/approved skills were checked first; no custom skill/plugin was created or used unless the gap, rejected existing options, approval, `docs/SKILL_LOCK.md`, and `docs/THIRD_PARTY_NOTICES.md` updates are linked.
- [ ] Repeated-review stop rule was evaluated; if a fresh review found a new defect class after a fix, implementation paused for contract rewrite before another bug-fix loop.
- [ ] Process/durability/governance work considered whether `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` should receive reusable lessons for future projects/apps.
- [ ] Implementation or release-readiness changes completed invariant, exploit-matrix, and contract/gate review per `docs/REVIEW_RIGOR_RETROSPECTIVE.md`.
- [ ] PR title, body, branch commit messages, and final merge/squash message plan were checked for automation-sensitive wording such as issue-closing keywords.
- [ ] Adversarial-framework changes keep stimuli separate from test-owned expectations and show the executor received stimulus only.
- [ ] Adversarial-framework candidate review states remain `PENDING_EXTERNAL_REVIEW`; every PASS links an eligible independent reviewer receipt for the exact head/tree.
- [ ] Mutation claims distinguish C2 test-oracle discrimination from C4 execution against the frozen production executor.
- [ ] The Issue #435 phase, corpus identity, path/cap, readability, correction-wave, and post-freeze stop rules were checked when applicable.

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

For Issue #435, state the immutable-runner result as exact typed RED,
`CONTRACT_FAILURE`, or `INFRASTRUCTURE_FAILURE`; a generic
nonzero `make` result is insufficient. List the exact candidate head/tree,
corpus semantic identity, 40-failure RED count, 12 executed/killed test-mutant
receipts, C1 blob, protected-source digest, charged-line totals, and four external
review dispositions. Never describe C2/C3 as merge-ready or implemented.
