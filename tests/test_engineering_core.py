"""Real C bridge acceptance for engineering-spec/1 (no browser evaluator)."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402


class EngineeringCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-eng-case-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = _bridge.BridgeSession(self.exe)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])
        self.assertTrue(self.command("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")["ok"])

    def command(self, command):
        return self.session.command(command)

    def read(self):
        result = self.command("engineering-read")
        self.assertTrue(result["ok"], result)
        return result

    def request(self, operations, revision=None):
        data = {"schema": "engineering-transaction/1", "expectedRevision": self.read()["revision"] if revision is None else revision, "operations": operations}
        path = self.directory / "request.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return self.command("engineering-preview " + str(path))

    def apply(self, operations):
        result = self.request(operations)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["preview"]["valid"], result)
        confirmed = self.command("engineering-confirm " + str(result["preview"]["token"]))
        self.assertTrue(confirmed["ok"], confirmed)
        return result, confirmed

    def apply_line(self, line):
        result = self.command("line " + line)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = self.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], result)
        return result

    def seed(self):
        material = {"id": "panel-a", "version": 1, "kind": "panel", "name": "面材", "width": 915, "length": 1830, "thickness": "6.50", "notes": None}
        method = {"id": "method-a", "version": 1, "name": "做法", "panel": {"id": "panel-a", "version": 1}, "gap": 3, "longAxis": "v", "mainAlong": "u"}
        app = {"id": "application-a", "placement_id": 1, "method": {"id": "method-a", "version": 1}, "overrides": {}, "anchorOptions": {"u": {"kind": "coordinate", "value": 0}, "v": {"kind": "coordinate", "value": 0}}}
        return [
            {"op": "publish-material", "value": material},
            {"op": "publish-method", "value": method},
            {"op": "put-application", "value": app},
            {"op": "bind-grid", "id": 1, "application": "application-a", "create": True},
        ]

    def test_preview_commit_sources_and_single_undo(self):
        before = self.command("dump")["text"]
        operations = self.seed()
        preview = self.request(operations)
        self.assertTrue(preview["preview"]["valid"], preview)
        self.assertEqual(before, self.command("dump")["text"])
        grid = preview["preview"]["after"]["geometry"]["grids"][0]
        self.assertEqual([916, 1834, 2752, 3670], grid["u"])
        self.assertEqual([1831], grid["v"])
        token = preview["preview"]["token"]
        self.assertTrue(self.command(f"engineering-confirm {token}")["history_changed"])
        state = self.read()["state"]
        # D28: equal numeric caches are not evidence that the requested
        # application references survived. Check identities from the input,
        # independently of dump/readback and of the engine's resolved path.
        expected_sources = [
            {"target": {"kind": "grid", "id": 1, "axis": axis, "field": field},
             "source": {"kind": "application", "id": "application-a", "field": axis + "." + field},
             "override": None, "effective": value}
            for axis, field, value in (("u", "panel", 915), ("u", "gap", 3),
                                       ("v", "panel", 1830), ("v", "gap", 3))
        ]
        by_target = lambda binding: json.dumps(binding["target"], sort_keys=True)
        self.assertEqual(sorted(expected_sources, key=by_target),
                         sorted([{k: source[k] for k in ("target", "source", "override", "effective")}
                                 for source in state["sources"]], key=by_target))
        expected = hashlib.sha256(json.dumps(operations[0]["value"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(expected, state["materials"][0]["fingerprint"])
        self.assertEqual("6.50", state["materials"][0]["thickness"])
        after = self.command("dump")["text"]
        self.assertIn("requires engineering-spec/1", after)
        self.assertIn("engineering grid ", after)
        self.assertNotIn("grid 1 on 1", after)
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before, self.command("dump")["text"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after, self.command("dump")["text"])

    def test_roundtrip_fingerprints_validate_is_readonly(self):
        self.apply(self.seed())
        before = self.command("dump")
        pending = self.request([{"op": "archive", "kind": "material", "id": "panel-a", "version": 1, "value": True}])
        scene = self.directory / "saved.scene"
        scene.write_text(before["text"], encoding="utf-8")
        validated = self.command("engineering-validate " + str(scene))
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(["engineering-spec/1"], validated["required_capabilities"])
        self.assertEqual(before["revision"], self.read()["revision"])
        self.assertTrue(self.command("engineering-confirm " + str(pending["preview"]["token"]))["ok"])
        self.assertTrue(self.command("loadfile " + str(scene))["ok"])
        self.assertEqual(before["text"], self.command("dump")["text"])

    def test_supplied_fingerprints_are_recomputed_and_failed_import_is_atomic(self):
        """D26/I34: a well-formed external hash is not trusted content proof."""
        value = {"id": "minimal-panel", "version": 1, "kind": "panel", "name": "面材", "width": 915, "length": 1830}
        fingerprint = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        before = self.read()
        before_dump = self.command("dump")
        poisoned = self.request([
            {"op": "publish-material", "value": {"id": "would-leak", "version": 1, "kind": "timber", "name": "角材", "A": 27, "B": 33}},
            {"op": "publish-material", "value": value, "fingerprint": "0" * 64},
        ])
        self.assertFalse(poisoned["preview"]["valid"], poisoned)
        self.assertFalse(self.command("engineering-confirm " + str(poisoned["preview"]["token"]))["ok"])
        self.assertEqual(before, self.read())
        self.assertEqual(before_dump, self.command("dump"))
        self.apply([{"op": "publish-material", "value": value, "fingerprint": fingerprint}])
        self.assertEqual([dict(value, fingerprint=fingerprint, archived=False)], self.read()["state"]["materials"])
        saved = self.command("dump")["text"]
        record_line = next(line for line in saved.splitlines() if line.startswith("engineering material "))
        record = json.loads(base64.b64decode(record_line.split()[2], validate=True))
        self.assertEqual({"value": value, "fingerprint": fingerprint}, record)
        self.assertNotIn("thickness", record["value"], "omitted optional content must not be silently normalized to null")
        record["fingerprint"] = "0" * 64
        encoded = base64.b64encode(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).decode()
        scene = self.directory / "forged-fingerprint.scene"
        scene.write_text(saved.replace(record_line, "engineering material " + encoded), encoding="utf-8")
        self.apply_line("spec keep_world 59")
        before = self.read()
        before_dump = self.command("dump")
        self.assertFalse(self.command("loadfile " + str(scene))["ok"])
        self.assertEqual(before, self.read())
        self.assertEqual(before_dump, self.command("dump"))

    def test_versions_overrides_and_restore(self):
        self.apply(self.seed())
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        self.apply([{"op": "set-override", "target": target, "value": {"kind": "literal", "value": 1000}}])
        self.assertEqual(1000, self.command("references")["grids"][0]["uDefinition"]["panel"])
        self.apply([{"op": "set-override", "target": target, "value": None}])
        self.assertEqual(915, self.command("references")["grids"][0]["uDefinition"]["panel"])
        conflict = copy.deepcopy(self.seed()[0]); conflict["value"]["width"] = 910
        baseline = self.command("dump")["text"]
        result = self.request([conflict])
        self.assertFalse(result["preview"]["valid"])
        self.assertFalse(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
        self.assertEqual(baseline, self.command("dump")["text"])
        _, idem = self.apply([self.seed()[0]])
        self.assertFalse(idem["history_changed"])

    def test_atomic_failure_stale_revision_and_cancel_token(self):
        first = self.request(self.seed())
        second = self.request(self.seed())
        self.assertFalse(self.command("engineering-cancel " + str(first["preview"]["token"]))["cancelled"])
        self.assertTrue(self.command("engineering-confirm " + str(second["preview"]["token"]))["ok"])
        revision = self.read()["revision"]
        operations = [{"op": "archive", "kind": "material", "id": "panel-a", "version": 1, "value": True}]
        staged = self.request(operations)
        self.assertTrue(self.command("line spec unrelated 7")["ok"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertFalse(self.command("engineering-confirm " + str(staged["preview"]["token"]))["ok"])
        self.assertEqual("STALE", self.request(operations, revision)["code"])
        baseline = self.command("dump")["text"]
        failed = self.request(operations + [{"op": "bind-grid", "id": 2, "application": "missing", "create": True}])
        self.assertFalse(failed["preview"]["valid"])
        self.assertEqual(baseline, self.command("dump")["text"])

    def test_rejected_and_cancelled_candidates_preserve_undo_and_redo(self):
        """I8/I35: read-only candidate evaluation must preserve both stacks."""
        self.apply(self.seed())
        original = self.command("dump")["text"]
        self.apply_line("spec history_marker 71")
        redo_world = self.command("dump")["text"]
        self.apply_line("undo")
        self.assertEqual(original, self.command("dump")["text"])
        for kind in ("invalid", "cancelled"):
            with self.subTest(candidate=kind):
                before = self.read()
                operations = [{"op": "archive", "kind": "material", "id": "panel-a", "version": 1, "value": True}]
                if kind == "invalid":
                    operations.append({"op": "bind-grid", "id": 2, "application": "missing", "create": True})
                candidate = self.request(operations)["preview"]
                self.assertEqual(kind == "cancelled", candidate["valid"])
                if kind == "cancelled":
                    self.assertTrue(self.command("engineering-cancel " + str(candidate["token"]))["cancelled"])
                self.assertFalse(self.command("engineering-confirm " + str(candidate["token"]))["ok"])
                self.assertEqual(before, self.read(), "failure/cancel must not change definitions or revision")
                self.assertEqual(original, self.command("dump")["text"])
                self.apply_line("redo")
                self.assertEqual(redo_world, self.command("dump")["text"], "candidate discarded the pre-existing redo entry")
                self.apply_line("undo")
                self.assertEqual(original, self.command("dump")["text"])
        # Also prove failure did not append a no-op undo entry over the seed.
        self.apply_line("undo")
        self.assertEqual([], self.read()["state"]["materials"])
        self.assertEqual([], self.command("references")["grids"])

    def test_fixed_versions_face_and_object_overrides_preserve_concrete_anchors(self):
        """D26-D28/R31: upgrades are explicit and each override is reversible."""
        initial = self.seed()
        initial[-1]["anchors"] = {"u": 100, "v": 200}
        self.apply(initial)
        old_material = copy.deepcopy(initial[0]["value"])
        new_material = dict(old_material, version=2, width=800, length=1600)
        new_method = copy.deepcopy(initial[1]["value"])
        new_method.update(version=2, panel={"id": "panel-a", "version": 2}, gap=8)
        self.apply([{"op": "publish-material", "value": new_material},
                    {"op": "publish-method", "value": new_method}])
        grid = self.command("references")["grids"][0]
        self.assertEqual((915, 1830, 3), (grid["uDefinition"]["panel"], grid["vDefinition"]["panel"], grid["uDefinition"]["gap"]))
        self.assertEqual({"id": "method-a", "version": 1}, self.read()["state"]["applications"][0]["method"])
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "gap"}
        object_override = {"kind": "literal", "value": 7}
        self.apply([{"op": "set-override", "target": target, "value": object_override}])
        upgraded = copy.deepcopy(initial[2]["value"])
        upgraded.update(method={"id": "method-a", "version": 2},
                        overrides={"gap": {"kind": "literal", "value": 5}},
                        anchorOptions={"u": {"kind": "coordinate", "value": 500},
                                       "v": {"kind": "coordinate", "value": 600}})
        self.apply([{"op": "put-application", "value": upgraded},
                    {"op": "bind-grid", "id": 1, "application": "application-a"}])
        grid = self.command("references")["grids"][0]
        self.assertEqual((800, 1600, 7, 5), (grid["uDefinition"]["panel"], grid["vDefinition"]["panel"], grid["uDefinition"]["gap"], grid["vDefinition"]["gap"]))
        self.assertEqual((100, 200), (grid["uDefinition"]["anchor"], grid["vDefinition"]["anchor"]))
        # floor(gap/2) is applied once: 100+800+3 and 200+1600+2.
        self.assertEqual([903, 1710, 2517, 3324], grid["u"])
        self.assertEqual([1802], grid["v"])
        binding = next(x for x in self.read()["state"]["sources"] if x["target"] == target)
        self.assertEqual({"kind": "application", "id": "application-a", "field": "u.gap"}, binding["source"])
        self.assertEqual(object_override, binding["override"])
        self.apply([{"op": "set-override", "target": target, "value": None}])
        self.assertEqual(5, self.command("references")["grids"][0]["uDefinition"]["gap"])
        upgraded["overrides"] = {}
        self.apply([{"op": "put-application", "value": upgraded}])
        self.assertEqual(8, self.command("references")["grids"][0]["uDefinition"]["gap"])
        self.apply([{"op": "archive", "kind": "material", "id": "panel-a", "version": 2, "value": True},
                    {"op": "archive", "kind": "method", "id": "method-a", "version": 2, "value": True}])
        expected_materials = [dict(value, fingerprint=hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), archived=value["version"] == 2)
                              for value in (old_material, new_material)]
        self.assertEqual(expected_materials, self.read()["state"]["materials"])
        scene = self.directory / "all-versions.scene"
        scene.write_text(self.command("dump")["text"], encoding="utf-8")
        self.apply_line("reset")
        self.assertTrue(self.command("loadfile " + str(scene))["ok"])
        self.assertEqual(expected_materials, self.read()["state"]["materials"], "unused and archived versions must also survive replay")
        self.assertEqual({"id": "method-a", "version": 2}, self.read()["state"]["applications"][0]["method"])
        self.assertEqual((100, 200), tuple(self.command("references")["grids"][0][axis + "Definition"]["anchor"] for axis in ("u", "v")))

    def test_named_source_recomputes_and_legacy_edit_cannot_flatten(self):
        self.apply(self.seed())
        self.assertTrue(self.command("line spec panelWidth 915")["ok"])
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        self.apply([{"op": "set-source", "target": target, "source": {"kind": "spec", "name": "panelWidth"}}])
        before = self.command("dump")["text"]
        preview = self.command("line spec panelWidth 910")
        self.assertTrue(preview["preview"]["valid"], preview)
        self.assertEqual(before, self.command("dump")["text"])
        self.assertTrue(self.command("line confirm " + str(preview["preview"]["token"]))["ok"])
        self.assertEqual(910, self.command("references")["grids"][0]["uDefinition"]["panel"])
        rejected = self.command("line grid 1 on 1 u panel 1000 gap 0 from 0")
        self.assertFalse(rejected["ok"])
        self.assertIn("engineering", rejected["error"])
        self.assertEqual(4, len(self.command("references")["engineeringSources"]))

    def test_bound_timber_rebuilds_downstream_and_roundtrips(self):
        self.assertTrue(self.command("default")["ok"])
        operations = [
            {"op": "publish-material", "value": {"id": "wood-a", "version": 1, "kind": "timber", "name": "邊界材", "A": 30, "B": 33}},
            {"op": "publish-method", "value": {"id": "framing", "version": 1, "name": "骨架", "roles": {"boundary": {"id": "wood-a", "version": 1}}}},
            {"op": "put-application", "value": {"id": "frame-face", "placement_id": 1, "method": {"id": "framing", "version": 1}}},
            {"op": "bind-timber", "id": 1, "application": "frame-face", "slot": "boundary"},
            {"op": "bind-timber", "id": 2, "application": "frame-face", "slot": "boundary"},
        ]
        before = self.command("references")["timbers"]
        self.assertEqual(2946, next(x for x in before if x["id"] == 3)["geometry"]["length"])
        self.apply(operations)
        timbers = self.command("references")["timbers"]
        self.assertEqual(30, next(x for x in timbers if x["id"] == 1)["geometry"]["A"])
        self.assertEqual(2940, next(x for x in timbers if x["id"] == 3)["geometry"]["length"])
        self.assertEqual("primary", next(x for x in timbers if x["id"] == 3)["role"])
        text = self.command("dump")["text"]
        self.assertIn("engineering timber ", text)
        scene = self.directory / "timber.scene"
        scene.write_text(text, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(scene))["ok"])
        self.assertEqual(text, self.command("dump")["text"])
        invalid = self.request([{"op": "bind-timber", "id": 3, "application": "frame-face", "slot": "boundary"}])
        self.assertFalse(invalid["preview"]["valid"])
        self.assertEqual(text, self.command("dump")["text"])

    def test_subgrid_lock_and_canvas_position_exception(self):
        self.apply(self.seed())
        self.assertTrue(self.command("line subgrid 2 parent 1 cell u line:0 line:1 v min line:0 divisions u 2 v 1")["ok"])
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        baseline = self.command("dump")["text"]
        failed = self.request([{"op": "set-override", "target": target, "value": {"kind": "literal", "value": 2000}}])
        self.assertFalse(failed["preview"]["valid"])
        self.assertEqual(baseline, self.command("dump")["text"])
        pending = self.request([{"op": "archive", "kind": "material", "id": "panel-a", "version": 1, "value": True}])
        self.assertTrue(self.command("line canvas-pos boundary 1 400 700")["ok"])
        self.assertTrue(self.command("engineering-confirm " + str(pending["preview"]["token"]))["ok"])
        self.assertIn("canvas-pos boundary 1 400 700", self.command("dump")["text"])

    def test_multiface_downstream_failure_rolls_back_every_target_and_one_undo(self):
        """I35/R31: the last face's indivisible child rejects the first too."""
        self.apply(self.seed())
        self.apply_line("surface 2 origin 0 0 5000 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        first_app = copy.deepcopy(self.seed()[2]["value"])
        second_app = dict(copy.deepcopy(first_app), id="application-b", placement_id=2)
        self.apply([{"op": "put-application", "value": second_app},
                    {"op": "bind-grid", "id": 3, "application": "application-b", "create": True}])
        for child, parent in ((2, 1), (4, 3)):
            self.apply_line(f"subgrid {child} parent {parent} cell u line:0 line:1 v min line:0 divisions u 2 v 1")
        before, before_read, before_refs = self.command("dump"), self.read(), self.command("references")
        first_app["overrides"] = {"gap": {"kind": "literal", "value": 5}}
        second_app["overrides"] = {"gap": {"kind": "literal", "value": 4}}
        operations = [{"op": "put-application", "value": app} for app in (first_app, second_app)]
        # Face 1 would have span 915+5=920 (divisible by 2). Face 2
        # would have 915+4=919: no integer child midpoint exists.
        invalid = self.request(operations)["preview"]
        self.assertFalse(invalid["valid"], invalid)
        self.assertTrue(invalid["violations"], invalid)
        self.assertFalse(self.command("engineering-confirm " + str(invalid["token"]))["ok"])
        self.assertEqual(before, self.command("dump"))
        self.assertEqual(before_read, self.read())
        self.assertEqual(before_refs, self.command("references"))
        second_app["overrides"]["gap"]["value"] = 5
        preview = self.request(operations)["preview"]
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.command("dump"), "even a valid batch is still preview-only")
        grids = {grid["id"]: grid for grid in preview["after"]["geometry"]["grids"]}
        for parent in (1, 3):
            self.assertEqual([917, 1837, 2757, 3677], grids[parent]["u"])
        for child in (2, 4):
            self.assertEqual([1377], grids[child]["u"])
        self.assertTrue(self.command("engineering-confirm " + str(preview["token"]))["history_changed"])
        after = self.command("dump")["text"]
        grids = {grid["id"]: grid for grid in self.command("references")["grids"]}
        for parent in (1, 3):
            self.assertEqual([917, 1837, 2757, 3677], grids[parent]["u"])
        for child in (2, 4):
            self.assertEqual([1377], grids[child]["u"])
        self.assertEqual({1, 2, 3, 4}, set(grids), "neither dependent child may be silently dropped")
        self.apply_line("undo")
        self.assertEqual(before["text"], self.command("dump")["text"])
        self.assertEqual(before_refs, self.command("references"))
        self.apply_line("redo")
        self.assertEqual(after, self.command("dump")["text"])

    def test_owned_definition_delete_undo_reused_id_and_failure_are_atomic(self):
        self.apply(self.seed())
        self.apply_line("subgrid 2 parent 1 cell u line:0 line:1 v min line:0 divisions u 2 v 1")
        before = self.command("dump")["text"]
        failed = self.command("line delete grid 1")
        self.assertFalse(failed["ok"])
        self.assertFalse(failed["preview"]["valid"])
        self.assertEqual(before, self.command("dump")["text"])
        self.apply_line("delete grid 2")
        before = self.command("dump")["text"]
        self.apply_line("delete grid 1")
        self.assertEqual([], self.read()["state"]["sources"])
        self.assertEqual(1, len(self.read()["state"]["applications"]))
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.apply_line("redo")
        self.apply_line("grid 1 on 1 u panel 1000 gap 0 from 0")
        self.assertEqual([], self.read()["state"]["sources"])
        self.apply_line("delete grid 1")
        self.apply_line("delete placement 1")
        self.assertEqual([], self.read()["state"]["applications"])
        self.assertEqual(1, len(self.read()["state"]["materials"]))
        self.apply_line("undo")
        self.assertEqual(1, len(self.read()["state"]["applications"]))
        self.apply_line("redo")
        self.apply_line("delete boundary 1")
        self.apply_line("surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.assertEqual([], self.read()["state"]["applications"])

    def test_bound_timber_delete_cleans_only_own_sources(self):
        self.assertTrue(self.command("default")["ok"])
        self.apply([{"op":"set-source","target":{"kind":"timber","id":3,"field":"A"},"source":{"kind":"literal","value":27}}])
        before = self.command("dump")["text"]
        self.apply_line("delete timber 3")
        self.assertEqual([], self.read()["state"]["sources"])
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.apply_line("redo")
        self.apply_line("timber 3 27 33 role primary")
        self.assertEqual([], self.read()["state"]["sources"])

    def split_room(self):
        self.apply_line("reset")
        for line in (ROOT / "_ax_r13_anchor_follows.scene").read_text(encoding="utf-8").splitlines():
            if line.startswith(("surface ", "space ")):
                self.apply_line(line)
        self.apply_line("beam 1 in 1 along y from 0 to 3000 at 2800 width 300 depth 500")

    def test_r13_application_follows_intact_source_identity(self):
        for anchor, should_move in ((0, False), (3300, True)):
            with self.subTest(anchor=anchor):
                self.split_room()
                operations = self.seed()
                operations[2]["value"]["anchorOptions"]["u"]["value"] = anchor
                self.apply(operations)
                before = self.command("dump")["text"]
                sources = self.read()["state"]["sources"]
                self.apply_line("apply-proj 1 b1 cut-strip")
                refs = self.command("references")
                grid = refs["grids"][0]
                app = self.read()["state"]["applications"][0]
                self.assertEqual(1, grid["id"])
                self.assertEqual(should_move, grid["surface"] != 1)
                self.assertEqual(grid["surface"], app["placement_id"])
                self.assertEqual(anchor, grid["uDefinition"]["anchor"])
                self.assertEqual(sources, self.read()["state"]["sources"])
                after = self.command("dump")["text"]
                scene = self.directory / "split.scene"
                scene.write_text(after, encoding="utf-8")
                self.assertTrue(self.command("engineering-validate " + str(scene))["ok"])
                self.apply_line("undo")
                self.assertEqual(before, self.command("dump")["text"])
                self.apply_line("redo")
                self.assertEqual(after, self.command("dump")["text"])

    def test_unused_face_override_and_hidden_bad_source_rejected(self):
        operations = self.seed()[:3]
        operations[2]["value"]["overrides"] = {"primary.A":{"kind":"spec","name":"missing"}}
        self.assertFalse(self.request(operations)["preview"]["valid"])
        self.apply(self.seed())
        target = {"kind":"grid","id":1,"axis":"u","field":"panel"}
        bad = self.request([
            {"op":"set-source","target":target,"source":{"kind":"material","id":"panel-a","version":99,"field":"width"}},
            {"op":"set-override","target":target,"value":{"kind":"literal","value":1000}},
        ])
        self.assertFalse(bad["preview"]["valid"])

    def test_r13_direct_material_source_moves_without_rewriting_application(self):
        self.split_room()
        operations = self.seed()
        operations[2]["value"]["anchorOptions"]["u"]["value"] = 3300
        for axis, field in (("u", "width"), ("v", "length")):
            operations += [
                {"op":"set-source","target":{"kind":"grid","id":1,"axis":axis,"field":"panel"},"source":{"kind":"material","id":"panel-a","version":1,"field":field}},
                {"op":"set-source","target":{"kind":"grid","id":1,"axis":axis,"field":"gap"},"source":{"kind":"literal","value":3}},
            ]
        self.apply(operations)
        sources = self.read()["state"]["sources"]
        self.apply_line("apply-proj 1 b1 cut-strip")
        self.assertNotEqual(1, self.command("references")["grids"][0]["surface"])
        self.assertEqual(1, self.read()["state"]["applications"][0]["placement_id"])
        self.assertEqual(sources, self.read()["state"]["sources"])

    def test_r13_application_cannot_implicitly_clone_across_fragments(self):
        self.split_room()
        self.apply_line("timber 10 27 33 role boundary")
        self.apply_line("place 10 on 1 at-face e3 +v +n")
        operations = self.seed()
        operations[2]["value"]["anchorOptions"]["u"]["value"] = 3300
        operations[2]["value"]["overrides"] = {"boundary.A":{"kind":"literal","value":27},"boundary.B":{"kind":"literal","value":33}}
        operations.append({"op":"bind-timber","id":10,"application":"application-a","slot":"boundary"})
        self.apply(operations)
        before = self.command("dump")["text"]
        result = self.command("line apply-proj 1 b1 cut-strip")
        self.assertFalse(result["preview"]["valid"], result)
        self.assertIn("one application", json.dumps(result))
        self.assertEqual(before, self.command("dump")["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
