# Architecture decision registry

Stable identity is the complete filename below. Existing numeric collisions are explicit aliases;
original files are retained. Status text is quoted from each source, not an acceptance verdict.
Missing or ambiguous status needs review. Absence of a supersession link proves no lifecycle claim.

| Stable alias | Source-declared status | Source-declared supersession |
|---|---|---|
| [0000-adr-process](0000-adr-process.md) | Accepted | Not declared; effective lifecycle unproved |
| [0001-architecture-approach](0001-architecture-approach.md) | Superseded by `docs/ADR/0001-system-architecture.md`. | Superseded by [docs/ADR/0001-system-architecture.md](0001-system-architecture.md). |
| [0001-system-architecture](0001-system-architecture.md) | Accepted for Stage 2 planning. | Not declared; effective lifecycle unproved |
| [0002-provider-agnostic-adapters](0002-provider-agnostic-adapters.md) | Accepted and amended for Stage 7. `docs/ADR/0003-llm-provider-routing.md` supersedes only the LLM routing details that previously lived here. The general provider-adapter rule remains authoritative for avatar, video, speech, storage, vector, evaluation, and observability adapters unless a later ADR explicitly replaces it. | Not declared; effective lifecycle unproved |
| [0002-rag-storage](0002-rag-storage.md) | Accepted for Stage 2 planning. | Not declared; effective lifecycle unproved |
| [0003-free-mode-vs-premium-mode](0003-free-mode-vs-premium-mode.md) | Superseded by `docs/ADR/0001-system-architecture.md`. | Superseded by [docs/ADR/0001-system-architecture.md](0001-system-architecture.md). |
| [0003-llm-provider-routing](0003-llm-provider-routing.md) | Accepted for Stage 2 planning. | Not declared; effective lifecycle unproved |
| [0004-avatar-provider-adapter](0004-avatar-provider-adapter.md) | Accepted for Stage 2 planning. | Not declared; effective lifecycle unproved |
| [0005-observability-and-evals](0005-observability-and-evals.md) | Accepted for Stage 2 planning. | Not declared; effective lifecycle unproved |
| [0006-stage8-release-hardening](0006-stage8-release-hardening.md) | Accepted for Stage 8. | Not declared; effective lifecycle unproved |
| [0007-local-principal-contract](0007-local-principal-contract.md) | Accepted for Phase 1 Closure issue `#37`. | Not declared; effective lifecycle unproved |
| [0008-postgresql-durability-schema-boundary](0008-postgresql-durability-schema-boundary.md) | Accepted for planning in Phase 1 Closure Context 1 (`#65`), advisory only. | Not declared; effective lifecycle unproved |
| [0009-context2-idempotency-lease-outbox-contract](0009-context2-idempotency-lease-outbox-contract.md) | Accepted (advisory) for planning in Issue `#66` (`DUR-IDEMP-001`, `DUR-LEASE-001`, `DUR-OUTBOX-001`). | Not declared; effective lifecycle unproved |
| [0010-context3-migrations-rollback-compatibility](0010-context3-migrations-rollback-compatibility.md) | Accepted for planning in Phase 1 Closure Context 3 (`#67`), advisory only. | Not declared; effective lifecycle unproved |
| [0011-context4-backup-restore-drill](0011-context4-backup-restore-drill.md) | Accepted for planning in Phase 1 Closure Context 4 (`#68`), advisory only. | Not declared; effective lifecycle unproved |
| [0012-context5-metrics-slos-watch](0012-context5-metrics-slos-watch.md) | Accepted for planning in Issue `#69`, advisory only. | Not declared; effective lifecycle unproved |
| [0013-ch01-migration-baseline-runner](0013-ch01-migration-baseline-runner.md) | Accepted for implementation in Phase 1 Closure issue `#86`. | Not declared; effective lifecycle unproved |
| [0014-ch02-acid-cas-storage-kernel](0014-ch02-acid-cas-storage-kernel.md) | Accepted for implementation in Phase 1 Closure issue `#93`. | Not declared; effective lifecycle unproved |
| [0015-ch04-idempotency-semantics](0015-ch04-idempotency-semantics.md) | Accepted for implementation in Phase 1 Closure issue `#97`. | Not declared; effective lifecycle unproved |
| [0016-ch05-lease-fencing](0016-ch05-lease-fencing.md) | Accepted for implementation in Phase 1 Closure issue `#95`. | Not declared; effective lifecycle unproved |
| [0017-ch06-committed-outbox](0017-ch06-committed-outbox.md) | Accepted for implementation in Phase 1 Closure issue `#96`. | Not declared; effective lifecycle unproved |
| [0018-ch03-stage4-durable-graph](0018-ch03-stage4-durable-graph.md) | Accepted for implementation in Phase 1 Closure issue `#107`. | Not declared; effective lifecycle unproved |
| [0019-ch16-consent-capture](0019-ch16-consent-capture.md) | Proposed in Issue `#111` for `CH-16` / `MEDIA-CONSENT-001`. | Not declared; effective lifecycle unproved |
| [0020-ch07-stage6-durable-replay](0020-ch07-stage6-durable-replay.md) | Accepted on branch. | Not declared; effective lifecycle unproved |
| [0021-ch08-stage7-render-artifact-state](0021-ch08-stage7-render-artifact-state.md) | Accepted for Phase 1 Closure CH-08 implementation evidence. | Not declared; effective lifecycle unproved |
| [0022-ch09-technical-rollback-compatibility](0022-ch09-technical-rollback-compatibility.md) | Accepted for implementation in Phase 1 Closure issue `#123`. | Not declared; effective lifecycle unproved |
| [0023-local-restore-integrity-drill](0023-local-restore-integrity-drill.md) | Accepted for issue `#125`; local-only implementation evidence. | Not declared; effective lifecycle unproved |
| [0024-ch10-production-metrics-contract](0024-ch10-production-metrics-contract.md) | Accepted for Phase 1 Closure child issue `#128`, implementation slice only. | Not declared; effective lifecycle unproved |
| [0025-ch11-slo-error-budget](0025-ch11-slo-error-budget.md) | Accepted for Phase 1 Closure child issue `#127`, implementation slice only. | Not declared; effective lifecycle unproved |
| [0026-ch14-restore-readiness-contract](0026-ch14-restore-readiness-contract.md) | Accepted for Phase 1 Closure child issue `#126`, implementation slice only. | Not declared; effective lifecycle unproved |
| [0027-production-like-durability-platform-ownership](0027-production-like-durability-platform-ownership.md) | Proposed technical baseline for issue `#141`; ADR acceptance and activation are blocked on the human approvals in this ADR. Not deployed and not production-like durability evidence. | Not declared; effective lifecycle unproved |
| [0028-local-lighthouse-browser-selection](0028-local-lighthouse-browser-selection.md) | Accepted for issue `#181`. | Not declared; effective lifecycle unproved |
| [0029-ch-m1-02-real-stack-evidence](0029-ch-m1-02-real-stack-evidence.md) | Accepted for issue `#208` / issue `#209` consolidated Phase 1 Closure PR. | Not declared; effective lifecycle unproved |
| [0030-mode1-stage6-stage7-bundle-binding](0030-mode1-stage6-stage7-bundle-binding.md) | Accepted for issue `#213`. | Not declared; effective lifecycle unproved |
| [0031-frontend-lighthouse-audit-remediation](0031-frontend-lighthouse-audit-remediation.md) | Accepted for issue `#219`. | Not declared; effective lifecycle unproved |
| [0032-local-demo-refusal-ux-boundary](0032-local-demo-refusal-ux-boundary.md) | Accepted for issue `#247`. | Not declared; effective lifecycle unproved |
| [0033-checkpoint3-real-browser-acceptance-evidence](0033-checkpoint3-real-browser-acceptance-evidence.md) | Accepted for issue `#269`. | Not declared; effective lifecycle unproved |
| [0034-c3a-r2-full-project-multilingual-gate](0034-c3a-r2-full-project-multilingual-gate.md) | Accepted for issue `#278` review. | Not declared; effective lifecycle unproved |
| [0035-issue280-input-api-error-contract](0035-issue280-input-api-error-contract.md) | Accepted for issue `#280` PR B scope only | Not declared; effective lifecycle unproved |
| [0036-issue280-local-e2e-demo-slice](0036-issue280-local-e2e-demo-slice.md) | Accepted for issue `#280` PR C. | Not declared; effective lifecycle unproved |
| [0037-issue280-ui-browser-demo-slice](0037-issue280-ui-browser-demo-slice.md) | Accepted for issue `#280` PR D. | Not declared; effective lifecycle unproved |
| [0037-postcss-audit-remediation](0037-postcss-audit-remediation.md) | Accepted for issue `#289`. | Not declared; effective lifecycle unproved |
| [0038-issue280-pr-e-local-demo-closure-contract](0038-issue280-pr-e-local-demo-closure-contract.md) | Accepted for issue `#280` PR E. | Not declared; effective lifecycle unproved |
| [0039-frontend-brace-expansion-audit-remediation](0039-frontend-brace-expansion-audit-remediation.md) | Accepted for issue `#296`. | Not declared; effective lifecycle unproved |
| [0040-heartbeat1-a1-curated-eligibility](0040-heartbeat1-a1-curated-eligibility.md) | Proposed for issue `#302` A1 review. Issue `#302` requires one bounded eligible-source path without authorizing A2 exclusion, UI/browser work, Heartbeat 2, providers, or production claims. | Not declared; effective lifecycle unproved |
| [0040-pr-body-live-state-reconciliation](0040-pr-body-live-state-reconciliation.md) | needs-review: missing or ambiguous source status | Not declared; effective lifecycle unproved |
| [0041-heartbeat1-a2-exclusion-summary](0041-heartbeat1-a2-exclusion-summary.md) | Proposed for issue `#304` review under parent authority `#302`. | Not declared; effective lifecycle unproved |
| [0042-heartbeat1-b-browser-reopen-evidence](0042-heartbeat1-b-browser-reopen-evidence.md) | Proposed for issue `#306` review under sole acceptance authority `#302`. | Not declared; effective lifecycle unproved |
| [0043-heartbeat2-curated-reviewer-demo](0043-heartbeat2-curated-reviewer-demo.md) | Accepted for Issue #308's frozen local/mock envelope | Not declared; effective lifecycle unproved |
| [0044-issue280-repair-architecture-feasibility](0044-issue280-repair-architecture-feasibility.md) | Accepted | Not declared; effective lifecycle unproved |
| [0045-issue280-semantic-repair-slice1](0045-issue280-semantic-repair-slice1.md) | Accepted for the bounded Issue #317 implementation | Not declared; effective lifecycle unproved |
| [0046-agent-context-shadow-architecture](0046-agent-context-shadow-architecture.md) | Accepted for Issue `#319` shadow evidence only | Not declared; effective lifecycle unproved |
| [0047-publication-boundary](0047-publication-boundary.md) | Accepted for Issue #324 governance; no product runtime or release authority. | Not declared; effective lifecycle unproved |
| [0048-cut1-presenter-enterprise-readiness-contracts](0048-cut1-presenter-enterprise-readiness-contracts.md) | Proposed through Issue #440; becomes accepted only after the dedicated PR is reviewed, merged, and reconciled in `docs/STATUS.md`. | Not declared; effective lifecycle unproved |
| [0048-quiet-presence-embedded-guide](0048-quiet-presence-embedded-guide.md) | Accepted for Issue #358 local/mock `/demo`; no deployment or production authority. | Not declared; effective lifecycle unproved |
| [0049-semgrep-cryptography-50-lock-refresh](0049-semgrep-cryptography-50-lock-refresh.md) | Accepted for bounded integration through Issue #360 review | Not declared; effective lifecycle unproved |
| [0050-brace-expansion-5-0-9-security-refresh](0050-brace-expansion-5-0-9-security-refresh.md) | Proposed for Issue #360 review | Not declared; effective lifecycle unproved |
| [0051-js-yaml-4-3-1-security-refresh](0051-js-yaml-4-3-1-security-refresh.md) | Proposed for Issue #396 exact-head review | Not declared; effective lifecycle unproved |
| [0052-pypdf-6-15-0-security-refresh](0052-pypdf-6-15-0-security-refresh.md) | Proposed for Issue #401 exact-head review | Not declared; effective lifecycle unproved |
| [0053-nanoid-3-3-17-security-refresh](0053-nanoid-3-3-17-security-refresh.md) | Accepted for Issue #403 | Not declared; effective lifecycle unproved |
| [0054-cut1-presenter-registry](0054-cut1-presenter-registry.md) | Proposed in Issue `#367`; accepted only after reviewed merged-main acceptance. | Not declared; effective lifecycle unproved |
| [0055-cut1-narration-speech-lock](0055-cut1-narration-speech-lock.md) | Proposed in Issue #382; effective only after merged-main acceptance | Not declared; effective lifecycle unproved |
| [0056-cut1-google-gemini-tts](0056-cut1-google-gemini-tts.md) | Runtime identity plus direct REST and official unary gRPC transports implemented behind a disabled boundary; activation remains package-governed | Not declared; effective lifecycle unproved |
| [0057-frontend-runtime-openssl-3-6-4](0057-frontend-runtime-openssl-3-6-4.md) | Accepted for Issue #413 review | Not declared; effective lifecycle unproved |
| [0058-cut1-atomic-project-facts-grounding](0058-cut1-atomic-project-facts-grounding.md) | proposed in Issue #421; effective only after reviewed merge | Not declared; effective lifecycle unproved |
| [0059-master-program-authority-and-route-bootstrap](0059-master-program-authority-and-route-bootstrap.md) | proposed in Issue #424; no implementation authority until reviewed merge and merged-main closeout | Not declared; effective lifecycle unproved |
| [0060-authority-reconciliation-and-stale-route-phase-spec](0060-authority-reconciliation-and-stale-route-phase-spec.md) | proposed by Issue #427; non-activating | Not declared; effective lifecycle unproved |
| [0061-core-authority-schemas-state-matrices](0061-core-authority-schemas-state-matrices.md) | Accepted for Child A implementation under Issue #431; nonactivating. | Not declared; effective lifecycle unproved |
| [0061-semgrep-1-172-mcp-override-renewal](0061-semgrep-1-172-mcp-override-renewal.md) | Accepted for Issue #150 implementation review on 2026-08-14. This decision is security-tooling-only and does not authorize release or production use. | Not declared; effective lifecycle unproved |
| [0062-nanoid-3-3-18-security-refresh](0062-nanoid-3-3-18-security-refresh.md) | Accepted for Issue #428 review on 2026-08-14. This is a security prerequisite, not product, release, or production authority. | Not declared; effective lifecycle unproved |
| [0063-authority-evidence-and-trust](0063-authority-evidence-and-trust.md) | Proposed for Issue #434 review | Not declared; effective lifecycle unproved |
| [0064-adversarial-convergence-protocol](0064-adversarial-convergence-protocol.md) | Accepted for inactive C2 RED construction; implementation pending | Not declared; effective lifecycle unproved |
| [0065-cut1-all-presenter-acceptance-provider-bakeoff](0065-cut1-all-presenter-acceptance-provider-bakeoff.md) | Proposed by Issue #452; no activation until reviewed and merged | Not declared; effective lifecycle unproved |
| [0066-cut1-presenter-live-binding-v2](0066-cut1-presenter-live-binding-v2.md) | Proposed by Issue #456; review and merge pending | Not declared; effective lifecycle unproved |
| [0068-cut1-controlled-presenter-controller](0068-cut1-controlled-presenter-controller.md) | Accepted for Issue #459 T04 local evidence validation | Not declared; effective lifecycle unproved |
| [0069-cut1-presenter-derivative-readiness-binding](0069-cut1-presenter-derivative-readiness-binding.md) | Accepted for Issue #459 T03 controlled-local readiness | Not declared; effective lifecycle unproved |
| [0069-semgrep-1-175-override-removal](0069-semgrep-1-175-override-removal.md) | Proposed for Issue #460 | Not declared; effective lifecycle unproved |
| [0070-cut1-t05-grounded-narration-handoff](0070-cut1-t05-grounded-narration-handoff.md) | Accepted for Issue #459 T05A controlled-local handoff | Not declared; effective lifecycle unproved |
| [0071-cut1-audio-caption-authority](0071-cut1-audio-caption-authority.md) | Accepted for Issue #459 T05B offline authority preparation | Not declared; effective lifecycle unproved |
| [0072-cut1-presenter-source-integrity](0072-cut1-presenter-source-integrity.md) | proposed in Issue #466; effective only after reviewed merge | Supersedes: [ADR 0058](0058-cut1-atomic-project-facts-grounding.md) only for shared claim 014's presenter predicate and source span |
| [0073-cut1-exact-hash-listening-authority](0073-cut1-exact-hash-listening-authority.md) | Accepted for the Issue #479 repository boundary | Not declared; effective lifecycle unproved |
| [0074-browserslist-4-28-8-security-refresh](0074-browserslist-4-28-8-security-refresh.md) | Accepted for Issue #495 review on 2026-09-02. This is a dependency-security prerequisite, not product, provider, release, or production authority. | Not declared; effective lifecycle unproved |
| [0075-pypdf-6-16-2-security-refresh](0075-pypdf-6-16-2-security-refresh.md) | Proposed for Issue #499 exact-head review | Not declared; effective lifecycle unproved |
| [0077-frontend-musl-scratch-runtime](0077-frontend-musl-scratch-runtime.md) | Proposed for Issue #502 exact-head review | Not declared; effective lifecycle unproved |
| [0078-cut1-configurable-audio-duration](0078-cut1-configurable-audio-duration.md) | Accepted for Issue #509 | Not declared; effective lifecycle unproved |
| [0079-cut1-t06-dual-plan-video-strategy](0079-cut1-t06-dual-plan-video-strategy.md) | Accepted for Issue #516 research sequencing | Not declared; effective lifecycle unproved |
| [0080-master-program-v2-prototype-first-governance](0080-master-program-v2-prototype-first-governance.md) | Proposed in Issue #521; authority effect `NONE` | Not declared; effective lifecycle unproved |
| [0081-httpx2-2-12-security-refresh](0081-httpx2-2-12-security-refresh.md) | Accepted child of the Issue #523 atomic candidate | Not declared; effective lifecycle unproved |
| [0082-frontend-dependency-security-refresh](0082-frontend-dependency-security-refresh.md) | Accepted | Not declared; effective lifecycle unproved |
| [0083-schema-oracle-runtime-policy](0083-schema-oracle-runtime-policy.md) | Accepted | Not declared; effective lifecycle unproved |
| [0084-native-arm64-hosted-security](0084-native-arm64-hosted-security.md) | Accepted for Issue #529 candidate validation | Not declared; effective lifecycle unproved |
| [0085-documentation-navigation](0085-documentation-navigation.md) | Proposed in Issue537 / draft PR536. No product or acceptance-policy effect. | Not declared; effective lifecycle unproved |
