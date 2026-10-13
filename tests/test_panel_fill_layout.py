"""PF-2 native oracles: D42/R42 tiles and ordered clipped loops, not PF-3 support or a UI receipt."""
import copy
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_panel_fill_finish_surface as pf1
surface, put = pf1.surface, pf1.put


def fill(**changes):
    value = dict(id=1, finishSurfaceId=1, panel=dict(id="pf-board", version=1),
                 lengthAlong="v", origin=[0, 0], gap=3, pattern="straight",
                 threshold=dict(parameterId=90, fieldId=1))
    value.update(changes)
    return {"op": "put-panel-fill", "value": value}


def area(loop):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(loop, loop[1:]+loop[:1])) // 2


class PanelFillLayout(unittest.TestCase):
    setUpClass = classmethod(pf1.FinishSurfaceNative.setUpClass.__func__)
    setUp = pf1.FinishSurfaceNative.setUp
    command = pf1.FinishSurfaceNative.command
    load_text = pf1.FinishSurfaceNative.load_text
    read = pf1.FinishSurfaceNative.read
    snapshot = pf1.FinishSurfaceNative.snapshot
    preview = pf1.FinishSurfaceNative.preview
    apply = pf1.FinishSurfaceNative.apply
    reject = pf1.FinishSurfaceNative.reject

    def seed(self, width=100, length=100, thickness="9", outline="0,0 250,0 250,250 0,250", extra="", obstacles=None):
        self.load_text("boundary 8 outline " + outline + " kind room_plan\n" + extra)
        request = self.directory / "engineering.json"
        request.write_text(json.dumps(dict(schema="engineering-transaction/1", expectedRevision=self.read()["revision"], operations=[
            dict(op="publish-material", value=dict(id="pf-board", version=1, name="板", kind="panel", width=width, length=length, thickness=thickness)),
            dict(op="put-parameter", value=dict(id=90, name="門檻", fields=[dict(id=1, name="X", type="dimension", input="8")]))])))
        result = self.command("engineering-preview " + str(request))
        self.assertTrue(result["ok"] and result["preview"]["valid"], result)
        self.assertTrue(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
        self.apply([put(surface(boundary=8, origin=(0, 0, 0), obstacles=obstacles or []))])

    def layout(self, value=None):
        self.apply([value or fill()])
        return self.read()["state"]["panelFills"][0]["derived"]

    def test_PF02_centers_are_integer_and_share_panel_lattice(self):
        self.seed()
        d = self.layout()
        self.assertEqual([101, 204], [s["coordinate"] for s in d["seamLines"] if s["axis"] == "u"], "PF02: g=3 must floor in finish frame")
        self.assertEqual(9, d["tileCount"])
        self.assertEqual(4, d["wholeCount"])
        self.assertEqual(5, d["cutCount"])

    def test_PF03_negative_indices_and_alternating_rows(self):
        self.seed(outline="-150,-150 250,-150 250,250 -150,250")
        d = self.layout(fill(pattern="stagger", stagger=dict(axis="u", value=20)))
        starts = {(t["i"], t["j"]): t["body"][0] for t in d["tiles"]}
        self.assertEqual(0, starts[0, 0]); self.assertEqual(20, starts[0, 1])
        self.assertEqual(0, starts[0, 2]); self.assertEqual(20, starts[0, -1])
        self.assertEqual(-103, starts[-1, 0])

    def test_PF03_coverage_matches_independent_integer_cell_oracle(self):
        self.seed(outline="0,0 250,0 250,120 120,120 120,250 0,250")
        d = self.layout(fill(origin=[200, -100], pattern="stagger", stagger=dict(axis="v", value=-17)))
        tiles = d["tiles"]
        for u in range(250):
            for v in range(250):
                in_f = u < 120 or v < 120
                i = (u-200)//103
                phase = -17 if i & 1 else 0
                board = (u-200)%103 < 100 and (v+100-phase)%103 < 100
                hits = sum(any(self.inside(f["outer"], u+.5, v+.5) and not any(self.inside(h,u+.5,v+.5) for h in f["holes"]) for f in t["fragments"]) for t in tiles)
                self.assertEqual(int(in_f and board), hits, "PF03: uncovered or overlapping board cell at %s" % ((u,v),))

    @staticmethod
    def inside(loop, x, y):
        return sum(a[0] == b[0] and min(a[1],b[1]) < y < max(a[1],b[1]) and a[0] > x for a,b in zip(loop,loop[1:]+loop[:1])) % 2 == 1

    def test_PF04_hole_loops_and_disconnected_fragments(self):
        self.seed(width=300, length=300, outline="0,0 250,0 250,250 0,250 hole 50,50 100,50 100,100 50,100")
        d = self.layout(fill(gap=0))
        f = d["tiles"][0]["fragments"][0]
        self.assertEqual([[0,0],[250,0],[250,250],[0,250]], f["outer"])
        self.assertEqual([[[50,50],[50,100],[100,100],[100,50]]], f["holes"])
        self.assertEqual(60000, area(f["outer"]) + sum(map(area,f["holes"])))
        self.seed(width=300, length=300, extra="column 9 at 100 0 size 20 250 z -10 20\n", obstacles=["c9"])
        fs = self.layout(fill(gap=0))["tiles"][0]["fragments"]
        self.assertEqual(2, len(fs), "PF04: an obstacle cutting the whole tile must produce two distinct fragments")
        self.assertEqual([[0,0],[120,0]], [f["outer"][0] for f in fs])

    def test_PF04_point_contact_does_not_merge_material(self):
        self.seed(width=300, length=300, extra="column 9 at 0 100 size 100 150 z -10 20\ncolumn 10 at 100 0 size 150 100 z -10 20\n", obstacles=["c9","c10"])
        fs = self.layout(fill(gap=0))["tiles"][0]["fragments"]
        self.assertEqual(2, len(fs), "R42: point contact is not material interior connectivity")
        for f in fs: self.assertEqual(len(f["outer"]),len(set(map(tuple,f["outer"]))), "R42: each output loop must be simple")

    def test_PF04_touching_holes_have_deterministic_simple_loops(self):
        self.seed(width=300,length=300,outline="0,0 250,0 250,250 0,250",extra="column 9 at 50 50 size 50 50 z -10 20\ncolumn 10 at 100 100 size 50 50 z -10 20\n",obstacles=["c9","c10"])
        fs=self.layout(fill(gap=0))["tiles"][0]["fragments"]
        self.assertEqual(1,len(fs)); self.assertEqual(2,len(fs[0]["holes"]), "R42: a repeated vertex must split into simple hole loops")
        self.assertEqual([[50,50],[100,100]],[h[0] for h in fs[0]["holes"]])
        for loop in [fs[0]["outer"]]+fs[0]["holes"]: self.assertEqual(len(loop),len(set(map(tuple,loop))))

    def test_PF13_extreme_world_vertex_is_honest_capacity_failure(self):
        self.seed()
        self.apply([put(surface(boundary=8,origin=(100000000,0,0),obstacles=[]))])
        self.reject([fill()],"CAPACITY")

    def test_PF08_PF09_panel_layer_uses_open_intervals(self):
        for z, expected in [(2600, True),(2400,False),(2480,False),(2491,False),(2500,True)]:
            with self.subTest(z=z):
                self.seed(extra="beam 2 along x from 0 to 250 at 100 width 40 depth 300 top 2800\n", obstacles=["b2"])
                self.apply([put(surface(boundary=8, origin=(0,0,z),obstacles=["b2"]))])
                d = self.layout()
                self.assertEqual(expected, d["obstacles"][0]["panelLayer"], "I53: positive volume, not closed contact")

    def test_PF09_vertical_and_negative_structure_side(self):
        self.seed(extra="column 9 at 0 20 size 9 40 z 0 250\n", obstacles=["c9"])
        self.apply([put(surface(boundary=8,origin=(0,0,0),obstacles=["c9"],u="+Y",v="+Z",n="+X"))])
        self.assertTrue(self.layout()["obstacles"][0]["panelLayer"], "R41 vertical layer must use n, not z")
        self.apply([put(surface(boundary=8,origin=(0,0,0),side=-1,obstacles=["c9"],u="+Y",v="+Z",n="+X"))])
        self.assertFalse(self.read()["state"]["panelFills"][0]["derived"]["obstacles"][0]["panelLayer"])

    def test_PF07_cancel_stale_and_undo_redo_are_atomic(self):
        self.seed(); self.layout()
        before = self.snapshot(); p = self.preview([fill(origin=[5,7])])
        self.assertEqual(before,self.snapshot()); self.command("panel-fill-cancel %d" % p["token"])
        self.assertEqual(before,self.snapshot()); self.apply([fill(origin=[5,7])])
        after=self.command("dump")["text"]; self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before[0],self.command("dump")["text"]); self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after,self.command("dump")["text"])
        self.assertFalse(self.command("panel-fill-confirm %d" % p["token"])["ok"])

    def test_PF11_native_dump_reopen_definitions_only(self):
        self.seed(); expected = self.layout(fill(pattern="stagger", stagger=dict(axis="u", value=20)))
        text = self.command("dump")["text"]
        self.assertNotIn('"fragments"',text); self.assertNotIn('"seamLines"',text)
        self.command("reset"); self.load_text(text, "reopen.scene")
        self.assertEqual(expected,self.read()["state"]["panelFills"][0]["derived"])
        self.assertEqual(text,self.command("dump")["text"])

    def test_PF13_thickness_required_even_without_obstacles(self):
        for t in [None,"0","9.5"]:
            if t == "0": continue  # D26 already rejects zero; no material is published.
            self.seed(thickness=t)
            self.reject([fill()],"I52")
        self.seed(thickness="9.000"); self.layout()

    def test_PF13_capacity_never_returns_partial_tiles(self):
        self.seed(width=1,length=1,outline="0,0 1000,0 1000,1000 0,1000")
        p=self.reject([fill(gap=0)],"CAPACITY")
        self.assertEqual("UNSUPPORTED",p["violations"][0]["status"])

    def test_I55_threshold_and_material_are_real_dependencies(self):
        self.seed(); self.layout()
        self.reject([dict(op="delete-finish-surface",id=1)],"I55")
        self.reject([fill(threshold=dict(parameterId=90,fieldId=99))],"I38")
        self.reject([fill(panel=dict(id="missing",version=1))],"I52")
        self.reject([fill(pattern="stagger",stagger=dict(axis="u",value=103))],"I52")


if __name__ == "__main__": unittest.main()
