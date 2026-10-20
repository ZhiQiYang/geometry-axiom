"""同候選變更、回滾與跨 consumer 依賴；兩個負控制須由具名斷言偵測。"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild


def includes(source, origin):
    return re.sub(r'(^\s*#\s*include\s*)"([^"\n]+)"',
                  lambda m: m[1] + '"' + (origin.parent / m[2]).resolve().as_posix() + '"', source, flags=re.M)


class LoadResidual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = NativeBuild(kernel_only=True)
        cls.exe = cls.compile("baseline")

    @classmethod
    def compile(cls, name, invalidate=True, dependencies=True):
        build = cls.build
        world_path = ROOT / "geometry-app/native/world_validation.inc"
        world = includes(world_path.read_text(encoding="utf-8"), world_path)
        if not invalidate:
            anchor = "memset(memo->valid,0,sizeof memo->valid);"
            assert world.count(anchor) == 1
            world = world.replace(anchor, "/* 負控制：保留同一快取儲存的舊值。 */")
        world_copy = build.work / (name + "-world.inc")
        world_copy.write_text(world, encoding="utf-8")
        sources_path = ROOT / "geometry-app/native/reference_sources.inc"
        sources = includes(sources_path.read_text(encoding="utf-8"), sources_path)
        if not dependencies:
            anchor = "if(geo_eval_depend(ctx->sources,"
            assert sources.count(anchor) == 3
            sources = sources.replace(anchor, "if(false&&geo_eval_depend(ctx->sources,")
        sources_copy = build.work / (name + "-sources.inc")
        sources_copy.write_text(sources, encoding="utf-8")
        references_path = ROOT / "geometry-core/references.inc"
        references = includes(references_path.read_text(encoding="utf-8"), references_path)
        references = references.replace(sources_path.as_posix(), sources_copy.as_posix())
        references_copy = build.work / (name + "-references.inc")
        references_copy.write_text(references, encoding="utf-8")
        geometry_path = ROOT / "current_geometry.c"
        geometry = includes(geometry_path.read_bytes().decode("utf-8"), geometry_path)
        geometry = geometry.replace(world_path.as_posix(), world_copy.as_posix())
        geometry = geometry.replace(references_path.as_posix(), references_copy.as_posix())
        geometry_copy = build.work / (name + "-geometry.c")
        geometry_copy.write_text(geometry, encoding="utf-8")
        harness = (ROOT / "tests/geo261_load_residual_harness.c").read_text(encoding="utf-8")
        harness = harness.replace('../current_geometry.c', geometry_copy.as_posix())
        client = build.work / (name + "-client.c")
        client.write_text(harness, encoding="utf-8")
        return build.link("residual-" + name, [build.compile(client, "residual-" + name)])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=90)
        self.assertIn(result.returncode, (0, 1), "編譯錯誤、崩潰或受阻不算偵測：" + result.stderr)
        return result

    def passes(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)

    def test_same_candidate_move_delete_failed_read_and_rollback(self):
        self.passes("move-delete")

    def test_same_candidate_parameter_value_change_and_rollback(self):
        self.passes("parameter")

    def test_second_consumer_retains_placement_and_pose_edges_and_sealed_lookup(self):
        self.passes("consumers")

    def test_never_invalidate_mutant_reports_stale_footprint(self):
        self.passes("move-delete")
        exe = self.compile("never-invalidate", invalidate=False)
        result = self.case("move-delete", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:stale-footprint-after-move ", result.stderr)
        print("永不失效突變：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:stale-" in s), flush=True)
        result = self.case("parameter", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:stale-footprint-after-parameter ", result.stderr)
        print("永不失效突變（參數）：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:stale-" in s), flush=True)
        self.passes("move-delete")

    def test_cross_consumer_mutant_reports_missing_dependency(self):
        self.passes("consumers")
        exe = self.compile("cross-consumer", dependencies=False)
        result = self.case("consumers", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:cross-consumer-placement-edge-missing ", result.stderr)
        print("跨 consumer 共用突變：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:cross-" in s), flush=True)
        self.passes("consumers")


if __name__ == "__main__":
    unittest.main(verbosity=2)
