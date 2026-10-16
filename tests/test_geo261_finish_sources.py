"""Finish/fill/derived calculations use the actual candidate-local K graph.

Boundary checks are portable. Native setup and execution belong to the
serialized validation runner; a compiler failure or crash is never a kill.
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


class FinishSourceBoundary(unittest.TestCase):
    def test_public_policy_ownership_and_handle_lifetime(self):
        for name in ("finish.h", "finish.c", "derived_placement.h", "derived_placement.c", "finish_sources.h", "finish_sources.c"):
            text = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|ReferenceEval|ParameterSet)\b")
            self.assertNotIn("internal/", text)
            self.assertNotIn("geometry-app", text)
        source = (MODULE / "finish_sources.c").read_text(encoding="utf-8")
        create = source[source.index("WoodFinishSources *wood_finish_sources_create"):source.index("bool wood_finish_sources_bind_finish")]
        self.assertIn("geo_eval_register(", create)
        self.assertNotIn("geo_eval_source(", create)
        self.assertNotIn("geo_eval_describe(", create)
        self.assertNotIn("geo_eval_", source[source.index("void wood_finish_sources_destroy"):])
        self.assertNotIn("placement_write(", source)

    def test_actual_policy_dispatch_and_upstream_values_drive_geometry(self):
        source = (MODULE / "derived_placement.c").read_text(encoding="utf-8")
        direct = source[source.index("bool wood_dp_value_direct("):source.index("bool wood_dp_rebuild(")]
        self.assertLess(direct.index("placement_read("), direct.index("evaluation->height("))
        self.assertLess(direct.index("evaluation->height("), direct.index("wood_dp_values("))
        self.assertLess(direct.index("wood_dp_values("), direct.index("evaluation->frame("))
        self.assertNotIn("placement_write(", direct)
        provider = (MODULE / "finish_sources.c").read_text(encoding="utf-8")
        for function in ("wood_fs_check_direct", "wood_pf_values_direct", "wood_pf_field_direct", "wood_dp_value_direct", "wood_dp_height_direct", "wood_dp_frame_direct"):
            self.assertIn(function + "(", provider)
        self.assertIn("out->frame=value.as.frame", provider)
        self.assertIn("GeoFrame frame=d->frame", source)


CONTROLS = (
    ("panel-field-bypass", "finish", "return w->evaluation&&w->evaluation->field?", "return false?", "graph", "panel-field-dependency-edge"),
    ("derived-frame-bypass", "derived_placement", "if(w->evaluation&&w->evaluation->frame){", "if(false){", "graph", "derived-actual-input-edges"),
    ("definition-relation", "finish_sources", "wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)", "wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)", "graph", "derived-definition-edge"),
    ("parameter-edge-bypass", "finish_sources", "if(!ref.set||!s->tokens.parameter){", "if(true){", "shared", "shared-parameter-field-edges"),
    ("diagnostic-retry", "finish_sources", ".retry_failure=true", ".retry_failure=false", "diagnostics", "failed-policy-retries-original-diagnostic"),
)


class FinishSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("finish_sources.h", "finish_sources.c"):
            shutil.copy2(MODULE / name, build.woodworking / name)
        client = build.woodworking / "finish-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_finish_sources_harness.c", client)
        cls.client = build.compile(client, "finish-sources-client")
        cls.provider = build.compile(build.woodworking / "finish_sources.c", "finish-sources-provider-client")
        cls.exe = build.link("finish-sources-client", cls.objects(build))

    @classmethod
    def objects(cls, build, module=None, changed=None):
        return [cls.client, changed if module == "finish_sources" else cls.provider,
                changed if module == "finish" else build.wood_finish_object,
                changed if module == "derived_placement" else build.wood_derived_placement_object,
                build.wood_engineering_object, build.wood_engineering_sources_object,
                build.wood_section_profile_object, build.wood_panel_layout_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a graph verdict: " + result.stderr)
        return result

    def test_true_derived_geometry_exact_edges_canonical_definitions_and_memoization(self):
        result = self.case("graph")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_finish_rebuild_and_fill_fields_resolve_actual_geometry_sources(self):
        result = self.case("finish")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_shared_parameter_provider_and_transitive_ast_references(self):
        result = self.case("shared")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_diagnostic_order_retry_and_partial_write_parity_without_hooks(self):
        result = self.case("diagnostics")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_candidate_identity_stable_borrowed_regions_and_both_teardown_orders(self):
        result = self.case("lifetime")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_five_source_hook_controls_fail_the_named_graph_assertion(self):
        build = native()
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                baseline = self.case(case)
                self.assertEqual(0, baseline.returncode, baseline.stderr)
                original = build.woodworking / (module + ".c")
                before_bytes = original.read_bytes()
                source = before_bytes.decode("utf-8")
                self.assertEqual(1, source.count(before), "Control must match exactly once: " + name)
                path = build.woodworking / ("finish-control-" + name + ".c")
                path.write_text(source.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "finish-control-" + name)
                executable = build.link("finish-control-" + name, self.objects(build, module, changed))
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn("ASSERT:" + marker + ":", result.stderr)
                self.assertEqual(before_bytes, original.read_bytes(), "Baseline source is unchanged")
                restored = self.case(case)
                self.assertEqual(0, restored.returncode, restored.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
