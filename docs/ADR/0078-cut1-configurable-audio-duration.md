# ADR 0078: Bind Cut 1 audio duration as governed configuration

- Status: Accepted for Issue #509
- Date: 2026-09-03
- Decision owner: Issue #509 freeze 5515713754

## Context

T05A fixed every narration receipt to 90–120 seconds, while T05B separately
fixed WAV input to 6,000,000 bytes. The owner-approved Myra narration is
127.661917 seconds and 6,127,816 bytes at the required 24-kHz mono PCM16
format. Altering its cadence or bytes to satisfy those constants would degrade
an accepted product artifact and would not solve the reusable configuration
problem tracked by Issue #493.

## Decision

NarrationService keeps 90–120 seconds as its safe default and accepts an
explicit constructor-injected pair of positive, ordered integer seconds. The
effective pair is part of every narration checksum, evaluation/approval chain,
TTS receipt, receipt checksum, and persisted/restored state. A state created
under one pair fails closed when loaded under another.

T05B accepts the current receipt-owned pair after validating its shape. Its
canonical WAV byte ceiling is derived from the upper duration, 24,000 samples
per second, two bytes per mono PCM16 sample, and the canonical 44-byte RIFF
header. There is no second independently tuned audio-byte value.

## Consequences

Issue #368 can inject 90–135 seconds and admit the exact approved audio without
shortening, compression, acceleration, trimming, resampling, or regeneration.
Invalid or substituted policy, stale state, oversized audio, and duration drift
still reject. The provider format and every presenter, narration, source,
evaluation, approval, receipt, configuration, audio, caption, commitment,
replay, and persistence boundary remain unchanged.

The constructor is the bounded configuration seam for this increment. Parent
Issue #493 remains open for broader deployment/tenant precedence, inventory,
and manifest-driven governance work. This ADR creates no provider, credential,
egress, spend, media, human acceptance, T06, deployment, release, production,
or Cut 1 completion authority.
