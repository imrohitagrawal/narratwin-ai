#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


BASE_IMAGE = (
    "docker.io/library/python:3.13-alpine@"
    "sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
)
EXPECTED_PLATFORM_DIGESTS = {
    "linux/amd64": "sha256:c25cdd83c6d9613de985ca971f41913c039f8f4d448c3058fd17c7f5f00a36be",
    "linux/arm64": "sha256:051506d858e750104f80a63465684f260ce2eeb220a24446a56f5ecc1609ecc8",
}
EXPECTED_FILE_HASHES = {
    "Lib/tarfile.py": "f99f0cbe945dd0519029612b74f60821371aeeea04c68ad424673ff49fde8da8",
    "Lib/html/parser.py": "9e905368ac7fdc15d335aa7678655ee397c955107fb3b8424f66d02824632c10",
}
EXPECTED_PATCHES = (
    ("CVE-2026-11972", "3f031d431f80668e14f3bc066bbf4369cd9281b9", "Lib/tarfile.py", EXPECTED_FILE_HASHES["Lib/tarfile.py"], "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b"),
    ("CVE-2026-11940", "771d12dda5140313db0ac550292987975651bbde", "Lib/tarfile.py", "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b", "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52"),
    ("CVE-2026-15308", "7933f4bf7131aa4140750f9404f5de0aa2969ced", "Lib/html/parser.py", EXPECTED_FILE_HASHES["Lib/html/parser.py"], "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2"),
)


class BackportError(RuntimeError):
    pass


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _stdlib_path(root: Path, manifest_path: str) -> Path:
    if not manifest_path.startswith("Lib/"):
        raise BackportError("unsupported path")
    candidate = root / manifest_path
    if candidate.exists():
        return candidate
    return root / manifest_path.removeprefix("Lib/")


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return validate_manifest(data)


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "CPythonSecurityBackportsV1":
        raise BackportError("invalid schema")
    base = manifest.get("base")
    if base != {
        "image": BASE_IMAGE,
        "python": "3.13.14",
        "platform_digests": EXPECTED_PLATFORM_DIGESTS,
        "file_sha256": EXPECTED_FILE_HASHES,
    }:
        raise BackportError("invalid base")
    patches = manifest.get("patches")
    if not isinstance(patches, list) or len(patches) != len(EXPECTED_PATCHES):
        raise BackportError("invalid patch count")
    for index, (patch, expected) in enumerate(zip(patches, EXPECTED_PATCHES, strict=True)):
        cve, commit, path, before, after = expected
        expected_fields = {
            "cve": cve,
            "commit": commit,
            "path": path,
            "before_sha256": before,
            "after_sha256": after,
        }
        if {key: patch.get(key) for key in expected_fields} != expected_fields:
            raise BackportError(f"invalid patch {index}")
        if not isinstance(patch.get("old"), str) or not patch["old"]:
            raise BackportError("missing old hunk")
        if not isinstance(patch.get("new"), str) or not patch["new"]:
            raise BackportError("missing new hunk")
    return manifest


def apply_backports(root: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    manifest = validate_manifest(manifest)
    virtual: dict[Path, str] = {}
    touched: list[tuple[Path, str, str]] = []
    for patch in manifest["patches"]:
        target = _stdlib_path(root, patch["path"])
        if not target.is_file():
            raise BackportError(f"missing target: {patch['path']}")
        text = virtual.get(target)
        if text is None:
            text = target.read_text(encoding="utf-8")
        if _sha256_text(text) != patch["before_sha256"]:
            raise BackportError(f"preimage mismatch: {patch['path']}")
        if text.count(patch["old"]) != 1:
            raise BackportError(f"hunk mismatch: {patch['path']}")
        patched = text.replace(patch["old"], patch["new"], 1)
        actual = _sha256_text(patched)
        if actual != patch["after_sha256"]:
            raise BackportError(f"postimage mismatch: {target.name}")
        virtual[target] = patched
        touched.append((target, patch["cve"], actual))

    for target, text in virtual.items():
        target.write_text(text, encoding="utf-8")
    return [{"cve": cve, "path": str(target), "sha256": actual} for target, cve, actual in touched]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = apply_backports(args.root, load_manifest(args.manifest))
    except BackportError as exc:
        raise SystemExit(f"backport verification failed: {exc}") from None
    print(json.dumps({"status": "pass", "applied": evidence}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
