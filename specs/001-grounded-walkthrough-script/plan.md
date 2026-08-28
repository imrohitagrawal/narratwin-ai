# Plan: Lane A Cut 1 Presenter Path

Status: specification-only; implementation blocked
Gate order: constitution -> spec -> plan -> tasks -> review checkpoint -> future issue
Invariant: `I16.PLAN.ORDER`.

## Planning decision

Use a vertical presenter slice that consumes rather than reimplements the
approved grounded script and lineage. Keep execution local/key-free and
provider-neutral until separately authorized. The future issue starts from
then-current accepted `main` and freezes exact sources, presenter cells, paths,
budgets, metrics, and human-only decisions before code.

## Dependency graph

```text
#440 / PR #443 canonical product contracts
  -> #452 / PR #455 presenter acceptance contract
    -> #456 / PR #457 live binding at 6f2bfebf794ca6263b6cb42f65bbdc8328cc8e5a
      -> Issue #16 merge and closeout
        -> create future Lane A Cut 1 issue and branch
          -> freeze exact RED corpus, sources, cells, paths and budgets
            -> provenance-bound derivatives and controlled executor
              -> narration/audio/caption/grounding lineage
                -> six independently reviewable artifacts
                  -> accessible reviewer path and exact-metric evidence
                    -> full evidence and independent review
```

Issue #435 is closed/separate, not a dependency. Issue #450 supplies planning
authority only and grants no mutation. Each boundary consumes only evidence
accepted by its predecessor.

## Future project structure

Exact future paths are frozen by the later preflight. Likely owning domains are
backend provider-neutral execution, focused unit/integration/API tests,
frontend reviewer UI/browser tests, eval/media fixtures, governed assets and
manifests, and docs/ADR/traceability evidence. This is orientation, not path
authority.

## Implementation phases

1. Freeze future issue authority, current source identities, six-cell matrix,
   metric bindings, paths/budgets, commands, invariant/failure matrix, and
   human-only decisions.
2. RED: prove missing/pooled cells, lineage substitution, stale approval,
   placeholder media, corruption, unsupported claims, severe defects,
   credential/egress/spend attempts, and accessibility failures cannot pass.
3. GREEN foundation: authorized provenance-bound derivatives plus controlled,
   provider-neutral local/key-free executor.
4. GREEN outcome: narration/audio/caption/grounding binding, six independently
   reviewable artifacts, accessible reviewer path, and exact metric evidence.
5. Refactor only while focused/full evidence remains green.
6. Run security/privacy, exact-artifact evaluation, accessibility, performance,
   governance, hosted and independent exact-head review gates.

## Testing strategy

- Unit: schema/manifest, lineage, cell independence, artifact identity, state.
- Integration: controlled executor, atomicity/idempotency, disabled provider,
  bounded error and complete metadata.
- Component/browser: evidence, captions, keyboard/reduced motion, safe retries.
- Media/performance: governed local path and canonical measurement topology.
- Mutation: swap lineage, omit cell, pool scores, substitute assets, corrupt
  artifacts, replay approval, expose credential, attempt egress/spend, or weaken
  metric binding.

Use real deterministic local implementations, fakes at external boundaries, no
paid provider, credential, external network, or unauthorized human study.

## Security and privacy

Validate every untrusted source/artifact; enforce project/tenant isolation,
bounded parsing/storage/logging, safe output encoding, provenance/consent,
retention/deletion, exact lineage, and fail-closed provider/credential/egress/
spend controls. Legal, regional-processing, likeness, voice, or public-use
decisions require separate owner authority.

## Observability and cost

Carry request/run/trace, source/script/evaluation, presenter/asset, audio/
caption, aspect, artifact/manifest checksum, metric, provider, duration,
error/refusal, provenance and cost posture. Logs exclude raw sources, prompts,
credentials, biometric data, personal data and provider payloads. Local/key-free
runs prove zero calls and zero spend.

## Accessibility and performance

Apply canonical Cut 1 metric rows without restatement. Define accessible
semantics and keyboard/reduced-motion tests alongside UI behavior. The future
issue binds exact environment, fixture, sample, warmup and measurement rules.

## Checkpoints

- A: future issue/preflight, sources and RED matrix accepted before code.
- B: derivative provenance and controlled-executor security review pass.
- C: each cell's artifact/lineage and fail-closed mutations pass.
- D: reviewer path, exact metrics, full gates, hosted checks and independent
  exact-head approvals pass.

## Issue #16 commands

```text
make issue16-spec-quality
uv run pytest -q tests/unit/test_issue16_spec_kit_gate.py tests/unit/test_quality_dispatcher.py
python3 scripts/guardrails_check.py
NARRATWIN_POLICY_ONLY=1 make quality
make quality
```

Future commands are copied from then-current canonical quality docs into the
separately authorized issue; they are not activated here.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Historical authority confusion | Current precedence and exact future preflight. |
| Pooled false success | Six independent cells and severe-defect fail-close. |
| Source/media substitution | Checksum-bound lineage and mutations. |
| Provider/spend creep | Local/key-free default; separate activation authority. |
| Privacy/provenance gap | Explicit derivative, consent, deletion and permitted-use gate. |
| Review validates prose only | Executable matrix, hosted gates and exact-head review. |

## Completion boundary

This plan completes only the Issue #16 gate. After merge/closure, create one
separate Lane A Cut 1 implementation issue, copy LA-C1-T01 through LA-C1-T08 and
all stop conditions into it, then create its branch from accepted main.
