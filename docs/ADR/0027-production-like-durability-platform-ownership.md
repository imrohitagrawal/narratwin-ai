# ADR 0027: Production-Like Durability Platform and Ownership

## Status

Proposed technical baseline for issue `#141`; ADR acceptance and activation are
blocked on the human approvals in this ADR. Not deployed and not production-like
durability evidence.

## Date

2026-07-14

## Context

The repository has PostgreSQL-compatible durability contracts and local
file-backed evidence, but it has no verified shared PostgreSQL environment,
backup catalog, isolated restore target, cloud account evidence, or successful
production-like restore. Issue `#141` must select the platform and ownership
boundary before issues `#142` through `#149` can create or verify those things.

This ADR supersedes the provider-neutral parts of ADR `0008` and specializes the
advisory backup plan in ADR `0011`. It does not implement a restore drill, close
issue `#126`, close matrix row `DUR-RESTORE-001`, or close issue `#39`.

## Decision

### Authoritative platform

The selected production-like source is Amazon RDS for PostgreSQL `17.10`,
Multi-AZ DB instance deployment, in AWS region `ap-south-1` (Mumbai). It runs in
a dedicated non-production AWS account and private VPC, with at least two
private DB subnets in distinct Availability Zones. Public accessibility is off.

PostgreSQL is authoritative for application business state and the metadata
needed to identify, authorize, verify, restore, and delete artifacts. Amazon S3
general-purpose buckets with Versioning are authoritative for approved upload,
audio, render, and export bytes. PostgreSQL retains the immutable bucket class,
object key, S3 Version ID, SHA-256 checksum, data class, provenance,
consent/deletion state, and ownership scope. Current approved normalized
Markdown text and chunks also remain in PostgreSQL so Stage 4 is recoverable
without a local-file dependency.

The source, restore-validation, and security-control S3 buckets are in the same
non-production account and `ap-south-1`, are private, block public access, use
SSE-KMS, and have distinct bucket names/ARNs, IAM policies, and KMS keys. The
control bucket stores the sanitized backup catalog, evidence, and append-only
deletion journal; it is never an application artifact bucket.

Production-like and eventual production deployments may differ in instance
class, storage allocation, autoscaling limits, and synthetic data volume. They
must not differ in engine major/minor pin, Multi-AZ posture, private networking,
TLS enforcement, customer-managed KMS encryption, RDS backup/PITR, S3
Versioning/noncurrent retention, source/target/control bucket separation, IAM
boundaries, secret rotation, audit/monitoring controls, or deletion protection.
Any minor-version change requires compatibility evidence and a reviewed ADR
amendment before rollout.

### Environment, account, and region boundaries

| Boundary | Contract |
|---|---|
| Local/dev/test | Docker PostgreSQL 17, in-memory state, and optional JSON state are developer evidence only and cannot prove this ADR is deployed. Paid providers remain disabled. |
| Pre-production source | Dedicated non-production AWS account, `ap-south-1`, private source VPC and source artifact bucket, synthetic data only, no public or production traffic. |
| Restore validation | same non-production account and region, but a dedicated restore VPC, subnet group, security groups, IAM roles, DNS namespace, artifact bucket, and required `narratwin:environment=restore-validation` tags. Direct RDS PITR inherits the source storage CMK; that shared-key residual requires Security approval. |
| Production | A separate production AWS account is required before Go. This ADR neither provisions nor approves it. No production data may be copied into pre-production. |

The restore target uses the same account/region for direct RDS point-in-time
restore. The RDS point-in-time API has no target storage `KmsKeyId` parameter, so
the restored instance inherits the source storage CMK. Cross-account or
re-encrypted snapshot restore requires manual KMS/snapshot sharing or copying,
which changes the direct PITR path. The same-account/shared-key target is
therefore a deliberate exception that requires independent Security approval
before issue `#144`; without that approval, `#144` must redesign the target and
re-baseline RPO assumptions.

The target must have a distinct VPC ID, DB subnet group, security-group IDs, IAM
restore role, DB identifier/ARN, and DNS suffix from the source. The catalog must
record that the storage KMS ARN is inherited rather than falsely asserting key
inequality. The target must never receive application or user traffic.
Automation must compare source and target identifiers before mutation, allow
only the target through an explicit allowlist, and deny source DB/KMS/network
mutation even when tags drift.

### Durable-state ownership for Stages 4, 6, and 7

| Stage | Authoritative durable state | Deliberately excluded from recovery scope |
|---|---|---|
| Stage 4 | PostgreSQL: projects; document identity/approval/normalized text; ingestion runs; chunks and embeddings/version metadata; retrieval context; walkthrough/generated-script state; claim/evaluation/citation evidence; idempotency, leases, outbox, audit, migration, ownership and transitions. S3: approved original upload version. PostgreSQL binds every object Version ID/checksum. | Rejected/unvalidated upload bytes, prompt scratchpads, provider wire payloads, caches, temporary parsing files, local JSON snapshots, secrets. |
| Stage 6 | PostgreSQL: translation/voice run, translated script/subtitle text, voice manifest, provider/fallback metadata, request dedupe/idempotency and source/evaluation/provenance linkage. S3: generated audio/downloadable artifact versions. PostgreSQL binds every object Version ID/checksum/class. | Raw provider responses, transient transcripts, provider caches, secrets, temporary work files. |
| Stage 7 | PostgreSQL: synthetic-media consent/idempotency, render request/result/status history, provider metadata, disclosure/provenance/source/evaluation/consent bindings and render idempotency. S3: render/export artifact versions. PostgreSQL binds every object Version ID/checksum/class. | Raw provider responses, cloned-identity material, transient work files, secrets, local previews not accepted as artifacts. |

Content restored from these data classes remains untrusted. Restore validation
must re-run schema, scope, checksum, consent, provenance, prompt-injection, and
retrieval-poisoning checks before replay or export.

The Application/Data owner (`@imrohitagrawal` for the current repository) owns
the logical Stage 4/6/7 schema, write invariants, and completeness of consent and
provenance references. Platform/Storage owns the physical PostgreSQL and S3
services, capacity, availability, recovery configuration and catalog. Security/Privacy owns consent,
provenance, retention and erasure policy and independently reviews their schema
and restored behavior. Operations owns recovery execution and the decision that
a validated target is operationally ready. This separates business meaning from
physical custody and recovery execution.

### Backup mechanism and artifact catalog

The baseline mechanism is RDS automated backups with continuous transaction-log
capture and point-in-time restore, configured for `14 days` retention. A drill
must select an immutable UTC restore timestamp; mutable `latest` is prohibited.
Manual drill snapshots may be used for portability evidence but are not a
substitute for PITR and must follow the same deletion rules.

S3 recovery uses Versioning plus a lifecycle rule that retains noncurrent source
artifact versions for at least `14 days`. Each PostgreSQL artifact row selects
an immutable S3 Version ID and checksum, so the database recovery point also
selects exact artifact bytes. The restore procedure copies those exact versions
to the isolated restore bucket and validates checksums; reading an unversioned
key or mutable current version is prohibited. Versioning is not represented as
a separate database backup, and its configuration/evidence belongs in the same
catalog and readiness review.

The security-control bucket uses Versioning and S3 Object Lock governance mode
for the sanitized catalog/evidence and append-only deletion journal. A deletion
is not acknowledged as complete until the committed PostgreSQL outbox event is
written to that journal and its opaque deletion ID is confirmed. The journal
stores entity/object identities, scope, deletion time, policy version and event
checksum—not content or user attributes—and is not rolled back with RDS PITR.
Only the Security/Privacy break-glass role can bypass governance retention.

The Platform/Storage owner is accountable for backup configuration and owns the
backup artifact catalog. Operations is the executing consumer and verifies
restorability. Security reviews KMS, access, retention, redaction, and evidence
handling. The catalog must contain:

- catalog/run ID; source DB resource ID and sanitized ARN; account class and region;
- engine version, topology, schema and synthetic-seed manifest versions;
- automated-backup or snapshot identifier; earliest/latest restorable UTC times;
- selected immutable restore UTC timestamp and service-reported backup status;
- sanitized KMS alias/ARN, retention expiry and deletion state;
- source/control/target S3 bucket class; artifact key hash, Version ID, object
  checksum, version-retention status and target-copy Version ID;
- deletion-journal high-watermark/event checksum used for the re-delete handoff;
- evidence SHA-256, creation/verification timestamps, owner and reviewer;
- target DB resource ID/ARN after restore and teardown outcome.

Catalog entries, metrics, and evidence must not contain connection strings,
credentials, tokens, document text, provider payloads, or customer data.

### Access control and secrets

- Humans use AWS IAM Identity Center, MFA, short-lived role sessions, and
  least-privilege separation between platform deployer, restore operator,
  catalog reader, security auditor, and break-glass administrator.
- GitHub deployment uses environment-protected OIDC federation. Static AWS keys
  are forbidden in GitHub, repository files, CI artifacts, and local examples.
- The workload identity receives only its application database secret and
  network path plus scoped source-artifact object permissions. The RDS master
  secret is RDS-managed in Secrets Manager, rotated, excluded from application
  access, and reserved for audited break-glass.
- Operators use RDS IAM database authentication with short-lived tokens. Workload
  credentials are Secrets Manager-managed and rotated; no secret is placed in
  backup catalogs or restore evidence.
- TLS certificate verification and `rds.force_ssl=1` are mandatory. Database
  roles are migration, application, read-only validation, and audited break-glass.
- The restore operator can create/inspect/delete restore-validation resources but
  has explicit deny controls for source DB, source KMS key, source VPC, backup
  retention changes, source/control S3 version deletion, Object Lock bypass, and
  deletion-protection removal.

### Retention, encryption, and integrity

| Data/evidence | Requirement |
|---|---|
| Automated backups/PITR logs | 14 days. Platform configures and proves the window; Security approves any change. |
| S3 source artifact versions | S3 Versioning enabled; current and noncurrent versions recoverable for at least 14 days. Permanent version deletion is denied to application and restore roles. |
| Manual drill snapshot | Delete after accepted evidence or within 14 days, whichever is earlier. |
| Restore DB and artifact bucket | Tear down/delete copied versions within 24 hours after evidence capture; hard maximum 72 hours requires dated Security and Operations exception. |
| Sanitized catalog, deletion journal, metrics, audit and evidence packet | Minimum 90 days and never less than the longest recoverable source window plus 7 days; later deletion follows CH-21 policy. |

RDS storage, logs, automated backups, snapshots, and replicas use a
customer-managed KMS key and AES-256 service encryption. TLS protects transit.
Key policy must prevent broad account principals, enable audited rotation, and
document deletion safeguards. The direct-PITR target inherits the source storage
CMK; the restore operator receives no KMS administration rights, and target
teardown does not schedule or disable the shared key.

S3 source, restore and control buckets use SSE-KMS with distinct customer-managed
keys and TLS. Bucket policies block public access and non-TLS requests, deny
unversioned artifact writes, and separate application, restore, catalog and
Security/Privacy journal roles.

Every selected restore point and target is checked for engine/schema/seed
version, source identity, table/entity parity, FK/state-machine validity,
idempotency/lease/outbox replay safety, immutable object-locator/checksum parity,
S3 Version ID/checksum parity, current deletion-journal high-watermark, and
evidence SHA-256. A service status of `available` is necessary but not sufficient
for integrity or readiness.

Issues `#143` and `#144` establish the journal writer/control bucket before
CH-14: the application outbox produces deletion events and the independent
control bucket preserves the current ledger outside RDS PITR. CH-14 owns backup
configuration, catalog lifecycle, restore-target TTL, restore measurement, and
the handoff obtained by comparing restored IDs/object versions against that
current journal. CH-21 owns data-class erasure policy, permanent deletion across
primary/backups/restores, audit exceptions, and proof that handed-off restored
records/objects are re-deleted. CH-14 must validate and emit the handoff but does
not claim CH-21 behavior proof, preserving the dependency direction from CH-14
to CH-21 without deriving tombstones from the rolled-back database.

### RTO/RPO ownership and measurement

The planning targets remain RTO `<= 75 minutes` and RPO `<= 5 minutes`. They are
not measured or achieved by this ADR. The repository/business owner approves
thresholds and cost trade-offs. Operations is accountable for measured RTO and
the residual operational-risk decision. Platform/Storage is accountable for
measured RPO and backup-window evidence. Security reviews data exposure during
measurement.

- Observed RTO is `restore_ready_utc - restore_start_utc`. The operator records
  `restore_start_utc` immediately after the reviewed holdpoint and before the
  first backup-selection or recovery action. `restore_ready_utc` is captured
  only after DB availability, migration compatibility, entity/integrity
  validation, and replay-safe smoke checks pass. API-submitted, API-accepted,
  and DB-available timestamps are retained as diagnostic sub-intervals; they do
  not shorten the end-to-end RTO clock.
- Observed RPO is
  `latest_source_commit_watermark_utc - latest_restored_commit_watermark_utc`
  using database-server UTC timestamps plus a monotonic commit sequence from the
  same issue `#146` seed manifest. A negative delta, target-ahead sequence, clock
  ambiguity, or manifest mismatch invalidates the evidence; it is never clamped
  to zero. RDS backup lag and earliest/latest restorable time are diagnostics,
  not RPO proof.
- Issue `#148` owns durable metric/event export; issue `#147` owns the runbook
  timestamps; issue `#149` reviews only environment, tooling, calculation-test,
  and reviewer-handoff readiness. Actual RTO/RPO results belong to the later
  issue `#126` exercise. No measurement may be claimed until that exercise exists.

### Ownership and required review

| Role | Accountable responsibility | Required acceptance evidence |
|---|---|---|
| Repository/business owner (`@imrohitagrawal`) | Issue/PR governance; RTO/RPO thresholds; proposed budget and risk disposition. AWS payer/cost authority remains unverified. | Dated issue comment and PR approval. |
| Application/Data owner (`@imrohitagrawal`) | Logical Stage 4/6/7 entity schema, relationship/write invariants, consent/provenance reference completeness and adapter acceptance. | Schema/adapter PR review and validator acceptance. |
| Operations owner (unassigned human blocker) | Runbook, restore execution, RTO, smoke acceptance, cleanup and operational residual risk. | Named owner comment, runbook approval, exercise signoff. |
| Platform/Storage owner (unassigned human blocker) | Account/IaC, restore-target environment, RDS/S3/KMS/networking, backups/version retention, artifact catalog, capacity and RPO. | Named owner comment, architecture/IaC approval, catalog/evidence signoff. |
| Independent Security/Privacy reviewer (unassigned human blocker) | IAM, Secrets Manager, KMS, network isolation, consent/provenance/retention/erasure policy, redaction and same-account exception. | Independent PR approval and dated exception/denial comment. |

Documentation is not a human signoff. Issue `#149` aggregates these approvals;
each child issue must also obtain its role-specific approvals before closeout.

### Dependencies and acceptance for issues #142-#149

| Issue | Dependencies | Acceptance owned by that issue |
|---|---|---|
| `#142` connection-backed PostgreSQL and migrations | `#141` approved baseline and named Platform owner | Real connection-backed adapter and migrations; fail-closed startup/config; no file-backed success path; migration/restart evidence on PostgreSQL 17.10. No cloud provisioning. |
| `#143` Stage 4/6/7 durable adapters | `#141`, `#142` | In-scope business entities use PostgreSQL; approved bytes use a versioned-object adapter; committed deletion outbox writes the independent journal before deletion completion; restart/replay/CAS/idempotency/lease/outbox, locator/checksum and untrusted-input tests pass. |
| `#144` pre-production source and isolated restore-target IaC | `#141`; Security approval of same-account/shared-RDS-key exception | Reproducible private Multi-AZ RDS 17.10 source/target plus distinct source/restore/control S3 buckets, IAM/KMS/network isolation, target inequality and source-mutation fail-closed evidence. No drill. |
| `#145` backup and artifact catalog | `#141`, `#144` | 14-day RDS PITR and S3 noncurrent-version retention configured; immutable DB time/object Version IDs selected; control-bucket catalog/journal retention, KMS/access/status evidence complete. No restore execution. |
| `#146` synthetic seed and validator | `#141`, `#143` | Versioned synthetic Stage 4/6/7 graph and S3 objects, at least one deletion-journal event, server UTC/commit sequence, expected counts/checksums/relationships and negative corruption cases portable to `#144`. |
| `#147` restore runbook and safety controls | `#144`, `#145`, `#146` | Executable but not yet executed RDS/object restore runbook; exact S3 Version ID copies; target allowlist/source deny; journal-derived re-delete handoff; cleanup/TTL controls; RTO/RPO definitions and holdpoints. |
| `#148` restore observability and evidence export | `#141`, `#144`; metric names aligned with CH-10/CH-11 | RDS/S3 restore, backup/version, catalog/journal, cleanup events and metrics; sanitized export; alert ownership; negative-delta-invalidating RTO/RPO calculation tests. No successful-drill claim. |
| `#149` production-like restore readiness review | `#141` through `#148` | Verify actual environment, backup/version sources, target, validator, runbook, calculation-test/fixture metrics and independent approvals; record Go/No-Go for a later drill without actual RTO/RPO or restore-success claims. Must leave `#126`, `DUR-RESTORE-001`, and `#39` open. |

No child may use this ADR as evidence for a resource or backup that it must
create or inspect itself. Dependencies are merge/evidence gates, not permission
to collapse issues into this branch.

No environment, backup, target, or restore evidence exists for this decision.

## External approval blockers

Before issue `#144` can provision anything, humans must record the AWS payer and
non-production account IDs, budget/cost owner and limit, approved region/data
residency decision, Operations owner, Platform/Storage owner, independent
Security reviewer, same-account restore-target exception decision, GitHub
environment approvers, and live RDS version/quota availability. Until then this
decision is design-ready only and the related PR must remain draft.

`@imrohitagrawal` is the repository decision coordinator, not a verified AWS
payer authority. The cost owner remains unassigned until an authorized human
accepts the account and budget in issue `#141`.

## Alternatives considered

- Self-managed PostgreSQL on EC2/ECS/EKS was rejected because NarraTwin would own
  patching, HA, backup orchestration, and restore mechanics before proving value.
- Aurora PostgreSQL was rejected for this phase because its cluster/serverless
  capacity and restore semantics add cost and a new topology without a measured
  requirement.
- A separate restore AWS account is the stronger blast-radius boundary but was
  deferred because direct encrypted RDS PITR does not cross accounts. Revisit it
  if Security rejects the documented same-account exception.
- Local Docker/JSON was rejected as production-like evidence; it remains useful
  for deterministic unit and local integration tests only.

## Consequences

Issues `#142` through `#149` now have one platform and ownership contract.
Platform coupling to AWS RDS/KMS/Secrets Manager is accepted for operational
simplicity; the application remains PostgreSQL-portable at its data-access
boundary. Cost, owner assignment, region approval, and environment proof remain
external blockers.

## References

- [RDS PostgreSQL release history](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/doc-history.html)
- [RDS Multi-AZ DB instances](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)
- [RDS automated backups and PITR](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html)
- [RDS encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html)
- [Private RDS access](https://docs.aws.amazon.com/AmazonRDS/latest/gettingstartedguide/security-public-private.html)
- [RDS IAM database authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)
- [RDS and Secrets Manager](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html)
- [Encrypted snapshot sharing constraints](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/share-encrypted-snapshot.html)
- [RDS RestoreDBInstanceToPointInTime API](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_RestoreDBInstanceToPointInTime.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- `docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md`
- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/ADR/0011-context4-backup-restore-drill.md`
