"""Evaluate typed geometry graphs with exact topology and root atomicity."""
from dataclasses import dataclass, replace

from . import geometry as geo
from .errors import EvaluationError, invalid, raise_errors
from .graph import (AssemblyDef, BoxDef, DependencyKind, DifferenceDef,
    EvaluationRequest, ExportView, ExtrusionDef, InteriorDef, Limits,
    OrientedShellDef, PlacedRegionDef, Program, SourceRef, SourceStatus,
    UnionDef, inputs, source_refs, validate_program)
from .types import CoordinateDomain, Quantity, QuantityType, RegionDef, RegionSetDef


@dataclass(frozen=True)
class GeometryRecord:
    node: int
    output_tag: tuple
    member_path: tuple
    domain: CoordinateDomain
    mesh: dict


@dataclass(frozen=True)
class RootOutcome:
    root_index: int
    status: str
    records: tuple
    diagnostics: tuple = ()


@dataclass(frozen=True)
class EvaluationResult:
    order: tuple
    outcomes: tuple
    sources: tuple
    snapshot_identity: tuple

    @property
    def status(self):
        if any(outcome.status == "INCOMPLETE" for outcome in self.outcomes):
            return "INCOMPLETE"
        return "EMPTY" if all(outcome.status == "EMPTY" for outcome in self.outcomes) else "COMPLETE"

    @property
    def records(self):
        return tuple(record for outcome in self.outcomes for record in outcome.records)

    @property
    def diagnostics(self):
        return tuple(error for outcome in self.outcomes for error in outcome.diagnostics)


@dataclass
class _State:
    geometry: object = None
    frame: object = None
    regions: object = None
    analysis: object = None
    problem: object = None
    interior_problem: object = None


_prefix = geo.prefix_geometry


def _dependencies(program):
    result = {node.key: tuple(dict.fromkeys((*[item.node for item in inputs(node.definition)], *node.definition_dependencies))) for node in program.nodes}
    for key, dependencies in program.external_dependencies:
        result[key] = tuple(dict.fromkeys((*result[key], *dependencies)))
    return result


def _selected(program, roots):
    dependencies = _dependencies(program)
    selected, pending = set(), list(roots)
    while pending:
        key = pending.pop()
        if key in selected:
            continue
        selected.add(key)
        pending.extend(dependencies.get(key, ()))
    return selected


def source_closure(program, roots, *, limits=Limits()):
    validated = validate_program(program, limits=limits)
    selected = _selected(program, roots)
    nodes = {node.key: node for node in program.nodes}
    if any(key not in nodes for key in roots):
        invalid("MISSING_REFERENCE", "Source closure root does not exist")
    sources = {source.key: source for source in program.sources}
    pending = [ref.key for key in selected for ref in source_refs(nodes[key].definition)]
    selected_sources = set()
    while pending:
        key = pending.pop()
        if key in selected_sources:
            continue
        selected_sources.add(key)
        pending.extend(edge.source for edge in sources[key].dependencies)
    return tuple(sources[key] for key in validated.source_order if key in selected_sources)


def evaluate(program, request, *, limits=Limits()):
    validated = validate_program(program, limits=limits)
    if not isinstance(request, EvaluationRequest):
        invalid("EVALUATION_REQUEST", "Expected a typed evaluation request")
    nodes = {node.key: node for node in program.nodes}
    sources = {source.key: source for source in program.sources}
    errors = []
    for index, root in enumerate(request.roots):
        if root.node not in nodes:
            errors.append(EvaluationError("INVALID", "MISSING_REFERENCE", "Model root does not exist", missing=root.node, root=index))
    # Invalid source definitions remain invalid even when no export selects them.
    for source in program.sources:
        if source.status == SourceStatus.INVALID:
            errors.append(EvaluationError("INVALID", "SOURCE_INVALID", "A source definition is invalid", node=source.key))
    raise_errors(errors)

    source_problems = {}
    for key in validated.source_order:
        source = sources[key]
        problems = []
        if source.status != SourceStatus.COMPLETE:
            problems.append(EvaluationError(source.status.value, "SOURCE_UNAVAILABLE", "A typed source value is unavailable", missing=key))
        for edge in source.dependencies:
            if edge.kind == DependencyKind.VALUE_REQUIRED and edge.source in source_problems:
                problems.append(source_problems[edge.source])
        try:
            raise_errors(problems)
        except EvaluationError as error:
            source_problems[key] = error

    def value(item):
        if not isinstance(item, SourceRef):
            return item
        if item.key in source_problems:
            raise source_problems[item.key]
        return sources[item.key].value

    def scalar(item):
        resolved = value(item)
        if isinstance(resolved, Quantity):
            if resolved.value_type not in (QuantityType.DIMENSION, QuantityType.AXIS_POSITION) or resolved.denominator != 1:
                invalid("SCALAR_VALUE", "Geometry bounds require exact integral length quantities")
            resolved = resolved.numerator
        if type(resolved) is not int:
            invalid("SCALAR_VALUE", "Geometry bounds require exact integers")
        return resolved

    states = {}

    def input_geometry(item, *, require_interior=False):
        state = states[item.node]
        if state.problem is not None:
            raise state.problem.contextualized(path=(*item.path, *state.problem.path))
        if require_interior and state.geometry.inside is None:
            if state.interior_problem is not None:
                raise state.interior_problem
            invalid("BOOLEAN_NOT_SOLID", "Boolean operands must all be solved solid sets")
        return _prefix(state.geometry, item.path, item.contribution)

    for key in validated.order:
        definition = nodes[key].definition
        failed = [states[item.node].problem for item in inputs(definition)
                  if states[item.node].problem is not None and states[item.node].problem.status != "INCOMPLETE"]
        if failed:
            # The independent failing definition already supplied its diagnostic;
            # consumers cannot add redundant copies of the same contradiction.
            states[key] = _State(problem=failed[0])
            continue
        try:
            if isinstance(definition, PlacedRegionDef):
                frame, regions = value(definition.frame), value(definition.region)
                if isinstance(regions, RegionDef):
                    regions = RegionSetDef((regions,))
                geometries = [geo.placed_region_geometry(frame, region, definition.source.feature(("surface", i if len(regions.components) > 1 else -1, -1)))
                              for i, region in enumerate(regions.components)]
                geometry = geo._Geometry([face for g in geometries for face in g.faces], domain=frame.domain)
                states[key] = _State(geometry=geometry, frame=frame, regions=regions)
            elif isinstance(definition, BoxDef):
                states[key] = _State(geometry=geo.box_geometry(definition))
            elif isinstance(definition, ExtrusionDef):
                placed = states[definition.region]
                if placed.problem is not None:
                    raise placed.problem
                lower, upper = scalar(definition.lower), scalar(definition.upper)
                geo.extrusion_span(lower, upper)
                geometries = []
                for component, region in enumerate(placed.regions.components):
                    features = [("bottom_cap", -1, -1), ("top_cap", -1, -1)]
                    features += [("outer_side" if i == 0 else "hole_side", i, j)
                                 for i, loop in enumerate((region.outer, *region.holes)) for j in range(len(loop))]
                    origins = {feature: definition.source.feature(feature if len(placed.regions.components) == 1 else (*feature, component)) for feature in features}
                    geometries.append(geo.extrusion_geometry(placed.frame, region, lower, upper, origins))
                geometry = (geo.boolean_geometry("UNION", geometries, max_source_faces=limits.max_source_faces) if geometries else
                            geo._Geometry([], lambda point: False, domain=placed.frame.domain))
                states[key] = _State(geometry=geometry)
            elif isinstance(definition, OrientedShellDef):
                faces = []
                for use in definition.uses:
                    geometry = input_geometry(use.region)
                    faces.extend(replace(face, sign=face.sign * use.orientation) for face in geometry.faces)
                geometry = geo._Geometry(tuple(faces))
                states[key] = _State(geometry=geometry, analysis=geo.analyze_shell(faces, max_cells=limits.max_cells))
            elif isinstance(definition, InteriorDef):
                shell = states[definition.shell.node]
                geometry = input_geometry(definition.shell)
                if shell.analysis["closed"]:
                    geometry = geo.enclosed_geometry(geometry.faces, max_cells=limits.max_cells)
                    states[key] = _State(geometry=geometry, analysis=shell.analysis)
                else:
                    message = "Open shell has no determined enclosed volume; boundary edges: " + str(shell.analysis["boundary_edges"])
                    problem = EvaluationError("INCOMPLETE", "OPEN_SHELL", message, node=key, path=definition.shell.path)
                    states[key] = _State(geometry=geometry, analysis=shell.analysis, interior_problem=problem)
            elif isinstance(definition, AssemblyDef):
                states[key] = _State()
            elif isinstance(definition, (UnionDef, DifferenceDef)):
                items = inputs(definition)
                operands = [input_geometry(item, require_interior=True) for item in items]
                geometry = geo.boolean_geometry("UNION" if isinstance(definition, UnionDef) else "DIFFERENCE", operands, max_source_faces=limits.max_source_faces)
                states[key] = _State(geometry=geometry)
                # Unselected operations receive the same manifold validation.
                geo.mesh_objects(geometry, geo.build_grid([geometry], max_cells=limits.max_cells), max_cells=limits.max_cells)
        except EvaluationError as error:
            contextual = error.contextualized(node=key)
            states[key] = _State(problem=contextual)
            if error.status != "INCOMPLETE":
                errors.append(contextual)
    raise_errors(errors)

    selected = _selected(program, (root.node for root in request.roots))
    geometries_by_domain = {}
    for key in validated.order:
        geometry = states[key].geometry
        if key in selected and geometry is not None:
            geometries_by_domain.setdefault(geometry.domain, []).append(geometry)
    grids = {domain: geo.build_grid(geometries, max_cells=limits.max_cells) for domain, geometries in geometries_by_domain.items()}

    def output(key, root, member_path=(), operation_path=(), contribution=None):
        definition, state = nodes[key].definition, states[key]
        if state.problem is not None:
            raise state.problem.contextualized(path=(*operation_path, *state.problem.path))
        if isinstance(definition, AssemblyDef):
            records = []
            for child in definition.children:
                child_path = member_path if child.member is None else (*member_path, child.member)
                records.extend(output(child.input.node, root, child_path, (*operation_path, *child.input.path), child.input.contribution if child.input.contribution is not None else contribution))
            return records
        geometry = _prefix(state.geometry, operation_path, contribution)
        if root.coordinate_domain is not None and root.coordinate_domain != geometry.domain:
            invalid("COORDINATE_DOMAIN", "Export and evaluated geometry coordinate domains disagree")
        if root.view == ExportView.INTERIOR_REQUIRED and geometry.inside is None:
            if state.interior_problem is not None:
                raise state.interior_problem.contextualized(path=(*operation_path, *state.interior_problem.path))
            invalid("TARGET_TYPE", "A boundary without a determined interior cannot be exported as a solid")
        volume_known = False if root.view == ExportView.BOUNDARY else None
        mesh_records = geo.mesh_objects(geometry, grids[geometry.domain], volume_known=volume_known, max_cells=limits.max_cells)
        return [GeometryRecord(key, root.output_tag, member_path, geometry.domain, mesh) for mesh in mesh_records]

    outcomes, incomplete = [], []
    for index, root in enumerate(request.roots):
        try:
            # A single root is staged in a private list. No leaf escapes if a
            # later member makes this root incomplete or invalid.
            records = tuple(output(root.node, root, root.member_path))
            status = "EMPTY" if all(record.mesh["status"] == "EMPTY" for record in records) else "COMPLETE"
            outcomes.append(RootOutcome(index, status, records))
        except EvaluationError as error:
            contextual = error.contextualized(root=index)
            if error.status == "INCOMPLETE":
                incomplete.append(contextual)
                outcomes.append(RootOutcome(index, "INCOMPLETE", (), (contextual,)))
            else:
                errors.append(contextual)
    raise_errors([*errors, *incomplete] if errors else ([] if request.allow_partial else incomplete))
    closure = source_closure(program, tuple(root.node for root in request.roots), limits=limits)
    return EvaluationResult(validated.order, tuple(outcomes), closure, program.snapshot_identity)
