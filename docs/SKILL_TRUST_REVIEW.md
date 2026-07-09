# Skill Trust Review

This file is the historical Stage 0 trust review for locked skill and workflow
sources. It is not the current activation ledger. Use `docs/SKILL_LOCK.md` as
the authoritative current skill/tool activation record and
`docs/SKILL_EXECUTION_PLAN.md` for allowed stage use.

No skills were installed or activated for product implementation in Stage 0.

## Decision legend

- `reference-only`: may be read as local guidance but not installed or activated for product work
- `needs-manual-review`: pin, license, install path, telemetry, and side effects must be reviewed before activation
- `approved-for-stage`: approved only for the named stage after lock fields are complete

## Stage model

The trust review follows the current repo stage sequence:

1. Stage 0: Codex operating model and skill lock
2. Stage 1: Product strategy and PRD v1.0
3. Stage 2: Architecture, security, AI safety
4. Stage 3: Repo foundation and CI/CD quality gates
5. Stage 4: Project upload to grounded script generation
6. Stage 5: Evaluations, guardrails, observability
7. Stage 6: Multilingual scripts, subtitles, voice adapter
8. Stage 7: Avatar rendering adapter and export
9. Stage 8: Performance, security hardening, release readiness
10. Final Review: Independent review

## Reviewed sources

| Active stage | Skill/tool | Source | Decision | Notes |
|---|---|---|---|---|
| Stage 0 | Addy Osmani Agent Skills | `https://github.com/addyosmani/agent-skills` | reference-only | Used only as local reading guidance in Stage 0. No install or activation performed. |
| Stage 0 | Agent Skills Standard | `https://github.com/agentskills/agentskills` | reference-only | Recorded as a governance source only. No install or activation performed. |
| Stage 1 | PM Skills | `https://github.com/phuryn/pm-skills` | needs-manual-review | Intended for strategy, PRD, metrics, roadmap, and PRD red-team review after pin and license verification. |
| Stage 2 and Stage 3 | GitHub Spec Kit | `https://github.com/github/spec-kit` | needs-manual-review | Intended for constitution, spec, plan, and tasks after immutable version review. Implementation commands remain blocked until Stage 4. |
| Stage 3 through Final Review | GitHub Actions workflow actions | `https://github.com/actions/checkout`, `https://github.com/actions/setup-python`, `https://github.com/actions/upload-artifact` | needs-manual-review | Existing CI dependencies; immutable action version review is still required. |
| Stage 3 through Stage 8 | Gitleaks GitHub Action | `https://github.com/gitleaks/gitleaks-action` | needs-manual-review | Existing CI secret-scan dependency; immutable action version review is still required. |
| Stage 3 through Final Review | Markdownlint CLI2 Action | `https://github.com/DavidAnson/markdownlint-cli2-action` | needs-manual-review | Existing CI markdown gate dependency; immutable action version review is still required. |

## Rules

1. Do not install all skills at once.
2. Do not paste API keys, GitHub tokens, or provider secrets into any skill installer.
3. Prefer official installers over copying skill files.
4. Do not commit `.codex` cache, vendor, auth, config, or plugin runtime state.
5. Pin version, release tag, or commit SHA before using a skill or workflow source in a repeatable build.
6. Record filesystem, network, telemetry, hook, and credential side effects before activation.
7. Security, privacy, consent, license, and stage-gate constraints override skill recommendations.
