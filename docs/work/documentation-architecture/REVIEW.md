# Documentation architecture review

## Plan review and root triage

Three independent read-only agents audited and reviewed the plan, then verified bounded corrections: authority/source ownership, contributor lifecycle, and executable integration. All three final plan dispositions were PASS within their lenses. Root accepted only substantiated findings; the audit records classifications, evidence, responsibility and limits.

Corrections: amend existing535 rather than add unsupported stacked routing; preserve historical9e35fb35 but treat expanded536 as a new subject; use DocumentationNavigationV1 with explicit incomplete capability/impact semantics; preserve ambiguous ADR lifecycle; tailor discovery/bug/implementation fields; keep indexes short; preserve all original authority/source bytes. Independent validators checked98 unique paths and35298 charged ceiling with no forbidden overlap or schema findings.

## Pre-code evidence

Full revised plan and review were published in Issue537 and PR536 before implementation. Commit72966390 changes only preflight535, after historical9e35fb35 and before new code. Original first preflight commit5392dfe1 remains. The preflight-only make quality run reported GPF.SCOPE.REQUIRED_NOT_CHANGED because new required files were not implemented yet; it was not green implementation evidence.

## Implementation verification

Independent implementation and correction reviews are complete within the recorded scope. Full local/hosted validation is recorded against the actual head in PR536. This document is a review checkpoint, not a live CI ledger.

The root added one prospectively declared ADR0085 path before writing that decision, giving99 cumulative paths and35398 charged lines. This records the navigation architecture itself; the generated ADR index is not used as a substitute decision.

The ADR scope rationale pushed the preflight objective past its existing2000-character limit; GPF.SCHEMA.LIMIT reproduced this. Root shortened the objective while preserving all explicit path/cap controls and boundaries. Existing schema tests cover this limit; no threshold was changed.

## Independent implementation findings and root disposition

| Finding | Reproduction / classification | Correction and owner |
|---|---|---|
| DOC-LINK | Inline code, escaped links and images passed required navigation. REQUIRED_CONTRACT: promised clickable route was absent. | Root excludes non-navigation tokens and checks required source links. |
| DOC-FORM | Empty dropdown and optional/empty retained guardrail choices passed. REQUIRED_CONTRACT: unusable form / lost obligations. | Root validates supported type options and profile-declared required checkbox labels. |
| DOC-ADR |39 legacy inline/bullet status declarations and scoped supersession were omitted. REQUIRED_CONTRACT: source metadata lost in generated view. | Root supports actual formats, continuations, ambiguity/empty status and source-resolved scoped supersession; original files retained. |
| DOC-ROOT | A new root Markdown guide was outside the fixed file list. REQUIRED_CONTRACT: declared inventory coverage could miss a new entry. | Root adds profile-driven root Markdown discovery and unclassified-file rejection. |

Root added behavioral regressions and observed12 failing cases across26tests before the bounded corrections; all27 current tests pass, including valid dropdown/retained-check positive partners. No test or threshold was weakened. Independent correction verification is requested separately.

Lifecycle reviewer passed all seven cold-reader scenarios, then flagged advisories: unsupported security-reporting route, non-rendered PR guidance, unlinked collections and generic update triggers. Root removed the unsupported route claim, provided visible authoring guidance, linked collections and made core update triggers concrete. Browser GitHub rendering is not claimed before default-branch activation.

One advisory remains: output generation validates all targets then writes sequentially under the root-only writer boundary; concurrent malicious path replacement is not proven safe. No concurrent writer was authorized or used. Full rendered-Markdown semantics, semantic source completeness, automated discussion capture and complete accepted capability/authority enforcement remain outside this increment.

## Independent correction verification

Authority reviewer verified all100 sampled original public sources byte-identical to9e35fb35 and exact scoped legacy status/supersession preservation. Lifecycle reviewer rechecked all four advisory corrections and retained PASS on all seven cold-reader scenarios. Validation reviewer independently verified real-link positive/negative partners, all six retained stage checkbox obligations, and new root-document detection.

The selective required-link path initially dropped actual fragments; root added a valid/missing-fragment regression, observed1RED in28tests, then corrected the same link-resolution boundary. Independent verification confirmed valid fragment PASS, missing fragment ANCHOR_MISSING and unrelated legacy links outside the selective check. All28tests now pass; no reproduced blocker remains within the three reviewed lenses.

## Skills, test levels and limits

The installed work-package protocol was consulted but its bytes/scope differ from the repository-approved activation; it was not activated as authority. Repository-native rules, public primary-source research and three read-only specialist reviews were used. The accepted master program defers external architecture-skill trust review; no new skill, plugin, package or runtime dependency was introduced.

Behavioral stdlib tests prove catalog/form/source boundaries with synthetic isolated fixtures. Static checks prove tracked references, form structure and generated views. Independent cold reading proves discoverability within seven scenarios. Full repository tests and hosted environments are still required for final validation; no local-only exact-head approval or GitHub UI-rendering claim is made.

Code/test review checkpoint SHA-256:

- `scripts/documentation_catalog.py`: `2d69edc881a36836d41ee6651e57ffb5fab066d2a6b9862058889798606dc775`
- `tests_stdlib/test_documentation_catalog.py`: `fa54dc50acf6bba697c73423610db1c491e2fb927654ce18aa5ef18526f0fc3b`

## Hosted compatibility correction

Hosted policy, quality and security checks on3a9c894c rejected the Markdown fence parser variable name as a potential credential assignment. Root classified this REQUIRED_CONTRACT because the required hosted scanner failed, while confirming the matched text is a parser expression, not a credential. Local make quality does not execute this separate compatibility scanner; the missing boundary was not covered by that green result.

Root added HostedCompatibilityTests using the actual scanner against the catalog source regardless of Git tracking, observed1RED, and renamed the local variable without changing the scanner. Independent review reproduced the old failure in an isolated fixture, verified the correction and all29tests, compared AST behavior and confirmed the scanner remains byte-identical. No waiver or threshold change. Re-run direct-head and pull-request guardrails plus the hosted checks before any exact-head acceptance; the earlier hosted failure remains historical evidence.

## Early-demo clarification review

The owner added an early intended-experience proof requirement during verification. All three reviewers passed the bounded plan before edits; preflight-only031a174f and Issue537 comment5662139760 precede the change. The exact instruction is owned by demo-comparison DECISIONS; the comparison handoff links it and this documentation work implements the reusable sequence.

All three independently reviewed the resulting documentation delta against e7ea57df and reported PASS with no reproduced blocker: lifecycle verified diagnostic/complete-output/integration/hardening order, maintenance reproduction and observed go/revise/stop; authority verified no provider/acceptance bypass, owner-reported versus observed evidence, the unidentified reference gap and eight preserved sources; validation verified unchanged form IDs/obligations, no code change, all10 new local links, work/plan bindings and99-path caps. Authority independently confirmed the quoted instruction matches the supplied visible owner message exactly after removing Markdown quote prefixes (922 characters including paragraph break). No private reads or media inspection occurred.

Existing29 focused tests and local quality/guardrails pass for the clarification. Full local integration started on e7ea57df; its results remain tied to that checkpoint. Current-head hosted checks and documentation-delta validation are required separately. The broader production and formal comparison requirements remain with their existing owners.
