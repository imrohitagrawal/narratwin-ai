# Issue #280 Merge-Safe Red Evidence Review

## Claim

PR A captures red evidence for #280 planning gaps without committing permanently
failing tests or claiming runtime completion.

## Red Evidence Posture

| Evidence class | PR A handling | Merge safety |
|---|---|---|
| Current runtime gaps from issue comments | Recorded as `RED_EVIDENCE_CAPTURED` rows in the matrix. | Static evidence only; no failing runtime tests committed. |
| Future executable failures | Planned commands recorded per row. | Later PRs own RED/GREEN implementation. |
| Strict xfail option | Allowed only with issue-linked removal criteria. | Static checker rejects missing owner/removal criteria. |
| Skipped tests option | Allowed only when skip reason and later owner are machine-checkable. | Static checker rejects permanent skip without owner. |
| Issue comments | Accepted as planning source only, never final evidence. | Matrix validator rejects issue-comment-only row evidence. |

## Reviewed Red Cases

- Prefix-only audience adaptation.
- Synonym-only audience adaptation.
- Generic persona slogans.
- Unsupported audience-specific claims.
- Citation/source-support drift.
- Deep output that pads without source-supported substance.
- Concise output that hides required source-backed caveats.
- Standard output identical to concise.
- Translated output that drops audience framing.
- UI metadata claiming behavior not visible in transcript.
- Artifact/export mismatch.
- Glossary terms used as instructions.
- Runtime private personality inference.
- Prompt text overriding selected audience/depth.
- Unsafe input echo.
- Planned-language fake success.

## Adversarial Review

Sub-agent tooling was checked and used after the first-commit preflight
invariant was preserved. Agent `Noether`
(`019f9377-c867-7ce3-be0d-ae00f84a5e0e`) performed a read-only adversarial
review of public/private boundary, arbitrary-project overclaim risk,
provider/public-demo/production exclusion, PR A scope, UI and conversion
completeness, critical connections, depth, audience invariant, translation-depth
risks, red-evidence merge safety, guardrail allowlist behavior,
status/traceability consistency, test/quality/CI evidence, and
governance/taste/scope.

Disposition:

- Actionable: require phase-quality validation for every matrix row status,
  evidence type, planned command, and owner PR slice.
- Actionable: require #249 and #280 reference-only PR wording.
- Actionable: require public-safe non-goals in preflight and PR body.
- Actionable from sub-agent review: concrete input bounds and planned error
  taxonomy were added to the matrix and checked by the static validator.
- Actionable from sub-agent review: runtime-completion claims are checked across
  title, body, and commit-message visible PR text.
- Actionable from sub-agent review: stale #274 status/next-action wording was
  reconciled to the active #280 PR A state.
- Accepted limitation: PR A does not prove runtime behavior; later PRs must
  convert planned rows into executable evidence.
