# Skill Execution Plan

This plan defines when Codex, PM, Spec Kit, engineering, security, testing, and release skills may be used for NarraTwin AI.

Selection within a stage follows
[`docs/SKILL_SELECTION_AND_EVIDENCE.md`](SKILL_SELECTION_AND_EVIDENCE.md):
start from the claim and boundary, choose the smallest test that can disprove
the claim, use a skill to govern the method, and record the resulting evidence
or prevented unsafe action. Skill invocation is not completion evidence.

Stage 0 does not install product implementation tools. Stage 0 records the operating model, lock requirements, and quality gates that future stages must follow.

## Product Mode Policy Authority Handoff

Only `docs/PHASE_PLAN.md` registered tables are authoritative for durable
Product Mode policy. Explanatory prose, examples, comments, quoted text, and
relocated tables do not authorize policy changes.

Before coding, PM/spec skills must validate both Product Mode 1 and Product Mode 2 and the reusable `project-avatar-pack` contract across the PRD, roadmap, architecture, and Slice 1 planning.

Skill selection and execution must respect the gate order
`PM-GATE-00 -> PM-GATE-10 -> PM-GATE-20 -> PM-GATE-30` before any Product Mode
claim is made. `docs/STATUS.md` StatusStateV1 table is the normalized mutable current-state authority,
alongside live GitHub issue and PR state.

No Product Mode 2, runtime, media, provider, hosted, public, or production work
is authorized by this handoff or by StatusStateV1.

## Issue 313 Architecture And Oracle Decision

Issue `#313` uses GitHub triage, spec-driven development,
planning-and-task-breakdown, context engineering, TDD, and incremental
implementation as process guidance for a governance-only architecture and
evaluation decision. Evidence is the frozen issue/preflight, committed failing
tests before checker/docs GREEN, oracle mutation coverage, quality gates, and
independent exact-head review; skill invocation alone proves nothing.

Backend, frontend, API, RAG, provider, browser, performance, observability, and
runtime security implementation skills are rejected as wrong-surface because
Issue #313 changes no product behavior. Custom skills, external translation
models, and model judges are rejected because existing approved guidance is
sufficient and those options introduce dependency, license, resource, or
circular-evaluation risk. A later Issue #280 repair must make a fresh selection
from its own behavioral claim and frozen implementation boundary.

## Issue 315 Product-Context Quality Gate

Issue `#315` uses GitHub workflow guidance, spec-driven development,
planning-and-task-breakdown, context engineering, TDD, and incremental
implementation for a governance-only product-context gate. Evidence is the
owner-approved issue contract, first-commit preflight, committed parser and
durability RED tests before GREEN, field-level and unexpanded-count false-pass
mutations, forced PR event validation, full quality gates, and independent
exact-head review. The reusable authoring rule is also copied into the new-
project engineering playbook so later repositories do not depend on this chat
or NarraTwin-only policy.

Backend, frontend, browser, provider, runtime security, performance,
observability, deployment, and shipping implementation skills are rejected as
wrong-surface because Issue #315 changes only PR authoring and review policy.
Custom skills, external models, and new dependencies are rejected because the
existing local parser and approved process guidance are sufficient. Skill
invocation is not evidence without the committed TDD and gate results.

## Stage-Aligned Skill Use

| Stage | Stage name | Skill/tool posture | Allowed outputs |
|---|---|---|---|
| Stage 0 | Codex operating model and skill lock | Read existing local skill documentation for governance only; do not activate product implementation tools | Operating docs, skill lock, stage issue plan, quality scripts |
| Stage 1 | Product strategy and PRD v1.0 | PM strategy, discovery, PRD, red-team, metrics, roadmap skills after lock review | Product strategy, PRD v1.0, red-team review, metrics, roadmap |
| Stage 2 | Architecture, security, AI safety | Spec, architecture, security, AI safety, ADR documentation skills after lock review | Architecture docs, ADRs, threat model, AI safety/evaluation plan |
| Stage 3 | Repo foundation and CI/CD quality gates | CI/CD, repo automation, local development, dependency/security scan skills | Executable repo quality gates and CI wrappers |
| Stage 4 | Project upload to grounded script generation | TDD, backend, frontend, RAG, evaluation, and review skills scoped to Slice 1 | First vertical slice with tests and docs |
| Stage 5 | Evaluations, guardrails, observability | AI evaluation, prompt-injection, observability, security review skills | Blocking evals, guardrails, trace/run metadata |
| Stage 6 | Multilingual scripts, subtitles, voice adapter | Localization, subtitle, voice adapter, accessibility, test skills | Mock/local voice path and subtitles |
| Stage 7 | Avatar rendering adapter and export | Avatar adapter, media export, provider contract, license review skills | Mock/local avatar export path |
| Stage 8 | Performance, security hardening, release readiness | Performance, security hardening, release readiness, shipping skills | Release-hardening evidence |
| Final Review | Independent review | Review-only skills and independent audit process | Independent review findings and sign-off record |

## Activation Rules

- Before creating, installing, or activating a custom skill/plugin, inspect the
  preinstalled and repo-approved skills/docs for a matching capability. The PR
  must record the checked options and why each was insufficient.
- Every skill or external workflow source must be listed in `docs/SKILL_LOCK.md` before use.
- Any source with an unresolved license, pin/version, telemetry, or credential risk is not approved for activation.
- Skills may not override `docs/CODEX_OPERATING_MODEL.md`, `docs/QUALITY_GATES.md`, security/privacy constraints, or human review decisions.
- Custom skills/plugins require explicit approval plus documented source, pin or
  version, license, filesystem/network/telemetry behavior, credential behavior,
  expiry or revisit trigger, `docs/SKILL_LOCK.md`, and
  `docs/THIRD_PARTY_NOTICES.md` updates before use.
- PM skills are not implementation skills.
- Spec Kit implementation commands are blocked until Stage 4 and only after Stage 0, Stage 1, Stage 2, and Stage 3 gates allow the planned slice.
- Engineering implementation skills are blocked during Stage 0, Stage 1, Stage 2, and Stage 3.
- Paid-provider skills or adapters must never be required for local/dev/test.
- Skill installers must not receive secrets or personal tokens.
- Actual child-issue and PR preflights must record invoked, rejected,
  unavailable/unapproved, ineffective, and wrong-stage candidates when they
  materially affect selection. Do not optimize for the number of skills used.
- A verification-skill trigger may authorize evaluation only. Installation or
  activation still requires explicit owner approval and the lock/notices review
  in this plan.

## Required Lock Fields

`docs/SKILL_LOCK.md` must record these fields for every skill/tool source:

- capability
- source URL
- pin/version status
- license status
- purpose
- active stage
- activation status

## Stage 0 Skill Scope

Allowed in this Stage 0 redo:

- read local cached skill docs for process guidance
- update `docs/SKILL_LOCK.md`
- update `docs/SKILL_EXECUTION_PLAN.md`
- update operating and quality docs

Not allowed in this Stage 0 redo:

- installing new skills from the network
- committing local `.codex` vendor/cache directories
- running product implementation skills
- creating backend, frontend, RAG, avatar, provider, database, Docker, or runtime product code

## Conflict Resolution

If skills disagree, apply this order:

1. Security, privacy, consent, and license constraints.
2. Stage gate and quality gate requirements.
3. Product strategy and PRD acceptance criteria.
4. Architecture ADRs.
5. TDD and evaluation evidence.
6. Skill recommendation.

## Future Activation Evidence

When a later stage activates a skill, update `docs/SKILL_LOCK.md` with:

- immutable tag, version, or commit SHA
- reviewed license status
- install or activation command used
- whether it writes files, runs scripts, touches network, or can affect credentials
- stage where the skill is active
- reviewer evidence in the stage PR

## Issue 317 semantic repair slice 1

Issue `#317` invokes spec-driven development to freeze the independent fixture
and contract, test-driven development for committed behavioral RED before
runtime GREEN, API/interface design for additive proposition/run/source
bindings, frontend UI engineering plus browser testing for genuine visible
behavior, and security/hardening guidance for fail-closed untrusted input.
Evidence is the commit order, mutation tests, semantic metrics, API/artifact
joins, real Playwright execution, exact scope gate, and independent exact-head
review; invocation alone proves nothing.

Phrasebook expansion, provider/model adapters, model judges, refusal-only
containment, performance optimization, observability expansion, shipping,
deployment, and custom skills are rejected because they either fail the
semantic claim or exceed the bounded local/mock surface. No dependency or skill
installation is needed. Human review remains mandatory for bilingual meaning,
non-cosmetic audience emphasis, citation truth, oracle/runtime independence,
claim boundaries, and merge wording.

## Issue 319 agent-context shadow slice

Issue `#319` uses context engineering, specification-driven development, TDD,
API/interface design, ADR documentation, security/hardening, code review,
incremental implementation, Git workflow, GitHub workflow guidance, and task
breakdown. They changed the work by separating authority from progressive
context, freezing independent fixtures, requiring 50 behavioral RED failures,
typing path/action/claim/decision planes, using deny-by-default boundaries, and
preserving exact-head review/closeout. Evidence is the commits, hashes, tests,
packets, receipts, budgets, gates, and independent review—not invocation.

Frontend/backend product implementation, RAG, providers, performance,
observability, shipping, deployment, deprecation/migration, custom skills,
hosted models, model judges, databases, new dependencies, and workflows are
rejected as wrong-surface, premature, circular, or outside the frozen shadow
authority. Root mandatory reading and human approval remain unchanged.
