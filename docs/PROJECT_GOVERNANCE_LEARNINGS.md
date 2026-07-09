# Project Governance Learnings

## Purpose

This page captures reusable governance patterns that emerged while building
NarraTwin AI. These patterns are not process decoration. They made the project
more robust by turning ambiguous review comments, stage progress, tool choices,
and release risks into durable, checkable artifacts.

Future applications should start with these defaults instead of rediscovering
them after the project becomes complex.

## Learning 1: Status Must Be A First-Class Artifact

### What Worked

`docs/STATUS.md` became the central ledger for stage state, issue and PR mapping,
current branch posture, merged baselines, known gaps, and next actions.

This avoided a common failure mode in AI-assisted builds: the agent remembers a
stage, branch, or PR state incorrectly and starts implementing against stale
context.

### Why It Matters

AI-assisted work often spans many sessions. Without a status ledger, context
compaction, branch switches, merged PRs, and partially completed stages can cause
the next agent run to act on an obsolete plan.

The status page gives reviewers and agents a stable answer to:

- What stage are we in?
- What branch and issue own the work?
- Which PR is open or merged?
- What is allowed in this stage?
- What is blocked?
- What quality gate is authoritative?
- What changed since the previous stage?

### Future Default

Every serious application should have a status tracker from the first stage.

Minimum fields:

- current stage
- current branch
- linked issue
- linked PR
- merged baseline commit
- implementation permission
- current blockers
- current known limitations
- next approved actions
- changelog of stage transitions

### Review Checklist

- Does the status page match the actual branch?
- Does it name the current issue and PR?
- Does it say what is blocked?
- Does it name the current quality gate?
- Does it record recent stage transitions with concrete dates and commits?

## Learning 2: Non-Blocking Review Items Need A Register

### What Worked

`docs/RECOMMENDED_REVIEW_ITEMS.md` turned optional reviewer feedback into tracked
work with an owner stage or phase. This prevented useful review insights from
being lost when they were not immediate blockers.

Examples from this project:

- durable idempotency and artifact state before multi-worker deployment
- real video export and license posture before public media output
- persistent synthetic-media consent and provenance before external avatar
  provider use
- source-run versus subtitle-bound rendering decision before real timed media
  export

### Why It Matters

Not every valid review comment should block the current PR. But if non-blocking
items are left only in PR comments, they disappear from future planning.

A recommended-review register creates a third state between "fix now" and
"ignore":

- accepted non-blocking
- required by a later stage
- superseded with rationale
- resolved with evidence

### Future Default

Every project should maintain a recommended-review register once more than one
stage or PR exists.

Minimum fields:

- ID
- recommendation
- required stage or phase
- disposition
- source
- rationale or evidence

### Review Checklist

- Are all due items resolved, accepted with rationale, or superseded?
- Is every accepted non-blocking item assigned to a concrete future stage?
- Does the quality gate fail if due items remain open?
- Does the status page summarize important pending review items?

## Learning 3: Stage Gates Must Fail Loudly Until Implemented

### What Worked

Stage-specific quality targets prevented future-stage checks from pretending to
pass before the stage existed. `make quality` dispatches based on `.stage/current`
and each stage has an executable contract.

### Why It Matters

Projects with staged delivery often accumulate placeholder scripts. If a future
stage target silently succeeds, reviewers get false confidence.

The right behavior is:

- implemented stage gate passes or fails based on real checks
- unimplemented future stage gate fails loudly
- active stage gate checks branch scope, required files, docs, tests, and quality
  wrappers

### Future Default

Use one stable command, such as `make quality`, but make it stage-aware. Each
stage should have a dedicated checker that validates the stage contract.

### Review Checklist

- Does the active stage gate execute real checks?
- Do future stage targets fail loudly?
- Does the gate validate changed-file scope?
- Does the gate assert important marker strings and test names?
- Does the gate run the local wrappers that CI also uses?

## Learning 4: Exact Stage Scope Prevents Drift

### What Worked

`docs/STAGE_ISSUE_PLAN.md` and stage checkers limited each stage to an explicit
file allowlist. This caught accidental drift and forced stage-scope decisions to
be documented.

### Why It Matters

AI-assisted implementation tends to expand. Exact stage scope keeps the current
PR focused and makes unrelated changes visible.

### Future Default

Every stage should define:

- allowed files
- blocked changes
- required artifacts
- stage-specific quality target
- issue and branch naming pattern

### Review Checklist

- Is every changed file in the stage allowlist?
- If a new file is needed, did the stage scope document change with rationale?
- Are blocked changes still blocked?
- Does the checker enforce scope against `main`?

## Learning 5: ADRs Are Needed For Gate And Boundary Changes

### What Worked

The repository guardrails require ADR updates for architecture-impacting changes.
Stage 8 needed ADR 0006 because request hardening, CI Docker scan behavior, and
release gates changed the architecture contract.

### Why It Matters

Architecture changes are not limited to domain code. CI/CD gates, security
boundaries, provider integration posture, and release constraints can all change
system behavior.

### Future Default

Require ADR updates when a change affects:

- provider boundaries
- storage or idempotency model
- request/security boundaries
- evaluation gates
- observability model
- CI/CD quality gates
- release approval criteria

### Review Checklist

- Does the PR touch architecture-sensitive paths?
- Is an ADR added or updated?
- Does the ADR explain alternatives and consequences?
- Do status and traceability docs point to the decision?

## Learning 6: Traceability Makes Review Claims Auditable

### What Worked

`docs/TRACEABILITY.md` links implementation artifacts to requirements and stages.
This made it easier to verify that docs, tests, scripts, and product behavior
were all aligned.

### Why It Matters

Without traceability, a release-readiness claim can become vague. Traceability
answers what artifact covers which requirement and whether that coverage is
planned, added, hardened, or blocked.

### Future Default

Maintain traceability for any application with staged requirements or public
claims.

Minimum fields:

- artifact
- requirement coverage
- stage or issue
- status

### Review Checklist

- Does every new major artifact have traceability?
- Do PRD-impacting changes update traceability?
- Are known blockers traceable to release docs or review items?

## Learning 7: Third-Party And Skill Registers Prevent Hidden Dependencies

### What Worked

`docs/THIRD_PARTY_NOTICES.md` and `docs/SKILL_LOCK.md` recorded packages, tools,
skills, actions, scanners, datasets, providers, and generated samples.

### Why It Matters

AI-built applications can silently accumulate dependencies through local tools,
skills, generated assets, and optional providers. If they are not recorded, later
release review has to rediscover licensing, telemetry, credential, and commercial
use risks.

### Future Default

Track third-party use from the beginning, including non-runtime tooling.

Include:

- package or tool name
- source
- pin or version
- license or terms status
- purpose
- active stage
- runtime versus dev-only posture
- credential or telemetry risk

### Review Checklist

- Did any dependency, action, tool, skill, provider, model, dataset, media asset,
  or generated sample get added?
- Is it in both the third-party notice and skill/tool lock where applicable?
- Is it optional or required?
- Does it introduce paid-provider or production-credential coupling?

## Learning 8: Release Readiness Needs Evidence, Not Just Tool Names

### What Worked

Stage 8 added release checklist, runbook, performance smoke, dependency audit,
Docker scan, Lighthouse, and release-readiness review artifacts.

### What Needed Improvement

Reviewers correctly observed that listing scripts is weaker than recording run
evidence. A release-readiness review should identify where the evidence lives:

- local `make quality` result
- PR CI run
- performance report
- Lighthouse report
- dependency/security output
- Docker scan SARIF artifact
- eval smoke report

### Future Default

Release-readiness docs should include either measured results or explicit links
to generated artifacts/CI runs that contain the measured results.

### Review Checklist

- Are budget results recorded?
- Are scan artifacts named?
- Is the rollback path actionable?
- Are monitoring limits and blockers explicit?
- Is production readiness clearly separated from local/demo readiness?

## Learning 9: Repository Settings Are Part Of Release Governance

### What Worked

Docs identified required status checks and non-negotiable branch/PR workflow.

### What Was Exposed

Read-only release review found that GitHub branch protection or repository
rulesets were not enabled even though the docs required them. This cannot be
fully solved in code, but it must be tracked as a release blocker or repository
administration task.

### Future Default

Every release-readiness review should inspect repository settings, not just
workflow files.

Required checks:

- branch protection or repository ruleset exists for `main`
- required checks match emitted workflow status contexts
- direct pushes to `main` are blocked
- PR review is required before merge
- stale approvals and admin bypass posture are explicit

### Review Checklist

- Do documented required checks exist as emitted status contexts?
- Are repository rulesets actually enabled?
- Is any mismatch recorded as a blocker?

## Learning 10: Root README Should Link Governance And Learnings

### What Worked

The root README already points to project status and build brief. Adding the
project learnings tracker makes reusable lessons discoverable for future work.

### Why It Matters

If governance and learnings are only buried under `docs/`, future agents or
developers may skip them. The README is the entry point for both humans and
agents.

### Future Default

The README of any serious AI-assisted application should link:

- current status
- build brief or operating model
- learnings tracker
- quality gate instructions
- contribution or stage workflow

The PR template should also require authors to check the learnings tracker and,
for implementation or release-readiness changes, confirm invariant,
exploit-matrix, and contract/gate review.

## Learning 11: Process Allowlists Must Cover Governance Learning Updates

### What Worked

Phase 1 process-learning PRs may update governance artifacts such as this file
when a reusable lesson exists.

This exposed an enforcement gap: `docs/PROJECT_GOVERNANCE_LEARNINGS.md` was not
in the Phase 1 process-only allowlist. A process-only PR that only updates this
file would be treated as changing an out-of-scope path even though it is a
governance deliverable.

### Why It Matters

Reusable governance learnings are low-cost, high-value updates. If process-only
allowlists block them, teams are incentivized to skip filing the lesson or route
it through a wider branch pattern, increasing risk of drift.

### Future Default

Include governance learning files in Phase 1 process-only change scopes so
process-learning updates are always possible without relaxing unrelated runtime
scope.

### Review Checklist

- Is this update scoped to a governance artifact that is explicitly in the
  process-only allowlist?
- Does the same file have a clear requirement in the stage-issue plan and
  checker scope?
- Does the process PR still avoid backend/frontend/provider/runtime files?

## Learning 12: Invariants Must Map to Tests, Gates, or Human-Only Checklist

### What Worked

`docs/ENGINEERING_PROCESS_RCA.md` and
`docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` are now the single places
that require process-invariant mapping before implementation starts.

### Why It Matters

PRs can still satisfy checklist-style text without proving negative behavior or old
bug exposure. Medium/Low PHF follow-ups showed that marker strings and manual
intent statements were not enough unless each invariant had a concrete mapping path.

### Future Default

For every non-trivial PR, require one of:

- executable tests for the matrix ID,
- executable gates/checkers,
- official source facts,
- explicit human-only review row with owner and residual-risk decision.

Process-critical governance docs, PR templates, quality gates, guardrail scripts,
and process-review registers count as non-trivial even when the edit looks
text-only. The cost of a preflight row is lower than another review/fix loop
caused by a marker-only process claim.

Then require either:

- old behavior fail evidence (RED, break-test, mutation, or regression reproduced), or
- explicit non-goal status with owner and rationale for why no automated proof is
  possible.

### Review Checklist

- Is there a matrix ID for every claimed process invariant?
- Is each matrix ID mapped to test/gate/source/human-only/non-goal evidence?
- Is old-behavior failure evidence present for false-pass-prone claims?
- Is every required human-only surface listed with owner and residual-risk decision?

## Summary Defaults For New Applications

Start new applications with these files or equivalents:

- `docs/STATUS.md`
- `docs/PROJECT_LEARNINGS_TRACKER.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/TRACEABILITY.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/SKILL_LOCK.md` or tool/agent lock
- `docs/ENGINEERING_PROCESS_RCA.md` or equivalent process-RCA artifact
- `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md` or equivalent project-start playbook
- `docs/ADR/`
- stage-specific quality gate scripts
- root README links to the above

These artifacts reduce drift, preserve review memory, and make future AI-assisted
work more reliable.
