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
complete, ordered, unique seven-entry
role/row/column-to-contemporaneous-object mapping before normalization. Replace
only exactly verified OIDs at those coordinates. Real-validator reordered,
missing, duplicate, extra, swapped, uppercase, and valid-but-wrong injections
must stop at exact prefixes. Unmapped or wrong-coordinate known values remain
raw or use explicit hostile
tokens and remain distinct across the normalized rows; merge-empty relations
stay role-specific.

Run the full 129-case metadata collector beneath equal-width A/B slots in one
cleanup-owned platform temporary base. Add an 81-filesystem-byte/six-component
suffix only to B. Before any descendant mutation, derive complete immutable
OWNER-relative plans from stored cleanup-owner path/type/device/inode. Bind every
component/byte length, filler/final split, candidate bytes/depth, governed path,
exact 700-byte/depth-18 shape, and A/B relation. Prove feasibility and every
8..255 bound before one post-gate seam runs. Freeze all real seam calls in a
model-specific or complete nested transcript and filesystem receipt with unique
contiguous ordinals. Execute 7/8/255/256, infeasible, early-A/B,
zero/one/three-root, plan shape/type, wrong relation,
duplicate/missing/reordered/no-op/wrong-path/error, transcript, envelope,
owner-alias/symlink/inode, and receipt-coordinate mutants through the same
validator. Collect the constructed roots independently and freeze execution,
stimulus, trigger-receipt, raw-read, close-order, normalized-payload, and
configured-plan-receipt catalogs. Exact cross-root rows/digests must match; a
single-coordinate divergence mutant must fail.

Every configured plan owns an ordered raw receipt with callback arguments,
normalized target path/role/ordinal, close outcomes, inter-role before/after
effect, complete stat/exception evidence, argument type/count, event ordinal,
and live-descriptor/open-event ordinal. Instrument discovery and reader
operations; emit discovery only for actual work and bind the exact custom/system
source. Preserve discovery as a distinct operation graph, including ancestor
descriptor ownership, reader use, and reverse cleanup across
discovery→reader→discovery. Do not flatten or relabel those events. The `dot_git`
handoff must carry the exact prior discovery-root path/type/device/inode record.
Bind exact typed pre-work findings to missing and wrong-role/path/type/device/inode
handoff mutants. Separately bind call-site object identity with
`parent_record is discovery.record` and a source-copy mutant; do not claim
reader-level detection of a value-identical copy or introduce an opaque token.
All stop before `.git` component, Git-object, or process work; device/inode
mutants may first traverse and re-stat the root record.
Freeze exact findings at `root`: `ACP.GIT_METADATA.CONTAINMENT` for
missing/wrong-role/wrong-path, `ACP.GIT_METADATA.WRONG_TYPE` for wrong-type, and
`ACP.GIT_METADATA.IDENTITY_CHANGED` for wrong-device/wrong-inode.
Source-copy call-site identity failure is `ACP.GIT_METADATA.CONTAINMENT/root`.
Record all five I/O callbacks (lstat/open/fstat/read/close) and require zero
`.git` work on handoff rejection. Compose wrong-type+wrong-device and freeze
`ACP.GIT_METADATA.WRONG_TYPE/root` precedence.

Parse exactly eight raw fields plus stored identity/index with exact types/caps,
closed role/path grammar, role-local event identity, callback-specific
argument/result grammar and bijection, `dirfd-none|dirfdOpenOrdinal-N` prior live
descriptor provenance, portable flags, bounded reads, causal
metadata/stat/error pairing, derived fields, guarded conversions, and typed
precedence. Allow exactly one initial filesystem-root anchor open per role: it
must be first, use `dirfd-none`, target the normalized outer ancestor, require
directory/no-follow flags and a directory result, omit prior lstat/fstat, and
close last in reverse cleanup. All later opens/uses require same-path lstat/fstat
identity, kind/flags/fstat relational consistency, positive reads→zero
EOF→post-lstat→reverse close, and exact event source/count/order. The inter target
must bind to the actual successful-open row's role/path/roleOrdinal/eventOrdinal,
never a relation-table path or `-1`. Trigger/terminal bind their actual raw
ordinals/paths with no later work after terminal. Non-inter target/path and ordinals derive only from the
decisive raw row, never a hardcoded role or global ledger selection. Require the
exact ordered seven-key inter-role arm and a closed
relation. `afterRole` uses discovery phases such as
`linked_git_dir`/`common_dir`; `roleEvents` use reader roles
`backlink`/`commondir`; projected target is separate. Inter receipts append
exactly one trailing auxiliary marker
`interReceiptOrdinal-N:afterRole-X`. Parse it separately, never as a reader role;
all preceding entries remain `ordinal:reader_role`. Freeze
missing/duplicate/nonterminal/wrong-ordinal/wrong-afterRole/reader-reclassification
mutants.
The actual raw terminal row—not the seam assertion or schedule—must carry a
label-free stored-parent identity/type mismatch bound to target role/path.
Execute terminal-success and terminal-path-swap mutants without reading case,
expected-finding, or declared-terminal inputs. Bind the raw-observed parent role
as well as path/type/device/inode; execute a wrong-parent-role/same-path mutant
and prohibit schedule-derived role. Receipt index is location/cap input only:
the parser cannot look up
execution ID, case, expected custom operation, plan, or per-case schedule. One
generic closed label-free grammar derives semantics. Parsed output owns actual
observed role/path/role ordinal/callback ordinal and projection. Project only
validated output. Bind by reparse, raw identity, stored observations, stored
projection, then plan. Freeze a separate binder-only index→expected
actual `executionEvidenceIdentity` SHA-256 of `(mode,payload_sha,role_traces)` and
exact role/terminal schedule table to kill
same-plan conventional/linked cross-swaps. Include expected raw-evidence identity,
observed-four tuple, and projection, or their combined canonical binding
identity. Cross-swaps feed donor raw+SHA+observed4+projection with recipient
execution evidence/index only when those coordinates differ. Freeze seven
complete-binding donor swaps that fail `executionEvidenceIdentity`, and the four raw-distinct
recipient-ID hybrids 8→9, 11→13, 12→14, and 18→19 that fail
`rawEvidenceIdentity`. Record pairs 1/2, 16/17, and 20/21 as evidence-equivalent
below execution identity, without a false raw-identity claim. The parser cannot
read the table. Continue
without labels, outcomes, global selection, fallback, or
synthesis. Freeze readable single-coordinate and composed mutants for every
raw/discovery/callback/event/role/schedule/path/descriptor/handoff,
metadata/stat/error/source/count/order/read/EOF/post-lstat/reverse-cleanup,
anchor-missing/duplicate/reorder/path/dirfd/flags/result/prior-fstat/final-close,
kind/flags/fstat/inter-terminal/no-later-work/decisive-row,
stored-observation/projection/plan
coordinate. Only stale identity preserves stale SHA; every row executes through
the same parser/binder and returns its exact typed location. Freeze configured
mutant fields for `mutantId`, `executionId`, exact first coordinate/location,
complete changed-binder-layer set, complete changed-raw-field set, operation, and
`rawIdentityAction`; a coherent multi-field change cannot masquerade as one
nominal coordinate. `executionId` may appear only as a non-authoritative
external test-catalog display/index label, never binder input, and cannot influence parsing or binding. Freeze all 22 actual
binding hashes and a case-label/order permutation non-influence proof. Keep schedule-owned ordinal and composed mutants in separate
explicit catalogs with their own counts/digests. Add a fixed-raw
permutation mutant: permuting execution order and per-case expectations leaves
the parse result unchanged and returns an exact binder mismatch. Record that
seven complete-binding execution-evidence-identity swaps and four raw-distinct recipient-ID
hybrids also fail only at the binder. Record that
17 historical configured-removal pair groups collapse into five complete
non-singleton configured-removed equivalence classes; require every pair to be
wholly and uniquely contained by one observed class, and kill a cross-class
mutant with an exact typed finding at the derived pair index. Do not call both
counts classes.

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

<!-- issue-435-reset47-red-snapshot:sha256=6a6c27c219edeb9e47008ea434321cd2ec4510c0923ba7bbd19b9aa807e07f47 -->
For the Issue #435 exemplar, label immutable evidence
`C2R48_RED_SNAPSHOT_ONLY`; never present it as mutable current GREEN truth. The
independently owned, non-self-referential snapshot catalog binds fixed base
`a6284f7d8f1a14ef4c9a99493d6b06046505f20c`, exact C1R48 parent
`d30fbccde228f713860d5592df1f6230953a30b1`, snapshot schema/version, exact
ordered rows, row count, and rows SHA-256. Record the actual C2 commit, tree, and
seven blobs only in the external checkpoint and subsequent freeze.

Exact use is matrix 4,509/5,500 (81.98%); protocol 5,525/12,000 (46.04%);
core 4,373/5,000 (87.46%); repository 16,999/19,000 (89.47%); template
408/600 (68.00%); ADR 417/550 (75.82%); playbook 584; validator
26,897/40,000 (67.24%); architecture/security 1,409/2,200 (64.05%); route
4,509/5,800 (77.74%); and seven-path aggregate 32,815/45,000 (72.92%).

The core, repository, validator, and aggregate evidence stays independently
reviewable; repository, validator, and aggregate reviews PASS. Independent
semantic literals and catalog assertions, with bounded helpers, keep each use below 90 percent with
no semantic compression. Further growth requires a fresh review before growth
continues. These values are immutable C2R48 history, not current GREEN truth.

Define a separate dynamic current-head proof that validates its frozen catalog
before either evidence source and accepts no caller-supplied current uses.
Tree-to-tree Git argv is
`/usr/bin/git --no-pager --no-replace-objects --no-optional-locks
--no-lazy-fetch -c protocol.allow=never -c core.commitGraph=false -c
core.fsmonitor=false -c log.showSignature=false -c fsck.skipList=/dev/null diff
--no-renames --ignore-submodules=none --no-ext-diff --no-textconv
--diff-filter=A --numstat
a6284f7d8f1a14ef4c9a99493d6b06046505f20c HEAD -- <seven-frozen-paths>`. Its fresh environment and exact
result bind integer-zero status, empty byte stderr, exact byte stdout, NUL-free
ASCII, seven terminal-LF rows, three tab fields, canonical counts, fixed-base
absence, and zero deletions. Git output paths are independently frozen in
lexicographic order as "docs/ADR/0064-adversarial-convergence-protocol.md",
"docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
"docs/governance/adversarial-convergence-invariant-matrix-v1.json",
"docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
"scripts/quality/issue435_adversarial_convergence.py",
"tests/unit/test_issue435_adversarial_convergence.py", and
"tests/unit/test_issue435_adversarial_convergence_repository.py".
Independently read only the exact contained
allowlist through no-symlink ancestors/leaves, regular fstat identity, and
bounded descriptors: 4,194,304 bytes per item and 16,777,216 total. Reject
FIFO/block/unbounded reads, non-bytes, NUL, invalid UTF-8, CR, or malformed line
endings and count LF records plus a final unterminated record exactly. Each source derives seven
uses, route/architecture/validator partitions, aggregate, binary-zero state,
ratios, review set, and strict below-90 results. Both remain under caps before
commit; clean immutable heads require exact equality. Catalog failure is first
with zero Git, raw reads, or later work. Mutants kill fsmonitor or HEAD omission,
stale/current substitution, threshold drift, hostile raw bytes, Git/raw
mismatch, path drift, and review-set drift before intentional RED. The
whole-line start marker encodes SHA-256 of raw
UTF-8/LF bytes strictly between the marker lines, including exactly one terminal
LF and excluding both markers.
<!-- issue-435-reset47-red-snapshot:end -->



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
