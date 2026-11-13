"""Same-candidate enclosure source data, identities, ordering and atomicity.

The standalone native client links actual K providers/evaluators with no H/W.
Each mutation changes one actual function and must reach one exact assertion;
compile failures, crashes and arbitrary nonzero exits are never detections.
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
    ("key-endian","geo_enclosure_source_u32","value>>(24-8*i)","value>>(8*i)","keys","key-seven-byte-layout"),
    ("key-id","geo_enclosure_source_read_u32","value=(value<<8)|bytes[i]","value=bytes[i]","keys","key-zero-max-roundtrip"),
    ("key-domain","geo_enclosure_source_decode","if(!geo_enclosure_source_indices(k,a,b))return false;","","keys","key-decode-failure-atomic"),
    ("result-endian","geo_enclosure_source_i64","bits>>(56-8*i)","bits>>(8*i)","typed","typed-region-overrides-owned"),
    ("definition-id","geo_enclosure_source_members","geo_enclosure_source_u32(bytes,value->id);","geo_enclosure_source_u32(bytes,0);","definition","definition-canonical-members-only"),
    ("member-order","geo_enclosure_source_members","value->member_ids[i]","value->member_ids[value->member_count-1-i]","definition","definition-canonical-members-only"),
    ("definition-unit","geo_enclosure_sources_describe","next.unit=kind==GEO_ENCLOSURE_SOURCE_AXIS_BOUND?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;","next.unit=GEO_UNIT_LENGTH;","definition","definition-scalar-metadata"),
    ("definition-upstream","geo_enclosure_sources_evaluate","size_t size=geo_enclosure_source_members(s->definitions[at],definition);",
        "size_t size=geo_enclosure_source_members(s->definitions[at],definition);GeoRegionSourceKey extra;geo_eval_depend(graph,geo_region_source_ref(s->region_token,0,&extra),GEO_DEPENDENCY_DEFINITION_REQUIRED);","definition","definition-no-upstream-evaluation"),
    ("frame-cache","geo_enclosure_source_frame","next.frame=value.as.frame;","next.frame=source->frame;","typed","typed-frame-overrides-owned"),
    ("region-cache","geo_enclosure_source_region","return geo_regions_put(target,&next);","return geo_regions_put(target,geo_regions_find(s->regions,id));","typed","typed-region-overrides-owned"),
    ("region-cardinality","geo_enclosure_source_region","value.as.regions.count!=1","value.as.regions.count<1","typed","typed-reject-multi-region"),
    ("frame-validity","geo_enclosure_source_frame","||!geo_frame_is_valid(&value.as.frame)","","typed","typed-reject-invalid-frame"),
    ("definition-edge","geo_enclosure_sources_evaluate","GEO_DEPENDENCY_DEFINITION_REQUIRED","GEO_DEPENDENCY_VALUE_REQUIRED","graph","graph-definition-edge-valid"),
    ("frame-edge","geo_enclosure_source_frame","GEO_DEPENDENCY_VALUE_REQUIRED","GEO_DEPENDENCY_DEFINITION_REQUIRED","graph","graph-value-region-frame-edges"),
    ("region-edge","geo_enclosure_source_region","GEO_DEPENDENCY_VALUE_REQUIRED","GEO_DEPENDENCY_DEFINITION_REQUIRED","graph","graph-value-region-frame-edges"),
    ("missing-member","geo_enclosure_source_carrier","if(!geo_regions_find(s->regions,member))","if(false)","ordered","ordered-member-identity-faults"),
    ("duplicate-member","geo_enclosure_source_carrier","fault->kind=GEO_ENCLOSURE_FAULT_DUPLICATE_REGION;","fault->kind=GEO_ENCLOSURE_FAULT_NO_CARRIER;","ordered","ordered-member-identity-faults"),
    ("ambiguous-carrier","geo_enclosure_source_carrier","if(count!=1)","if(!count)","ordered","ordered-member-identity-faults"),
    ("slot-order","geo_enclosure_source_result","if(!prefix&&fault.kind<=GEO_ENCLOSURE_FAULT_SLOT_TAKEN)","if(false)","ordered","ordered-slot-before-region-failure"),
    ("extent-order","geo_enclosure_source_result","fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH&&fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED",
        "fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH&&fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED&&fault.kind!=GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH","ordered","ordered-extent-before-later-frame-failure"),
    ("plane-order","geo_enclosure_source_result","fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH&&fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED",
        "fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED","ordered","ordered-plane-deferred"),
    ("inversion-order","geo_enclosure_source_result","fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH&&fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED",
        "fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH","ordered","ordered-inverted-deferred"),
    ("axis-cache","geo_enclosure_source_axis","bool ok=false;GeoCoord next;","bool ok=true;GeoCoord next;*out=definition->max[axis];","axis","axis-no-bbox-fallback"),
    ("axis-member-order","geo_enclosure_source_axis","definition->member_ids[i]","definition->member_ids[definition->member_count-1-i]","axis","axis-member-before-placement"),
    ("axis-placement-order","geo_enclosure_source_axis","geo_placements_at(s->placements,p)","geo_placements_at(s->placements,geo_placements_count(s->placements)-1-p)","axis","axis-ambiguous-first"),
    ("failure-publication","geo_enclosure_sources_value","GeoEnclosureSourceKey key;GeoSourceValue value;","memset(out,0,sizeof *out);GeoEnclosureSourceKey key;GeoSourceValue value;","atomic","atomic-upstream-preserves-output-fault"),
    ("success-fault","geo_enclosure_sources_value","geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,id,out);","geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,id,out)&&(fault?(memset(fault,0,sizeof *fault),true):true);","atomic","atomic-success-preserves-fault"),
    ("sealed-fault","geo_enclosure_sources_value","status==GEO_SOURCE_FAILED&&fault&&s->has_fault[at]","fault&&s->has_fault[at]","atomic","atomic-sealed-failure-preserves-fault"),
    ("token-collision","geo_enclosure_sources_register","token==placement_token||","","registration","registration-invalid-tokens-atomic"),
    ("registration-failure","geo_enclosure_sources_register","if(!geo_eval_register(graph,&provider)){free(s);return NULL;}","(void)geo_eval_register(graph,&provider);","registration","registration-duplicate-atomic"),
)


class EnclosureSourceBoundary(unittest.TestCase):
    def test_public_provider_and_client_have_no_host_template_or_private_store_layout(self):
        sources=[(KERNEL/"enclosure_sources.h").read_text(encoding="utf-8"),
            (KERNEL/"enclosure_sources.c").read_text(encoding="utf-8"),
            (ROOT/"tests/geo261_enclosure_sources_harness.c").read_text(encoding="utf-8")]
        for source in sources:
            self.assertNotRegex(code(source),r"\b(?:World|Space|Timber|Wood\w*|App\w*)\b|internal/")
        self.assertEqual(["enclosure.h","placement_sources.h","enclosure_sources.h","enclosure_sources.h"],
            re.findall(r'^#include "([^"]+)"',"\n".join(sources),re.M))

    def test_result_materializes_typed_values_and_reuses_the_actual_kernel_evaluator(self):
        source=(KERNEL/"enclosure_sources.c").read_text(encoding="utf-8")
        self.assertIn("next.frame=value.as.frame",definition(source,"geo_enclosure_source_frame"))
        self.assertIn("return geo_regions_put(target,&next)",definition(source,"geo_enclosure_source_region"))
        body=definition(source,"geo_enclosure_source_result")
        self.assertIn("geo_enclosure_evaluate",body)
        self.assertIn("geo_regions_clone",body);self.assertIn("geo_placements_clone",body)
        self.assertNotIn("GEO_SOURCE_BOX",source)

    def test_each_control_targets_one_actual_rule_and_one_exact_assertion(self):
        source=(KERNEL/"enclosure_sources.c").read_text(encoding="utf-8")
        harness=(ROOT/"tests/geo261_enclosure_sources_harness.c").read_text(encoding="utf-8")
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1,definition(source,function).count(before))
                self.assertNotEqual(before,after);self.assertEqual(1,harness.count('"'+marker+'"'))
                self.assertIn('"'+case+'"',harness)
        self.assertEqual(30,len(CONTROLS));self.assertEqual(30,len({row[0] for row in CONTROLS}))


class NativeEnclosureSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"enclosure-sources-client.c"
        shutil.copy2(ROOT/"tests/geo261_enclosure_sources_harness.c",source)
        cls.client=build.compile(source,"enclosure-sources-client");cls.objects=build.kernel_objects()
        if cls.objects.count(build.enclosure_sources_object)!=1:raise AssertionError("Expected one actual enclosure source object")
        cls.exe=build.link("enclosure-sources-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=15)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr);self.assertEqual("",run.stdout)

    def test_exact_key_layout_zero_max_identity_and_atomic_decode(self):self.case("keys")
    def test_canonical_member_definition_is_independent_of_geometry_and_caches(self):self.case("definition")
    def test_typed_values_drive_geometry_with_bounds_and_cardinality_checked(self):self.case("typed")
    def test_dependency_kinds_memoization_candidate_isolation_reset_and_typed_cycles(self):self.case("graph")
    def test_ordered_member_faults_precede_later_sources_and_final_plane_checks(self):self.case("ordered")
    def test_axis_uses_typed_normal_slots_and_keeps_member_then_placement_order(self):self.case("axis")
    def test_outputs_faults_and_owned_candidate_stores_are_atomic(self):self.case("atomic")
    def test_provider_registration_is_atomic_and_destruction_order_independent(self):self.case("registration")

    def test_actual_build_contains_only_kernel_sources_and_objects(self):
        build=kernel_only_native();self.assertTrue(build.kernel_only)
        self.assertFalse((build.work/"isolated-host").exists());self.assertFalse((build.work/"isolated-woodworking").exists())
        for row in build.logs:
            self.assertEqual(0,row["exit"])
            self.assertNotRegex(" ".join(row["arguments"]).lower(),r"geometry-app|geometry-templates|current_geometry|web_bridge|isolated-host|isolated-woodworking")
        self.assertTrue(any(str(build.kernel/"enclosure_sources.c") in row["arguments"] for row in build.logs))

    def test_actual_rules_fail_exact_named_oracles_between_passing_baselines(self):
        build=kernel_only_native();original=(build.kernel/"enclosure_sources.c").read_text(encoding="utf-8");source=code(original)
        for name,function,before,after,case,marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case);body=definition(original,function)
                self.assertEqual(1,body.count(before));self.assertEqual(1,source.count(body))
                path=build.kernel/("enclosure-sources-control-"+name+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"enclosure-sources-control-"+name)
                objects=[changed if obj==build.enclosure_sources_object else obj for obj in self.objects]
                mutant=build.link("enclosure-sources-control-"+name,[self.client,*objects])
                self.case(case,mutant,marker);self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
