# ADR 0056: Govern optional Google Gemini-TTS behind the existing TTS boundary

- Status: Adapter implemented behind a disabled boundary; activation not authorized
- Date: 2026-08-10
- Issue: #368
- Authority: [OWNER scope amendment](https://github.com/imrohitagrawal/narratwin-ai/issues/368#issuecomment-5241211974)

## Context

The preserved Issue #368 preflight commit proposed eSpeak-only local synthesis
through a new module. The OWNER subsequently selected three exact-hash Google
Cloud Text-to-Speech Gemini-TTS screening references and authorized governance
reconciliation. Issue #237 already owns a provider-neutral TTS boundary in
`backend/app/tts_provider.py`, consumed by Stage 6 with mock/local defaults and
injected test transports.

Narration text sent to a hosted provider crosses privacy, trust, retention and
cost boundaries. Regional Europe processing is not India residency. Generated
output is nondeterministic, and accepted screening bytes do not approve a later
full narration or establish legal rights.

## Decision

The Cut 1 implementation extends the existing `TTSProvider` boundary.
Domain and narration code select semantic profiles `meera`, `myra`, and `raj`.
Only the provider adapter knows the immutable mapping to Despina, Leda, and
Achird; `gemini-2.5-pro-tts`; `en-IN`; and
`https://eu-texttospeech.googleapis.com`.

Mock/local remains the default in local development, tests and CI. Google is an
optional hosted adapter, disabled by default and activated only through a
separate approved runtime-identity/configuration gate. Unit/API/CI tests use
fake transports and fake identity providers and make zero external calls.

Configuration is allowlisted before egress. Callers cannot choose a URL, model,
voice, locale, output, authentication mode or provider prompt. Google responses
are untrusted and require bounded schema, base64, format, decode, signal,
duration, truncation, clipping and checksum validation before persistence.

The adapter uses only unary `POST` to
`https://eu-texttospeech.googleapis.com/v1/text:synthesize`, exact single-speaker
`text`/`prompt` input, the selected model/locale/voice, and LINEAR16 24 kHz mono
PCM16 WAV output. Unknown request/response leaves and alternate audio controls
fail closed. The prerequisite OWNER-authorized contract at
`docs/governance/cut1-google-gemini-tts-style-prompts-v1.json` now fixes each
profile's exact decoded prompt string, version, UTF-8 byte count and SHA-256.
Those are the only permitted future adapter prompts; callers cannot supply or
modify them. The normative leaf and header allowlist is in the Issue #368
governance review.

The exact voice and locale are requested configuration, not proof of effective
output identity: Google's `VoiceSelectionParams` contract permits region or
language substitution. Activation therefore also requires a first-party
guarantee or separately approved, checksum-bound effective-output verification.
Invalid response/audio bytes are bounded-memory only and are never persisted or
quarantined when validation fails.

The request ledger binds current narration/source/evaluation/approval authority,
semantic profile, adapter configuration, request trace, response artifact,
decoded measurements, retention/deletion state and checksums. An ambiguous
timeout after possible egress is billable-unknown: it holds reservation and is
not automatically retried or refunded.

ADC or an equivalently governed workload identity may resolve outside source
control. Product configuration, APIs, logs and evidence cannot contain API keys,
OAuth or refresh tokens, service-account JSON, credential files or paths.

Every final 90–120-second artifact requires structural validation, exact
trace/checksum binding and exact-hash OWNER listening. No cloning, reference
audio, enrollment, biometric input, voice conversion or identifiable-person
imitation is permitted.

The normative facts, blockers, invariants, matrices, test plan and exact future
route are in
`docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md`.

## Consequences

- The stale `local_tts.py`/eSpeak execution route is rejected, while its commit
  remains in normal history.
- Provider substitution remains possible because vendor vocabulary stops at the
  adapter.
- Hosted narration cannot activate until legal, privacy/retention, account,
  budget/IAM/ADC, dependency/transport and exact-listening blockers are cleared.
- The canonical style-prompt prerequisite is satisfied, but adapter
  activation remains separately unauthorized and gated by legal, privacy,
  identity, billing, quota, endpoint-policy, effective-output and listening
  evidence.
- Output remains nondeterministic; selected screening hashes are reference
  evidence only, and final 90–120-second narration requires validation and OWNER
  listening.
- The implementation adds only an injected identity/HTTP adapter and a
  provider-neutral receipt delegation seam. It adds no network client,
  dependency, credential, generated audio, frontend choice, provider
  activation, deployment, distribution or release.
- The injected transport is two phase: it must return an opaque send capability
  bound to an already-established session that attests pinned
  public DNS, TLS/SNI, port 443, disabled redirects and no proxy before the
  adapter supplies either authorization or narration bytes. Receipt authority
  is checked again after egress and before any artifact commit.
- Enabled operation requires a durable state path and holds an atomic adjacent
  lock across refresh, reservation, egress and finalization. A retained crash
  lock blocks replay pending explicit reconciliation; every replay, state query
  and deletion refreshes disk state under the same cross-instance lock.
- Reservations conservatively include raw UTF-8 input bytes as an upper-bound
  text-token estimate plus 3,000 output tokens, bind the reviewed 2026-08-10
  prices, and reconcile accepted output to validated duration. These are safety
  ceilings, not observed billing or activation evidence.

## Alternatives rejected

- Retain eSpeak: contradicts the exact OWNER selection.
- Add a parallel Google-facing domain service: duplicates and weakens Issue #237.
- Expose Google choices to the frontend: creates vendor coupling and an
  untrusted configuration surface.
- Commit a credential file or use an API key: violates repository and OWNER
  credential boundaries.
- Retry ambiguous POST timeouts: no first-party TTS idempotency/billing-safe
  guarantee was found and duplicate spend is possible.
