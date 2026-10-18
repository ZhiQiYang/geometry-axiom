"""Independent literal oracle for approved source subdivision (#58/#59).

The fixture was written from the six approved behaviors, D19/D29/D30 and Q36's
published examples before reading the new evaluator. Production assertions must
compare against its literal coordinates; the arithmetic checks below only catch
transcription mistakes in the fixed vectors. They never call a native evaluator.

No branch discarded by undo is given permanent identity guarantees here. Query
budgets, DSL spellings and diagnostic codes were frozen by the native owner;
native contract assertions compare the public API to the fixed literal vectors.
"""
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest


FIXTURE = Path(__file__).parent / "fixtures" / "grid_subdivision_vectors.json"
VECTORS = json.loads(FIXTURE.read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in VECTORS["numerical_cases"]}
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402
from tests.test_grid_system_contract import rejection_reason  # noqa: E402


class IndependentSubdivisionVectors(unittest.TestCase):
    def test_unsupported_model_adapter_cannot_hide_subdivision_capability(self):
        sys.path.insert(0, str(ROOT / "geometry-core"))
        from modeling import ModelError
        from modeling.base import load_base
        from modeling.common import scene_required_capabilities
        from unittest import mock
        for scene in (
                "requires grid-subdivision-rules/1\n",
                "grid-source-rule 0 key 1 name-hex 72 selector all-cells divide 3 2\n",
                "grid-source-rule-highwater 0 next 2\n",
                "guide 1 1 v gridrule:10:0:1:0:0:u:0\n",
                "place 1 on 1 at-line rule 10 0 1 0 0 u 0 +v +n\n"):
            with self.subTest(scene=scene), mock.patch("modeling.base.subprocess.run") as execute:
                self.assertIn("grid-subdivision-rules/1", scene_required_capabilities(scene))
                with self.assertRaises(ModelError) as caught:
                    load_base(scene, executable="must-not-execute")
                self.assertEqual("CAPABILITY", caught.exception.code)
                execute.assert_not_called()
        self.assertEqual(set(), scene_required_capabilities("# gridrule:10:0:1:0:0:u:0\n"))

    def test_fixed_fixture_schema_and_unique_case_ids(self):
        self.assertEqual("grid-subdivision-numerical-oracle/1", VECTORS["schema"])
        self.assertEqual(16, len(CASES))
        self.assertEqual(len(VECTORS["numerical_cases"]), len(CASES))
        negative_ids = [case["id"] for case in VECTORS["negative_cases"]]
        self.assertEqual(len(set(negative_ids)), len(negative_ids))

    def test_literal_lines_are_internal_exact_and_ordered(self):
        for case in CASES.values():
            with self.subTest(case=case["id"]):
                self.assertNotEqual([1, 1], case["divisions"])
                for position, axis in enumerate(("u", "v")):
                    lo, hi = case["bounds"][axis]
                    count = case["divisions"][position]
                    self.assertEqual(case["pitch"][position], hi - lo)
                    self.assertEqual(0, (hi - lo) % count)
                    self.assertTrue(1 <= count <= 65)
                    lines = case["coordinates"][axis]
                    self.assertEqual(count - 1, len(lines))
                    # No application code supplies any value on either side.
                    self.assertEqual([Fraction(hi - lo, count)] * count,
                                     [b - a for a, b in zip([lo] + lines, lines + [hi])])

    def test_repeat_source_negative_cell_and_anchored_values_are_distinct(self):
        self.assertEqual({"u": [-1000, -800], "v": [600]}, CASES["repeat-negative-cell"]["coordinates"])
        self.assertEqual({"u": [300, 500], "v": [400]}, CASES["binding-left-top"]["coordinates"])
        self.assertEqual({"u": [-1500, -1200], "v": [600]}, CASES["repeat-changed-source-pitch"]["coordinates"])
        self.assertEqual({"u": [400, 700], "v": [400]}, CASES["binding-left-top-changed-pitch"]["coordinates"])
        self.assertEqual({"u": [0, 200], "v": [200]}, CASES["binding-center"]["coordinates"])
        self.assertEqual({"u": [-50, 250], "v": [200]}, CASES["binding-center-changed-pitch"]["coordinates"])

    def test_binding_relative_arithmetic_never_needs_huge_source_coordinates(self):
        for case in CASES.values():
            if case["target"] != "binding":
                continue
            with self.subTest(case=case["id"]):
                for position, axis in enumerate(("u", "v")):
                    fraction = Fraction(*case["anchor"][2 * position:2 * position + 2])
                    cell_delta = int(case["cell"][position]) - int(case["anchor_cell"][position])
                    self.assertEqual(case["bounds"][axis][0],
                                     case["vertex"][position] + (cell_delta - fraction) * case["pitch"][position])

    def test_repeat_pitch917_divides_exactly_into_seven(self):
        self.assertEqual(131, Fraction(917, 7))
        self.assertEqual([916, 1833], CASES["repeat-pitch917-origin"]["bounds"]["u"])
        self.assertEqual([1047, 1178, 1309, 1440, 1571, 1702],
                         CASES["repeat-pitch917-origin"]["coordinates"]["u"])
        self.assertEqual([130, 261, 392, 523, 654, 785],
                         CASES["repeat-pitch917-negative-cell"]["coordinates"]["u"])
        self.assertEqual([], CASES["repeat-pitch917-binding"]["coordinates"]["v"])

    def test_signed_cells_are_exact_decimal_strings_with_representable_upper_neighbor(self):
        for case in CASES.values():
            with self.subTest(case=case["id"]):
                for field in ("cell", "anchor_cell"):
                    for coordinate in case.get(field, []):
                        self.assertIsInstance(coordinate, str)
                        self.assertEqual(str(int(coordinate)), coordinate)
                        self.assertTrue(-(2 ** 63) <= int(coordinate) < 2 ** 63 - 1)
        positive = CASES["signed-positive-beyond-double"]["cell"]
        self.assertEqual(["9007199254740993", "-9007199254740995"], positive)
        self.assertNotEqual(int(positive[0]), int(float(positive[0])))
        self.assertEqual(["9007199254740994", "-9007199254740996"],
                         CASES["signed-adjacent-beyond-double"]["cell"])

    def test_non_integral_case_has_exact_nonzero_remainder(self):
        negative = next(case for case in VECTORS["negative_cases"]
                        if case["id"] == "600-not-divisible-by-7")
        arithmetic = negative["arithmetic"]
        self.assertEqual((85, 5), divmod(arithmetic["span"], arithmetic["divisor"]))
        self.assertEqual(arithmetic["span"],
                         arithmetic["quotient"] * arithmetic["divisor"] + arithmetic["remainder"])
        self.assertNotEqual(0, arithmetic["remainder"])

    def test_literal_segments_end_on_parent_cell_edges(self):
        for case in CASES.values():
            for axis, lines in case.get("segments", {}).items():
                with self.subTest(case=case["id"], axis=axis):
                    other = "v" if axis == "u" else "u"
                    along = 1 if axis == "u" else 0
                    for coordinate, endpoints in zip(case["coordinates"][axis], lines):
                        self.assertEqual(case["bounds"][other], [point[along] for point in endpoints])
                        self.assertEqual([coordinate, coordinate], [point[1 - along] for point in endpoints])


class NativeSubdivisionOracle(unittest.TestCase):
    """Black-box production acceptance; all numerical expectations are literals.

    This class shares only the repository's fresh-binary transport and existing
    rejection reason extraction. It reads no new evaluator or internal structs.
    """
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()

    def setUp(self):
        self.session = _bridge.BridgeSession(self.bridge)
        self.addCleanup(self.session.stop)
        self.directory = tempfile.TemporaryDirectory(prefix="grid-rule-oracle-")
        self.addCleanup(self.directory.cleanup)
        self.commit("reset")

    def command(self, command):
        return self.session.command(command)

    def line(self, command):
        return self.command("line " + command)

    def commit(self, command):
        result = self.line(command)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], (command, result))
            result = self.line("confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], (command, result))
        return result

    def dump(self):
        result = self.command("dump")
        self.assertTrue(result["ok"], result)
        return result["text"]

    def snapshot(self):
        return self.dump(), self.command("objects"), self.command("references")

    def preview(self, command, valid=True):
        before = self.snapshot()
        result = self.line(command)
        self.assertIn("preview", result, (command, result))
        self.assertEqual(valid, result["preview"]["valid"], (command, result))
        self.assertEqual(before, self.snapshot(), "preview changed the live World")
        return result["preview"]

    def reject(self, command, reason):
        before = self.snapshot()
        result = self.line(command)
        self.assertFalse(result.get("ok") and result.get("preview", {}).get("valid", True), (command, result))
        if "preview" in result:
            self.assertFalse(result["preview"]["valid"], result)
            self.assertFalse(self.line("confirm " + str(result["preview"]["token"]))["ok"])
        self.assertEqual(before, self.snapshot(), command)
        self.assertIn(reason.lower(), rejection_reason(result).lower(),
                      "a syntax error or unrelated refusal is not a passing guard")
        return result

    @staticmethod
    def source(identifier=0, u="repeat 0 600", v="repeat 0 400", main="none"):
        return (f"grid-system {identifier} name-hex {('oracle ' + str(identifier)).encode().hex()} "
                f"main-along {main} u {u} v {v}")

    @staticmethod
    def rule(identifier=0, key=None, selector="all-cells", divisions=(3, 2), name="oracle rule"):
        intent = "create" if key is None else f"key {key}"
        return (f"grid-source-rule {identifier} {intent} name-hex {name.encode().hex()} "
                f"selector {selector} divide {divisions[0]} {divisions[1]}")

    def owner(self, identifier=0):
        return next(row for row in self.command("objects")["gridSystems"] if row["id"] == identifier)

    def boundary(self, identifier=1, outline="100,200 2100,200 2100,1800 100,1800"):
        self.commit(f"boundary {identifier} outline {outline}")

    def binding(self, identifier=0, boundary=1, source=0, cell=("-2", "1"), anchor=(0, 1, 0, 1)):
        geometry = self.command(f"boundary {boundary}")
        self.assertTrue(geometry["ok"], geometry)
        self.commit(f"grid-binding {identifier} on-boundary {boundary} from-system {source} "
                    f"vertex outer 0 geometry-hash {geometry['geometryFingerprint']} "
                    f"cell {' '.join(map(str, cell))} anchor {' '.join(map(str, anchor))}")

    def apply_grid(self, identifier=10, surface=1, binding=0):
        self.commit(f"placement {surface} on boundary {surface} origin 0 0 0 u +x v +y")
        self.commit(f"grid {identifier} on {surface} from-binding {binding}")

    def query(self, kind="system", identifier=0, key=1, cell=("0", "0")):
        before = self.snapshot()
        result = self.command(f"grid-rule-query {kind} {identifier} rule {key} cell {' '.join(map(str, cell))}")
        self.assertEqual(before, self.snapshot(), "readonly query mutated definitions or resolved references")
        return result

    def rect_query(self, rect, mode="exact", limit=1024, kind="system", identifier=0, key=1):
        before = self.snapshot()
        result = self.command(f"grid-rule-query {kind} {identifier} rule {key} "
                              f"rect {' '.join(map(str, rect))} mode {mode} limit {limit}")
        self.assertEqual(before, self.snapshot(), "rectangle query changed the live World")
        return result

    def assert_case(self, result, case, placed=None):
        self.assertTrue(result["ok"], (case["id"], result))
        self.assertEqual(0, result["systemId"])
        self.assertEqual(1, result["ruleKey"])
        self.assertEqual(case["cell"], result["cell"])
        self.assertTrue(all(isinstance(value, str) for value in result["cell"]))
        self.assertEqual([case["bounds"]["u"][0], case["bounds"]["v"][0],
                          case["bounds"]["u"][1], case["bounds"]["v"][1]], result["bounds"])
        self.assertEqual(sum(case["divisions"]) - 2, len(result["lines"]),
                         "the complete line descriptors cannot include a hidden extra axis")
        for axis in ("u", "v"):
            rows = sorted((row for row in result["lines"] if row["axis"] == axis),
                          key=lambda row: row["innerIndex"])
            self.assertEqual(list(range(case["divisions"][0 if axis == "u" else 1] - 1)),
                             [row["innerIndex"] for row in rows], "missing or duplicate line identity")
            self.assertEqual(case["coordinates"][axis], [row["coordinate"] for row in rows])
            for row in rows:
                if placed is None:
                    self.assertIsNone(row["ref"], "unplaced queries cannot invent a placed reference")
                else:
                    self.assertEqual({"kind": "grid-rule-line", "appliedGridId": placed,
                                      "systemId": 0, "ruleKey": 1, "cellI": case["cell"][0],
                                      "cellJ": case["cell"][1], "axis": axis,
                                      "innerIndex": row["innerIndex"]}, row["ref"])
            if axis in case.get("segments", {}):
                # Segment direction is observationally irrelevant; line identity
                # and the complete multiset of endpoints must still match.
                normalized = lambda segments: sorted(tuple(sorted(map(tuple, segment))) for segment in segments)
                self.assertEqual([normalized([segment]) for segment in case["segments"][axis]],
                                 [normalized(row["segments"]) for row in rows])

    def test_literal_source_and_binding_numerical_vectors(self):
        for case in CASES.values():
            with self.subTest(case=case["id"]):
                self.commit("reset")
                self.commit(self.source(u=case["axes"]["u"], v=case["axes"]["v"]))
                self.commit(self.rule(divisions=case["divisions"]))
                if case["target"] == "binding":
                    self.boundary()
                    self.binding(cell=case["anchor_cell"], anchor=case["anchor"])
                self.assert_case(self.query(kind=case["target"], cell=case["cell"]), case)
                if case.get("source_coordinate_query"):
                    source_query = self.query(kind="system", cell=case["cell"])
                    self.assertFalse(source_query["ok"], source_query)
                    self.assertNotIn("unknown command", rejection_reason(source_query).lower())
                    self.assertRegex(rejection_reason(source_query).lower(),
                                     r"precision|domain|range|exceed|overflow|d1",
                                     "huge source coordinates must fail for arithmetic or geometry limits")
                self.assertEqual(1, len(self.owner()["rules"]))
                self.assertEqual([], self.command("references")["grids"],
                                 "all-cells queries must not instantiate stored child grids")

    def test_placed_reference_records_real_applied_grid_and_exact_signed_identity(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary()
        self.binding(cell=("9007199254740993", "-9007199254740995"))
        self.apply_grid()
        case = CASES["signed-positive-beyond-double"]
        self.assert_case(self.query("grid", 10, cell=case["cell"]), case, placed=10)
        self.commit("guide 1 1 v gridrule:10:0:1:9007199254740993:-9007199254740995:u:0")
        guide = next(row for row in self.command("references")["guides"] if row["id"] == 1)
        self.assertEqual(300, guide["off"])
        self.assertIn("gridrule:10:0:1:9007199254740993:-9007199254740995:u:0", self.dump())
        self.roundtrip()

    def roundtrip(self):
        before = self.snapshot()
        path = Path(self.directory.name) / "subdivision.scene"
        path.write_text(before[0], encoding="utf-8")
        result = self.command("loadfile " + str(path))
        self.assertTrue(result["ok"], result)
        self.assertEqual(before, self.snapshot(), "canonical closure lost definitions or references")

    def test_cancel_create_key_lifecycle_and_complete_undo_redo(self):
        self.commit(self.source())
        before = self.snapshot()
        self.assertEqual(1, self.owner()["nextRuleKey"])
        preview = self.preview(self.rule())
        self.commit("cancel-preview")
        self.assertEqual(before, self.snapshot())
        stale = self.line("confirm " + str(preview["token"]))
        self.assertFalse(stale["ok"], stale)
        self.assertEqual(1, self.owner()["nextRuleKey"])
        self.commit(self.rule())
        after = self.snapshot()
        self.assertEqual(1, self.owner()["rules"][0]["ruleKey"])
        self.assertEqual(2, self.owner()["nextRuleKey"])
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.commit("redo")
        self.assertEqual(after, self.snapshot())
        self.commit("grid-source-rule 0 delete 1")
        self.assertEqual([], self.owner()["rules"])
        self.assertEqual(2, self.owner()["nextRuleKey"])
        self.commit(self.rule())
        self.assertEqual(2, self.owner()["rules"][0]["ruleKey"])
        self.assertEqual(3, self.owner()["nextRuleKey"])
        self.assertIn("grid-source-rule-highwater 0 next 3", self.dump())
        self.roundtrip()

    def test_query_success_and_failure_preserve_a_valid_pending_confirmation(self):
        self.commit(self.source())
        self.commit(self.rule())
        preview = self.preview(self.rule(key=1, name="renamed rule"))
        self.assert_case(self.query(), CASES["repeat-origin"])
        result = self.query(cell=("9223372036854775807", "0"))
        self.assertFalse(result["ok"], result)
        self.assertIn("cell", rejection_reason(result).lower())
        self.commit("confirm " + str(preview["token"]))
        rule = self.owner()["rules"][0]
        self.assertEqual(1, rule["ruleKey"])
        self.assertEqual("renamed rule", rule["name"])

    def test_full_source_edit_retains_rules_and_updates_both_anchored_bindings(self):
        self.commit(self.source())
        self.commit(self.rule())
        for boundary, binding, anchor in ((1, 0, (0, 1, 0, 1)), (2, 1, (1, 2, 1, 2))):
            self.boundary(boundary)
            self.binding(binding, boundary=boundary, anchor=anchor)
        self.assert_case(self.query("binding", 0, cell=("-2", "1")), CASES["binding-left-top"])
        self.assert_case(self.query("binding", 1, cell=("-2", "1")), CASES["binding-center"])
        before = self.snapshot()
        preview = self.preview(self.source(u="repeat 0 900"))
        self.assertEqual({0, 1}, {row["id"] for row in preview["gridBindings"]})
        self.commit("confirm " + str(preview["token"]))
        self.assert_case(self.query("binding", 0, cell=("-2", "1")), CASES["binding-left-top-changed-pitch"])
        self.assert_case(self.query("binding", 1, cell=("-2", "1")), CASES["binding-center-changed-pitch"])
        self.assertEqual(1, self.owner()["rules"][0]["ruleKey"])
        after = self.snapshot()
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.commit("redo")
        self.assertEqual(after, self.snapshot())

    def test_invalid_divisions_source_and_cell_guards_refuse_without_partial_state(self):
        for divisions, reason in (((7, 2), "DIVISION_NOT_EXACT"), ((1, 1), "DIVISION_RANGE"),
                                  ((0, 2), "DIVISION_RANGE"), ((66, 2), "DIVISION_RANGE"),
                                  (("3/2", 2), "RULE_SYNTAX")):
            with self.subTest(divisions=divisions):
                self.commit("reset")
                self.commit(self.source())
                self.reject(self.rule(divisions=divisions), reason)
        for u, v in (("repeat 0 600", "none"), ("explicit 0 600", "explicit 0 400"),
                     ("repeat 0 600 stagger 100", "repeat 0 400")):
            with self.subTest(u=u, v=v):
                self.commit("reset")
                self.commit(self.source(u=u, v=v))
                self.reject(self.rule(), "SOURCE_KIND")
        self.commit("reset")
        self.commit(self.source())
        self.reject(self.rule(selector="cell 9223372036854775807 0"), "CELL_RANGE")
        self.reject(self.rule(selector="cell -9223372036854775809 0"), "CELL_RANGE")

    def test_source_rules_require_dual_repeat_while_ordinary_panel_sources_remain_supported(self):
        cases = [case for case in VECTORS["negative_cases"]
                 if case["id"].startswith("panel-") and case["id"].endswith("source-rule-rejected")]
        self.assertEqual(3, len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.commit("reset")
                self.commit(self.source(u=case["axes"]["u"], v=case["axes"]["v"]))
                ordinary = self.command("grid-query system 0 rect 0 0 2000 2000 mode exact limit 64")
                self.assertTrue(ordinary["ok"], ordinary)
                for axis in ("u", "v"):
                    expected = [916, 1833] if "repeat-panel" in case["axes"][axis] else [0, 917, 1834]
                    self.assertEqual(expected, [line["coordinate"] for line in ordinary["axes"][axis]["lines"]])
                self.boundary(outline="0,0 2500,0 2500,2500 0,2500")
                self.binding(cell=("0", "0"))
                self.apply_grid()
                bound = self.command("grid-query binding 0 rect 0 0 2000 2000 mode exact limit 64")
                self.assertTrue(bound["ok"], bound)
                for axis in ("u", "v"):
                    self.assertEqual([0, 917, 1834],
                                     [line["coordinate"] for line in bound["axes"][axis]["lines"]])
                # 917 / 7 is exactly 131: this must be a kind refusal, not an
                # incidental divisibility refusal on an otherwise legal panel.
                self.assertTrue(all(917 % n == 0 for n in case["divisions"]))
                self.reject(self.rule(divisions=case["divisions"]), case["reason"])
                self.assertEqual([], self.owner()["rules"])
                self.roundtrip()

        self.commit("reset")
        self.commit(self.source(u="repeat 0 917", v="repeat 0 917"))
        self.commit(self.rule(divisions=(7, 7)))
        self.boundary(outline="0,0 2500,0 2500,2500 0,2500")
        self.binding(cell=("0", "0"))
        self.apply_grid()
        self.commit("guide 9 1 v gridrule:10:0:1:0:0:u:0")
        for case in cases:
            with self.subTest(source_edit=case["id"]):
                self.reject(self.source(u=case["axes"]["u"], v=case["axes"]["v"]), "SOURCE_KIND")
        before = self.snapshot()
        pending = self.preview(self.rule(key=1, divisions=(7, 7), name="pending panel guard"))
        path = Path(self.directory.name) / "panel-source-with-rule.scene"
        path.write_text(before[0].replace("u repeat 0 917", "u repeat-panel 915 gap 2 from 0"),
                        encoding="utf-8")
        restored = self.command("loadfile " + str(path))
        self.assertFalse(restored["ok"], restored)
        self.assertIn("SOURCE_KIND", rejection_reason(restored))
        self.assertEqual(before, self.snapshot(), "rejected panel-rule restoration changed the complete World")
        self.commit("confirm " + str(pending["token"]))
        self.commit("undo")
        self.assertEqual(before, self.snapshot(), "panel-rule refusal changed revision, pending state or history")

    def test_single_cell_and_all_cells_overlap_rules_are_explicit(self):
        self.commit(self.source())
        self.commit(self.rule(selector="cell -2 1"))
        rule = self.owner()["rules"][0]
        self.assertEqual({"kind": "cell", "cell": ["-2", "1"]}, rule["selector"])
        self.assertEqual([3, 2], rule["divisions"])
        self.assert_case(self.query(cell=("-2", "1")), CASES["repeat-negative-cell"])
        mismatch = self.query(cell=("-1", "1"))
        self.assertFalse(mismatch["ok"], mismatch)
        self.assertIn("SELECTOR_MISS", rejection_reason(mismatch))
        self.reject(self.rule(selector="cell -2 1"), "RULE_OVERLAP")
        self.reject(self.rule(), "RULE_OVERLAP")
        self.commit(self.rule(selector="cell -1 1"))
        self.assertEqual([1, 2], [rule["ruleKey"] for rule in self.owner()["rules"]])
        self.commit("reset")
        self.commit(self.source())
        self.commit(self.rule())
        self.reject(self.rule(selector="cell -2 1"), "RULE_OVERLAP")

    def test_formal_guide_reference_locks_divisions_selector_and_delete(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary()
        self.binding()
        self.apply_grid()
        self.commit("guide 1 1 v gridrule:10:0:1:-2:1:u:0")
        self.reject(self.rule(key=1, divisions=(6, 2)), "RULE_REFERENCED")
        self.reject(self.rule(key=1, selector="cell -2 1"), "RULE_REFERENCED")
        self.reject("grid-source-rule 0 delete 1", "RULE_REFERENCED")
        self.commit(self.rule(key=1, name="new label"))
        self.assertEqual(300, self.command("references")["guides"][0]["off"])
        self.assertEqual(1, self.owner()["rules"][0]["ruleKey"])

    def test_explicit_edit_cannot_create_or_resurrect_a_key_and_highwater_is_replay_only(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.reject(self.rule(key=2, selector="cell 0 0"), "RULE_MISSING")
        self.reject("grid-source-rule-highwater 0 next 99", "HIGHWATER")
        self.commit("grid-source-rule 0 delete 1")
        self.reject(self.rule(key=1), "RULE_MISSING")
        self.assertEqual(2, self.owner()["nextRuleKey"])

    def test_missing_rule_and_out_of_range_inner_index_never_choose_nearby_lines(self):
        self.commit(self.source())
        self.commit(self.rule())
        missing = self.query(key=2)
        self.assertFalse(missing["ok"], missing)
        self.assertIn("RULE_MISSING", rejection_reason(missing))
        self.boundary()
        self.binding()
        self.apply_grid()
        self.commit("timber 9 20 20 role primary")
        self.reject("place 9 on 1 at-line rule 10 0 1 -2 1 u 2 +v +n", "INDEX_RANGE")
        self.reject("place 9 on 1 at-line rule 10 0 2 -2 1 u 0 +v +n", "RULE_MISSING")

    def test_rule_and_manual_conflicts_reject_in_both_creation_orders(self):
        self.commit(self.source())
        self.boundary()
        self.binding()
        self.apply_grid()
        self.commit("subgrid 11 parent 10 lattice-cell -2 1 divisions u 2 v 2")
        self.reject(self.rule(selector="cell -2 1"), "MANUAL_CONFLICT")
        self.reject(self.rule(), "MANUAL_CONFLICT")
        self.commit("delete grid 11")
        self.commit(self.rule(selector="cell -2 1"))
        self.reject("subgrid 11 parent 10 lattice-cell -2 1 divisions u 2 v 2", "MANUAL_CONFLICT")
        self.commit("subgrid 11 parent 10 lattice-cell -1 1 divisions u 2 v 2")

    def test_same_rule_key_in_another_source_cannot_rebind_an_existing_reference(self):
        for identifier in (0, 1):
            self.commit(self.source(identifier))
            self.commit(self.rule(identifier))
        self.boundary()
        self.binding()
        self.apply_grid()
        self.commit("guide 1 1 v gridrule:10:0:1:-2:1:u:0")
        geometry = self.command("boundary 1")
        self.reject("grid-binding 0 on-boundary 1 from-system 1 vertex outer 0 geometry-hash "
                    + geometry["geometryFingerprint"] + " cell -2 1 anchor 0 1 0 1", "WRONG_SOURCE")

    def test_hole_clipping_preserves_line_identity_and_all_visible_segments(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary(outline="100,200 2100,200 2100,1800 100,1800 hole 250,250 350,250 350,550 250,550")
        self.binding()
        result = self.query("binding", cell=("-2", "1"))
        self.assertTrue(result["ok"], result)
        by_line = {(row["axis"], row["innerIndex"]): row for row in result["lines"]}
        expected = {("u", 0): (300, [[[300, 200], [300, 250]], [[300, 550], [300, 600]]]),
                    ("u", 1): (500, [[[500, 200], [500, 600]]]),
                    ("v", 0): (400, [[[100, 400], [250, 400]], [[350, 400], [700, 400]]])}
        self.assertEqual(set(expected), set(by_line))
        normalized = lambda segments: sorted(tuple(sorted(map(tuple, segment))) for segment in segments)
        for identity, (coordinate, segments) in expected.items():
            self.assertEqual(coordinate, by_line[identity]["coordinate"])
            self.assertEqual(normalized(segments), normalized(by_line[identity]["segments"]))

    def test_legal_comb_holes_preserve_all_41_visible_segments_across_queries_and_guides(self):
        # Five disjoint legal holes, each with 32 literal vertices and eight
        # teeth. The u=500 line crosses 40 removed intervals, so its complete
        # visible geometry consists of the 41 literal endpoint pairs below.
        # This fixture exposed a former shared 32-segment truncation; neither
        # a clipped subset nor complete=true on that subset is acceptable.
        fixture = VECTORS["complex_clipping_fixture"]
        self.assertEqual(16, len(CASES), "complex clipping does not redefine the numerical vector catalog")
        self.assertEqual([32] * 5, [len(hole) for hole in fixture["holes"]])
        points = lambda ring: " ".join(f"{u},{v}" for u, v in ring)
        outline = points(fixture["outer"]) + "".join(" hole " + points(hole) for hole in fixture["holes"])
        self.boundary(outline=outline)
        geometry = self.command("boundary 1")
        self.assertTrue(geometry["ok"], geometry)
        self.assertEqual([4, 32, 32, 32, 32, 32], [len(loop["verts"]) for loop in geometry["loops"]])
        self.commit(self.source(u="repeat 0 1000", v="repeat 0 2000"))
        self.commit(self.rule(divisions=(2, 1)))
        self.binding(cell=("0", "0"))
        self.apply_grid()
        self.commit("guide 9 1 v gridrule:10:0:1:0:0:u:0")
        normalize = lambda segments: sorted(tuple(sorted(map(tuple, segment))) for segment in segments)
        expected = normalize(fixture["expectedSegments"])
        self.assertEqual(41, len(expected))
        before = self.snapshot()
        pending = self.preview(self.rule(key=1, divisions=(2, 1), name="pending complete clipping"))
        for kind, identifier in (("binding", 0), ("grid", 10)):
            with self.subTest(target=kind):
                cell = self.query(kind, identifier)
                self.assertTrue(cell["ok"], cell)
                self.assertEqual(fixture["cell"], cell["cell"])
                self.assertEqual(fixture["bounds"], cell["bounds"])
                self.assertEqual(1, len(cell["lines"]))
                line = cell["lines"][0]
                self.assertEqual(("u", 0, 500), (line["axis"], line["innerIndex"], line["coordinate"]))
                self.assertEqual(expected, normalize(line["segments"]))
                for mode in ("exact", "sample"):
                    rectangle = self.rect_query((0, 0, 1000, 2000), kind=kind, identifier=identifier,
                                                mode=mode, limit=1)
                    self.assertTrue(rectangle["ok"], rectangle)
                    if mode == "exact":
                        self.assertTrue(rectangle["complete"], rectangle)
                    self.assertEqual("1", rectangle["requiredCells"])
                    self.assertEqual("1", rectangle["stride"])
                    self.assertEqual(1, len(rectangle["cells"]))
                    row = rectangle["cells"][0]
                    self.assertEqual(fixture["cell"], row["cell"])
                    self.assertEqual(1, len(row["lines"]))
                    self.assertEqual(expected, normalize(row["lines"][0]["segments"]))
        guide = next(row for row in self.command("references")["guides"] if row["id"] == 9)
        self.assertEqual(500, guide["off"])
        self.assertEqual(expected, normalize(guide["segments"]))
        self.assertEqual(before, self.snapshot(), "all clipping reads must leave the complete live World untouched")
        self.commit("confirm " + str(pending["token"]))
        self.assertEqual("pending complete clipping", self.owner()["rules"][0]["name"])
        self.commit("undo")
        self.assertEqual(before, self.snapshot(), "clipping reads must preserve pending confirmation and history")
        self.roundtrip()

    def real_supports(self, surface=1, first=1, positions=(120, 680)):
        for timber, edge in ((first + 80, "e0"), (first + 81, "e2")):
            self.commit(f"timber {timber} 20 20 role boundary")
            self.commit(f"place {timber} on {surface} at-face {edge} +u +n")
        for offset, coordinate in enumerate(positions):
            identifier = first + offset
            self.commit(f"spec support_position_{identifier} {coordinate}")
            self.commit(f"guide {identifier} {surface} v spec:support_position_{identifier}")
            self.commit(f"timber {identifier} 20 20 role primary")
            self.commit(f"place {identifier} on {surface} at-line guide {identifier} +v +n")

    def timber(self, identifier):
        return next(row for row in self.command("references")["timbers"] if row["id"] == identifier)

    def test_direct_line_needs_real_support_and_complete_cell_scope_while_guide_is_coordinate_only(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary()
        self.binding()
        self.apply_grid()
        # The queried three child lines are present. They do not provide D11
        # stops, so the existence of a neighboring child line cannot support a
        # physical primary. Its complete length has to remain inside its cell.
        self.commit("timber 9 20 20 role primary")
        self.reject("place 9 on 1 at-line rule 10 0 1 -2 1 u 0 +v +n", "I13/R6")
        self.real_supports()
        self.reject("place 9 on 1 at-line rule 10 0 1 -2 1 u 0 +v +n", "I13/R6")
        self.commit("guide 9 1 v gridrule:10:0:1:-2:1:u:0")
        self.commit("place 9 on 1 at-line guide 9 +v +n")
        self.assertEqual(300, self.timber(9)["geometry"]["centerline"])
        self.assertEqual(1560, self.timber(9)["geometry"]["length"])
        self.commit("delete timber 9")
        self.commit("delete guide 9")
        self.commit("timber 10 20 20 role secondary")
        self.commit("place 10 on 1 at-line rule 10 0 1 -2 1 v 0 between t1 t2 +u +n")
        self.assertEqual(400, self.timber(10)["geometry"]["centerline"])
        self.assertEqual(540, self.timber(10)["geometry"]["length"])
        self.assertIn("at-line rule 10 0 1 -2 1 v 0", self.dump())
        self.reject(self.rule(key=1, divisions=(6, 2)), "RULE_REFERENCED")
        self.reject(self.rule(key=1, selector="cell -2 1"), "RULE_REFERENCED")
        self.reject("grid-source-rule 0 delete 1", "RULE_REFERENCED")
        self.roundtrip()

    def test_formal_rule_line_timber_undo_redo_survives_reset_load(self):
        """D30 formal rule-line timber: undo, redo, then reset before load.

        The shared roundtrip() helper is intentionally not used. It loads
        without proving the world was cleared, so a no-op load could pass.
        """
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary()
        self.binding()
        self.apply_grid()
        self.real_supports()
        self.commit("timber 10 20 20 role secondary")
        before = self.snapshot()
        self.commit("place 10 on 1 at-line rule 10 0 1 -2 1 v 0 between t1 t2 +u +n")
        self.assertEqual(400, self.timber(10)["geometry"]["centerline"])
        self.assertEqual(540, self.timber(10)["geometry"]["length"])
        placed = self.snapshot()
        self.assertNotEqual(before, placed)
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.commit("redo")
        self.assertEqual(placed, self.snapshot())
        self.assertEqual(400, self.timber(10)["geometry"]["centerline"])
        self.assertEqual(540, self.timber(10)["geometry"]["length"])
        path = Path(self.directory.name) / "formal-rule-timber.scene"
        path.write_text(placed[0], encoding="utf-8")
        self.assertTrue(self.command("reset")["ok"])
        cleared = self.snapshot()
        self.assertNotEqual(placed, cleared)
        for key in ("faces", "spaces", "gridSystems"):
            self.assertEqual([], cleared[1][key], key)
        for key in ("guides", "grids", "timbers", "specs", "datums"):
            self.assertEqual([], cleared[2][key], key)
        self.assertNotIn("timber 10", cleared[0])
        self.assertNotIn("at-line rule", cleared[0])
        loaded = self.command("loadfile " + str(path))
        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(placed, self.snapshot())

    def test_only_second_actual_component_invalidates_complete_source_candidate(self):
        self.commit(self.source())
        self.commit(self.rule())
        for surface, binding, grid, first, stops in ((1, 0, 10, 1, (120, 380)),
                                                   (2, 1, 20, 21, (120, 680))):
            self.boundary(surface)
            self.binding(binding, boundary=surface)
            self.apply_grid(grid, surface=surface, binding=binding)
            self.real_supports(surface=surface, first=first, positions=stops)
            secondary = first + 2
            self.commit(f"timber {secondary} 20 20 role secondary")
            self.commit(f"place {secondary} on {surface} at-line rule {grid} 0 1 -2 1 v 0 "
                        f"between t{first} t{first + 1} +u +n")
        self.assertEqual(240, self.timber(3)["geometry"]["length"])
        self.assertEqual(540, self.timber(23)["geometry"]["length"])
        before = self.snapshot()
        # After U=300, first cell [100,400] still has both physical supports.
        # The second complete span [130,670] exceeds that cell's U scope. It is
        # the second placed component that prevents the source-wide commit.
        preview = self.preview(self.source(u="repeat 0 300"), valid=False)
        self.assertEqual({0, 1}, {row["id"] for row in preview["gridBindings"]})
        self.assertEqual({23}, {row["timber"] for row in preview["violations"]},
                         "only the second component is invalid, and its typed id must be identified")
        refused = self.line("confirm " + str(preview["token"]))
        self.assertFalse(refused["ok"], refused)
        self.assertEqual(before, self.snapshot())

    def test_source_cell_outside_face_remains_defined_and_manual_positive_area_guard_remains(self):
        self.commit(self.source())
        self.commit(self.rule(selector="cell 20 20"))
        self.boundary()
        self.binding()
        self.apply_grid()
        result = self.query("grid", 10, cell=("20", "20"))
        self.assertTrue(result["ok"], result)
        self.assertEqual([13300, 7800, 13900, 8200], result["bounds"])
        self.assertEqual([13500, 13700], [row["coordinate"] for row in result["lines"] if row["axis"] == "u"])
        self.assertEqual([8000], [row["coordinate"] for row in result["lines"] if row["axis"] == "v"])
        self.assertTrue(all(row["segments"] == [] for row in result["lines"]))
        self.commit("guide 1 1 v gridrule:10:0:1:20:20:u:0")
        guide = self.command("references")["guides"][0]
        self.assertEqual(13500, guide["off"])
        self.assertEqual([], guide["segments"])
        # The next cell has no source rule, so the refusal tests only the
        # existing manual positive-area guard, rather than a rule conflict.
        self.reject("subgrid 11 parent 10 lattice-cell 21 20 divisions u 3 v 2", "I25")
        self.roundtrip()

    def test_exact_rectangle_has_positive_area_cells_and_real_row_major_identity(self):
        self.commit(self.source())
        self.commit(self.rule())
        result = self.rect_query((0, 0, 1200, 800), limit=4)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["complete"], result)
        self.assertEqual("4", result["requiredCells"])
        self.assertEqual("1", result["stride"])
        self.assertEqual([["0", "0"], ["1", "0"], ["0", "1"], ["1", "1"]],
                         [row["cell"] for row in result["cells"]])
        expected = [([200, 400], [200]), ([800, 1000], [200]),
                    ([200, 400], [600]), ([800, 1000], [600])]
        for cell, (u, v) in zip(result["cells"], expected):
            self.assertEqual(u, [line["coordinate"] for line in cell["lines"] if line["axis"] == "u"])
            self.assertEqual(v, [line["coordinate"] for line in cell["lines"] if line["axis"] == "v"])
        clipped = self.rect_query((250, 100, 450, 300), limit=1)
        self.assertTrue(clipped["ok"], clipped)
        self.assertEqual("1", clipped["requiredCells"])
        by_line = {(row["axis"], row["innerIndex"]): row for row in clipped["cells"][0]["lines"]}
        self.assertEqual([], by_line[("u", 0)]["segments"])
        self.assertEqual([[[400, 100], [400, 300]]], by_line[("u", 1)]["segments"])
        self.assertEqual([[[250, 200], [450, 200]]], by_line[("v", 0)]["segments"])

    def test_rectangle_selector_filters_before_capacity_and_zero_matches_are_complete(self):
        self.commit(self.source())
        self.commit(self.rule(selector="cell 0 0"))
        result = self.rect_query((-60000, -40000, 60000, 40000), limit=1)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["complete"], result)
        self.assertEqual("1", result["requiredCells"])
        self.assertEqual([["0", "0"]], [row["cell"] for row in result["cells"]])
        miss = self.rect_query((600, 400, 1200, 800), limit=1)
        self.assertTrue(miss["ok"], miss)
        self.assertTrue(miss["complete"], miss)
        self.assertEqual("0", miss["requiredCells"])
        self.assertEqual("1", miss["stride"])
        self.assertEqual([], miss["cells"])

    def test_query_cell_capacity_one_limit_limit_plus_one_and_honest_dense_sampling(self):
        self.commit(self.source(u="repeat 0 2", v="repeat 0 2"))
        self.commit(self.rule(divisions=(2, 1)))
        for rect, limit, count in (((0, 0, 2, 2), 1, "1"), ((0, 0, 64, 64), 1024, "1024")):
            with self.subTest(rect=rect):
                result = self.rect_query(rect, limit=limit)
                self.assertTrue(result["ok"], result)
                self.assertTrue(result["complete"], result)
                self.assertEqual(count, result["requiredCells"])
                self.assertEqual(int(count), len(result["cells"]))
        preview = self.preview(self.rule(key=1, divisions=(2, 1), name="pending capacity proof"))
        rejected = self.rect_query((0, 0, 2050, 2), limit=1024)
        self.assertFalse(rejected["ok"], rejected)
        self.assertIn("QUERY_CAPACITY", rejection_reason(rejected))
        self.assertEqual("1025", rejected["requiredCells"])
        sampled = self.rect_query((0, 0, 200, 200), mode="sample", limit=64)
        self.assertTrue(sampled["ok"], sampled)
        self.assertFalse(sampled["complete"], sampled)
        self.assertEqual("10000", sampled["requiredCells"])
        stride = int(sampled["stride"])
        self.assertGreater(stride, 1)
        expected_cells = [[str(ordinal % 100), str(ordinal // 100)]
                          for ordinal in range(0, 10000, stride)]
        self.assertEqual(expected_cells, [row["cell"] for row in sampled["cells"]])
        self.assertLessEqual(len(expected_cells), 64)
        for cell in sampled["cells"]:
            self.assertEqual(1, len(cell["lines"]))
            line = cell["lines"][0]
            self.assertEqual("u", line["axis"])
            self.assertEqual(0, line["innerIndex"])
            self.assertEqual(2 * int(cell["cell"][0]) + 1, line["coordinate"])
            self.assertEqual(1, len(line["segments"]))
        self.assertEqual([], self.command("references")["grids"])
        self.commit("confirm " + str(preview["token"]))
        self.assertEqual("pending capacity proof", self.owner()["rules"][0]["name"])

    def test_segment_capacity_exact_4096_and_4224_refusal_preserves_all_sampled_lines(self):
        self.commit(self.source(u="repeat 0 650", v="repeat 0 65"))
        self.commit(self.rule(divisions=(65, 65)))
        exact = self.rect_query((0, 0, 20800, 65))
        self.assertTrue(exact["ok"], exact)
        self.assertTrue(exact["complete"], exact)
        self.assertEqual("32", exact["requiredCells"])
        self.assertEqual(4096, sum(len(line["segments"]) for cell in exact["cells"] for line in cell["lines"]))
        rejected = self.rect_query((0, 0, 21450, 65))
        self.assertFalse(rejected["ok"], rejected)
        self.assertIn("QUERY_CAPACITY", rejection_reason(rejected))
        self.assertEqual("4224", rejected["requiredSegments"])
        sampled = self.rect_query((0, 0, 21450, 65), mode="sample")
        self.assertTrue(sampled["ok"], sampled)
        self.assertFalse(sampled["complete"], sampled)
        self.assertEqual("33", sampled["requiredCells"])
        stride = int(sampled["stride"])
        self.assertGreater(stride, 1)
        self.assertEqual([[str(i), "0"] for i in range(0, 33, stride)],
                         [cell["cell"] for cell in sampled["cells"]])
        for cell in sampled["cells"]:
            self.assertEqual(128, len(cell["lines"]))
            self.assertEqual(128, sum(len(line["segments"]) for line in cell["lines"]))

    def test_single_cell_4232_segments_rejects_unthinnable_sampling_with_counts_and_bounded_termination(self):
        fixture = VECTORS["unthinnable_clipping_fixture"]
        self.assertEqual([32] * 8, [len(hole) for hole in fixture["holes"]])
        coordinates = fixture["interiorCoordinates"]
        self.assertEqual(list(range(100, 6500, 100)), coordinates)
        self.assertEqual(65, len(fixture["verticalVisibleIntervals"]))

        # Independent orthogonal intersection counting, confined to this test.
        # No native result supplies either expected count. All line positions
        # avoid hole vertices, so each pair of strict crossings removes one
        # interval from a line that starts and ends inside the outer rectangle.
        def removed_intervals(axis, coordinate):
            total = 0
            for hole in fixture["holes"]:
                crossings = sum(a[1 - axis] == b[1 - axis]
                                and min(a[axis], b[axis]) < coordinate < max(a[axis], b[axis])
                                for a, b in zip(hole, hole[1:] + hole[:1]))
                self.assertEqual(0, crossings % 2)
                total += crossings // 2
            return total

        self.assertEqual([64] * 64, [removed_intervals(0, value) for value in coordinates])
        self.assertEqual(fixture["horizontalSplitCoordinates"],
                         [value for value in coordinates if removed_intervals(1, value)])
        vertical = sum(1 + removed_intervals(0, value) for value in coordinates)
        horizontal = sum(1 + removed_intervals(1, value) for value in coordinates)
        self.assertEqual(4160, vertical)
        self.assertEqual(72, horizontal)
        self.assertEqual(fixture["expectedVerticalSegments"], vertical)
        self.assertEqual(fixture["expectedHorizontalSegments"], horizontal)
        self.assertEqual(4232, vertical + horizontal)
        self.assertEqual(fixture["expectedTotalSegments"], vertical + horizontal)
        self.assertEqual(4096, fixture["querySegmentCapacity"])
        self.assertGreater(vertical + horizontal, fixture["querySegmentCapacity"])
        points = lambda ring: " ".join(f"{u},{v}" for u, v in ring)
        outline = points(fixture["outer"]) + "".join(" hole " + points(hole) for hole in fixture["holes"])
        self.boundary(outline=outline)
        geometry = self.command("boundary 1")
        self.assertTrue(geometry["ok"], geometry)
        self.assertEqual([4] + [32] * 8, [len(loop["verts"]) for loop in geometry["loops"]])
        self.commit(self.source(u=fixture["axes"]["u"], v=fixture["axes"]["v"]))
        self.commit(self.rule(divisions=fixture["divisions"]))
        self.binding(cell=fixture["cell"])
        self.apply_grid()
        before = self.snapshot()
        pending = self.preview(self.rule(key=1, divisions=(65, 65), name="pending unthinnable query"))

        def bounded_query(command):
            results, failures = [], []

            def run():
                try:
                    results.append(self.command(command))
                except BaseException as error:
                    failures.append(error)

            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            worker.join(timeout=5)
            if worker.is_alive():
                self.session.process.kill()
                worker.join(timeout=1)
                self.fail("an indivisible over-capacity cell must terminate within five seconds: " + command)
            if failures:
                raise failures[0]
            self.assertEqual(1, len(results))
            return results[0]

        for command, required_cells in (
                ("grid-rule-query binding 0 rule 1 cell 0 0", "1"),
                ("grid-rule-query binding 0 rule 1 rect 0 0 6500 6500 mode exact limit 1", "1"),
                ("grid-rule-query binding 0 rule 1 rect 0 0 6500 6500 mode sample limit 1", "1"),
                ("grid-rule-query binding 0 rule 1 rect 0 0 13000 6500 mode sample limit 1", "2")):
            with self.subTest(query=command):
                rejected = bounded_query(command)
                self.assertFalse(rejected["ok"], rejected)
                self.assertIn("QUERY_CAPACITY", rejection_reason(rejected))
                self.assertEqual(required_cells, rejected["requiredCells"])
                self.assertEqual("4232", rejected["requiredSegments"])
                self.assertEqual(before, self.snapshot(), "capacity refusal changed definitions or resolved references")
        # A successful confirmation proves the readonly failures did not advance
        # the exact revision gate; undo also proves their history was untouched.
        self.commit("confirm " + str(pending["token"]))
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.roundtrip()

    def test_native_save_requires_capability_and_load_failures_preserve_live_world(self):
        self.commit(self.source())
        self.commit(self.rule())
        before = self.snapshot()
        self.assertIn("grid-subdivision-rules/1", before[0])
        self.assertIn("grid-source-rule 0 key 1", before[0])
        self.assertIn("grid-source-rule-highwater 0 next 2", before[0])
        self.roundtrip()
        dump = self.dump()
        fixtures = {
            "unknown-capability": dump.replace("grid-subdivision-rules/1", "grid-subdivision-rules/999"),
            "missing-capability": "\n".join(line for line in dump.splitlines() if not line.startswith("requires ")) + "\n",
            "missing-owner": "\n".join(line for line in dump.splitlines() if not line.startswith("grid-system ")) + "\n",
            "missing-highwater": "\n".join(line for line in dump.splitlines() if not line.startswith("grid-source-rule-highwater ")) + "\n",
        }
        for identifier, text in fixtures.items():
            with self.subTest(fixture=identifier):
                before = self.snapshot()
                pending = self.preview(self.rule(key=1, name="pending load " + identifier))
                path = Path(self.directory.name) / (identifier + ".scene")
                path.write_text(text, encoding="utf-8")
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertEqual(before, self.snapshot(), "failed scene replacement lost the previous World")
                reason = str(result.get("error", "")).lower()
                self.assertNotIn("unknown command", reason)
                expected_reason = ("capability" if "capability" in identifier else
                                   "wrong_source" if identifier == "missing-owner" else "rule")
                self.assertIn(expected_reason, reason)
                self.commit("confirm " + str(pending["token"]))
                self.commit("undo")
                self.assertEqual(before, self.snapshot(), "failed load damaged the existing history")

    def test_new_allocator_input_syntax_requires_capability_even_when_final_state_is_default(self):
        self.commit(self.source())
        self.commit(self.rule())
        before = self.snapshot()
        pending = self.preview(self.rule(key=1, name="pending allocator capability guard"))
        source_only = self.source() + "\ngrid-source-rule-highwater 0 next 1\n"
        path = Path(self.directory.name) / "default-highwater-without-required-capability.scene"
        path.write_text(source_only, encoding="utf-8")
        rejected = self.command("loadfile " + str(path))
        self.assertFalse(rejected["ok"], rejected)
        self.assertIn("capability", rejection_reason(rejected).lower())
        self.assertEqual(before, self.snapshot(), "missing input capability replaced the complete live World")
        self.commit("confirm " + str(pending["token"]))
        self.commit("undo")
        self.assertEqual(before, self.snapshot(), "missing input capability damaged revision, pending state or history")

        path.write_text("requires grid-subdivision-rules/1\n" + source_only, encoding="utf-8")
        accepted = self.command("loadfile " + str(path))
        self.assertTrue(accepted["ok"], accepted)
        self.assertEqual([], self.owner()["rules"])
        self.assertEqual(1, self.owner()["nextRuleKey"])
        # A redundant default highwater need not remain in canonical output;
        # the input syntax still requires its explicit capability declaration.
        self.roundtrip()

    def test_saved_rule_reference_missing_key_wrong_source_and_index_reject_atomic_load(self):
        self.commit(self.source())
        self.commit(self.rule())
        self.boundary()
        self.binding()
        self.apply_grid()
        self.commit("guide 1 1 v gridrule:10:0:1:-2:1:u:0")
        dump = self.dump()
        fixtures = {
            "missing-rule": ("\n".join(line for line in dump.splitlines()
                                        if not line.startswith("grid-source-rule 0 key 1 ")) + "\n", "RULE_MISSING"),
            "wrong-source": (dump.replace("gridrule:10:0:1:-2:1:u:0", "gridrule:10:1:1:-2:1:u:0"), "WRONG_SOURCE"),
            "wrong-inner-index": (dump.replace("gridrule:10:0:1:-2:1:u:0", "gridrule:10:0:1:-2:1:u:2"), "INDEX_RANGE"),
            "extra-reference-field": (dump.replace("gridrule:10:0:1:-2:1:u:0", "gridrule:10:0:1:-2:1:u:0:extra"), "invalid/missing reference"),
            "empty-extra-reference-field": (dump.replace("gridrule:10:0:1:-2:1:u:0", "gridrule:10:0:1:-2:1:u:0:"), "invalid/missing reference"),
        }
        for identifier, (text, reason) in fixtures.items():
            with self.subTest(fixture=identifier):
                before = self.snapshot()
                pending = self.preview(self.rule(key=1, name="pending closed reference " + identifier))
                path = Path(self.directory.name) / (identifier + ".scene")
                path.write_text(text, encoding="utf-8")
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertIn(reason, rejection_reason(result))
                self.assertEqual(before, self.snapshot())
                self.commit("confirm " + str(pending["token"]))
                self.commit("undo")
                self.assertEqual(before, self.snapshot())

    def test_highwater_replay_lifecycle_cannot_supply_a_different_or_reset_source(self):
        self.commit(self.source())
        self.commit(self.rule())
        prefix = ["requires grid-subdivision-rules/1", self.source(), self.rule(key=1),
                  "grid-source-rule-highwater 0 next 2"]
        fixtures = {
            "deleted-owner-highwater-does-not-cover-new-owner": prefix + [
                "delete grid-system 0", self.source(1), self.rule(1, key=1)],
            "reset-clears-highwater-closure": prefix + [
                "reset", "requires grid-subdivision-rules/1", self.source(1), self.rule(1, key=1)],
            "highwater-before-key": ["requires grid-subdivision-rules/1", self.source(),
                                     "grid-source-rule-highwater 0 next 2", self.rule(key=1)],
        }
        for identifier, lines in fixtures.items():
            with self.subTest(fixture=identifier):
                before = self.snapshot()
                pending = self.preview(self.rule(key=1, name="pending " + identifier))
                path = Path(self.directory.name) / (identifier + ".scene")
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                result = self.command("loadfile " + str(path))
                self.assertFalse(result["ok"], result)
                self.assertIn("highwater", rejection_reason(result).lower())
                self.assertEqual(before, self.snapshot())
                self.commit("confirm " + str(pending["token"]))
                self.commit("undo")
                self.assertEqual(before, self.snapshot())

    def test_valid_highwater_replay_follows_source_when_an_earlier_owner_is_deleted(self):
        lines = ["requires grid-subdivision-rules/1", self.source(), self.rule(key=1),
                 "grid-source-rule-highwater 0 next 2", self.source(1), self.rule(1, key=1),
                 "grid-source-rule-highwater 1 next 2", "delete grid-system 0"]
        path = Path(self.directory.name) / "shifted-owner.scene"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = self.command("loadfile " + str(path))
        self.assertTrue(result["ok"], result)
        self.assertEqual([1], [row["id"] for row in self.command("objects")["gridSystems"]])
        self.assertEqual(1, self.owner(1)["rules"][0]["ruleKey"])
        self.assertEqual(2, self.owner(1)["nextRuleKey"])
        self.roundtrip()

    def test_rule_capacity_32_and_33rd_is_a_capacity_refusal(self):
        self.commit(self.source())
        for index in range(32):
            self.commit(self.rule(selector=f"cell {index} 0"))
        self.assertEqual(list(range(1, 33)), [rule["ruleKey"] for rule in self.owner()["rules"]])
        self.assertEqual(33, self.owner()["nextRuleKey"])
        self.reject(self.rule(selector="cell 32 0"), "CAPACITY")
        self.assertEqual(32, len(self.owner()["rules"]))
        self.assertEqual(33, self.owner()["nextRuleKey"])
        self.roundtrip()

    def test_maximum_uint32_allocator_exhaustion_survives_delete_save_and_history(self):
        lines = ["requires grid-subdivision-rules/1", self.source(),
                 self.rule(key=1, selector="cell -2 1"),
                 "grid-source-rule-highwater 0 next 4294967295"]
        path = Path(self.directory.name) / "near-exhaustion.scene"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        loaded = self.command("loadfile " + str(path))
        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(4294967295, self.owner()["nextRuleKey"])
        self.commit(self.rule(selector="cell 0 0"))
        self.assertEqual([1, 4294967295], [rule["ruleKey"] for rule in self.owner()["rules"]])
        self.assertEqual(0, self.owner()["nextRuleKey"])
        self.assertIn("grid-source-rule-highwater 0 next exhausted", self.dump())
        before_delete = self.snapshot()
        self.commit("grid-source-rule 0 delete 4294967295")
        after_delete = self.snapshot()
        self.assertEqual(0, self.owner()["nextRuleKey"])
        self.reject(self.rule(selector="cell 1 0"), "EXHAUST")
        self.commit("undo")
        self.assertEqual(before_delete, self.snapshot())
        self.commit("redo")
        self.assertEqual(after_delete, self.snapshot())
        self.roundtrip()
        self.assertEqual(0, self.owner()["nextRuleKey"])
        self.reject(self.rule(selector="cell 1 0"), "EXHAUST")

    def test_native_source_inspect_tracks_rule_edges_dependencies_and_definition_changes(self):
        self.commit(self.source())
        self.commit(self.rule(divisions=(3, 4)))
        self.boundary()
        self.binding()
        self.apply_grid()
        self.real_supports()
        self.commit("guide 9 1 v gridrule:10:0:1:-2:1:u:0")
        self.commit("timber 10 20 20 role secondary")
        self.commit("place 10 on 1 at-line rule 10 0 1 -2 1 v 0 between t1 t2 +u +n")
        self.assertEqual(300, self.timber(10)["geometry"]["centerline"])
        self.assertEqual(540, self.timber(10)["geometry"]["length"])

        def inspect():
            before = self.snapshot()
            result = self.command("source-inspect")
            self.assertTrue(result["ok"], result)
            self.assertTrue(result["complete"], result)
            self.assertEqual(before, self.snapshot())
            self.assertRegex(result["sourceFingerprint"], r"^[a-f0-9]{64}$")
            for node in result["nodes"]:
                self.assertIsInstance(node["id"], str)
                self.assertRegex(node["definitionFingerprint"], r"^[a-f0-9]{64}$")
                self.assertRegex(node["valueFingerprint"], r"^[a-f0-9]{64}$")
            return result

        before = inspect()
        expected_edges = {("guide:9", "grid:10", "position", "rule-line"),
                          ("guide:9", "grid-system:0", "position", "rule-source"),
                          ("timber:10", "grid:10", "position", "rule-line"),
                          ("timber:10", "grid-system:0", "position", "rule-source")}
        self.assertTrue(expected_edges.issubset({(edge["from"], edge["to"], edge["relation"], edge["field"])
                                               for edge in before["edges"]}))
        grid = next(row for row in self.command("references")["grids"] if row["id"] == 10)
        self.assertEqual([9], grid["dependencies"]["guides"])
        self.assertEqual([10], grid["dependencies"]["timbers"])
        node = lambda result, kind, identifier: next(row for row in result["nodes"]
                                                    if row["kind"] == kind and row["id"] == str(identifier))
        original_timber = node(before, "timber", 10)
        self.commit("place 10 on 1 at-line rule 10 0 1 -2 1 v 1 between t1 t2 +u +n")
        after = inspect()
        changed_timber = node(after, "timber", 10)
        self.assertEqual(400, self.timber(10)["geometry"]["centerline"])
        self.assertEqual(540, self.timber(10)["geometry"]["length"])
        self.assertNotEqual(original_timber["definitionFingerprint"], changed_timber["definitionFingerprint"])
        self.assertNotEqual(original_timber["valueFingerprint"], changed_timber["valueFingerprint"])
        self.assertTrue(self.timber(10)["definition"]["anchor"].startswith("at-line rule 10 0 1 -2 1 v 1"))
        self.commit("delete timber 10")
        self.commit("delete guide 9")
        before_rule = inspect()
        self.commit(self.rule(key=1, divisions=(6, 4)))
        after_rule = inspect()
        self.assertNotEqual(node(before_rule, "grid-system", 0)["definitionFingerprint"],
                            node(after_rule, "grid-system", 0)["definitionFingerprint"])
        self.assertNotEqual(before_rule["sourceFingerprint"], after_rule["sourceFingerprint"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
