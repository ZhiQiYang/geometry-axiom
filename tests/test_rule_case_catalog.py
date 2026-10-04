"""Independent data and native oracles for the six finite #49 cases."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
sys.path.insert(0, str(ROOT))

from rule_cases.catalog import case, cases
from rule_cases.definition import validate_case
from rule_cases.executor import NativeExecutor
from tests._bridge import find_bridge


CASE_IDS = (
    "same-role-distinct-members", "one-local-joint-new-version",
    "wrong-type-dimension-reference", "legal-rule",
    "legal-incomplete-binding", "fixed-version-immutable",
)


def canonical_hash(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def record(state, kind, identifier, version=None):
    """Find by native typed identity; array index and name never select a record."""
    records = state["rules" if kind == "rule" else "bindings"]
    matches = [item for item in records if item["value"]["id"] == identifier
               and (version is None or item["value"]["version"] == version)]
    if len(matches) != 1:
        raise AssertionError((kind, identifier, version, matches))
    return matches[0]


class RuleCaseCatalog(unittest.TestCase):
    def test_exactly_the_six_adopted_cases_in_first_slice_order(self):
        self.assertEqual(CASE_IDS, tuple(value["caseId"] for value in cases()))
        for value in cases():
            with self.subTest(case=value["caseId"]):
                self.assertEqual(value, validate_case(value))

    def test_definitions_are_independent_editable_copies(self):
        values = cases()
        original_joint_case = deepcopy(values[1])
        values[0]["input"]["transaction"][0]["value"]["members"][0]["id"] = 999
        self.assertEqual(original_joint_case, values[1])
        isolated = case("one-local-joint-new-version")
        isolated["input"]["setup"][0]["value"]["name"] = "edited"
        self.assertNotEqual("edited", case("one-local-joint-new-version")["input"]["setup"][0]["value"]["name"])
        self.assertEqual(11, cases()[0]["input"]["transaction"][0]["value"]["members"][0]["id"])
        with self.assertRaises(KeyError):
            case("uploaded-script")

    def test_pins_cover_every_setup_record_with_canonical_definition_hashes(self):
        kinds = {"publish-rule": "rule", "create-binding": "binding", "put-parameter": "parameter"}
        for value in cases():
            with self.subTest(case=value["caseId"]):
                expected = []
                for operation in value["input"]["setup"]:
                    source = operation["value"]
                    ref = {"kind": kinds[operation["op"]], "id": source["id"]}
                    if ref["kind"] == "rule":
                        ref["version"] = source["version"]
                    expected.append({"ref": ref, "sha256": canonical_hash(source)})
                self.assertEqual(expected, value["sourcePins"])

    def test_same_role_uses_distinct_nonsequential_member_and_joint_identities(self):
        value = case("same-role-distinct-members")
        rule = value["input"]["transaction"][0]["value"]
        self.assertEqual({11: 7, 37: 7, 89: 13}, {member["id"]: member["slotId"] for member in rule["members"]})
        self.assertEqual({101: (89, 11, "start"), 203: (89, 37, "finish")},
                         {joint["id"]: (joint["terminatedMember"], joint["targetMember"], joint["end"])
                          for joint in rule["joints"]})
        expected = {item["jointId"]: item["value"]["targetMember"]
                    for item in value["assertions"] if item["kind"] == "joint_tuple"}
        self.assertEqual({101: 11, 203: 37}, expected)

    def test_local_joint_case_changes_only_one_joint_in_a_new_version(self):
        value = case("one-local-joint-new-version")
        old = value["input"]["setup"][0]["value"]
        new = value["input"]["transaction"][0]["value"]
        expected = deepcopy(old)
        expected["version"] = 2
        expected["joints"][0]["side"] = "-u"
        self.assertEqual(expected, new)
        self.assertEqual({"id": 17, "version": 1}, value["input"]["setup"][1]["value"]["rule"])
        self.assertIn({"kind": "joint_tuple_equal",
                       "before": {"ref": {"kind": "rule", "id": 17, "version": 1}, "jointId": 203},
                       "after": {"ref": {"kind": "rule", "id": 17, "version": 2}, "jointId": 203}}, value["assertions"])

    def test_wrong_type_changes_only_the_exact_referenced_field_type(self):
        value = case("wrong-type-dimension-reference")
        old = value["input"]["setup"][1]["value"]
        expected = deepcopy(old)
        expected["fields"][0]["type"] = "count"
        self.assertEqual(expected, value["input"]["transaction"][0]["value"])
        bound = value["input"]["setup"][2]["value"]
        self.assertEqual({"kind": "parameter", "parameterId": 41, "fieldId": 9}, bound["slots"][0]["A"])
        self.assertEqual({"outcome": "rejected", "diagnostic": {
            "code": "DIMENSION_TYPE", "clause": "D33", "ref": {"kind": "parameter", "id": 41, "fieldId": 9}}}, value["expect"])

    def test_incomplete_is_unset_rather_than_a_missing_or_wrong_type_source(self):
        value = case("legal-incomplete-binding")
        binding = value["input"]["transaction"][0]["value"]
        self.assertEqual({"slotId": 13, "A": None, "B": None, "contactFace": None, "orientation": None}, binding["slots"][1])
        self.assertEqual("accepted", value["expect"]["outcome"])
        self.assertIn({"kind": "complete_flag", "ref": {"kind": "binding", "id": 29}, "value": False}, value["assertions"])

    def test_immutable_case_keeps_identity_even_after_rename_and_array_reordering(self):
        value = case("fixed-version-immutable")
        old = value["input"]["setup"][0]["value"]
        candidate = value["input"]["transaction"][0]["value"]
        self.assertEqual((17, 1), (candidate["id"], candidate["version"]))
        self.assertNotEqual(old["name"], candidate["name"])
        for field in ("slots", "members", "joints"):
            self.assertEqual(list(reversed(old[field])), candidate[field])
        self.assertEqual({"code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
                          "ref": {"kind": "rule", "id": 17, "version": 1}}, value["expect"]["diagnostic"])


class RuleCaseCatalogNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The existing registry builds/verifies native source closure and bytes.
        # No fixture mocks or unverified web_bridge.exe fallback are involved.
        cls.executor = NativeExecutor(find_bridge(), timeout_seconds=5)
        cls.receipts = {value["caseId"]: cls.executor.run(
            value, project_id="independent-catalog-oracle", generation=1) for value in cases()}

    def test_six_true_native_runs_keep_precise_negative_diagnostic_gaps_nonpass(self):
        expected = {
            "same-role-distinct-members": "passed", "one-local-joint-new-version": "passed",
            "wrong-type-dimension-reference": "blocked", "legal-rule": "passed",
            "legal-incomplete-binding": "passed", "fixed-version-immutable": "blocked",
        }
        pids = []
        for case_id, status in expected.items():
            receipt = self.receipts[case_id]
            with self.subTest(case=case_id):
                self.assertEqual(status, receipt["status"], receipt)
                self.assertTrue(receipt["executor"]["known"])
                self.assertTrue(receipt["conditions"]["isolated"])
                self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])
                self.assertIsInstance(receipt["conditions"]["nativePid"], int)
                self.assertTrue(all(item["passed"] for item in receipt["assertionResults"]))
                if status == "blocked":
                    self.assertEqual("diagnostic-unavailable", receipt["reason"])
                pids.append(receipt["conditions"]["nativePid"])
        self.assertEqual(6, len(set(pids)), "Each run requires a fresh native process")

    def test_same_role_native_records_match_independent_literal_oracle(self):
        observations = self.receipts["same-role-distinct-members"]["observations"]
        self.assertEqual([], observations["before"]["rules"])
        value = record(observations["after"], "rule", 17, 1)["value"]
        self.assertEqual({11: 7, 37: 7, 89: 13},
                         {member["id"]: member["slotId"] for member in value["members"]})
        self.assertEqual({
            101: ("end-to-side", "left", 89, 11, "start", "+u", "u"),
            203: ("end-to-side", "right", 89, 37, "finish", "-u", "u"),
        }, {joint["id"]: (joint["kind"], joint["scope"], joint["terminatedMember"],
                          joint["targetMember"], joint["end"], joint["side"], joint["dir"])
            for joint in value["joints"]})

    def test_one_joint_native_change_preserves_other_joint_and_fixed_binding(self):
        observations = self.receipts["one-local-joint-new-version"]["observations"]
        before, after = observations["before"], observations["after"]
        self.assertEqual(record(before, "rule", 17, 1), record(after, "rule", 17, 1))
        self.assertEqual(record(before, "binding", 29), record(after, "binding", 29))
        self.assertEqual({"id": 17, "version": 1}, record(after, "binding", 29)["value"]["rule"])
        new = record(after, "rule", 17, 2)["value"]
        self.assertEqual({
            "id": 17, "version": 2, "name": "有限主副支接合",
            "slots": [{"id": 7, "name": "主支"}, {"id": 13, "name": "副支"}],
            "members": [{"id": 11, "slotId": 7}, {"id": 37, "slotId": 7}, {"id": 89, "slotId": 13}],
            "joints": [
                {"id": 101, "kind": "end-to-side", "scope": "left", "terminatedMember": 89,
                 "targetMember": 11, "end": "start", "side": "-u", "dir": "u"},
                {"id": 203, "kind": "end-to-side", "scope": "right", "terminatedMember": 89,
                 "targetMember": 37, "end": "finish", "side": "-u", "dir": "u"},
            ],
        }, new)
        self.assertEqual({
            101: (89, 11, "start", "-u"),
            203: (89, 37, "finish", "-u"),
        }, {joint["id"]: (joint["terminatedMember"], joint["targetMember"], joint["end"], joint["side"])
            for joint in new["joints"]})
        old_joints = {joint["id"]: joint for joint in record(before, "rule", 17, 1)["value"]["joints"]}
        new_joints = {joint["id"]: joint for joint in new["joints"]}
        self.assertEqual(old_joints[203], new_joints[203])
        self.assertNotEqual(old_joints[101], new_joints[101])

    def test_legal_rule_native_accepts_unbound_authoring_definition(self):
        after = self.receipts["legal-rule"]["observations"]["after"]
        self.assertEqual([], after["bindings"])
        value = record(after, "rule", 17, 1)["value"]
        self.assertEqual({11: 7, 89: 13}, {member["id"]: member["slotId"] for member in value["members"]})
        self.assertEqual([101], [joint["id"] for joint in value["joints"]])

    def test_incomplete_native_binding_preserves_null_sources_and_complete_false(self):
        after = self.receipts["legal-incomplete-binding"]["observations"]["after"]
        bound = record(after, "binding", 29)
        self.assertIs(False, bound["complete"])
        slots = {slot["slotId"]: slot for slot in bound["value"]["slots"]}
        self.assertEqual({"slotId": 13, "A": None, "B": None, "contactFace": None, "orientation": None}, slots[13])
        self.assertEqual({"kind": "literal", "value": 27}, slots[7]["A"])

    def test_native_negative_rejections_keep_world_and_revision_and_dump_unchanged(self):
        for case_id in ("wrong-type-dimension-reference", "fixed-version-immutable"):
            receipt = self.receipts[case_id]
            with self.subTest(case=case_id):
                self.assertEqual("rejected", receipt["actualOutcome"])
                observed = receipt["observations"]
                self.assertEqual(observed["before"], observed["after"])
                self.assertEqual(observed["beforeRevision"], observed["afterRevision"])
                self.assertEqual(observed["beforeDumpHash"], observed["afterDumpHash"])
                generic = [item for item in receipt["actualDiagnostics"]
                           if item.get("code") == "ASSEMBLY_INVALID"]
                self.assertEqual(1, len(generic))
                self.assertEqual("I40/I41", generic[0]["clause"])
                self.assertNotIn("ref", generic[0])


if __name__ == "__main__":
    unittest.main()
