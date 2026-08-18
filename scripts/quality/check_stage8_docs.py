#!/usr/bin/env python3
"""Executable Stage 8 quality gate for hardening and release readiness."""
from __future__ import annotations
# ruff: noqa: E302, E305, E401, E701, E702
import hashlib, json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT));import scripts.quality.issue427_architecture_reset as issue427_reset  # noqa: E402
import scripts.quality.issue431_authority_core as issue431_authority_core  # noqa: E402
from scripts.quality.branch_identity import current_branch  # noqa: E402
from scripts.quality.check_stage2_docs import check_retrieval_strategy_v1_parity  # noqa: E402
from scripts.quality import stage8_brace_expansion_unblock as brace_security  # noqa: E402
from scripts.quality import stage8_cache_pruning as cache_pruning  # noqa: E402
from scripts.quality.stage8_a23b import A23A_BRANCH, A23B_BRANCH, A23_ROUTES, check_a23b  # noqa: E402
from scripts.quality import stage8_node_security as node_security, stage8_cut1_routes as cut1_routes  # noqa: E402
STAGE8_BRANCH_PATTERN = re.compile(r"(?ai)^stage8-(?![a-z0-9-]*366(?:-|$))(?![a-z0-9-]*cut1)[a-z0-9-]+$")
ISSUE84_GUARDRAIL_BRANCH = "guardrail-main-merge-push-detection-84"
ISSUE287_STAGE8_DRIFT_BRANCH = "phase-1-closure-process-287-stage8-quality-gate-drift"
ISSUE289_SECURITY_UNBLOCK_BRANCH = "phase-1-closure-process-289-security-postcss-stage8-gate-unblock"
ISSUE324_PUBLICATION_BRANCH = "phase-1-closure-process-324-publication-boundary-v2"
ISSUE346_TRANSITION_BRANCH = "cut1-process-346-governance-transition"
ISSUE335_A2_1_BRANCH = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
ISSUE349_A2_2_BRANCH = "cut1-349-r0c-a2-2-machine-contract-parity"
CITATION_PARITY_BRANCH = "cut1-372-citation-index-parity-post380"
ISSUE434_BRANCH = "cut1-process-434-authority-evidence-trust"
_I434=json.loads((ROOT/"docs/governance/preflights/issue-434.json").read_text());R434=tuple(_I434["scope"]["required"])
ISSUE434_FILES=set(R434);H434=hashlib.sha256(json.dumps(sorted(R434),separators=(",",":")).encode()).hexdigest()
if H434 != "c3414778d2ee1c9326d1c81537d5dfe9f528b22f12ec98394e0ac4270f7cab90": ISSUE434_FILES=set()
else: ISSUE434_FILES |= {"scripts/quality/issue434_authority_evidence_reconstruction.py",
    "tests/unit/test_issue434_authority_evidence_reconstruction.py", "tests/unit/test_dependency_security_contract.py"}
B434="87b8504ca8d5e094394343aeaa4ef5bad46133d5";A434=R434[:9]+R434[13:14]
D434="3ccf1eb51a359c734a0a3da7e66df6e4ed79843c8d05273b823636b788fb8a28";I434_ARTIFACT_SHA=A434
G434=((450,{R434[0],R434[2]}),(850,{R434[1],R434[13],R434[18]}),(1350,set(R434[3:9])),
    (4300,set(R434[9:13])|set(ISSUE434_FILES)-set(R434)),(250,{R434[i] for i in (14,15,16,17,19,20,21)}))
LIMITS434=dict(zip((R434[9],R434[10],*sorted(ISSUE434_FILES-set(R434))),(1200,1300,900,30,700),strict=True))
CP_BASE, CP_LIMIT = "372fb78245b8890157ffe54f48b90e523017bc43", 1200
CITATION_PARITY_FILES = {"docs/governance/preflights/issue-372.json", "backend/app/stage4.py",
    "tests/acceptance/test_checkpoint3_output_correctness.py", "tests/unit/test_local_durability.py",
    "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md", "docs/ADR/0002-rag-storage.md"}
QUIET_PRESENCE_BRANCH = "cut1-358-quiet-presence-ui"
CUT1_REAL_MEDIA_TRANSITION_BRANCH = "cut1-366-real-media-governance-transition"
C1_BASE, C1_LIMIT = "a69903fea50c22e12926d7e13dffdc74e55dfb65", 900
C1_FILE_LIMITS = {"scripts/quality/check_stage8_docs.py":350,"tests/unit/test_stage8_quality_gate.py":300}
C1_DOCS=("docs/QUALITY_GATES.md","docs/STAGE_ISSUE_PLAN.md","docs/STATUS.md","docs/TRACEABILITY.md")
C1_BOUND=("docs/governance/preflights/issue-366.json",*C1_DOCS)
C1_DOC_SHA="aa97ad3ad67d65f79fa21f3c9c8d89ab91594ca70e1fa9ae01c495221b3c2fbe"
QUIET_PRESENCE_FILES = {"docs/governance/preflights/issue-358.json", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md", "docs/ADR/0048-quiet-presence-embedded-guide.md",
    "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py", "frontend/src/app/demo/page.tsx",
    "frontend/src/app/demo/page.module.css", "frontend/src/app/demo/page.test.tsx",
    "frontend/src/app/demo/guide-client.ts", "frontend/src/app/demo/guide-client.test.ts",
    "frontend/tests/quiet-presence.spec.ts", "frontend/public/demo/narratwin-synthetic-presenter.webp"}
CUT1_REAL_MEDIA_TRANSITION_FILES=set(C1_BOUND)|{"scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py"}
NULL_GIT_SHA = "0" * 40
def issue324_allowed_files() -> set[str]:
    return set(json.loads((ROOT/"docs/governance/preflights/issue-324.json").read_text())["scope"]["required"])
REQUIRED_FILES = [
    ".stage/current", ".github/pull_request_template.md", ".github/workflows/ci.yml", ".github/workflows/security.yml",
    "Makefile", "README.md", "backend/app/main.py", "backend/app/stage4.py", "backend/app/stage6.py",
    "backend/Dockerfile",
    "frontend/Dockerfile", "frontend/package.json", "frontend/package-lock.json", "frontend/src/app/page.test.tsx",
    "frontend/scripts/run-lighthouse.mjs", "perf/stage8_locustfile.py", "pyproject.toml", "uv.lock",
    "scripts/ci/dependency-security.sh", "scripts/ci/docker-image-scan.sh", "scripts/ci/frontend-lighthouse.sh",
    "scripts/ci/performance-smoke.sh", "scripts/quality/check_quality_stage.py", "scripts/quality/check_stage8_docs.py",
    "tests/api/test_stage4_slice_api.py", "tests/api/test_stage6_multilingual_api.py",
    "tests/api/test_stage8_hardening_api.py", "tests/unit/test_stage6_multilingual.py", "demo/stage8_seed_project.md",
    "docs/ADR/0006-stage8-release-hardening.md", "docs/API_CONTRACT.md", "docs/ARCHITECTURE.md",
    "docs/QUALITY_GATES.md", "docs/PROJECT_LEARNINGS_TRACKER.md", "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md", "docs/REPOSITORY_GUARDRAILS.md", "docs/RELEASE_CHECKLIST.md",
    "docs/RELEASE_READINESS_REVIEW.md", "docs/REVIEW_RIGOR_RETROSPECTIVE.md", "docs/RUNBOOK.md",
    "docs/SKILL_LOCK.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md", "docs/demo/CONTROLLED_LOCAL_DEMO.md",
]; STAGE8_ALLOWED_FILES = set(REQUIRED_FILES) | {"tests/api/test_health_api.py", "tests/unit/test_health_contract.py"}
PROCESS_BRANCH_ALLOWED_FILES = {issue427_reset.BRANCH: set(issue427_reset.PATHS),
    issue431_authority_core.BRANCH: set(issue431_authority_core.PATHS),
    ISSUE434_BRANCH: ISSUE434_FILES,
    node_security.ISSUE374_SECURITY_BRANCH: node_security.ISSUE374_SECURITY_FILES,
    ISSUE346_TRANSITION_BRANCH: {
        "docs/governance/preflights/issue-346.json", "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
    },
    ISSUE335_A2_1_BRANCH: {
        "docs/governance/preflights/issue-335.json", "tests/unit/test_retrieval_strategy_v1_contract.py",
        "backend/app/rag/models.py", "backend/app/stage4.py", "docs/STATUS.md", "frontend/src/app/page.tsx",
        "docs/API_CONTRACT.md", "tests/unit/test_local_durability.py", "docs/ADR/0002-rag-storage.md",
        "backend/app/storage/local_restore_drill.py", "tests/api/test_stage4_slice_api.py",
        "tests/api/test_stage6_multilingual_api.py", "docs/TRACEABILITY.md",
        "scripts/quality/check_stage8_docs.py", "docs/ADR/0047-publication-boundary.md",
        "tests/unit/test_stage8_quality_gate.py", "docs/EVAL_REPORT.md", "docs/STAGE_ISSUE_PLAN.md",
        "evals/smoke/stage5_grounded_script_dataset.json", "scripts/ci/heartbeat2_evidence.py",
        "tests/unit/test_phase1_closure_docs.py", "scripts/quality/phase1_closure/legacy.py"},
    ISSUE349_A2_2_BRANCH: {
        "docs/governance/preflights/issue-349.json", "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
        "scripts/quality/check_stage2_docs.py", "tests/unit/test_stage8_quality_gate.py", "docs/STATUS.md",
        "scripts/quality/check_stage8_docs.py", "docs/ADR/0002-rag-storage.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md"},
    ISSUE84_GUARDRAIL_BRANCH: {"docs/STATUS.md","scripts/guardrails_check.py",
        "scripts/quality/check_stage8_docs.py","tests/unit/test_guardrails_check.py",
        "tests/unit/test_stage8_quality_gate.py"},
    ISSUE287_STAGE8_DRIFT_BRANCH: {"docs/governance/preflights/issue-287.json","docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md","docs/STATUS.md","scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_stage8_docs.py","tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage8_quality_gate.py"},
    ISSUE289_SECURITY_UNBLOCK_BRANCH: {"docs/governance/preflights/issue-289.json","docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md","docs/STATUS.md","docs/ADR/0037-postcss-audit-remediation.md",
        "docs/TRACEABILITY.md","docs/THIRD_PARTY_NOTICES.md","frontend/package.json","frontend/package-lock.json",
        "scripts/quality/check_phase1_closure_docs.py","scripts/quality/check_stage8_docs.py",
        "tests/unit/test_phase1_closure_docs.py","tests/unit/test_stage8_quality_gate.py"},
    ISSUE324_PUBLICATION_BRANCH: issue324_allowed_files(), QUIET_PRESENCE_BRANCH: QUIET_PRESENCE_FILES,
    CUT1_REAL_MEDIA_TRANSITION_BRANCH: CUT1_REAL_MEDIA_TRANSITION_FILES,
    CITATION_PARITY_BRANCH: CITATION_PARITY_FILES,
}
PROCESS_BRANCH_ALLOWED_FILES.update(
    A23_ROUTES
    | cache_pruning.CACHE_PRUNING_ROUTES
    | {branch: paths for branch, paths in cut1_routes.ROUTES.items() if branch != cut1_routes.ISSUE386_BRANCH}
)
EFFECTIVE_STAGE8_ROUTES = PROCESS_BRANCH_ALLOWED_FILES | brace_security.BRACE_EXPANSION_ROUTES \
    | node_security.I389_ROUTES | cut1_routes.ROUTES
def run(a:list[str])->subprocess.CompletedProcess[str]:return subprocess.run(a,cwd=ROOT,text=True,capture_output=True)
def issue434_artifact_findings(a:dict[str,bytes])->list[str]:
    if set(a)!=set(A434) or any(not isinstance(v,bytes) for v in a.values()):return ["I434 set."]
    s=hashlib.sha256;j=json.dumps;h={p:s(a[p]).hexdigest() for p in A434}
    d=s(j(h,sort_keys=True,separators=(",",":")).encode()).hexdigest();return [] if d==D434 else ["I434 bytes."]
def check_issue434_verifier(f:list[str])->None:
    try:
        a={p:(ROOT/p).read_bytes() for p in A434};q=issue434_artifact_findings(a)
        if q:f.extend(q);return
        c=("from scripts.quality.check_stage8_docs import A434 as A;"
              "from scripts.quality.issue434_authority_evidence_reconstruction import validate_artifact_set as v;"
              "a={p:open(p,'rb').read() for p in A[1:2]+A[3:8]};"
              "z=open(A[7].replace('evidence-trust','core'),'rb').read();"
              "raise SystemExit(not v(artifacts=a,child_a_matrix_bytes=z).valid)")
        t=["uv","run","python"];r=run(t+["scripts/quality/issue434_authority_evidence_trust.py"]);s=run(t+["-c",c])
    except OSError:fail("I434 unavailable.",f);return
    f.extend(q+([] if not r.returncode and not s.returncode else ["I434 verify."]))
def read(path:str)->str: return (ROOT/path).read_text(encoding="utf-8")
def fail(message:str,failures:list[str])->None: failures.append(message)
def changed_files_for_stage_scope() -> list[str]:
    head_result = run(["git", "rev-parse", "HEAD"])
    if head_result.returncode != 0 or not head_result.stdout.strip():
        raise RuntimeError(head_result.stderr.strip() or "git rev-parse HEAD failed")
    head=head_result.stdout.strip(); event_name=os.environ.get("GITHUB_EVENT_NAME","").strip()
    expected_head = os.environ.get("GITHUB_HEAD_SHA", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if event_path and event_name in {"pull_request", "pull_request_review", "push"}:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            event_head = (payload["after"] if event_name == "push" else payload["pull_request"]["head"]["sha"])
        except (KeyError, OSError, TypeError, ValueError) as error:
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.") from error
        if not isinstance(event_head, str) or not event_head.strip():
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
        if expected_head and expected_head != event_head.strip():
            raise RuntimeError("GitHub exact head evidence contradicts GITHUB_HEAD_SHA.")
        expected_head = event_head.strip()
    if not expected_head and event_name in {"pull_request", "pull_request_review", "push"}:
        raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
    if expected_head:
        expected_result = run(["git", "rev-parse", f"{expected_head}^{{commit}}"])
        if expected_result.returncode != 0 or not expected_result.stdout.strip():
            raise RuntimeError(expected_result.stderr.strip() or "git rev-parse exact head failed")
        if expected_result.stdout.strip() != head:
            raise RuntimeError("Stage 8 scope checkout does not match the exact head.")
    preferred_base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    push_ref = os.environ.get("NARRATWIN_HEAD_REF", os.environ.get("GITHUB_REF_NAME", "")).strip()
    branch_base = (event_name == "push" and push_ref != "main") or not preferred_base or preferred_base == NULL_GIT_SHA
    base_candidates = ["origin/main", "main"] if branch_base else [preferred_base]
    merge_base=""; last_error=""
    for candidate in base_candidates:
        result = run(["git", "merge-base", candidate, head])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
        last_error = result.stderr.strip()
    if not merge_base:
        raise RuntimeError(last_error or "git merge-base failed for Stage 8 scope.")
    diff_flags = ["--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"]
    paths: list[str] = []
    for args in (
        ["git", "diff", *diff_flags, f"{merge_base}..{head}", "--"],
        ["git", "diff", "--cached", *diff_flags, head, "--"],
        ["git", "diff", *diff_flags, "--"],
    ):
        result = run(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
        paths.extend(parse_name_status_z(result.stdout))
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files failed")
    paths.extend(parse_paths_z(untracked.stdout)); return sorted(set(paths))
def citation_parity_charge() -> int:
    p=CP_BASE; b=run(["git","merge-base",p,"HEAD"])
    i=run(["git","diff","--cached","--numstat",p,"--"]); w=run(["git","diff","--numstat",p,"--"])
    ds=(i,w); bad=b.returncode or b.stdout.strip()!=p or any(d.returncode for d in ds)
    if bad:raise RuntimeError("Issue #372 base diff unavailable.")
    try:return max(sum(int(a)+int(x) for a,x,_ in map(lambda line:line.split("\t"),d.stdout.splitlines())) for d in ds)
    except ValueError as error: raise RuntimeError("Issue #372 malformed or binary numstat.") from error
def issue434_charges()->tuple[int,dict[str,int]]:
    b=run(["git","merge-base",B434,"HEAD"])
    rs=tuple(run(["git",*kind,"--numstat",B434,"--"]) for kind in (("diff","--cached"),("diff",)))
    if b.returncode or b.stdout.strip()!=B434 or any(r.returncode for r in rs):raise RuntimeError("I434 base.")
    lines=[result.stdout.splitlines() for result in rs]
    try:maps=[{p:int(a)+int(d) for a,d,p in map(lambda line:line.split("\t"),rows)} for rows in lines]
    except ValueError as e:raise RuntimeError("I434 num.") from e
    if any(len(m)!=len(r) for m,r in zip(maps,lines,strict=True)):raise RuntimeError("I434 dup.")
    c={p:max(row.get(p,0) for row in maps) for p in set().union(*maps)}
    return sum(c.values()),c
def issue434_budget_findings(n:int,c:dict[str,int])->list[str]:
    f=[] if n<=5600 else [f"I434 total {n}>5600."]
    f += [f"I434 partition>{n}." for n,ps in G434 if sum(c.get(p,0) for p in ps)>n]
    f += [f"I434 {p}>{n}." for p,n in LIMITS434.items() if c.get(p,0)>n]
    if sum(c.get(p,0) for p in R434[11:13])>200:f.append("I434 Stage8>200.")
    return f
def cut1_transition_charges() -> tuple[int, dict[str, int]]:
    return cut1_routes.cut1_transition_charges(run, C1_BASE, CUT1_REAL_MEDIA_TRANSITION_FILES)
def cut1_digest() -> str:
    digest=hashlib.sha256()
    for path in C1_BOUND:
        data=read(path).encode(); digest.update(f"{path}\0{len(data)}\0".encode()); digest.update(data)
    return digest.hexdigest()
def parse_paths_z(output: str) -> list[str]:
    if not output:return []
    if not output.endswith("\0"):raise RuntimeError("Malformed NUL-delimited Git path output.")
    paths = output[:-1].split("\0")
    if any(not path for path in paths): raise RuntimeError("Malformed empty Git path.")
    return paths
def parse_name_status_z(output: str) -> list[str]:
    fields = parse_paths_z(output); paths: list[str] = []; index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status in {"A","B","D","M","T","U"}:arity=1
        elif re.fullmatch(r"[RC]\d{1,3}",status) and int(status[1:])<=100:arity=2
        else:raise RuntimeError(f"Malformed Git name-status record: {status!r}")
        record_paths = fields[index : index + arity]
        if len(record_paths) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status!r}")
        paths.extend(record_paths);index+=arity
    return paths
def check_required_files(failures: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            fail(f"Missing required Stage 8 file: {path}", failures)
A23A_CONTRACT_MARKERS = {
    "docs/API_CONTRACT.md": (
        "stage7-source-evaluation-checksum-v2", "compact sorted-key UTF-8 JSON",
        "`scope`: normalized `tenantId` and `projectId`", "even when `selectedContext` is empty",
        "`topK=6`", '`minimumScoreThreshold="0.72"`', '`minimumScoreComparison="inclusive-gte"`',
        "`minimumRetrievedChunks=1`", "`minimumDistinctDocuments=1`",
        "`maximumChunksPerDocument=3`", "`tieBreakOrder` is exact", "`fallback`",
        "`computedEvidenceScoresOnly=true`", "`syntheticEligibilityScoresAllowed=false`",
        "`belowThresholdBackfill=false`", "`terminalRefusalBeforeGeneration=true`",
        "`EMPTY_CONTEXT`", "`LOW_RETRIEVAL_CONFIDENCE`", "`AMBIGUOUS_CONTEXT`",
        "`CROSS_PROJECT_CONTEXT`", "`UNSAFE_CONTEXT`", "`approvedAt`",
        "unique `contextRefId` and `chunkId`", "array position is its zero-based context ordinal",
        "every row's tenant/project IDs must equal `scope`", "finite IEEE-754 binary64",
        "shortest correctly rounded base-10", "expand any exponent to fixed notation", "canonical zero is `0`",
        "independently verified `snapshotChecksum`", "`sourceCitationIndexes`: positive integers",
        "sha256:a956a969f4f147fb020fa06b71722d8fcf76ad850f0c5f6be8d78bbbadb81377"),
    "docs/ADR/0004-avatar-provider-adapter.md": (
        "local/mock stale-or-mismatch integrity", "not cryptographic authenticity",
        "Legacy v1 rows cannot replay as v2"),
    "docs/QUALITY_GATES.md": ("A2.3a evaluation-lineage contract gate", "wrong-schema"),
    "docs/STAGE_ISSUE_PLAN.md": (A23A_BRANCH, "300 charged lines"),
    "docs/STATUS.md": ("Issue `#351`", "A2.3b remains blocked"),
}
def evaluation_lineage_checksum_v2_contract_valid(documents: dict[str, str]) -> bool:
    return all(marker in documents[path] for path, markers in A23A_CONTRACT_MARKERS.items() for marker in markers)
def check_evaluation_lineage_checksum_v2_contract(root: Path, failures: list[str]) -> None:
    documents = {path: (root / path).read_text(encoding="utf-8") for path in A23A_CONTRACT_MARKERS}
    if not evaluation_lineage_checksum_v2_contract_valid(documents):
        fail("A2.3a contract is incomplete or drifted.", failures)
def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "8":
        fail(".stage/current must contain 8 for Stage 8 quality.", failures)
    branch = current_branch()
    if not branch:
        fail("Stage 8 branch evidence is unavailable or inconsistent.", failures)
        return
    if (
        branch
        and branch != "main"
        and not STAGE8_BRANCH_PATTERN.match(branch)
        and branch not in EFFECTIVE_STAGE8_ROUTES
    ):
        fail(f"Stage 8 work must run on a stage8-* branch or main after merge; got {branch}.", failures)
def check_stage_scope(failures: list[str]) -> None:
    branch = current_branch()
    if not branch:
        fail("Stage 8 scope branch evidence is unavailable or inconsistent.", failures)
        return
    if branch not in EFFECTIVE_STAGE8_ROUTES and branch != "main" and not STAGE8_BRANCH_PATTERN.match(branch):
        fail(f"Stage 8 scope requires an exact reviewed branch; got {branch}.", failures)
        return
    allowed_files = EFFECTIVE_STAGE8_ROUTES.get(branch, STAGE8_ALLOWED_FILES)
    changed_files = set(changed_files_for_stage_scope())
    outside = changed_files - allowed_files
    if not outside: cut1_routes.check_exact_route(ROOT, run, branch, changed_files, failures)
    for path in sorted(outside):
        fail(f"Stage 8 changed file outside the allowlist: {path}", failures)
    if branch==ISSUE434_BRANCH and not outside:
        failures.extend(f"Issue #434 route is missing required path: {p}" for p in sorted(allowed_files-changed_files))
        total,charges=issue434_charges();failures.extend(issue434_budget_findings(total,charges))
    if branch == CITATION_PARITY_BRANCH and not outside:
        failures.extend(f"Issue #372 missing required path: {path}" for path in sorted(allowed_files-changed_files))
        charge=citation_parity_charge()
        if charge>CP_LIMIT: fail(f"Issue #372 charge {charge} exceeds {CP_LIMIT}.",failures)
    if branch == CUT1_REAL_MEDIA_TRANSITION_BRANCH and not outside:
        failures.extend(f"Issue #366 route is missing required path: {p}" for p in sorted(allowed_files-changed_files))
        total,charges=cut1_transition_charges()
        if total>C1_LIMIT: fail(f"Issue #366 charge {total} exceeds {C1_LIMIT}.",failures)
        failures.extend(f"Issue #366 charge for {p} exceeds {n}." for p,n in C1_FILE_LIMITS.items()
                        if charges.get(p,0)>n)
        if cut1_digest()!=C1_DOC_SHA:
            fail("Issue #366 governance document contract drifted.",failures)
def check_backend_and_tests(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage4_text = read("backend/app/stage4.py")
    tests = read("tests/api/test_stage8_hardening_api.py")
    stage4_api_tests = read("tests/api/test_stage4_slice_api.py")
    stage6_api_tests = read("tests/api/test_stage6_multilingual_api.py")
    stage6_unit_tests = read("tests/unit/test_stage6_multilingual.py")
    for marker in (
        'stage="8"', "MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE",
        "Stage8WriteRateLimiter", "RATE_LIMIT_EXCEEDED",
        "REQUEST_TOO_LARGE", "CONTENT_LENGTH_REQUIRED",
        "MAX_STAGE8_RATE_LIMIT_KEYS", "rate_limit_key_from_scope",
        "actual_bytes", "Stage8RequestSizeLimitMiddleware", "stage8_write_rate_limiter.reset",
    ):
        if marker not in main_text:
            fail(f"Stage 8 API hardening must include {marker}.", failures)
    if "MAX_API_REQUEST_BYTES" not in stage4_text:
        fail("Stage 8 must define a general API request size limit.", failures)
    for marker in (
        "health_reports_stage8_with_local_latency_budget", "write_rate_limit_rejects_excess_requests",
        "write_rate_limit_uses_client_ip_and_bounds_retained_keys", "json_request_size_limit_is_enforced",
        "json_request_size_limit_rejects_missing_content_length",
        "json_request_size_limit_rejects_underreported_content_length", "upload_mime_validation_rejects_octet_stream",
        "mocked_script_generation_path_stays_under_two_seconds", "latency_ms < 200", "latency_ms < 2_000",
    ):
        if marker not in tests:
            fail(f"Stage 8 tests must cover {marker}.", failures)
    for marker in ("SECRET_LIKE_CONTENT", "IDEMPOTENCY_CONFLICT", "stage6-secret-glossary"):
        if marker not in stage6_api_tests:
            fail(f"Stage 8 Stage 6 API tests must cover {marker}.", failures)
    for marker in ("replay_response", "conflict_response", "secret-upload"):
        if marker not in stage4_api_tests:
            fail(f"Stage 8 Stage 4 API tests must cover {marker}.", failures)
    for marker in ("test_tts_provider_manifest_rejects_unknown_schema_fields", "unexpectedTopLevel",
                   "unexpectedNested"):
        if marker not in stage6_unit_tests:
            fail(f"Stage 8 Stage 6 unit tests must cover {marker}.", failures)
    frontend_dockerfile = read("frontend/Dockerfile")
    for marker in ("COPY --from=node-source", "COPY --from=atomic-source", "/usr/lib/apk/db/installed",
                   "fs.appendFileSync(p", 'USER 65532:65532', 'ENTRYPOINT ["/usr/bin/node"]'):
        if marker not in frontend_dockerfile:
            fail(f"Stage 8 frontend runtime image must preserve {marker}.", failures)
def check_dependencies_and_scripts(failures: list[str]) -> None:
    pyproject = read("pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    package_lock = read("frontend/package-lock.json")
    makefile = read("Makefile")
    security_workflow = read(".github/workflows/security.yml")
    ci_workflow = read(".github/workflows/ci.yml")
    if "locust" not in pyproject:
        fail("Stage 8 must lock locust as a dev-only performance tool.", failures)
    if "lighthouse" not in package.get("devDependencies", {}):
        fail("Stage 8 must lock Lighthouse as a frontend dev dependency.", failures)
    if '"lighthouse"' not in package_lock:
        fail("frontend/package-lock.json must include Lighthouse.", failures)
    for marker in (
        "check_stage8_docs.py",
        "performance-smoke.sh",
        "frontend-lighthouse.sh",
        "dependency-security.sh",
        "docker-image-scan.sh",
    ):
        if marker not in makefile:
            fail(f"make stage8-quality must run {marker}.", failures)
    scripts = "\n".join(
        read(path)
        for path in (
            "scripts/ci/performance-smoke.sh",
            "scripts/ci/frontend-lighthouse.sh",
            "scripts/ci/docker-image-scan.sh",
            "frontend/scripts/run-lighthouse.mjs",
            "perf/stage8_locustfile.py",
        )
    )
    for marker in (
        "locust",
        "stage8_hardening_api",
        "--headless",
        "NARRATWIN_LOCUST_HEALTH_P95_MS",
        "lighthouse",
        "trivy image",
        "aquasec/trivy@sha256", "verify_frontend_runtime", 'process.version!=="v26.7.0"',
        '"65532:65532"', "extras.length", "require_frontend_inventory", "actual_inventory", "open(3)",
        'encoding:"buffer"', "readlinkSync", "s.uid", "s.gid", "CapEff", "--connect-timeout", "--max-time",
        "cleanup_frontend_runtime", "FRONTEND_BUILD_IMAGE", "--target deps", "NODE_OPTIONS", "config != expected",
        "largest-contentful-paint",
        "cumulative-layout-shift",
        "performance",
        "accessibility",
    ):
        if marker not in scripts:
            fail(f"Stage 8 scripts must include {marker}.", failures)
    for marker in (
        "security / docker build",
        "Docker image vulnerability scan",
        "docker-image-scan.sh",
        "upload-artifact",
    ):
        if marker not in security_workflow:
            fail(f"Stage 8 security workflow must include {marker}.", failures)
    for marker in (
        "stage8 / performance lighthouse",
        "performance-smoke.sh",
        "frontend-lighthouse.sh",
        "stage8-performance-lighthouse-reports",
    ):
        if marker not in ci_workflow:
            fail(f"Stage 8 CI workflow must include {marker}.", failures)
def check_docs(failures: list[str]) -> None:
    docs = {
        path: read(path)
        for path in (
            "docs/API_CONTRACT.md",
            ".github/pull_request_template.md",
            "docs/ADR/0006-stage8-release-hardening.md",
            "docs/ARCHITECTURE.md",
            "docs/QUALITY_GATES.md",
            "docs/PROJECT_LEARNINGS_TRACKER.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "docs/RECOMMENDED_REVIEW_ITEMS.md",
            "docs/REPOSITORY_GUARDRAILS.md",
            "docs/RELEASE_CHECKLIST.md",
            "docs/RELEASE_READINESS_REVIEW.md",
            "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
            "docs/RUNBOOK.md",
            "docs/SKILL_LOCK.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/THIRD_PARTY_NOTICES.md",
            "docs/TRACEABILITY.md",
            "docs/demo/CONTROLLED_LOCAL_DEMO.md",
            "demo/stage8_seed_project.md",
        )
    }
    combined = "\n".join(docs.values())
    for marker in (
        "Stage 8", "Performance, security hardening, release readiness", "health endpoint < 200 ms local",
        "script generation mocked path < 2 sec", "upload limit enforced", "no critical/high dependency vulnerabilities",
        "no critical/high container vulnerabilities","rate limiting","request size limits","Content-Length is required",
        "actual ASGI body", "SECRET_LIKE_CONTENT", "Voice provider artifacts must be JSON manifests",
        "top-level or nested fields fail", "upload MIME validation", "Lighthouse", "p95", "Trivy", "Docker Scout",
        "release checklist", "rollback", "runbook", "demo seed data", "Controlled Local Demo", "LRN-001", "LRN-002",
        "Review Rigor Retrospective", "Project Governance Learnings", "PROJECT_LEARNINGS_TRACKER.md",
        "REVIEW_RIGOR_RETROSPECTIVE.md", "invariant, exploit-matrix, and contract/gate review", "branch protection",
        "Required status checks", "stage8 / performance lighthouse", "RR-029", "RR-030", "RR-031", "RR-032",
        "RR-033", "RR-034", "RR-035", "multi-worker deployment blocked", "source-run based avatar export",
    ):
        if marker not in combined:
            fail(f"Stage 8 docs must include {marker}.", failures)
    if "| RR-029 |" not in docs["docs/RECOMMENDED_REVIEW_ITEMS.md"]:
        fail("Stage 8 must carry forward RR-029 through RR-035.", failures)
def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_retrieval_strategy_v1_parity(ROOT, failures)
    check_evaluation_lineage_checksum_v2_contract(ROOT, failures)
    if not failures:
        check_stage_marker_and_branch(failures)
        check_stage_scope(failures)
        check_a23b(ROOT, run, failures, current_branch() == A23B_BRANCH)
        brace_security.check_exact_route(ROOT, run, failures, current_branch() == brace_security.BRANCH)
        node_security.check(ROOT, run, current_branch(), changed_files_for_stage_scope(), failures)
        cache_pruning.check_exact_route(ROOT, run, failures, current_branch() == cache_pruning.BRANCH)
        issue427_reset.check(ROOT, failures, current_branch() == issue427_reset.BRANCH)
        failures.extend(issue431_authority_core.repository_findings(ROOT))
        if current_branch() in {ISSUE434_BRANCH,"main"}: check_issue434_verifier(failures)
        check_backend_and_tests(failures)
        check_dependencies_and_scripts(failures)
        check_docs(failures)
    if failures:
        print("Stage 8 quality gate failed:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("Stage 8 quality gate passed.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
