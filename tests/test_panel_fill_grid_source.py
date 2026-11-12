"""C0: D10/R44 live from-fill sources on true R41 derived hosts.

The framing oracle is an independent geometry acceptance fixture, not a
production template generator.  No PF-6/UI or complete R03 claim is made.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import test_panel_fill_layout as pf2


class PanelFillGridSource(unittest.TestCase):
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

    def commit(self, line):
        result = self.command("line " + line)
        self.assertTrue(result["ok"], "C0_FROM_FILL_ACCEPT: " + line + " " + str(result))
        return result

    def host(self, side=1, outline="-250,-250 350,-250 350,350 -250,350", **changes):
        self.seed(outline=outline)
        if side != 1:
            self.apply([pf2.put(pf2.surface(boundary=8, origin=(0,0,0), side=side, obstacles=[]))])
        self.apply([pf2.fill(**changes), dict(op="put-derived-placement", value=dict(id=10,fillId=1,h=30))])

    def grid(self):
        return next(g for g in self.command("references")["grids"] if g["id"] == 11)

    def guides(self):
        return {g["id"]: g for g in self.command("references")["guides"]}

    def query(self, rect=(-250,-250,350,350)):
        result = self.command("grid-query grid 11 rect " + " ".join(map(str, rect)) + " mode exact limit 64")
        self.assertTrue(result["ok"], result)
        return result

    def test_C0_D10_source_identity_and_definition_only_roundtrip(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.assertEqual(1, self.grid()["fillId"], "C0_LIVE_SOURCE: retain source fill identity")
        self.assertEqual("lattice", self.grid()["indexSpace"])
        self.commit("guide 1 10 v grid:11:u:-1")
        self.commit("guide 2 10 u grid:11:v:0")
        self.assertEqual((-2,101), (self.guides()[1]["off"],self.guides()[2]["off"]))
        scene = self.command("dump")["text"]
        self.assertEqual(["grid 11 on 10 from-fill 1 main-along v"],
                         [line for line in scene.splitlines() if line.startswith("grid 11 ")])
        self.assertLess(scene.index("derived-placement 10 "), scene.index("grid 11 "))
        self.assertNotIn("grid 11 on 10 u ", scene, "C0_NO_SNAPSHOT: no expanded coordinate copy")
        before = self.command("references")
        self.load_text(scene, "from-fill.scene")
        self.assertEqual(scene, self.command("dump")["text"])
        self.assertEqual(before["grids"], self.command("references")["grids"])
        self.assertEqual(before["guides"], self.command("references")["guides"])

    def test_C0_R44_negative_structure_side_preserves_signed_k(self):
        self.host(side=-1)
        self.commit("grid 11 on 10 from-fill 1 main-along u")
        for identifier, axis, k in [(1,"u",-1),(2,"v",-1),(3,"v",0),(4,"v",1)]:
            self.commit(f"guide {identifier} 10 {'v' if axis == 'u' else 'u'} grid:11:{axis}:{k}")
        self.assertEqual([-2,2,-101,-204], [self.guides()[i]["off"] for i in range(1,5)],
                         "C0_SIDE_SIGN: map v=s*c(k), never renumber k or round gap/2 again")
        lines = self.query((-250,-350,350,250))["axes"]["v"]["lines"]
        expected = [(str(k),-(101+103*k)) for k in range(-5,5) if -350 <= -(101+103*k) <= 250]
        self.assertEqual(sorted(expected), sorted((r["index"],r["coordinate"]) for r in lines))

    def test_C0_R44_source_change_cancel_and_history(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.commit("guide 1 10 v grid:11:u:-1")
        before = self.snapshot()
        preview = self.preview([pf2.fill(origin=[10,20])])
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.snapshot(), "C0_PREVIEW_ZERO_WRITE")
        self.assertTrue(self.command("panel-fill-cancel " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.snapshot(), "C0_CANCEL_ZERO_WRITE")
        self.apply([pf2.fill(origin=[10,20])])
        self.assertEqual(8, self.guides()[1]["off"], "C0_LIVE_REBUILD: same signed source key follows fill")
        after = self.command("dump")["text"]
        self.commit("undo")
        self.assertEqual(before[0], self.command("dump")["text"])
        self.assertEqual(-2, self.guides()[1]["off"])
        self.commit("redo")
        self.assertEqual(after, self.command("dump")["text"])
        self.assertEqual(8, self.guides()[1]["off"])

    def test_C0_D10_rejects_wrong_host_mixed_source_and_children_atomically(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.commit("placement 8 on boundary 8 origin 0 0 0 u +x v +y")
        for line in ["grid 12 on 8 from-fill 1", "grid 11 on 10 from-fill 2",
                     "grid 11 on 10 u 10 20", "grid 12 on 10 from-fill 1 u 10 20",
                     "subgrid 12 parent 11 lattice-cell 0 0 divisions u 2 v 2"]:
            with self.subTest(line=line):
                before = self.snapshot()
                self.assertFalse(self.command("line " + line)["ok"], "C0_SOURCE_GUARD: " + line)
                self.assertEqual(before, self.snapshot(), "C0_REJECT_ZERO_WRITE: " + line)

    def test_C0_D43_bands_use_panel_rows_on_both_axes_and_sides(self):
        for axis in ("u", "v"):
            for side in (1, -1):
                with self.subTest(axis=axis, side=side):
                    self.host(side=side, pattern="stagger", stagger=dict(axis=axis,value=20))
                    self.commit("grid 11 on 10 from-fill 1 main-along v")
                    rect = (-250,-250,350,350) if side == 1 else (-250,-350,350,250)
                    result = self.query(rect)
                    actual = []
                    for row in result["axes"][axis]["lines"]:
                        if int(row["index"]) != 0:
                            continue
                        for segment in row["segments"]:
                            actual.append((int(segment["band"]), tuple(segment["a"]), tuple(segment["b"])))
                    expected = []
                    for band in range(-5,5):
                        lo,hi = max(-250,101+(band-1)*103),min(350,101+band*103)
                        if lo >= hi:
                            continue
                        coordinate = 101+(20 if band & 1 else 0)
                        if axis == "u":
                            low,high = sorted((side*lo,side*hi))
                            a,b = (coordinate,low),(coordinate,high)
                        else:
                            a,b = (lo,side*coordinate),(hi,side*coordinate)
                        expected.append((band,a,b))
                    self.assertEqual(sorted(expected), sorted(actual),
                                     "C0_D43_BAND: c(p-1)..c(p), signed row identity, then frame transform")

    def test_C0_D6a_and_D7_require_the_same_explicit_band(self):
        self.host(outline="-250,-2 350,-2 350,101 -250,101", pattern="stagger",stagger=dict(axis="u",value=20))
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.commit("guide 1 10 v grid:11:u:0:band:-1")
        self.commit("guide 2 10 v grid:11:u:0:band:0")
        self.assertEqual((121,101), (self.guides()[1]["off"],self.guides()[2]["off"]))
        for line in ["guide 3 10 v grid:11:u:0", "guide 3 10 u grid:11:v:0:band:0"]:
            before = self.snapshot()
            self.assertFalse(self.command("line "+line)["ok"], "C0_D6A_BAND_GUARD: "+line)
            self.assertEqual(before,self.snapshot())
        for identifier,edge in [(1,"e0"),(2,"e2")]:
            key = json.dumps([[edge,0,1]],separators=(",",":")).encode().hex()
            self.commit(f"timber {identifier} 10 30 role boundary")
            self.commit(f"place {identifier} on 10 at-face key-hex:{key} +u +n")
        self.commit("timber 3 27 30 role primary")
        for anchor in ["grid 11 u 0", "grid 11 v 0 band 0", "grid 11 u 0 band -1"]:
            before = self.snapshot()
            self.assertFalse(self.command("line place 3 on 10 at-line "+anchor+" between t1 t2 +v +n")["ok"],
                             "C0_D7_BAND_GUARD: "+anchor)
            self.assertEqual(before,self.snapshot())
        self.commit("place 3 on 10 at-line grid 11 u 0 band 0 between t1 t2 +v +n")
        placed = next(t for t in self.command("references")["timbers"] if t["id"] == 3)
        self.assertEqual("at-line grid 11 u 0 band 0",placed["definition"]["anchor"])
        self.assertEqual(101,placed["geometry"]["centerline"])
        scene = self.command("dump")["text"]
        self.load_text(scene,"band.scene")
        self.assertEqual(scene,self.command("dump")["text"])

    def test_C0_native_render_keeps_shifted_lines_and_their_band_extent(self):
        # In odd row 1, k=-2 moves from -105 (outside) to 95 (inside).
        # No unshifted u line is inside this host. This catches both a missing
        # expanded query window and rendering a staggered line as a through line.
        for side in (1,-1):
            with self.subTest(side=side):
                self.host(side=side,outline="20,-2 100,-2 100,201 20,201",
                          pattern="stagger",stagger=dict(axis="u",value=200))
                self.commit("grid 11 on 10 from-fill 1 main-along v")
                bounds = (20,-2,100,201) if side == 1 else (20,-201,100,2)
                lines = self.query(bounds)["axes"]["u"]["lines"]
                self.assertIn("-2",[line["index"] for line in lines],"C0_SHIFTED_WINDOW: retain source k")
                view = -1
                segments = []
                for op in self.command("render")["ops"]:
                    if op["op"] == "begin":
                        view += 1
                    if view == 2 and op["op"] == "line" and op["s"] == 7 and op["x0"] == op["x1"]:
                        segments.append(tuple(sorted(((op["x0"],op["y0"]),(op["x1"],op["y1"])))))
                self.assertEqual([((95,101),(95,201))],sorted(segments),
                                 "C0_RENDER_BANDS: actual DrawTarget must emit only the clipped band")

    def test_C0_live_D7_moves_and_collision_rejects_the_entire_source_edit(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        for identifier,edge in [(1,"e0"),(2,"e2")]:
            key = json.dumps([[edge,0,1]],separators=(",",":")).encode().hex()
            self.commit(f"timber {identifier} 27 30 role boundary")
            self.commit(f"place {identifier} on 10 at-face key-hex:{key} +u +n")
        for line in ["timber 3 27 30 role primary", "place 3 on 10 at-line grid 11 u 0 between t1 t2 +v +n",
                     "spec fixed 160", "guide 1 10 v spec:fixed", "timber 4 27 30 role primary",
                     "place 4 on 10 at-line guide 1 between t1 t2 +v +n"]:
            self.commit(line)
        def timber():
            return next(t for t in self.command("references")["timbers"] if t["id"] == 3)
        self.assertEqual(101,timber()["geometry"]["centerline"])
        before_move = self.snapshot()
        preview = self.preview([pf2.fill(origin=[10,20])])
        self.assertTrue(preview["valid"],preview)
        for state,centerline in [("before",101),("after",111)]:
            affected = next(t for t in preview["dependencies"][state]["geometry"]["timbers"] if t["id"] == 3)
            self.assertEqual(centerline,affected["geometry"]["centerline"],"C0_I8A_PREVIEW_GEOMETRY: "+state)
        self.assertEqual(before_move,self.snapshot(),"C0_I8A_PREVIEW_ZERO_WRITE")
        self.assertTrue(self.command("panel-fill-confirm "+str(preview["token"]))["ok"])
        self.assertEqual(111,timber()["geometry"]["centerline"],"C0_D7_REBUILD: actual R6 geometry must follow")
        self.assertEqual("at-line grid 11 u 0",timber()["definition"]["anchor"])
        before = self.snapshot()
        preview = self.preview([pf2.fill(origin=[59,20])])
        self.assertFalse(preview["valid"],"C0_COLLISION: moved source may not overlap the fixed primary")
        self.assertFalse(self.command("panel-fill-confirm "+str(preview["token"]))["ok"])
        self.assertEqual(before,self.snapshot(),"C0_COLLISION_ZERO_WRITE")
        self.assertEqual(111,timber()["geometry"]["centerline"])
        self.commit("undo")
        self.assertEqual(101,timber()["geometry"]["centerline"])
        self.commit("redo")
        self.assertEqual(111,timber()["geometry"]["centerline"])
        scene = self.command("dump")["text"]
        before_timbers = self.command("references")["timbers"]
        self.load_text(scene,"live-timber.scene")
        self.assertEqual(before_timbers,self.command("references")["timbers"])

    def test_C0_existing_distinct_fill_host_and_source_variants_cannot_be_hijacked(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.apply([pf2.fill(id=2), dict(op="put-derived-placement",value=dict(id=12,fillId=2,h=30))])
        self.commit("grid 13 on 12 u 10 20")
        for line in ["grid 14 on 12 from-fill 1", "grid 11 on 10 from-fill 2",
                     "grid 13 on 12 from-fill 2", "grid 11 on 10 from-fill 1 u 10",
                     "grid 11 on 12 from-fill 2"]:
            with self.subTest(line=line):
                before = self.snapshot()
                self.assertFalse(self.command("line "+line)["ok"],"C0_NO_HIJACK: "+line)
                self.assertEqual(before,self.snapshot())

    def test_C0_outside_line_identity_and_overflow_are_not_silently_clipped(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.commit("guide 1 10 v grid:11:u:-10")
        self.assertEqual(-929,self.guides()[1]["off"])
        self.assertEqual([],self.guides()[1]["segments"],"C0_OUTSIDE: invisible line retains its source key")
        for index in (9223372036854775807,-9223372036854775808):
            before = self.snapshot()
            self.assertFalse(self.command(f"line guide 2 10 v grid:11:u:{index}")["ok"])
            self.assertEqual(before,self.snapshot())

    def test_C0_missing_source_and_derived_host_cannot_partially_reopen(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        self.commit("guide 1 10 v grid:11:u:0")
        scene = self.command("dump")["text"]
        for prefix in ("panel-fill 1 ","derived-placement 10 ","requires panel-fill/1"):
            with self.subTest(prefix=prefix):
                corrupted = "\n".join(line for line in scene.splitlines() if not line.startswith(prefix))+"\n"
                path = self.directory/"incomplete.scene"
                path.write_text(corrupted)
                before = self.snapshot()
                self.assertFalse(self.command("loadfile "+str(path))["ok"],"C0_SOURCE_CLOSURE: "+prefix)
                self.assertEqual(before,self.snapshot())
        self.reject([dict(op="delete-panel-fill",id=1)],"source fill")
        self.reject([dict(op="delete-derived-placement",id=10)],"placement")

    def test_C0_oracle_F3_F4_all_eight_layouts_have_every_native_member(self):
        from tests.pf_from_fill_oracle import run_oracle_cases
        report = run_oracle_cases(self, cold=True)
        self.assertEqual(16,len(report["cases"]),"C0_ORACLE_ALL_LAYOUTS")
        self.assertEqual(592,sum(len(row["rows"]) for row in report["cases"]),"C0_ORACLE_ALL_MEMBERS")

    def test_C0_main_along_preferences_do_not_change_geometry_or_source(self):
        self.host()
        self.commit("grid 11 on 10 from-fill 1 main-along v")
        before = self.query()["axes"]
        self.commit("grid 11 on 10 from-fill 1 main-along u")
        self.assertEqual(before,self.query()["axes"],"C0_ROLE_GEOMETRY_SEPARATION")
        self.commit("grid 11 on 10 from-fill 1")
        self.assertIn("grid 11 on 10 from-fill 1 main-along u",self.command("dump")["text"])
        self.commit("grid 11 on 10 from-fill 1 main-along none")
        self.assertEqual(before,self.query()["axes"])
        self.assertEqual(1,self.grid()["fillId"])


if __name__ == "__main__":
    unittest.main()
