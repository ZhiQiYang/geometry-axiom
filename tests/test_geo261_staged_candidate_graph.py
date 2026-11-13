"""Seven actual H staged handlers must retain their real candidate source graph.

The old local-World path could validate in a nested candidate, discard that
resolver, and seal an empty outer graph. These cases inspect real evaluated
guide/member nodes, their spec edge and callback ownership before confirmation.
Confirmation must revalidate the same candidate and publish the reviewed dump.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_native_grid_product import source
from tests.test_geo261_wood_product import SCENE as WOOD_SCENE
from tests.test_grid_system_contract import system

# Existing product fixtures supply the DSL and geometry. Source 5 is the
# unstaggered subdivision variant already used in GridStoreProduct; source 6
# is the legacy finite system used in GridSystemContract. No model generator
# supplies an expected dependency graph or expected output coordinates.
SCENE = WOOD_SCENE + """boundary 71 outline 400,500 1600,500 1600,1300 400,1300
placement 71 on boundary 71 origin 0 0 0 u +x v +y
""" + source(5, "none", "repeat 7 120", "repeat -11 80") + "\n" + system(6) + "\n"


class StagedCandidateGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.scene = build.work / "staged-candidate-graph.scene"
        cls.scene.write_text(SCENE, encoding="utf-8")
        client = build.compile(ROOT / "tests/geo261_staged_graph_harness.c", "staged-candidate-graph-client",
            ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.exe = build.link("staged-candidate-graph-client", [client, *build.product_objects()])

    def case(self, name):
        result = subprocess.run([str(self.exe), name, str(self.scene)], capture_output=True,
                                text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a staged-graph verdict: " + result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_boundary_vertex_keys_keep_actual_outer_graph(self):
        self.case("boundary-keys")

    def test_moving_keyed_vertices_keeps_graph_and_confirm_validation_context(self):
        self.case("boundary-keyed")

    def test_grid_system_redeclaration_keeps_actual_outer_graph(self):
        self.case("grid-system")

    def test_finite_grid_system_application_keeps_actual_outer_graph(self):
        self.case("grid-system-application")

    def test_source_rule_creation_keeps_graph_and_allocates_key_once(self):
        self.case("grid-source-rule")

    def test_grid_binding_creation_keeps_actual_outer_graph(self):
        self.case("grid-binding")

    def test_grid_binding_application_keeps_actual_outer_graph(self):
        self.case("grid-binding-application")


if __name__ == "__main__":
    unittest.main(verbosity=2)
