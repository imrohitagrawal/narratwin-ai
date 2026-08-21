# Authority Evidence and Producer Trust V1

Status: documentation-quality offline verification contract. Activation is `NONE`.

## Boundary

This contract defines immutable evidence, independently pinned producer roots,
public-key lifecycle records, and retained-byte reconstruction. It provides no
signing, private-key, acquisition, persistence, network, identity-proof,
authority-selection, deployment, release, or runtime capability. A valid file,
hash, signature, fixture, test, or repository check has
`NO_AUTHORITY_EFFECT`.

All candidate documents and retained bytes are untrusted. Verification is pure
and receives every time, root pin, expected history head, and byte sequence as
an explicit argument. It never reads an ambient clock or derives trust from a
candidate document.

## Common closed profile

- JSON is strict UTF-8 without BOM or trailing bytes. Duplicate or unknown
  members reject before semantic use.
- Values are printable ASCII, integer-only JSON with depth at most 12, at most
  64 ordinary members/items, and ordinary strings at most 2,048 bytes.
- Canonical bytes sort object keys by ASCII code point and use no insignificant
  whitespace or trailing newline. Arrays retain their schema-defined order.
- A timestamp is exactly `YYYY-MM-DDTHH:MM:SSZ` and denotes a valid UTC second.
- SHA-256 values are exactly 64 lower-case hexadecimal characters. Ed25519
  public keys are 64 and signatures 128 lower-case hexadecimal characters.
- Presented malformed data is `INVALID`; missing required data is
  `UNAVAILABLE`; incompatible valid facts are `CONFLICTING`. Precedence is
  `CONFLICTING > INVALID > UNAVAILABLE > VALID`, retaining all findings.
- Every result fixes `authorityEffect=NO_AUTHORITY_EFFECT` and
  `activation=NONE`.

Hard bounds are 262,144 bytes per JSON/root/key/envelope blob, 131,072 bytes per
payload, 16,777,216 aggregate retained bytes, 64 key revisions, and 256 evidence
members. Bounds are enforced before cryptographic or graph work.

## Exact domains

Each shown `NUL` is one `0x00` byte. `C14N(x)` is the common canonical profile.

- Evidence identity: `SHA256("NARRATWIN-AUTHORITY-EVIDENCE-OBJECT-V1" || NUL || schemaVersion || NUL || C14N(object without contentHash))`.
- Root identity: `SHA256("NARRATWIN-AUTHORITY-TRUST-ROOT-V1" || NUL || schemaVersion || NUL || C14N(object without contentHash))`.
- Key-record identity: `SHA256("NARRATWIN-AUTHORITY-PRODUCER-KEY-V1" || NUL || schemaVersion || NUL || C14N(record without contentHash, retaining authorization signatures))`.
- Reconstruction identity: `SHA256("NARRATWIN-AUTHORITY-EVIDENCE-RECONSTRUCTION-V1" || NUL || schemaVersion || NUL || C14N(manifest without contentHash))`.
- Public-key ID: `SHA256("NARRATWIN-AUTHORITY-ED25519-PUBLIC-KEY-V1" || NUL || raw 32-byte public key)`.
- Evidence signature: `"NARRATWIN-AUTHORITY-EVIDENCE-SIGNATURE-V1" || NUL || schemaVersion || NUL || C14N(envelope without contentHash and signature)`.
- Root authorization: `"NARRATWIN-AUTHORITY-KEY-ROOT-AUTHORIZATION-V1" || NUL || schemaVersion || NUL || C14N(key record without contentHash and both authorization signatures)`.
- Predecessor authorization: `"NARRATWIN-AUTHORITY-KEY-PREDECESSOR-AUTHORIZATION-V1" || NUL || schemaVersion || NUL || the same unsigned key-record bytes`.

`AuthorityRootPinSetV1` is an independent input descriptor, not a candidate
trust object. Its only members are `schemaVersion`, `repository`, `programId`,
`generationId`, `producerId`, `evaluationPhase`, and `rootContentHashes`.
`evaluationPhase` is exactly `ACCEPTANCE` or `CURRENT`; the hash list is
nonempty, lower-case, sorted, and unique. Its identity is
`SHA256("NARRATWIN-AUTHORITY-ROOT-PIN-SET-V1" || NUL ||
"AuthorityRootPinSetV1" || NUL || C14N(descriptor))`. A verifier compares this
identity with a separately supplied expected hash. It never constructs or
extends a pin set from candidate roots, envelopes, fixtures, paths, or key
records.

Payload classes have an exact nonexecutable media-type bijection:
`BOUNDARY_SET -> application/vnd.narratwin.authority.boundary-set-v1+json`,
`CHECK_SET -> application/vnd.narratwin.authority.check-set-v1+json`,
`CLOSEOUT_RECEIPT -> application/vnd.narratwin.authority.closeout-receipt-v1+json`,
`CONTENT_REFERENCE -> application/vnd.narratwin.authority.content-reference-v1+json`,
`ISSUE_STATUS -> application/vnd.narratwin.authority.issue-status-v1+json`,
`LINKAGE_SET -> application/vnd.narratwin.authority.linkage-set-v1+json`,
`MERGE_RECEIPT -> application/vnd.narratwin.authority.merge-receipt-v1+json`,
`NEGATIVE_ASSERTION -> application/vnd.narratwin.authority.negative-assertion-v1+json`,
`OWNER_DECISION -> application/vnd.narratwin.authority.owner-decision-v1+json`,
`REASON -> application/vnd.narratwin.authority.reason-v1+json`,
`REVIEW_ATTESTATION -> application/vnd.narratwin.authority.review-attestation-v1+json`,
and `TIME_ASSERTION -> application/vnd.narratwin.authority.time-assertion-v1+json`.
No generic, executable, or aliased media type is permitted.

## Key lifecycle and heads

A history is scoped only to `(rootContentHash, producerId)`, is capped at 64
records, and is traversed iteratively from an independently supplied exact head
through every `historyPredecessorContentHash` to sequence 1. Timestamps never
resolve a gap, fork, cycle, duplicate identity, competing successor, or
unattested suffix. An exact duplicate is idempotent; the same immutable identity
with different bytes conflicts.

- `K01 ISSUE_GENESIS`: sequence 1, revision 1, exact root genesis binding, no
  predecessor or predecessor signature.
- `K02 ROTATE`: sequence increments by one; a distinct revision-1 successor
  names the active predecessor and is eligible at `activationTime` only after
  root and predecessor public signatures verify. The predecessor remains
  eligible until an explicit K03 retirement. Competing rotated children
  conflict.
- `K03 RETIRE`: same key, next revision and sequence, exact same-key and history
  predecessors, prospective `retiredAt`, and root authorization. Captures are
  eligible only strictly before `retiredAt`.
- `K04 REVOKE`: same key, next revision and sequence, root authorization,
  `activationTime <= invalidatesFrom <= revokedAt`. At evaluation times before
  `revokedAt`, it is not backdated; at or after `revokedAt`, captures at or after
  `invalidatesFrom` reject.
- `K05 RETIRED -> REVOKED`: the same rules apply to the next revision after K03.

Every root version starts an independent history and requires its own pin. An
old root, signature, or key chain cannot promote a successor root. Ordinary
succession uses `predecessorRootContentHash` and never invalidates the prior
root. Compromise recovery additionally uses `priorRootCompromise`, containing
the exact `priorRootContentHash` and half-open `invalidatesPriorRootFrom`
boundary. Only a separately pinned successor can make that declaration
structurally applicable. This structural result does not verify signatures,
confer trust, or activate authority; key-history structure inspection never
applies it.

The evaluator receives distinct acceptance-time and current expected heads and
root-pin-set descriptors. Each head is exactly `(rootContentHash, producerId,
historySequence, keyRecordContentHash)`. Neither may be learned from presented
history. A missing head is unavailable; a wrong, rolled-back, or prefix head is
invalid and cannot suppress later revocation.

## Closed objects

The four schemas beside this contract are authoritative field/type closures:

- `AuthorityEvidenceEnvelopeV1` binds one exact subject transition, evidence
  role, producer/root/key, observation window, payload reference, and signature.
- `AuthorityProducerTrustRootV1` is only a candidate configuration; an
  independent root pin and pin-set hash are always required.
- `AuthorityProducerKeyV1` records one immutable lifecycle event and retains
  root authorization; K02 additionally retains predecessor authorization.
- `AuthorityEvidenceReconstructionV1` is a bounded reference manifest. Blob
  bytes arrive in a separate exact-cardinality in-memory mapping; paths, URIs,
  loaders, callbacks, and network resolution are prohibited.

The machine-readable state matrix freezes lifecycle, bounds, domains, verdict
precedence, and typed-reference taxonomy. Schema validity does not establish
producer identity, reviewer eligibility, factual truth, authority, or
activation.

## Failure, recovery, and retention

Malformed, noncanonical, misbound, replayed, unauthorized, not-yet-valid,
retired, revoked, expired, stale, conflicting, truncated, or unreconstructable
input fails closed with bounded typed findings that never echo payload bytes.
There is no fallback, TOFU, algorithm negotiation, remote lookup, or exception
to a pin/head requirement.

Recovery never edits accepted bytes. Missing bytes must be recovered exactly;
stale evidence needs a new observation and envelope; key replacement needs a
separately authorized successor; conflicts remain quarantined; and deleted
required bytes make reconstruction `UNAVAILABLE`. Historical and current
verdicts remain separate. Retention does not extend freshness, trust, root
validity, or authority.

## Corrected executable-artifact identity freeze

The following subordinate bytes are frozen after the reset corrections. The
SHA-256 of this containing contract is recorded externally in the exact-head
closeout packet to avoid a self-referential hash.

- `authority-evidence-trust-state-matrices-v1.json`: `34a60bb3318b6c7477519238839f034496d2c36507dd4ae1f87144a448de7cf4`
- `authority-evidence-envelope-v1.schema.json`: `4e699c1223c20790b5dbcfb461fa72978448474a7de348aa0267e2befe334585`
- `authority-evidence-reconstruction-v1.schema.json`: `7951450388b8e78650a380e852ac95bd9114b67cdaae24c73122f365273ad65b`
- `authority-producer-key-v1.schema.json`: `90c47cf64be8815fbbfe8a3e074929d767f71696ee8bfdeb63ebf09da30f4ba6`
- `authority-producer-trust-root-v1.schema.json`: `5b39ebcf62de1e515ed453ab9700c2dfea5364e85419f4b2d6083bf49074f8ed`
