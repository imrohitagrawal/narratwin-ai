# Issue 300 Governance Reset Preflight

## Objective

Repair the Issue #280 semantic-closure governance and verifier before any
product/runtime recovery. Issue #280 is semantically `FAILED` at exact head
`f93653e8a11e697c88766b207fb01c18662339d6`.

## Forensic Source Facts

The following observed execution facts are inputs, not editable pass claims:

| Fact ID | Exact-head observation | Classification impact |
|---|---|---|
| GOV300-FACT-001 | API and browser attempted 525 combinations | structural execution occurred |
| GOV300-FACT-002 | 217 succeeded and 308 returned `ISSUE280_TRANSLATION_REFUSED` | required matrix is `FAILED` |
| GOV300-FACT-003 | CONCISE 175/175, STANDARD 21/175, DEEP 21/175 | depth matrix is `FAILED` |
| GOV300-FACT-004 | All 31 successful language/depth groups emitted identical target text for seven audiences | audience semantics are `FAILED` |
| GOV300-FACT-005 | Existing gate exits zero with `NOT_PROVEN` rows | closure verifier is `FAILED` |

Issue #280, merged PR #293, Issue #298, and PR #299 remain unchanged forensic
history. PR #299 must not be merged or sent for human review in this recovery.

## Scope And Non-Goals

Allowed work is limited to governance documents, repository guardrails,
semantic-closure verifier code, atomic evidence schemas, a repository-owned
output-correctness skill, and focused tests.

No backend, frontend, provider, RAG, avatar, database, Docker, hosted, public,
paid, real-media, cloned-identity, or other product/runtime implementation is
allowed. This issue does not attempt translation repair.

## Canonical Classification Contract

| Classification | Meaning | May satisfy a semantic row? |
|---|---|---:|
| `STRUCTURAL_PASS` | path, schema, artifact, or execution structure is mechanically valid | No |
| `SEMANTIC_PASS` | an independent, non-read-only exact-head oracle observed the required meaning | Yes |
| `NOT_PROVEN` | proof is missing, stale, partial, or incapable of proving the claim | No |
| `FAILED` | observed behavior contradicts the requirement or exposes a false pass | No |

These are the only allowed atomic outcomes. Documentation, metadata,
screenshots, matrix status, artifact downloadability, and self-attestation do
not upgrade structural evidence to semantic proof.

## Atomic Closure Model

Closure is a pure computation over atomic rows:

1. The declared required row IDs must exactly equal the observed row IDs.
2. Every row must use one canonical classification.
3. Every required semantic row must be `SEMANTIC_PASS`.
4. Every required structural row must be `STRUCTURAL_PASS` or
   `SEMANTIC_PASS`.
5. Any `NOT_PROVEN` or `FAILED` row makes closure false and the CLI nonzero.
6. Every semantic pass must bind to the exact reviewed head and the
   non-read-only output-correctness fan.
7. Editable aggregate fields such as `satisfied`, `complete`,
   `issue280SatisfiedByPrE`, and report-level `status: PASSED` are forbidden
   inputs and cannot affect closure.

## Review Fan Contract

Two fans are mandatory and exact-head bound:

| Fan | Mode | Independent responsibility |
|---|---|---|
| `pm-ai-shipping:intended-vs-implemented` | analytical review | compare documented atomic intent with cited enforcement and observed behavior |
| `output-correctness` | non-read-only execution | execute the user-visible slice and emit semantic observations |

The fans must use distinct reviewer identities and evidence records. The
output-correctness fan must declare `executionMode: non-read-only`. A shared
editable pass field, identical evidence record, stale commit, missing fan, or
same reviewer makes closure false.

## Architecture Feasibility Checkpoint

Before any later runtime issue starts, an exact-head review must select one:

- feasible with a reviewed executable semantic oracle;
- reduced/demoted support with honest refusal and matching product claims; or
- blocked.

Expected-output text authored solely by the implementation path cannot be the
oracle. Until this checkpoint and the semantic oracle are reviewed, product code
remains blocked.

## Semantic Oracle Contract

The future oracle must:

- execute through the user-visible path without synthetic success interception;
- bind every observation to the exact commit;
- cover every required atomic language/depth/audience row;
- detect refusals, source-language fallback, partial output, invariant audience
  output, and unsupported semantic additions;
- keep structural and semantic observations separate;
- fail closed on missing, partial, stale, or malformed evidence.

## Failure Matrix

| ID | Mutation / false pass | Required result |
|---|---|---|
| GOV300-FM-001 | `NOT_PROVEN` row with aggregate `satisfied: true` | nonzero |
| GOV300-FM-002 | `FAILED` row with report `status: PASSED` | nonzero |
| GOV300-FM-003 | semantic row classified `STRUCTURAL_PASS` | nonzero |
| GOV300-FM-004 | evidence head differs from reviewed head | nonzero |
| GOV300-FM-005 | required atomic row omitted | nonzero |
| GOV300-FM-006 | output fan is read-only | nonzero |
| GOV300-FM-007 | two fans share reviewer/evidence identity | nonzero |
| GOV300-FM-008 | audience-invariant execution is marked passed | rejected as `FAILED` |
| GOV300-FM-009 | translation refusals are hidden by successful rows | rejected as `FAILED` |
| GOV300-FM-010 | unknown classification or editable aggregate closure key | nonzero |

## Matrix-To-Test Mapping

`tests/unit/test_semantic_closure.py` owns GOV300-FM-001 through
GOV300-FM-010. Focused tests must be observed RED before
`scripts/quality/semantic_closure.py` is implemented. Mutation coverage changes
one load-bearing field at a time and requires the computed closure to remain
false.

## Skill And Tool Selection Ledger

| Claim/boundary | Option | Decision | Evidence or prevented action |
|---|---|---|---|
| intent gap | `pm-ai-shipping:intended-vs-implemented` | required fan | prevents docs/matrix claims from standing without implementation evidence |
| semantic output | repository-owned `output-correctness` | create and lock | supplies the missing non-read-only execution method |
| behavior change | TDD | invoke | RED verifier mutations precede implementation |
| GitHub state | GitHub skill plus local `gh`/`git` | invoke | exact issue, PR, branch, and head state verified |
| product implementation skills | frontend/backend/provider workflows | rejected now | architecture/oracle checkpoints are not reviewed |
| third-party custom skill | external skill install | rejected | a narrow first-party repository skill avoids new code, network, telemetry, hooks, and credentials |

## Stop Rule

Stop before product/runtime code. A newly discovered false-pass class requires
updating this contract and adding a RED mutation before changing the verifier.
Runtime recovery requires a later issue/branch/PR only after the architecture
feasibility checkpoint and semantic oracle are reviewed.
