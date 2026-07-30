# Agent Context Architecture — Shadow Slice 1

Issue `#319` adds a machine-verifiable context foundation without replacing
root `AGENTS.md` or any of its 13 mandatory sources. It is governance tooling,
not product runtime, release authority, or a default agent bootstrap.

## Commands

Validate the working tree:

```bash
python3 -m scripts.agent_context.cli validate --commit WORKTREE
```

Reproduce one routed packet from an exact commit:

```bash
python3 -m scripts.agent_context.cli route \
  --commit HEAD \
  --fixture-id RFV1-06-COLD-PR-REVIEW
```

Run the focused gate:

```bash
make agent-context-quality
```

Unknown commands, fields, tasks, modules, dependencies, conflicts, hashes,
heads, paths, budgets, or fixture provenance fail closed.

## Authority And Rule Model

The active candidate rule families are `CONST`, `STATE`, `STAGE`, `SCOPE`,
`SEC`, `AI`, `EVID`, `DELEG`, `REVIEW`, and `MERGE`. Their one active shadow
definition is the `rules` registry in
`context-policy-manifest-v1.json`. Fixture meanings are independently authored
expected values, not a second authority source. Existing repository prose keeps
precedence throughout Slice 1.

Modules bind exact full resources or exact Markdown heading sections. Each
module stores the whole-source SHA-256 and selected-content SHA-256. A packet
contains selected source text, the matching active rule definitions, the exact
repository commit, routing reasons, dependency closure, and canonical digests.
The router derives dependency closure from the manifest, proves that every
selected rule is owned by an included module, and rejects any drift in the
independently frozen fixture content hash. Summaries are never substituted for
source authority.

Manifest, contract, current-state, history, fixture, status, issue-scope, and
selected module bytes are all read from the requested Git commit. `WORKTREE` is
an explicit validation mode; it is never silently mixed with commit-pinned
input. Every V1 object is checked against the checked-in strict contract before
its semantic invariants are evaluated.

## Non-Widening Delegation

Authority is evaluated separately for read paths, write paths, actions,
external actions, claims, and reserved decisions:

```text
effective allow = repository ∩ issue/preflight ∩ parent ∩ child request
effective deny  = repository ∪ issue/preflight ∪ parent ∪ child deny
```

Every deny wins. Missing GitHub, provider, secret, deployment, destructive, or
external authority is a denial. A child may narrow an allow or add a deny; it
cannot add an allow or remove an inherited deny. Exact paths reject traversal,
absolute paths, globs, prose, symlinks, and normalized parallel collisions.

`AgentTaskCapsuleV1` binds the branch, distinct base/head, objective, deliverable,
authority digest, selected rules/module hashes, tests, assumptions, budgets,
stop conditions, and expected receipt. The CLI emits one deterministic capsule
with every routed fixture. The capsule is evidence of delegated bounds, not
proof that the child obeyed them.

## Handoff Receipts

`HandoffReceiptV1` records the accepted authority digest, actual branch/head,
manifest/rules/modules, sources, inspected and changed files, commands and exit
results, findings, proved/disproved/untested claims, assumptions, blockers,
risks, prevented actions, budgets, collision check, and follow-up. Validation
rejects missing command evidence, authority/head mismatches, read-only changes,
out-of-scope writes, and any self-certification.

A receipt cannot approve a PR, declare merge eligibility, close an issue,
authorize release, or claim production readiness. Parent verification and an
eligible independent human review remain required.

## Current State And History

`current-state-v1.json` is a structured shadow view of selected current facts.
`history-v1.jsonl` is append-only, explanatory, and explicitly non-authorizing.
The baseline entry preserves the detected contradiction between the old
repository Issue `#317` completion row and live open post-merge acceptance.
`docs/STATUS.md` now records the open/incomplete fact without selecting a
correction. Historical evidence is not rewritten.

## Frozen Cohorts And Budgets

The independently authored fixture covers nine exact cohorts: documentation
discovery, backend TDD, frontend/browser behavior, governance changes, security
review, cold PR review, merge/closeout, a read-only child, and a disjoint-path
write child. The router performs exact deterministic matching only; it does not
claim arbitrary task classification.

Ceilings are 250 lines/2,500 tokens for bootstrap, 180/2,000 for a capsule,
600/6,000 for discovery, 1,200/12,000 for proof review, 1,800/18,000 for
implementation, and 2,000/24,000 for high-risk governance/security. Token
budgeting uses documented `ceil(UTF-8 bytes / 4)` estimates; the measured
mandatory baseline uses `cl100k_base` for comparison.

At corrected GREEN, the universal bootstrap measures 43 lines and 928 estimated
tokens. Routed packets measure 158–369 lines and 2,079–3,913 estimated tokens;
capsules measure 114–167 pretty-printed lines and 724–1,162 estimated tokens.
All are validated against their executable ceilings.
Smaller size is not acceptance evidence; seeded-defect recall, critical-rule
completeness, cold reconstruction, and false-positive behavior remain the
meaningful comparison.

## Limits

Slice 1 does not retire mandatory reading, migrate every rule, archive all
history, authenticate an agent, sign a receipt, intercept platform tool calls,
activate routing by default, cover arbitrary tasks, fix Issue `#317`, modify
Issue `#280` or PR `#299`, add a provider/dependency/service/database, or claim
deployment, release, public availability, or production readiness.
