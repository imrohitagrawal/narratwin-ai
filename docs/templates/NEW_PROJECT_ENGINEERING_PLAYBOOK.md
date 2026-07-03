# New Project Engineering Playbook

## Purpose

Use this template before starting a new software project, major feature, or
high-risk technical change. It is intentionally source-backed and
artifact-driven so good engineering practices become visible work products, not
private intent.

The core principle:

```text
Do not start with code. Start with intent, source facts, invariants, and tests.
```

## Minimum External References

For new projects, consult authoritative sources that match the project risk.
At minimum, use these categories:

- Official platform/framework documentation for any behavior the project
  depends on.
- NIST SSDF for secure development process and root-cause prevention:
  https://csrc.nist.gov/pubs/sp/800/218/final
- OWASP SAMM for threat assessment, requirements-driven testing, misuse/abuse
  testing, and governance baselines:
  https://owaspsamm.org/model/
- Google SRE postmortem guidance for learning loops and preventive actions:
  https://sre.google/sre-book/postmortem-culture/
- DORA research for socio-technical delivery practices and documentation
  quality:
  https://dora.dev/research/
- GitHub Docs for repository automation, issue linkage, branch protection,
  merge methods, and Actions behavior when using GitHub:
  https://docs.github.com/
- NIST AI RMF and NIST Generative AI Profile when the project uses AI models,
  AI agents, retrieval, generated media, automated decisions, or model-assisted
  workflows:
  https://doi.org/10.6028/NIST.AI.100-1 and
  https://doi.org/10.6028/NIST.AI.600-1
- OWASP Top 10 for Large Language Model Applications / OWASP GenAI Security
  Project when the project uses prompts, agents, tools, model outputs, RAG,
  embeddings, or provider APIs:
  https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OpenSSF Scorecard when the project has a public or private software supply
  chain that depends on GitHub, CI, dependencies, releases, or workflow tokens:
  https://github.com/ossf/scorecard
- SLSA when build provenance, artifact integrity, package publication, or
  deployment supply-chain trust matters:
  https://slsa.dev/

Never rely on memory for platform semantics that can mutate state, change
security posture, close issues, deploy code, delete data, or affect production
readiness.

## Gate -1: Project Bootstrap

Create the governance starter kit before feature work begins. For a throwaway
prototype, explicitly mark which items are skipped and why.

```markdown
# Project Bootstrap

## Repository Controls

- [ ] Default branch protected or ruleset-backed.
- [ ] Direct commits to default branch blocked.
- [ ] Pull request review required.
- [ ] Required status checks listed by exact context name.
- [ ] Force pushes and deletions blocked.
- [ ] Workflow token permissions least-privilege.

## Required Files

| Artifact | Path | Minimum Contents | Status |
|---|---|---|---|
| Operating model | `docs/CODEX_OPERATING_MODEL.md` or equivalent | issue/branch/PR/quality/review rules | pending |
| Status ledger | `docs/STATUS.md` | current stage, issues, PRs, blockers, next actions | pending |
| Quality gates | `docs/QUALITY_GATES.md` | local and CI commands, stage gates, failure policy | pending |
| Traceability | `docs/TRACEABILITY.md` | requirements to implementation/tests/docs | pending |
| ADRs | `docs/ADR/` | accepted architecture decisions and alternatives | pending |
| Review register | `docs/RECOMMENDED_REVIEW_ITEMS.md` or equivalent | findings, owner, required stage, disposition | pending |
| Learnings tracker | `docs/PROJECT_LEARNINGS_TRACKER.md` or equivalent | reusable engineering lessons | pending |
| Third-party notices | `docs/THIRD_PARTY_NOTICES.md` | packages, tools, models, providers, datasets, licenses | pending |
| Skill/tool lock | `docs/SKILL_LOCK.md` or equivalent | agent tools, versions, trust posture | pending |
| README links | `README.md` | links to the governance docs above | pending |
```

## Gate 0: Source Control And Delivery Model

Do this before implementation.

```markdown
# Source Control Gate

## Issue

Issue/ticket:
Scope:
Non-goals:

## Branch

Branch name:
Base branch:
Why this branch is dedicated to this work:

## Pull Request

PR link:
Linked issue wording:
Does this PR intentionally close the issue? yes/no
If yes, exact closing keyword and issue:

## Required Local Commands

Quality:
Tests:
Security:
Docs:

## Required Remote Checks

| Context | Required? | Source |
|---|---:|---|
| lint/typecheck/tests | yes | branch protection/ruleset |
| secret scan | yes | branch protection/ruleset |
| quality gate | yes | branch protection/ruleset |

## Merge Rules

- [ ] No direct default-branch commit.
- [ ] Review required.
- [ ] CI required.
- [ ] Branch is up to date if repository policy requires it.
- [ ] Automation-sensitive PR title/body/commit messages reviewed.
```

## Gate 0: Intent Discovery

Do this before specification.

```markdown
# Intent Brief

## User

Who is this for?

## Problem

What painful situation exists today?

## Desired Outcome

What changes for the user when this works?

## Success Criteria

How will we know it worked? Use measurable, testable language.

## Non-Goals

What are we explicitly not building or not claiming?

## Constraints

Budget, timeline, data sensitivity, deployment target, compliance, provider
limits, operational limits.

## Confidence

Current confidence signal: high/medium/low.
Missing information:

- ...

## Assumptions Register

| ID | Assumption | Risk If Wrong | Owner | Due Date | Approved? |
|---|---|---|---|---|---|
| A1 | ... | ... | ... | YYYY-MM-DD | no |
```

Do not use confidence as a private feeling. If any high-risk assumption is
unapproved, continue discovery before writing the implementation spec.

## Gate 1: Specification

Create a spec before coding.

```markdown
# Spec: <name>

## Objective

What are we building and why?

## Users And Use Cases

Primary users, secondary users, abuse/misuse actors.

## Scope

In scope:

- ...

Out of scope:

- ...

## Acceptance Criteria

- [ ] ...

## Non-Functional Requirements

Security:
Reliability:
Performance:
Privacy:
Observability:
Accessibility:
Cost:

## Commands

Build:
Test:
Lint:
Run:

## Boundaries

Always:
Ask first:
Never:

## Open Questions

- ...
```

## Gate 2: Source Facts

Record official source facts before implementation.

```markdown
# Source Facts

| Area | Source | Fact Used | Design Impact | Verified Date |
|---|---|---|---|---|
| GitHub issue closing | <URL> | Closing keywords work in commit messages | PR title/body/commit messages need guardrail | YYYY-MM-DD |
| Filesystem writes | <URL> | Rename behavior depends on filesystem guarantees | Need recovery tests | YYYY-MM-DD |
```

Rules:

- Prefer official docs and standards.
- Use secondary articles only for context, not as authority.
- Mark unverified assumptions explicitly.
- If a fact can close an issue, delete data, leak secrets, or change runtime
  behavior, it must have a source or a test.

## Gate 3: Invariant And Failure Matrix

Write the contract as positive and negative claims.

```markdown
# Engineering Contract

## Positive Claims

- The system does ...

## Negative Invariants

- The system must not ...

## Trusted Boundaries

- Trusted:
- Untrusted:
- Sanitized/validated at:

## Failure Matrix

| ID | Case | Expected Behavior | Evidence Type | Test/Source/Doc |
|---|---|---|---|---|
| F1 | Valid small input | succeeds | test | pending |
| F2 | Missing required field | typed validation error | test | pending |
| F3 | Wrong nested type | rejected or degraded safely | test | pending |
| F4 | Duplicate request | idempotent replay/conflict per contract | test | pending |
| F5 | External tool unavailable | fail closed with clear error | test/manual | pending |
```

Minimum rows for most backend/API/state features:

- valid happy path
- empty/null input
- missing required field
- wrong primitive type
- wrong nested object/list type
- unknown/extra fields
- malformed serialized state
- schema-version mismatch
- stale/in-flight record
- duplicate request/replay
- conflicting idempotency body
- dependency/tool failure
- timeout or unavailable external system
- authorization/authentication mismatch
- secret-like or sensitive input
- response redaction
- metric/log posture

Matrix variants to add when relevant:

| Area | Required Negative Cases |
|---|---|
| UI/accessibility | small viewport, keyboard-only use, screen-reader labels, long text overflow, loading/error/empty states, unsafe downloads, disabled control states |
| AI/RAG/provider | prompt injection, indirect prompt injection, unsupported claims, missing citations, stale retrieval, provider timeout, provider wrong shape, provider unsafe output, secret-like prompt/upload/context |
| Data/privacy | sensitive input, path disclosure, raw payload logging, retention/cleanup, export/delete request, tenant boundary, backup/restore disclosure |
| CI/release/supply chain | missing required context, renamed status context, scanner unavailable, confirmed vulnerability, unpinned action, excessive workflow token permissions, release without signing or provenance |
| Ops/observability | missing metrics, metrics without scrape path, alert absent, log redaction, trace correlation, readiness versus liveness ambiguity, rollback path |

## Gate 4: Test-Driven Execution

Convert the failure matrix into RED tests before coding.

```markdown
# Test Plan

| Matrix ID | Test Name | Level | Red Confirmed | Green Confirmed |
|---|---|---|---:|---:|
| F1 | test_valid_small_input_succeeds | unit/api | no | no |
| F2 | test_missing_required_field_fails_typed | unit/api | no | no |
```

Rules:

- For bug fixes, reproduce the bug first.
- Tests assert behavior and state, not implementation details.
- If a row cannot be automated, document why and record manual/source evidence.
- Do not delete or weaken a failing test without explicit review.

## Gate 5: Architecture Review

Use this before implementation when behavior spans multiple modules or services.

```markdown
# Architecture Review

## State Model

Entities:
Lifecycle:
Ownership:
Persistence:

## Shared Semantics

| Semantics | Module A | Module B | Module C | Shared Helper? |
|---|---|---|---|---|
| idempotency replay | yes | yes | yes | required/justified no |
| schema validation | yes | yes | no | required |

## Reversibility

What is expensive or impossible to undo?

## Operational Model

Single process?
Multi-process?
Retries?
Backups?
Monitoring?
Rollback?

## Alternatives Considered

Option:
Rejected because:
```

## Gate 6: Adversarial Review

Run at least one fresh-context review on the contract before code is treated as
ready. The reviewer should receive only the artifact and contract, not the
author's reasoning.

```text
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident.

Branch:
Commit:
Files/contracts to inspect:

Invariants to prove or disprove:
- ...

Negative cases to attempt:
- ...

Review:
- unstated assumptions
- missing negative cases
- hidden coupling or shared state
- ways the contract can be violated
- source facts that need verification
- tests that would pass while the requirement is still false
- docs that overclaim or contradict implementation
- gates that pass while the requirement remains false

Do not validate. Find issues, or state explicitly that you cannot find any
after thorough examination.

Report format:
- blocking findings first
- file/line references where possible
- exact reproduction or reasoning
- residual risks separate from blockers

Artifact:
<paste>

Contract:
<paste>
```

Reviewer-role selector:

| Risk Area | Required Reviewer Prompt Emphasis |
|---|---|
| API/public contract | status codes, schemas, idempotency, headers, redaction, OpenAPI drift |
| Architecture/state | ownership, lifecycle, concurrency, restore, migration, data loss, repeated semantics |
| Security/privacy | untrusted input, secrets, authz, sensitive data, dependency and supply-chain posture |
| AI/provider | prompt injection, model output validation, evals, citations, provider boundaries |
| Frontend | accessibility, responsive layout, unsafe downloads, user-visible state, browser verification |
| Release/ops | readiness, monitoring, alerts, rollback, branch protection, CI evidence |

Classify every finding:

- contract misread
- valid and actionable
- valid trade-off
- noise

Do not rubber-stamp the reviewer. Re-read the artifact and decide.

## Gate 7: PR Evidence

Every non-trivial PR must include an evidence table, not just checked boxes.

```markdown
| Evidence | Artifact Path / URL | Matrix IDs | Command / CI / Source | Reviewer | Status | Residual Risk Decision |
|---|---|---|---|---|---|---|
| Intent/spec | `docs/...` | A1-A3 | reviewed by ... | ... | pass/fail | ... |
| Source facts | `docs/...` | S1-S4 | official URLs | ... | pass/fail | ... |
| Failure matrix | `docs/...` | F1-F12 | mapped tests | ... | pass/fail | ... |
| Tests | `tests/...` | F1-F12 | `make test` / CI URL | ... | pass/fail | ... |
| Docs | `docs/...` | D1-D4 | doc review | ... | pass/fail | ... |
| Adversarial review | `docs/reviews/...` or PR comment | R1-R3 | reviewer prompt/result | ... | pass/fail | ... |
| Release/ops | `docs/...` | O1-O4 | runbook/checklist/rollback | ... | pass/fail | ... |
```

## Stop Rules

Pause and run an RCA before continuing when:

- two substantive blockers are found after an "all checks pass" state
- the same failure class appears in more than one module
- a guardrail misses behavior documented by an official source
- tests are repeatedly added only after reviewers discover the scenario
- the PR becomes too large to review in one sitting
- implementation requires three or more major rewrites or force-push cycles
- the team cannot state the negative invariants in plain language

## RCA Pause Artifact

When a stop rule triggers, create a short RCA before further implementation.

```markdown
# RCA Pause: <topic>

## Trigger

Which stop rule fired?

## Impact

What could have gone wrong if this had merged?

## Missed Invariant

What requirement or negative invariant was absent or weak?

## Why Existing Checks Passed

Which tests/gates/reviews were green, and why were they insufficient?

## Matrix Delta

| New Matrix ID | Case | Expected Behavior | New Test/Source/Manual Evidence |
|---|---|---|---|
| F-new | ... | ... | ... |

## Correction

Code/design/doc/gate changes required:

- ...

## Resume Criteria

Implementation may resume only when:

- [ ] matrix delta has owner and evidence type
- [ ] RED tests or source/manual proof are added for new rows
- [ ] docs and PR evidence table are updated
- [ ] adversarial reviewer has checked the corrected matrix
- [ ] residual risks are accepted or tracked

## Reviewer Signoff

Reviewer:
Date:
Disposition:
```

## Definition Of Done

The work is done only when:

- user intent is explicit
- spec is approved or scope is otherwise unambiguous
- official source facts are recorded for platform semantics
- positive and negative invariants are listed
- failure matrix rows are resolved
- tests prove the important rows
- docs match behavior
- review findings are reconciled
- CI is green
- residual risks are visible and accepted

## Skip Template

Use this only for explicitly allowed deviations. A skip is not valid unless it
has an accountable approver, an expiry or revisit trigger, and a visible risk
decision in the PR evidence table.

Non-skippable gates for production-bound, security-sensitive, data-handling, AI,
payment, authentication, authorization, persistence, migration, release, or
governance changes:

- issue/owner/branch/PR workflow
- source-fact check for platform or automation behavior
- invariant and failure matrix
- tests or an explicit proof artifact for changed behavior
- adversarial review disposition
- security/privacy review where user data, secrets, auth, or untrusted input is
  involved
- release/rollback decision for deployable changes

Allowed approvers:

- accountable product/engineering owner for product-scope deviations
- security/privacy owner for security, privacy, auth, or untrusted-input
  deviations
- release owner for launch, rollback, or production-watch deviations
- repository/governance owner for workflow, branch-protection, CI, or guardrail
  deviations

Expiry requirements:

- High-risk deviations expire before merge unless the approver explicitly records
  why they can be accepted at merge.
- Medium-risk deviations require a dated follow-up issue or revisit trigger.
- Low-risk deviations may be accepted in the PR if the residual risk is named.

Skipping is forbidden when the skipped step is the only control preventing data
loss, secret exposure, issue auto-closure, production release overclaim, payment
error, security boundary bypass, irreversible migration, or public synthetic
media misuse.

```markdown
| Skipped Step | Reason | Risk | Approver | Expiry / Revisit Trigger |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |
```

## Anti-Patterns

- Starting with implementation because the ask "sounds clear."
- Treating test existence as proof of test completeness.
- Asking reviewers "does this look good?" instead of "how does this fail?"
- Adding guardrails without testing known bypass syntax.
- Copying behavior across modules without a parity matrix.
- Trusting PR title/body/commit text as harmless prose when automation parses it.
- Calling a local-only feature production-ready because it survives the happy
  path.
- Recording a checklist item without linking the evidence artifact.

## Reusable Sequence

```text
bootstrap -> source control gate -> interview -> spec -> source facts
-> contract -> failure matrix -> RED tests -> implementation
-> adversarial review -> docs/gates -> PR evidence -> merge
```

If a project skips one step, name the skip and why it is safe.
