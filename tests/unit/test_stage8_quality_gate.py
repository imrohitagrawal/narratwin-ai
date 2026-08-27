# ruff: noqa: E302, E305, E401, E701, E702, E731
import hashlib,importlib.util,json,subprocess as sp,unittest.mock as um;from pathlib import Path;from typing import Any
import pytest; from scripts.guardrails_check import canonical_stage_issue
from scripts.quality import stage8_a23b as a23b, stage8_cut1_routes as cut1_routes, issue427_architecture_reset as i
from scripts.quality.check_stage8_docs import (CUT1_REAL_MEDIA_TRANSITION_BRANCH as CUT1_REAL_MEDIA_TRANSITION,
    CUT1_REAL_MEDIA_TRANSITION_FILES as CUT1_REAL_MEDIA_TRANSITION_SCOPE,
    CITATION_PARITY_BRANCH as CP, CITATION_PARITY_FILES as CP_SCOPE, ISSUE434_BRANCH as B, ISSUE434_FILES as F,
    QUIET_PRESENCE_BRANCH as QP, QUIET_PRESENCE_FILES as QP_SCOPE)
TRANSITION = "cut1-process-346-governance-transition"; A2_1 = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
A2_2 = "cut1-349-r0c-a2-2-machine-contract-parity"; C1 = CUT1_REAL_MEDIA_TRANSITION
SCOPES = {TRANSITION: set("docs/governance/preflights/issue-346.json scripts/quality/check_stage8_docs.py "
    "tests/unit/test_stage8_quality_gate.py docs/QUALITY_GATES.md docs/STAGE_ISSUE_PLAN.md docs/STATUS.md".split()),
    A2_1: set(("docs/governance/preflights/issue-335.json tests/unit/test_retrieval_strategy_v1_contract.py "
        "backend/app/rag/models.py backend/app/stage4.py docs/STATUS.md frontend/src/app/page.tsx docs/API_CONTRACT.md "
        "tests/unit/test_local_durability.py docs/ADR/0002-rag-storage.md backend/app/storage/local_restore_drill.py "
        "tests/api/test_stage4_slice_api.py tests/api/test_stage6_multilingual_api.py docs/TRACEABILITY.md "
        "scripts/quality/check_stage8_docs.py docs/ADR/0047-publication-boundary.md "
        "tests/unit/test_stage8_quality_gate.py docs/EVAL_REPORT.md docs/STAGE_ISSUE_PLAN.md "
        "evals/smoke/stage5_grounded_script_dataset.json scripts/ci/heartbeat2_evidence.py "
        "tests/unit/test_phase1_closure_docs.py scripts/quality/phase1_closure/legacy.py").split()),
    A2_2: set("""docs/governance/preflights/issue-349.json docs/STAGE2_ARCHITECTURE_CONTRACT.json docs/STATUS.md
        scripts/quality/check_stage2_docs.py tests/unit/test_stage8_quality_gate.py docs/STAGE_ISSUE_PLAN.md
        scripts/quality/check_stage8_docs.py docs/ADR/0002-rag-storage.md docs/QUALITY_GATES.md""".split()),
    QP:QP_SCOPE,CP:CP_SCOPE,C1:CUT1_REAL_MEDIA_TRANSITION_SCOPE,i.BRANCH:set(i.PATHS),B:F,**a23b.A23_ROUTES}
def load(relative: str, name: str) -> Any:
    spec=importlib.util.spec_from_file_location(name,Path(__file__).parents[2]/relative);assert spec and spec.loader
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
stage8=load("scripts/quality/check_stage8_docs.py","s8"); stage2=load("scripts/quality/check_stage2_docs.py","s2")
def git(r:Path,*a:str)->str:return sp.run(["git",*a],cwd=r,text=True,capture_output=True,check=True).stdout.strip()
def put(r:Path,p:str,v:str)->None:t=r/p;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(v)
def route(m:Any,b:str,c:list[str])->list[str]:
    s=stage8;digest=s.cut1_digest;f:list[Any]=[];m.setattr(s,"current_branch",lambda:b)
    m.setattr(s,"changed_files_for_stage_scope",lambda:c);b!=C1 or m.setattr(s,"cut1_digest",lambda:s.C1_DOC_SHA)
    s.check_stage_marker_and_branch(f);s.check_stage_scope(f);m.setattr(s,"cut1_digest",digest);return f
def test_cut1_routes_are_exact_stage8_and_not_preflight_owned(monkeypatch: Any, tmp_path: Path) -> None:
    for x,s in (SCOPES|(b:=stage8.backend_security).ISSUE436_ROUTES).items():
        m=monkeypatch;m.setattr(stage8,"cut1_transition_charges",lambda:(0,{}))
        m.setattr(stage8,"citation_parity_charge",lambda:1200);assert route(m,x,sorted(s))==[]
        assert route(m,x,[e:="forbidden/outside.txt"])==[f"Stage 8 changed file outside the allowlist: {e}"]
        if x==CP:m.setattr(stage8,"citation_parity_charge",lambda:1201);assert len(route(m,x,sorted(s)[1:]))==2
    for branch in (f"{TRANSITION}-retry", f"{TRANSITION}/child", "cut1-process-347-governance-transition",
                   "cut1-336-r0c-a2-1-stage4-rag-v1-lineage", f"{A2_2}-retry", "cut1-proces\u0455-346-transition",
                   A2_2.replace("-349-", "-350-"), A2_2[:-1]+"\u0443", f"{CP}-retry", f"{a23b.A23A_BRANCH}-retry",
                   *(f"stage8-{CUT1_REAL_MEDIA_TRANSITION.replace(a,b)}" for a,b in (("cut1","CUT1"),("cut1","Cut1"),
                   ("c","\u0441"),("1","l"),("on","\u043en")))): assert len(route(m,branch,[])) == 2
    for issue,branch in ((346,TRANSITION),(349,A2_2),(351,a23b.A23A_BRANCH),(353,a23b.A23B_BRANCH),(358,QP),
                         (366,CUT1_REAL_MEDIA_TRANSITION),(372,CP),(436,b.ISSUE436_BRANCH)):
        artifact = json.loads((Path(__file__).parents[2]/f"docs/governance/preflights/issue-{issue}.json").read_text())
        assert artifact["branch"]==branch and set(artifact["scope"]["required"])==SCOPES.get(branch,b.ISSUE436_FILES)
    m.setattr(Path,"read_text",lambda path,*a,**kw:(_ for _ in ()).throw(AssertionError()) if path.name in
        {f"issue-{n}.json" for n in (346,335,349,351,358,372)} else ORIGINAL_READ(path,*a,**kw))
    policy = load("scripts/quality/check_stage8_docs.py", "reloaded").PROCESS_BRANCH_ALLOWED_FILES
    assert {b:policy[b] for b in SCOPES}==SCOPES;r=cut1_routes;c=stage8.issue431_authority_core.BRANCH
    registered={getattr(r,f"ISSUE{i}_BRANCH") for i in (150,396,401,403,413,428)}|{c}
    assert {b for b in policy if b[:5] == "cut1-"} - set(SCOPES) == registered
    dispatcher:Any=load("scripts/quality/check_quality_stage.py","dispatcher");stage_file=tmp_path/"stage"
    status_file=tmp_path/"status";mode="| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure |\n"
    stage_file.write_text("8\n"); status_file.write_text(mode)
    calls: list[list[str]] = []; m.setattr(dispatcher, "run_recommended_review_item_check", lambda _stage: 0)
    m.setattr(dispatcher, "CURRENT_STAGE", stage_file); m.setattr(dispatcher, "STATUS_DOC", status_file)
    record:Any=lambda args,cwd:calls.__iadd__([args])and 0;m.setattr(dispatcher.subprocess,"call",record)
    for branch in SCOPES | b.ISSUE436_ROUTES:
        calls.clear(); m.setattr(dispatcher, "current_branch", lambda branch=branch: branch)
        assert (dispatcher.main(), calls) == (0, [["make", "stage8-quality"]])
        assert branch in (a23b.A23B_BRANCH,b.ISSUE436_BRANCH) or canonical_stage_issue(branch) is None
def test_issue366_contract_rejects_partial_scope_and_content_mutations(monkeypatch: Any) -> None:
    m=monkeypatch;z=m.setattr;raises=pytest.raises;full=sorted(CUT1_REAL_MEDIA_TRANSITION_SCOPE);d=sp.CompletedProcess
    s=stage8;fn=s.cut1_transition_charges;sc:Any=lambda v:m.setattr(s,"cut1_transition_charges",lambda:v);sc((0,{}))
    assert route(m,CUT1_REAL_MEDIA_TRANSITION,full[1:])==[f"Issue #366 route is missing required path: {full[0]}"]
    limits=[(901,{},"Issue #366 charge 901 exceeds 900."),*((n+1,{p:n+1},
        f"Issue #366 charge for {p} exceeds {n}.") for p,n in stage8.C1_FILE_LIMITS.items())]
    for total,files,want in limits: sc((total,files)); assert route(m,CUT1_REAL_MEDIA_TRANSITION,full)==[want]
    sc(fn);p=next(iter(s.C1_FILE_LIMITS));out=iter((d([],0,stdout=s.C1_BASE+"\n"),d([],0,stdout="351\t0\t"+p),
        d([],0,stdout="300\t0\tscripts/quality/check_stage8_docs.py\n100\t0\ttests/unit/test_stage8_quality_gate.py")))
    m.setattr(stage8,"run",lambda _:next(out)); assert fn()==(
        400,{"scripts/quality/check_stage8_docs.py":351,"tests/unit/test_stage8_quality_gate.py":100})
    for c,t in ((1,s.C1_BASE+"\n"),(0,"bad")):m.setattr(s,"run",lambda _,c=c,t=t:d([],c,t,""));raises(RuntimeError,fn)
    docs={p:(REPO/p).read_text()for p in stage8.C1_BOUND};originals=docs.copy();docs[".stage/current"]="8"
    m.setattr(stage8,"read",docs.__getitem__);baseline=stage8.cut1_digest()
    p=stage8.C1_BOUND[0];docs[p]+="drift";assert stage8.cut1_digest()!=baseline;docs[p]=originals[p]
    plan="docs/STAGE_ISSUE_PLAN.md"; quality="docs/QUALITY_GATES.md"; line,rest=docs[plan].split("\n",1)
    docs[plan]=rest;docs[quality]+="\n"+line;assert stage8.cut1_digest()!=baseline
    docs.update(originals);docs["docs/STATUS.md"]+="\nIssue #383 required status reconciliation.\n"
    assert stage8.cut1_digest()!=baseline;sc((0,{}));assert route(m,CUT1_REAL_MEDIA_TRANSITION,full)==[]
    p=s.R434;q=s.check_issue434_verifier;v={**s.LIMITS434,p[11]:100,p[12]:100};k="NARRATWIN_POLICY_ONLY"
    cases:Any=((5601,{}),(1201,{p[9]:1201}),(0,v),(201,{p[11]:101,p[12]:100}));m.delenv("GITHUB_EVENT_NAME",False)
    p=sp.run(["python3","-S",p[11]],capture_output=True);q0=p.returncode;o=p.stdout;z0=p.stderr;r=0;b=sorted(F)
    h=lambda x:hashlib.shake_256(repr(x).encode()).hexdigest(8);e="6d072fdd70c3a1bfbb6d3fc768e5f0e9";A=s.A434
    assert [h(x)in e for x in ((q0,o,z0),(q0,o+b"x",z0),(q0,o,z0+b"x"))]==[1,0,0];g=["git"];x=d(g,0);w=um.Mock()
    z(s,"issue434_charges",lambda:(0,{}));assert route(m,B,b[1:])and all(s.issue434_budget_findings(*x)for x in cases)
    a={x:(REPO/x).read_bytes()for x in A};f=s.issue434_artifact_findings;assert not f(a)and f(a|{A[0]:b"x"})and f({})
    z(s,"run",w);m.setenv(k,"1");q([]);m.delenv(k);z(s,f.__name__,um.Mock(side_effect=(["x"],[])));q([]);q([])
    assert hashlib.shake_256(str((w.mock_calls,r)).encode()).hexdigest(20)=="c0be82aafcc30a7904d3618d5f4ed1731eaaa3a8"
    m.undo();z(s,"run",w);w.side_effect=(d(g,0,s.B434+"\n"),d(g,1),x,x);raises(RuntimeError,s.issue434_charges)
def test_scope_collection_covers_exact_layers_and_forbidden_sources(monkeypatch: Any, tmp_path: Path) -> None:
    g:Any=lambda *a:git(tmp_path,*a); g("init","-b","main"); g("config","user.name","Scope Test")
    g("config","user.email","scope@example.invalid")
    for path, value in {"rename-source": "rename", "copy-source": "copy", "cached-source": "cached",
                        "unstaged-source": "unstaged", "cancelled": "original"}.items():
        put(tmp_path, f"forbidden/{path}.txt", value)
    g("add","."); g("commit","-m","base"); g("checkout","-b","feature")
    g("mv","forbidden/rename-source.txt","rename-destination.txt")
    put(tmp_path, "copy-destination.txt", "copy"); put(tmp_path, "committed.txt", "committed")
    put(tmp_path,"backend/app/main.py","forbidden first push");g("add",".");g("commit","-m","first push")
    first_head=g("rev-parse","HEAD");put(tmp_path,"docs/STATUS.md","allowed second push")
    g("add",".");g("commit","-m","second push");head=g("rev-parse","HEAD");g("checkout","main")
    put(tmp_path,"main-only.txt","main");g("add",".");g("commit","-m","main");base=g("rev-parse","HEAD")
    g("update-ref","refs/remotes/origin/main",base); g("checkout","feature")
    g("mv","forbidden/cached-source.txt","cached-destination.txt")
    (tmp_path / "forbidden/unstaged-source.txt").rename(tmp_path / "unstaged-destination.txt")
    put(tmp_path, "forbidden/cancelled.txt", "staged"); git(tmp_path, "add", "forbidden/cancelled.txt")
    put(tmp_path, "forbidden/cancelled.txt", "original"); put(tmp_path, "untracked\nnewline.txt", "new")
    calls:list[list[str]]=[];m=monkeypatch; collect=stage8.changed_files_for_stage_scope; raises=pytest.raises
    def record(a:list[str])->Any:calls.append(a);return sp.run(a,cwd=tmp_path,text=True,capture_output=True)
    m.setattr(stage8,"ROOT",tmp_path); m.setattr(stage8,"run",record); m.delenv("GITHUB_EVENT_PATH",raising=False)
    m.setenv("GITHUB_EVENT_NAME","push"); m.setenv("NARRATWIN_HEAD_REF","feature")
    m.setenv("GITHUB_BASE_SHA",first_head); m.setenv("GITHUB_HEAD_SHA",head); paths=set(collect())
    required=set(("forbidden/rename-source.txt|rename-destination.txt|forbidden/copy-source.txt|copy-destination.txt|"
        "forbidden/cached-source.txt|cached-destination.txt|forbidden/unstaged-source.txt|unstaged-destination.txt|"
        "forbidden/cancelled.txt|backend/app/main.py|committed.txt|docs/STATUS.md|untracked\nnewline.txt").split("|"))
    assert required<=paths and "main-only.txt" not in paths
    assert ["git", "merge-base", "origin/main", head] in calls and ["git", "merge-base", first_head, head] not in calls
    m.setattr(stage8,"current_branch",lambda:TRANSITION); failures:list[str]=[]
    stage8.check_stage_scope(failures); forbidden = required - SCOPES[TRANSITION]; assert all(
        f"Stage 8 changed file outside the allowlist: {path}" in failures for path in forbidden)
    event=tmp_path/"event.json"; event.write_text(json.dumps({"pull_request":{"head":{"sha":first_head}}}))
    m.setenv("GITHUB_EVENT_NAME","pull_request"); m.setenv("GITHUB_BASE_SHA",base)
    m.setenv("GITHUB_EVENT_PATH",str(event)); m.delenv("GITHUB_HEAD_SHA")
    assert "exact head" in str(raises(RuntimeError,collect).value); m.setenv("GITHUB_EVENT_NAME","pull_request_review")
    event.write_text(json.dumps({"pull_request":{"head":{"sha":head}}})); assert required<=set(collect())
    n=len(calls);m.setenv("GITHUB_HEAD_SHA",first_head);assert "contradicts" in str(raises(RuntimeError,collect).value)
    assert calls[n:]==[["git","rev-parse","HEAD"]]; m.delenv("GITHUB_HEAD_SHA")
    m.setenv("GITHUB_EVENT_NAME","push"); event.write_text(json.dumps({"after":head})); assert required<=set(collect())
    event.write_text("{"); assert "malformed or unavailable" in str(raises(RuntimeError,collect).value)
    m.delenv("GITHUB_EVENT_PATH"); assert "malformed or unavailable" in str(raises(RuntimeError,collect).value)
def test_scope_parser_flags_and_command_failures(monkeypatch: Any, tmp_path: Path) -> None:
    assert stage8.parse_name_status_z("R087\0old\0new\0C064\0source\0copy\0") == ["old", "new", "source", "copy"]
    for malformed in ("R100\0old\0","M\0path","M\0\0","Q\0path\0","R101\0old\0new\0"):
        pytest.raises(RuntimeError,stage8.parse_name_status_z,malformed)
    bad=("0"*39,"0"*41,"0"*39+"1","invalid-explicit-base"); cases=[(None,"0"*40,""),*((x,"base","") for x in
        ("rev-parse","merge-base","committed","cached","unstaged","untracked")),
        *(("explicit-base",base,"pull_request" if i%2 else "pull_request_review") for i,base in enumerate(bad))]
    event=tmp_path/"event.json"; event.write_text(json.dumps({"pull_request":{"head":{"sha":"head"}}}))
    for failed, base, event_name in cases:
        calls:list[list[str]]=[]
        def fake(args: list[str]) -> sp.CompletedProcess[str]:
            calls.append(args); layer=("rev-parse" if "rev-parse" in args else "merge-base" if "merge-base" in args
                else "untracked" if "ls-files" in args else "cached" if "--cached" in args else
                     "committed" if any(".." in arg for arg in args) else "unstaged")
            output="head\n" if layer=="rev-parse" else "base\n" if layer=="merge-base" else ""
            bad_call=layer==failed or (failed=="explicit-base" and base in args) or "0"*40 in args
            return sp.CompletedProcess(args,int(bad_call),output,"failed")
        monkeypatch.setattr(stage8,"run",fake); monkeypatch.setenv("GITHUB_BASE_SHA",base)
        monkeypatch.setenv("GITHUB_HEAD_SHA","head"); monkeypatch.setenv("GITHUB_EVENT_NAME",event_name)
        monkeypatch.setenv("GITHUB_EVENT_PATH",str(event))
        if failed:
            assert "failed" in str(pytest.raises(RuntimeError,stage8.changed_files_for_stage_scope).value)
            if failed=="explicit-base": assert [a[2] for a in calls if a[:2]==["git","merge-base"]]==[base]
        else:
            assert stage8.changed_files_for_stage_scope()==[];diffs=[a for a in calls if a[:2]==["git","diff"]]
            assert ["git","merge-base","origin/main","head"] in calls; assert len(diffs)==3
            flags={"--name-status","-z","--find-renames","--find-copies","--find-copies-harder"}
            for args in diffs: assert flags<=set(args)
def test_citation_charge_uses_worktree_and_fails_closed(monkeypatch: Any) -> None:
    s=stage8; d=sp.CompletedProcess; calls=[]
    out=iter(("600\t600\tx\n","600\t600\tx\n","600\t601\tx\n","600\t600\tx\n","-\t1\tx\n","1\t1\tx\n"))
    def fake(a:list[str])->Any: calls.append(a); return d(a,0,s.CP_BASE+"\n" if a[1]=="merge-base" else next(out),"")
    monkeypatch.setattr(s,"run",fake); fn=s.citation_parity_charge; assert (fn(),fn())==(1200,1201)
    pytest.raises(RuntimeError,fn); assert ["git","diff","--cached","--numstat",s.CP_BASE,"--"] in calls
    monkeypatch.setattr(s,"run",lambda args:d(args,1,"","failed")); pytest.raises(RuntimeError,fn)
def test_legacy_route_allowlists_and_behavior_remain_exact(monkeypatch: Any) -> None:
    s=stage8; source=s.PROCESS_BRANCH_ALLOWED_FILES; sha=stage2.hashlib.sha256
    cases=((s.ISSUE84_GUARDRAIL_BRANCH,"backend/app/stage4.py"),(s.ISSUE287_STAGE8_DRIFT_BRANCH,
        "frontend/package-lock.json"),(s.ISSUE289_SECURITY_UNBLOCK_BRANCH,"backend/app/main.py"))
    encoded = json.dumps({b: sorted(source[b]) for b, _ in cases}, sort_keys=True, separators=(",", ":")).encode()
    assert sha(encoded).hexdigest() == "95bbea6ae7294e5db03ed5c62caae3b74a7aff8c8f12aef5efe134b15a585117"
    for branch, rejected in cases:
        error=f"Stage 8 changed file outside the allowlist: {rejected}"
        for c,w in ((sorted(source[branch]),[]),([rejected],[error])): assert route(monkeypatch,branch,c)==w
def test_stage8_script_markers_match_mandatory_container_scanners() -> None:
    f:list[str]=[]; stage8.check_dependencies_and_scripts(f); assert stage8.node_security.I376_ROUTES
    assert not any(m in "\n".join(f) for m in ("docker scout cves","--only-severity critical,high"))
def test_unrouted_stage8_branch_is_rejected(monkeypatch:Any)->None:
    b="x";monkeypatch.setattr(stage8,"current_branch",lambda:b);f=[];stage8.check_stage_marker_and_branch(f)
    assert f==[f"Stage 8 work must run on a stage8-* branch or main after merge; got {b}."]
A22_SOURCE,A22_DECL,A22_RUNTIME,A22_SELECT,A22_REFUSE=("Stage 2 retrieval-v1 accepted sources must retain the canonica"
    "l oracle.|Stage 2 retrievalStrategy must equal the canonical v1 machine declaration.|Stage 4 retrieval-v1 runtime "
    "constants must equal the canonical oracle.|Stage 4 retrieval selection must preserve canonical v1 control flow.|"
    "Stage 4 retrieval refusal must be terminal before generation.").split("|")
ARCH = "docs/ARCHITECTURE.md"; ADR = "docs/ADR/0002-rag-storage.md"; ORIGINAL_READ = Path.read_text
DECL = "docs/STAGE2_ARCHITECTURE_CONTRACT.json"; MODELS = "backend/app/rag/models.py"
RETRIEVAL = "backend/app/rag/retrieval.py"; STAGE4 = "backend/app/stage4.py"; REPO = Path(__file__).parents[2]
def a22_check(m: Any, edits: dict[str, tuple[tuple[Any, ...], ...]]) -> list[str]:
    def read(path: Path, *args: Any, **kwargs: Any) -> str:
        value = ORIGINAL_READ(path, *args, **kwargs); relative = path.relative_to(REPO).as_posix()
        for old, new, *count in edits.get(relative, ()):
            n=count[0] if count else 1; assert value.count(old)==n; value=value.replace(old, new, n)
        return value
    m.setattr(Path,"read_text",read); f:list[str]=[]; stage2.check_retrieval_strategy_v1_parity(REPO,f); return f
def test_a22_oracle_rejects_independent_drift(monkeypatch: Any) -> None:
    model=(("STRATEGY_VERSION",'"stage4-rag-v1"','"v2"'),("TOP_K","6","7"),("MIN_SCORE","0.72","0.60"),
           ("MAX_CHUNKS_PER_DOCUMENT","3","6")); prefix = "query=retrieval_query,\n" + " " * 24
    low = 'status="REFUSED",\n' + " " * 28 + "failure_reason=self.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL,"
    cap="RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT"; changes: dict[str, tuple[tuple[Any, ...], ...]] = {
        MODELS: tuple((f"RETRIEVAL_{name} = {old}", f"RETRIEVAL_{name} = {new}") for name, old, new in model) +
                tuple(("RETRIEVAL_TOP_K = 6", "RETRIEVAL_TOP_K = 6\n" + suffix) for suffix in
                ("RETRIEVAL_TOP_K = 7", "RETRIEVAL_TOP_K += 1", "RETRIEVAL_TOP_K: int = 7")),
        RETRIEVAL: (("if score >= min_score:", "if score > min_score:"), ("if score >= min_score:", "if True:"),
            ("    ranked =", "    scored += [(min_score, '', 0, '', None)]\n    ranked ="),
            ("tenant_id=tenant_id", 'tenant_id="wrong"'), ("project_id=project_id", 'project_id="wrong"'),
            *tuple((i, "'wrong'") for i in "-item[0]|_reverse_sort_text(item[1])|item[2]|item[3]".split("|")),
            (f">= {cap}:", f"> {cap}:"), ("context.chunk.document_id", "context.chunk.chunk_id", 2),
            ("WORD_PATTERN = re.compile", "RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT = 6\nWORD_PATTERN = re.compile"),
            ("    if not left or not right", "    return 1.0\n    if not left or not right"),
            ("def retrieve_context(\n", "@staticmethod\ndef retrieve_context(\n"),
            ("def _cosine_similarity(", "retrieve_context = lambda **kwargs: []\n\ndef _cosine_similarity("),
            ("WORD_PATTERN = re.compile", "min = lambda *args: 1.0\nWORD_PATTERN = re.compile")),
        STAGE4: ((prefix + "top_k=RETRIEVAL_TOP_K,", prefix + "top_k=7,"),
            ('LOW_RETRIEVAL = "LOW_RETRIEVAL_CONFIDENCE"', 'LOW_RETRIEVAL = "LOW_CONFIDENCE"'),
            ("                    if not retrieved:\n", "                    if False and not retrieved:\n"),
            (low, low.replace("REFUSED", "FAILED")), ("import math", "import math\nRETRIEVAL_TOP_K = 7")),
        ARCH: (("`topK = 6`", "`topK = 7`"), ("`min_retrieved_chunks = 1`", "`min_retrieved_chunks = 0`"),
               ("`min_distinct_documents = 1`", "`min_distinct_documents = 0`"),
               ("## Provider Adapter Contract", "## Retrieval Strategy v1   \n\n## Provider Adapter Contract")),
        ADR: (("`topK = 6`", "`topK = 7`"),), DECL: (('    "maximumChunksPerDocument": 3,\n', ""),
               ('"maximumChunksPerDocument": 3', '"maximumChunksPerDocument": true'),
               ('"maximumChunksPerDocument": 3', '"maximumChunksPerDocument": 6'),
               ('"retrievalStrategy": {', '"retrievalStrategy": {},\n  "retrievalStrategy": {'),
               ('"maximumChunksPerDocument": 3,', '"maximumChunksPerDocument": 3,\n    "minimumChunks": 1,')),}
    expected=(A22_RUNTIME,A22_SELECT,A22_REFUSE,A22_SOURCE,A22_SOURCE,A22_DECL); assert not a22_check(monkeypatch,{})
    for (path, edits), error in zip(changes.items(), expected):
        for edit in edits: assert a22_check(monkeypatch, {path: (edit,)}) == [error]
    for field,(name,old,new) in zip(("topK","minimumScoreThreshold","maximumChunksPerDocument"),model[1:],strict=True):
        assert a22_check(monkeypatch, {DECL: ((f'"{field}": {old}', f'"{field}": {new}'),),
            MODELS: ((f"RETRIEVAL_{name} = {old}", f"RETRIEVAL_{name} = {new}"),)}) == [A22_DECL, A22_RUNTIME]
    old = " " * 20 + "if not retrieved:\n"; call = " " * 20 + "self.l" + "lm.generate_" + "script(audience=audience)\n"
    assert a22_check(monkeypatch, {STAGE4: ((old, call + old),)}) == [A22_REFUSE]
    calls: list[Path] = []; monkeypatch.setattr(stage8, "check_required_files", lambda f: f.append("earlier"))
    for module in (stage8, stage2):
        monkeypatch.setattr(module, "check_retrieval_strategy_v1_parity", lambda root, failures: calls.append(root))
        assert module.main() == 1 and calls == [module.ROOT]; calls.clear()
def test_a23a_contract_gate_rejects_every_frozen_marker_mutation(tmp_path: Path) -> None:
    assert a23b.a23a_markers_frozen(stage8.A23A_CONTRACT_MARKERS)
    documents={path:(REPO/path).read_text(encoding="utf-8") for path in stage8.A23A_CONTRACT_MARKERS}
    valid=stage8.evaluation_lineage_checksum_v2_contract_valid;assert valid(documents)
    for path,marker in ((p,m) for p,markers in stage8.A23A_CONTRACT_MARKERS.items() for m in markers):
            mutated={**documents,path:documents[path].replace(marker,"MUTATED")};assert not valid(mutated)
    api=documents["docs/API_CONTRACT.md"]; preimage=api.rsplit("```json\n",1)[1].split("\n```",1)[0]
    f=a23b.semantic_detector_self_test; assert "sha256:" + hashlib.sha256(preimage.encode()).hexdigest() == (
        "sha256:a956a969f4f147fb020fa06b71722d8fcf76ad850f0c5f6be8d78bbbadb81377") and f(tmp_path)
