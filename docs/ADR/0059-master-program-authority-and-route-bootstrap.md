# ADR 0059: Master program authority and route bootstrap

- Status: proposed in Issue #424; no implementation authority until reviewed
  merge and merged-main closeout
- Date: 2026-08-12
- Decision owner: Rohit Agrawal / StackClimb
- Accepted base: `afcf0325c3ec925b68b770eda0bb8c839bcce4dd`

## Context

PR #422 merged the exact Meera grounding/narration-authority prerequisite, but
the repository still contains multiple historical Cut 1 routes whose presenter,
provider, audio, renderer, and acceptance assumptions conflict. Directly
continuing Issue #368 would allow stale issue prose and route-specific tests to
compete with the OWNER's new master program.

The master program also requires phase specifications and active-route hashes
before implementation. Those controls cannot truthfully be represented as
implemented by the document that first proposes them.

## Decision

Adopt a two-step bootstrap:

1. Issue #424 preserves and hash-binds the complete master controller, records
   three independent-review surfaces, and reconciles status/stage/traceability.
   It is governance-only and creates no active implementation route. A narrow
   bootstrap exception adds exact Stage 8 recognition for only this branch,
   its fourteen paths, fixed base, and 8,500-line ceiling after committed RED
   evidence proved the previously unrecognized route could not run quality.
2. Only after Issue #424 exact-byte OWNER approval, independent exact-head
   review, merge, merged-main checks, and closeout may a separately bounded
   child specify and implement `Cut1AuthorityManifestV1`,
   `ActiveProgramRouteV1`, and stale-route enforcement.

The canonical `GovernancePreflightV1` now uses its closed repository schema and
the Stage 8 route invokes that validator with the exact fourteen-path context.
The binding record is
`docs/governance/narratwin-master-program-v1.json`. It hashes only the canonical
Markdown document, avoiding self-reference, and is an immutable
`MasterProgramProposalBindingV1`. It cannot be mutated from `PROPOSED` into
authority. A later separately governed reconciliation child must create a
distinct current `MasterProgramAuthorityDecisionV1` containing exact controller,
head, approval, review, merge, merged-main, status, issue-disposition, authority,
verification, and expiry evidence before route activation. Review files are
prompts and disposition surfaces; `PENDING` never means passed.

The exact Issue #424 branch is reference-only. It does not close the already
closed Stage 8 umbrella Issue #13; near-match Stage 8 branches retain the normal
canonical-stage closure rule.

Until the bootstrap closes:

- `activeProgramRoute` is null;
- implementation authority is none;
- Issues #366/#368/#369/#370/#371 remain open historical/planned inputs but
  cannot authorize implementation;
- provider calls, credentials, egress, spend, audio, video, auditions, renders,
  UI real-media completion, deployment, publication, release, and production
  claims remain prohibited;
- release posture remains No-Go.

## Alternatives rejected

- **Continue Issue #368 immediately:** conflicts with the master program's
  required authority reconciliation and phase specification.
- **Implement route enforcement in the pre-log PR:** circular; implementation
  would precede approved specification/authority.
- **Treat the user-supplied plan or GitHub issue alone as execution authority:**
  bypasses exact-byte review and merged repository authority.
- **Mark the self-authored review documents passed:** violates separation of
  duties.
- **Delete conflicting historical records:** destroys evidence; supersession
  must be explicit and traceable.

## Consequences

The immediate path becomes slower but deterministic: authority is reviewed
before automation. Existing Cut 1 runtime remains unchanged and disabled
provider defaults remain intact. The next child must enumerate every
superseded source and implement mutation-tested route enforcement from an
approved phase specification.

## Rollback

Before merge, close Issue #424's PR unmerged and remove only its clean scoped
branch/worktree. After merge, revert this ADR/controller package through a new
issue, branch, and PR. Do not remove historical evidence or reactivate an older
route implicitly.
