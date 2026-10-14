"""P-060 candidate-final parameter deletion checks; real bridge, no evaluator substitute."""
import json
from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from tests import test_parameters_core as harness
from tests.test_parameters_core import card, field


class ParameterDeleteOrder(unittest.TestCase):
    setUpClass = classmethod(harness.ParametersCore.setUpClass.__func__)
    setUp = harness.ParametersCore.setUp
    command = harness.ParametersCore.command
    read = harness.ParametersCore.read
    request = harness.ParametersCore.request
    apply = harness.ParametersCore.apply
    apply_line = harness.ParametersCore.apply_line
    values = harness.ParametersCore.values
    rejected = harness.ParametersCore.rejected

    def seed_dependency(self):
        self.apply([card(1, "source", [field(1, "10")]),
                    card(2, "dependent", [field(1, "=@1:1 + 1 mm")])])
        self.assertEqual("11", self.values()[2, 1]["num"])

    def atomic_preview_and_confirm(self, operations):
        before = self.command("dump")["text"]
        revision = self.read()["revision"]
        result = self.request(operations)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["preview"]["valid"],
                        "P-060 complete candidate has no dangling reference: " + json.dumps(result))
        self.assertEqual(before, self.command("dump")["text"], "preview changed live World")
        self.assertEqual(revision, self.read()["revision"], "preview changed revision")
        confirmed = self.command("engineering-confirm " + str(result["preview"]["token"]))
        self.assertTrue(confirmed["ok"], confirmed)
        self.last_confirm_receipt = confirmed
        self.assertTrue(confirmed["history_changed"], confirmed)
        self.assertEqual(revision + 1, self.read()["revision"], "batch was not one history step")
        return before, self.command("dump")["text"]

    def assert_deleted_fields(self, *identities):
        expected = [{"kind": "parameter-field", "parameterId": identity, "fieldId": 1}
                    for identity in sorted(identities)]
        actual = sorted(self.last_confirm_receipt["deletedObjects"],
                        key=lambda item: (item["parameterId"], item["fieldId"]))
        self.assertEqual(expected, actual, "same-key rebuild lost the intermediate deletion")

    def independent_import(self):
        return {"op": "import-parameters", "value": {"schema": "geometry-parameters/1", "cards": [
            {"id": identity, "name": "import-" + str(identity), "fields": [
                {"id": 1, "name": "size", "type": "dimension",
                 "expression": {"op": "literal", "num": "3", "den": "1", "unit": "mm"}}]}
            for identity in (101, 102, 103)]}}

    def check_both_deleted(self, order):
        self.seed_dependency()
        operations = [{"op": "delete-parameter", "id": identity} for identity in order]
        before, after = self.atomic_preview_and_confirm(operations)
        self.assert_deleted_fields(1, 2)
        self.assertEqual([], self.read()["state"]["parameters"])
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.apply_line("redo")
        self.assertEqual(after, self.command("dump")["text"])
        self.apply_line("undo")
        for identity in (1, 2):
            with self.subTest(redeclare=identity):
                self.atomic_preview_and_confirm(operations + [card(identity, "rebuilt", [field(1, "9")])])
                self.assertEqual([identity], [c["id"] for c in self.read()["state"]["parameters"]])
                self.assertEqual("9", self.values()[identity, 1]["num"])
                self.assert_deleted_fields(1, 2)
                self.apply_line("undo")
                self.assertEqual(before, self.command("dump")["text"])
        # P-111: the free keys 1 and 2 may belong to new imported cards.
        self.atomic_preview_and_confirm(operations + [self.independent_import()])
        self.assertEqual([0, 1, 2], [c["id"] for c in self.read()["state"]["parameters"]])
        self.assertEqual({(0, 1), (1, 1), (2, 1)}, set(self.values()))
        self.assert_deleted_fields(1, 2)

    def test_delete_source_then_dependent_uses_complete_candidate(self):
        self.check_both_deleted((1, 2))

    def test_delete_dependent_then_source_is_positive_order_control(self):
        # This order already passed with the old per-delete guard; it must stay green.
        self.check_both_deleted((2, 1))

    def test_delete_and_literal_replacement_are_valid_in_both_orders(self):
        self.seed_dependency()
        delete = {"op": "delete-parameter", "id": 1}
        replace = card(2, "dependent", [field(1, "9")])
        for operations in ([delete, replace], [replace, delete]):
            with self.subTest(order=[o["op"] for o in operations]):
                before, after = self.atomic_preview_and_confirm(operations)
                self.assert_deleted_fields(1)
                self.assertEqual([2], [c["id"] for c in self.read()["state"]["parameters"]])
                self.assertEqual("9", self.values()[2, 1]["num"])
                self.apply_line("undo")
                self.assertEqual(before, self.command("dump")["text"])
                self.apply_line("redo")
                self.assertEqual(after, self.command("dump")["text"])
                self.apply_line("undo")
                self.atomic_preview_and_confirm(operations + [card(1, "rebuilt", [field(1, "10")])])
                self.assertEqual("10", self.values()[1, 1]["num"])
                self.assertEqual("9", self.values()[2, 1]["num"])
                self.assert_deleted_fields(1)
                self.apply_line("undo")
                self.assertEqual(before, self.command("dump")["text"])
                self.atomic_preview_and_confirm(operations + [self.independent_import()])
                ids = [c["id"] for c in self.read()["state"]["parameters"]]
                self.assertEqual([0, 1, 2, 3], sorted(ids))
                self.assertEqual("3", self.values()[1, 1]["num"])
                self.assertEqual("9", self.values()[2, 1]["num"])
                self.assert_deleted_fields(1)
                self.apply_line("undo")
                self.assertEqual(before, self.command("dump")["text"])

    def test_final_dangling_reference_rejects_atomically_and_keeps_redo(self):
        self.seed_dependency()
        self.apply([card(8, "redo marker", [field(1, "7")])])
        redo_world = self.command("dump")["text"]
        self.apply_line("undo")
        before = self.command("dump")["text"]
        revision = self.read()["revision"]
        result = self.request([{"op": "delete-parameter", "id": 1}])
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["preview"]["valid"], result)
        self.assertIn("parameter 1 is still referenced by parameter 2 field 1", json.dumps(result))
        self.assertFalse(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(revision, self.read()["revision"])
        self.assertEqual("11", self.values()[2, 1]["num"])
        self.apply_line("redo")
        self.assertEqual(redo_world, self.command("dump")["text"], "invalid candidate destroyed redo")


if __name__ == "__main__":
    unittest.main()
