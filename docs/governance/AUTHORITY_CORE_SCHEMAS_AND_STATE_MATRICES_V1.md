# Authority Core Schemas and State Matrices V1

Status: `CHILD_A_CONTRACT_NONACTIVATING`

Activation: `NONE`

Issue: [#431](https://github.com/imrohitagrawal/narratwin-ai/issues/431), child of [#426](https://github.com/imrohitagrawal/narratwin-ai/issues/426)

Architecture predecessor: [#427](https://github.com/imrohitagrawal/narratwin-ai/issues/427), [PR #430](https://github.com/imrohitagrawal/narratwin-ai/pull/430), merge `4d239942eeda0c0b6c385b2d85dae873af076aa6`

## 1. Binding and positive claims

This document defines three closed structural contracts, two exhaustive lifecycle matrices, one internal canonical byte profile, immutable hash-link checks, compatibility behavior, and a documentation-quality repository gate. It does not create, accept, select, activate, execute, persist, acquire, or publish an authority object or route.

The owned contracts are:

1. `MasterProgramAuthorityDecisionV1` — an immutable proposal/decision record that links a controller proposal to zero or one selected manifest.
2. `Cut1AuthorityManifestV1` — an immutable, bounded set of content-addressed authority-value references linked back to a decision.
3. `ActiveProgramRouteV1` — an immutable route boundary covering issues, branch, PR, base, predecessor, paths, budget, tests, reviewers, and execution window.

Structural validation means only “these bytes satisfy Child A.” It never means approved, current, active, trusted, fresh, executable, merged, released, or production-ready.

## 2. Owned invariants

- `AK-001`: an issue, comment, file, fixture, test, check, or structurally valid object has `NO_AUTHORITY_EFFECT`. Authority acceptance requires later integrated Child F evaluation over evidence owned by B–E.
- `AK-004`: a validated revision is byte-immutable. Revision `n + 1` retains the same repository, program, generation, schema, and object identity; names revision `n` by its exact content hash; increments by one; and has its own recomputed content hash. A fork, collision, cycle, missing parent, or in-place byte mutation is rejected.
- `AK-012`: each legal transition has exactly one source, operation, target, actor class, guard identifier, typed-reference class, effect, idempotency rule, rejection behavior, recovery class, and prohibited-substitute set. Every other state × operation cell is explicitly illegal.

## 3. Closed contract shapes

All root and nested objects reject unknown members. All listed root members are required; nullable values remain present as JSON `null`.

### 3.1 Common root fields

| Field | Exact rule |
|---|---|
| `schemaVersion` | One exact supported V1 contract name. |
| `repository` | Exact ASCII string `github.com/imrohitagrawal/narratwin-ai`. |
| `programId` | Exact ASCII string `narratwin-cut1`. |
| `generationId` | `generation:` plus 1–64 lowercase ASCII letters, digits, dot, or hyphen. |
| `objectId` | Contract-specific prefix (`decision:`, `manifest:`, or `route:`) plus a bounded lowercase identity. |
| `revision` | Signed-64-bit JSON integer, minimum 1; booleans and floats are not integers. |
| `lifecycleState` | Exact contract lifecycle enum; `UNVERIFIED` and `CONFLICTING` are excluded. |
| `predecessorContentHash` | `null` only for revision 1; otherwise 64 lowercase hexadecimal SHA-256 characters. |
| `contentHash` | The exact domain-separated hash defined in section 5. |
| `validity` | Closed `notBefore`, `expiresAt`, `revokedAt`, and `revocationReference` object. |
| `transition` | `null` for revision 1; otherwise the exact closed transition record. |
| `prohibitedCapabilities` | The exact ordered denial set embedded in each schema. Omission, addition, or reordering fails. |

`ContentAddressedReferenceV1` is a closed four-member value: `referenceType`, `schemaVersion`, `sha256`, and `subject`. It is only a content pointer. Production, signer trust, freshness, capture, and authenticity are Child B responsibilities.

The closed transition record contains `actorClass`, `effectId`, `guardReferences`, `idempotency`, `operation`, `prohibitedSubstitutes`, `recoveryClass`, `rejectionBehavior`, `sourceState`, and `targetState`.

### 3.2 Decision-only fields

- `sourceProposal`: required content-addressed proposal reference.
- `decisionAction`: exactly `SELECT_MANIFEST`, `REJECT_MANIFEST`, `SUPERSEDE_CURRENT`, or `REVOKE_CURRENT`.
- `effectiveAt`: exact UTC decision-effect time.
- `selectedManifest`: exact manifest reference if and only if the action selects or supersedes; `ACCEPTED_CURRENT` requires it.
- `priorDecision`: nullable prior-decision reference used by supersession or revocation.

### 3.3 Manifest-only fields

- `sourceProposal` and `decisionBacklink`: required proposal and decision references.
- `authorityValues`: a closed object containing exactly ten content-addressed references: `canonicalNarration`, `downstreamOrderPolicy`, `finalRenderPolicy`, `ownerAuthoritySource`, `presenterSelection`, `providerPolicy`, `rendererPolicy`, `revalidationPolicy`, `spendPolicy`, and `supersededSourceSet`.
- `capabilityClassifications`: the same ten closed keys, each exactly `PRESENT` or `DEFERRED`.

These references bind content identities only. They do not authorize a provider, credential, expense, presenter, narration, render, or execution.

### 3.4 Route-only fields

The route requires `controllerIssue`, `parentIssue`, `childIssue`, `branch`, `targetBranch`, state-bound `pullRequest`, `baseSha`, `predecessorMergeSha`, traversal-safe `allowedPaths`, exact `maxPathCount`, `maxChargedLines`, separate `focusedTestCommands` and `aggregateTestCommands`, `reviewerRoles`, typed `decision` and `selectedManifest`, nullable state-bound `supersededRoute`, and `executionWindow`. `targetBranch` is exactly `main`; reviewer roles are exactly OWNER, Principal Architect, Principal Test Engineer, and non-author.

Schema definition never changes a route from `DRAFT`, and this repository contains no conforming route instance.

## 4. Canonical JSON profile

`NarraTwinAuthorityCanonicalJsonV1` is an internal profile. This work does not claim conformance to RFC 8785, JCS, or another external JSON canonicalization standard.

1. Input is at most 131,072 bytes and must decode as UTF-8 without replacement. A BOM is not canonical.
2. Duplicate object members are rejected during syntactic parsing, before schema interpretation.
3. JSON syntax errors, trailing data, NaN, positive/negative infinity, and every floating-point lexical form are rejected.
4. Values are limited to objects, arrays, printable-ASCII strings, signed 64-bit integers, booleans, and null. Python/JSON bool-versus-int confusion is rejected by exact type checks.
5. Object depth is at most 12, objects have at most 64 members, arrays at most 128 items, and strings at most 2,048 UTF-8 bytes. Repository paths are separately bounded to 512 bytes.
6. Member names are sorted by ASCII code point; no insignificant whitespace is emitted; separators are exactly comma and colon; JSON literals are lowercase.
7. Strings are not normalized. Only code points U+0020 through U+007E are allowed, so normalization-equivalent non-ASCII spellings fail instead of converging silently. Quote and reverse-solidus use the required JSON escapes; solidus is unescaped.
8. Integers use base-10 shortest form with no leading zero, plus sign, exponent, fraction, or negative zero. The canonical re-encoding comparison enforces the lexical rule.
9. Timestamps are printable ASCII UTC instants exactly `YYYY-MM-DDTHH:MM:SSZ`, with real calendar values, no fractional seconds, offset, or leap-second spelling.
10. Canonical bytes contain no leading/trailing whitespace and no final newline. Accepted input bytes must equal a fresh canonical encoding byte for byte.

## 5. Hashing and immutable links

The content hash is lower-case hexadecimal SHA-256 over:

```text
UTF8("NARRATWIN-AUTHORITY-OBJECT-V1") || 0x00 ||
UTF8(schemaVersion) || 0x00 ||
canonicalBytes(object with contentHash member removed)
```

SHA-256 is the algorithm specified by NIST FIPS 180-4, August 2015 final/update 1, DOI `10.6028/NIST.FIPS.180-4`; primary source accessed 2026-08-15 at `https://csrc.nist.gov/pubs/fips/180-4/upd1/final`. This use provides deterministic content identity and mutation detection. It is not a signature, proof of actor identity, trust decision, freshness proof, or secret-bearing MAC.

For each successor, `predecessorContentHash` must resolve to exactly one validated prior object with the same stable identity and revision exactly one lower. Two different bytes at one immutable identity/revision are a collision; two successors of one predecessor are a fork; self-reference or any cycle is illegal. Repair creates a new hash-linked successor; it never edits accepted bytes.

## 6. Compatibility

- Supported negotiation is an exact match to one of the three V1 names. There is no “latest,” wildcard, prefix, or best-effort selection.
- A V0 name for a requested V1 contract is `DOWNGRADE_REJECTED`.
- A V2 or later same-family name is `UNSUPPORTED_VERSION` until a separately approved schema and migration exists.
- An unrelated or missing name is `SCHEMA_VERSION_MISMATCH`.
- V1 readers do not ignore unknown members and do not reinterpret future enums.
- Backward compatibility is immutable-byte retention: existing accepted V1 bytes remain V1. A future format produces a separately approved, hash-linked object; it does not rewrite V1 bytes.

## 7. Decision and manifest lifecycle

The machine-readable matrix is `DecisionManifestLifecycleV1`. Each guard means all named facts arrive as typed, content-addressed references; Child A neither produces nor trusts them.

| ID | Source → operation → target | Exact actor | Required guard | Deterministic effect | Recovery |
|---|---|---|---|---|---|
| D01 | PROPOSED → REVIEW → REVIEWED | Independent reviewer | Exact-byte review reference covering schema, hash, and generation | Create REVIEWED successor | Hash-linked successor |
| D02 | PROPOSED → REJECT → REJECTED | OWNER | Exact-byte OWNER rejection reference | Create terminal REJECTED successor | Hash-linked successor |
| D03 | REVIEWED → OWNER_APPROVE → OWNER_APPROVED | OWNER | OWNER approval for exact reviewed bytes and validity window | Create OWNER_APPROVED successor | Hash-linked successor |
| D04 | REVIEWED → REJECT → REJECTED | OWNER | Exact-byte OWNER rejection reference | Create terminal REJECTED successor | Hash-linked successor |
| D05 | OWNER_APPROVED → MERGE → MERGED | Merge coordinator | Exact-head merge reference preserving approved bytes | Create MERGED successor | Hash-linked successor |
| D06 | OWNER_APPROVED → REJECT → REJECTED | OWNER | Exact-byte OWNER withdrawal/rejection reference | Create terminal REJECTED successor | Hash-linked successor |
| D07 | MERGED → ACCEPT_CURRENT → ACCEPTED_CURRENT | Authority acceptor | Exact merged decision, selected-manifest link, validity, and conflict-free evaluation references | Create ACCEPTED_CURRENT successor; no source alone activates | Hash-linked successor |
| D08 | MERGED → REJECT → REJECTED | OWNER | Exact merged bytes plus OWNER rejection reference | Create terminal REJECTED successor | Hash-linked successor |
| D09 | ACCEPTED_CURRENT → SUPERSEDE → SUPERSEDED | Authority acceptor | Exact current object plus approved successor reference | Create SUPERSEDED successor linked to replacement | Hash-linked successor |
| D10 | ACCEPTED_CURRENT → REVOKE → REVOKED | OWNER | Exact current object plus revocation reason/reference | Create REVOKED successor | Hash-linked successor |
| D11 | ACCEPTED_CURRENT → EXPIRE → EXPIRED | Expiry evaluator | Exact current object plus deterministic expiry-time reference | Create EXPIRED successor | Hash-linked successor |

`REJECT` has no legal source after `ACCEPTED_CURRENT`. All terminal-state operations are illegal. Illegal cells have effect `NO_MUTATION_TYPED_ERROR` and recovery `CORRECT_AND_RETRY_OR_CREATE_SUCCESSOR`.

## 8. Route lifecycle

The machine-readable route matrix is `ActiveProgramRouteLifecycleV1`.

| ID | Source → operation → target | Exact actor | Required guard | Deterministic effect | Recovery |
|---|---|---|---|---|---|
| R01 | DRAFT → REVIEW → REVIEWED | Independent reviewer | Exact route-byte architecture/test review reference | Create REVIEWED successor | Hash-linked successor |
| R02 | DRAFT → REJECT → REJECTED | OWNER | Exact route-byte rejection reference | Create REJECTED successor | Hash-linked successor |
| R03 | REVIEWED → OWNER_APPROVE → OWNER_APPROVED | OWNER | Exact route bytes, scope, budget, base, and expiry approval | Create OWNER_APPROVED successor | Hash-linked successor |
| R04 | REVIEWED → REJECT → REJECTED | OWNER | Exact route-byte rejection reference | Create REJECTED successor | Hash-linked successor |
| R05 | OWNER_APPROVED → VERIFY_PREDECESSOR → PREDECESSOR_VERIFIED | Predecessor verifier | Exact predecessor merge/base/history reference | Create PREDECESSOR_VERIFIED successor | Hash-linked successor |
| R06 | OWNER_APPROVED → REJECT → REJECTED | OWNER | Exact route-byte rejection/withdrawal reference | Create REJECTED successor | Hash-linked successor |
| R07 | PREDECESSOR_VERIFIED → ACTIVATE → ACTIVE | Route activator | Exact final route bytes, unexpired window, linked accepted decision/manifest, predecessor verification, and required reviews | Create ACTIVE successor; no marker substitutes | Hash-linked successor |
| R08 | PREDECESSOR_VERIFIED → REJECT → REJECTED | OWNER | Exact route-byte rejection reference | Create REJECTED successor | Hash-linked successor |
| R09 | ACTIVE → MERGE → MERGED | Merge coordinator | Exact-head merge reference within path, budget, test, and review boundaries | Create MERGED successor | Hash-linked successor |
| R10 | MERGED → CLOSE → CLOSED | Closeout coordinator | Exact merge and terminal-check references | Create CLOSED successor; no execution effect | Administrative closeout |
| R11–R15 | DRAFT, REVIEWED, OWNER_APPROVED, PREDECESSOR_VERIFIED, or ACTIVE → SUPERSEDE → SUPERSEDED | OWNER | Exact route plus replacement-route reference | Create SUPERSEDED successor | Hash-linked successor |
| R16–R20 | DRAFT, REVIEWED, OWNER_APPROVED, PREDECESSOR_VERIFIED, or ACTIVE → EXPIRE → EXECUTION_EXPIRED | Expiry evaluator | Exact route and deterministic execution-expiry reference | Create EXECUTION_EXPIRED successor and prohibit governed mutation | Hash-linked successor |
| R21 | EXECUTION_EXPIRED → CLOSE → CLOSED | Closeout coordinator | Exact expired route plus administrative closeout references | Create CLOSED successor with no activation/execution effect | Administrative closeout |

The JSON artifact expands R11–R20 into one row per source and explicitly classifies all 90 route state × operation cells. `EXECUTION_EXPIRED` permits only R21. Administrative closeout cannot be substituted for R07 and cannot reactivate, mutate, merge, spend, call a provider, or perform governed execution.

Every legal row has `IDEMPOTENT_SAME_BYTES`; a repeat with different bytes is rejected. Every rejection has `NO_MUTATION_TYPED_ERROR`. Prohibited substitutes are exactly issue, comment, file, fixture, test, and CI markers.

## 9. Fail-closed fixtures and enforcement

`tests/fixtures/authority-core-v1-cases.json` is visibly fixture-only, uses an `.invalid` repository, and declares activation `NONE`. Every closed case binds an executable probe consumed by the gate; the accompanying mutation tests feed its parser, schema, lineage, matrix, false-authority, coordinated-mutation, expiry, and Child B–F boundary cases through the validators.

`scripts/quality/issue431_authority_core.py` is a documentation-quality validator. It parses no live authority location, persists nothing, performs no egress, and exposes no runtime service. `check_stage8_docs.py` invokes it only as a repository quality gate.

## 10. Deferred interfaces

- Child B owns evidence envelopes, producer trust, signature/key lifecycle, capture, authenticity, and freshness.
- Child C owns projections, CAS persistence, bootstrap, generation fencing, and recovery protocol.
- Child D owns audit coordination, reservations, terminal receipts, transport, and closeout service.
- Child E owns historical reconciliation and GitHub acquisition.
- Child F owns integrated evaluation, activation, kernel/oracle composition, and the only future authority decision point.

No provider, credential, egress, spending, media, infrastructure, deployment, publication, release, SLA, commercial, or production capability or claim is created here.
