#!/usr/bin/env python3
"""PR353 legacy precondition through the real snapshot/environment functions.

These checks do not launch Chrome or claim browser mutation kills. They exercise
the exact no-.git source container used by that runner, including untracked
manifest inputs, and prove corrupt legacy data cannot execute or fall back.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "tests/fixtures/pr353-legacy-reader-405f8c5e.json"
HELPER = "tests/pr353_legacy_reader.js"
SPEC = importlib.util.spec_from_file_location(
    "pr353_browser_mutation_check", ROOT / "geometry-web/browser_mutation_check.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

READ = """
const L=require('./tests/pr353_legacy_reader.js');
const crypto=require('node:crypto');
const sources=L.readLegacySources(),reader=L.loadLegacyReader();
if(typeof reader.pack!=='function'||typeof reader.unpack!=='function')throw Error('Legacy API unavailable');
console.log(JSON.stringify({commit:L.LEGACY_COMMIT,files:Object.entries(sources).map(([file,source])=>{
  const bytes=Buffer.from(source,'utf8');
  const blob=crypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+String.fromCharCode(0))).update(bytes).digest('hex');
  if(blob!==L.LEGACY_BLOBS[file])throw Error('Independent blob check failed');
  return {file,blob,bytes:bytes.length};
})}));
"""


class LegacySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="pr353-legacy-snapshot-")
        cls.directory = Path(cls.temporary.name)
        cls.source = cls.directory / "source"
        cls.source.mkdir()
        caller = dict(os.environ)
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            caller.pop(name, None)
        cls.manifest = RUNNER.read_manifest(ROOT / "geometry-web/grid_card_entry_mutations.json")
        # Only the sentinel is tracked. The fixture must travel as a declared
        # input even immediately after git apply, before the user commits it.
        for name in cls.manifest["inputs"]:
            target = cls.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        subprocess.run(["git", "init", "-q", str(cls.source)], env=caller, check=True)
        (cls.source / "sentinel.txt").write_text("tracked snapshot input\n")
        subprocess.run(["git", "-C", str(cls.source), "add", "sentinel.txt"], env=caller, check=True)
        cls.baseline = cls.directory / "baseline"
        cls.baseline.mkdir()
        with patch.dict(os.environ, caller, clear=True):
            cls.files = RUNNER.snapshot(cls.source, cls.baseline, cls.manifest["inputs"])
        caller["GEOMETRY_PR353_LEGACY_ROOT"] = str(cls.directory / "must-not-be-used")
        cls.env = RUNNER.isolated_environment(caller)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.work = self.directory / self._testMethodName
        shutil.copytree(self.baseline, self.work)

    def node(self, code=READ, env=None):
        return subprocess.run(["node", "-e", code], cwd=self.work,
                              env=self.env if env is None else env,
                              text=True, encoding="utf-8", capture_output=True,
                              timeout=30)

    def change_fixture(self, body):
        code = """
const fs=require('node:fs'),z=require('node:zlib');
const file='tests/fixtures/pr353-legacy-reader-405f8c5e.json';
const fixture=JSON.parse(fs.readFileSync(file,'utf8'));
const sources=JSON.parse(z.brotliDecompressSync(Buffer.from(fixture.payload.join(''),'base64')).toString('utf8'));
""" + body + """
fixture.payload=[z.brotliCompressSync(Buffer.from(JSON.stringify(sources))).toString('base64')];
fs.writeFileSync(file,JSON.stringify(fixture));
"""
        result = self.node(code)
        self.assertEqual(result.returncode, 0, result.stderr)

    def assert_blocked(self, text):
        result = self.node()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PR353 legacy reader precondition:", result.stderr)
        self.assertIn(text, result.stderr)
        return result

    def test_formal_snapshot_reads_all_seven_without_git_or_override(self):
        self.assertFalse((self.work / ".git").exists())
        self.assertNotIn("GEOMETRY_PR353_LEGACY_ROOT", self.env)
        self.assertNotIn("GIT_DIR", self.env)
        self.assertIn(FIXTURE, self.files)
        self.assertEqual(self.files[FIXTURE], RUNNER.digest((self.work / FIXTURE).read_bytes()))
        self.assertEqual(subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                                       cwd=self.work, env=self.env,
                                       capture_output=True).returncode, 128)
        result = self.node()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["commit"], "405f8c5e1a637a16cbe47470faf5ae1fa02b8676")
        self.assertEqual(len(receipt["files"]), 7)
        self.assertEqual(sum(row["bytes"] for row in receipt["files"]), 172159)

    def test_missing_untracked_fixture_blocks_snapshot(self):
        source = self.directory / "missing-input-source"
        shutil.copytree(self.source, source)
        (source / FIXTURE).unlink()
        destination = self.directory / "missing-input-snapshot"
        destination.mkdir()
        with patch.dict(os.environ, self.env, clear=True), self.assertRaisesRegex(ValueError, "Missing test input: " + FIXTURE):
            RUNNER.snapshot(source, destination, self.manifest["inputs"])

    def test_missing_fixture_does_not_fall_back(self):
        (self.work / FIXTURE).unlink()
        self.assert_blocked("fixed fixture unavailable or invalid")

    def test_changed_blob_is_rejected_before_any_legacy_code_executes(self):
        self.change_fixture("sources['geometry-web/reference-display.js'] += '\\nthrow Error(\\\"TAMPERED_LEGACY_EXECUTED\\\");\\n';")
        result = self.assert_blocked("Git blob mismatch for geometry-web/reference-display.js")
        self.assertNotIn("TAMPERED_LEGACY_EXECUTED", result.stderr)

    def test_closure_cannot_omit_or_add_a_source(self):
        original = (self.work / FIXTURE).read_bytes()
        for mutation in ["delete sources['geometry-web/reference-display.js'];",
                         "sources['geometry-web/extra.js']='module.exports={};';"]:
            with self.subTest(mutation=mutation):
                (self.work / FIXTURE).write_bytes(original)
                self.change_fixture(mutation)
                self.assert_blocked("exactly the seven fixed source blobs")

    def test_wrong_commit_or_noncanonical_payload_is_rejected(self):
        original = json.loads((self.work / FIXTURE).read_text())
        for change in [{"commit": "0" * 40}, {"payload": ["not base64!"]}]:
            with self.subTest(change=change):
                (self.work / FIXTURE).write_text(json.dumps({**original, **change}))
                self.assert_blocked("fixed fixture unavailable or invalid")

    def test_explicit_materialized_root_still_requires_immutable_blobs(self):
        target = self.directory / "materialized"
        result = self.node("console.log(JSON.stringify(require('./tests/pr353_legacy_reader.js').materializeLegacyReader(" + json.dumps(str(target)) + ")))")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["files"]), 7)
        explicit = {**self.env, "GEOMETRY_PR353_LEGACY_ROOT": str(target)}
        result = self.node(env=explicit)
        self.assertEqual(result.returncode, 0, result.stderr)
        changed = target / "geometry-web/project-store.js"
        changed.write_bytes(changed.read_bytes() + b"\n")
        result = self.node(env=explicit)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git blob mismatch", result.stderr)
        # A valid bundled fixture cannot hide corruption in an explicit root.
        self.assertEqual(self.node().returncode, 0)


if __name__ == "__main__":
    unittest.main()
