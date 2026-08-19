# ADR 0006: Stage 8 Release Hardening Gates

## Status

Accepted for Stage 8.

## Date

2026-07-01

## Context

Stage 8 moves NarraTwin AI from feature-slice implementation into
release-readiness hardening. The product still runs in local/mock mode, but the
review surface now includes performance budgets, request abuse controls,
dependency audits, Docker image scanning, frontend Lighthouse checks, and launch
evidence.

The Stage 8 review found that header-only request-size checks, caller-controlled
rate-limit keys, optional container scanning, and shallow performance smoke tests
would leave release risk hidden behind passing local unit tests.

## Decision

Stage 8 hardening is part of the architecture contract, not only test coverage.

- API write requests under `/api/v1/` require a valid non-negative
  `Content-Length` before body parsing; missing length fails with
  `411 CONTENT_LENGTH_REQUIRED`, malformed length fails with
  `400 INVALID_CONTENT_LENGTH`, oversized declared length fails with
  `413 REQUEST_TOO_LARGE`, and actual ASGI body bytes are counted so
  under-reported length cannot bypass the local budget.
- Local write rate limiting is keyed by client IP instead of caller-supplied
  headers, rejects over-budget writes with `429 RATE_LIMIT_EXCEEDED`, and bounds
  retained key state.
- Provider-bound walkthrough prompts and multilingual glossary terms get
  secret-like content screening before provider execution.
- Stage 4 and Stage 6 idempotency retains terminal semantic validation
  failures so exact request replays return the same failure and changed-body key
  reuse returns `IDEMPOTENCY_CONFLICT`; unexpected implementation exceptions
  still release the reservation.
- Stage 6 voice provider manifests are exact-schema validated before
  response/artifact exposure, including top-level and nested field rejection for
  unknown provider output.
- Performance smoke tests run both focused API latency tests and a headless
  Locust health-endpoint p95 budget check.
- Frontend Lighthouse checks enforce category scores and named audit budgets,
  including request count through the audit details table when no numeric value
  is provided by Lighthouse.
- Docker image scanning is required in the Stage 8 local gate and PR security
  workflow. The scan attempts local Trivy, Grype, pinned Dockerized Trivy, and
  Docker Scout per image. A confirmed critical/high SARIF report fails the gate;
  a scanner/tool failure without a usable SARIF report can fall through to the
  next scanner. Scanner exit codes are captured before fallback evaluation so a
  nonzero scan result with usable SARIF cannot be converted into a pass.
- PR CI emits a dedicated `stage8 / performance lighthouse` status when
  `.stage/current` is `8`, running the Locust and Lighthouse budget scripts
  outside the policy-only static quality job.
- Release checklist, runbook, status, traceability, skill lock, and third-party
  notices must remain consistent with the executable gates.

## Alternatives Considered

### Keep request-size checks on `Content-Length` only when present

Rejected. ASGI clients can send a body without that header, so fail-open behavior
would bypass the Stage 8 upload/request budget.

### Use caller-controlled local user headers for rate-limit identity

Rejected. It is acceptable for local demos to be unauthenticated, but rate-limit
identity must not be trivially rotated by changing a request header.

### Treat Docker scans as local-only evidence

Rejected. Stage 8 requires release-readiness evidence in PR CI, so the security
workflow must invoke the same image scan gate.

## Consequences

Positive:

- request budget enforcement fails closed
- local abuse controls are harder to bypass
- container vulnerability evidence is available in CI artifacts
- performance and Lighthouse checks measure concrete budgets, not just tool
  availability
- release reviewers have a single documented decision for Stage 8 hardening

Negative:

- clients that omit `Content-Length` on write requests must be fixed or routed
  through a supported upload path
- local rate limiting remains process-local and is not approved for multi-worker
  production deployment
- Dockerized Trivy introduces an additional third-party CI/tooling dependency
  that needs final release license review

## Phase 1 Closure Addendum For Issue #39

Date: 2026-07-03

Phase 1 Closure issue `#39` adds a local durability and monitoring remediation
without changing the production No-Go decision.

Decision:

- Stage 4, Stage 6, and Stage 7 services may opt into single-node JSON state
  snapshots through `NARRATWIN_STATE_DIR` or service-specific state-file
  variables.
- Persistence remains disabled by default for test isolation and unchanged local
  behavior.
- Snapshot writes use atomic local file replacement and may contain sensitive
  local data needed for restart recovery and idempotency replay: uploaded
  document text, chunks/context, generated scripts, evaluation details,
  translations/subtitles, avatar artifact payloads, base64 content, and
  metadata. These files must remain local and uncommitted.
- `GET /api/v1/ops/status` exposes local durability enablement, non-sensitive
  backend type, bounded record counts, and monitoring flags.
- The ops endpoint must not expose state-file paths, raw uploads, prompts,
  generated outputs, provider payloads, environment values, or secrets.

Consequences:

- Local/mock review can now demonstrate restart recovery for Stage 4 project,
  document, ingestion, walkthrough, RAG, and idempotency state; Stage 6
  multilingual idempotency replay; and Stage 7 avatar render, idempotency, and
  artifact metadata.
- JSON snapshots are not a production database. They do not provide ACID/CAS
  semantics, cross-worker locks, schema migrations, backup/restore policy, or
  production idempotency guarantees.
- Production go-live remains No-Go until a reviewed release phase adds
  production-grade durable metadata and deployment monitoring.

## Phase 1 Closure Addendum For Issue #55

Date: 2026-07-09

Issue `#55` is a follow-up triage issue for additional local restore-invariant
hardening discovered after PR `#54` merged. It remains under the issue `#39`
local-durability evidence scope and does not change the production No-Go
decision.

Decision:

- Stage 4 restore may prune RAG chunks whose restored payload no longer matches
  the owning document text and metadata, and may drop restored document,
  ingestion, walkthrough, evaluation, claim-support, and idempotency rows whose
  relationship graph no longer has the evidence needed to justify terminal
  state.
- Stage 6 restore may drop multilingual idempotency records whose restored
  derivative text, provider payload, artifacts, language tags, citations,
  glossary terms, or checksums no longer agree.
- Stage 7 restore may drop artifact metadata and terminal idempotency records
  that no longer match restored render artifacts, checksums, or serialized
  terminal error details.
- Stale-low counters must be derived from restored IDs, and failed-operation
  rollback must remain operation-scoped so it does not erase later successful
  operations.
- Stage 4 RAG chunk insertion must stage embedding/provider work for all
  prepared documents before mutating the in-memory chunk indexes or marking
  documents ingested, so an unexpected local embedding failure cannot leave
  partial orphan chunks behind the failed idempotent ingestion operation.
- Stage 4 failed-ingestion terminal-persist rollback must prune only RAG chunks
  introduced after the operation snapshot for the failed ingestion's documents,
  preserving prior and concurrent successful local chunks.
- Dead full-snapshot restore helpers should not remain available as alternate
  local rollback paths once operation-scoped rollback is the reviewed contract.

Consequences:

- Local restart-recovery evidence becomes stricter about restored graph and
  artifact consistency.
- Stage 4 local ingestion rollback now has direct single-document and
  multi-document evidence for all-or-nothing chunk insertion on unexpected
  local embedding failure while preserving operation-scoped rollback for
  concurrent successful writes, and direct evidence that a terminal local
  snapshot write failure removes failed-ingestion chunks without erasing
  concurrent successful ingestion chunks.
- Stage 4, Stage 6, and Stage 7 retain snapshot capture for operation-scoped
  rollback but no longer retain unused full-snapshot restore helpers that could
  reintroduce concurrent-success loss if reused later.
- Corrupt local snapshot rows may be pruned in memory and re-written on the
  next successful persist; this is still not a migration, backup, repair, or
  production recovery system.
- Production go-live remains No-Go until ACID/CAS durable metadata,
  cross-worker locking, migrations, backup/restore, production idempotency,
  dashboards/alerts, first-hour watch, and rollback communications are reviewed.

## Phase 1 Closure Security Addendum For Issue #138

Date: 2026-07-14

Issue `#138` remediates the Click command-injection advisory without removing
Semgrep coverage or placing an unsupported override in the application/runtime
dependency graph.

Decision:

- Semgrep is a security tool, not an application/runtime dependency. It runs
  from an exact, separately locked `tools/semgrep` project and isolated
  environment.
- The tool-only Click `8.3.3` and MCP `1.28.1` overrides are limited to
  Semgrep `1.168.0`, expire on `2026-08-13`, and require an accountable
  security/repository-owner decision before merge. MCP functionality is not
  started, exposed, or used by the repository scan.
- Tool version, full lock, rules, targets, invocation, canary configuration, and
  canary fixtures are hash-bound reviewed inputs. Any change invalidates the
  compatibility evidence and requires renewed review.
- Root and installed tool environments are audited separately without advisory
  ignores. Semgrep engine configuration validation, a zero-finding repository
  result validator, and a positive/clean execution canary fail independently.
- Backend image inventory is tied to the image just built and requires fixed
  Click with Semgrep absent.
- A passing first-scanner result is not evidence that a known confirmed image
  finding is absent. Issue `#151` owns the Trivy/Grype disagreement and three
  PSF-confirmed HIGH CPython findings; that risk blocks merge without being
  converted into a scanner waiver.
- Issue `#151` may use fixed-status scanner consensus only when the exact image
  digest, patch checksums, raw reports, and exploit regressions are all retained.

Consequences:

- Application/runtime Click can receive the fixed release independently of
  Semgrep's older declared constraints; MCP remains isolated security tooling,
  not an application/runtime dependency.
- The compatibility proof applies only to the committed, hash-bound Semgrep
  execution surface; other CLI paths are not approved.
- Security gates gain explicit false-green tests and installed-inventory proof.
- Issue `#138` remains open until human acceptance and post-merge verification;
  issue `#151` remains a separate merge blocker.
- This decision adds no production durability, backup/restore, RTO/RPO,
  monitoring, operator-signoff, or issue `#39` closure evidence.

## Issue #374 Frontend Runtime Image Addendum

Date: 2026-08-05

The frontend build stage uses official Node.js `26.6.0-alpine` pinned to index
digest `sha256:a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8`.
The standalone runtime uses the minimal Chainguard Node image pinned to index
digest `sha256:cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734`,
independently verified to execute Node.js 26.6.0. This replaces the Node.js
26.4.0 runtime reported for `CVE-2026-58043`, excludes the Alpine image's
unfixed BusyBox `CVE-2025-60876` Medium, and removes all general-purpose shell,
network, and build tooling before returning to non-root UID 65532. The Stage 8
gate rejects version, digest, mutable-tag, and stale-stage drift for both images
and validates the built runtime's identity, filesystem, and HTTP behavior. The
runtime gate binds the path, type, mode, ownership, and content of the complete immutable
filesystem to canonical inventories. Next's per-build preview and server-action secrets
are the only normalized fields: the gate validates their exact cryptographic formats,
single occurrences, and cross-manifest equality before hashing all remaining bytes.
It then performs a second uncached application build, requires the same source-bound
build ID and canonical inventory, and requires every normalized secret to be fresh.
The canonical inventories are
`1802:57f0e487d68f21d3fa257689364477caa211bd906e7a0f799485eb02ed1dbc52`
(arm64) and
`1804:55c33102ef9147b311df6e59b4616108df4fdc26e74f0975c6b306cbe7f94e15`
(amd64 Docker Desktop) or
`1802:9f07d878443a03e91f94d938b84fb83ed07897bee47fcc13c1f3bd0d32e0931a`
(amd64 hosted runner). Each build must match its architecture's finite reviewed set, and the primary
and uncached reproduction inventories must be identical. Only validated secret values, Docker-managed virtual trees, and injected host/hostname/resolver
mounts are excluded; renamed, relocated, linked, copied, executable, ELF,
JavaScript, JSON, and other regular-file tooling therefore fails before
scanner consensus. Raw-byte path traversal and length-prefixed binary records
make undecodable filenames unambiguous and any traversal/read error terminal.
The dependency stage verifies SHA-512 for exact npm 12.0.2 and its exact fixed
`brace-expansion`, `ip-address`, `tar`, and `undici` tarballs before extraction;
no ranged nested install supplies those repaired bytes. It is independently
required to pass both Trivy and Grype at Critical/High severity. The remaining unfixed
BusyBox `CVE-2025-60876` Medium exists only in the non-shipping build stage;
Issue `#376` accepts it only through 2026-08-12 or until a fixed BusyBox
package or suitable fixed builder digest is available, whichever occurs first.
The clean, shell-free runtime remains required through Medium. Runtime
configuration verification binds the complete behavior-bearing Docker config,
including environment, labels, working directory, exposed port, entrypoint,
and command; undeclared health checks, volumes, stop signals, shells, preload
controls, and other config fields fail closed. The application and trust paths
remain root-owned/non-writable and the runtime process must have zero effective
capabilities.

The Chainguard/Wolfi image choice changes only the container base. It does not
change frontend behavior, add providers or network calls, suppress scanner
findings, or authorize deployment, release, public availability, or production
readiness.

## Issue #389 Frontend Runtime Security Refresh

Date: 2026-08-06

Live Grype data later reported two High and five Medium findings against Wolfi
`npm-12 12.0.2-r1` in the Issue #374 runtime image metadata. Issue #389
therefore supersedes only that runtime pin with signed multi-architecture index
`sha256:d8d2883b26d4fde4e524d0068cd78abbb23c7c2113a22e67a02cc73a9182552d`.
Exact execution and the signed SPDX SBOM identify Node.js `26.7.0-r0` (MIT)
and fixed `npm-12 12.0.2-r2` (Artistic-2.0). Direct Grype scanning finds no
Medium-or-higher vulnerability in the base.

The public registry provides only the moving latest line without free
version-specific 26.6.0 access, so a digest-pinned Node 26.7.0 refresh is the
narrowest fixed public candidate. The final layer still removes npm, shells,
package managers, and general-purpose tooling. Runtime version, non-root
identity, complete immutable inventories, reproducibility, fresh build secrets,
both-scanner consensus, SBOM, config, ownership, zero capabilities, and HTTP
behavior remain fail-closed. Measured inventories are
`1803:06e4628f15e836b24128401deedceedeaebe0561bef29f96f3c9de7e2306e3e0`
for arm64 and
`1805:1c078e196a032c50ff9ba7f1954c4da2501a4ad47364ac44665ac29aed8c86b2`
for amd64 Docker Desktop and
`1803:e9a3cd116280dff5bd1e39833d511f9fa0eb952bbde5f0ffaf4aab0ab2306c9f`
for hosted amd64, measured by the fail-closed
[GitHub Actions security run](https://github.com/imrohitagrawal/narratwin-ai/actions/runs/31087364866).

Rollback may use only a newly researched, signed, immutable, scanner-clean
replacement. Returning to the Issue #374 digest, npm r1, a mutable tag, an
unscanned image, or a waiver is forbidden. This refresh changes no application,
provider, media, deployment, release, public-availability, or production claim.

## Issue #376 Frontend Dependency Builder Isolation

Date: 2026-08-20

The expired Issue #374 builder-only BusyBox acceptance cannot be renewed, and
the later Grype `CVE-2026-14456` High against Alpine `libcrypto3` and `libssl3`
3.5.7-r0 cannot be suppressed or represented as fixed. Issue #376 therefore
replaces the Alpine dependency image with the same minimal, digest-pinned
Chainguard `glibc-dynamic`, Docker Official Node 26.7.0 Bookworm-slim, and
Chainguard `gcc-glibc` composition already reviewed for the final runtime.

Only the Node executable, npm JavaScript tree, `libatomic`, and its truthful
APK/SPDX identity are imported into the dependency stage. The stage contains no
shell, package manager, OpenSSL executable, or operating-system `libcrypto` or
`libssl` package. Exact npm and nested repair archives are independently bound
by BuildKit SHA-256 and Node SHA-512 checks before identity-checked extraction;
npm and Next execute directly through the pinned Node binary. The final minimal
stage is the fail-closed `build` stage: it mounts dependencies and source
read-only, compiles in an ephemeral directory, copies only standalone output,
and removes the temporary tree in the same layer. The existing stage-filtered
reproduction therefore rotates all four Next secrets without retaining build
inputs or weakening the normalized-inventory comparison.

Node continues to truthfully report embedded OpenSSL 3.5.7. The build rejects
any Node identity where OpenSSL is shared or `node_use_quic` is enabled; the
reviewed executable exposes neither the QUIC server path described by the
OpenSSL advisory nor a shared affected operating-system library. This is a
bounded capability-removal decision, not VEX, an upstream-fix claim, scanner
logic change, severity downgrade, or exception. Both Trivy and Grype must find
zero Medium-or-higher vulnerabilities in the exact dependency image.

The final runtime identity, inventory, non-root behavior, reproduction, secret
freshness, scanner consensus, and HTTP checks remain unchanged. This builder
repair adds no application, dependency-lock, provider, media, deployment,
release, public-availability, or production-readiness authority.

## Related Documents

- `docs/QUALITY_GATES.md`
- `docs/API_CONTRACT.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/RUNBOOK.md`
- `docs/TRACEABILITY.md`
- `scripts/ci/docker-image-scan.sh`
- `scripts/ci/check_semgrep_security.py`
- `tools/semgrep/pyproject.toml`
- `.github/workflows/security.yml`

<!-- ISSUE158-SECURITY-HISTORY-V2:BEGIN -->

## Issue #158 Security History Chronology

```json
{
  "schema_version": "issue-158-security-history-v2", "record_verified_on": "2026-08-01", "evidence_scope": "public GitHub and merged repository evidence",
  "pr_152": {"number": 152, "head_commit": "1308e88255724918bbde3a4775a0c973abaca8f4",
    "ready_for_review_at": "2026-07-14T10:51:12Z", "approved_by": "rohitagrawal4u", "approved_at": "2026-07-14T10:50:43Z", "latest_required_checks_at_merge": "passed", "earlier_failed_reruns_observed": true,
    "merge_commit": "648c81c066127056334c5c2babae28585fd58d4d", "merged_at": "2026-07-14T10:52:59Z"
  },
  "state_at_pr_152_merge": {"issue_138": "open", "issue_150": "open", "issue_151": "open", "process_contract_deviation": true,
    "branch_protection_bypass_in_reviewed_evidence": "not-observed", "explicit_dated_semgrep_risk_acceptance_in_reviewed_evidence": "not-found", "cpython_scanner_consensus": "absent", "cpython_remediation": "incomplete", "waiver_in_reviewed_evidence": "not-found", "blocked_claims": ["clean-container-security", "hosted-release", "production"]
  },
  "issue_138_closeout": {"closed_at": "2026-07-14T10:53:41Z", "state_after_closeout": "closed"},
  "later_issue_151_resolution": {"pr": 180, "merge_commit": "8d18c3830ab5cb1336b33ce661e0aa33230e95e2",
    "head_commit": "f64cfb3dd34368a4920d9ec79ce9887fc17ca48e", "merged_at": "2026-07-16T21:47:31Z", "issue_151_at_pr_180_merge": "open", "issue_151_closed_at": "2026-07-16T21:48:43Z", "issue_151_state_after_closeout": "closed", "retroactively_erases_pr_152_deviation": false
  },
  "state_as_of_record_verification": {"issue_150": "open", "issue_151": "closed", "release_posture": "no-go"},
  "issue_158_effect": {"runtime_behavior": "unchanged", "scanner_behavior": "unchanged", "product_behavior": "unchanged", "global_clean_security_claim": "not-established"},
  "historical_source": {"commit": "648c81c066127056334c5c2babae28585fd58d4d", "blobs": {
      "docs/ADR/0006-stage8-release-hardening.md": "fa100222873b640371664a49caa2ba08c1f26073", "docs/RISK_REGISTER.md": "517e93cf86365574565f07f25ab44b289ca4e722", "docs/TRACEABILITY.md": "48c3c11a6abfa02014d4c044ce4ca906fa486822", "docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md": "a44d5be907e54c1e6f661c6d651d605242d668de"
    }
  }
}
```

<!-- ISSUE158-SECURITY-HISTORY-V2:END -->
