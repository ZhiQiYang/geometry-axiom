"""R37/R39 meshes from the authoritative native section-profile snapshot.

Dimensions, containment, collision and positioning are evaluated in C. This
module only turns the resulting exact rectangles/frame into the existing R29
mesh format. Local runs use independent coordinate spaces, never world axes.
"""
from copy import deepcopy

from .common import ModelError
from . import geometry as geo


def geometries(run):
    """Return one member geometry per native member, and the actual envelope."""
    root = {"kind": "profile-run", "id": run["id"]}
    frame = {key: deepcopy(run[key]) for key in ("origin", "u", "v", "n")}
    frame.update(id=None, boundary_id=None, holes=[])
    items = []
    for member in sorted(run["members"], key=lambda item: item["id"]):
        u0, v0, u1, v1 = member["rect"]
        placement = dict(frame, outline=[[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
        source = {"origin": root, "operation_path": ["members", str(member["id"])], "role": "boundary"}
        geometry = geo.extrusion_geometry(placement, 0, run["length"], source)
        items.append((geometry, {
            "run_id": run["id"], "profile_id": run["profile_id"],
            "member_id": member["id"], "kind": member["kind"],
            "coordinate_space": run["coordinate_space"],
            "dimensions_mm": list(member["dimensions_mm"]),
            "orientation": member["definition"]["orientation"],
        }))
    placement = dict(frame, outline=deepcopy(run["outline"]))
    source = {"origin": root, "operation_path": ["profile", str(run["profile_id"])], "role": "reference"}
    envelope = geo.extrusion_geometry(placement, 0, run["length"], source)
    items.append((envelope, {
        "run_id": run["id"], "profile_id": run["profile_id"],
        "member_id": None, "kind": "envelope",
        "coordinate_space": run["coordinate_space"],
        "dimensions_mm": None, "orientation": None,
    }))
    return items


def output(run, items, grid, *, max_cells):
    root = {"kind": "profile-run", "id": run["id"]}
    objects = []
    for geometry, metadata in items:
        reference = metadata["kind"] == "envelope"
        result = geo.mesh_objects(geometry, grid, root,
                                  member_path=[] if reference else [metadata["member_id"]],
                                  role="reference" if reference else "geometry", max_cells=max_cells)
        # A native member is a positive rectangle and a profile a connected
        # simple polygon; neither can silently become an empty/partial mesh.
        if len(result) != 1 or result[0]["status"] != "COMPLETE":
            raise ModelError("INVALID", "PROFILE_MESH", "R37", "A section-profile object must produce one complete solid", root=root)
        obj = result[0]
        vertices = obj["vertices_mm"]
        details = dict(metadata)
        details["bounds_mm"] = [[min(p[a] for p in vertices) for a in range(3)],
                                [max(p[a] for p in vertices) for a in range(3)]]
        details["material_volume_mm3"] = "0" if reference else obj["volume_mm3"]
        if not reference:
            a, b, length = metadata["dimensions_mm"]
            if obj["volume_mm3"] != str(a * b * length):
                raise ModelError("INVALID", "PROFILE_VOLUME", "R37", "Native dimensions and derived exact member volume disagree", root=root)
        obj["section_profile"] = details
        objects.append(obj)
    return objects
