"""Q38 native slice: independent numeric oracles against the real C bridge.

This gate does not certify the model renderer, UI, .gcanvas or simple placement.
"""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests._bridge import BridgeSession, find_bridge


def literal(value):
    return {"kind": "literal", "value": value}


def profile(identifier=1, outline=None):
    return {"id": identifier, "name": "L 斷面", "outline": outline or
            [[0, 0], [400, 0], [400, 60], [60, 60], [60, 250], [0, 250]]}


def member(identifier=1, u=0, v=0, **extra):
    return {"id": identifier, "profileId": 1, "kind": "timber", "A": literal(27),
            "B": literal(33), "orientation": "A-u", "u0": u, "v0": v, **extra}


def panel(identifier=4, u=27, v=0, width=346, **extra):
    return {"id": identifier, "profileId": 1, "kind": "panel", "panelSpec": "calcium-silicate-6",
            "width": width, "orientation": "thickness-v", "u0": u, "v0": v, **extra}


def run(identifier=1, **extra):
    return {"id": identifier, "profileId": 1, "length": literal(2400), "placement": None, **extra}


def put(kind, value):
    return {"op": "put-" + kind, "value": value}


class SectionProfileNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-q38-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bridge = BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.command("reset")

    def command(self, text):
        return self.bridge.command(text)

    def read(self):
        result = self.command("section-profile-read")
        self.assertTrue(result["ok"], result)
        return result

    def snapshot(self):
        return self.command("dump")["text"], self.read()["revision"]

    def preview(self, operations, revision=None):
        path = self.directory / "transaction.json"
        path.write_text(json.dumps({"schema": "section-profile-transaction/1",
                                   "expectedRevision": self.read()["revision"] if revision is None else revision,
                                   "operations": operations}, ensure_ascii=False), encoding="utf-8")
        result = self.command("section-profile-preview " + str(path))
        self.assertTrue(result["ok"], result)
        return result["preview"]

    def apply(self, operations):
        preview = self.preview(operations)
        self.assertTrue(preview["valid"], preview)
        done = self.command(f'section-profile-confirm {preview["token"]}')
        self.assertTrue(done["ok"], done)
        return preview, done

    def reject(self, operations, reason):
        before = self.snapshot()
        preview = self.preview(operations)
        self.assertFalse(preview["valid"], preview)
        self.assertIn(reason, json.dumps(preview, ensure_ascii=False))
        self.assertFalse(self.command(f'section-profile-confirm {preview["token"]}')["ok"])
        self.assertEqual(before, self.snapshot())
        return preview

    def reject_fractional_json(self, operations):
        before = self.snapshot()
        path = self.directory / "fractional.json"
        path.write_text(json.dumps({"schema": "section-profile-transaction/1", "expectedRevision": self.read()["revision"],
                                   "operations": operations}), encoding="utf-8")
        result = self.command("section-profile-preview " + str(path))
        self.assertFalse(result["ok"], result)
        self.assertEqual("JSON", result["code"])
        self.assertIn("Floating-point", result["error"])
        self.assertEqual(before, self.snapshot())

    def fixture(self):
        values = [member(), member(2, 373), member(3, 0, 223, orientation="A-v")]
        self.apply([put("profile", profile()), *[put("member", m) for m in values], put("run", run())])

    def test_ac01_03_08_independent_rectangles_volumes_and_scope(self):
        self.fixture()
        state = self.read()
        self.assertFalse(state["rendererSupported"])
        self.assertFalse(state["simplePlacementSupported"])
        self.assertNotIn("section-profile/1", state["capabilities"])
        self.assertIn("section-profile/1", state["required_capabilities"])
        self.assertIn("section-profile-native/1", state["native_capabilities"])
        records = state["state"]["members"]
        self.assertEqual([[0, 0, 27, 33], [373, 0, 400, 33], [0, 223, 33, 250]], [r["rect"] for r in records])
        r = state["state"]["runs"][0]
        self.assertEqual("local", r["coordinateSpace"])
        self.assertIsNone(r["frame"])
        volumes = []
        for record in r["members"]:
            lo, hi = record["bounds"]
            volumes.append((hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2]))
        self.assertEqual([2138400] * 3, volumes)
        self.assertEqual(6415200, sum(volumes))
        self.assertEqual([], self.command("objects")["timbers"])
        self.assertEqual([], self.command("surfaces")["surfaces"])

    def test_concave_not_four_corners_and_winding(self):
        outline = [[0, 0], [100, 0], [100, 100], [60, 100], [60, 40], [40, 40], [40, 100], [0, 100]]
        for vertices in (outline, list(reversed(outline))):
            self.apply([put("profile", profile(outline=vertices))])
            self.reject([put("member", member(u=20, v=20, A=literal(60), B=literal(60)))], "V_PROFILE_OUTSIDE")

    def test_touch_edges_points_and_cross_kind_overlap(self):
        self.apply([put("profile", profile()), put("member", member())])
        self.apply([put("member", member(2, 27)), put("member", member(3, 27, 33, A=literal(1), B=literal(1)))])
        self.reject([put("member", member(2, 26))], "intersection [26,27]x[0,33]")
        self.reject([put("member", panel(u=20, width=30))], "V_PROFILE_OVERLAP")
        self.apply([put("profile", profile(2)), put("member", member(4, profileId=2))])

    def test_profile_geometry_and_coordinate_rejections(self):
        self.apply([put("profile", profile())])
        for outline in ([[0, 0], [1, 0], [1, 1]], [[0, 0], [10, 0], [10, 0], [0, 10]],
                        [[0, 0], [10, 1], [10, 10], [0, 10]],
                        [[0, 0], [10, 0], [10, 10], [5, 10], [5, -5], [0, -5]],
                        [[0, 0], [100000001, 0], [100000001, 1], [0, 1]]):
            self.reject([put("profile", profile(outline=outline))], "I43")
        self.reject_fractional_json([put("member", member(u=0.5))])
        for coordinate in ("1/2", 100000001, True):
            self.reject([put("member", member(u=coordinate))], "I46")
        self.reject([put("member", member(3, 0, 223))], "V_PROFILE_OUTSIDE")

    def test_panel_strict_width_fixed_spec_and_long_run(self):
        self.apply([put("profile", profile(outline=[[0, 0], [1000, 0], [1000, 100], [0, 100]])),
                    put("member", panel(u=0, width=914)), put("run", run(length=literal(2000)))])
        p = self.read()["state"]["members"][0]
        self.assertEqual([0, 0, 914, 6], p["rect"])
        bounds = self.read()["state"]["runs"][0]["members"][0]["bounds"]
        self.assertEqual([[0, 0, 0], [914, 6, 2000]], bounds)
        self.assertEqual(10968000, 914 * 6 * 2000)
        self.reject_fractional_json([put("member", panel(u=0, width=1.5))])
        for width in (0, 915, -1):
            self.reject([put("member", panel(u=0, width=width))], "V_PANEL_WIDTH")
        self.reject([put("member", panel(u=0, width=914, thickness=9))], "D40/I46")
        self.apply([put("member", panel(u=0, width=1, orientation="thickness-u"))])
        self.assertEqual([0, 0, 6, 1], self.read()["state"]["members"][0]["rect"])

    def test_ac09_advanced_axes_and_vertex_range(self):
        self.fixture()
        placement = {"kind": "advanced", "origin": [1000, 2000, 2700], "N": "+Y", "V": "-Z"}
        self.apply([put("run", run(placement=placement))])
        r = self.read()["state"]["runs"][0]
        self.assertEqual([1, 0, 0], r["frame"]["U"])
        self.assertEqual([[1000, 2000, 2667], [1027, 4400, 2700]], r["members"][0]["bounds"])
        self.reject([put("run", run(placement={**placement, "N": "-Z"}))], "I48")
        self.reject([put("run", run(placement={**placement, "origin": [100000000, 0, 0]}))], "I47/I48/D1")
        self.reject([put("run", run(placement={"kind": "simple"}))], "UNSUPPORTED")
        self.reject_fractional_json([put("run", run(length=literal(1.5)))])
        for length in (0, -1, 100000001):
            self.reject([put("run", run(length=literal(length)))], "I")

    def test_atomic_preview_cancel_wrong_kind_stale_undo_redo(self):
        empty = self.command("dump")["text"]
        before = self.snapshot()
        preview = self.preview([put("profile", profile()), put("member", member()), put("run", run())])
        self.assertEqual(before, self.snapshot())
        for command in ("engineering-confirm", "assembly-confirm", "line confirm"):
            self.assertFalse(self.command(f'{command} {preview["token"]}')["ok"])
        self.assertTrue(self.command(f'section-profile-cancel {preview["token"]}')["cancelled"])
        self.assertEqual(before, self.snapshot())
        self.fixture()
        complete = self.command("dump")["text"]
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(empty, self.command("dump")["text"])
        self.reject([put("profile", profile(outline=[[0, 0]]))], "I43")
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(complete, self.command("dump")["text"])
        preview = self.preview([put("run", run(length=literal(3000)))])
        self.assertTrue(self.command("line undo")["ok"])
        stale_before = self.snapshot()
        self.assertFalse(self.command(f'section-profile-confirm {preview["token"]}')["ok"])
        self.assertEqual(stale_before, self.snapshot())

    def test_shrink_reject_and_expand_loses_right_contact(self):
        self.fixture()
        smaller = profile()
        smaller["outline"][1][0] = smaller["outline"][2][0] = 390
        self.reject([put("profile", smaller)], "V_PROFILE_OUTSIDE")
        bigger = profile()
        bigger["outline"][1][0] = bigger["outline"][2][0] = 420
        preview, _ = self.apply([put("profile", bigger)])
        self.assertIn({"code": "PROFILE_CONTACT_LOST", "clause": "I49", "memberId": 2, "profileId": 1},
                      preview["sectionProfiles"]["warnings"])
        self.assertEqual([373, 0, 400, 33], self.read()["state"]["members"][1]["rect"])

    def test_named_sources_rebuild_and_explicit_dependency_transaction(self):
        self.apply([{"op": "put-spec", "name": "A", "value": 27}, put("profile", profile()),
                    put("member", member(A={"kind": "spec", "name": "A"})), put("member", member(2, 27)), put("run", run())])
        self.reject([{"op": "put-spec", "name": "A", "value": 28}], "V_PROFILE_OVERLAP")
        self.reject([{"op": "delete-spec", "name": "A"}], "missing")
        self.reject([{"op": "delete-profile", "id": 1}], "I49")
        before = self.snapshot()
        denied = self.command("line spec A 28")
        self.assertFalse(denied["ok"])
        self.assertEqual(before, self.snapshot())
        self.apply([{"op": "put-spec", "name": "A", "value": 28}, put("member", member(2, 28))])
        self.assertEqual([0, 0, 28, 33], self.read()["state"]["members"][0]["rect"])
        self.apply([{"op": "delete-profile", "id": 1}, {"op": "delete-member", "id": 1},
                    {"op": "delete-member", "id": 2}, {"op": "delete-run", "id": 1}])
        self.assertEqual([], self.read()["required_capabilities"])

    def test_parameter_zero_ids_types_and_fixed_material_sources_roundtrip(self):
        parameter = {"id": 0, "name": "source", "fields": [{"id": 0, "name": "A", "type": "dimension", "input": "27"}]}
        material = {"id": "q38-timber", "version": 1, "kind": "timber", "name": "fixed section", "A": 27, "B": 33}
        a_source = {"kind": "parameter", "parameterId": 0, "fieldId": 0}
        b_source = {"kind": "material", "id": "q38-timber", "version": 1, "field": "B"}
        expected = member(A=a_source, B=b_source, orientation="A-v")
        self.apply([{"op": "put-parameter", "value": parameter}, {"op": "publish-material", "value": material},
                    put("profile", profile()), put("member", expected), put("run", run(length=a_source))])
        self.assertEqual([0, 0, 33, 27], self.read()["state"]["members"][0]["rect"])
        saved = self.command("dump")["text"]
        path = self.directory / "sources.scene"
        path.write_text(saved, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(saved, self.command("dump")["text"])
        self.assertEqual(expected, self.read()["state"]["members"][0]["value"])
        self.apply([{"op": "publish-material", "value": {**material, "version": 2, "B": 34}}])
        self.assertEqual([0, 0, 33, 27], self.read()["state"]["members"][0]["rect"])
        self.reject([put("member", member(A=a_source, B={**b_source, "field": "A"}))], "D36")
        for field_type, value in (("count", "27"), ("ratio", "27"), ("dimension", "1.5"), ("dimension", "0")):
            bad = deepcopy(parameter)
            bad["fields"][0].update(type=field_type, input=value)
            self.reject([{"op": "put-parameter", "value": bad}], "I")
        self.reject([{"op": "delete-parameter", "id": 0}], "I")
        changed = deepcopy(parameter)
        changed["fields"][0]["input"] = "29"
        self.apply([{"op": "put-parameter", "value": changed}])
        state = self.read()["state"]
        self.assertEqual([0, 0, 33, 29], state["members"][0]["rect"])
        self.assertEqual(29, state["runs"][0]["length"])
        self.assertEqual(expected, state["members"][0]["value"])

    def test_exact_dump_load_zero_ids_empty_profile_and_fail_closed(self):
        value = profile(0, [[-2, -2], [-1, -2], [-1, -1], [-2, -1]])
        self.apply([put("profile", value), put("run", run(0, profileId=0, length=literal(100000000))), put("profile", profile(1))])
        expected = self.command("dump")["text"]
        path = self.directory / "world.scene"
        path.write_text(expected, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(expected, self.command("dump")["text"])
        payloads = [json.loads(base64.b64decode(line.split()[2])) for line in expected.splitlines() if line.startswith("section-profile ")]
        self.assertIn(value, payloads)
        before = self.snapshot()
        variants = [expected.replace("requires section-profile/1\n", ""),
                    expected.replace("section-profile/1", "section-profile/99"),
                    expected + next(line for line in expected.splitlines() if line.startswith("section-profile profile ")) + "\n"]
        for content in variants:
            path.write_text(content, encoding="utf-8")
            self.assertFalse(self.command("loadfile " + str(path))["ok"])
            self.assertEqual(before, self.snapshot())
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            path.write_text(expected, encoding="utf-8")
            self.assertTrue(fresh.command("loadfile " + str(path))["ok"])
            self.assertEqual(expected, fresh.command("dump")["text"])

    def test_each_capacity_rejects_without_partial_writes(self):
        limits = self.read()["capacity"]
        self.apply([put("profile", profile(i, [[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) for i in range(limits["profiles"])])
        self.reject([put("profile", profile(limits["profiles"]))], "CAPACITY")
        self.apply([put("member", member(i, i * 2, 0, profileId=0, A=literal(1), B=literal(1))) for i in range(limits["members"])])
        self.reject([put("member", member(limits["members"], 999, profileId=0, A=literal(1), B=literal(1)))], "CAPACITY")
        self.apply([put("run", run(i, profileId=0)) for i in range(limits["runs"])])
        self.reject([put("run", run(limits["runs"], profileId=0))], "CAPACITY")
        expected = self.command("dump")["text"]
        path = self.directory / "capacity.scene"
        path.write_text(expected, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(expected, self.command("dump")["text"])

    def test_legacy_consumers_refuse_or_report_incomplete(self):
        from tests import binaries
        binary = os.environ.get("GEOMETRY_MODEL_BASE") or str(binaries.BY_NAME["model-base"].path)
        self.apply([put("profile", profile())])
        self.assertFalse(self.command("source-inspect")["complete"])
        path = self.directory / "legacy.scene"
        complete = self.command("dump")["text"]
        for content in (complete, complete.replace("requires section-profile/1\n", ""), "requires section-profile/1\n"):
            path.write_text(content, encoding="utf-8")
            result = subprocess.run([binary, str(path)], capture_output=True, text=True)
            self.assertEqual(1, result.returncode, result.stderr)
            reply = json.loads(result.stdout)
            self.assertEqual(("UNSUPPORTED", "CAPABILITY", "I32"), (reply["status"], reply["code"], reply["clause"]))
        path.write_text("spec old 27\n", encoding="utf-8")
        result = subprocess.run([binary, str(path)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.command("reset")
        self.assertTrue(self.command("source-inspect")["complete"])


if __name__ == "__main__":
    unittest.main()
