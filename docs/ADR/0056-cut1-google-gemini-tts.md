# ADR 0056: Govern optional Google Gemini-TTS behind the existing TTS boundary

- Status: Runtime identity plus direct REST and official unary gRPC transports implemented behind a disabled boundary; activation remains package-governed
- Date: 2026-08-11
- Issue: #368
- Authority: [OWNER runtime authorization](https://github.com/imrohitagrawal/narratwin-ai/issues/368#issuecomment-5245861950)

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

The optional runtime uses `google-auth==2.56.3` only in the providers extra. Its
locked closure is `cryptography==50.0.0`, `pyasn1-modules==0.4.2`,
`pyasn1==0.6.4`, and the already-present `cffi==2.0.0`/`pycparser==3.0`.
The transport uses direct standard-library sockets and TLS: all DNS answers are
screened, the checked peer is connected directly on port 443, exact EU SNI is
used, proxies and redirects are forbidden, and the prepared session is single
use. ADC is lazy and unreachable while disabled; refresh and quota-project
failures are bounded and redacted.

Enabled authorized-user ADC also requires one server-owned quota project and
its exact SHA-256. The configured project must be a valid 6–30-character Google
Cloud project ID, its hash must match, and native ADC—loaded without a desired
quota-project override—must expose the same non-empty project both at identity
resolution and immediately before egress. The adapter constructs
`x-goog-user-project` itself beside the exact Authorization and Content-Type
headers in the fingerprinted order. The raw project and access token are hidden
from runtime representations and are neither caller-selectable, persisted, logged, nor
returned by product APIs; only its approved hash enters activation, config, and
request-fingerprint evidence.

Every final 90–120-second artifact requires structural validation, exact
trace/checksum binding and exact-hash OWNER listening. No cloning, reference
audio, enrollment, biometric input, voice conversion or identifiable-person
imitation is permitted.

The normative facts, blockers, invariants, matrices, test plan and exact future
route are in
`docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md`.

### Current T05A presenter-binding compatibility

The current narration receipt deliberately carries `presenter_binding_checksum`
as exactly 64 lowercase hexadecimal characters, while its narration, source
evaluation, evaluation, approval, and receipt checksums remain `sha256:`-
prefixed. The Google adapter validates those two shapes independently and
rejects legacy-prefixed, uppercase, short, long, or non-hex presenter bindings
before identity resolution or transport preparation. This compatibility repair
does not change the provider, endpoint, voices, activation, or release posture.

### Supported ADC refresh transport

The optional runtime lazily creates the documented public
`google.auth.transport.requests.Request` for ADC refresh. It does not depend on
Google Auth's private `_http_client` module. Missing optional transport support
still fails closed as `GOOGLE_TTS_DEPENDENCY_UNAVAILABLE`, and injected test
factories remain available for zero-network validation. This correction changes
neither credentials nor the provider request transport, endpoint, model, voice
mapping, activation, budget, privacy, or release posture.

### Bounded synchronous response window

Google documents `text:synthesize` as synchronous: callers receive the result
only after all input has been processed. The first governed full-narration POST
returned no bytes within the former hard 30-second socket window and was
correctly retained as billable unknown. For the required 90–120-second Cut 1
artifact, the optional Google provider and regional transport therefore accept
one explicitly configured, numeric, finite, positive, runtime-representable
timeout up to Python's platform-derived `threading.TIMEOUT_MAX`. This is a
runtime capability, not a hard-coded business ceiling. The default remains 3
seconds; only server-owned configuration can select a longer window, and the
governed operation package binds the exact selected value.

The validator rejects boolean, non-numeric, non-finite, non-positive, and
non-representable values. This finite configured window does not change the exact endpoint,
single-use connection, one-request concurrency, maximum response bytes,
activation, budget, attempt ledger, or ambiguity behavior. A timeout after
possible egress remains `BILLABLE_UNKNOWN` and is never retried automatically.
The finite-timeout invariant is code-enforced; the operational duration is not
a hard-coded business ceiling. Generic environment configuration alone does not
grant provider, egress, retry, or spend authority.
The source contract is the official
[synchronous synthesis method](https://cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize).

### Privacy-safe non-success diagnostics

The package-12 Meera request received a definite non-success response, but the
adapter retained only its generic public 502. A typed provider diagnostic now
preserves the numeric upstream status, bounded response byte count and SHA-256,
an allowlisted structured Google error numeric code/status pair, and SHA-256
values for at most one allowlisted request identifier and trace identifier.
The exception keeps its existing generic code, status and message, remains
billable and non-retryable, and still transitions durable state to
`FAILED_BILLABLE`.

Raw provider response bodies, error messages, headers and identifiers are never
retained in the diagnostic. Structured fields are omitted when JSON is
malformed or duplicated, code/status values disagree, status vocabulary is not
allowlisted, or identifier aliases are conflicting, empty or oversized.
Out-of-range HTTP status and oversized response bodies continue to fail through
the existing response-schema/size boundaries without a diagnostic. The safe
mapping is available to a private operation driver for an immutable bounded
stop record; repository code does not write private operation evidence or
authorize a retry.

### Explicit official unary gRPC transport

Two fresh, independently frozen full-Meera packages sent the same authorized
request through the direct HTTP/1.1 REST transport. Both received the same
1,613-byte upstream 502 response with the same body hash after approximately
62.2 seconds. Credentials, quota project, billing, EU endpoint, privacy screen,
text, voice and configuration preflights had passed. The repeated timing and
response fingerprint support, but do not prove, a REST gateway/backend deadline;
Google supplied no usable request identifier or structured internal cause.

Issue #498 therefore adds a second, explicitly selected transport using
`google-cloud-texttospeech==2.37.0` and its public synchronous unary gRPC client.
It does not replace the existing REST transport and never falls back between
them. Before identity or narration is supplied, the new path resolves and
screens every EU-host address, opens a TLS channel pinned to one screened IP,
sets the exact EU hostname as SNI and authority, disables gRPC HTTP-proxy use,
and requires channel readiness. The SDK call receives the already validated
request as typed `SynthesisInput`, `VoiceSelectionParams`, and `AudioConfig`,
passes the ephemeral bearer and quota-project values only as per-call metadata,
sets `retry=None`, and uses the operation-configured finite timeout.

The returned raw audio is bounded, wrapped only for compatibility with the
existing internal response validator, and then follows the unchanged WAV,
durable ledger, T05B admission and T05C listening path. A failed call retains
only an allowlisted canonical gRPC status and generic billable-unknown error;
raw exception messages, details, debug strings, metadata, request content,
credentials, project identity and response payloads are discarded. Tests use
injected channels/clients plus real SDK request types and make no provider call.

This capability does not contain narration text, voice assets, audio, captions
or speaking avatars and does not itself call Google. After merge, a separately
frozen and authorized private operation package may explicitly select it for
the existing Meera, Myra and Raj mappings. Successful transport would still
prove neither spoken correctness nor human acceptance.

### Official-client failure-status compatibility

Issue #507 preserves the existing privacy-safe symbolic gRPC status when the
official client translates an RPC failure into a `google.api_core` exception.
The extractor accepts either the wrapper's `grpc_status_code` or the existing
raw callable `code()` shape only when the result is the binding's real gRPC
status enum, then reuses the fixed provider allowlist. Crafted, unknown,
malformed or throwing values become absent. Raw exception/provider data is not
retained, and billing, retry, timeout, transport and request behavior do not
change.

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
- The implementation adds a provider-owned optional runtime and pinned optional
  dependencies, but no credential, generated audio, frontend choice, automatic
  provider activation, deployment, distribution or release.
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
