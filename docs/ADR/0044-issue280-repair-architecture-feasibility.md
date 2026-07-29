# ADR 0044: Issue 280 Repair Architecture Feasibility

- Status: Accepted
- Date: 2026-07-30
- Decision owner: Issue #313
- Runtime posture: `NO-GO_UNTIL_SEPARATE_REPAIR_ISSUE`

## Context

Issue #280 is administratively closed but not semantically fixed. Preserved PR
#299 evidence at `f93653e8a11e697c88766b207fb01c18662339d6` shows completed output
whose visible target bodies collapse across audience selections. Negative
containment through Issue #300 and PR #301 prevents that evidence from becoming
a positive closure claim, but does not select a repair architecture or provide
an independent semantic oracle.

The current failure cannot be solved safely by adding more output markers or
by allowing the implementation to define its own expected text and row set.

## Decision

Approve a Semantic-frame intermediate representation with deterministic,
fail-closed local/mock language renderers as the bounded candidate for a later
repair issue.

The frame will carry source proposition IDs, semantic roles, audience emphasis,
depth eligibility, glossary bindings, citations, context refs, and
claim-support IDs. It may not contain unsupported meaning. A renderer that
cannot preserve a mandatory proposition must refuse rather than emit a
template, English fallback, or partial success.

Pair that architecture with an independent proposition oracle whose expected
semantics come from an owner-authored manifest frozen before repair code. The
oracle must not import the runtime converter or semantic-frame implementation,
must observe browser-visible and decoded artifact output, and must compute a
verdict over every repository-owned mandatory row.

No runtime code changes are authorized by this ADR or Issue #313. The selected
candidate is GO only for specification in a new controlling repair issue.

## Alternatives

### Phrasebook expansion

Rejected as the primary repair. It is deterministic but scales as clauses ×
languages × audiences × depths, encourages tests that mirror implementation
tables, and does not address arbitrary owner-authored propositions.

### Local model adapter

Rejected under current authority. It adds nondeterminism, dependencies,
resource and supply-chain costs, model/license review, and a likely model-judge
evaluation path. Those constraints conflict with the current deterministic
local/mock and independent-oracle boundary.

### Refusal-only containment

Rejected as the repair outcome because it cannot deliver the Issue #280 user
journey. It remains the required safe fallback for unsupported clauses,
languages, or missing semantic-frame capabilities.

## Consequences

Positive:

- source support survives as typed proposition identity rather than inferred
  from rendered strings;
- audience and depth semantics become explicit, testable inputs;
- deterministic renderers retain local/mock reproducibility;
- the oracle can falsify parser, renderer, UI, and artifact failures without
  sharing runtime implementation logic.

Costs and risks:

- the later repair requires a proposition parser and bounded renderers;
- owner-authored multilingual proposition fixtures require careful human audit;
- breadth must grow incrementally and unsupported cases must refuse honestly;
- an oracle executor and behavioral RED must land before runtime GREEN.

## Implementation Gate

Runtime repair remains `NO_GO_UNTIL_SEPARATE_REPAIR_ISSUE`. That issue must
freeze its own preflight, exact allowlist, budgets, proposition fixtures,
oracle executor, behavioral RED, implementation increments, full local/browser
evidence, and exact-head independent review. PR #299 and all existing forensic
evidence remain immutable inputs, never an implementation base.
