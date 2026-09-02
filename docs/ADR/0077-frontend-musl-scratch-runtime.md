# ADR 0077: frontend musl scratch runtime

- Status: Proposed for Issue #502 exact-head review
- Date: 2026-09-02
- Decision scope: frontend container runtime and dual-architecture security gate

## Context

Accepted main's minimal Wolfi/glibc frontend image fails closed because Grype
reports Medium `CVE-2026-18374` in `glibc 2.43-r12`; Trivy reports no finding.
No official fixed Wolfi package is available. Suppression, a lower threshold,
concealed package metadata, or fabricated VEX would make the gate less safe.

Docker Official Node publishes immutable Node 26.7.0 Alpine 3.24 images for
amd64 and arm64. The application already locks Sharp's musl native packages.
Node documents musl caveats, so the decision requires executable behavior on
both architectures and remains a controlled Cut 1 boundary, not production
readiness.

## Decision

Use exact index `node:26.7.0-alpine3.24@sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019`
only as an immutable source. Assemble a scratch dependency/build environment
and scratch final image containing the Node binary plus exactly six pinned,
truthfully recorded Alpine packages: `alpine-keys`, `alpine-release`,
`ca-certificates-bundle`, `libgcc`, `libstdc++`, and `musl`.

The final image runs as `65532:65532` with no shell, package manager, npm,
compiler, headers, glibc, gcompat, writable trusted tree, or effective
capabilities. It preserves the direct Node entry point, application command,
port, proxy target, security headers, and embedded OpenSSL/disabled-QUIC
identity. Sharp must perform a real PNG resize, not merely load its module.

The single required hosted context scans AMD64 and QEMU-emulated ARM64 in
separate report directories. Each architecture must build, start, return HTTP
200, transform an image, reproduce a normalized inventory, emit a truthful
CycloneDX SBOM, and pass both Trivy and Grype with zero Medium-or-higher
frontend findings. Scanner disagreement or incomplete evidence fails closed.

## Alternatives and consequences

Waiting for a Wolfi fix remains a future option. Current Chainguard glibc,
distroless/glibc, threshold changes, ignores, and VEX without official
non-applicability evidence were rejected. The musl route removes the affected
glibc capability while retaining application behavior and package visibility.

Rollback may not restore the vulnerable glibc runtime. Any Node, Alpine,
native-module, package, architecture, or inventory change requires renewed
evidence. This decision adds no provider call, credential use, narration,
voice, audio, caption, avatar media, deployment, release, production-readiness,
or Cut 1 acceptance authority.
