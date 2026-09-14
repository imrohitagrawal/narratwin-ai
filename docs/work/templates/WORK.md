# Work record template

Find other canonical forms in the [template catalog](../../templates/README.md). For starting a discovery, bug or implementation issue, follow [CONTRIBUTING](../../../CONTRIBUTING.md).

Use only the sections needed for independently owned work. Read PROCESS before
copying this template. Existing plans are referenced rather than copied.

## README

State stable work ID, purpose, scope, owner, parent/typed dependencies, existing
issues/PRs, current authority sources and reading order. Link plan, decisions,
handoff and evidence. Label candidate, accepted and historical sources separately.

## Plan

State the question/problem, intended result, source requirements, explicit
constraints, non-goals, authority/effective conditions, failure cases, verification
and integration sequence. Keep original source and execution-plan roles distinct.

## Decisions

For each decision record date, exact instruction/source coordinate and custody,
decision owner, reason, authority/effect, constraints, superseded record and next
action. Preserve previous decisions and failures; never silently rewrite history.

## Handoff

Record current plan revision, evidence set, observed repository/source commit and
verification time; current branch/PR and availability; completed work, unresolved
findings, next permitted action, source coverage/omissions, resources and retention.
Include PLAN_SHA256 and EVIDENCE_SHA256 markers. Never bind your own final commit.

## Evidence

Register originals once with owner, stable ID, revision, exact SHA-256 and size,
public locator or opaque restricted reference, custody, verification and derivation.
Consumers list IDs in `uses`. Keep approval, private availability and backup separate.
Place independently reviewed findings under `evidence/reviews/` when produced.

## Comparison or experiment

Record hypothesis, materially distinct candidates/exclusions, baseline, equivalent
content, separate format rankings, acceptance protocol, settings and exact operation
authority before runs. Bind original outputs, review copies and lineage separately.
Preserve failures and report complete duration, generated seconds, actual total cost,
accepted count/level, setup/revision effort and limitations together. Zero accepted
outputs has no finite observed cost per accepted output. A changed hypothesis is a
new revision; a whole-workflow comparison does not isolate a component advantage.
Formal acceptance retains its actual preregistration/matching/calibration/holdout
requirements. Complete API capability and repeat reliability need their own proof.

## Early demonstration and investment decision

Before substantial product/provider integration or production hardening, record:

- Intended user experience, riskiest hypothesis, source/reference identity and custody;
  distinguish owner-reported observations from independently inspected evidence.
- Smallest representative diagnostic, scope, minimum controls, exact operation
  authority and limits; use existing behavior/focused reproduction for maintenance.
- Minimum acceptable output and explicit rejection conditions agreed before running.
- Actual original output, observations, rejected results, uncertainty and reviewer.
- Go/revise/stop decision, its reason, next authorized step and unresolved questions.
- Representative complete-output proof before further adapter/integration investment;
  separate full narration, API suitability, repeatability and formal acceptance evidence.

For presenter output include natural performance and lively, coherent surroundings
appropriate to the intended scene. Inspect synchronization, anatomy and temporal
stability; unrelated motion does not prove quality. Identify the reference clip
before claiming reproduction. Demo existence is not success. Preserve baseline and
failure evidence; required stage, rights, privacy, security and operation/cost gates
apply before the demo. Production hardening follows evidence under its own gates.

## Closeout

Keep the work path after completion. Update authoritative status, decisions and
handoff, retain necessary revisions/sources, reconcile references and verify read-back.
Apply the repository's existing review/merge/cleanup rules. No implicit deletion,
provider, spending, release or backup authority is supplied by this template.

## Conditional discovery and design

For a new product or uncertain feature, link the existing engineering playbook's intent/spec sections from the template catalog. Record the user/job, observations, assumptions, decision sought, alternatives, next bounded investigation and decision owner. No existing PRD is required for discovery; accepted requirements are required before dependent implementation.

For design work, record current/proposed journey, interaction and loading/empty/error/refusal states, keyboard/accessibility and responsive constraints, prototype/source links, evidence, rejected alternatives and the design decision. Label proposed versus accepted work. Keep significant engineering tradeoffs in ADRs and link them; do not duplicate product requirements here.
