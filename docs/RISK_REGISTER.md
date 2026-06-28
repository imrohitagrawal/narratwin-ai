# Risk Register

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

## Top blockers before Slice 1

1. Finish skill trust review.
2. Confirm Slice 1 scope excludes avatar/video/TTS.
3. Add local validation and CI wrapper expectations.
4. Keep provider adapters mock-first.
5. Keep prompt-injection and unsupported-claim tests mandatory.
