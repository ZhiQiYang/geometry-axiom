"""Legacy wire shape and domain-policy admission; graph algorithms live in K."""
from copy import deepcopy
from .model_common import ModelError

_PRIORITY = {"INVALID": 3, "UNSUPPORTED": 2, "INCOMPLETE": 1}
_LIMIT = 100_000_000

def _fail(code, clause, message, path=(), *, missing=None, status="INVALID", root=None):
    raise ModelError(status, code, clause, message, path=list(path),
                     missing=missing, root=root)


def _keys(value, required, optional=(), path=(), clause="D25"):
    if type(value) is not dict:
        _fail("TYPE", clause, "Expected an object", path)
    extra = set(value) - set(required) - set(optional)
    if extra:
        _fail("UNKNOWN_FIELD", clause, "Unknown field: " + sorted(extra)[0], path)
    absent = set(required) - set(value)
    if absent:
        _fail("MISSING_FIELD", clause, "Missing field: " + sorted(absent)[0], path,
              missing=sorted(absent)[0])
    for key in required:
        if value[key] is None:
            _fail("TYPE", clause, "Required field cannot be null: " + key, [*path, key])


def _id(value, path):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        _fail("ID_RANGE", "D1", "Object id must be a uint32 integer", path)
    return value


def _ref(value, path, allowed=None):
    _keys(value, ("kind", "id"), path=path)
    if type(value["kind"]) is not str or value["kind"] not in allowed:
        _fail("REFERENCE_TYPE", "I29", "Unsupported reference kind", [*path, "kind"])
    return value["kind"], _id(value["id"], [*path, "id"])


def _as_ref(key):
    return {"kind": key[0], "id": key[1]}


def _ref_list(value, path, minimum=0, allowed=None):
    if type(value) is not list or len(value) < minimum:
        _fail("TYPE", "D23", "Expected reference array with at least %d item(s)" % minimum, path)
    refs = [_ref(item, [*path, str(i)], allowed) for i, item in enumerate(value)]
    if len(set(refs)) != len(refs):
        _fail("DUPLICATE_REFERENCE", "I29", "References must be distinct", path)
    return refs


def _raise_errors(errors):
    """Preserve all available diagnostics while reporting the strongest state."""
    if not errors:
        return
    strongest = max(errors, key=lambda item: _PRIORITY[item.status])
    diagnostics = []
    for error in errors:
        diagnostics.extend(error.diagnostics or [error.diagnostic()])
    raise ModelError(strongest.status, strongest.code, strongest.clause,
                     strongest.message, path=strongest.path, root=strongest.root,
                     missing=strongest.missing, diagnostics=diagnostics)


def _context(error, path, root=None):
    return ModelError(error.status, error.code, error.clause, error.message,
                      path=[*path, *error.path], root=error.root or root,
                      missing=error.missing, diagnostics=error.diagnostics)


def parse_request(request, policy):
    _keys(request, ("roots", "role", "target"), ("allow_partial",), ["request"], "D24")
    refs = _ref_list(request["roots"], ["request", "roots"], 1, policy.root_kinds)
    if request["role"] not in ("geometry", "enclosure", "clearance"):
        _fail("ROLE", "D24", "Unknown modeling role", ["request", "role"])
    if request["target"] not in ("surface-set", "solid-set"):
        _fail("TARGET", "D24", "Unknown modeling target", ["request", "target"])
    partial = request.get("allow_partial", False)
    if type(partial) is not bool:
        _fail("TYPE", "D24", "allow_partial must be boolean", ["request", "allow_partial"])
    return {"roots": [_as_ref(key) for key in sorted(refs)],
            "role": request["role"], "target": request["target"], "allow_partial": partial}


def parse_extensions(extensions, base, policy):
    if type(extensions) is not list:
        _fail("TYPE", "D25", "extensions must be an array", ["definitions", "extensions"])
    records, paths, dependencies = {}, {}, {}
    primitive = {(item["kind"], item["id"]) for item in base["solids"]}
    primitive.update(("placement", item["id"]) for item in base["placements"])
    specs = {item["name"]: item["value"] for item in base["specs"]}
    errors = []
    for index, original in enumerate(extensions):
        path = ["definitions", "extensions", str(index)]
        try:
            if type(original) is not dict or type(original.get("kind")) is not str:
                _fail("TYPE", "D25", "Extension must have a string kind", path)
            kind = original["kind"]
            if kind not in policy.extension_kinds:
                _fail("REFERENCE_TYPE", "D25", "Unknown extension kind", [*path, "kind"])
            if kind == "extrusion":
                _keys(original, ("kind", "id", "placement_id", "lo_spec", "hi_spec"), path=path, clause="D20")
            elif kind == "shell":
                _keys(original, ("kind", "id", "uses"), path=path, clause="D21")
            elif kind == "composite_space":
                _keys(original, ("kind", "id", "shell_id", "obstacles"), path=path, clause="D22")
            else:
                if original.get("op") == "DIFFERENCE":
                    fields = ("kind", "id", "op", "base", "tools")
                else:
                    fields = ("kind", "id", "op", "inputs")
                _keys(original, fields, path=path, clause="D23")
            key = (kind, _id(original["id"], [*path, "id"]))
            if key in records:
                _fail("DUPLICATE_ID", "I9", "Duplicate extension id in its kind namespace", path)
            record = deepcopy(original)
            deps = []
            if kind == "extrusion":
                placement = _id(record["placement_id"], [*path, "placement_id"])
                deps = [("placement", placement)]
                for field in ("lo_spec", "hi_spec"):
                    if type(record[field]) is not str or not record[field]:
                        _fail("TYPE", "D20", "Specification name must be a nonempty string", [*path, field])
                    if record[field] not in specs:
                        _fail("MISSING_SPEC", "I26", "Extrusion specification does not exist", [*path, field], missing=record[field])
                lo, hi = specs[record["lo_spec"]], specs[record["hi_spec"]]
                if lo >= hi:
                    _fail("NON_POSITIVE_SPAN", "I26", "Extrusion requires lo_spec < hi_spec", path)
                if not (-_LIMIT <= lo <= _LIMIT and -_LIMIT <= hi <= _LIMIT and hi - lo <= _LIMIT):
                    _fail("COORD_RANGE", "I26", "Extrusion span exceeds the D1 input range", path)
            elif kind == "shell":
                uses = record["uses"]
                if type(uses) is not list or not uses:
                    _fail("TYPE", "D21", "Shell uses must be a nonempty array", [*path, "uses"])
                seen = set()
                for i, use in enumerate(uses):
                    use_path = [*path, "uses", str(i)]
                    _keys(use, ("placement_id", "orientation", "purpose"), path=use_path, clause="D21")
                    placement = _id(use["placement_id"], [*use_path, "placement_id"])
                    if placement in seen:
                        _fail("DUPLICATE_FACE_USE", "I27", "A placement may occur only once in a shell", use_path)
                    seen.add(placement)
                    if type(use["orientation"]) is not int or use["orientation"] not in (-1, 1):
                        _fail("ORIENTATION", "D21", "orientation must be integer +1 or -1", [*use_path, "orientation"])
                    if use["purpose"] not in ("boundary", "calculation-cap"):
                        _fail("PURPOSE", "D21", "purpose must explicitly be boundary or calculation-cap", [*use_path, "purpose"])
                    deps.append(("placement", placement))
                record["uses"].sort(key=lambda use: use["placement_id"])
            elif kind == "composite_space":
                deps = [("shell", _id(record["shell_id"], [*path, "shell_id"]))]
                obstacles = _ref_list(record["obstacles"], [*path, "obstacles"], allowed=policy.primitive_solids | {"composition"})
                deps += obstacles
                record["obstacles"] = [_as_ref(ref) for ref in sorted(obstacles)]
            elif record["op"] == "KEEP":
                deps = _ref_list(record["inputs"], [*path, "inputs"], 1, policy.geometry_kinds)
            elif record["op"] == "UNION":
                deps = _ref_list(record["inputs"], [*path, "inputs"], 2, policy.primitive_solids | {"composition"})
                record["inputs"] = [_as_ref(ref) for ref in sorted(deps)]
            elif record["op"] == "DIFFERENCE":
                base_ref = _ref(record["base"], [*path, "base"], policy.primitive_solids | {"composition"})
                tools = _ref_list(record["tools"], [*path, "tools"], 1, policy.primitive_solids | {"composition"})
                deps = [base_ref, *tools]
                record["tools"] = [_as_ref(ref) for ref in sorted(tools)]
            else:
                _fail("OPERATION", "D23", "Unknown composition operation", [*path, "op"])
            records[key], paths[key], dependencies[key] = record, path, deps
        except ModelError as exc:
            errors.append(exc)
    _raise_errors(errors)

    return records, dependencies, paths
