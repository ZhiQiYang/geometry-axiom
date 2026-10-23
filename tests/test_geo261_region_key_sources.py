"""K region-key ledger definitions and coordinates use actual typed sources.

Portable checks never initialize a native build. Native cases are serialized
by the validation lane; only an exact named ASSERT with exit 1 kills a control.
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
    ("key-endian","geo_region_key_write32","value>>(24-8*i)","value>>(8*i)","keys","source-key-fixed-big-endian-bytes"),
    ("ledger-highwater","geo_region_key_ledger_encode","geo_region_key_write32(bytes+4,keys->next_key);","geo_region_key_write32(bytes+4,0);","codec","ledger-fixed-canonical-bytes"),
    ("ledger-key-order","geo_region_key_ledger_encode","keys->keys[l][i]","keys->keys[l][keys->counts[l]-1-i]","codec","ledger-fixed-canonical-bytes"),
    ("ledger-trailing","geo_region_key_ledger_decode","offset!=size||","false||","codec","ledger-invalid-and-trailing-decode-atomic"),
    ("typed-region","geo_region_key_evaluate","if(!geo_region_key_geometry(id,&region,&geometry))return false;",
        "const GeoRegionDefinition *raw=geo_regions_find(s->regions,id);if(!raw)return false;geometry=*raw;","typed","coordinate-consumes-typed-region-value"),
    ("typed-ledger","geo_region_key_evaluate","if(!geo_region_key_ledger_decode(ledger.as.definition.content,ledger.as.definition.content_size,&keys)||keys.boundary_id!=id)return false;",
        "const GeoRegionKeys *raw=geo_region_keys_find(s->regions,id);if(!raw)return false;keys=*raw;","typed","coordinate-consumes-canonical-ledger-value"),
    ("ledger-edge","geo_region_key_evaluate","GEO_DEPENDENCY_DEFINITION_REQUIRED,&ledger","GEO_DEPENDENCY_VALUE_REQUIRED,&ledger","graph","coordinate-ledger-definition-edge"),
    ("region-edge","geo_region_key_evaluate","GEO_DEPENDENCY_VALUE_REQUIRED,&region","GEO_DEPENDENCY_DEFINITION_REQUIRED,&region","graph","coordinate-region-value-edge"),
    ("key-policy","geo_region_key_evaluate","GeoPoint2 point;if(!geo_region_vertex_by_key(&geometry,&keys,key,&point))return false;",
        "GeoPoint2 point={0};bool found=false;for(size_t l=0;l<keys.loop_count;++l)for(size_t i=0;i<keys.counts[l];++i)if(keys.keys[l][i]==key){point=l?geometry.holes[l-1].v[i]:geometry.outline.v[i];found=true;}if(!found)return false;",
        "errors","invalid-coordinate-preserves-value"),
    ("point-atomicity","geo_region_key_sources_vertex","if(axis)next.v=value.as.quantity.num;else next.u=value.as.quantity.num;",
        "if(axis)next.v=value.as.quantity.num;else next.u=value.as.quantity.num;if(out)*out=next;","atomic","vertex-second-axis-failure-is-atomic"),
    ("unused-value","geo_region_key_sources_definitions","if(!s)return false;",
        "if(!s)return false;GeoRegionSourceKey extra_key;GeoSourceValue extra;(void)geo_eval_source(s->graph,geo_region_source_ref(s->region_token,0,&extra_key),GEO_DEPENDENCY_VALUE_REQUIRED,&extra);",
        "definitions","unused-ledgers-never-request-geometry"),
    ("registration-atomicity","geo_region_key_sources_register","if(!geo_eval_register(graph,&provider)){free(s);return NULL;}",
        "(void)geo_eval_register(graph,&provider);","registration","registration-duplicate-atomic"),
)


class RegionKeySourceBoundary(unittest.TestCase):
    def test_public_provider_and_client_have_only_public_kernel_dependencies(self):
        sources=[(KERNEL/name).read_text(encoding="utf-8") for name in ("region_key_sources.h","region_key_sources.c")]
        sources.append((ROOT/"tests/geo261_region_key_sources_harness.c").read_text(encoding="utf-8"))
        for source in sources:
            self.assertNotRegex(code(source),r"\b(?:World|App\w*|Wood\w*|Timber|ReferenceEval)\b|internal/|geometry-app|geometry-templates")
        self.assertEqual(["regions.h","source.h","region_key_sources.h","placement_sources.h","region_key_sources.h","placement_sources.h"],
            re.findall(r'^#include "([^"]+)"',"\n".join(sources),re.M))

    def test_registration_description_and_unused_enumeration_do_not_resolve_geometry(self):
        source=(KERNEL/"region_key_sources.c").read_text(encoding="utf-8")
        for name in ("geo_region_key_sources_register","geo_region_key_describe"):
            body=definition(source,name)
            self.assertNotRegex(body,r"geo_eval_(?:source|depend|describe)\(")
            self.assertNotRegex(body,r"geo_region_(?:vertex_by_key|keys_initialize|keys_reconcile)\(")
        self.assertNotIn("geo_eval_",definition(source,"geo_region_key_sources_destroy"))
        complete=definition(source,"geo_region_key_sources_definitions")
        self.assertIn("GEO_REGION_KEY_SOURCE_LEDGER",complete)
        self.assertNotIn("GEO_REGION_KEY_SOURCE_COORDINATE",complete)
        self.assertNotIn("geo_region_source_ref",complete)

    def test_controls_target_one_live_expression_and_one_exact_named_assertion(self):
        source=(KERNEL/"region_key_sources.c").read_text(encoding="utf-8")
        harness=(ROOT/"tests/geo261_region_key_sources_harness.c").read_text(encoding="utf-8")
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1,definition(source,function).count(before))
                self.assertNotEqual(before,after);self.assertEqual(1,harness.count('"'+marker+'"'))
                self.assertIn('"'+case+'"',harness)
        self.assertEqual(12,len(CONTROLS));self.assertEqual(12,len({row[0] for row in CONTROLS}))


class NativeRegionKeySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"region-key-sources-client.c"
        shutil.copy2(ROOT/"tests/geo261_region_key_sources_harness.c",source)
        cls.client=build.compile(source,"region-key-sources-client");cls.objects=build.kernel_objects()
        cls.provider=build.kernel_region_key_sources_object
        if cls.objects.count(cls.provider)!=1:raise AssertionError("Expected one actual region-key source object")
        cls.exe=build.link("region-key-sources-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=15)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr);self.assertEqual("",run.stdout)

    def test_fixed_big_endian_source_keys_zero_ids_max_keys_and_atomic_decode(self):self.case("keys")
    def test_canonical_ledger_codec_highwater_active_order_and_atomic_rejection(self):self.case("codec")
    def test_all_unused_ledgers_have_definitions_without_geometry_evaluation(self):self.case("definitions")
    def test_coordinates_consume_returned_region_and_canonical_ledger_values(self):self.case("typed")
    def test_real_edges_memoization_sealing_and_candidate_isolation(self):self.case("graph")
    def test_original_key_validity_typed_failures_cycles_and_unchanged_outputs(self):self.case("errors")
    def test_second_axis_failure_does_not_publish_half_a_point(self):self.case("atomic")
    def test_reset_rebuilds_values_with_the_same_stable_identity(self):self.case("reset")
    def test_registration_description_and_destruction_are_atomic(self):self.case("registration")
    def test_actual_region_provider_matches_original_vertex_lookup(self):self.case("actual-region")

    def test_actual_build_is_kernel_only(self):
        build=kernel_only_native();self.assertTrue(build.kernel_only)
        self.assertFalse((build.work/"isolated-host").exists());self.assertFalse((build.work/"isolated-woodworking").exists())
        for row in build.logs:
            self.assertEqual(0,row["exit"])
            self.assertNotRegex(" ".join(row["arguments"]).lower(),r"geometry-app|geometry-templates|current_geometry|web_bridge|isolated-host|isolated-woodworking")
        self.assertTrue(any(str(build.kernel/"region_key_sources.c") in row["arguments"] for row in build.logs))

    def test_twelve_controls_fail_exact_named_assertions_between_passing_baselines(self):
        build=kernel_only_native();original_path=build.kernel/"region_key_sources.c";original_bytes=original_path.read_bytes()
        original=original_bytes.decode("utf-8");source=code(original)
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case);body=definition(original,function)
                self.assertEqual(1,body.count(before));self.assertEqual(1,source.count(body))
                path=build.kernel/("region-key-source-control-"+name+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"region-key-source-control-"+name)
                exe=build.link("region-key-source-control-"+name,[self.client,*[changed if obj==self.provider else obj for obj in self.objects]])
                self.case(case,exe,marker);self.assertEqual(original_bytes,original_path.read_bytes());self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
