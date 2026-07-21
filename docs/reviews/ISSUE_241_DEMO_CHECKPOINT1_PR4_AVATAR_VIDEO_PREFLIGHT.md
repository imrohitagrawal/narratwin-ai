# Issue 241 Demo Checkpoint 1 PR4 Avatar/Video Preflight

Accessed date for source facts: 2026-07-21.

## Objective

Demo Checkpoint 1 PR4 adds an optional server-side avatar/video provider adapter
boundary for Checkpoint 1 only. Mock/local avatar/video remains the default for
local/dev/test/CI. Optional provider egress must stay disabled unless provider
configuration, env-only key loading, quota reservation/refund, timeout/retry,
retry cap, duplicate-spend prevention, output validation, retention/deletion
evidence, disclosure, and redacted observability gates pass first.

The adapter accepts an approved source run, evaluated script, citation refs,
audience/language metadata, and validated TTS/audio metadata when present. It
produces only validated media artifact metadata and disclosure/evidence surfaces
until a human owner explicitly approves any real provider call in writing.

## Non-Goals

- No hosted demo access system, invite flow, public URL, deployment, or demo
  polish.
- No cloned voice, cloned face/avatar, digital twin, replica-profile creation,
  real-person likeness workflow, Product Mode 2, public synthetic-media
  distribution, or production-readiness claim.
- No provider account setup, dashboard configuration, paid plan activation,
  wallet funding, paid spend, provider SDK installation, real provider calls in
  CI, or real provider test calls without explicit written owner approval.
- No broad refactors outside the avatar/video provider boundary.
- No PR5 hosted access/quota/retention polish.

## Changed-File Allowlist

The issue #241 branch may change only these paths:

- `docs/governance/preflights/issue-241.json`
- `docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/API_CONTRACT.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `backend/app/avatar_video_provider.py`
- `backend/app/stage7.py`
- `backend/app/main.py`
- `tests/unit/test_stage7_avatar_video_provider.py`
- `tests/unit/test_stage7_avatar.py`
- `tests/api/test_stage7_avatar_api.py`

Checker support rejects unrelated files including frontend files, GitHub
workflow files, Dockerfiles, dependency manifests, Stage 6 TTS files, and
`docs/LAUNCH_LEVELS.md`.

## Official Source Facts

| Provider | Facts used for PR4 boundary | Source |
|---|---|---|
| HeyGen | API use requires `X-Api-Key`; generation is async with polling and failed/completed states; 401 means auth failure; 429 includes `Retry-After`; Pay-As-You-Go supports 10 concurrent video jobs; script/audio limits and asset URL constraints exist; prompt-to-avatar is described as fully synthetic and no real person depicted; Digital Twin requires proof of consent. | `https://developers.heygen.com/docs/quick-start`, `https://developers.heygen.com/docs/usage-limits`, `https://developers.heygen.com/docs/create-avatar`, `https://developers.heygen.com/docs/avatar-consent`, `https://developers.heygen.com/docs/pricing` |
| Tavus | API keys are sent as `x-api-key` and must not be exposed client-side; generated video requests require a `replica_id` and either script or audio; statuses include queued/generating/ready/deleted/error; delete supports `hard=true` for irrevocable asset deletion; stock replicas exist on plans, while custom replicas are real-human likeness assets that require rights/permissions; video overage is pay-as-you-go on paid tiers. | `https://docs.tavus.io/api-reference/authentication`, `https://docs.tavus.io/api-reference/video-request/create-video`, `https://docs.tavus.io/api-reference/video-request/get-video`, `https://docs.tavus.io/api-reference/video-request/delete-video`, `https://docs.tavus.io/sections/faces/overview`, `https://docs.tavus.io/sections/faces/face-faqs`, `https://www.tavus.io/pricing` |
| D-ID | Talk creation accepts an HTTPS/S3 source image and required text or audio script; Talk status is polled by ID; API use requires a key and valid account credits; API credits come from the same balance as Studio; D-ID agreements require fees under order terms; synthetic marks/watermarks must not be hidden or removed without written approval. | `https://docs.d-id.com/reference/createtalk`, `https://docs.d-id.com/reference/gettalk`, `https://www.d-id.com/faqs/`, `https://www.d-id.com/eula/`, `https://www.d-id.com/pricing/api/` |

Provider selection decision: PR4 does not select a paid provider/model for active
egress. No real provider call is approved by PR4. The code path remains
provider-neutral, transport-injected, and disabled by default; tests use
fake/local transports only.

D-ID egress remains blocked unless a D-ID-approved synthetic-marking
policy/version is recorded. Synthetic mark metadata must be present, preserved,
and not configurable off. Equivalent provider-specific watermark or disclosure
requirements must be preserved for every provider.

Provider asset classes must use a provider asset provenance enum. The only PR4
default-eligible classes are fully synthetic no-real-person and provider-stock
licensed non-identifiable. Prompt-with-existing-avatar references, custom
replica, Digital Twin, user-provided likeness image, cloned identity, and any
other real-person likeness asset are rejected before transport call unless a
separate consent/provenance issue approves them.

## Adapter Interface Contract

Typed input schema:

- source run ID
- trace ID
- language
- audience
- script checksum
- sanitized script reference, never raw script in logs
- citation refs
- evaluation ID/status/checksum
- optional TTS/audio checksum and MIME metadata
- provider asset provenance enum
- idempotency key
- provider capability/config model

Typed output schema:

- provider ID/model/version
- provider job ID
- provider job states: queued, running, succeeded, failed, deleted,
  deletion_pending, deletion_failed, unknown_after_accept
- artifact checksum, MIME, extension, byte size, and safe storage reference
- disclosure text/version and provider synthetic-mark metadata
- retention/deletion state and provider-side deletion evidence
- redaction-safe observability metadata only

Failure codes:

- `AVATAR_VIDEO_PROVIDER_DISABLED`
- `AVATAR_VIDEO_PROVIDER_KEY_MISSING`
- `AVATAR_VIDEO_PROVIDER_KEY_INVALID`
- `AVATAR_VIDEO_EVAL_NOT_APPROVED`
- `AVATAR_VIDEO_BINDING_MISMATCH`
- `AVATAR_VIDEO_CITATION_MISMATCH`
- `AVATAR_VIDEO_LIKENESS_ASSET_REJECTED`
- `AVATAR_VIDEO_PROVIDER_TIMEOUT`
- `AVATAR_VIDEO_RETRY_CAP_EXCEEDED`
- `AVATAR_VIDEO_PROVIDER_RESPONSE_INVALID`
- `AVATAR_VIDEO_UNSAFE_URL`
- `AVATAR_VIDEO_ARTIFACT_INVALID`
- `AVATAR_VIDEO_QUOTA_EXHAUSTED`
- `AVATAR_VIDEO_DUPLICATE_SPEND_BLOCKED`
- `AVATAR_VIDEO_DELETION_EVIDENCE_UNAVAILABLE`
- `AVATAR_VIDEO_LOG_REDACTION_FAILED`

Idempotency scope: source run ID, trace ID, language, audience, script checksum,
evaluation ID/status/checksum, citation refs, optional TTS/audio checksum,
provider ID/model/version, provider asset provenance enum, and requested artifact
format. If provider create succeeds remotely, local call times out, or the
adapter cannot prove whether the provider accepted work, the quota reservation
moves to pending/unknown quota hold. The adapter must not issue a second create
unless provider-level idempotency is proven by official source facts and tests.

Provider billing-policy fixtures must cover billable unit, duration cap, per-run
dollar ceiling, balance/credit errors, retry/dedup behavior, and whether retries
can create additional billable jobs. Real egress remains blocked without this
provider-specific policy.

Provider-specific deletion/retention source facts are required before enabling a
provider. Tests must reject providers lacking hard-delete or auditable deletion
evidence.

Observability requires structured log event names, bounded-cardinality labels,
request/correlation propagation, and allowlisted fields only: event, trace_id,
provider ID, bounded status class/code, retry attempt, quota outcome, provider
job state, artifact validation result, and deletion evidence state.

## Old-Behavior and Failure Proof

Existing Stage 7 local/mock avatar rendering can produce consent-bound demo
exports and placeholder video metadata without external provider egress. Existing
external stubs fail closed. PR4 must preserve local/mock success, preserve
predecessor evidence surfaces #162, #163, #166, #167, and #168, and add optional
provider-boundary behavior only behind disabled-default gates.

Before implementation, expected failing proofs are:

- No branch-specific allowlist exists for issue #241.
- No avatar/video provider boundary module exists.
- No tests prove avatar/video provider disabled default, quota refund,
  duplicate-spend prevention, unsafe URL rejection, duplicate JSON key rejection,
  disclosure, retention/deletion evidence, or redacted logging.

## Invariant and Test Matrix

| Invariant | Required proof |
|---|---|
| Provider egress disabled by default | Unit test expects provider disabled error and no transport calls. |
| Missing or invalid key blocks egress | Unit tests cover absent key and malformed key. |
| Failed/stale eval blocks media generation | Stage 7 unit/API tests cover failed eval, stale eval, and stale source run. |
| Source/eval/media binding is complete | Tests assert source run ID, trace ID, language, audience, script checksum, citation refs, evaluation ID/status/checksum, optional TTS/audio checksum, provider ID/model/version, provider job ID, artifact checksum, disclosure/version, retention/deletion state. |
| Citation mismatch blocks generation | Unit/API tests mutate citation refs and expect rejection before egress. |
| Injection surfaces are rejected | Tests cover script, transcript, and provider-output prompt-injection markers. |
| Provider timeout/failure/retry cap is bounded | Fake transport tests cover timeout, retryable status, retry cap, retry-after metadata, and no unbounded polling. |
| Unsafe provider URLs are rejected | Tests cover non-HTTPS, localhost/private hosts, redirects, malformed URLs, unsafe extensions, resolved A/AAAA records, `169.254.169.254`, IPv6 loopback/link-local, DNS rebinding, redirect denial, and raw URL redaction before storage/display/download. |
| Malformed provider responses are rejected | Tests cover malformed JSON, duplicate JSON keys, unexpected fields, missing status/job/artifact fields, and failed job states. |
| Artifact validation is strict | Tests cover MIME/extension mismatch, oversized artifact, checksum mismatch, and unsupported content type. |
| Quota and spend controls are pre-egress | Tests cover quota exhaustion, reservation before create, refund on failed job, commit on valid artifact, duplicate-spend prevention, provider create succeeds remotely, local call times out, pending/unknown quota hold, provider-level idempotency, billable unit, duration cap, per-run dollar ceiling, and balance/credit errors. |
| Retry behavior is bounded | Tests cover retry cap, invalid/negative/huge/HTTP-date Retry-After parsing, clamp behavior, retry-after metadata, and no real sleeps in tests. |
| Retention/deletion evidence exists | Tests cover tombstone state, provider-side deletion evidence, provider-specific deletion/retention source facts, and rejection of providers lacking hard-delete or auditable deletion evidence without real provider calls. |
| Disclosure remains visible | Unit/API tests assert synthetic disclosure text/version survives metadata serialization. |
| Likeness assets are denied before egress | Provider-boundary tests accept only fully synthetic no-real-person or provider-stock licensed non-identifiable provenance and reject prompt-with-existing-avatar references, custom replica, Digital Twin, user-provided likeness image, cloned identity, and real-person likeness assets before transport call. |
| Logging is redacted and useful | Tests assert logs omit raw prompts, scripts, transcripts, provider payloads, URLs, keys, and media bytes while retaining structured log event names, allowlisted fields, trace_id, provider ID, bounded status class/code, retry attempt, quota outcome, and artifact validation result. |
| Hosted-demo/clone/product-mode non-goals hold | Checker tests and docs preserve forbidden hosted access, invite, public URL, demo polish, Product Mode 2, and clone surfaces. |

## Claim Mapping

| Claim | Proof type |
|---|---|
| Mock/local remains default | Executable unit/API tests and `make quality`. |
| Optional provider adapter is disabled unless configured | Executable unit tests. |
| Provider facts are current and official | Source facts table above. |
| Media metadata binding is complete | Executable unit/API tests. |
| Provider outputs are untrusted | Executable validation tests. |
| Quota/refund/retry/timeout/duplicate-spend controls exist | Executable unit tests. |
| Retention/deletion/tombstone evidence exists | Executable unit tests plus docs. |
| Redacted observability omits sensitive payloads | Executable unit tests. |
| No real calls, spend, hosted demo, clone, or Product Mode 2 | Checker allowlist, docs, and PR human checklist rows. |

Expected executable files for these claims include
`tests/unit/test_stage7_avatar_video_provider.py`,
`tests/unit/test_stage7_avatar.py`, and `tests/api/test_stage7_avatar_api.py`.

## Fan-Out Review Findings and Dispositions

| Area | Finding | Disposition |
|---|---|---|
| Cost/provider terms | Source facts, paid-spend blockers, marking/watermark policy, provider billing units, and no-real-call terms could false-pass if only the path allowlist is checked. | Add PR4 semantic checker markers and mutation tests before implementation. |
| Security/privacy/consent | Likeness, Digital Twin, custom replica, prompt-with-reference, and user-provided image denial must be executable, not only prose. | Require provider-boundary tests that reject unsafe asset provenance before transport call. |
| Eval/grounding/citations | Eval/source/media/citation binding and disclosure visibility need executable proof, and hosted-demo PR5 work must remain forbidden. | Keep required Stage 7/API tests and checker markers for failed/stale eval, citation mismatch, disclosure, hosted access, invite, public URL, and Product Mode 2 non-goals. |
| UX/demo/recruiter flow | Allowed API files could accidentally add hosted access or demo polish. | Keep frontend files forbidden; require API contract updates if `backend/app/main.py` changes and negative checks for hosted access, invite, public URL, deployment, and demo polish. |
| Performance/reliability/quota | Timeout after accepted create can cause duplicate paid jobs; Retry-After parsing can hang or explode backoff. | Require pending/unknown quota hold, no second create without provider-level idempotency, retry cap, Retry-After clamp, and no real sleeps in tests. |
| Test/quality/CI | Branch #241 had no semantic preflight checker and no near-match fail-closed regression. | Add `check_issue241_avatar_video_preflight`, mutation tests, and #241 near-match branch rejection. |
| Governance/taste-check | The branch dispatcher is brittle. | Fix #241 near-match now; defer table-driven dispatcher cleanup to a separate process issue. |
| API/interface design | Adapter contract lacked typed schemas, job states, error taxonomy, idempotency scope, and provider capability/config model. | Add Adapter Interface Contract before implementation. |
| Observability/logging/redaction | Redaction-by-absence is not enough; telemetry must remain useful and bounded. | Require structured log event names, bounded-cardinality fields, trace_id propagation, quota/retry/artifact/deletion lifecycle fields, and negative leak tests. |

## Skill and Evidence Ledger

Invoked skills: `planning-and-task-breakdown`, `spec-driven-development`,
`test-driven-development`, `source-driven-development`,
`security-and-hardening`, `code-review-and-quality`,
`git-workflow-and-versioning`, `taste-check`, and
`doubt-driven-development`.

Rejected options:

- Provider SDK installation: rejected because PR4 can use an injected transport
  boundary and no SDK should be installed without explicit justification.
- Real provider calls: rejected because source facts and safeguards are not a
  substitute for written owner approval.
- Tavus custom replica, HeyGen Digital Twin, D-ID cloned identity flows: rejected
  because cloned identity and real-person likeness workflows are out of scope.
- Hosted demo access/retention polish: rejected because PR5 owns that scope.

## Stop Rule

Implementation may start only after this document, issue #241 preflight, branch
allowlist checker support, regression tests, source facts, and fan-out review
findings/dispositions are complete.
