# Skills and Codex Setup

This file is the quick-start summary. The authoritative operating plan is `docs/SKILL_EXECUTION_PLAN.md`.

Do not install skills from this file alone. First complete `docs/SKILL_TRUST_REVIEW.md`.

## Operating rule

Install or activate only the skill needed for the current stage. Do not install every skill at once.

## Stage order

| Stage | Install/use | Purpose | Stop condition |
|---|---|---|---|
| Stage -1 | No implementation skills yet | Verify skill source, license, install command, telemetry, filesystem/network behavior, and secrets risk | `docs/SKILL_TRUST_REVIEW.md` exists and flags each skill as approved, rejected, or manual-review |
| Stage 0 | PM/spec skills only | Product discovery, strategy, PRD, roadmap, metrics, PRD red-team review | Product docs are implementation-ready |
| Stage 1 | Spec Kit / architecture / security review skills | Constitution, specs, architecture, ADRs, trust zones, AI safety, privacy | Architecture and risk docs are reviewed |
| Stage 2 | Engineering lifecycle and quality-gate skills | Local validation, CI contracts, PR templates, review checklist | Quality workflow and local commands are documented |
| Stage 3 | TDD/backend/provider/RAG testing skills | Implement Slice 1 with tests and mocks/fakes | Slice 1 works, tests pass, docs updated |
| Stage 4 | UI and E2E skills | Frontend flow, accessibility, Playwright/browser smoke tests | UI happy path and failure path are tested |
| Stage 5 | Documentation, performance, codebase-intelligence skills | Runbooks, release readiness, performance review, dependency map | Release-readiness review is complete |

## Recommended skill families

1. PM Skills: product discovery, product strategy, PRD, roadmap, metrics, red-team PRD.
2. GitHub Spec Kit or equivalent: constitution, spec, plan, tasks, implementation control.
3. Addy Osmani Agent Skills: plan-build-test-review-ship lifecycle.
4. TDD workflow: red-green-refactor for backend, provider, RAG, and evaluation logic.
5. Security hardening: uploads, secrets, LLM prompt injection, provider risk, license checks.
6. Python testing patterns: FastAPI, provider mocks, RAG tests, pytest fixtures.
7. Webapp/E2E testing: UI smoke, accessibility, Playwright flows.
8. Vercel/Next.js skills: frontend structure, accessibility, performance.
9. Project doc skills: README, runbooks, architecture docs, handoff docs.
10. Wednesday AI agent skills: only after meaningful code exists.

## Conflict rule

If two skills disagree, apply this order:

1. Security, privacy, consent, and license constraints.
2. PRD acceptance criteria.
3. Architecture ADRs.
4. Failing tests.
5. Vertical-slice scope.
6. Documentation and human review.

## Do not do this

- Do not create `.agents/vendor` before a trust review approves manual vendoring.
- Do not let UI skills override architecture or PRD decisions.
- Do not let PM skills generate implementation code.
- Do not run codebase-intelligence skills on an empty repo as the primary plan.
- Do not enable premium avatar, TTS, face clone, or voice clone providers in the MVP.
