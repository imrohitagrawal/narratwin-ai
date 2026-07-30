# ADR 0046: Shadow Agent-Context Manifest, Capsules, Router, And Receipts

- Status: Accepted for Issue `#319` shadow evidence only
- Date: 2026-07-30
- Decision owner: repository authority plus eligible human PR review

## Context

The mutation bootstrap is 14 files, 10,049 lines, 74,540 words, 620,708 bytes,
and 149,337 `cl100k_base` tokens. It mixes stable rules, mutable state, history,
examples, and duplicated explanation. Existing quality passes while the old
StatusStateV1 row contradicts live Issue `#317`. GovernancePreflightV1 strictly
checks paths but cannot execute action/claim prose stored in its path list or
prove non-widening child authority and handoff evidence.

## Decision

Add a standard-library shadow layer with:

1. `ContextPolicyManifestV1` modules and stable rule IDs bound to exact source
   and selected-content hashes;
2. exact-match deterministic routing for nine independently frozen cohorts;
3. `AgentTaskCapsuleV1` with typed path/action/external/claim/decision planes;
4. `HandoffReceiptV1` bound to capsule authority, manifest, branch/head,
   commands, files, findings, claims, budgets, and prevented actions;
5. separate structured current state and non-authorizing append-only history;
6. fail-closed graph, hash, conflict, staleness, path, collision, budget,
   summary-substitution, injection, and self-certification checks;
7. strict standard-library validation of every emitted V1 contract, with
   manifest-derived dependency closure and rule ownership; and
8. commit-pinned reads for every routing input, plus an explicit and separate
   `WORKTREE` validation mode.

Child allows are the intersection of repository, issue, parent, and child
allows. Denies are their union. This does not change existing authority
precedence; it makes the candidate computation explicit and testable.

## Consequences

Fresh read-only agents can receive reproducible packets without parent
reasoning. Write-capable children can receive exact disjoint paths and return a
verifiable receipt. Reviewers can inspect source text and rule definitions at
the exact commit. CI can execute the shadow validator, while root mandatory
reading remains unchanged and available as the comparison baseline.

Exact fixture matching intentionally fails unknown and ambiguous tasks. The
current source hashes and independently frozen fixture-content hash require an
explicit, reviewed refresh when binding sources or expected values change.
Receipts are not signed or self-authenticating, and tool enforcement remains
outside this slice.

## Alternatives Rejected

- Replace `AGENTS.md` now: rejected without parity and migration evidence.
- Reuse GovernancePreflightV1 for every restriction: rejected because its
  scope fields are path-only and its final artifact can differ from the first.
- Route with an LLM/model judge: rejected as non-deterministic and circular.
- Add a schema/provider/database/service dependency: rejected as unnecessary.
- Compress authority into generated summaries: rejected as lossy and unsafe.

## Rollback And Migration

Rollback is removal of the Issue `#319` shadow target and artifacts through a
separately authorized PR; existing bootstrap behavior is unaffected. A later
issue must decide activation, wider coverage, archival, signatures, expiry,
platform enforcement, or mandatory-reading retirement using benchmark and
independent-review evidence.
