"""Ordered face runs skip redundant merge work, without changing any face.

The observed counter counts calls of the actual product comparator. The n-1
bound is the exact number of binary merge-tree boundaries for sorted input;
it is not a wall-time threshold. Existing W/contact tests remain unchanged.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_contacts import record_native_execution

FAST_PATH = "if(middle==end||contact_face_index_before(out,index->sorted[middle-1],index->sorted[middle])){"
COMPARATOR = "static bool contact_face_index_before(const WoodStopFace *out,size_t a,size_t b)\n{"

CLIENT = r'''
#define REQUIRE(name,condition) do {if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}} while(0)
static void geo348_face(WoodStopFace *face,GeoCoord fixed,GeoCoord lo,GeoCoord hi,size_t ordinal)
{
    memset(face,0,sizeof *face);face->kind=WOOD_STOP_MEMBER_SIDE;
    face->timber_id=(uint32_t)(ordinal+1);face->hole_index=-1;
    face->edge_index=(int)ordinal;face->fixity=WOOD_STOP_FIXED;
    face->fixed=fixed;face->lo=lo;face->hi=hi;
}
static int geo348_ordered(size_t count)
{
    WoodStopFace out[128],original[128];ContactFaceIndex index;
    memset(out,0,sizeof out);memset(&index,0xa5,sizeof index);
    for(size_t i=0;i<count;++i)
        geo348_face(&out[i],(GeoCoord)(i/4),(GeoCoord)((i%4)/2),30+(GeoCoord)i,i);
    memcpy(original,out,sizeof out);geo348_run_comparisons=0;
    contact_face_index_build(&index,out,count);
    printf("ordered=%zu comparator_calls=%llu exact_bound=%zu\n",count,
        (unsigned long long)geo348_run_comparisons,count?count-1:0);
    REQUIRE("contact-face-ordered-runs-linear-comparisons",
        geo348_run_comparisons==(count?count-1:0));
    REQUIRE("contact-face-index-keeps-public-bytes",!memcmp(original,out,sizeof out));
    for(size_t i=0;i<count;++i){
        size_t end=(i/4+1)*4;if(end>count)end=count;
        REQUIRE("contact-face-ordered-stable-rank",index.sorted[i]==i&&index.rank[i]==i);
        REQUIRE("contact-face-ordered-plane-ranges",index.scratch[i]==i/4*4&&index.plane_end[i]==end);
        REQUIRE("contact-face-index-fresh-maximum",index.maximum[i]==0);
    }
    return 0;
}
static int geo348_unsorted(void)
{
    const GeoCoord fixed[8]={2,-1,2,INT64_MIN,INT64_MAX,-1,2,2};
    const GeoCoord lo[8]={4,5,0,-9,0,5,0,-2};
    const size_t expected[8]={3,1,5,7,2,6,0,4};
    WoodStopFace out[8],original[8];ContactFaceIndex index;
    memset(&index,0xa5,sizeof index);
    for(size_t i=0;i<8;++i)geo348_face(&out[i],fixed[i],lo[i],40+(GeoCoord)i,i);
    memcpy(original,out,sizeof out);geo348_run_comparisons=0;
    contact_face_index_build(&index,out,8);
    REQUIRE("contact-face-equal-keys-retain-original-ordinal",index.rank[1]<index.rank[5]&&index.rank[2]<index.rank[6]);
    REQUIRE("contact-face-unsorted-stable-full-coordinate-order",
        !memcmp(expected,index.sorted,sizeof expected));
    REQUIRE("contact-face-index-keeps-public-bytes",!memcmp(original,out,sizeof out));
    for(size_t i=0;i<8;++i){
        size_t begin=i,end=i+1;
        while(begin&&fixed[expected[begin-1]]==fixed[expected[i]])--begin;
        while(end<8&&fixed[expected[end]]==fixed[expected[i]])++end;
        REQUIRE("contact-face-unsorted-rank-plane-metadata",index.rank[expected[i]]==i&&
            index.scratch[i]==begin&&index.plane_end[i]==end&&index.maximum[i]==0);
    }
    return 0;
}
static int geo348_coverage(void)
{
    WoodStopFace out[6];ContactFaceIndex index;
    geo348_face(&out[0],7,0,100,0);geo348_face(&out[1],7,10,20,1);
    geo348_face(&out[2],7,100,110,2);geo348_face(&out[3],INT64_C(4294967303),10,20,3);
    geo348_face(&out[4],7,-10,10,4);geo348_face(&out[5],7,10,120,5);
    memset(&index,0xa5,sizeof index);contact_face_index_build(&index,out,6);
    REQUIRE("contact-face-no-old-active-witness",!contact_face_index_covered(&index,out,6,&out[1]));
    contact_face_index_insert(&index,out,6,0);
    REQUIRE("contact-face-covered-real-single-witness",contact_face_index_covered(&index,out,6,&out[1]));
    REQUIRE("contact-face-touching-not-cover",!contact_face_index_covered(&index,out,6,&out[2]));
    REQUIRE("contact-face-full-width-plane-isolated",!contact_face_index_covered(&index,out,6,&out[3]));
    REQUIRE("contact-face-partial-span-not-cover",!contact_face_index_covered(&index,out,6,&out[4])&&
        !contact_face_index_covered(&index,out,6,&out[5]));
    contact_face_index_build(&index,out,6);
    REQUIRE("contact-face-rebuild-clears-active-witness",!contact_face_index_covered(&index,out,6,&out[1]));
    return 0;
}
int main(int argc,char **argv)
{
    REQUIRE("contact-face-runs-mode",argc==2);
    if(!strcmp(argv[1],"ordered128"))return geo348_ordered(128);
    if(!strcmp(argv[1],"ordered127"))return geo348_ordered(127);
    if(!strcmp(argv[1],"empty-single")){int result=geo348_ordered(0);return result?result:geo348_ordered(1);}
    if(!strcmp(argv[1],"unsorted"))return geo348_unsorted();
    if(!strcmp(argv[1],"coverage"))return geo348_coverage();
    REQUIRE("contact-face-runs-known-mode",false);return 1;
}
'''


class ContactFaceOrderedRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.source = (build.woodworking / "contact_world.c").read_text(encoding="utf-8")
        cls.baseline = cls.executable(cls.source, "baseline")

    @classmethod
    def executable(cls, source, phase):
        if source.count(COMPARATOR) != 1:
            raise AssertionError("Actual comparator counter anchor must occur once")
        source = source.replace(COMPARATOR,
            "static uint64_t geo348_run_comparisons;\n" + COMPARATOR + "\n    ++geo348_run_comparisons;")
        build = native()
        path = build.woodworking / ("contact-face-runs-" + phase + ".c")
        path.write_text(source + CLIENT, encoding="utf-8")
        changed = build.compile(path, "contact-face-runs-" + phase)
        return build.link("contact-face-runs-" + phase, [changed,
            build.wood_contacts_object, build.wood_supports_object, *build.kernel_objects()])

    def case(self, executable, mode, phase="positive", assertion=None):
        command = [str(executable), mode]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", timeout=20)
        record_native_execution(self.id(), command, result, case=mode,
                                phase=phase, control="face-runs", assertion=assertion)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a mutant kill: " + result.stderr)
        return result

    def positive(self, mode):
        result = self.case(self.baseline, mode)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_sorted_power_of_two_has_exact_n_minus_one_comparisons(self):
        self.positive("ordered128")

    def test_sorted_uneven_tail_has_exact_n_minus_one_comparisons(self):
        self.positive("ordered127")

    def test_empty_and_singleton_need_no_comparison(self):
        self.positive("empty-single")

    def test_unsorted_runs_keep_stable_full_width_order_and_metadata(self):
        self.positive("unsorted")

    def test_coverage_uses_fresh_single_witness_and_full_width_plane(self):
        self.positive("coverage")

    def withdrawal(self, before, after, mode, name, assertion):
        self.assertEqual(1, self.source.count(before), "Withdrawal must change one actual product site")
        baseline = self.case(self.baseline, mode, "baseline", assertion)
        self.assertEqual(0, baseline.returncode, baseline.stderr)
        mutant = self.executable(self.source.replace(before, after), name)
        result = self.case(mutant, mode, "mutant", assertion)
        self.assertEqual(1, result.returncode, "Withdrawal survived: " + name)
        self.assertIn("ASSERT:" + assertion, result.stderr)
        restored = self.case(self.baseline, mode, "restored", assertion)
        self.assertEqual(0, restored.returncode, restored.stderr)

    def test_removing_run_skip_fails_its_named_work_bound(self):
        self.withdrawal(FAST_PATH, "if(false){", "ordered128", "remove-skip",
                        "contact-face-ordered-runs-linear-comparisons")

    def test_unconditional_skip_fails_the_real_unsorted_order(self):
        self.withdrawal(FAST_PATH, "if(true){", "unsorted", "unconditional-skip",
                        "contact-face-unsorted-stable-full-coordinate-order")

    def test_unstable_equal_keys_fail_the_original_ordinal_order(self):
        self.withdrawal("return plane<0||(plane==0&&out[a].lo<=out[b].lo);",
                        "return plane<0||(plane==0&&out[a].lo<out[b].lo);",
                        "unsorted", "unstable-tie",
                        "contact-face-equal-keys-retain-original-ordinal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
