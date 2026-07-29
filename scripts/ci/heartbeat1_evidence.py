#!/usr/bin/env python3
"""Fail-closed Heartbeat 1 privacy materialization and evidence scanning."""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, NoReturn, TypedDict
from urllib.parse import quote_from_bytes, quote_plus

ENCODING_NAMES = (
    "UTF-8 bytes", "hex", "Base64", "url-safe Base64", "percent-encoded", "JSON-escaped UTF-8",
)
FIXTURE_NAMES = ("PUBLIC_FIXTURE", "INTERNAL_FIXTURE", "canary")
MAX_SCAN_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 2_000
MAX_ARCHIVE_DEPTH = 3
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
PERCENT_ESCAPE = re.compile(rb"%[0-9A-Fa-f]{2}")
IMPORT = re.compile(r"(?:\bfrom\s+|\bimport\s*)[\"']([^\"']+)[\"']")
COMPUTED_MEMBER = re.compile(r"\b(?P<base>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\[\s*[A-Za-z_$'\"`]|[)\]]\s*\[\s*[A-Za-z_$'\"`]|\?\.\s*\[\s*[A-Za-z_$'\"`]")
ALLOWED_BROWSER_IMPORTS = {"@playwright/test", "node:fs/promises", "node:path"}
FORBIDDEN_BROWSER_TOKENS = (
    "route", ".fulfill(", "['fulfill']",
    '["fulfill"]', ".fallback(", ".continue(", ".postdata", "postdatabuffer", "request.newcontext",
    "fetch(", "xmlhttprequest", "navigator.serviceworker", "serviceworker.register", "service-worker", "msw", "fetch-mock", "nock",
    "require(", "import(", "{[", "reflect.", "getownproperty", "proxy(", "8122", "http://127.0.0.1:8122", "http://localhost:8122",
)


class EvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ScanStats(TypedDict):
    fileCount: int
    archiveCount: int
    memberCount: int
    byteCount: int
    matchCount: int
    aggregateSha256: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded_patterns(value: bytes) -> dict[str, bytes]:
    try:
        decoded = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError("FIXTURE_UTF8_INVALID") from exc
    return {
        "UTF-8 bytes": value,
        "hex": value.hex().encode(),
        "Base64": base64.b64encode(value),
        "url-safe Base64": base64.urlsafe_b64encode(value),
        "percent-encoded": b"".join(f"%{byte:02X}".encode() for byte in value),
        "JSON-escaped UTF-8": json.dumps(decoded, ensure_ascii=True)[1:-1].encode(),
    }


def _patterns(*values: bytes) -> tuple[bytes, ...]:
    patterns: set[bytes] = set()
    for value in values:
        encodings = encoded_patterns(value)
        patterns.update(encodings.values())
        quoted = quote_from_bytes(value, safe="").encode()
        form_quoted = quote_plus(value.decode("utf-8"), safe="").encode()
        patterns.update({encodings["hex"].upper(), encodings["Base64"].rstrip(b"="), encodings["url-safe Base64"].rstrip(b"=")})
        patterns.update({quoted, form_quoted})
    return tuple(pattern for pattern in patterns if pattern)


def _check(data: bytes, patterns: tuple[bytes, ...]) -> None:
    if any(pattern in data for pattern in patterns):
        raise EvidenceError("CONTROLLED_MATCH")
    normalized = PERCENT_ESCAPE.sub(lambda match: match.group().upper(), data)
    if any(PERCENT_ESCAPE.search(pattern) and PERCENT_ESCAPE.sub(lambda match: match.group().upper(), pattern) in normalized for pattern in patterns):
        raise EvidenceError("CONTROLLED_MATCH")


def _scan_archive(data: bytes, patterns: tuple[bytes, ...], stats: ScanStats, depth: int) -> None:
    if depth > MAX_ARCHIVE_DEPTH:
        raise EvidenceError("ARCHIVE_LIMIT")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_ARCHIVE_MEMBERS:
                raise EvidenceError("ARCHIVE_LIMIT")
            stats["archiveCount"] += 1
            for member in members:
                if member.flag_bits & 1 or member.file_size > MAX_SCAN_BYTES:
                    raise EvidenceError("ARCHIVE_INVALID")
                _check(member.filename.encode("utf-8", "surrogatepass") + member.comment + member.extra, patterns)
                payload = archive.read(member)
                stats["memberCount"] += 1
                stats["byteCount"] += len(payload)
                if stats["memberCount"] > MAX_ARCHIVE_MEMBERS or stats["byteCount"] > MAX_SCAN_BYTES:
                    raise EvidenceError("ARCHIVE_LIMIT")
                stats["aggregateSha256"] = sha256(
                    (stats["aggregateSha256"] + sha256(payload)).encode()
                )
                _check(payload, patterns)
                nested_archive = zipfile.is_zipfile(io.BytesIO(payload))
                if (member.filename.lower().endswith(".zip") or payload.startswith(ZIP_MAGIC)) and not nested_archive:
                    raise EvidenceError("ARCHIVE_INVALID")
                if nested_archive:
                    _scan_archive(payload, patterns, stats, depth + 1)
    except EvidenceError:
        raise
    except (OSError, RuntimeError, UnicodeError, zipfile.BadZipFile) as exc:
        raise EvidenceError("ARCHIVE_INVALID") from exc


def _files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_symlink() or not path.exists():
            raise EvidenceError("SCAN_INPUT_INVALID")
        candidates = [path] if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if candidate.is_symlink():
                raise EvidenceError("SCAN_INPUT_INVALID")
            if candidate.is_file():
                files.append(candidate)
    return files


def scan_evidence(paths: Iterable[Path], *, controlled: bytes, canary: bytes) -> ScanStats:
    patterns = _patterns(controlled, canary)
    stats: ScanStats = {
        "fileCount": 0,
        "archiveCount": 0,
        "memberCount": 0,
        "byteCount": 0,
        "matchCount": 0,
        "aggregateSha256": sha256(b""),
    }
    for path in _files(paths):
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise EvidenceError("SCAN_INPUT_INVALID") from exc
        stats["fileCount"] += 1
        stats["byteCount"] += len(data)
        if stats["byteCount"] > MAX_SCAN_BYTES:
            raise EvidenceError("SCAN_LIMIT")
        _check(data, patterns)
        is_archive = zipfile.is_zipfile(io.BytesIO(data))
        if (path.suffix.lower() == ".zip" or data.startswith(ZIP_MAGIC)) and not is_archive:
            raise EvidenceError("ARCHIVE_INVALID")
        if is_archive:
            _scan_archive(data, patterns, stats, 1)
    return stats


def fixture_constants(source: Path) -> dict[str, bytes]:
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise EvidenceError("FIXTURE_SOURCE_INVALID") from exc
    found: dict[str, bytes] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in FIXTURE_NAMES:
                if name in found or not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, bytes):
                    raise EvidenceError("FIXTURE_SOURCE_INVALID")
                found[name] = node.value.value
    if set(found) != set(FIXTURE_NAMES) or any(not found[name] for name in FIXTURE_NAMES):
        raise EvidenceError("FIXTURE_SOURCE_INVALID")
    return found


def materialize(source: Path, runtime: Path) -> dict[str, Any]:
    values = fixture_constants(source)
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime.chmod(0o700)
    for name, filename in (("PUBLIC_FIXTURE", "public.md"), ("INTERNAL_FIXTURE", "internal.md"), ("canary", "canary.bin")):
        destination = runtime / filename
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(values[name])
        destination.chmod(0o600)
    return {
        "schema": "heartbeat1-runtime-input-v1",
        "publicBytes": len(values["PUBLIC_FIXTURE"]), "publicSha256": sha256(values["PUBLIC_FIXTURE"]),
        "internalBytes": len(values["INTERNAL_FIXTURE"]), "internalSha256": sha256(values["INTERNAL_FIXTURE"]),
        "canaryBytes": len(values["canary"]), "canarySha256": sha256(values["canary"]),
    }


def scan_browser_sources(entry: Path, head_sha: str | None = None) -> dict[str, Any]:
    pending, seen, digest = [entry.resolve()], set(), hashlib.sha256()
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file() or path.is_symlink():
            if path not in seen:
                raise EvidenceError("BROWSER_SOURCE_INVALID")
            continue
        seen.add(path)
        data = path.read_bytes()
        if head_sha:
            try:
                relative = path.relative_to(Path.cwd().resolve()).as_posix()
            except ValueError as exc:
                raise EvidenceError("BROWSER_SOURCE_INVALID") from exc
            committed = subprocess.run(
                ["git", "show", f"{head_sha}:{relative}"], capture_output=True, check=False
            )
            if committed.returncode or committed.stdout != data:
                raise EvidenceError("BROWSER_HEAD_MISMATCH")
        text = data.decode("utf-8")
        compact = re.sub(r"\s+", "", text).lower()
        comment_probe = text.replace("http://127.0.0.1:3122", "")
        if "/*" in comment_probe or "//" in comment_probe or any(token in compact for token in FORBIDDEN_BROWSER_TOKENS):
            raise EvidenceError("FORBIDDEN_BROWSER_SOURCE")
        if any(match.group("base") not in {"const", "let", "var", "return"} for match in COMPUTED_MEMBER.finditer(text)):
            raise EvidenceError("FORBIDDEN_BROWSER_SOURCE")
        digest.update(sha256(data).encode())
        for match in IMPORT.finditer(text):
            specifier = match.group(1)
            if not specifier.startswith("."):
                if specifier not in ALLOWED_BROWSER_IMPORTS:
                    raise EvidenceError("BROWSER_SOURCE_INVALID")
                continue
            target = (path.parent / specifier).resolve()
            options = [target, target.with_suffix(".ts"), target.with_suffix(".tsx"), target / "index.ts"]
            resolved = next((option for option in options if option.is_file()), None)
            if resolved is None:
                raise EvidenceError("BROWSER_SOURCE_INVALID")
            pending.append(resolved)
    return {"entry": entry.as_posix(), "fileCount": len(seen), "aggregateSha256": digest.hexdigest(), "forbiddenMatchCount": 0}


def failure_summary(run_id: str, code: str, *, files: int = 0, members: int = 0, byte_count: int = 0) -> dict[str, Any]:
    return {"schema": "heartbeat1-privacy-failure-v1", "runId": run_id, "outcome": "WITHHELD", "failureCode": code, "filesScanned": files, "membersScanned": members, "bytesScanned": byte_count}


def _path_digest(path: Path) -> dict[str, Any]:
    digest, count, size = hashlib.sha256(), 0, 0
    base = path.resolve() if path.is_dir() else path.resolve().parent
    for candidate in _files([path]):
        data = candidate.read_bytes()
        relative = candidate.resolve().relative_to(base).as_posix()
        digest.update(relative.encode() + b"\0" + sha256(data).encode())
        count, size = count + 1, size + len(data)
    return {"path": path.as_posix(), "sha256": digest.hexdigest(), "byteCount": size, "fileCount": count}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _main(argv: list[str]) -> int:
    class SafeParser(argparse.ArgumentParser):
        def error(self, message: str) -> NoReturn:
            raise EvidenceError("ARGUMENT_INVALID")

    parser = SafeParser(add_help=False)
    parser.add_argument("command", choices=("materialize", "scan"))
    parser.add_argument("--fixture-source", required=True)
    parser.add_argument("--runtime-dir")
    parser.add_argument("--metadata-output")
    parser.add_argument("--run-id", default="materialize")
    parser.add_argument("--head-sha")
    parser.add_argument("--browser-entry")
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--failure-output")
    args = parser.parse_args(argv)
    if args.command == "materialize":
        if not args.runtime_dir or not args.metadata_output:
            raise EvidenceError("ARGUMENT_INVALID")
        _write(
            Path(args.metadata_output),
            materialize(Path(args.fixture_source), Path(args.runtime_dir)),
        )
        return 0
    if not RUN_ID.match(args.run_id) or not args.head_sha or not SHA.match(args.head_sha) or not args.browser_entry or not args.output or not args.failure_output or not args.input:
        raise EvidenceError("ARGUMENT_INVALID")
    values = fixture_constants(Path(args.fixture_source))
    inputs = [Path(value) for value in args.input]
    source = Path(__file__).resolve()
    committed = subprocess.run(
        ["git", "show", f"{args.head_sha}:scripts/ci/heartbeat1_evidence.py"],
        capture_output=True,
        check=False,
    ).stdout
    source_bytes = source.read_bytes()
    if committed != source_bytes:
        raise EvidenceError("SCANNER_HEAD_MISMATCH")
    graphs = [
        scan_browser_sources(Path(args.browser_entry), args.head_sha),
        scan_browser_sources(Path("frontend/playwright.heartbeat1.config.ts"), args.head_sha),
    ]
    browser_graph = {"entries": graphs, "fileCount": sum(item["fileCount"] for item in graphs), "aggregateSha256": sha256("".join(item["aggregateSha256"] for item in graphs).encode()), "forbiddenMatchCount": 0}
    input_bindings = [_path_digest(path) for path in inputs]
    stats = scan_evidence(inputs, controlled=values["INTERNAL_FIXTURE"], canary=values["canary"])
    if input_bindings != [_path_digest(path) for path in inputs]:
        raise EvidenceError("SCAN_INPUT_CHANGED")
    pattern_count = len(_patterns(values["INTERNAL_FIXTURE"], values["canary"]))
    percent_pattern_count = sum(PERCENT_ESCAPE.search(pattern) is not None for pattern in _patterns(values["INTERNAL_FIXTURE"], values["canary"]))
    scan_units = stats["fileCount"] + (2 * stats["memberCount"])
    report = {"schema": "heartbeat1-privacy-evidence-v1", "runId": args.run_id, "headSha": args.head_sha, "outcome": "ZERO_MATCH", "scanner": {"path": "scripts/ci/heartbeat1_evidence.py", "sourceSha256": sha256(source_bytes), "headMatches": True}, "controlledInput": {"byteCount": len(values["INTERNAL_FIXTURE"]), "sha256": sha256(values["INTERNAL_FIXTURE"])}, "canary": {"byteCount": len(values["canary"]), "sha256": sha256(values["canary"])}, "encodingSet": list(ENCODING_NAMES), "browserSourceGraph": browser_graph, "inputs": input_bindings, "recursiveMembers": {"archiveCount": stats["archiveCount"], "memberCount": stats["memberCount"], "byteCount": stats["byteCount"]}, "patternCount": pattern_count, "normalizedPercentPatternCount": percent_pattern_count, "scanUnitCount": scan_units, "zeroMatchCount": scan_units * (pattern_count + percent_pattern_count), "matchCount": 0}
    report["recursiveMembers"]["aggregateSha256"] = stats["aggregateSha256"]
    _write(Path(args.output), report)
    return 0


def main() -> int:
    try:
        return _main(sys.argv[1:])
    except Exception as exc:
        run_id, failure = "withheld", None
        code = exc.code if isinstance(exc, EvidenceError) else "UNEXPECTED_FAILURE"
        for index, value in enumerate(sys.argv):
            if (
                value == "--run-id"
                and index + 1 < len(sys.argv)
                and RUN_ID.match(sys.argv[index + 1])
            ):
                run_id = sys.argv[index + 1]
            if value == "--failure-output" and index + 1 < len(sys.argv):
                failure = Path(sys.argv[index + 1])
        if failure:
            try:
                _write(failure, failure_summary(run_id, code))
            except Exception:
                pass
        print("HEARTBEAT1_EVIDENCE_WITHHELD", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
