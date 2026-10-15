"""PF-1 native slice: D41 finish surfaces against the real C bridge (GEO-255, issue #128).

Covers D41 / I52 / I55 / I56 / R4 and the first half of R41 (obstacle projection R_k, q interval and the
plane relation int(R_k) n int(F)).  Every oracle below is computed by hand from the fixture numbers, not
read back from the implementation.  Two-layer judgement (I53) needs a panel fill (t) and a derived
placement (h); PF-1 has neither, so previews must say "pending" instead of guessing.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests._bridge import BridgeSession, find_bridge

# Boundary 3: 4000 x 3000 rectangle with one hole [1000,1400] x [1000,1300].
# Boundary 4: L shape; the notch u in [2000,4000] x v in [1500,3000] is outside F, although it is inside F's bbox.
# Column 1 sits in that notch (bbox overlap, no area overlap, no contact).  Column 5 touches the inner edge u=2000.
# Beam 2 crosses the whole room along x at y in [700,1000], z in [2500,2800].
BASE = """boundary 3 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan hole 1000,1000 1400,1000 1400,1300 1000,1300
boundary 4 outline 0,0 4000,0 4000,1500 2000,1500 2000,3000 0,3000 kind room_plan
column 1 at 3000 2000 size 300 300 z 0 3000
column 5 at 2000 2000 size 300 300 z 0 3000
beam 2 along x from 0 to 4000 at 850 width 300 depth 300 top 2800
"""


def frame(origin, u="+X", v="+Y", n="+Z"):
    return {"origin": list(origin), "U": u, "V": v, "N": n}


def surface(identifier=1, boundary=4, origin=(0, 0, 2480), side=1, obstacles=None, name="天花完成面", **axes):
    return {"id": identifier, "name": name, "boundaryId": boundary, "frame": frame(origin, **axes),
            "structureSide": side, "obstacles": ["b2", "c1", "c5"] if obstacles is None else obstacles}


def put(value):
    return {"op": "put-finish-surface", "value": value}


class FinishSurfaceNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-pf1-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bridge = BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.assertTrue(self.command("reset")["ok"])
        self.load_text(BASE)

    # ---- plumbing -------------------------------------------------------------------------------------------
    def command(self, text):
        return self.bridge.command(text)

    def load_text(self, text, name="scene.scene"):
        path = self.directory / name
        path.write_bytes(text.encode("utf-8"))
        result = self.command("loadfile " + str(path))
        self.assertTrue(result["ok"], result)
        return result

    def load_fails(self, text, reason):
        before = self.snapshot()
        path = self.directory / "bad.scene"
        path.write_bytes(text.encode("utf-8"))
        result = self.command("loadfile " + str(path))
        self.assertFalse(result["ok"], result)
        self.assertIn(reason, result["error"])
        self.assertEqual(before, self.snapshot(), "a rejected reopen must not replace the current World")

    def read(self):
        result = self.command("panel-fill-read")
        self.assertTrue(result["ok"], result)
        return result

    def snapshot(self):
        return self.command("dump")["text"], self.read()["revision"]

    def preview(self, operations, revision=None):
        path = self.directory / "transaction.json"
        path.write_text(json.dumps({"schema": "panel-fill-transaction/1",
                                    "expectedRevision": self.read()["revision"] if revision is None else revision,
                                    "operations": operations}, ensure_ascii=False), encoding="utf-8")
        result = self.command("panel-fill-preview " + str(path))
        self.assertTrue(result["ok"], result)
        return result["preview"]

    def apply(self, operations):
        preview = self.preview(operations)
        self.assertTrue(preview["valid"], preview)
        done = self.command("panel-fill-confirm %d" % preview["token"])
        self.assertTrue(done["ok"], done)
        return preview

    def reject(self, operations, reason):
        before = self.snapshot()
        preview = self.preview(operations)
        self.assertFalse(preview["valid"], preview)
        self.assertIn(reason, json.dumps(preview["violations"], ensure_ascii=False))
        self.assertFalse(self.command("panel-fill-confirm %d" % preview["token"])["ok"])
        self.assertEqual(before, self.snapshot(), "a rejected candidate must leave World and revision unchanged")
        return preview

    def surfaces(self, state=None):
        state = state or self.read()["state"]
        return {item["id"]: item for item in state["finishSurfaces"]}

    @staticmethod
    def relations(item):
        return {o["ref"]: (o["relation"], o["rect"], o["q"]) for o in item["derived"]["obstacles"]}

    # ---- D41 / R41: definition, world position and plane relation ---------------------------------------------
    def test_create_preview_lists_each_obstacle_relation_and_keeps_layers_pending(self):
        preview = self.apply([put(surface())])
        self.assertEqual([{"id": 1, "change": "created"}], preview["changes"])
        created = self.surfaces(preview["after"])[1]
        # The set is normalised to the R41 source order: columns by id, then beams by id.
        self.assertEqual(["c1", "c5", "b2"], created["obstacles"])
        self.assertEqual("+Z", created["derived"]["n"])
        rel = self.relations(created)
        # Column 1 is inside F's bounding box but in the L notch: no area, no contact.
        self.assertEqual(("separate", [3000, 2000, 3300, 2300], [-2480, 520]), rel["c1"])
        # Column 5 shares the inner edge u=2000 with F: contact only.
        self.assertEqual(("touch", [2000, 2000, 2300, 2300], [-2480, 520]), rel["c5"])
        self.assertEqual(("interior", [0, 700, 4000, 1000], [20, 320]), rel["b2"])
        for item in created["derived"]["obstacles"]:
            self.assertIsNone(item["layers"], "I53 needs t and h; PF-1 must not invent a layer verdict")
        self.assertEqual("pending", preview["layerJudgement"]["status"])
        self.assertEqual(self.surfaces()[1]["obstacles"], ["c1", "c5", "b2"])

    def test_world_position_follows_frame_and_structure_side(self):
        # Same L boundary, lower height, mirrored frame looking up (U=+X, V=-Y, N=-Z) and s=-1.
        self.apply([put(surface()), put(surface(2, origin=(0, 3000, 2400), side=-1, v="-Y", n="-Z"))])
        mirrored = self.surfaces()[2]
        self.assertEqual("+Z", mirrored["derived"]["n"], "n = s*N = (-1)*(-Z)")
        rel = self.relations(mirrored)
        # v = 3000 - y; w = 2400 - z; q = s*w = z - 2400.
        self.assertEqual(("interior", [3000, 700, 3300, 1000], [-2400, 600]), rel["c1"])
        self.assertEqual(("interior", [0, 2000, 4000, 2300], [100, 400]), rel["b2"])
        self.assertEqual(self.relations(self.surfaces()[1])["c1"][0], "separate")

    def test_holes_are_subtracted_from_f(self):
        self.load_text(BASE + "column 7 at 1050 1050 size 100 100 z 0 3000\n"
                              "column 8 at 1000 1000 size 50 50 z 0 3000\n", "holes.scene")
        self.apply([put(surface(1, boundary=3, obstacles=["c7", "c8", "c1"]))])
        rel = self.relations(self.surfaces()[1])
        self.assertEqual("separate", rel["c7"][0], "fully inside the hole, away from its edges")
        self.assertEqual("touch", rel["c8"][0], "inside the hole, touching its corner edges")
        self.assertEqual("interior", rel["c1"][0])

    def test_gap_between_prongs_is_outside_f(self):
        # U shape: one horizontal band crosses four vertical edges (u = 0, 1000, 2000, 3000); the middle pair
        # bounds the gap u in [1000,2000], v in [1000,3000], which is outside F although inside its bbox.
        self.load_text(BASE + "boundary 6 outline 0,0 3000,0 3000,3000 2000,3000 2000,1000 1000,1000 1000,3000 0,3000\n"
                              "column 11 at 1200 2000 size 600 300 z 0 3000\n"
                              "column 12 at 2400 2000 size 300 300 z 0 3000\n", "prongs.scene")
        self.apply([put(surface(1, boundary=6, obstacles=["c11", "c12"]))])
        rel = self.relations(self.surfaces()[1])
        self.assertEqual(("separate", [1200, 2000, 1800, 2300]), rel["c11"][:2])
        self.assertEqual(("interior", [2400, 2000, 2700, 2300]), rel["c12"][:2])

    # ---- I52 / D41 negatives --------------------------------------------------------------------------------
    def test_invalid_definitions_are_rejected_without_changing_world(self):
        cases = [
            (surface(boundary=99), "I52"),
            (surface(n="-Z"), "I1"),
            (surface(v="+X", n="+Z"), "I1"),
            (surface(origin=(100000001, 0, 0)), "I1"),
            (surface(side=0), "structureSide"),
            (surface(side=2), "structureSide"),
            (surface(obstacles=["c99"]), "c99"),
            (surface(obstacles=["b99"]), "b99"),
            (surface(obstacles=["x1"]), "c<id>"),
            (surface(obstacles=["c01"]), "c<id>"),
            (surface(obstacles=["c1", "c1"]), "more than once"),
            (surface(name=""), "name"),
            (surface(name="長" * 33), "name"),
            (surface(identifier=0), "D41"),
        ]
        for value, reason in cases:
            with self.subTest(reason=reason, value=value):
                self.reject([put(value)], reason)
        missing_frame = surface()
        del missing_frame["frame"]
        self.reject([put(missing_frame)], "D41")
        bad_axes = surface()
        bad_axes["frame"] = {"origin": [0, 0, 0], "U": "+X", "V": "+Y"}
        self.reject([put(bad_axes)], "I52")

    def test_local_obstacle_coordinates_must_stay_in_d1(self):
        self.load_text(BASE + "column 9 at 99999000 0 size 500 500 z 0 3000\n", "far.scene")
        self.reject([put(surface(origin=(-100000000, 0, 2480), obstacles=["c9"]))], "D1")
        # I55: editing an obstacle re-checks every finish surface that lists it, in the candidate World.
        self.apply([put(surface(origin=(-99990000, 0, 2480), obstacles=["c1"]))])
        self.assertEqual([99993000, 2000, 99993300, 2300], self.relations(self.surfaces()[1])["c1"][1])
        before = self.snapshot()
        result = self.command("line column 1 at 20000 2000 size 300 300 z 0 3000")
        self.assertFalse(result["ok"], "moving c1 to u=100010000 leaves D1 in finish surface 1's frame")
        self.assertEqual(before, self.snapshot())

    def test_capacity_is_explicit(self):
        capacity = self.read()["capacity"]["finishSurfaces"]
        self.apply([put(surface(i, obstacles=[])) for i in range(1, capacity + 1)])
        preview = self.reject([put(surface(capacity + 1, obstacles=[]))], "CAPACITY")
        violation = preview["violations"][0]
        self.assertEqual("UNSUPPORTED", violation.get("status"), "I33: capacity is a capability limit, not invalid geometry")
        self.assertEqual("CAPACITY", violation["code"])
        invalid = self.reject([put(surface(boundary=99, obstacles=[]))], "I52")["violations"][0]
        self.assertEqual("INVALID", invalid.get("status"), "a missing reference must not be relabelled as a capacity limit")
        self.assertEqual("PANEL_FILL_INVALID", invalid["code"])
        saved = self.command("dump")["text"]
        record = next(line for line in saved.splitlines() if line.startswith("finish-surface 1 "))
        path = self.directory / "seventeenth.scene"
        path.write_bytes((saved + record.replace("finish-surface 1 ", "finish-surface %d " % (capacity + 1)) + "\n").encode("utf-8"))
        before = self.snapshot()
        result = self.command("loadfile " + str(path))
        self.assertFalse(result["ok"], result)
        self.assertEqual(("UNSUPPORTED", "CAPACITY"), (result.get("status"), result.get("code")))
        self.assertEqual(before, self.snapshot())

    def test_name_capacity_is_not_invalid_and_never_commits(self):
        limit = self.read()["capacity"]["nameBytes"]
        self.apply([put(surface(name="a" * limit))])
        self.apply([put(surface(name="a" * limit, origin=(0, 0, 2600)))])
        self.assertTrue(self.command("line undo")["ok"])
        for name in ("a" * (limit + 1), "長" * (limit // 3 + 1), "a" * 1024):
            with self.subTest(bytes=len(name.encode("utf-8"))):
                violation = self.reject([put(surface(name=name))], "CAPACITY")["violations"][0]
                self.assertEqual(("UNSUPPORTED", "CAPACITY"), (violation["status"], violation["code"]))
        for name in ("", "a" * limit + "\n", "a" * limit + "\u0080"):
            with self.subTest(invalid_name=repr(name)):
                violation = self.reject([put(surface(name=name))], "name")["violations"][0]
                self.assertEqual(("INVALID", "PANEL_FILL_INVALID"), (violation["status"], violation["code"]))
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual([0, 0, 2600], self.surfaces()[1]["frame"]["origin"])

    def test_scene_obstacle_capacity_is_structured_and_atomic(self):
        limit = self.read()["capacity"]["obstacles"]
        sources = "".join("column %d at %d 0 size 1 1 z 0 3000\n" % (i, i * 2)
                          for i in range(1, 33))
        sources += "".join("beam %d along x from 0 to 100 at %d width 1 depth 1 top 2800\n" % (i, i * 2)
                           for i in range(1, 33))
        head = BASE + sources + "requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n"
        prefix = "finish-surface 1 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n obstacles "
        all_refs = ["c%d" % i for i in range(1, 33)] + ["b%d" % i for i in range(1, 33)]
        refs = all_refs[:limit]
        record = lambda values: prefix + " ".join(values) + " name-hex 61\n"
        self.load_text(head + record(refs), "at-limit.scene")
        self.assertEqual(limit, len(self.surfaces()[1]["obstacles"]))
        # Preserve an existing redo entry as well as committed definitions/revision on rejection.
        self.apply([put(surface(origin=(0, 0, 2600), obstacles=refs))])
        self.assertTrue(self.command("line undo")["ok"])
        before = self.snapshot()
        # Production has only 32 columns + 32 beams: a distinct 65th source cannot exist.
        # A private lower-capacity build exercises the reachable, fully valid set overflow.
        overflow = (all_refs[limit], "UNSUPPORTED", "CAPACITY") if limit < len(all_refs) else ("c33", "INVALID", "SCENE_INVALID")
        cases = ((refs + [overflow[0]], overflow[1], overflow[2]),
                 (refs + ["x1"], "INVALID", "SCENE_INVALID"),
                 (refs + ["c1"], "INVALID", "SCENE_INVALID"),
                 (refs[:-1] + ["c999"], "INVALID", "SCENE_INVALID"),
                 (refs[:-1] + ["c1"], "INVALID", "SCENE_INVALID"))
        for values, status, code in cases:
            with self.subTest(tail=values[-1], count=len(values)):
                path = self.directory / "over-limit.scene"
                path.write_bytes((head + record(values)).encode("utf-8"))
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertEqual((status, code), (result.get("status"), result.get("code")))
                self.assertEqual(before, self.snapshot())
                if status == "UNSUPPORTED":
                    path.write_bytes(b"not-a-scene-command\n")
                    invalid = self.command("loadfile " + str(path))
                    self.assertEqual(("INVALID", "SCENE_INVALID"), (invalid.get("status"), invalid.get("code")))
                    self.assertEqual(before, self.snapshot())
        # A previous CAPACITY must not contaminate an unrelated scene syntax error.
        path.write_bytes(b"not-a-scene-command\n")
        invalid = self.command("loadfile " + str(path))
        self.assertEqual(("INVALID", "SCENE_INVALID"), (invalid.get("status"), invalid.get("code")))
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual([0, 0, 2600], self.surfaces()[1]["frame"]["origin"])

    def test_scene_name_capacity_preserves_invalid_format_and_world(self):
        self.apply([put(surface())])
        saved = self.command("dump")["text"]
        original = "天花完成面".encode("utf-8").hex()
        before = self.snapshot()
        for name, status, code in (("a" * 97, "UNSUPPORTED", "CAPACITY"),
                                   ("長" * 33, "UNSUPPORTED", "CAPACITY"),
                                   ("a" * 1024, "UNSUPPORTED", "CAPACITY"),
                                   ("a" * 96 + "\n", "INVALID", "SCENE_INVALID"),
                                   ("a" * 96 + "\u0080", "INVALID", "SCENE_INVALID")):
            with self.subTest(bytes=len(name.encode("utf-8")), status=status):
                path = self.directory / "name.scene"
                path.write_bytes(saved.replace(original, name.encode("utf-8").hex()).encode("utf-8"))
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertEqual((status, code), (result.get("status"), result.get("code")))
                self.assertEqual(before, self.snapshot())
                if status == "UNSUPPORTED":
                    path.write_bytes(b"not-a-scene-command\n")
                    invalid = self.command("loadfile " + str(path))
                    self.assertEqual(("INVALID", "SCENE_INVALID"), (invalid.get("status"), invalid.get("code")))
                    self.assertEqual(before, self.snapshot())
        for hex_name in ("ff", "61" * 96 + "ff", "c0af", "ed a0 80".replace(" ", ""), "00", "", "zz"):
            with self.subTest(invalid_hex=hex_name):
                path.write_bytes(saved.replace(original, hex_name).encode("utf-8"))
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertEqual(("INVALID", "SCENE_INVALID"), (result.get("status"), result.get("code")))
                self.assertEqual(before, self.snapshot())
        transaction = json.dumps({"schema": "panel-fill-transaction/1", "expectedRevision": self.read()["revision"],
                                  "operations": [put(surface(name="bad"))]}).encode("utf-8")
        path = self.directory / "invalid-utf8.json"
        path.write_bytes(transaction.replace(b'"bad"', b'"\xff"'))
        result = self.command("panel-fill-preview " + str(path))
        self.assertFalse(result["ok"], result)
        self.assertIn("UTF-8", result["error"])
        self.assertEqual(before, self.snapshot())

    # ---- I55: edit, delete, cancel, stale, history ------------------------------------------------------------
    def test_modify_cancel_stale_delete_and_history(self):
        self.apply([put(surface())])
        after_create = self.snapshot()
        modified = surface(origin=(0, 0, 2600), obstacles=["b2"])
        preview = self.preview([put(modified)])
        self.assertEqual([{"id": 1, "change": "modified"}], preview["changes"])
        self.assertEqual(["c1", "c5", "b2"], self.surfaces(preview["before"])[1]["obstacles"])
        cancelled = self.command("panel-fill-cancel %d" % preview["token"])
        self.assertTrue(cancelled["ok"] and cancelled["cancelled"], cancelled)
        self.assertEqual(after_create, self.snapshot())
        stale = self.preview([put(modified)])
        self.assertTrue(self.command("line column 1 at 3000 2100 size 300 300 z 0 3000")["ok"])
        moved = self.snapshot()
        result = self.command("panel-fill-confirm %d" % stale["token"])
        self.assertFalse(result["ok"], result)
        self.assertEqual("STALE", result["code"])
        self.assertEqual(moved, self.snapshot())
        self.apply([put(modified)])
        self.assertEqual(["b2"], self.surfaces()[1]["obstacles"])
        self.assertEqual([-100, 200], self.relations(self.surfaces()[1])["b2"][2], "q = z - 2600 for z in [2500,2800]")
        deleted = self.apply([{"op": "delete-finish-surface", "id": 1}])
        self.assertEqual([{"id": 1, "change": "deleted"}], deleted["changes"])
        self.assertEqual({}, self.surfaces())
        self.reject([{"op": "delete-finish-surface", "id": 1}], "does not exist")
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(["b2"], self.surfaces()[1]["obstacles"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual({}, self.surfaces())

    def test_deleting_a_referenced_source_is_rejected_until_the_reference_is_removed(self):
        self.apply([put(surface())])
        for line, word in (("delete column 1", "column 1"), ("delete beam 2", "beam 2"),
                           ("delete boundary 4", "boundary 4")):
            with self.subTest(line=line):
                before = self.snapshot()
                result = self.command("line " + line)
                self.assertFalse(result["ok"], result)
                self.assertIn("I55", result["error"])
                self.assertIn(word, result["error"])
                self.assertIn("1", result["error"])
                self.assertEqual(before, self.snapshot())
        # Moving an obstacle is not a deletion: the relation is re-derived from the new AABB.
        self.assertTrue(self.command("line column 1 at 1000 2000 size 300 300 z 0 3000")["ok"])
        self.assertEqual("interior", self.relations(self.surfaces()[1])["c1"][0])
        self.apply([put(surface(obstacles=["b2", "c5"]))])
        self.assertTrue(self.command("line delete column 1")["ok"])
        self.apply([{"op": "delete-finish-surface", "id": 1}])
        self.assertTrue(self.command("line delete boundary 4")["ok"])

    def test_interactive_dsl_cannot_bypass_the_preview(self):
        before = self.snapshot()
        result = self.command("line finish-surface 9 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n "
                              "name-hex 61")
        self.assertFalse(result["ok"], result)
        self.assertIn("panel-fill-preview", result["error"])
        self.assertEqual(before, self.snapshot())

    def test_out_of_scope_operations_are_refused_instead_of_hidden(self):
        # The panel-fill preview only discloses finish surfaces, so it must not commit anything else (I8a/I55):
        # a perfectly valid parameter card would otherwise land in World behind an empty `changes` list.
        valid_card = {"op": "put-parameter", "value": {"id": 9, "name": "板材", "fields": [
            {"id": 1, "name": "寬", "type": "dimension", "input": "915"}]}}
        cases = [([valid_card], []),
                 ([put(surface()), valid_card], [{"id": 1, "change": "created"}]),
                 ([{"op": "set-source", "target": {"kind": "grid", "id": 1, "axis": "u", "field": "gap"},
                    "source": {"kind": "literal", "value": 3}}], [])]
        for operations, candidate_changes in cases:
            with self.subTest(ops=[o["op"] for o in operations]):
                preview = self.reject(operations, "only put-finish-surface and delete-finish-surface")
                self.assertEqual(candidate_changes, preview["changes"], "changes describe the rejected candidate, not a commit")
        self.assertEqual({}, self.surfaces())
        self.assertNotIn("parameters", self.command("dump")["text"])

    def test_tokens_of_other_transaction_kinds_are_refused(self):
        preview = self.preview([put(surface())])
        before = self.snapshot()
        for command in ("engineering-confirm", "section-profile-confirm", "assembly-confirm", "line confirm"):
            with self.subTest(command=command):
                self.assertFalse(self.command("%s %d" % (command, preview["token"]))["ok"])
                self.assertEqual(before, self.snapshot())
        self.assertFalse(self.command("engineering-cancel %d" % preview["token"])["cancelled"])
        self.assertTrue(self.command("panel-fill-confirm %d" % preview["token"])["ok"], "own token still valid")
        self.assertEqual(["c1", "c5", "b2"], self.surfaces()[1]["obstacles"])
        path = self.directory / "engineering.json"
        path.write_text(json.dumps({"schema": "engineering-transaction/1", "expectedRevision": self.read()["revision"],
                                    "operations": [{"op": "put-parameter", "value": {"id": 9, "name": "板材", "fields": [
                                        {"id": 1, "name": "寬", "type": "dimension", "input": "915"}]}}]},
                                   ensure_ascii=False), encoding="utf-8")
        engineering = self.command("engineering-preview " + str(path))["preview"]
        self.assertTrue(engineering["valid"], engineering)
        before = self.snapshot()
        self.assertFalse(self.command("panel-fill-confirm %d" % engineering["token"])["ok"])
        self.assertFalse(self.command("panel-fill-cancel %d" % engineering["token"])["cancelled"])
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command("engineering-cancel %d" % engineering["token"])["cancelled"])

    def test_mid_transaction_failure_commits_nothing(self):
        before = self.snapshot()
        self.reject([put(surface()), put(surface(2, boundary=99))], "I52")
        self.assertEqual({}, self.surfaces(), "the valid first operation must not survive the failed second one")
        self.assertEqual(before, self.snapshot())

    def test_rejected_or_cancelled_previews_keep_redo(self):
        self.apply([put(surface())])
        self.apply([put(surface(origin=(0, 0, 2600)))])
        self.assertTrue(self.command("line undo")["ok"])
        after_undo = self.snapshot()
        self.assertEqual([0, 0, 2480], self.surfaces()[1]["frame"]["origin"])
        self.reject([put(surface(boundary=99))], "I52")
        pending = self.preview([put(surface(obstacles=["b2"]))])
        self.assertFalse(self.command("engineering-confirm %d" % pending["token"])["ok"])
        self.assertTrue(self.command("panel-fill-cancel %d" % pending["token"])["cancelled"])
        self.assertEqual(after_undo, self.snapshot())
        self.assertTrue(self.command("line redo")["ok"], "redo must survive rejected, wrong-kind and cancelled previews")
        self.assertEqual([0, 0, 2600], self.surfaces()[1]["frame"]["origin"])

    # ---- I56 / R4 / R46: save and reopen ----------------------------------------------------------------------
    def test_dump_reopen_round_trip_is_exact(self):
        self.apply([put(surface()), put(surface(2, boundary=3, origin=(0, 3000, 2400), side=-1, v="-Y", n="-Z",
                                                obstacles=[], name="Ceiling B"))])
        text = self.command("dump")["text"]
        lines = text.splitlines()
        requires = [line for line in lines if line.startswith("requires ")]
        self.assertEqual(["requires engineering-spec/1", "requires parameters/1", "requires panel-fill/1"], requires)
        records = [line for line in lines if line.startswith("finish-surface ")]
        self.assertEqual([
            "finish-surface 1 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n obstacles c1 c5 b2 name-hex "
            + "天花完成面".encode("utf-8").hex(),
            "finish-surface 2 on boundary 3 origin 0 3000 2400 u +x v -y n -z side -n name-hex "
            + "Ceiling B".encode("utf-8").hex()], records)
        self.assertGreater(lines.index(records[0]), max(i for i, l in enumerate(lines) if l.startswith("beam ")))
        for derived in ("interior", "touch", "separate", "rect", "outline 0,0 4000,0 4000,1500"):
            self.assertNotIn(derived, "\n".join(records))
        state = self.read()["state"]
        hashed = self.command("dump")
        self.assertTrue(self.command("reset")["ok"])
        reopened = self.load_text(text, "saved.scene")
        self.assertIn("panel-fill/1", reopened["required_capabilities"])
        self.assertEqual(text, self.command("dump")["text"])
        self.assertEqual(state, self.read()["state"])
        self.assertEqual(hashed["definition_sha256"], self.command("dump")["definition_sha256"])

    def test_capabilities_are_declared_but_not_claimed_complete(self):
        self.assertNotIn("panel-fill/1", self.command("dump")["required_capabilities"])
        self.apply([put(surface())])
        dump = self.command("dump")
        self.assertEqual(["engineering-spec/1", "parameters/1", "panel-fill/1"], dump["required_capabilities"])
        self.assertNotIn("panel-fill/1", dump["capabilities"], "I32: PF-1 alone is not complete panel-fill/1")
        self.assertIn("panel-fill-native/1", dump["native_capabilities"])
        read = self.read()
        self.assertEqual(["finish-surface", "panel-fill", "derived-placement"], read["supportedRecords"])
        self.assertFalse(read["complete"])

    def test_reopen_rejects_tampered_or_undeclared_records(self):
        record = ("finish-surface 1 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n obstacles c1 b2 "
                  "name-hex 61\n")
        head = "requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n"
        self.load_fails(BASE + record, "I56")
        self.load_fails(BASE + "requires engineering-spec/1\nrequires panel-fill/1\n" + record, "I56")
        self.load_fails(BASE + "requires parameters/1\nrequires panel-fill/1\n", "I56")
        # Declared only after the record: the record itself is refused, not rescued by the end-of-file check.
        self.load_fails(BASE + "requires engineering-spec/1\nrequires panel-fill/1\n" + record + "requires parameters/1\n",
                        "declared first")
        self.load_fails(BASE + head + record.replace("boundary 4", "boundary 44"), "I52")
        self.load_fails(BASE + head + record.replace("c1", "c11"), "c11")
        self.load_fails(BASE + head + record.replace("u +x v +y n +z", "u +x v +y n -z"), "I1")
        self.load_fails(BASE + head + record.replace("side +n", "side +1"), "finish-surface id on boundary")
        self.load_fails(BASE + head + record + record, "duplicate")
        self.load_fails(head + record + BASE, "I52")
        self.load_fails(BASE + head + record + "panel-fill trial 1\n", "欄位數不對")
        self.load_fails(BASE + head + record + "delete column 1\n", "I55")
        self.load_fails(BASE + head.replace("panel-fill/1", "panel-fill/2") + record, "I32")

    def test_scenes_without_finish_surfaces_keep_their_old_dump(self):
        # Recorded once from the independent PF-0 commit, never regenerated from the bridge under test.
        oracle = json.loads((ROOT / "tests/fixtures/pf1-legacy-dumps.json").read_text(encoding="utf-8"))
        self.assertEqual("444a871c87d78f8a12fd40f8cd79c3e6621ff393", oracle["sourceCommit"])
        for name in ("ceiling-a.scene", "room_full.scene", "_wit_d31_parameters.scene",
                     "_wit_d28_engineering_sources.scene", "_ax_r08_snapshot.scene"):
            with self.subTest(scene=name):
                self.assertTrue(self.command("reset")["ok"])
                result = self.command("loadfile " + str(ROOT / name))
                self.assertTrue(result["ok"], result)
                self.assertNotIn("panel-fill/1", result["required_capabilities"])
                text = self.command("dump")["text"]
                self.assertEqual(oracle["scenes"][name]["dump"].encode("utf-8"), text.encode("utf-8"),
                                 name + ": dump bytes differ from the independent PF-0 fixture")
                self.assertNotIn("panel-fill", text)
                self.assertNotIn("finish-surface", text)
                self.assertEqual([], self.read()["state"]["finishSurfaces"])

    def test_apply_proj_footprint_is_only_contact(self):
        # PF16 (plane part): an obstacle already cut into F by apply-proj has R_k equal to the hole, so it only touches F.
        room = (ROOT / "_ax_r08_snapshot.scene").read_text(encoding="utf-8").replace("delete column 1\n", "")
        self.load_text(room, "applied.scene")
        preview = self.apply([put(surface(1, boundary=1, origin=(0, 0, 2490), obstacles=["c1"]))])
        self.assertEqual("touch", self.relations(self.surfaces(preview["after"])[1])["c1"][0])
        self.assertTrue(preview["valid"])


if __name__ == "__main__":
    unittest.main()
