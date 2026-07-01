# Skill Lock

This file records approved skill and workflow sources for NarraTwin AI. A source is not approved for use until its pin/version and license status are reviewed for the stage where it is active.

| Capability | Source URL | Pin/version status | License status | Purpose | Active stage | Activation status |
|---|---|---|---|---|---|---|
| PM Skills | `https://github.com/phuryn/pm-skills` | Pending Stage 1 activation; immutable tag or commit SHA required before use | Must be verified before activation | Product discovery, product strategy, PRD, metrics, roadmap, PRD red-team review | Stage 1 | Not activated in Stage 0 |
| GitHub Spec Kit | `https://github.com/github/spec-kit` | Pending Stage 2 or Stage 3 activation; immutable release or commit SHA required before use | Must be verified before activation | Constitution, specs, implementation plans, task breakdown, task-to-issue workflow | Stage 2 and Stage 3 planning; implementation commands blocked until Stage 4 | Not activated in Stage 0 |
| Addy Osmani Agent Skills | `https://github.com/addyosmani/agent-skills` | Pending stage-specific activation; immutable tag or commit SHA required before use | Must be verified before activation | Engineering lifecycle guidance for CI/CD, security, TDD, code review, performance, and release readiness | Stage 0 guidance only; Stage 3 through Stage 8 after activation | Not activated for product implementation in Stage 0 |
| Agent Skills Standard | `https://github.com/agentskills/agentskills` | Pending verification of repository pin before adoption | Must be verified before activation | Standard format for portable `SKILL.md` instructions | Stage 0 governance and future skill packaging | Not activated for product implementation in Stage 0 |
| GitHub Action: Checkout | `https://github.com/actions/checkout` | Workflow pin managed in `.github/workflows/quality*.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Check out repo contents in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| GitHub Action: Setup Python | `https://github.com/actions/setup-python` | Workflow pin managed in `.github/workflows/quality-gates.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Provision Python runtime for guardrail checks in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| GitHub Action: Setup Node | `https://github.com/actions/setup-node` | Workflow pin managed in `.github/workflows/*.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Provision Node.js runtime for frontend checks in CI | Stage 3 through Final Review | Stage 3 CI reference; not a product implementation dependency |
| GitHub Action: Upload Artifact | `https://github.com/actions/upload-artifact` | Workflow pin managed in `.github/workflows/eval-smoke.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Upload eval smoke artifacts | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| Gitleaks GitHub Action | `https://github.com/gitleaks/gitleaks-action` | Workflow pin currently managed in `.github/workflows/security.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Dedicated secret scanning in CI | Stage 3 through Stage 8 | Existing CI reference; not a product implementation dependency |
| GitHub Action: Markdownlint CLI2 | `https://github.com/DavidAnson/markdownlint-cli2-action` | Workflow pin managed in `.github/workflows/quality.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Markdown quality checks in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| UI/UX Pro Max Skill | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | CLI package verified locally as `ui-ux-pro-max-cli@2.10.0`; immutable repository commit pin still required before release dependency claims | MIT per npm package metadata; keep license under review before release | UI/UX design intelligence for Stage 7 avatar rendering/export workflow design review | Stage 7 | Activated locally for design guidance only via `uipro init --ai codex`; generated `.codex` files remain ignored and must not be committed |

## Lock Rules

- Do not activate a source with unclear license, telemetry, filesystem, network, hook, or credential behavior.
- Do not commit `.codex` cache, vendor, auth, config, or plugin runtime state.
- Do not run implementation-oriented skills in Stage 0.
- Update this file in the same PR that activates or changes a skill source.
- Update `docs/THIRD_PARTY_NOTICES.md` when a third-party package, tool, skill, model, API, dataset, provider, media asset, or generated sample is introduced.
