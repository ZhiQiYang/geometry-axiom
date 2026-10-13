"""#48 typed target facts from the real native bridge; no frontend evaluator.

Native content pins intentionally do not prove an object's incarnation. These
tests provide the independent zero-ID and recreation witnesses consumed by the
evidence adapter tests. All test definitions are authored here, with no PDF data.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402


def field(field_id, text="457.5", name="width", kind="dimension"):
    return {"id": field_id, "name": name, "type": kind, "input": text}


def card(card_id=0, fields=None, name="authored parameter"):
    return {"op": "put-parameter", "value": {
        "id": card_id, "name": name,
        "fields": [field(0)] if fields is None else fields,
    }}


class EvidenceLinkNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-evidence-native-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = _bridge.BridgeSession(self.bridge, cwd=self.directory)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])

    def command(self, text):
        return self.session.command(text)

    def read(self):
        result = self.command("engineering-read")
        self.assertTrue(result["ok"], result)
        return result

    def request(self, operations):
        request = {"schema": "engineering-transaction/1",
                   "expectedRevision": self.read()["revision"],
                   "operations": operations}
        path = self.directory / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        result = self.command("engineering-preview " + str(path))
        self.assertTrue(result["ok"], result)
        return result["preview"]

    def apply(self, operations):
        preview = self.request(operations)
        self.assertTrue(preview["valid"], preview)
        self.assertTrue(self.command("engineering-confirm " + str(preview["token"]))["ok"])

    def graph(self):
        result = self.command("source-inspect")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["complete"], result)
        return result

    def target(self, card_id=0, field_id=0):
        key = f"parameter-field:{card_id}:f{field_id}"
        return next(node for node in self.graph()["nodes"] if node["key"] == key)

    def value(self, card_id=0, field_id=0):
        cards = self.read()["state"]["parameters"]
        current = next(item for item in cards if item["id"] == card_id)
        return next(item["value"] for item in current["fields"] if item["id"] == field_id)

    def dump(self):
        return self.command("dump")["text"]

    def node_assertions(self, script, payload):
        preamble = r"""
          const assert = require('node:assert/strict');
          const fs = require('node:fs');
          const E = require('./geometry-web/evidence-links.js');
          const S = require('./geometry-web/source-inspector.js');
          const input = JSON.parse(fs.readFileSync(0, 'utf8'));
          const scope = 'authored-project';
          const document = {sourceHash:'a'.repeat(64),referencePageId:'authored-page',page:1,
            coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,
            rotationBasis:0,cropBasis:[20,30,200,120]};
          const observations = {
            drawing:{rawText:'915/2 mm drawing',rawValue:'915/2',unit:'mm',note:''},
            measurement:{rawText:'460.125 mm measured',rawValue:'460.125',unit:'mm',note:''}};
          const node = graph => S.index(graph).nodes.get(S.key('parameter-field',0,0,0));
          const target = graph => E.targetFromNode(scope,node(graph));
          const link = graph => ({evidenceId:'authored-evidence',document,region:[30,40,80,25],
            target:target(graph),observations,humanConfirmation:null});
        """
        result = subprocess.run(["node", "-e", preamble + script], input=json.dumps(payload),
                                cwd=ROOT, text=True, capture_output=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("native evidence assertions passed", result.stdout)

    def test_zero_typed_identity_exact_values_and_read_only_native_reads(self):
        self.apply([card(fields=[field(0), field(1, "2", "quantity", "count"),
                                 field(2, "1/3", "ratio", "ratio")])])
        before = self.dump()
        revision = self.read()["revision"]
        target = self.target()
        self.assertEqual(("parameter-field", "0", 0, "parameter-field:0:f0"),
                         (target["kind"], target["id"], target["fieldId"], target["key"]))
        self.assertEqual({"num": "915", "den": "2", "unit": "mm"}, self.value())
        self.assertEqual({"num": "2", "den": "1", "unit": "1"}, self.value(0, 1))
        self.assertEqual({"num": "1", "den": "3", "unit": "1"}, self.value(0, 2))
        objects = self.command("objects")["parameters"][0]["card"]
        self.assertEqual([0, 1, 2], [item["id"] for item in objects["fields"]])
        self.assertEqual(self.value(), objects["fields"][0]["value"])
        self.assertEqual("unknown", self.graph()["identityContinuity"])
        self.node_assertions(r"""
          (async()=>{
            let attachment=null,revision=0;
            const controller=E.createController({
              readFeatureAttachment:()=>attachment,
              setFeatureAttachment:(kind,value,token)=>{
                assert.equal(kind,E.KIND);assert.equal(token,'authored-context');
                attachment=structuredClone(value);revision++;
              },
              getStamp:()=>({projectScope:scope,contextToken:'authored-context',revision,
                nativeRevision:input.graph.revision}),
              readCurrent:async()=>({document,target:target(input.graph),modelValue:input.value,
                nativeRevision:input.graph.revision}),
              locateDocument:async()=>{},uuid:()=> 'authored-evidence',
              now:()=> '2026-10-04T00:00:00.000Z'
            });
            assert.deepEqual(target(input.graph),{projectScope:scope,kind:'parameter-field',
              parameterId:0,fieldId:0,definitionPin:node(input.graph).definitionFingerprint,incarnation:null});
            await controller.add({document,region:[30,40,80,25],target:target(input.graph),observations});
            await controller.setReviewed('authored-evidence',true);
            const view=(await controller.readView()).links[0];
            assert.equal(view.status,'confirmed-content');
            assert.deepEqual(view.modelValue,{num:'915',den:'2',unit:'mm'});
            assert.deepEqual(view.observations,observations);
            assert.equal(view.observations.measurement.rawValue,'460.125');
            assert.equal(view.humanConfirmation.targetPin,node(input.graph).definitionFingerprint);
            console.log('native evidence assertions passed');
          })().catch(error=>{console.error(error);process.exitCode=1;});
        """, {"graph": self.graph(), "value": self.value()})
        self.assertEqual(before, self.dump())
        self.assertEqual(revision, self.read()["revision"])

    def test_reorder_and_rename_keep_typed_pin_but_definition_change_updates_it(self):
        self.apply([card(fields=[field(0), field(1, "1", "quantity", "count")])])
        initial_graph = self.graph()
        initial = self.target()
        self.apply([card(fields=[field(1, "1", "count renamed", "count"),
                                 field(0, "457.5", "width renamed")], name="renamed card")])
        renamed = self.target()
        self.assertEqual(initial["key"], renamed["key"])
        self.assertEqual(initial["definitionFingerprint"], renamed["definitionFingerprint"])
        self.assertEqual(initial["valueFingerprint"], renamed["valueFingerprint"])
        self.assertNotEqual(initial["label"], renamed["label"])
        self.apply([card(fields=[field(0, "458", "width renamed"),
                                 field(1, "1", "count renamed", "count")])])
        changed = self.target()
        self.assertNotEqual(initial["definitionFingerprint"], changed["definitionFingerprint"])
        self.assertNotEqual(initial["valueFingerprint"], changed["valueFingerprint"])
        self.assertEqual({"num": "458", "den": "1", "unit": "mm"}, self.value())
        self.node_assertions(r"""
          const evidence=link(input.before);
          const prior={document,target:target(input.before),modelValue:input.beforeValue};
          const changed={document,target:target(input.after),modelValue:input.afterValue};
          assert.equal(E.assess(evidence,prior,{identityKnown:true}).canConfirm,true);
          assert.deepEqual(E.assess(evidence,changed,{identityKnown:true}),
            {status:'needs-reassociation',canConfirm:false});
          assert.notEqual(evidence.target.definitionPin,changed.target.definitionPin);
          assert.equal(evidence.observations.drawing.rawValue,'915/2');
          assert.deepEqual(changed.modelValue,{num:'458',den:'1',unit:'mm'});
          console.log('native evidence assertions passed');
        """, {"before": initial_graph, "after": self.graph(),
              "beforeValue": {"num": "915", "den": "2", "unit": "mm"}, "afterValue": self.value()})

    def test_dependency_value_change_preserves_local_definition_pin(self):
        self.apply([card(), card(1, [field(0, "=@0:0 + 2 mm")])])
        initial = self.target(1)
        self.assertEqual({"num": "919", "den": "2", "unit": "mm"}, self.value(1))
        self.apply([card(fields=[field(0, "458.5")])])
        changed = self.target(1)
        self.assertEqual(initial["definitionFingerprint"], changed["definitionFingerprint"])
        self.assertNotEqual(initial["valueFingerprint"], changed["valueFingerprint"])
        self.assertEqual({"num": "921", "den": "2", "unit": "mm"}, self.value(1))
        self.assertIn(("parameter-field:1:f0", "parameter-field:0:f0"),
                      {(edge["from"], edge["to"]) for edge in self.graph()["edges"]})

    def test_same_card_id_name_and_content_recreation_cannot_prove_incarnation(self):
        self.apply([card()])
        before = self.graph()
        initial = self.target()
        self.apply([{"op": "delete-parameter", "id": 0}])
        self.assertFalse(any(node["key"] == initial["key"] for node in self.graph()["nodes"]))
        self.apply([card()])
        recreated = self.target()
        self.assertEqual(initial, recreated)
        self.assertNotEqual(before["revision"], self.graph()["revision"])
        self.assertEqual("unknown", self.graph()["identityContinuity"])
        self.node_assertions(r"""
          const evidence=link(input.before);
          evidence.humanConfirmation={documentHash:document.sourceHash,
            targetPin:evidence.target.definitionPin,confirmedAt:'2026-10-04T00:00:00.000Z'};
          const current={document,target:target(input.after),modelValue:input.value};
          assert.deepEqual(evidence.target,current.target);
          assert.equal(input.after.identityContinuity,'unknown');
          assert.deepEqual(E.assess(evidence,current),{status:'needs-reassociation',canConfirm:false});
          assert.notEqual(input.before.revision,input.after.revision);
          console.log('native evidence assertions passed');
        """, {"before": before, "after": self.graph(), "value": self.value()})

    def test_deleted_field_zero_cannot_reuse_identity_in_retained_card(self):
        self.apply([card(fields=[field(0), field(1, "1", "quantity", "count")])])
        self.apply([card(fields=[field(1, "1", "quantity", "count")])])
        before = self.dump()
        rejected = self.request([card(fields=[field(0), field(1, "1", "quantity", "count")])])
        self.assertFalse(rejected["valid"], rejected)
        self.assertIn("cannot be reused", json.dumps(rejected))
        self.assertFalse(self.command("engineering-confirm " + str(rejected["token"]))["ok"])
        self.assertEqual(before, self.dump())

    def test_cancel_and_late_native_candidate_leave_formal_target_unchanged(self):
        self.apply([card()])
        before = self.dump()
        target = self.target()
        preview = self.request([card(fields=[field(0, "700")])])
        self.assertTrue(preview["valid"], preview)
        self.assertTrue(self.command("engineering-cancel " + str(preview["token"]))["cancelled"])
        self.assertEqual(before, self.dump())
        self.assertEqual(target, self.target())
        preview = self.request([card(fields=[field(0, "700")])])
        self.assertTrue(self.command("line spec unrelated_revision 9")["ok"])
        after_unrelated = self.dump()
        late = self.command("engineering-confirm " + str(preview["token"]))
        self.assertFalse(late["ok"], late)
        self.assertEqual("STALE", late["code"])
        self.assertEqual(after_unrelated, self.dump())
        self.assertEqual(target, self.target())


if __name__ == "__main__":
    unittest.main()
