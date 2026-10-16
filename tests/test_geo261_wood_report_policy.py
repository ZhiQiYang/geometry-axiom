"""GEO-075 report grouping/order and I3 defaults, including real CLI controls."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native


class ReportPolicyBoundary(unittest.TestCase):
    def test_policy_modules_do_not_import_application_state_or_render_text(self):
        for name in ("cut_list", "boundary_policy"):
            source=(ROOT/f"geometry-templates/woodworking/native/{name}.c").read_text(encoding="utf-8")
            code=re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code,r"\b(?:World|Timber|printf|scene_error|world_find_timber)\b")
            self.assertEqual([name+".h"],re.findall(r'^#include "([^"]+)"',source,re.M))

    def test_application_keeps_report_codec_and_calls_template_policy(self):
        source=(ROOT/"current_geometry.c").read_bytes().decode("utf-8").replace("\r\n","\n")
        report=source[source.index("static void print_cut_list("):source.index("\nint main(")]
        self.assertIn("wood_cut_list_collect",report)
        self.assertNotIn("bool swap",report)
        self.assertNotIn("total_length +=",report)
        self.assertIn("wood_boundary_default_fixity(out->fixity,4)",source)
        self.assertIn("wood_boundary_default_fixity(loop->fixity,POLY_MAX_VERTICES)",source)


class WoodReportPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native(); source=build.woodworking/"report-policy-client.c"
        shutil.copy2(ROOT/"tests/geo261_report_policy_harness.c",source)
        cls.client=build.compile(source,"report-policy-client")
        cls.exe=build.link("report-policy-client",[cls.client,build.wood_cut_list_object,build.wood_boundary_policy_object])

    def case(self,name,exe=None,marker=None):
        result=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=10)
        self.assertEqual(1 if marker else 0,result.returncode,result.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",result.stderr)

    def test_grouping_retains_exact_spec_identity_id_order_and_placed_participation(self): self.case("grouping")
    def test_group_order_is_descending_length_then_a_b_role(self): self.case("ordering")
    def test_empty_full_and_rejected_capacity_preserve_inputs(self): self.case("limits")
    def test_default_fixed_writes_only_requested_prefix_or_full_loop(self): self.case("fixity")

    def mutant(self,module,name,before,after):
        build=native(); source=(build.woodworking/(module+".c")).read_text(encoding="utf-8")
        self.assertEqual(1,source.count(before),"Control must replace exactly one production expression")
        path=build.woodworking/(name+".c");path.write_text(source.replace(before,after),encoding="utf-8")
        obj=build.compile(path,name)
        cut=obj if module=="cut_list" else build.wood_cut_list_object
        fixity=obj if module=="boundary_policy" else build.wood_boundary_policy_object
        return build.link(name,[self.client,cut,fixity]),obj

    def test_removed_participation_role_and_fixity_policies_fail_named_assertions(self):
        controls=[("cut_list","report-unplaced","if(!member->placed)continue;","","grouping","report-placed-only"),
            ("cut_list","report-role","&&group->role==member->role","","grouping","report-exact-spec-identity"),
            ("boundary_policy","report-free","fixity[i]=WOOD_EDGE_FIXED","fixity[i]=WOOD_EDGE_FREE","fixity","fixity-default-fixed")]
        for module,name,before,after,case,marker in controls:
            with self.subTest(control=name):
                self.case(case);exe,_=self.mutant(module,name,before,after);self.case(case,exe,marker);self.case(case)

    def cli_report(self,exe):
        with tempfile.TemporaryDirectory(prefix="geometry-report-") as directory:
            result=subprocess.run([str(exe),"--no-window","--scene",str(ROOT/"room_a.scene"),"--out",str(Path(directory)/"scene.svg")],capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(0,result.returncode,result.stderr)
        start=result.stdout.index("=== 下料清單 ===")
        end=result.stdout.index("\n=== SVG 三視圖 ===",start)
        return result.stdout[start:end]

    def test_sort_control_changes_actual_cli_report_and_restoration_recovers_exact_text(self):
        build=native();expected="=== 下料清單 ===\n4000x20x20 boundary x2（角材 90、91）\n2960x27x33 primary x1（角材 1）\n合計 3 支，2 種規格，總長 10960 mm\n"
        baseline=self.cli_report(build.cli());self.assertEqual(expected,baseline)
        self.case("ordering")
        exe,obj=self.mutant("cut_list","report-reverse-length","right->length>left->length","right->length<left->length")
        self.case("ordering",exe,"report-length-order")
        cli=build.compile(ROOT/"current_geometry.c","report-policy-cli",["GEOMETRY_KERNEL_EXTERNAL=1","GEOMETRY_WOODWORKING_EXTERNAL=1","GEOMETRY_HOST_HISTORY_EXTERNAL=1","GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        self.assertEqual(1,build.product_objects().count(build.wood_cut_list_object))
        objects=[obj if item==build.wood_cut_list_object else item for item in build.product_objects()]
        mutant=build.link("report-policy-mutant-cli",[cli,*objects])
        changed=self.cli_report(mutant)
        self.assertEqual(expected.replace("4000x20x20 boundary x2（角材 90、91）\n2960x27x33 primary x1（角材 1）", "2960x27x33 primary x1（角材 1）\n4000x20x20 boundary x2（角材 90、91）"),changed)
        self.case("ordering");self.assertEqual(expected,self.cli_report(build.cli()))


if __name__=="__main__": unittest.main(verbosity=2)
