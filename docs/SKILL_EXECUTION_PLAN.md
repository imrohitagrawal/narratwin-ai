# Skill Execution Plan

This plan defines when Codex, PM, Spec Kit, engineering, security, testing, and release skills may be used for NarraTwin AI.

Stage 0 does not install product implementation tools. Stage 0 records the operating model, lock requirements, and quality gates that future stages must follow.

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

## Stage 1 Product-Mode Validation Gate

Slice 1 is pure grounding; this gate does not authorize avatar, video, audio, or interactive Q&A implementation.

```narratwin-contract
contract=stage1-product-mode-validation
status=active
owners=stage1-pm-spec
timing=before-application-coding
targets=prd,roadmap,architecture,first-vertical-slice-plan
mode-1=pre-rendered-multilingual-demo-video
mode-2=interactive-ai-avatar-guide
avatar-pack=reusable-project-avatar-pack
first-slice=pure-grounding
avatar=blocked
video=blocked
audio=blocked
interactive-q-and-a=blocked
premature-implementation=blocked
on-failure=repair-planning-documents-before-application-code
```

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
