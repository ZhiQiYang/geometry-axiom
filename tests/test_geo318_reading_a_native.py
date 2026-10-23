"""Reading A public W/end-selection/revalidation semantic witnesses.

A compiler failure or abnormal exit is setup failure, never a mutation kill.
The FEATURE cases consume supplied faces, not repaired member rectangles.
"""
from pathlib import Path
import shutil
import re
import subprocess
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_contacts import record_native_execution

CONTROLS = (
    ("partial-admission", "contact_world", "    return WOOD_BOUNDARY_END_PARTIAL;", "    return WOOD_BOUNDARY_END_ORDINARY;", "eligibility", "positive-contact-without-new-minimum"),
    ("real-rc-width", "contact_world", "if(hi-lo>=width&&visible_lo<visible_hi&&", "if(hi-lo>width&&visible_lo<visible_hi&&", "features", "exact-width-rc-feature-refused"),
    ("real-rc-plane", "contact_world", "if(!contact_same_rc_plane(face,other)||", "if(true||", "features", "collinear-rc-subdivision-joined"),
    ("contact-side", "contact_world", "face->edge_index!=(end==0?1:0)", "false", "features", "wrong-side-feature-not-contact"),
    ("collector-partial", "contact_world", "if(admission==WOOD_BOUNDARY_END_PARTIAL)return true;", "if(false)return true;", "spans", "collector-partial-without-fullwidth"),
    ("span-partial", "member_reference", "if(admission==WOOD_BOUNDARY_END_PARTIAL)goto supported_end;", "if(false)goto supported_end;", "spans", "span-accepts-partial-end"),
    ("between-required-source", "member_reference", "s,e,face->fixed==s?0:1,face,&admission)", "s,e,face->fixed==s?0:1,NULL,&admission)", "spans", "between-required-face-must-itself-contact"),
    ("revalidate-partial", "world_validation", "if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;", "if(false)continue;", "revalidation", "r6e-accepts-partial-without-fullwidth-recheck"),
    ("revalidate-still-collides", "world_validation", "if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;", "if(admission==WOOD_BOUNDARY_END_PARTIAL)return true;", "revalidation", "partial-does-not-skip-world-collision"),
)

class ReadingANative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b=native()
        path=b.woodworking / "geo318-boundary-ends-client.c"
        shutil.copy2(ROOT / "tests/geo318_boundary_ends_harness.c",path)
        cls.client=b.compile(path,"geo318-boundary-ends-client")
        cls.exe=b.link("geo318-boundary-ends-client",cls.objects(b))

    @classmethod
    def objects(cls,b,changed=None,module=None):
        originals={"contact_world":b.wood_contact_world_object,"member_reference":b.wood_member_reference_object,"world_validation":b.wood_world_validation_object}
        return [cls.client,*[changed if changed is not None and obj==originals[module] else obj for obj in b.product_objects()]]

    def case(self,name,exe=None,*,phase="positive",control=None,assertion=None):
        command=[str(exe or self.exe),name]
        run=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=20)
        record_native_execution(self.id(),command,run,case=name,phase=phase,control=control,assertion=assertion)
        self.assertIn(run.returncode,(0,1),"Crash/setup failure is not a semantic verdict: "+run.stderr)
        if run.returncode:
            self.assertRegex(run.stderr,r"ASSERT:[a-z0-9-]+")
        return run

    def test_fixed_whole_positioning_edge_endpoint_placed_contact_and_roles(self):
        self.assertEqual(0,self.case("eligibility").returncode)

    def test_returned_features_real_rc_span_exact_width_and_collinear_faces(self):
        self.assertEqual(0,self.case("features").returncode)

    def test_actual_span_between_named_source_bare_rc_and_source_failure(self):
        self.assertEqual(0,self.case("spans").returncode)

    def test_r6e_partial_single_full_rc_source_failure_and_collision(self):
        self.assertEqual(0,self.case("revalidation").returncode)

    @classmethod
    def host_executable(cls, withdrawn=False):
        """Relocate only four include-chain files, never mutate this checkout."""
        b=native()
        if not hasattr(cls,"host_cache"):
            cls.host_cache={}
        if withdrawn in cls.host_cache:
            return cls.host_cache[withdrawn]
        paths=("current_geometry.c","geometry-core/references.inc","geometry-web/web_bridge.c",
               "tests/geo318_host_boundary_ends_harness.c")
        directory=b.work/("geo318-host-withdrawn" if withdrawn else "geo318-host-baseline")
        destinations={(ROOT/name).resolve():directory/name for name in paths}
        for name in paths:
            original=ROOT/name
            source=original.read_text(encoding="utf-8")
            if withdrawn and name=="geometry-core/references.inc":
                before="if(!wood_contact_end_support_check(admission,hits,a->has_between,detail,sizeof detail))"
                after="if(!hits || (!a->has_between && hits!=1))"
                if source.count(before)!=1:
                    raise AssertionError("Actual H collector withdrawal must change exactly one delegate")
                source=source.replace(before,after)
            def relocate(match):
                include=(original.parent/match.group(1)).resolve()
                target=destinations.get(include,include)
                return '#include "'+target.as_posix()+'"' if target.is_file() or include in destinations else match.group(0)
            target=destinations[original.resolve()]
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(re.sub(r'^#include "([^"\n]+)"',relocate,source,flags=re.M),encoding="utf-8")
        defines=["GEOMETRY_KERNEL_EXTERNAL=1","GEOMETRY_WOODWORKING_EXTERNAL=1",
                 "GEOMETRY_HOST_HISTORY_EXTERNAL=1","GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"]
        client=b.compile(destinations[(ROOT/paths[-1]).resolve()],"geo318-host-"+str(withdrawn),defines)
        cls.host_cache[withdrawn]=b.link("geo318-host-"+str(withdrawn),[client,*b.product_objects()])
        return cls.host_cache[withdrawn]

    def test_actual_host_collector_partial_and_i11_wiring_on_explicit_world(self):
        # This deliberately does not assert parse/load/rebuild reachability.
        self.assertEqual(0,self.case("host-collector",self.host_executable()).returncode)

    def test_actual_host_collector_withdrawal_fails_named_assertion_then_restores(self):
        self.assertEqual(0,self.case("host-collector",self.host_executable(),phase="baseline",control="host-collector").returncode)
        result=self.case("host-collector",self.host_executable(True),phase="mutant",control="host-collector",
                         assertion="actual-host-collector-accepts-partial")
        self.assertEqual(1,result.returncode)
        self.assertIn("ASSERT:actual-host-collector-accepts-partial",result.stderr)
        self.assertEqual(0,self.case("host-collector",self.host_executable(),phase="restored",control="host-collector").returncode)

    def test_nine_actual_source_controls_fail_named_assertions_then_restore(self):
        b=native()
        for name,module,before,after,case,assertion in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0,self.case(case,phase="baseline",control=name).returncode)
                text=(b.woodworking/(module+".c")).read_text(encoding="utf-8")
                self.assertEqual(1,text.count(before),"Control must change exactly one actual source site: "+name)
                path=b.woodworking/("geo318-"+name+".c")
                path.write_text(text.replace(before,after),encoding="utf-8")
                changed=b.compile(path,"geo318-"+name)
                exe=b.link("geo318-mutant-"+name,self.objects(b,changed,module))
                result=self.case(case,exe,phase="mutant",control=name,assertion=assertion)
                self.assertEqual(1,result.returncode,"Mutation survived: "+name)
                self.assertIn("ASSERT:"+assertion,result.stderr)
                self.assertEqual(0,self.case(case,phase="restored",control=name).returncode)

if __name__ == "__main__":
    unittest.main(verbosity=2)
