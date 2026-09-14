"""Regression coverage for issue535 measured scope, not product behavior."""
import copy
import unittest
from scripts.quality.work_archive_scope import budget_failures


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.paths = ["docs/STATUS.md", "docs/governance/preflights/issue-535.json"]
        self.preflight = {
            "schema_version": "GovernancePreflightV1", "issue_number": 535,
            "branch": "phase-1-closure-process-535-work-archive", "objective": "Test archive scope",
            "status_decision": "update-minimally",
            "scope": {"required": self.paths, "allowed_prefixes": self.paths, "forbidden": ["backend/", "docs/work-archive/.restricted/"]},
            "change_budget": {"exact_paths": 2, "maximum_additions_plus_deletions": 8,
                              "deletions_grant_credit": False,
                              "per_file_charged_lines": dict.fromkeys(self.paths, 5)},
        }
        self.branch = self.preflight["branch"]
        self.charges = dict.fromkeys(self.paths, 4)

    def test_exact_scope_and_caps_pass(self):
        self.assertEqual(budget_failures(self.preflight, self.charges, self.branch), [])

    def test_missing_extra_and_private_paths_fail(self):
        for changes in [{self.paths[0]: 4}, {**self.charges, "backend/new.py": 1},
                        {**self.charges, "docs/work-archive/.restricted/raw.txt": 1}]:
            with self.subTest(changes=changes):
                self.assertTrue(budget_failures(self.preflight, changes, self.branch))

    def test_deletions_are_charged_and_aggregate_is_enforced(self):
        self.assertTrue(budget_failures(self.preflight, dict.fromkeys(self.paths, 5), self.branch))
        self.assertTrue(budget_failures(self.preflight, {self.paths[0]: 6, self.paths[1]: 1}, self.branch))

    def test_wrong_branch_and_mutated_policy_fail(self):
        self.assertTrue(budget_failures(self.preflight, self.charges, self.branch + "-lookalike"))
        for key, value in [("deletions_grant_credit", True), ("exact_paths", True),
                           ("maximum_additions_plus_deletions", 0)]:
            bad = copy.deepcopy(self.preflight)
            bad["change_budget"][key] = value
            self.assertTrue(budget_failures(bad, self.charges, self.branch))

    def test_invalid_charges_fail_closed(self):
        for value in [None, -1, True, "3"]:
            with self.subTest(value=value):
                self.assertTrue(budget_failures(self.preflight, {self.paths[0]: value, self.paths[1]: 1}, self.branch))


class PreservedRouteTests(unittest.TestCase):
    def test_archive_route_preserves_all_legacy_checks(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from scripts.quality.phase1_closure import runner
        from scripts.quality import work_archive_scope

        calls = []
        checker = SimpleNamespace(
            check_branch=lambda failures: calls.append("branch"),
            check_required_files=lambda failures: calls.append("required"),
            check_final_review_baseline=lambda failures: calls.append("preserved"),
        )
        with patch.object(runner, "current_branch", return_value=work_archive_scope.BRANCH), \
             patch.object(work_archive_scope, "validate_scope", return_value=[]), \
             patch.multiple(runner.legacy,
                 _load_checker=lambda: checker,
                 legacy_parity_failures=lambda value: [],
                 PRESERVED_CHECKS=("check_final_review_baseline",),
                 _print_result=lambda failures: int(bool(failures))):
            self.assertEqual(runner.run_preserved_contracts(), 0)
        self.assertEqual(calls, ["branch", "required", "preserved"])


class GitScopeTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from scripts.quality.work_archive_scope import BRANCH
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.branch = BRANCH
        self.git("init", "-b", "main")
        (self.root / "docs/governance/preflights").mkdir(parents=True)
        (self.root / "docs/STATUS.md").write_text("baseline\n")
        (self.root / "scripts").mkdir()
        adapter = Path(__file__).resolve().parents[1] / "scripts/governance_preflight_repository.py"
        (self.root / "scripts/governance_preflight_repository.py").write_bytes(adapter.read_bytes())
        self.git("add", ".")
        self.commit("baseline")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("switch", "-c", BRANCH)
        self.preflight = {
            "schema_version": "GovernancePreflightV1", "issue_number": 535,
            "branch": BRANCH, "objective": "Synthetic Git ordering and measured charges",
            "status_decision": "update-minimally",
            "scope": {"required": ["docs/STATUS.md", "docs/governance/preflights/issue-535.json"],
                      "allowed_prefixes": ["docs/STATUS.md", "docs/governance/preflights/issue-535.json"],
                      "forbidden": ["backend/"]},
            "change_budget": {"exact_paths": 2, "maximum_additions_plus_deletions": 205,
                              "deletions_grant_credit": False,
                              "per_file_charged_lines": {"docs/STATUS.md": 5,
                                  "docs/governance/preflights/issue-535.json": 200}},
        }

    def git(self, *args):
        import subprocess
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL, timeout=5)

    def commit(self, message):
        self.git("-c", "user.name=Archive Test", "-c", "user.email=archive@example.invalid", "commit", "-m", message)

    def prepare(self, wrong_first=False):
        import json
        (self.root / "docs/governance/preflights/issue-535.json").write_text(json.dumps(self.preflight))
        if wrong_first:
            (self.root / "docs/STATUS.md").write_text("changed\n")
        self.git("add", ".")
        self.commit("preflight")
        if not wrong_first:
            (self.root / "docs/STATUS.md").write_text("changed\n")

    def check(self, hosted=False):
        from unittest.mock import patch
        from scripts.quality.work_archive_scope import validate_scope
        with patch.dict("os.environ", {"GITHUB_ACTIONS": "true" if hosted else "false"}):
            return validate_scope(self.root, self.branch)

    def test_real_first_commit_and_final_committed_scope(self):
        self.prepare()
        self.assertEqual(self.check(), [])
        self.assertEqual(self.check(hosted=True), ["ARCHIVE_SCOPE_HOSTED_DIRTY"])
        self.git("add", ".")
        self.commit("implementation")
        self.assertEqual(self.check(hosted=True), [])

    def test_wrong_first_commit_rejected(self):
        self.prepare(wrong_first=True)
        self.assertIn("GPF.REPO.PREFLIGHT_NOT_FIRST", self.check(hosted=True))

    def test_git_deletions_charge_budget(self):
        self.prepare()
        (self.root / "docs/STATUS.md").write_text("one\ntwo\nthree\nfour\nfive\n")
        self.assertIn("ARCHIVE_SCOPE_FILE_BUDGET", self.check())


if __name__ == "__main__":
    unittest.main()
