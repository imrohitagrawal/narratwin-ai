# Project Learnings Tracker

## Purpose

This tracker records reusable engineering, product, AI safety, security, release,
and agent-workflow learnings discovered while building NarraTwin AI.

Each row links to a dedicated page with enough context to reuse the learning in
this application or in future applications. Keep the tracker short; put detailed
analysis, examples, remediation, and future protocol in the linked page.

## How To Use This Tracker

Add a row whenever a project event reveals a reusable practice or failure mode:

- a bug escaped the first review pass
- a quality gate passed but did not prove the intended invariant
- a security, AI safety, performance, or release assumption was invalidated
- a stage workflow produced a reusable review or implementation protocol
- a future application should start with a stronger default because of this
  project's experience

Each linked page should include:

- context
- what went wrong or what worked
- root cause
- remediation
- future default approach
- checklist or protocol that can be reused

## Learning Register

| ID | Learning | Source stage | Dedicated page | Owner | Enforcement surface | Review cadence | Promotion status | Status | Reuse guidance |
|---|---|---|---|---|---|---|---|---|---|
| LRN-001 | Green gates and broad review are not enough; release review must start from invariants, exploit matrices, and contract-to-implementation proof. | Stage 8 | [Review Rigor Retrospective](REVIEW_RIGOR_RETROSPECTIVE.md) | Stage PR owner and reviewer | PR template, Stage 8 quality gate, sub-agent review protocol | Every implementation or release-readiness PR | Promoted to PR checklist and Stage 8 docs gate | Active | Use before every implementation-stage PR and before starting new apps with AI-assisted development. |
| LRN-002 | Status trackers, recommended-review registers, stage gates, ADRs, traceability, third-party/tool locks, and repository settings checks make AI-assisted builds more robust across sessions and applications. | Stage 0 through Stage 8 | [Project Governance Learnings](PROJECT_GOVERNANCE_LEARNINGS.md) | Stage PR owner and release reviewer | README, status ledger, stage plan, quality gates, release checklist | Every stage boundary and release-readiness review | Promoted to README links, Stage 8 docs gate, and release blocker checklist | Active | Use as the default governance starter kit for new applications and as the first audit checklist for existing applications. |

## Required Practice Going Forward

- Start every implementation or release-readiness review by checking this tracker.
- Promote repeated learnings into templates, quality gates, or ADRs when they
  become standing engineering policy.
- Keep owner, enforcement surface, review cadence, and promotion status current
  so each learning is auditable rather than advisory.
- Do not close a learning as superseded unless the replacement page or policy is
  linked here.
- Keep stage-specific lessons concrete; avoid vague process advice that cannot be
  turned into tests, prompts, or review checklists.
