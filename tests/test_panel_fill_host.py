"""P-098/P-116: native D4 host identity and D7 lifecycle, never ordinary placement."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_panel_fill_layout as pf2
fill = pf2.fill


class PanelFillHost(unittest.TestCase):
    setUpClass = pf2.PanelFillLayout.__dict__["setUpClass"]
    setUp = pf2.PanelFillLayout.setUp
    command = pf2.PanelFillLayout.command
    load_text = pf2.PanelFillLayout.load_text
    read = pf2.PanelFillLayout.read
    snapshot = pf2.PanelFillLayout.snapshot
    preview = pf2.PanelFillLayout.preview
    apply = pf2.PanelFillLayout.apply
    seed = pf2.PanelFillLayout.seed
    reject = pf2.PanelFillLayout.reject

    @staticmethod
    def key(value):
        return "key-hex:"+json.dumps(value,separators=(",",":")).encode().hex()

    def current_host(self):
        return self.read()["state"]["derivedPlacements"][0]

    def test_R41_touch_only_and_shared_obstacle_edges(self):
        for bounds in [(100,120,20,80),(100,120,100,120)]:
            x0,x1,y0,y1=bounds
            host=self.region(extra=f"beam 20 along x from {x0} to {x1} at {(y0+y1)//2} width {y1-y0} depth 39 top 39\n",obstacles=["b20"])
            self.assertEqual([[0,0],[100,0],[100,100],[0,100]],host["derived"]["components"][0]["outline"])
        host=self.region(extra="beam 20 along x from 20 to 40 at 30 width 20 depth 30 top 39\nbeam 21 along x from 40 to 60 at 30 width 20 depth 30 top 39\n",obstacles=["b20","b21"])
        self.assertEqual([[[20,20],[20,40],[60,40],[60,20]]],host["derived"]["components"][0]["holes"])

    def test_R41_hole_touching_concave_vertex_rejects(self):
        self.seed(outline="0,0 100,0 100,100 50,100 50,50 0,50",extra="beam 20 along x from 50 to 70 at 40 width 20 depth 30 top 39\n",obstacles=["b20"])
        self.apply([fill(gap=0)])
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))],"R41")

    def test_R41_vertical_frame_uses_normal_depth(self):
        self.seed(outline="0,0 100,0 100,100 0,100",extra="beam 20 along x from 1010 to 1020 at 50 width 20 depth 20 top 60\n",obstacles=[])
        self.apply([pf2.put(pf2.surface(boundary=8,origin=(1000,0,0),u="+Y",v="+Z",n="+X",obstacles=["b20"]))])
        self.apply([fill(gap=0),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
        host=self.current_host()
        self.assertEqual([1009,0,0],host["derived"]["frame"]["origin"])
        self.assertEqual(1,len(host["derived"]["components"][0]["holes"]),"PFH_VERTICAL_DEPTH: use n, not world z")
        self.assertTrue(self.command("line beam 20 along x from 1040 to 1050 at 50 width 20 depth 20 top 60")["ok"])
        self.assertEqual([],self.current_host()["derived"]["components"][0]["holes"])

    def test_R41_fixity_preserves_source_breaks_and_merged_keys(self):
        for fixity,expected in [("X F F F F",2),("F F F F F",1)]:
            host=self.region(outline="0,0 40,0 100,0 100,100 0,100 fixity "+fixity)
            edges=[e for e in host["derived"]["components"][0]["edges"] if e["start"][1]==e["end"][1]==0]
            self.assertEqual(expected,len(edges),"PFH_FIXITY: maximal edges merge only equal fixity")
            if expected==1:self.assertEqual([["e0",0,1],["e1",0,1]],edges[0]["key"])
            else:self.assertEqual(["FREE","FIXED"],[e["fixity"] for e in edges])

    def test_R41_total_source_segments_are_identity_and_stale_key_rejects(self):
        self.region(extra="beam 20 along x from 30 to 40 at 30 width 60 depth 30 top 39\nbeam 21 along x from 70 to 80 at 30 width 60 depth 30 top 39\n",obstacles=["b20"])
        key=self.key([["e0",0,2]])
        self.assertTrue(self.command("line timber 1 10 30 role boundary")["ok"])
        self.assertTrue(self.command("line place 1 on 10 at-face "+key+" +u +n")["ok"])
        self.reject([pf2.put(pf2.surface(boundary=8,origin=(0,0,0),obstacles=["b20","b21"]))],"R41")
        result=self.command("line delete timber 1")
        self.assertFalse(result["ok"]);self.assertTrue(result["preview"]["valid"],result)
        self.assertTrue(self.command("line confirm "+str(result["preview"]["token"]))["ok"])
        self.apply([pf2.put(pf2.surface(boundary=8,origin=(0,0,0),obstacles=["b20","b21"]))])
        keys=[e["key"] for e in self.current_host()["derived"]["components"][0]["edges"]]
        self.assertIn([["e0",0,3]],keys)
        self.assertNotIn([["e0",0,2]],keys)

    def test_R41_overlapping_sources_retain_full_order(self):
        host=self.region(extra="beam 21 along x from 20 to 40 at 30 width 20 depth 30 top 39\nbeam 20 along x from 20 to 40 at 30 width 20 depth 30 top 39\n",obstacles=["b21","b20"])
        keys=[e["key"] for e in host["derived"]["components"][0]["edges"]]
        self.assertIn([["b20:u-",0,1],["b21:u-",0,1]],keys)

    def test_D6a_derived_edge_keys_and_between_are_persistent(self):
        self.region()
        left=self.key([["e3",0,1]]);right=self.key([["e1",0,1]])
        for line in ["guide 1 10 v edge-key:"+left.split(":")[1]+":u",
                     "spec mid 5","guide 2 10 u spec:mid","timber 1 10 30 role boundary",
                     "place 1 on 10 at-line guide 2 between "+left+" "+right+" +u +n"]:
            self.assertTrue(self.command("line "+line)["ok"],"PFH_KEY_REFERENCE: "+line)
        before=self.snapshot()
        self.assertFalse(self.command("line guide 3 10 v vertex:v0:u")["ok"])
        self.assertEqual(before,self.snapshot())
        text=self.command("dump")["text"];self.load_text(text,"key.scene")
        self.assertEqual(text,self.command("dump")["text"])
        supports=self.command("references")["timberSupports"]["entries"][0]
        self.assertEqual([["e3",0,1]],supports["start"]["relation"]["edgeKey"])

    def test_I53_atomic_height_and_B_source_update(self):
        self.host();self.timbers()
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=31))],"V_DERIVED_TIMBER")
        operations=[dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=31))]
        operations += [dict(op="set-source",target=dict(kind="timber",id=i,field="B"),source=dict(kind="literal",value=31)) for i in (1,2,3)]
        preview=self.apply(operations)
        self.assertIn("dependencies",preview,"PFH_ATOMIC_PREVIEW: changed B sources must be disclosed")
        self.assertEqual(31,self.current_host()["derived"]["h"])
        self.assertEqual([31]*3,[t["geometry"]["B"] for t in self.command("references")["timbers"]])
        text=self.command("dump")["text"];self.load_text(text,"height.scene")
        self.assertEqual(text,self.command("dump")["text"])

    def test_D4_typed_h_sources_and_immutable_fill(self):
        self.region()
        self.assertTrue(self.command("line spec depth 30")["ok"])
        self.apply([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=dict(kind="spec",name="depth")))])
        self.assertTrue(self.command("line spec depth 31")["ok"])
        self.assertEqual(31,self.current_host()["derived"]["h"])
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=2,h=31))],"immutable")
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=dict(kind="application",id="a",field="primary.B")))],"application")

    def test_I55_delete_and_corrupt_reopen_preserve_world(self):
        self.host();self.timbers()
        self.reject([dict(op="delete-panel-fill",id=1)],"source fill")
        self.reject([dict(op="delete-derived-placement",id=10)],"placement")
        text=self.command("dump")["text"]
        for changed in [text.replace("requires panel-fill/1\n",""),text.replace("requires parameters/1\n",""),
                        "\n".join(line for line in text.splitlines() if not line.startswith("panel-fill "))]:
            before=self.snapshot();path=self.directory/"invalid.scene";path.write_text(changed)
            self.assertFalse(self.command("loadfile "+str(path))["ok"],"PFH_REOPEN_CLOSURE: missing source/capability rejects")
            self.assertEqual(before,self.snapshot())

    def test_D10_grid_save_order_and_reopen(self):
        self.region()
        self.assertTrue(self.command("line grid 1 on 10 u series 0 10 11")["ok"])
        text=self.command("dump")["text"]
        self.assertLess(text.index("derived-placement 10 "),text.index("grid 1 on 10 "))
        self.load_text(text,"grid.scene")
        self.assertEqual(text,self.command("dump")["text"])

    def test_P116_E1_E2_E3_real_host_feeds_separate_R43_oracle(self):
        from tests.pfh_oracle import footprint,support
        five=[[0,27,100,900],[27,50,10,20],[50,100,10,5],[100,273,10,20],[273,300,100,900]]
        three=[[0,27,100,900],[27,273,10,20],[273,300,100,900]]
        for x,expected in [(105,five),(125,three),(120,three)]:
            with self.subTest(obstacle=x):
                self.seed(width=915,length=1830,outline="0,0 1000,0 1000,300 0,300",
                          extra=f"column 1 at {x} 50 size {200-x} 50 z -2400 9\n",obstacles=["c1"])
                self.apply([fill(origin=[-815,-100],gap=0),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
                self.timbers()
                native=self.read()["state"]
                self.assertEqual(10,native["panelFills"][0]["derived"]["derivedPlacement"])
                rectangles=[footprint(t["geometry"]) for t in self.command("references")["timbers"]]
                self.assertEqual([(0,0,1000,27),(0,273,1000,300),(90,27,120,273)],rectangles,"PFH_TRUE_D7_WITNESS: actual legal footprints")
                layout=native["panelFills"][0]["derived"]
                self.assertEqual(expected,support(layout,rectangles),"PFH_NATIVE_ORACLE: E1 five, E2/E3 three")
                # P-103 retains the independent original one-footprint algorithm input.
                old=support(layout,[(90,0,120,300)])
                self.assertEqual([[0,50,10,20],[50,100,10,5],[100,300,10,20]] if x==105 else [[0,300,10,20]],old)
                self.assertIsNone(layout["support"],"PF-H does not claim PF-3 runtime support output")
                text=self.command("dump")["text"];self.load_text(text,"legal.scene")
                self.assertEqual(native,self.read()["state"])
                self.assertEqual(text,self.command("dump")["text"])

    def test_I53_negative_depth_and_empty_rebuild_reject_atomically(self):
        self.region(extra="beam 20 along x from -10 to 110 at 50 width 120 depth 30 top 39\n",obstacles=[])
        self.assertTrue(self.command("line timber 1 10 30 role boundary")["ok"])
        before=self.snapshot()
        reply=self.command("line place 1 on 10 at-face "+self.key([["e0",0,1]])+" +u -n")
        self.assertFalse(reply["ok"]);self.assertIn("V_DERIVED_TIMBER",reply["error"]);self.assertEqual(before,self.snapshot())
        self.assertTrue(self.command("line place 1 on 10 at-face "+self.key([["e0",0,1]])+" +u +n")["ok"])
        self.reject([pf2.put(pf2.surface(boundary=8,origin=(0,0,0),obstacles=["b20"]))],"R41")

    def test_D4_shared_id_normal_variant_cannot_be_replaced_or_aliased(self):
        self.host()
        self.apply([dict(op="delete-derived-placement",id=10)])
        self.assertTrue(self.command("line placement 10 origin 0 0 9 u +x v +y rect 0 0 1000 300")["ok"])
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))],"variant")
        self.host()
        for line in ["surface 10 origin 0 0 9 u +x v +y rect 0 0 1000 300",
                     "surface 10 origin 0 0 9 u +x v +y outline 0,0 1000,0 1000,300 0,300"]:
            before=self.snapshot();self.assertFalse(self.command("line "+line)["ok"]);self.assertEqual(before,self.snapshot())

    def region(self, outline="0,0 100,0 100,100 0,100", extra="", obstacles=None, side=1):
        self.seed(width=915, length=1830, outline=outline, extra=extra, obstacles=obstacles or [])
        if side != 1:
            self.apply([pf2.put(pf2.surface(boundary=8, origin=(0,0,0), side=side, obstacles=obstacles or []))])
        self.apply([fill(gap=0)])
        self.apply([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
        return self.read()["state"]["derivedPlacements"][0]

    def test_R41_multiple_components_share_one_host_and_preserve_gap(self):
        host = self.region(extra="beam 20 along x from 40 to 60 at 50 width 120 depth 30 top 39\n", obstacles=["b20"])
        self.assertEqual([[[0,0],[40,0],[40,100],[0,100]], [[60,0],[100,0],[100,100],[60,100]]],
                         [c["outline"] for c in host["derived"]["components"]], "PFH_MULTICOMPONENT: never fill the excluded strip")
        self.assertEqual(1, len(self.read()["state"]["derivedPlacements"]))
        self.assertTrue(self.command("line spec center 50")["ok"])
        self.assertTrue(self.command("line guide 1 10 u spec:center")["ok"])
        self.assertTrue(self.command("line timber 1 10 30 role boundary")["ok"])
        before = self.snapshot()
        result = self.command("line place 1 on 10 at-line guide 1 +u +n")
        self.assertFalse(result["ok"], "PFH_MULTICOMPONENT: ambiguous spans require selection; bbox is not a host")
        self.assertEqual(before, self.snapshot())

    def test_R41_layers_use_open_depth_intervals(self):
        for bottom, top, holes in [(0,9,0),(9,39,1),(39,49,0),(8,10,1)]:
            with self.subTest(depth=(bottom,top)):
                host = self.region(extra=f"beam 20 along x from 20 to 40 at 30 width 20 depth {top-bottom} top {top}\n", obstacles=["b20"])
                self.assertEqual(holes, len(host["derived"]["components"][0]["holes"]), "PFH_LAYER_OPEN: panel and timber layers differ at equal endpoints")

    def test_R41_point_connected_material_is_two_components(self):
        host = self.region(extra="beam 20 along x from 0 to 50 at 75 width 50 depth 30 top 39\nbeam 21 along x from 50 to 100 at 25 width 50 depth 30 top 39\n", obstacles=["b20","b21"])
        self.assertEqual(2,len(host["derived"]["components"]),"PFH_POINT_COMPONENTS: point contact is not interior connectivity")

    def test_R41_touching_holes_reject_without_changing_world(self):
        self.seed(width=915,length=1830,outline="0,0 100,0 100,100 0,100",
                  extra="beam 20 along x from 20 to 40 at 30 width 20 depth 30 top 39\nbeam 21 along x from 40 to 60 at 50 width 20 depth 30 top 39\n",obstacles=["b20","b21"])
        self.apply([fill(gap=0)])
        self.reject([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))],"R41")

    def test_R41_empty_host_remains_empty(self):
        host = self.region(extra="beam 20 along x from -10 to 110 at 50 width 120 depth 30 top 39\n",obstacles=["b20"])
        self.assertEqual([],host["derived"]["components"],"PFH_EMPTY: no fallback rectangle")
        self.assertTrue(self.command("line timber 1 27 30 role boundary")["ok"])
        before=self.snapshot()
        key=json.dumps([["e0",0,1]],separators=(",",":")).encode().hex()
        self.assertFalse(self.command("line place 1 on 10 at-face key-hex:"+key+" +u +n")["ok"])
        self.assertEqual(before,self.snapshot())

    def test_D4_identity_and_index_alias_rejection(self):
        self.host()
        self.reject([dict(op="put-derived-placement",value=dict(id=11,fillId=1,h=30))],"D4")
        before=self.snapshot()
        result=self.command("line placement 10 origin 0 0 9 u +x v +y rect 0 0 1000 300")
        self.assertFalse(result["ok"],"PFH_VARIANT: cannot replace a derived definition with a normal placement")
        self.assertEqual(before,self.snapshot())
        self.assertTrue(self.command("line timber 1 27 30 role boundary")["ok"])
        before=self.snapshot()
        self.assertFalse(self.command("line place 1 on 10 at-face e0 +u +n")["ok"],"PFH_KEY: no derived e-index aliases")
        self.assertEqual(before,self.snapshot())

    def host(self, side=1):
        self.seed(width=915, length=1830, outline="0,0 1000,0 1000,300 0,300")
        self.apply([fill(origin=[-815,-100], gap=0)])
        if side == -1:
            value = self.read()["state"]["finishSurfaces"][0]
            self.apply([dict(op="put-finish-surface",value=dict(id=1,name=value["name"],boundaryId=8,frame=value["frame"],structureSide=-1,obstacles=[]))])
        self.apply([dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
        hosts = self.read()["state"].get("derivedPlacements",[])
        self.assertEqual(1,len(hosts),"PFH_HOST_MISSING: real D4 derived host must be published")
        self.assertEqual(dict(id=10,fillId=1,h=30),hosts[0]["definition"])
        return hosts[0]

    def timbers(self):
        # R41 keys are source/segment/total triples, not derived e-index aliases.
        lower = json.dumps([["e0",0,1]],separators=(",",":")).encode().hex()
        upper = json.dumps([["e2",0,1]],separators=(",",":")).encode().hex()
        for line in ["timber 1 27 30 role boundary", "timber 2 27 30 role boundary",
                     "place 1 on 10 at-face key-hex:"+lower+" +u +n",
                     "place 2 on 10 at-face key-hex:"+upper+" +u +n",
                     "spec center 105", "guide 1 10 v spec:center", "timber 3 30 30 role primary",
                     "place 3 on 10 at-line guide 1 between t1 t2 +v +n"]:
            self.assertTrue(self.command("line "+line)["ok"],"PFH_E1_LEGAL: "+line)

    def test_E1_legal_native_host_and_saved_identity(self):
        self.host(); self.timbers()
        text=self.command("dump")["text"]
        self.assertIn("derived-placement 10 definition-hex ",text,"PFH_SAVE: source identity must survive")
        self.assertNotIn("placement 10 origin",text,"PFH_SAVE: no ordinary placement snapshot")
        before=self.read()["state"]
        self.load_text(text,"roundtrip.scene")
        self.assertEqual(before,self.read()["state"],"PFH_REOPEN: recompute identical host")
        self.assertEqual(text,self.command("dump")["text"])

    def test_host_maps_structure_side_and_board_back(self):
        host=self.host(-1)
        self.assertEqual([0,0,-9],host["derived"]["frame"]["origin"])
        self.assertEqual("-Y",host["derived"]["frame"]["V"])
        self.assertEqual("-Z",host["derived"]["frame"]["N"])
        self.assertEqual([[0,-300],[1000,-300],[1000,0],[0,0]],host["derived"]["components"][0]["outline"])

    def test_host_creation_undo_redo(self):
        self.host(); text=self.command("dump")["text"]
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual([],self.read()["state"]["derivedPlacements"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(text,self.command("dump")["text"])

    def test_derived_timber_depth_cannot_violate_I53(self):
        self.host()
        self.assertTrue(self.command("line timber 1 27 27 role boundary")["ok"])
        before=self.snapshot()
        lower=json.dumps([["e0",0,1]],separators=(",",":")).encode().hex()
        result=self.command("line place 1 on 10 at-face key-hex:"+lower+" +u +n")
        self.assertFalse(result["ok"],"PFH_I53: B27 cannot enter h30 host")
        self.assertIn("V_DERIVED_TIMBER",result["error"])
        self.assertEqual(before,self.snapshot())


if __name__ == "__main__":
    unittest.main()
