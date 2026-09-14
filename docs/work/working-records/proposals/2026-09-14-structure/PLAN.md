# Scalable work records and session entry points

Status: REVIEWED DESIGN — recommended by the root orchestrator for the implementation
sequence below. Three independent initial reviews and final correction-verification
passes completed; this does not activate repository policy or approve a merge.
Date: 14 September 2026. Owner: root orchestrator under delegated user authority.
Related work: Issue #535 / draft PR #536; README clarity #356; context freshness
Issue #328; broader resource automation #391; private evidence store #532.

This local review packet is preserved in the repository working folder. It is
not staged, merged, a scope amendment, a new product authority or a migration.
The existing archive and all recovered bytes remain untouched. SOURCES.json records
exact reviewed repository sources and the current open-issue census.

## Decision

Adopt stable `docs/work/<work-id>/` records for ongoing work. Keep product
requirements, accepted contracts, architecture, API, security, ADRs and traceability
at their established authoritative locations. Use a single discovery flow and
explicit evidence ownership, source identity and status references. Completed work
keeps its path; historical revisions remain reachable without treating an older
source as obsolete. This is a reusable project convention, not a claim that one
universal industry folder standard exists.

## Authority and discovery

| Concern | Authoritative home / role |
|---|---|
| Product purpose and initial requirements | Existing docs/PRD.md, interpreted with the accepted amendments identified by STATUS |
| Current accepted product/readiness contracts | Existing STATUS canonical-contract map and its linked contracts; PHASE_PLAN retains its existing precedence |
| Repository-tracked governance/delivery status | Existing docs/STATUS.md; live GitHub state is separately observed and reconciled |
| Architecture, APIs, security, operations and decisions | Existing docs/ARCHITECTURE.md, API_CONTRACT.md, SECURITY_AND_PRIVACY.md, RUNBOOK.md and ADR files |
| Requirement-to-implementation/evidence traceability | Existing TRACEABILITY/requirements/evidence maps; do not replace them with the work registry |
| Work navigation and relationships | docs/work/registry.json, with generated docs/work/INDEX.md |
| Current work plan and evidence | The registered plan/source and owning work record; PLAN.md is created only when that work owns a distinct plan |
| Agent instructions | AGENTS.md and existing mandatory reading; tool-specific files point to this shared flow |

README gives humans a prominent start map: product overview, current limitations,
PRD, STATUS/current accepted contracts, and the work index. AGENTS retains its
mandatory reading and links the shared session procedure in CODEX_OPERATING_MODEL.
STATUS adds the work index near its opening authority map, not only at its end.

A new session follows: repository README and applicable agent instructions ->
STATUS/current contract map -> PRD and applicable accepted detailed contracts ->
work INDEX -> selected work README/current plan/DECISIONS/HANDOFF -> required
original sources and verification. Before acting, verify the actual checkout,
branch/head, current applicable tracker facts and outstanding authorization.
The entry map does not replace AGENTS' existing required reading list.

CLAUDE.md, if supported, becomes a minimal tracked bridge to AGENTS and this
common flow, with no copied product/status rules. It is currently ignored; an
explicit narrow policy change is required before tracking it. Do not assume every
AI tool loads the same file automatically: verify discovery for each supported
tool. Generic agents and humans always have README as the visible fallback.
The existing docs/agent-context system remains shadow-only unless separately adopted.

## Directory convention

```text
docs/
  PRD.md                     existing product requirements
  STATUS.md                  existing current ledger and authority map
  ARCHITECTURE.md             existing architecture index
  ADR/                       existing architecture decisions
  work/
    INDEX.md                 generated navigation; do not edit a parallel ledger
    registry.json            stable work IDs, relationships and canonical pointers
    PROCESS.md               capture, registration, revision and handoff procedure
    templates/               small reusable work template and versioned schema
    master-program/
    g1-certification/
    demo-comparison/
    working-records/
    <another-stable-work-id>/
```

A substantial work record uses:

```text
<work-id>/
  README.md                  scope, reading order and links to canonical sources
  PLAN.md                    distinct current work plan, when owned here
  DECISIONS.md                dated decisions, authority, rationale and supersession
  HANDOFF.md                  observed revision, verification, open work, next action
  evidence/
    INDEX.json               owned artifact identities and shared-source references
    reviews/                 public-safe review findings and verification receipts
  proposals/                 unaccepted alternative plans, explicitly labeled
  history/                   superseded snapshots and historical receipts
  experiments/<experiment-id>/   optional independently identified runs/studies
```

When a current plan already exists, registry/README point to it; do not create a
second PLAN.md copy. Source plans and newly written execution plans are explicitly
different roles. Small routine changes use their parent record and existing issue/
PR evidence; they do not require a complete empty directory template. Create an
independent work record when it has a distinct owner, scope, decision or handoff.

## Registry, ownership and status

One registry owns discovery metadata. INDEX is rendered from it; duplicate hand-edited
navigation/state tables are prohibited. Minimum fields: stable ID, title, kind,
owner, record path, canonical plan reference with role, status reference, parent,
typed relationships, evidence index reference, handoff reference, and reconciliation
checkpoint. References include revision/commit or explicit current-document semantics.
Record branch/commit-specific availability for unmerged work; a main checkout must
not present a branch-only file as locally available. Optional display status is
source-derived and labeled with its observed revision, never an independent ledger.

Keep repository delivery status in STATUS. Plan approval and authority effects
come from their existing decision/acceptance sources. Evidence validity, private
availability and backup verification are separate observations. Registry entries
link these states instead of inventing a second acceptance system or granting
approval from folder placement. Unresolved source conflicts are visible and block
only the claims/work that depend on them; do not silently pick the newest prose.

Use kinds such as program, workstream, comparison, experiment, delivery increment,
and governance/recovery. One optional primary parent groups work; typed depends-on,
related-to and uses-evidence-from links handle multiple programs and shared assets.
Reject duplicate IDs, dangling/self references and parent or dependency cycles.
Ordinary related-to links may be reciprocal; do not reject every graph cycle.

An artifact has one logical owner and immutable revision identity. Minimum evidence
fields: stable artifact ID, owning work ID, role, revision, SHA-256, byte count,
public relative path or unchanged opaque restricted reference, custody/sensitivity,
verification receipt, and derived-from/supersedes references where applicable.
A consumer refers to the owner's artifact; it does not copy an original to become
another competing source. Version names and historical IDs remain exact, including
the existing B_V3 reference whose actual source is a V5 file.

## Coverage for NarraTwin

Start with the following records and links. This is a proposed grouping, not new
issue authority or a complete reclassification of every historical file.

| Work | Contents / existing links |
|---|---|
| master-program | Original September owner source, effective V1 and five-cut roadmap, separately labeled V2/six-cut candidate, program decisions; #521/#450 |
| g1-certification | Certification/correction work, the ten exact supporting masters, semantic reviews and dependencies; #521/#533/PR534 |
| demo-comparison | Current whole-workflow comparison, prior research and exclusions, format/protocol distinctions, future experiments; #449/#519/#512 |
| working-records | Retention recovery, this structure proposal, migration evidence and reusable process; #535/PR536; coordinate #356/#328 |
| delivery workstreams | TTS/narration, rendering, UI capture and integration; preserve #510/#368/#369/#370/#520/#371 scope and relationships |
| cross-cutting governance/security | Operational configuration, dependency remediation, evidence/privacy and lifecycle; #493/#523/#524/#525/#532/#391 |
| future capability work | Interactive Q&A and premium/observability tracks; #20/#21 and the current effective roadmap; mark deferred/candidate posture from their real authorities |
| readiness/operations | Production durability, monitoring, restore and security; #39 and its child work, existing enterprise readiness register |

The implementation inventory must reconcile every open issue, current program,
comparison, recovery packet and load-bearing plan to an owning record or an explicit
parent/exclusion, with reason and source. Register history through links instead
of relocating the whole repository. Dates belong to evidence/revisions, not IDs
that change whenever work resumes. Existing DocumentationMapV1/CapabilityStatusV1
requirements remain complementary; the work registry does not implement or replace
them merely by listing work.

Comparison/experiment profiles identify question, alternatives, baseline, criteria,
protocol, inputs/settings/authority, exact runs and outputs, outcomes, decisions
and limitations. Retain rejected outputs and changes to the hypothesis. Separate
exploratory/formal/production evidence and continuous/editorial formats where they
matter. Independent experiments may have their own work ID; ordinary runs stay
under their owning comparison. Registration grants no provider or spending authority.

## Private evidence and historical material

Separate logical ownership from private physical storage. The original owner plan
belongs logically to master-program; ten semantic sources belong to G1; comparisons
reference them. The complete recovered packet stays intact initially; do not split
or duplicate all its files merely to improve the public navigation.

Proposed long-term local store: `.evidence/stores/<stable-store-id>/`, protected
before any copy by exact reviewed ignore rules, tracked-file rejection and public
review. Store identity and actual relative locator mapping are kept in a restricted
catalog; public documents contain safe identifiers and explicit access instructions.
Existing restricted-evidence IDs remain unchanged. No personal absolute locator or
raw conversation is committed. New paths require privacy regression tests before use.

Until that store migration is verified, new work records may reference the current
intact private store. Mark its old work-archive location as a temporary retained
location, with a clear current-location map. If it moves, copy and hash first,
switch references together, retain original copies and safe redirect notices.
Do not overwrite original bytes while correcting their semantic interpretation.
History may contain necessary historical sources and rejected evidence; it does
not mean expendable data. Retention/deletion authority remains separately governed.

A clean public clone can validate its public documentation and references. It must
report private payloads as not checked/unavailable, and cannot approve dependent
source-based claims. Unrelated public work can continue. Local private read-back,
independent store access, encrypted backup and restore proof remain separate.
Independent backup is still UNPROVED under #532; an ignored folder is not a backup.

## Required capture and verification

At a meaningful decision, save the current plan revision and supporting files;
record user-visible instruction/source coordinate, reason, owner/authority, effect,
constraints, supersession, open questions and next action. Preserve restricted
verbatim records where required; summaries are additional reading aids. Record
coverage cursors and omissions, and include the actual stored message format in
capture tests (the prior channel/phase omission must remain a regression).

Before handoff/compaction, branch changes or cleanup: update the work record and
required indexes, verify actual sources, and bind handoff to the plan revision,
required artifact-set digest and observed repository state. A handoff can cite an
already existing verification/source commit; do not require embedding its own final
commit SHA, which would create a self-referential hash requirement.
Automation proves recorded data consistency, not that every conversation was captured.

Separate generic checks (schema/IDs/links/relationships/ownership/path safety,
handoff freshness and public/private boundaries) from artifact-specific profiles.
Retain the existing exact eleven-source G1 profile; no self-declared count replaces
its frozen authority descriptors. New work records should be data/configuration,
not another issue-number branch in central validation code. Unsupported profiles
fail the requested profile check without blocking unrelated supported records.

| Failure case | Required evidence |
|---|---|
| New reader picks V2/candidate as current accepted program | Cold-start reconstruction names effective V1/roadmap, candidate and constraints correctly |
| PRD alone misses later accepted contracts | Reading-flow test reaches STATUS authority map and applicable detailed contracts |
| Orphan/missing work, duplicate ID, broken source link | Registry schema and complete inventory reconciliation checks |
| Program parenting or prerequisite cycle; shared evidence duplicated | Typed graph and one-owner/reference tests; allow reciprocal related-to links |
| Missing/changed master hidden by a count | Existing exact eleven-source negative tests plus actual private read-back |
| New private directory accidentally tracked | Ignore and forced-tracked-path rejection tests at every supported storage root |
| Unsafe paths, symlinks, stale snapshot or locator | Existing path tests, migration map and source/plan/handoff drift rejection |
| Whole-workflow sample promoted to model/production proof | Profile review checks protocol, acceptance scope, lineage and limitations |
| Completed work is moved/deleted or historical source overwritten | Stable link/revision tests, retention review and copy-before-cutover evidence |
| Generic agent/Claude discovers a different authority | Human + available agent cold-start tests; tracked bridge non-divergence check |
| Public-only run claims private access, approval or backup | Explicit not-checked and unsupported-claim negative tests |
| Migration succeeds only in one dirty worktree | Clean public checkout, registered private-store read-back, old-path alias checks |

## Action plan and integration order

1. Finish this design review and retain its findings and exact proposal. Do not
   rename the archive or move private payloads during planning.
2. Reconcile the complete source/work inventory and select canonical owners and
   aliases. Reuse existing #356/#328/#391/#532 responsibilities instead of silently
   absorbing or duplicating their work. Declare exact per-increment paths, measured
   line/data budgets, storage ownership, tests and status effects before coding.
3. Revise #535/PR536's preflight and reviewer packet prospectively. Its current
   twenty-path allowance does not cover README, AGENTS, templates or generic registry
   work. Keep already verified recovery checks available while preparing the change.
   Record dependencies between the core navigation increment, authority/bridge work
   and private migration; the old pre-code PR-link deviation remains historical.
4. Prepare the exact proposed AGENTS delta for independent review. Follow the
   repository's separate anchor-prerequisite then authority-consumer route; never
   update AGENTS and its own cleanup hash anchor in the same PR. Validate old/new
   subject topologies and update necessary context source/selected bindings with
   independently reviewed fixtures. CLAUDE gets a narrow tracked bridge exception;
   no copied rulebook or silent force-add. Required reading remains in force.
5. Implement the registry/index, generic checks plus G1-specific profile, reusable
   minimal template, and prominent README/STATUS/CODEX links. Register initial work,
   shared evidence and current-source pointers. Avoid mass renaming existing PRD,
   ADR, contracts, roadmap or historical issue documents.
6. Migrate only necessary physical locations after privacy protections and tests
   pass. Freeze old-to-new IDs/paths/hashes, copy and read-back, switch indexes and
   entrypoints atomically in the reviewed package, retain old sources/redirects.
7. Independently test cold starts for a human, generic AI and each supported tool:
   identify the product, current capability/limits, accepted authority, relevant
   active plan, required exact evidence, outstanding work and next permitted action
   without relying on the previous conversation. Prove both clean-clone and private
   modes; run full applicable local and actual hosted checks before exact-head approval.
8. Preserve PR534's frozen subject and existing carrier sequence. Prepare these
   increments now; do not merge any ahead of the required carrier closeout. Refresh
   from verified current main afterward, reconcile scope/anchors, then merge the
   separately reviewed increments in dependency order. PR536 remains a draft until
   its required validation/approval conditions are proved. No G1 acceptance follows.
9. Adopt the small template/checklist across new work; backfill current material by
   reviewed batches, leave historical sources reachable, and handle encrypted backup
   and a real independent restore separately under #532. No paid service is selected.

Done means new contributors can deterministically find and verify the right sources
through stable entrypoints, with no competing authority, privacy regression, lost
source or fabricated completeness. It does not mean every historic issue is rewritten,
all conversations captured, backup proven, or product/production capability delivered.

## Review disposition

Three independent reviewers completed initial assessment and a bounded final
verification of the consolidated proposal. All three returned PASS within their
planning scopes, with no substantiated remaining blocker. Root substantiated the
concrete constraints against repository files and adopted the corrections above.
See REVIEW.md for findings, classification, verification and final scoped decision.
