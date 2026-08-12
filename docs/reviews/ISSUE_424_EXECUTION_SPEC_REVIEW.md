# Issue 424 Execution-Specification Review

## Review identity

- Controller digest: `a3e1d0180e4e28b99ca3e01ae03aa88d0273e69a0fb14ed090be32734d7f68d4`
- Review state: `PENDING_INDEPENDENT_REVIEW`
- Required reviewer: eligible fresh-context non-author
- Author self-review: prohibited as approval evidence

## Question

Can a later implementer derive bounded phase specifications and child tasks
without inventing contracts, skipping predecessor evidence, or activating from
stale prose?

## Mandatory checks

| ID | Check | Pass condition | Fail condition | Evidence |
|---|---|---|---|---|
| EX-01 | Authority layers | Controller, phase specification, child card, active route, branch/PR, and merged-main predecessor are distinct and ordered | Any layer substitutes for another | Sections 1, 3, 5, 20, 42 |
| EX-02 | Route identity | Active route requires exact issue/PR/base/predecessor/authority/specification/path/budget/reviewer bindings | Any identity or hash may drift silently | Section 3 |
| EX-03 | Transition completeness | Dependent work cannot start before all five closeout transitions | A child starts after merge alone | Sections 3 and 20 |
| EX-04 | Specification completeness | Phase specs require schemas, validation, transitions, recovery, security, migration, rollback, machine/human acceptance, and prohibited substitutes | A meaningful execution dimension is absent | Section 5 |
| EX-05 | Role authority | Actors and self-approval prohibitions are explicit | Implementer can approve own work/spend/media | Section 6 |
| EX-06 | Serialized route | All forty Cut 1 steps are dependency ordered | Egress/render/UI/acceptance can leapfrog a predecessor | Section 20 |
| EX-07 | Exceptional state recovery | BILLABLE_UNKNOWN/rejection/failure/cancellation/supersession cannot become success without new authority | Retry or fallback bypasses predecessor evidence | Sections 27 and 32 |
| EX-08 | Completion split | Cut 1 and full plug-and-play claims are separately enumerated | Cut 1 implies hosted/production/release | Sections 1 and 41 |
| EX-09 | Closeout | Resource, Git, provider, issue, evidence, and documentation closeout are command-bound | Prose-only clean claim is allowed | Sections 36–40 |
| EX-10 | Bootstrap | This PR remains proposed authority with no active route | Review artifacts or hash alone activate implementation | Section 42 and binding JSON |

## Required adversarial mutations

- Remove one numbered section.
- Replace an authority/specification hash after route activation.
- Start a child at `MERGED` before merged-main checks and issue disposition.
- Treat provider `SUCCEEDED` or one render as final acceptance.
- Retry after `BILLABLE_UNKNOWN`.
- Substitute a skill invocation for evidence.
- Claim cleanup without before/after inventory.
- Claim production readiness from Cut 1.

Each mutation must be rejected by the contract or recorded as a blocker for the
later enforcement specification.

## Reviewer disposition

- Reviewer: `PENDING`
- Exact commit: `PENDING`
- Decision: `PENDING`
- Blocking findings: `PENDING`
- Residual risks accepted by: `PENDING`

This file is a review surface, not proof that the review occurred.
