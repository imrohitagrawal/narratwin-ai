# Skills and Codex Setup

This file is a pointer-only quick-start. The authoritative sources are:

- `docs/SKILL_EXECUTION_PLAN.md` for stage-aligned skill use
- `docs/SKILL_LOCK.md` for the current activation ledger
- `docs/SKILL_TRUST_REVIEW.md` for the historical Stage 0 trust review
- `docs/QUALITY_GATES.md` and `docs/REPOSITORY_GUARDRAILS.md` for executable gates

Do not install, create, or activate skills from this file alone.

## Operating Rule

Use approved preinstalled/repo skills and docs first. Create or install a custom
skill/plugin only after the PR records:

- the capability gap
- preinstalled/repo options checked and rejected
- source, pin/version, license, telemetry, filesystem/network, hook, and
  credential behavior
- approval, expiry/revisit trigger, and residual risk
- required `docs/SKILL_LOCK.md` and `docs/THIRD_PARTY_NOTICES.md` updates

## Stage Order

Follow the approved stage model in `docs/SKILL_EXECUTION_PLAN.md`. If this file
and the execution plan disagree, this file is stale and the execution plan wins.

## Conflict Rule

If two skills disagree, apply this order:

1. Security, privacy, consent, and license constraints.
2. Stage gate and quality gate requirements.
3. Product strategy and PRD acceptance criteria.
4. Architecture ADRs.
5. Failing tests and evaluation evidence.
6. Vertical-slice scope.
7. Documentation and human review.

## Do not do this

- Do not create `.agents/vendor` before a trust review approves manual vendoring.
- Do not create custom skills/plugins when an approved installed skill/doc covers the need.
- Do not let UI skills override architecture or PRD decisions.
- Do not let PM skills generate implementation code.
- Do not run codebase-intelligence skills on an empty repo as the primary plan.
- Do not enable premium avatar, TTS, face clone, or voice clone providers in the MVP.
