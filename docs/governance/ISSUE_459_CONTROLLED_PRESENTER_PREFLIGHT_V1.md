# Issue 459 Controlled Presenter Entry Preflight V1

Status: T01/T02 entry contract; product implementation remains blocked
Issue: `#459`
Branch: `lane-a-cut1-459-controlled-presenter`
Accepted base: `ab97b6eecba6db9c66c37d19b29257c7398f3ab7`
Pre-code freeze: [Issue comment 5449765467](https://github.com/imrohitagrawal/narratwin-ai/issues/459#issuecomment-5449765467)

## Intent and completion boundary

This increment freezes and proves the entry contract for the controlled-local
Cut 1 presenter path. It does not implement that path. The future outcome uses
the already approved grounded walkthrough to produce independently reviewable
Meera, Raj, and Myra English landscape and portrait evidence. Every cell must
stand on its own; no aggregate can hide a failed cell or severe defect.

T01/T02 completes only when the exact branch route, closed schema, stimulus-only
RED corpus, literal test-owned expectations, typed unimplemented executor, and
independent entry review agree. The future executor remains RED. No backend,
frontend, asset, provider, media, credential, egress, spend, deployment,
publication, release, production-readiness, or human-study action is part of
this increment.

## Source identities frozen at the accepted base

| Source | SHA-256 | Role |
|---|---|---|
| `specs/001-grounded-walkthrough-script/spec.md` | `cd16ea947a70271f60a5ce7086e577c1cc25f380baf9a338342bfafb522b8c35` | Lane A requirements and non-goals |
| `specs/001-grounded-walkthrough-script/plan.md` | `166dd8021026eb334607d0dab290c2b121964bcb979e7e502b574f830b45dfd4` | dependency order and checkpoints |
| `specs/001-grounded-walkthrough-script/tasks.md` | `9c244de820bf0df1c1d7d7e4c323e5317ba5818cb625f88165e675ce51817fdc` | LA-C1-T01 through LA-C1-T08 |
| `docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md` | `14dbdeb898af240fd30d203e131be8c6e8e29c5803c82463c1b50dc4c8616877` | accepted Issue #16 review |
| `.specify/memory/constitution.md` | `ebb0c16c8aa9d967e4c946f31ae600e6e45016bf5c3aa6f098ceac795cd142c2` | implementation constitution |
| `docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` | `2e864e044253a98ea10fdf6dde1ab32a026354aaa5c00cebe3b40756d653936e` | presenter and Cut boundary |
| `docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md` | `14dbbb6f005d9887ad8ab90340bca9fdcc5fb969579ef3d03f69d5566d0616f8` | grounding and evaluation |
| `docs/ENTERPRISE_READINESS_REGISTER.md` | `fd42d73871b62f48e018ced1eb5020ffcb53a62cdbdd53936b7c257c22940c1d` | readiness non-claims |
| `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md` | `e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b` | metric authority |
| `docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md` | `7c041dfcca1e5f7e067744eaec18b1577df4be2cf391eb128b786bde7ca1521b` | exact C1-M01–C1-M10 checklist |
| `docs/governance/cut1-all-presenter-acceptance-matrix-v1.json` | `f61cef9f7731f4603778d1b6a3a9ccccd3682c8e0ad233c9370169320612b2f5` | six-cell and asset contract |
| `docs/governance/cut1-presenter-live-binding-v2.json` | `89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702` | immutable live input set |
| `docs/governance/cut1-project-facts-v1.json` | `cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b` | accepted atomic project facts |
| `docs/PRD.md` | `2cde5d9ec7d8e932b25f2fdf66d4dd11f49065b50078f16f59b6a65cbb7d720a` | inherited product requirements |
| `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` | `0a3c14d0d61fbfaf5fe6dec0a7ca3a9412f1b1fd8aa458837f0c3b37b5570db3` | inherited requirement mappings |
| `docs/ARCHITECTURE.md` | `e7515ee96dce07e0d583e15984ea335b6f2499bfd8aa6e9f519bc4a830122fa4` | architecture constraint |
| `docs/API_CONTRACT.md` | `910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf` | API constraint |
| `docs/DATA_MODEL.md` | `f073c9bff26717233f23c6317b03736c02bee5952b88fa840767f79287b6ec09` | data constraint |
| `docs/SECURITY_AND_PRIVACY.md` | `185fe98ffa0b12287b6e7e8a532fac89ffa7a29380db71f8dd6aa4d1b7bc4b62` | security/privacy constraint |
| `docs/OBSERVABILITY_AND_COST.md` | `c77a0d4ea071e6ea364d9c1f4175361633d4d54962c7fc8d9527033e160d91c6` | observability/cost constraint |
| `docs/governance/cut1-blinded-human-evaluation-protocol-v1.json` | `fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8` | nonactivated human-study contract |
| `docs/governance/cut1-provider-bakeoff-contract-v1.json` | `1a3fd981644488203e8c7cc38fc0389092b23b579cce860c3d35a1ca7a1786db` | disabled provider contract |
| `docs/STATUS.md` at accepted base | `9045b595ca1622680f621dffa4dff88435e2fde0d13e3c061ced7eb6df9ae8bf` | mutable current-state constraint before this route |
| `docs/TRACEABILITY.md` at accepted base | `e597069e3d6b765a9d68e5336ff9597d6d7b809e5ea6f316f22312ca71ea136a` | mutable traceability constraint before this route |
| `docs/QUALITY_GATES.md` at accepted base | `9f628d22ec62075e560ef478820cf094d923cdf1cfded56a512291c61f6e542b` | mutable quality constraint before this route |
| `docs/REPOSITORY_GUARDRAILS.md` at accepted base | `04f8b405bc7ba9b615cc1d5d7e489bcbf643b9de4bfc9b331e5a60c38629e82f` | immutable route-entry guardrail constraint |

The approved knowledge is `demo/stage8_seed_project.md` at
`49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e`.
The approved demo script is `docs/demo/PHASE_1_DEMO_SCRIPT.md` at
`3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435`.
The presenter registry is `backend/app/presenter_registry.json` at
`eb31a953b85ffaf2c43f54e4da7fb89eda740c724967a9301f726c6091ab01c2`.
Any mismatch stops and requires contract rebinding before product work.

### Editable GitHub authority snapshot

Bodies were read through the GitHub API on `2026-08-28` and hashed as their
exact UTF-8 body bytes with no added newline. URLs are evidence locators; the
digests are the frozen identities.

| Authority | Body SHA-256 |
|---|---|
| [Issue #459](https://github.com/imrohitagrawal/narratwin-ai/issues/459) | `dd03b171f25b0d249a79834f22674c728e539fa8b171a97b3a4728474e0039d5` |
| [Branch creation comment 5449632582](https://github.com/imrohitagrawal/narratwin-ai/issues/459#issuecomment-5449632582) | `07b7cb91660a21ba0a70419ff07195a2532089a087d7a289806142dc81151fa0` |
| [Branch correction comment 5449637037](https://github.com/imrohitagrawal/narratwin-ai/issues/459#issuecomment-5449637037) | `f236d2840a7ce35e074b6e370dcc706278772c47fa09b6c18b20a344b22fd1a0` |
| [T01/T02 freeze comment 5449765467](https://github.com/imrohitagrawal/narratwin-ai/issues/459#issuecomment-5449765467) | `75882f1f3deb8dea77ab945cd58f0526b04644fb4cb208bcd50ddea29846bbe7` |
| [Path correction comment 5449822130](https://github.com/imrohitagrawal/narratwin-ai/issues/459#issuecomment-5449822130) | `48f86809e1032884d5576ceefde06d64785b486e1adae940fe32c2b6391e6cf3` |

## Independent cells

| Cell | Role | Current derivative readiness |
|---|---|---|
| `meera-en-landscape` | primary | conditional |
| `meera-en-portrait` | primary | conditional |
| `raj-en-landscape` | first backup | `NOT_READY` |
| `raj-en-portrait` | first backup | `NOT_READY` |
| `myra-en-landscape` | second backup | `NOT_READY` |
| `myra-en-portrait` | second backup | `NOT_READY` |

The accepted still checksums remain:

- Meera: `d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1`
- Raj: `663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd`
- Myra: `30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97`

Originals are immutable inputs, never derivative outputs. Raj and Myra have no
hands-visible derivative authority. T03 and T06 stop until exact new paths,
bytes, provenance, permitted use, deletion posture, and human approval exist.

## Exact metrics

| ID | Pass contract | T02 discriminating mutation |
|---|---|---|
| C1-M01 | gaze ratio `>= 0.80`; off-camera interval `<= 2000 ms` | lower ratio or longer interval |
| C1-M02 | lip offset P95 `<= 80 ms`; continuous error `<= 200 ms` | either value above maximum |
| C1-M03 | word accuracy and spoken-word coverage `>= 0.98`; missing span `<= 1000 ms` | lower accuracy/coverage or longer gap |
| C1-M04 | citation coverage `1.0`; unsupported accepted count `0` | coverage below one or count above zero |
| C1-M05 | insufficient-context abstention `1.0` | any accepted unsupported response |
| C1-M06 | zero identity, face, hair, clothing, background, or switch mismatch | one mismatch |
| C1-M07 | zero malformed limb/finger defects; gesture repetition `<= 2` | one severe defect or repetition three |
| C1-M08 | keyboard, captions, screen reader, focus, reduced motion; contrast `>= 4.5` | any false state or contrast below 4.5 |
| C1-M09 | script/evaluation P95 `<= 20000 ms`; ready-to-preview `<= 5000 ms` | either latency above maximum |
| C1-M10 | two runs have identical script, bindings, evaluator and manifest checksum | any unequal binding |

Boundary values pass; weakening, rounding rescue, omitted measurements, `NaN`,
infinity, strings, booleans, pooled values, or missing per-cell evidence fail.

## Existing interfaces to consume

| Boundary | Existing authority | Future use | Prohibited substitute |
|---|---|---|---|
| Presenter identity | `PresenterRegistry`, `PresenterTraceBinding` | exact presenter lifecycle and trace binding | caller identity or arbitrary asset |
| Grounding | `Cut1GroundingContract`, Stage 4 evaluation lineage | source-bound claims and abstention | narration-as-source or Meera receipt reuse |
| Narration | `NarrationService`, `NarrationVersion`, `TTSConsumptionReceipt` | approved immutable spoken text | caller success assertion |
| Voice | `TTSProvider` protocol and local provider boundary | provider-neutral audio binding | optional external provider activation |
| Captions | Stage 6 artifact/manifest contracts | exact script/audio/caption agreement | text-only placeholder success |
| Presenter output | `AvatarProvider`, `Stage7Service`, artifact metadata | controlled local render boundary | external stub or JSON placeholder as video |
| Evaluation | current evaluation and approval checksums | current passing evidence | stale or replayed approval |

Approval evaluation is self-contained. For each cell, `artifactAuthorId` must
differ from `reviewerId`, `approvalUseCount` must equal one, and the approved
artifact and manifest digests must equal the same cell's artifact and manifest.
`approvalRequestSha256` is SHA-256 over the UTF-8 newline-framed sequence
`Cut1ApprovalRequestV1`, artifact digest, manifest digest, presenter-binding
digest. `approvalSha256` is SHA-256 over the UTF-8 newline-framed sequence
`Cut1ApprovalV1`, approval ID, approval-request digest, reviewer ID, artifact
author ID, approved-at timestamp. No corpus ID, magic actor name, prior process
memory, or expectation map is an input to those decisions.

### Reproduced lineage conflict

`backend/app/cut1_grounding.py` selects only Meera and validates claim hashes
against the Meera mapping. `backend/app/narration.py` rejects a presenter binding
whose presenter is not Meera, and the existing tests require Raj/Myra refusal.
This is accepted behavior, not a defect to patch during T01/T02.

Classification: `REQUIRED_CONTRACT`. T05 cannot bind Raj/Myra cells by reusing
Meera lineage. An owner-reviewed all-presenter lineage extension or explicit
handoff must precede any change to grounding, narration, or downstream audio.

## Observability contract

Every future cell evidence record must carry bounded, non-secret values for:

- tenant, project, request, run, and trace IDs;
- source, script, retrieval, claim-support, evaluation, and approval identities;
- presenter ID/version, registry digest, asset/derivative digest, and aspect;
- narration version/digest, voice profile/version, audio digest and measurements;
- caption digest, language, cue/accuracy/coverage evidence;
- artifact/manifest digest, decoder result, duration, dimensions, and media kind;
- provider mode/model/config digest with call, egress, retry, and spend counters;
- C1-M01–C1-M10 per-cell raw values, result, evaluator version, and evidence digest;
- refusal/error/fallback reason, timestamps/durations, provenance and deletion refs.

Logs and evidence must exclude raw private sources, prompts, narration, audio or
video bytes, biometric/personal data, credentials, environment values, provider
payloads, stderr, and sensitive absolute paths. IDs, counts, enum reasons,
durations, and hashes are the allowed diagnostic projection.

## Entry-route paths and budgets

Charged lines are additions plus deletions from the fixed base with no deletion
credit. The aggregate cap is 4,300, readability review begins at 3,655, and
work stops for rescope before 3,870.

| Path | Charged-line cap | Byte cap where applicable |
|---|---:|---:|
| `docs/governance/preflights/issue-459.json` | 220 | 32,000 |
| `docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md` | 850 | 64,000 |
| `docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json` | 450 | 40,000 |
| `docs/governance/cut1-controlled-presenter-red-corpus-v1.json` | 500 | 48,000 |
| `scripts/quality/cut1_controlled_presenter.py` | 140 | 16,000 |
| `tests/unit/test_cut1_controlled_presenter_red.py` | 700 | 60,000 |
| `scripts/quality/check_quality_stage.py` | 60 | — |
| `tests/unit/test_issue459_quality_dispatcher.py` | 140 | 24,000 |
| `scripts/quality/stage8_cut1_routes.py` | 180 | — |
| `tests/unit/test_stage8_cut1_routes.py` | 340 | — |
| `docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md` | 500 | 48,000 |
| `docs/QUALITY_GATES.md` | 120 | — |
| `docs/STAGE_ISSUE_PLAN.md` | 120 | — |
| `docs/PHASE_PLAN.md` | 100 | — |
| `docs/STATUS.md` | 160 | — |
| `docs/TRACEABILITY.md` | 120 | — |

All are regular UTF-8 text. Missing, extra, renamed, copied, binary, symlinked,
untracked, lookalike-branch, wrong-base, dirty, or cap-breaching evidence fails.

## Future path ownership freeze

The entry route does not allow these product paths. If all stops are resolved,
the reviewed transition may activate only this inventory, with new per-task
caps no greater than the maxima below. Adding or substituting a path requires
owner rescope before mutation.

| Task | Future-owned paths | Maximum charged lines |
|---|---|---:|
| T03 | `docs/governance/cut1-presenter-derivatives-v1.json`, `frontend/public/demo/cut1/meera-waist-up.webp`, `frontend/public/demo/cut1/raj-waist-up.webp`, `frontend/public/demo/cut1/myra-waist-up.webp`, `backend/app/presenter_registry.json`, `backend/app/presenter_registry.py`, `tests/unit/test_cut1_presenter_derivatives.py`, `docs/THIRD_PARTY_NOTICES.md` | 2,400 text; each binary <=500,000 bytes |
| T04 | `backend/app/cut1_controlled_presenter.py`, `tests/unit/test_cut1_controlled_presenter.py` | 2,400 |
| T05 | `backend/app/cut1_grounding.py`, `backend/app/narration.py`, `backend/app/stage6.py`, `backend/app/stage7.py`, `tests/unit/test_cut1_atomic_grounding.py`, `tests/unit/test_cut1_narration.py`, `tests/unit/test_stage6_multilingual.py`, `tests/unit/test_stage7_avatar.py` | 4,600 |
| T06 | `tests/acceptance/test_cut1_controlled_presenter.py`, `evals/cut1/controlled-presenter-v1.json` | 1,800 |
| T07 | `backend/app/main.py`, `tests/api/test_cut1_controlled_presenter_api.py`, `frontend/src/app/demo/guide-client.ts`, `frontend/src/app/demo/guide-client.test.ts`, `frontend/src/app/demo/page.tsx`, `frontend/src/app/demo/page.module.css`, `frontend/src/app/demo/page.test.tsx`, `frontend/tests/cut1-controlled-presenter.spec.ts` | 4,000 |
| T08 | `docs/ADR/0067-cut1-controlled-local-presenter.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/SECURITY_AND_PRIVACY.md`, `docs/OBSERVABILITY_AND_COST.md`, `docs/QUALITY_GATES.md`, `docs/STAGE_ISSUE_PLAN.md`, `docs/STATUS.md`, `docs/TRACEABILITY.md`, `docs/reviews/ISSUE_459_EXACT_ARTIFACT_ACCEPTANCE.md` | 2,400 |

Generated six-cell artifacts and raw measurements stay in a bounded private
task evidence root unless a later issue explicitly approves exact repository
paths and sizes. No unreviewed binary becomes repository authority.

## Failure and evidence matrix

| ID | False pass | Expected evidence | T02 status |
|---|---|---|---|
| I459-CELL-01 | cell missing, duplicated, or pooled | literal six-key set plus per-cell decisions | RED test |
| I459-LIN-01 | source/script/evaluation/presenter/audio/caption/config substitution | mutate every lineage leaf | RED test |
| I459-APR-01 | stale, replayed, revoked, self-authored, or pre-artifact approval | current exact-artifact approval | RED test |
| I459-MEDIA-01 | placeholder, text/JSON, empty, corrupt, nonregular, oversized, undecodable, or foreign media passes | byte/decode/type/checksum mutations | RED test |
| I459-GROUND-01 | unsupported claim or insufficient-context answer passes | grounding and abstention mutations | RED test |
| I459-ID-01 | unauthorized presenter, original overwrite, new likeness, clone, or unapproved derivative passes | registry/provenance/rights mutations | RED test |
| I459-PROV-01 | credential, external provider, egress, retry, or spend occurs | fake boundary plus exact zero counters | RED test |
| I459-A11Y-01 | keyboard, screen reader, focus, caption, contrast, reduced-motion failure passes | per-cell accessibility mutations | RED test |
| I459-M01 | weakened or missing gaze threshold passes | exact boundary and below/above mutations | RED test |
| I459-M02 | weakened or missing lip-sync threshold passes | exact boundary and above mutations | RED test |
| I459-M03 | weakened or missing caption threshold passes | exact boundary and accuracy/gap mutations | RED test |
| I459-M04 | weakened grounding threshold passes | coverage/count mutations | RED test |
| I459-M05 | incomplete abstention passes | insufficient-context mutation | RED test |
| I459-M06 | identity mismatch is averaged away | severe-defect mutation | RED test |
| I459-M07 | malformed motion or repeated gesture passes | severe/repetition mutation | RED test |
| I459-M08 | accessibility metric is omitted or weakened | control/contrast mutation | RED test |
| I459-M09 | timing budget is omitted or weakened | script/preview latency mutation | RED test |
| I459-M10 | unequal repeated-run bindings pass | checksum/version mutation | RED test |
| I459-OBS-01 | logs/evidence leak sensitive content or omit correlation/cost posture | schema and redaction mutation | RED test |
| I459-ROUTE-01 | lookalike branch, base drift, missing/extra path, or budget excess passes | route mutation tests | GREEN bootstrap test |

Every T02 future-behavior assertion must fail only because the executor returns
`CUT1.ENTRY.NOT_IMPLEMENTED`. Collection, import, materialization, corpus,
schema, route, dispatcher, and security checks must succeed.

## Failure behavior

Invalid input produces deterministic, bounded findings and no artifact. A cell
cannot transition to accepted until all predecessors and all applicable metrics
pass. Partial success is audit-visible but never aggregate success. Retry never
changes authority, spends, calls a provider, or reuses an artifact without the
same immutable request and current approval. Unexpected exceptions are not
success and cannot expose raw input.

## Commands and evidence classes

Entry bootstrap:

```text
python3 -m json.tool docs/governance/preflights/issue-459.json
uv run pytest -q tests/unit/test_stage8_cut1_routes.py tests/unit/test_issue459_quality_dispatcher.py
uv run pytest -q tests/unit/test_cut1_controlled_presenter_red.py -k 'not future_behavior'
python3 scripts/guardrails_check.py
NARRATWIN_POLICY_ONLY=1 make quality
```

Authentic RED:

```text
uv run pytest -q tests/unit/test_cut1_controlled_presenter_red.py
make quality
```

The final two commands are expected to fail at T02 with the exact typed RED
inventory. A generic nonzero exit, collection error, route error, or missing
tool is not authentic RED.

Future T08 additionally requires the full unit/API/frontend/browser, security,
dependency, evaluation, accessibility, performance, exact-hosted-topology,
artifact replay, policy and `make quality` gates. Local evidence cannot freeze
or approve a release candidate without hosted parity.

## Human-only decisions and unresolved dependencies

| Surface | Owner | Current decision | Revisit trigger |
|---|---|---|---|
| Raj/Myra/Meera hands-visible derivatives and permitted use | repository owner plus provenance/privacy reviewer | blocked; no derivative bytes authorized | before T03 or T06 |
| Raj/Myra grounding/narration lineage | repository owner plus AI-quality reviewer | blocked by accepted Meera-only contract | before T05 |
| Issue #368 audio/provider ownership | repository owner | remains with open #368; no duplication or closure | before any T05 audio work |
| Blinded human study | Issue #432 owner | not authorized | before recruiting, exposure, or study data |
| Provider/account/credentials/region/privacy/retention/egress/spend | Issue #449 owner plus security/privacy/cost reviewers | not authorized | before any provider operation |
| Legal/consent/disclosure/public use | accountable legal/compliance owner | not established | before derivative/public use |
| Manual visual, listening, and accessibility acceptance | independent eligible reviewers | not run | exact artifact available |
| Hosted settings and required status contexts | repository owner | must be reproduced, not inferred locally | before freeze/merge |
| Final squash/merge text | repository owner | reference-only wording required | immediately before merge |

Issue #421 supersedes only the historical missing-grounding blocker described
in Issue #368. It does not transfer final audio/provider ownership to #459.

## Skill and test selection ledger

| Claim/boundary | Option | Decision | Evidence or prevented action | Classification |
|---|---|---|---|---|
| task decomposition | `planning-and-task-breakdown` | invoked as in-session guidance | preserved T01/T02 entry slice and T03–T08 stops | guidance consulted; repository activation not claimed |
| behavior/gate proof | `test-driven-development` | invoked as in-session guidance | literal expectations precede any GREEN implementation | guidance consulted; repository activation not claimed |
| multi-file execution | `incremental-implementation` | invoked as in-session guidance | C1 preflight-only commit precedes C2 | guidance consulted; repository activation not claimed |
| security/privacy | repository RCA, playbook, security docs | selected | stopped credentials, egress, spend, derivatives and sensitive logs | useful; prevented unsafe action |
| browser testing | browser/DevTools skill | deferred | no UI exists in T01/T02 | considered but wrong stage |
| performance optimization | performance skill | deferred | no runtime performance claim exists | considered but redundant at entry |
| shipping/launch | shipping skill | rejected | release and deployment are prohibited | useful; prevented scope expansion |
| custom skill/plugin | any new custom capability | rejected | approved docs and existing guidance cover the method | considered but unnecessary |

Skill use is not completion evidence. Tests, hashes, route behavior, review, and
hosted receipts prove claims.

## Review prompt set

Independent reviewers must try to disprove, with exact paths and reproduction:

1. Can any missing or pooled cell pass?
2. Can a Meera grounding/narration receipt be substituted for Raj or Myra?
3. Can stale approval, placeholder/corrupt media, or recomputed outer hashes pass?
4. Can an unauthorized identity, derivative, credential, provider, egress, or spend attempt pass?
5. Can C1-M01–C1-M10 be weakened, omitted, rounded, pooled, or represented with non-finite values?
6. Can accessibility or sensitive-log failures be hidden?
7. Can a lookalike branch, base drift, missing/extra path, rename/copy, binary, symlink, untracked file, or budget excess pass?
8. Does any doc or test overclaim media, acceptance, study, hosted, release, or production status?

Findings are reproduced and classified as `CRITICAL_BLOCKER`,
`REQUIRED_CONTRACT`, `ADVISORY_DEBT`, `DUPLICATE`, or `OUT_OF_SCOPE`. Reviewer
labels alone do not decide progression.

## Stop conditions

Stop on source/hash, branch/base, path/budget, corpus/schema, metric, cell,
lineage, authority, identity/provenance, security/privacy, accessibility,
review, or hosted-topology drift. Stop on any new dependency/provider, any
credential/egress/spend/media/deployment/publication/release action, and on any
human-only uncertainty named above. Stop after two new substantive post-review
blocker classes and return to contract definition before another correction.

No GREEN product implementation begins until the entry review records no open
reproduced blocker. The Meera-only lineage conflict and derivative/audio/study/
provider authorities remain explicit later-task stops even if T01/T02 passes.
