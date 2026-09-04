# ADR 0079: Preserve two Cut 1 video strategy alternatives

- Status: Accepted for Issue #516 research sequencing
- Date: 2026-09-04
- Decision owner: Issue #516 freezes `5541564267` and `5542161744`
- Authority effect: `NO_AUTHORITY_EFFECT`
- Implementation authority: none

## Context

T05 has exact accepted Meera, Myra, and Raj narration audio and captions. T06
still has no accepted video cell. The three-provider short comparison and later
HeyGen v8/v9 tests proved that structurally valid media can remain visibly
synthetic: the presenter can look pasted over a background, face motion can be
decoupled from an inert body, and a human reviewer can reject the result even
when transport and media probes pass.

The product owner asked to preserve two current ideas instead of losing them in
chat: a full presenter-led Hedra Character-3 route and an editorial route using
short high-quality generated shots plus real product capture and deterministic
graphics. The owner also asked whether a multi-reference visual library and
Google Flow can improve authenticity.

The current T06 contract still requires six full-duration presenter/aspect
cells with continuous presenter visibility. Research naming is not provider
selection, and no adapter has demonstrated the exact accepted inputs.

## Decision

Preserve both strategies in the dated provider landscape and keep the core
architecture **provider-neutral**:

### Plan A

Treat Hedra Character-3 as a
`PREQUALIFICATION_CANDIDATE_CONTRACT_BLOCKED` presenter-led route. It is first
in the documented comparison because its current model page claims a single
audio-driven job can span each narration and required aspect. It is not selected
or activated. Current terms/privacy, mutable duration/resolution admission, and
the standard API-terms prohibition on product integration must clear before any
upload or spend. One start frame is not a
multi-image identity model, and human realism remains unproved.

### Plan B

Treat Seedance 2.5 and Google Flow as
`VISUAL_BROLL_RESEARCH_NON_ADMISSIBLE_FOR_T06` components of an editorial
hybrid. Short accepted presenter or environmental shots may later be combined
with real product screen recording, deterministic source-driven graphics, the
exact accepted audio, and exact captions. Generated audio and factual product
states are never authoritative.

Plan B may be the stronger product-authenticity direction, but the **current T06
contract remains unchanged**. It cannot satisfy T06 unless a separately
authorized contract amendment defines presenter-dominant editorial acceptance
and updates every affected invariant, test, and human-review surface.
In plain terms, the current T06 contract remains unchanged by this ADR.

### Presenter references

Define the proposed visual library as `PresenterReferencePackV1`, distinct from
the grounded project-avatar-pack. It is a versioned catalog of identity core,
motion reference, look variants, expressions, blocking, scene, product-truth,
and audio/caption assets. Every provider receives only the smallest consistent
subset it officially accepts. A multi-reference library creates no new
derivative, upload, provider, or acceptance authority.

### Adapter boundary

NarraTwin retains retrieval, grounding, evaluation, narration, exact audio,
captions, product truth, provenance, configuration policy, and acceptance.
A selected `AvatarProvider` will own only its provider-native render job; a
future `BrollProvider` can supply non-authoritative visuals; a provider-neutral
`VideoCompositor` will own deterministic audio/caption muxing, real product
capture, layout, and aspect packaging. First-time provider support still needs
a thin adapter, capability manifest, contract tests, privacy/terms review, and
an issue/PR.

## Consequences

- The stale “optimized HeyGen next” instruction is superseded; unchanged
  single-photo Avatar IV/static-composition work must not be repeated.
- Plan A is the only documented alternative that could fit the current
  continuous-presenter shape without first amending the contract, but it remains
  contract-blocked and unproved.
- Plan B can be prototyped locally to evaluate editorial authenticity, but it
  cannot hide or average away failed presenter intervals and cannot be called a
  T06 cell under current rules.
- Multiple angles, postures, dresses, day/night looks, front/back views,
  glasses states, and expressions are separated by role and look ID. They are
  not indiscriminately co-fed or promoted from generated output.
- Provider choice, shot coverage, duration, aspect, resolution, attempts, and
  spend remain validated manifest/configuration values. Consent, egress,
  duplicate-spend, exact-hash lineage, factual-visual, disclosure, deletion,
  media-structure, and human-acceptance invariants remain fail closed.
- Costs are compared using current list-price formulas and exact account deltas
  at execution; estimates grant no spend authority.

## Alternatives rejected

- Continue tuning the unchanged HeyGen Photo Avatar IV route: rejected because
  the exact v8/v9 human evidence demonstrated the same authenticity root cause.
- Submit every reference to every model: rejected because provider contracts
  differ and conflicting identity/look inputs can contaminate output.
- Treat cinematic generated UI/audio as evidence: rejected because product
  truth, narration, and captions must remain source-bound and exact.
- Implement an adapter before a materially different diagnostic passes:
  rejected because it repeats the expensive code-before-compatibility failure.

## Remaining decisions

An owner-approved future route must choose whether to retain continuous
presenter T06 acceptance or amend it to presenter-dominant editorial media. It
must then clear the selected provider's exact model, account, privacy, terms,
duration, aspect, input, output-audio, lifecycle, retry, billing, and human
quality gates before implementation.

This ADR makes **no provider selection**, provider activation, account or
credential use, upload, egress, spend, media generation, adapter/runtime
change, deployment, release, production-readiness, or Cut 1 completion claim.
