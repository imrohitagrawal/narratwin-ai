# Working records and session continuity

This is the shared procedure for programs, comparisons, experiments, delivery and
governance work. Existing PRD, accepted contracts, ADRs, traceability and STATUS
retain their authority. The registry owns navigation metadata; it does not adopt
a proposal, complete an issue, authorize a provider or prove production readiness.

## Start a session

1. Read repository README and applicable AGENTS instructions, including all required
   reading. CLAUDE points to the same instructions.
2. Read STATUS and its current accepted-contract map; read the PRD and applicable
   later accepted contracts. Distinguish effective V1 from candidate V2.
3. Open [INDEX.md](INDEX.md), select the work record, then read its registered plan,
   decisions, handoff and required evidence. Read full sources before relying on them.
4. Verify actual branch/head, applicable live issue/PR facts and operation authority.
   A checkpoint is an observation, not a live tracker or authority grant.
5. Run `make work-records-quality`. If exact G1 sources are needed, perform explicit
   private read-back as described below. Missing private evidence blocks dependent
   source claims; it does not block unrelated public navigation or public work.

## Register work without duplicating authority

Use `docs/work/<stable-work-id>/`; keep the ID and location after completion or
reopening. Dates identify revisions, not a work identity that changes every session.
Use the [small template](templates/WORK.md) and [versioned format](templates/registry.schema.json).
Create an independent record for distinct ownership, scope, decisions or handoffs.
Routine edits can use their parent record and existing issue/PR evidence.

Edit `registry.json`, then run `python3 -m scripts.work_records --write-index`.
INDEX is generated; do not maintain a second manual work/status table. Each record
points to STATUS, its plan with exact byte identity and role, existing authority
sources, handoff and evidence index. Keep current delivery state in STATUS and
approval/effect in existing decision/acceptance records. Do not infer either from
`reviewed-proposal`, an active directory or a completed recovery.

One optional primary parent groups work. Use typed `depends-on`, `related-to` and
`uses-evidence-from` relationships across programs. Parent/dependency cycles fail;
reciprocal related-to links are valid. Independently governed experiments can have
their own work ID; ordinary runs remain under the owning comparison.

This version requires every registered local plan and handoff to exist in the
checkout. An unmerged plan stays on its issue branch; its parent README may link
the exact remote branch/commit and label it unavailable locally. Do not register a
missing branch-only file as a current local source. Reconcile the reviewed issue
snapshot deliberately; automatic checks detect omitted or duplicated assignments
against the pinned snapshot, not new issues created after it.

## Preserve sources and decisions during work

- Give every artifact one owner and immutable ID/revision/hash/size. Other work
  uses its ID. Preserve original-to-derived relationships; never overwrite a source
  or rename a historical evidence version to fit a new folder name.
- At a meaningful decision, save the exact user-visible instruction in appropriate
  custody and record its source coordinate, date, owner, reason, effect, constraints,
  supersession and next action. Summaries supplement exact sources.
- Preserve rejected outputs and superseded plans with their original status. Link
  immutable revisions from `history/` when needed; old evidence is not disposable.
- Preserve visible user and assistant messages when needed for continuity. Record
  source format, selection rules, covered cursor/range and omissions. Never export
  hidden reasoning, system/developer content or secrets. No automatic collection or
  complete conversation coverage is claimed by this implementation.

## Before handoff, compaction, branch changes or cleanup

Update the plan, decisions, open work and next permitted action. Refresh plan and
evidence identities in the registry and handoff. The handoff contains exactly one
`PLAN_SHA256:` and one `EVIDENCE_SHA256:` marker, binding the referenced plan and
entire evidence-index bytes. Record observed repository/source head and verification
time, not the handoff's own future commit SHA. Record what was and was not checked.
Regenerate INDEX, run public validation and applicable private read-back, and retain
results. A changed plan or evidence index invalidates the previous handoff markers.

The orchestrator owns capture and reconciliation; the project owner retains private
source custody. Before material allocation, record purpose, owner, size budget,
sensitivity, retention and recovery. This procedure grants no deletion authority.
Existing DocumentationMapV1 and CapabilityStatusV1 requirements remain separate;
work navigation does not implement their product/capability mapping contracts.

## Private storage and verification

Logical ownership is separate from physical private storage. The September plan
belongs to master-program; ten masters belong to G1. The complete private recovery
packet remains intact at the retained location in
[MIGRATION.json](working-records/MIGRATION.json). No private payload was moved to
implement navigation. Future `.evidence/stores/<store-id>/` storage must pass
ignore/tracked-file protections before copying, followed by exact read-back,
reference cutover, retained old sources/redirects and independent review.

`make work-records-quality` validates generic records and the selected
`g1-originals` profile. `make work-archive-quality` retains the exact eleven-source
and full-private-inventory verifier. New records are data; artifact-specific checks
remain separate reviewed profiles. Unknown profiles fail only when requested.

For actual private read-back, explicitly run:

```sh
python3 scripts/work_archive.py --private-root /path/to/registered-private-store
```

The path is supplied locally; never commit personal locators or raw session logs.
Public verification reports private availability NOT_CHECKED and backup UNPROVED.
Local private read-back proves readable matching bytes; it does not prove semantic
acceptance, encryption, independent custody or disaster recovery. Issue #532 retains
the independent store/backup/restore work. Ignore rules do not protect already
tracked files, so forced-tracking tests and public diff review remain required.

## Reuse in another project

Keep the same small convention: existing product authority, one stable work index,
one owner per source and a shared session/handoff procedure. Populate that project's
IDs, source inventory, authority map and verification profiles. Do not copy NarraTwin
issue numbers, G1 identities or acceptance rules as universal policy. The template
is reusable; repository-specific profile logic and integration checks remain explicit.
