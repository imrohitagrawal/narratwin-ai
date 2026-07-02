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

## What is enforced in CI

The `Quality Gates` workflow runs `scripts/guardrails_check.py`,
`scripts/ci/verify_branch_protection.py`, and `make quality` on pull requests
into `main` and on pushes to non-main branches.

The policy check fails CI for:

- workflows without explicit `permissions:`
- workflows that use broad write permissions for pull-request validation
- likely committed secrets
- provider key assignments outside `.env.example`
- missing mock/local provider defaults
- architecture-impacting changes without ADR updates
- PRD-impacting changes without traceability updates
- repository-tracked governance changes without `docs/STATUS.md` updates
- drift between live `main` branch-protection required status contexts and the
  documented required context set
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

## Codex instruction

Codex must not start coding from a vague request. It must first identify or create the linked issue, create a branch, apply a scoped change, open a PR, and preserve the guardrails listed here.
