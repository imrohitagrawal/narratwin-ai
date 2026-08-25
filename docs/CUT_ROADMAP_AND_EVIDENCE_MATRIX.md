# Cut Roadmap and Evidence Matrix

Status: proposed with Issue #440; this is the single roadmap and acceptance
index for Cut 1 through Cut 5. It does not authorize implementation by itself.

## Authority and interpretation

`docs/STATUS.md` is the current ledger. `docs/PHASE_PLAN.md` is the delivery
sequence. The presenter, AI-quality, and enterprise contracts define the
requirements. This document maps each requirement to observable evidence so a
future agent cannot substitute an older issue, a prose promise, or a green CI
run for the required proof.

The status values below describe decision maturity, not a claim that the
feature already exists:

- `Specified`: owner, behavior, boundary, and acceptance rule are fixed.
- `Evidence required`: the implementation must produce the listed artifact.
- `Accepted`: the artifact passed its gate and was reviewed.
- `Deferred`: intentionally outside the current cut.
- `Blocked`: a prerequisite or owner decision prevents progress.

## Cut roadmap

| Cut | User-visible outcome | Included | Explicitly excluded | Exit gate |
|---|---|---|---|---|
| Cut 1 | A human-like Meera-led project explanation that a reviewer can run locally | Meera primary, Raj/Myra fallback, approved script, waist-up or mid-thigh framing, camera-directed eye contact, face/head/torso/hand/hair continuity, lip sync, captions, provenance, grounded claim review, and the demo checklist | Full-body walking, arbitrary live Q&A, public hosting, paid providers, cloned real-person identity, and production claims | `docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md` passes with all P0 rows and human review |
| Cut 2 | The same presenter path in approved additional languages | Language selection, translation/localization, glossary protection, captions, pronunciation, voice/media manifests, and multilingual evaluation | Unbounded language coverage, unsupported-language generation, and public distribution | Every supported-language row passes the AI contract and media report |
| Cut 3 | Grounded interactive project Q&A | User-selected language, audience, depth and style; retrieval-bound answer; citations; abstention; unsupported-claim evaluation; safe conversation state | Open-domain answers, autonomous actions, unsourced memory, and silent model learning | Golden suite, adversarial suite, lineage, and human review gates pass |
| Cut 4 | Broader avatar and provider capability | Full-body or expanded framing only where separately approved, richer gesture/head/eye/hair motion, provider-neutral adapters, export and fallback behavior | Real-person likeness without consent, mandatory paid providers, or provider lock-in | Media, provenance, safety, cost, accessibility, and rollback evidence pass |
| Cut 5 | Enterprise/commercial operating readiness | Multi-tenant controls, SLOs, HA/DR, capacity, observability, incident response, accessibility, support, cost, compliance, and launch review | Automatic public launch, legal approval by CI, or production claims without human sign-off | Enterprise register is validated, release checklist passes, and final review approves |

## Cut 1 numeric acceptance contract

These are the minimum gates for the controlled Cut 1 demo. A failure blocks the
cut; averages cannot hide a failed critical row.

| ID | Measure | Required threshold | Evidence |
|---|---|---|---|
| C1-M01 | Camera-directed eye contact | At least 80% of speaking intervals; no unintentional off-camera interval longer than 2 seconds | Timed gaze annotation and reviewer replay |
| C1-M02 | Lip synchronization | P95 audio/viseme offset at or below 80 ms; no continuous segment above 200 ms | Audio/video measurement report |
| C1-M03 | Caption fidelity | At least 98% word accuracy for the approved Cut 1 language; no missing caption span above 1 second | Caption diff report |
| C1-M04 | Grounded claims | 100% of material claims have source/chunk references; unsupported-claim rate is 0 on the Cut 1 golden suite | Evaluation report and source manifest |
| C1-M05 | Abstention | 100% refusal or clarification on deliberately unsupported golden cases | Negative-evaluation report |
| C1-M06 | Identity continuity | Zero presenter, clothing, hair, background, or face identity violations in the reviewed clip set | Asset/render checksum and human review |
| C1-M07 | Gesture quality | Zero malformed-limb/finger artifacts; no repeated gesture pattern more than twice consecutively | Adversarial media review |
| C1-M08 | Accessibility | WCAG 2.2 AA keyboard path; captions enabled; contrast at least 4.5:1 for normal text; reduced-motion option available | Browser/accessibility report |
| C1-M09 | Demo latency | P95 script/evaluation completion at or below 20 seconds on the governed local fixture; media preview begins within 5 seconds after artifact readiness | Timed demo trace |
| C1-M10 | Reproducibility | Same fixture/configuration produces identical canonical script, source bindings, evaluator version, and manifest checksum | Two-run parity report |

## Requirement-to-evidence matrix

| ID | Requirement | Canonical source | Evidence artifact | Gate / owner |
|---|---|---|---|---|
| E-001 | Presenter order and original provenance | Presenter contract | Identity registry, asset manifest, checksum report | Cut 1 / Product |
| E-002 | Eye contact, framing and motion | Presenter contract | Timed media review and adversarial render report | Cut 1 / Media |
| E-003 | Lip sync, captions and voice | Presenter contract; AI contract | Sync, caption and voice-manifest report | Cut 1/2 / Media |
| E-004 | Grounded claims and abstention | AI contract | Source-run manifest plus golden/negative evaluation report | Cut 1/3 / AI |
| E-005 | Golden suite composition | AI contract | Versioned dataset, checksums, case counts and release report | Stage 5 / AI |
| E-006 | Ragas/custom evaluator decision | AI contract | Dependency/license decision and evaluator output | Stage 5 / AI/Security |
| E-007 | LLM-judge calibration | AI contract | Human-labeled calibration set, agreement and drift report | Stage 5 / AI |
| E-008 | Model/prompt/retrieval lineage | AI contract | Run manifest with immutable versions and checksums | Stages 4-7 / Data |
| E-009 | Model promotion and rollback | AI contract | Canary report, approval record and rollback drill | Stages 5/8 / Platform |
| E-010 | Tenant isolation and authorization | Enterprise register | Cross-tenant negative suite and access audit | Stage 4/8 / Security |
| E-011 | Consent, retention and deletion | Enterprise register | Consent record, deletion/tombstone and purge report | Stages 4/7/8 / Privacy |
| E-012 | Safe logs and auditability | Enterprise register | Redaction test, correlation trace and audit-event report | Stages 5/8 / Observability |
| E-013 | SLOs and error budgets | Enterprise register | SLI dashboard, alert test and error-budget review | Stage 8 / SRE |
| E-014 | HA, DR, RTO and RPO | Enterprise register | Failover/restore drill and measured RTO/RPO report | Stage 8 / SRE |
| E-015 | Capacity, latency and cost | Enterprise register | Load test, capacity model, quota and cost report | Stage 8 / Performance |
| E-016 | Supply-chain integrity | Enterprise register | SBOM, license review, image scan and provenance record | Stages 3/8 / Security |
| E-017 | Accessibility and public-use behavior | Enterprise register; Cut 1 checklist | WCAG/browser report and legal/compliance review | Cuts 1/5 / UX/Legal |
| E-018 | Demo acceptance | Cut 1 checklist | Signed checklist, run trace, screenshots/media manifest | Cut 1 / Product |

## AI/MLOps operating protocol

1. Register every model, provider, prompt, retriever, evaluator, dataset and
   media renderer with version, owner, license, checksum and approval state.
2. Store an immutable run manifest linking tenant/project, source snapshot,
   retrieval result, prompt, model, evaluator, output and media artifacts.
3. Promote only through deterministic checks, golden suites, adversarial cases,
   calibrated human/LLM review, canary comparison and explicit approval.
4. Trigger investigation at a 5% relative quality regression, a 10% input or
   latency distribution shift, or any safety/privacy/provenance regression.
   Two consecutive failing evaluation windows block promotion.
5. Roll back to the last approved model/prompt/index/media bundle within 15
   minutes of a release-blocking regression in an operational environment.
6. Do not perform uncontrolled online self-training or agent-led production
   weight/policy changes. Agent feedback becomes a reviewed issue, dataset case,
   test, prompt/model change, or postmortem action.

## Enterprise and tenant targets

These targets are design gates; the release review may tighten them, but may
not silently loosen them:

- Tenant and project authorization is checked on every read/write; the negative
  suite must show 100% cross-tenant denial.
- Source and generated artifacts are encrypted in transit and at rest; secrets,
  raw private documents, prompts, transcripts, and provider payloads are absent
  from ordinary logs.
- Training reuse is disabled by default. Consent, purpose, retention, deletion,
  export, residency, and provider-processing terms are recorded per tenant.
- A deletion request creates an immediate tombstone and produces purge evidence
  within 24 hours for local-controlled data; provider-specific timelines require
  a separately approved legal/provider record.
- Internal pilot target: 99.5% service availability; commercial target: 99.9%.
  Commercial targets require measured SLOs, alerting and error-budget action.
- Commercial recovery target: RTO at or below 4 hours and RPO at or below 15
  minutes, proven by a restore/failover drill; local demo does not claim this.
- Provider/model calls have explicit per-tenant quotas, timeout/retry limits,
  and a cost budget; no paid provider is enabled by default in local/dev/test.

## Decisions intentionally deferred

The following are not missing requirements; they are later-stage choices that
must remain visible rather than being guessed early:

- final paid provider, region, plan, and commercial contract;
- exact full-body motion scope and rendering technology;
- final production cloud topology and database/storage vendor;
- final language list beyond the approved Cut 2 set;
- legal wording, jurisdiction, retention exceptions, and public launch approval;
- model fine-tuning or continuous-training strategy;
- commercial pricing, billing, support tiers and external SLA wording.

Each deferred choice requires a new issue, owner, ADR or release artifact before
it can change an acceptance gate.
