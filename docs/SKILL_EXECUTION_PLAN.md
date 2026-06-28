# Skill Execution Plan: NarraTwin AI

This document defines **which AI/Codex skills to install, where to install them from, when to use them, what they must produce, and when they must not be active**.

The goal is to prevent skill overload, conflicting instructions, shallow scaffolding, and low-quality autonomous implementation.

---

## 1. Critical clarification

This file is an **execution plan**, not the installed skills themselves.

Codex must not guess where skills come from. Every skill must have:

- source repository or registry URL
- install command
- stage of use
- expected artifact/output
- trust/license review entry

Before installing or using any external skill, Codex must create or update:

```text
docs/SKILL_TRUST_REVIEW.md
```

---

## 2. Install strategy

Do **not** install every skill at once.

Use this order:

```text
Stage -1: Trust review and skill source verification
Stage 0: Product strategy and PRD skills
Stage 1: Spec workflow skills
Stage 2: Engineering lifecycle skills
Stage 3: TDD/backend implementation skills
Stage 4: Security/AI safety skills
Stage 5: UI/E2E skills
Stage 6: Documentation/release/performance skills
Stage 7: Codebase intelligence skills after meaningful code exists
```

Reason:

- PM skills are not implementation skills.
- TDD skills should be active when building tests and code.
- UI skills should not dominate backend architecture.
- Performance skills matter after working UI/API flows exist.
- Codebase-intelligence skills are more useful once the repo has real code.

---

## 3. Environment safety defaults

Before installing skills, prefer telemetry opt-out where supported:

```bash
export DISABLE_TELEMETRY=1
export SUPERPOWERS_DISABLE_TELEMETRY=1
```

Do not paste API keys, personal tokens, or secret values into skill installers.

---

## 4. Skill source and installation matrix

| Stage | Skill/tool | Source | Install command | Use for | Required output |
|---|---|---|---|---|---|
| Stage 0 | PM Skills | `https://github.com/phuryn/pm-skills` | `codex plugin marketplace add phuryn/pm-skills` then selected `codex plugin add ...` commands below | Strategy, PRD, roadmap, metrics, red-team PRD | PRD v1, strategy, metrics, risk register, product-mode validation |
| Stage 1 | GitHub Spec Kit | `https://github.com/github/spec-kit` | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<latest-release-tag>` then `specify init . --integration codex --integration-options="--skills"` | Constitution, specs, plan, tasks, implementation discipline | `.specify/`, specs, plan, tasks |
| Stage 2 | Addy Osmani Agent Skills | `https://github.com/addyosmani/agent-skills` | `npx skills add https://github.com/addyosmani/agent-skills` | Define-plan-build-verify-review-ship lifecycle | Build/review/ship checklists |
| Stage 3 | Obra Superpowers | `https://github.com/obra/superpowers` | In Codex CLI use `/plugins`, search `superpowers`, install plugin; if marketplace unavailable, ask Codex to follow repo install docs | TDD, plans, code review, verification | TDD plan and review checkpoints |
| Stage 4 | Security and Hardening | `https://www.skills.sh/addyosmani/agent-skills/security-and-hardening` | `npx skills add https://github.com/addyosmani/agent-skills --skill security-and-hardening` | Secrets, uploads, LLM security, provider risk | Threat model, controls, tests |
| Stage 5 | Python Testing Patterns | `https://www.skills.sh/wshobson/agents/python-testing-patterns` | `npx skills add https://github.com/wshobson/agents --skill python-testing-patterns` | FastAPI, RAG, provider mocks, pytest | Backend tests and test patterns |
| Stage 6 | Vercel Agent Skills | `https://github.com/vercel-labs/agent-skills` | `npx skills add vercel-labs/agent-skills` | Next.js, React, frontend quality, accessibility | UI review and frontend fixes |
| Stage 6 | Webapp Testing | `https://www.skills.sh/anthropics/skills/webapp-testing` | `npx skills add https://github.com/anthropics/skills --skill webapp-testing` | Local Playwright/browser validation | Browser smoke/E2E scripts |
| Stage 6 | E2E Testing Patterns | `https://www.skills.sh/wshobson/agents/e2e-testing-patterns` | `npx skills add https://github.com/wshobson/agents --skill e2e-testing-patterns` | Playwright/Cypress E2E patterns | E2E test suite |
| Stage 6 | UI/UX Pro Max | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | `npm install -g ui-ux-pro-max-cli` then `uipro init --ai codex` | UI polish only, not product architecture | UI polish checklist |
| Stage 6 | Project Doc Skills | `https://github.com/imrohitagrawal/project-doc-skills` | If no package installer exists, clone/read the repo and copy approved `SKILL.md` folders into Codex-recognized skills location after trust review | README, architecture, API docs, runbooks | Release-quality docs |
| Stage 6 | Performance Skill | `https://www.skills.sh/addyosmani/web-quality-skills/performance` | `npx skills add https://github.com/addyosmani/web-quality-skills --skill performance` | Core Web Vitals, bundle, latency, caching | Performance review and fixes |
| Stage 7 | Wednesday AI Agent Skills | `https://github.com/wednesday-solutions/ai-agent-skills` | `npx @wednesday-solutions-eng/ai-agent-skills install` | Codebase intelligence after real code exists | Dependency graph, guardrails, risk map |

---

## 5. PM Skills install commands

Use PM Skills during Stage 0 only.

```bash
codex plugin marketplace add phuryn/pm-skills
codex plugin add pm-toolkit@pm-skills
codex plugin add pm-product-strategy@pm-skills
codex plugin add pm-product-discovery@pm-skills
codex plugin add pm-market-research@pm-skills
codex plugin add pm-data-analytics@pm-skills
codex plugin add pm-execution@pm-skills
codex plugin add pm-ai-shipping@pm-skills
```

Optional only if needed later:

```bash
codex plugin add pm-marketing-growth@pm-skills
codex plugin add pm-go-to-market@pm-skills
```

Do not use go-to-market/marketing skills during initial implementation unless the product strategy explicitly requires it.

---

## 6. Stage 0 product-mode validation gate

Before coding, PM/spec skills must validate that these concepts are reflected in the PRD, roadmap, architecture, and first vertical-slice plan:

- Mode 1: Pre-rendered multilingual demo video.
- Mode 2: Interactive AI avatar guide.
- Reusable project-avatar-pack contract from `docs/PROJECT_AVATAR_PACK.md`.
- Language, audience, depth, and style controls.
- Grounded generation from approved project knowledge only.
- Free-first mode with optional premium provider adapters.
- Slice 1 remains focused on the grounding loop and does not implement avatar/video/Q&A prematurely.

If these are missing or contradicted, Codex must update planning docs before writing application code.

---

## 7. Spec Kit install commands

Use during Stage 1.

```bash
# Install uv first if missing. Then install Spec Kit.
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<latest-release-tag>

# In existing repo root:
specify init . --integration codex --integration-options="--skills"
```

After initialization, use the Spec Kit flow:

```text
/speckit.constitution
/speckit.specify
/speckit.plan
/speckit.tasks
```

Do not run `/speckit.implement` until PRD, architecture, risk register, and task breakdown are reviewed.

---

## 8. Skills.sh install commands

Use only when the relevant stage starts.

```bash
# General engineering lifecycle
npx skills add https://github.com/addyosmani/agent-skills

# Security
npx skills add https://github.com/addyosmani/agent-skills --skill security-and-hardening

# Backend testing
npx skills add https://github.com/wshobson/agents --skill python-testing-patterns

# Webapp local testing
npx skills add https://github.com/anthropics/skills --skill webapp-testing

# E2E patterns
npx skills add https://github.com/wshobson/agents --skill e2e-testing-patterns

# Frontend/Vercel skills
npx skills add vercel-labs/agent-skills

# Performance
npx skills add https://github.com/addyosmani/web-quality-skills --skill performance
```

---

## 9. Superpowers install guidance

Use only if you want strict TDD and agentic discipline.

Preferred Codex CLI path:

```text
/plugins
search: superpowers
Install Plugin
```

If this is unavailable, Codex must not invent commands. It should read the upstream repository install docs and document the exact chosen install path in `docs/SKILL_TRUST_REVIEW.md`.

---

## 10. UI/UX Pro Max install commands

Use after the first UI exists, not at Stage 0.

```bash
npm install -g ui-ux-pro-max-cli
uipro init --ai codex
```

Use this for UI polish, visual hierarchy, dashboards, onboarding screens, and interaction quality.

Do not let this skill override product strategy, architecture, security, or PRD acceptance criteria.

---

## 11. Wednesday AI Agent Skills install commands

Use after meaningful code exists.

```bash
npx @wednesday-solutions-eng/ai-agent-skills install
```

Do not run this on an empty repo as the primary planning mechanism.

Use it for:

- codebase map
- dependency graph
- blast-radius analysis
- hooks
- codebase guardrails

---

## 12. Project Doc Skills install guidance

Source:

```text
https://github.com/imrohitagrawal/project-doc-skills
```

If no formal package installer is present, Codex should:

1. clone or inspect the repo
2. review licenses and `SKILL.md` files
3. document findings in `docs/SKILL_TRUST_REVIEW.md`
4. copy only approved documentation skills into the Codex-recognized skills directory or use them as reference prompts

Do not blindly vendor the whole repo.

---

## 13. Stage -1: Skill Trust Review

Before activating skills, create:

```text
docs/SKILL_TRUST_REVIEW.md
```

For each skill/tool, record:

```text
Name:
Source URL:
Install command:
License:
Includes executable scripts? yes/no
Touches filesystem? yes/no
Touches network? yes/no
Can affect git hooks? yes/no
Telemetry? yes/no/unknown
Secrets risk:
Conflict risk:
Approved stage:
Decision: approved / rejected / needs manual review
```

Block any skill whose license, install behavior, or execution behavior is unclear.

---

## 14. Skill conflict rules

If two skills disagree:

1. Security/privacy/license constraints win.
2. PRD and acceptance criteria win over implementation convenience.
3. Architecture ADRs win over ad-hoc code suggestions.
4. TDD test failures block progress.
5. Vertical-slice scope wins over broad scaffolding.
6. Human-readable docs must be updated with every significant decision.

---

## 15. First Codex prompt

Use this before coding:

```text
Read AGENTS.md, docs/AI_BUILD_BRIEF.md, docs/SKILLS_AND_CODEX_SETUP.md, docs/SKILL_EXECUTION_PLAN.md, and docs/PROJECT_AVATAR_PACK.md.

Do not write application code yet.

Execute Stage -1 and Stage 0 only:
1. Create docs/SKILL_TRUST_REVIEW.md.
2. Verify every recommended skill source and install command.
3. Install/use only Stage 0 PM/spec skills.
4. Upgrade seed docs into final v1 planning docs.
5. Validate that Mode 1, Mode 2, and the project-avatar-pack contract are reflected in PRD, roadmap, architecture, and vertical-slice planning.
6. Red-team the PRD.
7. Produce the first vertical-slice implementation plan.
8. Stop and summarize artifacts, risks, assumptions, and recommended next step.
```
