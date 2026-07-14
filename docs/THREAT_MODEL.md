# Threat Model

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-07-14
- Scope: pre-implementation architecture, first vertical slice, and issue `#141`
  production-like durability platform planning

## Scope

This threat model covers the planned NarraTwin AI system through Stage 4 Slice 1 and
the future provider/media boundaries that Stage 2 must account for.

In scope:

- frontend upload and walkthrough request flow
- backend API boundary
- ingestion worker
- RAG service and vector store
- script generation service
- evaluator service
- storage adapters
- provider abstraction
- avatar rendering adapter boundary
- observability and audit logs
- CI quality gates

Out of scope for implementation in Stage 2:

- product runtime code
- deployed infrastructure
- real avatar/video rendering
- real voice cloning or face cloning
- premium provider integration
- multi-user authentication implementation

## Assets

| Asset | Sensitivity | Notes |
|---|---|---|
| Provider keys | Critical | Must never reach frontend, prompts, logs, or git |
| Uploaded project knowledge | High | May contain confidential project data |
| Generated scripts | Medium to high | May contain unsupported or sensitive claims |
| Source chunks and context refs | High | Grounding basis for outputs |
| Evaluation results | Medium | Reviewer evidence and quality gate input |
| Project metadata | Medium | Future tenant/project isolation boundary |
| Audit logs | Medium | Must not contain secrets |
| Future avatar/voice/video artifacts | High | Consent, disclosure, and licensing risk |
| Future consent records | Critical | Required for identity media |
| Production-like PostgreSQL state | Critical | Stage 4/6/7 synthetic business state, relationships, replay controls, provenance, and consent references |
| Authoritative S3 artifact versions | Critical | Exact Stage 4/6/7 source/audio/render/export Version IDs and checksums; mutable aliases are not authoritative |
| Independent deletion/revocation journal | Critical | Gap-free, integrity-linked current control state outside RDS PITR; incomplete or unavailable state can resurrect deleted/revoked data |
| Backup/recovery-point catalog | High | Resource identities, restore timestamps, KMS references, status, retention, and evidence hashes; never credentials or payload data |
| Restore-validation environment | Critical | Destructive-operation target that must be isolated from the source and user traffic |

## Trust Boundaries

```text
Browser/user input
-> Backend API validation
-> Storage and metadata boundary
-> Versioned S3 artifact boundary
-> Independent security-control journal boundary
-> Ingestion worker
-> RAG/vector-store boundary
-> Prompt assembly boundary
-> External provider boundary
-> Evaluator boundary
-> Output display boundary
-> Observability/audit boundary
```

Untrusted:

- uploaded files
- filenames
- request bodies
- user prompts
- project docs used as RAG context
- transcripts
- provider responses
- model outputs
- vector-store records until metadata is verified
- future webhooks/callbacks

## Authorization Boundary

Stage 4+ local mode still has an authorization boundary. The default actor is
the synthetic local user `user_local` inside synthetic local tenant
`tenant_local`. In trusted local/dev/test only, `X-Local-User-Id` can simulate a
different local actor after strict normalization and validation. This header is
not authentication and is rejected as a production identity source.

Every project-scoped operation validates the resolved principal before lookup,
retrieval, generation, evaluation, export, or deletion.

The authorization predicate is `(tenant_id, owner_id, project_id)`. Child resource
queries either include all three fields directly or run only after a server-side
project authorization guard has verified ownership on `Project`.

## STRIDE Analysis

| Boundary | Spoofing | Tampering | Repudiation | Information disclosure | Denial of service | Elevation of privilege |
|---|---|---|---|---|---|---|
| Frontend to backend | forged user/project IDs | modified request parameters | denied upload/generation | leaked project metadata | repeated requests | access another project |
| Upload intake | fake content type | path traversal filename | denied malicious upload | uploaded secrets exposed | huge files/corpus | executable content used |
| Ingestion | fake metadata | poisoned chunks | denied ingestion action | raw content in logs | chunk explosion | bypass validation |
| RAG retrieval | fake project context | altered vector metadata | denied retrieval | cross-project chunks | expensive retrieval | retrieve unauthorized project |
| LLM provider | fake provider config | prompt injection | denied provider call | secrets in prompt | token/cost exhaustion | model controls tools |
| Deterministic Stage 4 evaluator | fake pass result | altered eval result | denied safety failure | raw evaluator payload leakage | eval loop abuse | bypass failed eval |
| Storage | fake artifact IDs | overwritten outputs | denied changes | unauthorized download | storage exhaustion | path traversal |
| Observability | fake event actor | altered logs | missing audit trail | secret logging | log volume abuse | hide malicious actions |
| Future avatar provider | fake consent | altered media output | denied render | identity/media leakage | render cost abuse | clone identity without consent |
| RDS source and backup path | forged operator or workload role | retention, recovery point, DB or KMS mutation | missing CloudTrail/database audit | backup/catalog/secret disclosure | connection, storage or backup exhaustion | workload becomes administrator |
| Versioned S3 artifact path | forged artifact/version identity | Version-ID substitution, checksum drift, delete marker or orphan/reference corruption | missing object/version audit | artifact or locator disclosure | KMS/object/version unavailable | workload or restore role mutates protected source versions |
| Security-control journal path | forged writer/event identity | suppressed, duplicated, reordered or rewritten event; gap/high-watermark rollback; retention bypass | missing delivery/break-glass audit | pseudonymous scope/resource leakage | journal/KMS/manifest unavailable or delivery backlog | writer bypasses retention or reader trusts mutable current key |
| Restore-validation target | forged target identity | source DB/KMS/VPC mutated instead of target | unsigned or incomplete evidence | restored data exposed through traffic/logs | orphaned target cost or restore flood | restore operator crosses into source boundary |

The Stage 4 evaluator boundary is deterministic and rule-backed. Model-as-judge evaluation is future scope and requires an ADR before it can affect acceptance or security decisions.

## Abuse Cases

### A1: Prompt Injection In Uploaded Markdown

Attack:

- uploaded doc tells the model to ignore system rules, reveal secrets, or make
  unsupported claims

Controls:

- treat uploaded docs as untrusted evidence
- delimiter prompt context
- enforce provider/tool permissions in code
- add malicious fixture tests
- evaluate unsupported claims

### A2: Cross-project Retrieval

Attack:

- user causes retrieval to include chunks from another project

Controls:

- every retrieval query includes `tenant_id` and `project_id` after the
  `(tenant_id, owner_id, project_id)` authorization guard
- vector-store metadata is validated
- tests assert cross-project isolation
- provider prompt includes only authorized context

### A2b: Approved Knowledge Poisoning

Attack:

- attacker uploads markdown that passes file validation and is silently treated as
  approved source-of-truth RAG content

Controls:

- uploaded documents start as `UPLOADED`, `STORED`, or `QUARANTINED`
- `document_status = STORED`, `approval_status = APPROVED`, and
  `ingestion_status = INGESTED` are required before retrieval or non-local provider
  egress
- prompt-injection text remains untrusted evidence, not instructions
- approval, quarantine, rejection, and deletion emit audit events

### A3: Secret Exfiltration Through Provider Prompt

Attack:

- uploaded file or environment accidentally includes provider key or token and is
  sent to an external provider

Controls:

- repository secret scanning
- mandatory `SecretScreeningResult` before any non-local provider egress, with
  scanner version, categories, blocking decision, redaction decision, optional
  reviewer override, and audit event
- secret screening is mandatory before any non-local provider egress
- no secrets in prompt assembly
- provider egress disabled by default locally
- no raw prompts in logs

### A4: Unsupported Portfolio Claims

Attack:

- generated script invents metrics, architecture, users, or business impact

Controls:

- context references required
- unsupported-claim evaluator
- empty-context refusal
- UI warnings
- failed eval blocks silent acceptance

### A5: Path Traversal Upload

Attack:

- filename such as `../../.env` attempts to overwrite local files

Controls:

- generated storage paths
- filename sanitization
- extension/content allowlists
- no direct use of original filename as filesystem path

### A6: Cost Exhaustion

Attack:

- repeated generation or huge uploads drive provider cost

Controls:

- upload and corpus limits
- token/output caps
- route and provider-mode rate limits
- caching
- estimated cost metadata

### A7: Identity Media Misuse

Attack:

- avatar or voice output implies consent from a real person

Controls:

- mock avatar default
- no face or voice cloning in MVP
- explicit documented consent before cloned identity features
- AI-generated media disclosure
- third-party/license review

### A8: Source/Restore Target Confusion

Attack:

- a privileged or faulty restore procedure treats the source RDS instance as the
  disposable target and mutates, disables protection on, or deletes source state

Controls:

- distinct VPC, subnet group, security group, IAM role, DNS namespace, DB
  resource identity, and required environment tags; direct PITR inherits the
  source storage CMK, so the catalog records shared-key identity instead of
  asserting false key inequality
- explicit target allowlist plus immutable source resource denies; tags alone do
  not authorize destructive action
- no application/user traffic to the target
- operator holdpoint, source/target inequality checks, teardown deadline, and
  independent Operations/Security review

### A9: Backup, Catalog, or Restore Evidence Exfiltration

Attack:

- backup access, restored content, catalog fields, logs, or evidence exports leak
  secrets, document text, provider payloads, or customer data

Controls:

- synthetic data only in pre-production; no production-to-pre-production copy
- customer-managed KMS encryption, TLS, private RDS access, SSO/MFA, short-lived roles,
  GitHub OIDC, Secrets Manager rotation, and no application access to master secret
- restricted catalog containing minimum operational identities plus a separate
  allowlisted/keyed-pseudonym reviewer export; both reject connection strings,
  credentials, tokens, content, direct user attributes, and provider payloads
- S3 source/restore/control bucket separation, immutable Version IDs/checksums,
  private SSE-KMS access, and at least 15-day noncurrent-version retention
- committed deletion outbox to a versioned/Object-Locked control-bucket journal
  outside RDS PITR; CH-14 derives its handoff from that current journal and
  CH-21 owns erasure/re-delete proof
- 14-day RDS PITR, bounded manual-snapshot/target TTL, and at least 90-day
  sanitized evidence/journal retention

### A10: S3 Artifact Version Substitution Or Publication Split-Brain

Attack:

- an actor publishes a PostgreSQL ready reference before the immutable object is
  verified, swaps a mutable alias/version, hides a version behind a delete marker,
  or deletes an orphan/reference without proving reachability

Controls:

- unique immutable keys and exact Version-ID/SHA-256 reads; unversioned/current
  aliases are rejected
- S3-version-first verification before transactional PostgreSQL publication;
  failed database publication quarantines the unreferenced version
- idempotent retry, referenced-version protection, and explicit tests for
  S3-success/database-failure, checksum mismatch, unavailable object, delete
  marker, orphan cleanup and garbage-collection reachability
- source roles deny mutation/version deletion; restore copies use scoped
  `GetObjectVersion`, KMS decrypt, destination put and data-key permissions only

### A11: Deletion Journal Suppression, Reordering, Or Rollback

Attack:

- delivery drops or reorders committed deletion/revocation events, a writer
  reuses a key/sequence, a delete marker masks a locked version, a privileged
  actor bypasses governance retention, or KMS loss makes the current journal
  unavailable while a stale high-watermark appears healthy

Controls:

- one create-only key per opaque scope/sequence/event ID; writer cannot overwrite,
  delete, shorten retention or bypass governance mode
- monotonic committed outbox sequence, last-contiguous high-watermark, gap and
  duplicate rejection, previous/event digest chain, versioned integrity manifest,
  version-aware enumeration and delete-marker rejection
- Platform/Storage reconciliation plus backlog/gap/KMS/retention alarms;
  Operations acknowledgment/escalation and Security-reviewed break-glass audit
- control-key disable/deletion safeguards, default retention verification, and
  negative tests for gaps, out-of-order delivery, missing retention, delete
  markers, hash mismatch, key unavailability and governance bypass
- restored consent/render/export state remains disabled until the journal and
  current CH-17 revocation/takedown source are reconciled

## Control Matrix

| Risk | Primary control | Evidence required |
|---|---|---|
| Secret leakage | secret scanning and no secret logging | CI scan and log redaction review |
| Prompt injection | context-as-data pattern | malicious upload fixture |
| Unsafe uploads | validation and generated paths | upload security tests |
| Cross-project data leak | project-scoped queries | isolation tests |
| Provider key exposure | backend-only adapters | config and adapter tests |
| Unsupported claims | evaluator and context refs | eval fixture report |
| DoS/cost abuse | rate limits and caps | rate-limit and token-cap tests |
| Supply-chain risk | dependency scanning | scan artifacts and notices |
| Web baseline issues | OWASP ZAP baseline when web exists | scan artifact |
| Identity media misuse | consent and disclosure | consent/disclosure tests |
| Source/target confusion | identity inequality, target allowlist, source deny | platform API evidence and wrong-target negative tests in issues `#144`/`#147` |
| Backup/evidence disclosure | KMS/private access/role separation/redacted schema | Security approval and negative redaction/access tests in issues `#145`/`#148` |
| Artifact version/publication split-brain | immutable version binding and publication compensation | adapter/object failure tests in issue `#143` and recovery parity in `#147` |
| Journal integrity/availability | contiguous sequence, integrity manifest, version-aware reads, alarms | writer/reconciliation/retention/KMS negative evidence in issues `#143`, `#145`, and `#148` |

## Issue #141 residual threats and blockers

ADR `0027` proposes RDS PostgreSQL 17.10 Multi-AZ in `ap-south-1` and a
same-account/region restore-validation target isolated by network, IAM, DNS,
resource identity, and traffic boundaries. Direct PITR inherits the source
storage CMK, so shared account/key blast radius is an explicit residual.
Same-account isolation has not been approved or deployed. The AWS account/payer, budget owner, region/data
residency approval, Operations owner, Platform/Storage owner, independent
Security reviewer, GitHub environment approvers, service quotas, and live engine
availability remain external blockers. No platform, backup, target, RTO/RPO, or
restore result is evidenced by this threat-model update.

## Open Threats Before Stage 4

- exact local vector-store dependency must pass review
- OWASP baseline scan cannot run until a web surface exists

## Review Cadence

Update this threat model when:

- a new external provider is added
- a new upload type is allowed
- authentication or multi-user access is implemented
- storage or vector-store architecture changes
- avatar, voice, subtitle, or video output is introduced
- security scans produce critical/high findings
