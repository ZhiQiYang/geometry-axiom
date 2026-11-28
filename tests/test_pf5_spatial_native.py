"""PF5 V: real native spatial output against the preserved independent oracle.

Fixtures choose every physical dimension, face, obstacle and material version.
The protocol adapter below only reads native loops, splits those submitted
loops into exact critical cells, and changes decimal strings to Python ints.
It does not call the constructor's parser, clipping or normalization helpers.
The preserved checker separately tests those cells against raw world cuboids.
"""
import copy
import itertools
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests._bridge import BridgeSession, find_bridge
from tests import pf5_geometry_oracle as ORACLE
from tests import pf5_geometry_check as CHECKER


def face(identity=1, origin=(0, 0, 2480), u=(1, 0, 0), v=(0, 1, 0),
         n=(0, 0, 1), side=1, outer=None, holes=None, obstacles=None):
    return {"id": identity, "label": "V explicit face "+str(identity),
            "frame": {"origin": list(origin), "u": list(u), "v": list(v), "n": list(n)},
            "side": side,
            "region": {"outer": [[0, 0], [100, 0], [100, 100], [0, 100]] if outer is None else outer,
                       "holes": [] if holes is None else holes},
            "obstacles": ["b20"] if obstacles is None else obstacles,
            "thickness": 9, "section": [27, 30]}


def example():
    return {"schema": "pf5-geometry-input/1", "room": {"min": [0, 0, 0], "max": [100, 100, 3000]},
            "obstacles": [{"ref": "b20", "min": [40, 20, 2500], "max": [60, 80, 3000]}],
            "finishes": [face()]}


def step_faces():
    data = example()
    data["obstacles"][0].update(min=[40, 0, 2500], max=[60, 100, 3000])
    data["finishes"] = [
        face(origin=(0, 0, 2600), outer=[[0, 0], [31, 0], [31, 100], [0, 100]]),
        face(2, origin=(0, 0, 2461), outer=[[31, 0], [69, 0], [69, 100], [31, 100]]),
        face(3, origin=(31, 0, 2461), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0),
             outer=[[0, 0], [100, 0], [100, 139], [0, 139]]),
    ]
    return data


def axis_name(vector):
    position = next(i for i, value in enumerate(vector) if value)
    return ("+" if vector[position] == 1 else "-")+"XYZ"[position]


def signed_area2(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1]))


def inside(loop, x2, y2):
    # Independent winding-number predicate on half-integer critical cells.
    winding = 0
    for a, b in zip(loop, loop[1:]+loop[:1]):
        cross = (b[0]-a[0])*(y2-2*a[1])-(b[1]-a[1])*(x2-2*a[0])
        if 2*a[1] <= y2 < 2*b[1] and cross > 0:
            winding += 1
        if 2*b[1] <= y2 < 2*a[1] and cross < 0:
            winding -= 1
    return winding != 0


def canonical_ring(ring):
    # Source-key/fixity breaks may add collinear vertices. Preserve orientation
    # and actual geometry, removing only those representational breakpoints.
    ring = [tuple(point) for point in ring]
    reduced = [point for i, point in enumerate(ring)
               if not (ring[i-1][0] == point[0] == ring[(i+1) % len(ring)][0]
                       or ring[i-1][1] == point[1] == ring[(i+1) % len(ring)][1])]
    first = min(range(len(reduced)), key=lambda i: reduced[i])
    return tuple(reduced[first:]+reduced[:first])


def canonical_region(region):
    return sorted((canonical_ring(component["outer"]),
                   tuple(sorted(canonical_ring(hole) for hole in component["holes"])))
                  for component in region["components"])


class PF5SpatialNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-pf5-v-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bridge = BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.command("reset")

    def command(self, text):
        reply = self.bridge.command(text)
        self.assertTrue(reply.get("ok"), "PF5_NATIVE_COMMAND: "+text+" "+json.dumps(reply, ensure_ascii=False))
        return reply

    def read(self):
        return self.command("panel-fill-read")

    def transaction(self, operations, kind="panel-fill", confirm=True):
        path = self.directory/(kind+".json")
        path.write_text(json.dumps({"schema": kind+"-transaction/1", "expectedRevision": self.read()["revision"],
                                    "operations": operations}, ensure_ascii=False), encoding="utf-8")
        preview = self.command(kind+"-preview "+str(path))["preview"]
        self.assertTrue(preview["valid"], "PF5_EXPLICIT_FIXTURE_VALID: "+json.dumps(preview, ensure_ascii=False))
        if confirm:
            self.command(kind+"-confirm "+str(preview["token"]))
        return preview

    def seed(self, data, hosts=True, gap=0, panel_size=(10000, 10000)):
        self.command("reset")
        scene = []
        for f in data["finishes"]:
            region = f["region"]
            text = "boundary "+str(100+f["id"])+" outline "+" ".join(
                str(x)+","+str(y) for x, y in region["outer"])
            for hole in region["holes"]:
                text += " hole "+" ".join(str(x)+","+str(y) for x, y in hole)
            scene.append(text)
        for obstacle in data["obstacles"]:
            ref, lo, hi = obstacle["ref"], obstacle["min"], obstacle["max"]
            if ref.startswith("c"):
                scene.append(f"column {ref[1:]} at {lo[0]} {lo[1]} size {hi[0]-lo[0]} {hi[1]-lo[1]} z {lo[2]} {hi[2]}")
            else:
                self.assertEqual(0, (lo[1]+hi[1]) % 2, "PF5_FIXTURE_BEAM_CENTER_IS_EXPLICIT_INTEGER")
                scene.append(f"beam {ref[1:]} along x from {lo[0]} to {hi[0]} at {(lo[1]+hi[1])//2} "
                             f"width {hi[1]-lo[1]} depth {hi[2]-lo[2]} top {hi[2]}")
        path = self.directory/"explicit.scene"
        path.write_text("\n".join(scene)+"\n", encoding="utf-8")
        self.command("loadfile "+str(path))
        materials = [{"op": "publish-material", "value": {
            "id": "v-board-"+str(f["id"]), "version": 1, "name": "V explicit panel",
            "kind": "panel", "width": panel_size[0], "length": panel_size[1], "thickness": str(f["thickness"])}}
            for f in data["finishes"]]
        materials.append({"op": "put-parameter", "value": {"id": 90, "name": "V explicit threshold",
                          "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "8"}]}})
        self.transaction(materials, "engineering")
        operations = []
        for f in data["finishes"]:
            identity, frame = f["id"], f["frame"]
            operations.extend([
                {"op": "put-finish-surface", "value": {"id": identity, "name": f["label"],
                 "boundaryId": 100+identity, "frame": {"origin": frame["origin"],
                     "U": axis_name(frame["u"]), "V": axis_name(frame["v"]), "N": axis_name(frame["n"])},
                 "structureSide": f["side"], "obstacles": f["obstacles"]}},
                {"op": "put-panel-fill", "value": {"id": identity, "finishSurfaceId": identity,
                 "panel": {"id": "v-board-"+str(identity), "version": 1}, "lengthAlong": "v", "origin": [0, 0],
                 "gap": gap, "pattern": "straight", "threshold": {"parameterId": 90, "fieldId": 1}}},
            ])
            if hosts:
                operations.append({"op": "put-derived-placement", "value": {
                    "id": 1000+identity, "fillId": identity, "h": f["section"][1]}})
        return self.transaction(operations)

    def spatial(self, reply=None):
        reply = self.read() if reply is None else reply
        # This is the T-only product red after a real scene has been built.
        self.assertIn("spatial", reply, "PF5_SPATIAL_ENTRY: native read/preview must expose spatial diagnostics")
        spatial = reply["spatial"]
        self.assertEqual("panel-fill-spatial/1", spatial["schema"], "PF5_SPATIAL_SCHEMA")
        self.assertEqual("diagnostic-envelope-only", spatial["scope"], "PF5_ENVELOPE_NOT_ACTUAL_TIMBER")
        return spatial

    def integer(self, value, tag="PF5_EXACT_DECIMAL_STRING"):
        self.assertIs(type(value), str, tag)
        self.assertIsNotNone(re.fullmatch(r"0|-?[1-9][0-9]*", value), tag)
        return int(value)

    def points(self, points, dimension=2):
        self.assertIs(type(points), list, "PF5_VERTEX_LIST")
        result = []
        for point in points:
            self.assertEqual(dimension, len(point), "PF5_VERTEX_DIMENSION")
            result.append([self.integer(value) for value in point])
        return result

    def frame(self, value):
        result = {"origin": self.points([value["origin"]], 3)[0]}
        for key in ("u", "v", "n"):
            self.assertTrue(isinstance(value[key], list) and len(value[key]) == 3
                            and all(type(x) is int and x in (-1, 0, 1) for x in value[key]), "PF5_SIGNED_AXIS_VECTOR")
            result[key] = value[key]
        return result

    def region(self, value):
        result = {"area": self.integer(value["area"]), "components": []}
        for component in value["components"]:
            outer, holes = self.points(component["outer"]), [self.points(h) for h in component["holes"]]
            self.assertGreater(signed_area2(outer), 0, "PF5_NATIVE_OUTER_CCW")
            for hole in holes:
                self.assertLess(signed_area2(hole), 0, "PF5_NATIVE_HOLE_CW")
            xs = sorted({point[0] for loop in [outer]+holes for point in loop})
            ys = sorted({point[1] for loop in [outer]+holes for point in loop})
            rectangles = [[x0, y0, x1, y1] for x0, x1 in zip(xs, xs[1:]) for y0, y1 in zip(ys, ys[1:])
                          if inside(outer, x0+x1, y0+y1)
                          and not any(inside(h, x0+x1, y0+y1) for h in holes)]
            result["components"].append({"outer": outer, "holes": holes, "rectangles": rectangles})
        return result

    def compare_world(self, f, layer, interval):
        self.assertEqual("complete", layer["status"], "PF5_NATIVE_LAYER_STATUS")
        self.assertEqual(list(interval), [self.integer(x) for x in layer["interval"]], "PF5_NATIVE_LAYER_INTERVAL")
        frame = f["frame"]
        for component in layer["components"]:
            loops = [self.points(component["outer"])]+[self.points(h) for h in component["holes"]]
            for name, depth in zip(("near", "far"), interval):
                expected = [[[frame["origin"][k]+p[0]*frame["u"][k]+p[1]*frame["v"][k]
                              +depth*f["side"]*frame["n"][k] for k in range(3)] for p in loop] for loop in loops]
                world = component["world"][name]
                self.assertEqual(expected[0], self.points(world["outer"], 3), "PF5_NATIVE_WORLD_VERTEX")
                self.assertEqual(expected[1:], [self.points(h, 3) for h in world["holes"]], "PF5_NATIVE_WORLD_HOLES")
                for view, indices in (("top", (0, 1)), ("front", (0, 2)), ("side", (1, 2))):
                    projected = component["projections"][view][name]
                    expected2 = [[[p[i] for i in indices] for p in loop] for loop in expected]
                    self.assertEqual(expected2[0], self.points(projected["outer"]), "PF5_NATIVE_THREE_VIEW_VERTEX")
                    self.assertEqual(expected2[1:], [self.points(h) for h in projected["holes"]], "PF5_NATIVE_THREE_VIEW_HOLES")

    def junction(self, value):
        self.assertEqual("complete", value["status"], "PF5_NATIVE_PAIR_STATUS")
        return {"finishes": value["finishes"], "joinPolicy": value["joinPolicy"],
                "sharedEdges": [{"start": self.points([edge["start"]], 3)[0],
                                  "end": self.points([edge["end"]], 3)[0], "length": self.integer(edge["length"])}
                                 for edge in value["sharedEdges"]],
                "visibleContactDimension": value["visibleContactDimension"],
                "minimumL1Gap": None if value["minimumL1Gap"] is None else self.integer(value["minimumL1Gap"]),
                "layers": {key: {"volume": self.integer(item["volume"]), "contactDimension": item["contactDimension"],
                                  "relation": item["relation"]} for key, item in value["layers"].items()}}

    def checked(self, data, reply=None, finish_ids=None):
        reply = self.read() if reply is None else reply
        finish_ids = {} if finish_ids is None else finish_ids
        native = self.spatial(reply)
        self.assertIs(native["complete"], True, "PF5_NATIVE_COMPLETE")
        self.assertEqual([], native["errors"], "PF5_NATIVE_NO_UNDISCLOSED_UNSUPPORTED")
        expected = ORACLE.solve(data)
        # Room and section.A are diagnostic-input context, not native claims.
        candidate = {"schema": "pf5-geometry-output/1", "scope": "diagnostic-envelope-only",
                     "edgeIdentity": "not-modeled", "room": copy.deepcopy(data["room"]), "finishes": [], "junctions": []}
        sources = {f["id"]: f for f in data["finishes"]}
        self.assertEqual(sorted(sources), sorted(f["id"] for f in native["finishes"]), "PF5_NATIVE_EXPLICIT_FACE_INVENTORY")
        for actual in native["finishes"]:
            f = sources[actual["id"]]
            witness = next(item for item in expected["finishes"] if item["id"] == f["id"])
            source_finish_id = finish_ids.get(f["id"], f["id"])
            self.assertEqual(source_finish_id, actual["finishId"], "PF5_NATIVE_FINISH_REFERENCE")
            self.assertEqual("complete", actual["status"], "PF5_NATIVE_FINISH_STATUS")
            self.assertEqual([], actual["missing"], "PF5_NATIVE_NOT_PENDING")
            self.assertEqual({"id": "v-board-"+str(source_finish_id), "version": 1}, actual["panelVersion"], "PF5_NATIVE_PINNED_PANEL")
            self.assertEqual(1000+f["id"], actual["hostId"], "PF5_NATIVE_HOST_ID")
            entry = {"id": actual["id"], "label": actual["label"], "frame": self.frame(actual["frame"]),
                     "side": actual["side"], "thickness": self.integer(actual["thickness"]),
                     "section": [f["section"][0], self.integer(actual["h"])], "obstacles": [],
                     "panel": self.region(actual["panel"]), "timber": self.region(actual["timber"])}
            for key in ("label", "frame", "side", "thickness", "section"):
                self.assertEqual(witness[key], entry[key], "PF5_NATIVE_SOURCE_"+key.upper())
            self.compare_world(f, actual["panel"], (0, f["thickness"]))
            self.compare_world(f, actual["timber"], (f["thickness"], f["thickness"]+f["section"][1]))
            for key in ("panel", "timber"):
                self.assertEqual(witness[key]["area"], entry[key]["area"], "PF5_NATIVE_"+key.upper()+"_AREA")
                self.assertEqual(canonical_region(witness[key]), canonical_region(entry[key]), "PF5_NATIVE_"+key.upper()+"_REGION")
            objects = {o["ref"]: o for o in data["obstacles"]}
            for obstacle in actual["obstacles"]:
                entry["obstacles"].append({"ref": obstacle["ref"],
                    "projectedRect": [self.integer(x) for x in obstacle["projectedRect"]],
                    "normalInterval": [self.integer(x) for x in obstacle["normalInterval"]],
                    "footprintRelation": obstacle["footprintRelation"], "panel": obstacle["panel"], "timber": obstacle["timber"]})
                original = objects[obstacle["ref"]]
                self.assertEqual(original["min"], self.points([obstacle["world"]["min"]], 3)[0], "PF5_NATIVE_OBSTACLE_WORLD_MIN")
                self.assertEqual(original["max"], self.points([obstacle["world"]["max"]], 3)[0], "PF5_NATIVE_OBSTACLE_WORLD_MAX")
                for view, indices in (("top", (0, 1)), ("front", (0, 2)), ("side", (1, 2))):
                    self.assertEqual([original["min"][i] for i in indices]+[original["max"][i] for i in indices],
                                     [self.integer(x) for x in obstacle["projections"][view]], "PF5_NATIVE_OBSTACLE_PROJECTION")
            entry["obstacles"].sort(key=lambda item: (item["ref"][0], int(item["ref"][1:])))
            self.assertEqual(sorted(witness["obstacles"], key=lambda item: (item["ref"][0], int(item["ref"][1:]))),
                             entry["obstacles"], "PF5_NATIVE_EACH_SELECTED_OBSTACLE")
            host = actual["host"]
            self.assertEqual(1000+f["id"], host["id"], "PF5_NATIVE_TYPED_HOST")
            self.assertEqual({"id": host["id"], "fillId": f["id"], "h": f["section"][1]}, host["definition"], "PF5_NATIVE_HOST_SOURCE")
            entry["host"] = {"frame": self.frame(host["frame"]), "h": self.integer(host["h"]), "region": self.region(host["region"])}
            self.assertEqual(witness["host"]["frame"], entry["host"]["frame"], "PF5_NATIVE_HOST_RIGHT_HANDED")
            self.assertEqual(witness["host"]["region"]["area"], entry["host"]["region"]["area"], "PF5_NATIVE_HOST_AREA")
            self.assertEqual(canonical_region(witness["host"]["region"]), canonical_region(entry["host"]["region"]), "PF5_NATIVE_HOST_REFLECTION")
            if "state" in reply:
                source_host = next(item for item in reply["uiContract"]["state"]["derivedPlacements"] if item["id"] == host["id"])
                original_edges = [edge for component in source_host["derived"]["components"] for edge in component["edges"]]
                exposed_edges = [edge for component in host["region"]["components"] for edge in component["edges"]]
                self.assertEqual(sorted(original_edges, key=lambda item: json.dumps(item, sort_keys=True)),
                                 sorted(exposed_edges, key=lambda item: json.dumps(item, sort_keys=True)),
                                 "PF5_NATIVE_EXISTING_R41_EDGE_VALUES")
            candidate["finishes"].append(entry)
        candidate["finishes"].sort(key=lambda item: item["id"])
        # The constructor preserves selected-reference order. This adapter maps
        # the native typed set order back to that explicit input order only.
        for f in candidate["finishes"]:
            order = sources[f["id"]]["obstacles"]
            f["obstacles"].sort(key=lambda item: order.index(item["ref"]))
        candidate["junctions"] = [self.junction(item) for item in native["junctions"]]
        candidate["junctions"].sort(key=lambda item: item["finishes"])
        for found, wanted in zip(candidate["junctions"], expected["junctions"]):
            wanted = copy.deepcopy(wanted)
            wanted["sharedEdges"].sort(key=lambda edge: (edge["start"], edge["end"]))
            self.assertEqual(wanted["sharedEdges"], found["sharedEdges"], "PF5_NATIVE_SHARED_EDGES")
            self.assertEqual(wanted, found, "PF5_NATIVE_PAIR_VALUES")
        self.assertEqual(len(expected["junctions"]), len(candidate["junctions"]), "PF5_NATIVE_PAIR_INVENTORY")
        self.assertEqual([], CHECKER.check(data, candidate), "PF5_NATIVE_INDEPENDENT_WORLD_CHECKER")
        return native, candidate

    def test_Q47_six_heights_keep_two_independent_layers(self):
        for height, panel, timber in [(2600, 8800, 8800), (2400, 10000, 10000), (2480, 10000, 8800),
                                      (2491, 10000, 8800), (2461, 10000, 10000), (3000, 10000, 10000)]:
            with self.subTest(height=height):
                data = example()
                data["finishes"][0]["frame"]["origin"][2] = height
                self.seed(data)
                _, checked = self.checked(data)
                self.assertEqual((panel, timber), tuple(checked["finishes"][0][key]["area"] for key in ("panel", "timber")), "PF5_Q47_EXACT")

    def test_explicit_step_junctions_and_missing_side_are_not_synthesized(self):
        data = step_faces()
        self.seed(data)
        _, candidate = self.checked(data)
        pair = next(j for j in candidate["junctions"] if j["finishes"] == [2, 3])
        self.assertEqual(8100, pair["layers"]["panel-panel"]["volume"], "PF5_EXPLICIT_UNRESOLVED_OVERLAP")
        data["finishes"].pop()
        self.seed(data)
        _, candidate = self.checked(data)
        self.assertEqual([1, 2], [f["id"] for f in candidate["finishes"]], "PF5_NO_AUTOMATIC_SIDE_FACE")
        self.assertEqual(139, candidate["junctions"][0]["minimumL1Gap"], "PF5_OPEN_STEP_GAP")

    def test_holes_all_components_point_touch_and_empty_survive(self):
        data = example()
        data["finishes"][0]["region"]["holes"] = [[[20, 20], [30, 20], [30, 30], [20, 30]]]
        data["obstacles"][0].update(min=[40, -10, 2489], max=[60, 110, 2519])
        self.seed(data)
        native, _ = self.checked(data)
        edges = [edge for c in native["finishes"][0]["host"]["region"]["components"] for edge in c["edges"]]
        self.assertTrue(any(any(source[0].startswith("b20:") for source in edge["key"]) for edge in edges), "PF5_NATIVE_R41_KEYS")
        self.assertTrue(any(any(source[0].startswith("h0e") for source in edge["key"]) for edge in edges), "PF5_NATIVE_HOLE_SOURCE_KEYS")
        data = example()
        data["obstacles"] = [{"ref": "b20", "min": [0, 50, 2489], "max": [50, 100, 2519]},
                             {"ref": "b21", "min": [50, 0, 2489], "max": [100, 50, 2519]}]
        data["finishes"][0]["obstacles"] = ["b20", "b21"]
        self.seed(data)
        self.checked(data)
        data["obstacles"][0].update(min=[-1, -1, 2480], max=[101, 101, 2519])
        data["finishes"].append(face(2, origin=(200, 0, 2480), obstacles=[]))
        self.seed(data)
        _, candidate = self.checked(data)
        self.assertEqual({"area": 0, "components": []}, candidate["finishes"][0]["panel"], "PF5_NATIVE_EMPTY_IS_REAL")
        self.assertIsNone(candidate["junctions"][0]["minimumL1Gap"], "PF5_NATIVE_EMPTY_GAP_NULL")

    def test_unselected_and_coincident_typed_obstacles_remain_explicit(self):
        data = example()
        data["obstacles"].append({**copy.deepcopy(data["obstacles"][0]), "ref": "c20"})
        data["finishes"][0]["obstacles"] = ["b20", "c20"]
        self.seed(data)
        self.checked(data)
        data["finishes"][0]["obstacles"] = []
        self.seed(data)
        _, candidate = self.checked(data)
        self.assertEqual(10000, candidate["finishes"][0]["timber"]["area"], "PF5_UNSELECTED_OBJECTS_NOT_CUT")

    def test_fill_identity_keeps_reverse_creation_and_shared_finish_distinct(self):
        data = step_faces()
        data["finishes"].reverse()
        self.seed(data)
        native, _ = self.checked(data)
        self.assertEqual([1, 2, 3], [f["id"] for f in native["finishes"]], "PF5_NATIVE_FILL_ID_ORDER")
        self.assertEqual([[1, 2], [1, 3], [2, 3]], [j["finishes"] for j in native["junctions"]], "PF5_NATIVE_PAIR_ID_ORDER")
        data = example()
        self.seed(data)
        self.transaction([
            {"op": "put-panel-fill", "value": {"id": 9, "finishSurfaceId": 1,
             "panel": {"id": "v-board-1", "version": 1}, "lengthAlong": "v", "origin": [0, 0],
             "gap": 0, "pattern": "straight", "threshold": {"parameterId": 90, "fieldId": 1}}},
            {"op": "put-derived-placement", "value": {"id": 1009, "fillId": 9, "h": 30}},
        ])
        second = copy.deepcopy(data["finishes"][0])
        second["id"] = 9  # Diagnostic identity is the explicit fill identity.
        data["finishes"].append(second)
        native, _ = self.checked(data, finish_ids={9: 1})
        self.assertEqual([1, 9], [f["id"] for f in native["finishes"]], "PF5_SAME_FINISH_TWO_EXPLICIT_FILLS")
        self.assertEqual([1, 1], [f["finishId"] for f in native["finishes"]], "PF5_SHARED_FINISH_SOURCE_NOT_ALIASED")
        self.assertEqual([[1, 9]], [j["finishes"] for j in native["junctions"]], "PF5_NO_IMPLICIT_FILL_GROUP")

    def test_all_signed_axis_frames_and_sides_have_exact_world_vertices(self):
        count = 0
        for permutation in itertools.permutations(range(3)):
            for signs in itertools.product((-1, 1), repeat=3):
                u, v, n = [[signs[i] if j == permutation[i] else 0 for j in range(3)] for i in range(3)]
                determinant = u[0]*(v[1]*n[2]-v[2]*n[1])-u[1]*(v[0]*n[2]-v[2]*n[0])+u[2]*(v[0]*n[1]-v[1]*n[0])
                if determinant != 1:
                    continue
                for side in (-1, 1):
                    data, origin = example(), [10, 20, 30]
                    data["finishes"] = [face(origin=origin, u=u, v=v, n=n, side=side)]
                    corners = [[origin[k]+x*u[k]+y*v[k]+q*side*n[k] for k in range(3)]
                               for x, y, q in itertools.product((20, 40), (30, 50), (10, 20))]
                    data["obstacles"][0].update(min=[min(p[k] for p in corners) for k in range(3)],
                                                max=[max(p[k] for p in corners) for k in range(3)])
                    self.seed(data)
                    self.checked(data)
                    count += 1
        self.assertEqual(48, count, "PF5_NATIVE_FRAME_SCAN_COUNT")

    def test_one_mm_product_scan_depth_plan_and_junction_gap(self):
        count = 0
        self.seed(example())
        for axis, first, last in [(0, -21, 101), (1, -61, 101), (2, 2440, 2520)]:
            for position in range(first, last+1):
                data = example()
                extent = data["obstacles"][0]["max"][axis]-data["obstacles"][0]["min"][axis]
                data["obstacles"][0]["min"][axis] = position
                data["obstacles"][0]["max"][axis] = position+extent
                lo, hi = data["obstacles"][0]["min"], data["obstacles"][0]["max"]
                self.command(f"line beam 20 along x from {lo[0]} to {hi[0]} at {(lo[1]+hi[1])//2} "
                             f"width {hi[1]-lo[1]} depth {hi[2]-lo[2]} top {hi[2]}")
                self.checked(data)
                count += 1
        for gap in range(-10, 11):
            data = example()
            data["obstacles"] = []
            data["finishes"] = [face(origin=(0, 0, 0), obstacles=[]),
                face(2, origin=(100+gap, 0, 0), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0), obstacles=[])]
            self.seed(data)
            self.checked(data)
            count += 1
        self.assertEqual(388, count, "PF5_NATIVE_ONE_MM_SCAN_COUNT")

    def test_face_edge_point_contact_has_exact_dimension_and_zero_volume(self):
        for origin, dimension, volume in [((0, 0, 9), 2, 0), ((100, 0, 9), 1, 0),
                                          ((100, 100, 9), 0, 0), ((101, 100, 9), -1, 0),
                                          ((0, 0, 8), 3, 10000), ((0, 0, 0), 3, 90000)]:
            with self.subTest(origin=origin):
                data = example()
                data["obstacles"] = []
                data["finishes"] = [face(origin=(0, 0, 0), obstacles=[]), face(2, origin=origin, obstacles=[])]
                self.seed(data)
                _, candidate = self.checked(data)
                layer = candidate["junctions"][0]["layers"]["panel-panel"]
                self.assertEqual((dimension, volume), (layer["contactDimension"], layer["volume"]), "PF5_NATIVE_EXACT_CONTACT_STRATUM")

    def test_volume_overflow_is_explicit_unsupported_and_world_remains_valid(self):
        data = example()
        data["obstacles"] = []
        outline = [[0, 0], [90000000, 0], [90000000, 90000000], [0, 90000000]]
        data["finishes"] = [face(1, origin=(0, 0, 0), outer=outline, obstacles=[]),
                             face(2, origin=(0, 0, 0), outer=outline, obstacles=[])]
        for f in data["finishes"]:
            f.update(thickness=1, section=[27, 1000000])
        self.seed(data, panel_size=(100000000, 100000000))
        before = self.command("dump")["text"]
        native = self.spatial()
        self.assertIs(native["complete"], False, "PF5_OVERFLOW_NOT_COMPLETE")
        pair = native["junctions"][0]
        self.assertEqual("unsupported", pair["status"], "PF5_OVERFLOW_IS_UNSUPPORTED")
        self.assertEqual("SPATIAL_VOLUME_CAPACITY", pair["error"]["code"], "PF5_OVERFLOW_NAMED_CAPACITY")
        self.assertNotIn("layers", pair, "PF5_OVERFLOW_NO_PARTIAL_OR_TRUNCATED_LAYERS")
        self.assertEqual([1, 2], pair["finishes"], "PF5_OVERFLOW_PAIR_IDENTITY")
        self.assertTrue(any(error["code"] == "SPATIAL_VOLUME_CAPACITY" and error["finishes"] == [1, 2]
                            for error in native["errors"]), "PF5_OVERFLOW_EXPOSED_IN_ERRORS")
        for finish in native["finishes"]:
            self.assertEqual("complete", finish["status"], "PF5_OVERFLOW_DOES_NOT_CORRUPT_LOCAL_GEOMETRY")
            self.assertEqual(8100000000000000, self.integer(finish["panel"]["area"]), "PF5_LARGE_EXACT_AREA")
        self.assertEqual(before, self.command("dump")["text"], "PF5_OVERFLOW_READ_PRESERVES_WORLD")

    def test_world_far_point_outside_d1_is_unsupported_without_clamping_or_world_change(self):
        data = example()
        data["obstacles"] = []
        data["finishes"][0].update(thickness=1, obstacles=[])
        data["finishes"][0]["frame"]["origin"][2] = 99999998
        data["finishes"].append(face(2, origin=(0, 0, 2480), obstacles=[]))
        preview = self.seed(data)
        self.assertTrue(preview["valid"], "PF5_EXISTING_LEGAL_WORLD_STAYS_CONFIRMABLE")
        before = self.command("dump")["text"]
        native = self.spatial()
        self.assertIs(native["complete"], False, "PF5_D1_FAR_POINT_NOT_COMPLETE")
        finish = native["finishes"][0]
        self.assertEqual("unsupported", finish["status"], "PF5_D1_FAR_POINT_UNSUPPORTED")
        self.assertEqual("SPATIAL_COORD_CAPACITY", finish["error"]["code"], "PF5_D1_CAPACITY_IS_NAMED")
        self.assertEqual([], finish["missing"], "PF5_D1_CAPACITY_IS_NOT_MISSING_SOURCE")
        for key in ("panel", "timber", "host"):
            self.assertIsNone(finish[key], "PF5_D1_NO_PARTIAL_OR_CLAMPED_GEOMETRY")
        self.assertTrue(any(error["code"] == "SPATIAL_COORD_CAPACITY" and error["fillId"] == 1
                            for error in native["errors"]), "PF5_D1_CAPACITY_EXPOSED_IN_ERRORS")
        pair = native["junctions"][0]
        self.assertEqual("unsupported", pair["status"], "PF5_UNAVAILABLE_SOURCE_PAIR_NOT_MEASURED")
        self.assertEqual("SPATIAL_SOURCE_UNAVAILABLE", pair["error"]["code"], "PF5_UNAVAILABLE_SOURCE_PAIR_REASON")
        for key in ("sharedEdges", "visibleContactDimension", "minimumL1Gap", "layers"):
            self.assertNotIn(key, pair, "PF5_UNAVAILABLE_SOURCE_PAIR_NO_FAKE_EMPTY")
        self.assertEqual(before, self.command("dump")["text"], "PF5_D1_UNSUPPORTED_PRESERVES_WORLD")

    def test_pending_height_preserves_panel_and_never_invents_timber(self):
        data = example()
        self.seed(data, hosts=False)
        native = self.spatial()
        self.assertIs(native["complete"], False, "PF5_PENDING_IS_NOT_COMPLETE")
        self.assertEqual([], native["errors"], "PF5_PENDING_IS_NOT_UNSUPPORTED")
        item = native["finishes"][0]
        self.assertEqual("pending", item["status"], "PF5_MISSING_HEIGHT_IS_VISIBLE")
        self.assertEqual(["derived-placement.h"], item["missing"], "PF5_MISSING_SOURCE_NAMED")
        self.assertIsNone(item["h"], "PF5_NO_DEFAULT_H")
        self.assertIsNone(item["hostId"], "PF5_NO_SYNTHETIC_HOST_ID")
        self.assertIsNone(item["timber"], "PF5_NO_SYNTHETIC_TIMBER")
        self.assertIsNone(item["host"], "PF5_NO_SYNTHETIC_HOST")
        self.assertEqual(10000, self.integer(item["panel"]["area"]), "PF5_PENDING_STILL_HAS_PANEL")
        self.assertIsNone(item["obstacles"][0]["timber"], "PF5_PENDING_OBSTACLE_LAYER")

    def test_preview_cancel_restore_reopen_are_read_only_and_recomputed(self):
        data = step_faces()
        self.seed(data)
        before_dump, before_read = self.command("dump")["text"], self.read()
        self.checked(data, before_read)
        update = copy.deepcopy(before_read["state"]["finishSurfaces"][0])
        update = {key: update[key] for key in ("id", "name", "boundaryId", "frame", "structureSide", "obstacles")}
        # Original source fields in state retain native protocol types; use the
        # explicit fixture integers for this transaction instead of derived data.
        update["frame"] = {"origin": [0, 0, 2599], "U": "+X", "V": "+Y", "N": "+Z"}
        preview = self.transaction([{"op": "put-finish-surface", "value": update}], confirm=False)
        self.assertIn("spatial", preview, "PF5_SPATIAL_PREVIEW_ENTRY")
        self.checked(data, {"spatial": preview["spatial"]["before"]})
        changed = copy.deepcopy(data)
        changed["finishes"][0]["frame"]["origin"][2] = 2599
        self.checked(changed, {"spatial": preview["spatial"]["after"]})
        self.assertEqual(before_dump, self.command("dump")["text"], "PF5_PREVIEW_NO_WORLD_MUTATION")
        self.command("panel-fill-cancel "+str(preview["token"]))
        self.assertEqual(before_dump, self.command("dump")["text"], "PF5_CANCEL_NO_WORLD_MUTATION")
        saved = self.directory/"reopen.scene"
        saved.write_text(before_dump, encoding="utf-8")
        self.bridge.stop()
        self.bridge = BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.command("loadfile "+str(saved))
        self.checked(data)
        self.assertEqual(before_dump, self.command("dump")["text"], "PF5_SPATIAL_NOT_SAVED_AS_CACHE")

    def test_confirm_undo_redo_reject_and_stale_preserve_the_current_native_geometry(self):
        data = example()
        self.seed(data)
        before_dump, before = self.command("dump")["text"], self.spatial()
        update = {"id": 1, "name": data["finishes"][0]["label"], "boundaryId": 101,
                  "frame": {"origin": [0, 0, 2600], "U": "+X", "V": "+Y", "N": "+Z"},
                  "structureSide": 1, "obstacles": ["b20"]}
        preview = self.transaction([{"op": "put-finish-surface", "value": update}], confirm=False)
        self.assertEqual(before, preview["spatial"]["before"], "PF5_HISTORY_PREVIEW_BEFORE")
        self.assertEqual(before_dump, self.command("dump")["text"], "PF5_HISTORY_PREVIEW_ZERO_WRITE")
        self.command("panel-fill-confirm "+str(preview["token"]))
        changed = copy.deepcopy(data)
        changed["finishes"][0]["frame"]["origin"][2] = 2600
        after, _ = self.checked(changed)
        after_dump = self.command("dump")["text"]
        self.assertEqual(preview["spatial"]["after"], after, "PF5_CONFIRM_MATCHES_CANDIDATE")
        self.assertNotEqual(before_dump, after_dump, "PF5_CONFIRM_WRITES_REQUESTED_DEFINITION")
        self.command("line undo")
        self.assertEqual(before_dump, self.command("dump")["text"], "PF5_UNDO_EXACT_DEFINITIONS")
        self.assertEqual(before, self.spatial(), "PF5_UNDO_RECOMPUTES_EXACT_GEOMETRY")

        # A rejected preview must preserve the redo stack and report no stale
        # candidate geometry. Use the existing invalid-reference rule.
        revision = self.read()["revision"]
        invalid = copy.deepcopy(update)
        invalid["boundaryId"] = 9999
        path = self.directory/"invalid-spatial.json"
        path.write_text(json.dumps({"schema": "panel-fill-transaction/1", "expectedRevision": revision,
                                    "operations": [{"op": "put-finish-surface", "value": invalid}]}), encoding="utf-8")
        rejected = self.command("panel-fill-preview "+str(path))["preview"]
        self.assertIs(rejected["valid"], False, "PF5_INVALID_SOURCE_PREVIEW_REJECTED")
        unavailable = rejected["spatial"]["after"]
        self.assertIs(unavailable["complete"], False, "PF5_INVALID_CANDIDATE_NOT_COMPLETE")
        self.assertEqual([], unavailable["finishes"], "PF5_INVALID_CANDIDATE_NO_STALE_HOST")
        self.assertEqual("CANDIDATE_UNAVAILABLE", unavailable["errors"][0]["code"], "PF5_INVALID_CANDIDATE_REASON")
        rejected_confirm = self.bridge.command("panel-fill-confirm "+str(rejected["token"]))
        self.assertIs(rejected_confirm["ok"], False, "PF5_INVALID_CONFIRM_REJECTED")
        self.command("panel-fill-cancel "+str(rejected["token"]))
        self.assertEqual((before_dump, revision, before),
                         (self.command("dump")["text"], self.read()["revision"], self.spatial()),
                         "PF5_REJECTION_ZERO_DEFINITION_REVISION_GEOMETRY_WRITE")
        self.command("line redo")
        self.assertEqual(after_dump, self.command("dump")["text"], "PF5_REDO_SURVIVES_REJECTION")
        self.assertEqual(after, self.spatial(), "PF5_REDO_RECOMPUTES_EXACT_GEOMETRY")

        update["frame"]["origin"][2] = 2491
        pending = self.transaction([{"op": "put-finish-surface", "value": update}], confirm=False)
        self.command("line beam 20 along x from 40 to 60 at 51 width 60 depth 500 top 3000")
        moved = copy.deepcopy(changed)
        moved["obstacles"][0]["min"][1], moved["obstacles"][0]["max"][1] = 21, 81
        moved_spatial, _ = self.checked(moved)
        moved_dump, moved_revision = self.command("dump")["text"], self.read()["revision"]
        stale = self.bridge.command("panel-fill-confirm "+str(pending["token"]))
        self.assertIs(stale["ok"], False, "PF5_STALE_CONFIRM_REJECTED")
        self.assertEqual("STALE", stale["code"], "PF5_STALE_REASON")
        self.assertEqual((moved_dump, moved_revision, moved_spatial),
                         (self.command("dump")["text"], self.read()["revision"], self.spatial()),
                         "PF5_STALE_ZERO_DEFINITION_REVISION_GEOMETRY_WRITE")


if __name__ == "__main__":
    unittest.main()
