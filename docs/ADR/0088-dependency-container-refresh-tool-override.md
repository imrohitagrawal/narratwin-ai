# ADR 0088: dependency and container refresh with a narrow tool override

Status: proposed in issue #571; acceptance requires exact-head review and CI.

## Context

The dependency and container refresh profile needs current exact versions in the
root, frontend and isolated Semgrep tool graphs, and current Alpine package
revisions in both images. Semgrep 1.183.0 pins its own MCP and OpenTelemetry
versions, so the tool audit cannot pass on Semgrep's resolved graph alone.
ADR 0069 forbids every tool override. This ADR narrows that one sentence.

## Decision

Refresh every affected package to a qualified exact version under the existing
profile contract: a preflight-only first commit, exact paths and charged-line
caps, closed profiles, strict audits, no ignored advisory, no lowered threshold
and no workflow or branch-protection change.

The owner allows one exception, recorded on issue #571. The Semgrep tool project
may override exactly these four packages to exactly these versions:
`mcp==1.30.0`, `opentelemetry-api==1.45.2`, `opentelemetry-sdk==1.45.2` and
`opentelemetry-exporter-otlp-proto-http==1.45.2`. Overriding the API alone passes
the audit but stops Semgrep from starting, so the three OpenTelemetry rows move as
one set. The root project stays free of overrides.

The contract compares the project list and the whole lock manifest with that exact
list and ties it to Semgrep 1.183.0. Any other override, constraint or dependency
metadata row, in either file, fails closed. The installed-tool check reads Semgrep's
installed requirements and fails as soon as a row is no longer outside them, so the
exception cannot outlive its reason after a Semgrep change. It is removed once
Semgrep's own pins allow these versions; a tracking issue holds that condition and
the command that settles it. It sets no precedent for any other package.

Next 16.4 writes ESLint import-resolver keys as absolute paths. The effective
configuration digest now removes only the actual frontend root, so a checkout
location cannot change it, and a resolver outside that root is refused. Rules,
parser and other settings stay in the digest.

The image scans also need newer CPython (3.13.18) and Node (26.13.0) releases and a
newer undici build archive (6.29.1). They move under the same exact-identity checks.

This change also removes names that should not be public from files this change
must edit; the frozen receipts of the closure check and its test are rebound for
that edit only. The Issue #158 record keeps its meaning and now uses a neutral
label for the approving account in all four documents that carry it.

## Alternatives

- Wait for Semgrep to move its pins: leaves required CI red for an unknown time.
- Ignore the advisories in the tool audit: forbidden by the audit contract.
- Replace Semgrep: a larger change that this refresh does not need.
- Override only the MCP and OpenTelemetry API rows: Semgrep fails to start.

## Consequences

The tool's OpenTelemetry versions differ from Semgrep's declared pins, so its
tracing path runs on versions upstream did not pin. The repository scan runs with
metrics off, and the canary, engine validation and clean scan must still pass.
This grants no provider, media, deployment or release authority.
