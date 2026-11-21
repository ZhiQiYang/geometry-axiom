"""PF4-A: create-only live grid transactions, against the actual native bridge.

These are explicit D10/R44 and issue #128 section 7.6 oracles.  They do not
claim D29 value snapshots, R45 suggestions, or a browser/L4 receipt.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import test_panel_fill_layout as pf2
from tests._bridge import BridgeSession


def create_grid(fill=1, host=10, main="v"):
    return {"op": "create-from-fill-grid", "value": {
        "fillId": fill, "hostId": host, "mainAlong": main}}


class PanelFillGridTransaction(unittest.TestCase):
    setUpClass = pf2.PanelFillLayout.__dict__["setUpClass"]
    setUp = pf2.PanelFillLayout.setUp
    command = pf2.PanelFillLayout.command
    load_text = pf2.PanelFillLayout.load_text
    read = pf2.PanelFillLayout.read
    snapshot = pf2.PanelFillLayout.snapshot
    preview = pf2.PanelFillLayout.preview
    apply = pf2.PanelFillLayout.apply
    seed = pf2.PanelFillLayout.seed

    def host(self, side=1, **changes):
        self.seed(outline="-250,-250 350,-250 350,350 -250,350")
        if side != 1:
            self.apply([pf2.put(pf2.surface(boundary=8, origin=(0, 0, 0), side=side, obstacles=[]))])
        self.apply([pf2.fill(**changes), {"op": "put-derived-placement",
                   "value": {"id": 10, "fillId": 1, "h": 30}}])

    def commit(self, line):
        result = self.command("line " + line)
        self.assertTrue(result["ok"], "PF4A_FIXTURE: " + str(result))
        return result

    def valid(self, operations):
        preview = self.preview(operations)
        self.assertTrue(preview["valid"], "PF4A_CREATE_NATIVE: " + json.dumps(preview["violations"]))
        return preview

    def grids(self, response=None, stage="state"):
        response = self.read() if response is None else response
        state = response["uiContract"][stage]
        self.assertIn("fillGrids", state, "PF4A_WIRE_GRIDS: complete source-grid view is required")
        return state["fillGrids"]

    def confirmed_grid(self, main="v"):
        preview = self.valid([create_grid(main=main)])
        done = self.command("panel-fill-confirm %d" % preview["token"])
        self.assertTrue(done["ok"], done)
        grids = self.grids()
        self.assertEqual(1, len(grids))
        return grids[0]["id"]

    def rejection(self, operations, message):
        before = self.snapshot()
        preview = self.preview(operations)
        self.assertFalse(preview["valid"], message)
        self.assertFalse(self.command("panel-fill-confirm %d" % preview["token"])["ok"], message)
        self.assertEqual(before, self.snapshot(), "PF4A_REJECT_ZERO_WRITE")
        return preview

    def test_PF4A_wire_is_explicit_additive_and_keeps_partial_capability(self):
        self.host()
        reply = self.read()
        self.assertFalse(reply["complete"], "PF4A_NO_FULL_PRODUCT_CLAIM")
        self.assertEqual(["read", "edit-definitions", "read-layout", "read-support",
                          "create-from-fill-grid"], reply["uiContract"]["supportedActions"])
        self.assertEqual([], self.grids(reply))
        self.assertEqual([], reply["uiContract"]["scope"]["fillGridIds"])
        self.assertNotIn("panel-fill/1", reply["capabilities"])

    def test_PF4A_create_preview_and_cancel_do_not_allocate_or_write(self):
        self.host()
        before = self.snapshot()
        ids = self.command("newid")
        preview = self.valid([create_grid()])
        self.assertEqual(before, self.snapshot(), "PF4A_PREVIEW_ZERO_WRITE")
        self.assertEqual(ids, self.command("newid"), "PF4A_PREVIEW_NO_FORMAL_ID_CONSUMPTION")
        self.assertEqual([], self.grids(preview, "before"))
        row, = self.grids(preview, "after")
        self.assertEqual({"id": row["id"], "hostId": 10, "fillId": 1, "mainAlong": "v"}, row["definition"])
        self.assertEqual([row["id"]], preview["uiContract"]["scope"]["fillGridIds"])
        self.assertIn({"record": "fill-grid", "id": row["id"], "change": "created"}, preview["changes"])
        for stage in ("before", "after"):
            self.assertTrue(all(k in preview["dependencies"][stage]["geometry"] for k in ("grids", "guides", "timbers")))
        self.assertTrue(self.command("panel-fill-cancel %d" % preview["token"])["ok"])
        self.assertEqual(before, self.snapshot(), "PF4A_CANCEL_ZERO_WRITE")
        self.assertEqual(ids, self.command("newid"))
        again = self.valid([create_grid()])
        self.assertEqual(row["id"], self.grids(again, "after")[0]["id"], "PF4A_CANDIDATE_ID_REUSED_AFTER_CANCEL")

    def test_PF4A_confirm_is_one_history_step_and_undo_redo_restore_definition(self):
        self.host()
        before = self.snapshot()
        preview = self.valid([create_grid()])
        done = self.command("panel-fill-confirm %d" % preview["token"])
        self.assertTrue(done["ok"] and done["history_changed"])
        self.assertEqual(before[1] + 1, done["revision"], "PF4A_SINGLE_REVISION")
        self.assertEqual(before[1], done["before_revision"])
        after = self.command("dump")["text"]
        self.assertNotEqual(before[0], after)
        self.commit("undo")
        self.assertEqual(before[0], self.command("dump")["text"], "PF4A_ONE_UNDO")
        self.assertEqual([], self.grids())
        self.commit("redo")
        self.assertEqual(after, self.command("dump")["text"], "PF4A_ONE_REDO")
        self.assertEqual(1, len(self.grids()))

    def test_PF4A_same_definition_is_native_noop_with_no_history_or_revision(self):
        self.host()
        grid_id = self.confirmed_grid(main=None)
        before = self.snapshot()
        preview = self.valid([create_grid(main=None)])
        self.assertEqual([], preview["changes"], "PF4A_NOOP_CHANGES")
        self.assertEqual(grid_id, self.grids(preview, "after")[0]["id"], "PF4A_NOOP_REUSE_ID")
        done = self.command("panel-fill-confirm %d" % preview["token"])
        self.assertTrue(done["ok"])
        self.assertIs(done["history_changed"], False, "PF4A_NOOP_HISTORY")
        self.assertEqual(before, self.snapshot(), "PF4A_NOOP_REVISION")
        self.commit("undo")
        self.assertEqual([], self.grids(), "PF4A_NOOP_DID_NOT_INSERT_UNDO")

    def test_PF4A_create_refuses_different_preference_without_becoming_put(self):
        self.host()
        self.confirmed_grid(main="u")
        for main in ("v", None):
            with self.subTest(main=main):
                self.rejection([create_grid(main=main)], "PF4A_CREATE_ONLY: existing mainAlong must not be overwritten")

    def test_PF4A_create_refuses_direct_or_foreign_main_grid(self):
        self.host()
        self.commit("grid 11 on 10 u 10 20")
        self.rejection([create_grid()], "PF4A_SOURCE_IDENTITY: do not replace a direct main grid")
        self.assertIn("grid 11 on 10 u 10 20", self.command("dump")["text"])

    def test_PF4A_strict_inputs_reject_unknown_fields_and_missing_preference(self):
        self.host()
        bad = []
        for key, value in (("id", 77), ("axes", {}), ("panel", 100), ("placementId", 10)):
            op = create_grid(); op["value"][key] = value; bad.append(op)
        op = create_grid(); del op["value"]["mainAlong"]; bad.append(op)
        for main in ("none", "x", 0, False):
            bad.append(create_grid(main=main))
        bad.extend([create_grid(fill=0), create_grid(fill=99), create_grid(host=999)])
        op = create_grid(); op["unexpected"] = True; bad.append(op)
        for op in bad:
            with self.subTest(op=op):
                self.rejection([op], "PF4A_STRICT_INPUT")

    def test_PF4A_requires_existing_formal_host_and_same_candidate_source_closure(self):
        self.seed()
        before = self.snapshot()
        self.rejection([pf2.fill(), {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 30}},
                        create_grid()], "PF4A_EXISTING_HOST: create cannot secretly build its prerequisite")
        self.assertEqual(before, self.snapshot())
        self.host()
        self.rejection([{"op": "delete-derived-placement", "id": 10}, create_grid()], "PF4A_CANDIDATE_HOST_MISSING")
        self.rejection([{"op": "delete-panel-fill", "id": 1}, create_grid()], "PF4A_CANDIDATE_FILL_MISSING")
        self.apply([pf2.fill(id=2), {"op": "put-derived-placement", "value": {"id": 12, "fillId": 2, "h": 30}}])
        self.rejection([create_grid(fill=1, host=12)], "PF4A_SAME_FILL_HOST_IDENTITY")

    def test_PF4A_empty_operations_and_stale_confirm_do_not_write(self):
        self.host()
        before = self.snapshot()
        path = self.directory / "empty.json"
        path.write_text(json.dumps({"schema": "panel-fill-transaction/1", "expectedRevision": before[1], "operations": []}))
        reply = self.command("panel-fill-preview " + str(path))
        self.assertFalse(reply["ok"], "PF4A_EMPTY_NOT_COMMITTABLE")
        self.assertEqual(before, self.snapshot())
        preview = self.valid([create_grid()])
        self.commit("spec changed 1")
        changed = self.snapshot()
        self.assertFalse(self.command("panel-fill-confirm %d" % preview["token"])["ok"], "PF4A_STALE_CONFIRM")
        self.assertEqual(changed, self.snapshot())
        self.assertEqual([], self.grids())

    def test_PF4A_native_allocator_skips_grid_ids_on_other_hosts(self):
        self.host()
        for identifier in (1, 3):
            self.commit(f"surface {20+identifier} origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 0,100")
            self.commit(f"grid {identifier} on {20+identifier} u 20")
        before = self.snapshot()
        preview = self.valid([create_grid()])
        row, = self.grids(preview, "after")
        self.assertNotIn(row["id"], (1, 3), "PF4A_NATIVE_ID_NO_COLLISION")
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command("panel-fill-confirm %d" % preview["token"])["ok"])
        self.assertEqual(3, len(self.command("references")["grids"]))

    def test_PF4A_exact_negative_side_and_stagger_keep_signed_source_indices(self):
        self.host(side=-1, pattern="stagger", stagger={"axis": "v", "value": 20})
        grid_id = self.confirmed_grid()
        row, = self.grids()
        self.assertEqual({"indexSpace": "lattice", "bandIndexSpace": "panel-row", "side": -1,
            "staggerAxis": "v", "staggerDelta": "-20", "axes": {
                "u": {"baseCoordinate": "101", "pitch": "103", "baseIndex": "0"},
                "v": {"baseCoordinate": "-101", "pitch": "-103", "baseIndex": "0"}}}, row["derived"],
            "PF4A_EXACT_GRID_VIEW: map values once; signed k is unchanged")
        self.commit(f"guide 1 10 u grid:{grid_id}:v:0:band:-1")
        guide, = self.command("references")["guides"]
        self.assertEqual(-121, guide["off"], "PF4A_NEGATIVE_ODD_BAND")
        self.commit(f"guide 2 10 u grid:{grid_id}:v:0:band:0")
        self.assertEqual(-101, self.command("references")["guides"][1]["off"])

    def test_PF4A_live_source_moves_real_D7_and_collision_rejects_whole_edit(self):
        self.host()
        grid_id = self.confirmed_grid()
        for identifier, edge in ((1, "e0"), (2, "e2")):
            key = json.dumps([[edge, 0, 1]], separators=(",", ":")).encode().hex()
            self.commit(f"timber {identifier} 27 30 role boundary")
            self.commit(f"place {identifier} on 10 at-face key-hex:{key} +u +n")
        for line in ("timber 3 27 30 role primary", f"place 3 on 10 at-line grid {grid_id} u 0 between t1 t2 +v +n",
                     "spec fixed 160", "guide 1 10 v spec:fixed", "timber 4 27 30 role primary",
                     "place 4 on 10 at-line guide 1 between t1 t2 +v +n"):
            self.commit(line)
        before = self.snapshot()
        candidate = self.valid([pf2.fill(origin=[10, 20]), create_grid()])
        for stage, coordinate in (("before", 101), ("after", 111)):
            timber = next(t for t in candidate["dependencies"][stage]["geometry"]["timbers"] if t["id"] == 3)
            self.assertEqual(coordinate, timber["geometry"]["centerline"], "PF4A_I8A_D7_" + stage)
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command("panel-fill-cancel %d" % candidate["token"])["ok"])
        self.assertEqual(before, self.snapshot(), "PF4A_MOVE_CANCEL_ZERO_WRITE")
        candidate = self.valid([pf2.fill(origin=[10, 20]), create_grid()])
        self.assertTrue(self.command("panel-fill-confirm %d" % candidate["token"])["ok"])
        self.rejection([pf2.fill(origin=[59, 20]), create_grid()], "PF4A_REAL_D7_COLLISION")
        timber = next(t for t in self.command("references")["timbers"] if t["id"] == 3)
        self.assertEqual(111, timber["geometry"]["centerline"])
        self.assertEqual(f"at-line grid {grid_id} u 0", timber["definition"]["anchor"])

    def test_PF4A_save_and_new_native_process_reopen_recompute_full_source_closure(self):
        self.host()
        grid_id = self.confirmed_grid()
        self.commit(f"guide 1 10 v grid:{grid_id}:u:-1")
        scene = self.command("dump")["text"]
        self.assertEqual([f"grid {grid_id} on 10 from-fill 1 main-along v"],
                         [line for line in scene.splitlines() if line.startswith("grid ")])
        before = self.read()["uiContract"]["state"]
        refs = self.command("references")
        path = self.directory / "reopen.scene"
        path.write_text(scene)
        with BridgeSession(self.binary, cwd=self.directory) as cold:
            self.assertTrue(cold.command("loadfile " + str(path))["ok"])
            self.assertEqual(scene, cold.command("dump")["text"], "PF4A_COLD_SCENE")
            self.assertEqual(before, cold.command("panel-fill-read")["uiContract"]["state"], "PF4A_COLD_DERIVED")
            for key in ("grids", "guides", "timbers"):
                self.assertEqual(refs[key], cold.command("references")[key], "PF4A_COLD_" + key)
        before_live = self.snapshot()
        for prefix in ("panel-fill 1 ", "derived-placement 10 ", "requires panel-fill/1"):
            path.write_text("\n".join(line for line in scene.splitlines() if not line.startswith(prefix)) + "\n")
            self.assertFalse(self.command("loadfile " + str(path))["ok"], "PF4A_REOPEN_MISSING_SOURCE: " + prefix)
            self.assertEqual(before_live, self.snapshot())


if __name__ == "__main__":
    unittest.main()
