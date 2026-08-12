# Issue 424 Platform, Security, and Learning Review

## Review identity

- Controller digest: `c356d2d7a2b5d2ad3d84d1e911fdf22b55412346b0c61e3ac39dbeef22c2ae76`
- Review state: `PENDING_INDEPENDENT_REVIEW`
- Required reviewers: eligible platform/security/privacy reviewer and, where
  provider facts are assessed, provider-terms reviewer

## Question

Does the controller keep provider choice, credentials, tenant data, spending,
lineage, observability, feedback, promotion, and cleanup explicit and fail
closed without claiming post-Cut-1 capabilities?

## Mandatory checks

| ID | Check | Pass condition | Fail condition | Evidence |
|---|---|---|---|---|
| PLAT-01 | Resolution order | Security/legal/provider/tenant/project/activation constraints precede user preference | User input activates provider/region/fallback/spend | Section 10 |
| PLAT-02 | Provider neutrality | Separate contracts share lifecycle semantics and core has no provider-name branching | Core branches by vendor | Section 11 |
| SEC-01 | Secret custody | Raw keys stay out of APIs/state/logs/evidence; selected adapter resolves opaque ref just-in-time | Cross-tenant/operator fallback or disabled lookup occurs | Section 12 |
| SEC-02 | Governance freshness | Exact provider facts and revalidation gate each dispatch | Unknown/expired facts or endpoint geography suffice | Section 13 |
| PLAT-03 | Migration pinning | Running jobs stay pinned; provider/index changes shadow/canary/promote with rollback | Silent mid-job change or in-place index mutation occurs | Section 14 |
| AI-01 | Role separation | State machine, typed roles, budgets, evidence, and self-approval prohibitions are explicit | Agent mutates policy/knowledge/provider/deployment | Section 15 |
| RAG-01 | Evidence portability | Project snapshots/versioned retrieval/claim bindings remain canonical | Provider memory or web evidence overwrites project facts | Section 16 |
| LINEAGE-01 | Immutable lineage | Requirements through artifacts/feedback/terminal state are bound; deletion/revocation propagates | Credentials or invalidated lineage remain active | Section 17 |
| OBS-01 | Telemetry boundary | Durable audit/billing/consent/deletion is separate from bounded OTel export | Best-effort telemetry becomes audit evidence or leaks high-cardinality IDs | Section 18 |
| LEARN-01 | Data lanes | Operations/private/opt-in/holdout lanes and rights are separated | Default feedback becomes global training data | Section 19 |
| LEARN-02 | Promotion authority | Offline orchestrator only proposes; profile promotion follows independent staged review | Agent changes production or mutates Git | Section 19 |
| OPS-01 | Safe cleanup | Only task-owned resources are removed after inventory and retention checks | Broad prune/delete touches user/shared/evidence resources | Sections 36–39 |
| CLAIM-01 | Honest availability | Cut 1 blockers and post-Cut-1 capabilities are explicit | Designed capability is reported implemented/verified/production | Sections 2 and 7 |

## Explicit non-evidence

- Cached or consulted skills are not repository-approved runtime dependencies.
- A local/mock implementation is not external-provider proof.
- Endpoint geography is not residency proof.
- Absence of complaints is not quality evidence.
- An LLM judge is not authoritative without calibration.
- Provider status, telemetry, or refund request is not durable outcome evidence.

## Reviewer disposition

- Platform reviewer: `PENDING`
- Security/privacy reviewer: `PENDING`
- Provider-terms reviewer: `PENDING_OR_NOT_APPLICABLE_FOR_PRELOG`
- Exact commit: `PENDING`
- Decision: `PENDING`
- Blocking findings: `PENDING`
- Residual risks accepted by: `PENDING`

This file is a review surface, not evidence that any review or provider
qualification occurred.
