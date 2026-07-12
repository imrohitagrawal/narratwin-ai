# Issue #125 Local Restore Drill Preflight

## Scope

- Issue: `#125`
- Branch: `phase-1-closure-39-restore-local-drill`
- Matrix ID: `DUR-RESTORE-001`
- Parent issue `#39` remains open and reference-only.

## Intent

Define the narrowest executable local restore-integrity drill the repo can
honestly support now for the existing file-backed Stage 4/6/7 state paths.

## Non-Goals

- No production-like `CH-14` restore proof.
- No backup platform, snapshot, or database-managed restore claim.
- No restore metrics, SLO, alert, dashboard, or first-hour watch closure.
- No retention, re-delete, rollback comms, provenance/disclosure, provider
  posture, or untrusted-input closure.

## Source Facts

- `docs/ADR/0011-context4-backup-restore-drill.md` defines the production
  planning-only restore contract and keeps runtime proof deferred.
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` keeps `CH-14` as the later
  production-like restore drill for `DUR-RESTORE-001`.
- The current repo already exposes optional file-backed Stage 4/6/7 state,
  which is the only executable restore surface in scope for `#125`.

## Invariant / Failure Matrix

| Matrix ID | Type | Invariant / failure mode | Coverage |
|---|---|---|---|
| `RESTORE-LOCAL-INV-001` | Positive invariant | Stage 4 replay must reissue the same idempotent `create_project`, `upload_document`, `approve_document`, `ingest_documents`, and `generate_walkthrough` operations after restore and return the original durable identifiers. | `tests/unit/test_local_restore_drill.py::test_local_restore_drill_replays_restored_state_without_new_ids` |
| `RESTORE-LOCAL-INV-002` | Positive invariant | Stage 6 replay must return the original multilingual run identifier and must not create new durable Stage 6 rows after restore. | `tests/unit/test_local_restore_drill.py::test_local_restore_drill_replays_restored_state_without_new_ids` |
| `RESTORE-LOCAL-INV-003` | Positive invariant | Stage 7 replay must return the original consent and render identifiers and must not create new durable Stage 7 rows after restore. | `tests/unit/test_local_restore_drill.py::test_local_restore_drill_replays_restored_state_without_new_ids` |
| `RESTORE-LOCAL-INV-004` | Positive invariant | Source and restored state files must stay byte-identical and the persisted evidence paths must remain readable after the drill exits. | `tests/unit/test_local_restore_drill.py::test_local_restore_drill_replays_restored_state_without_new_ids`; `tests/unit/test_local_restore_drill.py::test_local_restore_drill_writes_json_summary` |
| `RESTORE-LOCAL-INV-005` | Negative invariant | Replay must not silently increase Stage 4/6/7 durable record counts after restore. | `tests/unit/test_local_restore_drill.py::test_local_restore_drill_replays_restored_state_without_new_ids` |
| `RESTORE-LOCAL-NONGOAL-001` | Non-goal | Production backup tooling, restore metrics, RTO/RPO proof, retention/re-delete behavior, and operations/security signoff are intentionally out of scope. | `docs/ADR/0023-local-restore-integrity-drill.md`; `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` |

## Old-Behavior Proof

- Old behavior failed the intended contract because the drill replayed only
  Stage 4 project creation and walkthrough generation, so upload/approve/ingest
  restore idempotency could regress without failing the drill.
- Old behavior also emitted evidence paths from a temporary directory that was
  deleted before the command returned, weakening reviewer validation.
- Old behavior also skipped post-replay count verification, so duplicate
  idempotency or artifact rows could slip through while the returned IDs still
  matched.

## Review Prompt Set

1. Adversarial review prompt: prove or disprove that every claimed Stage 4/6/7
   replay invariant is exercised by the drill, not just described by the ADR.
2. False-close prompt: prove or disprove that any changed wording could be read
   as production restore evidence for `#39` or `CH-14`.
3. Evidence prompt: prove or disprove that the emitted JSON evidence remains
   inspectable after the command exits.

## Independent Review Disposition

- Independent adversarial sub-agent review found that the original drill
  over-claimed Stage 4 replay coverage because upload/approve/ingest replay was
  not exercised.
- Independent code-review-skill sub-agent review found that the original JSON
  summary pointed at deleted temporary paths and lacked post-replay count
  verification.
- This branch resolves those blocker classes by replaying the full Stage 4
  create/upload/approve/ingest/generate path, asserting post-replay count
  stability, and persisting inspectable evidence paths.

## Stop Rule

If review finds a new blocker class where the executable drill and the written
contract diverge again, stop the fix loop, rewrite this matrix and the review
prompts for the missing invariant, then continue implementation from the updated
contract instead of stacking another narrow patch.

## Skill / Tool Selection

- Checked repo docs first: `docs/AI_BUILD_BRIEF.md`, `docs/STATUS.md`,
  `docs/REPOSITORY_GUARDRAILS.md`, `docs/STAGE_ISSUE_PLAN.md`,
  `docs/ENGINEERING_PROCESS_RCA.md`, and
  `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`.
- Checked approved review tooling first: repo-approved sub-agent review and the
  active `code-review-and-quality` skill.
- No custom skill or plugin was created or installed for issue `#125`.
