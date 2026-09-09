# ADR 0083: Isolate and bound the Draft 2020-12 schema oracle

- Status: Accepted
- Date: 2026-09-09
- Issue: #525

## Context

The adversarial-convergence suite independently checks its application rules
against `jsonschema` Draft 2020-12 behavior. The accepted helper launched
ambient `/usr/bin/python3`, inherited its user-site package graph, and imposed
a fixed five-second timeout. Repeated cold runs exceeded that timeout even
though warm validation passed, so host scheduling and ambient package state
could falsely fail the complete repository gate.

The active locked development environment did not directly contain
`jsonschema`. It appeared in `uv.lock` only under an optional provider
dependency, so changing to an isolated project interpreter without also
closing that dependency would make the oracle unavailable.

## Decision

Run exactly one oracle subprocess with the active absolute `sys.executable`
under Python `-I -P`. Pass only `PATH` and `LC_ALL` to the child. The helper has
no retry, prewarm, fallback, ambient interpreter, or inherited credential
environment.

Use one typed timeout policy named
`NARRATWIN_SCHEMA_ORACLE_TIMEOUT_SECONDS`. Its default is 20 whole seconds and
its inclusive bounds are 1 through 60. Environment input accepts canonical
ASCII decimal only. Invalid policy blocks before process creation. Timeout,
invalid interpreter, and child-process failure diagnostics do not echo schema,
instance, stdout, stderr, or environment bytes.

Pin `jsonschema==4.25.1` in the development group only. Its already locked
official PyPI artifacts and dependencies remain unchanged. It is not added to
application dependencies or the optional provider extra.

## Consequences

The independent standards check is reproducible inside the same locked project
toolchain as the suite while retaining process isolation and a finite ceiling.
Focused tests bind the exact configuration path, dependency placement, package
artifacts, one-attempt failure behavior, and valid/invalid schema results.

This decision changes test and quality infrastructure only. It adds no product
runtime, provider, credential, egress, spend, media, deployment, release,
production-readiness, or Cut 1 authority.
