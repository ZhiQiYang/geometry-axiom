"""Actual K parameter returns control W dimensions after legacy admission.

The native witness intercepts the real registered parameter provider only
after its original evaluator returns. It keeps raw storage at 3 while K
returns 17, then checks W's result, retained definitions and typed edges.
The actual H member-dimension entry point uses the same W object. Malformed
returns, callback diagnostics and pure material decoding have separate cases.
"""
import base64
import json
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


def encoded(value):
    return base64.b64encode(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).decode()


def product_scene():
    card = {"id": 4, "name": "raw-three", "nextFieldId": 8}
    field = {"parameterId": 4, "id": 7, "name": "length", "type": 0,
             "expression": {"op": "literal", "num": "3", "den": "1", "unit": "mm"}}
    timber = {"id": 1, "role": "boundary", "A": {"source": {"kind": "parameter", "parameterId": 4, "fieldId": 7}, "override": None}, "B": 40}
    return ("requires parameters/1\nrequires engineering-spec/1\nparameters begin\nparameters card " + encoded(card) +
            "\nparameters field " + encoded(field) + "\nparameters end\n"
            "surface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000\n"
            "spec x 500\nguide 1 1 v spec:x\nengineering timber " + encoded(timber) +
            "\nplace 1 on 1 at-face e0 +u +n\n")


ASSIGNMENT = "/* The callback checks admission; the graph owns the successful value. */\n    *out=value.as.quantity.num;return true;"
PARAMETER_EDGE = "geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value)"
PARAMETER_HOOK = "bool found=w->source_parameter?w->source_parameter(w->sources,s->parameter,value,w->error,w->error_capacity):w->parameter(w->user,s->parameter,value,w->error,w->error_capacity);"


class EngineeringParameterAuthorityBoundary(unittest.TestCase):
    def test_existing_scene_encodes_a_three_mm_parameter_and_exact_binding_identity(self):
        records = {line.split(" ", 2)[0] + " " + line.split(" ", 2)[1]: json.loads(base64.b64decode(line.split(" ", 2)[2]))
                   for line in product_scene().splitlines()
                   if line.startswith(("parameters card ", "parameters field ", "engineering timber "))}
        self.assertEqual({"op": "literal", "num": "3", "den": "1", "unit": "mm"}, records["parameters field"]["expression"])
        self.assertEqual({"kind": "parameter", "parameterId": 4, "fieldId": 7}, records["engineering timber"]["A"]["source"])
        self.assertEqual(7, records["parameters field"]["id"])

    def test_each_negative_control_targets_one_specific_existing_decision(self):
        source = (ROOT / "geometry-templates/woodworking/native/engineering_sources.c").read_text(encoding="utf-8")
        resolver = (ROOT / "geometry-templates/woodworking/native/engineering.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(ASSIGNMENT))
        self.assertEqual(1, source.count(PARAMETER_EDGE))
        self.assertEqual(1, resolver.count(PARAMETER_HOOK))


class EngineeringParameterAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "engineering-parameter-authority-client.c"
        shutil.copy2(ROOT / "tests/geo261_engineering_parameter_authority_harness.c", client)
        cls.client = build.compile(client, "engineering-parameter-authority-client")
        cls.dependencies = [build.wood_engineering_object, build.wood_engineering_sources_object, *build.kernel_objects()]
        cls.exe = build.link("engineering-parameter-authority-client", [cls.client, *cls.dependencies])
        cls.product_client = build.compile(ROOT / "tests/geo261_engineering_parameter_authority_harness.c", "engineering-parameter-authority-product-client",
            ["GEO261_ENGINEERING_PARAMETER_PRODUCT=1", "GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.product = build.link("engineering-parameter-authority-product-client", [cls.product_client, *build.product_objects()])
        cls.scene = build.work / "engineering-parameter-authority.scene"
        cls.scene.write_text(product_scene(), encoding="utf-8")

    def case(self, name, *, product=False, exe=None, marker=None):
        command = [str(exe or (self.product if product else self.exe)), name]
        if product:
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertIn(result.returncode, (0, 1), "Crash/build/setup failure is not a parameter-authority verdict: " + result.stderr)
        self.assertEqual(1 if marker else 0, result.returncode, result.stdout + "\n" + result.stderr)
        if marker:
            self.assertRegex(result.stderr, r"^ASSERT:" + re.escape(marker) + r":\d+\n$")
        return result

    def test_actual_seventeen_controls_dimension_while_legacy_cache_stays_three(self):
        self.case("authority")

    def test_original_callback_failure_precedes_K_and_preserves_partial_output_and_error(self):
        self.case("callback-failure")

    def test_wrong_return_kind_is_rejected_without_raw_fallback(self):
        self.case("kind")

    def test_wrong_return_unit_is_rejected_without_raw_fallback(self):
        self.case("unit")

    def test_fractional_return_is_rejected_without_truncation(self):
        self.case("fraction")

    def test_out_of_D1_return_is_rejected_before_replacing_admission_output(self):
        self.case("range")

    def test_K_evaluation_failure_retains_existing_diagnostic_behavior(self):
        self.case("source-failure")

    def test_actual_zero_is_accepted_for_grid_gap(self):
        self.case("gap-zero")

    def test_actual_zero_is_rejected_for_positive_member_dimension(self):
        self.case("positive-zero")

    def test_actual_negative_reaches_original_positive_target_rejection(self):
        self.case("negative")

    def test_malformed_return_diagnostic_respects_small_caller_buffer(self):
        self.case("small-error")

    def test_pure_material_decoder_preserves_null_missing_and_full_precision_decimal(self):
        self.case("material-decode")

    def test_pure_material_decoder_rejects_invalid_and_noncanonical_bytes_atomically(self):
        self.case("material-rejections")

    def test_actual_H_member_dimension_consumes_the_returned_K_parameter_value(self):
        self.case("product", product=True)

    def test_value_bypass_edge_kind_and_W_hook_controls_fail_exact_oracles(self):
        build = native()
        source = (build.woodworking / "engineering_sources.c").read_text(encoding="utf-8")
        resolver = (build.woodworking / "engineering.c").read_text(encoding="utf-8")
        controls = [
            ("returned-value", source, ASSIGNMENT, ASSIGNMENT.replace("*out=value.as.quantity.num;", ""),
             build.wood_engineering_sources_object, "engineering-parameter-actual-value-authority", "product-engineering-parameter-actual-value-authority"),
            ("edge-kind", source, PARAMETER_EDGE, PARAMETER_EDGE.replace("GEO_DEPENDENCY_VALUE_REQUIRED", "GEO_DEPENDENCY_DEFINITION_REQUIRED"),
             build.wood_engineering_sources_object, "engineering-parameter-value-required-edge", "engineering-parameter-value-required-edge"),
            ("W-hook", resolver, PARAMETER_HOOK, PARAMETER_HOOK.replace("w->source_parameter?", "false?"),
             build.wood_engineering_object, "engineering-parameter-actual-value-authority", "product-engineering-parameter-actual-value-authority"),
        ]
        for name, text, before, after, original, marker, product_marker in controls:
            with self.subTest(control=name):
                self.case("authority");self.case("product", product=True)
                self.assertEqual(1, text.count(before))
                path = build.woodworking / ("engineering-parameter-control-" + name + ".c")
                path.write_text(text.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "engineering-parameter-control-" + name)
                standalone = build.link("engineering-parameter-control-" + name, [self.client,
                    *[changed if obj == original else obj for obj in self.dependencies]])
                product = build.link("engineering-parameter-product-control-" + name, [self.product_client,
                    *[changed if obj == original else obj for obj in build.product_objects()]])
                self.case("authority", exe=standalone, marker=marker)
                self.case("product", exe=product, product=True, marker=product_marker)
                self.case("authority");self.case("product", product=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
