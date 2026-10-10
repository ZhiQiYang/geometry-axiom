"""Authoring acceptance against the actual native bridge and scene loader."""
from copy import deepcopy
import hashlib
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

    def test_rule_cards_expose_exact_latest_native_definition_fingerprints(self):
        values = [rule(77, 1), rule(77, 3), rule(77, 2), rule(78, 1)]
        values[1]["joints"][0]["side"] = "-u"
        for value in values:
            self.publish(value)
        for identifier in (77, 78):
            self.assertTrue(self.command(f"line canvas-pos assembly-rule {identifier} 17 -8")["ok"])
        before = self.command("dump")["text"], self.read()["revision"]
        cards = self.command("objects")["assemblyRules"]
        self.assertEqual({(77, 3), (78, 1)}, {(c["id"], c["version"]) for c in cards})
        records = {(r["value"]["id"], r["value"]["version"]): r for r in self.read()["state"]["rules"]}
        for card in cards:
            self.assertIn("fingerprint", card)
            record = records[card["id"], card["version"]]
            canonical = json.dumps(record["value"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), card["fingerprint"])
            self.assertEqual(record["fingerprint"], card["fingerprint"])
        self.assertEqual(cards[0]["name"], cards[1]["name"])
        self.assertNotEqual(cards[0]["fingerprint"], cards[1]["fingerprint"])
        self.assertEqual(before, (self.command("dump")["text"], self.read()["revision"]))

    def test_rule_card_fingerprint_detects_same_tuple_replacement(self):
        self.publish()
        self.assertTrue(self.command("line canvas-pos assembly-rule 1 17 -8")["ok"])
        original = self.command("objects")["assemblyRules"][0]
        self.assertIn("fingerprint", original)
        self.apply([{"op": "delete-rule", "id": 1, "version": 1}])
        replacement = rule()
        replacement["joints"][0]["side"] = "-u"
        self.publish(replacement)
        self.assertTrue(self.command("line canvas-pos assembly-rule 1 17 -8")["ok"])
        changed = self.command("objects")["assemblyRules"][0]
        self.assertIn("fingerprint", changed)
        self.assertEqual({k: v for k, v in original.items() if k != "fingerprint"},
                         {k: v for k, v in changed.items() if k != "fingerprint"})
        canonical = json.dumps(replacement, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), changed["fingerprint"])
        self.assertEqual(self.read()["state"]["rules"][0]["fingerprint"], changed["fingerprint"])
        self.assertNotEqual(original["fingerprint"], changed["fingerprint"])

    def test_rule_card_fingerprint_reads_and_moves_preserve_pending_preview(self):
        self.publish()
        original = self.command("objects")["assemblyRules"][0]
        self.assertIn("fingerprint", original)
        preview = self.request([{"op": "create-binding", "value": binding(False)}])["preview"]
        self.assertTrue(preview["valid"])
        before = self.command("dump")["text"], self.read()["revision"]
        self.assertEqual(original, self.command("objects")["assemblyRules"][0])
        self.assertEqual(before, (self.command("dump")["text"], self.read()["revision"]))
        self.assertTrue(self.command("line canvas-pos assembly-rule 1 -21 34")["ok"])
        moved = self.command("objects")["assemblyRules"][0]
        self.assertEqual(original["fingerprint"], moved["fingerprint"])
        self.assertNotEqual(original, moved)
        self.assertEqual(before[1], self.read()["revision"])
        self.assertTrue(self.command(f'assembly-confirm {preview["token"]}')["ok"])
        self.assertEqual(binding(False), self.read()["state"]["bindings"][0]["value"])

    def test_explicit_create_rejects_live_id_including_identical_content(self):
        self.publish();self.apply([{"op":"create-binding","value":binding()}])
        for value in [binding(),dict(binding(),name="must not overwrite")]:
            self.reject([{"op":"create-binding","value":value}],"already exists")

    def test_explicit_edit_uses_native_definition_fingerprint_and_shared_history(self):
        import hashlib
        self.publish();self.apply([{"op":"create-binding","value":binding()}])
        original=self.read()["state"]["bindings"][0]
        canonical=json.dumps(original["value"],ensure_ascii=False,sort_keys=True,separators=(",",":"))
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),original["fingerprint"])
        edited=dict(binding(),name="explicit edit")
        operation={"op":"edit-binding","id":1,"expectedFingerprint":original["fingerprint"],"value":edited}
        preview=self.request([operation])["preview"]
        self.assertTrue(preview["valid"]);self.assertEqual(original,self.read()["state"]["bindings"][0])
        self.assertTrue(self.command(f'assembly-confirm {preview["token"]}')["ok"])
        self.assertEqual(edited,self.read()["state"]["bindings"][0]["value"])
        self.assertTrue(self.command("line undo")["ok"]);self.assertEqual(original,self.read()["state"]["bindings"][0])
        self.assertTrue(self.command("line redo")["ok"]);self.assertEqual(edited,self.read()["state"]["bindings"][0]["value"])
        # Canonical native fingerprints ignore JSON object key order.
        reordered=dict(reversed(list(edited.items())))
        current=self.read()["state"]["bindings"][0]
        self.apply([{"op":"edit-binding","id":1,"expectedFingerprint":current["fingerprint"],"value":reordered}])
        self.assertEqual(current,self.read()["state"]["bindings"][0])

    def test_stale_explicit_edit_rejects_even_with_current_revision(self):
        self.publish();self.apply([{"op":"create-binding","value":binding()}])
        fingerprint=self.read()["state"]["bindings"][0]["fingerprint"]
        self.apply([{"op":"put-binding","value":dict(binding(),name="new source")}])
        self.reject([{"op":"edit-binding","id":1,"expectedFingerprint":fingerprint,"value":binding()}],"STALE")
        self.apply([{"op":"delete-binding","id":1}])
        self.reject([{"op":"edit-binding","id":1,"expectedFingerprint":fingerprint,"value":binding()}],"does not exist")

    def test_explicit_edit_rejects_malformed_or_mismatched_identity_atomically(self):
        self.publish();self.apply([{"op":"create-binding","value":binding()}])
        fingerprint=self.read()["state"]["bindings"][0]["fingerprint"]
        operation={"op":"edit-binding","id":1,"expectedFingerprint":fingerprint,"value":binding()}
        for value in [dict(operation,id=2),dict(operation,value=binding(identifier=2)),
                      dict(operation,expectedFingerprint="not-a-hash"),dict(operation,expectedFingerprint="g"*64),
                      dict(operation,extra=1)]:
            self.reject([value],"I40")

    def test_guarded_operations_validate_candidate_order_without_partial_commit(self):
        self.publish()
        self.reject([{"op":"create-binding","value":binding()},{"op":"create-binding","value":binding()}],"already exists")
        self.apply([{"op":"create-binding","value":binding()}])
        fingerprint=self.read()["state"]["bindings"][0]["fingerprint"]
        self.reject([{"op":"put-binding","value":dict(binding(),name="candidate change")},
                     {"op":"edit-binding","id":1,"expectedFingerprint":fingerprint,"value":binding()}],"STALE")

    def test_guarded_edit_cancel_and_stale_confirmation_leave_world_unchanged(self):
        self.publish();self.apply([{"op":"create-binding","value":binding()}])
        original=self.read()["state"]
        operation={"op":"edit-binding","id":1,"expectedFingerprint":original["bindings"][0]["fingerprint"],"value":dict(binding(),name="preview only")}
        preview=self.request([operation])["preview"]
        self.assertTrue(self.command(f'assembly-cancel {preview["token"]}')["cancelled"])
        self.assertFalse(self.command(f'assembly-confirm {preview["token"]}')["ok"]);self.assertEqual(original,self.read()["state"])
        preview=self.request([operation])["preview"]
        self.apply([{"op":"put-binding","value":dict(binding(),name="committed other edit")}])
        before=self.command("dump")["text"]
        self.assertFalse(self.command(f'assembly-confirm {preview["token"]}')["ok"]);self.assertEqual(before,self.command("dump")["text"])

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

    def test_newid_wraps_past_max_in_independent_assembly_namespaces(self):
        for identifier in (1, 2, 4, 0xffffffff):
            self.publish(rule(identifier=identifier))
        for identifier in (2, 3, 0xffffffff):
            self.apply([{"op": "put-binding", "value": binding(identifier=identifier)}])
        before = self.read()["state"]
        allocated = self.command("newid")
        self.assertEqual(3, allocated["assemblyRule"])
        self.assertEqual(1, allocated["assemblyBinding"])
        self.assertEqual(before, self.read()["state"], "Allocation must not reserve by mutating World")
        self.publish(rule(identifier=allocated["assemblyRule"]))
        self.apply([{"op": "put-binding", "value": binding(identifier=allocated["assemblyBinding"])}])
        after = self.read()["state"]
        self.assertEqual(before["rules"], after["rules"][:-1])
        self.assertEqual(before["bindings"], after["bindings"][:-1])

    def test_copy_and_idempotent_publication(self):
        self.publish();done=self.publish();self.assertFalse(done["history_changed"])
        self.apply([{"op":"copy-rule","id":1,"version":1,"newId":2}])
        copies=self.read()["state"]["rules"]
        self.assertEqual([1,2],[r["value"]["id"] for r in copies])
        self.assertEqual(copies[0]["value"]["joints"],copies[1]["value"]["joints"])

    def test_same_transaction_delete_republish_cannot_change_fixed_version(self):
        self.apply([{"op":"publish-rule","value":rule()},{"op":"put-binding","value":binding()}])
        before = self.read(), self.command("dump")["text"]
        changed=rule();changed["name"]="Different content under old identity"
        changed["joints"][0]["side"]="-u"
        self.reject([{"op":"publish-rule","value":changed}],"D32: published rule 1@1 is immutable")
        self.reject([{"op":"delete-rule","id":1,"version":1}],"missing rule 1@1")
        self.reject([{"op":"delete-rule","id":1,"version":1},
                     {"op":"publish-rule","value":changed}],"D32: published rule 1@1 is immutable")
        self.assertEqual(before,(self.read(),self.command("dump")["text"]))
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual([],self.read()["state"]["rules"])
        self.assertEqual([],self.read()["state"]["bindings"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(before[0]["state"],self.read()["state"])
        self.assertEqual(before[1],self.command("dump")["text"])

    def test_unreferenced_delete_republish_also_preserves_immutable_identity(self):
        self.publish()
        changed=rule();changed["joints"][0]["side"]="-u"
        self.reject([{"op":"delete-rule","id":1,"version":1},
                     {"op":"publish-rule","value":changed}],"D32: published rule 1@1 is immutable")

    def test_delete_copy_cannot_replace_published_identity(self):
        self.publish();other=rule(2);other["name"]="Different rule"
        self.publish(other)
        self.reject([{"op":"delete-rule","id":1,"version":1},
                     {"op":"copy-rule","id":2,"version":1,"newId":1}],"D32: published rule 1@1 is immutable")

    def test_intermediate_identity_replacement_is_rejected_before_later_restore(self):
        self.publish()
        changed=rule();changed["name"]="Intermediate replacement"
        self.reject([{"op":"delete-rule","id":1,"version":1},
                     {"op":"publish-rule","value":changed},
                     {"op":"delete-rule","id":1,"version":1},
                     {"op":"publish-rule","value":rule()}],"D32: published rule 1@1 is immutable")

    def test_identical_delete_republish_has_no_revision_or_history_change(self):
        self.apply([{"op":"publish-rule","value":rule()},{"op":"put-binding","value":binding()}])
        before=self.read(),self.command("dump")["text"]
        done=self.apply([{"op":"delete-rule","id":1,"version":1},
                         {"op":"publish-rule","value":rule()}])
        self.assertFalse(done["history_changed"])
        self.assertEqual(before,(self.read(),self.command("dump")["text"]))
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual([],self.read()["state"]["rules"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(before[0]["state"],self.read()["state"])

    def test_atomic_new_version_rebind_delete_cancels_and_commits(self):
        self.apply([{"op":"publish-rule","value":rule()},{"op":"put-binding","value":binding()}])
        before=self.read(),self.command("dump")["text"]
        changed=rule(version=2);changed["joints"][0]["side"]="-u"
        operations=[{"op":"publish-rule","value":changed},
                    {"op":"put-binding","value":binding(version=2)},
                    {"op":"delete-rule","id":1,"version":1}]
        preview=self.request(operations)["preview"]
        self.assertTrue(preview["valid"])
        self.assertTrue(self.command("assembly-cancel "+str(preview["token"]))["cancelled"])
        self.assertFalse(self.command("assembly-confirm "+str(preview["token"]))["ok"])
        self.assertEqual(before,(self.read(),self.command("dump")["text"]))
        self.assertTrue(self.apply(operations)["history_changed"])
        after=self.read()["state"],self.command("dump")["text"]
        self.assertEqual([2],[r["value"]["version"] for r in after[0]["rules"]])
        self.assertEqual(2,after[0]["bindings"][0]["value"]["rule"]["version"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before[0]["state"],self.read()["state"])
        self.assertEqual(before[1],self.command("dump")["text"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after,(self.read()["state"],self.command("dump")["text"]))

    def test_unselected_binding_is_saved_as_incomplete(self):
        self.publish();self.apply([{"op":"put-binding","value":binding(False)}])
        self.assertFalse(self.read()["state"]["bindings"][0]["complete"])
        self.assertIsNone(self.read()["state"]["bindings"][0]["effective"][0]["A"])

        # A12: selecting dimensions does not silently choose a face/orientation.
        material={"id":"cedar","version":1,"kind":"timber","name":"杉木","A":13,"B":19}
        self.apply([{"op":"publish-material","value":material}])
        expected_effective=[{"slotId":1,"A":{"value":27,"path":"explicit integer mm"},"B":{"value":33,"path":"explicit integer mm"}},
                            {"slotId":2,"A":{"value":13,"path":"material:cedar@1.A"},"B":{"value":19,"path":"material:cedar@1.B"}}]
        identifier=2
        for field in ("contactFace","orientation"):
            for slot_index in (0,1):
                with self.subTest(missing=field,slotId=slot_index+1):
                    value=binding(identifier=identifier)
                    value["slots"][1].update(A={"kind":"material","id":"cedar","version":1,"field":"A"},
                                             B={"kind":"material","id":"cedar","version":1,"field":"B"},
                                             contactFace="B",orientation="A")
                    value["slots"][slot_index][field]=None
                    self.apply([{"op":"put-binding","value":value}])
                    actual=next(b for b in self.read()["state"]["bindings"] if b["value"]["id"]==identifier)
                    self.assertEqual(value,actual["value"])
                    self.assertFalse(actual["complete"])
                    self.assertEqual(expected_effective,actual["effective"])
                    invalid=deepcopy(value);invalid["slots"][slot_index][field]="unknown"
                    self.reject([{"op":"put-binding","value":invalid}],f"binding {identifier} slot {slot_index+1}")
                    identifier+=1
        before=self.read()["state"]
        self.assertEqual([],before["instances"])
        self.assertEqual([],self.command("objects")["timbers"])
        self.assertEqual([],self.command("surfaces")["surfaces"])
        scene=self.command("dump")["text"];path=self.directory/"partial-orientation.scene"
        path.write_text(scene,encoding="utf-8")
        with BridgeSession(self.bridge,cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile "+str(path))["ok"])
            self.assertEqual(scene,fresh.command("dump")["text"])
            self.assertEqual(before,fresh.command("assembly-read")["state"])

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

        # A11: role identity, rather than slot order or the latest material,
        # determines each fixed dimension source.
        self.apply([{"op":"publish-material","value":dict(material,version=2,A=41,B=53)},
                    {"op":"publish-material","value":{"id":"oak","version":1,"kind":"timber","name":"橡木","A":37,"B":49}}])
        dimensions={("pine",1):(27,33),("pine",2):(41,53),("oak",1):(37,49)}
        expected={}
        for identifier,secondary in enumerate((("pine",1),("pine",2),("oak",1)),1):
            with self.subTest(secondary=secondary):
                value=binding(identifier=identifier);effective=[]
                for slot,fixed in zip(value["slots"],(("pine",1),secondary)):
                    material_id,version=fixed
                    for axis in ("A","B"):
                        slot[axis]={"kind":"material","id":material_id,"version":version,"field":axis}
                    if slot["slotId"]==2:
                        slot.update(contactFace="B",orientation="A")
                    effective.append({"slotId":slot["slotId"],**{
                        axis:{"value":dimensions[fixed][index],"path":f"material:{material_id}@{version}.{axis}"}
                        for index,axis in enumerate(("A","B"))}})
                value["slots"].reverse()
                self.apply([{"op":"put-binding","value":value}])
                expected[identifier]=(value,{slot["slotId"]:slot for slot in effective})
                actual=next(b for b in self.read()["state"]["bindings"] if b["value"]["id"]==identifier)
                self.assertTrue(actual["complete"])
                self.assertEqual(value,actual["value"])
                self.assertEqual(expected[identifier][1],{slot["slotId"]:slot for slot in actual["effective"]})
        self.apply([{"op":"publish-material","value":dict(material,version=3,A=61,B=71)},
                    {"op":"publish-material","value":{"id":"oak","version":2,"kind":"timber","name":"橡木新版","A":79,"B":83}}])
        before=self.read()["state"]
        self.assertEqual({1,2,3},{b["value"]["id"] for b in before["bindings"]})
        for actual in before["bindings"]:
            value,effective=expected[actual["value"]["id"]]
            self.assertTrue(actual["complete"])
            self.assertEqual(value,actual["value"])
            self.assertEqual(effective,{slot["slotId"]:slot for slot in actual["effective"]})
        scene=self.command("dump")["text"];path=self.directory/"fixed-materials.scene"
        path.write_text(scene,encoding="utf-8")
        with BridgeSession(self.bridge,cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile "+str(path))["ok"])
            self.assertEqual(scene,fresh.command("dump")["text"])
            self.assertEqual(before,fresh.command("assembly-read")["state"])

    def test_delete_parameter_is_refused_at_the_delete_step_naming_the_binding(self):
        # GEO-258 / I38:被組構配置槽位引用的參數卡,刪除那一步就拒絕並指名槽位;同一交易內先改成直接值再刪就通過。
        self.publish()
        param = {"id": 1, "name": "截面", "fields": [{"id": 1, "name": "A", "type": "dimension", "input": "40"}]}
        b = binding()
        b["slots"][0]["A"] = {"kind": "parameter", "parameterId": 1, "fieldId": 1}
        self.apply([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": b}])
        self.reject([{"op": "delete-parameter", "id": 1}], "I38 MISSING: parameter 1 is still referenced by binding 1 slot 1.A")
        self.apply([{"op": "put-binding", "value": binding()}, {"op": "delete-parameter", "id": 1}])
        self.assertEqual([], self.command("engineering-read")["state"]["parameters"])

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
