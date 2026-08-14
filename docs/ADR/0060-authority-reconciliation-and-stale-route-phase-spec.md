# ADR 0060: Decompose authority reconciliation before protocol implementation

- Status: proposed by Issue #427; non-activating
- Date: 2026-08-13
- Decision owner: repository OWNER with eligible independent review
- Exact base: `f2a32b8c022c015dfa4e87c700fbfe1ed0d85183`

## Context

ADR 0059 preserves an immutable master-program proposal and requires a separate
current decision before any route can activate. The first Issue #427 attempt
expanded into field schemas, evidence capture, signing trust, projections, CAS,
audit transport, reconciliation, checkpointing, and an integrated kernel. Ten
review rounds showed that this was multiple independently testable subsystems,
not one reviewable specification. Its two-correction stop rule fired.

OWNER approval in Issue #427 comment `5273244742` accepts the bounded reset
requested in comment `5273122120`. Markdown reset approval `5289686674` accepts
request `5287631143`; CI route-reset provenance `5292268215` binds current main.
The proposal remains exactly `17,853` UTF-8 bytes and `326` LF lines at SHA-256
`794c2e90034a8012363a6a859dd3bac826280452e787b8a7afe5a49164849b29`.

## Decision

Issue #427 establishes only a cross-child architecture kernel, 23 invariants,
semantic state boundaries, one owner for each detailed protocol, and the strict
dependency order `A → B → C → D → E → F`:

1. A owns core schemas and state matrices.
2. B owns evidence and trust.
3. C owns projection, CAS and bootstrap.
4. D owns audit and closeout coordination.
5. E owns historical reconciliation.
6. F owns integrated offline composition and its oracle.

Each child requires a later OWNER-approved issue, branch, PR, predecessor,
scope, budget, invariant matrix, RED proof, review, stop rule and closeout. No
child is activated by this ADR or Issue #427. Detailed fields, wire formats,
algorithms, runtime enforcement, external acquisition and operating targets stay
with their owning children.

The proposal is immutable `RESET_PROPOSAL_UNAPPROVED`; the binding state remains
non-activating and `activation` is `NONE`. Issue prose, comments, files, tests,
CI and review documents are evidence inputs, not independent authority sources.

## Alternatives rejected

- Continue patching the monolith: violates the fired stop rule and reviewability.
- Implement the kernel in Issue #427: exceeds the documentation-only reset.
- Parallelize A–F without frozen interfaces: risks circular ownership and drift.
- Treat approval of this architecture as approval of a child: collapses
  separation of duties and permits self-expanding authority.

## Consequences

The reset makes the next work smaller and serializable while adding governance
latency. Release posture stays No-Go. Runtime/product behavior, providers,
credentials, egress, spend, media, infrastructure, deployment, publication,
release, SLA, commercial readiness and production remain unchanged and
unauthorized.

## Rollback

Before merge, close the PR unmerged and remove only its verified task-owned
branch/worktree. After merge, revert through a new issue, branch and PR. Preserve
the proposal, abandoned branch and review history; never silently reactivate a
historical route. A failed or reverted reset leaves no active authority route.
