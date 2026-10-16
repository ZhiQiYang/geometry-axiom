"""Host compatibility adapter for the shared exact geometry kernel.

This module translates legacy snapshots and provenance. Geometry algorithms
are implemented only by geometry_kernel and used by every product caller.
"""
from dataclasses import replace
from functools import wraps

from geometry_kernel import geometry as kernel
from geometry_kernel.errors import EvaluationError
from geometry_kernel.types import FrameDef, RegionDef, BoxDef, Provenance
from .common import ModelError
from .kernel_errors import translate

DEFAULT_MAX_CELLS = kernel.DEFAULT_MAX_CELLS
MAX_SOURCE_FACES = kernel.MAX_SOURCE_FACES
_LIMIT = kernel._LIMIT
Face = kernel._Face
Geometry = kernel._Geometry


def _adapt(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except EvaluationError as error:
            raise translate(error) from error
    return call


def _provenance(source, feature, placement_id=None, boundary_id=None, loop_index=-1, edge_index=-1):
    origin = source["origin"]
    return Provenance(
        (origin["kind"], origin["id"], placement_id, boundary_id),
        (feature, loop_index, edge_index),
        (origin["kind"], origin["id"], feature, loop_index, edge_index),
        tuple(source.get("operation_path", [])), source.get("role", "boundary"))


def _source_record(source):
    kind, identity, placement_id, boundary_id = source.origin_handle
    feature, loop_index, edge_index = source.feature_key
    return {"origin": {"kind": kind, "id": identity}, "feature": feature,
            "placement_id": placement_id, "boundary_id": boundary_id,
            "loop_index": loop_index, "edge_index": edge_index,
            "operation_path": list(source.operation_path), "role": source.contribution,
            "normal_sign": source.normal_sign}


def _inputs(placement):
    return (FrameDef(*(placement[key] for key in ("origin", "u", "v", "n"))),
            RegionDef(placement["outline"], placement["holes"]))


@_adapt
def placement_geometry(placement, source):
    frame, region = _inputs(placement)
    origin = _provenance(source, "surface", placement["id"], placement.get("boundary_id"))
    return kernel.placed_region_geometry(frame, region, origin)


@_adapt
def extrusion_geometry(placement, lo, hi, source):
    frame, region = _inputs(placement)
    features = [("bottom_cap", -1, -1), ("top_cap", -1, -1)]
    features += [("outer_side" if i == 0 else "hole_side", i, j)
                 for i, loop in enumerate((region.outer, *region.holes)) for j in range(len(loop))]
    sources = {key: _provenance(source, key[0], placement["id"], placement.get("boundary_id"), key[1], key[2])
               for key in features}
    return kernel.extrusion_geometry(frame, region, lo, hi, sources)


@_adapt
def solid_geometry(solid, source):
    """Verify a native box's complete six faces before constructing a K box."""
    faces = [kernel._face_vertices(face["vertices"], [_provenance(source, face["feature"], solid.get("placement_id"), solid.get("boundary_id"))])
             for face in solid["faces"]]
    if len(faces) != 6:
        raise ModelError("INVALID", "BASE_SOLID", "D7", "A base solid must provide six nondegenerate box faces")
    lower = tuple(min(p[a] for f in faces for p in f.vertices()) for a in range(3))
    upper = tuple(max(p[a] for f in faces for p in f.vertices()) for a in range(3))
    if any(lo >= hi for lo, hi in zip(lower, upper)):
        raise ModelError("INVALID", "BASE_SOLID", "D7", "A base solid must provide six nondegenerate box faces")
    by_side = {(f.axis, f.sign): f for f in faces}
    origins = []
    for axis in range(3):
        a, b = (i for i in range(3) if i != axis)
        expected = {(lower[a], lower[b]), (upper[a], lower[b]), (upper[a], upper[b]), (lower[a], upper[b])}
        for side, sign in enumerate((-1, 1)):
            face = by_side.get((axis, sign))
            if face is None or face.coord != (lower, upper)[side][axis] or face.holes or len(face.outer) != 4 or set(face.outer) != expected:
                raise ModelError("INVALID", "BASE_SOLID", "D7", "A base solid must provide six nondegenerate box faces")
            origins.append(face.sources[0])
    definition = BoxDef(FrameDef((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), lower, upper, tuple(origins))
    return kernel.box_geometry(definition)


def prefix(geometry, path=(), cut=False):
    if not path and not cut:
        return geometry
    return replace(geometry, faces=tuple(replace(face, sources=tuple(
        source.prefixed(path, contribution="cut" if cut else None) for source in face.sources)) for face in geometry.faces))


@_adapt
def mesh_objects(geometry, grid, root, member_path=None, role="geometry", volume_known=None, max_cells=DEFAULT_MAX_CELLS):
    records = kernel.mesh_objects(geometry, grid, volume_known=volume_known, max_cells=max_cells)
    for record in records:
        record.update(root=dict(root), member_path=list(member_path or []), role=role)
        record["face_sources"] = [[_source_record(source) for source in sources] for sources in record["face_sources"]]
    return records


build_grid = _adapt(kernel.build_grid)
analyze_shell = _adapt(kernel.analyze_shell)
enclosed_geometry = _adapt(kernel.enclosed_geometry)
boolean_geometry = _adapt(kernel.boolean_geometry)
