#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

mkdir -p reports/eval-smoke

REPORT_JSON="reports/eval-smoke/stage5-eval-smoke-report.json"
REPORT_MARKDOWN="docs/EVAL_REPORT.md"

uv run python - <<'PY'
import json
from pathlib import Path

from backend.app.eval.runner import run_stage5_eval_suite, to_markdown

fixture_path = Path("evals/smoke/stage5_grounded_script_dataset.json")
report = run_stage5_eval_suite(fixture_path=fixture_path)

report_json_path = Path("reports/eval-smoke/stage5-eval-smoke-report.json")
report_json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

markdown = to_markdown(report)
Path("docs/EVAL_REPORT.md").write_text(markdown, encoding="utf-8")

if not report.get("passed"):
    raise SystemExit(f"eval smoke failed; report written to {report_json_path}")

print(f"eval smoke report written to {report_json_path}")
print("eval smoke report written to docs/EVAL_REPORT.md")
PY
