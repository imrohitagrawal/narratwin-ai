#!/usr/bin/env python3
"""Independent fail-closed verifier for Heartbeat 2 browser evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn

from scripts.ci.heartbeat1_evidence import (
    EvidenceError as PrivacyError,
    scan_browser_sources,
    scan_evidence,
)

SHA = re.compile(r"^[0-9a-f]{40}$")
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
ORIGIN = "http://127.0.0.1:3122"
SOURCES = (
    "scripts/ci/heartbeat1_evidence.py",
    "scripts/ci/heartbeat2_evidence.py",
    "scripts/ci/heartbeat2-browser.sh",
    "frontend/playwright.heartbeat2.config.ts",
    "frontend/tests/heartbeat2-browser.spec.ts",
)
WRITES = (
    ("project", "POST", 201), ("submit", "POST", 201), ("approve", "PATCH", 200),
    ("ingest", "POST", 201), ("walkthrough", "POST", 201),
    ("multilingual", "POST", 201), ("consent", "POST", 201), ("render", "POST", 201),
)
READS = (("languages", 200, "curator_demo"), ("summary", 200, "curator_demo"), ("other-summary", 403, "other_demo"))


class EvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise EvidenceError("EVIDENCE_PATH")
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceError("EVIDENCE_PATH") from exc
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("EVIDENCE_PATH")
    return path


def _json(root: Path, value: Any) -> Any:
    try:
        return json.loads(_path(root, value).read_text(encoding="utf-8"))
    except EvidenceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("EVIDENCE_JSON") from exc


def _playwright(report: Any) -> None:
    stats = report.get("stats", {}) if isinstance(report, dict) else {}
    if any(stats.get(key) != expected for key, expected in {"expected": 1, "unexpected": 0, "skipped": 0, "flaky": 0}.items()):
        raise EvidenceError("PLAYWRIGHT_RESULT")
    tests: list[Any] = []
    pending = list(report.get("suites", []))
    while pending:
        suite = pending.pop()
        pending.extend(suite.get("suites", []))
        tests.extend(test for spec in suite.get("specs", []) for test in spec.get("tests", []))
    if len(tests) != 1:
        raise EvidenceError("PLAYWRIGHT_RESULT")
    test = tests[0]
    results = test.get("results", [])
    if test.get("expectedStatus") != "passed" or len(results) != 1 or results[0].get("status") != "passed" or results[0].get("retry") != 0 or results[0].get("errors"):
        raise EvidenceError("PLAYWRIGHT_RESULT")


def _traffic(traffic: Any, bundle: dict[str, Any]) -> None:
    try:
        writes, reads = traffic["writes"], traffic["reads"]
        if [(x["operation"], x["method"], x["status"]) for x in writes] != list(WRITES):
            raise EvidenceError("WRITE_LEDGER")
        if [(x["operation"], x["status"], x["principal"]) for x in reads] != list(READS):
            raise EvidenceError("READ_LEDGER")
        entries = writes + reads
        if [x["sequence"] for x in writes] != list(range(1, 9)) or [x["sequence"] for x in reads] != list(range(1, 4)):
            raise EvidenceError("TRAFFIC_LEDGER")
        if len({x["requestId"] for x in entries}) != 11 or any(x["requestId"] != x["responseRequestId"] or x["origin"] != ORIGIN for x in entries):
            raise EvidenceError("TRAFFIC_LEDGER")
        project, source, run = bundle["projectId"], bundle["source"]["id"], bundle["walkthrough"]["runId"]
        paths = (
            "/api/v1/projects", f"/api/v1/projects/{project}/knowledge-documents",
            f"/api/v1/projects/{project}/knowledge-documents/{source}/approval",
            f"/api/v1/projects/{project}/ingestion-runs", f"/api/v1/projects/{project}/walkthrough-runs",
            f"/api/v1/projects/{project}/walkthrough-runs/{run}/multilingual-runs",
            f"/api/v1/projects/{project}/walkthrough-runs/{run}/avatar-consents",
            f"/api/v1/projects/{project}/walkthrough-runs/{run}/avatar-renders",
        )
        if tuple(x["path"] for x in writes) != paths or tuple(x["path"] for x in reads) != ("/api/v1/languages", paths[3].replace("ingestion-runs", "source-curation-summary"), paths[3].replace("ingestion-runs", "source-curation-summary")):
            raise EvidenceError("TRAFFIC_LEDGER")
        if any(x["principal"] != "curator_demo" or x["projectId"] != project for x in writes) or any(x["projectId"] not in ("", project) for x in reads):
            raise EvidenceError("OWNER_JOIN")
    except EvidenceError:
        raise
    except (KeyError, TypeError) as exc:
        raise EvidenceError("TRAFFIC_LEDGER") from exc


def _artifacts(root: Path, artifacts: Any) -> None:
    required = {"translated", "subtitles", "voice", "preview", "renderManifest", "video"}
    if not isinstance(artifacts, dict) or set(artifacts) != required:
        raise EvidenceError("ARTIFACT_BINDING")
    for name, item in artifacts.items():
        try:
            path = _path(root, item["path"])
            valid = item["filename"] == path.name and item["sha256"] == sha256(path.read_bytes())
            valid = valid and item["mime"] == ("application/x-subrip" if name == "subtitles" else "text/html" if name == "preview" else "application/json")
        except (KeyError, TypeError, OSError) as exc:
            raise EvidenceError("ARTIFACT_BINDING") from exc
        if not valid:
            raise EvidenceError("ARTIFACT_BINDING")


def _joins(root: Path, bundle: dict[str, Any]) -> None:
    try:
        source, run, media, consent, render = (bundle[key] for key in ("source", "walkthrough", "multilingual", "consent", "render"))
        chunks = {(x["id"], x["checksum"]) for x in source["chunks"]}
        contexts = run["contextRefs"]
        context_chunks = {(x["chunkId"], x["chunkChecksum"]) for x in contexts}
        context_ids = [x["contextRefId"] for x in contexts]
        citation_indexes = [x["index"] for x in run["citations"]]
        valid = (
            bundle["principal"] == "curator_demo" and bundle["projectCount"] == 1 and bundle["legacySources"] == []
            and source["status"] == "SOURCE_INGESTED" and source["retained"] is True and chunks and chunks == context_chunks
            and all(x["documentId"] == source["id"] and x["sourceChecksum"] == source["checksum"] for x in contexts)
            and {x["contextRefId"] for x in run["claimSupports"]} == set(context_ids)
            and [x["contextRefId"] for x in run["citations"]] == context_ids and citation_indexes == list(range(1, len(contexts) + 1))
            and bundle["visibleCitationContextIds"] == context_ids
            and run["projectId"] == media["projectId"] == consent["projectId"] == render["projectId"] == bundle["projectId"]
            and run["status"] == "COMPLETED" and run["evaluation"]["status"] == "PASSED" and run["evaluation"]["unsupportedClaimCount"] == 0
            and media["sourceRunId"] == render["sourceRunId"] == run["runId"] and media["supportedLanguage"] is True
            and media["evaluationId"] == render["evaluationId"] == run["evaluation"]["id"]
            and media["evaluationChecksum"] == render["evaluationChecksum"] == run["evaluation"]["checksum"]
            and media["contextRefIds"] == render["contextRefIds"] == context_ids and media["citationIndexes"] == render["citationIndexes"] == citation_indexes
            and media["translationMode"] == "mock" and media["voiceMode"] == "mock" and render["avatarMode"] == "local"
            and media["artifactChecksums"] == {name: bundle["artifacts"][name]["sha256"] for name in ("translated", "subtitles", "voice")}
            and render["artifactChecksums"] == {name: bundle["artifacts"][name]["sha256"] for name in ("preview", "renderManifest", "video")}
            and render["multilingualRunId"] == media["runId"] and render["consentId"] == consent["id"] and render["cloneEnabled"] is False
            and bundle["otherDemo"] == {"readStatus": 403, "actionsHidden": True}
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("PRODUCT_JOIN") from exc
    if not valid:
        raise EvidenceError("PRODUCT_JOIN")
    _artifacts(root, bundle.get("artifacts"))


def _sources(manifest: dict[str, Any], head: str, *, committed: bool, source_root: Path) -> None:
    graph = manifest.get("sourceGraph")
    if not isinstance(graph, list) or {x.get("path") for x in graph} != set(SOURCES):
        raise EvidenceError("SOURCE_GRAPH")
    if committed and (subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() != head or subprocess.run(["git", "status", "--porcelain=v1"], capture_output=True, text=True).stdout):
        raise EvidenceError("SOURCE_GRAPH")
    for item in graph:
        path = _path(source_root, item.get("path"))
        if sha256(path.read_bytes()) != item.get("sha256"):
            raise EvidenceError("SOURCE_GRAPH")
        if committed:
            result = subprocess.run(["git", "show", f"{head}:{item['path']}"], capture_output=True)
            if result.returncode or result.stdout != path.read_bytes():
                raise EvidenceError("SOURCE_GRAPH")
    if committed:
        try:
            scan_browser_sources(Path("frontend/tests/heartbeat2-browser.spec.ts"), head)
            scan_browser_sources(Path("frontend/playwright.heartbeat2.config.ts"), head)
        except PrivacyError as exc:
            raise EvidenceError("BROWSER_SOURCE") from exc
        text = Path("frontend/tests/heartbeat2-browser.spec.ts").read_text(encoding="utf-8")
        if not all(token in text for token in ("WeakMap", "response.request()", "requestId", "responseRequestId")):
            raise EvidenceError("BROWSER_SOURCE")


def verify_evidence(root: Path, *, expected_head: str, expected_run_id: str, forbidden: tuple[bytes, ...] = (), committed: bool = False, source_root: Path = Path.cwd()) -> dict[str, Any]:
    if not SHA.match(expected_head) or not RUN_ID.match(expected_run_id):
        raise EvidenceError("EXPECTED_IDENTITY")
    manifest = _json(root, "manifest.json")
    if manifest.get("schema") != "heartbeat2-evidence-v2" or manifest.get("headSha") != expected_head or manifest.get("runId") != expected_run_id:
        raise EvidenceError("STALE_EVIDENCE")
    _playwright(_json(root, manifest.get("testReport")))
    bundle = _json(root, manifest.get("bundle"))
    _traffic(_json(root, manifest.get("traffic")), bundle)
    _joins(root, bundle)
    _sources(manifest, expected_head, committed=committed, source_root=source_root)
    try:
        stats = scan_evidence([root], controlled=forbidden[0] if forbidden else b"synthetic-never-present-h2", canary=forbidden[1] if len(forbidden) > 1 else b"synthetic-canary-never-present-h2")
    except PrivacyError as exc:
        raise EvidenceError("FORBIDDEN_OR_ARCHIVE") from exc
    return {"schema": "heartbeat2-verification-v2", "runId": expected_run_id, "headSha": expected_head, "outcome": "PASS", "writeCount": 8, "readCount": 3, "filesScanned": stats["fileCount"], "membersScanned": stats["memberCount"]}


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
    print(json.dumps(verify_evidence(Path(args.evidence), expected_head=args.head, expected_run_id=args.run_id, forbidden=forbidden, committed=True), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except (EvidenceError, OSError) as error:
        code = error.code if isinstance(error, EvidenceError) else "INPUT_READ"
        print(json.dumps({"schema": "heartbeat2-verification-v2", "outcome": "WITHHELD", "failureCode": code}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
