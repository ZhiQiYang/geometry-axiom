"""definition-import/1 against the authoritative bridge. Skips without a fresh bridge."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests._bridge import BridgeSession, find_bridge


def rule(identifier=1, version=1, name="S框架"):
    return {"id": identifier, "version": version, "name": name,
            "slots": [{"id": 1, "name": "主支"}, {"id": 2, "name": "副支"}],
            "members": [{"id": 1, "slotId": 1}, {"id": 2, "slotId": 1}, {"id": 3, "slotId": 2}],
            "joints": [{"id": 1, "kind": "end-to-side", "scope": "left", "terminatedMember": 3,
                        "targetMember": 1, "end": "start", "side": "+u", "dir": "u"},
                       {"id": 2, "kind": "end-to-side", "scope": "right", "terminatedMember": 3,
                        "targetMember": 2, "end": "finish", "side": "-u", "dir": "u"}]}


def literal(value):
    return {"kind": "literal", "value": value}


def face(source_a, source_b, slot_id=1, complete=True):
    return {"slotId": slot_id, "A": source_a, "B": source_b,
            "contactFace": "A" if complete else None, "orientation": "B" if complete else None}


class DefinitionImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="definition-import-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = BridgeSession(self.bridge, cwd=self.directory)
        self.addCleanup(self.session.stop)
        self.counter = 0
        self.assertTrue(self.command("reset")["ok"])

    def command(self, text):
        return self.session.command(text)

    def engineering(self):
        value = self.command("engineering-read")
        self.assertTrue(value.get("ok"), value)
        return value

    def assembly(self):
        value = self.command("assembly-read")
        self.assertTrue(value.get("ok"), value)
        return value

    def spec(self, name, value):
        result = self.command("line spec %s %s" % (name, value))
        if result.get("preview"):
            self.assertTrue(result["preview"].get("valid"), result)
            result = self.command("line confirm %s" % result["preview"]["token"])
        self.assertTrue(result.get("ok"), result)

    def apply(self, operations):
        revision = self.assembly()["revision"]
        path = self.directory / ("transaction-%d.json" % self.counter)
        self.counter += 1
        path.write_text(json.dumps({"schema": "assembly-transaction/1", "expectedRevision": revision,
                                    "operations": operations}, ensure_ascii=False), encoding="utf-8")
        preview = self.command("assembly-preview " + str(path))
        self.assertTrue(preview.get("ok") and preview.get("preview", {}).get("valid"), preview)
        done = self.command("assembly-confirm %s" % preview["preview"]["token"])
        self.assertTrue(done.get("ok"), done)
        return done

    def material(self, identifier, width, depth, name):
        return {"id": identifier, "version": 1, "kind": "timber", "name": name, "A": width, "B": depth}

    def card(self, identifier, name, text):
        return {"id": identifier, "name": name, "fields": [{"id": 1, "name": "W", "type": "dimension", "input": text}]}

    def binding(self, identifier, rule_id, slots, name="配置"):
        return {"id": identifier, "name": name, "rule": {"id": rule_id, "version": 1}, "slots": slots}

    def build_source(self):
        self.spec("柱寬", 27)
        derived = self.card(1, "S衍生", "=@0:1 + 6 mm")
        self.apply([
            {"op": "publish-rule", "value": rule(1, 1, "S框架")},
            {"op": "publish-material", "value": self.material("sharedwood", 27, 33, "共享")},
            {"op": "publish-material", "value": self.material("otherwood", 45, 90, "另一")},
            {"op": "put-parameter", "value": self.card(0, "S卡", "27")},
            {"op": "put-parameter", "value": derived},
            {"op": "put-binding", "value": self.binding(1, 1, [
                face({"kind": "parameter", "parameterId": 1, "fieldId": 1}, {"kind": "spec", "name": "柱寬"}),
                face({"kind": "material", "id": "sharedwood", "version": 1, "field": "A"},
                     {"kind": "material", "id": "otherwood", "version": 1, "field": "B"}, 2),
            ], "來源配置")},
        ])
        return self.command("dump")["text"]

    def build_target(self):
        self.spec("柱寬", 30)
        self.apply([
            {"op": "publish-rule", "value": rule(1, 1, "目標框架")},
            {"op": "publish-material", "value": self.material("sharedwood", 27, 33, "共享")},
            {"op": "put-parameter", "value": self.card(0, "目標卡", "10")},
            {"op": "put-binding", "value": self.binding(1, 1, [face(literal(27), literal(33)), face(literal(27), literal(33), 2)], "目標配置")},
        ])

    def preview(self, scene, roots, names, revision=None, raw=None, claimed=None):
        payload = raw if raw is not None else scene.encode("utf-8")
        digest = claimed if claimed is not None else hashlib.sha256(payload).hexdigest()
        if revision is None:
            revision = self.engineering()["revision"]
        directory = self.directory / ("import-%d" % self.counter)
        self.counter += 1
        directory.mkdir()
        (directory / "source.scene").write_bytes(payload)
        request = {"schema": "definition-import/1", "expectedRevision": revision,
                   "sourceSceneSha256": digest, "roots": roots, "names": names}
        (directory / "request.json").write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        return self.command("definition-import-preview " + str(directory))

    def confirm(self, preview):
        self.assertTrue(preview.get("ok") and preview.get("preview", {}).get("valid"), preview)
        done = self.command("definition-import-confirm %s" % preview["preview"]["token"])
        self.assertTrue(done.get("ok"), done)
        return done

    def test_reassign_rename_share_and_one_undo(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        self.build_target()
        before = self.command("dump")["text"]
        preview = self.preview(source, {"rules": [], "bindings": [1]}, {"柱寬": {"mode": "rename", "name": "柱寬匯入"}})
        mapping = preview["preview"]["map"]
        self.assertEqual([{"id": 2, "version": 1}], [row["to"] for row in mapping["rules"]])
        self.assertEqual(2, mapping["bindings"][0]["to"])
        self.assertEqual([1, 2], [row["to"] for row in mapping["parameters"]])
        spec_row = next(row for row in mapping["specs"] if row["from"] == "柱寬")
        self.assertEqual("rename", spec_row["action"])
        self.assertEqual("柱寬匯入", spec_row["to"])
        materials = {row["id"]: row["action"] for row in mapping["materials"]}
        self.assertEqual("share", materials["sharedwood"])
        self.assertEqual("create", materials["otherwood"])
        slot = preview["preview"]["bindings"][0]["slots"]
        self.assertEqual(33, slot[0]["A"]["effective"])
        self.assertEqual(27, slot[0]["B"]["effective"])
        self.assertEqual(27, slot[1]["A"]["effective"])
        self.assertEqual(90, slot[1]["B"]["effective"])
        self.confirm(preview)
        after = self.command("dump")["text"]
        self.assertIn("spec 柱寬 30", after)
        self.assertIn("spec 柱寬匯入 27", after)
        undone = self.command("line undo")
        self.assertTrue(undone.get("ok"), undone)
        self.assertEqual(before, self.command("dump")["text"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after, self.command("dump")["text"])
        state = self.engineering()["state"]
        self.assertEqual(1, sum(1 for item in state["materials"] if item and item.get("id") == "sharedwood"))
        self.assertEqual(1, sum(1 for item in state["materials"] if item and item.get("id") == "otherwood"))

    def test_empty_roots_and_instances_are_refused(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        before = self.command("dump")["text"]
        empty = self.preview(source, {"rules": [], "bindings": []}, {})
        self.assertFalse(empty["ok"])
        self.assertIn("匯入根不得是空的", empty["error"])
        instances = self.preview(source, {"rules": [], "bindings": [], "instances": [1]}, {})
        self.assertFalse(instances["ok"])
        self.assertEqual("UNSUPPORTED", instances["code"])
        self.assertEqual(before, self.command("dump")["text"])

    def test_rename_required_has_no_token(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        self.spec("柱寬", 30)
        before = self.command("dump")["text"]
        preview = self.preview(source, {"rules": [], "bindings": [1]}, {})
        self.assertTrue(preview["ok"])
        self.assertFalse(preview["preview"]["valid"])
        self.assertNotIn("token", preview["preview"])
        self.assertIn("IMPORT_RENAME_REQUIRED", json.dumps(preview, ensure_ascii=False))
        self.assertEqual(before, self.command("dump")["text"])

    def test_hash_mismatch_and_stale_revision_write_nothing(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        raw = source.encode("utf-8")
        mismatch = self.preview(source, {"rules": [], "bindings": [1]}, {}, raw=raw + b"\n", claimed=hashlib.sha256(raw).hexdigest())
        self.assertFalse(mismatch["ok"])
        self.assertEqual("INVALID", mismatch["code"])
        self.spec("柱寬", 30)
        preview = self.preview(source, {"rules": [], "bindings": [1]}, {"柱寬": {"mode": "map-existing"}})
        self.spec("ExtraSpec", 1)
        changed = self.command("dump")["text"]
        denied = self.command("definition-import-confirm %s" % preview["preview"]["token"])
        self.assertFalse(denied["ok"])
        self.assertEqual("STALE", denied["code"])
        self.assertEqual(changed, self.command("dump")["text"])

    def test_cancel_and_line_confirm_do_not_publish(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        before = self.command("dump")["text"]
        preview = self.preview(source, {"rules": [{"id": 1, "version": 1}], "bindings": []}, {})
        token = preview["preview"]["token"]
        denied = self.command("line confirm %s" % token)
        self.assertFalse(denied["ok"])
        self.assertEqual(before, self.command("dump")["text"])
        cancelled = self.command("definition-import-cancel %s" % token)
        self.assertTrue(cancelled.get("ok") and cancelled.get("cancelled") is True)
        self.assertFalse(self.command("definition-import-confirm %s" % token)["ok"])
        self.assertEqual(before, self.command("dump")["text"])

    def test_open_preview_blocks_a_second_preview(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        first = self.preview(source, {"rules": [{"id": 1, "version": 1}], "bindings": []}, {})
        second = self.preview(source, {"rules": [{"id": 1, "version": 1}], "bindings": []}, {})
        self.assertFalse(second["ok"])
        self.assertEqual("TOKEN", second["code"])
        self.assertTrue(self.command("definition-import-cancel %s" % first["preview"]["token"])["ok"])

    def test_uint32_wrap_allocates_the_next_free_id(self):
        self.apply([{"op": "publish-rule", "value": rule(7, 1, "來源")}])
        source = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        self.apply([{"op": "publish-rule", "value": rule(1, 1, "已用")}])
        self.apply([{"op": "publish-rule", "value": rule(4294967295, 1, "尾號")}])
        preview = self.preview(source, {"rules": [{"id": 7, "version": 1}], "bindings": []}, {})
        self.assertEqual(2, preview["preview"]["map"]["rules"][0]["to"]["id"])

    def test_two_versions_share_one_new_rule_id(self):
        self.apply([{"op": "publish-rule", "value": rule(1, 1, "第一版")}])
        self.apply([{"op": "publish-rule", "value": rule(1, 2, "第二版")}])
        source = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        self.apply([{"op": "publish-rule", "value": rule(1, 1, "目標")}])
        preview = self.preview(source, {"rules": [{"id": 1, "version": 1}, {"id": 1, "version": 2}], "bindings": []}, {})
        rows = preview["preview"]["map"]["rules"]
        self.assertEqual([(2, 1), (2, 2)], [(row["to"]["id"], row["to"]["version"]) for row in rows])

    def test_null_slot_stays_incomplete(self):
        self.apply([{"op": "publish-rule", "value": rule()},
                    {"op": "put-binding", "value": self.binding(1, 1, [face(None, None, complete=False), face(None, None, 2, False)])}])
        source = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        preview = self.preview(source, {"rules": [], "bindings": [1]}, {})
        slot = preview["preview"]["bindings"][0]["slots"][0]
        self.assertIsNone(slot["A"]["effective"])
        self.assertIsNone(slot["B"]["effective"])

    def test_repeated_import_copies_world_local_ids_and_shares_material(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        self.build_target()
        first = self.preview(source, {"rules": [], "bindings": [1]}, {"柱寬": {"mode": "rename", "name": "柱寬匯入"}})
        self.confirm(first)
        second = self.preview(source, {"rules": [], "bindings": [1]}, {"柱寬": {"mode": "map-existing"}})
        self.assertEqual("share", {row["id"]: row["action"] for row in second["preview"]["map"]["materials"]}["otherwood"])
        self.confirm(second)
        rules = [item["value"]["id"] for item in self.assembly()["state"]["rules"]]
        self.assertEqual([1, 2, 3], sorted(set(rules)))
        state = self.engineering()["state"]
        self.assertEqual(1, sum(1 for item in state["materials"] if item and item.get("id") == "otherwood"))

    def test_empty_target_assigns_from_one_rather_than_keeping_a_high_source_id(self):
        self.apply([{"op": "publish-rule", "value": rule(5, 1, "高號")},
                    {"op": "put-binding", "value": self.binding(4, 5, [face(literal(27), literal(33)), face(literal(27), literal(33), 2)])}])
        source = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        preview = self.preview(source, {"rules": [], "bindings": [4]}, {})
        self.assertEqual(1, preview["preview"]["map"]["rules"][0]["to"]["id"])
        self.assertEqual(1, preview["preview"]["map"]["bindings"][0]["to"])

    def test_unsupported_scene_capability_rejects_the_source(self):
        source = self.build_source()
        rejected = self.preview("requires not-a-capability/1\n" + source, {"rules": [{"id": 1, "version": 1}], "bindings": []}, {})
        self.assertFalse(rejected["ok"])
        self.assertEqual("UNSUPPORTED", rejected["code"])

    def test_save_reopen_keeps_imported_ids(self):
        source = self.build_source()
        self.assertTrue(self.command("reset")["ok"])
        preview = self.preview(source, {"rules": [], "bindings": [1]}, {})
        self.confirm(preview)
        saved = self.command("dump")["text"]
        path = self.directory / "reopen.scene"
        path.write_text(saved, encoding="utf-8")
        with BridgeSession(self.bridge, cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile " + str(path))["ok"])
            self.assertEqual(saved, fresh.command("dump")["text"])


if __name__ == "__main__":
    unittest.main()
