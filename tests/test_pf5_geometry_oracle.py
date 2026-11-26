"""Independent PF-5 design-tool contracts; these are not product acceptance tests.

Run directly with Python. Missing tools fail one named availability assertion;
geometry tests then skip explicitly, rather than producing an import/setup error.
"""
import copy
import importlib.util
import itertools
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


def _load(name):
    path = HERE / (name + ".py")
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ORACLE = _load("pf5_geometry_oracle")
CHECKER = _load("pf5_geometry_check")


def face(identity=1, origin=(0, 0, 2480), u=(1, 0, 0), v=(0, 1, 0),
         n=(0, 0, 1), side=1, outer=None, holes=None, obstacles=None):
    return {
        "id": identity,
        "label": "explicit fixture face " + str(identity),
        "frame": {"origin": list(origin), "u": list(u), "v": list(v), "n": list(n)},
        "side": side,
        "region": {"outer": outer if outer is not None else [[0, 0], [100, 0], [100, 100], [0, 100]],
                   "holes": holes if holes is not None else []},
        "obstacles": obstacles if obstacles is not None else ["b20"],
        "thickness": 9,
        "section": [27, 30],
    }


def example():
    # These are named fixture choices, never application defaults. The Q47
    # centimetre examples are explicitly converted to integer millimetres.
    return {
        "schema": "pf5-geometry-input/1",
        "room": {"min": [0, 0, 0], "max": [100, 100, 3000]},
        "obstacles": [{"ref": "b20", "min": [40, 20, 2500], "max": [60, 80, 3000]}],
        "finishes": [face()],
    }


def six_faces():
    result = example()
    wall = [[0, 0], [100, 0], [100, 2480], [0, 2480]]
    result["finishes"] = [
        face(),
        face(2, (0, 0, 0), side=-1),
        face(3, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), -1, outer=wall),
        face(4, (100, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 1, outer=wall),
        face(5, (0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0), 1, outer=wall),
        face(6, (0, 100, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0), -1, outer=wall),
    ]
    return result


def step_faces():
    # Three explicitly authored surfaces. The 31/69 boundaries and both
    # elevations are fixture choices, not an automatic beam-wrap policy.
    result = example()
    result["obstacles"][0].update(min=[40, 0, 2500], max=[60, 100, 3000])
    result["finishes"] = [
        face(origin=(0, 0, 2600), outer=[[0, 0], [31, 0], [31, 100], [0, 100]]),
        face(2, origin=(0, 0, 2461), outer=[[31, 0], [69, 0], [69, 100], [31, 100]]),
        face(3, origin=(31, 0, 2461), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0),
             outer=[[0, 0], [100, 0], [100, 139], [0, 139]]),
    ]
    return result


class PF5OracleAvailability(unittest.TestCase):
    def test_PF5_EXECUTABLE_GEOMETRY_AND_INDEPENDENT_CHECKER_EXIST(self):
        self.assertTrue(
            ORACLE is not None and callable(getattr(ORACLE, "solve", None))
            and CHECKER is not None and callable(getattr(CHECKER, "check", None)),
            "PF5_EXECUTABLE_GEOMETRY_AND_INDEPENDENT_CHECKER_EXIST: "
            "the design package must provide both callable diagnostic tools",
        )


@unittest.skipUnless(ORACLE is not None and CHECKER is not None, "PF5 diagnostic tools not installed")
class PF5GeometryOracle(unittest.TestCase):
    def checked(self, data):
        before = copy.deepcopy(data)
        result = ORACLE.solve(data)
        self.assertEqual([], CHECKER.check(data, result), "PF5_INDEPENDENT_CHECKER")
        self.assertEqual(before, data, "PF5_INPUT_PRESERVED")
        return result

    def test_Q47_three_heights_and_exact_touch_are_separate_layers(self):
        for height, panel_area, timber_area in [
            (2600, 8800, 8800), (2400, 10000, 10000), (2480, 10000, 8800),
            (2491, 10000, 8800), (2461, 10000, 10000), (3000, 10000, 10000),
        ]:
            with self.subTest(height=height):
                data = example()
                data["finishes"][0]["frame"]["origin"][2] = height
                result = self.checked(data)["finishes"][0]
                self.assertEqual(panel_area, result["panel"]["area"], "PF5_PANEL_INTERVAL_0_T")
                self.assertEqual(timber_area, result["timber"]["area"], "PF5_TIMBER_INTERVAL_T_T_PLUS_H")

    def test_vertical_normal_and_negative_side_board_back(self):
        for side, bounds in [(1, (1010, 1020)), (-1, (980, 990))]:
            with self.subTest(side=side):
                data = example()
                data["finishes"] = [face(origin=(1000, 0, 0), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0), side=side)]
                data["obstacles"][0].update(min=[bounds[0], 20, 20], max=[bounds[1], 80, 80])
                result = self.checked(data)["finishes"][0]
                self.assertEqual(10000, result["panel"]["area"], "PF5_VERTICAL_PANEL")
                self.assertEqual(6400, result["timber"]["area"], "PF5_NORMAL_NOT_WORLD_Z")
                frame = result["host"]["frame"]
                self.assertEqual([1000 + side * 9, 0, 0], frame["origin"], "PF5_BOARD_BACK")
                self.assertEqual([0, 0, side], frame["v"], "PF5_NEGATIVE_SIDE_RH_FRAME")
                self.assertEqual([side, 0, 0], frame["n"])
                hole = result["host"]["region"]["components"][0]["holes"][0]
                self.assertEqual((-80, -20) if side < 0 else (20, 80),
                                 (min(p[1] for p in hole), max(p[1] for p in hole)), "PF5_HOST_V_REFLECTION")

    def test_selected_obstacles_only_and_no_automatic_wrap_faces(self):
        data = example()
        data["finishes"][0]["obstacles"] = []
        result = self.checked(data)
        self.assertEqual([1], [f["id"] for f in result["finishes"]], "PF5_NO_AUTO_BEAM_WRAP")
        self.assertEqual([], result["finishes"][0]["obstacles"], "PF5_EXPLICIT_SELECTION")
        self.assertEqual(10000, result["finishes"][0]["timber"]["area"], "PF5_UNSELECTED_BEAM_IGNORED")

    def test_hole_and_disconnected_components_are_retained(self):
        data = example()
        data["finishes"][0]["region"]["holes"] = [[[20, 20], [30, 20], [30, 30], [20, 30]]]
        data["obstacles"][0].update(min=[40, -10, 2489], max=[60, 110, 2519])
        result = self.checked(data)["finishes"][0]
        self.assertEqual(9900, result["panel"]["area"], "PF5_PANEL_TOUCH_NOT_CUT")
        self.assertEqual(7900, result["timber"]["area"], "PF5_HOLE_AND_STRIP")
        self.assertEqual(2, len(result["host"]["region"]["components"]), "PF5_KEEP_EVERY_COMPONENT")
        self.assertEqual(1, sum(len(c["holes"]) for c in result["host"]["region"]["components"]))

    def test_point_touch_components_stay_distinct_and_empty_is_legal(self):
        data = example()
        data["obstacles"] = [
            {"ref": "b20", "min": [0, 50, 2489], "max": [50, 100, 2519]},
            {"ref": "b21", "min": [50, 0, 2489], "max": [100, 50, 2519]},
        ]
        data["finishes"][0]["obstacles"] = ["b20", "b21"]
        result = self.checked(data)["finishes"][0]
        self.assertEqual(2, len(result["host"]["region"]["components"]), "PF5_INTERIOR_CONNECTIVITY")
        self.assertEqual(5000, result["timber"]["area"])
        data["obstacles"][0].update(min=[-1, -1, 2489], max=[101, 101, 2519])
        result = self.checked(data)["finishes"][0]
        self.assertEqual({"area": 0, "components": []}, result["host"]["region"], "PF5_EMPTY_HOST_LEGAL")

    def test_invalid_or_missing_geometry_never_gets_guessed(self):
        changes = [
            lambda f: f.pop("thickness"),
            lambda f: f.update(thickness=9.5),
            lambda f: f.update(thickness=0),
            lambda f: f.update(section=[27, 0]),
            lambda f: f.pop("side"),
            lambda f: f["frame"].pop("origin"),
            lambda f: f["frame"].update(n=[0, 0, -1]),
            lambda f: f.update(obstacles=["b999"]),
            lambda f: f["region"].update(holes=[[[0, 20], [20, 20], [20, 40], [0, 40]]]),
            lambda f: f["region"].update(holes=[[[10, 10], [30, 10], [30, 30], [10, 30]],
                                                     [[30, 10], [40, 10], [40, 20], [30, 20]]]),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                data = example()
                change(data["finishes"][0])
                with self.assertRaises(ValueError, msg="PF5_EXPLICIT_VALID_INPUT_ONLY"):
                    ORACLE.solve(data)

    def test_unrepresentable_hole_touching_concave_corner_rejects(self):
        data = example()
        data["finishes"][0]["region"]["outer"] = [[0, 0], [100, 0], [100, 100], [50, 100], [50, 50], [0, 50]]
        data["obstacles"][0].update(min=[50, 30, 2489], max=[70, 50, 2519])
        with self.assertRaisesRegex(ValueError, "TOPOLOGY", msg="PF5_NO_BBOX_FALLBACK"):
            ORACLE.solve(data)

    def test_ceiling_walls_floor_junctions_are_read_only_relationships(self):
        data = six_faces()
        result = self.checked(data)
        self.assertEqual(6, len(result["finishes"]))
        self.assertEqual(15, len(result["junctions"]))
        for item in result["junctions"]:
            self.assertEqual("unselected", item["joinPolicy"], "PF5_NO_INVENTED_TRIM_POLICY")
        ceiling_west = next(j for j in result["junctions"] if j["finishes"] == [1, 3])
        self.assertEqual(100, sum(e["length"] for e in ceiling_west["sharedEdges"]), "PF5_EFFECTIVE_SHARED_EDGE")
        self.assertEqual(1, ceiling_west["visibleContactDimension"])
        self.assertEqual(0, ceiling_west["minimumL1Gap"])
        self.assertEqual(0, ceiling_west["layers"]["panel-panel"]["volume"])
        opposite = next(j for j in result["junctions"] if j["finishes"] == [3, 4])
        self.assertEqual(100, opposite["minimumL1Gap"])

    def test_cross_face_volume_overlap_is_reported_without_choosing_a_joint(self):
        data = example()
        data["obstacles"] = []
        data["finishes"] = [face(origin=(0, 0, 0), obstacles=[]),
                            face(2, origin=(100, 0, -50), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0), side=-1, obstacles=[])]
        junction = self.checked(data)["junctions"][0]
        self.assertEqual(8100, junction["layers"]["panel-panel"]["volume"], "PF5_POSITIVE_VOLUME")
        self.assertEqual("overlap", junction["layers"]["panel-panel"]["relation"])
        self.assertEqual("unselected", junction["joinPolicy"])

    def test_layer_face_edge_point_touch_have_zero_volume(self):
        for origin, dimension, volume in [((0, 0, 9), 2, 0), ((100, 0, 9), 1, 0),
                                          ((100, 100, 9), 0, 0), ((101, 100, 9), -1, 0),
                                          ((0, 0, 8), 3, 10000)]:
            with self.subTest(origin=origin):
                data = example()
                data["obstacles"] = []
                data["finishes"] = [face(origin=(0, 0, 0), obstacles=[]), face(2, origin=origin, obstacles=[])]
                layer = self.checked(data)["junctions"][0]["layers"]["panel-panel"]
                self.assertEqual((dimension, volume), (layer["contactDimension"], layer["volume"]), "PF5_CROSS_FACE_POSITIVE_VOLUME_ONLY")

    def test_empty_region_has_no_fictitious_junction_and_null_gap(self):
        data = example()
        data["obstacles"][0].update(min=[-1, -1, 2480], max=[101, 101, 2519])
        data["finishes"].append(face(2, origin=(200, 0, 2480), obstacles=[]))
        result = self.checked(data)
        junction = result["junctions"][0]
        self.assertEqual([], junction["sharedEdges"], "PF5_EMPTY_JUNCTION")
        self.assertEqual(-1, junction["visibleContactDimension"])
        self.assertIsNone(junction["minimumL1Gap"], "PF5_EMPTY_GAP_IS_NULL")
        for layer in junction["layers"].values():
            self.assertEqual({"volume": 0, "contactDimension": -1, "relation": "separate"}, layer)
        for key in ("panel", "timber"):
            candidate = copy.deepcopy(result)
            candidate["finishes"][0][key]["components"] = {}
            self.assertTrue(CHECKER.check(data, candidate), "PF5_EMPTY_COMPONENT_MUST_BE_LIST")
        candidate = copy.deepcopy(result)
        candidate["finishes"][0]["host"]["region"]["components"] = {}
        self.assertTrue(CHECKER.check(data, candidate), "PF5_EMPTY_HOST_COMPONENT_MUST_BE_LIST")

    def test_explicit_high_ceiling_low_beam_bottom_and_side_closure(self):
        data = step_faces()
        result = self.checked(data)
        by_id = {f["id"]: f for f in result["finishes"]}
        self.assertEqual([2600, 2461], [by_id[i]["frame"]["origin"][2] for i in (1, 2)], "PF5_TWO_EXPLICIT_HEIGHTS")
        self.assertEqual((13900, 3900), (by_id[3]["panel"]["area"], by_id[3]["timber"]["area"]), "PF5_SIDE_CLOSURE_TWO_LAYERS")
        pairs = {tuple(j["finishes"]): j for j in result["junctions"]}
        for pair, height in [((1, 3), 2600), ((2, 3), 2461)]:
            self.assertEqual([{"start": [31, 0, height], "end": [31, 100, height], "length": 100}],
                             pairs[pair]["sharedEdges"], "PF5_SIDE_CLOSURE_ENDPOINT")
            self.assertEqual("unselected", pairs[pair]["joinPolicy"], "PF5_SIDE_CLOSURE_NO_AUTO_TRIM")
        self.assertEqual(8100, pairs[2, 3]["layers"]["panel-panel"]["volume"], "PF5_SIDE_CLOSURE_UNRESOLVED_OVERLAP")
        data["finishes"].pop()
        without = self.checked(data)
        self.assertEqual([1, 2], [f["id"] for f in without["finishes"]], "PF5_MISSING_SIDE_NOT_SYNTHESIZED")
        self.assertEqual([], without["junctions"][0]["sharedEdges"])
        self.assertEqual(139, without["junctions"][0]["minimumL1Gap"], "PF5_OPEN_STEP_GAP_REPORTED")
        self.assertEqual("unselected", without["junctions"][0]["joinPolicy"])

    def test_uint32_identity_d1_projection_and_typed_coincident_obstacles(self):
        data = example()
        data["finishes"][0]["id"] = 4_294_967_295
        data["obstacles"].append({**copy.deepcopy(data["obstacles"][0]), "ref": "c4294967295"})
        data["finishes"][0]["obstacles"].append("c4294967295")
        result = self.checked(data)["finishes"][0]
        self.assertEqual(8800, result["timber"]["area"], "PF5_COINCIDENT_UNION_ONCE")
        self.assertEqual(["b20", "c4294967295"], [o["ref"] for o in result["obstacles"]], "PF5_TYPED_DIAGNOSTICS_PRESERVED")
        for invalid in (0, -1, 4_294_967_296, True):
            data["finishes"][0]["id"] = invalid
            with self.assertRaises(ValueError, msg="PF5_UINT32_FINISH_POSITIVE"):
                ORACLE.solve(data)
        data = example()
        data["finishes"][0]["frame"]["origin"][0] = -100_000_000
        with self.assertRaisesRegex(ValueError, "local projection", msg="PF5_D1_LOCAL_PROJECTION"):
            ORACLE.solve(data)

    def test_all_signed_axis_frames_and_structural_sides(self):
        count = 0
        for permutation in itertools.permutations(range(3)):
            for signs in itertools.product((-1, 1), repeat=3):
                axes = [[signs[i] if j == permutation[i] else 0 for j in range(3)] for i in range(3)]
                u, v, n = axes
                determinant = (u[0] * (v[1] * n[2] - v[2] * n[1])
                               - u[1] * (v[0] * n[2] - v[2] * n[0])
                               + u[2] * (v[0] * n[1] - v[1] * n[0]))
                if determinant != 1:
                    continue
                for side in (-1, 1):
                    data = example()
                    origin = [10, 20, 30]
                    data["finishes"] = [face(origin=origin, u=u, v=v, n=n, side=side)]
                    corners = [[origin[k] + x*u[k] + y*v[k] + q*side*n[k] for k in range(3)]
                               for x, y, q in itertools.product((20, 40), (30, 50), (10, 20))]
                    data["obstacles"][0].update(min=[min(p[k] for p in corners) for k in range(3)],
                                                max=[max(p[k] for p in corners) for k in range(3)])
                    result = self.checked(data)["finishes"][0]
                    self.assertEqual((10000, 9600), (result["panel"]["area"], result["timber"]["area"]))
                    count += 1
        self.assertEqual(48, count, "PF5_ALL_24_RH_FRAMES_TIMES_2_SIDES")

    def test_integer_mm_scans_depth_plan_position_and_junction_gap(self):
        count = 0
        for axis, start, stop in [(0, -21, 101), (1, -61, 101), (2, 2440, 2520)]:
            for position in range(start, stop + 1):
                data = example()
                size = data["obstacles"][0]["max"][axis] - data["obstacles"][0]["min"][axis]
                data["obstacles"][0]["min"][axis] = position
                data["obstacles"][0]["max"][axis] = position + size
                self.checked(data)
                count += 1
        for gap in range(-10, 11):
            data = example()
            data["obstacles"] = []
            data["finishes"] = [face(origin=(0, 0, 0), obstacles=[]),
                                face(2, origin=(100+gap, 0, 0), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0), obstacles=[])]
            junction = self.checked(data)["junctions"][0]
            self.assertEqual(max(0, gap), junction["minimumL1Gap"], "PF5_ONE_MM_JUNCTION_SCAN")
            count += 1
        self.assertEqual(388, count, "PF5_ONE_MM_SCAN_CASE_COUNT")

    def test_independent_checker_rejects_corrupt_outputs(self):
        data = example()
        valid = ORACLE.solve(data)
        mutations = [
            ("DROP_COMPONENT", lambda r: r["finishes"][0]["host"]["region"].update(components=[])),
            ("WRONG_HOST_BACK", lambda r: r["finishes"][0]["host"]["frame"]["origin"].__setitem__(2, 2488)),
            ("COMBINE_LAYERS", lambda r: r["finishes"][0].__setitem__("panel", copy.deepcopy(r["finishes"][0]["timber"]))),
            ("INVENTED_FACE", lambda r: r["finishes"].append(copy.deepcopy(r["finishes"][0]))),
            ("MISSING_OBSTACLE_DIAGNOSTIC", lambda r: r["finishes"][0].update(obstacles=[])),
            ("FALSE_AREA", lambda r: r["finishes"][0]["timber"].update(area=10000)),
            ("CLOCKWISE_OUTER", lambda r: r["finishes"][0]["host"]["region"]["components"][0]["outer"].reverse()),
            ("COUNTERCLOCKWISE_HOLE", lambda r: r["finishes"][0]["host"]["region"]["components"][0]["holes"][0].reverse()),
            ("UNKNOWN_COMPLETENESS_CLAIM", lambda r: r.update(complete=True)),
            ("BOOL_GEOMETRY", lambda r: r["finishes"][0]["host"]["frame"]["u"].__setitem__(0, True)),
            ("JUNCTIONS_NOT_LIST", lambda r: r.update(junctions={})),
        ]
        for name, mutate in mutations:
            candidate = copy.deepcopy(valid)
            mutate(candidate)
            self.assertTrue(CHECKER.check(data, candidate), "PF5_CHECKER_MUST_REJECT_" + name)

    def test_checker_independently_rejects_left_handed_source_even_if_output_agrees(self):
        data = example()
        data["finishes"][0]["obstacles"] = []
        candidate = ORACLE.solve(data)
        data["finishes"][0]["frame"]["n"] = [0, 0, -1]
        candidate["finishes"][0]["frame"]["n"] = [0, 0, -1]
        candidate["finishes"][0]["host"]["frame"].update(origin=[0, 0, 2471], n=[0, 0, -1])
        self.assertTrue(CHECKER.check(data, candidate), "PF5_CHECKER_D2_NOT_SELF_CONFIRMING")

    def test_checker_rejects_unknown_joint_policies_and_missing_relationships(self):
        data = six_faces()
        valid = ORACLE.solve(data)
        for name, mutate in [
            ("AUTO_TRIM_POLICY", lambda r: r["junctions"][0].update(joinPolicy="ceiling-over-wall")),
            ("MISSING_JUNCTION", lambda r: r["junctions"].pop()),
            ("FALSE_VOLUME", lambda r: r["junctions"][0]["layers"]["panel-panel"].update(volume=1)),
            ("FALSE_SHARED_EDGE", lambda r: r["junctions"][1].update(sharedEdges=[])),
            ("UNAUTHORIZED_AUTO_TRIM", lambda r: r["junctions"][1].update(autoTrimApplied=True)),
            ("UNAUTHORIZED_LOAD_BEARING_CLAIM", lambda r: r["junctions"][1].update(loadBearingPassed=True)),
            ("BOOL_FLOAT_PAIR_ID", lambda r: r["junctions"][0].update(finishes=[True, 2.0])),
            ("SHARED_EDGES_NOT_LIST", lambda r: r["junctions"][0].update(sharedEdges={})),
        ]:
            candidate = copy.deepcopy(valid)
            mutate(candidate)
            self.assertTrue(CHECKER.check(data, candidate), "PF5_CHECKER_MUST_REJECT_" + name)

    def test_constructor_and_checker_independently_reject_invalid_raw_inputs(self):
        original = example()
        original["finishes"][0]["obstacles"] = []
        output = ORACLE.solve(original)
        mutations = [
            ("ROOM_REVERSED", lambda d: d["room"].update(max=[0, 100, 3000])),
            ("ROOM_FLOAT", lambda d: d["room"]["min"].__setitem__(0, 0.0)),
            ("UNUSED_OBSTACLE_ZERO_EXTENT", lambda d: d["obstacles"][0]["max"].__setitem__(0, 40)),
            ("UNUSED_OBSTACLE_BAD_REF", lambda d: d["obstacles"][0].update(ref="beam20")),
            ("UNUSED_OBSTACLE_ID_OVERFLOW", lambda d: d["obstacles"][0].update(ref="b4294967296")),
            ("UNUSED_OBSTACLE_D1_OVERFLOW", lambda d: d["obstacles"][0]["max"].__setitem__(0, 100_000_001)),
            ("FINISH_BOOL_ID", lambda d: d["finishes"][0].update(id=True)),
            ("SIDE_BOOL", lambda d: d["finishes"][0].update(side=True)),
            ("SECTION_EXTRA_DIMENSION", lambda d: d["finishes"][0]["section"].append(1)),
            ("FRAME_NONUNIT", lambda d: d["finishes"][0]["frame"].update(u=[2, 0, 0])),
            ("ORIGIN_D1_OVERFLOW", lambda d: d["finishes"][0]["frame"]["origin"].__setitem__(2, 100_000_001)),
            ("UNKNOWN_INPUT_POLICY", lambda d: d["finishes"][0].update(joinPolicy="ceiling-over-wall")),
        ]
        for name, mutation in mutations:
            with self.subTest(name=name):
                data = copy.deepcopy(original)
                mutation(data)
                with self.assertRaises(ValueError, msg="PF5_CONSTRUCTOR_INVALID_" + name):
                    ORACLE.solve(data)
                self.assertTrue(CHECKER.check(data, output), "PF5_CHECKER_INVALID_" + name)


if __name__ == "__main__":
    unittest.main()
