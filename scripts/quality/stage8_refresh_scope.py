"""Manifest-bound scope proof for dependency/container hardening; no acceptance grant."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts.governance_preflight_v1 import validate_governance_preflight

REFRESH_BRANCH = re.compile(r"^stage8-(\d+)-dependency-container-refresh$")
REFRESH_HARDENING_PATHS = set(
    """pyproject.toml uv.lock backend/Dockerfile
scripts/quality/stage8_backend_security.py scripts/ci/backend-image-package-check.sh
scripts/ci/check_semgrep_security.py scripts/quality/check_stage8_docs.py
 tests/unit/test_backend_image_package_check.py tests/unit/test_cpython_security_backports.py
 tests/unit/test_stage8_backend_security.py tests/unit/test_stage8_dependency_refresh_scope.py
 scripts/quality/stage8_checkout_scope.py scripts/quality/stage8_refresh_scope.py
 tests/unit/test_dependency_security_contract.py tests/unit/test_dependency_refresh.py
 docs/security/DEPENDENCY_REFRESH.json docs/ADR/INDEX.md docs/STATUS.md docs/TRACEABILITY.md
 docs/documentation-catalog.json docs/README.md
 docs/THIRD_PARTY_NOTICES.md docs/QUALITY_GATES.md docs/work/registry.json
 docs/work/governance-backlog/HANDOFF.md tools/semgrep/pyproject.toml
 tools/semgrep/uv.lock tools/semgrep/reviewed-inputs.sha256
 frontend/package.json frontend/package-lock.json frontend/Dockerfile
 frontend/scripts/check-next-glob-compat.mjs frontend/scripts/frontend-security-profile.mjs
 docs/security/FRONTEND_DEPENDENCY_REFRESH.json scripts/ci/frontend_security_profile.py
 tests/unit/test_frontend_dependency_refresh.py scripts/ci/prepare_frontend_npm.mjs
 scripts/quality/stage8_node_security.py tests/unit/test_frontend_npm_preparation.py
 tests/unit/test_stage8_node_security.py scripts/ci/check_container_scan_consensus.py
 tests/unit/test_container_scan_consensus.py
 tests/unit/test_frontend_dependency_security_contract.py""".split()
)
REFRESH_HARDENING_PATHS.update(
    {
        "scripts/guardrails_check.py",
        "tests/unit/test_dependency_refresh_pr_policy.py",
        "tests/unit/test_frontend_container_runtime.py",
    }
)


def check_refresh_scope(
    branch: str,
    failures: list[str],
    root: Path,
    run: Callable[[list[str]], Any],
    changed_files: Callable[[], list[str]],
) -> None:
    """Scope/budget proof only; it does not confer hosted, security or media acceptance."""
    match = REFRESH_BRANCH.fullmatch(branch)
    assert match is not None
    issue = int(match[1])
    preflight = f"docs/governance/preflights/issue-{issue}.json"

    def git_output(*args: str) -> str:
        result = run(["git", *args])
        if result.returncode:
            raise RuntimeError("Dependency refresh Git evidence unavailable.")
        return str(result.stdout)

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate refresh manifest field.")
            result[key] = value
        return result

    try:
        artifact = json.loads(
            (root / preflight).read_text(encoding="utf-8"), object_pairs_hook=unique
        )
        changed = set(changed_files())
        findings = validate_governance_preflight(
            artifact,
            context={"issue_number": issue, "branch": branch, "changed_files": sorted(changed)},
        )
        if findings:
            raise RuntimeError(
                "Dependency refresh preflight invalid: " + ",".join(f.code for f in findings)
            )
        required = set(artifact["scope"]["required"])
        if required != set(artifact["scope"]["allowed_prefixes"]) or any(
            path not in REFRESH_HARDENING_PATHS
            and path != preflight
            and not (path.startswith("docs/ADR/") and path.endswith(".md"))
            for path in required
        ):
            raise RuntimeError("Dependency refresh exceeds the independent hardening envelope.")
        head = git_output("rev-parse", "HEAD").strip()
        event = os.environ.get("GITHUB_EVENT_NAME", "")
        hosted = bool(event) or os.environ.get("GITHUB_ACTIONS") == "true"
        if hosted:
            payload = json.loads(
                Path(os.environ["GITHUB_EVENT_PATH"]).read_text(), object_pairs_hook=unique
            )
            if event in {"pull_request", "pull_request_review"}:
                source = payload["pull_request"]["head"]["sha"]
                base = payload["pull_request"]["base"]["sha"]
                if payload["pull_request"]["head"]["ref"] != branch:
                    raise RuntimeError("Dependency refresh hosted branch mismatch.")
            elif event == "push":
                source = payload["after"]
                if payload["ref"] != "refs/heads/" + branch:
                    raise RuntimeError("Dependency refresh hosted ref mismatch.")
                base = git_output("merge-base", "origin/main", source).strip()
            else:
                raise RuntimeError("Dependency refresh hosted event missing.")
            if (
                git_output("diff", "--cached", "--name-only", "HEAD", "--").strip()
                or git_output("diff", "--name-only", "--").strip()
                or git_output("ls-files", "--others", "--exclude-standard").strip()
            ):
                raise RuntimeError("Dependency refresh hosted checkout is dirty.")
        else:
            source = head
            base = git_output("merge-base", "origin/main", source).strip()
        if not all(
            isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value)
            for value in (base, source)
        ):
            raise RuntimeError("Dependency refresh revision invalid.")
        git_output("merge-base", "--is-ancestor", base, source)
        commits = git_output(
            "rev-list", "--first-parent", "--reverse", f"{base}..{source}"
        ).splitlines()
        if not commits or git_output(
            "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commits[0]
        ).splitlines() != [preflight]:
            raise RuntimeError("Dependency refresh first commit must contain only its preflight.")
        historical = json.loads(
            git_output("show", commits[0] + ":" + preflight), object_pairs_hook=unique
        )
        if not isinstance(historical, dict) or "change_budget" not in historical:
            raise RuntimeError("Dependency refresh historical preflight invalid.")
        historical_scope = historical.get("scope")
        historical_paths = (
            historical_scope.get("required", []) if isinstance(historical_scope, dict) else []
        )
        historical_findings = validate_governance_preflight(
            historical,
            context={
                "issue_number": issue,
                "branch": branch,
                "changed_files": historical_paths,
            },
        )
        if historical_findings:
            raise RuntimeError("Dependency refresh historical preflight invalid.")
        if changed != required:
            raise RuntimeError("Dependency refresh exact changed paths do not match the manifest.")
        budget = artifact["change_budget"]
        maximum: dict[str, int] = {}
        indexed_manifest = json.loads(git_output("show", ":" + preflight), object_pairs_hook=unique)
        if indexed_manifest != artifact:
            raise RuntimeError(
                "Dependency refresh indexed manifest differs from the effective manifest."
            )
        for args in (
            ("diff", "--no-renames", "--numstat", f"{base}..{source}", "--"),
            ("diff", "--cached", "--no-renames", "--numstat", base, "--"),
            ("diff", "--no-renames", "--numstat", base, "--"),
        ):
            # Each layer is measured from the same qualified base; index cannot be hidden by working edits.
            rows = git_output(*args).splitlines()
            seen: set[str] = set()
            for row in rows:
                a, d, path = row.split("\t")
                if not a.isdigit() or not d.isdigit() or path not in required or path in seen:
                    raise RuntimeError("Dependency refresh charge evidence invalid.")
                seen.add(path)
                maximum[path] = max(maximum.get(path, 0), int(a) + int(d))
        for path in required:
            file = root / path
            if file.is_symlink() or not file.is_file():
                raise RuntimeError("Dependency refresh file type invalid.")
            raw = file.read_bytes()
            raw.decode("utf-8")
            if b"\0" in raw:
                raise RuntimeError("Dependency refresh binary content forbidden.")
            indexed = git_output("ls-files", "--stage", "--", path).splitlines()
            if indexed:
                if len(indexed) != 1 or indexed[0].split()[0] not in {"100644", "100755"}:
                    raise RuntimeError("Dependency refresh indexed file mode invalid.")
                if "\0" in git_output("show", ":" + path):
                    raise RuntimeError("Dependency refresh indexed binary forbidden.")
            if path not in maximum:
                maximum[path] = len(raw.splitlines())
            if maximum[path] > budget["per_file_charged_lines"][path]:
                raise RuntimeError("Dependency refresh per-path budget exceeded.")
        if sum(maximum.values()) > budget["maximum_additions_plus_deletions"]:
            raise RuntimeError("Dependency refresh aggregate budget exceeded.")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        failures.append(str(error))
