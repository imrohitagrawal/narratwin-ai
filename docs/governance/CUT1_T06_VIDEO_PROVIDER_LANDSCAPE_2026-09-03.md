# Cut 1 T06 Video Provider Landscape

## Decision status

- Research checkpoint: 2026-09-03 (Asia/Kolkata).
- Route: Issue `#512`; parent Cut 1 route: Issue `#459`.
- Decision: shortlist candidates and require a demo-before-code ladder.
- Provider selected: no.
- Provider activated: no.
- Accounts, credentials, egress, calls, or spend authorized by this record: no.
- Authority effect: `NO_AUTHORITY_EFFECT`.
- Revisit: immediately before any provider demonstration, when a material
  provider capability/price/terms change is reported, or after 30 days.

This is the durable refresh of the earlier provider analysis in
`docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md` and the immutable v1 research
contract in `docs/governance/cut1-provider-bakeoff-contract-v1.json`. The v1
contract stays byte-identical because the accepted Cut 1 live binding pins its
checksum. This document does not supersede or activate that authority.

## Product need and non-negotiable inputs

T06 must eventually create six independently reviewable videos: Meera, Myra,
and Raj in landscape and portrait. Each video must preserve presenter identity,
natural speech-linked facial motion, and useful upper-body expressiveness while
remaining provenance-bound and inspectable.

The already accepted audio is immutable:

| Presenter | Voice | Exact WAV SHA-256 | Duration |
|---|---|---|---:|
| Meera | Despina | `177b2755e300c8fcd52e2e84c642e130b9a8dab6ca454fb033205dfe9c6a7c7c` | 117.981917 s |
| Myra | Leda | `cd9b7a811108910168a13c88a8e7987c80ec78014c7554a3cf219d76f2c4664c` | 127.661917 s |
| Raj | Achird | `92c580762d7b358e7c67582ee1900a04e6e2b9593e48962651196b876c54216e` | 117.701917 s |

The total unique narration is 363.345751 seconds. Rendering both aspects is
726.691502 generated seconds before repeats or retries. A provider-produced MP4
may transcode its audio track; therefore the WAV remains the audio authority.
Any later remux policy must preserve timing and must never trim, accelerate,
time-compress, denoise, resample, or otherwise replace the accepted WAV.

## Research method and limits

The review started from product fit, then checked official API/model,
duration/aspect, motion, pricing, privacy/terms, and deployment documentation.
Marketing quality claims were not treated as acceptance evidence. A provider
without a sufficiently inspectable API or contractual privacy path was not
promoted merely because its showcase video looked strong.

No finite review can prove that it enumerated every application in the world.
This record covers the serious candidates discovered across dedicated avatar
platforms, audio-driven foundation models, cinematic video generators,
real-time/digital-twin products, and local/open-model routes. Newly identified
candidates should be added with an official URL and evaluated against the same
gates. The name “C-Dense” could not be resolved to an authoritative product or
vendor source; it remains unclassified until an exact URL is supplied.

## Recommended shortlist

| Disposition | Candidate | Why it remains in contention | Load-bearing uncertainty |
|---|---|---|---|
| `PRIMARY_TEST` | HeyGen Avatar IV Photo | Direct still-image plus audio workflow; portrait/landscape and 1080p path; motion prompting; mature API | Enterprise no-training/DPA posture, fictional-image compatibility, deletion evidence, and real output quality need proof |
| `DIRECT_CHALLENGER` | VEED Fabric 1.0 Fast through Hedra | Audio-driven image animation with unusually long published duration and both aspects | Official VEED pages conflict on maximum duration; Hedra route resolution tops at 720p; contractual posture needs proof |
| `GOVERNANCE_CHALLENGER` | Colossyan NEO/Instant Avatar | Enterprise security/no-training claims, API audio URL, gestures, and longer-form video orientation | Existing fictional still-image enrollment and exact audio behavior need written or demonstrated proof |
| `OPEN_MODEL_BENCHMARK` | LongCat-Video-Avatar 1.5 | Open MIT code, image-plus-audio control, long-form focus, and both aspects through hosted inference | High hosted cost, local GPU burden, provider retention, identity continuity, and production API stability |

HeyGen is therefore the recommended first compatibility test, not the final
provider selection. VEED/Hedra and Colossyan prevent a one-vendor conclusion;
LongCat supplies an open-model quality/control benchmark if its cost is accepted.

## Candidate evidence matrix

### Shortlisted candidates

| Candidate | Input and output evidence | Published limits and indicative cost | Privacy/rights evidence | Current conclusion |
|---|---|---|---|---|
| HeyGen Avatar IV Photo | [Create video API](https://developers.heygen.com/reference/create-video), [motion prompts](https://help.heygen.com/en/articles/12805098-fine-tune-avatar-gestures-and-movements-with-custom-motion-prompts-avatar-iv-v) | [API pricing](https://developers.heygen.com/docs/pricing) lists Avatar IV Photo around USD 0.05/s; the six unique cells estimate USD 36.33 before failures/repeats | [Terms](https://www.heygen.com/terms), [privacy](https://www.heygen.com/privacy), and [enterprise pricing](https://developers.heygen.com/docs/enterprise-pricing) require account-specific DPA/no-training confirmation | Best first test, subject to the privacy stop |
| VEED Fabric 1.0 Fast via Hedra | [VEED API page](https://www.veed.io/tools/fabric-1.0-api), [Hedra Fast model](https://www.hedra.com/models/video/veed/fabric-10-fast), [Hedra API models](https://www.hedra.com/develop/models/video) | Hedra publishes up to 3m10s at 480p/720p and both aspects for Fast; standard indicative USD 0.2143/s makes six cells about USD 155.73 | Provider terms, retention/deletion, and no-training commitment remain human/legal review surfaces | Direct challenger; verify current duration conflict before spend |
| Colossyan NEO/Instant Avatar | [Create avatar](https://docs.colossyan.com/avatar-creation/create-avatar), [manual video generation](https://docs.colossyan.com/video-generation/video-generation/generating-a-video-manually), [avatar API](https://docs.colossyan.com/basics/openapi/list-avatars) | [Pricing](https://www.colossyan.com/pricing/) supports longer-form plans; exact synthetic-avatar API price/limits require a quote | [Security](https://www.colossyan.com/security/) and [terms](https://www.colossyan.com/terms/) provide the strongest public governance lead in this shortlist, but applicability must be contracted | Governance challenger; written fictional-identity compatibility needed |
| LongCat-Video-Avatar 1.5 | [Official repository](https://github.com/meituan-longcat/LongCat-Video), [vLLM Omni recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/meituan-longcat/LongCat-Video-Avatar-1.5.md), [fal endpoint](https://fal.ai/models/fal-ai/longcat-single-avatar/image-audio-to-video) | Hosted 720p indicative USD 0.30/s makes six cells about USD 218.01; local execution needs substantial GPU memory | [fal payload handling](https://fal.ai/docs/documentation/model-apis/inference/payloads), [fal terms](https://fal.ai/legal/terms-of-service), and [fal CDN](https://fal.ai/docs/documentation/model-apis/fal-cdn) need retention/public-URL review | Optional benchmark, not fastest production route |

### Baselines, exploratory routes, and rejected Cut 1 routes

| Disposition | Candidate/category | Evidence and reason |
|---|---|---|
| `BASELINE_ONLY` | Hedra Avatar | [Model](https://www.hedra.com/models/video/hedra/avatar) accepts exact image/audio, both aspects, up to ten minutes and 540p/720p/1080p. It is a valuable talking-head baseline, but full upper-body credibility is unproved. Indicative six-cell cost is USD 36.33 at 720p or USD 45.42 at 1080p. |
| `BASELINE_ONLY` | D-ID Talks and Sync | [D-ID Talks](https://docs.d-id.com/reference/createtalk) and [Sync API](https://sync.so/docs/api-reference/api-overview) / [Sync 3](https://sync.so/docs/models/sync-3) are useful lip-sync comparators, but their head-centric boundary does not prove the desired waist-up/body expressiveness. |
| `EXPLORATORY` | Higgsfield | [Model/lipsync overview](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-lipsync-voiceover-and-aspect-ratios), [business controls](https://higgsfield.ai/creator-hub/help-center/business/team-and-business-higgsfield), and [terms](https://higgsfield.ai/terms-of-use-agreement) show a broad creative studio. A stable acceptance-grade direct API and applicable no-training terms were not established. |
| `EXPLORATORY` | Argil, AKOOL, Creatify | Potential presenter platforms, but this checkpoint did not establish enough official long-form, exact-audio, full-body, privacy, deletion, and stable-API evidence to displace the shortlist. |
| `REJECT_CUT1` | Google Veo, Flow, Pomelli | [Veo API](https://ai.google.dev/gemini-api/docs/video), [Flow](https://labs.google/fx/tools/flow), and [Pomelli](https://blog.google/innovation-and-ai/models-and-research/google-labs/pomelli/) are cinematic/marketing generation tools, not demonstrated exact two-minute audio-driven presenter renderers. Veo clip durations are far below the requirement. |
| `REJECT_CUT1` | Seedance | [Seedance 2.5 in Runway](https://help.runwayml.com/hc/en-us/articles/53542207042323-Creating-with-Seedance-2-5) and [Seedance 1.5 Pro](https://seed.bytedance.com/en/seedance1_5_pro) are generative clip routes, not accepted exact long-form presenter pipelines. |
| `REJECT_CUT1` | OmniHuman 1.5 alone | [Hosted model evidence](https://www.hedra.com/models/video/bytedance/omnihuman-15) is promising for audio-driven humans, but the published 16:9-only route fails the required portrait cell. Indicative six-output cost would be USD 116.27 even before solving that gap. |
| `REJECT_CUT1` | Runway Act-Two | [Act-Two](https://help.runwayml.com/hc/en-us/articles/42311337895827-Performance-Capture-with-Act-Two) requires a driving performance video and publishes a 30-second boundary, adding an unnecessary input/identity dependency. |
| `REJECT_CUT1` | Kling and similar short clips | Published one-minute or shorter clip boundaries do not satisfy the 117.7–127.7-second accepted narrations without stitching and continuity risk. |
| `CONDITIONAL_OR_FUTURE` | Synthesia, Tavus, DeepBrain and digital-twin platforms | [Synthesia audio upload](https://docs.synthesia.io/reference/upload-script-audio) and [Tavus video request](https://docs.tavus.io/api-reference/video-request/create-video) prove relevant APIs, but existing fictional still identity, exact WAV, consent/enrollment, and body-motion compatibility are unresolved. Tavus conversational video is more relevant to later interactive Mode 2. |
| `REJECT_DEFAULT` | Local SadTalker/Wav2Lip-class stack | License, model-weight, quality, duration, GPU, packaging, maintenance, and security burdens make this slower than a bounded hosted demo. Wav2Lip remains unsuitable for the default external/commercial path under its published restrictions. |

## Source conflicts and facts that documentation cannot prove

- VEED sources disagree: one support surface describes roughly one-minute
  behavior, the product page describes longer output, and Hedra publishes
  3m10s for Fabric Fast. A no-spend capability check or vendor confirmation is
  required before selecting it.
- No reviewed provider source proves that output MP4 audio bytes will equal the
  uploaded WAV. Final admission must inspect streams and preserve the accepted
  WAV as the governing audio artifact.
- Provider marketing cannot prove identity preservation, lip synchronization,
  pronunciation, natural motion, warmth, or presenter fit for NarraTwin assets.
  Those remain exact-output human review surfaces.
- Pricing is indicative, excludes plan minimums, tax, storage, failed jobs,
  retries, avatar setup, and vendor-specific rounding, and grants no spend
  authority.
- Privacy, training, region, retention, deletion, and commercial-use posture
  must be verified for the exact account/tier; public terms are not a substitute
  for an applicable enterprise commitment.

## Demo-before-code recommendation

Do not build or modify the NarraTwin adapter merely because an API appears to
fit on paper. Use these gates in order:

1. **Gate 0 — zero-network readiness.** Verify account/tier, applicable
   DPA/no-training terms, synthetic-fictional identity eligibility, region,
   retention/deletion, exact API/model, SecretRef, current price, call count,
   and spend ceiling. Freeze the request package without exposing a key.
2. **Gate 1 — short compatibility smoke.** Use one separately labelled
   10–15-second diagnostic excerpt of an accepted WAV with one accepted image
   on each authorized shortlist candidate. The excerpt is a derivative test
   input only; it cannot replace, shorten, or become an accepted T05/T06
   artifact. No source WAV changes.
3. **Gate 2 — full-duration risk test.** Render the longest/hardest accepted
   narration, Myra at 127.661917 seconds, in both landscape and portrait on the
   best one or two candidates. This detects the duration, drift, aspect,
   continuity, and pacing failures that a short sample cannot expose.
4. **Gate 3 — evidence-based selection.** Compare exact media probes, identity
   continuity, lip sync, motion, severe defects, repeatability, latency, cost,
   privacy/deletion evidence, and independent human review. Select a primary
   and a compatible fallback only after this evidence exists.
5. **Gate 4 — TDD adapter and final cells.** Only then freeze code scope, commit
   executable RED, implement the smallest provider-neutral adapter correction,
   and generate the six final presenter/aspect cells under separate authority.

This ladder avoids expensive code churn while still preventing a polished
short clip from being mistaken for proof that the complete narration works.

## Invariant and evidence matrix

| ID | Invariant | Evidence now | Required future proof |
|---|---|---|---|
| `T06-RSCH-001` | Research cannot activate a provider | This record and immutable v1 contract say `NO_AUTHORITY_EFFECT` | Exact owner-approved activation package |
| `T06-RSCH-002` | T05 audio bytes remain authoritative | Exact Package 43 hashes above | Pre/post-call hashes, stream probe, and any governed remux receipt |
| `T06-RSCH-003` | A short sample is not full-duration proof | Gate 1 is labelled diagnostic only | Gate 2 Myra landscape/portrait outputs and human review |
| `T06-RSCH-004` | Marketing is not media acceptance | Uncertainties and rejected routes remain explicit | Exact-output identity, lip-sync, motion, defect, and repeatability evidence |
| `T06-RSCH-005` | Provider facts are account- and time-specific | Official URLs, access date, conflicts, and revisit trigger are recorded | Gate 0 terms, privacy, price, quota, region, retention, and deletion checkpoint |
| `T06-RSCH-006` | Code follows demonstrated compatibility | No code path is owned by this issue | RED-first adapter issue only after Gates 1–3 pass |

## Skill and tool selection record

| Method considered | Decision | Evidence or prevented action |
|---|---|---|
| Source-driven development | Used for the research checkpoint | Official vendor/model/API/terms URLs and dated uncertainties replace memory or marketing-only selection |
| Competitor analysis | Used to normalize candidates | Common product-fit, duration/aspect, motion, API, governance, and cost criteria produced the dispositions above |
| Documentation and ADR workflow | Used for durable storage; no ADR yet | Additive dated record preserves alternatives while avoiding a false final architecture decision |
| Git workflow and versioning | Used for delivery | Issue-bound branch, preflight-first commit, bounded paths, review, CI, and closeout; immutable v1 contract preserved |
| TDD, security hardening, and CI/CD automation | Deferred to the adapter increment | Prevented code/tests/workflows from preceding provider compatibility and explicit activation authority |
| Shipping/launch and image generation | Rejected for this checkpoint | No deployment, publication, generated image, release, or production claim is in scope |

## Exact owner/operator inputs for Gate 0

The owner does not need to choose the winner now. To prepare a small demo, the
owner should provide only the following decisions or capabilities:

1. State which governed accounts are actually available: HeyGen, Hedra,
   Colossyan, and optionally fal.ai. An account name, tenant, project ID,
   credential path, or authentication state must not be posted publicly.
2. Confirm the applicable privacy route for each available account: enterprise
   DPA/no-training, or explicitly request a separate review of self-service
   terms. The recommended default is to stop when no-training is unproved.
3. Place each API key in the approved secret manager and provide only a
   non-secret `SecretRef` capability to the operator. Never send keys in chat,
   issues, PRs, files, logs, or shell history.
4. Authorize a named demo package only after its zero-network manifest states
   exact image/audio/excerpt hashes, provider/model/endpoint, calls, generated
   seconds, maximum spend, timeout/retry behavior, privacy/egress statement,
   expected outputs, and deletion evidence.
5. Remain available later for human review of the actual demo outputs. No test,
   waveform metric, or provider status can substitute for that decision.

Recommended first package shape after Gate 0 is complete: one call per
available top-three candidate, concurrency one, no automatic retry, one
10–15-second diagnostic excerpt, and a small aggregate spend ceiling. The exact
call count and USD cap must be calculated from the accounts that are genuinely
available and explicitly authorized before any egress. LongCat should be added
only if the owner accepts its materially higher indicative cost.

## Decision rule

A provider passes the research stage only when the exact account and API route
can run the bounded demo without violating identity, immutable-audio, privacy,
security, cost, deletion, or provenance rules. A short demo can eliminate an
incompatible option; it cannot select the final provider by itself. The
full-duration two-aspect test and human review are mandatory before code or the
six-cell generation route is frozen.
