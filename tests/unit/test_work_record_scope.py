"""Git-backed W1-W5 cases; removing scope/envelope/budget/history checks turns these red."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

BRANCH = "phase-1-closure-process-777-records"
PREFLIGHT = "docs/governance/preflights/issue-777.json"
RECORD = "docs/work/example/PLAN.md"
KERNEL = {
    "scripts/quality/work_record_scope.py",
    "scripts/quality/phase1_closure/legacy.py",
    "tests/unit/test_work_record_scope.py",
    "tests/unit/phase1_closure/test_legacy.py",
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def put(root: Path, name: str, body: str) -> None:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: Any) -> Path:
    for name in (
        "GITHUB_ACTIONS",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_HEAD_SHA",
        "GITHUB_HEAD_REF",
        "GITHUB_BASE_SHA",
        "GITHUB_REF_NAME",
    ):
        monkeypatch.delenv(name, raising=False)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    put(tmp_path, "scripts/governance_preflight_repository.py", "# adapter exists\n")
    put(tmp_path, "scripts/quality/work_record_scope.py", "# installed kernel\n")
    put(tmp_path, "docs/STATUS.md", "old\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(tmp_path, "checkout", "-qb", BRANCH)
    return tmp_path


def manifest(paths: set[str] | None = None) -> dict[str, Any]:
    paths = paths or {PREFLIGHT, RECORD, "docs/STATUS.md"}
    return dict(
        schema_version="GovernancePreflightV1",
        issue_number=777,
        branch=BRANCH,
        objective="Governed work-record fixture with no provider authority.",
        status_decision="update-minimally",
        change_budget=dict(
            exact_paths=len(paths),
            maximum_additions_plus_deletions=2000,
            deletions_grant_credit=False,
            per_file_charged_lines={p: 1000 for p in paths},
        ),
        scope=dict(required=sorted(paths), allowed_prefixes=sorted(paths), forbidden=[]),
    )


def candidate(
    root: Path, data: dict[str, Any] | None = None, *, commit: bool = True
) -> dict[str, Any]:
    data = data or manifest()
    put(root, PREFLIGHT, json.dumps(data, indent=2) + "\n")
    git(root, "add", PREFLIGHT)
    git(root, "commit", "-qm", "preflight")
    for path in data["scope"]["required"]:
        if path != PREFLIGHT:
            put(root, path, "reviewed changed content\n")
    if commit:
        git(root, "add", ".")
        git(root, "commit", "-qm", "records")
    return data


def check(root: Path) -> list[str] | None:
    from scripts.quality.work_record_scope import scope_findings

    return scope_findings(root, BRANCH)


def test_real_document_record_passes_and_old_boundary_rejects(
    repository: Path, monkeypatch: Any
) -> None:
    candidate(repository)
    from scripts.quality import check_phase1_closure_docs as frozen

    monkeypatch.setattr(frozen, "current_branch", lambda: BRANCH)
    monkeypatch.setattr(frozen, "changed_files", lambda: [RECORD])
    old: list[str] = []
    frozen.check_changed_files(old)
    assert len(old) == 1 and RECORD in old[0]
    assert check(repository) == []


@pytest.mark.parametrize(
    "path",
    [
        "backend/app/main.py",
        "frontend/app/page.tsx",
        ".github/workflows/test.yml",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/phase1_closure/legacy.py",
        "scripts/guardrails_check.py",
    ],
)
def test_coherent_manifest_cannot_authorize_runtime_or_installed_kernel(
    repository: Path, path: str
) -> None:
    candidate(repository, manifest({PREFLIGHT, RECORD, "docs/STATUS.md", path}))
    assert check(repository)


@pytest.mark.parametrize(
    "mutation",
    ["missing_budget", "credit", "aggregate", "perpath", "prefix", "wrong_issue", "wrong_branch"],
)
def test_exact_contract_and_measured_budgets(repository: Path, mutation: str) -> None:
    data = manifest()
    if mutation == "missing_budget":
        data.pop("change_budget")
    elif mutation == "credit":
        data["change_budget"]["deletions_grant_credit"] = True
    elif mutation == "aggregate":
        data["change_budget"]["maximum_additions_plus_deletions"] = 300
        data["change_budget"]["per_file_charged_lines"] = {
            p: 300 for p in data["scope"]["required"]
        }
    elif mutation == "perpath":
        data["change_budget"]["per_file_charged_lines"][RECORD] = 1
    elif mutation == "prefix":
        data["scope"]["allowed_prefixes"] = ["docs/"]
    elif mutation == "wrong_issue":
        data["issue_number"] = 778
    else:
        data["branch"] = BRANCH + "-other"
    candidate(repository, data)
    if mutation == "perpath":
        put(repository, RECORD, "one\ntwo\n")
    elif mutation == "aggregate":
        put(repository, RECORD, "line\n" * 270)
        put(repository, "docs/STATUS.md", "changed\n" * 70)
    assert check(repository)


@pytest.mark.parametrize("mode", ["missing", "mixed_first", "foreign", "multiple"])
def test_preflight_history_is_mandatory(repository: Path, mode: str) -> None:
    if mode == "missing":
        put(repository, RECORD, "content\n")
        git(repository, "add", ".")
        git(repository, "commit", "-qm", "no preflight")
    elif mode == "mixed_first":
        put(repository, RECORD, "early\n")
        git(repository, "add", RECORD)
        candidate(repository)
        # An earlier non-preflight commit makes first-preflight history false.
        first = git(repository, "rev-list", "--reverse", "origin/main..HEAD").splitlines()[0]
        assert first
        git(repository, "checkout", "-q", "origin/main", "--", "docs/STATUS.md")
        put(repository, "docs/work/example/early.md", "extra\n")
        # The staged record before the first preflight commit is retained in its index.
    else:
        candidate(repository)
        other = "docs/governance/preflights/issue-778.json"
        put(repository, other, json.dumps(manifest()))
        if mode == "foreign":
            (repository / PREFLIGHT).unlink()
        git(repository, "add", ".")
        git(repository, "commit", "-qm", "bad history")
    assert check(repository)


def test_dirty_local_docs_checked_but_dirty_hosted_rejected(
    repository: Path, monkeypatch: Any, tmp_path: Path
) -> None:
    candidate(repository, commit=False)
    assert check(repository) == []
    event = tmp_path.parent / (tmp_path.name + "-event.json")
    event.write_text(
        json.dumps(dict(after=git(repository, "rev-parse", "HEAD"), ref="refs/heads/" + BRANCH))
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert check(repository)


@pytest.mark.parametrize("kind", ["extra", "binary", "symlink", "invalid_utf8", "mode"])
def test_unsafe_working_files_fail_closed(repository: Path, kind: str) -> None:
    candidate(repository)
    p = repository / RECORD
    if kind == "extra":
        put(repository, "docs/work/extra.md", "new\n")
    elif kind == "binary":
        p.write_bytes(b"x\x00y")
    elif kind == "symlink":
        p.unlink()
        p.symlink_to(repository / "docs/STATUS.md")
    elif kind == "invalid_utf8":
        p.write_bytes(b"\xff")
    else:
        p.chmod(0o755)
    assert check(repository)


def test_committed_extra_cannot_be_hidden_by_working_deletion(repository: Path) -> None:
    candidate(repository)
    p = "docs/work/undeclared.md"
    put(repository, p, "bad\n")
    git(repository, "add", ".")
    git(repository, "commit", "-qm", "extra")
    (repository / p).unlink()
    assert check(repository)


def test_complete_kernel_install_only_on_uninstalled_base(repository: Path) -> None:
    git(repository, "checkout", "-q", "main")
    (repository / "scripts/quality/work_record_scope.py").unlink()
    git(repository, "add", ".")
    git(repository, "commit", "-qm", "uninstalled base")
    git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repository, "checkout", "-q", BRANCH)
    git(repository, "merge", "-q", "--ff-only", "main")
    candidate(repository, manifest({PREFLIGHT, RECORD, "docs/STATUS.md"} | KERNEL))
    assert check(repository) == []


def test_complete_kernel_forbidden_on_installed_base(repository: Path) -> None:
    candidate(repository, manifest({PREFLIGHT, RECORD, "docs/STATUS.md"} | KERNEL))
    assert check(repository)


@pytest.mark.parametrize("event_kind", ["push", "pull_request", "pull_request_review"])
def test_clean_detached_direct_head_and_merge_checkout(
    repository: Path, monkeypatch: Any, tmp_path: Path, event_kind: str
) -> None:
    candidate(repository)
    head, base = git(repository, "rev-parse", "HEAD"), git(repository, "rev-parse", "origin/main")
    event = (
        dict(after=head, before="0" * 40, ref="refs/heads/" + BRANCH)
        if event_kind == "push"
        else dict(
            pull_request=dict(head=dict(sha=head, ref=BRANCH), base=dict(sha=base, ref="main"))
        )
    )
    p = tmp_path.parent / (tmp_path.name + "-event.json")
    p.write_text(json.dumps(event))
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_kind)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(p))
    monkeypatch.setenv("GITHUB_HEAD_REF", BRANCH)
    git(repository, "checkout", "-q", "--detach", head)
    assert check(repository) == []
    if event_kind != "push":
        tree = git(repository, "rev-parse", head + "^{tree}")
        merge = git(repository, "commit-tree", tree, "-p", base, "-p", head, "-m", "merge checkout")
        git(repository, "checkout", "-q", "--detach", merge)
        assert check(repository) == []
        p.write_text(
            json.dumps(
                dict(pull_request=dict(head=dict(sha=base, ref=BRANCH), base=dict(sha=base)))
            )
        )
        assert check(repository)


def test_missing_origin_and_legacy_branch_do_not_grant_scope(repository: Path) -> None:
    candidate(repository)
    git(repository, "update-ref", "-d", "refs/remotes/origin/main")
    assert check(repository)
    from scripts.quality.work_record_scope import scope_findings

    assert scope_findings(repository, "main") is None


def test_staged_extra_masked_in_working_tree_is_rejected(repository: Path) -> None:
    candidate(repository)
    path = "backend/hidden.py"
    put(repository, path, "unauthorized\n")
    git(repository, "add", path)
    (repository / path).unlink()
    assert check(repository)


def test_staged_overrun_trimmed_in_working_tree_is_rejected(repository: Path) -> None:
    data = manifest()
    data["change_budget"]["per_file_charged_lines"][RECORD] = 1
    candidate(repository, data)
    put(repository, RECORD, "one\ntwo\n")
    git(repository, "add", RECORD)
    put(repository, RECORD, "reviewed changed content\n")
    assert check(repository)


def test_hosted_marker_without_event_packet_fails(repository: Path, monkeypatch: Any) -> None:
    candidate(repository, commit=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert check(repository)


def test_hosted_staged_divergence_cannot_hide_in_clean_worktree(
    repository: Path, monkeypatch: Any
) -> None:
    candidate(repository)
    head = git(repository, "rev-parse", "HEAD")
    event = repository.parent / (repository.name + "-push.json")
    event.write_text(json.dumps(dict(after=head, ref="refs/heads/" + BRANCH)))
    put(repository, RECORD, "staged change\n")
    git(repository, "add", RECORD)
    put(repository, RECORD, "reviewed changed content\n")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert check(repository)


def test_pr_applicability_uses_event_base_not_newer_main(
    repository: Path, monkeypatch: Any
) -> None:
    base = git(repository, "rev-parse", "origin/main")
    put(repository, "docs/STATUS.md", "legacy-only change\n")
    git(repository, "add", ".")
    git(repository, "commit", "-qm", "legacy")
    head = git(repository, "rev-parse", "HEAD")
    git(repository, "checkout", "-q", "main")
    put(repository, "docs/work/elsewhere/PLAN.md", "later main change\n")
    git(repository, "add", ".")
    git(repository, "commit", "-qm", "later main")
    git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(repository, "checkout", "-q", BRANCH)
    event = repository.parent / (repository.name + "-pr.json")
    event.write_text(
        json.dumps(dict(pull_request=dict(head=dict(sha=head, ref=BRANCH), base=dict(sha=base))))
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert check(repository) is None
