"""Unbound D28 applications retain their full validation dependency closure.

APP definitions remain metadata-only. The separate W check consumes the actual
APP definition, host definition, method and every enabled override, even with
no object bindings. D28's prohibition on parameter face overrides is unchanged.
"""
import base64
import hashlib
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


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def encoded(value):
    return base64.b64encode(canonical(value).encode()).decode()


def product_scene():
    material = {"id": "t", "version": 1, "kind": "timber", "name": "Timber", "A": 30, "B": 40}
    method = {"id": "m", "version": 1, "name": "Method"}
    application = {"id": "a", "placement_id": 1, "method": {"id": "m", "version": 1}, "overrides": {
        "gap": {"kind": "literal", "value": 0}, "primary.A": {"kind": "spec", "name": "width"},
        "secondary.B": {"kind": "material", "id": "t", "version": 1, "field": "B"}}}
    rows = ["requires engineering-spec/1",
            "surface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000", "spec width 3"]
    for kind, value in (("material", material), ("method", method)):
        rows.append("engineering " + kind + " " + encoded({"value": value, "fingerprint": hashlib.sha256(canonical(value).encode()).hexdigest()}))
    rows.append("engineering application " + encoded(application))
    return "\n".join(rows) + "\n"


CHECK_REQUEST = "if(!wood_source_definition_key(&key,s->tokens.version?5:2,a->id,0))return false;"
INSIDE_CHECK = "if(!a||!wood_eng_validate_application_direct(&s->context,a))return false;"
APP_READ = "EngApplication *a=wood_source_application_read(s,key.id);"
APP_EDGE = ("WoodDefinitionKey key;GeoSourceValue value;if(!wood_source_definition_key(&key,2,id,0))return NULL;\n"
            "    GeoSourceStatus status=geo_eval_source(s->evaluation,(GeoSourceRef){s->tokens.definition,&key,sizeof key},GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);")
NAMED_ASSIGNMENT = ("if(value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den!=1)return false;\n"
                    "    *out=value.as.quantity.num;return true;\n}\nstatic bool wood_source_parameter")
CONTROLS = (
    ("outside-check", "engineering_sources", (
        (CHECK_REQUEST, "if(s->tokens.version){const EngApplication *returned=wood_source_application_read(s,a->id);\n"
         "        if(!returned||!wood_eng_validate_application_direct(&s->context,returned))return false;}\n    " + CHECK_REQUEST),
        (INSIDE_CHECK, "if(!a)return false;")), "no-binding", "application-check-host-definition-edge", "product", "application-check-host-definition-edge"),
    ("APP-edge", "engineering_sources", ((APP_EDGE, APP_EDGE.replace("GEO_DEPENDENCY_DEFINITION_REQUIRED", "GEO_DEPENDENCY_VALUE_REQUIRED")),),
     "no-binding", "application-check-consumes-returned-definition", "product", "application-check-consumes-returned-definition"),
    ("unused-overrides", "engineering", (("for (int field=0;field<7;++field) if (a->overridden[field]) {",
      "for (int field=0;field<0;++field) if (a->overridden[field]) {"),),
     "no-binding", "application-check-all-unused-override-values", "product", "application-check-all-unused-override-values"),
    ("actual-APP", "engineering_sources", ((APP_READ, APP_READ + "\n            if(a)memcpy(a,wood_eng_application_direct(&s->context,key.id),sizeof *a);"),),
     "returned-definition", "application-returned-definition-controls-unused-override", None, None),
    ("actual-check", "engineering_sources", (("geo_json_free(&json);return ok&&valid!=0;", "geo_json_free(&json);return ok;"),),
     "check-false", "application-returned-check-result-controls-caller", None, None),
    ("actual-named", "engineering_sources", ((NAMED_ASSIGNMENT, NAMED_ASSIGNMENT.replace("*out=value.as.quantity.num;return true;",
      "return s->context.named_value(s->context.user,name,out);")),),
     "named-authority", "application-unused-returned-named-value-controls-validation", "product-zero", "application-product-unused-named-return-controls-validation"),
    ("inventory-side-effect", "engineering_sources", (("if(s->tokens.version){\n                EngApplication decoded;",
      "if(s->tokens.version){\n                if(!wood_eng_validate_application_direct(&s->context,a))return false;\n                EngApplication decoded;"),),
     "inventory", "application-inventory-does-not-run-checks-or-values", None, None),
)


class ApplicationClosureBoundary(unittest.TestCase):
    def test_product_fixture_has_only_legal_unbound_face_overrides(self):
        lines = product_scene().splitlines()
        self.assertFalse(any(line.startswith(("engineering timber ", "engineering grid ")) for line in lines))
        application = json.loads(base64.b64decode(next(line.split(" ", 2)[2] for line in lines if line.startswith("engineering application "))))
        self.assertEqual({"gap", "primary.A", "secondary.B"}, set(application["overrides"]))
        self.assertEqual({"literal", "spec", "material"}, {value["kind"] for value in application["overrides"].values()})
        self.assertIn("spec width 3", lines)

    def test_controls_have_unique_production_anchors_and_named_oracles(self):
        harness = (ROOT / "tests/geo261_application_closure_harness.c").read_text(encoding="utf-8")
        for name, module, replacements, case, marker, product, product_marker in CONTROLS:
            source = (ROOT / "geometry-templates/woodworking/native" / (module + ".c")).read_text(encoding="utf-8")
            with self.subTest(control=name):
                for before, after in replacements:
                    self.assertEqual(1, source.count(before))
                    self.assertNotEqual(before, after)
                self.assertEqual(1, harness.count('"' + marker + '"'))
                if product_marker:
                    self.assertEqual(1, harness.count('"' + product_marker + '"'))


class ApplicationClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "application-closure-client.c"
        shutil.copy2(ROOT / "tests/geo261_application_closure_harness.c", client)
        cls.client = build.compile(client, "application-closure-client")
        cls.objects = [build.wood_engineering_object, build.wood_engineering_sources_object, *build.kernel_objects()]
        cls.exe = build.link("application-closure-client", [cls.client, *cls.objects])
        cls.product_client = build.compile(ROOT / "tests/geo261_application_closure_harness.c", "application-closure-product-client",
            ["GEO261_APPLICATION_CLOSURE_PRODUCT=1", "GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.product = build.link("application-closure-product-client", [cls.product_client, *build.product_objects()])
        cls.scene = build.work / "application-closure.scene"
        cls.scene.write_text(product_scene(), encoding="utf-8")

    def case(self, name, *, exe=None, marker=None):
        product = name.startswith("product")
        command = [str(exe or (self.product if product else self.exe)), name]
        if product:
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(1 if marker else 0, result.returncode, "Crash/setup is not a verdict: " + result.stdout + result.stderr)
        if marker:
            self.assertEqual("ASSERT:" + marker + "\n", result.stderr)
        return result

    def test_definition_inventory_still_does_no_host_or_override_work(self):
        self.case("inventory")

    def test_unbound_application_check_owns_host_method_and_all_override_values(self):
        self.case("no-binding")

    def test_actual_named_return_controls_validation_of_an_unused_override(self):
        self.case("named-authority")

    def test_actual_APP_definition_controls_unbound_override_validation(self):
        self.case("returned-definition")

    def test_actual_false_check_result_is_consumed_by_caller(self):
        self.case("check-false")

    def test_malformed_check_schema_identity_and_boolean_are_rejected(self):
        for name in ("check-schema", "check-id", "check-boolean"):
            with self.subTest(case=name):
                self.case(name)

    def test_host_then_method_rejections_keep_the_original_order(self):
        for name in ("derived-first", "missing-host", "missing-method"):
            with self.subTest(case=name):
                self.case(name)

    def test_all_seven_enabled_overrides_keep_original_order_and_check_edges(self):
        self.case("all-slots")

    def test_parameter_face_override_still_has_the_original_D28_rejection(self):
        self.case("forbidden-parameter")

    def test_actual_H_unbound_application_has_a_placement_definition_dependency(self):
        self.case("product")

    def test_actual_H_rejects_the_returned_zero_even_without_any_object_binding(self):
        self.case("product-zero")

    def test_closure_and_actual_return_controls_fail_exact_oracles(self):
        build = native()
        for name, module, replacements, case, marker, product_case, product_marker in CONTROLS:
            with self.subTest(control=name):
                original = build.woodworking / (module + ".c")
                snapshot = original.read_bytes()
                text = snapshot.decode("utf-8").replace("\r\n", "\n")
                self.case(case)
                if product_case:
                    self.case(product_case)
                for before, after in replacements:
                    self.assertEqual(1, text.count(before))
                    text = text.replace(before, after)
                path = build.woodworking / ("application-closure-control-" + name + ".c")
                path.write_text(text, encoding="utf-8")
                changed = build.compile(path, "application-closure-control-" + name)
                target = build.wood_engineering_sources_object if module == "engineering_sources" else build.wood_engineering_object
                executable = build.link("application-closure-control-" + name, [self.client, *[changed if obj == target else obj for obj in self.objects]])
                self.case(case, exe=executable, marker=marker)
                if product_case:
                    executable = build.link("application-closure-product-control-" + name, [self.product_client,
                        *[changed if obj == target else obj for obj in build.product_objects()]])
                    self.case(product_case, exe=executable, marker=product_marker)
                self.assertEqual(snapshot, original.read_bytes())
                self.case(case)
                if product_case:
                    self.case(product_case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
