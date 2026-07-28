# ADR 0040: Heartbeat 1 A1 curated eligibility

Status: Proposed for issue `#302` A1 review.
Issue `#302` requires one bounded eligible-source path without authorizing A2 exclusion, UI/browser work, Heartbeat 2, providers, or production claims.

## Decision
Add an explicit `source-curation-v1` target kind beside the unchanged legacy document path.
Bind tenant, owner, project, source, decision, policy, version, checksum, and assertion fingerprint at submit and recheck them at approval and ingestion.
Persist only validated pending/approved pairs; ingest approved sources atomically; repair invalid dependent state before startup completes.

## Consequences
Exact replay is deterministic and durable; transport rejection stays nondurable, application rejection is replayable, and invalid or cross-scope state fails closed.
