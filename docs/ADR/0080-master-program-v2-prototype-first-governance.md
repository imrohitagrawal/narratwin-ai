# ADR 0080: Master Program V2 candidate and prototype-first governance

- Status: Proposed in Issue #521; authority effect `NONE`
- Date: 2026-09-07
- Owner: repository owner
- Base: `b6b0c05c7227428ff0841361f3970b0b2c40aa86`

## Context

V1, the five-cut roadmap, newer Cut 1 contracts, real-media evidence, the
dual-video strategy, and the owner's Digital Twin requirement need one audited
program without allowing new prose to weaken or activate old routes. Past
provider-specific implementation before exact account/output proof also created
avoidable cost and false-success risk.

## Decision

Introduce V2 only as a hash-bound candidate with `SupersetMappingV2` and
`CutTaxonomyV2`. Historical enterprise Cut 5 becomes Cut 6 through
`LegacyCut5Enterprise`; new Cut 5 is owner Digital Twin. Legacy evidence cannot
cross those meanings without migration validation.

Every new provider or materially changed media/realtime/storage boundary must
pass PF-0–PF-7 before provider-specific product code. The candidate cannot
supersede V1 or activate a route. Independent review, exact-byte owner approval,
eligible exact-head approval, protected merge, merged-main checks, and a
separate accepted-current transition are mandatory.

## Consequences

G1 changes no API/runtime. G2 owns executable hypothesis/receipt contracts; G3
owns restricted evidence and cost reconciliation. Provider calls, private-data
reads, spend, biometrics, deletion, publication, and release remain prohibited.
The accepted-current transition must atomically activate V2, supersede V1,
complete all seven compatibility-migration surfaces at the transition merge
time, and add V2 to required reading through the protected agent/playbook hash
transition. No intermediate state is valid.

## Rollback

Before merge, close the PR and remove only Issue #521 resources. After merge,
revert through a new issue/branch/PR. Never delete V1 or historical evidence or
implicitly reactivate a stale route.
