"""Black-box acceptance of explicit plan/faces-to-space authoring.

Uses the authoritative C adapter and reconstructs every exported package.
No source projection is mutated and no geometry is manufactured in the UI.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-web"))
import space_modeling as sm
import modeling
from modeling import ModelError, verify_package
from modeling.base import load_base


def request(example=0, walls=False):
    e = sm.examples()["examples"][example]
    result = {k: deepcopy(e[k]) for k in ("base_scene", "placement_id", "settings")}
    result.update(mode="plan", obstacles=[])
    if not walls:
        result["settings"]["wall_thickness"] = None
    return result


def bounds(package):
    points = [p for o in package["derived"]["objects"] for p in o["vertices_mm"]]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def mesh_volume(package):
    """Independent signed tetrahedral mesh volume, not engine cell occupancy."""
    volume6 = 0
    for obj in package["derived"]["objects"]:
        verts = obj["vertices_mm"]
        for triangle in obj["triangles"]:
            a, b, c = [verts[i] for i in triangle]
            cross = [b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2], b[0] * c[1] - b[1] * c[0]]
            volume6 += sum(a[i] * cross[i] for i in range(3))
    assert volume6 % 6 == 0
    return volume6 // 6


def timber_request(*, axes="u +x v +y", side="+n", origin="0 0 2500", placement=1):
    data = request()
    data["base_scene"] = ("boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan\n"
                          f"placement {placement} on boundary 1 origin {origin} {axes}\n"
                          "timber 0 27 33 role boundary\n"
                          f"place 0 on {placement} at-face e0 +u {side}\n")
    data.update(placement_id=placement, timbers=[{"kind": "timber", "id": 0}])
    data["settings"]["height"] = 3000
    return data


def frame_request():
    example = next(e for e in sm.examples()["examples"] if e["id"] == "timber-frame")
    return {**{key: deepcopy(example[key]) for key in ("base_scene", "placement_id", "settings", "timbers")},
            "mode": "plan", "obstacles": []}


def assert_closed_mesh(test, package):
    """Independent manifold check on each exported rectangular material."""
    for obj in package["derived"]["objects"]:
        edges = {}
        for triangle in obj["triangles"]:
            for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                edges.setdefault(tuple(sorted((a, b))), []).append((a, b))
        test.assertTrue(edges)
        for directions in edges.values():
            test.assertEqual(len(directions), 2)
            test.assertEqual(directions[0], directions[1][::-1])


def mesh_contains(package, point):
    """Independent +X ray against exported triangles; never reads engine cells.

    Test probes are strictly off boundaries. Deduplicate coplanar triangle hits
    so a quad's triangulation diagonal does not count as two intersections.
    """
    def cross(a, b, p):
        return (b[1] - a[1]) * (p[2] - a[2]) - (b[2] - a[2]) * (p[1] - a[1])
    for obj in package["derived"]["objects"]:
        hits = set()
        for triangle in obj["triangles"]:
            a, b, c = [obj["vertices_mm"][i] for i in triangle]
            if a[0] != b[0] or b[0] != c[0] or a[0] <= point[0]:
                continue
            sides = [cross(a, b, point), cross(b, c, point), cross(c, a, point)]
            if all(v >= 0 for v in sides) or all(v <= 0 for v in sides):
                hits.add(a[0])
        if len(hits) % 2:
            return True
    return False


def assert_exact_box(test, obj, expected):
    """Check a hand-specified material box, not a second engine-derived bbox."""
    one = {"derived": {"objects": [obj]}}
    test.assertEqual(bounds(one), expected)
    lo, hi = expected
    test.assertEqual(mesh_volume(one), (hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2]))
    assert_closed_mesh(test, one)
    for triangle in obj["triangles"]:
        a, b, c = [obj["vertices_mm"][i] for i in triangle]
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        normal = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        axes = [i for i in range(3) if normal[i]]
        test.assertEqual(len(axes), 1, "nondegenerate orthogonal box face")
        axis = axes[0]
        test.assertEqual(a[axis], hi[axis] if normal[axis] > 0 else lo[axis], "face must lie on the correct outward box plane")


# Hand calculation from 4000×3000, A=27, B=33 and guide centers 2000/1500.
# Odd A is split 13/14 at guide centers by the approved integer placement rule.
FRAME_BOXES = {
    10: [[0, 0, 2500], [4000, 27, 2533]],
    11: [[0, 2973, 2500], [4000, 3000, 2533]],
    12: [[3973, 27, 2500], [4000, 2973, 2533]],
    13: [[0, 27, 2500], [27, 2973, 2533]],
    20: [[1987, 27, 2500], [2014, 2973, 2533]],
    30: [[27, 1487, 2500], [1987, 1514, 2533]],
    31: [[2014, 1487, 2500], [3973, 1514, 2533]],
}


class SpaceModelingAcceptance(unittest.TestCase):
    maxDiff = 3000

    def rejects(self, data, code=None):
        with self.assertRaises(ModelError) as caught:
            sm.preview(data)
        if code:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_rectangle_exact_space_and_joined_material(self):
        data = request(walls=True)
        before = deepcopy(data)
        result = sm.preview(data)
        self.assertEqual(data, before)
        self.assertTrue(result["summary"]["closed"])
        self.assertEqual(result["summary"]["face_count"], 6)
        self.assertEqual(result["summary"]["volume_mm3"], "33600000000")
        self.assertEqual(result["summary"]["wall_volume_mm3"], "4032000000")
        self.assertEqual(mesh_volume(result["volume"]), 4_000 * 3_000 * 2_800)
        self.assertEqual(mesh_volume(result["walls"]), (4_200 * 3_200 - 4_000 * 3_000) * 2_800)
        self.assertEqual(bounds(result["walls"]), [[-100, -100, 0], [4100, 3100, 2800]])
        source = load_base(data["base_scene"])
        candidate = load_base(result["space"]["definitions"]["base_scene"])
        self.assertEqual(candidate["placements"][0], source["placements"][0])
        self.assertEqual(result["source_sha256"], hashlib.sha256(source["base_scene"].encode()).hexdigest())
        for key in ("space", "volume", "clearance", "walls"):
            verify_package(result[key])

    def test_l_shape_keeps_concavity_and_unions_overlap(self):
        result = sm.preview(request(1, walls=True))
        self.assertEqual(result["summary"]["face_count"], 8)
        self.assertEqual(result["summary"]["volume_mm3"], "68040000000")
        self.assertEqual(mesh_volume(result["volume"]), (6000 * 4500 - 1800 * 1500) * 2800)
        self.assertEqual(result["summary"]["wall_volume_mm3"], str((21000 * 100 + 4 * 100 * 100) * 2800))
        self.assertEqual(mesh_volume(result["walls"]), 5_992_000_000)

    def test_concavity_and_outward_walls_occupy_the_specified_regions(self):
        result = sm.preview(request(1, walls=True))
        # The missing corner is x>4200,y>3000, not an arbitrary equal-area void.
        for point in ([5101, 3803, 1401], [5901, 4403, 1401]):
            self.assertFalse(mesh_contains(result["volume"], point), point)
        for point in ([5101, 2803, 1401], [4001, 3803, 1401]):
            self.assertTrue(mesh_contains(result["volume"], point), point)
            self.assertFalse(mesh_contains(result["walls"], point), point)
        for point in ([4251, 3803, 1401], [5101, 3053, 1401], [-51, 1203, 1401]):
            self.assertTrue(mesh_contains(result["walls"], point), point)
        for point in ([4351, 3803, 1401], [5101, 3153, 1401], [-151, 1203, 1401]):
            self.assertFalse(mesh_contains(result["walls"], point), point)

    def test_projection_z_does_not_set_room_height(self):
        data = request()
        data["base_scene"] = data["base_scene"].replace("0 0 2500", "0 0 -1700")
        data["settings"].update(bottom=500, height=3200)
        result = sm.preview(data)
        self.assertEqual(result["summary"]["source_z"], -1700)
        self.assertEqual(bounds(result["space"]), [[0, 0, 500], [4000, 3000, 3700]])
        self.assertEqual(result["summary"]["volume_mm3"], str(4000 * 3000 * 3200))

    def test_open_room_keeps_geometry_but_no_volume_or_clearance(self):
        data = request()
        data["settings"]["ceiling"] = "none"
        result = sm.preview(data)
        self.assertEqual(result["space"]["derived"]["status"], "COMPLETE")
        self.assertEqual(result["space"]["derived"]["objects"][0]["closure"], "open")
        self.assertIsNone(result["volume"])
        self.assertIsNone(result["clearance"])
        self.assertFalse(result["summary"]["closed"])
        self.assertIn("未建立頂面", result["summary"]["missing"])

    def test_one_selected_edge_is_valid_open_space(self):
        data = request(walls=True)
        data["settings"].update(edges=[0], floor="none", ceiling="none")
        result = sm.preview(data)
        self.assertEqual(result["summary"]["face_count"], 1)
        self.assertEqual(result["summary"]["wall_volume_mm3"], str(4000 * 100 * 2800))
        self.assertEqual(bounds(result["space"]), [[0, 0, 0], [4000, 0, 2800]])
        self.assertIsNone(result["volume"])

    def test_hole_requires_explicit_role_and_through_survives(self):
        data = request(walls=True)
        data["base_scene"] = data["base_scene"].replace("kind room_plan", "kind room_plan hole 1000,1000 2000,1000 2000,2000 1000,2000")
        self.rejects(data, "SPACE_HOLE_PURPOSE")
        data["settings"]["holes"] = "through"
        result = sm.preview(data)
        self.assertEqual(result["summary"]["face_count"], 10)
        self.assertEqual(mesh_volume(result["volume"]), (4000 * 3000 - 1000 * 1000) * 2800)
        # Only outer walls receive material. No accidental wall inside the hole.
        self.assertEqual(mesh_volume(result["walls"]), 4_032_000_000)

    def test_through_hole_retains_its_exact_location_at_all_heights(self):
        data = request(walls=True)
        data["base_scene"] = data["base_scene"].replace("kind room_plan", "kind room_plan hole 1000,1000 2000,1000 2000,2000 1000,2000")
        data["settings"]["holes"] = "through"
        result = sm.preview(data)
        for z in (1, 1401, 2799):
            for point in ([1501, 1603, z], [1001, 1903, z], [1999, 1103, z]):
                self.assertFalse(mesh_contains(result["volume"], point), point)
                self.assertFalse(mesh_contains(result["walls"], point), point)
            for point in ([999, 1603, z], [2001, 1603, z], [1501, 999, z], [1501, 2001, z]):
                self.assertTrue(mesh_contains(result["volume"], point), point)

    def test_reversed_frame_keeps_world_orientation(self):
        data = request()
        data["base_scene"] = data["base_scene"].replace("u +x v +y", "u -x v +y")
        result = sm.preview(data)
        self.assertEqual(bounds(result["space"]), [[-4000, 0, 0], [0, 3000, 2800]])
        self.assertEqual(mesh_volume(result["volume"]), 33_600_000_000)

    def test_faces_mode_reuses_existing_placements_and_purposes(self):
        vectors = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())
        example = next(c for c in vectors["cases"] if c["id"] == "l_room_eight_faces")
        definitions = example["definitions"]
        uses = deepcopy(next(e for e in definitions["extensions"] if e["kind"] == "shell")["uses"])
        uses[-1]["purpose"] = "calculation-cap"
        result = sm.preview({"base_scene": definitions["base_scene"], "mode": "faces", "uses": uses, "obstacles": []})
        self.assertEqual(result["summary"]["generated_faces"], [])
        self.assertEqual(result["summary"]["volume_mm3"], "68040000000")
        candidate = result["space"]["definitions"]["base_scene"]
        self.assertEqual(candidate, load_base(definitions["base_scene"])["base_scene"])
        saved_uses = next(e for e in result["space"]["definitions"]["extensions"] if e["kind"] == "shell")["uses"]
        self.assertEqual(saved_uses[-1]["purpose"], "calculation-cap")

    def test_selected_obstacle_changes_clearance_only(self):
        data = request()
        data["base_scene"] += "beam 1 along x from 1000 to 2000 at 1500 width 1000 depth 1000 top 2000\n"
        data["obstacles"] = [{"kind": "beam", "id": 1}]
        result = sm.preview(data)
        self.assertEqual(result["summary"]["volume_mm3"], "33600000000")
        self.assertEqual(result["summary"]["clearance_mm3"], "32600000000")
        self.assertEqual(mesh_volume(result["clearance"]), 32_600_000_000)
        data["obstacles"] = [{"kind": "beam", "id": 2}]
        self.rejects(data, "SPACE_OBSTACLES")

    def test_selected_wall_capacity_rejects_whole_request_before_building_packages(self):
        data = request(walls=True)
        # 1 source + 5 unused boundaries + 6 new shell boundaries = 12.
        # Material needs 5 extra carriers: the whole selected request needs 17.
        data["base_scene"] += "".join(f"boundary {i} outline 0,0 10,0 10,10 0,10\n" for i in range(20, 25))
        before = deepcopy(data)
        with mock.patch.object(sm, "_package") as package, mock.patch.object(sm.Declarations, "face") as face:
            error = self.rejects(data, "SPACE_CAPACITY")
        package.assert_not_called()
        face.assert_not_called()
        self.assertEqual(error.status, "UNSUPPORTED")
        self.assertEqual(error.clause, "I33")
        self.assertEqual(error.path, ["settings", "wall_thickness"])
        self.assertIn("邊界面需 17/16，承載面需 12/16", error.message)
        self.assertIn("取消", error.message)
        self.assertEqual(data, before)
        # Boundary-only is a separate, explicitly chosen request.
        data["settings"]["wall_thickness"] = None
        result = sm.preview(data)
        self.assertTrue(result["summary"]["closed"])
        self.assertIsNone(result["walls"])
        self.assertEqual(result["summary"]["wall_diagnostics"], [])
        data["base_scene"] += "".join(f"boundary {i} outline 0,0 10,0 10,10 0,10\n" for i in range(25, 30))
        error = self.rejects(data, "SPACE_CAPACITY")
        self.assertEqual(error.status, "UNSUPPORTED")

    def test_exact_native_limit_remains_admitted_and_placement_capacity_is_independent(self):
        data = request(walls=True)
        data["base_scene"] += "".join(f"boundary {i} outline 0,0 10,0 10,10 0,10\n" for i in range(20, 24))
        result = sm.preview(data)
        self.assertEqual(result["summary"]["wall_volume_mm3"], "4032000000")
        candidate = load_base(result["walls"]["definitions"]["base_scene"])
        self.assertEqual(sum(line.startswith("boundary ") for line in candidate["base_scene"].splitlines()), 16)
        data = request(walls=True)
        data["base_scene"] += "".join(f"placement {i} on boundary 1 origin {i*10000} 0 0 u +x v +y\n" for i in range(20, 25))
        error = self.rejects(data, "SPACE_CAPACITY")
        self.assertIn("邊界面需 12/16，承載面需 17/16", error.message)

    def test_selected_material_specs_are_preflighted_without_changing_requirement(self):
        data = request(walls=True)
        data["base_scene"] += "".join(f"spec unused_{i} {i}\n" for i in range(62))
        with mock.patch.object(sm, "_package") as package:
            error = self.rejects(data, "SPACE_CAPACITY")
        package.assert_not_called()
        self.assertIn("具名規格需 65/64", error.message)
        self.assertEqual(data["settings"]["wall_thickness"], 100)

    def test_material_solver_failure_is_not_downgraded_to_success(self):
        for status, code in (("UNSUPPORTED", "PRECISION"), ("INVALID", "SHELL_ORIENTATION")):
            with self.subTest(status=status):
                data = request(walls=True)
                before = deepcopy(data)
                with mock.patch.object(sm, "_walls", side_effect=ModelError(status, code, "I33", "material solver failure")):
                    error = self.rejects(data, code)
                self.assertEqual(error.status, status)
                self.assertIn("材料牆", error.as_dict()["diagnostics"][0]["message"])
                self.assertEqual(data, before)

    def test_all_namespaces_and_uint_max_ids_are_preserved(self):
        data = request()
        data["base_scene"] += "boundary 4294967295 outline 0,0 10,0 10,10 0,10\nspace 2\n"
        result = sm.preview(data)
        generated_ids = {f["placement_id"] for f in result["summary"]["generated_faces"]}
        self.assertFalse(generated_ids & {1, 2, 4294967295})
        self.assertIn("boundary 4294967295", result["space"]["definitions"]["base_scene"])
        self.assertIn("space 2", result["space"]["definitions"]["base_scene"])

    def test_missing_negative_noninteger_and_unknown_settings_rejected(self):
        for key in ("bottom", "height", "edges", "floor", "ceiling", "holes", "wall_thickness"):
            with self.subTest(missing=key):
                data = request()
                del data["settings"][key]
                self.rejects(data, "SPACE_MISSING_FIELD")
        # (key, value, code): out-of-range / non-integer numbers, a float (JSON_TYPE: only integers are
        # representable), an empty edge list and a duplicated edge selection each have their own code.
        for key, value, code in (("height", -1, "SPACE_INPUT_RANGE"), ("height", 0, "SPACE_INPUT_RANGE"),
                                 ("bottom", True, "SPACE_INPUT_RANGE"), ("wall_thickness", -100, "SPACE_INPUT_RANGE"),
                                 ("height", 1.5, "JSON_TYPE"), ("edges", [], "SPACE_EDGES"), ("edges", [0, 0], "SPACE_EDGES")):
            with self.subTest(key=key, value=value):
                data = request()
                data["settings"][key] = value
                self.rejects(data, code)
        data = request()
        data["settings"]["guess_height"] = 2800
        self.rejects(data, "SPACE_UNKNOWN_FIELD")

    def test_nonhorizontal_missing_source_and_invalid_face_use_rejected(self):
        data = request()
        data["base_scene"] = data["base_scene"].replace("u +x v +y", "u +x v +z")
        self.rejects(data, "SPACE_SOURCE_PLANE")
        data = request()
        data["placement_id"] = 88
        self.rejects(data, "SPACE_SOURCE")
        self.rejects({"mode": "faces", "base_scene": request()["base_scene"], "uses": [{"placement_id": 1, "orientation": 1}], "obstacles": []}, "SPACE_MISSING_FIELD")


class SpaceTimberAcceptance(unittest.TestCase):
    maxDiff = 3000

    def rejects(self, data, code=None):
        before = deepcopy(data)
        with self.assertRaises(ModelError) as caught:
            sm.preview(data)
        self.assertEqual(data, before)
        if code:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_t01_true_material_dimensions_coplanarity_and_replay(self):
        data = timber_request()
        before = deepcopy(data)
        result = sm.preview(data)
        self.assertEqual(data, before)
        self.assertEqual(result["schema"], "geometry-space-preview/2")
        self.assertEqual(bounds(result["timbers"]), [[0, 0, 2500], [4000, 27, 2533]])
        self.assertEqual(mesh_volume(result["timbers"]), 4000 * 27 * 33)
        self.assertEqual(result["summary"]["timber_volume_mm3"], "3564000")
        self.assertEqual(result["summary"]["timber_count"], 1)
        self.assertEqual(result["timbers"]["request"], {"roots": [{"kind": "timber", "id": 0}],
                         "role": "geometry", "target": "solid-set", "allow_partial": False})
        self.assertEqual(result["timbers"]["definitions"], {"base_scene": load_base(data["base_scene"])["base_scene"], "extensions": []})
        self.assertNotEqual(result["space"]["definitions"], result["timbers"]["definitions"])
        assert_closed_mesh(self, result["timbers"])
        self.assertEqual(verify_package(result["timbers"])["derived"], result["timbers"]["derived"])
        for obj in result["timbers"]["derived"]["objects"]:
            for sources in obj["face_sources"]:
                self.assertTrue(sources)
                self.assertTrue(all(s["origin"] == {"kind": "timber", "id": 0} and
                                    s["placement_id"] == 1 and s["boundary_id"] == 1 for s in sources))

    def test_t02_world_orientation_and_translated_origin(self):
        for axes, side, origin, expected in (
            ("u +x v +y", "+n", "0 0 2500", [[0, 0, 2500], [4000, 27, 2533]]),
            ("u +y v +x", "-n", "0 0 2500", [[0, 0, 2500], [27, 4000, 2533]]),
            ("u +x v +y", "-n", "0 0 2500", [[0, 0, 2467], [4000, 27, 2500]]),
            ("u -x v +y", "-n", "100 200 2500", [[-3900, 200, 2500], [100, 227, 2533]]),
        ):
            with self.subTest(axes=axes, side=side, origin=origin):
                result = sm.preview(timber_request(axes=axes, side=side, origin=origin))
                self.assertEqual(bounds(result["timbers"]), expected)
                self.assertEqual(mesh_volume(result["timbers"]), 4000 * 27 * 33)

    def test_t03_placement_zero_and_shared_boundary_do_not_mix_material(self):
        data = timber_request(placement=0)
        data["base_scene"] += ("placement 2 on boundary 1 origin 0 0 3500 u +x v +y\n"
                               "timber 1 27 33 role boundary\nplace 1 on 2 at-face e0 +u +n\n")
        result = sm.preview(data)
        self.assertEqual(result["summary"]["source_placement"], 0)
        self.assertEqual(result["timbers"]["request"]["roots"], [{"kind": "timber", "id": 0}])
        self.assertEqual(bounds(result["timbers"])[0][2], 2500)
        data["timbers"] = [{"kind": "timber", "id": 1}]
        self.assertIn("#1", self.rejects(data, "SPACE_TIMBERS").message)
        data["placement_id"] = 2
        self.assertEqual(bounds(sm.preview(data)["timbers"])[0][2], 3500)

    def test_t04_selected_root_keeps_support_specs_and_original_roles(self):
        data = frame_request()
        data["timbers"] = [{"kind": "timber", "id": 30}]
        result = sm.preview(data)
        package = result["timbers"]
        self.assertEqual([o["root"] for o in package["derived"]["objects"]], data["timbers"])
        self.assertEqual(mesh_volume(package), 1960 * 27 * 33)
        source = package["definitions"]["base_scene"]
        self.assertIn("spec main_x 2000", source)
        self.assertIn("timber 10 27 33 role boundary", source)
        self.assertIn("timber 20 27 33 role primary", source)
        self.assertIn("timber 30 27 33 role secondary", source)
        deps = next(d for d in load_base(source)["dependencies"] if d["kind"] == "timber" and d["id"] == 30)
        self.assertIn({"kind": "timber", "id": 13}, deps["refs"])
        self.assertIn({"kind": "timber", "id": 20}, deps["refs"])
        self.assertEqual(verify_package(package)["derived"], package["derived"])

    def test_t04_main_and_child_grid_dependencies_are_preserved(self):
        data = request()
        data["base_scene"] += (
            "timber 80 20 33 role boundary\nplace 80 on 1 at-face e0 +u +n\n"
            "timber 81 20 33 role boundary\nplace 81 on 1 at-face e2 +u +n\n"
            "grid 1 on 1 main-along v u 1000 3000 v 1000 2000\n"
            "timber 1 20 33 role primary\nplace 1 on 1 at-line grid 1 u 0 +v +n\n"
            "timber 2 20 33 role primary\nplace 2 on 1 at-line grid 1 u 1 +v +n\n"
            "subgrid 2 parent 1 cell u line:0 line:1 v line:0 line:1 divisions u 2 v 2\n"
            "timber 3 20 33 role secondary\nplace 3 on 1 at-line grid 2 v 0 between t1 t2 +u +n\n")
        data["timbers"] = [{"kind": "timber", "id": 3}]
        package = sm.preview(data)["timbers"]
        self.assertEqual(bounds(package), [[1010, 1490, 2500], [2990, 1510, 2533]])
        self.assertEqual(mesh_volume(package), 1980 * 20 * 33)
        self.assertIn("subgrid 2 parent 1", package["definitions"]["base_scene"])
        self.assertEqual([o["root"] for o in package["derived"]["objects"]], data["timbers"])
        verify_package(package)

    def test_t07_material_selection_does_not_change_space_walls_or_clearance(self):
        data = frame_request()
        data["base_scene"] += "beam 90 along x from 1000 to 2000 at 1500 width 1000 depth 1000 top 2000\n"
        data["obstacles"] = [{"kind": "beam", "id": 90}]
        included = sm.preview(data)
        del data["timbers"]
        legacy = sm.preview(data)
        self.assertEqual(legacy["schema"], "geometry-space-preview/1")
        self.assertNotIn("timbers", legacy)
        self.assertNotIn("timber_count", legacy["summary"])
        self.assertNotIn("timber_volume_mm3", legacy["summary"])
        for key in ("space", "volume", "clearance", "walls", "source_sha256", "diagnostics"):
            self.assertEqual(included[key], legacy[key])
        self.assertEqual(included["summary"]["volume_mm3"], "36000000000")
        self.assertEqual(included["summary"]["clearance_mm3"], "35000000000")
        self.assertEqual(included["summary"]["wall_volume_mm3"], "4320000000")
        self.assertEqual(included["summary"]["timber_volume_mm3"], "18494487")
        self.assertEqual(mesh_volume(included["timbers"]), 18494487)

    def test_t08_height_bottom_thickness_changes_leave_timber_geometry_exact(self):
        data = timber_request()
        original = sm.preview(data)["timbers"]
        for bottom, height, thickness in ((0, 3200, 100), (-500, 2000, 150)):
            with self.subTest(bottom=bottom, height=height):
                data["settings"].update(bottom=bottom, height=height, wall_thickness=thickness)
                updated = sm.preview(data)
                self.assertEqual(updated["timbers"], original)
                self.assertEqual(updated["summary"]["top"], bottom + height)

    def test_t12_empty_duplicate_unknown_wrong_type_and_unplaced_are_rejected(self):
        # (refs, code): every shape/identity fault is SPACE_TIMBERS, except a bare non-object entry
        # (SPACE_INPUT) and an extra key inside a reference (SPACE_UNKNOWN_FIELD).
        for refs, code in (([], "SPACE_TIMBERS"), (None, "SPACE_TIMBERS"), ({}, "SPACE_TIMBERS"),
                           ([0], "SPACE_INPUT"), ([{"kind": "beam", "id": 0}], "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": True}], "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": -1}], "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": 4294967296}], "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": 999}], "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": 0}] * 2, "SPACE_TIMBERS"),
                           ([{"kind": "timber", "id": 0, "placement_id": 1}], "SPACE_UNKNOWN_FIELD")):
            with self.subTest(refs=refs):
                data = timber_request()
                data["timbers"] = refs
                self.rejects(data, code)
        data = timber_request()
        data["base_scene"] = data["base_scene"].replace("place 0 on 1 at-face e0 +u +n\n", "")
        # an unplaced timber is refused by the base scene's final check (I9), before any space logic
        self.assertIn("角材 0 沒有 place", self.rejects(data, "BASE_INVALID").message)
        data = timber_request()
        data.update(mode="faces", uses=[{"placement_id": 1, "orientation": 1, "purpose": "boundary"}])
        del data["settings"], data["placement_id"]
        self.rejects(data, "SPACE_UNKNOWN_FIELD")

    def test_t12_capacity_and_verification_failures_do_not_return_partial_success(self):
        data = timber_request()
        before = deepcopy(data)
        with self.assertRaises(ModelError) as capacity:
            sm.preview(data, max_cells=1)
        self.assertEqual(capacity.exception.status, "UNSUPPORTED")
        self.assertEqual(capacity.exception.code, "CAPACITY")
        self.assertIn("#0", capacity.exception.message)
        for operation, error in (("build_package", ModelError("UNSUPPORTED", "CAPACITY", "I33", "budget exceeded")),
                                 ("verify_package", ModelError("INVALID", "SNAPSHOT_MISMATCH", "I31", "bad mesh"))):
            with self.subTest(operation=operation), mock.patch.object(sm, operation, side_effect=error):
                caught = self.rejects(data, error.code)
                self.assertEqual(caught.status, error.status)
                self.assertIn("#0", caught.message)
                self.assertIn("#0", caught.as_dict()["diagnostics"][0]["message"])
        self.assertEqual(data, before)

    def test_t12_reconstructed_package_must_contain_every_requested_root(self):
        data = frame_request()
        package = sm.preview(data)["timbers"]
        for change in (lambda p: p["derived"]["objects"].pop(),
                       lambda p: p["request"].update(allow_partial=True),
                       lambda p: p["derived"]["objects"][0].update(closure="open")):
            corrupted = deepcopy(package)
            change(corrupted)
            with mock.patch.object(sm, "verify_package", return_value=corrupted):
                self.rejects(data, "SPACE_TIMBERS_INCOMPLETE")

    def test_t14_ready_example_is_complete_and_candidates_match_real_material(self):
        example = next(e for e in sm.examples()["examples"] if e["id"] == "timber-frame")
        self.assertEqual([e["id"] for e in sm.examples()["examples"][:2]], ["rectangle", "l-shape"])
        self.assertEqual([e["settings"]["height"] for e in sm.examples()["examples"][:2]], [2800, 2800])
        self.assertEqual(example["settings"]["height"], 3000)
        self.assertEqual([t["length"] for t in example["source"]["timbers"]], [4000, 4000, 2946, 2946, 2946, 1960, 1959])
        self.assertEqual({t["role"] for t in example["source"]["timbers"]}, {"boundary", "primary", "secondary"})
        result = sm.preview(frame_request())
        self.assertEqual(result["summary"]["timber_count"], 7)
        self.assertEqual(mesh_volume(result["timbers"]), (2 * 4000 + 3 * 2946 + 1960 + 1959) * 27 * 33)
        self.assertTrue(all(t["A"] == 27 and t["B"] == 33 and t["z_min"] == 2500 and t["z_max"] == 2533
                            for t in example["source"]["timbers"]))
        assert_closed_mesh(self, result["timbers"])
        verify_package(result["timbers"])
        example["source"]["timbers"].clear()
        self.assertEqual(len(sm.examples()["examples"][2]["source"]["timbers"]), 7)

    def test_t14_each_saved_member_has_its_own_exact_world_geometry(self):
        package = sm.preview(frame_request())["timbers"]
        actual = package["derived"]["objects"]
        self.assertEqual(len(actual), len(FRAME_BOXES))
        self.assertEqual({o["root"]["id"] for o in actual}, set(FRAME_BOXES))
        for obj in actual:
            with self.subTest(timber=obj["root"]):
                self.assertEqual(obj["root"]["kind"], "timber")
                assert_exact_box(self, obj, FRAME_BOXES[obj["root"]["id"]])
                for sources in obj["face_sources"]:
                    self.assertTrue(sources)
                    self.assertTrue(all(s["origin"] == obj["root"] and s["placement_id"] == 1 and s["boundary_id"] == 1 for s in sources))

    def test_t15_material_never_closes_an_open_room(self):
        data = timber_request()
        data["settings"]["ceiling"] = "none"
        result = sm.preview(data)
        self.assertFalse(result["summary"]["closed"])
        self.assertIsNone(result["volume"])
        self.assertIsNone(result["clearance"])
        self.assertEqual(result["timbers"]["derived"]["status"], "COMPLETE")
        self.assertEqual(result["summary"]["timber_count"], 1)


class HistoricalWallReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROOT / "tests/fixtures/issue119-legacy-missing-walls.gcanvas") as archive:
            cls.records = json.loads(archive.read("manifest.json"))["models"]
            pdf = archive.read("sources/3a87c8d7705c15b6a269207c0add8771c1dfa68ad9c33807f109c88a3c76c110")
        assert hashlib.sha256(pdf).hexdigest() == "3a87c8d7705c15b6a269207c0add8771c1dfa68ad9c33807f109c88a3c76c110"

    def test_actual_old_archive_replays_both_records_without_changing_requests(self):
        before = deepcopy(self.records)
        for record in self.records:
            self.assertEqual(sm.replay_stored(record["input"], record["result"]), record["result"])
        self.assertEqual(self.records, before)
        legacy = self.records[0]
        self.assertEqual(legacy["input"]["settings"]["wall_thickness"], 100)
        self.assertIsNone(legacy["result"]["walls"])
        with self.assertRaises(ModelError) as caught:
            sm.preview(legacy["input"])
        self.assertEqual(caught.exception.status, "UNSUPPORTED")

    def test_historical_missing_walls_still_require_exact_geometry_settings_and_diagnostics(self):
        changes = (
            lambda r: r["input"]["settings"].update(height=3200),
            lambda r: r["input"]["settings"].update(wall_thickness=None),
            lambda r: r["result"].update(source_sha256="a" * 64),
            lambda r: r["result"]["space"]["derived"]["objects"][0]["vertices_mm"][0].__setitem__(0, 999),
            lambda r: r["result"]["summary"].update(volume_mm3="1"),
            lambda r: r["result"]["summary"]["wall_diagnostics"][0].update(message="forged failure"),
            lambda r: r["result"]["summary"].update(wall_diagnostics=[]),
        )
        for change in changes:
            record = deepcopy(self.records[0]); change(record)
            before = deepcopy(record)
            with self.assertRaises(ModelError):
                sm.replay_stored(record["input"], record["result"])
            self.assertEqual(record, before)

    def test_removing_a_complete_wall_package_cannot_forge_a_historical_failure(self):
        record = deepcopy(self.records[1])
        record["result"]["walls"] = None
        record["result"]["summary"]["wall_volume_mm3"] = None
        record["result"]["summary"]["wall_diagnostics"] = deepcopy(self.records[0]["result"]["summary"]["wall_diagnostics"])
        with self.assertRaises(ModelError) as caught:
            sm.replay_stored(record["input"], record["result"])
        self.assertEqual(caught.exception.code, "SPACE_STORED_REPLAY")

    def test_supported_historical_package_metadata_is_verified_and_preserved(self):
        for original in self.records:
            record = deepcopy(original)
            for key in ("space", "volume", "clearance", "walls"):
                if record["result"][key] is not None:
                    manifest = record["result"][key]["manifest"]
                    manifest["axiom_revision"], manifest["axiom_sha256"] = next(iter(modeling.LEGACY_AXIOM_VERSIONS))
                    manifest["generator"] = {"name": "historical-author", "version": "0.9"}
            before = deepcopy(record)
            self.assertEqual(sm.replay_stored(record["input"], record["result"]), record["result"])
            self.assertEqual(record, before)
        damaged = deepcopy(record)
        damaged["result"]["space"]["manifest"]["axiom_sha256"] = "0" * 64
        with self.assertRaises(ModelError) as caught:
            sm.replay_stored(damaged["input"], damaged["result"])
        self.assertEqual(caught.exception.code, "AXIOM_VERSION")


if __name__ == "__main__":
    unittest.main()
