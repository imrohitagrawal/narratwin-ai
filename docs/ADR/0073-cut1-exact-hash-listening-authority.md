# ADR 0073: Cut 1 exact-hash human-listening authority

- Status: Accepted for the Issue #479 repository boundary
- Date: 2026-08-31
- Decision owners: Cut 1 governance and engineering

## Context

T05B proves bounded WAV/SRT structure, non-silence, exact caption text and
timing, and immutable T05A/provider lineage. Those checks cannot hear audio and
cannot establish intelligibility, exact spoken words, pronunciation,
naturalness, accent, effective selected-voice identity, warmth, pacing, or
presenter fit. Treating structural admission as listening acceptance would be
a false-success path.

T05C therefore needs a separate trust boundary. The same eligible human may
review all three presenters separately, but every presenter needs a unique
decision and the reviewer cannot be that audio artifact's independently
committed author.

## Decision

Add `backend/app/cut1_listening.py` as a provider-neutral, metadata-only
authority. It accepts exactly three decisions in canonical Meera, Myra, Raj
order. Every decision binds the current T05B manifest sequence/checksum and the
exact presenter, selected voice, narration, source/evaluation, approval,
receipt, spoken-text, request, public/runtime configuration, audio, caption,
caption-text, caption-timing, and T05B authority identities.

All nine criteria must be present with literal boolean `true`. Decision IDs are
unique. Reviewer and claimed artifact author must match independently supplied
trust metadata and must differ. Candidate hashes are consistency evidence only:
an injected exact decision-commitment manifest supplies trust and can revoke a
decision. An independent current-audio resolver and artifact-author resolver
prevent candidate self-attestation.

Admission is single-use per service/state. State contains bounded metadata and
hashes only, is written atomically, rejects duplicate JSON members and unsafe
paths, and restores all-or-nothing. Admission, restoration, and retrieval each
revalidate current T05B, author, and decision commitments. Missing, malformed,
partial, reordered, cross-presenter, substituted, stale, replayed, revoked, or
coherently rehashed evidence fails closed.

## Consequences

The repository can validate independently authored exact-hash decisions but
cannot create, infer, copy, or default them. No helper converts WAV/SRT tests,
scores, ASR, or automation into listening acceptance. The module needs no raw
audio, caption text, narration text, provider request, credential, environment
secret, network, synthesis, or provider runtime.

This decision does not prove that any full narration exists or has been heard.
T05 remains incomplete and T06 remains blocked until three admissible full
narrations and separately authored exact-byte decisions exist. Provider
activation, narration egress, spend, media generation, deployment, release,
production readiness, and Cut 1 acceptance remain outside this ADR.
