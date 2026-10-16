"""Legacy low-level profile seam, forwarding policy to W and geometry to K."""
from geometry_kernel import geometry as kernel
from geometry_kernel import EvaluationError

from .bootstrap import default_provider
from .model_common import ModelError
from .model_geometry import mesh_objects
from .kernel_errors import translate


def geometries(run):
    items = []
    for definition in default_provider().profile_objects(run):
        region = definition.region
        features = [("bottom_cap", -1, -1), ("top_cap", -1, -1)]
        features += [("outer_side" if i == 0 else "hole_side", i, j)
                     for i, loop in enumerate((region.outer, *region.holes)) for j in range(len(loop))]
        sources = {key: definition.source.feature(key) for key in features}
        try:
            geometry = kernel.extrusion_geometry(definition.frame, region, 0, definition.length, sources)
        except EvaluationError as error:
            raise translate(error) from error
        items.append((geometry, dict(definition.metadata)))
    return items


def output(run, items, grid, *, max_cells):
    provider = default_provider()
    definitions = provider.profile_objects(run)
    root = {"kind": "profile-run", "id": run["id"]}
    if len(items) != len(definitions):
        raise ModelError("INVALID", "PROFILE_MESH", "R37", "A section-profile object must produce one complete solid", root=root)
    objects = []
    for (geometry, _metadata), definition in zip(items, definitions):
        result = mesh_objects(geometry, grid, root, member_path=definition.member_path,
                              role=definition.export_role, max_cells=max_cells)
        if len(result) != 1:
            raise ModelError("INVALID", "PROFILE_MESH", "R37", "A section-profile object must produce one complete solid", root=root)
        try:
            result[0]["section_profile"] = provider.annotate_profile(definition, result[0])
        except ValueError as error:
            if not hasattr(error, "clause"):
                raise
            raise ModelError(error.status, error.code, error.clause, error.message, path=error.path, root=root) from error
        objects.extend(result)
    return objects
