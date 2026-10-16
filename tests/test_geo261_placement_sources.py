"""K placement/region sources consume typed upstream values and retain edges.

The standalone client uses the shared isolated NativeBuild and links only K
placement_sources, placements, regions, source and geometry objects. Exact
callback-value and region-edge negative controls preserve the other behavior;
only their named ASSERT with exit 1 counts, never a build error or native crash.
"""
from __future__ import annotations

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

KERNEL = ROOT / "geometry-core/kernel"
CONTROLS = (
    (
        "binding-value", "placement_sources", "binding-values", "placement-binding-consumes-upstream-frame",
        "if(s->binding&&s->binding(s->user,id,kind,&upstream))\n"
        "        return geo_eval_source(graph,upstream,GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;",
        "if(s->binding&&s->binding(s->user,id,kind,&upstream)){\n"
        "        GeoSourceValue ignored;\n"
        "        if(geo_eval_source(graph,upstream,GEO_DEPENDENCY_VALUE_REQUIRED,&ignored)!=GEO_SOURCE_OK)return false;\n"
        "    }",
    ),
    (
        "region-edge", "placement_sources", "region-edge", "placement-region-reference-edge",
        "return geo_eval_source(graph,geo_region_source_ref(s->region_token,p->region_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;",
        "out->kind=GEO_SOURCE_REGION_SET;\n"
        "        return geo_placement_domain_view(p,s->regions,&s->placement_views[i],&out->as.regions);",
    ),
    (
        "batch-invalid", "source", "batch-invalid", "batch-invalid-second-rejected",
        "if(!p->describe||!p->evaluate||!p->name_space||!*p->name_space||!p->implementation_fingerprint||!*p->implementation_fingerprint)return false;",
        "if(!p->evaluate||!p->name_space||!*p->name_space||!p->implementation_fingerprint||!*p->implementation_fingerprint)return false;",
    ),
    (
        "batch-duplicate", "source", "batch-duplicate", "batch-duplicate-second-rejected",
        "if(providers[i].token==p->token||!strcmp(providers[i].name_space,p->name_space))return false;",
        "if(false)return false;",
    ),
    (
        "batch-closed", "source", "batch-closed", "batch-used-or-sealed-graph-rejected",
        "if(!ctx||ctx->started||ctx->sealed||!providers||!count||count>SIZE_MAX/sizeof *providers-ctx->provider_count)return false;",
        "if(!ctx||!providers||!count||count>SIZE_MAX/sizeof *providers-ctx->provider_count)return false;",
    ),
)


class PlacementSourcesBoundary(unittest.TestCase):
    def test_public_provider_family_has_only_neutral_kernel_dependencies(self):
        source = "\n".join((KERNEL / name).read_text(encoding="utf-8")
                           for name in ("placement_sources.h", "placement_sources.c"))
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertEqual(["placements.h", "source.h", "placement_sources.h"],
                         re.findall(r'^\s*#include\s+"([^"]+)"', code, re.M))
        self.assertNotRegex(code, r"\b(?:World|AppWorld|Timber|woodworking|FinishSurface|world_revalidate)\b")

    def test_every_negative_control_hits_exactly_one_live_expression(self):
        for name, module, _case, _marker, before, _after in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, (KERNEL / (module + ".c")).read_text(encoding="utf-8").count(before))


class NativePlacementSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "placement-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_placement_sources_harness.c", source)
        cls.client = build.compile(source, "placement-sources-client")
        cls.objects = {"placement_sources": build.placement_sources_object, "source": build.source_object}
        cls.exe = cls.link("placement-sources-client", cls.objects)

    @classmethod
    def link(cls, name, objects):
        build = native()
        return build.link(name, [cls.client, objects["placement_sources"], objects["source"],
                                 build.placements_object, build.regions_object, build.geometry_object])

    def run_case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1),
                      "Native crash/setup failure is not a placement-source verdict: " + result.stdout + result.stderr)
        return result

    def pass_case(self, name):
        result = self.run_case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_exact_binary_keys_decode_full_uint32_and_preserve_failed_outputs(self):
        self.pass_case("keys")

    def test_actual_frame_rectangle_and_region_leaves_have_exact_typed_metadata(self):
        self.pass_case("leaves")

    def test_region_reference_consumes_core_region_and_records_required_value_edge(self):
        self.pass_case("region-edge")

    def test_empty_region_set_ordered_components_and_borrowed_holes_remain_stable(self):
        self.pass_case("views")

    def test_changed_upstream_frame_and_region_values_reach_candidate_results(self):
        self.pass_case("binding-values")

    def test_declined_binding_uses_explicit_values_and_region_reference_edge(self):
        self.pass_case("binding-declines")

    def test_wrong_typed_binding_or_failed_provider_preserves_output_bytes(self):
        self.pass_case("typed-failures")

    def test_missing_malformed_unresolved_and_unseen_sealed_sources_preserve_output(self):
        self.pass_case("missing-outputs")

    def test_same_source_keys_in_different_candidates_cannot_share_values_or_graphs(self):
        self.pass_case("isolation")

    def test_graph_and_provider_handle_support_both_destruction_orders(self):
        self.pass_case("destroy-orders")

    def test_invalid_second_batch_provider_leaves_existing_registry_and_bindings_unchanged(self):
        self.pass_case("batch-invalid")

    def test_duplicate_second_token_or_namespace_never_registers_partial_batch(self):
        self.pass_case("batch-duplicate")

    def test_batch_metadata_is_owned_and_used_or_sealed_graphs_reject_registration(self):
        self.pass_case("batch-closed")

    def test_placement_family_second_provider_collision_never_leaks_region_provider(self):
        self.pass_case("family-atomic")

    def control(self, selected):
        name, module, case, marker, before, after = next(c for c in CONTROLS if c[0] == selected)
        self.pass_case(case)
        build = native()
        original = (build.kernel / (module + ".c")).read_text(encoding="utf-8")
        self.assertEqual(1, original.count(before), "Negative control must hit one real expression")
        path = build.work / ("placement-sources-" + name + ".c")
        path.write_text(original.replace(before, after), encoding="utf-8")
        objects = dict(self.objects)
        objects[module] = build.compile(path, "placement-sources-" + name)
        result = self.run_case(case, self.link("placement-sources-" + name, objects))
        self.assertEqual(1, result.returncode, "Control did not fail a normal assertion: " + result.stdout + result.stderr)
        self.assertEqual("ASSERT:" + marker + "\n", result.stderr)
        self.assertEqual("", result.stdout)
        self.pass_case(case)

    def test_binding_value_discard_control_fails_named_consumption_assertion(self):
        self.control("binding-value")

    def test_same_geometry_without_region_edge_control_fails_named_edge_assertion(self):
        self.control("region-edge")

    def test_invalid_second_provider_guard_control_fails_named_batch_assertion(self):
        self.control("batch-invalid")

    def test_duplicate_second_provider_guard_control_fails_named_batch_assertion(self):
        self.control("batch-duplicate")

    def test_used_or_sealed_registration_guard_control_fails_named_batch_assertion(self):
        self.control("batch-closed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
