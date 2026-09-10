from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO = Path(__file__).parents[2]
WORKFLOW = REPO / ".github/workflows/ci.yml"
STATUS = REPO / "docs/STATUS.md"
TRACEABILITY = REPO / "docs/TRACEABILITY.md"
EXPECTED_TIMEOUTS = {
    "backend": 30,
    "frontend": 20,
    "docker": 20,
    "stage8-budgets": 35,
}

TIMEOUT_EVIDENCE = (
    ("34282990946", "102251927718", "15m18"),
    ("34252374484", "102149655021", "15m14"),
)
STALE_TIMEOUT_EVIDENCE = "34410932324"


def _job_blocks(workflow: str) -> dict[str, str]:
    lines = workflow.splitlines(keepends=True)
    jobs_index = next(
        (index for index, line in enumerate(lines) if line.rstrip("\n") == "jobs:"),
        None,
    )
    assert jobs_index is not None, "ci.yml must contain a top-level jobs mapping"

    headers: list[tuple[int, str]] = []
    for index in range(jobs_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line.startswith((" ", "#")):
            break
        match = re.match(r"  ([a-z0-9][a-z0-9_-]*):\s*\n?\Z", line)
        if match:
            headers.append((index, match.group(1)))

    names = [name for _index, name in headers]
    assert len(names) == len(set(names)), "ci.yml must not repeat a job identifier"
    blocks: dict[str, str] = {}
    for position, (start, name) in enumerate(headers):
        end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        blocks[name] = "".join(lines[start:end])
    return blocks


def _assert_timeout_policy(workflow: str) -> None:
    blocks = _job_blocks(workflow)
    for job, expected in EXPECTED_TIMEOUTS.items():
        assert job in blocks, f"ci.yml must retain the {job} job"
        values = re.findall(r"(?m)^    timeout-minutes:\s*(.*?)\s*$", blocks[job])
        assert len(values) == 1, f"{job} must declare exactly one job-level timeout"
        assert re.match(r"[0-9]+\Z", values[0]), f"{job} timeout must be numeric"
        assert int(values[0]) == expected, f"{job} timeout must remain {expected} minutes"


def test_ci_workflow_has_exact_finite_job_timeout_policy() -> None:
    _assert_timeout_policy(WORKFLOW.read_text(encoding="utf-8"))


def test_issue_527_docs_bind_timeout_claim_to_elapsed_ceiling_jobs() -> None:
    for path in (STATUS, TRACEABILITY):
        issue_527 = path.read_text(encoding="utf-8").split(
            "## Issue #527 backend CI timeout", maxsplit=1
        )[1]
        assert STALE_TIMEOUT_EVIDENCE not in issue_527
        for run_id, job_id, elapsed in TIMEOUT_EVIDENCE:
            assert run_id in issue_527
            assert job_id in issue_527
            assert elapsed in issue_527


@pytest.mark.parametrize(
    ("replacement", "count"),
    [
        ("", 1),
        ("    timeout-minutes: 30\n    timeout-minutes: 30", 1),
        ("    timeout-minutes: thirty", 1),
        ("    timeout-minutes: 29", 1),
        ("    timeout-minutes: 31", 1),
        ("      timeout-minutes: 30", 1),
    ],
    ids=["missing", "duplicate", "non-numeric", "lower", "higher", "misplaced"],
)
def test_backend_timeout_policy_rejects_ambiguous_or_drifted_values(
    replacement: str,
    count: int,
) -> None:
    accepted = WORKFLOW.read_text(encoding="utf-8").replace(
        "    timeout-minutes: 15",
        "    timeout-minutes: 30",
        1,
    )
    mutated = accepted.replace("    timeout-minutes: 30", replacement, count)
    with pytest.raises(AssertionError):
        _assert_timeout_policy(mutated)
