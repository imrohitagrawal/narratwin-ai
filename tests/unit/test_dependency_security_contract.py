"""Dependency contract tests; no LLM, script, or answer generation occurs here.

The contract has no provider output, source_chunk, or citation generation and
does not require trace/run_id metadata.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
from packaging.version import Version

import scripts.ci.check_semgrep_security as semgrep_security
from scripts.ci.check_semgrep_security import (
    ContractError,
    EXPECTED_TARGETS,
    REVIEWED_INPUTS,
    validate_audit_wrappers,
    validate_canary_result,
    validate_installed_tool,
    validate_project_contract,
    validate_reviewed_inputs,
    validate_rule_ids,
    validate_scan_result,
)


ROOT = Path(__file__).resolve().parents[2]
ISSUE360_BASE = "b9a2a8cd4aa05328116565990fc30ae44592c875"
ISSUE396_BASE = "9ee3f4a4d3b8cf1e78b5a878904748b60d557a76"
ISSUE401_BASE = "9cf6e01f9d0c32f25c229b5adf38c6eb716ca9a0"
ISSUE499_BASE = "d1f5400f5c6dfec5d4b63eb3a83aa82e3330743f"
BRACE_PATH = "node_modules/brace-expansion"
JS_YAML_PATH = "node_modules/js-yaml"
NANOID_PATH = "node_modules/nanoid"
JS_YAML_431_INTEGRITY = (
    "sha512-CY6crGq313MX8GkwvB7tzgp99vjQxY1++5y10/BKN/GUfHqWaOGQMNZkBvqSzsZKWk/ijwHlWzzkLulsGHhjWQ=="
)
BRACE_509_INTEGRITY = (
    "sha512-ScQ4IuvIEF1TMlP7Zt+vjJ//9zlPb2SDcxWxM3bk8s6t6GGdJ7KO1dCcTidOPJKePW30LE/2cT7wCyPho9/Wxg=="
)
ISSUE495_FRONTEND_PACKAGES = {
    "baseline-browser-mapping": ("2.11.20", "sha512-H0ulySigv6icDJ1F7SjtdCD6PrhTpdYCmP0CactWy1+ekh0AFd0o1Wn5T8b+hnTmdBx19u9yhL6wvCylXMY7zw=="),
    "browserslist": ("4.28.8", "sha512-V2NpofLblG64mfOtSgDhOJESZEGogzDMBv/q+W6oc4LXWP/q75eOXoOaaOu1EOadB9U4Bwx/e0yzbvwKH8zalA=="),
    "caniuse-lite": ("1.0.30001810", "sha512-TITQPUkaz+aVk5GL6NhOdwk1aEaNTSDPsGFWrTuhKGtjTF70jL/Oht2W4c6rXUe5fu7Ie19VIahAXHIIiWWNeg=="),
    "electron-to-chromium": ("1.5.419", "sha512-nHMPn8x4yCxCI0iSnL+LlHL5sUoUfjLXkcRIagZ4GBdrfFLFaiLNvzJWbJqZhFT9IAhw5tUSNlhggWN+otvp/A=="),
    "node-releases": ("2.0.54", "sha512-YHs7BmmcsdAI5Ozuf8JZo6PT0mv2GIWC9vMfvUC3dp65M8hn7Ux8CPL+2oBI7juNuj9d0ndhTcznq2ODBps9cQ=="),
    "update-browserslist-db": ("1.3.2", "sha512-UQ+MSxlhRm1bzjhU+DcuXfjFO1FzNtqhK5+9Yvlp90ItDLk5vT932A0rFu619nf7RVS+Y/VeaUW1jaRDqZ8VJw=="),
}
ISSUE150_BASE = "a02286240212ad8958915aec01aa5ebaf60fa705"
ISSUE460_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
PYPDF_WHEEL_SHA256 = "c8b09a59399062fb45a1b8156c18a787a10a3dae03ac9674397a226712c94604"
PYPDF_SDIST_SHA256 = "595647f6191de6f402cfde1d0c455d6cbccbd509aac32b34783009c032de5d6e"
PYPDF_PACKAGE_SHA256 = "e8a5256eb981e4dc5c904fa425c0ba134e251343a500219df5a91ea0fcc99423"
PYPDF_SDIST_URL = "https://files.pythonhosted.org/packages/44/66/54212e75406afd9f3e933d0dda23072f6aecc55c5a273077dc2e0b028b23/pypdf-6.16.2.tar.gz"
PYPDF_WHEEL_URL = "https://files.pythonhosted.org/packages/13/f1/a2da3b55acd4ab737bf728c97edaaed5ec1d3c1236acb639dcdfa97e42c7/pypdf-6.16.2-py3-none-any.whl"
PIP_SECURITY_VERSION = "26.2.1"
PIP_SECURITY_WHEEL_SHA256 = "71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e"
PIP_SECURITY_SDIST_SHA256 = "f6ad667e89a1fe78046c8f13232b247200f5258d7828f3f7883d660878e0813f"
PILLOW_PACKAGE_SHA256 = "c70cea2f3be57c728d2b012f17b7fbc4c9c839a9ed34329d17d7f57575f9e660"
GOOGLE_AUTH_PACKAGES = {
    "google-auth": ("2.56.3", "aafe27da7ef14e2ec2b24d75c45f7d800cfa7b3eb2d3d73a85228aafcfd870bc", "40e229fc901f0a305b553050e5fce562d509bee0435be053abfa91582b51b90c", "8ec438808f813ad034535000261eed1067475d229d05bbf4216e78c3f2362e53"),
    "cryptography": ("50.0.0", "8584b52fbe429cb4b08434bf19df055dfe7c97a11d486c9b265ec1ee01851bb4", "eeac2acb5a20ed25e0ad6d1df9891a520b78b404266b6d11778f25d5d691a6c9", "031e2d5dd4bb9caa3ca9c82e5a197fd8ae680232cee62603d1a813f3f07e3d03"),
    "pyasn1-modules": ("0.4.2", "6ca56d4d6b05cbc23d8920a3e91de1bac50e43b90e49439cc0d7aa7e143eb692", "677091de870a80aae844b1ca6134f54652fa2c8c5a52aa396440ac3106e941e6", "29253a9207ce32b64c3ac6600edc75368f98473906e8fd1043bd6b5b1de2c14a"),
    "pyasn1": ("0.6.4", "3ad96cec94414e068c189c877f0b9ffa701f05c7c1317874cf5dafff6a34130a", "9c447d8431c947fe4c8febc4ed9e760bc29011a5b01e5c74b67025bd9fb8ce81", "deda9277cfd454080ec40b207fb6df82206a3a2688735233cdcd8d3d565f088b"),
}
ISSUE482_PACKAGES = {
    "aiohttp": ("3.14.3", "ad7a70c5426492328c2ddc0fadd6040332646c74ec5e53142387a59a7395b746"),
    "cuda-bindings": ("13.3.1", "dcb0611f046b60cd6bd71096e04458faca2b53e0e517141643a57525bf44ff80"),
    "cuda-toolkit": ("13.0.3.0", "7f0e7c6f154685fbc63dac8c900a605fa46de3f331018f7b651bb5aedf47cfdd"),
    "datasets": ("5.0.1", "fed0d5c3a2eacd683ef71fb0cd2e233c933d004300c272aacf3328cd42be6f54"),
    "setuptools": ("84.0.0", "40d7bb1469b8b97ed537a39c27fa445b44513df8d59c77247cdc925f44c53343"),
    "torch": ("2.13.0", "25956554d432863f0207b50dc5f717d294723c4635a65700e4648f8aa2f5f112"),
}
def _normalize_issue434_project(project: dict[str, Any]) -> None:
    dev = project["dependency-groups"]["dev"]; assert dev.count("cryptography==50.0.0") == 1; dev.remove("cryptography==50.0.0")  # noqa: E702
def _normalize_issue434_lock(lock: dict[str, Any]) -> None:
    root = next(package for package in lock["package"] if package["name"] == "narratwin-ai"); dependencies = root["dev-dependencies"]["dev"]; metadata = root["metadata"]["requires-dev"]["dev"]  # noqa: E702
    assert dependencies.count({"name": "cryptography"}) == 1 and metadata.count({"name": "cryptography", "specifier": "==50.0.0"}) == 1; dependencies.remove({"name": "cryptography"}); metadata.remove({"name": "cryptography", "specifier": "==50.0.0"})  # noqa: E702


def _normalize_pip_security_delta(lock: dict[str, Any], base_lock: dict[str, Any]) -> None:
    package = next(package for package in lock["package"] if package["name"] == "pip")
    assert package["version"] == PIP_SECURITY_VERSION
    assert package["sdist"]["hash"] == f"sha256:{PIP_SECURITY_SDIST_SHA256}"
    assert package["wheels"][0]["hash"] == f"sha256:{PIP_SECURITY_WHEEL_SHA256}"
    index = next(i for i, item in enumerate(lock["package"]) if item["name"] == "pip")
    lock["package"][index] = next(item for item in base_lock["package"] if item["name"] == "pip")


def _normalize_issue482_delta(lock: dict[str, Any], base_lock: dict[str, Any]) -> None:
    for name, (version, digest) in ISSUE482_PACKAGES.items():
        index = next(i for i, item in enumerate(lock["package"]) if item["name"] == name)
        package = lock["package"][index]
        assert package["version"] == version
        assert hashlib.sha256(
            json.dumps(package, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest() == digest
        lock["package"][index] = next(
            item for item in base_lock["package"] if item["name"] == name
        )


def _normalize_t03_pillow_dev_delta(project: dict[str, Any], lock: dict[str, Any]) -> None:
    dev = project["dependency-groups"]["dev"]
    assert dev.count("pillow>=12.3.0") == 1
    dev.remove("pillow>=12.3.0")
    packages = [package for package in lock["package"] if package["name"] == "pillow"]
    assert len(packages) == 1
    pillow = packages[0]
    assert pillow["version"] == "12.3.0"
    assert pillow["source"] == {"registry": "https://pypi.org/simple"}
    assert hashlib.sha256(
        json.dumps(pillow, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest() == PILLOW_PACKAGE_SHA256
    root = next(package for package in lock["package"] if package["name"] == "narratwin-ai")
    root_dev = root["dev-dependencies"]["dev"]
    root_metadata = root["metadata"]["requires-dev"]["dev"]
    assert root_dev.count({"name": "pillow"}) == 1
    assert root_metadata.count({"name": "pillow", "specifier": ">=12.3.0"}) == 1
    root_dev.remove({"name": "pillow"})
    root_metadata.remove({"name": "pillow", "specifier": ">=12.3.0"})
    lock["package"] = [package for package in lock["package"] if package["name"] != "pillow"]


def _assert_google_auth_delta(project: dict[str, Any], lock: dict[str, Any], base_project: dict[str, Any], base_lock: dict[str, Any]) -> None:
    providers = project["project"]["optional-dependencies"]["providers"]
    base_providers = base_project["project"]["optional-dependencies"]["providers"]
    assert providers == ["google-auth==2.56.3", *base_providers]
    packages = {package["name"]: package for package in lock["package"]}
    base_packages = {package["name"]: package for package in base_lock["package"]}
    assert set(packages) == set(base_packages) | set(GOOGLE_AUTH_PACKAGES)
    assert packages["cffi"] == base_packages["cffi"]
    assert packages["pycparser"] == base_packages["pycparser"]
    for name, (version, digest, sdist_hash, wheel_hash) in GOOGLE_AUTH_PACKAGES.items():
        package = packages[name]
        assert package["version"] == version and package["source"] == {"registry": "https://pypi.org/simple"}
        assert package["sdist"]["hash"] == f"sha256:{sdist_hash}"
        assert package["wheels"][0]["hash"] == f"sha256:{wheel_hash}"
        assert hashlib.sha256(json.dumps(package, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == digest
    root = next(package for package in lock["package"] if package["name"] == "narratwin-ai")
    assert [item["name"] for item in root["optional-dependencies"]["providers"]] == ["google-auth", "litellm", "openai", "sentence-transformers"]
    google_metadata = [item for item in root["metadata"]["requires-dist"] if item["name"] == "google-auth"]
    assert google_metadata == [{"name": "google-auth", "marker": "extra == 'providers'", "specifier": "==2.56.3"}]
    normalized_project = copy.deepcopy(project)
    normalized_project["project"]["optional-dependencies"]["providers"] = base_providers
    _normalize_issue434_project(normalized_project)
    assert normalized_project == base_project
    normalized_lock = copy.deepcopy(lock)
    normalized_root = next(package for package in normalized_lock["package"] if package["name"] == "narratwin-ai")
    normalized_root["optional-dependencies"]["providers"].remove({"name": "google-auth"})
    normalized_root["metadata"]["requires-dist"].remove(google_metadata[0])
    normalized_lock["package"] = [package for package in normalized_lock["package"] if package["name"] not in GOOGLE_AUTH_PACKAGES]
    _normalize_issue434_lock(normalized_lock)
    _normalize_pip_security_delta(normalized_lock, base_lock)
    _normalize_issue482_delta(normalized_lock, base_lock)
    assert normalized_lock == base_lock


def _text_at(ref: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return result.stdout


def _base_text(path: str) -> str:
    return _text_at(ISSUE360_BASE, path)


def _base_json(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_base_text(path)))


def _normalize_issue495_frontend_delta(
    lock: dict[str, Any], base_lock: dict[str, Any]
) -> None:
    for name, (version, integrity) in ISSUE495_FRONTEND_PACKAGES.items():
        path = f"node_modules/{name}"
        record = lock["packages"][path]
        assert (record["version"], record["resolved"], record["integrity"]) == (
            version,
            f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz",
            integrity,
        )
        lock["packages"][path] = base_lock["packages"][path]


def _assert_pypdf_6162_contract(project_text: str, lock_text: str) -> None:
    project, lock = tomllib.loads(project_text), tomllib.loads(lock_text)
    base_project = tomllib.loads(_text_at(ISSUE401_BASE, "pyproject.toml"))
    base_lock = tomllib.loads(_text_at(ISSUE401_BASE, "uv.lock"))
    dependencies = project["project"]["dependencies"]
    assert [value for value in dependencies if value.startswith("pypdf")] == ["pypdf>=6.16.2"]
    google_project = copy.deepcopy(project)
    google_project["project"]["dependencies"][dependencies.index("pypdf>=6.16.2")] = "pypdf>=6.14.2"
    google_lock = copy.deepcopy(lock)
    google_root = next(package for package in google_lock["package"] if package["name"] == "narratwin-ai")
    google_pypdf_metadata = next(item for item in google_root["metadata"]["requires-dist"] if item["name"] == "pypdf")
    google_pypdf_metadata["specifier"] = ">=6.14.2"
    google_pypdf_index = next(i for i, package in enumerate(google_lock["package"]) if package["name"] == "pypdf")
    google_lock["package"][google_pypdf_index] = next(package for package in base_lock["package"] if package["name"] == "pypdf")
    _normalize_t03_pillow_dev_delta(google_project, google_lock)
    _assert_google_auth_delta(google_project, google_lock, base_project, base_lock)
    normalized_project = copy.deepcopy(project)
    index = dependencies.index("pypdf>=6.16.2")
    normalized_project["project"]["dependencies"][index] = "pypdf>=6.14.2"
    normalized_project["project"]["optional-dependencies"]["providers"] = base_project["project"]["optional-dependencies"]["providers"]
    _normalize_issue434_project(normalized_project)

    pypdf = [package for package in lock["package"] if package["name"] == "pypdf"]
    assert len(pypdf) == 1 and pypdf[0]["version"] == "6.16.2"
    assert pypdf[0]["source"] == {"registry": "https://pypi.org/simple"}
    assert pypdf[0]["sdist"]["url"] == PYPDF_SDIST_URL
    assert pypdf[0]["sdist"]["hash"] == f"sha256:{PYPDF_SDIST_SHA256}"
    assert pypdf[0]["sdist"]["size"] == 7008996
    assert len(pypdf[0]["wheels"]) == 1
    wheel = pypdf[0]["wheels"][0]
    assert wheel["url"] == PYPDF_WHEEL_URL
    assert wheel["hash"] == f"sha256:{PYPDF_WHEEL_SHA256}"
    assert wheel["size"] == 385060
    assert hashlib.sha256(
        json.dumps(pypdf[0], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest() == PYPDF_PACKAGE_SHA256

    normalized_lock = copy.deepcopy(lock)
    root = next(package for package in normalized_lock["package"] if package["name"] == "narratwin-ai")
    root["optional-dependencies"]["providers"].remove({"name": "google-auth"})
    google_metadata = next(item for item in root["metadata"]["requires-dist"] if item["name"] == "google-auth")
    root["metadata"]["requires-dist"].remove(google_metadata)
    root_metadata = next(item for item in root["metadata"]["requires-dist"] if item["name"] == "pypdf")
    root_metadata["specifier"] = ">=6.14.2"
    pypdf_index = next(i for i, package in enumerate(normalized_lock["package"]) if package["name"] == "pypdf")
    normalized_lock["package"][pypdf_index] = next(
        package for package in base_lock["package"] if package["name"] == "pypdf"
    )
    normalized_lock["package"] = [package for package in normalized_lock["package"] if package["name"] not in GOOGLE_AUTH_PACKAGES]
    _normalize_issue434_lock(normalized_lock)
    _normalize_pip_security_delta(normalized_lock, base_lock)
    _normalize_issue482_delta(normalized_lock, base_lock)
    _normalize_t03_pillow_dev_delta(normalized_project, normalized_lock)
    assert normalized_project == base_project
    assert normalized_lock == base_lock


def test_root_pypdf_resolution_is_exact_isolated_and_patched() -> None:
    _assert_pypdf_6162_contract(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        (ROOT / "uv.lock").read_text(encoding="utf-8"),
    )


def test_pypdf_contract_rejects_vulnerable_hash_and_unrelated_drift() -> None:
    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lock_text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    mutations = (
        (project_text.replace("pypdf>=6.16.2", "pypdf>=6.15.0"), lock_text),
        (project_text.replace("pypdf>=6.16.2", "pypdf>=6.16.0"), lock_text),
        (project_text.replace("pypdf>=6.16.2", "pypdf>=6.16.1"), lock_text),
        (project_text.replace('"cryptography==50.0.0"', '"cryptography==49.0.0"'), lock_text),
        (project_text.replace('    "pillow>=12.3.0",\n', ""), lock_text),
        (project_text.replace('"pillow>=12.3.0"', '"pillow>=12.2.0"'), lock_text),
        (project_text, lock_text.replace('    { name = "pillow" },\n', "", 1)),
        (project_text, lock_text.replace('    { name = "pillow", specifier = ">=12.3.0" },\n', "", 1)),
        (project_text, lock_text.replace('name = "pillow"\nversion = "12.3.0"', 'name = "missing-pillow"\nversion = "12.3.0"')),
        (project_text, lock_text.replace('name = "pillow"\nversion = "12.3.0"', 'name = "pillow"\nversion = "12.2.0"')),
        (project_text, lock_text.replace("sha256:3b8182a766685eaa002637e28b4ec8d6b18819a0c71f579bf0dbaa5830297cce", "sha256:" + "5" * 64)),
        (project_text, lock_text.replace('{ name = "cryptography", specifier = "==50.0.0" }', '{ name = "cryptography", specifier = "==49.0.0" }')),
        (project_text, lock_text.replace(f"sha256:{PYPDF_WHEEL_SHA256}", "sha256:wrong")),
        (project_text, lock_text.replace(f"sha256:{PIP_SECURITY_WHEEL_SHA256}", "sha256:wrong")),
        (project_text, lock_text.replace('version = "2.6.2"', 'version = "0.0.0"', 1)),
    )
    for candidate_project, candidate_lock in mutations:
        with pytest.raises(AssertionError):
            _assert_pypdf_6162_contract(candidate_project, candidate_lock)


def test_pypdf_contract_rejects_complete_provenance_and_graph_mutations() -> None:
    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lock_text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    pypdf_header = 'name = "pypdf"\nversion = "6.16.2"'
    pypdf_source = pypdf_header + '\nsource = { registry = "https://pypi.org/simple" }'
    pypdf_block_start = lock_text.index("[[package]]\n" + pypdf_header)
    pypdf_block_end = lock_text.index("\n[[package]]", pypdf_block_start + 1)
    pypdf_block = lock_text[pypdf_block_start:pypdf_block_end]
    project_mutations = (
        project_text.replace('    "pypdf>=6.16.2",\n', ""),
        project_text.replace('    "pypdf>=6.16.2",', '    "pypdf>=6.16.2",\n    "pypdf>=6.16.2",'),
        project_text.replace("pypdf>=6.16.2", "pypdf>=6"),
        project_text.replace("pypdf>=6.16.2", "pypdf==6.16.2"),
    )
    lock_mutations = (
        lock_text.replace(pypdf_source, pypdf_header + '\nsource = { registry = "https://example.invalid/simple" }'),
        lock_text.replace(PYPDF_SDIST_URL, "https://example.invalid/untrusted/pypdf-6.16.2.tar.gz"),
        lock_text.replace(PYPDF_WHEEL_URL, "https://example.invalid/untrusted/pypdf-6.16.2-py3-none-any.whl"),
        lock_text.replace("pypdf-6.16.2.tar.gz", "pypdf-6.16.2-forged.tar.gz", 1),
        lock_text.replace("pypdf-6.16.2-py3-none-any.whl", "pypdf-6.16.2-forged.whl", 1),
        lock_text.replace("size = 7008996", "size = 7008997", 1),
        lock_text.replace("size = 385060", "size = 385061", 1),
        lock_text.replace(pypdf_header, pypdf_header + '\ndependencies = [{ name = "google-auth" }]', 1),
        lock_text.replace(pypdf_header, pypdf_header + '\nforged = "extra-field"', 1),
        lock_text[:pypdf_block_end] + "\n" + pypdf_block + lock_text[pypdf_block_end:],
    )
    for candidate_project in project_mutations:
        with pytest.raises(AssertionError):
            _assert_pypdf_6162_contract(candidate_project, lock_text)
    for candidate_lock in lock_mutations:
        with pytest.raises(AssertionError):
            _assert_pypdf_6162_contract(project_text, candidate_lock)


def test_pypdf_refresh_preserves_unsupported_pdf_runtime_boundary() -> None:
    for path in ("backend/app/stage4.py", "tests/api/test_stage4_slice_api.py"):
        assert (ROOT / path).read_text(encoding="utf-8") == _text_at(ISSUE499_BASE, path)
    api_test = (ROOT / "tests/api/test_stage4_slice_api.py").read_text(encoding="utf-8")
    assert '("application/pdf" if case == "mime" else "text/markdown")' in api_test
    assert 'expected = "UNSUPPORTED_MEDIA_TYPE" if case in {"mime", "archive"}' in api_test


def test_google_auth_contract_rejects_direct_transitive_and_artifact_drift() -> None:
    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lock_text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    mutations = (
        (project_text.replace('"google-auth==2.56.3",\n', ""), lock_text),
        (
            project_text.replace('    "google-auth==2.56.3",\n', "").replace(
                '    "pypdf>=6.16.2",', '    "google-auth==2.56.3",\n    "pypdf>=6.16.2",'
            ),
            lock_text,
        ),
        (project_text.replace('"google-auth==2.56.3",', '"google-auth==2.56.2",'), lock_text),
        (project_text.replace('"google-auth==2.56.3",', '"google-auth==2.56.3",\n    "unexpected-provider>=1.0",'), lock_text),
        (project_text.replace('"google-auth==2.56.3",', '"google-auth==2.56.3",'), lock_text.replace('name = "pyasn1"\nversion = "0.6.4"', 'name = "unexpected-transitive"\nversion = "0.6.4"')),
        (project_text, lock_text.replace('version = "2.56.3"', 'version = "2.56.2"', 1)),
        (project_text, lock_text.replace('sha256:40e229fc901f0a305b553050e5fce562d509bee0435be053abfa91582b51b90c', 'sha256:' + '2' * 64)),
        (project_text, lock_text.replace('sha256:8ec438808f813ad034535000261eed1067475d229d05bbf4216e78c3f2362e53', 'sha256:' + '0' * 64)),
        (project_text, lock_text.replace('version = "50.0.0"', 'version = "49.0.0"', 1)),
        (project_text, lock_text.replace('sha256:031e2d5dd4bb9caa3ca9c82e5a197fd8ae680232cee62603d1a813f3f07e3d03', 'sha256:' + '3' * 64)),
        (project_text, lock_text.replace('sha256:9c447d8431c947fe4c8febc4ed9e760bc29011a5b01e5c74b67025bd9fb8ce81', 'sha256:' + '1' * 64)),
        (project_text, lock_text.replace('name = "pyasn1-modules"\nversion = "0.4.2"', 'name = "pyasn1-modules"\nversion = "0.4.1"')),
        (project_text, lock_text.replace(f'sha256:{PYPDF_SDIST_SHA256}', 'sha256:' + '4' * 64)),
    )
    for candidate_project, candidate_lock in mutations:
        with pytest.raises(AssertionError):
            _assert_pypdf_6162_contract(candidate_project, candidate_lock)


def _assert_js_yaml_431_contract(package_text: str, lock: dict[str, Any]) -> None:
    base_package = _text_at(ISSUE396_BASE, "frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_text_at(ISSUE396_BASE, "frontend/package-lock.json")))
    assert package_text == base_package
    paths = [path for path in lock["packages"] if path.endswith(JS_YAML_PATH)]
    assert paths == [JS_YAML_PATH]
    js_yaml, base_js_yaml = lock["packages"][JS_YAML_PATH], base_lock["packages"][JS_YAML_PATH]
    assert (js_yaml["version"], js_yaml["resolved"], js_yaml["integrity"]) == (
        "4.3.1",
        "https://registry.npmjs.org/js-yaml/-/js-yaml-4.3.1.tgz",
        JS_YAML_431_INTEGRITY,
    )
    assert {key: value for key, value in js_yaml.items() if key not in {"version", "resolved", "integrity"}} == {
        key: value for key, value in base_js_yaml.items() if key not in {"version", "resolved", "integrity"}
    }
    normalized = copy.deepcopy(lock)
    for path in (JS_YAML_PATH, NANOID_PATH):
        for field in ("version", "resolved", "integrity"):
            normalized["packages"][path][field] = base_lock["packages"][path][field]
    _normalize_issue495_frontend_delta(normalized, base_lock)
    assert normalized == base_lock


def test_frontend_js_yaml_lock_is_exact_isolated_and_patched() -> None:
    _assert_js_yaml_431_contract(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8"),
        json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8")),
    )


def test_js_yaml_contract_rejects_identity_integrity_and_unrelated_drift() -> None:
    package_text = _text_at(ISSUE396_BASE, "frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_text_at(ISSUE396_BASE, "frontend/package-lock.json")))
    patched = copy.deepcopy(base_lock)
    patched["packages"][JS_YAML_PATH].update(version="4.3.1", resolved="https://registry.npmjs.org/js-yaml/-/js-yaml-4.3.1.tgz", integrity=JS_YAML_431_INTEGRITY)
    mutations = []
    for field, value in (("version", "4.3.0"), ("resolved", "https://example.invalid/js-yaml.tgz"), ("integrity", "sha512-wrong")):
        candidate = copy.deepcopy(patched)
        candidate["packages"][JS_YAML_PATH][field] = value
        mutations.append((package_text, candidate))
    missing = copy.deepcopy(patched)
    del missing["packages"][JS_YAML_PATH]
    drifted = copy.deepcopy(patched)
    drifted["packages"]["node_modules/argparse"]["version"] = "0.0.0"
    mutations.extend(((package_text, missing), (package_text, drifted), (package_text + "\n", patched)))
    for candidate_package, candidate_lock in mutations:
        with pytest.raises((AssertionError, KeyError)):
            _assert_js_yaml_431_contract(candidate_package, candidate_lock)


def test_frontend_brace_expansion_override_and_lock_are_isolated_and_patched() -> None:
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    base_package, base_lock = _base_json("frontend/package.json"), _base_json("frontend/package-lock.json")

    assert package["overrides"]["brace-expansion"] == "5.0.9"
    normalized_package = copy.deepcopy(package)
    normalized_package["overrides"]["brace-expansion"] = base_package["overrides"]["brace-expansion"]
    assert normalized_package == base_package

    brace_paths = [path for path in lock["packages"] if path.endswith(BRACE_PATH)]
    assert brace_paths == [BRACE_PATH]
    brace = lock["packages"][BRACE_PATH]
    assert (brace["version"], brace["resolved"], brace["integrity"]) == (
        "5.0.9",
        "https://registry.npmjs.org/brace-expansion/-/brace-expansion-5.0.9.tgz",
        BRACE_509_INTEGRITY,
    )
    normalized_lock = copy.deepcopy(lock)
    for path in (BRACE_PATH, JS_YAML_PATH, NANOID_PATH):
        for field in ("version", "resolved", "integrity"):
            normalized_lock["packages"][path][field] = base_lock["packages"][path][field]
    _normalize_issue495_frontend_delta(normalized_lock, base_lock)
    assert normalized_lock == base_lock


def _packages(lock_path: Path) -> dict[str, set[str]]:
    data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages: dict[str, set[str]] = {}
    for package in data["package"]:
        version = package.get("version")
        if version is not None:
            packages.setdefault(package["name"], set()).add(version)
    return packages


def test_root_and_semgrep_tool_locks_are_separate_and_patched() -> None:
    validate_project_contract(ROOT, today=dt.date(2026, 8, 29))

    root_project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    tool_project = tomllib.loads(
        (ROOT / "tools/semgrep/pyproject.toml").read_text(encoding="utf-8")
    )
    root_packages = _packages(ROOT / "uv.lock")
    tool_packages = _packages(ROOT / "tools/semgrep/uv.lock")

    assert "override-dependencies" not in root_project.get("tool", {}).get("uv", {})
    assert "semgrep" not in root_packages
    assert len(root_packages["click"]) == 1
    assert Version(next(iter(root_packages["click"]))) >= Version("8.3.3")
    assert tool_project["project"]["dependencies"] == ["semgrep==1.175.0"]
    assert "override-dependencies" not in tool_project["tool"]["uv"]
    assert tool_packages["semgrep"] == {"1.175.0"}
    assert tool_packages["click"] == {"8.4.2"}
    assert tool_packages["mcp"] == {"1.29.0"}
    assert tool_packages["cryptography"] == {"50.0.0"}
    assert tool_packages["pyjwt"] == {"2.13.0"}


def test_semgrep_1_175_generated_lock_has_no_override_and_is_isolated() -> None:
    lock_bytes = (ROOT / "tools/semgrep/uv.lock").read_bytes()
    lock = tomllib.loads(lock_bytes.decode())
    base_lock = tomllib.loads(_text_at(ISSUE460_BASE, "tools/semgrep/uv.lock"))
    assert hashlib.sha256(lock_bytes).hexdigest() == "85340b301faabb76e071fe27b660f5532b54901b9d0c92e02000f16c16404416"
    assert "manifest" not in lock
    packages = {package["name"]: package for package in lock["package"]}
    assert packages["narratwin-semgrep-tool"]["dependencies"] == [{"name": "semgrep"}]
    assert packages["semgrep"]["version"] == "1.175.0"
    assert packages["mcp"]["version"] == "1.29.0"
    assert packages["click"]["version"] == "8.4.2"
    assert packages["pyjwt"]["version"] == "2.13.0"
    assert packages["cryptography"]["version"] == "50.0.0"
    assert base_lock["manifest"]["overrides"] == [{"name": "mcp", "specifier": "==1.28.1"}]
    assert [package["name"] for package in lock["package"]] == [
        package["name"] for package in base_lock["package"]
    ]
    normalized = copy.deepcopy(lock)
    normalized["manifest"] = base_lock["manifest"]
    for name in ("mcp", "narratwin-semgrep-tool", "semgrep"):
        current_index = next(
            index for index, package in enumerate(normalized["package"])
            if package["name"] == name
        )
        normalized["package"][current_index] = next(
            package for package in base_lock["package"] if package["name"] == name
        )
    assert normalized == base_lock


def test_semgrep_tool_contract_rejects_vulnerable_cryptography_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_project: dict[str, Any] = {"tool": {"uv": {}}}
    tool_project: dict[str, Any] = {
        "project": {"dependencies": ["semgrep==1.175.0"]},
        "tool": {"uv": {}},
    }
    root_lock = {"click": {"8.3.3"}}

    monkeypatch.setattr(
        semgrep_security,
        "_toml",
        lambda path: tool_project if "tools/semgrep" in str(path) else root_project,
    )
    monkeypatch.setattr(semgrep_security, "_manifest_targets", lambda root: EXPECTED_TARGETS)
    monkeypatch.setattr(
        semgrep_security,
        "_configured_rule_ids",
        lambda path: semgrep_security.EXPECTED_RULE_IDS,
    )
    monkeypatch.setattr(semgrep_security, "validate_reviewed_inputs", lambda root: None)
    monkeypatch.setattr(semgrep_security, "validate_audit_wrappers", lambda root: None)

    for version, accepted in (("49.0.0", False), ("50.0.0", True)):
        tool_lock = {
            "semgrep": {"1.175.0"},
            "click": {"8.4.2"},
            "mcp": {"1.29.0"},
            "cryptography": {version},
            "pyjwt": {"2.13.0"},
        }
        monkeypatch.setattr(
            semgrep_security,
            "_locked_versions",
            lambda path, lock=tool_lock: lock if "tools/semgrep" in str(path) else root_lock,
        )
        if accepted:
            validate_project_contract(ROOT, today=dt.date(2026, 8, 4))
        else:
            with pytest.raises(ContractError, match="cryptography"):
                validate_project_contract(ROOT, today=dt.date(2026, 8, 4))


def test_semgrep_tool_contract_rejects_any_override_and_dependency_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    root_project: dict[str, Any] = {"tool": {"uv": {}}}
    root_lock: dict[str, set[str]] = {"click": {"8.3.3"}}
    base_tool: dict[str, Any] = {"project": {"dependencies": ["semgrep==1.175.0"]}, "tool": {"uv": {}}}
    base_lock: dict[str, set[str]] = {"semgrep": {"1.175.0"}, "click": {"8.4.2"}, "mcp": {"1.29.0"}, "cryptography": {"50.0.0"}, "pyjwt": {"2.13.0"}}

    def install(tool_project: dict[str, Any], tool_lock: dict[str, set[str]]) -> None:
        monkeypatch.setattr(semgrep_security, "_toml", lambda path: tool_project if "tools/semgrep" in str(path) else root_project)
        monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: tool_lock if "tools/semgrep" in str(path) else root_lock)
        monkeypatch.setattr(semgrep_security, "_manifest_targets", lambda root: semgrep_security.EXPECTED_TARGETS)
        monkeypatch.setattr(semgrep_security, "_configured_rule_ids", lambda path: semgrep_security.EXPECTED_RULE_IDS)
        monkeypatch.setattr(semgrep_security, "validate_reviewed_inputs", lambda root: None)
        monkeypatch.setattr(semgrep_security, "validate_audit_wrappers", lambda root: None)

    for overrides in (["mcp==1.29.0"], ["click==8.4.2"], ["other==1"]):
        candidate = copy.deepcopy(base_tool)
        candidate["tool"]["uv"]["override-dependencies"] = overrides
        install(candidate, copy.deepcopy(base_lock))
        with pytest.raises(ContractError, match="overrides"):
            validate_project_contract(ROOT, today=dt.date(2026, 8, 29))
    install({**copy.deepcopy(base_tool), "project": {"dependencies": ["semgrep==1.174.0"]}}, base_lock)
    with pytest.raises(ContractError, match="Semgrep tool pin"):
        validate_project_contract(ROOT, today=dt.date(2026, 8, 29))
    install(copy.deepcopy(base_tool), {**base_lock, "mcp": {"1.28.1"}})
    with pytest.raises(ContractError, match="MCP lock"):
        validate_project_contract(ROOT, today=dt.date(2026, 8, 29))
    install(copy.deepcopy(base_tool), {**base_lock, "pyjwt": {"0.0.0"}})
    with pytest.raises(ContractError, match="PyJWT lock"):
        validate_project_contract(ROOT, today=dt.date(2026, 8, 29))
    root_lock["mcp"] = {"1.29.0"}
    install(copy.deepcopy(base_tool), copy.deepcopy(base_lock))
    with pytest.raises(ContractError, match="root lock"):
        validate_project_contract(ROOT, today=dt.date(2026, 8, 29))


def test_installed_semgrep_tool_identity_requires_locked_mcp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def dist(name: str, version: str) -> object:
        return type("Dist", (), {"metadata": {"Name": name}, "version": version})()

    site_packages = tmp_path / "semgrep-tool" / "lib"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(semgrep_security, "TOOL_ENV", tmp_path)
    lock = {"semgrep": {"1.175.0"}, "click": {"8.4.2"}, "mcp": {"1.29.0"}, "cryptography": {"50.0.0"}, "pyjwt": {"2.13.0"}}
    installed = [dist("semgrep", "1.175.0"), dist("click", "8.4.2"), dist("mcp", "1.29.0"), dist("cryptography", "50.0.0"), dist("PyJWT", "2.13.0")]
    monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: lock)
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: installed)
    validate_installed_tool(site_packages)
    installed[2] = dist("mcp", "1.23.3")
    with pytest.raises(ContractError, match="MCP identity"):
        validate_installed_tool(site_packages)


def test_installed_semgrep_tool_identity_rejects_vulnerable_cryptography(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def dist(name: str, version: str) -> object:
        return type("Dist", (), {"metadata": {"Name": name}, "version": version})()

    site_packages = tmp_path / "semgrep-tool" / "lib"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(semgrep_security, "TOOL_ENV", tmp_path)
    locked = {
        "semgrep": {"1.175.0"},
        "click": {"8.4.2"},
        "mcp": {"1.29.0"},
        "cryptography": {"50.0.0"},
        "pyjwt": {"2.13.0"},
    }
    monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: locked)
    installed = [
        dist("semgrep", "1.175.0"),
        dist("click", "8.4.2"),
        dist("mcp", "1.29.0"),
        dist("cryptography", "49.0.0"),
        dist("PyJWT", "2.13.0"),
    ]
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: installed)
    with pytest.raises(ContractError, match="cryptography"):
        validate_installed_tool(site_packages)


@pytest.mark.parametrize("version", [None, "2.12.0"])
def test_installed_semgrep_tool_identity_requires_exact_pyjwt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, version: str | None
) -> None:
    def dist(name: str, value: str) -> object:
        return type("Dist", (), {"metadata": {"Name": name}, "version": value})()

    site_packages = tmp_path / "semgrep-tool" / "lib"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(semgrep_security, "TOOL_ENV", tmp_path)
    installed = [dist("semgrep", "1.175.0"), dist("click", "8.4.2"), dist("mcp", "1.29.0"), dist("cryptography", "50.0.0")]
    if version is not None:
        installed.append(dist("PyJWT", version))
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: installed)
    with pytest.raises(ContractError, match="PyJWT identity"):
        validate_installed_tool(site_packages)


def test_security_wrapper_is_fail_closed_without_advisory_suppression() -> None:
    wrapper = (ROOT / "scripts/ci/dependency-security.sh").read_text(encoding="utf-8")
    audit_wrapper = (ROOT / "scripts/ci/dependency-audit.sh").read_text(encoding="utf-8")
    semgrep_wrapper = (ROOT / "scripts/ci/run-semgrep.sh").read_text(encoding="utf-8")
    combined = f"{wrapper}\n{audit_wrapper}\n{semgrep_wrapper}".lower()

    assert "bash scripts/ci/dependency-audit.sh" in wrapper
    assert "uv run pip-audit --strict" in audit_wrapper
    assert "--path" in audit_wrapper
    assert "python3 scripts/ci/check_semgrep_security.py installed-tool" in audit_wrapper
    assert "bash scripts/ci/run-semgrep.sh" in wrapper
    for forbidden in (
        "--ignore-vuln",
        "pysec-2026-2132",
        "cve-2026-7246",
        "ghsa-47fr-3ffg-hgmw",
        "|| true",
        "pip_audit_ignore",
    ):
        assert forbidden not in combined

    assert "semgrep scan \\\n  --validate" in semgrep_wrapper
    assert "--config semgrep.yml" in semgrep_wrapper
    assert "--error" in semgrep_wrapper
    assert "--metrics=off" in semgrep_wrapper
    assert "--json-output \"${SCAN_RESULT}\"" in semgrep_wrapper


def test_issue482_lock_refresh_is_exact_and_removes_vulnerable_versions() -> None:
    packages = {
        row["name"]: row
        for row in tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))["package"]
    }
    assert {
        name: packages[name]["version"] for name in ISSUE482_PACKAGES
    } == {name: version for name, (version, _digest) in ISSUE482_PACKAGES.items()}
    for name, (_version, digest) in ISSUE482_PACKAGES.items():
        assert hashlib.sha256(
            json.dumps(packages[name], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest() == digest
    assert not {
        ("aiohttp", "3.14.1"), ("datasets", "5.0.0"),
        ("setuptools", "81.0.0"), ("torch", "2.12.1"),
    } & {(name, package["version"]) for name, package in packages.items()}


def test_runtime_bypass_validator_covers_the_actual_audit_wrapper(tmp_path: Path) -> None:
    for relative_path in (
        "scripts/ci/dependency-audit.sh",
        "scripts/ci/dependency-security.sh",
        "scripts/ci/run-semgrep.sh",
    ):
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("set -euo pipefail\n", encoding="utf-8")

    validate_audit_wrappers(tmp_path)
    (tmp_path / "scripts/ci/dependency-audit.sh").write_text(
        "uv run pip-audit --ignore-vuln example\n", encoding="utf-8"
    )
    with pytest.raises(ContractError, match="forbidden audit bypass"):
        validate_audit_wrappers(tmp_path)


def test_reviewed_semgrep_inputs_are_hash_bound(tmp_path: Path) -> None:
    for relative_path in REVIEWED_INPUTS:
        source = ROOT / relative_path
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    manifest = tmp_path / "tools/semgrep/reviewed-inputs.sha256"
    manifest.write_text(
        "".join(
            f"{hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()}  {path}\n"
            for path in REVIEWED_INPUTS
        ),
        encoding="utf-8",
    )
    validate_reviewed_inputs(tmp_path)

    with (tmp_path / "semgrep.yml").open("a", encoding="utf-8") as config:
        config.write("\n")
    with pytest.raises(ContractError, match="changed without compatibility review"):
        validate_reviewed_inputs(tmp_path)


def test_semgrep_target_manifest_is_exact_and_independently_guarded() -> None:
    manifest = ROOT / "scripts/ci/semgrep-targets.txt"
    actual = tuple(
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )
    assert actual == EXPECTED_TARGETS

    shrunk = actual[:-1]
    assert len(shrunk) != len(EXPECTED_TARGETS)


def test_repository_scan_requires_files_no_errors_and_zero_findings() -> None:
    payload: dict[str, Any] = {
        "errors": [],
        "results": [],
        "paths": {"scanned": ["backend/app/main.py"]},
        "time": {},
    }
    validate_scan_result(payload)

    mutation: dict[str, Any]
    for mutation in (
        {"paths": {"scanned": []}},
        {"errors": [{"message": "parse failure"}]},
        {"results": [{"check_id": "python-exec-eval"}]},
    ):
        candidate = copy.deepcopy(payload)
        candidate.update(mutation)
        with pytest.raises(ContractError):
            validate_scan_result(candidate)

    with pytest.raises(ContractError):
        validate_rule_ids(())


def test_semgrep_canary_requires_one_finding_and_both_files() -> None:
    payload: dict[str, Any] = {
        "errors": [],
        "paths": {
            "scanned": [
                "scripts/ci/fixtures/semgrep/clean.py",
                "scripts/ci/fixtures/semgrep/positive.py",
            ]
        },
        "results": [
            {
                "check_id": "scripts.ci.narratwin-semgrep-canary",
                "path": "scripts/ci/fixtures/semgrep/positive.py",
            }
        ],
    }
    validate_canary_result(payload)

    mutation: dict[str, Any]
    for mutation in (
        {"results": []},
        {"paths": {"scanned": ["scripts/ci/fixtures/semgrep/positive.py"]}},
        {"errors": [{"message": "engine failure"}]},
    ):
        candidate = copy.deepcopy(payload)
        candidate.update(mutation)
        with pytest.raises(ContractError):
            validate_canary_result(candidate)


def test_removed_override_has_no_calendar_expiry() -> None:
    assert not hasattr(semgrep_security, "OVERRIDE_EXPIRY")
    validate_project_contract(ROOT, today=dt.date(2030, 1, 1))


def test_backend_build_requires_explicit_click_and_semgrep_inventory() -> None:
    docker_build = (ROOT / "scripts/ci/docker-build.sh").read_text(encoding="utf-8")
    inventory = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(
        encoding="utf-8"
    )

    assert (
        "BACKEND_IMAGE=narratwin-ai-backend:ci "
        "bash scripts/ci/backend-image-package-check.sh"
    ) in docker_build
    assert 'importlib.metadata.version("click")' in inventory
    assert "click_version < (8, 3, 3)" in inventory
    assert 'importlib.metadata.version("semgrep")' in inventory
