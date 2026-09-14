# Stable working records — Issue #535 / draft PR #536

Execution authority: the user requested implementation after three independent
design reviews and their final verification. The exact reviewed design and findings
are in [the proposal](proposals/2026-09-14-structure/PLAN.md) and its REVIEW.md.
The prospective scope amendment was posted to PR536 before new code and committed
as preflight-only `74b15e00`. Original first commit `5392dfe1` remains unchanged.

## Contract and scope

Implement stable public work records, generated navigation, one source owner,
shared human/agent entry flow, reusable capture/handoff guidance and executable
integrity checks. Preserve established PRD/contracts/STATUS/ADR/traceability authority,
all recovered private originals, frozen V2/carrier bytes and prior failed evidence.
The active comparison proposal moves logically to demo-comparison, with an exact
copy and historical original. Existing source verification stays separately pinned.

Nine initial records reconcile all 58 issues in the reviewed source snapshot.
These are navigation parents, not transfers of issue scope or closure decisions.
New live issues require explicit reconciliation; no exhaustive historical audit is
claimed. Records requiring a plan from another branch remain there until integrated.

Root is sole writer in the existing isolated Issue535 worktree. Three independent
agents perform bounded read-only preflight and implementation reviews. Shared dirty
tracked files are hash-inventoried before work and preserved. Resource ledger precedes
allocation: at most 1 MB new text and 50 MB temporary tests, no private copies or
provider spend; the existing worktree is reused. Retain all sources. Required `uv run` bootstrapped
a 363 MiB local environment from the existing lock/cache instead of reusing one;
that allocation was recorded after creation as a resource-ledger omission, not
misrepresented as preallocated. No dependency files or private sources changed.

## Failure matrix and verification

| ID | Failure to reject / boundary | Verification |
|---|---|---|
| WR01 | Duplicate work or artifact identity, dangling consumer/owner | Positive multi-work fixture plus duplicate/missing-reference mutations |
| WR02 | Missing observed issue or duplicate ownership | Pinned source census compared with all assignments |
| WR03 | Missing or altered plan and stale handoff | Real file reads, exact plan and evidence-index hashes |
| WR04 | Parent/prerequisite cycle; unrelated reciprocal links falsely rejected | Mixed-edge cycle mutation and valid reciprocal relation fixture |
| WR05 | Escaping path, symlink or forced private tracking | Safe component reads, traversal/symlink and Git-index negative tests |
| WR06 | Stale generated navigation or entry links | Byte comparison against generated INDEX plus clean-checkout read-flow review |
| WR07 | Generic metadata replaces exact original-source verification | Separate selected G1 profile binds all eleven authoritative descriptors; retained original checker tests |
| WR08 | Public checks imply private access/backup/acceptance | Explicit NOT_CHECKED/UNPROVED/NOT_GRANTED outputs and negative assertions |
| WR09 | Lost legacy scope/gates or undocumented budget expansion | Existing scope and runner tests; manifest exact paths and charged-line limits |
| WR10 | Candidate V2, comparison or active evidence gains authority from location | Independent authority/cold-start review, unchanged frozen subjects |
| WR11 | Source migration loses bytes or history | Exact comparison copy, unchanged private inventory/descriptors and read-back |
| WR12 | Tool-specific rules diverge or anchored AGENTS silently changes | Thin CLAUDE bridge, mandatory STATUS/CODEX flow, unchanged AGENTS hash and prepared separate consumer |

Meaningful negative tests start from a passing fixture and change the specific
contract boundary. Initial import failure established the absent utility only;
it is not claimed as behavioral RED. Mutation/rejection results provide behavioral
evidence. Full applicable repository commands and actual hosted topology remain
required before exact-head approval; this plan never substitutes a local pass.

## Implementation sequence and constraints

1. Publish amended exact scope and sources before code; preserve original history.
2. Implement generic schema, records, generated index and source-specific profile.
3. Wire README, top STATUS, CODEX and tracked CLAUDE; preserve mandatory reading.
4. Verify source retention, public-only behavior, private read-back and cold starts.
5. Independently review, triage/reproduce findings, and verify blocker corrections.
6. Run actual applicable local/hosted commands and reconcile PR evidence.
7. Keep PR536 draft until its required checks and original PR534 carrier dependency
   permit integration; refresh from verified current main then. No certification,
   accepted-current transition or provider operation is implied.

AGENTS already requires STATUS/CODEX, so the new procedure is in its mandatory read
flow. An explicit heading is prepared in [the consumer patch](proposals/agent-entry.patch).
The current single-hash anchor cannot accept a naive anchor-first replacement while
old AGENTS remains. [Transition requirements](proposals/AGENT_ENTRY_TRANSITION.md)
record the independently reproduced limitation. Keep that authority change separate;
never bypass the anchor or misreport the prepared patch as applied.

## Skills, sources and review limits

Existing required repository documents, the independently reviewed design and exact
source inventory govern this increment. Local work-package guidance was consulted;
its installed bytes/scope differ from the repository-approved Issue524 activation,
so it is not activated or treated as implementation authority. No custom skill,
dependency, paid service or provider is introduced. Repository-native preflight,
TDD/negative tests, single-writer isolation and independent review cover the boundary.
The broad documentation/PM skill bundles were unnecessary and were not activated.

Human/agent review owns semantic source interpretation, disclosure judgment, authority
labels and final merge wording. Automation checks recorded relationships; it cannot
prove all discussions were captured. Source-format capture regressions from the
recovery remain historical evidence, not a newly implemented conversation collector.
Independent backup remains UNPROVED under #532. Broader lifecycle automation remains
with #391. Repeated blockers trigger a bounded root-cause revision and independent
verification; advisory debt is recorded without automatically blocking progression.
