# Cut 1 T06 Video Provider Landscape

## Decision status

- Research checkpoint: 2026-09-03; controlling amendment: 2026-09-04
  (Asia/Kolkata).
- Routes: Issues `#512`, `#514`, and `#516`; parent Cut 1 route: Issue `#459`.
- Decision: preserve two current walkthrough plans, require a demo-before-code
  ladder, and reject further unchanged single-photo HeyGen Avatar IV work.
- Provider selected: no.
- Provider activated: no.
- Accounts, credentials, egress, calls, or spend authorized by this record: no.
- Authority effect: `NO_AUTHORITY_EFFECT`.
- Revisit: immediately before any provider demonstration, when a material
  provider capability/price/terms change is reported, or after 30 days.

The Issue #516 section at the end of this record controls when earlier rankings
or next-step wording conflicts with the later v8/v9 human-rejection evidence.
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

The exact governed presenter inputs are also immutable:

| Presenter | Exact repository input | Exact SHA-256 | Readiness |
|---|---|---|---|
| Meera | `frontend/public/demo/narratwin-synthetic-presenter.webp` | `d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1` | `SOURCE_READY_NO_DERIVATIVE` |
| Myra | `frontend/public/demo/cut1/myra-waist-up.webp` | `46390ac627662bff38c9bb4ec904520a808e42030ff698741b5c32519f0be4c3` | `DERIVATIVE_READY` |
| Raj | `frontend/public/demo/cut1/raj-waist-up.webp` | `f9060b3c0fb5d9cf0231f8142fff17a88c61537d12c6b90ad6be359085c86413` | `DERIVATIVE_READY` |

All three are `image/webp`. A PNG/JPEG-only route is not exact-still compatible.
Converting one would create different governed bytes and requires a separately
authorized, checksum-bound derivative; this research authorizes no conversion.

## Research method and limits

The review started from product fit, then checked official API/model,
duration/aspect, motion, pricing, privacy/terms, and deployment documentation.
It explicitly covered the owner-named HeyGen, Higgsfield, Runway, Superhuman,
ImagineArt, Synthesia, Creatify, Colossyan, and JoggAI routes, plus Hedra/VEED
Fabric, LongCat, D-ID, Tavus, ElevenLabs, Sync, Google video tools, Seedance,
OmniHuman, and credible local/open alternatives. Marketing quality claims and
vendor-authored comparison pages were not treated as acceptance evidence. A
provider without a sufficiently inspectable API or contractual privacy path
was not promoted merely because its showcase video looked strong.

No finite review can prove that it enumerated every application in the world.
This record covers the serious candidates discovered across dedicated avatar
platforms, audio-driven foundation models, cinematic video generators,
real-time/digital-twin products, and local/open-model routes. Newly identified
candidates should be added with an official URL and evaluated against the same
gates. The name “C-Dense” could not be resolved to an authoritative product or
vendor source; it remains unclassified until an exact URL is supplied.

## Hard-fit comparison

`PROVED` means a current official source documents the exact capability;
`CONDITIONAL` means account/tier/vendor confirmation is still required;
`FAIL` means the published route conflicts with Cut 1; and `UNKNOWN` means the
official material reviewed does not answer the question. These are source
grades, not media-quality scores.

| Candidate | Exact WAV + synthetic still | One-job 128 s | 16:9 + 9:16 | API/job evidence | Governance posture | Cut 1 disposition |
|---|---|---|---|---|---|---|
| HeyGen Avatar IV Photo | `CONDITIONAL`: accepted WebP input is undocumented; current image and Photo Avatar guides list PNG/JPEG only | `CONDITIONAL` | `PROVED` | `PROVED` | Enterprise no-training is proved; self-service needs opt-out | `PRIMARY_COMPATIBILITY_TEST` |
| JoggAI v2 Photo Avatar | `CONDITIONAL`: WAV is accepted, but 44.1 kHz is specified and the flow generates a new presenter derivative | `PROVED` (WAV up to 10 min) | `PROVED` | `PROVED` | Face-data training is opt-in, but general privacy/terms allow model improvement and broad content use; location text has placeholders | `TECHNICAL_CHALLENGER_ACTIVATION_BLOCKED` |
| Colossyan Instant Avatar | `CONDITIONAL`: image API is proved; fictional synthetic-anchor eligibility is not | `CONDITIONAL`: plans permit long video, but the exact Instant Avatar API route is access-gated | `PROVED` through explicit canvas size | `CONDITIONAL`: Instant API access requires support | Strongest Enterprise governance route; self-service terms permit broader content use | `GOVERNANCE_CHALLENGER` |
| Hedra Avatar | `PROVED` | `PROVED` (up to 10 min) | `PROVED` | `PROVED` | Current API terms allow training and prohibit product integration absent another order | `CONTRACT_BLOCKED` |
| VEED Fabric via fal.ai | `PROVED` | `PROVED` (up to 5 min) | `CONDITIONAL`: output follows the source framing; exact dimensions are not exposed | `PROVED` | fal.ai privacy, retention, deletion, region, and model-provider flow need Gate 0 proof | `FULL_LENGTH_PAYG_CHALLENGER` |
| VEED Fabric via Hedra | `PROVED` | `PROVED` (Fast up to 3m10s) | `PROVED` | `PROVED` | Hedra's current API terms allow training and prohibit product integration absent another order | `CONTRACT_BLOCKED` |
| Creatify Aurora | `PROVED` | `CONDITIONAL`: current live direct API says 5 min, while older indexed official pages said 60 s; fal limit is undocumented | `UNKNOWN`: request exposes no explicit aspect control | `PROVED` | Direct terms grant broad content rights and the public privacy policy does not establish exact media retention/training controls; fal adds a processor and public-file constraints | `FULL_LENGTH_QUALITY_CHALLENGER_ACTIVATION_BLOCKED` |
| Synthesia | `FAIL` for the required automated fictional-still route: Enterprise UI supports WAV, but API upload is MP3-only and Personal Avatar requires a real person's consent flow | `PROVED` in Enterprise UI only | `PROVED` | `FAIL` for exact WAV plus fictional still automation | Strong enterprise no-customer-training posture | `ENTERPRISE_CONDITIONAL` |
| Runway Avatar Video API | `PROVED` for one-image custom avatar plus uploaded audio; exact immutable-audio behavior is unproved | `UNKNOWN` | `UNKNOWN` | `PROVED`: `/v1/avatars` and `/v1/avatar_videos` are documented | Self-service terms permit input/output training and a perpetual sublicensable license; Enterprise advertises no training but needs applicable contract proof | `API_CHALLENGER_ACTIVATION_BLOCKED` |
| ImagineArt | UI accepts still + audio through several third-party models | Model-dependent/unclear | Model-dependent | `FAIL`: no reviewed lipsync API contract | Third-party routing and broad content license add uncertainty | `AGGREGATOR_ONLY` |
| Higgsfield | UI supports talking-avatar model selection | Engine-dependent | UI claims all required aspects | `UNKNOWN` for a stable exact-audio API | Self-service content is used for training; enterprise can contract out | `AGGREGATOR_ONLY` |
| Superhuman | `FAIL`: it is an AI work/productivity platform with a HeyGen connector | `FAIL` | `FAIL` | Connector, not renderer | Adds another orchestration/data boundary | `NOT_A_VIDEO_PROVIDER` |
| LongCat-Video-Avatar 1.5 | `PROVED` for image plus audio | Long-form focus is documented | `UNKNOWN`: hosted API exposes resolution but no aspect control | `PROVED` through fal.ai | Open model, but fal private-input constraints apply | `OPEN_MODEL_BENCHMARK` |

## Recommended shortlist

| Disposition | Candidate | Why it remains in contention | Load-bearing uncertainty |
|---|---|---|---|
| `PRIMARY_COMPATIBILITY_TEST` | HeyGen Avatar IV Photo | Direct still-plus-audio v3 API, both required aspects, 1080p, motion prompting, and the lowest credible entry friction | Current official guides list PNG/JPEG rather than the accepted WebPs; full 127.7-second allowance, exact fictional-image moderation, self-service opt-out/deletion, and real output quality need proof |
| `TECHNICAL_CHALLENGER_ACTIVATION_BLOCKED` | JoggAI v2 Photo Avatar | The clearest published technical fit: exact WAV up to ten minutes, custom photo avatar, audio-matched length, all required aspects, and asynchronous IDs | Photo Avatar API access appears tied to the USD 399/month Professional API plan; general privacy/terms permit model training/service improvement and a broad content license, while processor/data-location text contains literal placeholders |
| `FULL_LENGTH_PAYG_CHALLENGER` | VEED Fabric 1.0 through fal.ai | The official VEED route accepts any image plus WAV, publishes a five-minute limit, provides regular and fast modes, returns MP4, and uses per-second fal.ai billing with no subscription minimum | Output is capped at 720p; aspect behavior, exact audio-stream handling, fal retention/deletion/region, and whole-presenter continuity need exact-account and media proof |
| `GOVERNANCE_CHALLENGER` | Colossyan NEO/Instant Avatar | Its Organization/Enterprise terms provide the strongest reviewed no-training commitment, alongside long-form plans, image-created Instant Avatar, direct `audioUrl`, explicit canvas dimensions, and shoulder/bubble variants under NEO | Self-service terms permit internal research, service improvement, new-product development, and marketing use; an Order Form/API Agreement/DPA, Instant access, synthetic identity admission, output audio behavior, and motion quality need proof |
| `FULL_LENGTH_QUALITY_CHALLENGER_ACTIVATION_BLOCKED` | Creatify Aurora through direct API or fal | Single synthetic image plus WAV, expressive whole-person intent, model controls, and inspectable async APIs | Direct terms grant broad content rights and public privacy material does not prove exact media retention/training behavior; current direct API says five minutes but older indexed official pages said 60 seconds; no explicit aspect control; fal private-input constraints remain |
| `API_CHALLENGER_ACTIVATION_BLOCKED` | Runway `gwm1_avatars` / Avatar Videos | A newly documented API creates a custom avatar from one image and generates avatar video from uploaded audio or text | Self-service terms permit training on inputs/outputs and grant a perpetual transferable sublicensable license; Enterprise advertises no training but exact contract applicability, 127.7-second capacity, aspect control, resolution, immutable 24 kHz behavior, and pricing remain unproved |
| `OPEN_MODEL_BENCHMARK` | LongCat-Video-Avatar 1.5 | Open MIT code, image-plus-audio control, long-form focus, and hosted inference | Portrait/aspect control is not documented; high hosted cost, local GPU burden, provider retention, identity continuity, and API stability remain |

This was the 2026-09-03 pre-diagnostic ranking. Later v8/v9 human evidence
rejects the unchanged HeyGen single-photo/static-composition route; the Issue
#516 controlling amendment replaces it as the next-step decision.
VEED Fabric through fal.ai is the fastest published pay-as-you-go full-length
challenger after its Gate 0 privacy path clears. JoggAI remains the strongest
documented platform-specific full-duration route if its custom-photo API can be
enabled without accepting unclear data-location terms or buying a plan merely
for discovery. Colossyan is the preferred procurement/governance fallback.
Aurora is valuable for visual-quality comparison and may support full length,
but it must not win Cut 1 until its conflicting duration history, portrait
behavior, content terms, and exact-account route are resolved by evidence.

## Candidate evidence matrix

### Shortlisted candidates

| Candidate | Input and output evidence | Published limits and indicative cost | Privacy/rights evidence | Current conclusion |
|---|---|---|---|---|
| HeyGen Avatar IV Photo | [Image-to-Video](https://developers.heygen.com/image-to-video-1) and [Photo Avatar](https://developers.heygen.com/photo-avatar) document custom audio and motion controls but list PNG/JPEG input, not the exact accepted WebPs; [motion prompts](https://help.heygen.com/en/articles/12805098-fine-tune-avatar-gestures-and-movements-with-custom-motion-prompts-avatar-iv-v) remain a quality control | [Enterprise pricing](https://developers.heygen.com/docs/enterprise-pricing) lists Avatar IV Photo at 0.1 credit/s and USD 0.50/credit, equivalent to USD 0.05/s; [API plans](https://www.heygen.com/api-pricing) document a USD 5 pay-as-you-go entry and a separate API wallet; the six unique cells estimate USD 36.33 before failures/repeats | [Terms](https://www.heygen.com/terms), [privacy](https://www.heygen.com/privacy), and the applicable enterprise agreement require account-specific DPA/no-training confirmation | Best first test only after exact accepted WebP compatibility or a separately authorized lossless PNG derivative is proved |
| JoggAI v2 Photo Avatar | [Custom-audio video](https://docs.jogg.ai/api-reference/v2/API%20Documentation/AvatarVideosWithAudioSource), [asset upload](https://docs.jogg.ai/api-reference/v2/API%20Documentation/UploadMedia), and [Photo Avatar](https://docs.jogg.ai/api-reference/v2/API%20Documentation/CreatePhotoAvatar) document WAV, ten-minute audio, three aspects, audio-matched duration, and async IDs. However, audio requirements specify 44.1 kHz while accepted WAVs are immutable 24 kHz, and Photo Avatar generates new image variants before motion | [API pricing](https://www.jogg.ai/api-pricing/) lists USD 399/month for 800 Professional credits and Photo Avatar creation; six 118–128-second cells round to about eight video credits, but plan eligibility must be confirmed | [Privacy](https://www.jogg.ai/privacy-policy/) makes face-data training opt-in, but its general-purpose section permits model training and its processor/location sentence has placeholders. [Terms](https://www.jogg.ai/terms-of-use/) grant a transferable, sublicensable content license while stored for operating, improving, and promoting the service and do not guarantee deletion | Strong full-duration technical challenger only after unchanged 24 kHz acceptance and presenter-derivative lineage are proved; activation is also contract/privacy-blocked |
| VEED Fabric 1.0 through fal.ai | [Official API page](https://www.veed.io/api) and [Fabric route](https://www.veed.io/tools/fabric-1.0-api) document any still/illustration/mascot plus MP3/WAV/M4A, regular or fast generation, 480p/720p MP4, async jobs, and output up to five minutes | Regular costs USD 0.08/s at 480p or USD 0.15/s at 720p; Fast costs USD 0.10/s or USD 0.20/s. At raw accepted duration, Myra in both aspects is about USD 38.30 regular 720p or USD 51.06 Fast; six cells are about USD 109.00 or USD 145.34 before retries and provider rounding | VEED says the API is hosted and billed by fal.ai. fal [retention](https://fal.ai/docs/documentation/model-apis/inference/payloads) stores IO by default and does not delete input-CDN files with the request; [file documentation](https://fal.ai/docs/documentation/development/working-with-files) says fal CDN URLs are public. Exact private input transport, expiry, deletion, region, and model-processing flow must clear Gate 0 | Best published no-subscription full-length challenger, subject to a non-public input route, Gate 0, and exact aspect/media proof |
| Colossyan NEO/Instant Avatar | [Create avatar](https://docs.colossyan.com/avatar-creation/create-avatar), [manual video generation](https://docs.colossyan.com/video-generation/video-generation/generating-a-video-manually), and [avatar API](https://docs.colossyan.com/basics/openapi/list-avatars) prove image input, `audioUrl`, explicit canvas size, and NEO shoulder/bubble variants | [Pricing](https://www.colossyan.com/pricing/) supports long-form plans and API minutes; exact synthetic-avatar account price/limits require a quote | [Self-service terms](https://www.colossyan.com/terms/) permit broad research, improvement, product-development, and marketing uses. The same page's Organization Terms prohibit customer-material model training except the customer-specific avatar. [Security](https://www.colossyan.com/security/) adds SOC 2 Type II, encryption, and Enterprise EU/US residency claims | Enterprise governance challenger only; exact Order Form, API Agreement, DPA, Instant access, and fictional-identity compatibility need written proof |
| Creatify Aurora | The current live [direct POST API](https://docs.creatify.ai/api-reference/aurora/post-aurora) and [GET API](https://docs.creatify.ai/api-reference/aurora/get-aurora) say an AI-generated image plus WAV may run for five minutes, but older indexed copies of those same official pages said 60 seconds. The [fal API](https://fal.ai/models/fal-ai/creatify/aurora/api) publishes no duration limit, and neither route exposes an explicit aspect control | fal lists USD 0.07/s at 480p and USD 0.14/s at 720p. If full six-cell use is proved, per-output whole-second billing covers 728 seconds: about USD 50.96 or USD 101.92. Direct API pricing is versioned in credits and has changed | [Creatify terms](https://creatify.ai/terms) grant a perpetual, sublicensable license over input prompts/images and outputs for providing, promoting, and improving the service. Its direct [privacy policy](https://creatify.ai/privacy) discusses personal-data sharing and deletion but does not freeze exact uploaded-media retention, training, subprocessors, or processing region. [fal privacy](https://fal.ai/legal/privacy-policy) adds a separate processor and the public-file/retention constraints above | Full-length quality challenger, but direct and fal activation remain blocked until exact-account privacy, rights, duration, aspect, and input-transport controls pass Gate 0 |
| Runway Avatar Videos | The current [API reference](https://docs.dev.runwayml.com/api/) lists custom-avatar creation and “Generate avatar video from audio or text”; [supported formats](https://help.runwayml.com/hc/en-us/articles/42963684322323-Supported-file-types) include WebP and PCM WAV | [Pricing](https://docs.dev.runwayml.com/guides/pricing/) documents `gwm1_avatars`, but the exact batch-video cost/duration contract needs live account verification | [Self-service terms](https://runway.com/terms-of-use) allow inputs and outputs to train/improve models and grant a perpetual, transferable, sublicensable license. [Enterprise](https://runway.com/enterprise) advertises no training and output ownership, while the [privacy policy](https://runway.com/privacy-policy) states purpose-based retention and international transfers. Exact account contract, DPA, retention, deletion, region, and API applicability must be frozen | Activation-blocked API challenger: Enterprise may clear governance, but exact full duration, aspects, output resolution, and unchanged-audio behavior still need a zero-spend capability check |
| LongCat-Video-Avatar 1.5 | [Official repository](https://github.com/meituan-longcat/LongCat-Video), [vLLM Omni recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/meituan-longcat/LongCat-Video-Avatar-1.5.md), and [fal endpoint](https://fal.ai/models/fal-ai/longcat-single-avatar/image-audio-to-video) prove image/audio and long-form intent, but the hosted schema exposes resolution and segments without aspect control | Hosted 720p indicative USD 0.30/s makes six cells about USD 218.01; local execution needs substantial GPU memory | [fal payload handling](https://fal.ai/docs/documentation/model-apis/inference/payloads), [fal terms](https://fal.ai/legal/terms-of-service), and [fal CDN](https://fal.ai/docs/documentation/model-apis/fal-cdn) need retention/public-URL review | Optional benchmark; portrait support is unknown and it is not the fastest production route |

### Baselines, exploratory routes, and rejected Cut 1 routes

| Disposition | Candidate/category | Evidence and reason |
|---|---|---|
| `BASELINE_ONLY` | Hedra Avatar | [Model](https://www.hedra.com/models/video/hedra/avatar) accepts exact image/audio, both aspects, up to ten minutes and 540p/720p/1080p. It is a valuable talking-head baseline, but full upper-body credibility is unproved. Indicative six-cell cost is USD 36.33 at 720p or USD 45.42 at 1080p. |
| `BASELINE_ONLY` | D-ID Talks and Sync | [D-ID Talks](https://docs.d-id.com/reference/createtalk) and [Sync API](https://sync.so/docs/api-reference/api-overview) / [Sync 3](https://sync.so/docs/models/sync-3) are useful lip-sync comparators, but their head-centric boundary does not prove the desired waist-up/body expressiveness. |
| `CONTRACT_BLOCKED` | Hedra Avatar and VEED Fabric accessed through Hedra | The [Hedra Avatar API](https://www.hedra.com/develop/models/video/hedra-avatar) and [VEED Fabric Fast model on Hedra](https://www.hedra.com/models/video/veed/fabric-10-fast) satisfy long-form technical inputs. However, [Hedra API terms](https://www.hedra.com/api-terms) restrict use to personal/internal business purposes, prohibit integration into customer applications absent another order, permit customer content to improve/train models, and pass inputs to model providers. This block applies to Hedra-hosted access, not VEED's distinct official fal.ai route. No NarraTwin adapter or egress should use the Hedra route without a superseding enterprise agreement. |
| `AGGREGATOR_ONLY` | Higgsfield | [Lipsync overview](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-lipsync-voiceover-and-aspect-ratios) and [talking-avatar page](https://higgsfield.ai/ai-talking-avatar) show a broad model studio, but no stable acceptance-grade exact-audio API was established. [Current policy summary](https://higgsfield.ai/blog/terms-of-use-privacy-policy-update) says self-service content is used for training; enterprise can contract no-training and deletion terms. |
| `AGGREGATOR_ONLY` | ImagineArt | [Lipsync documentation](https://docs.imagine.art/video-tools/lipsync) offers Kling Avatar, InfiniTalk, OmniHuman, and Fabric with uploaded audio, but this review found no model-pinned lipsync API contract. [Terms](https://docs.imagine.art/policies/terms-and-conditions) include a broad perpetual sublicensable content license and third-party models, although training is opt-in by default. Useful for manual discovery, not the authoritative T06 route. |
| `MANUAL_EXPLORATION_ONLY` | Runway Character Script web app | [Character Script to Video](https://help.runwayml.com/hc/en-us/articles/51285026291219-Character-Script-to-Video) accepts a character image and own audio but publishes no duration boundary and points to stitching for longer sequences. This web app is distinct from the newly documented Runway Avatar Video API challenger. [Act-Two](https://help.runwayml.com/hc/en-us/articles/42311337895827-Performance-Capture-with-Act-Two) remains a separate 30-second route requiring driving performance video. |
| `ENTERPRISE_CONDITIONAL` | Synthesia | [Script audio](https://docs.synthesia.io/docs/script) supports WAV up to five minutes per Enterprise scene without speed changes, but the [API upload](https://docs.synthesia.io/reference/upload-script-audio) currently documents MP3 only and custom avatar compatibility with a fictional still is unproved. [AI governance](https://www.synthesia.io/legal/ai-governance-practices) states customer inputs/outputs are not used to pre-train. |
| `BETA_AGGREGATOR` | ElevenLabs Avatars/Image & Video | [Avatar docs](https://elevenlabs.io/docs/overview/capabilities/image-video/avatars) describe persistent identities but say Avatar API access is not available at launch. The separate [Image & Video API](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/image-and-video) exposes Creatify Aurora with image+audio on Pro, adding an intermediary without removing Aurora's unresolved full-duration boundary. |
| `EXPLORATORY` | Argil and AKOOL | Potential presenter platforms, but this checkpoint did not establish enough official long-form, exact-audio, full-body, privacy, deletion, and stable-API evidence to displace the shortlist. |
| `REJECT_CUT1` | Google Veo, Flow, Pomelli | [Veo API](https://ai.google.dev/gemini-api/docs/video), [Flow](https://labs.google/fx/tools/flow), and [Pomelli](https://blog.google/innovation-and-ai/models-and-research/google-labs/pomelli/) are cinematic/marketing generation tools, not demonstrated exact two-minute audio-driven presenter renderers. Veo clip durations are far below the requirement. |
| `REJECT_CUT1` | Seedance | [Seedance 2.5 in Runway](https://help.runwayml.com/hc/en-us/articles/53542207042323-Creating-with-Seedance-2-5) and [Seedance 1.5 Pro](https://seed.bytedance.com/en/seedance1_5_pro) are generative clip routes, not accepted exact long-form presenter pipelines. |
| `REJECT_CUT1` | OmniHuman 1.5 alone | [Hosted model evidence](https://www.hedra.com/models/video/bytedance/omnihuman-15) is promising for audio-driven humans, but the published 16:9-only route fails the required portrait cell. Indicative six-output cost would be USD 116.27 even before solving that gap. |
| `REJECT_CUT1` | Runway Act-Two | [Act-Two](https://help.runwayml.com/hc/en-us/articles/42311337895827-Performance-Capture-with-Act-Two) requires a driving performance video and publishes a 30-second boundary, adding an unnecessary input/identity dependency. |
| `REJECT_CUT1` | Kling and similar short clips | Published one-minute or shorter clip boundaries do not satisfy the 117.7–127.7-second accepted narrations without stitching and continuity risk. |
| `CONDITIONAL_OR_FUTURE` | Tavus, DeepBrain and digital-twin platforms | [Tavus video request](https://docs.tavus.io/api-reference/video-request/create-video) supports script or audio with an enrolled Replica, but NarraTwin has still images rather than consented replica-training footage. Tavus conversational video is more relevant to later interactive Mode 2. |
| `NOT_A_VIDEO_PROVIDER` | Superhuman | [Superhuman](https://superhuman.com/) provides mail/docs/AI-agent productivity software. Its HeyGen store item is a connector to HeyGen, while [Developer Terms](https://superhuman.com/legal/terms/developer) govern integrations and agents. It offers no independent render model or T06 capability and would add unnecessary indirection. |
| `REJECT_DEFAULT` | Local SadTalker/Wav2Lip-class stack | License, model-weight, quality, duration, GPU, packaging, maintenance, and security burdens make this slower than a bounded hosted demo. Wav2Lip remains unsuitable for the default external/commercial path under its published restrictions. |

## Source conflicts and facts that documentation cannot prove

- VEED routes must be kept provider-specific. VEED's official fal.ai route
  publishes up to five minutes; Hedra publishes 3m10s for its Fabric Fast
  hosting. Hedra's terms govern the latter, not the direct fal.ai route.
- Creatify's current live POST and GET API schemas say five minutes, while
  older indexed copies of those same official pages said 60 seconds and fal's
  schema publishes no limit. That change history and the absence of explicit
  aspect control require a no-spend account check; documentation drift is not
  proof that a 127.7-second portrait request will succeed.
- JoggAI's API documentation is unusually complete for Cut 1 technical fit,
  but “training off by default” is stated only in its face-data section. The
  general privacy section permits training service models, the terms grant a
  broad content license, and the processor/region sentence contains literal
  example placeholders. Activation therefore needs written all-input/output
  terms, not an inference from the face-data clause.
- fal stores request IO for 30 days by default. `X-Fal-Store-IO: 0` suppresses
  JSON history but does not remove CDN files, and deleting a completed request
  does not delete its input-CDN files. fal documentation says those CDN URLs
  are public. The accepted private WAV must never be uploaded to that public
  CDN; use an enterprise/private transport or an owner-controlled, short-lived
  signed source URL only after explicit authority; never use a public CDN for
  accepted input media.
- The supplied JoggAI-versus-HeyGen page is JoggAI-authored marketing. It is a
  discovery source only; no comparative claim from it is used as acceptance
  evidence.
- Superhuman's HeyGen connector does not make Superhuman a video engine. It
  would still depend on HeyGen and add another authorization/data-flow layer.
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

## Finding classification and disposition

| Finding | Classification | Impact and smallest route | Disposition |
|---|---|---|---|
| Building an adapter before exact-media compatibility is observed can institutionalize the wrong provider boundary | `REQUIRED_CONTRACT` | Run a bounded short smoke, then full Myra in both aspects, before TDD adapter scope | Demo-before-code ladder retained |
| Aurora was classified from a stale 60-second official schema even though the live schema now says five minutes; portrait control remains absent | `REQUIRED_CONTRACT` | Record the documentation conflict and require exact-account duration/aspect proof | Aurora restored as conditional full-length quality challenger |
| Runway was described as having no applicable API after its official reference added custom Avatar and Avatar Video endpoints | `REQUIRED_CONTRACT` | Separate the web app from the new API and require exact duration/aspect/audio proof | Runway restored as a conditional API challenger |
| JoggAI's 44.1 kHz specification and generated photo-avatar variants do not prove unchanged 24 kHz acceptance or accepted-still identity lineage | `REQUIRED_CONTRACT` | No resampling or silent derivative promotion; test unchanged diagnostic bytes and govern any new presenter derivative | JoggAI exact-media fit remains conditional |
| LongCat's hosted API exposes resolution but not aspect control | `REQUIRED_CONTRACT` | Require portrait output proof before shortlist promotion | Remains optional benchmark; both-aspect claim removed |
| Treating VEED Fabric through fal.ai as though Hedra's terms govern it erases a distinct five-minute pay-as-you-go route | `REQUIRED_CONTRACT` | Split model capability from hosting/provider terms and price each route independently | Direct VEED/fal restored as a challenger; Hedra-hosted route remains blocked |
| Hedra's published API terms prohibit application integration and allow content use for model improvement/training | `CRITICAL_BLOCKER` for a NarraTwin product adapter under those terms | Obtain a superseding enterprise order with explicit integration and no-training terms | Hedra-hosted route contract-blocked; no call authorized |
| JoggAI's face-data opt-in clause does not override general model-training language, broad content rights, deletion uncertainty, or placeholder location text | `REQUIRED_CONTRACT` for provider activation | Obtain written all-input/output no-training, content-rights, DPA/subprocessor/region, retention, and deletion commitments for the exact account | JoggAI stays a technical challenger; activation blocked |
| fal defaults can persist IO, leave input CDN objects undeleted, expose CDN URLs publicly, and automatically retry | `CRITICAL_BLOCKER` for sending accepted private media through fal CDN; otherwise `REQUIRED_CONTRACT` for activation | Require a private or owner-controlled expiring input path, no IO storage, no automatic retry/fallback, lifecycle limits, exact output download/hash/probe, deletion receipt, and account-specific privacy proof | Direct VEED/Aurora/LongCat calls blocked until the exact package proves every control |
| Colossyan self-service content rights differ materially from its Organization terms | `REQUIRED_CONTRACT` for provider activation | Require the applicable Order Form, API Agreement, DPA, no-training commitment, residency, and written fictional-anchor eligibility | Colossyan remains Enterprise governance challenger only |
| HeyGen self-service content may be used for training unless opted out | `REQUIRED_CONTRACT` for provider activation | Prove enterprise exclusion or completed self-service opt-out before any asset egress | HeyGen stays first compatibility candidate, not activated |
| HeyGen's current image routes list PNG/JPEG while every governed T06 presenter input is an immutable WebP | `REQUIRED_CONTRACT` for exact-media compatibility | Prove direct accepted-WebP admission or separately authorize and checksum-bind a lossless PNG derivative without replacing the WebP authority | HeyGen exact-still fit is conditional; no silent conversion or upload is authorized |
| Runway self-service terms permit training on inputs/outputs and grant a perpetual transferable sublicensable license | `REQUIRED_CONTRACT` for provider activation | Use no self-service route; require an applicable Enterprise agreement, DPA, no-training, retention, deletion, region, and API-route proof | Runway remains a technical challenger; all activation is blocked until Enterprise controls are proved |
| Creatify's direct terms grant broad content rights while its public privacy policy does not define exact uploaded-media retention, training, subprocessors, or processing region | `REQUIRED_CONTRACT` for provider activation | Require exact-account terms, DPA, no-training, retention/deletion, subprocessor/region, and direct-versus-fal flow proof | Creatify remains a quality challenger; both direct and fal activation are blocked |
| Marketing and short samples cannot prove full-duration identity, lip sync, motion, or continuity | `REQUIRED_CONTRACT` | Exact-output probes plus independent human review on full Myra landscape/portrait | Deferred to authorized demo evidence |
| Superhuman, ImagineArt, and Higgsfield add orchestration or model aggregation rather than a uniquely superior acceptance boundary | `OUT_OF_SCOPE` as primary T06 engines | Retain for discovery/manual comparison; integrate the underlying provider directly if selected | Not in first paid bake-off |
| Open/local routes offer control but add GPU, packaging, license, and quality work | `ADVISORY_DEBT` | Preserve LongCat as an optional benchmark after hosted compatibility | Does not block fastest hosted test |

## Demo-before-code recommendation

Do not build or modify the NarraTwin adapter merely because an API appears to
fit on paper. Use these gates in order:

1. **Gate 0 — zero-network readiness.** Verify account/tier, applicable
   DPA/no-training terms, synthetic-fictional identity eligibility, region,
   retention/deletion, exact API/model/version/revision with defaults and
   fallbacks disabled, SecretRef, current price, call count, and spend ceiling.
   Prove exact accepted WebP compatibility for each selected route. If HeyGen
   rejects WebP, stop until a separate route authorizes a lossless PNG derivative
   with source/derivative hashes, conversion receipt, rights, and review; never
   substitute or silently convert a presenter input.
   Freeze the request package without exposing a key. For fal, prohibit public
   input-CDN upload and require `X-Fal-Store-IO: 0`, `X-Fal-No-Retry: 1`, model
   fallback disablement, an object lifecycle, and an approved private or
   owner-controlled expiring source URL.
2. **Gate 1 — short compatibility smoke.** Use the same separately labelled
   10–15-second diagnostic excerpt of an accepted WAV with the same accepted
   image. First compare HeyGen and VEED Fabric through fal.ai if their Gate 0
   account/privacy stops clear; add Aurora as the short quality benchmark.
   Include JoggAI or Colossyan when suitable API access already exists. Do not
   buy an annual or USD 399 plan merely to run this gate without separate owner
   approval. The excerpt
   is a derivative test input only; it cannot replace, shorten, or become an
   accepted T05/T06 artifact. No source WAV changes.
3. **Gate 2 — full-duration risk test.** Render the longest/hardest accepted
   narration, Myra at 127.661917 seconds, in both landscape and portrait on the
   best one or two candidates whose documented or demonstrated route accepts
   the whole WAV in one job. Aurora or Runway may enter only after the exact
   account proves full duration and both aspect outputs without altering the
   audio. This detects duration, drift, aspect, continuity, and pacing failures
   that a short sample cannot expose.
4. **Gate 3 — evidence-based selection.** Compare exact media probes, identity
   continuity, lip sync, motion, severe defects, repeatability, latency, cost,
   privacy/deletion evidence, and independent human review. Select a primary
   and a compatible fallback only after this evidence exists.
5. **Gate 4 — TDD adapter and final cells.** Only then freeze code scope, commit
   executable RED, implement the smallest provider-neutral adapter correction,
   and generate the six final presenter/aspect cells under separate authority.

This ladder avoids expensive code churn while still preventing a polished
short clip from being mistaken for proof that the complete narration works.

## Normalized operational comparison

These figures normalize the actual next decision rather than only quoting a
provider's headline rate. They exclude tax, failed jobs, retries, storage, and
unknown provider rounding. “Time to first demo” is an operational estimate,
not a vendor SLA. No row authorizes purchase, account creation, credentials,
egress, or a call.

| Route | One 15 s diagnostic | Full Myra, two aspects | All six final cells | Fixed floor or access stop | Earliest credible demo | Duration/aspect boundary |
|---|---:|---:|---:|---|---|---|
| HeyGen Avatar IV Photo | About USD 0.75 | About USD 12.77 if the account permits 127.7 s | About USD 36.33 | Exact wallet/account minimum and self-service opt-out need live proof | Same day after Gate 0 and account access | Both aspects documented; full Myra duration conditional |
| VEED Fabric regular 720p through fal.ai | About USD 2.25 | About USD 38.30 | About USD 109.00 | No subscription/minimum published; fal privacy and exact model flow remain stops | Same day after Gate 0 and fal access | Five minutes proved; 720p ceiling; exact aspect result conditional |
| VEED Fabric Fast 720p through fal.ai | About USD 3.00 | About USD 51.06 | About USD 145.34 | Same fal Gate 0 stop | Same day after Gate 0 and fal access | Five minutes claimed for Fabric; exact Fast limit/aspect result must be confirmed |
| JoggAI Photo Avatar from scratch | 3 credits: avatar plus one render | 6 credits: avatar plus two rounded renders | 14 credits: three avatars plus six rounded renders | Professional publishes USD 399/month for Photo Avatar; privacy/terms and generated-derivative stops must be resolved | Account/procurement dependent | Ten minutes and all aspects documented; unchanged 24 kHz input is conditional |
| Colossyan Instant Avatar | Not reliably priceable from public API terms | Not reliably priceable from public API terms | Not reliably priceable from public API terms | Professional is USD 59/month annual and includes API minutes, but Instant API access requires support and synthetic eligibility proof | Support/account dependent | Platform duration and canvas fit; exact Instant API eligibility conditional |
| Creatify Aurora through fal.ai at 720p | About USD 2.10 | About USD 35.75 only if full duration and aspect pass | About USD 101.92 only if all six are proved | Usage pricing; fal Gate 0 stop and current duration/aspect uncertainty | Same day for short benchmark only | Live direct docs say five minutes; historical conflict and portrait remain conditional |
| Runway Avatar Video API | Account pricing check required | Unknown | Unknown | New endpoint/account and applicable terms must be confirmed | Account dependent | Full duration, aspects, resolution, and exact audio are unknown |

The fastest evidence path is therefore HeyGen plus direct VEED/fal for the same
short diagnostic, with Aurora only as a visual-quality comparator. If both
primary probes pass, run full Myra in both aspects on the best route. JoggAI
should replace or supplement VEED when a governed Professional account already
exists; buying it solely for the smoke test requires separate authorization.

## Exact call lineage and billable-unknown behavior

Every future demo manifest must persist the canonical request hash and any
provider-supported idempotency key before egress. It must freeze the API
version, endpoint, engine/model ID and revision, explicit aspect/resolution,
input hashes, account tier, price basis, call and generated-second ceilings,
and disabled retry/fallback settings. The receipt must capture the provider
request/job/result IDs, response/body hash, billing units, timestamps, and
final status without logging credentials, signed URLs, or media.

Use a signed, timestamp-checked, replay-resistant webhook only when the route
documents it; otherwise use bounded polling. A timeout, disconnect, or 5xx
after egress is `BILLABLE_UNKNOWN`: do not submit again until the provider job
and wallet are reconciled. HeyGen's 24-hour idempotency key should be used.
fal's request/gateway IDs, signed webhook, no-retry, no-fallback, IO-storage,
object-lifecycle, and billable-unit controls must be explicit. JoggAI documents
retrying system errors but no idempotent create key, so an ambiguous create
response is a manual stop. After success, download once, hash and probe the
output, capture deletion evidence, and retain the accepted WAV as authority.

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

1. State which governed accounts are actually available: HeyGen, JoggAI,
   Colossyan, fal.ai, direct Creatify, and Runway Enterprise. Include Hedra only
   if a superseding agreement clears its published contract stop. Runway
   self-service and direct Creatify remain activation-blocked until the exact
   account clears the controls above. An account name, tenant, project ID,
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

Recommended first package shape after Gate 0 is complete: one call each for the
available HeyGen and direct VEED/fal routes, plus one Aurora quality benchmark
when fal privacy is accepted; concurrency one, no automatic retry, the same
10–15-second diagnostic excerpt and presenter image, and a small aggregate
spend ceiling. JoggAI or Colossyan should be included when the required API
access already exists. The exact call count and USD cap must be calculated from
the accounts that are genuinely available and explicitly authorized before any
egress. LongCat is optional and should be added only if the owner accepts its
materially higher cost.

## Decision rule

A provider passes the research stage only when the exact account and API route
can run the bounded demo without violating identity, immutable-audio, privacy,
security, cost, deletion, or provenance rules. A short demo can eliminate an
incompatible option; it cannot select the final provider by itself. The
full-duration two-aspect test and human review are mandatory before code or the
six-cell generation route is frozen.

## Issue #514 evidence amendment: observed cost and actual output

This section appends evidence gathered after the original research freeze. It
does not replace the exact-account price preflight required before another paid
call. All three providers received the same 14.747-second Meera diagnostic
image/audio pair.

### Exact observed three-provider diagnostic

| Route | Exact or estimated cost | Observed output | Human disposition |
|---|---:|---|---|
| HeyGen Avatar IV image route | **USD 0.55 exact wallet delta** | 1280×720; 14.76 s | Best relative lip result, but still unacceptable; head cropped, weakest clarity, synthetic background |
| VEED Fabric through fal.ai | **USD 2.208 public-rate estimate** | 1152×768; 14.72 s; 28 reported billable units | Best clarity, but lip and motion realism unacceptable; exact account line item unavailable |
| Creatify Aurora through fal.ai | **USD 2.10 exact authenticated calculation** | 1216×768; 14.76 s | Best body movement, but lips and realism unacceptable; omitted 48.995 ms of non-silent audio tail |

The aggregate was USD 4.858 when the VEED public-rate estimate is used. The
owner rejected every output for final use. A learned SyncNet metric was
supporting diagnostic evidence only and did not override visible phoneme,
co-articulation, expression, framing, identity, or background-realism defects.

The result does **not** mean that fal.ai is inherently expensive or HeyGen is
always cheapest. fal.ai is a model marketplace and serving layer; VEED Fabric,
Aurora, Sync, and OmniHuman each set different output-second rates and rounding
rules. For this exact short workload, current list rates explain the direction:
HeyGen Avatar IV Photo 720p/1080p is USD 0.05 per output second plus USD 1 for a
reusable Photo Avatar creation; VEED Fabric 720p is USD 0.15 per output second;
Aurora 720p is USD 0.14 per output second with upward-second rounding; Sync-3
is approximately USD 0.1333 per output second; and OmniHuman v1.5 is USD 0.16
per output second. These are dated discovery figures, not activation authority.

## Google Flow and Gemini Omni: corrected capability decision

Google Flow is not rejected as a video-generation product. As of 2026-09-03,
Google describes Flow as a creative studio using Gemini Omni and Veo, with
text/image/video inputs, Characters, Avatars, and both portrait and landscape.
Its credit page says non-subscribers receive 50 daily credits, while its current
get-started page says access requires Plus, Pro, Ultra, or a qualifying
Workspace plan. That official access documentation currently conflicts, so an
exact account check—not a generic “free tier” assumption—must decide access.
It remains a meaningful visual-quality candidate.

The current roadblock is narrower: Flow/Gemini Omni does not meet NarraTwin's
**exact-artifact presenter contract** today.

1. The Gemini Omni API limitation states: “Uploading audio references is unsupported”
   in the current API. Audio in a video reference is ignored and
   voice editing is unsupported. Veo and Omni generate their own audio. They
   therefore cannot use the exact human-approved Meera, Myra, and Raj WAV bytes
   as the governing lip-sync driver.
2. Current Flow generation lengths are 4, 6, 8, or 10 seconds depending on the
   model and operation. The accepted narration tracks are 117.981917,
   127.661917, and 117.701917 seconds. Segmenting and extending generated clips
   would introduce identity, motion, audio, dialogue, continuity, and joining
   risks and would still not preserve the exact accepted WAV.
3. Flow Characters can preserve an appearance from one or two images and use a
   selected or custom generated voice. That is valuable for concept work, but a
   generated voice is not the exact accepted T05 artifact.
4. Flow's `@me` Avatar represents the account owner's own visual and audio
   likeness after mobile capture. It is a future product-owner Digital Twin
   candidate, not the fictional synthetic Meera/Myra/Raj route.
5. The Flow web product is a human-operated creative interface. A NarraTwin
   server adapter requires a stable, provider-native API contract with request,
   receipt, retry, billing, output, deletion, and exact-artifact behavior.
6. Before any upload, the exact account must disable “Help improve Google Flow”
   when required and pass privacy, reviewer-access, retention, deletion, region,
   terms, and input-rights review. Free credits do not grant egress authority.
7. Google states that a visible watermark is applied automatically for residents
   of India, South Korea, or Vietnam. A visible watermark fails professional T06
   media. For the current India-resident account, Flow is **concept-only** unless
   exact-account evidence proves the output is not visibly watermarked; never
   remove, conceal, or crop a required watermark.

### Permitted exploration role

Google Flow may be explored as a **visual concept and B-roll benchmark** after a
separate zero-network privacy and input-rights preflight. A free-credit,
human-operated comparison may evaluate a fictional synthetic character's
background, lighting, framing, camera language, body motion, and scene realism.
Its generated speech must be ignored and the result labelled non-admissible for
T06. It may inform a future `CinematicVideoProvider` or `BrollProvider`; it must
not masquerade as the exact-audio `AvatarProvider`.

Revisit the presenter-adapter decision when an official API demonstrates all
of: exact uploaded-audio reference support, full accepted duration or governed
lossless continuity, both aspects, identity consistency, explicit audio-output
behavior, programmatic lifecycle controls, and acceptable account terms. At
that point a thin `GoogleOmniAvatarAdapter` may enter the same contract test
suite; no domain or acceptance logic should change merely to add it.

Official sources verified 2026-09-03:

- Flow product, capabilities, free credits, and plans:
  <https://labs.google/fx/tools/flow>
- Flow model, aspect, and clip-duration matrix:
  <https://support.google.com/flow/answer/16352836>
- Flow Characters and selected/custom voice behavior:
  <https://support.google.com/flow/answer/16935308>
- Flow personal Avatar and deletion controls:
  <https://support.google.com/flow/answer/17102997>
- Gemini Omni API and exact current audio-reference limitations:
  <https://ai.google.dev/gemini-api/docs/omni>
- Veo API native generation behavior:
  <https://ai.google.dev/gemini-api/docs/veo>
- Flow interaction, upload, output, improvement, reviewer, and deletion posture:
  <https://support.google.com/labs/answer/17025472>

## Historical pre-v9 pre-implementation plan

This plan records the decision before the v8/v9 output reviews. Its optimized
HeyGen and fallback-ladder instructions are superseded by the controlling Issue
#516 amendment below; the capability-manifest, compositor, configuration, TDD,
and full-duration principles remain applicable.

These recommendations are gates for the next implementation route, not optional
notes. A later issue may change them only with newer reproduced evidence and an
explicitly frozen correction.

1. **Preserve inputs.** Keep all accepted presenter and audio bytes immutable.
   For Meera, preserve the `SOURCE_READY_NO_DERIVATIVE` anchor and use a
   separately rights-cleared photographed environment through composition.
2. **Run one optimized diagnostic before code.** The fastest current route is
   HeyGen Avatar IV Photo at 1080p with explicit `fit=contain`, full headroom,
   provider-side background removal/composition, exact accepted Meera audio,
   conservative motion, concurrency one, and no automatic retry. It needs a
   new exact package because the prior create authority is exhausted.
3. **Apply the complete quality matrix.** Reject on audio loss or drift, poor
   phoneme/mouth realism, identity instability, face/hand defects, temporal
   flicker, unnatural gaze/blink/breathing/posture/gesture behavior, head crop,
   matting halo, background/lighting/depth mismatch, codec incompatibility,
   unsafe lifecycle behavior, unbounded cost, or failed blind human review.
4. **Use a bounded fallback ladder.** If the optimized HeyGen output fails,
   preflight Sync-3 as the lip/facial challenger, then OmniHuman v1.5 as the
   motion challenger. Use Runway Act-Two only when a separately consented human
   driving-performance recording is authorized; it is not a same-input route.
   Do not repeat the unchanged rejected VEED Fabric or Aurora configurations.
5. **Require a `ProviderCapabilityManifest`.** Each implemented adapter must
   declare exact input types, duration/aspect/resolution limits, audio handling,
   retry/idempotency semantics, pricing basis, privacy/storage/deletion
   behavior, real-video support, and evidence version. Preflight rejects an
   incompatible job before upload or spend.
6. **Separate composition.** A provider-neutral `VideoCompositor` owns approved
   background plates, layout, captions, aspect packaging, and final remuxing.
   Presenter-generation adapters own only their provider-native render job.
7. **Make policy configurable without weakening invariants.** Resolution,
   aspect, duration, attempt and spend envelopes, timeouts, and provider choice
   are validated runtime policy/configuration. Consent, allowed-host/egress,
   duplicate-spend, disclosure, exact-hash provenance, media-structure, and
   deletion requirements remain fail-closed code invariants.
8. **Implement only after evidence selects a route.** Freeze an issue, base,
   branch, owned paths, budgets, manifest schema, mutation matrix, human-only
   surfaces, and stop conditions; commit RED contract tests; then add only the
   selected thin adapter. Mock/local remains the default. No provider SDK or
   branch-specific domain logic enters the core.
9. **Prove full duration before six cells.** A good short diagnostic eliminates
   incompatibility but never proves a canonical track. The selected route must
   pass full-duration landscape and portrait evidence before six-cell T06
   generation, T07 review, or T08 acceptance.

The repository is therefore provider-neutral by intent, but not magically
provider-complete: runtime switching is plug-and-play only among adapters that
already have a reviewed capability manifest and contract tests. Adding a new
provider requires a small adapter PR because its API and legal/security
semantics differ; it must not require changing product/domain behavior.

The future product-owner Digital Twin remains a separate path. HeyGen Avatar V,
Google Flow `@me`, Tavus Phoenix, and Synthesia Personal/Studio Avatar warrant a
fresh consented-likeness/voice-cloning, capture-quality, DPA/no-training,
retention/deletion, revocation, disclosure, pricing, and human-acceptance study.
Nothing in the fictional-presenter diagnostic authorizes that identity route.

## Issue #516 controlling amendment: two current walkthrough plans

The exact v8/v9 human reviews supersede the earlier recommendation to keep
tuning the same HeyGen Photo Avatar IV composition. The current strategy keeps
two plans visible so that a reviewer can understand both the full-presenter
contract and the more authentic editorial fallback. The numbering records the
two approaches requested by the product owner; it is not evidence that either
provider has passed.

### Plan A — presenter-led compatibility

Plan A evaluates **Hedra Character-3** as a continuous presenter-led route.
Hedra's current model page documents one required start frame, required audio,
audio-driven video, 540p/720p/1080p, seven aspect ratios, and up to 600 seconds.
That surface can cover each 117–128-second narration in one job and therefore
matches the current requirement for a continuously visible presenter more
directly than a stitched short-shot generator.

Plan A remains `PREQUALIFICATION_CANDIDATE_CONTRACT_BLOCKED`, not an activated
recommendation:

- Character-3 accepts a single start frame, not a multi-image identity pack.
  The broader pack can help humans select the best frame, but cannot be claimed
  as conditioning that the model never received.
- It remains in the single-image animation class that produced unacceptable
  realism in HeyGen. A materially different model can be tested, but marketing
  examples do not prove natural hands, body motion, lip sync, environment
  integration, identity, or human credibility for Meera/Myra/Raj.
- The live model page currently publishes a 600-second maximum and includes
  1080p in the same Character-3 surface. A previously indexed legacy duration
  page is no longer reproducible and is not relied upon. The **published
  600-second/1080p surface** is still a mutable product claim, so exact
  account/model admission must be checked without spend before a package is
  proposed.
- Hedra's current standard API terms prohibit integrating the API into a
  product and permit Customer Content use for model training/improvement. Its
  biometric policy also needs an exact applicability and retention decision.
  The prohibition on product integration is a hard activation stop.
  A signed governing order/DPA that expressly overrides those terms is required
  before upload, adapter code, or product use; an internal approval cannot
  override provider terms.
- “Audio-driven” does not prove that returned MP4 audio bytes are the accepted
  WAV. The approved WAV and captions remain authoritative; any final mux must
  be deterministic and timing-equivalent, and provider audio must not silently
  replace them.

The smallest Plan A experiment, if those zero-spend stops clear, is one short
Meera landscape diagnostic with one selected canonical frame and one complete
sentence. A pass permits a full-duration Myra landscape proof, then Myra
portrait; it does not directly authorize six-cell fan-out or adapter code.

### Plan B — editorial hybrid

Plan B uses a presenter-dominant edit instead of asking one model to fabricate
an uninterrupted two-minute human performance. The exact final narration and
captions remain continuous while the picture track deliberately alternates:

1. short, independently accepted presenter shots for introduction,
   transitions, emphasis, and conclusion;
2. **real product screen recordings** for every factual UI action or product
   state;
3. **deterministic source-driven graphics** and approved diagrams for concepts,
   architecture, provenance, and evidence that cannot be filmed; and
4. restrained environmental or contextual B-roll that makes no factual product
   claim.

Seedance 2.5 and Google Flow are
`VISUAL_BROLL_RESEARCH_NON_ADMISSIBLE_FOR_T06` complementary visual candidates
in this plan:

- Seedance 2.5 currently documents 4–30-second output and up to 30 image, 10
  video, and 10 audio references. It is the better direct consumer of a small,
  explicitly role-labelled identity/motion/scene subset. An audio reference is
  generative conditioning, not proof that exact audio is passed through.
- This document prices the Runway-hosted Seedance route. Runway self-service
  terms permit input/output training; Enterprise protections require exact
  account proof. Direct BytePlus is a different provider/model/region/rate-card
  contract and cannot be substituted under the same name or estimate.
- Google Flow Characters currently accept only one or two appearance images
  plus a selected or custom Flow voice. Current models generate 4/6/8/10-second
  clips depending on model and operation. Flow can add short full-frame
  presenter cutaways, establishing shots, transitions, and B-roll, but its
  generated voice/audio is not the accepted T05 WAV.
- Enable Flow's silent-output setting where possible. Generated sound from
  either route is discarded. For a visibly speaking presenter shot, a separate
  exact-audio lip-sync step must itself pass; otherwise use the shot only where
  the presenter is not visibly forming the narrated words.
- Flow may switch a request to a compatible model; every job must record the
  requested and realized model/credit delta. Flow outputs carry invisible
  SynthID, and any visible watermark fails professional T06 media. Its access
  and watermark rules require an exact-account residency/subscription check;
  mandatory visible-watermark output is concept-only, never T06 evidence.
- Generated product screens, numbers, citations, diagrams, captions, or UI
  states are never evidence. Real capture and deterministic rendering own
  those surfaces.
- Landscape and portrait are separate shot/edit decisions with independent
  safe-area and human review; a blind crop of one finished edit is not a cell.

Plan B is the stronger authenticity and product-truth architecture, but it is
not silently admissible under the current T06 master contract. That contract
requires the presenter to remain continuously visible. Plan B can satisfy T06
only after a **separately authorized contract amendment** defines a
presenter-dominant editorial composition and updates its exact acceptance
matrix. Until then it is a current fallback/complementary plan, not accepted
T06 evidence.

## Multi-reference character pack (`PresenterReferencePackV1`)

The proposed **Multi-reference character pack** is a versioned source library,
not a bag of every image sent to every model. Its angles and motion lengths are
design hypotheses for later validation, not provider guarantees. More references
help only when they are consistent and the provider accepts their declared role. Conflicting
dresses, glasses, lighting, camera lenses, ages, or expressions can be blended
into an unstable face, body, wardrobe, or skin tone.

| Layer | Recommended content | Purpose and rule |
|---|---|---|
| `IDENTITY_CORE_V1` | Neutral front, approximately 30-degree left, and approximately 30-degree right | For future real capture, use one consistent session. For fictional presenters, create separately governed synthetic derivatives under one look constraint. Same lens, distance, light, hair, attire, jewellery and glasses state; facial identity only |
| `PERFORMANCE_V1` | One 6–10-second chest/waist-up rights-cleared clip with blink, breath, small head turn and one restrained gesture | **motion reference**, not identity or voice authority; still images alone do not teach timing |
| `LOOK_<id>` | A complete, internally consistent pack for one dress, hairstyle, jewellery and glasses state | Keep all look variants separate; never mix look IDs in one request |
| `EXPRESSION_<id>` | Neutral, light smile, or serious stored separately | Select only what the shot needs; laughing/sad/numb extremes are not identity anchors |
| `BLOCKING_<shot>` | Posture, rear view, hand position, depth or choreography reference | Body/wardrobe continuity only; a back view provides no facial identity evidence |
| `SCENE_<id>` | Empty real environment plate for the intended time of day | Lighting/environment only; do not alter the identity core for morning/night |
| `PRODUCT_TRUTH` | Real product capture and source-derived graphics | Factual authority; never generated by a cinematic model |
| `AUDIO_CAPTIONS` | Exact accepted WAV/SRT plus all lineage hashes | Immutable narration authority; never replaced by generated audio |

Each asset needs an exact hash, source/rights record, capture metadata, declared
role, look ID, approval status, and allowed provider/use. Generated outputs do
not recursively become canonical identity inputs without a new human-governed
derivative decision, because that compounds identity drift.
Reference-image inference being zero-priced does not make pack creation free:
generation/capture, curation, rights, provenance, storage, and human acceptance
are separate costs and gates.

Provider-specific selection is mandatory:

- Character-3: choose one front or three-quarter start frame only.
- Seedance 2.5: normally choose the three identity-core stills, one motion
  reference, one scene plate, and only shot-specific supporting references;
  label every role explicitly rather than submitting the full catalog.
- Google Flow Character: choose one front and at most one three-quarter image.
- Future real-person Digital Twin capture: use the provider's separately
  consented guided video process; do not mix it with fictional identity assets.

The current presenter anchors remain immutable. Meera is still
`SOURCE_READY_NO_DERIVATIVE`; generating or accepting additional Meera angles,
looks, expressions, motion clips, or scene-composed derivatives requires a
separate governed derivative route. This document authorizes none.

## Comparable cost consequences

The following dated arithmetic uses published list prices, not account quotes
or spend authority. It excludes tax, failures, retries, minimum purchases,
input/reference-video charges unless stated, storage, editing labor, and local
compute. Every final call needs a fresh price preflight.

### Plan A indicative Character-3 cost

Hedra currently lists USD 0.025/s at 540p, USD 0.05/s at 720p, and USD
0.0625/s at 1080p. For 726.691502 total seconds across all six aspects, the
video-only estimates are **USD 18.17**, **USD 36.33**, and **USD 45.42**
respectively. The 1080p figure is conditional because of the conflicting
account/model admission described above. A ten-second elimination diagnostic is
USD 0.50 at 720p or USD 0.625 at 1080p before any account minimum.
If the existing three-distinct-output bake-off requirement were applied to
complete six-cell sets, the 720p inference estimate would be **USD 109.00**.
Whether repetition applies per candidate, aspect, or final cell must be frozen
before spend; this document does not infer a cheaper interpretation.

### Plan B Seedance and lip-sync scenarios

Runway currently prices Seedance 2.5 at USD 0.30/output-second for 720p.
Reference images and audio are free, but input/reference video is another USD
0.15/second and each generation has an USD 0.80 minimum. The current request
contract uses whole-second request durations, and the stricter current source
says combined reference video and audio duration must stay under 30 seconds.
Sync-3 is approximately
USD 8/minute, or USD 0.133333/second, and is a separate video-to-video pass.
The “combined” column therefore models a Seedance visual plus dedicated Sync-3
for every visibly speaking presenter second; non-speaking visuals do not need
that second pass. The seconds below are summed across six independent edits;
they do not assume that one generated aspect can be blindly reframed as the
other.

| Presenter footage across six edits | Seconds | Seedance 720p visual | Sync-3 speaking pass | Combined |
|---|---:|---:|---:|---:|
| 15 seconds per cell | 90.000000 | USD 27.00 | USD 12.00 | **USD 39.00** |
| 30 seconds per cell | 180.000000 | USD 54.00 | USD 24.00 | **USD 78.00** |
| 25% of final running time | 184 billable / 181.672876 speaking | USD 55.20 | USD 24.22 | **USD 79.42** |
| 50% of final running time | 364 billable / 363.345751 speaking | USD 109.20 | USD 48.45 | **USD 157.65** |
| 100% of final running time | 728 billable / 726.691502 speaking | USD 218.40 | USD 96.89 | **USD 315.29** |

Fractional coverage is rounded up independently for each presenter/aspect cell:
184, 364, and 728 are conservative billable lower bounds before sentence-boundary
segmentation. Sync-3 remains based on exact visibly speaking time; padding or
additional lip-sync shots can increase it.

At 1080p, Seedance alone is USD 0.68/output-second: USD 61.20 for 90
seconds, USD 122.40 for 180 seconds, and USD 495.04 for the 728 rounded
seconds before lip sync. Runway documents 1080p for the current route, but
resolution support does not prove authenticity, exact audio, or T06 acceptance.
Three complete 720p Seedance-only sets would estimate **USD 655.20** before
lip sync, reference-video charges, failures, or editing.

Real product recording, local deterministic graphics, and local composition
have zero marginal provider-generation charge. They still require engineering,
editing, review, storage, and compute, so this table does not call them free.

### Cash-to-start versus marginal inference

Marginal arithmetic is not the amount a new account must pay before the first
job. As verified 2026-09-04:

| Route | Marginal estimate used above | Current cash/access floor | Economic caution |
|---|---:|---:|---|
| Hedra Character-3 | USD 0.05/s at 720p | Basic is USD 15/month with 1,500 monthly credits | Monthly credits do not roll over; the standard API terms still block NarraTwin product integration, so purchasing a plan would not clear the contract stop |
| Runway Seedance 2.5 | USD 0.30/s at 720p | USD 10 minimum credit purchase; credits are priced at USD 0.01 each | A small diagnostic can consume less than USD 10 while still requiring the full minimum purchase; remaining-credit treatment and exact account balance must be checked before activation |
| Google Flow | Credits per generation | Exact qualifying subscription, Workspace entitlement, or exact-account daily-credit access | Official access pages conflict, India-resident output is visibly watermarked, and subscription cost cannot truthfully be allocated to one render without the account facts |
| Local capture/composition | No provider-generation charge | Existing capture/editing hardware and staff time | Not economically free: engineering, recording, editing, review, storage and compute remain real costs |

Neither a subscription, a wallet balance, nor unused credits constitute upload,
egress, spend, provider-selection, or acceptance authority.

### Plan B Google Flow credit scenarios

Flow uses credits per generation rather than a stable USD-per-second price.
As verified 2026-09-04, the credit page says non-subscribers receive **50 daily
credits**, but the get-started page requires a qualifying subscription or
Workspace plan; exact-account access must resolve that official conflict. Plus,
Pro, and the two Ultra tiers receive 200, 1,000, 10,000, or 25,000 monthly credits.
Veo 3.1 Lite costs 10 credits per 4/6/8-second generation for non-Ultra users
(5 for Ultra); **Omni Flash 720p costs 7/10/12/15 credits** for 4/6/8/10
seconds, while 360p costs 4/5/6/7.
Quality costs 100 credits for an 8-second generation. Paid subscribers receive
1080p upscaling at zero additional credits; it is unavailable to non-subscribers.

For six independent cells, 15 seconds per cell needs at least 12 ten-second
Omni generations, or **180 credits**; 30 seconds per cell needs 18, or **270 credits**.
Using eight-second Veo Lite, those same plans need at least 12 generations/120
non-Ultra credits and 24/240. Full six-cell coverage would need at least 92
Veo Lite generations/920 non-Ultra credits because each cell rounds separately;
three full repeated sets would require 2,760 credits. Requests may return more
than one generation and charge
each result; sentence boundaries, rejected shots, alternate aspects, and edits
raise the real total. Subscription prices and unused-credit economics prevent
a truthful universal USD conversion, so Flow must be compared using the exact
account's incremental credit/cash delta at execution.

## Current decision sequence

1. Preserve the rejected HeyGen outputs as negative evidence; do not rerun the
   same single-photo/static-composition root cause.
2. Obtain zero-spend written/capability answers for Character-3 duration by
   resolution, exact accepted WebP, returned-audio behavior, terms/no-training,
   retention/deletion, aspects, idempotency, and failed-job billing.
3. Freeze the multi-reference catalog schema and derivative authority before
   creating any additional presenter asset. Do not make a large pack merely
   because a model permits many references.
4. Prototype Plan B's editorial timing locally with existing rejected footage,
   real product capture, deterministic graphics, exact audio, and captions.
5. If Plan B is the product decision, amend the continuous-presenter contract
   before treating the prototype as T06 evidence.
6. Only after those no-spend gates, authorize one materially different short
   diagnostic on the best-fit route. Select no adapter until exact output and
   human review pass.

This amendment has `NO_AUTHORITY_EFFECT`: it makes no provider selection and
authorizes no account, credential, authentication, upload, egress, spend,
provider call, media generation, adapter/runtime change, release, deployment,
production-readiness, or Cut 1 completion claim.

Official sources verified 2026-09-04:

- Hedra Character-3 model and API:
  <https://www.hedra.com/models/video/hedra/character-3> and
  <https://www.hedra.com/develop/models/video/hedra-character-3>
- Hedra API terms governing integration and content use:
  <https://www.hedra.com/api-terms>
- Hedra current subscription and credit pricing:
  <https://www.hedra.com/pricing>
- Seedance 2.5 capabilities:
  <https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5>
- Runway Seedance pricing and input contract:
  <https://docs.dev.runwayml.com/guides/pricing/> and
  <https://docs.dev.runwayml.com/assets/inputs/>
- Runway account setup and minimum credit purchase:
  <https://docs.dev.runwayml.com/guides/setup/>
- Google Flow Character, asset, and silent-output behavior:
  <https://support.google.com/flow/answer/16935308>
- Google Flow models and credits:
  <https://support.google.com/flow/answer/16352836> and
  <https://support.google.com/flow/answer/16526234>
- Google Flow access, account, and watermark rules:
  <https://support.google.com/flow/answer/16353333>
- Sync-3 pricing and API:
  <https://fal.ai/models/fal-ai/sync-lipsync/v3>
