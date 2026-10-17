"""Independent unbind evaluates current required fields; final candidates stay atomic."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import test_parameters_core as harness
from tests.test_parameters_core import card, field


class IndependentUnbind(unittest.TestCase):
    setUpClass = classmethod(harness.ParametersCore.setUpClass.__func__)
    setUp = harness.ParametersCore.setUp
    command = harness.ParametersCore.command
    read = harness.ParametersCore.read
    request = harness.ParametersCore.request
    apply = harness.ParametersCore.apply
    apply_line = harness.ParametersCore.apply_line
    values = harness.ParametersCore.values
    TARGET = {"kind": "timber", "id": 1, "field": "A"}

    def seed(self, *, dependency=False, override=False):
        self.apply_line("timber 1 27 33 role boundary")
        self.apply_line("place 1 on 1 at-face e3 +v +n")
        cards = [card(1, "unrelated source", [field(1, "10")]),
                 card(2, "unrelated dependent", [field(1, "=@1:1")]),
                 card(3, "selected source", [field(1, "=@4:1" if dependency else "27")])]
        if dependency or override:
            cards.append(card(4, "selected dependency", [field(1, "29" if override else "27")]))
        self.apply(cards + [{"op": "set-source", "target": self.TARGET,
                             "source": {"kind": "parameter", "parameterId": 3, "fieldId": 1}}])
        if override:
            self.apply([{"op": "set-override", "target": self.TARGET,
                         "value": {"kind": "parameter", "parameterId": 4, "fieldId": 1}}])
        self.assertEqual(29 if override else 27, self.read()["state"]["sources"][0]["effective"])

    def unbind(self):
        return {"op": "unbind-source", "target": self.TARGET}

    def mixed(self, order):
        operations = {"delete1": {"op": "delete-parameter", "id": 1},
                      "delete2": {"op": "delete-parameter", "id": 2}, "unbind": self.unbind()}
        return [operations[name] for name in order]

    def accept_atomically(self, operations, *, value=27, identities=(3,)):
        before = self.command("dump")["text"]
        revision = self.read()["revision"]
        pending = self.request(operations)
        self.assertTrue(pending["ok"], pending)
        self.assertTrue(pending["preview"]["valid"],
                        "independent unbind must use its current required dependencies: " + json.dumps(pending))
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(revision, self.read()["revision"])
        self.assertEqual([], pending["preview"]["after"]["sources"])
        self.assertTrue(self.command("engineering-cancel " + str(pending["preview"]["token"]))["cancelled"])
        self.assertEqual(before, self.command("dump")["text"], "cancel changed formal definitions")
        self.assertEqual(revision, self.read()["revision"], "cancel changed revision")
        pending = self.request(operations)
        self.assertTrue(pending["preview"]["valid"], pending)
        confirmed = self.command("engineering-confirm " + str(pending["preview"]["token"]))
        self.assertTrue(confirmed["ok"], confirmed)
        self.assertTrue(confirmed["history_changed"], confirmed)
        self.assertEqual(revision + 1, self.read()["revision"], "mixed batch is one history step")
        after = self.command("dump")["text"]
        self.assertRegex(after, r"(?m)^timber 1 %d 33 role boundary$" % value,
                         "unbind did not preserve the current effective integer")
        self.assertEqual([], self.read()["state"]["sources"])
        self.assertEqual(list(identities), [c["id"] for c in self.read()["state"]["parameters"]])
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"], "Undo did not restore the full mixed candidate")
        self.apply_line("redo")
        self.assertEqual(after, self.command("dump")["text"], "Redo did not restore the full mixed candidate")
        return after

    def reject_atomically(self, operations, diagnostic):
        # Leave a real redo entry so rejecting a candidate cannot silently destroy it.
        self.apply([card(8, "redo marker", [field(1, "7")])])
        redo_world = self.command("dump")["text"]
        self.apply_line("undo")
        before = self.command("dump")["text"]
        revision = self.read()["revision"]
        pending = self.request(operations)
        self.assertTrue(pending["ok"], pending)
        self.assertFalse(pending["preview"]["valid"], "invalid dependency graph was accepted: " + json.dumps(pending))
        self.assertIn(diagnostic, json.dumps(pending))
        self.assertFalse(self.command("engineering-confirm " + str(pending["preview"]["token"]))["ok"])
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(revision, self.read()["revision"])
        self.apply_line("redo")
        self.assertEqual(redo_world, self.command("dump")["text"], "rejection destroyed the existing redo")

    def test_independent_unbind_between_deletes(self):
        self.seed()
        self.accept_atomically(self.mixed(("delete1", "unbind", "delete2")))

    def test_independent_unbind_before_deletes_is_order_control(self):
        self.seed()
        self.accept_atomically(self.mixed(("unbind", "delete1", "delete2")))

    def test_independent_unbind_after_deletes_is_order_control(self):
        self.seed()
        self.accept_atomically(self.mixed(("delete1", "delete2", "unbind")))

    def test_changed_dependency_is_recomputed_for_unbind(self):
        self.seed(dependency=True)
        operations = [card(4, "selected dependency", [field(1, "29")])]
        operations += self.mixed(("delete1", "unbind", "delete2"))
        self.accept_atomically(operations, value=29, identities=(3, 4))
        self.assertEqual("29", self.values()[3, 1]["num"])

    def test_parameter_override_is_recomputed_for_unbind(self):
        self.seed(override=True)
        operations = [card(4, "selected dependency", [field(1, "31")])]
        operations += self.mixed(("delete1", "unbind", "delete2"))
        self.accept_atomically(operations, value=31, identities=(3, 4))
        self.assertEqual("27", self.values()[3, 1]["num"], "override rewrote the base source")

    def test_missing_target_dependency_is_rejected(self):
        self.seed()
        self.reject_atomically([card(3, "selected source", [field(1, "=@99:1")]), self.unbind()],
                               "I38 MISSING: parameter 99 field 1")

    def test_cyclic_target_dependency_is_rejected(self):
        self.seed()
        self.reject_atomically([card(3, "selected source", [field(1, "=@3:1")]), self.unbind()],
                               "I38 CYCLE: parameter 3 field 1")

    def test_final_unrelated_cycle_is_still_rejected(self):
        self.seed()
        self.reject_atomically([card(1, "unrelated source", [field(1, "=@2:1")]), self.unbind()],
                               "I38 CYCLE")


if __name__ == "__main__":
    unittest.main()
