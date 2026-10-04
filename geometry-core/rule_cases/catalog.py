"""The six user-adopted finite authoring cases for issue #49.

These are data, not programs: only native typed transaction operations and the
finite assertion vocabulary are supplied.  Expected diagnostics deliberately
remain more precise than the current bridge's generic ASSEMBLY_INVALID reply;
an executor must report diagnostic-unavailable rather than pass either negative
case from a generic rejection.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json


def _hash(value: dict) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ref(kind: str, identifier: int, version: int | None = None) -> dict:
    value = {"kind": kind, "id": identifier}
    if version is not None:
        value["version"] = version
    return value


def _rule(version: int = 1) -> dict:
    return {
        "id": 17, "version": version, "name": "有限主副支接合",
        "slots": [{"id": 7, "name": "主支"}, {"id": 13, "name": "副支"}],
        "members": [{"id": 11, "slotId": 7}, {"id": 37, "slotId": 7},
                    {"id": 89, "slotId": 13}],
        "joints": [
            {"id": 101, "kind": "end-to-side", "scope": "left",
             "terminatedMember": 89, "targetMember": 11, "end": "start",
             "side": "+u", "dir": "u"},
            {"id": 203, "kind": "end-to-side", "scope": "right",
             "terminatedMember": 89, "targetMember": 37, "end": "finish",
             "side": "-u", "dir": "u"},
        ],
    }


def _binding(*, incomplete: bool = False, parameter: bool = False) -> dict:
    value = {
        "id": 29, "name": "固定來源配置", "rule": {"id": 17, "version": 1},
        "slots": [
            {"slotId": slot, "A": {"kind": "literal", "value": 27},
             "B": {"kind": "literal", "value": 33},
             "contactFace": "A", "orientation": "B"}
            for slot in (7, 13)
        ],
    }
    if incomplete:
        value["slots"][1].update(A=None, B=None, contactFace=None, orientation=None)
    if parameter:
        value["slots"][0]["A"] = {"kind": "parameter", "parameterId": 41, "fieldId": 9}
    return value


def _parameter(field_type: str = "dimension") -> dict:
    return {"id": 41, "name": "接合案例尺寸", "fields": [
        {"id": 9, "name": "截面A", "type": field_type, "input": "27"},
    ]}


def _pins(setup: list[dict]) -> list[dict]:
    kinds = {"publish-rule": "rule", "create-binding": "binding",
             "put-parameter": "parameter", "publish-material": "material"}
    result = []
    for operation in setup:
        value = operation["value"]
        kind = kinds[operation["op"]]
        ref = _ref(kind, value["id"], value.get("version") if kind in ("rule", "material") else None)
        result.append({"ref": ref, "sha256": _hash(value)})
    return result


def _case(case_id: str, label: str, setup: list[dict], transaction: list[dict],
          assertions: list[dict], *, diagnostic: dict | None = None,
          parameters: bool = False) -> dict:
    capabilities = ["assembly-rule-authoring/1"]
    if parameters:
        capabilities.extend(["parameters/1", "engineering-spec/1"])
    return {
        "schema": "rule-case/1", "caseId": case_id, "label": label,
        "input": {"setup": setup, "transaction": transaction},
        "sourcePins": _pins(setup), "requiredCapabilities": capabilities,
        "expect": {"outcome": "rejected" if diagnostic else "accepted", "diagnostic": diagnostic},
        "assertions": assertions,
    }


def _joint(ref: dict, joint_id: int, value: dict) -> dict:
    return {"kind": "joint_tuple", "ref": ref, "jointId": joint_id, "value": value}


def _build_cases() -> list[dict]:
    old_rule = _rule()
    fixed_binding = _binding()
    fixed_rule_ref = _ref("rule", 17, 1)
    binding_ref = _ref("binding", 29)
    publish = {"op": "publish-rule", "value": old_rule}
    bind = {"op": "create-binding", "value": fixed_binding}

    # Literal expected tuples are independent of rule array lookup and ordering.
    left = {"id": 101, "kind": "end-to-side", "scope": "left", "terminatedMember": 89,
            "targetMember": 11, "end": "start", "side": "+u", "dir": "u"}
    right = {"id": 203, "kind": "end-to-side", "scope": "right", "terminatedMember": 89,
             "targetMember": 37, "end": "finish", "side": "-u", "dir": "u"}
    member_case = _case(
        "same-role-distinct-members", "同角色的不同構件分開引用", [], [publish], [
            {"kind": "record_exists", "ref": fixed_rule_ref},
            {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 11, "slotId": 7},
            {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 37, "slotId": 7},
            {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 89, "slotId": 13},
            _joint(fixed_rule_ref, 101, left), _joint(fixed_rule_ref, 203, right),
        ])

    newer = _rule(2)
    newer["joints"][0]["side"] = "-u"
    new_rule_ref = _ref("rule", 17, 2)
    joint_case = _case(
        "one-local-joint-new-version", "新版本只改一處接合", [publish, bind],
        [{"op": "publish-rule", "value": newer}], [
            {"kind": "record_exists", "ref": new_rule_ref},
            {"kind": "record_pin_unchanged", "ref": fixed_rule_ref},
            {"kind": "record_pin_unchanged", "ref": binding_ref},
            _joint(new_rule_ref, 101, dict(left, side="-u")),
            {"kind": "joint_tuple_equal", "before": {"ref": fixed_rule_ref, "jointId": 203},
             "after": {"ref": new_rule_ref, "jointId": 203}},
            _joint(new_rule_ref, 203, right),
        ])

    wrong_type_case = _case(
        "wrong-type-dimension-reference", "尺寸引用拒絕計數型別", [
            publish, {"op": "put-parameter", "value": _parameter()},
            {"op": "create-binding", "value": _binding(parameter=True)},
        ], [{"op": "put-parameter", "value": _parameter("count")}], [
            {"kind": "rejection_world_unchanged"},
            {"kind": "record_pin_unchanged", "ref": fixed_rule_ref},
            {"kind": "record_pin_unchanged", "ref": binding_ref},
            {"kind": "exact_typed_ref", "ref": binding_ref, "slotId": 7, "axis": "A",
             "value": {"kind": "parameter", "parameterId": 41, "fieldId": 9}},
        ], diagnostic={"code": "DIMENSION_TYPE", "clause": "D33",
                       "ref": {"kind": "parameter", "id": 41, "fieldId": 9}}, parameters=True)

    legal = _rule()
    legal["members"] = [{"id": 11, "slotId": 7}, {"id": 89, "slotId": 13}]
    legal["joints"] = [deepcopy(left)]
    legal_case = _case("legal-rule", "合法規則可獨立發布", [], [
        {"op": "publish-rule", "value": legal},
    ], [
        {"kind": "record_exists", "ref": fixed_rule_ref},
        {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 11, "slotId": 7},
        {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 89, "slotId": 13},
        _joint(fixed_rule_ref, 101, left),
    ])

    incomplete_case = _case(
        "legal-incomplete-binding", "未選材料方向仍是合法未完成配置", [publish], [
            {"op": "create-binding", "value": _binding(incomplete=True)},
        ], [
            {"kind": "record_exists", "ref": binding_ref},
            {"kind": "record_pin_unchanged", "ref": fixed_rule_ref},
            {"kind": "complete_flag", "ref": binding_ref, "value": False},
            {"kind": "exact_typed_ref", "ref": binding_ref, "slotId": 13, "axis": "A", "value": None},
            {"kind": "exact_typed_ref", "ref": binding_ref, "slotId": 13, "axis": "B", "value": None},
        ])

    renamed_reordered = _rule()
    renamed_reordered["name"] = "改名與重排不能覆寫固定版本"
    for field in ("slots", "members", "joints"):
        renamed_reordered[field].reverse()
    immutable_case = _case(
        "fixed-version-immutable", "改名重排不改固定版本與既有配置", [publish, bind], [
            {"op": "publish-rule", "value": renamed_reordered},
        ], [
            {"kind": "rejection_world_unchanged"},
            {"kind": "record_pin_unchanged", "ref": fixed_rule_ref},
            {"kind": "record_pin_unchanged", "ref": binding_ref},
            {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 11, "slotId": 7},
            {"kind": "member_slot", "ref": fixed_rule_ref, "memberId": 37, "slotId": 7},
            _joint(fixed_rule_ref, 101, left), _joint(fixed_rule_ref, 203, right),
        ], diagnostic={"code": "RULE_VERSION_IMMUTABLE", "clause": "D32", "ref": fixed_rule_ref})

    return deepcopy([member_case, joint_case, wrong_type_case,
                     legal_case, incomplete_case, immutable_case])


_CASES = tuple(deepcopy(value) for value in _build_cases())


def cases() -> list[dict]:
    """Return editable independent copies, in the three-case slice priority order."""
    return [deepcopy(value) for value in _CASES]


def case(case_id: str) -> dict:
    """Return an independent built-in definition; unknown identities raise KeyError."""
    for value in _CASES:
        if value["caseId"] == case_id:
            return deepcopy(value)
    raise KeyError(case_id)
