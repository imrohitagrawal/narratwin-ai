#!/usr/bin/env python3
"""Dispatch the top-level quality command to the current stage gate."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT_STAGE = ROOT / ".stage" / "current"
FINAL_REVIEW_BRANCH_PREFIX = "final-review-"


def current_branch() -> str:
    env_branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if env_branch:
        return env_branch
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def run_recommended_review_item_check(stage: str) -> int:
    return subprocess.call(
        [sys.executable, "scripts/quality/check_recommended_review_items.py", stage],
        cwd=ROOT,
    )


def main() -> int:
    if not CURRENT_STAGE.exists():
        print("Missing .stage/current. Cannot determine quality stage.")
        return 1

    stage = CURRENT_STAGE.read_text(encoding="utf-8").strip()
    branch = current_branch()
    if branch.startswith(FINAL_REVIEW_BRANCH_PREFIX):
        stage = "Final Review"

    recommendation_status = run_recommended_review_item_check(stage)
    if recommendation_status != 0:
        return recommendation_status

    if stage == "0":
        return subprocess.call([sys.executable, "scripts/quality/check_stage0_docs.py"], cwd=ROOT)
    if stage == "1":
        return subprocess.call([sys.executable, "scripts/quality/check_stage1_docs.py"], cwd=ROOT)
    if stage == "2":
        return subprocess.call([sys.executable, "scripts/quality/check_stage2_docs.py"], cwd=ROOT)
    if stage == "3":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage3_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage3-quality"], cwd=ROOT)
    if stage == "4":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage4_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage4-quality"], cwd=ROOT)
    if stage == "5":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage5_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage5-quality"], cwd=ROOT)
    if stage == "6":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage6_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage6-quality"], cwd=ROOT)
    if stage == "7":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage7_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage7-quality"], cwd=ROOT)
    if stage == "8":
        if os.environ.get("NARRATWIN_POLICY_ONLY") == "1":
            return subprocess.call([sys.executable, "scripts/quality/check_stage8_docs.py"], cwd=ROOT)
        return subprocess.call(["make", "stage8-quality"], cwd=ROOT)
    if stage == "Final Review":
        return subprocess.call([sys.executable, "scripts/quality/check_final_review_docs.py"], cwd=ROOT)

    return subprocess.call(
        [sys.executable, "scripts/quality/stage_not_implemented.py", f"Stage {stage}"],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
