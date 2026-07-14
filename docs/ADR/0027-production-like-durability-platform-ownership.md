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

The selected AWS boundary applies to production-like durability validation and
eventual production, not to every way of running or presenting the product. AWS
is not required for local development or the controlled local mock demo, and no
AWS payer/account decision may block those local paths. The canonical audience,
data, infrastructure, claim, and Go/No-Go demarcations are in
`docs/LAUNCH_LEVELS.md`. A hosted internal demo needs its own environment review;
an external/invite-only soft launch is production-adjacent; neither inherits
local-demo approval. This clarification does not change the selected AWS
production-like baseline or authorize spend, provisioning, launch, or restore.

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
control bucket stores the sanitized backup catalog, evidence, and unique-key,
integrity-linked deletion journal; it is never an application artifact bucket.

Production-like and eventual production deployments may differ in instance
class, storage allocation, autoscaling limits, and synthetic data volume. They
must not differ in the reviewed engine major/minor baseline, Multi-AZ posture,
private networking, TLS enforcement, customer-managed KMS encryption, RDS
backup/PITR, S3 Versioning/noncurrent retention, source/target/control bucket
separation, IAM boundaries, secret rotation, audit/monitoring controls, or
source deletion protection. `AutoMinorVersionUpgrade` is disabled and verified
through IaC plus the live RDS API for the source and every restored target.
AWS can still force a minor upgrade for critical security or end-of-support
reasons. Any observed version drift immediately invalidates parity/readiness
evidence until compatibility tests pass and a reviewed ADR amendment
re-baselines the source, restore template, validator, and runbook.

### Environment, account, and region boundaries

| Boundary | Contract |
|---|---|
| Local/dev/test | Docker PostgreSQL 17, in-memory state, and optional JSON state are developer evidence only and cannot prove this ADR is deployed. Paid providers remain disabled. |
| Pre-production source | Dedicated non-production AWS account, `ap-south-1`, private source VPC and source artifact bucket, synthetic data only, no public or production traffic. |
| Restore validation | Same non-production account and region, but a pre-provisioned landing zone containing a dedicated restore VPC, subnet and parameter groups, security groups, IAM roles, DNS namespace, restore artifact bucket, private endpoints, and required `narratwin:environment=restore-validation` tags. No target DB exists before the later drill: direct RDS PITR creates a new target identifier and inherits the source storage CMK; that shared-key residual requires Security approval. |
| Production | A separate production AWS account is required before Go. This ADR neither provisions nor approves it. No production data may be copied into pre-production. |

The restore target uses the same account/region for direct RDS point-in-time
restore. The RDS point-in-time API has no target storage `KmsKeyId` parameter, so
the restored instance inherits the source storage CMK. Cross-account or
re-encrypted snapshot restore requires manual KMS/snapshot sharing or copying,
which changes the direct PITR path. The same-account/shared-key target is
therefore a deliberate exception that requires independent Security approval
before issue `#144`; without that approval, `#144` must redesign the target and
re-baseline RPO assumptions.

Issue `#144` provisions the source and isolated restore landing zone, not a
placeholder DB instance. The later `RestoreDBInstanceToPointInTime` call creates
a new target DB identifier. Before submission, automation verifies the source
and approved baseline both report engine version `17.10`; the PITR API has no
`EngineVersion` input. The request explicitly selects `MultiAZ=true`,
`PubliclyAccessible=false`, `EnableIAMDatabaseAuthentication=true`, the restore
subnet group, restore security groups, restore parameter group, restore tags,
deletion protection, and the reviewed automatic-minor-upgrade setting rather
than accepting service defaults. TLS is enforced by the selected parameter
group. After creation, platform APIs must prove engine version `17.10`,
Multi-AZ, private accessibility, IAM database authentication, the exact
network/parameter/tag configuration, deletion protection, and no traffic path;
any mismatch or forced engine drift invalidates readiness. The created target
must have a distinct VPC ID, DB subnet group, security-group IDs, IAM restore
role, DB identifier/ARN, and DNS suffix from the source. The catalog records
that the storage KMS ARN is inherited rather than falsely asserting key
inequality. The target never receives application or user traffic. Automation
compares source and target identifiers before mutation, allows only the target
through an explicit allowlist, and denies source DB/KMS/network mutation even
when tags drift.

### Durable-state ownership for Stages 4, 6, and 7

| Stage | Authoritative durable state | Deliberately excluded from recovery scope |
|---|---|---|
| Stage 4 | PostgreSQL: projects; document identity/approval/normalized text; ingestion runs; chunks and embeddings/version metadata; retrieval context; walkthrough/generated-script state; claim/evaluation/citation evidence; idempotency, leases, outbox, audit, migration, ownership and transitions. S3: approved original upload version. PostgreSQL binds every object Version ID/checksum. | Rejected/unvalidated upload bytes, prompt scratchpads, provider wire payloads, caches, temporary parsing files, local JSON snapshots, secrets. |
| Stage 6 | PostgreSQL: translation/voice run, translated script/subtitle text, voice manifest, provider/fallback metadata, request dedupe/idempotency and source/evaluation/provenance linkage. S3: generated audio/downloadable artifact versions. PostgreSQL binds every object Version ID/checksum/class. | Raw provider responses, transient transcripts, provider caches, secrets, temporary work files. |
| Stage 7 | PostgreSQL: synthetic-media consent/idempotency, render request/result/status history, provider metadata, disclosure/provenance/source/evaluation/consent bindings and render idempotency. S3: render/export artifact versions. PostgreSQL binds every object Version ID/checksum/class. | Raw provider responses, cloned-identity material, transient work files, secrets, local previews not accepted as artifacts. |

Content restored from these data classes remains untrusted. Restore validation
must re-run schema, scope, checksum, consent, provenance, prompt-injection, and
retrieval-poisoning checks before replay or export.

Publishing an accepted artifact across PostgreSQL and S3 follows an explicit
non-atomic compensation contract. The adapter first writes a unique immutable
S3 object key, captures its Version ID, reads that exact version back, and
verifies its SHA-256. Only then may a PostgreSQL transaction publish a `ready`
reference to that exact bucket class/key/Version ID/checksum. If the database
transaction fails, the unreferenced version is quarantined as an orphan with a
bounded cleanup deadline; it is never exposed as ready. Retrying the same
operation is idempotent for the same operation identity and checksum and fails
closed on a different checksum. Garbage collection proves that no committed
row references a version before deleting it. Missing, inaccessible, mutable-
alias, wrong-version, or checksum-mismatched objects block replay/export.
Before the object write, a durable publication-intent record binds the operation
identity, immutable object key and cleanup deadline. Scheduled reconciliation
discovers incomplete intents and matching unreferenced versions, including a
process crash after object verification but before PostgreSQL publication or
quarantine; it either completes the same verified publication or quarantines
and safely cleans the orphan. Issue `#143` owns failure tests for S3-success/
database-failure, database retry, crash-window discovery, checksum failure,
unavailable object, bounded orphan reconciliation/cleanup, and referenced-
version protection.

The Application/Data owner (`@imrohitagrawal` for the current repository) owns
the logical Stage 4/6/7 schema, write invariants, committed deletion-event
sequence, and completeness of consent and provenance references.
Platform/Storage owns the physical PostgreSQL and S3 services, journal delivery
and reconciliation, capacity, availability, recovery configuration and catalog.
Operations owns journal backlog alert response, recovery execution, and the
decision that a validated target is operationally ready. Security/Privacy owns
consent, provenance, retention and erasure policy and independently reviews
their schema and restored behavior. This separates business meaning from
physical custody and recovery execution.

### Backup mechanism and artifact catalog

The baseline mechanism is RDS automated backups with continuous transaction-log
capture and point-in-time restore, configured for `14 days` retention. A drill
must select an immutable UTC restore timestamp; mutable `latest` is prohibited.
Manual drill snapshots may be used for portability evidence but are not a
substitute for PITR and must follow the same deletion rules.

S3 recovery uses Versioning plus unique artifact keys and a lifecycle rule that
retains noncurrent source artifact versions for at least `15 days`, one day
longer than the RDS recovery window. Each PostgreSQL artifact row selects
an immutable S3 Version ID and checksum, so the database recovery point also
selects exact artifact bytes. The restore procedure copies those exact versions
to the isolated restore bucket and validates checksums; reading an unversioned
key or mutable current version is prohibited. Versioning is not represented as
a separate database backup, and its configuration/evidence belongs in the same
catalog and readiness review.

The security-control bucket uses Versioning and S3 Object Lock governance mode
for the restricted catalog, reviewer evidence exports, and deletion journal.
Object Lock protects a retained object version but does not prevent a new
version or delete marker from becoming current, so the journal never treats a
mutable current key or a bucket listing without version checks as authoritative.
Each committed deletion event uses a unique write-once key containing its opaque
scope, monotonic outbox sequence, and event ID. The journal writer has create-
only permissions and cannot overwrite, call `DeleteObject`, delete a version,
shorten retention, or bypass governance mode.

For each scope, the journal records the monotonic sequence, previous-event
digest, event checksum, policy version, deletion time, opaque entity/object
identities, and confirmed S3 Version ID. An idempotent retry of the same
event/key/checksum is accepted; a duplicate sequence, reused key, checksum
change, gap, out-of-order event, missing retention, delete marker, inaccessible
version, or hash-chain mismatch fails closed. The authoritative high-watermark
is the last contiguous, version-verified sequence—not the largest observed
sequence. A signed/versioned manifest binds that watermark, ordered event
digests, and evidence checksum. A dedicated Security-owned manifest-signing
principal uses a separate asymmetric KMS signing key and has no journal-write,
reconciliation, retention-bypass, or catalog-mutation permission. The journal
writer and reconciler cannot sign. Verification pins the signing-key ARN,
algorithm, manifest policy version and prior signed watermark; a missing,
invalid, unexpected-key, or rolled-back signature fails closed. A deletion is
not acknowledged as complete
until the committed PostgreSQL outbox event is version-verified in the journal.
The journal contains no content or direct user attributes and is not rolled back
with RDS PITR.

Application/Data owns monotonic sequence creation in the committed outbox.
Platform/Storage owns idempotent journal delivery, gap-free reconciliation,
retention verification, backlog age and high-watermark health. Operations owns
alert acknowledgment and escalation for stalled delivery, gaps, KMS access loss,
delete markers, or reconciliation failure. Only the independently approved
Security/Privacy break-glass role can bypass governance retention; every use is
alerted, dated, and reviewed. Control-key disablement/deletion safeguards and
alarms are mandatory.

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
- deletion-journal last-contiguous sequence, manifest Version ID, previous/event
  digests, retention state, reconciliation time and checksum used for the
  re-delete handoff;
- evidence SHA-256, creation/verification timestamps, owner and reviewer;
- target DB resource ID/ARN after restore and teardown outcome.

The restricted operational catalog may contain the minimum resource identities,
Version IDs and opaque scope mappings required to recover and reconcile. It is
not reviewer-facing evidence. Reviewer exports use a field allowlist, keyed
pseudonyms or opaque one-time mappings, minimum necessary timestamps/statuses,
separate read roles and access audit. Predictable hashes are not anonymous.
Neither surface may contain connection strings, credentials, tokens, document
text, provider payloads, direct user attributes, or customer content. Security/
Privacy approves classification, maximum retention, legal basis, mapping-key
custody, and CH-21 deletion behavior for both surfaces.

### Access control and secrets

- Humans use AWS IAM Identity Center, MFA, short-lived role sessions, and
  least-privilege separation between platform deployer, restore operator,
  catalog reader, security auditor, and break-glass administrator.
- The future deployment workflow identity is exactly
  `.github/workflows/durability-deploy.yml@refs/heads/main`. Only its deployment
  job references the `production-like-durability` environment and receives
  `id-token: write`; all other jobs and workflows have no token permission.
  Repository branch protection and CODEOWNERS require reviewed changes to that
  workflow before it reaches `main`.
- GitHub deployment uses environment-protected OIDC federation with
  `aud=sts.amazonaws.com` and the exact trust subject
  `repo:imrohitagrawal/narratwin-ai:environment:production-like-durability`.
  AWS trust accepts only those exact `aud` and `sub` values; no wildcard subject
  is allowed. The GitHub environment permits deployment only from
  `refs/heads/main`, explicitly excludes `refs/pull/*/merge` and tags, requires
  named approvers, prevents self-review, and disallows administrator bypass.
  Consequently a PR job cannot qualify merely by naming the environment. Issue
  `#144` must inspect the live token claims, workflow identity, branch policy,
  environment rules and IAM trust before apply; this ADR does not claim they
  exist. Pull-request workflows, forks, untrusted refs, and jobs without the
  protected environment cannot assume cloud roles. Static AWS keys are
  forbidden in GitHub, repository files, CI artifacts, and local examples.
- The workload identity receives only its application database secret and
  network path plus scoped source-artifact object permissions. The RDS master
  secret is RDS-managed in Secrets Manager, rotated, excluded from application
  access, and reserved for audited break-glass.
- Operators use RDS IAM database authentication with short-lived tokens. Workload
  credentials are Secrets Manager-managed and rotated; no secret is placed in
  backup catalogs or restore evidence.
- TLS certificate verification and `rds.force_ssl=1` are mandatory. Database
  roles are migration, application, read-only validation, and audited break-glass.
- The restore operator can create and inspect restore-validation resources. For
  exact-version artifact copying, the accepted recovery contract is a single
  `CopyObject` request for an object no larger than `5,000,000,000 bytes` (the
  conservative contract value for the service's 5-GB single-copy ceiling);
  larger objects fail preflight before any copy until a separate multipart-copy
  IAM, KMS and abort-cleanup contract is approved. The operator receives only source
  `s3:GetObjectVersion` and source-key `kms:Decrypt`, restricted to the source
  bucket prefix, cataloged manifest and expected encryption context, plus
  destination `s3:PutObject`, `s3:PutObjectTagging` for the fixed run/deadline
  tag set, and restore-key `kms:GenerateDataKey`. It cannot
  read mutable aliases, administer either key, manage buckets, mutate the
  source, delete versions, or access the control journal beyond its sanitized
  manifest input. The workload role has no restore/control-bucket access.
- A separate ephemeral validator runs through an audited private access channel.
  PostgreSQL ingress accepts only its security group. The restore VPC has no
  internet/NAT, source-VPC, application, provider, or production connectivity;
  narrowly scoped private AWS endpoints are the only egress. The validator role
  expires after the exercise and cannot change infrastructure or source state.
- The restore operator has explicit deny controls for source DB, source KMS key
  administration, source VPC, backup retention changes, source/control S3
  mutation, Object Lock bypass, and source deletion-protection removal. A
  separate target-cleanup role may remove deletion protection only from the
  cataloged restore target after evidence capture and dated Operations approval.
  On the run-tagged target ARN it receives only `rds:DescribeDBInstances`,
  `rds:ModifyDBInstance`, and `rds:DeleteDBInstance`; post-delete inventory uses
  `rds:DescribeDBSnapshots` and `rds:DescribeDBInstanceAutomatedBackups`, with
  `rds:DeleteDBSnapshot` or `rds:DeleteDBInstanceAutomatedBackup` only for a
  run-tagged orphan that the exact teardown should have removed. On the restore
  bucket/run prefix it receives `s3:ListBucketVersions`,
  `s3:GetObjectVersionTagging`, and `s3:DeleteObjectVersion`. It cannot put/read
  object content, change tags, bypass retention, administer KMS/buckets, or act
  on source/control buckets. Immutable source DB, source/control bucket and KMS
  ARN denies apply independently of tags; tags narrow the target allowlist but
  never authorize a source action.

### Retention, encryption, and integrity

| Data/evidence | Requirement |
|---|---|
| Automated backups/PITR logs | 14 days. Platform configures and proves the window; Security approves any change. |
| S3 source artifact versions | S3 Versioning enabled with unique keys; current and noncurrent versions recoverable for at least 15 days. Permanent version deletion is denied to application and restore roles. |
| Manual drill snapshot | Delete after accepted evidence or within 14 days, whichever is earlier. |
| Restore DB and artifact bucket | Persist the attempt and `cleanup_due_utc` before the create request, then tag the request/target and every copied object with the run ID and deadline immediately on API acceptance. Automatically tear down the target/delete copied versions within 24 hours even after timeout, partial restore/copy, or catalog-write failure. RDS deletion uses `SkipFinalSnapshot=true` and `DeleteAutomatedBackups=true`; post-delete evidence proves the DB, target-created snapshots, retained automated backups, copied versions and incomplete work are absent. A hard maximum 72 hours requires a dated Security and Operations exception with owner and reason. Scheduled catalog plus tag-based live-inventory discovery retries cleanup and alerts Operations and Platform on overdue/orphan state. The next exercise is blocked until both catalog and live inventory prove cleanup. |
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
S3 Version ID/checksum parity, last-contiguous deletion-journal high-watermark,
journal-derived handoff persistence, and evidence SHA-256. A service status of
`available` is necessary but not sufficient for integrity or readiness.

Issues `#143` and `#144` establish the journal writer/control bucket before
CH-14: the application outbox produces deletion events and the independent
control bucket preserves the current ledger outside RDS PITR. CH-14 owns backup
configuration, catalog lifecycle, restore-target TTL, restore measurement, and
the handoff obtained by comparing restored IDs/object versions against that
current journal. CH-21 owns data-class erasure policy, permanent deletion across
primary/backups/restores, audit exceptions, and proof that handed-off restored
records/objects are re-deleted. CH-17 supplies current consent-revocation and
takedown state to CH-21; restored consent/render/export state remains disabled
until that current source and the deletion journal are reconciled. CH-14 must
validate and emit the handoff but does not claim CH-21 behavior proof,
preserving the dependency direction from CH-14 to CH-21 without deriving
tombstones from the rolled-back database.

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
  only after DB availability, migration compatibility, database integrity,
  exact S3 Version-ID copy/checksum parity, last-contiguous journal validation,
  persisted re-delete/revocation handoff, replay-safe smoke checks, and live API
  proof of Multi-AZ, private/network/parameter/tag configuration, IAM database
  authentication, engine version `17.10`, deletion protection and no-traffic
  isolation pass.
  Drill-declared, holdpoint-entered/exited, API-submitted, API-accepted, and
  DB-available timestamps are retained as diagnostic sub-intervals; they do not
  shorten the end-to-end RTO clock.
- Observed RPO is
  `source_cutoff_watermark_utc - latest_restored_commit_watermark_utc`. At the
  reviewed holdpoint and before any recovery action, the operator freezes the
  scoped synthetic writer or records the incident/recovery-decision cutoff, then
  version-writes and checksum-verifies that immutable source cutoff in the
  security-control catalog before recovery begins, together with database-server
  UTC, monotonic commit sequence, seed-manifest digest and catalog/run ID. The restored watermark must
  use the same manifest and sequence domain. A moving post-start source query,
  negative delta, target-ahead sequence, clock ambiguity, cutoff mismatch, or
  manifest mismatch invalidates the evidence; it is never clamped to zero. RDS
  backup lag and earliest/latest restorable time are diagnostics, not RPO proof.
- Issue `#148` owns durable metric/event export; issue `#147` owns the runbook
  timestamps; issue `#149` reviews only environment, tooling, calculation-test,
  and reviewer-handoff readiness. Actual RTO/RPO results belong to the later
  issue `#126` exercise. No measurement may be claimed until that exercise exists.

### Ownership and required review

| Role | Accountable responsibility | Required acceptance evidence |
|---|---|---|
| Repository/business owner (`@imrohitagrawal`) | Issue/PR governance; RTO/RPO thresholds; proposed budget and risk disposition. AWS payer/cost authority remains unverified. | Dated issue comment and PR approval. |
| Application/Data owner (`@imrohitagrawal`) | Logical Stage 4/6/7 entity schema, relationship/write invariants, consent/provenance reference completeness and adapter acceptance. | Schema/adapter PR review and validator acceptance. |
| Operations owner (unassigned human blocker) | Runbook, restore execution, RTO, journal/cleanup alert response, smoke acceptance, cleanup escalation and operational residual risk. | Named owner/on-call substitute and escalation route, runbook approval, exercise signoff. |
| Platform/Storage owner (unassigned human blocker) | Account/IaC, restore landing zone, RDS/S3/KMS/networking, journal delivery/reconciliation, backups/version retention, artifact catalog, cleanup automation, capacity and RPO. | Named owner comment, architecture/IaC approval, catalog/evidence signoff. |
| Independent Security/Privacy reviewer (unassigned human blocker) | IAM, Secrets Manager, KMS, network isolation, consent/provenance/retention/erasure policy, redaction and same-account exception. | Independent PR approval and dated exception/denial comment. |

Documentation is not a human signoff. Issue `#149` aggregates these approvals;
each child issue must also obtain its role-specific approvals before closeout.

### Dependencies and acceptance for issues #142-#149

| Issue | Dependencies | Acceptance owned by that issue |
|---|---|---|
| `#142` connection-backed PostgreSQL and migrations | `#141` approved baseline and named Platform owner | Real connection-backed adapter and migrations; fail-closed startup/config; no file-backed success path; migration/restart evidence on PostgreSQL 17.10. No cloud provisioning. |
| `#143` Stage 4/6/7 durable adapters | `#141`, `#142` | In-scope business entities use PostgreSQL; approved bytes use the S3-version-first publication/compensation contract with durable intent and crash-window reconciliation; committed deletion outbox delivers a unique, contiguous, integrity-linked journal event before deletion completion; restart/replay/CAS/idempotency/lease/outbox, locator/checksum, orphan/retry/unavailable-object, journal gap/duplicate/out-of-order and untrusted-input tests pass. |
| `#144` pre-production source and isolated restore landing-zone IaC | `#141`; Security approval of same-account/shared-RDS-key exception | Reproducible private Multi-AZ RDS 17.10 source plus restore VPC/subnet/parameter/SG/DNS/private-endpoint template and distinct source/restore/control S3 buckets; exact workflow/environment/OIDC restrictions, IAM/KMS/network isolation, source denies and target-creation parameter evidence including IAM DB authentication and baseline/post-create engine verification. No pre-created target DB and no drill. |
| `#145` backup and artifact catalog | `#141`, `#144` | 14-day RDS PITR and at least 15-day S3 noncurrent-version retention configured; immutable DB time/object Version IDs selected; unique-key/version-aware journal, Object Lock retention, separately signed integrity manifest and rollback anchor, control-key safeguards, restricted catalog/reviewer-export split and KMS/access/status evidence complete. No restore execution. |
| `#146` synthetic seed and validator | `#141`, `#143`, `#144`, `#145` | Versioned synthetic Stage 4/6/7 graph and live test S3 objects, at least one contiguous integrity-linked deletion-journal event, immutable source cutoff/server UTC/commit sequence, expected counts/checksums/relationships and negative corruption cases in the selected landing zone. |
| `#147` restore runbook and safety controls | `#144`, `#145`, `#146` | Executable but not yet executed runbook whose later `#126` invocation creates a new RDS target with explicit Multi-AZ/private/network/parameter/tag/IAM-auth settings, pre/post engine verification, and no service defaults; exact single-copy `<=5,000,000,000 bytes` S3 Version ID copies; target allowlist/source deny; journal/revocation-derived handoff; pre-create cleanup deadline, tag discovery, `SkipFinalSnapshot=true`/`DeleteAutomatedBackups=true`, separately scoped RDS/S3 target-cleanup/live-inventory actions; restore/cleanup/journal failure severity, owner/ack/escalation and runbook-link handoff to CH-12; 24/72-hour escalation and next-exercise live-inventory block; RTO/RPO holdpoints. |
| `#148` restore observability and evidence export | `#130`, `#141`, `#144`, `#145`, `#146`, `#147`; metric names aligned with CH-10/CH-11 and alert routing owned by CH-12 | RDS/S3 restore, live target-configuration/isolation, backup/version, contiguous catalog/journal, cleanup-deadline/orphan/live-inventory and KMS-access events/metrics; tested CH-12 route handoff for restore timeout/failure, cleanup overdue/orphan, journal gap/backlog/signature failure and KMS loss with severity, owner acknowledgment/escalation and runbook links; restricted-catalog to allowlisted reviewer export; immutable-cutoff/negative-delta-invalidating RTO/RPO calculation tests. No successful-drill claim. |
| `#149` production-like restore readiness review | `#130`, `#141` through `#148` | Verify actual environment, backup/version sources, target, validator, runbook, calculation-test/fixture metrics, tested `#130`/CH-12 routes and independent approvals; record Go/No-Go for a later drill without actual RTO/RPO or restore-success claims. Must leave `#126`, `DUR-RESTORE-001`, and `#39` open. |

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
- [RDS DeleteDBInstance API](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DeleteDBInstance.html)
- [RDS engine upgrade behavior](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.Upgrading.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [S3 API permission mapping](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-policy-actions.html)
- [S3 CopyObject API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html)
- [AWS IAM OIDC role trust](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)
- [GitHub Actions OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)
- `docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md`
- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/ADR/0011-context4-backup-restore-drill.md`
