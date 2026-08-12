# Issue 424 Cut 1 False-Success and Media Review

## Review identity

- Controller digest: `c356d2d7a2b5d2ad3d84d1e911fdf22b55412346b0c61e3ac39dbeef22c2ae76`
- Review state: `PENDING_INDEPENDENT_REVIEW`
- Required reviewer: fresh-context media/acceptance reviewer who is not author

## Question

Can any placeholder, provider response, static artifact, one-output success,
machine-only check, or stale approval be misrepresented as genuine accepted
Cut 1 media?

## Mandatory checks

| ID | Check | Pass condition | Fail condition | Evidence |
|---|---|---|---|---|
| MEDIA-01 | Canonical audio | Exact accepted WAV is sole final-video source with technical and listening approval | Regenerated/substituted/stretched audio is allowed | Section 21 |
| MEDIA-02 | Presenter authority | Exact Meera derivative/background/direction and rights are locked before upload | Stock body, face crop, identity enhancement, or mutation survives | Section 22 |
| MEDIA-03 | Frozen calibration | Thresholds are fixed before viewing candidate output | Thresholds change to rescue an audition | Section 23 |
| MEDIA-04 | Provider qualification | Exact entity/product/API/model/endpoint/region and current rights/retention/deletion facts are required | Candidate name or endpoint region alone qualifies | Section 24 |
| MEDIA-05 | Hard floors | Every category independently reaches 4/5 with zero severe defect before ranking | Weighted score hides frozen body or severe defect | Section 25 |
| MEDIA-06 | Paid ambiguity | BILLABLE_UNKNOWN blocks retry/fallback/duplicate dispatch | Ambiguous call can reroll | Section 27 |
| MEDIA-07 | Genuine artifact | Time-varying raster video preserves full identity/body motion and sync | HTML/JSON/still/loop/mouth-patch/provider URL passes | Sections 28–29 |
| MEDIA-08 | Two outputs | Independent distinct landscape and portrait jobs both pass | One output or transcode satisfies both | Sections 30 and 32 |
| MEDIA-09 | Captions | One hash/timeline-bound VTT per MP4 passes machine and human checks | Missing/stale/shared-by-assumption VTT passes | Section 31 |
| MEDIA-10 | Aggregate allOf | Every audio, asset, provider, audition, render, retention, lineage, human, and browser gate passes | Provider success, ffprobe, storage, UI link, or human review alone completes | Sections 32 and 41 |
| MEDIA-11 | Browser authenticity | Non-intercepted real backend/store playback/download/replay proves changing frames/audio/captions/isolation/checksum | HAR, interception, manifest, provider URL, or base64 fabricates success | Section 34 |
| MEDIA-12 | Disclosure | Clean master and publication derivative remain distinct; unresolved destination rules block route | Clean master silently becomes public-compliant derivative | Section 33 |

## Required adversarial fixtures

The later phase specification must reject every case in Section 35, including
89.999/120.001-second audio, static/loop/mouth-only video, wrong identity or
audio, codec/profile/duration/caption drift, provider artifact mutation,
duplicate create/webhook, billable-unknown retry, threshold drift, post-approval
byte mutation, one aspect ratio, cross-project replay, and intercepted browser
success.

## Reviewer disposition

- Reviewer: `PENDING`
- Exact commit: `PENDING`
- Decision: `PENDING`
- Blocking findings: `PENDING`
- Residual risks accepted by: `PENDING`

This file is a prompt/checklist and cannot self-certify media acceptance.
