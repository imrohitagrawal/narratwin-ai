#!/usr/bin/env python3
"""Independent fail-closed verifier for Heartbeat 2 browser evidence."""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, NoReturn
from scripts.ci.heartbeat1_evidence import EvidenceError as PrivacyError, MAX_ARCHIVE_DEPTH, MAX_SCAN_BYTES, scan_browser_sources, scan_evidence
SHA, RUN_ID, ORIGIN = re.compile(r"^[0-9a-f]{40}$"), re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"), "http://127.0.0.1:3122"
SPEC, TEST_TITLE, MAX_ARCHIVE_MEMBERS = "heartbeat2-browser.spec.ts", "Heartbeat 2 local reviewer demo", 10_000
SOURCES = ("scripts/ci/heartbeat1_evidence.py", "scripts/ci/heartbeat2_evidence.py", "scripts/ci/heartbeat2-browser.sh", "frontend/playwright.heartbeat2.config.ts", "frontend/tests/heartbeat2-browser.spec.ts")
WRITES = (("project", "POST", 201), ("submit", "POST", 201), ("approve", "PATCH", 200), ("ingest", "POST", 201), ("walkthrough", "POST", 201), ("multilingual", "POST", 201), ("consent", "POST", 201), ("render", "POST", 201))
READS = (("languages", "GET", 200, "curator_demo"), ("summary", "GET", 200, "curator_demo"), ("other-summary", "GET", 403, "other_demo"))
DENIALS = (("other-walkthrough", "POST", 403), ("other-multilingual", "POST", 403), ("other-consent", "POST", 403), ("other-render", "POST", 403))
class EvidenceError(RuntimeError):
    pass
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def _local_only(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z]", "", str(key).lower())
            if normalized in {"allownetworkegress", "requiresapikey", "supportsrealvideo", "supportsclonedidentity", "realvideoproduced", "realaudioproduced", "providercallmade"} and item is not False:
                return False
            if ("url" in normalized or "endpoint" in normalized) and item:
                return False
            if not _local_only(item):
                return False
    elif isinstance(value, list):
        return all(_local_only(item) for item in value)
    elif isinstance(value, str) and value.lower().startswith(("http://", "https://")):
        return False
    return True
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
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("EVIDENCE_JSON") from exc
def _playwright(report: Any) -> None:
    if not isinstance(report, dict) or set(report) != {"config", "errors", "stats", "suites"} or report["errors"] != []:
        raise EvidenceError("PLAYWRIGHT_RESULT")
    config, stats = report["config"], report["stats"]
    if not isinstance(config, dict) or not {"configFile", "rootDir", "version", "projects"} <= set(config) or not str(config["configFile"]).endswith("playwright.heartbeat2.config.ts") or len(config["projects"]) != 1:
        raise EvidenceError("PLAYWRIGHT_RESULT")
    if set(stats) != {"startTime", "duration", "expected", "unexpected", "skipped", "flaky"} or any(stats.get(key) != expected for key, expected in {"expected": 1, "unexpected": 0, "skipped": 0, "flaky": 0}.items()):
        raise EvidenceError("PLAYWRIGHT_RESULT")
    tests: list[Any] = []
    identities: list[tuple[Any, Any]] = []
    pending = list(report.get("suites", []))
    while pending:
        suite = pending.pop()
        pending.extend(suite.get("suites", []))
        specs = suite.get("specs", [])
        if not {"column", "file", "line", "specs", "title"} <= set(suite) or any(not {"column", "file", "id", "line", "ok", "tags", "tests", "title"} <= set(spec) for spec in specs):
            raise EvidenceError("PLAYWRIGHT_RESULT")
        tests.extend(test for spec in specs for test in spec.get("tests", []))
        identities.extend((spec.get("file"), spec.get("title")) for spec in specs)
    if len(tests) != 1 or identities != [(SPEC, TEST_TITLE)]:
        raise EvidenceError("PLAYWRIGHT_RESULT")
    test = tests[0]
    results = test.get("results", [])
    required_test, required_result = {"annotations", "expectedStatus", "projectId", "projectName", "results", "status", "timeout"}, {"annotations", "attachments", "duration", "errors", "parallelIndex", "retry", "startTime", "status", "stderr", "stdout", "workerIndex"}
    if not required_test <= set(test) or test.get("expectedStatus") != "passed" or test.get("status") != "expected" or len(results) != 1 or not required_result <= set(results[0]) or results[0].get("status") != "passed" or results[0].get("retry") != 0 or results[0].get("errors"):
        raise EvidenceError("PLAYWRIGHT_RESULT")
    if [(x.get("name"), x.get("contentType"), Path(str(x.get("path"))).name) for x in results[0]["attachments"]] != [("trace", "application/zip", "trace.zip")]:
        raise EvidenceError("PLAYWRIGHT_RESULT")
def _traffic(traffic: Any, bundle: dict[str, Any]) -> None:
    try:
        requests, responses = traffic["requests"], traffic["responses"]
        if len(requests) != len(responses) or len({x["id"] for x in requests}) != len(requests) or len({x["requestId"] for x in responses}) != len(responses) or {x["id"] for x in requests} != {x["requestId"] for x in responses}:
            raise EvidenceError("TRAFFIC_LEDGER")
        status, (writes, reads, denials) = {x["requestId"]: x["status"] for x in responses}, (requests[:8], requests[8:11], requests[11:])
        if [(x["operation"], x["method"], status[x["id"]]) for x in writes] != list(WRITES):
            raise EvidenceError("WRITE_LEDGER")
        if [(x["operation"], x["method"], status[x["id"]], x["principal"]) for x in reads] != list(READS):
            raise EvidenceError("READ_LEDGER")
        if [(x["operation"], x["method"], status[x["id"]]) for x in denials] != list(DENIALS):
            raise EvidenceError("AUTHZ_LEDGER")
        if [x["sequence"] for x in writes] != list(range(1, 9)) or [x["sequence"] for x in reads] != list(range(1, 4)) or [x["sequence"] for x in denials] != list(range(1, 5)):
            raise EvidenceError("TRAFFIC_LEDGER")
        if any(x["origin"] != ORIGIN for x in requests):
            raise EvidenceError("TRAFFIC_LEDGER")
        project, source, run = bundle["projectId"], bundle["source"]["id"], bundle["walkthrough"]["runId"]
        paths = ("/api/v1/projects", f"/api/v1/projects/{project}/knowledge-documents", f"/api/v1/projects/{project}/knowledge-documents/{source}/approval", f"/api/v1/projects/{project}/ingestion-runs", f"/api/v1/projects/{project}/walkthrough-runs", f"/api/v1/projects/{project}/walkthrough-runs/{run}/multilingual-runs", f"/api/v1/projects/{project}/walkthrough-runs/{run}/avatar-consents", f"/api/v1/projects/{project}/walkthrough-runs/{run}/avatar-renders")
        summary = paths[3].replace("ingestion-runs", "source-curation-summary")
        if tuple(x["path"] for x in writes) != paths or tuple(x["path"] for x in reads) != ("/api/v1/languages", summary, summary) or tuple(x["path"] for x in denials) != paths[4:5] + paths[5:8]:
            raise EvidenceError("TRAFFIC_LEDGER")
        if any(x["principal"] != "curator_demo" or x["projectId"] != project for x in writes) or any(x["projectId"] not in ("", project) for x in reads) or any(x["principal"] != "other_demo" or x["projectId"] != project for x in denials):
            raise EvidenceError("OWNER_JOIN")
        payloads: dict[str, Any] = {}
        for request in requests:
            response = next(item for item in responses if item["requestId"] == request["id"])
            raw = base64.b64decode(response["bodyBase64"], validate=True)
            if response["bodySha256"] != sha256(raw):
                raise EvidenceError("TRAFFIC_LEDGER")
            payloads[request["operation"]] = json.loads(raw)
        source_payload = {"sourceId": source, "checksum": bundle["source"]["checksum"]}
        valid_payloads = (
            payloads["project"].get("projectId") == project
            and all(payloads[name].get(key) == value for name, state in (("submit", "PENDING_REVIEW"), ("approve", "APPROVED")) for key, value in (source_payload | {"decisionState": state}).items())
            and payloads["ingest"].get("status") == "COMPLETED" and payloads["ingest"].get("sourceIds") == [source]
            and payloads["walkthrough"] == bundle["walkthrough"] and payloads["multilingual"] == bundle["multilingual"]
            and payloads["consent"] == {"consentRecordId": bundle["consent"]["id"], "projectId": project, "sourceRunId": run, "sourceEvaluationId": bundle["walkthrough"]["evaluation"]["id"], "sourceEvaluationChecksum": bundle["walkthrough"]["evaluation"]["checksum"], "consentToUseSyntheticAvatar": True} and payloads["render"] == bundle["render"]
            and any(item.get("languageTag") == bundle["multilingual"]["targetLanguage"] and item.get("localDemoSupportStatus") == "SUPPORTED" for item in payloads["languages"].get("languages", []))
            and payloads["summary"].get("curatedSources") == [bundle["source"]] and payloads["summary"].get("legacySources") == []
            and all(payloads[name].get("error", {}).get("code") == "FORBIDDEN" for name in ("other-summary", *[x[0] for x in DENIALS]))
        )
        if not valid_payloads:
            raise EvidenceError("PRODUCT_JOIN")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EvidenceError("TRAFFIC_LEDGER") from exc
def _artifacts(root: Path, artifacts: Any, bundle: dict[str, Any]) -> None:
    if not isinstance(artifacts, dict) or set(artifacts) != {"translated", "subtitles", "voice", "preview", "renderManifest", "video"}:
        raise EvidenceError("ARTIFACT_BINDING")
    for name, item in artifacts.items():
        try:
            path = _path(root, item["path"])
            data = path.read_bytes()
            mime = "text/markdown" if name == "translated" else "application/x-subrip" if name == "subtitles" else "text/html" if name == "preview" else "application/json"
            valid = item["filename"] == path.name and item["sha256"] == sha256(data) and item["mime"] == mime
            if name in {"voice", "renderManifest", "video"}:
                parsed = json.loads(data)
                valid = valid and isinstance(parsed, dict) and _local_only(parsed)
                if name == "voice":
                    profile = parsed.get("mockAudioProfile", {})
                    valid = valid and parsed.get("provider") == "mock" and parsed.get("providerMode") == "LOCAL" and parsed.get("language") == bundle["multilingual"]["targetLanguage"] and profile.get("sampleRateHz") == 16000 and profile.get("channels") == 1
                else:
                    provider, source, media = parsed.get("providerConfig", {}), parsed.get("source", {}), parsed.get("multilingualBundle", {})
                    valid = valid and parsed.get("schema") == ("Stage7AvatarRenderManifest" if name == "renderManifest" else "Stage7VideoExportPlaceholder") and provider == {"provider": "mock", "providerMode": "LOCAL", "allowNetworkEgress": False, "requiresApiKey": False, "supportsRealVideo": False, "supportsClonedIdentity": False}
                    valid = valid and source == {"runId": bundle["walkthrough"]["runId"], "evaluationId": bundle["walkthrough"]["evaluation"]["id"], "evaluationChecksum": bundle["walkthrough"]["evaluation"]["checksum"], "contextRefIds": [x["contextRefId"] for x in bundle["walkthrough"]["contextRefs"]], "citationIndexes": [x["index"] for x in bundle["walkthrough"]["citations"]]}
                    valid = valid and media == {"sourceRunId": bundle["walkthrough"]["runId"], "multilingualRunId": bundle["multilingual"]["runId"], "contextRefIds": [x["contextRefId"] for x in bundle["walkthrough"]["contextRefs"]], "citationIndexes": [x["index"] for x in bundle["walkthrough"]["citations"]], "evaluationId": bundle["walkthrough"]["evaluation"]["id"], "evaluationChecksum": bundle["walkthrough"]["evaluation"]["checksum"]} and (name != "video" or parsed.get("realVideoProduced") is False)
            elif name == "translated":
                valid = valid and b"[1]" in data
            elif name == "subtitles":
                valid = valid and data.startswith(b"1\n00:00:00,000 -->") and b"[1]" in data
            else:
                valid = valid and b"<html" in data.lower() and b"synthetic" in data.lower()
        except (KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceError("ARTIFACT_BINDING") from exc
        if not valid:
            raise EvidenceError("ARTIFACT_BINDING")
def _joins(root: Path, bundle: dict[str, Any]) -> None:
    try:
        source, run, media, consent, render = (bundle[key] for key in ("source", "walkthrough", "multilingual", "consent", "render"))
        chunk_rows = [(x["id"], x["checksum"]) for x in source["chunks"]]
        chunks = set(chunk_rows)
        contexts = run["contextRefs"]
        context_chunks = {(x["chunkId"], x["chunkChecksum"]) for x in contexts}
        context_ids = [x["contextRefId"] for x in contexts]
        support_rows = [(x["claimId"], x["contextRefId"], x["documentId"], x["chunkId"], x["chunkChecksum"]) for x in run["claimSupports"]]
        citation_indexes = [x["index"] for x in run["citations"]]
        valid = (
            bundle["principal"] == "curator_demo" and bundle["projectCount"] == 1 and bundle["legacySources"] == [] and len(chunk_rows) == len(chunks) and len(contexts) == len(set(context_ids))
            and source["states"] == ["PENDING_REVIEW", "APPROVED", "SOURCE_INGESTED"] and source["status"] == "SOURCE_INGESTED" and source["retained"] is True and chunks and chunks == context_chunks
            and all(x["documentId"] == source["id"] and x["sourceChecksum"] == source["checksum"] for x in contexts)
            and len(support_rows) == len(set(support_rows)) and set(support_rows) == {(x["claimId"], x["contextRefId"], x["documentId"], x["chunkId"], x["chunkChecksum"]) for x in contexts}
            and [(x["claimId"], x["contextRefId"]) for x in run["citations"]] == [(x["claimId"], x["contextRefId"]) for x in contexts] and citation_indexes == list(range(1, len(contexts) + 1))
            and [(x["claimId"], x["contextRefId"], x["chunkId"]) for x in bundle["visibleCitations"]] == [(x["claimId"], x["contextRefId"], x["chunkId"]) for x in contexts]
            and run["projectId"] == media["projectId"] == consent["projectId"] == render["projectId"] == bundle["projectId"]
            and run["status"] == "COMPLETED" and run["evaluation"]["status"] == "PASSED" and run["evaluation"]["unsupportedClaimCount"] == 0
            and media["sourceRunId"] == render["sourceRunId"] == run["runId"] and media["supportedLanguage"] is True
            and consent["granted"] is True and consent["sourceRunId"] == run["runId"] and consent["evaluationId"] == run["evaluation"]["id"] and consent["evaluationChecksum"] == run["evaluation"]["checksum"]
            and media["evaluationId"] == render["evaluationId"] == run["evaluation"]["id"]
            and media["evaluationChecksum"] == render["evaluationChecksum"] == run["evaluation"]["checksum"]
            and media["contextRefIds"] == render["contextRefIds"] == context_ids and media["citationIndexes"] == render["citationIndexes"] == citation_indexes
            and media["translationMode"] == "mock" and media["voiceMode"] == "mock" and render["avatarMode"] == "local"
            and media["artifactChecksums"] == {name: bundle["artifacts"][name]["sha256"] for name in ("translated", "subtitles", "voice")}
            and render["artifactChecksums"] == {name: bundle["artifacts"][name]["sha256"] for name in ("preview", "renderManifest", "video")}
            and render["multilingualRunId"] == media["runId"] and render["consentId"] == consent["id"] and render["cloneEnabled"] is False
            and bundle["otherDemo"] == {"actionsHidden": True}
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("PRODUCT_JOIN") from exc
    if not valid:
        raise EvidenceError("PRODUCT_JOIN")
    _artifacts(root, bundle.get("artifacts"), bundle)
def _safe_archive(data: bytes, depth: int = 1, budget: dict[str, int] | None = None) -> None:
    budget = budget if budget is not None else {"bytes": 0, "members": 0}
    if depth > MAX_ARCHIVE_DEPTH:
        raise EvidenceError("FORBIDDEN_OR_ARCHIVE")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            budget["bytes"] += sum(item.file_size for item in members)
            budget["members"] += len(members)
            if budget["bytes"] > MAX_SCAN_BYTES or budget["members"] > MAX_ARCHIVE_MEMBERS:
                raise EvidenceError("FORBIDDEN_OR_ARCHIVE")
            for item in members:
                name = item.filename.replace("\\", "/")
                if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in name.split("/") or item.flag_bits & 1 or item.file_size > MAX_SCAN_BYTES:
                    raise EvidenceError("FORBIDDEN_OR_ARCHIVE")
                payload = archive.read(item)
                if zipfile.is_zipfile(io.BytesIO(payload)):
                    _safe_archive(payload, depth + 1, budget)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise EvidenceError("FORBIDDEN_OR_ARCHIVE") from exc
def _safe_archives(root: Path) -> None:
    budget = {"bytes": 0, "members": 0}
    for path in root.rglob("*"):
        if path.is_file():
            if path.stat().st_size > MAX_SCAN_BYTES:
                raise EvidenceError("FORBIDDEN_OR_ARCHIVE")
            if zipfile.is_zipfile(path):
                _safe_archive(path.read_bytes(), budget=budget)
def _trace(root: Path, manifest: dict[str, Any], traffic: dict[str, Any]) -> None:
    path = _path(root, manifest.get("trace"))
    if sha256(path.read_bytes()) != manifest.get("traceSha256"):
        raise EvidenceError("TRACE_BINDING")
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith("-trace.network")]
            if len(names) != 1:
                raise EvidenceError("TRACE_BINDING")
            prefix = names[0][:-len(".network")]
            if {prefix + ".trace", prefix + ".stacks"} - set(archive.namelist()):
                raise EvidenceError("TRACE_BINDING")
            contexts = [json.loads(line) for line in archive.read(prefix + ".trace").splitlines()]
            stacks = json.loads(archive.read(prefix + ".stacks"))
            if not contexts or contexts[0].get("type") != "context-options" or contexts[0].get("browserName") != "chromium" or contexts[0].get("options", {}).get("baseURL") != ORIGIN or contexts[0].get("options", {}).get("serviceWorkers") != "block" or not any(str(name).endswith("frontend/tests/" + SPEC) for name in stacks.get("files", [])):
                raise EvidenceError("TRACE_BINDING")
            records = [json.loads(line) for line in archive.read(names[0]).splitlines()]
            resource_bytes = {name: archive.read(name) for name in archive.namelist() if name.startswith("resources/")}
            before = {item.get("callId") for item in contexts if item.get("type") == "before" and item.get("pageId") and item.get("method")}
            after = {item.get("callId") for item in contexts if item.get("type") == "after"}
            if not before or not before <= after or not stacks.get("stacks"):
                raise EvidenceError("TRACE_BINDING")
        facts = []
        for record in records:
            snapshot = record.get("snapshot", {})
            request, response = snapshot.get("request", {}), snapshot.get("response", {})
            if record.get("type") == "resource-snapshot" and str(request.get("url", "")).startswith(f"{ORIGIN}/api/v1/"):
                headers = {str(x.get("name", "")).lower(): x.get("value") for x in request.get("headers", [])}
                resource = response.get("content", {}).get("_sha1")
                body = resource_bytes.get("resources/" + resource, b"") if isinstance(resource, str) else b""
                post_data = request.get("postData") or {}
                request_body = resource_bytes.get("resources/" + str(post_data.get("_sha1")), b"") if post_data.get("_sha1") else str(post_data.get("text", "")).encode()
                facts.append((request["url"], request["method"], response["status"], headers.get("x-local-user-id"), sha256(request_body), sha256(body)))
        statuses = {x["requestId"]: x["status"] for x in traffic["responses"]}
        bodies = {x["requestId"]: x["bodySha256"] for x in traffic["responses"]}
        expected = [(x["origin"] + x["path"], x["method"], statuses[x["id"]], x["principal"], x["bodySha256"], bodies[x["id"]]) for x in traffic["requests"]]
    except (KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise EvidenceError("TRACE_BINDING") from exc
    if facts != expected:
        raise EvidenceError("TRACE_BINDING")
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
    spec_text = (source_root / "frontend/tests/heartbeat2-browser.spec.ts").read_text(encoding="utf-8")
    semantic_patterns = (r"new\s+WeakMap<\s*Request", r"page\.on\([\"']request[\"']\s*,\s*\(request\)\s*=>\s*\{[^}]*requestIds\.set\(request", r"request\.postDataBuffer\(\)", r"page\.on\([\"']response[\"']\s*,\s*async\s*\(response\)\s*=>\s*\{[^}]*response\.request\(\)[^}]*responses\.push", r"await\s+response\.body\(\)")
    if not all(re.search(pattern, spec_text, re.DOTALL) for pattern in semantic_patterns):
        raise EvidenceError("BROWSER_SOURCE")
    arrow, positions = spec_text.find("=>", spec_text.find(TEST_TITLE)), [spec_text.find(f'page.on("{event}"') for event in ("request", "response")]
    block = spec_text.find("{", arrow)
    if arrow < 0 or block < 0 or any(position < 0 or spec_text[block:position].count("{") - spec_text[block:position].count("}") != 1 for position in positions):
        raise EvidenceError("BROWSER_SOURCE")
    if committed:
        try:
            scan_browser_sources(Path("frontend/tests/heartbeat2-browser.spec.ts"), head)
            scan_browser_sources(Path("frontend/playwright.heartbeat2.config.ts"), head)
        except PrivacyError as exc:
            raise EvidenceError("BROWSER_SOURCE") from exc
def verify_evidence(root: Path, *, expected_head: str, expected_run_id: str, forbidden: tuple[bytes, ...] = (), committed: bool = False, source_root: Path = Path.cwd()) -> dict[str, Any]:
    if not SHA.match(expected_head) or not RUN_ID.match(expected_run_id):
        raise EvidenceError("EXPECTED_IDENTITY")
    if committed and len(forbidden) != 2:
        raise EvidenceError("FORBIDDEN_INPUT")
    manifest = _json(root, "manifest.json")
    if manifest.get("schema") != "heartbeat2-evidence-v2" or manifest.get("headSha") != expected_head or manifest.get("runId") != expected_run_id:
        raise EvidenceError("STALE_EVIDENCE")
    _playwright(_json(root, manifest.get("testReport")))
    bundle = _json(root, manifest.get("bundle"))
    traffic = _json(root, manifest.get("traffic"))
    _traffic(traffic, bundle)
    _safe_archives(root)
    _trace(root, manifest, traffic)
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
        code = str(error) if isinstance(error, EvidenceError) else "INPUT_READ"
        print(json.dumps({"schema": "heartbeat2-verification-v2", "outcome": "WITHHELD", "failureCode": code}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
