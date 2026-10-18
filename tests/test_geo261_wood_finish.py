"""Actual W finish/fill policy plus K and bridge guard-removal witnesses.

Oracles are hand-calculated from D41-D44, I52-I56, R41-R43. Diagnostic
ordering is compatibility with the frozen pre-extraction finish/fill policy,
not an additional axiom. No runtime Git or embedded implementation is used.
"""
from pathlib import Path
import json
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

MODULE = ROOT / "geometry-templates/woodworking/native"
THICKNESS_POLICY_ERROR = "I52: panel-fill thickness must be explicitly set positive integer mm in D1; no rounding"
THICKNESS_SOURCE_ERROR = "I35: effective dimension violates its positive/nonnegative integer mm range"


class FinishBoundary(unittest.TestCase):
    def test_public_policy_depends_on_explicit_facts_and_public_kernel(self):
        for name in ("finish.h", "finish.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|ParameterSet|g_engineering_error|g_parameter_error|g_preview)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        source = (MODULE / "finish.c").read_text(encoding="utf-8")
        self.assertEqual(["finish.h", "section_profile.h", "grid.h"], re.findall(r'^#include "([^"]+)"', source, re.M))
        for service in ("geo_aabb_project_interval", "geo_loop_rect_intersection_area", "geo_loop_touches_rect",
                        "geo_region_clip_rect_minus_rects", "wood_panel_layout_build"):
            self.assertIn(service + "(", source)

    def test_actual_host_delegates_policy_and_preserves_rebuild_phase_order(self):
        finish = (ROOT / "geometry-core/finish_surfaces.inc").read_text(encoding="utf-8")
        fill = (ROOT / "geometry-core/panel_fill_layout.inc").read_text(encoding="utf-8")
        for source, names in ((finish, ("fs_name_check", "fs_used", "fs_index", "fs_find", "fs_obstacle_parse",
                                       "fs_obstacle_compare", "fs_obstacles_normalize", "fs_obstacle_view", "fs_check",
                                       "fs_reference_owner", "fs_from_json", "fs_put", "fs_delete", "fs_operation")),
                              (fill, ("pf_find", "pf_free", "pf_parse", "pf_values", "pf_region_view", "pf_clip_status",
                                      "pf_clip", "pf_build", "pf_rebuild", "pf_operation"))):
            for name in names:
                match = re.search(r"static [^\n]+\b" + name + r"\([^\n]+\)\s*\{([^{}]*)\}", source)
                self.assertIsNotNone(match, name)
                self.assertIn("wood_" + name + "(", match[1], name)
                self.assertNotRegex(match[1], r"\b(?:for|while)\s*\(", name)
        rebuild = re.search(r"static bool fs_rebuild\([^\n]+\)\s*\{(.*?)\n\}", finish, re.S)[1]
        self.assertLess(rebuild.index("wood_fs_rebuild("), rebuild.index("pf_rebuild("))
        self.assertLess(rebuild.index("pf_rebuild("), rebuild.index("dp_rebuild("))
        self.assertIn("wood_fs_load(", finish)
        self.assertIn("wood_pf_load(", fill)


# Changes remove actual policy checks. The panel-kind predicate occurs at both
# the batch and single-field entry points; that control removes both copies.
# K changes link through the same W consumer. Native setup is never a kill.
CONTROLS = (
    ("whole-name", "finish", "for(size_t i=0;i<n;){size_t k=geo_utf8_scalar", "for(size_t i=0;i<n&&i<FS_NAME_MAX;){size_t k=geo_utf8_scalar", "names", "name-entire-input-before-capacity"),
    ("duplicate-obstacle", "finish", "if(!wood_fs_obstacle_compare(&f->obstacles[i-1],&f->obstacles[i]))", "if(false)", "obstacles", "obstacle-duplicate"),
    ("projection-negative", "geometry", "out[0]=o-hi[c];out[1]=o-lo[c];", "out[0]=o-lo[c];out[1]=o-hi[c];", "obstacles", "projection-all-axis-signs"),
    ("subtract-holes", "finish", "area-=geo_loop_rect_intersection_area", "area+=geo_loop_rect_intersection_area", "relations", "relation-hole-interior-excluded"),
    ("closed-contact", "geometry", "geo_coord_min(a.u,b.u)<=u1&&u0<=geo_coord_max(a.u,b.u)&&geo_coord_min(a.v,b.v)<=v1&&v0<=geo_coord_max(a.v,b.v)", "geo_coord_min(a.u,b.u)<u1&&u0<geo_coord_max(a.u,b.u)&&geo_coord_min(a.v,b.v)<v1&&v0<geo_coord_max(a.v,b.v)", "relations", "relation-edge-touch-closed"),
    ("local-capacity", "finish", "if(!geo_coord_in_range(out->rect[i]))", "if(false)", "obstacles", "projection-local-capacity-before-boundary"),
    ("fractional-thickness", "versions", "if(field->literal[i]!='0')return GEO_VERSION_INTEGER;", "if(false)return GEO_VERSION_INTEGER;", "materials", "thickness-no-fractional-rounding"),
    ("panel-kind", "finish", "if(!m||m->kind!=0)", "if(!m)", "materials", "material-panel-kind-required"),
    ("positive-threshold", "finish", "if(x.num<=0)", "if(false)", "sources", "threshold-before-gap"),
    ("nonnegative-gap", "finish", "if(d->layout.gap<0)", "if(false)", "sources", "gap-nonnegative"),
    ("whole-pitch", "finish", "d->layout.stagger%geo_period_pitch(d->layout.size[p->stagger_axis],d->layout.gap)==0", "false", "sources", "stagger-not-whole-pitch"),
    ("open-layer", "finish", "d->obstacles[i].q[0]<d->t", "d->obstacles[i].q[0]<=d->t", "layout", "layer-open-depth-and-positive-area"),
    ("finish-capacity", "finish", "if(s->count>=FS_MAX)return wood_fs_capacity_error", "if(s->count>=FS_MAX-1)return wood_fs_capacity_error", "capacity", "finish-exact-capacity"),
    ("scoped-operation", "finish", "if(w->state->host_count&&(", "if(true&&(", "operations", "operation-scoped-without-host"),
)


class WoodFinish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "finish-client.c"
        shutil.copy2(ROOT / "tests/geo261_finish_harness.c", path)
        cls.client = build.compile(path, "finish-client")
        cls.exe = build.link("finish-client", cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None, module=None):
        kernel = build.kernel_objects()
        if module in ("geometry", "versions"):
            original = getattr(build, module + "_object")
            if kernel.count(original) != 1:
                raise AssertionError("K " + module + " object must occur once")
            kernel = [changed if obj == original else obj for obj in kernel]
        policy = changed if module == "finish" else build.wood_finish_object
        return [cls.client, policy, build.wood_section_profile_object, build.wood_engineering_object,
                build.wood_panel_layout_object, *kernel]

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a finish verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_complete_utf8_validation_before_byte_capacity_and_diagnostic_kind(self):
        self.assertEqual(0, self.case("names").returncode)

    def test_canonical_typed_obstacles_all_signed_projection_axes_and_local_capacity(self):
        self.assertEqual(0, self.case("obstacles").returncode)

    def test_holes_concavity_positive_area_and_closed_edge_point_contact(self):
        self.assertEqual(0, self.case("relations").returncode)

    def test_fixed_material_version_explicit_exact_thickness_and_axis_identity(self):
        self.assertEqual(0, self.case("materials").returncode)

    def test_parameter_callback_order_rational_threshold_gap_stagger_and_dual_errors(self):
        self.assertEqual(0, self.case("sources").returncode)

    def test_authored_put_delete_compaction_typed_references_and_scoped_operations(self):
        self.assertEqual(0, self.case("operations").returncode)

    def test_actual_kernel_clip_layout_open_layer_cuts_and_failed_result_cleanup(self):
        self.assertEqual(0, self.case("layout").returncode)

    def test_exact_capacities_replacement_scene_duplicates_and_tail_zeroing(self):
        self.assertEqual(0, self.case("capacity").returncode)

    def mutant(self, control):
        name, module, before, after, _, _ = control
        build = native()
        directory = build.kernel if module in ("geometry", "versions") else build.woodworking
        source = (directory / (module + ".c")).read_text(encoding="utf-8")
        self.assertEqual(2 if name == "panel-kind" else 1, source.count(before),
                         "Control must change its declared actual sites: " + name)
        path = directory / ("finish-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        return build.compile(path, "finish-" + name)

    def test_fourteen_guard_controls_fail_the_named_assertion(self):
        build = native()
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                self.assertEqual(0, self.case(control[4]).returncode)
                changed = self.mutant(control)
                exe = build.link("finish-mutant-" + control[0], self.objects(build, changed, control[1]))
                result = self.case(control[4], exe)
                self.assertEqual(1, result.returncode, "Guard removal survived: " + control[0])
                self.assertIn("ASSERT:" + control[5], result.stderr)
                self.assertEqual(0, self.case(control[4]).returncode)

    def preview_panel_thickness(self, exe, suffix, *, thickness="9.5", expected_message=THICKNESS_POLICY_ERROR):
        build = native()
        with _bridge.BridgeSession(exe) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            scene = build.work / ("finish-thickness-" + suffix + ".scene")
            scene.write_text("boundary 8 outline 0,0 250,0 250,250 0,250 kind room_plan\n", encoding="utf-8")
            response = bridge.command("loadfile " + str(scene))
            self.assertTrue(response["ok"], response)

            def snapshot():
                return bridge.command("dump")["text"], bridge.command("panel-fill-read")["revision"]

            def preview(kind, operations):
                path = build.work / ("finish-" + kind + "-" + suffix + ".json")
                request = {"schema": kind + "-transaction/1", "expectedRevision": snapshot()[1], "operations": operations}
                path.write_text(json.dumps(request), encoding="utf-8")
                before = snapshot()
                response = bridge.command(kind + "-preview " + str(path))
                self.assertTrue(response["ok"], response)
                self.assertEqual(before, snapshot(), "Preview must not change authored world or revision")
                return response["preview"]

            material = {"id": "pf-board", "version": 1, "name": "board", "kind": "panel",
                        "width": 100, "length": 100, "thickness": thickness}
            parameter = {"id": 90, "name": "threshold", "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "8"}]}
            result = preview("engineering", [{"op": "publish-material", "value": material}, {"op": "put-parameter", "value": parameter}])
            self.assertTrue(result["valid"], result)
            self.assertTrue(bridge.command("engineering-confirm " + str(result["token"]))["ok"])
            finish = {"id": 1, "name": "finish", "boundaryId": 8, "frame": {"origin": [0, 0, 0], "U": "+X", "V": "+Y", "N": "+Z"},
                      "structureSide": 1, "obstacles": []}
            result = preview("panel-fill", [{"op": "put-finish-surface", "value": finish}])
            self.assertTrue(result["valid"], result)
            self.assertTrue(bridge.command("panel-fill-confirm " + str(result["token"]))["ok"])
            fill = {"id": 1, "finishSurfaceId": 1, "panel": {"id": "pf-board", "version": 1}, "lengthAlong": "v",
                    "origin": [0, 0], "gap": 3, "pattern": "straight", "threshold": {"parameterId": 90, "fieldId": 1}}
            before = snapshot()
            result = preview("panel-fill", [{"op": "put-panel-fill", "value": fill}])
            self.assertEqual(expected_message is None, result["valid"], result)
            if result["valid"]:
                self.assertTrue(bridge.command("panel-fill-confirm " + str(result["token"]))["ok"])
                stored = bridge.command("panel-fill-read")["state"]["panelFills"][0]
                self.assertEqual(9, stored["derived"]["thickness"])
                self.assertEqual(9, stored["derived"]["tileCount"])
            else:
                violation = result["violations"][0]
                self.assertEqual("INVALID", violation["status"])
                self.assertEqual("PANEL_FILL_INVALID", violation["code"])
                self.assertEqual(expected_message, violation["message"])
                self.assertEqual(expected_message.split(":", 1)[0], violation["clause"])
                self.assertFalse(bridge.command("panel-fill-confirm " + str(result["token"]))["ok"])
                self.assertEqual(before, snapshot())
            return result["valid"]

    def test_fractional_thickness_guards_preserve_actual_preview_and_commit_atomicity(self):
        build = native()
        baseline = build.bridge()
        self.assertFalse(self.preview_panel_thickness(baseline, "baseline"))
        changed = self.mutant(CONTROLS[6])
        client = build.link("finish-fraction-product-client", self.objects(build, changed, "versions"))
        result = self.case("materials", client)
        self.assertEqual(1, result.returncode)
        self.assertIn("ASSERT:thickness-no-fractional-rounding", result.stderr)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.versions_object))
        bridge = build.link("finish-fraction-product-bridge", [build.bridge_object,
            *[changed if obj == build.versions_object else obj for obj in objects]])
        # 單點突變仍由真實 typed version source 的 19/2 mm 值擋下。
        self.assertFalse(self.preview_panel_thickness(bridge, "mutant", expected_message=THICKNESS_SOURCE_ERROR))
        # 原有成功確認、厚度 9 與九片斷言移至合法整數厚度，保留正控制。
        self.assertTrue(self.preview_panel_thickness(bridge, "mutant-integer", thickness="9.000", expected_message=None))
        self.assertFalse(self.preview_panel_thickness(baseline, "restored"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
