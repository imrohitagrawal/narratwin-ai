# ADR 0076: Session-scoped resource lifecycle enforcement

## Status

Accepted as a three-PR transition for the Issue #391 immediate enforcement
slice. The protected agent and playbook source update remains pending until the
first PR preauthorizes their exact replacement bytes.

## Context

Repeated exact-test and review sessions created short-lived Docker tags and
BuildKit cache without a creation-time ownership record. Cleanup prose existed,
but it was applied only when remembered at closeout. The machine reached 98%
data-volume utilization. An exact owner-authorized cleanup recovered about
30.25 GiB while preserving active and ambiguous cross-project resources.

## Decision

Resource lifecycle is a mandatory delivery gate:

- every autonomous engineering prompt carries a bounded finalization phase;
- each session inventories material resources at creation or reuse time;
- every non-trivial PR declares exact resource ownership, retention class,
  cleanup trigger/action, and verification destination;
- exclusively owned disposable resources are removed after their evidence
  obligation ends and before the next increment;
- active, persistent, shared, ambiguous, unrelated, and credential-bearing
  resources fail closed to retention;
- broad prune, force deletion, guessing, and workspace-wide cleanup are
  prohibited;
- reusable project guidance carries the contract into future repositories.

The first transition PR installs repository policy, the executable PR-body
guardrail, the reusable finalizer, and an exact pending-hash allowance. The
second PR consumes that allowance to update the protected `AGENTS.md` and
future-project playbook bytes. The third removes the superseded allowance. Full
manifest-backed start/audit/dry-run/finalize automation remains a later bounded
Issue #391 slice.

## Alternatives considered

### Keep cleanup in chat prompts only

Rejected because prompt context is temporary and the accumulated resources
demonstrated that reminder-only control does not converge reliably.

### Run broad scheduled pruning

Rejected because one Docker daemon and filesystem may contain active,
persistent, unrelated, or cross-project resources.

### Delete every resource immediately

Rejected because exact-head review, failure diagnosis, and merged-main
acceptance require some evidence to survive beyond individual commands.

## Consequences

PR authors must account for local resources and closeout takes measurable work.
Build caches may be retained for speed or removed for space, but the choice and
ownership are explicit. CI can reject missing lifecycle evidence; human
operators still own live destructive authorization and post-merge verification.

No product runtime, provider, media, deployment, release, or production
behavior changes through this decision.
