"""PF-3: D43 effective seams, R43 exact support and PF23/24 native results."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_panel_fill_host as pfh


class PanelFillSupport(unittest.TestCase):
    setUpClass = pfh.PanelFillHost.__dict__["setUpClass"]
    setUp = pfh.PanelFillHost.setUp
    command = pfh.PanelFillHost.command
    load_text = pfh.PanelFillHost.load_text
    read = pfh.PanelFillHost.read
    snapshot = pfh.PanelFillHost.snapshot
    preview = pfh.PanelFillHost.preview
    apply = pfh.PanelFillHost.apply
    seed = pfh.PanelFillHost.seed
    reject = pfh.PanelFillHost.reject
    host = pfh.PanelFillHost.host
    timbers = pfh.PanelFillHost.timbers

    def derived(self):
        d = self.read()["state"]["panelFills"][0]["derived"]
        self.assertNotIn("error",d,"PF3_UNPLACED: valid committed World always has complete support output")
        self.assertIsInstance(d["effectiveSeams"], list, "PF3_EFFECTIVE_SEAMS_MISSING")
        self.assertIsInstance(d["support"], list, "PF3_SUPPORT_MISSING")
        for s in d["support"]:
            self.assertEqual(("supported","green") if s["supported"] else ("insufficient","red"),
                             (s["status"],s["colour"]),"D44_RESULT: insufficient has explicit red status and actual widths")
        return d

    def widths(self, d=None, axis="u", coordinate=100):
        d = d or self.derived()
        ids = [i for i,s in enumerate(d["effectiveSeams"]) if s["axis"]==axis and s["coordinate"]==coordinate]
        return [[*s["range"],s["left"],s["right"],s["supported"]] for s in d["support"] if s["seam"] in ids]

    def e1(self, x=105):
        self.seed(width=915,length=1830,outline="0,0 1000,0 1000,300 0,300",
                  extra=f"column 1 at {x} 50 size {200-x} 50 z -2400 9\n",obstacles=["c1"])
        self.apply([pfh.fill(origin=[-815,-100],gap=0),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
        self.timbers()

    def parameter(self, value="8", fields=None):
        fields = fields if fields is not None else [dict(id=1,name="X",type="dimension",input=value)]
        path=self.directory/"parameter.json"
        path.write_text(json.dumps(dict(schema="engineering-transaction/1",expectedRevision=self.read()["revision"],
                                       operations=[dict(op="put-parameter",value=dict(id=90,name="renamed",fields=fields))])))
        return self.command("engineering-preview "+str(path))["preview"]

    def test_PF23_E1_legal_five_actual_widths_and_threshold_only(self):
        self.e1()
        expected=[[0,27,100,900,True],[27,50,10,20,True],[50,100,10,5,False],[100,273,10,20,True],[273,300,100,900,True]]
        self.assertEqual(expected,self.widths(),"PF23_LEGAL: every maximal pair of widths must be preserved")
        p=self.parameter("5");self.assertTrue(p["valid"],p)
        after=p["after"]["panelFill"]["panelFills"][0]["derived"]
        self.assertEqual([row[:4]+[True] for row in expected],self.widths(after),"PF23_X5: merge widths, never colours")
        self.assertEqual(expected,self.widths(),"I8a: preview cannot commit")

    def test_PF24_E2_E3_legal_merge_identical_widths(self):
        expected=[[0,27,100,900,True],[27,273,10,20,True],[273,300,100,900,True]]
        for x in (125,120):
            self.e1(x)
            self.assertEqual(expected,self.widths(),"PF24: irrelevant/contact obstacle vertices cannot split equal widths")

    def algorithm(self, rectangles):
        from tests import binaries
        binary=Path(os.environ.get("GEOMETRY_TEST_PF3_ALGORITHM",str(binaries.BY_NAME["pf3-algorithm"].path)))
        binaries.require_fresh("pf3-algorithm",binary)
        path=self.directory/"algorithm.scene";path.write_text(self.command("dump")["text"])
        result=subprocess.run([str(binary),str(path),*[str(n) for r in rectangles for n in r]],capture_output=True,text=True,timeout=60)
        self.assertEqual(0,result.returncode,"PF3_ALGORITHM_EXECUTION: "+result.stderr)
        return json.loads(result.stdout)

    def test_PF23_original_algorithm_three_segments_and_same_input_equivalence(self):
        self.e1()
        self.assertEqual([[0,50,10,20,True],[50,100,10,5,False],[100,300,10,20,True]],
                         self.algorithm([(90,0,120,300)]),"PF23_ORIGINAL: pure algorithm input, not a legal D7 scene")
        self.assertEqual(self.widths(),self.algorithm([(0,0,1000,27),(0,273,1000,300),(90,27,120,273)]),
                         "P103_SAME_INPUT: native footprints and pure evaluator must agree")
        p=self.parameter("5");self.assertTrue(p["valid"],p)
        self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])
        self.assertEqual([[0,50,10,20,True],[50,100,10,5,True],[100,300,10,20,True]],
                         self.algorithm([(90,0,120,300)]),"PF23_ORIGINAL_X5: all green still three widths")

    def test_PF24_original_E2_E3_one_segment(self):
        for x in (125,120):
            self.e1(x)
            self.assertEqual([[0,300,10,20,True]],self.algorithm([(90,0,120,300)]),"PF24_ORIGINAL: one maximal segment")

    def test_PF05_exact_8_8_7_9_and_local_gap(self):
        self.e1(125)
        for rectangles,expected in [([(92,0,108,300)],[[0,300,8,8,True]]),
                                    ([(93,0,109,300)],[[0,300,7,9,False]]),
                                    ([(92,0,108,50),(92,100,108,300)],[[0,50,8,8,True],[50,100,0,0,False],[100,300,8,8,True]])]:
            self.assertEqual(expected,self.algorithm(rectangles),"PF05_WIDTHS: per-side continuous coverage")

    def test_PF05_insufficient_can_save_and_X9_recomputes(self):
        self.host();self.timbers()
        p=self.parameter("1000");self.assertTrue(p["valid"],p)
        self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])
        before=self.derived();self.assertTrue(all(not s["supported"] for s in before["support"]))
        scene=self.command("dump")["text"];self.load_text(scene)
        self.assertEqual(before,self.derived(),"PF05_SAVE: insufficient support is a result, never a validity gate")
        self.assertNotIn('"effectiveSeams"',scene)
        self.assertNotIn('"support"',scene)

    def test_PF06_positive_rational_comparison_and_rename_reorder(self):
        self.e1(125)
        for value,green in [("8",True),("8.1",False),("7.9",True),("9",False)]:
            p=self.parameter(value);self.assertTrue(p["valid"],p)
            self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])
            self.assertEqual([[0,300,8,8,green]],self.algorithm([(92,0,108,300)]),"PF06_RATIONAL: no rounded or hidden threshold")
        old=self.derived()
        p=self.parameter(fields=[dict(id=2,name="other",type="dimension",input="1"),dict(id=1,name="new name",type="dimension",input="9")])
        self.assertTrue(p["valid"],p)
        self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])
        self.assertEqual(old,self.derived(),"PF06_ID: names/order do not retarget threshold")

    def test_PF06_extreme_rational_does_not_overflow_comparison(self):
        self.e1(125)
        for value,green in [("9223372036854775807/1000000000000000000",False),
                            ("9223372036854775807/2000000000000000000",True)]:
            p=self.parameter(value);self.assertTrue(p["valid"],p)
            self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])
            self.assertEqual([[0,300,8,8,green]],self.algorithm([(92,0,108,300)]),"PF06_OVERFLOW: compare integers to exact fraction without d*den overflow")
            self.assertEqual([[0,300,20,20,True]],self.algorithm([(80,0,120,300)]),"PF06_OVERFLOW: 20*den exceeds uint64, exact comparison must still be green")

    def test_PF13_capacity_N_N1_is_complete_or_explicit_rejection(self):
        from tests import binaries
        binary=Path(os.environ.get("GEOMETRY_TEST_PF3_ALGORITHM",str(binaries.BY_NAME["pf3-algorithm"].path)))
        binaries.require_fresh("pf3-algorithm",binary)
        result=subprocess.run([str(binary),"--capacity"],capture_output=True,text=True,timeout=60)
        self.assertEqual(0,result.returncode,"PF13_CAPACITY: "+result.stderr)
        self.assertEqual([32768,32768,0],json.loads(result.stdout))

    def test_PF06_invalid_thresholds_reject_entire_world(self):
        self.e1();before=self.snapshot()
        for fields in ([],[dict(id=1,name="X",type="scalar",input="8")],
                       [dict(id=1,name="X",type="dimension",input="0")],
                       [dict(id=1,name="X",type="dimension",input="-1")],
                       [dict(id=1,name="X",type="dimension",input="1/0")]):
            p=self.parameter(fields=fields);self.assertFalse(p["valid"],p)
            self.assertEqual(before,self.snapshot(),"PF06_ATOMIC: invalid source cannot change World/revision")

    def test_R43_no_host_and_other_coplanar_host_do_not_support(self):
        self.host();self.timbers()
        self.apply([pfh.fill(id=2,origin=[-815,-100],gap=0)])
        d=self.read()["state"]["panelFills"][1]["derived"]
        self.assertEqual([[0,300,0,0,False]],self.widths(d),"PF3_HOST_ID: same plane and fill geometry are not identity")
        self.apply([dict(op="put-derived-placement",value=dict(id=11,fillId=2,h=30))])
        d=self.read()["state"]["panelFills"][1]["derived"]
        self.assertEqual([[0,300,0,0,False]],self.widths(d),"PF3_HOST_FILTER: a different derived host must remain empty")

    def test_R43_ordinary_coplanar_placement_is_excluded(self):
        self.seed(width=915,length=1830,outline="0,0 1000,0 1000,300 0,300")
        self.apply([pfh.fill(origin=[-815,-100],gap=0)])
        for line in ["placement 10 on boundary 8 origin 0 0 9 u +x v +y", "timber 1 27 30 role boundary",
                     "timber 2 27 30 role boundary","place 1 on 10 at-face e0 +u +n","place 2 on 10 at-face e2 +u +n",
                     "spec center 105","guide 1 10 v spec:center","timber 3 30 30 role primary",
                     "place 3 on 10 at-line guide 1 between t1 t2 +v +n"]:
            self.assertTrue(self.command("line "+line)["ok"],line)
        self.assertEqual([[0,300,0,0,False]],self.widths(),"PF3_ORDINARY_HOST: geometrically identical ordinary placement is not the source derived host")

    def test_R43_unplaced_timbers_on_zero_id_host_do_not_count(self):
        self.host()
        self.apply([dict(op="delete-derived-placement",id=10),dict(op="put-derived-placement",value=dict(id=0,fillId=1,h=30))])
        self.assertTrue(self.command("line timber 99 200 30 role primary")["ok"],"PF3_UNPLACED: an unplaced declaration must not require a footprint")
        self.assertEqual([[0,300,0,0,False]],self.widths(),"PF3_UNPLACED: declarations without D7 placement have no footprint")

    def test_R43_negative_structure_side_and_vertical_frame_real_footprints(self):
        expected=[[0,27,100,900,True],[27,273,10,20,True],[273,300,100,900,True]]
        for side,vertical in [(-1,False),(1,True)]:
            self.seed(width=915,length=1830,outline="0,0 1000,0 1000,300 0,300")
            self.apply([pfh.pf2.put(pfh.pf2.surface(boundary=8,origin=(1000,0,0) if vertical else (0,0,0),side=side,
                       u="+Y" if vertical else "+X",v="+Z" if vertical else "+Y",n="+X" if vertical else "+Z",obstacles=[])),
                       pfh.fill(origin=[-815,-100],gap=0),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
            if side==1:self.timbers()
            else:
                key=pfh.PanelFillHost.key
                for line in ["timber 1 27 30 role boundary","timber 2 27 30 role boundary",
                             "place 1 on 10 at-face "+key([["e2",0,1]])+" +u +n",
                             "place 2 on 10 at-face "+key([["e0",0,1]])+" +u +n",
                             "spec center 105","guide 1 10 v spec:center","timber 3 30 30 role primary",
                             "place 3 on 10 at-line guide 1 between t1 t2 +v +n"]:
                    self.assertTrue(self.command("line "+line)["ok"],line)
            self.assertEqual(expected,self.widths(),"R43_FRAME: map (u,v_d) back to (u,s*v_d), never use world XY")

    def test_R43_v_axis_and_positive_gap_measure_from_each_board_edge(self):
        self.seed(width=100,length=400,outline="0,0 300,0 300,250 0,250")
        self.apply([pfh.fill(lengthAlong="u",origin=[-50,0],gap=3),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
        key=pfh.PanelFillHost.key
        for line in ["timber 1 27 30 role boundary","timber 2 27 30 role boundary",
                     "place 1 on 10 at-face "+key([["e1",0,1]])+" +v +n",
                     "place 2 on 10 at-face "+key([["e3",0,1]])+" +v +n",
                     "spec center 101","guide 1 10 u spec:center","timber 3 27 30 role primary",
                     "place 3 on 10 at-line guide 1 between t1 t2 +u +n"]:
            self.assertTrue(self.command("line "+line)["ok"],line)
        self.assertEqual([[0,27,100,100,True],[27,273,12,12,True],[273,300,100,100,True]],
                         self.widths(axis="v",coordinate=101),"R43_GAP_EDGES: 27mm footprint and gap3 give 12/12")

    def test_D43_holes_notches_and_obstacles_remove_only_one_sided_seams(self):
        for outline,extra,obstacles in [
            ("0,0 200,0 200,300 0,300 hole 100,50 150,50 150,100 100,100","",[]),
            ("0,0 200,0 200,50 100,50 100,100 200,100 200,300 0,300","",[]),
            ("0,0 200,0 200,300 0,300","column 1 at 100 50 size 50 50 z -2400 9\n",["c1"])]:
            self.seed(width=100,length=400,outline=outline,extra=extra,obstacles=obstacles)
            self.apply([pfh.fill(gap=0)])
            self.assertEqual([[0,50,0,0,False],[100,300,0,0,False]],self.widths(),"D43_TWO_SIDES: never infer from bbox")
            self.assertTrue(any(s["range"]==[50,100] for s in self.derived()["nonSeams"]),"D43_ONE_SIDE: explicitly report outer-edge-not-two-panels")

    def test_D43_positive_odd_gap_uses_board_edges_and_both_axes(self):
        self.seed(outline="0,0 250,0 250,250 0,250")
        self.apply([pfh.fill()]);d=self.derived()
        self.assertEqual([[0,100],[103,203],[206,250]], [s["range"] for s in d["effectiveSeams"] if s["axis"]=="u" and s["k"]==0],"D43_ODD_GAP: both board edges must exist")
        self.assertEqual([[0,100],[103,203],[206,250]], [s["range"] for s in d["effectiveSeams"] if s["axis"]=="v" and s["k"]==0],"D43_ODD_GAP: v-axis board edges")
        self.assertEqual([100,103], next(s for s in d["effectiveSeams"] if s["axis"]=="u")["edges"],"D43_ODD_GAP: floor belongs to finish frame")

    def test_D43_stagger_band_identity_signed_and_T_point(self):
        self.seed(outline="-150,-150 250,-150 250,250 -150,250")
        self.apply([pfh.fill(gap=0,pattern="stagger",stagger=dict(axis="u",value=20))]);d=self.derived()
        seams=d["effectiveSeams"]
        self.assertTrue(any(s.get("band")==-1 and s["coordinate"]==20 and s["range"]==[-100,0] for s in seams),"D43_NEGATIVE_BAND")
        self.assertTrue(all("band" in s for s in seams if s["axis"]=="u"),"D43_BAND_ID")
        self.assertTrue(all("band" not in s for s in seams if s["axis"]=="v"))
        for s in seams:
            if s["axis"]=="u":
                self.assertTrue(s["band"]*100<=s["range"][0]<s["range"][1]<=(s["band"]+1)*100,
                                "D43_NEGATIVE_BAND: no extra material outside each stable band identity")
        self.assertEqual([[-150,250]],[s["range"] for s in seams if s["axis"]=="v" and s["coordinate"]==100],"D43_T_POINT: zero-width intersection does not cut seam")

    def test_R43_union_continuity_and_ignore_isolated_cut_values(self):
        self.e1(125)
        self.assertEqual([[0,300,10,20,True]],self.algorithm([(90,0,105,300),(105,0,120,300)]),"R43_UNION: touching footprints form continuous coverage")
        self.assertEqual([[0,300,0,0,False]],self.algorithm([(80,0,90,300),(110,0,120,300)]),"R43_GAP: cannot jump to disconnected coverage")
        self.e1(110)
        self.assertEqual([[0,50,10,100,True],[50,300,10,10,True]],self.algorithm([(90,0,200,100),(90,100,110,300)]),"R43_OPEN_POINTS: exceptional cut point cannot block equal-value merging")

    def test_PF07_cancel_undo_redo_and_cold_reopen_support(self):
        self.e1();before=self.derived();scene=self.command("dump")["text"]
        p=self.preview([pfh.fill(origin=[-810,-100],gap=0)])
        self.assertTrue(p["valid"],p);self.assertNotEqual(before,p["after"]["panelFills"][0]["derived"])
        self.command("panel-fill-cancel "+str(p["token"]));self.assertEqual(before,self.derived())
        self.apply([pfh.fill(origin=[-810,-100],gap=0)])
        self.assertTrue(self.command("line undo")["ok"]);self.assertEqual(before,self.derived())
        self.assertTrue(self.command("line redo")["ok"]);self.assertNotEqual(before,self.derived())
        self.command("reset");self.load_text(scene,"cold.scene");self.assertEqual(before,self.derived())


if __name__ == "__main__":
    unittest.main()
