# Issue 237 Demo Checkpoint 1 PR3 TTS Preflight

Issue: #237  
Branch: `phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts`  
Created: 2026-07-21  
Owner role: Principal Staff AI Product Engineer

## Objective

Add a server-side TTS provider abstraction for Demo Checkpoint 1 PR3. The slice
keeps the existing mock/local TTS provider as the default for local/dev/test/CI,
adds an optional real TTS adapter boundary, and proves that provider egress is
impossible unless disabled-default, key, source/eval, language, script length,
quota, retry/timeout, duplicate-spend, output validation, retention/deletion,
and redaction controls all pass.

## Non-goals

- No avatar/video provider implementation.
- No hosted deployment, hosted access system, public URL, or demo access quota
  implementation.
- No provider account setup, dashboard configuration, paid plan activation,
  wallet funding, paid spend, real provider test calls, or real provider calls
  in CI.
- No provider SDK installation unless a later issue-linked plan justifies it.
- No cloned voice, cloned face/avatar, Product Mode 2, public synthetic-media
  distribution, or production-readiness claim.
- No frontend, Docker, CI workflow, database, Stage 7 avatar/video, or hosted
  deployment changes.

## Brainstorming To Decisions

- Candidate shape A: install a provider SDK. Rejected for PR3 because the local
  architecture already has an injectable server-side provider boundary and SDK
  installation increases dependency, notices, and secret-handling surface.
- Candidate shape B: generic provider framework for all media providers.
  Rejected because PR3 is TTS-only and must not absorb avatar/video work.
- Candidate shape C: HTTP-client adapter with injected fake transport and
  mock/local default. Selected because it proves the egress boundary while
  keeping tests provider-free and paid-spend-free.
- Candidate shape D: direct real provider integration tests. Rejected because
  PR3 forbids real calls without fresh plan plus explicit written human-owner
  approval.
- Candidate shape E: fall back silently to mock on real-provider config errors.
  Rejected for named real providers because it hides egress posture; named real
  provider requests must fail closed before egress when disabled, unkeyed,
  invalid, unsupported, over quota, or unsafe.

## Exact Changed-file Allowlist

- `docs/governance/preflights/issue-237.json`
- `docs/reviews/ISSUE_237_DEMO_CHECKPOINT1_PR3_TTS_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/API_CONTRACT.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `backend/app/tts_provider.py`
- `backend/app/stage6.py`
- `backend/app/main.py`
- `tests/unit/test_stage6_tts_provider.py`
- `tests/unit/test_stage6_multilingual.py`
- `tests/api/test_stage6_multilingual_api.py`

Checker support added in `scripts/quality/check_phase1_closure_docs.py` with
`test_issue_237_branch_has_exact_scope_allowlist`. The regression rejects
`backend/app/stage7.py`, `frontend/src/app/page.tsx`,
`.github/workflows/quality-gates.yml`, and `backend/Dockerfile`.

## Source Facts

Accessed date for every source below: 2026-07-21. All URLs are official provider
documentation or official provider terms/pricing pages.

### ElevenLabs Candidate Facts

| Area | Fact | Source |
| --- | --- | --- |
| Capability/languages | ElevenLabs TTS turns text into audio; listed models adapt across 32 languages. Free-tier users cannot access the voice library through the API. | `https://elevenlabs.io/docs/overview/capabilities/text-to-speech` |
| Model/limits | Flash v2.5 is described as ultra-low latency, 32 languages, 40,000 character limit. Multilingual v2/v3 is listed with 32 languages and 40,000 character limit. | `https://elevenlabs.io/pricing/api` |
| Pricing | Flash/Turbo TTS: $0.05 per 1K characters. Multilingual v2/v3: $0.10 per 1K characters. Prices exclude taxes, levies, and duties. | `https://elevenlabs.io/pricing/api` |
| Authentication/key handling | API requests use `xi-api-key`; keys authenticate requests and track quota. Keys are secrets and must not be exposed in client-side code. Key restrictions include scope, credit quota, and IP allowlist. | `https://elevenlabs.io/docs/api-reference/authentication` |
| Request/response | The create-speech endpoint is `POST /v1/text-to-speech/:voice_id`, accepts text/model fields, and returns audio. | `https://elevenlabs.io/docs/api-reference/text-to-speech/convert` |
| Retention | `enable_logging=false` uses zero-retention mode but is enterprise-only. Default history preservation is on when zero retention is not active. | `https://elevenlabs.io/docs/api-reference/text-to-speech/convert`; `https://elevenlabs.io/docs/eleven-api/resources/zero-retention-mode` |
| Deletion | All customers can delete generations at any time; deletion removes the corresponding audio and text from the provider database, while debugging/moderation logs may remain. The history delete endpoint is `DELETE /v1/history/:history_item_id`. | `https://elevenlabs.io/docs/eleven-api/resources/zero-retention-mode`; `https://elevenlabs.io/docs/api-reference/history/delete` |
| Retry/rate limits | 429 means rate or concurrency limit exceeded. Rate limiting guidance says to implement exponential backoff; concurrency guidance says wait for current requests to complete. | `https://elevenlabs.io/docs/eleven-api/resources/errors` |
| Concurrency | Subscription plan determines simultaneous request processing and queue priority; HTTP requests count individually toward concurrency. | `https://elevenlabs.io/docs/overview/models` |
| Commercial/public-use restrictions | The prohibited use policy forbids unauthorized, deceptive, or harmful impersonation, including replicating another person's voice without consent/legal right or deceiving others about AI generation. Free users may not use services for commercial purposes. | `https://elevenlabs.io/use-policy` |
| Voice clone restrictions | Professional Voice Cloning requires a verification step before training to ensure permission to use the voice. The voice owner must read CAPTCHA text aloud and submit a recording. | `https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/professional-voice-cloning` |

PR3 selection decision: implement an ElevenLabs-shaped HTTP adapter boundary
only. It remains disabled by default, uses no SDK, makes no real calls in tests,
does not select a production voice/model for runtime defaults, and requires
explicit config plus injected transport to egress.

### Gemini Candidate Facts

| Area | Fact | Source |
| --- | --- | --- |
| Capability/status | Gemini API can transform text input into single-speaker or multi-speaker audio; Gemini TTS is Preview. TTS models accept text-only inputs and produce audio-only outputs. | `https://ai.google.dev/gemini-api/docs/speech-generation` |
| Model/limits | `gemini-3.1-flash-tts-preview` accepts text input, returns audio output, has 8,192 input token limit and 16,384 output token limit, and does not support caching, search grounding, URL context, function calling, or structured outputs. | `https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview` |
| Pricing | Gemini 3.1 Flash TTS Preview standard tier lists free tier as free of charge; paid tier is $1.00 per 1M text input tokens and $20.00 per 1M audio output tokens. Audio tokens correspond to 25 tokens per second of audio. | `https://ai.google.dev/gemini-api/docs/pricing` |
| Data-use posture | The same Gemini pricing table marks free-tier submitted data as used to improve products and paid-tier submitted data as not used to improve products. | `https://ai.google.dev/gemini-api/docs/pricing` |
| Authentication/key handling | Gemini docs recommend setting `GEMINI_API_KEY` or `GOOGLE_API_KEY` as environment variables. | `https://ai.google.dev/gemini-api/docs/api-key` |
| Rate/spend limits | Gemini API enforces spend-based limits in addition to RPM/TPM for some tiers; hitting spend-based limits returns `429 RESOURCE_EXHAUSTED`. | `https://ai.google.dev/gemini-api/docs/rate-limits` |
| Use restrictions | Gemini API Additional Terms require age 18+ and state the services are for developers building with Google AI models for professional or business purposes. | `https://ai.google.dev/gemini-api/terms` |

PR3 decision: do not implement a Gemini adapter in PR3. Gemini remains a
source-fact-reviewed deferred candidate because Preview status, token/audio
pricing, and Interactions API shape would add a second provider contract and
increase scope beyond the narrow TTS adapter proof.

## Positive Claims

- C1-TTS-001: Mock/local TTS remains the default provider for local/dev/test/CI.
- C1-TTS-002: A named real TTS provider request cannot egress unless provider
  config is explicitly enabled and valid.
- C1-TTS-003: Provider egress is preceded by source/eval/citation binding,
  language support, script-length cap, quota reservation, retry cap, timeout,
  duplicate-spend prevention, and redacted observability setup.
- C1-TTS-004: Provider outputs are untrusted; malformed responses, unsafe URL
  payloads, oversized audio, unsupported MIME, bad checksums, and source/eval
  mismatches fail closed before storage/API serialization.
- C1-TTS-005: TTS artifacts are bound to source run, trace ID, language,
  audience, script checksum, citation/eval metadata, provider ID/model/version,
  provider history item where available, and artifact checksum.
- C1-TTS-006: TTS artifact deletion records tombstone local artifact metadata
  and records provider-side deletion evidence status without requiring a real
  provider call in local/dev/test/CI.
- C1-TTS-007: Logs and observability metadata never include raw uploads,
  prompts, TTS text, provider payloads, audio bytes, or provider secrets.

## Negative Invariants

- NONGOAL-AVATAR-VIDEO: No avatar/video provider code or Stage 7 changes.
- NONGOAL-HOSTED: No hosted deployment, hosted access system, public URL, or
  invite/access-system implementation.
- NONGOAL-SPEND: No provider setup, paid plan activation, wallet funding,
  selected production voice/model default, real provider calls, or paid spend.
- NONGOAL-CLONE: No cloned voice, cloned face/avatar, or voice-clone flow.
- NONGOAL-PRODUCTION: No production-readiness, Product Mode 2, or public
  synthetic-media distribution claim.
- NONGOAL-SDK: No provider SDK installation in PR3.

## Invariant And Test Matrix

| ID | Claim/boundary | Evidence owner |
| --- | --- | --- |
| C1-TTS-001 | Default service/API uses mock provider and no external transport. | `tests/unit/test_stage6_multilingual.py`, `tests/api/test_stage6_multilingual_api.py` |
| C1-TTS-002 | Disabled/missing/invalid key states fail before egress for named real provider. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-003A | Quota exhaustion blocks before egress; reservation occurs before fake transport call. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-003B | Failed provider job refunds reservation when no billable provider artifact is accepted. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-003C | Retry cap and timeout are enforced through fake transport. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-003D | Idempotency replay prevents duplicate provider spend for equivalent request. | `tests/unit/test_stage6_multilingual.py`, API idempotency tests |
| C1-TTS-003E | Unsupported language and provider script-length cap block before egress. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-004A | Malformed provider response fails closed. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-004B | Unsafe URL-shaped provider response is rejected as unsupported/malformed. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-004C | Oversized audio artifact fails closed. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-004D | Source/eval mismatch and failed eval block real TTS before egress. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-004E | Prompt-injection-like TTS text is treated as untrusted text and does not alter provider config/egress posture. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-005 | Artifact manifest/metadata bind source run, trace ID, language, audience, script checksum, citation/eval metadata, provider ID/model/version/history ID, and artifact checksum. | Unit/API assertions and metadata fixture decoding |
| C1-TTS-006 | Deletion path tombstones local artifact metadata and records provider-side deletion evidence status. | `tests/unit/test_stage6_multilingual.py` |
| C1-TTS-007 | Logs redact raw text, provider payloads, audio bytes, and secrets. | `tests/unit/test_stage6_multilingual.py` with `caplog` |
| SRC-ELEVEN-* | Provider pricing, key handling, request limits, retention/deletion, retry/rate, public-use/clone restrictions. | Official source facts table above |
| SRC-GEMINI-* | Deferred provider capability, pricing, limits, key handling, terms, and rate/spend limits. | Official source facts table above |
| HUMAN-REAL-CALLS | Any real provider test call requires explicit written human-owner approval on this issue/PR after a fresh safeguards plan. | Human-only checklist; no real calls planned |
| NONGOAL-* | Explicitly forbidden PR3 scopes. | Non-goals and checker allowlist |

## Old-behavior And Failure Proof

Before implementation, PR3 will add failing tests for the named real-provider
contract while preserving existing green tests for mock/local behavior:

- Existing behavior proof: `test_requested_voice_provider_falls_back_to_mock_provider`
  and the API fallback test prove unknown `external` still falls back to mock
  for the legacy local/demo posture.
- RED proof target: new tests for named `elevenlabs` disabled/missing/invalid
  key, quota, timeout, malformed response, oversized artifact, duplicate-spend,
  failed eval, prompt injection, deletion/tombstone, and redaction must fail
  against the current first-commit baseline because no real TTS adapter config,
  quota ledger, audio artifact binding, or deletion path exists yet.
- Mutation proof target: temporarily allowing real-provider egress without
  quota reservation, without redaction, or with malformed provider output should
  trip the corresponding unit test.

## Skill And Test Selection Evidence

| Change area | Invoked/selected | Rejected/prevented | Evidence required |
| --- | --- | --- | --- |
| Issue/branch/first commit | git-workflow-and-versioning | Direct `main` commit; branch before issue; first commit with extra files | Issue `#237`, branch `phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts`, first commit `9ae61c2` contains only `docs/governance/preflights/issue-237.json` |
| Scope boundary | planning-and-task-breakdown, spec-driven-development | Avatar/video, hosted access, frontend, Docker, CI workflow, broad media-provider framework | Exact changed-file allowlist plus checker regression for #237 exact branch and near-match fail-closed |
| Source facts | source-driven-development | Non-official provider blogs, stale remembered pricing, undocumented free-tier assumptions | Official ElevenLabs and Gemini URLs in source facts table, accessed 2026-07-21 |
| Provider adapter | api/interface design via fan-out, taste-check | Provider SDK install; generic all-provider abstraction; exposing provider-native payloads directly | Narrow `backend/app/tts_provider.py`, provider-neutral manifest, fake transport tests, no dependency changes |
| Config/security | security-and-hardening, test-driven-development | Silent fallback for named real provider; client-side key exposure; cloned/private/custom voice egress without provenance | Disabled/missing/invalid key tests, stock/non-cloned provenance config tests, redaction tests |
| Quota/reliability | test-driven-development, performance fan-out | Provider call before quota reservation; unlimited retry; no timeout; duplicate spend after retry/crash | RED tests for reservation before fake transport, refund, retry cap, timeout, backpressure, persisted RUNNING state before egress |
| Grounding/citations | test-driven-development, eval fan-out | TTS from FAILED/UNKNOWN/absent eval; extra citation markers; manifest missing source/eval binding | RED tests for failed/unknown/missing checksum, exact citation sequence, manifest source/eval/citation binding |
| Output validation | security-and-hardening, test-driven-development | Trusting provider URL/JSON; storing oversized audio; weakening mock manifest validation | Fake malformed response, unsafe URL-shaped response, oversized audio, MIME/checksum tests |
| Retention/deletion | security-and-hardening, spec-driven-development | Raw audio retained after deletion; provider deletion path without evidence state | Tombstone/delete tests for local artifact metadata and provider-side deletion evidence status |
| Observability | security-and-hardening, code-review-and-quality | Raw TTS text, provider request/response, audio bytes, keys, or poisoned restore values in logs | `caplog` tests for provider redaction and restore warning sanitization |
| Quality gate | code-review-and-quality | PR marked ready without local validation or forced PR guardrails | Validation command matrix and PR-body evidence |

## Fan-out Review Prompt Set

Fresh-context reviewers must attack this exact plan before implementation:

1. Cost/provider terms: find any path that could spend money, violate terms,
   rely on free-tier/public-use assumptions, or omit paid/free restrictions.
2. Security/privacy/consent: find any raw text, secret, prompt, provider
   payload, consent, clone, or deletion risk.
3. Eval/grounding/citations: find ways TTS can be generated from unsupported or
   mismatched source/eval/citation state.
4. UX/demo/recruiter flow: find any scope creep into hosted access, public URLs,
   public distribution, or demo polish.
5. Performance/reliability/quota: find missing timeout, retry, duplicate-spend,
   reservation/refund, concurrency, oversized-artifact, or provider-failure
   controls.
6. Test/quality/CI: find untested claims, weak old-behavior proof, or any test
   that could make real provider calls.
7. Governance/taste-check: find over-broad files, abstractions, SDK installs,
   status overclaims, missing first-commit evidence, or direct-main risks.
8. API/interface design: find unstable or leaky provider abstractions and API
   response fields that expose secrets/raw payloads or mix TTS with avatar.
9. Observability/logging/redaction: find any log/metadata event that can include
   raw TTS text, uploads, prompts, provider payloads, audio bytes, or secrets.

## Fan-out Findings And Dispositions

Completed before implementation. Real blockers below are promoted into the PR3
test/implementation contract and must be fixed before the PR can be marked ready.

| Angle | Finding | Disposition |
| --- | --- | --- |
| Cost/provider terms | Named real providers currently fall back to mock and can mask disabled/missing key/quota failures. Gemini deferred facts originally missed free-tier data-use posture. No current paid-call path exists. | Add named-provider fail-closed tests and implementation; Gemini data-use fact added above; keep Gemini unimplemented and no real calls planned. |
| Security/privacy/consent | Service boundary can synthesize from weak eval state; no non-clone voice provenance gate; no deletion/tombstone path; real audio must be separate from mock manifest; key handling needs concrete redaction tests. | Add service-layer PASSED/non-empty evidence/evaluator-supplied checksum gates for named real providers; require stock/non-cloned voice provenance in config; add deletion/tombstone service/API path; model manifest/audio separately; add key/log/metadata/API/persisted-state redaction tests. |
| Eval/grounding/citations | External TTS can run before provider mode validation and from FAILED/UNKNOWN eval; translation validation allows extra citation markers; voice manifest lacks source/eval/citation binding. | Validate provider config and source/eval/citations before synthesize; reject extra/altered citation marker sequence; bind manifest to source run, trace, eval ID/status/checksum, citation indexes/count, and script checksum. |
| UX/demo/recruiter flow | No blocker. Residual risk is allowed docs accidentally adding hosted/public/prod wording. | Preserve non-goals and run final PR review for hosted/public/production wording. |
| Performance/reliability/quota | No durable reservation before spend, no quota ledger, no retry/timeout/backpressure, no real response validation. | Persist RUNNING/reservation before provider call; add quota reserve/refund ledger; add bounded retry/backoff/timeout/concurrency handling; validate audio bytes/MIME/size/checksum/history metadata before storage. |
| Test/quality/CI | PR3 claims not yet backed by RED tests; no egress tripwire; #237 near-match branch fell through to process scope; Stage 6 validation command was placeholder. | Add RED tests before implementation; add provider-test fake transport/no-network guard; #237 near-match branch now fails closed; exact Stage 6 validation command added below. |
| Governance/taste-check | Initial preflight overclaimed fan-out completion while some angles were pending; `required` scope was used like an allowlist; implementation scope forced provider work into broad modules; skill evidence ledger was too ceremonial. | All fan-out angles are now complete; `issue-237.json` keeps mandatory proof paths in `required` and optional impacted paths in `allowed_prefixes`; `backend/app/tts_provider.py` and `tests/unit/test_stage6_tts_provider.py` added for narrow provider logic; skill ledger expanded below. |
| API/interface design | Real TTS Stage 6 output remains incompatible with Stage 7's local-only bundle contract; validators are mock-only; `voice.artifact`/`artifacts.voiceManifest` duplication is ambiguous for real audio; spend-bearing reservations need a separate ledger if Stage 6 idempotency status names stay unchanged. | PR3 will not modify Stage 7 and will document real TTS output as Stage 6-only until a later avatar/video PR updates Stage 7. PR3 adds a versioned provider-neutral TTS manifest plus optional normalized audio artifact and a separate provider spend/quota ledger. |
| Observability/logging/redaction | Restore warnings interpolate exception text from poisoned local state; metadata artifact stores user-facing raw glossary terms; caplog proof is missing. | Restore logs will emit sanitized reason classes only. Redaction claim is scoped to logs/observability/internal provider metadata, not user-facing Stage 6 artifacts. Add caplog poisoned-state and provider secret/payload redaction tests. |

## Human-only Surfaces

- Review any real-provider-call plan and explicitly approve in writing before
  any non-mock call. No such call is planned for PR3.
- Review PR body for the five-point reviewer overview, source-fact URLs, and
  human verification checklist.
- Confirm CI green and human approval on the exact latest head before merge.
- Confirm merge wording is reference-only until intentional closeout; no
  premature issue-closing keyword in PR body.

## Validation Plan

- `uv run pytest tests/unit/test_guardrails_check.py -q`
- `uv run pytest tests/unit/test_phase1_closure_docs.py -q`
- `python3 scripts/guardrails_check.py`
- `make quality`
- `uv run ruff check backend scripts tests`
- `uv run mypy backend scripts tests`
- `uv run pytest tests/unit/test_stage6_multilingual.py tests/api/test_stage6_multilingual_api.py -q`
- `make dependency-audit`
- `make security`
- `make container-scan`
- `make secrets-scan`
- `make eval`
- `make ci`
- After PR creation: forced pull-request guardrails with exact base/head SHAs
  using a synthetic pull_request event.

## Stop Rule

Stop and do not implement provider egress if any source fact cannot be verified
from official docs, if fan-out finds an unresolved blocker, if the allowlist
would need avatar/video/hosted/frontend/Docker/CI/dependency changes, if tests
would need real provider calls, or if enabling a paid provider would require
provider account setup, dashboard configuration, paid plan activation, wallet
funding, or paid spend.
