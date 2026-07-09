# Repository Guardrails

This repository is protected by workflow, review, and policy-as-code guardrails. These rules apply to Codex, humans, and any future automation.

## Non-negotiable rules

1. No direct commits to `main`.
2. Every stage must start from a GitHub issue.
3. Every change must use a dedicated branch.
4. Every change must be merged through a pull request.
5. CI must pass before merge.
6. No secrets, credentials, tokens, provider keys, or private certificates may be committed.
7. Tests must not require paid providers.
8. External services must have mock/local adapters.
9. Provider keys must be read from environment variables only.
10. LLM outputs must include trace/run metadata.
11. Generated scripts and answers must cite source chunks or context IDs.
12. Evaluation failures block merge.
13. Security critical/high findings block merge.
14. Architecture changes require an ADR update under `docs/ADR/`.
15. PRD-impacting changes require `docs/TRACEABILITY.md` updates.
16. GitHub Actions workflows must be YAML-defined.
17. Workflows must use least-privilege `GITHUB_TOKEN` permissions.
18. Repository-tracked stage and governance changes require `docs/STATUS.md` updates.
19. Non-trivial requirements, feature discussions, architecture locks,
    implementation work, release claims, and governance-gate changes must consult
    `docs/ENGINEERING_PROCESS_RCA.md` before coding or final review.

## What is enforced in CI

The `Quality Gates` workflow runs `scripts/guardrails_check.py`,
`scripts/ci/verify_branch_protection.py`, and `make quality` on pull requests
into `main` and on pushes to non-main branches. The required policy gate also
runs on `pull_request.edited` so PR title/body edits cannot add issue-closing
or other automation-sensitive wording after checks are green without rerunning
the guardrail.

The policy check fails CI for:

- workflows without explicit `permissions:`
- workflows that use broad write permissions for pull-request validation
- likely committed secrets
- provider key assignments outside `.env.example`
- missing mock/local provider defaults
- architecture-impacting changes without ADR updates
- PRD-impacting changes without traceability updates
- repository-tracked governance changes without `docs/STATUS.md` updates
- Phase 1 Closure quality drift in the `#39` production-closure matrix, including
  missing required IDs, malformed rows, duplicate or unexpected IDs, and invalid
  status values
- non-trivial pull requests without completed preflight evidence rows for the
  required source, invariant/failure matrix, test, docs/gates, and
  adversarial-review categories in the PR body
- non-trivial pull requests whose failure-matrix IDs are not fully covered by
  test, gate, source, human-only, or non-goal evidence, or whose tests lack
  old-behavior proof language such as RED, mutation, break-test,
  regression-reproduced, or fails-before evidence
- issue-closing keywords in PR title/body/commit messages outside explicitly
  allowed canonical stage issue closures
- drift between live `main` branch-protection settings and the documented
  required status checks and app bindings visible to CI; required PR review,
  admin enforcement, force-push/deletion, and conversation-resolution posture
  remain human-only when GitHub denies protected-branch detail access
- LLM-generation code without trace/run metadata
- generated-script/answer code without source chunk citations
- failing eval result reports
- security reports with critical/high findings

Direct pushes to `main` must be prevented by repository settings such as branch protection or rulesets; the CI policy check is not the enforcement layer for that event.

## Required GitHub repository settings

Some controls must be enabled as repository settings because policy files alone cannot fully prevent admin-level direct pushes.

Enable branch protection or repository ruleset for `main` with:

- Require a pull request before merging.
- Require status checks to pass before merging.
- Required status checks:
  - `policy-gates` from the `Quality Gates` workflow
  - `quality / secrets`
  - `quality / markdown`
  - `lint / typecheck / unit / api`
  - `frontend tests / playwright smoke`
  - `ci / docker build`
  - `secret scan / bandit / audit / semgrep`
  - `security / docker build`
  - `eval smoke`
  - `stage8 / performance lighthouse`
- Require branches to be up to date before merging.
- Block force pushes.
- Block deletions.
- Include administrators, if available on your plan/settings.
- Restrict who can push directly to `main`, if available.

For the current user-owned repository, GitHub rejected direct pusher
restrictions with `Only organization repositories can have users and team
restrictions`; the enforced path is required PR review, strict required checks,
administrator enforcement, blocked force pushes, blocked deletions, and required
conversation resolution.

## Required workflow for every stage

```text
Open issue
→ create branch from main
→ make scoped changes
→ open PR linked to issue
→ pass CI
→ review
→ merge
```

## Required preflight for non-trivial work

Before starting implementation or locking a feature approach, create or link a
reviewable preflight artifact that covers:

- intent and non-goals
- official source facts for platform/tool semantics
- positive claims and negative invariants
- failure-mode matrix
- matrix-to-test mapping
- architecture parity table when behavior repeats across modules
- adversarial review disposition for high-risk work

The pull-request preflight table must include completed rows for the executable
gate categories: intent/spec, source facts, failure matrix, tests, docs/gates,
adversarial review, review prompt set, stop rule, and skill/tool selection.
Completed means `pass` or `passed`; `tracked`, `accepted`, `pending`, `todo`,
and placeholder values do not count as completed evidence. Every matrix ID named
by the failure-matrix row must be covered by a test, executable gate, official
source fact, explicit human-only row, or documented non-goal. Range shorthand
such as `INV-1 through INV-6` is not a valid substitute for explicit matrix IDs.
The declared reference type must match the artifact form. Human-only evidence
must use concrete repo-file or non-placeholder URL references, and
pre-implementation URL evidence must use a specific issue-comment URL or PR URL
rather than a generic issue page. The tests row must state how old behavior was
proven false for changed guardrails, bug fixes, restore/replay paths, and
process-sensitive claims. Failure matrix, review prompt set, stop rule, and
skill/tool selection rows must link PR-specific artifacts; generic governance
docs such as the RCA, learning tracker, retrospective, or new-project playbook
do not count as proof for those rows.

Durability, restore/replay, derived-artifact, release, CI, and governance work
must include an invariant-to-test matrix before implementation. Marker-string
checks are not enough: every required process claim must map to a test, an
executable gate, an official source fact, or an explicitly human-only checklist
item with owner and residual-risk decision. Process-sensitive PRs must also show
pre-implementation evidence proving that the invariant/failure matrix and source
facts existed before implementation or guardrail edits began.
Process-critical governance docs, process-review registers, PR templates, and
quality/guardrail scripts remain non-trivial even for text-only edits. These
files define the review loop and therefore must carry preflight evidence rather
than relying on marker-only wording.

Skill/tool selection evidence must show that installed or approved repo skills,
docs, and tools were checked before creating or installing any custom skill or
plugin. A custom skill/plugin is allowed only when the PR links the unmet
capability gap, rejected existing options, source/pin/license/telemetry and
credential review, approval, `docs/SKILL_LOCK.md`, and
`docs/THIRD_PARTY_NOTICES.md` updates. If a fresh review finds a new defect
class after a fix, the stop-rule evidence must show that implementation paused
for contract rewrite and review-prompt correction before another fix loop.

For process and governance work, the PR template validation artifact is not optional:

- `Validation evidence` in `.github/pull_request_template.md` must include
  the required command references. Actual pull-request bodies must replace the
  template examples with result-bearing lines such as `-> passed` or CI run URLs;
  bare command names, TODO text, and placeholder event paths do not count.

```text
uv run pytest tests/unit/test_guardrails_check.py
uv run pytest tests/unit/test_phase1_closure_docs.py
python3 scripts/guardrails_check.py
make quality
uv run ruff check scripts tests
uv run mypy scripts tests
GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=/path/to/pr-event.json NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1 python3 scripts/guardrails_check.py
```

- The optional branch-protection verifier command is expected when branch-protection
  behavior changed or is directly reviewed:

```text
uv run pytest tests/unit/test_branch_protection_verifier.py
```

The phase-1 process check does not accept marker-only completion or placeholder
values in these fields.

Use `docs/ENGINEERING_PROCESS_RCA.md` for the NarraTwin-specific failure lessons
and `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` when creating a new
project or reusable project template.

## Codex instruction

Codex must not start coding from a vague request. It must first identify or
create the linked issue, create a branch, apply a scoped change, open a PR, and
preserve the guardrails listed here. For non-trivial work, Codex must also apply
the preflight above before treating tests or CI as sufficient evidence.
