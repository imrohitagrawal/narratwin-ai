# ADR 0068: Cut 1 controlled-presenter evidence controller

- Status: Accepted for Issue #459 T04 local evidence validation
- Date: 2026-08-28
- Decision owners: repository owner, governance, AI quality, security/privacy
- Scope: deterministic validation only; no rendering or acceptance authority

## Context

Issue #459 freezes six independent Meera, Raj, and Myra English presentation
cells across landscape and portrait aspects. Its T02 evidence schema and
136-case stimulus corpus define authority, lineage, approval, rights, media,
observability, dependency, and C1-M01 through C1-M10 failure boundaries. The
historical quality module was intentionally a typed RED executor and could not
serve as a production-owned canonical boundary.

T04 needs one real evaluator without activating a media generator, external
provider, credentials, egress, spend, retry, persistence, deployment, or human
study. It must also reject Stage 7 mock/stub compatibility output and
placeholder/non-real-video evidence rather than treating those older test
surfaces as Cut 1 artifacts.

## Decision

`backend/app/cut1_controlled_presenter.py` is the sole canonical T04 evaluator.
It accepts one already-materialized mapping and returns an immutable tuple
containing at most one primary finding. The quality module imports and
re-exports that implementation; it contains no second evaluator.

Validation is standard-library-only and pure. It closes mapping keys, scalar
types, bounded ID and RFC3339 timestamp lexemes, finite-number handling,
cell identity, frozen authority, lineage, approvals/currentness, rights,
provenance/deletion references, media facts, provider-disabled posture,
observability, the evidence register, C1-M01 through C1-M10, dependency stops,
and blocked acceptance state. Deny-signals for mock/stub adapters and
`supportsRealVideo=false` are evaluated before generic closed-shape rejection
so test-only compatibility output receives an explicit primary finding.

Finding precedence is deterministic and fail closed. Schema-invalid or
ordinary JSON-shaped malformed leaves cannot reach hashing, set operations,
sorting, or arithmetic that raises. Repeated evaluation does not mutate input
and serializes byte-for-byte identically.

An empty finding tuple proves only that the frozen synthetic blocked fixture is
internally coherent. It is not evidence that media exists and cannot authorize
Cut 1 acceptance.

## Security, privacy, and observability

The evaluator performs no filesystem read or write, network or URL access,
subprocess execution, environment or credential lookup, provider call, retry,
spend, rendering, media generation, or telemetry export. It logs no input,
provider payload, exception detail, identifier, or content. Callers own safe
materialization and any later audit persistence under separately reviewed
authority.

Malformed and hostile inputs produce one bounded code/path/message or the
pre-existing non-finite finding. No raw input is reflected in findings.

## T03 and later handoffs

T04 pins the historical source presenter registry digest used by the frozen
synthetic fixture. T03 must not silently overwrite that meaning when it adds
Raj/Myra derivative readiness. A later reviewed route must preserve the source
registry binding and add a separately named derivative/readiness binding, or
explicitly re-freeze every affected consumer.

T05 remains stopped on the Meera-only grounding/narration contract and Issue
#368 audio ownership. Issues #432 and #449 retain human-study and runtime
provider authority. Historical Stage 7 mocks/stubs remain unchanged for
compatibility and can never produce acceptance evidence.

## Consequences and limitations

The repository gains a deterministic policy/evidence controller and a thin
quality adapter. It does not gain a renderer, provider adapter, artifact writer,
runtime endpoint, UI flow, deployment, publication, release candidate, public
availability, production readiness, human-study result, or Cut 1 acceptance.

Independent exact-head review and hosted push checks remain required for the
T04 checkpoint. T03 asset activation is serialized after that checkpoint.

## Alternatives rejected

- Keep the typed RED executor: it cannot validate T04 evidence.
- Reuse Stage 7 mock/stub output: it creates false media acceptance.
- Duplicate logic in the quality adapter: it creates divergent authorities.
- Load the schema or environment at evaluation time: it introduces I/O and
  mutable ambient authority.
- Return every finding: it conflicts with the frozen single-mutation primary-
  finding contract and makes precedence unstable.
