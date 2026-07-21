# Real-Media Hosted Demo Plan

## Version

- Version: 0.1
- Issue: `#225`
- Status: Demo Phase 0 planning only
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

This is a hosted controlled or invite-only demo goal. It is not a production
launch, external soft launch with customer data, public synthetic-media
distribution approval, multi-worker durability claim, or production-readiness
claim.

## Demo Boundary

The target demo tier is a new hosted controlled/invite-only demo boundary that
must be explicitly reviewed before deployment. It sits above the current
`Local mock demo` row in `docs/LAUNCH_LEVELS.md` because it is externally
reachable and may use real provider credentials, but it remains below production
and must not inherit production claims.

Required boundary controls before a hosted demo URL exists:

- named owner for the hosted environment
- invite-only access or equivalent access control
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
| Avatar/video | HeyGen | `https://www.heygen.com/api-pricing` | pay-as-you-go minimum, per-minute video pricing, API wallet behavior |
| Avatar/video | HeyGen | `https://developers.heygen.com/` | developer API model costs and Digital Twin/Photo Avatar/Video Agent cost model |
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
| HeyGen API | API pricing/help pages describe pay-as-you-go wallet start around `$5` and standard generated avatar video around `$1/minute`; advanced avatar features can cost more. | Good first avatar/video candidate for non-cloned or stock/synthetic identity demo output. |
| D-ID API | API pricing page lists a free trial with up to 3 minutes and paid API plans starting around `$35/month`; minutes used via API are deducted from the same balance as the web product. | Viable alternate avatar/video adapter candidate; confirm public-use and retention rules before selection. |
| Tavus | Pricing page lists developer API access and generated-video overage around `$1/minute` on pay-as-you-go, with lower per-minute rates on larger plans. | Viable alternate avatar/video adapter candidate; confirm stock replica/custom replica rules before selection. |
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
estimate for 10 invited reviewers generating one 2-minute media output each:

| Cost area | Planning estimate | Control required |
|---|---:|---|
| Hosted app/database/cache | `$5-$50/month` | hard monthly cloud budget and teardown plan |
| TTS or voice clone | `$6-$30/month` plus usage, depending on provider and plan | per-run character/minute cap |
| Avatar/video generation | roughly `$1-$4/minute` depending on provider, avatar type, and engine | per-user video-minute quota |
| Failed runs and retries | 20-50 percent buffer | retry budget and idempotency |
| Total first-month demo budget | `$75-$200` | app-level provider budget stop |

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
2. provider abstraction plus real TTS PR
3. avatar/video provider PR
4. hosted-demo access, quota, artifact retention, and demo polish PR

Checkpoint 1 must retain mock/local providers for local/dev/test and CI.

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

The implementation specs must expand these categories into explicit matrix IDs
before code:

| Category | Required cases |
|---|---|
| Access | anonymous access, expired invite, wrong invite, abuse attempts |
| Provider config | missing key, invalid key, provider disabled, provider unavailable |
| Provider output | timeout, malformed response, unexpected MIME, duplicate JSON keys, unsafe URL, oversized audio/video |
| Cost | per-run budget exceeded, per-user quota exceeded, global monthly quota exceeded |
| Grounding | no uploaded knowledge, retrieval miss, unsupported claim, missing citation, eval failure |
| Prompt injection | uploaded docs attempt to override rules, call provider, reveal secrets, or force unsupported claims |
| Language | unsupported language, provider cannot render selected language, translation loses required terms |
| Audio | empty audio, wrong format, too long, missing disclosure, no clone consent |
| Video | missing audio binding, wrong source run, stale script, unsafe artifact, missing disclosure |
| Clone consent | clone requested without consent, wrong person, consent expired, consent not bound to artifact |
| Retention | artifact deletion, provider deletion request, stale artifact link, no raw secret/provider payload logging |
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
