# Issue 300 Negative Forensic Containment Preflight

## Objective

Contain PR #301 to negative evidence, remove positive authority, and avoid product repair. Issue #280 is not fixed.

## Bound Identities

| Label | Bound value |
|---|---|
| PR #299 base | `cc89b2dd52da38e8d8a9acbd813e327737cf0ca1` |
| PR #299 head / evidence head | `f93653e8a11e697c88766b207fb01c18662339d6` |
| PR #301 base | `cc89b2dd52da38e8d8a9acbd813e327737cf0ca1` |
| Merge base | `cc89b2dd52da38e8d8a9acbd813e327737cf0ca1` |
| PR #301 pre-correction head | `16536867dc2f3bca8c19281b58e924615475c158` |
| Review head | Unassigned: no corrected commit or review is authorized |
| Deployment identity | Not applicable: deployment is outside scope |
| Approved contract SHA-256 | `14ca82c43768975f4a904a308db10aab77ef50cdedd97e92601ecba67ab7e75a` |

These labels are not interchangeable; a later review must bind a newly verified review head.

## Scope And Non-Goals

The exact final 11-path allowlist is recorded in `docs/governance/preflights/issue-300.json`
and enforced statically. Eight PR paths may only be restored to the exact PR #301 base bytes.

No backend, frontend, workflow, provider, RAG, avatar, media, database, Docker, deployment,
product repair, generic assurance, external packet, PR #299, or Issue #280 history change is allowed.
The runtime/browser `correctnessReport.status = "PASSED"` surface is a later P0 product-repair
blocker; this PR revokes its authority but does not edit runtime code.

## Preserved Behavioral RED Evidence

The pre-correction sources were copied to scratch and the packet's `17_REPRODUCE_BASELINE.py`
harness changed only its scratch matrix, restored it, matched each result, and exited `0`.
That wrapper exit means reproduction succeeded; it is not product or semantic success.

Source identities before correction:

| Artifact | SHA-256 |
|---|---|
| `scripts/quality/semantic_closure.py` | `29509fa2cd476682099566f03f460a4f607b975894acc68fba1c3b2e22f832c7` |
| `scripts/quality/verify_issue280_output_correctness.py` | `367aaf945748d4433ea5754e2cd1e128c1c0f84777113ed576d20d831607c0dc` |
| `reports/checkpoint3-issue280/requirement-matrix.json` | `443300320f9c6eaca8245ab9693a50bea8e98bc0630bf7ddacabda3ea6fd6e5f` |
| Packet execution evidence `20_DELTA007_EXECUTION_EVIDENCE.json` | `98943e56952f35b613475c210be239bd3f91fb6702a853dad577efdd8e481b50` |
| Packet blind review `08_CLAUDE_BLIND_REVIEW_RESPONSE.md` | `03a581d205930ed5305731b10633b60c89dffef46a42edcb7228aa908e2a5bc8` |

### E1 — positive-path reachability

Command:

```text
/usr/local/bin/python3 /private/tmp/narratwin-issue300-red.3gx1YM/scripts/quality/verify_issue280_output_correctness.py --expected-head f93653e8a11e697c88766b207fb01c18662339d6
```

Exit: `1`; stderr: empty; stdout:

```text
Issue 280 semantic closure FAILED at exact head f93653e8a11e697c88766b207fb01c18662339d6:
- output-correctness:execution-not-provided
```

### E2 — claim-kind laundering

The same issue-specific command ran after all seven scratch rows were relabeled
`structural` / `STRUCTURAL_PASS` with structural observations.

Exit: `0`; stderr: empty; stdout:

```text
Issue 280 semantic closure passed at exact head f93653e8a11e697c88766b207fb01c18662339d6.
```

This is the false-positive path being removed.

### E5 — self-declared scope

Command:

```text
/usr/local/bin/python3 /private/tmp/narratwin-issue300-red.3gx1YM/scripts/quality/semantic_closure.py /private/tmp/narratwin-issue300-red.3gx1YM/e5-self-declared-one-row.json --expected-head f93653e8a11e697c88766b207fb01c18662339d6
```

Exit: `0`; stderr: empty; stdout:

```json
{"closed": true, "reasons": []}
```

This proves that a caller-selected one-row scope could emit closure.

### Focused TDD RED

Before implementing the correction,
`uv run pytest tests/unit/test_issue280_forensic_verifier.py -q` produced 19
failures. They exposed the absent `forensicEvidence` schema and the verifier's
dependency on the now-removed generic positive evaluator.

Independent-review scratch mutations then added top-level
`overallVerdict: PASSED` and `authorVerdict: FIXED` to the interim artifact.
Both incorrectly reached `ISSUE_280_NOT_FIXED` with exit `1`. After tests were
added for those mutations, a renamed arbitrary verdict, an unknown top-level
key, an unknown forensic key, and an unknown observed-execution key, the focused
suite produced four failures before the denylist was replaced by exact schema
allowlists. The retained tests now require unknown keys to produce
`ISSUE_280_EVIDENCE_MALFORMED` / exit `3`, including when another identity is stale.

## Negative-Only Result Contract

| Exit | Reason | Meaning |
|---:|---|---|
| `1` | `ISSUE_280_NOT_FIXED` | evidence is valid and preserves the known failure |
| `2` | `ISSUE_280_EVIDENCE_STALE` | a bound identity differs |
| `3` | `ISSUE_280_EVIDENCE_MALFORMED` | shape, type, or unknown schema key is invalid |
| `4` | `ISSUE_280_EVIDENCE_CONTRADICTORY` | well-formed observations differ from the preserved facts |

There is no exit `0` or positive semantic-closure result. The direct verifier exits `1`;
Make reports its failed recipe as exit `2`. The target is not a required green CI job;
required CI may run unit tests for expected negative behavior and static forensic integrity.

## Artifact And Context Budgets

- Final diff: exactly 11 paths.
- Hand-authored changed lines: at most 750.
- Net executable semantic logic: at most zero; the generic evaluator is removed.
- The 6,714-line phase checker receives only subtractive/static containment.
- This preflight: at most 1,800 words and 220 lines.
- No parallel status, learning, semantic, or assurance registry.
- Stop and split work if any budget or allowlist boundary is exceeded.

## Completion And Stop Rule

Completion requires mutation coverage for exits `1`–`4`, no positive closure entrypoint,
exact-base cleanup proof, focused tests, complete quality, and forbidden-path proof.
Issue #280 remains not fixed. Stop before commit, push, GitHub mutation, review, merge,
deployment, product repair, runner/oracle work, Q&A, avatar/media, or packet modification.
