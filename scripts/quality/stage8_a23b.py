from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

A23B_BRANCH = "stage8-353-r0c-a2-3b-evaluation-lineage-v2"
A23A_BRANCH = "cut1-351-r0c-a2-3a-evaluation-lineage-contract"
A23B_BASE, A23B_LINE_CAP = "90bbd59a84913ce9c7601bc180e051347cfccbcf", 1600
A23B_ALLOWED_FILES = {
    "tests/acceptance/test_checkpoint3_full_project_multilingual.py", "backend/app/storage/local_restore_drill.py",
    "tests/acceptance/test_checkpoint3_media_artifacts.py", "docs/governance/preflights/issue-353.json",
    "tests/unit/test_stage6_multilingual.py", "tests/unit/test_local_restore_drill.py", "backend/app/stage6.py",
    "tests/unit/test_stage8_quality_gate.py", "scripts/quality/check_stage8_docs.py", "backend/app/stage7.py",
    "tests/unit/test_local_durability.py", "tests/api/test_stage7_avatar_api.py", "scripts/quality/stage8_a23b.py",
    "backend/app/evaluation_lineage.py", "tests/unit/test_stage7_avatar.py", "backend/app/main.py",
    "docs/STATUS.md",
}
A23A_ALLOWED_FILES = {
    "docs/governance/preflights/issue-351.json", "docs/STATUS.md", "docs/API_CONTRACT.md",
    "docs/ADR/0004-avatar-provider-adapter.md", "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md",
    "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py",
}
A23_ROUTES = {A23A_BRANCH: A23A_ALLOWED_FILES, A23B_BRANCH: A23B_ALLOWED_FILES}
LEGACY_FIELDS = (
    ("evaluation", "id"), ("run", "id"), ("trace", "id"), ("evaluation", "status"), ("context", "ref"), ("citation",),
)


def _negative_typeerror(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.With):
            return "pytest.raises(TypeError)" in ast.unparse(node.items[0].context_expr)
    return False


def semantic_legacy_failures(path: Path, source: str | None = None) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8") if source is None else source, filename=path.as_posix())
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        if name == "build_source_evaluation_checksum" and len(node.args) != 1:
            if not _negative_typeerror(node, parents):
                failures.append(f"{path}: legacy evaluation-checksum call")
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "join":
            continue
        if not isinstance(node.func.value, ast.Constant) or node.func.value.value != "\n":
            continue
        sequence = node.args[0] if node.args else None
        if not isinstance(sequence, (ast.List, ast.Tuple)) or len(sequence.elts) != 6:
            continue
        fields = [ast.unparse(field).lower() for field in sequence.elts]
        if all(all(token in field for token in group) for field, group in zip(fields, LEGACY_FIELDS, strict=True)):
            failures.append(f"{path}: manual six-field evaluation-checksum preimage")
    return failures


def a23a_markers_frozen(markers: object) -> bool:
    encoded = json.dumps(markers, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest() == "0087f47c997797f9df40bd270379168b253ee7c744be71383a7c581592600288"


def semantic_detector_self_test(workdir: Path) -> bool:
    direct = ("build_source_evaluation_checksum(evaluation_id=e,run_id=r,trace_id=t,"
              "evaluation_status=s,context_ref_ids=c,citation_indexes=i)")
    manual = ('checksum_text("\\n".join([evaluation_id,run_id,trace_id,'
              'evaluation_status,context_ref_ids,citation_indexes]))')
    samples = (("direct.py", direct, True), ("manual.py", manual, True),
               ("canonical.py", "build_source_evaluation_checksum(lineage_payload)", False))
    results = (bool(semantic_legacy_failures(workdir / name, sample)) is expected
               for name, sample, expected in samples)
    source = Path(__file__).read_text(encoding="utf-8")
    lines = source.splitlines()
    bounded = len(lines) <= 250 and len(source.encode()) <= 32 * 1024 and max(map(len, lines)) <= 120
    return all(results) and bounded


def check_a23b(root: Path, run: Callable[[list[str]], Any], failures: list[str]) -> None:
    artifact = json.loads((root / "docs/governance/preflights/issue-353.json").read_text())
    scope_matches = set(artifact.get("scope", {}).get("required", ())) == A23B_ALLOWED_FILES
    if artifact.get("branch") != A23B_BRANCH or not scope_matches:
        failures.append("Issue #353 preflight does not match its exact branch and 17-path scope.")
    merge_base = run(["git", "merge-base", A23B_BASE, "HEAD"])
    if merge_base.returncode or merge_base.stdout.strip() != A23B_BASE:
        failures.append("Issue #353 merge base does not match its exact authorized base.")
    numstat = run(["git", "diff", "--numstat", A23B_BASE, "--"])
    rows = [row.split("\t") for row in numstat.stdout.splitlines()]
    if numstat.returncode or any(len(row) != 3 or not row[0].isdigit() or not row[1].isdigit() for row in rows):
        failures.append("Issue #353 charged-line evidence is unavailable.")
    elif sum(int(row[0]) + int(row[1]) for row in rows) > A23B_LINE_CAP:
        failures.append("Issue #353 exceeds its 1,600 charged-line hard ceiling.")
    for path in root.rglob("*.py"):
        if not any(part in {".git", ".venv"} for part in path.parts):
            failures.extend(semantic_legacy_failures(path))
