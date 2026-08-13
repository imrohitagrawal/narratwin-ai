# ADR 0061: Semgrep 1.172 MCP-only override renewal

## Status

Accepted for Issue #150 implementation review on 2026-08-14. This decision is
security-tooling-only and does not authorize release or production use.

## Context

The Semgrep 1.168 tool environment used two compatibility overrides: fixed
Click 8.3.3 and fixed MCP 1.28.1. That reviewed exception expired on
2026-08-13. Official Semgrep 1.172.0 metadata now declares fixed
`click~=8.4.2`, so the Click override is obsolete. The same metadata still pins
`mcp==1.23.3`; the repository requires fixed MCP 1.28.1.

## Decision

- Pin the isolated tool to Semgrep 1.172.0.
- Resolve Click 8.4.2 from upstream metadata with no Click override.
- Retain exactly one tool-only override, `mcp==1.28.1`.
- Expire the MCP-only exception on 2026-08-28 and revisit earlier on any tool,
  lock, rule, target, canary, invocation, reviewed-input, or advisory change.
- Keep root and tool audits separate and strict, retain zero advisory ignores,
  and preserve the exact local scan and canary invocation.

## Consequences

The generated lock keeps the same 68 package names. Only Click, Semgrep, the
tool root metadata, and the override manifest differ from the Issue #150 base.
Semgrep and MCP remain absent from the application/runtime lock and backend
image. MCP server functionality is not started, exposed, or used.

The renewal remains temporary. If upstream does not support fixed MCP before
2026-08-28, a security/repository owner must again choose a reviewed short
renewal, scanner replacement, or removal. A silent extension or audit waiver is
prohibited.

