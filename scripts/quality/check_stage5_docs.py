#!/usr/bin/env python3
"""Executable Stage 5 quality gate for evaluations, guardrails, and observability."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE5_BRANCH_PATTERN = re.compile(r"^stage5-")

REQUIRED_FILES = [
    ".stage/current",
    ".github/workflows/eval-smoke.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    "Makefile",
    "backend/app/main.py",
    "backend/app/stage4.py",
    "backend/app/rag/grounding.py",
    "backend/app/rag/models.py",
    "backend/app/eval/runner.py",
    "backend/app/eval/metrics.py",
    "backend/app/eval/unsupported_claims.py",
    "backend/app/eval/script_faithfulness.py",
    "backend/app/observability/__init__.py",
    "backend/app/observability/langfuse.py",
    "backend/app/observability/logs.py",
    "backend/app/observability/metrics.py",
    "backend/app/observability/traces.py",
    "evals/smoke/stage5_grounded_script_dataset.json",
    "evals/smoke/stage5_prompt_injection_set.json",
    "evals/smoke/stage5_file_upload_abuse_set.json",
    "tests/unit/test_retrieval_and_grounding.py",
    "tests/unit/test_health_contract.py",
    "tests/api/test_health_api.py",
    "tests/api/test_stage4_slice_api.py",
    "scripts/ci/eval-smoke.sh",
    "scripts/quality/check_stage5_docs.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "docs/EVAL_REPORT.md",
    "docs/ADR/0005-observability-and-evals.md",
    "docs/API_CONTRACT.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "uv.lock",
]

STAGE5_ALLOWED_FILES = set(REQUIRED_FILES) | {
    "backend/app/eval/__init__.py",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.test.tsx",
    "frontend/src/app/page.module.css",
    "frontend/tests/smoke.spec.ts",
}

BLOCKED_STAGE5_PATTERNS = [
    re.compile(r"(^|/)(avatar|tts|voice|subtitle|video|rendering|heygen|elevenlabs|tavus|wav2lip)(/|$)", re.IGNORECASE),
]

REQUIRED_DIRECT_DEPENDENCIES = {
    "langfuse",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-instrumentation-fastapi",
    "structlog",
    "prometheus-client",
}

MAX_SMOKE_CASES = 20
MAX_UPLOAD_FIXTURE_BYTES = 16 * 1024


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = ""
    attempted: list[str] = []

    for candidate in [item for item in base_candidates if item]:
        attempted.append(candidate)
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break

    if not merge_base:
        raise RuntimeError(f"git merge-base failed for Stage 5 scope. Tried: {', '.join(attempted)}")

    outputs: list[str] = []
    for args in (
        ["git", "diff", "--name-only", f"{merge_base}..HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        result = run(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
        outputs.append(result.stdout)

    return sorted({line.strip() for output in outputs for line in output.splitlines() if line.strip()})


def check_required_files(failures: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            fail(f"Missing required Stage 5 file: {path}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "5":
        fail(".stage/current must contain 5 for Stage 5 quality.", failures)

    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch and branch != "main" and not STAGE5_BRANCH_PATTERN.match(branch):
        fail(f"Stage 5 work must run on a stage5-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    for path in changed_files_for_stage_scope():
        if path not in STAGE5_ALLOWED_FILES:
            fail(f"Stage 5 changed file outside the allowlist: {path}", failures)
        for blocked in BLOCKED_STAGE5_PATTERNS:
            if blocked.search(path):
                fail(f"Stage 5 may not include blocked scope: {path}", failures)


def check_dependencies(failures: list[str]) -> None:
    data = tomllib.loads(read("pyproject.toml"))
    project = data.get("project", {})
    dependencies = {
        re.split(r"[<>=!~\[]", value, maxsplit=1)[0].strip().lower()
        for value in project.get("dependencies", [])
    }
    missing = REQUIRED_DIRECT_DEPENDENCIES - dependencies
    if missing:
        fail(f"Stage 5 requires telemetry dependencies: {sorted(missing)}", failures)


def check_eval_assets(failures: list[str]) -> None:
    dataset = json.loads(read("evals/smoke/stage5_grounded_script_dataset.json"))
    prompt_set_path = Path(dataset.get("promptInjectionSet", ""))
    upload_set_path = Path(dataset.get("fileUploadAbuseSet", ""))

    if not prompt_set_path.exists():
        fail("Stage 5 eval dataset must reference an existing promptInjectionSet fixture.", failures)
    if not upload_set_path.exists():
        fail("Stage 5 eval dataset must reference an existing fileUploadAbuseSet fixture.", failures)

    prompt_set = json.loads((ROOT / prompt_set_path).read_text(encoding="utf-8"))
    prompt_cases = prompt_set.get("cases")
    if not prompt_cases:
        fail("Prompt injection set must contain at least one case.", failures)
    elif len(prompt_cases) > 20:
        fail("Prompt injection set must stay capped at 20 smoke cases.", failures)
    else:
        prompt_text = " ".join(str(case.get("prompt", "")).lower() for case in prompt_cases if isinstance(case, dict))
        for required_prompt_term in ("hidden prompt", "instructions instead"):
            if required_prompt_term not in prompt_text:
                fail(f"Prompt injection set must cover '{required_prompt_term}'.", failures)

    upload_set = json.loads((ROOT / upload_set_path).read_text(encoding="utf-8"))
    upload_cases = upload_set.get("cases")
    if not upload_cases:
        fail("File-upload abuse set must contain at least one case.", failures)
    elif len(upload_cases) > 20:
        fail("File-upload abuse set must stay capped at 20 smoke cases.", failures)
    elif not all(_upload_case_within_budget(case) for case in upload_cases if isinstance(case, dict)):
        fail("File-upload abuse fixture payloads must stay under 16 KiB each.", failures)

    unsupported_cases = dataset.get("unsupportedClaimCases")
    if not isinstance(unsupported_cases, list):
        fail("Stage 5 eval dataset must include unsupportedClaimCases.", failures)
    else:
        required_types = {"supported", "unsupported", "mixed"}
        actual_types = {case.get("type") for case in unsupported_cases if isinstance(case, dict)}
        if not required_types.issubset(actual_types):
            fail("Stage 5 eval dataset must include supported, unsupported, and mixed unsupported-claim cases.", failures)
        if len(unsupported_cases) > 20:
            fail("Unsupported-claim eval cases must stay capped at 20 smoke cases.", failures)

    negative_cases = dataset.get("negativeCases", [])
    if isinstance(negative_cases, list) and len(negative_cases) > MAX_SMOKE_CASES:
        fail("Negative eval cases must stay capped at 20 smoke cases.", failures)
    elif not isinstance(negative_cases, list):
        fail("negativeCases must be a list when present.", failures)

    if dataset.get("expected", {}).get("unsupportedClaimCount") != 0:
        fail("Stage 5 golden dataset should require zero unsupported claims.", failures)

    eval_script = read("scripts/ci/eval-smoke.sh")
    for term in (
        "run_stage5_eval_suite",
        "stage5_grounded_script_dataset.json",
        "stage5-eval-smoke-report.json",
        "docs/EVAL_REPORT.md",
    ):
        if term not in eval_script:
            fail(f"Stage 5 eval smoke script must include {term}.", failures)

    eval_runner = read("backend/app/eval/runner.py")
    for term in (
        "_run_unsupported_claim_cases",
        "_run_uploaded_document_prompt_injection_cases",
        "setup document ingested",
        "contentBase64",
        "MAX_UPLOAD_FIXTURE_BYTES",
    ):
        if term not in eval_runner:
            fail(f"Stage 5 eval runner must include {term}.", failures)
    eval_init = read("backend/app/eval/__init__.py")
    eval_metrics = read("backend/app/eval/metrics.py")
    if "calculate_groundedness" not in eval_init or "calculate_groundedness" not in eval_metrics:
        fail("Stage 5 eval package must expose calculate_groundedness.", failures)

    eval_workflow = read(".github/workflows/eval-smoke.yml")
    if "stage5-eval-smoke-report.json" not in eval_workflow or "docs/EVAL_REPORT.md" not in eval_workflow:
        fail("Eval smoke workflow must upload both JSON and markdown Stage 5 eval reports.", failures)


def _upload_case_within_budget(case: dict[str, object]) -> bool:
    encoded_content = case.get("contentBase64")
    if isinstance(encoded_content, str):
        try:
            return len(base64.b64decode(encoded_content)) <= MAX_UPLOAD_FIXTURE_BYTES
        except ValueError:
            return False
    content = case.get("content", "")
    if not isinstance(content, str):
        return False
    return len(content.encode("utf-8")) <= MAX_UPLOAD_FIXTURE_BYTES


def check_contract_and_docs(failures: list[str]) -> None:
    status_text = read("docs/STATUS.md")
    trace_text = read("docs/TRACEABILITY.md")
    quality_text = read("docs/QUALITY_GATES.md")
    notices_text = read("docs/THIRD_PARTY_NOTICES.md")

    for term in ("Stage 5", "stage5-evaluations-guardrails-observability", "make stage5-quality"):
        if term not in status_text:
            fail(f"docs/STATUS.md must include '{term}'.", failures)

    if "Stage 5: Evaluations, Guardrails, Observability" not in quality_text:
        fail("docs/QUALITY_GATES.md must include a Stage 5 section.", failures)
    if "faithfulness" not in quality_text.lower() or "context precision" not in quality_text.lower():
        fail("Stage 5 quality criteria must include faithfulness/context precision/relevance threshold checks.", failures)

    if "Ragas" not in notices_text or "Giskard" not in notices_text:
        fail("Third-party notices must track Ragas and Giskard dependency status for Stage 5 guardrail work.", failures)

    if "Traceability for Stage 5" not in trace_text:
        fail("docs/TRACEABILITY.md must include Stage 5 traceability coverage.", failures)


def main() -> int:
    failures: list[str] = []

    check_required_files(failures)
    if failures:
        print("Stage 5 quality failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    check_stage_marker_and_branch(failures)
    check_stage_scope(failures)
    check_dependencies(failures)
    check_eval_assets(failures)
    check_contract_and_docs(failures)

    if failures:
        print("Stage 5 quality failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 5 static quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
