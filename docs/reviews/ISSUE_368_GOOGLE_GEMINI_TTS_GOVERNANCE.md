# Issue #368 Google Gemini-TTS governance reconciliation

Status: governance contract only; runtime implementation and activation are not
authorized. Release remains **No-Go**.

Observed: `2026-08-10T13:54:26Z` unless a row says otherwise.

## Authority and decision boundary

The OWNER accepted the selected screening references by exact hash in
[Issue #368 comment 5240725519](https://github.com/imrohitagrawal/narratwin-ai/issues/368#issuecomment-5240725519)
and supplied the controlling scope amendment in
[Issue #368 comment 5241211974](https://github.com/imrohitagrawal/narratwin-ai/issues/368#issuecomment-5241211974).
The private inventory SHA-256 is
`0254a800487eeb74c09a6e2486db807ded9baf8be9c5663c8cd9bd034c3d910b`,
with 1,569 inventory bytes, four entries totaling 20,894 bytes, and zero replay
mismatches. No private clip, request payload, credential, or generated audio is
copied into Git.

| Profile | Adapter-only selection | Accepted reference evidence |
|---|---|---|
| `meera` | `gemini-2.5-pro-tts`, `en-IN`, `eu-texttospeech.googleapis.com`, Despina | clip `4a650279a67a4a5a328b907e4447a0760a1cf8fe6014dbc9258db803df26c06a`; request manifest `d6f3f3a250e773bd8528586d9a29ca2732170394c65cc8b56a14330a88ce1e2f` |
| `myra` | same model, locale, endpoint; Leda | three-paragraph clip `0b8b798d5690a6be3b21aa2779bcb7133cabed08343cb01bb6128b46cf7472a1` (30.152875 seconds); segment manifests `a1891952b0bdc9b62ada4dad73f1573ac9713f3bd1874149022e01a18ea8eb6c`, `7d57778f34ca992ba114a1ada6a34eb41a4af3041eda04de7bddbbdbafffe86b`, `9c57a380800372902a2b79893cf3cd7fbcd286567e6067285fb84b3367ff86e0` |
| `raj` | same model, locale, endpoint; Achird | clip `87e942edebde3084e465b20042eaf1c32d64e06f3cd8a6e40458397834978c74`; request manifest `530a7744fd65af88faf53e1e49dff07035a4bd6f7e5779876b474fd265ecfdd7` |

These hashes prove OWNER acceptance of those reference bytes only. They do not
prove deterministic future output, full-narration acceptance, licensing or
commercial-use clearance, privacy clearance, provider activation, deployment,
distribution, or release.

## Reconciliation with the repository

The original commit `b346a9d4fbccffeb9c3ee3950e6f00893d7c9f92` proposed a
new `backend/app/local_tts.py`, eSpeak 1.52, local-only, offline-only, key-free
execution route. That proposal is preserved in history but is not implementable.
This amendment replaces only those conflicting assumptions.

Issue #237 already established the correct seam:

- `backend/app/tts_provider.py` owns the optional server-side TTS provider and
  injected transport boundary.
- `backend/app/stage6.py` consumes that boundary and keeps `MockTTSProvider` as
  the default.
- unit and API tests inject transports and make no real provider call.
- source/evaluation bindings, quota, idempotency, artifact metadata, deletion,
  restore, and redacted error surfaces already exist but need Cut 1 hardening.

The future change must evolve that seam. It must not create a second
product-facing Google service, route, or domain vocabulary. Narration and Stage
6 consumers select `meera`, `myra`, or `raj`; an adapter-owned immutable mapping
selects Despina, Leda, or Achird. No frontend field contains a Google endpoint,
model, voice, authentication mode, or provider-native payload.

The current code is not claimed ready. In particular, it is ElevenLabs-shaped,
uses a concrete external-provider type in Stage 6, accepts an API-key field,
does not structurally decode all audio, and can refund timeout failures. Future
implementation must generalize the interface, prohibit key/file configuration
for Google, validate decoded audio, and hold ambiguous post-egress timeouts as
billable-unknown.

## First-party source ledger

All source observations below are first-party Google publications. Facts apply
as observed; activation requires a fresh-source replay because provider facts
can change.

| Source and exact URL | Directly supported fact | Consequence |
|---|---|---|
| [Gemini-TTS documentation](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts) | `gemini-2.5-pro-tts` is documented for Cloud Text-to-Speech; the page lists Despina, Leda, Achird and `en-IN`. It describes GA models, unary formats including LINEAR16/WAV and MP3, 8,192 input and 16,384 output token limits, prompt and text limits of 4,000 bytes each and 8,000 combined, approximate output up to 655 seconds with possible truncation, and permission `aiplatform.endpoints.predict` (included in `roles/aiplatform.user`). | Pin exact allowlisted values; validate UTF-8 bytes before egress; use a stricter Cut 1 duration/size budget; treat any truncation as failure; least-privilege IAM review is required. |
| [Cloud TTS release notes](https://docs.cloud.google.com/text-to-speech/docs/release-notes) | Gemini 2.5 Pro TTS became GA on 2025-09-30; the Pro model became available on global, US, and EU endpoints on 2025-12-11. Release notes also demonstrate changing model/voice availability. | Selected model/region is not a preview assumption, but availability must be rechecked before activation and monitored; no immutable model revision is documented. |
| [Cloud TTS endpoints](https://docs.cloud.google.com/text-to-speech/docs/endpoints) | The exact EU hostname is `eu-texttospeech.googleapis.com`; regional-endpoint data at rest and in use remains within the Europe boundary. Google documents an organization-policy endpoint restriction. | Allowlist only `https://eu-texttospeech.googleapis.com`; reject redirects and caller URLs; require policy evidence. Europe processing is not India residency. |
| [Cloud TTS quotas](https://docs.cloud.google.com/text-to-speech/quotas) | Gemini 2.5 Pro TTS has a documented default quota of 125 requests/minute; project-effective quota can vary. This page also says synthesized audio may be used in applications or media subject to Google Cloud terms and applicable law. Its generic request-content limit says 5,000 bytes. | Read effective project quota at activation; enforce a lower app limit. The generic 5,000-byte statement conflicts with the Gemini page's 8,000 combined rule, so the implementation must satisfy each per-field Gemini cap and an app-level combined cap no greater than 5,000 until Google resolves the discrepancy. This is not commercial legal clearance. |
| [Cloud TTS pricing](https://cloud.google.com/text-to-speech/pricing) | Gemini 2.5 Pro TTS lists no free allowance, charges $1 per million text tokens for input and $20 per million audio tokens for output, with audio tokens calculated at 25 tokens/second. Billing must be enabled. | Budget by token estimate and duration, not generic character pricing; reserve before egress and reconcile actual bounded metadata afterward. Price must be rechecked before activation. |
| [Cloud TTS authentication](https://docs.cloud.google.com/text-to-speech/docs/authentication) and [ADC overview](https://docs.cloud.google.com/docs/authentication/application-default-credentials) | Cloud TTS supports Application Default Credentials. ADC searches an environment credential path, a local ADC file, then an attached service account. | Product configuration must not accept any credential path or secret; activation must use an externally governed runtime identity and must prove which ADC source resolved. |
| [Provide credentials to ADC](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc) | Google recommends attached service accounts on Google Cloud and Workload Identity Federation outside Google Cloud; service-account keys create security risk. | Long-lived service-account JSON and keys are prohibited. Runtime identity selection remains an activation review item. |
| [Cloud TTS data logging](https://docs.cloud.google.com/text-to-speech/docs/data-logging) | Google describes Cloud TTS as stateless/resourceless and says it does not log customer text or audio; Data Access and System Event audit logs do not apply. | Application logs must provide redacted decision/cost evidence because provider content logs are unavailable. This statement does not by itself resolve all Gemini abuse-monitoring retention. |
| [Google Cloud service-specific terms](https://cloud.google.com/terms/service-terms) | Generated Output is Customer Data; as between Google and the customer, Google does not claim ownership in new IP created in Generated Output. Output may be similar or inaccurate. The terms constrain training on generated output and describe prompt/output handling. | Bind terms version/date at activation, disclose nondeterminism, prohibit training, and obtain legal review. Ownership language is not a warranty, indemnity, or commercial-use clearance. |
| [Generative AI indemnified services](https://cloud.google.com/terms/generative-ai-indemnified-services) | No Text-to-Speech entry was found at observation time. | Do not claim Google generative-AI IP indemnity for this route; legal/commercial distribution approval is an activation blocker. |
| [Generative AI prohibited-use policy](https://policies.google.com/terms/generative-ai/use-policy) and [Google Cloud AUP](https://cloud.google.com/terms/aup) | Policies prohibit rights/privacy violations, deceptive impersonation and other harmful or unlawful uses. | Enforce no cloning, enrollment, biometrics, identifiable-person imitation, voice conversion, provenance deception, or unlawful content. |
| [Cloud data residency terms](https://cloud.google.com/terms/data-residency) | Cloud Text-to-Speech appears as an AI/ML data-location service. | Regional documentation supports a Europe boundary only; it does not establish India residency or the complete contractual retention posture. |
| [Google generative-AI abuse monitoring](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/abuse-monitoring) | Google separately documents abuse monitoring for some generative-AI services, including possible suspicious-prompt retention and human review. The page does not establish that the Cloud TTS Gemini route is in or out of that program. | Treat the tension with the TTS no-content-logging page as unresolved. Account-specific written confirmation is required before real narration egress. |
| [Google Cloud deprecation policy](https://cloud.google.com/terms/deprecation) | GA services are generally governed by applicable deprecation terms; pre-GA offerings are excluded. | The service is GA, but exact model/voice/version guarantees remain unresolved. Monitor release notes and fail closed on allowlist drift. |
| [REST synthesize method](https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize) | Synthesis is a POST operation using the Cloud Platform OAuth scope. | POST is not assumed idempotent. The request ledger must prevent duplicate spend. |
| [SynthesisInput](https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/SynthesisInput) and [AudioConfig](https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioConfig) | `prompt` is the unedited Gemini-TTS style instruction; input sources are a union. Audio controls include encoding, sample rate, speaking rate, pitch, volume gain and effects profiles. | Permit plain `text` plus one approved prompt only; reject SSML/markup/multi-speaker/custom-pronunciation and every unselected audio control. |
| [VoiceSelectionParams](https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/VoiceSelectionParams) | Google warns that the service may choose a voice with a different region or even a different language from the requested `languageCode`; request parameters guide selection but do not prove the effective output locale. | Treat `en-IN` and the stock voice names as exact requested configuration only. Effective locale/voice assurance needs a Google guarantee or separately bound verification evidence and remains an activation blocker. |
| [Google Cloud retry strategy](https://docs.cloud.google.com/storage/docs/retry-strategy) | Google's general retry guidance makes retry safety depend on response and operation idempotency. It is not a Cloud TTS billing guarantee. | Inference: without a documented TTS idempotency key or billing-safe retry contract, retry only proven pre-egress failures. A timeout after possible egress is billable-unknown and is never automatically retried or refunded. |

## Unresolved activation blockers

These are not contradictions to the governance amendment, because no activation
is authorized, but each blocks a real call or distributable narration:

1. Legal review must approve applicable Cloud/service terms, generated-output
   rights, lack of a found TTS indemnity listing, commercial distribution, and
   acceptable-use obligations. The reference hashes do not supply that review.
2. Privacy review must obtain account/service-specific confirmation reconciling
   TTS no-content-logging with potentially applicable generative-AI abuse
   monitoring, retention, human review, and deletion behavior.
3. The OWNER must accept external narration-text egress and Europe—not India—
   processing for the exact approved narration.
4. Cloud project, billing account, effective quota, budget/alert, endpoint
   organization policy, least-privilege IAM, runtime identity, and ADC source
   require recorded human approval outside source control.
5. Dependency/transport choice is unresolved. No Google SDK is approved by this
   governance PR. A future implementation preflight must justify the official
   client library or a standards-based transport, licenses, transitive supply
   chain, credential behavior, and exact changed lockfiles before mutation.
6. Google does not document an immutable model revision, a TTS idempotency key,
   billing treatment for ambiguous timeouts, or product-specific retry safety.
7. The generic 5,000-byte request limit and Gemini 8,000-byte combined limit
   require conservative app enforcement or written clarification.
8. Every final 90–120-second artifact remains blocked until structural checks,
   exact binding/checksum replay, and exact-hash OWNER listening accept it.
9. The private selected request-manifest hashes do not expose the style-prompt
   bytes or a separately verifiable prompt hash. No executor may invent, omit or
   approximate them. A prerequisite governance amendment must record approved
   canonical prompt bytes and SHA-256 for each semantic profile before future
   runtime implementation begins.
10. Google documents possible region/language substitution. Exact request-field
    binding therefore does not prove the effective output locale or voice. A
    first-party guarantee or separately governed effective-output verification
    method must be approved and bound before activation.

## Normative adapter request and output allowlist

The following is the only permitted logical Cloud TTS contract. A provider SDK
may not broaden it. The unresolved prompt row makes implementation fail closed;
it is not a wildcard.

| Leaf | Exact allowed value |
|---|---|
| transport | synchronous unary HTTPS only; no streaming or long-audio API |
| method and URL | `POST https://eu-texttospeech.googleapis.com/v1/text:synthesize` |
| request top-level keys | exactly `input`, `voice`, `audioConfig`; reject unknown or duplicate keys; omit `advancedVoiceOptions` |
| `input` keys | exactly `text`, `prompt`; `text` equals the current receipt's UTF-8 `spoken_text`; no `ssml`, `markup`, `multiSpeakerMarkup` or `customPronunciations` |
| `input.prompt` | **BLOCKED** until a prerequisite OWNER-authorized governance amendment records canonical bytes, version and SHA-256 separately for `meera`, `myra`, and `raj`; selected request-manifest hashes cannot substitute for prompt hashes |
| input byte limits | `len(text.encode("utf-8")) <= 4000`, `len(prompt.encode("utf-8")) <= 4000`, and their sum `<= 5000`; count canonical raw field-string bytes before JSON escaping and reject before auth/network |
| `voice.languageCode` | requested value exactly `en-IN`; effective locale substitution remains blocked as described above |
| `voice.modelName` | exactly `gemini-2.5-pro-tts` |
| `voice.name` | immutable requested adapter map: `meera -> Despina`, `myra -> Leda`, `raj -> Achird`; request equality does not prove effective output identity |
| `voice` other keys | none; no multi-speaker voice configuration or caller field |
| `audioConfig` | exactly `{"audioEncoding":"LINEAR16","sampleRateHertz":24000}`; no speaking rate, pitch, volume gain, effects profile or other leaf |
| auth scope | exactly `https://www.googleapis.com/auth/cloud-platform`, obtained through externally governed ADC/equivalent identity |
| logical application headers | exactly `Authorization: Bearer <redacted-runtime-token>` and `Content-Type: application/json; charset=utf-8`; `x-goog-user-project: <approved-project-id>` is required only when a signed activation record pins `quota_project_required=true` and the approved project-ID hash, otherwise it is prohibited; reject every other application header; transport diagnostic headers require separate review and cannot carry product content |
| response JSON | exactly one `audioContent` base64 string; reject unknown/duplicate fields, malformed base64, trailing data and non-success statuses |
| decoded container | complete RIFF/WAVE with signed 16-bit little-endian PCM, 24,000 Hz, mono; reject extra executable/unknown chunks and every mismatched property |
| Cut 1 duration | decoded 90–120 seconds inclusive; the provider's larger documented maximum is not accepted |

The canonical request checksum covers method, full URL, exact ordered logical
JSON, semantic profile, prompt version/hash, output contract, exact header names,
the deterministic quota-header presence flag and approved project-ID hash.
Authorization bytes and raw quota-project identity are bound through separate
non-secret identity/config evidence, never serialized.

## Future implementation invariants

The separate implementation issue phase must prove all of these before any
optional provider can be considered usable:

1. `TTSProvider` remains the sole product-facing synthesis interface.
2. Domain input is a semantic presenter ID plus an exact current
   `TTSConsumptionReceipt`; it contains no provider URL/model/voice/auth input.
3. An immutable adapter table maps only `meera -> Despina`, `myra -> Leda`, and
   `raj -> Achird`, with the exact model, locale, and EU hostname above.
4. Mock/local is the local/dev/test/CI default. Google requires an explicit
   server-side activation control and is disabled when any activation evidence
   is absent, stale, malformed, or contradictory.
5. Configuration is fully validated before secret screening and egress. No
   caller-controlled URL, model, voice, locale, auth mode, credential path,
   prompt style, retry policy, or output format reaches the adapter.
6. Only HTTPS port 443 to the exact EU hostname is allowed; redirects, proxies
   outside an approved deployment boundary, alternate IP literals, DNS rebinding
   mismatches, and global/US/India endpoints fail closed.
7. ADC or an equivalently governed workload identity is resolved outside source
   control. API keys, OAuth/refresh tokens, service-account JSON, credential
   files, and credential paths never enter product config, Git, APIs, logs, test
   fixtures, exceptions, traces, or evidence.
8. Narration text and style prompts are untrusted external egress. Secret/PII
   screening, approved-text checksum replay, UTF-8 byte limits, budget, quota,
   concurrency, deadline, and policy checks all pass before transport.
9. Responses are untrusted. Base64/schema/status/header checks precede bounded
   decode. Audio must be nonempty, complete, exact allowlisted format, within
   byte/duration/sample-rate/channel/bit-depth limits, and reject malformed,
   truncated, oversized, silent, near-silent, tone-only, or severely clipped
   signals. Validation uses bounded memory only; failed bytes are never written
   to a file, artifact store, log, trace or evidence package, and references are
   released immediately after a bounded failure checksum/outcome is recorded.
   No artifact is stored before every check passes.
10. Evidence binds tenant/actor/project, source run/request/trace, source and
    narration evaluations, exact approved narration version and checksum,
    presenter/profile, provider/engine/model/locale/endpoint, prompt/style and
    config hashes, request trace/ledger reservation/attempt, response artifact,
    decoded properties, retention state, and all checksums.
11. Edited, superseded, revoked, deleted, restored-with-drift, or stale narration
    approval fails closed. A prior artifact cannot satisfy a new narration.
12. A stable request fingerprint and state ledger preserve idempotency. One
    authorized fingerprint can enter egress once; completed replay returns the
    verified stored result without egress. Concurrent and conflicting requests
    fail closed.
13. Failures proven before egress release reservation. Accepted success commits
    it. Timeout/disconnect after possible egress is `BILLABLE_UNKNOWN`, holds
    reservation, forbids automatic retry/refund, and requires reconciliation.
14. Retries are bounded and allowed only when no bytes left the process or a
    future first-party contract explicitly proves TTS idempotency and billing
    safety. `429`/`5xx` alone does not prove safe replay.
15. Logs contain only allowlisted bounded metadata: event/code, trace/request
    fingerprint, semantic presenter, provider mode, endpoint region label,
    attempt count, elapsed bucket, byte/duration buckets, quota/cost state,
    validation outcomes, and non-content checksums. Text, prompt, payload,
    audio, credentials, tokens, headers, provider bodies, and URLs with query
    data are redacted.
16. Delete, pending-delete, tombstone, provider-retention-unknown, and local
    artifact deletion states are monotonic and checksum-bound. No missing
    provider deletion API is misrepresented as confirmed provider deletion.
17. Unit/API/CI use injected fake transports and fake identity/token providers.
    Tests assert zero network and zero real provider calls. No generated WAV or
    private screening evidence is committed.
18. No frontend Google hard-coding, cloning, reference audio, enrollment,
    biometric input, voice conversion, identifiable-person imitation, full
    narration, deployment, distribution, or release is implied.

## Failure matrix

| Boundary | Required failure | Spend state | Evidence |
|---|---|---|---|
| Authority/source/narration binding missing or stale | reject before adapter | none | bounded code plus binding hashes |
| Presenter other than three semantic IDs | reject before mapping | none | `PRESENTER_NOT_ALLOWLISTED` |
| URL/model/voice/locale/auth/output/style config drift | reject before identity or network | none | config digest and failed field code, never value |
| Secret/PII/policy screening failure | quarantine; no egress | none | screening policy/version/result |
| Budget/quota/concurrency/deadline unavailable | reject before egress | none | reservation outcome |
| Transport construction/DNS/TLS failure before write | fail; bounded retry only if proven pre-egress | released | attempt and pre-egress proof |
| Timeout/disconnect after possible write | fail closed; no automatic retry | `BILLABLE_UNKNOWN`, held | attempt, deadline, unknown marker |
| `401`/`403` | fail closed; no secret echo | according to accepted/unknown evidence | redacted auth code |
| `429`/`5xx` | fail closed; retry only with separately proven safety | held if egress possible | status class, Retry-After bucket |
| malformed/error/oversized provider body | reject; bounded memory is released and no body/audio persists | committed or unknown according to egress | response-size/checksum metadata only |
| invalid/silent/tone/clipped/truncated audio | reject; release bounded in-memory bytes immediately, with no file/artifact/quarantine persistence | committed | decoded measurements, failure checksum and destruction outcome |
| persistence/finalize failure after valid response | fail closed; recover staged state without re-egress | committed | staged artifact checksum/state |
| exact replay of completed fingerprint | return verified stored result | no new spend | replay result/checksums |
| conflicting or concurrent fingerprint | reject | no duplicate spend | conflict code |
| deletion requested | local delete/tombstone; provider retention remains factual | n/a | monotonic deletion evidence |

## TDD test mapping for the separate implementation phase

| Claim | First failing test level |
|---|---|
| semantic presenter mapping and all configuration allowlists | unit contract tests |
| stale approval/source/profile/config rejection before transport | unit service tests with spy transport |
| exact method/full URL, header names, request leaf set/order, profile prompt bytes/hash/version, voice mapping, LINEAR16/24 kHz config and byte limits | unit adapter golden-contract tests with fake token/HTTP transport |
| response-only `audioContent`, strict base64, WAV PCM16/24 kHz/mono and unknown-field rejection | unit adapter/audio tests with in-memory fixtures |
| no credential/key/path fields in config, response, errors or serialization | unit schema/redaction tests |
| timeout-after-egress held unknown; pre-egress failure releasable; no unsafe retry | unit ledger/state-machine tests |
| malformed/base64/empty/oversized/wrong-format/truncated/silent/near-silent/tone/clipped audio | unit binary fixtures generated in memory only |
| receipt-to-request-to-artifact-to-tombstone checksum graph | unit state/restore/mutation tests |
| zero-network mock/local default and disabled Google API behavior | API tests with injected fakes and a socket-deny fixture |
| idempotent replay, concurrency, crash recovery and duplicate-spend prevention | service/API tests with deterministic barriers/fault injection |
| exact 90–120-second artifact and OWNER listening | manual, exact-hash evidence outside CI after all blockers clear |

Effective locale/voice verification is human/source-governed unless Google adds
a machine-verifiable response contract. Tests prove requested fields and that no
unsupported effective-identity claim is serialized; they cannot prove the
provider honored the requested identity.

No automated test may call Google. Test fixtures must not contain real tokens,
private narration evidence, or generated screening WAVs.

## Separate future implementation allowlist and budget

This governance PR does not grant implementation authority. If this governance
PR and the prerequisite prompt-contract amendment are merged and the blockers
needed for coding are resolved, a fresh issue preflight and dedicated branch may
propose exactly these 21 paths, with a maximum 5,600 additions plus deletions and
no deletion credit:

1. `docs/governance/preflights/issue-368.json`
2. `backend/app/narration.py`
3. `backend/app/tts_provider.py`
4. `backend/app/stage6.py`
5. `tests/unit/test_cut1_narration.py`
6. `tests/unit/test_stage6_tts_provider.py`
7. `tests/unit/test_stage6_multilingual.py`
8. `tests/api/test_stage6_multilingual_api.py`
9. `scripts/quality/stage8_cut1_routes.py`
10. `tests/unit/test_stage8_cut1_routes.py`
11. `docs/ADR/0056-cut1-google-gemini-tts.md`
12. `docs/ARCHITECTURE.md`
13. `docs/SECURITY_AND_PRIVACY.md`
14. `docs/OBSERVABILITY_AND_COST.md`
15. `docs/QUALITY_GATES.md`
16. `docs/STAGE_ISSUE_PLAN.md`
17. `docs/STATUS.md`
18. `docs/TRACEABILITY.md`
19. `docs/THIRD_PARTY_NOTICES.md`
20. `docs/API_CONTRACT.md`
21. `docs/DATA_MODEL.md`

Justification: paths 2–4 extend the existing receipt/provider/Stage 6 seam;
paths 5–8 prove domain, adapter, service, and API contracts; paths 9–10 preserve
the exact route; paths 11–19 reconcile the already governing architecture,
security, cost, quality, status, traceability, and third-party records; paths
20–21 reconcile the public request/error contract and persisted ledger/artifact/
retention/checksum state model. No
frontend, `main.py`, Docker, CI workflow, new `local_tts.py`, dependency, lockfile,
or generated-media path is allowed.

If implementation proves a client dependency, separate adapter module, runtime
wiring path, or lockfile change necessary, this exact route is insufficient. The
executor must stop, provide first-party and license evidence, and obtain a new
OWNER-authorized preflight rather than silently widening it.

## Fresh-context adversarial review dispositions

The required independent issues-only review returned two blocking findings:

- **High — incomplete wire/audio contract. Resolved in governance.** The
  normative table now fixes the full unary method/URL, leaf allowlist, single
  speaker mapping, LINEAR16 24 kHz mono PCM16 WAV response, headers, strict
  unknown-field behavior and golden tests. Because approved prompt bytes cannot
  be derived from private request-manifest hashes, implementation is explicitly
  blocked on a prerequisite OWNER-authorized prompt-bytes/hash amendment rather
  than inventing a value.
- **Required — stale API/data contracts. Resolved in planning.** The future
  allowlist now contains `docs/API_CONTRACT.md` and `docs/DATA_MODEL.md`, is
  exactly 21 paths, and has a 5,600-line ceiling. Their request/error and
  ledger/artifact/retention/checksum reconciliations are mandatory.

No Critical or Medium finding was returned. The optional external cross-model
pass was not run because this autonomous execution had no explicit authority to
invoke an external model CLI.

### Final staged-diff review

The pre-commit issues-only review returned four blocking findings, all resolved
within the existing 14-path governance route:

- **High — moving route base.** Issue #368 now pins and tests exact accepted base
  `ef9cabc23762560912d99f10831241b8a65b869c`; later-main ancestry fails closed.
- **Required — provider substitution.** The source ledger and contract now state
  that exact request locale/voice does not prove effective output identity and
  block activation on a first-party guarantee or separately bound verification.
- **Required — ambiguous byte ceiling.** The normative contract now fixes UTF-8
  field counting at 4,000 bytes each and 5,000 bytes combined.
- **Required — invalid-audio retention conflict.** Failed provider bytes are
  bounded-memory only, never persisted or quarantined, and released after
  non-content failure evidence is recorded.

No cross-model CLI was invoked because the continuing autonomous execution did
not authorize an external model command. A post-fix fresh-context recheck is
required before commit.

## Skill and test-selection evidence

| Method | Concrete evidence or prevented action |
|---|---|
| Source-driven development | The source ledger ties each provider claim to an exact first-party URL, labels the generic/Gemini byte-limit conflict, separates TTS logging from unresolved abuse monitoring, and blocks SDK selection rather than inferring it. |
| API and interface design | Existing Stage 6 and Issue #237 interfaces were traced; the contract retains one provider-neutral interface, semantic IDs, immutable adapter mapping, typed failures, no provider-native frontend/domain fields, and substitutability. |
| Security and hardening | Threat boundaries cover credential injection, SSRF/redirect/DNS, untrusted content and audio, secret/PII egress, duplicate spend, log leakage, stale authority, retention, and deceptive identity. |
| Planning and task breakdown | Governance and implementation are separate gates; the future 21-path route, 5,600-line budget, prerequisite prompt contract, invariants, blockers, failure matrix, and test mapping define ordered stop points. |
| Specification-driven development | This document and ADR are the normative contract before runtime code; every external effect has preconditions, state transitions, failure behavior, and observable evidence. |
| Test-driven development planning | Each future claim starts with a named failing unit/API/manual test level; injected transports and socket denial prove zero paid calls rather than treating mocks as evidence. |
| Doubt-driven/adversarial review | A fresh-context issues-only review is required before commit; every Critical/High/Medium/Required finding must be resolved in scope or execution stops. |
| Code-review and quality planning | The governance route is exactly 14 files/3,200 charged lines; runtime/dependency/media paths are forbidden; `make quality`, focused tests, guardrails, diff and secret review must pass at latest head. |

Rejected options: retaining eSpeak would contradict OWNER authority; a new
product-facing Google abstraction would duplicate Issue #237; frontend voice
selection would leak vendor details; API keys/service-account JSON would violate
credential policy; real-call tests would spend and egress; automatic retry after
an ambiguous timeout could duplicate spend; treating EU as India residency or
reference acceptance as legal/full-narration approval would make unsupported
claims.

## Reviewer pass/fail boundary

Pass only if the branch contains governance and governance tests only, the exact
14-path route and budget pass, every source fact is supported or explicitly
unresolved, mock/local remains default, no real call or credential/audio path
exists, and latest-head CI plus a non-author human review are eligible.

Fail on any runtime behavior, dependency, credential, audio, frontend, workflow,
activation, call, deployment, distribution, release, issue-close, silent route
widening, unsupported legal/privacy claim, or unresolved Required-or-higher
governance finding. Merge is not authorized by this document.
