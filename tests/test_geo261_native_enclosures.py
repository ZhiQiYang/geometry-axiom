"""Independent K enclosure geometry, ordered faults and owned-byte witnesses.

Native links contain only K objects. Each control edits one actual enclosure
function and must fail one exact named assertion between two passing baselines.
Build failures, crashes and arbitrary nonzero exits never count as detection.
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
    if match is None:raise AssertionError("Missing enclosure function "+name)
    depth=1;end=match.end()
    while depth:
        depth+=(source[end]=="{")-(source[end]=="}");end+=1
    return source[match.start():end]


class EnclosureBoundary(unittest.TestCase):
    def test_public_and_private_definitions_use_only_neutral_kernel_records(self):
        paths=("enclosure.h","enclosure.c","internal/enclosures.h")
        source="\n".join((KERNEL/p).read_text(encoding="utf-8") for p in paths)
        self.assertNotRegex(code(source),r"\b(?:World|Space|Timber|Wood\w*|App\w*|scene_error|boundary_id|room_min|room_max|fixity)\b")
        self.assertEqual(["placements.h","internal/enclosures.h","../enclosure.h"],
            re.findall(r'^\s*#include\s+"([^"]+)"',source,re.M))

    def test_owned_store_is_inline_and_queries_return_const_borrowed_values(self):
        private=code((KERNEL/"internal/enclosures.h").read_text(encoding="utf-8"))
        body=private[private.index("struct GeoEnclosureStore {"):private.index("};")]
        self.assertNotIn("*",body)
        self.assertIn("GeoEnclosure values[GEO_ENCLOSURE_CAPACITY]",body)
        public=(KERNEL/"enclosure.h").read_text(encoding="utf-8")
        for name in ("at","find","values"):
            self.assertIn("const GeoEnclosure *geo_enclosures_"+name,public)

    def test_stage_is_separate_from_evaluation_and_native_client_has_no_host_template(self):
        source=(KERNEL/"enclosure.c").read_text(encoding="utf-8")
        stage=definition(source,"geo_enclosures_stage")
        self.assertNotRegex(stage,r"\bgeo_(?:enclosure_evaluate|regions_find|placements_at|frame_is_valid)\b")
        self.assertIn("geo_loop_bbox",definition(source,"geo_enclosure_extent"))
        harness=(ROOT/"tests/geo261_enclosure_harness.c").read_text(encoding="utf-8")
        self.assertEqual(["enclosure.h","internal/enclosures.h"],re.findall(r'^#include "([^"]+)"',harness,re.M))
        self.assertNotRegex(code(harness),r"\b(?:World|Space|Wood\w*|App\w*)\b")


class NativeEnclosures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"enclosure-client.c"
        shutil.copy2(ROOT/"tests/geo261_enclosure_harness.c",source)
        cls.client=build.compile(source,"enclosure-client")
        cls.objects=build.kernel_objects()
        if cls.objects.count(build.enclosure_object)!=1:
            raise AssertionError("Expected one actual enclosure K object")
        cls.exe=build.link("enclosure-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=15)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr)
        self.assertEqual("",run.stdout)

    def test_six_faces_literal_bounds_each_open_face_and_output_id_alias(self):self.case("box")
    def test_single_plane_extents_do_not_invent_other_normal_slots(self):self.case("partial")
    def test_negative_and_permuted_local_axes_preserve_literal_extents(self):self.case("negative")
    def test_holes_and_concave_outlines_use_outer_bounding_extremes(self):self.case("outline")
    def test_zero_members_arguments_capacity_and_atomic_failure(self):self.case("arguments")
    def test_region_identity_carrier_cardinality_and_member_error_order(self):self.case("identity")
    def test_duplicate_normal_slot_precedes_ordered_extent_mismatches(self):self.case("members")
    def test_final_plane_mismatches_precede_inversion_and_follow_xyz(self):self.case("planes")
    def test_equal_and_inverted_opposing_planes_on_each_axis(self):self.case("inverted")
    def test_axis_queries_actual_slots_and_member_then_placement_order(self):self.case("axis")
    def test_zero_identity_requires_explicit_region_reference_domain(self):self.case("typed")
    def test_store_owns_all_bytes_aliases_clones_and_failed_writes(self):self.case("storage")
    def test_capacity_replacement_removal_order_and_zero_tail(self):self.case("capacity")
    def test_empty_staging_keeps_cache_until_explicit_evaluation(self):self.case("empty-cache")
    def test_membership_can_be_shared_and_removal_never_cascades(self):self.case("sharing")

    def test_actual_kernel_controls_fail_exact_named_oracles(self):
        controls=[
            ("capacity","geo_enclosures_stage","if(at>=GEO_ENCLOSURE_CAPACITY)","if(at>=GEO_ENCLOSURE_CAPACITY-1)","capacity","capacity-four-in-order"),
            ("canonical","geo_enclosures_stage","memset(&next,0,sizeof next);","memset(&next,0xa5,sizeof next);","storage","store-canonical-unused-padding"),
            ("replace","geo_enclosures_stage","store->values[at].id!=value->id","true","capacity","capacity-replace-stays-in-place"),
            ("tail","geo_enclosures_remove","memset(&store->values[--store->count],0,sizeof store->values[0]);","--store->count;","capacity","capacity-zero-vacated-tail"),
            ("remove-order","geo_enclosures_remove","memmove(store->values+at,store->values+at+1,(store->count-at-1)*sizeof store->values[0]);",";","capacity","capacity-remove-preserves-order"),
            ("empty-cache","geo_enclosures_stage","next.min[axis]=value->min[axis];next.max[axis]=value->max[axis];",
                "next.min[axis]=value->member_count?value->min[axis]:0;next.max[axis]=value->member_count?value->max[axis]:0;","empty-cache","empty-cache-stage-preserves-derived-values"),
            ("clone","geo_enclosures_clone","memcpy(copy,source,sizeof *copy);","memset(copy,0,sizeof *copy);","storage","store-clone-complete-bytes"),
            ("member-capacity","geo_enclosure_evaluate","member_count>GEO_ENCLOSURE_MEMBER_CAPACITY","member_count>GEO_ENCLOSURE_MEMBER_CAPACITY-1","arguments","arguments-eight-enters-member-validation"),
            ("missing-region","geo_enclosure_evaluate","if(!region)return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_MISSING_REGION,member,-1);",
                "if(!region)return true;","identity","identity-missing-region"),
            ("no-carrier","geo_enclosure_evaluate","if(carriers!=1)","if(carriers==0)return true;if(carriers!=1)","identity","identity-no-carrier"),
            ("ambiguous","geo_enclosure_evaluate","if(carriers!=1)","if(!carriers)","identity","identity-ambiguous-before-later-duplicate"),
            ("member-order","geo_enclosure_evaluate","uint32_t member=next.member_ids[i];","uint32_t member=next.member_ids[member_count-1-i];","identity","identity-member-order-first"),
            ("duplicate","geo_enclosure_evaluate","if(next.member_ids[j]==member)","if(false)","identity","identity-duplicate-before-slot"),
            ("slot","geo_enclosure_evaluate","if(occupied[axis][slot])","if(false)","members","member-slot-before-extents"),
            ("extent","geo_enclosure_evaluate","if(extent_low[j].set&&(extent_low[j].value!=low||extent_high[j].value!=high))","if(false)","members","member-extent-x-before-y"),
            ("extent-order","geo_enclosure_evaluate","for(int j=0;j<3;++j)","for(int j=2;j>=0;--j)","members","member-extent-x-before-y"),
            ("lower-plane","geo_enclosure_evaluate","bound[axis][0].set&&extent_low[axis].set&&bound[axis][0].value!=extent_low[axis].value","false","planes","plane-lower-mismatch"),
            ("upper-plane","geo_enclosure_evaluate","bound[axis][1].set&&extent_high[axis].set&&bound[axis][1].value!=extent_high[axis].value","false","planes","plane-upper-mismatch"),
            ("final-axis-order","geo_enclosure_evaluate","for(int axis=0;axis<3;++axis)","for(int axis=2;axis>=0;--axis)","planes","plane-final-x-before-y-z"),
            ("inverted-equal","geo_enclosure_evaluate","bound[axis][0].value>=bound[axis][1].value","bound[axis][0].value>bound[axis][1].value","inverted","inverted-equal-planes"),
            ("closed","geo_enclosure_evaluate","&&occupied[2][1]","","box","box-open-five"),
            ("upper-value","geo_enclosure_evaluate","bound[axis][1].set?bound[axis][1].value:extent_high[axis].value","extent_high[axis].value","partial","single-plane-extents"),
            ("lower-value","geo_enclosure_evaluate","bound[axis][0].set?bound[axis][0].value:extent_low[axis].value","extent_low[axis].value","negative","negative-lower-plane-no-upper-invention"),
            ("negative-u","geo_enclosure_extent","u>0?bounds.min_u:-bounds.max_u","u>0?bounds.min_u:-bounds.min_u","negative","negative-u-extents"),
            ("negative-v","geo_enclosure_extent","v>0?bounds.min_v:-bounds.max_v","v>0?bounds.min_v:-bounds.min_v","negative","negative-v-extents"),
            ("hole-bounds","geo_enclosure_extent","GeoLoop2View outline={region->outline.v,region->outline.count};",
                "GeoLoop2View outline=region->hole_count?(GeoLoop2View){region->holes[0].v,region->holes[0].count}:(GeoLoop2View){region->outline.v,region->outline.count};","outline","outline-hole-does-not-shrink"),
            ("concave-bounds","geo_enclosure_extent","GeoLoop2View outline={region->outline.v,region->outline.count};",
                "GeoLoop2View outline={region->outline.v,region->outline.count>4?4:region->outline.count};","outline","outline-concave-bbox-extremes"),
            ("typed-domain","geo_enclosure_carrier","placement->domain==GEO_PLACEMENT_REGION_REF&&","","typed","typed-inactive-zero-is-not-reference"),
            ("axis-extent-fallback","geo_enclosure_axis_bound","    return false;\n}",
                "    *out=slot?enclosure->max[axis]:enclosure->min[axis];return true;\n}","axis","axis-no-cached-extent-fallback"),
            ("axis-normal","geo_enclosure_axis_bound","if(geo_enclosure_axis(placement->frame.normal)!=axis)continue;","","axis","axis-no-cached-extent-fallback"),
            ("axis-slot","geo_enclosure_axis_bound","(geo_enclosure_vector_component(placement->frame.normal,axis)>0?1:0)==slot","true","axis","axis-normal-slot-sign"),
            ("axis-placement-order","geo_enclosure_axis_bound","geo_placements_at(placements,p)","geo_placements_at(placements,geo_placements_count(placements)-1-p)","axis","axis-first-placement-no-unique-recheck"),
            ("axis-member-order","geo_enclosure_axis_bound","enclosure->member_ids[i]","enclosure->member_ids[enclosure->member_count-1-i]","axis","axis-member-before-placement-order"),
            ("failure-publication","geo_enclosure_evaluate","GeoEnclosure next;memset(&next,0,sizeof next);","memset(out,0,sizeof *out);GeoEnclosure next;memset(&next,0,sizeof next);","identity","identity-missing-region"),
            ("input-alias","geo_enclosure_evaluate","GeoEnclosure next;memset(&next,0,sizeof next);","memset(out,0,sizeof *out);GeoEnclosure next;memset(&next,0,sizeof next);","box","box-input-output-id-alias"),
            ("success-fault","geo_enclosure_evaluate","memcpy(out,&next,sizeof next);return true;","memcpy(out,&next,sizeof next);if(fault)memset(fault,0,sizeof *fault);return true;","box","box-success-fault-and-unused"),
        ]
        build=kernel_only_native();original=(build.kernel/"enclosure.c").read_text(encoding="utf-8")
        source=code(original)
        for name,function,before,after,case,marker in controls:
            with self.subTest(control=name):
                self.case(case)
                body=definition(original,function)
                self.assertEqual(1,body.count(before),"Control must target one actual rule: "+name)
                self.assertEqual(1,source.count(body))
                path=build.kernel/("enclosure-control-"+name+".c")
                path.write_text(source.replace(body,body.replace(before,after)),encoding="utf-8")
                changed=build.compile(path,"enclosure-control-"+name)
                objects=[changed if obj==build.enclosure_object else obj for obj in self.objects]
                mutant=build.link("enclosure-control-"+name,[self.client,*objects])
                self.case(case,mutant,marker)
                self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
