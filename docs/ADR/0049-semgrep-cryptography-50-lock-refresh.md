# ADR 0049: Semgrep Cryptography 50 Lock Refresh

Date: 2026-08-04
Status: Accepted for bounded integration through Issue #360 review

## Context

The isolated Semgrep lock resolved `cryptography==49.0.0`, affected by
`GHSA-g6cj-pr64-35w5` / `CVE-2026-69247`. Version `50.0.0` contains the fix.
Issue #359 is the immutable reviewed source; it remains open until the convergence
change merges and merged-main verification passes.

## Decision

Refresh only the isolated lock to `cryptography==50.0.0` and hash-bind it.
Keep Semgrep `1.168.0`, PyJWT `2.13.0`, Click `8.3.3`, MCP `1.28.1`, direct
dependencies, overrides, rules, targets, and canaries unchanged. Require strict
audit, installed-tool identity, scan, canary, and zero-waiver evidence.

## Consequences

This changes security tooling only, not product/runtime behavior. Issue `#150`
and its `2026-08-13` expiry remain unchanged. Rollback may not restore vulnerable
`49.0.0`; no provider, deployment, release, public, or production authority is granted.
