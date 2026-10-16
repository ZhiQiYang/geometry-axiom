"""N1b public geometry behavior plus shared K/product containment negative control."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class NativeGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native()
        source=build.work / "geometry-client.c"
        shutil.copy2(ROOT / "tests/geo261_geometry_harness.c",source)
        cls.client=build.compile(source,"geometry-client")
        cls.exe=build.link("geometry-client",[cls.client,build.geometry_object])

    def case(self,name,exe=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),"native crash is not a geometric verdict: "+run.stderr)
        return run

    def check(self,name):
        run=self.case(name)
        self.assertEqual(0,run.returncode,run.stderr)

    def test_all_cardinal_frames_and_inverse_uv(self):self.check("frames")
    def test_concave_closed_containment_and_preserved_collinear_vertices(self):self.check("loops")
    def test_holes_closed_boundary_and_invalid_views(self):self.check("regions")
    def test_line_clipping_reports_capacity_without_partial_output(self):self.check("clipping")
    def test_box_outward_faces_footprint_and_projection(self):self.check("boxes")
    def test_complete_strip_intervals_multicomponent_holes_obstacles_and_capacity(self):self.check("strips")

    def product_notch(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command("reset")["ok"])
            return session.command("loadfile "+str(ROOT / "_ax_i5_notch_cell_corners_on_ring.scene"))

    def test_containment_negative_control_changes_kernel_and_actual_product(self):
        build=native()
        self.check("loops")
        control=self.product_notch(build.bridge())
        self.assertFalse(control["ok"],control)
        client,bridge=build.mutant("geometry",
            "if (!geo_loop_rect_center_inside(loop, min_u, min_v, max_u, max_v))",
            "if (0)",self.client)
        self.assertEqual(1,self.case("loops",client).returncode)
        broken=self.product_notch(bridge)
        self.assertTrue(broken["ok"],broken)
        self.check("loops")
        self.assertFalse(self.product_notch(build.bridge())["ok"])


if __name__=="__main__":
    unittest.main(verbosity=2)
