"""Issue #374 frontend build/runtime pin and branch-scope contract."""
from __future__ import annotations

import re

ISSUE374_SECURITY_BRANCH = "stage8-374-node-image-cve-2026-58043"
ISSUE374_SECURITY_FILES = {
    "frontend/Dockerfile",
    "frontend/next.config.ts",
    "scripts/ci/docker-image-scan.sh",
    "scripts/ci/check_container_scan_consensus.py",
    "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_node_security.py",
    "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_container_scan_consensus.py",
    "tests/unit/test_stage8_node_security.py",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
FRONTEND_NODE_BUILD_IMAGE = (
    "node:26.6.0-alpine@sha256:"
    "a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8"
)
FRONTEND_NODE_RUNTIME_IMAGE = (
    "cgr.dev/chainguard/node:latest@sha256:"
    "cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734"
)
FRONTEND_BUILD_ARCHIVE_SHA512 = {
    "npm@12.0.2": (
        "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b"
        "1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943"
    ),
    "brace-expansion@5.0.9": (
        "49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2cea"
        "de8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6"
    ),
    "ip-address@10.3.1": (
        "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d"
        "800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea"
    ),
    "tar@7.5.21": (
        "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b"
        "09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c"
    ),
    "undici@6.28.0": (
        "2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e2"
        "74e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28"
    ),
}
FRONTEND_NODE_IMAGE_FAILURE = (
    "Stage 8 frontend build and runtime images must retain the reviewed Node image pin."
)


def frontend_node_image_valid(dockerfile: str) -> bool:
    expected = [
        f"FROM {FRONTEND_NODE_BUILD_IMAGE} AS deps",
        "FROM deps AS build",
        f"FROM {FRONTEND_NODE_RUNTIME_IMAGE} AS runner",
    ]
    actual = [
        line.strip()
        for line in dockerfile.splitlines()
        if re.match(r"(?i)^from(?:\s|$)", line.lstrip())
    ]
    return (
        actual == expected
        and dockerfile.count("sha512sum -c -") == len(FRONTEND_BUILD_ARCHIVE_SHA512)
        and all(
            package in dockerfile and f"echo '{digest}  /tmp/" in dockerfile
            for package, digest in FRONTEND_BUILD_ARCHIVE_SHA512.items()
        )
    )


def check_frontend_node_image(dockerfile: str, failures: list[str]) -> None:
    if not frontend_node_image_valid(dockerfile):
        failures.append(FRONTEND_NODE_IMAGE_FAILURE)
