"""Neutral authored linear definitions, independent wire vectors and real K consumers.

Portable boundary checks do not initialize NativeBuild. Native tests belong in
the serialized validation lane; a control is killed only by exit 1 and its exact
named ASSERT. Compile failures, crashes, timeouts and unavailable compilers do
not count as a successful control.
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
HARNESS=ROOT/"tests/geo261_linear_definition_sources_harness.c"


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*","",source,flags=re.S)


def definition(source,name):
    source=code(source)
    match=re.search(r"^[\w *]+\b"+re.escape(name)+r"\s*\([^;]*?\)\s*\{",source,re.M|re.S)
    if match is None:raise AssertionError("Missing function "+name)
    depth=1;end=match.end()
    while depth:
        if end>=len(source):raise AssertionError("Unclosed function "+name)
        depth+=(source[end]=="{")-(source[end]=="}");end+=1
    return source[match.start():end]


# Every replacement targets one live expression inside one named function.
# The final columns are a baseline case and the sole accepted failure marker.
CONTROLS=(
    ("key-endian","linear_definition_sources.c","geo_ld_put32","value>>(24-8*i)","value>>(8*i)","keys","key-fixed-big-endian"),
    ("mode","linear_definition_sources.c","geo_ld_expression_write","geo_ld_put32(p,(uint32_t)expression->mode);","geo_ld_put32(p,0);","codec","datum-fixed-canonical-vector"),
    ("complete","linear_definition_sources.c","geo_ld_expression_write","expression->complete?1:0","1","codec","datum-fixed-canonical-vector"),
    ("term-order","linear_definition_sources.c","geo_ld_expression_write","&expression->terms[i]","&expression->terms[expression->count-1-i]","codec","datum-fixed-canonical-vector"),
    ("coefficient","linear_definition_sources.c","geo_ld_expression_write","geo_ld_put64(p,term->denominator);","geo_ld_put64(p,1);","codec","datum-fixed-canonical-vector"),
    ("embedded-nul","linear_definition_sources.c","geo_ld_expression_read","memchr(r->p,0,(size_t)length)","false","rejection","invalid-datum-decode-atomic"),
    ("trailing-bytes","linear_definition_sources.c","geo_datum_definition_decode","||r.p!=r.end","||false","rejection","invalid-datum-decode-atomic"),
    ("datum-returned-definition","linear_definition_sources.c","geo_linear_definition_sources_datum","memcpy(out,&result,sizeof result)","*out=*geo_datums_find(s->datums,id)","typed","datum-accessor-reads-returned-definition"),
    ("guide-returned-definition","linear_definition_sources.c","geo_linear_definition_sources_guide","memcpy(out,&result,sizeof result)","*out=*geo_guides_find(s->guides,id)","typed","guide-accessor-reads-returned-definition"),
    ("unused-guides","linear_definition_sources.c","geo_linear_definition_sources_complete","for(size_t i=0;i<geo_guides_count(s->guides);++i)","for(size_t i=geo_guides_count(s->guides);i<geo_guides_count(s->guides);++i)","definitions","all-unused-definitions-enumerated"),
    ("datum-definition-edge","linear_definition_sources.c","geo_ld_evaluate","GEO_DEPENDENCY_DEFINITION_REQUIRED","GEO_DEPENDENCY_VALUE_REQUIRED","definitions","guide-datum-edge-is-definition-only"),
    ("datum-supplied-coefficients","datums.c","geo_datums_evaluate_definition","&definition->expression","&datum->expression","datum","datum-evaluate-supplied-coefficients"),
    ("guide-supplied-coefficients","guides.c","geo_guides_evaluate_definition","&definition->expression","&guide->expression","guide","guide-evaluate-supplied-coefficients"),
    ("datum-range-cache","datums.c","geo_datums_evaluate_definition","result.status==GEO_LINEAR_OK||result.status==GEO_LINEAR_RANGE","result.status==GEO_LINEAR_OK","datum-errors","datum-range-keeps-attempted-position"),
    ("guide-local-range-cache","guides.c","geo_guides_evaluate_definition","if (result.linear.status != GEO_LINEAR_OK) {","if (result.linear.status != GEO_LINEAR_OK) { guide->offset = result.linear.value.num;","guide-errors","local-range-does-not-publish-attempt"),
    ("guide-supplied-datum","guides.c","geo_guides_evaluate_definition","datum->id != definition->datum_id","datum->id != guide->datum_id","guide","guide-evaluate-supplied-datum-reference"),
    ("guide-invalid-direction","guides.c","geo_guides_evaluate_definition","definition->direction != GEO_GUIDE_ALONG_U && definition->direction != GEO_GUIDE_ALONG_V","false","guide-errors","invalid-local-direction-precedes-resolution"),
    ("guide-source-kind","guides.c","geo_guides_evaluate_definition","definition->source != store->values[index].source","false","guide-errors","guide-source-kind-cannot-change-authored-storage"),
)


class LinearDefinitionSourceBoundary(unittest.TestCase):
    def test_provider_and_witness_use_only_public_kernel_dependencies(self):
        sources=[(KERNEL/name).read_text(encoding="utf-8") for name in ("linear_definition_sources.h","linear_definition_sources.c")]
        sources.append(HARNESS.read_text(encoding="utf-8"))
        for source in sources:
            self.assertNotRegex(code(source),r"\b(?:World|App\w*|Wood\w*|Timber|ReferenceEval)\b|internal/|geometry-app|geometry-templates")
        self.assertEqual(["guides.h","source.h","linear_definition_sources.h","linear_definition_sources.h"],
                         re.findall(r'^#include "([^"]+)"',"\n".join(sources),re.M))

    def test_definition_registration_description_and_completion_never_resolve_geometry(self):
        source=(KERNEL/"linear_definition_sources.c").read_text(encoding="utf-8")
        for name in ("geo_linear_definition_sources_register","geo_ld_describe"):
            self.assertNotRegex(definition(source,name),r"geo_eval_(?:source|depend|describe)\(")
        self.assertNotRegex(code(source),r"geo_(?:linear_evaluate|datums_evaluate(?:_definition)?|guides_evaluate(?:_definition)?|datum_intersection|frame_point)\(")
        self.assertNotIn("geo_eval_",definition(source,"geo_linear_definition_sources_destroy"))
        complete=definition(source,"geo_linear_definition_sources_complete")
        self.assertIn("GEO_LINEAR_DEFINITION_DATUM",complete)
        self.assertIn("GEO_LINEAR_DEFINITION_GUIDE",complete)

    def test_controls_have_one_live_anchor_and_one_exact_named_assertion(self):
        harness=HARNESS.read_text(encoding="utf-8")
        for name,file,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                source=(KERNEL/file).read_text(encoding="utf-8");body=definition(source,function)
                self.assertEqual(1,body.count(before));self.assertEqual(1,code(source).count(body))
                self.assertNotEqual(before,after);self.assertEqual(1,harness.count('"'+marker+'"'))
                self.assertIn('"'+case+'"',harness)
        self.assertEqual(18,len(CONTROLS));self.assertEqual(18,len({row[0] for row in CONTROLS}))


class NativeLinearDefinitionSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"linear-definition-sources-client.c"
        shutil.copy2(HARNESS,source)
        cls.client=build.compile(source,"linear-definition-sources-client")
        cls.objects=build.kernel_objects()
        cls.targets={"linear_definition_sources.c":build.linear_definition_sources_object,
                     "datums.c":build.datums_object,"guides.c":build.guides_object}
        for name,obj in cls.targets.items():
            if cls.objects.count(obj)!=1:raise AssertionError("Expected one actual kernel object for "+name)
        cls.exe=build.link("linear-definition-sources-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=15)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr)
        self.assertEqual("",run.stdout)

    def test_fixed_source_key_bytes_and_atomic_invalid_identity_decoding(self):self.case("keys")
    def test_independent_codec_vectors_retain_authored_data_and_exclude_caches(self):self.case("codec")
    def test_truncation_nul_capacity_and_invalid_codec_inputs_preserve_outputs(self):self.case("rejection")
    def test_unused_incomplete_definitions_and_description_never_request_geometry(self):self.case("definitions")
    def test_accessors_and_consumers_read_actual_returned_definitions(self):self.case("typed")
    def test_registration_candidate_isolation_reset_sealing_and_both_teardown_orders(self):self.case("lifecycle")
    def test_datum_evaluation_uses_supplied_coefficients_and_preserves_authored_store(self):self.case("datum")
    def test_datum_range_and_valid_prefix_failure_rules_remain_unchanged(self):self.case("datum-errors")
    def test_guide_evaluation_uses_supplied_expression_and_datum_reference(self):self.case("guide")
    def test_guide_local_and_datum_failures_keep_distinct_partial_cache_rules(self):self.case("guide-errors")

    def test_actual_build_has_no_host_or_template_source_closure(self):
        build=kernel_only_native();self.assertTrue(build.kernel_only)
        self.assertFalse((build.work/"isolated-host").exists());self.assertFalse((build.work/"isolated-woodworking").exists())
        for row in build.logs:
            self.assertEqual(0,row["exit"])
            self.assertNotRegex(" ".join(row["arguments"]).lower(),r"geometry-app|geometry-templates|current_geometry|web_bridge|isolated-host|isolated-woodworking")
        self.assertTrue(any(str(build.kernel/"linear_definition_sources.c") in row["arguments"] for row in build.logs))

    def test_eighteen_controls_fail_exact_assertions_between_passing_baselines(self):
        build=kernel_only_native()
        for name,file,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                original_path=build.kernel/file;original_bytes=original_path.read_bytes();original=original_bytes.decode("utf-8")
                body=definition(original,function);source=code(original)
                self.assertEqual(1,body.count(before));self.assertEqual(1,source.count(body));self.case(case)
                path=build.kernel/("linear-definition-control-"+name+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"linear-definition-control-"+name)
                objects=[changed if obj==self.targets[file] else obj for obj in self.objects]
                exe=build.link("linear-definition-control-"+name,[self.client,*objects])
                self.case(case,exe,marker);self.assertEqual(original_bytes,original_path.read_bytes());self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
