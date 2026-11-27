#!/usr/bin/env python3
"""Adversarial R03B checker regressions; source selection also proves v1 red.

Fixtures may use the policy-A builder.  Each assertion calls only the independent
checker after construction, so a constructor verdict cannot make an attack pass.
"""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tests/diagnostics/r03_notch_oracle.py"
SOURCE = Path(os.environ.get("R03B_CHECKER_SOURCE", CHECKER))
SPEC = importlib.util.spec_from_file_location("r03b_checker_regression", CHECKER)
CHECK = importlib.util.module_from_spec(SPEC)
# Keep the repository locator unchanged when replaying preserved source bytes.
exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), CHECK.__dict__)


def split_main(candidate, replacement="boundary"):
    value = deepcopy(candidate)
    main = next(t for t in value["timbers"] if t["kind"] == "main")
    a, b = value["a"], value["b"]
    rect = list(main["rect"])
    middle = (rect[b] + rect[b + 2]) // 2
    low, plug, high = list(rect), list(rect), list(rect)
    low[b + 2], plug[b], plug[b + 2], high[b] = middle, middle, middle + 27, middle + 27
    main["rect"] = low
    ident = max(t["id"] for t in value["timbers"]) + 1
    value["timbers"].extend((dict(main, id=ident, rect=high),
                            dict(id=ident + 1, kind=replacement, rect=plug,
                                 edge=[rect[a], rect[a + 2]], rc_line=middle)))
    return value, plug


class NotchCheckerRegression(unittest.TestCase):
    def setUp(self):
        self.params = dict(CHECK.PARAMS)
        self.room, _ = CHECK.normalize_room(CHECK.L_ROOM)
        self.original = CHECK.REFERENCE.build(self.room, CHECK.LAYOUT, self.params)

    def codes(self, candidate):
        failures, _ = CHECK.independent_check(self.room, candidate, self.params)
        return {row["check"] for row in failures}

    def test_C01_indoor_fake_boundary_cannot_terminate_main(self):
        wrong, plug = split_main(self.original)
        self.assertIn("R03B_MAIN_CONTINUOUS_TRUE_RC_SPAN", self.codes(wrong),
                      "R03B_CHECKER_INDOOR_FAKE_BOUNDARY: " + str(plug))

    def test_C02_any_member_kind_cannot_replace_required_main(self):
        wrong = deepcopy(self.original)
        for timber in wrong["timbers"]:
            if timber["kind"] == "main":
                timber.update(kind="secondary")
        self.assertIn("R03B_REQUIRED_MAIN_RC_SPAN", self.codes(wrong),
                      "R03B_CHECKER_REQUIRED_MAIN_KIND")

    def test_C03_deleted_seam_metadata_does_not_delete_obligation(self):
        wrong = deepcopy(self.original)
        wrong["seams_a"] = []
        self.assertIn("R03B_SEAMS_FROM_INPUT", self.codes(wrong),
                      "R03B_CHECKER_SEAMS_A_INDEPENDENT")

    def test_C04_shifted_origin_is_detected_without_historical_check(self):
        wrong = CHECK.REFERENCE.build(self.room, CHECK.LAYOUT, self.params, {"shift_origin"})
        with patch.object(CHECK.REFERENCE, "check", side_effect=AssertionError("REFERENCE_CHECK_FORBIDDEN")), \
                patch.object(CHECK.REFERENCE, "build", side_effect=AssertionError("REFERENCE_BUILD_FORBIDDEN")), \
                patch.object(CHECK.REFERENCE, "Region", side_effect=AssertionError("REFERENCE_REGION_FORBIDDEN")):
            codes = self.codes(wrong)
        self.assertIn("R03B_SEAMS_FROM_INPUT", codes, "R03B_CHECKER_ORIGIN_INDEPENDENT")

    def test_C05_candidate_axes_and_layout_are_not_input(self):
        wrong = deepcopy(self.original)
        wrong["a"], wrong["b"] = 1, 0
        wrong["layout"] = dict(A="y", a_start="max", b_start="max")
        self.assertIn("R03B_AXES_FROM_INPUT", self.codes(wrong),
                      "R03B_CHECKER_AXES_INDEPENDENT")

    def test_C06_u_cut_splits_one_nominal_board_into_two_components(self):
        room = CHECK.u_room(begin=500)
        candidate = CHECK.REFERENCE.build(room, CHECK.LAYOUT, self.params)
        failures, boards = CHECK.independent_check(room, candidate, self.params)
        self.assertEqual(failures, [], "R03B_CHECKER_U_FIXTURE_VALID")
        pieces = [board for board in boards if board["key"] == [4, 0]]
        self.assertEqual(len(pieces), 2, "R03B_CHECKER_R42_TWO_COMPONENTS")
        self.assertEqual([board.get("componentId") for board in pieces], [0, 1],
                         "R03B_CHECKER_R42_COMPONENT_ORDER")
        self.assertEqual([board["clipped_cells"] for board in pieces],
                         [[[3668, 0, 3880, 500]], [[3668, 900, 3880, 1830]]],
                         "R03B_CHECKER_R42_COMPONENT_GEOMETRY")
        for board in pieces:
            self.assertEqual(len(board["sides"]), 4, "R03B_CHECKER_COMPONENT_PHYSICAL_EDGES")
            for side in board["sides"]:
                self.assertTrue(side["supports"] or side["short_edge_bridges"],
                                "R03B_CHECKER_COMPONENT_BEARING")

    def test_C07_true_rc_is_derived_without_self_reported_edge(self):
        clean = deepcopy(self.original)
        for timber in clean["timbers"]:
            for key in ("edge", "rc_line", "ext", "shift", "at"):
                timber.pop(key, None)
        self.assertEqual(self.codes(clean), set(), "R03B_CHECKER_RC_DERIVED_FROM_RING")

    def test_C08_deleted_seams_and_retyped_members_remain_rejected(self):
        wrong = deepcopy(self.original)
        wrong["seams_a"] = []
        for timber in wrong["timbers"]:
            if timber["kind"] == "main":
                timber["kind"] = "boundary"
                timber["edge"] = [timber["rect"][0], timber["rect"][2]]
        self.assertIn("R03B_REQUIRED_MAIN_RC_SPAN", self.codes(wrong),
                      "R03B_CHECKER_NO_SELF_DECLARED_MAIN_OBLIGATION")

    def test_C09_fake_boundary_replacement_preserves_material_coverage(self):
        wrong, _ = split_main(self.original)
        failures, _ = CHECK.independent_check(self.room, wrong, self.params)
        self.assertFalse(any(row["check"] in ("R03B_NO_OVERLAP", "R03B_NO_WALL_CROSSING",
                                              "R03B_BOARD_EDGE_UNSUPPORTED") for row in failures),
                         "R03B_CHECKER_ATTACK_IS_CONTINUITY_NOT_MISSING_MATERIAL")
        self.assertTrue(failures, "R03B_CHECKER_FULL_COVERAGE_IS_NOT_MAIN_CONTINUITY")

    def test_C10_split_u_remains_valid_for_both_gaps_and_all_input_layouts(self):
        for gap in (2, 3):
            for layout in CHECK.REFERENCE.LAYOUTS:
                with self.subTest(gap=gap, layout=layout):
                    output, _ = CHECK.construct(CHECK.u_room(begin=500), layout, dict(self.params, gap=gap))
                    self.assertEqual(output["reference_verdict"], "buildable", "R03B_CHECKER_U_POLICY_BASELINE")
                    self.assertEqual(output["independent_failures"], [], "R03B_CHECKER_U_ALL_LAYOUTS_NO_NARROWING")

    def test_C11_point_contact_is_not_material_connectivity(self):
        components = getattr(CHECK, "material_components", None)
        self.assertTrue(callable(components), "R03B_CHECKER_R42_INTERIOR_CONNECTIVITY")
        self.assertEqual(components([[0, 0, 10, 10], [10, 10, 20, 20]]),
                         [[[0, 0, 10, 10]], [[10, 10, 20, 20]]], "R03B_CHECKER_R42_POINT_CONTACT_SEPARATE")
        self.assertEqual(components([[0, 0, 10, 10], [10, 0, 20, 10]]),
                         [[[0, 0, 10, 10], [10, 0, 20, 10]]], "R03B_CHECKER_R42_POSITIVE_EDGE_CONNECTED")

    def test_C12_ring_start_and_winding_do_not_change_component_identity(self):
        room = CHECK.u_room(begin=500)
        original = CHECK.REFERENCE.build(room, CHECK.LAYOUT, self.params)
        def geometry(boards):
            self.assertTrue(all("componentId" in board and "rings" in board for board in boards),
                            "R03B_CHECKER_R42_COMPLETE_COMPONENT_GEOMETRY")
            return [{key: board[key] for key in ("key", "componentId", "clipped_cells", "rings")} for board in boards]
        _, boards = CHECK.independent_check(room, original, self.params)
        expected = geometry(boards)
        ring = room["outer"]
        for changed in (ring[3:] + ring[:3], list(reversed(ring))):
            failures, other = CHECK.independent_check(dict(outer=changed), original, self.params)
            self.assertEqual(failures, [], "R03B_CHECKER_TRUE_RC_RING_ORDER_INDEPENDENT")
            self.assertEqual(geometry(other), expected, "R03B_CHECKER_R42_STABLE_COMPONENT_IDENTITY")

    def test_C13_short_edge_exception_does_not_waive_transverse_bearing(self):
        room = dict(outer=[[0, 0], [5, 0], [5, 100], [0, 100]])
        candidate = dict(a=0, b=1, seams_a=[], seams_b=[],
                         timbers=[dict(id=0, kind="main", rect=[0, 0, 5, 100])])
        _, failures = CHECK.board_supports(room, candidate, self.params)
        self.assertTrue(any(row["check"] == "R03B_BOARD_EDGE_BEARING_TOO_NARROW" for row in failures),
                        "R03B_CHECKER_X_IS_NOT_TRANSVERSELY_WAIVED")


if __name__ == "__main__":
    unittest.main()
