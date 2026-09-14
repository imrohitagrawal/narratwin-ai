# Documentation architecture and contribution lifecycle — proposed plan

## Outcome and scope
Make repository documents, templates and current work discoverable from one entry flow, across new-product discovery, designer exploration, feature intake, implementation, review, operations and handoff. Preserve established product authority and source history. Implement bounded navigation, intake and integrity controls; do not claim all enterprise engineering practices or full CapabilityStatusV1 are proved.

## Verified problem
PR536 adds stable work records, but does not catalog all documents/templates. The sole issue form omits user/problem context, plan links and dependencies. Canonical guidance is embedded in several long documents. Legacy ADR numbers collide, architecture headers mix historical assumptions with newer implementation, and templates have multiple valid physical homes. Existing PR readability requirements are already enforced and will be retained.

## Architecture
- README is the repository front door; docs/README.md is the documentation map; CONTRIBUTING.md routes idea/discovery, design, feature, bug, implementation and review. AGENTS mandatory STATUS/CODEX flow and CLAUDE reach the same entry.
- Keep one owner for each concern: PRD/contracts product intent; ARCHITECTURE/ADRs technical decisions; STATUS current repository posture; live GitHub issue/PR/checks actual tracker facts; operating model/RCA/playbook engineering rules; stable work records plans/decisions/handoffs/evidence; GitHub native templates forms.
- One machine-readable navigation catalogue owns document roles, owner roles, update triggers, canonical template/embedded-section references, classification of all tracked documentation paths, and implementation-area documentation-impact links. Generate docs/README.md and docs/templates/README.md from it. Use the explicit name DocumentationNavigationV1, not a claim of completed DocumentationMapV1. This increments navigation and declared documentation-impact routes only. Capability-backed README generation, capability evidence, full Mermaid/ADR lifecycle semantics, stale-route authority enforcement and enforcement that every changed code path updates appropriate documentation remain outstanding accepted program requirements.
- Classification covers all tracked docs plus root entry Markdown, GitHub templates and the specification constitution. Use explicit source paths and directory rules; reject ambiguous/unmapped paths. Directory rules categorize historical/evidence collections without declaring every child accepted/current. Generated index roles, private roots and exclusions are explicit.
- Keep docs/ARCHITECTURE.md as architecture index. Preserve its bytes in this increment; the catalog explicitly identifies historical baseline prose and routes current behavior to STATUS. Add an ADR registry with stable full-filename identities, explicit legacy numeric-collision aliases, source-declared lifecycle/supersession and links; no renumbering or acceptance inference. Do not alter architecture baseline claims during navigation work.
- Keep all template originals in valid tool-owned locations. Add central catalog entries for native GitHub forms, work template, embedded intent/spec/design/preflight/closeout forms and existing invariant templates. Add no competing PR template or duplicate PRD.

## User and contributor lifecycle
- Discovery issue: affected user/problem/current evidence, unknowns, desired decision, design/source links; explicit research outcome rather than invented implementation approval. Support blank-product and feature/design questions.
- Bug issue: expected/actual behavior, reproduction/environment, user impact, safe evidence, existing work/contract. Do not solicit secrets or private session dumps.
- Extend existing implementation/stage form with user context, durable plan/work links, dependencies/decision owner and validation/closeout; retain existing field IDs and guardrail obligations.
- Keep native templates at .github/ISSUE_TEMPLATE and .github/pull_request_template.md. Add only a concise link to contributor guidance in the PR template; retain required headings, seven impact labels, five reviewer points and all evidence rules.
- CONTRIBUTING explains UI and gh CLI issue creation, search/reuse of existing work, discovery versus execution readiness, self-contained PR writing, sources supporting rather than replacing explanation, verification and closeout. Optional design prompts extend WORK.md: journey/alternatives/states/accessibility/prototype/evidence/decision. Reuse the existing playbook for intent/spec/architecture/quality rules.
- docs/DOCUMENTATION_GUIDE.md defines placement, canonical vs derived/history/template roles, update/ownership/retention rules, source capture at decisions and before handoff, supported no-GitHub adaptation for new repositories, documentation-impact selection and known limits.
- Register this increment under its own stable work record, bind plan and evidence into handoff, update observed issue ownership and STATUS minimally. New sessions can find completed checks, unresolved items and next permitted action without chat.

## Boundaries
Issue537 is the linked new request and owns a separate stable work record. Prospectively amend existing Issue535 / draft PR536 on its dedicated branch; preserve the original first preflight-only commit and commit the scope amendment alone before new implementation. Head9e35fb357835c518be0c6ffcdda06c7f51dc91fe remains immutable historical evidence; expanded PR536 is a new reviewed subject. PR534 remains unchanged; do not integrate ahead of its required closeout. No new stacked-base or branch-routing mechanism. Preserve original September source, ten masters, private inventory, all frozen V2 artifacts, AGENTS bytes and shadow authority. No runtime/provider/dependency/workflow changes, no private reads/copies, no spending, deployment, renumbering or old-source deletion. Keep broader #328/#356/#391/#426/#532/#521/#39 prerequisites open.

## Verification matrix before implementation
- DOC01 positive: all covered tracked documentation paths classified once; negative: unclassified path and equal-precedence ambiguous ownership reject.
- DOC02 canonical template ownership: native forms and embedded anchors resolve; missing target/anchor, duplicate template identity and newly unregistered template reject.
- DOC03 generated outputs: deterministic regeneration; stale index/catalog/ADR output rejects.
- DOC04 safe public traversal: path escape, symlinks and private-root references reject before read; no ignored-file traversal.
- DOC05 lifecycle intake: valid native form structures and required user/problem/outcome/evidence fields; duplicate field IDs/missing form-specific mandatory fields reject; discovery accepts unknowns and a next investigation, bug accepts observed reproduction, implementation requires a requirement and validation plan. Blank-product source links may be none yet. Native form documents use JSON (a YAML subset) for dependency-free structural validation. Existing stage IDs and PR heading obligations retained.
- DOC06 ADR identity: all existing ADRs indexed by unique full path and exact source-declared status/supersession references; absent/ambiguous lifecycle is needs-review, not inferred acceptance. Explicitly allow existing legacy collisions; new unregistered numeric collision rejects. Do not infer acceptance from filenames or catalog membership.
- DOC07 documentation-impact routes: changed implementation areas map to authoritative docs and owner/update trigger, with no second capability/status ledger. Validate configured route declarations and an explicit area query; unknown area or broken route rejects. Do not claim automatic changed-code documentation-impact enforcement.
- DOC08 cold onboarding: independent designer, zero-product discovery, feature, bug, reviewer, returning-agent and operations scenarios reconstruct source, correct form, output owner, next action and limits.
- DOC09 preservation and scope: exact allowed paths/charged-line caps; original/frozen/private descriptors and AGENTS unchanged; original PR534 subject unchanged; original PR536 checkpoint preserved in history.
- DOC10 portability: synthetic second-repository fixture uses different paths and no GitHub forms; same checker/profile adapts without code changes; declared unavailable host checks are not silently considered passed.

## Review and implementation order
1. Three independent audits (authority, contributor lifecycle, executable integration); root substantiates and classifies findings.
2. Independent review of this concrete plan, exact paths/budgets and failure matrix; publish retained source/review/preflight evidence before implementation.
3. Preflight-only amendment commit; existing draft PR536 links both535 and537 and publishes the reviewed plan before new code. The only preflight remains issue-535.json.
4. Root sole writer implements; behavioral regressions demonstrate old gaps before checker correction. Reviewers read only, use owned fixtures if execution needed.
5. Independent implementation/cold-session review, bounded blocker corrections and independent verification.
6. Run exact repository local and hosted boundaries; document actual results and source preservation. Keep draft integration dependencies; no evidence freeze/approval from local checks alone.

## Practical limits
A catalog validates recorded ownership, references and workflow shape, not truth of every sentence, complete chat capture, backup, implementation quality of every subsystem, UI auto-loading or production readiness. Broader capability/ADR semantic reconciliation remains explicit. Existing enterprise readiness register retains engineering-domain acceptance and evidence ownership; link it instead of creating a second all-green checklist.

## Reviewed refinements
Generated entry pages contain short audience routes, canonical documents and collection links; exhaustive classification remains machine-checked rather than flooding the front door with historical files. Discussion notes preserve questions/decisions; discovery ends in an evidenced decision; implementation requires execution-ready scope and applicable authority. No issue/PR filing grants execution authority. No-GitHub adaptation applies only to other repositories with an explicit local profile; NarraTwin issue/branch/PR requirements remain unchanged. Required public navigation parses real Markdown links outside comments/fences, checks canonical target/anchor and fails for a missing procedure/template. The checker supports a documented Markdown subset and no full-renderer claim.

## Exact cumulative scope
The prospective preflight contains 99 exact paths and 35398 cumulative additions-plus-deletions ceiling. New text/JSON/Markdown count physical lines; no deletion credit. Preserved historical source data is not copied. Existing allowances remain and are amended before implementation. New or increased paths:

- `docs/STATUS.md`: 180 charged lines.
- `docs/CODEX_OPERATING_MODEL.md`: 180 charged lines.
- `Makefile`: 60 charged lines.
- `README.md`: 450 charged lines.
- `docs/work/registry.json`: 3000 charged lines.
- `docs/work/PROCESS.md`: 400 charged lines.
- `docs/work/templates/WORK.md`: 400 charged lines.
- `CONTRIBUTING.md`: 280 charged lines.
- `docs/README.md`: 250 charged lines.
- `docs/DOCUMENTATION_GUIDE.md`: 300 charged lines.
- `docs/documentation-catalog.json`: 2600 charged lines.
- `docs/templates/README.md`: 150 charged lines.
- `docs/ADR/INDEX.md`: 180 charged lines.
- `.github/ISSUE_TEMPLATE/discovery.yml`: 160 charged lines.
- `.github/ISSUE_TEMPLATE/bug_report.yml`: 160 charged lines.
- `.github/ISSUE_TEMPLATE/stage_guardrail.yml`: 330 charged lines.
- `.github/pull_request_template.md`: 20 charged lines.
- `scripts/documentation_catalog.py`: 1000 charged lines.
- `tests_stdlib/test_documentation_catalog.py`: 850 charged lines.
- `docs/work/documentation-architecture/README.md`: 160 charged lines.
- `docs/work/documentation-architecture/PLAN.md`: 200 charged lines.
- `docs/work/documentation-architecture/AUDIT.md`: 250 charged lines.
- `docs/work/documentation-architecture/REVIEW.md`: 300 charged lines.
- `docs/work/documentation-architecture/DECISIONS.md`: 150 charged lines.
- `docs/work/documentation-architecture/HANDOFF.md`: 150 charged lines.
- `docs/work/documentation-architecture/evidence/INDEX.json`: 120 charged lines.
- `docs/work/documentation-architecture/evidence/SOURCES.json`: 650 charged lines.
- `docs/THIRD_PARTY_NOTICES.md`: 60 charged lines.

- `docs/ADR/0085-documentation-navigation.md`: 100 charged lines, prospectively added in5a597655 before its source was written; record the architecture decision as well as its generated index.

## Owner clarification during verification — early demo before further investment

The owner requested early proof of the actual intended experience before substantial infrastructure and production hardening, with natural presenter performance and lively coherent surroundings. The exact instruction and comparison-specific effect are retained by [the comparison owner record](../demo-comparison/DECISIONS.md#14-september-2026--early-proof-of-the-intended-presenter-experience); no reference clip was inspected here.

Three independent reviewers passed a bounded clarification within the existing99 paths/caps. Preflight-only commit031a174f precedes these edits; the [reviewed plan was published before edits](https://github.com/imrohitagrawal/narratwin-ai/issues/537#issuecomment-5662139760). Update CONTRIBUTING, work template and existing discovery/stage field descriptions with diagnostic → reviewed representative complete output → further integration → production hardening; record minimum quality, rejection, observations and go/revise/stop. Maintenance can reuse existing behavior and focused reproduction. Record the source at demo-comparison DECISIONS, link its handoff, and capture procedural adoption in this work's guide/decisions/review/handoff. Original comparison PLAN and frozen subjects remain unchanged.

Minimum stage, security, rights, privacy and operation/cost controls apply before a demo. No provider execution or acceptance-policy activation follows. Complete narration, API suitability, repetition and formal acceptance retain separate proof. Verify with independent cold reading, existing29 tests, form/navigation/scope/handoff checks, source preservation and updated hosted checks; do not add tests that mirror prose. Full local integration begun on e7ea57df remains that checkpoint's evidence; validate the subsequent documentation delta and current hosted head explicitly.
