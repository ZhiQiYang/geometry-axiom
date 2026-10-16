"""W grid policy executes inside the candidate's actual typed K source graph.

Portable boundary checks do not compile. Native execution and the controls are
owned by the serialized validation lane; setup errors/crashes are never kills.
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


class GridSourceBoundary(unittest.TestCase):
    def test_public_ownership_candidate_binding_and_safe_lifetime(self):
        for name in ("grid_application.h", "grid_application.c", "grid_cells.c", "grid_rules.c", "grid_sources.h", "grid_sources.c"):
            text = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|ReferenceEval|ParameterSet)\b")
            self.assertNotIn("internal/", text)
            self.assertNotIn("geometry-app", text)
        source = (MODULE / "grid_sources.c").read_text(encoding="utf-8")
        create = source[source.index("WoodGridSources *wood_grid_sources_create"):source.index("bool wood_grid_sources_bind")]
        self.assertIn("geo_eval_register(", create)
        self.assertNotIn("geo_eval_source(", create)
        self.assertNotIn("geo_eval_describe(", create)
        self.assertNotIn("geo_eval_", source[source.index("void wood_grid_sources_destroy"):])
        self.assertIn("c->before!=b->before", source)
        self.assertIn("e->versions!=a->versions", source)

    def test_hooks_use_direct_policy_and_returned_typed_regions(self):
        source = (MODULE / "grid_sources.c").read_text(encoding="utf-8")
        for function in ("wood_grid_system_evaluate_direct", "wood_grid_binding_cache_direct", "wood_grid_application_evaluate_direct", "wood_grid_application_dimension_direct", "wood_grid_rule_line_direct", "wood_grid_rule_cell_direct", "wood_grid_cell_bounds", "wood_grid_line_coord_in_resolved", "wood_grid_anchor_line_coord_resolved"):
            self.assertIn(function + "(", source)
        self.assertIn("target->bounds=scope", source)
        self.assertIn("wood_grid_scope_read(&value,&scope)", source)
        self.assertIn("s->base.coordinate(s->base.user,ref,out)", source)
        self.assertIn("wood_grid_copy_binding_cache(g,&r->cache)", source)
        self.assertNotIn("memcmp(e,a,sizeof", source)


CONTROLS = (
    ("shared-parameter-bypass", "grid_sources", "if(!ref.set||!s->tokens.parameter){", "if(true){", "graph", "shared-parameter-edge"),
    ("definition-relation", "grid_sources", "wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition", "wood_grid_root_get(s,WOOD_GRID_SOURCE_SYSTEM_DEFINITION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&definition", "graph", "definition-relation-exact"),
    ("rule-cell-hook-bypass", "grid_rules", 'if(!strcmp(kind,"grid")&&ctx->evaluation&&ctx->evaluation->rule_cell)', "if(false)", "graph", "rule-line-cell-value-edge"),
    ("typed-cell-value", "grid_sources", "GeoRect2 q=r->scope;r->points[0]", "GeoRect2 q=r->scope;++q.min_u;++q.max_u;r->points[0]", "graph", "rule-cell-returned-region-drives-line"),
    ("typed-child-cell-value", "grid_sources", "GeoRect2 q=r->scope;r->points[0]", "GeoRect2 q=r->scope;++q.min_u;++q.max_u;r->points[0]", "child-value", "child-line-returned-region-drives-subdivision"),
    ("partial-cache-copy", "grid_sources", "if(ok||r->cache_attempts!=attempts)wood_grid_copy_binding_cache", "if(ok)wood_grid_copy_binding_cache", "diagnostics", "failed-binding-preserves-partial-cache-parity"),
    ("failed-diagnostic-retry", "grid_sources", ".retry_failure=true", ".retry_failure=false", "diagnostics", "failed-policy-retries-original-diagnostic"),
)


class GridSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("grid_sources.h", "grid_sources.c"):
            shutil.copy2(MODULE / name, build.woodworking / name)
        client = build.woodworking / "grid-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_sources_harness.c", client)
        cls.client = build.compile(client, "grid-sources-client")
        cls.provider = build.compile(build.woodworking / "grid_sources.c", "grid-sources-provider-client")
        cls.exe = build.link("grid-sources-client", cls.objects(build))

    @classmethod
    def objects(cls, build, module=None, changed=None):
        return [cls.client, changed if module == "grid_sources" else cls.provider,
                build.wood_grid_application_object, build.wood_grid_cells_object,
                changed if module == "grid_rules" else build.wood_grid_rules_object,
                build.wood_engineering_object, build.wood_engineering_sources_object,
                *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a source verdict: " + result.stderr)
        return result

    def test_real_parameter_binding_line_child_cell_and_rule_cell_edges(self):
        result = self.case("graph")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_engineering_panel_quantities_drive_actual_grid_coordinates(self):
        result = self.case("engineering")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_failure_diagnostic_order_partial_binding_caches_and_retry(self):
        result = self.case("diagnostics")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_failure_outputs_preserve_original_total_and_coordinate(self):
        result = self.case("failure-output")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_candidate_isolation_canonical_keys_borrowed_views_and_teardown(self):
        result = self.case("lifetime")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_seven_controls_fail_named_independent_assertions(self):
        build = native()
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                baseline = self.case(case)
                self.assertEqual(0, baseline.returncode, baseline.stderr)
                original = build.woodworking / (module + ".c")
                original_bytes = original.read_bytes()
                source = original_bytes.decode("utf-8")
                self.assertEqual(1, source.count(before), "Control must match exactly once: " + name)
                path = build.woodworking / ("grid-source-control-" + name + ".c")
                path.write_text(source.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "grid-source-control-" + name)
                executable = build.link("grid-source-control-" + name, self.objects(build, module, changed))
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn("ASSERT:" + marker + ":", result.stderr)
                self.assertEqual(original_bytes, original.read_bytes())
                restored = self.case(case)
                self.assertEqual(0, restored.returncode, restored.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
