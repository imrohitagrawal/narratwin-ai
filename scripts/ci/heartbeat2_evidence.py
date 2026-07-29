#!/usr/bin/env python3
"""Independent fail-closed verifier for Heartbeat 2 browser evidence."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, NoReturn

SHA = re.compile(r"^[0-9a-f]{40}$")
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
WRITES = ("project", "submit", "approve", "ingest", "walkthrough", "multilingual", "consent", "render")
MAX_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 1_000


class EvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(root: Path, relative: str) -> Any:
    path = _path(root, relative)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("EVIDENCE_JSON") from exc


def _path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise EvidenceError("EVIDENCE_PATH")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceError("EVIDENCE_PATH") from exc
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("EVIDENCE_PATH")
    return path


def _scan(paths: Iterable[Path], forbidden: tuple[bytes, ...]) -> tuple[int, int]:
    files = members = size = 0
    pending = list(paths)
    while pending:
        path = pending.pop()
        if path.is_symlink() or not path.is_file():
            raise EvidenceError("EVIDENCE_PATH")
        data = path.read_bytes()
        files += 1
        size += len(data)
        if size > MAX_BYTES or any(value and value in data for value in forbidden):
            raise EvidenceError("FORBIDDEN_MATERIAL" if size <= MAX_BYTES else "EVIDENCE_LIMIT")
        if path.suffix.lower() == ".zip" or data.startswith(b"PK"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for member in archive.infolist():
                        member_path = Path(member.filename)
                        if member_path.is_absolute() or ".." in member_path.parts or member.is_dir():
                            raise EvidenceError("ARCHIVE_INVALID")
                        payload = archive.read(member)
                        members += 1
                        size += len(payload)
                        if members > MAX_MEMBERS or size > MAX_BYTES or any(value and value in payload for value in forbidden):
                            raise EvidenceError("FORBIDDEN_MATERIAL" if size <= MAX_BYTES else "EVIDENCE_LIMIT")
            except EvidenceError:
                raise
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise EvidenceError("ARCHIVE_INVALID") from exc
    return files, members


def _grounding(summary: dict[str, Any]) -> None:
    try:
        source = summary["source"]
        chunks = {(item["id"], item["checksum"]) for item in source["chunks"]}
        contexts = summary["contextDocuments"]
        support = summary["claimSupport"]
        context_chunks = {(item["chunkId"], item["checksum"]) for item in contexts}
        support_chunks = {(item["chunkId"], item["checksum"]) for item in support}
        valid = (
            summary["principal"] == "curator_demo"
            and summary["projectCount"] == 1
            and summary["legacySources"] == []
            and chunks
            and chunks == context_chunks == support_chunks
            and all(item["documentId"] == source["id"] for item in contexts)
            and summary["evaluation"] == {"passed": True, "unsupportedClaimCount": 0}
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("GROUNDING_JOIN") from exc
    if not valid:
        raise EvidenceError("GROUNDING_JOIN")


def verify_evidence(
    root: Path, *, expected_head: str, expected_run_id: str, forbidden: tuple[bytes, ...] = (), require_committed: bool = False
) -> dict[str, Any]:
    if not SHA.match(expected_head) or not RUN_ID.match(expected_run_id):
        raise EvidenceError("EXPECTED_IDENTITY")
    manifest = _json(root, "manifest.json")
    if manifest.get("schema") != "heartbeat2-evidence-v1" or manifest.get("headSha") != expected_head or manifest.get("runId") != expected_run_id:
        raise EvidenceError("STALE_EVIDENCE")
    if manifest.get("interceptionUsed") is not False or manifest.get("substitutionUsed") is not False or manifest.get("forbiddenMatchCount") != 0:
        raise EvidenceError("FABRICATED_EVIDENCE")
    report = _json(root, manifest.get("testReport"))
    if report.get("stats") != {"expected": 1, "unexpected": 0, "skipped": 0, "flaky": 0}:
        raise EvidenceError("PLAYWRIGHT_RESULT")
    ledger = _json(root, manifest.get("ledger"))
    try:
        valid_ledger = (
            [item["operation"] for item in ledger] == list(WRITES)
            and [item["sequence"] for item in ledger] == list(range(1, 9))
            and all(item["method"] == "POST" and item["origin"] == "http://127.0.0.1:3122" and 200 <= item["status"] < 300 for item in ledger)
            and len({item["requestKey"] for item in ledger}) == 8
            and all(item["requestKey"] == item["responseKey"] for item in ledger)
        )
    except (KeyError, TypeError) as exc:
        raise EvidenceError("WRITE_LEDGER") from exc
    if not valid_ledger:
        raise EvidenceError("WRITE_LEDGER")
    summary = _json(root, manifest.get("summary"))
    _grounding(summary)
    try:
        project = summary["projectId"]
        consent, render, media, other = summary["consent"], summary["render"], summary["media"], summary["otherDemo"]
        artifact = _path(root, render["artifact"])
        valid_media = (
            consent["projectId"] == render["projectId"] == project
            and consent["id"] == render["consentId"]
            and media["translated"] is media["subtitles"] is True
            and media["voiceMode"] == "mock"
            and render["mime"] == "application/json"
            and render["filename"] == artifact.name
            and render["sha256"] == sha256(artifact.read_bytes())
            and other == {"readStatus": 403, "actionsHidden": True}
        )
    except (KeyError, TypeError, OSError) as exc:
        raise EvidenceError("ARTIFACT_BINDING") from exc
    if not valid_media:
        raise EvidenceError("ARTIFACT_BINDING")
    graph = manifest.get("sourceGraph")
    if not isinstance(graph, list) or not graph:
        raise EvidenceError("SOURCE_GRAPH")
    if "scripts/ci/heartbeat2_evidence.py" not in {item.get("path") for item in graph}:
        raise EvidenceError("SOURCE_GRAPH")
    for item in graph:
        path = _path(Path.cwd(), item.get("path"))
        if sha256(path.read_bytes()) != item.get("sha256"):
            raise EvidenceError("SOURCE_GRAPH")
        if require_committed:
            committed = subprocess.run(["git", "show", f"{expected_head}:{item['path']}"], capture_output=True, check=False)
            if committed.returncode or committed.stdout != path.read_bytes():
                raise EvidenceError("SOURCE_GRAPH")
    files, members = _scan([path for path in root.rglob("*") if path.is_file()], forbidden)
    return {"schema": "heartbeat2-verification-v1", "runId": expected_run_id, "headSha": expected_head, "outcome": "PASS", "writeCount": 8, "fileCount": files, "memberCount": members}


def _main(argv: list[str]) -> int:
    class Parser(argparse.ArgumentParser):
        def error(self, message: str) -> NoReturn:
            raise EvidenceError("ARGUMENT_INVALID")
    parser = Parser(add_help=False)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--forbidden-file", action="append", default=[])
    args = parser.parse_args(argv)
    forbidden = tuple(Path(value).read_bytes() for value in args.forbidden_file)
    print(json.dumps(verify_evidence(Path(args.evidence), expected_head=args.head, expected_run_id=args.run_id, forbidden=forbidden, require_committed=True), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except EvidenceError as error:
        print(json.dumps({"schema": "heartbeat2-verification-v1", "outcome": "WITHHELD", "failureCode": error.code}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
