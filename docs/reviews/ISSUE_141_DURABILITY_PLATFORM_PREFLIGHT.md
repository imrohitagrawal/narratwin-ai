# Issue #141 Durability Platform and Ownership Preflight

## Scope and stop rule

Issue `#141` chooses and documents the production-like durability platform and
ownership model. It may change ADR/governance documentation and executable
documentation guardrails only. It must stop before credentials, cloud resources,
IaC, database connections, backups, catalogs, restore tooling, metrics emitters,
or a restore exercise are created.

No successful production-like durability or restore claim is permitted. Issue
`#126`, matrix row `DUR-RESTORE-001`, and issue `#39` remain open.

AWS is the selected production-like evidence platform, not a prerequisite for
local development or the controlled local mock demo. `docs/LAUNCH_LEVELS.md`
owns the canonical launch-level boundary. Issue `#141` authorizes no AWS spend
or resource creation; issue `#144` is the first possible provisioning gate after
the recorded human decisions. A free or low-cost hosted resource may be assessed
for an internal synthetic demo, but it is not production-like evidence merely
because it is hosted or PostgreSQL-compatible.

## Source facts

- Current runtime state is in-memory or optional local JSON; Compose PostgreSQL
  is local developer infrastructure and cannot be cloud evidence.
- ADR `0008` selects PostgreSQL but did not select provider, topology, account,
  region, engine patch, or Stage 6/7 ownership.
- ADR `0011` contains planning targets but no configured backup, isolated target,
  catalog, or observed RTO/RPO.
- AWS documentation supports RDS PostgreSQL 17.10, Multi-AZ standby replication,
  automated-backup PITR, private VPC access, KMS encryption, IAM DB auth, and
  Secrets Manager integration. Cross-account encrypted snapshots require
  explicit sharing/copy operations and are not direct cross-account PITR.
- AWS PITR creates a new target DB identifier and otherwise defaults to
  service-selected/single-AZ/default network and parameter settings unless the
  restore request overrides them. IAM DB authentication also defaults off, and
  the API has no `EngineVersion` input. Issue `#144` therefore creates the
  landing zone/template; the later drill sets IAM auth and other supported
  inputs, then verifies the actual engine/configuration after target creation.
- AWS documentation supports immutable S3 Version IDs and Object Lock governance
  retention, but a locked version can still be masked by a new version or delete
  marker. The journal therefore requires unique write-once keys, version-aware
  enumeration, contiguous sequence/gap detection and an integrity manifest.
- AWS can force an RDS minor upgrade for critical security or end-of-support
  reasons even when automatic minor upgrades are disabled; version drift
  invalidates readiness until re-baselined.
- AWS exact-version single-request copy needs source `GetObjectVersion`/KMS
  decrypt and destination put/data-key permissions and is conservatively limited
  to exactly `5,000,000,000 bytes`;
  larger objects require a separate multipart IAM/KMS/abort-cleanup contract.
- RDS deletion must explicitly skip a final snapshot and delete automated
  backups, followed by inventory proof, to avoid retaining target-created state.
- Fixed destination tags use scoped `s3:PutObjectTagging`; a distinct cleanup
  role gets only target RDS describe/modify/delete and restore-bucket version
  list/tag-read/version-delete actions, with immutable source/control denies.
- GitHub OIDC trust must restrict audience and repository/environment subject;
  because an environment subject alone does not distinguish a PR job, the
  environment must allow only `main`, exclude PR refs, prevent self-review and
  bypass, and bind the exact reviewed deployment workflow/job.
- The proposed source/restore/control buckets and deletion journal are
  architecture only; no bucket or object evidence exists.

## Invariant and acceptance matrix

| ID | Required proof in this issue | Negative/old-behavior test | Human-only surface |
|---|---|---|---|
| `PLAT-DEC-001` | RDS PostgreSQL 17.10, Multi-AZ, `ap-south-1`, private source boundary. | Remove provider/version/topology marker; docs gate fails. | Region, cost and account approval. |
| `PLAT-SCOPE-001` | Exact Stage 4/6/7 PostgreSQL entity and S3 versioned-byte inventory. | Delete any complete Stage row; structural docs gate fails. | Data-class/legal review. |
| `PLAT-BACKUP-001` | 14-day RDS PITR, 15-day S3-version mechanism, restricted catalog/reviewer export and owner. | Replace immutable timestamp/Version ID, remove evidence separation or owner; docs gate fails. | Platform owner assignment. |
| `PLAT-ISOLATION-001` | Landing zone; PITR target with supported explicit parameters, IAM-auth input and post-create engine/config verification; inherited storage-CMK disclosure; source deny; pre-create deadline and separately scoped RDS/S3 cleanup authority. | Service defaults, impossible engine input, late/discretionary cleanup, missing final-snapshot/backup deletion, missing cleanup action or runtime/IaC on this branch fails. | Security same-account/shared-key exception. |
| `PLAT-ACCESS-001` | SSO/MFA, exact OIDC workflow/environment/branch/job trust, bounded single-copy S3/KMS permissions, private validator, IAM DB auth/Secrets Manager/CMK/TLS boundaries. | Remove any trust/permission/network/copy-limit marker; detailed docs gate fails. | Security approval and live policy inspection. |
| `PLAT-RETENTION-001` | Backup/version/target/evidence retention, contiguous integrity-linked and separately signed journal manifest, cleanup/inventory escalation, CH-17 revocation and CH-14/CH-21 split. | Remove journal/signing/break-glass/inventory fields or CH-17 dependency; structural docs gate fails. | Security/privacy disposition. |
| `PLAT-SLO-001` | Planned RTO/RPO owners, live target controls in the restore-ready boundary and version-written immutable source cutoff; negative/mismatched deltas invalidate evidence. | Reduced readiness, moving cutoff, discretionary cleanup and result/achieved/verified claims fail focused guardrails. | Business threshold and Operations risk acceptance. |
| `PLAT-DEPS-001` | Exact affirmative dependency and acceptance table for issues `#142`-`#149`, including tested `#130`/CH-12 routes before `#149` Go. | Delete/negate a row, mutate a dependency set or remove route severity/ack/escalation/runbook evidence; structural docs gate fails. | Per-child reviewer approvals. |
| `PLAT-OVERCLAIM-001` | Explicit no-environment/no-backup/no-restore/launch evidence boundary. | Contradictory platform, approval, Go/launch and closure claims fail; truthful negations pass. | Actual environment inspection later. |
| `HUMAN-PLAT-001` | Blocker list and named role responsibilities. | Remove blocked marker; docs gate fails. | AWS account/budget/region/owner assignments and independent Security decision. |

`HUMAN-PLAT-001` remains blocked: the payer/account IDs, budget authority,
region/data-residency approval, Operations owner, Platform/Storage owner,
independent Security reviewer, same-account restore exception, GitHub environment
approvers, and live service quota/version evidence are not present in the repo.

## Review protocol

- Operations: attack runbook ownership, RTO clock boundaries, smoke readiness,
  cleanup/TTL, and residual-risk acceptance.
- Platform/Storage: attack RDS version/topology, account/region, backup/PITR,
  catalog, KMS, capacity, RPO watermark, and source/target inequality.
- Security: attack private networking, IAM/SSO/OIDC, secret rotation, KMS policy,
  same-account exception, retention/redaction, and source mutation denies.
- Fresh-context adversarial review: look for missing entities, cyclic CH-14/CH-21
  dependencies, evidence stealing from `#142`-`#149`, and language that could be
  read as an actual deployed/verified durability claim.

Every material fix receives focused regression and docs-contract re-review. The
second independent review loop is registered at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4970335301>
under IDs `REV141-JOURNAL-001` through `REV141-LAUNCH-001`. Five angles requested
changes, so the stop rule paused publication for contract/test rewrite before
another review loop.
Wave 1 of the next independent review at commit `3b0a3e0` is registered at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4970564802>
under IDs `REV141-OIDC-002` through `REV141-SIGN-002`. Platform, Security and
Operations each requested changes, so another RED-to-GREEN loop is required
before the six-angle final review.

## Evidence plan

The RED test is the issue `#141` focused docs suite before ADR/guardrail support.
GREEN evidence is the focused suite, repository guardrails, and `make quality`.
Remediation loop 2 RED evidence is nine focused failures proving missing Stage
and child rows, dependency drift, journal-field loss, contradictory platform and
launch approval claims, and a truthful-negation false positive before checker
changes.
Remediation loop 3 RED evidence is 17 focused failures proving that OIDC,
copy-IAM, private-network, evidence separation, journal/break-glass, STRIDE,
PITR-default, reduced-RTO, moving-cutoff, cleanup, CH-12 and `#139`/`#141`
closure regressions could bypass the prior checker.
Final guardrail review additionally demonstrated negated dependency and
adversarial negation lead-in false passes; final Operations review demonstrated
that CH-12 routing was named but not a Go prerequisite. Affirmative dependency
grammar, proposition-bound negation, and explicit `#130` route evidence close
those gaps.
The issue comment at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4968602415>
records this pre-implementation plan. The correction at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4968788598>
supersedes its target-KMS assumption and records the S3/journal/RPO/child-issue
handoffs. A draft PR uses reference-only `Refs #141` wording and may not close
any issue.
