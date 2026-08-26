# Adversarial Convergence Framework v1

Issue #435 defines a finite, offline governance framework. It does not define
the threat model for every NarraTwin feature, prove a product slice, activate a
provider, or authorize release. Activation is `NONE`, authority effect is
`NO_AUTHORITY_EFFECT`, and release posture remains No-Go.

The controlling OWNER amendment is
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5416186961>.
The one-time materialized-corpus correction is authorized by
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5421421524>.
The blocked candidate findings and exact bounded H3 replan are authorized by
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5422439650>.
The preserved-H4 additive H5 budget correction is authorized by
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5424570808>.
The exact three-root H6 validation correction is authorized by
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5425499794>.
The final C4 false-acceptance recovery is authorized by <https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5428186737>.
Hosted detached recovery is authorized by `issuecomment-5429174756`, additive correction `issuecomment-5429198021`, direct-head closure `issuecomment-5430095513`, and omitted-head closure `issuecomment-5430474392`.
The framework branch starts at
`a6284f7d8f1a14ef4c9a99493d6b06046505f20c`. C1 is preserved at
`205c02b3bac633d023d753356bc966c194ed36a7`; its preflight blob must remain
`c554eaf7f73ea081434b1e2f818441fe0bc3eee9`.

## Ownership boundary

Framework v1 owns:

- a closed vocabulary, schema, bounded parser, and deterministic stage order;
- typed findings, verdicts, observations, mutation receipts, and review states;
- stimulus/expectation separation and generic validation of a supplied matrix;
- route, budget, checkpoint, review, RED-freeze, and stop rules;
- a small framework-only adversarial corpus and test harness.

Each future slice owns its domain threats, invariants, lifecycle and trust
semantics, stimuli, independently fixed expected outcomes, evidence sources,
mutants, budgets, acceptance thresholds, and reviewers. A slice cannot cite
this framework as proof that its matrix is complete.

## Closed framework threat universe

| ID | Threat | Required framework response |
|---|---|---|
| ACP-T01 | Unsafe filesystem input | Descriptor-relative, no-follow, bounded regular-file access or typed rejection. |
| ACP-T02 | Malformed or excessive JSON | Identity before parse; reject invalid UTF-8, duplicates, malformed input, depth, work, and byte excess. |
| ACP-T03 | Schema drift | Closed versions and members; missing, unknown, or expanded vocabulary fails. |
| ACP-T04 | Pipeline predecessor violation | Every stage requires the complete earlier-stage prefix; rejection prevents later callbacks. |
| ACP-T05 | Generic or subset outcome | Compare exact ordered findings and verdicts; generic success is not evidence. |
| ACP-T06 | Unexecuted mutant | A declaration is not a receipt; execution count one and a named killing assertion are required. |
| ACP-T07 | Fabricated mock ledger | Candidate, order, count, phase, and observed result must match the independent ledger. |
| ACP-T08 | Forged review evidence | Candidate authors cannot review themselves; four roles bind one head/tree and durable sources. |
| ACP-T09 | Implementation-derived expectation | Corpus carries stimuli only; tests own expectations; executor receives one materialized stimulus. |
| ACP-T10 | Route, identity, or budget drift | Exact branch/base/path/mode/history/blob and additions-plus-deletions caps fail closed. |
| ACP-T11 | False checkpoint | Missing, stale, substituted, or prematurely passing checkpoint state is invalid. |
| ACP-T12 | Platform, import, or resource failure | Contain failures as typed results; no exception, platform-root, or import-collision credit. |

Adding a thirteenth threat, a new path, a cap, or a semantic invariant stops the
route for OWNER rescope. Future domain threats belong to the future slice.

## Deterministic processing order

1. `BOUNDS`
2. `PARSE`
3. `SCHEMA`
4. `CANONICAL_IDENTITY`
5. `INDEPENDENT_TRUST`
6. `AUTHORIZATION`
7. `GRAPH_CONFLICT`
8. `PHASE_VERDICT`

Each observation records its stage, state, callback count, justification, and
finding codes. A rejected stage makes every later stage `NOT_REACHED` with
callback count zero. `NOT_APPLICABLE` requires a nonempty justification.
Findings sort by stage ordinal, JSON-pointer location, then code.

## Corpus and expectation boundary

The C2 corpus is `ACP-FRAMEWORK-CASES-V1-N40`, exactly 40 ordered cases
`ACP-C001` through `ACP-C040`, and only ACP-T01 through ACP-T12. Its records
contain exactly `caseId`, `threatId`, `testClass`, and `stimulus`. They contain
no expected finding, verdict, review PASS, mutation success, or completion
claim.

Semantic identity is:

```text
SHA256(
  b"NARRATWIN-ADVERSARIAL-CONVERGENCE-CASES-V1\0"
  + strict_canonical_json(parsed_corpus)
)
= 3b2a0c4b3b13cf6ab71ec4e7a3dd4e3566a0c8195e3c7bed6bf956575e5f9fc6
```

Canonical JSON uses UTF-8/ASCII-safe output, sorted keys, `(',', ':')`
separators, and no NaN. Raw corpus SHA-256 is
`59581f0530b9b56b68e9bfc313497b22d1be2ce371d0cb2c64ea2b3c01dc6a75`.
The materialized corpus is 18,821 bytes, below the 48 KiB target and 64 KiB
hard cap. It has no `variant` labels. Twelve test-owned held-out transforms
prevent the reproduced fixed-label lookup bypass without increasing N=40.

`tests/unit/test_adversarial_convergence.py` owns the literal expected result
for every case. Production code neither imports that test nor receives a case
ID, threat ID, class, expectation, or corpus object during execution.

## C2 RED and mutation evidence

C2 intentionally exposes one callable `execute(stimulus)`. Its typed result is
`ACP.NOT_IMPLEMENTED`, `NOT_IMPLEMENTED`, blocker `IMPLEMENTATION`, activation
`NONE`, and authority effect `NO_AUTHORITY_EFFECT`. The 40 future-behavior
tests therefore fail by exact result mismatch, not import, collection, setup,
skip, xfail, or missing-callable behavior.

Twelve separately named test-only mutant executors each model one ACP-T01 to
ACP-T12 defect. Each receives only a stimulus, executes exactly once, differs
from the test-owned expectation, and is killed only when the same named literal
assertion used for acceptance is caught. The measured call count and caught
assertion are the evidence; candidate-authored receipt synthesis is forbidden.
This proves C2 assertion discrimination. It is not a claim that the
unimplemented production executor has passed mutation testing; C4 must make
the real executor satisfy the frozen 40 expectations without changing them.

## Safe input contract

- Reject absolute paths, parent components, empty components, and unsupported
  no-follow platforms.
- Open the trusted root and every descendant descriptor-relative with
  `O_NOFOLLOW`; the final descriptor is nonblocking and must be regular.
- Check device, inode, size, byte cap, complete read, replacement, and short
  read before parsing.
- Verify the supplied whole-file SHA-256 before UTF-8 decoding or JSON parsing.
- Reject duplicate members before overwrite and contain decode, recursion,
  member-work, resource, import, and OS failures as typed findings.
- Use no network, provider, credential, private key, shell, database, or write
  capability.

## Route and phase contract

- C1 changes only the preflight and is immutable afterward.
- C2 cumulatively changes all 19 non-freeze paths and contains no freeze file.
- The additive recovery preserves prior C3/C4 as rejected history, removes that freeze from the new C2 tree, and appends C3/C4 without history rewriting or force push.
- Four independent reviews bind one exact C2 head/tree while candidate review
  state remains `PENDING_EXTERNAL_REVIEW`.
- Only OWNER-enumerated corrections may occur before C3. H3 follows preserved
  blocked head `134fbd9`; H4 follows preserved blocked H3 head `6d741ae` and is
  limited to schema-value parity, exact PASS grammar, and Git-derived author
  exclusion. H5 preserves H4 `9bd0a27` and only restores the pre-review budget
  gate; H6 preserves H5 `6b681b4` and only closes JSON identity types, canonical
  identities, and distinct receipt URLs. Architecture closeout preserves H6
  `7a17fe3` and changes only the two infeasible caps. All four reviews rerun.
- C3 adds only `adversarial-convergence-red-freeze-v1.json` and binds the C2
  objects, corpus identities, protected-source digest, dispatcher, acceptance
  test, schema, guardrail, skeleton, and four durable review receipts.
- C4 changes only bytes inside the marked executor region of
  `scripts/quality/adversarial_convergence.py`; every byte outside it remains
  bound to C2. The region is at most 240 physical lines; final module projection is at most 790/900, below the 810-line stop.
- No correction follows C3. A required C4 finding stops for OWNER disposition.

The exact dispatcher routes only
`governance-435-adversarial-convergence-framework-v1` to the C2-frozen pytest
acceptance file. Lookalikes receive no authority, and the mutable worker CLI
cannot declare repository GREEN. Worker exits are diagnostic:

On GitHub, ambient `HEAD` is untrusted; the route selects the candidate only from a detached two-parent merge with exact ordered base/head parents, an exact detached event head whose canonical base is an ancestor, or the quality runner's detached ambient head when its canonical branch and strict ancestor base are supplied but the runner omits `GITHUB_HEAD_SHA`. Attached, malformed, equal-base, unrelated, reversed, or conflicting topology fails closed; all evidence is evaluated at the validated candidate head and complete fixed history.

| Exit | Kind | Meaning |
|---:|---|---|
| 0 | completed worker result | Repository GREEN still requires the frozen pytest file to pass. |
| 1 | `CONTRACT_FAILURE` | Route, schema, identity, trust, or budget contract failed. |
| 2 | `INFRASTRUCTURE_FAILURE` | Git, import, platform, or resource evidence was unavailable. |
| 3 | `INTENTIONAL_RED` | C2/C3 reached the exact typed `ACP.NOT_IMPLEMENTED` boundary. |

At C2/C3, all 108 corpus and hostile-regression worker calls return typed exit 3 and canonical `ACP.NOT_IMPLEMENTED`; pytest reports exactly 108 failures
and zero errors. At C4, dispatcher exit 0 is available only after the unchanged
acceptance file passes in full.

Mandatory readability evidence is recorded for the four C2 designated paths:
`docs/ENGINEERING_PROCESS_RCA.md` 71/80,
`scripts/quality/adversarial_convergence.py` 555/900 and `tests/unit/test_adversarial_convergence.py` 899/1000, with
`tests/unit/test_quality_dispatcher.py` 83/100. All remain below the 90-percent
stop and require independent exact-head readability disposition. The only
production function above 60 logical lines is the 63-line fail-closed repository
inspector; it has two parameters, bounded early exits, and no semantic executor
responsibility.

Executable thresholds accept module 809 and focused-test 899 only with readability evidence; 810 and 900 stop.
Aggregate stops remain 3,500 for C2 and 3,620 after the C3 freeze.

## Historical regression mapping

| Reset50/51 blocker | v1 regression or residual risk |
|---|---|
| Unsafe eager fixture reads, symlink/FIFO following, parse-before-hash, short reads, depth and exception leakage | ACP-T01/T02/T12 safe-loader and hostile-parser GREEN tests. |
| Central route contradiction and freeze excluded from the phase map | ACP-T04/T10 exact dispatcher, cumulative phase paths, and frozen sentinel checks. |
| Subset-accepting routes and near-match authority | Exact path equality, A/M-only status, mode, numstat, history, blob, dirty-state, and near-match tests. |
| Forged `sys.modules` oracle credit and implementation-derived results | ACP-T08/T09 AST import boundary plus stimulus-only handoff and test-owned literal expectations. |
| macOS-only temporary roots | Tests use pytest `tmp_path`; production accepts an explicit trusted root. |
| Oversized/compressed helpers and premature PASS prose | Function-length tests, per-file caps, mandatory readability review, and `PENDING_EXTERNAL_REVIEW`. |
| Universal self-proving oracle growth | Finite N=40 corpus, 12 threats, 12 mutants, 3,500-line aggregate, OWNER-enumerated corrections, and no automatic v2/reset. |

Residual risk before C3 is external-review authenticity and exact candidate
identity; before C4 it is the intentionally absent executor. Neither is a
product/runtime risk because the framework has no activation authority.

### Review receipt grammar and candidate authors

Each receipt `content` is exactly seven LF-delimited, ASCII lines, with no
prefix, suffix, alternate disposition, or substring interpretation:

```text
ISSUE435_REVIEW_V1
role=<exact frozen role>
disposition=PASS
head=<exact lowercase 40-hex C2 head>
tree=<exact lowercase 40-hex C2 tree>
reviewer=<canonical lower-case name <canonical lower-case email>>
url=<exact ASCII-decimal Issue #435 comment URL>
```

The application validates every freeze value constraint, additionally requires
exactly four ordered receipts, and binds the digest to the exact content above.
Candidate authors are not caller declarations: a bounded, NUL-framed Git log
over the trusted base-to-C2 history supplies normalized `name <email>` values.
The declaration must equal that derived ordered unique list. Reviewer names and
emails are independently unique and neither normalized component may equal any
candidate-author component. C3 must still authenticate durable GitHub comment
authorship externally; local receipt parsing does not prove GitHub identity.

## Review finding triage and correction outcome

Each exact-head observation receives one evidence-backed disposition. The
Primary Orchestrator, not the reviewer label, owns the final classification:

| Disposition | Meaning | Gate effect |
|---|---|---|
| `CRITICAL_BLOCKER` | Reproduced false acceptance, security bypass, or authority bypass. | Blocks. |
| `REQUIRED_CONTRACT` | Reproduced direct violation of frozen acceptance. | Blocks. |
| `ADVISORY_DEBT` | Readability or maintainability debt without false credit. | Record owner and rationale; does not block by itself. |
| `DUPLICATE` | Same root cause and correction as an existing finding. | Consolidate; no second blocker. |
| `OUT_OF_SCOPE` | Outside the issue's frozen authority. | Prevent the action and route separately if needed. |

Reproduction binds the exact head, environment, and input; compares actual
output with a literal oracle; includes positive and negative controls; and
checks evidence provenance, completeness, and integrity. Independent
confirmation is required where the contract calls for it. The evidence,
rationale, disposition, owner, and prevented action are durable review output.

If an authorized bounded correction still has a blocker, return to an architecture
and authority checkpoint. Do not patch again automatically, declare the issue
impossible, or abandon it. The OWNER may approve another finite plan, defer, or
close out the attempt. A future root `CLAUDE.md` must be a thin pointer to
`AGENTS.md` on a separate issue/branch after Issue #435; it is not part of this
path set.

## Required commands

```bash
python3 -m json.tool docs/governance/adversarial-convergence-framework-cases-v1.json
uv run pytest tests/unit/test_adversarial_convergence.py -k 'not future_validator'
uv run pytest tests/unit/test_adversarial_convergence.py -k future_validator --tb=no
uv run pytest tests/unit/test_quality_dispatcher.py tests/unit/test_guardrails_check.py -k 'issue435 or dispatcher'
uv run ruff check scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
uv run mypy --strict scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
python3 -m py_compile scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
python3 scripts/guardrails_check.py
make quality
```

At C2, the bootstrap/harness/security/route subset must be GREEN, the future
executor subset must contain exactly 108 failures and zero errors, and `make quality` must reach the same exact 108 typed `ACP.NOT_IMPLEMENTED`
failures and zero errors through the immutable runner. Any different failure
stops.
