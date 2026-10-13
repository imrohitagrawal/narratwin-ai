# ADR 0087: current dependency and container recovery

Status: proposed in issue #561; acceptance requires exact-head review and CI.

## Problem and decision

Main's Alpine OpenSSL r0 pin disappeared, and strict audits find six vulnerable
application packages plus two vulnerable isolated-tool packages. The prior
September successor's r1 pin is also stale. Preserve that history and the
original dirty checkout; repair the currently demonstrated failures separately.
Target only qualified security packages and their required transitive records.
Semgrep 1.175 caps PyJWT below its patched version; actual resolution proves
that a compatible upstream Semgrep 1.180 pin is necessary. No override or audit
exception is permitted. Keep Alpine 3.21 with verified current APK revisions.

A closed, validated public profile binds exact current project/record hashes,
source receipts, isolated tool identity, APK values and verification timeout.
Checker/probe consumers read it; the probe receives validated public values
with the original profile hash. Dockerfile/pyproject/lock files are deployment
configuration and must agree with it. Future patch data changes require fresh
source qualification, graph review, audits and actual builds. Agreement alone
never grants owner or hosted approval.

Historical compatibility tests keep their original mutations on immutable
prior inputs, acquired only after the exact supplied current pair has passed
whole-graph/provenance validation. A separate mutation suite rejects vulnerable,
forged, duplicate, missing and unrelated current inputs before normalization.

## Scope, authority and verification

The owner's current repair instruction is recorded separately from host review.
C1 f74768c6 remains immutable history; a documented current preflight amendment
governs 49 paths and 4,000 additions plus deletions. A bounded Stage 8 hardening
envelope, first-commit proof, manifest budgets and real checkout topology retain
the existing semantic gates and frozen Phase 1 substrate.

Root and tool strict audits, installed PyJWT options regression, Semgrep canary
and repository scan, complete unit/API/frontend checks, exact local/direct/merge
quality and native hosted x86/ARM image build/probe/scan must pass before merge.
Owner removed the preset memory/disk reserve prerequisite; actual capacity
is observed without an arbitrary reserve approval gate. Local and native hosted
commands provide verification. No immutable release evidence is frozen
from local approximation. Prior four review rounds/two approaches remain history. The owner removed the
work-package-protocol dependency and its review-limit approval gate; repository
technical review and hosted verification still govern acceptance.

## Frontend qualification amendment

Current npm audit also demonstrates vulnerable Next, brace-expansion, Sharp and
source-map-js records. Qualified patch versions and required native/transitive
records are refreshed, including the vendored npm brace archive. The unpatched
braces dependency is removed through a truthful scoped tinyglobby alias.
General glob and local-file adapter qualification failed and are not promoted.

The actual ESLint configuration does not set next.rootDir. A mandatory lint,
test and build prerequisite binds every effective rule/options/parser/settings
for supported types and all actual lint targets, including root configuration files, verifies the unmodified published
Next consumer, blocks custom rootDir, and runs real failing/passing Next-rule
canaries. All baseline rules remain; the official Next patch adds one rule.
This qualifies current configuration only; future custom rootDir needs a new
compatibility decision. There is no general fast-glob compatibility claim.

A separate closed frontend profile carries current graph bindings, native and
npm-archive identity, effective configuration hashes and verification timeout.
Both Python and Node consumers reject malformed/duplicate/foreign data. Timeout
is capped by Node's intrinsic signed-32-bit millisecond timer representation.
Native scanner/SBOM checks consume current Sharp and runtime-package identity.
Interrupted local full-suite/secret scans are retained as incomplete; actual
hosted full checks remain mandatory. The pre-code amendment is issue comment
6145651233; earlier exclusions and C1 remain history, review counters unchanged.

## Limits

No application feature, provider account mutation, biometric transfer, voice
clone, paid operation, deployment, protection change, threshold reduction or
shared/historical cleanup. No new Meera/Cut 1 or personal-avatar media acceptance.
Durable execution records remain outside temporary worktrees, with custody and
resume instructions; independent backup is not proved.

Actual hosted ARM bootstrap also reproduced missing frontend Alpine release
and certificate revisions. Official v3.24 indexes on both architectures qualify
3.24.2-r0 and 20260909-r0; no other runtime package changed. The maintenance
branch family is reference-only and remains subject to exact scope validation;
canonical Stage 8 completion and near-match branches keep their closure policy.

Native deps-stage scan also found bundled http-cache-semantics 4.2.0 and
undici 6.28.0 at HIGH severity. Latest npm still bundles both, so the existing
verified archive-preparation boundary installs published http-cache-semantics
4.3.0 (outside the reported affected range; maintainer disputes the advisory,
no invented fixed-version metadata) and patched undici 6.28.1. The closed
archive set now has six identities; npm, IP-address and tar remain unchanged.
Actual unsuppressed native scans must qualify this correction.

Native scanners reproduced new critical/high CPython3.13.15 findings.
Official signed Python3.13.16 fixes those reported issues; its version/hash
are configured through the closed dependency profile and checked in the actual
image probe. Trust key, nonroot/TLS and capability-isolation contracts remain.

The frozen legacy test explicitly invokes a local child. Its scoped fixture
removes only that test's inherited hosted marker; missing hosted event data
still fails closed. Mypy uses explicit namespace bases and the existing unit
test import path to check both same-named fixtures without exclusions.
