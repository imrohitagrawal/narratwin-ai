# ADR 0063: Authority Evidence and Producer Trust

- Status: Proposed for Issue #434 review
- Date: 2026-08-18
- Activation: `NONE`
- Authority effect: `NO_AUTHORITY_EFFECT`

## Context

Child A supplies closed authority-subject schemas and lifecycle matrices, but
does not establish how evidence about those subjects is signed, rooted,
rotated, reconstructed, or evaluated at historical and current instants.
Accepting candidate-provided roots, ambient time, incomplete key history, or a
valid signature without exact lineage would create false authority.

Child B must remain documentation-quality infrastructure. It cannot create a
live producer, trust root, private key, signer, store, acquisition service,
provider integration, runtime authority, or deployment capability.

## Decision

Adopt `AuthorityEvidenceEnvelopeV1`, `AuthorityProducerTrustRootV1`,
`AuthorityProducerKeyV1`, and `AuthorityEvidenceReconstructionV1` as closed,
canonical JSON contracts. Bind their identities with separate SHA-256 domains
and bind signatures with distinct evidence, root-authorization, and
predecessor-authorization domains.

Trust is resolved only from independently supplied, phase-scoped root-pin
descriptors and expected pin-set hashes; exact root bytes; exact acceptance and
current history heads; explicit evaluation times; and the envelope's exact
issuing-key identity. Candidate-derived roots and trust-on-first-use are
prohibited.

Producer-key history is a bounded, immutable, exact-predecessor graph. K01
genesis, K02 dual-authorized rotation, K03 retirement, and K04/K05 revocation
retain distinct state and temporal semantics. Independently pinned successor
roots alone may declare prior-root compromise boundaries. A signature is only
a cryptographic primitive result and cannot bypass root, pin, key, subject,
freshness, replay, or reconstruction validation.

Historical acceptance and current trust are evaluated independently. Missing
required evidence is `UNAVAILABLE`; malformed or misbound presented evidence
is `INVALID`; incompatible well-formed claims are `CONFLICTING`; only a fully
closed phase is `VALID`. Precedence is
`CONFLICTING > INVALID > UNAVAILABLE > VALID`.

Use `cryptography==50.0.0` as a direct development dependency solely for
offline Ed25519 public verification. The Stage 8 system-Python wrapper does not
import the verifier; it invokes exactly
`uv run python scripts/quality/issue434_authority_evidence_trust.py` and
propagates failure.

## Consequences

- Root pins, heads, evaluation times, and retained bytes remain explicit caller
  inputs; no network or ambient clock is consulted.
- Canonical, byte, member, depth, record, and aggregate bounds precede
  expensive parsing, hashing, cryptography, identity indexing, and graph work.
- Reconstruction status is independent of historical/current trust verdicts.
- Fixtures, checks, comments, files, signatures, and agent reviews cannot
  activate authority.
- Activation remains `NONE`; release remains No-Go.

The cost is a deliberately strict contract and larger adversarial test surface.
Future contract changes require a versioned successor and governed migration,
not an in-place weakening.

## Rejected alternatives

- Candidate-derived root selection or TOFU: rejected because the candidate
  could choose its own trust anchor.
- Signature-valid-implies-trusted: rejected because cryptographic validity does
  not establish producer eligibility, lineage, freshness, or subject meaning.
- One combined historical/current verdict: rejected because revocation and
  later trust changes must not rewrite what was valid at acceptance time.
- Ambient wall-clock evaluation: rejected because results would be
  non-reconstructable and nondeterministic.
- Private test keys or runtime signing: rejected as unnecessary and outside
  Child B authority.

## Boundaries and follow-up

Child C owns CAS, persistence, projection, and bootstrap. Child D owns audit and
closeout receipts. Child E owns acquisition and reconciliation. Child F owns
integrated kernel/oracle behavior. Issue #432 remains unmerged source authority
and needs a future parent amendment; this ADR does not implement or reorder it.
