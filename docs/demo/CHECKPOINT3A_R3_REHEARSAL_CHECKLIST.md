# Checkpoint 3A R3 Rehearsal Checklist

This checklist is reviewer-facing planning evidence for issue #280 PR A. It is
not a runtime demo, public URL, hosted deployment, provider setup, real media, or
production-readiness artifact.

## Human Review Checklist

| Focus area | Verify | Pass condition | Fail condition |
|---|---|---|---|
| Scope | PR A changed files match `docs/governance/preflights/issue-280.json`. | Only planning, docs, reports, validators, and unit tests changed. | Backend/frontend/runtime/provider files changed. |
| Issue posture | #249 and #280 remain reference-only. | PR body says both remain open. | Any closing keyword or completion claim appears. |
| Runtime boundary | PR A does not implement runtime product behavior. | Matrix rows are planned/red/static only. | PR claims arbitrary synthetic multilingual flow now passes. |
| Persona research | Persona rows cite public sources and avoid stereotypes. | Every audience mode has research basis and source-binding rule. | Persona relies on implementer assumption or private inference. |
| Audience/depth | Audience invariant and depth invariant are explicit. | Matrix covers all audiences, all depths, and interaction rows. | Prefix-only or metadata-only adaptation could pass. |
| UI coverage | Required UI controls and tooltips are represented. | Matrix covers DEEP, full transcript, truncation, info icons, errors, glossary, visible state, citations, exports, keyboard, mobile, and refusal preservation. | UI row omits any required user-facing affordance. |
| Info icons | Required guidance surfaces are listed. | Project name, Knowledge document, Audience, Depth, Target language, Glossary terms, Synthetic avatar consent, Walkthrough script, Demo preview, Citations, Export artifacts, and provider/local/mock posture are covered. | Any required tooltip/info surface is absent. |
| Conversion parity | Source, English, target transcript, stored output, UI, export, and Stage 7 placeholder parity are represented. | Matrix includes run IDs, language, direction, audience, depth, glossary, citations, contextRefs, claimSupports, eval ID, checksums, subtitles, voice manifest, avatar demo, render manifest, and video placeholder. | Metadata-only or artifact-only success can pass. |
| Development test strategy | Future #280 implementation PRs treat tests as part of the feature contract. | Owned rows declare positive, negative, corner, API, contract, exact browser UI, E2E flow, and regression coverage or a reviewed re-scope. | A future PR claims behavior is satisfied with unit-only, metadata-only, UI-without-browser, or issue-comment-only evidence. |
| Red evidence | Failing behavior is merge-safe. | No permanently failing tests are committed; rows use planned/red statuses. | CI must fail for PR A to preserve red evidence. |

## Later Demo Path To Prove

`create project -> upload markdown -> approve -> ingest -> generate English Stage 4 -> translate Stage 6 -> avatar placeholder/export Stage 7 -> UI render -> download/decode artifacts -> compare report`

The planned gate name is `make issue280-output-correctness`. PR A defines this
contract only; later PRs must implement the executable path.
