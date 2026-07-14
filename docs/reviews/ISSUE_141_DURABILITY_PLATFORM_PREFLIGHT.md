# Issue #141 Durability Platform and Ownership Preflight

## Scope and stop rule

Issue `#141` chooses and documents the production-like durability platform and
ownership model. It may change ADR/governance documentation and executable
documentation guardrails only. It must stop before credentials, cloud resources,
IaC, database connections, backups, catalogs, restore tooling, metrics emitters,
or a restore exercise are created.

No successful production-like durability or restore claim is permitted. Issue
`#126`, matrix row `DUR-RESTORE-001`, and issue `#39` remain open.

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
- AWS documentation supports immutable S3 Version IDs and Object Lock governance
  retention. The proposed source/restore/control buckets and deletion journal are
  architecture only; no bucket or object evidence exists.

## Invariant and acceptance matrix

| ID | Required proof in this issue | Negative/old-behavior test | Human-only surface |
|---|---|---|---|
| `PLAT-DEC-001` | RDS PostgreSQL 17.10, Multi-AZ, `ap-south-1`, private source boundary. | Remove provider/version/topology marker; docs gate fails. | Region, cost and account approval. |
| `PLAT-SCOPE-001` | Stage 4/6/7 PostgreSQL entity and S3 versioned-byte inventory. | Remove ownership marker; docs gate fails. | Data-class/legal review. |
| `PLAT-BACKUP-001` | 14-day RDS PITR/S3-version mechanism and catalog schema/owner. | Replace immutable timestamp/Version ID or owner; docs gate fails. | Platform owner assignment. |
| `PLAT-ISOLATION-001` | Restore VPC/subnet/SG/IAM/DNS/identifier inequality, inherited storage-CMK disclosure, and source deny. | Any runtime/IaC path on this branch is rejected. | Security same-account/shared-key exception. |
| `PLAT-ACCESS-001` | SSO/MFA/OIDC/IAM DB auth/Secrets Manager/CMK/TLS boundaries. | Remove access-control marker; docs gate fails. | Security approval. |
| `PLAT-RETENTION-001` | Backup/version/target/evidence retention, independent deletion journal, and CH-14/CH-21 split. | Remove journal/acyclic ownership marker; docs gate fails. | Security/privacy disposition. |
| `PLAT-SLO-001` | Planned RTO/RPO owners and timestamp/watermark formulas; negative deltas invalidate evidence. | Result/achieved/verified claims fail the anti-overclaim guardrail. | Business threshold and Operations risk acceptance. |
| `PLAT-DEPS-001` | Dependency and acceptance table for issues `#142`-`#149`. | Remove any child marker; docs gate fails. | Per-child reviewer approvals. |
| `PLAT-OVERCLAIM-001` | Explicit no-environment/no-backup/no-restore evidence boundary. | Mutated production-like/closure claims fail focused tests. | Actual environment inspection later. |
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

Every material fix receives focused regression and docs-contract re-review.

## Evidence plan

The RED test is the issue `#141` focused docs suite before ADR/guardrail support.
GREEN evidence is the focused suite, repository guardrails, and `make quality`.
The issue comment at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4968602415>
records this pre-implementation plan. The correction at
<https://github.com/imrohitagrawal/narratwin-ai/issues/141#issuecomment-4968788598>
supersedes its target-KMS assumption and records the S3/journal/RPO/child-issue
handoffs. A draft PR uses reference-only `Refs #141` wording and may not close
any issue.
