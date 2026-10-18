"""Domain admission and capabilities; no host imports or geometry algorithms."""
from dataclasses import dataclass


# Not frozen: Python writes __traceback__ on chained exceptions (unittest,
# contextlib).  eq=False keeps BaseException's identity __eq__/__hash__;
# the dataclass default eq=True would set __hash__ to None.
@dataclass(eq=False)
class PolicyIssue(ValueError):
    code: str
    clause: str
    message: str
    path: tuple = ()
    root: tuple | None = None
    status: str = "INVALID"


class WoodworkingModelProvider:
    identity = ("woodworking-model", 1)
    source_capabilities = frozenset({"engineering-spec/1", "parameters/1", "section-profile/1"})
    extension_kinds = frozenset({"extrusion", "shell", "composite_space", "composition"})
    primitive_solids = frozenset({"column", "beam", "timber", "extrusion"})
    geometry_kinds = frozenset({"placement", "shell", "composition"}) | primitive_solids
    root_kinds = geometry_kinds | {"composite_space", "profile-run"}
    kind_capability = {
        "extrusion": "extrusion/1", "shell": "shell/1",
        "composite_space": "composite-space/1", "composition": "solid-composition/1",
    }
    capabilities = (
        "composite-space/1", "extrusion/1", "model-export/1", "shell/1",
        "solid-composition/1", "engineering-spec/1", "parameters/1", "section-profile/1",
    )

    def admit_root(self, key, records, target, role, path=()):
        if key[0] == "profile-run":
            if role != "geometry" or target != "solid-set":
                raise PolicyIssue("TARGET_TYPE", "R39", "ProfileRun requires geometry role and solid-set target", path, key)
            return
        if key[0] == "composite_space":
            if role not in ("enclosure", "clearance"):
                raise PolicyIssue("TARGET_TYPE", "D24", "CompositeSpace requires enclosure or clearance role", path, key)
            return
        if role != "geometry":
            raise PolicyIssue("TARGET_TYPE", "D24", "This root requires geometry role", path, key)
        if key[0] in ("placement", "shell") and target == "solid-set":
            raise PolicyIssue("TARGET_TYPE", "D24", "A zero-thickness face or shell is not a material solid", path)
        if key[0] == "composition" and records[key]["op"] == "KEEP":
            for i, item in enumerate(records[key]["inputs"]):
                self.admit_root((item["kind"], item["id"]), records, target, role, (*path, "inputs", str(i)))

    def bind_sources(self, base, sources, roots):
        from .model_sources import bind_sources
        return bind_sources(base, sources, roots)

    def profile_objects(self, run, sources=None):
        from .section_profile import profile_objects
        return profile_objects(run, sources)

    def annotate_profile(self, definition, mesh):
        from .section_profile import annotate_profile
        return annotate_profile(definition, mesh)
