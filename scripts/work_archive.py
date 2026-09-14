"""Offline work-archive integrity checks; neither semantic approval nor backup proof."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
from io import BufferedReader
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Iterator, NoReturn, cast


# Stable identities of the reviewed recovery package, not operational limits.
MAPPING = "docs/governance/superset-mapping-v2.json"
PACKAGE = "docs/work-archive/2026-09-14-recovery"
DEFAULT_INDEX = PACKAGE + "/INDEX.json"
DEFAULT_GIT_TIMEOUT_SECONDS = 5.0
ARTIFACT_IDS = {"A", "B", "B0", "C", "I", "IM", "L", "P", "R"}
REQUIRED_DOCS = {
    "docs/work-archive/README.md", "docs/work-archive/PROCESS.md",
    "docs/governance/NARRATWIN_MASTER_PROGRAM_V2.md",
    *(PACKAGE + "/" + name for name in
      ("COMPARISON_AND_AMENDMENT.md", "DECISIONS.md", "REVIEW.md")),
}


class ArchiveError(ValueError):
    """Only fixed, non-sensitive diagnostic codes cross the CLI boundary."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, "INVALID_ARGUMENTS\n")


def positive_seconds(value: str) -> float:
    try:
        seconds = float(value)
        if math.isfinite(seconds) and seconds > 0:
            return seconds
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("timeout must be finite and positive")


def require(condition: bool, code: str = "INDEX_INVALID") -> None:
    if not condition:
        raise ArchiveError(code)


def relative(value: Any) -> str:
    require(isinstance(value, str) and bool(value), "UNSAFE_PATH")
    require(not any(c in value for c in ("\\", "\x00", "\n", "\r")), "UNSAFE_PATH")
    parts = value.split("/")
    require(all(p not in ("", ".", "..") for p in parts), "UNSAFE_PATH")
    require(not PurePosixPath(value).is_absolute(), "UNSAFE_PATH")
    return cast(str, value)


def root_path(value: Path) -> Path:
    path = value.absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "UNSAFE_PATH")
    require(path.is_dir(), "ROOT_UNAVAILABLE")
    return path


@contextmanager
def opened(root: Path, name: str) -> Iterator[BufferedReader]:
    """Open each component without following links, including intermediate directories."""
    parts = relative(name).split("/")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(child, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "UNSAFE_PATH")
            yield stream
    finally:
        os.close(fd)


def read(root: Path, name: str) -> bytes:
    with opened(root, name) as stream:
        return stream.read()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def decoded(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=pairs)


def shape(value: Any, keys: set[str]) -> None:
    require(isinstance(value, dict) and set(value) == keys)


def descriptor(value: Any, path_key: str = "path", extra: set[str] | None = None) -> None:
    shape(value, {path_key, "sha256", "bytes"} | (extra or set()))
    relative(value[path_key])
    require(type(value["bytes"]) is int and value["bytes"] >= 0)
    require(isinstance(value["sha256"], str) and
            re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None)


def matched(root: Path, entry: dict[str, Any], code: str, path_key: str = "path") -> None:
    try:
        with opened(root, entry[path_key]) as stream:
            require(os.fstat(stream.fileno()).st_size == entry["bytes"], code + "_CORRUPT")
            require(hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"],
                    code + "_CORRUPT")
    except FileNotFoundError as exc:
        raise ArchiveError(code + "_MISSING") from exc


def expected_artifacts(mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require(isinstance(mapping, dict), "AUTHORITY_CENSUS_INVALID")
    overlay = mapping.get("externalSemanticCorrectionOverlay")
    require(isinstance(overlay, dict), "AUTHORITY_CENSUS_INVALID")
    review = cast(dict[str, Any], overlay)["exhaustiveReview"]
    require(isinstance(review, dict) and isinstance(review.get("artifacts"), dict)
            and isinstance(review.get("independentValidator"), dict), "AUTHORITY_CENSUS_INVALID")
    expected = dict(review["artifacts"])
    require(set(expected) == ARTIFACT_IDS and all(isinstance(v, dict) for v in expected.values()),
            "AUTHORITY_CENSUS_INVALID")
    expected["VALIDATOR"] = review["independentValidator"]
    sources = mapping.get("sources")
    require(isinstance(sources, list), "AUTHORITY_CENSUS_INVALID")
    owners = []
    for source in cast(list[Any], sources):
        require(isinstance(source, dict), "AUTHORITY_CENSUS_INVALID")
        origin = source.get("authorityOrigin")
        require(isinstance(origin, dict), "AUTHORITY_CENSUS_INVALID")
        if origin.get("kind") == "RESTRICTED_OWNER_MESSAGE":
            owners.append(origin)
    require(len(owners) == 1, "AUTHORITY_CENSUS_INVALID")
    owner = owners[0]
    expected["OWNER_PLAN"] = dict(restrictedEvidenceRef=owner["reference"],
                                  fileSha256=owner["contentSha256"], byteCount=owner["byteCount"])
    return expected


def public_index(repo: Path, index_name: str,
                 git_timeout_seconds: float = DEFAULT_GIT_TIMEOUT_SECONDS) -> dict[str, Any]:
    require(type(git_timeout_seconds) in (int, float) and math.isfinite(git_timeout_seconds)
            and git_timeout_seconds > 0, "INVALID_CONFIGURATION")
    data = read(repo, index_name)
    index = decoded(data)
    shape(index, {"schemaVersion", "mapping", "artifacts", "publicDocuments", "handoffPath",
                  "privateInventory", "backup", "semanticAcceptance"})
    require(type(index["schemaVersion"]) is int and index["schemaVersion"] == 1)
    require(index["backup"] == "UNPROVED" and index["semanticAcceptance"] == "NOT_GRANTED",
            "UNSUPPORTED_ACCEPTANCE_CLAIM")
    shape(index["mapping"], {"path", "sha256"})
    require(index["mapping"]["path"] == MAPPING, "AUTHORITY_MISMATCH")
    mapping_data = read(repo, MAPPING)
    require(hashlib.sha256(mapping_data).hexdigest() == index["mapping"]["sha256"],
            "AUTHORITY_MISMATCH")
    expected = expected_artifacts(decoded(mapping_data))
    require(isinstance(index["artifacts"], list))
    ids, names, refs = set(), set(), set()
    for entry in index["artifacts"]:
        descriptor(entry, "privatePath", {"id", "restrictedEvidenceRef"})
        key, name, ref = entry["id"], entry["privatePath"], entry["restrictedEvidenceRef"]
        require(isinstance(key, str) and key in expected and key not in ids, "ARTIFACT_CENSUS_INVALID")
        require(isinstance(ref, str) and ref.startswith("restricted-evidence:") and ref not in refs)
        require(name not in names, "DUPLICATE_PATH")
        source = expected[key]
        require(entry["sha256"] == source["fileSha256"] and ref == source["restrictedEvidenceRef"],
                "AUTHORITY_MISMATCH")
        if "byteCount" in source:
            require(type(source["byteCount"]) is int and entry["bytes"] == source["byteCount"],
                    "AUTHORITY_MISMATCH")
        ids.add(key)
        names.add(name)
        refs.add(ref)
    require(ids == set(expected), "ARTIFACT_CENSUS_INVALID")
    descriptor(index["privateInventory"])
    require(index["privateInventory"]["path"] == "PRIVATE_INVENTORY.json")
    require("PRIVATE_INVENTORY.json" not in names)
    require(isinstance(index["publicDocuments"], list))
    docs: set[str] = set()
    for entry in index["publicDocuments"]:
        descriptor(entry)
        require(entry["path"] not in docs and entry["path"] in REQUIRED_DOCS, "PUBLIC_CENSUS_INVALID")
        docs.add(entry["path"])
        matched(repo, entry, "PUBLIC_DOCUMENT")
    require(docs == REQUIRED_DOCS, "PUBLIC_CENSUS_INVALID")
    require(index["handoffPath"] == PACKAGE + "/HANDOFF.md", "HANDOFF_INVALID")
    handoff = read(repo, index["handoffPath"]).decode("utf-8")
    markers = re.findall(r"^INDEX_SHA256:.*$", handoff, re.MULTILINE)
    require(markers == ["INDEX_SHA256: " + hashlib.sha256(data).hexdigest()], "HANDOFF_STALE")
    tracked = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"],
                             capture_output=True, check=False, timeout=git_timeout_seconds)
    require(tracked.returncode == 0, "TRACKED_CHECK_UNAVAILABLE")
    for path in tracked.stdout.split(b"\x00"):
        parts = path.split(b"/")
        require(b".restricted" not in parts and parts[-1] != b"PRIVATE_INVENTORY.json",
                "RESTRICTED_FILE_TRACKED")
    return cast(dict[str, Any], index)


def private_files(root: Path, index: dict[str, Any]) -> int:
    for entry in index["artifacts"]:
        matched(root, entry, "PRIVATE", "privatePath")
    inventory_entry = index["privateInventory"]
    matched(root, inventory_entry, "PRIVATE_INVENTORY")
    inventory = decoded(read(root, inventory_entry["path"]))
    require(isinstance(inventory, dict) and type(inventory.get("schemaVersion")) is int
            and inventory["schemaVersion"] == 1
            and inventory.get("sensitivity") == "RESTRICTED_LOCAL_ONLY", "PRIVATE_INVENTORY_INVALID")
    require(isinstance(inventory.get("files"), list), "PRIVATE_INVENTORY_INVALID")
    entries: dict[str, dict[str, Any]] = {}
    for entry in inventory["files"]:
        descriptor(entry)
        require(entry["path"] not in entries and entry["path"] != inventory_entry["path"],
                "PRIVATE_INVENTORY_INVALID")
        matched(root, entry, "PRIVATE_INVENTORY")
        entries[entry["path"]] = entry
    for master in index["artifacts"]:
        expected = dict(path=master["privatePath"], sha256=master["sha256"], bytes=master["bytes"])
        require(entries.get(master["privatePath"]) == expected, "PRIVATE_INVENTORY_INVALID")
    actual = set()
    for directory, directories, files in os.walk(root, followlinks=False, onerror=raise_walk_error):
        for name in directories + files:
            path = Path(directory) / name
            require(not path.is_symlink(), "UNSAFE_PATH")
        for name in files:
            actual.add((Path(directory) / name).relative_to(root).as_posix())
    require(actual == set(entries) | {inventory_entry["path"]}, "PRIVATE_INVENTORY_CENSUS_INVALID")
    return len(entries)


def raise_walk_error(error: OSError) -> None:
    raise ArchiveError("PRIVATE_INVENTORY_UNAVAILABLE") from error


def main(argv: list[str] | None = None) -> int:
    parser = SafeParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--index", default=DEFAULT_INDEX, help="repository-relative index path")
    parser.add_argument("--private-root", type=Path, help="explicit local archive; never accessed by default")
    parser.add_argument("--git-timeout-seconds", type=positive_seconds,
                        default=DEFAULT_GIT_TIMEOUT_SECONDS, help="finite positive Git timeout")
    args = parser.parse_args(argv)
    report: dict[str, Any] = dict(publicIndex="NOT_CHECKED", privateAvailability="NOT_CHECKED",
                                  backup="UNPROVED", semanticAcceptance="NOT_GRANTED",
                                  effectiveConfiguration={"gitTimeoutSeconds": args.git_timeout_seconds})
    phase = "publicIndex"
    try:
        repo = root_path(args.repo_root)
        index = public_index(repo, relative(args.index), args.git_timeout_seconds)
        report[phase] = "VALID"
        if args.private_root is not None:
            phase = "privateAvailability"
            report["inventoryFilesVerified"] = private_files(root_path(args.private_root), index)
            report[phase] = "VERIFIED"
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.TimeoutExpired) as exc:
        report[phase] = "FAILED"
        report["error"] = str(exc) if isinstance(exc, ArchiveError) else "INVALID_OR_UNREADABLE_INPUT"
        print(json.dumps(report, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
