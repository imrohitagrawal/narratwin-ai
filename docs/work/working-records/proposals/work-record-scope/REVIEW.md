# Work-record scope review

Status: independent technical review rounds1/2 complete; hosted acceptance pending.

## Findings and disposition

| Finding | Reproduction / demonstrated impact | Classification | Owner / disposition |
|---|---|---|---|
| Omitted index snapshot | Staged backend addition hidden by working deletion, and staged overrun trimmed in worktree, both returned local success before fix | REQUIRED_CONTRACT W3/W4/W5 | root; RED regressions then index paths/modes/blob/manifest/charge proof; independently corrected |
| Missing hosted packet | Actual dirty candidate with only GITHUB_ACTIONS=true returned local success before fix | REQUIRED_CONTRACT W5 | root; host marker requires event; regression RED before/GREEN after; independent read-only rejection confirmed |
| PR applicability against newer main | Legacy-only PR reclassified after later main work-record change | REQUIRED_CONTRACT compatibility W5/W6 | root; eventbase regression RED before/GREEN after; corrected without scope expansion |
| Cached old preflight during preparation | Staged16path preflight and new ADR conflicted with18path working amendment | Expected fail-closed refusal, no code defect | root; stage complete final snapshot before local quality/commit |
| Hosted fixture marker warning | Reviewer saw earlier file while writer updated fixture | DUPLICATE / stale observation | independently rechecked current fixture clears GITHUB_ACTIONS; no additional patch |

Independent implementation/security and operations/economics reviewers receive
exact source, contract and disproof cases, with no shared writes. Round2 source
review found no remaining substantiated code blocker; frozen files, narrow
documentation envelope and preserved semantic checks remain unchanged.
Counters: two review rounds, initial approach plus one bounded RCA correction;
never reset. No third speculative expansion or immutable freeze.

## Verification and limits

Original valid-route RED:35 Git-backed cases failed before helper existed;
old frozen checker independently rejects the same work-record path. Focused
route/wrapper/runner suite passed61cases before review and66after boundary
regressions; final rerun and full backend suite follow corrected source.
Actual pre-RCA make quality passed77 record/archive/navigation tests and phase
checks; post-RCA final staged snapshot must pass again before commit.
Fresh uv0.11.18 sync --frozen on Python3.13 passed. Exact backend lint command
passed ruff and mypy224source files. Full unit/API command is required and its
final result is recorded in issue/PR evidence. Local worktree checks are not
hosted acceptance. Complete required hosted contexts, direct-head/merge checkout
and exact commands remain mandatory; no release or provider/media proof follows.

## Pre-code provenance

First preflight-only commit d9548e5 preceded implementation. Retained selected
visible tool records show invariant/source contract write at2026-10-13T10:08:39.666Z
before initial implementation call at2026-10-13T10:13:21.143Z. This records actual
local pre-code order, not a claim the later full matrix file existed in C1.
RCA delta was added before the bounded correction. No hidden reasoning, system
or developer content was captured in the selected source evidence.

## Rebase verification checkpoint — 2026-10-14

Original rounds and corrected findings above remain history. The owner removed
the work-package dependency and its fixed reserve/procedural review prerequisites.
The resumed candidate uses mergedmain5303ade4; the kernel is unchanged. Conflicts
were confined to append-only ADR/quality sections and derived STATUS identity.
New exact-head independent review and local/hosted verification are pending;
previous CI failures repaired by PR562 are historical, not current blockers.

## Current pending-mode correction disposition — 2026-10-14

The initial resumed candidate5d7a856 preserved the original kernel. Independent
review then reproduced one additional REQUIRED_CONTRACT W4 finding: executable
and symlink committed preflights can be masked by regular index/current copies
during preflight-only local preparation. Primary independently reproduced both;
hosted pending candidates still rejected. No hosted false acceptance demonstrated.

Two new Git regressions failed RED with the original helper returning success.
The smallest correction unconditionally requires the committed preflight's100644
mode before its blob is consumed. Existing repository schema validation proves
committed JSON bytes, and current/index/file safety checks remain in place. Valid
uncommitted document preparation stays permitted. Root owns the fix; independent
corrected-boundary review and complete new-head integration/hosted checks remain
required. Earlier exact-head PASS receipts are historical, not current acceptance.
The helper and its test now differ narrowly from c97ebd95; the wrapper and its
test remain byte-identical. No envelope, threshold, runtime or authority change.
