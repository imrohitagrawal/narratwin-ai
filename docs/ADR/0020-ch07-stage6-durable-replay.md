# ADR 0020: CH-07 Stage 6 Durable Replay

## Status

Accepted on branch.

## Context

Stage 6 produces translated scripts, subtitles, voice-manifest metadata, and a
derived metadata artifact from a grounded Stage 4 walkthrough run. The replay
contract for Phase 1 Closure issue `#39` must preserve these artifacts from
durable local state without treating them as trusted provider output.

The replay surface must bind:

- tenant, project, and actor identity
- source run identity
- source and target language
- source text checksum
- source evaluation ID and checksum
- source context reference IDs and citation indexes
- trace identity
- idempotency scope and request checksum

Restored rows must be rejected when malformed, incomplete, cross-boundary,
checksum-mismatched, or stale. Pending and running idempotency rows are not
durable success states.

## Decision

Stage 6 durable replay stores an explicit multilingual result envelope and a
derived metadata artifact that together encode the source binding and checksum
contract. Restore logic revalidates the stored result, subtitles, voice-manifest
metadata, and derived metadata artifact before replaying a completed response.

Replay uses checksum-based dedupe keyed by the request identity and source
binding. A restored row is only replayable when the source binding and all
derived checksums still match the canonical values reconstructed from the
stored row.

Local/mock provider posture remains the only supported runtime behavior in this
branch. No paid provider enablement, external egress, or production readiness is
claimed by this ADR.

## Consequences

- Durable Stage 6 rows carry enough information to replay translated scripts,
  subtitles, and derived metadata safely.
- Restore can drop corrupted or tampered rows instead of trusting them.
- API responses can expose the bound trace metadata without exposing secrets or
  provider-trusted content.
- Future production work still needs the remaining durability, retention,
  provider-posture, and untrusted-input closure items tracked under issue `#39`.
