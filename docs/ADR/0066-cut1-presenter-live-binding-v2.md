# ADR 0066: Version Cut 1 presenter live binding

- Status: Proposed by Issue #456; review and merge pending
- Date: 2026-08-28
- Decision owners: governance, AI quality, security/privacy
- Scope: Lane B integrity routing only

## Context

PR #455 accepted the Issue #452 Cut 1 presenter contract and preserved its
reviewed RED inputs in
`docs/governance/cut1-presenter-contract-red-freeze-v1.json`. That v1 artifact
is valid historical evidence, but its live validator rehashed all frozen paths
against the current worktree. The map includes mutable shared ledgers, prose,
routes, tests, and the validator alongside five immutable contract-owned JSON
and schema inputs.

An isolated append to `docs/STATUS.md` therefore produced
`CUT1.BUNDLE.PROTOCOL`, even though no presenter requirement, threshold, study,
provider candidate, or acceptance result changed. This blocked truthful later
governance work, including Issue #16.

## Decision

Preserve the v1 manifest byte-for-byte at SHA-256
`b9921a468f1383a3525879144992fd9ccb30c3dbf62481dcfc9f6e2d3b8afceb`.
Its v2 successor pins PR #455 accepted head
`89164f25998b0088ae2b6c645dbe935efe50cf7e`, tree
`6d42093643a133f239265432a2cca4f539eb392b`, merge
`c3ac83bf05336a539dbdd6af1de9905e6b954289`, and the v1 SHA.

Current-worktree integrity is limited to these immutable Issue #452 inputs:

1. all-presenter acceptance matrix;
2. blinded human-evaluation protocol;
3. provider bake-off contract;
4. human-realism evaluation schema;
5. presenter-provider acceptance schema.

The v2 manifest is itself byte-pinned in the validator. A coordinated input and
manifest digest edit therefore fails. Manifest changes—including malformed,
duplicate, unknown, missing, non-object, or non-finite forms—cannot equal the
accepted byte identity and fail closed before they can redefine the live set.
The validator permits only bounded regular files, rejects symlinked path
components, hashes bytes read from the accepted fixed paths, and reuses those
same captured bytes for semantic contract validation.

The Phase 1 runner order becomes publication boundary, Cut 1 live binding, then
preserved contracts. Any nonzero status short-circuits later checks; unexpected
exceptions produce only the existing generic runner message.

The frozen legacy path list predates prospective GovernancePreflightV1 routes.
For the exact Issue #456 branch only, the runner hard-binds the fixed base and
eleven paths in code, validates repository history and the matching preflight,
then omits only the obsolete legacy `check_changed_files` call. Legacy parity,
branch, required-file, and every `PRESERVED_CHECKS` check still run. Every other
branch retains the frozen legacy scope path unchanged; a coherent preflight plus
extra-path edit is rejected by the independently hard-coded path equality.

## Security, privacy, and observability

- Validation is standard-library-only, offline, and performs no provider call,
  credential lookup, egress, spend, telemetry, or persistence.
- Inputs and exception details are never logged. The observable result is an
  empty finding set or generic `CUT1.BUNDLE.PROTOCOL`, propagated as process
  status by the runner.
- V1, v2, and immutable files are bounded before parsing. Missing, oversized,
  directory, leaf-symlink, and symlinked-parent cases fail closed.
- Fixed-path checks reduce ordinary worktree substitution risk. An actor with
  concurrent write access could still race a path after it is opened; CI and
  review must run on an immutable exact head, and this local governance checker
  is not a hostile multi-tenant filesystem sandbox.
- No uploaded document, prompt, transcript, provider output, personal data, or
  presenter asset is added or processed by this change.

## Consequences and limitations

Mutable ledgers, routes, tests, ADRs, preflights, and canonical prose may evolve
without falsely invalidating the immutable Cut 1 bundle. Their accepted #452
state remains auditable through v1 and Git history; v2 does not erase it.

This decision changes no Meera, Raj, or Myra role or parity requirement, no
framing, motion, voice, language, caption, grounding, consent, provenance,
privacy, or numeric threshold, and no provider candidate. It does not prove
human acceptance, media quality, production readiness, public availability, or
literal indistinguishability. It authorizes no product/runtime/provider/media
work. Issue #16 and Lane A remain blocked until Issue #456 is reviewed and
merged and Issue #16 subsequently closes under its own authority.

## Alternatives rejected

- Continue hashing mutable current bytes: reproduces the evolvability conflict.
- Rewrite v1: destroys accepted historical identity.
- Drop integrity checks: permits acceptance-contract drift.
- Hash general prose selectively: creates an unstable and ambiguous live set.
