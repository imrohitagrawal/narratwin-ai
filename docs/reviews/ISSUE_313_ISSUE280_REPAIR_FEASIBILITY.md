# Issue 313: Issue 280 Repair Feasibility And Semantic Oracle Decision

## Decision Summary

Issue #280 is closed administratively but is not semantically fixed. This
workstream is **GO for a subsequent repair issue** using a bounded,
source-grounded Semantic-frame intermediate representation and deterministic
local/mock renderers. It is **NO-GO for runtime repair in Issue #313**. The
later issue must first implement the independent proposition oracle and commit
behavioral RED against the current runtime before changing product code.

PR #299 remains unchanged. Its branch head
`f93653e8a11e697c88766b207fb01c18662339d6` remains falsifying evidence, not an
implementation base or positive closure source.

## Audience-collapse defect

The defect is a semantic false-pass boundary, not simply missing translation.
The preserved execution evidence records 525 completed rows and zero refusals,
yet each of 75 language/depth groups contains seven accepted audience scripts
with only one distinct visible target body. Audience labels and metadata vary;
the meaning delivered to the user collapses.

This exposes three separable failures:

1. The current bounded phrasebook/converter architecture cannot reliably map
   arbitrary owner-authored source propositions to audience- and depth-specific
   target meaning.
2. Earlier closure paths allowed structural labels, implementation-authored
   expectations, or caller-selected scope to stand in for semantic proof.
3. No independent oracle owns the expected proposition set, mandatory rows,
   exact thresholds, and verdict computation.

Transport, request completion, target-language markers, citation shape,
artifact checksums, and distinct strings are useful structural evidence. None
proves that required meaning is present, unsupported meaning is absent, or
audience/depth choices materially affect the visible target transcript.

## Bound Evidence And Preservation

The following identities are observations only. Issue #313 does not edit their
sources or reinterpret them as success.

| Evidence | Immutable identity | Meaning |
|---|---|---|
| PR #299 branch | `f93653e8a11e697c88766b207fb01c18662339d6` | Preserved unmerged correction and forensic evidence |
| Main requirement matrix blob | `eb9336c69f318391c7ac53f4cd24f0136a3bf1f7` | Negative containment matrix on branch base `6e78ecd89373901795d97e4baddf03f54b1df4a4` |
| Main forensic verifier blob | `f1fc0ccb25ce3237d3f4a4b1c92579efcdd76365` | Negative-only verifier; never a semantic pass oracle |
| Issue #300 preflight blob | `22efd5e66f4a61b213df699f2e4ab50439805991` | Preserved E1/E2/E5 and containment contract |
| Forensic unit-test blob | `2957673c9e96b2b055822a5dcae16b7bcb383282` | Preserved negative verifier tests |

The Issue #313 allowlist excludes `reports/`, the forensic verifier, runtime
code, and every existing Issue #280 artifact. Base-relative path equality and
the exact branch gate make preservation executable.

## Independent semantic oracle

The normative contract is
`docs/evals/issue280_semantic_oracle_v1.json`. It deliberately separates:

- expected truth: a reviewed, owner-authored proposition manifest frozen
  before repair code;
- actual evidence: browser-visible target transcript plus decoded exported
  artifacts;
- implementation: the later semantic-frame compiler and language renderers;
- verdict: a separate oracle executor that evaluates every repository-owned
  mandatory row.

The oracle must not import `backend/app/issue280.py`, generate fixtures from the
repair implementation, use converter-authored target text as expected truth,
accept caller-selected rows, or accept an implementation-authored verdict.
Human bilingual review may audit fixture meaning, but cannot replace the
machine-enforced coverage and zero-tolerance invariants.

### Required measurements

Every mandatory row must meet every threshold; averages cannot compensate for
a failure:

| Measurement | Required result | Why it blocks false pass |
|---|---:|---|
| Essential-proposition recall | `1.0` | User-supplied facts cannot disappear |
| Unsupported-proposition count | `0` | Renderers cannot invent claims |
| Citation-support precision | `1.0` | Meaning must remain bound to its source |
| Audience required-emphasis recall | `1.0` | Audience selection must affect meaning |
| Pairwise audience-collapse count | `0` | Prefix/label changes cannot pass |
| Depth-role violation count | `0` | Concise/standard/deep roles remain exact |
| Glossary loss count | `0` | Required protected terms survive |
| Target-script violation count | `0` | English fallback/templates cannot pass |
| Mandatory-row coverage | `1.0` | Scope cannot be narrowed by the caller |

The verdict codomain is `SEMANTIC_PASS`, `NOT_PROVEN`, or `FAILED`.
`STRUCTURAL_PASS` can describe plumbing but cannot satisfy a semantic row.

### Required later fixture shape

The subsequent repair issue must freeze synthetic markdown and an independent
proposition manifest before runtime changes. Each proposition needs a stable
ID, source span, required/optional status, audience-emphasis tags, depth role,
glossary terms, citation/context/claim-support binding, and forbidden
inferences. The mandatory matrix includes all supported languages at the
standard recruiter baseline; every depth on one identical tuple; every
audience on one identical tuple; Latin, Devanagari, RTL, and CJK script
representatives; and explicit unsupported-language/clause refusals.

## Architecture Comparison

| Candidate | Semantic fidelity | Determinism | Oracle independence | Breadth and cost | Decision |
|---|---|---|---|---|---|
| Phrasebook expansion | Low outside enumerated clauses; repeats the current coupling | High | Weak because expected phrases tend to mirror implementation tables | Maintenance grows by clause × language × audience × depth | **NO-GO** as the repair architecture |
| Semantic-frame intermediate representation plus deterministic renderers | High within an explicitly bounded synthetic domain; propositions remain source-bound | High | Strong if the oracle owns a separate proposition manifest and never imports runtime frames | Moderate implementation; incremental language coverage; local/mock | **GO** candidate for a subsequent repair issue |
| Local model adapter | Potentially broad but nondeterministic and difficult to prove without human/model judgment | Low to medium | Weak unless evaluated by a separately licensed and operated judge | New model/dependency, resource, license, supply-chain, and reproducibility risks | **NO-GO** under current authority |
| Refusal-only containment | Honest and safe but delivers no repaired multilingual product outcome | High | Strong | Low cost, high loss of user value | **NO-GO** as repair; retain only as fallback behavior |

### Selected architecture boundary

The subsequent repair may introduce a typed semantic frame between grounded
Stage 4 propositions and Stage 6 target rendering. A frame may carry only
source-supported proposition IDs, roles, audience emphasis, depth eligibility,
glossary bindings, citations, context refs, and claim-support IDs. Language
renderers consume that frame deterministically and must fail closed when a
required proposition or renderer capability is unavailable.

The frame is not the oracle. The oracle starts from its separately frozen
owner-authored proposition manifest and observes visible/decoded outputs. It
must therefore detect a parser that drops meaning, a renderer that collapses
audiences, and an artifact path that changes the visible result.

## Subsequent Repair Issue Entry Criteria

A later controlling issue may authorize runtime repair only when it freezes:

1. the exact backend/frontend/test/docs allowlist and a bounded line budget;
2. owner-authored fixtures and proposition manifests independent of runtime;
3. an oracle executor path that does not import repair code;
4. behavioral RED reproducing audience collapse, prefix-only variation,
   missing propositions, unsupported claims, and self-scoped row selection;
5. incremental implementation order: oracle executor, RED evidence, semantic
   frame, one language/audience/depth vertical slice, then bounded expansion;
6. mandatory local API/browser/artifact evidence and exact-head CI review;
7. explicit refusal behavior for unsupported clauses and languages.

No implementation may claim Issue #280 fixed until every mandatory oracle row
is `SEMANTIC_PASS`, all adversarial cases are rejected, and the original
Issue #280 acceptance contract is reconciled without proxy criteria.

## Skills And Test Selection

Invoked: GitHub triage, spec-driven development, planning-and-task-breakdown,
context engineering, TDD, and incremental implementation. They governed the
frozen contract, dependency order, committed RED, and bounded GREEN work.

Rejected as wrong-surface: backend, frontend, API, RAG, provider, browser,
performance, observability, and runtime security implementation skills. No UI
or runtime behavior changes here. Custom skills, external translation models,
and model judges were rejected because existing repository guidance is
sufficient and those options add dependency, license, resource, and circular
evaluation risk.

## Human Review And Stop Rule

The independent reviewer must decide whether the oracle remains independent of
the semantic-frame representation, whether exact thresholds reject the known
false-pass classes, whether the GO candidate is feasible within local/mock
scope, and whether all forensic evidence is unchanged.

Stop if a model/provider, new dependency, real/private data, license decision,
protected-evidence edit, wider architecture, or non-deterministic human-grade
translation claim becomes necessary. Runtime status remains
`NO_GO_UNTIL_SEPARATE_REPAIR_ISSUE`.
