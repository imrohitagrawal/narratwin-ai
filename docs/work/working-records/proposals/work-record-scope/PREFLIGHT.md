# Work-record manifest scope preflight

Status: contract established before implementation; exact candidate verification pending.

Issue559, branch phase-1-closure-process-559-work-record-scope, base2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce.
Owner current-session permission approves separate narrow gate correction.
This removes the reproduced15-path rejection blocking personal-avatar preparation558.
No provider/media/spend/biometric authority follows. Dirty/unpublished338 is untouched.

## Scope and implementation boundary

One scope helper and legacy-wrapper call change; frozen checker/test bytes remain
unchanged. Work-record manifests cannot authorize runtime, providers, workflows,
dependencies or installed quality-kernel edits. Exact manifest path and line
budgets remain issue-owned data, not central per-issue literals.

Stable installation kernel: scripts/quality/work_record_scope.py,
scripts/quality/phase1_closure/legacy.py, tests/unit/test_work_record_scope.py,
tests/unit/phase1_closure/test_legacy.py. Admit installation only when helper is
absent from positively verified base and all kernel paths are declared/changed.
Installed bases reject kernel changes in the documentation route; future
maintenance needs a separately reviewed route. Ordinary envelope is docs/work,
exact issue preflight and existing process-document paths plus third-party notices.
Installation additionally owns an ADR. Never allow arbitrary manifest-declared code.

## Invariant / failure matrix

| ID | Required behavior | Decisive positive and negative evidence | Owner |
|---|---|---|---|
| W1 | Real pilot work-record docs can pass exact manifest route | Isolated Git fixture valid docs; prior frozen checker rejects same path | root |
| W2 | Issue/branch/first-preflight/full branch scope stay bound | Correct first commit; missing/multiple/foreign/non-first preflight and committed-extra masking reject | root |
| W3 | Self-authored scope cannot grant runtime/code privilege | Exact docs envelope and full kernel install; coherent backend/workflow/dependency/kernel manifest rejects | root |
| W4 | Budgets measure actual content with no deletion credit | Boundary additions+deletions; malformed/missing caps, per-path/aggregate overrun and unsafe bytes/modes reject | root |
| W5 | Local work is inspectable, hosted candidate stays clean and truthful | Working/untracked local manifest check; hosted dirt, head/branch/event/merge-parent mismatch and missing history reject | root |
| W6 | Frozen parity and preserved checks survive scope replacement | Valid scope executes every preserved check; scope failure and preserved-contract/frozen drift prevent success | root |
| W7 | Evidence survives sessions and host gates remain mandatory | Retained original repo evidence, source hashes, exact CI commands; no immutable freeze before hosted pass | root |

## Source facts and claim boundaries

Official Git diff documentation: https://git-scm.com/docs/git-diff accessed2026-10-13.
NUL-delimited name/numstat and explicit no-renames avoid ambiguous parsing;
symlink modes and binary/unreadable evidence are rejected.
Official checkout source: https://github.com/actions/checkout accessed2026-10-13.
GitHub event reference: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows accessed2026-10-13.
PR workflows may use synthetic merge commits, while policy uses direct head.
Candidate head, firstpreflight history and actual checkout content must agree;
push before is not the integration base. Repo workflow permissions and bootstraps
are read from current .github/workflows, not assumed from a local approximation.

## Test and hosted parity plan

TDD Git fixtures: valid docs, install kernel, installed-base refusal, coherent
malicious manifest, first-preflight faults, committed/current divergence, bytes/
modes, exact paths/budgets and preserved continuation. Test RED precedes helper
implementation; mutation restores rejection or removes envelope and tests go RED.
Run complete backend unit/API suite and exact backend lint/test commands.
Run make quality (archive/records/catalog plus phase checks), repository guardrails,
PR-event evidence and live protection/status contexts. Hosted Python3.13 and
uv0.11.18 --frozen bootstrap, direct-head/merge, push zero/prior SHA, PR/review
events and detached checkout all have executable proof before freeze.
No paid providers are used in tests. Missing/shallow/stale history is not PASS.

## Skill selection, review and stop rule

Existing RCA/playbook/work-record workflow consulted. Work-package protocol
guides isolation/resource custody and independent review. Repository TDD guidance
produces RED/GREEN negative fixtures; existing record/catalog tools prove metadata.
No skill installation/activation, SDK, dependency or UI work. Frontend/provider
skills deferred; no useful claim at those boundaries in this increment.
Independent implementation/security and operations/economics reviewers receive
exact candidate, contract and disproof cases; no shared writes. Reproduce/classify
findings; only demonstrated mandatory failures block. One initial and one bounded
RCA approach, four review rounds maximum without reset. Fundamental assumption
changes cause bounded replan, no blanket permissions or freeze.

## Human-only and resource surfaces

Rohit is final owner; agent review is not GitHub APPROVED or audiovisual acceptance.
Keep current protection unchanged; use only existing permitted owner route after
required checks/review. Final reference-only merge wording inspected before merge.
Provider consent, rights, billing and media quality remain separately unverified.
Before allocation recorded128MiB writer/reviewer checkout,500MiB test scratch,
up to1GiB isolated locked environment,10MiB durable evidence,5GiB reserve.
Preserve original dirty bytes and retained evidence; no historical cleanup.
General playbook already addresses these lessons; no broad playbook edits.

## Bounded RCA correction after review round1

Trigger: independent review reproduced omitted staged state and missing hosted
event classification. Root cause: the proof enumerated committed/worktree states
without index, and inferred hosting only from event-name presence. Existing
focused/local green evidence was insufficient for W4/W5. Add index path/type/
byte/charge checks and hosted detection from GITHUB_ACTIONS plus event signal.
PR applicability uses event base, preventing newer main from rerouting an
unrelated historical branch. Regression fixtures precede correction; unchanged
frozen checker, docs envelope and budgets remain. This is the one bounded RCA
approach, review round2 next; cumulative review/approach counters do not reset.
Resume only after staged masking and missing-host tests fail before/pass after,
full suite and independent corrected-boundary verification.
