# ADR 0071: Bind approved narration audio and captions before rendering

- Status: Accepted for Issue #459 T05B offline authority preparation
- Date: 2026-08-30
- Decision owner: Issue #459 checkpoints `5466871459` and `5467125295`
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

Issue #475 reproduced two integration defects without calling a provider. The
public narration service emits `presenter_binding_checksum` as 64 lowercase
hexadecimal characters without a `sha256:` prefix, while T05B expected the
prefixed representation. Separately, a hosted provider result binds a private
runtime configuration whose checksum is intentionally distinct from the
public Cut 1 configuration checksum; treating those as one identity rejected a
genuine candidate or invited the public contract to be overwritten.

## Decision

`backend.app.tts_provider.ApprovedNarrationTTSResult` is the provider-neutral
result type for approved narration. The existing Google result structurally
extends it, while the provider remains optional and disabled unless injected.

`backend.app.cut1_audio.Cut1AudioAuthorityService` accepts only already-
materialized typed candidates. It has no provider seam and never calls
synthesis. Before persistence it:

1. revalidates the exact T05A receipt, including its genuine bare presenter
   binding digest;
2. preserves the byte-identical public configuration checksum and, for hosted
   candidates only, requires a distinct provider-runtime configuration
   checksum that matches the typed provider result;
3. recomputes the audio checksum and independently decodes bounded RIFF/WAVE;
4. requires mono PCM16 at 24 kHz, 90–120 seconds, and non-silent signal;
5. strictly parses canonical UTF-8 SRT with continuous ordered timing;
6. proves caption words equal the exact citation-free spoken narration; and
7. checksum-binds all receipt, source, evaluation, presenter, configuration,
   audio, measurement, caption, and timing fields; and
8. requires the exact request and final authority checksums, record
   completeness, and canonical presenter order to match a trusted immutable
   external commitment manifest.

Optional local persistence stores receipt, result bytes, caption bytes, and the
authority projection in one bounded atomic JSON state. The state file's hashes
are not treated as their own trust anchor. Restore additionally requires its
manifest sequence/checksum and exact ordered commitments to match the external
current manifest. Coherently rehashed artifact replacement, record deletion,
reordering, rollback, duplicate members, unsafe files, stale receipt authority,
or malformed artifacts quarantine the state and expose zero authority.
Persistence completes before the replacement set becomes visible.

Issue #475 advances the authority, state, commitment, and commitment-manifest
schemas to v2 so both configuration identities are persisted, restored,
hashed, and externally committed. `cut1-audio-config-v1` remains unchanged
because the public configuration preimage and checksum do not change.

## Security and capability boundary

The authority module imports no provider SDK, credential/environment facility,
network client, socket, or subprocess facility. It does not synthesize or
generate media. Test-only WAV/SRT fixtures exercise validation and are not
accepted media, provider evidence, or Cut 1 evidence.

Configuration is constructor-injected and exact: its checksum is derived from
provider, mode, locale, model, and the full presenter-to-voice mapping. A
result cannot self-select different configuration. Hosted candidates require
the separate runtime checksum; local/mock candidates record explicit `null`
and cannot fabricate hosted runtime authority. Receipt currency is checked
again immediately before persistence and on every retrieval. A new trusted
manifest replaces the complete authority set atomically, leaving no stale
presenter row. Raw narration, audio, and captions are not logged.

## Consequences and limitations

- T05B removes the opaque provider result and creates a deterministic offline
  admission boundary for future genuine Issue #368 artifacts.
- The bound waveform checks prove format, duration, checksum, and non-silence;
  they do not prove intelligibility, naturalness, effective voice identity, or
  human acceptance. Those remain exact-artifact Issue #368/T08 evidence.
- Continuous SRT timing proves a complete, non-overlapping declared timeline;
  it does not prove forced alignment to speech. Exact alignment remains future
  genuine-artifact evidence.
- Security depends on the commitment resolver being current, immutable outside
  the mutable state file, and independently governed. T05B implements no
  production commitment store and makes no hardware-backed durability claim.
- No audio/caption artifact is committed or accepted by this increment. T05,
  T06, Cut 1, release, deployment, publication, and production readiness remain
  incomplete and No-Go.
- Issue #475 performs zero provider calls, credential reads, egress, spend,
  synthesis, audio generation, or listening acceptance. Missing, malformed,
  substituted, stale, cross-presenter, partial, replayed, receipt-reused, and
  coherently rehashed bindings continue to fail closed.
