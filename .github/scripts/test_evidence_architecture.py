"""Immutable architecture evidence regression tests, using real temporary Git trees.

The fixture runs the unchanged generator and real scanner against a tiny synthetic
manifest. Its two unittest commands are fixture tests, not product evidence. The
first test also runs before the new store exists, against the previous documented
three-file adoption operation, and fails because that operation loses an origin.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("evidence_architecture.py")
MANIFEST = "geometry-core/domain-decoupling/product-architecture.json"
LEGACY = ("PRODUCT-ARCHITECTURE.md", "product-architecture-receipt.json",
          "product-architecture-scan.json")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class PreviousThreeFileAdoption:
    """The old copy-to-fixed-path operation, for the initial behavioral red run."""
    FROZEN = {}

    @staticmethod
    def import_artifact(root, artifact, store):
        target = Path(store) / "current"
        target.mkdir(parents=True, exist_ok=True)
        for name in LEGACY:
            shutil.copyfile(Path(artifact) / name, target / name)
        return {"path": str(target)}

    @staticmethod
    def check_store(root, store, materialize=None):
        receipt = json.loads((Path(store) / "current" / LEGACY[1]).read_bytes())
        return {"origins": [{"sourceHead": receipt["sourceHead"]}]}


if SCRIPT.is_file():
    spec = importlib.util.spec_from_file_location("geometry_evidence_architecture", SCRIPT)
    evidence = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = evidence
    spec.loader.exec_module(evidence)
else:
    evidence = PreviousThreeFileAdoption


class ArchitectureEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="geometry-architecture-store-test-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "repo"
        self.root.mkdir()
        for relative in ("tests/architecture_contract.py", ".github/scripts/architecture_evidence.py"):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)
        (self.root / "src").mkdir()
        (self.root / "src/core.c").write_text("int neutral(void) { return 0; }\n", encoding="utf-8")
        (self.root / "README.md").write_text("Fixture documentation.\n", encoding="utf-8")
        manifest = {
            "schema": "geometry-architecture/1",
            "sourceRoots": ["src"],
            "searchRoots": {"c": ["src"], "python": ["src"], "javascript": ["src"]},
            "sources": [{"path": "src/core.c", "layer": "K", "language": "c",
                         "purpose": "Synthetic input for evidence storage regression"}],
            "exclusions": [],
            "policy": {"cSystemHeaders": [], "pythonStdlib": [], "javascriptBuiltins": [],
                       "externalModules": [], "forbiddenIdentifiers": [], "forbiddenStrings": [],
                       "forbiddenModules": {"c": [], "python": [], "javascript": []}},
        }
        manifest_path = self.root / MANIFEST
        manifest_path.parent.mkdir(parents=True)
        save(manifest_path, manifest)
        # These are complete, nonzero, zero-skip fixture commands. They are not
        # substitutes for the actual repository's 205 + 18 architecture tests.
        fixture_test = (
            "import unittest\n"
            "class Fixture(unittest.TestCase):\n"
            "    def test_fixture(self): self.assertEqual(2 + 2, 4)\n"
            "if __name__ == '__main__': unittest.main()\n"
        )
        for name in ("test_architecture_contract.py", "test_product_architecture.py"):
            (self.root / "tests" / name).write_text(fixture_test, encoding="utf-8")
        self.frozen = {}
        for name in LEGACY:
            relative = "geometry-core/domain-decoupling/" + name
            raw = ("Frozen fixture: " + name + "\n").encode()
            (self.root / relative).write_bytes(raw)
            self.frozen[relative] = sha(raw)
        self.frozen_patch = patch.object(evidence, "FROZEN", self.frozen)
        self.frozen_patch.start()
        self.addCleanup(self.frozen_patch.stop)
        self.git("init", "-q")
        self.git("config", "user.name", "Evidence Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.commit("fixture source")
        self.store = self.home / "store"
        self.sequence = 0

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.STDOUT).decode().strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def generate(self):
        self.sequence += 1
        destination = self.home / ("artifact-" + str(self.sequence))
        env = dict(os.environ, GITHUB_RUN_ID=str(self.sequence), GITHUB_RUN_ATTEMPT="1")
        result = subprocess.run([sys.executable, "-B", ".github/scripts/architecture_evidence.py",
                                 "--out", str(destination)], cwd=self.root, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return destination

    def adopt(self, artifact=None):
        artifact = artifact or self.generate()
        result = evidence.import_artifact(self.root, artifact, self.store)
        return Path(result["path"])

    def rejects(self, code, action):
        with self.assertRaises(evidence.EvidenceError) as caught:
            action()
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def reseal(self, bundle, filename, raw):
        """Change a payload and its outer hash, retaining inner command hashes."""
        (bundle / filename).write_bytes(raw)
        envelope = json.loads((bundle / "bundle.json").read_bytes())
        envelope["files"][filename] = {"bytes": len(raw), "sha256": sha(raw)}
        save(bundle / "bundle.json", envelope)

    def test_unrelated_merge_preserves_both_raw_origins(self):
        first_artifact = self.generate()
        first_raw = (first_artifact / LEGACY[1]).read_bytes()
        first_head = self.git("rev-parse", "HEAD")
        first = self.adopt(first_artifact)
        (self.root / "README.md").write_text("Unrelated documentation merge.\n", encoding="utf-8")
        second_head = self.commit("unrelated documentation")
        second_artifact = self.generate()
        second_raw = (second_artifact / LEGACY[1]).read_bytes()
        second = self.adopt(second_artifact)
        result = evidence.check_store(self.root, self.store)
        self.assertEqual(len(result["origins"]), 2, "fixed-path adoption overwrote a real execution receipt")
        self.assertEqual({origin["sourceHead"] for origin in result["origins"]}, {first_head, second_head})
        self.assertEqual((first / LEGACY[1]).read_bytes(), first_raw)
        self.assertEqual((second / LEGACY[1]).read_bytes(), second_raw)
        self.assertNotEqual(first, second)
        self.assertEqual(Path(result["selected"]), min(first, second))
        for source, adopted in ((first_artifact, first), (second_artifact, second)):
            for path in source.iterdir():
                self.assertEqual((adopted / path.name).read_bytes(), path.read_bytes())

    def test_source_change_is_stale_without_rewriting_old_origin(self):
        bundle = self.adopt()
        old = (bundle / LEGACY[1]).read_bytes()
        (self.root / "src/core.c").write_text("int neutral(void) { return 1; }\n", encoding="utf-8")
        self.commit("changed product")
        self.rejects("STALE", lambda: evidence.check_store(self.root, self.store))
        self.assertEqual((bundle / LEGACY[1]).read_bytes(), old)

    def test_unregistered_source_blocks_before_cache_selection(self):
        self.adopt()
        (self.root / "src/unlisted.c").write_text("int unlisted;\n", encoding="utf-8")
        self.rejects("INVENTORY", lambda: evidence.check_store(self.root, self.store))

    def test_generator_change_is_stale(self):
        self.adopt()
        path = self.root / ".github/scripts/architecture_evidence.py"
        path.write_bytes(path.read_bytes() + b"\n# generator changed\n")
        self.commit("generator changed")
        self.rejects("STALE", lambda: evidence.check_store(self.root, self.store))

    def test_import_rejects_an_unsupported_generator(self):
        artifact = self.generate()
        path = self.root / ".github/scripts/architecture_evidence.py"
        path.write_bytes(path.read_bytes() + b"\n# generator changed\n")
        self.commit("generator changed")
        receipt = json.loads((artifact / LEGACY[1]).read_bytes())
        old_head = receipt["sourceHead"]
        receipt["sourceHead"] = self.git("rev-parse", "HEAD")
        save(artifact / LEGACY[1], receipt)
        report = artifact / LEGACY[0]
        report.write_bytes(report.read_bytes().replace(old_head.encode(), receipt["sourceHead"].encode()))
        self.rejects("GENERATOR", lambda: self.adopt(artifact))

    def test_import_rejects_a_different_execution_head(self):
        artifact = self.generate()
        (self.root / "README.md").write_text("Unrelated merge.\n", encoding="utf-8")
        self.commit("new head")
        self.rejects("SOURCE_HEAD", lambda: self.adopt(artifact))

    def test_import_rejects_dirty_checkout(self):
        artifact = self.generate()
        (self.root / "README.md").write_text("Uncommitted documentation.\n", encoding="utf-8")
        self.rejects("DIRTY", lambda: self.adopt(artifact))

    def test_frozen_views_cannot_be_changed_or_committed(self):
        self.adopt()
        path = self.root / "geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md"
        path.write_bytes(path.read_bytes() + b"changed\n")
        self.rejects("FROZEN_BASELINE", lambda: evidence.check_store(self.root, self.store))
        self.commit("illegal baseline rewrite")
        self.rejects("FROZEN_BASELINE", lambda: evidence.check_store(self.root, self.store))

    def test_worktree_cannot_hide_a_changed_committed_frozen_view(self):
        self.adopt()
        path = self.root / "geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md"
        original = path.read_bytes()
        path.write_bytes(original + b"changed\n")
        self.commit("illegal baseline rewrite")
        path.write_bytes(original)
        self.rejects("FROZEN_BASELINE", lambda: evidence.check_store(self.root, self.store))

    def test_old_three_files_without_raw_outputs_are_not_importable(self):
        artifact = self.generate()
        (artifact / "architecture-unit.stderr").unlink()
        self.rejects("RAW_FILES", lambda: self.adopt(artifact))

    def test_local_run_without_official_origin_is_not_importable(self):
        for field in ("runId", "runAttempt"):
            with self.subTest(field=field):
                artifact = self.generate()
                receipt = json.loads((artifact / LEGACY[1]).read_bytes())
                receipt[field] = None
                save(artifact / LEGACY[1], receipt)
                if field == "runId":
                    report = artifact / LEGACY[0]
                    report.write_bytes(report.read_bytes().replace(
                        ("Actions run `" + str(self.sequence) + "`").encode(), b"Actions run `None`"))
                self.rejects("RECEIPT", lambda: self.adopt(artifact))

    def test_raw_command_hash_is_checked_after_outer_hash_is_resealed(self):
        bundle = self.adopt()
        self.reseal(bundle, "architecture-unit.stderr", b"Ran 1 test in 0.001s\n\nOK\n")
        self.rejects("COMMAND_HASH", lambda: evidence.check_store(self.root, self.store))

    def test_raw_byte_count_is_checked(self):
        bundle = self.adopt()
        envelope = json.loads((bundle / "bundle.json").read_bytes())
        envelope["files"]["architecture-unit.stderr"]["bytes"] += 1
        save(bundle / "bundle.json", envelope)
        self.rejects("RAW_HASH", lambda: evidence.check_store(self.root, self.store))

    def test_invalid_candidate_is_not_hidden_by_a_valid_candidate(self):
        first = self.adopt()
        (self.root / "README.md").write_text("New origin.\n", encoding="utf-8")
        self.commit("new origin")
        second = self.adopt()
        # The invalid candidate is deliberately sorted last: selecting the first
        # apparently-green proof would hide it.
        invalid = max(first, second)
        self.reseal(invalid, "architecture-product.stderr", b"corrupt raw output\n")
        self.rejects("COMMAND_HASH", lambda: evidence.check_store(self.root, self.store))

    def test_self_consistent_conflicting_scan_cannot_hide_behind_canonical_origin(self):
        self.adopt()
        (self.root / "README.md").write_text("Another complete origin.\n", encoding="utf-8")
        self.commit("second origin")
        second = self.adopt()
        scan = json.loads((second / LEGACY[2]).read_bytes())
        scan["edges"] = [{"source": "src/core.c", "target": "src/core.c", "line": 1}]
        scan_raw = (json.dumps(scan, ensure_ascii=False, indent=2) + "\n").encode()
        (second / LEGACY[2]).write_bytes(scan_raw)
        (second / "architecture-cli.stdout").write_bytes(scan_raw)
        receipt = json.loads((second / LEGACY[1]).read_bytes())
        receipt["edgeCount"] = 1
        receipt["scanSha256"] = sha(scan_raw)
        receipt["commands"][0]["stdoutSha256"] = sha(scan_raw)
        save(second / LEGACY[1], receipt)
        report = second / LEGACY[0]
        report.write_bytes(report.read_bytes().replace(b"0 edges", b"1 edges"))
        envelope = json.loads((second / "bundle.json").read_bytes())
        for name in envelope["files"]:
            raw = (second / name).read_bytes()
            envelope["files"][name] = {"bytes": len(raw), "sha256": sha(raw)}
        save(second / "bundle.json", envelope)
        second.rename(second.with_name(sha((second / LEGACY[1]).read_bytes())))
        self.rejects("CONTRADICTORY", lambda: evidence.check_store(self.root, self.store))

    def test_adopting_same_artifact_twice_keeps_one_identical_bundle(self):
        artifact = self.generate()
        first = self.adopt(artifact)
        before = {path.name: path.read_bytes() for path in first.iterdir()}
        second = self.adopt(artifact)
        self.assertEqual(first, second)
        self.assertEqual(before, {path.name: path.read_bytes() for path in second.iterdir()})
        self.assertEqual(len(evidence.check_store(self.root, self.store)["origins"]), 1)

    def test_test_script_change_is_stale(self):
        self.adopt()
        path = self.root / "tests/test_product_architecture.py"
        path.write_bytes(path.read_bytes() + b"\n# oracle changed\n")
        self.commit("test script changed")
        self.rejects("STALE", lambda: evidence.check_store(self.root, self.store))

    def test_bundle_context_cannot_drop_an_input(self):
        bundle = self.adopt()
        envelope = json.loads((bundle / "bundle.json").read_bytes())
        envelope["context"]["inputs"] = []
        save(bundle / "bundle.json", envelope)
        self.rejects("CLOSURE", lambda: evidence.check_store(self.root, self.store))

    def test_no_matching_bundle_blocks_without_using_legacy_receipt(self):
        self.rejects("STALE", lambda: evidence.check_store(self.root, self.store))

    def test_materialization_is_outside_repo_and_preserves_exact_bytes(self):
        bundle = self.adopt()
        self.rejects("MATERIALIZE", lambda: evidence.check_store(
            self.root, self.store, self.root / "replacement-view"))
        destination = self.home / "view"
        evidence.check_store(self.root, self.store, destination)
        for name in LEGACY:
            self.assertEqual((destination / name).read_bytes(), (bundle / name).read_bytes())
        self.rejects("MATERIALIZE", lambda: evidence.check_store(self.root, self.store, destination))

    def test_symlink_payload_is_not_adopted(self):
        artifact = self.generate()
        path = artifact / "architecture-unit.stdout"
        original = self.home / "aliased-output"
        path.rename(original)
        path.symlink_to(original)
        self.rejects("RAW_FILES", lambda: self.adopt(artifact))

    def test_zero_tests_skip_or_command_change_cannot_be_imported(self):
        for change in ("zero", "skip", "command", "exit"):
            with self.subTest(change=change):
                artifact = self.generate()
                receipt = json.loads((artifact / LEGACY[1]).read_bytes())
                row = receipt["commands"][1]
                if change in ("zero", "skip"):
                    raw = b"Ran 0 tests in 0.001s\n\nOK\n" if change == "zero" else b"Ran 1 test in 0.001s\n\nOK (skipped=1)\n"
                    (artifact / row["stderr"]).write_bytes(raw)
                    row["stderrSha256"] = sha(raw)
                    row["testsRun"] = 0 if change == "zero" else 1
                elif change == "command":
                    row["command"].append("--skip")
                else:
                    row["exitCode"] = 1
                save(artifact / LEGACY[1], receipt)
                self.rejects("COMMAND", lambda: self.adopt(artifact))


if __name__ == "__main__":
    unittest.main()
