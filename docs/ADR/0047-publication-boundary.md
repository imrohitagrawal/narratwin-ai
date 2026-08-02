# ADR 0047: Fail-Closed Publication Boundary

## Status

Accepted for Issue #324 governance; no product runtime or release authority.

## Context

Canonical public sources mixed product value with owner-designated delivery and
distribution strategy. A public repository cannot protect a file merely by
labeling it internal. NarraTwin also emits or plans to emit text, media,
metadata, logs, search queries, and provider requests, so prose cleanup alone
would not define a durable boundary.

## Decision

Adopt `PublicationBoundaryV1` with three schema-closed classes: `PUBLIC`,
`INTERNAL`, and `RESTRICTED`. Classify at source, propagate the most restrictive
provenance, reject unknown classes, and prevent prompts, retrieval, models, or
providers from downgrading provenance. Keep private records outside this public
repository in genuine access-controlled storage.

The executable repository gate validates the contract, all 12 surface families,
canonical public markers, neutral controlled-demo path, and launch No-Go. It is
a governance oracle for later runtime adoption, not evidence that runtime
redaction, public distribution, or production is implemented.

### Enforcement structure

The gate uses a responsibility-split `publication_boundary` package:

- shared `branch_identity.py` reconciles and validates event/Git identity;
- `contract.py` owns the closed schema and surface registry;
- `decision.py` owns the pure fail-closed approval/provenance decision;
- `repository.py` owns canonical-source and known-regression evidence;
- `scope.py` owns the exact branch/path/charged-line policy;
- `git_evidence.py` owns pinned-base and bounded diff evidence;
- `context.py` owns recursive file indexing and per-file budgets;
- `reporting.py` owns bounded, control-safe failure output;
- `cli.py` composes checks and fails closed on missing evidence;
- `__init__.py` is the explicit package API index; and
- `check_publication_boundary.py` is the stable thin entry point.

`check_phase1_quality.py` is the canonical Phase 1 entry point. Its separate
`phase1_closure` package runs the publication gate first, then executes the
still-applicable legacy contracts in their original order. Executable source
characterization rejects an added, removed, or reordered legacy check or demo
marker. Whole-file SHA-256 and line-count receipts also reject any silent growth
of the 7,387-line checker or 9,970-line test. Only the exact Issue `#324` legacy
scope check and the removed demo path are superseded; other branches and merged
`main` retain legacy scope behavior.

Tests mirror those responsibilities instead of appending to the historical
Phase 1 closure test monolith. Executable per-file context budgets cap each new
implementation or test module at 250 lines, 32,000 bytes, and 120 characters
per line; the entry point is capped at 40 lines. Touched pre-existing
integration gates are grandfathered at 500 lines and may not grow past that
ceiling. Every owned module/test is recursively discovered, must be explicitly
indexed in the preflight, and must be a regular non-symlink file. Pure functions
own stateless rules. A frozen approval value object is
used only where policy version,
approver, source checksums, surface, provenance, and exact payload digest must
stay bound together.

The decision engine consumes a fully validated compiled policy. An untrusted
envelope contains only its surface and payload. `ALLOW` additionally requires a
matching `PublicationApproval` from a trusted server-side registry. Payload or
caller claims cannot manufacture approval. This PR defines and tests the
governance oracle but creates no cryptographic, identity, authorization, or
runtime storage boundary; those require a separate implementation controller.

Stopped v1 reached 10,158 test lines. The merged baseline and current v2 keep
the 9,970-line Phase 1 test file and 7,387-line checker unchanged. They require
separate, incremental extraction with characterization tests. Refactoring them
inside Issue #324 would expand the publication-boundary blast radius and delay
the accepted product path.

## Alternatives rejected

- **Rename an in-repository folder to internal:** rejected because repository
  visibility, not the filename, controls access.
- **Keyword denylist only:** rejected because paraphrases and structured metadata
  bypass vocabulary scanning, while legitimate audience terms could be erased.
- **Let prompts or models decide:** rejected because model instructions are not
  an authorization or confidentiality boundary.
- **Append another block to the Phase 1 monoliths:** rejected because unrelated
  controller rules, failures, and review context would remain coupled.
- **Introduce an object hierarchy for a stateless rule:** rejected because
  modular pure functions provide the required ownership without hidden state or
  inheritance coupling.
- **Rewrite history:** rejected because protected evidence must remain intact.

## Consequences

- Public sources use one neutral product statement while preserving legitimate
  audience adaptation.
- Internal and restricted content fails closed and requires an external private
  system chosen by the repository owner.
- Historical references remain visible as history; this is prospective control,
  not retroactive erasure.
- Future runtime publication requires a separate issue, implementation, tests,
  human risk decisions, and launch authorization.

## Issue #335 amendment — 2026-08-02

Issue #335 required a one-time, human-reviewed receipt rotation. The frozen test
remains exactly 9,970 lines; its only ratified changes replace the controlled
Heartbeat 2 prompt and repair the independent expectation so selected retrieval
contexts are a bounded, unique subset of accepted chunks. This amendment does
not authorize further growth of either legacy monolith. Future unrelated
behavior still requires modular extraction rather than another monolith edit.
