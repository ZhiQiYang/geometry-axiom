"""Real native zero-ID ParameterRef controls for assembly draft validation."""
import unittest

from tests import test_assembly_rules as harness
from tests._bridge import BridgeSession
binding, rule = harness.binding, harness.rule


class AssemblyParameterRefs(unittest.TestCase):
    setUpClass = classmethod(harness.AssemblyRules.setUpClass.__func__)
    setUp = harness.AssemblyRules.setUp
    command = harness.AssemblyRules.command
    read = harness.AssemblyRules.read
    request = harness.AssemblyRules.request
    apply = harness.AssemblyRules.apply
    reject = harness.AssemblyRules.reject

    def seed(self, parameter_id, field_id, field_type="dimension", value="27"):
        param = {"id": parameter_id, "name": "zero identity source", "fields": [
            {"id": field_id, "name": "width", "type": field_type, "input": value}]}
        bound = binding()
        bound["slots"][0]["A"] = {"kind": "parameter", "parameterId": parameter_id, "fieldId": field_id}
        return param, bound

    def test_zero_ids_commit_reload_and_follow_source_without_flattening(self):
        for parameter_id, field_id in [(1, 1), (0, 1), (1, 0), (0, 0)]:
            with self.subTest(parameter_id=parameter_id, field_id=field_id):
                self.assertTrue(self.command("reset")["ok"])
                param, bound = self.seed(parameter_id, field_id)
                self.apply([{"op": "publish-rule", "value": rule()},
                            {"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}])
                record = self.read()["state"]["bindings"][0]
                self.assertEqual(bound, record["value"])
                self.assertEqual(27, record["effective"][0]["A"]["value"])
                saved = self.command("dump")["text"]
                path = self.directory / "parameter-binding.scene"
                path.write_text(saved, encoding="utf-8")
                # Reopen in a new native process, rather than reading the same World.
                reopened = BridgeSession(self.bridge, cwd=self.directory)
                try:
                    self.assertTrue(reopened.command("loadfile " + str(path))["ok"])
                    loaded = reopened.command("assembly-read")["state"]["bindings"][0]
                    self.assertEqual(bound, loaded["value"])
                    self.assertEqual(27, loaded["effective"][0]["A"]["value"])
                finally:
                    reopened.stop()
                param["fields"][0]["input"] = "29"
                self.apply([{"op": "put-parameter", "value": param}])
                record = self.read()["state"]["bindings"][0]
                self.assertEqual(bound, record["value"])
                self.assertEqual(29, record["effective"][0]["A"]["value"])

    def test_zero_identity_does_not_bypass_dimension_type_and_value_guards(self):
        self.apply([{"op": "publish-rule", "value": rule()}])
        for field_type, value in [("count", "27"), ("ratio", "27"), ("dimension", "0"),
                                  ("dimension", "-1"), ("dimension", "1.5"), ("dimension", "100000001")]:
            with self.subTest(field_type=field_type, value=value):
                param, bound = self.seed(0, 0, field_type, value)
                self.reject([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}], "binding 1 slot 1.A")

    def test_missing_zero_reference_rejected_without_world_mutation(self):
        self.apply([{"op": "publish-rule", "value": rule()}])
        for parameter_id, field_id in [(0, 1), (1, 0), (0, 0)]:
            _, bound = self.seed(parameter_id, field_id)
            self.reject([{"op": "put-binding", "value": bound}], "binding 1 slot 1.A")
            # P121/P122: identical full binding declarations count only after deletion.
            param, bound = self.seed(parameter_id, field_id)
            self.apply([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}])
            param["fields"][0]["input"] = "29"
            deleted = {"op": "delete-parameter", "id": parameter_id}
            rebuilt = {"op": "put-parameter", "value": param}
            declared = {"op": "put-binding", "value": bound}
            self.reject([deleted, rebuilt], "binding 1 slot 1.A")
            self.reject([declared, deleted, rebuilt], "binding 1 slot 1.A")
            preview = self.request([deleted, rebuilt, declared])["preview"]
            self.assertTrue(preview["valid"], preview)
            self.assertEqual([{"kind": "assembly-binding", "id": 1, "slot": 0}],
                             [r["owner"] for r in preview["redeclaredReferences"]])
            self.assertEqual([{"parameterId": parameter_id, "fieldId": field_id}],
                             [r["source"] for r in preview["redeclaredReferences"]])
            done = self.command("assembly-confirm " + str(preview["token"]))
            self.assertTrue(done["ok"], done)
            self.assertEqual(29, self.read()["state"]["bindings"][0]["effective"][0]["A"]["value"])
            self.assertEqual([{"kind": "parameter-field", "parameterId": parameter_id, "fieldId": field_id}], done["deletedObjects"])
            self.apply([{"op": "delete-binding", "id": 1}, {"op": "delete-parameter", "id": parameter_id}])


if __name__ == "__main__":
    unittest.main()
