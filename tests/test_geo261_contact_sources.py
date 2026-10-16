"""Actual W ordered-contact policy exposed through candidate-local K sources.

NativeBuild supplies isolated public K/W dependencies. One test-local hook can
change only returned FEATURE segments, proving collect consumes graph values.
Six negative controls require their exact normal ASSERT; build failures,
timeouts, native crashes and unavailable compilers never count as detection.
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
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native"
FEATURE_RETURN = "out->kind=GEO_SOURCE_FEATURE;out->as.feature=(GeoFeatureValue){record,WOOD_CONTACT_SOURCE_METADATA_SIZE,segment};return true;"
FEATURE_HOOK = "contact_test_transform_feature(&segment);" + FEATURE_RETURN
HOOK_DECLARATION = '#include "contact_sources.h"\nvoid contact_test_transform_feature(GeoSegment3 *);\n'


def instrument(source):
    if source.count(FEATURE_RETURN) != 1:
        raise AssertionError("Feature instrumentation must hit exactly one return")
    return HOOK_DECLARATION + source.replace(FEATURE_RETURN, FEATURE_HOOK)


CONTROLS = (
    ("policy-bypass", "contact_sources", "graph", "contact-collection-runs-real-facts-and-policy",
     "size_t count=wood_contact_collect_stops(&world,q->request.along_v,q->request.exclude,faces,q->cap);", "size_t count=0;"),
    ("feature-edge", "contact_sources", "graph", "contact-feature-requires-collection-value",
     "wood_contact_source_ref(s->token,WOOD_CONTACT_SOURCE_COLLECTION,id,0,&key),\n        GEO_DEPENDENCY_VALUE_REQUIRED,&collection)",
     "wood_contact_source_ref(s->token,WOOD_CONTACT_SOURCE_COLLECTION,id,0,&key),\n        GEO_DEPENDENCY_EVALUATE_BEFORE,&collection)"),
    ("query-reuse", "contact_sources", "evolving", "contact-evolving-placed-subset-is-fresh",
     "q->id=++s->sequence;", "q->id=1;++s->sequence;"),
    ("hidden-coordinates", "contact_sources", "feature-values", "contact-returned-feature-segment-consumed",
     "face.fixed=along_v?segment->start.y:segment->start.x;\n"
     "    face.lo=along_v?segment->start.x:segment->start.y;\n"
     "    face.hi=along_v?segment->end.x:segment->end.y;",
     "face.fixed=wood_contact_source_read_coord(metadata+24);\n"
     "    face.lo=wood_contact_source_read_coord(metadata+32);\n"
     "    face.hi=wood_contact_source_read_coord(metadata+40);"),
    ("placement-order", "contact_world", "ordering", "contact-placement-order-and-stable-ties",
     "if(previous<=order)break;", "if(true)break;"),
    ("failure-count", "contact_sources", "failures", "contact-failure-keeps-output-and-count",
     "WoodContactQuery *q=calloc(1,sizeof *q);if(!q)return false;",
     "*count=0;WoodContactQuery *q=calloc(1,sizeof *q);if(!q)return false;"),
)


class ContactSourcesBoundary(unittest.TestCase):
    def test_source_provider_has_no_host_or_private_store_dependencies(self):
        source = "\n".join((MODULE / name).read_text(encoding="utf-8") for name in ("contact_sources.h", "contact_sources.c"))
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertEqual(["contact_world.h", "source.h", "contact_sources.h"], re.findall(r'^\s*#include\s+"([^"]+)"', code, re.M))
        self.assertNotRegex(code, r"\b(?:World|TimberAnchor|PlacementSurface|ReferenceEval|SpaceBoundarySurface)\b")
        self.assertNotIn("internal/", code)
        self.assertNotIn("geometry-app", code)

    def test_test_hook_preserves_production_body_and_controls_hit_once(self):
        original = (MODULE / "contact_sources.c").read_text(encoding="utf-8")
        changed = instrument(original)
        self.assertEqual(original, changed[len(HOOK_DECLARATION):].replace(FEATURE_HOOK, FEATURE_RETURN))
        for name, module, _case, _marker, before, _after in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, (MODULE / (module + ".c")).read_text(encoding="utf-8").count(before))


class NativeContactSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        shutil.copy2(MODULE / "contact_sources.h", build.woodworking / "contact_sources.h")
        client = build.woodworking / "contact-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_contact_sources_harness.c", client)
        cls.client = build.compile(client, "contact-sources-client")
        cls.source = instrument((MODULE / "contact_sources.c").read_text(encoding="utf-8"))
        provider = build.woodworking / "contact-sources-instrumented.c"
        provider.write_text(cls.source, encoding="utf-8")
        cls.provider = build.compile(provider, "contact-sources-instrumented")
        cls.exe = cls.link("contact-sources-client")

    @classmethod
    def link(cls, name, module=None, changed=None):
        build = native()
        return build.link(name, [cls.client, changed if module == "contact_sources" else cls.provider,
            changed if module == "contact_world" else build.wood_contact_world_object,
            build.wood_contacts_object, build.wood_supports_object, build.placement_sources_object,
            build.placements_object, build.regions_object, build.source_object, build.geometry_object])

    def run_case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a contact verdict: " + result.stdout + result.stderr)
        return result

    def pass_case(self, name):
        result = self.run_case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_real_k_frame_region_box_values_feed_w_policy_and_typed_dependency_edges(self):
        self.pass_case("graph")

    def test_returned_feature_segments_control_both_local_uv_axis_outputs(self):
        self.pass_case("feature-values")

    def test_upstream_geometry_changes_candidate_isolation_and_borrowed_value_lifetime(self):
        self.pass_case("upstream")

    def test_actual_ordered_policy_preserves_placement_order_ties_and_cover_dedup(self):
        self.pass_case("ordering")

    def test_components_hole_indices_and_free_or_other_fixity_metadata_are_preserved(self):
        self.pass_case("components")

    def test_empty_and_evolving_queries_keep_dependencies_without_forcing_unplaced_members(self):
        self.pass_case("evolving")

    def test_zero_capacity_pair_admission_and_truncation_before_dedup_match_old_policy(self):
        self.pass_case("capacity")

    def test_failures_cycles_and_invalid_inputs_preserve_caller_outputs(self):
        self.pass_case("failures")

    def test_actual_h_contact_consumer_uses_box_origin_axes_and_original_member_identity(self):
        build = native()
        client = build.compile(ROOT / "tests/geo261_contact_pose_product_harness.c", "contact-pose-product",
                               ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
                                "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        executable = build.link("contact-pose-product", [client, *build.product_objects()])
        result = self.run_case("pose", executable)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS pose\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_six_negative_controls_fail_only_the_named_semantic_assertion(self):
        build = native()
        for name, module, case, marker, before, after in CONTROLS:
            with self.subTest(control=name):
                self.pass_case(case)
                source = self.source if module == "contact_sources" else (build.woodworking / "contact_world.c").read_text(encoding="utf-8")
                self.assertEqual(1, source.count(before), "Negative control must replace exactly one expression")
                path = build.woodworking / ("contact-source-control-" + name + ".c")
                path.write_text(source.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "contact-source-control-" + name)
                result = self.run_case(case, self.link("contact-source-control-" + name, module, changed))
                self.assertEqual(1, result.returncode, "Control did not fail a normal assertion: " + result.stdout + result.stderr)
                self.assertEqual("ASSERT:" + marker + "\n", result.stderr)
                self.assertEqual("", result.stdout)
                self.pass_case(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
