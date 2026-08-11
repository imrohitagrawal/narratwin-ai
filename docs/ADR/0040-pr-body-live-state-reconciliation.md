# ADR 0040: PR-body live-state reconciliation

## Decision

PR bodies retain human-authored product and reviewer context. A unique delimited
managed block contains deterministic GitHub-derived metadata and is reconciled
by trusted base-branch code. `pr-body-consistency` validates the stored body and
is intended for branch protection only after a post-merge canary succeeds.

## Security posture

The privileged updater uses `pull_request_target` only to run code checked out
at the event base SHA, never the pull-request head. It accepts event/API values
as data, uses a bounded standard-library HTTPS client, compares the head SHA
before writing, and performs no write for unchanged output. Fork PRs fail
closed because the updater is same-repository only.

## Consequences

The managed block is the authority for mutable metadata; prose must not mirror
current CI state. A new head invalidates the prior reconciliation. External URL
availability is not a required gate; internal GitHub evidence is validated by
the trusted implementation.
