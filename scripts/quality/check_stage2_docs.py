#!/usr/bin/env python3
"""Executable Stage 2 quality gate for NarraTwin AI."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STAGE2_BRANCH_PATTERN = re.compile(r"^stage2-")
RETRIEVAL_V1_SOURCE_ERROR, RETRIEVAL_V1_DECLARATION_ERROR, RETRIEVAL_V1_RUNTIME_ERROR, RETRIEVAL_V1_SELECTION_ERROR, RETRIEVAL_V1_REFUSAL_ERROR = ("Stage 2 retrieval-v1 accepted sources must retain the canonical oracle.", "Stage 2 retrievalStrategy must equal the canonical v1 machine declaration.", "Stage 4 retrieval-v1 runtime constants must equal the canonical oracle.", "Stage 4 retrieval selection must preserve canonical v1 control flow.", "Stage 4 retrieval refusal must be terminal before generation.")
RETRIEVAL_V1_DECLARATION = {"version": "stage4-rag-v1", "topK": 6, "minimumScoreThreshold": 0.72, "maximumChunksPerDocument": 3, "tieBreakOrder": ["score desc", "approved_at desc", "chunk_index asc", "chunk_id asc"], "fallback": "deterministic keyword overlap fallback only; no cross-project expansion", "refusalReasons": ["EMPTY_CONTEXT", "LOW_RETRIEVAL_CONFIDENCE", "AMBIGUOUS_CONTEXT", "CROSS_PROJECT_CONTEXT", "UNSAFE_CONTEXT"]}
RETRIEVAL_V1_SOURCE_SECTIONS = (
    ("docs/ARCHITECTURE.md", "## Retrieval Strategy v1", "216605678fdf9bb8ca41395f14a75aba27ee70c6662c02951dc97e79401d4c2c"), ("docs/ADR/0002-rag-storage.md", "## Retrieval Strategy v1 Decision", "dac842cb365229a868844565051601bb1d2a6eb8f19edfb02292c0177af3a8df"))

REQUIRED_FILES = [
    ".env.example",
    ".gitignore",
    ".stage/current",
    "Makefile",
    "docs/ADR/0001-system-architecture.md",
    "docs/ADR/0002-rag-storage.md",
    "docs/ADR/0003-llm-provider-routing.md",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/ADR/0005-observability-and-evals.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/STAGE2_REVIEW_PROMPT_PACK.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "scripts/quality/check_stage2_docs.py",
]

STAGE2_ALLOWED_FILES = {
    ".github/workflows/quality-gates.yml",
    ".env.example",
    ".gitignore",
    ".stage/current",
    "Makefile",
    "docs/ADR/0001-architecture-approach.md",
    "docs/ADR/0001-system-architecture.md",
    "docs/ADR/0002-provider-agnostic-adapters.md",
    "docs/ADR/0002-rag-storage.md",
    "docs/ADR/0003-free-mode-vs-premium-mode.md",
    "docs/ADR/0003-llm-provider-routing.md",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/ADR/0005-observability-and-evals.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/STAGE2_REVIEW_PROMPT_PACK.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "scripts/quality/check_stage2_docs.py",
}

PRODUCT_CODE_PATTERNS = [
    re.compile(r"^(app|apps|api|backend|frontend|server|src|web|packages|services|rag|providers|avatar)/"),
    re.compile(r"(^|/)(package\.json|pyproject\.toml|requirements.*\.txt|uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock)$"),
    re.compile(r"(^|/)(Dockerfile|docker-compose\.ya?ml|compose\.ya?ml)$"),
]

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-or-v1-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|credential)\b\s*[:=]\s*['\"]?([^'\"\s#]{8,})['\"]?"),
]

PRIVATE_KEY_CERT_SUFFIXES = {".pem", ".key", ".crt", ".cer", ".p12", ".pfx"}

PYTHON_GOVERNANCE_FILES = (
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/check_stage1_docs.py",
    "scripts/quality/check_stage2_docs.py",
)

STDLIB_IMPORT_ROOTS = set(getattr(sys, "stdlib_module_names", set())) | {"__future__"}

REQUIRED_PHRASES_BY_FILE = {
    "docs/ARCHITECTURE.md": [
        "Synthetic Local Principal",
        "Knowledge State Separation",
        "Stage 4 Resource Budgets",
        "Queue, Lease, Attempt, And Outbox Contract",
        "Retrieval Strategy v1",
        "Provider Adapter Contract",
        "Observability Event Contract",
    ],
    "docs/SECURITY_AND_PRIVACY.md": [
        "Authorization Model",
        "Secret screening is mandatory before non-local provider egress",
        "Rate And Cost Limit Values",
        "Approved Knowledge Controls",
    ],
    "docs/AI_SAFETY_AND_EVALUATION.md": [
        "Stage 4 Evaluation Policy",
        "unsupported_claim_count = 0",
        "claim-level context references",
        "Evaluation Fixture Contract",
        "UI Evaluation State Matrix",
    ],
    "docs/API_CONTRACT.md": [
        "/api/v1",
        "Idempotency Requirements",
        "Typed Response Schemas",
        "`ing_`",
        "`ctx_`",
        "Stage 4 Language Scope",
    ],
    "docs/DATA_MODEL.md": [
        "Synthetic Local Tenant And User",
        "IngestionRun",
        "ClaimSupport",
        "Required Indexes",
        "Retention And Deletion Decision",
    ],
    "docs/OBSERVABILITY_AND_COST.md": [
        "EventEnvelope",
        "p95",
        "queue_depth",
        "cost_budget_exceeded",
    ],
    "docs/PORTABILITY_STRATEGY.md": [
        "Provider Adapter Contract",
        "Export Tombstones",
        "Synthetic local tenant",
    ],
    "docs/THREAT_MODEL.md": [
        "Approved Knowledge Poisoning",
        "Authorization Boundary",
        "secret screening is mandatory",
    ],
    "docs/QUALITY_GATES.md": [
        "Stage 2 quality is executable",
        "Stage 2 validates",
        "Recommended Review Items",
    ],
    "docs/RECOMMENDED_REVIEW_ITEMS.md": [
        "Recommended Review Items",
        "RR-001",
        "Required stage",
    ],
    "docs/STAGE_ISSUE_PLAN.md": [
        "Stage 2 Architecture And Safety Branch Scope",
        "docs/API_CONTRACT.md",
    ],
    "docs/STATUS.md": [
        "Stage 2 quality is executable locally",
        "Stage 2 remediation",
    ],
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json": [
        "\"canonicalIssue\": \"#2\"",
        "\"canonicalPullRequest\": \"#27\"",
    ],
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md": [
        "Stage 2 Human Review Checklist",
        "Product implementation allowed: no",
        "Cross-model second-opinion findings",
    ],
    "docs/STAGE2_REVIEW_PROMPT_PACK.md": [
        "Stage 2 Review Prompt Pack",
        "Ruthless Architecture Reviewer",
        "Cross-Model Second Opinion",
    ],
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def repo_files() -> list[str]:
    tracked = run(["git", "ls-files"])
    if tracked.returncode != 0:
        raise RuntimeError(tracked.stderr.strip() or "git ls-files failed")
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files --others failed")
    return sorted(
        {
            line.strip()
            for output in (tracked.stdout, untracked.stdout)
            for line in output.splitlines()
            if line.strip()
        }
    )


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = None
    attempted: list[str] = []
    for candidate in [item for item in base_candidates if item]:
        attempted.append(candidate)
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result
            break
    if merge_base is None:
        raise RuntimeError(f"git merge-base failed for Stage 2 scope. Tried: {', '.join(attempted)}")

    base = merge_base.stdout.strip()
    committed = run(["git", "diff", "--name-only", f"{base}..HEAD"])
    working = run(["git", "diff", "--name-only", "HEAD"])
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    for result, label in ((committed, "committed diff"), (working, "working diff"), (untracked, "untracked files")):
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"git {label} failed")
    return sorted(
        {
            line.strip()
            for output in (committed.stdout, working.stdout, untracked.stdout)
            for line in output.splitlines()
            if line.strip()
        }
    )


def check_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"Missing required Stage 2 file: {rel}", failures)


def check_current_stage(failures: list[str]) -> None:
    current = ROOT / ".stage" / "current"
    if not current.exists():
        fail("Missing .stage/current.", failures)
        return
    value = current.read_text(encoding="utf-8").strip()
    if value != "2":
        fail(f".stage/current must contain 2 during Stage 2, found: {value!r}", failures)


def check_branch_name(failures: list[str]) -> None:
    result = run(["git", "branch", "--show-current"])
    if result.returncode != 0:
        fail(result.stderr.strip() or "Could not determine current branch.", failures)
        return
    branch = result.stdout.strip() or os.environ.get("GITHUB_HEAD_REF", "").strip()
    if branch == "main":
        return
    if not STAGE2_BRANCH_PATTERN.search(branch):
        fail(f"Stage 2 branch must match `stage2-*` before merge or be `main` after merge, found: {branch}", failures)


def check_stage2_scope(failures: list[str]) -> None:
    try:
        changed_files = changed_files_for_stage_scope()
    except RuntimeError as exc:
        fail(str(exc), failures)
        return
    for rel in changed_files:
        if rel not in STAGE2_ALLOWED_FILES:
            fail(f"Stage 2 branch changed file outside the allowed scope: {rel}", failures)


def check_no_product_code(files: list[str], failures: list[str]) -> None:
    allowed_scripts = {
        "scripts/guardrails_check.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_recommended_review_items.py",
        "scripts/quality/check_stage0_docs.py",
        "scripts/quality/check_stage1_docs.py",
        "scripts/quality/check_stage2_docs.py",
        "scripts/quality/stage_not_implemented.py",
    }
    for rel in files:
        if rel in allowed_scripts:
            continue
        if any(pattern.search(rel) for pattern in PRODUCT_CODE_PATTERNS):
            fail(f"Product/runtime code or manifest is not allowed in Stage 2: {rel}", failures)


def check_required_phrases(failures: list[str]) -> None:
    for rel, phrases in REQUIRED_PHRASES_BY_FILE.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} must include Stage 2 remediation phrase: {phrase}", failures)


def check_adr_canon(failures: list[str]) -> None:
    legacy_adrs = {
        "docs/ADR/0001-architecture-approach.md": "Superseded by `docs/ADR/0001-system-architecture.md`",
        "docs/ADR/0002-provider-agnostic-adapters.md": "Superseded by `docs/ADR/0003-llm-provider-routing.md`",
        "docs/ADR/0003-free-mode-vs-premium-mode.md": "Superseded by `docs/ADR/0001-system-architecture.md`",
    }
    for rel, phrase in legacy_adrs.items():
        path = ROOT / rel
        if path.exists() and phrase not in path.read_text(encoding="utf-8"):
            fail(f"{rel} must mark the legacy ADR as superseded: {phrase}", failures)


def check_mock_local_defaults(failures: list[str]) -> None:
    text = read(".env.example") if (ROOT / ".env.example").exists() else ""
    for default in (
        "LLM_PROVIDER=mock",
        "EMBEDDING_PROVIDER=mock",
        "EVALUATION_PROVIDER=mock",
        "TRANSLATION_PROVIDER=mock",
        "AVATAR_PROVIDER=mock",
        "TTS_PROVIDER=mock",
        "STT_PROVIDER=mock",
        "SUBTITLE_PROVIDER=mock",
        "VIDEO_RENDERER=local",
        "STORAGE_PROVIDER=local",
        "VECTOR_STORE=disabled",
    ):
        if default not in text:
            fail(f".env.example must include free/local test default: {default}", failures)


def load_stage2_contract(failures: list[str]) -> dict[str, Any]:
    path = ROOT / "docs/STAGE2_ARCHITECTURE_CONTRACT.json"
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"docs/STAGE2_ARCHITECTURE_CONTRACT.json must be valid JSON: {exc}", failures)
        return {}
    if not isinstance(contract, dict):
        fail("docs/STAGE2_ARCHITECTURE_CONTRACT.json must contain a JSON object.", failures)
        return {}
    return contract


def _retrieval_section(text: str, heading: str) -> str:
    starts = [match.start() for match in re.finditer(rf"(?m)^ {{0,3}}{re.escape(heading)}(?:[ \t]+#+[ \t]*|[ \t]*)$", text)]
    if len(starts) != 1 or text.count(heading.removeprefix("## ")) != 1:
        return ""
    start = starts[0]
    ends = [index for marker in ("\n## ", "\n### ") if (index := text.find(marker, start + len(heading))) >= 0]
    return text[start:min(ends)] if ends else text[start:]


def _bound_names(tree: ast.AST) -> list[str]:
    names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))]
    names += [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    names += [node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)]
    names += [(node.asname or node.name.split(".")[0]) for node in ast.walk(tree) if isinstance(node, ast.alias)]
    names += [node.name for node in ast.walk(tree) if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name]
    return names


def _imports_once(tree: ast.Module, module: str | None, names: tuple[str, ...]) -> bool:
    imported = [alias.name for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names
                if alias.asname is None and ((module is None and isinstance(node, ast.Import)) or
                (isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == module))]
    bindings = _bound_names(tree)
    return "*" not in bindings and all(imported.count(name) == bindings.count(name) == 1 for name in names)


def _unique_function(tree: ast.Module | ast.ClassDef, name: str) -> ast.FunctionDef | None:
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    return matches[0] if len(matches) == 1 and not matches[0].decorator_list and _bound_names(tree).count(name) == 1 else None


def _call_name(node: ast.Call) -> str:
    return node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""


def check_retrieval_strategy_v1_parity(root: Path, failures: list[str]) -> None:
    """Compare accepted sources, machine declaration, and active runtime without imports."""
    source_bad = False
    for relative, heading, expected_digest in RETRIEVAL_V1_SOURCE_SECTIONS:
        try:
            section = _retrieval_section((root / relative).read_text(encoding="utf-8"), heading)
        except OSError:
            section = ""
        source_bad |= hashlib.sha256(section.encode()).hexdigest() != expected_digest
    if source_bad:
        fail(RETRIEVAL_V1_SOURCE_ERROR, failures)

    try:
        declaration = json.loads((root / "docs/STAGE2_ARCHITECTURE_CONTRACT.json").read_text(encoding="utf-8"),
            object_pairs_hook=lambda pairs: dict(pairs) if len(dict(pairs)) == len(pairs) else (_ for _ in ()).throw(ValueError("duplicate JSON key")))
        declaration_ok = isinstance(declaration, dict) and declaration.get("retrievalStrategy") == RETRIEVAL_V1_DECLARATION
    except (OSError, ValueError):
        declaration_ok = False
    if not declaration_ok:
        fail(RETRIEVAL_V1_DECLARATION_ERROR, failures)

    trees: dict[str, ast.Module | None] = {}
    for relative in ("backend/app/rag/models.py", "backend/app/rag/retrieval.py", "backend/app/stage4.py"):
        try:
            trees[relative] = ast.parse((root / relative).read_text(encoding="utf-8"), filename=relative)
        except (OSError, SyntaxError):
            trees[relative] = None

    expected_constants = {"RETRIEVAL_STRATEGY_VERSION": "stage4-rag-v1", "RETRIEVAL_TOP_K": 6, "RETRIEVAL_MIN_SCORE": 0.72, "RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT": 3}
    models_tree = trees["backend/app/rag/models.py"]
    runtime_ok = bool(models_tree and all(
        _bound_names(models_tree).count(name) == 1 and
        [ast.unparse(node) for node in models_tree.body if isinstance(node, ast.Assign) and
         any(isinstance(target, ast.Name) and target.id == name for target in node.targets)] == [f"{name} = {expected!r}"]
        for name, expected in expected_constants.items()))
    if not runtime_ok:
        fail(RETRIEVAL_V1_RUNTIME_ERROR, failures)

    retrieval_tree = trees["backend/app/rag/retrieval.py"]
    functions = ("retrieve_context", "_cosine_similarity", "_retrieval_score", "_reverse_sort_text")
    retrieve, cosine, score, reverse = tuple(_unique_function(retrieval_tree, name) for name in functions) if retrieval_tree else (None,) * 4
    retrieval_bindings = _bound_names(retrieval_tree) if retrieval_tree else []
    retrieval_imports_ok = bool(retrieval_tree and _imports_once(retrieval_tree, None, ("hashlib", "heapq", "re"))
        and _imports_once(retrieval_tree, "collections", ("defaultdict",)) and _imports_once(
            retrieval_tree, "backend.app.rag.models", ("RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT", "RetrievedContext")))
    patterns = [node for node in retrieval_tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "WORD_PATTERN" for target in node.targets)] if retrieval_tree else []
    expected_retrieve = [
        "query_embedding = embedder.embed(query)",
        "scored: list[tuple[float, str, int, str, RetrievedContext]] = []",
        "per_document_counts: defaultdict[str, int] = defaultdict(int)",
        "for chunk in store.chunks_for_project(tenant_id=tenant_id, project_id=project_id):\n    score = _retrieval_score(query=query, query_embedding=query_embedding, text=chunk.text, embedding=chunk.embedding)\n    context_ref_id = 'ctx_' + hashlib.sha256(f'{tenant_id}:{project_id}:{chunk.chunk_id}:{query}'.encode('utf-8')).hexdigest()[:16]\n    if score >= min_score:\n        scored.append((score, chunk.approved_at, chunk.chunk_index, chunk.chunk_id, RetrievedContext(context_ref_id, chunk, score)))",
        "ranked = heapq.nsmallest(len(scored), scored, key=lambda item: (-item[0], _reverse_sort_text(item[1]), item[2], item[3]))",
        "selected: list[RetrievedContext] = []",
        "for _score, _approved_at, _chunk_index, _chunk_id, context in ranked:\n    if per_document_counts[context.chunk.document_id] >= RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT:\n        continue\n    selected.append(context)\n    per_document_counts[context.chunk.document_id] += 1\n    if len(selected) == top_k:\n        break",
        "return selected",
    ]
    expected_score = ["cosine = _cosine_similarity(query_embedding, embedding)", "query_terms = set(WORD_PATTERN.findall(query.lower()))", "text_terms = set(WORD_PATTERN.findall(text.lower()))", "if not query_terms:\n    return cosine", "lexical_overlap = len(query_terms & text_terms) / len(query_terms)", "return min(1.0, cosine + lexical_overlap * 0.25)"]
    expected_cosine = ["if not left or not right or len(left) != len(right):\n    return 0.0",
                       "return sum((left_value * right_value for left_value, right_value in zip(left, right, strict=True)))"]
    semantic_builtins = ("int", "len", "min", "ord", "set", "sum", "tuple", "zip")
    selection_ok = bool(retrieve and cosine and score and reverse and retrieval_imports_ok
        and not any(name in retrieval_bindings for name in semantic_builtins)
        and retrieval_bindings.count("WORD_PATTERN") == len(patterns) == 1
        and ast.unparse(patterns[0].value) == "re.compile('[a-z0-9]+')"
        and [ast.unparse(node) for node in retrieve.body] == expected_retrieve
        and [arg.arg for arg in retrieve.args.kwonlyargs] == ["store", "embedder", "tenant_id", "project_id", "query", "top_k", "min_score"]
        and [ast.unparse(node) for node in cosine.body] == expected_cosine
        and [ast.unparse(node) for node in score.body] == expected_score
        and [ast.unparse(node) for node in reverse.body] == ["return tuple((-ord(char) for char in value))"])
    if not selection_ok:
        fail(RETRIEVAL_V1_SELECTION_ERROR, failures)

    stage4_tree = trees["backend/app/stage4.py"]
    classes = ([node for node in stage4_tree.body if isinstance(node, ast.ClassDef)
                and node.name == "Stage4Service"] if stage4_tree else [])
    stage4_bindings_ok = bool(
        stage4_tree and _imports_once(stage4_tree, "backend.app.rag.models", tuple(expected_constants))
        and _imports_once(stage4_tree, "backend.app.rag.retrieval", ("retrieve_context",)))
    class_ok = (len(classes) == 1 and not classes[0].decorator_list
                and _bound_names(stage4_tree).count("Stage4Service") == 1) if stage4_tree else False
    method = _unique_function(classes[0], "_generate_walkthrough_once") if class_ok else None
    class_constants = ([node for node in classes[0].body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name)
                                and target.id == "WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL"
                                for target in node.targets)] if len(classes) == 1 else [])
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)] if method else []
    retrieve_calls = [node for node in calls if _call_name(node) == "retrieve_context"]
    generators = [node for node in calls if _call_name(node) == "generate_script"]
    refusal_ifs = [node for node in ast.walk(method) if isinstance(node, ast.If)
                   and ast.unparse(node.test) == "not retrieved"] if method else []
    refusal_ok = (stage4_bindings_ok and len(class_constants) == len(retrieve_calls)
                  == len(generators) == len(refusal_ifs) == 1
                  and _bound_names(classes[0]).count("WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL") == 1)
    if refusal_ok:
        retrieval_keywords = {item.arg: ast.unparse(item.value) for item in retrieve_calls[0].keywords}
        refusal = refusal_ifs[0]
        body_calls = [node for statement in refusal.body for node in ast.walk(statement)
                      if isinstance(node, ast.Call)]
        else_calls = [node for statement in refusal.orelse for node in ast.walk(statement)
                      if isinstance(node, ast.Call)]
        builders = [node for node in body_calls if _call_name(node) == "_build_walkthrough_run"]
        builder_keywords = ({item.arg: ast.unparse(item.value) for item in builders[0].keywords}
                            if len(builders) == 1 else {})
        refusal_ok = (
            ast.unparse(class_constants[0].value) == "'LOW_RETRIEVAL_CONFIDENCE'"
            and retrieval_keywords == {"store": "self.rag_store", "embedder": "self.embedder",
                                       "tenant_id": "principal.tenant_id", "project_id": "project_id",
                                       "query": "retrieval_query", "top_k": "RETRIEVAL_TOP_K",
                                       "min_score": "RETRIEVAL_MIN_SCORE"}
            and not any(_call_name(node) == "generate_script" for node in body_calls)
            and generators[0] in else_calls and builder_keywords.get("status") == "'REFUSED'"
            and builder_keywords.get("failure_reason")
            == "self.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL"
        )
    if not refusal_ok:
        fail(RETRIEVAL_V1_REFUSAL_ERROR, failures)


def check_contract_invariants(contract: dict[str, Any], failures: list[str]) -> None:
    required_keys = [
        "version",
        "stage",
        "canonicalIssue",
        "canonicalPullRequest",
        "providerDefaults",
        "documentStatus",
        "approvalStatus",
        "ingestionStatus",
        "projectStatus",
        "idempotencyRequiredEndpoints",
        "idempotencyRecordFields",
        "walkthroughRunLifecycleFields",
        "runStatus",
        "evaluationStatus",
        "claimSupportStatus",
        "claimStatus",
        "evidenceSnapshotFields",
        "evaluationResultFields",
        "retrievalStrategy",
        "stage4Budgets",
        "rateLimits",
        "backpressurePolicy",
        "cacheKeyFields",
        "cacheInvalidationTriggers",
        "cacheHitRevalidationFields",
        "providerBoundSecretScreeningInputs",
        "secretScreeningResultFields",
        "observabilitySchemas",
        "providerFallbackPolicy",
    ]
    for key in required_keys:
        if key not in contract:
            fail(f"Stage 2 architecture contract is missing key: {key}", failures)
    if contract.get("stage") != 2:
        fail("Stage 2 architecture contract must set stage to 2.", failures)
    if contract.get("canonicalIssue") != "#2":
        fail("Stage 2 architecture contract must map to issue #2.", failures)
    if contract.get("canonicalPullRequest") != "#27":
        fail("Stage 2 architecture contract must map to PR #27.", failures)
    expected_types = {
        "providerDefaults": list,
        "idPrefixes": dict,
        "documentStatus": list,
        "approvalStatus": list,
        "ingestionStatus": list,
        "projectStatus": list,
        "runStatus": list,
        "evaluationStatus": list,
        "claimSupportStatus": list,
        "claimStatus": list,
        "idempotencyRequiredEndpoints": list,
        "idempotencyRecordFields": list,
        "walkthroughRunLifecycleFields": list,
        "publicWalkthroughFields": dict,
        "evidenceSnapshotFields": list,
        "evaluationResultFields": list,
        "retrievalStrategy": dict,
        "stage4Budgets": dict,
        "rateLimits": dict,
        "backpressurePolicy": dict,
        "cacheKeyFields": list,
        "cacheInvalidationTriggers": list,
        "cacheHitRevalidationFields": list,
        "providerBoundSecretScreeningInputs": list,
        "secretScreeningResultFields": list,
        "observabilitySchemas": list,
        "providerFallbackPolicy": str,
    }
    for key, expected_type in expected_types.items():
        if not isinstance(contract.get(key), expected_type):
            fail(f"Stage 2 architecture contract {key} must be a {expected_type.__name__}.", failures)
    expected_exact_lists = {
        "documentStatus": ["UPLOADED", "STORED", "QUARANTINED", "DELETED"],
        "approvalStatus": ["PENDING", "APPROVED", "REJECTED"],
        "ingestionStatus": [
            "NOT_STARTED",
            "QUEUED",
            "RUNNING",
            "INGESTED",
            "FAILED",
            "REFUSED",
            "CANCELLED",
            "INVALIDATED",
        ],
        "projectStatus": ["ACTIVE", "DELETED"],
        "runStatus": ["QUEUED", "RUNNING", "COMPLETED", "FAILED", "REFUSED", "CANCELLED"],
        "evaluationStatus": ["PASSED", "WARNING", "FAILED", "REFUSED"],
        "claimSupportStatus": ["SUPPORTED", "UNSUPPORTED", "AMBIGUOUS"],
        "claimStatus": ["SUPPORTED", "UNSUPPORTED", "AMBIGUOUS", "MISSING_CONTEXT_REF"],
    }
    for key, expected in expected_exact_lists.items():
        if contract.get(key) != expected:
            fail(f"Stage 2 architecture contract {key} must equal {expected!r}.", failures)
    expected_id_prefixes = {
        "projectId": "proj_",
        "documentId": "doc_",
        "chunkId": "chunk_",
        "contextRefId": "ctx_",
        "ingestionRunId": "ing_",
        "runId": "run_",
        "evaluationId": "eval_",
        "claimId": "claim_",
        "claimSupportId": "claimsup_",
        "evidenceSnapshotId": "evsnap_",
        "artifactId": "art_",
        "tombstoneId": "tomb_",
        "auditEventId": "audit_",
        "requestId": "req_",
        "traceId": "trace_",
        "embeddingId": "emb_",
        "idempotencyRecordId": "idem_",
        "secretScreeningId": "secscan_",
    }
    if contract.get("idPrefixes") != expected_id_prefixes:
        fail(f"Stage 2 architecture contract idPrefixes must equal {expected_id_prefixes!r}.", failures)
    expected_idempotency_endpoints = [
        "POST /api/v1/projects",
        "PATCH /api/v1/projects/{projectId}",
        "POST /api/v1/projects/{projectId}/knowledge-documents",
        "PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval",
        "DELETE /api/v1/projects/{projectId}/knowledge-documents/{documentId}",
        "POST /api/v1/projects/{projectId}/ingestion-runs",
        "POST /api/v1/projects/{projectId}/walkthrough-runs",
        "DELETE /api/v1/projects/{projectId}",
    ]
    if contract.get("idempotencyRequiredEndpoints") != expected_idempotency_endpoints:
        fail(
            "Stage 2 architecture contract idempotencyRequiredEndpoints must equal "
            f"{expected_idempotency_endpoints!r}.",
            failures,
        )
    expected_evidence_snapshot_fields = [
        "evidence_snapshot_id",
        "tenant_id",
        "project_id",
        "document_id",
        "chunk_id",
        "source_filename",
        "chunk_index",
        "source_document_checksum",
        "chunk_checksum",
        "chunking_strategy_version",
        "retrieval_score",
        "redacted_excerpt",
        "excerpt_start",
        "excerpt_end",
        "redaction_flags",
        "captured_at",
        "snapshot_checksum",
    ]
    if contract.get("evidenceSnapshotFields") != expected_evidence_snapshot_fields:
        fail(
            "Stage 2 architecture contract evidenceSnapshotFields must equal "
            f"{expected_evidence_snapshot_fields!r}.",
            failures,
        )
    expected_evaluation_result_fields = [
        "evaluation_id",
        "run_id",
        "project_id",
        "tenant_id",
        "evaluation_status",
        "groundedness_score",
        "unsupported_claim_count",
        "unsupported_claims",
        "claim_supports",
        "context_refs",
        "context_ref_coverage",
        "evaluator_version",
        "prompt_template_version",
        "embedding_provider",
        "embedding_model",
        "embedding_model_version",
        "embedding_dimension",
        "vector_store",
        "retrieval_strategy_version",
        "retrieval_top_k",
        "retrieval_score_threshold",
        "error_code",
        "prompt_injection_detected",
        "language_check",
        "audience_fit_check",
        "output_schema_valid",
        "refusal_reason",
        "provider",
        "provider_mode",
        "model",
        "latency_ms",
        "estimated_cost",
        "created_at",
    ]
    if contract.get("evaluationResultFields") != expected_evaluation_result_fields:
        fail(
            "Stage 2 architecture contract evaluationResultFields must equal "
            f"{expected_evaluation_result_fields!r}.",
            failures,
        )
    retrieval = contract.get("retrievalStrategy", {})
    expected_refusals = [
        "EMPTY_CONTEXT",
        "LOW_RETRIEVAL_CONFIDENCE",
        "AMBIGUOUS_CONTEXT",
        "CROSS_PROJECT_CONTEXT",
        "UNSAFE_CONTEXT",
    ]
    if not isinstance(retrieval, dict):
        fail("Stage 2 architecture contract retrievalStrategy must be an object.", failures)
    elif retrieval.get("refusalReasons") != expected_refusals:
        fail(f"Stage 2 retrieval refusalReasons must equal {expected_refusals!r}.", failures)


def require_terms(rel: str, terms: list[str], failures: list[str]) -> None:
    text = read(rel) if (ROOT / rel).exists() else ""
    for term in terms:
        if term not in text:
            fail(f"{rel} must include contract term: {term}", failures)


def section_contains_exact_list(text: str, heading: str, items: list[str]) -> bool:
    section = section_between(text, heading)
    if not section:
        return False
    for item in items:
        if f"`{item}`" not in section:
            return False
    return True


def section_bullets(text: str, heading: str) -> list[str]:
    section = section_between(text, heading)
    return re.findall(r"^\s*-\s+`([^`]+)`\s*$", section, flags=re.MULTILINE)


def subsection_bullets(text: str, heading: str, start_marker: str, end_markers: tuple[str, ...]) -> list[str]:
    section = section_between(text, heading)
    start = section.find(start_marker)
    if start == -1:
        return []
    body = section[start + len(start_marker) :]
    end = len(body)
    for marker in end_markers:
        idx = body.find(marker)
        if idx != -1 and idx < end:
            end = idx
    return re.findall(r"^\s*-\s+`([^`]+)`\s*$", body[:end], flags=re.MULTILINE)


def section_between(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    next_heading = text.find("\n### ", start + len(heading))
    if next_heading == -1:
        next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def check_contract_semantics(contract: dict[str, Any], failures: list[str]) -> None:
    provider_defaults = contract.get("providerDefaults", [])
    if isinstance(provider_defaults, list):
        require_terms(".env.example", provider_defaults, failures)
        require_terms("scripts/guardrails_check.py", provider_defaults, failures)

    require_terms("docs/STATUS.md", ["#2", "#27", "Stage 2"], failures)
    require_terms("docs/STAGE_ISSUE_PLAN.md", ["Stage 2", "`#2`", "`stage2-*`"], failures)
    require_terms(
        "docs/API_CONTRACT.md",
        contract.get("idempotencyRequiredEndpoints", []) + [
            "IdempotencyRecord",
            "IDEMPOTENCY_CONFLICT",
            "BACKPRESSURE_QUEUE_FULL",
            "Retry-After",
            "`evsnap_`",
            "`tomb_`",
            "ProjectPatchRequest",
            "cacheInvalidationStatus",
            "tombstoneId",
            "already deleted",
            "acceptedScriptText",
            "rawGeneratedText",
            "documentStatus",
            "approvalStatus",
            "ingestionStatus",
            "retrievalScoreThreshold",
            "contextRefs",
            "claimSupports",
            "contextRefCoverage",
            "EvaluationSummary",
            '"schema": "EvaluationSummary"',
            '"evidenceSnapshot"',
            "embeddingProvider",
            "embeddingModel",
            "embeddingDimension",
            "vectorStore",
            "(tenantId, ownerId, projectId)",
            "evaluator_payload",
            "chunkingStrategyVersion maps to `chunking_strategy_version`",
        ],
        failures,
    )
    api_text = read("docs/API_CONTRACT.md") if (ROOT / "docs/API_CONTRACT.md").exists() else ""
    if "and request body checksum" in api_text:
        fail("docs/API_CONTRACT.md must not include request body checksum in the idempotency uniqueness scope.", failures)
    id_prefixes = contract.get("idPrefixes", {})
    if isinstance(id_prefixes, dict):
        for name, prefix in id_prefixes.items():
            if f"`{prefix}`" not in api_text:
                fail(f"docs/API_CONTRACT.md must document canonical ID prefix {name}: {prefix}", failures)
    for status in ("RESERVED", "RUNNING", "SUCCEEDED", "FAILED", "EXPIRED"):
        if f"`{status}`" not in api_text and f'"{status}"' not in api_text:
            fail(f"docs/API_CONTRACT.md must include idempotency status: {status}", failures)
    if '"acceptedScriptText": null' in api_text:
        fail("docs/API_CONTRACT.md failed/refused examples must omit acceptedScriptText instead of returning null.", failures)
    if "Response `200` for failed or refused output" in api_text:
        fail("docs/API_CONTRACT.md must not label new failed/refused POST output as Response 200.", failures)
    idempotency_section = section_between(api_text, "## Idempotency Requirements")
    if "- optional `responseStatus`" not in idempotency_section:
        fail("docs/API_CONTRACT.md IdempotencyRecord responseStatus must be optional.", failures)
    typed_schema_section = section_between(api_text, "## Typed Response Schemas")
    for schema_name in ("EvaluationSummary", "ClaimSupport"):
        if f"`{schema_name}`" not in typed_schema_section:
            fail(f"docs/API_CONTRACT.md required schema list must include {schema_name}.", failures)
    evaluation_response_section = section_between(api_text, "### Get Evaluation Result")
    for field_name in (
        "promptInjectionDetected",
        "languageCheck",
        "audienceFitCheck",
        "outputSchemaValid",
        "provider",
        "providerMode",
        "latencyMs",
        "estimatedCost",
    ):
        if f'"{field_name}"' not in evaluation_response_section:
            fail(f"docs/API_CONTRACT.md EvaluationResult response must include {field_name}.", failures)
    accepted_run_section = section_between(api_text, "### Generate Walkthrough")
    for field_name in (
        "tenantId",
        "projectId",
        "runId",
        "evaluationId",
        "chunkId",
        "documentId",
        "supportReason",
    ):
        if f'"{field_name}"' not in accepted_run_section:
            fail(f"docs/API_CONTRACT.md embedded claimSupports must include canonical ClaimSupport field {field_name}.", failures)
    for unsafe_error_term in (
        "raw prompts",
        "raw uploads",
        "provider payloads",
        "stack traces",
        "environment variables",
        "secrets",
    ):
        if unsafe_error_term not in api_text:
            fail(f"docs/API_CONTRACT.md must ban {unsafe_error_term} in error details.", failures)
    retrieval = contract.get("retrievalStrategy", {})
    if isinstance(retrieval, dict):
        expected_tie_break = ["score desc", "approved_at desc", "chunk_index asc", "chunk_id asc"]
        if retrieval.get("tieBreakOrder") != expected_tie_break:
            fail(f"Stage 2 retrieval tie-break order must be {expected_tie_break!r}.", failures)
        require_terms("docs/ARCHITECTURE.md", expected_tie_break, failures)
        require_terms("docs/ADR/0002-rag-storage.md", expected_tie_break, failures)
        refusal_reasons = retrieval.get("refusalReasons", [])
        if isinstance(refusal_reasons, list):
            for rel in (
                "docs/API_CONTRACT.md",
                "docs/AI_SAFETY_AND_EVALUATION.md",
                "docs/ARCHITECTURE.md",
                "docs/ADR/0002-rag-storage.md",
            ):
                require_terms(rel, refusal_reasons, failures)
    require_terms(
        "docs/DATA_MODEL.md",
        contract.get("idempotencyRecordFields", [])
        + contract.get("walkthroughRunLifecycleFields", [])
        + contract.get("evidenceSnapshotFields", [])
        + [
            "IdempotencyRecord",
            "EvidenceSnapshot",
            "JobLease",
            "OutboxEvent",
            "raw_generated_text",
            "accepted_script_text",
            "claim_supports",
            "context_ref_coverage",
            "project_status",
            "Tombstone",
        ],
        failures,
    )
    data_text = read("docs/DATA_MODEL.md") if (ROOT / "docs/DATA_MODEL.md").exists() else ""
    knowledge_document_section = section_between(data_text, "### KnowledgeDocument")
    for field_name in ("approved_by", "ingested_at"):
        if f"- optional `{field_name}`" not in knowledge_document_section:
            fail(f"docs/DATA_MODEL.md KnowledgeDocument field {field_name} must be optional.", failures)
    normalized_data_text = re.sub(r"\s+", " ", data_text)
    required_idempotency_index = "(tenant_id, actor_id, idempotency_scope, endpoint, idempotency_key)"
    stale_idempotency_index = "(tenant_id, actor_id, project_id, endpoint, idempotency_key)"
    if required_idempotency_index not in normalized_data_text:
        fail(f"docs/DATA_MODEL.md Required Indexes must include {required_idempotency_index}.", failures)
    if stale_idempotency_index in normalized_data_text:
        fail(f"docs/DATA_MODEL.md must not use stale idempotency index {stale_idempotency_index}.", failures)
    walkthrough_statuses = subsection_bullets(data_text, "### WalkthroughRun", "Statuses:", ("Indexes:", "Rules:"))
    if walkthrough_statuses != contract.get("runStatus", []):
        fail("docs/DATA_MODEL.md WalkthroughRun statuses must exactly match the canonical runStatus enum.", failures)
    ingestion_statuses = subsection_bullets(data_text, "### IngestionRun", "Statuses:", ("Indexes:", "Rules:"))
    if ingestion_statuses != contract.get("runStatus", []):
        fail("docs/DATA_MODEL.md IngestionRun statuses must exactly match the canonical runStatus enum.", failures)
    ingestion_section = section_between(data_text, "### IngestionRun")
    job_lease_section = section_between(data_text, "### JobLease")
    for section_name, section_text in (("IngestionRun", ingestion_section), ("JobLease", job_lease_section)):
        for field_name in ("locked_by", "locked_at", "lease_expires_at"):
            if f"`{field_name}`" not in section_text:
                fail(f"docs/DATA_MODEL.md {section_name} must use canonical lease field {field_name}.", failures)
        if "lease_owner" in section_text:
            fail(f"docs/DATA_MODEL.md {section_name} must not use stale lease_owner field.", failures)
    evaluation_section = section_between(data_text, "### EvaluationResult")
    for term in contract.get("evaluationResultFields", []):
        if term not in evaluation_section:
            fail(f"docs/DATA_MODEL.md EvaluationResult must include field: {term}", failures)
    project_section = section_between(data_text, "### Project")
    for status in contract.get("projectStatus", []):
        if f"`{status}`" not in project_section:
            fail(f"docs/DATA_MODEL.md Project must include project_status: {status}", failures)
    unsupported_claim_section = section_between(data_text, "### UnsupportedClaim")
    for status in contract.get("claimStatus", []):
        if f"`{status}`" not in unsupported_claim_section:
            fail(f"docs/DATA_MODEL.md UnsupportedClaim must include claim_status: {status}", failures)
    claim_support_section = section_between(data_text, "### ClaimSupport")
    for status in contract.get("claimSupportStatus", []):
        if f"`{status}`" not in claim_support_section:
            fail(f"docs/DATA_MODEL.md ClaimSupport must include support_status: {status}", failures)
    tombstone_statuses = subsection_bullets(data_text, "### Tombstone", "Cache invalidation statuses:", ("Indexes:", "Rules:"))
    if tombstone_statuses != ["PENDING", "COMPLETED", "FAILED"]:
        fail("docs/DATA_MODEL.md Tombstone cache_invalidation_status must exactly match PENDING/COMPLETED/FAILED.", failures)
    evidence_fields = contract.get("evidenceSnapshotFields", [])
    if isinstance(evidence_fields, list):
        require_terms("docs/DATA_MODEL.md", evidence_fields, failures)
        require_terms("docs/AI_SAFETY_AND_EVALUATION.md", evidence_fields, failures)
        camelish = {
            "source_filename": "sourceFilename",
            "chunk_index": "chunkIndex",
            "retrieval_score": "retrievalScore",
        }
        require_terms("docs/API_CONTRACT.md", list(camelish.values()), failures)
    require_terms(
        "docs/AI_SAFETY_AND_EVALUATION.md",
        [
            "tenant_id",
            "claim_supports",
            "context_ref_coverage",
            "CLAIM_BUDGET_EXCEEDED",
            "EvidenceSnapshot",
            "scriptText",
            "evaluation_status",
        ],
        failures,
    )
    ai_safety_text = read("docs/AI_SAFETY_AND_EVALUATION.md") if (ROOT / "docs/AI_SAFETY_AND_EVALUATION.md").exists() else ""
    ai_eval_section = section_between(ai_safety_text, "## Evaluation Result Schema")
    for term in contract.get("evaluationResultFields", []):
        if term not in ai_eval_section:
            fail(f"docs/AI_SAFETY_AND_EVALUATION.md Evaluation Result Schema must include field: {term}", failures)
    require_terms(
        "docs/ARCHITECTURE.md",
        [
            "Knowledge State Separation",
            "Queue, Lease, Attempt, And Outbox Contract",
            "Retrieval Strategy v1",
            "retrieval_score_threshold = 0.72",
            "LOW_RETRIEVAL_CONFIDENCE",
            "AMBIGUOUS_CONTEXT",
            "PROVIDER_FALLBACK_BLOCKED",
            "ACID",
            "atomic compare-and-swap",
        ],
        failures,
    )
    require_terms(
        "docs/OBSERVABILITY_AND_COST.md",
        contract.get("cacheKeyFields", [])
        + contract.get("cacheInvalidationTriggers", [])
        + contract.get("cacheHitRevalidationFields", [])
        + ["RunMetadata", "EventEnvelope", "MetricPoint", "generatedScriptWords = 1200"],
        failures,
    )
    require_terms("docs/SECURITY_AND_PRIVACY.md", contract.get("secretScreeningResultFields", []), failures)
    require_terms("docs/SECURITY_AND_PRIVACY.md", contract.get("providerBoundSecretScreeningInputs", []), failures)
    require_terms(
        "docs/SECURITY_AND_PRIVACY.md",
        [
            "1,200 words",
            "100 extracted project-specific factual claims",
            "evaluator_version",
            "prompt_template_version",
            "embedding_model_version",
            "deterministic, rule-backed evaluation",
        ],
        failures,
    )
    require_terms(
        "docs/THREAT_MODEL.md",
        ["Deterministic Stage 4 evaluator", "Model-as-judge evaluation is future scope"],
        failures,
    )
    budgets = contract.get("stage4Budgets", {})
    if isinstance(budgets, dict):
        required_budget_values = {
            "fileSizeMiB": 1,
            "documentsPerProject": 10,
            "projectCorpusMiB": 5,
            "chunkTargetTokens": 800,
            "chunkMaxTokens": 1000,
            "chunkOverlapTokens": 100,
            "chunksPerDocument": 100,
            "chunksPerProject": 200,
            "embeddingBatchSize": 32,
            "retrievalTopK": 6,
            "promptContextTokens": 6000,
            "generatedScriptWords": 1200,
            "generatedScriptOutputTokens": 2500,
            "unsupportedClaimsEvaluated": 100,
            "automaticRetryMax": 1,
            "generationTimeoutSeconds": 60,
            "evaluationTimeoutSeconds": 30,
            "queueCapacity": 20,
            "initialPageSize": 20,
            "maxPageSize": 100,
            "maxOffsetDepth": 500,
            "cacheTtlHours": 24,
            "cacheEntriesPerProject": 100,
            "mockLocalCostBudgetUsd": 0,
            "freeProviderDailyBudgetUsd": 1,
        }
        for key, expected in required_budget_values.items():
            if budgets.get(key) != expected:
                fail(f"Stage 2 budget {key} must be locked to {expected!r}.", failures)
        for key, value in budgets.items():
            if not isinstance(value, (int, float)):
                fail(f"Stage 2 budget {key} must be numeric.", failures)
            if key != "mockLocalCostBudgetUsd" and isinstance(value, (int, float)) and value <= 0:
                fail(f"Stage 2 budget {key} must be positive.", failures)
    backpressure = contract.get("backpressurePolicy", {})
    if isinstance(backpressure, dict):
        if backpressure.get("queueFullCode") != "BACKPRESSURE_QUEUE_FULL":
            fail("Stage 2 backpressure policy must use BACKPRESSURE_QUEUE_FULL.", failures)
        if backpressure.get("queueCapacityScope") != "per_project":
            fail("Stage 2 backpressure policy must scope queue capacity per project.", failures)
        if backpressure.get("retryAfterRequired") is not True:
            fail("Stage 2 backpressure policy must require Retry-After.", failures)
    rate_limits = contract.get("rateLimits", {})
    if isinstance(rate_limits, dict):
        expected_limits = {
            "uploadRequestsPerProjectPerHour": 30,
            "ingestionJobsPerProjectPerHour": 10,
            "concurrentIngestionJobsPerProject": 1,
            "generationRunsPerProjectPerHour": 20,
            "concurrentGenerationJobsPerProject": 1,
            "providerCallsPerProviderModeProjectHour": 30,
        }
        for key, expected in expected_limits.items():
            if rate_limits.get(key) != expected:
                fail(f"Stage 2 rate limit {key} must be locked to {expected!r}.", failures)
        require_terms("docs/SECURITY_AND_PRIVACY.md", [str(value) for value in expected_limits.values()], failures)
    fallback_policy = contract.get("providerFallbackPolicy", "")
    if isinstance(fallback_policy, str):
        for term in ("Only same-egress-class fallback", "PROVIDER_FALLBACK_BLOCKED"):
            if term not in fallback_policy:
                fail(f"Stage 2 providerFallbackPolicy must include: {term}", failures)
        if "unless explicitly configured" in fallback_policy:
            fail(
                "Stage 2 providerFallbackPolicy must not allow mock/local to non-local fallback by configuration.",
                failures,
            )
    workflow = read(".github/workflows/quality-gates.yml") if (ROOT / ".github/workflows/quality-gates.yml").exists() else ""
    if isinstance(provider_defaults, list):
        for default in provider_defaults:
            if "=" in default:
                key, value = default.split("=", 1)
                yaml_default = f"{key}: {value}"
            else:
                yaml_default = default
            if default not in workflow and yaml_default not in workflow:
                fail(f".github/workflows/quality-gates.yml must set deterministic provider default: {default}", failures)


def check_no_contradictory_stage2_language(failures: list[str]) -> None:
    combined = "\n".join(
        read(rel)
        for rel in (
            "docs/ARCHITECTURE.md",
            "docs/SECURITY_AND_PRIVACY.md",
            "docs/API_CONTRACT.md",
            "docs/AI_SAFETY_AND_EVALUATION.md",
            "docs/QUALITY_GATES.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/THREAT_MODEL.md",
            "docs/PORTABILITY_STRATEGY.md",
        )
        if (ROOT / rel).exists()
    )
    normalized = " ".join(combined.split())
    banned = [
        "optional obvious-secret screening before non-local provider egress",
        "fail, warn, or regenerate according to stage policy",
        "Authentication is future Stage 3/4 design",
        "Before Stage 4 code:",
        "During Stage 1, `make quality`",
        "Current Stage 1 behavior",
        "future `tenant_id`",
        "future tenant_id",
    ]
    for phrase in banned:
        if phrase in combined or phrase in normalized:
            fail(f"Stage 2 docs still contain unresolved or contradictory language: {phrase}", failures)


def check_makefile_and_dispatcher(failures: list[str]) -> None:
    makefile = read("Makefile") if (ROOT / "Makefile").exists() else ""
    dispatcher = read("scripts/quality/check_quality_stage.py") if (ROOT / "scripts/quality/check_quality_stage.py").exists() else ""
    guardrails = read("scripts/guardrails_check.py") if (ROOT / "scripts/guardrails_check.py").exists() else ""
    if "python3 scripts/quality/check_stage2_docs.py" not in makefile:
        fail("Makefile stage2-quality must run scripts/quality/check_stage2_docs.py.", failures)
    if "check_stage2_docs.py" not in dispatcher:
        fail("scripts/quality/check_quality_stage.py must dispatch Stage 2 to check_stage2_docs.py.", failures)
    for default in (
        "LLM_PROVIDER=mock",
        "EMBEDDING_PROVIDER=mock",
        "EVALUATION_PROVIDER=mock",
        "TRANSLATION_PROVIDER=mock",
        "AVATAR_PROVIDER=mock",
        "TTS_PROVIDER=mock",
        "STT_PROVIDER=mock",
        "SUBTITLE_PROVIDER=mock",
        "VIDEO_RENDERER=local",
        "STORAGE_PROVIDER=local",
        "VECTOR_STORE=disabled",
    ):
        if default not in guardrails:
            fail(f"scripts/guardrails_check.py must enforce provider default: {default}", failures)


def line_for_match(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def is_allowlisted_secret_match(rel: str, text: str, match: re.Match[str]) -> bool:
    matched_text = match.group(0)
    if rel.endswith(".env.example") and matched_text.endswith("="):
        return True
    if rel.endswith(".env.example") and re.search(r"=\s*['\"]?\s*['\"]?$", matched_text):
        return True
    if "PLACEHOLDER" in matched_text or "example" in matched_text.lower():
        return True
    line = line_for_match(text, match)
    if rel in {"scripts/guardrails_check.py", "scripts/quality/check_stage2_docs.py"}:
        if "re.compile" in line or "SECRET_PATTERNS" in line or "PROVIDER_KEY_NAMES" in line:
            return True
        if "providerDefaults" in line or "check_mock_local_defaults" in line:
            return True
    return False


def check_no_obvious_secrets(failures: list[str]) -> None:
    for rel in repo_files():
        path = ROOT / rel
        if path.suffix.lower() in PRIVATE_KEY_CERT_SUFFIXES:
            fail(f"{rel} is a key/certificate file. Private keys and certificates must not be committed.", failures)
            continue
        if not path.is_file() or path.suffix not in {".json", ".md", ".py", ".txt", ".yaml", ".yml", ".example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if is_allowlisted_secret_match(rel, text, match):
                    continue
                fail(f"Potential committed secret pattern found in {rel}.", failures)


def check_python_governance_scripts(failures: list[str]) -> None:
    for rel in PYTHON_GOVERNANCE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            fail(f"{rel} must compile: {exc}", failures)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module.split(".", 1)[0]]
            else:
                continue
            for root in roots:
                if root not in STDLIB_IMPORT_ROOTS:
                    fail(f"{rel} imports non-stdlib dependency {root!r}.", failures)


def check_git_diff_clean(failures: list[str]) -> None:
    result = run(["git", "diff", "--check"])
    if result.returncode != 0:
        fail(result.stdout.strip() or result.stderr.strip() or "git diff --check failed.", failures)


def main() -> int:
    failures: list[str] = []
    try:
        files = repo_files()
    except RuntimeError as exc:
        print(f"Stage 2 quality failures:\n- {exc}")
        return 1

    check_required_files(failures)
    check_current_stage(failures)
    check_branch_name(failures)
    check_stage2_scope(failures)
    check_no_product_code(files, failures)
    check_required_phrases(failures)
    contract = load_stage2_contract(failures)
    if contract:
        check_contract_invariants(contract, failures)
        check_contract_semantics(contract, failures)
    check_retrieval_strategy_v1_parity(ROOT, failures)
    check_adr_canon(failures)
    check_mock_local_defaults(failures)
    check_no_contradictory_stage2_language(failures)
    check_makefile_and_dispatcher(failures)
    check_no_obvious_secrets(failures)
    check_python_governance_scripts(failures)
    check_git_diff_clean(failures)

    if failures:
        print("Stage 2 quality failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 2 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
