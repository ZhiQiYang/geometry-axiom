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



# ---------------------------------------------------------------------------
# R17 / #335: D16a boundary-pair/1 native slice.  The positive is the same
# 13 mm wall step as step() above; product lengths are compared to the oracle
# rectangles value by value.  These cases drive the real core (--scene) and the
# real bridge line protocol (loadfile / line / dump / undo / redo).
# ---------------------------------------------------------------------------
import os
import re
import shutil
try:
    import resource
    _soft, _hard = resource.getrlimit(resource.RLIMIT_STACK)
    if _soft != resource.RLIM_INFINITY and _soft < 16 * 1024 * 1024:
        resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024 if _hard == resource.RLIM_INFINITY
                                                   else min(16 * 1024 * 1024, _hard), _hard))
except (ImportError, ValueError, OSError):
    pass
_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import binaries  # noqa: E402
import _bridge  # noqa: E402

ROOT = _TESTS.parent
STEP_SURFACE = "surface 1 origin 0 0 2500 u +x v +y outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000"
PAIR_LINES = ("timber 1 27 20 role boundary", "timber 2 27 20 role boundary",
              "place 1 on 1 at-face e0 +u +n", "place 2 on 1 at-face e2 +u +n")


def pair_scene(order=(0, 1, 2, 3), begin="1 2", requires=True, surface=STEP_SURFACE, body=None, extra=()):
    lines = ["requires boundary-pair/1"] if requires else []
    lines += [surface, "boundary-pair begin " + begin]
    lines += [(body or PAIR_LINES)[i] for i in order] + ["boundary-pair end", *extra]
    return "\n".join(lines) + "\n"


def core_executable():
    explicit = os.environ.get("GEOMETRY_TEST_CORE")
    if explicit:
        return binaries.require_fresh("core", explicit) if hasattr(binaries, "require_fresh") else explicit
    info = binaries.inspect_one(binaries.BY_NAME["core"])
    if info.state != "fresh":
        raise unittest.SkipTest("core is %s (%s); run python3 tests/binaries.py build core" % (info.state, info.reason))
    return str(info.path)


def run_core(exe, scene):
    with tempfile.TemporaryDirectory(prefix="r17-pair-") as directory:
        path = Path(directory) / "pair.scene"
        path.write_text(scene, encoding="utf-8")
        run = subprocess.run([exe, "--no-window", "--scene", str(path), "--out", str(Path(directory) / "o.svg")],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return run


TIMBER_RE = re.compile(r"角材 ID：(\d+)\n尺寸：L=(\d+)，A=(\d+)，B=(\d+) mm\n角材原點：\((-?\d+), (-?\d+), (-?\d+)\)")


def placed_timbers(stdout):
    return {int(m[1]): dict(L=int(m[2]), A=int(m[3]), B=int(m[4]), origin=(int(m[5]), int(m[6]), int(m[7])))
            for m in TIMBER_RE.finditer(stdout)}


def assert_pair_positive(run):
    """Named judgement used by the positive cases and by the named withdrawals."""
    if run.returncode < 0:
        raise RuntimeError("core crashed (signal %d); a crash is never a semantic verdict" % -run.returncode)
    reg, own, other = step()
    expected = {}
    for timber in (own, other):
        x0, y0, x1, y1 = timber["rect"]
        expected[timber["id"]] = dict(L=x1 - x0, A=27, B=20, origin=(x0, y0, 2500))
    placed = placed_timbers(run.stdout) if run.returncode == 0 else {}
    actual = {key: placed[key] for key in expected if key in placed}
    if run.returncode != 0 or actual != expected:
        raise AssertionError("BOUNDARY_PAIR_POSITIVE: expected oracle %r, got exit %d %r; %s" % (
            expected, run.returncode, actual, run.stderr.strip()))
    return actual


def assert_pair_preview(preview, change="created"):
    """Named I8a/D16a preview contract: authored records, both members' sources,
    roles and old/new intervals, and the real central contact."""
    try:
        pairs = preview["boundaryPairs"]
        group = next(g for g in pairs if (g["first"], g["second"]) == (1, 2))
        assert group["change"] == change and group["capability"] == "boundary-pair/1", group
        if change == "removed":
            assert group["after"] is None and [m["id"] for m in group["before"]["members"]] == [1, 2], group
            assert preview["command"] == "boundary-pair delete 1 2", preview["command"]
            return group
        assert group["before"] is None, group
        members = {m["id"]: m for m in group["after"]["members"]}
        for member, edge, interval in ((1, "e0", [0, 500]), (2, "e2", [500, 1000])):
            m = members[member]
            assert m["role"] == "boundary" and (m["A"], m["B"]) == (27, 20), m
            assert m["source"] == {"surface": 1, "kind": "at-face", "edge": edge, "dir": "+u", "side": "+n"}, m
            assert m["interval"] == interval and m["cross"] == ([0, 27] if member == 1 else [13, 40]), m
        assert group["after"]["contacts"] == [{"member": 1, "end": "END", "peer": 2, "peerEnd": "START",
                                               "plane": 500, "contact": [13, 27]}], group["after"]["contacts"]
        for line in PAIR_LINES:
            assert line in preview["command"].split("\n"), preview["command"]
        assert preview["command"].startswith("boundary-pair begin ") and preview["command"].endswith("boundary-pair end")
        return group
    except (AssertionError, KeyError, StopIteration, TypeError) as error:
        raise AssertionError("BOUNDARY_PAIR_PREVIEW_CONTRACT: %r" % (error,)) from None


DOWNSTREAM_SCENE = pair_scene(extra=("timber 3 27 20 role boundary", "place 3 on 1 at-face e4 +u +n",
                                      "guide 9 1 v timber:1:A", "timber 4 27 20 role primary",
                                      "place 4 on 1 at-line guide 9 +v +n"))


def _scene_file(text, name):
    directory = Path(tempfile.mkdtemp(prefix="r17-scene-"))
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def bridge_replies(exe, commands):
    """One bridge process, one JSON reply per command; a crash is setup failure, never a kill."""
    run = subprocess.run([exe], input="\n".join(commands) + "\n", capture_output=True, text=True,
                         encoding="utf-8", timeout=180)
    if run.returncode < 0:
        raise RuntimeError("bridge crashed (signal %d); not a semantic verdict" % -run.returncode)
    replies = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
    if len(replies) != len(commands):
        raise RuntimeError("bridge dialogue incomplete: %r" % replies)
    return replies


def downstream_impact_run(exe):
    replies = bridge_replies(exe, ["loadfile " + str(_scene_file(DOWNSTREAM_SCENE, "downstream.scene")),
                                   "line preview timber 1 30 20 role boundary"])
    if not replies[0].get("ok") or not replies[1].get("ok") or not replies[1].get("preview"):
        raise RuntimeError("downstream preview setup failed: %r" % replies)
    return replies[1]["preview"]


def assert_downstream_impact(preview):
    """Named I8a/D16a judge: a member section change lists every affected ordinary timber
    with its role, authored source and real end contacts, not only moved geometry."""
    try:
        assert preview["valid"] is True, preview.get("violations")
        impacts = {row["id"]: row for row in preview["timberImpacts"]}
        assert {1, 2, 4} <= set(impacts), sorted(impacts)
        row = impacts[4]
        for side, centre, contact in (("before", 27, [14, 41]), ("after", 30, [17, 44])):
            value = row[side]
            assert value["role"] == "primary" and value["source"]["anchor"] == "at-line guide 9", value
            assert value["boundaryPair"] is None and value["geometry"]["centerline"] == centre, value
            ends = {(c["end"], c["kind"], c.get("timber")): c["contact"] for c in value["contacts"]}
            assert ends == {("START", "timber", 1): contact, ("END", "timber", 3): contact}, ends
        member = impacts[1]
        assert member["before"]["boundaryPair"] == [1, 2] and member["before"]["source"]["anchor"] == "at-face e0", member
        assert (member["before"]["A"], member["after"]["A"]) == (27, 30), member
        peer = {(c["end"], c.get("timber")): c["contact"] for c in impacts[2]["after"]["contacts"] if c["kind"] == "timber"}
        assert peer == {("START", 1): [13, 30]}, impacts[2]
        return impacts
    except (AssertionError, KeyError, TypeError) as error:
        raise AssertionError("BOUNDARY_PAIR_DOWNSTREAM_IMPACT: %r" % (error,)) from None


def guide_roundtrip_run(exe, field="A"):
    scene = pair_scene(extra=("guide 9 1 v timber:1:%s" % field,))
    first = bridge_replies(exe, ["loadfile " + str(_scene_file(scene, "guide.scene")), "dump"])
    if not first[0].get("ok"):
        raise RuntimeError("original guide scene refused: %r" % first[0])
    text = first[1]["text"]
    second = bridge_replies(exe, ["loadfile " + str(_scene_file(text, "dumped.scene")), "dump"])
    return text, second[0], second[1].get("text")


def assert_guide_roundtrip(result):
    """Named R4/I9 judge: a guide on a member's A/B is written after the closed group and reloads idempotently."""
    text, reloaded, again = result
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    try:
        guide = next(i for i, line in enumerate(lines) if line.startswith("guide 9 "))
        assert lines.index("boundary-pair end") < guide, lines
        assert reloaded.get("ok") is True, reloaded
        assert again == text, (again, text)
    except (AssertionError, StopIteration, ValueError) as error:
        raise AssertionError("BOUNDARY_PAIR_GUIDE_ROUNDTRIP: %r" % (error,)) from None


def placed_section(stdout):
    return stdout[stdout.index("=== 已放置的完整角材 ==="):stdout.index("=== SVG 三視圖 ===")]


class BoundaryPairNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = core_executable()

    def bridge(self):
        session = _bridge.BridgeSession()
        self.addCleanup(session.stop)
        return session

    def load(self, session, scene):
        directory = tempfile.TemporaryDirectory(prefix="r17-pair-bridge-")
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "load.scene"
        path.write_text(scene, encoding="utf-8")
        return session.command("loadfile " + str(path))

    def test_BP_positive_thirteen_mm_step_matches_oracle_in_both_member_orders(self):
        reg, own, other = step()
        # Independent oracle verdict for both central ends of the same geometry.
        self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, own, [own, other], 0, 500))
        self.assertEqual(fo.READING_A_PARTIAL, fo.reading_a_end_admission(reg, other, [own, other], 0, 500))
        runs = [run_core(self.core, pair_scene(order, begin)) for order, begin in
                (((0, 1, 2, 3), "1 2"), ((1, 0, 3, 2), "2 1"), ((3, 1, 2, 0), "2 1"))]
        for run in runs:
            actual = assert_pair_positive(run)
            self.assertEqual({1: 500, 2: 500}, {k: v["L"] for k, v in actual.items()})
        self.assertEqual(placed_section(runs[0].stdout), placed_section(runs[1].stdout))
        self.assertEqual(placed_section(runs[0].stdout), placed_section(runs[2].stdout))
        dumps = []
        for order, begin in (((0, 1, 2, 3), "1 2"), ((1, 0, 3, 2), "2 1")):
            session = self.bridge()
            self.assertTrue(self.load(session, pair_scene(order, begin))["ok"])
            dumps.append(session.command("dump")["text"])
        self.assertEqual(dumps[0].encode("utf-8"), dumps[1].encode("utf-8"))

    def test_BP_single_member_paths_keep_the_issue_335_refusals(self):
        base = STEP_SURFACE + "\ntimber 1 27 20 role boundary\ntimber 2 27 20 role boundary\n"
        first = run_core(self.core, base + "place 1 on 1 at-face e0 +u +n\nplace 2 on 1 at-face e2 +u +n\n")
        self.assertEqual(1, first.returncode)
        self.assertIn("跨距終點沒有擋面", first.stderr)
        second = run_core(self.core, base + "place 2 on 1 at-face e2 +u +n\nplace 1 on 1 at-face e0 +u +n\n")
        self.assertEqual(1, second.returncode)
        self.assertIn("中線上沒有任何合法跨距", second.stderr)
        alone = run_core(self.core, STEP_SURFACE + "\ntimber 2 27 20 role boundary\nplace 2 on 1 at-face e2 +u +n\n")
        self.assertEqual(0, alone.returncode, alone.stderr)
        self.assertEqual(1000, placed_timbers(alone.stdout)[2]["L"])

    def test_BP_dump_is_one_closed_unit_with_capability_and_round_trips(self):
        tail = ("timber 3 27 20 role boundary", "place 3 on 1 at-face e4 +u +n")
        session = self.bridge()
        self.assertTrue(self.load(session, pair_scene((2, 3, 1, 0), "2 1", extra=tail))["ok"])
        text = session.command("dump")["text"]
        lines = [line for line in text.splitlines() if not line.startswith("#")]
        self.assertIn("requires boundary-pair/1", lines)
        start = lines.index("boundary-pair begin 1 2")
        self.assertEqual(["boundary-pair begin 1 2", *PAIR_LINES, "boundary-pair end"], lines[start:start + 6])
        self.assertEqual(1, text.count("timber 1 27 20 role boundary"))
        self.assertEqual(1, text.count("place 1 on"))
        self.assertLess(start, lines.index("place 3 on 1 at-face e4 +u +n"))
        self.assertLess(lines.index("requires boundary-pair/1"), start)
        again = self.bridge()
        self.assertTrue(self.load(again, text)["ok"])
        self.assertEqual(text, again.command("dump")["text"])
        # A group created after an ordinary member keeps that member before it.
        before = self.bridge()
        scene = "requires boundary-pair/1\n" + STEP_SURFACE + "\n" + "\n".join(tail) + "\nboundary-pair begin 1 2\n" + \
            "\n".join(PAIR_LINES) + "\nboundary-pair end\n"
        self.assertTrue(self.load(before, scene)["ok"])
        lines = [line for line in before.command("dump")["text"].splitlines() if not line.startswith("#")]
        self.assertLess(lines.index("place 3 on 1 at-face e4 +u +n"), lines.index("boundary-pair begin 1 2"))
        state = session.command("engineering-read")["state"]
        self.assertEqual(["boundary-pair/1"], [c for c in state["required_capabilities"] if c == "boundary-pair/1"])
        self.assertNotIn("boundary-pair/1", state["capabilities"], "the native subset is not complete host support")
        self.assertEqual(("boundary-pair/1", False, ["literal"]), (state["boundary_pair_native"]["capability"],
                         state["boundary_pair_native"]["complete"], state["boundary_pair_native"]["memberDimensionSources"]))
        positive = run_core(self.core, text)
        actual = assert_pair_positive(positive)
        self.assertEqual({1: 500, 2: 500}, {k: actual[k]["L"] for k in (1, 2)})

    def test_BP_interactive_preview_confirm_cancel_delete_undo_redo(self):
        s = self.bridge()
        self.assertTrue(self.load(s, STEP_SURFACE + "\n")["ok"])
        empty = s.command("dump")["text"]
        self.assertTrue(s.line("boundary-pair begin 1 2")["ok"])
        for line in PAIR_LINES:
            self.assertTrue(s.line(line)["ok"], line)
        self.assertEqual(empty, s.command("dump")["text"], "package lines are not individual commits")
        nested = s.line("boundary-pair begin 3 4")
        self.assertFalse(nested["ok"])
        self.assertIn("D16a", nested["error"])
        self.assertFalse(s.line("boundary-pair end")["ok"], "a refused begin discards the open input")
        self.assertTrue(s.line("boundary-pair begin 2 1")["ok"])
        for line in reversed(PAIR_LINES):
            self.assertTrue(s.line(line)["ok"], line)
        ended = s.line("boundary-pair end")
        self.assertTrue(ended["ok"], ended)
        self.assertFalse(ended["history_changed"])
        token = ended["preview"]["token"]
        assert_pair_preview(ended["preview"])
        self.assertEqual(empty, s.command("dump")["text"], "preview does not publish")
        self.assertFalse(s.line("boundary-pair begin 1 2")["ok"], "a pending preview blocks a new begin")
        self.assertFalse(s.line("confirm %d" % token)["ok"], "generic confirm cannot take a pair token")
        confirmed = s.line("boundary-pair confirm %d" % token)
        self.assertTrue(confirmed["ok"], confirmed)
        self.assertTrue(confirmed["history_changed"])
        paired = s.command("dump")["text"]
        self.assertIn("boundary-pair begin 1 2", paired)
        self.assertFalse(s.line("boundary-pair confirm %d" % token)["ok"], "a used token cannot commit twice")
        for refused in ("place 1 on 1 at-face e0 +u +n", "delete timber 1", "timber 2 27 20 role primary"):
            result = s.line(refused)
            self.assertFalse(result["ok"], refused)
            self.assertIn("D16a", result["error"], refused)
        self.assertEqual(paired, s.command("dump")["text"])
        self.assertTrue(s.line("undo")["ok"])
        self.assertEqual(empty, s.command("dump")["text"])
        self.assertTrue(s.line("redo")["ok"])
        self.assertEqual(paired, s.command("dump")["text"])
        prepared = s.line("boundary-pair delete 2 1")
        self.assertTrue(prepared["ok"], prepared)
        self.assertTrue(s.line("boundary-pair cancel")["ok"])
        self.assertEqual(paired, s.command("dump")["text"])
        prepared = s.line("boundary-pair delete 1 2")
        assert_pair_preview(prepared["preview"], "removed")
        removed = s.line("boundary-pair confirm %d" % prepared["preview"]["token"])
        self.assertTrue(removed["ok"], removed)
        self.assertEqual(empty, s.command("dump")["text"])
        self.assertTrue(s.line("undo")["ok"])
        self.assertEqual(paired, s.command("dump")["text"])

    def test_BP_refusals_name_their_clause_before_replacing_the_world(self):
        rectangle = "surface 1 origin 0 0 2500 u +x v +y outline 0,0 1000,0 1000,1000 0,1000"
        cases_ = {
            "P1-A not butting": (pair_scene(surface=rectangle), "D16a"),
            "missing piece": (pair_scene(order=(0, 1, 2)), "D16a"),
            "duplicate place": (pair_scene(order=(0, 1, 2, 2)), "D16a"),
            "mixed command": (pair_scene(order=(0, 1, 2, 3)).replace("boundary-pair end", "spec x 5\nboundary-pair end"), "D16a"),
            "unterminated": (pair_scene().replace("boundary-pair end\n", ""), "D16a"),
            "same edge": (pair_scene(body=(*PAIR_LINES[:3], "place 2 on 1 at-face e0 +u +n")), "D16a"),
            "role not boundary": (pair_scene(body=(PAIR_LINES[0], "timber 2 27 20 role primary", *PAIR_LINES[2:])), "D16a"),
            "forward reference": (pair_scene(body=(*PAIR_LINES[:2], "place 1 on 9 at-face e0 +u +n",
                                                   "place 2 on 9 at-face e2 +u +n")).replace(
                "boundary-pair end", "boundary-pair end\nsurface 9 origin 0 0 0 u +x v +y rect 0 0 10 10"), "I9"),
            "capability missing": (pair_scene(requires=False), "boundary-pair/1"),
        }
        for name, (scene, clause) in cases_.items():
            with self.subTest(case=name):
                run = run_core(self.core, scene)
                self.assertEqual(1, run.returncode, run.stdout[-400:])
                self.assertIn(clause, run.stderr)
                s = self.bridge()
                self.assertTrue(self.load(s, STEP_SURFACE + "\n")["ok"])
                before = s.command("dump")["text"]
                self.assertFalse(self.load(s, scene)["ok"])
                self.assertEqual(before, s.command("dump")["text"], "a refused load keeps the old World")

    def test_BP_downstream_preview_and_member_guide_round_trip(self):
        bridge = _bridge.find_bridge()
        impacts = assert_downstream_impact(downstream_impact_run(bridge))
        self.assertEqual("changed", impacts[4]["change"])
        for field in ("A", "B"):
            with self.subTest(field=field):
                assert_guide_roundtrip(guide_roundtrip_run(bridge, field))
        # An ordinary single member keeps its original dependency order and round trip.
        single = STEP_SURFACE + "\ntimber 2 27 20 role boundary\nplace 2 on 1 at-face e2 +u +n\nguide 9 1 v timber:2:A\n"
        first = bridge_replies(bridge, ["loadfile " + str(_scene_file(single, "single.scene")), "dump"])
        second = bridge_replies(bridge, ["loadfile " + str(_scene_file(first[1]["text"], "single2.scene")), "dump"])
        self.assertTrue(second[0]["ok"], second[0])
        self.assertEqual(first[1]["text"], second[1]["text"])

    def test_BP_named_withdrawals_fail_exact_assertions_then_restore(self):
        rectangle = "surface 1 origin 0 0 2500 u +x v +y outline 0,0 1000,0 1000,1000 0,1000"
        controls = (
            ("pair-candidate", "geometry-core/references.inc", "if(boundary_pair_member(w,ti)>=0)return boundary_pair_candidate(evaluation,w,ti);",
             "", pair_scene(), "BOUNDARY_PAIR_POSITIVE"),
            ("pair-validation", "current_geometry.c", "if(!boundary_pair_check_all(candidate))",
             "if(false)", pair_scene(surface=rectangle), "BOUNDARY_PAIR_P1A_REFUSED"),
            ("pair-preview", "geometry-web/reference_bridge.inc", "    json_boundary_pair_preview();\n",
             "", None, "BOUNDARY_PAIR_PREVIEW_CONTRACT"),
        )

        def preview_run(exe):
            session = _bridge.BridgeSession(exe) if exe else _bridge.BridgeSession()
            try:
                self.assertTrue(self.load(session, STEP_SURFACE + "\n")["ok"])
                for line in ("boundary-pair begin 1 2", *PAIR_LINES):
                    self.assertTrue(session.line(line)["ok"], line)
                return session.line("boundary-pair end")
            finally:
                session.stop()

        def judge(name, run):
            if name == "pair-preview":
                if not run.get("ok"):
                    raise RuntimeError("preview setup failed: %r" % run)
                assert_pair_preview(run["preview"])
                return
            if name == "pair-candidate":
                assert_pair_positive(run)
                return
            if run.returncode < 0:
                raise RuntimeError("core crashed (signal %d)" % -run.returncode)
            if run.returncode != 1 or "D16a" not in run.stderr:
                raise AssertionError("BOUNDARY_PAIR_P1A_REFUSED: exit %d %s" % (run.returncode, run.stderr.strip()))

        for name, module, before, after, scene, assertion in controls:
            with self.subTest(control=name):
                phases = []
                fresh = (lambda: preview_run(None)) if scene is None else (lambda: run_core(self.core, scene))
                judge(name, fresh())
                phases.append(dict(phase="baseline", exit_code=0))
                with tempfile.TemporaryDirectory(prefix="r17-withdraw-") as directory:
                    if scene is None:
                        exe = build_withdrawn(Path(directory), "geometry-web/web_bridge.c", module, before, after, "bridge")
                        run = preview_run_unchecked(exe)
                    else:
                        exe = build_withdrawn(Path(directory), "current_geometry.c", module, before, after, "core")
                        run = run_core(exe, scene)
                    with self.assertRaises(AssertionError) as raised:
                        judge(name, run)
                    self.assertIn(assertion, str(raised.exception))
                    phases.append(dict(phase="withdrawn", exit_code=1, core_exit=getattr(run, "returncode", 0),
                                       assertion=str(raised.exception).split(":")[0]))
                judge(name, fresh())
                phases.append(dict(phase="restored", exit_code=0))
                print("R17_BOUNDARY_PAIR_WITHDRAWAL " + json.dumps(dict(control=name, module=module, phases=phases),
                      ensure_ascii=False), flush=True)

        scripted = (
            ("pair-impacts", "geometry-web/reference_bridge.inc", "    json_timber_impacts();\n", "",
             downstream_impact_run, assert_downstream_impact, "BOUNDARY_PAIR_DOWNSTREAM_IMPACT"),
            ("pair-guide-order", "geometry-core/references.inc",
             "        if (ti>=0 && !placed[ti] && boundary_pair_index(w,(uint32_t)id)>=0) return false;\n", "",
             guide_roundtrip_run, assert_guide_roundtrip, "BOUNDARY_PAIR_GUIDE_ROUNDTRIP"),
        )
        bridge = _bridge.find_bridge()
        for name, module, before, after, runner, verdict, assertion in scripted:
            with self.subTest(control=name):
                phases = []
                verdict(runner(bridge))
                phases.append(dict(phase="baseline", exit_code=0))
                with tempfile.TemporaryDirectory(prefix="r17-withdraw-") as directory:
                    exe = build_withdrawn(Path(directory), "geometry-web/web_bridge.c", module, before, after, "bridge")
                    result = runner(exe)
                    with self.assertRaises(AssertionError) as raised:
                        verdict(result)
                    self.assertIn(assertion, str(raised.exception))
                    phases.append(dict(phase="withdrawn", exit_code=1, assertion=str(raised.exception).split(":")[0]))
                verdict(runner(bridge))
                phases.append(dict(phase="restored", exit_code=0))
                print("R17_BOUNDARY_PAIR_WITHDRAWAL " + json.dumps(dict(control=name, module=module, phases=phases),
                      ensure_ascii=False), flush=True)


def preview_run_unchecked(exe):
    """Drive a withdrawn bridge directly (no registry freshness sidecar exists for it)."""
    lines = ["loadfile " + str(_STEP_FILE()), "line boundary-pair begin 1 2", *("line " + l for l in PAIR_LINES),
             "line boundary-pair end"]
    run = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode < 0:
        raise RuntimeError("withdrawn bridge crashed (signal %d); not a kill" % -run.returncode)
    replies = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
    if len(replies) != len(lines) or not all(r.get("ok") for r in replies):
        raise RuntimeError("withdrawn bridge setup failed: %r" % replies)
    return replies[-1]


def _STEP_FILE():
    directory = Path(tempfile.mkdtemp(prefix="r17-step-"))
    path = directory / "step.scene"
    path.write_text(STEP_SURFACE + "\n", encoding="utf-8")
    return path


def build_withdrawn(directory, main, module, before, after, registry):
    """Relocate the main unit and one include file into TEMP; never edit the checkout."""
    variant = {}
    # current_geometry.c is always relocated: bridge-side includes of core files go through it.
    for name in dict.fromkeys((main, "current_geometry.c", module)):
        text = (ROOT / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        if name == module:
            if text.count(before) != 1:
                raise AssertionError("withdrawal must change exactly one site: " + before)
            text = text.replace(before, after)
        variant[name] = text
    targets = {(ROOT / name).resolve(): directory / name for name in variant}
    for name, text in variant.items():
        origin = ROOT / name

        def relocate(match, origin=origin):
            include = (origin.parent / match.group(1)).resolve()
            return '#include "%s"' % targets.get(include, include).as_posix()
        target = targets[origin.resolve()]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(re.sub(r'^#include "([^"\n]+)"', relocate, text, flags=re.M), encoding="utf-8")
    exe = directory / (registry + "-withdrawn")
    cc = os.environ.get("CC", "cc")
    build = subprocess.run([cc, *binaries.BY_NAME[registry].posix_flags, str(targets[(ROOT / main).resolve()]),
                            "-o", str(exe), "-lm"], cwd=ROOT, capture_output=True, text=True, timeout=900)
    if build.returncode:
        raise RuntimeError("withdrawn " + registry + " did not compile (setup failure, not a kill): " + build.stderr[-2000:])
    return str(exe)


if __name__ == "__main__":
    unittest.main()
