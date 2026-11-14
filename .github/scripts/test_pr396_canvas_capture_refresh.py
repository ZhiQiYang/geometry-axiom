"""Pinned P90 baseline refresh; synthetic judges only, never browser evidence.

Pass the exact published generator with its unchanged T patch beside it.
The generator's synthetic count 12 is confined to temporary in-memory fixtures.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/pr396_canvas_capture.py"
GENERATOR = None
GOLDEN_SHA = "47731559a71bc01ddb608f114707cda3c664b9d8742e37bd5061d464a028b6ef"
REBASED_SHA = "2f070942be7fd6da66dbcdc42e7b671870d619044ebe121ab611c706df0cb67b"


class CaptureBaselineRefresh(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("capture_refresh_under_test", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def checked(self, operation, marker):
        try:
            return operation()
        except (ValueError, RuntimeError, AttributeError) as error:
            self.fail(marker + ": " + str(error))

    def loaded(self):
        return self.checked(lambda: self.m.generator(GENERATOR), "R396_REFRESH_GENERATOR_LOAD")

    def test_current_95_section_baseline_loads_without_writing_golden(self):
        path = ROOT / "geometry-web/cdp_sections.golden.json"
        before = path.read_bytes()
        source = """const fs=require('fs'), c=require('./geometry-web/canvas_capture.js'),
e=require('./tests/helpers/canvas_shards.js');
const p=JSON.parse(fs.readFileSync('geometry-web/canvas_shards.json')),
g=JSON.parse(fs.readFileSync('geometry-web/cdp_sections.golden.json'));
const hashes=Object.fromEntries(['geometry-web/canvas_shards.json','geometry-web/cdp_sections.golden.json']
.map(n=>[n,e.sha(fs.readFileSync(n))]));
console.log(JSON.stringify(c.buildPlan(e.buildPlan(g,p,hashes))));"""
        run = subprocess.run(["node", "-e", source], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, "R396_REFRESH_CURRENT_GOLDEN: " + run.stderr)
        plan = json.loads(run.stdout)
        self.assertEqual(plan["baseline"]["golden"]["total"], 4823)
        self.assertEqual(plan["baseline"]["golden"]["sections"]["P90"], 11)
        self.assertEqual(len(plan["baseline"]["golden"]["sections"]), 95)
        self.assertNotIn("P1161", plan["baseline"]["golden"]["sections"])
        self.assertEqual(plan["units"][1]["sections"][-3:], ["P353", "P1161", "P359"])
        self.assertIs(plan["acceptance"], False)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(hashlib.sha256(before).hexdigest(), GOLDEN_SHA)

    def test_published_generator_is_rebased_to_exact_current_sources(self):
        tool, _, t_raw = self.loaded()
        before = self.checked(lambda: tool.before_files(ROOT), "R396_REFRESH_CURRENT_GENERATOR_BASELINE")
        self.assertEqual((len(before[tool.GOLDEN]), tool.sha(before[tool.GOLDEN])), (1484, GOLDEN_SHA))
        self.assertEqual((len(before[tool.TEST]), tool.sha(before[tool.TEST])),
                         (47521, "7db9dc879d60a4ea52866fb244c51edf735c54aef05d39090bd36911e5e472c6"))
        self.assertEqual((len(t_raw), tool.sha(t_raw)),
                         (1773, "72182fc5a746bbb99b460c5e814e37d79b2d2bde744e33ccb75b9001af985027"))
        raw = self.checked(lambda: self.m.rebase_generator(GENERATOR.read_bytes()), "R396_REFRESH_FIXED_REBASE")
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (30590, REBASED_SHA))

    def test_render_preserves_existing_golden_bytes_and_both_prior_projections(self):
        tool, t_path, _ = self.loaded()
        before = self.checked(lambda: tool.before_files(ROOT), "R396_REFRESH_RENDER_BASELINE")
        with tempfile.TemporaryDirectory(prefix="pr396-refresh-synthetic-") as directory:
            root = Path(directory)
            for name, raw in before.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(raw)
            run = subprocess.run(["git", "apply", str(t_path)], cwd=root, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            after = self.checked(lambda: tool.render_after(before, (root / tool.TEST).read_bytes(), 12),
                                 "R396_REFRESH_RENDER_WITH_EXISTING_P90_PROJECTION")
        projected = after[tool.GOLDEN].replace(b'    "P1161": 12,\n', b'').replace(b'  "total": 4835,\n', b'  "total": 4823,\n')
        self.assertEqual(projected, before[tool.GOLDEN])
        self.assertEqual(json.loads(after[tool.GOLDEN])["sections"]["P90"], 11)
        self.assertIn(b'r400Extension.projectGolden(pfExtension.projectGolden(beforeWorkspace))', after[tool.TEST])
        self.assertIn(b"R396_95_OLD_GOLDEN_BYTES_UNCHANGED", after[tool.TEST])

    def test_transformed_bytes_cannot_drift_even_after_original_hash_matches(self):
        replacements = self.checked(lambda: list(self.m.GENERATOR_REBASE), "R396_REFRESH_FIXED_REBASE_REQUIRED")
        index = next(i for i, row in enumerate(replacements) if row[0] == b"4820")
        old, _, count = replacements[index]
        replacements[index] = (old, b"4824", count)
        with mock.patch.object(self.m, "GENERATOR_REBASE", tuple(replacements)):
            with self.assertRaisesRegex(ValueError, "CAPTURE_GENERATOR_REBASE_CHANGED"):
                self.m.generator(GENERATOR)

    def test_every_preexisting_count_still_has_an_exact_source_pin(self):
        tool, _, _ = self.loaded()
        before = self.checked(lambda: tool.before_files(ROOT), "R396_REFRESH_PINNED_INPUTS")
        with tempfile.TemporaryDirectory(prefix="pr396-refresh-drift-") as directory:
            root = Path(directory)
            for name, raw in before.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(raw)
            raw = before[tool.GOLDEN].replace(b'"P90": 11', b'"P90": 12').replace(b'"total": 4823', b'"total": 4824')
            self.assertNotEqual(raw, before[tool.GOLDEN])
            (root / tool.GOLDEN).write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError, "BEFORE_MISMATCH:geometry-web/cdp_sections.golden.json"):
                tool.before_files(root)

    def test_workflow_selftest_uses_the_same_verified_rebased_loader(self):
        workflow = (ROOT / ".github/workflows/pr396-canvas-capture.yml").read_text()
        self.assertIn('python3 -B .github/scripts/pr396_canvas_capture.py generator-self-test', workflow,
                      "R396_REFRESH_WORKFLOW_SELFTEST")
        run = subprocess.run(["python3", "-B", str(SCRIPT), "generator-self-test", "--repo", str(ROOT),
                              "--generator", str(GENERATOR)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, "R396_REFRESH_SELFTEST_CLI: " + run.stderr)
        summary = json.loads(run.stdout)
        self.assertEqual(summary["passed"], 23)
        self.assertIs(summary["patches_written"], False)
        self.assertIn("NOT browser acceptance", summary["kind"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    args, remaining = parser.parse_known_args()
    GENERATOR = args.generator.resolve()
    unittest.main(argv=[__file__, *remaining])
