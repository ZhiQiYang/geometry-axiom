"""Validated definition graph and request evaluation for orthogonal-model/1.

The C adapter owns the existing scene language. This module owns extension
references, request typing and completeness; geometry.py owns exact geometry.
No application display state is used when evaluating a model.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import heapq

from .common import (ModelError, canonical_bytes, ENGINEERING_CAPABILITY,
                     PARAMETER_CAPABILITY, SECTION_PROFILE_CAPABILITY)

CAPABILITIES = (
    "composite-space/1", "extrusion/1", "model-export/1", "shell/1",
    "solid-composition/1", ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, SECTION_PROFILE_CAPABILITY,
)
_EXTENSION_KINDS = {"extrusion", "shell", "composite_space", "composition"}
_PRIMITIVE_SOLIDS = {"column", "beam", "timber", "extrusion"}
_GEOMETRY_KINDS = {"placement", "shell", "composition"} | _PRIMITIVE_SOLIDS
_ROOT_KINDS = _GEOMETRY_KINDS | {"composite_space", "profile-run"}
_KIND_CAPABILITY = {
    "extrusion": "extrusion/1", "shell": "shell/1",
    "composite_space": "composite-space/1", "composition": "solid-composition/1",
}
_PRIORITY = {"INVALID": 3, "UNSUPPORTED": 2, "INCOMPLETE": 1}
_LIMIT = 100_000_000
MAX_EXTENSIONS = 512
MAX_DEPENDENCY_DEPTH = 64
MAX_EXPANDED_KEEP_LEAVES = 10_000


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
    if type(value["kind"]) is not str or value["kind"] not in (allowed or _ROOT_KINDS):
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


def _parse_request(request):
    _keys(request, ("roots", "role", "target"), ("allow_partial",), ["request"], "D24")
    refs = _ref_list(request["roots"], ["request", "roots"], 1)
    if request["role"] not in ("geometry", "enclosure", "clearance"):
        _fail("ROLE", "D24", "Unknown modeling role", ["request", "role"])
    if request["target"] not in ("surface-set", "solid-set"):
        _fail("TARGET", "D24", "Unknown modeling target", ["request", "target"])
    partial = request.get("allow_partial", False)
    if type(partial) is not bool:
        _fail("TYPE", "D24", "allow_partial must be boolean", ["request", "allow_partial"])
    return {"roots": [_as_ref(key) for key in sorted(refs)],
            "role": request["role"], "target": request["target"], "allow_partial": partial}


def _parse_extensions(extensions, base):
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
            if kind not in _EXTENSION_KINDS:
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
                obstacles = _ref_list(record["obstacles"], [*path, "obstacles"], allowed=_PRIMITIVE_SOLIDS | {"composition"})
                deps += obstacles
                record["obstacles"] = [_as_ref(ref) for ref in sorted(obstacles)]
            elif record["op"] == "KEEP":
                deps = _ref_list(record["inputs"], [*path, "inputs"], 1, _GEOMETRY_KINDS)
            elif record["op"] == "UNION":
                deps = _ref_list(record["inputs"], [*path, "inputs"], 2, _PRIMITIVE_SOLIDS | {"composition"})
                record["inputs"] = [_as_ref(ref) for ref in sorted(deps)]
            elif record["op"] == "DIFFERENCE":
                base_ref = _ref(record["base"], [*path, "base"], _PRIMITIVE_SOLIDS | {"composition"})
                tools = _ref_list(record["tools"], [*path, "tools"], 1, _PRIMITIVE_SOLIDS | {"composition"})
                deps = [base_ref, *tools]
                record["tools"] = [_as_ref(ref) for ref in sorted(tools)]
            else:
                _fail("OPERATION", "D23", "Unknown composition operation", [*path, "op"])
            records[key], paths[key], dependencies[key] = record, path, deps
        except ModelError as exc:
            errors.append(exc)
    _raise_errors(errors)

    # Resolve and type-check the complete graph before any capability failure can
    # hide a known contradiction in another root or unselected definition.
    for key, record in records.items():
        for dep in dependencies[key]:
            if dep not in records and dep not in primitive:
                errors.append(ModelError("INVALID", "MISSING_REFERENCE", "I30",
                                         "Referenced object does not exist", path=paths[key], missing=_as_ref(dep)))
            elif dep[0] == "composition" and records[dep]["op"] == "KEEP":
                if key[0] == "composite_space" or (key[0] == "composition" and record["op"] != "KEEP"):
                    errors.append(ModelError("INVALID", "OPERAND_TYPE", "I29",
                                             "KEEP assemblies are not Boolean solids", path=paths[key], missing=_as_ref(dep)))
    _raise_errors(errors)
    indegree = {key: len(set(dep for dep in deps if dep in records)) for key, deps in dependencies.items()}
    followers = {key: [] for key in records}
    for key, deps in dependencies.items():
        for dep in set(deps):
            if dep in followers:
                followers[dep].append(key)
    ready = [key for key, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        key = heapq.heappop(ready)
        ordered.append(key)
        for child in followers[key]:
            indegree[child] -= 1
            if not indegree[child]:
                heapq.heappush(ready, child)
    if len(ordered) != len(records):
        cycle = min(key for key, degree in indegree.items() if degree)
        _fail("DEPENDENCY_CYCLE", "I29", "Extension references contain a cycle", paths[cycle])
    # Imports may permute independent definitions, but a reference cannot be
    # completed by a later declaration (I9 and MODELING-CONTRACT sections 1/2).
    declared = set(primitive)
    for key in records:
        forward = next((dep for dep in dependencies[key] if dep not in declared), None)
        if forward is not None:
            _fail("FORWARD_REFERENCE", "I9", "Referenced extension must be declared before its consumer",
                  paths[key], missing=_as_ref(forward))
        declared.add(key)
    if len(records) > MAX_EXTENSIONS:
        _fail("CAPACITY", "I33", f"Executor supports at most {MAX_EXTENSIONS} extensions", status="UNSUPPORTED")
    depths, leaves = {}, {}
    for key in ordered:
        depths[key] = 1 + max((depths.get(dep, 0) for dep in dependencies[key]), default=0)
        if depths[key] > MAX_DEPENDENCY_DEPTH:
            _fail("CAPACITY", "I33", f"Dependency depth exceeds {MAX_DEPENDENCY_DEPTH}", paths[key], status="UNSUPPORTED")
        record = records[key]
        leaves[key] = (sum(leaves.get(dep, 1) for dep in dependencies[key])
                       if key[0] == "composition" and record["op"] == "KEEP" else 1)
        if leaves[key] > MAX_EXPANDED_KEEP_LEAVES:
            _fail("CAPACITY", "I33", f"Expanded KEEP leaves exceed {MAX_EXPANDED_KEEP_LEAVES}", paths[key], status="UNSUPPORTED")
    canonical = [records[key] for key in ordered]
    paths = {key: ["definitions", "extensions", str(i)] for i, key in enumerate(ordered)}
    return records, dependencies, ordered, canonical, paths


def _prefix(geometry, path=(), cut=False):
    from .geometry import prefix
    return prefix(geometry, path, cut)


def _source(key):
    return {"origin": _as_ref(key), "operation_path": [], "role": "boundary"}


def _root_types(key, records, target, role, path=()):
    if key[0] == "profile-run":
        if role != "geometry" or target != "solid-set":
            _fail("TARGET_TYPE", "R39", "ProfileRun requires geometry role and solid-set target", path, root=_as_ref(key))
        return
    if key[0] == "composite_space":
        if role not in ("enclosure", "clearance"):
            _fail("TARGET_TYPE", "D24", "CompositeSpace requires enclosure or clearance role", path, root=_as_ref(key))
        return
    if role != "geometry":
        _fail("TARGET_TYPE", "D24", "This root requires geometry role", path, root=_as_ref(key))
    if key[0] in ("placement", "shell") and target == "solid-set":
        _fail("TARGET_TYPE", "D24", "A zero-thickness face or shell is not a material solid", path)
    if key[0] == "composition" and records[key]["op"] == "KEEP":
        for i, item in enumerate(records[key]["inputs"]):
            _root_types((item["kind"], item["id"]), records, target, role, [*path, "inputs", str(i)])


def evaluate(definitions, request, *, capabilities=None, max_cells=200000,
             base_executable=None):
    """Return canonical definitions/request and deterministic derived geometry.

    Definitions are validated in full and preserved in the exchange package.
    Only selected roots and their dependencies contribute to the output grid.
    Invalid, unsupported, and non-partial incomplete requests raise ModelError.
    """
    from .base import load_base
    from . import geometry as geo
    from . import section_profile as profile_geo

    canonical_bytes(definitions)
    canonical_bytes(request)
    _keys(definitions, ("base_scene", "extensions"), path=["definitions"])
    if type(definitions["base_scene"]) is not str:
        _fail("TYPE", "D25", "base_scene must be a string", ["definitions", "base_scene"])
    if type(max_cells) is not int or max_cells < 1:
        _fail("CAPACITY", "I33", "max_cells must be a positive integer", status="UNSUPPORTED")
    canonical_request = _parse_request(request)
    base = load_base(definitions["base_scene"], executable=base_executable)
    records, dependencies, ordered, canonical, paths = _parse_extensions(definitions["extensions"], base)
    placements = {("placement", item["id"]): item for item in base["placements"]}
    solids = {(item["kind"], item["id"]): item for item in base["solids"]}
    profile_runs = {("profile-run", item["id"]): item for item in base.get("profile_runs", [])}
    specs = {item["name"]: item["value"] for item in base["specs"]}
    available = set(placements) | set(solids) | set(records) | set(profile_runs)
    roots = [(item["kind"], item["id"]) for item in canonical_request["roots"]]
    errors = []
    for key in roots:
        try:
            if key not in available:
                _fail("MISSING_REFERENCE", "D24", "Model root does not exist or is not placed",
                      ["request", "roots"], missing=_as_ref(key), root=_as_ref(key))
            _root_types(key, records, canonical_request["target"], canonical_request["role"])
        except ModelError as exc:
            errors.append(_context(exc, [], _as_ref(key)))
    # Known request contradictions dominate all missing capability diagnostics.
    _raise_errors(errors)

    geometries, shell_info, composite_clearance = {}, {}, {}
    for key, placement in placements.items():
        geometries[key] = geo.placement_geometry(placement, _source(key))
    for key, solid in solids.items():
        geometries[key] = geo.solid_geometry(solid, _source(key))
    failed = set()
    for key in ordered:
        if any(dep in failed for dep in dependencies[key]):
            failed.add(key)
            continue
        record = records[key]
        try:
            if key[0] == "extrusion":
                geometry = geo.extrusion_geometry(placements[("placement", record["placement_id"])],
                                                  specs[record["lo_spec"]], specs[record["hi_spec"]], _source(key))
                # D1 checks generated world vertices, not merely local offsets.
                for face in geometry.faces:
                    if abs(face.coord) > _LIMIT or any(abs(value) > _LIMIT for ring in (face.outer, *face.holes) for vertex in ring for value in vertex):
                        _fail("COORD_RANGE", "I26", "Generated extrusion vertex exceeds D1 range")
                geometries[key] = geometry
            elif key[0] == "shell":
                faces = []
                for i, use in enumerate(record["uses"]):
                    placement = _prefix(geometries[("placement", use["placement_id"])], ["uses", str(i), "placement_id"])
                    faces.extend(replace(face, sign=face.sign * use["orientation"]) for face in placement.faces)
                geometries[key] = geo.Geometry(tuple(faces))
                shell_info[key] = geo.analyze_shell(faces, max_cells=max_cells)
            elif key[0] == "composition" and record["op"] != "KEEP":
                if record["op"] == "UNION":
                    operands = [_prefix(geometries[(ref["kind"], ref["id"])], ["inputs", str(i)])
                                for i, ref in enumerate(record["inputs"])]
                else:
                    ref = record["base"]
                    operands = [_prefix(geometries[(ref["kind"], ref["id"])], ["base"])]
                    operands += [_prefix(geometries[(ref["kind"], ref["id"])], ["tools", str(i)], cut=True)
                                 for i, ref in enumerate(record["tools"])]
                geometries[key] = geo.boolean_geometry(record["op"], operands)
            elif key[0] == "composite_space":
                shell = ("shell", record["shell_id"])
                enclosure = _prefix(geometries[shell], ["shell_id"])
                if shell_info[shell]["closed"]:
                    enclosure = geo.enclosed_geometry(enclosure.faces, max_cells=max_cells)
                    operands = [enclosure]
                    operands += [_prefix(geometries[(ref["kind"], ref["id"])], ["obstacles", str(i)])
                                 for i, ref in enumerate(record["obstacles"])]
                    composite_clearance[key] = (geo.boolean_geometry("DIFFERENCE", operands)
                                                if record["obstacles"] else enclosure)
                geometries[key] = enclosure
            # Validate every Boolean result, including unselected definitions.
            # A locally valid operand does not guarantee a manifold result.
            if ((key[0] == "composition" and record["op"] != "KEEP") or
                    (key[0] == "composite_space" and key in composite_clearance)):
                geometry = composite_clearance.get(key, geometries[key])
                grid = geo.build_grid([geometry], max_cells=max_cells)
                geo.mesh_objects(geometry, grid, _as_ref(key), max_cells=max_cells)
        except ModelError as exc:
            failed.add(key)
            errors.append(_context(exc, paths[key]))
    # Capability reduction is supported for explicit subset executors/tests.
    # We still report any contradiction our actual validator can establish.
    if capabilities is None:
        capability_set = set(CAPABILITIES)
    elif not isinstance(capabilities, (list, tuple, set, frozenset)) or any(type(item) is not str for item in capabilities):
        errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32", "capabilities must be a string collection"))
        capability_set = set()
    else:
        capability_set = set(capabilities)
        unknown = capability_set - set(CAPABILITIES)
        if unknown:
            errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32", "Unknown capability: " + min(unknown)))
    required = {"model-export/1"} | {_KIND_CAPABILITY[key[0]] for key in records} | set(base.get("required_capabilities", []))
    missing_caps = sorted(required - capability_set)
    if missing_caps:
        errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32",
                                 "Required capabilities are unavailable: " + ", ".join(missing_caps), missing=missing_caps))
    _raise_errors(errors)

    # The C adapter reports the semantic geometric closure of legacy objects
    # (including earlier same-carrier timber stop faces). Guide/spec references
    # without a world surface stay in source but add no grid coordinates.
    base_dependencies = {(item["kind"], item["id"]):
                         [(ref["kind"], ref["id"]) for ref in item["refs"]]
                         for item in base.get("dependencies", [])}
    selected, pending = set(), list(roots)
    while pending:
        key = pending.pop()
        if key in selected:
            continue
        selected.add(key)
        pending.extend(dependencies.get(key, []))
        pending.extend(base_dependencies.get(key, []))
        if key in solids and solids[key].get("placement_id") is not None:
            pending.append(("placement", solids[key]["placement_id"]))
    selected_geometries = [geometries[key] for key in sorted(selected) if key in geometries]
    selected_geometries += [composite_clearance[key] for key in sorted(selected) if key in composite_clearance]
    profile_items = {key: profile_geo.geometries(profile_runs[key]) for key in roots if key in profile_runs}
    # Placed runs share the request's R29 world arrangement. Each unplaced run
    # has its own local frame and never contributes coordinates to world roots.
    selected_geometries += [geometry for key, items in profile_items.items()
                            if profile_runs[key]["coordinate_space"] == "world"
                            for geometry, _ in items]
    grid = geo.build_grid(selected_geometries, max_cells=max_cells)
    objects, diagnostics, incomplete = [], [], []

    def output(key, root, member_path=(), operation_path=()):
        if key in profile_runs:
            run = profile_runs[key]
            profile_grid = (grid if run["coordinate_space"] == "world" else
                            geo.build_grid([g for g, _ in profile_items[key]], max_cells=max_cells))
            return profile_geo.output(run, profile_items[key], profile_grid, max_cells=max_cells)
        if key[0] == "composition" and records[key]["op"] == "KEEP":
            result = []
            for i, ref in enumerate(records[key]["inputs"]):
                result.extend(output((ref["kind"], ref["id"]), root,
                                     (*member_path, i), (*operation_path, "inputs", str(i))))
            return result
        role = canonical_request["role"]
        volume_known = None
        geometry = geometries[key]
        if key[0] in ("placement", "shell"):
            volume_known = False
        elif key[0] == "composite_space":
            shell = ("shell", records[key]["shell_id"])
            if not shell_info[shell]["closed"]:
                if role == "clearance" or canonical_request["target"] == "solid-set":
                    boundary_edges = shell_info[shell].get("boundary_edges", [])
                    _fail("OPEN_SHELL", "I28", "Open shell has no determined enclosed volume; boundary edges: " + str(boundary_edges),
                          [*operation_path, "shell_id"], status="INCOMPLETE", root=root)
                volume_known = False
            elif role == "clearance":
                geometry = composite_clearance[key]
        geometry = _prefix(geometry, operation_path)
        return geo.mesh_objects(geometry, grid, root, member_path=list(member_path),
                                role=role, volume_known=volume_known, max_cells=max_cells)

    for key in roots:
        try:
            objects.extend(output(key, _as_ref(key)))
        except ModelError as exc:
            error = _context(exc, [], _as_ref(key))
            if error.status == "INCOMPLETE":
                incomplete.append(error)
            else:
                errors.append(error)
    if errors:
        _raise_errors([*errors, *incomplete])
    if incomplete and not canonical_request["allow_partial"]:
        _raise_errors(incomplete)
    diagnostics.extend(item.diagnostic() for item in incomplete)
    for item in objects:
        if item["status"] == "EMPTY":
            diagnostics.append({"root": item["root"], "path": [str(i) for i in item["member_path"]],
                                "code": "EMPTY_RESULT", "clause": "D23", "message": "Regularized operation produced the empty set"})
    objects.sort(key=lambda item: (item["root"]["kind"], item["root"]["id"], item["member_path"],
                                   -1 if item["component"] is None else item["component"]))
    status = "INCOMPLETE" if incomplete else ("EMPTY" if all(item["status"] == "EMPTY" for item in objects) else "COMPLETE")
    return {"definitions": {"base_scene": base["base_scene"], "extensions": canonical},
            "required_capabilities": sorted(base.get("required_capabilities", [])),
            "request": canonical_request,
            "derived": {"status": status, "objects": objects}, "diagnostics": diagnostics}
