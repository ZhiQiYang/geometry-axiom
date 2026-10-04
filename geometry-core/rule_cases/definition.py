"""Bounded data-only rule-case/1 definitions for isolated native execution.

validate_case returns a detached definition or raises CaseDefinitionError with
code SCHEMA, CAPACITY, CLOSURE, or PIN. decode_case also rejects duplicate JSON
keys. validate_cases accepts at most six unique case IDs. canonical encodes
strict integer-only JSON; digest hashes it. definition_hash includes all keys,
including the label, so even editorial definition changes stale a receipt.

Parameter input is tokenized only to check source closure, never evaluated.
Native validation decides arithmetic, units, completeness, joint conflicts,
immutability, and candidate acceptance. Source pins hash the exact setup value
(including input/AST representation), not a normalized native definition.
"""

from copy import deepcopy
import hashlib
import json
import re

SCHEMA = "rule-case/1"
MAX_CASE_BYTES = 65536
MAX_DEPTH = 16
MAX_NODES = 4096
MAX_ASSERTIONS = 32
MAX_OPERATIONS = 32  # Independently for setup and transaction.
MAX_CASES = 6
UINT32_MAX = 4294967295
INT64_MAX = 9223372036854775807
MAX_MM = 100000000
PREDICATE_KINDS = frozenset({
    "record_exists", "member_slot", "joint_tuple", "joint_tuple_equal",
    "complete_flag", "exact_typed_ref", "record_pin_unchanged",
    "rejection_world_unchanged",
})
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_CAPABILITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,95}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_INTEGER_TEXT = re.compile(r"-?[0-9]+\Z")
_INPUT_TOKEN = re.compile(
    r"(?P<ref>@(?P<card>[0-9]+):(?P<field>[0-9]+))|"
    r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)|mm|[=＝()+\-−*×/÷]|[ \t\r\n]+"
)


class CaseDefinitionError(ValueError):
    """Invalid finite definition, with a machine-readable failure-domain code."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _fail(code, path, message):
    raise CaseDefinitionError(code, f"{path}: {message}")


def _json_tree(value):
    # Bound work before recursive encoding/deepcopy. Exact builtin types avoid
    # invoking custom mapping/string/number implementations.
    pending, nodes = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            _fail("CAPACITY", "$", "JSON node/depth limit exceeded")
        if type(item) is dict:
            if len(item) * 2 > MAX_NODES - nodes - len(pending):
                _fail("CAPACITY", "$", "object exceeds remaining JSON node budget")
            if any(type(key) is not str for key in item):
                _fail("SCHEMA", "$", "object keys must be strings")
            pending.extend((child, depth + 1) for child in item.values())
            pending.extend((key, depth + 1) for key in item)
        elif type(item) is list:
            if len(item) > MAX_NODES - nodes - len(pending):
                _fail("CAPACITY", "$", "array exceeds remaining JSON node budget")
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            try:
                size = len(item.encode("utf-8"))
            except UnicodeEncodeError:
                _fail("SCHEMA", "$", "strings must be valid UTF-8")
            if size > MAX_CASE_BYTES:
                _fail("CAPACITY", "$", "string exceeds case byte limit")
        elif type(item) is int:
            if not -INT64_MAX <= item <= INT64_MAX:
                _fail("SCHEMA", "$", "integer exceeds signed 64-bit range")
        elif item is not None and type(item) is not bool:
            _fail("SCHEMA", "$", "unsupported JSON value type (floats are forbidden)")


def canonical(value):
    """Sorted-key, whitespace-free UTF-8 JSON; floats/NaN are forbidden."""
    _json_tree(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_CASE_BYTES:
        _fail("CAPACITY", "$", "canonical JSON exceeds case byte limit")
    return encoded


def digest(value):
    """Lowercase SHA-256 of canonical(value)."""
    return hashlib.sha256(canonical(value)).hexdigest()


def _object(value, required, optional=(), path="$"):
    if type(value) is not dict:
        _fail("SCHEMA", path, "expected an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        _fail("SCHEMA", path, f"missing keys {sorted(missing)}; unknown keys {sorted(unknown)}")


def _array(value, maximum, path, minimum=0):
    if type(value) is not list:
        _fail("SCHEMA", path, "expected an array")
    if len(value) > maximum:
        _fail("CAPACITY", path, f"at most {maximum} entries are allowed")
    if len(value) < minimum:
        _fail("SCHEMA", path, f"at least {minimum} entries are required")


def _text(value, path, maximum=96, minimum=1, controls=False):
    if type(value) is not str:
        _fail("SCHEMA", path, "expected a string")
    size = len(value.encode("utf-8"))
    if size > maximum:
        _fail("CAPACITY", path, f"string exceeds {maximum} UTF-8 bytes")
    if size < minimum or (not controls and any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)):
        _fail("SCHEMA", path, "empty string or control character")


def _integer(value, path, minimum=0, maximum=UINT32_MAX):
    if type(value) is not int or not minimum <= value <= maximum:
        _fail("SCHEMA", path, f"expected integer in {minimum}..{maximum}")


def _enum(value, choices, path, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or value not in choices:
        _fail("SCHEMA", path, f"expected one of {sorted(choices)}")


def _identifier(value, path):
    if type(value) is not str or not _ID.fullmatch(value):
        _fail("SCHEMA", path, "expected a 1..64 byte ASCII identity")


def _ref(value, path, record=False, diagnostic=False):
    extras = ("version", "fieldId", "slotId", "axis") if diagnostic else ("version",)
    _object(value, ("kind", "id"), extras, path)
    _enum(value["kind"], {"rule", "binding"} if record else
          {"rule", "binding", "parameter", "material"}, path + ".kind")
    kind = value["kind"]
    if kind == "material":
        _identifier(value["id"], path + ".id")
    else:
        _integer(value["id"], path + ".id", 0 if kind == "parameter" else 1)
    if kind in {"rule", "material"}:
        if "version" not in value:
            _fail("SCHEMA", path, "fixed rule/material version required")
        _integer(value["version"], path + ".version", 1)
    elif "version" in value:
        _fail("SCHEMA", path, "unversioned record cannot carry version")
    if diagnostic:
        for key in ("fieldId", "slotId"):
            if key in value:
                _integer(value[key], path + "." + key, 0 if key == "fieldId" else 1)
        if "axis" in value:
            _enum(value["axis"], {"A", "B"}, path + ".axis")
        if "fieldId" in value and kind != "parameter":
            _fail("SCHEMA", path, "fieldId requires a parameter ref")
        if ("slotId" in value or "axis" in value) and kind != "binding":
            _fail("SCHEMA", path, "slotId/axis require a binding ref")
    return kind, value["id"], value.get("version")


def _source(value, path, refs, capabilities):
    if value is None:
        return
    _object(value, ("kind",), ("value", "parameterId", "fieldId", "id", "version", "field"), path)
    kind = value["kind"]
    if kind == "literal":
        _object(value, ("kind", "value"), path=path)
        _integer(value["value"], path + ".value", -MAX_MM, MAX_MM)
    elif kind == "parameter":
        _object(value, ("kind", "parameterId", "fieldId"), path=path)
        _integer(value["parameterId"], path + ".parameterId")
        _integer(value["fieldId"], path + ".fieldId")
        refs.append((("parameter", value["parameterId"], None), "field", value["fieldId"], path))
        capabilities.add("parameters/1")
    elif kind == "material":
        _object(value, ("kind", "id", "version", "field"), path=path)
        _identifier(value["id"], path + ".id")
        _integer(value["version"], path + ".version", 1)
        _enum(value["field"], {"A", "B", "width", "length"}, path + ".field")
        refs.append((("material", value["id"], value["version"]), "material_field", value["field"], path))
        capabilities.add("engineering-spec/1")
    else:
        _fail("SCHEMA", path, "only literal, parameter, material or null sources are supported")


def _joint(value, path):
    _object(value, ("id", "kind", "scope", "side", "dir"),
            ("terminatedMember", "targetMember", "end", "continuousMember", "splitMembers"), path)
    _integer(value["id"], path + ".id", 1)
    _text(value["scope"], path + ".scope", 64)
    _enum(value["side"], {"+u", "-u", "+v", "-v"}, path + ".side")
    _enum(value["dir"], {"u", "v"}, path + ".dir")
    if value["kind"] == "end-to-side":
        _object(value, ("id", "kind", "scope", "side", "dir", "terminatedMember", "targetMember", "end"), path=path)
        for key in ("terminatedMember", "targetMember"):
            _integer(value[key], path + "." + key, 1)
        _enum(value["end"], {"start", "finish"}, path + ".end")
    elif value["kind"] == "ortho-split":
        _object(value, ("id", "kind", "scope", "side", "dir", "continuousMember", "splitMembers"), path=path)
        _integer(value["continuousMember"], path + ".continuousMember", 1)
        _array(value["splitMembers"], 2, path + ".splitMembers", 2)
        for member in value["splitMembers"]:
            _integer(member, path + ".splitMembers", 1)
    else:
        _fail("SCHEMA", path, "unknown joint kind")


def _expression(value, path, refs, counter):
    counter[0] += 1
    if counter[0] > 128:
        _fail("CAPACITY", path, "at most 128 expression nodes are allowed")
    _object(value, ("op",), ("num", "den", "unit", "parameterId", "fieldId", "left", "right"), path)
    op = value["op"]
    if op == "literal":
        _object(value, ("op", "num", "den", "unit"), path=path)
        for key in ("num", "den"):
            number = value[key]
            if (type(number) is not str or not _INTEGER_TEXT.fullmatch(number)
                    or len(number) > 20 or abs(int(number)) > INT64_MAX):
                _fail("SCHEMA", path + "." + key, "expected bounded decimal integer string")
        _enum(value["unit"], {"mm", "1"}, path + ".unit")
    elif op == "ref":
        _object(value, ("op", "parameterId", "fieldId"), path=path)
        _integer(value["parameterId"], path + ".parameterId")
        _integer(value["fieldId"], path + ".fieldId")
        refs.append((("parameter", value["parameterId"], None), "field", value["fieldId"], path))
    elif op in {"add", "sub", "mul", "div", "neg"}:
        _object(value, ("op", "left") if op == "neg" else ("op", "left", "right"), path=path)
        _expression(value["left"], path + ".left", refs, counter)
        if op != "neg":
            _expression(value["right"], path + ".right", refs, counter)
    else:
        _fail("SCHEMA", path, "unknown expression operation")


def _parameter_input(value, path, refs):
    _text(value, path, 2047, controls=True)
    offset = 0
    while offset < len(value):
        match = _INPUT_TOKEN.match(value, offset)
        if not match:
            _fail("SCHEMA", path, "parameter input contains an unknown token")
        if match.group("ref"):
            for name in ("card", "field"):
                token = match.group(name)
                if len(token) > 10 or int(token) > UINT32_MAX:
                    _fail("SCHEMA", path, "parameter reference exceeds uint32 range")
            refs.append((("parameter", int(match.group("card")), None),
                         "field", int(match.group("field")), path))
        offset = match.end()


def _operation(value, path, refs, capabilities):
    _object(value, ("op", "value"), path=path)
    op, data = value["op"], value["value"]
    _enum(op, {"publish-rule", "publish-material", "put-parameter", "create-binding", "put-binding"}, path + ".op")
    p = path + ".value"
    if op == "publish-rule":
        capabilities.add("assembly-rule-authoring/1")
        _object(data, ("id", "version", "name", "slots", "members", "joints"), path=p)
        _integer(data["id"], p + ".id", 1)
        _integer(data["version"], p + ".version", 1)
        _text(data["name"], p + ".name")
        for key, bound in (("slots", 8), ("members", 12), ("joints", 16)):
            _array(data[key], bound, p + "." + key, 1)
        for index, slot in enumerate(data["slots"]):
            q = f"{p}.slots[{index}]"
            _object(slot, ("id", "name"), path=q)
            _integer(slot["id"], q + ".id", 1)
            _text(slot["name"], q + ".name")
        for index, member in enumerate(data["members"]):
            q = f"{p}.members[{index}]"
            _object(member, ("id", "slotId"), path=q)
            _integer(member["id"], q + ".id", 1)
            _integer(member["slotId"], q + ".slotId", 1)
        for index, joint in enumerate(data["joints"]):
            _joint(joint, f"{p}.joints[{index}]")
        identity = ("rule", data["id"], data["version"])
    elif op in {"create-binding", "put-binding"}:
        capabilities.add("assembly-rule-authoring/1")
        _object(data, ("id", "name", "rule", "slots"), path=p)
        _integer(data["id"], p + ".id", 1)
        _text(data["name"], p + ".name")
        _object(data["rule"], ("id", "version"), path=p + ".rule")
        _integer(data["rule"]["id"], p + ".rule.id", 1)
        _integer(data["rule"]["version"], p + ".rule.version", 1)
        refs.append((("rule", data["rule"]["id"], data["rule"]["version"]), None, None, p + ".rule"))
        _array(data["slots"], 8, p + ".slots", 1)
        for index, slot in enumerate(data["slots"]):
            q = f"{p}.slots[{index}]"
            _object(slot, ("slotId", "A", "B", "contactFace", "orientation"), path=q)
            _integer(slot["slotId"], q + ".slotId", 1)
            for axis in ("A", "B"):
                _source(slot[axis], q + "." + axis, refs, capabilities)
            _enum(slot["contactFace"], {"A", "B"}, q + ".contactFace", True)
            _enum(slot["orientation"], {"A", "B"}, q + ".orientation", True)
        identity = ("binding", data["id"], None)
    elif op == "put-parameter":
        capabilities.add("parameters/1")
        _object(data, ("id", "name", "fields"), ("nextFieldId",), p)
        _integer(data["id"], p + ".id")
        _text(data["name"], p + ".name")
        if "nextFieldId" in data:
            _integer(data["nextFieldId"], p + ".nextFieldId")
        _array(data["fields"], 16, p + ".fields", 1)
        for index, field in enumerate(data["fields"]):
            q = f"{p}.fields[{index}]"
            _object(field, ("id", "name", "type"), ("input", "expression"), q)
            if ("input" in field) == ("expression" in field):
                _fail("SCHEMA", q, "exactly one input or expression is required")
            _integer(field["id"], q + ".id")
            _text(field["name"], q + ".name")
            _enum(field["type"], {"dimension", "count", "ratio"}, q + ".type")
            if "input" in field:
                _parameter_input(field["input"], q + ".input", refs)
            else:
                _expression(field["expression"], q + ".expression", refs, [0])
                if len(canonical(field["expression"])) > 2047:
                    _fail("CAPACITY", q, "expression exceeds 2047 UTF-8 bytes")
        identity = ("parameter", data["id"], None)
    else:
        capabilities.add("engineering-spec/1")
        _object(data, ("id", "version", "kind", "name"),
                ("A", "B", "width", "length", "thickness", "brand", "model", "notes"), p)
        _enum(data["kind"], {"timber", "panel"}, p + ".kind")
        dimensions = ("A", "B") if data["kind"] == "timber" else ("width", "length")
        _object(data, ("id", "version", "kind", "name") + dimensions,
                ("brand", "model", "notes") + (() if data["kind"] == "timber" else ("thickness",)), p)
        _identifier(data["id"], p + ".id")
        _integer(data["version"], p + ".version", 1)
        _text(data["name"], p + ".name")
        for key in dimensions:
            _integer(data[key], p + "." + key, -MAX_MM, MAX_MM)
        for key in ("brand", "model", "notes", "thickness"):
            if key in data and data[key] is not None:
                _text(data[key], p + "." + key, 127 if key == "thickness" else 191, minimum=0)
        identity = ("material", data["id"], data["version"])
    limit = 1023 if op == "publish-material" else MAX_CASE_BYTES if op == "put-parameter" else 8191
    if len(canonical(data)) > limit:
        _fail("CAPACITY", p, "native record byte limit exceeded")
    return identity, data


def _assertion(value, path, refs, pins, capabilities):
    _object(value, ("kind",), ("ref", "memberId", "slotId", "jointId", "value", "before", "after", "axis"), path)
    kind = value["kind"]
    _enum(kind, PREDICATE_KINDS, path + ".kind")
    fields = {
        "record_exists": ("ref",), "member_slot": ("ref", "memberId", "slotId"),
        "joint_tuple": ("ref", "jointId", "value"), "joint_tuple_equal": ("before", "after"),
        "complete_flag": ("ref", "value"), "exact_typed_ref": ("ref", "slotId", "axis", "value"),
        "record_pin_unchanged": ("ref",), "rejection_world_unchanged": (),
    }[kind]
    _object(value, ("kind",) + fields, path=path)
    if kind == "rejection_world_unchanged":
        return
    capabilities.add("assembly-rule-authoring/1")
    if kind == "joint_tuple_equal":
        for key in ("before", "after"):
            side = value[key]
            _object(side, ("ref", "jointId"), path=path + "." + key)
            identity = _ref(side["ref"], path + "." + key + ".ref", record=True)
            if identity[0] != "rule":
                _fail("SCHEMA", path, "joint predicates require a rule ref")
            _integer(side["jointId"], path + "." + key + ".jointId", 1)
            refs.append((identity, "joint", side["jointId"], path + "." + key))
        return
    identity = _ref(value["ref"], path + ".ref", record=True)
    refs.append((identity, None, None, path))
    if kind in {"member_slot", "joint_tuple"} and identity[0] != "rule":
        _fail("SCHEMA", path, "member/joint predicates require a rule ref")
    if kind in {"complete_flag", "exact_typed_ref"} and identity[0] != "binding":
        _fail("SCHEMA", path, "binding predicate requires a binding ref")
    if kind == "member_slot":
        for key in ("memberId", "slotId"):
            _integer(value[key], path + "." + key, 1)
        refs.extend(((identity, "member", value["memberId"], path), (identity, "slot", value["slotId"], path)))
    elif kind == "joint_tuple":
        _integer(value["jointId"], path + ".jointId", 1)
        _joint(value["value"], path + ".value")
        if value["value"]["id"] != value["jointId"]:
            _fail("SCHEMA", path, "joint tuple ID must match jointId")
        refs.append((identity, "joint", value["jointId"], path))
    elif kind == "complete_flag":
        if type(value["value"]) is not bool:
            _fail("SCHEMA", path, "complete flag must be boolean")
    elif kind == "exact_typed_ref":
        _integer(value["slotId"], path + ".slotId", 1)
        _enum(value["axis"], {"A", "B"}, path + ".axis")
        _source(value["value"], path + ".value", refs, capabilities)
        refs.append((identity, "slot", value["slotId"], path))
    elif kind == "record_pin_unchanged" and identity not in pins:
        _fail("PIN", path, "unchanged record must have a setup source pin")


def _closure(refs, definitions):
    for identity, selector, target, path in refs:
        records = definitions.get(identity, ())
        if not records:
            _fail("CLOSURE", path, f"missing source {identity}")
        if selector is None:
            continue
        if selector == "material_field":
            found = any(target in record for record in records)
        else:
            list_key = {"field": "fields", "member": "members", "joint": "joints", "slot": "slots"}[selector]
            id_key = "slotId" if identity[0] == "binding" and selector == "slot" else "id"
            found = any(any(item[id_key] == target for item in record[list_key]) for record in records)
        if not found:
            _fail("CLOSURE", path, f"missing {selector} {target} in source {identity}")


def validate_case(value):
    """Validate the full finite case, returning a detached independent copy."""
    canonical(value)
    _object(value, ("schema", "caseId", "label", "input", "sourcePins", "requiredCapabilities", "expect", "assertions"))
    if value["schema"] != SCHEMA:
        _fail("SCHEMA", "$.schema", "unknown case schema")
    _identifier(value["caseId"], "$.caseId")
    _text(value["label"], "$.label")
    _object(value["input"], ("setup", "transaction"), path="$.input")
    refs, capabilities, definitions, setup = [], set(), {}, {}
    for stage in ("setup", "transaction"):
        operations = value["input"][stage]
        _array(operations, MAX_OPERATIONS, "$.input." + stage)
        for index, operation in enumerate(operations):
            path = f"$.input.{stage}[{index}]"
            identity, data = _operation(operation, path, refs, capabilities)
            definitions.setdefault(identity, []).append(data)
            if stage == "setup":
                if identity in setup:
                    _fail("CLOSURE", path, "duplicate setup record identity")
                setup[identity] = data
    _array(value["sourcePins"], MAX_OPERATIONS, "$.sourcePins")
    pins = {}
    for index, pin in enumerate(value["sourcePins"]):
        path = f"$.sourcePins[{index}]"
        _object(pin, ("ref", "sha256"), path=path)
        identity = _ref(pin["ref"], path + ".ref")
        if type(pin["sha256"]) is not str or not _HASH.fullmatch(pin["sha256"]):
            _fail("PIN", path, "expected lowercase SHA-256")
        if identity in pins or identity not in setup:
            _fail("PIN", path, "duplicate pin or pin outside setup")
        if pin["sha256"] != digest(setup[identity]):
            _fail("PIN", path, "source pin does not match exact setup value")
        pins[identity] = pin["sha256"]
    if pins.keys() != setup.keys():
        _fail("PIN", "$.sourcePins", "every setup record requires exactly one source pin")
    _object(value["expect"], ("outcome", "diagnostic"), path="$.expect")
    _enum(value["expect"]["outcome"], {"accepted", "rejected"}, "$.expect.outcome")
    diagnostic = value["expect"]["diagnostic"]
    if diagnostic is not None:
        if value["expect"]["outcome"] != "rejected":
            _fail("SCHEMA", "$.expect", "accepted outcome cannot require a rejection diagnostic")
        _object(diagnostic, ("code", "clause", "ref"), path="$.expect.diagnostic")
        for key in ("code", "clause"):
            _text(diagnostic[key], "$.expect.diagnostic." + key, 64)
        ref = diagnostic["ref"]
        identity = _ref(ref, "$.expect.diagnostic.ref", diagnostic=True)
        refs.append((identity, "field" if "fieldId" in ref else "slot" if "slotId" in ref else None,
                     ref.get("fieldId", ref.get("slotId")), "$.expect.diagnostic.ref"))
    _array(value["assertions"], MAX_ASSERTIONS, "$.assertions")
    for index, assertion in enumerate(value["assertions"]):
        _assertion(assertion, f"$.assertions[{index}]", refs, pins, capabilities)
    _closure(refs, definitions)
    _array(value["requiredCapabilities"], 16, "$.requiredCapabilities")
    declarations = set()
    for capability in value["requiredCapabilities"]:
        if type(capability) is not str or not _CAPABILITY.fullmatch(capability):
            _fail("SCHEMA", "$.requiredCapabilities", "invalid capability identity")
        if capability in declarations:
            _fail("SCHEMA", "$.requiredCapabilities", "duplicate capability")
        declarations.add(capability)
    if not capabilities <= declarations:
        _fail("CLOSURE", "$.requiredCapabilities", f"missing declarations {sorted(capabilities - declarations)}")
    return deepcopy(value)


def decode_case(data):
    """Decode bounded strict UTF-8 JSON, reject duplicate keys, then validate."""
    if type(data) is not bytes:
        _fail("SCHEMA", "$", "decode_case expects bytes")
    if len(data) > MAX_CASE_BYTES:
        _fail("CAPACITY", "$", "input exceeds case byte limit")
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError:
        _fail("SCHEMA", "$", "input is not valid UTF-8")
    # Reject hostile nesting before the JSON decoder can descend into it.
    depth, quoted, escaped = 0, False, False
    for char in source:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH + 1:
                _fail("CAPACITY", "$", "input nesting exceeds depth limit")
        elif char in "]}":
            depth -= 1

    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                _fail("SCHEMA", "$", f"duplicate JSON key {key!r}")
            result[key] = item
        return result

    def integer(text):
        if len(text) > 20:
            _fail("CAPACITY", "$", "numeric token exceeds integer limit")
        return int(text)

    def unsupported_number(_):
        _fail("SCHEMA", "$", "floating-point numbers and constants are forbidden")

    try:
        value = json.loads(source, object_pairs_hook=pairs, parse_int=integer,
                           parse_float=unsupported_number, parse_constant=unsupported_number)
    except (json.JSONDecodeError, RecursionError) as exc:
        _fail("SCHEMA", "$", f"invalid JSON: {exc}")
    return validate_case(value)


def definition_hash(value):
    """Hash all validated definition keys; changing a label changes the hash."""
    return digest(validate_case(value))


def validate_cases(values):
    """Return at most six detached cases; duplicate case identities reject."""
    _array(values, MAX_CASES, "$.cases")
    result, identities = [], set()
    for value in values:
        case = validate_case(value)
        if case["caseId"] in identities:
            _fail("SCHEMA", "$.cases", "duplicate caseId")
        identities.add(case["caseId"])
        result.append(case)
    return result
