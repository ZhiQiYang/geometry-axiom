"""I2/I5 regressions in isolated K and the actual bridge, with removal controls.

The tests express the corrected SSOT behavior. A frozen predecessor run must
record its expected failures separately; legacy acceptance is not an oracle.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class RegionEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "region-edges-client.c"
        shutil.copy2(ROOT / "tests/geo261_region_edges_harness.c", source)
        cls.client = build.compile(source, "region-edges-client")
        cls.exe = build.link("region-edges-client", [cls.client, build.geometry_object])

    def case(self, name, exe=None):
        run = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(run.returncode, (0, 1), "native crash is not a geometry verdict: " + run.stderr)
        return run

    def check(self, name):
        run = self.case(name)
        self.assertEqual(0, run.returncode, run.stderr)

    def product_case(self, name, exe=None):
        lines = [line for line in (ROOT / "tests/fixtures" / name).read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        with _bridge.BridgeSession(exe or native().bridge()) as session:
            self.assertTrue(session.command("reset")["ok"])
            for line in lines[:-1]:
                response = session.line(line)
                self.assertTrue(response["ok"], (line, response))
            before = session.command("dump")
            response = session.line(lines[-1])
            after = session.command("dump")
            return response, before, after

    def rejected_product(self, name):
        response, before, after = self.product_case(name)
        self.assertFalse(response["ok"], response)
        self.assertEqual(before, after, "rejected transaction changed the world")

    def test_crossing_holes_have_positive_overlap_without_contained_vertices(self):
        self.check("crossing-holes")

    def test_hole_contacts_stay_invalid_and_rectangle_contacts_stay_valid(self):
        self.check("contact-controls")

    def test_unit_rectangles_exclude_hole_interiors_at_coordinate_limits(self):
        self.check("unit-rectangles")

    def test_unit_strips_keep_two_maximal_intervals_and_capacity_failure(self):
        self.check("unit-strips")

    def test_product_crossing_holes_rejected_without_mutation(self):
        self.rejected_product("geo261_region_crossing.scene")

    def test_product_unit_hole_placement_rejected_without_mutation(self):
        self.rejected_product("geo261_region_unit_hole.scene")

    def test_removing_hole_crossing_guard_breaks_kernel_and_product(self):
        build = native()
        self.check("crossing-holes")
        self.rejected_product("geo261_region_crossing.scene")
        client, bridge = build.mutant("geometry",
            "return false; /* GEO261_HOLE_EDGE_CROSSING */",
            "(void)0; /* removed hole crossing rejection */", self.client)
        self.assertEqual(1, self.case("crossing-holes", client).returncode)
        response, before, after = self.product_case("geo261_region_crossing.scene", bridge)
        self.assertTrue(response["ok"], response)
        self.assertNotEqual(before, after)
        self.check("crossing-holes")
        self.rejected_product("geo261_region_crossing.scene")

    def test_removing_hole_center_guard_breaks_kernel_strips_and_product(self):
        build = native()
        self.check("unit-rectangles")
        self.check("unit-strips")
        self.rejected_product("geo261_region_unit_hole.scene")
        client, bridge = build.mutant("geometry",
            "if (geo_loop_rect_center_inside(hole, min_u, min_v, max_u, max_v))",
            "if (0)", self.client)
        self.assertEqual(1, self.case("unit-rectangles", client).returncode)
        self.assertEqual(1, self.case("unit-strips", client).returncode)
        response, before, after = self.product_case("geo261_region_unit_hole.scene", bridge)
        self.assertTrue(response["ok"], response)
        self.assertNotEqual(before, after)
        self.check("unit-rectangles")
        self.rejected_product("geo261_region_unit_hole.scene")


if __name__ == "__main__":
    unittest.main(verbosity=2)
