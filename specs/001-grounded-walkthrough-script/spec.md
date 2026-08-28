# Specification: Lane A Cut 1 Presenter Path

Status: Issue #16 governance gate; no implementation authority
Future mapping: Lane A Cut 1 issue created only after Issue #16 merges and closes

## Objective

Specify the Lane A Cut 1 path that consumes the existing approved grounded
walkthrough script and evidence lineage to produce an independently reviewable,
controlled-local, human-like presenter explanation. Meera is primary; Raj and
Myra are governed fallbacks. This specification neither reimplements existing
Stage 4 behavior nor authorizes product, provider, or media mutation.

## Authoritative sources and precedence

1. `docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` defines presenter and
   Cut 1/Cut 2 boundaries.
2. `docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md` defines grounding and AI quality.
3. `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md` defines exact Cut 1 metrics.
4. `docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md` defines executable acceptance.
5. `docs/PRD.md` and `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` define inherited
   grounded-walkthrough requirements.
6. Architecture, API, data, security/privacy, observability, and current status
   documents constrain any later issue; this spec does not amend them.

Current sources override historical product-mode or issue prose. Issue #450 is
planning authority only. Issue #435 is closed and separate. Issue #456 merged
through PR #457 at `6f2bfebf794ca6263b6cb42f65bbdc8328cc8e5a`.

## Users and use cases

1. A reviewer runs a local Meera-led explanation built from the approved,
   checksum-bound script, source references, evaluation, voice, captions,
   presenter identity, and configuration.
2. A reviewer independently inspects each Meera/Raj/Myra × English ×
   landscape/portrait cell without pooled masking.
3. A user follows a keyboard-accessible path with captions, reduced motion,
   visible evidence, safe failures, and truthful limitations.
4. An abuse actor substitutes sources, evidence, identity, media, provider
   output, or approval; the system rejects the mismatch.

## Inherited grounded-walkthrough prerequisites

These retain their meanings from `docs/PRD.md`. They are accepted inputs and
prerequisites, not authority to rebuild or broaden existing behavior.

| ID | Prerequisite |
|---|---|
| FR-001 | Stable project creation and selection. |
| FR-002 | Approved markdown/text project knowledge upload. |
| FR-003 | Type, filename, size, path, and content validation. |
| FR-004 | Deterministic ingest/chunk/source metadata. |
| FR-005 | Project-scoped retrieval. |
| FR-006 | Audience/depth/style/requested-language grounded script generation. |
| FR-007 | Context references for project-specific claims. |
| FR-008 | Unsupported-claim and insufficient-context evaluation. |
| FR-009 | Uploaded-content prompt-injection neutralization. |

| ID | Prerequisite |
|---|---|
| NFR-001 | Local/dev/test/CI requires no paid provider. |
| NFR-002 | No committed secrets or credentials. |
| NFR-003 | Future provider keys use environment-backed configuration only. |
| NFR-004 | Source, prompt, filename, transcript, model/provider output is untrusted. |
| NFR-005 | Output carries run metadata and context references. |
| NFR-006 | Evaluation failures block merge once evaluation exists. |
| NFR-007 | Reproduced critical/high security findings block merge. |
| NFR-008 | Architecture-impacting work updates ADRs. |
| NFR-009 | Requirement-impacting work updates traceability. |
| NFR-010 | New third-party tools/providers/models/data/media update notices. |
| NFR-011 | Future public avatar/voice follows canonical disclosure/consent policy. |
| NFR-012 | Provider mode and cost posture are traceable per run. |

## Lane A requirements

| ID | Requirement |
|---|---|
| LA-C1-R01 | Consume only approved, checksum-bound script, source, evaluation, narration, presenter, and configuration lineage. |
| LA-C1-R02 | Preserve Meera-primary, Raj-first-backup, Myra-second-backup order and reject unauthorized identity substitution. |
| LA-C1-R03 | Keep six presenter × English × landscape/portrait cells independent; no aggregate hides a failed cell or severe defect. |
| LA-C1-R04 | Enforce governed framing, gaze, identity continuity, motion, lip synchronization, captions, and gesture quality. |
| LA-C1-R05 | Keep claims source-bound, unsupported cases abstaining, and evaluation/current-source lineage fail-closed. |
| LA-C1-R06 | Preserve originals; derivatives require separate provenance, permitted-use, consent/privacy, deletion, and checksum authority. |
| LA-C1-R07 | Provide keyboard, caption, contrast, reduced-motion, readable-error, and evidence-inspection behavior. |
| LA-C1-R08 | Bind artifacts/manifests to run, source, evaluation, presenter, audio, caption, aspect, provider posture, and checksums. |
| LA-C1-R09 | Default to local/key-free/provider-disabled; credentials, egress, spend, provider or human study require separate authority. |
| LA-C1-R10 | Reject placeholder media, missing/non-regular/substituted artifacts, stale/replayed approval, malformed output, or incomplete evidence. |

## Exact Cut 1 metrics

`C1-M01` through `C1-M10` are incorporated without restatement from
`docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md` and
`docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md`. A future issue must test their exact
current thresholds and six-cell evidence. Source drift stops work and requires
contract rebinding before implementation.

## Positive acceptance

1. A controlled-local run consumes exact approved lineage and produces
   separately inspectable landscape/portrait evidence plus a reproducible
   manifest without external provider calls or spend.
2. Every one of six cells independently satisfies all applicable canonical
   metric rows and severe-defect rules; no pooled result substitutes for a cell.
3. Reviewer can inspect grounding, abstention, identity, motion, audio, captions,
   provider posture, provenance, checksums, limitations, and safe failure through
   an accessible path.

## Negative and prohibited behavior

- Unsupported claims, missing/pooled cells, placeholder success, unapproved
  derivatives, lineage substitution, stale approval, malformed output, severe
  defects, or incomplete evidence cannot pass.
- No real provider, credential, egress, spend, human study, new likeness,
  unrestricted Q&A, Cut 2+ scope, deployment, public hosting/distribution,
  release, or production-readiness behavior is authorized here.
- No Lane A issue or branch exists before Issue #16 merges and closes.

## Security, privacy, observability, and cost

Treat all inputs and derived artifacts as untrusted. Preserve request/run/trace,
source/script/evaluation, presenter/asset, audio/caption, aspect, artifact/
manifest checksum, metric, provider mode, duration, error/refusal,
consent/provenance and zero-cost posture. Bound/redact logs; exclude raw private
sources, prompts, credentials, biometric data and provider payloads. Enforce
tenant/project isolation, safe output encoding, deletion/retention boundaries,
and explicit authority for likeness, voice, provider and study decisions.

## Accessibility and performance

Apply the exact canonical accessibility and performance metrics by reference.
Issue #16 reviews Markdown semantics and task feasibility only; runtime evidence
belongs to the future issue using the governed measurement topology.

## Acceptance commands

```text
make issue16-spec-quality
uv run pytest -q tests/unit/test_issue16_spec_kit_gate.py tests/unit/test_quality_dispatcher.py
python3 scripts/guardrails_check.py
NARRATWIN_POLICY_ONLY=1 make quality
make quality
```

Hosted required checks and `pr-body-consistency` must pass on the final exact
head. Commands do not replace semantic review.

## Success and stop conditions

Pass when requirements map to dependency-ordered tasks/evidence, exact gate
mutations fail, reviewers find no unresolved reproduced blocker, and product
work stays blocked. Stop for authority/source drift, unapproved dependency,
provider/data/asset scope, missing negative evidence, path/budget breach, or a
decision needing owner authority, credentials, spending, deployment,
consent/provenance, legal, or destructive action.

## Known limitations

This gate proves specification structure, not runtime/media behavior. Existing
grounded-script behavior is prerequisite input. Meera remains conditional and
Raj/Myra remain `NOT_READY` for hands-visible scoring until separately
authorized derivative evidence exists. Provider selection, real media, required
human study, interactive Q&A, multilingual quality, hosted/public operation,
production durability, release readiness, and human acceptance remain separate.
