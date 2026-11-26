"""PF-4B / R44: explicit ordinary D29 value snapshots through the real bridge.

Only transport and existing fixture construction are shared with PF-1/PF-2.
Coordinates and signed band conversion are calculated here from authored inputs,
never copied from the fill reader, grid evaluator, or implementation constants.
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_panel_fill_finish_surface as pf1
from tests import test_panel_fill_layout as pf2


def snapshot_op(identifier=71, fill_id=1, main="none", **extra):
    return {"op": "export-fill-grid-snapshot",
            "value": dict(id=identifier, fillId=fill_id, mainAlong=main, **extra)}


def parameter(gap="3", stagger="-17", extra_fields=()):
    return {"op": "put-parameter", "value": {
        "id": 91, "name": "快照來源", "fields": [
            {"id": 1, "name": "縫寬", "type": "dimension", "input": gap},
            {"id": 2, "name": "相位", "type": "dimension", "input": stagger},
            *extra_fields]}}


class PanelFillSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            pf1.FinishSurfaceNative.setUpClass.__func__(cls)
        except unittest.SkipTest as exc:
            raise AssertionError("PF4B_BUILD_REQUIRED: unavailable bridge is not acceptance: " + str(exc)) from exc
    setUp = pf1.FinishSurfaceNative.setUp
    command = pf1.FinishSurfaceNative.command
    load_text = pf1.FinishSurfaceNative.load_text
    read = pf1.FinishSurfaceNative.read
    snapshot = pf1.FinishSurfaceNative.snapshot
    preview = pf1.FinishSurfaceNative.preview
    apply = pf1.FinishSurfaceNative.apply
    seed = pf2.PanelFillLayout.seed
    layout = pf2.PanelFillLayout.layout

    def engineering_preview(self, operations):
        request = self.directory / "snapshot-request.json"
        request.write_text(json.dumps({"schema": "engineering-transaction/1",
                                      "expectedRevision": self.read()["revision"],
                                      "operations": operations}), encoding="utf-8")
        result = self.command("engineering-preview " + str(request))
        self.assertTrue(result["ok"], ("PF4B_TRANSPORT", result))
        return result["preview"]

    def engineering_apply(self, operations):
        preview = self.engineering_preview(operations)
        self.assertTrue(preview["valid"], ("PF4B_EXPORT_ACCEPT", preview["violations"]))
        confirmed = self.command("engineering-confirm %d" % preview["token"])
        self.assertTrue(confirmed["ok"], ("PF4B_CONFIRM", confirmed))
        return preview, confirmed

    def reject_export(self, operations, reason):
        before = self.snapshot()
        preview = self.engineering_preview(operations)
        self.assertFalse(preview["valid"], ("PF4B_REJECT", reason))
        self.assertIn(reason, json.dumps(preview["violations"], ensure_ascii=False),
                      "PF4B_NAMED_REJECTION")
        self.assertFalse(self.command("engineering-confirm %d" % preview["token"])["ok"])
        self.assertEqual(before, self.snapshot(), "PF4B_REJECTION_ATOMIC")

    def systems(self):
        result = self.command("objects")
        self.assertTrue(result["ok"], result)
        return {s["id"]: s for s in result["gridSystems"]}

    def query(self, identifier=71, rect=(-450, -450, 450, 450)):
        result = self.command("grid-query system %d rect %s mode exact limit 64" %
                              (identifier, " ".join(map(str, rect))))
        self.assertTrue(result["ok"], result)
        return result

    def commit_line(self, text):
        result = self.command("line " + text)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = self.command("line confirm %d" % result["preview"]["token"])
        self.assertTrue(result["ok"], result)
        return result

    def assert_axes(self, system, size=(83, 127), gap=3, origin=(-19, 23), stagger=None):
        for a, axis in enumerate("uv"):
            expected = {"source": "repeat-panel", "panel": size[a], "gap": gap,
                        "anchor": origin[a], "anchorExplicit": True}
            if stagger and stagger[0] == axis:
                expected["anchor"] += stagger[1]
                expected["stagger"] = -stagger[1]
            self.assertEqual(expected, system[axis + "Definition"],
                             "PF4B_DIRECT_VALUES_AND_D29_CELL_PARITY " + axis)
        self.assertNotIn("cardReference", system, "PF4B_NO_LIVE_CARD_REFERENCE")

    def seed_fill(self, **changes):
        # Each parameterized geometry fixture is independent. History behavior
        # is exercised explicitly in PF4B-11, not accumulated across cases.
        self.assertTrue(self.command("reset")["ok"])
        self.seed(width=83, length=127)
        self.layout(pf2.fill(origin=[-19, 23], **changes))

    def test_PF4B_01_preview_discloses_new_ordinary_source_and_confirm_once(self):
        self.seed_fill()
        before = self.snapshot()
        preview = self.engineering_preview([snapshot_op(main="v")])
        self.assertTrue(preview["valid"], ("PF4B_EXPORT_ACCEPT", preview["violations"]))
        self.assertEqual(before, self.snapshot(), "PF4B_PREVIEW_READ_ONLY")
        self.assertEqual([], preview["before"]["geometry"]["gridSystems"])
        new, = preview["after"]["geometry"]["gridSystems"]
        self.assertEqual(71, new["id"])
        self.assert_axes(new)
        self.assertEqual("v", new["mainAlong"], "PF4B_EXPLICIT_MAIN_ROLE")
        self.assertIn("1", new["name"], "PF4B_DEFAULT_NAME_IDENTIFIES_FILL")
        self.assertEqual([], new["applications"], "PF4B_NO_IMPLICIT_D30_OR_D10")
        self.assertEqual([], new["bindings"])
        self.assertTrue(self.command("engineering-confirm %d" % preview["token"])["history_changed"])
        self.assertEqual(before[1] + 1, self.read()["revision"], "PF4B_ONE_REVISION")
        self.assertEqual(new, self.systems()[71], "PF4B_SAME_CANDIDATE")
        self.assertFalse(self.command("engineering-confirm %d" % preview["token"])["ok"])

    def test_PF4B_02_straight_signed_infinite_lines_and_axis_identity(self):
        for gap in (0, 3):
            for along, sizes in (("v", (83, 127)), ("u", (127, 83))):
                with self.subTest(lengthAlong=along, gap=gap):
                    self.seed_fill(lengthAlong=along, gap=gap)
                    self.engineering_apply([snapshot_op(identifier=0, name="同名")])
                    self.assert_axes(self.systems()[0], size=sizes, gap=gap)
                    result = self.query(0)
                    for a, axis in enumerate("uv"):
                        expected = [(k, (-19, 23)[a] + sizes[a] + gap // 2 + k * (sizes[a] + gap))
                                    for k in range(-20, 21)
                                    if -450 <= (-19, 23)[a] + sizes[a] + gap // 2 + k * (sizes[a] + gap) <= 450]
                        actual = [(int(row["index"]), row["coordinate"])
                                  for row in result["axes"][axis]["lines"]]
                        self.assertEqual(expected, actual, "PF4B_SIGNED_UNBOUNDED_ORACLE")
                        self.assertTrue(any(k < -1 for k, _ in actual), "PF4B_NOT_VISIBLE_EXPLICIT_COPY")

    def test_PF4B_03_stagger_both_axes_signed_cells_and_negative_side(self):
        rect = (-220, -220, 270, 270)
        sizes, anchors = (83, 127), (-19, 23)
        for axis in (0, 1):
            for delta in (-17, 20):
                for gap, side in ((0, -1), (0, 1), (3, -1), (3, 1)):
                    with self.subTest(axis=axis, delta=delta, side=side, gap=gap):
                        self.seed_fill(gap=gap, pattern="stagger", stagger={"axis": "uv"[axis], "value": delta})
                        self.apply([pf1.put(pf1.surface(boundary=8, origin=(0, 0, 0), side=side, obstacles=[]))])
                        self.engineering_apply([snapshot_op()])
                        self.assert_axes(self.systems()[71], gap=gap, stagger=("uv"[axis], delta))
                        rows = self.query(rect=rect)["axes"]["uv"[axis]]["lines"]
                        actual = sorted((int(line["index"]), int(seg["band"]), tuple(seg["a"]), tuple(seg["b"]))
                                        for line in rows for seg in line["segments"])
                        expected = []
                        other = 1 - axis
                        for k in range(-8, 9):
                            for p in range(-8, 9):
                                c = anchors[axis] + sizes[axis] + gap // 2 + k * (sizes[axis] + gap)
                                c += delta if p % 2 else 0
                                b0 = anchors[other] + sizes[other] + gap // 2 + (p - 1) * (sizes[other] + gap)
                                b1 = b0 + sizes[other] + gap
                                lo, hi = max(rect[other], b0), min(rect[other + 2], b1)
                                if rect[axis] <= c <= rect[axis + 2] and lo < hi:
                                    a, b = [0, 0], [0, 0]
                                    a[axis] = b[axis] = c
                                    a[other], b[other] = lo, hi
                                    expected.append((k, p - 1, tuple(a), tuple(b)))
                        self.assertEqual(sorted(expected), actual, "PF4B_R44_SIGNED_BAND_CELL_ORACLE")

    def test_PF4B_04_snapshot_survives_fill_edit_and_source_deletion(self):
        self.seed_fill()
        self.engineering_apply([snapshot_op()])
        saved, lines = self.systems()[71], self.query()
        self.layout(pf2.fill(origin=[40, -30], gap=5, lengthAlong="u"))
        self.assertEqual(saved, self.systems()[71], "PF4B_NO_FILL_LIVE_REFERENCE")
        self.apply([{"op": "delete-panel-fill", "id": 1}, {"op": "delete-finish-surface", "id": 1}])
        self.engineering_apply([{"op": "delete-parameter", "id": 90}])
        self.assertEqual(saved, self.systems()[71], "PF4B_NO_SOURCE_CLOSURE_DEPENDENCY")
        self.assertEqual(lines, self.query(), "PF4B_QUERY_SURVIVES_SOURCE_REMOVAL")

    def test_PF4B_05_parameter_capture_uses_each_ordered_step(self):
        self.seed(width=83, length=127)
        self.engineering_apply([parameter()])
        self.layout(pf2.fill(origin=[-19, 23], gap={"parameterId": 91, "fieldId": 1},
                            pattern="stagger", stagger={"axis": "u", "value": {"parameterId": 91, "fieldId": 2}}))
        self.engineering_apply([parameter("5", "20"), snapshot_op(71),
                                parameter("7", "-13"), snapshot_op(72), parameter("9", "21")])
        self.assert_axes(self.systems()[71], gap=5, stagger=("u", 20))
        self.assert_axes(self.systems()[72], gap=7, stagger=("u", -13))
        self.engineering_apply([parameter("11", "23")])
        self.assert_axes(self.systems()[71], gap=5, stagger=("u", 20))
        self.assert_axes(self.systems()[72], gap=7, stagger=("u", -13))

    def test_PF4B_06_invalid_capture_cannot_borrow_future_valid_parameter(self):
        self.seed(width=83, length=127)
        self.engineering_apply([parameter()])
        self.layout(pf2.fill(gap={"parameterId": 91, "fieldId": 1}))
        self.reject_export([parameter("1/2"), snapshot_op(), parameter("3")], "integer")
        self.reject_export([parameter("-1"), snapshot_op(), parameter("3")], "nonnegative")
        self.reject_export([{"op": "delete-parameter", "id": 91}, snapshot_op(), parameter()], "MISSING")

    def test_PF4B_07_unrelated_transient_parameter_does_not_block_capture(self):
        self.seed_fill()
        invalid = {"id": 3, "name": "暫時", "type": "dimension", "input": "=1 mm/0"}
        repaired = dict(invalid, input="4")
        self.engineering_apply([parameter(extra_fields=[invalid]), parameter(extra_fields=[repaired])])
        self.engineering_apply([parameter(extra_fields=[invalid]), snapshot_op(), parameter(extra_fields=[repaired])])
        self.assert_axes(self.systems()[71])

    def test_PF4B_08_create_only_ids_names_and_scope(self):
        self.seed_fill()
        self.engineering_apply([snapshot_op(0, name="同名"), snapshot_op(71, name="同名")])
        self.assertEqual({0, 71}, set(self.systems()), "PF4B_NAME_IS_NOT_IDENTITY")
        for operation, reason in ((snapshot_op(71), "NEW_ID"), (snapshot_op(72, fill_id=99), "MISSING_FILL"),
                                  (snapshot_op(72, name=""), "NAME"), (snapshot_op(72, name="x\ny"), "NAME"),
                                  (snapshot_op(72, name="界" * 33), "NAME"), (snapshot_op(72, main="auto"), "MAIN_ALONG"),
                                  (snapshot_op(72, bind=True), "INPUT"), (snapshot_op(-1), "INPUT")):
            with self.subTest(reason=reason, operation=operation):
                self.reject_export([operation], reason)

    def test_PF4B_09_collision_inside_batch_rolls_back_all_exports(self):
        self.seed_fill()
        self.reject_export([snapshot_op(71), snapshot_op(72), snapshot_op(71)], "NEW_ID")
        self.assertEqual({}, self.systems(), "PF4B_NO_PREFIX_COMMIT")

    def test_PF4B_10_capacity_is_existing_sixteen_and_atomic(self):
        self.seed_fill()
        self.engineering_apply([snapshot_op(i) for i in range(16)])
        self.assertEqual(16, len(self.systems()))
        self.reject_export([snapshot_op(16)], "CAPACITY")

    def test_PF4B_11_preview_cancel_stale_and_one_step_history(self):
        self.seed_fill()
        before = self.snapshot()
        preview = self.engineering_preview([snapshot_op()])
        self.assertTrue(preview["valid"], ("PF4B_EXPORT_ACCEPT", preview["violations"]))
        self.assertTrue(self.command("engineering-cancel %d" % preview["token"])["cancelled"])
        self.assertEqual(before, self.snapshot(), "PF4B_CANCEL_ZERO_WRITE")
        preview = self.engineering_preview([snapshot_op()])
        self.commit_line("spec unrelated 4")
        self.assertFalse(self.command("engineering-confirm %d" % preview["token"])["ok"], "PF4B_STALE")
        self.assertEqual({}, self.systems(), "PF4B_STALE_ZERO_WRITE")
        before_dump = self.command("dump")["text"]
        self.engineering_apply([snapshot_op(71), snapshot_op(72)])
        after_dump = self.command("dump")["text"]
        self.commit_line("undo")
        self.assertEqual(before_dump, self.command("dump")["text"], "PF4B_BATCH_ONE_UNDO")
        self.commit_line("redo")
        self.assertEqual(after_dump, self.command("dump")["text"], "PF4B_BATCH_ONE_REDO")

    def test_PF4B_12_standalone_cold_reopen_and_normal_D29_edit(self):
        self.seed_fill()
        self.engineering_apply([snapshot_op()])
        expected = self.query()
        record, = [line for line in self.command("dump")["text"].splitlines() if line.startswith("grid-system ")]
        self.assertNotIn("param:", record, "PF4B_DUMP_DIRECT_VALUES")
        self.assertNotIn("fill", record, "PF4B_NO_NEW_SNAPSHOT_RECORD")
        self.load_text(record + "\n", "snapshot-only.scene")
        self.assertEqual(expected, self.query(), "PF4B_REOPEN_NO_ORIGINAL_CLOSURE")
        self.assertEqual([], self.read()["state"]["panelFills"])
        with pf1.BridgeSession(self.binary, cwd=self.directory) as reopened:
            self.assertTrue(reopened.command("loadfile " + str(self.directory / "snapshot-only.scene"))["ok"])
            cold = reopened.command("grid-query system 71 rect -450 -450 450 450 mode exact limit 64")
            self.assertEqual(expected, cold, "PF4B_FRESH_PROCESS_NO_ORIGINAL_CLOSURE")
            self.assertEqual([], reopened.command("panel-fill-read")["state"]["panelFills"])
        self.commit_line("grid-system 71 name-hex 47 main-along none u repeat-panel 90 gap 5 from 11 v repeat-panel 140 gap 5 from 22")
        self.assert_axes(self.systems()[71], size=(90, 140), gap=5, origin=(11, 22))

    def test_PF4B_13_ordinary_D30_binding_reanchors_the_snapshot(self):
        self.seed_fill()
        self.engineering_apply([snapshot_op()])
        geometry = self.command("boundary 8")
        self.assertTrue(geometry["ok"], geometry)
        self.commit_line("grid-binding 5 on-boundary 8 from-system 71 vertex outer 0 geometry-hash "
                         + geometry["geometryFingerprint"] + " cell 0 0 anchor 0 1 0 1")
        binding, = self.command("objects")["gridBindings"]
        self.assertEqual([-65, -151], binding["translation"], "PF4B_D30_ORDINARY_ANCHOR_TRANSLATION")
        self.assert_axes(self.systems()[71])

    def test_PF4B_14_existing_unsupported_overrides_are_never_ignored(self):
        self.seed_fill()
        before = self.snapshot()
        operation = pf2.fill(seamOverrides=[{"axis": "u", "k": "0", "coordinate": 101}])
        preview = self.preview([operation])
        self.assertFalse(preview["valid"], "PF4B_BASE_HAS_NO_SEAM_OVERRIDE_CAPABILITY")
        self.assertIn("D42", json.dumps(preview["violations"]))
        self.assertEqual(before, self.snapshot(), "PF4B_UNKNOWN_DEFINITION_ZERO_WRITE")

    def test_PF4B_15_shifted_anchor_must_stay_in_D1(self):
        self.seed(width=83, length=127)
        self.layout(pf2.fill(origin=[100000000, 0], pattern="stagger", stagger={"axis": "u", "value": 20}))
        self.reject_export([snapshot_op()], "R44 D1")

    def test_PF4B_16_zero_gap_and_large_negative_stagger_are_exact(self):
        self.seed_fill(gap=0, pattern="stagger", stagger={"axis": "v", "value": -500})
        self.engineering_apply([snapshot_op()])
        self.assert_axes(self.systems()[71], gap=0, stagger=("v", -500))


if __name__ == "__main__":
    unittest.main()
