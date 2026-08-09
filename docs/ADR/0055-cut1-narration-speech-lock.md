# ADR 0055: Cut 1 narration speech lock

- Status: Proposed in Issue #382; effective only after merged-main acceptance
- Date: 2026-08-08
- Amended: 2026-08-09 by OWNER comment `5229508771`
- Decision owners: Rohit Agrawal / StackClimb
- Depends on: ADR 0054 and accepted Stage 4 evaluation lineage

## Context

Cut 1 needs one reviewable narration authority between a passing grounded Stage
4 run and later local English speech. A passing generation alone cannot authorize
speech: text may be edited, presenter identity may change or be revoked, evidence
may become stale, and visible citations must not be spoken.

## Decision

`backend.app.narration` owns an isolated, controlled-local lifecycle:

`DRAFT → EVALUATION_REQUIRED → EVALUATED → APPROVED_FOR_SPEECH → CONSUMED_BY_TTS`

Each immutable content version binds tenant, actor, project, presenter and full
ADR-0054 registry binding, exact review/spoken bytes, Stage 4 run/request/trace,
the canonical evaluation-lineage JSON and checksum, contexts, citation indexes,
claim supports, and the downstream 90–120-second measured-audio requirement.
Narration evaluation and explicit speech approval extend that checksum chain.
Consumption is a single-use text-authority receipt; it is not audio.

Meera uses comment `5197711390` with only the opening superseded by OWNER comment
`5229508771`: she welcomes everyone as the NarraTwin host, without a spoken
synthetic-presenter introduction. Myra and Raj replace exactly the two `Meera`
tokens. Visible validated citation markers remain in
review data and only those markers are removed from spoken text. The canonical
NarraTwin project requires the exact presenter text. Another project must retain
the StackClimb envelope, name its current project, and match its own passing
Stage 4 evidence.

Every edit creates the next `DRAFT` and binds invalidation of the prior version
and checksum for evaluation, speech approval, TTS/audio, caption, render,
video/export, and replay. One lock serializes edit/evaluate/approve/consume.

Optional JSON persistence uses the existing atomic writer but performs its own
4 MiB bounded binary read, strict UTF-8 and duplicate-key parsing, exact fields,
count/type/checksum/time validation, live Stage 4/registry reconciliation, and
exact equality between consumed-version and validated-receipt keys. Any missing
receipt, detached receipt, malformed, or stale snapshot restores no authority.

## Consequences and limits

- Issue #368 receives only current approved spoken text plus a fully bound
  receipt. It must independently generate and measure real audio.
- No API/UI, TTS/audio, provider/network/dependency, Stage 4/6 mutation,
  renderer/media, cloning/likeness, deployment, publication, release, public,
  or production capability is added.
- This local in-process store is not a multi-node transaction protocol. Cloud,
  multi-user, retention, or external approval roles require later authority.
