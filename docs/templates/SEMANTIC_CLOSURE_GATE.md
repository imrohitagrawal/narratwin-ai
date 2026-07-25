# Semantic Closure Gate

## Purpose

Use this template for any project where implementation can appear complete while
the user-visible outcome is still wrong. It is a reusable project-memory
artifact: copy it into new repositories or reference it from project bootstrap
docs before implementation begins.

Core rule:

```text
SATISFIED means product behavior proves the requirement.
It does not mean code exists, tests passed, metadata is present, or docs say done.
```

## When To Use

Use this as a default backbone for implementation architecture when the project
has any of these surfaces:

- browser-visible or app-visible behavior;
- AI, RAG, generated content, translation, summarization, evaluation, or media;
- imports, exports, reports, dashboards, documents, or derived artifacts;
- workflows where API/schema success can hide an incorrect user outcome;
- release, demo, portfolio, or production-readiness claims;
- agent-built implementation where the same agent might otherwise mark its own
  work complete.

For a future project such as Dreaming, use this from day one if the product
generates, transforms, explains, translates, recommends, or displays any
meaning-bearing output. Treat it as an architectural quality backbone, not only
as a late-stage test checklist.

## Required Memory Shape

Every non-trivial implementation slice should preserve this chain:

```text
intent -> requirement row -> failure modes -> executable verifier
-> visible observed output -> classification -> matrix/status update
```

The project memory should include:

- the intended user outcome in plain language;
- positive claims and negative invariants;
- false-pass examples that would look correct structurally but fail intent;
- the exact executable verifier command or browser flow;
- observed pass/fail evidence from the running product;
- the requirement classification;
- remaining `NOT_PROVEN` or `FAILED` rows.

## Classifications

Use these statuses in requirement matrices, PR bodies, and verifier reports:

| Status | Meaning | May Mark Requirement Satisfied? |
|---|---|---:|
| `STRUCTURAL_PASS` | The endpoint, schema, UI shell, artifact, or metadata exists. | no |
| `SEMANTIC_PASS` | The user-visible behavior satisfies the intended requirement. | yes |
| `NOT_PROVEN` | The available evidence does not prove the user-visible requirement. | no |
| `FAILED` | Executed evidence contradicts the requirement. | no |

`EXECUTABLE_CONTRACT_PASS` or similar structural statuses are not enough for
semantic, output-correctness, translation, summary, recommendation, dashboard,
document, report, or workflow-outcome requirements.

## Verifier Contract

Each implementation PR must include a post-implementation execution verifier.
It must run after implementation and execute the relevant product path end to
end. It cannot be read-only.

Minimum verifier evidence:

- starts the product through repo-supported commands;
- exercises the real user path, preferably through a browser when the feature is
  user-facing;
- captures actual network/API calls where relevant;
- inspects rendered user-visible output, not only response shape;
- verifies important negative cases and refusal/error paths;
- compares visible output with artifacts or backend state when artifacts exist;
- records deterministic pass/fail evidence and traceable report files.

Do not accept these as semantic proof:

- metadata-only evidence;
- screenshot-only evidence;
- docs-only evidence;
- matrix-only evidence;
- artifact-only evidence;
- mocked-status-only evidence;
- fixture-only happy paths that do not exercise arbitrary bounded input;
- API-only evidence for browser-visible claims.

## False-Pass Examples

Adapt this table into each project preflight:

| Area | False Pass | Required Failure |
|---|---|---|
| Multilingual output | Target text says "Local mock conversion" or repeats English operational metadata. | Fail unless the visible target text semantically converts the source clauses. |
| AI answer grounding | Answer has citation-looking tokens but cited source text does not support the claim. | Fail unsupported claim and preserve citation/source mismatch evidence. |
| Dashboard | Chart renders with correct labels but values come from stale fixtures. | Fail unless visible values reconcile with current source data. |
| Document generation | PDF exists but clauses are placeholders or omit required terms. | Fail unless generated document text satisfies the clause-level requirement. |
| Import/export | File count or row count matches but fields are transformed incorrectly. | Fail unless record-level semantic parity is proven. |
| Workflow automation | Status changes to success while side effects are skipped or simulated. | Fail unless required side effects or explicit non-goals are observed. |

## PR Body Section

Every implementation PR should include:

```markdown
## Post-implementation execution verifier

| Requirement | Classification | Executed path | Observed evidence | Negative proof |
|---|---|---|---|---|
| <requirement id/name> | SEMANTIC_PASS / STRUCTURAL_PASS / NOT_PROVEN / FAILED | <browser/API/product path actually executed> | <visible behavior and artifacts observed> | <fallbacks, templates, metadata-only proof, unsafe output, or other false-pass paths rejected> |
```

## Matrix Rule

Requirement matrices must not allow a semantic row to move to satisfied unless
the row has `SEMANTIC_PASS` evidence or an explicitly equivalent semantic pass
status backed by an execution verifier.

For rows that are only structurally complete, use `STRUCTURAL_PASS` and leave the
requirement open or explicitly mark the semantic portion `NOT_PROVEN`.

## Architecture Guidance

Use this as a default architecture backbone for new projects by making semantic
closure a first-class design component:

- define verifier hooks while designing APIs and UI states;
- make trace IDs, artifact IDs, source refs, checksums, and evaluation metadata
  visible enough for tests and reviewers to compare;
- keep mock/local/demo mode product-faithful where requirements demand user
  outcome parity;
- fail closed when bounded deterministic behavior cannot honestly satisfy the
  requested semantic transformation;
- separate structural health from semantic correctness in dashboards, status
  ledgers, and release claims.

The pattern does not guarantee zero errors. It reduces recurring gaps by making
weak evidence fail earlier and by forcing future agents to prove the claim in
the running product before updating docs or matrices.
