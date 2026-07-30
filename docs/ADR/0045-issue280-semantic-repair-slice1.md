# ADR 0045: Issue 280 semantic repair slice 1

- Status: Accepted for the bounded Issue #317 implementation
- Date: 2026-07-30
- Authority: Issue #317, following ADR 0044 and Issue #313

## Context

The prior local/mock path preserved transport, structure, citations, and
language markers while discarding audience meaning during target-language
rendering. Seven accepted Spanish scripts could therefore expose one semantic
body. Structural runtime success is not evidence of the required product
outcome.

## Decision

Implement ADR 0044's semantic-frame candidate for one repository-owned
synthetic cohort. Runtime owns immutable proposition IDs, English source
clauses, Spanish target clauses, essential/audience roles, `STANDARD` depth
roles, glossary terms, and citation indexes. It selects two essential
propositions plus the requesting audience's one required emphasis and renders
them deterministically. The existing API, replay storage, transcript artifact,
claim support, and browser surfaces carry the proposition bindings.

An independently authored manifest owns expected semantics and mandatory rows.
A standard-library executor consumes only that manifest and an observation
envelope, computes every exact threshold, rejects row/schema manipulation and
surface disagreement, and cannot import runtime. Runtime cannot import the
manifest or executor. Altered or incomplete cohort clauses, non-Spanish target
language, non-`STANDARD` depth, or required glossary loss refuse before
storage.

## Consequences

The seven audiences now have distinct, citation-bound Spanish bodies for one
auditable source, and the browser/API/artifact/oracle surfaces can prove the
same outcome. Meanings are duplicated intentionally across independent
runtime and oracle authorities; drift fails tests rather than allowing one to
generate the other's truth. Existing unrelated local/mock fixtures retain
their legacy structural behavior and receive no semantic certification.

This decision does not establish arbitrary translation, another language or
depth, provider quality, real-data behavior, hosted/public operation,
durability, privacy, production readiness, release, or complete Issue #280
repair. Those require separately authorized expansion. PR #299 and all
forensic evidence remain immutable historical evidence.

## Post-merge compatibility correction

Issue #321 preserves this architecture while correcting the renderer call
boundary introduced by PR #318. A semantic request passes its exact non-null
frame to the renderer. A non-semantic request uses the established
`facts`/`audience`/`depth` keyword contract without supplying the optional
keyword as `None`. Each path invokes the renderer once.

The correction deliberately does not catch `TypeError` or retry rendering.
Internal renderer defects therefore remain public-safe internal failures,
while unsupported renderer output continues through the existing evaluator to
the established HTTP 422 refusal. No semantic proposition, language, depth,
artifact, citation, oracle, storage, or browser contract changes.
