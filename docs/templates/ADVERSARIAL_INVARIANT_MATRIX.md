# Adversarial Invariant Matrix Template

Use this template for one separately authorized slice. Do not copy the
framework's ACP-T01–ACP-T12 self-test corpus as the slice threat model. The
slice owner supplies every domain threat, invariant, stimulus, expectation,
lifecycle/trust rule, mutant, budget, review role, and acceptance threshold.

## Authority

| Field | Required value |
|---|---|
| Issue / OWNER amendment | Exact durable URL |
| Base / branch | Exact Git identities |
| Activation / authority effect | Explicit values; default `NONE` / `NO_AUTHORITY_EFFECT` |
| Allowed paths and caps | Exact paths; additions plus deletions; no wildcard authority |
| Non-goals | Runtime, provider, network, credential, spend, deployment, and release posture |
| Stop rule | Rescope triggers, correction-wave count, review disagreement, and budget thresholds |

## Trust boundaries and assets

| Boundary ID | Untrusted source | Protected asset or decision | Allowed operation | Failure behavior | Evidence owner |
|---|---|---|---|---|---|
| TB-... | ... | ... | ... | typed fail-closed result | ... |

List filesystem, JSON/document, expectation, execution ledger, review receipt,
Git identity, provider, model, user-data, and external-source boundaries that
actually apply. Mark absent boundaries as non-goals; never silently omit them.

## Closed slice threat model

| Threat ID | Abuse case | Boundary | Invariant IDs | Test IDs | Residual risk owner |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

Freeze the exact ordered IDs before implementation. Adding an ID later is a
contract change, not a correction.

## Invariants

| Invariant ID | Threat ID | Stage | Complete predecessors | Applicability | Lifecycle | Exact rule | Evidence class |
|---|---|---|---|---|---|---|---|
| ... | ... | `BOUNDS`…`PHASE_VERDICT` | ... | ... | ... | ... | test/source/human-only/non-goal |

Processing order is fixed:

1. `BOUNDS`
2. `PARSE`
3. `SCHEMA`
4. `CANONICAL_IDENTITY`
5. `INDEPENDENT_TRUST`
6. `AUTHORIZATION`
7. `GRAPH_CONFLICT`
8. `PHASE_VERDICT`

After a rejected stage, later callbacks are forbidden. Record them as
`NOT_REACHED` with callback count zero. `NOT_APPLICABLE` requires a reason.

## Stimuli and independent expectations

| Case ID | Threat ID | Test class | Stimulus reference | Test-owned expected ordered findings | Historical verdict | Current verdict | Mutant ID |
|---|---|---|---|---|---|---|---|
| ... | ... | positive/negative/boundary/malformed/deletion/corruption/reordering/duplication/substitution/max-cardinality | ... | ... | ... | ... | ... |

Keep stimulus bytes/records separate from expectations. The executor receives
only the materialized stimulus. Expected findings and verdicts must be frozen
by a source independent of the implementation and compared outside it.

## Controlled mutants

| Mutant ID | Exact defect or source transformation | Stimulus | Named killing test/assertion | Expected finding/verdict | Execution count | State |
|---|---|---|---|---|---:|---|
| ... | ... | ... | ... | ... | 1 | killed/survived/not-executed |

A declaration, advertised command, or fabricated mock row is not an execution
receipt. Record the candidate, ordinal, count, phase, actual result, and named
assertion. C2 test-only mutants prove oracle discrimination; production-mutant
claims require the separately frozen implementation and real execution.

## Review receipts

| Role | Reviewer identity | Candidate head | Candidate tree | Durable URL | Disposition |
|---|---|---|---|---|---|
| Architecture / scope / phase | ... | ... | ... | ... | pending/pass/request changes |
| Security / trust | ... | ... | ... | ... | pending/pass/request changes |
| Readability / feasibility | ... | ... | ... | ... | pending/pass/request changes |
| Mutation / false pass | ... | ... | ... | ... | pending/pass/request changes |

The candidate author cannot fill `PASS`. All four receipts bind the same exact
head/tree. A corrected head invalidates all four receipts.

## Route and budget evidence

| Path | Per-path cap | Additions | Deletions | Charged | Mode | Disposition |
|---|---:|---:|---:|---:|---|---|
| ... | ... | ... | ... | additions + deletions | regular text | ... |

Record aggregate and partition totals, binary/rename/copy/symlink/nonregular/
missing/extra checks, C1/freeze identities, and staged/worktree/untracked state.
No deletion credit or cap redistribution is allowed. At 85 percent record the
required readability review; at 90 percent stop before further mutation.

## Checkpoint

```yaml
reviewState: PENDING_EXTERNAL_REVIEW
activation: NONE
authorityEffect: NO_AUTHORITY_EFFECT
expectedRed: []
implementationBlockers: []
evidenceBlockers: []
nextAction: obtain independent exact-head review
```

Expected RED failures, implementation blockers, evidence blockers, and
post-GREEN blockers are separate sets. A checkpoint cannot promote itself.
