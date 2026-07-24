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

## Adversarial Review Fallback

Fresh-context sub-agent tooling was not invoked before this artifact was written
because PR A needed the first-commit preflight invariant first. Manual
adversarial fallback reviewed public/private boundary, arbitrary-project
overclaim risk, provider/public-demo/production exclusion, PR A scope, UI and
conversion completeness, critical connections, depth, audience invariant,
translation-depth risks, red-evidence merge safety, guardrail allowlist behavior,
status/traceability consistency, and governance/taste/scope.

Disposition:

- Actionable: require phase-quality validation for every matrix row status,
  evidence type, planned command, and owner PR slice.
- Actionable: require #249 and #280 reference-only PR wording.
- Actionable: require public-safe non-goals in preflight and PR body.
- Accepted limitation: PR A does not prove runtime behavior; later PRs must
  convert planned rows into executable evidence.

