# Adversarial Invariant Matrix Template

Use this template only under an exact OWNER-approved sensitive-work route. The
machine-readable matrix and RED-freeze overlay are authoritative; this document
is the reviewer-facing projection.

## Route identity

| Field | Required value |
|---|---|
| Issue and parent | Exact issue numbers and authority URLs |
| Branch | Exact branch |
| Base and tree | Forty-hex commit and tree |
| Expiry | Absolute timestamp |
| Activation | Exact enum; normally `NONE` |
| Authority effect | Exact enum; normally `NO_AUTHORITY_EFFECT` |
| Paths and budgets | Exact paths, per-file/partition/aggregate/binary caps |

## Closed universes

List every dimension, test class, stage, phase, verdict, blocker class, and
mutation action. The executable validator must reject removed, added,
duplicated, reordered, or silently non-applicable members.

## Invariant rows

| Invariant ID | Contract/version | Dimension | Stage | Predecessors | Lifecycle state/operation | Phase | Exact invariant | Trust precondition | Authorization precondition | Case profiles | Exact finding tuple | Historical verdict | Current verdict | Graph eligible | Mutant/action | Kill test | Blocker class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ACP-...` | `...V1` | one closed dimension | one exact stage | ordered earlier stages | exact state and operation | historical/current/acceptance | falsifiable rule | independent input only | phase/scope rule | all required classes | stage, phase, code, location | exact enum | exact enum | true/false | named remove/bypass/reorder/replace | exact test name | implementation/evidence |

Each major invariant must cover positive, negative, boundary, malformed,
deletion, corruption, reordering, duplication, substitution, and maximum
cardinality. Reference normalized profiles only when the executable validator
expands and verifies the complete Cartesian product.
The machine contract must define exact class-precedence and reconstruction
overrides so a malformed, deleted, corrupted, duplicated, substituted, or
reordered input resolves to the real earliest pipeline finding rather than an
invariant-label-derived finding.

Every normalized case must resolve through a closed independent fixture
registry. Each fixture carries only already-mutated untrusted candidate bytes,
evaluation context, independent trust and authorization inputs, and optional
retained reconstruction material. Outside that retained historical transcript,
case, dimension, class, mutation recipe, finding, verdict, assertion, mutant,
and expected-outcome labels are forbidden; retained values are observations,
never instructions for the current result.
Opaque content must not be derived from those public labels. The strict parser
must return an exact typed rejection for duplicate, unknown, forbidden, missing,
wrongly typed, malformed-hex, invalid-enum, malformed-context, malformed-retained,
or oversized stimulus input.
Bind the fixture bytes/hash, exact assertion identity, ordered stage ledger, exact
signature/key/message crypto ledger or explicit no-call, graph result/selection,
three-phase verdicts, mutant, blocker class, and evidence state. The executor
accepts only the stimulus, calls exactly one canonical evaluator or
reconstructor selected by the frozen per-cell mode, and wraps the exact returned
object with the stimulus digest. Observe that delegation for every resolved
reference, assert complete crypto-spy consumption, compare evaluation transcripts
under outcome-distinct derangements, and perturb phase, time, trust,
authorization, crypto, graph, and replay inputs independently. Every dimension's
negative and boundary cases must differ operationally; label, digest, count,
recipe, or echo completeness is not behavioral completeness.

## Pipeline-call ledger

| Case ID | Bounds | Parse | Schema | Identity | Trust/crypto | Authorization | Graph/conflict | Phase verdict | Earliest exact finding |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `...` | exact count | exact count | exact count | exact count | exact count | exact count | exact count | exact count | stage, phase, code, location |

Every count after an earlier rejection is zero.

## Cryptographic ledger

| Ordinal | Candidate ID | Signature | Total candidates | Phase | Independently supplied key | Message identity | Exact result |
|---:|---|---|---:|---|---|---|---|
| 0 | exact value | exact bytes/hash | exact count | exact enum | exact external reference | exact canonical message/hash | true/false |

Broad success mocks are prohibited. Include real public vectors and mutated
negative vectors without private/signing material.

## Controlled mutants

| Mutant ID | Action | Exact source/anchor | Change | Named kill test | Expected exact finding/verdict | Observed exact finding/verdict | Result | Blocker class |
|---|---|---|---|---|---|---|---|---|
| `MUT-...` | remove/bypass/reorder/replace | exact path and unique anchor | exact edit | exact test | exact tuple/enums | exact tuple/enums | killed/survived | implementation/evidence |

Run only in disposable copies. An import failure or unrelated assertion does
not kill the intended mutant. Bind each assertion identity to its matrix-owned
exact code, location, three-phase verdict, stage ledger, and selection rule.

## Budget feasibility

| Level | Name | Cap | Projection | Projected use | Actual use | Disposition |
|---|---|---:|---:|---:|---:|---|
| per-file/partition/aggregate | exact name | number | number | percent | number | normal / >=85% review / >=90% stop |

Never compress semantics to fit a cap.

## Pre-GREEN review overlay

The immutable machine overlay, created after reviews, must bind:

- exact RED head;
- matrix and focused-test Git blob OIDs and SHA-256 values;
- independently frozen semantic SHA-256;
- three distinct reviewer identities and exact review URLs;
- architecture, security/trust, and mutation dispositions;
- the exact ordered genuine-RED node catalog and its independent digest;
- separate implementation/evidence blocker counts;
- activation and authority effect; and
- `PRE_GREEN_REVIEWS_COMPLETE` state.

Missing, mutable, self-reviewed, stale, mismatched, noncanonical, duplicate-key,
or incomplete evidence fails closed.

## Transition and status

Record focused tests, mutation results, blocker counts, and the next allowed
action. Do not begin repository-wide CI or push while focused convergence is
red. A new invariant class returns to matrix and RED review.
