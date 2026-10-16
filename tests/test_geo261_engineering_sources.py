"""W engineering decisions use real typed K source nodes in one candidate.

Fixed dimensions, canonical version content, exact edge kinds and established
error order are checked independently of no-hook parity. The same W hook-bypass
object must lose its quantity edge in isolated W/K and the actual bridge while
all earlier numeric assertions still pass. No crash or build error is a kill.
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


def engineering_product_scene():
    material = {"id": "t", "version": 1, "kind": "timber", "name": "Member", "A": 30, "B": 40}
    record = {"fingerprint": hashlib.sha256(canonical(material).encode()).hexdigest(), "value": material}
    timber = {"id": 1, "role": "boundary", "A": {"source": {"kind": "material", "id": "t", "version": 1, "field": "A"}, "override": None}, "B": 40}
    encode = lambda value: base64.b64encode(canonical(value).encode()).decode()
    return ("requires engineering-spec/1\nengineering material " + encode(record) +
            "\nsurface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000\n"
            "spec x 500\nguide 1 1 v spec:x\nengineering timber " + encode(timber) +
            "\nplace 1 on 1 at-face e0 +u +n\n")


class EngineeringSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "engineering-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_engineering_sources_harness.c", client)
        cls.client = build.compile(client, "engineering-sources-client")
        cls.dependencies = [build.wood_engineering_sources_object, *build.kernel_objects()]
        cls.exe = build.link("engineering-sources-client", [cls.client, build.wood_engineering_object, *cls.dependencies])
        cls.product_client = build.compile(ROOT / "tests/geo261_engineering_sources_harness.c", "engineering-sources-product-client",
            ["GEO261_ENGINEERING_PRODUCT=1", "GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.product = build.link("engineering-sources-product-client", [cls.product_client, *build.product_objects()])
        cls.scene = build.work / "engineering-sources-product.scene"
        cls.scene.write_text(engineering_product_scene(), encoding="utf-8")

    def case(self, name, *, exe=None, product=False, expected=0):
        command = [str(exe or (self.product if product else self.exe)), name]
        if product:
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not an engineering-graph verdict: " + result.stderr)
        self.assertEqual(expected, result.returncode, result.stderr)
        if expected == 1:
            self.assertIn("ASSERT:engineering-source-dependency-edge:", result.stderr,
                          "Mutation must fail the exact source edge after its value assertions pass")
        return result

    def test_material_definition_source_binding_and_actual_memoized_value(self):
        self.case("material")

    def test_application_method_retains_selected_and_unused_material_identities(self):
        self.case("application")

    def test_face_and_object_overrides_select_active_values_without_losing_base_identity(self):
        self.case("overrides")

    def test_specs_and_parameter_ast_use_shared_kernel_providers(self):
        self.case("shared")

    def test_original_identity_errors_precede_invalid_override_values(self):
        self.case("identity-errors")

    def test_rebuild_keeps_original_error_order_and_no_hook_write_parity(self):
        self.case("rebuild-errors")

    def test_actual_bridge_pose_consumes_candidate_binding_through_confirm_and_undo(self):
        self.case("product", product=True)

    def test_same_w_resolve_hook_bypass_fails_exact_edges_in_standalone_and_bridge(self):
        build = native()
        self.case("material")
        self.case("product", product=True)
        original = build.woodworking / "engineering.c"
        before_bytes = original.read_bytes()
        source = before_bytes.decode("utf-8")
        needle = "if(w->resolve_source)"
        self.assertEqual(1, source.count(needle), "Exactly one shared W hook is bypassed")
        mutant_source = build.woodworking / "engineering-source-hook-mutant.c"
        mutant_source.write_text(source.replace(needle, "if(0)"), encoding="utf-8")
        changed = build.compile(mutant_source, "engineering-source-hook-mutant")
        standalone = build.link("engineering-sources-hook-mutant", [self.client, changed, *self.dependencies])
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_engineering_object))
        self.assertEqual(1, objects.count(build.wood_engineering_sources_object))
        product = build.link("engineering-sources-product-hook-mutant", [self.product_client,
            *[changed if obj == build.wood_engineering_object else obj for obj in objects]])
        self.case("material", exe=standalone, expected=1)
        self.case("product", exe=product, product=True, expected=1)
        self.assertEqual(before_bytes, original.read_bytes(), "Baseline source must remain unmodified")
        self.case("material")
        self.case("product", product=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
