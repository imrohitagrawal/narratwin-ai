from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.quality import stage8_backend_security as security
from scripts.quality import stage8_node_security as node_security


ROOT = Path(__file__).parents[2]


def test_issue436_backend_image_contract_is_exact_and_fail_closed() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    assert security.BACKEND_BASE_IMAGE == (
        "docker.io/library/alpine:3.21@sha256:"
        "48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d"
    )
    assert security.CPYTHON_VERSION == "3.13.15"
    assert security.CPYTHON_SHA256 == (
        "1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76"
    )
    assert security.ISSUE436_BRANCH == "stage8-436-backend-tls-capability-isolation-r4"
    assert security.ISSUE436_CHARGE_LIMIT == 1400
    assert len(security.ISSUE436_FILES) == 13
    assert security.ISSUE436_STACK_BASE == "6bcdb8d60ebb4d1e5fef3725cffc459dd5525987"
    assert security.ISSUE436_STACK_FILES == security.ISSUE436_FILES | node_security.ISSUE376_SECURITY_FILES
    assert security.backend_dockerfile_valid(dockerfile)


def test_issue547_exact_alpine_runtime_revisions_reach_real_consumers() -> None:
    expected = {"OPENSSL_PACKAGE_REVISION": "3.3.7-r1", "ALPINE_RELEASE_REVISION": "3.21.8-r0",
                "ALPINE_KEYS_REVISION": "2.5-r0", "ISSUE436_OPENSSL_PACKAGE_REVISION": "3.3.7-r0",
                "ISSUE436_ALPINE_RELEASE_REVISION": "3.21.7-r0"}
    assert {name: getattr(security, name, None) for name in expected} == expected
    assert security.backend_dockerfile_valid((ROOT / "backend/Dockerfile").read_text())
    assert callable(getattr(security, "backend_runtime_probe_valid", None))
    assert security.backend_runtime_probe_valid((ROOT / "scripts/ci/backend-image-package-check.sh").read_text())


def test_issue547_rejects_each_old_partial_mismatched_or_floating_pin() -> None:
    current = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    desired = current.replace("3.3.7-r0", "3.3.7-r1").replace("3.21.7-r0", "3.21.8-r0")
    assert security.backend_dockerfile_valid(desired), "reviewed three-pin contract must be accepted"
    for package, revision, rejected in (
        ("openssl-dev", "3.3.7-r1", "3.3.7-r0"), ("libcrypto3", "3.3.7-r1", "3.3.7-r0"),
        ("libssl3", "3.3.7-r1", "3.3.7-r0"), ("alpine-release", "3.21.8-r0", "3.21.7-r0"),
        ("alpine-keys", "2.5-r0", "2.4-r1"),
    ):
        marker = f"{package}={revision}"
        assert marker in desired
        for replacement in (f"{package}={rejected}", package):
            assert not security.backend_dockerfile_valid(desired.replace(marker, replacement))


def test_issue547_runtime_probe_rejects_each_inventory_mismatch() -> None:
    validator = getattr(security, "backend_runtime_probe_valid", None)
    assert callable(validator), "runtime inventory consumer validation must exist"
    probe = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(encoding="utf-8")
    assert validator(probe)
    for package, revision, rejected in (
        ("libcrypto3", "3.3.7-r1", "3.3.7-r0"), ("libssl3", "3.3.7-r1", "3.3.7-r0"),
        ("alpine-release", "3.21.8-r0", "3.21.7-r0"), ("alpine-keys", "2.5-r0", "2.4-r1"),
    ):
        marker = f'packages["{package}"] == "{revision}"'
        assert marker in probe
        assert not validator(probe.replace(marker, f'packages["{package}"] == "{rejected}"'))


def test_issue436_rejects_image_source_tls_and_metadata_mutations() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    mutations = (
        dockerfile.replace(security.BACKEND_BASE_IMAGE, "alpine:3.21"),
        dockerfile.replace(security.BACKEND_BASE_IMAGE, security.BACKEND_BASE_IMAGE[:-1] + "0"),
        dockerfile.replace(security.CPYTHON_VERSION, "3.13.14"),
        dockerfile.replace(security.CPYTHON_SHA256, "0" * 64),
        dockerfile.replace("sha256sum -c -", "REMOVED"),
        dockerfile.replace("libssl3=3.3.7-r1", "libssl3=3.5.7-r0"),
        dockerfile.replace("libcrypto3=3.3.7-r1", "libcrypto3=3.5.7-r0"),
        dockerfile.replace("/lib/apk/db/installed", "/tmp/concealed"),
        dockerfile + "\nFROM alpine:latest AS bypass\n",
    )
    assert all(not security.backend_dockerfile_valid(value) for value in mutations)


def test_issue436_runtime_probe_requires_tls_and_safe_openssl_line() -> None:
    probe = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(encoding="utf-8")
    for marker in (
        "ssl.OPENSSL_VERSION",
        'startswith("OpenSSL 3.3.7 ")',
        "ssl.create_default_context()",
        "/lib/apk/db/installed",
        'packages["libcrypto3"] == "3.3.7-r1"',
        'packages["libssl3"] == "3.3.7-r1"',
    ):
        assert marker in probe


def test_issue547_inventory_validator_is_consumed(monkeypatch) -> None:
    monkeypatch.setattr(security, "backend_dockerfile_valid", lambda _: True)
    monkeypatch.setattr(security, "backend_runtime_probe_valid", lambda _: False, raising=False)
    failures = []
    security.check(ROOT, lambda args: subprocess.CompletedProcess(args, 0, "", ""), "main", failures)
    assert failures == ["Stage 8 backend runtime inventory contract drifted."]


def test_issue436_route_binds_base_first_commit_scope_and_budget() -> None:
    numstat = "".join(f"1\t1\t{path}\n" for path in sorted(security.ISSUE436_FILES))

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[1:3] == ["merge-base", "--is-ancestor"]:
            output = ""
        elif args[1] == "merge-base":
            output = security.ISSUE436_STACK_BASE + "\n"
        elif args[1] == "rev-list":
            output = security.ISSUE436_PREFLIGHT_COMMIT + "\nnext\n"
        elif args[1] == "diff-tree":
            output = "docs/governance/preflights/issue-436.json\n"
        elif args[1] == "ls-files":
            output = ""
        else:
            output = numstat
        return subprocess.CompletedProcess(args, 0, output, "")

    failures: list[str] = []
    security.check_route(ROOT, run, failures)
    assert failures == []

    def wrong_first(args: list[str]) -> subprocess.CompletedProcess[str]:
        result = run(args)
        if args[1] == "rev-list":
            return subprocess.CompletedProcess(args, 0, "0" * 40 + "\n", "")
        return result

    failures = []
    security.check_route(ROOT, wrong_first, failures)
    assert failures == ["Issue #436 base, first commit, or charged-line evidence failed closed."]


def test_issue436_route_rejects_over_budget_foreign_and_untracked_evidence() -> None:
    paths = sorted(security.ISSUE436_FILES)

    def check(numstat: str, untracked: str = "") -> list[str]:
        def run(args: list[str]) -> subprocess.CompletedProcess[str]:
            if args[1:3] == ["merge-base", "--is-ancestor"]:
                output = ""
            elif args[1] == "merge-base":
                output = security.ISSUE436_STACK_BASE + "\n"
            elif args[1] == "rev-list":
                output = security.ISSUE436_PREFLIGHT_COMMIT + "\nnext\n"
            elif args[1] == "diff-tree":
                output = "docs/governance/preflights/issue-436.json\n"
            elif args[1] == "ls-files":
                output = untracked
            else:
                output = numstat
            return subprocess.CompletedProcess(args, 0, output, "")

        failures: list[str] = []
        security.check_route(ROOT, run, failures)
        return failures

    exact = "".join(f"0\t0\t{path}\n" for path in paths)
    over = exact.replace(f"0\t0\t{paths[0]}", f"1401\t0\t{paths[0]}")
    assert "Issue #436 exceeds its 1,400 charged-line budget." in check(over)
    foreign = exact.replace(paths[0], "forbidden/outside.txt")
    assert "Issue #436 charged-line evidence has a foreign or duplicate path." in check(foreign)
    assert "Issue #436 untracked-path evidence is not allowed." in check(exact, "new.txt\n")
