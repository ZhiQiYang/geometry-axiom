"""Typed member/envelope requests and R37 metadata, with no mesh implementation."""
from copy import deepcopy
from dataclasses import dataclass

from geometry_kernel import (CoordinateDomain, FrameDef, ProvenanceTemplate,
                             RegionDef, SourceRef)
from .model_policy import PolicyIssue


@dataclass(frozen=True)
class ProfileObject:
    frame: FrameDef | SourceRef
    region: RegionDef | SourceRef
    length: int | SourceRef
    source: ProvenanceTemplate
    metadata: dict

    @property
    def export_role(self):
        return "reference" if self.metadata["kind"] == "envelope" else "geometry"

    @property
    def member_path(self):
        return () if self.metadata["member_id"] is None else (self.metadata["member_id"],)


def profile_objects(run, sources=None):
    if sources is None:
        domain = CoordinateDomain() if run["coordinate_space"] == "world" else CoordinateDomain(("profile-run", run["id"]))
        axes = FrameDef(*(run[key] for key in ("origin", "u", "v", "n")), domain=domain)
    identity = ("profile-run", run["id"])
    objects = []
    for member in sorted(run["members"], key=lambda item: item["id"]):
        if sources is None:
            u0, v0, u1, v1 = member["rect"]
            shape = RegionDef(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
            length = run["length"]
        else:
            axes, shape, length = sources[(run["id"], member["id"])]
        source = ProvenanceTemplate((*identity, None, None), identity, ("members", str(member["id"])))
        metadata = {
            "run_id": run["id"], "profile_id": run["profile_id"],
            "member_id": member["id"], "kind": member["kind"],
            "coordinate_space": run["coordinate_space"],
            "dimensions_mm": list(member["dimensions_mm"]),
            "orientation": member["definition"]["orientation"],
        }
        objects.append(ProfileObject(axes, shape, length, source, metadata))
    source = ProvenanceTemplate((*identity, None, None), identity, ("profile", str(run["profile_id"])), "reference")
    metadata = {
        "run_id": run["id"], "profile_id": run["profile_id"],
        "member_id": None, "kind": "envelope", "coordinate_space": run["coordinate_space"],
        "dimensions_mm": None, "orientation": None,
    }
    if sources is None:
        shape, length = RegionDef(run["outline"]), run["length"]
    else:
        axes, shape, length = sources[(run["id"], None)]
    objects.append(ProfileObject(axes, shape, length, source, metadata))
    return tuple(objects)


def annotate_profile(definition, mesh):
    metadata = definition.metadata
    root = ("profile-run", metadata["run_id"])
    if mesh["status"] != "COMPLETE":
        raise PolicyIssue("PROFILE_MESH", "R37", "A section-profile object must produce one complete solid", root=root)
    reference = metadata["kind"] == "envelope"
    vertices = mesh["vertices_mm"]
    details = deepcopy(metadata)
    details["bounds_mm"] = [[min(p[a] for p in vertices) for a in range(3)],
                            [max(p[a] for p in vertices) for a in range(3)]]
    details["material_volume_mm3"] = "0" if reference else mesh["volume_mm3"]
    if not reference:
        a, b, length = metadata["dimensions_mm"]
        if mesh["volume_mm3"] != str(a * b * length):
            raise PolicyIssue("PROFILE_VOLUME", "R37", "Native dimensions and derived exact member volume disagree", root=root)
    return details
