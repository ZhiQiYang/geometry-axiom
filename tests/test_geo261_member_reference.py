"""Actual W member reconstruction, role/pose and R6 selection policy.

Numeric expectations and callback-event oracles are authored independently.
Every guard control changes one actual W site; the boundary guard is also
linked into the real bridge. Compilation/crash/setup failures are not kills.
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

MODULE = ROOT / "geometry-templates/woodworking/native"


def body(source, name):
    match = re.search(r"\bstatic\s+[^;{}]*\b" + name + r"\([^;]*?\)\s*\{", source, re.S)
    if not match:
        raise AssertionError("Missing actual consumer: " + name)
    start = match.end()
    depth = 1
    at = start
    while depth:
        depth += (source[at] == "{") - (source[at] == "}")
        at += 1
    return source[start:at - 1]


class MemberReferenceBoundary(unittest.TestCase):
    def test_public_policy_accepts_explicit_facts_and_public_kernel_only(self):
        for filename in ("member_reference.h", "member_reference.c"):
            source = (MODULE / filename).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|TimberAnchor|PlacementSurface|SpaceBoundarySurface|ReferenceEval|g_parameter_error|g_engineering_error)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        source = (MODULE / "member_reference.c").read_text(encoding="utf-8")
        for symbol in ("geo_strip_intervals", "geo_region_contains_rect", "geo_rectangle_footprint",
                       "wood_stop_ref_candidates", "wood_stop_pick", "wood_member_boundary_props"):
            self.assertIn(symbol + "(", source)

    def test_actual_reference_and_main_consumers_delegate_the_policy(self):
        references = (ROOT / "geometry-core/references.inc").read_text(encoding="utf-8")
        main = (ROOT / "current_geometry.c").read_bytes().decode("utf-8").replace("\r\n", "\n")
        for name, target in (("reference_compute_timber", "wood_member_reference_compute"),
                             ("reference_place_geometry", "wood_member_reference_place")):
            actual = body(references, name)
            self.assertIn(target + "(", actual)
            self.assertNotRegex(actual, r"\b(?:for|while)\s*\(")
        for name, target in (("timber_place_a0_on_surface", "wood_member_place_a0"),
                             ("timber_boundary_role_check", "wood_member_boundary_role_check"),
                             ("surface_primary_axis_check", "wood_member_primary_axis_check"),
                             ("anchor_corner_from_rect", "wood_member_anchor_corner"),
                             ("resolve_auto_span", "wood_member_resolve_span")):
            actual = body(main, name)
            self.assertIn(target + "(", actual)
            self.assertNotIn("V_PRIMARY_AXIS", actual)
            self.assertNotIn("V_BOUNDARY_ROLE", actual)
            self.assertNotIn("geo_strip_intervals(", actual)
        compute = body(references, "reference_compute_timber")
        self.assertLess(compute.index("wood_member_reference_compute("), compute.index("reference_place_geometry("))


CONTROLS = (
    ("dependency-kind", "(void)w->evaluate_member(w->user,j,GEO_DEPENDENCY_EVALUATE_BEFORE);", "(void)w->evaluate_member(w->user,j,GEO_DEPENDENCY_VALUE_REQUIRED);", "dependencies", "dependency-order-kind"),
    ("zero-id", "for(int k=0;k<3;++k)if(ref_used[k])", "for(int k=0;k<3;++k)if(ref_used[k]&&refs[k]!=0)", "dependencies", "zero-identity-source-required"),
    ("earlier-order", "prior.anchor.order>=a->order", "prior.anchor.order>a->order", "dependencies", "equal-order-source-refused"),
    ("grid-axis", "||(a->ref_grid_axis==0)!=along", "||false", "anchors", "grid-coordinate-axis"),
    ("odd-width", "widths[0][0]=center-t->size_a/2;", "widths[0][0]=center-(t->size_a+1)/2;", "anchors", "odd-width-positive-side"),
    ("derived-height", "if(p.derived&&(t->size_b!=p.height||a->depth_side!=WOOD_DEPTH_POSITIVE_NORMAL))", "if(false)", "anchors", "derived-height-and-side"),
    ("collect-checks", "if(!w->boundary_role(w->user,p.id,&probe,&request,start,end,&rect,err,sizeof err))", "if(false&& !w->boundary_role(w->user,p.id,&probe,&request,start,end,&rect,err,sizeof err))", "candidates", "all-checks-recorded-in-order"),
    ("unique-candidate", "if(found!=1)", "if(found==0)", "candidates", "two-candidates-ambiguous"),
    ("primary-axis", "} else if (axis != primary_axis) {", "} else if (false) {", "roles", "primary-axis-unique"),
    ("boundary-fixed", "if (fixities[edge_index] != WOOD_STOP_FIXED)", "if (false)", "boundary", "boundary-fixed-required"),
    ("boundary-full-edge", "if (!covers_edge)", "if (false)", "boundary", "boundary-full-edge-required"),
    ("complete-component", "if(component==domain->count)return false;", "if(false)return false;", "poses", "pose-hole-complete-footprint"),
    ("free-pose-end", "if(wood_reference_max(rect.min_v,wood_reference_min(p.v,q.v))<wood_reference_min(rect.max_v,wood_reference_max(p.v,q.v))&&fixities[component][i]==WOOD_STOP_FREE)return false;", "if(false)return false;", "poses", "pose-free-end-refused"),
    ("contact-positive", "intervals[i].start < contact_hi &&\n                intervals[i].end > contact_lo", "intervals[i].start <= contact_hi &&\n                intervals[i].end >= contact_lo", "spans", "contact-positive-overlap"),
    ("complete-scope", "if (intervals[i].start>=scope_lo && intervals[i].end<=scope_hi)", "if (true)", "spans", "scope-never-clips-interval"),
    ("through-closed", "if (through >= intervals[i].start &&", "if (through > intervals[i].start &&", "spans", "through-closed-endpoint"),
    ("unique-stop", "if (hits > 1) {\n        snprintf(err, err_cap, \"跨距起點擋面歧義\");\n        return WOOD_SPAN_START_AMBIGUOUS;\n    }", "if (hits > 1) return WOOD_SPAN_OK;", "spans", "unique-start-stop"),
    ("between-contained", "if (!inside || (scope && (s<scope_lo || e>scope_hi)))", "if (false)", "spans", "between-cannot-cross-obstacle"),
)


class MemberReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "member-reference-client.c"
        shutil.copy2(ROOT / "tests/geo261_member_reference_harness.c", path)
        cls.client = build.compile(path, "member-reference-client")
        cls.exe = build.link("member-reference-client", cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None):
        return [cls.client, changed or build.wood_member_reference_object,
                build.wood_members_object, build.wood_supports_object, *build.kernel_objects()]

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a W verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_ordered_dependency_kinds_zero_identity_and_earlier_source_admission(self):
        self.assertEqual(0, self.case("dependencies").returncode)

    def test_line_grid_rule_axis_odd_width_scope_and_derived_side(self):
        self.assertEqual(0, self.case("anchors").returncode)

    def test_candidate_uniqueness_exact_keys_contact_sides_and_all_check_order(self):
        self.assertEqual(0, self.case("candidates").returncode)

    def test_primary_boundary_secondary_axis_priority_and_extra_member(self):
        self.assertEqual(0, self.case("roles").returncode)

    def test_boundary_fixed_full_edge_and_i5_diagnostic_precedence(self):
        self.assertEqual(0, self.case("boundary").returncode)

    def test_pose_eight_signed_corners_right_handed_frame_hole_and_component_atomicity(self):
        self.assertEqual(0, self.case("poses").returncode)

    def test_actual_strip_intervals_scope_contact_through_between_and_unique_stops(self):
        self.assertEqual(0, self.case("spans").returncode)

    def mutant(self, control):
        name, before, after, _, _ = control
        build = native()
        source = (build.woodworking / "member_reference.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Control must change exactly one actual site: " + name)
        path = build.woodworking / ("member-reference-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        return build.compile(path, "member-reference-" + name)

    def test_eighteen_guard_controls_fail_named_assertions(self):
        build = native()
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                self.assertEqual(0, self.case(control[3]).returncode)
                changed = self.mutant(control)
                executable = build.link("member-reference-mutant-" + control[0], self.objects(build, changed))
                result = self.case(control[3], executable)
                self.assertEqual(1, result.returncode, "Guard removal survived: " + control[0])
                self.assertIn("ASSERT:" + control[4], result.stderr)
                self.assertEqual(0, self.case(control[3]).returncode)

    def free_boundary_transaction(self, executable):
        with _bridge.BridgeSession(executable) as session:
            self.assertTrue(session.command("reset")["ok"])
            for command in ("boundary 1 outline 0,0 100,0 100,100 0,100 fixity X F F F",
                            "placement 1 on boundary 1 origin 0 0 0 u +x v +y", "timber 17 10 5 role boundary"):
                response = session.line(command)
                self.assertTrue(response["ok"], response)
            before = session.command("dump")["text"]
            response = session.line("place 17 on 1 at-face e0 +u +n")
            placed = response["ok"]
            if placed:
                self.assertIn("place 17 on 1 at-face e0", session.command("dump")["text"])
                members = session.command("objects")["timbers"]
                self.assertEqual([17], [item["id"] for item in members])
                self.assertTrue(members[0]["onBoundary"])
                self.assertTrue(members[0]["coversEdge"])
                self.assertEqual(0, members[0]["boundaryEdge"])
            else:
                self.assertIn("V_BOUNDARY_ROLE", response["error"])
                self.assertIn("e0 是自由邊", response["error"])
                self.assertEqual(before, session.command("dump")["text"])
                self.assertEqual([], session.command("objects")["timbers"])
            return placed

    def test_same_boundary_guard_controls_the_actual_atomic_bridge_transaction(self):
        build = native()
        baseline = build.bridge()
        self.assertFalse(self.free_boundary_transaction(baseline))
        control = next(item for item in CONTROLS if item[0] == "boundary-fixed")
        changed = self.mutant(control)
        executable = build.link("member-reference-boundary-product-client", self.objects(build, changed))
        result = self.case("boundary", executable)
        self.assertEqual(1, result.returncode)
        self.assertIn("ASSERT:boundary-fixed-required", result.stderr)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_member_reference_object))
        bridge = build.link("member-reference-boundary-product-bridge", [build.bridge_object,
            *[changed if obj == build.wood_member_reference_object else obj for obj in objects]])
        self.assertTrue(self.free_boundary_transaction(bridge))
        self.assertFalse(self.free_boundary_transaction(baseline))


if __name__ == "__main__":
    unittest.main(verbosity=2)
