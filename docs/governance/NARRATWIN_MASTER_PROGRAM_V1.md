# NarraTwin Authoritative Master Program V1

## Document control

- Controller: Issue #424
- Bootstrap branch: `stage8-424-master-program-authority-prelog`
- Accepted base: `afcf0325c3ec925b68b770eda0bb8c839bcce4dd`
- State in this PR: proposed repository authority; no implementation route active
- Release posture: No-Go

This controller governs Cut 1 grounded narration, Meera audio, photorealistic
real-media delivery, provider-neutral architecture, product AI and RAG,
observability and cost controls, controlled feedback and learning, living
architecture, and scoped workspace/Docker/Git/data hygiene. It defines
authority, sequencing, dependencies, boundaries, and completion claims. It is
not an implementation specification.

No implementation PR may cite this controller alone. Every implementation
requires an approved phase specification with complete contracts, schemas,
state transitions, thresholds, failure handling, migrations, security, tests,
evidence, ownership, and rollback; one bounded child issue; an active
`ActiveProgramRouteV1`; a dedicated branch and reviewed PR; and merged-main
predecessor evidence.

Cut 1 completion is separate from full plug-and-play completion. Cut 1 never
implies tenant BYOK, arbitrary-provider or arbitrary-project certification,
all fifteen roles active at runtime, controlled-learning automation, hosted
operation, production durability/readiness, public availability, or release.

## 1. Purpose, claims, and execution authority

The master controller owns program authority, scope, phase order, completion
claims, and blocking versus nonblocking work. A phase specification owns
field-level execution semantics. A child task card owns one bounded outcome.

Issue comments are source authority. Reviewed and merged canonical repository
files are execution authority. Historical evidence remains preserved but may
be marked `SUPERSEDED` only with its replacement route and authority hash.

Implementation is forbidden when its governing phase specification, child
issue, active route, predecessor evidence, review, or branch/PR binding is
missing, stale, expired, revoked, or inconsistent.

## 2. Capability and evidence classification

Every named capability records all of these dimensions independently:

- Implementation: `NOT_STARTED`, `PARTIAL`, or `IMPLEMENTED`.
- Verification: `UNVERIFIED`, `VERIFIED`, `FAILED`, or `EXPIRED`.
- Authority: `ACTIVE`, `SUPERSEDED`, or `REVOKED`.
- Availability: `DISABLED`, `LOCAL_ONLY`, `CONTROLLED`, or `PRODUCTION`.

Every evidence record includes repository, environment, commit, branch,
provider mode, activation-profile hash, command/test, artifact/checksum,
reviewer, observed time, expiry/revalidation trigger, and limitations.
Local/mock evidence cannot be represented as external-provider or production
evidence.

## 3. Stale-plan and route enforcement

Maintain exactly one repository-authoritative `ActiveProgramRouteV1` with:

- route ID and version;
- controller issue;
- active phase and child issue;
- branch and PR;
- exact base SHA and required predecessor merge SHA;
- governing authority-manifest and phase-specification hashes;
- allowed paths, file budget, and charged-line budget;
- predecessor evidence and required tests/reviewers;
- activation/expiry timestamps and superseded-route references.

CI must fail when more than one route is active; a PR cites a superseded route;
issue, branch, PR, base SHA, authority hash, or specification hash differs;
merged-main predecessor evidence is absent; a required document/test/ADR/
status/traceability mapping is absent; implementation starts from issue prose
or this controller without a phase specification; or stale tests and
placeholder contracts are presented as current acceptance authority.

Dependent children advance only through:

```text
MERGED
→ MERGED_MAIN_CHECKS_PASSED
→ STATUS_RECONCILED
→ ISSUE_CLOSED_OR_EXPLICITLY_RETAINED
→ NEXT_ROUTE_ACTIVATED
```

No dependent child starts sooner.

## 4. Cut1AuthorityManifestV1

Before new audio or renderer provider work, merge one authority-reconciliation
route that defines:

- canonical route ID, effective time, exact OWNER authority source, author
  association, retrieval time, source bytes, and source hash;
- every superseded issue body, comment, document section, test, guardrail, and
  route;
- selected presenter Meera only, with Myra and Raj explicitly deferred;
- canonical narration identity;
- Google TTS model, voice, endpoint policy, credential source, retry policy,
  and spending authority;
- external-renderer research and audition authority;
- US$100 total audition ceiling, plus a separate winner-specific final-render
  quote and OWNER approval;
- two independent final renders, disclosure policy, downstream issue order,
  forbidden actions, expiry, and revalidation triggers.

It must explicitly reconcile Issues #366, #368, #369, #370, #371, #421,
PR #422, and all affected status, stage, architecture, API, traceability,
ADR, test, and guardrail records.

## 5. Planning and delivery layers

### Master controller

Defines program authority, scope/exclusions, order, completion claims, and
blocking versus nonblocking work.

### Phase specification

Every phase specification defines required/optional fields, enums, validation,
serialization, public errors, compatibility/versioning, valid/invalid examples,
owning modules, transitions and guards, atomic writes, replay/idempotency,
timeouts/retries/cancellation, terminal states, recovery ownership,
compensation, security/redaction, migrations/rollback, automated and human
acceptance, focused and aggregate commands, evidence locations, and prohibited
success substitutes.

### Child task card

Every child issue names one phase specification, one bounded outcome,
dependencies, expected paths, file/line budget, RED evidence, implementation
and acceptance commands, rollback, stop conditions, reviewers, and closeout.

## 6. Roles and separation of duties

- Repository OWNER controls requirements, supersession, budgets, renderer
  selection, final-media acceptance, and completion authority.
- Implementers produce implementation and evidence and cannot self-approve.
- Eligible non-author reviewers review the exact head.
- Security/privacy reviewers own credential, egress, use, retention, deletion,
  and privacy decisions.
- Provider-terms reviewers qualify the exact entity/product/API/model/endpoint.
- Budget approvers authorize reservations and paid operations.
- Two blinded media reviewers score auditions independently.
- The OWNER media reviewer selects or rejects the winner and accepts final
  artifacts.
- Release/operations reviewers own rollback, monitoring, publication, and
  closeout.
- The merger acts only after every required approval and gate passes.

Every phase specification states who may trigger each transition and who is
prohibited from approving it.

## 7. Intended-versus-implemented baseline

Before new platform implementation, create a matrix for every named
capability using `REUSE_AS_IS`, `MODIFY_FOR_CUT1`, `NEW_CUT1_BLOCKER`,
`POST_CUT1`, or `SUPERSEDED`.

Every row maps:

```text
requirement → current implementation → evidence → gap → classification
→ phase specification → owning issue → tests → human review
→ completion authority
```

Only these platform changes block Cut 1: authority/stale-route enforcement;
post-PR-422 narration authority; a typed Cut 1 composition root;
server-controlled TTS/renderer activation; provider governance; selected
credential resolution; paid-operation safety; artifact quarantine/storage;
end-to-end lineage; renderer adapter; media validation; provider-neutral Cut 1
observability; genuine UI playback/download; and mechanically separate
real-media acceptance.

Tenant BYOK, more adapters, complete controlled learning, complete fifteen-role
runtime, broader languages/live Q&A, arbitrary-project certification, ADR
renumbering, hosted dashboards/SLO proof, production durability/restore, and
public/production release remain post-Cut-1.

## 8. Architecture and living documentation

Evaluate the `architecture-and-decisions` engineering skill in a separate,
nonblocking trust-review issue/PR. Pin source commit
`a94cd5b179bc6dd314887cb1d8f583d149ca60cb` and package SHA-256
`64d66b0c9e43ca4a90ea40c1819698989832dc5eb3bb532c970631e216b52d8f`.
Review license/attribution, filesystem/network/telemetry/credentials/hooks,
packaging, installation, rollback, and restart evidence. It must never become
a NarraTwin runtime dependency and does not block Cut 1.

Keep `docs/ARCHITECTURE.md` as the index. Add nonduplicating Mermaid-as-code
views for C4 context/containers, requirement-to-artifact flow, product AI,
tenant/trust boundaries, provider selection, TTS/renderer execution, artifact
lifecycle, observability, feedback/learning, failure modes, and rollback/
recovery.

Maintain an ADR registry. Duplicate legacy numbers receive unique aliases or
replacement IDs, lifecycle state, and supersession links. Renumbering is
nonblocking unless separately authorized.

Introduce `CapabilityStatusV1` and `DocumentationMapV1`. The documentation map
binds implementation areas to README, architecture, API, portability,
observability, runbook, ADR, status, traceability, security/privacy, and
third-party notices. Deterministically validate README current state from
capability records.

README/status must state existing Stage 4–7 local/mock behavior, durability
limits, real-provider state, PR #422 state, historical HTML/JSON placeholders,
and that placeholders never satisfy Cut 1. CI validates schemas, links,
Mermaid, ADR lifecycle, generated sections, capability evidence, stale routes,
document-impact mappings, and mutations; human semantic review remains
mandatory.

## 9. Project requirements intake

`ProjectExecutionRequirementsV1` records tenant/project, data classification,
permitted processing/storage regions, languages, audience/depth/style,
modalities, quality/latency objectives, budget/quota, retention/deletion,
provider allow/deny policy, operator-key or tenant-BYOK source, web permission,
identity/consent, and disclosure/publication requirements.

Unsatisfied requirements return an explicit capability failure. They never
trigger silent fallback.

## 10. Composition and provider resolution

Implement one typed application composition root and installed-adapter
registry. Resolution precedence is:

1. version-controlled security/legal invariants;
2. installed adapters and operator allowlist;
3. current provider-governance approval;
4. tenant entitlement and credential source;
5. project data/residency/quality/budget policy;
6. workflow activation profile;
7. user preference among already-permitted options.

User input cannot activate an unapproved provider, credential, region, egress
class, fallback, or spend level. Named-provider failure never silently routes
elsewhere. Fallback requires explicit activation-profile equivalence for data
posture, credential source, residency, rights, capability, quality, and budget.
Persist the resolved activation-profile hash on every run and job.

## 11. Provider-neutral contracts

Keep separate versioned contracts for LLM, embedding, vector storage,
retrieval/reranking, speech synthesis, presenter rendering, artifact storage,
observability export, and workflow/agent execution. Each combines its domain
capabilities with initialization/health, timeout/cancellation, request and
response limits, schema validation, structured errors, idempotency, ambiguous
acceptance, retry, rate limits, backpressure, circuit breaking, billing
evidence, region, retention, training/data use, deletion, polling/webhooks, and
adapter/configuration versions. Core domain logic contains no provider-name
branching.

## 12. Credentials and BYOK

Define opaque `SecretRefV1`. Raw keys are prohibited from APIs, activation
profiles, run lineage, application databases, logs, traces, exports, and
generated evidence.

`SecretRefV1` records owner (tenant/operator), provider scope, secret-store
reference, allowed profiles, rotation/revocation/deletion/expiry, access audit,
and custody region/policy. Local tests use a deterministic fake store. A later
hosted AWS implementation uses Secrets Manager and KMS behind `SecretStore`.
Tenant BYOK and operator credentials remain separate: no cross-tenant,
tenant-to-operator, revoked-secret, or long-lived in-memory fallback.

Only the selected adapter resolves its credential immediately before
authorized egress. A disabled adapter performs zero provider-module import,
environment/secret/ADC/metadata lookup, DNS/socket/HTTP, background work,
exporter flush, or provider telemetry.

## 13. Provider governance

`ProviderGovernanceProfileV1` binds exact legal entity, product, API,
model/revision, endpoint, region, terms/DPA and verification time, input/output
and commercial rights, training/data use/opt-out, retention/logging, deletion
SLA/mechanism, subprocessors/transfers, processing/storage regions, security/
incident posture, identity/provenance classes, expiry, and revalidation
triggers.

Unknown, expired, or conflicting governance blocks activation. Endpoint
geography alone does not prove processing or storage residency. Revalidate
immediately before each audition and each independent full render. Final
acceptance requires provider deletion evidence or explicit OWNER-approved
retained-state policy.

## 14. Provider switching and migration

Provider-class changes follow:

```text
PREPARE → VALIDATE → SHADOW → CANARY → PROMOTE → DRAIN → RETIRE
```

Jobs remain pinned to their original activation profile and never silently
change provider/model/endpoint/credential/policy. Embedding or chunking changes
create a new index generation, controlled backfill/validation, atomic alias
switch, and rollback-compatible previous generation. Media jobs reconcile
remote state before retry. Record model revision/fingerprint; unknown revision
or canary drift marks the profile `UNVERIFIED`, and material media-model drift
requires re-audition.

## 15. Product AI workflow

A deterministic state machine owns orchestration. The fifteen canonical
responsibilities are:

1. authorization intake;
2. project fetcher/retriever;
3. optional governed web researcher;
4. semantic-plan generator;
5. grounding/citation evaluator;
6. adversarial reviewer;
7. fact/freshness evaluator;
8. audience/depth/style realizer;
9. localizer/translator;
10. language evaluator;
11. bounded repair synthesizer;
12. deterministic final gate;
13. media adapters;
14. provenance store;
15. telemetry emitter.

`AgentRoleSpecV1` defines typed I/O, trust class, evidence, prompt/policy
hashes, model capability profile, tools/egress, tenant/project boundary,
token/time/cost/retry/repair budgets, idempotency/resume, failure/refusal,
human gates, and telemetry.

A role cannot approve itself; change its own model/prompt/evaluator/tools/
credentials; mutate canonical knowledge; make a dataset authoritative; deploy;
or accept legal/privacy/security/spending risk. Cut 1 implements only retrieval,
planning, grounding, freshness, adversarial review, bounded repair, final gate,
provenance, telemetry, and media. Other roles remain designed.

## 16. RAG and knowledge portability

Version parser, chunking, embedding, indexing, retrieval, reranking,
freshness, and evaluation. Persist project/corpus snapshot, parser/chunker,
document/chunk hashes, query/filters/scores, index generation, embedding/
retrieval models, claim-evidence bindings, and evaluator versions.

Provider memory is never canonical evidence. User-reported project errors
create `KnowledgeCorrectionProposalV1`; only an authorized project owner can
approve a replacement snapshot. Web evidence is separately classified and
cannot overwrite project facts. Stale, conflicting, missing, below-threshold,
or cross-project evidence clarifies or refuses.

Before claiming project plug-and-play, pass an unseen non-NarraTwin project
without project-specific code, prompts, fixtures, or branching.

## 17. Run lineage

Immutable `RunManifestV1` binds requirements and activation profiles,
provider-governance profile, credential reference ID only, project/corpus
snapshot, parser/chunker/index/embedding/retrieval, workflow/roles/prompts/
tools/models/revisions, evaluations/safety policies, costs, consent,
retention, artifacts, feedback, and terminal state. Deletion and revocation
propagate through lineage with tombstones and explicit invalidation.

## 18. Observability and NFR controls

Domain code emits OpenTelemetry-compatible signals only. Langfuse is an
optional exporter created exclusively by the composition root. Exporter policy
defines fields, redaction, sampling, queue/backpressure/drop/outage behavior,
health/drop metrics, flush, region, and retention. Security, audit, billing,
consent, and deletion evidence uses durable records, never best-effort
telemetry.

Separate online operational proxies, offline independently labelled
evaluations, and sampled human judgment. Cover request rate, p50/p95/p99 HTTP
latency, 4xx/5xx, readiness/saturation/process metrics, workflow/node latency,
retrieval miss/empty retrieval, citation/freshness/refusal/cross-project,
labelled recall/precision/hallucination/false pass/refusal/abstention/evaluator
disagreement, provider latency/error/retry/rate limits/drift/deletion, TTS/
render sync/identity/media review, and reservation/estimate/charge/quota/
reconciliation/daily spend.

Prometheus/OpenTelemetry labels use bounded enums. Tenant/project/run/user/
request/artifact IDs remain in access-controlled logs, traces, analytics, or
cost ledgers.

`ControlCatalogV1` records owner, signal/formula/numerator/denominator,
population, objective/window/exclusions, missing-data policy, evaluator/
dataset version, sample/uncertainty, label budget, dashboard/query, alert/
burn window, runbook, capability state, and evidence.

## 19. Controlled feedback and learning

Keep four separated data lanes:

1. content-free operational telemetry;
2. tenant-private support/quality feedback;
3. explicitly opted-in, rights-cleared, redacted improvement candidates;
4. sealed benchmark/holdout data.

Default use is `OPERATIONS_ONLY`. Global improvement, cross-tenant use, or
fine-tuning requires separate consent and rights approval.

Define `FeedbackEventV1`, `HumanLabelV1`, `FailureCaseV1`,
`DatasetCandidateV1`, `DatasetManifestV1`, `CandidateProfileV1`,
`PromotionDecisionV1`, and `KnowledgeCorrectionProposalV1`.

Feedback follows:

```text
CAPTURED → QUARANTINED → TRIAGED → REPRODUCED
→ INDEPENDENTLY_LABELED → ADJUDICATED → CANDIDATE_CASE
→ APPROVED_DATASET
```

Controls include lineage, consent/purpose/use, classification, retention/
deletion, checksums, screening for prompt injection and accidental credential
exposure, duplicate/sybil detection, conflicts/appeals, reviewer independence,
transitive deletion, and tenant isolation.

Maintain development, regression, temporal holdout, unseen-project holdout,
adversarial, language, and provider-conformance splits. Protected holdouts stay
sealed from prompt authors and improvement agents; diagnosis/tuning cases leave
the holdout. Calibrate each evaluator against independent human labels. High
risk uses two blind reviewers plus adjudication. Record confusion matrix,
precision/recall, false-pass/refusal, abstention, coverage, uncertainty, and
per-slice results. LLM judges are advisory when calibration is inadequate.
Absence of complaints is not correctness; use stratified random human audits.

The offline `ImprovementOrchestrator` may cluster feedback, propose causes,
reproduce failures, draft regression tests, compare baseline/candidate, and
recommend changes. It cannot change production prompts/models/retrieval/
thresholds/tools/providers/policies, edit knowledge, promote datasets, deploy,
mutate Git, or bypass approval.

Promotion follows:

```text
APPROVED_DATASET → OFFLINE_COMPARISON
→ SECURITY/PRIVACY/BIAS/QUALITY/LATENCY/COST_REVIEW
→ APPROVED_SHADOW → APPROVED_CANARY
→ PROMOTION_OR_ROLLBACK → POST_CHANGE_MONITORING
```

The complete `ActivationProfileV1` is the atomic promotion/rollback unit.

## 20. Serialized Cut 1 route

The mandatory route is:

1. revalidate PR #422 exact head and merge eligibility;
2. merge only that head;
3. run merged-main checks;
4. close Issue #421 explicitly;
5. merge authority reconciliation and stale-route enforcement;
6. approve the intended-versus-implemented matrix;
7. approve the minimum Cut 1 foundation specification;
8. create a fresh grounded Meera Stage 4 run;
9. persist snapshot, claims, classifications, evaluator versions, and hashes;
10. create a fresh narration version;
11. evaluate narration;
12. obtain exact-hash speech approval;
13. issue one single-use TTS receipt;
14. revalidate current authority before egress;
15. consume the receipt atomically;
16. generate the canonical WAV;
17. technically validate it;
18. obtain exact-hash OWNER listening acceptance;
19. freeze the sample-addressed 15-second audition excerpt;
20. freeze media calibration before candidate output is viewed;
21. lock Meera presenter/background authority;
22. prequalify providers;
23. approve candidates and audition reservations;
24. run auditions;
25. technically validate auditions;
26. complete blinded reviews;
27. obtain OWNER winner selection or reject all;
28. obtain winner-specific final-render quote;
29. obtain separate OWNER final-render budget approval;
30. implement/activate winner adapter;
31. independently render 1920×1080;
32. independently render 1080×1920;
33. quarantine and technically validate both;
34. compose deterministic audio/captions;
35. obtain human acceptance for both outputs and captions;
36. integrate genuine playback/download/replay;
37. run non-intercepted browser acceptance;
38. emit `CUT1_REAL_MEDIA_ACCEPTED`;
39. complete Cut 1 PR/issue closeout;
40. continue post-Cut-1 work separately.

No step starts without predecessor merged-main or immutable paid-operation
evidence, as applicable.

## 21. Canonical Meera narration and audio

Canonical narration is Meera, eight paragraphs, 261 words, 1,904 UTF-8 bytes,
no trailing newline, SHA-256
`3edffc6169460546ae0bdee867fdeaf3c0ae383535e2976e0333f39c03ff614e`.
Bind repository path, Git blob, source snapshot, grounding evaluation,
narration version, speech approval, and single-use receipt. A narration copy
cannot be its own evidence.

The governed TTS profile is Google Gemini TTS, `gemini-2.5-pro-tts`, voice
`Despina`, language `en-IN`, approved EU endpoint policy, mono PCM16 LINEAR16
WAV at 24 kHz. Revalidate endpoint/model/region/retention/terms immediately
before egress.

Audio validation requires RIFF/WAVE magic and valid decoding; mono PCM16 at
24 kHz; decoded duration 90.000–120.000 seconds; all eight paragraphs and
correct final words; exact provider-request binding; transcript/forced
alignment; approved pronunciation transform; clipping/DC/peak/RMS and
leading/trailing/internal silence analysis; no spoken citations or time
stretch; exact WAV/decoded-PCM hashes; and exact-hash OWNER listening approval.

Only one retry is allowed, and only for a predeclared independently evidenced
technical failure. Aesthetic preference, unsuitable delivery, wrong voice or
content, content rejection, possible remote acceptance, and
`BILLABLE_UNKNOWN` are not retryable. The accepted WAV is the sole final-video
audio source.

Record deterministic WAV-to-AAC tool/version/flags/priming compensation.
Demux each MP4 and prove channel, duration, timeline, decoded similarity, no
substitution/regeneration, and no timing-changing normalization.

## 22. Meera asset authority

Define `MeeraAssetAuthorityV1` before upload with the original source path and
SHA-256, exact waist-up derivative path and SHA-256, dimensions, crop/mask/color
transformations, background hashes,
performance-direction hash, synthetic-person classification, provenance,
license/commercial derivative/upload rights, permitted providers, retention/
deletion/revocation, and OWNER visual acceptance.

Reject stock/substitute presenters, unrelated bodies, identity replacement or
identity-changing enhancement, unapproved clothing/jewelry/hair/background,
and face-only/mouth-only crops. Mutation invalidates audition/winner authority.

## 23. Media calibration

Freeze `MediaCalibrationProfileV1` before any audition output is generated or
viewed. It includes corpus/anchor hashes; decoder/probe/tool/model and rubric
versions; resolution/CFR/frame-rate/duration rules; A/V offset; lip-sync and
identity thresholds; frozen/black/duplicate/loop limits; motion inside/outside
the mouth; clipping/silence; caption timing/coverage; file size; decoder-error
policy; severe-artifact taxonomy; and reviewer approval.

Thresholds cannot change after viewing candidate output. A change invalidates
the auditions and requires re-audition.

## 24. Renderer prequalification

Prequalify the exact legal entity, product, API, model/revision, endpoint, and
region. Research candidates may include HeyGen Avatar IV, Mirage Video 1,
Hedra Character-3, qualified Kling Avatar v2 Pro access, and Higgsfield only
with an appropriate production API. Names are research candidates, never
implicit approval.

Evidence must cover custom synthetic image and exact supplied audio support;
no prohibited clone/enrollment; commercial/output rights; likeness processing;
training/opt-out; retention/deletion; subprocessors/transfers; watermark/
disclosure; duration/resolution/aspect/background; API/idempotency/billing;
polling/webhook; and provider deletion. Unknown/expired facts exclude a
provider.

## 25. Audition fixture and scoring

Freeze exact WAV sample start/end, excerpt hash, phoneme/pause/closure
coverage, Meera derivative/background/direction hashes, and output profile.
Each qualified candidate receives one synthesis. Retry requires a predeclared
verified technical failure.

Technical validation precedes scoring and requires genuine container/magic,
audio/video tracks, decodable frames, dimensions/frame rate/duration, temporal
progression, and exact audition-audio binding.

Independent hard floors of at least 4/5 apply to realism, identity, full-face
lip sync, eyes/blinking, head/shoulders/torso/posture/intended hand motion, and
artifact freedom. Zero severe defects are allowed. Reject static/slideshow/
pan-zoom/loop/mouth-only/patch output; frozen eyes/body; substituted identity;
watermark; and facial/body/clothing/hair/jewelry/teeth/tongue/hand/background
defects.

Two blinded reviewers score exact hashes with frozen anchors and notes.
Weighted ranking starts only after every hard floor passes. OWNER selects the
exact winner or rejects all; no least-bad selection.

## 26. Winner lock

Winner selection binds provider entity/product/API/model revision/endpoint/
region, presenter/background/audio hashes, prompt/settings/seed, adapter
version, governance hash, audition hash, rate card, and limits. Full rendering
cannot silently change or fall back from any field. Material drift requires
re-audition.

## 27. PaidOperationV1

States are:

```text
INTENT → RESERVED → DISPATCHED
→ REMOTE_ACCEPTED | BILLABLE_UNKNOWN
→ SUCCEEDED | FAILED_TECHNICAL | REJECTED
→ RECONCILED | REFUNDED
```

Additional terminal states are `CANCELLED` and `SUPERSEDED`. Every transition
defines actor, guard, atomic persistence, idempotency, event, timeout, recovery
owner, compensation, and illegal-transition error.

Each audition and final aspect-ratio render has one logical fingerprint, one
idempotency key, at most one active remote job, provider request/job IDs,
estimate/actual, and rate-card/currency/tax/fee evidence.

`BILLABLE_UNKNOWN` retains reservation; prohibits retry/fallback/reroll/
duplicate create; reconciles via signed webhook, polling, or manual provider
evidence; never treats requested refund as completed; and blocks dispatch when
worst-case exposure exceeds authority.

The US$100 ceiling applies only to auditions. Final renders need a separate
winner-specific worst-case quote and OWNER approval including taxes, fees,
currency conversion, and contingency.

## 28. ArtifactStore and MediaValidator

Define streaming `ArtifactStore` lifecycle:

```text
QUARANTINE → VALIDATE → COMMIT
```

Store provider-independent reference, MIME, size, checksum, duration,
provenance, tenant/project scope, retention, legal hold, deletion, and provider
deletion evidence. Use incremental checksum, byte limits, malware scan,
transactional metadata/outbox, controlled access, and migration copy/
reconciliation. Never store full media as base64 application JSON or a
provider-native canonical object. Provider URL/success payload is not an
artifact.

## 29. Cut1VisualArtifactAcceptanceV1

A valid visual artifact is time-varying raster video from the approved Meera
asset, continuously preserving Meera while naturally animating lips, jaw,
cheeks, eyes/blinks, head, shoulders, torso, posture, and intended hand motion,
synchronized to accepted audio with stable identity/body/clothing/jewelry/
hair/skin/hands/background/lighting.

HTML/CSS/JSON/manifest/metadata/provider status, a still with audio,
slideshow/pan-zoom/loop/mouth-only/patch animation, unrelated performer/stock
body, and fabricated/inaccessible provider output are invalid.

Retain separate hashes for primary provider artifact, deterministic composed
output, and committed delivery artifact. Machine validation covers tracks,
frames, motion, frozen/duplicate/loop/black frames, A/V alignment, identity
sampling, and decoder validity. Automation cannot approve realism or human
naturalness; exact-hash human viewing is mandatory.

## 30. Independent full renders

Create two independent provider jobs:

- 1920×1080 premium-studio hero;
- 1080×1920 professional-office social.

Each must be constant 30 fps H.264 browser-compatible `yuv420p`, AAC-LC,
ISO-BMFF MP4; match accepted-audio duration within one frame after documented
priming compensation; contain no truncation/frozen/black interval/unintended
silence/watermark/logo/text; preserve continuous identity and full-duration
lip sync; pass quarantine/validation; and have a distinct exact hash. One
aspect ratio cannot satisfy both.

## 31. Captions

Create one UTF-8 WebVTT per output, exactly bound to its MP4 timeline and hash.
Cues are monotonic, nonoverlapping, complete for spoken words, contain no
inserted spoken citation or unsafe active markup, keep the final cue inside the
final frame, and obey readable line limits. Each VTT has an exact hash and
human spot-check. Identical timelines must be proved, never assumed.

## 32. Cut1RealMediaAcceptanceV1

Legacy Stage 7 `COMPLETED`, HTML/JSON/manifests/placeholders/fixtures, file
existence, or provider `SUCCEEDED` cannot satisfy Cut 1.

Happy path:

```text
AUTHORIZED
→ AUDIO_GENERATED
→ AUDIO_TECH_VALIDATED
→ AUDIO_HUMAN_ACCEPTED
→ ASSET_APPROVED
→ PROVIDER_PREQUALIFIED
→ AUDITION_TECH_VALIDATED
→ AUDITION_HUMAN_ACCEPTED
→ PROFILE_SELECTED
→ FULL_RENDERS_PROVIDER_SUCCEEDED
→ FULL_RENDERS_QUARANTINED
→ FULL_RENDERS_TECH_VALIDATED
→ FULL_RENDERS_HUMAN_ACCEPTED
→ UI_REPLAY_ACCEPTED
→ CUT1_REAL_MEDIA_ACCEPTED
```

Exceptional states are `REJECTED`, `FAILED_TECHNICAL`, `BILLABLE_UNKNOWN`,
`CANCELLED`, and `SUPERSEDED`. They cannot enter acceptance without a new
authorized operation/profile and legal predecessor evidence.

The aggregate requires exactly one accepted canonical WAV, one distinct
accepted 1920×1080 MP4, one distinct accepted 1080×1920 MP4, one hash-bound
VTT per MP4, technical and human approval for both, browser evidence for both,
winner lock, current governance, provider retention/deletion outcome, and
complete lineage. Multi-output transitions use `allOf`; one output cannot
advance the aggregate.

## 33. Disclosure policy

The access-controlled clean master has no voluntary spoken, burned-in, or
adjacent visible AI-use statement. NarraTwin adds disclosure only when a
reviewed law/country/platform/destination/onboarding/publication-contract rule
requires it.

`DisclosureProfileV1` records governing requirement/source/reviewer,
jurisdiction/destination, effective/expiry dates, metadata/derivative
requirements, and affected artifact hashes. Unresolved disclosure blocks that
publication/download route. The clean master is never silently treated as a
compliant public derivative. Internal provenance remains recorded without
automatic viewer disclosure.

## 34. UI and browser acceptance

Segregate historical placeholders from Cut 1 media. A completed Cut 1 card
appears only after `CUT1_REAL_MEDIA_ACCEPTED` and exposes committed artifact
references, MIME, checksum, size, duration, output profile, captions, and only
permitted playback/download actions.

Non-intercepted browser acceptance proves real backend/artifact store, no route
interception/HAR replay, valid Range/content headers, dimensions/duration,
advancing playback and changing decoded frames, audible audio, seek/pause/
resume, reload/restart replay, captions, checksum-identical download,
authentication/project isolation, and no console/network error or placeholder/
manifest/provider-URL/base64 substitution.

The UI cannot show completion while remote-only, quarantined, failed, unknown,
unvalidated, expired, revoked, or missing either aspect ratio.

## 35. Required negative tests

Reject at minimum:

- legacy Stage 7 `COMPLETED`;
- HTML/JSON/manifest renamed MP4 or fake bytes with correct MIME;
- static, one-frame, slideshow, pan/zoom, loop, mouth-only, or frozen-body
  video;
- wrong presenter/asset/model/profile/background/provider/audio;
- silent, truncated, time-stretched, regenerated, or substituted audio;
- stale narration/approval/receipt/provider terms/winner;
- 89.999- or 120.001-second audio;
- wrong codec/dimensions/aspect/pixel format/frame rate/profile or disallowed
  VFR;
- duration drift;
- missing/stale/overlapping/incomplete/mistimed captions;
- inaccessible/redirected/missing/mutated provider artifact;
- duplicate create/webhook;
- billable unknown followed by retry;
- full render without separate budget approval;
- low motion or severe defects hidden by aggregate scoring;
- thresholds changed after output;
- model drift, segment seam, or identity drift;
- bytes changed after approval;
- missing provider retention/deletion outcome;
- unresolved destination requirement followed by publication;
- intercepted browser success or download checksum mismatch;
- expired artifact, cross-project replay, one accepted aspect only; and
- placeholder fields mapped to real-media acceptance.

## 36. Task resource ledger

Every chat/process/issue/branch/PR/audition/render/verification run records:
repository/worktree/branch/base/head; temporary directories/files/reports;
Compose project; task containers/networks/volumes/images; background processes,
sockets/PIDs/locks; provider jobs/uploads; restricted evidence; accepted
artifacts; retention; and cleanup owner. Names and labels are task-specific.

## 37. Docker, temporary-file, and process hygiene

At every success/failure/cancellation/supersession/handoff, stop/remove only
task-owned temporary containers and networks; remove disposable task-owned
volumes/images only after proving no required evidence depends on them; remove
task temporary/secret files, sockets, PIDs, locks, and background processes;
reconcile/cancel provider jobs where allowed; request provider deletion when
required; retain governed evidence/accepted artifacts only; and confirm no
unnecessary task-owned secret/private/media remains.

Cleanup requires before/after inventory. Never use `docker system prune`, broad
recursive deletion, unresolved variables/globs, repository/home/shared-root
deletion, unrelated/user-owned removal, required-evidence deletion, or
protected-forensic deletion.

Intentionally retained/unremovable resources record exact identifier/location,
reason, owner, sensitivity, retention requirement, next action, and deletion
date. “No residual data” means no unnecessary task-owned residual data; it does
not authorize unrelated cleanup.

## 38. Git, main synchronization, and branch cleanup

Remote `main` is canonical. Before work: fetch; compare local/remote main;
start from clean current `origin/main`; create an issue-linked dedicated
branch, preferably in a dedicated worktree; preserve unrelated dirty work; and
never commit directly to main.

After merge: verify merge SHA and post-merge workflows; fetch; fast-forward
local main; prove local main equals origin/main; prove no required unmerged
task commits; delete merged local/remote branches; remove task worktree; prune
only stale worktree references; and reconcile issue/status/README/capability/
ADR/diagram/traceability state.

Do not delete a branch with required unmerged work, protected evidence,
another owner/task, unproven merge/abandonment, or active-authority conflict.
With a dirty shared workspace, synchronize from an isolated worktree without
stashing/moving/deleting user changes.

## 39. End-of-process closeout verification

Every terminal process records worktree cleanliness excluding documented user
changes; task branch/commit; local/remote main SHAs and equality; merge SHA and
post-merge checks; local/remote branch deletion; worktree removal; absence of
task containers/networks/disposable volumes/images/temp files/background
processes/secrets/private data; accepted evidence access; provider job and
retention/deletion state; issue/PR disposition; and README/status/diagrams/ADR/
traceability reconciliation.

“Everything is clean” without scoped inventory and command results is
insufficient. Incomplete cleanup/synchronization leaves the process `PARTIAL`
or `BLOCKED`.

## 40. Mandatory plain-English handoff

Every terminal chat/process provides concise bullets:

- **Status before:** previous state, gaps, governing issue/PR/commit.
- **Completed:** changes, passing evidence, acceptance, cleanup.
- **Pending:** all blockers, failed/expired checks, retained resources, jobs,
  approvals, limitations, and deferrals.
- **Next action:** one authorized action, owner, prerequisite, and stop
  condition.

Also state current branch/commit; local-main/origin-main equality; task-branch
deletion; Docker/temp cleanup; and intentional retention/reason. Never claim a
fact not verified.

## 41. Completion claims

Emit `Cut1DemoCompleteV1` only while `CUT1_REAL_MEDIA_ACCEPTED` is current and
passing. Provider success, one render, ffprobe, stored artifact, UI link, human
approval alone, PR merge, or legacy Stage 7 completion is insufficient.

Full plug-and-play additionally requires same-build adapter switching; no core
provider branching; tenant BYOK isolation; provider conformance; RAG migration/
rollback; portable artifact/lineage export/import; non-NarraTwin
generalization; controlled-learning promotion/rollback; hosted durability;
observability/SLOs/alerts; successful restore; and release gates. Cut 1 may be
accepted while these remain partial/planned.

## 42. Final pre-log review gate

Before this controller becomes executable repository authority:

1. run a fresh independent execution-specification review;
2. run a fresh Cut 1 false-success/media review;
3. run a platform/security/learning review;
4. resolve every blocker;
5. verify exact bytes and hash;
6. obtain exact-byte OWNER approval;
7. use a dedicated governance issue, branch, and PR;
8. merge canonical authority before implementation.

Reviewers must confirm that the complete prior architecture plan was
preserved; operational closeout was added rather than substituted; legacy
placeholders cannot satisfy real-media acceptance; stale routes cannot
authorize implementation; provider/spend cannot activate implicitly; the Cut
1 route is completely serialized; cleanup cannot delete unrelated data; and
completion/handoff claims remain evidence-bound.

Until all of these gates pass, this document is proposed authority only and no
downstream implementation route is active.
