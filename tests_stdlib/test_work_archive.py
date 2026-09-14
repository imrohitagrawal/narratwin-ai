"""Synthetic stdlib boundary tests; no private project evidence is required."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/work_archive.py"


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        self.private = self.base / "private"
        self.repo.mkdir()
        self.private.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.index_path = "docs/work-archive/2026-09-14-recovery/INDEX.json"
        self.handoff = "docs/work-archive/2026-09-14-recovery/HANDOFF.md"
        self.artifacts = []
        source = {}
        for key in ["A", "B", "B0", "C", "I", "IM", "L", "P", "R", "VALIDATOR", "OWNER_PLAN"]:
            data = ("synthetic " + key).encode()
            name = key + ".bin"
            self.write(self.private, name, data)
            ref = "restricted-evidence:" + key
            self.artifacts.append(dict(id=key, restrictedEvidenceRef=ref,
                                       sha256=digest(data), bytes=len(data), privatePath=name))
            source[key] = dict(restrictedEvidenceRef=ref, fileSha256=digest(data),
                               byteCount=len(data))
        source["VALIDATOR"].pop("byteCount")
        owner = source.pop("OWNER_PLAN")
        validator = source.pop("VALIDATOR")
        self.mapping = {
            "externalSemanticCorrectionOverlay": {"exhaustiveReview": {
                "artifacts": source, "independentValidator": validator}},
            "sources": [{"authorityOrigin": {
                "kind": "RESTRICTED_OWNER_MESSAGE", "reference": owner["restrictedEvidenceRef"],
                "contentSha256": owner["fileSha256"], "byteCount": owner["byteCount"]}}]}
        mapping_path = "docs/governance/superset-mapping-v2.json"
        raw = json.dumps(self.mapping).encode()
        self.write(self.repo, mapping_path, raw)
        docs = ["docs/work-archive/README.md", "docs/work-archive/PROCESS.md",
                "docs/governance/NARRATWIN_MASTER_PROGRAM_V2.md"]
        docs += ["docs/work-archive/2026-09-14-recovery/" + name for name in
                 ["COMPARISON_AND_AMENDMENT.md", "DECISIONS.md", "REVIEW.md"]]
        entries = []
        for path in docs:
            self.write(self.repo, path, b"synthetic public document\n")
            entries.append(dict(path=path, sha256=digest(b"synthetic public document\n"), bytes=26))
        self.index = dict(schemaVersion=1, mapping=dict(path=mapping_path, sha256=digest(raw)),
                          artifacts=self.artifacts, publicDocuments=entries, handoffPath=self.handoff,
                          privateInventory={}, backup="UNPROVED", semanticAcceptance="NOT_GRANTED")
        self.inventory = dict(schemaVersion=1, sensitivity="RESTRICTED_LOCAL_ONLY", files=[
            dict(path=a["privatePath"], sha256=a["sha256"], bytes=a["bytes"])
            for a in self.artifacts])
        self.save_inventory()
        self.save_index()

    def write(self, root, path, data):
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    def save_inventory(self):
        data = json.dumps(self.inventory).encode()
        self.write(self.private, "PRIVATE_INVENTORY.json", data)
        self.index["privateInventory"] = dict(path="PRIVATE_INVENTORY.json", sha256=digest(data), bytes=len(data))

    def save_index(self, handoff=True):
        data = json.dumps(self.index).encode()
        self.write(self.repo, self.index_path, data)
        if handoff:
            self.write(self.repo, self.handoff, ("INDEX_SHA256: " + digest(data) + "\n").encode())

    def run_cli(self, private=False, **options):
        args = ["python3", "-B", str(SCRIPT), "--repo-root", str(self.repo),
                "--index", self.index_path]
        if private:
            args += ["--private-root", str(self.private)]
        for key, value in options.items():
            args += ["--" + key.replace("_", "-"), str(value)]
        return subprocess.run(args, capture_output=True, text=True, check=False)

    def reject(self, private=False):
        result = self.run_cli(private)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn(str(self.base), result.stdout + result.stderr)
        self.assertNotIn("synthetic ", result.stdout + result.stderr)
        self.assertIn("error", json.loads(result.stdout))
        return result

    def test_public_does_not_claim_private_or_backup(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["privateAvailability"], "NOT_CHECKED")
        self.assertEqual(report["backup"], "UNPROVED")

    def test_private_verifies_masters_and_full_inventory(self):
        self.write(self.private, "history/extra.txt", b"retained history")
        self.inventory["files"].append(dict(path="history/extra.txt", bytes=16,
                                             sha256=digest(b"retained history")))
        self.save_inventory()
        self.save_index()
        result = self.run_cli(True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["privateAvailability"], "VERIFIED")
        self.assertEqual(json.loads(result.stdout)["inventoryFilesVerified"], 12)

    def test_census_omission_duplicate_and_unrecognized_identity(self):
        for mutate in [lambda: self.index["artifacts"].pop(),
                       lambda: self.index["artifacts"].append(self.artifacts[0].copy()),
                       lambda: self.artifacts[0].update(id="OTHER")]:
            old = json.loads(json.dumps(self.index))
            mutate()
            self.save_index()
            self.reject()
            self.index = old
            self.artifacts = self.index["artifacts"]

    def test_types_and_authority_mismatch(self):
        original = self.artifacts[0].copy()
        for change in [dict(bytes=True), dict(bytes=-1), dict(sha256="z" * 64),
                       dict(sha256="0" * 64), dict(restrictedEvidenceRef="restricted-evidence:other")]:
            self.artifacts[0].update(change)
            self.save_index()
            self.reject()
            self.artifacts[0].update(original)

    def test_unsafe_and_duplicate_paths(self):
        for path in ["../escape", "/absolute", "a/../b", "a\\b", "a//b", "A.bin/", "B.bin"]:
            self.artifacts[0]["privatePath"] = path
            self.save_index()
            self.reject()

    def test_missing_corrupt_and_symlinked_private_file(self):
        path = self.private / "A.bin"
        old = path.read_bytes()
        path.unlink()
        self.assertIn("PRIVATE_MISSING", self.reject(True).stdout)
        path.write_bytes(b"wrong bytes")
        self.assertIn("PRIVATE_CORRUPT", self.reject(True).stdout)
        path.unlink()
        path.symlink_to(self.private / "B.bin")
        self.reject(True)
        path.unlink()
        path.write_bytes(old)

    def test_inventory_extra_corruption_omission_and_duplicate(self):
        self.write(self.private, "extra", b"history")
        self.inventory["files"].append(dict(path="extra", bytes=7, sha256=digest(b"history")))
        self.save_inventory()
        self.save_index()
        self.write(self.private, "extra", b"changed")
        self.reject(True)
        self.inventory["files"].pop()
        self.save_inventory()
        self.save_index()
        self.reject(True)
        self.inventory["files"].append(self.inventory["files"][0].copy())
        self.save_inventory()
        self.save_index()
        self.reject(True)

    def test_stale_handoff_and_changed_public_doc(self):
        self.write(self.repo, self.handoff, ("INDEX_SHA256: " + "0" * 64 + "\n").encode())
        self.assertIn("HANDOFF_STALE", self.reject().stdout)
        self.save_index()
        self.write(self.repo, self.index["publicDocuments"][0]["path"], b"changed")
        self.reject()

    def test_required_document_cannot_be_removed(self):
        self.index["publicDocuments"].pop()
        self.save_index()
        self.reject()

    def test_backup_or_semantic_acceptance_cannot_be_claimed(self):
        for key in ["backup", "semanticAcceptance"]:
            old = self.index[key]
            self.index[key] = "PASS"
            self.save_index()
            self.reject()
            self.index[key] = old

    def test_tracked_private_path_rejected_without_private_access(self):
        self.write(self.repo, "docs/work-archive/.restricted/secret", b"restricted fixture")
        subprocess.run(["git", "-C", str(self.repo), "add", "docs/work-archive/.restricted/secret"], check=True)
        self.reject()

    def test_public_symlink_and_private_root_symlink(self):
        p = self.repo / self.index["publicDocuments"][0]["path"]
        p.unlink()
        p.symlink_to(self.repo / self.index["publicDocuments"][1]["path"])
        self.reject()
        p.unlink()
        p.write_bytes(b"synthetic public document\n")
        link = self.base / "private-link"
        link.symlink_to(self.private, target_is_directory=True)
        result = self.run_cli(private_root=link)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(str(link), result.stdout + result.stderr)

    def test_duplicate_json_keys_and_unknown_keys_rejected(self):
        p = self.repo / self.index_path
        p.write_text('{"schemaVersion":1,"schemaVersion":1}')
        self.reject()
        self.index["unexpected"] = "value"
        self.save_index()
        self.reject()

    def test_intermediate_private_symlink_rejected(self):
        (self.private / "linked").symlink_to(self.private, target_is_directory=True)
        self.artifacts[0]["privatePath"] = "linked/A.bin"
        self.save_index()
        self.reject(True)

    def test_public_pass_survives_absent_private_directory(self):
        self.private.rename(self.base / "unavailable")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        failed = self.reject(True)
        self.assertEqual(json.loads(failed.stdout)["publicIndex"], "VALID")

    def test_inventory_digest_cannot_be_replaced_silently(self):
        self.write(self.private, "PRIVATE_INVENTORY.json", b"{}")
        self.assertIn("PRIVATE_INVENTORY_CORRUPT", self.reject(True).stdout)

    def test_duplicate_handoff_marker_rejected(self):
        p = self.repo / self.handoff
        p.write_text(p.read_text() + "INDEX_SHA256: invalid\n")
        self.assertIn("HANDOFF_STALE", self.reject().stdout)

    def test_malformed_mapping_returns_structured_redacted_failure(self):
        for sources in [[None], None, [{"authorityOrigin": None}]]:
            self.mapping["sources"] = sources
            raw = json.dumps(self.mapping).encode()
            self.write(self.repo, self.index["mapping"]["path"], raw)
            self.index["mapping"]["sha256"] = digest(raw)
            self.save_index()
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            self.assertNotIn(str(self.base), result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["error"], "AUTHORITY_CENSUS_INVALID")

    def test_git_timeout_configuration_rejects_nonpositive_and_nonfinite(self):
        for value in ["0", "-1", "nan", "inf", "invalid"]:
            result = self.run_cli(git_timeout_seconds=value)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(str(self.base), result.stdout + result.stderr)

    def test_git_timeout_reaches_consumer_and_failure_is_redacted(self):
        spec = importlib.util.spec_from_file_location("archive_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = ["--repo-root", str(self.repo), "--index", self.index_path,
                "--git-timeout-seconds", "0.75"]
        for result in [subprocess.TimeoutExpired("secret-command", .75,
                                                 output="secret-output", stderr="secret-error"),
                       subprocess.CompletedProcess([], 1, b"secret-output", b"secret-error")]:
            output = io.StringIO()
            kwargs = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
            with patch.object(module.subprocess, "run", **kwargs) as call, redirect_stdout(output):
                self.assertEqual(module.main(args), 1)
            self.assertEqual(call.call_args.kwargs["timeout"], .75)
            self.assertEqual(json.loads(output.getvalue())["effectiveConfiguration"]["gitTimeoutSeconds"], .75)
            self.assertNotIn("secret", output.getvalue())
            self.assertNotIn(str(self.base), output.getvalue())


if __name__ == "__main__":
    unittest.main()
