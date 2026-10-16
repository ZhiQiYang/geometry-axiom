"""Strict decoding of a single native candidate and its typed source graph.

This module does not parse scene syntax or choose a template. Coverage is a
required transport property; an incomplete graph never becomes a snapshot-only
geometry input. The product loader is connected only after native coverage is
complete and the transport has frozen source-matched integration evidence.
"""
from base64 import b64decode, b64encode
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re

from geometry_kernel import (BoxDef, CoordinateDomain, DependencyEdge,
    DependencyKind, EvaluationError, FrameDef, Program, Provenance, Quantity,
    QuantityType, RegionDef, RegionSetDef, SourceContext, SourceDescriptor,
    SourceKey, SourceRef, SourceStatus, Unit, ValueType, canonical_bytes,
    strict_json_loads, validate_program)
from geometry_kernel.types import coordinate, vector

from .model_common import ModelError


_VALUE_TYPES = {"quantity": ValueType.QUANTITY, "axis-position": ValueType.QUANTITY,
                "frame": ValueType.FRAME, "region-set": ValueType.REGION_SET,
                "box": ValueType.BOX, "feature": ValueType.FEATURE}
_ROOT_TYPES = {"placement.frame": ValueType.FRAME,
               "placement.region": ValueType.REGION_SET, "solid.box": ValueType.BOX,
               "spec.value": ValueType.QUANTITY, "parameter.value": ValueType.QUANTITY,
               "profile.frame": ValueType.FRAME, "profile.region": ValueType.REGION_SET,
               "profile.length": ValueType.QUANTITY}
_STATUSES = {"ok": SourceStatus.COMPLETE, "missing": SourceStatus.INCOMPLETE,
             "failed": SourceStatus.INCOMPLETE, "cycle": SourceStatus.INVALID,
             "invalid": SourceStatus.INVALID, "memory": SourceStatus.UNSUPPORTED}
_QUANTITIES = {"dimension": QuantityType.DIMENSION, "count": QuantityType.COUNT,
               "ratio": QuantityType.RATIO}


def _fail(message, *, code="BASE_SOURCE_PROTOCOL"):
    raise ModelError("UNSUPPORTED", code, "I32", message)


def _shape(value, required, optional=()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        _fail("Native source transport has an invalid object shape.")
    return value


def _array(value):
    if type(value) is not list:
        _fail("Native source transport requires an array.")
    return value


def _text(value):
    if type(value) is not str or not value:
        _fail("Native source transport requires a nonempty string.")
    return value


def _uint(value):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        _fail("Native source identity must be an exact uint32.")
    return value


def _hash(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        _fail("Native source transport requires an exact SHA-256 identity.")
    return value


def _bytes(value):
    _text(value)
    try:
        result = b64decode(value, validate=True)
    except (ValueError, TypeError) as error:
        raise ModelError("UNSUPPORTED", "BASE_SOURCE_PROTOCOL", "I32", "Native source key is not valid Base64.") from error
    if not result or b64encode(result).decode("ascii") != value:
        _fail("Native source key must use canonical nonempty Base64.")
    return result


def _decimal(value):
    if type(value) is not str or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value) is None:
        _fail("Native quantity must use exact decimal integer strings.")
    try:
        result = int(value)
    except ValueError as error:
        raise ModelError("UNSUPPORTED", "BASE_SOURCE_PROTOCOL", "I32", "Native quantity integer string exceeds supported decoding limits.") from error
    if str(result) != value:
        _fail("Native quantity integer string is not canonical.")
    return result


@dataclass(frozen=True)
class NativeFace:
    axis: int
    side: int
    legacy_feature: str
    feature_key: bytes


@dataclass(frozen=True)
class NativeRoot:
    kind: str
    identity: int
    slot: str
    member: int | None
    name: str | None
    source: SourceRef
    faces: tuple = ()

    @property
    def association(self):
        return (self.kind, self.identity, self.slot, self.member, self.name)


@dataclass(frozen=True)
class NativeCandidate:
    canonical_snapshot: bytes
    candidate_id: str
    base_revision: int
    source_hash: str
    providers: tuple
    sources: tuple
    roots: tuple
    execution_identity: tuple

    @property
    def legacy_snapshot(self):
        # Return a fresh value so callers cannot mutate the pinned snapshot.
        return json.loads(self.canonical_snapshot)

    @property
    def snapshot_identity(self):
        return ("native-candidate", self.candidate_id, self.base_revision,
                self.source_hash, self.providers, self.execution_identity)

    def program(self):
        return Program(sources=self.sources, snapshot_identity=self.snapshot_identity)


class _Decoder:
    def __init__(self, providers):
        self.providers = {}
        for entry in _array(providers):
            _shape(entry, ("namespace", "implementationFingerprint"))
            namespace, fingerprint = _text(entry["namespace"]), _text(entry["implementationFingerprint"])
            if namespace in self.providers:
                _fail("Native source provider namespaces must be unique.")
            self.providers[namespace] = fingerprint

    def reference(self, value):
        _shape(value, ("namespace", "keyBase64"))
        namespace = _text(value["namespace"])
        if namespace not in self.providers:
            _fail("Native source reference names an undeclared provider.")
        return SourceKey(namespace, (self.providers[namespace], _bytes(value["keyBase64"]).hex()))

    def owner(self, value):
        if value is None:
            return ()
        key = self.reference(value)
        return (key.namespace, *key.key)

    def context(self, value):
        _shape(value, ("placementId", "axis", "owner"))
        placement = None if value["placementId"] is None else _uint(value["placementId"])
        axis = value["axis"]
        if axis is not None and (type(axis) is not int or axis not in (0, 1, 2)):
            _fail("Native source context has an invalid coordinate axis.")
        owner = self.owner(value["owner"])
        domain = CoordinateDomain(("native-local", *owner)) if owner else CoordinateDomain()
        return SourceContext(domain, axis, ("native-context", placement, owner))

    def frame(self, value, context):
        _shape(value, ("origin", "u", "v", "n", "coordinateDomain", "owner"))
        owner = self.owner(value["owner"])
        if value["coordinateDomain"] == "world" and not owner:
            domain = CoordinateDomain()
        elif value["coordinateDomain"] == "local" and owner:
            domain = CoordinateDomain(("native-local", *owner))
        else:
            _fail("Native frame domain and owner disagree.")
        if context.domain != domain or context.owner[2] != owner:
            _fail("Native frame and source context disagree.")
        return FrameDef(*(value[key] for key in ("origin", "u", "v", "n")), domain=domain)

    def value(self, value, descriptor, key):
        kind, unit = descriptor["valueType"], descriptor["unit"]
        context = self.context(descriptor["context"])
        if kind == "quantity":
            _shape(value, ("num", "den", "unit", "quantityType"))
            if value["unit"] != unit or type(value["quantityType"]) is not str or value["quantityType"] not in _QUANTITIES:
                _fail("Native quantity type or unit disagrees with its descriptor.")
            return Quantity(_QUANTITIES[value["quantityType"]], _decimal(value["num"]),
                            _decimal(value["den"]), Unit.MM if unit == "length" else Unit.UNITLESS)
        if kind == "axis-position":
            _shape(value, ("coordinate", "context"))
            if unit != "length" or self.context(value["context"]) != context:
                _fail("Native axis position and descriptor context disagree.")
            return Quantity(QuantityType.AXIS_POSITION, coordinate(value["coordinate"]), 1, Unit.MM)
        if kind == "frame":
            return self.frame(value, context)
        if kind == "region-set":
            _shape(value, ("components",))
            components = []
            for component in _array(value["components"]):
                _shape(component, ("outer", "holes", "vertexKeys"))
                loops = (_array(component["outer"]), *_array(component["holes"]))
                keys = component["vertexKeys"]
                if keys is None:
                    identities = ()
                else:
                    if len(_array(keys)) != len(loops) or any(len(_array(ids)) != len(_array(loop)) for ids, loop in zip(keys, loops)):
                        _fail("Native vertex identities must be parallel to every complete loop.")
                    identities = tuple(_uint(identity) for loop in keys for identity in loop)
                components.append(RegionDef(component["outer"], component["holes"], identities))
            return RegionSetDef(tuple(components))
        if kind == "box":
            _shape(value, ("frame", "lo", "hi"))
            origins = tuple(Provenance((key.namespace, *key.key), (axis, side), (axis, side))
                            for axis in range(3) for side in range(2))
            return BoxDef(self.frame(value["frame"], context), value["lo"], value["hi"], origins)
        _shape(value, ("keyBase64", "segment"))
        segment = _array(value["segment"])
        if len(segment) != 2:
            _fail("Native feature segment requires two exact endpoints.")
        return (_bytes(value["keyBase64"]).hex(), vector(segment[0]), vector(segment[1]))

    def descriptors(self, nodes, edges):
        dependencies = {}
        parsed = {}
        for node in _array(nodes):
            _shape(node, ("ref", "descriptor", "status", "value"))
            key = self.reference(node["ref"])
            if key in parsed:
                _fail("Native source keys must be unique.")
            descriptor = _shape(node["descriptor"], ("valueType", "unit", "context"))
            if (type(descriptor["valueType"]) is not str or descriptor["valueType"] not in _VALUE_TYPES
                    or descriptor["unit"] not in ("length", "scalar")
                    or type(node["status"]) is not str or node["status"] not in _STATUSES):
                _fail("Native source descriptor has an unknown type, unit or status.")
            if descriptor["valueType"] != "quantity" and descriptor["unit"] != "length":
                _fail("Native geometric source descriptors require length units.")
            if (node["status"] == "ok") != (node["value"] is not None):
                _fail("Native source status and value availability disagree.")
            parsed[key] = (descriptor, node)
            dependencies[key] = []
        for edge in _array(edges):
            _shape(edge, ("consumer", "source", "kind"))
            consumer, source = self.reference(edge["consumer"]), self.reference(edge["source"])
            if consumer not in parsed or source not in parsed:
                _fail("Native source edge points outside the complete node table.")
            try:
                relation = DependencyKind(edge["kind"])
            except (ValueError, TypeError) as error:
                raise ModelError("UNSUPPORTED", "BASE_SOURCE_PROTOCOL", "I32", "Native source edge kind is unknown.") from error
            dependencies[consumer].append(DependencyEdge(source, relation))
        result = []
        for key, (descriptor, node) in parsed.items():
            value = None if node["value"] is None else self.value(node["value"], descriptor, key)
            result.append(SourceDescriptor(key, _VALUE_TYPES[descriptor["valueType"]], self.context(descriptor["context"]),
                tuple(dependencies[key]), value, _STATUSES[node["status"]], (key.namespace, *key.key)))
        return tuple(result)

    def roots(self, roots, descriptors):
        sources = {source.key: source for source in descriptors}
        result, identities = [], set()
        for entry in _array(roots):
            _shape(entry, ("kind", "id", "slot", "memberId", "name", "ref"), ("faces",))
            kind, identity, slot = _text(entry["kind"]), _uint(entry["id"]), _text(entry["slot"])
            member = None if entry["memberId"] is None else _uint(entry["memberId"])
            name = None if entry["name"] is None else _text(entry["name"])
            key = self.reference(entry["ref"])
            if slot not in _ROOT_TYPES or key not in sources or sources[key].value_type != _ROOT_TYPES[slot]:
                _fail("Native root source is absent or has the wrong declared type.")
            source = sources[key]
            faces = []
            if slot == "solid.box":
                for face in _array(entry.get("faces")):
                    _shape(face, ("axis", "side", "legacyFeature", "featureKeyBase64"))
                    if type(face["axis"]) is not int or face["axis"] not in (0, 1, 2) or type(face["side"]) is not int or face["side"] not in (0, 1):
                        _fail("Native box face must identify an exact local side.")
                    faces.append(NativeFace(face["axis"], face["side"], _text(face["legacyFeature"]), _bytes(face["featureKeyBase64"])))
                if len(faces) != 6 or {(face.axis, face.side) for face in faces} != {(a, s) for a in range(3) for s in range(2)} or len({face.feature_key for face in faces}) != 6:
                    _fail("Native box requires six distinct complete source face associations.")
            elif "faces" in entry:
                _fail("Native face associations belong only to typed box roots.")
            root = NativeRoot(kind, identity, slot, member, name, SourceRef(key, source.value_type, source.context), tuple(faces))
            if root.association in identities:
                _fail("Native root associations must be unique.")
            identities.add(root.association)
            result.append(root)
        return tuple(result)

    def face_values(self, descriptors, roots):
        associations = {}
        for root in roots:
            if not root.faces:
                continue
            key = root.source.key
            faces = tuple(sorted(root.faces, key=lambda face: (face.axis, face.side)))
            if key in associations and associations[key] != faces:
                _fail("Native roots disagree about the same box's source faces.")
            associations[key] = faces
        result = []
        for descriptor in descriptors:
            faces = associations.get(descriptor.key)
            if faces is not None and descriptor.value is not None:
                key = descriptor.key
                origins = tuple(Provenance((key.namespace, *key.key),
                    ("face", face.feature_key.hex()), (face.axis, face.side)) for face in faces)
                descriptor = replace(descriptor, value=replace(descriptor.value, face_origins=origins))
            result.append(descriptor)
        return tuple(result)


def decode_candidate(payload, *, source_bytes, execution_identity):
    """Decode a complete same-candidate envelope without executing a process."""
    try:
        if type(source_bytes) is not bytes or type(execution_identity) is not tuple:
            _fail("Native candidate decoding requires original bytes and an immutable execution identity.")
        envelope = strict_json_loads(payload)
        _shape(envelope, ("ok", "schema", "candidate", "source", "legacySnapshot", "neutralSources"))
        if envelope["ok"] is not True or envelope["schema"] != "geometry-neutral-source-envelope/1":
            _fail("Native source envelope schema is unsupported.")
        candidate = _shape(envelope["candidate"], ("id", "baseRevision"))
        identity = _hash(candidate["id"])
        revision = candidate["baseRevision"]
        if type(revision) is not int or not 0 <= revision <= 0xFFFFFFFFFFFFFFFF:
            _fail("Native candidate revision must be an exact uint64.")
        hashes = _shape(envelope["source"], ("sha256Before", "sha256After"))
        original = sha256(source_bytes).hexdigest()
        if _hash(hashes["sha256Before"]) != original or _hash(hashes["sha256After"]) != original:
            _fail("Native source bytes changed or belong to another input.", code="BASE_RUNTIME_CHANGED")
        snapshot = envelope["legacySnapshot"]
        if type(snapshot) is not dict or snapshot.get("ok") is not True or snapshot.get("schema") != "geometry-base-snapshot/1" or type(snapshot.get("base_scene")) is not str:
            _fail("Native source envelope has no matching legacy snapshot.")
        if any(type(snapshot.get(name)) is not list for name in ("specs", "placements", "solids", "unplaced_timbers", "dependencies")):
            _fail("Native source envelope has an incomplete legacy snapshot.")
        if sha256(snapshot["base_scene"].encode("utf-8")).hexdigest() != identity:
            _fail("Native candidate identity disagrees with its full canonical definitions.")
        graph = _shape(envelope["neutralSources"], ("schema", "candidate", "coverage", "providers", "nodes", "edges", "roots"))
        graph_candidate = _shape(graph["candidate"], ("id", "baseRevision"))
        if (graph["schema"] != "geometry-neutral-sources/1" or graph_candidate != candidate
                or type(graph_candidate["baseRevision"]) is not int):
            _fail("Native geometry and source graph belong to different candidates.")
        coverage = _shape(graph["coverage"], ("complete", "rootsComplete", "missingGroups"))
        if coverage["complete"] is not True or coverage["rootsComplete"] is not True or _array(coverage["missingGroups"]):
            _fail("Native source graph coverage is incomplete; snapshot-only evaluation is unavailable.", code="BASE_SOURCE_COVERAGE")
        decoder = _Decoder(graph["providers"])
        descriptors = decoder.descriptors(graph["nodes"], graph["edges"])
        roots = decoder.roots(graph["roots"], descriptors)
        descriptors = decoder.face_values(descriptors, roots)
        result = NativeCandidate(canonical_bytes(snapshot), identity, revision, original,
            tuple(sorted(decoder.providers.items())), descriptors, roots, execution_identity)
        validate_program(result.program())
        return result
    except EvaluationError as error:
        raise ModelError("UNSUPPORTED", "BASE_SOURCE_PROTOCOL", "I32", "Invalid typed native source graph: " + error.code) from error
