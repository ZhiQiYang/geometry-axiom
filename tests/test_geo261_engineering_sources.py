"""W engineering decisions use real typed K source nodes in one candidate.

Fixed dimensions, canonical version content, exact edge kinds and established
error order are checked independently of no-hook parity. The same W hook-bypass
object must lose its quantity edge in isolated W/K and the actual bridge while
all earlier numeric assertions still pass. No crash or build error is a kill.
Definition completion also retains unused published inventory without asking
for unused dimensions, repeating ordered writes or changing active values.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
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


class EngineeringBindingBoundary(unittest.TestCase):
    def test_fixed_literal_vector_is_independently_encoded_without_c_padding(self):
        source=(ROOT/'tests/geo261_engineering_sources_harness.c').read_text(encoding='utf-8')
        body=re.search(r'static const unsigned char expected\[50\]=\{([^}]+)\}',source).group(1)
        actual=bytes(map(int,re.findall(r'\d+',body)))
        expected=struct.pack('>4I2Iq2I?2I?',1,0x01020304,0,1,0,0,-7,0,0,False,0,0,False)
        self.assertEqual(50,len(expected));self.assertEqual(expected,actual)

    def test_stored_and_request_keys_are_explicit_public_contracts(self):
        header=(ROOT/'geometry-templates/woodworking/native/engineering_sources.h').read_text(encoding='utf-8')
        source=(ROOT/'geometry-templates/woodworking/native/engineering_sources.c').read_text(encoding='utf-8')
        self.assertIn('WOOD_BINDING_SOURCE_REQUEST_DEFINITION=3',header)
        self.assertIn('wood_engineering_binding_source_decode',header)
        self.assertNotIn('EngBinding binding;} key',source)
        self.assertIn('geo_eval_source(ctx,upstream,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)',source)


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

    def test_canonical_binding_codec_fixed_vectors_and_failure_preserves_output(self):
        self.case('binding-codec')

    def test_stored_binding_target_identity_survives_changed_definition(self):
        self.case('binding-identity')

    def test_temporary_requests_keep_independent_values_and_sealed_memoization(self):
        self.case('binding-temporary')

    def test_definition_first_cached_binding_rejects_same_graph_store_mutation(self):
        self.case('binding-definition-first')

    def test_all_published_definitions_include_unused_material_method_application_and_binding(self):
        self.case('definitions')

    def test_definition_completion_preserves_first_values_order_and_memoized_quantities(self):
        self.case('definitions-after-values')

    def test_definition_inventory_controls_fail_exact_named_oracles(self):
        build=native()
        source=(build.woodworking/'engineering_sources.c').read_text(encoding='utf-8')
        controls=[
            ('material-inventory','for(size_t i=0;i<state->material_count;++i){',
             'for(size_t i=state->material_count;i<state->material_count;++i){','definitions-unused-material-published'),
            ('method-inventory','for(size_t i=0;i<state->method_count;++i){',
             'for(size_t i=state->method_count;i<state->method_count;++i){','definitions-unused-method-published'),
            ('application-inventory','for(size_t i=0;i<state->application_count;++i){',
             'for(size_t i=state->application_count;i<state->application_count;++i){','definitions-unselected-application-published'),
            ('binding-inventory','for(size_t i=0;i<state->binding_count;++i){',
             'for(size_t i=state->binding_count;i<state->binding_count;++i){','definitions-unused-binding-published'),
            ('inactive-slot-edge','geo_eval_depend(ctx,(GeoSourceRef){s->tokens.definition,&upstream,sizeof upstream},GEO_DEPENDENCY_DEFINITION_REQUIRED)',
             'geo_eval_depend(ctx,(GeoSourceRef){s->tokens.definition,&upstream,sizeof upstream},GEO_DEPENDENCY_VALUE_REQUIRED)',
             'definitions-inactive-method-slots-definition-required'),
        ]
        for name,before,after,marker in controls:
            with self.subTest(control=name):
                self.case('definitions');self.assertEqual(1,source.count(before),name)
                path=build.woodworking/('definition-inventory-control-'+name+'.c')
                path.write_text(source.replace(before,after),encoding='utf-8')
                obj=build.compile(path,'definition-inventory-control-'+name)
                executable=build.link('definition-inventory-control-'+name,[self.client,build.wood_engineering_object,
                    *[obj if value==build.wood_engineering_sources_object else value for value in self.dependencies]])
                result=subprocess.run([str(executable),'definitions'],capture_output=True,text=True,encoding='utf-8',timeout=30)
                self.assertEqual(1,result.returncode,result.stdout+'\n'+result.stderr)
                self.assertRegex(result.stderr,r'^ASSERT:'+re.escape(marker)+r':\d+\n$')
                self.case('definitions')

    def test_binding_identity_controls_fail_exact_named_oracles(self):
        build=native()
        source=(build.woodworking/'engineering_sources.c').read_text(encoding='utf-8')
        controls=[
            ('stored-key','if(kind<=WOOD_BINDING_SOURCE_EFFECTIVE)',
             'if(kind==WOOD_BINDING_SOURCE_DEFINITION)','binding-codec','binding-target-key-stable-across-source-change'),
            ('temporary-alias','bool owned=stored_size==size&&!memcmp(payload,stored_payload,size);',
             'bool owned=stored!=NULL;','binding-temporary','binding-temporary-does-not-alias-owned-target'),
            ('definition-edge','geo_eval_source(ctx,upstream,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)',
             'geo_eval_source(ctx,upstream,GEO_DEPENDENCY_VALUE_REQUIRED,&definition)','binding-identity','binding-canonical-definition-edge'),
            ('definition-first','if(definition.as.definition.content_size!=result->definition_size||\n'
             '           memcmp(definition.as.definition.content,result->definition,result->definition_size))',
             'if(0)','binding-definition-first','binding-definition-first-stale-rejected'),
        ]
        for name,before,after,case,marker in controls:
            with self.subTest(control=name):
                self.case(case);self.assertEqual(1,source.count(before),name)
                path=build.woodworking/('binding-identity-control-'+name+'.c')
                path.write_text(source.replace(before,after),encoding='utf-8')
                obj=build.compile(path,'binding-identity-control-'+name)
                executable=build.link('binding-identity-control-'+name,[self.client,build.wood_engineering_object,
                    *[obj if value==build.wood_engineering_sources_object else value for value in self.dependencies]])
                result=subprocess.run([str(executable),case],capture_output=True,text=True,encoding='utf-8',timeout=30)
                self.assertEqual(1,result.returncode,result.stdout+'\n'+result.stderr)
                self.assertRegex(result.stderr,r'^ASSERT:'+re.escape(marker)+r':\d+\n$')
                self.case(case)

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
