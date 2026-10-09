"""Adversarial finite-case inputs, independently of the native result oracle."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))

from rule_cases.definition import (
    CaseDefinitionError, MAX_CASE_BYTES, MAX_DEPTH, MAX_NODES, PREDICATE_KINDS,
    canonical, decode_case, definition_hash, digest, validate_case, validate_cases,
)


def rule(version=1):
    return {
        "id": 5, "version": version, "name": "規則",
        "slots": [{"id": 3, "name": "主支"}, {"id": 8, "name": "副支"}],
        "members": [{"id": 17, "slotId": 3}, {"id": 43, "slotId": 8}],
        "joints": [{"id": 71, "kind": "end-to-side", "scope": "first",
                    "terminatedMember": 43, "targetMember": 17, "end": "start",
                    "side": "+u", "dir": "u"}],
    }


def binding():
    return {"id": 12, "name": "配置", "rule": {"id": 5, "version": 1},
            "slots": [{"slotId": slot, "A": {"kind": "literal", "value": 27},
                       "B": None, "contactFace": None, "orientation": None}
                      for slot in (3, 8)]}


def parameter(identifier=0, field_id=0, field_type="dimension", **definition):
    return {"id": identifier, "name": "參數", "fields": [
        dict(id=field_id, name="值", type=field_type, **(definition or {"input": "27"}))]}


def pin_setup(value):
    """Pins computed without importing the production hash function."""
    kinds = {"publish-rule": "rule", "put-binding": "binding", "create-binding": "binding",
             "publish-material": "material", "put-parameter": "parameter"}
    result = deepcopy(value)
    result["sourcePins"] = []
    for operation in result["input"]["setup"]:
        data = operation["value"]
        ref = {"kind": kinds[operation["op"]], "id": data["id"]}
        if ref["kind"] in ("rule", "material"):
            ref["version"] = data["version"]
        encoded = json.dumps(data, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        result["sourcePins"].append({"ref": ref, "sha256": hashlib.sha256(encoded).hexdigest()})
    return result


def sample():
    return {
        "schema": "rule-case/1", "caseId": "independent-case", "label": "有限例",
        "input": {"setup": [], "transaction": [{"op": "publish-rule", "value": rule()}]},
        "sourcePins": [], "requiredCapabilities": ["assembly-rule-authoring/1"],
        "expect": {"outcome": "accepted", "diagnostic": None},
        "assertions": [{"kind": "member_slot", "ref": {"kind": "rule", "id": 5, "version": 1},
                        "memberId": 17, "slotId": 3}],
    }


def with_setup():
    value = sample()
    value["input"] = {"setup": [{"op": "publish-rule", "value": rule()},
                               {"op": "create-binding", "value": binding()}],
                      "transaction": [{"op": "publish-rule", "value": rule(2)}]}
    return pin_setup(value)


class RuleCaseDefinition(unittest.TestCase):
    def rejects(self, value, code="SCHEMA"):
        with self.assertRaises(CaseDefinitionError) as raised:
            validate_case(value)
        self.assertEqual(code, raised.exception.code, str(raised.exception))

    def test_canonical_encoding_and_hash_are_exact_and_key_order_independent(self):
        value = {"字": "尺寸", "a": [True, None, 3]}
        expected = '{"a":[true,null,3],"字":"尺寸"}'.encode("utf-8")
        self.assertEqual(expected, canonical(value))
        self.assertEqual(hashlib.sha256(expected).hexdigest(), digest(value))
        self.assertEqual(digest(value), digest(dict(reversed(list(value.items())))))

    def test_validated_copy_and_decoded_case_do_not_share_mutable_input(self):
        original = sample()
        accepted = validate_case(original)
        self.assertEqual(original, decode_case(canonical(original)))
        accepted["input"]["transaction"][0]["value"]["members"][0]["id"] = 999
        self.assertEqual(17, original["input"]["transaction"][0]["value"]["members"][0]["id"])

    def test_all_definition_fields_including_label_change_hash(self):
        original = sample()
        changes = [
            ("label", "改標題"), ("caseId", "another-case"),
            ("requiredCapabilities", ["assembly-rule-authoring/1", "unknown/1"]),
            ("assertions", [{"kind": "member_slot", "ref": {"kind": "rule", "id": 5, "version": 1},
                             "memberId": 43, "slotId": 8}]),
        ]
        for key, changed in changes:
            with self.subTest(key=key):
                altered = deepcopy(original)
                altered[key] = changed
                self.assertNotEqual(definition_hash(original), definition_hash(altered))
        reordered = dict(reversed(list(original.items())))
        self.assertEqual(definition_hash(original), definition_hash(reordered))

    def test_root_input_operation_and_nested_unknown_keys_reject(self):
        for location in ("root", "input", "operation", "rule", "slot", "member", "joint", "assertion"):
            with self.subTest(location=location):
                value = sample()
                operation = value["input"]["transaction"][0]
                places = {"root": value, "input": value["input"], "operation": operation,
                          "rule": operation["value"], "slot": operation["value"]["slots"][0],
                          "member": operation["value"]["members"][0],
                          "joint": operation["value"]["joints"][0], "assertion": value["assertions"][0]}
                places[location]["script"] = "print('arbitrary')"
                self.rejects(value)
        value = sample()
        del value["input"]["transaction"][0]["value"]["name"]
        self.rejects(value)

    def test_only_finite_typed_operations_and_predicates_are_accepted(self):
        for operation in ("eval", "run", "load-scene", "delete-rule", "copy-rule", "edit-binding"):
            value = sample()
            value["input"]["transaction"][0]["op"] = operation
            self.rejects(value)
        for assertion in ({"kind": "eval", "script": "True"},
                          {"kind": "record_exists", "path": "$.rules[0]"},
                          {"kind": "rejection_world_unchanged", "selector": "*"}):
            value = sample()
            value["assertions"] = [assertion]
            self.rejects(value)
        self.assertEqual(8, len(PREDICATE_KINDS))

    def test_fixed_typed_identities_require_exact_id_scalar_and_versions(self):
        for number in (True, False, 1.0, 0, -1, 4294967296, "5"):
            value = sample()
            value["input"]["transaction"][0]["value"]["id"] = number
            self.rejects(value)
        for ref in ({"kind": "rule", "id": 5},
                    {"kind": "binding", "id": 12, "version": 1},
                    {"kind": "rule", "id": 5, "version": False}):
            value = sample()
            value["assertions"][0]["ref"] = ref
            self.rejects(value)

    def test_uint32_zero_is_legal_for_parameter_and_field_only(self):
        value = sample()
        value["input"]["transaction"].append({"op": "put-parameter", "value": parameter()})
        value["requiredCapabilities"].append("parameters/1")
        self.assertEqual(value, validate_case(value))
        value["input"]["transaction"][-1]["value"]["fields"][0]["id"] = 4294967295
        self.assertEqual(value, validate_case(value))

    def test_pin_set_exactly_covers_setup_and_hashes_exact_input_representation(self):
        value = with_setup()
        self.assertEqual(value, validate_case(value))
        for change in ("missing", "duplicate", "outside", "mismatch", "uppercase"):
            altered = deepcopy(value)
            with self.subTest(change=change):
                if change == "missing":
                    altered["sourcePins"].pop()
                elif change == "duplicate":
                    altered["sourcePins"].append(deepcopy(altered["sourcePins"][0]))
                elif change == "outside":
                    altered["sourcePins"][0]["ref"]["version"] = 2
                elif change == "mismatch":
                    altered["input"]["setup"][0]["value"]["name"] = "新名稱"
                else:
                    altered["sourcePins"][0]["sha256"] = altered["sourcePins"][0]["sha256"].upper()
                self.rejects(altered, "PIN")
        value["input"]["setup"].append(deepcopy(value["input"]["setup"][0]))
        self.rejects(value, "CLOSURE")

    def test_unchanged_predicate_requires_a_pinned_before_record(self):
        value = sample()
        value["assertions"] = [{"kind": "record_pin_unchanged",
                                "ref": {"kind": "rule", "id": 5, "version": 1}}]
        self.rejects(value, "PIN")
        value = with_setup()
        value["assertions"] = [{"kind": "record_pin_unchanged", "ref": {"kind": "binding", "id": 12}}]
        self.assertEqual(value, validate_case(value))

    def test_missing_external_rule_or_parameter_field_is_a_closure_error(self):
        value = sample()
        value["input"]["transaction"] = [{"op": "create-binding", "value": binding()}]
        value["assertions"] = [{"kind": "record_exists", "ref": {"kind": "binding", "id": 12}}]
        self.rejects(value, "CLOSURE")
        value = with_setup()
        value["input"]["transaction"].append({"op": "put-parameter", "value": parameter()})
        value["requiredCapabilities"].append("parameters/1")
        bound = value["input"]["setup"][1]["value"]
        bound["slots"][0]["A"] = {"kind": "parameter", "parameterId": 0, "fieldId": 99}
        self.rejects(pin_setup(value), "CLOSURE")

    def test_setup_cannot_borrow_a_source_introduced_only_by_transaction(self):
        value = sample()
        value["input"]["setup"] = [{"op": "create-binding", "value": binding()}]
        # The rule exists in the combined operation list, but cannot supply
        # the baseline binding before the tested transaction runs.
        self.rejects(pin_setup(value), "CLOSURE")
        # Forward references inside the same atomic setup remain supported.
        value["input"]["setup"].append({"op": "publish-rule", "value": rule()})
        self.assertEqual(pin_setup(value), validate_case(pin_setup(value)))

    def test_binding_source_rejects_scripts_paths_specs_and_unknown_nested_fields(self):
        for source in ({"kind": "spec", "name": "legacy"}, {"kind": "script", "value": "27"},
                       {"kind": "literal", "value": 27, "path": "/tmp/program"},
                       {"kind": "parameter", "parameterId": 0, "fieldId": 0, "selector": "*"}):
            value = with_setup()
            value["input"]["setup"][1]["value"]["slots"][0]["A"] = source
            self.rejects(pin_setup(value))

    def test_material_source_closure_and_numeric_bound(self):
        value = with_setup()
        material = {"id": "timber-A", "version": 7, "name": "角材", "kind": "timber", "A": 27, "B": 33}
        value["input"]["setup"][1]["value"]["slots"][0]["A"] = {
            "kind": "material", "id": "timber-A", "version": 7, "field": "A"}
        value["input"]["setup"].append({"op": "publish-material", "value": material})
        value["requiredCapabilities"].append("engineering-spec/1")
        value = pin_setup(value)
        self.assertEqual(value, validate_case(value))
        altered = deepcopy(value)
        altered["input"]["setup"][1]["value"]["slots"][0]["A"]["version"] = 8
        self.rejects(pin_setup(altered), "CLOSURE")
        value["input"]["setup"][-1]["value"]["A"] = 100000001
        self.rejects(value)

    def test_parameter_native_input_tokenization_collects_typed_closure_without_eval(self):
        value = sample()
        value["input"]["transaction"].extend([
            {"op": "put-parameter", "value": parameter()},
            {"op": "put-parameter", "value": parameter(9, 2, input="＝(@0:0 + 2 mm) / 3")},
        ])
        value["requiredCapabilities"].append("parameters/1")
        self.assertEqual(value, validate_case(value))
        value["input"]["transaction"][-1]["value"]["fields"][0]["input"] = "=@0:999 + 2 mm"
        self.rejects(value, "CLOSURE")
        for script in ("__import__('os')", "alert(1)", "=Math.max(2,3)", "=1;print(2)",
                       "@/tmp/file:0", "@4294967296:0", "1e10", "=foo", "\x00"):
            with self.subTest(script=script):
                value["input"]["transaction"][-1]["value"]["fields"][0]["input"] = script
                self.rejects(value)

    def test_finite_parameter_ast_and_nested_reference_closure(self):
        literal = {"op": "literal", "num": "2", "den": "1", "unit": "mm"}
        expression = {"op": "add", "left": {"op": "ref", "parameterId": 0, "fieldId": 0},
                      "right": literal}
        value = sample()
        value["input"]["transaction"].extend([
            {"op": "put-parameter", "value": parameter()},
            {"op": "put-parameter", "value": parameter(9, 2, expression=expression)},
        ])
        value["requiredCapabilities"].append("parameters/1")
        self.assertEqual(value, validate_case(value))
        for op in ("eval", "call", [], {}, True):
            with self.subTest(op=op):
                altered = deepcopy(value)
                altered["input"]["transaction"][-1]["value"]["fields"][0]["expression"]["op"] = op
                self.rejects(altered)
        altered = deepcopy(value)
        altered["input"]["transaction"][-1]["value"]["fields"][0]["expression"]["left"]["fieldId"] = 99
        self.rejects(altered, "CLOSURE")
        altered = deepcopy(value)
        altered["input"]["transaction"][-1]["value"]["fields"][0]["input"] = "2"
        self.rejects(altered)

    def test_native_domain_errors_are_not_mistaken_for_definition_errors(self):
        # Conflicting member roles, immutable overwrite, bad units, and cycles
        # remain native decisions rather than a parallel geometry evaluator.
        value = with_setup()
        value["input"]["transaction"][0]["value"]["version"] = 1
        value["input"]["transaction"][0]["value"]["name"] = "不可覆寫"
        value["expect"] = {"outcome": "rejected", "diagnostic": {
            "code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
            "ref": {"kind": "rule", "id": 5, "version": 1}}}
        self.assertEqual(value, validate_case(value))
        value = sample()
        value["input"]["transaction"].append({"op": "put-parameter", "value": parameter(
            field_type="count", expression={"op": "ref", "parameterId": 0, "fieldId": 0})})
        value["requiredCapabilities"].append("parameters/1")
        self.assertEqual(value, validate_case(value))

    def test_capability_declarations_are_complete_and_unique(self):
        value = sample()
        value["requiredCapabilities"] = []
        self.rejects(value, "CLOSURE")
        value = sample()
        value["requiredCapabilities"].append("assembly-rule-authoring/1")
        self.rejects(value)
        value = sample()
        value["requiredCapabilities"].append("future-runtime/2")
        self.assertEqual(value, validate_case(value))
        value["requiredCapabilities"][-1] = "run shell command"
        self.rejects(value)

    def test_parameter_and_material_capabilities_cannot_be_stripped(self):
        for operation, capability in (
            ({"op": "put-parameter", "value": parameter()}, "parameters/1"),
            ({"op": "publish-material", "value": {"id": "wood", "version": 1,
              "kind": "timber", "name": "木", "A": 27, "B": 33}}, "engineering-spec/1"),
        ):
            value = sample()
            value["input"]["transaction"].append(operation)
            self.rejects(value, "CLOSURE")
            value["requiredCapabilities"].append(capability)
            self.assertEqual(value, validate_case(value))

    def test_predicate_selectors_are_finite_and_present_in_closure(self):
        value = sample()
        value["assertions"][0]["memberId"] = 999
        self.rejects(value, "CLOSURE")
        value["assertions"][0]["memberId"] = 17
        value["assertions"][0]["slotId"] = 999
        self.rejects(value, "CLOSURE")
        value = with_setup()
        value["assertions"] = [{"kind": "complete_flag", "ref": {"kind": "binding", "id": 12}, "value": 0}]
        self.rejects(value)
        value["assertions"][0]["value"] = False
        self.assertEqual(value, validate_case(value))

    def test_joint_tuple_is_full_typed_and_id_matched(self):
        value = sample()
        value["assertions"] = [{"kind": "joint_tuple", "ref": {"kind": "rule", "id": 5, "version": 1},
                                "jointId": 71, "value": deepcopy(rule()["joints"][0])}]
        self.assertEqual(value, validate_case(value))
        for change in ("missing", "mismatched", "unknown"):
            altered = deepcopy(value)
            if change == "missing":
                del altered["assertions"][0]["value"]["targetMember"]
            elif change == "mismatched":
                altered["assertions"][0]["value"]["id"] = 72
            else:
                altered["assertions"][0]["value"]["kind"] = "arbitrary-joint"
            self.rejects(altered)

    def test_exact_diagnostic_has_typed_ref_and_cannot_be_attached_to_acceptance(self):
        value = with_setup()
        value["expect"]["diagnostic"] = {"code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
                                          "ref": {"kind": "rule", "id": 5, "version": 1}}
        self.rejects(value)
        value["expect"]["outcome"] = "rejected"
        self.assertEqual(value, validate_case(value))
        del value["expect"]["diagnostic"]["ref"]
        self.rejects(value)

    def test_vacuous_transactions_assertions_and_nonspecific_rejection_reject(self):
        value = sample()
        value["input"]["transaction"] = []
        self.rejects(value)
        value = sample()
        value["assertions"] = []
        self.rejects(value)
        value = sample()
        value["expect"]["outcome"] = "rejected"
        self.rejects(value)

    def test_case_count_and_identity_are_bounded(self):
        self.assertEqual([], validate_cases([]))
        values = [dict(sample(), caseId=f"case-{i}") for i in range(6)]
        self.assertEqual(values, validate_cases(values))
        with self.assertRaises(CaseDefinitionError) as raised:
            validate_cases(values + [sample()])
        self.assertEqual("CAPACITY", raised.exception.code)
        with self.assertRaises(CaseDefinitionError) as raised:
            validate_cases([sample(), sample()])
        self.assertEqual("SCHEMA", raised.exception.code)

    def test_operation_assertion_and_utf8_label_limits(self):
        value = sample()
        value["input"]["transaction"] *= 33
        self.rejects(value, "CAPACITY")
        value = sample()
        value["assertions"] *= 33
        self.rejects(value, "CAPACITY")
        value = sample()
        value["label"] = "字" * 32  # 96 UTF-8 bytes, not 96 characters.
        self.assertEqual(value, validate_case(value))
        value["label"] += "字"
        self.rejects(value, "CAPACITY")
        value["label"] = "newline\nlabel"
        self.rejects(value)

    def test_json_scalar_types_cycles_and_budget_fail_closed(self):
        for item in (1.0, float("nan"), float("inf"), (1, 2), object(), {1: "key"}, "\ud800"):
            with self.subTest(type=type(item).__name__):
                with self.assertRaises(CaseDefinitionError):
                    canonical(item)
        for item in ([0] * MAX_NODES, {str(i): 0 for i in range(MAX_NODES)}):
            with self.assertRaises(CaseDefinitionError) as raised:
                canonical(item)
            self.assertEqual("CAPACITY", raised.exception.code)
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(CaseDefinitionError) as raised:
            canonical(cycle)
        self.assertEqual("CAPACITY", raised.exception.code)
        with self.assertRaises(CaseDefinitionError) as raised:
            canonical("x" * MAX_CASE_BYTES)
        self.assertEqual("CAPACITY", raised.exception.code)
        with self.assertRaises(CaseDefinitionError) as raised:
            canonical(["x" * 40000, "y" * 40000])
        self.assertEqual("CAPACITY", raised.exception.code)

    def test_decode_rejects_duplicate_keys_even_nested_or_escaped(self):
        encoded = canonical(sample())
        for data in (
            encoded.replace(b'"schema":"rule-case/1"', b'"schema":"rule-case/1","schema":"rule-case/1"'),
            encoded.replace(b'"slotId":3', b'"slotId":3,"slot\\u0049d":3', 1),
        ):
            with self.subTest(data=data):
                with self.assertRaises(CaseDefinitionError) as raised:
                    decode_case(data)
                self.assertEqual("SCHEMA", raised.exception.code)
                self.assertIn("duplicate JSON key", str(raised.exception))

    def test_decode_rejects_bad_utf8_nonjson_float_nan_and_oversized_input(self):
        for data in (b"\xff", b"\xef\xbb\xbf{}", b"{} trailing", b"{",
                     b'{"n":NaN}', b'{"n":Infinity}', b'{"n":1.0}', b'{"n":1e2}'):
            with self.subTest(data=data):
                with self.assertRaises(CaseDefinitionError) as raised:
                    decode_case(data)
                self.assertEqual("SCHEMA", raised.exception.code)
        for data in (b" " * (MAX_CASE_BYTES + 1),
                     b"[" * (MAX_DEPTH + 2) + b"0" + b"]" * (MAX_DEPTH + 2),
                     b"1" * 5000):
            with self.assertRaises(CaseDefinitionError) as raised:
                decode_case(data)
            self.assertEqual("CAPACITY", raised.exception.code)
        with self.assertRaises(CaseDefinitionError):
            decode_case(canonical(sample()).decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
