"""Independent black-box checks for orthogonal-model/1.

The 18 normative vectors are read without modification.  The mesh oracle below
uses only the exported coordinates: it does not import the runtime's geometry,
occupancy, triangulation, topology, or canonicalization helpers.
"""

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import ModelError, ModelWorld, build_package, verify_package

VECTORS = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())
CASES = {case["id"]: case for case in VECTORS["cases"]}
SOURCE_FIELDS = {"origin", "feature", "placement_id", "boundary_id", "loop_index",
                 "edge_index", "operation_path", "role", "normal_sign"}


def axiom_digest():
    """條文雜湊的獨立算法:行尾正規化後再 sha256(GEO-153)。

    這裡刻意不 import 執行器的 _axiom_hash——測試要能獨立證明那個值是對的。
    """
    raw = (ROOT / "公理層.md").read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def volume6(obj, indices=None):
    """Signed tetrahedral volume, evaluated with unbounded exact integers."""
    vertices = obj["vertices_mm"]
    triangles = obj["triangles"]
    selected = range(len(triangles)) if indices is None else indices
    return sum(dot(vertices[a], cross(vertices[b], vertices[c]))
               for a, b, c in (triangles[i] for i in selected))


def bounds(objects):
    vertices = [v for obj in objects for v in obj["vertices_mm"]]
    return [[min(v[i] for v in vertices) for i in range(3)],
            [max(v[i] for v in vertices) for i in range(3)]]


def edge_uses(obj, indices=None):
    uses = defaultdict(list)
    triangles = obj["triangles"]
    selected = range(len(triangles)) if indices is None else indices
    for tid in selected:
        tri = triangles[tid]
        for a, b in zip(tri, tri[1:] + tri[:1]):
            uses[tuple(sorted((a, b)))].append((tid, a, b))
    return uses


def components(adjacency):
    remaining = set(adjacency)
    result = []
    while remaining:
        pending = [min(remaining)]
        found = set()
        while pending:
            node = pending.pop()
            if node in found:
                continue
            found.add(node)
            pending.extend(adjacency[node] - found)
        remaining.difference_update(found)
        result.append(found)
    return result


def contains(obj, point):
    """Exact +X ray winding test; same-plane triangle hits count once.

    Test probes are deliberately away from physical boundary edges.  Rectangle
    diagonals are allowed, and their two triangles must describe one crossing.
    """
    hits = {}
    vertices = obj["vertices_mm"]
    for triangle in obj["triangles"]:
        a, b, c = (vertices[i] for i in triangle)
        normal = cross(sub(b, a), sub(c, a))
        if not normal[0] or a[0] <= point[0]:
            continue
        yz = [(v[1], v[2]) for v in (a, b, c)]
        p = point[1:]
        sides = [(v[0] - u[0]) * (p[1] - u[1]) -
                 (v[1] - u[1]) * (p[0] - u[0])
                 for u, v in zip(yz, yz[1:] + yz[:1])]
        if min(sides) >= 0 or max(sides) <= 0:
            sign = 1 if normal[0] > 0 else -1
            if a[0] in hits and hits[a[0]] != sign:
                raise AssertionError("overlapping opposite faces in exported mesh")
            hits[a[0]] = sign
    return sum(hits.values()) == 1


class ModelingAcceptance(unittest.TestCase):
    maxDiff = 2500

    def build(self, case_id, **kwargs):
        case = deepcopy(CASES[case_id])
        if "executor_capabilities" in case:
            kwargs.setdefault("capabilities", case["executor_capabilities"])
        return build_package(case["definitions"], case["request"], **kwargs)

    def test_subgrid_definitions_remain_valid_model_base_sources(self):
        """D19 definitions round-trip without changing the extrusion geometry."""
        case = deepcopy(CASES["wall_through_hole"])
        original = build_package(case["definitions"], case["request"])
        case["definitions"]["base_scene"] += (
            "grid 7 on 1 main-along v u 1000 3000 v 500 2300\n"
            "subgrid 8 parent 7 cell u line:0 line:1 v line:0 line:1 divisions u 2 v 2\n"
        )
        package = build_package(case["definitions"], case["request"])
        self.assertEqual(package["derived"], original["derived"])
        self.assertIn("subgrid 8 parent 7", package["definitions"]["base_scene"])
        verify_package(package)
        case["definitions"]["base_scene"] = case["definitions"]["base_scene"].replace(
            "divisions u 2 v 2", "divisions u 3 v 2")
        with self.assertRaises(ModelError):
            build_package(case["definitions"], case["request"])

    def assert_mesh(self, obj):
        self.assertEqual(obj["representation"], "mesh")
        vertices, triangles = obj["vertices_mm"], obj["triangles"]
        self.assertEqual(vertices, sorted(vertices))
        self.assertEqual(len(vertices), len(set(map(tuple, vertices))))
        for vertex in vertices:
            self.assertEqual(len(vertex), 3)
            self.assertTrue(all(type(value) is int for value in vertex))
        self.assertEqual(len(triangles), len(obj["face_sources"]))
        self.assertEqual(len(triangles), len(set(map(tuple, triangles))))
        used = set()
        for triangle, sources in zip(triangles, obj["face_sources"]):
            self.assertEqual(len(triangle), 3)
            self.assertEqual(len(set(triangle)), 3)
            self.assertTrue(all(type(i) is int and 0 <= i < len(vertices)
                                for i in triangle))
            used.update(triangle)
            a, b, c = (vertices[i] for i in triangle)
            normal = cross(sub(b, a), sub(c, a))
            self.assertEqual(sum(x != 0 for x in normal), 1)
            self.assertTrue(sources, "every triangle needs original feature provenance")
            self.assertEqual(len(sources), len({canonical(s) for s in sources}))
            for source in sources:
                self.assertEqual(set(source), SOURCE_FIELDS)
                self.assertIn(source["origin"]["kind"],
                              ("placement", "column", "beam", "timber", "extrusion"))
                self.assertEqual(set(source["origin"]), {"kind", "id"})
                self.assertIn(source["normal_sign"], (-1, 1))
                self.assertIn(source["role"], ("boundary", "cut"))
                self.assertTrue(all(type(p) is str for p in source["operation_path"]))
                self.assertEqual(source["role"] == "cut",
                                 "tools" in source["operation_path"])
        self.assertEqual(used, set(range(len(vertices))))
        if obj["status"] == "EMPTY":
            for key in ("vertices_mm", "triangles", "face_sources", "boundary_shells"):
                self.assertEqual(obj[key], [])
            self.assertEqual(obj["closure"], "empty")
            self.assertIsNone(obj["component"])
            self.assertEqual(obj["volume_mm3"], "0")
            return

        self.assertTrue(triangles)
        uses = edge_uses(obj)
        self.assertTrue(all(1 <= len(value) <= 2 for value in uses.values()))
        boundary_count = 0
        face_adjacency = {i: set() for i in range(len(triangles))}
        for values in uses.values():
            if len(values) == 1:
                boundary_count += 1
            else:
                first, second = values
                self.assertEqual(first[1:], second[1:][::-1],
                                 "a shared edge must have opposite orientations")
                face_adjacency[first[0]].add(second[0])
                face_adjacency[second[0]].add(first[0])
        self.assertEqual(obj["closure"] == "closed", boundary_count == 0)

        # A vertex link must be exactly one cycle or boundary path, not two
        # disconnected fans hidden by a superficially correct edge count.
        for vertex in range(len(vertices)):
            link = defaultdict(set)
            for triangle in triangles:
                if vertex in triangle:
                    a, b = [i for i in triangle if i != vertex]
                    link[a].add(b)
                    link[b].add(a)
            self.assertEqual(len(components(link)), 1)
            degrees = sorted(len(neighbors) for neighbors in link.values())
            self.assertTrue(all(degree in (1, 2) for degree in degrees))
            self.assertIn(degrees.count(1), (0, 2))
            if obj["closure"] == "closed":
                self.assertEqual(degrees.count(1), 0)

        shells = obj["boundary_shells"]
        self.assertEqual(sorted(i for shell in shells for i in shell["triangles"]),
                         list(range(len(triangles))))
        actual_groups = {frozenset(group) for group in components(face_adjacency)}
        self.assertEqual({frozenset(shell["triangles"]) for shell in shells}, actual_groups)
        for shell in shells:
            self.assertIn(shell["role"], ("outer", "cavity", "open"))
            if obj["volume_mm3"] is not None:
                signed = volume6(obj, shell["triangles"])
                if shell["role"] == "outer":
                    self.assertGreater(signed, 0)
                elif shell["role"] == "cavity":
                    self.assertLess(signed, 0)
        if obj["volume_mm3"] is not None:
            self.assertRegex(obj["volume_mm3"], r"^(0|[1-9][0-9]*)$")
            self.assertGreater(int(obj["volume_mm3"]), 0)
            self.assertEqual(volume6(obj), 6 * int(obj["volume_mm3"]))

    def assert_package(self, package):
        self.assertEqual(set(package) - {"presentation"},
                         {"manifest", "definitions", "request", "derived", "diagnostics"})
        manifest = package["manifest"]
        self.assertEqual(manifest["schema"], "geometry-model-package/1")
        self.assertEqual(manifest["profile"], "orthogonal-model/1")
        self.assertEqual(manifest["units"], "mm")
        self.assertEqual(manifest["coordinate_system"], {"handedness": "right", "up": "+Z"})
        self.assertRegex(manifest["axiom_revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(manifest["axiom_sha256"], axiom_digest())
        self.assertEqual(manifest["source_sha256"], digest(package["definitions"]))
        self.assertEqual(manifest["geometry_sha256"], digest(package["derived"]))
        roots = package["request"]["roots"]
        for obj in package["derived"]["objects"]:
            self.assertIn(obj["root"], roots)
            self.assertEqual(obj["role"], package["request"]["role"])
            self.assert_mesh(obj)
        rebuilt = verify_package(deepcopy(package))
        self.assertEqual(rebuilt["derived"], package["derived"])
        self.assertEqual(rebuilt["definitions"], package["definitions"])
        self.assertEqual(rebuilt["manifest"]["geometry_sha256"], manifest["geometry_sha256"])

    def check_vector(self, case):
        expected = case["expected"]
        original = deepcopy(case)
        if expected["status"] in ("INVALID", "UNSUPPORTED", "INCOMPLETE"):
            kwargs = ({"capabilities": case["executor_capabilities"]}
                      if "executor_capabilities" in case else {})
            with self.assertRaises(ModelError) as caught:
                build_package(case["definitions"], case["request"], **kwargs)
            self.assertEqual(caught.exception.status, expected["status"])
            self.assertEqual(caught.exception.code, expected["code"])
            self.assertEqual(caught.exception.clause, expected["clause"])
            self.assertEqual(case, original, "rejected input must not be mutated")
            return
        package = self.build(case["id"])
        self.assert_package(package)
        self.assertEqual(package["derived"]["status"], expected["status"])
        objects = package["derived"]["objects"]
        if "bounds_mm" in expected:
            self.assertEqual(bounds(objects), expected["bounds_mm"])
        if "closure" in expected:
            self.assertEqual({obj["closure"] for obj in objects}, {expected["closure"]})
        if "volume_mm3" in expected:
            if expected["volume_mm3"] is None:
                self.assertTrue(all(obj["volume_mm3"] is None for obj in objects))
            else:
                self.assertEqual(sum(int(obj["volume_mm3"]) for obj in objects),
                                 int(expected["volume_mm3"]))
        if "object_count" in expected:
            self.assertEqual(len(objects), expected["object_count"])
        if "per_object_volume_mm3" in expected:
            self.assertEqual([obj["volume_mm3"] for obj in objects],
                             expected["per_object_volume_mm3"])
        if "volume_components" in expected:
            solids = [obj for obj in objects if obj["status"] != "EMPTY"]
            self.assertEqual(len(solids), expected["volume_components"])
            self.assertEqual([obj["component"] for obj in solids], list(range(len(solids))))
        if "boundary_shell_roles" in expected:
            self.assertCountEqual([s["role"] for obj in objects for s in obj["boundary_shells"]],
                                  expected["boundary_shell_roles"])
        if expected.get("root_retained"):
            self.assertEqual(len(objects), 1)
            self.assertEqual(objects[0]["root"], case["request"]["roots"][0])
            self.assertIn("EMPTY_RESULT", [d["code"] for d in package["diagnostics"]])
        if "excluded_point_mm" in expected:
            self.assertFalse(any(contains(obj, expected["excluded_point_mm"]) for obj in objects))
        if "shell_members" in expected:
            sources = [s for obj in objects for face in obj["face_sources"] for s in face]
            self.assertEqual(len({s["placement_id"] for s in sources}), expected["shell_members"])

        case_id = case["id"]
        if case_id.startswith("wall_"):
            y = -60 if case_id == "wall_through_hole" else 60
            self.assertFalse(contains(objects[0], (1500, y, 1300)))
            self.assertTrue(contains(objects[0], (500, y, 1300)))
            self.assertTrue(contains(objects[0], (1500, y, 400)))
            # A single through hole has Euler characteristic zero (one handle).
            self.assertEqual(len(objects[0]["vertices_mm"]) - len(edge_uses(objects[0])) +
                             len(objects[0]["triangles"]), 0)
            hole_sources = [s for face in objects[0]["face_sources"] for s in face
                            if s["feature"] == "hole_side"]
            self.assertEqual({s["loop_index"] for s in hole_sources}, {1})
            self.assertEqual({s["edge_index"] for s in hole_sources}, {0, 1, 2, 3})
        if case_id == "l_room_eight_faces":
            self.assertTrue(contains(objects[0], (2000, 4000, 1300)))
            self.assertTrue(contains(objects[0], (5000, 2000, 1300)))
        if case_id == "keep_overlap_preserves_objects":
            self.assertEqual([obj["member_path"] for obj in objects], [[0], [1]])
            self.assertEqual([bounds([obj]) for obj in objects],
                             [[[0, 0, 0], [2000, 2000, 2000]],
                              [[1000, 0, 0], [3000, 2000, 2000]]])
            for obj, plane in zip(objects, (2000, 1000)):
                self.assertTrue(any(all(obj["vertices_mm"][i][0] == plane for i in tri)
                                    for tri in obj["triangles"]))
        if case_id == "union_overlap":
            self.assertFalse(any(all(obj["vertices_mm"][i][0] == plane for i in tri)
                                 for obj in objects for tri in obj["triangles"]
                                 for plane in (1000, 2000)))
            self.assertTrue(contains(objects[0], (1500, 700, 1300)))
        if case_id == "difference_internal_cavity":
            self.assertFalse(contains(objects[0], (1000, 900, 1100)))
            self.assertTrue(contains(objects[0], (100, 900, 1100)))
            for shell in objects[0]["boundary_shells"]:
                if shell["role"] == "cavity":
                    sources = [s for i in shell["triangles"]
                               for s in objects[0]["face_sources"][i]]
                    self.assertEqual({s["origin"]["id"] for s in sources}, {2})
                    self.assertEqual({s["role"] for s in sources}, {"cut"})
                    self.assertEqual({s["normal_sign"] for s in sources}, {-1})
        if case_id == "difference_two_pieces":
            self.assertEqual([bounds([obj]) for obj in objects],
                             [[[0, 0, 0], [900, 2000, 2000]],
                              [[1100, 0, 0], [2000, 2000, 2000]]])
        if case_id == "edge_contact_does_not_weld":
            self.assertEqual(len(objects), 2)
            self.assertTrue(set(map(tuple, objects[0]["vertices_mm"])) &
                            set(map(tuple, objects[1]["vertices_mm"])))
            # Separate object-local index domains are required even when XYZ
            # happens to match; the closed-manifold checks above reject welding.
            self.assertIsNot(objects[0]["vertices_mm"], objects[1]["vertices_mm"])

    def test_partial_is_root_atomic(self):
        case = deepcopy(CASES["l_room_eight_faces"])
        shell = deepcopy(case["definitions"]["extensions"][0])
        shell["id"] = 71
        shell["uses"] = [use for use in shell["uses"] if use["placement_id"] != 2]
        case["definitions"]["extensions"].extend([
            shell, {"kind": "composite_space", "id": 81, "shell_id": 71, "obstacles": []}])
        case["request"]["roots"].append({"kind": "composite_space", "id": 81})
        with self.assertRaises(ModelError) as caught:
            build_package(case["definitions"], case["request"])
        self.assertEqual(caught.exception.status, "INCOMPLETE")
        case["request"]["allow_partial"] = True
        package = build_package(case["definitions"], case["request"])
        self.assert_package(package)
        self.assertEqual(package["derived"]["status"], "INCOMPLETE")
        self.assertEqual({o["root"]["id"] for o in package["derived"]["objects"]}, {80})
        missing = [d for d in package["diagnostics"] if d["root"] ==
                   {"kind": "composite_space", "id": 81}]
        self.assertTrue(missing)
        self.assertTrue(all(d["code"] == "OPEN_SHELL" for d in missing))

    def test_invalid_has_priority_over_missing_capability(self):
        with self.assertRaises(ModelError) as caught:
            self.build("zero_thickness_rejected", capabilities=[])
        self.assertEqual(caught.exception.status, "INVALID")

    def test_cell_limit_is_unsupported_not_invalid_or_partial(self):
        case = deepcopy(CASES["wall_through_hole"])
        case["request"]["allow_partial"] = True
        with self.assertRaises(ModelError) as caught:
            build_package(case["definitions"], case["request"], max_cells=1)
        self.assertEqual(caught.exception.status, "UNSUPPORTED")

    def test_dependency_depth_and_expanded_keep_capacity_are_explicit(self):
        scene = "beam 1 along x from 0 to 10 at 5 width 10 depth 10 top 10\n"
        deep = []
        previous = {"kind": "beam", "id": 1}
        for i in range(1, 66):
            deep.append({"kind": "composition", "id": i, "op": "KEEP", "inputs": [previous]})
            previous = {"kind": "composition", "id": i}
        branching = [
            {"kind": "composition", "id": 1, "op": "KEEP", "inputs": [{"kind": "beam", "id": 1}]},
            {"kind": "composition", "id": 2, "op": "KEEP", "inputs": [{"kind": "beam", "id": 1}]},
        ]
        for i in range(3, 27):
            branching.append({"kind": "composition", "id": i, "op": "KEEP", "inputs": [
                {"kind": "composition", "id": i - 1}, {"kind": "composition", "id": i - 2}]})
        for label, extensions in (("dependency depth", deep), ("expanded KEEP leaves", branching)):
            with self.subTest(label=label):
                definitions = {"base_scene": scene, "extensions": extensions}
                request = {"roots": [{"kind": "composition", "id": extensions[-1]["id"]}],
                           "role": "geometry", "target": "solid-set", "allow_partial": True}
                with self.assertRaises(ModelError) as caught:
                    build_package(definitions, request)
                self.assertEqual(caught.exception.status, "UNSUPPORTED")
                self.assertEqual(caught.exception.code, "CAPACITY")
                self.assertEqual(caught.exception.clause, "I33")

    def test_strict_inputs_reject_unknown_null_bool_and_float(self):
        mutations = [
            ("unknown definition", lambda d, r: d.update(typo=1)),
            ("unknown extension", lambda d, r: d["extensions"][0].update(thickness=120)),
            ("null spec", lambda d, r: d["extensions"][0].update(hi_spec=None)),
            ("boolean id", lambda d, r: d["extensions"][0].update(id=True)),
            ("fractional id", lambda d, r: d["extensions"][0].update(id=50.0)),
            ("unknown request", lambda d, r: r.update(typo=False)),
            ("integer partial", lambda d, r: r.update(allow_partial=1)),
            ("null roots", lambda d, r: r.update(roots=None)),
            ("unknown reference", lambda d, r: r["roots"][0].update(typo=1)),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                case = deepcopy(CASES["wall_through_hole"])
                mutate(case["definitions"], case["request"])
                with self.assertRaises(ModelError) as caught:
                    build_package(case["definitions"], case["request"])
                self.assertEqual(caught.exception.status, "INVALID")

    def test_shell_purpose_is_required_and_calculation_cap_is_explicit(self):
        case = deepcopy(CASES["l_room_eight_faces"])
        case["definitions"]["extensions"][0]["uses"][1]["purpose"] = "calculation-cap"
        package = build_package(case["definitions"], case["request"])
        self.assertEqual(sum(int(o["volume_mm3"]) for o in package["derived"]["objects"]),
                         68040000000)
        del case["definitions"]["extensions"][0]["uses"][1]["purpose"]
        with self.assertRaises(ModelError) as caught:
            build_package(case["definitions"], case["request"])
        self.assertEqual(caught.exception.status, "INVALID")

    def test_closed_inward_shell_is_not_a_composite_space(self):
        case = deepcopy(CASES["l_room_eight_faces"])
        for use in case["definitions"]["extensions"][0]["uses"]:
            use["orientation"] *= -1
        with self.assertRaises(ModelError) as caught:
            build_package(case["definitions"], case["request"])
        self.assertEqual(caught.exception.status, "INVALID")
        self.assertEqual(caught.exception.clause, "I28")

    def test_nonmanifold_three_face_edge_and_point_pinch_are_rejected(self):
        scenes = [
            ("three faces on one edge",
             "placement 1 origin 0 0 0 u +x v +y rect 0 0 10 10\n"
             "placement 2 origin 0 0 0 u +x v +z rect 0 0 10 10\n"
             "placement 3 origin 0 -10 0 u +x v +y rect 0 0 10 10\n", [1, -1, 1]),
            ("two surface patches touch only at one vertex",
             "placement 1 origin 0 0 0 u +x v +y rect 0 0 10 10\n"
             "placement 2 origin 10 10 0 u +x v +y rect 0 0 10 10\n", [1, 1]),
        ]
        for label, scene, orientations in scenes:
            with self.subTest(label=label):
                definitions = {"base_scene": scene, "extensions": [{
                    "kind": "shell", "id": 70, "uses": [
                        {"placement_id": i + 1, "orientation": sign, "purpose": "boundary"}
                        for i, sign in enumerate(orientations)]}]}
                request = {"roots": [{"kind": "shell", "id": 70}],
                           "role": "geometry", "target": "surface-set", "allow_partial": False}
                with self.assertRaises(ModelError) as caught:
                    build_package(definitions, request)
                self.assertEqual(caught.exception.status, "INVALID")
                self.assertEqual(caught.exception.clause, "I27")

    def test_clearance_clips_only_declared_obstacles(self):
        case = deepcopy(CASES["l_room_eight_faces"])
        # Beam 1 extends outside the shell; beam 2 exists but is not an obstacle.
        case["definitions"]["base_scene"] += (
            "beam 1 along x from -100 to 1000 at 500 width 1000 depth 3000 top 3000\n"
            "beam 2 along x from 2000 to 3000 at 2500 width 1000 depth 2000 top 2000\n")
        case["definitions"]["extensions"][1]["obstacles"] = [{"kind": "beam", "id": 1}]
        case["request"]["role"] = "clearance"
        package = build_package(case["definitions"], case["request"])
        self.assert_package(package)
        objects = package["derived"]["objects"]
        self.assertEqual(sum(int(o["volume_mm3"]) for o in objects), 68040000000 - 2800000000)
        self.assertEqual(bounds(objects), [[0, 0, 0], [6000, 4500, 2800]])
        self.assertFalse(any(contains(o, (500, 500, 1400)) for o in objects))
        self.assertTrue(any(contains(o, (2500, 2500, 1400)) for o in objects))
        origins = {s["origin"]["id"] for o in objects for face in o["face_sources"]
                   for s in face if s["origin"]["kind"] == "beam"}
        self.assertEqual(origins, {1})

    def test_extension_forward_reference_is_not_silently_sorted_into_legality(self):
        case = deepcopy(CASES["empty_reused_in_union"])
        case["definitions"]["extensions"].reverse()
        with self.assertRaises(ModelError) as caught:
            build_package(case["definitions"], case["request"])
        self.assertEqual(caught.exception.status, "INVALID")
        self.assertEqual(caught.exception.code, "FORWARD_REFERENCE")
        self.assertEqual(caught.exception.clause, "I9")

    def test_hashes_are_reproducible_and_ignore_presentation(self):
        package = self.build("wall_through_hole")
        again = self.build("wall_through_hole")
        self.assertEqual(package["derived"], again["derived"])
        self.assertEqual(package["manifest"], again["manifest"])
        package["presentation"] = {"camera": [5, 8, 13], "canvas": {"x": -55, "y": 89}}
        rebuilt = verify_package(package)
        self.assertEqual(rebuilt["derived"], again["derived"])
        self.assertEqual(rebuilt["manifest"]["geometry_sha256"],
                         again["manifest"]["geometry_sha256"])
        self.assertEqual(rebuilt["manifest"]["source_sha256"],
                         again["manifest"]["source_sha256"])

    def test_import_rebuild_rejects_rehashed_false_geometry(self):
        package = self.build("wall_through_hole")
        package["derived"]["objects"][0]["volume_mm3"] = "1"
        package["manifest"]["geometry_sha256"] = digest(package["derived"])
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.status, "INVALID")

    def test_import_rejects_version_axes_and_hash_tampering(self):
        mutations = [
            ("schema", "geometry-model-package/999"),
            ("profile", "orthogonal-model/999"),
            ("units", "cm"),
            ("coordinate_system", {"handedness": "left", "up": "+Y"}),
            ("source_sha256", "0" * 64),
            ("geometry_sha256", "0" * 64),
            ("axiom_sha256", "0" * 64),
        ]
        original = self.build("wall_through_hole")
        for field, value in mutations:
            with self.subTest(field=field):
                package = deepcopy(original)
                package["manifest"][field] = value
                with self.assertRaises(ModelError):
                    verify_package(package)

    def test_external_generator_diagnostics_and_partial_root_evidence(self):
        case = deepcopy(CASES["l_room_eight_faces"])
        shell = deepcopy(case["definitions"]["extensions"][0])
        shell["id"] = 71
        shell["uses"] = [use for use in shell["uses"] if use["placement_id"] != 2]
        case["definitions"]["extensions"].extend([
            shell, {"kind": "composite_space", "id": 81, "shell_id": 71, "obstacles": []}])
        case["request"]["roots"].append({"kind": "composite_space", "id": 81})
        case["request"]["allow_partial"] = True
        partial = build_package(case["definitions"], case["request"])
        for original in (self.build("difference_empty"), partial):
            with self.subTest(status=original["derived"]["status"]):
                external = deepcopy(original)
                external["manifest"]["generator"] = {"name": "independent-example", "version": "7.2"}
                for diagnostic in external["diagnostics"]:
                    diagnostic["message"] = "由其他符合規格的產生器提供：" + diagnostic["message"]
                    if diagnostic["code"] != "EMPTY_RESULT":
                        diagnostic["code"] = "EXTERNAL_OPEN_BOUNDARY"
                rebuilt = verify_package(external)
                self.assertEqual(rebuilt["definitions"], original["definitions"])
                self.assertEqual(rebuilt["derived"], original["derived"])
                self.assertEqual(rebuilt["manifest"]["generator"], original["manifest"]["generator"])
                self.assertEqual(rebuilt["diagnostics"], original["diagnostics"])
        with self.subTest(status="missing omitted-root evidence"):
            partial["diagnostics"] = [item for item in partial["diagnostics"]
                                      if item["root"] != {"kind": "composite_space", "id": 81}]
            with self.assertRaises(ModelError) as caught:
                verify_package(partial)
            self.assertEqual(caught.exception.status, "INVALID")

    def test_identical_reopened_preview_cannot_reuse_an_old_token(self):
        for cancel_first in (True, False):
            with self.subTest(cancel_first=cancel_first):
                case = deepcopy(CASES["wall_through_hole"])
                world = ModelWorld(case["definitions"], case["request"])
                before = deepcopy(world.package)
                candidate = deepcopy(case["definitions"])
                candidate["base_scene"] = candidate["base_scene"].replace("spec far 120", "spec far 240")
                first = world.preview(candidate)
                if cancel_first:
                    world.cancel(first["token"])
                second = world.preview(deepcopy(candidate))
                self.assertNotEqual(first["token"], second["token"])
                with self.assertRaises(ModelError) as caught:
                    world.confirm(first["token"])
                self.assertEqual(caught.exception.code, "STALE_PREVIEW")
                self.assertEqual(world.package, before)
                world.confirm(second["token"])
                self.assertEqual(world.package["derived"]["objects"][0]["volume_mm3"], "2342400000")

    def test_transaction_preview_confirm_and_live_spec_recompute(self):
        case = deepcopy(CASES["wall_through_hole"])
        world = ModelWorld(case["definitions"], case["request"])
        before = deepcopy(world.package)
        candidate = deepcopy(case["definitions"])
        candidate["base_scene"] = candidate["base_scene"].replace("spec far 120", "spec far 240")
        preview = world.preview(candidate)
        self.assertEqual(world.package, before, "preview cannot mutate committed world")
        self.assertEqual(preview["package"]["derived"]["objects"][0]["volume_mm3"], "2342400000")
        world.confirm(preview["token"])
        after = world.package
        self.assertEqual(after["derived"]["objects"][0]["volume_mm3"], "2342400000")
        self.assertEqual(bounds(after["derived"]["objects"]), [[0, -240, 0], [4000, 0, 2800]])
        self.assertNotEqual(after["manifest"]["source_sha256"], before["manifest"]["source_sha256"])
        self.assertNotEqual(after["manifest"]["geometry_sha256"], before["manifest"]["geometry_sha256"])
        self.assert_package(after)
        # An exported value is a copy, not a backdoor around the transaction gate.
        after["definitions"]["extensions"].clear()
        self.assertTrue(world.definitions["extensions"])

    def test_failed_edit_and_referenced_source_deletion_roll_back(self):
        case = deepcopy(CASES["wall_through_hole"])
        world = ModelWorld(case["definitions"], case["request"])
        before = deepcopy(world.package)
        bad_scenes = [
            case["definitions"]["base_scene"].replace("spec far 120", "spec far 0"),
            "\n".join(line for line in case["definitions"]["base_scene"].splitlines()
                      if not line.startswith("placement 1 ")) + "\n",
            "\n".join(line for line in case["definitions"]["base_scene"].splitlines()
                      if not line.startswith("spec far ")) + "\n",
        ]
        for scene in bad_scenes:
            with self.subTest(scene=scene):
                candidate = deepcopy(case["definitions"])
                candidate["base_scene"] = scene
                with self.assertRaises(ModelError):
                    world.preview(candidate)
                self.assertEqual(world.package, before)

    def test_frame_change_recomputes_world_coordinates_and_cancel_is_atomic(self):
        case = deepcopy(CASES["wall_through_hole"])
        world = ModelWorld(case["definitions"], case["request"])
        before = deepcopy(world.package)
        candidate = deepcopy(case["definitions"])
        candidate["base_scene"] = candidate["base_scene"].replace("origin 0 0 0", "origin 100 200 300")
        preview = world.preview(candidate)
        self.assertEqual(bounds(preview["package"]["derived"]["objects"]),
                         [[100, 80, 300], [4100, 200, 3100]])
        self.assertEqual(preview["package"]["derived"]["objects"][0]["volume_mm3"], "1171200000")
        world.cancel(preview["token"])
        self.assertEqual(world.package, before)
        with self.assertRaises(ModelError) as caught:
            world.confirm(preview["token"])
        self.assertEqual(caught.exception.code, "STALE_PREVIEW")


def vector_test(case):
    def test(self):
        self.check_vector(case)
    test.__doc__ = "Normative vector: " + case["id"]
    return test


for _case in VECTORS["cases"]:
    setattr(ModelingAcceptance, "test_vector_" + _case["id"], vector_test(_case))


class AxiomSourceIdentity(unittest.TestCase):
    """GEO-153:條文的身分不該隨簽出平台改變。

    這一組刻意不經過 build_package——沒有 gcc 系編譯器的機器會先撞
    BASE_COMPILER,公理閘門輪不到,缺陷就測不出來。
    """

    def test_hash_matches_the_declared_constant(self):
        """工作區是 CRLF(Windows)或 LF(Linux)都必須通過。

        修好之前:Windows 上這裡會丟 UNSUPPORTED/AXIOM_VERSION,
        連帶讓所有建模功能失效。
        """
        self.assertEqual(modeling._axiom_hash(), modeling.AXIOM_SHA256)
        self.assertEqual(axiom_digest(), modeling.AXIOM_SHA256)

    def test_hash_ignores_line_endings(self):
        lf = (ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        self.assertNotEqual(lf, crlf)          # 條文有換行,兩種簽出確實不同 bytes
        for label, data in (("LF", lf), ("CRLF", crlf)):
            with self.subTest(eol=label), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "公理層.md"
                path.write_bytes(data)
                with mock.patch.object(modeling, "_AXIOM_PATH", path):
                    self.assertEqual(modeling._axiom_hash(), modeling.AXIOM_SHA256)

    def test_real_content_change_is_still_rejected(self):
        """正規化不得把閘門關掉:改一個字仍然要擋。"""
        body = (ROOT / "公理層.md").read_bytes() + "\n新增一行不屬於條文的字。\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "公理層.md"
            path.write_bytes(body)
            with mock.patch.object(modeling, "_AXIOM_PATH", path):
                with self.assertRaises(ModelError) as caught:
                    modeling._axiom_hash()
        diagnostic = caught.exception.as_dict()["diagnostics"][0]
        self.assertEqual((diagnostic["code"], diagnostic["clause"]), ("AXIOM_VERSION", "I32"))


class WslBaseAdapterTests(unittest.TestCase):
    def test_startup_preserves_explicit_base_or_native_update_compiler_fallback(self):
        from modeling.base import startup_base_transport
        cases = [({}, "wsl"),
                 ({"GEOMETRY_MODEL_BASE": "native adapter.exe"}, "configured"),
                 ({"GEOMETRY_MODEL_BASE": "/opt/geometry/model-base", "GEOMETRY_MODEL_BASE_WSL_DISTRO": "Ubuntu-24.04"}, "configured"),
                 ({"GEOMETRY_MODEL_UPDATE_BRIDGE": "native update bridge.exe"}, "native"),
                 ({"GEOMETRY_MODEL_BASE": "native adapter.exe", "GEOMETRY_MODEL_UPDATE_BRIDGE": "native update bridge.exe"}, "configured")]
        for environment, expected in cases:
            with self.subTest(environment=environment), mock.patch.dict("os.environ", environment, clear=True):
                self.assertEqual(startup_base_transport(), expected)

    def test_update_bridge_only_uses_native_compiler_result_as_literal_argv(self):
        from modeling.base import load_base, startup_base_transport
        snapshot = {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": "", "specs": [], "placements": [], "solids": [], "unplaced_timbers": [], "dependencies": []}
        result = mock.Mock(returncode=0, stdout=json.dumps(snapshot).encode())
        with mock.patch("modeling.base.sys.platform", "win32"), mock.patch.dict("os.environ", {"GEOMETRY_MODEL_UPDATE_BRIDGE": "native update bridge.exe"}, clear=True), mock.patch("modeling.base._build_adapter", return_value="compiled native adapter.exe") as build, mock.patch("modeling.base.subprocess.run", return_value=result) as run:
            self.assertEqual(startup_base_transport(), "native")
            self.assertEqual(load_base(""), snapshot)
        build.assert_called_once_with()
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], "compiled native adapter.exe")
        self.assertEqual(len(run.call_args.args[0]), 2)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_wsl_scene_path_is_translated_and_passed_as_one_literal_argument(self):
        from modeling.base import _adapter_command
        converted = mock.Mock(returncode=0, stdout=b"/mnt/c/scene folder/input.scene\n")
        with mock.patch("modeling.base.subprocess.run", return_value=converted) as run:
            command = _adapter_command("/opt/geometry/model-base", r"C:\scene folder\input.scene", wsl_distro="Ubuntu-24.04")
        self.assertEqual(command, ["wsl.exe", "-d", "Ubuntu-24.04", "--user", "root", "--exec", "/opt/geometry/model-base", "/mnt/c/scene folder/input.scene"])
        self.assertEqual(run.call_args.args[0][-1], "C:/scene folder/input.scene")
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_failed_or_malformed_wsl_path_conversion_is_rejected(self):
        from modeling.base import _adapter_command
        for code, output in [(1, b"/mnt/c/input.scene"), (0, b"relative.scene"), (0, b"/mnt/c/input.scene\nextra"), (0, b"\xff")]:
            with self.subTest(code=code, output=output), mock.patch("modeling.base.subprocess.run", return_value=mock.Mock(returncode=code, stdout=output)):
                with self.assertRaises(ModelError) as caught:
                    _adapter_command("/opt/geometry/model-base", "input.scene", wsl_distro="Ubuntu-24.04")
                self.assertEqual(caught.exception.code, "BASE_EXECUTABLE")

    def test_native_executable_override_ignores_wsl_environment(self):
        from modeling.base import load_base
        snapshot = {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": "", "specs": [], "placements": [], "solids": [], "unplaced_timbers": [], "dependencies": []}
        result = mock.Mock(returncode=0, stdout=json.dumps(snapshot).encode())
        with mock.patch("modeling.base.sys.platform", "win32"), mock.patch.dict("os.environ", {"GEOMETRY_MODEL_BASE_WSL_DISTRO": "Ubuntu-24.04"}), mock.patch("modeling.base.subprocess.run", return_value=result) as run:
            self.assertEqual(load_base("", executable="native adapter.exe"), snapshot)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], "native adapter.exe")

    def test_windows_environment_runs_the_configured_wsl_adapter(self):
        from modeling.base import load_base
        snapshot = {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": "", "specs": [], "placements": [], "solids": [], "unplaced_timbers": [], "dependencies": []}
        converted = mock.Mock(returncode=0, stdout=b"/mnt/c/temp/input.scene\n")
        result = mock.Mock(returncode=0, stdout=json.dumps(snapshot).encode())
        with mock.patch("modeling.base.sys.platform", "win32"), mock.patch.dict("os.environ", {"GEOMETRY_MODEL_BASE": "/opt/geometry/model-base", "GEOMETRY_MODEL_BASE_WSL_DISTRO": "Ubuntu-24.04"}), mock.patch("modeling.base.subprocess.run", side_effect=[converted, result]) as run:
            self.assertEqual(load_base(""), snapshot)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0][-2:], ["/opt/geometry/model-base", "/mnt/c/temp/input.scene"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
