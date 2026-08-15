# ADR 0061: Closed authority schemas and exhaustive state matrices

## Status

Accepted for Child A implementation under Issue #431; nonactivating.

## Context

ADR 0060 and the merged architecture proposal assign Child A the structural contracts for authority decisions, manifests, routes, immutable successors, and exact transition definitions. Open JSON, ambiguous canonical bytes, implicit transitions, or marker-based acceptance would permit false authority before Children B–F exist.

## Decision

Adopt three custom, closed `NarraTwinClosedSchemaDocumentV1` artifacts and the internal `NarraTwinAuthorityCanonicalJsonV1` byte profile. Unknown/duplicate members, floats, non-ASCII ambiguity, unsupported versions, noncanonical bytes, invalid identities, resource-limit violations, and hash/link mutations fail closed.

Adopt exhaustive `DecisionManifestLifecycleV1` and `ActiveProgramRouteLifecycleV1` state × operation grids. Each legal edge binds one exact actor, typed guard, deterministic effect, idempotency rule, rejection behavior, recovery, and substitute-denial set. `UNVERIFIED` and `CONFLICTING` remain evaluation outcomes. Execution expiry prohibits governed mutation and permits only administrative closeout.

SHA-256 content identities use an explicit NarraTwin domain prefix and exclude only the `contentHash` member. Structural validation never accepts or activates authority.

Cross-contract linkage is acyclic: an accepted decision selects merged-manifest bytes, an accepted manifest successor backlinks accepted-decision bytes, terminal manifest revisions retain that backlink through their acceptance ancestor, and a route binds that exact accepted pair. Governed subjects and hashes must resolve with identical repository, program, generation, and required lifecycle state. Set-like route arrays are lexicographically canonical; typed source-state, accepted-successor, reciprocal, revocation-reference, and effective-time guards bind their exact governed bytes or scalar.

## Consequences

- Accepted bytes can only be changed by a new hash-linked successor.
- V1 readers reject downgrades and future versions until separately approved.
- Fixtures and schema documents remain visibly non-authoritative.
- Child B retains evidence/trust; C projection/CAS/bootstrap; D audit/receipts; E acquisition/reconciliation; F integrated evaluation/activation.
- No runtime service, persistence, provider, credential, egress, spending, media, infrastructure, deployment, publication, release, or production capability is introduced.

## Evidence

The dedicated Issue #431 validator, focused mutation suite, exact Stage 8 dispatch, and Child A specification provide executable documentation-quality evidence for AK-001, AK-004, and AK-012.
