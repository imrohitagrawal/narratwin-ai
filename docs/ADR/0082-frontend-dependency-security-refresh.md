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

Owner/orchestrator amendment `5600552079` binds the complete fifty-record
canonical digest, duplicate-member rejection, and normal merge into a separately
amended Issue #523 route. Cleanup amendment `5601014173` reclassifies the earlier
short inventory as preliminary and adds the byte-identical StackClimb
`TaskResourceLedgerV1` schema plus a frozen, sanitized sixteen-resource package
ledger with executable schema and semantic mutation coverage. Live-census
authority `5601780266` replaces that preliminary count with thirty-four exact
resources and sixty-eight lifecycle events, including every full-gate output
observed in the worktree. Canonical whole-ledger SHA-256 binding prevents
fingerprint, byte, evidence, retention, and sensitivity forgery while keeping
private locators out of Git. Frontend install, lint, type
checking, unit tests, production build, browser
checks, strict audit, and the complete repository gate must pass. Issue #524
retains its RED/GREEN history and is normally merged into the amended Issue
#523 branch for one atomic, independently reviewed security PR. Neither audit
is waived and neither branch alone is described as full-gate green.

Full-gate amendment `5601451115` keeps the historical nanoid contract
discriminating while normalizing the immutable Issue #524 reference and removes
one accidental key-shaped substring from the opaque ledger ID. It does not
weaken the secret scanner or widen the dependency delta.

Provenance authority `5601842704` adds the repository skill lock for the exact
StackClimb 1.0.0 commit and custom `LicenseRef-stackclimb-source-v1`. The
work-package protocol and read-only machine inventory are governance guidance,
not runtime code or cleanup authority; redistribution must retain the complete
notice and visible attribution recorded in `docs/THIRD_PARTY_NOTICES.md`.

The ledger grants no cleanup authority: every resource remains classified with
a pending retention trigger and active evidence obligation. Task-local caches,
dependencies, build output, branch, and worktree can be proposed for removal
only after accepted merged-main verification and fresh exact ownership,
activity, sensitivity, reference, and survivor checks. Unrelated dirty state,
shared caches, historical resources, Docker objects, and private evidence are
explicitly excluded.

This decision adds no product behavior, provider integration, credential use,
egress, spend, media, deployment, release, or production authority.
