"""Public W child-grid policy with literal oracles and same-object controls.

Only the boundary class is portable. Native builds/runs belong to P1's queue.
Compile errors, unavailable execution and crashes never satisfy a control.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_subgrid_contract import rejection_reason

MODULE = ROOT / "geometry-templates/woodworking/native"
CONTROLS = (
    ("adjacency", "refs[i+1]==grid->cell_ref[axis][1]", "true", "adjacency", "adjacent-only"),
    ("positive-area", "if (!wood_grid_cell_has_area(p,out))", "if (false)", "area", "positive-area-not-bbox"),
    ("parent-count", "if (on!=n)", "if (false)", "cardinality", "parent-cardinality-locked"),
    ("missing-band", "if(staggered!=has_band)", "if(false)", "bands", "missing-band-rejected"),
    ("duplicate-child", "other->id!=grid->id && other->is_subgrid", "false && other->is_subgrid", "duplicate", "duplicate-child-rejected"),
)


class GridCellsBoundary(unittest.TestCase):
    def test_w_has_no_host_types_or_private_state_and_delegates_geometry_to_k(self):
        text = (MODULE / "grid_cells.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|ReferenceGrid|PlacementSurface|SpaceBoundarySurface|g_subgrid_before|world_find_grid|placement_local_bounds)\b")
        self.assertNotIn("internal/", text)
        self.assertEqual(["grid_application.h"], re.findall(r'^#include "([^"]+)"', text, re.M))
        for name in ("geo_lattice_coord", "geo_lattice_window", "geo_finite_sequence", "geo_interval_subdivide", "geo_region_set_intersects_rect_positive", "geo_alternating_shift"):
            self.assertIn(name + "(", text)

    def test_public_entries_and_explicit_baseline_are_present(self):
        source = (MODULE / "grid_cells.c").read_text(encoding="utf-8")
        header = (MODULE / "grid_application.h").read_text(encoding="utf-8")
        names = ("axis_lines", "valid", "cell_bounds", "axis_lines_in", "line_coord_in", "anchor_line_coord", "valid_in", "parent_count_valid", "world_valid", "family_fits", "lattice_coord", "lattice_coord_band")
        for name in names:
            self.assertRegex(source, r"\bbool wood_grid_" + name + r"\(")
            self.assertRegex(header, r"\bbool wood_grid_" + name + r"\(")
        self.assertIn("wood_grid_parent_count_valid(world->before", source)
        self.assertIn("wood_grid_parent_count_valid(w->before", source)


class WoodGridCells(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "grid-cells-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_cells_harness.c", path)
        cls.client = build.compile(path, "grid-cells-client")
        cls.exe = build.link("grid-cells-client", cls.objects(build, build.wood_grid_cells_object))

    @classmethod
    def objects(cls, build, changed):
        return [cls.client, changed, build.wood_grid_application_object, build.wood_grid_rules_object,
                build.wood_engineering_object, *build.kernel_objects()]

    def run_case(self, name, exe=None):
        return subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, encoding="utf-8", timeout=20)

    def succeeds(self, name, exe=None):
        result = self.run_case(name, exe)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("PASS " + name, result.stdout.strip())

    def test_finite_sources_odd_gap_and_declared_zero_lines(self):
        self.succeeds("finite")

    def test_canonical_min_max_and_strict_adjacent_boundaries(self):
        self.succeeds("adjacency")

    def test_exact_subdivision_and_child_index_diagnostics(self):
        self.succeeds("division")

    def test_holes_disconnected_components_and_positive_area(self):
        self.succeeds("area")

    def test_signed_lattice_identity_capacity_and_offscreen_lines(self):
        self.succeeds("lattice")

    def test_required_band_negative_parity_and_output_range(self):
        self.succeeds("bands")

    def test_duplicate_children_parent_role_and_stagger_error_order(self):
        self.succeeds("duplicate")

    def test_old_candidate_geometry_locks_finite_cardinality_only(self):
        self.succeeds("cardinality")

    def test_family_relocation_uses_baseline_and_leaves_inputs_unchanged(self):
        self.succeeds("family")

    def mutant(self, control):
        name, before, after, _, _ = control;build = native()
        text = (build.woodworking / "grid_cells.c").read_text(encoding="utf-8")
        self.assertEqual(1, text.count(before), name)
        source = build.woodworking / ("grid-cells-" + name + ".c")
        source.write_text(text.replace(before, after), encoding="utf-8")
        changed = build.compile(source, "grid-cells-" + name)
        return changed, build.link("grid-cells-mutant-" + name, self.objects(build, changed))

    def test_five_guard_removals_fail_the_named_independent_assertion(self):
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                case, label = control[3:]
                self.succeeds(case)
                _, mutant = self.mutant(control)
                run = self.run_case(case, mutant)
                self.assertEqual(1, run.returncode, "Crash/build/runtime errors are not a policy assertion: " + run.stderr)
                self.assertIn("ASSERT:" + label, run.stderr)
                self.succeeds(case)

    def product_adjacency(self, executable):
        with _bridge.BridgeSession(executable) as bridge:
            for line in ("surface 90 origin 0 0 0 u +x v +y outline 0,0 120,0 120,100 0,100",
                         "grid 10 on 90 main-along v u 0 30 60 120"):
                response = bridge.command("line " + line)
                if "preview" in response:
                    self.assertTrue(response["preview"]["valid"], response)
                    response = bridge.command("line confirm " + str(response["preview"]["token"]))
                self.assertTrue(response["ok"], response)
            before = bridge.command("dump")["text"]
            result = bridge.command("line subgrid 20 parent 10 cell u min line:2 v min max divisions u 3 v 4")
            accepted = result["ok"] or result.get("preview", {}).get("valid", False)
            if not accepted:
                self.assertIn("彼此相鄰", rejection_reason(result))
                self.assertEqual(before, bridge.command("dump")["text"])
            return accepted

    def test_actual_bridge_uses_same_adjacency_guard_object(self):
        build = native();baseline = build.bridge()
        self.assertFalse(self.product_adjacency(baseline))
        changed, _ = self.mutant(CONTROLS[0]);objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_grid_cells_object))
        mutant = build.link("grid-cells-mutant-bridge", [build.bridge_object, *[changed if obj == build.wood_grid_cells_object else obj for obj in objects]])
        self.assertTrue(self.product_adjacency(mutant))
        self.assertFalse(self.product_adjacency(baseline))


if __name__ == "__main__":
    unittest.main(verbosity=2)
