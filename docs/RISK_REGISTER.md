# Risk Register

Status: this file remains a product risk seed plus Phase 1 Closure addendum.
The Final Review Risk Register baseline in `docs/reviews/RISK_REGISTER.md` and
`docs/reviews/GO_NO_GO.md` records the July 1 No-Go review posture from PR
`#45`. Post-Final Review issue dispositions are superseded by reviewed Phase 1
Closure evidence in `docs/reviews/PHASE_1_CLOSURE_REPORT.md` and the addendum
below.

| ID | Risk | Severity | Likelihood | Owner | Mitigation | Status |
|---|---|---:|---:|---|---|---|
| R1 | MVP expands into avatar, TTS, video, Q&A, and premium providers too early | High | High | Product/Engineering | Enforce vertical slices and PRD cut line | Open |
| R2 | Generated walkthrough includes unsupported claims | High | Medium | AI Evaluation | Add unsupported-claim detection and refusal tests | Open |
| R3 | Uploaded documents contain prompt injection | High | Medium | Security/AI Safety | Treat uploads as data, not instructions; add injection tests | Open |
| R4 | User uploads secrets or confidential information | High | Medium | Security | Secret scan, local-first storage, upload limits, clear warnings | Open |
| R5 | Local avatar/lip-sync tools have restrictive licenses | High | Medium | Engineering/Legal Review | Complete third-party notices before enabling any tool | Open |
| R6 | Premium provider becomes mandatory by accident | Medium | Medium | Architecture | Provider interfaces, mock providers, no paid keys in tests | Open |
| R7 | Costs rise due to repeated generation | Medium | Medium | Platform | Cache outputs and track estimated cost per run | Open |
| R8 | UI polish hides weak backend grounding | Medium | Medium | Product/Review | Build grounding loop before avatar/video polish | Open |
| R9 | CI fails once backend/frontend appears because wrapper scripts are missing | Medium | High | Engineering | Add `scripts/ci/*` wrappers with the first code slice | Open |
| R10 | Skills conflict and Codex follows the wrong instruction source | Medium | Medium | Engineering | Use `docs/SKILL_TRUST_REVIEW.md` conflict rules | Open |

## Phase 1 Closure Addendum

| ID | Risk | Priority | Source | Current disposition |
|---|---|---:|---|---|
| P1-R1 | Governance/release docs contradict merged Stage 8 and Final Review state | P0 | `#35`, `#40` | Must close in Module A. |
| P1-R2 | Final Review remains No-Go for production, multi-worker, external provider, real video, and public synthetic-media claims | P1 | `#39`, `docs/reviews/GO_NO_GO.md` | Must remain blocked or be explicitly downgraded with evidence. |
| P1-R3 | Local principal contract and checksum evidence-integrity gaps weakened security/correctness claims | P1 | `#37`, `#42` | Closed through merged PRs `#47` and `#50`; keep evidence referenced for audit, but these are no longer active Phase 1 blockers. |
| P1-R4 | Branch protection/ruleset enforcement could not be proven from repository files | P1 | `#38` | Resolved with live GitHub evidence and the required-context drift check in PR `#53`: `main` branch protection is enabled with strict required CI checks, required PR review, admin enforcement, blocked force pushes, blocked deletions, and required conversation resolution; `policy-gates` now verifies the public branch summary API reports `protected: true`, `enforcement_level: everyone`, exact required contexts, and GitHub Actions app bindings; direct pusher restrictions are unavailable on this user-owned repository per GitHub API validation. |
| P1-R5 | Production durability and monitoring remain incomplete despite local/mock demo readiness | P1 | `#39` | Production, multi-worker, external-provider, and public synthetic-media release remain No-Go until durable state and operational monitoring evidence exist. |
| P1-R6 | PR `#47` residual hardening items could be mistaken for Phase 1 release blockers | P2 | `#48`, `#49` | Classified as pre-production/P2 hardening. They block stronger production auth, local-demo durability, multi-worker, or production-readiness claims, but do not block local/mock Phase 1 demo review while production remains No-Go. |

## Top blockers before Slice 1

1. Close or downgrade remaining Phase 1 P0/P1 issue `#39` with evidence.
2. Keep release posture No-Go until `docs/reviews/GO_NO_GO.md` is updated by reviewed PR.
3. Keep provider adapters mock-first.
4. Keep prompt-injection and unsupported-claim tests mandatory.
5. Do not create a release tag until all Phase 1 gates pass.
