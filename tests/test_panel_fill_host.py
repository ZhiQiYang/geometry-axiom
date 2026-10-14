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
