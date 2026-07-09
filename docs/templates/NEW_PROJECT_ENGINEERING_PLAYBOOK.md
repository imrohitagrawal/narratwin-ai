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
| F1 | Valid small input | succeeds | test | draft-only; not implementation-ready |
| F2 | Missing required field | typed validation error | test | draft-only; not implementation-ready |
| F3 | Wrong nested type | rejected or degraded safely | test | draft-only; not implementation-ready |
| F4 | Duplicate request | idempotent replay/conflict per contract | test | draft-only; not implementation-ready |
| F5 | External tool unavailable | fail closed with clear error | test/manual | draft-only; not implementation-ready |
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

## Executable Invariants Before Implementation

Before writing implementation code for a new project/app, copy and adapt this
section into that project's preflight artifact. Do not leave it as generic
boilerplate. Rename entities, artifacts, providers, and gates to match the new
system, then create tests from the adapted rows.

Required rule:

- every process-sensitive or durability-sensitive claim must map to a test,
  executable gate, official source fact, or explicitly human-only review item;
- every failure-matrix ID must be fully covered by a test, executable gate,
  official source fact, explicit human-only review row, or documented non-goal;
- negative, mutation, break-test, RED, or "old behavior fails" evidence is
  required for behavior that previously could false-pass;
- implementation starts only after the invariant-to-test matrix is reviewable.

## Gate 3A: Contract Freeze Before Code

For high-risk work, the invariant matrix is not advisory. It is the entry
criterion for coding.

High-risk work includes:

- guardrails, quality gates, CI policy, issue/PR automation, release gates, or
  repository governance;
- durability, restore, replay, idempotency, migrations, storage, queues, or
  rollback;
- privacy, deletion/erasure, consent, provenance, provider egress, secrets, or
  untrusted input;
- production-readiness, monitoring, alerts, SLOs, incident response, or
  deployment posture;
- AI/RAG/provider behavior, generated media, evaluations, or safety controls.

Before implementation starts, the PR-specific preflight artifact must contain:

| Required artifact | Minimum content | Blocking if missing? |
|---|---|---:|
| Intent/spec | objective, scope, non-goals, users/actors, success criteria | yes |
| Source facts | official docs or standards for any platform behavior that can mutate state, close issues, leak data, deploy, delete, or change release posture | yes |
| Positive claims | what the change is allowed to prove | yes |
| Negative invariants | what the change must not allow, including false-pass and abuse paths | yes |
| False-pass matrix | ways a weak implementation could appear compliant while violating intent | yes |
| Test/gate mapping | positive, negative, mutation, RED, break-test, source, or human-only evidence for every row | yes |
| Review prompt set | adversarial prompts generated from the matrix, not generic role prompts | yes |
| Stop rule | criteria for pausing implementation and returning to contract definition | yes |
| Skill/tool selection | preinstalled or approved skills/docs checked first; custom skill/plugin gap, rejected options, approval, lock, and notices when applicable | yes |

No code, guardrail, workflow, release, or governance implementation may start
until the adapted artifact exists and the PR body links it. A template copied
without project-specific entities, threats, tests, and sources does not satisfy
this gate.

## Stop Rule: Review Finds New Defect Classes

If adversarial review finds a new class of blocking issue after implementation
has begun, do not continue patching one symptom at a time.

Stop and reset to contract work when any of these happen:

- two or more review passes find different blocker classes for the same
  requirement;
- a positive test fixture is discovered to encode weak or fake evidence;
- reviewers find a false-pass path not represented in the matrix;
- a governance or release document was cited but no adapted PR-specific artifact
  exists;
- a fix requires changing the definition of done, not just the implementation.

Required reset actions:

1. Add the missing blocker class to the invariant/false-pass matrix.
2. Add a negative test, source-fact row, executable gate, or human-only evidence
   row for it.
3. Re-check whether sibling rows share the same weakness.
4. Update the review prompts from the revised matrix.
5. Resume implementation only after the revised matrix is coherent.

This stop rule prevents the failure mode where review agents become the primary
requirements-discovery mechanism after code is already moving.

## Gate 3B: Skill/Tool Selection Before Customization

Before creating, installing, or activating a custom skill/plugin:

1. Search the preinstalled and repo-approved skills/docs for the needed
   capability.
2. Record the checked options and why they are insufficient.
3. Document source, pin/version, license, telemetry, filesystem/network, hook,
   and credential behavior.
4. Record approval, expiry/revisit trigger, and residual risk.
5. Update the skill lock and third-party notices before use.

If an approved installed skill or repo doc covers the need, use it. Do not
create a parallel custom skill.

## Durability / Restore / Replay Checklist

Adapt this checklist for any project with persisted state, restart recovery,
idempotency, queues, derived data, imports, exports, migrations, or local
snapshot files.

Core data graph invariants:

- list every persisted entity and relationship before coding;
- prove valid restored IDs are insufficient and relationship consistency is
  checked across tenant/user/project/parent/child/run/artifact references;
- validate restored child rows against the owning parent, including owner,
  project, source filename, source checksum, approved or effective timestamp,
  row checksum, and derived text/metadata;
- completed jobs/runs must have the surviving records needed to justify their
  terminal status;
- parent status fields must reconcile with surviving child/job/artifact state;
- terminal idempotency records must reference valid typed restored values or
  serialized terminal errors;
- stale `PENDING` or `RUNNING` records must not replay as terminal results;
- corrupt `FAILED` records without serialized error details must be dropped;
- counters and sequence numbers must derive from restored IDs and tolerate
  missing or stale-low persisted counters;
- rollback after terminal persist failure must remove only failed operation
  effects and preserve concurrent successful operations;
- state pruning must say whether corrupt rows remain on disk until the next
  successful write.

## Derived Artifact Consistency Checklist

Use this when the project creates translations, exports, reports, media,
provider results, downloadable files, manifests, embeddings, indexes, rendered
views, or any other artifact derived from source data.

Required invariants:

- derived text, provider payload, manifest, downloadable artifact, metadata,
  checksums, language/locale tags, provider mode, source references, and
  idempotency records mutually agree;
- restored artifacts are validated from payload bytes/content, not only IDs;
- checksums are recomputed from restored content;
- provider mode is explicit, and local/mock assumptions do not restore external
  provider claims as trusted local state;
- glossary, citation, source-evidence, and safety/disclosure fields survive
  restore or the row is dropped;
- source run identity, retrieved context refs, source citation indexes,
  evaluation ID/status/checksum, and claim-support records stay bound to the
  derived artifact before replay, display, export, or downstream processing;
- corrupted or tampered provider/artifact payloads are rejected before replay,
  display, export, or downstream processing;
- idempotency retry semantics cover completed, failed, pending, running, stale,
  and conflicting requests;
- counters and rollback semantics match the durability checklist.

## Governance / CI / False-Pass Checklist

Use this when the project has CI, branch protection, release gates, issue
automation, PR templates, docs-as-gates, security scans, eval gates, or other
process controls.

Required invariants:

- issue auto-close protections cover title, body, branch commits, edited PR
  body, colon forms, cross-repo refs, full issue URLs, canonical-stage
  exceptions, and extra issue closures;
- final squash/merge message is listed as human-only because CI cannot inspect
  the final editor text before merge;
- preflight evidence requires concrete artifacts, not placeholder rows, empty
  tables, or bare URLs;
- branch-protection verification separates live API-verified settings from
  human-only repository settings;
- required CI contexts are exact and drift-checked when the platform exposes
  them;
- marker-string checks are not sufficient unless each required process claim
  also maps to an executable gate, test, source fact, or human-only checklist
  item;
- security, eval, release, and governance gates include negative tests for known
  bypass syntax and scanner-unavailable behavior.

## Human-Only Review Surfaces

Human-only does not mean optional. It means the repository cannot fully automate
the check, so the PR must name the owner and residual risk.

Common human-only surfaces:

- final squash/merge commit title and body typed in the hosting-platform merge
  dialog;
- repository or organization settings not visible to CI credentials;
- paid provider dashboard settings, billing limits, webhook secrets, and
  production keys;
- legal/license approvals, consent records, and public synthetic-media release
  decisions;
- production incident communications, first-hour launch watch ownership, and
  rollback go/no-go decisions;
- manual accessibility, visual, or user-acceptance checks not covered by
  automated tooling.

Record them like this:

```markdown
| Surface | Automation Gap | Owner | Evidence | Residual Risk Decision | Expiry / Revisit Trigger |
|---|---|---|---|---|---|
| Final squash message | CI runs before the merge dialog text is finalized | repo owner | reviewer checks exact text before merge | accepted for PR only | before merge |
```

## Invariant-to-Test Matrix Template

Copy this table into the project preflight artifact before coding. Replace the
example IDs with project-specific IDs.

```markdown
| ID | Area | Invariant | Old Failure / False-Pass Risk | Positive Test | Negative / Mutation Test | Gate / Source / Human-Only Evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| CORE-RESTORE-001 | Core graph restore | Child records match owning parent identity, source checksum, timestamp, content checksum, and derived metadata | Valid IDs restore while relationships are corrupt | `test_restore_valid_graph` | `test_restore_drops_tampered_child_source`; break-test proves old behavior failed | `make test`; restore gate | owner | pass |
| DERIVED-ARTIFACT-001 | Derived artifact | Provider payload, artifact bytes, manifest, metadata, checksums, language tags, citations, and provider mode agree | Tampered artifact replays from idempotency | `test_replay_valid_derived_artifact` | `test_drop_tampered_artifact_payload`; mutation changes checksum/text | `make test` | owner | pass |
| DERIVED-SOURCE-001 | Derived source binding | Source run, retrieved context refs, evaluation status/checksum, citation indexes, and claim-support records stay bound to the derived artifact | A valid export/artifact ID can replay with source evidence from another run | `test_replay_valid_source_bound_artifact` | `test_drop_artifact_with_mismatched_source_run`; break-test proves old behavior failed | `make test`; source-evidence gate | owner | pass |
| GOV-FALSEPASS-001 | Governance | PR evidence rows include concrete artifacts, full matrix-ID coverage, and old-behavior proof | Placeholder evidence table passes CI | `test_preflight_accepts_complete_mapping` | `test_preflight_rejects_partial_matrix_coverage`; `test_preflight_rejects_without_old_behavior_proof` | `scripts/guardrails_check.py` | owner | pass |
| HUMAN-001 | Human-only surface | Final merge message is inspected before merge | CI passes but final squash message closes the wrong issue | N/A | N/A | human checklist item with owner | repo owner | pass |
```

Completion rules:

- No row may stay `pending` when implementation starts.
- Evidence may be `test`, `gate`, `source`, `human-only`, or `non-goal`.
- Completed PR preflight status must be `pass` or `passed`; `tracked` and
  `accepted` are residual-risk decisions, not completion statuses.
- Partial matrix-ID overlap is insufficient; every failure-matrix ID must be
  covered.
- `human-only` rows need an owner and a residual-risk decision.
- `non-goal` rows need docs that prevent overclaiming.
- If a reviewer finds a missing case, add a matrix row before changing code.

Pre-implementation evidence template:

```markdown
| Requirement | Pre-code artifact | Timestamp / commit / PR comment | Reviewer | Decision |
|---|---|---|---|---|
| Invariant/failure matrix | `docs/path/to/preflight.md` | issue comment: https://github.com/org/repo/issues/<issue>#issuecomment-<id> | reviewer | pass |
| Source facts | `docs/path/to/sources.md` | draft pr: https://github.com/org/repo/pull/<id> | reviewer | pass |
| Human-only surfaces, if any | `docs/path/to/preflight.md` | verified commit order: <matrix-commit> before <implementation-commit> | reviewer | pass |
```

## Definition of Done for Process-Sensitive Work

Process-sensitive work includes durability, restore/replay, idempotency,
rollback, migrations, provider boundaries, CI, branch protection, issue
automation, release readiness, security gates, eval gates, and governance docs.

It is done only when:

- the adapted invariant checklist is in the PR artifact;
- every invariant has a matrix ID;
- every matrix ID maps to positive evidence and, where relevant, negative or
  mutation evidence;
- old false-pass behavior has RED, break-test, mutation, regression, or
  fails-before evidence;
- human-only surfaces are listed with owner and residual risk;
- docs state what remains out of scope and what must not be claimed;
- executable gates fail when required rows, artifacts, or mappings are missing;
- reviewers can verify the matrix without reverse-engineering the code.

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

## Gate 8: Proactive Next-Step Closeout

At the end of every non-trivial repo-governance, PR-review, release-readiness,
durability, security, or implementation turn, the agent or reviewer must state
the next step without waiting for the user to ask.

Minimum closeout:

- current state: branch, PR, issue, head commit, CI/review posture, and local
  worktree posture when relevant;
- recommended next action: the one action the owner should take next and why;
- alternatives: reasonable options and trade-offs, including doing nothing;
- agent-owned next work: what the agent can do without more user input;
- human-owned gates: approvals, reviews, merge-dialog text, repository settings,
  legal/provider decisions, production claims, or other surfaces automation
  cannot safely complete;
- stop conditions: what would keep the PR or release from advancing.

For pull requests, include a merge posture:

```markdown
## Next Step

Current state:
Recommended action:
Alternatives:
I can do next:
Needs human review/approval:
Do not proceed if:
```

Rules:

- Do not end a governance or review turn with only "tests pass" or "CI is
  green" when another review, approval, merge, or human-only gate remains.
- If the PR is not ready, say exactly what keeps it from being ready.
- If the PR is ready, say whether it is ready for review, ready for merge, or
  still waiting on a human-only check such as final squash-message inspection.
- Preserve negative claims explicitly when they matter, such as "this does not
  close the production blocker" or "this does not claim production readiness."

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
- the final response or review note states the recommended next action,
  alternatives, and remaining human-owned gates

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
- Ending a PR, release, or governance turn without telling the owner the
  recommended next step, alternatives, and remaining human-only gates.

## Reusable Sequence

```text
bootstrap -> source control gate -> interview -> spec -> source facts
-> contract -> failure matrix -> RED tests -> implementation
-> adversarial review -> docs/gates -> PR evidence
-> proactive next-step closeout -> merge
```

If a project skips one step, name the skip and why it is safe.
