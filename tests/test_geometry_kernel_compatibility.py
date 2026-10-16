"""Frozen pre-extraction mesh ordering and the production facade's K seam."""
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))
from modeling import geometry as legacy
from modeling.common import digest
from modeling.engine import _prefix


def placement(outline=None, holes=(), origin=(0, 0, 0)):
    return {"id": 5, "boundary_id": 8, "origin": list(origin), "u": [1, 0, 0],
            "v": [0, 1, 0], "n": [0, 0, 1],
            "outline": outline or [[0, 0], [20, 0], [20, 20], [0, 20]],
            "holes": list(holes)}


def source(identity=9):
    return {"origin": {"kind": "extrusion", "id": identity}, "operation_path": [], "role": "boundary"}


def frozen_mesh_cases():
    p = placement(holes=[[[5, 5], [5, 15], [15, 15], [15, 5]]])
    hole = legacy.extrusion_geometry(p, -2, 7, source())
    reverse = legacy.extrusion_geometry(placement(list(reversed(p["outline"])), p["holes"]), -2, 7, source())
    outer = legacy.extrusion_geometry(placement(), 0, 20, source(1))
    tool = legacy.extrusion_geometry(placement([[5, 5], [15, 5], [15, 15], [5, 15]]), 5, 15, source(2))
    cavity = legacy.boolean_geometry("DIFFERENCE", [_prefix(outer, ["base"]), _prefix(tool, ["tools", "0"], cut=True)])
    splitting = legacy.extrusion_geometry(placement([[8, -1], [12, -1], [12, 21], [8, 21]]), -1, 21, source(3))
    split = legacy.boolean_geometry("DIFFERENCE", [outer, splitting])
    empty = legacy.boolean_geometry("DIFFERENCE", [outer, outer])
    return {name: legacy.mesh_objects(g, legacy.build_grid([g]), {"kind": "composition", "id": 30})
            for name, g in {"hole": hole, "reverse": reverse, "cavity": cavity, "split": split, "empty": empty}.items()}


# Captured from cdaa2010ca27ba011b5e21fabccbab93a574c7b4 before extraction.
FROZEN_DIGESTS = {
    "hole": "f3c7c54550c088fbdb62b92270270dd3df1d1bd5baadc4a43397d0a947d939f7",
    "reverse": "45641a2e8ee55a58c798a8e43dc9ba25ad063278f44498d62c782697bc7f8e63",
    "cavity": "5c1902eaf69008080329016608d36c6b93bf59a5a38928674069de59d3e5ccdc",
    "split": "041e4265ef2dddef3d4d992aada97b365d2b8122230e59d2c08e3ca8c0b033cc",
    "empty": "1c4409702e8f254813ae74ebe7ca5887503b7390028026d4f1b0ff0bd3aa7e85",
}


class GeometryKernelCompatibilityTests(unittest.TestCase):
    def test_pre_extraction_meshes_are_byte_identical(self):
        self.assertEqual({name: digest(value) for name, value in frozen_mesh_cases().items()}, FROZEN_DIGESTS)


if __name__ == "__main__":
    unittest.main()
