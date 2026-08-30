# ADR 0072: Cut 1 presenter-source integrity

- Status: proposed in Issue #466; effective only after reviewed merge
- Date: 2026-08-30
- Decision owner: Rohit Agrawal / StackClimb
- Supersedes: ADR 0058 only for shared claim 014's presenter predicate and source span

## Context

T05A expanded exact Cut 1 claim inference and narration receipts from Meera to
Myra and Raj. The atomic-facts asset carried claim hashes for all three, but
shared claim 014 still required `presenter.selected_meera` and cited only an
owner statement selecting Meera. Public persisted Myra and Raj runs therefore
returned passing source authority from evidence that contradicted their
presenter identity. Structural tests checked that proposition evidence existed,
but did not check its presenter meaning.

This false acceptance is separate from the older Issue #368 runner, which
correctly failed ordinary Stage 4 because it omitted the governed facts
projection and used style `CONFIDENT`.

## Decision

Issue #466 records an independent first-party owner assertion that Meera, Myra,
and Raj are each authorized controlled presenters for an independently bound
prepared walkthrough. The complete Issue #466 body and its exact 122-byte
authority span are pinned by revision, byte range, byte count, and SHA-256.

The governed facts asset keeps the historical Meera-only span for audit but no
longer uses it to support shared claim 014. `fact_013` instead cites the Issue
Issue #466 span and requires `presenter.governed_cut1`. The verifier code-pins the
complete proposition identity, statement, predicates, source span, and
classification in addition to the whole-asset digest. Rehashing a substituted
statement therefore cannot create authority.

All other claim mappings, repository spans, owner assertions, ordinary Stage 4
direct-support behavior, canonical presenter inference, narration lifecycle,
and T05B admission remain unchanged.

## Security and privacy consequences

- Owner evidence is first-party authority, not external corroboration.
- The issue body is not fetched at runtime; reviewed bytes are represented only
  in the bounded policy asset and code pins.
- Uploaded narration, caller proposition metadata, cross-presenter state,
  stale receipts, and coherently rehashed substitutions remain untrusted.
- No credentials, network lookup, provider call, narration egress, spend,
  synthesis, or media generation is introduced.

## Alternatives rejected

- Keep the Meera-only source for Myra/Raj: contradictory false acceptance.
- Infer authorization from passing code or tests: output is not source truth.
- Copy canonical narration into a source: circular self-grounding.
- Weaken generic Stage 4 support: expands risk outside Cut 1.
- Create presenter receipts before correction: preserves invalid lineage.

## Limits

This decision proves only truthful controlled-presenter source binding for the
existing canonical narration contract. It does not prove audio existence,
spoken-word accuracy, listening acceptance, captions, rendered media, public
rights, deployment, release, production readiness, or Cut 1 acceptance.
