# AI Engineering Session Finalizer

Append this bounded phase to every autonomous engineering prompt. Replace the
bracketed values before use; it does not broaden authority granted elsewhere.

```text
FINAL RESOURCE LIFECYCLE PHASE

Session identity: [issue / branch / worktree / run identity]
Applicable contract: [repository resource-lifecycle document]

Track every material resource when created or reused, including branches,
worktrees, dependency environments, temporary and evidence paths, downloads,
build outputs, Docker images/builders/cache records/containers/volumes/networks,
and generated or private evidence.

For each resource record:
- exact identity;
- ownership proof;
- retention class;
- cleanup trigger and exact bounded action;
- verification and closeout-evidence destination.

After the required merge and merged-main acceptance, or at an authorized stop,
and before starting the next increment:
1. Re-inventory live state.
2. Preserve evidence still required for review, recovery, or audit.
3. Retain active, persistent, shared, ambiguous, unrelated, and
   credential-bearing resources with an explicit reason.
4. Delete only exact, inactive, exclusively session-owned disposable resources
   whose cleanup is already authorized.
5. Prove target absence and protected-resource survival.
6. Measure before/after disk usage when material space is involved.
7. Report deleted resources, retained resources and reasons, reproducibility or
   recoverability, reclaimed space, cleanup failures, and remaining owner-only
   actions in the PR and issue closeout evidence.

Never use broad Docker/system/image/cache/builder/volume/network prune, broad
Git clean/worktree prune, force deletion, unresolved variables or globs,
workspace/home-root recursive cleanup, or filename guessing. Stop and request
exact authorization when ownership, activity, evidence retention, or scope is
uncertain.
```

The finalizer is an operator checklist, not deletion authority and not a
substitute for repository-owned validation. Projects should add manifest-backed
automation and tests when their resource volume justifies it.
