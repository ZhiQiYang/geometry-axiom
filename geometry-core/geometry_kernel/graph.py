"""Immutable typed geometry and source graphs; no legacy syntax or policy."""
from dataclasses import dataclass
from enum import Enum
import heapq

from .errors import EvaluationError, invalid, raise_errors
from .types import (BoxDef, CoordinateDomain, FrameDef, Provenance, Quantity,
                    QuantityType, RegionDef, RegionSetDef, SourceKey, _identity)


def _tuple(value, code, message):
    if not isinstance(value, (tuple, list)):
        invalid(code, message)
    return tuple(value)


def _identity_tuple(value):
    if type(value) is not tuple:
        invalid("IDENTITY", "An identity must be an immutable tuple")
    _identity(value)


class ValueType(Enum):
    QUANTITY = "quantity"
    FRAME = "frame"
    REGION_SET = "region-set"
    BOX = "box"
    FEATURE = "feature"


class DependencyKind(Enum):
    VALUE_REQUIRED = "value-required"
    DEFINITION_REQUIRED = "definition-required"
    EVALUATE_BEFORE = "evaluate-before"


class SourceStatus(Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class SourceContext:
    domain: CoordinateDomain | None = None
    axis: int | None = None
    owner: tuple = ()

    def __post_init__(self):
        if self.domain is not None and not isinstance(self.domain, CoordinateDomain):
            invalid("SOURCE_CONTEXT", "Invalid source coordinate domain")
        if self.axis is not None and (type(self.axis) is not int or self.axis not in (0, 1, 2)):
            invalid("SOURCE_CONTEXT", "A source axis must be an exact coordinate axis")
        _identity_tuple(self.owner)


@dataclass(frozen=True)
class DependencyEdge:
    source: SourceKey
    kind: DependencyKind = DependencyKind.VALUE_REQUIRED

    def __post_init__(self):
        if not isinstance(self.source, SourceKey) or not isinstance(self.kind, DependencyKind):
            invalid("SOURCE_DEPENDENCY", "A source edge needs an explicit key and dependency kind")


@dataclass(frozen=True)
class SourceDescriptor:
    key: SourceKey
    value_type: ValueType
    context: SourceContext
    dependencies: tuple
    value: object
    status: SourceStatus = SourceStatus.COMPLETE
    origin: tuple = ()

    def __post_init__(self):
        if not isinstance(self.key, SourceKey) or not isinstance(self.value_type, ValueType) or not isinstance(self.context, SourceContext) or not isinstance(self.status, SourceStatus):
            invalid("SOURCE_DESCRIPTOR", "A source requires typed identity, value, context and status")
        object.__setattr__(self, "dependencies", _tuple(self.dependencies, "SOURCE_DEPENDENCY", "Source dependencies must be typed edges"))
        if any(not isinstance(edge, DependencyEdge) for edge in self.dependencies):
            invalid("SOURCE_DEPENDENCY", "Source dependencies must be typed edges")
        if len(set(self.dependencies)) != len(self.dependencies):
            invalid("SOURCE_DEPENDENCY", "A source dependency cannot be repeated")
        _identity_tuple(self.origin)
        expected = {ValueType.QUANTITY: Quantity, ValueType.FRAME: FrameDef,
                    ValueType.REGION_SET: RegionSetDef, ValueType.BOX: BoxDef,
                    ValueType.FEATURE: tuple}[self.value_type]
        if self.value is not None and not isinstance(self.value, expected):
            invalid("SOURCE_VALUE_TYPE", "Source value and declared type disagree")
        if self.value_type == ValueType.FEATURE and self.value is not None:
            _identity(self.value)
        if isinstance(self.value, FrameDef) and self.context.domain is not None and self.value.domain != self.context.domain:
            invalid("SOURCE_CONTEXT", "Source frame and declared coordinate domain disagree")
        if isinstance(self.value, BoxDef) and self.context.domain is not None and self.value.frame.domain != self.context.domain:
            invalid("SOURCE_CONTEXT", "Source box and declared coordinate domain disagree")
        if self.status == SourceStatus.COMPLETE and self.value is None:
            invalid("SOURCE_VALUE_MISSING", "A complete source requires its typed value")


@dataclass(frozen=True)
class SourceRef:
    key: SourceKey
    value_type: ValueType
    context: SourceContext | None = None

    def __post_init__(self):
        if not isinstance(self.key, SourceKey) or not isinstance(self.value_type, ValueType) or (self.context is not None and not isinstance(self.context, SourceContext)):
            invalid("SOURCE_REFERENCE", "A source reference needs a typed stable key")


@dataclass(frozen=True)
class ProvenanceTemplate:
    origin_handle: tuple
    order_prefix: tuple
    operation_path: tuple = ()
    contribution: str = "boundary"

    def __post_init__(self):
        # Reuse the same full immutable validation used for resolved features.
        Provenance(self.origin_handle, (), self.order_prefix, self.operation_path, self.contribution)

    def feature(self, key):
        return Provenance(self.origin_handle, key, (*self.order_prefix, *key),
                          self.operation_path, self.contribution)


@dataclass(frozen=True)
class PlacedRegionDef:
    frame: FrameDef | SourceRef
    region: RegionDef | RegionSetDef | SourceRef
    source: ProvenanceTemplate


@dataclass(frozen=True)
class SourceBoxDef:
    box: SourceRef


@dataclass(frozen=True)
class ExtrusionDef:
    region: int
    lower: int | SourceRef
    upper: int | SourceRef
    source: ProvenanceTemplate


@dataclass(frozen=True)
class NodeInput:
    node: int
    path: tuple = ()
    contribution: str | None = None

    def __post_init__(self):
        if type(self.node) is not int or self.node < 0 or type(self.path) is not tuple or (self.contribution is not None and type(self.contribution) is not str):
            invalid("NODE_REFERENCE", "A node input requires an exact key and immutable provenance path")
        _identity(self.path)


@dataclass(frozen=True)
class FaceUse:
    region: NodeInput
    orientation: int = 1


@dataclass(frozen=True)
class OrientedShellDef:
    uses: tuple

    def __post_init__(self):
        object.__setattr__(self, "uses", _tuple(self.uses, "SHELL_USES", "Shell uses must be a sequence"))


@dataclass(frozen=True)
class InteriorDef:
    shell: NodeInput


@dataclass(frozen=True)
class AssemblyChild:
    input: NodeInput
    member: int | str | None


@dataclass(frozen=True)
class AssemblyDef:
    children: tuple

    def __post_init__(self):
        object.__setattr__(self, "children", _tuple(self.children, "ASSEMBLY_CHILDREN", "Assembly children must be a sequence"))


@dataclass(frozen=True)
class UnionDef:
    inputs: tuple

    def __post_init__(self):
        object.__setattr__(self, "inputs", _tuple(self.inputs, "BOOLEAN_INPUTS", "Union inputs must be a sequence"))


@dataclass(frozen=True)
class DifferenceDef:
    base: NodeInput
    tools: tuple

    def __post_init__(self):
        object.__setattr__(self, "tools", _tuple(self.tools, "BOOLEAN_INPUTS", "Difference tools must be a sequence"))


NODE_TYPES = (PlacedRegionDef, BoxDef, SourceBoxDef, ExtrusionDef, OrientedShellDef,
              InteriorDef, AssemblyDef, UnionDef, DifferenceDef)


@dataclass(frozen=True)
class Node:
    key: int
    definition: object
    order_token: tuple = ()
    definition_dependencies: tuple = ()

    def __post_init__(self):
        if type(self.key) is not int or self.key < 0 or not isinstance(self.definition, NODE_TYPES):
            invalid("NODE_DEFINITION", "A geometry node requires an exact key and supported typed definition")
        if type(self.order_token) is not tuple:
            invalid("NODE_ORDER", "Node order must be an immutable token")
        _identity(self.order_token)
        object.__setattr__(self, "definition_dependencies", _tuple(self.definition_dependencies, "NODE_REFERENCE", "Definition dependencies must be a sequence"))
        if any(type(key) is not int or key < 0 for key in self.definition_dependencies):
            invalid("NODE_REFERENCE", "Definition dependencies require exact node keys")
        if len(set(self.definition_dependencies)) != len(self.definition_dependencies):
            invalid("DUPLICATE_REFERENCE", "Definition dependencies must be distinct")

    @property
    def sort_key(self):
        return (Provenance((), (), self.order_token).sort_key, self.key)


@dataclass(frozen=True)
class Program:
    sources: tuple = ()
    nodes: tuple = ()
    declarations: tuple | None = None
    external_dependencies: tuple = ()
    snapshot_identity: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "sources", _tuple(self.sources, "PROGRAM", "Program collections must be sequences"))
        object.__setattr__(self, "nodes", _tuple(self.nodes, "PROGRAM", "Program collections must be sequences"))
        object.__setattr__(self, "external_dependencies", _tuple(self.external_dependencies, "PROGRAM", "Program collections must be sequences"))
        declarations = tuple(node.key for node in self.nodes if isinstance(node, Node)) if self.declarations is None else _tuple(self.declarations, "DECLARATIONS", "Declarations must be a sequence")
        object.__setattr__(self, "declarations", declarations)
        _identity_tuple(self.snapshot_identity)


class ExportView(Enum):
    GEOMETRY = "geometry"
    BOUNDARY = "boundary"
    INTERIOR_REQUIRED = "interior-required"
    INTERIOR_OR_BOUNDARY = "interior-or-boundary"


@dataclass(frozen=True)
class ExportRoot:
    node: int
    view: ExportView = ExportView.GEOMETRY
    coordinate_domain: CoordinateDomain | None = None
    member_path: tuple = ()
    output_tag: tuple = ()

    def __post_init__(self):
        if type(self.node) is not int or self.node < 0 or not isinstance(self.view, ExportView):
            invalid("EXPORT_ROOT", "An export root requires an exact node key and a supported view")
        if self.coordinate_domain is not None and not isinstance(self.coordinate_domain, CoordinateDomain):
            invalid("EXPORT_DOMAIN", "An export root requires a typed coordinate domain")
        for value in (self.member_path, self.output_tag):
            if type(value) is not tuple:
                invalid("EXPORT_IDENTITY", "Export identities must be immutable tuples")
            _identity(value)


@dataclass(frozen=True)
class EvaluationRequest:
    roots: tuple
    allow_partial: bool = False

    def __post_init__(self):
        object.__setattr__(self, "roots", _tuple(self.roots, "EVALUATION_REQUEST", "Export roots must be a sequence"))
        if not self.roots or any(not isinstance(root, ExportRoot) for root in self.roots) or type(self.allow_partial) is not bool:
            invalid("EVALUATION_REQUEST", "A request requires typed export roots and an explicit partial flag")


@dataclass(frozen=True)
class Limits:
    max_cells: int = 200_000
    max_nodes: int = 512
    max_depth: int = 64
    max_expanded_leaves: int = 10_000
    max_source_faces: int = 12_000

    def __post_init__(self):
        if any(type(value) is not int or value < 1 for value in (self.max_cells, self.max_nodes, self.max_depth, self.max_expanded_leaves, self.max_source_faces)):
            raise EvaluationError("UNSUPPORTED", "CAPACITY", "Evaluation limits must be positive exact integers")


@dataclass(frozen=True)
class ValidatedProgram:
    program: Program
    order: tuple
    source_order: tuple


def inputs(definition):
    if isinstance(definition, ExtrusionDef):
        return (NodeInput(definition.region),)
    if isinstance(definition, OrientedShellDef):
        return tuple(use.region for use in definition.uses)
    if isinstance(definition, InteriorDef):
        return (definition.shell,)
    if isinstance(definition, AssemblyDef):
        return tuple(child.input for child in definition.children)
    if isinstance(definition, UnionDef):
        return definition.inputs
    if isinstance(definition, DifferenceDef):
        return (definition.base, *definition.tools)
    return ()


def source_refs(definition):
    if isinstance(definition, SourceBoxDef):
        return (definition.box,)
    if isinstance(definition, PlacedRegionDef):
        return tuple(value for value in (definition.frame, definition.region) if isinstance(value, SourceRef))
    if isinstance(definition, ExtrusionDef):
        return tuple(value for value in (definition.lower, definition.upper) if isinstance(value, SourceRef))
    return ()


def _shape(definition):
    if isinstance(definition, SourceBoxDef):
        if not isinstance(definition.box, SourceRef) or definition.box.value_type != ValueType.BOX:
            invalid("SOURCE_REFERENCE_TYPE", "A source box requires a typed box reference")
    elif isinstance(definition, PlacedRegionDef):
        if not isinstance(definition.frame, (FrameDef, SourceRef)) or not isinstance(definition.region, (RegionDef, RegionSetDef, SourceRef)) or not isinstance(definition.source, ProvenanceTemplate):
            invalid("NODE_DEFINITION", "A placed region requires typed frame, region and provenance")
        for value, expected in ((definition.frame, ValueType.FRAME), (definition.region, ValueType.REGION_SET)):
            if isinstance(value, SourceRef) and value.value_type != expected:
                invalid("SOURCE_REFERENCE_TYPE", "A placed region reference has the wrong value type")
    elif isinstance(definition, ExtrusionDef):
        if type(definition.region) is not int or definition.region < 0 or not isinstance(definition.source, ProvenanceTemplate):
            invalid("NODE_DEFINITION", "An extrusion requires a placed region and provenance")
        for value in (definition.lower, definition.upper):
            if type(value) is not int and not (isinstance(value, SourceRef) and value.value_type == ValueType.QUANTITY):
                invalid("SOURCE_REFERENCE_TYPE", "Extrusion bounds require exact scalar values")
    elif isinstance(definition, OrientedShellDef):
        if not definition.uses or any(not isinstance(use, FaceUse) or not isinstance(use.region, NodeInput) or type(use.orientation) is not int or use.orientation not in (-1, 1) for use in definition.uses):
            invalid("SHELL_USES", "A shell requires explicit signed region uses")
    elif isinstance(definition, InteriorDef):
        if not isinstance(definition.shell, NodeInput):
            invalid("NODE_DEFINITION", "An interior requires an oriented shell")
    elif isinstance(definition, AssemblyDef):
        if not definition.children or any(not isinstance(child, AssemblyChild) or not isinstance(child.input, NodeInput) or (child.member is not None and type(child.member) not in (int, str)) for child in definition.children):
            invalid("ASSEMBLY_CHILDREN", "An ordered assembly needs explicitly identified children")
        if len({child.member for child in definition.children}) != len(definition.children):
            invalid("ASSEMBLY_CHILDREN", "Assembly member identities must be distinct")
    elif isinstance(definition, UnionDef):
        if len(definition.inputs) < 2 or any(not isinstance(item, NodeInput) for item in definition.inputs):
            invalid("BOOLEAN_INPUTS", "A union requires at least two solid inputs")
    elif isinstance(definition, DifferenceDef):
        if not isinstance(definition.base, NodeInput) or not definition.tools or any(not isinstance(item, NodeInput) for item in definition.tools):
            invalid("BOOLEAN_INPUTS", "A difference requires a base and explicit tools")
    dependencies = tuple(definition.tools) if isinstance(definition, DifferenceDef) else inputs(definition)
    if len({item.node for item in dependencies}) != len(dependencies):
        invalid("DUPLICATE_REFERENCE", "Node references must be distinct")


def _topological(keys, dependencies, sort_key, code, message):
    indegree = {key: len(set(dependencies[key])) for key in keys}
    followers = {key: [] for key in keys}
    for key in keys:
        for dep in set(dependencies[key]):
            followers[dep].append(key)
    ready = [(sort_key(key), key) for key, degree in indegree.items() if not degree]
    heapq.heapify(ready)
    ordered = []
    while ready:
        _, key = heapq.heappop(ready)
        ordered.append(key)
        for follower in followers[key]:
            indegree[follower] -= 1
            if not indegree[follower]:
                heapq.heappush(ready, (sort_key(follower), follower))
    if len(ordered) != len(keys):
        key = min((key for key, degree in indegree.items() if degree), key=sort_key)
        raise EvaluationError("INVALID", code, message, node=key, phase="declaration")
    return tuple(ordered)


def validate_program(program, *, limits=Limits()):
    if not isinstance(program, Program) or not isinstance(limits, Limits):
        invalid("PROGRAM", "Expected an immutable program and explicit limits")
    if any(not isinstance(node, Node) for node in program.nodes) or any(not isinstance(source, SourceDescriptor) for source in program.sources):
        invalid("PROGRAM", "A program contains only typed nodes and sources")
    nodes = {node.key: node for node in program.nodes}
    sources = {source.key: source for source in program.sources}
    if len(nodes) != len(program.nodes) or len(sources) != len(program.sources):
        invalid("DUPLICATE_DEFINITION", "Program identities must be unique")
    external = {}
    for entry in program.external_dependencies:
        if type(entry) is not tuple or len(entry) != 2 or type(entry[0]) is not int or entry[0] not in nodes or type(entry[1]) is not tuple or any(type(key) is not int or key not in nodes for key in entry[1]):
            invalid("EXTERNAL_DEPENDENCIES", "External geometry dependencies must identify existing nodes")
        if entry[0] in external or len(set(entry[1])) != len(entry[1]):
            invalid("EXTERNAL_DEPENDENCIES", "External dependency entries must be distinct")
        external[entry[0]] = entry[1]
    errors = []
    for node in program.nodes:
        try:
            _shape(node.definition)
        except EvaluationError as error:
            errors.append(error.contextualized(node=node.key, phase="declaration"))
            continue
        for reference in source_refs(node.definition):
            try:
                source = sources.get(reference.key)
                if source is None:
                    raise EvaluationError("INVALID", "SOURCE_MISSING_REFERENCE", "Referenced source does not exist", missing=reference.key)
                if source.value_type != reference.value_type or (reference.context is not None and source.context != reference.context):
                    raise EvaluationError("INVALID", "SOURCE_REFERENCE_TYPE", "Source reference type or context disagrees", missing=reference.key)
            except EvaluationError as error:
                errors.append(error.contextualized(node=node.key, phase="declaration"))
        direct = {item.node for item in inputs(node.definition)}
        for dependency_key in dict.fromkeys((*node.definition_dependencies, *(item.node for item in inputs(node.definition)))):
            try:
                if dependency_key not in nodes:
                    raise EvaluationError("INVALID", "MISSING_REFERENCE", "Referenced object does not exist", missing=dependency_key)
                if dependency_key not in direct:
                    continue
                dependency = nodes[dependency_key].definition
                if isinstance(node.definition, (UnionDef, DifferenceDef)) and not isinstance(dependency, (BoxDef, SourceBoxDef, ExtrusionDef, InteriorDef, UnionDef, DifferenceDef)):
                    raise EvaluationError("INVALID", "OPERAND_TYPE", "Boolean inputs require typed solid definitions", missing=dependency_key)
                if isinstance(node.definition, ExtrusionDef) and not isinstance(dependency, PlacedRegionDef):
                    raise EvaluationError("INVALID", "OPERAND_TYPE", "An extrusion requires a placed region", missing=dependency_key)
                if isinstance(node.definition, OrientedShellDef) and not isinstance(dependency, PlacedRegionDef):
                    raise EvaluationError("INVALID", "OPERAND_TYPE", "A shell use requires a placed region", missing=dependency_key)
                if isinstance(node.definition, InteriorDef) and not isinstance(dependency, OrientedShellDef):
                    raise EvaluationError("INVALID", "OPERAND_TYPE", "An interior requires an oriented shell", missing=dependency_key)
            except EvaluationError as error:
                errors.append(error.contextualized(node=node.key, phase="declaration"))
    for source in program.sources:
        for edge in source.dependencies:
            if edge.source not in sources:
                errors.append(EvaluationError("INVALID", "SOURCE_MISSING_REFERENCE", "Referenced source definition does not exist", node=source.key, missing=edge.source, phase="declaration"))
    raise_errors(errors)
    source_order = _topological(sources, {key: tuple(edge.source for edge in value.dependencies) for key, value in sources.items()},
                                lambda key: Provenance((key.namespace, key.key), (), (key.namespace, key.key)).sort_key,
                                "SOURCE_DEPENDENCY_CYCLE", "Source references contain a cycle")
    dependencies = {key: tuple(dict.fromkeys((*[item.node for item in inputs(value.definition)], *value.definition_dependencies, *external.get(key, ())))) for key, value in nodes.items()}
    order = _topological(nodes, dependencies, lambda key: nodes[key].sort_key,
                         "DEPENDENCY_CYCLE", "Geometry references contain a cycle")
    declarations = program.declarations
    if any(type(key) is not int or key not in nodes for key in declarations) or len(set(declarations)) != len(declarations):
        invalid("DECLARATIONS", "Declarations must identify each declared node exactly once")
    declared = set(nodes) - set(declarations)
    for key in declarations:
        forward = next((dep for dep in dependencies[key] if dep not in declared), None)
        if forward is not None:
            raise EvaluationError("INVALID", "FORWARD_REFERENCE", "Referenced definition must be declared before its consumer", node=key, missing=forward, phase="declaration")
        declared.add(key)
    if len(nodes) > limits.max_nodes:
        raise EvaluationError("UNSUPPORTED", "CAPACITY", f"Program contains more than {limits.max_nodes} geometry nodes")
    depths, leaves = {}, {}
    declared_set = set(declarations)
    for key in order:
        depths[key] = (1 if key in declared_set else 0) + max((depths[dep] for dep in dependencies[key]), default=0)
        leaves[key] = sum(leaves[dep] for dep in dependencies[key]) if isinstance(nodes[key].definition, AssemblyDef) else 1
        if depths[key] > limits.max_depth:
            raise EvaluationError("UNSUPPORTED", "CAPACITY", f"Dependency depth exceeds {limits.max_depth}", node=key)
        if leaves[key] > limits.max_expanded_leaves:
            raise EvaluationError("UNSUPPORTED", "CAPACITY", f"Expanded assembly leaves exceed {limits.max_expanded_leaves}", node=key)
    return ValidatedProgram(program, order, source_order)


class ProgramBuilder:
    def __init__(self, sources=(), *, snapshot_identity=()):
        self._sources = _tuple(sources, "PROGRAM", "Builder sources must be a sequence")
        self._nodes = []
        self._declarations = []
        self._snapshot_identity = snapshot_identity

    @classmethod
    def from_sources(cls, sources, *, snapshot_identity=()):
        return cls(sources, snapshot_identity=snapshot_identity)

    def add(self, definition, *, key=None, order_token=(), declared=True, definition_dependencies=()):
        if type(declared) is not bool:
            invalid("DECLARATIONS", "A declaration flag must be an explicit boolean")
        if key is None:
            key = max((node.key for node in self._nodes), default=-1) + 1
        node = Node(key, definition, order_token, definition_dependencies)
        if any(existing.key == key for existing in self._nodes):
            invalid("DUPLICATE_DEFINITION", "A builder node key is already present")
        self._nodes.append(node)
        if declared:
            self._declarations.append(key)
        return key

    def freeze(self, *, external_dependencies=()):
        return Program(self._sources, tuple(self._nodes), tuple(self._declarations),
                       tuple(external_dependencies), self._snapshot_identity)
