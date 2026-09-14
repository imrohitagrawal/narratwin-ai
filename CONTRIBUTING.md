# Contributing and starting work

Start with [the documentation map](docs/README.md), [current status](docs/STATUS.md)
and [work records](docs/work/INDEX.md). Agents also read [AGENTS](AGENTS.md), including
all required sources. [Document placement and ownership](docs/DOCUMENTATION_GUIDE.md)
explains where each output belongs. [Template catalog](docs/templates/README.md)
links the canonical forms, including embedded playbook sections.

## Choose the question before the solution

| Situation | Start with | Useful completion |
|---|---|---|
| No product yet | Discovery issue; existing playbook intent brief | Evidence about users/problem, constraints and a decision to continue, change direction or stop |
| New feature or design exploration | Discovery issue linked to existing product/work | A reviewed user journey and decision; unresolved assumptions remain explicit |
| Reproducible defect | Bug report | Agreed expected behavior, reproduction and a bounded correction plan |
| Accepted implementation or engineering maintenance | Stage / Guardrail Work issue | Exact scoped outcome, acceptance, verification and closeout |

Discussion notes retain questions, observations and decisions in the owning work
record. A discovery issue closes on an evidenced decision; it does not need an
invented PRD or an approved implementation plan. An implementation issue starts
from an accepted requirement and applicable authority. Creating an issue or PR
does not authorize providers, spending, private-data use, deployment or release.

## Create a useful GitHub issue

Search existing issues and [registered work](docs/work/INDEX.md) first. Reuse the
owning issue for the same scope; create a linked child for independently owned
work. In GitHub choose **Issues → New issue**, then discovery, bug or stage work.
Native forms live in [.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE/stage_guardrail.yml).
The new forms become available through the default branch after merge.

State a concrete title such as “Investigate how reviewers find source citations”
or “Preserve citations when revising an approved sentence.” Include:

- Who experiences the problem and the current situation.
- The desired outcome or the decision the investigation must answer.
- Relevant safe observations, reproduction or existing requirements.
- Scope, exclusions, unknowns and dependencies appropriate to the work type.
- The accountable owner and links to the stable work, plan and design when known.
- What proves completion, including prohibited behavior and the next step.

“Unknown” and “none yet” are useful discovery answers when accompanied by the next
investigation. Before implementation, the responsible engineer fills in accepted
scope, plan, authority and verification rather than silently treating those answers
as approval. For security-sensitive findings, agree a private reporting channel with the
repository owner before sharing details; this repository has no documented
reporting address. [Security and privacy](docs/SECURITY_AND_PRIVACY.md) describes
project controls. Do not paste secrets, customer data, private session logs or
unapproved screenshots in public issues.

CLI/API issue creation does not automatically enforce browser forms. Write a
completed Markdown body with the same relevant fields, then use:

```sh
gh issue create --title 'Investigate citation discovery' --body-file issue-body.md
```

Replace the example title and file with the actual reviewed content. Record the
resulting issue link in the owning work record. Forms are intake aids; maintainer
triage and existing execution gates determine readiness.

## Design and plan the change

A designer starts with [product intent](docs/PRD.md), [strategy](docs/PRODUCT_STRATEGY.md),
[current working behavior](docs/STATUS.md) and the applicable work record. Capture
audience and job, current/proposed journey, alternatives, loading/empty/error/refusal
states, keyboard/accessibility and responsive behavior, approved prototype references,
constraints, evidence and the decision owner. Use the conditional design section in
[WORK](docs/work/templates/WORK.md). Unapproved designs stay proposals.

The engineer records the bounded execution plan and required preflight using the
[existing engineering playbook](docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md)
and [RCA workflow](docs/ENGINEERING_PROCESS_RCA.md). Significant technical decisions
belong in [architecture and ADRs](docs/ARCHITECTURE.md), with the [ADR index](docs/ADR/INDEX.md)
providing unique source identities. Do not duplicate a PRD or create an ADR for a
routine edit that changes neither requirements nor architecture.

Select affected documentation from the [documentation impact routes](docs/DOCUMENTATION_GUIDE.md#select-documentation-impact).
The [readiness register](docs/ENTERPRISE_READINESS_REGISTER.md) owns security,
reliability, accessibility and other engineering acceptance requirements. A template
checkbox does not prove those requirements are met.

## Implement and verify

Follow [AGENTS](AGENTS.md), [repository guardrails](docs/REPOSITORY_GUARDRAILS.md),
[quality gates](docs/QUALITY_GATES.md) and [local development](docs/LOCAL_DEVELOPMENT.md).
Preserve a dirty shared checkout; use the issue's dedicated branch. Record resource
ownership before material allocation. Match tests and independent review to the
claim being proved. Keep safe mock/local defaults and exact evidence of failures
and corrections. Update only the affected canonical documents and work record.

## Write a PR a newcomer can understand

Use the single [PR template](.github/pull_request_template.md). Keep its required
product context, seven impact answers, five reviewer-overview points and evidence
sections. Put the problem and observable result first. Use short, specific answers;
explain each section's distinct purpose instead of copying the same paragraph.

For example: “Reviewers could not find the original source for a decision. This
change adds one source link to each decision record and rejects missing targets.”
Then state scope, what is complete after merge, remaining gaps and how to verify.
An issue link supports that explanation; it cannot replace it. List actual commands
and results, reproducible review steps, failure conditions and residual risks.
Do not copy this example as evidence for a different change.

For CLI creation, fill the canonical template in a local Markdown file and use
`gh pr create --draft --body-file pr-body.md` with the correct branch/base. Run
`make pr-reconcile PR=NUMBER` with the actual PR number after the final push, as
required by [the operating model](docs/CODEX_OPERATING_MODEL.md).
A reviewer should understand the before/after result from the PR itself and use
linked exact sources to check it. Keep current CI in GitHub Checks and the managed
live-state block; historical results remain labeled with their tested head.

## Close out or hand off

Follow [the shared handoff procedure](docs/work/PROCESS.md) before compaction,
branch changes, cleanup or ending a session with unfinished work. Record completed
work and evidence, unresolved questions/findings, next permitted action, branch/PR
and observed head, resource retention and source-coverage limits. Refresh plan and
evidence hashes and run `make documentation-quality` and `make work-records-quality`.

A merged issue closes only when its actual acceptance conditions and closeout gates
are met. Keep the work folder after completion; record supersession and reopening
there. Routine merge/check/cleanup receipts belong in PR/issue comments under the
existing operating model, with material repository status changes in STATUS.
