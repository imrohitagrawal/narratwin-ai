# Adversarial Verification Playbook

This playbook is the repository-binding procedure for work classified as
security-, trust-, authority-, governance-, replay-, lineage-, or
reconstruction-sensitive. It creates no authority or runtime capability.

## Governing boundary

- Activation is always explicit. The reference protocol is `NONE`.
- Authority effect is always explicit. The reference protocol is
  `NO_AUTHORITY_EFFECT`.
- A green validator is documentation-quality evidence, not an accepted
  decision, trust root, active route, release, or production claim.
- The OWNER issue route selects whether work is sensitive. Automation verifies
  the declared route and matrix; it does not silently broaden authority.
- Uploaded material, matrices, freeze records, replay inputs, fixtures, and
  external outputs are untrusted bytes.

## Required artifacts

Every sensitive route must bind exact paths for:

1. a closed machine-readable invariant matrix;
2. a fixed focused test oracle authored before implementation;
3. a genuine RED implementation skeleton or old behavior;
4. three pre-GREEN technical review records;
5. an immutable closed RED-freeze overlay;
6. controlled mutation evidence; and
7. a quality-dispatch integration that cannot be bypassed by policy-only mode.

The semantic matrix and RED-freeze overlay are a joined contract. The semantic
matrix owns requirements. The overlay owns evidence identity only. Review URLs,
reviewer dispositions, blocker counts, and completion state never change the
semantic projection. The overlay must freeze the exact RED head, matrix and
test blobs, their byte hashes, and the independently calculated semantic hash.

## Closed-universe rule

Before implementation, declare every applicable dimension and every required
test class as finite ordered universes. The validator generates the Cartesian
product. A matrix is incomplete when a pair is missing, duplicated, silently
marked non-applicable, or removed by shrinking either universe.

The reference dimensions are:

- validation order;
- lifecycle state;
- temporal boundary;
- phase separation;
- cardinality and maximum limits;
- malformed input;
- deletion and corruption;
- reordering and duplication;
- substitution;
- cryptographic eligibility;
- graph/conflict eligibility and precedence; and
- reconstruction and replay.

Every Cartesian cell resolves to an independently frozen execution mode and a
serialized operational stimulus. Shared neutral payload content must not encode
the dimension, class, ordinal, expected outcome, digest, or registry position.
The parser is a closed typed boundary: unknown,
duplicate, forbidden, missing, wrongly typed, malformed, or oversized fields
produce an exact finding. Observe one exact-byte parser call for every real
fixture and require the canonical engine to receive the exact objects returned
by that call. Parser rejection propagates through the executor with zero engine
and crypto calls. The executor delegates valid fixtures to exactly one canonical
evaluator or reconstructor and returns that engine's object; a sentinel-only
composition test is insufficient. Negative and boundary cases
must differ in operational input and observed enforcement for every dimension.

The reference test classes are positive, negative, boundary, malformed,
deletion, corruption, reordering, duplication, substitution, and maximum
cardinality. A new applicable class returns the work to RED review.

## Mandatory processing pipeline

The exact stage order is:

```text
bounds
-> parse
-> schema
-> canonical identity
-> independent trust
-> authorization
-> graph/conflict
-> phase verdict
```

Each stage records a bounded call ledger. A rejection records the earliest
exact finding and makes every later count zero. Non-applicable stages require a
matrix row, reason, reviewer disposition, and exact no-call evidence. Silent
skipping is forbidden.

### Bounds

Check zero, one, N, N+1, individual bytes, aggregate bytes, depth, member count,
row count, candidate count, finding count, and retained-material count before
parse, hashing, cryptography, or graph work. Malformed evidence never excuses a
pre-work bound. Matrix bytes, freeze bytes, findings, retained materials, and
rows require exact N/N+1 evidence through both the public validator and the
route gate; helper-only evidence is insufficient.

### Parse and schema

Reject duplicate JSON members, invalid UTF-8, non-object roots, excessive
depth, unknown fields, missing fields, extra fields, wrong types, booleans used
as integers, invalid enums, path traversal, symlinks, nonregular files, and
binary input. Every nested tuple member and limit has an exact type/domain/range
case. JSON syntax failures return typed findings rather than leaking decoder
exceptions. JSON is strict and duplicate-free; a semantically equal alternate
serialization is still noncanonical when the contract binds storage bytes.
Before read, prove the target and every ancestor are non-symlinks, the resolved
path stays beneath the validated root, and the target is a regular text file;
include a socket or FIFO negative, not only a directory. Static local-read
allowlists name exact governed paths and independently bind every allowed
import, call, target, and command form.

### Canonical identity

Use a versioned domain separator and one documented canonical serialization.
Identity is calculated independently of caller-supplied identity. Missing,
extra, truncated, corrupted, reordered, duplicated, substituted, or cross-phase
material must not retain an earlier identity.

### Independent trust

Trust inputs come from a separately supplied trusted boundary. A candidate,
matrix, fixture, ambient state, cached verdict, or trust-on-first-use claim can
never create its own trust. Signature eligibility follows structure and
identity. Missing trust is `UNAVAILABLE`; invalid cryptography is `INVALID`.

Cryptographic fakes are narrow spies. They record and assert candidate identity,
signature, order, candidate count, phase, key/message, and result. Real public
vectors cover success plus mutation without private or signing keys.

### Authorization

Authorization follows successful independent trust and is phase- and
scope-specific. An unauthorized candidate never enters graph work. A trusted
candidate is not automatically authorized.

### Graph/conflict

Only structurally valid, identity-valid, independently trusted, authorized
candidates are eligible. Permutations produce the same graph result. Cover
forks, cycles, precedence, deletion, duplication, invalid competitors, and
substitution. `CONFLICTING` is reserved for multiple eligible candidates that
meet the exact conflict rule. Finding-code substrings do not select verdicts.

### Phase verdict

Historical, current, and acceptance phases are separate. Findings are exact
ordered tuples of stage, phase, code, and location. Historical and current
verdicts are compared for exact equality during replay. Membership, subset,
any-error, generic-invalid, generic-exception, and process-exit-only assertions
are insufficient.

## Genuine RED and review freeze

RED must collect and import successfully. It fails because the named behavior
is absent or the old behavior is reproduced. A missing module, syntax error,
fixture absence, generic exception, or command failure is not acceptable RED.

The sequence is strict:

1. commit route preflight only;
2. commit semantic matrix, fixed tests, protocol, ADR, and typed
   `NOT_IMPLEMENTED` skeleton;
3. execute focused tests and preserve exact failures;
4. obtain architecture, security/trust, and mutation/false-pass reviews from
   three distinct non-author identities;
5. resolve every credible finding without beginning GREEN;
6. create the immutable RED-freeze overlay only; and
7. begin small GREEN commits.

The focused test blob and semantic matrix blob do not change after RED. If a
new false-pass class appears, stop, preserve history, record an OWNER reset,
add a new genuine RED commit, renew semantic identity, repeat all three reviews,
and create a superseding freeze under explicit route authority.

## Controlled mutation

Every important enforcement claim names one mutation action and one kill test.
Allowed actions are remove, bypass, reorder, and replace. A mutation row is not
evidence by itself.

The named assertion identity owns the exact matrix findings, three-phase verdict,
stage and crypto ledgers, eligible candidates, graph count, and selection,
including exact empty tuples and nulls. The assertion derives these values only
from the frozen matrix. An adjacent ID-bearing equality, caller-supplied ledger,
or metadata-to-metadata comparison is not evidence.

Execute mutants in a disposable copy or clone. Never mutate the governed branch.
For each mutant record:

- source and exact anchor;
- replacement or removal;
- named test;
- expected exact finding and verdict;
- observed exact finding and verdict;
- killed or survived; and
- blocker class when it survives.

A mutant survives when the named assertion does not fail for the intended
reason. Killing a mutant through import failure, unrelated assertion, timeout,
or generic exception is an evidence blocker, not success.

## Blocker classes

`IMPLEMENTATION_BLOCKER` means the implementation violates or omits a semantic
contract. Correction returns to the smallest failing behavior.

`EVIDENCE_BLOCKER` means the claim is not discriminating or independently
proven: weak assertion, missing mutant, stale review, self-approval, ambiguous
finding, unavailable scan, or unbound evidence. Correction returns to the
matrix/test/review surface and may require renewed RED.

Both classes stop GREEN, publication, approval request, and merge. They remain
separate in checkpoints and review dispositions.

## Budget feasibility

Compute projected additions plus deletions for every file, partition, and
aggregate before implementation. Deletions grant no credit. Record each ratio.

- Below 85%: normal convergence review.
- At or above 85%: stop and record explicit readability and convergence risk.
- At or above 90%: no GREEN until an approved simplification, decomposition,
  cap redistribution, or bounded reset restores headroom.

Dense one-line code, collapsed assertions, broad helpers that hide outcomes,
and semantic compression used only to fit a cap are prohibited.

## Focused-to-full transition

The focused predicate requires the frozen matrix/test identity, three reviews,
zero implementation blockers, zero evidence blockers, every controlled mutant
killed, focused exact tests green, and the pure validator green under ordinary
and isolated system Python execution.

Only then run repository-wide validation. Full CI is integration confirmation;
it does not define semantic GREEN. Hosted jobs may execute in parallel. The
repository does not claim physical hosted-job ordering; the no-push checkpoint
and exact branch history enforce the transition.

## Checkpoints

Post a durable issue checkpoint after every major transition and material
correction. Include at least:

```yaml
issue:
slice:
base:
head:
tree:
diff_sha256:
branch:
worktree_state:
activation:
authorized_paths:
budgets:
completed_tests:
open_findings:
authority_links:
next_action:
last_updated:
```

Plain-language status must identify blocker, impact, and next action. Raw
internal tool or agent failures are not pasted into the durable record.

## Publication and closeout

Freeze base, head, tree, diff digest, history, paths, all budgets, activation,
and authority effect. Obtain fresh exact-head architecture, security/trust, and
mutation reviews. Then run complete local gates, publish the draft PR, reconcile
the body, pass protected checks, and obtain an eligible non-author GitHub
approval on the latest unchanged head.

Technical reviews and OWNER delegation do not replace GitHub approval. After a
protected merge, verify tree equivalence and merged-main gates before issue
closure and cleanup. Finalize repository-tracked status in the substantive PR;
routine merge facts belong in PR/issue comments, not a status-only successor.

## Stop and reset

Stop on authority, base, history, scope, path, budget, semantic identity,
matrix/test blob, freeze, review, check, scanner, expiry, activation, authority
effect, or prohibited-capability drift. Record exact head/tree/diff/charges and
the typed blocker before correction. Preserve history: never amend, rebase,
drop, rewrite, graft, replace refs, or force push.
