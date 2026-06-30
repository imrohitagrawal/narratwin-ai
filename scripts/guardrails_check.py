#!/usr/bin/env python3
"""Repository guardrails for NarraTwin AI.

This script intentionally uses only the Python standard library so CI can run
without paid providers, real API keys, or project-specific dependencies.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".chroma",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "outputs",
    ".next",
    ".venv",
    "venv",
}

TEXT_SUFFIXES = {
    ".adoc",
    ".cer",
    ".crt",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".key",
    ".md",
    ".mjs",
    ".p12",
    ".pem",
    ".pfx",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

PRIVATE_KEY_CERT_SUFFIXES = {".pem", ".key", ".crt", ".cer", ".p12", ".pfx"}

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("openai key", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openrouter key", re.compile(r"sk-or-v1-[A-Za-z0-9_\-]{20,}")),
    ("github token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("google api key", re.compile(r"AIza[0-9A-Za-z_\-]{20,}")),
    ("aws access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("jwt-like token", re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}")),
    ("bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}")),
    (
        "secret assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|credential)\b\s*[:=]\s*['\"]?([^'\"\s#]{8,})['\"]?"
        ),
    ),
]

PROVIDER_KEY_NAMES = {
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "HEYGEN_API_KEY",
    "TAVUS_API_KEY",
    "DID_API_KEY",
    "ELEVENLABS_API_KEY",
}

ARCHITECTURE_IMPACT_PREFIXES = (
    "src/",
    "app/",
    "backend/",
    "frontend/",
    "infra/",
    "terraform/",
    "docker/",
    "docs/ARCHITECTURE.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/THREAT_MODEL.md",
)

PRD_IMPACT_PREFIXES = (
    "src/",
    "app/",
    "backend/",
    "frontend/",
    "docs/PRD.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/ROADMAP.md",
)

STATUS_IMPACT_PREFIXES = (
    ".github/pull_request_template.md",
    ".github/workflows/",
    ".stage/current",
    "AGENTS.md",
    "Makefile",
    "docs/ADR/",
    "docs/AI_BUILD_BRIEF.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/DATA_MODEL.md",
    "docs/METHODOLOGY.md",
    "docs/NORTH_STAR_METRICS.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/PRD.md",
    "docs/PRD_RED_TEAM_REVIEW.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/PROJECT_AVATAR_PACK.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/RELEASE_QUALITY_BAR.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/ROADMAP.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/quality/",
)

CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}

failures: list[str] = []
warnings: list[str] = []


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def is_zero_sha(value: str) -> bool:
    return bool(value) and set(value) == {"0"}


def resolve_diff_base(head: str, preferred_base: str) -> str:
    if preferred_base and not is_zero_sha(preferred_base):
        verified = run_git(["rev-parse", "--verify", f"{preferred_base}^{{commit}}"])
        if verified:
            merge_base = run_git(["merge-base", preferred_base, head])
            if merge_base:
                return merge_base
    for candidate in ("origin/main", "main"):
        merge_base = run_git(["merge-base", candidate, head])
        if merge_base:
            return merge_base
    return "HEAD~1"


def changed_files() -> list[str]:
    base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    head = os.environ.get("GITHUB_HEAD_SHA", "").strip() or "HEAD"
    resolved_base = resolve_diff_base(head, base)
    output = run_git(["diff", "--name-only", resolved_base, head])
    return [line.strip() for line in output.splitlines() if line.strip()]


def iter_text_files() -> list[Path]:
    tracked = run_git(["ls-files"])
    untracked = run_git(["ls-files", "--others", "--exclude-standard"])
    files: list[Path] = []
    for rel in sorted({line.strip() for output in (tracked, untracked) for line in output.splitlines()}):
        if not rel:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & EXCLUDED_DIRS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "Makefile", ".env.example"}:
            files.append(path)
    return files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def line_for_match(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def is_allowlisted_secret_match(path: str, text: str, match: re.Match[str]) -> bool:
    matched_text = match.group(0)
    if path.endswith(".env.example") and matched_text.endswith("="):
        return True
    if path.endswith(".env.example") and re.search(r"=\s*['\"]?\s*['\"]?$", matched_text):
        return True
    if "PLACEHOLDER" in matched_text or "example" in matched_text.lower():
        return True
    line = line_for_match(text, match)
    if path in {"scripts/guardrails_check.py", "scripts/quality/check_stage2_docs.py"}:
        if "re.compile" in line or "SECRET_PATTERNS" in line or "PROVIDER_KEY_NAMES" in line:
            return True
        if "expected_defaults" in line or "providerDefaults" in line:
            return True
    return False


def check_no_direct_main_push() -> None:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref = os.environ.get("GITHUB_REF_NAME", "")
    if event == "push" and ref == "main":
        failures.append("Direct push to main detected. All work must go through issue + branch + PR.")


def check_issue_linked_pull_request() -> None:
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        failures.append("Pull request event payload is unavailable; cannot verify issue linkage.")
        return
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"Could not read pull request event payload: {exc}")
        return
    pr = event.get("pull_request", {})
    body = pr.get("body") or ""
    head_ref = (pr.get("head") or {}).get("ref")
    base_ref = (pr.get("base") or {}).get("ref")
    if head_ref == "main":
        failures.append("Pull request head branch must not be main.")
    if base_ref != "main":
        failures.append("Pull requests for guarded work must target main.")
    if not re.search(r"(?i)(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#\d+", body):
        failures.append("Pull request body must link an issue using Closes #<issue>, Fixes #<issue>, or Resolves #<issue>.")
    canonical_stage_issues = {
        "stage2-": ("Stage 2", "2"),
        "stage3-": ("Stage 3", "5"),
    }
    for branch_prefix, (stage_name, issue_number) in canonical_stage_issues.items():
        if head_ref and head_ref.startswith(branch_prefix):
            pattern = rf"(?i)(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{issue_number}\b"
            if not re.search(pattern, body):
                failures.append(
                    f"{stage_name} pull requests must close the canonical {stage_name} issue using "
                    f"Closes #{issue_number}, Fixes #{issue_number}, or Resolves #{issue_number}."
                )


def check_workflows_least_privilege() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.exists():
        failures.append("Missing .github/workflows directory. CI must be YAML-defined.")
        return
    for workflow in list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")):
        text = read_text(workflow)
        rel = relative(workflow)
        if "permissions:" not in text:
            failures.append(f"{rel} is missing explicit least-privilege permissions.")
        if re.search(r"permissions:\s*write-all", text):
            failures.append(f"{rel} uses write-all permissions. Use least privilege instead.")
        if re.search(r"contents:\s*write", text) and "pull_request" in text:
            failures.append(f"{rel} grants contents: write for PR validation. Use contents: read unless a write is required.")


def check_secrets() -> None:
    for path in iter_text_files():
        rel = relative(path)
        if path.suffix.lower() in PRIVATE_KEY_CERT_SUFFIXES:
            failures.append(f"{rel} is a key/certificate file. Private keys and certificates must not be committed.")
            continue
        text = read_text(path)
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if is_allowlisted_secret_match(rel, text, match):
                    continue
                failures.append(f"Potential {name} found in {rel}. No secrets may be committed.")


def check_provider_keys_are_env_only() -> None:
    env_example = ROOT / ".env.example"
    if not env_example.exists():
        failures.append("Missing .env.example. Provider keys must be documented as environment variables.")
        return
    env_text = read_text(env_example)
    for key in sorted(PROVIDER_KEY_NAMES):
        if key not in env_text:
            failures.append(f"Missing {key} placeholder in .env.example.")
    for path in iter_text_files():
        rel = relative(path)
        text = read_text(path)
        if rel.endswith(".env.example"):
            continue
        for key_name in PROVIDER_KEY_NAMES:
            assignment = re.compile(rf"{re.escape(key_name)}\s*=\s*['\"]?[^'\"\n#]+")
            for match in assignment.finditer(text):
                if is_allowlisted_secret_match(rel, text, match):
                    continue
                failures.append(f"{rel} appears to assign {key_name}. Provider keys must come from environment variables.")


def check_mock_local_defaults() -> None:
    env_example = ROOT / ".env.example"
    text = read_text(env_example) if env_example.exists() else ""
    expected_defaults = {
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
    }
    for default in sorted(expected_defaults):
        if default not in text:
            failures.append(f".env.example must include free/local test default: {default}")


def check_traceability_rules(changes: list[str]) -> None:
    if not changes:
        return
    changed_set = set(changes)
    architecture_changed = any(change.startswith(ARCHITECTURE_IMPACT_PREFIXES) for change in changes)
    adr_updated = any(change.startswith("docs/ADR/") for change in changes)
    if architecture_changed and not adr_updated:
        failures.append("Architecture-impacting changes require an ADR update under docs/ADR/.")

    prd_changed = any(change.startswith(PRD_IMPACT_PREFIXES) for change in changes)
    traceability_updated = "docs/TRACEABILITY.md" in changed_set
    if prd_changed and not traceability_updated:
        failures.append("PRD-impacting changes require docs/TRACEABILITY.md to be updated.")


def check_status_tracking_rules(changes: list[str]) -> None:
    if not changes:
        return
    changed_set = set(changes)
    status_updated = "docs/STATUS.md" in changed_set
    status_impacted = any(change.startswith(STATUS_IMPACT_PREFIXES) for change in changes)
    if status_impacted and not status_updated:
        failures.append("Repository-tracked stage/governance changes require docs/STATUS.md to be updated.")


def check_llm_tracing_and_citations() -> None:
    for path in iter_text_files():
        rel = relative(path)
        if path.suffix.lower() not in CODE_SUFFIXES:
            continue
        if rel == "scripts/guardrails_check.py" or rel.startswith("scripts/quality/"):
            continue
        text = read_text(path).lower()
        if any(term in text for term in ["llm", "generate_script", "walkthrough script", "generated_script"]):
            if "trace" not in text and "run_id" not in text:
                failures.append(f"{rel} appears to generate/use LLM output without trace/run_id metadata.")
            if any(term in text for term in ["script", "walkthrough", "answer"]):
                if "source_chunk" not in text and "citation" not in text and "context_id" not in text:
                    failures.append(f"{rel} appears to generate scripts/answers without source chunk citations.")


def check_eval_results_blocking() -> None:
    candidate_paths = [ROOT / "reports" / "eval-results.json", ROOT / "eval-results.json"]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except json.JSONDecodeError:
            failures.append(f"{relative(path)} is not valid JSON.")
            continue
        status = str(data.get("status", data.get("result", ""))).lower()
        failures_found = data.get("failures", [])
        if status in {"fail", "failed", "error"} or failures_found:
            failures.append(f"Evaluation failures found in {relative(path)}. Eval failures block merge.")


def check_security_results_blocking() -> None:
    candidate_paths = [ROOT / "reports" / "security-results.json", ROOT / "security-results.json"]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except json.JSONDecodeError:
            failures.append(f"{relative(path)} is not valid JSON.")
            continue
        findings = data.get("findings", data if isinstance(data, list) else [])
        for finding in findings:
            severity = str(finding.get("severity", "")).lower() if isinstance(finding, dict) else ""
            if severity in {"critical", "high"}:
                failures.append(f"Security {severity} finding found in {relative(path)}. Critical/high findings block merge.")


def main() -> int:
    changes = changed_files()
    check_no_direct_main_push()
    check_issue_linked_pull_request()
    check_workflows_least_privilege()
    check_secrets()
    check_provider_keys_are_env_only()
    check_mock_local_defaults()
    check_traceability_rules(changes)
    check_status_tracking_rules(changes)
    check_llm_tracing_and_citations()
    check_eval_results_blocking()
    check_security_results_blocking()

    if warnings:
        print("Guardrail warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if failures:
        print("Guardrail failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("All NarraTwin AI repository guardrails passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
