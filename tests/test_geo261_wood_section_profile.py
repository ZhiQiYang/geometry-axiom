"""Public W section-profile behavior and real bridge guard-removal witness.

Expected geometry/errors come from D35-D40, I43-I51, R36-R40 and the original
section-profile authoring/placement/validation functions. No Git is needed to
run this gate, and compilation/process failures are never counted as kills.
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


class SectionProfileBoundary(unittest.TestCase):
    def test_public_policy_uses_only_public_types_and_explicit_candidate_facts(self):
        for name in ("section_profile.h", "section_profile.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|ParameterSet|g_engineering_error|g_preview)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        self.assertEqual(["section_profile.h"], re.findall(r'^#include "([^"]+)"',
            (MODULE / "section_profile.c").read_text(encoding="utf-8"), re.M))
        header = (MODULE / "section_profile.h").read_text(encoding="utf-8")
        self.assertEqual(["engineering.h", "domain_values.h"], re.findall(r'^#include "([^"]+)"', header, re.M))

    def test_actual_host_delegates_authoring_geometry_placement_and_conversion(self):
        source = (ROOT / "geometry-core/section_profiles.inc").read_text(encoding="utf-8")
        names = ("sp_used", "sp_profile", "sp_member", "sp_run", "sp_coord", "sp_axis",
                 "sp_put_profile", "sp_put_member", "sp_put_run", "sp_point", "sp_outside_regions",
                 "sp_intersection", "sp_rebuild")
        for name in names:
            match = re.search(r"static [^\n]+\b" + name + r"\([^\n]+\)\s*\{([^{}]*)\}", source)
            self.assertIsNotNone(match, name)
            self.assertIn("wood_" + name + "(", match[1], name)
            self.assertNotRegex(match[1], r"\b(?:for|while)\s*\(", name)
        conversion = (ROOT / "geometry-core/section_profile_conversion.inc").read_text(encoding="utf-8")
        for name in ("begin_conversion", "host_json", "host", "conversion_fields"):
            self.assertIn("wood_sp_" + name + "(", conversion)
        self.assertIn("geo_parameters_evaluate_field(&w->parameters,source->parameter", source)
        self.assertIn("return eng_resolve(w,source,target,UINT32_MAX,0,out,NULL,0)", source)
        self.assertIn("geo_loop_rect_complement(&view,r,out,SP_OUTSIDE_MAX,&count)",
            (MODULE / "section_profile.c").read_text(encoding="utf-8"))


# Every tuple has a unique actual implementation target and a named assertion.
# The K complement control links its changed object through the same W caller.
CONTROLS = (
    ("panel-width", "section_profile", "m.width>=wood_sp_panel_spec.width_max", "false", "authoring", "panel-strict-width"),
    ("material-identity", "section_profile", "out->kind==ENG_MATERIAL && out->field!=(field?ENG_B:ENG_A)", "false", "authoring", "material-source-identity"),
    ("touching-overlap", "section_profile", "r->min_u<r->max_u&&r->min_v<r->max_v", "r->min_u<=r->max_u&&r->min_v<=r->max_v", "geometry", "overlap-edge-contact"),
    ("copied-host", "section_profile", "if(r->copied_host){", "if(false){", "placement", "placement-copied-independent"),
    ("derived-host", "section_profile", "if(derived)return wood_sp_error", "if(false)return wood_sp_error", "placement", "placement-derived-host"),
    ("placement-up", "section_profile", "r->frame.axis_v=wood_sp_scaled(r->up,-1);", "r->frame.axis_v=wood_sp_scaled(r->up,1);", "placement", "placement-frame-signs"),
    ("host-range", "section_profile", "if(!inside||!perpendicular||!origin)", "if(!perpendicular||!origin)", "placement", "placement-host-range"),
    ("conversion-plane", "section_profile", "bool plane=geo_vector_dot(delta,host->normal)==0", "bool plane=true", "conversion", "conversion-plane"),
    ("conversion-range", "section_profile", "range=geo_coord_in_range(p)&&geo_coord_in_range(q)&&wood_sp_region_point(region,(GeoPoint2){p,q})", "range=true", "conversion", "conversion-hole-capacity"),
    ("conversion-up", "section_profile", "bool legal_up=geo_vector_dot(up,r->frame.normal)==0&&geo_vector_dot(up,up)==1", "bool legal_up=true", "conversion", "conversion-up"),
    ("first-diagnostic", "section_profile", "if(!first[0])snprintf(first,cap", "if(true)snprintf(first,cap", "diagnostics", "diagnostics-first-error"),
    ("source-cache", "section_profile", "if(!dimensions)continue;", "if(false)continue;", "diagnostics", "diagnostics-source-cache"),
    ("run-range", "section_profile", "r->resolved=p&&r->length_resolved&&r->placement_resolved&&!r->range_error;", "r->resolved=p&&r->length_resolved&&r->placement_resolved;", "runs", "run-range-cache"),
    ("profile-capacity", "section_profile", "w->state->profile_count==SP_PROFILE_MAX", "w->state->profile_count==SP_PROFILE_MAX-1", "capacity", "capacity-profile-full"),
    ("remove-tail", "section_profile", "memset((unsigned char*)base+*count*bytes,0,bytes);", "(void)bytes;", "capacity", "capacity-tail-zero"),
    ("complement-last-gap", "geometry", "if(cursor<r->max_u){if(n==capacity)", "if(false){if(n==capacity)", "geometry", "notch-is-outside"),
)


class WoodSectionProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "section-profile-client.c"
        shutil.copy2(ROOT / "tests/geo261_section_profile_harness.c", path)
        cls.client = build.compile(path, "section-profile-client")
        cls.exe = build.link("section-profile-client",
            [cls.client, build.wood_section_profile_object, build.wood_engineering_object, *build.kernel_objects()])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a section-profile verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_authoring_panel_strict_width_and_material_source_identity(self):
        self.assertEqual(0, self.case("authoring").returncode)

    def test_exact_concave_complement_and_strict_positive_area_overlap(self):
        self.assertEqual(0, self.case("geometry").returncode)

    def test_selected_dimensions_errors_and_fixed_anchor_recomputation(self):
        self.assertEqual(0, self.case("sources").returncode)

    def test_live_copied_derived_hosts_and_exact_right_handed_frames(self):
        self.assertEqual(0, self.case("placement").returncode)

    def test_conversion_fields_all_reasons_and_unchanged_authored_run(self):
        self.assertEqual(0, self.case("conversion").returncode)

    def test_first_diagnostic_and_complete_partial_cache_rebuild(self):
        self.assertEqual(0, self.case("diagnostics").returncode)

    def test_unplaced_and_long_runs_positive_lengths_and_vertex_range(self):
        self.assertEqual(0, self.case("runs").returncode)

    def test_bounded_capacity_replacement_and_removal_compaction(self):
        self.assertEqual(0, self.case("capacity").returncode)

    def mutant(self, control):
        name, module, before, after, _, _ = control
        build = native()
        directory = build.kernel if module == "geometry" else build.woodworking
        source = (directory / (module + ".c")).read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Control must change exactly one real implementation site: " + name)
        path = directory / ("section-profile-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        return build.compile(path, "section-profile-" + name)

    def link_client(self, name, module, changed):
        build = native()
        kernel = build.kernel_objects()
        if module == "geometry":
            self.assertEqual(1, kernel.count(build.geometry_object))
            kernel = [changed if obj == build.geometry_object else obj for obj in kernel]
        policy = build.wood_section_profile_object if module == "geometry" else changed
        return build.link("section-profile-mutant-" + name,
            [self.client, policy, build.wood_engineering_object, *kernel])

    def test_sixteen_guard_controls_fail_the_named_assertion(self):
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                self.assertEqual(0, self.case(control[4]).returncode)
                changed = self.mutant(control)
                exe = self.link_client(control[0], control[1], changed)
                result = self.case(control[4], exe)
                self.assertEqual(1, result.returncode, "Guard removal survived: " + control[0])
                self.assertIn("ASSERT:" + control[5], result.stderr)
                self.assertEqual(0, self.case(control[4]).returncode)

    def preview_width(self, exe, suffix):
        build = native()
        with _bridge.BridgeSession(exe) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            profile = {"id": 1, "name": "width witness", "outline": [[0, 0], [1000, 0], [1000, 100], [0, 100]]}
            member = {"id": 1, "profileId": 1, "kind": "panel", "panelSpec": "calcium-silicate-6",
                      "width": 914, "orientation": "thickness-v", "u0": 0, "v0": 0}

            def preview(operations):
                read = bridge.command("section-profile-read")
                self.assertTrue(read["ok"], read)
                request = {"schema": "section-profile-transaction/1", "expectedRevision": read["revision"], "operations": operations}
                path = build.work / ("section-profile-width-" + suffix + ".json")
                path.write_text(json.dumps(request), encoding="utf-8")
                before = bridge.command("dump")["text"]
                response = bridge.command("section-profile-preview " + str(path))
                self.assertTrue(response["ok"], response)
                self.assertEqual(before, bridge.command("dump")["text"])
                return response["preview"]

            first = preview([{"op": "put-profile", "value": profile}, {"op": "put-member", "value": member}])
            self.assertTrue(first["valid"], first)
            self.assertTrue(bridge.command("section-profile-confirm " + str(first["token"]))["ok"])
            before = bridge.command("dump")["text"]
            result = preview([{"op": "put-member", "value": dict(member, width=915)}])
            if result["valid"]:
                self.assertTrue(bridge.command("section-profile-confirm " + str(result["token"]))["ok"])
                stored = bridge.command("section-profile-read")["state"]["members"][0]
                self.assertEqual(915, stored["value"]["width"])
                self.assertEqual([0, 0, 915, 6], stored["rect"])
            else:
                self.assertIn("V_PANEL_WIDTH", json.dumps(result))
                self.assertFalse(bridge.command("section-profile-confirm " + str(result["token"]))["ok"])
                self.assertEqual(before, bridge.command("dump")["text"])
            return result["valid"]

    def test_same_panel_width_guard_controls_actual_bridge_preview_and_commit(self):
        build = native()
        baseline = build.bridge()
        self.assertFalse(self.preview_width(baseline, "baseline"))
        changed = self.mutant(CONTROLS[0])
        client = self.link_client("panel-width-product", "section_profile", changed)
        self.assertIn("ASSERT:panel-strict-width", self.case("authoring", client).stderr)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_section_profile_object))
        bridge = build.link("section-profile-product-mutant-bridge", [build.bridge_object,
            *[changed if obj == build.wood_section_profile_object else obj for obj in objects]])
        self.assertTrue(self.preview_width(bridge, "mutant"))
        self.assertFalse(self.preview_width(baseline, "restored"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
