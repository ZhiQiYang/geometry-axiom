"""Approved Reading A geometry and independent positive coverage controls.

These tests use the oracle's all-FIXED single-placement model. Native FREE,
placement identity, returned FEATURE and atomic edit controls are separate.
"""
from pathlib import Path
import sys
import hashlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ORACLE = Path(__file__).resolve().parents[1] / "geometry-core/framing-template/oracle"
sys.path.insert(0, str(ORACLE))
import framing_oracle as fo
import reading_a_cases as cases


def step(amount=13):
    # Own lower fixed edge is x=0..500 at y=0. At x=500, amount mm
    # faces short RC and 27-amount mm contacts the next same-axis timber.
    region = fo.Region([(0, 0), (500, 0), (500, amount), (1000, amount),
                        (1000, 1000), (0, 1000)], [])
    own = dict(id=1, kind="boundary", outer=True, edge=[0, 500], rect=(0, 0, 500, 27))
    other = dict(id=2, kind="boundary", outer=True, edge=[500, 1000],
                 rect=(500, amount, 1000, amount + 27))
    return region, own, other


class ReadingAOracle(unittest.TestCase):
    def test_same_axis_thirteen_mm_step_accepts_fourteen_mm_timber_contact(self):
        reg, own, other = step()
        self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))
        self.assertEqual(fo.READING_A_PARTIAL, fo._reading_a_build_end(reg, own, [own, other], 0, 500))

    def test_one_mm_contact_is_positive_without_a_new_minimum(self):
        for amount in (1, 13, 26):
            with self.subTest(step=amount):
                reg, own, other = step(amount)
                self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))

    def test_target_role_does_not_restore_a_priority_restriction(self):
        reg, own, other = step()
        for kind in ("boundary", "main", "secondary", "rc_parallel"):
            with self.subTest(kind=kind):
                other.update(kind=kind, core_role="custom", priority=99)
                self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))

    def test_no_timber_point_contact_and_wrong_side_do_not_claim_exception(self):
        reg, own, other = step()
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own], 0, 500))
        other["rect"] = (500, 27, 1000, 54)
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))
        other["rect"] = (400, 13, 500, 40)  # crosses into self; its far face cannot supply contact
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))

    def test_other_self_roles_cannot_borrow_boundary_policy(self):
        reg, own, other = step()
        for kind in ("main", "secondary", "rc_parallel"):
            own["kind"] = kind
            self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))
        own.update(kind="boundary", core_role="custom")
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))

    def test_short_fixed_segment_and_extension_end_do_not_claim_exception(self):
        reg, own, other = step()
        own["rect"] = (0, 0, 499, 27)
        other["rect"] = (499, 13, 1000, 40)
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 499))
        # Upper boundary can extend left of its own edge in this valid region;
        # that far end is still I22, even though the whole rectangle is inside.
        own["rect"] = (0, 13, 1000, 40)
        self.assertEqual(fo.READING_A_ORDINARY, fo.reading_a_end_admission(reg, own, [own, other], 0, 0))

    def test_bare_rc_uses_original_face_length_including_exact_width(self):
        # Arithmetic controls feed explicit contact intervals to the RC helper;
        # they do not claim a whole physically valid placed scene.
        for length in (27, 28, 100):
            reg = fo.Region([(0, 0), (500, 0), (500, length), (0, length)], [])
            self.assertTrue(fo.reading_a_has_bare_rc(reg, 0, 500, (0, 27), [(13, 27)]))
        short = fo.Region([(0, 0), (500, 0), (500, 26), (0, 26)], [])
        self.assertFalse(fo.reading_a_has_bare_rc(short, 0, 500, (0, 27), [(26, 27)]))

    def test_collinear_subdivision_cannot_shrink_the_actual_rc_face(self):
        reg = fo.Region([(0, 0), (500, 0), (500, 15), (500, 30), (0, 30)], [])
        self.assertTrue(fo.reading_a_has_bare_rc(reg, 0, 500, (0, 27), [(13, 27)]))
        self.assertFalse(fo.reading_a_has_bare_rc(reg, 0, 500, (0, 27), [(0, 27)]))

    def test_rc_face_is_measured_along_its_unlined_run(self):
        # RC face x=500, y 0..90; above it the room continues (y 90..100 holds the
        # contact). Only the unlined run holding the exposed part decides.
        reg = fo.Region([(0, 0), (500, 0), (500, 90), (1000, 90), (1000, 1000), (0, 1000)], [])
        self.assertTrue(fo.reading_a_has_bare_rc(reg, 0, 500, (73, 100), [(90, 100)]))
        self.assertFalse(fo.reading_a_has_bare_rc(reg, 0, 500, (73, 100), [(90, 100)], [(0, 73)]))
        self.assertTrue(fo.reading_a_has_bare_rc(reg, 0, 500, (73, 100), [(90, 100)], [(0, 63)]))
        # COLSTEP(3000), left-top start, panels along Y: the y=3661 boundary ends at
        # x=3000 with 17 mm on the column-top timber and 10 mm on the column face,
        # whose other 190 mm is already lined. Removing that lining must refuse.
        room = {"outer": [[0, 0], [4100, 0], [4100, 3661], [3000, 3661], [3000, 3700], [0, 3700]],
                "holes": [[[2600, 3444], [3000, 3444], [3000, 3644], [2600, 3644]]]}
        layout = next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿Y")
        params = json.loads((ORACLE / "rooms.json").read_text(encoding="utf-8"))["params"]
        res = fo.build(room, layout, params)
        self.assertEqual(("buildable", []), fo.verdict(res, params))
        own = next(t for t in res["timbers"] if tuple(t["rect"]) == (3000, 3634, 4100, 3661))
        liner = next(t for t in res["timbers"] if tuple(t["rect"]) == (3000, 27, 3027, 3634))
        rest = [t for t in res["timbers"] if t is not liner]
        for judge in (fo._reading_a_build_end, fo.reading_a_end_admission):
            with self.subTest(judge=judge.__name__):
                self.assertEqual(fo.READING_A_PARTIAL, judge(res["region"], own, res["timbers"], res["a"], 3000))
                self.assertEqual(fo.READING_A_BARE_RC, judge(res["region"], own, rest, res["a"], 3000))

    def test_constructor_and_checker_have_independent_policy_derivations(self):
        reg, own, other = step()
        with patch.object(fo, "reading_a_end_admission", side_effect=AssertionError("checker called by builder")):
            self.assertEqual(fo.READING_A_PARTIAL, fo._reading_a_build_end(reg, own, [own, other], 0, 500))
        with patch.object(fo, "_reading_a_build_end", side_effect=AssertionError("builder called by checker")):
            self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))

    def test_only_approved_boundary_limit_is_removed_and_others_stay_bound(self):
        reg, own, other = step()
        record = dict(code="CORE_LIMIT_BOUNDARY_END_FREE", _t=own, end=500)
        untouched = dict(code="CORE_LIMIT_EXTENSION_END_FREE", _t=own, end=0)
        self.assertEqual([untouched], fo.reading_a_boundary_limits(reg, [own, other], [record, untouched], 0))

    def test_frozen_positive_identities_keep_all_528_and_1056_cases(self):
        required = cases.load_required()
        self.assertEqual(528, len(required["step"]))
        self.assertEqual(1056, len(required["step_mirror"]))
        for keys in required.values():
            observed = {key: "buildable" for key in keys}
            self.assertEqual({"missing": [], "not_buildable": []}, cases.coverage_problems(observed, keys))
            first = min(keys)
            del observed[first]
            self.assertEqual([first], cases.coverage_problems(observed, keys)["missing"])
            observed[first] = "core_limited"
            self.assertEqual([(first, "core_limited")], cases.coverage_problems(observed, keys)["not_buildable"])

    def test_builder_and_checker_withdrawal_fail_exact_assertions_then_restore(self):
        source = ORACLE / "framing_oracle.py"
        original = source.read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        client = ORACLE / "reading_a_source_control.py"
        for control, name in (("builder", "_reading_a_build_end"), ("checker", "reading_a_end_admission")):
            with self.subTest(control=control), tempfile.TemporaryDirectory(prefix="reading-a-source-") as directory:
                anchor = f"def {name}(reg, timber, timbers, k, at):\n"
                text = original.decode("utf-8")
                self.assertEqual(1, text.count(anchor))
                mutant = Path(directory) / "framing_oracle.py"
                mutant.write_text(text.replace(anchor, anchor + "    return READING_A_ORDINARY\n"), encoding="utf-8")
                phases = []
                for phase, path, code in (("baseline", source, 0), ("withdrawn", mutant, 1), ("restored", source, 0)):
                    command = [sys.executable, "-B", str(client), "--source", str(path), "--control", control]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    phases.append(dict(phase=phase, command=command, exit_code=result.returncode,
                                       stdout=result.stdout, stderr=result.stderr))
                    self.assertEqual(code, result.returncode, result.stdout + result.stderr)
                    if code:
                        self.assertIn("AssertionError: READING_A_" + control.upper() + "_PARTIAL", result.stderr)
                    self.assertEqual(digest, hashlib.sha256(source.read_bytes()).hexdigest())
                print("READING_A_SOURCE_PROOF " + json.dumps(dict(control=control, source_sha256=digest,
                      phases=phases), ensure_ascii=False), flush=True)

    def test_full_scan_cannot_filter_out_a_missing_room(self):
        required = {("A", "layout"), ("B|上下", "layout")}
        self.assertEqual(required, cases.expected_for_run(required, {"A"}, False))
        self.assertEqual({("A", "layout")}, cases.expected_for_run(required, {"A"}, True))


if __name__ == "__main__":
    unittest.main()
