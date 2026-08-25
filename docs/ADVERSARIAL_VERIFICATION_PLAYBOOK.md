# Adversarial Convergence Framework v1

Issue #435 defines a finite, offline governance framework. It does not define
the threat model for every NarraTwin feature, prove a product slice, activate a
provider, or authorize release. Activation is `NONE`, authority effect is
`NO_AUTHORITY_EFFECT`, and release posture remains No-Go.

The controlling OWNER amendment is
<https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-5416186961>.
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
= 5fd31be0dddf4572f1e8cb5405524ee97e4bd2b20448aded7197949ecb3fe371
```

Canonical JSON uses UTF-8/ASCII-safe output, sorted keys, `(',', ':')`
separators, and no NaN. Raw corpus SHA-256 is
`49184abda0f21351049810bee09eb81dba40bdfb8a9afbdaf8f97cf8dcbe8cab`.
The corpus is 6,782 bytes, below the 48 KiB target and 64 KiB hard cap.

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
from the test-owned expectation, and produces a `KILLED` receipt naming its
assertion. This proves C2 assertion discrimination. It is not a claim that the
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
- Four independent reviews bind one exact C2 head/tree while candidate review
  state remains `PENDING_EXTERNAL_REVIEW`.
- At most one correction wave may occur before C3; all four reviews rerun.
- C3 adds only `adversarial-convergence-red-freeze-v1.json` and binds the C2
  objects, semantic corpus identity, route-adapter digest, and review receipts.
- C4 changes only `scripts/quality/adversarial_convergence.py`, outside the
  frozen route-adapter sentinel, to replace the executor skeleton.
- No correction follows C3. A required C4 finding stops for OWNER disposition.

The exact dispatcher routes only
`governance-435-adversarial-convergence-framework-v1` to this gate. Lookalikes
receive no authority. Direct gate exit codes are authoritative:

| Exit | Kind | Meaning |
|---:|---|---|
| 0 | completed framework result | Available only after C4 satisfies the frozen contract. |
| 1 | `CONTRACT_FAILURE` | Route, schema, identity, trust, or budget contract failed. |
| 2 | `INFRASTRUCTURE_FAILURE` | Git, import, platform, or resource evidence was unavailable. |
| 3 | `INTENTIONAL_RED` | C2/C3 reached the exact typed `ACP.NOT_IMPLEMENTED` boundary. |

`make` itself reports nonzero recipes generically; the gate's canonical JSON
`kind`, `code`, and direct exit distinguish intentional RED from infrastructure.

## Historical regression mapping

| Reset50/51 blocker | v1 regression or residual risk |
|---|---|
| Unsafe eager fixture reads, symlink/FIFO following, parse-before-hash, short reads, depth and exception leakage | ACP-T01/T02/T12 safe-loader and hostile-parser GREEN tests. |
| Central route contradiction and freeze excluded from the phase map | ACP-T04/T10 exact dispatcher, cumulative phase paths, and frozen sentinel checks. |
| Subset-accepting routes and near-match authority | Exact path equality, A/M-only status, mode, numstat, history, blob, dirty-state, and near-match tests. |
| Forged `sys.modules` oracle credit and implementation-derived results | ACP-T08/T09 AST import boundary plus stimulus-only handoff and test-owned literal expectations. |
| macOS-only temporary roots | Tests use pytest `tmp_path`; production accepts an explicit trusted root. |
| Oversized/compressed helpers and premature PASS prose | Function-length tests, per-file caps, mandatory readability review, and `PENDING_EXTERNAL_REVIEW`. |
| Universal self-proving oracle growth | Finite N=40 corpus, 12 threats, 12 mutants, 3,500-line aggregate, one correction wave, and no automatic v2/reset. |

Residual risk before C3 is external-review authenticity and exact candidate
identity; before C4 it is the intentionally absent executor. Neither is a
product/runtime risk because the framework has no activation authority.

## Required commands

```bash
python3 -m json.tool docs/governance/adversarial-convergence-framework-cases-v1.json
uv run pytest tests/unit/test_adversarial_convergence.py -k 'not future_validator_matches_test_owned_expectation'
uv run pytest tests/unit/test_adversarial_convergence.py -k future_validator_matches_test_owned_expectation --tb=no
uv run pytest tests/unit/test_quality_dispatcher.py tests/unit/test_guardrails_check.py -k 'issue435 or dispatcher'
uv run ruff check scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
uv run mypy --strict scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
python3 -m py_compile scripts/quality/adversarial_convergence.py tests/unit/test_adversarial_convergence.py
python3 scripts/guardrails_check.py
make quality
```

At C2, the bootstrap/harness/security/route subset must be GREEN, the future
executor subset must contain exactly 40 failures and zero errors, and
`make quality` must reach typed `INTENTIONAL_RED`. Any different failure stops.
