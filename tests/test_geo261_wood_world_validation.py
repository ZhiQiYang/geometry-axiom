"""Final-world W participation, scopes, support order and obstacle policy."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests import geo300_scene_generator as scene_generator
from tests.test_geo261_native_kernel import native

COLUMN_GUARD="if(geo_rect_overlap_positive(&left,&right))return false;\n        }\n    }\n    for(size_t i=0;i<beam_count;"
SELECT_COMPONENT_GUARD="if(footprint)out->b=placement_boundary_for_rect(out->p,out->b,footprint);"
PRODUCT_DEFINES=["GEOMETRY_KERNEL_EXTERNAL=1","GEOMETRY_WOODWORKING_EXTERNAL=1",
    "GEOMETRY_HOST_HISTORY_EXTERNAL=1","GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"]


def copy_product_closure(entry,destination):
    """Copy only actual quoted includes, retaining paths for one H mutation.

    Public include-path headers come from NativeBuild's normal isolated K
    headers. No repository file is edited and no H policy is reconstructed.
    """
    pending=[entry.resolve()];seen=set()
    while pending:
        source=pending.pop()
        if source in seen:continue
        relative=source.relative_to(ROOT);seen.add(source)
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        data=source.read_bytes();target.write_bytes(data)
        for include in re.findall(rb'^\s*#\s*include\s*"([^"]+)"',data,re.M):
            child=(source.parent/include.decode("utf-8")).resolve()
            if child.is_file():
                child.relative_to(ROOT)
                pending.append(child)
    return destination/entry.relative_to(ROOT)


class WorldValidationBoundary(unittest.TestCase):
    def test_world_policy_uses_only_public_values_and_explicit_candidate_context(self):
        source=(ROOT/"geometry-templates/woodworking/native/world_validation.c").read_text(encoding="utf-8")
        code=re.sub(r"/\*.*?\*/|//[^\n]*","",source,flags=re.S)
        self.assertNotRegex(code,r"\b(?:World|TimberAnchor|scene_error|world_find_placement|g_revalidate_error)\b")
        self.assertEqual(["world_validation.h"],re.findall(r'^#include "([^"]+)"',source,re.M))
        self.assertEqual(1,source.count(COLUMN_GUARD))

    def test_host_adapters_delegate_member_and_obstacle_rules(self):
        source=(ROOT/"current_geometry.c").read_bytes().decode("utf-8").replace("\r\n","\n")
        start=source.index("static bool world_validate_derived(")
        code=source[start:source.index("static bool world_revalidate_candidate(",start)]
        self.assertIn("wood_world_validate_members",code)
        self.assertIn("app_world_obstacles_valid",code)
        self.assertNotIn("ANCHOR_AT_GRID",code)
        self.assertNotIn("wood_stop_count_legal",code)
        self.assertNotIn("world->wood.column_count",code)


class WoodWorldValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.woodworking/"world-validation-client.c"
        shutil.copy2(ROOT/"tests/geo261_world_validation_harness.c",source)
        cls.client=build.compile(source,"world-validation-client")
        cls.exe=build.link("world-validation-client",[cls.client,*build.product_objects()])

    def case(self,name,exe=None,marker=None):
        result=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=10)
        self.assertEqual(1 if marker else 0,result.returncode,result.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",result.stderr)

    def test_support_uniqueness_between_free_and_local_probe_identity(self): self.case("support")
    def test_missing_host_grid_placement_end_and_role_error_order(self): self.case("phases")
    def test_positive_area_collision_obeys_host_and_placed_membership(self): self.case("collision")
    def test_primary_and_secondary_direction_policy(self): self.case("axis")
    def test_rule_anchor_uses_real_source_binding_and_complete_parent_cell(self): self.case("rule")
    def test_subgrid_anchor_uses_real_child_bounds_and_full_footprint(self): self.case("subgrid")
    def test_stagger_anchor_uses_real_lattice_and_closed_band_bounds(self): self.case("stagger")
    def test_column_plan_collision_volume_room_and_beam_exemption(self): self.case("obstacles")

    def mutant(self,name,before,after,bridge=False):
        build=native();source=(build.woodworking/"world_validation.c").read_text(encoding="utf-8")
        self.assertEqual(1,source.count(before),"Control must replace one production rule")
        path=build.woodworking/(name+".c");path.write_text(source.replace(before,after),encoding="utf-8")
        obj=build.compile(path,name)
        self.assertEqual(1,build.product_objects().count(build.wood_world_validation_object))
        objects=[obj if item==build.wood_world_validation_object else item for item in build.product_objects()]
        exe=build.link(name,[self.client,*objects])
        if not bridge:return exe
        build.bridge();return exe,build.link(name+"-bridge",[build.bridge_object,*objects])

    def test_removed_rules_fail_exact_named_assertions(self):
        controls=[("validation-unplaced","if(!member->placed)continue;","","phases","validation-unplaced-skipped"),
            ("validation-unique","(!fact.has_between&&hits!=1)","false","support","validation-unique-stops"),
            ("validation-presence","!hits||","","support","validation-between-needs-stop"),
            ("validation-collision","if(geo_rect_overlap_positive(&left,&right))return false;\n        }\n    }\n    WoodMemberAxisFact", "if(false)return false;\n        }\n    }\n    WoodMemberAxisFact","collision","validation-positive-collision"),
            ("validation-same-host","||a.placement_id!=b.placement_id","","collision","validation-separate-hosts"),
            ("validation-pair-placed","if(!b.member->placed||","if(","collision","validation-unplaced-no-collision"),
            ("validation-axis","if(!wood_member_primary_axis_check(","if(false&&!wood_member_primary_axis_check(","axis","validation-primary-axis"),
            ("validation-volume","obstacle->max[axis]<=obstacle->min[axis]","obstacle->max[axis]<obstacle->min[axis]","obstacles","validation-positive-volume"),
            ("validation-rule-scope","!context->footprint(context->user,i,fact.placement_id,&footprint)||!validation_inside(&footprint,&cell)",
                "!context->footprint(context->user,i,fact.placement_id,&footprint)||false","rule","validation-rule-full-cell"),
            ("validation-subgrid-scope","grid&&grid->is_subgrid&&(!wood_grid_cell_bounds",
                "false&&grid&&grid->is_subgrid&&(!wood_grid_cell_bounds","subgrid","validation-subgrid-full-cell"),
            ("validation-stagger-lower","||flo<lo||fhi>hi","||false||fhi>hi","stagger","validation-stagger-lower-bound"),
            ("validation-stagger-upper","||flo<lo||fhi>hi","||flo<lo||false","stagger","validation-stagger-upper-bound")]
        for name,before,after,case,marker in controls:
            with self.subTest(control=name):
                self.case(case);exe=self.mutant(name,before,after);self.case(case,exe,marker);self.case(case)

    def commit_line(self,session,line):
        response=session.command("line "+line)
        if "preview" in response:
            if not response["preview"]["valid"]:return False,response
            response=session.command("line confirm "+str(response["preview"]["token"]))
        return bool(response.get("ok")),response

    def overlapping_columns(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command("reset")["ok"])
            accepted,response=self.commit_line(session,"column 1 at 0 0 size 20 20 z 0 100")
            self.assertTrue(accepted,response)
            before=session.command("dump")["text"]
            accepted,response=self.commit_line(session,"column 2 at 10 10 size 20 20 z 1000 1100")
            after=session.command("dump")["text"]
            if accepted:self.assertIn("column 2 ",after)
            else:self.assertEqual(before,after,"Rejected overlap must retain the complete candidate world")
            return accepted,response

    def test_column_collision_guard_controls_actual_bridge_and_atomic_refusal(self):
        build=native();accepted,response=self.overlapping_columns(build.bridge());self.assertFalse(accepted,response)
        self.case("obstacles")
        exe,bridge=self.mutant("validation-column",COLUMN_GUARD,COLUMN_GUARD.replace("if(geo_rect_overlap_positive(&left,&right))return false;","if(false)return false;"),True)
        self.case("obstacles",exe,"validation-column-plan-overlap")
        accepted,response=self.overlapping_columns(bridge);self.assertTrue(accepted,response)
        self.case("obstacles");accepted,response=self.overlapping_columns(build.bridge());self.assertFalse(accepted,response)


class WorldValidationProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();cls.harness=ROOT/"tests/geo261_world_validation_product_harness.c"
        obj=build.compile(cls.harness,"world-validation-product-client",PRODUCT_DEFINES)
        cls.exe=build.link("world-validation-product-client",[obj,*build.product_objects()])

    def selected_component(self,exe,marker=None):
        result=subprocess.run([str(exe),"selected-component"],capture_output=True,text=True,encoding="utf-8",timeout=10)
        self.assertEqual(1 if marker else 0,result.returncode,result.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",result.stderr)
        self.assertEqual("",result.stdout)

    def test_actual_bridge_candidate_selects_component_and_keeps_copied_geometry(self):
        self.selected_component(self.exe)

    def test_removing_actual_host_selector_changes_final_validation_verdict(self):
        build=native();self.selected_component(self.exe)
        destination=build.work/"world-validation-host-selector"
        harness=copy_product_closure(self.harness,destination)
        adapter=destination/"geometry-app/native/world_validation.inc"
        source=adapter.read_text(encoding="utf-8")
        self.assertEqual(1,source.count(SELECT_COMPONENT_GUARD),"Control must remove one actual H selector")
        adapter.write_text(source.replace(SELECT_COMPONENT_GUARD,""),encoding="utf-8")
        obj=build.compile(harness,"world-validation-product-no-selector",PRODUCT_DEFINES)
        mutant=build.link("world-validation-product-no-selector",[obj,*build.product_objects()])
        self.selected_component(mutant,"validation-product-selected-component-verdict")
        self.selected_component(self.exe)



class MemberValidationHostWork(unittest.TestCase):
    """GEO-381: the final member validation reads each host a bounded number of
    times per placed member on the real step-by-step generator history.

    The H host callback gets a counter and the one real call site prints the
    per-validation total; W policy and the published World are untouched."""
    MARKER=b"GEO381-MEMBER-VALIDATION "
    HOST=b"static bool app_validation_host(void *user,uint32_t id,const GeoRect2 *footprint,WoodGridHost *out)\n{"
    CALL=b"    if(!wood_world_validate_members(&context,error,sizeof error)){\r\n"
    # Named withdrawal: confirm the host again for every same-host pair.
    ONCE="(!host_confirmed&&!context->host(context->user,a.placement_id,NULL,&host))||"
    EVERY="(!context->host(context->user,a.placement_id,NULL,&host))||"

    @classmethod
    def setUpClass(cls):
        text,_=scene_generator.build(24,"single")
        cls.statements=[line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        commands=["reset"]+["line "+s for s in cls.statements]+["dump","references","line timber 25 27 33 role primary","dump"]
        cls.payload="".join(c+"\n" for c in commands).encode("utf-8")

    def counted_bridge(self,label,withdraw=False):
        build=native();destination=build.work/("geo381-host-closure-"+label);destination.mkdir()
        entry=copy_product_closure(ROOT/"geometry-web/web_bridge.c",destination)
        adapter=destination/"geometry-app/native/world_validation.inc";source=adapter.read_bytes()
        self.assertEqual(1,source.count(self.HOST),"one actual H host callback")
        adapter.write_bytes(source.replace(self.HOST,b"static size_t geo381_host_reads;\n"+self.HOST+b"++geo381_host_reads;"))
        host=destination/"current_geometry.c";source=host.read_bytes()
        self.assertEqual(1,source.count(self.CALL),"one actual final member validation")
        host.write_bytes(source.replace(self.CALL,
            b"    size_t geo381_before=geo381_host_reads,geo381_placed=0;\r\n"
            b"    for(size_t k=0;k<world->wood.timber_count;++k)geo381_placed+=world->wood.timbers[k].placed;\r\n"
            b"    bool geo381_ok=wood_world_validate_members(&context,error,sizeof error);\r\n"
            b"    fprintf(stderr,\"GEO381-MEMBER-VALIDATION %zu %zu %zu\\n\",geo381_placed,context.grids.state->count,geo381_host_reads-geo381_before);\r\n"
            b"    if(!geo381_ok){\r\n"))
        obj=build.compile(entry,"geo381-host-"+label,PRODUCT_DEFINES)
        objects=build.product_objects()
        self.assertEqual(1,objects.count(build.wood_world_validation_object))
        if withdraw:
            source=(build.woodworking/"world_validation.c").read_text(encoding="utf-8")
            self.assertEqual(1,source.count(self.ONCE),"Named withdrawal must change one actual site")
            path=build.woodworking/"geo381-host-every-pair.c";path.write_text(source.replace(self.ONCE,self.EVERY),encoding="utf-8")
            changed=build.compile(path,"geo381-host-every-pair")
            objects=[changed if item==build.wood_world_validation_object else item for item in objects]
        return build.link("geo381-host-"+label,[obj,*objects])

    def host_work(self,bridge):
        result=_bridge.run_once(self.payload,text=False,bridge=bridge,timeout=600)
        self.assertEqual(0,result.returncode,result.stderr)
        rows=[tuple(map(int,line.split()[1:])) for line in result.stderr.splitlines() if line.startswith(self.MARKER)]
        other=b"".join(line+b"\n" for line in result.stderr.splitlines() if not line.startswith(self.MARKER))
        return result.stdout,other,rows

    def test_real_history_reads_each_host_linearly_and_withdrawal_is_red(self):
        plain=_bridge.run_once(self.payload,text=False,bridge=native().bridge(),timeout=600)
        self.assertEqual(0,plain.returncode,plain.stderr)
        self.assertNotIn(self.MARKER,plain.stderr,"product bridge must not carry the test marker")
        stdout,stderr,rows=self.host_work(self.counted_bridge("fixed"))
        self.assertEqual((plain.stdout,plain.stderr),(stdout,stderr),"marker must not change replies or stderr")
        self.assertEqual(24,max(placed for placed,_,_ in rows),"the real history validates all 24 placed members")
        worst=max(reads-grids-4*placed for placed,grids,reads in rows)
        print("geo381-host phase=fixed validations=%d max_reads=%d max_excess_over_grids_plus_4n=%d"%(len(rows),max(r for _,_,r in rows),worst))
        for placed,grids,reads in rows:
            self.assertLessEqual(reads,grids+4*placed,"ASSERT:geo381-member-validation-host-reads-linear")
        stdout,stderr,red=self.host_work(self.counted_bridge("withdrawn",withdraw=True))
        print("geo381-host phase=withdrawn max_reads=%d max_excess_over_grids_plus_4n=%d"%(max(r for _,_,r in red),max(r-g-4*p for p,g,r in red)))
        self.assertEqual((plain.stdout,plain.stderr),(stdout,stderr),"both loops publish the same World")
        self.assertTrue(any(reads>grids+4*placed for placed,grids,reads in red),"withdrawal must restore the per-pair reads")
        self.assertEqual(rows,self.host_work(self.counted_bridge("restored"))[2])

if __name__=="__main__":unittest.main(verbosity=2)
