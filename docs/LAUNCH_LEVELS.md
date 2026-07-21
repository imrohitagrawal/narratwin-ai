# NarraTwin AI Launch Levels and Infrastructure Boundaries

Status: Merged documentation baseline through PR `#153` at `2fb5569`;
issue `#141` and activation remain blocked on the recorded human approvals.

## Purpose

This document is the canonical boundary between development, demos,
production-like durability validation, soft launch, and production. It prevents
an infrastructure choice for one level from becoming an accidental prerequisite
or readiness claim for another level.

ADR `0027` selects AWS for the production-like durability evidence and eventual
production paths, not for local development or controlled local demos.
An AWS account is not required for local development or the controlled local mock demo.
The AWS selection gives issues `#142` through `#149` a concrete, testable
RDS/S3/KMS/IAM/network contract; it does not make AWS a product runtime
dependency for local use and it does not authorize a restore drill.

## Launch-level boundary

| Level | Audience and data | Permitted infrastructure | AWS requirement under ADR 0027 | Current posture | Claim boundary |
|---|---|---|---|---|---|
| Local development/test | Developers; synthetic or local test data only. | Local Docker PostgreSQL, in-memory state, optional JSON snapshots, and local/mock artifact and provider paths. | No. | Not a launch. | Test evidence only; no availability, shared durability, backup, restore, RTO, or RPO claim. |
| Local mock demo | Controlled presenter-led reviewers; synthetic demo data only; no public endpoint. | The reviewed local Compose/mock stack and optional local restart snapshots. | No. | Conditional Go only through `docs/demo/PHASE_1_DEMO_CHECKLIST.md`. | Product-flow demonstration only; no production-like durability, real-provider, multi-worker, or service-level claim. |
| Hosted internal synthetic demo | Named internal workforce reviewers; synthetic product data only; internal environment access/SSO and minimum employee identity/access audit metadata under documented retention; non-public. | A free or low-cost hosted resource may be considered only after an environment owner documents access control, secret handling, retention, teardown, logging, limits, and incident contact. | No. If the environment is intended to produce production-like evidence, it must move to the production-like validation row and satisfy issues `#142` through `#149`. | No-Go until an environment-specific review records those controls and the applicable product gates pass. | Convenience hosting only; it is not production-like durability evidence and cannot inherit local-demo approval. |
| External/invite-only soft launch | Any external identity or user, customer/content personal data, customer-facing application authentication, public or customer-reachable endpoint, or reliability promise. | Reviewed hosted tenancy with durable data/artifact storage, backup, access control, secrets, monitoring, retention/deletion, incident response, rollback, and named owners. | AWS is the current durability baseline; a different provider requires a reviewed ADR amendment and re-baselined evidence before durability or launch claims. | No-Go. | External users or customer data make this production-adjacent regardless of the words `demo`, `beta`, or `soft launch`. |
| Production-like durability validation | Authorized reviewers; synthetic seed only; no application, customer, or public traffic. | The ADR `0027` non-production RDS/S3/KMS/private-network source and isolated restore-validation landing zone. | Yes, for the current selected baseline. | No-Go until issues `#142` through `#149`, named human approvals, and live environment evidence pass; actual restore results remain with later issue `#126`. | Validates production-shaped durability controls only; it is neither a demo launch nor production authorization. |
| Production | External users and approved production data/traffic. | Separate production tenancy/account with reviewed application, durability, security, privacy, operations, monitoring, rollback, and support controls. | Yes, a separate production AWS account under the current baseline; an alternative requires a superseding ADR and equivalent evidence. | No-Go. | Requires an independent production Go decision; production-like evidence does not automatically authorize production. |

The highest-risk applicable row governs. Moving an activity to a smaller audience
does not make it local when it still uses external identities, customer/content
personal data, customer-facing application authentication, a public or
customer-reachable endpoint, or a service-level promise. Internal workforce
authentication and minimum identity/access audit metadata do not alone promote
an otherwise qualifying hosted internal synthetic demo to soft launch.

## Free and low-cost resource rule

A free or low-cost resource does not, by price alone, prove security, durability,
privacy, or operational readiness. It may be used for local work or a separately
approved hosted internal synthetic demo when its actual controls match that row.
Even a zero-cost hosted tenancy needs a named owner, access boundary, secret
handling, data classification, retention/teardown plan, usage limit, and incident
contact.

A candidate service cannot satisfy the production-like row merely because it
offers PostgreSQL. The reviewed evidence boundary also includes versioned artifact
storage, immutable recovery selection, backup/PITR, encryption and key custody,
private networking, federated access, an isolated restore target, audit evidence,
cleanup, and measurable RTO/RPO. If a non-AWS option is preferred, issue `#141`
must remain open while a reviewed ADR amendment maps every issue `#142` through
`#149` acceptance criterion to that option. After issue `#141` is accepted or
closed, any provider change requires a new tracked issue and a superseding ADR.
Cost reduction is a valid reason to reconsider the platform; it is not an
evidence waiver.

## Decision and escalation rules

- Local development and the controlled local mock demo must not wait for AWS
  payer, account, region, budget, or cloud-owner decisions.
- Demo Checkpoint 1 PR 2 may define access, quota, retention, cache, and
  launch-level minimum requirements before a hosted URL exists, but it does not
  create a launch approval, hosted environment, provider egress approval,
  provider account, dashboard configuration, paid plan, wallet funding, model or
  voice selection, or paid-spend authorization. Any later hosted URL must be
  classified by the highest-risk applicable row in this table before it is made
  reachable.
- Issue `#144` is the first infrastructure-provisioning gate for the current
  production-like AWS path. No AWS spend or resource creation is authorized by
  issue `#141` or PR `#153`.
- A hosted internal demo needs its own dated environment decision. Approval of
  the local mock demo does not transfer to it.
- Real provider credentials do not alone change the audience tier, but they
  require separate provider-specific security, privacy, egress, cost, secret,
  evaluation, and license approval; local/mock provider approval does not
  transfer to them.
- A soft launch is production-adjacent. Invitation-only access, a small user
  count, or a free hosting plan does not downgrade it to a demo.
- Production-like validation uses synthetic data and no product traffic. Its
  purpose is to prove durability and recovery controls, not market availability.
- Production requires a separate Go/No-Go decision after all applicable product,
  security, privacy, operations, durability, observability, and rollback gates.

## Current decision summary

- Local mock demo: conditional Go under the existing checklist.
- Hosted internal synthetic demo: No-Go until environment-specific controls are
  reviewed.
- External/invite-only soft launch: No-Go.
- Production-like durability validation: No-Go; AWS is selected but not
  provisioned or approved.
- Production: No-Go.

Issue `#126`, matrix row `DUR-RESTORE-001`, and issue `#39` remain open. This
document creates no account, resource, backup, target, restore evidence, or
launch authorization.

## Related decisions and evidence

- `docs/ADR/0027-production-like-durability-platform-ownership.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/demo/PHASE_1_DEMO_CHECKLIST.md`
- `docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
