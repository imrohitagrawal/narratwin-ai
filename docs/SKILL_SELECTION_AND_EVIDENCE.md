# Skill Selection And Evidence

## Purpose And Decision

This page records how NarraTwin AI selects skills, test levels, tools, gates,
and evidence. It was created from the Mode 1 controlled-local-demo review in
issues `#155` and `#164`, where several capabilities all sounded like
"testing" but proved different boundaries.

The motivating example is concrete: the existing Playwright smoke test uses a
real browser framework but intercepts API requests. It can prove deterministic
frontend handling of mocked responses. It cannot prove the real browser to
Next.js proxy to backend flow, durable avatar consent, or Stage 6 to Stage 7
multilingual artifact binding. A tool name is not an evidence classification.

The governing principle is:

```text
skills govern the method; evidence proves the claim
```

This page also retains negative learning. A skill can be useful because it
produced accepted evidence or because it prevented unsafe or unnecessary work.
A considered skill can be redundant, unavailable, unapproved, ineffective, or
appropriate only at a later stage.

## Canonical Storage Model

The project uses five complementary storage layers:

| Concern | Canonical location | What belongs there | What does not belong there |
|---|---|---|---|
| Repository rules | `AGENTS.md` | Short, mandatory selection and workflow rules | Full skill catalog or per-PR activity |
| Stage sequencing | `docs/SKILL_EXECUTION_PLAN.md` | Stage-aligned skill posture and activation sequencing | Per-invocation outcomes |
| Trust and activation | `docs/SKILL_LOCK.md` | Source, version/pin, license, permissions, approval, activation | Claims that a skill was useful |
| Selection and learning | This page | Taxonomy, routing, metrics, triggers, reusable defaults | Detailed PR execution history |
| Actual execution | Child issue and PR preflight | Invoked, considered, rejected, evidence, result, correction | A second global catalog |

Issue `#155` receives meaningful Mode 1 checkpoint summaries.
`docs/STATUS.md` records durable governance or delivery state changes, not every
skill invocation.

If a tool-specific instruction file is added later, it must point to
`AGENTS.md`; it must not duplicate or compete with repository rules.

## Non-Goals

This policy does not:

- approve, install, or activate a skill;
- make a cached skill repository-approved;
- replace requirements, tests, review, or runtime evidence;
- require every relevant-looking skill to be invoked;
- authorize real audio/video, Mode 2, hosted launch, public distribution, or
  production work;
- change the Mode 1 runtime quality path tracked separately under `#155`;
- revive PR `#163` or unrelated Stage 1 cleanup;
- create a composite skill quality score.

## Vocabulary

| Term | Definition |
|---|---|
| Claim | A statement the change intends to make true, such as "consent is captured before render." |
| Boundary | The trust, process, runtime, module, network, or human boundary across which the claim could become false. |
| Skill or workflow | Instructions that govern how analysis, planning, implementation, testing, or review is performed. |
| Test level | The scope of behavior exercised: unit, component, API, integration, mocked browser, real-stack end-to-end, or manual. |
| Tool or framework | The mechanism used, such as pytest, Vitest, Playwright, Compose, or browser DevTools. |
| Executable gate | A command or CI policy that blocks progression when its contract fails. |
| Evidence artifact | An inspectable result tied to the claim: test, report, exact-commit run, source fact, review record, or approved manual proof. |
| Human-only evidence | Required evidence that automation cannot fully observe, with an owner, decision, and revisit point. |

A single tool may serve multiple test levels. Conversely, multiple tools can
prove the same boundary. Classification follows the boundary actually crossed,
not the product name printed on the tool.

## Selection Rule

Use this order:

```text
claim
→ boundary that could invalidate the claim
→ smallest test capable of disproving it
→ workflow skill governing the method
→ evidence artifact and result
→ higher-level proof only for boundaries not yet crossed
```

Rules:

1. Start from the acceptance claim and its negative invariants.
2. Select the smallest deterministic test that can disprove the claim.
3. Add a higher test level only when the lower level cannot cross a required
   boundary.
4. Name synthetic success, interception, mocks, and human-only surfaces.
5. Never cite skill invocation as completion evidence.
6. Record why materially overlapping skills were not selected.
7. Repository policy, security, consent, license, and stage rules outrank a
   skill recommendation.
8. If a skill is unavailable or unapproved, do not record it as invoked.

## Development Lifecycle Routing Matrix

| Phase | Question being answered | Preferred skill/workflow | Test/tool or artifact | Required evidence | Do not use it for |
|---|---|---|---|---|---|
| Intent audit | What was approved, and what exists now? | `intended-vs-implemented` | Requirements, code, tests, live tracker | Evidence-backed gap table | Implementation or completion proof |
| Discovery | Is the user problem or scope still ambiguous? | interview/discovery skills when confidence is low | Intent brief, assumptions register | Reviewed outcome and non-goals | Reopening a locked checkpoint without evidence |
| Specification | What must be true and remain false? | `spec-driven-development`; PM test scenarios when manual scenarios add value | Acceptance contract and failure matrix | Reviewed contract with boundaries | Claiming runtime behavior |
| API/data contract | How do components exchange identity, provenance, errors, and replay state? | `api-and-interface-design`, documentation/ADR workflow | API schema, data model, compatibility table | Source-backed interface decision | UI styling |
| Task planning | What is the smallest dependency-safe order? | `planning-and-task-breakdown`, incremental implementation | Child issues and dependency graph | Acceptance, validation, files, parallel rule | Replacing a spec |
| Backend/provider/RAG behavior | Does logic satisfy positive and negative invariants? | TDD, security hardening where inputs or providers are untrusted | pytest unit/API/eval tests | RED, GREEN, refactor, failure-path proof | Browser usability claims |
| Frontend component behavior | Does one component render, validate, and transition correctly? | TDD plus frontend UI engineering | Vitest/React Testing Library | Fast deterministic component evidence | Backend integration claims |
| Mocked browser workflow | Does the assembled UI handle expected response shapes? | TDD plus frontend testing | Playwright with route interception | Explicitly labelled mocked browser smoke | Calling the result real-stack E2E |
| API integration | Do frontend requests match backend schemas and typed failures? | API/interface design plus TDD | API tests or frontend against a real local backend | Request/response and negative-contract evidence | Visual confidence |
| Real-stack E2E | Can a user complete the critical flow through the local stack? | Browser-testing workflow plus TDD | Playwright against Compose with no synthetic success interception | Browser → proxy → backend → state evidence at an exact commit | Exhaustive edge-case coverage |
| Exploratory diagnosis | Why is browser or runtime behavior wrong? | Debugging/error recovery and browser DevTools | DOM, console, network, accessibility inspection | Reproduction and diagnostic record | Deterministic CI regression proof |
| Security/accessibility | Is untrusted output safe and is the flow usable? | Security hardening plus frontend engineering | Tamper/XSS, keyboard, semantic and accessibility checks | Negative security and accessibility evidence | Replacing functional flow tests |
| Observability | Can a failed real flow be diagnosed without exposing sensitive content? | Observability/instrumentation | Traces, bounded logs, metrics | Correlated, redacted failure evidence | Inventing production SLO claims |
| Performance | Does an approved performance budget fail predictably? | Performance optimization | Load/profile/Lighthouse tools | Budget result tied to workload and commit | Functional correctness |
| Completion review | Does the evidence cover the complete accepted contract? | Code review, doubt-driven review, verification-before-completion equivalent | Focused tests, quality gate, exact-commit evidence | Consolidated PR evidence and residual risks | Discovering requirements for the first time |
| Release/launch | Are launch, rollback, monitoring, and owner decisions ready? | Shipping/launch only at an approved launch level | Release checklist, runbook, watch evidence | Level-specific Go/No-Go evidence | A controlled local mock demo |

## Mode 1 UI Testing Worked Example

The confirmed Mode 1 gaps are the reference example for boundary selection:

- the frontend skips the durable avatar-consent endpoint and omits
  `consentRecordId`;
- the existing Playwright smoke intercepts APIs and does not prove a real
  browser-to-backend flow;
- Stage 7 reads the original Stage 4 English script instead of the selected
  Stage 6 multilingual bundle;
- the frontend does not expose the JSON voice manifest;
- presenter/checklist evidence stops at grounded script generation.

| Layer | Appropriate proof | What it establishes | What remains unproven |
|---|---|---|---|
| Component | Vitest/React tests | Artifact validation, consent UI state, safe links, errors | Backend schema and state |
| Mocked browser | Intercepted Playwright | Deterministic assembled-UI handling and call ordering against fixtures | Real proxy/backend/state integration |
| API | Backend unit/API tests | Consent, provenance, tampering, replay, typed failures | Browser wiring and user-visible state |
| Real-stack E2E | Non-intercepted Playwright against Compose | Critical browser → proxy → backend → state chain | Broad failure taxonomy and production behavior |
| Exploratory | DevTools/network/DOM inspection | Diagnosis and manual runtime evidence | Repeatable CI regression |
| Completion | Independent contract/evidence review | Coverage reconciliation and residual risks | Missing runtime evidence |

For the controlled local mock demo, Playwright is real-stack evidence only when
the critical success response comes from the real local backend. Interception
used for unrelated failure injection must be named precisely and must not
supply the success being claimed.

## Spec-Driven And Test-Driven Development

Spec-driven development and test-driven development are complementary:

- SDD freezes externally meaningful contracts, acceptance criteria, ownership,
  provenance, replay, and negative invariants before code. It is mandatory for
  the Stage 6 to Stage 7 multilingual source-binding contract and the Mode 1
  quality-path contract.
- TDD converts a behavior or gate contract into observable RED evidence, makes
  the smallest change to reach GREEN, then refactors without weakening proof.
  It governs consent, provenance, artifact, replay, frontend, E2E, and quality
  gate behavior.
- Pure prose does not need artificial unit tests. Prose that defines an
  executable process contract needs a gate or semantic contract test for its
  load-bearing assertions.

The sequence is:

```text
specification → failure matrix → RED → GREEN → refactor
→ exact-boundary verification → independent review
```

## Skill Routing And Timing

### Useful now or in approved Mode 1 chunks

| Skill/workflow | Appropriate use | Inappropriate use |
|---|---|---|
| `intended-vs-implemented` | Compare approved Mode 1 intent with code/tests | Implementation or completion proof |
| `planning-and-task-breakdown` | Dependency-ordered child issues | Replacing a specification |
| `spec-driven-development` | Quality-path and Stage 6→7 contracts | Tiny static fixes |
| `test-driven-development` | Consent, provenance, artifacts, replay, frontend, E2E, gates | Pure prose |
| `incremental-implementation` | One bounded child issue/PR at a time | Combining unrelated cleanup |
| `api-and-interface-design` | IDs, errors, provenance, compatibility | Visual styling |
| `frontend-ui-engineering` | Consent state, artifact visibility, accessibility | Backend agreement claims |
| `security-and-hardening` | Untrusted HTML/JSON, checksums, consent, cross-scope data | Generic visual polish |
| `ci-cd-and-automation` | The directly required Mode 1 quality path | Hosted deployment work |
| `documentation-and-adrs` | Durable Stage 6→7 source-binding decisions | Duplicating an existing source of truth |
| `doubt-driven-development` | Contract and provenance adversarial review | Routine formatting |
| `code-review-and-quality` | Independent pre-merge review | Replacing tests |
| `git-workflow-and-versioning` | Issue/branch/PR/closeout discipline | Broad restructuring |
| `debugging-and-error-recovery` | Unexpected test/runtime failures | Specifying desired behavior |

### Useful later within Mode 1

| Skill/workflow | Activation condition |
|---|---|
| Browser testing with DevTools | Exploratory diagnosis when its required browser integration is available; not a CI substitute |
| PM test scenarios | Presenter/manual Mode 1 acceptance after the contract freezes; do not duplicate backend TDD matrices |
| Observability/instrumentation | Real-stack evidence shows failures cannot be diagnosed from current traces/logs |
| Code simplification or taste check | Behavior is correct and review finds avoidable complexity |
| PM strategy red-team | Checkpoint claim review after approval and skill-lock reconciliation |
| Shipping artifacts | A concrete documentation coverage gap remains; do not create a parallel documentation tree |

### Correctly deferred

- Performance optimization until an accepted Mode 1 performance requirement or
  the existing performance track needs it.
- Shipping and launch until hosted or production launch work is approved.
- Deprecation/migration unless the Stage 7 API cannot evolve compatibly.
- Privacy-policy drafting until external users or personal/customer data enter
  scope.
- Pricing, market sizing, personas, monetization, brand, banners, slides, image
  generation, Atlassian, resume, NDA, spreadsheet, and presentation workflows.
- Plugin or skill creation because no unmet capability currently justifies it.
- Obra/Jesse Vincent Superpowers until the trigger below authorizes evaluation
  and the owner separately approves any installation.

## Availability And Approval States

Always record these separately:

```text
present on disk
≠ available to invoke in the current session
≠ approved and operational for NarraTwin
```

- Present on disk describes local files or a cache only.
- Available to invoke means the current agent runtime exposes the skill and its
  required integrations.
- Approved and operational means the repository trust/activation requirements
  in `docs/SKILL_LOCK.md` are satisfied for the stage.

Reading or consulting exposed guidance under an explicit user instruction is
not the same as repository-approved invocation or activation. Record that case
as guidance consulted in-session, name the unresolved lock state, and do not
claim repository approval, activation, or completion evidence.

Browser DevTools guidance, for example, may be present while its required MCP
integration is unavailable. Superpowers may exist in a temporary cache while
remaining neither invokable nor repository-approved. Neither may be claimed as
invoked on that basis.

## Per-Change Skill Ledger

Every non-trivial child issue and PR preflight should include:

| Phase | Claim/boundary | Skill or source considered | Decision | Reason | Evidence produced or action prevented | Outcome classification | Reuse decision |
|---|---|---|---|---|---|---|---|
| example | browser/backend integration | browser-testing workflow | invoke | boundary requires a real browser | exact-commit non-intercepted E2E result | useful; produced evidence | candidate default |

Allowed outcome classifications:

- useful and produced accepted evidence;
- useful and prevented an unsafe or unnecessary action;
- guidance consulted in-session; repository activation not claimed;
- considered but redundant;
- unavailable or unapproved;
- invoked but ineffective;
- invoked at the wrong stage.

An invocation without an identifiable decision, evidence artifact, or prevented
unsafe action is ceremonial and must not be promoted as a default.

## Measurement Model

Use raw measures first. If a denominator is zero, report `N/A`; do not convert
it to a perfect score. Record numerator, denominator, calculation date, issue or
PR set, and reviewer.

| Measure | Formula | Why it matters |
|---|---|---|
| Claim coverage | claims with identified evidence / applicable claims | Detects unverified requirements |
| Boundary coverage | tested trust/runtime boundaries / required boundaries | Prevents lower-level tests being mistaken for integration proof |
| Negative-invariant coverage | invariants with negative, mutation, source, or human evidence / total invariants | Measures failure-path coverage |
| Skill evidence yield | invocations producing accepted evidence / total invocations | Identifies ceremonial use; interpret with prevented-action outcomes |
| Selection rationale coverage | non-selected candidates with recorded reasons / non-selected candidates considered | Preserves negative learning |
| Real E2E integrity | critical E2E paths without synthetic success interception / critical E2E paths | Detects false E2E claims |
| Evidence freshness | runtime evidence tied to exact commit or CI run / runtime evidence records | Prevents stale proof |
| Late defect escape rate | defect classes first found after their intended gate / total defect classes | Shows whether routing selected the wrong boundary or test level |
| Duplicate-artifact rate | artifacts duplicating an existing source of truth / artifacts created | Detects process bloat |
| Default reuse success | promoted-default uses without routing correction / total promoted-default uses | Tests whether learned defaults generalize |

Skill evidence yield is not sufficient alone. A correctly selected skill can
prevent unsafe work and intentionally produce no code artifact. Report that
outcome alongside the ratio.

## Measures We Do Not Optimize

Do not target or reward:

- total skills invoked;
- skills per PR;
- number of test frameworks;
- raw test count without requirement mapping;
- document count;
- a composite skill quality score.

These measures are easily gamed and reward ceremony or duplication rather than
evidence quality.

## Verification-Skill Activation Trigger

Obra/Jesse Vincent Superpowers verification guidance is not installed,
activated, or approved for NarraTwin by this policy. Its verification principle
overlaps current TDD, `make quality`, PR evidence, independent review,
exact-commit verification, and merge closeout.

The trigger is:

```text
When at least 3 eligible Mode 1 PRs have merged since the current evaluation
baseline, and at least 2 qualifying completion defect classes from those
eligible PRs have been discovered after merge since that same baseline despite
declared green evidence, set the state to FIRED.
```

FIRED authorizes a capability and trust evaluation only. It never authorizes
installation or activation. Installation requires explicit repository-owner
approval through a dedicated issue, branch, PR, source/pin/license review,
filesystem/network/telemetry/hook/credential review, `docs/SKILL_LOCK.md`, and
`docs/THIRD_PARTY_NOTICES.md`.

An eligible Mode 1 PR must:

- be linked to `#155` or a Mode 1 child issue;
- be merged, not merely opened;
- declare green test/quality evidence;
- claim completion of a defined acceptance contract;
- include the skill-selection ledger.

A qualifying completion escape must:

- be discovered after merge;
- arise from an eligible PR counted after the current evaluation baseline;
- violate that eligible PR's approved acceptance contract;
- belong to a boundary the declared evidence claimed to cover;
- represent a defect class, not repeated occurrences of one defect.

Qualifying completion escapes are counted only when discovered after merge.
An explicit pre-merge completion claim does not override the exclusion for
findings caught before merge.

The following do not count:

- new requirements;
- predeclared limitations;
- deferred real media, Mode 2, hosted, public, or production work;
- external CVEs or provider changes unrelated to the PR behavior;
- findings caught before merge;
- cosmetic preferences outside acceptance criteria.

After every completed evaluation, record a new baseline. A future trigger needs
another three eligible PRs and two qualifying escapes after that baseline; it
does not remain permanently fired.

Allowed states are:

- `ARMED`;
- `FIRED`;
- `EVALUATING`;
- `EVALUATED_NO_INSTALL`;
- `APPROVED_FOR_INSTALLATION`;
- `ACTIVATED`.

Legal transitions and their authority are:

- `ARMED` → `FIRED` when both documented thresholds are met; the issue/PR
  reviewer records the evidence and the repository owner confirms the state in
  `#155`.
- `FIRED` → `EVALUATING` when a dedicated read-only capability/trust evaluation
  issue begins. This does not authorize installation.
- `EVALUATING` → `EVALUATED_NO_INSTALL` when the evaluation concludes that
  existing routing should be fixed or no capability gap exists.
- `EVALUATING` → `APPROVED_FOR_INSTALLATION` only with explicit repository-owner
  approval recorded in the dedicated issue.
- `APPROVED_FOR_INSTALLATION` → `ACTIVATED` only after the dedicated
  issue/branch/PR, trust review, lock, notices, CI, and merge closeout complete.
- `EVALUATED_NO_INSTALL` → `ARMED` when the new evaluation baseline is recorded.

All state changes are repository changes made through the issue/branch/PR
workflow. No agent may infer installation authority from a counter or state
label.

When the threshold fires:

1. Record the qualifying PRs and escaped defect classes.
2. Identify which existing control should have caught each defect.
3. Compare approved existing workflows with the candidate verification skill.
4. Review source, immutable pin, license, filesystem/network/telemetry, hooks,
   and credential behavior.
5. Decide whether the gap is new or existing routing was not followed.
6. Recommend one of: fix existing routing; run a bounded evaluation without
   activation; or request installation through a dedicated issue/branch/PR.
7. Ask for and wait for explicit owner approval before installation.

## Trigger Baseline

| Evaluation baseline | Eligible Mode 1 PRs | Qualifying escapes | State | Decision |
|---|---:|---:|---|---|
| Initial — 2026-07-15 | 0 | 0 | ARMED | Superpowers not installed; evaluate only if the threshold fires |

Per-PR observation table:

| PR | Contract completed | Declared green evidence | Escaped defect class | Expected catching gate | Qualifies? |
|---|---|---|---|---|---|
| None at initial baseline | N/A | N/A | N/A | N/A | no |

Update issue `#155` with a checkpoint summary when the state changes. Update
`docs/STATUS.md` only when the trigger fires, an evaluation decision is
recorded, or activation state changes.

## Issue 164 Pilot Record

The actual planning and review ledger for this policy belongs to issue `#164`
and PR `#165`, as required by the Canonical Storage Model. It is not duplicated
here. The issue record must distinguish guidance consulted in-session from a
repository-approved invocation: the PM bundle and the broad Addy Osmani bundle
remain pending or guidance-only under `docs/SKILL_LOCK.md`. Their appearance in
the runtime catalog does not change that trust state.

The durable learning promoted from the pilot is the selection order, outcome
taxonomy, routing matrices, raw measures, and trigger contract on this page.
Session-specific tool versions, invocation outcomes, and review evidence remain
in the issue and PR preflight.

## Maintenance And Promotion

- Record each non-trivial change's selection ledger in its issue/PR.
- Recalculate raw measures after the first three eligible Mode 1 PRs, not after
  arbitrary activity.
- Promote a routing choice to a reusable default only after at least three uses
  with no material routing correction, or with reviewed evidence explaining why
  the correction does not invalidate the default.
- Demote a default when late defect escapes show that it selected the wrong
  boundary or test level.
- Automate only after at least three Mode 1 PRs make the record shape stable.
  Until then, use Markdown rather than a premature JSONL schema.
- Revisit the Superpowers trigger at each Mode 1 checkpoint and when its state
  changes; do not install it simply because it is present in a cache.
- Keep the catalog concise. Add a skill family only when it changes selection,
  evidence, or a future activation decision.
