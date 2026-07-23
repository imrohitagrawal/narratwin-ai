# Issue 274 C3B-PR1 Preflight

## Objective

C3B-PR1 is the public-safe Checkpoint 3B consent/provenance planning gate for
public tracker issue `#249` and child issue `#274`.

The claim is deliberately narrow: this PR reconciles the repository ledger after
PR `#273` merged at `0f737c564f9245b66640988573ac04f4432e06d5` and issue
`#269` closed, records that the currently listed Checkpoint 3A executable
acceptance probe set is complete through CP1-CP8, and defines Checkpoint 3B as
planning only. It does not implement Checkpoint 3B runtime behavior.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3B-PR1-LEDGER-001 | `docs/STATUS.md` records PR `#273` merged at `0f737c564f9245b66640988573ac04f4432e06d5`, issue `#269` closed, issue `#249` still open as the public Checkpoint 3 tracker, and issue `#274` satisfied by this PR when merged. |
| C3B-PR1-C3A-001 | Repository docs state only that the currently listed Checkpoint 3A executable acceptance probe set is complete through CP1-CP8. |
| C3B-PR1-BOUNDARY-001 | Checkpoint 3B is bounded to consent/provenance planning, acceptance contracts, risk boundaries, and future issue sequencing. |
| C3B-PR1-GUARDRAIL-001 | The Phase 1 closure checker accepts the exact issue `#274` branch/file allowlist and rejects near-match branches and unauthorized files. |
| C3B-PR1-NONGOAL-001 | The planning gate does not authorize provider setup, paid spend, hosted deployment, public URLs, cloned identity runtime, real media, public distribution, or production readiness. |
| C3B-PR1-PUBLICSAFE-001 | Public artifacts avoid private strategy, provider choices, reviewer strategy, invite codes, private media, real personal data, provider payloads, provider outputs, secrets, tokens, and credentials. |

## Scope

In scope:

- `docs/governance/preflights/issue-274.json`
- `docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

Out of scope: no backend, no frontend, no provider, no RAG, no avatar, no
database, no Docker, no workflow, no dependency, no hosted deployment, no
public URL, no provider setup, no provider SDK, no provider key, no real
provider call, no paid spend, no cloned identity runtime, no cloned voice, no
cloned face, no digital twin, no real-person likeness, no clone enrollment, no
real media, no public distribution, no Checkpoint 3C, no Product Mode 2, no
production readiness, no private strategy, no provider choices, no reviewer
strategy, no invite codes, no private media, no real personal data, no real
provider payloads, no provider outputs, no secrets, no tokens, and no
credentials.

The boundary also means no provider enablement of any kind.

The PR may bundle repository-ledger cleanup for PR `#273` and issue `#269`
because this is a material C3B planning gate, not a standalone status-only
follow-up. Issue `#249` remains open.

## Source Facts

Accessed date: 2026-07-23.

| Source | Fact used |
| --- | --- |
| https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue | GitHub supports issue-linking from pull requests, and merging a qualifying linked pull request into the default branch can automatically update issue state. |
| https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests | GitHub writing docs define reserved pull-request issue-linking terms, so this branch uses reference-only wording for issues `#249` and `#274`. |

Repository facts:

- `docs/REPOSITORY_GUARDRAILS.md` requires reference-only issue wording for
  non-canonical stage issues and forbids issue-closing keywords in PR title,
  body, and commit messages outside explicit exceptions.
- `docs/STATUS.md` is the repository-tracked governance ledger and allows
  routine GitHub merge facts to be bundled into the next material governance
  update.
- Live GitHub state verified on 2026-07-23: PR `#273` is merged at
  `0f737c564f9245b66640988573ac04f4432e06d5`, issue `#269` is closed, issue
  `#249` is open, and the post-merge `quality` workflow run `29994103118`
  succeeded.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3B-PR1-LEDGER-001 | `docs/STATUS.md` Current Baseline and StatusStateV1 rows | planned RED/green through status invariant checks |
| C3B-PR1-C3A-001 | `docs/STATUS.md`, `docs/QUALITY_GATES.md`, and `docs/TRACEABILITY.md` wording | planned docs/gate check |
| C3B-PR1-BOUNDARY-001 | `docs/STAGE_ISSUE_PLAN.md` issue `#274` section and this preflight | planned docs/gate check |
| C3B-PR1-GUARDRAIL-001 | `tests/unit/test_phase1_closure_docs.py::test_issue_274_branch_has_exact_scope_allowlist` and `tests/unit/test_phase1_closure_docs.py::test_issue_274_near_match_branch_fails_closed` | RED confirmed before checker update; green before PR |
| C3B-PR1-NONGOAL-001 | Non-goal markers in this preflight, status docs, stage issue plan, and quality gates | planned docs/gate check |
| C3B-PR1-PUBLICSAFE-001 | Public-safe wording review and fan-out disposition | planned human-review plus guardrail checks |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3B-PR1-NONGOAL-001 | The planning PR must not authorize provider setup, paid spend, hosted deployment, public URLs, cloned identity runtime, real media, public distribution, or production readiness. | Preflight markers, `docs/STATUS.md`, `docs/STAGE_ISSUE_PLAN.md`, and PR human checklist |
| C3B-PR1-PUBLICSAFE-001 | Public artifacts must not expose private strategy, provider choices, reviewer strategy, invite codes, private media, real personal data, real provider payloads, provider outputs, secrets, tokens, or credentials. | Public-safe review and secrets scan |
| C3B-PR1-GUARDRAIL-001 | Near-match branches and unauthorized changed files must fail closed. | Focused unit tests and `scripts/quality/check_phase1_closure_docs.py` |
| C3B-PR1-TRACKER-001 | Issue `#249` must remain open unless repository-tracked docs explicitly and correctly state that the whole public tracker is complete through reviewed work. | `docs/STATUS.md`, `docs/STAGE_ISSUE_PLAN.md`, PR body, and post-merge closeout rule |
| C3B-PR1-C3A-001 | CP1-CP8 completion wording must not become a Checkpoint 3B, Checkpoint 3C, hosted/public demo, provider, cloned identity, real media, public distribution, or production claim. | Docs/gate markers and fan-out review |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3B-PR1-FM-001 | Repository ledger still says issue `#269` is satisfied by a future PR after PR `#273` has merged. | Update `docs/STATUS.md` and StatusStateV1 to record PR `#273` merged and issue `#269` closed. |
| C3B-PR1-FM-002 | Checkpoint 3A CP1-CP8 completion wording overclaims Checkpoint 3B readiness. | Status, quality, traceability, and preflight text distinguish Checkpoint 3A local/mock evidence from C3B planning. |
| C3B-PR1-FM-003 | C3B planning text authorizes cloned identity runtime or provider/media/hosted work. | Non-goal markers and issue-specific scope forbid runtime, provider, hosted, public, real media, and production work. |
| C3B-PR1-FM-004 | Public docs expose private strategy, provider choices, reviewer strategy, invite codes, private media, real personal data, provider payloads, or outputs. | Public-safe wording review plus secrets and guardrail scans. |
| C3B-PR1-FM-005 | Near-match branch receives the issue `#274` allowlist. | Exact branch comparison plus prefix fail-closed unit test. |
| C3B-PR1-FM-006 | Unauthorized runtime, workflow, dependency, frontend, backend, or third-party notice files are accepted. | Exact changed-file allowlist and unauthorized-file regression test. |
| C3B-PR1-FM-007 | PR body or commit message uses issue-closing keywords for `#249` or `#274`. | Source-backed reference-only policy, forced PR guardrails, and human-only final merge-message row. |
| C3B-PR1-FM-008 | Issue `#249` is closed while the public Checkpoint 3 tracker is still active. | Status docs and closeout instructions keep `#249` open; only issue `#274` may be closed after approved merge. |

## Fan-Out Review Findings

Initial implementation-pausing fan-out was launched before substantive planning
docs were implemented. Four sub-agent reviews covered public-safe scope,
ledger/status consistency, guardrail behavior, and PR-readiness evidence.

Required fan-out prompts covered:

- public/private boundary
- C3A completion wording without overclaim
- C3B consent/provenance planning scope
- cloned-identity implementation exclusion
- provider/hosted/public/production exclusion
- issue `#249` tracker status
- issue `#269`/PR `#273` ledger reconciliation
- guardrail allowlist behavior
- status/traceability consistency
- test/quality/CI
- governance/taste/scope

Disposition before implementation:

- Public/private boundary: accepted; public artifacts use only issue, PR,
  commit, file, command, and source-doc facts, and exclude private strategy,
  provider choices, reviewer strategy, invite codes, private media, real
  personal data, provider payloads, provider outputs, secrets, tokens, and
  credentials.
- Ledger/status: accepted; docs record PR `#273` and issue `#269` as
  merged/closed while keeping issue `#249` open.
- Guardrail/test behavior: RED confirmed for issue `#274` allowlist before the
  checker was updated; the exact branch allowlist and near-match branch
  rejection now have targeted tests.
- Governance/taste/scope: accepted; scope remains docs and checker/test only
  with no runtime or dependency files.

Final fan-out disposition before human review:

- Public/private boundary review: clean after remediation; the artifact uses
  public-safe repository facts only and keeps sensitive categories excluded.
- C3A/C3B wording review: clean after remediation; CP1-CP8 is described only as
  the currently listed Checkpoint 3A executable acceptance probe set, while C3B
  remains consent/provenance planning, acceptance contracts, risk boundaries,
  and future issue sequencing.
- Non-goal review: clean after remediation; no provider setup, no paid spend,
  no hosted deployment, no public URL, no cloned identity runtime, no real
  media, no public distribution, and no production readiness are authorized.
- Tracker/ledger review: clean after remediation; PR `#273` and issue `#269`
  are reconciled as merged/closed, issue `#249` remains open, and issue `#274`
  is the only child issue planned for post-merge closeout.
- Guardrail review: accepted finding; near-match issue `#274` branches were
  initially too broad, including process and default branch fallthrough forms,
  then fixed with exact-branch routing and fail-closed regression coverage.
- PR-readiness review: accepted findings; reserved issue-linking examples were
  removed from this artifact, exact out-of-scope markers were restored, and the
  eventual PR body must include `## Status impact`.
- Final pre-human-review fan-out is clean.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue creation, branch creation, first-commit preflight, allowlist RED/GREEN, planning docs, validation, PR, CI watch, and approval-bound closeout. |
| spec-driven-development | Invoked | Objective, positive claims, negative invariants, failure matrix, and non-goals are defined before substantive planning docs. |
| test-driven-development | Invoked | Issue `#274` allowlist tests failed before checker update and passed after implementation. |
| source-driven-development | Invoked | Official GitHub issue-linking and closing-keyword docs are cited for PR wording policy. |
| security-and-hardening | Invoked | Public/private boundary and secret/provider-output non-goals prevent exposing sensitive material or enabling provider work. |
| api-and-interface-design | Invoked | Consent/provenance remains an acceptance-contract planning boundary only; no API endpoint or schema change is introduced. |
| observability-and-instrumentation | Invoked | The planning gate records future evidence questions without adding telemetry code or production signals. |
| code-review-and-quality | Invoked | Fan-out review and final self-review are required before PR ready. |
| doubt-driven-development | Invoked | Failure modes target overclaim, false allowlist, issue auto-close, and public/private leaks. |
| taste-check | Invoked | Narrow checker additions and docs avoid new abstractions, dependencies, or runtime branching. |
| git-workflow-and-versioning | Invoked | Issue `#274`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | No browser/runtime implementation changes are in scope. |
| frontend-ui-engineering | Rejected | No frontend UI changes are in scope. |
| performance-optimization | Rejected | No runtime performance behavior changes are in scope. |

## Stop Rule

Stop and open a new issue if C3B-PR1 requires backend, frontend, provider, RAG,
avatar, database, Docker, workflow, dependency, hosted deployment, public URL,
provider setup, provider SDK, provider key, real provider call, paid spend,
cloned identity runtime, cloned voice, cloned face, digital twin,
real-person likeness, clone enrollment, real media, public distribution,
Checkpoint 3C, Product Mode 2, production readiness, private strategy, provider
choices, reviewer strategy, invite codes, private media, real personal data,
real provider payloads, provider outputs, secrets, tokens, or credentials.
