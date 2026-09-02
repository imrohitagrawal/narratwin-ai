# Resource Lifecycle

## Purpose

Every engineering increment must leave the machine no dirtier than its declared
retention policy requires. Resource cleanup is part of delivery, not optional
housekeeping and not a later prompt reminder.

This contract applies to humans, agents, local automation, and future project
templates. It does not authorize deletion by itself. Ownership, lifecycle, and
the current operation authority must all permit the exact action.

## Creation-Time Inventory

Assign an issue, branch, worktree, and session identity before creating a
material resource. Record each resource when it is created or first reused:

| Field | Required meaning |
|---|---|
| Resource | Exact path, Git ref, Docker name/ID, cache ID, or other stable identity |
| Ownership proof | Why this issue/session exclusively owns it, or why it is shared |
| Retention class | One class from the closed vocabulary below |
| Cleanup contract | Non-executable structured data declaring disposition, kind, literal locator, and trigger |
| Verification evidence | Where absence, retention reason, and reclaimed space will be recorded |

Inventory at least:

- local and remote branches and dedicated worktrees;
- dependency environments, downloads, package caches, and build outputs;
- temporary files, reports, screenshots, replay directories, and review evidence;
- Docker images, builders, cache records, containers, volumes, and networks;
- generated artifacts or private evidence that must survive for review.

## Cleanup Contract

The pull-request table records data, never an executable command. Use one
compact JSON object with exactly four string fields:

```json
{"disposition":"delete","kind":"git-worktree","locator":"/private/tmp/issue-391","trigger":"merged-main-green"}
```

- `disposition` is `delete` or `retain` and must agree with the retention
  class.
- `kind` is one stable operation category: `git-branch`,
  `git-remote-branch`, `git-worktree`, `filesystem-path`,
  `temporary-file`, `python-venv`, `node-modules`, `docker-image`,
  `docker-container`, `docker-volume`, `docker-network`,
  `docker-builder`, `buildkit-cache-record`, or `shared-resource`.
- `locator` is one literal exact identity. Path kinds require an absolute
  path. Variables, globs, root paths, parent traversal, options, multiple
  targets, and shell syntax are invalid.
- `trigger` is a compact event slug selected for the PR, such as
  `merged-main-green`, `session-end`, or `owner-verified`.

Stable resource kinds and safety semantics remain code-controlled; project
needs such as exact identities and lifecycle events remain data-configurable.
The contract never grants execution authority. At cleanup time the operator
must re-resolve ownership and activity read-only, then select the repository-
approved operation for exactly that kind and locator.

## Retention Classes

| Class | Meaning |
|---|---|
| `always-clean` | Remove after the command/session that created it, even when work fails, unless it becomes required diagnostic evidence. |
| `success-clean` | Remove after successful merge and merged-main acceptance. |
| `failure-retain` | Retain the smallest diagnostic bundle on failure; record owner and revisit trigger. |
| `evidence-until-merged-main` | Preserve exact evidence until review, merge, and merged-main checks pass, then remove if no longer required. |
| `persistent` | Deliberately durable product or operator state; never delete as routine engineering cleanup. |
| `shared-retain` | Shared, active, ambiguous, unrelated, or cross-project resource; retain until separately scoped authority proves safe deletion. |

## Finalization Gate

Before starting another increment after merge or an authorized stop:

1. Re-inventory live resources; do not trust a stale manifest or prompt.
2. Compare live identities with the creation-time inventory.
3. Prove each deletion target is exact, inactive, exclusively owned, and no
   longer required for evidence or recovery.
4. Delete only the enumerated eligible resources.
5. Prove each target is absent and each protected resource remains present.
6. Measure before/after disk usage when cleanup can reclaim material space.
7. Record deleted resources, retained resources and reasons, recoverability or
   reproducibility, failures, and remaining owner actions in the PR and issue
   closeout evidence.

Finalization is incomplete when an owned disposable resource is silently left
behind. It is also incomplete when a shared or ambiguous resource is deleted to
make the report look clean.

## Docker Rules

- Prefer stable reusable image tags for repeated local checks. If an exact
  per-run tag is required, register it at creation and delete it at finalization.
- Label session-owned resources when the build path supports labels.
- Treat BuildKit cache as shared unless exact cache IDs and impact are known.
- Preserve images referenced by containers and all active or unrelated
  containers, volumes, and networks.
- Use exact image tags/IDs and exact cache selectors. Never use host-wide
  `docker system prune`, broad image/volume/network prune, builder/cache prune,
  or a force flag to bypass ownership or active-reference protection.
- Cache deletion is reproducible but may slow the next build; record that
  tradeoff and the measured reclaim.

## Filesystem And Git Rules

- Never target a home directory, workspace root, unresolved variable, glob, or
  guessed filename for recursive deletion.
- Never use broad `git clean`, worktree prune, history rewriting, reset, or
  branch switching as cleanup.
- Reverify dirty and preserved work before and after cleanup.
- Remove a worktree only after proving it is the exact completed worktree and
  contains no uncommitted user work.
- Dependency environments created inside a dedicated worktree inherit that
  worktree lifecycle; shared environments are retained and reported.

## Stop Conditions

Stop and request exact owner direction when ownership is ambiguous, a resource
is active or shared, deletion could destroy required evidence or credentials,
the target differs from the inventory, the operation needs force, or the only
available action is broad/destructive.

## Enforcement Boundary

This transition's first PR makes the pull-request guardrail require a complete
`Resource lifecycle and cleanup` table for every non-trivial PR and publishes
the reusable finalizer prompt. A separately reviewed protected-source PR will
make the root `AGENTS.md` and reusable future-project playbook carry the same
creation-time inventory and finalization contract. A final transition PR will
then remove the superseded protected-source hash allowance.

This slice does not implement a host-wide janitor. Later Issue #391 work may add
schema-backed start, audit, dry-run, and finalize commands only if they preserve
these fail-closed boundaries.
