"""來源圖索引的順序、碰撞、配置降級，以及必須命名重複的突變自證。"""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild


class SourceIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = NativeBuild(kernel_only=True)
        cls.harness = cls.build.work / "source-index-client.c"
        shutil.copy2(ROOT / "tests/geo261_source_index_harness.c", cls.harness)
        cls.exe = cls.build.link("source-index-client", [cls.build.compile(cls.harness, "source-index-client")])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True,
                                text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "原生崩潰或啟動失敗不是有效斷言：" + result.stderr)
        return result

    def passes(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)

    def test_many_binary_keys_collisions_identity_order_and_sealed_lookup(self):
        self.passes("nodes")

    def test_each_edge_field_deduplicates_in_linear_order_and_reset_rebuilds(self):
        self.passes("edges")

    def test_allocation_failure_falls_back_without_changing_existing_state(self):
        self.passes("allocation")

    def test_array_growth_retries_exact_size_and_preserves_state_on_memory(self):
        self.passes("growth")

    def test_missing_invalid_failed_cycle_and_output_statuses(self):
        self.passes("statuses")

    def control(self, target, case, verdict):
        self.passes(case)
        source = (self.build.kernel / "source.c").read_text(encoding="utf-8")
        marker = "geo_source_find_" + target + "("
        start = source.index("{", source.index(marker))
        # 僅在函式最前面插入永遠查不到；所有配置與插入路徑維持原碼。
        source = source[:start+1] + ("\nreturn SIZE_MAX;" if target == "node" else "\nreturn false;") + source[start+1:]
        work = self.build.work / ("mutant-source-" + target)
        work.mkdir()
        (work / "source.c").write_text(source, encoding="utf-8")
        client = work / "client.c"
        shutil.copy2(self.harness, client)
        name = "source-index-never-" + target
        exe = self.build.link(name, [self.build.compile(client, name)])
        result = self.case(case, exe)
        self.assertEqual(1, result.returncode, "突變必須由正常斷言偵測：" + result.stdout + result.stderr)
        self.assertRegex(result.stderr, rf"^ASSERT:duplicate-{verdict} line=\d+ expr=")
        self.assertEqual("", result.stdout)
        print(f"突變 {target}：結束碼 {result.returncode}；{result.stderr.strip()}", flush=True)
        self.passes(case)

    def test_never_find_node_mutant_reports_duplicate(self):
        self.control("node", "nodes", "node")

    def test_never_find_edge_mutant_reports_duplicate(self):
        self.control("edge", "edges", "edge")


if __name__ == "__main__":
    unittest.main(verbosity=2)
