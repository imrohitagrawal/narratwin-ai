# Skill Trust Review

This file records the trust and installation review for skills listed in `docs/SKILL_EXECUTION_PLAN.md`.

## Status legend

- `approved-for-stage`: can be installed or used only in the named stage.
- `needs-manual-review`: do not install until license, install behavior, and execution behavior are manually checked.
- `rejected-for-now`: do not install for the current roadmap.

## Rules

1. Do not install all skills at once.
2. Do not paste API keys, GitHub tokens, or provider secrets into any skill installer.
3. Prefer official package/plugin installers over copying skill files.
4. Clone or vendor skill files only when no installer exists and this review approves the exact source.
5. Pin version, release tag, or commit before using a skill in a repeatable build.
6. If a skill changes git hooks, filesystem state, network behavior, telemetry, or CI behavior, record it here before use.
7. Security, privacy, license, and PRD acceptance criteria override skill recommendations.

## Reviewed skills and tools

| Stage | Skill/tool | Source | Install path | Decision | Notes |
|---|---|---|---|---|---|
| Stage 0 | PM Skills | `https://github.com/phuryn/pm-skills` | Codex plugin marketplace and selected `codex plugin add ...` commands | needs-manual-review | Use for PRD, strategy, roadmap, metrics, and PRD red-team only. Do not use for implementation. |
| Stage 1 | GitHub Spec Kit | `https://github.com/github/spec-kit` | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<pinned-tag>` | needs-manual-review | Use for constitution, specs, plan, and tasks. Do not run implementation command until Stage 0 and architecture are approved. |
| Stage 2 | Addy Osmani Agent Skills | `https://github.com/addyosmani/agent-skills` | `npx skills add https://github.com/addyosmani/agent-skills` | needs-manual-review | Use for engineering lifecycle, review, and shipping checklists. Do not let it override NarraTwin PRD scope. |
| Stage 3 | Obra Superpowers | `https://github.com/obra/superpowers` | Codex plugin install if available; otherwise inspect upstream docs | needs-manual-review | Use only if strict TDD/review workflow is needed. Do not invent install commands. |
| Stage 4 | Security and Hardening | `https://www.skills.sh/addyosmani/agent-skills/security-and-hardening` | `npx skills add https://github.com/addyosmani/agent-skills --skill security-and-hardening` | needs-manual-review | Use before upload, prompt-injection, provider, and secrets work. |
| Stage 5 | Python Testing Patterns | `https://www.skills.sh/wshobson/agents/python-testing-patterns` | `npx skills add https://github.com/wshobson/agents --skill python-testing-patterns` | needs-manual-review | Use when FastAPI, RAG, provider mocks, and pytest code are introduced. |
| Stage 5 | Webapp Testing | `https://www.skills.sh/anthropics/skills/webapp-testing` | `npx skills add https://github.com/anthropics/skills --skill webapp-testing` | needs-manual-review | Use after the UI exists and can run locally. |
| Stage 5 | E2E Testing Patterns | `https://www.skills.sh/wshobson/agents/e2e-testing-patterns` | `npx skills add https://github.com/wshobson/agents --skill e2e-testing-patterns` | needs-manual-review | Use for Playwright/Cypress patterns after at least one real UI flow exists. |
| Stage 5 | Vercel Agent Skills | `https://github.com/vercel-labs/agent-skills` | `npx skills add vercel-labs/agent-skills` | needs-manual-review | Use for Next.js frontend quality. Not a product strategy source. |
| Stage 5 | UI/UX Pro Max | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | `npm install -g ui-ux-pro-max-cli` then `uipro init --ai codex` | needs-manual-review | Use for UI polish after functional UI exists. Do not start here. |
| Stage 6 | Project Doc Skills | `https://github.com/imrohitagrawal/project-doc-skills` | Inspect/clone only after review; copy only approved `SKILL.md` folders if needed | needs-manual-review | Use for README, runbooks, architecture docs, and release handoff. Do not blindly vendor whole repo. |
| Stage 6 | Performance Skill | `https://www.skills.sh/addyosmani/web-quality-skills/performance` | `npx skills add https://github.com/addyosmani/web-quality-skills --skill performance` | needs-manual-review | Use after UI/API flows exist. Do not optimize before the first slice works. |
| Stage 7 | Wednesday AI Agent Skills | `https://github.com/wednesday-solutions/ai-agent-skills` | `npx @wednesday-solutions-eng/ai-agent-skills install` | needs-manual-review | Use after meaningful code exists for codebase map, dependency graph, and guardrails. |

## Skill activation order

1. Stage -1: Complete this trust review.
2. Stage 0: Install/use only PM and spec skills for product strategy and PRD hardening.
3. Stage 1: Use architecture, ADR, security, and AI safety review skills.
4. Stage 2: Add repo quality gates and local validation wrappers.
5. Stage 3: Implement Slice 1 using TDD and backend/provider/RAG testing skills.
6. Stage 4: Add UI/E2E skills only after a working UI exists.
7. Stage 5: Add performance, documentation, and codebase intelligence skills only after meaningful code exists.

## Stop/go gates

### Before coding

- `docs/PRODUCT_STRATEGY.md` is specific to NarraTwin AI.
- `docs/PRD.md` has implementation-ready user journeys, requirements, non-goals, NFRs, risks, and acceptance criteria.
- `docs/ARCHITECTURE.md` defines module boundaries, data flow, trust zones, provider contracts, and evaluation flow.
- `docs/SECURITY_AND_PRIVACY.md` defines upload, secret, consent, provider, and prompt-injection controls.
- `docs/AI_SAFETY_AND_EVALUATION.md` defines hard gates and required tests.
- `docs/THIRD_PARTY_NOTICES.md` has no unresolved licensing blockers for the planned slice.

### Before merging Slice 1

- Local quality gates pass.
- GitHub Actions `quality` workflow passes.
- Tests cover happy path and at least one failure/refusal path.
- Unsupported claims are flagged or refused.
- Uploaded documents are treated as untrusted input.
- No paid provider key is required.
- Docs and known limitations are updated.

## Conflict resolution

1. Security, privacy, consent, and license constraints win.
2. PRD acceptance criteria win over broad implementation suggestions.
3. ADRs win over ad-hoc architecture suggestions.
4. TDD failures block progress.
5. Vertical-slice scope wins over skeleton expansion.
6. Human-readable docs must be updated when decisions change.
