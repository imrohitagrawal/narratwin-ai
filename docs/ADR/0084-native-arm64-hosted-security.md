# ADR 0084: Run ARM64 container security checks on native hosted compute

- Status: Accepted for Issue #529 candidate validation
- Date: 2026-09-10
- Issue: #529

## Context

The Stage 8 security workflow built the ARM64 frontend on an x64 GitHub-hosted
runner through QEMU. At exact PR #528 head `36a3d12f`, push run `34428261263`
reached the ARM64 `npm ci` layer twice, QEMU terminated with target signal 4,
and the build stopped producing output until the finite job timeout cancelled
it. The same source passed in the pull-request event. This suppresses a required
ARM64 verdict and therefore fails closed; it is not evidence that NarraTwin or
the ARM64 image failed.

GitHub documentation inspected on 2026-09-10 lists `ubuntu-24.04-arm` as a
standard native ARM64 hosted label. The public-repository billing documentation
states that standard GitHub-hosted runners are free for public repositories,
and the published ARM image inventory includes Docker Engine and Buildx. The
QEMU action remains commit-pinned, but its default binfmt image is floating.

## Decision

Keep `security / docker build` on `ubuntu-latest` as the existing protected
AMD64 context. Remove QEMU from that job. Add a distinct, finite 30-minute
`security / docker build (ARM64 native)` job on `ubuntu-24.04-arm`.

Both jobs run the same unchanged `docker-build.sh` and
`docker-image-scan.sh`. Each builds and checks native backend and frontend
images, starts the frontend, performs the Sharp transform and HTTP check,
rebuilds for normalized reproducibility, emits truthful CycloneDX evidence,
and applies unchanged Trivy and Grype consensus thresholds. Image tags,
session IDs, report directories, and uploaded artifact names are isolated by
architecture.

The native ARM64 context must pass for both push and pull-request events at the
exact candidate head. Its observed stable check name is added to protected-main
requirements before merge. A build or scan failure remains blocking; there is
no retry, fallback, skip, cross-build substitution, or warning-only path.

This supersedes only ADR 0077's single-context and QEMU-hosted topology
decision. Every image, runtime, scanner, consensus, and severity threshold in
ADR 0077 remains active.

## Alternatives and consequences

An unchanged rerun, unconditional retry, and warning-only behavior were
rejected because they could hide failure. Repinning QEMU was rejected because
it retains the demonstrated emulation boundary without causal proof.
Cross-building was rejected because it cannot establish executable runtime,
Sharp, HTTP, inventory, or reproducibility evidence. A frontend-only scanner
mode was rejected because native execution can preserve the complete existing
scanner without a wider schema and policy refactor.

This adds parallel hosted CI work but no incremental public-repository Actions
charge under the inspected terms. Entitlement, label, billing, and runner image
must be revalidated if repository visibility or GitHub policy changes. The
change adds no product behavior, provider call, credential use, media, egress,
spend, deployment, release, production-readiness, or Cut 1 evidence.

## Sources

- <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>
- <https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job>
- <https://docs.github.com/en/billing/concepts/product-billing/github-actions>
- <https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Arm64-Readme.md>
- <https://github.com/docker/setup-qemu-action/blob/master/action.yml>
