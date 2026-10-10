"""Typed evidence from existing native assembly refusals; no message parsing."""
from copy import deepcopy
import unittest

from tests import test_assembly_rules as harness
from tests import test_assembly_parameter_refs as parameter_harness


class AssemblyNativeDiagnostics(unittest.TestCase):
    setUpClass = classmethod(harness.AssemblyRules.setUpClass.__func__)
    setUp = harness.AssemblyRules.setUp
    command = harness.AssemblyRules.command
    read = harness.AssemblyRules.read
    request = harness.AssemblyRules.request
    apply = harness.AssemblyRules.apply
    seed = parameter_harness.AssemblyParameterRefs.seed

    def evidence(self, operations, code, clause, ref=None):
        before = self.command("dump")["text"], self.read()["revision"]
        result = self.request(operations)
        self.assertTrue(result["ok"], result)
        preview = result["preview"]
        self.assertFalse(preview["valid"], preview)
        violation = preview["violations"][0]
        self.assertEqual(code, violation["code"])
        self.assertEqual(clause, violation["clause"])
        if ref is None:
            self.assertNotIn("ref", violation)
        else:
            self.assertEqual(ref, violation["ref"])
        self.assertTrue(violation["message"])
        self.assertFalse(self.command(f'assembly-confirm {preview["token"]}')["ok"])
        self.assertEqual(before, (self.command("dump")["text"], self.read()["revision"]))
        return preview

    def test_wrong_dimension_types_and_zero_identities_have_exact_refs(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        for parameter_id, field_id in [(41, 9), (0, 9), (41, 0), (0, 0)]:
            for field_type in ("count", "ratio"):
                with self.subTest(parameter_id=parameter_id, field_id=field_id, field_type=field_type):
                    param, bound = self.seed(parameter_id, field_id, field_type)
                    self.evidence([{"op": "put-parameter", "value": param},
                                   {"op": "put-binding", "value": bound}],
                                  "DIMENSION_TYPE", "D33",
                                  {"kind": "parameter", "id": parameter_id, "fieldId": field_id})

    def test_numeric_dimension_failures_keep_generic_evidence(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        for value in ("0", "-1", "1.5", "100000001"):
            with self.subTest(value=value):
                param, bound = self.seed(41, 9, "dimension", value)
                self.evidence([{"op": "put-parameter", "value": param},
                               {"op": "put-binding", "value": bound}],
                              "ASSEMBLY_INVALID", "I40/I41")

    def test_missing_parameter_and_field_keep_generic_evidence(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        param, bound = self.seed(41, 9, "count")
        self.evidence([{"op": "put-binding", "value": bound}], "ASSEMBLY_INVALID", "I40/I41")
        param["fields"][0]["id"] = 10
        self.evidence([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}],
                      "ASSEMBLY_INVALID", "I40/I41")

    def test_immutable_overwrite_and_delete_republish_have_exact_fixed_ref(self):
        original = harness.rule(17, 1)
        self.apply([{"op": "publish-rule", "value": original}])
        changed = deepcopy(original)
        changed["name"] = "changed fixed version"
        ref = {"kind": "rule", "id": 17, "version": 1}
        self.evidence([{"op": "publish-rule", "value": changed}], "RULE_VERSION_IMMUTABLE", "D32", ref)
        self.evidence([{"op": "delete-rule", "id": 17, "version": 1},
                       {"op": "publish-rule", "value": changed}], "RULE_VERSION_IMMUTABLE", "D32", ref)

    def test_first_ref_is_frozen_before_after_state_resolves_other_fields(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        first, bound = self.seed(41, 9, "count")
        second, unused = self.seed(42, 10, "ratio")
        bound["slots"][1]["A"] = unused["slots"][0]["A"]
        self.evidence([{"op": "put-parameter", "value": first}, {"op": "put-parameter", "value": second},
                       {"op": "put-binding", "value": bound}], "DIMENSION_TYPE", "D33",
                      {"kind": "parameter", "id": 41, "fieldId": 9})

    def test_valid_preview_after_typed_failure_and_reads_has_no_stale_evidence(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        param, bound = self.seed(0, 0, "count")
        self.evidence([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}],
                      "DIMENSION_TYPE", "D33", {"kind": "parameter", "id": 0, "fieldId": 0})
        param["fields"][0]["type"] = "dimension"
        valid = self.request([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}])
        self.assertTrue(valid["preview"]["valid"], valid)
        self.assertEqual([], valid["preview"]["violations"])
        for command in ("assembly-read", "engineering-read", "objects", "dump"):
            self.assertTrue(self.command(command)["ok"])
        token = valid["preview"]["token"]
        self.assertTrue(self.command(f"assembly-confirm {token}")["ok"])
        changed = harness.rule()
        changed["name"] = "changed"
        self.evidence([{"op": "publish-rule", "value": changed}], "RULE_VERSION_IMMUTABLE", "D32",
                      {"kind": "rule", "id": 1, "version": 1})

    def test_early_protocol_failure_does_not_leak_into_next_generic_candidate(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        changed = harness.rule()
        changed["name"] = "changed"
        self.evidence([{"op": "publish-rule", "value": changed}], "RULE_VERSION_IMMUTABLE", "D32",
                      {"kind": "rule", "id": 1, "version": 1})
        path = self.directory / "invalid.json"
        path.write_text("{", encoding="utf-8")
        self.assertFalse(self.command("assembly-preview " + str(path))["ok"])
        _, bound = self.seed(99, 99)
        self.evidence([{"op": "put-binding", "value": bound}], "ASSEMBLY_INVALID", "I40/I41")

    def test_cancel_and_invalid_candidates_leave_undo_history_and_serialization_clean(self):
        self.apply([{"op": "publish-rule", "value": harness.rule()}])
        param, bound = self.seed(41, 9, "count")
        invalid = self.evidence([{"op": "put-parameter", "value": param}, {"op": "put-binding", "value": bound}],
                                "DIMENSION_TYPE", "D33", {"kind": "parameter", "id": 41, "fieldId": 9})
        self.assertTrue(self.command(f'assembly-cancel {invalid["token"]}')["ok"])
        saved = self.command("dump")["text"]
        for text in ("DIMENSION_TYPE", "RULE_VERSION_IMMUTABLE", "assembly_diagnostic"):
            self.assertNotIn(text, saved)
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual([], self.read()["state"]["rules"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(saved, self.command("dump")["text"])


if __name__ == "__main__":
    unittest.main()
