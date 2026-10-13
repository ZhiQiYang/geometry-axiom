"""A13 native source-type and capacity boundaries; every rejection is atomic."""
from copy import deepcopy
import unittest

from tests import test_assembly_rules as harness


class AssemblyCapacity(unittest.TestCase):
    setUpClass = classmethod(harness.AssemblyRules.setUpClass.__func__)
    setUp = harness.AssemblyRules.setUp
    command = harness.AssemblyRules.command
    read = harness.AssemblyRules.read
    request = harness.AssemblyRules.request
    apply = harness.AssemblyRules.apply
    reject = harness.AssemblyRules.reject
    publish = harness.AssemblyRules.publish

    def test_material_kind_field_and_fixed_version_are_not_incomplete_values(self):
        wood = {"id": "wood", "version": 1, "kind": "timber", "name": "Wood", "A": 27, "B": 33}
        panel = {"id": "panel", "version": 1, "kind": "panel", "name": "Panel", "width": 915, "length": 1830}
        good = harness.binding()
        for axis in ("A", "B"):
            good["slots"][0][axis] = {"kind": "material", "id": "wood", "version": 1, "field": axis}
        self.apply([{"op": "publish-rule", "value": harness.rule()},
                    {"op": "publish-material", "value": wood},
                    {"op": "publish-material", "value": panel},
                    {"op": "put-binding", "value": good}])
        accepted = self.read()["state"]["bindings"][0]
        self.assertTrue(accepted["complete"])
        self.assertEqual(good, accepted["value"])
        self.assertEqual([27, 33], [accepted["effective"][0][axis]["value"] for axis in ("A", "B")])
        for axis, source in [
            ("A", {"kind": "material", "id": "panel", "version": 1, "field": "width"}),
            ("B", {"kind": "material", "id": "panel", "version": 1, "field": "B"}),
            ("A", {"kind": "material", "id": "wood", "version": 1, "field": "B"}),
            ("B", {"kind": "material", "id": "wood", "version": 1, "field": "A"}),
            ("A", {"kind": "material", "id": "wood", "version": 2, "field": "A"}),
        ]:
            with self.subTest(axis=axis, source=source):
                invalid = deepcopy(good)
                invalid["slots"][0][axis] = source
                self.reject([{"op": "put-binding", "value": invalid}], "binding 1 slot 1." + axis)
                self.assertEqual(accepted, self.read()["state"]["bindings"][0])

    def test_slot_member_and_joint_capacity_has_an_accepted_boundary(self):
        # Each independent fixture reaches the declared limit without a duplicate
        # identity, duplicate scope, or repeated endpoint masking the capacity guard.
        for collection, limit in [("slots", 8), ("members", 12), ("joints", 16)]:
            with self.subTest(collection=collection):
                self.assertTrue(self.command("reset")["ok"])
                value = harness.rule()
                if collection == "slots":
                    value["slots"] = [{"id": i, "name": "Slot " + str(i)} for i in range(1, 9)]
                    extra = {"id": 9, "name": "Overflow slot"}
                elif collection == "members":
                    value["members"] = [{"id": i, "slotId": 1 if i != 3 else 2} for i in range(1, 13)]
                    extra = {"id": 13, "slotId": 1}
                else:
                    value["members"] = [{"id": i, "slotId": 1 if i == 1 else 2} for i in range(1, 13)]
                    value["joints"] = [{"id": i + 1, "kind": "end-to-side", "scope": "joint-" + str(i + 1),
                                        "terminatedMember": i // 2 + 2, "targetMember": 1,
                                        "end": "start" if i % 2 == 0 else "finish", "side": "+u", "dir": "u"}
                                       for i in range(16)]
                    extra = {"id": 17, "kind": "end-to-side", "scope": "joint-17",
                             "terminatedMember": 10, "targetMember": 1, "end": "start", "side": "+u", "dir": "u"}
                self.assertEqual(limit, len(value[collection]))
                self.publish(value)
                self.assertEqual(value, self.read()["state"]["rules"][0]["value"])
                overflow = deepcopy(value)
                overflow["version"] = 2
                overflow[collection].append(extra)
                self.reject([{"op": "publish-rule", "value": overflow}], "I40/CAPACITY")

    def test_published_version_capacity_counts_versions_and_recovers_after_delete(self):
        # All 32 versions belong to one rule: counting distinct rule IDs would
        # incorrectly miss this boundary and could write beyond the native array.
        for version in range(1, 33):
            self.publish(harness.rule(version=version))
        self.assertEqual(list(range(1, 33)), [r["value"]["version"] for r in self.read()["state"]["rules"]])
        self.publish(harness.rule(version=32))  # Idempotence at full capacity is legal.
        self.reject([{"op": "publish-rule", "value": harness.rule(version=33)}], "CAPACITY")
        self.apply([{"op": "delete-rule", "id": 1, "version": 1},
                    {"op": "publish-rule", "value": harness.rule(version=33)}])
        self.assertEqual(list(range(2, 34)), [r["value"]["version"] for r in self.read()["state"]["rules"]])

    def test_binding_capacity_rejects_new_identity_but_allows_explicit_update(self):
        self.publish()
        for identifier in range(1, 65):
            self.apply([{"op": "put-binding", "value": harness.binding(identifier=identifier)}])
        self.assertEqual(list(range(1, 65)), [b["value"]["id"] for b in self.read()["state"]["bindings"]])
        update = harness.binding(identifier=64)
        update["name"] = "Explicitly updated existing binding"
        self.apply([{"op": "put-binding", "value": update}])
        self.assertEqual(update, self.read()["state"]["bindings"][-1]["value"])
        self.reject([{"op": "put-binding", "value": harness.binding(identifier=65)}], "CAPACITY")
        self.apply([{"op": "delete-binding", "id": 1},
                    {"op": "put-binding", "value": harness.binding(identifier=65)}])
        self.assertEqual(list(range(2, 66)), [b["value"]["id"] for b in self.read()["state"]["bindings"]])

    def test_utf8_name_and_scope_limits_reject_without_truncation(self):
        value = harness.rule()
        value["name"] = "木" * 32  # 96 UTF-8 bytes, not 96 Unicode codepoints.
        value["slots"][0]["name"] = "框" * 32
        value["joints"][0]["scope"] = "s" * 64
        self.publish(value)
        self.assertEqual(value, self.read()["state"]["rules"][0]["value"])
        for field in ("rule-name", "slot-name", "scope"):
            with self.subTest(field=field):
                invalid = deepcopy(value)
                invalid["version"] = 2
                if field == "rule-name":
                    invalid["name"] += "x"
                elif field == "slot-name":
                    invalid["slots"][0]["name"] += "x"
                else:
                    invalid["joints"][0]["scope"] += "x"
                self.reject([{"op": "publish-rule", "value": invalid}], "D32" if field == "rule-name" else "I40")


if __name__ == "__main__":
    unittest.main()
