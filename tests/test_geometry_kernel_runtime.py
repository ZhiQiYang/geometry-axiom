"""Frozen legacy wire oracles for the product path through the neutral graph.

The exact native snapshot fixtures are supplied at the established loader seam.
This suite does not replace the real native adapter replay gate.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
from modeling import ModelError, canonical_bytes
from modeling.common import digest
from modeling.engine import evaluate


def placement(identity=1, *, origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0), n=(0, 0, 1), holes=()):
    return {"id": identity, "boundary_id": identity, "origin": list(origin), "u": list(u), "v": list(v), "n": list(n),
            "outline": [[0, 0], [20, 0], [20, 20], [0, 20]], "holes": list(holes)}


def solid(identity=1, origin=(0, 0, 0), upper=(20, 20, 20), kind="column"):
    local = [
        [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
        [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
        [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
        [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    ]
    return {"kind": kind, "id": identity, "placement_id": None, "boundary_id": None,
            "faces": [{"feature": "face-" + str(i), "vertices": [[origin[a]+p[a]*upper[a] for a in range(3)] for p in points]} for i, points in enumerate(local)]}


def snapshot(*, placements=(), solids=(), specs=(), profiles=(), dependencies=()):
    return {"schema": "geometry-base-snapshot/1", "base_scene": "# preserved native source\n",
            "placements": list(placements), "solids": list(solids), "specs": list(specs),
            "profile_runs": list(profiles), "dependencies": list(dependencies), "required_capabilities": []}


def ref(kind, identity):
    return {"kind": kind, "id": identity}


def request(*roots, role="geometry", target="solid-set", partial=False):
    return {"roots": list(roots), "role": role, "target": target, "allow_partial": partial}


def case(base, extensions, req, **options):
    return base, {"base_scene": base["base_scene"], "extensions": extensions}, req, options


def shell_case(*, closed=True, inward=False, obstacles=()):
    rows = [placement(1, u=(0, 0, 1), v=(0, 1, 0), n=(-1, 0, 0)),
            placement(2, origin=(20, 0, 0), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0)),
            placement(3, u=(1, 0, 0), v=(0, 0, 1), n=(0, -1, 0)),
            placement(4, origin=(0, 20, 0), u=(0, 0, 1), v=(1, 0, 0), n=(0, 1, 0)),
            placement(5, u=(0, 1, 0), v=(1, 0, 0), n=(0, 0, -1)),
            placement(6, origin=(0, 0, 20))]
    rows = rows[:6 if closed else 5]
    base = snapshot(placements=rows, solids=obstacles)
    extensions = [{"kind": "shell", "id": 9, "uses": [{"placement_id": p["id"], "orientation": -1 if inward else 1, "purpose": "boundary"} for p in reversed(rows)]},
                  {"kind": "composite_space", "id": 10, "shell_id": 9, "obstacles": [ref(item["kind"], item["id"]) for item in obstacles]}]
    return base, extensions


def profile(identity=8, coordinate_space="local"):
    return {"id": identity, "profile_id": 7, "coordinate_space": coordinate_space, "origin": [3, 7, 11],
            "u": [1, 0, 0], "v": [0, 1, 0], "n": [0, 0, 1], "length": 30,
            "outline": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "members": [{"id": 1, "kind": "panel", "rect": [0, 0, 10, 2], "dimensions_mm": [10, 2, 30], "definition": {"orientation": "uv"}},
                        {"id": 2, "kind": "timber", "rect": [0, 2, 2, 10], "dimensions_mm": [2, 8, 30], "definition": {"orientation": "vu"}}]}


def cases():
    results = {}
    base = snapshot(placements=(placement(),), specs=({"name": "lo", "value": 0}, {"name": "hi", "value": 20}))
    extrusion = {"kind": "extrusion", "id": 50, "placement_id": 1, "lo_spec": "lo", "hi_spec": "hi"}
    results["placement"] = case(base, [], request(ref("placement", 1), target="surface-set"))
    results["extrusion"] = case(base, [extrusion], request(ref("extrusion", 50)))
    holed = deepcopy(base)
    holed["placements"][0]["holes"] = [[[5, 5], [15, 5], [15, 15], [5, 15]]]
    results["holed"] = case(holed, [extrusion], request(ref("extrusion", 50)))
    boxes = snapshot(solids=(solid(), solid(2, (5, 5, 5), (10, 10, 10))))
    difference = {"kind": "composition", "id": 90, "op": "DIFFERENCE", "base": ref("column", 1), "tools": [ref("column", 2)]}
    results["cavity"] = case(boxes, [difference], request(ref("composition", 90)))
    results["empty"] = case(boxes, [{**difference, "tools": [ref("column", 1)]}], request(ref("composition", 90)))
    keep = {"kind": "composition", "id": 80, "op": "KEEP", "inputs": [ref("column", 2), ref("column", 1)]}
    results["keep"] = case(boxes, [keep], request(ref("composition", 80)))
    nested = {"kind": "composition", "id": 81, "op": "KEEP", "inputs": [ref("composition", 80)]}
    results["nested_keep"] = case(boxes, [keep, nested], request(ref("composition", 81)))
    base_closed, extensions = shell_case(obstacles=(solid(20, (5, 5, 5), (10, 10, 10)),))
    results["enclosure"] = case(base_closed, extensions, request(ref("composite_space", 10), role="enclosure"))
    results["clearance"] = case(base_closed, extensions, request(ref("composite_space", 10), role="clearance"))
    results["shell"] = case(base_closed, extensions, request(ref("shell", 9), target="surface-set"))
    base_open, opened = shell_case(closed=False)
    results["open_boundary"] = case(base_open, opened, request(ref("composite_space", 10), role="enclosure", target="surface-set"))
    results["open_interior"] = case(base_open, opened, request(ref("composite_space", 10), role="clearance"))
    results["open_partial"] = case(base_open, opened, request(ref("composite_space", 10), role="clearance", partial=True))
    inward_base, inward = shell_case(inward=True)
    results["unselected_inward"] = case(inward_base, inward, request(ref("placement", 1), target="surface-set"))
    results["missing_reference"] = case(boxes, [{**difference, "tools": [ref("column", 99)]}], request(ref("column", 1)))
    results["forward_reference"] = case(boxes, [nested, keep], request(ref("composition", 81)))
    cycle = {**keep, "inputs": [ref("composition", 81)]}
    results["cycle"] = case(boxes, [cycle, nested], request(ref("column", 1)))
    results["keep_operand"] = case(boxes, [keep, {**difference, "tools": [ref("composition", 80)]}], request(ref("column", 1)))
    results["unknown_capability"] = case(boxes, [difference], request(ref("composition", 90)), capabilities=["unknown/1"])
    results["invalid_before_capability"] = case(inward_base, inward, request(ref("placement", 1), target="surface-set"), capabilities=[])
    inward_box_base, inward_box = shell_case(inward=True, obstacles=(solid(20, (5, 5, 5), (10, 10, 10)),))
    results["inward_with_obstacle"] = case(inward_box_base, inward_box, request(ref("placement", 1), target="surface-set"))
    missing_two = {**difference, "tools": [ref("column", 98), ref("column", 99)]}
    results["multiple_missing_references"] = case(boxes, [missing_two], request(ref("column", 1)))
    results["missing_root"] = case(boxes, [], request(ref("column", 99)))
    results["wrong_role"] = case(boxes, [], request(ref("column", 1), role="enclosure"))
    results["local_profile"] = case(snapshot(solids=(solid(),), profiles=(profile(),)), [], request(ref("column", 1), ref("profile-run", 8)))
    results["world_profile"] = case(snapshot(solids=(solid(),), profiles=(profile(coordinate_space="world"),)), [], request(ref("column", 1), ref("profile-run", 8)))
    profile_dependencies = ({"kind": "profile-run", "id": 8, "refs": [ref("column", 1)]},)
    results["unselected_profile_dependencies"] = case(snapshot(solids=(solid(),), profiles=(profile(),), dependencies=profile_dependencies), [], request(ref("column", 1)))
    return results


def execute(evaluator, inputs):
    base, definitions, req, options = deepcopy(inputs)
    with mock.patch("modeling.base.load_base", return_value=base):
        try:
            return {"result": evaluator(definitions, req, **options)}
        except ModelError as error:
            return {"error": error.as_dict()}


# Captured from 3a9dc84 (pre-neutral-controller engine), not the new compiler.
FROZEN_DIGESTS = {
    "placement": "bfa6a8f85d0d724f8abd82cae1d6f133ed88c8110f49534dd8bda8f9dde70251",
    "extrusion": "9b5d167490dddd483971f93a3e5f2313603df09ea968469a58b9d8ca83c67b32",
    "holed": "46aa481d950ef45103f192501407611f5da9922165ffe34f6129dbab3f421316",
    "cavity": "118b27caf9a15cee8ac5487135dcdd5c958e9728fc592d0c2ff826fdc818d04d",
    "empty": "0933bcfa4ce96d862dfa4b0ca6366d6544fcec8b08508f47fe89841d2d5e2d7c",
    "keep": "661863c4c92d48d6360011d78c350209a6a0b7b708ed5d2d7b3b49225c8f4939",
    "nested_keep": "bee210fa29ffc46791d9d593ef0f5816dda6c8a9d15b71c3a54972383a9f33cb",
    "enclosure": "ef4bd399363b2e98cb206c0d0b480ff97c26e100a78e2a7932ef22f375f6543f",
    "clearance": "3d259284ec4e936580f96b787daa607616f83abce77f0a2f90b5fcf8dc51a93f",
    "shell": "0bc304dd87915dd9683ad8057cc83e763e7f1afe1c77d92b9918dd6b6951c9d8",
    "open_boundary": "2e457d0328295a7e6a8133277f7b5f890bdab147138c7908d3b955467c8d154a",
    "open_interior": "266a10372eac4e222817c131bebf92615b8f33d84aa1b3a2c3e0700fdc19ea17",
    "open_partial": "9af8f280aabc647f342ec3584c3e82f2a40d22b44bf4a79ed6ea293d14141122",
    "unselected_inward": "8e3882a9012dbbaa98d76ec2bc920549aea20796825e99e2ee5e7de61da11e0a",
    "missing_reference": "6700e6137525eaad955cebd3372cc016f763ee785234d6abaadd475266e7a287",
    "forward_reference": "fa8231d08486bb260ffc2fb0de9c0ba6f204f40c2ab654282cfae7ad6960392e",
    "cycle": "0e15ef4d4b70add6214c0ab345a46511d05c6bdae1f5a5751dcf634d76b4326a",
    "keep_operand": "c2c6e1580df5065176256e57835d22fead68ff043a8f215b1425b7e69f5ac82d",
    "unknown_capability": "b7f98335838aca703d79df9967dd7c1b1ae2db6b4b496ad52ca5a72f94235419",
    "invalid_before_capability": "a11e48df9ee5cec1ff750ee995aae61fd22a89406c44af35a1be4298ae5cc1f7",
    "inward_with_obstacle": "8e3882a9012dbbaa98d76ec2bc920549aea20796825e99e2ee5e7de61da11e0a",
    "multiple_missing_references": "99c2acdc94d9b63e373249639d9b43efd284f35669d17b1d600cffd834cfff13",
    "missing_root": "103784876321b87273680554f023ea22524ec34fa8ad8f4bc1606ac084183129",
    "wrong_role": "f600581d6f13b82290747b8d668f55c027a8638fff9f1dc2e26db03c6f392231",
    "local_profile": "1f05d7152cce63efc5486d1274dabaec724076fdfec9afd9dc88b7b2920ae877",
    "world_profile": "217760df66e49881376ff33d560dfa6574dd93d9ca7331dc056957c244d069cf",
    "unselected_profile_dependencies": "a692f2a71692f030c345ae6f599c32b20a3d2d0c73da2b73b7b0418a538ada6b",
}


class KernelRuntimeTests(unittest.TestCase):
    def test_product_evaluator_preserves_frozen_wire_and_diagnostics(self):
        fixtures = cases()
        self.assertEqual(set(fixtures), set(FROZEN_DIGESTS))
        for name, inputs in fixtures.items():
            with self.subTest(case=name):
                self.assertEqual(FROZEN_DIGESTS[name], digest(execute(evaluate, inputs)))

    def test_product_path_calls_public_neutral_evaluator(self):
        import geometry_kernel
        with mock.patch.object(geometry_kernel, "evaluate", wraps=geometry_kernel.evaluate) as call:
            output = execute(evaluate, cases()["cavity"])
        self.assertEqual("7000", output["result"]["derived"]["objects"][0]["volume_mm3"])
        self.assertEqual(1, call.call_count)
        self.assertIsInstance(call.call_args.args[0], geometry_kernel.Program)


if __name__ == "__main__":
    unittest.main()
