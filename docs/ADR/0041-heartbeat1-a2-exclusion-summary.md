# ADR 0041: Heartbeat 1 A2 exclusion and owner summary

Status: Proposed for issue `#304` review under parent authority `#302`.

## Decision

Represent exclusion as a durable `SourceDecisionRecord` with `DENY`, `EXCLUDED`, no retained `SourceRecord`, and one bounded action/reason pair.
Keep safety ahead of action and policy so exclusion cannot launder unsafe input into durable metadata.
Expose one owner-scoped, deterministically ordered summary that separates curated sources, metadata-only exclusions, and derived `UNSEALED_LEGACY` records.
Restore validates source-less decisions independently and removes every forbidden attached source, chunk, ingestion, dependent claim, and invalid replay result.

## Consequences

Exact exclusion replay survives local restart without retaining raw content, while changed requests conflict.
A1 and valid v1 behavior remain additive and unchanged; UI/browser proof, H2, providers, deployment, and production claims remain deferred.
