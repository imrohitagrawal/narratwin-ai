# ADR 0070: Infer governed presenter identity from exact narration claims

- Status: Accepted for Issue #459 T05A controlled-local handoff
- Date: 2026-08-30
- Decision owner: Issue #459 checkpoint `5465050919`

## Context

The immutable Cut 1 facts contract already binds every one of the eighteen
canonical claims to separate Meera, Raj, and Myra hashes. The evaluator and
narration lifecycle nevertheless enforced the earlier Issue #421 Meera-only
selection. After T03 activated governed Raj/Myra derivatives, that historical
execution restriction prevented each fallback from obtaining its own grounded
Stage 4 run and narration receipt. Reusing Meera's run or receipt would violate
presenter, script, evaluation, and source lineage.

Issue #368 owns real audio and caption production. T05A must provide its exact
provider-neutral input authority without performing provider work or claiming
that audio or captions exist.

## Decision

The Cut 1 evaluator compares the complete ordered eighteen-claim hash set with
all three immutable presenter mappings and accepts only when exactly one
presenter matches. No match, multiple matches, mixed claims, incomplete claims,
claim reordering, source drift, or evidence drift remains a failure.

The narration service accepts any active governed presenter only when removing
the validated citation markers from that exact passing run yields that
presenter's canonical narration byte-for-byte. The narration checksum and TTS
text-authority receipt continue to bind the presenter registry, source run,
request, trace, evaluation, claim evidence, approval, and spoken text. A run
for one presenter cannot be combined with another presenter's binding.

## Consequences

Meera, Raj, and Myra can each produce an independent, persisted, replayable
narration receipt for the later Issue #368 handoff. The receipt authorizes exact
text consumption only; it is not audio, a caption file, a render, or acceptance
evidence.

No provider, credential, environment lookup, network, egress, spend, synthesis,
retry, media generation, registry/media mutation, deployment, publication,
release, production-readiness, or Cut 1 acceptance authority is created.
Issue #368 must separately produce and bind real audio/caption artifacts before
T05 can complete.
