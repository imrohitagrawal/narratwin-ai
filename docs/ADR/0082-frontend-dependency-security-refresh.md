# ADR 0082: Refresh the affected frontend dependency graph

- Status: Accepted
- Date: 2026-09-09
- Issue: #524

## Context

The official npm advisory feed now rejects the accepted lock for two critical
Next.js findings, one high sharp finding, one high js-yaml finding, and a
moderate Vitest/@vitest-mocker finding. The repository blocks critical and high
dependency findings. Issue #523 fixes a separate Python audit failure, so the
two security branches must converge before either can prove the complete gate.

## Decision

Use the official npm registry and make the smallest coherent graph refresh:

- pin Next.js at 16.3.4;
- raise the sharp override and install-script authorization to 0.35.4;
- lock transitive js-yaml at 4.3.2 without making it direct or overriding it;
- raise Vitest and its coupled `@vitest` family to 4.1.11; and
- preserve eslint-config-next 16.2.9 and every unrelated manifest and lock
  record.

Exact registry integrity values and the complete permitted lock-record delta
are executable test inputs. The resolver may add the nested Emscripten runtime
required by sharp 0.35.4, but cannot refresh unrelated Vite/Rolldown or CSS
tooling merely because their version ranges admit newer releases.

## Consequences

Frontend install, lint, type checking, unit tests, production build, browser
checks, strict audit, and the complete repository gate must pass. Issue #524
retains its RED/GREEN history and is normally merged into the amended Issue
#523 branch for one atomic, independently reviewed security PR. Neither audit
is waived and neither branch alone is described as full-gate green.

Task-local npm cache, `node_modules`, build output, browser output, branch, and
worktree are removed only after accepted merged-main verification and exact
ownership/survivor checks. Shared caches and historical resources are not part
of that cleanup.

This decision adds no product behavior, provider integration, credential use,
egress, spend, media, deployment, release, or production authority.
