---
name: output-correctness
description: Execute and independently verify meaning-bearing user-visible outputs at an exact Git head. Use for generated text, translation, audience/depth adaptation, RAG answers, reports, exports, dashboards, documents, media, or any closure claim where structural checks, metadata, screenshots, artifacts, mocks, or self-attestation could falsely pass.
---

# Output Correctness

## Contract

Act as the non-read-only execution fan. Do not implement or repair the behavior
under review. Observe it through the real in-scope user path at the exact
reviewed head.
Bind every run to the exact reviewed head.

Use only these atomic classifications:

- `STRUCTURAL_PASS`: structure exists or is mechanically valid; meaning is not
  proven.
- `SEMANTIC_PASS`: independent execution proves the required user-visible
  meaning.
- `NOT_PROVEN`: evidence is missing, stale, partial, or unable to prove the
  claim.
- `FAILED`: observed behavior contradicts the requirement or reveals a false
  pass.

Never upgrade documentation, metadata, screenshots, matrices, downloadable
artifacts, mocked status, templates, source-heading summaries, source-language
fallback, or self-attestation into semantic proof.

## Workflow

1. Resolve and record the full Git head. Stop if the worktree or evidence target
   is ambiguous.
2. Read the atomic requirement IDs and their semantic oracle before execution.
   Reject editable aggregate satisfaction fields.
3. Execute the real in-scope path without success interception or read-only
   inspection. Capture inputs, observable outputs, refusals, and exit codes.
4. Bind every observation to the exact head and one atomic requirement ID.
5. Classify every required row. Missing or partial rows are `NOT_PROVEN`;
   contradictory execution is `FAILED`.
6. For translation or adaptation, detect source-language fallback, partial
   conversion, refusals, invariant audience output, padding-only depth changes,
   and unsupported additions.
7. Run the repository atomic-closure verifier. Any `NOT_PROVEN` or `FAILED`
   result must return nonzero.
8. Emit a separate evidence record from the
   `pm-ai-shipping:intended-vs-implemented` fan. Do not reuse its reviewer,
   evidence ID, or editable pass signal.

## Stop Rules

Stop and classify `NOT_PROVEN` when the oracle, exact-head binding, required row
set, or independent execution path is missing. Stop and classify `FAILED` when
execution contradicts a requirement. Do not change product/runtime code while
acting as this verifier.
