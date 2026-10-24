"""Q38 native slice: independent numeric oracles against the real C bridge.

This gate certifies native definitions, geometry, simple placement and history; UI/model gates are separate.
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
        self.assertTrue(preview["valid"], "expected the candidate to be accepted: %s" % preview)
        done = self.command(f'section-profile-confirm {preview["token"]}')
        self.assertTrue(done["ok"], done)
        return preview, done

    def reject(self, operations, reason):
        before = self.snapshot()
        preview = self.preview(operations)
        self.assertFalse(preview["valid"], "expected rejection %r but the candidate was accepted: %s" % (reason, preview))
        self.assertIn(reason, json.dumps(preview, ensure_ascii=False), "rejected, but not for %r" % reason)
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

    def legacy_source_fixture(self, source):
        for line in ("surface 7 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
                     "timber 11 27 33 role boundary", "place 11 on 7 at-face e0 +u +n",
                     "timber 12 27 33 role boundary", "place 12 on 7 at-face e2 +u +n",
                     "guide 19 7 v " + source, "timber 23 27 33 role primary",
                     "place 23 on 7 at-line guide 19 +v +n"):
            result = self.command("line " + line)
            if line == "guide 19 7 v " + source and source.startswith("param:"):
                self.assertFalse(result["ok"], result)
                self.assertTrue(result["preview"]["valid"], result)
                result = self.command(f'line confirm {result["preview"]["token"]}')
            self.assertTrue(result["ok"], result)

    def assert_legacy_impact(self, state, center):
        geometry = state["geometry"]
        guide = next(g for g in geometry["guides"] if g["id"] == 19)
        timber = next(t for t in geometry["timbers"] if t["id"] == 23)["geometry"]
        self.assertEqual(center, guide["off"])
        self.assertEqual([center, 0, 2500], guide["worldPoint"])
        self.assertEqual(center, timber["centerline"])
        self.assertEqual([center + 14, 27, 2500], timber["origin"])
        self.assertEqual(2946, timber["length"])

    def assert_live_matches_preview(self, state):
        references = self.command("references")
        self.assertEqual(state["geometry"]["guides"], references["guides"])
        self.assertEqual([(t["id"], t["geometry"]) for t in state["geometry"]["timbers"]],
                         [(t["id"], t["geometry"]) for t in references["timbers"]])
        self.assertEqual(state["sectionProfiles"], self.read()["state"])
        current = self.command("engineering-read")["state"]
        for key in ("specs", "parameters", "materials", "methods", "applications", "sources"):
            self.assertEqual(state[key], current[key])

    def test_named_spec_preview_discloses_legacy_geometry_without_profiles(self):
        self.assertTrue(self.command("line spec SharedAxis 500")["ok"])
        self.legacy_source_fixture("spec:SharedAxis")
        before = self.snapshot()
        preview = self.preview([{"op": "put-spec", "name": "SharedAxis", "value": 600}])
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([{"name": "SharedAxis", "value": 500}], preview["before"]["specs"])
        self.assertEqual([{"name": "SharedAxis", "value": 600}], preview["after"]["specs"])
        self.assert_legacy_impact(preview["before"], 500)
        self.assert_legacy_impact(preview["after"], 600)
        self.assertEqual([], preview["after"]["sectionProfiles"]["profiles"])
        self.assertTrue(self.command(f'section-profile-confirm {preview["token"]}')["ok"])
        self.assert_live_matches_preview(preview["after"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assert_live_matches_preview(preview["before"])
        self.assertEqual(before[0], self.command("dump")["text"])

    def test_shared_parameter_preview_cancel_tokens_and_history_both_domains(self):
        parameter = {"id": 37, "name": "shared dimension", "fields":
                     [{"id": 5, "name": "value", "type": "dimension", "input": "500"}]}
        source = {"kind": "parameter", "parameterId": 37, "fieldId": 5}
        self.apply([{"op": "put-parameter", "value": parameter},
                    put("profile", profile(3, [[0, 0], [1000, 0], [1000, 1000], [0, 1000]])),
                    put("member", member(17, profileId=3, A=source)),
                    put("run", run(29, profileId=3, length=source))])
        self.legacy_source_fixture("param:37:5")
        before = self.snapshot()
        changed = deepcopy(parameter)
        changed["fields"][0]["input"] = "600"
        operations = [{"op": "put-parameter", "value": changed}]
        preview = self.preview(operations)
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.snapshot())
        self.assert_legacy_impact(preview["before"], 500)
        self.assert_legacy_impact(preview["after"], 600)
        for key, size in (("before", 500), ("after", 600)):
            state = preview[key]
            self.assertEqual({"op": "literal", "num": str(size), "den": "1", "unit": "mm"},
                             state["parameters"][0]["fields"][0]["expression"])
            self.assertEqual([0, 0, size, 33], state["sectionProfiles"]["members"][0]["rect"])
            self.assertEqual(size, state["sectionProfiles"]["runs"][0]["length"])
            self.assertEqual([[0, 0, 0], [size, 33, size]],
                             state["sectionProfiles"]["runs"][0]["members"][0]["bounds"])
        for command in ("engineering-confirm", "assembly-confirm", "line confirm"):
            self.assertFalse(self.command(f'{command} {preview["token"]}')["ok"])
            self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command(f'section-profile-cancel {preview["token"]}')["cancelled"])
        self.assertEqual(before, self.snapshot())
        self.assert_live_matches_preview(preview["before"])
        preview = self.preview(operations)
        done = self.command(f'section-profile-confirm {preview["token"]}')
        self.assertTrue(done["ok"], done)
        self.assertEqual(before[1] + 1, done["revision"])
        self.assert_live_matches_preview(preview["after"])
        complete = self.command("dump")["text"]
        stale = self.preview(operations)
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before[0], self.command("dump")["text"])
        self.assert_live_matches_preview(preview["before"])
        undone = self.snapshot()
        self.assertFalse(self.command(f'section-profile-confirm {stale["token"]}')["ok"])
        self.assertEqual(undone, self.snapshot())
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(complete, self.command("dump")["text"])
        self.assert_live_matches_preview(preview["after"])

    def test_source_only_native_preview_discloses_material_publication(self):
        material = {"id": "preview-only", "version": 1, "kind": "timber",
                    "name": "source without consumers", "A": 27, "B": 33}
        before = self.snapshot()
        preview = self.preview([{"op": "publish-material", "value": material}])
        self.assertTrue(preview["valid"], preview)
        self.assertEqual([], preview["before"]["materials"])
        self.assertEqual(material, {k: preview["after"]["materials"][0][k] for k in material})
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command(f'section-profile-confirm {preview["token"]}')["ok"])
        self.assert_live_matches_preview(preview["after"])

    def test_ac01_03_08_independent_rectangles_volumes_and_scope(self):
        self.fixture()
        state = self.read()
        self.assertTrue(state["simplePlacementSupported"])
        self.assertTrue(state["diagnosticsComplete"])
        self.assertIn("section-profile/1", state["capabilities"])
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
            # I44/D35: every corner of these rectangles lies on an outline edge and no edge crosses their interior,
            # yet each one fills the notch, i.e. lies wholly outside F.
            for u0, v0, a, b, region in ((40, 50, 20, 20, [40, 50, 60, 70]), (40, 40, 20, 60, [40, 40, 60, 100]),
                                         (40, 60, 20, 40, [40, 60, 60, 100])):
                preview = self.reject([put("member", member(u=u0, v=v0, A=literal(a), B=literal(b)))], "V_PROFILE_OUTSIDE")
                self.assertEqual([[region]], [v["outsideRegions"] for v in preview["violations"] if v["code"] == "V_PROFILE_OUTSIDE"])
            # Touching the notch edge from the material side is contained (closed region), not outside.
            for u0, v0, a, b in ((40, 0, 20, 40), (0, 40, 40, 60), (60, 40, 40, 60)):
                self.apply([put("member", member(u=u0, v=v0, A=literal(a), B=literal(b)))])
                self.apply([{"op": "delete-member", "id": 1}])
        opens_right = [[0, 0], [100, 0], [100, 40], [30, 40], [30, 70], [100, 70], [100, 100], [0, 100]]
        self.apply([put("profile", profile(outline=opens_right))])
        preview = self.reject([put("member", member(u=50, v=40, A=literal(30), B=literal(20), orientation="A-v"))], "V_PROFILE_OUTSIDE")
        self.assertEqual([[[50, 40, 70, 70]]], [v["outsideRegions"] for v in preview["violations"] if v["code"] == "V_PROFILE_OUTSIDE"])

    def test_member_in_notch_with_corners_on_walls_is_outside_i44(self):
        # GEO-257:槽 x∈[40,60]、y∈[40,100] 在輪廓外。成員矩形 [40,60]x[50,70] 四角都落在槽壁上、
        # 沒有任何輪廓邊穿過內部,但整塊在槽裡 → I44 必須拒絕,且差集精確等於整個成員矩形。
        outline = [[0, 0], [100, 0], [100, 100], [60, 100], [60, 40], [40, 40], [40, 100], [0, 100]]
        for vertices in (outline, list(reversed(outline))):
            self.apply([put("profile", profile(outline=vertices))])
            preview = self.reject([put("member", member(u=40, v=50, A=literal(20), B=literal(20)))], "V_PROFILE_OUTSIDE")
            outside = [v for v in preview["violations"] if v["code"] == "V_PROFILE_OUTSIDE"]
            self.assertEqual([[[40, 50, 60, 70]]], [v["outsideRegions"] for v in outside])
            # 對照組:同樣貼槽壁/槽底、但真的在輪廓內的成員必須接受。
            accepted, _ = self.apply([put("member", member(1, 0, 50, A=literal(40), B=literal(20))),
                                      put("member", member(2, 40, 0, A=literal(20), B=literal(40)))])
            self.assertEqual([[0, 50, 40, 70], [40, 0, 60, 40]],
                             [m["rect"] for m in accepted["sectionProfiles"]["after"]["members"]])
            self.apply([{"op": "delete-member", "id": 1}, {"op": "delete-member", "id": 2}])

    def test_touch_edges_points_and_cross_kind_overlap(self):
        self.apply([put("profile", profile()), put("member", member())])
        self.apply([put("member", member(2, 27)), put("member", member(3, 27, 33, A=literal(1), B=literal(1)))])
        preview=self.reject([put("member", member(2, 26))], "V_PROFILE_OVERLAP")
        self.assertEqual([26,0,27,33],preview["violations"][0]["intersection"])
        self.reject([put("member", panel(u=20, width=30))], "V_PROFILE_OVERLAP")
        self.apply([put("profile", profile(2)), put("member", member(4, profileId=2))])

    def test_ac23_panel_width_346_touches_timbers_u(self):
        # AC23: the panel fills the 346 mm gap between M1 and M2.  I45/R36
        # permit the two shared edges; source-inspect/registry receipts are unrelated.
        self.apply([put("profile", profile()), put("member", member()),
                    put("member", member(2, 373))])
        self.apply([put("member", panel())])
        members = {m["value"]["id"]: m for m in self.read()["state"]["members"]}
        self.assertEqual([0, 0, 27, 33], members[1]["rect"])
        self.assertEqual([373, 0, 400, 33], members[2]["rect"])
        self.assertEqual([27, 0, 373, 6], members[4]["rect"])

    def test_ac23_panel_width_346_touches_timbers_v(self):
        # The same AC23 rectangles with u/v exchanged exercise the other strict
        # inequality, with exactly the same material dimensions and gap.
        outline = [[0, 0], [250, 0], [250, 60], [60, 60], [60, 400], [0, 400]]
        self.apply([put("profile", profile(outline=outline)),
                    put("member", member(orientation="A-v")),
                    put("member", member(2, 0, 373, orientation="A-v"))])
        self.apply([put("member", panel(u=0, v=27, orientation="thickness-u"))])
        members = {m["value"]["id"]: m for m in self.read()["state"]["members"]}
        self.assertEqual([0, 0, 33, 27], members[1]["rect"])
        self.assertEqual([0, 373, 33, 400], members[2]["rect"])
        self.assertEqual([0, 27, 6, 373], members[4]["rect"])

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
        self.reject([put("member", member(orientation="A-w"))], "timber orientation must be A-u or A-v")
        self.reject([put("member", panel(u=0, width=100, orientation="thickness-w"))], "panel orientation must be thickness-v or thickness-u")
        self.reject([put("member", panel(u=0, width=100, panelSpec="gypsum-board-9"))], "panel requires calcium-silicate-6")

    def test_panel_strict_width_fixed_spec_and_long_run(self):
        self.apply([put("profile", profile(outline=[[0, 0], [1000, 0], [1000, 100], [0, 100]])),
                    put("member", panel(u=0, width=914)), put("run", run(length=literal(2000)))])
        p = self.read()["state"]["members"][0]
        self.assertEqual([0, 0, 914, 6], p["rect"], "D40/R36: calcium-silicate-6 is 6 mm thick, thickness along v, w=914")
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
        self.reject([put("run", run(placement={"kind": "simple"}))], "explicit")
        self.reject_fractional_json([put("run", run(length=literal(1.5)))])
        for length, reason in ((0, "RUN_LENGTH_INVALID"), (-1, "I35: literal dimension"), (100000001, "I35: literal dimension")):
            self.reject([put("run", run(length=literal(length)))], reason)
        # I47/D1: the far end of the run is a generated vertex too; origin alone being legal is not enough.
        far = {**placement, "origin": [1000, 99998000, 2700]}
        self.apply([put("run", run(length=literal(2000), placement=far))])
        self.assertEqual([[1000, 99998000, 2667], [1027, 100000000, 2700]], self.read()["state"]["runs"][0]["members"][0]["bounds"])
        self.reject([put("run", run(length=literal(2001), placement=far))], "I47/I48/D1")
        self.reject([put("run", run(length=literal(2000), placement={**far, "origin": [1000, 99998001, 2700]}))], "I47/I48/D1")

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
        self.reject([{"op": "delete-profile", "id": 1}, {"op": "delete-member", "id": 1}, {"op": "delete-member", "id": 2}],
                    "I49")  # the run still references the profile
        self.reject([{"op": "delete-profile", "id": 1}, {"op": "delete-run", "id": 1}], "I49")  # the members still do
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
        self.reject([put("run", run(length={**b_source, "field": "A"}))], "unsupported dimension source")
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

    def test_delete_parameter_names_section_profile_member_and_run_referrers(self):
        # GEO-258:被斷面成員/擠出段引用的參數卡不得刪除,訊息指名引用者;先改成直接值再刪就通過。
        parameter = {"id": 0, "name": "source", "fields": [{"id": 0, "name": "A", "type": "dimension", "input": "27"}]}
        source = {"kind": "parameter", "parameterId": 0, "fieldId": 0}
        self.apply([{"op": "put-parameter", "value": parameter}, put("profile", profile()),
                    put("member", member(A=source)), put("run", run(length=source))])
        self.reject([{"op": "delete-parameter", "id": 0}],
                    "parameter 0 is still referenced by section-profile member 1 A; section-profile run 1 length")
        self.reject([put("member", member()), {"op": "delete-parameter", "id": 0}],
                    "parameter 0 is still referenced by section-profile run 1 length")
        # Rebuilding the key cannot acknowledge either surviving reference owner.
        deleted = {"op": "delete-parameter", "id": 0}
        rebuilt = {"op": "put-parameter", "value": parameter}
        declare_member = put("member", member(A=source))
        declare_run = put("run", run(length=source))
        self.reject([deleted, rebuilt], "section-profile member 1 A; section-profile run 1 length")
        self.reject([deleted, rebuilt, declare_member], "section-profile run 1 length")
        self.reject([deleted, rebuilt, declare_run], "section-profile member 1 A")
        self.reject([deleted, rebuilt, declare_member, declare_run, deleted, rebuilt], "section-profile member 1 A")
        preview, done = self.apply([deleted, rebuilt, declare_member, declare_run])
        self.assertEqual([{"kind": "section-profile-member", "id": 1, "slot": 0},
                          {"kind": "section-profile-run", "id": 1, "slot": 0}],
                         [r["owner"] for r in preview["redeclaredReferences"]])
        self.assertEqual([{"parameterId": 0, "fieldId": 0}] * 2,
                         [r["source"] for r in preview["redeclaredReferences"]])
        self.assertEqual([{"kind": "parameter-field", "parameterId": 0, "fieldId": 0}], done["deletedObjects"])
        self.apply([put("member", member()), put("run", run()), deleted])
        self.assertEqual([], self.command("engineering-read")["state"]["parameters"])

    def test_exact_dump_load_zero_ids_empty_profile_and_fail_closed(self):
        value = profile(0, [[-2, -2], [-1, -2], [-1, -1], [-2, -1]])
        self.apply([put("profile", value), put("member", member(0, -2, -2, profileId=0, A=literal(1), B=literal(1))),
                    put("run", run(0, profileId=0, length=literal(100000000))), put("profile", profile(1))])
        self.assertEqual([[-2, -2, -1, -1]], [m["rect"] for m in self.read()["state"]["members"]])
        expected = self.command("dump")["text"]
        path = self.directory / "world.scene"
        path.write_text(expected, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(expected, self.command("dump")["text"])
        payloads = [json.loads(base64.b64decode(line.split()[2])) for line in expected.splitlines() if line.startswith("section-profile ")]
        self.assertIn(value, payloads)
        before = self.snapshot()
        profile_line = next(line for line in expected.splitlines() if line.startswith("section-profile profile "))
        variants = [("missing requires section-profile/1 marker", expected.replace("requires section-profile/1\n", "")),
                    ("unknown section-profile/99 capability", expected.replace("section-profile/1", "section-profile/99")),
                    ("duplicate profile id record", expected + profile_line + "\n")]
        for label, content in variants:
            path.write_text(content, encoding="utf-8")
            self.assertFalse(self.command("loadfile " + str(path))["ok"], "I51: a scene with a %s must be rejected" % label)
            self.assertEqual(before, self.snapshot())
        injected = self.command("line " + profile_line)
        self.assertFalse(injected["ok"], "I49: section-profile records must not be injected line by line: %s" % injected)
        self.assertNotIn("preview", injected, "I49: section-profile records must not be injected line by line (not even as a confirmable preview)")
        self.assertEqual(before, self.snapshot())
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            path.write_text(expected, encoding="utf-8")
            self.assertTrue(fresh.command("loadfile " + str(path))["ok"])
            self.assertEqual(expected, fresh.command("dump")["text"])
            # The declaration stays in force after the load; the atomic-load rule is what still refuses a late record.
            late = base64.b64encode(json.dumps({"id": 7, "name": "late", "outline": [[0, 0], [10, 0], [10, 10], [0, 10]]},
                                               separators=(",", ":"), sort_keys=True).encode()).decode()
            injected = fresh.command("line section-profile profile " + late)
            self.assertFalse(injected["ok"], "I49: section-profile records must not be injected line by line after a scene load: %s" % injected)
            self.assertNotIn("preview", injected, "I49: section-profile records must not be injected line by line (not even as a confirmable preview)")
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

    def test_source_index_typed_closure_and_display_identity(self):
        a = member(A={"kind": "spec", "name": "a"})
        self.apply([{"op":"put-spec","name":"a","value":27}, put("profile",profile()), put("member",a), put("member",panel()), put("run",run())])
        graph = self.command("source-inspect")
        self.assertTrue(graph["complete"], graph)
        nodes = {n["key"]:n for n in graph["nodes"]}
        edges = {(e["from"],e["to"]) for e in graph["edges"]}
        self.assertTrue({"section-profile:1","profile-member:1","profile-member:4","profile-run:1","panel-spec:calcium-silicate-6"} <= nodes.keys())
        self.assertTrue({("profile-member:1","spec:a"),("profile-member:1","section-profile:1"),("profile-member:4","panel-spec:calcium-silicate-6"),("profile-run:1","profile-member:1"),("profile-run:1","profile-member:4")} <= edges)
        value = profile(); value["name"] = "display only"
        self.apply([put("profile",value)])
        changed = {n["key"]:n for n in self.command("source-inspect")["nodes"]}
        self.assertEqual(nodes["section-profile:1"]["definitionFingerprint"], changed["section-profile:1"]["definitionFingerprint"])
        self.assertEqual(nodes["profile-run:1"]["valueFingerprint"], changed["profile-run:1"]["valueFingerprint"])
        self.apply([{"op":"put-spec","name":"a","value":26}])
        changed = {n["key"]:n for n in self.command("source-inspect")["nodes"]}
        self.assertNotEqual(nodes["profile-member:1"]["valueFingerprint"], changed["profile-member:1"]["valueFingerprint"])
        self.assertNotEqual(nodes["profile-run:1"]["valueFingerprint"], changed["profile-run:1"]["valueFingerprint"])
        # Scenario verification preserves the same exact native inventory.
        sys.path.insert(0,str(ROOT/"geometry-web"))
        import scenario_verify
        path=self.directory/"inventory.scene";path.write_text(self.command("dump")["text"])
        graph=self.command("source-inspect-file "+str(path))
        objects,inventory=scenario_verify._inventory(graph,{"boundaries":[],"placements":[]})
        self.assertTrue({("section-profile",1),("profile-member",1),("profile-member",4),("profile-run",1),("panel-spec","calcium-silicate-6")} <= {(o["kind"],o["id"]) for o in objects})
        self.assertEqual(len(graph["edges"]),len(inventory["references"]))
        self.assertIn("section-profile/1",scenario_verify._capabilities(["section-profile/1"],()))
        complete=scenario_verify.verify_project(
            {"manifest":{"requiredCapabilities":["section-profile/1"],"faces":[],
                         "faceProjections":[],"reconstructionReviews":[],"models":[]},
             "scene":path.read_text()},bridge_executable=self.binary)
        self.assertEqual(path.read_text(),complete["final_scene"])
        self.assertEqual(objects,complete["objects"])

    def host(self, holes=None):
        return {"kind":"space-wall-values","sourceDescription":"依某空間牆取值，不隨空間變動",
                "frame":{"origin":[0,0,2700],"U":"+X","V":"+Y","N":"+Z"},
                "region":{"outline":[[0,0],[5000,0],[5000,5000],[0,5000]],"holes":holes or []}}

    def simple(self, host=None, **extra):
        return {"kind":"simple","host":host or self.host(),"dir":"+v","p":1000,"q":2000,"up":"+Z",**extra}

    def live_host(self, origin=2700):
        self.assertTrue(self.command("line boundary 9 outline 0,0 5000,0 5000,5000 0,5000")["ok"])
        reply=self.command(f"line placement 9 on boundary 9 origin 0 0 {origin} u +x v +y")
        self.assertTrue(reply["ok"],reply)
        if reply.get("preview"):
            self.assertTrue(self.command("line confirm "+str(reply["preview"]["token"]))["ok"])
        return {"kind":"placement","placementId":9}

    def test_all_violations_exact_regions_and_retained_rectangles(self):
        outline=[[0,0],[100,0],[100,100],[60,100],[60,40],[40,40],[40,100],[0,100]]
        self.apply([put("profile",profile(outline=outline))])
        invalid=[member(1,20,20,A=literal(60),B=literal(60)), member(2,90,90,A=literal(20),B=literal(20)), member(3,25,25,A=literal(10),B=literal(10))]
        preview=self.reject([put("member",m) for m in invalid],"V_PROFILE_OUTSIDE")
        self.assertTrue(preview["diagnosticsComplete"])
        violations=preview["violations"]
        self.assertEqual(violations,preview["sectionProfiles"]["violations"])
        outside={v["memberId"]:v for v in violations if v["code"]=="V_PROFILE_OUTSIDE"}
        self.assertEqual({1,2},set(outside))
        self.assertEqual([[40,40,60,80]],outside[1]["outsideRegions"])
        self.assertEqual([[100,90,110,100],[90,100,110,110]],outside[2]["outsideRegions"])
        overlap=next(v for v in violations if v["code"]=="V_PROFILE_OVERLAP")
        self.assertEqual((1,3,[25,25,35,35]),(overlap["memberId"],overlap["otherMemberId"],overlap["intersection"]))
        self.assertEqual([[20,20,80,80],[90,90,110,110],[25,25,35,35]],[m["rect"] for m in preview["sectionProfiles"]["after"]["members"]])
        self.assertEqual([],self.read()["state"]["members"])

    def test_simple_copied_host_ac24_and_fresh_scene_roundtrip(self):
        self.fixture()
        value=run(placement=self.simple())
        self.apply([put("run",value)])
        item=self.read()["state"]["runs"][0]
        self.assertEqual({"origin":[1000,2000,2700],"U":[1,0,0],"V":[0,0,-1],"N":[0,1,0]},item["frame"],
                         "R38/AC10: dir=+v, up=+Z, (p,q)=(1000,2000) on the host frame at z=2700")
        self.assertEqual([[1000,2000,2667],[1027,4400,2700]],item["members"][0]["bounds"])
        graph=self.command("source-inspect")
        self.assertFalse(any(e["from"]=="profile-run:1" and e["to"].startswith(("space:","placement:")) for e in graph["edges"]))
        dump=self.command("dump")["text"];path=self.directory/"copied.scene";path.write_text(dump)
        with BridgeSession(self.binary,cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile "+str(path))["ok"])
            self.assertEqual(dump,fresh.command("dump")["text"])
            self.assertEqual(item,fresh.command("section-profile-read")["state"]["runs"][0])
        renamed=self.host();renamed["sourceDescription"]="另一個顯示名稱"
        self.apply([put("run",run(placement=self.simple(renamed)))])
        after=self.command("source-inspect")
        a=next(n for n in graph["nodes"] if n["key"]=="profile-run:1")
        b=next(n for n in after["nodes"] if n["key"]=="profile-run:1")
        self.assertEqual((a["definitionFingerprint"],a["valueFingerprint"]),(b["definitionFingerprint"],b["valueFingerprint"]))

    def test_simple_holes_closed_boundary_vertical_direction_and_invalid_up(self):
        self.apply([put("profile",profile())])
        host=self.host([[[900,1900],[1100,1900],[1100,2100],[900,2100]]])
        self.reject([put("run",run(placement=self.simple(host)))],"outside closed host range")
        self.apply([put("run",run(placement=self.simple(host,p=900)))])
        self.reject([put("run",run(placement=self.simple(up="+Y")))],"perpendicular")
        self.reject([put("run",run(placement=self.simple(p=5001)))],"outside closed host range")
        vertical=self.host();vertical["frame"]={"origin":[0,0,0],"U":"+X","V":"+Z","N":"-Y"}
        self.apply([put("run",run(placement=self.simple(vertical,up="+X")))])
        self.assertEqual([0,0,1],self.read()["state"]["runs"][0]["frame"]["N"])
        far=self.host();far["frame"]["origin"]=[99999999,0,2700]
        self.reject([put("run",run(placement=self.simple(far)))],"origin exceeds D1")
        bad=self.simple(vertical);del bad["up"]
        self.reject([put("run",run(placement=bad))],"explicit")

    def test_live_host_follow_detach_conversion_and_atomic_delete(self):
        host=self.live_host();self.fixture()
        self.apply([put("run",run(placement=self.simple(host)))])
        graph=self.command("source-inspect")
        self.assertTrue(any(e["from"]=="profile-run:1" and e["to"]=="placement:9" for e in graph["edges"]))
        before=self.read()["state"]["runs"][0]
        reply=self.command("line placement 9 on boundary 9 origin 0 0 2800 u +x v +y")
        self.assertFalse(reply["ok"],reply)
        self.assertTrue(reply["preview"]["valid"],reply)
        self.assertTrue(self.command("line confirm "+str(reply["preview"]["token"]))["ok"])
        self.assertEqual([1000,2000,2800],self.read()["state"]["runs"][0]["frame"]["origin"],
                         "R38/R40: O = o_H + p*U_H + q*V_H must follow the live host to z=2800")
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before,self.read()["state"]["runs"][0])
        self.reject([{"op":"delete-placement","id":9}],"missing or invalid")
        preview,_=self.apply([{"op":"convert-run-to-advanced","id":1}])
        self.assertIn("RUN_HOST_DETACHED",[w["code"] for w in preview["sectionProfiles"]["warnings"]])
        detached=self.read()["state"]["runs"][0]
        self.assertEqual(before["frame"],detached["frame"])
        self.assertEqual(before["members"],detached["members"])
        self.apply([{"op":"convert-run-to-simple","id":1,"host":host}])
        self.assertEqual(before,self.read()["state"]["runs"][0],"D38: advanced->simple must give back the authored live placement")
        self.apply([{"op":"convert-run-to-advanced","id":1},{"op":"delete-placement","id":9}])
        self.assertEqual(detached,self.read()["state"]["runs"][0])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before,self.read()["state"]["runs"][0])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(detached,self.read()["state"]["runs"][0])

    def test_conversion_reports_all_unsatisfied_conditions_and_zero_writes(self):
        self.apply([put("profile",profile()),put("run",run(placement={"kind":"advanced","origin":[6000,6000,2800],"N":"+Z","V":"+Y"}))])
        preview=self.reject([{"op":"convert-run-to-simple","id":1,"host":self.host()}],"origin not in host plane")
        text=json.dumps(preview)
        self.assertIn("N not a host-plane direction",text)
        self.assertIn("p,q outside host range",text)

    def test_all_bad_dimension_dependents_are_diagnosed(self):
        self.apply([{"op":"put-spec","name":"a","value":27},put("profile",profile()),
                    put("member",member(A={"kind":"spec","name":"a"})),
                    put("member",member(2,373,A={"kind":"spec","name":"a"}))])
        preview=self.reject([{"op":"delete-spec","name":"a"}],"MEMBER_DIMENSION_INVALID")
        errors=[v for v in preview["violations"] if v["code"]=="MEMBER_DIMENSION_INVALID"]
        self.assertEqual({1,2},{v["memberId"] for v in errors})

    def test_upstream_engineering_and_parameter_failure_still_lists_each_profile_dependent(self):
        for line in ("surface 7 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
                     "timber 11 27 33 role boundary","place 11 on 7 at-face e0 +u +n"):
            self.assertTrue(self.command("line "+line)["ok"])
        source={"kind":"spec","name":"shared"}
        self.apply([{"op":"put-spec","name":"shared","value":27},
                    {"op":"set-source","target":{"kind":"timber","id":11,"field":"A"},"source":source},
                    put("profile",profile()),put("member",member(A=source)),put("member",member(2,373,A=source))])
        preview=self.reject([{"op":"delete-spec","name":"shared"}],"MEMBER_DIMENSION_INVALID")
        self.assertEqual({1,2},{v["memberId"] for v in preview["violations"] if v["code"]=="MEMBER_DIMENSION_INVALID"})
        parameter={"id":0,"name":"source","fields":[{"id":0,"name":"A","type":"dimension","input":"27"}]}
        source={"kind":"parameter","parameterId":0,"fieldId":0}
        self.apply([{"op":"put-parameter","value":parameter},put("member",member(A=source)),put("member",member(2,373,A=source))])
        del parameter["fields"][0]["input"]
        parameter["fields"][0]["expression"]={"op":"ref","parameterId":0,"fieldId":0}
        preview=self.reject([{"op":"put-parameter","value":parameter}],"MEMBER_DIMENSION_INVALID")
        self.assertEqual({1,2},{v["memberId"] for v in preview["violations"] if v["code"]=="MEMBER_DIMENSION_INVALID"})

    def test_live_host_shrink_lists_each_run_and_pending_reads_preserve_token(self):
        host=self.live_host()
        self.apply([put("profile",profile()),put("run",run(1,placement=self.simple(host))),
                    put("run",run(2,placement=self.simple(host,p=3000)))])
        before=self.snapshot()
        rejected=self.command("line boundary 9 outline 0,0 500,0 500,500 0,500")
        self.assertFalse(rejected["ok"],rejected)
        self.assertFalse(rejected["preview"]["valid"],rejected)
        errors=rejected["preview"]["sectionProfiles"]["violations"]
        self.assertEqual({1,2},{v["runId"] for v in errors if v["code"]=="RUN_PLACEMENT_INVALID"})
        self.assertEqual(before,self.snapshot())
        preview=self.preview([put("run",run(1,placement=self.simple(host,p=1200)))])
        self.assertTrue(preview["valid"])
        path=self.directory/"snapshot.scene";path.write_text(before[0])
        self.assertTrue(self.command("source-inspect-file "+str(path))["complete"])
        self.assertTrue(self.command("section-profile-confirm "+str(preview["token"]))["ok"])
        self.assertEqual([1200,2000,2700],self.read()["state"]["runs"][0]["frame"]["origin"],"R38: p=1200 moves the run origin along U_H")

    def test_all_cardinal_frames_and_four_host_directions_are_exact(self):
        self.apply([put("profile",profile())])
        axes={"+X":[1,0,0],"-X":[-1,0,0],"+Y":[0,1,0],"-Y":[0,-1,0],"+Z":[0,0,1],"-Z":[0,0,-1]}
        def cross(a,b):
            return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
        for uname,u in axes.items():
            for vname,v in axes.items():
                if sum(a*b for a,b in zip(u,v)):continue
                n=cross(u,v);nname=next(k for k,a in axes.items() if a==n)
                host=self.host();host["frame"]={"origin":[0,0,0],"U":uname,"V":vname,"N":nname}
                for direction,expected in [("+u",u),("-u",[-a for a in u]),("+v",v),("-v",[-a for a in v])]:
                    placement=self.simple(host,dir=direction,p=0,q=0,up=nname)
                    self.apply([put("run",run(placement=placement))])
                    state=self.read()["state"]["runs"][0]
                    where="host U=%s V=%s dir=%s up=%s"%(uname,vname,direction,nname)
                    self.assertEqual(expected,state["frame"]["N"],"R38: N must equal the run direction d ("+where+")")
                    self.assertEqual([-a for a in n],state["frame"]["V"],"R38: V must be -up ("+where+")")
                    self.assertEqual(cross([-a for a in n],expected),state["frame"]["U"],"R38: U must be V x N ("+where+")")
                    self.apply([{"op":"convert-run-to-advanced","id":1}])
                    self.assertEqual(state["frame"],self.read()["state"]["runs"][0]["frame"],"D38: simple->advanced must keep the evaluated frame ("+where+")")
                    self.apply([{"op":"convert-run-to-simple","id":1,"host":host}])
                    self.assertEqual(state,self.read()["state"]["runs"][0],"D38: advanced->simple must recover dir/p/q/up ("+where+")")

    def test_maximum_pair_diagnostics_and_copied_host_capacity_roundtrip(self):
        self.apply([put("profile",profile())])
        capacity=self.read()["capacity"]["members"]
        preview=self.reject([put("member",member(i)) for i in range(capacity)],"V_PROFILE_OVERLAP")
        self.assertEqual(capacity*(capacity-1)//2,len(preview["violations"]))
        self.assertTrue(preview["diagnosticsComplete"])
        holes=[[[100+i*300,100],[200+i*300,100],[200+i*300,200],[100+i*300,200]] for i in range(8)]
        host=self.host(holes)
        self.apply([put("run",run(i,placement=self.simple(host))) for i in range(self.read()["capacity"]["runs"])])
        expected=self.command("dump")["text"]
        path=self.directory/"hosts.scene";path.write_text(expected)
        with BridgeSession(self.binary,cwd=self.directory) as fresh:
            self.assertTrue(fresh.command("loadfile "+str(path))["ok"])
            self.assertEqual(expected,fresh.command("dump")["text"])
        host["region"]["holes"].append([[3000,100],[3100,100],[3100,200],[3000,200]])
        self.reject([put("run",run(placement=self.simple(host)))],"bounded effective region")


if __name__ == "__main__":
    unittest.main()
