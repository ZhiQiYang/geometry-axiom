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
        self.assertTrue(self.command("undo")["ok"])
        self.assertEqual([],self.read()["state"]["derivedPlacements"])
        self.assertTrue(self.command("redo")["ok"])
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
