"""Authoring acceptance against the actual native bridge and scene loader."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests._bridge import BridgeSession, find_bridge


def rule(identifier=1, version=1):
    return {"id": identifier, "version": version, "name": "主副支交接",
            "slots": [{"id": 1, "name": "主支"}, {"id": 2, "name": "副支"}],
            "members": [{"id": 1, "slotId": 1}, {"id": 2, "slotId": 1}, {"id": 3, "slotId": 2}],
            "joints": [{"id": 1, "kind": "end-to-side", "scope": "left", "terminatedMember": 3,
                        "targetMember": 1, "end": "start", "side": "+u", "dir": "u"},
                       {"id": 2, "kind": "end-to-side", "scope": "right", "terminatedMember": 3,
                        "targetMember": 2, "end": "finish", "side": "-u", "dir": "u"}]}


def literal(n):
    return {"kind": "literal", "value": n}


def binding(complete=True, identifier=1, version=1):
    return {"id": identifier, "name": "角材組合", "rule": {"id": 1, "version": version},
            "slots": [{"slotId": i, "A": literal(27) if complete else None,
                       "B": literal(33) if complete else None,
                       "contactFace": "A" if complete else None, "orientation": "B" if complete else None}
                      for i in (1, 2)]}


class AssemblyRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="assembly-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = BridgeSession(self.bridge, cwd=self.directory)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])

    def command(self, value):
        return self.session.command(value)

    def read(self):
        value = self.command("assembly-read")
        self.assertTrue(value.get("ok"), value)
        self.assertIn("state", value)
        return value

    def request(self, ops, revision=None):
        if revision is None:
            revision = self.read()["revision"]
        path = self.directory / "transaction.json"
        path.write_text(json.dumps({"schema": "assembly-transaction/1", "expectedRevision": revision,
                                    "operations": ops}, ensure_ascii=False), encoding="utf-8")
        return self.command("assembly-preview " + str(path))

    def apply(self, ops):
        result = self.request(ops)
        self.assertTrue(result.get("ok"), result)
        self.assertTrue(result["preview"]["valid"], result)
        done = self.command(f'assembly-confirm {result["preview"]["token"]}')
        self.assertTrue(done.get("ok"), done)
        return done

    def publish(self, value=None):
        return self.apply([{"op": "publish-rule", "value": value or rule()}])

    def reject(self, operations, reason):
        before = self.command("dump")["text"], self.read()["revision"]
        result = self.request(operations)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["preview"]["valid"], result)
        self.assertIn(reason, json.dumps(result, ensure_ascii=False))
        self.assertFalse(self.command(f'assembly-confirm {result["preview"]["token"]}')["ok"])
        self.assertEqual(before, (self.command("dump")["text"], self.read()["revision"]))

    def test_publish_without_geometry_and_native_identity(self):
        self.publish()
        state = self.read()["state"]
        self.assertEqual(rule(), state["rules"][0]["value"])
        self.assertEqual([], self.command("objects")["timbers"])
        self.assertEqual([], self.command("surfaces")["surfaces"])
        self.assertEqual(1, self.command("objects")["assemblyRules"][0]["id"])
        self.assertEqual(2, self.command("newid")["assemblyRule"])

    def test_duplicate_scope_and_endpoint_rejected(self):
        for change in ("scope", "end"):
            value = rule(); value["joints"][1][change] = value["joints"][0][change]
            self.reject([{"op": "publish-rule", "value": value}], "joints 1 and 2")

    def test_missing_duplicate_and_unknown_fields_rejected(self):
        variants = []
        value=rule();value["members"][1]["id"]=1;variants.append(value)
        value=rule();value["members"][0]["slotId"]=99;variants.append(value)
        value=rule();value["joints"][0]["targetMember"]=99;variants.append(value)
        value=rule();value["joints"][0]["kind"]="nested-rule";variants.append(value)
        value=rule();value["joints"][0]["side"]="mouse-left";variants.append(value)
        value=rule();value["slots"][0]["unexpected"]=1;variants.append(value)
        for value in variants:
            with self.subTest(value=value):self.reject([{"op":"publish-rule","value":value}],"I40")

    def test_orthogonal_split_and_geometric_loop(self):
        value=rule();value["joints"]=[{"id":1,"kind":"ortho-split","scope":"cross","continuousMember":1,"splitMembers":[2,3],"side":"+u","dir":"v"}]
        self.publish(value)
        value=rule(2);value["members"].append({"id":4,"slotId":2})
        value["joints"]=[{"id":i,"kind":"end-to-side","scope":str(i),"terminatedMember":i,"targetMember":i%4+1,"end":"finish","side":"+u","dir":"v"} for i in range(1,5)]
        self.publish(value)
        self.assertEqual(2,len(self.read()["state"]["rules"]))

    def test_immutable_version_rename_reorder_and_fixed_binding(self):
        self.publish();self.apply([{"op":"put-binding","value":binding()}])
        changed=rule();changed["name"]="重新命名"
        self.reject([{"op":"publish-rule","value":changed}],"immutable")
        changed["version"]=2;changed["slots"].reverse();changed["members"].reverse();self.publish(changed)
        state=self.read()["state"]
        self.assertEqual(1,state["bindings"][0]["value"]["rule"]["version"])
        self.assertEqual(rule()["joints"],state["rules"][1]["value"]["joints"])

    def test_copy_and_idempotent_publication(self):
        self.publish();done=self.publish();self.assertFalse(done["history_changed"])
        self.apply([{"op":"copy-rule","id":1,"version":1,"newId":2}])
        copies=self.read()["state"]["rules"]
        self.assertEqual([1,2],[r["value"]["id"] for r in copies])
        self.assertEqual(copies[0]["value"]["joints"],copies[1]["value"]["joints"])

    def test_unselected_binding_is_saved_as_incomplete(self):
        self.publish();self.apply([{"op":"put-binding","value":binding(False)}])
        self.assertFalse(self.read()["state"]["bindings"][0]["complete"])
        self.assertIsNone(self.read()["state"]["bindings"][0]["effective"][0]["A"])

    def test_material_source_and_parameter_recomputation(self):
        self.publish()
        material={"id":"pine","version":1,"kind":"timber","name":"松木","A":27,"B":33}
        param={"id":1,"name":"截面","fields":[{"id":1,"name":"A","type":"dimension","input":"40"}]}
        b=binding();b["slots"][0]["A"]={"kind":"parameter","parameterId":1,"fieldId":1}
        b["slots"][0]["B"]={"kind":"material","id":"pine","version":1,"field":"B"}
        self.apply([{"op":"publish-material","value":material},{"op":"put-parameter","value":param},{"op":"put-binding","value":b}])
        self.assertEqual(40,self.read()["state"]["bindings"][0]["effective"][0]["A"]["value"])
        param["fields"][0]["input"]="50";self.apply([{"op":"put-parameter","value":param}])
        self.assertEqual(50,self.read()["state"]["bindings"][0]["effective"][0]["A"]["value"])
        self.reject([{"op":"delete-parameter","id":1}],"binding 1 slot 1.A")
        self.apply([{"op":"delete-binding","id":1},{"op":"delete-parameter","id":1}])
        self.assertEqual([],self.read()["state"]["bindings"])

    def test_bad_dimension_sources_rejected_not_incomplete(self):
        self.publish()
        for source in [literal(0),literal(-1),{"kind":"material","id":"missing","version":1,"field":"A"},
                       {"kind":"parameter","parameterId":99,"fieldId":1},{"kind":"application","id":"x","field":"primary.A"}]:
            b=binding();b["slots"][0]["A"]=source
            self.reject([{"op":"put-binding","value":b}],"binding 1 slot 1.A")

    def test_referenced_rule_delete_and_atomic_rebind(self):
        self.publish();self.publish(rule(version=2));self.apply([{"op":"put-binding","value":binding()}])
        self.reject([{"op":"delete-rule","id":1,"version":1}],"missing rule 1@1")
        self.apply([{"op":"put-binding","value":binding(version=2)},{"op":"delete-rule","id":1,"version":1}])
        self.assertEqual([2],[r["value"]["version"] for r in self.read()["state"]["rules"]])
        after=self.command("dump")["text"]
        self.assertTrue(self.command("line undo")["ok"])
        restored=self.read()["state"]
        self.assertEqual([1,2],[r["value"]["version"] for r in restored["rules"]])
        self.assertEqual(1,restored["bindings"][0]["value"]["rule"]["version"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after,self.command("dump")["text"])

    def test_cancel_and_protocol_tokens_do_not_commit(self):
        r=self.request([{"op":"publish-rule","value":rule()}]);token=r["preview"]["token"]
        self.assertFalse(self.command(f"engineering-confirm {token}")["ok"])
        self.assertFalse(self.command(f"engineering-cancel {token}")["cancelled"])
        self.assertTrue(self.command(f"assembly-cancel {token}")["cancelled"])
        self.assertFalse(self.command(f"assembly-confirm {token}")["ok"])
        self.assertEqual([],self.read()["state"]["rules"])

    def test_stale_preview_and_wrong_revision(self):
        r=self.request([{"op":"publish-rule","value":rule()}]);revision=self.read()["revision"]
        self.assertTrue(self.command("line spec changed 10")["ok"])
        self.assertFalse(self.command(f'assembly-confirm {r["preview"]["token"]}')["ok"])
        self.assertEqual("STALE",self.request([{"op":"publish-rule","value":rule()}],revision)["code"])

    def test_canvas_move_preserves_preview_and_history(self):
        self.publish();r=self.request([{"op":"put-binding","value":binding()}])
        self.assertTrue(self.command("line canvas-pos assembly-rule 1 17 -8")["ok"])
        self.assertTrue(self.command(f'assembly-confirm {r["preview"]["token"]}')["ok"])
        self.assertTrue(self.command("line undo")["ok"]);self.assertEqual([],self.read()["state"]["bindings"])
        self.assertTrue(self.command("line redo")["ok"]);self.assertEqual(1,len(self.read()["state"]["bindings"]))
        self.assertIn("canvas-pos assembly-rule 1 17 -8",self.command("dump")["text"])

    def test_scene_roundtrip_in_fresh_process(self):
        self.publish();self.publish(rule(version=2));self.apply([{"op":"put-binding","value":binding(False)}])
        before=self.command("dump")["text"];path=self.directory/"saved.scene";path.write_text(before,encoding="utf-8")
        self.assertTrue(all(len(line.encode())<16384 for line in before.splitlines()))
        with BridgeSession(self.bridge,cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile "+str(path))["ok"])
            self.assertEqual(before,fresh.command("dump")["text"])
            self.assertEqual(self.read()["state"],fresh.command("assembly-read")["state"])

    def test_truncated_corrupt_and_duplicate_records_are_atomic(self):
        self.publish();before=self.command("dump")["text"]
        variants=[before.replace("assembly end\n",""),before.replace("assembly commit\n",""),before.replace("assembly data ","assembly data !",1),before+before]
        for text in variants:
            path=self.directory/"bad.scene";path.write_text(text,encoding="utf-8")
            self.assertFalse(self.command("loadfile "+str(path))["ok"])
            self.assertEqual(before,self.command("dump")["text"])
        self.assertFalse(self.command("line assembly begin")["ok"])

    def test_binding_slot_and_face_contract(self):
        self.publish()
        for change in ("missing","duplicate","face"):
            b=binding()
            if change=="missing":b["slots"].pop()
            elif change=="duplicate":b["slots"][1]["slotId"]=1
            else:b["slots"][0]["contactFace"]="screen-left"
            self.reject([{"op":"put-binding","value":b}],"I40")

    def test_parameter_preview_includes_assembly_consumers(self):
        self.publish()
        param={"id":1,"name":"尺寸","fields":[{"id":1,"name":"A","type":"dimension","input":"27"}]}
        b=binding();b["slots"][0]["A"]={"kind":"parameter","parameterId":1,"fieldId":1}
        self.apply([{"op":"put-parameter","value":param},{"op":"put-binding","value":b}])
        uses=self.command("objects")["parameterUses"]
        self.assertTrue(any(u["kind"]=="assembly-binding" and u["id"]==1 for u in uses))
        param["fields"][0]["input"]="29"
        path=self.directory/"engineering.json"
        path.write_text(json.dumps({"schema":"engineering-transaction/1","expectedRevision":self.read()["revision"],"operations":[{"op":"put-parameter","value":param}]}),encoding="utf-8")
        preview=self.command("engineering-preview "+str(path))["preview"]
        self.assertTrue(preview["valid"])
        self.assertEqual(27,preview["before"]["assembly"]["bindings"][0]["effective"][0]["A"]["value"])
        self.assertEqual(29,preview["after"]["assembly"]["bindings"][0]["effective"][0]["A"]["value"])
        self.assertEqual(27,self.read()["state"]["bindings"][0]["effective"][0]["A"]["value"])

    def test_wrong_typed_fractional_sources_and_legacy_delete_reject(self):
        self.publish()
        self.apply([{"op":"put-parameter","value":{"id":1,"name":"數量","fields":[{"id":1,"name":"件數","type":"count","input":"27"}]} }])
        b=binding();b["slots"][0]["A"]={"kind":"parameter","parameterId":1,"fieldId":1}
        self.reject([{"op":"put-binding","value":b}],"binding 1 slot 1.A")
        self.assertTrue(self.command("line spec SectionA 27")["ok"])
        b["slots"][0]["A"]={"kind":"spec","name":"SectionA"};self.apply([{"op":"put-binding","value":b}])
        before=self.command("dump")["text"]
        self.assertFalse(self.command("line delete spec SectionA")["ok"])
        self.assertFalse(self.command("line spec SectionA 0")["ok"])
        self.assertEqual(before,self.command("dump")["text"])
        preview=self.command("line spec SectionA 29")["preview"]
        self.assertTrue(preview["valid"])
        self.assertEqual(27,preview["assembly"]["before"]["bindings"][0]["effective"][0]["A"]["value"])
        self.assertEqual(29,preview["assembly"]["after"]["bindings"][0]["effective"][0]["A"]["value"])
        self.assertEqual(before,self.command("dump")["text"])
        self.assertTrue(self.command("line confirm "+str(preview["token"]))["ok"])

    def test_authoring_capability_does_not_enable_model_generation(self):
        sys.path.insert(0,str(ROOT/"geometry-core"))
        from modeling.base import load_base
        from modeling import ModelError
        self.publish();scene=self.command("dump")["text"]
        for value in [scene,scene.replace("requires assembly-rule-authoring/1\n","")]:
            with self.assertRaises(ModelError) as caught:load_base(value)
            self.assertEqual("UNSUPPORTED",caught.exception.status)
            self.assertEqual("CAPABILITY",caught.exception.code)


if __name__ == "__main__":
    unittest.main()
