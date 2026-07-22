# ADR 0032: Local Demo Refusal UX Boundary

## Status

Accepted for issue `#247`.

## Context

The Checkpoint 1 local/self-hosted demo preserves grounded-generation refusal
semantics. If Stage 4 cannot retrieve enough approved project context, the
backend returns a refused walkthrough run, for example with
`LOW_RETRIEVAL_CONFIDENCE`. That refusal is correct and must block downstream
multilingual, voice, and avatar generation.

Before issue `#247`, the frontend continued into the Stage 6 multilingual
endpoint after a refused walkthrough. The backend then correctly returned a
semantic `422`, but the user-visible demo showed the generic
`NarraTwin API request failed with 422` message instead of the safe refusal
state.

## Decision

The frontend local demo must treat any walkthrough run that is not completed
with accepted script text and evaluation evidence as non-renderable for the
demo chain. It must stop before Stage 6 or Stage 7 calls and show a bounded,
allowlisted refusal message when the backend supplies a safe refusal payload.

This preserves the backend refusal contract rather than weakening retrieval or
evaluation gates.

## Boundaries

- No hosted deployment, public URL, provider egress, paid spend, cloned
  identity, Product Mode 2, or production-readiness claim is authorized.
- The UI may display only bounded, allowlisted refusal text and must not expose
  raw prompts, raw scripts, provider payloads, media bytes, tokens, secrets,
  invite/session identifiers, or idempotency keys.
- Downstream media generation remains available only for completed, evaluated,
  grounded walkthrough runs.

## Validation

- `frontend/src/app/page.test.tsx` covers refused walkthroughs producing a safe
  visible stop reason.
- `tests/unit/test_phase1_closure_docs.py` covers the issue `#247` branch
  allowlist and rejects adjacent backend/frontend files.
- A live browser repro against the local Compose stack confirmed insufficient
  knowledge shows `Walkthrough refused:` and does not call downstream media
  endpoints.
