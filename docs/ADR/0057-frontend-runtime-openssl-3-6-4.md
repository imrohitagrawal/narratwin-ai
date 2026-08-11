# ADR 0057: Bind the frontend runtime to an unaffected OpenSSL line

- Status: Accepted for Issue #413 review
- Date: 2026-08-11
- Issue: #413

## Context

PR #412 independently exposed `CVE-2026-54876` in the pinned Chainguard Node
runtime: both `libcrypto3` and `libssl3` were `3.6.3-r3`. The OpenSSL advisory
and official CVE record say 3.6.0 through versions before 3.6.4 are affected;
3.6.4 fixes that line. OpenSSL 3.6.3 therefore cannot be treated as fixed.

Registry, package and scanner inspection on 2026-08-11 rejected Chainguard
Node `latest` (3.6.3-r3), Chainguard `latest-slim` (3.6.2-r2), Docker Official
Node Alpine (Grype BusyBox Medium), Docker Official Node Bookworm-slim
(multiple Medium-to-Critical findings), Google Distroless Node Debian 13
(Medium-to-Critical findings), and two Alpine musl scratch prototypes (Grype
Medium/High). No finding was ignored and package metadata was not removed.

## Decision

The final frontend stage is the exact Chainguard `glibc-dynamic` multi-platform
index `sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70`:

- amd64: `sha256:f95c554213997aeb84b4c146819f08481e99a6f9b0a7a7524cdcc02632cfac5d`
- arm64: `sha256:4edabf15b30c80cc70a24d0614a6f911d306f58a1613d72a653a0e135eccdde8`

It receives only the Node 26.7.0 binary from Docker Official Node
Bookworm-slim index `sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341`
and `libatomic` 16.1.0-r4 plus its exact APK/SPDX records from Chainguard
`gcc-glibc` index `sha256:8cfe0b01dcf3ad08aa8d51811175749f7390228be059497ddc6d94551a68f66e`.
All three sources bind reviewed amd64 and arm64 manifests in the scanner
contract. The Node binary reports embedded OpenSSL 3.5.7, outside the affected
ranges; this decision does not claim it is 3.6.4.

The final image retains `/usr/lib/apk/db/installed` with exactly eight truthful
Wolfi runtime packages and retains their SPDX records. It has no shell, package
manager, npm or global tooling, exposes only `/usr/bin/node`, and runs the
standalone Next.js server as `65532:65532`.

The scanner gate checks immutable runtime configuration, Node/OpenSSL/package
identity, root ownership and permissions, zero capabilities, exact
runtime architecture, bounded normalized inventory shape, non-root HTTP smoke,
same-builder two-build inventory equality, CycloneDX identity, and Trivy/Grype
consensus through Medium. It does not hardcode the complete application-layer
filesystem hash across native and emulated builders; CI demonstrated that such
hashes can differ while the separately exact source, config, package, OpenSSL,
SBOM and runtime contracts remain identical.

## Consequences and boundaries

The runtime is a minimal composition of exact official verified artifacts and
preserves package metadata rather than concealing findings. A digest, platform manifest, package,
SBOM, inventory, configuration, entrypoint, user or scanner mismatch fails
closed. This changes no frontend behavior or application dependency and grants
no deployment, release, public-availability, production-readiness, Issue #368,
or Cut 1 completion claim.

Sources observed 2026-08-11: the OpenSSL security advisory, official CVEProject
record, Docker Official Node manifests, and Chainguard image manifests and
vulnerability inventories.
