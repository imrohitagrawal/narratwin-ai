# Enterprise Readiness Register

Status: proposed canonical index; no row implies implementation or production
approval. Proposed authority: Issue #440, pending review and merge. Detailed ADRs, runbooks,
threat models, and release reports remain the evidence sources linked below.

## Status model

`Specified` -> `Designed` -> `Implementing` -> `Validated`.
Non-progress states are `Deferred`, `Blocked`, `Accepted risk`, and
`Superseded`. A capability is commercial/public-ready only after its evidence,
owner approval, and release gate pass.

## Register

| ID | Domain | Capability | Phase | Status | Owner | Evidence / canonical source | Release impact |
|---|---|---|---|---|---|---|---|
| ER-001 | Product | Cut 1 presenter contract and Meera/Raj/Myra order | Cut 1 | Specified | Product owner | `docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` | Demo |
| ER-002 | Product | Eye contact, framing, face, lip sync, head, torso, hand/body, hair, and identity acceptance | Cut 1 / Stage 7 | Specified | Product/Media owner | Evidence to create: timed eye-contact review, media checklist, and render report | Demo |
| ER-003 | AI | Grounding, citation binding, abstention, hallucination controls | Stage 2/5 | Specified | AI quality owner | `docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md`; `docs/AI_SAFETY_AND_EVALUATION.md` | All |
| ER-004 | AI | Golden suites and deterministic regression gates | Stage 5 | Specified | AI quality owner | Evidence to create: versioned golden suite and regression report | Internal/commercial |
| ER-005 | AI | Ragas metrics and dependency/license decision | Stage 5 | Specified | AI quality/security owner | Evidence to create: dependency/license decision and evaluator report; current use is not active by default | Internal/commercial |
| ER-006 | AI | DeepEval/custom evaluators and LLM-judge calibration | Stage 5 | Specified | AI quality owner | Evidence to create: labeled calibration set, agreement threshold, drift report, and fallback rule | Internal/commercial |
| ER-007 | AI | Multilingual, caption, voice, and presenter-media evaluation | Stages 6-7 | Specified | AI/media owner | Evidence to create: language/media suites and manifests | Demo/commercial |
| ER-008 | Data | Source, chunk, retrieval, evaluation, approval, and artifact lineage | Stages 4-5 | Specified | Data/AI owner | `docs/DATA_MODEL.md`; `docs/TRACEABILITY.md` | All |
| ER-009 | Security | Prompt injection, untrusted uploads, provider output validation, tenant isolation | Stages 2/5 | Specified | Security owner | `docs/THREAT_MODEL.md`; security tests | All |
| ER-010 | Privacy | Consent, provenance, retention, deletion, redaction, and compliance metadata | Stages 2/7/8 | Specified | Security/privacy owner | `docs/SECURITY_AND_PRIVACY.md`; legal review to create | Commercial/public |
| ER-011 | Architecture | Provider-agnostic adapters and replaceable storage/evaluation boundaries | Stage 2 | Designed | Architecture owner | ADRs and architecture contract | Commercial |
| ER-012 | DevOps | CI/CD, environments, migrations, feature flags, rollback, and release approvals | Stage 3/8 | Specified | Platform/release owner | quality gates and release checklist | Commercial |
| ER-013 | Supply chain | Dependency/license review, SBOM, signing, image scan, and provenance | Stage 3/8 | Specified | Security/platform owner | third-party notices and CI evidence | Commercial/public |
| ER-014 | SRE | SLOs, SLIs, error budgets, alerting, on-call, incidents, and postmortems | Stage 8 | Specified | SRE/operations owner | ADRs `0024`/`0025`, runbook, dashboards | Commercial |
| ER-015 | Reliability | HA, failover, graceful degradation, backup/restore, RTO/RPO, and restore drills | Stage 8 | Specified | SRE/platform owner | Issue #39 closure artifacts and ADRs | Commercial/public |
| ER-016 | Scale | Capacity, load, latency, concurrency, queueing, caching, rate limits, and autoscaling | Stage 8 | Specified | Performance owner | Evidence to create: benchmark, capacity model, and threshold review | Commercial |
| ER-017 | Observability | Safe logs, metrics, traces, audit events, correlation IDs, cost, and privacy redaction | Stages 5/8 | Specified | Observability owner | `docs/OBSERVABILITY_AND_COST.md` | All |
| ER-018 | Operations | Ownership, runbooks, patching, support, maintenance, deprecation, and vendor exit | Stage 8 | Specified | Operations owner | `docs/RUNBOOK.md`, release review | Commercial |
| ER-019 | Accessibility | Keyboard, screen reader, captions, contrast, and accessible presenter review | Stages 4-7 | Specified | UX/accessibility owner | Evidence to create: browser/accessibility report | Public |
| ER-020 | Commercial | Quotas, cost ceilings, tenant administration, billing boundaries, legal review, and launch gates | Stage 8/final | Deferred | Product/release owner | Evidence to create: release-readiness review and legal/commercial approval | Commercial/public |

## Non-negotiable boundaries

Specification is not implementation, validation, deployment, or launch approval.
Paid providers remain optional and disabled by default in local/dev/test. No
public or production claim is permitted until the relevant rows are validated
and approved through the stage and release gates.

## Concrete target baseline

The detailed Cut 1–5 roadmap and requirement-to-evidence mapping are in
`docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md`. The following targets are the
baseline for later evidence; they are not claims that production exists today:

- Every read/write is tenant- and project-authorized; the negative suite must
  demonstrate 100% cross-tenant denial.
- Training reuse is disabled by default. Consent, purpose, retention, deletion,
  export, residency, and provider-processing terms are recorded per tenant.
- A deletion request creates an immediate tombstone and produces local purge
  evidence within 24 hours; provider-specific timelines require legal review.
- Internal pilot availability target is 99.5%; commercial target is 99.9%.
- Commercial recovery target is RTO <=4 hours and RPO <=15 minutes, proven by a
  measured restore/failover drill.
- A 5% relative AI-quality regression, 10% distribution/latency shift, or any
  safety/privacy/provenance regression blocks model/prompt promotion.
- WCAG 2.2 AA, captions, keyboard access, reduced motion, and >=4.5:1 normal
  text contrast are required for public-readiness review.

The register's `Specified` status means the decision is complete. The status
may advance to `Validated` only when the evidence artifact in the roadmap
matrix exists, passes, and has an accountable human reviewer.

## Issue #452 readiness disposition

The executable provider schema now requires closed rights/consent bindings,
identity compatibility, training/region/retention/deletion evidence,
SecretRef-only credentials, six-segment screening, disabled egress policy,
hard call/time/retry/concurrency/spend controls, idempotency, tenant/project/
actor lineage, output distrust, disclosure, reproducibility, observability,
tombstones and resurrection checks. Current eligibility remains
`NOT_AUTHORIZED`, `CONDITIONAL`, or `EXPLORATORY_ONLY`; no row is `Validated`.
