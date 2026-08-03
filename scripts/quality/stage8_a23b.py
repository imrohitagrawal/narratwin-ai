from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

A23B_BRANCH = "stage8-353-r0c-a2-3b-evaluation-lineage-v2"
A23A_BRANCH = "cut1-351-r0c-a2-3a-evaluation-lineage-contract"
A23B_BASE, A23B_LINE_CAP = "90bbd59a84913ce9c7601bc180e051347cfccbcf", 2700
A23B_ALLOWED_FILES = {
    "backend/app/evaluation_lineage.py",
    "backend/app/evaluation_lineage_state.py",
    "backend/app/main.py",
    "backend/app/stage6.py",
    "backend/app/stage7.py",
    "backend/app/storage/local_restore_drill.py",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/governance/preflights/issue-353.json",
    "scripts/guardrails_check.py",
    "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_a23b.py",
    "tests/acceptance/test_checkpoint3_full_project_multilingual.py",
    "tests/acceptance/test_checkpoint3_media_artifacts.py",
    "tests/api/test_stage7_avatar_api.py",
    "tests/unit/test_evaluation_lineage.py",
    "tests/unit/test_evaluation_lineage_state.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_local_durability.py",
    "tests/unit/test_local_restore_drill.py",
    "tests/unit/test_stage6_multilingual.py",
    "tests/unit/test_stage7_avatar.py",
    "tests/unit/test_stage8_quality_gate.py",
}
A23A_ALLOWED_FILES = {
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/API_CONTRACT.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/governance/preflights/issue-351.json",
    "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py",
}
A23_ROUTES = {A23A_BRANCH: A23A_ALLOWED_FILES, A23B_BRANCH: A23B_ALLOWED_FILES}
LEGACY_FIELDS = (
    ("evaluation", "id"),
    ("run", "id"),
    ("trace", "id"),
    ("evaluation", "status"),
    ("context", "ref"),
    ("citation",),
)


def _negative_typeerror(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.With):
            return "pytest.raises(TypeError)" in ast.unparse(node.items[0].context_expr)
    return False


def _resolve(node: ast.AST, assignments: dict[str, ast.AST]) -> ast.AST:
    seen: set[str] = set()
    while isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
        seen.add(node.id)
        node = assignments[node.id]
    return node


def _legacy_fields(node: ast.AST, assignments: dict[str, ast.AST]) -> bool:
    node = _resolve(node, assignments)
    if isinstance(node, (ast.GeneratorExp, ast.ListComp)) and node.generators:
        node = _resolve(node.generators[0].iter, assignments)
    if not isinstance(node, (ast.List, ast.Tuple)) or len(node.elts) != 6:
        return False
    fields = [ast.unparse(field).lower() for field in node.elts]
    return all(all(token in field for token in group) for field, group in zip(fields, LEGACY_FIELDS, strict=True))


def _legacy_preimage(
    node: ast.AST,
    assignments: dict[str, ast.AST],
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
    seen: frozenset[int] = frozenset(),
) -> bool:
    node = _resolve(node, assignments)
    if id(node) in seen:
        return False
    seen |= {id(node)}
    if isinstance(node, ast.Starred):
        return _legacy_preimage(node.value, assignments, functions, seen)
    if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 1:
        return _legacy_preimage(node.elts[0], assignments, functions, seen)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "encode":
            return _legacy_preimage(node.func.value, assignments, functions, seen)
        if node.func.attr == "join" and node.args:
            separator = _resolve(node.func.value, assignments)
            return (
                isinstance(separator, ast.Constant)
                and separator.value == "\n"
                and _legacy_fields(node.args[0], assignments)
            )
    if isinstance(node, ast.Call):
        function = _resolve(node.func, assignments)
        name = function.id if isinstance(function, ast.Name) else ""
        definition = function if isinstance(function, ast.Lambda) else functions.get(name)
        if definition:
            function_args = definition.args
            positional_args = (*function_args.posonlyargs, *function_args.args)
            bindings = assignments | dict(
                zip((arg.arg for arg in positional_args[::-1]), function_args.defaults[::-1], strict=False)
            )
            bindings.update(
                (arg.arg, value)
                for arg, value in zip(function_args.kwonlyargs, function_args.kw_defaults, strict=True)
                if value is not None
            )
            bindings.update(zip((arg.arg for arg in positional_args), node.args, strict=False))
            if function_args.vararg:
                bindings[function_args.vararg.arg] = ast.Tuple(elts=node.args[len(positional_args) :], ctx=ast.Load())
            bindings.update((item.arg, item.value) for item in node.keywords if item.arg)
            if isinstance(definition, ast.Lambda):
                values = iter((definition.body,))
            else:
                values = (item.value for item in ast.walk(definition) if isinstance(item, ast.Return) and item.value)
            return any(_legacy_preimage(value, bindings, functions, seen) for value in values)
    if isinstance(node, ast.JoinedStr) or isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        names = [ast.unparse(item).lower() for item in ast.walk(node) if isinstance(item, (ast.Name, ast.Attribute))]
        newline = any(isinstance(item, ast.Constant) and item.value == "\n" for item in ast.walk(node))
        return newline and all(
            any(all(token in name for token in group) for name in names) for group in LEGACY_FIELDS
        )
    return False


def semantic_legacy_failures(path: Path, source: str | None = None) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8") if source is None else source, filename=path.as_posix())
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    assignments: dict[str, ast.AST] = {
        target.id: node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    checksum_names = {"build_source_evaluation_checksum"}
    checksum_names.update(
        alias.asname
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name == "build_source_evaluation_checksum" and alias.asname
    )
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = _resolve(node.func, assignments)
        name = function.attr if isinstance(function, ast.Attribute) else getattr(function, "id", "")
        if name in checksum_names and len(node.args) != 1:
            if not _negative_typeerror(node, parents):
                failures.append(f"{path}: legacy evaluation-checksum call")
        arguments = (*node.args, *(item.value for item in node.keywords))
        if any(_legacy_preimage(argument, assignments, functions) for argument in arguments):
            failures.append(f"{path}: manual six-field evaluation-checksum preimage")
    return failures


def a23a_markers_frozen(markers: object) -> bool:
    encoded = json.dumps(markers, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest() == "0087f47c997797f9df40bd270379168b253ee7c744be71383a7c581592600288"


def semantic_detector_self_test(workdir: Path) -> bool:
    direct = (
        "build_source_evaluation_checksum(evaluation_id=e,run_id=r,trace_id=t,"
        "evaluation_status=s,context_ref_ids=c,citation_indexes=i)"
    )
    fields = "[evaluation_id,run_id,trace_id,evaluation_status,context_ref_ids,citation_indexes]"
    indirect = "fields=" + fields + '\nchecksum_text("\\n".join(fields))'
    generator = indirect.replace("join(fields)", "join(value for value in fields)")
    concat = (
        'checksum_text(evaluation_id+"\\n"+run_id+"\\n"+trace_id+"\\n"+'
        'evaluation_status+"\\n"+context_ref_ids+"\\n"+citation_indexes)'
    )
    joined = '"\\n".join(' + fields + ")"
    helper = "def legacy(): return " + joined + "\nchecksum_text(legacy())"
    parameter = "def legacy(fields): return '\\n'.join(fields)\nchecksum_text(legacy(" + fields + "))"
    positional_only = parameter.replace("legacy(fields)", "legacy(fields, /)")
    vararg = ("def legacy(prefix,*fields): return '\\n'.join(fields)\nchecksum_text(legacy('x',"
              + fields[1:-1] + "))")
    lambda_forward = parameter.replace("def legacy(fields): return", "legacy = lambda fields:")
    fstring = 'checksum_text(f"' + "\\n".join("{" + item + "}" for item in fields[1:-1].split(",")) + '")'
    alias = "legacy=build_source_evaluation_checksum\n" + direct.replace("build_source_evaluation_checksum", "legacy")
    starred = "values=[" + joined + "]\nchecksum_text(*values)"
    cycle = "value=value.encode()\nchecksum_text(value)"
    samples = (
        ("direct.py", direct, True),
        ("fstring.py", fstring, True),
        ("indirect.py", indirect, True),
        ("generator.py", generator, True),
        ("concat.py", concat, True),
        ("helper.py", helper, True),
        ("parameter.py", parameter, True),
        ("positional.py", positional_only, True),
        ("vararg.py", vararg, True),
        ("lambda.py", lambda_forward, True),
        ("alias.py", alias, True),
        ("starred.py", starred, True),
        ("cycle.py", cycle, False),
        ("canonical.py", "build_source_evaluation_checksum(lineage_payload)", False),
    )
    results = (
        bool(semantic_legacy_failures(workdir / name, sample)) is expected
        for name, sample, expected in samples
    )
    source = Path(__file__).read_text(encoding="utf-8")
    lines = source.splitlines()
    bounded = len(lines) <= 250 and len(source.encode()) <= 32 * 1024 and max(map(len, lines)) <= 120
    checker = Path(__file__).with_name("check_stage8_docs.py").read_text(encoding="utf-8")
    return all(results) and bounded and "check_a23b(ROOT, run, failures," in checker


def check_a23b(root: Path, run: Callable[[list[str]], Any], failures: list[str], exact_route: bool = True) -> None:
    for path in root.rglob("*.py"):
        if not any(part in {".git", ".venv"} for part in path.parts):
            failures.extend(semantic_legacy_failures(path))
    if not exact_route:
        return
    artifact = json.loads((root / "docs/governance/preflights/issue-353.json").read_text())
    scope_matches = set(artifact.get("scope", {}).get("required", ())) == A23B_ALLOWED_FILES
    if artifact.get("branch") != A23B_BRANCH or not scope_matches:
        failures.append("Issue #353 preflight does not match its exact branch and 24-path scope.")
    merge_base = run(["git", "merge-base", A23B_BASE, "HEAD"])
    if merge_base.returncode or merge_base.stdout.strip() != A23B_BASE:
        failures.append("Issue #353 merge base does not match its exact authorized base.")
    numstat = run(["git", "diff", "--numstat", A23B_BASE, "--"])
    rows = [row.split("\t") for row in numstat.stdout.splitlines()]
    if numstat.returncode or any(len(row) != 3 or not row[0].isdigit() or not row[1].isdigit() for row in rows):
        failures.append("Issue #353 charged-line evidence is unavailable.")
    elif sum(int(row[0]) + int(row[1]) for row in rows) > A23B_LINE_CAP:
        failures.append("Issue #353 exceeds its 2,700 charged-line hard ceiling.")
