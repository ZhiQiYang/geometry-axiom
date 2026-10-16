"""Compile legacy models to the one neutral graph evaluator and encode old wire.

The provider supplies domain admission and profile metadata. Native transport is
injected by the host; the geometry kernel never parses scene or package syntax.
"""
from copy import deepcopy
from dataclasses import dataclass

import geometry_kernel as kernel
from geometry_kernel import (AssemblyChild, AssemblyDef, DependencyEdge,
    DifferenceDef, EvaluationError, EvaluationRequest, ExportRoot, ExportView,
    ExtrusionDef, FaceUse, InteriorDef, Limits, NodeInput, OrientedShellDef,
    PlacedRegionDef, ProgramBuilder, ProvenanceTemplate, Quantity, QuantityType,
    SourceContext, SourceDescriptor, SourceKey, SourceRef, Unit, UnionDef,
    ValueType)

from .model_common import ModelError, canonical_bytes, digest
from .model_codec import (_as_ref, _context, _fail, _keys, _raise_errors,
                          parse_extensions, parse_request)
from .model_geometry import _inputs, _source_record, solid_definition
from .kernel_errors import translate


MAX_EXTENSIONS = 512
MAX_DEPENDENCY_DEPTH = 64
MAX_EXPANDED_KEEP_LEAVES = 10_000


def _source(key):
    return {"origin": _as_ref(key), "operation_path": [], "role": "boundary"}


def _provenance(key, placement=None):
    placement = placement or {}
    return ProvenanceTemplate((*key, placement.get("id"), placement.get("boundary_id")), key)


def _policy_error(error):
    return ModelError(error.status, error.code, error.clause, error.message,
                      path=error.path, root=None if error.root is None else _as_ref(error.root))


@dataclass
class CompiledModel:
    base: dict
    records: dict
    dependencies: dict
    paths: dict
    original_paths: dict
    identities: dict
    node_identities: dict
    roots: tuple
    canonical_request: dict
    program: object
    kernel_request: EvaluationRequest
    limits: Limits
    profile_definitions: dict
    canonical: list | None = None

    def error(self, error):
        key = self.node_identities.get(error.node)
        paths = self.original_paths if error.phase == "declaration" else self.paths
        path = [*paths.get(key, ()), *error.path]
        root = self.roots[error.root] if error.root is not None else None
        missing = self.node_identities.get(error.missing)
        code, message, clause = error.code, error.message, None
        if code == "MISSING_REFERENCE":
            clause, message = "I30", "Referenced object does not exist"
        elif code == "OPERAND_TYPE":
            clause, message = "I29", "KEEP assemblies are not Boolean solids"
        elif code == "DEPENDENCY_CYCLE":
            clause, message = "I29", "Extension references contain a cycle"
        elif code == "FORWARD_REFERENCE":
            clause, message = "I9", "Referenced extension must be declared before its consumer"
        elif code == "CAPACITY":
            if message.startswith("Program contains more than"):
                message, path = f"Executor supports at most {MAX_EXTENSIONS} extensions", []
            message = message.replace("Expanded assembly leaves", "Expanded KEEP leaves")
        elif code == "OPEN_SHELL" and root is not None:
            # Output incompleteness is rooted at the requested export, not its
            # source definition's canonical position.
            path = list(error.path)
        mapped = translate(error)
        result = ModelError(error.status, code, clause or mapped.clause,
                            message if clause is not None or code == "CAPACITY" else mapped.message,
                            path=path, root=None if root is None else _as_ref(root),
                            missing=None if missing is None else _as_ref(missing))
        if error.diagnostics:
            result.diagnostics = [self.error(item).diagnostic() for item in error.diagnostics]
        return result


class ModelingRuntime:
    def __init__(self, *, provider, native_loader):
        if provider is None or not callable(native_loader):
            raise ModelError("UNSUPPORTED", "MODEL_PROVIDER", "I32", "An explicit modeling provider and native loader are required")
        self.provider = provider
        self.native_loader = native_loader

    def compile(self, definitions, request, *, max_cells, base_executable=None):
        canonical_bytes(definitions)
        canonical_bytes(request)
        _keys(definitions, ("base_scene", "extensions"), path=["definitions"])
        if type(definitions["base_scene"]) is not str:
            _fail("TYPE", "D25", "base_scene must be a string", ["definitions", "base_scene"])
        if type(max_cells) is not int or max_cells < 1:
            _fail("CAPACITY", "I33", "max_cells must be a positive integer", status="UNSUPPORTED")
        canonical_request = parse_request(request, self.provider)
        base = self.native_loader(definitions["base_scene"], executable=base_executable)
        records, dependencies, original_paths = parse_extensions(definitions["extensions"], base, self.provider)
        placements = {("placement", item["id"]): item for item in base["placements"]}
        solids = {(item["kind"], item["id"]): item for item in base["solids"]}
        profiles = {("profile-run", item["id"]): item for item in base.get("profile_runs", [])}
        roots = tuple((item["kind"], item["id"]) for item in canonical_request["roots"])
        available = set(placements) | set(solids) | set(records) | set(profiles)
        referenced = {dep for refs in dependencies.values() for dep in refs}
        identities = {key: i for i, key in enumerate(sorted(available | referenced))}
        node_identities = {value: key for key, value in identities.items()}
        # PY2 retains native-evaluated quantities without inventing another scene
        # parser. The full same-candidate source DTO is a separate required gate.
        sources = tuple(SourceDescriptor(SourceKey("legacy-spec", (item["name"],)), ValueType.QUANTITY,
                        SourceContext(), (), Quantity(QuantityType.DIMENSION, item["value"], 1, Unit.MM),
                        origin=("legacy-spec", item["name"])) for item in base["specs"])
        builder = ProgramBuilder(sources, snapshot_identity=("legacy-source", digest(base["base_scene"])))
        for key, placement in placements.items():
            axes, region = _inputs(placement)
            builder.add(PlacedRegionDef(axes, region, _provenance(key, placement)), key=identities[key], order_token=key, declared=False)
        for key, solid in solids.items():
            builder.add(solid_definition(solid, _source(key)), key=identities[key], order_token=key, declared=False)

        next_hidden = len(identities)
        hidden_count = 0
        enclosure_nodes = {}
        external = {}
        profile_definitions = {}

        def hidden(definition, owner, **options):
            nonlocal next_hidden, hidden_count
            key = next_hidden
            next_hidden += 1
            hidden_count += 1
            node_identities[key] = owner
            return builder.add(definition, key=key, order_token=(*owner, key), declared=False, **options)

        def node_input(reference, path=(), contribution=None):
            key = (reference["kind"], reference["id"])
            return NodeInput(identities[key], path, contribution)

        for key, record in records.items():
            if key[0] == "extrusion":
                placed_key = ("placement", record["placement_id"])
                definition = ExtrusionDef(identities[placed_key],
                    SourceRef(SourceKey("legacy-spec", (record["lo_spec"],)), ValueType.QUANTITY),
                    SourceRef(SourceKey("legacy-spec", (record["hi_spec"],)), ValueType.QUANTITY),
                    _provenance(key, placements.get(placed_key)))
            elif key[0] == "shell":
                definition = OrientedShellDef(tuple(FaceUse(NodeInput(identities[("placement", use["placement_id"])],
                    ("uses", str(i), "placement_id")), use["orientation"]) for i, use in enumerate(record["uses"])))
            elif key[0] == "composition":
                if record["op"] == "KEEP":
                    definition = AssemblyDef(tuple(AssemblyChild(node_input(ref, ("inputs", str(i))), i) for i, ref in enumerate(record["inputs"])))
                elif record["op"] == "UNION":
                    definition = UnionDef(tuple(node_input(ref, ("inputs", str(i))) for i, ref in enumerate(record["inputs"])))
                else:
                    definition = DifferenceDef(node_input(record["base"], ("base",)),
                        tuple(node_input(ref, ("tools", str(i)), "cut") for i, ref in enumerate(record["tools"])))
            else:
                interior = InteriorDef(NodeInput(identities[("shell", record["shell_id"])], ("shell_id",)))
                if record["obstacles"]:
                    enclosure = hidden(interior, key)
                    enclosure_nodes[key] = enclosure
                    obstacles = tuple(node_input(ref, ("obstacles", str(i))) for i, ref in enumerate(record["obstacles"]))
                    definition = DifferenceDef(NodeInput(enclosure), obstacles)
                    external[enclosure] = tuple(item.node for item in obstacles)
                else:
                    definition = interior
                    enclosure_nodes[key] = identities[key]
            builder.add(definition, key=identities[key], order_token=key,
                        definition_dependencies=tuple(dict.fromkeys(identities[dep] for dep in dependencies[key])))

        # Profile policy emits typed region/span requests. The same K evaluator
        # builds members and envelope; no separate profile mesher is selected.
        for key in roots:
            if key not in profiles:
                continue
            children = []
            for item in self.provider.profile_objects(profiles[key]):
                placed = hidden(PlacedRegionDef(item.frame, item.region, item.source), key)
                solid = hidden(ExtrusionDef(placed, 0, item.length, item.source), key)
                profile_definitions[solid] = item
                children.append(AssemblyChild(NodeInput(solid), item.metadata["member_id"]))
            builder.add(AssemblyDef(tuple(children)), key=identities[key], order_token=key, declared=False)

        for entry in base.get("dependencies", []):
            key = (entry["kind"], entry["id"])
            if key not in placements and key not in solids and key not in roots:
                continue
            refs = [(ref["kind"], ref["id"]) for ref in entry["refs"]]
            # Native source-only objects are retained by native definitions but
            # have no world geometry coordinates to add to this arrangement.
            external[identities[key]] = tuple(identities[ref] for ref in refs if ref in placements or ref in solids)
        for key, solid in solids.items():
            if solid.get("placement_id") is not None:
                owner = identities[key]
                ref = identities.get(("placement", solid["placement_id"]))
                if ref is not None:
                    external[owner] = tuple(dict.fromkeys((*external.get(owner, ()), ref)))

        program = builder.freeze(external_dependencies=tuple(external.items()))
        limits = Limits(max_cells=max_cells, max_nodes=MAX_EXTENSIONS + len(program.nodes) - len(records),
                        max_depth=MAX_DEPENDENCY_DEPTH, max_expanded_leaves=MAX_EXPANDED_KEEP_LEAVES)
        exports = []
        for key in roots:
            selected = identities.get(key, next_hidden)
            view = ExportView.BOUNDARY if key[0] in ("placement", "shell") else ExportView.GEOMETRY
            if key[0] == "composite_space" and key in records:
                if canonical_request["role"] == "enclosure":
                    selected = enclosure_nodes[key]
                    view = ExportView.INTERIOR_REQUIRED if canonical_request["target"] == "solid-set" else ExportView.INTERIOR_OR_BOUNDARY
                else:
                    view = ExportView.INTERIOR_REQUIRED
            exports.append(ExportRoot(selected, view=view, output_tag=key))
        compiled = CompiledModel(base, records, dependencies, original_paths, original_paths,
                    identities, node_identities, roots, canonical_request, program,
                    EvaluationRequest(tuple(exports), canonical_request["allow_partial"]), limits, profile_definitions)
        try:
            validated = kernel.validate_program(program, limits=limits)
        except EvaluationError as error:
            raise compiled.error(error) from error
        ordered = tuple(node_identities[key] for key in validated.order
                        if key in identities.values() and node_identities[key] in records)
        compiled.canonical = [records[key] for key in ordered]
        compiled.paths = {key: ["definitions", "extensions", str(i)] for i, key in enumerate(ordered)}
        errors = []
        for key in roots:
            try:
                if key not in available:
                    _fail("MISSING_REFERENCE", "D24", "Model root does not exist or is not placed",
                          ["request", "roots"], missing=_as_ref(key), root=_as_ref(key))
                self.provider.admit_root(key, records, canonical_request["target"], canonical_request["role"])
            except ModelError as error:
                errors.append(_context(error, [], _as_ref(key)))
            except ValueError as error:
                if not hasattr(error, "clause"):
                    raise
                errors.append(_context(_policy_error(error), [], _as_ref(key)))
        _raise_errors(errors)
        return compiled

    def evaluate(self, definitions, request, *, capabilities=None, max_cells=200000, base_executable=None):
        compiled = self.compile(definitions, request, max_cells=max_cells, base_executable=base_executable)
        capability_errors = []
        if capabilities is None:
            capability_set = set(self.provider.capabilities)
        elif not isinstance(capabilities, (list, tuple, set, frozenset)) or any(type(item) is not str for item in capabilities):
            capability_errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32", "capabilities must be a string collection"))
            capability_set = set()
        else:
            capability_set = set(capabilities)
            unknown = capability_set - set(self.provider.capabilities)
            if unknown:
                capability_errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32", "Unknown capability: " + min(unknown)))
        required = {"model-export/1"} | {self.provider.kind_capability[key[0]] for key in compiled.records} | set(compiled.base.get("required_capabilities", []))
        missing_caps = sorted(required - capability_set)
        if missing_caps:
            capability_errors.append(ModelError("UNSUPPORTED", "CAPABILITY", "I32", "Required capabilities are unavailable: " + ", ".join(missing_caps), missing=missing_caps))
        errors = []
        result = None
        try:
            result = kernel.evaluate(compiled.program, compiled.kernel_request, limits=compiled.limits,
                                     validation_only=bool(capability_errors))
        except EvaluationError as error:
            errors.append(compiled.error(error))
        # Definition contradictions still precede capability diagnostics. Export
        # incompleteness/capacity is considered only after capability admission.
        _raise_errors([*errors, *capability_errors])
        objects, diagnostics = [], []
        for outcome in result.outcomes:
            if outcome.status == "INCOMPLETE":
                diagnostics.extend(compiled.error(error).diagnostic() for error in outcome.diagnostics)
            profile_counts = {}
            for record in outcome.records:
                mesh = deepcopy(record.mesh)
                mesh.update(root=_as_ref(compiled.roots[outcome.root_index]), member_path=list(record.member_path), role=compiled.canonical_request["role"])
                mesh["face_sources"] = [[_source_record(source) for source in row] for row in mesh["face_sources"]]
                if record.node in compiled.profile_definitions:
                    definition = compiled.profile_definitions[record.node]
                    profile_counts[record.node] = profile_counts.get(record.node, 0) + 1
                    if profile_counts[record.node] != 1:
                        raise ModelError("INVALID", "PROFILE_MESH", "R37", "A section-profile object must produce one complete solid", root=mesh["root"])
                    try:
                        mesh["section_profile"] = self.provider.annotate_profile(definition, mesh)
                    except ValueError as error:
                        if not hasattr(error, "clause"):
                            raise
                        raise _policy_error(error) from error
                    mesh["role"] = definition.export_role
                objects.append(mesh)
                if mesh["status"] == "EMPTY":
                    diagnostics.append({"root": mesh["root"], "path": [str(i) for i in mesh["member_path"]],
                        "code": "EMPTY_RESULT", "clause": "D23", "message": "Regularized operation produced the empty set"})
        objects.sort(key=lambda item: (item["root"]["kind"], item["root"]["id"], item["member_path"],
                                      -1 if item["component"] is None else item["component"]))
        return {"definitions": {"base_scene": compiled.base["base_scene"], "extensions": compiled.canonical},
                "required_capabilities": sorted(compiled.base.get("required_capabilities", [])),
                "request": compiled.canonical_request,
                "derived": {"status": result.status, "objects": objects}, "diagnostics": diagnostics}
