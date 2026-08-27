# ADR 0064: Finite Adversarial-Convergence Framework

- Status: Accepted for inactive C2 RED construction; implementation pending
- Date: 2026-08-26
- Issue: #435
- Decision owner: repository OWNER amendment

## Context

Repeated Issue #435 attempts grew a slice-specific oracle into a universal,
self-proving protocol. The rejected candidate reached roughly 75,600 added
lines and included a 1.27 MB fixture. Review found unsafe fixture reads,
parse-before-identity behavior, exception leakage, route contradictions,
subset acceptance, forged import/oracle credit, platform-specific roots,
compressed tests, and candidate-authored PASS claims. Adding more cases and
reset numbers did not converge.

Issue #435 is a non-product governance prerequisite. It must remain separate
from the Cut 1 presenter and future product/runtime/provider work.

## Decision

Adopt one finite framework v1 with:

- the closed self-threat universe ACP-T01 through ACP-T12;
- exactly 40 ordered framework cases and 12 controlled test-owned mutants;
- a stimulus-only corpus and literal expectations owned by focused tests;
- a descriptor-relative bounded reader, strict duplicate-free JSON parsing,
  whole-file identity before parse, and typed failure containment;
- eight deterministic processing stages with complete predecessors;
- typed findings, verdicts, observations, mutation receipts, and review states;
- exact Issue #435 branch/base/path/mode/history/blob/budget enforcement;
- C1/C2/C3/C4 sequencing, four external reviews, only OWNER-enumerated pre-C3 corrections,
  a RED freeze, and no correction after C3;
- fixed readability, per-file, aggregate, corpus, and stop limits.

Framework v1 validates an explicitly supplied future-slice matrix but does not
author or certify that matrix. Every future slice owns its domain threats,
semantics, expectations, evidence, mutants, thresholds, and review.

## Trust and authority

All paths, JSON, matrices, stimuli, execution observations, mutation receipts,
review receipts, Git/event identity, and provider/model outputs are untrusted
until their applicable stage validates them. Candidate artifacts remain
`PENDING_EXTERNAL_REVIEW`; the candidate author cannot create a review PASS.

Activation is `NONE`, authority effect is `NO_AUTHORITY_EFFECT`, and release is
No-Go. The decision adds no runtime, product, provider, media, network,
credential, persistence, workflow, dependency, deployment, publication, or
spend authority.

## Phase consequences

1. C1 preserves only the preflight; `issuecomment-5435405260` adds parity checkpoint P, retaining C4/freeze solely to prove locked hosted CI without phase credit.
2. C2 freezes complete contracts, N=40 stimuli, test-owned expectations,
   adapters, tests, docs, and a typed `ACP.NOT_IMPLEMENTED` executor.
3. Four independent reviews bind one immutable C2 candidate. The original
   correction and blocked heads `134fbd9`, H3 `6d741ae`, and H4 `9bd0a27` are
   preserved. H5 `6b681b4` restores its budget gate; H6 is authorized by
   `issuecomment-5425499794` to fail closed on every JSON identity type, require
   distinct receipt sources, and enforce canonical author/reviewer identities.
   False-acceptance recovery `issuecomment-5428186737` preserves reviewed C2
   `26347f4` and archives invalid C3/C4 refs while adding 68 test-owned hostile
   regressions. Feasibility caps become module/test 950/1100, the C4 region remains 240 lines, and the projected final module is at most 850/950.
   N=40, threats, corpus identities, aggregates, and product authority do not
   change; every review binds the resulting exact head anew. Hosted-route
   recovery `issuecomment-5429174756`, corrected by `issuecomment-5429198021`,
   direct-head closure `issuecomment-5430095513`, omitted-head closure
   `issuecomment-5430474392`, and explicit-ancestor closure
   `issuecomment-5434868752`, preserves each reviewed
   C3/C4 as rejected history and appends ordinary fast-forward suffixes. Its
   sole semantic change outside the executor validates GitHub's detached merge
   or exact detached candidate checkout before selecting the candidate head.
4. C3 adds only the RED-freeze file and binds C2 objects plus review receipts.
5. C4 changes only the marked executor region, which is limited to 240 physical
   lines; the dispatcher, acceptance tests, and every production byte outside
   that region remain frozen.

The immutable dispatcher-owned runner distinguishes contract failure,
infrastructure failure, and exact typed RED; the mutable worker cannot
self-green. C2/C3 are intentionally not merge-eligible. Any new threat,
path, cap, invariant, corpus identity, unapproved correction, required post-C3
finding, or unresolved review disagreement stops for OWNER disposition.

## Alternatives rejected

### Continue Reset51 candidate2

Rejected. Its preserved review found phase-route mistakes, post-identity
resource leakage, forged `sys.modules` credit, subset acceptance, nonportable
test roots, compressed helpers, and premature PASS evidence.

### Build a universal oracle

Rejected. A reusable framework cannot prove every future domain. Universal
coverage expands state space, couples implementation to its expectations, and
recreates the non-convergent review loop.

### Put expectations in the corpus or implementation

Rejected. Candidate-controlled expected results permit self-fulfilling PASS.
Expectations remain literal test-owned data and the executor receives stimulus
only.

### Reuse the legacy Stage 8 route

Rejected for this issue. It rejects the exact OWNER-authorized governance
branch before the Issue #435 boundary. A narrow exact dispatcher preserves all
unrelated Stage 8, Final Review, and Phase 1 Closure behavior.

## Verification

- Green C2 subsets prove corpus/schema identity, safe input handling,
  expectation separation, 12 executed/killed mutants, route rejection, and
  import/readability boundaries.
- The exact 40 future-behavior tests fail only with `ACP.NOT_IMPLEMENTED`.
- `make quality` reaches the typed intentional RED rather than legacy routing.
- C3 and C4 require the separately frozen identities and review evidence.
- Hosted checks use a detached merge or candidate checkout. The route accepts
  omitted-head evidence only when its canonical branch is detached, its supplied
  base is a strict ancestor of ambient HEAD, and the complete fixed topology passes.
  Explicit-head single-parent evidence requires ambient to equal the event head
  and its supplied base to be a strict ancestor. Explicit two-parent merge
  evidence remains bound to exact canonical base/head order.
  A detached merge still requires ordered frozen-base/candidate parents; all
  repository evidence is read from the selected candidate, never ambient merge
  content.

## Residual risks

At C2, the production executor is intentionally absent and external review
receipts do not yet exist. At C3, implementation remains absent. At C4, frozen
tests may still reveal a required finding; the only response is OWNER rescope,
defer, or explicit non-convergent closeout. None of these states authorizes
product behavior or release.
