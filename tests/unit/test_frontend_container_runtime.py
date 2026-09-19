from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "frontend/Dockerfile"
CONSENSUS = ROOT / "scripts/ci/check_container_scan_consensus.py"
INDEX_DIGEST = "sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
PLATFORM_DIGESTS = {
    "amd64": "sha256:b4fea132199070b0c8ea9ac66f363fe2cd6d1e4f994e61d8c87976c2157a1b8a",
    "arm64": "sha256:d778881fd638833a2a0ed0fbb30577718729ab08112776dea4555eb5551826da",
}
NODE_SOURCE_INDEX = INDEX_DIGEST
NODE_SOURCE_PLATFORM_DIGESTS = PLATFORM_DIGESTS
RUNTIME_PACKAGES = {
    "alpine-keys": "2.6-r0", "alpine-release": "3.24.2-r0",
    "ca-certificates-bundle": "20260909-r0", "libgcc": "15.2.0-r5",
    "libstdc++": "15.2.0-r5", "musl": "1.2.6-r2",
}


def load_consensus() -> ModuleType:
    spec = importlib.util.spec_from_file_location("issue413_consensus", CONSENSUS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_exact_runtime_apk_install(source: str) -> None:
    # Independent full-source oracle: this increment freezes every Dockerfile byte.
    assert hashlib.sha256(source.encode()).hexdigest() == "33c0c52eda6aa80d9576397976255da56acae4ff69b21fe69bce442a0377926d"
    active = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    instructions = [line for line in active.replace("\\\n", " ").splitlines() if line.startswith("RUN set -eux;")]
    assert len(instructions) == 1 and active.count("apk add") == 1
    options = "apk add --root /runtime --initdb --no-cache --no-scripts --keys-dir /etc/apk/keys --repositories-file /etc/apk/repositories".split()
    assert instructions[0].split(";")[1].split() == options + [f"{name}={version}" for name, version in RUNTIME_PACKAGES.items()]


def test_issue554_actual_apk_install_and_scan_inventory_match_exact_pins() -> None:
    _assert_exact_runtime_apk_install(DOCKERFILE.read_text())
    assert load_consensus().FRONTEND_RUNTIME_PACKAGES == RUNTIME_PACKAGES


def test_issue554_source_predicate_rejects_active_non_apk_decoys() -> None:
    source = DOCKERFILE.read_text()
    for name, version in RUNTIME_PACKAGES.items():
        pin = f"{name}={version}"
        for actual in (name, f"{name}=0-r0"):
            for decoy in (f'ENV EXPECTED="{pin}"', f'RUN echo "{pin}"', f'LABEL expected="{pin}"'):
                with pytest.raises(AssertionError):
                    _assert_exact_runtime_apk_install(source.replace(pin, actual, 1) + "\n" + decoy + "\n")


def issue555_heredoc_mutant(source: str) -> str:
    options = "--root /runtime --initdb --no-cache --no-scripts --keys-dir /etc/apk/keys --repositories-file /etc/apk/repositories"
    fake = "RUN set -eux; apk add " + options + " " + " ".join(f"{n}={v}" for n, v in RUNTIME_PACKAGES.items()) + ";"
    start = source.index("RUN set -eux; \\\n")
    end = source.index("\n\nFROM scratch AS deps", start)
    replacement = ("RUN <<'OUTER'\ncat <<'INNER' >/dev/null\n" + fake + "\nINNER\nset -eux\n"
                   + '/sbin/apk "add" ' + options + " " + " ".join(RUNTIME_PACKAGES) + ";\n"
                   + "rm -f /runtime/var/log/apk.log;\nmkdir -p /runtime/usr/bin /runtime/app /runtime/tmp;\n"
                   + "cp /usr/local/bin/node /runtime/usr/bin/node;\nchmod 0755 /runtime/usr/bin/node;\n"
                   + "chmod 1777 /runtime/tmp;\ntest -s /runtime/lib/apk/db/installed;\ntest ! -e /runtime/bin/sh\nOUTER")
    result = source[:start] + replacement + source[end:]
    assert len(result.encode()) == 3942
    assert hashlib.sha256(result.encode()).hexdigest() == "3e953325f1a5af73851e83de7f5eb878f4cb15a27ea31e8d21eb7a4171accf35"
    return result


def test_issue555_independent_complete_source_oracle_rejects_inert_pins() -> None:
    source = DOCKERFILE.read_text()
    _assert_exact_runtime_apk_install(source)
    with pytest.raises(AssertionError):
        _assert_exact_runtime_apk_install(issue555_heredoc_mutant(source))


def test_runtime_pins_the_reviewed_node_source_and_minimal_final_stage() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    assert f"FROM node:26.7.0-alpine3.24@{NODE_SOURCE_INDEX} AS node-source" in source
    assert source.count("FROM scratch AS") == 2
    assert "FROM scratch AS deps" in source and "FROM scratch AS build" in source
    assert all(value not in source.lower() for value in ("glibc", "gcompat", "libatomic"))


def test_runtime_contract_binds_platform_manifests_and_unaffected_openssl() -> None:
    module = load_consensus()
    assert module.FRONTEND_RUNTIME_INDEX == INDEX_DIGEST
    assert module.FRONTEND_RUNTIME_PLATFORM_DIGESTS == PLATFORM_DIGESTS
    assert module.FRONTEND_NODE_SOURCE_INDEX == NODE_SOURCE_INDEX
    assert module.FRONTEND_NODE_SOURCE_PLATFORM_DIGESTS == NODE_SOURCE_PLATFORM_DIGESTS
    assert module.FRONTEND_RUNTIME_PACKAGES == RUNTIME_PACKAGES
    assert module.FRONTEND_RUNTIME_OPENSSL_VERSION == "3.5.7"
    assert module.frontend_openssl_is_acceptable("3.5.7")
    for vulnerable in ("3.6.0", "3.6.3"):
        assert not module.frontend_openssl_is_acceptable(vulnerable)


def test_runtime_preserves_package_identity_while_removing_tools() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    final = source.split(" AS build", 1)[1]
    assert "COPY --from=node-source /runtime/ /" in final
    assert "ENTRYPOINT [\"/usr/bin/node\"]" in final
    assert "USER 65532:65532" in final
    assert "apk" not in final and "/bin/sh" not in final
    assert "/lib/apk/db/installed" in source


def test_runtime_discards_volatile_apk_install_log() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    node_source = source.split("FROM scratch AS deps", 1)[0]

    assert "rm -f /runtime/var/log/apk.log" in node_source
    assert node_source.index("apk add --root /runtime") < node_source.index(
        "rm -f /runtime/var/log/apk.log"
    )
    assert "/runtime/lib/apk/db/installed" in node_source


def test_scan_contract_requires_runtime_package_metadata_and_openssl_identity() -> None:
    script = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    assert "FRONTEND_RUNTIME_INDEX" in script
    assert "FRONTEND_RUNTIME_PLATFORM_DIGESTS" in script
    assert "FRONTEND_RUNTIME_PACKAGES" in script
    assert "/lib/apk/db/installed" in script
    assert "frontend_openssl_is_acceptable" in script
    assert "actual_architecture" in script
    assert 'actual_architecture}" != "${FRONTEND_ARCH}' in script
