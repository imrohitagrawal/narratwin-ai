# Real-Media Hosted Demo Plan

## Version

- Version: 0.1
- Issue: `#225`; Checkpoint 1 PR 1 issue `#229`; Checkpoint 1 PR 2 issue `#235`
- Status: Demo Phase 0 complete; Checkpoint 1 PR 2 contract-only work active
- Last updated: 2026-07-21

## Purpose

This document is the durable planning source for the hosted controlled
real-media NarraTwin demo. It captures the path agreed in issue `#225` before
any provider SDK, provider key, real-media generation, cloned-identity
implementation, hosted deployment, Product Mode 2 implementation, or production
readiness claim is added.

The demo end goal is fixed:

```text
User uploads or uses project knowledge
-> user selects language and audience
-> NarraTwin generates a grounded walkthrough
-> walkthrough is delivered by an avatar/voice clone
-> citations and evaluation evidence remain visible behind the media output
```

This is a controlled reviewer demo goal. It is not a production launch, public
synthetic-media distribution approval, multi-worker durability claim, or
production-readiness claim. If the demo URL is reachable by recruiters, hiring
managers, or any other external identity, `docs/LAUNCH_LEVELS.md` classifies it
as an external/invite-only soft-launch boundary regardless of the word `demo`;
before that URL exists, the implementation plan must either stay in an
owner-approved/internal synthetic hosted demo boundary or explicitly inherit the
soft-launch controls for access, secrets, monitoring, retention/deletion,
incident response, rollback, backup, and named ownership.

## Demo Boundary

The target demo tier is a new hosted controlled/invite-only demo boundary that
must be explicitly reviewed before deployment. It sits above the current
`Local mock demo` row in `docs/LAUNCH_LEVELS.md` because it is externally
reachable and may use real provider credentials, but it remains below production
and must not inherit production claims.

Required boundary controls before a hosted demo URL exists:

- named owner for the hosted environment
- invite-only access or equivalent access control
- launch-level decision that either keeps access internal/owner-approved or
  inherits the external/invite-only soft-launch controls
- incident response, rollback, backup, monitoring, and named-owner controls
  before any external invite URL exists
- synthetic or owner-approved demo data only
- explicit provider-key secret storage outside the repo
- per-user and global provider-cost quota
- artifact retention and deletion rule
- AI-generated media disclosure in UI and artifacts
- clone consent and provenance before any cloned face or cloned voice is used
- no public synthetic-media distribution claim
- no production-readiness claim
- no production durability, uptime, RTO, RPO, backup, or multi-worker claim

## Provider Strategy

The fastest path for the hosted demo is provider-backed real media with
mock/local fallback retained for tests.

### Provider-Backed Path

Use external provider adapters only after source facts are reviewed and the
provider is selected behind an internal NarraTwin interface.

Candidate source facts to review:

| Area | Candidate | Official source | Fact to verify before implementation |
|---|---|---|---|
| Voice/TTS | ElevenLabs | `https://elevenlabs.io/pricing/api` | plan cost, included minutes/characters, overage behavior, API access |
| Voice/TTS | ElevenLabs | `https://elevenlabs.io/text-to-speech-api` | output formats, supported languages, rate limits, per-minute or character cost |
| Voice clone | ElevenLabs | `https://help.elevenlabs.io/hc/en-us/articles/36842751624209-Can-I-create-a-Professional-Voice-Clone-of-someone-else-s-voice` | own-voice verification requirement and restriction on cloning another person's voice |
| Voice policy | ElevenLabs | `https://elevenlabs.io/use-policy` | prohibited impersonation, consent, disclosure, harmful use, and election/political limits |
| Avatar/video | HeyGen | `https://www.heygen.com/api-pricing` | pay-as-you-go minimum, API wallet behavior, and API billing pool |
| Avatar/video | HeyGen | `https://developers.heygen.com/docs/pricing` | model-specific per-second costs for Avatar III, Avatar IV, Avatar V, Video Agent, lipsync, and TTS |
| Avatar consent | HeyGen | `https://developers.heygen.com/docs/avatar-consent` | digital twin consent requirements and enterprise-only consent bypass constraints |
| Avatar/video | D-ID | `https://www.d-id.com/pricing/api/` | API plan, credits, trial, output limitations |
| Avatar/video | D-ID | `https://www.d-id.com/faqs/` | credit-to-video-duration mapping and public-use constraints |
| Avatar/video | Tavus | `https://www.tavus.io/pricing` | free/starter/business limits, stock replica access, custom replica availability |
| Avatar/video | Tavus | `https://docs.tavus.io/api-reference/video-request/create-video` | video generation API inputs, script/audio behavior, output lifecycle |
| Hosting | Railway | `https://docs.railway.com/pricing/plans` | hosted demo minimum spend, included usage, overage behavior |
| Hosting | Vercel | `https://vercel.com/pricing` | frontend hosting tier and usage/cost controls |
| Hosting | Render | `https://render.com/docs/free` | free service/database limitations and non-production posture |

Provider-backed implementation is the recommended Checkpoint 1 path because it
can produce recruiter-visible real media without local GPU setup, large model
bundles, or uncertain local render quality.

### Source-Fact Snapshot

Reviewed on 2026-07-21 against the official sources listed above:

| Candidate | Current source fact | Demo implication |
|---|---|---|
| ElevenLabs | API pricing page lists self-serve tiers, including Starter at `$6/month`, Creator at `$22/month`, and TTS model pricing around `$0.05-$0.10` per 1,000 characters depending on model class. | Good fit for Checkpoint 1 real TTS if key storage, usage cap, consent, and disclosure controls are added first. |
| HeyGen API | API pricing pages describe pay-as-you-go wallet start around `$5`, API usage deducted from the API wallet, and model-specific per-second video pricing; Avatar III Digital Twin/Studio Avatar is around `$0.0167/sec`, Avatar III Photo Avatar around `$0.0433/sec`, Avatar IV Photo Avatar around `$0.05/sec`, Avatar IV/V Digital Twin or Studio Avatar around `$0.0667/sec`, and Video Agent Prompt to Video around `$0.0333/sec`. | Good first avatar/video candidate only after the avatar/video PR selects the exact model and proves the 2-minute run cost, retry buffer, and global quota fit the owner-approved budget. |
| D-ID API | API pricing page lists a free trial with up to 3 minutes; FAQ states credits are worth up to 15 seconds of video and API usage draws from the same balance as the Studio product. | Viable alternate avatar/video adapter candidate; selected plan, credit package, public-use, watermark, and retention rules must be refreshed before selection. |
| Tavus | Pricing page lists developer/API access, allocated conversation or video-generation minutes, pay-as-you-go behavior on paid plans, 30-second minimums for conversations, and no overage cap on paid plans. | Viable alternate avatar/video adapter candidate only with app-side hard quotas; selected plan, stock replica/custom replica rules, and generated-video cost must be refreshed before selection. |
| OpenVoice | Official repository states OpenVoice V1 and V2 are MIT licensed and free for commercial and research use. | Promising local clone research candidate, but still needs dependency, model-weight, quality, hardware, and consent review. |
| SadTalker | Official repository states the license has moved to Apache 2.0 and removed the prior non-commercial restriction. | Possible local avatar research candidate, but still needs model-weight, asset, quality, hardware, and consent review. |
| Wav2Lip | Official repository says the code can only be used for personal/research/non-commercial purposes. | Rejected for the default recruiter/portfolio demo path. |
| XTTS-v2 | Hugging Face license states the model and outputs are non-commercial only. | Rejected for the default recruiter/portfolio clone path. |

### Local-Model Path

Local models are a research track, not the first implementation path.

| Candidate | Official source | Current planning posture |
|---|---|---|
| OpenVoice | `https://github.com/myshell-ai/OpenVoice` | promising local voice-clone candidate; verify exact code, weight, dependency, and output-license posture before use |
| SadTalker | `https://github.com/OpenTalker/SadTalker` | possible local talking-head candidate; verify license, model weights, assets, runtime, GPU, and quality before use |
| Wav2Lip | `https://github.com/Rudrabha/Wav2Lip` | rejected for default recruiter/portfolio path while official repo says personal/research/non-commercial only |
| XTTS-v2 | `https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt` | rejected for public/commercial-facing clone path while model license permits only non-commercial use |

Local models reduce third-party runtime dependency but add hardware, quality,
license, setup, packaging, and operational risks. They should become optional
adapters only after provider-backed demo flow is stable.

## Cost Planning

Demo Phase 0 must produce a budget table before implementation. Initial planning
estimate for 10 invited reviewers generating one 2-minute media output each.
The default controlled-demo posture should be cost-minimized:

| Cost area | Cost-minimized planning estimate | Control required |
|---|---:|---|
| Hosted app/database/cache | `$0-$5/month` preferred for the controlled demo; use `$20+` only if the selected host requires paid spend controls or team features | hard monthly cloud budget, teardown plan, and no production durability claim |
| TTS or voice clone | Checkpoint 1 TTS should target low single-digit usage or the smallest terms-compatible paid plan when output is recruiter-facing or otherwise external; cloned voice remains out of scope until Checkpoint 2 | per-run character/minute cap |
| Avatar/video generation | target roughly `$1/minute` for non-cloned/stock/synthetic output; avoid premium avatar engines unless explicitly justified | per-user video-minute quota |
| Failed runs and retries | 20 percent default buffer; 50 percent only for provider-selection testing, not normal reviewer access | retry budget and idempotency |
| Cost-minimized first-month demo target | `$30-$60` for 10 invited reviewers x one 2-minute output each | app-level provider budget stop |
| First-month approval ceiling | `$75-$200` only if paid hosting controls, monthly provider plans, or higher-cost avatar engines are explicitly selected | owner approval before spend |

The cheapest credible recruiter-facing demo mode is view-first:

```text
invite link
-> owner-approved pre-generated real-media walkthrough
-> compact trust strip with 0 unsupported claims, source count, AI-media disclosure
-> expandable human-readable citations and eval evidence
-> optional regeneration only inside a hard per-reviewer quota
```

View-first mode reduces provider spend, avoids slow first-impression waits,
keeps a working artifact available when providers are down, and still preserves
the end-to-end proof because the displayed media must be bound to its source
run, citations, eval result, provider metadata, and artifact manifest.

No implementation PR may rely on these estimates alone. The selected provider
PR must record current official pricing, plan, limits, and expected cost per
demo run.

## Checkpoints

Research for Checkpoint 1 and Checkpoint 2 can happen in parallel during Demo
Phase 0. Implementation must be sequential.

### Checkpoint 1: Real Media Without Cloned Identity

Goal:

```text
project knowledge
-> grounded multilingual script
-> real TTS audio
-> real avatar/video using approved stock, synthetic, or non-cloned identity
-> hosted controlled demo access
-> citations/eval/provider metadata visible
```

Expected PR sequence:

1. spec/source facts/governance PR
2. latency, capacity, cost, access, quota, cache/pre-generation, retention, and
   launch-level contract PR
3. provider abstraction plus real TTS PR
4. avatar/video provider PR
5. hosted-demo access, quota, artifact retention, and demo polish PR

Checkpoint 1 must retain mock/local providers for local/dev/test and CI.

### Checkpoint 1 PR 1: Spec, Source Facts, Governance

Issue `#229` is the first Checkpoint 1 PR. It is a governance/spec/source-facts
slice only. It may update this document, `docs/STAGE_ISSUE_PLAN.md`,
`docs/STATUS.md`, `docs/THIRD_PARTY_NOTICES.md`, and its matching
GovernancePreflightV1 artifact. It must not implement provider abstraction,
TTS, avatar/video, hosted-demo access, quotas, retention, demo polish, backend,
frontend, RAG, database, Docker, provider SDKs, provider keys, real media,
cloned identity, Product Mode 2, public distribution, or production-readiness
claims.

Positive claims for Checkpoint 1 PR 1:

- `C1-SPEC-001`: official provider/platform source facts are refreshed with
  source URLs and verified dates.
- `C1-SPEC-002`: future Checkpoint 1 implementation PR contracts are defined
  before implementation begins.
- `C1-SPEC-003`: cost-minimized first-month controlled-demo constraints are
  defined before paid-provider work begins.
- `C1-SPEC-004`: security/privacy/consent/eval failure matrix IDs are explicit
  enough for later PRs to map to tests, gates, source facts, human-only rows, or
  documented non-goals.

Negative invariants for Checkpoint 1 PR 1:

- `NONGOAL-RUNTIME-001`: no backend, frontend, provider, RAG, avatar, database,
  Docker, hosted deployment, provider SDK, provider key, or runtime product path
  may change.
- `NONGOAL-MEDIA-001`: no real audio generation, real video generation,
  media-provider call, clone profile, cloned voice, cloned face, or cloned
  identity behavior may be implemented.
- `NONGOAL-LAUNCH-001`: this PR must not claim hosted launch, public synthetic
  media distribution, Product Mode 2, production durability, production
  monitoring, production readiness, or release Go.

### Checkpoint 1 PR 2: Latency, Capacity, Cost, Access, Quota Contract

Issue `#235` is the second Checkpoint 1 PR. It is a contract-only slice for
latency, capacity, cost, access, quota, cache/pre-generation, retention, and
launch-level boundaries. It may update this document, `docs/LAUNCH_LEVELS.md`,
`docs/STAGE_ISSUE_PLAN.md`, `docs/STATUS.md`,
`docs/THIRD_PARTY_NOTICES.md`, its matching GovernancePreflightV1 artifact, and
the narrow Phase 1 Closure checker/test files that enforce the exact branch
scope. It must not implement backend, frontend, provider abstraction, TTS,
avatar/video, hosted deployment, access-system implementation, database, Docker,
CI workflow, provider SDKs, provider keys, real audio/video generation, cloned
identity, Product Mode 2, public distribution, or production-readiness claims.

It also must not perform provider account setup, provider dashboard
configuration, paid plan activation, provider wallet funding, model or voice
selection, real provider test calls, paid spend, or hosted URL creation. PR2
creates minimum future requirements only; PR3 provider abstraction plus real TTS
still needs fresh selected-provider source facts and executable disabled-default,
quota, retention/deletion, redaction, timeout, retry, and duplicate-spend
safeguards before any provider egress is enabled.

Positive claims for Checkpoint 1 PR 2:

- `C1-CONTRACT-001`: latency and first-view performance budgets are explicit
  enough for later implementation PRs to test.
- `C1-CONTRACT-002`: reviewer capacity, concurrency, backpressure, provider-off,
  provider-failure, missing-artifact, quota-exhaustion, and unavailable states
  are explicit enough for later implementation PRs to test.
- `C1-CONTRACT-003`: first-month spend target, approval ceiling, quota
  reservation, refund, retry, timeout, and duplicate-spend controls are explicit
  before any provider spend can occur.
- `C1-CONTRACT-004`: view-first pre-generated media, cache invalidation,
  retention, deletion, tombstones, provider-side deletion evidence, disclosure,
  invite/access, and launch-level boundaries are explicit.
- `C1-CONTRACT-005`: every changed PR2 claim maps to an executable test, gate,
  official source fact, human-only checklist row, or documented non-goal for the
  future PR that will implement it.

PR2 changed-claim evidence mapping:

| Contract ID | Claim boundary | Required evidence class before implementation | Future owner |
|---|---|---|---|
| `C1-CONTRACT-001` | valid invite first visible view-first artifact targets p95 under 3 seconds; provider generation is not on first view | executable latency budget test plus human UX review for first viewport | hosted-demo PR |
| `C1-CONTRACT-002` | default capacity is 10 invited reviewers, one view-first artifact, and optional regeneration only inside quota; backpressure preserves view-first output | executable quota/backpressure tests plus source facts for selected provider limits | hosted-demo and provider PRs |
| `C1-CONTRACT-003` | target first-month spend is `$30-$60`; `$75-$200` is an owner-approved ceiling, not automatic authority | official selected-provider pricing source facts, executable quota reservation/refund tests, and owner human checklist row | provider and hosted-demo PRs |
| `C1-CONTRACT-004` | cached media displays only when provenance, eval, disclosure, retention, and deletion state match; deletion leaves minimum tombstone/evidence only | executable cache invalidation and retention/deletion tests plus provider-side deletion source facts or human row | avatar/video and hosted-demo PRs |
| `C1-CONTRACT-005` | PR2 itself stays docs/gates only and does not pre-authorize PR3 egress, hosted access, or paid spend | Phase 1 Closure branch allowlist gate and PR body human-only scope review | PR2 |

Human-only PR2 surfaces:

| Surface | Automation gap | Required reviewer check | Residual-risk owner |
|---|---|---|---|
| Provider pricing and quota facts | Pricing, dashboard limits, overage, model catalogs, rate limits, and retention/deletion terms can change after PR2. | Confirm PR2 uses source facts only as planning inputs and requires fresh selected-provider facts before PR3 egress or spend. | repository owner |
| Launch/access level | CI cannot decide whether a future URL is internal, external/invite-only, production-like validation, or production. | Confirm `docs/LAUNCH_LEVELS.md` remains canonical and that any external identity inherits the external/invite-only soft-launch boundary. | repository owner |
| Paid provider setup | CI cannot see provider dashboards, wallet balances, plan activation, or test calls outside the repo. | Confirm PR2 performed none of these actions and that future PRs must record owner approval before any paid spend. | repository owner |
| Final merge message | CI cannot inspect the final squash/merge editor text. | Use reference-only wording for issue `#235` unless a human intentionally chooses an issue-closing closeout at merge time. | repository owner |

## Checkpoint 1 Source Facts

Verified on 2026-07-21 against official provider/platform documentation where
available. Pricing, policy, and API facts are volatile; implementation PRs must
refresh the selected provider facts again before spending money, setting up
provider accounts, selecting models or voices, funding wallets, configuring
dashboards, making real provider test calls, or enabling any provider call.

| ID | Area | Official source | Fact used | Checkpoint 1 implication |
|---|---|---|---|---|
| `SRC-ELEVEN-TTS-001` | ElevenLabs TTS pricing | `https://elevenlabs.io/pricing/api` | API pricing lists TTS by characters, with lower-cost Flash/Turbo and higher-cost Multilingual/v3 classes. | The TTS PR must calculate estimated character cost per run, reserve quota before provider calls, and default to the lowest acceptable terms-compatible model for the controlled demo. Free-tier output is not acceptable for recruiter-facing or external output unless a fresh terms review explicitly proves the selected use is allowed. |
| `SRC-ELEVEN-TTS-002` | ElevenLabs TTS model limits | `https://elevenlabs.io/text-to-speech-api` | Public TTS page describes model-specific language support, character limits, and approximate per-minute costs. | The TTS PR must cap script length and selected languages before audio generation. |
| `SRC-ELEVEN-CLONE-001` | ElevenLabs voice cloning | `https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/professional-voice-cloning` and `https://help.elevenlabs.io/hc/en-us/articles/36842751624209-Can-I-create-a-Professional-Voice-Clone-of-someone-else-s-voice` | Professional Voice Cloning requires verification, and ElevenLabs help states a user can create a Professional Voice Clone only of their own voice; another person must create, verify, and privately share their own clone from their own account. | Checkpoint 1 must avoid cloned identity. Checkpoint 2 consent is necessary but not sufficient for ElevenLabs PVC: third-party PVC enrollment is excluded unless the subject owns the verified clone and privately shares it under a recorded scope. |
| `SRC-ELEVEN-POLICY-001` | ElevenLabs use policy | `https://elevenlabs.io/use-policy` | Policy prohibits unauthorized, deceptive, or harmful impersonation, including replicating another person's voice without consent or legal right. | Consent, disclosure, and no-deceptive-impersonation gates are mandatory before any voice clone path. |
| `SRC-HEYGEN-PRICE-001` | HeyGen API pricing | `https://www.heygen.com/api-pricing` and `https://developers.heygen.com/docs/pricing` | Public API pricing says pay-as-you-go starts around `$5`, Direct API usage is deducted from a separate API dashboard balance, and developer pricing is model-specific per second or per operation. | The avatar/video PR must select one explicit model, convert seconds to expected dollars, include wallet/minimum-spend behavior, and block unbounded generation. |
| `SRC-HEYGEN-VIDEO-001` | HeyGen create video API | `https://developers.heygen.com/reference/create-video` | Create Video supports avatar/image based video and scripts or pre-recorded audio, with selectable avatar engines. | The avatar/video PR must bind the selected source run, TTS audio, script, citations, eval, provider model, and artifact manifest. |
| `SRC-HEYGEN-CONSENT-001` | HeyGen avatar consent | `https://developers.heygen.com/docs/avatar-consent` | Digital twin generation requires consent for the depicted person; photo avatars and prompt-to-avatar characters are documented as not requiring digital-twin consent only when they do not depict a real identifiable person. | Checkpoint 1 must use provider-stock, synthetic, or non-identifiable identity assets by default; any real-person photo, face, likeness, or training asset requires explicit rights, consent, source-asset deletion, and audit evidence before provider egress. Digital twin or cloned identity must wait for Checkpoint 2. |
| `SRC-DID-PRICE-001` | D-ID API pricing | `https://www.d-id.com/pricing/api/` and `https://www.d-id.com/faqs/` | D-ID API plans use credits; FAQ states each credit is worth up to 15 seconds of video and API minutes draw from the same balance as the web product. | D-ID remains viable only with strict per-run credit reservation and a hard monthly budget stop. |
| `SRC-DID-TERMS-001` | D-ID synthetic marking | `https://www.d-id.com/eula/` | D-ID terms restrict hiding or minimizing synthetic marks or watermarks without prior written approval. | The avatar/video PR must preserve provider marks/disclosures and must not promise white-label output. |
| `SRC-TAVUS-PRICE-001` | Tavus pricing | `https://www.tavus.io/pricing` | Tavus pricing lists monthly plans, allocated conversation/video-generation minutes, 30-second minimums, pay-as-you-go overage on paid plans, and no overage cap on paid plans. | Tavus is not cost-safe without app-level hard quota enforcement; no-overage-cap provider behavior cannot be trusted as the budget control. |
| `SRC-TAVUS-VIDEO-001` | Tavus generate video API | `https://docs.tavus.io/api-reference/video-request/create-video` | Generate Video requires a face/replica ID and either script or audio URL, returns queued status and a hosted URL. | The avatar/video PR must handle async status, polling, provider failure, unsafe URLs, timeout, and artifact download validation. |
| `SRC-TAVUS-KEY-001` | Tavus API authentication | `https://docs.tavus.io/api-reference/authentication` | Tavus docs state API keys are secrets and must not be exposed in browser/client-side code; load securely from environment/server configuration. | Future provider PRs must keep provider calls server-side, env-only, disabled by default, and redacted from logs. |
| `SRC-TAVUS-CONSENT-001` | Tavus face rights | `https://docs.tavus.io/sections/replica/replica-faqs` | Tavus requires appropriate rights and permissions for another person's likeness, voice, and training content. | Checkpoint 2 clone work must record rights, permissions, consent scope, revocation, and deletion paths before profile creation. |
| `SRC-RAILWAY-001` | Railway pricing | `https://docs.railway.com/pricing/plans` and `https://docs.railway.com/pricing/cost-control` | Railway plans include usage credits/minimum commitments, and cost-control docs describe configurable usage limits for some spend areas. | Hosted-demo PR must use an owner-approved project budget, alerts, teardown plan, and no production durability claim. |
| `SRC-VERCEL-001` | Vercel pricing and limits | `https://vercel.com/pricing`, `https://vercel.com/docs/pricing`, and `https://vercel.com/docs/plans/hobby` | Vercel has Hobby and Pro tiers, usage limits, Pro included credit across resources, and Hobby is described as personal/non-commercial. | Vercel Hobby must not be selected for a recruiter-facing or external demo unless the owner records a terms-compatible non-commercial classification. Otherwise budget Vercel as Pro-like spend or choose another host with source-backed access and spend controls. |
| `SRC-RENDER-001` | Render free service behavior | `https://render.com/docs/free` | Render free web services spin down after 15 minutes without inbound traffic and take about one minute to spin back up. | Render free hosting is risky for recruiter first impression unless view-first media, warmup, or paid non-spindown behavior is selected. |
| `SRC-OPENVOICE-001` | OpenVoice license | `https://github.com/myshell-ai/OpenVoice` | Official repository states OpenVoice V1 and V2 are MIT licensed and free for commercial and research use. | OpenVoice remains a local research candidate only; model weights, dependencies, hardware, quality, consent, and output rights still need review. |
| `SRC-SADTALKER-001` | SadTalker license | `https://github.com/OpenTalker/SadTalker` | Official repository says the license moved to Apache 2.0 and removed the prior non-commercial restriction. | SadTalker remains a local research candidate only; model weights, assets, runtime, hardware, consent, and output quality still need review. |
| `SRC-WAV2LIP-001` | Wav2Lip license | `https://github.com/Rudrabha/Wav2Lip` | Official repository says the code can only be used for personal/research/non-commercial purposes. | Wav2Lip remains rejected for the recruiter/portfolio demo path. |
| `SRC-XTTS-001` | XTTS-v2 license | `https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt` | The model license allows only non-commercial use of the model and outputs. | XTTS-v2 remains rejected for public, recruiter-facing, or commercial-facing clone output. |

## Checkpoint 1 Implementation Contract

Each future Checkpoint 1 PR must start from its own GitHub issue, branch, PR,
preflight, source-fact refresh, matrix-to-test mapping, fan-out review, and
local/CI evidence. The PRs below are sequential unless a human explicitly
approves a narrower split.

### Future PR: Provider Abstraction Plus Real TTS

Allowed objective:

```text
grounded multilingual script bundle
-> server-side optional TTS provider adapter
-> real TTS audio artifact metadata
-> citation/eval/source-run binding retained
```

Required contract:

- Keep mock/local providers as the default for local/dev/test/CI.
- Keep provider SDKs optional; no paid provider required for tests.
- Keep provider key server-side, env-only, never in frontend code, logs, docs,
  fixtures, artifacts, or PR evidence.
- Use the existing provider-agnostic boundary where possible; do not hardcode a
  selected vendor into core script generation.
- Generate or store real audio only after quota reservation, source-run binding,
  supported-language check, script-length cap, disclosure metadata, provider
  failure policy, artifact validation, retention/deletion policy, and
  provider-side deletion/tombstone evidence path exist.
- For Checkpoint 1, use non-cloned stock/generated voices only unless a separate
  Checkpoint 2 clone-consent issue is opened and approved.
- Required evidence before merge: unit/API tests for disabled provider defaults,
  missing/invalid key, quota reservation/refund, provider timeout, malformed
  provider output, unsafe URL rejection when applicable, source-run/eval binding,
  prompt-injection refusal for every provider-fed text surface, retention/deletion
  behavior for generated/provider artifacts, and redacted logs.

Explicit non-goals:

- No avatar/video provider.
- No voice cloning.
- No hosted deployment.
- No production readiness.

### Future PR: Avatar/Video Provider

Allowed objective:

```text
approved source run + evaluated script + validated TTS/audio or script
-> optional real avatar/video provider adapter
-> validated video/media artifact metadata
-> citations/eval/provider/disclosure evidence visible
```

Required contract:

- Use provider-stock, synthetic, prompt-generated, or otherwise non-identifiable
  identity assets for Checkpoint 1 by default.
- Do not use a real person's photo, face, likeness, custom face, image-to-face
  asset, replica, or training asset in Checkpoint 1 unless the avatar/video PR
  records explicit rights, consent scope, source-asset retention/deletion,
  provider-side deletion path, and audit evidence before provider egress.
- Keep cloned face, cloned voice, digital twin, and replica-profile creation out
  of scope until Checkpoint 2 consent/provenance controls exist.
- Bind every media artifact to source run ID, trace ID, language, audience,
  script checksum, citation refs, evaluation ID/status/checksum, TTS/audio
  checksum if present, provider ID/model/version, provider job ID, artifact
  checksum, and disclosure text/version.
- Validate provider output before storage, display, or download: status,
  timeout, retry-after, max attempts, MIME, extension, size, checksum, duplicate
  JSON keys, unsafe URL, redirect, unexpected fields, stale source run, stale
  eval, failed eval, and prompt/provider-output injection attempts.
- Preserve provider synthetic marks/watermarks unless a written provider/legal
  approval explicitly permits an alternate disclosure path.
- Required evidence before merge: tests for provider disabled default, missing
  key, failed eval block, source-run/eval/media mismatch, citation mismatch,
  prompt injection across script/transcript/provider-output surfaces, provider
  timeout/failure, unsafe URL, oversized artifact, quota exhaustion,
  retention/deletion/provider deletion path, and disclosure visibility.

Explicit non-goals:

- No cloned identity.
- No public synthetic-media distribution.
- No Product Mode 2.
- No production readiness.

### Future PR: Hosted Demo Access, Quota, Retention, Demo Polish

Allowed objective:

```text
invite-controlled hosted demo
-> view-first pre-generated media
-> optional regeneration inside hard quota
-> retention/deletion/disclosure/evidence controls
```

Required contract:

- Before any hosted URL exists, record launch-level decision, named owner,
  access control, secret storage, provider budget, incident contact, rollback,
  monitoring, retention/deletion, teardown, and no-production-claim wording.
- Default to view-first pre-generated media for recruiters and reviewers.
  Regeneration must be optional and guarded by per-reviewer and global quotas.
- External invite access inherits the external/invite-only soft-launch boundary
  if any non-owner external identity can reach the URL.
- The hosted app must show AI-generated media disclosure and allow citation/eval
  evidence inspection from the media output.
- Required evidence before merge: access-denied tests, expired/wrong invite
  tests, quota-exceeded tests, retry/cost budget tests, retention/deletion tests,
  disclosure visibility review, provider-off fallback, and manual provider
  dashboard budget checks with owner and revisit trigger.

Explicit non-goals:

- No public launch.
- No production SLA, backup, RTO, RPO, or multi-worker durability claim.
- No clone profile enrollment.

## Cost-Minimized Controlled Demo Constraints

First-month planning target:

- Target spend: `$30-$60`.
- Approval ceiling: `$75-$200`, only with explicit owner approval for the chosen
  host/provider mix.
- Default audience: 10 invited reviewers.
- Default media budget: one owner-approved view-first pre-generated
  walkthrough, plus optional one regeneration per reviewer only if quota
  remains and the selected model-specific cost fits the target.
- Default generated media length: cap at 2 minutes unless the owner approves a
  higher per-run budget.
- Default retry budget: at most one automatic retry for transient provider
  failure, and no retry after quota exhaustion, unsupported claims, consent
  failure, invalid upload, citation mismatch, or provider policy failure.

Model-specific first-month budget check for 10 reviewers, 2-minute cap, and no
retry. Future PRs must refresh these values from official source facts before
selection:

| Candidate | Source fact | Approx 20-minute reviewer budget | Checkpoint 1 posture |
|---|---|---:|---|
| HeyGen Avatar III Digital Twin/Studio Avatar | `$0.0167/sec` | `$20.04` plus wallet/minimum spend | Cost-plausible, but Digital Twin/Studio identity is not allowed for Checkpoint 1 unless stock/non-cloned use is source-approved. |
| HeyGen Avatar III Photo Avatar | `$0.0433/sec` | `$51.96` plus wallet/minimum spend | Within target only with no broad retry buffer; future PR must prove consent/policy fit for the selected photo/avatar source. |
| HeyGen Avatar IV Photo Avatar | `$0.05/sec` | `$60.00` plus wallet/minimum spend | At the top of target before retries or hosting; requires owner approval for any retry budget. |
| HeyGen Video Agent Prompt to Video | `$0.0333/sec` | `$39.96` plus wallet/minimum spend | Cost-plausible if output can preserve source/eval/citation bindings and disclosure. |
| HeyGen Avatar IV/V Digital Twin or Studio Avatar | `$0.0667/sec` | `$80.04` plus wallet/minimum spend | Outside target and inside approval-ceiling territory; not a default Checkpoint 1 choice. |
| Tavus generated video overage | provider pricing describes allocated minutes, overage, 30-second minimums, and possible no-overage-cap behavior | must be recomputed from the selected paid plan | Not cost-safe until app-side caps and provider dashboard evidence exist. |
| D-ID credits | FAQ maps one credit to up to 15 seconds | must be recomputed from selected paid plan and credit expiry | Alternate only; trial/free output is not acceptable for recruiter-visible output unless terms explicitly allow it. |

Hosting/access cost must be separated from media generation:

- Static pre-generated artifact path: may use a static site or object-hosted
  artifact only after access boundary, disclosure, evidence visibility,
  retention, deletion, and no-public-launch wording are explicit.
- Authenticated hosted app path: requires source-backed plan selection for
  frontend, backend, storage, logs, invite control, and provider egress before
  any hosted URL exists. Vercel Pro-like costs, Railway minimum spend/overage
  behavior, Render free cold starts/ephemeral filesystem/30-day free Postgres,
  and paid deployment-protection add-ons must be treated as first-month budget
  inputs, not ignored overhead.
- Vercel Hobby must not be used for recruiter-facing or otherwise external
  access unless the owner records a source-backed non-commercial classification;
  absent that record, budget Vercel as Pro-like spend or choose a different
  terms-compatible host.
- Render Free is acceptable only for previewing platform behavior, not for a
  production-readiness claim, and only if cold start cannot make the first
  recruiter viewport look broken.

Hard guardrails required before any paid provider call:

- Per-run quota reservation before provider work starts.
- Per-user/reviewer quota.
- Global monthly quota.
- Provider-specific max seconds/characters/credits.
- Atomic durable check-and-reserve across per-run, per-user/reviewer, retry, and
  global monthly budgets before provider egress. Concurrent requests must use a
  lease-fenced reservation or equivalent transaction so they cannot each pass
  the same global budget check.
- Failed-job refund policy only for failures that did not incur provider cost.
- Idempotency key and provider job ID binding to prevent duplicate spend.
- Dashboard or provider-side spend limit where available, plus app-side budget
  stop because providers may allow overage.
- Redacted cost telemetry: provider, model, seconds/characters/credits, reserved
  amount, charged estimate, quota decision, retry count, and failure code, with
  no prompt, upload text, transcript, provider secret, or raw provider payload.
- Hosted/invite logs must minimize or redact invite tokens, signed artifact
  URLs, reviewer emails, IP addresses, user agents, referrers, provider job IDs
  when not needed for support, and provider dashboard identifiers before any
  invite-controlled URL exists.

### Quota, Retry, And Cost Contract

Future paid-provider PRs must make these controls executable before any provider
egress is enabled:

| Control ID | Dimension | Planning limit | Reservation timing | Refund rule | Terminal behavior |
|---|---|---:|---|---|---|
| `COST-RUN-001` | Single generation run | selected-provider estimate for max 2 minutes or capped characters | reserve before first provider call | refund only when no provider job or billable request was accepted | no provider call when reservation fails |
| `COST-USER-001` | Invited reviewer | one optional regeneration after viewing owner-approved artifact | reserve before regeneration starts | refund only for app-side validation failures before provider egress | regeneration disabled; view-first artifact remains available |
| `COST-GLOBAL-001` | First-month demo | `$30-$60` target; `$75-$200` owner-approved ceiling | checked before each provider job and each retry | manual owner reconciliation against provider dashboard | all regeneration disabled when exceeded |
| `COST-RETRY-001` | Automatic retry | at most one transient retry per provider job | reserve retry budget before retry | no refund if provider accepted a billable retry | typed retry-exhausted failure |
| `COST-OVERRIDE-001` | Owner override | explicit owner approval only | recorded before quota increase | no automatic refund assumption | expiry/revisit required before merge |

Retry rules:

- Retry only transient provider timeout, documented temporary provider
  unavailable status, or rate-limit responses where the provider documents retry
  semantics.
- If a provider submit call times out after egress and acceptance is unknown,
  do not automatically retry unless the provider has documented idempotency for
  the submitted request key or a provider job lookup proves no accepted billable
  job exists.
- Respect provider `Retry-After` when present and below the app max wait;
  otherwise use the app backoff ceiling.
- Never retry unsupported claims, citation mismatch, source/eval/media mismatch,
  upload validation failure, consent failure, provider-policy failure, quota
  exhaustion, unsafe URL, unexpected MIME, oversized artifact, or duplicate JSON
  key failure.
- Bind retries to idempotency key, request checksum, provider job ID when
  assigned, provider model, source run, language, audience, and reserved budget.

### Async Provider Lifecycle Contract

Real avatar/video providers can return queued jobs, hosted URLs, webhooks,
rate-limit headers, or credit errors. Future provider PRs must define and test
one normalized lifecycle before provider enablement. Selected-provider source
facts must cover rate limits, `Retry-After`, idempotency support or absence,
polling/webhook semantics, hosted URL TTL, and artifact download behavior before
generic retry or polling logic is accepted:

| Lifecycle field | Required contract |
|---|---|
| Provider job ID | Stored only after provider accepts the request; bound to source run, request checksum, quota reservation, provider ID/model, and idempotency key. |
| Normalized states | At minimum: `reserved`, `submitted`, `queued`, `running`, `succeeded`, `failed`, `timed_out`, `cancelled`, `deleted`, `blocked`. Provider-specific states must map explicitly. |
| Poll cadence | Bounded cadence with max attempts and max elapsed time; provider `Retry-After` takes precedence only inside the app ceiling. |
| Webhooks | Optional only after signature verification, replay protection, source/job binding, and duplicate delivery handling are specified. Polling remains required as a fallback unless provider docs make webhooks mandatory. |
| Duplicate spend prevention | Duplicate idempotent request replays the existing terminal result or in-flight state; changed request checksum conflicts before provider egress. |
| Unsafe provider URL | Any provider-hosted or downloadable URL must be HTTPS, expected host or allowlisted pattern, no private/reserved IP fetch, no unexpected redirect, and must be validated before display/download. |
| Failure display | Provider failure keeps view-first artifact available when valid, disables regeneration when appropriate, shows owner contact path, and avoids uptime or production promises. |

### Media Artifact Cache Contract

View-first mode depends on cached/pre-generated media. Future implementation PRs
must define this cache as a provenance-bound artifact store, not as a generic URL
cache:

| Cache field | Required binding |
|---|---|
| Cache key | tenant/project/sourceRunId/language/audience/scriptChecksum/evaluationId/evaluationChecksum/providerId/providerModel/disclosureVersion/artifactChecksum. |
| Display allowed | only when source run, current evaluation status, context refs, citation indexes, language artifact, media artifact, provider manifest, retention state, and disclosure all match a `PASSED` source graph. |
| Stale eval | stale, failed, deleted, or mismatched eval blocks clean media display; UI may show a disabled artifact with explicit stale/fail state only if no provider artifact is fetched. |
| Invalidation | source upload deletion, source run deletion, eval failure, citation mismatch, consent revocation, retention expiry, provider deletion, disclosure-version change, or artifact checksum mismatch invalidates the media. |
| Retention/deletion | delete or tombstone media artifacts per hosted-demo retention policy; preserve only minimum audit evidence needed to prove deletion and prevent replay. |
| Provider URL | provider-hosted URLs are never trusted as durable cache keys; download/ingest must validate bytes, MIME, size, checksum, and source binding before display. |

### Multilingual Grounding Contract

Checkpoint 1 media may use translated scripts, subtitles, or target-language
audio. Preserving citation markers is necessary but not sufficient.

Future implementation PRs must block media display unless:

- translated claim text is tied to the source-language claim, citation indexes,
  context refs, and evaluation record;
- glossary and citation markers are preserved;
- translated output does not introduce unsupported factual claims;
- subtitles, TTS text, audio manifest, and media script share the same language,
  source run, evaluation, and checksum chain;
- translated-claim support or meaning-preservation checks are represented in the
  PR failure matrix and tests.

### Recruiter Flow UX Contract

Minimum first-screen controlled-demo behavior:

| State | Required user-visible behavior | Provider action |
|---|---|---|
| Valid invite, artifact ready and eval passed | first viewport shows playable owner-approved media, AI-generated media disclosure, unsupported-claim count of 0, source count, eval timestamp/run ID, and one-click citations/eval drawer | no provider call on first view |
| Valid invite, artifact failed eval or unsupported claims | media is blocked or disabled; first viewport shows AI-generated media disclosure context, unsupported-claim/fail state, source count, eval timestamp/run ID, citation/eval drawer, and owner contact path | no provider call on first view |
| Valid invite, artifact missing/not ready/invalid | show a non-broken unavailable state with AI-media disclosure context, owner contact path, and no generate-first path; regeneration remains disabled until an owner-approved provenance-bound artifact exists | no provider call on first view |
| Valid invite, provider down | view-first artifact remains available if provenance is valid and eval passed, with the same disclosure, unsupported-claim count of 0, source count, eval timestamp/run ID, and citation/eval drawer as the happy path; regeneration disabled; owner contact path visible | no new provider call |
| Invalid or expired invite | show access-denied state with owner contact path and no product data | no provider call |
| Per-user quota exhausted | approved artifact remains visible only if provenance is valid and eval passed, with disclosure, unsupported-claim count of 0, source count, eval timestamp/run ID, and citation/eval drawer; regeneration disabled; copy says regeneration is paused for this invite | no provider call |
| Global budget exhausted | approved artifact remains visible only if provenance is valid and eval passed, with disclosure, unsupported-claim count of 0, source count, eval timestamp/run ID, and citation/eval drawer; all regeneration disabled; owner-only budget action required | no provider call |
| Eval/source/media mismatch | media is blocked or visibly disabled; evidence drawer shows mismatch state | no provider call |

Target first impression for the hosted demo: valid invite to first visible
view-first artifact should target p95 under 3 seconds from the reviewer opening
the invite URL on a normal broadband connection, including DNS, auth redirect,
server cold start, first byte, and first render. Free hosting with documented
one-minute cold starts is acceptable only if a warmup or pre-rendered static
shell prevents the first screen from appearing broken and the end-to-end invite
open still meets the target or is explicitly owner-approved as a demo limitation.

## Checkpoint 1 Failure Matrix

Every future implementation PR must map each applicable ID below to a test,
executable gate, official source fact, explicit human-only row, or documented
non-goal. Range shorthand is not acceptable in PR evidence.

| ID | Area | Case | Expected behavior | Evidence owner |
|---|---|---|---|---|
| `UPLOAD-VALIDATION-001` | Upload safety | wrong MIME, oversized file, unsafe filename, active content, malformed text | reject before ingestion/provider prompt; no raw upload in logs/errors | provider/TTS or hosted PR if upload path is touched |
| `PROMPT-INJECTION-001` | Prompt injection | upload, audience/language input, transcript, provider output, or model output attempts to override rules or reveal secrets | treat as untrusted data; generated output and media refuse unsafe instruction | provider/TTS and avatar/video PRs |
| `UNSUPPORTED-CLAIMS-001` | Evaluation | generated script has unsupported claim or failed eval | block media generation and display refusal/warning; no accepted media artifact | provider/TTS and avatar/video PRs |
| `CITATION-MISMATCH-001` | Citations | media/script references source chunk not retrieved or citation text drifts | block accepted output and require eval/citation repair | provider/TTS and avatar/video PRs |
| `SOURCE-EVAL-MEDIA-MISMATCH-001` | Provenance | source run, language bundle, eval, TTS audio, avatar job, media artifact, or manifest belongs to a different run | reject replay/display/download; record typed failure | provider/TTS and avatar/video PRs |
| `MULTILINGUAL-DRIFT-001` | Multilingual grounding | translated script, subtitles, TTS text, or audio changes meaning, drops glossary/citation markers, adds unsupported claims, or diverges from source-language eval | block media generation/display until translated claims, citations, subtitles, audio, and eval evidence match the approved source graph | provider/TTS and avatar/video PRs |
| `PROVIDER-FAILURE-001` | Provider reliability | missing key, invalid key, disabled provider, timeout, malformed response, `Retry-After`, unsafe URL, unexpected MIME, oversized artifact, duplicate JSON keys, max attempts exceeded | fail closed or fall back to mock/view-first artifact without hiding failure | provider/TTS and avatar/video PRs |
| `QUOTA-EXHAUSTION-001` | Cost/quota | per-run, per-user, retry, provider, or global monthly quota exceeded | do not call provider; show quota-exceeded state; no retry loop | every paid-provider or hosted PR |
| `BACKPRESSURE-RATE-LIMIT-001` | Reliability/capacity | queue saturated, concurrent reviewer limit reached, provider 429/rate limit, provider queue delay, local worker unavailable, or backpressure threshold exceeded | do not start duplicate provider work; preserve view-first artifact; show typed retry-later or regeneration-paused state inside quota rules | every paid-provider or hosted PR |
| `CONSENT-REVOKED-001` | Consent | consent expires, is revoked, wrong subject, wrong scope, or consent not bound to artifact | block clone/profile/media generation and hide/delete affected artifacts per retention policy | Checkpoint 2; non-goal in Checkpoint 1 |
| `CLONE-PROFILE-DELETION-001` | Clone lifecycle | provider clone/profile/source asset deletion requested or provider profile missing | stop use, block replay/regeneration, record provider deletion evidence | Checkpoint 2; non-goal in Checkpoint 1 |
| `RETENTION-DELETION-001` | Retention/deletion | user/owner requests deletion of upload, generated script, audio, video, provider artifact, source asset, invite, or log | delete or tombstone per policy; provider-side deletion tracked where applicable | hosted-demo PR |
| `DISCLOSURE-VISIBILITY-001` | Disclosure | AI-generated media disclosure hidden, removed, too small, missing from artifact, or inconsistent with provider mark | block publish/share/download until visible disclosure exists | avatar/video and hosted-demo PRs |
| `EXTERNAL-INVITE-BOUNDARY-001` | Launch boundary | external reviewer can access hosted URL before soft-launch controls are accepted, expired invite, wrong invite, anonymous access, owner contact path missing | enforce invite-only access and soft-launch controls before external access; no public/prod claim | hosted-demo PR |

## Checkpoint 1 Skill/Tool Selection

Issue `#229` PR 1 selected skills and evidence from the claim boundary, not from
ceremony:

| Skill/tool | Decision | Evidence boundary |
|---|---|---|
| `spec-driven-development` | Invoked | This PR defines future contracts and non-goals before implementation. |
| `planning-and-task-breakdown` | Invoked | Checkpoint 1 is split into provider abstraction/TTS, avatar/video provider, and hosted-demo access/quota/retention follow-up PRs. |
| `source-driven-development` | Invoked | Volatile provider/platform facts are recorded from official sources with verified date and source URLs. |
| `security-and-hardening` | Invoked | Failure matrix covers untrusted uploads/prompts/provider outputs, consent, disclosure, retention, and deletion. |
| `performance-optimization` | Invoked only for planning | Latency, cold-start, quota, retry, and first-month cost constraints are specified; no performance implementation is included. |
| `code-review-and-quality` | Invoked | Fan-out reviewers attacked the plan across source facts, security, eval, UX, reliability, CI, and governance before PR open. |
| `git-workflow-and-versioning` | Invoked | Work starts from issue `#229`, dedicated branch, and first commit containing only `docs/governance/preflights/issue-229.json`. |
| `taste-check` | Invoked locally | The plan keeps one existing demo-plan source of truth and rejects new runtime/product files or duplicated governance docs. |
| Provider SDK/tool install | Rejected | No runtime implementation, provider dependency, provider key, hosted deployment, or real media generation is allowed in this PR. |

Issue `#235` PR 2 reuses the same claim-boundary discipline for the latency,
capacity, cost, access, quota, cache/pre-generation, retention, and launch-level
contract. It adds `docs/LAUNCH_LEVELS.md` alignment, an exact branch changed-file
allowlist, and focused allowlist regression coverage because those are the
minimum executable gates needed to keep the contract-only PR from drifting into
implementation or later hosted-demo authorization.

## Checkpoint 1 Review Prompt Set

Future implementation PRs must adapt these prompts before coding:

- Cost/provider terms: disprove pricing, overage, provider policy, license,
  consent, public-use, and deletion assumptions from official sources.
- Security/privacy/consent: attack untrusted uploads, prompts, transcripts,
  provider outputs, model outputs, log redaction, clone consent, revocation, and
  deletion.
- Eval/grounding/citations: attack unsupported claims, citation drift, stale
  source runs, failed eval media display, and source-run/eval/media mismatch.
- UX/demo/recruiter flow: attack view-first path, first impression latency,
  quota copy, disclosure visibility, evidence inspectability, and soft-launch
  overclaim.
- Performance/reliability/quota: attack provider timeout, async polling,
  retry-after, queue/backpressure, idempotency, cold starts, pre-generated
  fallback, and budget stops.
- Test/quality/CI: attack branch allowlist, preflight first-commit evidence,
  PR-body guardrails, validation commands, and docs-only false passes.
- Governance/taste-check: attack duplicated docs, vague contracts, ceremonial
  review, missing stop rules, and scope creep.

## Checkpoint 1 Fan-Out Review Record

Issue `#229` PR 1 review posture:

| Reviewer angle | Finding summary | Disposition |
|---|---|---|
| Cost/provider terms | Blocking review found false-pass risk in generic `$1/minute` avatar cost, understated ElevenLabs PVC ownership limits, and hosting/access costs mixed with static artifact costs. | Source facts now use model-specific HeyGen rates, budget math for 20 reviewer-minutes, ElevenLabs own-voice/share constraint, and separate static artifact versus authenticated hosted-app cost contracts. App-side hard quotas remain mandatory. |
| Security/privacy/consent | Review attacked clone consent, revocation, provider-output trust, and deletion. | Checkpoint 1 keeps cloned identity out of scope; `CONSENT-REVOKED-001`, `CLONE-PROFILE-DELETION-001`, `RETENTION-DELETION-001`, and provider-output failure rows are explicit future gates. |
| Eval/grounding/citations | Review attacked stale eval display, citation drift, source-run/media mismatch, and multilingual translation drift. | Media cache and multilingual contracts require current `PASSED` eval, matching citations/source run/language checksums, and block display on mismatch. |
| UX/demo/recruiter flow | Review attacked first viewport trust, quota/error copy, evidence inspectability, and public-launch overclaim. | Recruiter-flow contract requires view-first artifact, disclosure, unsupported-claim/eval/source counts, citation/eval drawer, access-denied states, owner contact path, and no provider call on first view. |
| Performance/reliability/quota | Review attacked async provider jobs, retries, cold starts, duplicate spend, provider outages, and budget stops. | Async lifecycle, idempotency, retry, cache, and `COST-*` controls now require bounded polling, app-side quota reservation, one transient retry max, and fallback to valid view-first artifacts. |
| Test/quality/CI | Review attacked first-commit evidence, branch allowlist, PR-body guardrails, and docs-only false passes. | First commit contains only the issue preflight; branch allowlist is formalized; forced PR guardrails are required after PR creation; local quality commands remain mandatory evidence. |
| Governance/taste-check | Local review attacked scope creep, duplicated source-of-truth docs, vague contracts, and ceremonial review. | The PR reuses `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`, keeps runtime/provider files untouched, expands concrete IDs instead of category labels, and records a stop rule for future implementation drift. |

Issue `#235` PR 2 review posture:

| Reviewer angle | Finding summary | Disposition |
|---|---|---|
| Cost/provider terms | Fresh review found that pricing, credits, rate limits, overage caps, retry billing, refund semantics, and dashboard controls are volatile and differ across candidate TTS, avatar/video, and hosting providers. | PR2 treats provider and hosting facts as planning inputs only. It sets a target first-month spend and owner approval ceiling, forbids account setup, dashboard configuration, plan activation, wallet funding, model/voice selection, test calls, and spend, and requires fresh selected-provider source facts plus executable quota safeguards in PR3 before egress. |
| Security/privacy/consent | Review attacked uploads, prompts, transcripts, provider/model outputs, external URLs, generated media retention, provider-side deletion evidence, and clone-adjacent identity drift. | PR2 keeps all such inputs untrusted, keeps cloned identity and real media generation out of scope, requires disabled-by-default provider behavior, retention/deletion/tombstone/provider-side evidence paths, and keeps consent/profile work for later issue-linked PRs. |
| Eval/grounding/citations | Review attacked unsupported claims, stale citations, failed eval display, source-run/media mismatch, and cache reuse after source or eval changes. | PR2 requires cached or pre-generated media to display only when provenance, citation, eval, disclosure, retention, and launch/access state match; future implementation must map every display claim to executable cache/eval/provenance tests. |
| UX/demo/recruiter flow | Review attacked first-view latency, cold start, unavailable/provider-off states, quota copy, evidence inspectability, and accidental public-launch claims. | PR2 requires a view-first pre-generated path, explicit unavailable states, reviewer capacity assumptions, no provider generation on first view, and launch/access wording aligned to `docs/LAUNCH_LEVELS.md` before any hosted URL exists. |
| Performance/reliability/quota | Review attacked provider 429s, async delay, retries, duplicate spend, queue saturation, timeout handling, provider outage, and quota exhaustion. | PR2 adds contract IDs for latency, capacity, quota reservation/refund, retry, timeout, backpressure, duplicate-spend prevention, provider-off/failure/missing-artifact/quota-exhaustion states, and later executable tests. |
| Test/quality/CI | Review attacked the missing issue `#235` changed-file allowlist, absent unrelated-file regression, marker-only prose scans, first-commit drift, and PR-body guardrail gaps. | PR2 adds an exact branch allowlist and regression test, preserves the first branch commit as preflight-only evidence, and requires PR-body claim mapping, human checklist rows, validation evidence, and forced PR guardrails after PR creation. |
| Governance/taste-check | Review attacked launch-level wording drift, duplicate authority, pre-authorizing hosted-demo work, standalone status-only follow-ups, and ceremonial source-fact review. | PR2 keeps `docs/LAUNCH_LEVELS.md` canonical for access/launch authority, updates `docs/STATUS.md` in the same PR with the intended post-merge next state, keeps routine closeout facts in PR/issue comments, and leaves PR3/provider egress blocked until fresh facts and executable safeguards exist. |

## Checkpoint 1 Stop Rule

Pause implementation and return to this contract if any future Checkpoint 1 PR
hits one of these conditions:

- a provider source fact changes pricing, consent, retention, deletion,
  public-use, or API behavior after implementation begins;
- two fan-out reviewers find different missing matrix rows;
- tests prove provider success using synthetic/intercepted success while the PR
  claims real provider behavior;
- quota, retry, or idempotency evidence cannot show duplicate spend prevention;
- media can be displayed without matching source run, citations, eval, provider
  metadata, artifact checksum, and disclosure;
- a hosted URL becomes externally reachable before access, incident, retention,
  deletion, budget, owner, and launch-level controls are accepted.

### Checkpoint 2: Cloned Identity

Goal:

```text
Checkpoint 1 flow
-> explicit voice and avatar clone consent
-> cloned voice/avatar profile
-> avatar/voice clone walkthrough output
-> stricter identity provenance and disclosure
```

Checkpoint 2 starts only after Checkpoint 1 is stable and reviewed. It must not
be implemented in parallel with Checkpoint 1 because cloned identity adds
biometric, consent, impersonation, provider-policy, disclosure, and public-use
risk.

## Failure Matrix Categories

Historical Demo Phase 0 category inventory. Checkpoint 1 PR 1 supersedes this
inventory with the explicit `Checkpoint 1 Failure Matrix` IDs above. Future
implementation PRs must cite the explicit IDs, not these broad categories, and
range shorthand remains unacceptable in PR evidence.

| Category | Required cases |
|---|---|
| Access | anonymous access, expired invite, wrong invite, abuse attempts, magic-link/no-account reviewer access, view-only default, quota-exceeded copy, owner contact path, target time-to-demo |
| Provider config | missing key, invalid key, provider disabled, provider unavailable |
| Provider output | timeout, malformed response, unexpected MIME, duplicate JSON keys, unsafe URL, oversized audio/video, async video polling, `Retry-After` handling, max attempts exceeded |
| Cost | per-run budget exceeded, per-user quota exceeded, global monthly quota exceeded, quota reservation, quota refund on failed provider job |
| Hosted capacity | concurrent reviewer limit, queue/backpressure, provider rate limit, cached media reuse, pre-generated fallback artifact, provider outage while view-first artifact remains available |
| Grounding | no uploaded knowledge, retrieval miss, unsupported claim, missing citation, eval failure |
| Evidence visibility | hidden evidence UI, stale eval record, source-run/eval/citation mismatch, media display when eval failed, citations/eval evidence not inspectable from the avatar/video output |
| Prompt injection | uploaded docs attempt to override rules, language/audience inputs attempt to override rules, provider/media outputs include unsafe instructions, reveal secrets, call providers directly, or force unsupported claims |
| Uploaded content safety | MIME/type/size validation failure, active-content stripping failure, output encoding failure, prompt/provider payload redaction failure, uploaded-doc retention/deletion failure |
| Language | unsupported language, provider cannot render selected language, translation loses required terms, translated unsupported claims, citation drift after translation, subtitle/audio divergence, eval evidence tied to wrong language artifact |
| Audio | empty audio, wrong format, too long, missing disclosure, no clone consent |
| Video | missing audio binding, wrong source run, stale script, unsafe artifact, missing disclosure |
| Clone consent | clone requested without consent, wrong person, consent expired, consent revoked or withdrawn, consent not bound to artifact, source media/voice sample not covered by consent |
| Retention | artifact deletion, provider deletion request, provider-side clone profile deletion, clone enrollment asset deletion, stale artifact link, no raw secret/provider payload logging, consent-record retention boundary |
| Review | no source facts, no cost proof, no fan-out review, no old-behavior proof for changed guardrails |

## Fan-Out Review Requirements

Each implementation PR in Checkpoint 1 and Checkpoint 2 must run or record
fan-out review coverage for:

- testing
- performance
- verification/evidence freshness
- `taste-check` code-quality review
- security and privacy
- provider terms and consent
- cost and quota behavior
- UX and accessibility
- eval/grounding
- failure cases and boundary values

Skill invocation is not completion evidence. Each review must identify the
claim, boundary, evidence, and residual risk.

## Autonomous Execution Rule

One autonomous prompt may drive Checkpoint 1, but it must still produce the PR
sequence above. The work must not collapse into one mega-PR. Each PR must:

- link the relevant issue
- preserve mock/local test fallback
- include source facts and failure-matrix coverage
- include tests and quality evidence
- keep provider keys out of the repository
- keep routine post-merge facts in PR/issue comments
- update `docs/STATUS.md` only for durable repository-tracked state changes

## Non-Goals For Issue `#225`

Issue `#225` is planning only. It does not authorize:

- backend or frontend runtime code changes
- provider SDK installation
- provider key handling
- hosted deployment
- real audio generation
- real video generation
- cloned face or voice implementation
- Product Mode 2 implementation
- public synthetic-media distribution
- production-readiness claims
