"""Canonical K parameter authoring is consumed by the original evaluator.

Portable checks never construct NativeBuild. The native lane uses isolated K
objects and accepts only an exact named ASSERT with exit 1 as a control kill.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import kernel_only_native

KERNEL=ROOT/"geometry-core/kernel"


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*","",source,flags=re.S)


def definition(source,name):
    source=code(source)
    match=re.search(r"^[\w *]+\b"+re.escape(name)+r"\s*\([^;]*?\)\s*\{",source,re.M|re.S)
    if match is None:raise AssertionError("Missing function "+name)
    depth=1;end=match.end()
    while depth:
        depth+=(source[end]=="{")-(source[end]=="}");end+=1
    return source[match.start():end]


CONTROLS=(
    ("key-endian","geo_parameter_definition_u32","value>>(24-8*i)","value>>(8*i)","keys","definition-key-fixed-big-endian"),
    ("card-highwater","geo_parameter_card_definition_encode","geo_parameter_definition_u32(bytes+4,card->next_field_id);",
        "geo_parameter_definition_u32(bytes+4,0);","codec","card-fixed-authored-bytes"),
    ("card-field-order","geo_parameter_card_definition_encode","card->fields[i]","card->fields[card->count-1-i]","codec","card-fixed-authored-bytes"),
    ("field-type","geo_parameter_field_definition_encode","(uint32_t)field->type","(uint32_t)GEO_PARAMETER_DIMENSION","codec","field-fixed-authored-bytes"),
    ("canonical-ast","geo_parameter_definition_expression","if(!canonical)memcpy(out,expression,strlen(expression)+1);",
        'if(!canonical||strstr(expression,"\\\"op\\\""))memcpy(out,expression,strlen(expression)+1);',"codec","field-canonical-full-ast"),
    ("returned-authoring","geo_parameter_source_definition","s->working->fields[index]=field;","(void)field;","typed","quantity-consumes-returned-field-definition"),
    ("descriptor-authority","geo_parameter_source_describe","out->unit=definition.type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;",
        "out->unit=geo_parameters_fields(state->store)[index].type==GEO_PARAMETER_DIMENSION?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;",
        "descriptor","quantity-descriptor-uses-canonical-unit"),
    ("quantity-definition-edge","geo_parameter_source_definition",
        "if(!geo_parameter_definition_get(s,GEO_PARAMETER_DEFINITION_FIELD,ref.parameter_id,ref.field_id,&definition))return false;",
        "GeoParameterDefinitionKey key;if(geo_eval_source(s->sources,geo_parameter_definition_source_ref(s->definition_token,GEO_PARAMETER_DEFINITION_FIELD,ref.parameter_id,ref.field_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&definition)!=GEO_SOURCE_OK)return false;",
        "graph","quantity-field-definition-edge"),
    ("owner-definition-edge","geo_parameter_definition_evaluate",
        "if(!geo_parameter_definition_get(s,GEO_PARAMETER_DEFINITION_CARD,card,0,&owner)||",
        "GeoParameterDefinitionKey owner_key;if(geo_eval_source(s->sources,geo_parameter_definition_source_ref(s->definition_token,GEO_PARAMETER_DEFINITION_CARD,card,0,&owner_key),GEO_DEPENDENCY_VALUE_REQUIRED,&owner)!=GEO_SOURCE_OK||",
        "graph","field-card-definition-edge"),
    ("successful-cache","geo_parameter_source_evaluate","memcpy(&cached->num,&out->as.quantity.num,sizeof cached->num);",
        "(void)index;","prefix","successful-prefix-cache-is-published"),
    ("unused-quantity","geo_parameter_sources_definitions","GeoSourceValue value;",
        "GeoSourceValue value;GeoQuantity extra;GeoParameterError ignored;(void)geo_parameter_sources_value(state,(GeoParameterRef){true,10,9},&extra,&ignored);",
        "definitions","metadata-enumeration-never-evaluates-quantities"),
    ("reset-generation","geo_parameter_source_bound","return value&&definition;","return true;",
        "reset","reset-old-handle-is-rejected-before-register"),
    ("registration-atomicity","geo_parameter_sources_register_with_definitions",
        "if(!geo_eval_register_many(ctx,providers,2)){geo_parameter_sources_destroy(state);return NULL;}return state;",
        "(void)geo_eval_register_many(ctx,providers,2);return state;","registration","definition-family-registration-is-atomic"),
)

CACHE_CONTROLS=(
    ("parameters.c","parameters_object","geo_parameter_eval_field",
        "memcpy(&f->value.num,&value.num,sizeof value.num);",
        "memset(&f->value,0,sizeof f->value);memcpy(&f->value.num,&value.num,sizeof value.num);",
        "cache-plain","plain-cache-writes-only-quantity-members"),
    ("parameter_sources.c","parameter_sources_object","geo_parameter_source_evaluate",
        "memcpy(&cached->num,&out->as.quantity.num,sizeof cached->num);",
        "memset(cached,0,sizeof *cached);memcpy(&cached->num,&out->as.quantity.num,sizeof cached->num);",
        "cache-source","source-cache-writes-only-quantity-members"),
)


class ParameterDefinitionBoundary(unittest.TestCase):
    def test_public_header_and_client_use_only_public_kernel_dependencies(self):
        header=(KERNEL/"parameter_sources.h").read_text(encoding="utf-8")
        source=(KERNEL/"parameter_sources.c").read_text(encoding="utf-8")
        harness=(ROOT/"tests/geo261_parameter_definition_sources_harness.c").read_text(encoding="utf-8")
        for text in (header,source,harness):
            self.assertNotRegex(code(text),r"\b(?:World|App\w*|Wood\w*|Timber|ReferenceEval)\b|geometry-app|geometry-templates")
        self.assertNotIn("internal/",header+harness)
        self.assertEqual(["parameters.h","source.h"],re.findall(r'^#include "([^"]+)"',header,re.M))
        self.assertEqual(["parameter_sources.h","internal/parameter_store.h","codec.h"],re.findall(r'^#include "([^"]+)"',source,re.M))
        self.assertEqual(["parameter_sources.h"],re.findall(r'^#include "([^"]+)"',harness,re.M))

    def test_registration_description_and_metadata_do_not_evaluate_quantities(self):
        source=(KERNEL/"parameter_sources.c").read_text(encoding="utf-8")
        for name in ("geo_parameter_sources_register_with_definitions","geo_parameter_definition_describe","geo_parameter_source_describe","geo_parameter_definition_record"):
            body=definition(source,name)
            self.assertNotRegex(body,r"geo_eval_(?:source|depend|describe)\(|geo_parameter_evaluation_field\(")
        complete=definition(source,"geo_parameter_sources_definitions")
        self.assertIn("GEO_PARAMETER_DEFINITION_CARD",complete);self.assertIn("GEO_PARAMETER_DEFINITION_FIELD",complete)
        self.assertNotIn("geo_parameter_sources_value(",complete)
        self.assertNotIn("geo_parameter_source_working(",complete)
        self.assertNotIn("geo_eval_",definition(source,"geo_parameter_sources_destroy"))

    def test_controls_target_one_live_expression_and_one_exact_named_assertion(self):
        source=(KERNEL/"parameter_sources.c").read_text(encoding="utf-8")
        harness=(ROOT/"tests/geo261_parameter_definition_sources_harness.c").read_text(encoding="utf-8")
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1,definition(source,function).count(before));self.assertNotEqual(before,after)
                self.assertEqual(1,harness.count('"'+marker+'"'));self.assertIn('"'+case+'"',harness)
        self.assertEqual(13,len(CONTROLS));self.assertEqual(13,len({row[0] for row in CONTROLS}))
        for filename,attribute,function,before,after,case,marker in CACHE_CONTROLS:
            with self.subTest(cache_control=case):
                body=definition((KERNEL/filename).read_text(encoding="utf-8"),function)
                self.assertEqual(1,body.count(before));self.assertNotEqual(before,after)
                self.assertEqual(1,harness.count('"'+marker+'"'));self.assertIn('"'+case+'"',harness)


class NativeParameterDefinitionSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"parameter-definition-sources-client.c"
        shutil.copy2(ROOT/"tests/geo261_parameter_definition_sources_harness.c",source)
        cls.client=build.compile(source,"parameter-definition-sources-client");cls.objects=build.kernel_objects()
        cls.provider=build.parameter_sources_object
        if cls.objects.count(cls.provider)!=1:raise AssertionError("Expected one actual parameter source object")
        cls.exe=build.link("parameter-definition-sources-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr);self.assertEqual("",run.stdout)

    def test_canonical_keys_include_zero_and_max_ids_and_reject_reserved_bytes(self):self.case("keys")
    def test_fixed_authored_bytes_complete_ast_names_types_order_highwater_and_atomic_codecs(self):self.case("codec")
    def test_unused_invalid_and_empty_cards_are_complete_without_quantity_evaluation(self):self.case("definitions")
    def test_quantity_parser_consumes_returned_definition_and_changes_only_success_cache(self):self.case("typed")
    def test_actual_definition_and_ast_value_edges_survive_sealed_memoization(self):self.case("graph")
    def test_successful_cache_writes_preserve_every_byte_outside_quantity_members(self):
        self.case("cache-plain");self.case("cache-source")
    def test_quantity_descriptor_uses_canonical_unit_in_both_directions_and_metadata_first_order(self):self.case("descriptor")
    def test_original_parser_first_error_identity_trace_and_output_are_preserved(self):self.case("diagnostics")
    def test_recursive_and_cached_depth_limits_keep_exact_diagnostics_and_cache_prefix(self):self.case("depth")
    def test_failed_outer_expression_preserves_successful_prefix_and_authored_bytes(self):self.case("prefix")
    def test_two_resets_rebuild_same_identity_with_new_ast_and_card_highwater(self):self.case("reset")
    def test_isolated_candidate_values_and_both_destruction_orders(self):self.case("lifetime")
    def test_registration_is_atomic_and_description_never_evaluates_missing_metadata(self):self.case("registration")
    def test_legacy_value_only_registration_retains_existing_key_and_edge_contract(self):self.case("legacy")

    def test_actual_build_is_kernel_only(self):
        build=kernel_only_native();self.assertTrue(build.kernel_only)
        self.assertFalse((build.work/"isolated-host").exists());self.assertFalse((build.work/"isolated-woodworking").exists())
        for row in build.logs:
            self.assertEqual(0,row["exit"])
            self.assertNotRegex(" ".join(row["arguments"]).lower(),r"geometry-app|geometry-templates|current_geometry|web_bridge|isolated-host|isolated-woodworking")
        self.assertTrue(any(str(build.kernel/"parameter_sources.c") in row["arguments"] for row in build.logs))

    def test_thirteen_controls_fail_exact_named_assertions_between_passing_baselines(self):
        build=kernel_only_native();original_path=build.kernel/"parameter_sources.c";original_bytes=original_path.read_bytes()
        original=original_bytes.decode("utf-8");source=code(original)
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case);body=definition(original,function)
                self.assertEqual(1,body.count(before));self.assertEqual(1,source.count(body))
                path=build.kernel/("parameter-definition-control-"+name+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"parameter-definition-control-"+name)
                exe=build.link("parameter-definition-control-"+name,[self.client,*[changed if obj==self.provider else obj for obj in self.objects]])
                self.case(case,exe,marker);self.assertEqual(original_bytes,original_path.read_bytes());self.case(case)

    def test_both_cache_padding_controls_fail_exact_assertions_between_passing_baselines(self):
        build=kernel_only_native()
        for filename,attribute,function,before,after,case,marker in CACHE_CONTROLS:
            with self.subTest(cache_control=case):
                original_path=build.kernel/filename;original_bytes=original_path.read_bytes()
                original=original_bytes.decode("utf-8");source=code(original);body=definition(original,function)
                self.case(case);self.assertEqual(1,body.count(before));self.assertEqual(1,source.count(body))
                path=build.kernel/("parameter-cache-control-"+case+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"parameter-cache-control-"+case);target=getattr(build,attribute)
                self.assertEqual(1,self.objects.count(target))
                exe=build.link("parameter-cache-control-"+case,[self.client,*[changed if obj==target else obj for obj in self.objects]])
                self.case(case,exe,marker);self.assertEqual(original_bytes,original_path.read_bytes());self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
