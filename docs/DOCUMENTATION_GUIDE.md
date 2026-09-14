# Documentation architecture and ownership

[Documentation map](README.md) · [Template catalog](templates/README.md) ·
[Contributor lifecycle](../CONTRIBUTING.md) · [Current work](work/INDEX.md)

## One owner per concern

| Question | Canonical home | Do not infer |
|---|---|---|
| What product are we building? | PRD, product strategy and accepted product contracts selected by STATUS | A proposal is approved because it is in docs |
| What works and what remains? | STATUS repository ledger; live issue/PR/check records for current tracker facts | Historical checkpoints are live state |
| How is it designed? | ARCHITECTURE as index, API/data/security views and ADR source files | A diagram proves running behavior |
| How do we engineer it? | AGENTS, operating model, guardrails, RCA, quality gates and existing playbook | A checklist proves acceptance |
| What is this work doing? | Stable docs/work record with plan, decisions, handoff and evidence | Work location grants implementation or spending authority |
| Which form should I use? | Template catalog linking native forms and embedded source sections | All templates must physically move into one folder |
| What proves a claim? | Original evidence and its owning record, exact source revision and verification | A digest proves semantics or backup |

README is the front door. This map organizes documents; the work index organizes
independently owned work. They reference the same existing status and authority
sources. The navigation catalog owns paths, roles, maintainer roles and update
triggers only. Maintainer roles describe responsibility, not a new permission or
CODEOWNERS assignment. Assign an accountable person/agent in each actual issue.

## Placement and naming

Keep existing canonical files and stable work IDs. Native GitHub templates stay in
`.github/`; root entry files remain where tools expect them. Shared reusable forms
live in `docs/templates/` or link to existing embedded forms. Work-specific plans,
design notes, decisions and evidence live under `docs/work/WORK-ID/`. Significant
architecture decisions remain under `docs/ADR/`; technical views link from
ARCHITECTURE. Current views link originals instead of copying their requirements.

Use a stable descriptive work ID, not a date that changes each session. Dates and
revisions identify preserved proposals/evidence. Retain completed/reopened work at
the same path. Historical recovery stays historical; it is not a default location
for active plans. A move requires a reference inventory, provenance/derivation,
retained old source or redirect, refreshed bindings and independent verification.
No source deletion is authorized by this process.

## Catalog and generated views

[documentation-catalog.json](documentation-catalog.json) is the single navigation
configuration. `DocumentationNavigationV1` is deliberately limited: entries own
individual files; collections classify remaining files using the longest matching
prefix. Exact file entries take precedence; duplicate file owners and identical
collection prefixes fail. Collection roles describe storage, not semantic authority
of each child. New root documents must receive an explicit entry; new collection
files inherit a reviewed classification. Every native or reusable template requires
an explicit catalog entry, even when its directory has a collection rule.

The generator produces the documentation map, template catalog and ADR index.
It uses tracked public files only. Add new files to Git's index before generating:

```sh
python3 -m scripts.documentation_catalog --catalog docs/documentation-catalog.json --write
make documentation-quality
```

Git timeout is a finite positive configurable option, `--git-timeout-seconds`.
Public checks reject path escape, symlinks, missing/untracked targets, private paths,
dangling supported headings, unregistered templates, ADR collision drift and stale
generated output. Required entry links must be actual inline Markdown links outside
comments/fenced examples. The supported subset is ATX headings, inline links and
simple explicit anchors; reference-style links, full GitHub rendering, external
network availability and complete Mermaid semantics are not certified by this gate.

The ADR registry uses full filenames as stable aliases. Legacy numeric collisions
are explicitly enumerated and retained. New collisions need a reviewed correction;
do not renumber historical evidence for neatness. Lifecycle text is source-declared,
not a verdict. Missing/ambiguous status is marked needs-review. Existing supersession
references are linked and checked; no link does not prove an ADR remains effective.

ARCHITECTURE and several engineering documents preserve historical stage baselines.
Use STATUS's accepted-contract map and exact later amendments for current effect.
This navigation increment preserves those originals rather than silently recasting
old assumptions as current runtime truth.

## Select documentation impact

Configured area routes connect implementation locations to relevant canonical
sources, owner roles and update triggers. Inspect a route before planning a change:

```sh
python3 -m scripts.documentation_catalog --catalog docs/documentation-catalog.json --area api-data
```

Routes cover product/design, API/data, AI/evaluation, media/localization, security,
operations/reliability, CI/supply chain and engineering governance. The checker proves
that configured locations/references exist and rejects unknown queries. It does not
inspect a Git diff and prove that every changed implementation has accurate matching
documentation. The implementer and reviewer select the affected docs under existing
PRD/ADR/traceability/status rules; full change-impact enforcement remains separate.

The [enterprise readiness register](ENTERPRISE_READINESS_REGISTER.md) and
[quality gates](QUALITY_GATES.md) remain the sources for engineering-domain acceptance.
This catalog supplies discovery and responsibility, not a parallel all-green maturity
score. Capability-backed README generation, capability evidence, full Mermaid/ADR
lifecycle semantics, stale-route authority enforcement and complete document-impact
traceability from the accepted master program remain outstanding requirements.

## Capture decisions and resume without chat

Capture early demonstration requirements and investment decisions in the owning
work record using the [work template](work/templates/WORK.md#early-demonstration-and-investment-decision)
and [contributor sequence](../CONTRIBUTING.md#prove-the-intended-experience-early).
Retain desired experience, identified references, minimum quality, actual outputs,
failures and the go/revise/stop decision. Distinguish reported dissatisfaction from
inspected evidence. A small diagnostic precedes representative complete-output proof;
substantial integration and production hardening follow supporting evidence, while
minimum required controls apply before the demo. A missing reference identity stays
an explicit evidence gap rather than a claim that an example was reproduced.

Follow [work PROCESS](work/PROCESS.md). At a meaningful decision record the exact
visible source coordinate and permitted custody, date, decision owner, rationale,
constraints, effect, rejected alternatives and superseded record. Retain original
instructions and evidence; summaries are navigation aids. Never export hidden
reasoning, private credentials or raw private sessions to public documentation.

Before handoff record what is complete, what is pending, blockers, next permitted
action, plan/evidence identities, observed checkout/tracker facts and which sources
were not inspected. A new session verifies live facts before action. Offline checks
validate recorded consistency; they cannot know about an omitted conversation or a
new live issue. Owners must reconcile coverage explicitly. Local copies and hashes
are not independent backup; existing backup/restore work retains that responsibility.

## Reuse for a new repository

Start small: product intent, current status, one architecture index, one contribution
route, work records and a template catalog. Grow a document only when its concern has
independent ownership or consumers. Use the existing engineering playbook's intent
and spec sections rather than copying this repository's requirements.

Adapt the catalog profile: inventory roots/files, canonical paths, owner roles,
update triggers, private roots, templates, intake requirements, impact routes, ADR
prefix/collision policy and output locations. The checker accepts `--root` and
`--catalog`; tests exercise different paths and a profile without GitHub forms.
Reuse its small public-file helper alongside the checker; no provider or package
installation is required. The work-record checker has separate NarraTwin integration
assumptions; this does not claim that every repository script is portable.

For a new repository without GitHub, use its declared issue/review capabilities and
record what is unavailable; local Markdown intake is possible if that repository's
policy permits it. This is not an exception to NarraTwin's issue/branch/PR rules.
Do not copy NarraTwin issue IDs, source hashes, private locations or acceptance gates.
Before adoption, exercise a zero-product idea, design/feature, bug, PR review,
operator lookup and interrupted-session resume using only the new entry points.
