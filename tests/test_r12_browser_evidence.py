"""Evidence classification and frozen-source gates, not product browser evidence."""
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests import r12_browser_evidence as evidence


def green():
    return {"exitCode": 0, "timedOut": False, "runtimeUnchanged": True,
            "result": {"completed": True, "passed": 64, "failed": 0, "exceptions": [], "consoleErrors": [],
                       "scope": {"mode": "partial", "included": ["profile-space"],
                                 "filters": ["GEOMETRY_SPACE_PROFILE_ONLY"]},
                       "groups": {"setup": {"expected": 2, "passed": 2, "failed": 0, "completed": True},
                                  "profile-space": {"expected": 60, "passed": 60, "failed": 0, "completed": True},
                                  "browser-health": {"expected": 2, "passed": 2, "failed": 0, "completed": True}},
                       "results": []}}


class BrowserEvidenceVerdicts(unittest.TestCase):
    def test_baseline_requires_exact_scope_setup_count_health_and_fresh_runtime(self):
        self.assertEqual(evidence.classify(green()), "green")
        changes = [
            lambda r: r.update(timedOut=True),
            lambda r: r.update(runtimeUnchanged=False),
            lambda r: r.update(error="Chrome failed before CDP"),
            lambda r: r["result"].update(passed=63),
            lambda r: r["result"].update(completed=False),
            lambda r: r["result"].update(exceptions=["runtime exception"]),
            lambda r: r["result"].update(consoleErrors=["resource failure"]),
            lambda r: r["result"]["scope"].update(mode="full-space-suite"),
            lambda r: r["result"]["scope"].update(included=[]),
            lambda r: r["result"]["groups"]["setup"].update(passed=1),
            lambda r: r["result"]["groups"]["profile-space"].update(expected=59),
            lambda r: r["result"]["groups"]["browser-health"].update(completed=False),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                row = green()
                change(row)
                self.assertNotEqual(evidence.classify(row), "green")

    def test_only_the_registered_product_assertion_is_a_kill(self):
        row = green()
        row["exitCode"] = 1
        row["result"].update(completed=False, passed=11, failed=3)
        row["result"]["groups"]["profile-space"].update(passed=9, failed=1, completed=False)
        row["result"]["groups"]["browser-health"].update(passed=0, completed=False)
        row["result"]["results"] = [{"name": "R12_ALL_WORLD_CANDIDATES", "ok": False},
                                    {"name": "complete browser flow", "ok": False},
                                    {"name": "space group completeness", "ok": False}]
        self.assertEqual(evidence.classify(row, "R12_ALL_WORLD_CANDIDATES"), "killed")
        self.assertEqual(evidence.classify(row, "R12_EXPLICIT_SELECTION"), "blocked")
        self.assertEqual(evidence.classify(row), "blocked")
        for mutate in [lambda r: r.update(timedOut=True),
                       lambda r: r["result"].update(consoleErrors=["page failed"]),
                       lambda r: r["result"]["results"].append({"name": "unrelated assertion", "ok": False}),
                       lambda r: r["result"]["results"].append({"name": "R12_ALL_WORLD_CANDIDATES", "ok": False})]:
            value = deepcopy(row)
            mutate(value)
            self.assertEqual(evidence.classify(value, "R12_ALL_WORLD_CANDIDATES"), "blocked")

    def test_setup_failure_or_missing_result_never_kills_any_named_withdrawal(self):
        for row in [{"exitCode": 1, "runtimeUnchanged": True},
                    {"exitCode": -6, "runtimeUnchanged": True, "error": "AF_UNIX EPERM"},
                    {"exitCode": 1, "runtimeUnchanged": True, "result": {"completed": False,
                      "results": [{"name": "R12_ALL_WORLD_CANDIDATES", "ok": False}]}}]:
            self.assertEqual(evidence.classify(row, "R12_ALL_WORLD_CANDIDATES"), "blocked")

    def test_sparse_archives_are_declared_but_missing_application_sources_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r12-evidence-contract-") as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            archive = root / "tests/evidence/old/receipt.json"
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'{"old":true}\n')
            source = root / "app.js"
            source.write_bytes(b"const value = 1;\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            expected_blob = subprocess.check_output(["git", "hash-object", str(archive)], text=True).strip()
            subprocess.run(["git", "update-index", "--skip-worktree", "tests/evidence/old/receipt.json"], cwd=root, check=True)
            archive.unlink()
            work = Path(directory) / "frozen"
            sources, archives = evidence.freeze(root, work)
            self.assertEqual((work / "app.js").read_bytes(), source.read_bytes())
            self.assertEqual(set(sources), {"app.js"})
            self.assertEqual(archives, {"tests/evidence/old/receipt.json": {"mode": "100644", "gitBlob": expected_blob}})
            source.unlink()
            with self.assertRaisesRegex(RuntimeError, "ordinary source files"):
                evidence.freeze(root, Path(directory) / "missing")
            subprocess.run(["git", "update-index", "--skip-worktree", "app.js"], cwd=root, check=True)
            with self.assertRaisesRegex(RuntimeError, "Sparse source must be materialized"):
                evidence.freeze(root, Path(directory) / "sparse-app")


if __name__ == "__main__":
    unittest.main()
