# ADR 0071: Bind approved narration audio and captions before rendering

- Status: Accepted for Issue #459 T05B offline authority preparation
- Date: 2026-08-30
- Decision owner: Issue #459 checkpoint `5466871459`
- Depends on: ADR 0055, ADR 0056, and ADR 0070

## Context

T05A created separate, current, replayable narration receipts for Meera, Myra,
and Raj. The downstream approved-narration provider protocol still returned an
opaque `object`, and Stage 6 delegated that value without independently binding
audio and captions to the narration receipt. No persisted record joined the
exact script, source run, evaluation, presenter, approved configuration, WAV
bytes, decoded measurements, and caption bytes.

Issue #368 retains genuine synthesis and exact-hash listening ownership. Its
historical non-TTS search-egress incident is not accepted or superseded here.
No existing private screening or rejected artifact is final Cut 1 evidence.

## Decision

`backend.app.tts_provider.ApprovedNarrationTTSResult` is the provider-neutral
result type for approved narration. The existing Google result structurally
extends it, while the provider remains optional and disabled unless injected.

`backend.app.cut1_audio.Cut1AudioAuthorityService` validates an already
materialized result through an injected provider seam. Before persistence it:

1. revalidates the exact T05A receipt;
2. rejects receipt reuse and cross-presenter or configuration substitution;
3. recomputes the audio checksum and independently decodes bounded RIFF/WAVE;
4. requires mono PCM16 at 24 kHz, 90–120 seconds, and non-silent signal;
5. strictly parses canonical UTF-8 SRT with continuous ordered timing;
6. proves caption words equal the exact citation-free spoken narration; and
7. checksum-binds all receipt, source, evaluation, presenter, configuration,
   audio, measurement, caption, and timing fields.

Optional local persistence stores the receipt, result bytes, caption bytes,
and immutable authority record in one bounded atomic JSON state. Restore is
all-or-nothing: duplicate members, unsafe files, checksum drift, stale receipt
authority, malformed artifacts, record substitution, or duplicate receipts
quarantine the state and expose zero authority. Persistence completes before
the in-memory record becomes visible.

## Security and capability boundary

The authority module imports no provider SDK, credential/environment facility,
network client, socket, or subprocess facility. It does not synthesize or
generate media. Test-only WAV/SRT fixtures exercise validation and are not
accepted media, provider evidence, or Cut 1 evidence.

Configuration is constructor-injected and exact: provider, mode, locale, model,
presenter-to-voice mapping, and configuration checksum must match. A result
cannot self-select different configuration. Raw narration, audio, and captions
are not logged.

## Consequences and limitations

- T05B removes the opaque provider result and creates a deterministic offline
  admission boundary for future genuine Issue #368 artifacts.
- The bound waveform checks prove format, duration, checksum, and non-silence;
  they do not prove intelligibility, naturalness, effective voice identity, or
  human acceptance. Those remain exact-artifact Issue #368/T08 evidence.
- Continuous SRT timing proves a complete, non-overlapping declared timeline;
  it does not prove forced alignment to speech. Exact alignment remains future
  genuine-artifact evidence.
- The local checksum chain detects state and record tampering but is not a
  hardware-backed anti-rollback counter. Whole-storage rollback outside the
  current narration receipt is not represented as production durability.
- No audio/caption artifact is committed or accepted by this increment. T05,
  T06, Cut 1, release, deployment, publication, and production readiness remain
  incomplete and No-Go.
