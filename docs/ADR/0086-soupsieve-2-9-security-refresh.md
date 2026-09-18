# ADR 0086: Preserve the isolated Soup Sieve 2.9 security candidate

- Status: Frozen component draft; standalone merge prohibited
- Date: 2026-09-18
- Issue: #549

## Context

The strict Python audit reports GHSA-j934-xhv5-fg8f and
GHSA-gjv8-xp57-g29c against transitive Soup Sieve 2.8.4. Both availability
findings are fixed in 2.9. Beautiful Soup 4.15.0 accepts the update without a
manifest change, and no direct user-controlled selector path was reproduced.

The one authorized `uv 0.11.18` resolver attempt reported success and changed
only the Soup Sieve record. Its controller nevertheless failed with exit 76:
the task cache peaked at 114404 KiB against the prospective 65536 KiB ceiling.
That resource failure remains historical truth. The attempt is spent; the
task-local cache and scratch were removed and their absence verified.

Recovery authority is limited to the exact already-produced `uv.lock` bytes:
734793 bytes, SHA-256
`c0ed386893396e65e5c58d4a0b87209120669b049d250566b8cfcaab24670b0a`,
Git blob `e646ac355a5697f29f5b75e892351bf80ab08f5e`. Comment `5732696613`
(SHA-256 `644de05a6ef35b7e7fb225ae087e5018697f2187d1b4196827e8cc6a73f8d2bc`)
authorizes preservation, not recreation or a second resolution.

## Decision

Preserve the exact failed-attempt output as `FROZEN_COMPONENT_DRAFT`. The sole
lock delta replaces Soup Sieve 2.8.4 with official PyPI 2.9 artifacts while
leaving raw `pyproject.toml`, Beautiful Soup 4.15.0, and every other lock record
unchanged. Exact package structure, source, artifact hashes, sizes, and
unrelated-record equality are executable contracts.

The candidate cannot merge standalone. Docker security corrections in Issue
#547 and a prospectively authorized atomic #549/#547 successor must bind these
immutable bytes, fresh exact-head review, hosted checks, and the sole final
push. Audit suppression, retry, repair, manual reconstruction, alternate
registry, or broader refresh is prohibited.

The amendment permits one non-mutating offline `uv lock --check` only when at
least 4194304 KiB is free. It was not run while capacity was below that floor;
this is pending validation, not a pass or a new failure.

## Consequences

The component records a precise candidate without erasing the controller and
resource failures. It changes no parser call site, product behavior, provider,
credential, egress, spend, media, deployment, release, production-readiness,
demo, or Cut 1 acceptance state.
