# Issue #459 T01/T02 Entry-Gate Review

Status: `APPROVED_T01_T02_EXACT_HEAD_2CFCED8`

Scope is limited to the fixed-base preflight, exact route/dispatcher, closed
evidence schema, stimulus-only corpus, literal test-owned RED oracle, process
ledgers, and independent review. It does not review or authorize product,
provider, asset, media, audio, human-study, deployment, release, or acceptance
behavior.

## Reproduced findings before candidate review

| Finding | Classification | Disposition |
|---|---|---|
| Exact Issue #459 route was absent | REQUIRED_CONTRACT | Corrected by fixed branch/base/path/budget route and mutation tests |
| Per-path and byte budgets were prose-only | REQUIRED_CONTRACT | Corrected by executable line and byte tables |
| Accepted grounding/narration is Meera-only | REQUIRED_CONTRACT for T05/T06, not T01/T02 | Preserved as a stop; no Raj/Myra substitution |
| Issue #368 retains audio ownership | REQUIRED_CONTRACT for T05 | Preserved as a stop pending reviewed handoff |
| Raj/Myra derivatives lack ready provenance evidence | REQUIRED_CONTRACT for T03/T06 | Preserved as a stop |
| Human study and provider activation lack authority | REQUIRED_CONTRACT for acceptance/provider work | Preserved under #432/#449 |

## Exact-head review record

Candidate `81183ad4d229e257cc2924c8b7f4916d078cf1b4` was reviewed independently
for requirements/governance, security/quality, and topology/acceptance. No
CRITICAL_BLOCKER was reproduced. The reviewers reproduced these consolidated
entry-scope REQUIRED_CONTRACT roots:

| Root | Reproduction | Correction disposition |
|---|---|---|
| Incomplete source freeze | incorporated PRD/traceability/architecture/API/data/security/observability/human/provider leaves were absent | all direct leaves added to prose plus offline file-hash enforcement and test-owned constants |
| Thin schema/RED coverage | compound metric, lineage, approval, media, provider, accessibility and observability leaves lacked mutations; authority digests were mislabeled | closed schema expanded; project facts/live binding correctly named; exact synthetic approval/currentness bindings added; every frozen leaf receives a literal stimulus |
| Six-cell/readiness ambiguity | bootstrap helper ignored `allOf`; Raj/Myra target cells looked passed/authorized while dependencies said not ready | explicit six-key schema clauses are interpreted in a test-owned assertion; every cell is `SYNTHETIC_RED_TARGET_NOT_EXECUTED`, derivative authority is false, Cut 1 remains blocked |
| Rename/copy false acceptance | synthesized in-allowlist `R100`/`C100` collapsed to the required path set | exact route now rejects rename/copy statuses without weakening global copy detection |
| Incomplete route mutations | only one missing path and production-owned caps were indirectly exercised | every Issue #459 missing path, extra path, line cap, byte cap, aggregate cap, source drift, editable-authority drift, branch/base and rename/copy boundary is test-owned |
| Stale current-state ledger | STATUS and stage plan simultaneously called Issue #16 current/future and #459 current | #16/#456 wording made explicitly historical/completed; #459 is the only current Lane A entry route |

The correction head must independently reproduce green bootstrap/policy checks
and exactly 136 future assertions failing only against
`CUT1.ENTRY.NOT_IMPLEMENTED`. Any new reproduced CRITICAL_BLOCKER or entry-scope
REQUIRED_CONTRACT keeps this review pending and blocks GREEN implementation.

Independent review of correction candidate
`8dd002589d45b41205a80dc004e7e6480bec901f` closed the earlier source,
topology, route, readiness, and ledger roots, then reproduced two narrower
`REQUIRED_CONTRACT` roots. First, mutable incorporated repository authorities
needed accepted-base digests and several observability, approval/dependency,
rights, configuration, and acceptance leaves lacked literal mutations. Second,
self-authorship, replay, and approval checksum findings depended on magic values
rather than relations available to the materialized-stimulus-only executor.

The pending final correction binds the four mutable authorities to their
accepted-base bytes, expands the stimulus-only corpus to 136 test-owned cases,
and defines reviewer/author independence, single-use approval state, immutable
request framing, and canonical approval-digest framing. Focused bootstrap,
route/dispatcher, lint, type, guardrail, diff, budget, and policy checks are
green. Full RED has one bootstrap pass and exactly 136 future failures, each
showing only typed `CUT1.ENTRY.NOT_IMPLEMENTED`, with no setup or collection
error. These are candidate observations, not an approval; independent review
must reproduce them on the committed exact head before T03 or any GREEN work.

Review of `77ebfc3218a003a06f7b43098624c30f2b43bf4e` reproduced a coherent
recomputation/currentness root: candidate artifact and approval fields could be
rewritten together, valid hashes recomputed, and self-asserted currentness left
true without an external anchor. Configuration, provenance, and deletion
references had the same valid-substitution weakness, and repeated synthetic
digests did not discriminate ordered fields. That head is rejected. The next
candidate must bind distinct synthetic fields through the frozen evidence
register, prove ordered framing, and include coherent-forgery, revoked,
expired, and pre-artifact stimuli before independent exact-head review.

## Final exact-head disposition

Requirements/governance, security/quality, and topology/acceptance reviewers
independently pinned
`2cfced8034b207e2ad12c450d5281d8446060a85`. Each reported no reproduced
`CRITICAL_BLOCKER` or T01/T02 `REQUIRED_CONTRACT`. They reproduced:

- the fixed base, exact 16-path topology, no rename/copy, 1,956/4,300 aggregate
  charge, every per-path and byte cap, 25 repository source hashes, four
  accepted-base hashes, and five editable GitHub authority hashes;
- six unique non-executed cells, distinct ordered primary bindings, correct
  C1-M10 repeat equality, fixed provider configuration, and the frozen evidence
  register across provider, identity, lineage, rights, and artifact projections;
- schema-valid coherent artifact/approval and provenance/deletion substitution,
  attacker-recomputed outer-register rejection, and relational self-author,
  replay, revoked, expired, pre-artifact, and swapped-order cases;
- 83 route/dispatcher passes, one bootstrap pass with 136 deselections, exactly
  136 authentic future failures against typed `CUT1.ENTRY.NOT_IMPLEMENTED`,
  direct-head hosted-policy parity, guardrails, diff checks, and a clean head.

T01/T02 may complete. This approval creates no artifact, product, provider,
media, human-study, hosted-freeze, merge, release, or Cut 1 acceptance evidence.
T03/T05/T06 and later remain governed by the derivative, Meera-only lineage,
Issue #368, #432, #449, legal, accessibility, exact-artifact, and hosted-parity
stops in the preflight. No GREEN behavior is included in the reviewed head.

## T04 controller convergence record

Independent contract and security/governance reviews of candidate
`729c1dd3bb0ad1e5fa500cf40e8d40b6bea86352` reproduced one consolidated
`CRITICAL_BLOCKER`: the evaluator closed mapping keys but not scalar types and
domains. Schema-invalid upper ratios, negative timing/count values and a
fractional integer returned no finding; malformed JSON-shaped leaves could
raise instead of returning one bounded finding; and invalid non-secret
observability IDs could pass. The exception symptoms are `DUPLICATE` instances
of that scalar-boundary root rather than separate defects.

The controller owner corrected the smallest responsible boundary before any
checkpoint push or T03 activation. The correction adds pure pre-hash scalar
type and ID validation, rejects otherwise false-accepted metric domains,
guards non-mapping cells, and preserves the frozen semantic precedence.
Regression evidence covers every scalar leaf with JSON object substitution,
the reproduced metric/domain values, invalid observability IDs, non-mapping
cells, unhashable artifact values, deterministic repeats, and at-most-one
finding. Focused evidence is 696 passing tests; policy-only quality, full
quality, Ruff, mypy, and the exact route remain green. The correction remains
pending independent review at its new committed exact head.

The full-history Gitleaks result contains six older findings: none is introduced
by the `c1a08396..729c1dd3` increment. This is classified `OUT_OF_SCOPE` for the
T04 implementation while remaining explicit hosted-baseline debt; it is not
silently converted into controller acceptance evidence.

Re-review of `eef7a3569fe1adf600755f8144b88f44e7f39bbf` closed the first
reproductions and then found one narrower `CRITICAL_BLOCKER` at the same schema
boundary: Python accepted ISO week/basic timestamp lexemes that the frozen
RFC3339 schema rejects. An extreme JSON integer also raised during float
finiteness conversion; that exception is a `DUPLICATE` symptom. The correction
adds an explicit RFC3339 lexical guard and treats integers as intrinsically
finite while applying `math.isfinite` only to floats. Six exact regressions join
the full scalar suite, bringing focused/frozen evidence to 702 passes.

The canonical repository guardrail then reproduced one separate
`REQUIRED_CONTRACT`: a new backend authority boundary requires an ADR. Issue
comment `5452170084` adds exactly ADR `0068` without expanding behavior or the
2,000-line implementation budget. The executable route binds its 260-line and
32,000-byte caps inside the existing cumulative maximum. This correction is
pending independent exact-head review and committed-head guardrail evidence.
