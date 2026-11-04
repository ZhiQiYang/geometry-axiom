"""#360: native witnesses for D59-D61/I70-I72/R56; no JS allocator oracle."""
import base64
import copy
import json
import os
import secrets
import tempfile
import unittest
from pathlib import Path

from tests import _bridge

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = "boundary 1 outline 0,0 4000,0 4000,3000 0,3000"


def card(identifier=9, fields=None):
    return {"op": "put-parameter", "value": {"id": identifier, "name": "Unused",
        "fields": fields or [{"id": 0, "name": "A", "type": "dimension", "input": "1000"},
                            {"id": 1, "name": "B", "type": "dimension", "input": "2000"}]}}


class IdentityLedgerReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Match the native product launcher's 16 MiB stack on POSIX. R13's
        # existing projection workspace is larger than the shell's 8 MiB.
        if os.name != "nt":
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            if soft != resource.RLIM_INFINITY and soft < 16 * 1024 * 1024:
                resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, hard))
        cls.binary = _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r09a-native-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bridge = _bridge.BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.ok("reset")
        self.epoch = secrets.token_hex(16)
        self.ok("identity-epoch " + self.epoch)

    def command(self, command):
        return self.bridge.command(command)

    def ok(self, command):
        result = self.command(command)
        self.assertTrue(result.get("ok"), (command, result))
        return result

    def line(self, line):
        result = self.command("line " + line)
        if result.get("preview", {}).get("valid"):
            result = self.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result.get("ok"), (line, result))
        return result

    def ledger(self):
        return self.ok("identity-read")

    def marks(self):
        return {(m["kind"], m["id"], m.get("fieldId", 0)): m["mark"] for m in self.ledger()["marks"]}

    def dump(self):
        return self.ok("dump")["text"]

    def preview(self, operations, route="engineering"):
        schema = route + "-transaction/1"
        path = self.directory / (route + ".json")
        path.write_text(json.dumps({"schema": schema, "expectedRevision": self.ok("engineering-read")["revision"],
                                    "operations": operations}), encoding="utf-8", newline="\n")
        return self.ok(route + "-preview " + str(path))

    def batch(self, operations, route="engineering"):
        result = self.preview(operations, route)
        self.assertTrue(result["preview"]["valid"], result)
        confirm = "assembly" if route == "assembly-generation" else route
        return self.ok(confirm + "-confirm " + str(result["preview"]["token"]))

    def seed(self, active=True, batch_ready=False):
        self.line(BOUNDARY)
        self.line("placement 0 on boundary 1 origin 0 0 0 u +x v +y")
        self.line("column 2 at 5000 5000 size 100 100 z 0 100")
        self.batch([card(2, [{"id": 0, "name": "A", "type": "dimension", "input": "3200"},
                            {"id": 1, "name": "B", "type": "dimension", "input": "=@2:0/2"}])])
        # S's primary timbers are intentionally unplaced. Batch candidates must
        # also satisfy I9, so the batch witnesses use the same keys/sections as
        # two valid boundary timbers. This never bypasses native validation.
        for ident, edge in ((5, "e0"), (6, "e2")):
            self.line(f"timber {ident} 27 33 role " + ("boundary" if batch_ready else "primary"))
            if batch_ready:
                self.line(f"place {ident} on 0 at-face {edge} +u +n")
        if active:
            self.line("identity-ledger activate")
            expected = [("boundary", 1, 0), ("placement", 0, 0), ("column", 2, 0),
                        ("timber", 5, 0), ("timber", 6, 0), ("parameter", 2, 0),
                        ("parameter-field", 2, 0), ("parameter-field", 2, 1)]
            self.assertEqual({k: self.epoch + ":" + str(i + 1) for i, k in enumerate(expected)}, self.marks(), "L01_FIXED_ORDER")

    def save(self, text, name="saved.scene"):
        path = self.directory / name
        path.write_bytes(text.encode("utf-8"))
        return path

    def test_B1_zero_ids_save_and_reopen_in_a_new_process(self):
        self.seed(False, batch_ready=True)
        self.line("column 0 at 6000 6000 size 100 100 z 0 100")
        self.batch([card(0)])
        self.line("timber 0 27 33 role primary")
        self.line("guide 0 0 v 1/2*edge:e1:u")
        self.line("place 0 on 0 at-line guide 0 +v +n")
        self.line("identity-ledger activate")
        before = self.marks()
        for kind in ("placement", "timber", "column", "parameter", "parameter-field"):
            self.assertIn((kind, 0, 0), before, "B1_ZERO_MARK_EXISTS")
        scene = self.dump()
        with _bridge.BridgeSession(self.binary) as fresh:
            loaded = fresh.command("loadfile " + str(self.save(scene)))
            self.assertTrue(loaded.get("ok"), "B1_ZERO_ID_REOPEN: " + str(loaded))
            self.assertEqual(fresh.command("identity-read")["marks"], self.ledger()["marks"])
            self.assertEqual(fresh.command("dump")["text"], scene)
        self.ok("reset")
        self.ok("identity-epoch " + secrets.token_hex(16))
        self.line("beam 0 along x from 0 to 100 at 0 width 20 depth 20 top 50")
        self.line("identity-ledger activate")
        scene = self.dump()
        with _bridge.BridgeSession(self.binary) as fresh:
            loaded = fresh.command("loadfile " + str(self.save(scene)))
            self.assertTrue(loaded.get("ok"), "B1_ZERO_BEAM_REOPEN: " + str(loaded))
            self.assertEqual(fresh.command("dump")["text"], scene)

    def test_B3_line_noop_receipt_matches_native_undo_active_and_inactive(self):
        for active in (False, True):
            with self.subTest(active=active):
                self.ok("reset")
                self.ok("identity-epoch " + secrets.token_hex(16))
                self.line(BOUNDARY)
                if active:
                    self.line("identity-ledger activate")
                self.line("spec receipt_before 17")
                before = self.dump()
                revision = self.ok("engineering-read")["revision"]
                result = self.ok("line " + BOUNDARY)
                self.assertIs(result.get("history_changed"), False, "B3_NOOP_RECEIPT")
                self.assertEqual(result.get("revision"), revision)
                self.assertEqual(result.get("before_revision"), revision)
                self.line("undo")
                self.assertNotIn("spec receipt_before 17", self.dump(), "B3_UNDO_REAL_STEP")
                self.line("redo")
                self.assertEqual(self.dump(), before)

    def test_B3_drag_noop_receipt_does_not_consume_history(self):
        self.line("surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.line("spec mid 500")
        self.line("guide 1 1 v spec:mid")
        self.line("identity-ledger activate")
        self.line("spec receipt_before 17")
        before = self.dump()
        result = self.command("drag 0 2 500 0")
        self.assertTrue(result.get("ok"), result)
        self.assertIs(result.get("history_changed"), False, "B3_DRAG_NOOP_RECEIPT")
        self.assertEqual(self.dump(), before)
        self.line("undo")
        self.assertNotIn("spec receipt_before 17", self.dump(), "B3_DRAG_UNDO_REAL_STEP")

    def test_S1_whole_replacement_clears_epoch_only_on_success(self):
        self.line(BOUNDARY)
        self.line("identity-ledger activate")
        text = self.dump()
        path = self.save(text)
        for command in ("reset", "default", "loadfile " + str(path)):
            with self.subTest(command=command):
                self.ok("identity-epoch " + secrets.token_hex(16))
                serial = self.ledger()["nextSerial"]
                self.ok(command)
                self.assertFalse(self.ledger()["epochSet"], "S1_REPLACEMENT_EPOCH_UNSET")
                self.assertEqual(self.ledger()["nextSerial"], serial)
        self.ok("identity-epoch " + secrets.token_hex(16))
        state = self.ledger()
        self.assertFalse(self.command("loadfile " + str(path) + ".missing")["ok"])
        self.assertEqual(self.ledger(), state, "S1_FAILED_LOAD_PRESERVES_EPOCH")
        prepared = self.ok("load-prepare " + str(path))
        self.assertEqual(self.ledger(), state, "S1_PREPARE_PRESERVES_EPOCH")
        self.ok("load-cancel " + str(prepared["token"]))
        self.assertEqual(self.ledger(), state, "S1_CANCEL_PRESERVES_EPOCH")
        prepared = self.ok("load-prepare " + str(path))
        self.ok("load-confirm " + str(prepared["token"]))
        self.assertFalse(self.ledger()["epochSet"], "S1_CONFIRM_EPOCH_UNSET")
        self.line("undo")
        self.assertFalse(self.ledger()["epochSet"], "S1_UNDO_MUST_NOT_RESTORE_EPOCH")

    def test_L04_group_order_and_failed_group_keep_consumed_serials(self):
        self.seed(batch_ready=True)
        before = self.dump()
        self.line("history-begin")
        self.line("delete timber 6")
        self.line("timber 6 27 33 role boundary")
        self.line("place 6 on 0 at-face e2 +u +n")
        self.line("history-end")
        self.assertEqual(self.marks()["timber", 6, 0], self.epoch + ":9")
        self.line("undo")
        self.assertEqual(self.dump(), before)
        self.line("history-begin")
        self.line("guide 9 0 v 1/4*edge:e1:u")
        self.line("timber 9 27 33 role primary")
        self.line("place 9 on 0 at-line guide 9 +v +n")
        self.line("guide 7 0 v 1/2*edge:e1:u")
        self.line("timber 7 27 33 role primary")
        self.line("place 7 on 0 at-line guide 7 +v +n")
        marks = self.marks()
        self.assertEqual(marks["timber", 9, 0], self.epoch + ":10", "L04_LINE_ORDER")
        self.assertEqual(marks["timber", 7, 0], self.epoch + ":11")
        self.line("history-end")
        self.line("undo")
        self.assertEqual(self.dump(), before)
        self.assertEqual(self.ledger()["nextSerial"], 12, "L04_NO_SERIAL_RETURN")
        self.line("history-begin")
        self.line("timber 9 27 33 role primary")
        self.assertFalse(self.command("line placement 99 on boundary 999 origin 0 0 0 u +x v +y")["ok"])
        self.assertEqual(self.dump(), before, "P053_FAILED_GROUP_WORLD_ROLLBACK")
        self.assertEqual(self.ledger()["nextSerial"], 13, "P053_GROUP_SERIAL_NOT_RETURNED")

    def test_L07_new_process_restore_no_epoch_old_key_edit_and_new_epoch(self):
        self.seed(batch_ready=True)
        scene, marks = self.dump(), self.ledger()["marks"]
        with _bridge.BridgeSession(self.binary) as fresh:
            loaded = fresh.command("loadfile " + str(self.save(scene)))
            self.assertTrue(loaded.get("ok"), "L07_NEW_PROCESS_REOPEN: " + str(loaded))
            self.assertEqual(fresh.command("identity-read")["marks"], marks)
            self.assertFalse(fresh.command("identity-read")["epochSet"])
            rejected = fresh.line("timber 8 27 33 role primary")
            self.assertFalse(rejected["ok"])
            self.assertIn("未設定配號區段", rejected["error"])
            self.assertEqual(fresh.command("dump")["text"], scene)
            changed = fresh.line("timber 5 27 40 role boundary")
            if changed.get("preview", {}).get("valid"):
                changed = fresh.line("confirm " + str(changed["preview"]["token"]))
            self.assertTrue(changed["ok"], changed)
            self.assertEqual(fresh.command("identity-read")["marks"], marks)
            epoch = secrets.token_hex(16)
            self.assertTrue(fresh.command("identity-epoch " + epoch)["ok"])
            self.assertTrue(fresh.line("timber 8 27 33 role primary")["ok"])
            new = next(m for m in fresh.command("identity-read")["marks"] if m["kind"] == "timber" and m["id"] == 8)
            self.assertEqual(new["mark"], epoch + ":1")
            self.assertFalse(fresh.command("identity-epoch " + self.epoch)["ok"])

    def test_L08_load_rejection_matrix_is_atomic(self):
        self.line(BOUNDARY)
        self.line("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.line("timber 5 27 33 role boundary")
        self.line("place 5 on 1 at-face e0 +u +n")
        self.line("identity-ledger activate")
        scene = self.dump()
        # A legal complete control must reopen before any negative variant.
        # An unplaced primary timber would make I9 reject every variant and
        # could falsely stand in for the identity validation under review.
        with _bridge.BridgeSession(self.binary) as control:
            opened = control.command("loadfile " + str(self.save(scene)))
            self.assertTrue(opened.get("ok"), "L08_VALID_CONTROL_REOPENS: " + str(opened))
            self.assertEqual(control.command("dump")["text"], scene)
            self.assertEqual(control.command("identity-read")["marks"], self.ledger()["marks"])
        line = "identity timber 5 " + self.epoch + ":3\n"
        self.assertEqual(scene.count(line), 1, "L08_CONTROL_HAS_TARGET_MARK")
        variants = {"missing": scene.replace(line, ""),
            "extra": scene + "identity timber 9 " + self.epoch + ":4\n",
            "duplicate-mark": scene.replace(self.epoch + ":3", self.epoch + ":1"),
            "uppercase": scene.replace(self.epoch, "A" * 32),
            "serial-zero": scene.replace(self.epoch + ":3", self.epoch + ":0"),
            "leading-zero": scene.replace(self.epoch + ":3", self.epoch + ":03"),
            "no-requires": scene.replace("requires identity-ledger/1\n", ""),
            "requires-no-marks": "\n".join(row for row in scene.splitlines() if not row.startswith("identity ")) + "\n",
            "scene-activate": scene + "identity-ledger activate\n",
            "duplicate-key": scene + line,
            "boundary-zero": scene + "identity boundary 0 " + self.epoch + ":4\n"}
        state = self.ledger()
        for name, changed in variants.items():
            with self.subTest(name=name):
                self.assertNotEqual(changed, scene, "L08_VARIANT_CHANGES_CONTROL_" + name)
                result = self.command("loadfile " + str(self.save(changed)))
                self.assertFalse(result.get("ok"), "L08_REJECT_" + name)
                diagnostic = {"no-requires": "I72:", "scene-activate": "I71:"}.get(name, "I70:")
                self.assertIn(diagnostic, result.get("error", ""), "L08_IDENTITY_DIAGNOSTIC_" + name)
                self.assertEqual(self.dump(), scene, "L08_ATOMIC_" + name)
                self.assertEqual(self.ledger(), state)
        interactive = self.command("line identity timber 5 " + self.epoch + ":99")
        self.assertFalse(interactive["ok"])
        self.assertIn("I71:", interactive["error"])
        self.assertEqual(self.dump(), scene)

    def rebuild(self, route):
        self.seed(batch_ready=True)
        self.batch([card()])
        baseline = self.marks()
        for key in (("parameter", 9, 0), ("parameter-field", 9, 0), ("parameter-field", 9, 1)):
            self.assertIn(key, baseline, "L21_NATIVE_BATCH_SETTLES_NEW_KEYS_" + route)
        self.assertEqual([baseline[k] for k in (("parameter", 9, 0), ("parameter-field", 9, 0), ("parameter-field", 9, 1))],
                         [self.epoch + ":" + str(i) for i in (9, 10, 11)], "L21_NATIVE_BATCH_SETTLES_NEW_KEYS")
        plain = self.ok("dump-deidentified")["text"]
        revision = self.ok("engineering-read")["revision"]
        noop = self.batch([card()], route)
        self.assertIs(noop["history_changed"], False, "L24_BATCH_REDECLARE_IS_NOOP_" + route)
        self.assertEqual(noop["revision"], revision)
        self.assertEqual(self.marks(), baseline, "L24_CONTINUED_KEYS_KEEP_MARKS_" + route)
        self.assertEqual(self.ledger()["nextSerial"], 12)
        result = self.batch([{"op": "delete-parameter", "id": 9}, card()], route)
        expected = dict(baseline)
        for offset, key in enumerate([("parameter", 9, 0), ("parameter-field", 9, 0), ("parameter-field", 9, 1)], 12):
            expected[key] = self.epoch + ":" + str(offset)
        self.assertEqual(self.marks(), expected, "L21_EXPLICIT_DELETE_" + route)
        self.assertEqual(self.ledger()["nextSerial"], 15, "L21_COMMIT_ALL_NEW_SERIALS_" + route)
        self.assertTrue(result["history_changed"], "L21_MARKS_ARE_CHANGE_" + route)
        self.assertEqual(result["revision"], revision + 1)
        self.assertEqual(self.ok("dump-deidentified")["text"], plain)
        self.line("undo")
        self.assertEqual(self.marks(), baseline)

    def test_L21_engineering_same_key_rebuild(self):
        self.rebuild("engineering")

    def test_L21_assembly_same_key_rebuild(self):
        self.rebuild("assembly")

    def test_L21_generation_same_key_rebuild(self):
        self.rebuild("assembly-generation")

    def test_L21_section_same_key_rebuild(self):
        self.rebuild("section-profile")

    def test_L10_L21_parameter_import_reuses_id_but_not_mark(self):
        self.seed(batch_ready=True)
        self.batch([card(0)])
        exported = copy.deepcopy(next(c for c in self.ok("engineering-read")["state"]["parameters"] if c["id"] == 0))
        for field in exported["fields"]:
            field.pop("value")
        package = {"schema": "geometry-parameters/1", "cards": [exported]}
        self.assertNotIn("identity", json.dumps(package))
        before = self.marks()
        self.batch([{"op": "delete-parameter", "id": 0}, {"op": "import-parameters", "value": package}])
        after = self.marks()
        for key in (("parameter", 0, 0), ("parameter-field", 0, 0), ("parameter-field", 0, 1)):
            self.assertNotEqual(after[key], before[key], "L21_IMPORT_REBUILT_KEY")
        for key in before.keys() - {("parameter", 0, 0), ("parameter-field", 0, 0), ("parameter-field", 0, 1)}:
            self.assertEqual(after[key], before[key])

    def test_L16_activation_expires_every_candidate_route(self):
        for route in ("engineering", "assembly", "assembly-generation", "section-profile"):
            with self.subTest(route=route):
                self.ok("reset")
                self.ok("identity-epoch " + secrets.token_hex(16))
                preview = self.preview([card()], route)
                self.assertTrue(preview["preview"]["valid"], preview)
                self.line("identity-ledger activate")
                before = self.dump(), self.ledger()
                confirm = "assembly" if route == "assembly-generation" else route
                result = self.command(confirm + "-confirm " + str(preview["preview"]["token"]))
                self.assertFalse(result["ok"], "L16_STALE_" + route)
                self.assertEqual((self.dump(), self.ledger()), before)
                self.batch([card()], route)
                self.assertIn(("parameter", 9, 0), self.marks())
        for route in ("interactive", "load"):
            with self.subTest(route=route):
                self.ok("reset")
                self.ok("identity-epoch " + secrets.token_hex(16))
                if route == "interactive":
                    preview = self.ok("line preview " + BOUNDARY)["preview"]
                    command = "line confirm " + str(preview["token"])
                else:
                    preview = self.ok("load-prepare " + str(self.save(BOUNDARY + "\n")))
                    command = "load-confirm " + str(preview["token"])
                self.line("identity-ledger activate")
                before = self.dump(), self.ledger()
                result = self.command(command)
                self.assertFalse(result["ok"], "L16_STALE_" + route)
                self.assertEqual((self.dump(), self.ledger()), before)
                if route == "interactive":
                    fresh = self.ok("line preview " + BOUNDARY)["preview"]
                    self.ok("line confirm " + str(fresh["token"]))
                    self.assertIn(("boundary", 1, 0), self.marks(), "L16_FRESH_INTERACTIVE_SETTLES")
                else:
                    fresh = self.ok("load-prepare " + str(self.save(BOUNDARY + "\n")))
                    self.ok("load-confirm " + str(fresh["token"]))
                    self.assertIn(BOUNDARY, self.dump(), "L16_FRESH_LOAD_CONFIRMS")

    def test_L11_projection_split_preserves_retained_and_reattached_marks(self):
        for line in (ROOT / "_ax_r13_anchor_follows.scene").read_text(encoding="utf-8").splitlines():
            if line.startswith(("surface ", "space ")):
                self.line(line)
        self.line("boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 3300,500 3800,500 3800,800 3300,800 hole 3300,2200 3800,2200 3800,2500 3300,2500")
        self.line("beam 1 in 1 along y from 0 to 3000 at 2800 width 300 depth 500")
        self.line("spec split_anchor 3500")
        self.line("guide 1 1 v spec:split_anchor")
        self.line("timber 1 27 33 role primary")
        self.line("place 1 on 1 at-line guide 1 between h0e2 h1e0 +v +n")
        self.line("identity-ledger activate")
        before, scene = self.marks(), self.dump()
        original = next(t for t in self.ok("references")["timbers"] if t["id"] == 1)["geometry"]
        self.line("apply-proj 1 b1 cut-strip")
        after = self.marks()
        for key, mark in before.items():
            self.assertEqual(after[key], mark, "L11_RETAINED_AND_REATTACHED_MARK")
        fresh = after.keys() - before.keys()
        self.assertTrue(fresh, "L11_NEW_SPLIT_OBJECTS_EXIST")
        self.assertEqual({key[0] for key in fresh}, {"boundary", "placement"})
        self.assertTrue(set(after[k] for k in fresh).isdisjoint(before.values()), "L11_NEW_FRAGMENT_NEW_MARK")
        moved = next(t for t in self.ok("references")["timbers"] if t["id"] == 1)["geometry"]
        self.assertNotEqual(moved["surface"], original["surface"], "L11_R13_CHANGED_HOST")
        self.assertEqual(moved["origin"], original["origin"])
        self.assertEqual(moved["length"], 1400)
        self.line("undo")
        self.assertEqual(self.dump(), scene)

    def test_L12_native_fingerprints_ignore_activation(self):
        self.seed(False, batch_ready=True)
        graph = self.ok("source-inspect")
        self.assertTrue(graph["complete"])
        nodes = {n["key"]: (n["definitionFingerprint"], n["valueFingerprint"]) for n in graph["nodes"]}
        dumped = self.ok("dump")
        boundaries = self.ok("boundary 1")
        references = self.ok("references")
        self.line("identity-ledger activate")
        current = self.ok("source-inspect")
        self.assertEqual({n["key"]: (n["definitionFingerprint"], n["valueFingerprint"]) for n in current["nodes"]}, nodes, "L12_CONTENT_FINGERPRINTS")
        self.assertEqual(current["sourceFingerprint"], graph["sourceFingerprint"])
        self.assertEqual(self.ok("references")["sourceFingerprint"], references["sourceFingerprint"])
        self.assertEqual(self.ok("boundary 1"), boundaries, "L12_GEOMETRY_HASH")
        plain = self.ok("dump-deidentified")
        self.assertEqual(plain["text"], dumped["text"])
        self.assertEqual(plain["definition_sha256"], dumped["definition_sha256"], "L12_ENG_DEFINITION_HASH")
    def seed_derived(self):
        from tests.test_panel_fill_layout import fill
        from tests.test_panel_fill_finish_surface import surface, put
        self.line(BOUNDARY)
        self.batch([{"op": "publish-material", "value": {"id": "pf-board", "version": 1, "name": "Board",
            "kind": "panel", "width": 915, "length": 1830, "thickness": "9"}},
            card(90, [{"id": 1, "name": "threshold", "type": "dimension", "input": "8"}])])
        self.batch([put(surface(boundary=1, origin=(0, 0, 0), obstacles=[])), fill(gap=0),
            {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 30}}], "panel-fill")
        self.line("identity-ledger activate")

    def test_S2_derived_placement_covered_and_cold_reopened(self):
        self.seed_derived()
        self.assertIn(("placement", 10, 0), self.marks(), "S2_DERIVED_COVERED")
        before = self.marks()
        self.batch([{"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 31}}], "panel-fill")
        self.assertEqual(self.marks(), before, "S2_REDECLARE_CONTINUES")
        scene = self.dump()
        with _bridge.BridgeSession(self.binary) as fresh:
            result = fresh.command("loadfile " + str(self.save(scene)))
            self.assertTrue(result["ok"], result)
            self.assertEqual(fresh.command("identity-read")["marks"], self.ledger()["marks"])
            self.assertEqual(fresh.command("dump")["text"], scene)

    def test_S2_derived_explicit_delete_rebuild_is_new_incarnation(self):
        self.seed_derived()
        before = self.marks()
        self.assertIn(("placement", 10, 0), before, "S2_DERIVED_COVERED")
        plain = self.ok("dump-deidentified")["text"]
        result = self.batch([{"op": "delete-derived-placement", "id": 10},
            {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 30}}], "panel-fill")
        after = self.marks()
        self.assertNotEqual(after["placement", 10, 0], before["placement", 10, 0], "S2_DERIVED_EXPLICIT_DELETE")
        self.assertTrue(result["history_changed"])
        self.assertEqual(self.ok("dump-deidentified")["text"], plain)
        self.line("undo")
        self.assertEqual(self.marks(), before)

    def test_L19_generated_owned_timbers_have_no_marks(self):
        from tests.test_assembly_generation import Generation
        case = Generation()
        self.addCleanup(case.doCleanups)
        case.setUp()
        case.command("identity-epoch " + secrets.token_hex(16))
        case.line("identity-ledger activate")
        initial = case.command("identity-read")
        case.apply([case.create()])
        self.assertEqual(case.command("identity-read"), initial, "L19_OWNED_EXCLUDED")
        instance = case.instance()
        ids = {m["timberId"] for m in instance["members"]}
        self.assertEqual(len(ids), 3)
        for mark in case.command("identity-read")["marks"]:
            self.assertFalse(mark["kind"] == "timber" and mark["id"] in ids)
        for node in case.command("source-inspect")["nodes"]:
            if node["key"] in {"timber:" + str(i) for i in ids}:
                self.assertIsNone(node["incarnation"], "L19_OWNED_NODE_IS_UNCOVERED")
        for identifier in ids:
            self.assertNotIn("identity timber " + str(identifier) + " ", case.dump())
        case.apply([{"op": "delete-instance", "id": 1, "expectedFingerprint": instance["fingerprint"]}, case.create()])
        self.assertEqual(case.command("identity-read"), initial)
        instance = case.instance()
        self.assertEqual({m["timberId"] for m in instance["members"]}, ids, "L19_OWNED_BATCH_REUSES_IDS")
        case.apply([{"op": "delete-instance", "id": 1, "expectedFingerprint": instance["fingerprint"]}])
        ordinary = min(ids)
        case.line(f"timber {ordinary} 27 33 role primary")
        old = next(m["mark"] for m in case.command("identity-read")["marks"] if m["kind"] == "timber" and m["id"] == ordinary)
        case.line("delete timber " + str(ordinary))
        case.apply([case.create()])
        self.assertIn(ordinary, {m["timberId"] for m in case.instance()["members"]}, "L19_ORDINARY_ID_NOW_OWNED")
        self.assertNotIn(old, {m["mark"] for m in case.command("identity-read")["marks"]}, "L19_OLD_INCARNATION_ENDED")
        node = next(n for n in case.command("source-inspect")["nodes"] if n["key"] == "timber:" + str(ordinary))
        self.assertIsNone(node["incarnation"])
        self.assertNotIn("identity timber " + str(ordinary) + " ", case.dump())

    def test_L23_host_gate_runtime_is_pure_and_not_epoch_based(self):
        self.seed()
        before = self.dump(), self.ledger(), self.ok("engineering-read")["revision"]
        for line in ("timber 8 27 33 role primary", "delete timber 5", "reset", "move 1 spec:x",
                     "preview timber 8 27 33", "confirm 1", "history-begin", "identity-ledger activate"):
            result = self.ok("host-gate-check desktop " + line)
            self.assertTrue(result["rejected"], "L23_DESKTOP_GUARD")
            self.assertFalse(self.ok("host-gate-check none " + line)["rejected"], "L23_NONE_GUARD")
        for line in ("undo", "redo"):
            self.assertFalse(self.ok("host-gate-check desktop " + line)["rejected"], "L23_HISTORY_EXEMPT")
        self.assertEqual((self.dump(), self.ledger(), self.ok("engineering-read")["revision"]), before)
        self.ok("loadfile " + str(self.save(BOUNDARY + "\n")))
        self.assertFalse(self.ok("host-gate-check desktop timber 8 27 33")["rejected"], "L23_INACTIVE_WRITABLE")
        self.line("undo")
        self.assertTrue(self.ok("host-gate-check desktop timber 8 27 33")["rejected"])


if __name__ == "__main__":
    unittest.main()
