# Final Review Handoff

Stage: Final Review - Independent reviewer pass  
Issue: `#6`  
Recommended branch pattern: `final-review-*`  
Current baseline: `main` after Stage 8 merge commit `fb40113`

## Purpose

Run an independent Staff-level release review across the complete repository.
This pass is review-only. Do not fix issues during the pass. Create review
artifacts and file follow-up issues for defects, risks, or release blockers.

## Required Starting Checks

Before review work starts:

- confirm the current branch starts from latest `origin/main`
- confirm `.stage/current` is `8`
- confirm Stage 8 PR `#33` is merged
- confirm Final Review issue `#6` is the linked issue for the review branch and PR
- confirm no paid provider key, production credential, or external paid-provider
  dependency is required for review
- confirm `main` branch protection or repository rulesets are enabled or record
  that verification as a release-blocking external action

## Reviewer Agents To Install Or Activate

Use these reviewer agents if they are not already active:

```bash
cp -R .codex/skills/vendor/addyosmani-agent-skills/agents/code-reviewer.md .codex/skills/active/ || true
cp -R .codex/skills/vendor/addyosmani-agent-skills/agents/security-auditor.md .codex/skills/active/ || true
cp -R .codex/skills/vendor/addyosmani-agent-skills/agents/test-engineer.md .codex/skills/active/ || true
```

Record any newly activated agent/tooling in `docs/SKILL_LOCK.md` and
`docs/THIRD_PARTY_NOTICES.md` if repository policy requires it.

## Final Review Prompt

Use this prompt for the independent review:

```text
Act as an independent Staff-level reviewer.

Review the full repo against:
1. PRD
2. architecture
3. security model
4. AI safety/evals
5. test coverage
6. CI gates
7. portability
8. performance
9. documentation
10. portfolio-readiness

Produce:
- docs/reviews/FINAL_REVIEW.md
- docs/reviews/RISK_REGISTER.md
- docs/reviews/DEFECT_BACKLOG.md
- docs/reviews/GO_NO_GO.md

Do not fix issues in this pass.
Only review and create issues.
```

## Required Review Inputs

Read these sources before writing findings:

- `AGENTS.md`
- `docs/AI_BUILD_BRIEF.md`
- `docs/PRD.md`
- `docs/PRODUCT_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/THREAT_MODEL.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/QUALITY_GATES.md`
- `docs/REPOSITORY_GUARDRAILS.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/RUNBOOK.md`
- `docs/TRACEABILITY.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/PROJECT_LEARNINGS_TRACKER.md`
- `docs/PROJECT_GOVERNANCE_LEARNINGS.md`
- `docs/REVIEW_RIGOR_RETROSPECTIVE.md`
- all `docs/ADR/*.md`
- `.github/pull_request_template.md`
- `scripts/guardrails_check.py`
- stage quality scripts under `scripts/quality/`

## Required Outputs

Create the review outputs under `docs/reviews/`:

- `FINAL_REVIEW.md`: full independent review summary, evidence reviewed,
  findings by review dimension, and unresolved questions.
- `RISK_REGISTER.md`: release risks with severity, likelihood, impact, owner,
  mitigation, status, and issue link.
- `DEFECT_BACKLOG.md`: defects found during review, each mapped to a GitHub
  issue, severity, affected files, expected behavior, actual behavior, and
  suggested stage/fix path.
- `GO_NO_GO.md`: explicit release recommendation with go/no-go decision,
  required pre-release actions, accepted residual risks, and sign-off evidence.

## Issue Creation Rules

For each blocking defect or release risk:

- create or update a GitHub issue
- link the issue from `docs/reviews/RISK_REGISTER.md` or
  `docs/reviews/DEFECT_BACKLOG.md`
- include reproduction steps or evidence when applicable
- do not implement the fix in the final review branch
- classify whether the issue blocks portfolio demo, local release readiness,
  production readiness, or public synthetic-media distribution

## Minimum Review Depth

The review must cover:

- intended-vs-implemented gaps against PRD and traceability
- architecture boundary violations and ADR drift
- untrusted input handling for uploads, prompts, provider outputs, generated
  artifacts, and downloadable frontend content
- provider-bound secret screening and mock/local provider defaults
- AI safety/eval coverage, unsupported claim handling, and evidence contracts
- idempotency semantics, especially validation failures and replay behavior
- test coverage quality, including whether tests assert behavior rather than
  implementation details
- CI and local quality gate parity
- dependency and Docker image scan posture
- portability and local-first setup
- performance budgets and evidence quality
- release checklist, rollback/runbook coverage, and portfolio README readiness
- known Stage 8 limitations: no multi-worker production approval, no real video
  export approval, no external avatar provider approval, and no public
  synthetic-media distribution approval without persistent consent/provenance

## Verification Commands

Run and cite the results where feasible:

```bash
make quality
python3 scripts/guardrails_check.py
python3 scripts/quality/check_recommended_review_items.py "Final Review"
```

`make final-review-quality` is expected to fail loudly until the Final Review
quality gate is implemented. If the reviewer implements only review evidence and
the gate remains intentionally pending, record that explicitly in
`docs/reviews/GO_NO_GO.md`.

## Non-Goals

Do not:

- implement product fixes
- enable paid provider calls
- add production credentials
- enable multi-worker production deployment
- implement real video export
- add external avatar provider integration
- approve public synthetic-media distribution without persistent consent and
  provenance

