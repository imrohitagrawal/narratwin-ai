# ADR 0043: Heartbeat 2 curated reviewer demo

- Status: Accepted for Issue #308's frozen local/mock envelope
- Date: 2026-07-29
- Authority: Issue #308 and reset-6 canonical comment `5121265229`

## Context

Heartbeat 1 already persists approved curated chunks in the project-scoped RAG store. The existing local walkthrough path retrieves from that store, but the browser UI's legacy demo creates a second project and uploads a second document. That split prevents a reviewer from proving that the curated source drove the displayed script and local/mock media chain.

## Decision

Use two serialized PRs. PR A establishes exact branch/allowlist policy, fail-closed semantic/privacy verification, and a trusted-CI execution boundary. PR B may then connect the existing curation UI to the existing Stage 4, 6, and 7 contracts using one `curator_demo` project and the Next rewrite.

The verified chain must join curated source/checksum/chunks to walkthrough context, claim support, evaluation, visible citations, translation, subtitles, mock voice, consent, render manifest, and JSON video placeholder. The browser ledger contains exactly eight writes: project, submit, approve, ingest, walkthrough, multilingual, consent, render. `other_demo` must receive 403 and see no project actions.

`scripts/ci/heartbeat2_evidence.py` independently confirms semantic/privacy integrity: exact run/head identity, one non-skipped browser case, request-object-paired traffic, local-only trace traffic, exact joins, artifact bytes and metadata, safe archives, source digests, and zero forbidden matches. Local verification reports `SEMANTIC_PASS_LOCAL`, never execution authenticity. CI evidence is valid only when the required exact-head GitHub Actions job also records zero-exit Playwright execution, binds workflow/runner/report/trace digests and run context, verifies `CI_EXECUTION_BOUND`, and uploads from the same successful workflow run. Post-run acceptance rebinds artifact digest and workflow-run metadata to the exact reviewed head.

Owner-authorized Contract reset 6 adds only the existing CI workflow to PR A and replaces the impossible standalone source-authenticity claim with trusted execution provenance. Its exact ceilings are PR A 9 files / 1,600 lines / 5 surfaces, PR B 12 / 900 / 6, and aggregate 15 / 2,500 / 8. PR A proves verifier and workflow-contract behavior with synthetic packets; only PR B may produce genuine browser evidence.

## Boundaries

This is a post-Checkpoint-B local reviewer integration heartbeat, not Product Mode 2. It changes no backend/API/storage contract and authorizes no providers, paid service, real media, cloned identity, deployment, hosting, public distribution, production claim, private data, or Issue #20 Q&A. Issue #8 remains open product memory; #155 stays closed; #20, #43, and #249 stay unchanged.

## Consequences

The local demo becomes product-faithful for the controlled synthetic fixture while retaining honest local/mock limits. PR B cannot begin until PR A receives eligible exact-head approval, merges, and completes post-merge verification. Any need for an unlisted path, backend change, third PR, excluded capability, or budget expansion stops H2.
