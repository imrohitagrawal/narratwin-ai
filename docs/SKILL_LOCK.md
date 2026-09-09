# Skill Lock

This file records approved skill and workflow sources for NarraTwin AI. A source is not approved for use until its pin/version and license status are reviewed for the stage where it is active.

| Capability | Source URL | Pin/version status | License status | Purpose | Active stage | Activation status |
|---|---|---|---|---|---|---|
| PM Skills | `https://github.com/phuryn/pm-skills` | Pending Stage 1 activation; immutable tag or commit SHA required before use | Must be verified before activation | Product discovery, product strategy, PRD, metrics, roadmap, PRD red-team review | Stage 1 | Not activated in Stage 0 |
| GitHub Spec Kit | `https://github.com/github/spec-kit` | Pending Stage 2 or Stage 3 activation; immutable release or commit SHA required before use | Must be verified before activation | Constitution, specs, implementation plans, task breakdown, task-to-issue workflow | Stage 2 and Stage 3 planning; implementation commands blocked until Stage 4 | Not activated in Stage 0 |
| Addy Osmani Agent Skills | `https://github.com/addyosmani/agent-skills` | Pending stage-specific activation; immutable tag or commit SHA required before use | Must be verified before activation | Engineering lifecycle guidance for CI/CD, security, TDD, code review, performance, and release readiness | Stage 0 guidance only; Stage 3 through Stage 8 after activation | Not activated for product implementation in Stage 0 |
| Addy Osmani Performance Optimization Skill | Local vendored copy from `https://github.com/addyosmani/agent-skills` | Local workspace vendor copy active; upstream immutable pin still required before release dependency claims | Must be verified before release dependency claims | Stage 8 performance budget and smoke-test guidance | Stage 8 | Activated as `.codex/skills/active/performance-optimization`; guidance only, not a runtime dependency |
| Addy Osmani Security and Hardening Skill | Local vendored copy from `https://github.com/addyosmani/agent-skills` | Local workspace vendor copy active; upstream immutable pin still required before release dependency claims | Must be verified before release dependency claims | Stage 8 request/upload/dependency/container hardening guidance | Stage 8 | Activated as `.codex/skills/active/security-and-hardening`; guidance only, not a runtime dependency |
| Addy Osmani Shipping and Launch Skill | Local vendored copy from `https://github.com/addyosmani/agent-skills` | Local workspace vendor copy active; upstream immutable pin still required before release dependency claims | Must be verified before release dependency claims | Stage 8 release checklist, runbook, rollback, and launch-readiness guidance | Stage 8 | Activated as `.codex/skills/active/shipping-and-launch`; guidance only, not a runtime dependency |
| Agent Skills Standard | `https://github.com/agentskills/agentskills` | Pending verification of repository pin before adoption | Must be verified before activation | Standard format for portable `SKILL.md` instructions | Stage 0 governance and future skill packaging | Not activated for product implementation in Stage 0 |
| GitHub Action: Checkout | `https://github.com/actions/checkout` | Workflow pin managed in `.github/workflows/quality*.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Check out repo contents in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| GitHub Action: Setup Python | `https://github.com/actions/setup-python` | Workflow pin managed in `.github/workflows/quality-gates.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Provision Python runtime for guardrail checks in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| GitHub Action: Setup Node | `https://github.com/actions/setup-node` | Workflow pin managed in `.github/workflows/*.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Provision Node.js runtime for frontend checks in CI | Stage 3 through Final Review | Stage 3 CI reference; not a product implementation dependency |
| GitHub Action: Upload Artifact | `https://github.com/actions/upload-artifact` | Workflow pin managed in `.github/workflows/eval-smoke.yml` and `.github/workflows/security.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Upload eval and Docker image scan artifacts | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| Gitleaks GitHub Action | `https://github.com/gitleaks/gitleaks-action` | Workflow pin currently managed in `.github/workflows/security.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Dedicated secret scanning in CI | Stage 3 through Stage 8 | Existing CI reference; not a product implementation dependency |
| GitHub Action: Markdownlint CLI2 | `https://github.com/DavidAnson/markdownlint-cli2-action` | Workflow pin managed in `.github/workflows/quality.yml`; immutable pin review required in Stage 3 | Must be verified before Stage 3 hardening | Markdown quality checks in CI | Stage 3 through Final Review | Existing CI reference; not a product implementation dependency |
| UI/UX Pro Max Skill | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | CLI package verified locally as `ui-ux-pro-max-cli@2.10.0`; immutable repository commit pin still required before release dependency claims | MIT per npm package metadata; keep license under review before release | UI/UX design intelligence for Stage 7 avatar rendering/export workflow design review | Stage 7 | Activated locally for design guidance only via `uipro init --ai codex`; generated `.codex` files remain ignored and must not be committed |
| Locust | `https://github.com/locustio/locust` | Locked in `uv.lock` through dev dependency `locust==2.44.4` | Pending dependency license review before release | Stage 8 local API performance smoke profile and latency-budget tooling | Stage 8 | Activated as dev-only tooling; not installed in backend runtime image |
| Lighthouse | `https://github.com/GoogleChrome/lighthouse` | Locked in `frontend/package-lock.json` through dev dependency `lighthouse` | Apache License 2.0 per upstream project; verify package metadata before release | Stage 8 frontend performance/accessibility/best-practices/SEO audit | Stage 8 | Activated as frontend dev-only tooling; not a product runtime dependency |
| Trivy | `https://github.com/aquasecurity/trivy` | Installed locally via Homebrew as `trivy 0.72.0`; Dockerized fallback pinned as `aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f`; CI runner availability must be verified | Apache License 2.0 per upstream project; verify package metadata before release | Stage 8 primary Docker image vulnerability scanner | Stage 8 | Local/CI security tooling only; scans backend/frontend images for critical/high vulnerabilities and writes SARIF reports |
| Docker Scout CLI | Docker Desktop bundled CLI `docker scout` | Local CLI verified as `v1.22.0`; CI runner availability must be verified | Docker terms apply | Stage 8 Docker image scan fallback when Trivy/Grype are unavailable | Stage 8 | Local/CI security tooling only; scans backend/frontend images for critical/high vulnerabilities |
| Grype | `https://github.com/anchore/grype` | Installed locally via Homebrew as `grype 0.115.0`; CI runner availability must be verified | Apache License 2.0 per upstream project; verify package metadata before release | Stage 8 Docker image vulnerability scanning without Docker Scout login | Stage 8 | Local/CI security tooling only; scans backend/frontend images for critical/high vulnerabilities |
| StackClimb work-package protocol | `https://github.com/imrohitagrawal/stackclimb-skills.git` | VERSION 1.0.0; commit `4c49e59e5e6bb41ccca229db106de2eda3164df6`; tree `267ce5b1d05734f972bbe997d070e35546077870`; `SKILL.md` SHA-256 `ac9d5f348b2ae6d69d691f0fd990537b2dace23d799a2b3a0c9819f35837314a`; unsigned commit with no release tag | Custom `LicenseRef-stackclimb-source-v1` (MIT + Attribution); LICENSE SHA-256 `f74c8f2fdc0e2edd955b999216d660d06c69986b98427d1147f404f27057c8f5`; full notice in `docs/THIRD_PARTY_NOTICES.md` | Closed work-package/resource-ledger and governed closeout guidance; existing security/TDD/git/shipping skills did not supply the exact `TaskResourceLedgerV1` and current-session cleanup-authority boundary | Stage 8 Issue #524 governance only | Owner-approved by Issue #524 comment `5601842704`; supervised guidance only, not runtime or evidence by itself; expires 2026-10-09 |
| StackClimb machine-space reclamation | Same exact source, VERSION, commit, tree, and local symlinked checkout as the work-package protocol | `SKILL.md` SHA-256 `3c6c9f8b2aa5b13f67cf745fd5cc47e0a02b519036ac68b7bac72be2d4ff6e2c`; unsigned commit with no release tag | Same custom `LicenseRef-stackclimb-source-v1` and complete carried notice | Read-only Issue #524 resource assessment; destructive execution remains outside this activation and requires a separately frozen exact proposal plus fresh current-session authority | Stage 8 Issue #524 governance only | Invoked for read-only inventory under comment `5601842704`; no deletion activated; expires 2026-10-09 |

## StackClimb Issue #524 trust record

- The source is a clean detached checkout reached through local skill symlinks.
  The pin is exact but the symlink target is locally mutable; a source, target,
  VERSION, commit, tree, LICENSE, skill, reference, schema, or metadata change
  blocks reuse and requires review. Upstream verification passed 28 checks,
  which proves its own structural suite only—not semantic fitness for NarraTwin.
- Static review found Markdown/JSON/YAML and one standard-library `verify.py`.
  The verifier reads repository files, prints, and exits; it contains no write,
  delete, subprocess, socket, HTTP, environment-value, credential, telemetry,
  analytics, background-worker, or hook-install behavior. No package install or
  product runtime dependency is introduced.
- Both skills permit implicit invocation in their OpenAI metadata, but their
  policy requires supervision and grants no autonomy. Their frontmatter has no
  host-enforced `allowed-tools`, so NarraTwin issue, authority, spend, provider,
  merge, and cleanup gates remain controlling.
- Host CLIs can have separate authentication, telemetry, and side effects.
  No bundled credential acquisition or storage exists; the source forbids
  reading secret values, secret stores, raw process arguments, or secret URLs.
  The installed machine-space skill supplies no deletion adapter and was used
  only for non-mutating inventory in #524.
- Re-review no later than 2026-10-09, and earlier before automation,
  public/commercial redistribution, widened network/merge/deploy/cleanup use,
  or any unexpected telemetry, hook, credential, or side-effect behavior.
  Residual risks are policy-not-enforcement, an unsigned untagged pin, mutable
  local symlinks, and separately governed host tools.

## Lock Rules

- Prefer preinstalled and repo-approved skills/docs before creating, installing,
  or activating a custom skill/plugin. Record the checked options and unmet gap
  in the PR preflight evidence.
- Do not use a custom skill/plugin unless the PR links explicit approval,
  rejected existing options, source, pin/version, license, telemetry,
  filesystem/network, hook, credential, expiry/revisit, residual-risk,
  `docs/SKILL_LOCK.md`, and `docs/THIRD_PARTY_NOTICES.md` evidence.
- Do not activate a source with unclear license, telemetry, filesystem, network, hook, or credential behavior.
- Do not commit `.codex` cache, vendor, auth, config, or plugin runtime state.
- Do not run implementation-oriented skills in Stage 0.
- Update this file in the same PR that activates or changes a skill source.
- Update `docs/THIRD_PARTY_NOTICES.md` when a third-party package, tool, skill, model, API, dataset, provider, media asset, or generated sample is introduced.
