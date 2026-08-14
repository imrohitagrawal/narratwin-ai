# Authority Reconciliation Architecture Reset Proposal

## 1. Document control

| Field | Value |
|---|---|
| Status | `RESET_PROPOSAL_UNAPPROVED` |
| Issue | `#427`, under parent `#426` |
| Repository | `imrohitagrawal/narratwin-ai` |
| Existing approved base | `f2a32b8c022c015dfa4e87c700fbfe1ed0d85183` |
| Current local committed head | `2f2779d7a79daf3ccbe3cab441b5a3b5596142c0` |
| Purpose | Replace an oversized specification attempt with a bounded architecture kernel and serialized child graph |
| Authority effect | None |

This document is a reset proposal, not the accepted Issue #427 phase
specification, an implementation route, an authority decision, a manifest, or
an active program route. It grants no permission to implement, push, open or
merge a pull request, activate a provider, use credentials, spend money,
generate or publish media, deploy, release, or claim production or commercial
readiness.

The previous 2,145-line draft remains available in local Git/worktree history
by its recorded SHA-256
`e2d4e7761fe765619ae1a85252debaf950d3c8d29f9de308aa5106c31fe1f430`.
It is design exploration only and is not silently accepted by this reset.

Issue #427's two-repair stop rule has been exceeded. Before this proposal can
replace its contract, the repository OWNER must approve an exact Issue #427
rewrite or a replacement issue route. The pending route-and-command amendment
request in comment `5271427782` is not approval.

## 2. Why the reset is required

Issue #427 originally needed a non-activating specification for three core
records and their authority boundaries:

1. `MasterProgramAuthorityDecisionV1`;
2. `Cut1AuthorityManifestV1`;
3. `ActiveProgramRouteV1`.

Successive correction rounds expanded the same artifact into evidence capture,
human signature trust, key rotation, historical registry reconstruction,
checkpointing, an offline authority kernel, an audit coordinator, a wire
protocol, concurrency control, projection publication and closeout recovery.
Those are separately testable subsystems with different owners and failure
modes. Keeping them in one specification made review the primary requirements
discovery mechanism and repeatedly created new cross-contract contradictions.

The reset applies three rules:

- keep the cross-subsystem authority invariants small and stable;
- assign every detailed protocol to exactly one bounded child;
- never make a downstream child's unresolved design a prerequisite for
  approving the architecture kernel.

## 3. Decision requested from the OWNER

Approve one of these mutually exclusive routes:

### 3.1 Preferred route: rewrite Issue #427

Rewrite Issue #427 as the architecture-kernel and delivery-decomposition child
defined in Sections 4 through 10. It remains documentation-only and
non-activating. After it closes, create the serialized children in Section 7.

### 3.2 Alternative route: close Issue #427 unmerged

Preserve its review history as an unsuccessful design exploration, close it
without completion, and create a new architecture-kernel issue from parent
Issue #426. The new issue must have its own branch, base, paths, budget, preflight,
review conditions and expiry.

No implementer chooses between these routes. Until the OWNER chooses, the
state is `BLOCKED_OWNER_REWRITE_DECISION`.

## 4. Architecture kernel

Only the following invariants are shared by every later child.

### 4.1 Authority sources

- Issue prose, comments, branch names, files, tests and CI results are evidence
  inputs; none independently activates authority.
- An accepted decision is the only record that can select the current manifest.
- An active route must reference the accepted decision and selected manifest.
- Every authority-bearing object is repository-bound, content-addressed,
  versioned, immutable after acceptance and scoped to one repository.
- At most one current decision/manifest pair and at most one active writer route
  may exist for a governed program generation.
- Unknown, missing, stale, expired, revoked, conflicting, gapped or mismatched
  authority fails closed.

### 4.2 Separation of concerns

- Candidate records describe proposed state.
- Evidence records describe observed facts.
- Decisions select candidates after required evidence and human authority.
- Projections are derived views and never create authority absent their inputs.
- Audit records describe attempts and outcomes; audit delivery does not by
  itself authorize the attempted action.
- Closeout records prove administrative completion; they do not retroactively
  authorize execution.

### 4.3 Execution fencing

- No route may mutate governed state before activation.
- Activation selects one writer generation and fences every earlier generation.
- Every authoritative mutation uses compare-and-swap or an equivalent
  single-writer guard bound to the current generation.
- A stale writer, callback, lease or route can provide reconciliation evidence
  but cannot mutate current authority.
- Expiry or revocation immediately fences execution authority while preserving
  an administrative path to record rejection, supersession or closeout.

### 4.4 Evidence semantics

- Implementation, technical verification, independent review, human authority,
  availability and operating effectiveness remain separate states.
- Evidence identifies its subject, producer, observation time, validity window,
  source and limitations.
- Evidence for different subjects or lifecycle phases cannot be substituted.
- Durable acceptance evidence must be reconstructable for the lifetime of the
  authority it supports.
- Missing audit delivery fails the affected authority transition closed but
  does not convert an evaluated failure into success.

### 4.5 Non-activation

The architecture-kernel child may define names, invariants, child boundaries,
review roles and stop conditions only. It does not serialize accepted candidate
objects, implement a kernel, create signing keys, add workflows, contact GitHub
or providers, or activate a route.

## 5. Core contract responsibility

The architecture-kernel child defines only the minimum stable identity and
linkage of the three core records. Closed field-level schemas are delivered by
the owning schema child, not invented here.

| Contract | Stable responsibility | Explicitly deferred detail |
|---|---|---|
| `MasterProgramAuthorityDecisionV1` | identifies the governed program and generation, selects one manifest candidate, records decision action and validity, and binds required evidence/authority references | canonical JSON schema, transition receipt layout, evidence capture and storage |
| `Cut1AuthorityManifestV1` | binds the exact Cut 1 authority values required by the master controller and names blocked capabilities that still need separate authority | provider execution, credential, spend, media acceptance and artifact production |
| `ActiveProgramRouteV1` | bounds one issue/branch/PR/base/path/budget/test/reviewer route, names predecessor generation and prohibited capabilities, and carries execution deadline | projection algorithm, CAS persistence, audit wire protocol and administrative closeout evidence transport |

The schema child may strengthen field validation but may not weaken or change
these responsibilities without a new architecture decision.

## 6. State-model boundaries

The architecture kernel fixes semantic phases, not serialization details.

### 6.1 Decision and manifest pair

```text
PROPOSED
→ REVIEWED
→ OWNER_APPROVED
→ MERGED
→ ACCEPTED_CURRENT
→ SUPERSEDED | REVOKED | EXPIRED
```

`REJECTED` may be reached before acceptance. `UNVERIFIED` and `CONFLICTING` are
evaluation outcomes, not persisted lifecycle transitions.

### 6.2 Route

```text
DRAFT
→ REVIEWED
→ OWNER_APPROVED
→ PREDECESSOR_VERIFIED
→ ACTIVE
→ MERGED
→ CLOSED
```

Pre-merge routes may become `REJECTED`, `SUPERSEDED` or execution-expired.
Once execution authority expires, no governed mutation is permitted, but an
already merged route retains an administrative closeout path. The route-schema
child must define every legal edge and its exact evidence.

### 6.3 Bootstrap

Bootstrap is a one-time bounded authorization for creating the first decision,
manifest and route implementation. It is not modeled as an ordinary active
route and it terminates after closeout. Its detailed two-stage approval and
descendant controls belong to the bootstrap child.

## 7. Serialized delivery graph

Every child below receives its own OWNER-approved issue, branch, PR, exact
predecessor, allowed paths, budget, tests, reviewers, expiry and closeout. No
child may absorb another child's responsibilities merely to resolve review
feedback.

| Order | Child | Delivers | Must not deliver | Required specialist review |
|---:|---|---|---|---|
| 1 | `A — Core schemas and state matrices` | closed schemas for the three core contracts; exhaustive legal/illegal lifecycle matrices; canonical serialization and compatibility | evidence capture, audit service, GitHub acquisition, runtime activation | Principal Architect; Principal Test Engineer |
| 2 | `B — Evidence and trust` | evidence subjects/phases, capture envelope, producer trust, freshness, key rotation/revocation and reconstruction rules | route CAS, audit coordinator, provider/runtime authority | Security Architect; Identity/Trust reviewer; Test Engineer |
| 3 | `C — Projection, CAS and bootstrap` | current-set and route projections, generation fencing, bootstrap declarations, atomic state transitions and recovery | external audit transport, performance claims, production activation | Principal Architect; SRE; Test Engineer |
| 4 | `D — Audit and closeout coordinator protocol` | attempt audit, reservation/evaluation/commit/lookup lifecycle, terminal receipts, rollover, projection publication, and administrative closeout evidence transport/recovery | authority-policy decisions, GitHub capture, route lifecycle decisions, hosted deployment | SRE; DevOps; Security; Performance/NFR |
| 5 | `E — Historical reconciliation` | exact source inventory, stale-source discovery, checkpointing, bounded replay and drift handling | trust-root creation, route activation, product behavior | Security; SRE; Repository governance reviewer |
| 6 | `F — Integrated offline kernel and oracle` | composes A–E, validates exact request matrices, proves false-pass mutations and produces non-activating candidate projections | hosted service, workflow, credentials, provider, spend, media, deployment or release | Architecture; EM/DevOps; Test/SRE/NFR; Security |

Dependencies are strictly `A → B → C → D → E → F` unless an approved child
spec proves two adjacent children can be independently developed against a
frozen interface. Integrated authority remains unavailable until F closes.

## 8. Invariant and ownership matrix

Every row has one owning child and one required proof class. Later child specs
must expand their rows into positive, negative and mutation cases before code.

| ID | Invariant / false-pass prevented | Owner | Required proof |
|---|---|---|---|
| `AK-001` | no issue/comment/file/check independently activates authority | A | closed schema plus negative fixture |
| `AK-002` | at most one current decision/manifest pair per generation | C | 32-writer CAS test and state-machine proof |
| `AK-003` | at most one active writer route per generation | C | concurrency, stale-writer and split-brain tests |
| `AK-004` | accepted objects are immutable and successors are hash-linked | A | canonicalization and mutation tests |
| `AK-005` | missing/stale/expired/revoked/conflicting evidence fails closed | B | boundary and hostile evidence fixtures |
| `AK-006` | evidence cannot move between subjects or lifecycle phases | B | substitution and mixed-subject tests |
| `AK-007` | producer identity has a noncircular independently trusted root | B | trust-bootstrap and fabricated-signer tests |
| `AK-008` | key rotation cannot validate new captures with retired keys | B | before/at/after revocation tests |
| `AK-009` | old accepted evidence remains reconstructable for its required lifetime | B | rotation and historical reconstruction drill |
| `AK-010` | bootstrap authorizes only bounded descendant changes | C | exact-base/path/budget/history mutations |
| `AK-011` | bootstrap cannot self-authorize or survive its closeout | C | genesis and termination state tests |
| `AK-012` | every legal transition has one exact actor, guard, effect and recovery | A | exhaustive state-machine enumeration |
| `AK-013` | audit describes every attempt without becoming an authority source | D | success/failure/audit-injection tests |
| `AK-014` | audited evidence set is exactly the set evaluated | D | omission/addition/substitution tests |
| `AK-015` | a reservation is single-use or returns byte-identical idempotent replay | D | concurrent duplicate-evaluation tests |
| `AK-016` | terminal audit outcome is recoverable after lost response or crash | D | lookup/replay/expire recovery tests |
| `AK-017` | successful validation without projection is representable | F | operation/output-union tests |
| `AK-018` | every operation and target state has one exact ordered input set | F | table-driven missing/extra/reorder tests |
| `AK-019` | historical deletion, fork or gap cannot reset a high-water mark | E | delayed-delete/fork/gap fixtures |
| `AK-020` | bounded replay can checkpoint without authorizing at a historical head | E | checkpoint/catch-up/current-head tests |
| `AK-021` | route execution expiry never prevents administrative closeout | C | deadline/merge/closeout state tests |
| `AK-022` | no child activates runtime, provider, credential, spend, media or release capability | F | exact prohibited-capability gate |
| `AK-023` | administrative closeout evidence can be delivered or recovered after response loss without becoming an authority source | D | receipt transport, lookup and crash-recovery tests |

Rows may be split into more specific child rows. They may not be silently
deleted, reassigned to “future work” or claimed by a marker-only test.

## 9. Planning and review gates

### 9.1 Before each child is approved

The child card must contain:

- objective, positive claims, non-goals and prohibited claims;
- complete child-specific invariant/false-pass matrix;
- exact contract inputs and outputs;
- dependency hashes and explicitly deferred interfaces;
- RED-test or other evidence mapping for every matrix row;
- exact local and hosted commands proven compatible with the branch family;
- path and charged-line budgets sized for one reviewable subsystem;
- stop rule after one correction wave reveals a new defect class.

### 9.2 Review wave

One author freezes the artifact and records its repository head, SHA-256, byte
count and line count. No edits occur while reviewers read it. Findings are
consolidated by defect class and adjudicated once as `ACTIONABLE`,
`MISREAD`, `TRADE_OFF`, or `NOISE`.

One correction wave is permitted. If the correction creates a new subsystem,
changes the definition of done or produces a second new blocker class, the
child stops and returns to its parent. It is not patched repeatedly.

### 9.3 Review sequencing

- Architecture reviews the kernel and subsystem boundaries first.
- Security reviews Child B and the integrated trust boundary, not incomplete
  audit or performance mechanics.
- Performance/NFR reviews Child D only after its workload, concurrency and
  resource profiles are executable.
- Integrated review occurs once in Child F after A–E are individually accepted.

## 10. Acceptance criteria for this reset proposal

This proposal passes its architecture planning gate only if an independent
reviewer confirms all of the following:

1. the architecture kernel contains only cross-child invariants;
2. every detailed protocol has exactly one owning child;
3. the delivery graph is acyclic and each child is independently reviewable;
4. the final blockers from the prior draft map to explicit matrix rows and
   owning children;
5. security and performance review are scheduled at appropriate maturity;
6. no unresolved downstream protocol is required to approve this reset;
7. the proposal remains non-activating and names the missing OWNER authority.

Architecture `PASS` on this proposal is not Issue #427 completion. It means the
decomposition is suitable to present to the OWNER as a contract rewrite.

## 11. Current stop conditions

Stop immediately on:

- treating this proposal or chat approval as repository execution authority;
- pushing, opening a PR or merging before the OWNER approves the rewritten
  route and exact quality commands;
- adding the two paths requested by unapproved comment `5271427782`;
- continuing the former monolithic specification as if this reset had not
  superseded it locally;
- moving a protocol between children during review without updating the
  dependency graph and matrix;
- starting security or performance certification against an incomplete child;
- claiming any hosted, production, SLA or commercial readiness.

## 12. Next action after architecture review

If the architecture review passes, post an OWNER amendment request containing:

1. the chosen rewrite or replacement route from Section 3;
2. the exact frozen hash, bytes and lines of this proposal;
3. the reduced Issue #427 acceptance criteria;
4. the six serialized children and their dependency order;
5. the exact path/budget/quality-command correction;
6. the statement that prior draft review evidence is historical only.

If the architecture review blocks, update this decomposition once. A new
protocol-level demand is assigned to its owning child rather than expanded in
this proposal. A second new architecture blocker stops the reset and returns to
the OWNER without another review loop.
