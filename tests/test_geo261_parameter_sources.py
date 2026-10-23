"""Native parameter AST edges survive the actual H candidate lifecycle.

Standalone clients see only isolated public K headers. Fixed values, failures
and traces are asserted before evaluator parity. The same parameters.c mutant
retains correct values but must fail an edge assertion in both K and the actual
inline bridge candidate; crashes or build failures never count as kills.
"""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE as WOOD_SCENE


def encoded(value):
    return base64.b64encode(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).decode()


def parameter_graph_scene():
    # Use the existing atomic parameters DSL, including a forward cross-card
    # AST reference. The 7/3 mm leaf is legal; its geometric consumer uses the
    # exact 7 mm result, never a rounded leaf or a replacement literal.
    rows = ["requires parameters/1", "parameters begin"]
    for identifier in (1, 2):
        rows.append("parameters card " + encoded({"id": identifier, "name": "card-" + str(identifier), "nextFieldId": 2}))
    expressions = [
        {"op": "mul", "left": {"op": "ref", "parameterId": 2, "fieldId": 1},
         "right": {"op": "literal", "num": "3", "den": "1", "unit": "1"}},
        {"op": "literal", "num": "7", "den": "3", "unit": "mm"},
    ]
    for identifier, expression in enumerate(expressions, 1):
        rows.append("parameters field " + encoded({"parameterId": identifier, "id": 1,
                    "name": "length", "type": 0, "expression": expression}))
    return "\n".join(rows + ["parameters end"]) + "\n" + WOOD_SCENE + "guide 2 1 v param:1:1\n"


class ParameterSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "parameter-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_parameter_sources_harness.c", source)
        cls.client = build.compile(source, "parameter-sources-client")
        cls.dependencies = [build.parameter_sources_object, build.source_object,
                            build.codec_object, build.exact_object, build.geometry_object]
        cls.exe = build.link("parameter-sources-client", [cls.client, build.parameters_object, *cls.dependencies])
        cls.product_client = build.compile(ROOT / "tests/geo261_parameter_graph_product_harness.c",
            "parameter-graph-product-client", ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
            "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.product = build.link("parameter-graph-product-client", [cls.product_client, *build.product_objects()])
        cls.scene = build.work / "parameter-graph-product.scene"
        cls.scene.write_text(parameter_graph_scene(), encoding="utf-8")

    def run_case(self, name, *, exe=None, product=False, expected=0):
        command = [str(exe or (self.product if product else self.exe)), name]
        if product:
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a parameter-graph verdict: " + result.stderr)
        self.assertEqual(expected, result.returncode, result.stderr)
        if expected == 1:
            self.assertIn("ASSERT:parameter-ast-dependency-edge:", result.stderr,
                          "The mutant must fail the dependency assertion after its exact-value assertions pass")
        return result

    def test_diamond_retains_actual_ast_edges_and_exact_values(self):
        self.run_case("diamond")

    def test_count_ratio_definitions_and_dimension_units_remain_distinct(self):
        self.run_case("types")

    def test_missing_field_has_fixed_identity_trace_and_evaluator_parity(self):
        self.run_case("missing")

    def test_cycle_has_fixed_identity_trace_and_evaluator_parity(self):
        self.run_case("cycle")

    def test_recursive_depth_64_accepts_and_65_rejects_with_exact_trace(self):
        self.run_case("depth-stack")

    def test_cached_chain_depth_65_still_rejects_with_exact_trace(self):
        self.run_case("depth-cached")

    def test_closure_ignores_unrelated_bad_field_but_full_rebuild_rejects_it(self):
        self.run_case("closure")

    def test_snapshots_and_sealed_reads_keep_graph_store_and_live_isolated(self):
        self.run_case("snapshots")

    def test_real_candidate_retains_edges_through_preview_confirm_and_one_undo(self):
        self.run_case("preview", product=True)

    def test_product_current_values_evaluates_cloned_parameters_without_live_writes(self):
        self.run_case("read-only", product=True)

    def test_read_only_definition_edge_kind_control_fails_exact_edge_set(self):
        # Same six nodes and five edges, but FIELD/CARD reads become value-required:
        # the count oracle passes, so only the exact edge-set oracle can fail.
        build = native()
        self.run_case("read-only", product=True)
        original = build.kernel / "parameter_sources.c"
        before_bytes = original.read_bytes()
        source = before_bytes.decode("utf-8")
        needle = "GEO_DEPENDENCY_DEFINITION_REQUIRED,out);"
        self.assertEqual(1, source.count(needle), "Definition-edge control must target exactly one K read")
        changed_source = build.kernel / "parameter-sources-definition-edge-mutant.c"
        changed_source.write_text(source.replace(needle, "GEO_DEPENDENCY_VALUE_REQUIRED,out);"), encoding="utf-8")
        changed = build.compile(changed_source, "parameter-sources-definition-edge-mutant")
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.parameter_sources_object), "Exactly one K provider is replaced")
        product = build.link("parameter-graph-product-definition-edge-mutant", [self.product_client,
            *[changed if obj == build.parameter_sources_object else obj for obj in objects]])
        result = subprocess.run([str(product), "read-only", str(self.scene)], capture_output=True, text=True,
                                encoding="utf-8", timeout=30)
        self.assertEqual(1, result.returncode, "Crash/setup is not an edge-set verdict: " + result.stderr)
        self.assertRegex(result.stderr, r"\AASSERT:readonly-exact-native-parameter-edge-set:\d+\n\Z")
        self.assertEqual("", result.stdout)
        self.assertEqual(before_bytes, original.read_bytes(), "Mutation must not alter the baseline K source")
        self.run_case("read-only", product=True)

    def test_same_kernel_resolver_bypass_fails_standalone_and_actual_candidate_edge(self):
        build = native()
        self.run_case("diamond")
        self.run_case("preview", product=True)
        original = build.kernel / "parameters.c"
        before_bytes = original.read_bytes()
        source = before_bytes.decode("utf-8")
        needle = "if(e->resolve){"
        self.assertEqual(1, source.count(needle), "Resolver negative control must target exactly one native branch")
        changed_source = build.kernel / "parameters-graph-bypass-mutant.c"
        changed_source.write_text(source.replace(needle, "if(0){"), encoding="utf-8")
        changed = build.compile(changed_source, "parameters-graph-bypass-mutant")
        standalone = build.link("parameter-sources-bypass-mutant",
                                [self.client, changed, *self.dependencies])
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.parameters_object), "Exactly one K evaluator is replaced")
        self.assertEqual(1, objects.count(build.parameter_sources_object), "The provider is linked once and stays unchanged")
        product = build.link("parameter-graph-product-bypass-mutant", [self.product_client,
            *[changed if obj == build.parameters_object else obj for obj in objects]])
        self.run_case("diamond", exe=standalone, expected=1)
        self.run_case("preview", exe=product, product=True, expected=1)
        self.assertEqual(before_bytes, original.read_bytes(), "Mutation must not alter the baseline K source")
        # Restored controls use the unmodified shared K object in new processes.
        self.run_case("diamond")
        self.run_case("preview", product=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
