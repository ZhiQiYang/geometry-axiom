"""Execute a genuinely template-free installation and source-level mutants."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PURE_TESTS = ("test_geometry_kernel_geometry", "test_geometry_kernel_graph",
              "test_geometry_kernel_transactions", "test_geometry_kernel_session")

ISOLATED = r'''
import importlib.abc, json, pathlib, sys, unittest
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
class RejectHostAndTemplate(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'modeling', 'geometry_app', 'geometry_woodworking'}:
            raise AssertionError('Forbidden import attempted: ' + fullname)
sys.meta_path.insert(0, RejectHostAndTemplate())
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
    ('test_geometry_kernel_geometry.KernelGeometryTests', 'test_geometry_kernel_graph.KernelGraphTests',
     'test_geometry_kernel_transactions.CandidateCellTests', 'test_geometry_kernel_session.KernelSessionTests'))
result = unittest.TextTestRunner(verbosity=1).run(suite)
loaded = []
for name, module in sys.modules.items():
    if name == 'geometry_kernel' or name.startswith('geometry_kernel.'):
        path = pathlib.Path(module.__file__).resolve()
        assert path.is_relative_to(root / 'geometry_kernel'), path
        loaded.append(name)
assert not any(name.split('.')[0] in {'modeling', 'geometry_app', 'geometry_woodworking'} for name in sys.modules)
assert len(loaded) >= 5, loaded
print(json.dumps({'tests': result.testsRun, 'loaded': sorted(loaded), 'success': result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
'''

MUTANT_RUN = r'''
import pathlib, sys, unittest
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in sys.argv[2:])
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
'''


class KernelIsolationTests(unittest.TestCase):
    def copy_pure(self, root):
        shutil.copytree(ROOT / "geometry-core/geometry_kernel", root / "geometry_kernel", ignore=shutil.ignore_patterns("__pycache__"))
        for name in PURE_TESTS:
            shutil.copy2(ROOT / "tests" / (name + ".py"), root / (name + ".py"))

    def run_process(self, script, root, *args):
        return subprocess.run([sys.executable, "-I", "-B", "-c", script, str(root), *args],
                              cwd=root, capture_output=True, text=True, timeout=30)

    def test_only_kernel_files_installed_with_blocking_import_finder(self):
        with tempfile.TemporaryDirectory(prefix="geometry-kernel-only-") as directory:
            root = Path(directory)
            self.copy_pure(root)
            self.assertEqual({"geometry_kernel", *(name + ".py" for name in PURE_TESTS)}, {p.name for p in root.iterdir()})
            result = self.run_process(ISOLATED, root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            receipt = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(82, receipt["tests"])
            self.assertTrue(receipt["success"])

    def test_shared_implementation_source_mutants_fail_both_oracles(self):
        cases = (
            ("types.py", "            if location:\n", "            if False:\n",
             "test_geometry_kernel_geometry.KernelGeometryTests.test_through_hole_extrusion_has_exact_volume_and_inward_hole_faces"),
            ("geometry.py", "normal_sign=sign*face.source_sign", "normal_sign=1",
             "test_geometry_kernel_geometry.KernelGeometryTests.test_boolean_cavity_records_all_shells_and_tool_normal_sign"),
        )
        for filename, before, after, pure_oracle in cases:
            with self.subTest(mutant=filename), tempfile.TemporaryDirectory(prefix="geometry-shared-mutant-") as directory:
                root = Path(directory)
                self.copy_pure(root)
                shutil.copytree(ROOT / "geometry-core/modeling", root / "modeling", ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copytree(ROOT / "geometry-app/geometry_app", root / "geometry_app", ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copytree(ROOT / "geometry-templates/woodworking/geometry_woodworking", root / "geometry_woodworking", ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copy2(ROOT / "tests/test_geometry_kernel_compatibility.py", root / "test_geometry_kernel_compatibility.py")
                legacy_oracle = "test_geometry_kernel_compatibility.GeometryKernelCompatibilityTests.test_pre_extraction_meshes_are_byte_identical"
                baseline = self.run_process(MUTANT_RUN, root, pure_oracle, legacy_oracle)
                self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
                path = root / "geometry_kernel" / filename
                original = path.read_text(encoding="utf-8")
                self.assertEqual(1, original.count(before))
                path.write_text(original.replace(before, after), encoding="utf-8")
                for oracle in (pure_oracle, legacy_oracle):
                    result = self.run_process(MUTANT_RUN, root, oracle)
                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn("Ran 1 test", result.stderr)
                    self.assertNotIn("ImportError", result.stderr)
                    self.assertNotIn("SyntaxError", result.stderr)
                path.write_text(original, encoding="utf-8")
                restored = self.run_process(MUTANT_RUN, root, pure_oracle, legacy_oracle)
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == "__main__":
    unittest.main()
