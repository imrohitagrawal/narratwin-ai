from __future__ import annotations
# ruff: noqa: E302, E305, E701, E702
import hashlib; import importlib.util; import json; import subprocess
from pathlib import Path; from types import ModuleType; from typing import Any, Mapping, Sequence
import pytest; from scripts.guardrails_check import canonical_stage_issue
TRANSITION = "cut1-process-346-governance-transition"; A2_1 = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
A2_2 = "cut1-349-r0c-a2-2-machine-contract-parity"
SCOPES = {TRANSITION: {"docs/governance/preflights/issue-346.json", "scripts/quality/check_stage8_docs.py",
                 "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
                 "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md"},
    A2_1: {"docs/governance/preflights/issue-335.json", "tests/unit/test_retrieval_strategy_v1_contract.py",
           "backend/app/rag/models.py", "backend/app/stage4.py", "docs/STATUS.md", "frontend/src/app/page.tsx",
           "docs/API_CONTRACT.md", "tests/unit/test_local_durability.py", "docs/ADR/0002-rag-storage.md",
           "backend/app/storage/local_restore_drill.py", "tests/api/test_stage4_slice_api.py",
           "tests/api/test_stage6_multilingual_api.py", "docs/TRACEABILITY.md",
           "scripts/quality/check_stage8_docs.py", "docs/ADR/0047-publication-boundary.md",
           "tests/unit/test_stage8_quality_gate.py", "docs/EVAL_REPORT.md", "docs/STAGE_ISSUE_PLAN.md",
           "evals/smoke/stage5_grounded_script_dataset.json", "scripts/ci/heartbeat2_evidence.py",
           "tests/unit/test_phase1_closure_docs.py", "scripts/quality/phase1_closure/legacy.py"},
    A2_2: {"docs/governance/preflights/issue-349.json", "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
           "scripts/quality/check_stage2_docs.py", "tests/unit/test_stage8_quality_gate.py", "docs/STATUS.md",
           "scripts/quality/check_stage8_docs.py", "docs/ADR/0002-rag-storage.md", "docs/QUALITY_GATES.md",
           "docs/STAGE_ISSUE_PLAN.md"},
}
def load_module(relative: str, name: str) -> ModuleType:
    module_path = Path(__file__).parents[2] / relative
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
stage8: Any = load_module("scripts/quality/check_stage8_docs.py", "stage8_quality_under_test")
stage2: Any = load_module("scripts/quality/check_stage2_docs.py", "stage2_quality_under_test")
def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
def put(repo: Path, path: str, value: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")
def test_cut1_routes_are_exact_stage8_and_not_preflight_owned(monkeypatch: Any, tmp_path: Path) -> None:
    for branch, scope in SCOPES.items():
        monkeypatch.setattr(stage8, "current_branch", lambda branch=branch: branch)
        monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda scope=scope: sorted(scope))
        failures: list[str] = []
        stage8.check_stage_marker_and_branch(failures); stage8.check_stage_scope(failures)
        assert failures == []
        extra = "backend/app/main.py" if branch == A2_1 else "backend/app/stage4.py"
        monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda extra=extra: [extra])
        failures = []; stage8.check_stage_scope(failures)
        assert failures == [f"Stage 8 changed file outside the allowlist: {extra}"]
    for branch in (f"{TRANSITION}-retry", f"{TRANSITION}/child", "cut1-process-347-governance-transition",
                   f"{A2_1}-copy", "cut1-336-r0c-a2-1-stage4-rag-v1-lineage", f"{A2_2}-retry",
                   f"{A2_2}/child", "cut1-350-r0c-a2-2-machine-contract-parity",
                   "cut1-349-r0c-a2-2-machine-contract-parit\u0443", "cut1-proces\u0455-346-transition"):
        monkeypatch.setattr(stage8, "current_branch", lambda branch=branch: branch)
        failures = []; stage8.check_stage_marker_and_branch(failures); stage8.check_stage_scope(failures)
        assert len(failures) == 2
    for issue, branch in ((346, TRANSITION), (349, A2_2)):
        artifact = json.loads((Path(__file__).parents[2]/f"docs/governance/preflights/issue-{issue}.json").read_text())
        assert artifact["branch"] == branch and set(artifact["scope"]["required"]) == SCOPES[branch]
    original_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda path, *a, **kw: (_ for _ in ()).throw(AssertionError())
                        if path.name in {"issue-346.json", "issue-335.json", "issue-349.json"}
                        else original_read(path, *a, **kw))
    policy = load_module("scripts/quality/check_stage8_docs.py", "reloaded").PROCESS_BRANCH_ALLOWED_FILES
    assert {branch: policy[branch] for branch in SCOPES} == SCOPES
    assert {branch for branch in policy if branch.startswith("cut1-")} == set(SCOPES)
    dispatcher: Any = load_module("scripts/quality/check_quality_stage.py", "dispatcher")
    stage_file, status_file = tmp_path / "stage", tmp_path / "status"
    mode = "| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure |\n"
    stage_file.write_text("8\n"); status_file.write_text(mode)
    calls: list[list[str]] = []
    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status_file)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda _stage: 0)
    def record(args: list[str], cwd: Path) -> int:
        calls.append(args); return 0
    monkeypatch.setattr(dispatcher.subprocess, "call", record)
    for branch in SCOPES:
        calls.clear(); monkeypatch.setattr(dispatcher, "current_branch", lambda branch=branch: branch)
        assert (dispatcher.main(), calls, canonical_stage_issue(branch)) == (0, [["make", "stage8-quality"]], None)
def test_scope_collection_covers_exact_layers_and_forbidden_sources(monkeypatch: Any, tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main"); git(tmp_path, "config", "user.name", "Scope Test")
    git(tmp_path, "config", "user.email", "scope@example.invalid")
    for path, value in {"rename-source": "rename", "copy-source": "copy", "cached-source": "cached",
                        "unstaged-source": "unstaged", "cancelled": "original"}.items():
        put(tmp_path, f"forbidden/{path}.txt", value)
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "base"); git(tmp_path, "checkout", "-b", "feature")
    git(tmp_path, "mv", "forbidden/rename-source.txt", "rename-destination.txt")
    put(tmp_path, "copy-destination.txt", "copy"); put(tmp_path, "committed.txt", "committed")
    put(tmp_path, "backend/app/main.py", "forbidden first push")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "first push")
    first_head = git(tmp_path, "rev-parse", "HEAD")
    put(tmp_path, "docs/STATUS.md", "allowed second push")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "second push"); head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "checkout", "main"); put(tmp_path, "main-only.txt", "main")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "main"); base = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "update-ref", "refs/remotes/origin/main", base)
    git(tmp_path, "checkout", "feature"); git(tmp_path, "mv", "forbidden/cached-source.txt", "cached-destination.txt")
    (tmp_path / "forbidden/unstaged-source.txt").rename(tmp_path / "unstaged-destination.txt")
    put(tmp_path, "forbidden/cancelled.txt", "staged"); git(tmp_path, "add", "forbidden/cancelled.txt")
    put(tmp_path, "forbidden/cancelled.txt", "original"); put(tmp_path, "untracked\nnewline.txt", "new")
    calls: list[list[str]] = []
    def record(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args); return subprocess.run(args, cwd=tmp_path, text=True, capture_output=True, check=False)
    monkeypatch.setattr(stage8, "ROOT", tmp_path); monkeypatch.setattr(stage8, "run", record)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push"); monkeypatch.setenv("NARRATWIN_HEAD_REF", "feature")
    monkeypatch.setenv("GITHUB_BASE_SHA", first_head)
    monkeypatch.setenv("GITHUB_HEAD_SHA", head); paths = set(stage8.changed_files_for_stage_scope())
    required = {"forbidden/rename-source.txt", "rename-destination.txt", "forbidden/copy-source.txt",
                "copy-destination.txt", "forbidden/cached-source.txt", "cached-destination.txt",
                "forbidden/unstaged-source.txt", "unstaged-destination.txt", "forbidden/cancelled.txt",
                "backend/app/main.py", "committed.txt", "docs/STATUS.md", "untracked\nnewline.txt"}
    assert required <= paths and "main-only.txt" not in paths
    assert ["git", "merge-base", "origin/main", head] in calls and ["git", "merge-base", first_head, head] not in calls
    monkeypatch.setattr(stage8, "current_branch", lambda: TRANSITION); failures: list[str] = []
    stage8.check_stage_scope(failures)
    forbidden = required - SCOPES[TRANSITION]; assert all(
        f"Stage 8 changed file outside the allowlist: {path}" in failures for path in forbidden)
    event = tmp_path / "event.json"; event.write_text(json.dumps({"pull_request": {"head": {"sha": first_head}}}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request"); monkeypatch.setenv("GITHUB_BASE_SHA", base)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event)); monkeypatch.delenv("GITHUB_HEAD_SHA")
    with pytest.raises(RuntimeError, match="exact head"): stage8.changed_files_for_stage_scope()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_review")
    event.write_text(json.dumps({"pull_request": {"head": {"sha": head}}}))
    assert required <= set(stage8.changed_files_for_stage_scope())
    before = len(calls); monkeypatch.setenv("GITHUB_HEAD_SHA", first_head)
    with pytest.raises(RuntimeError, match="contradicts"): stage8.changed_files_for_stage_scope()
    assert calls[before:] == [["git", "rev-parse", "HEAD"]]; monkeypatch.delenv("GITHUB_HEAD_SHA")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push"); event.write_text(json.dumps({"after": head}))
    assert required <= set(stage8.changed_files_for_stage_scope()); event.write_text("{")
    with pytest.raises(RuntimeError, match="malformed or unavailable"): stage8.changed_files_for_stage_scope()
    monkeypatch.delenv("GITHUB_EVENT_PATH")
    with pytest.raises(RuntimeError, match="malformed or unavailable"): stage8.changed_files_for_stage_scope()
def test_scope_parser_flags_and_command_failures(monkeypatch: Any, tmp_path: Path) -> None:
    assert stage8.parse_name_status_z("R087\0old\0new\0C064\0source\0copy\0") == ["old", "new", "source", "copy"]
    for malformed in ("R100\0old\0", "M\0path", "M\0\0", "Q\0path\0", "R101\0old\0new\0"):
        with pytest.raises(RuntimeError): stage8.parse_name_status_z(malformed)
    bad_bases = ("0" * 39, "0" * 41, "0" * 39 + "1", "invalid-explicit-base")
    layers = ("rev-parse", "merge-base", "committed", "cached", "unstaged", "untracked")
    cases = [(None, "0" * 40, ""), *((layer, "base", "") for layer in layers)]
    cases += [("explicit-base", base, ("pull_request" if index % 2 else "pull_request_review"))
              for index, base in enumerate(bad_bases)]
    event = tmp_path / "event.json"; event.write_text(json.dumps({"pull_request": {"head": {"sha": "head"}}}))
    for failed, base, event_name in cases:
        calls: list[list[str]] = []
        def fake(args: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            layer = ("rev-parse" if "rev-parse" in args else "merge-base" if "merge-base" in args else
                     "untracked" if "ls-files" in args else "cached" if "--cached" in args else
                     "committed" if any(".." in arg for arg in args) else "unstaged")
            output = "head\n" if layer == "rev-parse" else "base\n" if layer == "merge-base" else ""
            explicit_failure = failed == "explicit-base" and args == ["git", "merge-base", base, "head"]
            should_fail = layer == failed or explicit_failure or "0" * 40 in args
            return subprocess.CompletedProcess(args, int(should_fail), output, "failed")
        monkeypatch.setattr(stage8, "run", fake); monkeypatch.setenv("GITHUB_BASE_SHA", base)
        monkeypatch.setenv("GITHUB_HEAD_SHA", "head")
        monkeypatch.setenv("GITHUB_EVENT_NAME", event_name); monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
        if failed:
            with pytest.raises(RuntimeError, match="failed"): stage8.changed_files_for_stage_scope()
            if failed == "explicit-base":
                assert [args[2] for args in calls if args[:2] == ["git", "merge-base"]] == [base]
        else:
            assert stage8.changed_files_for_stage_scope() == []
            diffs = [args for args in calls if args[:2] == ["git", "diff"]]; assert len(diffs) == 3
            assert ["git", "merge-base", "origin/main", "head"] in calls
            for args in diffs:
                assert {"--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"} <= set(args)
def test_legacy_route_allowlists_remain_exact() -> None:
    source = stage8.PROCESS_BRANCH_ALLOWED_FILES
    branches = (stage8.ISSUE84_GUARDRAIL_BRANCH, stage8.ISSUE287_STAGE8_DRIFT_BRANCH,
                stage8.ISSUE289_SECURITY_UNBLOCK_BRANCH); policy = {b: sorted(source[b]) for b in branches}
    encoded = json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == "95bbea6ae7294e5db03ed5c62caae3b74a7aff8c8f12aef5efe134b15a585117"
def test_stage8_script_markers_match_mandatory_container_scanners() -> None:
    failures: list[str] = []; stage8.check_dependencies_and_scripts(failures)
    assert not [failure for failure in failures if "docker scout cves" in failure]
    assert not [failure for failure in failures if "--only-severity critical,high" in failure]
def test_non_stage8_non_process_branch_still_rejected(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: "feature/untracked-stage8-work")
    failures: list[str] = []; stage8.check_stage_marker_and_branch(failures)
    assert failures == ["Stage 8 work must run on a stage8-* branch or main after merge; "
                        "got feature/untracked-stage8-work."]
A22_SOURCE = "Stage 2 retrieval-v1 accepted sources must retain the canonical oracle."
A22_DECL = "Stage 2 retrievalStrategy must equal the canonical v1 machine declaration."
A22_RUNTIME = "Stage 4 retrieval-v1 runtime constants must equal the canonical oracle."
A22_SELECT = "Stage 4 retrieval selection must preserve canonical v1 control flow."
A22_REFUSE = "Stage 4 retrieval refusal must be terminal before generation."
ARCH = "docs/ARCHITECTURE.md"; ADR = "docs/ADR/0002-rag-storage.md"
DECL = "docs/STAGE2_ARCHITECTURE_CONTRACT.json"; MODELS = "backend/app/rag/models.py"
RETRIEVAL = "backend/app/rag/retrieval.py"; STAGE4 = "backend/app/stage4.py"; REPO = Path(__file__).parents[2]
def a22_check(monkeypatch: Any, edits: Mapping[str, Sequence[tuple[Any, ...]]]) -> list[str]:
    original = Path.read_text
    def read(path: Path, *args: Any, **kwargs: Any) -> str:
        value = original(path, *args, **kwargs); relative = path.relative_to(REPO).as_posix()
        for old, new, *count in edits.get(relative, ()):
            n=count[0] if count else 1; assert value.count(old)==n; value=value.replace(old, new, n)
        return value
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", read); failures: list[str] = []
        stage2.check_retrieval_strategy_v1_parity(REPO, failures); return failures
def test_a22_oracle_rejects_independent_drift(monkeypatch: Any) -> None:
    model=(("STRATEGY_VERSION",'"stage4-rag-v1"','"v2"'),("TOP_K","6","7"),("MIN_SCORE","0.72","0.60"),
           ("MAX_CHUNKS_PER_DOCUMENT","3","6")); prefix = "query=retrieval_query,\n" + " " * 24
    low = 'status="REFUSED",\n' + " " * 28 + "failure_reason=self.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL,"
    changes: dict[str, tuple[tuple[Any, ...], ...]] = {
        MODELS: tuple((f"RETRIEVAL_{name} = {old}", f"RETRIEVAL_{name} = {new}") for name, old, new in model) +
                (("RETRIEVAL_TOP_K = 6", "RETRIEVAL_TOP_K = 6\nRETRIEVAL_TOP_K = 7"),),
        RETRIEVAL: (("if score >= min_score:", "if score > min_score:"), ("if score >= min_score:", "if True:"),
            ("    ranked =", "    scored += [(min_score, '', 0, '', None)]\n    ranked ="),
            ("RetrievedContext(context_ref_id, chunk, score)", "RetrievedContext(context_ref_id, chunk, min_score)"),
            ("tenant_id=tenant_id", 'tenant_id="wrong"'), ("project_id=project_id", 'project_id="wrong"'),
            ("-item[0]", "'wrong'"), ("_reverse_sort_text(item[1])", "'wrong'"),
            ("item[2]", "'wrong'"), ("item[3]", "'wrong'"),
            (">= RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT:", "> RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT:"),
            ("context.chunk.document_id", "context.chunk.chunk_id", 2),
            ("return min(1.0, cosine + lexical_overlap * 0.25)", "return min(1.0, cosine)")),
        STAGE4: ((prefix + "top_k=RETRIEVAL_TOP_K,", prefix + "top_k=7,"),
            ('WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL = "LOW_RETRIEVAL_CONFIDENCE"',
             'WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL = "LOW_CONFIDENCE"'),
            ("                    if not retrieved:\n", "                    if False and not retrieved:\n"),
            (low, low.replace("REFUSED", "FAILED"))),
        ARCH: (("`topK = 6`", "`topK = 7`"), ("`min_retrieved_chunks = 1`", "`min_retrieved_chunks = 0`"),
               ("`min_distinct_documents = 1`", "`min_distinct_documents = 0`")),
        ADR: (("`topK = 6`", "`topK = 7`"),),
        DECL: (('    "maximumChunksPerDocument": 3,\n', ""),
               ('"maximumChunksPerDocument": 3', '"maximumChunksPerDocument": true'),
               ('"maximumChunksPerDocument": 3', '"maximumChunksPerDocument": 6'),
               ('"maximumChunksPerDocument": 3,', '"maximumChunksPerDocument": 3,\n    "minimumChunks": 1,')),
    }
    expected = (A22_RUNTIME, A22_SELECT, A22_REFUSE, A22_SOURCE, A22_SOURCE, A22_DECL)
    assert a22_check(monkeypatch, {}) == []
    for (path, edits), error in zip(changes.items(), expected):
        for edit in edits: assert a22_check(monkeypatch, {path: (edit,)}) == [error]
def test_a22_paired_weakening_oracle(monkeypatch: Any) -> None:
    pairs = (("topK", "TOP_K", "6", "7"), ("minimumScoreThreshold", "MIN_SCORE", "0.72", "0.6"),
             ("maximumChunksPerDocument", "MAX_CHUNKS_PER_DOCUMENT", "3", "6"))
    for field, name, old, new in pairs:
        edits = {DECL: ((f'"{field}": {old}', f'"{field}": {new}'),),
                 MODELS: ((f"RETRIEVAL_{name} = {old}", f"RETRIEVAL_{name} = {new}"),)}
        assert a22_check(monkeypatch, edits) == [A22_DECL, A22_RUNTIME]
def test_a22_refusal_and_unconditional_entrypoints(monkeypatch: Any) -> None:
    old = " " * 20 + "if not retrieved:\n"; call = " " * 20 + "self.l" + "lm.generate_" + "script(audience=audience)\n"
    assert a22_check(monkeypatch, {STAGE4: ((old, call + old),)}) == [A22_REFUSE]
    calls: list[Path] = []; monkeypatch.setattr(stage8, "check_required_files", lambda f: f.append("earlier"))
    monkeypatch.setattr(stage8, "check_retrieval_strategy_v1_parity", lambda root, failures: calls.append(root))
    assert stage8.main() == 1 and calls == [stage8.ROOT]
    calls.clear(); monkeypatch.setattr(stage2, "check_retrieval_strategy_v1_parity", lambda r, f: calls.append(r))
    assert stage2.main() == 1 and calls == [stage2.ROOT]
