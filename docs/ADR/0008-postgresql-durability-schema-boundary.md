# ADR 0008: PostgreSQL Durability Boundary for Issue #39

## Status

Accepted for planning in Phase 1 Closure Context 1 (`#65`), advisory only.

## Date

2026-07-10

## Context

Issue `#39` remains open because production-grade durability and monitoring are
still missing. Context 1 must define a schema boundary and durable state model for
production metadata before implementation contexts begin.

The repository already treats local durability and restart-recovery as JSON-backed,
non-production semantics. Context 1 is the transition to an advisory production
durability design that can be handed to implementation-ready contexts without
bringing runtime behavior into this issue.

## Decision

NarraTwin AI uses PostgreSQL as the durable metadata boundary for production
durability once the product advances into implementation contexts.

### PostgreSQL as durability boundary

- PostgreSQL provides transactional ACID behavior, row-level locking, and
  uniqueness constraints needed for deterministic compare-and-set (CAS)-style write
  control.
- Production entities in scope for this ADR are modeled with durable identifiers,
  explicit version counters, and terminal-state transitions.
- PostgreSQL-backed state is the source of truth for production claims and audit
  review, not local snapshots.

### Schema boundary (durable vs non-durable)

#### In-boundary (PostgreSQL durable)

- `project`
- `document`
- `chunk`
- `run`
- `evaluation`
- `project_state_transition` and `run_replay_event` audit linkage

These entities are the minimum production surface for `DUR-STAGE4-001` and are
owned by storage/API interoperability requirements.

#### Out-of-boundary (non-production durable scope / externalized or local-only for this issue)

- raw uploaded files, parsed text buffers, and temporary extraction artifacts
- provider prompts, provider outputs, transcripts, and generated outputs
- generated script/translation/audio/artifact payloads and signed download metadata
- local-file snapshots from `NARRATWIN_STATE_DIR`
- queue/lease/outbox rows (deferred to later contexts)

No table definitions, DDL, migration scripts, or query implementation are added
in this context.

### ACID/CAS durability model (`DUR-ACID-001`)

All boundary rows share a minimal invariant schema envelope:

| Column | Purpose |
|---|---|
| `id` | Durable entity ID, stable across retries |
| `tenant_id`, `owner_id`, `project_id` | Authorization scope fields carried into durable review |
| `state` | Explicit state machine status (`Open`/`Terminal`/`Error`) |
| `version` | Monotonic integer version for compare-and-set operations |
| `request_id` | Idempotency/operation identity for replay correlation |
| `terminal_state` | Terminal marker with reason and timestamp |

Replay and CAS rules:

1. A state transition must specify the expected previous `version`.
2. If the current `version` does not match, the write is rejected as conflict.
3. Conflict responses require replay to fetch the latest state before re-issue.
4. Once `state = Terminal`, replay must be read-only for non-recovery paths.
5. `Error` is terminal until explicit recovery handoff; repair requires a
   new durable operation sequence outside this context.

Conflict example:

- `run#A` is currently `state=Processing`, `version=5`.
- Worker 1 proposes `Processing -> Terminal/success`, expected version `5`.
- Worker 2 simultaneously proposes `Processing -> Terminal/failed`, expected version
  `5`.
- First commit wins and increments version to `6`.
- Second commit is rejected with CAS conflict and must replay from version `6`.

### Replay-safe state machine (`DUR-STAGE4-001`)

#### Open / Terminal / Error conventions

| State | Allowed transitions |
|---|---|
| `Open` | `Terminal`, `Error` |
| `Terminal` | terminal (read-only unless explicit migration/repair path) |
| `Error` | terminal (read-only until approved recovery path) |

#### Entity state expectations

- `project`: Open, Terminal, Error
- `document`: Open, Ingesting, Terminal, Error
- `chunk`: Open, Indexed, Terminal, Error
- `run`: Open, Processing, Terminal, Error
- `evaluation`: Open, Scored, Terminal, Error

Replay-safe behavior:

- A repeated request with same durable identifiers and same `request_id` must
  either re-enter the same terminal state or produce a conflict with latest
  durable state.
- Non-terminal replay attempts are allowed only within explicit operation windows;
  non-deterministic side effects (for example provider calls) are deferred to
  later contexts.
- Durable state transition events are append-only; only current state plus
  transition metadata are part of the required boundary for this context.

### Deferred areas

The following are **explicitly deferred**:

- SQL DDL and migrations.
- Foreign-key and indexing finalization.
- Backend persistence runtime code, repository migrations, worker lease/outbox
  logic, API transaction boundaries, provider adapter changes, and runtime
  initialization.
- Backup/restore, rollback, and monitoring implementation wiring.

### Schema ownership and migration expectations

Ownership split for this boundary:

- This ADR defines the durable entity boundary and state-transition contract.
- The implementation context that introduces persistence code owns concrete
  migration sequencing and forward-compatible schema evolution.
- Any migration plan must preserve existing transition invariants, require
  backward-compatible reads/writes for one deploy window, and document rollback
  expectations before implementation starts.

### Security/privacy and untrusted-input handling

- Uploaded documents, prompts, provider outputs, transcripts, and generated output
  fragments remain **untrusted** at the boundary until validated by explicit
  review-time controls.
- Storage contracts should treat these values as tainted:
  - strict size and encoding checks
  - prompt-injection and retrieval-poisoning controls before use
  - schema-level redaction of secrets/tokens in durable logs/metrics
  - replay validation paths that re-run untrusted-input checks
- Consent, provenance, deletion, retention, and legal review tables are
  out-of-scope for Context 1 and must be owned by later implementation stages.

### Observability and audit expectations

For each durable transition, systems should produce:

- state transition record (entity, prior version, next version, actor, request id)
- conflict outcome (`conflict`, `ignored`, `replayed`, `terminal`) with reason
- replay count and terminalization path for operations that reach `Error` or
  `Terminal`

These records support residual `DUR-ACID-001` replay checks and production
evidence for `DUR-STAGE4-001` conflict handling.

### Local/dev/test posture

- Local/dev/test continue to use optional file-backed local state as documented in
  existing issue `#39` Context 0 artifacts.
- Production PostgreSQL boundary ownership does not imply active local `main`-line
  runtime behavior change in this issue.
- External paid providers remain optional and disabled by default outside explicit
  production enablement; this issue does not enable any provider runtime.

## Alternatives Considered

### Keep local file state as production metadata for all stages

Rejected. Local snapshots support recovery for local demos but do not provide
ACID/CAS semantics, replay-safe conflict handling, or shared concurrent-worker
durability guarantees required by `DUR-ACID-001` and `DUR-STAGE4-001`.

### Use a different RDBMS vendor in this boundary

Deferred. Multiple vendors may be valid in architecture, but the current product
context requires a deterministic PostgreSQL-compatible boundary to align with
existing guardrails and operational runbooks.

## Consequences

Positive:

- Issue `#65` provides a concrete, reviewable schema boundary contract for
  production durability work without changing runtime.
- `DUR-ACID-001` and `DUR-STAGE4-001` now have an explicit, conflict-aware
  state surface and replay model.
- Future runtime contexts can implement migration and replay logic against a
  documented contract instead of ad-hoc assumptions.

Negative:

- No production implementation evidence is produced in this issue.
- The contract does not itself satisfy any of the production go-live gates.

## Related Documents

- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
