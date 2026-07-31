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
| P1-R5 | Production durability and monitoring remain incomplete despite local/mock demo readiness | P1 | `#39` | Optional local JSON snapshots and `/api/v1/ops/status` reduce restart and visibility gaps for local review. Production, multi-worker, external-provider, and public synthetic-media release remain No-Go until ACID/CAS durable state and deployment monitoring evidence exist. |
| P1-R6 | PR `#47` residual hardening items could be mistaken for Phase 1 release blockers | P2 | `#48`, `#49` | Classified as pre-production/P2 hardening. They block stronger production auth, local-demo durability, multi-worker, or production-readiness claims, but do not block local/mock Phase 1 demo review while production remains No-Go. |
| P1-R7 | Semgrep `1.168.0` has not declared compatibility with fixed Click releases | P1 | `#138`, `#150`, `#158` | PR `#152` merged the isolated tool override after exact-head approval and passing required checks. The reviewed public record contains no separate explicit dated Semgrep residual-risk acceptance, so issue `#158` records a process-contract deviation without treating approval or merge action as that acceptance. Issue `#150` remains open for removal or re-review by `2026-08-13`. |
| P1-R8 | CPython `3.13.14` requires maintained downstream security backports and dual-scanner consensus | P1 | `#151` | PR `#180` merged checksum-bound CPython backports, exploit regressions, and dual Trivy/Grype consensus controls; issue `#151` then closed on 2026-07-16. That later remediation does not erase PR `#152`'s earlier process deviation or establish hosted, release, deployment, or production readiness. |

## Top blockers before Slice 1

1. Close or downgrade remaining Phase 1 P0/P1 issue `#39` with evidence.
2. Keep release posture No-Go until `docs/reviews/GO_NO_GO.md` is updated by reviewed PR.
3. Keep provider adapters mock-first.
4. Keep prompt-injection and unsupported-claim tests mandatory.
5. Do not create a release tag until all Phase 1 gates pass.

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
