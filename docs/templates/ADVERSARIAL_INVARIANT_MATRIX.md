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
Use a shared neutral content source that is not derived from public labels,
ordinals, hashes, expected outcomes, or registry position. The strict parser
must return an exact typed rejection for duplicate, unknown, forbidden, missing,
wrongly typed, malformed-hex, invalid-enum, malformed-context, malformed-retained,
or oversized stimulus input. Close every nested member over exact identifier,
hash, enum, primitive, range, maximum, cross-field cardinality, and ordered-
ordinal constraints across every pipeline stage. Governed matrix, freeze,
and oracle paths must remain beneath the validated root with no symlink target
or ancestor. Reject directories, sockets, other non-regular files, binary data,
invalid UTF-8, malformed JSON, non-object documents, duplicate members, and
semantically equivalent alternate serialization before trusting content. Freeze
an exact positive static grammar whose local-read entries name only those
governed paths, and independently remove/test every import, call, read target,
and command form. Freeze the safe exact AST dump of the single top-level
governed-reader `FunctionDef`; make it return bytes or an exact typed finding;
prove exact per-path failure tuple identity without retry/later reads; and test
rebinding, ignored guards, reordered reads, unsafe relatives, and the closed
universe of applicable function/class/assignment/loop/context/import/exception/
pattern/Python-3.13-type-alias/async/nested-global/delete binding forms.
Exercise every non-root ancestor for every target with within-root symlinks and
pre-read traps. Retained stage references are stage-sensitive and ordinal-bound;
crypto ordinals/counts/exact 64-byte signature, actual/max cardinality, ledger
row/order/identity, and graph-call ranges are exact and orthogonally isolated
with valid one- and two-candidate bases. Member-type checks cover all eight
stages; float ordinals fail exact integer typing and valid-reference N+1 rows
isolate range enforcement. Reject a second JSON token in both
evaluate and reconstruct stimuli rather than ignoring decoder remainder. The executor must
propagate parser rejection with zero evaluator, reconstructor, or crypto calls.
Bind the fixture bytes/hash, exact assertion identity, ordered stage ledger, exact
signature/key/message crypto ledger or explicit no-call, graph result/selection,
three-phase verdicts, mutant, blocker class, and evidence state. The executor
accepts only the fixture bytes, calls the strict parser exactly once, passes the
identity-distinct parser result to exactly one canonical evaluator or
reconstructor selected by the frozen per-cell mode, and wraps the exact returned
object with the stimulus digest. Observe that delegation for every resolved
reference, assert complete crypto-spy consumption, compare evaluation
transcripts under a fixed expected-only outcome-distinct bijection, execute
unseen evaluate and reconstruct stimuli, and force opposite-mode parser returns
to prove dispatch follows the parsed object. Perturb phase, time, trust,
authorization, crypto, graph, and replay inputs independently. Every dimension's
negative and boundary cases must differ operationally; label, digest, count,
recipe, or echo completeness is not behavioral completeness.

The valid two-candidate reconstruction baseline must wrap the saved real
reconstructor. It delegates parser-returned documents, context, retained
evidence, and the verifier by identity; consumes two ordered exact probes;
asserts the complete stage, crypto, eligibility, precedence, graph, and phase
transcript; and preserves the exact returned `Evaluation` object.

Repository freeze evidence must remain valid after later linear GREEN commits.
Independently bind `.git` directory or strict linked-worktree discovery metadata
with descriptor-relative held-directory traversal, lstat/open/fstat identity,
bounded repeated reads, post-read identity, reverse close, exact backlink/
commondir/layout checks, and absent graft, shallow, local-alternate, and HTTP-
alternate inodes. Freeze a closed role/cap/step/finding/location table and run
every target/ancestor/type/encoding/record/relationship/race case through the
public validator before any Git call. Use freshly created
direct environment literals to bind the derived Git dir/common dir/worktree for
every absolute-Git call. Require SHA-1 plus full strict primary object fsck before
HEAD and RED evidence. Freeze fourteen exact forms and their result, stream,
timeout, return, byte, line, decode, token, role, path, ref, and precedence
contracts. RED type/size/ancestry must precede topology; the complete capped
parent chain must be linear with no merge; recursive no-external-diff/no-renames/
include-submodules checks must prove only the freeze changed. Positionally bind
the four RED objects, reported C3 size to raw bytes, and bounded ASCII author.
Fake gitfiles, corrupt objects, grafts, alternates, local config, legacy forms,
permissive trimming, mutable environment constants, and generic errors must fail.
The oracle must bind all supported and unsupported return codes, exact result/
bytes subclasses, composed failure precedence, every chain invariant, all
positional object swaps/substitutions, full hostile ambient/config markers,
fresh-environment mutation isolation, and single-coordinate argv/keyword/env
mutations. Boundary exclusions must name live trust producers, workflow
capability, dependency mutation/activation, SLA claims, and commercial-readiness
claims in addition to the existing nonactivation universe.
The metadata section must enumerate one closed
`mode/case/role/stimulus/code/location` row per operational case and hash the
exact reader and discovery top-level ASTs. Preserve lexical absolute root bytes;
do not resolve root or pre-root components before held-descriptor traversal.
The reader must derive its target, cap, expected inode kind, and location from a
closed role and the exact first-read `.git` record. The executor must consume
every frozen full execution contract in exact order, including the complete
catalog row, observed stimulus identity, role prefix, and normalized per-role
I/O/cleanup transcript. Cases declared for both layouts must run once
conventionally and once through a real linked worktree.
The Issue #435 RED exemplar owns 94 case rows and 129 ordered executions.
Linked discovery must strictly parse backlink and `commondir` UTF-8, line, and
record shape before relationship comparison or later work. Each dependent read
must compare the previously observed parent-directory type/device/inode, and
discovery must revalidate the `.git`, linked Git directory, and common directory
bindings immediately before process evidence begins.

### Filesystem snapshot boundary

<!-- issue-435-filesystem-snapshot-boundary:start -->
Every repository matrix must also freeze a filesystem threat-model object with
the exact scope, proofs, defense-in-depth controls, Git process-binding model,
excluded threat, claims not made, and disposition for stronger claims. The
Issue #435 exemplar assumes one stable local filesystem metadata and object
snapshot for the full invocation. Its Git process is path-based, not
descriptor-bound; concurrent out-of-process mutation after descriptor close or
during reopen is excluded. Reader-local race detection and final revalidation
must not be promoted into race-free, atomic, or all-concurrent-mutation claims.
Any stronger claim is an `EVIDENCE_BLOCKER` pending new authority and proof.
Freeze a bounded synonym grammar and reject its case, whitespace, hyphen, and
Markdown-normalized variants across every governed claim document. Add
backtick-only and leading/trailing-whitespace-only variants, plus bounded
case-plus-Markdown-plus-hyphen-plus-backtick-plus-edge-whitespace and
bounded-synonym-plus-Markdown-plus-hyphen-plus-backtick-plus-edge-whitespace
compositions with actual Markdown markers and hyphens for every prohibited
family. Mutants omitting backtick removal or final strip must fail.
<!-- issue-435-filesystem-snapshot-boundary:end -->
Freeze fsck status 1 as object-integrity failure, missing-object type status 128
as missing RED, and `-1`, `2`, and `127` for every form as the generic process
finding before byte/decode/line/token semantics. Script the RED-size input for
exact 320/321-byte author evidence and separately test a smaller dynamic cap.
Enumerate all fourteen Git roles against remove-LF, CRLF, extra-line,
corrupt-token, and valid-semantic transformations. Mark non-text roles
explicitly inapplicable; for fixed-cap roles preserve the canonical token and
accept byte-cap precedence rather than introducing a second defect.

For every dynamic-OID role, strictly parse saved real output and freeze a
complete, ordered, unique role/position-to-contemporaneous-object mapping before
normalization. Replace only exactly verified OIDs. Uppercase, corrupt,
injected-valid-but-wrong, reordered, missing, and extra values remain raw or use
explicit hostile tokens and remain distinct across all 44 normalized rows;
merge-empty relations stay role-specific.

Run the full 129-case metadata collector under cleanup-bound original roots
measured at `(27 filesystem bytes, depth 4)` and `(108 filesystem bytes, depth
10)`, padded independently to one 700-byte/depth-16 governed parent shape.
Freeze separate execution, stimulus, trigger-receipt, raw-read, close-order, and
normalized-payload catalogs; exact cross-root rows and digests plus
configured-plan receipts must match, and a single-coordinate divergence mutant
must fail. Every configured plan also owns
an observed callback, target/path/role, phase/order, and effect receipt whose
raw-evidence identity hashes exactly the callback, metadata, stat, and exception
event fields and nothing else, with four single-coordinate mutants. Record that
17 historical configured-removal pair groups collapse into five complete
non-singleton configured-removed equivalence classes; do not call both counts
classes.

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
exact findings, three-phase verdict, stage and crypto ledgers, eligibility,
graph count, and selection, including empty values. Caller-supplied expectations
are prohibited. A replay-subset mutant must use successful independent trust and
the complete pipeline, then introduce an extra retained finding so subset
comparison is killed without fabricating work after a failed crypto check.

## Budget feasibility

| Level | Name | Cap | Projection | Projected use | Actual use | Disposition |
|---|---|---:|---:|---:|---:|---|
| per-file/partition/aggregate | exact name | number | number | percent | number | normal / >=85% review / >=90% stop |

Never compress semantics to fit a cap.

For the Issue #435 Reset31 exemplar, record matrix 4,200, protocol 4,200, core
oracle 4,200, repository oracle 14,500, template 600, ADR 550, route 5,800,
architecture/security 2,200, validator 28,000, seven-path aggregate 34,000, and
zero binaries. At or above 85 percent, record a readability/convergence review;
at or above 90 percent stop before C3/GREEN and decompose.

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
