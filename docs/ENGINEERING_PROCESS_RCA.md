# Engineering Process RCA

## Status

Proposed in PR `#54`; accepted as a standing project reference after PR `#54`
is reviewed and merged.

This file must be consulted before NarraTwin requirement gathering, feature
discussion, architecture locking, implementation, review, release-readiness
claims, and governance-gate changes. It records why PR `#54` repeatedly
surfaced new blockers despite using specs, tests, review agents, and quality
gates.

This is a blameless engineering RCA. The failure was not lack of effort. The
failure was that the process had good skills available but did not make their
outputs load-bearing before code and claims moved forward.

## Evidence Base

Local repository and GitHub evidence collected on 2026-07-08:

- Initial RCA snapshot for PR `#54`: `06d003ccdc10841bab9c0e42cbe27a3e25b73c15`.
- External-review snapshot for PR `#54`: `8640bb1f641294394a93d0fcfa1223d08f4b21e5`.
- Branch: `phase-1-closure-39-durability-monitoring`.
- Single branch commit over `origin/main`: `fix: add local durability and ops status`.
- Git reflog shows repeated amended heads for the same logical change:
  `5c9926d`, `90f4d12`, `63b0f76`, `931fe15`, `122616f`, `1d9de54`,
  `350405a`, `2027482`, `a41a922`, `ba5d5a7`, `84df3d4`, `06d003c`, and
  `8640bb1` from 2026-07-03 through 2026-07-08.
- Diff size at `8640bb1`: 37 files, 3399 insertions, 85 deletions.
- Issue `#39` is still open: `Final Review: resolve production durability and
  monitoring blockers`.
- PR `#54` review state is `REVIEW_REQUIRED`; merge state is `BLOCKED` because
  approval is still required, while all listed GitHub status checks are green.
- PR body validation evidence at `0665bc8` listed:
  - `tests/unit/test_guardrails_check.py`: 17 passed
  - `tests/unit/test_local_durability.py`: 19 passed
  - `tests/unit tests/api`: 166 passed
  - Ruff, mypy, repository guardrails, `make phase1-closure-quality`, and
    `make quality` passing
- `.github/pull_request_template.md` already required invariant,
  exploit-matrix, and contract/gate review, but did not require a linked
  artifact, matrix, or machine-checkable evidence row.
- `docs/REVIEW_RIGOR_RETROSPECTIVE.md` already warned that green gates are not
  proof of release readiness and that sub-agents must be proof generators, not
  generic reviewers. PR `#54` repeated the same pattern.
- `docs/AI_BUILD_BRIEF.md` already says "Do not start coding immediately" and
  requires product discovery, spec-driven development, architecture/ADRs,
  vertical-slice planning, TDD, AI evaluation gates, security-by-design,
  observability, and release-readiness review.
- `docs/QUALITY_GATES.md` says gates are executable stage contracts, but PR
  `#54` proved that an executable gate can still be incomplete when the contract
  omits important negative cases.

PR `#54` Finding Evidence Table:

| Source | Date / SHA | Missing Invariant | Remediation Evidence |
|---|---|---|---|
| Local adversarial review | 2026-07-04, `63b0f76` | PR title/body/merge text must not auto-close `#39`; corrupt snapshots must not brick app import | title/body changed to reference-only wording; corrupt JSON restore tests added |
| Local adversarial review | 2026-07-07, `931fe15` | Valid JSON with wrong shapes must degrade safely, not only malformed JSON | restore guards expanded for wrong-shape rows, bad counters, malformed RAG store payloads |
| Local adversarial review | 2026-07-07, `122616f` | Nested non-object `ragStore` must not crash app import | `ragStore` restore path hardened and regression covered |
| Local governance review | 2026-07-07, `350405a` | Guardrails must reject closing keywords in PR title/body, not only require linkage | PR title fixed and guardrail tests added for title/body closing keywords |
| Local governance review | 2026-07-07, `2027482` | GitHub closing keyword grammar includes colon, repository-qualified, URL, and commit-message forms | guardrail regex and tests expanded to those forms |
| Independent local sub-agent review | 2026-07-08, `84df3d4` | Completed idempotency refs must not dangle; missing counters must not reuse IDs; persistence failure must not leave in-memory success | Stage 4/6/7 restore and rollback logic hardened; local durability tests expanded |
| Independent local sub-agent review | 2026-07-08, working tree after `06d003c` | Stage 7 render persistence and terminal idempotency completion must be one transaction | Stage 7 split-persist path removed; regression added for terminal persist failure |
| External adversarial LLM review | 2026-07-08, `8640bb1` | The RCA was not in `AGENTS.md`; `#39` close protection was branch-name-bound; guardrail tests and CODEOWNERS were weak; Stage 7 rollback could erase a concurrent committed render | `AGENTS.md` required reading added; `#39` closing guard made issue-based; CODEOWNERS/status tracking expanded; concurrent Stage 7 persist-failure regression added |
| Local adversarial sub-agent review | 2026-07-08, `0665bc8` | PR body edits did not rerun policy gates; Stage 6 rollback could erase concurrent committed idempotency; restored Stage 6/7 provider claims bypassed local-only validation; preflight evidence was marker-only | `pull_request.edited` added to policy gate; Stage 6 surgical rollback and tamper-restore tests added; preflight PR body evidence gate added |

These review findings came from chat/local agent review artifacts and live
execution, not from GitHub PR review comments. The absence of checked-in review
artifacts before this RCA is itself one of the process failures.

External references consulted for this RCA:

- GitHub Docs, "Linking a pull request to an issue": closing keywords work in
  PR descriptions and commit messages; supported syntax includes same-repo
  issues, cross-repo issues, uppercase, and colon forms.
  https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
- GitHub Docs, "Configuring commit squashing for pull requests": squash default
  messages may include PR title, commits, and optionally PR description.
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests
- NIST SP 800-218 SSDF: secure development practices should be integrated into
  the SDLC and should address root causes to prevent recurrence.
  https://csrc.nist.gov/pubs/sp/800/218/final
- OWASP SAMM Requirements-driven Testing: requirements tests must include both
  positive and negative testing, including misuse and abuse cases.
  https://owaspsamm.org/model/verification/requirements-driven-testing/
- OWASP SAMM Threat Assessment: project risk should be identified from software
  functionality and runtime characteristics, with threat modeling becoming
  standardized and periodically reviewed.
  https://owaspsamm.org/model/design/threat-assessment/
- Google SRE, "Postmortem Culture": postmortems need impact, root causes,
  preventive actions, and review; no postmortem should be left unreviewed.
  https://sre.google/sre-book/postmortem-culture/
- DORA Research: high-quality internal documentation is foundational for
  technical capability adoption, and AI benefits depend on the underlying
  socio-technical system rather than tools alone.
  https://dora.dev/research/

## What Actually Failed

### 1. Skills Were Available, But Their Outputs Were Not Entry Criteria

The project had the right named skills and documents:

- `interview-me` for intent extraction
- `spec-driven-development` for concrete requirements and boundaries
- `test-driven-development` for RED/GREEN/REFACTOR proof
- `doubt-driven-development` for fresh-context adversarial review
- `code-review-and-quality` for multi-axis review
- `source-driven-development` for official-source verification
- `documentation-and-adrs` for durable decision context

The gap was sequencing and evidence. We treated the skills like review style and
confidence boosters, not as required artifacts that block coding. For PR `#54`,
the invariant matrix and negative cases became clearer only after reviewers
found failures.

Corrective interpretation: a skill has not been used for a high-stakes change
unless its output is visible in the PR as a reviewable artifact or test matrix.

### 2. The Initial Requirement Did Not Separate Positive Claims From Negative Invariants

Issue `#39` was production durability and monitoring. PR `#54` intentionally
implemented only local restart-recovery evidence and ops posture visibility
without closing production readiness.

The positive requirement was clear enough:

- add optional local JSON snapshots
- add `/api/v1/ops/status`
- preserve local-only/no-production claims

The negative invariants were not first-class early enough:

- merging the PR must not close issue `#39`
- local snapshots must not be described as production durability
- corrupt or incompatible snapshots must not brick app boot
- ops status must not disclose paths, secrets, raw uploaded content, generated
  output, or snapshot payloads
- idempotency replay must not silently return `None`
- missing counters must not cause ID reuse
- persistence failure must not leave in-memory success behind a failed request

The repeated bugs were not random. They were missing rows in the negative
invariant matrix.

### 3. Source-Driven Development Was Applied After Platform-Semantics Bugs Appeared

The initial guardrail missed GitHub's full issue-closing grammar. External
GitHub documentation would have shown up front that closing keywords may appear
in commit messages, may use colon forms, and may target cross-repo/full-syntax
references.

Data point: the PR later needed explicit guardrail tests for:

- safe `Refs #39`
- forbidden title `Resolve #39`
- forbidden body `Fixes #39`
- forbidden colon form `Fixes: #39`
- forbidden cross-repo form `Closes imrohitagrawal/narratwin-ai#39`
- forbidden issue URL form
- forbidden commit-message form

This was a requirements-source miss. The repository platform was part of the
runtime behavior, but we initially reviewed it like wording instead of a
state-changing API.

### 4. TDD Was Reactive Instead Of Matrix-Driven

The current test suite is strong, but its growth pattern shows the gap. Tests
for corruption, guardrail keywords, dangling idempotency, missing counters, and
write-failure rollback exist now because reviews found those issues.

TDD was used for bug fixes after discovery. It was not used as a pre-code
failure-mode derivation step.

Corrective interpretation: for high-risk behavior, RED tests must be generated
from the failure-mode matrix before implementation, not from review findings
after implementation.

### 5. Architecture Review Did Not Attack Duplicated State And Transaction Semantics First

PR `#54` touched Stage 4, Stage 6, and Stage 7 state restore paths. The same
state concepts repeated across services:

- state file schema handling
- invalid JSON/non-object handling
- wrong-shape row handling
- stale in-flight idempotency handling
- completed idempotency reference resolution
- counter restoration and derivation
- persistence after memory mutation
- terminal idempotency commit and value persistence as one transaction

The repeated bug classes across stages show an architecture smell: shared
semantics were implemented as parallel service-local logic before a contract
test matrix proved parity.

The Stage 7 split-persist bug found during this RCA made the deeper issue
explicit: the duplicated contract was not only "how do we restore state?" but
"what is the atomic state transition for memory, disk, counter, artifact, and
idempotency record?"

Corrective interpretation: when a behavior is copied across stages, the review
unit is not "each file looks correct"; the review unit is the shared state-model
contract and its parity table.

### 6. Green CI Was Mistaken For Contract Completeness

At multiple points, local tests and CI were green while new blockers still
existed. Current PR data makes the distinction concrete:

- All listed GitHub checks were green at `06d003c` and again at `8640bb1`
  before the external-review hardening changes in this RCA follow-up.
- PR state still requires review and merge is blocked.
- The PR body includes many post-review fixes that were not part of the first
  green state.

Green checks mean implemented checks passed. They do not prove that the checks
represent the full requirement, platform behavior, failure taxonomy, or
production/non-production boundary.

### 7. Reviews Were Too Broad Before They Were Precise

The review requests asked for many valuable perspectives: code quality,
architecture, API, documentation, adversarial staff review, and independent
sub-agents. The problem was not the number of reviewers. The problem was that
reviewers were often asked after implementation, and the prompts initially did
not force a concrete matrix of disproof cases.

This repeated the failure already documented in
`docs/REVIEW_RIGOR_RETROSPECTIVE.md`: broad review can validate visible code
instead of attacking the load-bearing invariants.

Corrective interpretation: every adversarial reviewer must receive:

- exact commit
- explicit contract
- exact invariants to disprove
- negative cases to execute or reason through
- instruction to report only data-backed issues, with file/line evidence

### 8. The PR Template Had A Checkbox, Not A Gate

The pull request template already had a checkbox for invariant,
exploit-matrix, and contract/gate review. That checkbox did not prevent this
loop because it did not require:

- a linked preflight artifact
- a complete failure matrix
- a matrix-to-test mapping
- a source-citation row for platform semantics
- reviewer signoff on the matrix before coding
- a stop rule when repeated blockers appear

Corrective interpretation: a checkbox without an inspectable artifact is weak
evidence.

## Root Causes

1. **Entry criteria were advisory.** The project had good practices, but the
   process allowed coding to begin before a signed-off invariant/failure matrix
   existed.
2. **Negative requirements were under-specified.** The key failures were about
   what must not happen: no auto-close, no boot brick, no path disclosure, no
   ID reuse, no `None` replay, no state divergence.
3. **Official platform semantics were not sourced before implementation.** The
   GitHub auto-close behavior was a platform contract and should have been
   read from official docs before writing regexes or PR wording.
4. **TDD followed bugs instead of preceding them.** Regression tests were added
   well, but after review-discovered failures.
5. **Shared behavior lacked a shared contract.** Stage 4/6/7 restore semantics
   drifted because the abstraction was "three services" rather than "one local
   state contract with service adapters."
6. **Review prompts optimized for coverage breadth before disproof depth.**
   Expert roles are useful only after the artifact and contract are small and
   adversarial.
7. **No stop rule triggered a process review.** After repeated blocker
   discoveries in the same PR, the process continued patching instead of
   pausing to analyze why blockers kept escaping.

## What Could Have Prevented This

The following would have prevented or sharply reduced the loop:

1. A pre-code `#39` local-closure contract with explicit positive and negative
   invariants.
2. An official-source pass before implementation for GitHub issue-closing
   semantics and filesystem/state durability claims.
3. A state-restore failure matrix covering invalid JSON, non-object JSON,
   schema mismatch, wrong row shape, wrong nested type, missing counters,
   dangling references, stale in-flight records, and write failures.
4. RED tests generated from that matrix before implementation.
5. A parity table requiring Stage 4, Stage 6, and Stage 7 to handle the same
   restore/idempotency/counter classes consistently.
6. A pre-implementation adversarial sub-agent review of the contract and matrix,
   not only the code.
7. A stop rule: after two substantive post-review blockers in one change, pause
   and perform an RCA before continuing.
8. A PR requirement to attach the preflight matrix and matrix-to-test mapping,
   not just check a box.

## Required Future Workflow For NarraTwin

Use this workflow for every non-trivial NarraTwin change.

### 1. Intent Gate

Before feature discussion or coding:

- State the user/problem/outcome in one paragraph.
- State confidence in the requirement.
- If confidence is below 95%, use an interview flow before spec or plan.
- Explicitly list non-goals and "must remain false" constraints.

### 2. Source Gate

Before implementation where a platform/tool behavior matters:

- Identify official sources.
- Extract the relevant behavior into the spec or preflight artifact.
- Record unverified assumptions as blockers or risks.

Examples:

- GitHub issue auto-close behavior
- framework routing/API behavior
- database transaction semantics
- filesystem durability guarantees
- CI branch-protection/ruleset semantics
- provider API contract and failure modes

### 3. Contract Gate

Write a short preflight artifact containing:

- positive claims
- negative invariants
- trusted/untrusted boundaries
- data/state lifecycle
- failure-mode matrix
- docs that must match behavior
- gates/tests that prove each row

This artifact must exist before coding for high-stakes behavior.

### 4. TDD Gate

Convert the failure matrix into tests before implementation.

For every matrix row, mark one of:

- `test`: a failing test exists and will be made green
- `manual`: manual proof is required and recorded
- `source`: official source proves behavior outside repo control
- `non-goal`: consciously out of scope, documented in user-facing docs

Rows without one of those statuses are unresolved.

### 5. Architecture Gate

If the behavior repeats across stages/modules:

- Create a parity table.
- Prefer a shared contract/helper where it reduces drift.
- If duplication remains, explain why and require identical tests per service.

### 6. Doubt Gate

Before merging non-trivial work:

- Spawn at least one fresh-context adversarial reviewer with only the artifact
  and contract.
- Ask the reviewer to disprove the contract, not approve the implementation.
- Reconcile each finding as contract misread, actionable, trade-off, or noise.
- Offer cross-model review for high-risk or repeated-failure work.

### 7. Stop Rule

Pause implementation and run this RCA process when any of these happen:

- two substantive blockers are found after an "all checks pass" state
- the same class of bug appears in two modules
- a PR needs three or more force-pushed/amended heads after review starts
- a guardrail misses a behavior documented by an official source
- tests are added only after an external reviewer finds the scenario

### 8. PR Evidence Gate

Every non-trivial PR must include or link:

- preflight artifact
- matrix-to-test mapping
- source citations for platform/tool semantics
- local validation commands
- residual risks and non-goals
- reviewer prompts or review summaries for adversarial reviews

## Practical Checklist

Before coding:

- [ ] Intent and non-goals are explicit.
- [ ] Source docs are checked for platform/tool semantics.
- [ ] Positive claims and negative invariants are listed.
- [ ] Failure-mode matrix exists.
- [ ] Tests are planned from the matrix.
- [ ] Shared/repeated behavior has a parity table.
- [ ] A fresh-context reviewer has attacked the contract if the change is high
      risk.

Before review:

- [ ] All matrix rows are mapped to test/manual/source/non-goal evidence.
- [ ] Docs match implementation.
- [ ] Gates check the important behavior, not just marker strings.
- [ ] PR title/body/branch commit messages are reviewed as behavior when they
      affect GitHub automation.
- [ ] Residual risks are named and accepted or tracked.

Before merge:

- [ ] CI is green.
- [ ] Review is complete.
- [ ] No open blockers remain.
- [ ] `docs/STATUS.md` is updated for governance/stage changes.
- [ ] Stop-rule conditions have been checked explicitly.
- [ ] Final merge/squash commit text is inspected before clicking merge when
      issue-closing semantics matter, because PR CI cannot see the editor's
      final merge message.

## Reusable Lesson

The missing capability was not "more skills." It was turning skills into
ordered, inspectable, and enforced work products:

```text
intent -> source facts -> contract -> failure matrix -> RED tests
-> implementation -> adversarial proof -> docs/gates -> merge
```

If that chain is broken, review quality becomes dependent on who happens to ask
the right question later. That is the loop PR `#54` exposed.
